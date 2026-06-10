"""Every home-page shortcut must resolve to a real, runnable endpoint."""
from seo_analyser.registry import catalogue
from seo_analyser.ui.home import SHORTCUTS


def test_shortcuts_resolve_to_runnable_endpoints():
    for label, _blurb, family, endpoint in SHORTCUTS:
        meta = catalogue.find_endpoint(family, endpoint)
        assert meta is not None, f"{label}: {family}.{endpoint} not in catalogue"
        assert meta.request_model is not None, f"{label}: {family}.{endpoint} not runnable"


def test_shortcut_count_fits_grid():
    assert 6 <= len(SHORTCUTS) <= 8
