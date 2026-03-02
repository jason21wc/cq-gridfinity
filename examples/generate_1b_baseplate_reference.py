#!/usr/bin/env python3
"""Generate reference STEP files for Phase 1B.9-1B.13 features.

1B.9:  Skeletonized baseplate
1B.10: Screw-together baseplate
1B.11: Fit-to-drawer baseplate
1B.12: Non-integer grid sizes (bins)
1B.13: Half-grid 21mm mode (bins)

Usage:
    conda run -n gridfinity python examples/generate_1b_baseplate_reference.py

Output goes to examples/output/ (gitignored).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cqgridfinity import GridfinityBaseplate, GridfinityBox

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate(label, obj):
    fn = os.path.join(OUTPUT_DIR, label + ".step")
    print(f"  Generating {label}...", end=" ", flush=True)
    obj.render()
    obj.save_step_file(filename=fn)
    print("done")


if __name__ == "__main__":
    print("=== Phase 1B.9-1B.13: Reference STEP Files ===\n")

    # 1B.9: Skeletonized baseplate
    print("1B.9: Skeletonized baseplate")
    generate("1B9_skeleton_4x3",
             GridfinityBaseplate(4, 3, skeleton=True))
    generate("1B9_skeleton_mag_4x3",
             GridfinityBaseplate(4, 3, skeleton=True, magnet_holes=True))
    generate("1B9_skeleton_screw_4x3",
             GridfinityBaseplate(4, 3, skeleton=True, screw_holes=True))
    generate("1B9_skeleton_mag-screw_4x3",
             GridfinityBaseplate(4, 3, skeleton=True, magnet_holes=True, screw_holes=True))

    # 1B.10: Screw-together baseplate
    print("\n1B.10: Screw-together baseplate")
    generate("1B10_screw-together_4x3",
             GridfinityBaseplate(4, 3, screw_together=True))
    generate("1B10_screw-together_n2_4x3",
             GridfinityBaseplate(4, 3, screw_together=True, n_screws=2))
    generate("1B10_screw-together_mag_4x3",
             GridfinityBaseplate(4, 3, screw_together=True, magnet_holes=True))
    generate("1B10_screw-together_skeleton_4x3",
             GridfinityBaseplate(4, 3, skeleton=True, screw_together=True))

    # 1B.11: Fit-to-drawer baseplate
    print("\n1B.11: Fit-to-drawer baseplate")
    generate("1B11_fit-to-drawer_200x150",
             GridfinityBaseplate(0, 0, distancex=200, distancey=150))
    generate("1B11_fit-to-drawer_fitx-left_200x150",
             GridfinityBaseplate(0, 0, distancex=200, distancey=150, fitx=-1))
    generate("1B11_fit-to-drawer_fitx-right_200x150",
             GridfinityBaseplate(0, 0, distancex=200, distancey=150, fitx=1))
    generate("1B11_fit-to-drawer_explicit-grid_3x2_200mm",
             GridfinityBaseplate(3, 2, distancex=200))

    # 1B.12: Non-integer grid sizes
    print("\n1B.12: Non-integer grid sizes")
    generate("1B12_nonint_2p5x3x4",
             GridfinityBox(2.5, 3, 4))
    generate("1B12_nonint_1p5x2x3",
             GridfinityBox(1.5, 2, 3))
    generate("1B12_nonint_2p5x2x4_mag",
             GridfinityBox(2.5, 2, 4, holes=True))

    # 1B.13: Half-grid 21mm mode
    print("\n1B.13: Half-grid 21mm mode")
    generate("1B13_halfgrid_4x2x3",
             GridfinityBox(4, 2, 3, half_grid=True))
    generate("1B13_halfgrid_4x2x3_mag",
             GridfinityBox(4, 2, 3, half_grid=True, holes=True))
    generate("1B13_halfgrid_2x2x3",
             GridfinityBox(2, 2, 3, half_grid=True))

    print(f"\nAll files saved to: {OUTPUT_DIR}")
