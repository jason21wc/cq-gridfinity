"""Hole grid tests (P2).

`cylindrical=True` cut one circle per compartment and nothing else. The grid is
now generic -- shape, size, rows, columns -- because with STEP output you can
always tweak a single hole in CAD, but you cannot conjure a 4x12 array by hand.

`cylindrical` remains as sugar and its geometry is unchanged; the legacy tests
in test_bin_features.py are the guard on that.
"""

import math

import pytest

from cqgridfinity import GridfinityBox, HoleGrid


def _render(**kwargs):
    return GridfinityBox(3, 2, 5, **kwargs).render()


# --- Validation -------------------------------------------------------------


def test_rejects_unknown_shape():
    with pytest.raises(ValueError, match="shape must be"):
        HoleGrid(shape="triangle")


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"size": 0}, "size must be positive"),
        ({"size_y": -1}, "size_y must be positive"),
        ({"rows": 0}, "rows must be"),
        ({"cols": -2}, "cols must be"),
        ({"depth": 0}, "depth must be positive"),
        ({"chamfer": -0.1}, "chamfer"),
        ({"clearance": -0.1}, "clearance"),
    ],
)
def test_rejects_bad_attributes(kwargs, match):
    with pytest.raises(ValueError, match=match):
        HoleGrid(**kwargs)


# --- Sizing semantics -------------------------------------------------------


def test_clearance_enlarges_the_hole():
    """Clearance makes the hole bigger so the part fits -- printed holes come
    out undersized, so this must add rather than subtract."""
    g = HoleGrid("circle", size=14.5, clearance=0.25)
    assert g.effective_size == pytest.approx(14.75)


def test_hex_size_is_across_flats():
    """Hex stock is specified across flats: a 1/4in bit shank is 6.35mm AF.
    The footprint is therefore wider across corners by 2/sqrt(3)."""
    g = HoleGrid("hex", size=6.35)
    fx, fy = g.footprint()
    assert fx == pytest.approx(6.35)
    assert fy == pytest.approx(6.35 * 2 / math.sqrt(3))


def test_rect_defaults_to_square():
    assert HoleGrid("rect", size=8).effective_size_y == pytest.approx(8)
    assert HoleGrid("rect", size=8, size_y=3).effective_size_y == pytest.approx(3)


def test_derives_layout_flag():
    assert HoleGrid("circle", size=10).derives_layout
    assert not HoleGrid("circle", size=10, rows=2, cols=3).derives_layout
    assert HoleGrid("circle", size=10, rows=2).derives_layout  # cols still None


# --- Geometry ---------------------------------------------------------------


@pytest.mark.parametrize("shape", ["circle", "hex", "rect"])
def test_each_shape_renders_valid(shape):
    r = _render(hole_grid=HoleGrid(shape, size=8, rows=2, cols=3))
    assert r.val().isValid()
    assert len(r.solids().vals()) == 1


def test_explicit_layout_cuts_requested_hole_count():
    """rows x cols is independent of dividers -- that is the whole point."""
    solid = _render(solid=True).val().Volume()
    few = _render(hole_grid=HoleGrid("circle", size=8, rows=2, cols=2)).val().Volume()
    many = _render(hole_grid=HoleGrid("circle", size=8, rows=2, cols=6)).val().Volume()
    assert few < solid
    # 6 columns removes materially more than 2 at the same hole size.
    assert (solid - many) > (solid - few)


def test_layout_independent_of_dividers():
    """A 4x3 grid must be 12 holes whether or not dividers are present."""
    a = _render(hole_grid=HoleGrid("circle", size=8, rows=3, cols=4)).val().Volume()
    b = (
        _render(
            hole_grid=HoleGrid("circle", size=8, rows=3, cols=4),
            length_div=2,
            width_div=1,
        )
        .val()
        .Volume()
    )
    assert a == pytest.approx(b, rel=1e-9)


def test_depth_limit_removes_less_material():
    full = _render(hole_grid=HoleGrid("circle", size=8, rows=2, cols=3)).val().Volume()
    shallow = (
        _render(hole_grid=HoleGrid("circle", size=8, rows=2, cols=3, depth=5))
        .val()
        .Volume()
    )
    assert shallow > full  # less removed -> more material left


