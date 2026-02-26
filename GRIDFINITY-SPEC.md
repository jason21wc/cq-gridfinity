# Gridfinity Specification Reference

Authoritative dimensional reference for the Gridfinity standard. Compiled from:
- **Official spec:** https://gridfinity.xyz/specification/
- **kennetek/gridfinity-rebuilt-openscad** `src/core/standard.scad` (MIT) — commit `910e22d`
- **cq-gridfinity** `cqgridfinity/constants.py` (MIT) — v0.5.7

When values differ between sources, kennetek's values (derived from the official spec) take precedence.

---

## 1. Grid System

| Parameter | Value | Notes |
|-----------|-------|-------|
| Grid unit XY | 42.0 mm | 1 GU = 42mm in both X and Y |
| Grid unit Z | 7.0 mm | 1 height unit = 7mm |
| Base top dimensions | 41.5 x 41.5 mm | Per grid cell |
| Base gap / tolerance | 0.5 mm total | 0.25mm per side between adjacent bases |

## 2. Base Profile (Cross-Section)

The base profile is a 2D cross-section swept around a rounded rectangle. It consists of three segments from bottom to top:

```
BASE_PROFILE = [
    [0, 0],                           # Innermost bottom point
    [0.8, 0.8],                       # 45° chamfer up-and-out
    [0.8, 2.6],                       # Vertical straight section (1.8mm)
    [2.95, 4.75]                      # 45° chamfer up-and-out (2.15mm run)
]
```

| Parameter | Value | Notes |
|-----------|-------|-------|
| Profile height | 4.75 mm | Total from bottom to top of profile |
| Bottom chamfer | 0.8 mm at 45° | First angled segment |
| Straight section | 1.8 mm | Vertical wall between chamfers |
| Top chamfer | 2.15 mm at 45° | Upper angled segment |
| Base top corner radius | 3.75 mm | Rounded rectangle corner at profile top |
| Base bottom corner radius | 0.8 mm | = top_radius - profile_x_extent |
| Total base height | 7.0 mm | Profile (4.75) + bridge (2.25) |
| Bridge height | 2.25 mm | Flat section connecting to bin floor |

### cq-gridfinity Implementation

cq-gridfinity defines the base profile differently — as a sequence of (distance, angle) tuples:

```python
# cq-gridfinity constants.py
GR_BASE_HEIGHT = 4.75
GR_BASE_CHAMF_H = 0.98994949 / sqrt(2)  # ≈ 0.7 (bottom chamfer height)
GR_STR_H = 1.8                           # straight section
GR_BASE_TOP_CHAMF = 4.75 - 0.7 - 1.8    # ≈ 2.25 (top chamfer)

GR_BASE_PROFILE = (
    (GR_BASE_TOP_CHAMF * sqrt(2), 45),   # top chamfer (2.25mm × √2, 45°)
    GR_STR_H,                             # straight 1.8mm
    (GR_BASE_CHAMF_H * sqrt(2), 45),      # bottom chamfer
)
```

**Note:** cq-gridfinity's profile is ordered top-to-bottom; kennetek's is bottom-to-top. Both produce the same geometry.

## 3. Stacking Lip Profile

The stacking lip is the interlocking rim on top of bins that allows stacking.

```
STACKING_LIP_LINE = [
    [0, 0],             # Inner tip (bottom of lip)
    [0.7, 0.7],         # 45° outward
    [0.7, 2.5],         # Vertical (1.8mm)
    [2.6, 4.4]          # 45° outward (1.9mm run, 1.9mm rise)
]
```

| Parameter | Value | Notes |
|-----------|-------|-------|
| Lip width (X extent) | 2.6 mm | Total horizontal protrusion |
| Lip height (Y extent) | 4.4 mm | Total vertical extent |
| Fillet radius | 0.6 mm | Applied at top of lip |
| Support height | 1.2 mm | Inner support ledge below lip |
| First segment | 0.7mm at 45° | |
| Vertical section | 1.8 mm | |
| Top segment | 1.9mm at 45° | |

