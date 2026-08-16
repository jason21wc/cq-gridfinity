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
from cqgridfinity.gf_baseplate import GridfinityBaseplate
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

# -- Lip seal (1E.3) -----------------------------------------------------
SK_SEAL_TYPES = ("none", "wedge", "square", "filament-1.75mm")
SK_SEAL_FILAMENT_D = 1.75  # standard filament, used as gasket stock
# Clearance between the ridge and its groove, for the moulded seal types.
# Not used by the filament seal, where both halves are simply grooved.
SK_SEAL_CLEARANCE = 0.2
# Net depth a moulded ridge is buried in the lid, so the union actually fuses
# rather than leaving it as a separate solid touching on a coplanar face.
# NOTE this is the depth AFTER the clearance offset: offset2D(-clearance)
# shrinks the profile in every direction, so the embed passed to the profile
# must exceed the clearance or the ridge ends up entirely below the mating
# plane and never touches the lid at all.
SK_SEAL_EMBED = 0.2

# -- Integrated baseplate (1E.4) -----------------------------------------
# smkent rugged-box-gridfinity.scad:
#     border = 5;
#     width  = Width  * l_grid + border;
#     length = Length * l_grid + border;
# The interior is FIVE millimetres larger than the Gridfinity footprint it
# holds -- 2.5mm of clearance per side. It is not decorative: the baseplate
# inside is exactly n*42 with a 4.0mm outer corner radius, sitting in a cavity
# radiused 3.75mm, so without the border the plate would foul all four corners
# and bins would be an interference fit into a printed box.
SK_GF_BORDER = 5.0

# Gridfinity's own corner radius, which smkent passes as the box's INTERIOR
# corner radius (`corner_radius = r_base`). kennetek renamed r_base to
# BASE_TOP_RADIUS = 7.5 / 2 in src/core/standard.scad.
GF_CORNER_RAD = 3.75

# smkent `edge_chamfer_proportion`, Gridfinity preset. Chamfers the outward
# end of each half: proportion of corner_radius horizontally, 1.5x vertically.
SK_EDGE_CHAMFER_PROP = 0.95

# -- Support ribs (1E.9) -------------------------------------------------
# smkent `plain_ribs_angle`: draft on the plan-view outline, so a rib is
# wider where it meets the wall than at its outer tip.
SK_PLAIN_RIB_ANGLE = 8.0

# -- Attachments: placement, eyelets, screws (1E.10, 1E.11) --------------
SK_SCREW_EYELET_PROP = 3.0    # screw_eyelet_size_proportion
SK_SCREW_HOLE_FIT = 0.2       # of the diameter; oversize so the screw turns
SK_HINGE_EXTRA_SETBACK = 0.2  # hinge_extra_setback
SK_HINGE_SIZE_TOL = 0.1       # hinge_size_tolerance
SK_TOP_HINGE_EYELET_TOL = 0.1  # top_hinge_eyelet_position_tolerance
# smkent `third_hinge_width` in the Gridfinity wrapper: l_grid * 5. A lid
# this wide on two corner hinges racks under its own weight.
SK_THIRD_HINGE_U = 5


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


def _rounded_rect_wire(length, width, radius, z=0.0):
    """Closed rounded-rectangle wire at height z.

    `placeSketch(...).wires().val()` does not return a Wire, so build the face
    by extruding and take its outer boundary instead.
    """
    slab = (
        cq.Workplane("XY")
        .placeSketch(rounded_rect_sketch(length, width, radius))
        .extrude(1)
    )
    wires = slab.faces("<Z").val().Wires()
    length_of = lambda w: w.Length() if callable(w.Length) else w.Length
    outer = max(wires, key=length_of)
    return outer.moved(cq.Location(cq.Vector(0, 0, z)))


