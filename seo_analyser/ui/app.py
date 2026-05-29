"""SEO Analyzer Tool — auto-generated DataForSEO gateway."""
from __future__ import annotations

import streamlit as st

from seo_analyser.ui.endpoint_page import render_endpoint_page
from seo_analyser.ui.sidebar import render_sidebar


def main() -> None:
    st.set_page_config(page_title="SEO Analyzer Tool", layout="wide")
    st.title("SEO Analyzer Tool")
    creds, family, endpoint_name = render_sidebar()
    if family and endpoint_name:
        render_endpoint_page(creds, family, endpoint_name)
    else:
        st.info("Pick an API family and endpoint from the sidebar to begin.")


if __name__ == "__main__":
    main()