### cq-gridfinity Lip Profile

```python
GR_LIP_PROFILE = (
    (GR_UNDER_H * sqrt(2), 45),    # 1.6mm underside (reversed direction)
    GR_TOPSIDE_H,                   # 1.2mm vertical
    (0.7 * sqrt(2), -45),           # 0.7mm at -45°
    1.8,                            # 1.8mm vertical
    (1.3 * sqrt(2), -45),           # 1.3mm at -45°
)
# Total lip height ≈ 6.6mm (includes underside)
```

## 4. Magnet & Screw Holes

Four holes per grid cell, positioned at corners. Each corner can have magnet hole, screw hole, or both.

| Parameter | Value | Notes |
|-----------|-------|-------|
| Magnet diameter | 6.0 mm | Standard neodymium disc magnet |
| Magnet hole diameter | 6.5 mm | 0.5mm clearance |
| Magnet hole depth | 2.4 mm | For 2mm magnet + 2 print layers (0.4mm) |
| Magnet height (actual) | 2.0 mm | Standard disc magnet thickness |
| Screw hole diameter | 3.0 mm | M3 clearance hole |
| Screw hole radius | 1.5 mm | |
| Hole distance from bottom edge | 4.8 mm | Center of hole from base bottom |
| Hole distance from side | 8.0 mm | Center of hole from bin side (cq-gridfinity uses `GR_HOLE_DIST = 13.0` from center) |

### Hole Placement

In kennetek's implementation, holes are placed 4.8mm from the bottom edge of the base. In cq-gridfinity, `GR_HOLE_DIST = 13.0` (26/2) measures from the cell center to hole center.

### Refined Holes (Gridfinity Refined)

| Parameter | Value | Notes |
|-----------|-------|-------|
| Refined hole diameter | 5.86 mm | Tighter than standard, press-fit |
| Refined hole depth | 1.9 mm | Magnet height - 0.1mm |
| Bottom layers | 2 | Layers between hole and bottom surface |

### Crush Rib Holes

| Parameter | Value | Notes |
|-----------|-------|-------|
| Inner radius | 2.95 mm | 5.9mm diameter |
| Rib count | 8 | For press-fit grip |

### Chamfered Holes

| Parameter | Value | Notes |
|-----------|-------|-------|
| Chamfer additional radius | 0.8 mm | Added to hole radius for chamfer |
| Chamfer angle | 45° | |

### Baseplate Screw Countersink

| Parameter | Value | Notes |
|-----------|-------|-------|
| Countersink additional radius | 2.5 mm | Added to screw radius |
| Counterbore radius | 2.75 mm | 5.5mm diameter |
| Counterbore height | 3.0 mm | |

## 5. Wall & Interior Dimensions

| Parameter | Value | Notes |
|-----------|-------|-------|
| Minimum wall thickness | 0.95 mm | `d_wall` in kennetek |
| Nominal wall thickness | 1.0 mm | `GR_WALL` in cq-gridfinity |
| Divider wall width | 1.2 mm | Between compartments |
| Internal fillet radius | 2.8 mm | `r_f2` — inside corners of compartments |
| Inside fillet radius | 1.1 mm | `GR_FILLET` in cq-gridfinity |
| Floor offset | 2.25 mm | `GR_FLOOR = GR_BOT_H - GR_BASE_HEIGHT` |
| Nominal floor height | 7.0 mm | `GR_BOT_H` — base to interior floor |
| Base clearance | 0.25 mm | `GR_BASE_CLR` — extra above nominal base |

## 6. Weighted Baseplate

| Parameter | Value | Notes |
|-----------|-------|-------|
| Bottom height | 6.4 mm | `bp_h_bot` |
| Cut size | 21.4 mm | `bp_cut_size` — square weight pocket |
| Cut depth | 4.0 mm | `bp_cut_depth` |
| Round cut width | 8.5 mm | `bp_rcut_width` — for screw channels |
| Round cut length | 4.25 mm | `bp_rcut_length` |
| Round cut depth | 2.0 mm | `bp_rcut_depth` |

