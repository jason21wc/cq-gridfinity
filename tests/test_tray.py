# Gridfinity Tray tests
import pytest

from cqgridfinity import *
from cqgridfinity.extended.tray import GridfinityTray

from cqkit.cq_helpers import size_3d
from cqkit import *

from common_test import (
    EXPORT_STEP_FILE_PATH,
    _almost_same,
    _export_files,
    SKIP_TEST_TRAY,
)


@pytest.mark.skipif(
    SKIP_TEST_TRAY, reason="Skipped intentionally by test scope environment variable"
)
def test_basic_tray():
    """Basic tray with default settings."""
    t = GridfinityTray(3, 2)
    r = t.render()
    assert _almost_same(size_3d(r), (125.5, 83.5, 17.8), tol=0.3)
    assert t.lip_style == "none"
    assert t.scoops is True
    assert t.height_u == 2
    assert t.filename() == "gf_tray_3x2x2_scoops"
    if _export_files("tray"):
        t.save_step_file(path=EXPORT_STEP_FILE_PATH)


@pytest.mark.skipif(
    SKIP_TEST_TRAY, reason="Skipped intentionally by test scope environment variable"
)
def test_tray_1x1():
    """Smallest tray size."""
    t = GridfinityTray(1, 1)
    r = t.render()
    assert _almost_same(size_3d(r), (41.5, 41.5, 17.8), tol=0.3)
    assert r.val().Volume() > 0


@pytest.mark.skipif(
    SKIP_TEST_TRAY, reason="Skipped intentionally by test scope environment variable"
)
def test_tray_custom_height():
    """Tray with custom height."""
    t = GridfinityTray(2, 2, height_u=3)
    r = t.render()
    assert _almost_same(size_3d(r), (83.5, 83.5, 24.8), tol=0.3)
    assert t.filename() == "gf_tray_2x2x3_scoops"


@pytest.mark.skipif(
    SKIP_TEST_TRAY, reason="Skipped intentionally by test scope environment variable"
)
def test_tray_override_defaults():
    """User can override tray defaults."""
    t = GridfinityTray(2, 2, lip_style="normal", scoops=False)
    assert t.lip_style == "normal"
    assert t.scoops is False
    r = t.render()
    assert r.val().Volume() > 0


@pytest.mark.skipif(
    SKIP_TEST_TRAY, reason="Skipped intentionally by test scope environment variable"
)
def test_tray_with_dividers():
    """Tray with dividers."""
    t = GridfinityTray(3, 2, length_div=2, width_div=1)
    r = t.render()
    assert r.val().Volume() > 0
    assert "div2x1" in t.filename()


@pytest.mark.skipif(
    SKIP_TEST_TRAY, reason="Skipped intentionally by test scope environment variable"
)
def test_tray_with_holes():
    """Tray with magnet holes."""
    t = GridfinityTray(2, 2, holes=True)
    r = t.render()
    assert r.val().Volume() > 0
    assert "_mag" in t.filename()
