#! /usr/bin/env python3
#
# Gridfinity Trays — shallow, open bins for catching loose items
#
# Copyright (C) 2026  Jason Collier
# MIT License (see LICENSE)

import os

from cqgridfinity import *
from cqgridfinity.gf_box import GridfinityBox


class GridfinityTray(GridfinityBox):
    """A Gridfinity tray — shallow, open bin for catching loose items.

    Inherits all GridfinityBox features. Defaults are optimized for tray use:
    no lip, scoops enabled, low height (2U).

    Parameters (in addition to all GridfinityBox params):
      All GridfinityBox parameters are supported. Defaults changed:
        height_u: 2 (shallow)
        lip_style: "none" (trays don't need stacking lip)
        scoops: True (easy item retrieval)
    """

    def __init__(self, length_u, width_u, height_u=2, **kwargs):
        tray_defaults = {
            "lip_style": "none",
            "scoops": True,
        }
        merged = {**tray_defaults, **kwargs}
        super().__init__(length_u, width_u, height_u, **merged)

    def filename(self, prefix=None, path=None):
        if prefix is not None:
            fn_prefix = prefix
        else:
            fn_prefix = "gf_tray_"
        fn = ""
        if path is not None:
            fn = path + os.sep
        fn += fn_prefix
        fn += "%dx%dx%d" % (self.length_u, self.width_u, self.height_u)
        if self.scoops:
            fn += "_scoops"
        if self.holes:
            fn += "_mag"
        if self.labels:
            fn += "_labels"
        if self.length_div:
            fn += "_div%d" % self.length_div
        if self.width_div:
            if self.length_div:
                fn += "x%d" % self.width_div
            else:
                fn += "_divx%d" % self.width_div
        return fn
