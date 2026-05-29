from seo_analyser.forms.builder import bool_from_choice


def test_unset_is_none():
    assert bool_from_choice("") is None


def test_true_false():
    assert bool_from_choice("true") is True
    assert bool_from_choice("false") is False
