from seo_analyser.registry.introspect import group_task_methods
from seo_analyser.runner.tasks import extract_task_id, ready_ids


def test_groups_triplet():
    methods = [
        "google_organic_live_advanced",
        "google_organic_task_post",
        "google_organic_tasks_ready",
        "google_organic_task_get_advanced",
        "google_organic_task_get_regular",
    ]
    groups = group_task_methods(methods)
    assert "google_organic" in groups
    g = groups["google_organic"]
    assert g["post"] == "google_organic_task_post"
    assert g["ready"] == "google_organic_tasks_ready"
    assert g["get"] == "google_organic_task_get_advanced"  # prefers advanced


def test_no_post_means_no_group():
    assert group_task_methods(["serp_locations"]) == {}


def test_extract_task_id():
    resp = {"tasks": [{"id": "abc-123", "status_code": 20100}]}
    assert extract_task_id(resp) == "abc-123"


def test_extract_task_id_missing():
    assert extract_task_id({"tasks": []}) is None


def test_ready_ids():
    resp = {"tasks": [{"result": [{"id": "a"}, {"id": "b"}]}]}
    assert ready_ids(resp) == {"a", "b"}
