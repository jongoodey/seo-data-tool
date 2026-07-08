"""Override-key validity and Backlinks workflow discoverability (Linear IND-20).

A stale override key silently does nothing (the real bug that left
backlinks.summary_live dead until 2026-06-10), so every override key and every
home shortcut is pinned to a real catalogue endpoint here.
"""
import pathlib

import yaml

from seo_analyser.registry import catalogue
from seo_analyser.ui.home import SHORTCUTS

_OVERRIDES = yaml.safe_load(
    (pathlib.Path(__file__).parent.parent
     / "seo_analyser/registry/overrides.yml").read_text()
)


def _exists(family: str, endpoint: str) -> bool:
    return catalogue.find_endpoint(family, endpoint) is not None


def test_every_override_key_maps_to_a_real_endpoint():
    for key in _OVERRIDES:
        family, _, endpoint = key.partition(".")
        assert _exists(family, endpoint), f"override key '{key}' has no endpoint"


def test_every_home_shortcut_maps_to_a_real_endpoint():
    for _label, _blurb, family, endpoint in SHORTCUTS:
        assert _exists(family, endpoint), f"shortcut {family}.{endpoint} missing"


def _names(query: str) -> set[str]:
    return {e.name for e in catalogue.search_endpoints(query)}


def test_required_backlinks_searches_return_expected_endpoints():
    assert {"summary_live", "backlinks_live"} & _names("backlink audit")
    assert {"domain_intersection_live", "page_intersection_live"} & _names("link gap")
    assert "anchors_live" in _names("anchors")
    assert "referring_domains_live" in _names("referring domains")
    assert {"timeseries_new_lost_summary_live",
            "bulk_new_lost_backlinks_live"} & _names("new lost backlinks")
    assert "bulk_spam_score_live" in _names("spam score")
    assert "bulk_backlinks_live" in _names("bulk backlinks")


def test_existing_shortcut_searches_still_work():
    # The ranked search behaviour from the junior-SEO pass must be intact.
    assert "google_ai_mode_live_advanced" in _names("ai overview")
    assert _names("ranked keywords")
