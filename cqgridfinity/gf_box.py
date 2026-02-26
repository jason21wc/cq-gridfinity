#! /usr/bin/env python3
#
# Copyright (C) 2023  Michael Gale
# This file is part of the cq-gridfinity python module.
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# Gridfinity Boxes

import math

import cadquery as cq
from cqkit import HasZCoordinateSelector, VerticalEdgeSelector, FlatEdgeSelector
from cqkit.cq_helpers import rounded_rect_sketch, composite_from_pts
from cqgridfinity import *
from cqgridfinity.gf_wall_pattern import make_wall_pattern


class GridfinityBox(GridfinityObject):
    """Gridfinity Box

    This class represents a Gridfinity compatible box module. As a minimum,
    this class is initialized with basic 3D unit dimensions for length,
    width, and height.  length and width are multiples of 42 mm Gridfinity
    intervals and height represents multiples of 7 mm.

    Many box features can be enabled with attributes provided either as
    keywords or direct dotted access.  These attributes include:
    - solid :   renders the box without an interior, i.e. a solid block. This
                is useful for making custom Gridfinity modules by subtracting
                out shapes from the solid interior. Normally, the box is
                rendered solid up to its maximum size; however, the
                solid_ratio attribute can specify a solid fill of between
                0.0 to 1.0, i.e. 0 to 100% fill.
    - holes : adds bottom mounting holes for magnets or screws
    - scoops : adds a radiused bottom edge to the interior to help fetch
               parts from the box
    - labels : adds a flat flange along each compartment for adding a label
    - no_lip : removes the contoured lip on the top module used for stacking
    - length_div, width_div : subdivides the box into sub-compartments in
                 length and/or width.
    - lite_style : render box as an economical shell without elevated floor
    - unsupported_holes : render bottom holes as 3D printer friendly versions
                          which can be printed without supports
    - label_width : width of top label ledge face overhang
    - label_height : height of label ledge overhang
    - scoop_rad : radius of the bottom scoop feature
    - wall_th : wall thickness
    - hole_diam : magnet/counterbore bolt hole diameter

    """

    def __init__(self, length_u, width_u, height_u, **kwargs):
        super().__init__()
        self.length_u = length_u
        self.width_u = width_u
        self.height_u = height_u
        self.length_div = 0
        self.width_div = 0
        self.scoops = False
        self.labels = False
        self.solid = False
        self.holes = False
        self.no_lip = False
        self.lip_style = "normal"
        self.solid_ratio = 1.0
        self.lite_style = False
        self.unsupported_holes = False
        self.label_width = 12  # width of the label strip
        self.label_height = 10  # thickness of label overhang
        self.label_lip_height = 0.8  # thickness of label vertical lip
        self.scoop_rad = 14  # radius of optional interior scoops
        self.fillet_interior = True
        self.fillet_rad = None  # user-configurable interior fillet (None = use default)
        self.wall_th = GR_WALL
        self.hole_diam = GR_HOLE_D  # magnet/bolt hole diameter
        self.wall_pattern = False  # enable wall pattern cutouts
        self.wall_pattern_style = "hexgrid"  # "hexgrid" or "grid"
        self.wall_pattern_cell = GR_PAT_CELL  # hole size (mm)
        self.wall_pattern_spacing = GR_PAT_SPACING  # web thickness (mm)
        self.wall_pattern_sides = GR_PAT_SIDES  # polygon sides
        self.wall_pattern_walls = (True, True, True, True)  # front, back, left, right
        self.thumbscrew = False  # add thumbscrew hole in front wall
        self.thumbscrew_diam = 4.0  # thumbscrew clearance hole diameter (mm)
        self.vase_mode = False  # single-wall construction for slicer spiralize
        for k, v in kwargs.items():
            if k in self.__dict__:
                self.__dict__[k] = v
        # Backward compat: no_lip=True maps to lip_style="none"
        if self.no_lip and self.lip_style == "normal":
            self.lip_style = "none"
        # Vase mode forces no-lip, no interior features
        if self.vase_mode:
            self.lip_style = "none"
            self.scoops = False
            self.labels = False
            self.holes = False
            self.length_div = 0
            self.width_div = 0
            self.solid = False
            self.wall_pattern = False
        if self.lip_style not in ("normal", "reduced", "none"):
            raise ValueError(
                "lip_style must be 'normal', 'reduced', or 'none', "
                "got '%s'" % self.lip_style
            )
        self._int_shell = None
        self._ext_shell = None

    def __str__(self):
        s = []
        s.append(
            "Gridfinity Box %dU x %dU x %dU (%.2f x %.2f x %.2f mm)"
            % (
                self.length_u,
                self.width_u,
                self.height_u,
                self.length - GR_TOL,
                self.width - GR_TOL,
                self.height,
            )
        )
        lip_desc = {
            "normal": "with mating top lip",
            "reduced": "with reduced top lip",
            "none": "no mating top lip",
        }
        sl = lip_desc.get(self.lip_style, "with mating top lip")
        ss = "Lite style box  " if self.lite_style else ""
        s.append("  %sWall thickness: %.2f mm  %s" % (ss, self.wall_th, sl))
        s.append(
            "  Floor height  : %.2f mm  Inside height: %.2f mm  Top reference height: %.2f mm"
            % (self.floor_h + GR_BASE_HEIGHT, self.int_height, self.top_ref_height)
        )
        if self.solid:
            s.append("  Solid filled box with fill ratio %.2f" % (self.solid_ratio))
        if self.holes:
            s.append("  Bottom mounting holes with %.2f mm diameter" % (self.hole_diam))
            if self.unsupported_holes:
                s.append("  Holes are 3D printer friendly and can be unsupported")
        if self.scoops:
            s.append("  Lengthwise scoops with %.2f mm radius" % (self.scoop_rad))
        if self.labels:
            s.append(
                "  Lengthwise label shelf %.2f mm wide with %.2f mm overhang"
                % (self.label_width, self.label_height)
            )
        if self.length_div:
            xl = (self.inner_l - GR_DIV_WALL * (self.length_div)) / (
                self.length_div + 1
            )
            s.append(
                "  %dx lengthwise divisions for %.2f mm compartment lengths"
                % (self.length_div, xl)
            )
        if self.width_div:
            yl = (self.inner_w - GR_DIV_WALL * (self.width_div)) / (self.width_div + 1)
            s.append(
                "  %dx widthwise divisions for %.2f mm compartment widths"
                % (self.width_div, yl)
            )
        s.append("  Auto filename: %s" % (self.filename()))
        return "\n".join(s)

    def render(self):
        """Returns a CadQuery Workplane object representing this Gridfinity box."""
        self._int_shell = None
        if self.lite_style:
            # just force the dividers to the desired quantity in both dimensions
            # rather than raise a exception
            if self.length_div:
                self.length_div = self.length_u - 1
            if self.width_div:
                self.width_div = self.width_u - 1
            if self.solid:
                raise ValueError(
                    "Cannot select both solid and lite box styles together"
                )
            if self.holes:
                raise ValueError(
                    "Cannot select both holes and lite box styles together"
                )
            if self.wall_th > 1.5:
                raise ValueError(
                    "Wall thickness cannot exceed 1.5 mm for lite box style"
                )
        if self.wall_th > 2.5:
            raise ValueError("Wall thickness cannot exceed 2.5 mm")
        if self.wall_th < 0.5:
            raise ValueError("Wall thickness must be at least 0.5 mm")
        if self.vase_mode:
            return self.render_vase_mode()
        r = self.render_shell()
        rd = self.render_dividers()
        rs = self.render_scoops()
        rl = self.render_labels()
        for e in (rd, rl, rs):
            if e is not None:
                r = r.union(e)
        if not self.solid and self.fillet_interior:
            heights = [GR_FLOOR]
            if self.labels:
                heights.append(self.safe_label_height(backwall=True, from_bottom=True))
                heights.append(self.safe_label_height(backwall=False, from_bottom=True))
            bs = (
                HasZCoordinateSelector(heights, min_points=1, tolerance=0.5)
                + VerticalEdgeSelector(">5")
                - HasZCoordinateSelector("<%.2f" % (self.floor_h))
            )
            if self.lite_style and self.scoops:
                bs = bs - HasZCoordinateSelector("<=%.2f" % (self.floor_h))
                bs = bs - VerticalEdgeSelector()
            r = self.safe_fillet(r, bs, self.safe_fillet_rad)

            if self.lite_style and not self.has_dividers:
                bs = FlatEdgeSelector(self.floor_h)
                if self.wall_th < 1.2:
                    r = self.safe_fillet(r, bs, 0.5)
                elif self.wall_th < 1.25:
                    r = self.safe_fillet(r, bs, 0.25)

            if not self.labels and self.has_dividers:
                bs = VerticalEdgeSelector(
                    GR_TOPSIDE_H, tolerance=0.05
                ) & HasZCoordinateSelector(GRHU * self.height_u - GR_BASE_HEIGHT)
                r = self.safe_fillet(r, bs, GR_TOPSIDE_H - EPS)

        if self.holes:
            r = self.render_holes(r)
        r = r.translate((-self.half_l, -self.half_w, GR_BASE_HEIGHT))
        if self.unsupported_holes:
            r = self.render_hole_fillers(r)
        if self.wall_pattern and not self.solid:
            r = self.render_wall_patterns(r)
        if self.thumbscrew and not self.solid:
            r = self.render_thumbscrew(r)
        return r

    @property
    def top_ref_height(self):
        """The height of the top surface of a solid box or the floor
        height of an empty box."""
        if self.solid:
            return self.max_height * self.solid_ratio + GR_BOT_H
        if self.lite_style:
            return self.floor_h
        return GR_BOT_H

    @property
    def bin_height(self):
        return self.height - GR_BASE_HEIGHT

    def safe_label_height(self, backwall=False, from_bottom=False):
        lw = self.label_width
        if backwall:
            lw += self.lip_width
        lh = self.label_height * (lw / self.label_width)
        yl = self.max_height - self.label_height + self.wall_th
        if backwall:
            yl -= self.lip_width
        if yl < 0:
            lh = self.max_height - 1.5 * GR_FILLET - 0.1
        elif yl < 1.5 * GR_FILLET:
            lh -= 1.5 * GR_FILLET - yl + 0.1
        if from_bottom:
            ws = math.sin(math.atan2(self.label_height, self.label_width))
            if backwall:
                lh = self.max_height + GR_FLOOR - lh + ws * self.wall_th
            else:
                lh = self.max_height + GR_FLOOR - lh + ws * GR_DIV_WALL
        return lh

    @property
    def has_dividers(self):
        return self.length_div > 0 or self.width_div > 0

    @property
    def interior_solid(self):
        if self._int_shell is not None:
            return self._int_shell
        self._int_shell = self.render_interior()
        return self._int_shell

    def render_interior(self, force_solid=False):
        """Renders the interior cutting solid of the box."""
        wall_u = self.wall_th - GR_WALL
        wall_h = self.int_height + wall_u
        under_h = ((GR_UNDER_H - wall_u) * SQRT2, 45)
        if self.lip_style == "none":
            profile = GR_NO_PROFILE
        elif self.lip_style == "reduced":
            profile = [under_h, *GR_REDUCED_LIP_PROFILE[1:]]
        else:
            profile = [under_h, *GR_LIP_PROFILE[1:]]
        profile = [wall_h, *profile]
        if self.int_height < 0:
            profile = [self.height - GR_BOT_H]
        rci = self.extrude_profile(
            rounded_rect_sketch(*self.inner_dim, self.inner_rad), profile
        )
        rci = rci.translate((*self.half_dim, self.floor_h))
        if self.solid or force_solid:
            hs = self.max_height * self.solid_ratio
            ri = rounded_rect_sketch(*self.inner_dim, self.inner_rad)
            rf = cq.Workplane("XY").placeSketch(ri).extrude(hs)
            rf = rf.translate((*self.half_dim, self.floor_h))
            rci = rci.cut(rf)
        if self.scoops and self.lip_style != "none" and not self.lite_style:
            rf = (
                cq.Workplane("XY")
                .rect(self.inner_l, 2 * self.under_h)
                .extrude(self.max_height)
                .translate((self.half_l, -self.half_in, self.floor_h))
            )
            rci = rci.cut(rf)
        if self.lite_style:
            r = composite_from_pts(self.base_interior(), self.grid_centres)
            rci = rci.union(r)
        return rci

    def solid_shell(self):
        """Returns a completely solid box object useful for intersecting with other solids."""
        if self._ext_shell is not None:
            return self._ext_shell
        r = self.render_shell(as_solid=True)
        self._ext_shell = r.cut(self.render_interior(force_solid=True))
        return self._ext_shell

    def mask_with_obj(self, obj):
        """Intersects a solid object with this box."""
        return obj.intersect(self.solid_shell())

    def base_interior(self):
        profile = [GR_BASE_HEIGHT, *GR_BOX_PROFILE]
        zo = GR_BASE_HEIGHT + GR_BASE_CLR
        if self.int_height < 0:
            h = self.bin_height - GR_BASE_HEIGHT
            profile = [h, *profile]
            zo += h
        r = self.extrude_profile(
            rounded_rect_sketch(GRU - GR_TOL, GRU - GR_TOL, self.outer_rad),
            profile,
        )
        rx = r.faces("<Z").shell(-self.wall_th)
        r = r.cut(rx).mirror(mirrorPlane="XY").translate((0, 0, zo))
        return r

    def render_shell(self, as_solid=False):
        """Renders the box shell without any added features."""
        r = self.extrude_profile(
            rounded_rect_sketch(GRU, GRU, self.outer_rad + GR_BASE_CLR), GR_BOX_PROFILE
        )
        r = r.translate((0, 0, -GR_BASE_CLR))
        r = r.mirror(mirrorPlane="XY")
        r = composite_from_pts(r, self.grid_centres)
        rs = rounded_rect_sketch(*self.outer_dim, self.outer_rad)
        rw = (
            cq.Workplane("XY")
            .placeSketch(rs)
            .extrude(self.bin_height - GR_BASE_CLR)
            .translate((*self.half_dim, GR_BASE_CLR))
        )
        rc = (
            cq.Workplane("XY")
            .placeSketch(rs)
            .extrude(-GR_BASE_HEIGHT - 1)
            .translate((*self.half_dim, 0.5))
        )
        rc = rc.intersect(r).union(rw)
        if not as_solid:
            return rc.cut(self.interior_solid)
        return rc

    def render_dividers(self):
        r = None
        if self.length_div > 0 and not self.solid:
            wall_w = (
                cq.Workplane("XY")
                .rect(GR_DIV_WALL, self.outer_w)
                .extrude(self.max_height)
                .translate((0, 0, self.floor_h))
            )
            xl = self.inner_l / (self.length_div + 1)
            pts = [
                ((x + 1) * xl - self.half_in, self.half_w)
                for x in range(self.length_div)
            ]
            r = composite_from_pts(wall_w, pts)

        if self.width_div > 0 and not self.solid:
            wall_l = (
                cq.Workplane("XY")
                .rect(self.outer_l, GR_DIV_WALL)
                .extrude(self.max_height)
                .translate((0, 0, self.floor_h))
            )
            yl = self.inner_w / (self.width_div + 1)
            pts = [
                (self.half_l, (y + 1) * yl - self.half_in)
                for y in range(self.width_div)
            ]
            rw = composite_from_pts(wall_l, pts)
            if r is not None:
                r = r.union(rw)
            else:
                r = rw
        return r

    def render_scoops(self):
        if not self.scoops or self.solid:
            return None
        # front wall scoop
        # prevent the scoop radius exceeding the internal height
        srad = min(self.scoop_rad, self.int_height - 0.1)
        rs = cq.Sketch().rect(srad, srad).vertices(">X and >Y").circle(srad, mode="s")
        rsc = cq.Workplane("YZ").placeSketch(rs).extrude(self.inner_l)
        rsc = rsc.translate((0, 0, srad / 2 + GR_FLOOR))
        yo = -self.half_in + srad / 2
        # offset front wall scoop by top lip overhang if applicable
        if self.lip_style != "none" and not self.lite_style:
            yo += self.under_h
        zo = -GR_BOT_H + self.wall_th if self.lite_style else 0
        rs = rsc.translate((-self.half_in, yo, zo))
        # intersect to prevent solids sticking out of rounded corners
        r = rs.intersect(self.interior_solid)
        if self.width_div > 0:
            # add scoops along each internal dividing wall in the width dimension
            yl = self.inner_w / (self.width_div + 1)
            pts = [
                (-self.half_in, (y + 1) * yl - self.half_in)
                for y in range(self.width_div)
            ]
            rs = composite_from_pts(rsc, pts)
            r = r.union(rs.translate((0, GR_DIV_WALL / 2 + srad / 2, zo)))
            r = r.intersect(self.render_shell(as_solid=True))
        return r

    def render_labels(self):
        if not self.labels or self.solid:
            return None
        # back wall label flange with compensated width and height
        lw = self.label_width + self.lip_width
        rs = (
            cq.Sketch()
            .segment((0, 0), (lw, 0))
            .segment((lw, -self.safe_label_height(backwall=True)))
            .segment((0, -self.label_lip_height))
            .close()
            .assemble()
            .vertices("<X")
            .vertices("<Y")
            .fillet(self.label_lip_height / 2)
        )
        rsc = cq.Workplane("YZ").placeSketch(rs).extrude(self.inner_l)
        yo = -lw + self.outer_w / 2 + self.half_w + self.wall_th / 4
        rs = rsc.translate((-self.half_in, yo, self.floor_h + self.max_height))
        # intersect to prevent solids sticking out of rounded corners
        r = rs.intersect(self.interior_solid)
        if self.width_div > 0:
            # add label flanges along each dividing wall
            rs = (
                cq.Sketch()
                .segment((0, 0), (self.label_width, 0))
                .segment((self.label_width, -self.safe_label_height(backwall=False)))
                .segment((0, -self.label_lip_height))
                .close()
                .assemble()
                .vertices("<X")
                .vertices("<Y")
                .fillet(self.label_lip_height / 2)
            )
            rsc = cq.Workplane("YZ").placeSketch(rs).extrude(self.inner_l)
            rsc = rsc.translate((0, -self.label_width, self.floor_h + self.max_height))
            yl = self.inner_w / (self.width_div + 1)
            pts = [
                (-self.half_in, (y + 1) * yl - self.half_in + GR_DIV_WALL / 2)
                for y in range(self.width_div)
            ]
            r = r.union(composite_from_pts(rsc, pts))
        return r

    def render_holes(self, obj):
        if not self.holes:
            return obj
        h = GR_HOLE_H
        if self.unsupported_holes:
            h += GR_HOLE_SLICE
        return (
            obj.faces("<Z")
            .workplane()
            .pushPoints(self.hole_centres)
            .cboreHole(GR_BOLT_D, self.hole_diam, h, depth=GR_BOLT_H)
        )

    def render_vase_mode(self):
        """Render a vase-mode (spiralize) compatible bin.

        Creates a single-walled, open-top bin with standard Gridfinity base
        profile for stacking compatibility. The slicer's vase/spiral mode
        handles turning this into a continuous single-perimeter print.

        Construction:
        1. Standard base profile per grid cell (for baseplate mating)
        2. Thin-walled enclosure from floor to top (no lip, no floor fill)
        """
        # 1. Build the standard base footprint (same as normal box)
        r = self.extrude_profile(
            rounded_rect_sketch(GRU, GRU, self.outer_rad + GR_BASE_CLR),
            GR_BOX_PROFILE,
        )
        r = r.translate((0, 0, -GR_BASE_CLR))
        r = r.mirror(mirrorPlane="XY")
        r = composite_from_pts(r, self.grid_centres)
        rs = rounded_rect_sketch(*self.outer_dim, self.outer_rad)
        # Outer block: base to bin top
        rw = (
            cq.Workplane("XY")
            .placeSketch(rs)
            .extrude(self.bin_height - GR_BASE_CLR)
            .translate((*self.half_dim, GR_BASE_CLR))
        )
        rc = (
            cq.Workplane("XY")
            .placeSketch(rs)
            .extrude(-GR_BASE_HEIGHT - 1)
            .translate((*self.half_dim, 0.5))
        )
        outer = rc.intersect(r).union(rw)

        # 2. Cut interior — simple box offset by wall_th, from floor to top
        # (no lip profile, no elevated floor — just a thin shell)
        ri_sketch = rounded_rect_sketch(*self.inner_dim, self.inner_rad)
        inner = (
            cq.Workplane("XY")
            .placeSketch(ri_sketch)
            .extrude(self.bin_height)
            .translate((*self.half_dim, self.floor_h))
        )
        r = outer.cut(inner)

        # 3. Translate to centered coordinates (same as normal render)
        r = r.translate((-self.half_l, -self.half_w, GR_BASE_HEIGHT))
        return r

    def render_thumbscrew(self, obj):
        """Cut a thumbscrew clearance hole through the front wall of the bin.

        After the main translate, the bin is centered at XY origin with Z=0
        at the base bottom. The front wall outer face is at Y = -outer_w/2.
        One hole per grid unit, centered on each cell at floor height.
        """
        rad = self.thumbscrew_diam / 2
        oy = self.outer_w
        # Hole at floor height (just above base profile)
        z_hole = GR_BASE_HEIGHT + GR_FLOOR + rad + 1.0
        # XZ workplane: extrude(+) goes -Y, extrude(-) goes +Y
        # We need +Y (inward from front wall), so use negative extrude
        cut_depth = self.wall_th * 3
        # One hole per grid unit along X
        for i in range(self.length_u):
            x = (i - (self.length_u - 1) / 2) * GRU
            hole = (
                cq.Workplane("XZ")
                .center(x, z_hole)
                .circle(rad)
                .extrude(-cut_depth)
                .translate((0, -oy / 2 - EPS, 0))
            )
            obj = obj.cut(hole)
        return obj

    def render_hole_fillers(self, obj):
        rc = (
            cq.Workplane("XY")
            .rect(self.hole_diam / 2, self.hole_diam)
            .extrude(GR_HOLE_SLICE)
        )
        xo = self.hole_diam / 2
        rs = composite_from_pts(rc, [(-xo, 0, GR_HOLE_H), (xo, 0, GR_HOLE_H)])
        rs = composite_from_pts(rs, self.hole_centres)
        return obj.union(rs.translate((-self.half_l, self.half_w, 0)))

    def render_wall_patterns(self, obj):
        """Cut wall patterns into the exterior walls of the bin.

        After the main render translate, the bin is centered at XY origin
        with Z=0 at the bottom of the base. Pattern canvas is inset from
        corners, floor, and lip to avoid cutting into structural features.
        """
        # Pattern area vertical bounds (in the translated coordinate system)
        z_bot = GR_BASE_HEIGHT + GR_PAT_FLOOR_CLR
        z_top = self.height - GR_PAT_LIP_CLR
        if self.lip_style == "none":
            z_top = self.height - 1.0  # small margin for no-lip
        elif self.lip_style == "reduced":
            z_top = self.height - GR_PAT_LIP_CLR + 0.6
        canvas_h = z_top - z_bot
        if canvas_h < self.wall_pattern_cell:
            return obj

        # Outer dimensions (centered at origin after translate)
        ox = self.outer_l  # length_u * GRU - GR_TOL
        oy = self.outer_w  # width_u * GRU - GR_TOL
        inset = GR_PAT_CORNER_INSET
        depth = self.wall_th + EPS  # cut fully through wall

        front, back, left, right = self.wall_pattern_walls

        # Front/back walls run along X axis
        canvas_x = ox - 2 * inset
        if canvas_x >= self.wall_pattern_cell:
            pat_fb = make_wall_pattern(
                canvas_x, canvas_h, depth,
                style=self.wall_pattern_style,
                cell_size=self.wall_pattern_cell,
                spacing=self.wall_pattern_spacing,
                sides=self.wall_pattern_sides,
            )
            if pat_fb is not None:
                z_mid = (z_bot + z_top) / 2
                if front:
                    # Front wall: Y = -oy/2, pattern on YZ plane
                    pf = (
                        pat_fb
                        .rotate((0, 0, 0), (1, 0, 0), 90)
                        .translate((0, -oy / 2 + depth / 2 - EPS, z_mid))
                    )
                    obj = obj.cut(pf)
                if back:
                    pb = (
                        pat_fb
                        .rotate((0, 0, 0), (1, 0, 0), 90)
                        .translate((0, oy / 2 - depth / 2 + EPS, z_mid))
                    )
                    obj = obj.cut(pb)

        # Left/right walls run along Y axis
        canvas_y = oy - 2 * inset
        if canvas_y >= self.wall_pattern_cell:
            pat_lr = make_wall_pattern(
                canvas_y, canvas_h, depth,
                style=self.wall_pattern_style,
                cell_size=self.wall_pattern_cell,
                spacing=self.wall_pattern_spacing,
                sides=self.wall_pattern_sides,
            )
            if pat_lr is not None:
                z_mid = (z_bot + z_top) / 2
                if left:
                    pl = (
                        pat_lr
                        .rotate((0, 0, 0), (1, 0, 0), 90)
                        .rotate((0, 0, 0), (0, 0, 1), 90)
                        .translate((-ox / 2 + depth / 2 - EPS, 0, z_mid))
                    )
                    obj = obj.cut(pl)
                if right:
                    pr = (
                        pat_lr
                        .rotate((0, 0, 0), (1, 0, 0), 90)
                        .rotate((0, 0, 0), (0, 0, 1), 90)
                        .translate((ox / 2 - depth / 2 + EPS, 0, z_mid))
                    )
                    obj = obj.cut(pr)

        return obj


class GridfinitySolidBox(GridfinityBox):
    """Convenience class to represent a solid Gridfinity box."""

    def __init__(self, length_u, width_u, height_u, **kwargs):
        super().__init__(length_u, width_u, height_u, **kwargs, solid=True)
