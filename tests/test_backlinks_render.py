"""Backlinks rendering logic tests (Linear IND-22..26), driven off real fixtures.

Fixtures in tests/fixtures/backlinks/ were captured live from DataForSEO by
scripts/backlinks_capture.py, so these pin the module against the API's actual
response shapes rather than hand-written guesses.
"""
import json
import pathlib

import pytest

from seo_analyser.results import backlinks as bl
from seo_analyser.results.detect import first_result, parse_response

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "backlinks"


def load(name: str) -> dict:
    return json.loads((FIXTURES / f"{name}.json").read_text())


def items_of(name: str) -> list[dict]:
    return parse_response(load(name)).items


# --- IND-22: Backlink Summary as profile metrics -------------------------

def test_summary_is_detected_and_yields_metrics():
    result0 = first_result(load("summary_live"))
    assert bl.is_summary(result0)
    metrics = dict(bl.summary_metrics(result0))
    assert "Backlinks" in metrics and "Referring domains" in metrics
    # Dofollow/nofollow domain split is derived from the nofollow count.
    assert metrics["Dofollow ref. domains"] + metrics["Nofollow ref. domains"] \
        == result0["referring_domains"]


def test_summary_scalar_table_excludes_nested_breakdowns():
    result0 = first_result(load("summary_live"))
    rows = bl.summary_scalar_table(result0)
    assert len(rows) == 1
    # referring_links_types etc. are dicts and must not appear as columns.
    assert "referring_links_types" not in rows[0]
    assert all(not isinstance(v, (dict, list)) for v in rows[0].values())


def test_backlink_rows_and_history_are_not_mistaken_for_summary():
    # history items carry backlinks/referring_domains too, but have a type.
    assert not bl.is_summary(items_of("history_live")[0])


# --- IND-23: Backlink Explorer rows --------------------------------------

def test_backlink_rows_lead_with_audit_columns():
    items = items_of("backlinks_live")
    assert bl.item_type(items) == "backlink"
    rows = bl.clean_rows(items, "backlink")
    cols = list(rows[0].keys())
    assert cols[:3] == ["url_from", "url_to", "anchor"]
    # Noisy machine fields are dropped from the first table.
    assert "url_from_https" not in cols and "text_pre" not in cols
    # No cell is ever a raw list/dict — list fields (attributes,
    # domain_from_platform_type) are joined to strings so the table stays flat.
    assert all(not isinstance(v, (list, dict))
               for r in rows for v in r.values())
    joined = [r["attributes"] for r in rows if isinstance(r.get("attributes"), str)]
    assert joined, "expected at least one row with joined attributes"


def test_clean_rows_preserve_all_items():
    items = items_of("backlinks_live")
    assert len(bl.clean_rows(items, "backlink")) == len(items)


# --- IND-24: referring domains / anchors / networks / pages --------------

@pytest.mark.parametrize("name,itype,lead", [
    ("anchors_live", "backlinks_anchor", "anchor"),
    ("referring_domains_live", "backlinks_referring_domain", "domain"),
    ("referring_networks_live", "backlinks_referring_network", "network_address"),
    ("domain_pages_live", "backlinks_domain_page", "page"),
    ("domain_pages_summary_live", "backlinks_page_summary", "url"),
])
def test_supporting_endpoints_render_ordered_tables(name, itype, lead):
    items = items_of(name)
    assert bl.item_type(items) == itype
    rows = bl.clean_rows(items, itype)
    assert rows and list(rows[0].keys())[0] == lead
    assert "type" not in rows[0]


# --- IND-25: competitor gap / intersection -------------------------------

def test_domain_intersection_flattens_to_opportunity_rows():
    resp = load("domain_intersection_live")
    parsed = parse_response(resp)
    result0 = first_result(resp)
    rows = bl.flatten_intersection(parsed.items, result0.get("targets") or {}, "domain")
    assert rows, "intersection must not render empty (the IND-21 gotcha)"
    row = rows[0]
    assert "referring_domain" in row
    # One 'backlinks → <target>' column per compared target.
    assert any(k.startswith("backlinks →") for k in row)


