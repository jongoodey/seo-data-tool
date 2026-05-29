"""Fetch the DataForSEO account balance for the sidebar widget."""
from __future__ import annotations

from seo_analyser.auth import Credentials
from seo_analyser.runner.live import _api_class_for


def parse_balance(user_data_response: dict) -> float | None:
    """Pull money.balance out of an appendix user_data response."""
    results = (user_data_response.get("tasks") or [{}])[0].get("result") or []
    if not results or not isinstance(results[0], dict):
        return None
    money = results[0].get("money") or {}
    return money.get("balance")


def account_balance(creds: Credentials) -> float | None:
    if not creds.is_complete:
        return None
    from dataforseo_client import api_client as prov
    from dataforseo_client import configuration as cfg
    from dataforseo_client.api.appendix_api import AppendixApi

    try:
        conf = cfg.Configuration(username=creds.login, password=creds.password)
        with prov.ApiClient(conf) as client:
            resp = AppendixApi(client).user_data()
            data = resp.to_dict() if hasattr(resp, "to_dict") else resp
        return parse_balance(data)
    except Exception:
        return None
