#! /usr/bin/env python3
#
# Copyright (C) 2026  Jason Collier
#
# Independent CadQuery implementation of the smkent rugged box design.
# Original design: smkent (https://github.com/smkent/monoscad), rugged-box.
#
# This module is licensed under Creative Commons Attribution-ShareAlike 4.0
# International (CC BY-SA 4.0), matching its upstream design source.
# https://creativecommons.org/licenses/by-sa/4.0/
#
# NOTE: this is deliberately a SEPARATE module from gf_ruggedbox.py, which
# implements Pred's design under CC BY-NC-SA 4.0. A derivative of a
# NonCommercial work stays NonCommercial, so no code may cross between them.
#
# smkent Rugged Box

"""Rugged box, smkent variant.

Distinct from `gf_ruggedbox.py` (Pred's design) in three ways that matter:

1. **License.** CC BY-SA rather than CC BY-NC-SA, so commercial use is allowed.
2. **Sealing.** A lip seal groove, including one sized for a loop of 1.75mm
   filament as gasket stock.
3. **Parametric walls.** Seven dimensions exposed rather than baked in, with
   `size_tolerance` as the single knob for dialling in fit on a given printer.

Everything prints without support, which is a design constraint upstream rather
than a happy accident.
"""

import math
import warnings

import cadquery as cq
from cqkit.cq_helpers import rounded_rect_sketch

from cqgridfinity.constants import (
    EPS,
    GRU,
    GRHU,
    GR_LIP_APEX_SETBACK,
    GR_STACKING_LIP_H,
)
from cqgridfinity.gf_obj import GridfinityObject

__all__ = ["GridfinityRuggedBoxSmkent"]

# smkent rbox_size_adjustments() -- Gridfinity presets, not the generic ones.
SK_WALL_TH = 3.0  # base wall thickness
SK_LIP_TH = 3.0  # additional thickness through the lip region
SK_RIB_WIDTH = 6.0  # support rib base width
SK_LATCH_WIDTH = 28.0  # latch side-to-side
SK_LATCH_SCREW_SEP = 16.0  # screw-to-screw within a latch
SK_SIZE_TOL = 0.20  # fit tolerance (0.05 generic / 0.20 gridfinity)

SK_M3 = 3.0  # screw diameter
SK_LATCH_BODY_PROPORTION = 3.0  # latch body size relative to screw diameter
SK_LATCH_EDGE_RADIUS = 0.8
SK_SCREW_HOLE_TOL = -0.1  # undersize so the screw forms its own thread

# -- Draw latch (1E.2) ---------------------------------------------------
# Two-piece over-center toggle: a handle and a catch joined by a pin. Unlike
# the clip latch it actively CLAMPS the lid, which is why the lip seal depends
# on it -- a seal only seals under compression.
# Values from smkent rugged-box-library.scad "Internal constants".
SK_DRAW_THICKNESS = SK_M3 * (SK_LATCH_BODY_PROPORTION / 2) / 2  # latch_base_size/2
SK_DRAW_HANDLE_LENGTH = SK_M3 * (SK_LATCH_BODY_PROPORTION / 2) * 3.25
SK_DRAW_SCREW_EYELET_R = SK_M3 * 1.1
SK_DRAW_PIN_HANDLE_R = SK_M3 * 1.6
SK_DRAW_PIN_R = SK_DRAW_PIN_HANDLE_R - 2.2
SK_DRAW_SEP = 0.4  # clearance between the two pieces
SK_DRAW_VSEP = 0.6  # vertical separation between interlocking segments
SK_DRAW_BODY_ANGLE = 25
SK_DRAW_BODY_CURVE_R = 10
SK_DRAW_GRIP_ANGLE = 45
SK_DRAW_GRIP_CURVE_R = 16
SK_DRAW_SEGMENTS = 5  # alternating interlocking bands across the latch width


def _tangent_point(radius, point, prefer_right=True):
    """Where a line from `point` touches a circle of `radius` at the origin.

    OpenSCAD's hull() of a circle and a distant point is bounded by this
    tangent. Computing it exactly keeps the arc analytic instead of degrading
    the circle into a polygon, which would show up as planar facets in the
    exported STEP.
    """
    px, py = point
    d = math.hypot(px, py)
    if d <= radius:
        raise ValueError(
            "Tangent undefined: point %r lies inside the circle (r=%.3f)"
            % (point, radius)
        )
    theta = math.atan2(py, px)
    alpha = math.acos(radius / d)
    ang = theta - alpha if prefer_right else theta + alpha
    return radius * math.cos(ang), radius * math.sin(ang)


