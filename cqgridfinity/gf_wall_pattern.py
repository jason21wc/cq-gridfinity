#! /usr/bin/env python3
#
# Wall pattern generation for Gridfinity bins.
# Generates hex grid, square grid, and other hole patterns
# for cutting into bin exterior walls.

import math
import cadquery as cq
from cqgridfinity.constants import *


def _hex_centres(canvas_w, canvas_h, cell_size, spacing):
    """Compute hex-grid hole centres within a canvas.

    Returns list of (x, y) positions centered on the canvas.
    Hex packing: alternating rows offset by half the column spacing.
    """
    sides = 6
    # Circumscribed radius for regular polygon
    ri = cell_size / 2  # inscribed radius
    rc = ri / math.cos(math.pi / sides)  # circumscribed radius

    # Hex spacing
    dy = cell_size + spacing
    dx = math.sqrt((cell_size + spacing) ** 2 - (dy / 2) ** 2)
    if dx < EPS:
        return []

    nx = max(1, int(math.floor((canvas_w - cell_size) / dx)) + 1)
    ny = max(1, int(math.floor((canvas_h - cell_size) / dy)) + 1)

    pts = []
    for iy in range(ny):
        for ix in range(nx):
            x = ix * dx - (nx - 1) * dx / 2
            y = iy * dy - (ny - 1) * dy / 2
            if iy % 2 == 1:
                x += dx / 2
            # Only include if hole fits within canvas
            if abs(x) + ri <= canvas_w / 2 + EPS and abs(y) + ri <= canvas_h / 2 + EPS:
                pts.append((x, y))
    return pts


def _grid_centres(canvas_w, canvas_h, cell_size, spacing):
    """Compute square-grid hole centres within a canvas."""
    dx = cell_size + spacing
    dy = cell_size + spacing
    if dx < EPS or dy < EPS:
        return []

    nx = max(1, int(math.floor((canvas_w + spacing) / dx)))
    ny = max(1, int(math.floor((canvas_h + spacing) / dy)))

    pts = []
    for iy in range(ny):
        for ix in range(nx):
            x = ix * dx - (nx - 1) * dx / 2
            y = iy * dy - (ny - 1) * dy / 2
            pts.append((x, y))
    return pts


def _polygon_sketch(cell_size, sides, corner_rad=0):
    """Create a regular polygon sketch for a single hole."""
    ri = cell_size / 2
    if sides <= 2:
        sides = 6
    rc = ri / math.cos(math.pi / sides)

    s = cq.Sketch()
    if sides == 4:
        s = s.rect(cell_size, cell_size)
    elif sides >= 32:
        s = s.circle(ri)
    else:
        s = s.regularPolygon(rc, sides)

    if corner_rad > 0 and sides < 32 and sides != 4:
        max_rad = ri * math.tan(math.pi / sides) - EPS
        rad = min(corner_rad, max_rad)
        if rad > EPS:
            s = s.vertices().fillet(rad)
    elif corner_rad > 0 and sides == 4:
        max_rad = cell_size / 2 - EPS
        rad = min(corner_rad, max_rad)
        if rad > EPS:
            s = s.vertices().fillet(rad)

    return s


def make_wall_pattern(canvas_w, canvas_h, depth, style="hexgrid",
                      cell_size=GR_PAT_CELL, spacing=GR_PAT_SPACING,
                      sides=GR_PAT_SIDES, corner_rad=GR_PAT_CORNER_RAD):
    """Generate a wall pattern solid for boolean cutting.

    Args:
        canvas_w: Width of the pattern area (mm)
        canvas_h: Height of the pattern area (mm)
        depth: Depth of the cut (wall thickness)
        style: "hexgrid" or "grid"
        cell_size: Hole size in mm
        spacing: Web thickness between holes in mm
        sides: Polygon sides (4=square, 6=hex, 8=octagon, 64=circle)
        corner_rad: Corner rounding on holes

    Returns:
        CadQuery solid centered at origin, extending in +Z by depth.
        Returns None if no holes fit.
    """
    if canvas_w < cell_size or canvas_h < cell_size:
        return None

    if style == "hexgrid":
        pts = _hex_centres(canvas_w, canvas_h, cell_size, spacing)
    elif style == "grid":
        pts = _grid_centres(canvas_w, canvas_h, cell_size, spacing)
    else:
        return None

    if not pts:
        return None

    hole = _polygon_sketch(cell_size, sides, corner_rad)
    r = cq.Workplane("XY").placeSketch(hole).extrude(depth)

    if len(pts) == 1:
        return r.translate((pts[0][0], pts[0][1], 0))

    # Build compound from all hole positions
    from cqkit.cq_helpers import composite_from_pts
    return composite_from_pts(r, [(x, y, 0) for x, y in pts])
