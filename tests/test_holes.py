# Tests for enhanced hole types (1B.1-1B.4)
import pytest
import math

from cqgridfinity import *
from cqgridfinity.gf_holes import (
    magnet_hole,
    refined_magnet_hole,
    crush_rib_magnet_hole,
    enhanced_magnet_hole,
    _chamfer_cone,
    _printable_bridge,
)
from cqkit.cq_helpers import size_3d
from common_test import (
    _almost_same,
    _export_files,
    EXPORT_STEP_FILE_PATH,
    SKIP_TEST_BASEPLATE,
    SKIP_TEST_BOX,
)


# ---------------------------------------------------------------------------
# Individual hole geometry tests
# ---------------------------------------------------------------------------


def test_standard_magnet_hole():
    """Standard magnet hole: 6.5mm dia, 2.4mm deep."""
    h = magnet_hole()
    bb = h.val().BoundingBox()
    assert _almost_same(bb.xlen, GR_HOLE_D, tol=0.1)
    assert _almost_same(bb.ylen, GR_HOLE_D, tol=0.1)
    assert bb.zlen >= GR_HOLE_H


def test_refined_magnet_hole():
    """1B.3: Refined hole — 5.86mm dia, 1.9mm deep."""
    h = refined_magnet_hole()
    bb = h.val().BoundingBox()
    assert _almost_same(bb.xlen, GR_REFINED_HOLE_D, tol=0.1)
    assert _almost_same(bb.ylen, GR_REFINED_HOLE_D, tol=0.1)
    assert bb.zlen >= GR_REFINED_HOLE_H
    assert bb.zlen < GR_HOLE_H + 0.1  # shallower than standard


def test_crush_rib_magnet_hole():
    """1B.1: Crush rib hole — 8 ribs, inner dia 5.9mm."""
    h = crush_rib_magnet_hole()
    bb = h.val().BoundingBox()
    # kennetek: outer diameter = GR_HOLE_D = 6.5mm (gridfinity-rebuilt-holes.scad)
    assert _almost_same(bb.xlen, GR_HOLE_D, tol=0.1)
    assert _almost_same(bb.ylen, GR_HOLE_D, tol=0.1)
    assert bb.zlen >= GR_HOLE_H
    # The cutting tool should have less volume than a plain cylinder
    # (rib material is removed from the cutting tool)
    plain = magnet_hole()
    ribbed = crush_rib_magnet_hole()
    plain_vol = plain.val().Volume()
    ribbed_vol = ribbed.val().Volume()
    assert ribbed_vol < plain_vol
    # kennetek: GR_CRUSH_RIB_COUNT=8 ribs (ribbed_cylinder, gridfinity-rebuilt-holes.scad)
    # Volume removed per rib ~ pi*r_outer^2*h - pi*r_inner^2*h spread across rib_count ribs.
    # Verify that the volume difference is proportional to rib count.
    h4 = crush_rib_magnet_hole(rib_count=4)
    h8 = crush_rib_magnet_hole(rib_count=8)
    h16 = crush_rib_magnet_hole(rib_count=16)
    vol4 = h4.val().Volume()
    vol8 = h8.val().Volume()
    vol16 = h16.val().Volume()
    # More ribs → more material retained → less cutting volume
    assert vol4 > vol8 > vol16
    # Default rib count must be 8 (from spec constant)
    # kennetek: GR_CRUSH_RIB_COUNT=8 (gridfinity-rebuilt-holes.scad)
    assert GR_CRUSH_RIB_COUNT == 8
    # kennetek: GR_CRUSH_RIB_INNER_D=5.9mm (ribbed_cylinder inner)
    assert _almost_same(GR_CRUSH_RIB_INNER_D, 5.9, tol=0.01)


def test_crush_rib_hole_rib_count():
    """Crush ribs: verify different rib counts produce different geometry."""
    h4 = crush_rib_magnet_hole(rib_count=4)
    h8 = crush_rib_magnet_hole(rib_count=8)
    # Different rib counts should produce different volumes
    assert abs(h4.val().Volume() - h8.val().Volume()) > 0.01