def _hull_of_circles(circles):
    """Exact 2D convex hull of circles, as a list of (kind, ...) wire segments.

    OpenSCAD leans on hull() constantly; CadQuery has none. For circles of
    EQUAL radius the hull is just `polygon(centres).offset2D(r)`, which the clip
    latch uses. The draw latch hulls circles of DIFFERENT radii, where that
    shortcut does not apply.

    The true boundary alternates arcs and external tangent lines. For two
    circles at distance d, the outward normal n satisfies n . u = (r1 - r2) / d
    with u the unit vector between centres, so the tangent points are
    c1 + r1*n and c2 + r2*n. Computing them keeps the arcs analytic instead of
    faceting the circles into polygons -- the degradation this project exists
    to avoid.

    Returns [("arc", centre, radius, start_ang, end_ang) |
             ("line", p0, p1)] in counter-clockwise order.
    """
    pts = [(c[0], c[1]) for c in circles]
    # Order by the hull of the centres. Adequate here: no circle in these
    # shapes swallows another, which is the case that would break it.
    hull = _convex_hull_2d(pts)
    if len(hull) < 2:
        raise ValueError("need at least two distinct circles")
    idx = [pts.index(h) for h in hull]
    segs, tangents = [], []
    for i in range(len(idx)):
        a, b = circles[idx[i]], circles[idx[(i + 1) % len(idx)]]
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        if d <= abs(a[2] - b[2]) or d == 0:
            raise ValueError("one circle contains another; hull undefined here")
        ux, uy = (b[0] - a[0]) / d, (b[1] - a[1]) / d
        phi = math.acos(max(-1.0, min(1.0, (a[2] - b[2]) / d)))
        # Rotate u by -phi for the outward (counter-clockwise) normal.
        nx = ux * math.cos(-phi) - uy * math.sin(-phi)
        ny = ux * math.sin(-phi) + uy * math.cos(-phi)
        tangents.append((
            (a[0] + a[2] * nx, a[1] + a[2] * ny),
            (b[0] + b[2] * nx, b[1] + b[2] * ny),
            math.atan2(ny, nx),
        ))
    for i in range(len(idx)):
        c = circles[idx[i]]
        prev_ang = tangents[i - 1][2]
        this_ang = tangents[i][2]
        segs.append(("arc", (c[0], c[1]), c[2], prev_ang, this_ang))
        segs.append(("line", tangents[i][0], tangents[i][1]))
    return segs


def _convex_hull_2d(points):
    """Monotone chain hull. Plain geometry, no CAD kernel involved."""
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def _wire_from_hull(segs):
    """Build a closed CadQuery wire from _hull_of_circles output."""
    wp = cq.Workplane("XY")
    start = None
    for kind, *rest in segs:
        if kind == "line":
            p0, p1 = rest
            if start is None:
                wp = wp.moveTo(*p0)
                start = p0
            wp = wp.lineTo(*p1)
        else:
            centre, radius, a0, a1 = rest
            while a1 < a0:
                a1 += 2 * math.pi
            mid = (a0 + a1) / 2
            pm = (centre[0] + radius * math.cos(mid),
                  centre[1] + radius * math.sin(mid))
            pe = (centre[0] + radius * math.cos(a1),
                  centre[1] + radius * math.sin(a1))
            if start is None:
                p0 = (centre[0] + radius * math.cos(a0),
                      centre[1] + radius * math.sin(a0))
                wp = wp.moveTo(*p0)
                start = p0
            wp = wp.threePointArc(pm, pe)
    return wp.close()


