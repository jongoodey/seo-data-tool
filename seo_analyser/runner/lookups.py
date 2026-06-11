"""Dynamic value lookups for fields whose valid options live in another endpoint.

The clearest case is the LLM response endpoints: `model_name` is required but its
valid values are served by a sibling `*_llm_responses_models` endpoint rather than
described inline. We fetch and cache those so the form can offer a dropdown.
"""
from __future__ import annotations

import re
from functools import lru_cache

from seo_analyser.auth import Credentials
from seo_analyser.registry.introspect import EndpointMeta
from seo_analyser.runner.live import _api_class_for

# Matches the live variant, the raw task_post, and the folded task triplet
# (which has no suffix at all) — every shape that takes a model_name.
_LLM_RESPONSES_RE = re.compile(r"^(?P<prefix>.+)_llm_responses(?:_live|_task_post)?$")


def models_method_name(endpoint_name: str) -> str | None:
    """Map an LLM responses endpoint to its sibling models-listing method.

    'chat_gpt_llm_responses_live' -> 'chat_gpt_llm_responses_models'
    'chat_gpt_llm_responses' (task triplet) -> 'chat_gpt_llm_responses_models'
    Returns None for endpoints without a models sibling.
    """
    match = _LLM_RESPONSES_RE.match(endpoint_name)
    return f"{match.group('prefix')}_llm_responses_models" if match else None


def llm_model_choices(meta: EndpointMeta, creds: Credentials) -> list[str] | None:
    """Valid model_name values for an LLM endpoint, or None if not applicable."""
    if not creds.is_complete:
        return None
    method = models_method_name(meta.name)
    if method is None:
        return None
    return _fetch_model_names(meta.family, method, creds.login, creds.password)


@lru_cache(maxsize=64)
def _fetch_model_names(family: str, method_name: str, login: str, password: str):
    from dataforseo_client import api_client as prov
    from dataforseo_client import configuration as cfg

    try:
        conf = cfg.Configuration(username=login, password=password)
        with prov.ApiClient(conf) as client:
            api = _api_class_for(family)(client)
            method = getattr(api, method_name, None)
            if method is None:
                return None
            resp = method()
            data = resp.to_dict() if hasattr(resp, "to_dict") else resp
            results = (data.get("tasks") or [{}])[0].get("result") or []
            names = [r["model_name"] for r in results
                     if isinstance(r, dict) and r.get("model_name")]
            return names or None
    except Exception:
        return None
