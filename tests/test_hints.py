from seo_analyser.forms.hints import hint_for


def test_backlinks_fields_have_plain_english_hints():
    for field in ("filters", "backlinks_filters", "order_by", "targets", "exclude_targets"):
        hint = hint_for("backlinks", field)
        assert hint, f"expected a hint for backlinks.{field}"


def test_targets_hint_shows_shape_and_caps():
    hint = hint_for("backlinks", "targets")
    assert "example.com" in hint
    assert "20" in hint and "1,000" in hint


def test_hints_are_scoped_to_family():
    assert hint_for("serp", "filters") is None
    assert hint_for("backlinks", "keyword") is None
