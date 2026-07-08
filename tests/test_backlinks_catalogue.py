"""Pin the Backlinks family catalogue coverage (Linear IND-19).

The Backlinks integration work assumes exactly these 24 endpoints exist under
the `backlinks` family. If a dataforseo-client upgrade adds/renames/removes
endpoints, this test fails loudly instead of the UI silently drifting.
"""
from seo_analyser.registry.introspect import build_catalogue

CATALOGUE = build_catalogue()

# All 24 Backlinks SDK operations as introspected from dataforseo-client.
EXPECTED_BACKLINKS_ENDPOINTS = {
    # analysis (live, per-target)
    "summary_live",
    "history_live",
    "backlinks_live",
    "anchors_live",
    "domain_pages_live",
    "domain_pages_summary_live",
    "referring_domains_live",
    "referring_networks_live",
    "competitors_live",
    "domain_intersection_live",
    "page_intersection_live",
    "timeseries_summary_live",
    "timeseries_new_lost_summary_live",
    # bulk (many targets per request)
    "bulk_ranks_live",
    "bulk_backlinks_live",
    "bulk_spam_score_live",
    "bulk_referring_domains_live",
    "bulk_new_lost_backlinks_live",
    "bulk_new_lost_referring_domains_live",
    "bulk_pages_summary_live",
    # metadata / account
    "backlinks_id_list",
    "backlinks_errors",
    "backlinks_available_filters",
    "index",
}


def test_backlinks_family_has_exactly_the_24_expected_endpoints():
    names = {e.name for e in CATALOGUE["backlinks"]}
    assert names == EXPECTED_BACKLINKS_ENDPOINTS


def test_backlinks_endpoints_are_all_live():
    for e in CATALOGUE["backlinks"]:
        assert not e.is_task_based, f"{e.name} unexpectedly task-based"


def test_backlinks_runnable_endpoints_have_request_models():
    # index and available_filters are GET-style endpoints with no request body;
    # every other backlinks endpoint must be runnable through run_live.
    no_body = {"index", "backlinks_available_filters"}
    for e in CATALOGUE["backlinks"]:
        if e.name in no_body:
            assert e.request_model is None
        else:
            assert e.request_model is not None, f"{e.name} lost its request model"
