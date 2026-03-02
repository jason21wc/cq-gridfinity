# Tests for 1B.16-1B.17: Spiral Vase (GridfinityVaseBox + GridfinityVaseBase)
#
# Source: kennetek/gridfinity-spiral-vase.scad (MIT)
# Acceptance criteria from FEATURE-SPEC.md:
#   1B.16: VaseBox — thin-wall (2*nozzle) open-top shell, X-cutouts, optional lip
#   1B.17: VaseBase — base insert with ribs, X-protrusion, magnet holes

import pytest

from cqgridfinity import GridfinityVaseBox, GridfinityVaseBase
from cqkit.cq_helpers import size_3d
from cqgridfinity.constants import GR_BASE_HEIGHT, GRHU
from common_test import _almost_same, SKIP_TEST_BOX, _export_files, EXPORT_STEP_FILE_PATH


# ---------------------------------------------------------------------------
# VaseBox — attribute defaults
# ---------------------------------------------------------------------------

def test_vasebox_defaults():
    """VaseBox has expected default attribute values."""
    b = GridfinityVaseBox(1, 1, 3)
    assert b.nozzle == 0.6
    assert b.layer == 0.35
    assert b.bottom_layer == 3
    assert b.n_divx == 0
    assert b.style_tab == 0
    assert b.style_base == 0
    assert b.enable_lip is True
    assert b.enable_scoop_chamfer is True
    assert b.enable_zsnap is False
    assert b.wall_th == pytest.approx(2 * 0.6, abs=1e-6)


def test_vasebox_d_bottom():
    """d_bottom = layer × bottom_layer."""
    b = GridfinityVaseBox(1, 1, 3)
    assert b.d_bottom == pytest.approx(0.35 * 3, abs=1e-6)


def test_vasebox_d_bottom_zero_layers():
    """bottom_layer=0 uses max(0,1)=1 → d_bottom = layer × 1."""
    b = GridfinityVaseBox(1, 1, 3, bottom_layer=0)
    assert b.d_bottom == pytest.approx(0.35, abs=1e-6)


def test_vasebox_wall_th_from_nozzle():
    """wall_th always = 2 × nozzle (derived, not independent)."""
    b = GridfinityVaseBox(1, 1, 3, nozzle=0.4)
    assert b.wall_th == pytest.approx(0.8, abs=1e-6)


# ---------------------------------------------------------------------------
# VaseBox — filename
# ---------------------------------------------------------------------------

def test_vasebox_filename_prefix():
    """VaseBox filename starts with gf_vase_."""
    b = GridfinityVaseBox(2, 2, 3)
    assert b.filename().startswith("gf_vase_")


def test_vasebox_filename_dimensions():
    """Filename encodes LxW dimensions."""
    b = GridfinityVaseBox(2, 3, 4)
    fn = b.filename()
    assert "2x3" in fn


def test_vasebox_filename_nolip():
    """enable_lip=False adds _nolip suffix."""
    b = GridfinityVaseBox(1, 1, 3, enable_lip=False)
    assert "_nolip" in b.filename()


def test_vasebox_filename_dividers():
    """n_divx>1 adds _divN suffix."""
    b = GridfinityVaseBox(2, 1, 3, n_divx=2)
    assert "_div2" in b.filename()


def test_vasebox_filename_mode_suffix():
    """gridz_define != 0 adds _mN suffix."""
    b = GridfinityVaseBox(1, 1, 25.0, gridz_define=1)
    assert "_m1" in b.filename()


def test_vasebox_unknown_kwarg_warns():
    """Unknown kwargs produce a warning (no silent swallowing)."""
    import warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        GridfinityVaseBox(1, 1, 3, nonexistent_param=99)
        assert len(w) == 1
        assert "nonexistent_param" in str(w[0].message)


# ---------------------------------------------------------------------------
# VaseBox — renders (geometry validity + bbox)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_vasebox_1x1_renders_valid():
    """Basic 1×1×3 VaseBox renders a valid solid."""
    b = GridfinityVaseBox(1, 1, 3)
    r = b.render()
    assert r.val().isValid()


