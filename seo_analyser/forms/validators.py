"""Client-side validation so obvious mistakes are caught before a paid call."""
from __future__ import annotations

import re

# Scheme + a host containing a dot, then anything (path optional).
_URL_RE = re.compile(r"^https?://[^\s/]+\.[^\s]+$", re.IGNORECASE)


def looks_like_url(value: str) -> bool:
    return isinstance(value, str) and bool(_URL_RE.match(value.strip()))


_ID_FIELDS = {"id", "task_id"}


def validate_payload(payload: dict) -> list[str]:
    """Return human-readable warnings for values that won't be accepted.

    Currently checks URL fields ('url' or '*_url') start with http:// or https://.
    """
    warnings: list[str] = []
    for key, value in payload.items():
        if (key == "url" or key.endswith("_url")) and isinstance(value, str) and value.strip():
            if not looks_like_url(value):
                warnings.append(
                    f"'{key}' should be a full URL starting with http:// or https:// "
                    f"(you entered '{value}')."
                )
    return warnings


def validate_required_fields(specs, payload: dict) -> list[str]:
    """Flag empty required fields before a paid call is wasted on 'Invalid Field'.

    Only unambiguous cases block: hard-required fields (the introspection already
    separates 'required unless X' into requirement == "conditional"), and
    conditional pairs where neither half is filled. Id fields are handled by
    validate_required_ids; nested fields aren't renderable; fields with an API
    default are fine to omit.
    """
    warnings: list[str] = []
    filled = {k for k, v in payload.items() if v not in (None, "", [])}
    seen_pairs: set[frozenset[str]] = set()
    for spec in specs:
        if spec.name in _ID_FIELDS or spec.kind == "nested" or spec.default_hint:
            continue
        if spec.requirement == "required" and spec.name not in filled:
            warnings.append(f"'{spec.name}' is required. Fill it in before running.")
        elif spec.requirement == "conditional" and spec.partner:
            pair = frozenset((spec.name, spec.partner))
            if pair in seen_pairs or filled & pair:
                continue
            seen_pairs.add(pair)
            warnings.append(
                f"Provide either '{spec.name}' or '{spec.partner}' before running.")
    return warnings


def validate_required_ids(specs, payload: dict) -> list[str]:
    """Flag a required task-id field that's empty before a (futile) call.

    `specs` is a list of FieldSpec. A required 'id'/'task_id' that's missing means
    the endpoint reads from a prior task — surface that instead of 'Task Not Found'.
    """
    warnings: list[str] = []
    for spec in specs:
        if spec.name in _ID_FIELDS and spec.requirement == "required" and not payload.get(spec.name):
            warnings.append(
                f"'{spec.name}' is required: this endpoint reads results from a prior task. "
                "Run the matching Task Post first, then paste its id here."
            )
    return warnings
