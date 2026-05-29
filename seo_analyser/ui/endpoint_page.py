"""Endpoint page: friendly header + auto-form + Run + rendered results."""
from __future__ import annotations

import streamlit as st

from seo_analyser.auth import Credentials
from seo_analyser.forms.builder import render_form
from seo_analyser.labels import titleize
from seo_analyser.registry import catalogue
from seo_analyser.results.render import render_result
from seo_analyser.runner.errors import RunError
from seo_analyser.runner.live import run_live


def render_endpoint_page(creds: Credentials, family: str, endpoint_name: str) -> None:
    meta = catalogue.find_endpoint(family, endpoint_name)
    if meta is None:
        st.warning("Select an endpoint from the sidebar.")
        return

    st.subheader(titleize(endpoint_name))
    st.caption(f"{titleize(family)}  ·  `{endpoint_name}`")

    if meta.is_task_based:
        st.info(
            "This is a task-based endpoint. Submitting starts a job that is polled "
            "for results — full polling support is coming in the next phase."
        )
    if meta.request_model is None:
        st.warning("This endpoint takes no inputs and isn't runnable yet.")
        return

    payload = render_form(meta.request_model, key_prefix=f"{family}.{endpoint_name}")

    if st.button("Run", type="primary"):
        with st.spinner("Calling DataForSEO..."):
            try:
                result = run_live(meta, payload, creds)
            except RunError as err:
                st.error(str(err))
                return
        render_result(result)
