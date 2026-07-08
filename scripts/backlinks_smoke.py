"""Backlinks API smoke test (Linear IND-19).

Runs every Backlinks endpoint once through the app's own run_live path with
safe, low-cost parameters (limit=10, small stable targets), then reports the
DataForSEO status code and cost per endpoint plus the total spend.

Usage:
    source .venv/bin/activate
    python scripts/backlinks_smoke.py            # free endpoints only
    python scripts/backlinks_smoke.py --paid     # all endpoints (~$0.40-0.60)

Credentials come from .env.local (user_name/password) like the app itself.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from seo_analyser.auth import from_env
from seo_analyser.registry.introspect import build_catalogue
from seo_analyser.runner.live import run_live
from seo_analyser.runner.errors import RunError

# Small, stable, well-indexed targets. dataforseo.com keeps row counts modest;
# limit=10 caps per-row charges on every list endpoint.
TARGET = "dataforseo.com"
TARGET_2 = "ahrefs.com"
PAGE = "https://dataforseo.com/"

FREE_PAYLOADS: dict[str, dict] = {
    "backlinks_id_list": {
        "datetime_from": "2026-07-01 00:00:00 +00:00",
        "datetime_to": "2026-07-08 00:00:00 +00:00",
        "limit": 10,
    },
    "backlinks_errors": {"limit": 10},
}

PAID_PAYLOADS: dict[str, dict] = {
    "summary_live": {"target": TARGET, "internal_list_limit": 1},
    "history_live": {"target": TARGET, "date_from": "2026-01-01", "date_to": "2026-06-01"},
    "backlinks_live": {"target": TARGET, "limit": 10, "mode": "as_is"},
    "anchors_live": {"target": TARGET, "limit": 10},
    "domain_pages_live": {"target": TARGET, "limit": 10},
    "domain_pages_summary_live": {"target": TARGET, "limit": 10},
    "referring_domains_live": {"target": TARGET, "limit": 10},
    "referring_networks_live": {"target": TARGET, "limit": 10},
    "competitors_live": {"target": TARGET, "limit": 10},
    "domain_intersection_live": {"targets": {"1": TARGET, "2": TARGET_2}, "limit": 10},
    "page_intersection_live": {"targets": {"1": PAGE, "2": "https://ahrefs.com/"}, "limit": 10},
    "timeseries_summary_live": {
        "target": TARGET, "date_from": "2026-01-01", "date_to": "2026-06-01", "group_range": "month",
    },
    "timeseries_new_lost_summary_live": {
        "target": TARGET, "date_from": "2026-01-01", "date_to": "2026-06-01", "group_range": "month",
    },
    "bulk_ranks_live": {"targets": [TARGET, TARGET_2]},
    "bulk_backlinks_live": {"targets": [TARGET, TARGET_2]},
    "bulk_spam_score_live": {"targets": [TARGET, TARGET_2]},
    "bulk_referring_domains_live": {"targets": [TARGET, TARGET_2]},
    "bulk_new_lost_backlinks_live": {"targets": [TARGET, TARGET_2], "date_from": "2026-06-01"},
    "bulk_new_lost_referring_domains_live": {"targets": [TARGET, TARGET_2], "date_from": "2026-06-01"},
    "bulk_pages_summary_live": {"targets": [TARGET, PAGE]},
}


def run_no_body(name: str, creds) -> dict:
    """index and backlinks_available_filters are GET endpoints with no request
    model, so run_live refuses them — call the SDK method directly."""
    from dataforseo_client import api_client as dfs_api_provider
    from dataforseo_client import configuration as dfs_config
    from dataforseo_client.api.backlinks_api import BacklinksApi

    config = dfs_config.Configuration(username=creds.login, password=creds.password)
    with dfs_api_provider.ApiClient(config) as client:
        response = getattr(BacklinksApi(client), name)()
    return response.to_dict()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paid", action="store_true", help="also run the 20 paid endpoints")
    args = parser.parse_args()

    creds = from_env()
    if not creds.is_complete:
        print("No credentials in .env.local / env — aborting.")
        return 1

    catalogue = {e.name: e for e in build_catalogue()["backlinks"]}
    payloads = dict(FREE_PAYLOADS)
    if args.paid:
        payloads.update(PAID_PAYLOADS)

    total_cost = 0.0
    failures = []

    for name in ("index", "backlinks_available_filters"):
        try:
            resp = run_no_body(name, creds)
            print(f"{name:40s} OK    api={resp.get('status_code')} cost={resp.get('cost')}")
            total_cost += resp.get("cost") or 0.0
        except Exception as exc:  # noqa: BLE001 — smoke report, keep going
            failures.append(name)
            print(f"{name:40s} FAIL  {exc}")

    for name, payload in payloads.items():
        meta = catalogue[name]
        try:
            resp = run_live(meta, payload, creds)
            task = (resp.get("tasks") or [{}])[0]
            code, msg = task.get("status_code"), task.get("status_message")
            cost = resp.get("cost") or 0.0
            total_cost += cost
            ok = "OK  " if code == 20000 else "WARN"
            if code != 20000:
                failures.append(name)
            print(f"{name:40s} {ok}  task={code} ({msg}) cost=${cost:.5f}")
        except RunError as exc:
            failures.append(name)
            print(f"{name:40s} FAIL  [{exc.kind}] {exc.message}")
        except Exception as exc:  # noqa: BLE001
            failures.append(name)
            print(f"{name:40s} FAIL  {exc}")

    print(f"\nTotal cost: ${total_cost:.5f}")
    if failures:
        print(f"Failures ({len(failures)}): {', '.join(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
