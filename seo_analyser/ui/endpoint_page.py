"""Endpoint page: auto-form + Run + raw JSON result."""
from __future__ import annotations

import streamlit as st

from seo_analyser.auth import Credentials
from seo_analyser.forms.builder import render_form
from seo_analyser.registry import catalogue
from seo_analyser.runner.errors import RunError
from seo_analyser.runner.live import run_live


def render_endpoint_page(creds: Credentials, family: str, endpoint_name: str) -> None:
    meta = catalogue.find_endpoint(family, endpoint_name)
    if meta is None:
        st.warning("Select an endpoint from the sidebar.")
        return

    st.subheader(f"{family} · {endpoint_name}")
    if meta.is_task_based:
        st.info("This is a task-based endpoint. Task polling lands in Phase 2 — running it live may not return results yet.")
    if meta.request_model is None:
        st.warning("This endpoint takes no request body and isn't runnable in Phase 1.")
        return

    payload = render_form(meta.request_model, key_prefix=f"{family}.{endpoint_name}")

    if st.button("Run", type="primary"):
        with st.spinner("Calling DataForSEO..."):
            try:
                result = run_live(meta, payload, creds)
            except RunError as err:
                st.error(str(err))
                return
        st.success("Done.")
        st.json(result)
