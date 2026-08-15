# Gridfinity tests
import pytest

# my modules
from cqgridfinity import *

from cqkit.cq_helpers import *
from cqkit import *

from common_test import (
    EXPORT_STEP_FILE_PATH,
    _almost_same,
    _edges_match,
    _faces_match,
    _export_files,
    SKIP_TEST_BOX,
)


@pytest.mark.slow
@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_basic_box():
    b1 = GridfinityBox(2, 3, 5, no_lip=True)
    r = b1.render()
    assert r.val().isValid()
    assert _almost_same(size_3d(r), (83.5, 125.5, b1.actual_height))
    # no_lip has no contoured lip, so no tip fillet: a flat rim, as before.
    assert _faces_match(r, ">Z", 1)
    assert _faces_match(r, "<Z", 6)
    assert _edges_match(r, ">Z", 16)
    assert _edges_match(r, "<Z", 48)
    assert b1.filename() == "gf_bin_2x3x5_nolip"
    if _export_files("box"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)
    b1 = GridfinityBox(2, 3, 5, no_lip=True)
    if _export_files("box"):
        b1.wall_th = 1.5
        r = b1.render()
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_invalid_box():
    with pytest.raises(ValueError):
        b1 = GridfinityBox(2, 3, 5, lite_style=True, solid=True)
        b1.render()
    with pytest.raises(ValueError):
        b1 = GridfinityBox(2, 3, 5, lite_style=True, holes=True)
        b1.render()
    with pytest.raises(ValueError):
        b1 = GridfinityBox(2, 3, 5, lite_style=True, wall_th=2.0)
        b1.render()
    with pytest.raises(ValueError):
        b1 = GridfinityBox(2, 3, 5, wall_th=0.4)
        b1.render()
    with pytest.raises(ValueError):
        b1 = GridfinityBox(2, 3, 5, wall_th=3.0)
        b1.render()


@pytest.mark.slow
@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_lite_box():
    b1 = GridfinityBox(2, 3, 5, lite_style=True)
    r = b1.render()
    assert r.val().isValid()
    if _export_files("box"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)
    assert _almost_same(size_3d(r), (83.5, 125.5, b1.actual_height))
    assert _faces_match(r, ">Z", 4)  # filleted lip tip, not a flat rim
    assert _faces_match(r, "<Z", 6)
    assert _edges_match(r, ">Z", 16)
    assert _edges_match(r, "<Z", 48)
    assert b1.filename() == "gf_bin_2x3x5_lite"
    if _export_files("box"):
        b1 = GridfinityBox(2, 3, 5, lite_style=True)
        b1.wall_th = 1.2
        r = b1.render()
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)

    b1 = GridfinityBox(1, 1, 1, lite_style=True)
    r = b1.render()
    assert r.val().isValid()
    if _export_files("box"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)
    assert _almost_same(size_3d(r), (41.5, 41.5, b1.actual_height))

    b1 = GridfinityBox(1, 1, 2, lite_style=True)
    r = b1.render()
    assert r.val().isValid()
    if _export_files("box"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)
    assert _almost_same(size_3d(r), (41.5, 41.5, b1.actual_height))


@pytest.mark.slow
@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_empty_box():
    b1 = GridfinityBox(2, 3, 5, holes=True)
    r = b1.render()
    assert r.val().isValid()
    if _export_files("box"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)
    assert _almost_same(size_3d(r), (83.5, 125.5, b1.actual_height))
    assert _faces_match(r, ">Z", 4)  # filleted lip tip, not a flat rim
    assert _faces_match(r, "<Z", 6)
    assert _edges_match(r, ">Z", 16)
    assert _edges_match(r, "<Z", 72)
    assert b1.filename() == "gf_bin_2x3x5_mag"
    assert _almost_same(b1.top_ref_height, 7)
    if _export_files("box"):
        b1 = GridfinityBox(2, 3, 5, holes=True)
        b1.wall_th = 1.5
        r = b1.render()
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)

    b1 = GridfinityBox(1, 1, 1)
    r = b1.render()
    assert r.val().isValid()
    if _export_files("box"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)
    assert _almost_same(size_3d(r), (41.5, 41.5, b1.actual_height))

    b1 = GridfinityBox(1, 1, 2)
    r = b1.render()
    assert r.val().isValid()
    if _export_files("box"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)
    assert _almost_same(size_3d(r), (41.5, 41.5, b1.actual_height))


