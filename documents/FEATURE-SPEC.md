# Feature Traceability Specification

**Project:** Gridfinity STEP Generator
**Mode:** Standard
**Version:** 1.0
**Created:** 2026-02-26

> **SCOPE RULE:** Every feature in this document traces to a specific upstream source.
> If a feature cannot be traced to a row in this matrix, it MUST NOT be implemented.
> If a planned feature is not listed here, it is OUT OF SCOPE until added with traceability.

---

## Specification Summary

- **Problem:** No Gridfinity generator produces native STEP files — only STL (mesh) or OpenSCAD (requires OpenSCAD toolchain). STEP is the standard exchange format for manufacturing and CAD editing.
- **Users:** Makers, engineers, and designers who need editable Gridfinity geometry for Fusion 360, SolidWorks, FreeCAD, or CNC workflows.
- **Core Value:** Generate exact B-Rep STEP files for the full Gridfinity ecosystem from a Python library and CLI.
- **Approach:** Fork cq-gridfinity (MIT), extend with independent CadQuery implementations of features defined by 6 upstream Gridfinity projects.

---

## Out of Scope (Maintained List)

These items are explicitly NOT being built. Do not implement them.

| Item | Reason | Date Added |
|------|--------|------------|
| OpenGrid (28mm grid) | Not Gridfinity-native, different grid standard | 2026-02-26 |
| Underware cable management | Not Gridfinity-native, different system | 2026-02-26 |
| Voronoi wall patterns | Requires scipy dependency, defer to future | 2026-02-26 |
| Thumbscrew holes (M15x1.5) | Computationally expensive in CadQuery, defer | 2026-02-26 |
| Kumiko wall pattern | Complex geometry, insufficient spec detail | 2026-02-26 |
| Web UI (Phase 2) | Deferred until library is complete | 2026-02-26 |
| Deployment/Docker (Phase 3) | Deferred until web UI exists | 2026-02-26 |
| STL-to-STEP conversion | Not viable; native generation only | 2026-02-22 |
| Custom-invented features | No upstream source = no implementation | 2026-02-26 |
| ostat code porting | GPL license; spec reference only | 2026-02-22 |

---

## Feature Traceability Matrix

### Legend

- **Source:** Upstream project providing the specification
- **Source File:** Specific file/function in that project (verified where possible, `[needs verify]` where not)
- **Phase:** Which sub-phase implements this feature
- **Status:** Not Started / In Progress / Complete / Verified (tested)
- **Acceptance:** How we verify the implementation is correct

---

### Already Implemented (cq-gridfinity upstream + our additions)

