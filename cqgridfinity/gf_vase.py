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
# Gridfinity Spiral Vase (1B.16-1B.17)
# Source: kennetek/gridfinity-spiral-vase.scad (MIT)
#
# NOTE: Some Kennetek features are FDM slicer-specific and do not translate
# to B-Rep STEP geometry:
#   - "magic slice" (0.001mm cut to force slicer recognition) — omitted
#   - "alternating layer slicing" on dividers — omitted; plain thin walls used
#   - "funnel fingertip features" — omitted (complex, slicer-dependent geometry)

import math
import warnings

import cadquery as cq
from cqkit.cq_helpers import rounded_rect_sketch, composite_from_pts

from cqgridfinity.constants import (
    EPS,
    GR_BASE_CLR,
    GR_BASE_HEIGHT,
    GR_BOX_PROFILE,
    GR_HOLE_DIST,
    GR_HOLE_D,
    GR_HOLE_H,
    GR_LIP_H,
    GR_LIP_PROFILE,
    GR_MAGNET_H,
    GR_RAD,
    GR_TOL,
    GR_TOPSIDE_H,
    GR_UNDER_H,
    GR_WALL,
    GRU,
    GRU2,
    GRHU,
    SQRT2,
)
from cqgridfinity.gf_box import GridfinityBox
from cqgridfinity.gf_obj import GridfinityObject

# X-pattern arm width in mm (fraction of cell half-width)
_X_ARM_W = 3.0
# X-pattern size = half of grid unit
_X_SIZE = GRU2  # 21mm


def _x_profile(arm_w=_X_ARM_W):
    """2D X-profile sketch: two diagonal rectangles (±45°) forming an X.

    Returns a CadQuery 2D Workplane sketch (not closed; used via polygon).
    Arm width = arm_w mm. The X spans _X_SIZE × _X_SIZE.
    """
    diag_l = _X_SIZE * SQRT2 + arm_w  # diagonal arm length (clipped to cell)
    # Two rectangles at ±45° — create as wire sketches on XY plane
    def _diag_rect(angle_deg):
        angle = math.radians(angle_deg)
        # Half-lengths along the diagonal
        hl = diag_l / 2
        hw = arm_w / 2
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        pts = [
            (-hl * cos_a - hw * sin_a, -hl * sin_a + hw * cos_a),
            (-hl * cos_a + hw * sin_a, -hl * sin_a - hw * cos_a),
            ( hl * cos_a + hw * sin_a,  hl * sin_a - hw * cos_a),
            ( hl * cos_a - hw * sin_a,  hl * sin_a + hw * cos_a),
        ]
        return pts

    pts45  = _diag_rect(45)
    pts135 = _diag_rect(135)
    return pts45, pts135


def _x_solid(depth, arm_w=_X_ARM_W):
    """Solid X-shaped block of given depth (height in Z).

    Used both for vase shell cutouts and base insert protrusions.
    The X is centred at origin.
    """
    pts45, pts135 = _x_profile(arm_w)
    r45 = cq.Workplane("XY").polyline(pts45).close().extrude(depth)
    r135 = cq.Workplane("XY").polyline(pts135).close().extrude(depth)
    return r45.union(r135)


