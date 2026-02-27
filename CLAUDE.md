# Gridfinity STEP Generator

## Project Overview
Fork-and-extend of `cq-gridfinity` (MIT, by Michael Gale) to cover the full Gridfinity ecosystem with native STEP file output via CadQuery/OpenCASCADE.

**Owner:** Jason — Senior Principal Manufacturing Engineer, Six Sigma MBB
**License:** MIT (matching upstream cq-gridfinity)
**Python:** 3.11+ | **Core deps:** CadQuery 2.0+, cq-kit

## Key Decisions (Do Not Revisit)
- **CadQuery over OpenSCAD** — decided; CadQuery produces exact B-Rep geometry (true STEP)
- **Fork cq-gridfinity, don't rewrite** — extend existing classes, add new modules alongside
- **No STL→STEP conversion** — not viable; generate native STEP from the start
- **Phase 1 = Library + CLI first** — no web UI until geometry library is solid
- **GPL caution** — ostat's `gridfinity_extended_openscad` is GPL; use as *specification reference only* (dimensions, feature behavior), write independent CadQuery code

## Architecture
```
cqgridfinity/              # Core library (from fork + extensions)
├── constants.py           # Gridfinity spec constants
├── gf_baseplate.py        # Baseplates (magnets, screws, weighted)
├── gf_box.py              # Bins (lip styles, dividers, scoops, labels)
├── gf_rugged_box.py       # Rugged box (existing upstream)
├── gf_drawer_spacer.py    # Drawer spacers (existing upstream)
└── gf_obj.py              # Base class for all Gridfinity objects
```

## Gridfinity Spec
See **GRIDFINITY-SPEC.md** for full dimensional reference (base profile, stacking lip, magnet/screw holes, weighted baseplate, etc.). Quick reference:
- Grid unit XY: 42.0 mm | Grid unit Z: 7.0 mm
- Base profile: 4.75mm tall, three-segment cross-section swept around rounded rect
- Stacking lip: 2.6mm wide x 4.4mm tall, 0.6mm fillet
- Magnet hole: 6.5mm dia x 2.4mm deep | Screw: 3.0mm dia
- Corner radius: 3.75mm (top), 0.8mm (bottom)
- Wall: 0.95mm min | Divider: 1.2mm | Internal fillet: 2.8mm

## Development Phases
1. **Phase 1 — Library + CLI** ← CURRENT
   - Fork cq-gridfinity, set up dev environment
   - Convert features from kennetek/gridfinity-rebuilt-openscad (MIT) to CadQuery
   - Only implement features that exist in kennetek or cq-gridfinity upstream
2. **Phase 2 — Local Web UI** (FastAPI + Three.js)
3. **Phase 3 — Deploy** (Docker, job queue, caching)

## OpenSCAD Source References
- **kennetek/gridfinity-rebuilt-openscad** (MIT) — primary geometry spec
- **ostat/gridfinity_extended_openscad** (GPL) — spec reference only, no code porting
- **smkent/monoscad** (CC BY-SA) — rugged box reference only

## Testing Strategy
- Each component gets a test file
- Verify: bounding box dims, valid solid (watertight), STEP export succeeds
- Use CadQuery measurement: `.val().BoundingBox()`, `.faces()`, `.edges()`
- Visual spot-checks in FreeCAD or Fusion 360

## Code Style
- Follow existing cq-gridfinity patterns and class hierarchy
- Python type hints on public APIs
- Docstrings on classes and public methods
- Keep modules focused — one component type per file

## Common CadQuery Patterns
- `hull()` → use `.loft()`, `.fillet()`, or manual convex construction
- `minkowski()` → use `.fillet()`, `.chamfer()`, or `.shell()`
- OpenSCAD `$fn` → not needed; CadQuery uses exact analytic geometry
