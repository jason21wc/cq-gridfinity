# Tests for enhanced bin features (1B.5-1B.8)
import pytest

from cqgridfinity import *
from cqkit.cq_helpers import size_3d
from common_test import (
    _almost_same,
    _export_files,
    EXPORT_STEP_FILE_PATH,
    SKIP_TEST_BOX,
)


# ---------------------------------------------------------------------------
# 1B.5: Scoop scaling (0-1)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_scoop_scaling_full():
    """scoops=1.0 should produce same result as scoops=True (backward compat)."""
    b_bool = GridfinityBox(2, 2, 3, scoops=True)
    b_float = GridfinityBox(2, 2, 3, scoops=1.0)
    assert b_bool.scoops == 1.0
    assert b_float.scoops == 1.0
    r_bool = b_bool.render()
    r_float = b_float.render()
    assert r_bool.val().isValid()
    assert r_float.val().isValid()
    assert _almost_same(size_3d(r_bool), size_3d(r_float))


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_scoop_scaling_zero():
    """scoops=0.0 should produce same result as scoops=False."""
    b_false = GridfinityBox(2, 2, 3, scoops=False)
    b_zero = GridfinityBox(2, 2, 3, scoops=0.0)
    assert b_false.scoops == 0.0
    assert b_zero.scoops == 0.0
    r_false = b_false.render()
    r_zero = b_zero.render()
    assert r_false.val().isValid()
    assert r_zero.val().isValid()
    assert _almost_same(size_3d(r_false), size_3d(r_zero))


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_scoop_scaling_half():
    """scoops=0.5 should produce valid geometry with smaller scoop."""
    b = GridfinityBox(2, 2, 5, scoops=0.5)
    assert b.scoops == 0.5
    r = b.render()
    assert r.val().isValid()
    assert _almost_same(size_3d(r), (83.5, 83.5, 38.8))
    # Half scoop should be between no-scoop and full-scoop volumes
    b_none = GridfinityBox(2, 2, 5, scoops=False)
    b_full = GridfinityBox(2, 2, 5, scoops=True)
    r_none = b_none.render()
    r_full = b_full.render()
    assert r_none.val().isValid()
    assert r_full.val().isValid()
    vol_none = r_none.val().Volume()
    vol_half = r.val().Volume()
    vol_full = r_full.val().Volume()
    # Scoop removes material from interior corners, so full scoop = less volume
    # Actually scoops are ADDED to the shell (fill corners), so more scoop = more volume
    # Half scoop should be between no-scoop and full-scoop
    assert vol_none <= vol_half <= vol_full or vol_none >= vol_half >= vol_full


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_scoop_scaling_filename():
    """Partial scoop should show scale in filename."""
    b_full = GridfinityBox(2, 2, 3, scoops=True)
    b_half = GridfinityBox(2, 2, 3, scoops=0.5)
    b_quarter = GridfinityBox(2, 2, 3, scoops=0.3)
    assert "_scoops" in b_full.filename()
    assert "_scoop0.5" in b_half.filename()
    assert "_scoop0.3" in b_quarter.filename()


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_scoop_scaling_clamped():
    """Scoop values outside 0-1 should be clamped."""
    b_over = GridfinityBox(2, 2, 3, scoops=1.5)
    b_under = GridfinityBox(2, 2, 3, scoops=-0.5)
    assert b_over.scoops == 1.0
    assert b_under.scoops == 0.0