def test_page_intersection_flattens_with_link_counts():
    resp = load("page_intersection_live")
    parsed = parse_response(resp)
    result0 = first_result(resp)
    rows = bl.flatten_intersection(parsed.items, result0.get("targets") or {}, "page")
    assert rows
    assert any(k.startswith("links →") for k in rows[0])


def test_competitors_lead_columns():
    items = items_of("competitors_live")
    assert bl.item_type(items) == "backlinks_competitors"
    rows = bl.clean_rows(items, "backlinks_competitors")
    assert list(rows[0].keys())[:3] == ["target", "rank", "intersections"]


# --- IND-26: history and timeseries --------------------------------------

@pytest.mark.parametrize("name,itype", [
    ("timeseries_summary_live", "backlinks_timeseries_summary"),
    ("timeseries_new_lost_summary_live", "backlinks_timeseries_new_lost_summary"),
    ("history_live", "backlinks_history"),
])
def test_timeseries_have_date_and_chartable_columns(name, itype):
    items = items_of(name)
    assert bl.item_type(items) == itype
    rows = bl.timeseries_rows(items)
    assert rows and list(rows[0].keys())[0] == "date"
    chart_cols = bl.timeseries_columns(itype, list(rows[0].keys()))
    assert chart_cols, "at least one numeric series must be chartable"
    assert "date" not in chart_cols


def test_new_lost_separates_new_and_lost_series():
    cols = bl.timeseries_columns(
        "backlinks_timeseries_new_lost_summary",
        ["date", "new_backlinks", "lost_backlinks", "new_referring_domains"],
    )
    assert "new_backlinks" in cols and "lost_backlinks" in cols


# --- IND-27: bulk workflows ----------------------------------------------

@pytest.mark.parametrize("name", [
    "bulk_ranks_live", "bulk_backlinks_live", "bulk_referring_domains_live",
    "bulk_new_lost_backlinks_live", "bulk_new_lost_referring_domains_live",
])
def test_typeless_bulk_rows_detected_and_target_first(name):
    items = items_of(name)
    assert bl.is_bulk_rows(items)
    rows = bl.bulk_rows(items)
    assert list(rows[0].keys())[0] == "target"


def test_bulk_spam_score_uses_typed_lead_columns():
    # bulk_spam_score carries a type, so it goes through clean_rows, not is_bulk_rows.
    items = items_of("bulk_spam_score_live")
    assert bl.item_type(items) == "backlinks_bulk_spam_score"
    assert not bl.is_bulk_rows(items)
    rows = bl.clean_rows(items, "backlinks_bulk_spam_score")
    assert list(rows[0].keys())[:2] == ["target", "spam_score"]


def test_backlink_explorer_rows_are_not_mistaken_for_bulk():
    # backlinks_live rows have a 'target'-free shape and a type; must not match.
    assert not bl.is_bulk_rows(items_of("backlinks_live"))


def test_clean_targets_drops_blanks_and_duplicates_in_order():
    unique, blanks, dupes = bl.clean_targets(
        ["a.com", "", "b.com", "a.com", "  ", " b.com "])
    assert unique == ["a.com", "b.com"]
    assert blanks == 2 and dupes == 2


# --- IND-25 root cause: deep-convert nested SDK model objects -------------

class _FakeModel:
    """Stand-in for an SDK model whose to_dict leaves nested models unconverted."""
    def __init__(self, data):
        self._data = data

    def to_dict(self):
        return self._data


def test_deep_plain_converts_nested_model_objects():
    from seo_analyser.runner.live import _deep_plain
    # Mirrors the intersection shape: a dict-of-model field to_dict leaves alone.
    resp = {"tasks": [{"result": [{"items": [
        {"domain_intersection": {"1": _FakeModel({"target": "a.com", "backlinks": 5})}}
    ]}]}]}
    plain = _deep_plain(resp)
    nested = plain["tasks"][0]["result"][0]["items"][0]["domain_intersection"]["1"]
    assert nested == {"target": "a.com", "backlinks": 5}
    # Result must be JSON-serialisable (the store would otherwise stringify it).
    json.dumps(plain)
