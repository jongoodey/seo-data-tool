"""Client-side validation so obvious mistakes are caught before a paid call."""
from __future__ import annotations

import re
from datetime import date

# Scheme + a host containing a dot, then anything (path optional).
_URL_RE = re.compile(r"^https?://[^\s/]+\.[^\s]+$", re.IGNORECASE)
# Bare hostname: dot-separated labels of letters/digits/hyphens, no scheme/path.
_DOMAIN_RE = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$",
                        re.IGNORECASE)
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def looks_like_url(value: str) -> bool:
    return isinstance(value, str) and bool(_URL_RE.match(value.strip()))


def looks_like_domain(value: str) -> bool:
    return isinstance(value, str) and bool(_DOMAIN_RE.match(value.strip()))


def looks_like_target(value: str) -> bool:
    """A DataForSEO target is a bare domain/subdomain or an absolute http(s) URL."""
    return looks_like_domain(value) or looks_like_url(value)


def parse_targets(value) -> list[str]:
    """Normalise a targets input (list, dict, or comma/newline string) to a clean list."""
    if value is None:
        return []
    if isinstance(value, dict):
        raw = list(value.values())
    elif isinstance(value, str):
        raw = re.split(r"[,\n]", value)
    else:
        raw = list(value)
    return [item.strip() for item in raw if isinstance(item, str) and item.strip()]


_ID_FIELDS = {"id", "task_id"}

# Documented DataForSEO Backlinks constraints (docs.dataforseo.com/v3/backlinks-overview,
# verified 2026-07-08 in the IND-19 audit).
_INTERSECTION_ENDPOINTS = {"domain_intersection_live", "page_intersection_live"}
_BULK_MAX_TARGETS = 1000
_INTERSECTION_MAX_TARGETS = 20
_EXCLUDE_MAX_TARGETS = 10
# $0.024/request + $0.000036/row — a full 1,000-row page costs ~$0.06.
_COST_PER_REQUEST = 0.024
_COST_PER_ROW = 0.000036


def _bad_entries(targets: list[str]) -> list[str]:
    return [t for t in targets if not looks_like_target(t)]


def validate_backlinks(endpoint_name: str, payload: dict) -> list[str]:
    """Backlinks-specific blocking checks: target shape, targets counts, dates.

    Empty required fields are validate_required_fields' job — this only judges
    values the user actually entered, so an empty payload stays quiet.
    """
    problems: list[str] = []

    target = payload.get("target")
    if isinstance(target, str) and target.strip():
        cleaned = target.strip()
        if cleaned.lower().startswith("www."):
            problems.append(
                f"'target' should be entered without the www. prefix "
                f"(use '{cleaned[4:]}' instead of '{cleaned}')."
            )
        elif not looks_like_target(cleaned):
            problems.append(
                f"'target' should be a domain like example.com (no https:// or www.), "
                f"or a full page URL starting with http:// or https:// "
                f"(you entered '{cleaned}')."
            )

    max_targets = (_INTERSECTION_MAX_TARGETS if endpoint_name in _INTERSECTION_ENDPOINTS
                   else _BULK_MAX_TARGETS)
    for field, cap in (("targets", max_targets), ("exclude_targets", _EXCLUDE_MAX_TARGETS)):
        if field not in payload:
            continue
        targets = parse_targets(payload[field])
        bad = _bad_entries(targets)
        if bad:
            shown = "', '".join(bad[:5])
            problems.append(
                f"'{field}' has {len(bad)} entry(ies) that aren't a domain like example.com "
                f"or a full http(s):// URL: '{shown}'."
            )
        if len(targets) > cap:
            problems.append(
                f"'{field}' allows at most {cap} entries for this endpoint "
                f"(you have {len(targets)}). Split the list into smaller batches."
            )

    problems.extend(_date_problems(payload))
    return problems


def _date_problems(payload: dict) -> list[str]:
    problems: list[str] = []
    parsed: dict[str, date] = {}
    for field in ("date_from", "date_to"):
        value = payload.get(field)
        if not (isinstance(value, str) and value.strip()):
            continue
        cleaned = value.strip()
        if not _DATE_RE.match(cleaned):
            problems.append(
                f"'{field}' should be a date in yyyy-mm-dd format, e.g. 2026-01-15 "
                f"(you entered '{cleaned}')."
            )
            continue
        try:
            parsed[field] = date.fromisoformat(cleaned)
        except ValueError:
            problems.append(f"'{field}' isn't a real calendar date (you entered '{cleaned}').")
    if "date_from" in parsed and "date_to" in parsed and parsed["date_from"] > parsed["date_to"]:
        problems.append("'date_from' must be on or before 'date_to'.")
    return problems


def backlinks_advisories(payload: dict) -> list[str]:
    """Non-blocking cost warnings for inputs that will bill heavily if run."""
    notes: list[str] = []
    limit = payload.get("limit")
    if isinstance(limit, int) and limit > 100:
        cost = _COST_PER_REQUEST + _COST_PER_ROW * limit
        notes.append(
            f"limit {limit} can return up to {limit} billed rows "
            f"(~${cost:.3f} for this request). Lower it if you only need a sample."
        )
    targets = parse_targets(payload.get("targets"))
    if len(targets) > 100:
        cost = _COST_PER_REQUEST + _COST_PER_ROW * len(targets)
        notes.append(
            f"{len(targets)} targets bill one row each (~${cost:.3f} for this request)."
        )
    return notes


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
