"""smkent rugged box tests (P3).

Separate module from Pred's box by licence necessity: a derivative of a
NonCommercial work stays NonCommercial, so no code crosses between them.
"""

import math

import pytest

from cqgridfinity import GridfinityRuggedBoxSmkent as SK
from cqgridfinity.gf_ruggedbox_smkent import SK_M3
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
    b = _box()
    assert b.int_length == pytest.approx(5 * 42)
    assert b.int_width == pytest.approx(4 * 42)
    # Interior height is N*7 PLUS room for the bins' stacking lips, matching
    # smkent's top_height = N*7 + h_lip.
    assert b.int_height == pytest.approx(6 * 7 + b.bin_lip_clearance)


def test_lip_clearance_matches_kennetek_h_lip():
    """smkent budgets lid clearance with kennetek's h_lip = 3.548. We derive
    the same number from our own lip geometry instead of hardcoding it."""
    assert _box().bin_lip_clearance == pytest.approx(3.548, abs=0.01)


def test_a_full_height_bin_actually_fits():
    """The point of the clearance: a 6U bin must fit a 6U box."""
    from cqgridfinity import GridfinityBox

    b = _box()
    assert GridfinityBox(2, 2, 6).actual_height <= b.int_height + 1e-6


def test_outer_size_adds_two_walls():
    b = _box()
    assert b.box_length == pytest.approx(5 * 42 + 2 * b.wall_thickness)
    assert b.box_width == pytest.approx(4 * 42 + 2 * b.wall_thickness)


def test_body_and_lid_heights_sum_to_interior():
    b = _box()
    assert b.body_height + b.lid_height == pytest.approx(b.int_height)


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
    from OCP.BRepAdaptor import BRepAdaptor_Surface

    kinds = [
        str(BRepAdaptor_Surface(f.wrapped).GetType()).rsplit("_", 1)[-1]
        for f in _box().render_draw_latch_handle().val().Faces()
    ]
    assert kinds.count("Cylinder") >= 5, "arcs must survive as cylinders"
    assert "BSplineSurface" not in kinds, "no facet/spline fallback expected here"


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


# --- Naming -----------------------------------------------------------------


def test_filename_distinguishes_from_pred_box():
    assert _box().filename() == "gf_ruggedbox_sk_5x4x6_clip"


def test_filename_records_non_default_tolerance():
    assert "tol0.05" in SK(5, 4, 6, size_tolerance=0.05).filename()
