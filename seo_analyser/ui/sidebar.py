"""Sidebar: credentials + family/endpoint picker."""
from __future__ import annotations

import streamlit as st

from seo_analyser.auth import Credentials, from_env
from seo_analyser.registry import catalogue


def render_sidebar() -> tuple[Credentials, str | None, str | None]:
    env = from_env()
    with st.sidebar:
        st.header("DataForSEO credentials")
        login = st.text_input("Login", value=env.login)
        password = st.text_input("Password", value=env.password, type="password")
        creds = Credentials(login=login, password=password)

        st.header("Endpoint")
        family = st.selectbox("API family", catalogue.families())
        endpoints = catalogue.endpoints_for(family)
        names = [e.name for e in endpoints]
        endpoint_name = st.selectbox("Endpoint", names) if names else None
    return creds, family, endpoint_name
