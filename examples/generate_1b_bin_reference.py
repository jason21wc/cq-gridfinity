#!/usr/bin/env python3
"""Generate reference STEP files for Phase 1B.5-1B.8 bin features.

Usage:
    conda run -n gridfinity python examples/generate_1b_bin_reference.py

Output goes to examples/output/ (gitignored).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cqgridfinity import GridfinityBox

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate(label, box):
    fn = os.path.join(OUTPUT_DIR, label + ".step")
    print(f"  Generating {label}...", end=" ", flush=True)
    box.render()
    box.save_step_file(filename=fn)
    print("done")


if __name__ == "__main__":
    print("=== Phase 1B.5-1B.8: Bin Feature Reference STEP Files ===\n")

    # 1B.5: Scoop scaling
    print("1B.5: Scoop scaling (0-1)")
    generate("1B5_scoop_0.3", GridfinityBox(2, 2, 5, scoops=0.3))
    generate("1B5_scoop_0.5", GridfinityBox(2, 2, 5, scoops=0.5))
    generate("1B5_scoop_1.0", GridfinityBox(2, 2, 5, scoops=1.0))

    # 1B.6: Tab positioning
    print("\n1B.6: Tab positioning (6 styles)")
    generate("1B6_label_full", GridfinityBox(3, 2, 5, label_style="full", length_div=1))
    generate("1B6_label_auto", GridfinityBox(3, 2, 5, label_style="auto", length_div=1))
    generate("1B6_label_left", GridfinityBox(3, 2, 5, label_style="left", length_div=1))
    generate("1B6_label_center", GridfinityBox(3, 2, 5, label_style="center", length_div=1))
    generate("1B6_label_right", GridfinityBox(3, 2, 5, label_style="right", length_div=1))

    # 1B.7: Custom compartment depth
    print("\n1B.7: Custom compartment depth")
    generate("1B7_depth_0", GridfinityBox(2, 2, 5))
    generate("1B7_depth_5mm", GridfinityBox(2, 2, 5, compartment_depth=5))
    generate("1B7_depth_10mm", GridfinityBox(2, 2, 5, compartment_depth=10))
    generate("1B7_height_internal_10mm", GridfinityBox(2, 2, 5, height_internal=10))

    # 1B.8: Cylindrical compartments
    print("\n1B.8: Cylindrical compartments")
    generate("1B8_cylindrical_1x1", GridfinityBox(1, 1, 5, cylindrical=True, cylinder_diam=30))
    generate("1B8_cylindrical_2x2", GridfinityBox(2, 2, 5, cylindrical=True, cylinder_diam=20))
    generate("1B8_cylindrical_2x2_div",
             GridfinityBox(2, 2, 5, cylindrical=True, cylinder_diam=20,
                           length_div=1, width_div=1))
    generate("1B8_cylindrical_3x3_small",
             GridfinityBox(3, 3, 5, cylindrical=True, cylinder_diam=10,
                           length_div=2, width_div=2))

    print(f"\nAll files saved to: {OUTPUT_DIR}")
