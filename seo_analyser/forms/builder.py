"""Render FieldSpecs as Streamlit widgets and collect a payload dict."""
from __future__ import annotations

from typing import Any

import streamlit as st

from seo_analyser.forms.widgets import FieldSpec, fields_for


def render_form(model: type, key_prefix: str) -> dict[str, Any]:
    """Render one widget per field. Returns {field_name: value} with empties dropped."""
    payload: dict[str, Any] = {}
    for spec in fields_for(model):
        value = _render_field(spec, key=f"{key_prefix}.{spec.name}")
        if value not in (None, "", []):
            payload[spec.name] = value
    return payload


def _render_field(spec: FieldSpec, key: str) -> Any:
    help_text = spec.description or None
    label = spec.name
    if spec.kind == "bool":
        return st.checkbox(label, value=bool(spec.default), help=help_text, key=key)
    if spec.kind == "select":
        options = [""] + spec.choices
        return st.selectbox(label, options, help=help_text, key=key) or None
    if spec.kind == "int":
        return _number(label, spec, help_text, key, is_float=False)
    if spec.kind == "float":
        return _number(label, spec, help_text, key, is_float=True)
    if spec.kind == "list":
        raw = st.text_area(f"{label} (one per line)", help=help_text, key=key)
        return [line.strip() for line in raw.splitlines() if line.strip()]
    if spec.kind == "nested":
        st.caption(f"{label}: advanced nested field — not editable in this view yet.")
        return None
    return st.text_input(label, help=help_text, key=key) or None


def _number(label, spec: FieldSpec, help_text, key, is_float: bool):
    kwargs: dict[str, Any] = {"help": help_text, "key": key, "value": None}
    if spec.min is not None:
        kwargs["min_value"] = float(spec.min) if is_float else int(spec.min)
    if spec.max is not None:
        kwargs["max_value"] = float(spec.max) if is_float else int(spec.max)
    if not is_float:
        kwargs["step"] = 1
    return st.number_input(label, **kwargs)
