# Gridfinity Item Holder tests
import pytest

from cqgridfinity import *
from cqgridfinity.extended.item_holder import GridfinityItemHolder

from cqkit.cq_helpers import size_3d
from cqkit import *

from common_test import (
    EXPORT_STEP_FILE_PATH,
    _almost_same,
    _export_files,
    SKIP_TEST_ITEMHOLDER,
)


@pytest.mark.skipif(
    SKIP_TEST_ITEMHOLDER, reason="Skipped intentionally by test scope environment variable"
)
def test_battery_holder_AA():
    """AA battery holder should render with pockets."""
    h = GridfinityItemHolder(3, 2, 3, item_preset="AA")
    r = h.render()
    assert _almost_same(size_3d(r)[:2], (125.5, 83.5), tol=0.3)
    # Should have auto-calculated grid
    assert h.grid_x > 0
    assert h.grid_y > 0
    # Volume should be less than a plain bin (pockets removed)
    plain = GridfinityBox(3, 2, 3)
    r_plain = plain.render()
    assert r.val().Volume() < r_plain.val().Volume()
    assert "AA" in h.filename()
    if _export_files("itemholder"):
        h.save_step_file(path=EXPORT_STEP_FILE_PATH)


@pytest.mark.skipif(
    SKIP_TEST_ITEMHOLDER, reason="Skipped intentionally by test scope environment variable"
)
def test_battery_holder_AAA():
    """AAA battery holder with hex layout."""
    h = GridfinityItemHolder(2, 2, 3, item_preset="AAA")
    r = h.render()
    assert r.val().Volume() > 0
    assert h.grid_style == "hex"  # round items default to hex
    assert "AAA" in h.filename()


@pytest.mark.skipif(
    SKIP_TEST_ITEMHOLDER, reason="Skipped intentionally by test scope environment variable"
)
def test_card_holder_SD():
    """SD card holder with auto grid."""
    h = GridfinityItemHolder(2, 1, 3, item_preset="SD")
    r = h.render()
    assert r.val().Volume() > 0
    assert h.grid_style == "square"  # rectangular items default to square
    assert "SD" in h.filename()


@pytest.mark.skipif(
    SKIP_TEST_ITEMHOLDER, reason="Skipped intentionally by test scope environment variable"
)
def test_custom_round_holder():
    """Custom round pockets."""
    h = GridfinityItemHolder(2, 2, 3, item_diameter=10.0, item_height=15.0)
    r = h.render()
    assert _almost_same(size_3d(r)[:2], (83.5, 83.5), tol=0.3)
    assert r.val().Volume() > 0
    assert h.grid_x > 0
    assert h.grid_y > 0


@pytest.mark.skipif(
    SKIP_TEST_ITEMHOLDER, reason="Skipped intentionally by test scope environment variable"
)
def test_custom_rect_holder():
    """Custom rectangular pockets."""
    h = GridfinityItemHolder(2, 2, 3, item_width=20.0, item_depth=10.0, item_height=12.0)
    r = h.render()
    assert r.val().Volume() > 0
    assert h.grid_style == "square"


@pytest.mark.skipif(
    SKIP_TEST_ITEMHOLDER, reason="Skipped intentionally by test scope environment variable"
)
def test_item_holder_with_bin_features():
    """Item holders should inherit all bin features."""
    h = GridfinityItemHolder(
        2, 2, 3, item_preset="AAA",
        holes=True, lip_style="reduced",
    )
    r = h.render()
    assert r.val().Volume() > 0
    assert "gf_itemholder" in h.filename()


@pytest.mark.skipif(
    SKIP_TEST_ITEMHOLDER, reason="Skipped intentionally by test scope environment variable"
)
def test_explicit_grid():
    """Explicitly set grid dimensions."""
    h = GridfinityItemHolder(
        2, 2, 3, item_diameter=10.0, item_height=10.0,
        grid_x=3, grid_y=3, grid_style="square",
    )
    assert h.grid_x == 3
    assert h.grid_y == 3
    r = h.render()
    assert r.val().Volume() > 0


@pytest.mark.skipif(
    SKIP_TEST_ITEMHOLDER, reason="Skipped intentionally by test scope environment variable"
)
def test_invalid_preset():
    """Unknown preset should raise ValueError."""
    with pytest.raises(ValueError):
        GridfinityItemHolder(2, 2, 3, item_preset="nonexistent")


@pytest.mark.skipif(
    SKIP_TEST_ITEMHOLDER, reason="Skipped intentionally by test scope environment variable"
)
def test_no_item_params():
    """Item holder with no item params renders as plain bin."""
    h = GridfinityItemHolder(2, 2, 3)
    r = h.render()
    plain = GridfinityBox(2, 2, 3)
    r_plain = plain.render()
    # Without item parameters, should be approximately equal volume
    assert _almost_same(r.val().Volume(), r_plain.val().Volume(), tol=1.0)
