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

import warnings

import cadquery as cq

from cqgridfinity.constants import (
    EPS,
    GR_BASE_HEIGHT,
    GR_BASE_PROFILE,
    GR_BP_BOT_H,
    GR_BP_CUT_DEPTH,
    GR_BP_CUT_SIZE,
    GR_BP_RCUT_D,
    GR_BP_RCUT_L,
    GR_BP_RCUT_W,
    GR_HOLE_D,
    GR_HOLE_DIST,
    GR_HOLE_H,
    GR_RAD,
    GR_REFINED_HOLE_H,
    GR_SKEL_H,
    GR_SKEL_INNER,
    GR_SKEL_KEEPOUT_R,
    GR_SKEL_RAD,
    GR_SCREW_DEPTH,
    GR_SKEL_SCREW_NONE,
    GR_ST_ADDITIONAL_H,
    GR_ST_SCREW_D,
    GR_ST_SCREW_HEAD_D,
    GR_ST_SCREW_SPACING,
    GR_STR_BASE_PROFILE,
    GRU,
    GRU2,
    GRU_CUT,
)
from cqgridfinity.gf_obj import GridfinityObject
from cqgridfinity.gf_holes import (
    cut_magnet_holes,
    cut_screw_holes,
    cut_enhanced_holes,
)
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
      skeleton - remove material from slab leaving cross-shaped rib pattern (style_plate=2)
      screw_together - add horizontal M3 screw holes along edges for joining baseplates (style_plate=3/4)
      n_screws - number of screws per grid unit per edge (1-3, default 1)
      refined_holes - use refined magnet holes (5.86mm dia, 1.9mm deep, tighter press-fit)
      crush_ribs - add crush ribs to magnet holes for press-fit retention (8 ribs)
      chamfer_holes - add entry chamfer to magnet holes (0.8mm at 45deg)
      printable_hole_top - add thin bridge layer at hole top for supportless FDM printing
      distancex - target drawer X dimension in mm (0=disabled); auto-calcs length_u when length_u=0
      distancey - target drawer Y dimension in mm (0=disabled); auto-calcs width_u when width_u=0
      fitx - X padding alignment: -1=grid flush left, 0=centered, 1=grid flush right
      fity - Y padding alignment: -1=grid flush front, 0=centered, 1=grid flush back
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
        self.skeleton = False
        self.screw_together = False
        self.n_screws = 1
        self.refined_holes = False
        self.crush_ribs = False
        self.chamfer_holes = False
        self.printable_hole_top = False
        self.distancex = 0
        self.distancey = 0
        self.fitx = 0
        self.fity = 0
        for k, v in kwargs.items():
            if k in self.__dict__:
                if v is not None:
                    self.__dict__[k] = v
            else:
                warnings.warn(
                    f"{self.__class__.__name__}: unknown keyword argument '{k}' ignored",
                    stacklevel=2,
                )
        # Fit-to-drawer: auto-calculate grid units from drawer dimensions
        if self.distancex > 0 and self.length_u == 0:
            self.length_u = max(1, int(self.distancex // GRU))
        if self.distancey > 0 and self.width_u == 0:
            self.width_u = max(1, int(self.distancey // GRU))
        self.fitx = max(-1, min(1, self.fitx))
        self.fity = max(-1, min(1, self.fity))
        # Auto-adjust ext_depth to ensure enough material for features
        if self.skeleton:
            # kennetek calculate_offset_skeletonized():
            # ext_depth = h_skel + magnet_depth + screw_clearance
            mag_depth = self._magnet_hole_depth if self.magnet_holes else 0
            skel_depth = GR_SKEL_H + mag_depth + GR_SKEL_SCREW_NONE
            self.ext_depth = max(self.ext_depth, skel_depth)
        if self.screw_together:
            self.ext_depth = max(self.ext_depth, GR_ST_ADDITIONAL_H)
        if self.weighted:
            self.ext_depth = max(self.ext_depth, GR_BP_BOT_H)
        elif self.magnet_holes and self.screw_holes:
            self.ext_depth = max(self.ext_depth, GR_HOLE_H + GR_SCREW_DEPTH)
        elif self.magnet_holes:
            self.ext_depth = max(self.ext_depth, GR_HOLE_H)
        elif self.screw_holes:
            self.ext_depth = max(self.ext_depth, GR_SCREW_DEPTH)
        if self.corner_screws:
            self.ext_depth = max(self.ext_depth, 5.0)

    @property
    def _has_bottom_features(self):
        """True if this baseplate needs a solid slab below the receptacle."""
        return (self.magnet_holes or self.screw_holes or self.weighted
                or self.skeleton or self.screw_together)

    @property
    def _is_fit_to_drawer(self):
        """True when fit-to-drawer mode is active."""
        return self.distancex > 0 or self.distancey > 0

    @property
    def _fit_length(self):
        """Actual outer X dimension (may exceed grid length for fit-to-drawer)."""
        return max(self.length, self.distancex)

    @property
    def _fit_width(self):
        """Actual outer Y dimension (may exceed grid width for fit-to-drawer)."""
        return max(self.width, self.distancey)

    @property
    def _grid_offset(self):
        """Offset of grid center from outer block center for fit-to-drawer."""
        padding_x = self._fit_length - self.length
        padding_y = self._fit_width - self.width
        return (padding_x * self.fitx / 2, padding_y * self.fity / 2)

    @property
    def _bp_cell_centres(self):
        """Grid cell centres in the baseplate coordinate system (centered).
        Offset by _grid_offset when fit-to-drawer is active."""
        ox, oy = self._grid_offset
        return [
            (
                (i - (self.length_u - 1) / 2) * GRU + ox,
                (j - (self.width_u - 1) / 2) * GRU + oy,
            )
            for i in range(self.length_u)
            for j in range(self.width_u)
        ]

    @property
    def _bp_hole_centres(self):
        """Magnet/screw hole positions in the baseplate coordinate system (centered).
        Four holes per grid cell at corners, offset GR_HOLE_DIST from cell centre.
        Offset by _grid_offset when fit-to-drawer is active."""
        ox, oy = self._grid_offset
        return [
            (
                (i - (self.length_u - 1) / 2) * GRU + GR_HOLE_DIST * di + ox,
                (j - (self.width_u - 1) / 2) * GRU + GR_HOLE_DIST * dj + oy,
            )
            for i in range(self.length_u)
            for j in range(self.width_u)
            for di in (-1, 1)
            for dj in (-1, 1)
        ]

    def _corner_pts(self):
        oxy = self.corner_tab_size / 2
        return [
            (i * (self._fit_length / 2 - oxy), j * (self._fit_width / 2 - oxy), 0)
            for i in (-1, 1)
            for j in (-1, 1)
        ]

    @property
    def _filename_prefix(self) -> str:
        return "gf_baseplate_"

    def _filename_suffix(self) -> str:
        fn = ""
        # 1. Base style
        if self.skeleton:
            fn += "_skel"
        elif self.weighted:
            fn += "_weighted"
        # 1b. Screw-together
        if self.screw_together:
            fn += "_screwtog"
            if self.n_screws > 1:
                fn += "%d" % self.n_screws
        # 2. Hole features
        if self.magnet_holes and self.screw_holes:
            fn += "_mag-screw"
        elif self.magnet_holes:
            fn += "_mag"
        elif self.screw_holes:
            fn += "_screw"
        # 2b. Enhanced hole options
        if self.magnet_holes and self._has_enhanced_holes:
            opts = []
            if self.refined_holes:
                opts.append("ref")
            if self.crush_ribs:
                opts.append("rib")
            if self.chamfer_holes:
                opts.append("chm")
            if self.printable_hole_top:
                opts.append("prt")
            fn += "_" + "-".join(opts)
        # 3. Mounting
        if self.corner_screws:
            fn += "_csk"
        # 4. Manual ext_depth (only if no features auto-set it)
        if (self.ext_depth > 0
                and not self._has_bottom_features
                and not self.corner_screws):
            fn += "_d%.1f" % (self.ext_depth)
        # 5. Fit-to-drawer
        if self._is_fit_to_drawer:
            fn += "_fit%dx%d" % (int(self.distancex), int(self.distancey))
        return fn

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
        if self._is_fit_to_drawer:
            ox, oy = self._grid_offset
            rc = rc.translate((ox, oy, 0))
        r = (
            cq.Workplane("XY")
            .rect(self._fit_length, self._fit_width)
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
        if self.skeleton:
            r = self._render_skeleton_cutouts(r)
        if self.screw_together:
            r = self._render_screw_together_holes(r)
        if self.magnet_holes or self.screw_holes:
            r = self._render_baseplate_holes(r)
        if self.weighted and not self.skeleton:
            r = self._render_weight_pockets(r)
        return r

    @property
    def _has_enhanced_holes(self):
        """True if any enhanced hole option is enabled."""
        return self.refined_holes or self.crush_ribs or self.chamfer_holes or self.printable_hole_top

    @property
    def _magnet_hole_depth(self):
        """Effective magnet hole depth based on hole style."""
        if self.refined_holes:
            return GR_REFINED_HOLE_H
        return GR_HOLE_H

    def _render_skeleton_cutouts(self, obj):
        """Cut skeleton material-removal pockets from the baseplate slab.

        Creates 4 corner pocket cutouts per grid cell, leaving a cross-shaped
        rib pattern that preserves material around hole positions.

        Reproduces kennetek profile_skeleton(): the rib half-width equals
        hole_dist minus keepout_r (5.75mm), so ribs are 11.5mm wide.
        Each corner pocket is cut_size × cut_size (12.4mm) with r_skel
        rounded corners, extruded through the full ext_depth.
        """
        rib_half_w = GR_HOLE_DIST - GR_SKEL_KEEPOUT_R  # 5.75mm
        cut_size = GR_SKEL_INNER / 2 - rib_half_w  # 12.4mm
        offset = rib_half_w + cut_size / 2  # 11.95mm
        r = GR_SKEL_RAD  # 2.0mm

        # Single corner pocket with rounded corners
        cutout = (
            cq.Workplane("XY")
            .rect(cut_size, cut_size)
            .extrude(self.ext_depth + EPS)
            .edges("|Z").fillet(r)
            .translate((0, 0, -EPS))
        )

        # 4 corner positions per cell, tiled across all cells
        pts = []
        for cx, cy in self._bp_cell_centres:
            for dx in (-1, 1):
                for dy in (-1, 1):
                    pts.append((cx + dx * offset, cy + dy * offset, 0))

        cutouts = composite_from_pts(cutout, pts)
        return obj.cut(cutouts)

    def _render_screw_together_holes(self, obj):
        """Cut horizontal screw holes along all 4 edges for joining baseplates.

        Each edge gets holes at every grid unit position. Each hole is a
        horizontal cylinder (dia GR_ST_SCREW_D, length GRU/2) centered at the
        edge, Z-centered in the additional-height section. Adjacent baseplates
        align so a screw passes from one into the other.

        Multi-screw mode spaces n_screws at 5.5mm center-to-center
        (GR_ST_SCREW_HEAD_D + GR_ST_SCREW_SPACING) perpendicular to hole axis.

        For fit-to-drawer, holes are placed at grid edges (not outer block
        edges) so they align with adjacent standard baseplates.
        """
        hole_r = GR_ST_SCREW_D / 2
        hole_len = GRU2  # 21mm, extends inward from edge
        hole_z = GR_ST_ADDITIONAL_H / 2  # Z-center in extra-height section
        half_lx = self.length / 2  # grid edge, not outer block
        half_ly = self.width / 2   # grid edge, not outer block
        ox, oy = self._grid_offset
        screw_cc = GR_ST_SCREW_HEAD_D + GR_ST_SCREW_SPACING  # 5.5mm

        # Multi-screw offsets perpendicular to hole axis
        offsets = [0.0]
        if self.n_screws == 2:
            offsets = [-screw_cc / 2, screw_cc / 2]
        elif self.n_screws >= 3:
            offsets = [-screw_cc, 0.0, screw_cc]

        # Template cylinders centered at origin
        # X-direction: cylinder along X-axis
        x_hole = (
            cq.Workplane("YZ")
            .circle(hole_r)
            .extrude(hole_len)
            .translate((-hole_len / 2, 0, 0))
        )
        # Y-direction: cylinder along Y-axis
        y_hole = (
            cq.Workplane("XZ")
            .circle(hole_r)
            .extrude(hole_len)
            .translate((0, -hole_len / 2, 0))
        )

        x_pts = []  # positions for X-direction holes
        y_pts = []  # positions for Y-direction holes

        # ±X edges: holes at each grid unit along Y, extending inward along X
        for j in range(self.width_u):
            cy = (j - (self.width_u - 1) / 2) * GRU
            for off in offsets:
                x_pts.append((ox + half_lx - hole_len / 2, oy + cy + off, hole_z))
                x_pts.append((ox - half_lx + hole_len / 2, oy + cy + off, hole_z))

        # ±Y edges: holes at each grid unit along X, extending inward along Y
        for i in range(self.length_u):
            cx = (i - (self.length_u - 1) / 2) * GRU
            for off in offsets:
                y_pts.append((ox + cx + off, oy + half_ly - hole_len / 2, hole_z))
                y_pts.append((ox + cx + off, oy - half_ly + hole_len / 2, hole_z))

        if x_pts:
            obj = obj.cut(composite_from_pts(x_hole, x_pts))
        if y_pts:
            obj = obj.cut(composite_from_pts(y_hole, y_pts))
        return obj

    def _render_baseplate_holes(self, obj):
        """Cut magnet and/or screw holes into the solid slab below receptacles.

        The receptacle floor is at Z=ext_depth. Below it is a solid slab
        from Z=0 to Z=ext_depth where holes are cut.
        Magnet recesses are blind holes from the floor downward.
        Screw holes pass through the remaining material to the bottom.

        When enhanced hole options are set (refined, crush_ribs, chamfer,
        printable_top), uses cut_enhanced_holes() instead of basic cuts.
        """
        pts = self._bp_hole_centres
        mag_depth = self._magnet_hole_depth
        if self.magnet_holes:
            if self._has_enhanced_holes:
                obj = cut_enhanced_holes(
                    obj,
                    pts,
                    z_offset=self.ext_depth - mag_depth,
                    refined=self.refined_holes,
                    crush_ribs=self.crush_ribs,
                    chamfer=self.chamfer_holes,
                    printable_top=self.printable_hole_top,
                )
            else:
                obj = cut_magnet_holes(
                    obj, pts, z_offset=self.ext_depth - GR_HOLE_H
                )
        if self.screw_holes:
            top = self.ext_depth - mag_depth if self.magnet_holes else self.ext_depth
            obj = cut_screw_holes(obj, pts, depth=top)
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

