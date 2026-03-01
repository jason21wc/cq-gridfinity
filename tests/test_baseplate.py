# Gridfinity tests
import pytest

# my modules
from cqgridfinity import *
from cqgridfinity.constants import (
    GR_BASE_HEIGHT,
    GR_HOLE_H,
    GR_ST_ADDITIONAL_H,
)
from cqkit import FlatEdgeSelector
from cqkit.cq_helpers import size_3d
from common_test import (
    EXPORT_STEP_FILE_PATH,
    _almost_same,
    _faces_match,
    _export_files,
    SKIP_TEST_BASEPLATE,
)


@pytest.mark.skipif(
    SKIP_TEST_BASEPLATE,
    reason="Skipped intentionally by test scope environment variable",
)
def test_make_baseplate():
    bp = GridfinityBaseplate(4, 3)
    r = bp.render()
    assert r.val().isValid()
    if _export_files("baseplate"):
        bp.save_step_file(path=EXPORT_STEP_FILE_PATH)
    assert bp.filename() == "gf_baseplate_4x3"
    assert _almost_same(size_3d(r), (168, 126, 4.75))
    assert _faces_match(r, ">Z", 16)
    assert _faces_match(r, "<Z", 1)
    edge_diff = abs(len(r.edges(FlatEdgeSelector(0)).vals()) - 104)
    assert edge_diff < 3


@pytest.mark.skipif(
    SKIP_TEST_BASEPLATE,
    reason="Skipped intentionally by test scope environment variable",
)
def test_make_ext_baseplate():
    bp = GridfinityBaseplate(5, 4, ext_depth=5, corner_screws=True)
    r = bp.render()
    assert r.val().isValid()
    assert _almost_same(size_3d(r), (210, 168, 9.75))
    edge_diff = abs(len(r.edges(FlatEdgeSelector(0)).vals()) - 188)
    assert edge_diff < 3


@pytest.mark.skipif(
    SKIP_TEST_BASEPLATE,
    reason="Skipped intentionally by test scope environment variable",
)
def test_magnet_baseplate():
    """Baseplate with magnet holes only."""
    bp = GridfinityBaseplate(2, 2, magnet_holes=True)
    r = bp.render()
    assert r.val().isValid()
    # ext_depth should auto-adjust to GR_HOLE_H (2.4mm)
    assert bp.ext_depth == GR_HOLE_H
    expected_h = GR_BASE_HEIGHT + GR_HOLE_H  # 4.75 + 2.4 = 7.15
    assert _almost_same(size_3d(r), (84, 84, expected_h), tol=0.1)
    # Should have 4 holes per cell × 4 cells = 16 magnet holes
    if _export_files("baseplate"):
        bp.save_step_file(filename="./tests/testfiles/gf_baseplate_2x2_magnets.step")


@pytest.mark.skipif(
    SKIP_TEST_BASEPLATE,
    reason="Skipped intentionally by test scope environment variable",
)
def test_screw_baseplate():
    """Baseplate with screw through-holes only."""
    bp = GridfinityBaseplate(2, 2, screw_holes=True)
    r = bp.render()
    assert r.val().isValid()
    # ext_depth should auto-adjust to 4.0mm
    assert bp.ext_depth == 4.0
    expected_h = GR_BASE_HEIGHT + 4.0  # 4.75 + 4.0 = 8.75
    assert _almost_same(size_3d(r), (84, 84, expected_h), tol=0.1)
    if _export_files("baseplate"):
        bp.save_step_file(filename="./tests/testfiles/gf_baseplate_2x2_screws.step")


@pytest.mark.skipif(
    SKIP_TEST_BASEPLATE,
    reason="Skipped intentionally by test scope environment variable",
)
def test_magnet_screw_baseplate():
    """Baseplate with combined magnet recesses and screw through-holes."""
    bp = GridfinityBaseplate(2, 2, magnet_holes=True, screw_holes=True)
    r = bp.render()
    assert r.val().isValid()
    # ext_depth should auto-adjust to GR_HOLE_H + 4.0 = 6.4mm
    assert bp.ext_depth == GR_HOLE_H + 4.0
    expected_h = GR_BASE_HEIGHT + GR_HOLE_H + 4.0  # 4.75 + 6.4 = 11.15
    assert _almost_same(size_3d(r), (84, 84, expected_h), tol=0.1)
    if _export_files("baseplate"):
        bp.save_step_file(
            filename="./tests/testfiles/gf_baseplate_2x2_magnet_screw.step"
        )


@pytest.mark.skipif(
    SKIP_TEST_BASEPLATE,
    reason="Skipped intentionally by test scope environment variable",
)
def test_weighted_baseplate():
    """Weighted baseplate with weight pockets in bottom."""
    bp = GridfinityBaseplate(2, 2, weighted=True, magnet_holes=True)
    r = bp.render()
    assert r.val().isValid()
    # ext_depth should auto-adjust to GR_BP_BOT_H (6.4mm)
    assert bp.ext_depth == GR_BP_BOT_H
    expected_h = GR_BASE_HEIGHT + GR_BP_BOT_H  # 4.75 + 6.4 = 11.15
    assert _almost_same(size_3d(r), (84, 84, expected_h), tol=0.1)
    if _export_files("baseplate"):
        bp.save_step_file(filename="./tests/testfiles/gf_baseplate_2x2_weighted.step")


# --- Screw-together baseplate tests (1B.10) ---


