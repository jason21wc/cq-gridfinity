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


def _a_font():
    """Any font file, for exercising the text path.

    A TEST may use a system font; OUTPUT may not, which is why `font_path` is
    required rather than looked up. Skips where no font is found so the suite
    stays portable.
    """
    import glob

    for pattern in (
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/**/*.ttf",
    ):
        found = sorted(glob.glob(pattern, recursive=True))
        if found:
            return found[0]
    return None


def test_embossed_text_stands_proud_and_debossed_text_does_not():
    """The text path had no coverage at all until this test: `font_size`,
    `text_depth` and `deboss` were parameters whose geometry nothing ran.
    That is the failure mode this project keeps hitting.
    """
    font = _a_font()
    if font is None:
        pytest.skip("no font available to exercise the text path")

    blank = CullenectLabel(1).render().val()
    emboss = CullenectLabel(1, text="M3x12", font_path=font).render().val()
    deboss = CullenectLabel(1, text="M3x12", font_path=font, deboss=True).render().val()

    for shape in (emboss, deboss):
        assert shape.isValid()
        assert len(shape.Solids()) == 1

    # Embossed text rises exactly `text_depth` above the tile and adds material.
    assert emboss.BoundingBox().zmax == pytest.approx(1.2 + 0.2, abs=1e-3)
    assert emboss.Volume() > blank.Volume()
    # Debossed text cuts in: no protrusion, less material.
    assert deboss.BoundingBox().zmax == pytest.approx(1.2, abs=1e-3)
    assert deboss.Volume() < blank.Volume()


def test_text_uses_the_bundled_font_by_default():
    """No font_path means the BUNDLED font, never a system lookup -- the
    output must not depend on what the machine happens to have installed."""
    from cqgridfinity.gf_fonts import font_path

    label = CullenectLabel(1, text="M3")
    assert label.font_path is None
    assert label.render().val().isValid()
    assert font_path().endswith(".ttf")


def test_a_missing_bundled_font_is_fatal_not_silent():
    """CadQuery accepts a bad fontPath and quietly substitutes a system font,
    so a font missing from the wheel would engrave the wrong typeface on every
    part without raising. gf_fonts checks the file itself."""
    from cqgridfinity.gf_fonts import font_path

    with pytest.raises((FileNotFoundError, ValueError)):
        font_path("NoSuchFont.ttf")


def test_bundled_font_is_a_real_font_file():
    """Guards the failure that actually happened while bundling it: the file
    arrived base64-encoded, and CadQuery rendered it 'successfully' by falling
    back to a system font."""
    from cqgridfinity.gf_fonts import font_path

    with open(font_path(), "rb") as fp:
        assert fp.read(4) == b"\x00\x01\x00\x00"


def test_filenames_distinguish_width_and_style():
    assert CullenectLabel(1).filename() == "cullenect_label_1u"
    assert "2u" in CullenectLabel(2).filename()


# --- Socket on the bin (1D.5) -----------------------------------------------


def test_socket_needs_a_label_shelf_to_cut_into():
    from cqgridfinity import GridfinityBox

    with pytest.raises(ValueError, match="label shelf"):
        GridfinityBox(3, 2, 6, cullenect_socket=True, fillet_interior=False).render()


def test_bin_socket_accepts_the_tile():
    """The half that was missing: 1D.3/1D.4 gave a tile and a negative volume,
    but nothing put the socket ON a bin, so there was no way to bring them
    together. Measured on the real bin, not a test block."""
    from cqgridfinity import GridfinityBox

    b = GridfinityBox(3, 2, 6, labels=True, cullenect_socket=True,
                      fillet_interior=False)
    binned = b.render().val()
    assert binned.isValid()
    assert len(binned.Solids()) == 1

    shelf = b.render_labels().val().BoundingBox()
    tile = CullenectLabel(b.cullenect_label_u)
    placed = tile.render().val().translate(
        ((shelf.xmin + shelf.xmax) / 2,
         (shelf.ymin + shelf.ymax) / 2,
         shelf.zmax - tile.thickness)
    )
    assert binned.intersect(placed).Volume() == pytest.approx(0.0, abs=1e-6)
    # Sits flush with the shelf rather than proud of it.
    assert placed.BoundingBox().zmax == pytest.approx(shelf.zmax, abs=1e-6)


def test_socket_removes_exactly_the_negative_volume():
    from cqgridfinity import GridfinityBox

    plain = GridfinityBox(3, 2, 6, labels=True, fillet_interior=False).render().val()
    socketed = GridfinityBox(3, 2, 6, labels=True, cullenect_socket=True,
                             fillet_interior=False).render().val()
    tile = CullenectLabel(3)
    assert plain.Volume() - socketed.Volume() == pytest.approx(
        tile.socket_negative().val().Volume(), rel=1e-6
    )
