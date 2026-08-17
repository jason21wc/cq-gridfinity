#! /usr/bin/env python3
#
# Copyright (C) 2026  Jason Collier
#
# Independent CadQuery implementation of the Cullenect swappable label.
# Original design: Cullen J Webb, https://github.com/CullenJWebb/Cullenect-Labels
# Copyright (c) 2024 Cullen J Webb, MIT licensed.
#
# This module is MIT licensed, matching its upstream source.
#
# Cullenect click-in labels (1D.3, 1D.4)

"""Cullenect swappable labels.

The point of the design: relabel a bin by reprinting a 2g tile instead of a
6-hour bin. The label clicks into a socket moulded into the bin wall, held by
a groove around its own perimeter that two ribs in the socket snap into.

Two halves, and they must agree:

* `CullenectLabel`         -- the tile you print and swap
* `CullenectLabel.socket_negative()` -- the volume you SUBTRACT from a bin to
  leave the socket that holds it

Unlike most of this project's upstream references, Cullenect ships readable
MIT source rather than dimensions alone, so this is a translation rather than
a reconstruction.
"""

import cadquery as cq
from cqkit.cq_helpers import rounded_rect_sketch

from cqgridfinity.constants import GRU
from cqgridfinity.gf_fonts import font_path
from cqgridfinity.gf_obj import GridfinityObject

__all__ = ["CullenectLabel"]

# -- Cullenect.scad, [Hidden] block --------------------------------------
CL_GRID_INSET = 6.0     # labelX = (label_width * 42) - 6
CL_HEIGHT = 11.0        # labelY, fixed regardless of width
CL_THICKNESS = 1.2      # labelZ
CL_LATCH_XY = 0.2       # latchX -- how far the groove is inset from the edge
CL_LATCH_Z = 0.6        # latchZ -- height of the groove
CL_BASE_Z = 0.2         # material below the groove
CL_CORNER_R = 0.5       # RoundedCube radius used throughout the label
CL_LAYER = 0.2          # text/icon relief height

# -- socket ---------------------------------------------------------------
CL_SOCKET_OFFSET = 0.3  # socket is this much larger than the label, in XY
CL_RIB_Z = 0.4          # ribZ -- height of the snap ribs
CL_SOCKET_R = 0.5


