"""Execute a live endpoint through the SDK.

Builds a Configuration from credentials, instantiates the right Api class,
calls the method with a list-wrapped request model, and returns the parsed
response as a plain dict. Raises RunError on failure.
"""
from __future__ import annotations

import importlib
import inspect

from seo_analyser.auth import Credentials
from seo_analyser.registry.introspect import EndpointMeta
from seo_analyser.runner.errors import RunError, normalise


def _api_class_for(family: str):
    module = importlib.import_module(f"dataforseo_client.api.{family}_api")
    return next(
        cls for name, cls in inspect.getmembers(module, inspect.isclass)
        if name.endswith("Api") and cls.__module__ == module.__name__
    )


def run_live(meta: EndpointMeta, payload: dict, creds: Credentials) -> dict:
    if not creds.is_complete:
        raise RunError("auth", "Enter your DataForSEO login and password first.")
    if meta.request_model is None:
        raise RunError("bad_request", f"{meta.name} has no request model — not runnable yet.")

    from dataforseo_client import api_client as dfs_api_provider
    from dataforseo_client import configuration as dfs_config

    config = dfs_config.Configuration(username=creds.login, password=creds.password)
    try:
        request_obj = meta.request_model(**payload)
        with dfs_api_provider.ApiClient(config) as client:
            api = _api_class_for(meta.family)(client)
            method = getattr(api, meta.name)
            response = method([request_obj])
        return _to_dict(response)
    except RunError:
        raise
    except Exception as exc:  # noqa: BLE001 — normalised below
        raise normalise(exc) from exc


def _to_dict(response) -> dict:
    if hasattr(response, "to_dict"):
        return response.to_dict()
    if isinstance(response, dict):
        return response
    return {"result": str(response)}
