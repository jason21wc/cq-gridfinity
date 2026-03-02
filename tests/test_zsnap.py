# Tests for 1B.15: Z-snap (round bin height to next 7mm Gridfinity multiple)
#
# Source: kennetek/gridfinity-rebuilt-utility.scad — z_snap() + height(z, gridz_define)
# Acceptance criteria from FEATURE-SPEC.md:
#   - enable_zsnap=False by default (no-op)
#   - Rounds up to next 7mm multiple: h + 7 - h%7 if not already a multiple
#   - Applied after gridz_define conversion (modes 0-3)
#   - Mode 0 with integer height_u: always a no-op (7*z is already a multiple of 7)
#   - Filename suffix _zs when enable_zsnap=True

import pytest

from cqgridfinity import GridfinityBox
from cqkit.cq_helpers import size_3d
from cqgridfinity.constants import GRHU, GR_LIP_H, GR_BOT_H, GR_STACKING_LIP_H
from common_test import _almost_same, SKIP_TEST_BOX


# ---------------------------------------------------------------------------
# Default / no-op behaviour
# ---------------------------------------------------------------------------

def test_zsnap_default_disabled():
    """enable_zsnap defaults to False."""
    b = GridfinityBox(2, 2, 5)
    assert b.enable_zsnap is False


def test_zsnap_mode0_integer_noop():
    """Mode 0 with integer height_u: enable_zsnap is a no-op (7*z already multiple of 7)."""
    b_off = GridfinityBox(2, 2, 5)
    b_on  = GridfinityBox(2, 2, 5, enable_zsnap=True)
    assert abs(b_on.height - b_off.height) < 1e-6


def test_zsnap_mode0_integer_various():
    """No-op for several integer z-units."""
    for z in (1, 2, 3, 4, 5, 10):
        b_off = GridfinityBox(1, 1, z)
        b_on  = GridfinityBox(1, 1, z, enable_zsnap=True)
        assert abs(b_on.height - b_off.height) < 1e-6, f"z={z} should be a no-op"


# ---------------------------------------------------------------------------
# Mode 0: float height_u (non-integer from 1B.12 non-integer grid)
# ---------------------------------------------------------------------------

def test_zsnap_mode0_float_snaps_up():
    """Mode 0 with float height_u=2.5 snaps to 3 units: 3.8 + 3*7 = 24.8mm."""
    b = GridfinityBox(2, 2, 2.5, enable_zsnap=True)
    expected = 3.8 + 3 * GRHU  # 24.8mm
    assert abs(b.height - expected) < 1e-6


def test_zsnap_mode0_float_15_snaps_to_2():
    """Mode 0 with height_u=1.5 snaps to 2 units: 3.8 + 2*7 = 17.8mm."""
    b = GridfinityBox(2, 2, 1.5, enable_zsnap=True)
    expected = 3.8 + 2 * GRHU  # 17.8mm
    assert abs(b.height - expected) < 1e-6


def test_zsnap_mode0_float_already_integer_equivalent():
    """Mode 0 with height_u=3.0 (float but exact integer): no-op."""
    b_off = GridfinityBox(2, 2, 3.0)
    b_on  = GridfinityBox(2, 2, 3.0, enable_zsnap=True)
    assert abs(b_on.height - b_off.height) < 1e-6


# ---------------------------------------------------------------------------
# Mode 1: height_u in internal usable mm
# ---------------------------------------------------------------------------

def test_zsnap_mode1_multiple_of_7_noop():
    """Mode 1 with height_u=28 (4*7): snap is a no-op."""
    b_off = GridfinityBox(2, 2, 28.0, gridz_define=1)
    b_on  = GridfinityBox(2, 2, 28.0, gridz_define=1, enable_zsnap=True)
    assert abs(b_on.height - b_off.height) < 1e-6


def test_zsnap_mode1_snaps_up():
    """Mode 1 with height_u=25mm snaps to 28mm internal: height = 28 + GR_LIP_H + GR_BOT_H."""
    b = GridfinityBox(2, 2, 25.0, gridz_define=1, enable_zsnap=True)
    expected = 28.0 + GR_LIP_H + GR_BOT_H
    assert abs(b.height - expected) < 1e-6


def test_zsnap_mode1_30mm_snaps_to_35():
    """Mode 1 with height_u=30mm snaps to 35mm (5*7)."""
    b = GridfinityBox(2, 2, 30.0, gridz_define=1, enable_zsnap=True)
    expected = 35.0 + GR_LIP_H + GR_BOT_H
    assert abs(b.height - expected) < 1e-6


# ---------------------------------------------------------------------------
# Mode 2: height_u is total external mm
# ---------------------------------------------------------------------------

def test_zsnap_mode2_standard_height_noop():
    """Mode 2 with a standard Gridfinity height (3.8 + k*7) is a no-op."""
    standard = 3.8 + 5 * GRHU  # 38.8mm — same as mode 0, z=5
    b_off = GridfinityBox(2, 2, standard, gridz_define=2)
    b_on  = GridfinityBox(2, 2, standard, gridz_define=2, enable_zsnap=True)
    assert abs(b_on.height - b_off.height) < 1e-6


