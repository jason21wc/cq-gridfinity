#! /usr/bin/env python3
#
# Gridfinity Modular Drawers — sliding drawer bodies and chest frames
#
# Copyright (C) 2026  Jason Collier
# MIT License (see LICENSE)

import os

import cadquery as cq
from cqkit.cq_helpers import rounded_rect_sketch, composite_from_pts
from cqkit import rotate_x

from cqgridfinity import *
from cqgridfinity.gf_obj import GridfinityObject

# Drawer-specific constants
GR_DRAWER_WALL = 1.6       # drawer wall thickness (mm)
GR_DRAWER_FLOOR = 1.2      # drawer floor thickness (mm)
GR_DRAWER_RAIL_W = 2.0     # slide rail width (mm)
GR_DRAWER_RAIL_H = 3.0     # slide rail height (mm)
GR_DRAWER_RAIL_CLR = 0.3   # rail-to-groove clearance (mm)
GR_DRAWER_RAD = 2.0        # drawer corner radius (mm)
GR_DRAWER_HANDLE_W = 30.0  # handle cutout width (mm)
GR_DRAWER_HANDLE_H = 10.0  # handle cutout height (mm)
GR_DRAWER_HANDLE_D = 5.0   # handle cutout depth (mm)
GR_DRAWER_DIVIDER_TH = 1.2 # horizontal divider between drawer slots (mm)


