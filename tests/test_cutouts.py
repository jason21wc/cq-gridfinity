# Gridfinity Cutout Profile tests
import pytest

from cqgridfinity.extended.cutouts import (
    RoundCutout, RectCutout, layout_cutouts,
)

from cqkit.cq_helpers import size_3d

from common_test import _almost_same, SKIP_TEST_CUTOUT


@pytest.mark.skipif(
    SKIP_TEST_CUTOUT, reason="Skipped intentionally by test scope environment variable"
)
def test_round_cutout():
    """Round cutout should produce a cylinder with clearance."""
    c = RoundCutout(diameter=14.5, height=12.0)
    r = c.render()
    bb = size_3d(r)
    expected_d = 14.5 + 2 * 0.25  # diameter + clearance
    assert _almost_same(bb[0], expected_d, tol=0.3)
    assert _almost_same(bb[1], expected_d, tol=0.3)
    assert _almost_same(bb[2], 12.0, tol=0.3)


@pytest.mark.skipif(
    SKIP_TEST_CUTOUT, reason="Skipped intentionally by test scope environment variable"
)
def test_rect_cutout():
    """Rectangular cutout with correct dimensions."""
    c = RectCutout(width=24.0, depth=2.1, height=18.0)
    r = c.render()
    bb = size_3d(r)
    assert _almost_same(bb[0], 24.0 + 0.5, tol=0.3)
    assert _almost_same(bb[1], 2.1 + 0.5, tol=0.3)
    assert _almost_same(bb[2], 18.0, tol=0.3)


@pytest.mark.skipif(
    SKIP_TEST_CUTOUT, reason="Skipped intentionally by test scope environment variable"
)
def test_round_cutout_no_chamfer():
    """Round cutout with chamfer disabled."""
    c = RoundCutout(diameter=10.0, height=8.0, chamfer=0)
    r = c.render()
    assert r.val().Volume() > 0


@pytest.mark.skipif(
    SKIP_TEST_CUTOUT, reason="Skipped intentionally by test scope environment variable"
)
def test_layout_square():
    """Square grid layout should produce correct number of items."""
    c = RoundCutout(diameter=10.0, height=8.0)
    grid = layout_cutouts(c, 3, 2, spacing=2.0, style="square")
    assert grid is not None
    assert grid.val().Volume() > 0
    # Volume should be approximately 6x a single cutout
    single_vol = c.render().val().Volume()
    assert _almost_same(grid.val().Volume(), single_vol * 6, tol=single_vol * 0.5)


@pytest.mark.skipif(
    SKIP_TEST_CUTOUT, reason="Skipped intentionally by test scope environment variable"
)
def test_layout_hex():
    """Hex grid layout should produce items."""
    c = RoundCutout(diameter=10.0, height=8.0)
    grid = layout_cutouts(c, 3, 3, spacing=2.0, style="hex")
    assert grid is not None
    assert grid.val().Volume() > 0


@pytest.mark.skipif(
    SKIP_TEST_CUTOUT, reason="Skipped intentionally by test scope environment variable"
)
def test_layout_single():
    """Layout with 1x1 should work."""
    c = RectCutout(width=20.0, depth=10.0, height=5.0)
    grid = layout_cutouts(c, 1, 1, spacing=2.0)
    assert grid is not None
    assert grid.val().Volume() > 0


@pytest.mark.skipif(
    SKIP_TEST_CUTOUT, reason="Skipped intentionally by test scope environment variable"
)
def test_layout_zero_returns_none():
    """Layout with 0 items should return None."""
    c = RoundCutout(diameter=10.0, height=5.0)
    assert layout_cutouts(c, 0, 3) is None
    assert layout_cutouts(c, 3, 0) is None
