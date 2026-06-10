"""Prerequisite-task workflow for readers that consume a prior task's id.

Two families have "orphan reader" endpoints whose required id comes from an
earlier task:

- on_page: fifteen readers (pages, links, content_parsing, raw_html, ...) all
  take the ``id`` of an On-Page crawl (``task_post`` -> poll ``summary`` until
  ``crawl_progress == "finished"``).
- serp: ``ai_summary`` and ``screenshot`` take the ``task_id`` of a completed
  SERP task (google organic ``task_post`` -> ``tasks_ready``).

This module knows how to start those prerequisite tasks, poll them to
readiness, and harvest usable ids from run history.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from seo_analyser.auth import Credentials
from seo_analyser.registry import catalogue
from seo_analyser.runner.errors import RunError, normalise
from seo_analyser.runner.live import _api_class_for, _to_dict
from seo_analyser.runner.tasks import extract_task_id, ready_ids

_SERP_TASK_BASE = "google_organic"


@dataclass(frozen=True)
class Prerequisite:
    id_field: str   # name of the field on the reader form ("id" / "task_id")
    family: str
    label: str      # human phrase for the UI
    kind: str       # "onpage_crawl" | "serp_task"


def prerequisite_for(family: str, specs) -> Prerequisite | None:
    """Return the prerequisite descriptor if this endpoint reads a prior task."""
    required = {s.name for s in specs if s.requirement == "required"}
    if family == "on_page" and "id" in required:
        return Prerequisite("id", "on_page", "an On-Page crawl", "onpage_crawl")
    if family == "serp" and "task_id" in required:
        return Prerequisite("task_id", "serp", "a completed SERP task", "serp_task")
    return None


def crawl_finished(summary_resp: dict) -> bool:
    """True when an on_page summary response reports the crawl as finished."""
    for task in summary_resp.get("tasks") or []:
        for row in task.get("result") or []:
            if isinstance(row, dict) and row.get("crawl_progress") == "finished":
                return True
    return False


def _post_endpoint_meta(prereq: Prerequisite):
    if prereq.kind == "onpage_crawl":
        meta = catalogue.find_endpoint("on_page", "task_post")
        if meta is None:
            raise RunError("bad_request", "on_page task_post endpoint not found.")
        return meta, "task_post", None
    meta = catalogue.find_endpoint("serp", _SERP_TASK_BASE)
    if meta is None or not meta.task_methods:
        raise RunError("bad_request", "serp google organic task endpoint not found.")
    post_method, ready_method, _ = meta.task_methods
    return meta, post_method, ready_method


def post_prerequisite(prereq: Prerequisite, payload: dict, creds: Credentials) -> str:
    """Start the prerequisite task; returns its id (the reader can use it once ready)."""
    if not creds.is_complete:
        raise RunError("auth", "Enter your DataForSEO login and password first.")
    meta, post_method, _ = _post_endpoint_meta(prereq)

    from dataforseo_client import api_client as prov
    from dataforseo_client import configuration as cfg

    conf = cfg.Configuration(username=creds.login, password=creds.password)
    try:
        request_obj = meta.request_model(**payload)
        with prov.ApiClient(conf) as client:
            api = _api_class_for(prereq.family)(client)
            posted = _to_dict(getattr(api, post_method)([request_obj]))
    except RunError:
        raise
    except Exception as exc:  # noqa: BLE001 — normalised below
        raise normalise(exc) from exc

    task_id = extract_task_id(posted)
    status = (posted.get("tasks") or [{}])[0].get("status_message", "")
    if not task_id or posted.get("status_code") != 20000:
        raise RunError("bad_request", f"Task not accepted: {status or 'unknown error'}")
    return task_id


def is_ready(prereq: Prerequisite, task_id: str, creds: Credentials) -> bool:
    """One readiness probe (no waiting). on_page polls summary; serp polls tasks_ready."""
    from dataforseo_client import api_client as prov
    from dataforseo_client import configuration as cfg

    conf = cfg.Configuration(username=creds.login, password=creds.password)
    try:
        with prov.ApiClient(conf) as client:
            api = _api_class_for(prereq.family)(client)
            if prereq.kind == "onpage_crawl":
                return crawl_finished(_to_dict(api.summary(id=task_id)))
            _, _, ready_method = _post_endpoint_meta(prereq)
            return task_id in ready_ids(_to_dict(getattr(api, ready_method)()))
    except Exception as exc:  # noqa: BLE001 — normalised below
        raise normalise(exc) from exc


def wait_until_ready(prereq: Prerequisite, task_id: str, creds: Credentials,
                     on_wait=None, max_wait: int = 180, interval: int = 6) -> bool:
    """Poll until the task is ready. Returns False on timeout (id is still valid)."""
    waited = 0
    while waited < max_wait:
        if is_ready(prereq, task_id, creds):
            return True
        if on_wait:
            on_wait(waited)
        time.sleep(interval)
        waited += interval
    return False


def recent_task_ids(store, prereq: Prerequisite, limit: int = 30) -> list[tuple[str, str]]:
    """(task_id, label) pairs harvested from run history, newest first.

    Ids live in two places: the params of earlier reader runs (the user already
    pasted a valid id once) and the saved responses of prerequisite-task runs.
    """
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    loads = 0
    for run in store.recent_runs(limit):
        if run.family != prereq.family:
            continue
        stamp = run.created_at.strftime("%d %b %H:%M") if run.created_at else ""
        param_id = (run.params or {}).get(prereq.id_field)
        if param_id and param_id not in seen:
            seen.add(param_id)
            out.append((param_id, f"used by {run.endpoint} · {stamp}"))
        is_post_run = (
            run.endpoint == "task_post" if prereq.kind == "onpage_crawl"
            else run.endpoint == _SERP_TASK_BASE
        )
        if is_post_run and run.has_response and loads < 10:
            loads += 1
            response = store.load_response(run.id) or {}
            rid = extract_task_id(response)
            if rid and rid not in seen:
                seen.add(rid)
                out.append((rid, f"{run.endpoint} · {stamp}"))
    return out