class GridfinityVaseBox(GridfinityBox):
    """Gridfinity spiral vase bin shell (1B.16).

    Single-wall (2×nozzle) open-top shell designed for FDM spiral/vase mode
    printing. Generates a STEP solid; downstream slicer prints in vase mode.

    Source: kennetek/gridfinity-spiral-vase.scad — gridfinityVase() (type=0)

    Parameters
    ----------
    length_u, width_u : float
        Grid dimensions (supports non-integer per 1B.12).
    height_u : float
        Bin height (in 7mm units by default; controlled by gridz_define).
    nozzle : float
        Extrusion width in mm (default 0.6). Wall = 2 × nozzle.
    layer : float
        Slicer layer height in mm (default 0.35). Bottom = layer × bottom_layer.
    bottom_layer : int
        Number of base layers on build plate (default 3, 0 = no solid bottom).
    n_divx : int
        Number of internal X-axis dividers (default 0 = none).
    style_tab : int
        Tab style: 0=continuous, 1=broken, 2=auto, 3=right, 4=center,
        5=left, 6=none. Default 0 (continuous).
    style_base : int
        Base X-cutout style: 0=all cells, 1=corners only, 2=edges only,
        3=auto, 4=none. Default 0.
    enable_lip : bool
        Add stacking lip at top (default True).
    enable_scoop_chamfer : bool
        Chamfer at the bottom of the back wall interior (default True).
    enable_zsnap : bool
        Round height to next 7mm multiple (default False; from 1B.15).
    gridz_define : int
        Height mode 0-3 (default 0; from 1B.14).

    Notes
    -----
    FDM slicer tricks NOT implemented in STEP geometry:
    - magic slice (0.001mm cut) — meaningless for B-Rep
    - alternating layer slicing on dividers — plain thin walls used instead
    - finger-grab funnels — omitted (slicer-dependent geometry)
    - inset / pinch — omitted (marginal for STEP workflow)
    """

    def __init__(self, length_u, width_u, height_u, **kwargs):
        # Initialise parent with no kwargs (we process all kwargs below)
        super().__init__(length_u, width_u, height_u)
        # Vase-specific defaults
        self.nozzle = 0.6
        self.layer = 0.35
        self.bottom_layer = 3
        self.n_divx = 0
        self.style_tab = 0
        self.style_base = 0
        self.enable_lip = True
        self.enable_scoop_chamfer = True
        # Apply all kwargs (vase-specific + inherited parent attrs)
        for k, v in kwargs.items():
            if k in self.__dict__:
                self.__dict__[k] = v
            else:
                warnings.warn(
                    f"{self.__class__.__name__}: unknown keyword argument '{k}' ignored",
                    stacklevel=2,
                )
        # Wall thickness always derived from nozzle (2×nozzle, per Kennetek)
        self.wall_th = 2 * self.nozzle
        # Re-validate height mode (parent may have validated already, redo for safety)
        if self.gridz_define not in (0, 1, 2, 3):
            raise ValueError("gridz_define must be 0-3, got %r" % self.gridz_define)

    @property
    def d_bottom(self):
        """Bottom layer thickness in mm = layer × max(bottom_layer, 1)."""
        return self.layer * max(self.bottom_layer, 1)

    @property
    def _filename_prefix(self) -> str:
        return "gf_vase_"

    def _filename_suffix(self) -> str:
        fn = "x%s" % self._fmt_unit(self.height_u)
        if self.gridz_define != 0:
            fn += "_m%d" % self.gridz_define
        if self.enable_zsnap:
            fn += "_zs"
        if self.n_divx > 1:
            fn += "_div%d" % self.n_divx
        if not self.enable_lip:
            fn += "_nolip"
        if self.style_tab != 0:
            fn += "_tab%d" % self.style_tab
        if self.style_base != 0:
            fn += "_base%d" % self.style_base
        return fn

    def _cell_corners(self):
        """Grid cell positions that are corners (for style_base=1)."""
        nx = math.floor(self.length_u)
        ny = math.floor(self.width_u)
        return [
            (x * GRU, y * GRU)
            for x in range(nx)
            for y in range(ny)
            if (x in (0, nx - 1)) and (y in (0, ny - 1))
        ]

    def _cell_edges(self):
        """Grid cell positions that are on edges but not corners (style_base=2)."""
        nx = math.floor(self.length_u)
        ny = math.floor(self.width_u)
        corners = set(self._cell_corners())
        return [
            (x * GRU, y * GRU)
            for x in range(nx)
            for y in range(ny)
            if (x in (0, nx - 1) or y in (0, ny - 1))
            and (x * GRU, y * GRU) not in corners
        ]

    def _x_cutout_cells(self):
        """Cell positions that receive X-cutouts, per style_base."""
        all_cells = self.grid_centres
        if self.style_base == 0:
            return all_cells
        if self.style_base == 1:
            return self._cell_corners()
        if self.style_base == 2:
            return self._cell_edges()
        if self.style_base == 3:
            # auto: all for 1×1, edges+corners otherwise
            if math.floor(self.length_u) == 1 and math.floor(self.width_u) == 1:
                return all_cells
            return list(self._cell_corners()) + list(self._cell_edges())
        return []  # style_base == 4: none

    def render(self):
        """Render the vase shell as a thin-wall open-top B-Rep solid."""
        wall_th = self.wall_th       # 2*nozzle
        d_bottom = self.d_bottom     # solid bottom thickness

        # Height of the bin body above the base profile
        bin_h = self.bin_height      # = height - GR_BASE_HEIGHT

        # ── 1. Base profiles (same Gridfinity base as normal bins) ──────────
        base_profile = self.extrude_profile(
            rounded_rect_sketch(self._gru, self._gru, self.outer_rad + GR_BASE_CLR),
            GR_BOX_PROFILE,
        )
        base_profile = base_profile.translate((0, 0, -GR_BASE_CLR))
        base_profile = base_profile.mirror(mirrorPlane="XY")
        base_profile = composite_from_pts(base_profile, self.grid_centres)

        # Connector block: merge base grid cells with the outer shell
        rs = rounded_rect_sketch(*self.outer_dim, self.outer_rad)
        connector = (
            cq.Workplane("XY")
            .placeSketch(rs)
            .extrude(-GR_BASE_HEIGHT - 1)
            .translate((*self.half_dim, 0.5))
        )
        connector = connector.intersect(base_profile)

        # ── 2. Outer shell walls ─────────────────────────────────────────────
        outer_walls = (
            cq.Workplane("XY")
            .placeSketch(rs)
            .extrude(bin_h - GR_BASE_CLR)
            .translate((*self.half_dim, GR_BASE_CLR))
        )

        # ── 3. Inner void (above solid bottom) ──────────────────────────────
        in_l = self.outer_l - 2 * wall_th
        in_w = self.outer_w - 2 * wall_th
        in_rad = max(self.outer_rad - wall_th, 0.5)
        ri = rounded_rect_sketch(in_l, in_w, in_rad)
        cut_h = bin_h - d_bottom + EPS
        inner_void = (
            cq.Workplane("XY")
            .placeSketch(ri)
            .extrude(cut_h)
            .translate((*self.half_dim, d_bottom))
        )

        # ── Assemble: connector + walls − inner void ─────────────────────────
        r = connector.union(outer_walls).cut(inner_void)

        # ── 4. X-cutouts through the bottom slab (style_base) ───────────────
        x_cells = self._x_cutout_cells()
        if x_cells:
            x_solid = _x_solid(d_bottom + EPS + 0.01)
            x_cuts = composite_from_pts(x_solid, [(cx, cy, -EPS) for cx, cy in x_cells])
            r = r.cut(x_cuts)

        # ── 5. Optional stacking lip ─────────────────────────────────────────
        if self.enable_lip:
            lip_profile = GR_LIP_PROFILE
            lip_top = (
                cq.Workplane("XY")
                .placeSketch(rs)
                .extrude(GR_TOPSIDE_H)
                .translate((*self.half_dim, bin_h))
            )
            ri_inner = rounded_rect_sketch(in_l - 2 * wall_th, in_w - 2 * wall_th,
                                           max(in_rad - wall_th, 0.5))
            lip_cut = (
                cq.Workplane("XY")
                .placeSketch(ri_inner)
                .extrude(GR_TOPSIDE_H + EPS)
                .translate((*self.half_dim, bin_h - EPS))
            )
            lip = lip_top.cut(lip_cut)
            r = r.union(lip)

        # ── 6. Optional dividers (thin walls ⊥ to X) ────────────────────────
        if self.n_divx > 1:
            divider_h = bin_h - d_bottom
            div_wall = (
                cq.Workplane("XY")
                .rect(wall_th, self.outer_w - wall_th)
                .extrude(divider_h)
                .translate((*self.half_dim, d_bottom))
            )
            xl = self.outer_l / self.n_divx
            # Dividers at equal intervals across the bin width (centered).
            # i*xl - outer_l/2 is the offset from the shell centre (half_dim).
            div_pts = [
                (i * xl - self.outer_l / 2, 0)
                for i in range(1, self.n_divx)
            ]
            r = r.union(composite_from_pts(div_wall, div_pts))

        # ── 7. Optional scoop chamfer (back wall bottom interior) ─────────────
        if self.enable_scoop_chamfer and bin_h > d_bottom + 1.0:
            # Chamfer the bottom-rear interior edge: 45° wedge cut
            scoop_d = min(8.0, (bin_h - d_bottom) * 0.3)
            scoop = (
                cq.Workplane("XZ")
                .moveTo(self.outer_w / 2, d_bottom)
                .lineTo(self.outer_w / 2, d_bottom + scoop_d)
                .lineTo(self.outer_w / 2 - scoop_d, d_bottom)
                .close()
                .revolve(0)  # used as wire only — extrude below
            )
            # Use a simple wedge-shaped cut on the back interior surface
            scoop_wedge = (
                cq.Workplane("YZ")
                .moveTo(self.outer_w / 2 - wall_th, d_bottom)
                .lineTo(self.outer_w / 2 - wall_th - scoop_d, d_bottom)
                .lineTo(self.outer_w / 2 - wall_th, d_bottom + scoop_d)
                .close()
                .extrude(self.outer_l)
                .translate((-self.outer_l / 2, 0, 0))
                .translate((*self.half_dim, 0))
            )
            r = r.cut(scoop_wedge)

        # ── 8. Optional tabs (style_tab; simplified: continuous vs none) ──────
        if self.style_tab != 6:
            tab_h = 1.2   # triangular tab height (mm) at top front edge
            tab_w = self.outer_l if self.style_tab == 0 else self.outer_l * 0.4
            tab_x_offset = 0.0
            if self.style_tab == 3:   # right
                tab_x_offset = (self.outer_l - tab_w) / 2
            elif self.style_tab == 4:  # center
                tab_x_offset = 0.0
            elif self.style_tab == 5:  # left
                tab_x_offset = -(self.outer_l - tab_w) / 2

            tab = (
                cq.Workplane("XZ")
                .moveTo(tab_x_offset - tab_w / 2, bin_h)
                .lineTo(tab_x_offset + tab_w / 2, bin_h)
                .lineTo(tab_x_offset, bin_h + tab_h)
                .close()
                .extrude(wall_th)
                .translate((*self.half_dim, 0))
                .translate((0, -(self.outer_w / 2 - wall_th / 2), 0))
            )
            r = r.union(tab)

        # ── Final transform (same as standard bin) ───────────────────────────
        r = r.translate((-self.half_l, -self.half_w, GR_BASE_HEIGHT))
        return r


