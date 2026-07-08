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

import re
from dataclasses import dataclass, field
from typing import Any

_SCALAR = (str, int, float, bool)
_SUCCESS = 20000
_CLOSING_TAG_RE = re.compile(r"</[a-zA-Z]")
_SCRIPT_RE = re.compile(r"<script\b[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL)


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


_INVALID_FIELD_RE = re.compile(r"invalid field:?\s*'?([a-z0-9_]+)'?", re.I)


def friendly_error(status_message: str, status_code: int | None = None) -> str:
    """Translate DataForSEO error phrasing into instructions a beginner can act on.

    'Invalid Field' almost always means a required field was left empty, not that
    the value was wrong; say so, but keep the original message for power users.
    """
    msg = status_message or (f"status code {status_code}" if status_code else "unknown error")
    m = _INVALID_FIELD_RE.search(msg)
    if m:
        name = m.group(1)
        return (f"'{name}' is missing or not valid. Fill in the '{name}' field "
                f"above and run again. (API said: {msg})")
    low = msg.lower()
    if "task" in low and "not found" in low:
        return ("That task id was not found. The task may still be processing "
                "(wait a minute and fetch or run again), or the id may be mistyped. "
                f"(API said: {msg})")
    return msg


# Machine locators DataForSEO attaches to SERP items; never useful to a reader.
_NOISE_FIELDS = {"xpath", "rectangle"}


_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}")
_SERIES_DATE_KEYS = ("date", "date_from")
_CONTEXT_KEYS = ("keyword", "target", "title")


def extract_time_series(resp: Any, max_series: int = 6, min_points: int = 3) -> list[dict]:
    """Find plottable time series anywhere in a response, however nested.

    Recognises two row shapes inside arrays of dicts:
      {"year": 2025, "month": 7, "<metric>": <number>}          -> monthly points
      {"date"/"date_from": "2025-07-01...", "<metric>": <number>} -> dated points

    This covers monthly_searches (Google Ads / Labs keyword data), the AI keyword
    search-volume series, backlinks timeseries rows, and anything future-shaped
    the same way. Returns [{"label", "points": [(iso_date, value), ...]}] with
    points sorted chronologically; labels are prefixed with the nearest ancestor
    keyword/target so multi-keyword responses stay tellable-apart.
    """
    found: list[dict] = []
    seen_labels: set[str] = set()

    def context_label(stack: list) -> str:
        for node in reversed(stack):
            for key in _CONTEXT_KEYS:
                value = node.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()[:40]
        return ""

    def add_series(rows: list[dict], stack: list) -> None:
        sample = rows[0]
        has_ym = isinstance(sample.get("year"), int) and isinstance(sample.get("month"), int)
        date_key = None
        if not has_ym:
            date_key = next((k for k in _SERIES_DATE_KEYS
                             if isinstance(sample.get(k), str)
                             and _ISO_DATE_RE.match(sample[k])), None)
        if not (has_ym or date_key):
            return
        metric_keys = [k for k, v in sample.items()
                       if k not in ("year", "month") and k != date_key
                       and isinstance(v, (int, float)) and not isinstance(v, bool)]
        prefix = context_label(stack)
        for metric in metric_keys[:3]:
            if len(found) >= max_series:
                return
            points = []
            for row in rows:
                value = row.get(metric)
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    continue
                if has_ym and isinstance(row.get("year"), int):
                    month = row.get("month")
                    if not (isinstance(month, int) and 1 <= month <= 12):
                        continue
                    when = f"{row['year']:04d}-{month:02d}-01"
                elif date_key and isinstance(row.get(date_key), str):
                    when = str(row[date_key])[:10]
                else:
                    continue
                points.append((when, float(value)))
            if len(points) >= min_points:
                label = f"{prefix} · {metric}" if prefix else metric
                if label in seen_labels:
                    label = f"{label} ({len(found) + 1})"
                seen_labels.add(label)
                found.append({"label": label, "points": sorted(points)})

    def walk(node: Any, stack: list) -> None:
        if len(found) >= max_series:
            return
        if isinstance(node, dict):
            for value in node.values():
                walk(value, stack + [node])
        elif isinstance(node, list):
            dict_rows = [r for r in node if isinstance(r, dict)]
            if len(dict_rows) >= min_points and len(dict_rows) == len(node):
                add_series(dict_rows, stack)
            for value in node[:50]:
                walk(value, stack)

    walk(resp, [])
    return found


