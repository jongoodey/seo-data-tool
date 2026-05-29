from seo_analyser.presets import presets_for


def test_location_name_presets():
    labels = [lbl for lbl, _ in presets_for("location_name")]
    assert "United Kingdom" in labels
    assert "Spain" in labels


def test_location_code_values_are_ints():
    by_label = dict(presets_for("location_code"))
    assert by_label["United Kingdom (2826)"] == 2826
    assert all(isinstance(v, int) for v in by_label.values())


def test_language_code_presets():
    by_label = dict(presets_for("language_code"))
    assert by_label["English (en)"] == "en"
    assert by_label["Spanish (es)"] == "es"


def test_unknown_field_has_no_presets():
    assert presets_for("keyword") == []
