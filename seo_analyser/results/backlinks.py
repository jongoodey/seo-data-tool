"""Backlinks-specific detection and table shaping (Linear IND-22..26).

The generic renderer (results/render.py) flattens any DataForSEO response to a
scalar table. That is unreadable for the Backlinks family: summary responses are
one wide metrics blob, backlink rows carry ~45 columns in API order, and the
intersection/timeseries endpoints nest their useful data. This module turns each
recognised Backlinks shape into an ordered, reporting-friendly table (plus, for
summaries, a metrics list, and for timeseries, a chart frame).

Pure logic only — no Streamlit import — so every shape is unit-testable against
the captured fixtures in tests/fixtures/backlinks/.
"""
from __future__ import annotations

from typing import Any

# The DataForSEO item ``type`` string is the reliable discriminator; summaries
# carry no items and are matched on shape instead (see is_summary).
LEAD_COLUMNS: dict[str, list[str]] = {
    # IND-23 — Backlink Explorer: source page, target, anchor, then link quality.
    "backlink": [
        "url_from", "url_to", "anchor", "dofollow", "item_type",
        "domain_from_rank", "page_from_rank", "rank", "backlink_spam_score",
        "first_seen", "last_seen", "is_new", "is_lost", "attributes",
        "url_to_status_code", "domain_from_platform_type", "domain_from_country",
        "page_from_title", "page_from_language",
    ],
    # IND-24 — supporting audit endpoints.
    "backlinks_anchor": [
        "anchor", "backlinks", "referring_domains", "referring_main_domains",
        "rank", "backlinks_spam_score", "first_seen", "lost_date",
        "referring_domains_nofollow", "broken_backlinks",
    ],
    "backlinks_referring_domain": [
        "domain", "backlinks", "referring_domains", "rank",
        "backlinks_spam_score", "first_seen", "lost_date",
        "referring_domains_nofollow", "broken_backlinks",
    ],
    "backlinks_referring_network": [
        "network_address", "backlinks", "referring_domains",
        "referring_main_domains", "rank", "first_seen", "lost_date",
    ],
    "backlinks_domain_page": [
        "page", "status_code", "first_visited", "fetch_time",
        "media_type", "size", "server",
    ],
    "backlinks_page_summary": [
        "url", "backlinks", "referring_domains", "rank",
        "backlinks_spam_score", "first_seen", "lost_date",
        "referring_domains_nofollow", "broken_backlinks",
    ],
    # IND-25 — competitor overlap.
    "backlinks_competitors": ["target", "rank", "intersections"],
    # IND-27 — bulk spam score carries a type; other bulk shapes don't.
    "backlinks_bulk_spam_score": ["target", "spam_score"],
}

# IND-27 — the bulk endpoints that return {target, <metric>...} with no `type`
# key. Detection is tight (every non-target key must be a known bulk metric) so
# other families' target-keyed rows aren't mistaken for these.
BULK_METRIC_KEYS = {
    "rank", "backlinks", "spam_score",
    "referring_domains", "referring_domains_nofollow",
    "referring_main_domains", "referring_main_domains_nofollow",
    "new_backlinks", "lost_backlinks",
    "new_referring_domains", "lost_referring_domains",
    "new_referring_main_domains", "lost_referring_main_domains",
}

# Fields never worth showing in the first table (kept in the raw JSON).
_NOISE: dict[str, set[str]] = {
    "backlink": {
        "url_from_https", "url_to_https", "tld_from", "domain_from_is_ip",
        "domain_from_ip", "page_from_encoding", "page_from_size", "prev_seen",
        "original", "alt", "image_url", "text_pre", "text_post",
        "semantic_location", "links_count", "group_count", "is_indirect_link",
        "indirect_link_path", "ranked_keywords_info", "is_broken",
        "page_from_external_links", "page_from_internal_links",
        "page_from_status_code", "url_to_redirect_target", "url_to_spam_score",
        "type", "mode", "custom_mode",
    },
}
# Everything else: drop the API discriminator 'type' from the visible table.
_GLOBAL_NOISE = {"type"}