def test_chamfer_cone():
    """1B.2: Chamfer cone — 0.8mm extra radius at 45 degrees."""
    r = GR_HOLE_D / 2
    cone = _chamfer_cone(r)
    bb = cone.val().BoundingBox()
    expected_diam = GR_HOLE_D + 2 * GR_CHAMFER_EXTRA_R
    assert _almost_same(bb.xlen, expected_diam, tol=0.1)
    assert _almost_same(bb.ylen, expected_diam, tol=0.1)
    chamfer_h = GR_CHAMFER_EXTRA_R / math.tan(math.radians(GR_CHAMFER_ANGLE))
    assert _almost_same(bb.zlen, chamfer_h, tol=0.1)


def test_printable_bridge():
    """1B.4: Printable bridge — thin disc for FDM bridging."""
    r = GR_HOLE_D / 2
    bridge = _printable_bridge(r, 0.4)
    bb = bridge.val().BoundingBox()
    assert _almost_same(bb.xlen, GR_HOLE_D, tol=0.1)
    assert _almost_same(bb.zlen, 0.4, tol=0.05)


# ---------------------------------------------------------------------------
# Combined enhanced_magnet_hole tests
# ---------------------------------------------------------------------------


def test_enhanced_hole_refined():
    """Enhanced hole with refined=True uses smaller dimensions."""
    h = enhanced_magnet_hole(refined=True)
    bb = h.val().BoundingBox()
    assert _almost_same(bb.xlen, GR_REFINED_HOLE_D, tol=0.1)
    assert bb.zlen >= GR_REFINED_HOLE_H


def test_enhanced_hole_crush_ribs():
    """Enhanced hole with crush_ribs=True has less volume than plain."""
    plain = enhanced_magnet_hole()
    ribbed = enhanced_magnet_hole(crush_ribs=True)
    assert ribbed.val().Volume() < plain.val().Volume()


def test_enhanced_hole_chamfer():
    """Enhanced hole with chamfer=True extends above base depth."""
    plain = enhanced_magnet_hole()
    chamfered = enhanced_magnet_hole(chamfer=True)
    plain_bb = plain.val().BoundingBox()
    chamfered_bb = chamfered.val().BoundingBox()
    # Chamfered hole should be taller (chamfer cone adds height)
    assert chamfered_bb.zlen > plain_bb.zlen


def test_enhanced_hole_printable_top():
    """Enhanced hole with printable_top=True has less volume than plain."""
    plain = enhanced_magnet_hole()
    printable = enhanced_magnet_hole(printable_top=True)
    # Printable top removes a disc from the cutting tool = less volume
    assert printable.val().Volume() < plain.val().Volume()


def test_enhanced_hole_all_options():
    """Enhanced hole with all options enabled produces valid geometry."""
    h = enhanced_magnet_hole(
        refined=True, crush_ribs=True, chamfer=True, printable_top=True
    )
    bb = h.val().BoundingBox()
    # Should be valid solid with refined diameter
    assert _almost_same(bb.xlen, GR_REFINED_HOLE_D + 2 * GR_CHAMFER_EXTRA_R, tol=0.2)
    assert bb.zlen > 0


# ---------------------------------------------------------------------------
# Baseplate integration tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    SKIP_TEST_BASEPLATE,
    reason="Skipped intentionally by test scope environment variable",
)
def test_baseplate_crush_rib_holes():
    """1B.1: Baseplate with crush rib magnet holes."""
    bp = GridfinityBaseplate(2, 2, magnet_holes=True, crush_ribs=True)
    r = bp.render()
    assert r.val().isValid()
    expected_h = GR_BASE_HEIGHT + GR_HOLE_H
    assert _almost_same(size_3d(r), (84, 84, expected_h), tol=0.2)
    if _export_files("holes"):
        bp.save_step_file(filename="./tests/testfiles/gf_baseplate_2x2_crush_rib.step")


