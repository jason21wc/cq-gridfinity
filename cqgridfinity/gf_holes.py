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
# positions.
#
# Hole types (from kennetek/gridfinity-rebuilt-openscad):
#   - Standard: plain cylinder (6.5mm dia, 2.4mm deep)
#   - Refined: tighter tolerances (5.86mm dia, 1.9mm deep)
#   - Crush rib: 8 thin ribs protruding into hole for press-fit
#   - Chamfered: 0.8mm chamfer at hole entry for easier magnet insertion
#   - Printable top: thin bridge layer at hole top for supportless FDM printing

import math

import cadquery as cq
from cqkit.cq_helpers import composite_from_pts

from cqgridfinity.constants import (
    EPS,
    GR_BOLT_D,
    GR_BOLT_H,
    GR_CHAMFER_ANGLE,
    GR_CHAMFER_EXTRA_R,
    GR_CRUSH_RIB_COUNT,
    GR_CRUSH_RIB_INNER_D,
    GR_HOLE_D,
    GR_HOLE_H,
    GR_HOLE_SLICE,
    GR_REFINED_HOLE_D,
    GR_REFINED_HOLE_H,
    GR_SCREW_DEPTH,
)


# ---------------------------------------------------------------------------
# Basic hole primitives
# ---------------------------------------------------------------------------


def magnet_hole(diameter: float = GR_HOLE_D, depth: float = GR_HOLE_H) -> cq.Workplane:
    """Create a cylindrical magnet recess solid for boolean cutting.

    Args:
        diameter: Hole diameter (default 6.5mm for standard 6mm magnets).
        depth: Hole depth (default 2.4mm).

    Returns:
        CadQuery Workplane solid at origin, extruding in +Z.
    """
    return cq.Workplane("XY").circle(diameter / 2).extrude(depth + EPS)


def screw_hole(diameter: float = GR_BOLT_D, depth: float = GR_SCREW_DEPTH) -> cq.Workplane:
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


# ---------------------------------------------------------------------------
# Enhanced hole types (1B.1–1B.4, from kennetek gridfinity-rebuilt-holes.scad)
# ---------------------------------------------------------------------------


def refined_magnet_hole(
    diameter: float = GR_REFINED_HOLE_D,
    depth: float = GR_REFINED_HOLE_H,
) -> cq.Workplane:
    """Create a refined magnet hole with tighter press-fit tolerances.

    Refined holes use a smaller diameter (5.86mm vs 6.5mm) and shallower
    depth (1.9mm vs 2.4mm) for a tighter fit without additional features.
    From kennetek refined_hole(), REFINED_HOLE_RADIUS=5.86/2.

    Args:
        diameter: Hole diameter (default 5.86mm).
        depth: Hole depth (default 1.9mm).

    Returns:
        CadQuery Workplane solid at origin, extruding in +Z.
    """
    return cq.Workplane("XY").circle(diameter / 2).extrude(depth + EPS)


def crush_rib_magnet_hole(
    diameter: float = GR_HOLE_D,
    depth: float = GR_HOLE_H,
    rib_count: int = GR_CRUSH_RIB_COUNT,
    inner_diameter: float = GR_CRUSH_RIB_INNER_D,
) -> cq.Workplane:
    """Create a magnet hole with crush ribs for press-fit retention.

    Crush ribs are thin ridges protruding inward from the hole wall. When
    a magnet is pressed in, the ribs deform slightly, creating a friction
    fit that holds the magnet securely.

    From kennetek ribbed_cylinder(): 8 ribs, outer=6.5mm, inner=5.9mm.

    The cutting tool is a cylinder with thin rib-shaped notches removed.
    When subtracted from a baseplate, the notch areas remain as material
    protrusions (the ribs) inside the hole.

    Args:
        diameter: Outer hole diameter (default 6.5mm).
        depth: Hole depth (default 2.4mm).
        rib_count: Number of ribs around circumference (default 8).
        inner_diameter: Diameter at rib tips (default 5.9mm).

    Returns:
        CadQuery Workplane cutting solid with rib cutouts.
    """
    outer_r = diameter / 2
    inner_r = inner_diameter / 2
    rib_radial = outer_r - inner_r  # radial extent of each rib (0.3mm)
    # Circumferential rib width: ~1/3 of the arc between ribs
    rib_arc = 2 * math.pi * outer_r / rib_count
    rib_width = rib_arc * 0.3  # thin ribs, ~30% of arc spacing

    # Main cylinder (the full hole)
    hole = cq.Workplane("XY").circle(outer_r).extrude(depth + EPS)

    # Create rib material solids — these are subtracted from the cutting tool
    # so they remain as material (protrusions) when the hole is cut
    shapes = []
    for i in range(rib_count):
        angle = i * (360.0 / rib_count)
        rib = (
            cq.Workplane("XY")
            .center(inner_r + rib_radial / 2, 0)
            .rect(rib_radial, rib_width)
            .extrude(depth + EPS)
        )
        if angle != 0:
            rib = rib.rotate((0, 0, 0), (0, 0, 1), angle)
        shapes.append(rib.val())

    rib_compound = cq.Compound.makeCompound(shapes)
    ribs = cq.Workplane("XY").newObject([rib_compound])

    return hole.cut(ribs)


