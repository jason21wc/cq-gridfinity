"""smkent rugged box tests (P3).

Separate module from Pred's box by licence necessity: a derivative of a
NonCommercial work stays NonCommercial, so no code crosses between them.
"""

import math

import pytest

from cqgridfinity import GridfinityRuggedBoxSmkent as SK
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
    assert b.int_height == pytest.approx(6 * 7)


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


# --- Naming -----------------------------------------------------------------


def test_filename_distinguishes_from_pred_box():
    assert _box().filename() == "gf_ruggedbox_sk_5x4x6_clip"


def test_filename_records_non_default_tolerance():
    assert "tol0.05" in SK(5, 4, 6, size_tolerance=0.05).filename()
