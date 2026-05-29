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


def items_table(items: list[dict]) -> list[dict]:
    """Reduce each item to its scalar fields so it renders as a flat table."""
    return [_scalars(it) for it in items]


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
    """Collect source citations (title + url) from LLM-response annotations.

    LLM endpoints attach sources as items[].sections[].annotations = [{title, url}].
    Returns a de-duplicated list of {"title", "url"}.
    """
    links: list[dict] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        sections = item.get("sections") or []
        if not sections and isinstance(item.get("content"), dict):
            sections = item["content"].get("sections") or []
        for section in sections:
            if not isinstance(section, dict):
                continue
            for ann in section.get("annotations") or []:
                url = isinstance(ann, dict) and ann.get("url")
                if url and url not in seen:
                    seen.add(url)
                    links.append({"title": ann.get("title") or url, "url": url})
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
        elif isinstance(it.get("text"), str):
            parts.append(it["text"])
        elif isinstance(it.get("message"), str):
            parts.append(it["message"])
    return "\n\n".join(p for p in parts if p)
