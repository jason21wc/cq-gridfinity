# Gridfinity tests
import pytest

# my modules
from cqgridfinity import *

from cqkit.cq_helpers import *
from cqkit import *

from common_test import (
    EXPORT_STEP_FILE_PATH,
    _almost_same,
    _export_files,
    SKIP_TEST_RBOX,
)


def _rugged_box():
    b1 = GridfinityRuggedBox(5, 4, 6)
    b1.inside_baseplate = True
    b1.lid_baseplate = True
    b1.front_handle = True
    b1.front_label = True
    b1.side_clasps = True
    b1.stackable = True
    b1.wall_vgrooves = True
    b1.side_handles = True
    b1.back_feet = True
    b1.hinge_bolted = False
    return b1


@pytest.mark.skipif(
    SKIP_TEST_RBOX, reason="Skipped intentionally by test scope environment variable"
)
def test_rugged_box():
    b1 = _rugged_box()
    assert b1.filename() == "gf_ruggedbox_5x4x6_fr-hl_sd-hc_stack_lidbp"
    r = b1.render()
    assert r is not None
    assert r.val().isValid()
    assert _almost_same(size_3d(r), (230.0, 194.15, 47.5))
    if _export_files("rbox"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)


@pytest.mark.skipif(
    SKIP_TEST_RBOX, reason="Skipped intentionally by test scope environment variable"
)
def test_rugged_box_lid():
    """Lid must be a valid solid.

    Was xfail: the integrated Gridfinity baseplate left 48 invalid conical
    faces (4 chamfers per cell, all at one height, all 0.517mm^2). The shell
    was closed and the volume correct, but BRepCheck rejected the faces and
    CAD packages would not treat the lid as a selectable solid body. Fixed by
    repair_if_invalid() in render_lid(); volume and face count are unchanged.
    """
    b1 = _rugged_box()
    r = b1.render_lid()
    assert r is not None
    assert r.val().isValid()
    assert _almost_same(size_3d(r), (230.0, 188, 12.5))
    assert b1.filename() == "gf_ruggedbox_5x4x6_lid_fr-hl_sd-hc_stack_lidbp"
    if _export_files("rbox"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)


@pytest.mark.skipif(
    SKIP_TEST_RBOX, reason="Skipped intentionally by test scope environment variable"
)
def test_rugged_box_acc():
    b1 = _rugged_box()
    r = b1.render_accessories()
    assert len(r.solids().vals()) == 16
    assert b1.filename() == "gf_ruggedbox_5x4x6_acc_fr-hl_sd-hc_stack_lidbp"
    if _export_files("rbox"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)


@pytest.mark.skipif(
    SKIP_TEST_RBOX, reason="Skipped intentionally by test scope environment variable"
)
def test_rugged_box_parts():
    b1 = _rugged_box()
    r = b1.render_handle()
    assert r is not None
    assert r.val().isValid()
    assert b1.filename() == "gf_ruggedbox_5x4x6_handle_fr-hl_sd-hc_stack_lidbp"
    if _export_files("rbox"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)

    r = b1.render_hinge()
    assert r is not None
    assert r.val().isValid()
    assert b1.filename() == "gf_ruggedbox_5x4x6_hinge_fr-hl_sd-hc_stack_lidbp"
    if _export_files("rbox"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)

    r = b1.render_label()
    assert r is not None
    assert r.val().isValid()
    assert b1.filename() == "gf_ruggedbox_5x4x6_label_fr-hl_sd-hc_stack_lidbp"
    if _export_files("rbox"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)

    r = b1.render_latch()
    assert r is not None
    assert r.val().isValid()
    assert b1.filename() == "gf_ruggedbox_5x4x6_latch_fr-hl_sd-hc_stack_lidbp"
    if _export_files("rbox"):
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)


@pytest.mark.skipif(
    SKIP_TEST_RBOX, reason="Skipped intentionally by test scope environment variable"
)
def test_rugged_box_assembly():
    if _export_files("rbox"):
        b1 = _rugged_box()
        r = b1.render_assembly()
        assert b1.filename() == "gf_ruggedbox_5x4x6_assembly_fr-hl_sd-hc_stack_lidbp"
        b1.save_step_file(path=EXPORT_STEP_FILE_PATH)


@pytest.mark.skipif(
    SKIP_TEST_RBOX, reason="Skipped intentionally by test scope environment variable"
)
def test_rugged_box_invalid_dimensions():
    """Verify that invalid dimensions raise ValueError, not AssertionError.
    Rugged box minimum: 3x3x4. This ensures validation works under python -O."""
    with pytest.raises(ValueError, match="length_u must be >= 3"):
        GridfinityRuggedBox(2, 4, 6).check_dimensions()
    with pytest.raises(ValueError, match="width_u must be >= 3"):
        GridfinityRuggedBox(3, 2, 6).check_dimensions()
    with pytest.raises(ValueError, match="height_u must be >= 4"):
        GridfinityRuggedBox(3, 3, 3).check_dimensions()
