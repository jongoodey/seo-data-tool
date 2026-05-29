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


@dataclass
class FieldSpec:
    name: str
    kind: str            # "text" | "int" | "float" | "bool" | "select" | "list" | "nested"
    description: str = ""
    default: Any = None
    choices: list[str] = field(default_factory=list)
    min: int | None = None
    max: int | None = None


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
    """Return (kind, inner_for_list)."""
    inner = _base_type(annotation)
    origin = typing.get_origin(inner)
    if origin in (list, typing.List):
        return "list", inner
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
    for fname, finfo in model.model_fields.items():
        desc = finfo.description or ""
        default = finfo.default
        kind, _inner = _kind_for(finfo.annotation)
        choices = extract_choices(desc)
        lo, hi = extract_range(desc)
        if kind == "text" and choices:
            kind = "select"
        specs.append(
            FieldSpec(
                name=fname, kind=kind, description=desc,
                default=default, choices=choices, min=lo, max=hi,
            )
        )
    return specs
