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
| 1B.1 | Crush rib magnet holes | `src/core/gridfinity-rebuilt-holes.scad` | `ribbed_cylinder()`, `block_base_hole()` with `crush_ribs=true` | 1B | Verified | 8 ribs (`GR_CRUSH_RIB_COUNT`), 5.9mm inner dia (`GR_CRUSH_RIB_INNER_D`). Baseplates: `gf_baseplate.py` via `gf_holes.cut_enhanced_holes()`. Bins: `gf_box.py` render_holes() enhanced path. Tests: `test_holes.py` (baseplates + bins). |
| 1B.2 | Chamfered magnet holes | `src/core/gridfinity-rebuilt-holes.scad` | `block_base_hole()` with `chamfer_holes=true` | 1B | Verified | 0.8mm chamfer (`GR_CHAMFER_EXTRA_R`), 45° angle (`GR_CHAMFER_ANGLE`). Baseplates + Bins via `gf_holes.enhanced_magnet_hole(chamfer=True)`. Tests: `test_holes.py`. |
| 1B.3 | Refined magnet holes | `src/core/gridfinity-rebuilt-holes.scad` | `refined_hole()`, `block_base_hole()` with `refined_holes=true` | 1B | Verified | 5.86mm dia (`GR_REFINED_HOLE_D`), 1.9mm deep (`GR_REFINED_HOLE_H`). Baseplates + Bins via `gf_holes.enhanced_magnet_hole(refined=True)`. Tests: `test_holes.py`. |
| 1B.4 | Printable hole top | `src/core/gridfinity-rebuilt-holes.scad` | `make_hole_printable()`, `block_base_hole()` with `printable_hole_top=true` | 1B | Verified | 0.4mm bridge disc at hole top. Baseplates + Bins via `gf_holes.enhanced_magnet_hole(printable_top=True)`. Tests: `test_holes.py`. |

#### 1B Bin Features (scoop, tabs, depth, cylindrical)

| # | Feature | Source File | Function/Module | Phase | Status | Acceptance |
|---|---------|-------------|-----------------|-------|--------|------------|
| 1B.5 | Scoop scaling (0-1) | `src/core/cutouts.scad` | `cut_compartment_auto()` with `scoop` param | 1B | Verified | `scoops` param accepts float 0.0-1.0 (bool backward compat: True→1.0, False→0.0). Scales `scoop_rad` by factor. 0=none, 1=full. Impl: `gf_box.py` render_scoops(). Tests: `test_bin_features.py` (5 tests). |
| 1B.6 | Tab positioning (6 styles) | `src/core/cutouts.scad` | `cut_compartment_auto()` with `style_tab` param | 1B | Verified | `label_style` param: "full"/"auto"/"left"/"center"/"right"/"none". Auto-sizes to min(42mm, compartment). Per-compartment positioning with dividers. Impl: `gf_box.py` render_labels() + _compute_tab_positions(). Tests: `test_bin_features.py` (8 tests). |
| 1B.7 | Custom compartment depth | `gridfinity-rebuilt-bins.scad` + `src/core/bin.scad` | `depth` param → `cgs(height=depth)`, `height_internal` → `fill_height` in `new_bin()` | 1B | Verified | `compartment_depth` (mm) raises floor; `height_internal` (mm) overrides internal height. Raised floor block unioned with shell. Fillet selectors adjusted for effective floor. Impl: `gf_box.py` _render_raised_floor() + _floor_raise property. Tests: `test_bin_features.py` (5 tests). |
| 1B.8 | Cylindrical compartments | `gridfinity-rebuilt-bins.scad` + `src/core/cutouts.scad` | `cut_chamfered_cylinder(cd/2, depth_real, c_chamfer)` | 1B | Verified | `cylindrical=True`, `cylinder_diam` (default 10mm, GR_CYL_DIAM), `cylinder_chamfer` (default 0.5mm, GR_CYL_CHAMFER). Solid shell with cylindrical cuts at compartment centers. Auto-clamps diameter to fit compartment. Impl: `gf_box.py` _render_cylindrical_cuts(). Tests: `test_bin_features.py` (6 tests). |

#### 1B Baseplate Features (skeleton, screw-together, fit-to-drawer)

