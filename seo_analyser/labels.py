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