def test_zsnap_mode2_nonstandard_snaps_up():
    """Mode 2 with 35mm external snaps to 38.8mm (next standard height = 3.8 + 5*7)."""
    b = GridfinityBox(2, 2, 35.0, gridz_define=2, enable_zsnap=True)
    expected = 3.8 + 5 * GRHU  # 38.8mm
    assert abs(b.height - expected) < 1e-6


# ---------------------------------------------------------------------------
# Mode 3: height_u in external mm including stacking lip
# ---------------------------------------------------------------------------

def test_zsnap_mode3_standard_noop():
    """Mode 3 with a standard height + stacking lip is a no-op."""
    standard_raw = 3.8 + 5 * GRHU   # 38.8mm raw height
    height_u_m3 = standard_raw + GR_STACKING_LIP_H
    b_off = GridfinityBox(2, 2, height_u_m3, gridz_define=3)
    b_on  = GridfinityBox(2, 2, height_u_m3, gridz_define=3, enable_zsnap=True)
    assert abs(b_on.height - b_off.height) < 1e-6


def test_zsnap_mode3_nonstandard_snaps():
    """Mode 3 with non-standard input snaps to next standard height.

    height_u = 39.4mm (content_before_snap = 39.4 - 4.4 - 3.8 = 31.2mm).
    z_snap(31.2) = 35mm. Snapped result = 35 + 3.8 = 38.8mm.
    """
    # height_u chosen so content = 31.2mm (not a multiple of 7):
    # z = content + GR_STACKING_LIP_H + 3.8 = 31.2 + 4.4 + 3.8 = 39.4mm
    b = GridfinityBox(2, 2, 39.4, gridz_define=3, enable_zsnap=True)
    expected = 3.8 + 5 * GRHU  # 38.8mm
    assert abs(b.height - expected) < 1e-6


# ---------------------------------------------------------------------------
# Snap equivalence: snapped float == unsnapped next-integer
# ---------------------------------------------------------------------------

def test_zsnap_mode0_snap_equals_next_integer():
    """Mode 0 z-snap on 2.5 units produces same height as integer 3 units (no snap)."""
    b_snap = GridfinityBox(2, 2, 2.5, enable_zsnap=True)
    b_int  = GridfinityBox(2, 2, 3)    # integer z — snap is a no-op
    assert abs(b_snap.height - b_int.height) < 1e-6


def test_zsnap_mode1_snap_equals_rounded_mode0():
    """Mode 1 z-snap on 25mm produces height matching a mode-0 integer bin.

    25mm snaps to 28mm (4*7). The resulting height = 28 + GR_LIP_H + GR_BOT_H.
    Verify this matches the property, not a cross-mode comparison.
    """
    b = GridfinityBox(2, 2, 25.0, gridz_define=1, enable_zsnap=True)
    assert abs(b.int_height - 28.0) < 1e-6  # internal space = next 7mm multiple


# ---------------------------------------------------------------------------
# Filename suffix
# ---------------------------------------------------------------------------

def test_zsnap_filename_suffix_present():
    """enable_zsnap=True adds _zs to filename."""
    b = GridfinityBox(2, 2, 5, enable_zsnap=True)
    assert "_zs" in b.filename()


def test_zsnap_filename_suffix_absent_by_default():
    """enable_zsnap=False (default) does NOT add _zs."""
    b = GridfinityBox(2, 2, 5)
    assert "_zs" not in b.filename()


def test_zsnap_filename_with_mode():
    """_zs appears after _m{N} in filename."""
    b = GridfinityBox(2, 2, 25.0, gridz_define=1, enable_zsnap=True)
    fn = b.filename()
    assert "_m1" in fn
    assert "_zs" in fn
    assert fn.index("_m1") < fn.index("_zs")


# ---------------------------------------------------------------------------
# Render test (geometry validity)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_zsnap_renders_valid_solid():
    """A z-snapped bin (mode 1, 25mm → 28mm) renders a valid solid with correct Z."""
    b = GridfinityBox(2, 2, 25.0, gridz_define=1, enable_zsnap=True, fillet_interior=False)
    r = b.render()
    assert r.val().isValid()
    sx, sy, sz = size_3d(r)
    expected_z = 28.0 + GR_LIP_H + GR_BOT_H
    assert _almost_same(sz, expected_z, tol=0.2)


@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_zsnap_mode0_float_renders():
    """Z-snap on mode 0 float height_u (2.5→3 units) renders valid solid."""
    b = GridfinityBox(2, 2, 2.5, enable_zsnap=True, fillet_interior=False)
    r = b.render()
    assert r.val().isValid()
    sx, sy, sz = size_3d(r)
    expected_z = 3.8 + 3 * GRHU  # 24.8mm
    assert _almost_same(sz, expected_z, tol=0.2)
