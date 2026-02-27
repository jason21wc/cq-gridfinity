# Gridfinity STEP Generator

## Project Overview
Fork-and-extend of `cq-gridfinity` (MIT, by Michael Gale) to cover the full Gridfinity ecosystem with native STEP file output via CadQuery/OpenCASCADE.

**Owner:** Jason — Senior Principal Manufacturing Engineer, Six Sigma MBB
**License:** MIT (core) + per-module (see `LICENSE-COMPONENTS.md`)
**Python:** 3.11+ | **Core deps:** CadQuery 2.0+, cq-kit

## Key Decisions (Do Not Revisit)
- **CadQuery over OpenSCAD** — decided; CadQuery produces exact B-Rep geometry (true STEP)
- **Fork cq-gridfinity, don't rewrite** — extend existing classes, add new modules alongside
- **No STL→STEP conversion** — not viable; generate native STEP from the start
- **Phase 1 = Library + CLI first** — no web UI until geometry library is solid
- **GPL caution** — ostat's `gridfinity_extended_openscad` is GPL; use as *specification reference only* (dimensions, feature behavior), write independent CadQuery code
- **Per-module licensing** — see `LICENSE-COMPONENTS.md` (MIT core, CC BY-NC-SA 4.0 ruggedbox, etc.)

## Architecture
```
cqgridfinity/
├── __init__.py                    # Updated exports
├── constants.py                   # Gridfinity spec constants
├── gf_obj.py                      # Base class (extensible filename())
├── gf_baseplate.py                # Baseplates (magnets, screws, weighted)
├── gf_box.py                      # Bins (lip styles, dividers, scoops, labels)
├── gf_ruggedbox.py                # Pred rugged box (CC BY-NC-SA 4.0)
├── gf_drawer.py                   # Drawer spacers (existing upstream)
├── gf_helpers.py                  # Geometry helpers
├── gf_holes.py                    # Hole type library (shared by baseplates + bins)
├── patterns/                      # Wall/floor pattern system (planned)
├── lids/                          # Lid systems (planned)
├── labels/                        # Label systems (planned)
├── holders/                       # Item holders (planned)
├── drawers/                       # Drawer system (planned)
├── gridflock/                     # Segmented baseplates (planned)
└── scripts/                       # CLI scripts
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
   - 1A: Foundation (licensing, refactoring, docs) — DONE
   - 1B: Kennetek feature parity (enhanced holes, bins, baseplates, vase)
   - 1C: Extended features (patterns, lip variants, subdivisions, text)
   - 1D: Accessories (lids, labels, holders, drawers, trays)
   - 1E: Rugged box expansion (smkent variant)
   - 1F: GridFlock segmented baseplates
2. **Phase 2 — Local Web UI** (FastAPI + Three.js)
3. **Phase 3 — Deploy** (Docker, job queue, caching)

## In-Scope Projects (6 + upstream)
- **kennetek/gridfinity-rebuilt-openscad** (MIT) — primary geometry spec
- **ostat/gridfinity_extended_openscad** (GPL) — spec reference ONLY, no code porting
- **smkent/monoscad** (CC BY-SA 4.0) — rugged box variant
- **yawkat/gridflock** (MIT) — segmented baseplates
- **rngcntr/anylid** (license TBD) — universal click-lock lids
- **CullenJWebb/CullenectLabels** (MIT) — click-in swappable labels
- **cq-gridfinity** (MIT) — upstream base

## Deferred to Future Phase
- OpenGrid (28mm grid, not Gridfinity-native)
- Underware (cable management, not Gridfinity-native)
- Voronoi patterns (needs scipy)
- Thumbscrew holes (computationally expensive)

## Governance Rules (MUST FOLLOW)
- **Feature Traceability:** Every feature MUST have a row in `documents/FEATURE-SPEC.md` with an upstream source before implementation begins. No row = no implementation.
- **No Invented Features:** Do NOT create features that don't exist in any upstream project. If you think something should exist, flag it — don't build it.
- **Verify Before Implementing:** If a feature's source file says `[needs verify]`, read the actual upstream source to confirm the feature exists and note the specific file/function before writing code.
- **Phase Gate Validation:** Before starting a new phase, confirm all features in that phase pass the gate checklist in `documents/FEATURE-SPEC.md`.
- **Out of Scope:** Check the Out of Scope list in `documents/FEATURE-SPEC.md` before implementing anything not in the matrix.
- **GPL Isolation:** ostat code is GPL. Read dimensions/behavior only. Write independent CadQuery code. Never translate, port, or adapt ostat code.

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
