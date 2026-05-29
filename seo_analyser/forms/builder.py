"""Render FieldSpecs as Streamlit widgets and collect a payload dict."""
from __future__ import annotations

from typing import Any

import streamlit as st

from seo_analyser.forms.widgets import FieldSpec, fields_for
from seo_analyser.labels import humanize

# Fields most users reach for first; everything else goes under "Advanced options".
_COMMON_FIELDS = {
    "keyword", "keywords", "target", "domain", "url",
    "location_name", "language_name", "location_code", "language_code",
    "device", "depth", "limit",
    "prompt", "user_prompt", "message", "model_name",
}


def render_form(
    model: type,
    key_prefix: str,
    dynamic_choices: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """Render common fields up front and the rest behind an expander.

    `dynamic_choices` maps a field name to a list of options sourced at runtime
    (e.g. model_name from the models endpoint); such fields render as dropdowns.
    Returns {field_name: value} with empty values dropped.
    """
    dynamic_choices = dynamic_choices or {}
    specs = fields_for(model)
    common = [s for s in specs if s.name in _COMMON_FIELDS]
    advanced = [s for s in specs if s.name not in _COMMON_FIELDS]
    if not common:  # nothing well-known — don't bury the whole form
        common, advanced = advanced, []

    payload: dict[str, Any] = {}
    for spec in common:
        _collect(spec, key_prefix, payload, dynamic_choices)
    if advanced:
        with st.expander(f"Advanced options ({len(advanced)})"):
            for spec in advanced:
                _collect(spec, key_prefix, payload, dynamic_choices)
    return payload


def _collect(
    spec: FieldSpec,
    key_prefix: str,
    payload: dict[str, Any],
    dynamic_choices: dict[str, list[str]],
) -> None:
    value = _render_field(
        spec,
        key=f"{key_prefix}.{spec.name}",
        choices_override=dynamic_choices.get(spec.name),
    )
    if value not in (None, "", []):
        payload[spec.name] = value


_BOOL_OPTIONS = ["", "true", "false"]


def bool_from_choice(choice: str) -> bool | None:
    """Map a tri-state dropdown choice to a bool or None (unset).

    Optional API booleans must NOT be sent when untouched — DataForSEO rejects
    conditionally-valid fields (e.g. force_web_search) when sent as a bare false.
    """
    if choice == "true":
        return True
    if choice == "false":
        return False
    return None


def _render_field(spec: FieldSpec, key: str, choices_override: list[str] | None = None) -> Any:
    help_text = spec.description or None
    label = humanize(spec.name)
    if choices_override:
        return st.selectbox(label, [""] + list(choices_override), help=help_text, key=key) or None
    if spec.kind == "bool":
        return bool_from_choice(st.selectbox(label, _BOOL_OPTIONS, help=help_text, key=key))
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
