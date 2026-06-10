"""Welcome screen: maps common SEO jobs to pre-chosen endpoints.

A junior SEO should not need to know DataForSEO's API vocabulary to start;
each shortcut jumps straight to a curated endpoint (titles/descriptions for
these live in registry/overrides.yml).
"""
from __future__ import annotations

import streamlit as st

NAV_KEY = "nav_target"

# (button label, one-line blurb, family, endpoint)
SHORTCUTS = [
    ("Check Google rankings", "Top organic results for a keyword",
     "serp", "google_organic_live_advanced"),
    ("See Google's AI Overview", "Google's AI answer for a query, with sources",
     "serp", "google_ai_mode_live_advanced"),
    ("Ask ChatGPT", "Send a prompt; see the answer and its cited sources",
     "ai_optimization", "chat_gpt_llm_responses_live"),
    ("Keyword search volumes", "Monthly volume, competition and CPC",
     "keywords_data", "google_ads_search_volume_live"),
    ("Check backlinks", "Top-level backlink metrics for any domain",
     "backlinks", "summary_live"),
    ("Keywords a site ranks for", "Positions and volumes for any domain",
     "dataforseo_labs", "google_ranked_keywords_live"),
    ("Audit a page", "Instant on-page SEO checks for a single URL",
     "on_page", "instant_pages"),
    ("Ask Claude", "Send a prompt to an Anthropic Claude model",
     "ai_optimization", "claude_llm_responses_live"),
]


def render_home() -> None:
    st.markdown("#### What do you want to do?")
    st.caption("Pick a job below, or search all endpoints from the sidebar.")
    cols = st.columns(2)
    for i, (label, blurb, family, endpoint) in enumerate(SHORTCUTS):
        with cols[i % 2]:
            if st.button(label, key=f"home.{family}.{endpoint}", use_container_width=True):
                st.session_state[NAV_KEY] = (family, endpoint)
                st.rerun()
            st.caption(blurb)
