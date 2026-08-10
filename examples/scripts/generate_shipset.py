#!/usr/bin/env python
"""Generate the P1 ship set -- the common Gridfinity parts (ROADMAP.md §4).

This is the deliverable that tests the project's premise for the first time:
one command produces the parts people actually print, every solid validated
watertight, ready to open in real CAD.

The set is deliberately the *minimum* that exercises the pipeline end to end,
not a bound on what the library can make. Layering more options onto the
standard bin is the point of the architecture.

Usage:
    python examples/scripts/generate_shipset.py
    python examples/scripts/generate_shipset.py --out ~/Downloads/gridfinity-shipset
    python examples/scripts/generate_shipset.py --out ~/Downloads/gfx --skip-rugged

Then audit the result:
    python tools/step_audit.py ~/Downloads/gridfinity-shipset
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from cqgridfinity import (
    GridfinityBaseplate,
    GridfinityBox,
    GridfinityRuggedBox,
    GridfinitySolidBox,
)

DEFAULT_OUT = Path(__file__).resolve().parents[1] / "output" / "shipset"


# Each entry: (filename_stem, builder, one-line purpose)
# Purpose strings are not decoration -- per D5, nothing ships without a stated
# use case, and these become the manifest a user reads.
def build_manifest(skip_rugged: bool = False):
    items = []

    # -- Baseplates -------------------------------------------------------
    # Every Gridfinity install needs one. Plain saves filament; magnet holds
    # bins down in a drawer that gets opened hard or a box that gets carried.
    for lu, wu in ((2, 2), (3, 3), (4, 4), (2, 4)):
        items.append((
            f"baseplate_{lu}x{wu}_plain",
            lambda lu=lu, wu=wu: GridfinityBaseplate(lu, wu),
            "Plain baseplate - cheapest, lightest, bins sit by gravity",
        ))
        items.append((
            f"baseplate_{lu}x{wu}_magnet",
            lambda lu=lu, wu=wu: GridfinityBaseplate(lu, wu, magnet_holes=True),
            "Magnet baseplate - bins stay put when the drawer is yanked",
        ))

    # -- Bins: footprint coverage at a shallow height ---------------------
    # 3U is the workhorse depth for small hardware and loose parts.
    for lu, wu in ((1, 1), (1, 2), (2, 1), (1, 3), (2, 2), (2, 3), (3, 2)):
        items.append((
            f"bin_{lu}x{wu}x3_plain",
            lambda lu=lu, wu=wu: GridfinityBox(lu, wu, 3),
            "Standard bin - the default container",
        ))

    # -- Bins: taller variants --------------------------------------------
    # 6U holds tools stood upright, tall bottles, longer stock.
    for lu, wu in ((1, 2), (2, 2), (3, 2)):
        items.append((
            f"bin_{lu}x{wu}x6_plain",
            lambda lu=lu, wu=wu: GridfinityBox(lu, wu, 6),
            "Deep bin - upright tools, tall items",
        ))

    # -- Bins: the feature combinations people actually print --------------
    items += [
        ("bin_2x2x6_scoop",
         lambda: GridfinityBox(2, 2, 6, scoops=True),
         "Scoop - radiused front floor so you can sweep small parts out"),
        ("bin_2x2x6_label",
         lambda: GridfinityBox(2, 2, 6, labels=True),
         "Label shelf - flat ledge along the back wall for a tape/paper label"),
        ("bin_2x2x6_scoop_label",
         lambda: GridfinityBox(2, 2, 6, scoops=True, labels=True),
         "Scoop + label - the classic parts bin, most-printed combination"),
        ("bin_1x3x6_scoop_label",
         lambda: GridfinityBox(1, 3, 6, scoops=True, labels=True),
         "Narrow parts bin - fits more lanes per drawer"),
        ("bin_2x3x6_div2",
         lambda: GridfinityBox(2, 3, 6, length_div=1, width_div=1),
         "Divided bin - 4 compartments, sorts related small parts together"),
        ("bin_3x2x6_div_label",
         lambda: GridfinityBox(3, 2, 6, length_div=2, labels=True),
         "Divided + labelled - 3 lanes, each identified"),
        ("bin_2x2x3_holes",
         lambda: GridfinityBox(2, 2, 3, holes=True),
         "Magnet holes - bin locks to a magnet baseplate, survives tipping"),
        ("bin_2x2x3_lite",
         lambda: GridfinityBox(2, 2, 3, lite_style=True),
         "Lite style - thin walls, no raised floor; least filament and time"),
        ("bin_2x2x6_nolip",
         lambda: GridfinityBox(2, 2, 6, lip_style="none"),
         "No stacking lip - flat rim, for bins that never stack"),
    ]

    # -- Lids --------------------------------------------------------------
    # A solid bin IS the community-standard lid: the stacking lip mates it to
    # the bin below. Rests, does not latch -- see PRODUCTS.md.
    for lu, wu in ((1, 1), (1, 2), (2, 2), (2, 3)):
        items.append((
            f"lid_{lu}x{wu}x1_solid",
            lambda lu=lu, wu=wu: GridfinitySolidBox(lu, wu, 1),
            "Lid - solid bin sits on top, held by the stacking lip",
        ))

    # -- Rugged box --------------------------------------------------------
    if not skip_rugged:
        items.append((
            "ruggedbox_4x3x6",
            lambda: GridfinityRuggedBox(4, 3, 6),
            "Rugged box - hinged lid, clasps, handle (CC BY-NC-SA, see LICENSE-COMPONENTS.md)",
        ))

    return items


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=str(DEFAULT_OUT),
                    help=f"output directory (default: {DEFAULT_OUT})")
    ap.add_argument("--skip-rugged", action="store_true",
                    help="skip the rugged box (slowest model; known xfail on lid)")
    ap.add_argument("--no-validate", action="store_true",
                    help="skip isValid() checks (faster, not recommended)")
    args = ap.parse_args(argv)

    out = Path(args.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)

    manifest = build_manifest(skip_rugged=args.skip_rugged)
    print(f"Generating {len(manifest)} models -> {out}\n")

    failures, invalid = [], []
    manifest_lines = ["# Ship Set Manifest\n",
                      "| Model | Purpose |", "|-------|---------|"]
    t_start = time.time()

    for i, (stem, builder, purpose) in enumerate(manifest, 1):
        t0 = time.time()
        status = "ok"
        try:
            obj = builder()
            # Rugged box renders an assembly; everything else a single solid.
            if isinstance(obj, GridfinityRuggedBox):
                shape = obj.render_assembly()
            else:
                shape = obj.render()

            if not args.no_validate and hasattr(shape, "val"):
                if not shape.val().isValid():
                    status = "INVALID"
                    invalid.append(stem)

            obj.save_step_file(str(out / f"{stem}.step"))
        except Exception as exc:  # noqa: BLE001 - report, keep going
            status = f"FAILED {type(exc).__name__}"
            failures.append((stem, f"{type(exc).__name__}: {exc}"))

        dt = time.time() - t0
        mark = "✓" if status == "ok" else "✗"
        print(f"[{i:>2}/{len(manifest)}] {mark} {stem:<32} {dt:>6.1f}s  {status if status != 'ok' else ''}")
        manifest_lines.append(f"| `{stem}.step` | {purpose} |")

    (out / "MANIFEST.md").write_text("\n".join(manifest_lines) + "\n")

    total = time.time() - t_start
    print(f"\n{len(manifest)} models in {total:.1f}s -> {out}")
    print(f"Manifest: {out / 'MANIFEST.md'}")

    if invalid:
        print(f"\n⚠️  {len(invalid)} model(s) NOT watertight (DoD-2 failure):")
        for s in invalid:
            print(f"    {s}")
    if failures:
        print(f"\n❌ {len(failures)} model(s) failed to generate:")
        for s, e in failures:
            print(f"    {s}: {e}")

    print(f"\nNext: python tools/step_audit.py {out}")
    return 1 if (failures or invalid) else 0


if __name__ == "__main__":
    sys.exit(main())