| # | Feature | Source File | Function/Module | Phase | Status | Acceptance |
|---|---------|-------------|-----------------|-------|--------|------------|
| 1B.9 | Skeletonized baseplate | `gridfinity-rebuilt-baseplate.scad` + `src/core/standard.scad` | `style_plate=2`, constants `r_skel=2`, `h_skel=1` | 1B | Verified | `skeleton=True` param. 4 corner pocket cutouts per cell (12.4mm sq, 2mm fillet) leaving 11.5mm cross ribs. ext_depth auto: 4.35mm (plain), 6.75mm (magnets), 6.25mm (refined). Skeleton before holes in pipeline, overrides weighted. Impl: `gf_baseplate.py` `_render_skeleton_cutouts()`. Tests: `test_skeleton_baseplate.py` (15 tests). |
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

Features in this phase use **ostat/gridfinity_extended_openscad** (GPL) as **dimensional/behavioral spec reference ONLY**. All implementations are independent CadQuery code. All source references verified 2026-02-27. See `documents/UPSTREAM-REFERENCE.md` for detailed parameters and constants.

| # | Feature | Source File | Function/Module | Phase | Status | Acceptance |
|---|---------|-------------|-----------------|-------|--------|------------|
| 1C.1 | Wall pattern: grid | `modules/module_patterns.scad` + `modules/module_item_holder.scad` | `cutout_pattern()` → `GridItemHolder(hexGrid=false)` | 1C | Not Started | Configurable `cellSize` (default [10,10]mm), `strength` (2mm), `circleFn` (4/6/8/64), `holeRadius` (0.5mm), `patternBorder`, `patternDepth` |
| 1C.2 | Wall pattern: hex | `modules/module_patterns.scad` + `modules/module_item_holder.scad` | `cutout_pattern()` → `GridItemHolder(hexGrid=true)` | 1C | Not Started | Same params as 1C.1. Hex is ostat's default wall pattern style |
| 1C.3 | Wall pattern: brick | `modules/module_pattern_brick.scad` | `brick_pattern()` via `cutout_pattern()` | 1C | Not Started | Two sub-styles: `"brick"` (aligned) and `"brickoffset"` (staggered). `cell_size` [15,5]mm, `spacing` 1mm, `corner_radius` 3mm, `center_weight` |
| 1C.4 | Wall pattern: slat | `modules/module_pattern_slat.scad` | `slat_pattern()` via `cutout_pattern()` | 1C | Not Started | Vertical strips (not horizontal). `slat_width`, `spacing`, `slat_chamfer` supports [top,bottom] |
| 1C.5 | Per-wall pattern enable/disable | `modules/module_patterns.scad` | `get_wallpattern_positions()` with `wallpattern_walls` | 1C | Not Started | Same pattern on/off per wall: `wallpattern_walls=[f,b,l,r]` (each 0/1). Also `wallpattern_dividers_enabled` ("disabled"/"horizontal"/"vertical"/"both") |
| 1C.6 | Pattern fill modes (9) | `modules/module_patterns.scad` | `PatternSettings()` | 1C | Not Started | 9 modes: none, space, crop, crophorizontal, cropvertical, spacehorizontal, spacevertical, crophorizontal_spacevertical, cropvertical_spacehorizontal |
| 1C.7 | Minimum lip | `modules/module_lip.scad` | `cupLip()` with `lipStyle="minimum"` | 1C | Not Started | `lipSupportThickness=0`, removes entire lip cavity. Thinnest possible rim |
| 1C.7b | Reduced double lip | `modules/module_lip.scad` | `cupLip()` with `lipStyle="reduced_double"` | 1C | Not Started | Second lip below first, offset by `lipHeight + labelCornerRadius`. Double-stack reduced lip |
| 1C.8 | Finger slide (rounded) | `modules/module_fingerslide.scad` + `modules/utility/module_utility.scad` | `FingerSlide()` → `roundedCorner()` | 1C | Not Started | Quarter-cylinder cutout (90°, not semi-circular). `fingerslide_radius` default -3 (proportional: `min(cup_h, cup_size)/abs(val)`). `fingerslide_walls` [f,b,l,r], `fingerslide_lip_aligned` |
| 1C.9 | Finger slide (chamfered) | `modules/module_fingerslide.scad` + `modules/utility/module_utility.scad` | `FingerSlide()` → `chamferedCorner()` | 1C | Not Started | Angled flat cut. Same params as 1C.8. `chamferLength`, `cornerRadius`, `angled_extension` |
| 1C.10 | Tapered bin corners | `modules/module_gridfinity_cup.scad` (line ~995) | `bin_cutouts()` with `tapered_corner` | 1C | Not Started | Back-wall-top corner cutout (not interior corners). `tapered_corner`: "none"/"rounded"/"chamfered". `tapered_corner_size` default 10mm (-1=full, -2=half). `tapered_setback` default -1 (=corner_radius) |
| 1C.11 | Wall cutouts | `modules/utility/wallcutout.scad` + `modules/module_gridfinity_cup.scad` | `WallCutout()`, `WallCutoutSettings()`, `calculateWallCutouts()` | 1C | Not Started | Trapezoidal profile, rounded corners. `type`: enabled/wallsonly/frontonly/etc. `angle` 70°, `corner_radius` 5mm. Separate vertical/horizontal settings. Multiple positions per wall |
| 1C.12 | Irregular subdivisions | `modules/module_bin_chambers.scad` | `ChamberSettings()` + `calculateSeparators()` | 1C | Not Started | `vertical/horizontal_irregular_subdivisions` (bool). Separator config: pipe-separated positions with per-separator overrides (position,bend_separation,bend_angle,cut_depth,cut_width,wall_thickness) |
| 1C.13 | Divider wall notches | `modules/module_bin_chambers.scad` + `modules/utility/module_utility.scad` | `bentWall()` with `wall_cutout_depth` | 1C | Not Started | U-shaped notches from top of divider walls (not grooves in bin walls). `separator_cut_depth` (0=disabled), `wall_cutout_width` (0=auto=length/2). Per-separator override via irregular config |
| 1C.14 | Extendable (split) bins | `modules/module_gridfinity_Extendable.scad` | `ExtendableSettings()`, `cut_bins_for_extension()`, `extension_tabs()` | 1C | Not Started | Called "Extendable" in ostat. Cut bin in two with snap tabs. `extension_x/y_enabled` ("disabled"/"front"/"back"), `extension_x/y_position` (0.0-1.0), `extension_tab_size` [h,w,t,style] |
| 1C.15 | ~~Bottom text embossing~~ | — | — | — | REMOVED | Does not exist in ostat. Only debossing available (see 1C.16) |
| 1C.16 | Bottom text debossing | `modules/module_gridfinity_cup_base_text.scad` | `cup_base_text()` | 1C | Not Started | Recessed text on bin underside. `text_1` (auto bin size), `text_2` (custom), `text_depth` 0.3mm, `text_size` (0=auto-fit 30mm), fonts: Aldo/B612/Open Sans/Ubuntu |
| 1C.17 | Floor pattern: grid | `modules/module_gridfinity_cup.scad` + `modules/module_patterns.scad` | `bin_floor_pattern()` → `cutout_pattern()` | 1C | Not Started | All 8 pattern styles available for floors. `floorpattern_border` min 5mm. Respects divider/magnet positions. Default style = hexgrid, default enabled = false |
| 1C.18 | Floor pattern: hex | Same as 1C.17 | `bin_floor_pattern()` with `hexgrid` | 1C | Not Started | Default floor pattern style. Same system as wall patterns |