def test_holes_shrink_to_fit_the_cell():
    """An oversized request must be clamped rather than blowing out the walls."""
    r = _render(hole_grid=HoleGrid("circle", size=500, rows=2, cols=3))
    assert r.val().isValid()
    bb = r.val().BoundingBox()
    assert bb.xlen == pytest.approx(3 * 42 - 0.5, abs=0.01)


def test_hole_grid_overrides_cylindrical():
    a = _render(cylindrical=True, hole_grid=HoleGrid("hex", size=8, rows=2, cols=3))
    b = _render(hole_grid=HoleGrid("hex", size=8, rows=2, cols=3))
    assert a.val().Volume() == pytest.approx(b.val().Volume(), rel=1e-9)


def test_no_grid_leaves_box_untouched():
    assert _render(hole_grid=None, cylindrical=False).val().isValid()


# --- Fixed pitch and alignment ---------------------------------------------


def test_pitch_must_be_positive():
    with pytest.raises(ValueError, match="pitch must be positive"):
        HoleGrid("circle", size=8, pitch=0)


def test_align_is_clamped_not_rejected():
    """Matches baseplate fitx/fity, which clamps rather than raising."""
    g = HoleGrid("circle", size=8, align_x=-5, align_y=42)
    assert g.align_x == -1.0
    assert g.align_y == 1.0


def test_pitch_y_defaults_to_pitch():
    assert HoleGrid("circle", size=8, pitch=12).effective_pitch == (12, 12)
    assert HoleGrid("circle", size=8, pitch=12, pitch_y=5).effective_pitch == (12, 5)
    assert HoleGrid("circle", size=8).effective_pitch == (None, None)


def test_fixed_pitch_spacing_is_exact():
    b = GridfinityBox(3, 2, 5)
    g = HoleGrid("circle", size=10, rows=2, cols=4, pitch=15)
    pts, _ = b._hole_grid_positions(g)
    xs = sorted({round(p[0], 6) for p in pts})
    assert len(xs) == 4
    assert all(
        xs[i + 1] - xs[i] == pytest.approx(15) for i in range(len(xs) - 1)
    )


@pytest.mark.parametrize(
    "align,expect_edge",
    [(-1, "low"), (1, "high")],
)
def test_alignment_puts_array_flush_against_the_chosen_edge(align, expect_edge):
    b = GridfinityBox(3, 2, 5)
    size = 10.0
    g = HoleGrid("circle", size=size, rows=2, cols=4, pitch=15, align_x=align)
    pts, _ = b._hole_grid_positions(g)
    xs = sorted({p[0] for p in pts})
    lo_edge, hi_edge = -b.half_in, -b.half_in + b.inner_l
    if expect_edge == "low":
        assert xs[0] - size / 2 == pytest.approx(lo_edge)
    else:
        assert xs[-1] + size / 2 == pytest.approx(hi_edge)


def test_alignment_zero_centres_the_array():
    b = GridfinityBox(3, 2, 5)
    g = HoleGrid("circle", size=10, rows=2, cols=4, pitch=15, align_x=0)
    pts, _ = b._hole_grid_positions(g)
    xs = sorted({p[0] for p in pts})
    centre = -b.half_in + b.inner_l / 2
    assert (xs[0] + xs[-1]) / 2 == pytest.approx(centre)


def test_alignment_ignored_when_spreading_evenly():
    """With no pitch there is no slack, so alignment has nothing to act on."""
    b = GridfinityBox(3, 2, 5)
    a, _ = b._hole_grid_positions(HoleGrid("circle", size=8, rows=2, cols=4))
    c, _ = b._hole_grid_positions(
        HoleGrid("circle", size=8, rows=2, cols=4, align_x=-1, align_y=1)
    )
    assert sorted(a) == pytest.approx(sorted(c))


def test_corner_anchored_grid_renders_valid():
    r = _render(
        hole_grid=HoleGrid(
            "hex", size=8, rows=2, cols=3, pitch=12, align_x=-1, align_y=-1
        )
    )
    assert r.val().isValid()
    assert len(r.solids().vals()) == 1
