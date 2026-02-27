#! /usr/bin/env python3
#
# Copyright (C) 2024-2026  Jason Collier
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
# Gridfinity Hole Types — shared geometry for baseplates and bins.
#
# Provides standalone functions for creating Gridfinity-compatible hole
# geometries. Both baseplates and bins use these to cut holes at grid
# positions. Future enhanced hole types (crush rib, chamfered, refined)
# will be added here.

import cadquery as cq
from cqkit.cq_helpers import composite_from_pts

from cqgridfinity.constants import (
    EPS,
    GR_BOLT_D,
    GR_BOLT_H,
    GR_HOLE_D,
    GR_HOLE_H,
    GR_HOLE_SLICE,
)


def magnet_hole(diameter: float = GR_HOLE_D, depth: float = GR_HOLE_H) -> cq.Workplane:
    """Create a cylindrical magnet recess solid for boolean cutting.

    Args:
        diameter: Hole diameter (default 6.5mm for standard 6mm magnets).
        depth: Hole depth (default 2.4mm).

    Returns:
        CadQuery Workplane solid at origin, extruding in +Z.
    """
    return cq.Workplane("XY").circle(diameter / 2).extrude(depth + EPS)


def screw_hole(diameter: float = GR_BOLT_D, depth: float = 4.0) -> cq.Workplane:
    """Create a cylindrical screw through-hole solid for boolean cutting.

    Args:
        diameter: Hole diameter (default 3.0mm for M3).
        depth: Hole depth in mm.

    Returns:
        CadQuery Workplane solid at origin, extruding in +Z.
    """
    return cq.Workplane("XY").circle(diameter / 2).extrude(depth + EPS)


def hole_filler(
    hole_diam: float = GR_HOLE_D, slice_height: float = GR_HOLE_SLICE
) -> cq.Workplane:
    """Create a printable bridge filler for unsupported holes.

    Two thin rectangular slabs that span the hole at the magnet recess depth,
    allowing FDM printing without supports.

    Args:
        hole_diam: Diameter of the hole being bridged.
        slice_height: Thickness of the bridge layer.

    Returns:
        CadQuery Workplane compound solid (two slabs at GR_HOLE_H height).
    """
    rc = cq.Workplane("XY").rect(hole_diam / 2, hole_diam).extrude(slice_height)
    xo = hole_diam / 2
    return composite_from_pts(rc, [(-xo, 0, GR_HOLE_H), (xo, 0, GR_HOLE_H)])


def cut_magnet_holes(
    obj: cq.Workplane,
    points: list,
    z_offset: float = 0,
    diameter: float = GR_HOLE_D,
    depth: float = GR_HOLE_H,
) -> cq.Workplane:
    """Cut magnet recesses into an object at the given XY positions.

    Args:
        obj: Target CadQuery object to cut into.
        points: List of (x, y) tuples for hole centre positions.
        z_offset: Z position of the bottom of the magnet recess.
        diameter: Magnet hole diameter.
        depth: Magnet hole depth.

    Returns:
        CadQuery Workplane with holes cut.
    """
    mag = magnet_hole(diameter, depth).translate((0, 0, z_offset))
    holes = composite_from_pts(mag, [(x, y, 0) for x, y in points])
    return obj.cut(holes)


def cut_screw_holes(
    obj: cq.Workplane,
    points: list,
    depth: float = 4.0,
    diameter: float = GR_BOLT_D,
) -> cq.Workplane:
    """Cut screw through-holes into an object at the given XY positions.

    Args:
        obj: Target CadQuery object to cut into.
        points: List of (x, y) tuples for hole centre positions.
        depth: Depth of screw holes from Z=0.
        diameter: Screw hole diameter.

    Returns:
        CadQuery Workplane with holes cut.
    """
    screw = screw_hole(diameter, depth)
    holes = composite_from_pts(screw, [(x, y, 0) for x, y in points])
    return obj.cut(holes)
