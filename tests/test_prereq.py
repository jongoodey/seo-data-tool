"""Prerequisite-task workflow: descriptor selection, readiness parsing, id harvest."""
from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

from seo_analyser.registry import catalogue
from seo_analyser.runner.prereq import (
    Prerequisite, crawl_finished, prerequisite_for, recent_task_ids,
)


def _spec(name: str, requirement: str = "required"):
    return SimpleNamespace(name=name, requirement=requirement)


class TestPrerequisiteFor:
    def test_onpage_reader_matches(self):
        p = prerequisite_for("on_page", [_spec("id")])
        assert p and p.kind == "onpage_crawl" and p.id_field == "id"

    def test_serp_reader_matches(self):
        p = prerequisite_for("serp", [_spec("task_id")])
        assert p and p.kind == "serp_task" and p.id_field == "task_id"

    def test_optional_id_is_not_a_prerequisite(self):
        assert prerequisite_for("on_page", [_spec("id", "optional")]) is None

    def test_other_families_unaffected(self):
        assert prerequisite_for("backlinks", [_spec("id")]) is None


class TestCrawlFinished:
    def test_finished(self):
        resp = {"tasks": [{"result": [{"crawl_progress": "finished"}]}]}
        assert crawl_finished(resp)

    def test_in_progress(self):
        resp = {"tasks": [{"result": [{"crawl_progress": "in_progress"}]}]}
        assert not crawl_finished(resp)

    def test_empty(self):
        assert not crawl_finished({})


class _StubStore:
    def __init__(self, runs, responses):
        self._runs, self._responses = runs, responses

    def recent_runs(self, limit):
        return self._runs[:limit]

    def load_response(self, run_id):
        return self._responses.get(run_id)


def _run(run_id, family, endpoint, params=None, has_response=False):
    return SimpleNamespace(id=run_id, family=family, endpoint=endpoint,
                           params=params or {}, has_response=has_response,
                           created_at=datetime(2026, 6, 10, 12, 0))


class TestRecentTaskIds:
    def test_harvests_param_ids_and_post_response_ids(self):
        prereq = Prerequisite("id", "on_page", "an On-Page crawl", "onpage_crawl")
        runs = [
            _run(1, "on_page", "pages", params={"id": "crawl-aaa"}),
            _run(2, "on_page", "task_post", has_response=True),
            _run(3, "serp", "ai_summary", params={"task_id": "serp-zzz"}),
        ]
        store = _StubStore(runs, {2: {"tasks": [{"id": "crawl-bbb"}]}})
        ids = [tid for tid, _ in recent_task_ids(store, prereq)]
        assert ids == ["crawl-aaa", "crawl-bbb"]

    def test_dedupes(self):
        prereq = Prerequisite("id", "on_page", "an On-Page crawl", "onpage_crawl")
        runs = [
            _run(1, "on_page", "pages", params={"id": "same"}),
            _run(2, "on_page", "links", params={"id": "same"}),
        ]
        ids = recent_task_ids(_StubStore(runs, {}), prereq)
        assert len(ids) == 1


class TestCatalogueAssumptions:
    """The workflow depends on these endpoints existing under these names."""

    def test_onpage_task_post_exists(self):
        meta = catalogue.find_endpoint("on_page", "task_post")
        assert meta is not None and meta.request_model is not None

    def test_serp_google_organic_task_exists(self):
        meta = catalogue.find_endpoint("serp", "google_organic")
        assert meta is not None and meta.task_methods
        post, ready, get = meta.task_methods
        assert post and ready and get
