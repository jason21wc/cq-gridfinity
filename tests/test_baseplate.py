# Gridfinity tests
import pytest

# my modules
from cqgridfinity import *
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
    # ext_depth should auto-adjust to GR_BP_BOT_H (6.4mm)
    assert bp.ext_depth == GR_BP_BOT_H
    expected_h = GR_BASE_HEIGHT + GR_BP_BOT_H  # 4.75 + 6.4 = 11.15
    assert _almost_same(size_3d(r), (84, 84, expected_h), tol=0.1)
    if _export_files("baseplate"):
        bp.save_step_file(filename="./tests/testfiles/gf_baseplate_2x2_weighted.step")


@pytest.mark.skipif(
    SKIP_TEST_BASEPLATE,
    reason="Skipped intentionally by test scope environment variable",
)
def test_skeletal_baseplate():
    """Skeletal lightweight baseplate with material removed from bottom."""
    bp = GridfinityBaseplate(2, 2, skeletal=True, magnet_holes=True)
    r = bp.render()
    # ext_depth should be at least GR_HOLE_H (2.4) and GR_BP_SKEL_H + 1.0 (2.0)
    assert bp.ext_depth == GR_HOLE_H
    expected_h = GR_BASE_HEIGHT + bp.ext_depth
    assert _almost_same(size_3d(r), (84, 84, expected_h), tol=0.1)
    if _export_files("baseplate"):
        bp.save_step_file(filename="./tests/testfiles/gf_baseplate_2x2_skeletal.step")


@pytest.mark.skipif(
    SKIP_TEST_BASEPLATE,
    reason="Skipped intentionally by test scope environment variable",
)
def test_weighted_skeletal_exclusive():
    """Weighted and skeletal should be mutually exclusive."""
    with pytest.raises(ValueError):
        GridfinityBaseplate(2, 2, weighted=True, skeletal=True)
