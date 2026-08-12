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
# Hole grids for Gridfinity bins

"""Hole grid: an array of shaped holes cut into a solid bin.

For holding arrayed objects -- batteries, hex bits, cards, dowels, test tubes.
The primitive is deliberately generic: **shape, size, rows, columns**. There is
no catalogue of named sizes. With STEP output you can always tweak a hole in
CAD, but you cannot conjure a 4x12 array by hand without pain, so the array is
what the library owes you.

`cylindrical=True` remains as sugar: a circular grid whose rows and columns come
from the bin's compartments.

Note this is a *subtractive* construction -- a solid block with holes cut into
it -- as opposed to the normal additive path of a hollow shell with walls added.
Those are genuinely different constructions, so they stay two named modes rather
than being forced into one pipeline.
"""

import math
from dataclasses import dataclass
from typing import Optional

__all__ = ["HoleGrid"]

SHAPES = ("circle", "hex", "rect")


@dataclass
class HoleGrid:
    """An array of holes cut into a solid bin interior.

    Attributes:
        shape: "circle", "hex" or "rect".
        size: Hole size in mm. For circle, the diameter. For hex, the
            **across-flats** distance, which is what hex stock and bit shanks
            are specified by (a 1/4" bit is 6.35mm across flats). For rect, the
            X dimension.
        size_y: Y dimension for "rect". Defaults to `size` (square).
        rows: Number of holes along Y. None means derive from the bin's
            compartments, matching the old `cylindrical` behaviour.
        cols: Number of holes along X. None means derive from compartments.
        depth: Hole depth in mm from the interior floor. None means full depth.
        chamfer: Chamfer at the hole mouth, mm. Eases insertion and removes the
            first-layer elephant-foot lip.
        clearance: Added to `size` so the part actually fits. FDM holes print
            undersized, so a nominal 14.5mm AA cell needs a slightly larger
            hole. Defaults to 0 -- set it explicitly rather than having the
            library guess at your printer's behaviour.
    """

    shape: str = "circle"
    size: float = 10.0
    size_y: Optional[float] = None
    rows: Optional[int] = None
    cols: Optional[int] = None
    depth: Optional[float] = None
    chamfer: float = 0.5
    clearance: float = 0.0

    def __post_init__(self):
        if self.shape not in SHAPES:
            raise ValueError(
                "HoleGrid shape must be one of %s, got %r" % (SHAPES, self.shape)
            )
        if self.size <= 0:
            raise ValueError("HoleGrid size must be positive, got %r" % (self.size,))
        if self.size_y is not None and self.size_y <= 0:
            raise ValueError("HoleGrid size_y must be positive, got %r" % (self.size_y,))
        for name in ("rows", "cols"):
            v = getattr(self, name)
            if v is not None and v < 1:
                raise ValueError("HoleGrid %s must be >= 1, got %r" % (name, v))
        if self.depth is not None and self.depth <= 0:
            raise ValueError("HoleGrid depth must be positive, got %r" % (self.depth,))
        if self.chamfer < 0:
            raise ValueError("HoleGrid chamfer cannot be negative")
        if self.clearance < 0:
            raise ValueError("HoleGrid clearance cannot be negative")

    @property
    def effective_size(self) -> float:
        """Size actually cut, including clearance."""
        return self.size + self.clearance

    @property
    def effective_size_y(self) -> float:
        base = self.size_y if self.size_y is not None else self.size
        return base + self.clearance

    @property
    def derives_layout(self) -> bool:
        """True if rows/cols come from the bin's compartments."""
        return self.rows is None or self.cols is None

    def footprint(self):
        """(x, y) bounding extent of one hole, used for fit checks."""
        if self.shape == "rect":
            return self.effective_size, self.effective_size_y
        if self.shape == "hex":
            # Across-flats is the width; across-corners is the height.
            af = self.effective_size
            return af, af * 2.0 / math.sqrt(3.0)
        return self.effective_size, self.effective_size