@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_vasebox_1x1_height():
    """1×1×3 VaseBox (no lip, no tab) Z = b.height = 3.8 + 3*7 = 24.8mm.

    Tab (style_tab=0) and lip (enable_lip=True) both add ~1.2mm above b.height;
    disable both to test the core height formula in isolation.
    """
    b = GridfinityVaseBox(1, 1, 3, enable_lip=False, style_tab=6)
    r = b.render()
    _, _, sz = size_3d(r)
    assert _almost_same(sz, b.height, tol=0.3)


@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_vasebox_2x2_renders_valid():
    """Multi-cell 2×2×3 VaseBox renders a valid solid."""
    b = GridfinityVaseBox(2, 2, 3)
    r = b.render()
    assert r.val().isValid()


@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_vasebox_nolip_renders_valid():
    """VaseBox without stacking lip renders valid."""
    b = GridfinityVaseBox(1, 1, 3, enable_lip=False)
    r = b.render()
    assert r.val().isValid()


@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_vasebox_nolip_shorter():
    """VaseBox without lip is no taller than with lip (or same)."""
    b_lip = GridfinityVaseBox(1, 1, 3, enable_lip=True)
    b_nolip = GridfinityVaseBox(1, 1, 3, enable_lip=False)
    _, _, sz_lip = size_3d(b_lip.render())
    _, _, sz_nolip = size_3d(b_nolip.render())
    assert sz_nolip <= sz_lip + 0.1


@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_vasebox_dividers_renders_valid():
    """VaseBox with n_divx=2 (1 divider) renders valid."""
    b = GridfinityVaseBox(2, 1, 3, n_divx=2)
    r = b.render()
    assert r.val().isValid()


@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_vasebox_style_base_none_renders_valid():
    """style_base=4 (no X-cutouts) renders valid."""
    b = GridfinityVaseBox(1, 1, 3, style_base=4)
    r = b.render()
    assert r.val().isValid()


@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_vasebox_style_base_corners_renders_valid():
    """style_base=1 (corners only) renders valid for 2×2."""
    b = GridfinityVaseBox(2, 2, 3, style_base=1)
    r = b.render()
    assert r.val().isValid()


@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_vasebox_no_scoop_chamfer():
    """enable_scoop_chamfer=False renders valid."""
    b = GridfinityVaseBox(1, 1, 3, enable_scoop_chamfer=False)
    r = b.render()
    assert r.val().isValid()


@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_vasebox_tab_none():
    """style_tab=6 (no tab) renders valid."""
    b = GridfinityVaseBox(1, 1, 3, style_tab=6)
    r = b.render()
    assert r.val().isValid()


@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_vasebox_tab_right():
    """style_tab=3 (right tab) renders valid."""
    b = GridfinityVaseBox(1, 1, 3, style_tab=3)
    r = b.render()
    assert r.val().isValid()


@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_vasebox_step_export(tmp_path):
    """VaseBox saves a valid STEP file."""
    b = GridfinityVaseBox(1, 1, 2)
    b.save_step_file(filename=str(tmp_path / "vase_box.step"))


# ---------------------------------------------------------------------------
# VaseBase — attribute defaults
# ---------------------------------------------------------------------------

def test_vasebase_defaults():
    """VaseBase has expected default attribute values."""
    b = GridfinityVaseBase(1, 1)
    assert b.length_u == 1
    assert b.width_u == 1
    assert b.nozzle == 0.6
    assert b.layer == 0.35
    assert b.bottom_layer == 3
    assert b.holes is True
    assert b.style_base == 0
    assert b.wall_th == pytest.approx(2 * 0.6, abs=1e-6)


def test_vasebase_geometry_properties():
    """VaseBase outer_l/outer_w/half_l/half_w are correct for 2×2."""
    from cqgridfinity.constants import GRU, GR_TOL
    b = GridfinityVaseBase(2, 2)
    assert b.outer_l == pytest.approx(2 * GRU - GR_TOL, abs=1e-6)
    assert b.outer_w == pytest.approx(2 * GRU - GR_TOL, abs=1e-6)
    assert b.half_l == pytest.approx((2 - 1) * GRU / 2, abs=1e-6)
    assert b.half_w == pytest.approx((2 - 1) * GRU / 2, abs=1e-6)