def _xf(pts, ang=None, tr=None):
    """Apply OpenSCAD-style rotate/translate to a list of 2D points.

    smkent composes several rotate/translate steps onto a square; replaying the
    same chain is clearer -- and less error-prone -- than pre-multiplying it by
    hand into final coordinates.
    """
    out = []
    for x, y in pts:
        if ang is not None:
            a = math.radians(ang)
            x, y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
        if tr is not None:
            x, y = x + tr[0], y + tr[1]
        out.append((x, y))
    return out


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
            if radius <= EPS:
                # A degenerate "circle" is a point: the tangent lines either
                # side already meet there, so there is no arc to draw. Lets a
                # polygon corner take part in a hull of circles.
                continue
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
        # smkent's Top_Height default is 2, and so is ours. A 1U lid is legal
        # once the outer height includes its wall, but has only 0.048mm to
        # spare over the lip profile it must contain (ramp 4.5 + land 6.0 =
        # 10.5mm, against an interior of 7 + 3.548).
        self.lid_height_u = 2  # lid depth in Gridfinity height units
        self.latch_type = "clip"  # "clip" | "draw"
        # Lip seal (1E.3). "filament-1.75mm" cuts a half-round groove in BOTH
        # halves so a loop of 1.75mm filament serves as the gasket -- stock you
        # already own, in whatever durometer you like if you use TPU.
        self.lip_seal_type = "wedge"
        # Integrated baseplate (1E.4). smkent ships four named styles; the
        # two axes underneath them are all that vary, so they are exposed as
        # two booleans instead:
        #     minimal      -> False, False   (upstream default, and ours)
        #     enabled_full -> True,  False
        #     enabled      -> True,  True
        # Upstream's fourth style, "thick" (a full-depth slab with no magnet
        # holes), is deliberately not reachable: it is pure ballast in a box
        # whose whole point is being carried.
        self.baseplate_magnets = False
        self.baseplate_skeletonized = False
        # Third hinge (1E.6). Structural, not decorative -- upstream's
        # Gridfinity wrapper turns it on by default and it self-activates by
        # width, so there is nothing to tune.
        self.third_hinge = True
        # Hinge end stops (1E.7). Bottom half only -- a physical limit on lid
        # rotation, which is the commonest way a printed hinge dies.
        self.hinge_end_stops = True
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
        if self.lid_height_u < 1:
            raise ValueError(
                "lid_height_u must be >= 1, got %r" % (self.lid_height_u,)
            )
        if self.height_u <= self.lid_height_u:
            raise ValueError(
                "height_u (%r) must exceed lid_height_u (%r): the lid is "
                "carved out of the total, so the body would get no depth"
                % (self.height_u, self.lid_height_u)
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
        if self.lip_seal_type not in SK_SEAL_TYPES:
            raise ValueError(
                "lip_seal_type must be one of %s, got %r"
                % (SK_SEAL_TYPES, self.lip_seal_type)
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
        """Interior length: the Gridfinity footprint, plus smkent's border.

        Upstream is `width = Width * l_grid + border` with `border = 5`, so
        the cavity carries 2.5mm of clearance per side around the baseplate
        and the bins standing in it. See SK_GF_BORDER.
        """
        return self.length_u * GRU + SK_GF_BORDER

    @property
    def int_width(self):
        return self.width_u * GRU + SK_GF_BORDER

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

        The integrated baseplate then pushes the floor up by its own slab
        depth, so the bins keep their full N*7 regardless of base style --
        upstream's `bottom_height = Bottom_Height * 7 + base_extra_height()`.

        This is the INTERIOR across both halves. Each half's outer height adds
        a wall_thickness on top of its own share; see `body_height`.
        """
        return self.body_int_height + self.lid_int_height

    @property
    def body_u(self):
        """Gridfinity height units in the lower half -- upstream Bottom_Height.

        `height_u` is the total; the lid is carved out of it rather than being
        a second independent parameter, which is the one place this API differs
        from upstream's separate Bottom_Height / Top_Height.
        """
        return self.height_u - self.lid_height_u

    @property
    def body_int_height(self):
        """Interior depth of the lower half.

        smkent `bottom_height = Bottom_Height * 7 + base_extra_height()`.
        """
        return self.body_u * GRHU + self.baseplate_extra_depth

    @property
    def lid_int_height(self):
        """Interior depth of the lid.

        smkent `top_height = Top_Height * 7 + h_lip`. The stacking-lip
        headroom belongs to the LID, where the topmost bin's lip actually
        protrudes -- not to the body.
        """
        return self.lid_height_u * GRHU + self.bin_lip_clearance

    # -- integrated baseplate (1E.4) --------------------------------------

    def _baseplate(self):
        """The Gridfinity baseplate that lines the box floor.

        `GridfinityBaseplate` is reused rather than re-derived: upstream does
        the same thing, calling kennetek's `gridfinityBaseplate()` from the
        rugged box wrapper instead of drawing its own receptacles. It is also
        where the magnet, skeleton and hole geometry is already tested.
        """
        return GridfinityBaseplate(
            self.length_u,
            self.width_u,
            magnet_holes=self.baseplate_magnets,
            skeleton=self.baseplate_skeletonized,
        )

    @property
    def baseplate_extra_depth(self):
        """Solid slab below the plate's receptacles, in mm.

        Upstream hardcodes this as kennetek's `h_hole` (2.4mm) whenever the
        base style is not "minimal". We take it from the plate we actually
        build, so a skeletonized plate -- which needs more depth than a bare
        magnet pocket -- is accounted for rather than assumed. For the
        magnets-only case the two agree exactly; that is asserted in
        tests/test_rbox_smkent.py.
        """
        return self._baseplate().ext_depth

    def render_baseplate(self):
        """The integrated baseplate, sitting on the box's interior floor."""
        r = self._baseplate().render().translate((0, 0, self.wall_thickness))
        self._cq_obj = r
        self._obj_label = "baseplate"
        return r

    @property
    def bin_lip_clearance(self):
        """Extra headroom a stacked bin's lip needs, above N*7."""
        return GR_STACKING_LIP_H - GR_LIP_APEX_SETBACK

    @property
    def box_length(self):
        """smkent: outer = inner + total_lip_thickness * 2.

        NOT wall_thickness. The outer dimension is set by the LIP land, which
        is the thickest part of the wall -- using wall_thickness made the box
        6mm undersized in each direction.
        """
        return self.int_length + 2 * self.total_lip_thickness

    @property
    def box_width(self):
        return self.int_width + 2 * self.total_lip_thickness

    @property
    def lid_height(self):
        """OUTER height of the lid: smkent `top_outer = top_inner + wall`.

        Regression: this returned the interior figure and was then used as the
        extrude height, so the ceiling was carved out of the interior instead
        of added outside it. A 6U box came up 4.2mm short of a 6U bin.
        """
        return self.lid_int_height + self.wall_thickness

    @property
    def body_height(self):
        """OUTER height of the lower half: `bottom_outer = bottom_inner + wall`."""
        return self.body_int_height + self.wall_thickness

    @property
    def corner_radius(self):
        """Outer corner radius at the lip land.

        smkent line 544: `outer_radius = corner_radius + wall_thickness`,
        where `corner_radius` is the INTERIOR radius (line 76). At the lip the
        wall is total_lip_thickness, so the land's radius follows that.
        """
        return GF_CORNER_RAD + self.total_lip_thickness

    @property
    def outer_chamfer_horizontal(self):
        """smkent `$b_outer_chamfer_horizontal`."""
        return SK_EDGE_CHAMFER_PROP * GF_CORNER_RAD

    @property
    def outer_chamfer_vertical(self):
        """smkent `$b_outer_chamfer_vertical` -- 1.5x the horizontal."""
        return self.outer_chamfer_horizontal * 1.5

    @property
    def latch_part_width(self):
        """Width of the latch PART -- smkent `_latch_width()`.

        `latch_width` is the space reserved on the box; the part itself is
        `size_tolerance` narrower on each side, and that difference is the
        entire running clearance. Every latch extrusion upstream uses this,
        never the raw parameter.

        Regression: all ten latch extrusions used the raw width, so a latch
        was 2 x size_tolerance too wide to drop between its own ribs -- and
        `size_tolerance`, documented as the knob to reach for when a latch
        does not fit, changed no geometry at all.
        """
        return self.latch_width - self.size_tolerance * 2

    @property
    def latch_base_size(self):
        """smkent latch_base_size = screw_diameter * (proportion / 2)."""
        return SK_M3 * (SK_LATCH_BODY_PROPORTION / 2)

    # -- lip seal (1E.3) ---------------------------------------------------

    @property
    def seal_thickness(self):
        """smkent: 1.75 for the filament seal, else total_lip_thickness / 3."""
        if self.lip_seal_type == SK_SEAL_TYPES[3]:
            return SK_SEAL_FILAMENT_D
        return self.total_lip_thickness / 3

    @property
    def seal_is_inset(self):
        """True when BOTH halves are grooved rather than ridge-and-groove.

        The filament seal works that way: each half gets a half-round channel
        and a loop of filament sits between them. The moulded types instead put
        a ridge on the lid and a matching groove in the body.
        """
        return self.lip_seal_type == SK_SEAL_TYPES[3]

    def _seal_profile_points(self, embed=0.0):
        """Seal cross-section. Local x is radial, local y is vertical.

        `embed` extends the profile ABOVE the mating plane. A ridge otherwise
        sits entirely below z=0 and meets the lid only on that plane -- a
        coplanar contact, which OpenCASCADE will not fuse, leaving the ridge as
        a second disconnected solid. See LEARNING-LOG: coplanar boolean faces.
        The protruding height is unchanged; only the buried part grows.
        """
        t = self.seal_thickness
        if self.lip_seal_type == "square":
            return [(-t / 2, -t), (t / 2, -t), (t / 2, embed), (-t / 2, embed)]
        if self.lip_seal_type == "wedge":
            # smkent's trapezoid: narrow at the root, wide at the tip.
            return [(-t / 4, -t), (t / 4, -t), (t / 2, embed), (-t / 2, embed)]
        return None  # circle, handled separately

    def _seal_path(self):
        """Closed rounded-rect path the seal follows, inset into the lip."""
        inset = self.total_lip_thickness / 2
        pl = self.box_length - 2 * inset
        pw = self.box_width - 2 * inset
        pr = max(self.corner_radius - inset, 0.5)
        slab = (
            cq.Workplane("XY")
            .placeSketch(rounded_rect_sketch(pl, pw, pr))
            .extrude(1)
        )
        wires = slab.faces("<Z").val().Wires()
        length_of = lambda w: w.Length() if callable(w.Length) else w.Length
        return max(wires, key=length_of)

    def render_seal_ring(self, delta=0.0, z=None, embed=0.0):
        """The seal as a swept ring, ready to add to the lid or cut from the body.

        `delta` shrinks the profile (negative) so the lid's ridge is smaller
        than the groove it seats into -- that difference is the seal clearance.
        """
        if self.lip_seal_type == "none":
            return None
        path = self._seal_path()
        sp = path.startPoint()
        tangent = path.tangentAt(0)
        # Local x radial, local y vertical, normal along the path.
        plane = cq.Plane(origin=sp, normal=tangent, xDir=cq.Vector(-1, 0, 0))
        wp = cq.Workplane(plane)
        if self.seal_is_inset:
            prof = wp.circle(self.seal_thickness / 2 + delta)
        else:
            pts = self._seal_profile_points(embed=embed)
            prof = wp.polyline(pts).close()
            if abs(delta) > 1e-9:
                prof = prof.offset2D(delta)
        ring = prof.sweep(cq.Workplane(obj=path), isFrenet=True)
        zz = self.body_height if z is None else z
        return ring.translate((0, 0, zz))

    # -- geometry ---------------------------------------------------------

    @property
    def plain_outer_length(self):
        """Outer length below the lip: `inner + 2 * wall_thickness`."""
        return self.int_length + 2 * self.wall_thickness

    @property
    def plain_outer_width(self):
        return self.int_width + 2 * self.wall_thickness

    @property
    def plain_corner_radius(self):
        """Outer corner radius below the lip."""
        return GF_CORNER_RAD + self.wall_thickness

    def _outer_block(self, height, z0=0.0, lip_at_top=True):
        """The outer surface: a thin wall that steps OUT into the lip land.

        smkent's `_box_wall_shape` subtracts from the OUTER side below the
        lip. The interior is a constant `inner` for the full height; the
        outside is `inner + 2*wall_thickness` for most of it, ramps over
        `1.5 * lip_thickness`, then holds `inner + 2*total_lip_thickness`
        for the top `lip_height`.

        Regression: this used to be a plain prism at the full outer size with
        the step taken out of the CAVITY instead -- a different solid, 6mm
        oversized over most of its height, and with no thin wall for a support
        rib to thicken. See documents/SHELL-AUDIT-1E8.md.
        """
        lip_h = self.lip_height
        ramp_h = self.lip_thickness * 1.5
        plain_h = max(height - lip_h - ramp_h, 0.0)
        pl, pw, pr = (
            self.plain_outer_length,
            self.plain_outer_width,
            self.plain_corner_radius,
        )
        parts = []
        if plain_h > EPS:
            parts.append(
                cq.Workplane("XY")
                .placeSketch(rounded_rect_sketch(pl, pw, pr))
                .extrude(plain_h)
            )
        # Ramp: loft outward from the plain wall up to the lip land.
        if ramp_h > EPS:
            lo = _rounded_rect_wire(pl, pw, pr, plain_h)
            hi = _rounded_rect_wire(
                self.box_length, self.box_width, self.corner_radius,
                plain_h + ramp_h,
            )
            parts.append(
                cq.Workplane("XY").newObject([cq.Solid.makeLoft([lo, hi], ruled=True)])
            )
        top_h = height - plain_h - ramp_h
        if top_h > EPS:
            parts.append(
                cq.Workplane("XY")
                .placeSketch(
                    rounded_rect_sketch(
                        self.box_length, self.box_width, self.corner_radius
                    )
                )
                .extrude(top_h)
                .translate((0, 0, plain_h + ramp_h))
            )
        block = parts[0]
        for extra in parts[1:]:
            block = block.union(extra)
        block = self._cut_outer_chamfer(block, height)
        block = self._round_outer_edges(block)
        if not lip_at_top:
            block = block.mirror("XY").translate((0, 0, height))
        return block.translate((0, 0, z0))

    # -- attachments: placement and eyelets (1E.10, 1E.11) ----------------

    @property
    def screw_eyelet_radius(self):
        """smkent `screw_eyelet_radius = screw_hole_diameter * 3.0 / 2`."""
        return SK_M3 * SK_SCREW_EYELET_PROP / 2

    @property
    def attachment_screw_offset(self):
        """How far the screw axis stands off the wall.

        smkent `_attachment_screw_offset() = total_lip_thickness +
        screw_eyelet_radius + hinge_extra_setback`. Latch and hinge share it.
        """
        return (
            self.total_lip_thickness
            + self.screw_eyelet_radius
            + SK_HINGE_EXTRA_SETBACK
        )

    @property
    def latch_count(self):
        """smkent's Gridfinity wrapper: `latch_count = (Width <= 2 ? 1 : 2)`.

        Upstream's `Width` is our `length_u` -- the axis the latches sit
        along.
        """
        return 1 if self.length_u <= 2 else 2

    @property
    def latch_hinge_position(self):
        """smkent `rb_latch_hinge_position() = l_grid * (Width / 2 - 0.5)`."""
        return GRU * (self.length_u / 2 - 0.5)

    @property
    def third_hinge_width(self):
        """smkent `third_hinge_width = Third_Hinge ? l_grid * 5 : 0`."""
        return GRU * SK_THIRD_HINGE_U if self.third_hinge else 0.0

    @property
    def has_third_hinge(self):
        """smkent: `third_hinge_width > 0 && inner_width >= third_hinge_width`.

        Note it tests the INTERIOR against the threshold, and our interior
        carries the 5mm border -- so a 5U box (215) clears 210 and a 4U box
        (173) does not, which is the documented "5U or wider".
        """
        return (
            self.latch_count == 2
            and self.third_hinge_width > 0
            and self.int_length >= self.third_hinge_width
        )

    def attachment_positions(self, hinge=False):
        """X offsets of the attachment sites -- smkent `_box_attachment_placement`.

        Latches and hinges share this. With two latches the sites are mirrored
        about the centre; **the third hinge is simply one more position at
        x = 0**, and only for hinges. That is the whole of feature 1E.6: the
        rule is trivial, and everything it needs underneath it is not.
        """
        if self.latch_count != 2:
            return [0.0]
        pos = [-self.latch_hinge_position, self.latch_hinge_position]
        if hinge and self.has_third_hinge:
            pos.append(0.0)
        return sorted(pos)

    def attachment_pair_offsets(self, inner=False):
        """The rib pair straddling one attachment -- `_box_attachment_rib_pair`."""
        half = (self.latch_width + self.rib_width) / 2
        shift = -self.size_tolerance if inner else 0.0
        return [-(half + shift), half + shift]

    def _screw_eyelet(self, width, half=False):
        """smkent `_box_screw_eyelet_body`: a boss for the M3 to pass through.

        Axis along Y, `width` long, ends rounded by `edge_radius`. `half`
        takes the 180-degree version the hinge bodies hull against.
        """
        r = self.screw_eyelet_radius
        cyl = cq.Workplane("XY").circle(r).extrude(width)
        try:
            cyl = cyl.edges("%CIRCLE").fillet(self.edge_radius)
        except Exception:
            pass
        cyl = cyl.rotate((0, 0, 0), (1, 0, 0), -90).translate((0, width / 2, 0))
        if half:
            keep = (
                cq.Workplane("XY")
                .box(4 * r, 2 * width, 2 * r)
                .translate((-r, 0, 0))
            )
            cyl = cyl.intersect(keep)
        return cyl

    def _screw_hole(self, width, oversize=False):
        """smkent `_box_screw_hole`.

        The two halves are drilled differently on purpose: the bottom is
        undersized by 0.1mm so the screw forms its own thread, the top
        oversized by 0.2 x diameter so it turns freely. That is what makes
        the pair act as a hinge rather than seize.
        """
        d = SK_M3 + (SK_M3 * SK_SCREW_HOLE_FIT if oversize else SK_SCREW_HOLE_TOL)
        # Centred on the origin along its own axis: upstream's
        # `translate([0, 0, -width]) cylinder(width * 2)` straddles the part.
        # Getting this offset wrong drills a hole in mid-air next to the boss
        # and leaves the boss solid -- which is exactly what it did.
        return (
            cq.Workplane("XY")
            .circle(d / 2)
            .extrude(2 * width)
            .rotate((0, 0, 0), (1, 0, 0), -90)
            .translate((0, -width, 0))
        )

    # -- hinge ribs (1E.13) and end stops (1E.7) --------------------------

    @property
    def hinge_rib_width(self):
        """smkent `hinge_rib_width = rib_width * 2` -- the body's knuckles."""
        return self.rib_width * 2

    @property
    def top_hinge_width(self):
        """The lid's central knuckle, sized to drop between the body's pair.

        smkent: `_latch_width() - hinge_rib_width - hinge_size_tolerance * 2`.
        """
        return (
            self.latch_part_width
            - self.hinge_rib_width
            - SK_HINGE_SIZE_TOL * 2
        )

    def _hinge_hull_circles(self, inner=False):
        """XZ hull inputs for one knuckle, with z=0 at the part's joint face.

        Same collapse as the latch boss: web prism and eyelet cylinders are
        both prisms along the pin axis over one interval, so the 3D hull is a
        2D hull swept.

        Upstream hulls against HALF eyelets (`angle=-180`) and unions a full
        one on top. That is not a flourish: hulling against FULL circles fills
        the wedge ABOVE the joint plane between the web and the knuckle --
        which is exactly where the other half's lip land sits. Tried it; the
        assembled halves interfered by 973mm3. The hull is therefore clipped
        to the joint plane and the eyelet added back whole.
        """
        cr, r = GF_CORNER_RAD, self.screw_eyelet_radius
        h = (
            r * (2 if inner else 3)
            + 2 * (self.wall_thickness + self.rib_width)
            + cr * 1.5
        )
        # Web: rib profile taken only to wall_thickness, set back by cr+wall.
        back = cr + self.wall_thickness
        x0, x1 = self.edge_radius - back, self.wall_thickness - back
        circles = [(x0, -h, 0.0), (x1, -h, 0.0), (x1, 0.0, 0.0), (x0, 0.0, 0.0)]
        xe = self.attachment_screw_offset
        circles.append((xe, 0.0, r))
        if not inner:
            circles.append((xe, -r, r))
        return circles

    def _hinge_eyelet_solid(self, height, width, lid=False):
        """The knuckle proper: a full eyelet centred on the joint plane.

        The lid's is drawn out by `top_hinge_eyelet_position_tolerance` into a
        stadium, so the pivot has somewhere to turn.
        """
        r = self.screw_eyelet_radius
        xe = self.attachment_screw_offset
        if lid:
            wire = _wire_from_hull(
                _hull_of_circles(
                    [(xe, 0.0, r), (xe, SK_TOP_HINGE_EYELET_TOL, r)]
                )
            )
        else:
            wire = cq.Workplane("XY").center(xe, 0.0).circle(r)
        return (
            wire.extrude(width)
            .rotate((0, 0, 0), (1, 0, 0), 90)
            .translate((0, width / 2, height))
        )

    def _hinge_rib_body(self, height, width, inner=False, lid=False):
        """One hinge knuckle, trimmed back to the wall like the latch boss."""
        wire = _wire_from_hull(
            _hull_of_circles(self._hinge_hull_circles(inner=inner))
        )
        body = (
            wire.extrude(width)
            .rotate((0, 0, 0), (1, 0, 0), 90)
            .translate((0, width / 2, height))
        )
        # Clip the hull to the joint plane, then put the eyelet back whole.
        above = (
            cq.Workplane("XY")
            .box(8 * self.attachment_screw_offset, 4 * width, 4 * height)
            .translate((2 * self.attachment_screw_offset, 0, height + 2 * height))
        )
        body = body.cut(above).union(
            self._hinge_eyelet_solid(height, width, lid=lid)
        )
        body = self._break_extruded_edges(
            body, radius=self.edge_radius, selectors=(">Y", "<Y")
        )
        return body.cut(self._attachment_rib_cut(width, height))

    def _hinge_end_stop(self, height, width):
        """1E.7. smkent keeps only the LOWER part of a knuckle, as a tab.

        Over-rotation is the commonest failure of a printed hinge; this is the
        physical barrier that prevents it, and it also stops the lid falling
        open past vertical.
        """
        ww = self.attachment_screw_offset * 2 + self.screw_eyelet_radius * 2
        keeper = (
            cq.Workplane("XY")
            .box(ww, 2 * width, 2 * ww)
            .translate((-1.25, 0, height - 2.0 - self.screw_eyelet_radius - ww))
        )
        return self._hinge_rib_body(height, width).intersect(keeper)

    def render_hinge_ribs(self, height=None, lid=False):
        """All hinge knuckles for one half -- smkent `_box_hinge_ribs`.

        The two halves interleave along the pin: the body takes a pair at
        +/-(latch_width + rib_width)/2 - rib_width/2, the lid a central block
        plus two narrower knuckles that drop into the gaps with
        `hinge_size_tolerance` of running clearance either side.

        These sit on the REAR wall (+Y) -- the shared placement unmirrored --
        and this is where `attachment_positions(hinge=True)` puts the third
        hinge into actual geometry.
        """
        h = (self.lid_height if lid else self.body_height) if height is None else height
        pair = self.attachment_pair_offsets(inner=lid)
        parts = []
        if lid:
            gap = self.hinge_rib_width + SK_HINGE_SIZE_TOL
            knuckle = self._rib_solid(h, self.rib_width).union(
                self._hinge_rib_body(h, self.rib_width, lid=True)
            )
            # The central knuckle carries a support rib of its own. Upstream
            # gives one only to the outer pair, which leaves a small sealed
            # pocket in the wall in the gap between them -- see the shell
            # count test. Cheap to close, and it is more material under the
            # hinge, not less.
            middle = self._rib_solid(h, self.top_hinge_width).union(
                self._hinge_rib_body(h, self.top_hinge_width, inner=True, lid=True)
            )
            for i, off in enumerate(pair):
                shift = off - gap if off > 0 else off + gap
                parts.append((knuckle, shift))
            parts.append((middle, 0.0))
        else:
            knuckle = self._rib_solid(h, self.hinge_rib_width).union(
                self._hinge_rib_body(h, self.hinge_rib_width)
            )
            half = self.rib_width / 2
            for off in pair:
                parts.append((knuckle, off - half if off > 0 else off + half))
            if self.hinge_end_stops:
                stop = self._rib_solid(h, self.latch_part_width).union(
                    self._hinge_end_stop(h, self.latch_part_width)
                )
                parts.append((stop, 0.0))
        placed = []
        for px in self.attachment_positions(hinge=True):
            for solid, off in parts:
                placed.append(
                    solid.rotate((0, 0, 0), (0, 0, 1), 90).translate(
                        (px + off, self.int_width / 2, 0)
                    )
                )
        out = placed[0]
        for extra in placed[1:]:
            out = out.union(extra)
        # The pin: one M3 per hinge, drilled to fit its half.
        holes = []
        for px in self.attachment_positions(hinge=True):
            hole = (
                self._screw_hole(3 * self.latch_width, oversize=lid)
                .rotate((0, 0, 0), (0, 0, 1), 90)
                .translate(
                    (
                        px,
                        self.int_width / 2 + self.attachment_screw_offset,
                        h + (SK_TOP_HINGE_EYELET_TOL if lid else 0.0),
                    )
                )
            )
            holes.append(hole)
        for hole in holes:
            out = out.cut(hole)
        return out

    # -- support ribs (1E.9) ----------------------------------------------

    # -- latch mounting ribs (1E.12) ---------------------------------------

    @property
    def effective_latch_amount_on_top(self):
        """How much of the screw separation sits on the LID side.

        smkent `_init_latch_amount_on_top()`; 0 means auto, which is our
        default. The two halves' screw heights then differ by exactly
        `latch_screw_separation`, which is what lets one latch span the joint.
        """
        if self.latch_amount_on_top > 0:
            return self.latch_amount_on_top
        if self.latch_type == "draw":
            by_type = self.latch_screw_separation - self.screw_eyelet_radius * 1.25
        else:
            by_type = min(
                self.screw_eyelet_radius * 2.0, self.latch_screw_separation / 2
            )
        return min((self.lid_int_height + self.wall_thickness) / 2, by_type)

    def latch_offset_from_base(self, lid=False):
        """Height of the latch screw above the part's own base.

        smkent `_latch_offset_from_base()`: the lid keeps
        `latch_amount_on_top`, the body the remainder of the separation.
        """
        height = self.lid_height if lid else self.body_height
        top = self.effective_latch_amount_on_top
        return height - (top if lid else self.latch_screw_separation - top)

    def _latch_boss_hull_circles(self, latch_position):
        """Hull inputs for the latch attachment boss, in the XZ plane.

        smkent hulls a Z-extruded rib prism against two eyelet cylinders whose
        axes run along Y. CadQuery has no 3D hull -- but it does not need one:
        both bodies are prisms along Y over the SAME interval, so the 3D hull
        restricted to that slab is exactly the 2D hull of their XZ profiles
        swept across it. The prism contributes its four rectangle corners as
        zero-radius circles.
        """
        cr = GF_CORNER_RAD
        r = self.screw_eyelet_radius
        h = r * 6 + cr * 2  # smkent latch_attachment_height
        x0, x1 = self.edge_radius - cr, self.total_lip_thickness - cr
        z0, z1 = latch_position - h / 2, latch_position + h / 2
        xe = self.attachment_screw_offset
        return [
            (x0, z0, 0.0),
            (x1, z0, 0.0),
            (x1, z1, 0.0),
            (x0, z1, 0.0),
            (xe, latch_position - r / 2, r),
            (xe, latch_position + r / 2, r),
        ]

    def _latch_boss(self, latch_position, width):
        """The boss the latch screws into, before trimming."""
        wire = _wire_from_hull(
            _hull_of_circles(self._latch_boss_hull_circles(latch_position))
        )
        boss = wire.extrude(width)
        # The hull was drawn in the workplane's XY; stand it up so its second
        # axis is Z and the sweep runs along Y, centred on the rib.
        boss = boss.rotate((0, 0, 0), (1, 0, 0), 90).translate((0, width / 2, 0))
        return self._break_extruded_edges(
            boss, radius=self.edge_radius, selectors=(">Y", "<Y")
        )

    def _attachment_rib_cut(self, width, height):
        """smkent `_box_attachment_rib_cut`: keep the boss OUTSIDE the wall.

        Everything inboard of the plain wall's outer face, and everything
        below the floor, is removed -- the rib alone carries the boss into the
        wall.
        """
        cr = GF_CORNER_RAD
        inner = (
            cq.Workplane("XY")
            .box(2 * (cr + self.wall_thickness), 4 * width, 2 * height)
            .translate((-cr, 0, self.wall_thickness + height))
        )
        below = (
            cq.Workplane("XY")
            .box(6 * self.latch_width, 4 * width, 2 * height)
            .translate((0, 0, -height))
        )
        return inner.union(below)

    def _latch_rib(self, height, width=None, lid=False):
        """One latch rib: a support rib plus the screwed boss on top of it."""
        width = self.rib_width if width is None else width
        pos = self.latch_offset_from_base(lid=lid)
        rib = self._rib_solid(height, width)
        boss = self._latch_boss(pos, width)
        # smkent bounds the boss with cube([cr + screw_offset*4, width,
        # outer_height]) at x = -cr, z = 0: it may not reach above the part.
        span = GF_CORNER_RAD + self.attachment_screw_offset * 4
        keep = (
            cq.Workplane("XY")
            .box(span, width, height)
            .translate((span / 2 - GF_CORNER_RAD, 0, height / 2))
        )
        boss = boss.intersect(keep).cut(self._attachment_rib_cut(width, height))
        out = rib.union(boss)
        # Screw hole, drilled to fit its half.
        hole = self._screw_hole(width * 2, oversize=lid).translate(
            (self.attachment_screw_offset, 0, pos)
        )
        return out.cut(hole)

    def render_latch_ribs(self, height=None, lid=False):
        """All latch ribs for one half -- smkent `_box_latch_ribs`.

        They sit on the FRONT wall (-Y): upstream mirrors the shared
        attachment placement, which the hinge ribs use unmirrored.
        """
        h = (self.lid_height if lid else self.body_height) if height is None else height
        rib = self._latch_rib(h, lid=lid)
        placed = []
        for px in self.attachment_positions(hinge=False):
            for off in self.attachment_pair_offsets():
                placed.append(
                    rib.rotate((0, 0, 0), (0, 0, 1), -90).translate(
                        (px + off, -self.int_width / 2, 0)
                    )
                )
        out = placed[0]
        for extra in placed[1:]:
            out = out.union(extra)
        return out

    def _rib_profile(self, width, angle=0.0):
        """smkent `_box_rib_shape`: the rib's plan-view outline.

        Local x runs outward from the interior surface, y along the wall. The
        rib spans `edge_radius` to `total_lip_thickness`, so it buries itself
        slightly in the wall and finishes flush with the lip land -- standing
        proud of the plain wall by exactly `lip_thickness`. That is the whole
        point of it, and why an unstepped wall left it nowhere to go.

        `angle` is the draft. It defaults to NONE because only `_box_plain_rib`
        sets `$br_angle`; the attachment ribs call `_box_rib()` directly and so
        run undrafted. That is the sole purpose of upstream's `_box_rib_angle`
        wrapper -- to tell the two kinds of rib apart.
        """
        x0 = self.edge_radius
        x1 = self.total_lip_thickness
        add = math.tan(math.radians(angle)) * width
        pts = [
            (x0, width / 2 + add),
            (x1, width / 2),
            (x1, -width / 2),
            (x0, -(width / 2 + add)),
        ]
        prof = cq.Workplane("XY").polyline(pts).close()
        # smkent `_round_shape(edge_radius)`.
        return prof.offset2D(-x0).offset2D(2 * x0).offset2D(-x0)

    def _rib_solid(self, height, width, angle=0.0):
        """smkent `_box_rib`: the rib run up the wall, following the chamfer.

        Its lower `vertical_chamfer` is lofted in from `2/3` of that
        horizontally, so the rib rakes back with the box's own outer chamfer
        instead of overhanging it. It stops `edge_radius * 1.5` below the rim.
        """
        vc = min(
            self.outer_chamfer_vertical,
            max(
                0.0,
                height - self.lip_height - self.lip_thickness - self.wall_thickness,
            ),
        )
        hc = vc * 2 / 3
        top = height - self.edge_radius * 1.5
        prof = self._rib_profile(width, angle=angle)
        parts = []
        if top - vc > EPS:
            parts.append(prof.extrude(top - vc).translate((0, 0, vc)))
        if vc > EPS:
            lo = prof.translate((-hc, 0, 0)).vals()[0]
            hi = prof.translate((0, 0, vc)).vals()[0]
            parts.append(
                cq.Workplane("XY").newObject([cq.Solid.makeLoft([lo, hi], ruled=True)])
            )
        rib = parts[0]
        for extra in parts[1:]:
            rib = rib.union(extra)
        return rib

    def rib_positions(self):
        """(side, rear) rib positions, from the Gridfinity wrapper's overrides.

        `rb_side_rib_positions()` puts one rib per grid unit along each side.
        `rb_rear_rib_positions()` puts one on each INTERIOR grid line at the
        rear only -- `i = 1 .. Width-2` -- because the rear corners are where
        the hinges go.

        Upstream's axes are transposed against ours: its `Width` is our
        `length_u` (X), its `Length` our `width_u` (Y).
        """
        side = [GRU * (i - self.width_u / 2 + 0.5) for i in range(self.width_u)]
        rear = [
            GRU * (i - self.length_u / 2 + 0.5)
            for i in range(1, max(self.length_u - 1, 1))
        ]
        return side, rear

    def render_ribs(self, height=None, lip_at_top=True):
        """All support ribs for one half, as a single solid."""
        h = self.body_height if height is None else height
        width = self.rib_width * 2  # smkent `_box_plain_rib`
        rib = self._rib_solid(h, width, angle=SK_PLAIN_RIB_ANGLE)
        side, rear = self.rib_positions()
        placed = []
        for py in side:
            placed.append(rib.translate((self.int_length / 2, py, 0)))
            placed.append(
                rib.rotate((0, 0, 0), (0, 0, 1), 180).translate(
                    (-self.int_length / 2, py, 0)
                )
            )
        for px in rear:
            placed.append(
                rib.rotate((0, 0, 0), (0, 0, 1), 90).translate(
                    (px, self.int_width / 2, 0)
                )
            )
        out = placed[0]
        for extra in placed[1:]:
            out = out.union(extra)
        if not lip_at_top:
            out = out.mirror("XY").translate((0, 0, h))
        return out

    def _round_outer_edges(self, block):
        """smkent rounds the whole wall cross-section by `edge_radius`.

        On the swept solid that lands on the horizontal loops where the
        section changes: the base, both ends of the outer chamfer, both ends
        of the lip ramp, and the top rim. Convex corners round over, concave
        ones fill -- a CadQuery fillet does both.
        """
        edges = [e for e in block.edges().vals() if abs(e.BoundingBox().zlen) < EPS]
        if not edges:
            return block
        try:
            return block.newObject(edges).fillet(self.edge_radius)
        except Exception:
            # Never trade a valid solid for a cosmetic radius.
            warnings.warn(
                "%s: outer edge rounding failed, leaving edges sharp"
                % self.__class__.__name__,
                stacklevel=2,
            )
            return block

    def _cut_outer_chamfer(self, block, height):
        """Chamfer the bottom outer edge -- smkent `_box_wall_outer_chamfer_shape`.

        Horizontal `edge_chamfer_proportion * corner_radius`, vertical 1.5x
        that. It faces the part's outward end, so on the assembled box the
        body chamfers at the base and the lid at the top.
        """
        hc = self.outer_chamfer_horizontal
        vc = self.outer_chamfer_vertical
        # Upstream clamps the chamfer so it cannot eat into the lip region.
        vc = min(vc, max(height - self.lip_height - self.lip_thickness * 1.5, 0.0))
        if vc <= EPS or hc <= EPS:
            return block
        hc = hc * (vc / self.outer_chamfer_vertical)
        # Ring between the chamfered-in footprint and the full plain wall,
        # lofted so it opens out to nothing at the top of the chamfer.
        lo = _rounded_rect_wire(
            self.plain_outer_length - 2 * hc,
            self.plain_outer_width - 2 * hc,
            max(self.plain_corner_radius - hc, 0.1),
            0.0,
        )
        hi = _rounded_rect_wire(
            self.plain_outer_length,
            self.plain_outer_width,
            self.plain_corner_radius,
            vc,
        )
        keep = cq.Workplane("XY").newObject([cq.Solid.makeLoft([lo, hi], ruled=True)])
        below = (
            cq.Workplane("XY")
            .placeSketch(
                rounded_rect_sketch(
                    self.box_length + 10, self.box_width + 10, self.corner_radius
                )
            )
            .extrude(vc)
        )
        return block.cut(below.cut(keep))

    def _interior_void(self, height, z0, lip_at_top=True):
        """The cavity: a constant `inner` rounded rect, full height.

        Upstream's interior does not change section -- `_box_wall_interior_shape`
        removes one constant block. All the stepping lives on the outside.
        """
        void = (
            cq.Workplane("XY")
            .placeSketch(
                rounded_rect_sketch(self.int_length, self.int_width, GF_CORNER_RAD)
            )
            .extrude(height)
        )
        if not lip_at_top:
            void = void.mirror("XY").translate((0, 0, height))
        return void.translate((0, 0, z0))

    def render_body(self):
        """Lower half of the box: floor, walls, baseplate, and lower lip land.

        The body always receives the GROOVE, whichever seal type is chosen.
        """
        h = self.body_height
        r = self._outer_block(h)
        # The cavity runs from the floor to the rim, so its height is the box
        # height LESS the floor. Passing the full height pushed the lip land
        # above the box entirely and the wall never reached total_lip_thickness.
        void = self._interior_void(h - self.wall_thickness, self.wall_thickness)
        r = r.cut(void)
        # Baseplate goes in AFTER the cavity is cut, or it would be removed
        # with it. Its underside is coplanar with the interior floor, so the
        # union fuses on a shared face rather than leaving a second solid.
        r = r.union(self.render_baseplate())
        r = r.union(self.render_ribs(h))
        r = r.union(self.render_latch_ribs(h))
        r = r.union(self.render_hinge_ribs(h))
        groove = self.render_seal_ring()
        if groove is not None:
            r = r.cut(groove)
        self._cq_obj = r
        self._obj_label = "body"
        return r

    def render_lid(self):
        """Upper half. Rendered at the origin, not in assembled position.

        Moulded seals put a RIDGE here, undersized by SK_SEAL_CLEARANCE so it
        seats into the body's groove. The filament seal instead grooves this
        half too, so the gasket sits between two channels.
        """
        h = self.lid_height
        # Lid is the mirror image: its lip land sits at the BOTTOM, where it
        # meets the body, and its outer chamfer at the top.
        r = self._outer_block(h, lip_at_top=False)
        void = self._interior_void(h - self.wall_thickness, 0, lip_at_top=False)
        r = r.cut(void)
        r = r.union(self.render_ribs(h, lip_at_top=False))
        r = r.union(self.render_latch_ribs(h, lid=True).mirror("XY").translate((0, 0, h)))
        r = r.union(self.render_hinge_ribs(h, lid=True).mirror("XY").translate((0, 0, h)))
        if self.lip_seal_type != "none":
            if self.seal_is_inset:
                r = r.cut(self.render_seal_ring(z=0.0))
            else:
                ridge = self.render_seal_ring(
                    delta=-SK_SEAL_CLEARANCE,
                    z=0.0,
                    embed=SK_SEAL_CLEARANCE + SK_SEAL_EMBED,
                )
                r = r.union(ridge)
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
        solid = solid.cut(hinge_hole).cut(catch_hole)
        return self._round_profile_edges(solid, height)

    def _round_profile_edges(self, solid, height):
        """smkent wraps `_clip_latch_shape` in `_round_shape($b_edge_radius)`.

        That rounds the 2D outline before extrusion; on a prismatic solid the
        equivalent is filleting the edges parallel to the extrusion axis. It
        is separate from, and smaller than, the `latch_edge_radius` break on
        the two end faces -- upstream applies both.
        """
        axial = [
            e
            for e in solid.edges().vals()
            if abs(e.BoundingBox().zlen - height) < EPS
        ]
        if not axial:
            return solid
        try:
            return solid.newObject(axial).fillet(self.edge_radius)
        except Exception:
            warnings.warn(
                "%s: could not round the profile edges; they stay sharp"
                % self.__class__.__name__,
                stacklevel=2,
            )
            return solid

    def _break_extruded_edges(
        self, obj, radius=SK_LATCH_EDGE_RADIUS, selectors=(">Z", "<Z")
    ):
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
        for selector in selectors:
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

    def _draw_latch_handle_hull_circles(self):
        """The lever arm: a hull of the screw eyelet and the pin boss.

        Unequal radii (3.3 and 4.8), which is precisely the case
        polygon().offset2D(r) cannot express -- it is why the exact
        hull-of-circles primitive exists.
        """
        return [
            (0.0, 0.0, SK_DRAW_SCREW_EYELET_R),
            (
                SK_DRAW_SCREW_EYELET_R - SK_DRAW_PIN_HANDLE_R,
                -SK_DRAW_HANDLE_LENGTH,
                SK_DRAW_PIN_HANDLE_R,
            ),
        ]

    def render_draw_latch_handle_arm(self):
        """Lever arm with its pin and screw holes, before the grip is added.

        The pin HOLE is offset 0.3mm from the pin BOSS centre (smkent's
        draw_latch_pin_offset subtracts screw_diameter * 0.1), which biases the
        pivot -- it is not a centring error.
        """
        h = self.latch_part_width
        arm = _wire_from_hull(
            _hull_of_circles(self._draw_latch_handle_hull_circles())
        ).extrude(h)
        pin_hole = (
            cq.Workplane("XY")
            .circle(SK_DRAW_PIN_R + SK_DRAW_SEP)
            .extrude(h)
            .translate((*self._draw_pin_offset, 0))
        )
        # Screw hole: nominal, less the thread-forming tolerance, plus the
        # running-fit allowance -- smkent's screw_hole_diameter_fit = d * 0.2.
        screw_d = SK_M3 + SK_SCREW_HOLE_TOL + SK_M3 * 0.2
        screw_hole = cq.Workplane("XY").circle(screw_d / 2).extrude(h)
        return arm.cut(pin_hole).cut(screw_hole)

    def _draw_latch_curve_solid(self, h):
        """The handle's bent elbow, between the pin boss and the grip.

        smkent builds it as a union of a circle, two rectangles and a 25 degree
        annular sector, then applies `offset(-r) offset(r)` -- a CLOSING
        operation that rounds the concave junctions between those pieces.
        CadQuery spells that offset2D(+r).offset2D(-r).
        """
        thick = SK_DRAW_THICKNESS
        roff = SK_DRAW_PIN_HANDLE_R - SK_DRAW_SCREW_EYELET_R
        ox = -roff + SK_DRAW_PIN_HANDLE_R - thick  # inner frame origin x

        circ = (
            cq.Workplane("XY").circle(SK_DRAW_PIN_HANDLE_R).extrude(h)
            .translate((-roff, 0, 0))
        )
        sq = (
            cq.Workplane("XY").rect(thick, thick).extrude(h)
            .translate((ox + thick / 2, -thick / 2, 0))
        )
        # 25 degree annular sector: the outside of the elbow.
        cx = ox + SK_DRAW_BODY_CURVE_R + thick
        cy = -thick
        ring = (
            cq.Workplane("XY")
            .circle(SK_DRAW_BODY_CURVE_R + thick)
            .circle(SK_DRAW_BODY_CURVE_R)
            .extrude(h)
            .translate((cx, cy, 0))
        )
        a0 = math.radians(180)
        a1 = math.radians(180 + SK_DRAW_BODY_ANGLE)
        big = SK_DRAW_BODY_CURVE_R * 4
        wedge = (
            cq.Workplane("XY").moveTo(cx, cy)
            .lineTo(cx + big * math.cos(a0), cy + big * math.sin(a0))
            .lineTo(cx + big * math.cos((a0 + a1) / 2),
                    cy + big * math.sin((a0 + a1) / 2))
            .lineTo(cx + big * math.cos(a1), cy + big * math.sin(a1))
            .close().extrude(h)
        )
        sector = ring.intersect(wedge)
        # Cap at the far end of the elbow, carried through the same transform
        # chain smkent uses (rot180 -> translate -> rotate by the body angle).
        pts = [(0, 0), (thick, 0), (thick, SK_LATCH_EDGE_RADIUS * 1.5),
               (0, SK_LATCH_EDGE_RADIUS * 1.5)]
        pts = _xf(pts, ang=180)
        pts = _xf(pts, tr=(-SK_DRAW_BODY_CURVE_R, 0))
        pts = _xf(pts, ang=SK_DRAW_BODY_ANGLE)
        pts = _xf(pts, tr=(SK_DRAW_BODY_CURVE_R + thick, -thick))
        pts = _xf(pts, tr=(ox, 0))
        cap = cq.Workplane("XY").polyline(pts).close().extrude(h)

        merged = circ.union(sq).union(sector).union(cap)
        # Closing: dilate then erode, rounding the concave junctions.
        r = SK_DRAW_PIN_HANDLE_R * 1.25
        try:
            wires = cq.Workplane("XY").add(merged.faces("<Z").val()).wires()
            return wires.toPending().offset2D(r).offset2D(-r).extrude(h)
        except Exception:
            warnings.warn(
                "%s: could not close the handle curve; junctions stay sharp. "
                "Geometry is otherwise valid." % (self.__class__.__name__,),
                stacklevel=2,
            )
            return merged

    def _grip_curve_radius(self, y):
        """Grip curve radius at position y across the latch width.

        smkent: deg = |y - lw/2| / lw / 2 * 360 * 0.8, radius = cos(deg) * R*0.9.
        Flatter in the middle (14.4mm), tighter at the edges (4.45mm) -- the
        saddle that makes the grip sit in a fingertip.
        """
        lw = self.latch_part_width
        deg = abs(y - lw / 2) / lw / 2 * 360 * 0.8
        return math.cos(math.radians(deg)) * (SK_DRAW_GRIP_CURVE_R * 0.9)

    def _grip_section_wire(self, y):
        """One grip cross-section: a 45 degree arc rib of constant thickness.

        Built from true circular arcs rather than sampled points, so each
        section stays analytic before lofting.
        """
        ler = SK_LATCH_EDGE_RADIUS / 2
        thick = SK_DRAW_THICKNESS
        ang = math.radians(SK_DRAW_GRIP_ANGLE)
        crad = self._grip_curve_radius(y)
        dx = (SK_DRAW_GRIP_CURVE_R - crad) / 2  # smkent _curve_offset_inverse
        dy = -crad

        def arc_pt(radius, a):
            return (radius * math.sin(a) + dx, radius * math.cos(a) + dy)

        r_in, r_out = crad + ler, crad + thick - ler
        return (
            cq.Workplane("XY")
            .moveTo(ler, thick - ler)
            .lineTo(ler, ler)
            .lineTo(*arc_pt(r_in, 0))
            .threePointArc(arc_pt(r_in, ang / 2), arc_pt(r_in, ang))
            .lineTo(*arc_pt(r_out, ang))
            .threePointArc(arc_pt(r_out, ang / 2), arc_pt(r_out, 0))
            .close()
        )

    def _draw_latch_grip_solid(self, sections=15):
        """The grip, lofted through varying cross-sections.

        DELIBERATE DIVERGENCE FROM UPSTREAM, agreed with Jason.

        smkent stacks `draw_latch_poly_div` = 10 polyhedra because OpenSCAD has
        no lofting -- the facets are a workaround, not the design intent. A loft
        produces the smooth surface those facets approximate, which is both
        closer to the intent and better B-Rep for STEP output. Per the project
        rule that upstream is a starting point rather than gospel.
        """
        lw = self.latch_part_width
        wires = []
        for i in range(sections):
            y = lw * i / (sections - 1)
            w = self._grip_section_wire(y).wires().val()
            wires.append(w.moved(cq.Location(cq.Vector(0, 0, y))))
        return cq.Workplane("XY").newObject(
            [cq.Solid.makeLoft(wires, ruled=False)]
        )

    def _placed_grip(self):
        """Grip positioned on the handle, replaying smkent's transform chain.

            translate([eyelet_r, -handle_length - thickness])
            translate([body_curve_r, 0]) rotate(body_angle)
            translate([-body_curve_r, 0]) mirror([1, 0, 0])

        Applied innermost-first, as OpenSCAD does.
        """
        g = self._draw_latch_grip_solid()
        g = g.mirror("YZ")                                   # mirror([1,0,0])
        g = g.translate((-SK_DRAW_BODY_CURVE_R, 0, 0))
        g = g.rotate((0, 0, 0), (0, 0, 1), SK_DRAW_BODY_ANGLE)
        g = g.translate((SK_DRAW_BODY_CURVE_R, 0, 0))
        return g.translate(
            (SK_DRAW_SCREW_EYELET_R,
             -SK_DRAW_HANDLE_LENGTH - SK_DRAW_THICKNESS, 0)
        )

    def render_draw_latch_handle(self):
        """Full handle: lever arm unioned with the elbow, then holes cut.

        Order matters and follows smkent: union first, drill after, so the
        holes are not partly filled by the elbow.
        """
        h = self.latch_part_width
        arm = _wire_from_hull(
            _hull_of_circles(self._draw_latch_handle_hull_circles())
        ).extrude(h)
        curve = self._draw_latch_curve_solid(h).translate(
            (0, -SK_DRAW_HANDLE_LENGTH, 0)
        )
        body = arm.union(curve).union(self._placed_grip())
        pin_hole = (
            cq.Workplane("XY").circle(SK_DRAW_PIN_R + SK_DRAW_SEP).extrude(h)
            .translate((*self._draw_pin_offset, 0))
        )
        screw_d = SK_M3 + SK_SCREW_HOLE_TOL + SK_M3 * 0.2
        screw_hole = cq.Workplane("XY").circle(screw_d / 2).extrude(h)
        r = body.cut(pin_hole).cut(screw_hole)
        return self.repair_if_invalid(r)

    def segment_bands(self, for_handle=False):
        """Z-ranges of the interlocking bands across the latch width.

        smkent splits the width into 5 and keeps the ODD ones (1 and 3). The
        catch KEEPS those bands; the handle SUBTRACTS them, so the two mesh.
        The handle's cut is widened by draw_latch_vsep on each side, which is
        the running clearance between the meshed fingers.
        """
        lw = self.latch_part_width
        seg = lw / SK_DRAW_SEGMENTS
        vsep = SK_DRAW_VSEP if for_handle else 0.0
        return [
            (seg * i - vsep, seg * i + seg + vsep)
            for i in range(SK_DRAW_SEGMENTS)
            if i % 2 == 1
        ]

    def _band_solid(self, bands, size=200.0):
        """Union of slabs spanning the given Z-ranges."""
        out = None
        for z0, z1 in bands:
            slab = (
                cq.Workplane("XY")
                .box(size, size, z1 - z0)
                .translate((0, 0, (z0 + z1) / 2))
            )
            out = slab if out is None else out.union(slab)
        return out

    def render_draw_latch_catch_segmented(self):
        """Catch with only its pin ATTACH cut back to interlocking fingers.

        Regression: this intersected the WHOLE catch with the bands, which cut
        the part into two disconnected fingers -- a catch you could not print.
        The meshing test still passed, because two parts that do not touch
        interfere by exactly zero.

        smkent extrudes body + hook + pin barrel at full width and segments
        only `_draw_latch_attach_shape`. Those flanges are what bridge the pin
        to the body, so the catch stays one solid through the odd bands.
        """
        return self.render_draw_latch_catch(segmented=True)

    def render_draw_latch_handle_segmented(self):
        """Handle with slots cut for the catch's fingers.

        The cut is confined to the catch's own footprint, expanded by
        draw_latch_sep in XY. Cutting full-width slabs instead would sever the
        handle into three disconnected pieces -- the bands are slots, not
        through-cuts.
        """
        handle = self.render_draw_latch_handle()
        catch = self.render_draw_latch_catch()
        # Both parts are prismatic in Z, so an XY offset of the cross-section
        # gives the running clearance without needing a true 3D offset.
        section = catch.faces("<Z").wires().toPending().offset2D(SK_DRAW_SEP)
        region = section.extrude(self.latch_part_width)
        cutter = region.intersect(self._band_solid(self.segment_bands(True)))
        r = handle.cut(cutter)
        return self.repair_if_invalid(r)

    def _draw_latch_pin_attach_circles(self, sep=SK_DRAW_SEP):
        """The catch's pin boss: a hull of three circles at the pin offset.

        This is the part of the catch that reaches across to the handle's
        pivot. Without it the two parts barely overlap, so there is nothing
        for the interlocking slots to be cut from.
        """
        t = SK_DRAW_THICKNESS
        pin_diameter = SK_DRAW_PIN_R - sep / 2
        offset_from_pin = sep + t + SK_DRAW_PIN_HANDLE_R
        size_delta = pin_diameter - t
        px, py = self._draw_pin_offset
        return [
            (px, py, SK_DRAW_PIN_R),
            (px + offset_from_pin, py + offset_from_pin + size_delta, t),
            (px + offset_from_pin, py + offset_from_pin - size_delta, t),
        ]

    def render_draw_latch_pin_attach(self):
        """The catch's pin boss as a solid."""
        circles = self._draw_latch_pin_attach_circles()
        return _wire_from_hull(_hull_of_circles(circles)).extrude(self.latch_part_width)

    def render_draw_latch_catch(self, segmented=False):
        """Catch = stadium body + hook + pin boss, as smkent assembles it.

        `segmented` keeps the pin barrel full width but reduces the attach
        flanges to the interlocking bands -- see
        `render_draw_latch_catch_segmented`.
        """
        h = self.latch_part_width
        body = self.render_draw_latch_catch_body()
        hook = self._draw_latch_hook_solid(h).translate(
            (
                SK_DRAW_SEP,
                self.latch_screw_separation - self.latch_base_size + SK_M3 / 2,
                0,
            )
        )
        px, py = self._draw_pin_offset
        attach = self.render_draw_latch_pin_attach()
        if segmented:
            barrel = (
                cq.Workplane("XY")
                .circle(SK_DRAW_PIN_R)
                .extrude(h)
                .translate((px, py, 0))
            )
            attach = barrel.union(
                attach.intersect(self._band_solid(self.segment_bands(False)))
            )
        r = body.union(hook).union(attach)
        # Pin centre hole: smkent drills (pin_r + sep) / 5 through the joint.
        centre_hole = (
            cq.Workplane("XY")
            .circle((SK_DRAW_PIN_R + SK_DRAW_SEP) / 5)
            .extrude(h)
            .translate((px, py, 0))
        )
        return self.repair_if_invalid(r.cut(centre_hole))

    def render_draw_latch_catch_body(self):
        """The catch's main body, before the hook is added.

        Built with the exact hull-of-circles primitive rather than an
        approximation, so the end caps stay true arcs.
        """
        circles = self._draw_latch_catch_body_circles()
        wire = _wire_from_hull(_hull_of_circles(circles))
        return wire.extrude(self.latch_part_width)

    def render_draw_latch(self, open_angle=0.0):
        """The draw latch as the TWO printed parts it is -- `_draw_latch_part`.

        Handle and catch are separate prints joined by an M3 through the pin,
        so this returns a compound rather than pretending they are one solid.
        `open_angle` swings the catch about the pin, as upstream's preview
        does; 0 is the closed, over-centre position.
        """
        handle = self.render_draw_latch_handle_segmented()
        catch = self.render_draw_latch_catch_segmented()
        if abs(open_angle) > EPS:
            px, py = self._draw_pin_offset
            catch = catch.rotate((px, py, 0), (px, py, 1), -open_angle)
        return cq.Workplane("XY").newObject(
            [cq.Compound.makeCompound(handle.vals() + catch.vals())]
        )

    def render_latch(self, open_angle=0.0):
        """The latch, whichever style is selected.

        The clip latch is one flexing part; the draw latch is two, which is
        why this can return a compound. `open_angle` applies to the draw
        latch only.
        """
        if self.latch_type == "draw":
            r = self.render_draw_latch(open_angle=open_angle)
        else:
            r = self._clip_latch_solid(self.latch_part_width)
            r = self._break_extruded_edges(r)
            r = self.repair_if_invalid(r)
        self._cq_obj = r
        self._obj_label = "latch"
        return r

    def render(self):
        """Default render is the box body."""
        return self.render_body()

    # -- per-part output ---------------------------------------------------

    def parts(self):
        """Every printable part of this box, as {label: Workplane}.

        A rugged box is not one model: it is a body, a lid, and N latches,
        each printed separately and assembled with M3 hardware. Rendering
        only `render()` gives you a third of the object.
        """
        out = {
            "body": self.render_body(),
            "lid": self.render_lid(),
        }
        if self.latch_type == "draw":
            out["latch_handle"] = self.render_draw_latch_handle_segmented()
            out["latch_catch"] = self.render_draw_latch_catch_segmented()
        else:
            out["latch"] = self.render_latch()
        return out

    def save_step_parts(self, path=".", prefix=None):
        """Write every part to its own STEP file. Returns the paths written."""
        import os

        written = []
        base = prefix if prefix is not None else self.filename()
        for label, shape in self.parts().items():
            self._cq_obj = shape
            self._obj_label = label
            fn = os.path.join(path, "%s_%s.step" % (base, label))
            cq.exporters.export(shape, fn)
            written.append(fn)
        return written

    def bom(self):
        """Screws this box needs -- smkent `rbox_bom()`.

        Every attachment is an M3 through a pair of eyelets: one per latch,
        one per hinge, and the third hinge adds one more when it activates.
        """
        latches = len(self.attachment_positions(hinge=False))
        hinges = len(self.attachment_positions(hinge=True))
        return {
            "M3x40 DIN 912 (latch)": latches,
            "M3x40 DIN 912 (hinge)": hinges,
            "latch assemblies": latches,
        }

    # -- naming -----------------------------------------------------------

    @property
    def _filename_prefix(self) -> str:
        return "gf_ruggedbox_sk_"

    def _filename_suffix(self) -> str:
        fn = "x%s" % self._fmt_unit(self.height_u)
        fn += "_%s" % self.latch_type
        bp = "-".join(
            n
            for n, on in (
                ("mag", self.baseplate_magnets),
                ("skel", self.baseplate_skeletonized),
            )
            if on
        )
        if bp:
            fn += "_bp-%s" % bp
        if abs(self.size_tolerance - SK_SIZE_TOL) > 1e-6:
            fn += "_tol%.2f" % self.size_tolerance
        return fn