def _chamfer_cone(
    hole_radius: float,
    chamfer_extra_r: float = GR_CHAMFER_EXTRA_R,
    chamfer_angle: float = GR_CHAMFER_ANGLE,
) -> cq.Workplane:
    """Create a conical chamfer solid for the entry of a magnet hole.

    The chamfer widens the hole opening to guide magnet insertion.
    At Z=0, the cone has radius (hole_radius + chamfer_extra_r).
    At Z=chamfer_height, the cone narrows to hole_radius.

    Args:
        hole_radius: Base hole radius.
        chamfer_extra_r: Additional radius at cone base (default 0.8mm).
        chamfer_angle: Chamfer angle in degrees (default 45°).

    Returns:
        CadQuery Workplane cone solid at origin, narrowing in +Z.
    """
    chamfer_h = chamfer_extra_r / math.tan(math.radians(chamfer_angle))
    top_r = hole_radius + chamfer_extra_r
    return (
        cq.Workplane("XY")
        .circle(top_r)
        .workplane(offset=chamfer_h)
        .circle(hole_radius)
        .loft()
    )


def _printable_bridge(
    hole_radius: float,
    bridge_height: float = 0.4,
) -> cq.Workplane:
    """Create a thin bridge disc for FDM-printable hole tops.

    This disc is subtracted from the cutting tool so that a thin layer
    of material remains at the top of the hole, allowing the slicer to
    print a bridge layer without supports.

    Args:
        hole_radius: Radius of the hole being bridged.
        bridge_height: Thickness of the bridge layer (default 0.4mm, ~2 layers).

    Returns:
        CadQuery Workplane disc solid at origin.
    """
    return cq.Workplane("XY").circle(hole_radius).extrude(bridge_height)


def enhanced_magnet_hole(
    diameter: float = GR_HOLE_D,
    depth: float = GR_HOLE_H,
    refined: bool = False,
    crush_ribs: bool = False,
    chamfer: bool = False,
    printable_top: bool = False,
) -> cq.Workplane:
    """Create a magnet hole with optional enhanced features.

    Combines any combination of: standard/refined base hole, crush ribs,
    entry chamfer, and printable bridge top. Matches kennetek's
    block_base_hole() with bundle_hole_options().

    Args:
        diameter: Standard hole diameter (used if refined=False).
        depth: Standard hole depth (used if refined=False).
        refined: Use refined hole dimensions (5.86mm dia, 1.9mm deep).
        crush_ribs: Add crush ribs for press-fit retention.
        chamfer: Add entry chamfer for easier magnet insertion.
        printable_top: Add thin bridge layer at hole top for FDM.

    Returns:
        CadQuery Workplane cutting solid at origin, extruding in +Z.
        Total height may exceed 'depth' if chamfer is enabled.
    """
    d = GR_REFINED_HOLE_D if refined else diameter
    h = GR_REFINED_HOLE_H if refined else depth
    r = d / 2

    # Base hole (with or without crush ribs)
    if crush_ribs:
        hole = crush_rib_magnet_hole(d, h)
    else:
        hole = magnet_hole(d, h)

    # Entry chamfer at the top of the hole
    if chamfer:
        cone = _chamfer_cone(r).translate((0, 0, h))
        hole = hole.union(cone)

    # Printable bridge top: remove a thin disc from the cutting tool at the
    # hole top so that material remains as a bridge layer
    if printable_top:
        bridge_h = 0.4  # ~2 print layers at 0.2mm
        bridge = _printable_bridge(r, bridge_h).translate((0, 0, h - bridge_h))
        hole = hole.cut(bridge)

    return hole


# ---------------------------------------------------------------------------
# High-level cut functions (used by baseplates and bins)
# ---------------------------------------------------------------------------


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
    depth: float = GR_SCREW_DEPTH,
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


def cut_enhanced_holes(
    obj: cq.Workplane,
    points: list,
    z_offset: float = 0,
    diameter: float = GR_HOLE_D,
    depth: float = GR_HOLE_H,
    refined: bool = False,
    crush_ribs: bool = False,
    chamfer: bool = False,
    printable_top: bool = False,
) -> cq.Workplane:
    """Cut enhanced magnet holes into an object at the given XY positions.

    Uses enhanced_magnet_hole() to create the cutting tool, then places
    copies at each point position.

    Args:
        obj: Target CadQuery object to cut into.
        points: List of (x, y) tuples for hole centre positions.
        z_offset: Z position of the bottom of the magnet recess.
        diameter: Standard hole diameter (used if refined=False).
        depth: Standard hole depth (used if refined=False).
        refined: Use refined hole dimensions.
        crush_ribs: Add crush ribs.
        chamfer: Add entry chamfer.
        printable_top: Add printable bridge layer.

    Returns:
        CadQuery Workplane with enhanced holes cut.
    """
    hole = enhanced_magnet_hole(
        diameter=diameter,
        depth=depth,
        refined=refined,
        crush_ribs=crush_ribs,
        chamfer=chamfer,
        printable_top=printable_top,
    ).translate((0, 0, z_offset))
    holes = composite_from_pts(hole, [(x, y, 0) for x, y in points])
    return obj.cut(holes)
