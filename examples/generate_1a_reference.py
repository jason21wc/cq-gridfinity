#!/usr/bin/env python3
"""Generate reference STEP files for all Phase 1A (Already Implemented) features.

Features 0.1-0.20 from documents/FEATURE-SPEC.md.
Run with: conda run -n gridfinity python examples/generate_1a_reference.py
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cqgridfinity import (
    GridfinityBaseplate,
    GridfinityBox,
    GridfinitySolidBox,
)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def save(obj, name):
    """Render and save a STEP file, printing timing info."""
    t0 = time.time()
    obj.render()
    t1 = time.time()
    path = os.path.join(OUTPUT_DIR, name + ".step")
    obj.save_step_file(filename=path)
    t2 = time.time()
    print(f"  {name}.step  (render {t1 - t0:.1f}s, save {t2 - t1:.1f}s)")


def main():
    print("Generating Phase 1A reference STEP files...\n")
    print("=== BASEPLATES ===")

    # 0.1 - Plain baseplate
    save(GridfinityBaseplate(4, 3), "0.01_baseplate_plain_4x3")

    # 0.2 - Extended-depth baseplate
    save(GridfinityBaseplate(4, 3, ext_depth=5), "0.02_baseplate_ext-depth_4x3")

    # 0.3 - Corner screw baseplate
    save(
        GridfinityBaseplate(4, 3, ext_depth=5, corner_screws=True),
        "0.03_baseplate_corner-screws_4x3",
    )

    # 0.13 - Magnet holes baseplate
    save(
        GridfinityBaseplate(4, 3, magnet_holes=True),
        "0.13_baseplate_magnets_4x3",
    )

    # 0.14 - Screw holes baseplate
    save(
        GridfinityBaseplate(4, 3, screw_holes=True),
        "0.14_baseplate_screws_4x3",
    )

    # 0.15 - Combined magnet + screw baseplate
    save(
        GridfinityBaseplate(4, 3, magnet_holes=True, screw_holes=True),
        "0.15_baseplate_mag-screw_4x3",
    )

    # 0.16 - Weighted baseplate
    save(
        GridfinityBaseplate(4, 3, weighted=True, magnet_holes=True),
        "0.16_baseplate_weighted_4x3",
    )

    print("\n=== BINS ===")

    # 0.4 - Standard bin
    save(GridfinityBox(3, 2, 5), "0.04_bin_standard_3x2x5")

    # 0.5 - Lite-style bin
    save(GridfinityBox(3, 2, 5, lite_style=True), "0.05_bin_lite_3x2x5")

    # 0.6 - Solid block
    save(GridfinitySolidBox(3, 2, 3), "0.06_bin_solid_3x2x3")

    # 0.7 - Dividers (length + width)
    save(
        GridfinityBox(3, 2, 5, length_div=2, width_div=1),
        "0.07_bin_dividers_3x2x5_div2x1",
    )

    # 0.8 - Scoops
    save(GridfinityBox(3, 2, 5, scoops=True), "0.08_bin_scoops_3x2x5")

    # 0.9 - Labels
    save(GridfinityBox(3, 2, 5, labels=True), "0.09_bin_labels_3x2x5")

    # 0.10 - Unsupported holes (bins)
    save(GridfinityBox(3, 2, 5, holes=True), "0.10_bin_holes_3x2x5")

    # All features combined
    save(
        GridfinityBox(
            3, 2, 5,
            holes=True,
            scoops=True,
            labels=True,
            length_div=2,
            width_div=1,
        ),
        "0.04-10_bin_all-features_3x2x5",
    )

    print("\n=== LIP STYLES ===")

    # 0.17 - Normal lip (default)
    save(GridfinityBox(2, 2, 3), "0.17_bin_lip-normal_2x2x3")

    # 0.18 - Reduced lip
    save(
        GridfinityBox(2, 2, 3, lip_style="reduced"),
        "0.18_bin_lip-reduced_2x2x3",
    )

    # 0.19 - No lip
    save(
        GridfinityBox(2, 2, 3, lip_style="none"),
        "0.19_bin_lip-none_2x2x3",
    )

    print("\n=== CONFIGURABLE FILLET ===")

    # 0.20 - Custom interior fillet
    save(
        GridfinityBox(3, 2, 5, fillet_rad=1.0),
        "0.20_bin_fillet-1.0_3x2x5",
    )

    # Compare: default fillet for reference
    save(
        GridfinityBox(3, 2, 5),
        "0.20_bin_fillet-default_3x2x5",
    )

    print("\n=== DONE ===")
    step_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".step")]
    print(f"Generated {len(step_files)} STEP files in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
