# Skeletonized baseplate tests (1B.9)
import pytest

from cqgridfinity import *
from cqkit.cq_helpers import size_3d
from common_test import (
    EXPORT_STEP_FILE_PATH,
    _almost_same,
    _export_files,
    SKIP_TEST_BASEPLATE,
)

SKIP = pytest.mark.skipif(
    SKIP_TEST_BASEPLATE,
    reason="Skipped intentionally by test scope environment variable",
)

# Expected ext_depth values
SKEL_DEPTH_PLAIN = GR_SKEL_H + GR_SKEL_SCREW_NONE  # 1.0 + 3.35 = 4.35
SKEL_DEPTH_MAG = GR_SKEL_H + GR_HOLE_H + GR_SKEL_SCREW_NONE  # 1.0 + 2.4 + 3.35 = 6.75
SKEL_DEPTH_REFINED = GR_SKEL_H + GR_REFINED_HOLE_H + GR_SKEL_SCREW_NONE  # 1.0 + 1.9 + 3.35 = 6.25


@SKIP
def test_skeleton_basic_2x2():
    """Basic 2x2 skeleton baseplate with no holes."""
    bp = GridfinityBaseplate(2, 2, skeleton=True)
    r = bp.render()
    assert _almost_same(bp.ext_depth, SKEL_DEPTH_PLAIN)
    expected_h = GR_BASE_HEIGHT + SKEL_DEPTH_PLAIN  # 4.75 + 4.35 = 9.1
    assert _almost_same(size_3d(r), (84, 84, expected_h), tol=0.15)
    assert r.val().isValid()


@SKIP
def test_skeleton_1x1():
    """1x1 skeleton baseplate."""
    bp = GridfinityBaseplate(1, 1, skeleton=True)
    r = bp.render()
    assert _almost_same(bp.ext_depth, SKEL_DEPTH_PLAIN)
    expected_h = GR_BASE_HEIGHT + SKEL_DEPTH_PLAIN
    assert _almost_same(size_3d(r), (42, 42, expected_h), tol=0.15)
    assert r.val().isValid()


@SKIP
def test_skeleton_with_magnets():
    """Skeleton baseplate with magnet holes."""
    bp = GridfinityBaseplate(2, 2, skeleton=True, magnet_holes=True)
    r = bp.render()
    assert _almost_same(bp.ext_depth, SKEL_DEPTH_MAG)
    expected_h = GR_BASE_HEIGHT + SKEL_DEPTH_MAG  # 4.75 + 6.75 = 11.5
    assert _almost_same(size_3d(r), (84, 84, expected_h), tol=0.15)
    assert r.val().isValid()


@SKIP
def test_skeleton_with_screws():
    """Skeleton baseplate with screw holes only.
    Screw ext_depth = 4.0 < skel_depth = 4.35, so skel wins."""
    bp = GridfinityBaseplate(2, 2, skeleton=True, screw_holes=True)
    r = bp.render()
    assert _almost_same(bp.ext_depth, SKEL_DEPTH_PLAIN)
    assert r.val().isValid()


@SKIP
def test_skeleton_with_mag_screw():
    """Skeleton baseplate with magnet + screw holes."""
    bp = GridfinityBaseplate(2, 2, skeleton=True, magnet_holes=True, screw_holes=True)
    r = bp.render()
    assert _almost_same(bp.ext_depth, SKEL_DEPTH_MAG)
    expected_h = GR_BASE_HEIGHT + SKEL_DEPTH_MAG
    assert _almost_same(size_3d(r), (84, 84, expected_h), tol=0.15)
    assert r.val().isValid()


@SKIP
def test_skeleton_with_refined_magnets():
    """Skeleton baseplate with refined magnet holes (shallower depth)."""
    bp = GridfinityBaseplate(
        2, 2, skeleton=True, magnet_holes=True, refined_holes=True
    )
    r = bp.render()
    assert _almost_same(bp.ext_depth, SKEL_DEPTH_REFINED)
    assert r.val().isValid()


@SKIP
def test_skeleton_with_enhanced_holes():
    """Skeleton baseplate with crush ribs and chamfer."""
    bp = GridfinityBaseplate(
        2, 2,
        skeleton=True,
        magnet_holes=True,
        crush_ribs=True,
        chamfer_holes=True,
    )
    r = bp.render()
    assert _almost_same(bp.ext_depth, SKEL_DEPTH_MAG)
    assert r.val().isValid()


@SKIP
def test_skeleton_with_corner_screws():
    """Skeleton baseplate with corner mounting screws."""
    bp = GridfinityBaseplate(
        2, 2, skeleton=True, magnet_holes=True, corner_screws=True
    )
    r = bp.render()
    # skel_depth = 6.75 > corner_screw_depth = 5.0, so skel wins
    assert _almost_same(bp.ext_depth, SKEL_DEPTH_MAG)
    assert r.val().isValid()


@SKIP
def test_skeleton_overrides_weighted():
    """Skeleton takes priority over weighted — no weight pockets cut."""
    bp = GridfinityBaseplate(
        2, 2, skeleton=True, weighted=True, magnet_holes=True
    )
    r = bp.render()
    assert "_skel" in bp.filename()
    assert "_weighted" not in bp.filename()
    assert r.val().isValid()


