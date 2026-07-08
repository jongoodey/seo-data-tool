"""Capture real Backlinks responses to fixtures (Linear IND-22..28 support).

Runs every Backlinks endpoint once with the same safe low-cost params as the
smoke test, but SAVES each JSON response to tests/fixtures/backlinks/<name>.json
so renderers and unit tests can be built against ground-truth shapes without
re-billing. Also prints the exact per-endpoint cost (feeds IND-28's cost table).

Usage:
    source .venv/bin/activate
    python scripts/backlinks_capture.py            # ~$0.50 across all endpoints
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from seo_analyser.auth import from_env
from seo_analyser.registry.introspect import build_catalogue
from seo_analyser.runner.live import run_live
from seo_analyser.runner.errors import RunError

from scripts.backlinks_smoke import (  # reuse the vetted payloads
    FREE_PAYLOADS, PAID_PAYLOADS, run_no_body,
)

FIXTURES = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "backlinks"


def main() -> int:
    creds = from_env()
    if not creds.is_complete:
        print("No credentials in .env.local / env — aborting.")
        return 1

    FIXTURES.mkdir(parents=True, exist_ok=True)
    catalogue = {e.name: e for e in build_catalogue()["backlinks"]}
    total = 0.0
    costs: dict[str, float] = {}

    for name in ("index", "backlinks_available_filters"):
        try:
            resp = run_no_body(name, creds)
        except Exception as exc:  # noqa: BLE001
            print(f"{name:40s} FAIL {exc}")
            continue
        (FIXTURES / f"{name}.json").write_text(json.dumps(resp, indent=2, default=str))
        cost = resp.get("cost") or 0.0
        total += cost
        costs[name] = cost
        print(f"{name:40s} saved  cost=${cost:.5f}")

    payloads = {**FREE_PAYLOADS, **PAID_PAYLOADS}
    for name, payload in payloads.items():
        try:
            resp = run_live(catalogue[name], payload, creds)
        except RunError as exc:
            print(f"{name:40s} FAIL [{exc.kind}] {exc.message}")
            continue
        except Exception as exc:  # noqa: BLE001
            print(f"{name:40s} FAIL {exc}")
            continue
        (FIXTURES / f"{name}.json").write_text(json.dumps(resp, indent=2, default=str))
        cost = resp.get("cost") or 0.0
        total += cost
        costs[name] = cost
        task = (resp.get("tasks") or [{}])[0]
        print(f"{name:40s} saved  task={task.get('status_code')} cost=${cost:.5f}")

    (FIXTURES / "_costs.json").write_text(json.dumps(costs, indent=2))
    print(f"\nTotal spend: ${total:.5f}  ·  {len(costs)} fixtures in {FIXTURES}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
