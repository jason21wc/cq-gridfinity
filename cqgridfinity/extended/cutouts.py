#! /usr/bin/env python3
#
# Gridfinity Cutout Profiles — shaped pockets for item holders and trays
#
# Copyright (C) 2026  Jason Collier
# MIT License (see LICENSE)

import math

import cadquery as cq

from cqgridfinity import EPS


class CutoutProfile:
    """Base class for cutout shapes.

    A cutout generates a CadQuery solid that can be subtracted from a bin
    floor to create a shaped pocket. Subclasses define the shape.

    Parameters:
      width: X extent in mm
      depth: Y extent in mm
      height: Z extent (pocket depth) in mm
      clearance: Added to all lateral dimensions for fit tolerance
      chamfer: Top edge chamfer for easier insertion (0 to disable)
    """

    def __init__(self, width, depth, height, clearance=0.25, chamfer=0.5, **kwargs):
        self.width = width
        self.depth = depth
        self.height = height
        self.clearance = clearance
        self.chamfer = chamfer
        for k, v in kwargs.items():
            if k in self.__dict__:
                self.__dict__[k] = v

    @property
    def effective_width(self):
        return self.width + 2 * self.clearance

    @property
    def effective_depth(self):
        return self.depth + 2 * self.clearance

    def render(self):
        """Return a CadQuery solid at origin, extending +Z by self.height."""
        raise NotImplementedError

    @property
    def pitch_x(self):
        """Minimum X spacing center-to-center."""
        return self.effective_width

    @property
    def pitch_y(self):
        """Minimum Y spacing center-to-center."""
        return self.effective_depth


class RoundCutout(CutoutProfile):
    """Circular pocket (batteries, round tool shanks).

    Parameters:
      diameter: Hole diameter in mm
      height: Pocket depth in mm
    """

    def __init__(self, diameter, height, **kwargs):
        super().__init__(diameter, diameter, height, **kwargs)
        self.diameter = diameter

    @property
    def effective_diameter(self):
        return self.diameter + 2 * self.clearance

    @property
    def pitch_x(self):
        return self.effective_diameter

    @property
    def pitch_y(self):
        return self.effective_diameter

    def render(self):
        r = self.effective_diameter / 2
        obj = cq.Workplane("XY").circle(r).extrude(self.height)
        if self.chamfer > 0:
            # Chamfer the top edge for easier insertion
            chamf = min(self.chamfer, r * 0.4, self.height * 0.4)
            if chamf > EPS:
                obj = obj.faces(">Z").edges().chamfer(chamf)
        return obj


class RectCutout(CutoutProfile):
    """Rectangular pocket (cards, cartridges, tools).

    Parameters:
      width: X extent in mm
      depth: Y extent in mm
      height: Pocket depth in mm
      corner_rad: Internal corner radius for printability
    """

    def __init__(self, width, depth, height, corner_rad=0.5, **kwargs):
        super().__init__(width, depth, height, **kwargs)
        self.corner_rad = corner_rad

    def render(self):
        ew = self.effective_width
        ed = self.effective_depth
        obj = cq.Workplane("XY").rect(ew, ed).extrude(self.height)
        # Fillet vertical corners for printability
        if self.corner_rad > 0:
            rad = min(self.corner_rad, ew / 2 - EPS, ed / 2 - EPS)
            if rad > EPS:
                obj = obj.edges("|Z").fillet(rad)
        if self.chamfer > 0:
            chamf = min(self.chamfer, ew / 4, ed / 4, self.height * 0.4)
            if chamf > EPS:
                obj = obj.faces(">Z").edges().chamfer(chamf)
        return obj


def layout_cutouts(cutout, grid_x, grid_y, spacing=2.0, style="square"):
    """Arrange cutout instances in a grid pattern.

    Parameters:
      cutout: A CutoutProfile instance (already configured)
      grid_x: Number of items in X direction
      grid_y: Number of items in Y direction
      spacing: Minimum gap between pockets (mm)
      style: "square" or "hex" layout

    Returns:
      CadQuery Workplane of all cutouts unioned together, centered at origin.
    """
    if grid_x < 1 or grid_y < 1:
        return None

    unit = cutout.render()
    pitch_x = cutout.pitch_x + spacing
    pitch_y = cutout.pitch_y + spacing

    pts = []
    if style == "hex":
        # Hex packing: offset every other row by half pitch
        for iy in range(grid_y):
            x_offset = (pitch_x / 2) if (iy % 2 == 1) else 0
            # Hex rows may have one fewer item on offset rows
            nx = grid_x if (iy % 2 == 0) else max(grid_x - 1, 1)
            for ix in range(nx):
                x = ix * pitch_x + x_offset
                y = iy * pitch_y * math.sqrt(3) / 2
                pts.append((x, y, 0))
    else:
        for iy in range(grid_y):
            for ix in range(grid_x):
                x = ix * pitch_x
                y = iy * pitch_y
                pts.append((x, y, 0))

    if not pts:
        return None

    # Centre the grid at origin
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    pts = [(p[0] - cx, p[1] - cy, 0) for p in pts]

    from cqkit.cq_helpers import composite_from_pts
    return composite_from_pts(unit, pts)
