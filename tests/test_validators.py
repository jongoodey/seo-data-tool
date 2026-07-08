from seo_analyser.forms.validators import (
    looks_like_url, validate_payload, validate_required_ids,
)
from seo_analyser.forms.widgets import FieldSpec


def test_looks_like_url():
    assert looks_like_url("https://indexify.co.uk") is True
    assert looks_like_url("http://example.com/page?x=1") is True
    assert looks_like_url("indexify.co.uk") is False
    assert looks_like_url("ftp://x.com") is False
    assert looks_like_url("") is False


def test_validate_payload_flags_bad_url():
    warnings = validate_payload({"url": "indexify.co.uk", "keyword": "shoes"})
    assert len(warnings) == 1
    assert "url" in warnings[0]


def test_validate_payload_passes_good_url():
    assert validate_payload({"url": "https://indexify.co.uk"}) == []


def test_validate_payload_ignores_non_url_fields_and_lists():
    # remove_from_url is a list, not a scalar url field
    assert validate_payload({"remove_from_url": ["a", "b"], "target": "indexify.co.uk"}) == []


def test_validate_required_ids_flags_missing_id():
    specs = [FieldSpec(name="id", kind="text", requirement="required"),
             FieldSpec(name="url", kind="text", requirement="required")]
    warnings = validate_required_ids(specs, {"url": "https://x.com"})  # id missing
    assert len(warnings) == 1
    assert "prior task" in warnings[0]


def test_validate_required_ids_ok_when_present():
    specs = [FieldSpec(name="id", kind="text", requirement="required")]
    assert validate_required_ids(specs, {"id": "abc-123"}) == []


def test_validate_required_ids_ignores_optional_id():
    specs = [FieldSpec(name="id", kind="text", requirement="optional")]
    assert validate_required_ids(specs, {}) == []


# --- validate_required_fields -------------------------------------------------

from seo_analyser.forms.validators import validate_required_fields
from seo_analyser.forms.widgets import FieldSpec


def _spec(name, requirement="", partner=None, kind="text", default_hint=None):
    return FieldSpec(name=name, kind=kind, requirement=requirement,
                     partner=partner, default_hint=default_hint)


def test_blocks_empty_hard_required_field():
    specs = [_spec("keyword", "required")]
    assert validate_required_fields(specs, {}) != []
    assert validate_required_fields(specs, {"keyword": "indexify"}) == []


def test_skips_ids_nested_and_defaulted_fields():
    specs = [_spec("id", "required"),                         # covered by validate_required_ids
             _spec("filters", "required", kind="nested"),     # not renderable
             _spec("depth", "required", default_hint="100")]  # API has a default
    assert validate_required_fields(specs, {}) == []


def test_blocks_conditional_pair_only_when_both_empty():
    specs = [_spec("language_name", "conditional", partner="language_code"),
             _spec("language_code", "conditional", partner="language_name")]
    assert len(validate_required_fields(specs, {})) == 1  # deduplicated pair message
    assert validate_required_fields(specs, {"language_code": "en"}) == []


# --- Backlinks target / targets / date validation (IND-21) ---------------------

from seo_analyser.forms.validators import (
    backlinks_advisories, looks_like_domain, looks_like_target, parse_targets,
    validate_backlinks,
)


def test_looks_like_domain():
    assert looks_like_domain("example.com") is True
    assert looks_like_domain("sub.example.co.uk") is True
    assert looks_like_domain("www.example.com") is True   # shape-valid; flagged elsewhere
    assert looks_like_domain("https://example.com") is False
    assert looks_like_domain("example") is False
    assert looks_like_domain("not a domain") is False
    assert looks_like_domain("") is False


def test_looks_like_target_accepts_domain_or_full_url():
    assert looks_like_target("example.com") is True
    assert looks_like_target("https://example.com/page") is True
    assert looks_like_target("ftp://example.com") is False
    assert looks_like_target("just words") is False


def test_parse_targets_from_list_string_and_dict():
    assert parse_targets(["a.com", " b.com ", ""]) == ["a.com", "b.com"]
    assert parse_targets("a.com, b.com") == ["a.com", "b.com"]
    assert parse_targets("a.com\nb.com\n") == ["a.com", "b.com"]
    assert parse_targets({"1": "a.com", "2": "b.com"}) == ["a.com", "b.com"]
    assert parse_targets(None) == []


def test_validate_backlinks_accepts_domain_without_scheme():
    assert validate_backlinks("summary_live", {"target": "example.com"}) == []
    assert validate_backlinks("summary_live", {"target": "https://example.com/page"}) == []


def test_validate_backlinks_flags_www_prefix():
    problems = validate_backlinks("summary_live", {"target": "www.example.com"})
    assert len(problems) == 1
    assert "www." in problems[0]


def test_validate_backlinks_flags_malformed_target():
    problems = validate_backlinks("summary_live", {"target": "not a domain"})
    assert len(problems) == 1
    assert "example.com" in problems[0]  # plain-English guidance with an example


def test_validate_backlinks_flags_malformed_targets_entries():
    problems = validate_backlinks("bulk_ranks_live", {"targets": ["a.com", "bad target!"]})
    assert len(problems) == 1
    assert "bad target!" in problems[0]


def test_validate_backlinks_enforces_target_counts():
    bulk_over = [f"site{i}.com" for i in range(1001)]
    assert validate_backlinks("bulk_ranks_live", {"targets": bulk_over}) != []
    assert validate_backlinks("bulk_ranks_live", {"targets": bulk_over[:1000]}) == []

    intersect_over = {str(i): f"site{i}.com" for i in range(1, 22)}
    assert validate_backlinks("domain_intersection_live", {"targets": intersect_over}) != []

    excludes = [f"site{i}.com" for i in range(11)]
    assert validate_backlinks(
        "domain_intersection_live",
        {"targets": {"1": "a.com", "2": "b.com"}, "exclude_targets": excludes},
    ) != []


def test_validate_backlinks_checks_date_format_and_order():
    ok = {"target": "a.com", "date_from": "2026-01-01", "date_to": "2026-06-01"}
    assert validate_backlinks("history_live", ok) == []
    bad_format = {"target": "a.com", "date_from": "01/02/2026"}
    assert any("yyyy-mm-dd" in p for p in validate_backlinks("history_live", bad_format))
    reversed_range = {"target": "a.com", "date_from": "2026-06-01", "date_to": "2026-01-01"}
    assert validate_backlinks("history_live", reversed_range) != []


def test_validate_backlinks_empty_payload_is_quiet():
    # empty required fields are validate_required_fields' job, not this one's
    assert validate_backlinks("summary_live", {}) == []


def test_backlinks_advisories_warn_on_expensive_inputs_without_blocking():
    assert backlinks_advisories({"limit": 50}) == []
    high_limit = backlinks_advisories({"limit": 1000})
    assert len(high_limit) == 1 and "$" in high_limit[0]
    many_targets = backlinks_advisories({"targets": [f"s{i}.com" for i in range(500)]})
    assert len(many_targets) == 1 and "$" in many_targets[0]


def test_empty_target_blocks_on_real_summary_model():
    # acceptance: empty target fields block paid calls (via required-field check)
    from seo_analyser.forms.widgets import fields_for
    from seo_analyser.registry.introspect import build_catalogue

    summary = next(e for e in build_catalogue()["backlinks"] if e.name == "summary_live")
    warnings = validate_required_fields(fields_for(summary.request_model), {})
    assert any("target" in w for w in warnings)