def items_table(items: list[dict]) -> list[dict]:
    """Reduce each item to its scalar fields so it renders as a flat table."""
    return [{k: v for k, v in _scalars(it).items() if k not in _NOISE_FIELDS}
            for it in items]


def first_result(resp: Any) -> dict:
    """The response's tasks[0].result[0] dict, or {} if absent.

    Summary metrics live here directly, and intersection endpoints keep their
    target map here, so renderers need it alongside the flattened items.
    """
    try:
        result0 = resp["tasks"][0]["result"][0]
    except (KeyError, IndexError, TypeError):
        return {}
    return result0 if isinstance(result0, dict) else {}


def looks_like_html(value: Any) -> bool:
    """Heuristic: a longish string with several closing tags is renderable HTML."""
    return (
        isinstance(value, str)
        and len(value) > 50
        and len(_CLOSING_TAG_RE.findall(value)) >= 3
    )


def strip_scripts(html: str) -> str:
    """Remove <script> blocks so an embedded preview can't navigate or run JS."""
    return _SCRIPT_RE.sub("", html or "")


# Disable link clicks in the preview — they 404 inside the sandboxed iframe.
_PREVIEW_STYLE = (
    "<style>a{pointer-events:none !important;cursor:default !important;}</style>"
)


def sanitize_for_preview(html: str) -> str:
    """Strip scripts and neutralise links for a safe, static in-app preview."""
    return _PREVIEW_STYLE + strip_scripts(html or "")


def extract_html(resp: Any) -> str | None:
    """Find the largest HTML-looking string anywhere in a response (e.g. *_live_html)."""
    best: str | None = None

    def walk(node: Any) -> None:
        nonlocal best
        if isinstance(node, str):
            if looks_like_html(node) and (best is None or len(node) > len(best)):
                best = node
        elif isinstance(node, dict):
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(resp)
    return best


def extract_links(items: list[dict]) -> list[dict]:
    """Collect source citations (title + url) from response items.

    Two shapes exist: LLM endpoints attach sources as
    items[].sections[].annotations = [{title, url}]; AI Overview / AI Mode items
    carry items[].references = [{title, url, domain}] (also on nested sub-items).
    Returns a de-duplicated list of {"title", "url"}.
    """
    links: list[dict] = []
    seen: set[str] = set()

    def add(entry) -> None:
        url = isinstance(entry, dict) and entry.get("url")
        if url and url not in seen:
            seen.add(url)
            links.append({"title": entry.get("title") or url, "url": url})

    def walk(item) -> None:
        if not isinstance(item, dict):
            return
        sections = item.get("sections") or []
        if not sections and isinstance(item.get("content"), dict):
            sections = item["content"].get("sections") or []
        for section in sections:
            if isinstance(section, dict):
                for ann in section.get("annotations") or []:
                    add(ann)
        for ref in item.get("references") or []:
            add(ref)
        for sub in item.get("items") or []:
            walk(sub)

    for item in items:
        walk(item)
    return links


def extract_message_text(items: list[dict]) -> str:
    """Pull readable answer text out of LLM-response items.

    LLM endpoints (ChatGPT/Claude/Gemini/Perplexity, AI overview/mode) nest the
    answer as items[].sections[].text (or content.sections, or a plain text/
    message string). Returns the concatenated text, or "" if none.
    """
    parts: list[str] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        sections = it.get("sections")
        if sections is None and isinstance(it.get("content"), dict):
            sections = it["content"].get("sections")
        if isinstance(sections, list):
            for sec in sections:
                if isinstance(sec, dict) and sec.get("text"):
                    parts.append(str(sec["text"]))
        elif isinstance(it.get("markdown"), str) and it["markdown"].strip():
            # AI Overview / AI Mode items carry the whole answer as markdown.
            parts.append(it["markdown"])
        elif isinstance(it.get("text"), str):
            parts.append(it["text"])
        elif isinstance(it.get("message"), str):
            parts.append(it["message"])
    return "\n\n".join(p for p in parts if p)
