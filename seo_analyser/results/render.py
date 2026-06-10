"""Render a parsed DataForSEO response as a friendly summary + table."""
from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from seo_analyser.results.detect import (
    extract_html, extract_links, extract_message_text, friendly_error, items_table,
    parse_response, sanitize_for_preview,
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

    rows = items_table(parsed.items)
    if rows:
        df = pd.DataFrame(rows)
        ordered = [c for c in _PRIORITY_COLS if c in df.columns]
        ordered += [c for c in df.columns if c not in ordered]
        st.dataframe(df[ordered], use_container_width=True, hide_index=True)
    elif parsed.ok:
        st.info("The request succeeded but returned no rows.")

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
