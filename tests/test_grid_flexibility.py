# Tests for 1B.12: Non-integer grid sizes
#
# Acceptance: e.g., 2.5 x 3 grid units. Internal grid calculations use raw
# float values. Base profiles placed only at integer cell positions (floor).
# Source: kennetek/gridfinity-rebuilt-bins.scad (gridx/gridy with .1 step)
import math

import pytest

from cqgridfinity import GridfinityBox
from cqkit.cq_helpers import size_3d
from common_test import _almost_same, SKIP_TEST_BOX
from cqgridfinity.constants import GRU, GR_TOL, GR_BASE_HEIGHT, GRHU


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _expected_outer_l(length_u):
    """Outer length = length_u * 42 - 0.5 mm tolerance."""
    return length_u * GRU - GR_TOL


def _expected_outer_w(width_u):
    return width_u * GRU - GR_TOL


def _expected_height(height_u):
    return 3.8 + GRHU * height_u


# ---------------------------------------------------------------------------
# 1B.12: Non-integer grid sizes — geometry
# ---------------------------------------------------------------------------


@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_noninteger_bbox_25x3():
    """2.5 x 3 bin should have outer dims 2.5*42-0.5 x 3*42-0.5."""
    b = GridfinityBox(2.5, 3, 3, fillet_interior=False)
    r = b.render()
    assert r.val().isValid()
    sx, sy, sz = size_3d(r)
    assert _almost_same(sx, _expected_outer_l(2.5), tol=0.05)
    assert _almost_same(sy, _expected_outer_w(3), tol=0.05)
    assert _almost_same(sz, _expected_height(3), tol=0.05)


@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_noninteger_bbox_15x2():
    """1.5 x 2 bin should produce correct outer dimensions."""
    b = GridfinityBox(1.5, 2, 2, fillet_interior=False)
    r = b.render()
    assert r.val().isValid()
    sx, sy, sz = size_3d(r)
    assert _almost_same(sx, _expected_outer_l(1.5), tol=0.05)
    assert _almost_same(sy, _expected_outer_w(2), tol=0.05)


@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_noninteger_point1_step():
    """3.1 x 2.7 bin (.1 step) should render as a valid solid."""
    b = GridfinityBox(3.1, 2.7, 4, fillet_interior=False)
    r = b.render()
    assert r.val().isValid()
    sx, sy, sz = size_3d(r)
    assert _almost_same(sx, _expected_outer_l(3.1), tol=0.05)
    assert _almost_same(sy, _expected_outer_w(2.7), tol=0.05)


# ---------------------------------------------------------------------------
# 1B.12: Base profiles at integer positions only (floor)
# ---------------------------------------------------------------------------


def test_grid_centres_integer_floor():
    """grid_centres should contain floor(length_u) * floor(width_u) entries."""
    b = GridfinityBox(2.5, 3, 2)
    centres = b.grid_centres
    expected_count = math.floor(2.5) * math.floor(3)  # 2 * 3 = 6
    assert len(centres) == expected_count


def test_grid_centres_15x15():
    """1.5 x 1.5 bin has only 1 base profile (floor(1.5)=1 per axis)."""
    b = GridfinityBox(1.5, 1.5, 2)
    centres = b.grid_centres
    assert len(centres) == 1  # floor(1.5) * floor(1.5) = 1 * 1


def test_grid_centres_integer_unchanged():
    """Integer grids should produce the same number of centres as before."""
    b = GridfinityBox(3, 2, 2)
    centres = b.grid_centres
    assert len(centres) == 6  # 3 * 2


def test_hole_centres_count():
    """hole_centres = floor(length_u) * floor(width_u) * 4 (4 holes per cell)."""
    b = GridfinityBox(2.5, 3, 2, holes=True)
    centres = b.hole_centres
    expected = int(2.5) * int(3) * 4  # 2 * 3 * 4 = 24
    assert len(centres) == expected


# ---------------------------------------------------------------------------
# 1B.12: Filename formatting
# ---------------------------------------------------------------------------


def test_filename_integer_unchanged():
    """Integer grid units should still produce integer-format filenames."""
    b = GridfinityBox(3, 2, 4)
    assert "3x2" in b.filename()


def test_filename_noninteger_25():
    """2.5 grid unit should appear as '2p5' in the filename."""
    b = GridfinityBox(2.5, 3, 4)
    fn = b.filename()
    assert "2p5" in fn
    assert "3" in fn


def test_filename_noninteger_15():
    """1.5 grid unit should appear as '1p5' in the filename."""
    b = GridfinityBox(1.5, 2, 3)
    fn = b.filename()
    assert "1p5" in fn


def test_filename_fmt_unit_integers():
    """_fmt_unit helper: integers format without decimal point."""
    from cqgridfinity.gf_obj import GridfinityObject
    assert GridfinityObject._fmt_unit(2) == "2"
    assert GridfinityObject._fmt_unit(3.0) == "3"
    assert GridfinityObject._fmt_unit(10) == "10"