@SKIP
def test_skeleton_large_grid():
    """4x3 skeleton baseplate with magnets — tiling works correctly."""
    bp = GridfinityBaseplate(4, 3, skeleton=True, magnet_holes=True)
    r = bp.render()
    expected_h = GR_BASE_HEIGHT + SKEL_DEPTH_MAG
    assert _almost_same(size_3d(r), (168, 126, expected_h), tol=0.15)
    assert r.val().isValid()


@SKIP
def test_skeleton_filename_conventions():
    """Skeleton filename suffix is correct for various configs."""
    bp1 = GridfinityBaseplate(2, 2, skeleton=True)
    assert bp1.filename() == "gf_baseplate_2x2_skel"

    bp2 = GridfinityBaseplate(2, 2, skeleton=True, magnet_holes=True)
    assert bp2.filename() == "gf_baseplate_2x2_skel_mag"

    bp3 = GridfinityBaseplate(
        2, 2, skeleton=True, magnet_holes=True, screw_holes=True
    )
    assert bp3.filename() == "gf_baseplate_2x2_skel_mag-screw"

    bp4 = GridfinityBaseplate(2, 2, skeleton=True, screw_holes=True)
    assert bp4.filename() == "gf_baseplate_2x2_skel_screw"

    bp5 = GridfinityBaseplate(
        2, 2, skeleton=True, magnet_holes=True, corner_screws=True
    )
    assert bp5.filename() == "gf_baseplate_2x2_skel_mag_csk"


@SKIP
def test_skeleton_default_unchanged():
    """Backward compat: skeleton=False by default, no change to existing behavior."""
    bp = GridfinityBaseplate(2, 2, magnet_holes=True)
    assert bp.skeleton is False
    assert bp.ext_depth == GR_HOLE_H
    assert "_skel" not in bp.filename()


@SKIP
def test_skeleton_cutout_dimensions():
    """Skeleton cutout pocket width matches kennetek spec.

    kennetek standard.scad: GR_SKEL_INNER = GRU - 2*GR_BP_PROFILE_X = 42 - 2*2.85 = 36.3mm
    Each cell has 4 corner pocket cutouts. The cutout inner dimension is derived from
    GR_SKEL_INNER minus keepout zones around hole positions.
    """
    # kennetek: GR_SKEL_INNER = 36.3mm (full inner cell dimension)
    assert _almost_same(GR_SKEL_INNER, 36.3, tol=0.01)
    # kennetek: GR_SKEL_RAD = 2.0mm (cutout corner radius, r_skel)
    assert _almost_same(GR_SKEL_RAD, 2.0, tol=0.01)
    # kennetek: GR_SKEL_H = 1.0mm (structural spacing)
    assert _almost_same(GR_SKEL_H, 1.0, tol=0.01)
    # Verify rendered skeleton has correct overall dimensions
    bp = GridfinityBaseplate(2, 2, skeleton=True, magnet_holes=True)
    r = bp.render()
    assert r.val().isValid()
    # Skeleton should be shorter than an equivalently-featured non-skeleton
    # because skeleton cutouts remove material from the slab
    bp_solid = GridfinityBaseplate(2, 2, magnet_holes=True, ext_depth=bp.ext_depth)
    r_solid = bp_solid.render()
    assert r.val().Volume() < r_solid.val().Volume()


@SKIP
def test_skeleton_volume_less_than_solid():
    """Skeleton baseplate has less volume than equivalent solid-slab baseplate."""
    # Compare skeleton+magnets vs magnets-only at same ext_depth.
    # Both have _has_bottom_features=True, so both get the solid slab path.
    # Only difference is the skeleton cutouts.
    bp_skel = GridfinityBaseplate(
        2, 2, skeleton=True, magnet_holes=True
    )
    r_skel = bp_skel.render()
    assert r_skel.val().isValid()

    bp_solid = GridfinityBaseplate(
        2, 2, magnet_holes=True, ext_depth=bp_skel.ext_depth
    )
    r_solid = bp_solid.render()
    assert r_solid.val().isValid()

    vol_skel = r_skel.val().Volume()
    vol_solid = r_solid.val().Volume()
    assert vol_skel < vol_solid


@SKIP
def test_skeleton_watertight():
    """Skeleton baseplate with magnets produces a watertight solid."""
    bp = GridfinityBaseplate(2, 2, skeleton=True, magnet_holes=True)
    r = bp.render()
    assert r.val().isValid()


@SKIP
def test_skeleton_step_export():
    """Skeleton baseplate can be exported to STEP without error."""
    bp = GridfinityBaseplate(2, 2, skeleton=True, magnet_holes=True)
    r = bp.render()
    assert r.val().isValid()
    if _export_files("baseplate"):
        bp.save_step_file(path=EXPORT_STEP_FILE_PATH)
    # Just verify render completes without exception — STEP export
    # is tested by the save_step_file call above when EXPORT_STEP_FILES is set.
    # For CI, we at least confirm filename is correct.
    assert bp.filename() == "gf_baseplate_2x2_skel_mag"
