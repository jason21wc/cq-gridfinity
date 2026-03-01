# Upstream Implementation Reference

**Project:** Gridfinity STEP Generator
**Purpose:** Detailed parameters, constants, dimensions, and geometry descriptions verified against upstream source code. Use this as the primary implementation reference — avoids re-fetching from upstream repos.
**Last Verified:** 2026-02-27

> **Usage:** When implementing a feature, find it by ID (e.g., 1C.3) in this document.
> Each entry has the exact source file, function, parameters with defaults, and geometry notes.
> For traceability and status tracking, see `documents/FEATURE-SPEC.md`.

---

## Table of Contents

- [Phase 1C: Extended Feature Set (ostat)](#phase-1c-extended-feature-set-ostat)
- [Phase 1D: Accessories (mixed sources)](#phase-1d-accessories-mixed-sources)
- [Phase 1E: Rugged Box Expansion (smkent)](#phase-1e-rugged-box-expansion-smkent)
- [Phase 1F: GridFlock Segmented Baseplates (yawkat)](#phase-1f-gridflock-segmented-baseplates-yawkat)

---

## Phase 1B: Kennetek Feature Parity (Late Additions)

### 1B.10: Screw-Together Baseplate

**Source:** `kennetek/gridfinity-rebuilt-openscad` (MIT)
**File:** `gridfinity-rebuilt-baseplate.scad` → `cutter_screw_together()`
**Styles:** `style_plate=3` (skeleton interior + screw holes), `style_plate=4` (thin interior + screw holes)

**Parameters (verified 2026-02-28):**
| Parameter | Value | Notes |
|-----------|-------|-------|
| `d_screw` | 3.35 mm | Screw hole diameter (M3 clearance) |
| `d_screw_head` | 5.0 mm | Used only for multi-screw spacing calc |
| `screw_spacing` | 0.5 mm | Gap between adjacent holes |
| `n_screws` | 1 (range 1-3) | Screws per grid unit per edge |
| Additional height | 6.75 mm | Always added for screw-together styles |
| Hole Z-center | `additional_height / 2` = 3.375 mm | Centered in extra-height section |
| Hole length | `l_grid / 2` = 21.0 mm | Extends inward from edge |
| Hole orientation | Horizontal | Perpendicular to the edge they serve |
| Edges with holes | All 4 | 1 hole group per grid unit per edge |
| Multi-screw spacing | 5.5 mm center-to-center | `d_screw_head + screw_spacing` |

**Geometry:** Each edge gets horizontal cylindrical holes at every grid unit. Each hole is dia 3.35mm, length 21mm, centered at the edge, Z-centered in the additional-height section. Multi-screw mode distributes holes at 5.5mm c-c perpendicular to the hole axis. Adjacent baseplates align so a screw passes from one into the other.

### 1B.11: Fit-to-Drawer Baseplate

**Source:** `kennetek/gridfinity-rebuilt-openscad` (MIT)
**File:** `gridfinity-rebuilt-baseplate.scad` → `[Fit to Drawer]` section
**Selection:** Set `gridx=0` / `gridy=0` to trigger auto-calculation from `distancex` / `distancey`

**Parameters (verified 2026-02-28):**
| Parameter | Default | Notes |
|-----------|---------|-------|
| `distancex` | 0 | Target drawer X dimension (mm); 0 = disabled |
| `distancey` | 0 | Target drawer Y dimension (mm); 0 = disabled |
| `fitx` | 0 | X padding alignment: -1 = flush left, 0 = centered, 1 = flush right |
| `fity` | 0 | Y padding alignment: -1 = flush front, 0 = centered, 1 = flush back |

**Algorithm:**
1. Auto-grid: `grid = floor(distance / l_grid)` when `gridx=0` (upstream `l_grid = 42`)
2. Outer size: `max(grid * l_grid, distance)` — ensures plate is never smaller than drawer
3. Padding: `outer_size - grid * l_grid`
4. Grid offset from outer center: `padding * fit / 2`
   - `fit = -1` → grid flush to negative side (left/front), padding on opposite side
   - `fit = 0` → grid centered, equal padding both sides
   - `fit = +1` → grid flush to positive side (right/back), padding on opposite side

**Upstream source lines (kennetek):**
- `gridx = 0` triggers: `gridx = max(1, floor(distancex / l_grid))`
- `distancex = max(gridx * l_grid, distancex)` — outer size calc
- Grid offset: `(distancex - gridx * l_grid) * fitx / 2`

**Compatibility:** All existing features (magnets, screws, weighted, skeleton, screw-together, corner screws) work with fit-to-drawer. The grid offset is applied to all hole/cell/screw positions.

---

## Phase 1C: Extended Feature Set (ostat)

**Source repo:** `ostat/gridfinity_extended_openscad` (GPL — spec reference ONLY)
**Key files:** `modules/module_patterns.scad`, `modules/module_item_holder.scad`, `modules/module_gridfinity_cup.scad`, `modules/module_lip.scad`, `modules/module_fingerslide.scad`, `modules/module_bin_chambers.scad`

### 1C.1: Wall Pattern — Grid

**Source:** `modules/module_patterns.scad` → `cutout_pattern()` → `modules/module_item_holder.scad` → `GridItemHolder(hexGrid=false)`

**Parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `cellSize` | `[10, 10]` mm | Grid cell dimensions |
| `strength` / `holeSpacing` | `2` mm (becomes `[2, 2]`) | Wall thickness between holes |
| `circleFn` / `holeHoleSides` | `6` | Hole shape: 4=square, 6=hex, 8=octo, 64=circle |
| `holeRadius` | `0.5` mm | Corner radius on hole shape |
| `patternGridChamfer` | `0` | Taper/chamfer on pattern cuts |
| `patternBorder` | `0` mm | Border inset from wall edge |
| `patternDepth` | `0` (= full wall) | Depth of pattern cuts |

### 1C.2: Wall Pattern — Hex

**Source:** Same as 1C.1 but `GridItemHolder(hexGrid=true)`

Hex is the default wall pattern style (`wallpattern_style = "hexgrid"`). Uses alternating row offset logic in `GridItemHolder()`. All parameters same as 1C.1.

### 1C.3: Wall Pattern — Brick

**Source:** `modules/module_pattern_brick.scad` → `brick_pattern()` via `cutout_pattern()`

**Two sub-styles:**
- `"brick"` — aligned rows
- `"brickoffset"` — staggered/alternating rows (matches FEATURE-SPEC description)

**Parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `cell_size` | `[15, 5]` mm | Brick dimensions |
| `spacing` | `1` mm | Mortar thickness (from `strength`) |
| `corner_radius` | `3` mm | Brick corner rounding (from `holeRadius`) |
| `center_weight` | `3` (customizer default `5`) | Controls center weighting via `patternBrickWeight` |
| `offset_layers` | bool | `true` for `"brickoffset"` style |

### 1C.4: Wall Pattern — Slat

**Source:** `modules/module_pattern_slat.scad` → `slat_pattern()` via `cutout_pattern()`

**Note:** Slats are **vertical strips** (not horizontal slots). Rotation can change orientation.

**Parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `slat_width` | from `cellSize.x` | Width of each slat cutout |
| `spacing` | from `strength.x` | Gap between slats |
| `slat_chamfer` | from `patternGridChamfer` | Supports `[top, bottom]` chamfer |
| `thickness` | wall depth | Depth of cut |

### 1C.5: Per-Wall Pattern Enable/Disable

**Source:** `modules/module_patterns.scad` → `get_wallpattern_positions()` + `modules/module_gridfinity_cup.scad`

**Important:** This enables/disables the **same** pattern on each wall individually. It does NOT assign different patterns to different walls.

**Parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `wallpattern_walls` | `[1,1,1,1]` | `[front, back, left, right]`, each 0 or 1 |
| `wallpattern_dividers_enabled` | `"disabled"` | Options: `"disabled"`, `"horizontal"`, `"vertical"`, `"both"` |

### 1C.6: Pattern Fill Modes

**Source:** `modules/module_patterns.scad` → `PatternSettings()`

**9 fill modes** (used by both wall and floor patterns):
| Constant | Description |
|----------|-------------|
| `PatternFill_none` | Natural grid placement, no adjustment |
| `PatternFill_space` | Distribute spacing evenly to fill canvas |
| `PatternFill_crop` | Clip patterns beyond canvas (both axes) |
| `PatternFill_crophorizontal` | Crop horizontal only |
| `PatternFill_cropvertical` | Crop vertical only |
| `PatternFill_spacehorizontal` | Space horizontal only |
| `PatternFill_spacevertical` | Space vertical only |
| `PatternFill_crophorizontal_spacevertical` | Crop H + space V |
| `PatternFill_cropvertical_spacehorizontal` | Crop V + space H |

### 1C.7: Minimum Lip (5th Style)

**Source:** `modules/module_lip.scad` → `cupLip()` / `cupLip_cavity()` with `lipStyle = "minimum"`

All 5 lip styles in ostat:
| Style | Constant | Notes |
|-------|----------|-------|
| Normal | `LipStyle_normal` | Already implemented (0.17) |
| Reduced | `LipStyle_reduced` | Already implemented (0.18) |
| Reduced Double | `LipStyle_reduced_double` | Double-stack reduced lip — second lip below first, offset by `lipHeight + labelCornerRadius` |
| Minimum | `LipStyle_minimum` | Thinnest possible: `lipSupportThickness = 0`, removes entire lip cavity |
| None | `LipStyle_none` | Already implemented (0.19) |

**For `minimum`:** Removes `hull() cornercopy() cylinder(r=innerWallRadius, h=gf_Lip_Height)`, creating just a thin rim.

### 1C.8: Finger Slide — Rounded

**Source:** `modules/module_fingerslide.scad` → `FingerSlide()` → `modules/utility/module_utility.scad` → `roundedCorner()`

**Note:** This is a **quarter-cylinder** cutout (90°), not semi-circular.

**Parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `fingerslide_radius` | `-3` | Negative = proportional: `min(cup_height, cup_size) / abs(value)` |
| `fingerslide_walls` | `[1,0,0,0]` | `[front, back, left, right]`, default front only |
| `fingerslide_lip_aligned` | `true` | Align slide to lip profile |

**`roundedCorner()` params:** `radius`, `length`, `height` — creates quarter-cylinder subtraction volume.

### 1C.9: Finger Slide — Chamfered

**Source:** `modules/module_fingerslide.scad` → `FingerSlide()` → `chamferedCorner()`

Same parameters as 1C.8. Creates angled flat cut instead of curve.

**`chamferedCorner()` params:** `chamferLength`, `cornerRadius`, `length`, `height`, `width`, `angled_extension`.

### 1C.10: Tapered Bin Corners

**Source:** `modules/module_gridfinity_cup.scad` (line ~995) → `bin_cutouts()` with `tapered_corner` param

**Important:** NOT interior corner chamfers. These are **large back-wall-top corner cutouts** for easier item retrieval (similar to a scoop but at the top back).

**Parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `tapered_corner` | `"none"` | `"none"` / `"rounded"` / `"chamfered"` |
| `tapered_corner_size` | `10` mm | Size; `-1`=full height, `-2`=half height, `0`=full minus fillet |
| `tapered_setback` | `-1` | Default = `gf_cup_corner_radius` |

**Geometry:** Positioned at back wall (`num_y` side), spanning full bin width. Rounded = quarter cylinder, chamfered = angled flat.

### 1C.11: Wall Cutouts

**Source:** `modules/utility/wallcutout.scad` → `WallCutout()`, `WallCutoutSettings()`, `calculateWallCutouts()`

**Parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `type` | `"disabled"` | `"disabled"/"enabled"/"wallsonly"/"frontonly"/"backonly"/"inneronly"/"leftonly"/"rightonly"` |
| `width` | `0` (auto) | mm; `0` = `wall_length * pitch / 3` |
| `angle` | `70°` | Trapezoidal widening angle |
| `height` | `0` (auto) | mm; negative = ratio |
| `corner_radius` | `5` mm | Cutout corner rounding |
| `position` | varies | GF units or ratio; negative = ratio of `length/abs(value)` |

Separate settings for vertical (front/back) and horizontal (left/right) walls. Supports multiple cutout positions per wall. Shape: trapezoidal profile with rounded corners via triple-offset fillet.

### 1C.12: Irregular Subdivisions

**Source:** `modules/module_bin_chambers.scad` → `ChamberSettings()` with `irregular_subdivisions = true`, `calculateSeparators()`

**Parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `vertical_irregular_subdivisions` | `false` | Enable vertical irregular mode |
| `horizontal_irregular_subdivisions` | `false` | Enable horizontal irregular mode |
| `vertical_separator_config` | `""` | Pipe-separated positions, e.g., `"10.5\|21\|42\|50\|60"` |
| `horizontal_separator_config` | `""` | Same format |

Per-separator overrides (CSV within each pipe segment): `position,bend_separation,bend_angle,cut_depth,cut_width,wall_thickness`

### 1C.13: Divider Wall Notches (Removable Dividers)

**Source:** `modules/module_bin_chambers.scad` + `modules/utility/module_utility.scad` → `bentWall()` with `wall_cutout_depth`

**Important:** These are **U-shaped notches cut from the top of divider walls**, not grooves in bin walls. Reduces divider height to allow removable insert dividers.

**Parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `separator_cut_depth` | `0` (disabled) | Height of notch from divider top |
| `wall_cutout_width` | `0` (auto = `length/2`) | Width of notch |
| `wall_cutout_radius` | varies | Corner radius of notch |

Per-separator override via irregular config: 4th CSV field = `cut_depth`, 5th = `cut_width`.

### 1C.14: Extendable (Split) Bins

**Source:** `modules/module_gridfinity_Extendable.scad` → `ExtendableSettings()`, `cut_bins_for_extension()`, `extension_tabs()`

Called "Extendable" in ostat. Cuts bin into two halves with snap-together tabs for printing large bins in pieces.

**Parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `extension_x_enabled` | `"disabled"` | `"disabled"/"front"/"back"` |
| `extension_y_enabled` | `"disabled"` | `"disabled"/"front"/"back"` |
| `extension_x_position` | `0.5` | Cut position (0.0–1.0) |
| `extension_y_position` | `0.5` | Cut position (0.0–1.0) |
| `extension_tabs_enabled` | `true` | Generate interlocking tabs |
| `extension_tab_size` | `[10,0,0,0]` | `[height, width, thickness, style]`; width default = height, thickness default = 1.4 |

### 1C.15: REMOVED — Bottom Text Embossing

**Does not exist in ostat.** The `cup_base_text()` module only supports debossing (subtraction via `difference()`). There is no embossing option. See 1C.16.

### 1C.16: Bottom Text Debossing

**Source:** `modules/module_gridfinity_cup_base_text.scad` → `cup_base_text()` (called from `module_gridfinity_cup.scad` line 603)

**Parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `text_1` | `false` | Enable line 1 (auto-generates bin size, e.g., "2 x 1 x 3") |
| `text_2` | `false` | Enable line 2 with custom text |
| `text_2_text` | `"Gridfinity"` | Custom text string |
| `text_size` | `0` (auto) | mm; `0` = auto-fit to 30mm width |
| `text_depth` | `0.3` mm | Subtraction depth |
| `text_offset` | `[0, 0]` mm | X/Y offset |
| `text_font` | `"Aldo"` | Options: `"Aldo"`, `"B612"`, `"Open Sans"`, `"Ubuntu"` |

Text is positioned on the underside (bottom face) relative to magnet holes and wall thickness.

### 1C.17: Floor Pattern — Grid

**Source:** `modules/module_gridfinity_cup.scad` → `bin_floor_pattern()` (line ~921) → `modules/module_patterns.scad` → `cutout_pattern()`

Same pattern system as wall patterns. All 8 pattern styles available for floors (not just grid).

**Parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `floorpattern_style` | `"hexgrid"` | Any of the 8 pattern styles |
| `floorpattern_enabled` | `false` | Enable floor patterns |
| `floorpattern_fill` | `"crop"` | Fill mode (see 1C.6) |
| `floorpattern_cell_size` | varies | Cell dimensions |
| `floorpattern_strength` | varies | Wall between holes |
| `floorpattern_hole_sides` | varies | Hole shape |
| `floorpattern_border` | `5` mm minimum | Border inset (forced `max(5, ...)`) |

Respects divider positions (subtracts divider walls). Respects magnet/screw pad positions.

### 1C.18: Floor Pattern — Hex

Same as 1C.17 with `floorpattern_style = "hexgrid"` (this is the default).

### Additional ostat Pattern Styles (Not in Current Scope)

The following pattern styles exist in ostat but are not individually tracked:
- `"voronoi"` — requires external library (deferred, see Out of Scope)
- `"voronoigrid"` — voronoi constrained to grid
- `"voronoihexgrid"` — voronoi constrained to hex grid

---

## Phase 1D: Accessories (Mixed Sources)

### 1D.1: Anylid Click-Lock Lid

**Source:** rngcntr/anylid — **NO GitHub repo.** Available on [MakerWorld model #1059434](https://makerworld.com/en/models/1059434) and integrated into [Perplexing Labs Generator](https://gridfinity.perplexinglabs.com/pr/anylid/0/0).
**License:** TBD/unclear — community has asked rngcntr for permissive license. MakerWorld default applies.

**Key specs (from MakerWorld description):**
- Click-lock mechanism snaps onto any bin with Gridfinity-compatible stacking lip
- 1U height (stays in-system)
- Compatible with all stackable Gridfinity boxes
- Label accommodation (reduce click rail length by label width)
- Rails in X or Y direction (not both when using labels)
- Optional magnet holes

**Implementation note:** Cannot implement without resolving license. May need to use as dimensional spec reference only (measure from STL/description) or contact rngcntr.

### 1D.2: Anylid Baseplate-on-Top

**Source:** Same as 1D.1 (rngcntr/anylid on MakerWorld)

**Key specs:**
- Top grid functions as regular baseplate
- Each lid adds exactly 1U height — 3U bin + lid = 4U bin height
- Allows stacking boxes on top of each other
- Full baseplate receptacles on lid top surface, standard Gridfinity grid pattern

**License:** Same TBD issue as 1D.1.

### 1D.3: Cullenect Click-In Label

**Source:** `CullenJWebb/Cullenect-Labels` (note: **hyphen** in repo name)
**License:** MIT (confirmed)
**Source file:** `OpenSCAD/Cullenect.scad`

**Key modules:**
- `cullenect_base_v1()` — V1 label with wall sockets (backward compatible)
- `cullenect_base_v2()` — V2 label without backward compatibility
- `cullenect_base()` — version selector
- `cullenect_socket()` — horizontal socket with ribs
- `cullenect_label_generate()` — master module

**Key dimensions:**
| Dimension | Value |
|-----------|-------|
| Label width | `(42mm × GF_units) - 6mm` |
| Label height (Y) | `11.0` mm |
| Label depth (Z) | `1.2` mm |
| Latch inset | `0.2` mm perimeter |
| Latch depth | `0.6` mm |
| Socket XY offset | `0.3` mm |
| Socket rib XY | `0.2` mm |
| Socket rib depth | `0.4` mm |

**Features:** Embossed/debossed text, hardware icons (Phillips, Hex, Torx, screw heads, washers, nuts, T-nuts, magnets, crimp fittings — 18+ types), surface finishes.

### 1D.4: Label Negative Volume

**Source:** `CullenJWebb/Cullenect-Labels`
**Files:**
- `OpenSCAD/Cullenect Negative Volume.stl` — pre-built STL
- `cullenect_socket_negative()` — horizontal socket negative module
- `cullenect_vertical_socket_negative()` — vertical socket negative module

Boolean subtraction volume to carve label socket into any bin. For our implementation, we'll generate the negative geometry natively in CadQuery.

### 1D.5: Item Holder — Battery

**Source:** `ostat/gridfinity_extended_openscad` (GPL — spec reference ONLY)
**Files:** `gridfinity_item_holder.scad`, `modules/module_item_holder.scad`, `modules/module_item_holder_data.scad`
**Key function:** `LookupKnownBattery()`

**Battery dimensions `[diameter, width, thickness, depth, height, shape]`:**
| Battery | Diameter | Height | Shape |
|---------|----------|--------|-------|
| AAA | 10.5 mm | 44.5 mm | round |
| AA | 14.5 mm | 50.5 mm | round |
| 9V | 17.5×26.5 mm | 48.5 mm | square |
| 18650 | 18 mm | 65 mm | round |
| C | varies | varies | round |
| D | varies | varies | round |

Also: `LookupKnownCellBattery()` for coin cells (CR927 through CR11108 series).

**Key parameters:** `itemholder_hole_clearance` (default 0.25mm), `itemholder_grid_style` ("square"/"hex"/"auto"), `itemholder_compartments` [x, y].

### 1D.6: Item Holder — Hex Bit

**Source:** Same as 1D.5
**Key function:** `LookupKnownTool()`

**Tool dimensions:**
| Tool | Diameter | Shape |
|------|----------|-------|
| 1/4" hex | 6.35 mm | hex |
| 3/8" hex | 9.52 mm | hex |
| Router bits | various | round/hex |

`circleFn=6` for hexagonal holes.

### 1D.7: Item Holder — Card

**Source:** Same as 1D.5
**Key functions:** `LookupKnownCard()`, `multiCard()`

**Card dimensions:**
| Card | Width | Thickness | Height | Shape |
|------|-------|-----------|--------|-------|
| SD | 24 mm | 2.1 mm | 32 mm | square |
| MicroSD | 11 mm | 0.7 mm | 15 mm | square |
| CompactFlash I | 43 mm | 3.3 mm | 36 mm | square |

Also: `LookupKnownCartridge()` for game cartridges (Nintendo, Sega, Atari, Sony).

**Multi-card module:** `multiCard()` with `longCenter`, `smallCenter`, `side`, `chamfer`, `alternate` params. `itemholder_multi_cards` (comma-separated, e.g., `"sd;USBA;microsd"`), `itemholder_multi_card_compact` (nesting ratio 0–1).

### 1D.8: Sliding Lid

**Source:** `ostat/gridfinity_extended_openscad` (GPL — spec reference ONLY)
**Files:** `gridfinity_sliding_lid.scad`, `modules/module_gridfinity_sliding_lid.scad`

**Key modules:**
- `SlidingLid()` — main lid generator
- `SlidingLidCavity()` — cavity for lid insertion in bin walls
- `SlidingLidSupportMaterial()` — print support structures
- `SlidingLidSettings()` — configuration (18 parameters)

**Key parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `lidThickness` | `1.6` mm | 0 = wall_thickness × 2 |
| `clearance` | `0.1` mm | Gap for smooth sliding |
| `lip_clearance` | `0.1` mm | |
| `lip_height` | `3.75` mm | |
| `headroom` | `0.8` mm | |
| `pull_style` | `"disabled"` | `"disabled"/"lip"/"finger"` |
| `nub_size` | `0.5` mm | Retention nub |
| `text_depth` | `0.3` mm | Optional text engraving depth |

Mechanism: slides along cylindrical support rails. Pull styles: lip (tapering ledge), finger (3mm radius cylindrical indentation).

### 1D.9: Drawer Chest Frame

**Source:** `ostat/gridfinity_extended_openscad` (GPL — spec reference ONLY)
**File:** `gridfinity_drawers.scad`

**Key modules:** `chest()`, `chestCutouts()`, `gridfinity_drawer()`, `feet()` / `foot()` / `footrecess()`
**Render choice:** `render_choice = "chest"`

**Key parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `chest_wall_thickness` | `2` mm | |
| `chest_clearance` | `0.25` mm | Per axis |
| `chest_drawer_slide_thickness` | `0` | |
| `chest_drawer_slide_width` | `10` | |
| `chest_enable_top_grid` | bool | Baseplate grid on top |
| `chest_bottom_grid` | bool | Baseplate grid on bottom |
| Magnet specs | 6.5mm dia × 2.4mm | Standard gridfinity |

### 1D.10: Drawer Sliding Unit

**Source:** Same as 1D.9
**Render choice:** `render_choice = "onedrawer"` or `"drawers"`

**Key modules:** `drawers()`, `drawer()`, `drawerPull()` / `basicDrawerPull()`

**Key parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `drawer_inner_depth` | varies | |
| `drawer_inner_height` | varies | |
| `drawer_inner_width` | varies | |
| `drawer_wall_thickness` | `2` mm | |
| `drawer_clearance` | `[x,y,z]` | Per-axis spacing |
| `drawer_base` | `"default"` | `"default"` or `"grid"` |
| `drawer_count` | varies | + `drawer_custom_sizes` per-drawer |
| `handle_size` | varies | Pull dimensions |

### 1D.11: Catch-All Tray

**Source:** `ostat/gridfinity_extended_openscad` (GPL — spec reference ONLY)
**File:** `gridfinity_tray.scad`

**Key modules:** `tray()`, `gridfinity_tray()`

**Key parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `tray_corner_radius` | `2` mm | |
| `tray_spacing` | `2` mm | Between compartments |
| `tray_vertical_compartments` | `1` | |
| `tray_horizontal_compartments` | `1` | |
| `tray_custom_compartments` | `""` | Format: `"xpos,ypos,xsize,ysize,radius,depth\|..."` |
| `tray_zpos` | varies | Vertical offset |
| `tray_magnet_radius` | varies | |

Set compartments to 1×1 for true catch-all (open, no dividers). Custom compartment string allows arbitrary subdivision. Full gridfinity cup integration (lip, labels, patterns, efficient floor).

### 1D.12: Vertical Divider

**Source:** `ostat/gridfinity_extended_openscad` (GPL — spec reference ONLY)
**File:** `gridfinity_vertical_divider.scad` (separate from tray)

**Note:** Upstream calls this "Gridfinity Divider" — it's a bin with tall vertical partition walls (for files, folders, envelopes), not a shallow tray.

**Key modules:** `Gridfinity_Divider()`, `PatternedDivider()`, `Divider()` (2D profile)

**Key parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `dividerCount` | `4` | Number of internal vertical partitions |
| `dividerHeight` | `50` mm | |
| `dividerWidth` | `3` mm | Partition wall thickness |
| `frontTopInset` | `20` mm | |
| `frontTopAngle` | `65°` | Angled top for easy access |
| `backTopInset` | `20` mm | |
| `backTopAngle` | `65°` | |
| `radius` | `5` mm | Corner radius |
| `baseHeight` | `10` mm | Solid base below partitions |
| `wallpatternEnabled` | bool | Patterns on divider walls |

---

## Phase 1E: Rugged Box Expansion (smkent)

**Source repo:** `smkent/monoscad` (CC BY-SA 4.0)
**Primary library:** `rugged-box/rugged-box-library.scad` (~2,182 lines)
**Gridfinity wrapper:** `gridfinity/rugged-box/rugged-box-gridfinity.scad` (~368 lines)

### 1E.1: Clip Latch

**Source:** `rugged-box/rugged-box-library.scad`
**Key modules:** `_clip_latch_shape()` (line ~1629), `_clip_latch_part()` (line ~1666), `_latch()` (line ~2029, dispatcher), `rbox_latch(placement="print")` (line ~233)
**Selection:** `latch_type = "clip"` in `rbox()`

**Key parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `latch_edge_radius` | `0.8` | Edge chamfer |
| `latch_body_size_proportion` | `3.0` | Size relative to screw diameter |
| `latch_base_size` | `4.5` mm | `screw_diameter × (proportion / 2)` |
| `screw_diameter` | `3` mm | M3 screws |
| `$b_latch_width` | 22mm (generic), 28mm (GF) | Latch width |
| Latch screw separation | 20mm (generic), 16mm (GF) | |
| `screw_hole_diameter_size_tolerance` | `-0.1` | Thread-forming fit |

**Geometry:** Single-piece: hinge eyelet (bottom), main body, catch eyelet with flex slot (top). Extruded with `_linear_extrude_with_chamfer()`.

### 1E.2: Draw Latch

**Source:** `rugged-box/rugged-box-library.scad`
**Key modules:** `_draw_latch_handle()` (line ~1853), `_draw_latch_catch()` (line ~1990), `_draw_latch_grip()` (line ~1836), `_draw_latch_part()` (line ~2015)
**Selection:** `latch_type = "draw"` in `rbox()`

**Key parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `draw_latch_body_angle` | `25°` | |
| `draw_latch_body_curve_radius` | `10` mm | |
| `draw_latch_grip_angle` | `45°` | |
| `draw_latch_grip_curve_radius` | `16` mm | |
| `draw_latch_thickness` | `2.25` mm | `latch_base_size / 2` |
| `draw_latch_handle_length` | `14.625` mm | `latch_base_size × 3.25` |
| `draw_latch_screw_eyelet_radius` | `3.3` mm | |
| `draw_latch_pin_handle_radius` | `4.8` mm | |
| `draw_latch_pin_radius` | `2.6` mm | |
| `draw_latch_sep` | `0.4` mm | Clearance between segments |
| `draw_latch_vsep` | `0.6` mm | Vertical separation |
| `draw_latch_poly_div` | `10` | Polyhedron subdivision |

**Geometry:** Two-piece design (handle + catch connected by pin joint). Handle has curved grip surface via custom polyhedra. Segmented into alternating interlocking sections.

### 1E.3: Lip Seal (4 Types)

**Source:** `rugged-box/rugged-box-library.scad`
**Key modules:** `_box_seal_shape()` (line ~991), `_box_seal()` (line ~1012), `_box_add_seal()` (line ~1020)
**Selection:** `lip_seal_type` in `rbox()`

| Type | Value | Geometry |
|------|-------|----------|
| None | `"none"` | No seal |
| Wedge | `"wedge"` | Trapezoidal cross-section, `seal_thickness = $b_total_lip_thickness / 3` |
| Square | `"square"` | Square cross-section, same thickness |
| Filament | `"filament-1.75mm"` | Circle d=1.75mm, cut into BOTH halves |

For wedge/square: seal protrudes from top, groove cut into bottom.
For filament: groove cut into both top and bottom (no protrusion).
Seal position: `$b_corner_radius + $b_total_lip_thickness / 2` from box wall center.

### 1E.4: Base Styles (4 — Gridfinity-Specific)

**Source:** `gridfinity/rugged-box/rugged-box-gridfinity.scad`
**Key functions:** `gridfinity_base_plate_style()` (line ~145), `gridfinity_base_plate_magnets_enabled()` (line ~137)

| Style | Value | Magnets | Plate |
|-------|-------|---------|-------|
| Minimal | `"minimal"` | No | Thin (style 0) |
| Thick | `"thick"` | No | Full (style 1) |
| Enabled (Skeletonized) | `"enabled"` | Yes | Skeletonized (style 2), top = full |
| Enabled (Full) | `"enabled_full"` | Yes | Full (style 1) |

Uses kennetek `gridfinityBaseplate()` for actual plate geometry.
Stackable mode offsets: `stackable_plate_offset = 3.4`, `stackable_top_plate_offset = -0.8`, `stackable_bottom_base_offset = -0.6`.

### 1E.5: Stacking Latches

**Source:** `rugged-box/rugged-box-library.scad`
**Key modules:** `_stacking_latch_shape()` (line ~2079), `_stacking_latch_part()` (line ~2127), `_stacking_latch()` (line ~2134), `_box_stacking_latch_ribs()` (line ~1348)

**Key parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `stacking_latch_catch_offset` | `-10` | Offset of catch |
| `stacking_latch_grip_length` | `8` mm | |
| `stacking_latch_screw_separation` | `20` mm | |
| `$b_stacking_separation` | `1.6` mm (GF stackable) | Vertical gap between stacked boxes |

**Requirements:** Box must be tall enough: `$b_outer_height > stacking_latch_screw_separation * 2.0` (>40mm). Placed on **sides** of box.

### 1E.6: Third Hinge

**Source:** `rugged-box/rugged-box-library.scad`
**Key:** `third_hinge_width` in `rbox_size_adjustments()` (line ~186), applied in `_box_attachment_placement(hinge=true)` (line ~1162)

**Logic:** When `$b_third_hinge_width > 0` and `$b_inner_width >= $b_third_hinge_width`, adds center hinge at position `[0]`.
**Gridfinity:** Activates at 5U wide (5 × 42 = 210mm): `third_hinge_width = Third_Hinge ? (l_grid * 5) : 0`
Adds 1 more screw to BOM.

### 1E.7: Hinge End Stops

**Source:** `rugged-box/rugged-box-library.scad`
**Key modules:** `_box_hinge_rib_bottom_end_stop(width)` (line ~1400), applied in `_box_hinge_ribs()` (line ~1418)
**Selection:** `hinge_end_stops` param, `Hinge_End_Stops = true` in customizer.

Added only to **bottom** box part hinges. Physical barrier limiting hinge rotation angle. Width = `_latch_width()`. Positioned 2.0mm below top of box wall.

### 1E.8: Parametric Walls

**Source:** `rugged-box/rugged-box-library.scad` → `rbox_size_adjustments()` (line ~186)

| Parameter | Generic Default | Gridfinity Default | Range | Description |
|-----------|----------------|-------------------|-------|-------------|
| `wall_thickness` | 2.4 mm | 3.0 mm | 0.4–10 mm | Base wall thickness |
| `lip_thickness` | 2.0 mm | 3.0 mm | 0.4–10 mm | Added for lip area |
| `rib_width` | 4.0 mm | 6.0 mm | 1–20 mm | Support rib base |
| `latch_width` | 22 mm | 28 mm | 5–50 mm | Latch side-to-side |
| `latch_screw_separation` | 20 mm | 16 mm | 5–40 mm | Screw-to-screw |
| `latch_amount_on_top` | 0 (auto) | 0 (auto) | — | Overlap on top half |
| `size_tolerance` | 0.05 mm | 0.20 mm | 0–1 mm | Fit tolerance |

**Computed values:**
- `$b_total_lip_thickness = wall_thickness + lip_thickness`
- `$b_lip_height = lip_thickness × 2`
- `$b_edge_radius = wall_thickness / 5`

### Additional smkent Features (Not in Phase 1E)

Exist in smkent/monoscad but not tracked in FEATURE-SPEC:
- **Handle** — `_handle_part()` — parametric handle for wide boxes
- **Label/Label Holder** — `_box_label_holder()` — snap-in label with embossed text
- **Top Grip** — `_box_top_grip()` — front grip for easier opening
- **Reinforced Corners** — `$b_reinforced_corners` — thickened corner walls
- **Gridfinity Stackable Mode** — external stacking plates on top/bottom
- **Bill of Materials** — `rbox_bom()` — auto-calculates screw quantities
- **Print Modifier Volumes** — `rbox_body_modifier_volume()` — multi-material meshes

---

## Phase 1F: GridFlock Segmented Baseplates (yawkat)

**Source repo:** `yawkat/gridflock` (MIT + CC-BY 4.0 dual license)
**Main file:** `gridflock.scad` (~1,260 lines, single-file architecture)
**Supporting:** `clickgroove-base.scad`, `puzzle.svg`, `extract_paths.py`

### 1F.1: Baseplate Segment

**Source:** `gridflock.scad` → `segment()` (line ~848)
**Signature:** `module segment(trace, padding, connector, global_segment_index, global_cell_index, global_cell_count)`

A segment is an individual printable piece of a larger baseplate. The `main()` module (line ~1133) splits `plate_size` into segments fitting `bed_size`.

**Key parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `plate_size` | `[371, 254]` mm | Total baseplate size |
| `bed_size` | `[250, 220]` mm | Printer bed size |
| `plate_corner_radius` | `4` mm | |
| `alignment` | `[0.5, 0.5]` | Grid centering within plate |
| `x_segment_algorithm` | `0` | 0=Ideal, 1=Incremental |
| `numbering` | bool | Embossed segment numbers |
| `number_depth` / `number_size` / `number_font` | varies | Numbering format |

**Key dimensions:**
- Profile height: `_profile_height = 4.65` mm
- Segment gap in output layout: `_segment_gap = 10` mm
- Staggered Y splitting via `plan_axis_staggered()` to avoid 4-way intersections

**Supporting functions:** `compute_segment_size()`, `segment_rectangle()`, `cell()`

### 1F.2: Puzzle Connector — Intersection

**Source:** `gridflock.scad` → `puzzle_male()` / `puzzle_female()` (lines ~400–430), `segment_intersection_connectors()` (line ~616)

**Shape source:** `puzzle.svg` (Inkscape SVG with 4 paths: `male_tight`, `male_loose`, `female_tight`, `female_loose`). Converted to OpenSCAD polygons via `extract_paths.py`.

**Parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `connector_intersection_puzzle` | `true` | Enable/disable |
| `intersection_puzzle_fit` | `1` (0–1) | 0=loose, 1=tight |

**Geometry:** Weighted blend: `tight × fit + loose × (1 - fit)`. Connectors at cell intersections (corners). Male on N/E edges, female on S/W edges. Scale: `1/128 × 4`, centered at `[-128, -128]`. Cleanup: subtract radius-4 circle at origin to avoid bin profile overlap.

### 1F.3: Puzzle Connector — Edge

**Source:** `gridflock.scad` → `edge_puzzle()` (line ~739), `segment_edge_connectors()` (line ~696), `round_bar_x()` (line ~713)

**Parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `connector_edge_puzzle` | `false` | Enable/disable |
| `edge_puzzle_count` | `1` | Connectors per cell edge |
| `edge_puzzle_dim` | `[10, 2.5]` mm | Male connector `[length, width]` |
| `edge_puzzle_dim_c` | `[3, 1.2]` mm | Bridge dimensions `[length, width]` |
| `edge_puzzle_gap` | `0.15` mm | Clearance male↔female |
| `edge_puzzle_magnet_border` | `true` | Stability bar at magnet level |
| `edge_puzzle_magnet_border_width` | `2.5` mm | |
| `edge_puzzle_height_female` | `2.25` mm | Female connector height |
| `edge_puzzle_height_male_delta` | `0.25` mm | Male is smaller by this |
| `_edge_puzzle_stagger` | `dim.x + 2` mm | Spacing between multiple connectors |

**Direction:** `[true, true, false, false]` = N/E are male, S/W are female. Male clipped against neighbor's bin profile. Half-size cells: `max(1, floor(count/2))` connectors.

### 1F.4: Filler — None

**Source:** `gridflock.scad` → `compute_global_trace()` (line ~1128)
**Constant:** `_FILLER_NONE = 0`

When `filler_x = 0` or `filler_y = 0`: only full-size (1×) cells. Remaining space = padding. Distribution via `alignment` param.

### 1F.5: Filler — Integer Fraction

**Source:** `gridflock.scad` → `compute_global_trace_fraction()` (line ~1116)
**Constant:** `_FILLER_INTEGER = 1` (this is the default)

**Parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `filler_x` / `filler_y` | `1` | Set to 1 for integer fraction mode |
| `filler_fraction` | `[2, 2]` | Denominator: 2=half, 3=third, etc. |

**Logic:** `scaled = floor(length_norm × fraction)` → split into `whole` full cells + `part` fractional cells (each `1/fraction` size).

### 1F.6: Filler — Dynamic

**Source:** `gridflock.scad` → `compute_global_trace_dynamic()` (line ~1122)
**Constant:** `_FILLER_DYNAMIC = 2`

**Parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `filler_x` / `filler_y` | `2` | Set to 2 for dynamic mode |
| `filler_minimum_size` | `[15, 15]` mm | Minimum filler cell size |

**Logic:** `dyn = length_norm % 1`. If `dyn < minimum_size_norm` → expand last full cell to absorb remainder. Otherwise → create dynamic-sized filler cell. Prevents tiny cells while filling full plate area.

### 1F.7: ClickGroove Anti-Creep Latch

**Source:** `gridflock.scad` (baseplate side, lines ~315–332) + `clickgroove-base.scad` (bin side template)

**IMPORTANT:** This is a **bin-to-baseplate** anti-creep mechanism, NOT a segment-to-segment connector. The puzzle connectors (1F.2, 1F.3) are the segment interlocking mechanisms.

**Two click-latch styles:**
| Style | Constant | Description |
|-------|----------|-------------|
| Arc | `_CLICK1 = 0` | Logistic curve sweep, more robust but more creep-susceptible |
| ClickGroove | `_CLICK2 = 1` | Tab-in-groove, reduced creep |

**ClickGroove (style 1) parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `click` | `false` | Enable click latch |
| `click_style` | `1` | 0=Arc, 1=ClickGroove |
| `clickgroove_gap_length` | `25` mm | Gap behind latch |
| `clickgroove_tab_length` | `10` mm | Tab engagement length |
| `clickgroove_strength` | `1.4` mm | Latch thickness |
| `clickgroove_wall_strength` | `1` mm | Backing wall |
| `clickgroove_depth` | `0.9` mm | Tab protrusion |

**Baseplate geometry:** Gap cut `[2.85 - wall - strength, profile_height, gap_length]`. Triangular tab polygon at `[-2.15, 0.8 + 1.8/2]`.

**Bin groove (from `clickgroove-base.scad`):**
- Groove height: `1.5` mm, depth: `0.75` mm, gap: `0.1` mm
- Groove profile: `polygon([[(1.8-height)/2-gap, -gap], [0.9, depth], [1.8-(1.8-height)/2+gap, -gap]])`
- Placed at `[0, 2.15+0.25/2, 2.6]`, 30mm width, all 4 sides via rotation

### Additional gridflock Features (Not in Phase 1F)

Exist in yawkat/gridflock but not tracked in FEATURE-SPEC:
- **Arc-style click latch** (click_style=0) — alternative to ClickGroove
- **Magnets** — press-fit, glue-from-top, glue-from-bottom, with solid/rounded-corner frames
- **Vertical screws** — at plate corners, edges, segment corners/edges, other intersections; countersink/counterbore
- **Thumb screws** — Gridfinity Refined compatible cutouts
- **Segment numbering** — embossed on bottom for assembly
- **Plate walls** — top/bottom rims with per-side thickness
- **Chamfers** — top/bottom, per-edge configurable
- **Edge adjustment** — shift grid, add padding, squeeze extra cells
- **Cell override** — per-cell normal/solid/empty for irregular shapes
- **Magnet insertion jig** — separate `mag_insert_jig.scad`

---

## Revision History

| Date | Change |
|------|--------|
| 2026-02-27 | Initial creation. All Phase 1C–1F features verified against upstream repos. |
| 2026-02-28 | Added Phase 1B.10 (Screw-together baseplate) verified parameters from kennetek source. |
| 2026-02-28 | Added Phase 1B.11 (Fit-to-drawer baseplate) verified parameters from kennetek source. |