| # | Feature | Source | Source File | Status | Acceptance |
|---|---------|--------|-------------|--------|------------|
| 0.1 | Plain baseplate | cq-gridfinity | `gf_baseplate.py` | Verified | BBox matches GRU * L x GRU * W x 4.75mm |
| 0.2 | Extended-depth baseplate | cq-gridfinity | `gf_baseplate.py` | Verified | BBox height = 4.75 + ext_depth |
| 0.3 | Corner screw baseplate | cq-gridfinity | `gf_baseplate.py` | Verified | 4 CSK holes at corners |
| 0.4 | Standard bin | cq-gridfinity | `gf_box.py` | Verified | BBox, watertight, stacking lip present |
| 0.5 | Lite-style bin | cq-gridfinity | `gf_box.py` | Verified | No elevated floor, thin walls |
| 0.6 | Solid block | cq-gridfinity | `gf_box.py` | Verified | solid_ratio controls fill |
| 0.7 | Dividers (length + width) | cq-gridfinity | `gf_box.py` | Verified | Correct compartment count |
| 0.8 | Scoops | cq-gridfinity | `gf_box.py` | Verified | Radiused front wall interior |
| 0.9 | Labels | cq-gridfinity | `gf_box.py` | Verified | Flat ledge on back wall |
| 0.10 | Unsupported holes (bins) | cq-gridfinity | `gf_box.py` | Verified | Bridge fillers present |
| 0.11 | Rugged box (Pred) | cq-gridfinity | `gf_ruggedbox.py` | Verified | Assembly renders |
| 0.12 | Drawer spacer | cq-gridfinity | `gf_drawer.py` | Verified | Best-fit to dimensions |
| 0.13 | Magnet holes (baseplate) | kennetek + our impl | `gf_baseplate.py` | Verified | 6.5mm dia, 2.4mm deep, 4/cell |
| 0.14 | Screw holes (baseplate) | kennetek + our impl | `gf_baseplate.py` | Verified | 3.0mm dia, through-holes |
| 0.15 | Combined mag+screw (baseplate) | kennetek + our impl | `gf_baseplate.py` | Verified | Both present, correct depths |
| 0.16 | Weighted baseplate | kennetek + our impl | `gf_baseplate.py` | Verified | Weight pockets + cross channels |
| 0.17 | Stacking lip: normal | cq-gridfinity + kennetek | `gf_box.py` | Verified | Full interlocking profile |
| 0.18 | Stacking lip: reduced | Our impl (kennetek spec) | `gf_box.py` | Verified | Underside chamfer only |
| 0.19 | Stacking lip: none | cq-gridfinity (no_lip) | `gf_box.py` | Verified | Flat rim, no profile |
| 0.20 | Configurable interior fillet | Our impl (kennetek spec) | `gf_box.py` | Verified | fillet_rad param, clamped to safe range |

---

### Phase 1B: Kennetek Feature Parity

All features in this phase trace to **kennetek/gridfinity-rebuilt-openscad** (MIT). All source references verified 2026-02-26.

#### 1B Holes (crush rib, chamfered, refined, printable top)

| # | Feature | Source File | Function/Module | Phase | Status | Acceptance |
|---|---------|-------------|-----------------|-------|--------|------------|
| 1B.1 | Crush rib magnet holes | `src/core/gridfinity-rebuilt-holes.scad` | `ribbed_cylinder()`, `block_base_hole()` with `crush_ribs=true` | 1B | Complete | 8 ribs (`GR_CRUSH_RIB_COUNT`), 5.9mm inner dia (`GR_CRUSH_RIB_INNER_D`). Impl: `gf_holes.crush_rib_magnet_hole()`. Tests: `test_holes.py` (4 tests). |
| 1B.2 | Chamfered magnet holes | `src/core/gridfinity-rebuilt-holes.scad` | `block_base_hole()` with `chamfer_holes=true` | 1B | Complete | 0.8mm chamfer (`GR_CHAMFER_EXTRA_R`), 45° angle (`GR_CHAMFER_ANGLE`). Impl: `gf_holes._chamfer_cone()` + `enhanced_magnet_hole(chamfer=True)`. Tests: `test_holes.py`. |
| 1B.3 | Refined magnet holes | `src/core/gridfinity-rebuilt-holes.scad` | `refined_hole()`, `block_base_hole()` with `refined_holes=true` | 1B | Complete | 5.86mm dia (`GR_REFINED_HOLE_D`), 1.9mm deep (`GR_REFINED_HOLE_H`). Impl: `gf_holes.refined_magnet_hole()`. Tests: `test_holes.py`. |
| 1B.4 | Printable hole top | `src/core/gridfinity-rebuilt-holes.scad` | `make_hole_printable()`, `block_base_hole()` with `printable_hole_top=true` | 1B | Complete | 0.4mm bridge disc at hole top. Impl: `gf_holes._printable_bridge()` + `enhanced_magnet_hole(printable_top=True)`. Tests: `test_holes.py`. |

#### 1B Bin Features (scoop, tabs, depth, cylindrical)