# List-valued cells worth keeping as a comma-joined string rather than dropping.
_JOINABLE = {"attributes", "domain_from_platform_type", "dofollow_and_nofollow"}

TIMESERIES_TYPES = {
    "backlinks_timeseries_summary",
    "backlinks_timeseries_new_lost_summary",
    "backlinks_history",
}

_SCALAR = (str, int, float, bool)


def item_type(items: list[dict]) -> str | None:
    """The shared ``type`` of a list of items, or None if mixed/absent."""
    types = {it.get("type") for it in items if isinstance(it, dict)}
    if len(types) == 1:
        return next(iter(types))
    return None


def is_summary(result0: dict) -> bool:
    """A Backlink Summary result: metrics live on result[0], with no item type."""
    return (
        isinstance(result0, dict)
        and result0.get("type") is None
        and "backlinks" in result0
        and "referring_domains" in result0
        and "target" in result0
    )


# Ordered (label, key) pairs for the summary metric grid (IND-22).
_SUMMARY_METRICS: list[tuple[str, str]] = [
    ("Rank", "rank"),
    ("Backlinks", "backlinks"),
    ("Referring domains", "referring_domains"),
    ("Referring main domains", "referring_main_domains"),
    ("Referring pages", "referring_pages"),
    ("Referring IPs", "referring_ips"),
    ("Spam score", "backlinks_spam_score"),
    ("Broken backlinks", "broken_backlinks"),
]


def summary_metrics(result0: dict) -> list[tuple[str, Any]]:
    """Headline profile metrics for a summary, in display order.

    Adds derived dofollow/nofollow domain counts when the nofollow split exists.
    Only includes metrics actually present in the response.
    """
    out: list[tuple[str, Any]] = []
    for label, key in _SUMMARY_METRICS:
        if result0.get(key) is not None:
            out.append((label, result0[key]))
    dom = result0.get("referring_domains")
    nof = result0.get("referring_domains_nofollow")
    if isinstance(dom, int) and isinstance(nof, int):
        out.append(("Dofollow ref. domains", dom - nof))
        out.append(("Nofollow ref. domains", nof))
    return out


def summary_scalar_table(result0: dict) -> list[dict]:
    """The remaining scalar summary fields as a one-row table (nested breakdowns
    such as referring_links_types stay in the raw JSON)."""
    shown = {k for _, k in _SUMMARY_METRICS} | {
        "referring_domains", "referring_domains_nofollow", "type"}
    row = {k: v for k, v in result0.items()
           if isinstance(v, _SCALAR) and k not in shown}
    return [row] if row else []


def _cell(value: Any) -> Any:
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return value


def clean_rows(items: list[dict], itype: str) -> list[dict]:
    """Order and prune columns for a known Backlinks item type (IND-23/24/25).

    Lead columns come first in a stable order; remaining scalar (and a few
    joinable list) columns follow; noise and nested structures are dropped so
    the audit-relevant fields lead. Used for both the table and CSV export.
    """
    lead = LEAD_COLUMNS.get(itype, [])
    noise = _NOISE.get(itype, set()) | _GLOBAL_NOISE
    rows: list[dict] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        row: dict[str, Any] = {}
        for col in lead:
            if col in it:
                row[col] = _cell(it[col])
        for key, value in it.items():
            if key in row or key in noise or key in lead:
                continue
            if isinstance(value, _SCALAR) or value is None:
                row[key] = value
            elif key in _JOINABLE and isinstance(value, list):
                row[key] = _cell(value)
        rows.append(row)
    return rows


