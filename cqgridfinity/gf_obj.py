#! /usr/bin/env python3
#
# Copyright (C) 2023  Michael Gale
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
# Gridfinity base object class

import math
import os

from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.StlAPI import StlAPI_Writer
import cadquery as cq
from cadquery import exporters

from cqgridfinity.constants import (
    EPS,
    GR_HOLE_DIST,
    GR_RAD,
    GR_TOL,
    GRU,
    GRU2,
    GRHU,
    SQRT2,
)
from cqkit import export_step_file

# Special test to see which version of CadQuery is installed and
# therefore if any compensation is required for extruded zlen
# CQ versions < 2.4.0 typically require zlen correction, i.e.
# scaling the vertical extrusion extent by 1/cos(taper)
ZLEN_FIX = True
_r = cq.Workplane("XY").rect(2, 2).extrude(1, taper=45)
_bb = _r.vals()[0].BoundingBox()
if abs(_bb.zlen - 1.0) < 1e-3:
    ZLEN_FIX = False


class GridfinityObject:
    """Base Gridfinity object class

    This class bundles glabally relevant constants, properties, and methods
    for derived Gridfinity object classes.
    """

    def __init__(self, **kwargs):
        self.length_u = 1
        self.width_u = 1
        self.height_u = 1
        self._cq_obj = None
        self._obj_label = None
        for k, v in kwargs.items():
            if k in self.__dict__:
                self.__dict__[k] = v

    @property
    def cq_obj(self):
        if self._cq_obj is None:
            return self.render()
        return self._cq_obj

    @property
    def length(self):
        return self.length_u * GRU

    @property
    def width(self):
        return self.width_u * GRU

    @property
    def height(self):
        # 3.8 = GR_BASE_HEIGHT (4.75) - GR_WALL (1.0) + GR_BASE_CLR (0.05)
        # This is the offset from the base profile top to where stacking units begin.
        # Inherited from upstream cq-gridfinity; produces correct total heights.
        return 3.8 + GRHU * self.height_u

    @property
    def outer_l(self):
        return self.length_u * GRU - GR_TOL

    @property
    def outer_w(self):
        return self.width_u * GRU - GR_TOL

    @property
    def outer_dim(self):
        return self.outer_l, self.outer_w

    @property
    def half_l(self):
        return (self.length_u - 1) * GRU2

    @property
    def half_w(self):
        return (self.width_u - 1) * GRU2

    @property
    def half_dim(self):
        return self.half_l, self.half_w

    @property
    def outer_rad(self):
        return GR_RAD - GR_TOL / 2

    @property
    def grid_centres(self):
        return [
            (x * GRU, y * GRU)
            for x in range(self.length_u)
            for y in range(self.width_u)
        ]

    @property
    def hole_centres(self):
        return [
            (x * GRU - GR_HOLE_DIST * i, -(y * GRU - GR_HOLE_DIST * j))
            for x in range(self.length_u)
            for y in range(self.width_u)
            for i in (-1, 1)
            for j in (-1, 1)
        ]

    def safe_fillet(self, obj, selector, rad):
        if len(obj.edges(selector).vals()) > 0:
            try:
                return obj.edges(selector).fillet(rad)
            except Exception:
                # Fillet may fail on complex geometry (raised floors,
                # positioned labels, etc.); skip gracefully
                return obj
        return obj

    @property
    def _filename_prefix(self) -> str:
        """Override in subclasses to set the filename type prefix.

        Examples: "gf_baseplate_", "gf_bin_", "gf_drawer_"
        """
        return "gf_"

    def _filename_suffix(self) -> str:
        """Override in subclasses to add type-specific filename parts.

        Returns a string to append after the LxW dimension portion.
        """
        return ""

    def filename(self, prefix=None, path=None):
        """Returns a descriptive readable filename representing a Gridfinity object.

        Naming convention (sorted for filesystem browsing):
          gf_{type}_{LxW[xH]}[_{style}][_{lip}][_{bottom}][_{interior}][_{params}]

        Examples:
          gf_baseplate_4x3_mag-screw_csk
          gf_bin_3x2x5_mag_scoops_labels

        Subclasses override _filename_prefix and _filename_suffix() to
        provide type-specific naming without isinstance chains.
        """
        fn = ""
        if path is not None:
            fn = path + os.sep
        fn += prefix if prefix is not None else self._filename_prefix
        fn += "%dx%d" % (self.length_u, self.width_u)
        fn += self._filename_suffix()
        return fn

    def save_step_file(self, filename=None, path=None, prefix=None):
        fn = (
            filename
            if filename is not None
            else self.filename(path=path, prefix=prefix)
        )
        if not fn.lower().endswith(".step"):
            fn = fn + ".step"
        if isinstance(self.cq_obj, cq.Assembly):
            self.cq_obj.save(fn)
        else:
            export_step_file(self.cq_obj, fn)

    def save_stl_file(
        self, filename=None, path=None, prefix=None, tol=1e-2, ang_tol=0.1
    ):
        fn = (
            filename
            if filename is not None
            else self.filename(path=path, prefix=prefix)
        )
        if not fn.lower().endswith(".stl"):
            fn = fn + ".stl"
        obj = self.cq_obj.val().wrapped
        mesh = BRepMesh_IncrementalMesh(obj, tol, True, ang_tol, True)
        mesh.Perform()
        writer = StlAPI_Writer()
        writer.Write(obj, fn)

    def save_svg_file(self, filename=None, path=None, prefix=None):
        fn = (
            filename
            if filename is not None
            else self.filename(path=path, prefix=prefix)
        )
        if not fn.lower().endswith(".svg"):
            fn = fn + ".svg"
        r = self.cq_obj.rotate((0, 0, 0), (0, 0, 1), 75)
        r = r.rotate((0, 0, 0), (1, 0, 0), -90)
        exporters.export(
            r,
            fn,
            opt={
                "width": 600,
                "height": 400,
                "showAxes": False,
                "marginTop": 20,
                "marginLeft": 20,
                "projectionDir": (1, 1, 1),
            },
        )

    def extrude_profile(self, sketch, profile, workplane="XY", angle=None):
        taper = profile[0][1] if isinstance(profile[0], (list, tuple)) else 0
        zlen = profile[0][0] if isinstance(profile[0], (list, tuple)) else profile[0]
        if abs(taper) > 0:
            if angle is None:
                zlen = zlen if ZLEN_FIX else zlen / SQRT2
            else:
                zlen = zlen / math.cos(math.radians(taper)) if ZLEN_FIX else zlen
        r = cq.Workplane(workplane).placeSketch(sketch).extrude(zlen, taper=taper)
        for level in profile[1:]:
            if isinstance(level, (tuple, list)):
                if angle is None:
                    zlen = level[0] if ZLEN_FIX else level[0] / SQRT2
                else:
                    zlen = (
                        level[0] / math.cos(math.radians(level[1]))
                        if ZLEN_FIX
                        else level[0]
                    )
                r = r.faces(">Z").wires().toPending().extrude(zlen, taper=level[1])
            else:
                r = r.faces(">Z").wires().toPending().extrude(level)
        return r

    @classmethod
    def to_step_file(
        cls,
        length_u,
        width_u,
        height_u=None,
        filename=None,
        prefix=None,
        path=None,
        **kwargs
    ):
        """Convenience method to create, render and save a STEP file representation
        of a Gridfinity object."""
        obj = GridfinityObject.as_obj(cls, length_u, width_u, height_u, **kwargs)
        obj.save_step_file(filename=filename, path=path, prefix=prefix)

    @classmethod
    def to_stl_file(
        cls,
        length_u,
        width_u,
        height_u=None,
        filename=None,
        prefix=None,
        path=None,
        **kwargs
    ):
        """Convenience method to create, render and save an STL file representation
        of a Gridfinity object."""
        obj = GridfinityObject.as_obj(cls, length_u, width_u, height_u, **kwargs)
        obj.save_stl_file(filename=filename, path=path, prefix=prefix)

    @staticmethod
    def as_obj(cls, length_u=None, width_u=None, height_u=None, **kwargs):
        # Lazy imports to avoid circular dependency at import time
        from cqgridfinity.gf_box import GridfinityBox, GridfinitySolidBox
        from cqgridfinity.gf_baseplate import GridfinityBaseplate
        from cqgridfinity.gf_drawer import GridfinityDrawerSpacer
        from cqgridfinity.gf_ruggedbox import GridfinityRuggedBox

        if issubclass(cls, GridfinitySolidBox):
            obj = GridfinityBox(length_u, width_u, height_u, **kwargs)
            obj.solid = True
        elif issubclass(cls, GridfinityBox):
            obj = GridfinityBox(length_u, width_u, height_u, **kwargs)
        elif issubclass(cls, GridfinityBaseplate):
            obj = GridfinityBaseplate(length_u, width_u, **kwargs)
        elif issubclass(cls, GridfinityDrawerSpacer):
            obj = GridfinityDrawerSpacer(**kwargs)
        elif issubclass(cls, GridfinityRuggedBox):
            obj = GridfinityRuggedBox(length_u, width_u, height_u, **kwargs)
        else:
            raise TypeError(
                "as_obj() does not support %s" % cls.__name__
            )
        return obj