class GridfinityVaseBase(GridfinityObject):
    """Gridfinity spiral vase base insert (1B.17).

    Separate base piece that inserts into the GridfinityVaseBox shell.
    Provides structural bottom, magnet holes, and X-pattern engagement
    protrusion for the vase shell X-cutouts.

    Source: kennetek/gridfinity-spiral-vase.scad — gridfinityBaseVase() (type=1)

    Parameters
    ----------
    length_u, width_u : int
        Grid dimensions (integer; base insert covers full grid).
    nozzle : float
        Extrusion width in mm (default 0.6). Wall = 2 × nozzle.
    layer : float
        Slicer layer height in mm (default 0.35).
    bottom_layer : int
        Number of base layers (default 3). Bottom thickness = layer × bottom_layer.
    holes : bool
        Add magnet holes (default True).
    style_base : int
        X-cutout engagement style: 0=all, 1=corners, 2=edges, 3=auto, 4=none.
        Must match the GridfinityVaseBox style_base. Default 0.

    Notes
    -----
    FDM features NOT implemented:
    - magic slice (0.001mm cut) — omitted for B-Rep
    """

    def __init__(self, length_u=1, width_u=1, **kwargs):
        super().__init__()
        self.length_u = length_u
        self.width_u = width_u
        # Parameters
        self.nozzle = 0.6
        self.layer = 0.35
        self.bottom_layer = 3
        self.holes = True
        self.style_base = 0
        # Apply kwargs
        for k, v in kwargs.items():
            if k in self.__dict__:
                self.__dict__[k] = v
            else:
                warnings.warn(
                    f"{self.__class__.__name__}: unknown keyword argument '{k}' ignored",
                    stacklevel=2,
                )
        self.wall_th = 2 * self.nozzle

    @property
    def d_bottom(self):
        """Bottom layer thickness = layer × max(bottom_layer, 1)."""
        return self.layer * max(self.bottom_layer, 1)

    @property
    def outer_l(self):
        return self.length_u * GRU - GR_TOL

    @property
    def outer_w(self):
        return self.width_u * GRU - GR_TOL

    @property
    def outer_rad(self):
        return GR_RAD - GR_TOL / 2

    @property
    def half_l(self):
        return (self.length_u - 1) * GRU / 2

    @property
    def half_w(self):
        return (self.width_u - 1) * GRU / 2

    @property
    def half_dim(self):
        return self.half_l, self.half_w

    @property
    def grid_centres(self):
        return [
            (x * GRU, y * GRU)
            for x in range(self.length_u)
            for y in range(self.width_u)
        ]

    @property
    def _filename_prefix(self) -> str:
        return "gf_vase_base_"

    def _filename_suffix(self) -> str:
        fn = "%dx%d" % (self.length_u, self.width_u)
        if self.holes:
            fn += "_mag"
        if self.style_base != 0:
            fn += "_base%d" % self.style_base
        return fn

    def _x_cutout_cells(self):
        """Same selection logic as GridfinityVaseBox._x_cutout_cells()."""
        all_cells = self.grid_centres
        nx = self.length_u
        ny = self.width_u
        if self.style_base == 0:
            return all_cells
        corners = [
            (x * GRU, y * GRU)
            for x in range(nx) for y in range(ny)
            if (x in (0, nx - 1)) and (y in (0, ny - 1))
        ]
        if self.style_base == 1:
            return corners
        edges = [
            (x * GRU, y * GRU)
            for x in range(nx) for y in range(ny)
            if (x in (0, nx - 1) or y in (0, ny - 1))
            and (x * GRU, y * GRU) not in corners
        ]
        if self.style_base == 2:
            return edges
        if self.style_base == 3:
            if nx == 1 and ny == 1:
                return all_cells
            return corners + edges
        return []

    def render(self):
        """Render the vase base insert."""
        wall_th = self.wall_th
        d_bottom = self.d_bottom

        rs = rounded_rect_sketch(*self.outer_dim, self.outer_rad)

        # ── 1. Base profiles at each grid cell ───────────────────────────────
        base_profile = self.extrude_profile(
            rounded_rect_sketch(GRU, GRU, self.outer_rad + GR_BASE_CLR),
            GR_BOX_PROFILE,
        )
        base_profile = base_profile.translate((0, 0, -GR_BASE_CLR))
        base_profile = base_profile.mirror(mirrorPlane="XY")
        base_profile = composite_from_pts(base_profile, self.grid_centres)

        # ── 2. Outer shell + bottom slab ─────────────────────────────────────
        # Connector block to join base profiles into one solid
        connector = (
            cq.Workplane("XY")
            .placeSketch(rs)
            .extrude(-GR_BASE_HEIGHT - 1)
            .translate((*self.half_dim, 0.5))
        )
        connector = connector.intersect(base_profile)

        # Outer bottom slab (thickness d_bottom)
        bottom_slab = (
            cq.Workplane("XY")
            .placeSketch(rs)
            .extrude(d_bottom + GR_BASE_CLR)
            .translate((*self.half_dim, -GR_BASE_CLR))
        )
        r = connector.union(bottom_slab)

        # ── 3. Cross ribs: 4 diagonal walls per cell (4× circular pattern) ───
        # Ribs at 45°/135°/225°/315° from each cell center,
        # spanning from center outward, height = GR_BASE_HEIGHT.
        rib_len = GRU2 + 2  # rib length (to outer wall) + clearance
        rib_pts = []
        for cx, cy in self.grid_centres:
            for angle in (45, 135):
                rib_pts.append((cx, cy, math.radians(angle)))

        for cx, cy, angle in rib_pts:
            # A thin wall along the diagonal, placed at cell center (cx, cy)
            # in pre-transform coords (final translate handles centering).
            rib = (
                cq.Workplane("XY")
                .rect(rib_len, wall_th)
                .extrude(GR_BASE_HEIGHT)
                .translate((cx, cy, 0))
            )
            rib = rib.rotate((cx, cy, 0), (cx, cy, 1), math.degrees(angle))
            # Clip rib to the base solid (don't extend outside)
            rib = rib.intersect(r)
            r = r.union(rib)

        # ── 4. X-pattern protrusion on top (engages vase shell X-cutouts) ────
        x_cells = self._x_cutout_cells()
        if x_cells:
            x_protrusion = _x_solid(d_bottom, arm_w=_X_ARM_W - 0.1)  # slight clearance
            # Place at each cell center in pre-transform coords; final translate
            # handles world-coord centering (avoids double-subtracting half_l/half_w).
            for cx, cy in x_cells:
                xp = x_protrusion.translate((cx, cy, d_bottom))
                r = r.union(xp)

        # ── 5. Magnet holes ───────────────────────────────────────────────────
        if self.holes:
            hole_cyl = (
                cq.Workplane("XY")
                .circle(GR_HOLE_D / 2)
                .extrude(GR_MAGNET_H)
                .translate((0, 0, d_bottom - GR_MAGNET_H))
            )
            for cx, cy in self.grid_centres:
                for dx in (-GR_HOLE_DIST, GR_HOLE_DIST):
                    for dy in (-GR_HOLE_DIST, GR_HOLE_DIST):
                        # Place at (cx+dx, cy+dy) in pre-transform coords;
                        # final translate handles centering (avoids double-subtracting).
                        r = r.cut(hole_cyl.translate((cx + dx, cy + dy, 0)))

        # ── Final transform ───────────────────────────────────────────────────
        r = r.translate((-self.half_l, -self.half_w, GR_BASE_HEIGHT))
        return r
