"""Optional app password gate for the public deployment.

When the APP_PASSWORD environment variable is set (Railway), visitors must
enter that passphrase once per session before the app renders. This is what
makes it safe to also set the DataForSEO credentials as server env vars
(user_name/password), which pre-fill the sidebar and survive every deploy —
without the gate, a public URL with pre-filled keys would let any stranger
spend the account balance.
"""
from __future__ import annotations

import hmac
import os

import streamlit as st


def check_app_password(entered: str, required: str) -> bool:
    """True when access should be granted. No password configured = open."""
    if not required:
        return True
    return bool(entered) and hmac.compare_digest(entered, required)


def gate_passed() -> bool:
    """Render the gate if needed; True when the visitor may see the app."""
    required = os.environ.get("APP_PASSWORD", "").strip()
    if not required:
        return True
    if st.session_state.get("gate_ok"):
        return True
    st.title("🔍 SEO Analyzer Tool")
    entered = st.text_input("App password", type="password",
                            help="Set by the site owner (APP_PASSWORD).")
    if entered:
        if check_app_password(entered, required):
            st.session_state["gate_ok"] = True
            st.rerun()
        else:
            st.error("Wrong password.")
    return False
