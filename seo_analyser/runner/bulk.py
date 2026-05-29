"""Helpers for running an endpoint once per row of uploaded data."""
from __future__ import annotations

from typing import Any

MAX_ROWS = 50


def rows_to_payloads(base_payload: dict, field: str, values: list[Any]) -> list[dict]:
    """Build one payload per value, overriding `field` on a copy of base_payload.

    Blank values are skipped; the list is capped at MAX_ROWS.
    """
    payloads: list[dict] = []
    for value in values:
        if value in (None, ""):
            continue
        payload = dict(base_payload)
        payload[field] = value
        payloads.append(payload)
        if len(payloads) >= MAX_ROWS:
            break
    return payloads
