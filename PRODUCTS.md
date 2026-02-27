# Gridfinity Product Guide

A comprehensive guide to Gridfinity components, variants, and when to use each one.

---

## What Is Gridfinity?

Gridfinity is an open-source, modular storage system designed by [Zack Freedman](https://www.youtube.com/watch?v=ra_9zU-mnl8) in 2022. The system is built on a simple idea: a universal grid of **42mm squares** that baseplates, bins, and accessories all snap into.

**Why it works:**
- **Modular** — Mix and match any combination of bins on any baseplate
- **Stackable** — Bins interlock vertically via a stacking lip profile
- **Customizable** — Open-source designs let you create exactly what you need
- **Printable** — All components are optimized for FDM 3D printing

**Core dimensions:**
| Parameter | Value |
|-----------|-------|
| Grid unit (XY) | 42.0 mm |
| Height unit (Z) | 7.0 mm |
| Base profile height | 4.75 mm |
| Tolerance / gap | 0.5 mm (0.25mm per side) |

A "3x2" component occupies 3 grid cells in one direction and 2 in the other (126mm x 84mm). A "5U" tall bin is 5 x 7mm = 35mm of usable interior height above the base.

---

## The Gridfinity Ecosystem

Three major open-source implementations exist. Understanding their differences helps you choose the right features.

### Gridfinity Rebuilt (kennetek)

**Repository:** [kennetek/gridfinity-rebuilt-openscad](https://github.com/kennetek/gridfinity-rebuilt-openscad) (MIT license)

The **standard reference implementation**. kennetek's codebase defines the canonical Gridfinity geometry — base profile coordinates, stacking lip dimensions, hole placements, and tolerances. If you're unsure whether a dimension is "correct," kennetek's `standard.scad` is the authority.

**Strengths:**
- Clean, well-documented codebase
- Strict adherence to Zack Freedman's original spec
- MIT license — no restrictions on use or modification
- Excellent wiki documentation

**What it covers:**
- Baseplates (plain, magnet, screw, weighted)
- Standard bins with scoops, labels, dividers
- Lite-style (economy) bins
- Multiple hole styles (refined, crush-rib, chamfered)

**What it doesn't cover:**
- Wall patterns (no hex grids, decorative cutouts)
- Extended accessories (item holders, trays, drawers)
- Wall-mount systems
- Vase mode optimization

### Gridfinity Extended (ostat)

**Repository:** [ostat/gridfinity_extended_openscad](https://github.com/ostat/gridfinity_extended_openscad) (GPL license)

A **feature-rich extension** of Gridfinity that adds dozens of options not in the standard spec. Think of it as the "everything and the kitchen sink" version.

**Strengths:**
- 8+ wall pattern styles (hex, grid, voronoi, brick, slats)
- Item holders (batteries, bits, cards, bottles)
- Modular drawers with slides
- Custom cutout profiles
- Per-wall pattern control
- Extensive parametric options

**Important:** GPL license means derivative works must also be GPL. This project uses ostat's work as a **specification reference only** — we read dimensions and feature descriptions, then write independent CadQuery implementations.

### This Project (cq-gridfinity STEP Generator)

**What we are:** A fork of Michael Gale's [cq-gridfinity](https://github.com/michaelgale/cq-gridfinity) (MIT), extended to cover features from both Rebuilt and Extended, outputting native **STEP files** instead of STL.

**Why STEP matters:**
- **Exact geometry** — B-Rep (boundary representation) surfaces, not tessellated triangles
- **Editable** — Import into Fusion 360, SolidWorks, FreeCAD for further modification
- **Precision** — No faceting artifacts on curves and fillets
- **Professional** — STEP is the standard exchange format for manufacturing

**Our coverage (current + planned):**

| Feature | Rebuilt | Extended | This Project |
|---------|---------|----------|-------------|
| Plain baseplates | Yes | Yes | Yes |
| Magnet/screw baseplates | Yes | Yes | Yes |
| Weighted baseplates | Yes | Yes | Yes |
| Skeleton baseplates | Yes | Yes | Planned (1B) |
| Standard bins | Yes | Yes | Yes |
| Lite-style bins | Yes | Yes | Yes |
| Lip style variants | Partial | Yes | Yes |
| Enhanced holes | Yes | No | Planned (1B) |
| Wall/floor patterns | No | Yes | Planned (1C) |
| Rugged boxes (Pred) | No | No | Yes (upstream) |
| Rugged boxes (smkent) | No | No | Planned (1E) |
| Lids (Anylid) | No | No | Planned (1D) |
| Click-in labels | No | No | Planned (1D) |
| Segmented baseplates | No | No | Planned (1F) |
| STEP output | No | No | **Yes** |

---

## Baseplates

Baseplates are the foundation. Bins sit in the baseplate receptacles and are held in place by the interlocking base profile. Choose your baseplate based on how secure you need the bins to be and whether you want to mount the baseplate to a surface.

### Plain Baseplate

```python
GridfinityBaseplate(4, 3)
```

**What it is:** A flat plate with Gridfinity receptacles on top. Bins sit in the receptacles by gravity.

**When to use:**
- Desktop organizers on flat surfaces
- Situations where you frequently rearrange bins
- Lowest material usage and fastest print time

**Trade-offs:** Bins can slide or lift out if bumped. Not suitable for vertical or mobile use.

### Magnet Baseplate

```python
GridfinityBaseplate(4, 3, magnet_holes=True)
```

**What it is:** Baseplate with 6.5mm diameter x 2.4mm deep recesses in the receptacle floor, four per grid cell. You press-fit 6mm x 2mm neodymium disc magnets into these holes. Bins with matching magnets snap into place.

**When to use:**
- Workbenches where bins get bumped
- Light-duty vertical mounting
- When you want bins to "click" into place but still be removable by hand

**Trade-offs:** Requires magnets (~$0.05-0.10 each, 4 per cell per baseplate + 4 per cell per bin). Adds ~2.4mm to baseplate thickness.

### Screw Baseplate

```python
GridfinityBaseplate(4, 3, screw_holes=True)
```

**What it is:** Baseplate with 3.0mm through-holes at the same four-per-cell positions. An M3 bolt passes through from below and threads into a bin's base (or is used with a nut).

**When to use:**
- Permanent or semi-permanent installations
- When you need bins locked down but don't want magnets
- Workshop tool carts that see vibration

**Trade-offs:** Requires M3 hardware. Less convenient than magnets for frequent rearrangement.

### Magnet + Screw (Combined) Baseplate

```python
GridfinityBaseplate(4, 3, magnet_holes=True, screw_holes=True)
```

**What it is:** Both features combined — magnet recesses from the top and screw through-holes from the bottom, sharing the same four-per-cell positions. The screw passes through the remaining material below the magnet recess.

**When to use:**
- Maximum security — magnets for daily use, screws for transport
- Vehicle tool organizers
- Vertical or overhead mounting

**Trade-offs:** Thickest baseplate variant (~6.4mm extra depth). Most hardware required.

### Weighted Baseplate

```python
GridfinityBaseplate(4, 3, weighted=True, magnet_holes=True)
```

**What it is:** Baseplate with square pockets (21.4mm, 4mm deep) in the bottom of each grid cell, plus cross-shaped channels for screw access. You insert weights (coins, steel plates, lead) into the pockets.

**When to use:**
- Freestanding desktop organizers that need stability
- When you want the baseplate to resist tipping without mounting it
- Heavy-bin configurations where the base needs ballast

**Trade-offs:** Heaviest baseplate. Requires weights.

### Corner Screw Baseplate

```python
GridfinityBaseplate(4, 3, ext_depth=5, corner_screws=True)
```

**What it is:** Baseplate with countersunk mounting screw holes at the four outer corners. Used to bolt the baseplate to a surface (desk, shelf, drawer bottom, wall).

**When to use:**
- Permanent mounting to surfaces
- Can be combined with any other baseplate feature
- When the baseplate itself needs to be secured

### Baseplate Decision Guide

```
Need bins to stay put?
├── No → Plain baseplate
├── Yes, but easy to remove → Magnet baseplate
├── Yes, locked down → Screw baseplate
├── Yes, maximum security → Magnet + Screw baseplate
└── Need the baseplate itself stable?
    ├── Mounted to surface → Corner screw baseplate
    └── Freestanding → Weighted baseplate
```

---

## Bins (Boxes)

Bins are the containers that sit in baseplates. They come in various styles optimized for different use cases.

### Standard Bin

```python
GridfinityBox(3, 2, 5)  # 3x2 grid units, 5 height units
```

**What it is:** The default Gridfinity bin — an open-top box with the standard base profile (for baseplate mating) and stacking lip (for vertical stacking). Wall thickness is 0.95-1.0mm.

**When to use:** General-purpose storage. The starting point for most use cases.

### Standard Bin with Features

```python
GridfinityBox(3, 2, 5, holes=True, scoops=True, labels=True, length_div=2, width_div=1)
```

All features can be combined:

| Feature | What it does | When to use |
|---------|-------------|-------------|
| `holes=True` | Magnet/screw counterbored holes in bin base | Magnetic attachment to baseplates |
| `scoops=True` | Radiused ramp on front wall interior | Small parts that are hard to grab from flat-bottom bins |
| `labels=True` | Flat ledge on back wall for label strips | Organized workshops, inventory systems |
| `length_div=N` | N dividing walls along length | Separating different items (e.g., screw sizes) |
| `width_div=N` | N dividing walls along width | Creating a grid of compartments |

### Lite-Style Bin

```python
GridfinityBox(3, 2, 5, lite_style=True)
```

**What it is:** An economy bin that uses less material. Thinner walls (max 1.5mm), no elevated floor above the base — the interior goes all the way down to the base profile. Faster to print, uses less filament.

**When to use:**
- Large quantities of bins where material cost matters
- Light-duty storage (paper clips, rubber bands, craft supplies)
- When you want the maximum possible interior volume

**Trade-offs:** Less rigid. Cannot use bottom mounting holes. Dividers are forced to match grid units (can't subdivide freely).

### Solid Block

```python
GridfinitySolidBox(4, 2, 3)
# or
GridfinityBox(4, 2, 3, solid=True, solid_ratio=0.75)
```

**What it is:** A completely filled (or partially filled) Gridfinity block with no interior cavity. Used as a blank for CNC machining, custom modifications, or as a spacer/filler.

**When to use:**
- Starting point for custom tool holders (subtract your tool shape)
- Spacers to fill unused baseplate positions
- Weighted blocks for stability
- `solid_ratio` controls fill level (0.0 = empty, 1.0 = fully solid)

### Rugged Box

```python
GridfinityRuggedBox(4, 3, 6)
```

**What it is:** A heavy-duty enclosed box with hinged lid, clasps, and optional handles. Based on Pred's design (upstream cq-gridfinity). Designed for transport and protection.

**When to use:**
- Portable tool kits
- Transport of delicate or organized items
- When you need a lid and secure closure

---

## Stacking Lip Styles

The stacking lip is the shaped rim around the top of a bin that interlocks with the base profile of a bin stacked above it. Three options are available:

### Normal Lip (`lip_style="normal"`)

```python
GridfinityBox(2, 2, 3)  # normal is the default
```

**What it is:** The full Gridfinity stacking lip — a multi-segment profile with underside chamfer, straight section, and overhanging top. Total height ~6.6mm, protrusion ~2.6mm.

**When to use:**
- Any time you plan to stack bins
- The standard choice for most applications

**Printing note:** The overhang on the lip interior prints at 45° — this is within most printers' capability without supports, but very fast print speeds or poor cooling may cause slight drooping on the innermost overhang.

### Reduced Lip (`lip_style="reduced"`)

```python
GridfinityBox(2, 2, 3, lip_style="reduced")
```

**What it is:** Keeps the underside chamfer (the part that mates with the base profile for stacking) but replaces the overhanging sections with a straight wall. Same total height as normal lip, but no inward overhang.

**When to use:**
- **Easier to print** — no overhangs at all
- Still stacks with baseplates and other bins (the underside chamfer is retained)
- Printers with poor overhang performance
- Fast print profiles where quality on overhangs would suffer

**Trade-offs:** The interlocking "click" is slightly less pronounced. Stacking still works but the lateral retention is reduced compared to the full lip.

### No Lip (`lip_style="none"`)

```python
GridfinityBox(2, 2, 3, lip_style="none")
# or legacy syntax:
GridfinityBox(2, 2, 3, no_lip=True)
```

**What it is:** The top of the bin is a plain flat rim — no stacking lip profile at all. The bin height is the same (the lip height is replaced with straight wall), so interior volume is slightly larger.

**When to use:**
- Bins that will never be stacked
- When you need maximum interior height
- Bins used inside drawers where the drawer itself provides organization
- When paired with a custom lid or cover

**Trade-offs:** Cannot stack other bins on top. Bins may slide more easily on baseplates since there's no lip engaging with adjacent bins.

### Lip Style Comparison

| | Normal | Reduced | None |
|---|--------|---------|------|
| Stacks with bins above | Yes (full interlock) | Yes (partial) | No |
| Mates with baseplates | Yes | Yes | Yes |
| Overhangs to print | Yes (45°) | No | No |
| Interior volume | Standard | Standard | Slightly more |
| Print difficulty | Medium | Easy | Easiest |

---

## Feature Combinations

Most features can be combined freely. Here are some popular configurations:

### Workshop Organizer
```python
# Screw bins on magnetic baseplate, labeled, with scoops for easy access
GridfinityBaseplate(6, 4, magnet_holes=True, corner_screws=True)
GridfinityBox(2, 1, 3, holes=True, scoops=True, labels=True)
```

### Secure Transport
```python
# Magnet+screw baseplate for vibration-prone environments
GridfinityBaseplate(4, 3, magnet_holes=True, screw_holes=True)
GridfinityBox(2, 1, 5, holes=True, labels=True)
```

### Drawer Insert
```python
# No-lip bins in a drawer
GridfinityBaseplate(6, 3)
GridfinityBox(2, 1, 3, lip_style="none", length_div=3)
```

### Incompatible Combinations

| Combination | Why |
|-------------|-----|
| `lite_style=True` + `solid=True` | Contradictory concepts |
| `lite_style=True` + `holes=True` | Lite style has no elevated floor for holes |
| `lite_style=True` + `wall_th > 1.5` | Lite style enforces thin walls |

---

## Printing Guidelines

### Material Recommendations

| Material | Best for | Notes |
|----------|----------|-------|
| **PLA** | Most Gridfinity components | Stiff, easy to print, dimensionally accurate |
| **PETG** | Bins that see temperature changes | Slightly more flexible, better layer adhesion |
| **ABS/ASA** | Outdoor or high-temp environments | Requires enclosure, prone to warping on large baseplates |
| **TPU** | Soft-grip tool holders | Not suitable for baseplates or structural components |

### Print Settings

| Setting | Recommendation | Notes |
|---------|---------------|-------|
| Layer height | 0.2mm | 0.16mm for finer detail on lip profiles |
| Wall count | 2-3 | Sufficient for standard bins |
| Top/bottom layers | 4-5 | Solid base for bin floor |
| Infill | 15-25% | Higher for weighted/structural components |
| Supports | Usually not needed | Stacking lip prints at 45° which is within most printers' capability |

### Per-Feature Notes

- **Magnet holes:** Print with the baseplate top-side up. Holes face upward during printing and need no supports. Press magnets in after printing while the plastic is cool.
- **Stacking lip (normal):** The innermost overhang is the trickiest part. If it sags, switch to `lip_style="reduced"` or slow down the top few layers.
- **Large baseplates:** Print with a brim (5-10mm) to prevent corner lifting, especially with ABS/ASA.

---

## Glossary

| Term | Definition |
|------|-----------|
| **GU / Grid Unit** | 42mm — the fundamental Gridfinity dimension |
| **Height Unit** | 7mm — vertical grid increment |
| **Base profile** | The shaped cross-section (4.75mm tall) that allows bins to sit in baseplates |
| **Stacking lip** | The interlocking rim on top of bins that enables vertical stacking |
| **Receptacle** | The shaped pocket in a baseplate where a bin's base profile sits |
| **Lite style** | Economy bin with thinner walls and no elevated floor |
| **Solid ratio** | 0.0 to 1.0 — how much of a solid block's interior is filled |
| **Weighted** | Baseplate with pockets for inserting metal weights |

---

*This document covers features available in the cq-gridfinity STEP Generator. Features are sourced from 6 Perplexing Labs Gridfinity projects + cq-gridfinity upstream, all as independent CadQuery implementations. See LICENSE-COMPONENTS.md for per-module licensing.*
