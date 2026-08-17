"""smkent rugged box tests (P3).

Separate module from Pred's box by licence necessity: a derivative of a
NonCommercial work stays NonCommercial, so no code crosses between them.
"""

import math
import os

import pytest

from cqgridfinity import GridfinityRuggedBoxSmkent as SK
from cqgridfinity.gf_ruggedbox_smkent import (
    SK_GF_BORDER,
    SK_HINGE_SIZE_TOL,
    SK_M3,
)
from cqgridfinity.gf_ruggedbox_smkent import _tangent_point


def _box(**kw):
    return SK(5, 4, 6, **kw)


# --- Parametric walls (1E.8) ------------------------------------------------


def test_gridfinity_wall_defaults():
    """Gridfinity presets, not the generic ones."""
    b = _box()
    assert b.wall_thickness == 3.0
    assert b.lip_thickness == 3.0
    assert b.latch_width == 28.0
    assert b.latch_screw_separation == 16.0
    assert b.size_tolerance == 0.20


def test_computed_wall_values_follow_upstream_formulas():
    b = _box(wall_thickness=2.4, lip_thickness=2.0)
    assert b.total_lip_thickness == pytest.approx(4.4)  # wall + lip
    assert b.lip_height == pytest.approx(4.0)  # lip * 2
    assert b.edge_radius == pytest.approx(0.48)  # wall / 5


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"wall_thickness": 0.1}, "wall_thickness"),
        ({"lip_thickness": 20}, "lip_thickness"),
        ({"rib_width": 0.5}, "rib_width"),
        ({"latch_width": 100}, "latch_width"),
        ({"latch_screw_separation": 1}, "latch_screw_separation"),
        ({"size_tolerance": 5}, "size_tolerance"),
        ({"latch_type": "velcro"}, "latch_type"),
    ],
)
def test_parameter_ranges_enforced(kwargs, match):
    with pytest.raises(ValueError, match=match):
        _box(**kwargs)


def test_unknown_kwarg_raises_rather_than_warning():
    """Pred's box warns; a typo silently doing nothing is worse than a stop."""
    with pytest.raises(ValueError, match="unknown keyword"):
        _box(wall_thicknes=3.0)


def test_too_short_box_rejected():
    with pytest.raises(ValueError, match="height_u must be >= 2"):
        SK(5, 4, 1)


def test_size_tolerance_accepts_sub_millimetre_steps():
    """DoD-6: real fit corrections live at 0.05-0.2mm, not 1mm steps."""
    for tol in (0.0, 0.05, 0.1, 0.15, 0.2):
        assert SK(5, 4, 6, size_tolerance=tol).size_tolerance == pytest.approx(tol)


# --- Sizing -----------------------------------------------------------------


def test_interior_holds_the_gridfinity_footprint():
    """smkent: width = Width * l_grid + border, with border = 5.

    Regression: the border was dropped, leaving the cavity exactly n*42 --
    zero clearance for the bins and a corner interference against the
    integrated baseplate, whose radius is 4.0mm to the cavity's 3.75mm.
    """
    b = _box()
    assert b.int_length == pytest.approx(5 * 42 + SK_GF_BORDER)
    assert b.int_width == pytest.approx(4 * 42 + SK_GF_BORDER)
    # Interior height is N*7 PLUS room for the bins' stacking lips, matching
    # smkent's top_height = N*7 + h_lip.
    assert b.int_height == pytest.approx(6 * 7 + b.bin_lip_clearance)


def test_lip_clearance_matches_kennetek_h_lip():
    """smkent budgets lid clearance with kennetek's h_lip = 3.548. We derive
    the same number from our own lip geometry instead of hardcoding it."""
    assert _box().bin_lip_clearance == pytest.approx(3.548, abs=0.01)


