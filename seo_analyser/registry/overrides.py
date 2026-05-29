"""Per-endpoint UX overrides (friendly title / description).

Loaded from overrides.yml next to this file. Endpoints without an entry use the
auto-generated presentation. Default-param prefilling is a future enhancement.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

_OVERRIDES_FILE = Path(__file__).resolve().parent / "overrides.yml"


@lru_cache(maxsize=1)
def _load() -> dict:
    if not _OVERRIDES_FILE.exists():
        return {}
    data = yaml.safe_load(_OVERRIDES_FILE.read_text()) or {}
    return data if isinstance(data, dict) else {}


def override_for(family: str, endpoint: str) -> dict:
    """Return the override dict for `family.endpoint`, or {} if none."""
    return _load().get(f"{family}.{endpoint}", {})
