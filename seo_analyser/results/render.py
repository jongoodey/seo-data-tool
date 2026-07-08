"""Render a parsed DataForSEO response as a friendly summary + table."""
from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from seo_analyser.results import backlinks as bl
from seo_analyser.results.detect import (
    extract_html, extract_links, extract_message_text, first_result,
    friendly_error, items_table, parse_response, sanitize_for_preview,
)
from seo_analyser.results.export import to_csv_bytes, to_json_bytes

# Columns that, when present, read best left-to-right.
_PRIORITY_COLS = [
    "rank_group", "rank_absolute", "position", "type",
    "title", "domain", "url", "breadcrumb", "description",
    "keyword", "search_volume", "competition", "cpc",
    "keyword_difficulty", "etv", "rank", "spam_score",
]

# Meta fields worth surfacing as a one-line caption above the table.
_META_KEYS = [
    "keyword", "target", "location_code", "language_code",
    "se_domain", "total_count", "items_count", "se_results_count",
]


def render_result(resp: dict, endpoint: str = "result") -> None:
    parsed = parse_response(resp)

    if not parsed.ok:
        st.error("DataForSEO returned an error: "
                 + friendly_error(parsed.status_message, parsed.status_code))

    col1, col2, col3 = st.columns(3)
    col1.metric("Status", "OK" if parsed.ok else "Error")
    col2.metric("Results", f"{len(parsed.items):,}")
    col3.metric("Cost", f"${parsed.cost:.4f}")

    meta_bits = [
        f"**{k.replace('_', ' ')}:** {parsed.result_meta[k]}"
        for k in _META_KEYS
        if parsed.result_meta.get(k) not in (None, "")
    ]
    if meta_bits:
        st.caption("  ·  ".join(meta_bits))

    # LLM / AI overview answers nest their text — surface it prominently.
    answer = extract_message_text(parsed.items)
    if answer:
        st.markdown("#### Response")
        st.markdown(answer)

    links = extract_links(parsed.items)
    if links:
        st.markdown("**Sources**")
        for link in links:
            st.markdown(f"- [{link['title']}]({link['url']})")

    # HTML-returning endpoints (*_live_html, raw_html) — render it in-app.
    html = extract_html(resp)
    if html:
        st.markdown("#### Rendered HTML")
        tab_view, tab_source = st.tabs(["Preview", "Source"])
        with tab_view:
            st.caption("Scripts removed and links disabled for a safe preview. "
                       "Download for the full, interactive page.")
            components.html(sanitize_for_preview(html), height=600, scrolling=True)
        with tab_source:
            st.code(html[:20000] + ("\n…(truncated)" if len(html) > 20000 else ""),
                    language="html")
        stamp_html = datetime.now().strftime("%Y%m%d-%H%M%S")
        st.download_button(
            "Download HTML", html.encode("utf-8"),
            file_name=f"{endpoint}-{stamp_html}.html", mime="text/html",
        )

    # Backlinks family: metrics/chart/ordered tables. Falls back to the generic
    # table when the response isn't a recognised Backlinks shape.
    rows = _render_backlinks_body(resp, parsed)
    if rows is None:
        rows = _render_generic_table(parsed, answer)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    col_csv, col_json = st.columns(2)
    if rows:
        col_csv.download_button(
            "Download CSV", to_csv_bytes(rows),
            file_name=f"{endpoint}-{stamp}.csv", mime="text/csv",
        )
    col_json.download_button(
        "Download JSON", to_json_bytes(resp),
        file_name=f"{endpoint}-{stamp}.json", mime="application/json",
    )

    with st.expander("Raw JSON response"):
        st.json(resp)


def _dataframe(rows: list[dict], priority: list[str]) -> None:
    df = pd.DataFrame(rows)
    ordered = [c for c in priority if c in df.columns]
    ordered += [c for c in df.columns if c not in ordered]
    st.dataframe(df[ordered], use_container_width=True, hide_index=True)


