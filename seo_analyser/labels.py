"""Turn snake_case SDK identifiers into human-readable labels."""
from __future__ import annotations

# Acronyms that should stay upper-cased in titles.
_ACRONYMS = {"serp", "url", "ai", "id", "os", "cpc", "se", "html", "api", "llm"}


def humanize(name: str) -> str:
    """Sentence case for field labels: 'location_name' -> 'Location name'."""
    words = name.replace("_", " ").strip()
    return words[:1].upper() + words[1:] if words else name


def titleize(name: str) -> str:
    """Title case for endpoint/family names, keeping known acronyms upper-cased.

    'google_organic_live_advanced' -> 'Google Organic Live Advanced'
    'serp' -> 'SERP'
    """
    parts = name.replace("_", " ").strip().split()
    if not parts:
        return name
    return " ".join(p.upper() if p.lower() in _ACRONYMS else p.capitalize() for p in parts)


# Junior-SEO-friendly names for the API families; fall back to titleize for new ones.
_FAMILY_LABELS = {
    "serp": "Rankings (SERP)",
    "keywords_data": "Keyword Volumes",
    "dataforseo_labs": "Keyword & Competitor Research",
    "backlinks": "Backlinks",
    "on_page": "Site Audits (On-Page)",
    "ai_optimization": "AI Visibility (LLMs)",
    "content_analysis": "Brand Mentions",
    "content_generation": "Content Generation",
    "domain_analytics": "Domain Tech & Whois",
    "business_data": "Business Listings & Reviews",
    "merchant": "Amazon & Shopping",
    "app_data": "App Stores",
    "appendix": "Account & Admin",
}


def family_label(name: str) -> str:
    """Plain-English family name for menus, e.g. 'serp' -> 'Rankings (SERP)'."""
    return _FAMILY_LABELS.get(name) or titleize(name)
