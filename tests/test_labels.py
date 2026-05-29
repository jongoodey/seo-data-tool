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