@pytest.mark.skipif(
    SKIP_TEST_BASEPLATE,
    reason="Skipped intentionally by test scope environment variable",
)
def test_baseplate_chamfered_holes():
    """1B.2: Baseplate with chamfered magnet holes."""
    bp = GridfinityBaseplate(2, 2, magnet_holes=True, chamfer_holes=True)
    r = bp.render()
    assert r.val().isValid()
    expected_h = GR_BASE_HEIGHT + GR_HOLE_H
    assert _almost_same(size_3d(r), (84, 84, expected_h), tol=0.2)
    if _export_files("holes"):
        bp.save_step_file(filename="./tests/testfiles/gf_baseplate_2x2_chamfered.step")


@pytest.mark.skipif(
    SKIP_TEST_BASEPLATE,
    reason="Skipped intentionally by test scope environment variable",
)
def test_baseplate_refined_holes():
    """1B.3: Baseplate with refined magnet holes."""
    bp = GridfinityBaseplate(2, 2, magnet_holes=True, refined_holes=True)
    r = bp.render()
    assert r.val().isValid()
    # Refined holes are shallower (1.9mm), so ext_depth auto-adjusts to GR_HOLE_H
    # (because auto-adjust uses the standard depth — refined is opt-in geometry only)
    expected_h = GR_BASE_HEIGHT + GR_HOLE_H
    assert _almost_same(size_3d(r), (84, 84, expected_h), tol=0.2)
    if _export_files("holes"):
        bp.save_step_file(filename="./tests/testfiles/gf_baseplate_2x2_refined.step")


@pytest.mark.skipif(
    SKIP_TEST_BASEPLATE,
    reason="Skipped intentionally by test scope environment variable",
)
def test_baseplate_printable_holes():
    """1B.4: Baseplate with printable hole tops."""
    bp = GridfinityBaseplate(2, 2, magnet_holes=True, printable_hole_top=True)
    r = bp.render()
    assert r.val().isValid()
    expected_h = GR_BASE_HEIGHT + GR_HOLE_H
    assert _almost_same(size_3d(r), (84, 84, expected_h), tol=0.2)
    if _export_files("holes"):
        bp.save_step_file(filename="./tests/testfiles/gf_baseplate_2x2_printable.step")


@pytest.mark.skipif(
    SKIP_TEST_BASEPLATE,
    reason="Skipped intentionally by test scope environment variable",
)
def test_baseplate_all_enhanced_holes():
    """All enhanced hole options combined on a baseplate."""
    bp = GridfinityBaseplate(
        2, 2,
        magnet_holes=True,
        screw_holes=True,
        crush_ribs=True,
        chamfer_holes=True,
        printable_hole_top=True,
    )
    r = bp.render()
    # Should render without errors
    assert r is not None
    assert r.val().isValid()
    bb = r.val().BoundingBox()
    assert bb.xlen > 0
    if _export_files("holes"):
        bp.save_step_file(
            filename="./tests/testfiles/gf_baseplate_2x2_all_enhanced.step"
        )


@pytest.mark.skipif(
    SKIP_TEST_BASEPLATE,
    reason="Skipped intentionally by test scope environment variable",
)
def test_baseplate_enhanced_filename():
    """Enhanced hole options reflected in filename."""
    bp = GridfinityBaseplate(
        4, 3, magnet_holes=True, crush_ribs=True, chamfer_holes=True
    )
    fn = bp.filename()
    assert "rib" in fn
    assert "chm" in fn


@pytest.mark.skipif(
    SKIP_TEST_BASEPLATE,
    reason="Skipped intentionally by test scope environment variable",
)
def test_baseplate_backward_compat():
    """Existing magnet_holes=True without enhanced options stays the same."""
    bp = GridfinityBaseplate(2, 2, magnet_holes=True)
    r = bp.render()
    assert r.val().isValid()
    # No enhanced options = same as before
    assert not bp._has_enhanced_holes
    assert bp.ext_depth == GR_HOLE_H
    expected_h = GR_BASE_HEIGHT + GR_HOLE_H
    assert _almost_same(size_3d(r), (84, 84, expected_h), tol=0.1)


