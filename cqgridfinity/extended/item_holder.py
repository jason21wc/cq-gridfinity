#! /usr/bin/env python3
#
# Gridfinity Item Holders — bins with shaped pocket arrays
#
# Copyright (C) 2026  Jason Collier
# MIT License (see LICENSE)

import math
import os

import cadquery as cq

from cqgridfinity import *
from cqgridfinity.gf_box import GridfinityBox
from cqgridfinity.extended.cutouts import RoundCutout, RectCutout, layout_cutouts
from cqgridfinity.extended.presets import ALL_PRESETS


class GridfinityItemHolder(GridfinityBox):
    """A Gridfinity bin with shaped pocket arrays for specific items.

    Extends GridfinityBox — inherits wall patterns, lip styles, holes,
    labels, scoops, and all other bin features. Adds cutout pockets
    in the bin floor.

    Usage:
      # From preset
      h = GridfinityItemHolder(3, 2, 3, item_preset="AA")

      # Custom round pockets
      h = GridfinityItemHolder(2, 2, 3, item_diameter=10.0, item_height=20.0)

      # Custom rectangular pockets
      h = GridfinityItemHolder(2, 2, 3, item_width=24.0, item_depth=2.1, item_height=30.0)

    Parameters (in addition to all GridfinityBox params):
      item_preset: Named preset from presets.py (e.g., "AA", "SD", "hex_quarter")
      item_diameter: Pocket diameter for round items (mm)
      item_width: Pocket width for rectangular items (mm)
      item_depth: Pocket depth for rectangular items (mm)
      item_height: Pocket depth/height (mm); auto-clamped to available floor space
      item_clearance: Fit tolerance added to pocket dimensions (mm)
      item_chamfer: Top chamfer on each pocket for easy insertion (mm)
      grid_x: Number of pockets in X (0 = auto-calculate)
      grid_y: Number of pockets in Y (0 = auto-calculate)
      grid_style: "square", "hex", or "auto"
      grid_spacing: Gap between pockets (mm)
    """

    def __init__(self, length_u, width_u, height_u, **kwargs):
        self.item_preset = None
        self.item_diameter = None
        self.item_width = None
        self.item_depth = None
        self.item_height = None
        self.item_clearance = 0.25
        self.item_chamfer = 0.5
        self.grid_x = 0
        self.grid_y = 0
        self.grid_style = "auto"
        self.grid_spacing = 2.0
        super().__init__(length_u, width_u, height_u, **kwargs)
        if self.item_preset:
            self._apply_preset()
        if self.grid_style == "auto":
            self.grid_style = "hex" if self.item_diameter else "square"
        self._auto_grid()

    def _apply_preset(self):
        """Resolve a named preset to item dimensions."""
        p = ALL_PRESETS.get(self.item_preset)
        if p is None:
            raise ValueError(
                "Unknown item preset: '%s'. Available: %s"
                % (self.item_preset, ", ".join(sorted(ALL_PRESETS.keys())))
            )
        if "diameter" in p:
            if self.item_diameter is None:
                self.item_diameter = p["diameter"]
        else:
            if self.item_width is None:
                self.item_width = p["width"]
            if self.item_depth is None:
                self.item_depth = p["depth"]
        if self.item_height is None:
            self.item_height = p.get("height")

    def _auto_grid(self):
        """Calculate grid dimensions if not explicitly set."""
        cutout = self._build_cutout()
        if cutout is None:
            return
        pitch_x = cutout.pitch_x + self.grid_spacing
        pitch_y = cutout.pitch_y + self.grid_spacing
        margin = self.grid_spacing
        avail_x = self.inner_l - 2 * margin
        avail_y = self.inner_w - 2 * margin
        if self.grid_x == 0:
            self.grid_x = max(1, int(avail_x / pitch_x) + 1)
            # Verify fit
            while self.grid_x > 1 and (self.grid_x - 1) * pitch_x + cutout.pitch_x > avail_x:
                self.grid_x -= 1
        if self.grid_y == 0:
            if self.grid_style == "hex":
                row_pitch = pitch_y * math.sqrt(3) / 2
                self.grid_y = max(1, int(avail_y / row_pitch) + 1)
                while self.grid_y > 1 and (self.grid_y - 1) * row_pitch + cutout.pitch_y > avail_y:
                    self.grid_y -= 1
            else:
                self.grid_y = max(1, int(avail_y / pitch_y) + 1)
                while self.grid_y > 1 and (self.grid_y - 1) * pitch_y + cutout.pitch_y > avail_y:
                    self.grid_y -= 1

    def _build_cutout(self):
        """Create the cutout profile from item parameters."""
        if self.item_diameter is not None:
            h = self._clamped_height()
            return RoundCutout(
                diameter=self.item_diameter,
                height=h,
                clearance=self.item_clearance,
                chamfer=self.item_chamfer,
            )
        elif self.item_width is not None and self.item_depth is not None:
            h = self._clamped_height()
            return RectCutout(
                width=self.item_width,
                depth=self.item_depth,
                height=h,
                clearance=self.item_clearance,
                chamfer=self.item_chamfer,
            )
        return None

    def _clamped_height(self):
        """Clamp pocket height to available interior space."""
        if self.item_height is None:
            return max(self.int_height - 1.0, 1.0)
        # Don't cut deeper than the interior allows
        max_h = self.int_height - 0.5
        return max(min(self.item_height, max_h), 1.0)

    def render(self):
        """Render the item holder: standard bin + pocket array cut from floor."""
        r = super().render()
        cutout = self._build_cutout()
        if cutout is None:
            return r
        grid = layout_cutouts(
            cutout, self.grid_x, self.grid_y,
            spacing=self.grid_spacing,
            style=self.grid_style,
        )
        if grid is None:
            return r
        # Position the cutout array at the bin floor level.
        # After super().render(), the bin is centered at XY origin
        # with Z=0 at the base bottom. Floor is at Z = GR_BASE_HEIGHT + GR_FLOOR.
        # Offset by EPS below the floor to avoid coplanar boolean failure
        # (see LEARNING-LOG.md: "Coplanar Face Boolean Cuts").
        z_floor = GR_BASE_HEIGHT + GR_FLOOR - EPS
        grid = grid.translate((0, 0, z_floor))
        r = r.cut(grid)
        return r

    def filename(self, prefix=None, path=None):
        if prefix is not None:
            fn_prefix = prefix
        else:
            fn_prefix = "gf_itemholder_"
        fn = ""
        if path is not None:
            fn = path + os.sep
        fn += fn_prefix
        fn += "%dx%dx%d" % (self.length_u, self.width_u, self.height_u)
        # Item descriptor
        if self.item_preset:
            fn += "_%s" % self.item_preset
        elif self.item_diameter:
            fn += "_r%.0f" % self.item_diameter
        elif self.item_width:
            fn += "_%.0fx%.0f" % (self.item_width, self.item_depth)
        # Layout
        fn += "_%s" % self.grid_style
        # Grid count
        fn += "_%dx%d" % (self.grid_x, self.grid_y)
        return fn
