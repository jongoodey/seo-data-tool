from seo_analyser.labels import humanize, titleize


def test_humanize_sentence_case():
    assert humanize("location_name") == "Location name"
    assert humanize("keyword") == "Keyword"
    assert humanize("") == ""


def test_titleize_words():
    assert titleize("google_organic_live_advanced") == "Google Organic Live Advanced"


def test_titleize_keeps_acronyms():
    assert titleize("serp") == "SERP"
    assert titleize("ai_optimization") == "AI Optimization"


# --- family_label -------------------------------------------------------------

def test_every_family_has_a_plain_english_label():
    from seo_analyser.labels import family_label
    from seo_analyser.registry import catalogue
    for fam in catalogue.families():
        label = family_label(fam)
        assert label and "_" not in label


def test_family_label_falls_back_to_titleize():
    from seo_analyser.labels import family_label
    assert family_label("made_up_family") == "Made Up Family"


def test_family_label_is_friendly_for_serp():
    from seo_analyser.labels import family_label
    assert family_label("serp") == "Rankings (SERP)"
