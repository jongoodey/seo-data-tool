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
