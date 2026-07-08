"""Every home-page shortcut must resolve to a real, runnable endpoint."""
from seo_analyser.registry import catalogue
from seo_analyser.ui.home import SHORTCUTS


def test_shortcuts_resolve_to_runnable_endpoints():
    for label, _blurb, family, endpoint in SHORTCUTS:
        meta = catalogue.find_endpoint(family, endpoint)
        assert meta is not None, f"{label}: {family}.{endpoint} not in catalogue"
        assert meta.request_model is not None, f"{label}: {family}.{endpoint} not runnable"


def test_shortcut_count_fits_grid():
    # 2-column grid; keep the count even and not overwhelming. Backlinks added
    # a workflow cluster (IND-20), so the ceiling is 12.
    assert 6 <= len(SHORTCUTS) <= 12
    assert len(SHORTCUTS) % 2 == 0, "odd shortcut count leaves a lonely column"