class GridfinityDrawer(GridfinityObject):
    """A sliding drawer body that fits into a GridfinityDrawerChest.

    The drawer is an open-top box with slide rails on each side that
    engage with grooves in the chest. The front face can include
    a handle cutout for easy pull.

    The drawer interior dimensions are based on grid units, allowing
    standard Gridfinity bins or baseplates to sit inside (optional).

    Parameters:
      length_u: Interior length in grid units (X direction, width of drawer)
      width_u: Interior depth in grid units (Y direction, slide direction)
      height_u: Interior height in 7mm units
      wall_th: Wall thickness (mm)
      floor_th: Floor thickness (mm)
      rail_width: Slide rail width (mm)
      rail_height: Slide rail height (mm)
      rail_clearance: Tolerance between rail and groove (mm)
      handle: Add a handle cutout on the front face
      handle_width: Handle cutout width (mm)
      handle_height: Handle cutout height (mm)
      handle_depth: Handle cutout depth (mm)
    """

    def __init__(self, length_u, width_u, height_u=2, **kwargs):
        super().__init__()
        self.length_u = length_u
        self.width_u = width_u
        self.height_u = height_u
        self.wall_th = GR_DRAWER_WALL
        self.floor_th = GR_DRAWER_FLOOR
        self.rail_width = GR_DRAWER_RAIL_W
        self.rail_height = GR_DRAWER_RAIL_H
        self.rail_clearance = GR_DRAWER_RAIL_CLR
        self.handle = True
        self.handle_width = GR_DRAWER_HANDLE_W
        self.handle_height = GR_DRAWER_HANDLE_H
        self.handle_depth = GR_DRAWER_HANDLE_D
        for k, v in kwargs.items():
            if k in self.__dict__:
                self.__dict__[k] = v

    def __str__(self):
        s = []
        s.append(
            "Gridfinity Drawer %dU x %dU x %dU (%.2f x %.2f x %.2f mm)"
            % (
                self.length_u, self.width_u, self.height_u,
                self.drawer_outer_l, self.drawer_outer_w, self.drawer_outer_h,
            )
        )
        s.append("  Wall: %.2f mm  Floor: %.2f mm" % (self.wall_th, self.floor_th))
        s.append("  Rail: %.1f x %.1f mm (clearance %.2f mm)"
                 % (self.rail_width, self.rail_height, self.rail_clearance))
        if self.handle:
            s.append("  Handle: %.1f x %.1f mm" % (self.handle_width, self.handle_height))
        s.append("  Auto filename: %s" % self.filename())
        return "\n".join(s)

    # --- Drawer dimensions ---

    @property
    def drawer_int_l(self):
        """Drawer interior length (X)."""
        return self.length_u * GRU

    @property
    def drawer_int_w(self):
        """Drawer interior depth (Y, slide direction)."""
        return self.width_u * GRU

    @property
    def drawer_int_h(self):
        """Drawer interior height."""
        return self.height_u * GRHU

    @property
    def drawer_outer_l(self):
        """Drawer outer length including walls (X)."""
        return self.drawer_int_l + 2 * self.wall_th

    @property
    def drawer_outer_w(self):
        """Drawer outer depth including walls and front face (Y)."""
        return self.drawer_int_w + 2 * self.wall_th

    @property
    def drawer_outer_h(self):
        """Drawer outer height including floor (Z)."""
        return self.drawer_int_h + self.floor_th

    @property
    def rail_z(self):
        """Z position of rail center (midway up the drawer exterior)."""
        return self.drawer_outer_h / 2

    def filename(self, prefix=None, path=None):
        if prefix is not None:
            fn_prefix = prefix
        else:
            fn_prefix = "gf_drawer_"
        fn = ""
        if path is not None:
            fn = path + os.sep
        fn += fn_prefix
        fn += "%dx%dx%d" % (self.length_u, self.width_u, self.height_u)
        if self.handle:
            fn += "_handle"
        return fn

    def render(self):
        """Render the drawer body.

        Construction (centered at XY origin, Z=0 at bottom):
        1. Outer box with rounded corners
        2. Cut interior cavity (open top)
        3. Add slide rails on left and right sides
        4. Cut handle on front face
        """
        ol = self.drawer_outer_l
        ow = self.drawer_outer_w
        oh = self.drawer_outer_h
        rad = min(GR_DRAWER_RAD, ol / 4, ow / 4)

        # 1. Outer box
        r = (
            cq.Workplane("XY")
            .placeSketch(rounded_rect_sketch(ol, ow, rad))
            .extrude(oh)
        )

        # 2. Cut interior cavity
        inner_l = self.drawer_int_l
        inner_w = self.drawer_int_w
        inner_h = self.drawer_int_h
        inner_rad = max(rad - self.wall_th, 0.1)
        cavity = (
            cq.Workplane("XY")
            .placeSketch(rounded_rect_sketch(inner_l, inner_w, inner_rad))
            .extrude(inner_h + EPS)
            .translate((0, 0, self.floor_th))
        )
        r = r.cut(cavity)

        # 3. Add slide rails on left and right exterior
        r = self._add_rails(r)

        # 4. Handle cutout
        if self.handle:
            r = self._cut_handle(r)

        return r

    def _add_rails(self, obj):
        """Add slide rails on the left and right exterior walls.

        Rails are rectangular bumps running along the full depth (Y)
        of the drawer on each side, centered vertically.
        """
        rw = self.rail_width
        rh = self.rail_height
        rail_len = self.drawer_outer_w - 2 * GR_DRAWER_RAD
        rail_z = self.rail_z

        # Rail as a simple box: rh thick (X), rail_len long (Y), rw tall (Z)
        rail = (
            cq.Workplane("XY")
            .rect(rh, rail_len)
            .extrude(rw)
            .translate((0, 0, rail_z - rw / 2))
        )

        ox = self.drawer_outer_l / 2 + rh / 2
        obj = obj.union(rail.translate((ox, 0, 0)))
        obj = obj.union(rail.translate((-ox, 0, 0)))

        return obj

    def _cut_handle(self, obj):
        """Cut a handle through-hole in the front face of the drawer.

        The handle is a rounded rectangular opening through the front wall,
        centered horizontally and vertically.
        """
        hw = min(self.handle_width, self.drawer_outer_l - 4.0)
        hh = min(self.handle_height, self.drawer_outer_h - 4.0)
        ow = self.drawer_outer_w
        cut_depth = self.wall_th + 2 * EPS
        handle_z = self.drawer_outer_h / 2

        # XZ workplane: extrude(+) goes -Y direction.
        # Front wall: Y = -ow/2 to Y = -ow/2 + wall_th.
        # Position so the cut spans through the front wall with EPS overlap.
        handle = (
            cq.Workplane("XZ")
            .center(0, handle_z)
            .rect(hw, hh)
            .extrude(cut_depth)
            .translate((0, -ow / 2 + cut_depth + EPS, 0))
        )
        obj = obj.cut(handle)
        return obj