def test_filename_fmt_unit_floats():
    """_fmt_unit helper: floats use 'p' in place of '.'."""
    from cqgridfinity.gf_obj import GridfinityObject
    assert GridfinityObject._fmt_unit(2.5) == "2p5"
    assert GridfinityObject._fmt_unit(1.5) == "1p5"
    assert GridfinityObject._fmt_unit(3.1) == "3p1"


# ---------------------------------------------------------------------------
# 1B.12: Backward compatibility — integer values unaffected
# ---------------------------------------------------------------------------


@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_integer_backward_compat_bbox():
    """Integer grid sizes should produce the same outer dims as before."""
    b = GridfinityBox(2, 3, 4, fillet_interior=False)
    r = b.render()
    assert r.val().isValid()
    sx, sy, sz = size_3d(r)
    assert _almost_same(sx, _expected_outer_l(2), tol=0.05)
    assert _almost_same(sy, _expected_outer_w(3), tol=0.05)


@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_noninteger_with_holes():
    """Non-integer grid with holes should render without error."""
    b = GridfinityBox(2.5, 2, 3, holes=True, fillet_interior=False)
    r = b.render()
    assert r.val().isValid()


@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_noninteger_with_features():
    """Non-integer grid with scoops + labels should render as valid solid."""
    b = GridfinityBox(2.5, 2, 4, scoops=True, labels=True, fillet_interior=False)
    r = b.render()
    assert r.val().isValid()


# ---------------------------------------------------------------------------
# 1B.12: Validation guards
# ---------------------------------------------------------------------------


def test_sub1_length_u_raises():
    """length_u < 1 must raise ValueError (cannot form a valid base profile)."""
    with pytest.raises(ValueError, match="length_u must be >= 1"):
        GridfinityBox(0.5, 2, 3)


def test_sub1_width_u_raises():
    """width_u < 1 must raise ValueError."""
    with pytest.raises(ValueError, match="width_u must be >= 1"):
        GridfinityBox(2, 0.9, 3)


def test_noninteger_baseplate_raises():
    """GridfinityBaseplate rejects non-integer grid units (bin-only feature)."""
    from cqgridfinity import GridfinityBaseplate
    with pytest.raises(ValueError, match="integer length_u"):
        GridfinityBaseplate(2.5, 3)


def test_noninteger_baseplate_width_raises():
    """GridfinityBaseplate rejects non-integer width_u."""
    from cqgridfinity import GridfinityBaseplate
    with pytest.raises(ValueError, match="integer width_u"):
        GridfinityBaseplate(3, 2.5)


# ---------------------------------------------------------------------------
# 1B.13: Half-grid (21mm) mode
# ---------------------------------------------------------------------------


def test_halfgrid_bbox_4x2():
    """4×2 half-grid bin outer dims = 4×21-0.5 × 2×21-0.5 mm."""
    b = GridfinityBox(4, 2, 3, half_grid=True, fillet_interior=False)
    assert b.half_grid is True
    r = b.render()
    assert r.val().isValid()
    sx, sy, sz = size_3d(r)
    assert _almost_same(sx, 4 * 21 - 0.5, tol=0.05)  # 83.5 mm
    assert _almost_same(sy, 2 * 21 - 0.5, tol=0.05)  # 41.5 mm


@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_halfgrid_bbox_2x2():
    """2×2 half-grid bin is 42×42mm outer — equivalent to a 1×1 full-grid bin."""
    b = GridfinityBox(2, 2, 3, half_grid=True, fillet_interior=False)
    r = b.render()
    assert r.val().isValid()
    sx, sy, sz = size_3d(r)
    assert _almost_same(sx, 2 * 21 - 0.5, tol=0.05)  # 41.5 mm
    assert _almost_same(sy, 2 * 21 - 0.5, tol=0.05)  # 41.5 mm


@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_halfgrid_isvalid():
    """Half-grid bins should render as valid closed solids."""
    b = GridfinityBox(4, 2, 4, half_grid=True, fillet_interior=False)
    r = b.render()
    assert r.val().isValid()


def test_halfgrid_grid_unit():
    """_gru property returns GRU2 (21mm) for half-grid, GRU (42mm) for standard."""
    from cqgridfinity.constants import GRU, GRU2
    b_hg = GridfinityBox(2, 2, 3, half_grid=True)
    b_std = GridfinityBox(2, 2, 3, half_grid=False)
    assert b_hg._gru == GRU2
    assert b_std._gru == GRU


def test_halfgrid_grid_centres_spacing():
    """grid_centres for half-grid use 21mm spacing."""
    b = GridfinityBox(4, 2, 3, half_grid=True)
    centres = b.grid_centres
    assert len(centres) == 8  # 4×2 = 8 centres
    # Check X spacing: should be 21mm steps
    x_vals = sorted(set(c[0] for c in centres))
    assert _almost_same(x_vals[1] - x_vals[0], 21.0)


def test_halfgrid_hole_centres_only_corners():
    """Half-grid bins use only_corners mapped to the equivalent full-grid frame.

    4×2 half-grid → floor(4/2)=2 × floor(2/2)=1 full-grid → 2 corner cells × 4 holes = 8.
    Holes are positioned at the 42mm-grid ±GR_HOLE_DIST offsets so they land
    within the bin walls and align with standard Gridfinity baseplates.
    """
    b = GridfinityBox(4, 2, 3, half_grid=True, holes=True)
    centres = b.hole_centres
    assert len(centres) == 8  # 2 full-grid corners × 4 holes each


