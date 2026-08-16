"""smkent rugged box tests (P3).

Separate module from Pred's box by licence necessity: a derivative of a
NonCommercial work stays NonCommercial, so no code crosses between them.
"""

import math

import pytest

from cqgridfinity import GridfinityRuggedBoxSmkent as SK
from cqgridfinity.gf_ruggedbox_smkent import SK_GF_BORDER, SK_M3
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
    b = _box()
    bb = b.render_body().val().BoundingBox()
    assert bb.xlen == pytest.approx(b.box_length, abs=0.01)
    assert bb.ylen == pytest.approx(b.box_width, abs=0.01)
    assert bb.zlen == pytest.approx(b.body_height, abs=0.01)


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


def _wall_at(solid, z):
    """Wall thickness at height z, or None if there is no ring there."""
    import cadquery as _cq

    plate = _cq.Workplane("XY").rect(500, 500).extrude(0.02).translate((0, 0, z))
    rings = [f for f in solid.intersect(plate.val()).Faces() if len(f.Wires()) == 2]
    if not rings:
        return None
    f = max(rings, key=lambda x: x.BoundingBox().xlen)
    inner = sorted(f.Wires(), key=lambda w: w.BoundingBox().xlen)[0]
    return (f.BoundingBox().xlen - inner.BoundingBox().xlen) / 2


def _extents_at(solid, z):
    """(outer, inner) X extents of the ring at height z."""
    import cadquery as _cq

    plate = _cq.Workplane("XY").rect(500, 500).extrude(0.02).translate((0, 0, z))
    rings = [f for f in solid.intersect(plate.val()).Faces() if len(f.Wires()) == 2]
    assert rings, "no ring at z=%s" % z
    f = max(rings, key=lambda x: x.BoundingBox().xlen)
    inner = sorted(f.Wires(), key=lambda w: w.BoundingBox().xlen)[0]
    return f.BoundingBox().xlen, inner.BoundingBox().xlen


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
    outer_low, inner_low = _extents_at(body, 8.0)
    outer_high, inner_high = _extents_at(body, b.body_height - 1.0)

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
        """Below the floor the section is solid, so measure the slice itself."""
        slab = cq.Workplane("XY").box(500, 500, 0.02).translate((0, 0, z)).val()
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
    h = body.BoundingBox().zlen
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
    for width in (22.0, 28.0, 34.0):
        bb = _box(latch_width=width).render_latch().val().BoundingBox()
        assert bb.zlen == pytest.approx(width, abs=0.01)


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


def test_draw_latch_not_yet_implemented():
    """Explicit rather than silently producing a clip latch."""
    with pytest.raises(NotImplementedError, match="draw latch"):
        _box(latch_type="draw").render_latch()


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
    expected = (_m.pi * t * t + 2 * t * span) * b.latch_width
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
    r = b._draw_latch_hook_solid(b.latch_width)
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
    bb = b._draw_latch_hook_solid(b.latch_width).val().BoundingBox()
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
    h = b.latch_width
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
        for f in b._draw_latch_hook_solid(b.latch_width).val().Faces()
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
    assert bb.zlen == pytest.approx(b.latch_width, abs=0.01)


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
    ).extrude(b.latch_width).val().Volume()
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
        (pin_a + screw_a) * b.latch_width, rel=1e-6
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
    h = b.latch_width
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
    h = b.latch_width
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
    lw = b.latch_width
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
    assert bb.zlen == pytest.approx(b.latch_width, abs=0.01)


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
    seg = b.latch_width / 5
    assert catch[0] == pytest.approx((seg, 2 * seg))
    for (c0, c1), (h0, h1) in zip(catch, handle):
        assert h0 == pytest.approx(c0 - SK_DRAW_VSEP)
        assert h1 == pytest.approx(c1 + SK_DRAW_VSEP)


def test_catch_segments_into_separate_fingers():
    cs = _box().render_draw_latch_catch_segmented().val()
    assert cs.isValid()
    assert len(cs.Solids()) == 2, "catch should reduce to two fingers"


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
    areas = []
    for kw in ({}, {"baseplate_magnets": True}):
        b = _small(**kw)
        faces = b.render_body().faces("<Z").vals()
        assert len(faces) == 1, "the underside broke into pieces"
        areas.append(faces[0].Area())
    # Differential: turning magnets on must not change the underside at all.
    assert areas[0] == pytest.approx(areas[1], rel=1e-9), "magnets broke through"
    # And the underside is the chamfered footprint, not the full one.
    b = _small()
    hc = b.outer_chamfer_horizontal
    assert areas[0] == pytest.approx(
        (b.plain_outer_length - 2 * hc) * (b.plain_outer_width - 2 * hc), rel=0.02
    )


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
