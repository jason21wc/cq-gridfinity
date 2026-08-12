#! /usr/bin/env python3
#
# Copyright (C) 2026  Jason Collier
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Divider objects for Gridfinity bins

"""Divider objects.

Bins previously expressed compartments as two integers, `length_div` and
`width_div`, which could only produce evenly-spaced full-height walls. Four
wanted features are attributes of a single divider rather than separate
subsystems -- unequal spacing, cut-down notches, per-divider height, and angled
tops -- so the underlying representation is a list of `Divider` objects.

ostat's own separator config proves the shape of the data: it carries
`position, bend_separation, bend_angle, cut_depth, cut_width, wall_thickness`
per separator. They encode that list as a pipe-delimited *string* because the
OpenSCAD Customizer cannot expose a list of objects. Python can, so we do not
reproduce that limitation.

`length_div` / `width_div` still work and are unchanged -- they are sugar that
emits evenly-spaced dividers.
"""

from dataclasses import dataclass
from typing import Optional

from cqgridfinity.constants import GR_DIV_WALL

__all__ = ["Divider", "dividers_from_counts"]


@dataclass
class Divider:
    """A single interior dividing wall.

    Attributes:
        axis: "x" splits the bin along its length (wall runs across the width);
            "y" splits along the width. Matches the old `length_div` /
            `width_div` split respectively.
        pos: Position as a **fraction** of the interior dimension, 0.0-1.0
            exclusive. Fractions rather than mm so a layout survives a change
            of bin size, and so a UI drag handle maps to it directly. For
            evenly spaced dividers this is (i + 1) / (n + 1).
        thickness: Wall thickness in mm.
        height: Wall height in mm above the floor. None means full height.
        notch_depth: Depth of a U-notch cut down from the top of the wall, mm.
            0 disables. Lets long items bridge two compartments (ostat 1C.13).
        notch_width: Width of that notch, mm. 0 means auto -- half the wall's
            span, matching ostat's default.
        top_angle: Angle of the wall's top face in degrees, 0 for flat. 65
            gives the sloped top used for filing flat items upright, so they
            drop in without catching an edge (from ostat 1D.12).
    """

    axis: str
    pos: float
    thickness: float = GR_DIV_WALL
    height: Optional[float] = None
    notch_depth: float = 0.0
    notch_width: float = 0.0
    top_angle: float = 0.0

    def __post_init__(self):
        if self.axis not in ("x", "y"):
            raise ValueError("Divider axis must be 'x' or 'y', got %r" % (self.axis,))
        if not 0.0 < self.pos < 1.0:
            raise ValueError(
                "Divider pos must be a fraction strictly between 0 and 1, got %r. "
                "It is a fraction of the interior dimension, not millimetres."
                % (self.pos,)
            )
        if self.thickness <= 0:
            raise ValueError(
                "Divider thickness must be positive, got %r" % (self.thickness,)
            )
        if self.height is not None and self.height <= 0:
            raise ValueError(
                "Divider height must be positive or None (full height), got %r"
                % (self.height,)
            )
        if self.notch_depth < 0:
            raise ValueError(
                "Divider notch_depth cannot be negative, got %r" % (self.notch_depth,)
            )
        if self.notch_width < 0:
            raise ValueError(
                "Divider notch_width cannot be negative, got %r" % (self.notch_width,)
            )
        if not -90.0 < self.top_angle < 90.0:
            raise ValueError(
                "Divider top_angle must be between -90 and 90 degrees, got %r"
                % (self.top_angle,)
            )

    @property
    def is_full_height(self) -> bool:
        return self.height is None

    @property
    def has_notch(self) -> bool:
        return self.notch_depth > 0

    def offset_mm(self, interior_dim: float) -> float:
        """Position in mm from the interior's low edge, given its length."""
        return self.pos * interior_dim


def dividers_from_counts(length_div: int, width_div: int):
    """Build evenly-spaced dividers, reproducing the old integer behaviour.

    `length_div=2` yields walls at 1/3 and 2/3 of the interior length --
    identical placement to the arithmetic it replaces.
    """
    out = []
    for i in range(int(length_div)):
        out.append(Divider(axis="x", pos=(i + 1) / (length_div + 1)))
    for j in range(int(width_div)):
        out.append(Divider(axis="y", pos=(j + 1) / (width_div + 1)))
    return out
