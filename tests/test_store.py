import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from seo_analyser.persistence.store import Store


@pytest.fixture
def store():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool, future=True)
    return Store(engine)


def test_add_and_recent_runs(store):
    store.add_run("google_organic_live_advanced", "serp",
                  {"keyword": "shoes"}, 0.002, "ok")
    store.add_run("backlinks_summary_live", "backlinks", {"target": "x.com"}, 0.02, "ok")
    runs = store.recent_runs()
    assert len(runs) == 2
    assert runs[0].endpoint == "backlinks_summary_live"  # newest first
    assert runs[1].params == {"keyword": "shoes"}


def test_stores_and_loads_response(store):
    store.add_run("google_organic_live_html", "serp", {"keyword": "shoes"},
                  0.002, "ok", response={"tasks": [{"id": "abc"}]})
    run = store.recent_runs()[0]
    assert run.has_response is True
    assert store.load_response(run.id) == {"tasks": [{"id": "abc"}]}


def test_no_response_has_response_false(store):
    store.add_run("e", "f", {}, 0.0, "ok")  # no response
    run = store.recent_runs()[0]
    assert run.has_response is False
    assert store.load_response(run.id) is None


def test_update_run_completes_a_pending_run(store):
    store.add_run("chat_gpt_llm_responses_live", "ai_optimization", {"user_prompt": "x"},
                  0.0, "pending", response={"tasks": [{"id": "t1"}]})
    run_id = store.recent_runs()[0].id
    store.update_run(run_id, cost=0.01, status="ok",
                     response={"tasks": [{"id": "t1", "result": [{"items": []}]}]})
    run = store.recent_runs()[0]
    assert run.status == "ok"
    assert run.cost == 0.01
    assert store.load_response(run_id)["tasks"][0]["result"] == [{"items": []}]


def test_save_and_load_preset(store):
    store.save_preset("UK SERP", "serp", "google_organic_live_advanced",
                      {"location_name": "United Kingdom"})
    assert [p.name for p in store.list_presets()] == ["UK SERP"]
    loaded = store.load_preset("UK SERP")
    assert loaded.params == {"location_name": "United Kingdom"}


def test_save_preset_overwrites_same_name(store):
    store.save_preset("p", "serp", "e", {"a": 1})
    store.save_preset("p", "serp", "e", {"a": 2})
    assert len(store.list_presets()) == 1
    assert store.load_preset("p").params == {"a": 2}


def test_delete_preset(store):
    store.save_preset("p", "serp", "e", {})
    store.delete_preset("p")
    assert store.list_presets() == []