def _render_generic_table(parsed, answer: str) -> list[dict]:
    rows = items_table(parsed.items)
    if answer:
        # The answer is already rendered above; an 8KB markdown blob in a table
        # cell would just bury the readable columns.
        rows = [{k: v for k, v in r.items() if k != "markdown"} for r in rows]
        rows = [r for r in rows if r]
    if rows:
        _dataframe(rows, _PRIORITY_COLS)
    elif parsed.ok:
        st.info("The request succeeded but returned no rows.")
    return rows


def _render_backlinks_body(resp: dict, parsed) -> list[dict] | None:
    """Render a recognised Backlinks shape; return its CSV rows, or None if the
    response isn't a Backlinks shape (caller then renders the generic table)."""
    result0 = first_result(resp)

    # Backlink Summary (IND-22): metrics on result[0], no item type.
    if bl.is_summary(result0):
        metrics = bl.summary_metrics(result0)
        _render_metric_grid(metrics)
        scalar_rows = bl.summary_scalar_table(result0)
        if scalar_rows:
            with st.expander("All summary fields"):
                _dataframe(scalar_rows, [])
        elif not metrics and parsed.ok:
            st.info("The request succeeded but returned no backlink profile.")
        return [{k: v for k, v in result0.items()
                 if isinstance(v, (str, int, float, bool))}]

    if not parsed.items:
        return None
    itype = bl.item_type(parsed.items)

    # Intersection (IND-25): nested per-target data, otherwise an empty table.
    if "domain_intersection" in parsed.items[0]:
        return _render_intersection(parsed.items, result0, "domain")
    if "page_intersection" in parsed.items[0]:
        return _render_intersection(parsed.items, result0, "page")

    # Timeseries / history (IND-26): chart + table.
    if itype in bl.TIMESERIES_TYPES:
        return _render_timeseries(parsed.items, itype)

    # Explorer / referring domains / anchors / networks / pages (IND-23/24/25).
    if itype in bl.LEAD_COLUMNS:
        rows = bl.clean_rows(parsed.items, itype)
        if rows:
            _dataframe(rows, bl.LEAD_COLUMNS[itype])
        elif parsed.ok:
            st.info("The request succeeded but returned no rows.")
        return rows

    # Bulk endpoints (IND-27): {target, metric...} rows, target first.
    if bl.is_bulk_rows(parsed.items):
        rows = bl.bulk_rows(parsed.items)
        _dataframe(rows, ["target"])
        return rows

    return None


def _render_metric_grid(metrics: list[tuple[str, object]]) -> None:
    if not metrics:
        return
    st.markdown("#### Backlink profile")
    per_row = 4
    for start in range(0, len(metrics), per_row):
        chunk = metrics[start:start + per_row]
        cols = st.columns(per_row)
        for col, (label, value) in zip(cols, chunk):
            shown = f"{value:,}" if isinstance(value, int) else value
            col.metric(label, shown)


def _render_intersection(items: list[dict], result0: dict, kind: str) -> list[dict]:
    targets = result0.get("targets") or {}
    rows = bl.flatten_intersection(items, targets, kind)
    if rows:
        st.caption("Referring domains/pages linking to the compared targets. "
                   "Each column shows the link count toward that target.")
        _dataframe(rows, ["referring_domain", "referring_page", "rank"])
    else:
        st.info("The request succeeded but found no overlap between the targets.")
    return rows


def _render_timeseries(items: list[dict], itype: str) -> list[dict]:
    rows = bl.timeseries_rows(items)
    if not rows:
        st.info("The request succeeded but returned no trend data.")
        return rows
    df = pd.DataFrame(rows)
    chart_cols = bl.timeseries_columns(itype, list(df.columns))
    if "date" in df.columns and chart_cols:
        st.line_chart(df.set_index("date")[chart_cols])
    _dataframe(rows, ["date"])
    return rows
