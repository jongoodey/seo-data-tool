from seo_analyser.billing.balance import parse_balance
from seo_analyser.billing.cost import estimate_cost, format_estimate


def test_parse_balance():
    resp = {"tasks": [{"result": [{"money": {"balance": 296.45, "total": 351.0}}]}]}
    assert parse_balance(resp) == 296.45


def test_parse_balance_missing():
    assert parse_balance({"tasks": [{"result": []}]}) is None
    assert parse_balance({}) is None


def test_estimate_cost_known_and_unknown():
    assert estimate_cost("serp") == 0.002
    assert estimate_cost("nonexistent") is None


def test_format_estimate():
    assert "per call" in format_estimate("backlinks")
    assert format_estimate("appendix") == "Estimated cost: free"
    assert format_estimate("nope") is None