| # | Feature | Source File | Function/Module | Phase | Status | Acceptance |
|---|---------|-------------|-----------------|-------|--------|------------|
| 1B.5 | Scoop scaling (0-1) | `src/core/cutouts.scad` | `cut_compartment_auto()` with `scoop` param | 1B | Complete | `scoops` param accepts float 0.0-1.0 (bool backward compat: True→1.0, False→0.0). Scales `scoop_rad` by factor. 0=none, 1=full. Impl: `gf_box.py` render_scoops(). Tests: `test_bin_features.py` (5 tests). |
| 1B.6 | Tab positioning (6 styles) | `src/core/cutouts.scad` | `cut_compartment_auto()` with `style_tab` param | 1B | Complete | `label_style` param: "full"/"auto"/"left"/"center"/"right"/"none". Auto-sizes to min(42mm, compartment). Per-compartment positioning with dividers. Impl: `gf_box.py` render_labels() + _compute_tab_positions(). Tests: `test_bin_features.py` (8 tests). |
| 1B.7 | Custom compartment depth | `gridfinity-rebuilt-bins.scad` + `src/core/bin.scad` | `depth` param → `cgs(height=depth)`, `height_internal` → `fill_height` in `new_bin()` | 1B | Complete | `compartment_depth` (mm) raises floor; `height_internal` (mm) overrides internal height. Raised floor block unioned with shell. Fillet selectors adjusted for effective floor. Impl: `gf_box.py` _render_raised_floor() + _floor_raise property. Tests: `test_bin_features.py` (5 tests). |
| 1B.8 | Cylindrical compartments | `gridfinity-rebuilt-bins.scad` + `src/core/cutouts.scad` | `cut_chamfered_cylinder(cd/2, depth_real, c_chamfer)` | 1B | Complete | `cylindrical=True`, `cylinder_diam` (default 10mm, GR_CYL_DIAM), `cylinder_chamfer` (default 0.5mm, GR_CYL_CHAMFER). Solid shell with cylindrical cuts at compartment centers. Auto-clamps diameter to fit compartment. Impl: `gf_box.py` _render_cylindrical_cuts(). Tests: `test_bin_features.py` (6 tests). |

#### 1B Baseplate Features (skeleton, screw-together, fit-to-drawer)

| # | Feature | Source File | Function/Module | Phase | Status | Acceptance |
|---|---------|-------------|-----------------|-------|--------|------------|
| 1B.9 | Skeletonized baseplate | `gridfinity-rebuilt-baseplate.scad` + `src/core/standard.scad` | `style_plate=2`, constants `r_skel=2`, `h_skel=1` | 1B | Not Started | Material removed between receptacles, 2mm skeleton corner radius, 1mm minimum thickness. Additional height depends on magnet/screw options via `calculate_offset_skeletonized()` |
| 1B.10 | Screw-together baseplate | `gridfinity-rebuilt-baseplate.scad` | `style_plate=3` (skel interior) or `style_plate=4` (thin interior), `cutter_screw_together()` | 1B | Not Started | Horizontal M3 screw holes along edges for joining baseplates side-by-side. Params: `d_screw=3.35`, `d_screw_head=5`, `screw_spacing=0.5`, `n_screws=1-3`. Additional height: 6.75mm |
| 1B.11 | Fit-to-drawer baseplate | `gridfinity-rebuilt-baseplate.scad` | `[Fit to Drawer]` section: `distancex/y`, `fitx/fity` | 1B | Not Started | `distancex/y` = target drawer dimension (mm). `gridx/y=0` → auto-fill (floor division). `fitx/fity` (-1 to 1) controls padding alignment: -1=left, 0=center, 1=right. Padding filled with solid material |

#### 1B Grid Flexibility (non-integer, half-grid, height modes, Z-snap)

