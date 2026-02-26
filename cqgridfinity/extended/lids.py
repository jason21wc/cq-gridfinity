#! /usr/bin/env python3
#
# Gridfinity Lids — flat, stackable, and click-lock covers for bins
#
# Copyright (C) 2026  Jason Collier
# MIT License (see LICENSE)

import cadquery as cq
from cqkit.cq_helpers import rounded_rect_sketch, composite_from_pts
from cqkit import rotate_x

from cqgridfinity import *
from cqgridfinity.gf_obj import GridfinityObject

# Lid-specific constants
GR_LID_FLAT_TH = 1.2       # flat lid plate thickness (mm)
GR_LID_FINGER_W = 16.0     # finger grip slot width (mm)
GR_LID_FINGER_D = 2.5      # finger grip slot depth into lid underside (mm)
GR_LID_LABEL_DEPTH = 0.4   # label recess depth (mm)


class GridfinityLid(GridfinityObject):
    """Gridfinity lid that sits on top of bins via the stacking lip receptacle.

    Lid types:
      - "flat": Simple cover plate with inverse lip profile on underside
      - "stackable": Flat lid with baseplate receptacle array on top,
                     allowing bins to stack on the lid

    Parameters:
      length_u, width_u: Grid dimensions (same as the bin it covers)
      lid_style: "flat" or "stackable"
      lid_thickness: Plate thickness in mm (default 1.2)
      finger_slot: Add a grip cutout on one edge for easy removal
      finger_slot_width: Width of the finger grip (mm)
      finger_slot_depth: Depth of the finger grip recess (mm)
      label: Add a recessed label area on the top surface
      label_width: Label recess width (mm)
      label_height: Label recess height (mm)
      label_depth: Label recess depth (mm)
    """

    def __init__(self, length_u, width_u, **kwargs):
        super().__init__()
        self.length_u = length_u
        self.width_u = width_u
        self.lid_style = "flat"
        self.lid_thickness = GR_LID_FLAT_TH
        self.finger_slot = True
        self.finger_slot_width = GR_LID_FINGER_W
        self.finger_slot_depth = GR_LID_FINGER_D
        self.label = False
        self.label_width = 30.0
        self.label_height = 12.0
        self.label_depth = GR_LID_LABEL_DEPTH
        for k, v in kwargs.items():
            if k in self.__dict__:
                self.__dict__[k] = v
        if self.lid_style not in ("flat", "stackable"):
            raise ValueError(
                "lid_style must be 'flat' or 'stackable', got '%s'" % self.lid_style
            )

    def __str__(self):
        s = []
        s.append(
            "Gridfinity Lid %dU x %dU (%.2f x %.2f mm) [%s]"
            % (
                self.length_u, self.width_u,
                self.outer_l, self.outer_w,
                self.lid_style,
            )
        )
        s.append("  Thickness: %.2f mm" % self.lid_thickness)
        if self.finger_slot:
            s.append("  Finger slot: %.1f mm wide" % self.finger_slot_width)
        if self.label:
            s.append(
                "  Label recess: %.1f x %.1f mm, %.2f mm deep"
                % (self.label_width, self.label_height, self.label_depth)
            )
        s.append("  Auto filename: %s" % self.filename())
        return "\n".join(s)

    @property
    def lip_h(self):
        """Total height of the lip receptacle portion on the underside."""
        return GR_LIP_H

    @property
    def total_height(self):
        """Total height of the lid."""
        h = self.lid_thickness + self.lip_h
        if self.lid_style == "stackable":
            h += GR_BASE_HEIGHT
        return h

    def filename(self, prefix=None, path=None):
        import os
        if prefix is not None:
            fn_prefix = prefix
        else:
            fn_prefix = "gf_lid_"
        fn = ""
        if path is not None:
            fn = path + os.sep
        fn += fn_prefix
        fn += "%dx%d" % (self.length_u, self.width_u)
        fn += "_%s" % self.lid_style
        if self.finger_slot:
            fn += "_finger"
        if self.label:
            fn += "_label"
        return fn

    def render(self):
        """Render the lid as a CadQuery Workplane object.

        Construction (bottom to top, Z=0 at lid bottom):
        1. Lip receptacle: inverse of GR_LIP_PROFILE extruded inward from
           the outer perimeter. This creates the cavity that mates with
           the bin's stacking lip.
        2. Flat plate: solid slab on top of the lip receptacle.
        3. (Stackable only) Baseplate receptacle array on the top surface.
        4. Finger slot: rounded cutout on one edge for grip.
        5. Label recess: shallow pocket on top surface.
        """
        # The lid outer dims match the bin outer dims exactly
        ol, ow = self.outer_l, self.outer_w
        orad = self.outer_rad

        # --- 1. Build the solid outer block ---
        # Height = lip receptacle + plate (+ baseplate for stackable)
        block_h = self.lid_thickness + self.lip_h
        r = (
            cq.Workplane("XY")
            .placeSketch(rounded_rect_sketch(ol, ow, orad))
            .extrude(block_h)
        )

        # --- 2. Cut lip receptacle from the underside ---
        # The receptacle is the inverse of the stacking lip:
        # a solid that matches the lip's outer shape, cut from Z=0 upward.
        # Lip profile sweeps inward from the outer wall.
        #
        # From GR_LIP_PROFILE (bottom to top of lip):
        #   (GR_UNDER_H * SQRT2, 45)  -> underside chamfer, inward 1.6mm over 1.6mm height
        #   GR_TOPSIDE_H              -> vertical, 1.2mm
        #   (0.7 * SQRT2, -45)        -> outward 0.7mm over 0.7mm
        #   1.8                        -> vertical, 1.8mm
        #   (1.3 * SQRT2, -45)        -> outward 1.3mm over 1.3mm
        #
        # The receptacle matches this: we extrude the lip profile shape
        # and subtract it from the lid block.
        r = self._cut_lip_receptacle(r, ol, ow, orad)

        # --- 3. Stackable: add baseplate receptacle on top ---
        if self.lid_style == "stackable":
            r = self._add_baseplate_top(r, block_h)

        # --- 4. Finger slot ---
        if self.finger_slot:
            r = self._cut_finger_slot(r)

        # --- 5. Label recess ---
        if self.label:
            top_z = block_h
            if self.lid_style == "stackable":
                top_z += GR_BASE_HEIGHT
            r = self._cut_label_recess(r, top_z)

        return r

    def _cut_lip_receptacle(self, obj, ol, ow, orad):
        """Cut the lip mating receptacle from the underside of the lid.

        The receptacle is the space the bin's stacking lip occupies.
        We build a solid matching the lip outer envelope and subtract
        the lip inner shape, giving us the negative space.

        Approach: extrude the lip profile outward from an inner contour
        to create the lip solid, then subtract it from the lid block.
        """
        # The lip sits at the top of the bin. Its base starts at the
        # bin interior wall and expands outward via the profile.
        # For the lid, this means the receptacle starts at the lid's
        # inner surface and expands to the outer surface.
        #
        # Inner contour of the lip receptacle = bin outer wall - lip overhang
        # The lip profile's maximum outward extension is:
        #   GR_UNDER_H (1.6mm chamfer) then back in by 0.7+1.3=2.0mm
        #   Net inward from outer wall = GR_UNDER_H = 1.6mm at the narrowest
        # But actually, the bin's lip starts at (outer_wall - wall_th - under_h)
        # and the outer surface of the lip IS the bin's outer surface.
        #
        # Simpler approach: the receptacle is just a scaled-down version
        # of the outer profile that, when subtracted, leaves the lip shape.
        #
        # Simplest correct approach: use the same extrude_profile method
        # that creates the bin interior, but inverted for the lid.
        #
        # The lip shape from inside: the bin's render_interior creates it
        # by extruding GR_LIP_PROFILE from the inner wall.
        # For the lid receptacle, we need the OUTSIDE of that shape.
        #
        # We'll build it as: full block at Z=0..lip_h minus the lid walls.
        # The lid wall thickness at the lip area follows the lip profile.

        lip_h = self.lip_h

        # Build the lip receptacle cavity using the profile.
        # Start with the inner wall dimensions (same as bin interior)
        # Wall thickness for the lid at the lip = GR_WALL (standard 1.0mm)
        wall_th = GR_WALL
        inner_l = ol - 2 * wall_th
        inner_w = ow - 2 * wall_th
        inner_rad = orad - wall_th

        # Extrude the lip profile from the inner contour upward.
        # This creates the interior volume that the bin lip fills.
        profile = list(GR_LIP_PROFILE)
        lip_solid = self.extrude_profile(
            rounded_rect_sketch(inner_l, inner_w, inner_rad),
            profile,
        )
        # The profile extrudes upward from Z=0. Position at lid Z=0.
        obj = obj.cut(lip_solid)

        return obj

    def _add_baseplate_top(self, obj, base_z):
        """Add baseplate receptacle array on the top surface of the lid.

        This allows bins to stack on top of the lid, making it a
        functional baseplate surface.
        """
        # Use the same baseplate receptacle as GridfinityBaseplate
        profile = GR_BASE_PROFILE
        rc = self.extrude_profile(
            rounded_rect_sketch(GRU_CUT, GRU_CUT, GR_RAD), profile
        )
        rc = rotate_x(rc, 180).translate(
            (GRU2, GRU2, base_z + GR_BASE_HEIGHT)
        )

        # Create receptacle for each grid cell
        from cqgridfinity.gf_baseplate import GridfinityBaseplate
        bp_temp = GridfinityBaseplate.__new__(GridfinityBaseplate)
        bp_temp.length_u = self.length_u
        bp_temp.width_u = self.width_u

        rc = composite_from_pts(rc, self.grid_centres)
        # Recentre to lid coordinate system
        from cqkit.cq_helpers import recentre
        rc = recentre(rc, "XY")

        # Build top slab (rounded_rect_sketch already has rounded corners)
        top_slab = (
            cq.Workplane("XY")
            .placeSketch(rounded_rect_sketch(
                self.length_u * GRU, self.width_u * GRU, GR_RAD
            ))
            .extrude(GR_BASE_HEIGHT)
            .translate((0, 0, base_z))
        )

        # Cut receptacles from slab
        top_slab = top_slab.faces(">Z").cut(rc)

        # Union with lid body
        obj = obj.union(top_slab)
        return obj

    def _cut_finger_slot(self, obj):
        """Cut a finger grip slot on the front edge of the lid."""
        fw = self.finger_slot_width
        fd = self.finger_slot_depth
        # Semi-circular slot on the front edge (Y = -ow/2)
        # The slot is a half-cylinder cut into the underside front edge
        slot_rad = fd
        slot = (
            cq.Workplane("XZ")
            .center(0, slot_rad / 2)
            .slot2D(fw, slot_rad * 2, angle=0)
            .extrude(-self.outer_w / 2)
            .translate((0, -EPS, 0))
        )
        obj = obj.cut(slot)
        return obj

    def _cut_label_recess(self, obj, top_z):
        """Cut a shallow label recess on the top surface."""
        lw = self.label_width
        lh = self.label_height
        ld = self.label_depth
        recess = (
            cq.Workplane("XY")
            .rect(lw, lh)
            .extrude(ld)
            .translate((0, 0, top_z - ld))
        )
        obj = obj.cut(recess)
        return obj