def test_a_full_height_bin_actually_fits():
    """The point of the clearance: a 6U bin must fit a 6U box.

    Measured from the rendered solids, not from `int_height`. The parameter
    version of this test passed while the real cavity was 4.2mm short, because
    the interior figure was being spent as the outer extrude height.
    """
    import cadquery as cq

    from cqgridfinity import GridfinityBox

    b = _box()

    # Probe down a grid CELL CENTRE, not the box axis: a bin's base nests into
    # the baseplate receptacle, so what it rests on is the receptacle floor,
    # not the plate rim between cells.
    px = (b.length_u // 2 - (b.length_u - 1) / 2) * 42
    py = (b.width_u // 2 - (b.width_u - 1) / 2) * 42

    def _cavity(shape, outer_h):
        """Material spans down a column through one grid cell."""
        probe = cq.Workplane("XY").circle(5).extrude(outer_h * 3).translate(
            (px, py, -outer_h)
        )
        solid = shape.val().intersect(probe.val())
        spans = [(s.BoundingBox().zmin, s.BoundingBox().zmax) for s in solid.Solids()]
        assert spans, "probe found no material in the cell"
        return spans

    # Body: material from the floor up; cavity is everything above it.
    body_spans = _cavity(b.render_body(), b.body_height)
    floor_top = max(zmax for _, zmax in body_spans)
    body_cavity = b.body_height - floor_top
    # Lid: ceiling material at the top; cavity is everything below it.
    lid_spans = _cavity(b.render_lid(), b.lid_height)
    ceiling_bottom = min(zmin for zmin, _ in lid_spans)
    lid_cavity = ceiling_bottom

    total = body_cavity + lid_cavity
    bin_h = GridfinityBox(2, 2, 6).actual_height
    assert total >= bin_h - 1e-6, (
        "6U box holds only %.3fmm; a 6U bin is %.3fmm" % (total, bin_h)
    )


def test_outer_size_adds_two_total_lip_thicknesses():
    """smkent: outer = inner + total_lip_thickness * 2.

    Regression: this used wall_thickness, making the box 6mm undersized in
    each direction. The outer dimension is set by the LIP land, which is the
    thickest part of the wall -- not by the plain wall.
    """
    b = _box()
    inner_l, inner_w = 5 * 42 + SK_GF_BORDER, 4 * 42 + SK_GF_BORDER
    assert b.box_length == pytest.approx(inner_l + 2 * b.total_lip_thickness)
    assert b.box_width == pytest.approx(inner_w + 2 * b.total_lip_thickness)


def test_body_and_lid_heights_sum_to_interior_plus_two_walls():
    """smkent: each half's outer height is its own interior PLUS a wall.

    Regression: `lid_height` returned the interior figure and was then used as
    the extrude height, so the floor and ceiling were carved out of the
    interior rather than added outside it -- 6mm of capacity, silently.
    """
    b = _box()
    assert b.body_height + b.lid_height == pytest.approx(
        b.int_height + 2 * b.wall_thickness
    )
    assert b.body_height == pytest.approx(b.body_int_height + b.wall_thickness)
    assert b.lid_height == pytest.approx(b.lid_int_height + b.wall_thickness)


# --- Shell geometry ---------------------------------------------------------


def test_body_renders_valid_solid():
    r = _box().render_body()
    assert r.val().isValid()
    assert len(r.solids().vals()) == 1


def test_lid_renders_valid_solid():
    r = _box().render_lid()
    assert r.val().isValid()
    assert len(r.solids().vals()) == 1


def test_body_outer_dimensions():
    """The shell is box_length x box_width; the latch bosses then stand proud
    of the FRONT wall only, by eyelet centre + radius less the wall."""
    b = _box()
    bb = b.render_body().val().BoundingBox()
    proud = b.attachment_screw_offset + b.screw_eyelet_radius - b.total_lip_thickness
    # Knuckles straddle the joint, so the bbox runs an eyelet radius past it.
    assert bb.zlen == pytest.approx(
        b.body_height + b.screw_eyelet_radius, abs=0.01
    )
    # Latch bosses at the front, hinge knuckles at the back, stacking latch
    # mounts on both sides -- every attachment reaches by the same amount.
    assert bb.ylen == pytest.approx(b.box_width + 2 * proud, abs=0.01)
    assert bb.ymax == pytest.approx(b.box_width / 2 + proud, abs=0.01)
    assert bb.xlen == pytest.approx(b.box_length + 2 * proud, abs=0.01)
    # Without stacking latches the sides are bare shell again.
    bare = SK(5, 4, 6, stacking_latches=False).render_body().val().BoundingBox()
    assert bare.xlen == pytest.approx(b.box_length, abs=0.01)


# --- Exact hull translation -------------------------------------------------


def test_tangent_point_is_on_the_circle_and_perpendicular():
    """OpenSCAD hull() of circle+point is bounded by this tangent. Computing it
    exactly keeps the arc analytic instead of faceting it."""
    r, p = 4.5, (-1.5, 16.0)
    tx, ty = _tangent_point(r, p)
    assert math.hypot(tx, ty) == pytest.approx(r)  # on the circle
    # radius . (point - tangent) == 0
    assert tx * (p[0] - tx) + ty * (p[1] - ty) == pytest.approx(0, abs=1e-9)


def test_tangent_point_rejects_interior_point():
    with pytest.raises(ValueError, match="inside the circle"):
        _tangent_point(4.5, (1.0, 1.0))


# --- Lip land and lip seal (1E.3) -------------------------------------------


def _section_at(solid, z, y=0.0, band=1.0):
    """(outer, inner) X extents of the two side walls at height z.

    Probes a narrow band in y rather than the whole cross-section, so support
    ribs -- which sit at known y positions -- are included or avoided
    deliberately instead of quietly inflating a bounding box. y=0 lies between
    ribs on every box wide enough to have them.
    """
    import cadquery as _cq

    probe = _cq.Workplane("XY").box(1000, band, 0.02).translate((0, y, z)).val()
    pieces = solid.intersect(probe).Solids()
    if len(pieces) != 2:
        return None
    left, right = sorted(pieces, key=lambda s: s.BoundingBox().xmin)
    outer = right.BoundingBox().xmax - left.BoundingBox().xmin
    inner = right.BoundingBox().xmin - left.BoundingBox().xmax
    return outer, inner


def _wall_at(solid, z, y=0.0):
    """Wall thickness at height z, or None if there is no ring there."""
    got = _section_at(solid, z, y=y)
    if got is None:
        return None
    outer, inner = got
    return (outer - inner) / 2


def test_the_wall_thickens_outward_not_inward():
    """Which surface moves -- the defect thickness alone cannot see.

    smkent's `_box_wall_shape` subtracts from the OUTER side below the lip:
    the interior is a constant `inner` for the full height and the outside
    steps out at the land. We had it inverted -- constant outer, interior
    bulging 6mm below the lip -- and every thickness assertion in this file
    passed either way, because the thickness was right in both.

    See documents/SHELL-AUDIT-1E8.md.
    """
    b = SK(5, 4, 6, lip_seal_type="none")
    body = b.render_body().val()
    outer_low, inner_low = _section_at(body, 8.0)
    outer_high, inner_high = _section_at(body, b.body_height - 1.0)

    # The interior never moves.
    assert inner_low == pytest.approx(b.int_length, abs=0.05)
    assert inner_high == pytest.approx(b.int_length, abs=0.05)
    # The outside steps out by exactly lip_thickness per side.
    assert outer_low == pytest.approx(b.plain_outer_length, abs=0.05)
    assert outer_high == pytest.approx(b.box_length, abs=0.05)
    assert outer_high - outer_low == pytest.approx(2 * b.lip_thickness, abs=0.05)


def test_outer_chamfer_at_the_outward_end():
    """smkent chamfers the outward end of each half: horizontal
    edge_chamfer_proportion * corner_radius, vertical 1.5x that."""
    b = SK(5, 4, 6, lip_seal_type="none")
    hc, vc = b.outer_chamfer_horizontal, b.outer_chamfer_vertical
    assert hc == pytest.approx(0.95 * 3.75)
    assert vc == pytest.approx(hc * 1.5)
    import cadquery as cq

    body = b.render_body().val()

    def outer_at(z):
        """Narrow band at y=0, between ribs -- the ribs rake with the chamfer
        and would otherwise dominate the extent."""
        slab = cq.Workplane("XY").box(500, 1.0, 0.02).translate((0, 0, z)).val()
        return body.intersect(slab).BoundingBox().xlen

    # Sample inside the chamfer's linear stretch, clear of the edge rounding
    # at either end, and check its slope: 2 * horizontal over vertical.
    lo, hi = 1.5, 3.5
    slope = (outer_at(hi) - outer_at(lo)) / (hi - lo)
    assert slope == pytest.approx(2 * hc / vc, rel=0.02)
    # And by the top of the chamfer it has reached the plain wall.
    assert outer_at(vc + 0.5) == pytest.approx(b.plain_outer_length, abs=0.05)
    # The chamfer really removes material: the base is well inside the wall.
    assert outer_at(0.3) < b.plain_outer_length - 2 * hc * 0.8


def test_wall_thickens_into_a_lip_land():
    """smkent's wall is wall_thickness for most of its height and thickens to
    total_lip_thickness over the top lip_height. That land is where the seal
    lives -- without it the groove falls half outside the material."""
    b = SK(5, 4, 6, lip_seal_type="none")
    body = b.render_body().val()
    # The part height, NOT the bounding box: hinge knuckles straddle the joint
    # and push the bbox above the rim.
    h = b.body_height
    assert _wall_at(body, h * 0.4) == pytest.approx(b.wall_thickness, abs=0.05)
    assert _wall_at(body, h - 1.0) == pytest.approx(
        b.total_lip_thickness, abs=0.05
    )


def test_lid_lip_land_is_at_the_bottom():
    """The lid is the mirror image: its land meets the body.

    Probe inside the cavity region only -- the lid's roof is solid above the
    void, so there is no ring to measure up there.
    """
    b = SK(5, 4, 6, lip_seal_type="none")
    lid = b.render_lid().val()
    assert _wall_at(lid, 1.0) == pytest.approx(b.total_lip_thickness, abs=0.05)
    # Higher up, well inside the cavity, the wall has thinned back down.
    upper = _wall_at(lid, b.lid_height - b.wall_thickness - 1.0)
    assert upper is not None, "probe fell outside the cavity"
    assert upper < b.total_lip_thickness - 1.0, "wall never thins above the land"


def test_lid_is_tall_enough_for_the_full_lip_profile():
    """The lid's INTERIOR must clear ramp + land (10.5mm), or its land never
    reaches full thickness. smkent's Top_Height default is 2."""
    b = SK(5, 4, 6)
    assert b.lid_int_height >= b.lip_height + b.lip_thickness * 1.5


@pytest.mark.parametrize("seal", ["none", "wedge", "square", "filament-1.75mm"])
def test_every_seal_type_yields_one_solid(seal):
    """A moulded ridge sits below the mating plane and touches the lid on a
    coplanar face, which OpenCASCADE will not fuse -- it came through as a
    second disconnected solid until the ridge was embedded past the clearance
    offset."""
    b = SK(5, 4, 6, lip_seal_type=seal)
    for part in (b.render_body(), b.render_lid()):
        assert part.val().isValid()
        assert len(part.val().Solids()) == 1


def test_seal_groove_lands_fully_in_material():
    """The check that caught the missing lip land.

    A moulded groove must remove the WHOLE ring from the body. When the wall
    was a constant 3mm the ring was only a quarter buried, so the seal would
    have leaked while looking correct in CAD.
    """
    for seal in ("wedge", "square"):
        plain = SK(5, 4, 6, lip_seal_type="none").render_body().val().Volume()
        b = SK(5, 4, 6, lip_seal_type=seal)
        removed = plain - b.render_body().val().Volume()
        assert removed == pytest.approx(
            b.render_seal_ring().val().Volume(), rel=1e-3
        )


def test_filament_seal_grooves_both_halves_equally():
    """The filament gasket needs a matching half-round channel in each half."""
    b = SK(5, 4, 6, lip_seal_type="filament-1.75mm")
    plain = SK(5, 4, 6, lip_seal_type="none")
    d_body = plain.render_body().val().Volume() - b.render_body().val().Volume()
    d_lid = plain.render_lid().val().Volume() - b.render_lid().val().Volume()
    assert d_body == pytest.approx(d_lid, rel=1e-3), "grooves are asymmetric"
    # Each half takes half the ring.
    assert d_body + d_lid == pytest.approx(
        b.render_seal_ring().val().Volume(), rel=1e-2
    )


def test_seal_ring_matches_its_analytic_volume():
    """Filament seal is a circular sweep: pi*r^2 * path length."""
    import math as _m

    b = SK(5, 4, 6, lip_seal_type="filament-1.75mm")
    path = b._seal_path()
    length = path.Length() if callable(path.Length) else path.Length
    r = 1.75 / 2
    assert b.render_seal_ring().val().Volume() == pytest.approx(
        _m.pi * r * r * length, rel=1e-3
    )


def test_unknown_seal_type_rejected():
    with pytest.raises(ValueError, match="lip_seal_type"):
        SK(5, 4, 6, lip_seal_type="rubber-band")


# --- Exact hull of circles (draw latch prerequisite) ------------------------


def test_hull_of_equal_circles_is_a_stadium():
    """Analytic check: two equal circles hull to pi*r^2 + 2*r*d."""
    import math as _m

    from cqgridfinity.gf_ruggedbox_smkent import _hull_of_circles, _wire_from_hull

    r, d = 3.0, 10.0
    area = _wire_from_hull(
        _hull_of_circles([(0, 0, r), (d, 0, r)])
    ).extrude(1).val().Volume()
    assert area == pytest.approx(_m.pi * r * r + 2 * r * d, abs=0.01)


@pytest.mark.parametrize(
    "circles",
    [
        [(0, 0, 3.0), (10, 0, 3.0)],
        [(0, 0, 4.0), (12, 0, 1.5)],          # unequal radii
        [(0, 0, 3.0), (10, 0, 2.0), (5, 9, 1.5)],
    ],
)
def test_hull_contains_every_circle(circles):
    """The hull must enclose all input circles.

    Equal radii can be done with offset2D; unequal radii cannot, and that is
    the case the draw latch needs. Sampling each circle's rim is the check that
    the tangent-line construction is right rather than merely plausible.
    """
    import math as _m

    import cadquery as _cq

    from cqgridfinity.gf_ruggedbox_smkent import _hull_of_circles, _wire_from_hull

    face = _wire_from_hull(_hull_of_circles(circles)).extrude(1).val()
    for cx, cy, r in circles:
        for k in range(36):
            a = 2 * _m.pi * k / 36
            probe = _cq.Workplane("XY").box(0.02, 0.02, 0.02).translate(
                (cx + r * _m.cos(a), cy + r * _m.sin(a), 0.5)
            )
            assert face.intersect(probe.val()).Volume() > 1e-9, (
                "circle rim falls outside the hull"
            )


def test_hull_rejects_contained_circle():
    """One circle swallowing another is the case the ordering cannot handle."""
    from cqgridfinity.gf_ruggedbox_smkent import _hull_of_circles

    with pytest.raises(ValueError, match="contains another"):
        _hull_of_circles([(0, 0, 10.0), (1, 0, 2.0)])


# --- Clip latch (1E.1) ------------------------------------------------------


def test_clip_latch_renders_valid_solid():
    r = _box().render_latch()
    assert r.val().isValid()
    assert len(r.solids().vals()) == 1


def test_clip_latch_width_follows_parameter():
    """The PART is `size_tolerance` narrower per side than the space reserved
    for it -- smkent `_latch_width() = latch_width - size_tolerance * 2`.

    Regression: this asserted the rendered latch equalled the raw parameter,
    which is what the defect did. The latch came out 0.4mm too wide to drop
    between its own ribs, and `size_tolerance` -- documented as the knob for
    exactly this -- changed no geometry at all.
    """
    for width in (22.0, 28.0, 34.0):
        b = _box(latch_width=width)
        bb = b.render_latch().val().BoundingBox()
        assert bb.zlen == pytest.approx(width - 2 * b.size_tolerance, abs=0.01)


def test_size_tolerance_actually_moves_the_latch():
    """The knob must change metal, not just a stored value. Two tolerances,
    two different parts, differing by exactly twice the change."""
    loose = _box(size_tolerance=0.0).render_latch().val().BoundingBox().zlen
    tight = _box(size_tolerance=0.2).render_latch().val().BoundingBox().zlen
    assert loose - tight == pytest.approx(0.4, abs=0.01)


def test_clip_latch_geometry_stays_analytic():
    """The whole premise is B-Rep. A hull() translated as a polygon would show
    up here as a pile of planar facets and no cylinders."""
    from OCP.BRepAdaptor import BRepAdaptor_Surface

    faces = _box().render_latch().val().Faces()
    kinds = [
        str(BRepAdaptor_Surface(f.wrapped).GetType()).rsplit("_", 1)[-1]
        for f in faces
    ]
    assert kinds.count("Cylinder") >= 4, "hinge/catch arcs must stay cylindrical"
    assert kinds.count("Torus") >= 2, "broken edges must stay analytic"


def test_clip_latch_profile_corners_are_rounded():
    """smkent wraps `_clip_latch_shape` in `_round_shape($b_edge_radius)`.

    That is a SECOND rounding, separate from and smaller than the
    `latch_edge_radius` break on the end faces -- upstream applies both, and
    we applied only the end-face one. On a prismatic solid the profile
    rounding shows up as cylinders of exactly `edge_radius`.
    """
    from OCP.BRepAdaptor import BRepAdaptor_Surface

    b = _box()
    radii = []
    for f in b.render_latch().val().Faces():
        surf = BRepAdaptor_Surface(f.wrapped)
        if str(surf.GetType()).rsplit("_", 1)[-1] == "Cylinder":
            radii.append(surf.Cylinder().Radius())
    assert any(
        abs(r - b.edge_radius) < 1e-6 for r in radii
    ), "no profile corner was rounded at edge_radius (got %s)" % sorted(
        set(round(r, 3) for r in radii)
    )


def test_render_latch_dispatches_on_style():
    """The clip latch is one flexing part; the draw latch is two, joined by a
    pin, so it comes back as a compound rather than a fake single solid."""
    assert len(_box().render_latch().val().Solids()) == 1
    draw = _box(latch_type="draw").render_latch()
    assert len(draw.val().Solids()) == 2
    for s in draw.val().Solids():
        assert s.isValid()


def test_draw_latch_opens_about_its_pin():
    """Closing the loop on the open item: the parts are now posed, not just
    built. Swinging the catch must move it without changing what it is."""
    b = _box(latch_type="draw")
    closed = b.render_latch().val()
    opened = b.render_latch(open_angle=45).val()
    assert len(opened.Solids()) == len(closed.Solids())
    assert opened.Volume() == pytest.approx(closed.Volume(), rel=1e-9)
    # The bounding box is set by the handle, which does not move -- compare
    # where the individual parts sit instead.
    def centres(shape):
        return sorted(round(s.Center().y, 3) for s in shape.Solids())

    assert centres(opened) != centres(closed), "the catch did not move"


# --- Draw latch (1E.2) ------------------------------------------------------


def test_draw_latch_constants_follow_upstream_formulas():
    """From smkent's "Internal constants" block."""
    from cqgridfinity.gf_ruggedbox_smkent import (
        SK_DRAW_HANDLE_LENGTH, SK_DRAW_PIN_HANDLE_R, SK_DRAW_PIN_R,
        SK_DRAW_SCREW_EYELET_R, SK_DRAW_THICKNESS,
    )

    assert SK_DRAW_THICKNESS == pytest.approx(2.25)      # latch_base_size / 2
    assert SK_DRAW_HANDLE_LENGTH == pytest.approx(14.625)  # base_size * 3.25
    assert SK_DRAW_SCREW_EYELET_R == pytest.approx(3.3)  # screw_d * 1.1
    assert SK_DRAW_PIN_HANDLE_R == pytest.approx(4.8)    # screw_d * 1.6
    assert SK_DRAW_PIN_R == pytest.approx(2.6)           # pin_handle_r - 2.2


def test_draw_latch_catch_body_is_an_exact_stadium():
    """Two equal circles hulled -> pi*r^2 + 2*r*span, times the latch width.

    Checks the volume analytically rather than just isValid: an approximated
    hull would be close but not exact, and that is the failure mode worth
    catching.
    """
    import math as _m

    b = _box()
    circles = b._draw_latch_catch_body_circles()
    span = abs(circles[1][1] - circles[0][1])
    t = circles[0][2]
    vol = b.render_draw_latch_catch_body().val().Volume()
    expected = (_m.pi * t * t + 2 * t * span) * b.latch_part_width
    assert vol == pytest.approx(expected, rel=1e-6)


def test_draw_latch_catch_body_keeps_analytic_end_caps():
    """The hull's arcs must survive as cylinders, not become facets."""
    from OCP.BRepAdaptor import BRepAdaptor_Surface

    faces = _box().render_draw_latch_catch_body().val().Faces()
    kinds = [str(BRepAdaptor_Surface(f.wrapped).GetType()).rsplit("_", 1)[-1]
             for f in faces]
    assert kinds.count("Cylinder") == 2, "stadium end caps must stay cylindrical"


def test_draw_latch_catch_body_renders_valid():
    r = _box().render_draw_latch_catch_body()
    assert r.val().isValid()
    assert len(r.solids().vals()) == 1


def test_draw_latch_hook_renders_valid():
    b = _box()
    r = b._draw_latch_hook_solid(b.latch_part_width)
    assert r.val().isValid()
    assert len(r.solids().vals()) == 1


def test_draw_latch_hook_dimensions_follow_source():
    """outr = eyelet_r + 2*thickness = 7.8; claw spans -outr*0.65 .. +outr."""
    from cqgridfinity.gf_ruggedbox_smkent import (
        SK_DRAW_SCREW_EYELET_R, SK_DRAW_THICKNESS,
    )

    b = _box()
    outr = SK_DRAW_SCREW_EYELET_R + SK_DRAW_THICKNESS * 2
    assert outr == pytest.approx(7.8)
    bb = b._draw_latch_hook_solid(b.latch_part_width).val().BoundingBox()
    assert bb.ylen == pytest.approx(outr, abs=0.01)
    assert bb.xlen == pytest.approx(outr + outr * 0.65, abs=0.01)


def test_draw_latch_throat_is_asymmetric():
    """The throat is the mechanism, not decoration.

    smkent cuts it with two ellipse quarters scaled (1+cr) and (1-cr), so the
    mouth is wider where the keeper enters and tighter where it is retained. A
    symmetric circular throat would either not close by hand or not hold.
    Approximating the ellipses with circles loses exactly this.
    """
    import cadquery as _cq

    b = _box()
    h = b.latch_part_width
    hook = b._draw_latch_hook_solid(h).val()
    er, cr = 3.3, 0.52
    cx = -er * cr

    def is_void(x, y):
        probe = _cq.Workplane("XY").box(0.15, 0.15, 0.15).translate((x, y, h / 2))
        return hook.intersect(probe.val()).Volume() < 1e-9

    y = 2.5
    # Analytic reach of each lobe at this height.
    scale = (1 - (y / er) ** 2) ** 0.5
    tight_reach = er * (1 - cr) * scale
    wide_reach = er * (1 + cr) * scale
    assert wide_reach / tight_reach == pytest.approx((1 + cr) / (1 - cr))

    # Inside each lobe is void; comfortably outside is material.
    assert is_void(cx + wide_reach * 0.5, y), "entry side should be open"
    assert not is_void(cx - tight_reach * 2.0, y), "retention side should be solid"
    # And the entry side is open well past where the retention side is solid.
    assert is_void(cx + tight_reach * 2.0, y), (
        "throat is symmetric -- the ellipse scaling was lost"
    )


def test_draw_latch_hook_keeps_ellipses_analytic():
    """Ellipse arcs must survive as analytic surfaces, not facets."""
    from OCP.BRepAdaptor import BRepAdaptor_Surface

    b = _box()
    kinds = [
        str(BRepAdaptor_Surface(f.wrapped).GetType()).rsplit("_", 1)[-1]
        for f in b._draw_latch_hook_solid(b.latch_part_width).val().Faces()
    ]
    assert kinds.count("Cylinder") >= 3, "circular arcs must stay cylindrical"
    assert "SurfaceOfExtrusion" in kinds, "ellipse arcs must stay analytic"


def test_draw_latch_catch_combines_body_and_hook():
    b = _box()
    catch = b.render_draw_latch_catch()
    assert catch.val().isValid()
    assert len(catch.solids().vals()) == 1
    # Taller than the body alone -- the hook sits above it.
    assert (catch.val().BoundingBox().ylen
            > b.render_draw_latch_catch_body().val().BoundingBox().ylen)


def test_draw_latch_handle_arm_renders_valid():
    r = _box().render_draw_latch_handle_arm()
    assert r.val().isValid()
    assert len(r.solids().vals()) == 1


def test_draw_latch_handle_arm_dimensions():
    """Hull of the eyelet (r=3.3 at origin) and pin boss (r=4.8 at
    (-1.5, -14.625)), so x spans -6.3..3.3 and y spans -19.425..3.3."""
    b = _box()
    bb = b.render_draw_latch_handle_arm().val().BoundingBox()
    assert bb.xlen == pytest.approx(9.6, abs=0.01)
    assert bb.ylen == pytest.approx(22.725, abs=0.01)
    assert bb.zlen == pytest.approx(b.latch_part_width, abs=0.01)


def test_draw_latch_handle_arm_hull_area_matches_sampled_hull():
    """Independent cross-check of the UNEQUAL-radius hull.

    Polygon hulls of densely sampled rims inscribe the arcs, so they approach
    the true area from below. Convergence to our value confirms the tangent-line
    construction rather than merely that it produced a solid.
    """
    import math as _m

    from cqgridfinity.gf_ruggedbox_smkent import (
        _convex_hull_2d, _hull_of_circles, _wire_from_hull,
    )

    b = _box()
    circles = b._draw_latch_handle_hull_circles()
    ours = _wire_from_hull(_hull_of_circles(circles)).extrude(1).val().Volume()
    areas = []
    for n in (48, 384):
        pts = [
            (round(cx + r * _m.cos(2 * _m.pi * k / n), 9),
             round(cy + r * _m.sin(2 * _m.pi * k / n), 9))
            for cx, cy, r in circles for k in range(n)
        ]
        h = _convex_hull_2d(pts)
        areas.append(abs(sum(
            h[i][0] * h[(i + 1) % len(h)][1] - h[(i + 1) % len(h)][0] * h[i][1]
            for i in range(len(h))
        )) / 2)
    assert all(a <= ours + 1e-6 for a in areas), "sampled hull exceeds ours"
    assert areas[-1] == pytest.approx(ours, rel=1e-3), "not converging to ours"


def test_draw_latch_handle_arm_has_both_holes():
    """Pin hole and screw hole must actually be cut."""
    import cadquery as _cq

    from cqgridfinity.gf_ruggedbox_smkent import (
        _hull_of_circles, _wire_from_hull,
    )

    b = _box()
    solid_hull = _wire_from_hull(
        _hull_of_circles(b._draw_latch_handle_hull_circles())
    ).extrude(b.latch_part_width).val().Volume()
    drilled = b.render_draw_latch_handle_arm().val().Volume()
    assert drilled < solid_hull, "no material removed"
    # Two through-holes of known radius.
    from cqgridfinity.gf_ruggedbox_smkent import (
        SK_DRAW_PIN_R, SK_DRAW_SEP, SK_M3, SK_SCREW_HOLE_TOL,
    )
    import math as _m

    pin_a = _m.pi * (SK_DRAW_PIN_R + SK_DRAW_SEP) ** 2
    screw_a = _m.pi * ((SK_M3 + SK_SCREW_HOLE_TOL + SK_M3 * 0.2) / 2) ** 2
    assert solid_hull - drilled == pytest.approx(
        (pin_a + screw_a) * b.latch_part_width, rel=1e-6
    )


def test_draw_latch_pin_hole_is_offset_from_the_boss():
    """Not a centring error: smkent biases the pivot by screw_diameter * 0.1."""
    b = _box()
    boss = b._draw_latch_handle_hull_circles()[1]
    assert b._draw_pin_offset[0] == pytest.approx(boss[0] - SK_M3 * 0.1)
    assert b._draw_pin_offset[1] == pytest.approx(boss[1])


def test_draw_latch_handle_renders_valid():
    r = _box().render_draw_latch_handle()
    assert r.val().isValid()
    assert len(r.solids().vals()) == 1


def test_draw_latch_handle_includes_the_elbow():
    """The handle is the arm PLUS the bent elbow, so it must reach further
    than the arm alone in both x and y."""
    b = _box()
    arm = b.render_draw_latch_handle_arm().val().BoundingBox()
    full = b.render_draw_latch_handle().val().BoundingBox()
    assert full.xlen > arm.xlen
    assert full.ylen > arm.ylen


def test_draw_latch_curve_closing_fills_concave_junctions():
    """smkent's offset(-r) offset(r) is a CLOSING: it must ADD material in the
    concave corners while leaving the outer extent unchanged."""
    b = _box()
    h = b.latch_part_width
    closed = b._draw_latch_curve_solid(h).val()
    # Rebuild the un-closed union to compare against.
    import cadquery as _cq

    from cqgridfinity.gf_ruggedbox_smkent import (
        SK_DRAW_BODY_CURVE_R, SK_DRAW_PIN_HANDLE_R, SK_DRAW_SCREW_EYELET_R,
        SK_DRAW_THICKNESS,
    )

    roff = SK_DRAW_PIN_HANDLE_R - SK_DRAW_SCREW_EYELET_R
    circ = (_cq.Workplane("XY").circle(SK_DRAW_PIN_HANDLE_R).extrude(h)
            .translate((-roff, 0, 0)))
    assert closed.Volume() > circ.val().Volume()
    # Closing never grows the silhouette.
    cb = closed.BoundingBox()
    assert cb.xlen < SK_DRAW_BODY_CURVE_R * 2
    assert closed.isValid()


def test_draw_latch_handle_keeps_geometry_analytic():
    """Arcs stay cylindrical and the face count stays low.

    NOTE: B-splines are NOT a failure here. An earlier version of this test
    asserted their absence and called them a "fallback", which conflates them
    with facets. A B-spline is exact analytic geometry -- it is what a lofted
    surface correctly produces, and the grip is lofted on purpose. The thing
    worth catching is FACETING: an arc degraded into dozens of tiny planes.
    """
    from OCP.BRepAdaptor import BRepAdaptor_Surface

    kinds = [
        str(BRepAdaptor_Surface(f.wrapped).GetType()).rsplit("_", 1)[-1]
        for f in _box().render_draw_latch_handle().val().Faces()
    ]
    assert kinds.count("Cylinder") >= 5, "arcs must survive as cylinders"
    # A faceted arc would show up as a pile of planes; the handle has a
    # handful of genuinely flat faces and nothing like a tessellation.
    assert kinds.count("Plane") <= 12, "planar face count suggests faceting"
    assert len(kinds) < 40, "face count suggests tessellation, not B-Rep"


def test_draw_latch_handle_holes_survive_the_union():
    """Order matters: union the elbow FIRST, drill after. Drilling first would
    let the elbow backfill the pin hole."""
    import math as _m

    from cqgridfinity.gf_ruggedbox_smkent import SK_DRAW_PIN_R, SK_DRAW_SEP

    b = _box()
    h = b.latch_part_width
    handle = b.render_draw_latch_handle().val()
    # Probe the pin hole centre -- must be empty.
    import cadquery as _cq

    px, py = b._draw_pin_offset
    probe = _cq.Workplane("XY").box(0.3, 0.3, 0.3).translate((px, py, h / 2))
    assert handle.intersect(probe.val()).Volume() < 1e-9, "pin hole backfilled"
    # And the screw hole at the origin.
    probe2 = _cq.Workplane("XY").box(0.3, 0.3, 0.3).translate((0, 0, h / 2))
    assert handle.intersect(probe2.val()).Volume() < 1e-9, "screw hole backfilled"


# --- Grip (lofted, deliberate divergence from upstream) ---------------------


def test_grip_curve_radius_is_a_symmetric_saddle():
    """smkent varies the curve radius across the width with cos():
    flatter in the middle, tighter at the edges. That is what makes the grip
    sit in a fingertip rather than being a plain extruded rib."""
    b = _box()
    lw = b.latch_part_width
    mid = b._grip_curve_radius(lw / 2)
    edge = b._grip_curve_radius(0.0)
    assert mid == pytest.approx(14.4, abs=0.05)
    assert edge == pytest.approx(4.45, abs=0.05)
    assert mid > edge, "grip should be flatter at the centre"
    # Symmetric about the centreline.
    for d in (2.0, 5.0, 11.0):
        assert b._grip_curve_radius(lw / 2 - d) == pytest.approx(
            b._grip_curve_radius(lw / 2 + d)
        )


def test_grip_lofts_to_a_valid_solid():
    r = _box()._draw_latch_grip_solid()
    assert r.val().isValid()
    assert len(r.solids().vals()) == 1


def test_grip_spans_the_full_latch_width():
    b = _box()
    bb = b._draw_latch_grip_solid().val().BoundingBox()
    assert bb.zlen == pytest.approx(b.latch_part_width, abs=0.01)


def test_grip_is_lofted_not_faceted():
    """The point of the divergence: smkent stacks 10 polyhedra because
    OpenSCAD cannot loft. We loft, so the surface must come through as
    B-splines rather than a pile of planes."""
    from OCP.BRepAdaptor import BRepAdaptor_Surface

    kinds = [
        str(BRepAdaptor_Surface(f.wrapped).GetType()).rsplit("_", 1)[-1]
        for f in _box()._draw_latch_grip_solid().val().Faces()
    ]
    assert kinds.count("BSplineSurface") >= 4, "grip should be a lofted surface"
    assert kinds.count("Plane") <= 2, "only the two end caps should be planar"


def test_grip_section_count_does_not_change_the_form():
    """More loft sections must refine the same surface, not alter it."""
    b = _box()
    coarse = b._draw_latch_grip_solid(sections=9).val()
    fine = b._draw_latch_grip_solid(sections=25).val()
    assert fine.Volume() == pytest.approx(coarse.Volume(), rel=0.02)


def test_handle_includes_the_grip():
    b = _box()
    without = b.render_draw_latch_handle_arm().val().BoundingBox()
    full = b.render_draw_latch_handle().val().BoundingBox()
    assert full.ylen > without.ylen + 5, "grip should extend the handle"
    assert b.render_draw_latch_handle().val().isValid()


# --- Interlocking segments --------------------------------------------------


def test_segment_bands_interleave_with_clearance():
    """5 bands, odd ones used. The catch KEEPS them, the handle SUBTRACTS
    them widened by vsep -- that difference is the running clearance."""
    from cqgridfinity.gf_ruggedbox_smkent import SK_DRAW_VSEP

    b = _box()
    catch = b.segment_bands(False)
    handle = b.segment_bands(True)
    assert len(catch) == 2 and len(handle) == 2
    seg = b.latch_part_width / 5
    assert catch[0] == pytest.approx((seg, 2 * seg))
    for (c0, c1), (h0, h1) in zip(catch, handle):
        assert h0 == pytest.approx(c0 - SK_DRAW_VSEP)
        assert h1 == pytest.approx(c1 + SK_DRAW_VSEP)


def test_catch_stays_one_printable_piece():
    """Only the pin ATTACH is segmented; body, hook and pin barrel stay full
    width, and the flanges bridge them through the odd bands.

    Regression: this asserted the catch reduced to TWO solids -- the defect
    written down as the expectation, while the test directly below it rightly
    demanded the handle stay in one piece. A catch in two pieces cannot be
    printed, and the meshing test could not see it: two parts that do not
    touch interfere by exactly zero.
    """
    b = _box()
    cs = b.render_draw_latch_catch_segmented().val()
    assert cs.isValid()
    assert len(cs.Solids()) == 1, "catch must be one printable piece"
    # It IS segmented, though: less material than the full-width catch.
    assert cs.Volume() < b.render_draw_latch_catch().val().Volume()


def test_handle_slots_do_not_sever_it():
    """The bands are SLOTS, not through-cuts. Cutting full-width slabs would
    leave three disconnected pieces, so the cut is confined to the catch's
    footprint."""
    b = _box()
    hs = b.render_draw_latch_handle_segmented().val()
    assert hs.isValid()
    assert len(hs.Solids()) == 1, "handle must remain one piece"
    assert hs.Volume() < b.render_draw_latch_handle().val().Volume(), (
        "no material removed -- the slots were not cut"
    )


def test_segmented_parts_mesh_without_interference():
    """The whole point of the segmentation.

    Un-segmented the two halves occupy the same space at the pin. Segmented,
    they must interleave with zero overlap -- otherwise the printed parts bind
    and the joint will not turn.
    """
    b = _box()
    solid_overlap = (
        b.render_draw_latch_handle().val()
        .intersect(b.render_draw_latch_catch().val()).Volume()
    )
    assert solid_overlap > 100, "expected the halves to collide before segmenting"

    meshed = (
        b.render_draw_latch_handle_segmented().val()
        .intersect(b.render_draw_latch_catch_segmented().val()).Volume()
    )
    assert meshed == pytest.approx(0.0, abs=1e-6), "meshed parts interfere"


def test_catch_pin_boss_reaches_the_handle():
    """Without the pin boss the two parts barely overlap and there is nothing
    to interlock -- which is exactly how a missing boss shows up."""
    b = _box()
    cb = b.render_draw_latch_catch().val().BoundingBox()
    hb = b.render_draw_latch_handle().val().BoundingBox()
    assert cb.xmin < hb.xmax and cb.ymin < hb.ymax, "catch does not reach the handle"


# --- Attachment placement and eyelets (1E.10, 1E.11) ------------------------


def test_latch_count_follows_the_wrapper_rule():
    """smkent's Gridfinity wrapper: `latch_count = (Width <= 2 ? 1 : 2)`,
    where its Width is our length_u."""
    assert SK(2, 2, 6).latch_count == 1
    assert SK(3, 2, 6).latch_count == 2


def test_attachment_positions_mirror_about_the_centre():
    """smkent `rb_latch_hinge_position() = l_grid * (Width / 2 - 0.5)`."""
    b = SK(5, 4, 6)
    assert b.attachment_positions() == pytest.approx([-84.0, 84.0])
    assert b.latch_hinge_position == pytest.approx(42 * (5 / 2 - 0.5))
    # A single-latch box has one central site.
    assert SK(2, 2, 6).attachment_positions() == pytest.approx([0.0])


@pytest.mark.parametrize(
    "length_u,expected",
    [(3, False), (4, False), (5, True), (6, True)],
)
def test_third_hinge_activates_at_five_units(length_u, expected):
    """1E.6. smkent: `third_hinge_width > 0 && inner_width >= third_hinge_width`
    with `third_hinge_width = l_grid * 5 = 210`. The test is against the
    INTERIOR, which carries the 5mm border -- so 5U (215) clears it and 4U
    (173) does not."""
    b = SK(length_u, 3, 6)
    assert b.has_third_hinge is expected
    assert (0.0 in b.attachment_positions(hinge=True)) is expected


def test_third_hinge_is_hinges_only_and_can_be_turned_off():
    """It is one extra position at x=0, and only for hinges -- a latch never
    gets a third."""
    b = SK(5, 4, 6)
    assert 0.0 in b.attachment_positions(hinge=True)
    assert 0.0 not in b.attachment_positions(hinge=False)
    assert SK(5, 4, 6, third_hinge=False).has_third_hinge is False


def test_attachment_geometry_matches_upstream_arithmetic():
    b = SK(5, 4, 6)
    assert b.screw_eyelet_radius == pytest.approx(3.0 * 3.0 / 2)
    assert b.attachment_screw_offset == pytest.approx(
        b.total_lip_thickness + b.screw_eyelet_radius + 0.2
    )
    assert b.attachment_pair_offsets() == pytest.approx(
        [-(b.latch_width + b.rib_width) / 2, (b.latch_width + b.rib_width) / 2]
    )


def test_screw_holes_differ_between_the_two_halves():
    """The bottom is undersized so the screw cuts its own thread; the top is
    oversized so it turns freely. That difference is what makes a pair of
    eyelets a hinge instead of a seized joint."""
    import math

    b = SK(5, 4, 6)
    w = 12.0

    def diameter(shape):
        return 2 * math.sqrt(shape.val().Volume() / (2 * w * math.pi))

    assert diameter(b._screw_hole(w)) == pytest.approx(3.0 - 0.1, abs=0.01)
    assert diameter(b._screw_hole(w, oversize=True)) == pytest.approx(
        3.0 + 3.0 * 0.2, abs=0.01
    )


def test_half_eyelet_is_exactly_half():
    b = SK(5, 4, 6)
    full = b._screw_eyelet(12.0).val().Volume()
    half = b._screw_eyelet(12.0, half=True).val().Volume()
    assert half == pytest.approx(full / 2, rel=1e-6)


# --- Hinge ribs (1E.13) and end stops (1E.7) --------------------------------


def _assembled(b):
    """Body, and the lid placed on it at the joint."""
    return b.render_body().val(), b.render_lid().val().translate(
        (0, 0, b.body_height)
    )


@pytest.mark.slow
def test_the_assembled_halves_do_not_interfere():
    """The whole box in one number. Knuckles interleave along the pin, the
    seal ridge seats in its groove, and nothing collides.

    This caught a real error: hulling the hinge web against FULL eyelet
    circles (rather than the half-circles upstream uses, with the full eyelet
    unioned back) fills the wedge above the joint plane -- exactly where the
    other half's lip land sits. 973mm3 of interference, invisible to every
    other check.
    """
    body, lid = _assembled(_box())
    assert body.intersect(lid).Volume() == pytest.approx(0.0, abs=1e-6)


@pytest.mark.slow
def test_the_hinge_pin_passes_through_both_halves():
    """One M3 is the pivot, so both halves must be drilled on a common axis."""
    import cadquery as cq

    b = _box()
    body, lid = _assembled(b)
    pin = (
        cq.Workplane("XY")
        .circle(SK_M3 / 2 - 0.15)
        .extrude(400)
        .rotate((0, 0, 0), (0, 1, 0), 90)
        .translate(
            (-200, b.int_width / 2 + b.attachment_screw_offset, b.body_height)
        )
        .val()
    )
    assert body.intersect(pin).Volume() == pytest.approx(0.0, abs=1e-6)
    assert lid.intersect(pin).Volume() == pytest.approx(0.0, abs=1e-6)


def test_knuckles_interleave_along_the_pin():
    """The body takes the outer pair, the lid the middle. They must abut with
    clearance, not overlap: `hinge_size_tolerance` plus the inner offset."""
    b = _box()
    body_inner = abs(b.attachment_pair_offsets()[1] - b.rib_width / 2) - (
        b.hinge_rib_width / 2
    )
    lid_outer = b.top_hinge_width / 2
    assert body_inner > lid_outer, "knuckles overlap"
    assert body_inner - lid_outer == pytest.approx(
        b.size_tolerance + SK_HINGE_SIZE_TOL, abs=1e-9
    )


def test_third_hinge_becomes_real_geometry():
    """1E.6 stops being a rule here. A 5U box grows a centre knuckle; a 4U one
    does not, and the difference is material at x = 0 on the pin axis."""
    import cadquery as cq

    def centre_material(b):
        # Narrow in y so the probe sits outside the rear wall entirely and
        # can only ever find knuckle.
        probe = (
            cq.Workplane("XY")
            .box(10, 2, 20)
            .translate(
                (0, b.int_width / 2 + b.attachment_screw_offset, b.body_height)
            )
            .val()
        )
        return b.render_body().val().intersect(probe).Volume()

    assert SK(5, 3, 6).has_third_hinge
    assert not SK(4, 3, 6).has_third_hinge
    assert centre_material(SK(5, 3, 6)) > 20
    assert centre_material(SK(4, 3, 6)) == pytest.approx(0.0, abs=1e-6)


def test_end_stops_are_bottom_half_only_and_optional():
    """smkent adds them to the box bottom, never the lid: they are what the
    lid swings against."""
    b = _box()
    with_stops = b.render_hinge_ribs().val().Volume()
    without = SK(5, 4, 6, hinge_end_stops=False).render_hinge_ribs().val().Volume()
    assert with_stops > without, "end stops added no material"
    # The lid is unaffected either way.
    assert b.render_hinge_ribs(lid=True).val().Volume() == pytest.approx(
        SK(5, 4, 6, hinge_end_stops=False).render_hinge_ribs(lid=True).val().Volume()
    )


def test_hinge_knuckle_straddles_the_joint_plane():
    """A knuckle centred on the joint is what lets the halves pivot; it must
    stand proud by its eyelet radius on each side."""
    b = _box()
    bb = b.render_hinge_ribs().val().BoundingBox()
    assert bb.zmax == pytest.approx(
        b.body_height + b.screw_eyelet_radius, abs=0.05
    )


def test_both_halves_are_one_solid_with_every_attachment():
    b = SK(3, 2, 4)
    for shape in (b.render_body(), b.render_lid()):
        v = shape.val()
        assert v.isValid()
        assert len(v.Solids()) == 1
        assert len(v.Shells()) == 1, "a sealed pocket formed"


# --- Latch mounting ribs (1E.12) --------------------------------------------


def test_the_two_halves_screws_are_one_separation_apart():
    """The functional point of the whole assembly: measured from the joint,
    the lid's screw and the body's screw must be `latch_screw_separation`
    apart, because one latch spans both.

    smkent gets that by giving the lid `latch_amount_on_top` and the body the
    remainder -- `_latch_offset_from_base()`.
    """
    b = _box()
    from_joint_body = b.body_height - b.latch_offset_from_base()
    from_joint_lid = b.lid_height - b.latch_offset_from_base(lid=True)
    assert from_joint_body + from_joint_lid == pytest.approx(
        b.latch_screw_separation
    )
    assert from_joint_lid == pytest.approx(b.effective_latch_amount_on_top)


def test_latch_amount_on_top_is_auto_but_overridable():
    """0 means auto -- upstream `_init_latch_amount_on_top`. For the clip latch
    that is min(eyelet_r * 2, separation / 2), capped by the lid's own depth."""
    b = _box()
    assert b.latch_amount_on_top == 0
    assert b.effective_latch_amount_on_top == pytest.approx(
        min(b.screw_eyelet_radius * 2.0, b.latch_screw_separation / 2)
    )
    assert _box(latch_amount_on_top=5.0).effective_latch_amount_on_top == 5.0
    # The draw latch positions its screw differently.
    assert _box(latch_type="draw").effective_latch_amount_on_top != pytest.approx(
        b.effective_latch_amount_on_top
    )


def test_latch_ribs_come_in_pairs_at_every_attachment():
    """Two ribs straddle each latch, so a 2-latch box gets four."""
    b = _box()
    assert len(b.attachment_positions()) == 2
    assert len(b.render_latch_ribs().solids().vals()) == 4


def test_latch_boss_stands_proud_of_the_front_wall_only():
    b = _box()
    bb = b.render_latch_ribs().val().BoundingBox()
    reach = b.int_width / 2 + b.attachment_screw_offset + b.screw_eyelet_radius
    assert bb.ymin == pytest.approx(-reach, abs=0.05)
    assert bb.ymax < 0, "latch ribs belong on the front wall"


def test_latch_screw_hole_is_drilled_through_the_boss():
    """And to the right size for its half -- thread-forming in the body,
    clearance in the lid."""
    import cadquery as cq

    b = _box()
    pos = b.latch_offset_from_base()
    rib = b._latch_rib(b.body_height)
    # Probe along the screw axis: the boss must be hollow there.
    # Straddle the rib: this probe used to sit at y in [50, 150], nowhere near
    # the rib at y in [-3, 3], so it passed while the hole itself was also
    # missing the boss. Both bugs, one blind spot.
    probe = (
        cq.Workplane("XY")
        .circle(1.0)
        .extrude(40)
        .rotate((0, 0, 0), (1, 0, 0), -90)
        .translate((b.attachment_screw_offset, -20, pos))
    )
    assert probe.val().BoundingBox().ymin < -b.rib_width / 2, "probe misses the rib"
    assert probe.val().BoundingBox().ymax > b.rib_width / 2, "probe misses the rib"
    assert rib.val().intersect(probe.val()).Volume() == pytest.approx(0, abs=1e-6)


def test_latch_boss_is_trimmed_to_the_part_height():
    """smkent bounds it with a cube of exactly outer_height: a boss that
    overhangs the rim would foul the other half."""
    b = _box()
    for lid in (False, True):
        h = b.lid_height if lid else b.body_height
        bb = b._latch_rib(h, lid=lid).val().BoundingBox()
        assert bb.zmax <= h + 0.01
        assert bb.zmin >= -0.01


# --- Support ribs (1E.9) ----------------------------------------------------


def test_rib_positions_follow_the_gridfinity_wrapper():
    """One rib per grid unit along each side; rear ribs on INTERIOR grid lines
    only (`i = 1 .. Width-2`), because the rear corners are where the hinges
    go. Upstream's Width is our length_u, its Length our width_u."""
    b = SK(5, 4, 6)
    side, rear = b.rib_positions()
    assert side == pytest.approx([-63.0, -21.0, 21.0, 63.0])
    assert rear == pytest.approx([-42.0, 0.0, 42.0])


def test_ribs_stand_proud_of_the_plain_wall_and_flush_with_the_lip():
    """The rib IS the local thickening of a thin wall: it fills exactly the
    step between the plain wall and the lip land. If the wall never thinned,
    the rib would be buried inside the solid and this test could not tell the
    difference -- which is what happened before the shell rebuild."""
    import cadquery as cq

    b = SK(5, 4, 6, lip_seal_type="none")
    body = b.render_body().val()
    side, _ = b.rib_positions()
    z = 15.0  # plain-wall region, above the chamfer, below the ramp

    def x_extent_at(y):
        probe = cq.Workplane("XY").box(1000, 1.0, 0.4).translate((0, y, z)).val()
        return body.intersect(probe).BoundingBox().xlen

    on_rib = x_extent_at(side[1])
    between = x_extent_at((side[1] + side[2]) / 2)
    assert on_rib == pytest.approx(b.box_length, abs=0.05), "rib not flush with lip"
    assert between == pytest.approx(
        b.plain_outer_length, abs=0.05
    ), "wall not thin between ribs"
    assert on_rib - between == pytest.approx(2 * b.lip_thickness, abs=0.05)


def test_ribs_actually_add_material():
    """Guards the silent no-op: the rib set must show up in the body's volume."""
    b = SK(3, 2, 4, lip_seal_type="none")
    h = b.body_height
    bare = b._outer_block(h).cut(
        b._interior_void(h - b.wall_thickness, b.wall_thickness)
    )
    bare = bare.union(b.render_baseplate())
    full = b.render_body()
    gain = full.val().Volume() - bare.val().Volume()
    assert gain > 1000, "ribs added almost nothing (%.1f mm3)" % gain


def test_ribs_stop_below_the_rim():
    """smkent stops the rib `edge_radius * 1.5` short of the top."""
    b = SK(3, 2, 4)
    top = b.render_ribs().val().BoundingBox().zmax
    assert top == pytest.approx(b.body_height - b.edge_radius * 1.5, abs=0.01)


def test_body_and_lid_stay_one_solid_with_ribs():
    b = SK(3, 2, 4)
    for shape in (b.render_body(), b.render_lid()):
        assert shape.val().isValid()
        assert len(shape.val().Solids()) == 1
        assert len(shape.val().Shells()) == 1


# --- Integrated baseplate (1E.4) --------------------------------------------
#
# smkent exposes four named styles; the two axes underneath them are all that
# vary, so the API is two booleans (FEATURE-TRIAGE 1E.4). Upstream's fourth,
# "thick" -- a full slab with no magnet holes -- is deliberately unreachable.


def _small(**kw):
    """A 2x2x4 box: big enough for a real baseplate, cheap enough to render."""
    return SK(2, 2, 4, **kw)


def test_baseplate_footprint_is_the_bare_grid():
    """The plate is n*42 exactly; the border is what makes it fit."""
    bb = _small().render_baseplate().val().BoundingBox()
    assert bb.xlen == pytest.approx(2 * 42, abs=0.01)
    assert bb.ylen == pytest.approx(2 * 42, abs=0.01)


def test_baseplate_clears_the_cavity_by_half_the_border():
    b = _small()
    bb = b.render_baseplate().val().BoundingBox()
    assert (b.int_length - bb.xlen) / 2 == pytest.approx(SK_GF_BORDER / 2)
    assert (b.int_width - bb.ylen) / 2 == pytest.approx(SK_GF_BORDER / 2)


def test_baseplate_sits_on_the_interior_floor():
    """Bottom flush with the floor, top one base-profile above it."""
    from cqgridfinity.constants import GR_BASE_HEIGHT

    b = _small()
    bb = b.render_baseplate().val().BoundingBox()
    assert bb.zmin == pytest.approx(b.wall_thickness, abs=0.01)
    assert bb.zmax == pytest.approx(b.wall_thickness + GR_BASE_HEIGHT, abs=0.01)


def test_minimal_baseplate_costs_no_interior_height():
    """Upstream's default style: a thin plate with no slab under it."""
    b = _small()
    assert b.baseplate_extra_depth == 0
    assert b.int_height == pytest.approx(4 * 7 + b.bin_lip_clearance)


def test_magnet_baseplate_grows_the_interior_by_kenneteks_hole_depth():
    """smkent's gridfinity_base_extra_height() is a hardcoded h_hole = 2.4.

    We derive it from the plate we actually build; this is the cross-check
    that the derivation lands on upstream's number.
    """
    from cqgridfinity.constants import GR_HOLE_H

    b = _small(baseplate_magnets=True)
    assert b.baseplate_extra_depth == pytest.approx(GR_HOLE_H)
    assert b.int_height == pytest.approx(
        4 * 7 + b.bin_lip_clearance + GR_HOLE_H
    )
    # The extra depth lands in the body, not the lid -- upstream puts it in
    # bottom_height. A bin still gets its full 4U above the plate.
    assert b.lid_height == pytest.approx(_small().lid_height)
    assert b.body_height == pytest.approx(_small().body_height + GR_HOLE_H)


def test_baseplate_is_fused_into_the_body_not_merely_touching():
    """A coplanar union that fails to fuse leaves two solids that isValid()
    still passes -- the failure mode the seal ridge hit."""
    b = _small()
    r = b.render_body()
    assert r.val().isValid()
    assert len(r.solids().vals()) == 1
    assert len(r.val().Shells()) == 1, "a sealed internal void was created"


def test_baseplate_actually_adds_its_own_volume():
    """Guards 'parameters computed, geometry never built': the body must gain
    exactly the plate, with no overlap double-counted."""
    b = _small()
    h = b.body_height
    bare = b._outer_block(h).cut(
        b._interior_void(h - b.wall_thickness, b.wall_thickness)
    )
    bare = bare.union(b.render_ribs(h))
    bare = bare.union(b.render_latch_ribs(h))
    bare = bare.union(b.render_hinge_ribs(h))
    stack = b.render_stacking_latch_ribs(h)
    if stack is not None:
        bare = bare.union(stack)
    groove = b.render_seal_ring()
    if groove is not None:
        bare = bare.cut(groove)
    plate_vol = b.render_baseplate().val().Volume()
    assert plate_vol > 1000
    assert b.render_body().val().Volume() == pytest.approx(
        bare.val().Volume() + plate_vol, rel=1e-6
    )


def test_skeletonizing_removes_material_from_the_plate():
    """The whole point is weight off something you carry."""
    from cqgridfinity import GridfinityBaseplate

    skel = SK(2, 2, 4, baseplate_magnets=True, baseplate_skeletonized=True)
    solid = GridfinityBaseplate(
        2, 2, magnet_holes=True, ext_depth=skel.baseplate_extra_depth
    )
    lighter = skel.render_baseplate().val().Volume()
    assert lighter < solid.render().val().Volume() - 1000


def test_magnet_pockets_do_not_perforate_the_box_floor():
    """Magnet recesses are blind from above, so the box still holds liquid --
    and the magnets drop in from inside rather than needing a print pause."""
    for kw in ({}, {"baseplate_magnets": True}):
        b = _small(**kw)
        faces = b.render_body().faces("<Z").vals()
        assert len(faces) == 1, "the underside broke into pieces"
        # One wire means one boundary: no hole punched through from inside.
        assert len(faces[0].Wires()) == 1, "a pocket broke through the underside"
        # And the chamfer really pulls the base inside the wall footprint.
        assert faces[0].Area() < b.plain_outer_length * b.plain_outer_width


# --- Counts (the class of defect nothing was checking) ----------------------


def _hole_segments(shape, axis):
    """Distinct screw-hole segments running along `axis`.

    Identified by the two perpendicular coordinates of the axis line PLUS the
    segment's extent along it, so collinear holes in separate ribs count
    separately -- which is the whole point. All four latch holes share one
    axis line; only their extents tell them apart.
    """
    from OCP.BRepAdaptor import BRepAdaptor_Surface

    i = {"X": 0, "Y": 1, "Z": 2}[axis]
    out = set()
    for f in shape.Faces():
        s = BRepAdaptor_Surface(f.wrapped)
        if str(s.GetType()).rsplit("_", 1)[-1] != "Cylinder":
            continue
        c = s.Cylinder()
        if not (1.3 <= c.Radius() <= 1.9):
            continue
        d = c.Axis().Direction()
        if abs((d.X(), d.Y(), d.Z())[i]) < 0.9:
            continue
        loc = (c.Location().X(), c.Location().Y(), c.Location().Z())
        bb = f.BoundingBox()
        lo = (bb.xmin, bb.ymin, bb.zmin)[i]
        hi = (bb.xmax, bb.ymax, bb.zmax)[i]
        out.add(
            tuple(round(v, 1) for j, v in enumerate(loc) if j != i)
            + (round(lo, 1), round(hi, 1))
        )
    return out


@pytest.mark.slow
@pytest.mark.parametrize(
    "length_u,width_u,height_u", [(5, 4, 6), (3, 2, 4), (6, 4, 9)]
)
def test_every_attachment_gets_exactly_its_screws(length_u, width_u, height_u):
    """Defect 11 was a COUNT error -- the lid took the body's answer and came
    out with twice the stacking holes. Nothing here counted anything, so
    nothing caught it; a human did, by eye.

    Counts are derived from the rules, not recorded from the output.
    """
    b = SK(length_u, width_u, height_u)
    for lid in (False, True):
        shape = (b.render_lid() if lid else b.render_body()).val()
        along_x = _hole_segments(shape, "X")
        front = [h for h in along_x if h[0] < 0]  # latch wall
        rear = [h for h in along_x if h[0] > 0]  # hinge wall
        stacking = _hole_segments(shape, "Y")

        assert len(front) == 2 * len(b.attachment_positions()), "latch screws"

        # The body pierces its PAIR of knuckles at each hinge; the lid's
        # central block is one piece, so one segment. The end stop takes no
        # part -- it lives below the pin, which is what makes it a stop.
        per_hinge = 1 if lid else 2
        assert len(rear) == per_hinge * len(
            b.attachment_positions(hinge=True)
        ), "hinge screws"

        expected_stack = (
            2  # side walls
            * len(b.stacking_latch_positions())
            * 2  # ribs straddling each site
            * len(b.stacking_screw_heights(lid=lid))
        )
        assert len(stacking) == expected_stack, "stacking screws"


# --- Does it actually go together? ------------------------------------------


@pytest.mark.slow
def test_the_latch_fits_between_its_own_ribs():
    """Measured on BOTH sides of the interface: the gap the box leaves, and
    the part built to drop into it. Everything else about the latch was
    checked against upstream arithmetic; this is the first check that the two
    halves of the design agree with each other.
    """
    import cadquery as cq

    b = _box()
    body = b.render_body().val()
    px = b.attachment_positions()[1]
    # Probe outboard of the plain wall, where the ribs stand proud, and clear
    # of the screw axis -- which is drilled, so a probe there finds nothing.
    yy = -(b.int_width / 2 + b.wall_thickness + b.lip_thickness / 2)
    probe = cq.Workplane("XY").box(400, 1, 1).translate((0, yy, 15.0)).val()
    spans = sorted(
        (s.BoundingBox().xmin, s.BoundingBox().xmax)
        for s in body.intersect(probe).Solids()
    )
    near = [s for s in spans if abs((s[0] + s[1]) / 2 - px) < 40]
    assert len(near) == 2, "expected a rib either side of the latch"
    gap = near[1][0] - near[0][1]
    assert gap == pytest.approx(b.latch_width, abs=0.05)
    clearance = (gap - b.latch_part_width) / 2
    assert clearance == pytest.approx(b.size_tolerance, abs=0.02)
    assert clearance > 0, "the latch cannot drop into its own mount"


def test_latch_hole_spacing_matches_the_box_screws():
    """The part's two holes and the box's two screws must be the same
    distance apart, or the latch cannot span the joint."""
    from OCP.BRepAdaptor import BRepAdaptor_Surface

    b = _box()
    axes = set()
    for f in b.render_latch().val().Faces():
        s = BRepAdaptor_Surface(f.wrapped)
        if str(s.GetType()).rsplit("_", 1)[-1] == "Cylinder":
            c = s.Cylinder()
            if 1.35 <= c.Radius() <= 1.85:
                axes.add((round(c.Radius(), 3), round(c.Location().Y(), 3)))
    ys = sorted(y for _, y in axes)
    assert len(ys) == 2, "expected exactly a hinge hole and a catch hole"
    assert max(ys) - min(ys) == pytest.approx(b.latch_screw_separation, abs=0.01)
    # And they are drilled differently: running fit at the hinge, thread
    # forming at the catch.
    radii = {y: r for r, y in axes}
    assert radii[min(ys)] > radii[max(ys)]


# --- Stacking latches (1E.5) ------------------------------------------------


def test_stacking_latch_positions_pair_and_collapse():
    """smkent pairs each index with its mirror across the box and collapses
    the pair when they coincide: 2U gets one central latch, 6U gets three."""
    assert SK(5, 2, 6).stacking_latch_positions() == pytest.approx([0.0])
    assert SK(5, 4, 6).stacking_latch_positions() == pytest.approx([-42.0, 42.0])
    assert SK(5, 6, 6).stacking_latch_positions() == pytest.approx(
        [-84.0, 0.0, 84.0]
    )
    assert SK(5, 4, 6, stacking_latches=False).stacking_latch_positions() == []


def test_stack_catch_needs_a_tall_enough_box():
    """smkent `_stacking_latches_enabled()`: over two screw separations, or
    the two screw positions would collide. A short box still takes the mount,
    just not the second catch."""
    short, tall = SK(5, 4, 6), SK(5, 4, 9)
    assert short.body_height < 40 and not short.stacking_latches_enabled()
    assert tall.body_height > 40 and tall.stacking_latches_enabled()
    assert len(short.stacking_screw_heights()) == 1
    assert len(tall.stacking_screw_heights()) == 2


def test_stack_catch_is_decided_per_half_not_per_box():
    """Upstream reads `$b_outer_height` -- the CURRENT PART's height -- so the
    question is answered per half. A lid is never 40mm tall, so it always
    takes a single screw however tall the body is.

    Regression: this hardcoded `body_height` for both halves, so the lid of a
    tall box came out with twice the screw holes it should have. The tell was
    that `stacking_screw_heights()` accepted a `lid` argument it never used.
    Found by eye in CAD, not by any test here.
    """
    tall = SK(6, 4, 9)
    assert tall.body_height > 40 and tall.lid_height < 40
    assert tall.stacking_latches_enabled() is True
    assert tall.stacking_latches_enabled(lid=True) is False
    assert len(tall.stacking_screw_heights()) == 2
    assert len(tall.stacking_screw_heights(lid=True)) == 1
    # And that reaches the geometry: the lid gets half the side holes.
    sites = len(tall.stacking_latch_positions())
    body_holes = 2 * sites * 2 * len(tall.stacking_screw_heights())
    lid_holes = 2 * sites * 2 * len(tall.stacking_screw_heights(lid=True))
    assert (body_holes, lid_holes) == (16, 8)


def test_stacking_latch_is_a_clip_latch_with_a_second_catch():
    """Style x context: the mechanism is the clip latch's, mounted on the side
    and clamping box-to-box instead of lid-to-body. So it is longer, and it
    prints as one piece."""
    b = _box()
    stack = b.render_stacking_latch().val()
    assert stack.isValid()
    assert len(stack.Solids()) == 1
    assert stack.BoundingBox().zlen == pytest.approx(b.latch_part_width, abs=0.01)
    # Longer than the lid latch, because it reaches to a second catch.
    assert stack.BoundingBox().ylen > b.render_latch().val().BoundingBox().ylen


def test_stacking_ribs_land_on_both_side_walls():
    b = _box()
    bb = b.render_stacking_latch_ribs().val().BoundingBox()
    reach = b.int_length / 2 + b.attachment_screw_offset + b.screw_eyelet_radius
    assert bb.xmin == pytest.approx(-reach, abs=0.05)
    assert bb.xmax == pytest.approx(reach, abs=0.05)


def test_stacking_latches_can_be_turned_off():
    b = SK(3, 2, 4, stacking_latches=False)
    assert b.render_stacking_latch_ribs() is None
    assert "stacking_latch" not in b.parts()
    assert b.render_body().val().Volume() < SK(3, 2, 4).render_body().val().Volume()


# --- Per-part output and BOM ------------------------------------------------


def test_parts_covers_everything_you_have_to_print():
    """A rugged box is not one model. Rendering only `render()` gives you the
    body and nothing to close it with."""
    clip = SK(3, 2, 4)
    assert set(clip.parts()) == {"body", "lid", "latch", "stacking_latch"}
    assert set(SK(3, 2, 4, stacking_latches=False).parts()) == {
        "body",
        "lid",
        "latch",
    }
    draw = SK(3, 2, 4, latch_type="draw", stacking_latches=False)
    assert set(draw.parts()) == {"body", "lid", "latch_handle", "latch_catch"}
    for shape in draw.parts().values():
        assert shape.val().isValid()
        assert len(shape.val().Solids()) == 1, "every part prints as one piece"


def test_save_step_parts_writes_a_file_each(tmp_path):
    b = SK(3, 2, 4)
    paths = b.save_step_parts(path=str(tmp_path))
    assert len(paths) == len(b.parts())
    for p in paths:
        assert p.endswith(".step")
        assert os.path.getsize(p) > 1000


def test_bom_counts_a_screw_for_every_attachment():
    """P3 exit criterion. Every attachment is an M3 through a pair of eyelets,
    and the third hinge adds one more when it activates."""
    wide, narrow = SK(5, 4, 6), SK(4, 4, 6)
    assert wide.bom()["M3x40 DIN 912 (hinge)"] == 3
    assert narrow.bom()["M3x40 DIN 912 (hinge)"] == 2
    assert wide.bom()["M3x40 DIN 912 (latch)"] == 2
    assert SK(2, 2, 4).bom()["M3x40 DIN 912 (latch)"] == 1


# --- Naming -----------------------------------------------------------------


def test_filename_records_the_baseplate_style():
    assert "bp-mag" in SK(2, 2, 4, baseplate_magnets=True).filename()
    assert "bp-mag-skel" in SK(
        2, 2, 4, baseplate_magnets=True, baseplate_skeletonized=True
    ).filename()


def test_filename_distinguishes_from_pred_box():
    assert _box().filename() == "gf_ruggedbox_sk_5x4x6_clip"


def test_filename_records_non_default_tolerance():
    assert "tol0.05" in SK(5, 4, 6, size_tolerance=0.05).filename()
