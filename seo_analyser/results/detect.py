"""Parse a DataForSEO response into a display-friendly shape.

DataForSEO responses follow a consistent envelope:

    {status_code, status_message, cost, tasks: [
        {status_code, status_message, cost, result: [
            {<scalar meta...>, items: [ {row}, {row} ]}
        ]}
    ]}

This module flattens that into a ParsedResult the UI can render without knowing
the envelope. It carries no Streamlit dependency so it can be unit-tested.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

_SCALAR = (str, int, float, bool)
_SUCCESS = 20000


@dataclass
class ParsedResult:
    ok: bool
    status_code: int | None
    status_message: str
    cost: float
    task_count: int
    result_meta: dict        # scalar fields from result[0], excluding items
    items: list[dict]        # the data rows
    raw: dict


def _scalars(d: dict) -> dict:
    return {k: v for k, v in d.items() if isinstance(v, _SCALAR) or v is None}


def parse_response(resp: dict) -> ParsedResult:
    if not isinstance(resp, dict):
        return ParsedResult(False, None, "Unrecognised response", 0.0, 0, {}, [], {"result": resp})

    status_code = resp.get("status_code")
    ok = status_code == _SUCCESS
    status_message = resp.get("status_message", "")
    cost = resp.get("cost") or 0.0
    tasks = resp.get("tasks") or []
    items: list[dict] = []
    result_meta: dict = {}

    if tasks:
        task = tasks[0] or {}
        t_status = task.get("status_code")
        if t_status is not None and t_status != _SUCCESS:
            ok = False
            status_message = task.get("status_message", status_message)
        cost = cost or task.get("cost") or 0.0
        results = task.get("result") or []
        if results:
            first = results[0] if isinstance(results[0], dict) else {}
            if isinstance(first.get("items"), list):
                items = [i for i in first["items"] if isinstance(i, dict)]
                result_meta = _scalars(first)
            else:
                # result entries are themselves the rows (e.g. summary endpoints)
                items = [r for r in results if isinstance(r, dict)]

    return ParsedResult(
        ok=ok,
        status_code=status_code,
        status_message=status_message,
        cost=float(cost or 0.0),
        task_count=len(tasks),
        result_meta=result_meta,
        items=items,
        raw=resp,
    )


def items_table(items: list[dict]) -> list[dict]:
    """Reduce each item to its scalar fields so it renders as a flat table."""
    return [_scalars(it) for it in items]
