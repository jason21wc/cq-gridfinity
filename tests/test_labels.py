"""Cullenect click-in label tests (P4, features 1D.3 and 1D.4).

Unlike most upstream references in this project, Cullenect ships readable MIT
source, so these assert against the source's own expressions rather than
against dimensions transcribed second-hand.
"""

import cadquery as cq
import pytest

from cqgridfinity import CullenectLabel
from cqgridfinity.gf_labels import (
    CL_BASE_Z,
    CL_LATCH_XY,
    CL_LATCH_Z,
    CL_RIB_Z,
    CL_SOCKET_OFFSET,
)


def test_label_dimensions_follow_the_standard():
    """Cullenect: labelX = width_u * 42 - 6; labelY and labelZ are fixed.

    Height and thickness are not parameters by choice -- a label that varied
    them would not swap with anyone else's.
    """
    for u in (1, 2, 3):
        label = CullenectLabel(u)
        assert label.length == pytest.approx(u * 42 - 6)
        assert label.width == pytest.approx(11.0)
        assert label.thickness == pytest.approx(1.2)
    assert CullenectLabel(1).length == pytest.approx(36.0)


def test_label_renders_one_valid_solid():
    for u in (1, 2):
        r = CullenectLabel(u).render()
        assert r.val().isValid()
        assert len(r.val().Solids()) == 1


def test_label_has_a_groove_around_its_perimeter():
    """The whole mechanism. Full width at the base and the cap, inset by
    `latchX` through the middle -- that inset IS the socket latch groove."""
    label = CullenectLabel(1).render().val()

    def width_at(z):
        slab = cq.Workplane("XY").box(60, 20, 0.02).translate((0, 0, z)).val()
        return label.intersect(slab).BoundingBox().ylen

    assert width_at(0.1) == pytest.approx(11.0, abs=0.02)  # base, full
    assert width_at(0.5) == pytest.approx(
        11.0 - 2 * CL_LATCH_XY, abs=0.02
    )  # groove
    assert width_at(1.0) == pytest.approx(11.0, abs=0.02)  # cap, full


def test_groove_spans_exactly_the_latch_height():
    """From the top of the base to `latchZ` above it -- 0.2 to 0.8."""
    label = CullenectLabel(1).render().val()

    def is_grooved(z):
        slab = cq.Workplane("XY").box(60, 20, 0.02).translate((0, 0, z)).val()
        return label.intersect(slab).BoundingBox().ylen < 11.0 - CL_LATCH_XY

    assert not is_grooved(CL_BASE_Z - 0.05)
    assert is_grooved(CL_BASE_Z + 0.05)
    assert is_grooved(CL_BASE_Z + CL_LATCH_Z - 0.05)
    assert not is_grooved(CL_BASE_Z + CL_LATCH_Z + 0.05)


def test_socket_is_offset_from_the_label():
    """`socketX = labelX + 0.3` -- the running clearance that lets a tile
    drop in."""
    label = CullenectLabel(1)
    assert label.socket_length == pytest.approx(label.length + CL_SOCKET_OFFSET)
    assert label.socket_width == pytest.approx(label.width + CL_SOCKET_OFFSET)


def test_socket_negative_keeps_two_ribs():
    """Subtracting the negative from a bin leaves the ribs standing -- they
    are what hold the tile in, so they must NOT be part of the cut."""
    label = CullenectLabel(1)
    neg = label.socket_negative().val()
    # Compare against the cavity built the SAME way -- rounded corners and
    # all -- or the corner radius pollutes the difference.
    plain = label._plate(
        label.socket_length, label.socket_width, label.thickness, radius=0.5
    ).val()
    removed = plain.Volume() - neg.Volume()
    expected = 2 * label.socket_length * CL_LATCH_XY * CL_RIB_Z
    assert removed == pytest.approx(expected, rel=0.02), "ribs missing from the cut"


def test_the_label_actually_seats_in_its_socket():
    """Both sides of the interface in one test.

    Seated, the ribs sit in the groove and nothing collides. Getting in takes
    a deliberate interference -- the cap has to deflect past the ribs, and
    that is the click.
    """
    label = CullenectLabel(1)
    tile = label.render().val()
    wall = (
        cq.Workplane("XY")
        .box(60, 20, label.thickness, centered=(True, True, False))
        .val()
        .cut(label.socket_negative().val())
    )
    assert wall.isValid()
    assert tile.intersect(wall).Volume() == pytest.approx(0.0, abs=1e-6)

    rib_inner = (label.socket_width - 2 * CL_LATCH_XY) / 2
    snap = label.width / 2 - rib_inner
    clearance = rib_inner - (label.width - 2 * CL_LATCH_XY) / 2
    assert snap > 0, "ribs do not overlap the cap; the tile would fall out"
    assert clearance > 0, "ribs bind in the groove; the tile would not seat"
    assert snap == pytest.approx(0.05, abs=0.01)
    assert clearance == pytest.approx(0.15, abs=0.01)


def test_text_refuses_a_system_font_lookup():
    """A system font makes the output depend on the machine that ran it."""
    with pytest.raises(ValueError, match="font_path"):
        CullenectLabel(1, text="M3")
    # Without text, no font is needed.
    assert CullenectLabel(1).render().val().isValid()


def test_filenames_distinguish_width_and_style():
    assert CullenectLabel(1).filename() == "cullenect_label_1u"
    assert "2u" in CullenectLabel(2).filename()
