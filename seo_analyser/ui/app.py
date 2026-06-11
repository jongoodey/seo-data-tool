"""SEO Analyzer Tool — auto-generated DataForSEO gateway."""
from __future__ import annotations

import streamlit as st

from seo_analyser.registry import catalogue
from seo_analyser.ui.endpoint_page import render_endpoint_page, render_shared_request
from seo_analyser.ui.gate import gate_passed
from seo_analyser.ui.home import NAV_KEY, render_home
from seo_analyser.ui.share import SHARE_KEY, decode_share
from seo_analyser.ui.sidebar import render_sidebar


def main() -> None:
    st.set_page_config(page_title="SEO Analyzer Tool", page_icon="🔍", layout="wide")
    if not gate_passed():
        return
    st.title("🔍 SEO Analyzer Tool")

    # Build the catalogue once, with feedback on the first (slow) load.
    if "catalogue_ready" not in st.session_state:
        with st.spinner("Loading the DataForSEO endpoint catalogue..."):
            catalogue.get_catalogue()
        st.session_state["catalogue_ready"] = True

    creds, family, endpoint_name = render_sidebar()

    if not creds.is_complete:
        st.info(
            "Enter your DataForSEO login and password in the sidebar to begin. "
            "Then pick an API family and an endpoint to run."
        )
        return

    shared = decode_share(st.query_params.get(SHARE_KEY, ""))
    if shared:
        render_shared_request(creds, shared)
        st.divider()

    if family and endpoint_name:
        st.session_state.pop(NAV_KEY, None)   # a sidebar choice overrides a shortcut
        render_endpoint_page(creds, family, endpoint_name)
    elif st.session_state.get(NAV_KEY):
        nav_family, nav_endpoint = st.session_state[NAV_KEY]
        render_endpoint_page(creds, nav_family, nav_endpoint)
    else:
        render_home()


if __name__ == "__main__":
    main()
