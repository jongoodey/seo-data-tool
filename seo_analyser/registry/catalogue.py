"""Process-wide cached access to the endpoint catalogue."""
from __future__ import annotations

from functools import lru_cache

from seo_analyser.registry.introspect import EndpointMeta, build_catalogue


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


def matches_query(family: str, name: str, query: str) -> bool:
    tokens = query.lower().split()
    if not tokens:
        return False
    haystack = f"{family} {name}".lower()
    return all(token in haystack for token in tokens)


def search_endpoints(query: str, limit: int = 50) -> list[EndpointMeta]:
    hits = [e for e in all_endpoints() if matches_query(e.family, e.name, query)]
    return hits[:limit]
