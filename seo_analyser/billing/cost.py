"""Rough per-call cost estimates, surfaced before a run.

Order-of-magnitude figures per DataForSEO pricing (endpoint-inventory.md §17).
These are indicative, not exact — the precise cost is shown after each run.
"""
from __future__ import annotations

_PER_FAMILY_USD = {
    "serp": 0.002,
    "keywords_data": 0.05,
    "business_data": 0.003,
    "dataforseo_labs": 0.02,
    "ai_optimization": 0.01,
    "app_data": 0.003,
    "merchant": 0.003,
    "on_page": 0.0015,
    "backlinks": 0.024,  # $0.024/request + $0.000036/row since 1 July 2026
    "domain_analytics": 0.05,
    "content_analysis": 0.01,
    "content_generation": 0.01,
    "appendix": 0.0,
}


def estimate_cost(family: str) -> float | None:
    """Indicative USD cost for one call in this family, or None if unknown."""
    return _PER_FAMILY_USD.get(family)


def format_estimate(family: str) -> str | None:
    cost = estimate_cost(family)
    if cost is None:
        return None
    if cost == 0:
        return "Estimated cost: free"
    return f"Estimated cost: ~${cost:.4f} per call (indicative)"