### Skeletal Baseplate

| Parameter | Value | Notes |
|-----------|-------|-------|
| Skeleton radius | 2.0 mm | `r_skel` — fillet on skeleton cutouts |
| Skeleton height | 1.0 mm | `h_skel` — minimum remaining material |

## 7. Tab / Label Strip

| Parameter | Value | Notes |
|-----------|-------|-------|
| Tab width (nominal) | 42.0 mm | Full grid unit width |
| Tab depth | 15.85 mm | |
| Tab support angle | 36° | |
| Tab support height | 1.2 mm | |

### Tab Polygon
```
TAB_POLYGON = [
    [0, 0],
    [0, height],        # height = tan(36°) × 15.85 + 1.2 ≈ 12.72
    [15.85, height],
    [15.85, height - 1.2]
]
```

## 8. Thumbscrew (Gridfinity Refined)

| Parameter | Value | Notes |
|-----------|-------|-------|
| Outer diameter | 15.0 mm | |
| Thread pitch | 1.5 mm | |

## 9. Common Formulas

### Bin outer dimensions
```
outer_x = grid_units_x × 42.0 - 0.5    # e.g., 2×42 - 0.5 = 83.5mm
outer_y = grid_units_y × 42.0 - 0.5
```

### Height from grid units
```
height_mm = grid_units_z × 7.0
```

### Height calculation (kennetek)
```python
def calculate_bin_height(raw_mm, includes_base=False, includes_lip=False):
    return raw_mm + (0 if includes_base else 7.0) - (4.4 if includes_lip else 0)
```

### Z-snap (round up to next 7mm multiple)
```python
def z_snap(height_mm):
    return height_mm if height_mm % 7 == 0 else height_mm + 7 - height_mm % 7
```

## 10. Source Code References

### kennetek/gridfinity-rebuilt-openscad (MIT)
- **Repo:** https://github.com/kennetek/gridfinity-rebuilt-openscad
- **Docs wiki:** https://kennetek.github.io/gridfinity-rebuilt-openscad/
- **Official spec:** https://gridfinity.xyz/specification/
- Key files (current structure):
  - `src/core/standard.scad` — all dimensional constants
  - `src/core/base.scad` — base profile, gridfinityBase(), lite bases, hole placement
  - `src/core/wall.scad` — stacking lip geometry, sweep_rounded()
  - `src/core/bin.scad` — bin construction, subdivide, infill
  - `src/core/cutouts.scad` — compartment cutters, scoop, chamfer
  - `src/core/gridfinity-rebuilt-holes.scad` — hole types (refined, ribbed, chamfered)
  - `src/helpers/generic-helpers.scad` — sweep_rounded(), general geometry utilities

### cq-gridfinity (MIT)
- **Repo:** https://github.com/michaelgale/cq-gridfinity
- Key files:
  - `cqgridfinity/constants.py` — all constants (reviewed in this doc)
  - `cqgridfinity/gf_obj.py` — base class with rendering, export
  - `cqgridfinity/gf_baseplate.py` — baseplate generation
  - `cqgridfinity/gf_box.py` — bin/box generation
  - `cqgridfinity/gf_drawer.py` — drawer spacers
  - `cqgridfinity/gf_ruggedbox.py` — rugged box (Pred's design)
  - `cqgridfinity/gf_helpers.py` — geometry helpers

### ostat/gridfinity_extended_openscad (GPL — spec reference ONLY)
- **Repo:** https://github.com/ostat/gridfinity_extended_openscad
- **Docs:** https://docs.ostat.com/docs/openscad/gridfinity-extended
- Use for understanding *what* to build (feature dimensions/behavior), NOT *how*

---

## Revision History

| Date | Change |
|------|--------|
| 2026-02-22 | Initial compilation from kennetek standard.scad + cq-gridfinity constants.py |
