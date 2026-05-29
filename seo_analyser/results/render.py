"""Render a parsed DataForSEO response as a friendly summary + table."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from seo_analyser.results.detect import extract_message_text, items_table, parse_response

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


def render_result(resp: dict) -> None:
    parsed = parse_response(resp)

    if not parsed.ok:
        msg = parsed.status_message or f"status code {parsed.status_code}"
        st.error(f"DataForSEO returned an error: {msg}")

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

    rows = items_table(parsed.items)
    if rows:
        df = pd.DataFrame(rows)
        ordered = [c for c in _PRIORITY_COLS if c in df.columns]
        ordered += [c for c in df.columns if c not in ordered]
        st.dataframe(df[ordered], use_container_width=True, hide_index=True)
    elif parsed.ok:
        st.info("The request succeeded but returned no rows.")

    with st.expander("Raw JSON response"):
        st.json(resp)