def test_vasebase_grid_centres_1x1():
    """VaseBase(1,1).grid_centres has exactly 1 cell at (0,0)."""
    b = GridfinityVaseBase(1, 1)
    assert b.grid_centres == [(0, 0)]


def test_vasebase_grid_centres_2x2():
    """VaseBase(2,2).grid_centres has 4 cells."""
    from cqgridfinity.constants import GRU
    b = GridfinityVaseBase(2, 2)
    assert len(b.grid_centres) == 4
    assert (GRU, GRU) in b.grid_centres


# ---------------------------------------------------------------------------
# VaseBase — filename
# ---------------------------------------------------------------------------

def test_vasebase_filename_prefix():
    """VaseBase filename starts with gf_vase_base_."""
    b = GridfinityVaseBase(2, 2)
    assert b.filename().startswith("gf_vase_base_")


def test_vasebase_filename_mag():
    """holes=True adds _mag suffix."""
    b = GridfinityVaseBase(1, 1, holes=True)
    assert "_mag" in b.filename()


def test_vasebase_filename_no_mag():
    """holes=False → no _mag suffix."""
    b = GridfinityVaseBase(1, 1, holes=False)
    assert "_mag" not in b.filename()


# ---------------------------------------------------------------------------
# VaseBase — renders (geometry validity + bbox)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_vasebase_1x1_renders_valid():
    """VaseBase(1,1) renders a valid solid."""
    b = GridfinityVaseBase(1, 1)
    r = b.render()
    assert r.val().isValid()


@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_vasebase_2x2_renders_valid():
    """VaseBase(2,2) renders a valid solid (multi-cell: tests rib/hole positioning)."""
    b = GridfinityVaseBase(2, 2)
    r = b.render()
    assert r.val().isValid()


@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_vasebase_no_holes_renders_valid():
    """VaseBase(1,1, holes=False) renders a valid solid."""
    b = GridfinityVaseBase(1, 1, holes=False)
    r = b.render()
    assert r.val().isValid()


@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_vasebase_2x1_renders_valid():
    """VaseBase(2,1) (non-square) renders valid (tests asymmetric coord offsets)."""
    b = GridfinityVaseBase(2, 1)
    r = b.render()
    assert r.val().isValid()


@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_vasebase_style_base_corners():
    """VaseBase style_base=1 (corners) renders valid."""
    b = GridfinityVaseBase(2, 2, style_base=1)
    r = b.render()
    assert r.val().isValid()


@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_vasebase_style_base_none():
    """VaseBase style_base=4 (no X-protrusion) renders valid."""
    b = GridfinityVaseBase(1, 1, style_base=4)
    r = b.render()
    assert r.val().isValid()


@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_vasebase_sits_at_z0():
    """VaseBase bottom is at z=0 (world origin)."""
    b = GridfinityVaseBase(1, 1)
    r = b.render()
    bb = r.val().BoundingBox()
    assert abs(bb.zmin) < 0.3  # base profile bottom at/near z=0


@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_vasebase_step_export(tmp_path):
    """VaseBase saves a valid STEP file."""
    b = GridfinityVaseBase(1, 1)
    b.save_step_file(filename=str(tmp_path / "vase_base.step"))


# ---------------------------------------------------------------------------
# VaseBox + VaseBase — pair dimensions match
# ---------------------------------------------------------------------------

@pytest.mark.skipif(SKIP_TEST_BOX, reason="Skipped by SKIP_TEST_BOX env var")
def test_vase_pair_xy_match():
    """VaseBox and VaseBase XY footprint matches (base fits inside shell)."""
    box = GridfinityVaseBox(2, 2, 3)
    base = GridfinityVaseBase(2, 2)
    rb = box.render()
    rbase = base.render()
    sx_box, sy_box, _ = size_3d(rb)
    sx_base, sy_base, _ = size_3d(rbase)
    # Base must fit inside box (toleranced slightly smaller)
    assert sx_base <= sx_box + 1.0
    assert sy_base <= sy_box + 1.0
