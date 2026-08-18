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
import warnings

from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.ShapeFix import ShapeFix_Shape
from OCP.StlAPI import StlAPI_Writer
import cadquery as cq
from cadquery import exporters

from cqgridfinity.constants import (
    EPS,
    GR_HOLE_DIST,
    GR_STACKING_LIP_H,
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
            else:
                warnings.warn(
                    f"{self.__class__.__name__}: unknown keyword argument '{k}' ignored",
                    stacklevel=2,
                )

    @property
    def cq_obj(self):
        if self._cq_obj is None:
            return self.render()
        return self._cq_obj

    @property
    def _gru(self):
        """Grid unit size for XY dimensions (mm).

        Returns GRU (42mm) for standard bins and baseplates.
        Subclasses override to return GRU2 (21mm) for half-grid mode (1B.13).
        All XY dimension properties derive from this single value so that
        half-grid support is automatic across the whole hierarchy.
        """
        return GRU

    @property
    def length(self):
        return self.length_u * self._gru

    @property
    def width(self):
        return self.width_u * self._gru

    @property
    def height(self):
        """Nominal total height: Grid Z Unit * height units + stacking lip.

        Matches the official "Bin Total Height" drawing. Was hardcoded 3.8 --
        upstream's incorrect lip height -- until 2026-08-15. No subclass
        currently uses this (every one defines its own height), so correcting
        it changes no geometry; it is fixed so a future subclass cannot inherit
        the wrong figure.

        Subclasses whose height is not lip-based (baseplates, rugged boxes)
        override this. GridfinityBox additionally distinguishes nominal from
        `actual_height`, which accounts for the lip tip fillet.
        """
        return GR_STACKING_LIP_H + GRHU * self.height_u

    @property
    def outer_l(self):
        return self.length_u * self._gru - GR_TOL

    @property
    def outer_w(self):
        return self.width_u * self._gru - GR_TOL

    @property
    def outer_dim(self):
        return self.outer_l, self.outer_w

    @property
    def half_l(self):
        # (n-1) * _gru/2: the distance from the first grid-centre to the outer
        # shell centre.  Algebraically equal to (n*_gru - _gru)/2 for any
        # positive n including non-integers (1B.12) and half-grid (1B.13).
        return (self.length_u - 1) * self._gru / 2

    @property
    def half_w(self):
        return (self.width_u - 1) * self._gru / 2

    @property
    def half_dim(self):
        return self.half_l, self.half_w

    @property
    def outer_rad(self):
        return GR_RAD - GR_TOL / 2

    @property
    def grid_centres(self):
        gru = self._gru
        return [
            (x * gru, y * gru)
            for x in range(math.floor(self.length_u))
            for y in range(math.floor(self.width_u))
        ]

    @property
    def hole_centres(self):
        gru = self._gru
        return [
            (x * gru - GR_HOLE_DIST * i, -(y * gru - GR_HOLE_DIST * j))
            for x in range(math.floor(self.length_u))
            for y in range(math.floor(self.width_u))
            for i in (-1, 1)
            for j in (-1, 1)
        ]

    def safe_fillet(self, obj, selector, rad):
        """Fillet the selected edges, degrading gracefully if that is not possible.

        Two very different things used to look identical from outside:
        a selector matching NO edges (a conditional fillet that simply does not
        apply -- routine, e.g. lite_style bins) and the fillet KERNEL FAILING on
        edges that do exist (a real loss of geometry). Only the second warrants
        attention, so only the second warns.
        """
        n_edges = len(obj.edges(selector).vals())
        if n_edges == 0:
            return obj  # nothing to fillet; not a failure
        if rad < 0.05:
            # Below roughly one extrusion width the blend is meaningless, and
            # a near-zero radius cannot succeed anyway. Clamping upstream can
            # legitimately produce this on very short bins.
            return obj
        try:
            return obj.edges(selector).fillet(rad)
        except Exception:
            # Complex geometry (raised floors, positioned labels) can defeat
            # the fillet kernel. The object stays valid but loses this blend,
            # so say so rather than silently shipping a sharper part.
            warnings.warn(
                "%s: fillet r=%.2f failed on %d edge(s); those edges stay "
                "sharp. Geometry is otherwise valid."
                % (self.__class__.__name__, rad, n_edges),
                stacklevel=2,
            )
            return obj

    #: A boolean between near-coincident planes can leave a sliver shell a few
    #: hundredths of a millimetre across. It is an OpenCASCADE artifact, not a
    #: cavity -- below this it is a third of one 0.2mm layer and cannot exist
    #: in a printed part. Real voids found in this project were 13mm3.
    VOID_TOL = 0.1

    def assert_sound(self, obj, what="model"):
        """Refuse to return geometry that is not a single closed solid.

        Range checks on parameters cannot catch this: a feature that lands
        past the wall it was meant to sit on, or two features that merge into
        each other, produce a render that *looks* like it worked -- several
        disconnected lumps, or a solid with a cavity sealed inside it -- while
        every dimensional assertion still passes.

        Voids smaller than `VOID_TOL` across are ignored as boolean slivers.
        Subclasses may catch this and re-raise with parameter-specific advice.
        """
        v = obj.val() if hasattr(obj, "val") else obj
        solids = v.Solids()
        shells = [
            sh for sh in v.Shells()
            if sh.BoundingBox().DiagonalLength >= self.VOID_TOL
        ]
        if len(solids) == 1 and len(shells) == 1 and v.isValid():
            return obj
        problems = []
        if not v.isValid():
            problems.append("the solid is not valid")
        if len(solids) != 1:
            problems.append("%d disconnected pieces" % len(solids))
        if len(shells) > 1:
            problems.append("%d sealed void(s)" % (len(shells) - 1))
        raise ValueError(
            "%s: the %s did not come out as one closed solid: %s. This is a "
            "combination the parameters allow but the geometry cannot build."
            % (self.__class__.__name__, what, "; ".join(problems))
        )

    def repair_if_invalid(self, obj):
        """Repair a solid with OCC's ShapeFix, but only if it is actually invalid.

        Boolean-heavy geometry occasionally leaves faces whose parametrisation
        or tolerance is subtly wrong -- the shell is closed and the volume is
        right, but BRepCheck rejects individual faces. Downstream CAD then
        refuses to treat the result as a solid body, so it cannot be selected
        or edited even though it looks correct.

        ShapeFix_Shape corrects the face representations without altering the
        geometry. This is a no-op when the shape is already valid, so it costs
        nothing on the common path.

        Returns the repaired object, or the original if repair fails or does
        not help -- never raises.
        """
        try:
            shape = obj.val() if isinstance(obj, cq.Workplane) else obj
            if BRepCheck_Analyzer(shape.wrapped).IsValid():
                return obj
            fixer = ShapeFix_Shape(shape.wrapped)
            fixer.Perform()
            fixed = cq.Shape.cast(fixer.Shape())
            if not BRepCheck_Analyzer(fixed.wrapped).IsValid():
                return obj  # repair did not help; keep the original
            return cq.Workplane(obj=fixed) if isinstance(obj, cq.Workplane) else fixed
        except Exception:
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

    @staticmethod
    def _fmt_unit(v):
        """Format a grid unit value for filenames.

        Integers render as plain ints (e.g., 2 → "2").
        Non-integers use 'p' in place of '.' (e.g., 2.5 → "2p5").
        Designed for values in the range 0-100; non-finite inputs raise ValueError.
        """
        if not math.isfinite(v):
            raise ValueError("Grid unit must be a finite number, got %r" % v)
        if v == math.floor(v):
            return "%d" % int(v)
        return ("%g" % v).replace(".", "p")

    def filename(self, prefix=None, path=None):
        """Returns a descriptive readable filename representing a Gridfinity object.

        Naming convention (sorted for filesystem browsing):
          gf_{type}_{LxW[xH]}[_{style}][_{lip}][_{bottom}][_{interior}][_{params}]

        Examples:
          gf_baseplate_4x3_mag-screw_csk
          gf_bin_3x2x5_mag_scoops_labels
          gf_bin_2p5x3x4         (non-integer: 2.5 U rendered as "2p5")

        Subclasses override _filename_prefix and _filename_suffix() to
        provide type-specific naming without isinstance chains.
        """
        fn = ""
        if path is not None:
            fn = path + os.sep
        fn += prefix if prefix is not None else self._filename_prefix
        fn += "%sx%s" % (self._fmt_unit(self.length_u), self._fmt_unit(self.width_u))
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