| # | Feature | Source File | Function/Module | Phase | Status | Acceptance |
|---|---------|-------------|-----------------|-------|--------|------------|
| 1B.12 | Non-integer grid sizes | `gridfinity-rebuilt-bins.scad` | `gridx/gridy` accept decimals (.1 step), `new_bin()` accepts any positive `grid_size` | 1B | Not Started | e.g., 2.5 x 3 grid units. `gridx/gridy` use `//.1` step notation in customizer. Internal grid calculations use the raw float values |
| 1B.13 | Half-grid (21mm) mode | `gridfinity-rebuilt-bins.scad` | `half_grid=true` → `GRID_DIMENSIONS_MM / 2`, forces `only_corners=true` | 1B | Not Started | 21mm grid increments (42/2). Half-grid bins always use only-corners base holes. `grid_dimensions` param in `new_bin()` |
| 1B.14 | Height mode selection (4 modes) | `src/core/gridfinity-rebuilt-utility.scad` | `height(z, gridz_define, enable_zsnap)`, `_gridz_functions[0-3]` | 1B | Not Started | Mode 0: 7mm units (z*7). Mode 1: internal mm (z + BASE_HEIGHT, excl base & lip). Mode 2: external mm (z as-is, excl lip). Mode 3: external mm (z - STACKING_LIP_HEIGHT, incl everything). Result always includes BASE_HEIGHT, excludes lip |
| 1B.15 | Z-snap (round to 7mm) | `src/core/gridfinity-rebuilt-utility.scad` | `z_snap(height_mm)` | 1B | Not Started | Rounds up to next 7mm multiple: `height_mm + 7 - height_mm % 7` if not already a multiple. Applied after gridz_define conversion, before `max(total_height, BASE_HEIGHT)` floor. `enable_zsnap` param (default false in bins entry) |

#### 1B Spiral Vase Bins

| # | Feature | Source File | Function/Module | Phase | Status | Acceptance |
|---|---------|-------------|-----------------|-------|--------|------------|
| 1B.16 | Spiral vase bin (shell) | `gridfinity-spiral-vase.scad` | `gridfinityVase()` (type=0) | 1B | Not Started | Single-wall (2×nozzle thick), no infill/top. Features: tabs (`style_tab` 0-6), scoop chamfer, finger-grab funnels, inset, pinch (lip strength), dividers with alternating-layer slicing. `style_base` controls base X-cutout (0:all, 1:corners, 2:edges, 3:auto, 4:none) |
| 1B.17 | Spiral vase bin (base) | `gridfinity-spiral-vase.scad` | `gridfinityBaseVase(wall_thickness, bottom_thickness)` (type=1) | 1B | Not Started | Separate base insert: outer shell + cross bracing ribs (4× circular pattern) + magnet hole blanks + X-pattern cutouts + "magic slice" (0.001mm cut for slicer compatibility). Bottom layers = `layer × max(bottom_layer, 1)` |

> **Note on 1B.16-17 (Spiral Vase):** These features are specifically designed for FDM spiral/vase mode printing. Since this project generates STEP files, the geometry must be constructed as single-wall solids that a downstream slicer would print correctly in vase mode. The "magic slice" and "alternating divider layers" are slicer tricks that may need adaptation for B-Rep geometry.

---

### Phase 1C: Extended Feature Set

Features in this phase use **ostat/gridfinity_extended_openscad** (GPL) as **dimensional/behavioral spec reference ONLY**. All implementations are independent CadQuery code.

