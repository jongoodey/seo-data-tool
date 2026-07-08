from seo_analyser.forms.builder import bool_from_choice


def test_unset_is_none():
    assert bool_from_choice("") is None


def test_true_false():
    assert bool_from_choice("true") is True
    assert bool_from_choice("false") is False


# --- split_common_advanced ------------------------------------------------------

from seo_analyser.forms.builder import split_common_advanced


def _named_spec(name, requirement=""):
    from seo_analyser.forms.widgets import FieldSpec
    return FieldSpec(name=name, kind="text", requirement=requirement)


def test_code_twin_demoted_when_name_present():
    specs = [_named_spec("language_name", "conditional"),
             _named_spec("language_code", "conditional")]
    common, advanced = split_common_advanced(specs)
    assert [s.name for s in common] == ["language_name"]
    assert [s.name for s in advanced] == ["language_code"]


def test_code_stays_upfront_without_name_twin():
    specs = [_named_spec("language_code", "required")]
    common, _advanced = split_common_advanced(specs)
    assert [s.name for s in common] == ["language_code"]


def test_numbered_targets_builds_dataforseo_dict():
    from seo_analyser.forms.builder import numbered_targets
    assert numbered_targets(["a.com", "b.com"]) == {"1": "a.com", "2": "b.com"}
    assert numbered_targets([]) == {}