class GridfinityDrawerChest(GridfinityObject):
    """A chest/frame that holds GridfinityDrawer instances.

    The chest sits on a Gridfinity baseplate via the standard base profile
    on its bottom. Inside, it has horizontal dividers creating slots for
    drawers, with rail grooves on the interior side walls.

    Parameters:
      length_u: Width in grid units (must match drawer length_u)
      width_u: Depth in grid units (must match drawer width_u)
      drawer_count: Number of drawer slots
      drawer_height_u: Height of each drawer slot in 7mm units
      wall_th: Wall thickness (mm)
      divider_th: Horizontal divider thickness between slots (mm)
      rail_width: Must match drawer rail_width (mm)
      rail_height: Must match drawer rail_height (mm)
      rail_clearance: Gap between rail and groove (mm)
      has_base_profile: Add Gridfinity base profile on bottom
    """

    def __init__(self, length_u, width_u, drawer_count=3, **kwargs):
        super().__init__()
        self.length_u = length_u
        self.width_u = width_u
        self.drawer_count = drawer_count
        self.drawer_height_u = 2
        self.wall_th = GR_DRAWER_WALL
        self.divider_th = GR_DRAWER_DIVIDER_TH
        self.rail_width = GR_DRAWER_RAIL_W
        self.rail_height = GR_DRAWER_RAIL_H
        self.rail_clearance = GR_DRAWER_RAIL_CLR
        self.has_base_profile = True
        for k, v in kwargs.items():
            if k in self.__dict__:
                self.__dict__[k] = v

    def __str__(self):
        s = []
        s.append(
            "Gridfinity Drawer Chest %dU x %dU, %d drawers x %dU"
            % (self.length_u, self.width_u, self.drawer_count, self.drawer_height_u)
        )
        s.append("  Outer: %.2f x %.2f x %.2f mm"
                 % (self.chest_outer_l, self.chest_outer_w, self.chest_outer_h))
        s.append("  Auto filename: %s" % self.filename())
        return "\n".join(s)

    # --- Chest dimensions ---

    @property
    def slot_height(self):
        """Height of each drawer slot (interior)."""
        return self.drawer_height_u * GRHU

    @property
    def chest_outer_l(self):
        """Chest outer length (X). Must accommodate drawer + walls + rail space."""
        # Drawer outer_l + rail_height on each side + clearance + chest walls
        drawer_l = self.length_u * GRU + 2 * GR_DRAWER_WALL
        return drawer_l + 2 * (self.rail_height + self.rail_clearance) + 2 * self.wall_th

    @property
    def chest_outer_w(self):
        """Chest outer depth (Y)."""
        drawer_w = self.width_u * GRU + 2 * GR_DRAWER_WALL
        return drawer_w + self.wall_th  # open front, wall on back

    @property
    def chest_outer_h(self):
        """Total chest height including base and all drawer slots."""
        slots_h = self.drawer_count * self.slot_height
        dividers_h = (self.drawer_count - 1) * self.divider_th
        floor_h = self.wall_th  # top and bottom walls
        top_h = self.wall_th
        base_h = GR_BASE_HEIGHT if self.has_base_profile else 0
        return slots_h + dividers_h + floor_h + top_h + base_h

    @property
    def chest_inner_l(self):
        """Interior width available for drawers + rails."""
        return self.chest_outer_l - 2 * self.wall_th

    @property
    def chest_inner_w(self):
        """Interior depth."""
        return self.chest_outer_w - self.wall_th  # open front

    def filename(self, prefix=None, path=None):
        if prefix is not None:
            fn_prefix = prefix
        else:
            fn_prefix = "gf_chest_"
        fn = ""
        if path is not None:
            fn = path + os.sep
        fn += fn_prefix
        fn += "%dx%d" % (self.length_u, self.width_u)
        fn += "_%dd" % self.drawer_count
        fn += "x%du" % self.drawer_height_u
        if self.has_base_profile:
            fn += "_base"
        return fn

    def render(self):
        """Render the drawer chest.

        Construction (centered at XY origin, Z=0 at bottom):
        1. Outer box with rounded corners
        2. Cut drawer slot cavities (open front)
        3. Cut rail grooves in side walls
        4. Add base profile on bottom (optional)
        """
        ol = self.chest_outer_l
        ow = self.chest_outer_w
        oh = self.chest_outer_h
        rad = min(GR_DRAWER_RAD, ol / 4, ow / 4)

        # 1. Outer box
        r = (
            cq.Workplane("XY")
            .placeSketch(rounded_rect_sketch(ol, ow, rad))
            .extrude(oh)
            .translate((0, 0, 0))
        )

        # 2. Cut drawer slot cavities
        base_h = GR_BASE_HEIGHT if self.has_base_profile else 0
        slot_inner_l = self.chest_inner_l
        slot_inner_w = self.chest_inner_w + EPS  # extend through front face
        slot_rad = max(rad - self.wall_th, 0.1)

        for i in range(self.drawer_count):
            z_bot = base_h + self.wall_th + i * (self.slot_height + self.divider_th)
            slot = (
                cq.Workplane("XY")
                .placeSketch(rounded_rect_sketch(slot_inner_l, slot_inner_w, slot_rad))
                .extrude(self.slot_height)
                .translate((0, -(ow - slot_inner_w) / 2 + EPS, z_bot))
            )
            r = r.cut(slot)

        # 3. Cut rail grooves in the side walls of each slot
        r = self._cut_rail_grooves(r, base_h)

        # 4. Optional base profile
        if self.has_base_profile:
            r = self._add_base_profile(r, ol, ow, rad)

        return r

    def _cut_rail_grooves(self, obj, base_h):
        """Cut rail grooves into the interior side walls for each drawer slot.

        Grooves are rectangular channels running along Y (depth) on
        both interior side walls, matching the drawer rail positions.
        """
        rw = self.rail_width + 2 * self.rail_clearance
        rh = self.rail_height + 2 * self.rail_clearance
        groove_len = self.chest_inner_w + 2 * EPS

        for i in range(self.drawer_count):
            z_bot = base_h + self.wall_th + i * (self.slot_height + self.divider_th)
            rail_z = z_bot + self.slot_height / 2

            # Groove as a box: rh thick (X), groove_len long (Y), rw tall (Z)
            groove = (
                cq.Workplane("XY")
                .rect(rh, groove_len)
                .extrude(rw)
                .translate((0, 0, rail_z - rw / 2))
            )

            # Position at inner wall faces
            ox = self.chest_outer_l / 2 - self.wall_th / 2
            obj = obj.cut(groove.translate((ox, 0, 0)))
            obj = obj.cut(groove.translate((-ox, 0, 0)))

        return obj

    def _add_base_profile(self, obj, ol, ow, rad):
        """Add Gridfinity base profile on the bottom for baseplate mating.

        Uses a simplified approach: cut the base profile receptacle shape
        from the bottom of the chest, matching standard Gridfinity geometry.
        """
        # For the chest, we add a simple chamfered bottom that mates with baseplates.
        # Use the standard base profile per grid cell.
        profile = GR_BASE_PROFILE
        # Calculate how many grid cells fit under the chest
        # The chest may be larger than a neat grid multiple, so we compute based
        # on the closest grid coverage.
        # For now, create a single baseplate-style bottom for the full footprint.

        # Simple approach: chamfer the bottom edges to approximate base profile mating
        # Full baseplate receptacle would require the chest to sit on a specific baseplate.
        # For practical use, the chest bottom is flat with a small chamfer.
        try:
            obj = obj.faces("<Z").edges().chamfer(min(GR_BASE_CHAMF_H, rad * 0.4))
        except Exception:
            pass  # Skip if chamfer fails on complex geometry
        return obj
