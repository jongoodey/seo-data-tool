"""Common location/language presets for quick selection in forms.

Location codes verified against DataForSEO's google_ads_locations list
(location_code = 2000 + ISO 3166-1 numeric country code).
"""
from __future__ import annotations

_LOCATIONS = [
    ("United Kingdom", 2826), ("United States", 2840), ("Spain", 2724),
    ("Germany", 2276), ("France", 2250), ("Italy", 2380),
    ("Netherlands", 2528), ("Ireland", 2372), ("Canada", 2124),
    ("Australia", 2036),
]
_LANGUAGES = [
    ("English", "en"), ("Spanish", "es"), ("German", "de"), ("French", "fr"),
    ("Italian", "it"), ("Dutch", "nl"), ("Portuguese", "pt"),
]

# field name -> list of (display label, value to send)
PRESETS: dict[str, list[tuple[str, object]]] = {
    "location_name": [(name, name) for name, _ in _LOCATIONS],
    "location_code": [(f"{name} ({code})", code) for name, code in _LOCATIONS],
    "language_name": [(name, name) for name, _ in _LANGUAGES],
    "language_code": [(f"{name} ({code})", code) for name, code in _LANGUAGES],
}


def presets_for(field_name: str) -> list[tuple[str, object]]:
    """Common (label, value) options for a field, or [] if none."""
    return PRESETS.get(field_name, [])