class CullenectLabel(GridfinityObject):
    """A Cullenect click-in label tile.

    width_u is in Gridfinity units: the tile spans `width_u * 42 - 6` mm, so a
    1U label is 36mm wide. Height and thickness are fixed by the standard at
    11.0 and 1.2mm -- a label that varied them would not swap.

    Everything is centred on the origin in XY, unlike upstream's lower-left
    convention, so the tile drops straight into a centred socket.

    NOTE: this builds the **V2** label. Upstream also carries a segmented V1
    base, and makes it the DEFAULT for 1U tiles (`backward_compatible = true`),
    so most Cullenect labels in the wild are V1-shaped.

    Our tiles are verified against our own sockets. Upstream's socket module
    is common to both revisions, so a V2 tile very likely fits a socket
    printed from upstream too -- but that is **not verified here**, and anyone
    with existing Cullenect bins should test one tile before printing a set.
    """

    def __init__(self, width_u=1, **kwargs):
        super().__init__()
        self.width_u = width_u
        self.label_length = 0.0  # >0 overrides the grid-derived width, in mm
        self.text = ""
        self.font_path = None  # None uses the bundled Open Sans
        self.font_size = 5.0
        self.text_depth = CL_LAYER
        self.deboss = False  # True cuts the text in rather than raising it
        for k, v in kwargs.items():
            if k in self.__dict__:
                self.__dict__[k] = v
            else:
                raise ValueError(
                    "%s: unknown keyword argument %r" % (self.__class__.__name__, k)
                )
        self._validate()

    def _validate(self):
        if self.label_length <= 0 and self.width_u < 1:
            raise ValueError("width_u must be >= 1, got %r" % (self.width_u,))
        # No validation needed: text falls back to the BUNDLED font, never to
        # a system lookup. See gf_fonts.

    # -- dimensions -------------------------------------------------------

    @property
    def length(self):
        """Cullenect `labelX = (label_width * gridfinityX) - 6`."""
        if self.label_length > 0:
            return self.label_length
        return self.width_u * GRU - CL_GRID_INSET

    @property
    def width(self):
        """`labelY` -- fixed by the standard."""
        return CL_HEIGHT

    @property
    def thickness(self):
        """`labelZ` -- fixed by the standard."""
        return CL_THICKNESS

    @property
    def socket_length(self):
        """`socketX = labelX + socket_offset`."""
        return self.length + CL_SOCKET_OFFSET

    @property
    def socket_width(self):
        """`socketY = labelY + socket_offset`."""
        return self.width + CL_SOCKET_OFFSET

    # -- geometry ---------------------------------------------------------

    def _plate(self, length, width, height, z0=0.0, radius=CL_CORNER_R):
        return (
            cq.Workplane("XY")
            .placeSketch(rounded_rect_sketch(length, width, radius))
            .extrude(height)
            .translate((0, 0, z0))
        )

    def render(self):
        """The label tile.

        Three stacked plates, exactly as upstream stacks them: a full-width
        base, a plate inset by `latchX` that runs from the bottom up past the
        groove, and a full-width cap. The union leaves a groove around the
        perimeter between z=0.2 and z=0.8 -- which is the whole mechanism.
        """
        base = self._plate(self.length, self.width, CL_BASE_Z)
        middle = self._plate(
            self.length - 2 * CL_LATCH_XY,
            self.width - 2 * CL_LATCH_XY,
            self.thickness - CL_BASE_Z,
        )
        cap_z = CL_BASE_Z + CL_LATCH_Z
        cap = self._plate(
            self.length, self.width, self.thickness - cap_z, z0=cap_z
        )
        r = base.union(middle).union(cap)
        r = self._apply_text(r)
        self._cq_obj = r
        self._obj_label = "label"
        return r

    def _apply_text(self, obj):
        """Raise or sink the label text on the top face.

        An unset `font_path` uses the bundled Open Sans rather than whatever
        the machine happens to have installed -- CadQuery would accept a bad
        path and silently substitute a system font.
        """
        if not self.text:
            return obj
        fp = self.font_path or font_path()
        solid = (
            cq.Workplane("XY")
            .workplane(offset=self.thickness)
            .text(
                self.text,
                self.font_size,
                self.text_depth,
                fontPath=fp,
                combine=False,
                halign="center",
                valign="center",
            )
        )
        if self.deboss:
            return obj.cut(solid.translate((0, 0, -self.text_depth)))
        return obj.union(solid)

    def socket_negative(self):
        """The volume to SUBTRACT from a bin wall to leave a socket.

        Cullenect `cullenect_socket_negative()`: the socket cavity, less the
        two ribs that snap into the label's groove. Subtracting this leaves
        the ribs standing as material -- they are what hold the tile in.

        Upstream derives it as `cavity - socket`, where the socket's outer
        shell is disjoint from the cavity by construction; the surviving
        terms are the cavity and the ribs, which is what is built here.
        """
        cavity = self._plate(
            self.socket_length, self.socket_width, self.thickness,
            radius=CL_SOCKET_R,
        )
        ribs = None
        for sign in (-1, 1):
            rib = (
                cq.Workplane("XY")
                .box(self.socket_length, CL_LATCH_XY, CL_RIB_Z, centered=(True, True, False))
                .translate(
                    (0, sign * (self.socket_width - CL_LATCH_XY) / 2, CL_BASE_Z)
                )
            )
            ribs = rib if ribs is None else ribs.union(rib)
        r = cavity.cut(ribs)
        self._cq_obj = r
        self._obj_label = "socket_negative"
        return r

    # -- naming -----------------------------------------------------------

    @property
    def _filename_prefix(self) -> str:
        return "cullenect_label_"

    def _filename_suffix(self) -> str:
        fn = ""
        if self.text:
            fn += "_txt"
        if self.deboss:
            fn += "_deboss"
        return fn

    def filename(self, prefix=None, path=None):
        """A label is sized in label units, not a Gridfinity LxWxH footprint,
        so the base class's grid stem does not describe it."""
        stem = (
            "%gu" % self.width_u if self.label_length <= 0 else "%gmm" % self.length
        )
        name = "%s%s%s" % (self._filename_prefix, stem, self._filename_suffix())
        if path is not None:
            import os

            return os.path.join(path, name)
        return name