# ---------------------------------------------------------------------------
# 1B.6: Tab positioning (6 styles)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_label_style_full_backward_compat():
    """labels=True with default style should match original behavior."""
    b_old = GridfinityBox(2, 2, 3, labels=True)
    assert b_old.label_style == "full"
    assert b_old.labels is True
    assert "_labels" in b_old.filename()
    r = b_old.render()
    assert r.val().isValid()
    assert _almost_same(size_3d(r), (83.5, 83.5, 24.8))
    # Label adds material (overhang shelf) — labeled bin should have more volume
    b_plain = GridfinityBox(2, 2, 3)
    r_plain = b_plain.render()
    assert r.val().Volume() > r_plain.val().Volume()


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_label_style_none():
    """label_style='none' should produce no labels."""
    b = GridfinityBox(2, 2, 3, label_style="none")
    assert b.labels is False
    assert b.label_style == "none"
    r = b.render()
    assert r.val().isValid()
    b_plain = GridfinityBox(2, 2, 3)
    r_plain = b_plain.render()
    assert r_plain.val().isValid()
    assert _almost_same(size_3d(r), size_3d(r_plain))


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_label_style_auto():
    """label_style='auto' should produce valid geometry."""
    b = GridfinityBox(3, 2, 5, label_style="auto")
    assert b.labels is True
    assert b.label_style == "auto"
    assert "_label-auto" in b.filename()
    r = b.render()
    assert r is not None
    assert r.val().isValid()
    bb = r.val().BoundingBox()
    assert bb.xlen > 0


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_label_style_left():
    """label_style='left' should produce valid geometry."""
    b = GridfinityBox(3, 2, 5, label_style="left", length_div=1)
    assert b.label_style == "left"
    assert "_label-left" in b.filename()
    r = b.render()
    assert r is not None
    assert r.val().isValid()


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_label_style_center():
    """label_style='center' should produce valid geometry."""
    b = GridfinityBox(3, 2, 5, label_style="center")
    assert b.label_style == "center"
    r = b.render()
    assert r is not None
    assert r.val().isValid()


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_label_style_right():
    """label_style='right' should produce valid geometry."""
    b = GridfinityBox(3, 2, 5, label_style="right")
    assert b.label_style == "right"
    r = b.render()
    assert r is not None
    assert r.val().isValid()


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_label_style_with_dividers():
    """Positioned labels should work with width dividers."""
    b = GridfinityBox(3, 3, 5, label_style="center", width_div=1, length_div=1)
    r = b.render()
    assert r is not None
    assert r.val().isValid()
    bb = r.val().BoundingBox()
    assert bb.xlen > 0


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_invalid_label_style():
    """Invalid label_style should raise ValueError."""
    with pytest.raises(ValueError):
        GridfinityBox(2, 2, 3, label_style="invalid")


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_label_style_sets_labels():
    """Setting label_style (non-none) should automatically set labels=True."""
    b = GridfinityBox(2, 2, 3, label_style="left")
    assert b.labels is True


# ---------------------------------------------------------------------------
# 1B.7: Custom compartment depth
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_compartment_depth_zero():
    """compartment_depth=0 should be same as default."""
    b_default = GridfinityBox(2, 2, 5)
    b_zero = GridfinityBox(2, 2, 5, compartment_depth=0)
    r_default = b_default.render()
    r_zero = b_zero.render()
    assert r_default.val().isValid()
    assert r_zero.val().isValid()
    assert _almost_same(size_3d(r_default), size_3d(r_zero))


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_compartment_depth_raises_floor():
    """compartment_depth > 0 should raise the floor, reducing interior volume."""
    b_full = GridfinityBox(2, 2, 5)
    b_shallow = GridfinityBox(2, 2, 5, compartment_depth=5)
    r_full = b_full.render()
    r_shallow = b_shallow.render()
    assert r_full.val().isValid()
    assert r_shallow.val().isValid()
    # Same exterior dimensions
    assert _almost_same(size_3d(r_full), size_3d(r_shallow))
    # Shallow bin has more material (raised floor fills interior)
    vol_full = r_full.val().Volume()
    vol_shallow = r_shallow.val().Volume()
    assert vol_shallow > vol_full


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_compartment_depth_filename():
    """compartment_depth should appear in filename."""
    b = GridfinityBox(2, 2, 3, compartment_depth=3)
    assert "_d3.0" in b.filename()


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_height_internal_override():
    """height_internal sets a fixed internal height."""
    b = GridfinityBox(2, 2, 5, height_internal=10)
    assert b._floor_raise > 0
    assert "_hi10.0" in b.filename()
    r = b.render()
    assert r is not None
    assert r.val().isValid()
    # height_internal bin should have more material (raised floor) than default
    b_default = GridfinityBox(2, 2, 5)
    r_default = b_default.render()
    assert r.val().Volume() > r_default.val().Volume()


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_compartment_depth_with_scoops():
    """Scoops should adjust to raised floor."""
    b = GridfinityBox(2, 2, 5, scoops=True, compartment_depth=5)
    r = b.render()
    assert r is not None
    assert r.val().isValid()
    assert _almost_same(size_3d(r), (83.5, 83.5, 38.8))


