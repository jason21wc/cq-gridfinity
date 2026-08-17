#! /usr/bin/env python
"""Generate the P3 reference models -- the smkent rugged box (1E.1-1E.14).

Every claim about this box is machine-measured. These are the files a human
looks at, so the set is designed rather than enumerated.

DESIGN OF THE SET
-----------------
Screening design, main effects, every level of every factor seen at least
once. Factors and levels:

    A  latch_type          clip | draw                       (2)
    B  baseplate           minimal | magnets | mag+skel      (3)
    C  lip_seal_type       none | wedge | square | filament  (4)
    D  reinforced_corners  off | on                          (2)
    E  hinge_end_stops     off | on                          (2)
    F  stacking_latches    off | on                          (2)
    G  third hinge         absent | present   (driven by length_u >= 5)
    H  latch count         1 | 2              (driven by length_u <= 2)
    I  stacking 2nd catch  absent | present   (driven by body > 40mm)

Four runs is the floor: C has four levels, so no smaller set can show them
all. Full PAIRWISE coverage would need at least 4 x 3 = 12 runs -- roughly
triple the files -- so it is deliberately not attempted. Some two-factor
interactions are therefore aliased (with six two-level factors in four runs
they must be; this is a resolution III design). Interactions are covered by
the test suite, which runs combinations no human needs to look at.

G and H are coupled: length_u drives both, and a 1-latch box cannot have a
third hinge, so that cell is unreachable rather than merely unused.

The latches are exported ONCE, not per box. They are geometrically identical
at every box size -- same volume to six decimals, same face count -- because
they depend on latch parameters alone. Four copies of one part is not
coverage.

Usage:
    python examples/scripts/generate_p3_reference.py
    python examples/scripts/generate_p3_reference.py --out ~/Downloads/gridfinity-shipset
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import cadquery as cq

from cqgridfinity import GridfinityRuggedBoxSmkent

DEFAULT_OUT = Path(__file__).resolve().parents[1] / "output" / "p3"


# (stem, kwargs, what this run is for)
# Levels are assigned so each factor's levels are as balanced as four runs
# allow, and so latch_type is fully crossed with reinforced_corners and with
# hinge_end_stops -- the two interactions most likely to show up by eye.
RUNS = [
    (
        "run1_2x2x4",
        dict(
            length_u=2, width_u=2, height_u=4,
            latch_type="clip", lip_seal_type="none",
            baseplate_magnets=False, baseplate_skeletonized=False,
            reinforced_corners=False, hinge_end_stops=False,
            stacking_latches=False,
        ),
        "Smallest box, everything OFF. ONE latch (2U), no third hinge, no "
        "seal, no stacking mounts, bare corners -- the baseline to compare "
        "the others against",
    ),
    (
        "run2_3x2x6",
        dict(
            length_u=3, width_u=2, height_u=6,
            latch_type="draw", lip_seal_type="wedge",
            baseplate_magnets=True, baseplate_skeletonized=False,
            reinforced_corners=True, hinge_end_stops=True,
            stacking_latches=True,
        ),
        "Draw latch, magnet baseplate, wedge seal, reinforced corners, end "
        "stops. TWO latches but still no third hinge",
    ),
    (
        "run3_5x4x6",
        dict(
            length_u=5, width_u=4, height_u=6,
            latch_type="clip", lip_seal_type="square",
            baseplate_magnets=True, baseplate_skeletonized=True,
            reinforced_corners=True, hinge_end_stops=True,
            stacking_latches=True,
        ),
        "THIRD HINGE appears at 5U. Skeletonized magnet baseplate, square "
        "seal",
    ),
    (
        "run4_6x4x9",
        dict(
            length_u=6, width_u=4, height_u=9,
            latch_type="draw", lip_seal_type="filament-1.75mm",
            baseplate_magnets=False, baseplate_skeletonized=False,
            reinforced_corners=False, hinge_end_stops=False,
            stacking_latches=True,
        ),
        "Body over 40mm, so the stacking latch gains its SECOND catch. "
        "Filament seal grooves both halves instead of moulding a ridge",
    ),
]

# Exported once each: identical at every box size.
SHARED = [
    ("smkent_latch_clip", dict(latch_type="clip"), "render_latch",
     "The clip latch. One flexing part, no hardware but its screws"),
    ("smkent_latch_draw_handle", dict(latch_type="draw"),
     "render_draw_latch_handle_segmented",
     "Draw latch handle -- half of a two-part over-centre toggle"),
    ("smkent_latch_draw_catch", dict(latch_type="draw"),
     "render_draw_latch_catch_segmented",
     "Draw latch catch. Its fingers interlock with the handle's slots"),
    ("smkent_stacking_latch", dict(), "render_stacking_latch",
     "Stacking latch: a clip latch with a second catch, locking box to box"),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="output directory")
    args = ap.parse_args()
    out = Path(args.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)

    n = 0
    t_all = time.time()
    for stem, kwargs, _purpose in RUNS:
        box = GridfinityRuggedBoxSmkent(**kwargs)
        t0 = time.time()
        for label, shape in (("body", box.render_body()), ("lid", box.render_lid())):
            path = out / f"smkent_{stem}_{label}.step"
            assert shape.val().isValid(), f"{path.name} is not a valid solid"
            assert len(shape.val().Solids()) == 1, f"{path.name} is not one piece"
            cq.exporters.export(shape, str(path))
            n += 1
        print("  %-14s body+lid  %5.1fs  BOM %s" % (stem, time.time() - t0, box.bom()))

    canonical = GridfinityRuggedBoxSmkent(5, 4, 6)
    for stem, kwargs, method, _purpose in SHARED:
        box = GridfinityRuggedBoxSmkent(5, 4, 6, **kwargs) if kwargs else canonical
        shape = getattr(box, method)()
        path = out / f"{stem}.step"
        assert shape.val().isValid(), f"{path.name} is not a valid solid"
        cq.exporters.export(shape, str(path))
        n += 1
        print("  %-28s (size-invariant, exported once)" % stem)

    print("\n%d files in %.1fs -> %s" % (n, time.time() - t_all, out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