def flatten_intersection(items: list[dict], targets: dict, kind: str) -> list[dict]:
    """Flatten domain_/page_intersection items into one opportunity row each.

    Each item nests per-target data under numbered keys ("1", "2", …) that map
    to the queried targets via result_meta['targets']. domain_intersection nests
    a single object per target; page_intersection nests a list of backlinks — we
    surface the first source page and a per-target link count. Without this the
    generic renderer shows an empty table (the row's own fields are all nested).
    """
    field = "domain_intersection" if kind == "domain" else "page_intersection"
    labels = {k: str(v) for k, v in (targets or {}).items()}
    rows: list[dict] = []
    for it in items:
        nested = it.get(field) or {}
        if not isinstance(nested, dict) or not nested:
            continue
        row: dict[str, Any] = {}
        first = _first_intersection_entry(nested)
        if kind == "domain":
            row["referring_domain"] = (first or {}).get("target")
            row["rank"] = (first or {}).get("rank")
        else:
            row["referring_page"] = (first or {}).get("url_from")
            row["referring_domain"] = (first or {}).get("domain_from")
        for key in sorted(nested, key=_as_int):
            label = labels.get(key, f"target {key}")
            entry = nested[key]
            if kind == "domain" and isinstance(entry, dict):
                row[f"backlinks → {label}"] = entry.get("backlinks")
            elif kind == "page" and isinstance(entry, list):
                row[f"links → {label}"] = len(entry)
        rows.append(row)
    return rows


def _as_int(key: str) -> int:
    try:
        return int(key)
    except (TypeError, ValueError):
        return 0


def _first_intersection_entry(nested: dict):
    for key in sorted(nested, key=_as_int):
        entry = nested[key]
        if isinstance(entry, dict):
            return entry
        if isinstance(entry, list) and entry and isinstance(entry[0], dict):
            return entry[0]
    return None


def timeseries_columns(itype: str, present: list[str]) -> list[str]:
    """Which numeric series to chart for a timeseries type, in a sensible order.

    Returns only columns present in the data, excluding the date/type keys.
    """
    preferred = {
        "backlinks_timeseries_summary": [
            "backlinks", "referring_domains", "referring_pages"],
        "backlinks_timeseries_new_lost_summary": [
            "new_backlinks", "lost_backlinks",
            "new_referring_domains", "lost_referring_domains"],
        "backlinks_history": [
            "backlinks", "referring_domains", "new_backlinks", "lost_backlinks"],
    }.get(itype, [])
    return [c for c in preferred if c in present]


def is_bulk_rows(items: list[dict]) -> bool:
    """A typeless bulk result: every row is {target, <known bulk metric>...}."""
    if not items:
        return False
    for it in items:
        if not isinstance(it, dict) or it.get("type") is not None or "target" not in it:
            return False
        extras = set(it) - {"target"}
        if not extras or not extras <= BULK_METRIC_KEYS:
            return False
    return True


def bulk_rows(items: list[dict]) -> list[dict]:
    """Bulk rows with 'target' pinned to the first column (IND-27)."""
    rows: list[dict] = []
    for it in items:
        scalars = {k: v for k, v in it.items() if isinstance(v, _SCALAR)}
        if "target" in scalars:
            scalars = {"target": scalars.pop("target"), **scalars}
        rows.append(scalars)
    return rows


def clean_targets(values) -> tuple[list[str], int, int]:
    """Drop blanks and duplicate targets, preserving first-seen order (IND-27).

    Returns (unique_targets, n_blanks_dropped, n_duplicates_dropped) so the UI
    can tell the user what it removed before a paid bulk call.
    """
    seen: set[str] = set()
    unique: list[str] = []
    blanks = dupes = 0
    for value in values or []:
        if not (isinstance(value, str) and value.strip()):
            blanks += 1
            continue
        cleaned = value.strip()
        if cleaned in seen:
            dupes += 1
            continue
        seen.add(cleaned)
        unique.append(cleaned)
    return unique, blanks, dupes


def timeseries_rows(items: list[dict]) -> list[dict]:
    """Scalar rows for a timeseries table, 'date' first, type dropped."""
    rows: list[dict] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        row = {k: v for k, v in it.items()
               if isinstance(v, _SCALAR) and k != "type"}
        if "date" in row:
            row = {"date": row.pop("date"), **row}
        rows.append(row)
    return rows
