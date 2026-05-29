"""Client-side validation so obvious mistakes are caught before a paid call."""
from __future__ import annotations

import re

# Scheme + a host containing a dot, then anything (path optional).
_URL_RE = re.compile(r"^https?://[^\s/]+\.[^\s]+$", re.IGNORECASE)


def looks_like_url(value: str) -> bool:
    return isinstance(value, str) and bool(_URL_RE.match(value.strip()))


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
