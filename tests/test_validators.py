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
