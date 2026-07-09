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


# --- llm_mention_target (AI-visibility target objects) --------------------------

from seo_analyser.forms.builder import llm_mention_target


def test_llm_mention_target_domain_forms():
    assert llm_mention_target("indexify.co.uk") == {"type": "domain", "domain": "indexify.co.uk"}
    assert llm_mention_target("https://www.indexify.co.uk/blog?utm=x") == {
        "type": "domain", "domain": "indexify.co.uk"}
    assert llm_mention_target("WWW.Example.COM") == {"type": "domain", "domain": "Example.COM"}


def test_llm_mention_target_keyword_forms():
    assert llm_mention_target("best trail running shoes") == {
        "type": "keyword", "keyword": "best trail running shoes"}
    assert llm_mention_target("open 24/7 gyms") == {"type": "keyword", "keyword": "open 24/7 gyms"}


def test_llm_targets_survive_sdk_round_trip():
    # The exact path run_live now takes: payload -> from_dict -> to_dict.
    from seo_analyser.registry import catalogue
    meta = catalogue.find_endpoint("ai_optimization", "llm_mentions_search_live")
    payload = {"target": [llm_mention_target("indexify.co.uk"),
                          llm_mention_target("best trail running shoes")],
               "location_name": "United Kingdom"}
    sent = meta.request_model.from_dict(payload).to_dict()
    assert sent["target"][0]["domain"] == "indexify.co.uk"
    assert sent["target"][1]["keyword"] == "best trail running shoes"
    assert sent["location_name"] == "United Kingdom"