@pytest.mark.slow
@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_solid_box():
    b1 = GridfinitySolidBox(4, 2, 3)
    r = b1.render()
    assert r.val().isValid()
    if _export_files("box"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)
    assert _almost_same(size_3d(r), (167.5, 83.5, b1.actual_height))
    assert _faces_match(r, ">Z", 4)  # filleted lip tip, not a flat rim
    assert _faces_match(r, "<Z", 8)
    assert _edges_match(r, ">Z", 16)
    assert _edges_match(r, "<Z", 64)
    assert len(r.faces(FlatFaceSelector(21)).vals()) == 1
    assert len(r.edges(FlatEdgeSelector(21)).vals()) == 8
    assert b1.filename() == "gf_bin_4x2x3_solid"
    assert _almost_same(b1.top_ref_height, 21)
    b1.solid_ratio = 0.5
    assert _almost_same(b1.top_ref_height, 14)


@pytest.mark.parametrize("length_u,width_u", [(1, 1), (1, 2), (2, 2), (2, 3)])
def test_solid_box_1u_lid(length_u, width_u):
    """1U solid boxes are the community-standard Gridfinity lid.

    Regression: these crashed with Standard_Failure:
    BRepSweep_Translation::Constructor. At height_u=1, int_height is negative,
    so render_interior() falls back to a cavity profile of (height - GR_BOT_H)
    while the solid fill still referenced max_height -- which is 0 there. That
    passed 0 to extrude() and would have under-filled the box regardless.
    See GridfinityBox.cavity_height.
    """
    b = GridfinitySolidBox(length_u, width_u, 1)
    r = b.render()
    assert r.val().isValid()
    assert len(r.solids().vals()) == 1
    assert _almost_same(
        size_3d(r), (length_u * 42 - 0.5, width_u * 42 - 0.5, 11.4)
    )
    # Fully solid: the top reference is the full external height.
    assert _almost_same(b.top_ref_height, 11.4)


def test_fillet_radius_never_exceeds_the_cavity():
    """A 7.01mm bin has 0.01mm of interior; a 1.1mm fillet cannot fit in it.

    Unclamped, the kernel was asked for a radius 100x the available space and
    silently dropped the blend.
    """
    for h in (7.01, 8.0, 12.0, 25.4):
        b = GridfinityBox(2, 2, h, gridz_define=2)
        assert b.safe_fillet_rad <= b.cavity_height / 2 + 1e-9


def test_solid_box_zero_ratio_does_not_crash():
    """solid_ratio=0 means nothing to fill -- must not reach extrude(0)."""
    b = GridfinityBox(2, 2, 1, solid=True, solid_ratio=0.0)
    assert b.render().val().isValid()


# --- Height boundary family -------------------------------------------------
# Three separate zero-length extrudes lurked around the short-height edges, all
# surfacing as Standard_Failure: BRepSweep_Translation::Constructor.
#   height <= 5.00 (GR_BASE_HEIGHT + GR_BASE_CLR) -> shell wall extrude == 0
#   height <= 7.00 (GR_BOT_H)                     -> cavity profile == 0
#   height_u == 1 in unit mode                    -> max_height == 0 for the fill
# All three must now raise a clear ValueError or build cleanly -- never crash.


@pytest.mark.parametrize("height_mm", [3.0, 4.0, 5.0])
def test_height_below_base_profile_raises(height_mm):
    """A box shorter than its own Gridfinity feet is impossible, not a crash."""
    for kwargs in ({"solid": True}, {}):
        b = GridfinityBox(2, 2, height_mm, gridz_define=2, **kwargs)
        with pytest.raises(ValueError, match="base profile"):
            b.render()


@pytest.mark.parametrize("height_mm", [5.5, 6.0, 7.0])
def test_no_cavity_height_solid_ok_hollow_raises(height_mm):
    """Between the feet and GR_BOT_H there is no interior: lid yes, bin no."""
    lid = GridfinityBox(2, 2, height_mm, solid=True, gridz_define=2)
    r = lid.render()
    assert r.val().isValid()
    assert not lid.has_cavity
    assert _almost_same(r.val().BoundingBox().zlen, height_mm)

    hollow = GridfinityBox(2, 2, height_mm, gridz_define=2)
    with pytest.raises(ValueError, match="no interior cavity"):
        hollow.render()