---

### Phase 1D: Accessories

All source references verified 2026-02-27. See `documents/UPSTREAM-REFERENCE.md` for detailed parameters and constants.

| # | Feature | Source Project | Source File | Function/Module | Phase | Status | Acceptance |
|---|---------|--------------|-------------|-----------------|-------|--------|------------|
| 1D.1 | Anylid click-lock lid | rngcntr/anylid (**NO GitHub repo** — MakerWorld #1059434 only, **license TBD**) | No source code available | N/A | 1D | Not Started | Click-lock mechanism, 1U height, stackable. Rails in X or Y. Label accommodation. Optional magnets. **Blocked: license must be resolved before implementation** |
| 1D.2 | Anylid baseplate-on-top | rngcntr/anylid (same as 1D.1) | No source code available | N/A | 1D | Not Started | Full baseplate receptacles on lid top. Each lid = +1U height. **Blocked: license** |
| 1D.3 | Cullenect click-in label | CullenJWebb/**Cullenect-Labels** (MIT) | `OpenSCAD/Cullenect.scad` | `cullenect_base_v1/v2()`, `cullenect_socket()`, `cullenect_label_generate()` | 1D | Not Started | Snap-in label. Width=(42×units)-6mm, height=11mm, depth=1.2mm, latch inset=0.2mm, latch depth=0.6mm. Embossed/debossed text, 18+ hardware icons |
| 1D.4 | Label negative volume | CullenJWebb/**Cullenect-Labels** (MIT) | `OpenSCAD/Cullenect.scad` + `Cullenect Negative Volume.stl` | `cullenect_socket_negative()`, `cullenect_vertical_socket_negative()` | 1D | Not Started | Boolean subtraction volume. Socket XY offset=0.3mm, rib=0.2mm XY/0.4mm depth. Generate natively in CadQuery |
| 1D.5 | Item holder: battery | ostat (spec ref, GPL) | `gridfinity_item_holder.scad` + `modules/module_item_holder.scad` + `modules/module_item_holder_data.scad` | `LookupKnownBattery()`, `GridItemHolder()` | 1D | Not Started | AAA(10.5mm), AA(14.5mm), 9V(17.5×26.5mm), 18650(18mm), C, D, coin cells. `hole_clearance` 0.25mm, grid_style square/hex/auto |
| 1D.6 | Item holder: hex bit | ostat (spec ref, GPL) | Same as 1D.5 | `LookupKnownTool()`, `GridItemHolder(circleFn=6)` | 1D | Not Started | 1/4" hex (6.35mm), 3/8" hex (9.52mm), router bits. circleFn=6 for hex holes |
| 1D.7 | Item holder: card | ostat (spec ref, GPL) | Same as 1D.5 | `LookupKnownCard()`, `multiCard()` | 1D | Not Started | SD(24×2.1mm), MicroSD(11×0.7mm), CF(43×3.3mm), game cartridges. Multi-card: comma-separated, compact nesting 0-1 |
| 1D.8 | Sliding lid | ostat (spec ref, GPL) | `gridfinity_sliding_lid.scad` + `modules/module_gridfinity_sliding_lid.scad` | `SlidingLid()`, `SlidingLidCavity()`, `SlidingLidSettings()` | 1D | Not Started | `lidThickness` 1.6mm, `clearance` 0.1mm, `lip_height` 3.75mm. Pull styles: disabled/lip/finger. Nub 0.5mm. Optional text engraving |
| 1D.9 | Drawer chest frame | ostat (spec ref, GPL) | `gridfinity_drawers.scad` | `chest()`, `chestCutouts()`, `gridfinity_drawer()` | 1D | Not Started | `wall_thickness` 2mm, `clearance` 0.25mm. Optional top/bottom grids. Supportless feet. Magnet 6.5mm×2.4mm |
| 1D.10 | Drawer sliding unit | ostat (spec ref, GPL) | `gridfinity_drawers.scad` | `drawer()`, `drawers()`, `drawerPull()` | 1D | Not Started | `wall_thickness` 2mm, configurable clearance [x,y,z]. Base: default/grid. Custom per-drawer sizing. Handle configurable |
| 1D.11 | Catch-all tray | ostat (spec ref, GPL) | `gridfinity_tray.scad` | `tray()`, `gridfinity_tray()` | 1D | Not Started | `corner_radius` 2mm, `spacing` 2mm. 1×1 compartments = open tray. Custom layout string: "xpos,ypos,xsize,ysize,radius,depth\|...". Full cup integration |
| 1D.12 | Vertical divider | ostat (spec ref, GPL) | `gridfinity_vertical_divider.scad` | `Gridfinity_Divider()`, `PatternedDivider()`, `Divider()` | 1D | Not Started | Upstream name: "Gridfinity Divider" (bin with tall partitions, not shallow tray). `dividerCount` 4, `dividerHeight` 50mm, `dividerWidth` 3mm, angled tops (65°), base 10mm. Wall patterns on dividers |

---

### Phase 1E: Rugged Box Expansion

All features from **smkent/monoscad** (CC BY-SA 4.0). Primary library: `rugged-box/rugged-box-library.scad` (~2,182 lines). Gridfinity wrapper: `gridfinity/rugged-box/rugged-box-gridfinity.scad` (~368 lines). All source references verified 2026-02-27. See `documents/UPSTREAM-REFERENCE.md` for detailed parameters and constants.

| # | Feature | Source File | Function/Module | Phase | Status | Acceptance |
|---|---------|-------------|-----------------|-------|--------|------------|
| 1E.1 | Clip latch | `rugged-box/rugged-box-library.scad` | `_clip_latch_shape()` (line ~1629), `_clip_latch_part()`, `_latch()` dispatcher, `rbox_latch()` | 1E | Not Started | `latch_type="clip"`. Single-piece: hinge eyelet + body + catch w/ flex slot. M3 screws, `latch_edge_radius` 0.8mm, `latch_base_size` 4.5mm. Width: 22mm (generic) / 28mm (GF) |
| 1E.2 | Draw latch | `rugged-box/rugged-box-library.scad` | `_draw_latch_handle()` (~1853), `_draw_latch_catch()` (~1990), `_draw_latch_part()` (~2015) | 1E | Not Started | `latch_type="draw"`. Two-piece (handle+catch via pin joint). Body angle 25°, grip angle 45°, thickness 2.25mm, handle length 14.625mm. Segmented interlocking, sep=0.4mm |
| 1E.3 | Lip seal (4 types) | `rugged-box/rugged-box-library.scad` | `_box_seal_shape()` (~991), `_box_seal()`, `_box_add_seal()` | 1E | Not Started | `lip_seal_type`: none/wedge/square/filament-1.75mm. Wedge+square: `seal_thickness = total_lip_thickness/3`, protrude top + groove bottom. Filament: 1.75mm circle, groove both halves |
| 1E.4 | Base styles (4, GF-specific) | `gridfinity/rugged-box/rugged-box-gridfinity.scad` | `gridfinity_base_plate_style()` (~145), `gridfinity_base_plate_magnets_enabled()` | 1E | Not Started | minimal (no magnets, thin), thick (no magnets, full), enabled (magnets, skeletonized), enabled_full (magnets, full). Uses kennetek `gridfinityBaseplate()`. Stackable offsets: 3.4 / -0.8 / -0.6mm |
| 1E.5 | Stacking latches | `rugged-box/rugged-box-library.scad` | `_stacking_latch_shape()` (~2079), `_stacking_latch_part()`, `_box_stacking_latch_ribs()` | 1E | Not Started | Side-mounted. `catch_offset` -10mm, `grip_length` 8mm, `screw_separation` 20mm. Requires box height >40mm. Stacking gap 1.6mm (GF stackable) |
| 1E.6 | Third hinge | `rugged-box/rugged-box-library.scad` | `rbox_size_adjustments()` (~186), `_box_attachment_placement(hinge=true)` (~1162) | 1E | Not Started | Center hinge when `inner_width >= third_hinge_width`. GF: activates at 5U wide (210mm). Adds 1 screw to BOM |
| 1E.7 | Hinge end stops | `rugged-box/rugged-box-library.scad` | `_box_hinge_rib_bottom_end_stop()` (~1400), in `_box_hinge_ribs()` | 1E | Not Started | Bottom box part only. Physical rotation limiter. Width = latch_width. Positioned 2mm below box top |
| 1E.8 | Parametric walls | `rugged-box/rugged-box-library.scad` | `rbox_size_adjustments()` (~186) | 1E | Not Started | 7 params: wall_thickness (2.4/3.0mm), lip_thickness (2.0/3.0mm), rib_width (4/6mm), latch_width (22/28mm), latch_screw_sep (20/16mm), latch_amount_on_top, size_tolerance (0.05/0.20mm). Generic/GF defaults differ |

---

### Phase 1F: GridFlock Segmented Baseplates

All features from **yawkat/gridflock** (MIT + CC-BY 4.0 dual license). Single-file architecture: `gridflock.scad` (~1,260 lines). Supporting: `clickgroove-base.scad`, `puzzle.svg`. All source references verified 2026-02-27. See `documents/UPSTREAM-REFERENCE.md` for detailed parameters and constants.

| # | Feature | Source File | Function/Module | Phase | Status | Acceptance |
|---|---------|-------------|-----------------|-------|--------|------------|
| 1F.1 | Baseplate segment | `gridflock.scad` | `segment()` (~848), `main()` (~1133), `compute_segment_size()`, `cell()` | 1F | Not Started | Individual printable piece. Auto-splits `plate_size` to fit `bed_size`. `plate_size` [371,254]mm, `bed_size` [250,220]mm, `plate_corner_radius` 4mm, `alignment` [0.5,0.5]. Ideal + incremental + staggered algorithms. `_profile_height` 4.65mm |
| 1F.2 | Puzzle connector (intersection) | `gridflock.scad` + `puzzle.svg` | `puzzle_male()` / `puzzle_female()` (~400-430), `segment_intersection_connectors()` (~616) | 1F | Not Started | SVG-defined shape (4 paths: male/female × tight/loose). Weighted blend by `intersection_puzzle_fit` (0-1, default 1). Male on N/E edges, female on S/W. Scale 1/128×4 |
| 1F.3 | Puzzle connector (edge) | `gridflock.scad` | `edge_puzzle()` (~739), `segment_edge_connectors()` (~696), `round_bar_x()` | 1F | Not Started | `edge_puzzle_dim` [10,2.5]mm, bridge [3,1.2]mm, `gap` 0.15mm. `count` per edge, `height_female` 2.25mm, `male_delta` 0.25mm. Optional magnet border (2.5mm). Male N/E, female S/W |
| 1F.4 | Filler: none | `gridflock.scad` | `compute_global_trace()` (~1128), `_FILLER_NONE=0` | 1F | Not Started | Only full-size cells. Remaining space = padding via `alignment` param |
| 1F.5 | Filler: integer-fraction | `gridflock.scad` | `compute_global_trace_fraction()` (~1116), `_FILLER_INTEGER=1` | 1F | Not Started | Default mode. `filler_fraction` [2,2] (denominator: 2=half, 3=third). Splits into whole + fractional cells |
| 1F.6 | Filler: dynamic | `gridflock.scad` | `compute_global_trace_dynamic()` (~1122), `_FILLER_DYNAMIC=2` | 1F | Not Started | `filler_minimum_size` [15,15]mm. If remainder < minimum → expand last cell. Otherwise → dynamic-sized filler. Prevents tiny cells |
| 1F.7 | ClickGroove anti-creep latch | `gridflock.scad` (lines ~315-332) + `clickgroove-base.scad` | `cell()` with `click_style==_CLICK2` | 1F | Not Started | **Bin-to-baseplate** mechanism (NOT segment-to-segment). Two styles: Arc (_CLICK1, logistic curve) and ClickGroove (_CLICK2, tab-in-groove). `gap_length` 25mm, `tab_length` 10mm, `strength` 1.4mm, `depth` 0.9mm. Bin groove: 1.5mm height, 0.75mm depth, all 4 sides |

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

### Phase 1B Exit Gate Checklist

Before declaring Phase 1B complete, verify ALL of the following:

- [x] 1B.1-1B.4 (Enhanced holes): Verified — work on both baseplates AND bins via shared `gf_holes.py`
- [x] 1B.5-1B.8 (Bin features): Verified — scoop scaling, tab positioning, custom depth, cylindrical
- [x] 1B.9 (Skeletonized baseplate): Verified — 16 tests, watertight validated
- [ ] 1B.10-1B.11 (Baseplate features): Not Started — screw-together, fit-to-drawer
- [ ] 1B.12-1B.15 (Grid flexibility): Not Started — non-integer, half-grid, height modes, Z-snap
- [ ] 1B.16-1B.17 (Spiral vase): Not Started — shell + base insert
- [ ] All 17 features status = Verified (with passing tests and isValid checks)
- [ ] All tests pass (0 failures; xfail quarantined only; skip justified only)
- [ ] All render tests include `isValid()` watertight check
- [ ] No invented geometry — every feature traces to FEATURE-SPEC.md row
- [ ] PRODUCTS.md and PROJECT-MEMORY.md reflect current status

**Current status (2026-02-28):** 9/17 features Verified (1B.1-1B.9). 8 features Not Started (1B.10-1B.17). Phase 1B is **IN PROGRESS**.

---

## Revision History

| Date | Change | Author |
|------|--------|--------|
| 2026-02-26 | Initial feature spec with traceability matrix | Jason + Claude |
| 2026-02-26 | Phase 1B: All 17 features verified against kennetek source. Resolved all `[needs verify]` markers. Updated acceptance criteria with exact constants, params, and dimensions from 7 source files. Added spiral vase adaptation note. | Jason + Claude |
| 2026-02-27 | Phases 1C–1F: All 45 features verified against upstream repos (ostat, smkent, yawkat, CullenJWebb, rngcntr). 1C.15 (embossing) removed — does not exist in ostat. 1C.7b (reduced_double lip) added. 1F.7 description corrected (bin-to-baseplate, not segment-to-segment). anylid license flagged as TBD/blocked. Created `documents/UPSTREAM-REFERENCE.md` with detailed parameters, constants, and dimensions. | Jason + Claude |
| 2026-02-28 | Remediation: 1B.1-1B.9 status updated to Verified. Enhanced holes now work on bins (via gf_holes boolean cut path). Added Phase 1B Exit Gate checklist. All render tests include isValid() watertight checks. Rugged box lid quarantined as xfail (pre-existing non-watertight geometry). | Jason + Claude |