# ---------------------------------------------------------------------------
# Bin integration tests — enhanced holes on GridfinityBox
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_bin_crush_rib_holes():
    """1B.1 on bins: crush ribs leave more material than plain enhanced holes.

    Note: enhanced holes use boolean cutting (different from standard .cboreHole()),
    so comparisons must use the same code path. We use printable_hole_top as a
    minimal enhanced baseline to ensure both variants use the boolean path.
    """
    # Both use boolean cut path (printable_hole_top triggers enhanced)
    base = GridfinityBox(2, 2, 3, holes=True, printable_hole_top=True)
    ribbed = GridfinityBox(2, 2, 3, holes=True, printable_hole_top=True, crush_ribs=True)
    rb = base.render()
    rr = ribbed.render()
    assert rb.val().isValid()
    assert rr.val().isValid()
    # kennetek: GR_CRUSH_RIB_COUNT=8, ribs leave material inside hole
    # → ribbed bin has MORE volume (ribs reduce the cutting tool volume)
    assert rr.val().Volume() > rb.val().Volume()


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_bin_chamfered_holes():
    """1B.2 on bins: chamfered holes remove more material than plain enhanced."""
    # Both use boolean cut path
    base = GridfinityBox(2, 2, 3, holes=True, printable_hole_top=True)
    chamfered = GridfinityBox(2, 2, 3, holes=True, printable_hole_top=True, chamfer_holes=True)
    rb = base.render()
    rc = chamfered.render()
    assert rb.val().isValid()
    assert rc.val().isValid()
    # kennetek: GR_CHAMFER_EXTRA_R=0.8mm, 45° cone at hole entry
    # → chamfered bin has LESS volume (chamfer cone removes additional material)
    assert rc.val().Volume() < rb.val().Volume()


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_bin_refined_holes():
    """1B.3 on bins: refined holes use smaller diameter (5.86mm vs 6.5mm)."""
    # Both use boolean cut path
    base = GridfinityBox(2, 2, 3, holes=True, printable_hole_top=True)
    refined = GridfinityBox(2, 2, 3, holes=True, printable_hole_top=True, refined_holes=True)
    rb = base.render()
    rr = refined.render()
    assert rb.val().isValid()
    assert rr.val().isValid()
    # kennetek: GR_REFINED_HOLE_D=5.86mm (vs 6.5mm), GR_REFINED_HOLE_H=1.9mm (vs 2.4mm)
    # → refined bin has MORE volume (smaller, shallower holes)
    assert rr.val().Volume() > rb.val().Volume()


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_bin_printable_hole_top():
    """1B.4 on bins: printable bridge produces valid geometry."""
    bridge = GridfinityBox(2, 2, 3, holes=True, printable_hole_top=True)
    rb = bridge.render()
    assert rb is not None
    assert rb.val().isValid()
    bb = rb.val().BoundingBox()
    assert bb.xlen > 0


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_bin_all_enhanced_holes():
    """All enhanced hole options combined on a bin."""
    b = GridfinityBox(
        2, 2, 3,
        holes=True,
        crush_ribs=True,
        chamfer_holes=True,
        printable_hole_top=True,
    )
    r = b.render()
    assert r is not None
    assert r.val().isValid()
    bb = r.val().BoundingBox()
    assert bb.xlen > 0


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_bin_enhanced_holes_filename():
    """Enhanced hole options reflected in bin filename."""
    b = GridfinityBox(
        3, 2, 5, holes=True, crush_ribs=True, chamfer_holes=True, refined_holes=True
    )
    fn = b.filename()
    assert "_mag" in fn
    assert "-ribs" in fn
    assert "-chamfer" in fn
    assert "-refined" in fn


@pytest.mark.skipif(
    SKIP_TEST_BOX, reason="Skipped intentionally by test scope environment variable"
)
def test_bin_standard_holes_unchanged():
    """Standard holes (no enhanced options) match golden volume baseline."""
    b = GridfinityBox(2, 2, 3, holes=True)
    r = b.render()
    assert r.val().isValid()
    # Golden baseline captured pre-refactor: 49186.950685 mm³
    assert _almost_same(r.val().Volume(), 49186.950685, tol=1.0)