@pytest.mark.skipif(
    SKIP_TEST_BASEPLATE,
    reason="Skipped intentionally by test scope environment variable",
)
def test_screw_together_basic():
    """2x2 screw-together baseplate: valid, correct height and filename."""
    bp = GridfinityBaseplate(2, 2, screw_together=True)
    r = bp.render()
    assert r.val().isValid()
    assert bp.ext_depth == GR_ST_ADDITIONAL_H  # 6.75mm
    expected_h = GR_BASE_HEIGHT + GR_ST_ADDITIONAL_H  # 4.75 + 6.75 = 11.5
    assert _almost_same(size_3d(r), (84, 84, expected_h), tol=0.1)
    assert "_screwtog" in bp.filename()
    if _export_files("baseplate"):
        bp.save_step_file(filename="./tests/testfiles/gf_baseplate_2x2_screwtog.step")


@pytest.mark.skipif(
    SKIP_TEST_BASEPLATE,
    reason="Skipped intentionally by test scope environment variable",
)
def test_screw_together_with_skeleton():
    """Skeleton + screw-together (kennetek style_plate=3): both coexist."""
    bp = GridfinityBaseplate(2, 2, skeleton=True, screw_together=True)
    r = bp.render()
    assert r.val().isValid()
    # ext_depth should be max of skeleton needs and screw-together needs
    assert bp.ext_depth >= GR_ST_ADDITIONAL_H
    assert "_skel" in bp.filename()
    assert "_screwtog" in bp.filename()


@pytest.mark.skipif(
    SKIP_TEST_BASEPLATE,
    reason="Skipped intentionally by test scope environment variable",
)
def test_screw_together_minimal():
    """Screw-together without skeleton (kennetek style_plate=4): valid."""
    bp = GridfinityBaseplate(2, 2, screw_together=True)
    r = bp.render()
    assert r.val().isValid()
    # No skeleton tag, just screwtog
    assert "_skel" not in bp.filename()
    assert "_screwtog" in bp.filename()


@pytest.mark.skipif(
    SKIP_TEST_BASEPLATE,
    reason="Skipped intentionally by test scope environment variable",
)
def test_screw_together_with_magnets():
    """Screw-together + magnet holes: ext_depth = max(6.75, 2.4) = 6.75."""
    bp = GridfinityBaseplate(2, 2, screw_together=True, magnet_holes=True)
    r = bp.render()
    assert r.val().isValid()
    assert bp.ext_depth == GR_ST_ADDITIONAL_H  # 6.75 > 2.4
    assert "_screwtog" in bp.filename()
    assert "_mag" in bp.filename()


@pytest.mark.skipif(
    SKIP_TEST_BASEPLATE,
    reason="Skipped intentionally by test scope environment variable",
)
def test_screw_together_multi_screw():
    """Multi-screw (n_screws=2 and 3): valid, more holes = less volume."""
    bp1 = GridfinityBaseplate(2, 2, screw_together=True, n_screws=1)
    r1 = bp1.render()
    bp2 = GridfinityBaseplate(2, 2, screw_together=True, n_screws=2)
    r2 = bp2.render()
    bp3 = GridfinityBaseplate(2, 2, screw_together=True, n_screws=3)
    r3 = bp3.render()
    assert r1.val().isValid()
    assert r2.val().isValid()
    assert r3.val().isValid()
    # More screws = more material removed
    v1 = r1.val().Volume()
    v2 = r2.val().Volume()
    v3 = r3.val().Volume()
    assert v2 < v1
    assert v3 < v2


@pytest.mark.skipif(
    SKIP_TEST_BASEPLATE,
    reason="Skipped intentionally by test scope environment variable",
)
def test_screw_together_volume():
    """Screw-together has less volume than equivalent non-screw baseplate."""
    # Both use solid-slab render path (magnet_holes triggers _has_bottom_features)
    bp_plain = GridfinityBaseplate(2, 2, magnet_holes=True, ext_depth=GR_ST_ADDITIONAL_H)
    bp_screw = GridfinityBaseplate(2, 2, magnet_holes=True, screw_together=True)
    r_plain = bp_plain.render()
    r_screw = bp_screw.render()
    # Same ext_depth, same magnet holes; screw-together removes additional material
    assert bp_plain.ext_depth == bp_screw.ext_depth
    assert r_screw.val().Volume() < r_plain.val().Volume()


@pytest.mark.skipif(
    SKIP_TEST_BASEPLATE,
    reason="Skipped intentionally by test scope environment variable",
)
def test_screw_together_filename():
    """Filename variations for screw-together configs."""
    bp1 = GridfinityBaseplate(2, 2, screw_together=True)
    assert bp1.filename() == "gf_baseplate_2x2_screwtog"

    bp2 = GridfinityBaseplate(2, 2, screw_together=True, n_screws=2)
    assert bp2.filename() == "gf_baseplate_2x2_screwtog2"

    bp3 = GridfinityBaseplate(2, 2, screw_together=True, n_screws=3)
    assert bp3.filename() == "gf_baseplate_2x2_screwtog3"

    bp4 = GridfinityBaseplate(2, 2, skeleton=True, screw_together=True, magnet_holes=True)
    fn = bp4.filename()
    assert "_skel" in fn
    assert "_screwtog" in fn
    assert "_mag" in fn


@pytest.mark.skipif(
    SKIP_TEST_BASEPLATE,
    reason="Skipped intentionally by test scope environment variable",
)
def test_screw_together_large_grid():
    """4x3 screw-together for tiling correctness on larger grids."""
    bp = GridfinityBaseplate(4, 3, screw_together=True)
    r = bp.render()
    assert r.val().isValid()
    expected_h = GR_BASE_HEIGHT + GR_ST_ADDITIONAL_H
    assert _almost_same(size_3d(r), (168, 126, expected_h), tol=0.1)
    if _export_files("baseplate"):
        bp.save_step_file(filename="./tests/testfiles/gf_baseplate_4x3_screwtog.step")