def test_as_lid_default():
    """Default lid is GR_LID_TH above the feet -- 8.00mm total."""
    b = GridfinitySolidBox.as_lid(2, 3)
    r = b.render()
    assert r.val().isValid()
    assert _almost_same(b.lid_thickness, GR_LID_TH)
    assert _almost_same(r.val().BoundingBox().zlen, GR_BASE_HEIGHT + GR_LID_TH)
    assert b.filename() == "gf_lid_2x3_th3p25"


@pytest.mark.parametrize("thickness", [GR_LID_TH_MIN, 2.0, 5.0])
def test_as_lid_custom_thickness(thickness):
    """Any thickness at or above the floor builds; total is derived."""
    b = GridfinitySolidBox.as_lid(2, 2, thickness=thickness)
    r = b.render()
    assert r.val().isValid()
    assert _almost_same(b.lid_thickness, thickness)
    assert _almost_same(r.val().BoundingBox().zlen, GR_BASE_HEIGHT + thickness)


@pytest.mark.parametrize("thickness", [0.1, 0.5, GR_LID_TH_MIN - 0.01])
def test_as_lid_below_minimum_raises(thickness):
    """Below one wall thickness is a policy floor, not a crash guard."""
    with pytest.raises(ValueError, match="below the"):
        GridfinitySolidBox.as_lid(2, 2, thickness=thickness)


def test_solid_box_filename_unaffected_by_lid_support():
    """A plain solid box must still be named as a bin, not a lid."""
    assert GridfinitySolidBox(4, 2, 3).filename() == "gf_bin_4x2x3_solid"


@pytest.mark.parametrize("height_mm", [7.01, 8.0, 10.8])
def test_height_above_cavity_threshold_builds_both(height_mm):
    """Just above GR_BOT_H both a lid and a hollow bin are valid."""
    for kwargs in ({"solid": True}, {}):
        b = GridfinityBox(2, 2, height_mm, gridz_define=2, **kwargs)
        r = b.render()
        assert r.val().isValid()
        assert b.has_cavity
        assert _almost_same(r.val().BoundingBox().zlen, height_mm)


@pytest.mark.slow
@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_divided_box():
    b1 = GridfinityBox(3, 3, 3, holes=True, length_div=2, width_div=1)
    r = b1.render()
    assert r.val().isValid()
    if _export_files("box"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)
    assert _almost_same(size_3d(r), (125.5, 125.5, b1.actual_height))
    assert _faces_match(r, ">Z", 4)  # filleted lip tip, not a flat rim
    assert _faces_match(r, "<Z", 9)
    assert _edges_match(r, ">Z", 16)
    assert _edges_match(r, "<Z", 108)
    assert len(r.faces(FlatFaceSelector(21)).vals()) == 1
    bs = FlatEdgeSelector(21) - EdgeLengthSelector("<0.1")
    assert len(r.edges(bs).vals()) == 54
    assert b1.filename() == "gf_bin_3x3x3_mag_div2x1"


