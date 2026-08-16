#!/usr/bin/env python
"""Generate the P3 reference models -- the smkent rugged box (1E.1-1E.13).

Every claim about this box so far is machine-measured: watertight, single
shell, zero assembled interference, analytic B-Rep. None of it has been seen
by a human in CAD. That is DoD-3, and these are the files for it.

The four configurations are chosen to exercise the decisions that differ,
not to enumerate options:

  A  5x4x6 clip   - everything on. 5U wide, so the THIRD HINGE is present
  B  5x4x6 draw   - the other latch style, two printed parts on a pin
  C  3x2x4 clip   - small and quick to print; too narrow for a third hinge
  D  6x4x9 clip   - over 40mm, so the stacking latch gets its SECOND catch

Usage:
    python examples/scripts/generate_p3_reference.py
    python examples/scripts/generate_p3_reference.py --out ~/Downloads/gridfinity-shipset

Then audit the result:
    python tools/step_audit.py ~/Downloads/gridfinity-shipset
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from cqgridfinity import GridfinityRuggedBoxSmkent

DEFAULT_OUT = Path(__file__).resolve().parents[1] / "output" / "p3"


# (stem, kwargs, what this configuration is for)
CONFIGS = [
    (
        "smkent_5x4x6_clip",
        dict(
            length_u=5,
            width_u=4,
            height_u=6,
            latch_type="clip",
            baseplate_magnets=True,
            baseplate_skeletonized=True,
        ),
        "Everything on. 5U wide so the third hinge is present; skeletonized "
        "magnet baseplate in the floor",
    ),
    (
        "smkent_5x4x6_draw",
        dict(length_u=5, width_u=4, height_u=6, latch_type="draw"),
        "Draw latch: two printed parts joined by an M3 through the pin. The "
        "only style that CLAMPS, which is what makes the lip seal seal",
    ),
    (
        "smkent_3x2x4_clip",
        dict(length_u=3, width_u=2, height_u=4, latch_type="clip"),
        "Small enough to print in an evening. Too narrow for a third hinge, "
        "and one stacking latch per side rather than two",
    ),
    (
        "smkent_6x4x9_clip",
        dict(length_u=6, width_u=4, height_u=9, latch_type="clip"),
        "Body over 40mm, so the stacking latch gains its second catch and can "
        "actually lock to the box below",
    ),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="output directory")
    args = ap.parse_args()
    out = Path(args.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    t_all = time.time()
    for stem, kwargs, purpose in CONFIGS:
        box = GridfinityRuggedBoxSmkent(**kwargs)
        t0 = time.time()
        parts = box.parts()
        for label, shape in parts.items():
            path = out / f"{stem}_{label}.step"
            box._cq_obj = shape
            box._obj_label = label
            import cadquery as cq

            cq.exporters.export(shape, str(path))
            solids = len(shape.val().Solids())
            rows.append((path.name, purpose if label == "body" else "", solids))
            assert shape.val().isValid(), f"{path.name} is not a valid solid"
            assert solids == 1, f"{path.name} is not one printable piece"
        print(
            "  %-22s %d parts  %5.1fs  BOM %s"
            % (stem, len(parts), time.time() - t0, box.bom())
        )
    print("\n%d files in %.1fs -> %s" % (len(rows), time.time() - t_all, out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
