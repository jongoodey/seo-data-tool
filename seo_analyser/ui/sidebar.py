"""Sidebar: credentials + endpoint search / family+endpoint picker."""
from __future__ import annotations

import streamlit as st

from seo_analyser.auth import Credentials, from_env
from seo_analyser.billing.balance import account_balance
from seo_analyser.labels import family_label, titleize
from seo_analyser.registry import catalogue


def _render_balance(creds: Credentials) -> None:
    if "balance" not in st.session_state:
        with st.spinner("Checking balance..."):
            st.session_state["balance"] = account_balance(creds)
    balance = st.session_state["balance"]
    col_a, col_b = st.columns([3, 1])
    col_a.metric("Account balance", f"${balance:,.2f}" if balance is not None else "—")
    if col_b.button("↻", help="Refresh balance"):
        del st.session_state["balance"]
        st.rerun()


def render_sidebar() -> tuple[Credentials, str | None, str | None]:
    env = from_env()
    with st.sidebar:
        st.header("DataForSEO credentials")
        login = st.text_input("Login", value=env.login)
        password = st.text_input("Password", value=env.password, type="password")
        creds = Credentials(login=login, password=password)
        if creds.is_complete:
            st.caption("✓ Credentials loaded")
            _render_balance(creds)

        st.header("Choose an endpoint")
        query = st.text_input("Search all endpoints", key="sb.query",
                              placeholder="e.g. ai overview, keyword volume, backlinks")
        if query.strip():
            hits = catalogue.search_endpoints(query)
            if not hits:
                st.caption("No endpoints match.")
                return creds, None, None
            labels = {
                f"{family_label(e.family)} · {titleize(e.name)}": (e.family, e.name)
                for e in hits
            }
            chosen = st.selectbox(f"{len(hits)} matches", list(labels), key="sb.search_pick")
            family, endpoint_name = labels[chosen]
            return creds, family, endpoint_name

        family = st.selectbox("API family", catalogue.families(), format_func=family_label,
                              index=None, placeholder="Browse the API families...",
                              key="sb.family")
        if family is None:
            return creds, None, None
        endpoints = catalogue.endpoints_for(family)
        names = [e.name for e in endpoints]
        endpoint_name = st.selectbox("Endpoint", names, format_func=titleize,
                                     index=None, placeholder="Pick an endpoint...",
                                     key="sb.endpoint")
        st.caption(f"{len(names)} endpoints in {family_label(family)}")
    return creds, family, endpoint_name
