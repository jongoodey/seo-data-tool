from seo_analyser.registry.introspect import build_catalogue, EndpointMeta

CATALOGUE = build_catalogue()

EXPECTED_FAMILIES = {
    "serp", "keywords_data", "business_data", "dataforseo_labs",
    "ai_optimization", "app_data", "merchant", "on_page",
    "backlinks", "domain_analytics", "content_analysis",
    "content_generation", "appendix",
}


def test_all_families_present():
    assert set(CATALOGUE.keys()) == EXPECTED_FAMILIES


def test_serp_is_largest_family():
    counts = {fam: len(eps) for fam, eps in CATALOGUE.items()}
    assert max(counts, key=counts.get) == "serp"
    # 181 canonical SERP endpoints per endpoint-inventory.md; allow drift across SDK versions
    assert counts["serp"] > 100


def test_endpoint_meta_shape():
    serp = CATALOGUE["serp"]
    organic = next(e for e in serp if e.name == "google_organic_live_advanced")
    assert isinstance(organic, EndpointMeta)
    assert organic.request_model is not None
    # the request model must expose Pydantic fields
    assert hasattr(organic.request_model, "model_fields")
    assert "keyword" in organic.request_model.model_fields


def test_variants_are_filtered_out():
    for eps in CATALOGUE.values():
        for e in eps:
            assert not e.name.endswith("_with_http_info")
            assert not e.name.endswith("_without_preload_content")


def test_task_based_detection():
    serp = CATALOGUE["serp"]
    assert any(e.is_task_based for e in serp)
