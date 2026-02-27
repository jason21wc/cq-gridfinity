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
# Gridfinity Baseplates

import cadquery as cq

from cqgridfinity import *
from cqkit.cq_helpers import (
    rounded_rect_sketch,
    composite_from_pts,
    rotate_x,
    recentre,
)
from cqkit import VerticalEdgeSelector, HasZCoordinateSelector


class GridfinityBaseplate(GridfinityObject):
    """Gridfinity Baseplate

    This class represents a Gridfinity baseplate object with optional
    magnet holes, screw holes, and weighted bottom.

      length_u - length in U (42 mm / U)
      width_u - width in U (42 mm / U)
      ext_depth - extrude bottom face by an extra amount in mm
      straight_bottom - remove bottom chamfer and replace with straight side
      corner_screws - add countersink mounting screws to the inside corners
      corner_tab_size - size of mounting screw corner tabs
      csk_hole - mounting screw hole diameter
      csk_diam - mounting screw countersink diameter
      csk_angle - mounting screw countersink angle
      magnet_holes - add magnet recesses in receptacle floors (6.5mm dia, 2.4mm deep)
      screw_holes - add screw through-holes in receptacle floors (3.0mm dia)
      weighted - add weight pockets in baseplate bottom
    """

    def __init__(self, length_u, width_u, **kwargs):
        super().__init__()
        self.length_u = length_u
        self.width_u = width_u
        self.ext_depth = 0
        self.straight_bottom = False
        self.corner_screws = False
        self.corner_tab_size = 21
        self.csk_hole = 5.0
        self.csk_diam = 10.0
        self.csk_angle = 82
        self.magnet_holes = False
        self.screw_holes = False
        self.weighted = False
        for k, v in kwargs.items():
            if k in self.__dict__ and v is not None:
                self.__dict__[k] = v
        # Auto-adjust ext_depth to ensure enough material for features
        if self.weighted:
            self.ext_depth = max(self.ext_depth, GR_BP_BOT_H)
        elif self.magnet_holes and self.screw_holes:
            self.ext_depth = max(self.ext_depth, GR_HOLE_H + 4.0)
        elif self.magnet_holes:
            self.ext_depth = max(self.ext_depth, GR_HOLE_H)
        elif self.screw_holes:
            self.ext_depth = max(self.ext_depth, 4.0)
        if self.corner_screws:
            self.ext_depth = max(self.ext_depth, 5.0)

    @property
    def _has_bottom_features(self):
        """True if this baseplate needs a solid slab below the receptacle."""
        return self.magnet_holes or self.screw_holes or self.weighted

    @property
    def _bp_cell_centres(self):
        """Grid cell centres in the baseplate coordinate system (centered)."""
        return [
            (
                (i - (self.length_u - 1) / 2) * GRU,
                (j - (self.width_u - 1) / 2) * GRU,
            )
            for i in range(self.length_u)
            for j in range(self.width_u)
        ]

    @property
    def _bp_hole_centres(self):
        """Magnet/screw hole positions in the baseplate coordinate system (centered).
        Four holes per grid cell at corners, offset GR_HOLE_DIST from cell centre."""
        return [
            (
                (i - (self.length_u - 1) / 2) * GRU + GR_HOLE_DIST * di,
                (j - (self.width_u - 1) / 2) * GRU + GR_HOLE_DIST * dj,
            )
            for i in range(self.length_u)
            for j in range(self.width_u)
            for di in (-1, 1)
            for dj in (-1, 1)
        ]

    def _corner_pts(self):
        oxy = self.corner_tab_size / 2
        return [
            (i * (self.length / 2 - oxy), j * (self.width / 2 - oxy), 0)
            for i in (-1, 1)
            for j in (-1, 1)
        ]

    def render(self):
        profile = GR_BASE_PROFILE if not self.straight_bottom else GR_STR_BASE_PROFILE
        total_h = GR_BASE_HEIGHT + self.ext_depth
        if self._has_bottom_features and self.ext_depth > 0:
            # For features that need solid material below the receptacle:
            # DON'T extend the receptacle profile. Instead, keep the standard
            # profile depth and let the outer block provide a solid slab below.
            # The receptacle sits on top of the slab at Z=ext_depth.
            rc = self.extrude_profile(
                rounded_rect_sketch(GRU_CUT, GRU_CUT, GR_RAD), profile
            )
            rc = rotate_x(rc, 180).translate(
                (GRU2, GRU2, total_h)
            )
        else:
            # Original behavior: extend the receptacle profile with ext_depth
            if self.ext_depth > 0:
                profile = [*profile, self.ext_depth]
            rc = self.extrude_profile(
                rounded_rect_sketch(GRU_CUT, GRU_CUT, GR_RAD), profile
            )
            rc = rotate_x(rc, 180).translate(
                (GRU2, GRU2, total_h)
            )
        rc = recentre(composite_from_pts(rc, self.grid_centres), "XY")
        r = (
            cq.Workplane("XY")
            .rect(self.length, self.width)
            .extrude(total_h)
            .edges("|Z")
            .fillet(GR_RAD)
            .faces(">Z")
            .cut(rc)
        )
        if self.corner_screws:
            rs = cq.Sketch().rect(self.corner_tab_size, self.corner_tab_size)
            rs = cq.Workplane("XY").placeSketch(rs).extrude(self.ext_depth)
            rs = rs.faces(">Z").cskHole(
                self.csk_hole, cskDiameter=self.csk_diam, cskAngle=self.csk_angle
            )
            r = r.union(recentre(composite_from_pts(rs, self._corner_pts()), "XY"))
            bs = VerticalEdgeSelector(self.ext_depth) & HasZCoordinateSelector(0)
            r = r.edges(bs).fillet(GR_RAD)
        if self.magnet_holes or self.screw_holes:
            r = self._render_baseplate_holes(r)
        if self.weighted:
            r = self._render_weight_pockets(r)
        return r

    def _render_baseplate_holes(self, obj):
        """Cut magnet and/or screw holes into the solid slab below receptacles.

        The receptacle floor is at Z=ext_depth. Below it is a solid slab
        from Z=0 to Z=ext_depth where holes are cut.
        Magnet recesses are blind holes from the floor downward.
        Screw holes pass through the remaining material to the bottom.
        """
        pts = self._bp_hole_centres
        if self.magnet_holes:
            # Magnet recesses: 6.5mm dia, 2.4mm deep from receptacle floor
            mag = (
                cq.Workplane("XY")
                .circle(GR_HOLE_D / 2)
                .extrude(GR_HOLE_H + EPS)
                .translate((0, 0, self.ext_depth - GR_HOLE_H))
            )
            holes = composite_from_pts(mag, [(x, y, 0) for x, y in pts])
            obj = obj.cut(holes)
        if self.screw_holes:
            # Screw through-holes: 3.0mm dia from bottom to receptacle floor
            # (or to bottom of magnet recess if both enabled)
            top = self.ext_depth - GR_HOLE_H if self.magnet_holes else self.ext_depth
            screw = (
                cq.Workplane("XY")
                .circle(GR_BOLT_D / 2)
                .extrude(top + EPS)
            )
            holes = composite_from_pts(screw, [(x, y, 0) for x, y in pts])
            obj = obj.cut(holes)
        return obj

    def _render_weight_pockets(self, obj):
        """Cut weight pockets from the bottom of a weighted baseplate.

        Each grid cell gets a square pocket (21.4mm, 4mm deep) for inserting
        weights (coins, steel plates), plus cross-shaped channels for screw
        access.
        """
        # Main square weight pocket, offset slightly below Z=0 to avoid coplanar face issues
        pocket = (
            cq.Workplane("XY")
            .rect(GR_BP_CUT_SIZE, GR_BP_CUT_SIZE)
            .extrude(GR_BP_CUT_DEPTH + EPS)
            .translate((0, 0, -EPS))
        )
        # Cross channels for screw access (perpendicular slots)
        chan_x = (
            cq.Workplane("XY")
            .rect(GR_BP_RCUT_L * 2 + GR_BP_CUT_SIZE, GR_BP_RCUT_W)
            .extrude(GR_BP_RCUT_D + EPS)
            .translate((0, 0, -EPS))
        )
        chan_y = (
            cq.Workplane("XY")
            .rect(GR_BP_RCUT_W, GR_BP_RCUT_L * 2 + GR_BP_CUT_SIZE)
            .extrude(GR_BP_RCUT_D + EPS)
            .translate((0, 0, -EPS))
        )
        pocket = pocket.union(chan_x).union(chan_y)
        pockets = composite_from_pts(
            pocket, [(x, y, 0) for x, y in self._bp_cell_centres]
        )
        obj = obj.cut(pockets)
        return obj