| # | Feature | Spec Reference | Spec Detail | Phase | Status | Acceptance |
|---|---------|---------------|-------------|-------|--------|------------|
| 1C.1 | Wall pattern: grid | ostat `modules/gridfinity_cup_modules.scad` [needs verify] | Rectangular grid cutouts | 1C | Not Started | Configurable grid size, wall selection |
| 1C.2 | Wall pattern: hex | ostat `modules/gridfinity_cup_modules.scad` [needs verify] | Hexagonal cutouts | 1C | Not Started | Configurable hex size, wall selection |
| 1C.3 | Wall pattern: brick | ostat [needs verify] | Offset brick pattern | 1C | Not Started | Alternating rows |
| 1C.4 | Wall pattern: slat | ostat [needs verify] | Horizontal slot cutouts | 1C | Not Started | Configurable slat width/spacing |
| 1C.5 | Per-wall pattern control | ostat [needs verify] | Different pattern per wall | 1C | Not Started | front/back/left/right independent |
| 1C.6 | Pattern fill modes | ostat [needs verify] | Crop/fill/none per wall | 1C | Not Started | Pattern alignment options |
| 1C.7 | Minimum lip (4th style) | ostat [needs verify] | Thinnest possible stacking lip | 1C | Not Started | Functional stacking, minimal material |
| 1C.8 | Finger slide (rounded) | ostat [needs verify] | Rounded cutout in front wall | 1C | Not Started | Semi-circular, configurable size |
| 1C.9 | Finger slide (chamfered) | ostat [needs verify] | Chamfered cutout in front wall | 1C | Not Started | Angled cut, configurable |
| 1C.10 | Tapered bin corners | ostat [needs verify] | Interior corner chamfers | 1C | Not Started | Configurable taper angle |
| 1C.11 | Wall cutouts | ostat [needs verify] | Rectangular openings in walls | 1C | Not Started | Configurable position/size |
| 1C.12 | Irregular subdivisions | ostat [needs verify] | Non-uniform compartment sizes | 1C | Not Started | Specify individual compartment widths |
| 1C.13 | Removable divider slots | ostat [needs verify] | Grooves for insert dividers | 1C | Not Started | Slot width/depth configurable |
| 1C.14 | Split bins | ostat [needs verify] | Bin split into two pieces | 1C | Not Started | Cut plane configurable |
| 1C.15 | Bottom text embossing | ostat [needs verify] | Raised text on bin bottom | 1C | Not Started | 2 lines, font selection, depth |
| 1C.16 | Bottom text debossing | ostat [needs verify] | Recessed text on bin bottom | 1C | Not Started | 2 lines, font selection, depth |
| 1C.17 | Floor pattern: grid | ostat [needs verify] | Grid cutouts in floor | 1C | Not Started | Same system as wall patterns |
| 1C.18 | Floor pattern: hex | ostat [needs verify] | Hex cutouts in floor | 1C | Not Started | Same system as wall patterns |

---

### Phase 1D: Accessories

| # | Feature | Source Project | Source File | Phase | Status | Acceptance |
|---|---------|--------------|-------------|-------|--------|------------|
| 1D.1 | Anylid click-lock lid | rngcntr/anylid | [needs verify — license TBD] | 1D | Not Started | Click-lock mechanism, 1U height, stackable |
| 1D.2 | Anylid baseplate-on-top | rngcntr/anylid | [needs verify] | 1D | Not Started | Baseplate receptacles on lid top |
| 1D.3 | Cullenect click-in label | CullenJWebb/CullenectLabels (MIT) | [needs verify] | 1D | Not Started | Snap-in label, swappable |
| 1D.4 | Label negative volume | CullenJWebb/CullenectLabels (MIT) | [needs verify] | 1D | Not Started | Boolean subtraction volume for any bin |
| 1D.5 | Item holder: battery | ostat (spec ref) | [needs verify] | 1D | Not Started | Parametric slots for standard battery sizes |
| 1D.6 | Item holder: hex bit | ostat (spec ref) | [needs verify] | 1D | Not Started | Hex socket array |
| 1D.7 | Item holder: card | ostat (spec ref) | [needs verify] | 1D | Not Started | Card-width slots |
| 1D.8 | Sliding lid | ostat (spec ref) | [needs verify] | 1D | Not Started | Rail channels on bin walls |
| 1D.9 | Drawer chest frame | ostat (spec ref) | [needs verify] | 1D | Not Started | Frame that holds drawer units |
| 1D.10 | Drawer sliding unit | ostat (spec ref) | [needs verify] | 1D | Not Started | Bin-sized drawer with rails |
| 1D.11 | Catch-all tray | ostat (spec ref) | [needs verify] | 1D | Not Started | Open tray, no compartments |
| 1D.12 | Vertical divider tray | ostat (spec ref) | [needs verify] | 1D | Not Started | Tray with vertical dividers |

---

### Phase 1E: Rugged Box Expansion