@pytest.mark.slow
@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_all_features_box():
    b1 = GridfinityBox(
        4, 2, 5, holes=True, length_div=2, width_div=1, scoops=True, labels=True
    )
    b1.label_height = 9
    b1.scoop_rad = 20
    r = b1.render()
    assert r.val().isValid()
    assert _almost_same(size_3d(r), (167.5, 83.5, b1.actual_height))
    s1 = str(b1)
    assert len(s1.splitlines()) == 9
    assert "167.50 x 83.50 x 38.55 mm" in s1  # actual, post lip-fillet
    assert "thickness: 1.00 mm" in s1
    assert "20.00 mm radius" in s1
    assert "label shelf 12.00 mm wide" in s1
    assert "25.20" in s1
    assert "54.37" in s1
    assert "40.15" in s1
    assert "gf_bin_4x2x5_mag_scoops_labels_div2x1" in s1
    if _export_files("box"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)
        b1.save_stl_file(path=EXPORT_STEP_FILE_PATH)
    assert _faces_match(r, ">Z", 4)  # filleted lip tip, not a flat rim
    assert _faces_match(r, "<Z", 8)
    assert _edges_match(r, ">Z", 16)
    assert _edges_match(r, "<Z", 96)
    assert len(r.faces(FlatFaceSelector(35)).vals()) == 1
    assert len(r.edges(FlatEdgeSelector(35)).vals()) == 51
    assert b1.filename() == "gf_bin_4x2x5_mag_scoops_labels_div2x1"
    b1 = GridfinityBox(
        2, 2, 3, holes=True, length_div=1, width_div=1, scoops=True, labels=True
    )
    r = b1.render()
    assert r.val().isValid()
    assert _almost_same(size_3d(r), (83.5, 83.5, b1.actual_height))
    if _export_files("box"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)
        b1 = GridfinityBox(
            2,
            2,
            3,
            holes=True,
            length_div=1,
            width_div=1,
            scoops=True,
            labels=True,
            wall_th=1.25,
        )
        r = b1.render()
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_reduced_lip_box():
    """Box with reduced lip style (underside chamfer only, no overhang)."""
    # Fillet tested in test_basic_box
    b1 = GridfinityBox(2, 2, 3, lip_style="reduced", fillet_interior=False)
    r = b1.render()
    assert r.val().isValid()
    # Same bounding box as normal lip — profile total height is identical
    b_normal = GridfinityBox(2, 2, 3, lip_style="normal", fillet_interior=False)
    r_normal = b_normal.render()
    assert r_normal.val().isValid()
    assert _almost_same(size_3d(r), size_3d(r_normal))
    assert b1.filename() == "gf_bin_2x2x3_reduced"
    assert "reduced top lip" in str(b1)
    if _export_files("box"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_no_lip_backward_compat():
    """no_lip=True should map to lip_style='none' for backward compatibility."""
    # Fillet tested in test_basic_box
    b1 = GridfinityBox(2, 2, 3, no_lip=True, fillet_interior=False)
    assert b1.lip_style == "none"
    assert b1.filename() == "gf_bin_2x2x3_nolip"
    r = b1.render()
    assert r.val().isValid()
    assert _almost_same(size_3d(r), (83.5, 83.5, b1.actual_height))


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_lip_style_none():
    """lip_style='none' should produce the same result as no_lip=True."""
    # Fillet tested in test_basic_box
    b_old = GridfinityBox(2, 2, 3, no_lip=True, fillet_interior=False)
    b_new = GridfinityBox(2, 2, 3, lip_style="none", fillet_interior=False)
    assert b_new.lip_style == "none"
    r_old = b_old.render()
    r_new = b_new.render()
    assert r_old.val().isValid()
    assert r_new.val().isValid()
    assert _almost_same(size_3d(r_old), size_3d(r_new))
    assert b_new.filename() == "gf_bin_2x2x3_nolip"


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_reduced_lip_with_scoops():
    """Reduced lip should work with scoops (underside chamfer still present)."""
    # Fillet tested in test_all_features_box
    b1 = GridfinityBox(2, 2, 3, lip_style="reduced", scoops=True,
                       fillet_interior=False)
    r = b1.render()
    assert r.val().isValid()
    assert _almost_same(size_3d(r), (83.5, 83.5, b1.actual_height))
    if _export_files("box"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_invalid_lip_style():
    """Invalid lip_style should raise ValueError."""
    with pytest.raises(ValueError):
        GridfinityBox(2, 2, 3, lip_style="invalid")


@pytest.mark.slow
@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_fillet_rad_default():
    """Default fillet_rad=None uses GR_FILLET (1.1mm), clamped to inner_rad."""
    b1 = GridfinityBox(1, 1, 3)
    assert b1.fillet_rad is None
    # safe_fillet_rad should return GR_FILLET clamped to inner_rad - 0.05
    assert b1.safe_fillet_rad <= b1.inner_rad - 0.05
    assert b1.safe_fillet_rad > 0
    r = b1.render()
    assert r.val().isValid()
    assert _almost_same(size_3d(r), (41.5, 41.5, b1.actual_height))


@pytest.mark.slow
@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_fillet_rad_custom():
    """Custom fillet_rad with thin walls should produce valid geometry."""
    # Thin wall: inner_rad = 3.75 - 0.8 = 2.95, so fillet_rad=2.5 fits
    b1 = GridfinityBox(1, 1, 3, wall_th=0.8, fillet_rad=2.5)
    assert b1.fillet_rad == 2.5
    assert _almost_same(b1.safe_fillet_rad, 2.5)
    r = b1.render()
    assert r.val().isValid()
    assert _almost_same(size_3d(r), (41.5, 41.5, b1.actual_height))
    # Larger fillet should be clamped if it exceeds inner_rad
    b2 = GridfinityBox(1, 1, 3, wall_th=1.0, fillet_rad=5.0)
    assert b2.safe_fillet_rad <= b2.inner_rad - 0.05
    r2 = b2.render()
    assert r2.val().isValid()
    assert _almost_same(size_3d(r2), (41.5, 41.5, b2.actual_height))
