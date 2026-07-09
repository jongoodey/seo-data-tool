"""Render FieldSpecs as Streamlit widgets and collect a payload dict."""
from __future__ import annotations

import re
from typing import Any

import streamlit as st

from seo_analyser.forms.hints import hint_for
from seo_analyser.forms.validators import looks_like_domain
from seo_analyser.forms.widgets import RENDERABLE_ITEM_MODELS, FieldSpec, fields_for
from seo_analyser.labels import humanize
from seo_analyser.presets import presets_for

_OTHER = "Other (type a value)…"

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
    family: str = "",
) -> dict[str, Any]:
    """Render common fields up front and the rest behind an expander.

    `dynamic_choices` maps a field name to a list of options sourced at runtime
    (e.g. model_name from the models endpoint); such fields render as dropdowns.
    `family` lets fields pick up plain-English hints (forms/hints.py).
    Returns {field_name: value} with empty values dropped.
    """
    dynamic_choices = dynamic_choices or {}
    specs = fields_for(model)
    common, advanced = split_common_advanced(specs)

    payload: dict[str, Any] = {}
    for spec in common:
        _collect(spec, key_prefix, payload, dynamic_choices, family)
    if advanced:
        with st.expander(f"Advanced options ({len(advanced)})"):
            for spec in advanced:
                _collect(spec, key_prefix, payload, dynamic_choices, family)
    return payload


def split_common_advanced(specs: list[FieldSpec]) -> tuple[list[FieldSpec], list[FieldSpec]]:
    """Partition fields into up-front vs Advanced.

    Required/conditional and well-known fields go up front, except a *_code field
    whose *_name twin is on the same form: names are friendlier, so the code twin
    moves to Advanced even though the API marks it conditional.
    """
    names = {s.name for s in specs}

    def is_upfront(spec: FieldSpec) -> bool:
        if spec.name in ("location_code", "language_code") \
                and spec.name.replace("_code", "_name") in names:
            return False
        return spec.name in _COMMON_FIELDS or spec.requirement in ("required", "conditional")

    common = [s for s in specs if is_upfront(s)]
    advanced = [s for s in specs if not is_upfront(s)]
    if not common:  # nothing well-known — don't bury the whole form
        return advanced, []
    return common, advanced


def _collect(
    spec: FieldSpec,
    key_prefix: str,
    payload: dict[str, Any],
    dynamic_choices: dict[str, list[str]],
    family: str = "",
) -> None:
    value = _render_field(
        spec,
        key=f"{key_prefix}.{spec.name}",
        choices_override=dynamic_choices.get(spec.name),
        hint=hint_for(family, spec.name),
    )
    if value not in (None, "", []):
        payload[spec.name] = value


_BOOL_OPTIONS = ["", "true", "false"]

# Dict-typed API fields that are really numbered lists ({"1": ..., "2": ...}):
# the DataForSEO intersection-style inputs. Other dict fields stay non-editable.
_NUMBERED_DICT_FIELDS = {"targets", "pages", "app_ids", "asins"}


def numbered_targets(entries: list[str]) -> dict[str, str]:
    """Build the {"1": target, "2": target} dict intersection endpoints expect."""
    return {str(i): entry for i, entry in enumerate(entries, start=1)}


def llm_mention_target(entry: str) -> dict:
    """Build the typed target object the AI-visibility (LLM Mentions) API expects.

    The API wants a list of {"type": "domain"|"keyword", ...} objects, but a
    junior shouldn't have to know that: anything that looks like a domain
    (however pasted — with https://, www., or a trailing path) becomes a domain
    target; everything else is searched as a keyword phrase.
    """
    cleaned = entry.strip()
    host = re.sub(r"^https?://", "", cleaned, flags=re.I)
    host = host.split("/", 1)[0].split("?", 1)[0]
    if host.lower().startswith("www."):
        host = host[4:]
    if looks_like_domain(host):
        return {"type": "domain", "domain": host}
    return {"type": "keyword", "keyword": cleaned}


def decorate_label(spec: FieldSpec) -> str:
    """Append a plain-language requirement/default marker to a field label."""
    bits: list[str] = []
    if spec.requirement == "required":
        bits.append("required")
    elif spec.requirement == "conditional":
        bits.append(f"required unless {humanize(spec.partner)} set" if spec.partner else "conditional")
    elif spec.requirement == "dependent":
        bits.append(f"only with {humanize(spec.partner)}" if spec.partner else "optional")
    elif spec.requirement == "optional":
        bits.append("optional")
    if spec.default_hint:
        bits.append(f"default: {spec.default_hint}")
    base = humanize(spec.name)
    return f"{base}  ·  {', '.join(bits)}" if bits else base


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


def _coerce(value: Any, kind: str) -> Any:
    """Cast a chosen/typed value to int when the field expects an int."""
    if kind == "int" and value not in (None, ""):
        try:
            return int(value)
        except (ValueError, TypeError):
            return value
    return value


# Sensible starting values for quick-pick dropdowns (a beginner shouldn't have
# to discover that language is effectively mandatory).
_DEFAULT_CHOICES = {"language_name": "English"}


def _render_combobox(spec: FieldSpec, label: str, help_text, key: str,
                     presets: list[tuple[str, Any]]) -> Any:
    """Dropdown of common presets plus an 'Other' option for free text."""
    by_label = {lbl: val for lbl, val in presets}
    options = [""] + list(by_label) + [_OTHER]
    default = _DEFAULT_CHOICES.get(spec.name)
    index = options.index(default) if default in options else 0
    choice = st.selectbox(label, options, index=index, help=help_text, key=key)
    if choice == _OTHER:
        typed = st.text_input(f"{humanize(spec.name)} — custom value", key=f"{key}.custom")
        return _coerce((typed or "").strip() or None, spec.kind)
    if choice:
        return _coerce(by_label[choice], spec.kind)
    return None


def _render_field(spec: FieldSpec, key: str, choices_override: list[str] | None = None,
                  hint: str | None = None) -> Any:
    help_text = f"{hint}\n\n{spec.description}" if hint else (spec.description or None)
    label = decorate_label(spec)
    if choices_override:
        return st.selectbox(label, [""] + list(choices_override), help=help_text, key=key) or None
    presets = presets_for(spec.name)
    if presets:
        return _render_combobox(spec, label, help_text, key, presets)
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
    if spec.kind == "list_nested":
        if spec.item_model in RENDERABLE_ITEM_MODELS:
            raw = st.text_area(f"{label} (one per line)", help=help_text, key=key)
            return [llm_mention_target(line) for line in raw.splitlines() if line.strip()]
        st.caption(f"{label}: advanced nested field — not editable in this view yet.")
        return None
    if spec.kind == "dict":
        if spec.name in _NUMBERED_DICT_FIELDS:
            raw = st.text_area(f"{label} (one per line)", help=help_text, key=key)
            return numbered_targets(
                [line.strip() for line in raw.splitlines() if line.strip()]) or None
        st.caption(f"{label}: advanced nested field — not editable in this view yet.")
        return None
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
