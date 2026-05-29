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
