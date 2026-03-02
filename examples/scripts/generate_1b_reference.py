#!/usr/bin/env python3
"""Generate reference STEP files for all Phase 1B (Kennetek Feature Parity) features.

Features 1B.5-1B.17 from documents/FEATURE-SPEC.md.

Run with: conda run -n gridfinity python examples/scripts/generate_1b_reference.py

Output: examples/output/  (gitignored — regenerate any time)
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from cqgridfinity import (
    GridfinityBaseplate,
    GridfinityBox,
    GridfinityVaseBase,
    GridfinityVaseBox,
)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")
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
    print("Generating Phase 1B reference STEP files...\n")

    # ── 1B.5: Scoop scaling ──────────────────────────────────────────────────
    print("=== 1B.5: Scoop scaling ===")
    save(GridfinityBox(2, 2, 5, scoops=0.3), "1B05_scoop_0.3_2x2x5")
    save(GridfinityBox(2, 2, 5, scoops=0.5), "1B05_scoop_0.5_2x2x5")
    save(GridfinityBox(2, 2, 5, scoops=1.0), "1B05_scoop_1.0_2x2x5")

    # ── 1B.6: Tab positioning ────────────────────────────────────────────────
    print("\n=== 1B.6: Tab positioning ===")
    save(GridfinityBox(3, 2, 5, label_style="full",   length_div=1), "1B06_label_full_3x2x5")
    save(GridfinityBox(3, 2, 5, label_style="left",   length_div=1), "1B06_label_left_3x2x5")
    save(GridfinityBox(3, 2, 5, label_style="center", length_div=1), "1B06_label_center_3x2x5")
    save(GridfinityBox(3, 2, 5, label_style="right",  length_div=1), "1B06_label_right_3x2x5")

    # ── 1B.7: Custom compartment depth ──────────────────────────────────────
    print("\n=== 1B.7: Custom compartment depth ===")
    save(GridfinityBox(2, 2, 5),                             "1B07_depth_default_2x2x5")
    save(GridfinityBox(2, 2, 5, compartment_depth=5),        "1B07_depth_5mm_2x2x5")
    save(GridfinityBox(2, 2, 5, compartment_depth=10),       "1B07_depth_10mm_2x2x5")
    save(GridfinityBox(2, 2, 5, height_internal=10),         "1B07_height-internal-10mm_2x2x5")

    # ── 1B.8: Cylindrical compartments ──────────────────────────────────────
    print("\n=== 1B.8: Cylindrical compartments ===")
    save(GridfinityBox(1, 1, 5, cylindrical=True, cylinder_diam=30),
         "1B08_cylindrical_30mm_1x1x5")
    save(GridfinityBox(2, 2, 5, cylindrical=True, cylinder_diam=20),
         "1B08_cylindrical_20mm_2x2x5")
    save(GridfinityBox(2, 2, 5, cylindrical=True, cylinder_diam=20,
                       length_div=1, width_div=1),
         "1B08_cylindrical_20mm-div_2x2x5")

    # ── 1B.9: Skeletonized baseplate ─────────────────────────────────────────
    print("\n=== 1B.9: Skeletonized baseplate ===")
    save(GridfinityBaseplate(4, 3, skeleton=True),
         "1B09_skeleton_4x3")
    save(GridfinityBaseplate(4, 3, skeleton=True, magnet_holes=True),
         "1B09_skeleton_mag_4x3")
    save(GridfinityBaseplate(4, 3, skeleton=True, screw_holes=True),
         "1B09_skeleton_screw_4x3")
    save(GridfinityBaseplate(4, 3, skeleton=True, magnet_holes=True, screw_holes=True),
         "1B09_skeleton_mag-screw_4x3")

    # ── 1B.10: Screw-together baseplate ──────────────────────────────────────
    print("\n=== 1B.10: Screw-together baseplate ===")
    save(GridfinityBaseplate(4, 3, screw_together=True),
         "1B10_screw-together_4x3")
    save(GridfinityBaseplate(4, 3, screw_together=True, n_screws=2),
         "1B10_screw-together_n2_4x3")
    save(GridfinityBaseplate(4, 3, screw_together=True, magnet_holes=True),
         "1B10_screw-together_mag_4x3")
    save(GridfinityBaseplate(4, 3, skeleton=True, screw_together=True),
         "1B10_skeleton-screw-together_4x3")

    # ── 1B.11: Fit-to-drawer baseplate ───────────────────────────────────────
    print("\n=== 1B.11: Fit-to-drawer baseplate ===")
    save(GridfinityBaseplate(0, 0, distancex=200, distancey=150),
         "1B11_fit-to-drawer_200x150mm")
    save(GridfinityBaseplate(0, 0, distancex=200, distancey=150, fitx=-1),
         "1B11_fit-to-drawer_align-left_200x150mm")
    save(GridfinityBaseplate(0, 0, distancex=200, distancey=150, fitx=1),
         "1B11_fit-to-drawer_align-right_200x150mm")
    save(GridfinityBaseplate(3, 2, distancex=200),
         "1B11_fit-to-drawer_explicit-3x2_200mm")

    # ── 1B.12: Non-integer grid sizes ────────────────────────────────────────
    print("\n=== 1B.12: Non-integer grid sizes ===")
    save(GridfinityBox(2.5, 3, 4),              "1B12_nonint_2p5x3x4")
    save(GridfinityBox(1.5, 2, 3),              "1B12_nonint_1p5x2x3")
    save(GridfinityBox(2.5, 2, 4, holes=True),  "1B12_nonint_2p5x2x4_mag")

    # ── 1B.13: Half-grid 21mm mode ───────────────────────────────────────────
    print("\n=== 1B.13: Half-grid 21mm mode ===")
    save(GridfinityBox(4, 2, 3, half_grid=True),              "1B13_halfgrid_4x2x3")
    save(GridfinityBox(4, 2, 3, half_grid=True, holes=True),  "1B13_halfgrid_4x2x3_mag")
    save(GridfinityBox(2, 2, 3, half_grid=True),              "1B13_halfgrid_2x2x3")

    # ── 1B.14: Height modes (gridz_define) ───────────────────────────────────
    print("\n=== 1B.14: Height modes (gridz_define) ===")
    save(GridfinityBox(2, 2, 3),                              "1B14_height_mode0_2x2x3u")
    save(GridfinityBox(2, 2, 21.0, gridz_define=1),           "1B14_height_mode1_2x2_21mm-int")
    save(GridfinityBox(2, 2, 24.8, gridz_define=2),           "1B14_height_mode2_2x2_24p8mm-ext")
    save(GridfinityBox(2, 2, 29.2, gridz_define=3),           "1B14_height_mode3_2x2_29p2mm-total")

    # ── 1B.15: Z-snap ────────────────────────────────────────────────────────
    print("\n=== 1B.15: Z-snap ===")
    save(GridfinityBox(2, 2, 2.5, enable_zsnap=True),         "1B15_zsnap_mode0_2p5u_snaps-to-3u")
    save(GridfinityBox(2, 2, 25.0, gridz_define=1, enable_zsnap=True),
         "1B15_zsnap_mode1_25mm-int_snaps-to-28mm")

    # ── 1B.16: Spiral vase shell ─────────────────────────────────────────────
    print("\n=== 1B.16: Spiral vase shell (GridfinityVaseBox) ===")
    save(GridfinityVaseBox(1, 1, 3),                              "1B16_vase_1x1x3_default")
    save(GridfinityVaseBox(2, 1, 3),                              "1B16_vase_2x1x3")
    save(GridfinityVaseBox(2, 2, 3),                              "1B16_vase_2x2x3")
    save(GridfinityVaseBox(1, 1, 5, enable_lip=False),            "1B16_vase_1x1x5_nolip")
    save(GridfinityVaseBox(2, 1, 4, n_divx=2),                    "1B16_vase_2x1x4_div2")
    save(GridfinityVaseBox(2, 2, 3, style_base=1),                "1B16_vase_2x2x3_corners")
    save(GridfinityVaseBox(2, 2, 3, style_base=4),                "1B16_vase_2x2x3_noxcut")
    save(GridfinityVaseBox(1, 1, 3, style_tab=3),                 "1B16_vase_1x1x3_tab-right")
    save(GridfinityVaseBox(1, 1, 3, style_tab=6),                 "1B16_vase_1x1x3_tab-none")

    # ── 1B.17: Spiral vase base insert ───────────────────────────────────────
    print("\n=== 1B.17: Spiral vase base insert (GridfinityVaseBase) ===")
    save(GridfinityVaseBase(1, 1),                                "1B17_vasebase_1x1_mag")
    save(GridfinityVaseBase(2, 2),                                "1B17_vasebase_2x2_mag")
    save(GridfinityVaseBase(2, 2, holes=False),                   "1B17_vasebase_2x2_noholes")
    save(GridfinityVaseBase(2, 2, style_base=1),                  "1B17_vasebase_2x2_corners")

    print("\n=== DONE ===")
    step_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".step")]
    print(f"Generated {len(step_files)} STEP files total in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