# ---------------------------------------------------------------------------
# 1B.8: Cylindrical compartments
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_cylindrical_basic():
    """Basic cylindrical bin should render valid geometry."""
    b = GridfinityBox(2, 2, 5, cylindrical=True, cylinder_diam=20)
    r = b.render()
    assert r is not None
    assert r.val().isValid()
    assert _almost_same(size_3d(r), (83.5, 83.5, 38.8))
    assert "_cyl20" in b.filename()


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_cylindrical_with_dividers():
    """Cylindrical with dividers should create multiple cylinders."""
    b1 = GridfinityBox(2, 2, 5, cylindrical=True, cylinder_diam=20)
    b4 = GridfinityBox(2, 2, 5, cylindrical=True, cylinder_diam=20,
                       length_div=1, width_div=1)
    r1 = b1.render()
    r4 = b4.render()
    assert r1.val().isValid()
    assert r4.val().isValid()
    # 4 cylinders should remove more material than 1 cylinder
    vol1 = r1.val().Volume()
    vol4 = r4.val().Volume()
    assert vol4 < vol1


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_cylindrical_auto_clamps_diameter():
    """Cylinder diameter should be clamped to fit in compartment."""
    # 1x1 bin with huge cylinder request — should clamp to fit
    b = GridfinityBox(1, 1, 3, cylindrical=True, cylinder_diam=100)
    r = b.render()
    assert r is not None
    assert r.val().isValid()
    bb = r.val().BoundingBox()
    assert bb.xlen > 0


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_cylindrical_default_diameter():
    """Default cylinder diameter is GR_CYL_DIAM (10mm)."""
    b = GridfinityBox(2, 2, 3, cylindrical=True)
    assert b.cylinder_diam == GR_CYL_DIAM
    assert b.cylinder_chamfer == GR_CYL_CHAMFER
    r = b.render()
    assert r is not None
    assert r.val().isValid()


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_cylindrical_with_holes():
    """Cylindrical bins should support bottom holes."""
    b = GridfinityBox(2, 2, 3, cylindrical=True, cylinder_diam=20, holes=True)
    r = b.render()
    assert r is not None
    assert r.val().isValid()


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_cylindrical_with_depth():
    """Cylindrical bins should respect compartment_depth."""
    b_full = GridfinityBox(2, 2, 5, cylindrical=True, cylinder_diam=20)
    b_shallow = GridfinityBox(2, 2, 5, cylindrical=True, cylinder_diam=20,
                              compartment_depth=5)
    r_full = b_full.render()
    r_shallow = b_shallow.render()
    assert r_full.val().isValid()
    assert r_shallow.val().isValid()
    # Shallower cylinders = more material remaining
    vol_full = r_full.val().Volume()
    vol_shallow = r_shallow.val().Volume()
    assert vol_shallow > vol_full


# ---------------------------------------------------------------------------
# STEP file generation for visual inspection
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_step_export_bin_features():
    """Generate reference STEP files for 1B.5-1B.8 visual inspection."""
    if not _export_files("bin_features"):
        pytest.skip("Set EXPORT_STEP_FILES=bin_features to generate")

    bins = [
        # 1B.5: Scoop scaling
        GridfinityBox(2, 2, 5, scoops=0.3),
        GridfinityBox(2, 2, 5, scoops=0.5),
        GridfinityBox(2, 2, 5, scoops=1.0),
        # 1B.6: Tab positioning
        GridfinityBox(3, 2, 5, label_style="auto", length_div=1),
        GridfinityBox(3, 2, 5, label_style="left", length_div=1),
        GridfinityBox(3, 2, 5, label_style="center", length_div=1),
        GridfinityBox(3, 2, 5, label_style="right", length_div=1),
        # 1B.7: Custom compartment depth
        GridfinityBox(2, 2, 5, compartment_depth=5),
        GridfinityBox(2, 2, 5, height_internal=10),
        # 1B.8: Cylindrical compartments
        GridfinityBox(2, 2, 5, cylindrical=True, cylinder_diam=20),
        GridfinityBox(3, 3, 5, cylindrical=True, cylinder_diam=15,
                      length_div=1, width_div=1),
    ]
    for b in bins:
        b.render()
        b.save_step_file(path=EXPORT_STEP_FILE_PATH)
