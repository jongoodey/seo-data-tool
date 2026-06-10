from seo_analyser.registry.catalogue import score_endpoint, search_endpoints
from seo_analyser.registry.introspect import EndpointMeta


def _meta(family, name):
    return EndpointMeta(name=name, family=family, request_model=None, is_task_based=False)


def test_matches_all_tokens():
    e = _meta("serp", "google_organic_live_advanced")
    assert score_endpoint(e, ["google", "organic"]) > 0
    assert score_endpoint(e, ["organic", "serp"]) > 0


def test_non_match_scores_zero():
    assert score_endpoint(_meta("serp", "google_organic_live_advanced"), ["backlinks"]) == 0


def test_all_tokens_must_match():
    assert score_endpoint(_meta("backlinks", "available_filters"), ["ai", "overview"]) == 0


def test_word_match_outranks_substring():
    ai = _meta("serp", "ai_summary")
    avail = _meta("backlinks", "available_filters")   # "ai" hides inside "available"
    assert score_endpoint(ai, ["ai"]) > score_endpoint(avail, ["ai"])


def test_empty_query_returns_nothing():
    assert search_endpoints("") == []


def test_ai_overview_finds_ai_endpoints_first():
    top = search_endpoints("ai overview")[0]
    haystack = f"{top.family} {top.name}".replace("_", " ")
    assert "ai" in haystack.split(), f"unexpected top hit: {top.family}.{top.name}"
