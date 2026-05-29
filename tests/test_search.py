from seo_analyser.registry.catalogue import matches_query


def test_matches_all_tokens():
    assert matches_query("serp", "google_organic_live_advanced", "google organic") is True
    assert matches_query("serp", "google_organic_live_advanced", "organic serp") is True


def test_non_match():
    assert matches_query("serp", "google_organic_live_advanced", "backlinks") is False


def test_empty_query_is_false():
    assert matches_query("serp", "google_organic_live_advanced", "") is False
