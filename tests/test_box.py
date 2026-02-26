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


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_basic_box():
    b1 = GridfinityBox(2, 3, 5, no_lip=True)
    r = b1.render()
    assert _almost_same(size_3d(r), (83.5, 125.5, 38.8))
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


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_lite_box():
    b1 = GridfinityBox(2, 3, 5, lite_style=True)
    r = b1.render()
    if _export_files("box"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)
    assert _almost_same(size_3d(r), (83.5, 125.5, 38.8))
    assert _faces_match(r, ">Z", 1)
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
    if _export_files("box"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)
    assert _almost_same(size_3d(r), (41.5, 41.5, 10.8))

    b1 = GridfinityBox(1, 1, 2, lite_style=True)
    r = b1.render()
    if _export_files("box"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)
    assert _almost_same(size_3d(r), (41.5, 41.5, 17.8))


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_empty_box():
    b1 = GridfinityBox(2, 3, 5, holes=True)
    r = b1.render()
    if _export_files("box"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)
    assert _almost_same(size_3d(r), (83.5, 125.5, 38.8))
    assert _faces_match(r, ">Z", 1)
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
    if _export_files("box"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)
    assert _almost_same(size_3d(r), (41.5, 41.5, 10.8))

    b1 = GridfinityBox(1, 1, 2)
    r = b1.render()
    if _export_files("box"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)
    assert _almost_same(size_3d(r), (41.5, 41.5, 17.8))


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_solid_box():
    b1 = GridfinitySolidBox(4, 2, 3)
    r = b1.render()
    if _export_files("box"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)
    assert _almost_same(size_3d(r), (167.5, 83.5, 24.8))
    assert _faces_match(r, ">Z", 1)
    assert _faces_match(r, "<Z", 8)
    assert _edges_match(r, ">Z", 16)
    assert _edges_match(r, "<Z", 64)
    assert len(r.faces(FlatFaceSelector(21)).vals()) == 1
    assert len(r.edges(FlatEdgeSelector(21)).vals()) == 8
    assert b1.filename() == "gf_bin_4x2x3_solid"
    assert _almost_same(b1.top_ref_height, 21)
    b1.solid_ratio = 0.5
    assert _almost_same(b1.top_ref_height, 14)


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_divided_box():
    b1 = GridfinityBox(3, 3, 3, holes=True, length_div=2, width_div=1)
    r = b1.render()
    if _export_files("box"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)
    assert _almost_same(size_3d(r), (125.5, 125.5, 24.8))
    assert _faces_match(r, ">Z", 1)
    assert _faces_match(r, "<Z", 9)
    assert _edges_match(r, ">Z", 16)
    assert _edges_match(r, "<Z", 108)
    assert len(r.faces(FlatFaceSelector(21)).vals()) == 1
    bs = FlatEdgeSelector(21) - EdgeLengthSelector("<0.1")
    assert len(r.edges(bs).vals()) == 54
    assert b1.filename() == "gf_bin_3x3x3_mag_div2x1"


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
    assert _almost_same(size_3d(r), (167.5, 83.5, 38.8))
    s1 = str(b1)
    assert len(s1.splitlines()) == 9
    assert "167.50 x 83.50 x 38.80 mm" in s1
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
    assert _faces_match(r, ">Z", 1)
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
    assert _almost_same(size_3d(r), (83.5, 83.5, 24.8))
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
    b1 = GridfinityBox(2, 2, 3, lip_style="reduced")
    r = b1.render()
    # Same bounding box as normal lip — profile total height is identical
    b_normal = GridfinityBox(2, 2, 3, lip_style="normal")
    r_normal = b_normal.render()
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
    b1 = GridfinityBox(2, 2, 3, no_lip=True)
    assert b1.lip_style == "none"
    assert b1.filename() == "gf_bin_2x2x3_nolip"
    r = b1.render()
    assert _almost_same(size_3d(r), (83.5, 83.5, 24.8))


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_lip_style_none():
    """lip_style='none' should produce the same result as no_lip=True."""
    b_old = GridfinityBox(2, 2, 3, no_lip=True)
    b_new = GridfinityBox(2, 2, 3, lip_style="none")
    assert b_new.lip_style == "none"
    r_old = b_old.render()
    r_new = b_new.render()
    assert _almost_same(size_3d(r_old), size_3d(r_new))
    assert b_new.filename() == "gf_bin_2x2x3_nolip"


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_reduced_lip_with_scoops():
    """Reduced lip should work with scoops (underside chamfer still present)."""
    b1 = GridfinityBox(2, 2, 3, lip_style="reduced", scoops=True)
    r = b1.render()
    assert _almost_same(size_3d(r), (83.5, 83.5, 24.8))
    if _export_files("box"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_invalid_lip_style():
    """Invalid lip_style should raise ValueError."""
    with pytest.raises(ValueError):
        GridfinityBox(2, 2, 3, lip_style="invalid")


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_wall_pattern_hexgrid():
    """Box with hex grid wall pattern."""
    b1 = GridfinityBox(3, 2, 5, wall_pattern=True)
    r = b1.render()
    assert _almost_same(size_3d(r), (125.5, 83.5, 38.8))
    assert b1.filename() == "gf_bin_3x2x5_hex"
    # Pattern should reduce volume compared to plain box
    b_plain = GridfinityBox(3, 2, 5)
    r_plain = b_plain.render()
    assert r.val().Volume() < r_plain.val().Volume()
    if _export_files("box"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_wall_pattern_grid():
    """Box with square grid wall pattern."""
    b1 = GridfinityBox(2, 2, 5, wall_pattern=True, wall_pattern_style="grid",
                       wall_pattern_sides=4)
    r = b1.render()
    assert _almost_same(size_3d(r), (83.5, 83.5, 38.8))
    assert b1.filename() == "gf_bin_2x2x5_grid"
    if _export_files("box"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_wall_pattern_selective_walls():
    """Wall pattern applied only to front and back walls."""
    b1 = GridfinityBox(3, 2, 5, wall_pattern=True,
                       wall_pattern_walls=(True, True, False, False))
    r = b1.render()
    # Should still render without error
    assert _almost_same(size_3d(r), (125.5, 83.5, 38.8))
    if _export_files("box"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_wall_pattern_small_box_skipped():
    """Pattern should be skipped gracefully on too-small boxes."""
    b1 = GridfinityBox(1, 1, 1, wall_pattern=True, wall_pattern_cell=50)
    r = b1.render()
    # Should render without error, pattern just won't fit
    assert _almost_same(size_3d(r), (41.5, 41.5, 10.8))


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_vase_mode_box():
    """Vase mode produces a thin-walled, open-top bin."""
    b1 = GridfinityBox(2, 2, 5, vase_mode=True)
    r = b1.render()
    assert _almost_same(size_3d(r), (83.5, 83.5, 38.8))
    assert b1.filename() == "gf_bin_2x2x5_vase"
    # Vase mode forces no-lip and no features
    assert b1.lip_style == "none"
    assert b1.scoops is False
    assert b1.labels is False
    assert b1.holes is False
    # Vase mode should have less volume than regular (thinner walls)
    b_reg = GridfinityBox(2, 2, 5)
    r_reg = b_reg.render()
    assert r.val().Volume() < r_reg.val().Volume()
    if _export_files("box"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_vase_mode_single_unit():
    """Vase mode works for 1x1 boxes."""
    b1 = GridfinityBox(1, 1, 3, vase_mode=True)
    r = b1.render()
    assert _almost_same(size_3d(r), (41.5, 41.5, 24.8))
    assert b1.filename() == "gf_bin_1x1x3_vase"


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_thumbscrew_box():
    """Box with thumbscrew hole in front wall."""
    b1 = GridfinityBox(2, 2, 5, thumbscrew=True)
    r = b1.render()
    assert _almost_same(size_3d(r), (83.5, 83.5, 38.8))
    assert b1.filename() == "gf_bin_2x2x5_thumb"
    # Thumbscrew hole should reduce volume
    b_plain = GridfinityBox(2, 2, 5)
    r_plain = b_plain.render()
    assert r.val().Volume() < r_plain.val().Volume()
    if _export_files("box"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_thumbscrew_multi_unit():
    """Multi-unit box should have one thumbscrew per grid unit."""
    b1 = GridfinityBox(3, 2, 5, thumbscrew=True)
    r = b1.render()
    assert _almost_same(size_3d(r), (125.5, 83.5, 38.8))
    assert b1.filename() == "gf_bin_3x2x5_thumb"
    if _export_files("box"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)


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
    assert _almost_same(size_3d(r), (41.5, 41.5, 24.8))


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
    assert _almost_same(size_3d(r), (41.5, 41.5, 24.8))
    # Larger fillet should be clamped if it exceeds inner_rad
    b2 = GridfinityBox(1, 1, 3, wall_th=1.0, fillet_rad=5.0)
    assert b2.safe_fillet_rad <= b2.inner_rad - 0.05
    r2 = b2.render()
    assert _almost_same(size_3d(r2), (41.5, 41.5, 24.8))
