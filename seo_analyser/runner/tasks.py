"""Run task-based endpoints: post -> poll tasks_ready -> fetch by id."""
from __future__ import annotations

import time

from seo_analyser.auth import Credentials
from seo_analyser.registry.introspect import EndpointMeta
from seo_analyser.runner.errors import RunError, normalise
from seo_analyser.runner.live import _api_class_for, _to_dict


def extract_task_id(resp: dict) -> str | None:
    tasks = resp.get("tasks") or []
    if not tasks:
        return None
    return tasks[0].get("id")


def ready_ids(resp: dict) -> set[str]:
    out: set[str] = set()
    for task in resp.get("tasks") or []:
        for row in task.get("result") or []:
            if isinstance(row, dict) and row.get("id"):
                out.add(row["id"])
    return out


def run_task(meta: EndpointMeta, payload: dict, creds: Credentials,
             on_wait=None, max_wait: int = 120, interval: int = 5) -> dict:
    if not creds.is_complete:
        raise RunError("auth", "Enter your DataForSEO login and password first.")
    post_method, ready_method, get_method = meta.task_methods
    if not (post_method and ready_method and get_method):
        raise RunError("bad_request", f"{meta.name} is missing task methods.")

    from dataforseo_client import api_client as prov
    from dataforseo_client import configuration as cfg

    conf = cfg.Configuration(username=creds.login, password=creds.password)
    try:
        request_obj = meta.request_model(**payload)
        with prov.ApiClient(conf) as client:
            api = _api_class_for(meta.family)(client)
            posted = _to_dict(getattr(api, post_method)([request_obj]))
            task_id = extract_task_id(posted)
            if not task_id:
                raise RunError("bad_request",
                               f"Task not accepted: {posted.get('status_message')}")

            waited = 0
            while waited < max_wait:
                ready = _to_dict(getattr(api, ready_method)())
                if task_id in ready_ids(ready):
                    break
                if on_wait:
                    on_wait(waited)
                time.sleep(interval)
                waited += interval

            return _to_dict(getattr(api, get_method)(id=task_id))
    except RunError:
        raise
    except Exception as exc:  # noqa: BLE001 — normalised below
        raise normalise(exc) from exc
