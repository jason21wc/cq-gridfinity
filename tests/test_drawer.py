# Gridfinity Modular Drawer tests
import pytest

from cqgridfinity import *
from cqgridfinity.extended.drawer import GridfinityDrawer, GridfinityDrawerChest

from cqkit.cq_helpers import size_3d
from cqkit import *

from common_test import (
    EXPORT_STEP_FILE_PATH,
    _almost_same,
    _export_files,
    SKIP_TEST_DRAWER,
)


@pytest.mark.skipif(
    SKIP_TEST_DRAWER, reason="Skipped intentionally by test scope environment variable"
)
def test_drawer_body():
    """Basic drawer body should render with correct dimensions."""
    d = GridfinityDrawer(3, 2, 2)
    r = d.render()
    bb = size_3d(r)
    # Outer = interior (3*42, 2*42) + walls (2*1.6) + rails protrude from sides
    # X: 126 + 3.2 + 2*3.0(rail_height) = 135.2 (approx, with rail)
    assert bb[0] > 125  # wider than interior
    assert bb[1] > 80   # deeper than interior
    assert bb[2] > 14   # 2*7 + floor
    assert r.val().Volume() > 0
    assert d.filename() == "gf_drawer_3x2x2_handle"
    if _export_files("drawer"):
        d.save_step_file(path=EXPORT_STEP_FILE_PATH)


@pytest.mark.skipif(
    SKIP_TEST_DRAWER, reason="Skipped intentionally by test scope environment variable"
)
def test_drawer_no_handle():
    """Drawer without handle should have more volume."""
    d_handle = GridfinityDrawer(2, 2, 2, handle=True)
    d_plain = GridfinityDrawer(2, 2, 2, handle=False)
    r_handle = d_handle.render()
    r_plain = d_plain.render()
    assert r_plain.val().Volume() > r_handle.val().Volume()
    assert d_plain.filename() == "gf_drawer_2x2x2"


@pytest.mark.skipif(
    SKIP_TEST_DRAWER, reason="Skipped intentionally by test scope environment variable"
)
def test_drawer_1x1():
    """Smallest drawer."""
    d = GridfinityDrawer(1, 1, 2)
    r = d.render()
    assert r.val().Volume() > 0


@pytest.mark.skipif(
    SKIP_TEST_DRAWER, reason="Skipped intentionally by test scope environment variable"
)
def test_drawer_has_rails():
    """Drawer with rails should be wider than without."""
    d = GridfinityDrawer(2, 2, 2)
    r = d.render()
    bb = size_3d(r)
    # Rails add rail_height (3mm) on each side beyond the box
    assert bb[0] > d.drawer_outer_l


@pytest.mark.skipif(
    SKIP_TEST_DRAWER, reason="Skipped intentionally by test scope environment variable"
)
def test_drawer_str():
    """String representation."""
    d = GridfinityDrawer(2, 2, 2)
    s = str(d)
    assert "Drawer" in s
    assert "Rail" in s
    assert "Handle" in s


@pytest.mark.skipif(
    SKIP_TEST_DRAWER, reason="Skipped intentionally by test scope environment variable"
)
def test_chest_body():
    """Basic chest should render."""
    c = GridfinityDrawerChest(3, 2, drawer_count=3, drawer_height_u=2)
    r = c.render()
    assert r.val().Volume() > 0
    bb = size_3d(r)
    # Should be tall enough for 3 drawers
    assert bb[2] > 3 * 14  # 3 slots * 2U * 7mm = 42mm minimum
    assert "gf_chest_" in c.filename()
    if _export_files("drawer"):
        c.save_step_file(path=EXPORT_STEP_FILE_PATH)


@pytest.mark.skipif(
    SKIP_TEST_DRAWER, reason="Skipped intentionally by test scope environment variable"
)
def test_chest_str():
    """String representation."""
    c = GridfinityDrawerChest(2, 2, drawer_count=2)
    s = str(c)
    assert "Chest" in s
    assert "2 drawers" in s


@pytest.mark.skipif(
    SKIP_TEST_DRAWER, reason="Skipped intentionally by test scope environment variable"
)
def test_drawer_fits_in_chest():
    """Drawer outer dims should be smaller than chest inner dims."""
    d = GridfinityDrawer(3, 2, 2)
    c = GridfinityDrawerChest(3, 2, drawer_count=3, drawer_height_u=2)
    rd = d.render()
    rc = c.render()
    bd = size_3d(rd)
    bc = size_3d(rc)
    # Drawer must be shorter than chest in every dimension
    assert bd[0] < bc[0]  # width (X)
    assert bd[1] < bc[1]  # depth (Y)
    assert bd[2] < bc[2]  # height (Z)


@pytest.mark.skipif(
    SKIP_TEST_DRAWER, reason="Skipped intentionally by test scope environment variable"
)
def test_chest_single_drawer():
    """Chest with a single drawer slot."""
    c = GridfinityDrawerChest(2, 2, drawer_count=1, drawer_height_u=3)
    r = c.render()
    assert r.val().Volume() > 0


@pytest.mark.skipif(
    SKIP_TEST_DRAWER, reason="Skipped intentionally by test scope environment variable"
)
def test_chest_no_base():
    """Chest without base profile should be shorter."""
    c_base = GridfinityDrawerChest(2, 2, drawer_count=2, has_base_profile=True)
    c_nobase = GridfinityDrawerChest(2, 2, drawer_count=2, has_base_profile=False)
    r_base = c_base.render()
    r_nobase = c_nobase.render()
    h_base = size_3d(r_base)[2]
    h_nobase = size_3d(r_nobase)[2]
    assert h_base > h_nobase
