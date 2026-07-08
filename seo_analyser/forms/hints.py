"""Plain-English hints prepended to the SDK's field descriptions.

The SDK descriptions are accurate but dense; these lead with what a junior SEO
needs to type. Keyed by family so other families' fields are untouched.
"""
from __future__ import annotations

_HINTS: dict[str, dict[str, str]] = {
    "backlinks": {
        "targets": (
            "One target per line. Domains and subdomains go without https:// or www. "
            "(e.g. example.com); individual pages need the full URL "
            "(e.g. https://example.com/page). Intersections take up to 20 targets; "
            "bulk endpoints up to 1,000."
        ),
        "exclude_targets": (
            "Domains or pages to leave out of the comparison, one per line, up to 10. "
            "Same format as targets."
        ),
        "filters": (
            'Advanced: JSON conditions, e.g. ["dofollow", "=", true] — up to 8, '
            'joined with "and"/"or". Leave empty to get everything (filtering is free).'
        ),
        "backlinks_filters": (
            'Advanced: filters the underlying backlinks feeding the aggregated metrics, '
            'e.g. ["dofollow", "=", true]. Leave empty to count all backlinks.'
        ),
        "order_by": (
            'Sorting rules as field,direction — e.g. rank,desc — one per line, up to three. '
            "Direction is asc or desc."
        ),
    },
}


def hint_for(family: str, field_name: str) -> str | None:
    return _HINTS.get(family, {}).get(field_name)
