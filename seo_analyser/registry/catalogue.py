"""Process-wide cached access to the endpoint catalogue."""
from __future__ import annotations

import re
from functools import lru_cache

from seo_analyser.registry.introspect import EndpointMeta, build_catalogue
from seo_analyser.registry.overrides import override_for

_WORD_RE = re.compile(r"[a-z0-9]+")


@lru_cache(maxsize=1)
def get_catalogue() -> dict[str, list[EndpointMeta]]:
    return build_catalogue()


def families() -> list[str]:
    return sorted(get_catalogue().keys())


def endpoints_for(family: str) -> list[EndpointMeta]:
    return get_catalogue().get(family, [])


def find_endpoint(family: str, name: str) -> EndpointMeta | None:
    return next((e for e in endpoints_for(family) if e.name == name), None)


def all_endpoints() -> list[EndpointMeta]:
    out: list[EndpointMeta] = []
    for eps in get_catalogue().values():
        out.extend(eps)
    return out


def _haystack(e: EndpointMeta) -> tuple[list[str], str]:
    title = override_for(e.family, e.name).get("title", "")
    words = _WORD_RE.findall(f"{e.family} {e.name} {title}".lower())
    return words, " ".join(words)


def score_endpoint(e: EndpointMeta, tokens: list[str]) -> int:
    """Rank a hit: exact word 3, word prefix 2, substring 1; 0 if any token misses.

    Word-boundary scoring stops "ai" matching the inside of "available"/"domain",
    which made the old all-substrings search surface the wrong endpoints first.
    """
    words, joined = _haystack(e)
    total = 0
    for token in tokens:
        if token in words:
            total += 3
        elif any(w.startswith(token) for w in words):
            total += 2
        elif token in joined:
            total += 1
        else:
            return 0
    return total


def search_endpoints(query: str, limit: int = 50) -> list[EndpointMeta]:
    tokens = [t for t in query.lower().split() if t]
    if not tokens:
        return []
    scored = sorted(
        ((score_endpoint(e, tokens), e) for e in all_endpoints()),
        key=lambda pair: -pair[0],
    )
    return [e for s, e in scored if s > 0][:limit]