| # | Feature | Source Project | Source File | Phase | Status | Acceptance |
|---|---------|--------------|-------------|-------|--------|------------|
| 1E.1 | smkent clip latch | smkent/monoscad (CC BY-SA 4.0) | [needs verify] | 1E | Not Started | Clip-style closure mechanism |
| 1E.2 | smkent draw latch | smkent/monoscad | [needs verify] | 1E | Not Started | Draw-latch closure |
| 1E.3 | smkent lip seal (4 types) | smkent/monoscad | [needs verify] | 1E | Not Started | Weatherproofing lip options |
| 1E.4 | smkent base styles (4) | smkent/monoscad | [needs verify] | 1E | Not Started | Different bottom configurations |
| 1E.5 | smkent stacking latches | smkent/monoscad | [needs verify] | 1E | Not Started | External stacking mechanism |
| 1E.6 | smkent third hinge | smkent/monoscad | [needs verify] | 1E | Not Started | Centre hinge for wide boxes |
| 1E.7 | smkent hinge end stops | smkent/monoscad | [needs verify] | 1E | Not Started | Lid opening angle limit |
| 1E.8 | smkent parametric walls | smkent/monoscad | [needs verify] | 1E | Not Started | Configurable wall thickness |

---

### Phase 1F: GridFlock Segmented Baseplates

| # | Feature | Source Project | Source File | Phase | Status | Acceptance |
|---|---------|--------------|-------------|-------|--------|------------|
| 1F.1 | Baseplate segment | yawkat/gridflock (MIT) | [needs verify] | 1F | Not Started | Individual printable segment |
| 1F.2 | Puzzle connector (intersection) | yawkat/gridflock | [needs verify] | 1F | Not Started | T/cross connectors at grid intersections |
| 1F.3 | Puzzle connector (edge) | yawkat/gridflock | [needs verify] | 1F | Not Started | Edge connectors between segments |
| 1F.4 | Filler: none | yawkat/gridflock | [needs verify] | 1F | Not Started | No gap filling |
| 1F.5 | Filler: integer-fraction | yawkat/gridflock | [needs verify] | 1F | Not Started | Fill with integer-fraction pieces |
| 1F.6 | Filler: dynamic | yawkat/gridflock | [needs verify] | 1F | Not Started | Computed optimal fill |
| 1F.7 | ClickGroove anti-creep latch | yawkat/gridflock | [needs verify] | 1F | Not Started | Interlocking mechanism between segments |

---

## Phase Gate Validation Checklist

Before starting any phase, verify ALL of the following:

- [ ] All features in the phase have traced upstream sources (no `[needs verify]` remaining for that phase)
- [ ] Acceptance criteria are specific and testable
- [ ] No feature requires inventing new geometry not in upstream sources
- [ ] Upstream source files have been read/analyzed (not just assumed)
- [ ] Existing tests still pass (28 baseline)
- [ ] Previous phase is fully Verified (not just Complete)

### Phase 1B Gate Status (2026-02-26)

- [x] All features traced to upstream sources — **17/17 verified** against kennetek source
- [x] Acceptance criteria are specific and testable — updated with exact constants, params, dimensions
- [x] No invented geometry — all features exist in kennetek/gridfinity-rebuilt-openscad
- [x] Upstream source files read/analyzed — 7 files: `standard.scad`, `base.scad`, `bin.scad`, `cutouts.scad`, `gridfinity-rebuilt-holes.scad`, `gridfinity-rebuilt-utility.scad`, `gridfinity-spiral-vase.scad`
- [x] Existing tests still pass (28 baseline) — **28/28 passed** (347.94s, 2026-02-26)
- [x] Previous phase (1A) fully Verified — all 20 features in "Already Implemented" are Verified

---

## Revision History

| Date | Change | Author |
|------|--------|--------|
| 2026-02-26 | Initial feature spec with traceability matrix | Jason + Claude |
| 2026-02-26 | Phase 1B: All 17 features verified against kennetek source. Resolved all `[needs verify]` markers. Updated acceptance criteria with exact constants, params, and dimensions from 7 source files. Added spiral vase adaptation note. | Jason + Claude |
