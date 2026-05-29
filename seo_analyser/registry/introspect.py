"""Walk the dataforseo-client SDK and build a catalogue of endpoints.

The SDK exposes 13 API-family modules under dataforseo_client.api.*, each with
one Api class. Every endpoint is a public method whose request payload is a
Pydantic v2 BaseModel. The generator emits three variants per endpoint; we keep
only the canonical one.
"""
from __future__ import annotations

import importlib
import inspect
import pkgutil
import re
from dataclasses import dataclass

import dataforseo_client.api as api_pkg
import dataforseo_client.models as models_pkg
from pydantic import BaseModel

_VARIANT_SUFFIXES = ("_with_http_info", "_without_preload_content")
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


@dataclass(frozen=True)
class EndpointMeta:
    name: str            # SDK method name, e.g. "google_organic_live_advanced"
    family: str          # e.g. "serp"
    request_model: type | None   # Pydantic request model class, or None for GET-only
    is_task_based: bool  # True when this is a *_task_post method


def _api_class(module) -> type:
    """Return the single class ending in 'Api' defined in this module."""
    return next(
        cls for name, cls in inspect.getmembers(module, inspect.isclass)
        if name.endswith("Api") and cls.__module__ == module.__name__
    )


def _resolve_model_name(name: str) -> type | None:
    """Look a class name up in dataforseo_client.models; return it if it's a BaseModel."""
    cls = getattr(models_pkg, name, None)
    if inspect.isclass(cls) and issubclass(cls, BaseModel):
        return cls
    return None


def _request_model(method) -> type | None:
    """Resolve the request-body model for an SDK method.

    The generated SDK stores parameter annotations as *strings* (e.g.
    "List[Optional[SerpGoogleOrganicLiveAdvancedRequestInfo]]") that the runtime
    never resolves, so we parse the class name out and look it up in the models
    package. The body is always the first non-self, non-private parameter.
    """
    try:
        sig = inspect.signature(method)
    except (ValueError, TypeError):
        return None
    for pname, param in sig.parameters.items():
        if pname == "self" or pname.startswith("_"):
            continue
        ann = param.annotation
        # Already a real class (defensive — some methods may resolve normally).
        if inspect.isclass(ann) and issubclass(ann, BaseModel):
            return ann
        # String annotation: take the last-resolving identifier (inner model name).
        if isinstance(ann, str):
            for ident in reversed(_IDENT_RE.findall(ann)):
                model = _resolve_model_name(ident)
                if model is not None:
                    return model
        # Typing generic carrying real classes (e.g. List[Model]).
        for a in getattr(ann, "__args__", ()):
            if inspect.isclass(a) and issubclass(a, BaseModel):
                return a
        # Only the first body parameter matters; GET-only endpoints have none.
        return None
    return None


def build_catalogue() -> dict[str, list[EndpointMeta]]:
    catalogue: dict[str, list[EndpointMeta]] = {}
    for _, mod_name, _ in pkgutil.iter_modules(api_pkg.__path__):
        module = importlib.import_module(f"dataforseo_client.api.{mod_name}")
        api_class = _api_class(module)
        family = mod_name[:-4] if mod_name.endswith("_api") else mod_name
        endpoints: list[EndpointMeta] = []
        for method_name, method in inspect.getmembers(api_class, inspect.isfunction):
            if method_name.startswith("_"):
                continue
            if method_name.endswith(_VARIANT_SUFFIXES):
                continue
            endpoints.append(
                EndpointMeta(
                    name=method_name,
                    family=family,
                    request_model=_request_model(method),
                    is_task_based=method_name.endswith("_task_post"),
                )
            )
        catalogue[family] = endpoints
    return catalogue


if __name__ == "__main__":
    cat = build_catalogue()
    total = sum(len(v) for v in cat.values())
    for fam in sorted(cat, key=lambda f: -len(cat[f])):
        print(f"{fam:<22} {len(cat[fam])}")
    print(f"{'TOTAL':<22} {total}")
