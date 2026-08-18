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
from dataclasses import replace
import warnings

import cadquery as cq
from cqkit import HasZCoordinateSelector, VerticalEdgeSelector, FlatEdgeSelector
from cqkit.cq_helpers import rounded_rect_sketch, composite_from_pts, rotate_z
from cqgridfinity.constants import (
    EPS,
    GR_BASE_CLR,
    GR_BASE_HEIGHT,
    GR_BOT_H,
    GR_BOLT_D,
    GR_BOLT_H,
    GR_BOX_PROFILE,
    GR_CYL_CHAMFER,
    GR_CYL_DIAM,
    GR_DIV_WALL,
    GR_FILLET,
    GR_FLOOR,
    GR_HOLE_D,
    GR_HOLE_DIST,
    GR_HOLE_H,
    GR_HOLE_SLICE,
    GR_NOTCH_FILLET_MAX,
    GR_LID_TH,
    GR_LID_TH_MIN,
    GR_LIP_APEX_SETBACK,
    GR_LIP_FILLET,
    GR_LIP_H,
    GR_LIP_PROFILE,
    GR_STACKING_LIP_H,
    GR_NO_PROFILE,
    GR_RAD,
    GR_REDUCED_LIP_PROFILE,
    GR_SCREW_DEPTH,
    GR_TOL,
    GR_TOPSIDE_H,
    GR_UNDER_H,
    GR_WALL,
    GRU,
    GRU2,
    GRHU,
    SQRT2,
)
from cqgridfinity.gf_divider import Divider, dividers_from_counts
from cqgridfinity.gf_holegrid import HoleGrid
from cqgridfinity.gf_obj import GridfinityObject
from cqgridfinity.gf_holes import (
    cut_enhanced_holes,
    hole_filler,
)
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
        # Explicit divider objects. None means "derive evenly-spaced dividers
        # from length_div/width_div", which is what every existing caller does.
        # Set a list to place them individually -- unequal compartments,
        # notches, per-divider height, angled tops. See gf_divider.Divider.
        self.dividers = None
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
        self.label_style = None  # None=auto; "full"/"auto"/"left"/"center"/"right"/"none"
        self.cullenect_socket = False  # click-in label socket in the shelf (1D.5)
        self.cullenect_label_u = 0  # 0 = size the tile to the shelf
        self.compartment_depth = 0  # raise compartment floor (mm), 0=full depth
        self.height_internal = 0  # override internal height (mm), 0=default
        self.cylindrical = False  # cut cylindrical compartments
        # Generic hole grid: shape (circle/hex/rect), size, rows, cols.
        # Overrides `cylindrical` when set. See gf_holegrid.HoleGrid.
        self.hole_grid = None
        self.cylinder_diam = GR_CYL_DIAM  # cylinder diameter (mm)
        self.cylinder_chamfer = GR_CYL_CHAMFER  # cylinder top chamfer (mm)
        # Enhanced hole options (kennetek gridfinity-rebuilt-holes.scad)
        self.refined_holes = False  # tighter press-fit (5.86mm dia, 1.9mm deep)
        self.crush_ribs = False  # 8 ribs for friction-fit retention
        self.chamfer_holes = False  # 0.8mm 45° entry chamfer
        self.printable_hole_top = False  # thin bridge layer for FDM
        # Grid flexibility (1B.12-1B.13)
        self.half_grid = False  # 21mm grid increments; forces only_corners holes
        # Height mode selection (1B.14) — mirrors kennetek gridz_define 0-3:
        #   0: height_u in 7mm gridfinity units (default)
        #   1: height_u in internal usable mm (excl floor & lip)
        #   2: height_u in external mm (total bin height)
        #   3: height_u in external mm including the 4.4mm stacking lip protrusion
        self.gridz_define = 0
        # Z-snap (1B.15): round height up to next 7mm Gridfinity multiple
        self.enable_zsnap = False
        for k, v in kwargs.items():
            if k in self.__dict__:
                self.__dict__[k] = v
            else:
                warnings.warn(
                    f"{self.__class__.__name__}: unknown keyword argument '{k}' ignored",
                    stacklevel=2,
                )
        # Validate height mode (1B.14)
        if self.gridz_define not in (0, 1, 2, 3):
            raise ValueError(
                "gridz_define must be 0-3, got %r" % self.gridz_define
            )
        # Validate grid dimensions: must be >= 1 to form a valid base profile.
        # Non-integer values are accepted (1B.12); partial cells produce
        # an outer shell extension with no base profile in the partial area.
        if self.length_u < 1:
            raise ValueError(
                "length_u must be >= 1, got %g (minimum Gridfinity unit size)" % self.length_u
            )
        if self.width_u < 1:
            raise ValueError(
                "width_u must be >= 1, got %g (minimum Gridfinity unit size)" % self.width_u
            )
        # Normalize scoops: bool→float, clamp to [0, 1]
        if isinstance(self.scoops, bool):
            self.scoops = 1.0 if self.scoops else 0.0
        else:
            self.scoops = max(0.0, min(1.0, float(self.scoops)))
        # Normalize label_style from labels boolean
        if self.label_style is None:
            self.label_style = "full" if self.labels else "none"
        elif self.label_style != "none":
            self.labels = True
        else:
            self.labels = False
        _valid_label_styles = ("full", "auto", "left", "center", "right", "none")
        if self.label_style not in _valid_label_styles:
            raise ValueError(
                "label_style must be one of %s, got '%s'"
                % (_valid_label_styles, self.label_style)
            )
        # Backward compat: no_lip=True maps to lip_style="none"
        if self.no_lip and self.lip_style == "normal":
            self.lip_style = "none"
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
            "Gridfinity Box %gU x %gU x %dU (%.2f x %.2f x %.2f mm)"
            % (
                self.length_u,
                self.width_u,
                self.height_u,
                self.length - GR_TOL,
                self.width - GR_TOL,
                # Report the finished part, not the construction height: this
                # is what a caller would measure with calipers.
                self.actual_height,
            )
        )
        lip_desc = {
            "normal": "with mating top lip",
            "reduced": "with reduced top lip",
            "none": "no mating top lip",
        }
        sl = lip_desc.get(self.lip_style, "with mating top lip")
        ss = "Lite style box  " if self.lite_style else ""
        hg = "Half-grid (21mm)  " if self.half_grid else ""
        s.append("  %s%sWall thickness: %.2f mm  %s" % (hg, ss, self.wall_th, sl))
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
            s.append("  Lengthwise scoops with %.2f mm radius" % (self.scoop_rad * self.scoops))
        if self.labels:
            style_info = "" if self.label_style == "full" else " (%s)" % self.label_style
            s.append(
                "  Lengthwise label shelf %.2f mm wide with %.2f mm overhang%s"
                % (self.label_width, self.label_height, style_info)
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

    @staticmethod
    def _z_snap(content_mm: float) -> float:
        """Round content height up to next 7mm Gridfinity multiple (1B.15).

        Equivalent to Kennetek's z_snap(): h if h%7==0 else h+7-h%7.
        Uses EPS tolerance to avoid floating-point false positives.
        """
        rem = content_mm % GRHU
        if rem < EPS:
            return content_mm
        return content_mm + GRHU - rem

    @property
    def height(self):
        """Total bin height in mm, derived from height_u via gridz_define mode (1B.14).

        Mode 0 (default): height_u in 7mm gridfinity units  → 4.4 + 7*height_u
        Mode 1: height_u in internal usable mm              → height_u + GR_LIP_H + GR_BOT_H
        Mode 2: height_u is total external mm               → height_u (used as-is)
        Mode 3: height_u in external mm incl stacking lip   → height_u - GR_STACKING_LIP_H

        If enable_zsnap is True (1B.15), snaps the mode-specific content height
        to the next 7mm multiple before returning. Equivalent to Kennetek's
        z_snap(height(z, gridz_define)) applied after gridz_define conversion.

        Mode 0/1 content = the value z_snap operates on in Kennetek.
        Mode 2/3 content = (external_height - GR_STACKING_LIP_H) so the result stays
        in the standard-height form 4.4 + k*7 that mode 0 produces.
        """
        h = self._raw_height
        # Modes 2/3 promise an exact EXTERNAL height, so compensate for the
        # material the lip fillet removes -- otherwise asking for 8.00mm
        # silently yields 7.15mm. Modes 0/1 need no compensation: their nominal
        # height is to the theoretical sharp apex (what the drawings dimension),
        # and the finished part is reported by `actual_height`.
        if self.gridz_define in (2, 3):
            h += self._lip_setback
        return h

    @property
    def _lip_nominal(self):
        """Nominal lip contribution to external height, by style.

        The official "Bin Total Height" drawing gives two equations:
            with a lip:    Grid Z Unit * Height Units + Stacking Lip
            without a lip: Grid Z Unit * Height Units
        so lip_style="none" adds nothing at all -- a 6U no-lip bin is 42.0mm,
        not 46.4mm.
        """
        # "reduced" now carries the same rim taper as "normal", so it has the
        # same sharp apex and takes the same fillet -- no special case.
        return 0.0 if self.lip_style == "none" else GR_STACKING_LIP_H

    @property
    def _raw_height(self):
        """Height before any fillet compensation. See `height`."""
        z = self.height_u
        if self.gridz_define == 0:
            content = GRHU * z
            if self.enable_zsnap:
                content = self._z_snap(content)
            return content + self._lip_nominal
        elif self.gridz_define == 1:
            content = float(z)
            if self.enable_zsnap:
                content = self._z_snap(content)
            return content + GR_LIP_H + GR_BOT_H
        elif self.gridz_define == 2:
            if self.enable_zsnap:
                content = float(z) - GR_STACKING_LIP_H
                content = self._z_snap(content)
                return content + GR_STACKING_LIP_H
            return float(z)
        else:  # 3
            raw = float(z) - GR_STACKING_LIP_H
            if self.enable_zsnap:
                content = raw - GR_STACKING_LIP_H
                content = self._z_snap(content)
                return content + GR_STACKING_LIP_H
            return raw

    @property
    def has_lip_profile(self):
        """True if this bin actually grows a contoured stacking lip.

        Two ways to end up without one: a non-normal lip_style, or a bin so
        short that int_height goes negative -- render_interior() then falls
        back to a plain straight profile with no lip contour at all. Computed
        from _raw_height rather than height, since height depends on this.
        """
        if self.lip_style not in ("normal", "reduced"):
            return False
        return (self._raw_height - GR_LIP_H - GR_BOT_H) >= 0

    @property
    def _lip_setback(self):
        """How much the tip fillet lowers the apex, 0 if there is no fillet."""
        return GR_LIP_APEX_SETBACK if self.has_lip_profile else 0.0

    @property
    def actual_height(self):
        """Height of the finished part, after the lip tip fillet.

        `height` is the CONSTRUCTION height -- to the theoretical sharp apex,
        which is what the Gridfinity drawings dimension (7*u + 4.4). Rounding
        that apex removes material, so the part you measure is shorter.

        kennetek draws the same distinction: their stacking_lip_height()
        computes from the filleted profile and is documented as returning
        "The actual height, not nominal."
        """
        return self.height - self._lip_setback

    @property
    def int_height(self):
        h = self.height - GR_LIP_H - GR_BOT_H
        if self.lite_style:
            return h + self.wall_th
        return h

    @property
    def max_height(self):
        return self.int_height + GR_UNDER_H + GR_TOPSIDE_H

    @property
    def cavity_height(self):
        """Height of the interior cavity actually built by render_interior().

        For normal bins this is max_height. For very short bins (height_u=1)
        int_height is negative, render_interior() falls back to a single
        straight profile of (height - GR_BOT_H), and max_height is 0 -- so
        max_height is the wrong reference there. Using it would under-fill a
        solid box and pass 0 to extrude(), which raises
        Standard_Failure: BRepSweep_Translation::Constructor.
        """
        if self.int_height < 0:
            return self.height - GR_BOT_H
        return self.max_height

    @property
    def has_cavity(self):
        """True if this box has any interior volume above the floor.

        False when total height <= GR_BOT_H (7.0mm) -- the base profile and
        floor consume the whole box. Legitimate for a solid box used as a lid;
        meaningless for a hollow bin.
        """
        return self.cavity_height > EPS

    @property
    def floor_h(self):
        if self.lite_style:
            return GR_FLOOR - self.wall_th
        return GR_FLOOR

    @property
    def lip_width(self):
        if self.lip_style == "none":
            return self.wall_th
        return GR_UNDER_H + self.wall_th

    @property
    def inner_l(self):
        return self.outer_l - 2 * self.wall_th

    @property
    def inner_w(self):
        return self.outer_w - 2 * self.wall_th

    @property
    def inner_dim(self):
        return self.inner_l, self.inner_w

    @property
    def inner_rad(self):
        return self.outer_rad - self.wall_th

    @property
    def under_h(self):
        return GR_UNDER_H - (self.wall_th - GR_WALL)

    @property
    def safe_fillet_rad(self):
        rad = self.fillet_rad or GR_FILLET
        # Always clamp to inner corner radius to prevent CAD kernel crash
        rad = min(rad, self.inner_rad - 0.05)
        # has_dividers, not the raw length_div/width_div integers: a bin built
        # from explicit Divider objects has dividers too, and skipping this
        # clamp for it let the radius exceed the wall it has to blend into.
        if any([self.scoops, self.labels, self.has_dividers]):
            rad = min(rad, (GR_UNDER_H + GR_WALL) - self.wall_th - 0.05)
        # A fillet cannot be larger than the cavity it sits in. Very short bins
        # (a 7.01mm shell has 0.01mm of interior) would otherwise ask the
        # kernel for a radius 100x the available space and fail.
        if self.cavity_height > 0:
            rad = min(rad, self.cavity_height / 2)
        # A notched divider leaves tight topology around the U-cut that defeats
        # the fillet kernel at the default radius. Determined empirically:
        # 0.8mm fails, 0.5mm succeeds. Clamping keeps the blend rather than
        # dropping it entirely.
        if any(d.has_notch for d in self.divider_list):
            rad = min(rad, GR_NOTCH_FILLET_MAX)
        return max(rad, 0)

    @property
    def _gru(self):
        """Grid unit size: 21mm for half-grid (1B.13), 42mm for standard bins."""
        return GRU2 if self.half_grid else GRU

    @property
    def hole_centres(self):
        """Magnet/screw hole positions for this bin.

        Standard: 4 holes per cell at ±GR_HOLE_DIST from each cell centre.
        Half-grid (1B.13): only_corners — 4 corner hole clusters positioned at
        the equivalent full-grid (42mm) corners mapped into the half-grid
        pre-translation frame.  Ensures physical compatibility with standard
        Gridfinity baseplates (42mm grid, ±13mm hole offset).

        Returns [] when the bin is too small to fit any full-grid-aligned holes,
        i.e. when floor(length_u/2) < 1 or floor(width_u/2) < 1.
        """
        if not self.half_grid:
            return super().hole_centres
        n_full_l = math.floor(self.length_u / 2)
        n_full_w = math.floor(self.width_u / 2)
        if n_full_l < 1 or n_full_w < 1:
            return []
        # Deduplicated corner cells in the full-grid equivalent
        seen: set = set()
        corners = []
        for ci in (0, n_full_l - 1):
            for cj in (0, n_full_w - 1):
                if (ci, cj) not in seen:
                    seen.add((ci, cj))
                    corners.append((ci, cj))
        # Full-grid cell centre in the final (centred) coordinate frame:
        #   x_final = (ci - (n_full_l - 1) / 2) * GRU
        # Convert to pre-translation frame by adding half_dim:
        #   x_pretrans = x_final + half_l   (half_l uses GRU2 for half-grid)
        cx_off = self.half_l  # (length_u - 1) * GRU2 / 2
        cy_off = self.half_w  # (width_u - 1) * GRU2 / 2
        result = []
        for (ci, cj) in corners:
            cx = (ci - (n_full_l - 1) / 2) * GRU + cx_off
            cy = (cj - (n_full_w - 1) / 2) * GRU + cy_off
            for di in (-1, 1):
                for dj in (-1, 1):
                    result.append((cx - GR_HOLE_DIST * di, -(cy - GR_HOLE_DIST * dj)))
        return result

    @property
    def half_in(self):
        """Half interior width of a single grid cell (used for scoop/divider offsets).

        Scales with _gru so half-grid bins compute correct interior offsets.
        """
        return self._gru / 2 - self.wall_th - GR_TOL / 2

    @property
    def _filename_prefix(self) -> str:
        return "gf_bin_"

    def _filename_suffix(self) -> str:
        fn = "x%s" % self._fmt_unit(self.height_u)
        # Non-default height mode (1B.14): append _m{mode} so filenames are unambiguous
        if self.gridz_define != 0:
            fn += "_m%d" % self.gridz_define
        # Z-snap (1B.15): mark when enabled so snapped vs unsnapped filenames differ
        if self.enable_zsnap:
            fn += "_zs"
        # Half-grid mode (1B.13): mark before style to avoid ambiguity
        if self.half_grid:
            fn += "_hg"
        # 1. Construction style (broadest differentiator)
        if self.lite_style:
            fn += "_lite"
        elif self.solid:
            fn += "_solid"
        # 2. Lip style (omit for normal/default)
        if self.lip_style == "none":
            fn += "_nolip"
        elif self.lip_style == "reduced":
            fn += "_reduced"
        # 3. Bottom features
        if self.holes:
            fn += "_mag"
            if self.refined_holes:
                fn += "-refined"
            if self.crush_ribs:
                fn += "-ribs"
            if self.chamfer_holes:
                fn += "-chamfer"
            if self.printable_hole_top:
                fn += "-bridge"
        # 4. Interior features
        if not self.solid:
            if self.scoops:
                if self.scoops < 1.0:
                    fn += "_scoop%.1f" % self.scoops
                else:
                    fn += "_scoops"
            if self.labels:
                if self.label_style != "full":
                    fn += "_label-%s" % self.label_style
                else:
                    fn += "_labels"
            if self.compartment_depth > 0:
                fn += "_d%.1f" % self.compartment_depth
            elif self.height_internal > 0:
                fn += "_hi%.1f" % self.height_internal
            if self.cylindrical:
                fn += "_cyl%.0f" % self.cylinder_diam
            # Divider counts come from the resolved list, so an explicit layout
            # is named as accurately as the count-based sugar. "u" marks an
            # explicit (possibly unequal) layout so it cannot be confused with
            # an evenly divided bin of the same count.
            nx_div = len(self._dividers_on("x"))
            ny_div = len(self._dividers_on("y"))
            tag = "divu" if self.dividers is not None else "div"
            if nx_div:
                fn += "_%s%d" % (tag, nx_div)
            if ny_div:
                if nx_div:
                    fn += "x%d" % (ny_div)
                else:
                    fn += "_%sx%d" % (tag, ny_div)
        # 5. Non-default parameters
        if abs(self.wall_th - GR_WALL) > 1e-3:
            fn += "_w%.2f" % (self.wall_th)
        return fn

    def render(self):
        """Returns a CadQuery Workplane object representing this Gridfinity box."""
        # Save original divider counts so render() is idempotent.
        # try/finally ensures restoration even if an exception occurs.
        orig_length_div = self.length_div
        orig_width_div = self.width_div
        try:
            self._int_shell = None
            if self.lite_style:
                # Clamp dividers for lite_style: max one per full grid unit.
                # math.floor() supports non-integer length_u/width_u (1B.12).
                # Only applies to the count-based sugar -- an explicit divider
                # list is the caller stating exactly what they want, so we
                # respect it rather than silently rewriting their layout.
                if self.dividers is None:
                    if self.length_div:
                        self.length_div = math.floor(self.length_u) - 1
                    if self.width_div:
                        self.width_div = math.floor(self.width_u) - 1
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
            # A box cannot be shorter than its own base profile. Below this the
            # shell wall extrude collapses to zero or negative and OpenCASCADE
            # raises Standard_Failure: BRepSweep_Translation::Constructor.
            _min_h = GR_BASE_HEIGHT + GR_BASE_CLR
            if self.height <= _min_h:
                raise ValueError(
                    "Total height %.2f mm is not greater than the base profile "
                    "(%.2f mm). Nothing can be built above the Gridfinity feet."
                    % (self.height, _min_h)
                )
            if self.wall_th > 2.5:
                raise ValueError("Wall thickness cannot exceed 2.5 mm")
            if self.wall_th < 0.5:
                raise ValueError("Wall thickness must be at least 0.5 mm")
            self._ext_shell = None
            if self.cylindrical or self.hole_grid is not None:
                r = self.solid_shell()
                r = self._render_cylindrical_cuts(r)
            else:
                r = self.render_shell()
                rf = self._render_raised_floor()
                if rf is not None:
                    r = r.union(rf)
                rd = self.render_dividers()
                rs = self.render_scoops()
                rl = self.render_labels()
                for e in (rd, rl, rs):
                    if e is not None:
                        r = r.union(e)
                # Cullenect socket is cut AFTER the shelf is unioned in: it
                # is a pocket in that shelf, not a feature of its own.
                sock = self.render_cullenect_socket()
                if sock is not None:
                    r = r.cut(sock)
            if (
                not self.solid
                and not self.cylindrical
                and self.hole_grid is None
                and self.fillet_interior
            ):
                effective_floor = GR_FLOOR + self._floor_raise
                heights = [effective_floor]
                if self.labels:
                    heights.append(self.safe_label_height(backwall=True, from_bottom=True))
                    heights.append(self.safe_label_height(backwall=False, from_bottom=True))
                bs = (
                    HasZCoordinateSelector(heights, min_points=1, tolerance=0.5)
                    + VerticalEdgeSelector(">5")
                    - HasZCoordinateSelector("<%.2f" % (self.floor_h + self._floor_raise))
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

            r = self._fillet_lip_tip(r)
            if self.holes:
                r = self.render_holes(r)
            r = r.translate((-self.half_l, -self.half_w, GR_BASE_HEIGHT))
            if self.unsupported_holes:
                r = self.render_hole_fillers(r)
            r = self.assert_sound(r, "bin")
            return r
        finally:
            self.length_div = orig_length_div
            self.width_div = orig_width_div

    @property
    def top_ref_height(self):
        """The height of the top surface of a solid box or the floor
        height of an empty box."""
        if self.solid:
            return self.cavity_height * self.solid_ratio + GR_BOT_H
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
    def divider_list(self):
        """The dividers to build: explicit if given, else derived from counts.

        This is the single source of truth for every consumer -- walls, scoops
        along walls, label tab counts, hole-grid cell counts. `length_div` /
        `width_div` remain the ergonomic input for even spacing and are
        unchanged; they simply generate the same objects an explicit list would.
        """
        if self.dividers is not None:
            return list(self.dividers)
        return dividers_from_counts(self.length_div, self.width_div)

    def _dividers_on(self, axis):
        """Dividers splitting the given axis, ordered by position."""
        return sorted(
            (d for d in self.divider_list if d.axis == axis), key=lambda d: d.pos
        )

    @property
    def has_dividers(self):
        return len(self.divider_list) > 0

    def _divider_offset(self, d):
        """Absolute coordinate of a divider in the pre-translation frame.

        The interior's low edge sits at -half_in on BOTH axes (algebraically:
        half_l - inner_l/2 == -(gru/2 - wall_th - GR_TOL/2) == -half_in, and
        likewise for width), which is why one constant serves both.
        """
        span = self.inner_l if d.axis == "x" else self.inner_w
        return d.pos * span - self.half_in

    @property
    def interior_solid(self):
        if self._int_shell is not None:
            return self._int_shell
        self._int_shell = self.render_interior()
        return self._int_shell

    def render_interior(self, force_solid=False):
        """Renders the interior cutting solid of the box, or None if there is none.

        Returns None when the box has no cavity at all (total height <=
        GR_BOT_H). Callers must skip their cut in that case -- the shell is
        already the finished object. Previously this built a zero- or
        negative-height profile and OpenCASCADE raised
        Standard_Failure: BRepSweep_Translation::Constructor.
        """
        if not self.has_cavity:
            if not (self.solid or force_solid):
                raise ValueError(
                    "Bin height %.2f mm leaves no interior cavity: the base "
                    "profile and floor consume everything up to %.2f mm. "
                    "Use solid=True for a lid, or increase the height."
                    % (self.height, GR_BOT_H)
                )
            return None
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
            hs = self.cavity_height * self.solid_ratio
            # solid_ratio=0 (or a zero-height cavity) means nothing to fill;
            # extrude(0) would raise Standard_Failure.
            if hs > EPS:
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
        inner = self.render_interior(force_solid=True)
        self._ext_shell = r if inner is None else r.cut(inner)
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
        cell = self._gru  # 21mm for half-grid, 42mm for standard (1B.13)
        r = self.extrude_profile(
            rounded_rect_sketch(cell - GR_TOL, cell - GR_TOL, self.outer_rad),
            profile,
        )
        rx = r.faces("<Z").shell(-self.wall_th)
        r = r.cut(rx).mirror(mirrorPlane="XY").translate((0, 0, zo))
        return r

    def render_shell(self, as_solid=False):
        """Renders the box shell without any added features."""
        r = self.extrude_profile(
            rounded_rect_sketch(self._gru, self._gru, self.outer_rad + GR_BASE_CLR), GR_BOX_PROFILE
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
            interior = self.interior_solid
            if interior is None:
                return rc  # no cavity (e.g. a 1U solid lid) -- shell is final
            return rc.cut(interior)
        return rc

    def render_dividers(self):
        """Build every divider wall from `divider_list`.

        Each wall is placed individually rather than as a patterned array, so
        unequal spacing, per-divider thickness and height, notches and angled
        tops all fall out of the same loop instead of needing separate paths.
        """
        if self.solid:
            return None
        r = None
        for d in self.divider_list:
            wall = self._render_divider_wall(d)
            if wall is None:
                continue
            r = wall if r is None else r.union(wall)
        return r

    def _render_divider_wall(self, d):
        """One divider wall, including its notch and angled top if set."""
        height = self.max_height if d.height is None else min(d.height, self.max_height)
        if height <= EPS:
            return None
        # Wall spans the full outer dimension of the other axis; the shell cut
        # trims the overhang, which is how the original array-based code worked.
        if d.axis == "x":
            section, centre = (d.thickness, self.outer_w), (
                self._divider_offset(d),
                self.half_w,
            )
            span = self.outer_w
        else:
            section, centre = (self.outer_l, d.thickness), (
                self.half_l,
                self._divider_offset(d),
            )
            span = self.outer_l
        wall = (
            cq.Workplane("XY")
            .rect(*section)
            .extrude(height)
            .translate((*centre, self.floor_h))
        )
        wall = self._apply_divider_top_angle(wall, d, height, span)
        wall = self._apply_divider_notch(wall, d, height, span, centre)
        return wall

    def _apply_divider_top_angle(self, wall, d, height, span):
        """Give the divider a symmetric roof so items drop in without catching.

        The top becomes a ridge: it peaks on the wall's centreline and slopes
        down to zero at both faces at `top_angle` from horizontal. A one-sided
        chamfer would bias items toward one compartment; a ridge sheds into
        either. Used for filing flat items upright (ostat 1D.12).
        """
        if not d.top_angle:
            return wall
        th = d.thickness
        rise = (th / 2) * math.tan(math.radians(abs(d.top_angle)))
        rise = min(rise, height - EPS)
        if rise <= EPS:
            return wall
        top_z = self.floor_h + height
        # Region ABOVE the two roof planes. Extended to +/-th (twice the
        # half-thickness) along the same slope lines, so the cutter overhangs
        # the wall faces instead of sharing them -- coincident faces are where
        # boolean ops get fragile. The slope still reaches z=0 exactly at
        # +/-th/2, which is the wall surface.
        profile = [
            (-th, -rise),
            (0.0, rise),
            (th, -rise),
            (th, 2 * rise),
            (-th, 2 * rise),
        ]
        plane = "XZ" if d.axis == "x" else "YZ"
        cutter = cq.Workplane(plane).polyline(profile).close().extrude(span + 2)
        # Position by bounding box rather than assuming an extrude direction:
        # Workplane("XZ") extrudes toward -Y, "YZ" toward +X, and relying on
        # that sign is exactly the bug this replaces.
        offs = self._divider_offset(d)
        cx, cy = (offs, self.half_w) if d.axis == "x" else (self.half_l, offs)
        bb = cutter.val().BoundingBox()
        cutter = cutter.translate(
            (
                cx - (bb.xmin + bb.xmax) / 2,
                cy - (bb.ymin + bb.ymax) / 2,
                top_z - (bb.zmin + bb.zmax) / 2 - rise / 2,
            )
        )
        return wall.cut(cutter)

    def _apply_divider_notch(self, wall, d, height, span, centre):
        """Cut a U-notch down from the top so long items bridge compartments."""
        if not d.has_notch:
            return wall
        depth = min(d.notch_depth, height - EPS)
        if depth <= EPS:
            return wall
        width = d.notch_width if d.notch_width > 0 else span / 2
        top_z = self.floor_h + height
        if d.axis == "x":
            cutter = (
                cq.Workplane("XY")
                .rect(d.thickness * 3, width)
                .extrude(depth + EPS)
                .translate((centre[0], centre[1], top_z - depth))
            )
        else:
            cutter = (
                cq.Workplane("XY")
                .rect(width, d.thickness * 3)
                .extrude(depth + EPS)
                .translate((centre[0], centre[1], top_z - depth))
            )
        return wall.cut(cutter)

    def render_scoops(self):
        if not self.scoops or self.solid:
            return None
        # front wall scoop
        # Scale scoop radius by scoop factor (0.0-1.0)
        raise_h = self._floor_raise
        effective_h = self.int_height - raise_h
        if effective_h <= 0.1:
            return None
        srad = min(self.scoop_rad * self.scoops, effective_h - 0.1)
        if srad <= 0:
            return None
        rs = cq.Sketch().rect(srad, srad).vertices(">X and >Y").circle(srad, mode="s")
        rsc = cq.Workplane("YZ").placeSketch(rs).extrude(self.inner_l)
        rsc = rsc.translate((0, 0, srad / 2 + GR_FLOOR + raise_h))
        yo = -self.half_in + srad / 2
        # offset front wall scoop by top lip overhang if applicable
        if self.lip_style != "none" and not self.lite_style:
            yo += self.under_h
        zo = -GR_BOT_H + self.wall_th if self.lite_style else 0
        rs = rsc.translate((-self.half_in, yo, zo))
        # intersect to prevent solids sticking out of rounded corners
        r = rs.intersect(self.interior_solid)
        y_divs = self._dividers_on("y")
        if y_divs:
            # add scoops along each internal dividing wall in the width dimension
            pts = [(-self.half_in, self._divider_offset(d)) for d in y_divs]
            rs = composite_from_pts(rsc, pts)
            r = r.union(rs.translate((0, GR_DIV_WALL / 2 + srad / 2, zo)))
            r = r.intersect(self.render_shell(as_solid=True))
        return r

    def _build_label_wall(self, sketch, spans, yo, z_top):
        """Build label geometry for one wall (back wall or divider wall).

        Returns a CadQuery solid (full-width or positioned tabs), or None.
        """
        if self.label_style == "full":
            rsc = cq.Workplane("YZ").placeSketch(sketch).extrude(self.inner_l)
            return rsc.translate((-self.half_in, yo, z_top))
        else:
            r = None
            for tab_x, tab_w in self._compute_tab_positions(spans):
                rsc = cq.Workplane("YZ").placeSketch(sketch).extrude(tab_w)
                rsc = rsc.translate((tab_x, yo, z_top))
                r = rsc if r is None else r.union(rsc)
            return r

    def render_cullenect_socket(self):
        """Socket for a click-in Cullenect label, cut into the label shelf (1D.5).

        1D.3 and 1D.4 give you a tile and a negative volume; this is what puts
        the socket on a bin, so the tile has somewhere to go. Without it the
        feature is two parts and no way to bring them together.

        The shelf's top face is flat and horizontal, so the socket is a plain
        pocket in it: a label lying there reads from above, which is how bins
        in a drawer are read. The tile is sized to the bin's own width in grid
        units, and the pocket is centred on the shelf.
        """
        if not self.cullenect_socket:
            return None
        if not self.labels or self.solid or self.label_style == "none":
            raise ValueError(
                "cullenect_socket needs a label shelf to cut into: set "
                "labels=True (and not solid, and label_style != 'none')"
            )
        from cqgridfinity.gf_labels import CullenectLabel

        shelf = self.render_labels()
        if shelf is None:
            return None
        bb = shelf.val().BoundingBox()
        tile = CullenectLabel(self.cullenect_label_u_for(bb.xlen))
        if tile.socket_length > bb.xlen or tile.socket_width > bb.ylen:
            raise ValueError(
                "a %gU Cullenect socket is %.1f x %.1f mm and will not fit the "
                "%.1f x %.1f mm label shelf. Even a 1U tile needs %.1fmm; use "
                "a wider label_style or a deeper label_width"
                % (tile.width_u, tile.socket_length, tile.socket_width,
                   bb.xlen, bb.ylen, CullenectLabel(1).socket_length)
            )
        neg = tile.socket_negative()
        # Drop the pocket into the shelf's top face, centred on it.
        return neg.translate(
            (
                (bb.xmin + bb.xmax) / 2,
                (bb.ymin + bb.ymax) / 2,
                bb.zmax - tile.thickness,
            )
        )

    def cullenect_label_u_for(self, shelf_length):
        """Largest tile that fits the shelf, in grid units.

        Sized from the SHELF, not from `length_u`. With `label_style="full"`
        the shelf spans the bin and the two agree, but every tab style
        ("auto", "left", "center", "right") gives a shelf about one grid unit
        long whatever the bin's width -- and sizing the tile off the bin then
        demanded a 120mm tile for a 42mm tab and refused to build at all.
        """
        if self.cullenect_label_u > 0:
            return self.cullenect_label_u
        from cqgridfinity.gf_labels import CullenectLabel

        u = 1
        while CullenectLabel(u + 1).socket_length <= shelf_length:
            u += 1
        return u

    def render_labels(self):
        if not self.labels or self.solid or self.label_style == "none":
            return None
        # back wall label flange with compensated width and height
        lw = self.label_width + self.lip_width
        back_sketch = (
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
        yo = -lw + self.outer_w / 2 + self.half_w + self.wall_th / 4
        z_top = self.floor_h + self.max_height
        spans = self._compartment_spans("x")

        r = self._build_label_wall(back_sketch, spans, yo, z_top)
        if r is None:
            return None
        r = r.intersect(self.interior_solid)

        if self._dividers_on("y"):
            # add label flanges along each dividing wall
            div_sketch = (
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
            for d in self._dividers_on("y"):
                div_yo = self._divider_offset(d) + d.thickness / 2
                wall = self._build_label_wall(
                    div_sketch, spans, div_yo - self.label_width, z_top
                )
                if wall is not None:
                    r = r.union(wall)
        return r

    def _compartment_spans(self, axis):
        """(start, length) of each compartment along an axis, low edge first.

        Boundaries are divider *centres*, matching how the original uniform
        arithmetic worked -- it never subtracted wall thickness either. For
        evenly spaced dividers this returns exactly the same spans as
        `i * inner/(n+1) - half_in`; it simply also handles unequal spacing.
        """
        span = self.inner_l if axis == "x" else self.inner_w
        lo = -self.half_in
        bounds = [lo]
        bounds += [self._divider_offset(d) for d in self._dividers_on(axis)]
        bounds.append(lo + span)
        return [(bounds[i], bounds[i + 1] - bounds[i]) for i in range(len(bounds) - 1)]

    def _compute_tab_positions(self, spans):
        """Compute (x_start, width) pairs for each compartment's label tab."""
        positions = []
        for comp_start, comp_length in spans:
            tab_w = min(self._gru, comp_length)  # tab max width = 1 grid unit
            if self.label_style in ("auto", "center"):
                tab_x = comp_start + (comp_length - tab_w) / 2
            elif self.label_style == "right":
                tab_x = comp_start + comp_length - tab_w
            else:  # "left", "full", or any other -- anchor to the compartment
                tab_x = comp_start
            positions.append((tab_x, tab_w))
        return positions

    def _fillet_lip_tip(self, obj):
        """Round the stacking lip tip so it is not a zero-thickness edge.

        The spec's full-height lip converges to a true point ("Bin Sharp
        Stacking Lip Profile"). That is not manufacturable, so the spec also
        publishes a rounded variant and kennetek fillets it by 0.6mm. Only
        lip_style="normal" produces the sharp tip -- "reduced" and "none"
        already terminate in a flat rim, so they are left alone.
        """
        # Applies to solid boxes too: a solid bin still carries a stacking lip,
        # so it has the same sharp tip. Bins too short to grow a lip contour
        # have a flat rim already and need no fillet.
        if not self.has_lip_profile:
            return obj
        top = obj.val().BoundingBox().zmax
        edges = obj.edges(HasZCoordinateSelector(top))
        if not edges.vals():
            return obj
        try:
            return edges.fillet(GR_LIP_FILLET)
        except Exception:
            # Visible, not swallowed: the bin is still valid, it just keeps a
            # sharp lip tip. Silent no-ops on edge treatment have bitten this
            # codebase twice already (see LEARNING-LOG).
            warnings.warn(
                "%s: could not fillet the stacking lip tip; it stays sharp. "
                "Geometry is otherwise valid." % (self.__class__.__name__,),
                stacklevel=2,
            )
            return obj

    def render_holes(self, obj):
        """Cut magnet/screw holes from the bottom face of the bin.

        Standard holes use CadQuery's .cboreHole() for exact geometry match
        with upstream cq-gridfinity. Enhanced hole features (crush_ribs,
        chamfer, etc.) use gf_holes boolean cutting for the additional geometry.
        """
        if not self.holes or not self.hole_centres:
            return obj

        has_enhanced = any([
            self.refined_holes,
            self.crush_ribs,
            self.chamfer_holes,
            self.printable_hole_top,
        ])

        if has_enhanced:
            # Enhanced holes use the shared gf_holes pipeline
            mag_depth = GR_HOLE_H
            if self.unsupported_holes:
                mag_depth += GR_HOLE_SLICE
            z_bottom = -GR_BASE_HEIGHT
            return cut_enhanced_holes(
                obj, self.hole_centres, z_offset=z_bottom,
                diameter=self.hole_diam, depth=mag_depth,
                refined=self.refined_holes, crush_ribs=self.crush_ribs,
                chamfer=self.chamfer_holes, printable_top=self.printable_hole_top,
                include_screw=True, screw_diameter=GR_BOLT_D, screw_depth=GR_BOLT_H,
            )
        else:
            # Standard holes: use .cboreHole() for exact upstream geometry match
            h = GR_HOLE_H
            if self.unsupported_holes:
                h += GR_HOLE_SLICE
            return (
                obj.faces("<Z")
                .workplane()
                .pushPoints(self.hole_centres)
                .cboreHole(GR_BOLT_D, self.hole_diam, h, depth=GR_BOLT_H)
            )

    def render_hole_fillers(self, obj):
        """Add printable bridge fillers at hole positions for unsupported printing.

        Uses gf_holes.hole_filler() for consistency with the shared hole module.
        """
        if not self.hole_centres:
            return obj
        filler = hole_filler(self.hole_diam, GR_HOLE_SLICE)
        fillers = composite_from_pts(filler, self.hole_centres)
        return obj.union(fillers.translate((-self.half_l, self.half_w, 0)))

    @property
    def _floor_raise(self):
        """Amount the compartment floor is raised above the standard floor."""
        if self.height_internal > 0:
            return max(self.int_height - self.height_internal, 0)
        return max(self.compartment_depth, 0)

    def _render_raised_floor(self):
        """Create a raised floor block for custom compartment depth."""
        raise_h = self._floor_raise
        if raise_h <= 0:
            return None
        rs = rounded_rect_sketch(*self.inner_dim, self.inner_rad)
        rf = cq.Workplane("XY").placeSketch(rs).extrude(raise_h)
        return rf.translate((*self.half_dim, self.floor_h))

    @property
    def _resolved_hole_grid(self):
        """The hole grid to cut, or None.

        `cylindrical=True` is sugar for a circular grid laid out on the bin's
        compartments, so the old parameters keep working unchanged.
        """
        if self.hole_grid is not None:
            return self.hole_grid
        if self.cylindrical:
            return HoleGrid(
                shape="circle",
                size=self.cylinder_diam,
                chamfer=self.cylinder_chamfer,
            )
        return None

    def _hole_grid_positions(self, grid):
        """Centres for each hole, and the space available around one hole."""
        x_spans = self._compartment_spans("x")
        y_spans = self._compartment_spans("y")
        if grid.derives_layout:
            # One hole per compartment -- the original cylindrical behaviour.
            pts = [
                (xs + xl / 2, ys + yl / 2)
                for xs, xl in x_spans
                for ys, yl in y_spans
            ]
            avail = (min(l for _, l in x_spans), min(l for _, l in y_spans))
            return pts, avail
        cols, rows = grid.cols, grid.rows
        px, py = grid.effective_pitch
        if px is None and py is None:
            # Spread evenly to fill the interior. No slack exists, so the
            # alignment settings have nothing to act on.
            pitch_x, pitch_y = self.inner_l / cols, self.inner_w / rows
            x0, y0 = -self.half_in, -self.half_in
            pts = [
                (x0 + (i + 0.5) * pitch_x, y0 + (j + 0.5) * pitch_y)
                for i in range(cols)
                for j in range(rows)
            ]
            return pts, (pitch_x, pitch_y)

        # Fixed pitch: the array occupies only part of the interior, and the
        # leftover goes wherever align_x/align_y say.
        fx, fy = grid.footprint()
        pitch_x = px if px is not None else self.inner_l / cols
        pitch_y = py if py is not None else self.inner_w / rows
        first_x = self._aligned_start(
            self.inner_l, (cols - 1) * pitch_x + fx, grid.align_x, fx
        )
        first_y = self._aligned_start(
            self.inner_w, (rows - 1) * pitch_y + fy, grid.align_y, fy
        )
        pts = [
            (first_x + i * pitch_x, first_y + j * pitch_y)
            for i in range(cols)
            for j in range(rows)
        ]
        return pts, (pitch_x, pitch_y)

    def _aligned_start(self, interior, occupied, align, hole_extent):
        """Centre of the first hole along one axis, honouring alignment.

        align -1 puts the slack at the high edge (array flush low), 0 splits it,
        +1 puts it at the low edge. Same convention as baseplate fitx/fity.
        """
        slack = max(interior - occupied, 0.0)
        offset = slack / 2.0 * (1.0 + align)
        return -self.half_in + offset + hole_extent / 2.0

    def _hole_cutter(self, grid, height):
        """One hole solid of the configured shape, chamfered at the mouth."""
        if grid.shape == "circle":
            cutter = cq.Workplane("XY").circle(grid.effective_size / 2).extrude(height)
            limit = grid.effective_size / 2
        elif grid.shape == "hex":
            # polygon() takes the circumscribed diameter; hex stock is
            # specified across flats, so convert.
            across_corners = grid.effective_size * 2.0 / math.sqrt(3.0)
            cutter = cq.Workplane("XY").polygon(6, across_corners).extrude(height)
            limit = grid.effective_size / 2
        else:  # rect
            cutter = (
                cq.Workplane("XY")
                .rect(grid.effective_size, grid.effective_size_y)
                .extrude(height)
            )
            limit = min(grid.effective_size, grid.effective_size_y) / 2
        if grid.chamfer > 0:
            cf = min(grid.chamfer, height / 2 - 0.01, limit - 0.01)
            if cf > 0:
                cutter = cutter.edges(">Z").chamfer(cf)
        return cutter

    def _render_cylindrical_cuts(self, obj):
        """Cut an array of shaped holes into a solid bin shell.

        Subtractive construction: the shell is solid and holes are removed,
        which is a different build from the additive hollow-shell path. The two
        stay separate modes rather than being forced into one pipeline.
        """
        grid = self._resolved_hole_grid
        if grid is None:
            return obj
        pts, avail = self._hole_grid_positions(grid)
        if not pts:
            return obj

        # Shrink to fit the tightest cell. With unequal compartments the
        # smallest one governs, so a single size still fits everywhere.
        fx, fy = grid.footprint()
        scale = min((avail[0] - 0.5) / fx, (avail[1] - 0.5) / fy, 1.0)
        if scale <= 0:
            return obj
        if scale < 1.0:
            grid = replace(
                grid,
                size=grid.size * scale,
                size_y=None if grid.size_y is None else grid.size_y * scale,
            )

        raise_h = self._floor_raise
        # Must use max_height, not int_height: solid_shell() fills the interior
        # up to max_height + floor_h (not just int_height + floor_h). Using
        # int_height leaves a 2.8mm ceiling (GR_UNDER_H + GR_TOPSIDE_H) that
        # seals the holes from the top and makes the bin appear solid.
        full_h = self.max_height - raise_h
        depth = full_h if grid.depth is None else min(grid.depth, full_h)
        if depth <= 0:
            return obj
        cyl = self._hole_cutter(grid, depth)
        # A depth-limited grid must open at the TOP, so sink it from there.
        z_top = self.floor_h + raise_h + full_h
        pts = [(x, y, 0) for x, y in pts]
        cuts = composite_from_pts(cyl.translate((0, 0, z_top - depth)), pts)
        return obj.cut(cuts)


class GridfinitySolidBox(GridfinityBox):
    """Convenience class to represent a solid Gridfinity box."""

    def __init__(self, length_u, width_u, height_u, **kwargs):
        super().__init__(length_u, width_u, height_u, **kwargs, solid=True)
        # Set by as_lid() so filenames say "lid" and report thickness rather
        # than leaking total height and the gridz_define mode number.
        self._is_lid = False

    @property
    def _filename_prefix(self) -> str:
        # NOTE: the base is a @property, so this override needs the decorator
        # too, and super() cannot call it. Read the parent value explicitly.
        if self._is_lid:
            return "gf_lid_"
        return GridfinityBox._filename_prefix.fget(self)

    def _filename_suffix(self) -> str:
        if not self._is_lid:
            return super()._filename_suffix()
        return "_th%s" % self._fmt_unit(self.lid_thickness)

    @classmethod
    def as_lid(cls, length_u, width_u, thickness=None, **kwargs):
        """Build a Gridfinity lid: a solid box specified by material thickness.

        A lid is a solid box whose feet drop into the stacking lip of the bin
        below, holding it located. It rests; it does not latch.

        `thickness` is the material ABOVE the 4.75mm Gridfinity feet -- the
        number you actually care about. Total height is derived as
        GR_BASE_HEIGHT + thickness, so you never do that arithmetic yourself.

            GridfinitySolidBox.as_lid(2, 3)                 # 3.25mm -> 8.00mm total
            GridfinitySolidBox.as_lid(2, 3, thickness=2.0)  # 2.00mm -> 6.75mm total

        Defaults live in constants.py: GR_LID_TH (default) and GR_LID_TH_MIN
        (floor). Retune them there rather than passing a value everywhere.

        Raises ValueError below GR_LID_TH_MIN. That floor is a *policy* -- the
        geometry stays valid down to ~0.26mm, but a lid that thin is a handful
        of layers spanning the whole footprint and will warp and flex. The
        separate geometric floor is enforced in GridfinityBox.render().
        """
        th = GR_LID_TH if thickness is None else float(thickness)
        if th < GR_LID_TH_MIN:
            raise ValueError(
                "Lid thickness %.2f mm is below the %.2f mm minimum "
                "(one wall thickness). That is only %d layer(s) at 0.2 mm "
                "spanning the full footprint -- it will warp and flex. "
                "Lower GR_LID_TH_MIN in constants.py to override."
                % (th, GR_LID_TH_MIN, max(1, round(th / 0.2)))
            )
        # gridz_define=2: height_u is total external mm.
        obj = cls(length_u, width_u, GR_BASE_HEIGHT + th, gridz_define=2, **kwargs)
        obj._is_lid = True
        return obj

    @property
    def lid_thickness(self):
        """Material above the Gridfinity feet, in mm."""
        return self.height - GR_BASE_HEIGHT