def test_halfgrid_hole_centres_1x1():
    """1×1 half-grid bin: floor(1/2)=0 full-grid cells — no holes fit."""
    b = GridfinityBox(1, 1, 3, half_grid=True, holes=True)
    centres = b.hole_centres
    assert len(centres) == 0  # bin too small for 42mm-grid-aligned holes


def test_halfgrid_hole_centres_2x1():
    """2×1 half-grid: floor(1/2)=0 full-grid cells in Y — no holes fit (bin only 21mm tall)."""
    b = GridfinityBox(2, 1, 3, half_grid=True, holes=True)
    centres = b.hole_centres
    assert len(centres) == 0  # 21mm height is too narrow for ±13mm holes


def test_halfgrid_filename():
    """Half-grid filename includes '_hg' marker."""
    b = GridfinityBox(4, 2, 3, half_grid=True)
    fn = b.filename()
    assert "_hg" in fn


def _hole_within_footprint(b, px, py, tol=0.1):
    """Return True if the hole at local workplane (px, py) is within the bin footprint.

    hole_centres uses local workplane coords where global_Y = -py (workplane Y = global -Y).
    The bin outer footprint in pre-translation global XY is centred at half_dim.
    """
    x_min = b.half_l - b.outer_l / 2
    x_max = b.half_l + b.outer_l / 2
    y_min = b.half_w - b.outer_w / 2
    y_max = b.half_w + b.outer_w / 2
    gx, gy = px, -py
    return (x_min - tol < gx < x_max + tol) and (y_min - tol < gy < y_max + tol)


def test_halfgrid_hole_positions_within_bin_4x2():
    """All 8 hole centres for a 4×2 half-grid bin must lie within the outer footprint."""
    b = GridfinityBox(4, 2, 3, half_grid=True, holes=True)
    centres = b.hole_centres
    assert len(centres) == 8
    for px, py in centres:
        assert _hole_within_footprint(b, px, py), \
            f"Hole at local ({px:.2f}, {py:.2f}) → global ({px:.2f}, {-py:.2f}) outside footprint"


def test_halfgrid_hole_positions_within_bin_2x2():
    """All 4 hole centres for a 2×2 half-grid bin must lie within the outer footprint."""
    b = GridfinityBox(2, 2, 3, half_grid=True, holes=True)
    centres = b.hole_centres
    assert len(centres) == 4
    for px, py in centres:
        assert _hole_within_footprint(b, px, py), \
            f"Hole at local ({px:.2f}, {py:.2f}) → global ({px:.2f}, {-py:.2f}) outside footprint"


def test_halfgrid_2x2_holes_match_1x1_standard():
    """2×2 half-grid bin (42×42mm outer) has holes at the same final positions as a 1×1 standard bin."""
    b_hg = GridfinityBox(2, 2, 3, half_grid=True, holes=True)
    b_std = GridfinityBox(1, 1, 3, holes=True)
    # After translate(-half_l, -half_w, ...) in render(), final position in centred frame:
    #   x_final = px - half_l,  y_final = (-py) - half_w
    def final_positions(b):
        return sorted(
            (round(px - b.half_l, 3), round((-py) - b.half_w, 3))
            for px, py in b.hole_centres
        )
    assert final_positions(b_hg) == final_positions(b_std)


def test_halfgrid_standard_unchanged():
    """Non-half-grid bins are not affected by the new _gru property."""
    from cqgridfinity.constants import GRU
    b = GridfinityBox(2, 3, 4)
    assert b._gru == GRU
    # Outer dims unchanged
    assert _almost_same(b.outer_l, 2 * GRU - 0.5)
    assert _almost_same(b.outer_w, 3 * GRU - 0.5)


@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_halfgrid_with_holes():
    """Half-grid bin with holes should render without error."""
    b = GridfinityBox(4, 2, 3, half_grid=True, holes=True, fillet_interior=False)
    r = b.render()
    assert r.val().isValid()


@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_halfgrid_2x1_holes_renders():
    """2×1 half-grid with holes=True: hole_centres=[] so render is a no-op for holes."""
    b = GridfinityBox(2, 1, 3, half_grid=True, holes=True, fillet_interior=False)
    assert len(b.hole_centres) == 0
    r = b.render()
    assert r.val().isValid()


@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_halfgrid_1x1_holes_renders():
    """1×1 half-grid with holes=True: hole_centres=[] so render is a no-op for holes."""
    b = GridfinityBox(1, 1, 3, half_grid=True, holes=True, fillet_interior=False)
    assert len(b.hole_centres) == 0
    r = b.render()
    assert r.val().isValid()


@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_halfgrid_with_scoops_labels():
    """Half-grid bin with scoops and labels should render as valid solid."""
    b = GridfinityBox(4, 2, 4, half_grid=True, scoops=True, labels=True,
                      fillet_interior=False)
    r = b.render()
    assert r.val().isValid()
