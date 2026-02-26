# Gridfinity Lid tests
import pytest

from cqgridfinity import *
from cqgridfinity.extended.lids import GridfinityLid

from cqkit.cq_helpers import size_3d
from cqkit import *

from common_test import (
    EXPORT_STEP_FILE_PATH,
    _almost_same,
    _export_files,
    SKIP_TEST_LID,
)


@pytest.mark.skipif(
    SKIP_TEST_LID, reason="Skipped intentionally by test scope environment variable"
)
def test_flat_lid():
    """Basic flat lid should have correct bounding box."""
    lid = GridfinityLid(2, 2, lid_style="flat")
    r = lid.render()
    bb = size_3d(r)
    # Outer dims match 2x2 bin: 83.5 x 83.5
    assert _almost_same(bb[0], 83.5, tol=0.3)
    assert _almost_same(bb[1], 83.5, tol=0.3)
    # Height = lip_h (~5.6mm) + lid_thickness (1.2mm)
    assert bb[2] > 5.0
    assert bb[2] < 9.0
    assert lid.filename() == "gf_lid_2x2_flat_finger"
    if _export_files("lid"):
        lid.save_step_file(path=EXPORT_STEP_FILE_PATH)


@pytest.mark.skipif(
    SKIP_TEST_LID, reason="Skipped intentionally by test scope environment variable"
)
def test_flat_lid_1x1():
    """Flat lid for smallest bin size."""
    lid = GridfinityLid(1, 1, lid_style="flat")
    r = lid.render()
    bb = size_3d(r)
    assert _almost_same(bb[0], 41.5, tol=0.3)
    assert _almost_same(bb[1], 41.5, tol=0.3)
    assert r.val().Volume() > 0


@pytest.mark.skipif(
    SKIP_TEST_LID, reason="Skipped intentionally by test scope environment variable"
)
def test_flat_lid_no_finger():
    """Flat lid without finger slot."""
    lid = GridfinityLid(2, 2, lid_style="flat", finger_slot=False)
    r = lid.render()
    assert r.val().Volume() > 0
    assert lid.filename() == "gf_lid_2x2_flat"
    # Lid with finger slot should have less volume
    lid_with = GridfinityLid(2, 2, lid_style="flat", finger_slot=True)
    r_with = lid_with.render()
    assert r.val().Volume() > r_with.val().Volume()


@pytest.mark.skipif(
    SKIP_TEST_LID, reason="Skipped intentionally by test scope environment variable"
)
def test_lid_outer_dims_match_bin():
    """Lid outer dimensions must match bin outer dimensions."""
    for lu, wu in [(1, 1), (2, 2), (3, 2), (4, 3)]:
        lid = GridfinityLid(lu, wu)
        box = GridfinityBox(lu, wu, 3)
        assert _almost_same(lid.outer_l, box.outer_l)
        assert _almost_same(lid.outer_w, box.outer_w)


@pytest.mark.skipif(
    SKIP_TEST_LID, reason="Skipped intentionally by test scope environment variable"
)
def test_stackable_lid():
    """Stackable lid should be taller (has baseplate receptacle on top)."""
    lid_flat = GridfinityLid(2, 2, lid_style="flat")
    lid_stack = GridfinityLid(2, 2, lid_style="stackable")
    r_flat = lid_flat.render()
    r_stack = lid_stack.render()
    h_flat = size_3d(r_flat)[2]
    h_stack = size_3d(r_stack)[2]
    # Stackable should be ~4.75mm taller (baseplate height)
    assert h_stack > h_flat + 3.0
    assert _almost_same(size_3d(r_stack)[0], 84.0, tol=0.8)
    assert lid_stack.filename() == "gf_lid_2x2_stackable_finger"
    if _export_files("lid"):
        lid_stack.save_step_file(path=EXPORT_STEP_FILE_PATH)


@pytest.mark.skipif(
    SKIP_TEST_LID, reason="Skipped intentionally by test scope environment variable"
)
def test_lid_with_label():
    """Lid with label recess should have less volume."""
    lid_plain = GridfinityLid(2, 2, label=False)
    lid_label = GridfinityLid(2, 2, label=True)
    r_plain = lid_plain.render()
    r_label = lid_label.render()
    assert r_plain.val().Volume() > r_label.val().Volume()
    assert "label" in lid_label.filename()


@pytest.mark.skipif(
    SKIP_TEST_LID, reason="Skipped intentionally by test scope environment variable"
)
def test_lid_str():
    """String representation should include key parameters."""
    lid = GridfinityLid(2, 2, lid_style="flat", label=True)
    s = str(lid)
    assert "2U x 2U" in s
    assert "flat" in s
    assert "Label" in s


@pytest.mark.skipif(
    SKIP_TEST_LID, reason="Skipped intentionally by test scope environment variable"
)
def test_invalid_lid_style():
    """Invalid lid_style should raise ValueError."""
    with pytest.raises(ValueError):
        GridfinityLid(2, 2, lid_style="invalid")


@pytest.mark.skipif(
    SKIP_TEST_LID, reason="Skipped intentionally by test scope environment variable"
)
def test_lid_is_watertight():
    """Lid should be a valid watertight solid."""
    lid = GridfinityLid(2, 2, lid_style="flat")
    r = lid.render()
    # A valid solid has positive volume
    assert r.val().Volume() > 0
    # Check it has faces on top and bottom
    top_faces = len(r.faces(">Z").vals())
    bot_faces = len(r.faces("<Z").vals())
    assert top_faces >= 1
    assert bot_faces >= 1