class GridfinityRuggedBoxSmkent(GridfinityObject):
    """Rugged box (smkent design) sized in Gridfinity units.

    length_u x width_u is the Gridfinity footprint the interior must hold;
    height_u is in 7mm Gridfinity height units.

    The seven wall parameters from upstream `rbox_size_adjustments()` are
    exposed directly. `size_tolerance` is the one to reach for when latches or
    hinges do not fit on your printer -- it is why the ecosystem's 1mm UI
    increments are useless, since real corrections live at 0.05-0.2mm.
    """

    def __init__(self, length_u, width_u, height_u, **kwargs):
        super().__init__()
        self.length_u = length_u
        self.width_u = width_u
        self.height_u = height_u
        # -- parametric walls (1E.8) --------------------------------------
        self.wall_thickness = SK_WALL_TH
        self.lip_thickness = SK_LIP_TH
        self.rib_width = SK_RIB_WIDTH
        self.latch_width = SK_LATCH_WIDTH
        self.latch_screw_separation = SK_LATCH_SCREW_SEP
        self.latch_amount_on_top = 0  # 0 = auto
        self.size_tolerance = SK_SIZE_TOL
        # -- assembly -----------------------------------------------------
        self.lid_height_u = 1  # lid depth in Gridfinity height units
        self.latch_type = "clip"  # "clip" | "draw"
        for k, v in kwargs.items():
            if k in self.__dict__:
                self.__dict__[k] = v
            else:
                raise ValueError(
                    "%s: unknown keyword argument %r"
                    % (self.__class__.__name__, k)
                )
        self._validate()

    def _validate(self):
        if self.length_u < 1 or self.width_u < 1:
            raise ValueError("length_u and width_u must be >= 1")
        if self.height_u < 2:
            raise ValueError(
                "height_u must be >= 2 (a box shallower than its own lid "
                "cannot close), got %r" % (self.height_u,)
            )
        for name in ("wall_thickness", "lip_thickness"):
            v = getattr(self, name)
            if not 0.4 <= v <= 10:
                raise ValueError("%s must be 0.4-10 mm, got %r" % (name, v))
        if not 1 <= self.rib_width <= 20:
            raise ValueError("rib_width must be 1-20 mm, got %r" % (self.rib_width,))
        if not 5 <= self.latch_width <= 50:
            raise ValueError(
                "latch_width must be 5-50 mm, got %r" % (self.latch_width,)
            )
        if not 5 <= self.latch_screw_separation <= 40:
            raise ValueError(
                "latch_screw_separation must be 5-40 mm, got %r"
                % (self.latch_screw_separation,)
            )
        if not 0 <= self.size_tolerance <= 1:
            raise ValueError(
                "size_tolerance must be 0-1 mm, got %r" % (self.size_tolerance,)
            )
        if self.latch_type not in ("clip", "draw"):
            raise ValueError(
                "latch_type must be 'clip' or 'draw', got %r" % (self.latch_type,)
            )

    # -- derived dimensions ----------------------------------------------

    @property
    def total_lip_thickness(self):
        """Wall thickness through the lip region. smkent $b_total_lip_thickness."""
        return self.wall_thickness + self.lip_thickness

    @property
    def lip_height(self):
        """smkent $b_lip_height."""
        return self.lip_thickness * 2

    @property
    def edge_radius(self):
        """smkent $b_edge_radius."""
        return self.wall_thickness / 5

    @property
    def int_length(self):
        """Interior length: the Gridfinity footprint it must hold."""
        return self.length_u * GRU

    @property
    def int_width(self):
        return self.width_u * GRU

    @property
    def int_height(self):
        """Interior height, including room for the bins' stacking lips.

        smkent computes lid clearance as
            top_height = Top_Height * gridfinity_height_increment + h_lip
        i.e. N*7 plus the ACTUAL (post-fillet) lip height, taken from
        kennetek's h_lip = 3.548. We derive the same quantity from our own
        geometry rather than hardcoding it, so it stays correct if the lip
        fillet is ever retuned. The two agree to 0.0035mm -- see
        tests/test_spec_conformance.py.
        """
        return self.height_u * GRHU + self.bin_lip_clearance

    @property
    def bin_lip_clearance(self):
        """Extra headroom a stacked bin's lip needs, above N*7."""
        return GR_STACKING_LIP_H - GR_LIP_APEX_SETBACK

    @property
    def box_length(self):
        return self.int_length + 2 * self.wall_thickness

    @property
    def box_width(self):
        return self.int_width + 2 * self.wall_thickness

    @property
    def lid_height(self):
        return self.lid_height_u * GRHU

    @property
    def body_height(self):
        """Height of the lower (box) half, excluding the lid."""
        return self.int_height - self.lid_height

    @property
    def corner_radius(self):
        """Outer corner radius. Gridfinity's own 3.75mm plus the wall."""
        return 3.75 + self.wall_thickness

    @property
    def latch_base_size(self):
        """smkent latch_base_size = screw_diameter * (proportion / 2)."""
        return SK_M3 * (SK_LATCH_BODY_PROPORTION / 2)

    # -- geometry ---------------------------------------------------------

    def _outer_block(self, height, z0=0.0):
        """Rounded-rectangle prism forming the outer surface."""
        sketch = rounded_rect_sketch(
            self.box_length, self.box_width, self.corner_radius
        )
        return (
            cq.Workplane("XY").placeSketch(sketch).extrude(height).translate((0, 0, z0))
        )

    def _interior_void(self, height, z0):
        """The cavity that holds Gridfinity bins."""
        sketch = rounded_rect_sketch(self.int_length, self.int_width, 3.75)
        return (
            cq.Workplane("XY").placeSketch(sketch).extrude(height).translate((0, 0, z0))
        )

    def render_body(self):
        """Lower half of the box: floor, walls, and the lip's lower land."""
        h = self.body_height
        r = self._outer_block(h)
        void = self._interior_void(h, self.wall_thickness)
        r = r.cut(void)
        self._cq_obj = r
        self._obj_label = "body"
        return r

    def render_lid(self):
        """Upper half. Rendered at the origin, not in assembled position."""
        h = self.lid_height
        r = self._outer_block(h)
        void = self._interior_void(h - self.wall_thickness, 0)
        r = r.cut(void)
        self._cq_obj = r
        self._obj_label = "lid"
        return r

    # -- clip latch (1E.1) -------------------------------------------------
    #
    # Translated from smkent _clip_latch_shape(). OpenSCAD builds it with
    # hull(); CadQuery has no hull, and a polygon approximation would replace
    # analytic arcs with dozens of planar facets -- the exact degradation this
    # project exists to avoid. Both hulls are therefore constructed exactly:
    #   - hull of N equal circles  -> polygon through centres, offset2D(r)
    #   - hull of a circle + a point -> arc, plus the true tangent line
    # See LEARNING-LOG for the tangent derivation.

    @property
    def _screw_hole_d(self):
        """shd: nominal M3 minus a thread-forming interference fit."""
        return SK_M3 + SK_SCREW_HOLE_TOL

    @property
    def latch_body_width(self):
        """smkent bw = latch_base_size - screw_hole_diameter / 2."""
        return self.latch_base_size - SK_M3 / 2

    def _clip_latch_solid(self, height):
        """The clip latch as a solid, extruded `height` across its width.

        Built by extruding each piece and booleaning the solids -- CadQuery's
        union() operates on solids, not 2D wires.

        x runs across the latch, y from the hinge eyelet up past the catch.
        """
        r = self.latch_base_size
        bw = self.latch_body_width
        sep = self.latch_screw_separation

        # -- outer shape ---------------------------------------------------
        hinge = cq.Workplane("XY").circle(r).extrude(height)
        catch = cq.Workplane("XY").center(0, sep).circle(r).extrude(height)
        # Full-height spine: square([bw, sep + latch_base_size * 2.5]) at (-r, 0)
        spine_h = sep + r * 2.5
        spine = (
            cq.Workplane("XY")
            .center(-r + bw / 2, spine_h / 2)
            .rect(bw, spine_h)
            .extrude(height)
        )
        # hull(hinge circle, spine rect): the circle and spine already cover
        # everything but the wedge between the circle's right flank and the
        # spine's top corner. Bound that by the exact tangent line, so the
        # arc stays an arc.
        corner = (-r + bw, sep)
        tx, ty = _tangent_point(r, corner)
        wedge = (
            cq.Workplane("XY")
            .polyline([(-r + bw, 0.0), (tx, ty), corner])
            .close()
            .extrude(height)
        )
        solid = hinge.union(catch).union(spine).union(wedge)

        # -- holes ---------------------------------------------------------
        shd = self._screw_hole_d
        # Hinge hole is a running fit, so it gets the extra clearance.
        hinge_hole = (
            cq.Workplane("XY").circle((shd + SK_M3 * 0.2) / 2).extrude(height)
        )
        # Catch hole: hull of three equal circles == polygon through their
        # centres offset outward by the radius. Exact, and keeps real arcs.
        catch_hole = (
            cq.Workplane("XY")
            .polyline(
                [
                    (0.0, sep),
                    (r + bw / 1.6, 0.0),
                    ((shd + bw) * 2, sep - shd),
                ]
            )
            .close()
            .offset2D(shd / 2)
            .extrude(height)
        )
        return solid.cut(hinge_hole).cut(catch_hole)

    def _break_extruded_edges(self, obj, radius=SK_LATCH_EDGE_RADIUS):
        """Break the sharp edges at both ends of an extrusion.

        DEVIATION FROM UPSTREAM, stated deliberately rather than silently.

        smkent breaks these edges with `_chamfer_edges()`, a minkowski against
        a double cone -- a true 45 degree chamfer, despite the parameter being
        named `latch_edge_radius`. OpenCASCADE refuses to chamfer this edge
        loop at any size (`BRep_API: command not done`, tested at 0.8, 0.4 and
        0.2mm, and on each end separately). It accepts a fillet of the same
        size without complaint.

        A fillet and a 45 degree chamfer serve the same purpose here -- taking
        the sharpness off a printed edge -- so we fillet and say so. The
        alternative was leaving the edges sharp, or wrapping the chamfer in a
        try/except that quietly did nothing, which is how the divider roof bug
        hid (see LEARNING-LOG).

        Returns the object unchanged if even the fillet fails, but never
        pretends to have applied one.
        """
        for selector in (">Z", "<Z"):
            try:
                obj = obj.faces(selector).edges().fillet(radius)
            except Exception:
                # Recorded, not hidden: the caller's geometry is still valid,
                # it simply keeps a sharp edge at that end.
                warnings.warn(
                    "%s: could not break edges on the %s face; that end stays "
                    "sharp. Geometry is otherwise valid."
                    % (self.__class__.__name__, selector),
                    stacklevel=2,
                )
        return obj

    # -- draw latch (1E.2) ------------------------------------------------

    @property
    def _draw_pin_offset(self):
        """Pin joint centre, relative to the handle origin."""
        return (
            SK_DRAW_SCREW_EYELET_R - SK_DRAW_PIN_HANDLE_R - SK_M3 * 0.1,
            -SK_DRAW_HANDLE_LENGTH,
        )

    def _draw_latch_catch_body_circles(self):
        """The catch body is a hull of two equal circles -- a stadium.

        smkent:
            translate([eyelet_r + thickness + sep, 0])
            hull() { circle(thickness) at y = -handle_length + offset - delta;
                     circle(thickness) at y = -base_size + screw_d/2 + sep; }
        """
        t = SK_DRAW_THICKNESS
        pin_diameter = SK_DRAW_PIN_R - SK_DRAW_SEP / 2
        offset_from_pin = SK_DRAW_SEP + t + SK_DRAW_PIN_HANDLE_R
        size_delta = pin_diameter - t
        x = SK_DRAW_SCREW_EYELET_R + t + SK_DRAW_SEP
        y_lo = -SK_DRAW_HANDLE_LENGTH + offset_from_pin - size_delta
        y_hi = -self.latch_base_size + SK_M3 / 2 + self.latch_screw_separation
        return [(x, y_lo, t), (x, y_hi, t)]

    def _quadrant(self, shape, h, xs, ys):
        """Keep one quadrant of a 2D shape by intersecting with a half-space box.

        OpenSCAD writes `intersection() { circle(r); square(r); }` to take a
        quarter disc. Intersecting a full circle/ellipse with a box does the
        same thing here and, importantly, leaves the arc analytic -- building
        the quarter from sampled points would facet it.
        """
        big = 1000.0
        box = (
            cq.Workplane("XY")
            .box(big, big, h * 3)
            .translate((xs * big / 2, ys * big / 2, h / 2))
        )
        return shape.intersect(box)

    def _draw_latch_hook_solid(self, h):
        """The hook: the claw that swallows the lid's keeper bar.

        Translated from smkent _draw_latch_catch_shape_hook(). The claw is
        built up from a quarter disc (its spine), a shank and curl that wrap
        under the keeper, and a thumb nub; then the THROAT is cut out.

        The throat is cut with two **elliptical** quarters, not circular ones:
        smkent scales the quarter disc by (1 + cr) on one side and (1 - cr) on
        the other, which makes the mouth asymmetric -- wider where the keeper
        enters, tighter where it is retained. Approximating those with circles
        would give a latch that either will not close or will not hold, so the
        scale factors are carried through exactly.
        """
        outr = SK_DRAW_SCREW_EYELET_R + SK_DRAW_THICKNESS * 2  # 7.8
        compress = 0.65
        cr = compress * 0.8  # 0.52

        # -- spine: quarter disc, first quadrant ---------------------------
        spine = self._quadrant(
            cq.Workplane("XY").circle(outr).extrude(h), h, +1, +1
        )
        # -- shank: rectangle, mirrored to -x ------------------------------
        shank_w, shank_h = outr * compress, outr * (1 - compress - 0.1)
        shank = (
            cq.Workplane("XY")
            .rect(shank_w, shank_h)
            .extrude(h)
            .translate((-shank_w / 2, outr * 0.2 + shank_h / 2, 0))
        )
        # -- curl: quarter disc r = outr*compress, mirrored to -x ----------
        curl = self._quadrant(
            cq.Workplane("XY").circle(outr * compress).extrude(h), h, -1, +1
        ).translate((0, outr * (1 - compress), 0))
        # -- thumb nub ------------------------------------------------------
        nub = (
            cq.Workplane("XY")
            .circle(SK_DRAW_THICKNESS * 1.5 / 2)
            .extrude(h)
            .translate((outr / 1.5, outr / 1.5, 0))
        )
        claw = spine.union(shank).union(curl).union(nub)

        # -- throat: two elliptical quarters, asymmetric --------------------
        er = SK_DRAW_SCREW_EYELET_R
        wide = self._quadrant(
            cq.Workplane("XY").ellipse(er * (1 + cr), er).extrude(h), h, +1, +1
        )
        tight = self._quadrant(
            cq.Workplane("XY").ellipse(er * (1 - cr), er).extrude(h), h, -1, +1
        )
        throat = wide.union(tight).translate((-er * cr, 0, 0))
        return claw.cut(throat)

    def render_draw_latch_catch(self):
        """Catch = stadium body + hook, positioned as smkent places it."""
        h = self.latch_width
        body = self.render_draw_latch_catch_body()
        hook = self._draw_latch_hook_solid(h).translate(
            (
                SK_DRAW_SEP,
                self.latch_screw_separation - self.latch_base_size + SK_M3 / 2,
                0,
            )
        )
        r = body.union(hook)
        return self.repair_if_invalid(r)

    def render_draw_latch_catch_body(self):
        """The catch's main body, before the hook is added.

        Built with the exact hull-of-circles primitive rather than an
        approximation, so the end caps stay true arcs.
        """
        circles = self._draw_latch_catch_body_circles()
        wire = _wire_from_hull(_hull_of_circles(circles))
        return wire.extrude(self.latch_width)

    def render_latch(self):
        """The clip latch: a single flexing part, no hardware but its screws."""
        if self.latch_type != "clip":
            raise NotImplementedError(
                "Only the clip latch is implemented so far; draw latch is next. "
                "Got latch_type=%r" % (self.latch_type,)
            )
        r = self._clip_latch_solid(self.latch_width)
        r = self._break_extruded_edges(r)
        r = self.repair_if_invalid(r)
        self._cq_obj = r
        self._obj_label = "latch"
        return r

    def render(self):
        """Default render is the box body."""
        return self.render_body()

    # -- naming -----------------------------------------------------------

    @property
    def _filename_prefix(self) -> str:
        return "gf_ruggedbox_sk_"

    def _filename_suffix(self) -> str:
        fn = "x%s" % self._fmt_unit(self.height_u)
        fn += "_%s" % self.latch_type
        if abs(self.size_tolerance - SK_SIZE_TOL) > 1e-6:
            fn += "_tol%.2f" % self.size_tolerance
        return fn
