"""Map Pydantic request-model fields to UI-agnostic widget specs.

A FieldSpec is what the UI needs to render a widget; it carries no Streamlit
dependency so it can be unit-tested.
"""
from __future__ import annotations

import re
import types
import typing
from dataclasses import dataclass, field
from typing import Any

_CHOICE_RE = re.compile(r"possible values:?\s*([a-z0-9_]+(?:\s*,\s*[a-z0-9_]+)+)", re.I)
_MAX_RE = re.compile(r"max(?:imum)? value:?\s*(\d+)", re.I)
_RANGE_RE = re.compile(r"range:?\s*(\d+)\s*-\s*(\d+)", re.I)
_FROM_TO_RE = re.compile(r"from\s+(\d+)\s+to\s+(\d+)", re.I)
# Only trust clean default tokens (true/false/integer); skip messy concatenated prose.
_DEFAULT_RE = re.compile(r"default value:?\s*(true|false|\d+)", re.I)


@dataclass
class FieldSpec:
    name: str
    kind: str            # "text" | "int" | "float" | "bool" | "select" | "list" | "list_nested" | "dict" | "nested"
    description: str = ""
    default: Any = None
    choices: list[str] = field(default_factory=list)
    min: int | None = None
    max: int | None = None
    requirement: str = ""        # "required" | "conditional" | "optional" | ""
    partner: str | None = None   # for conditional fields, the alternative field name
    default_hint: str | None = None  # default value parsed from the description
    item_model: str | None = None    # for list_nested, the element model's class name


# list_nested element models the form knows how to build from plain text lines.
# Everything else renders as a "not editable yet" caption instead of silently
# sending strings the SDK rejects (the AI-visibility target bug, 2026-07-09).
RENDERABLE_ITEM_MODELS = {"BaseAiOptimizationLLmMentionsTargetElement"}


def extract_requirement(description: str) -> str:
    """Classify a field: required / conditional (one-of-a-pair) / dependent / optional.

    DataForSEO uses two OPPOSITE 'required field if' phrasings that must not be
    conflated (learned from backlinks_live blocking valid calls, 2026-07-09):
      "required field if you DON'T specify <partner>"  -> conditional: one of the
        pair is genuinely needed (location_name OR location_code).
      "required field if you (choose to) specify <partner>" -> dependent: needed
        only WHEN the optional partner is used (custom_mode's field/value);
        leaving both empty is a perfectly valid call.
    """
    low = (description or "").lower()
    if "optional field" in low:
        return "optional"
    if "required field" in low:
        if "don't specify" in low or "don’t specify" in low:
            return "conditional"
        if "required field if" in low:
            return "dependent"
        return "required"
    return ""


def resolve_partner(description: str, siblings: list[str]) -> str | None:
    """Find which sibling field a conditional clause points at.

    Descriptions are space-less ('...specify language_codeif you...'), so we match
    against real field names rather than regex-guessing the boundary.
    """
    text = description or ""
    for cand in sorted(siblings, key=len, reverse=True):
        if f"specify {cand}" in text or f"specify the {cand}" in text:
            return cand
    return None


def extract_default(description: str) -> str | None:
    m = _DEFAULT_RE.search(description or "")
    return m.group(1) if m else None


def extract_choices(description: str) -> list[str]:
    m = _CHOICE_RE.search(description or "")
    if not m:
        return []
    return [c.strip() for c in m.group(1).split(",") if c.strip()]


def extract_range(description: str) -> tuple[int | None, int | None]:
    text = description or ""
    m = _RANGE_RE.search(text) or _FROM_TO_RE.search(text)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = _MAX_RE.search(text)
    if m:
        return None, int(m.group(1))
    return None, None


def _base_type(annotation: Any) -> Any:
    """Strip Optional/Union and Annotated wrappers, but stop at list/List.

    Pydantic's StrictInt/StrictStr expand to ``Annotated[int, Strict()]`` whose
    ``__name__`` is ``"Annotated"``, so we must unwrap the metadata to reach the
    real scalar type. List types are preserved so the caller can detect them.
    """
    origin = typing.get_origin(annotation)
    if origin is typing.Union or origin is getattr(types, "UnionType", ()):
        non_none = [a for a in typing.get_args(annotation) if a is not type(None)]
        return _base_type(non_none[0]) if non_none else annotation
    if getattr(annotation, "__metadata__", None) is not None:  # Annotated[...]
        return _base_type(typing.get_args(annotation)[0])
    return annotation


def _kind_for(annotation: Any) -> tuple[str, Any]:
    """Return (kind, inner). For list_nested, inner is the element model class."""
    inner = _base_type(annotation)
    origin = typing.get_origin(inner)
    if origin in (list, typing.List):
        args = typing.get_args(inner)
        element = _base_type(args[0]) if args else None
        if hasattr(element, "model_fields"):  # list of pydantic models, not scalars
            return "list_nested", element
        return "list", inner
    if origin is dict:
        return "dict", inner
    name = getattr(inner, "__name__", str(inner)).lower()
    if "bool" in name:
        return "bool", inner
    if "int" in name:
        return "int", inner
    if "float" in name:
        return "float", inner
    return "text", inner


def fields_for(model: type) -> list[FieldSpec]:
    specs: list[FieldSpec] = []
    siblings = [n for n in model.model_fields if n != "additional_properties"]
    for fname, finfo in model.model_fields.items():
        if fname == "additional_properties":
            continue  # pydantic catch-all on every SDK model, not a real API field
        desc = finfo.description or ""
        default = finfo.default
        kind, inner = _kind_for(finfo.annotation)
        choices = extract_choices(desc)
        lo, hi = extract_range(desc)
        requirement = extract_requirement(desc)
        partner = (resolve_partner(desc, siblings)
                   if requirement in ("conditional", "dependent") else None)
        if kind == "text" and choices:
            kind = "select"
        specs.append(
            FieldSpec(
                name=fname, kind=kind, description=desc,
                default=default, choices=choices, min=lo, max=hi,
                requirement=requirement, partner=partner,
                default_hint=extract_default(desc),
                item_model=(getattr(inner, "__name__", None)
                            if kind == "list_nested" else None),
            )
        )
    return specs
