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
├── gf_vase.py                     # Spiral vase shell + base insert (1B.16-17)
├── shims/                         # Compatibility shims
└── scripts/                       # CLI scripts (gridfinitybox, gridfinitybase, ruggedbox)
```

**Planned modules** (per `documents/ROADMAP.md` — none exist yet):
```
gf_divider.py                      # Divider objects — P2 (unequal, notches, angled tops)
gf_ruggedbox_smkent.py             # smkent rugged box, CC BY-SA 4.0 — P3
gf_labels.py                       # Cullenect click-in labels, MIT — P4
gf_gridflock.py                    # Segmentation + connectors + ClickGroove, MIT — P5
```

```
examples/
├── scripts/                       # Generator scripts (committed to git)
│   ├── generate_1a_reference.py   # Phase 1A (features 0.1-0.20)
│   ├── generate_1b_reference.py   # Phase 1B (features 1B.5-1B.17, all Kennetek)
│   └── generate_{phase}_reference.py  # One script per phase going forward
├── output/                        # Generated STEP files (gitignored — regenerate freely)
│   └── .gitkeep                   # Preserves empty dir in git
└── demo1.assy                     # PartCAD assembly demo (committed)
```

## Examples Convention
- **Scripts live in `examples/scripts/`** — committed, one file per phase
- **Output goes to `examples/output/`** — gitignored, regenerate any time with the scripts
- **Naming:** `{Phase}_{FeatureNum}_{descriptor}_{dimensions}.step`
  - Example: `1B16_vase_2x2x3.step`, `1B09_skeleton_mag_4x3.step`
- **Never create ad-hoc subfolders** in `examples/` (e.g., `review_xyz/`) — use `output/` instead
- **Run scripts from project root:** `conda run -n gridfinity python examples/scripts/generate_1b_reference.py`

## Gridfinity Spec
See **GRIDFINITY-SPEC.md** for full dimensional reference (base profile, stacking lip, magnet/screw holes, weighted baseplate, etc.). Quick reference:
- Grid unit XY: 42.0 mm | Grid unit Z: 7.0 mm
- Base profile: 4.75mm tall, three-segment cross-section swept around rounded rect
- Stacking lip: 2.6mm wide x 4.4mm tall, 0.6mm fillet
- Magnet hole: 6.5mm dia x 2.4mm deep | Screw: 3.0mm dia
- Corner radius: 3.75mm (top), 0.8mm (bottom)
- Wall: 0.95mm min | Divider: 1.2mm | Internal fillet: 2.8mm

## Development Phases

> **Authoritative plan: `documents/ROADMAP.md`.** The old parity-ordered sequence
> (1C → 1D → 1E → 1F) is **retired**. Phases were re-ordered by user value after a
> full feature triage. **Do not start "Phase 1C" — it no longer exists.**

- **1A** — Foundation (licensing, refactoring, docs) — DONE
- **1B** — Kennetek feature parity — **CLOSED 2026-08-09** (17/17 Verified)
- **P0** — Close 1B, reconcile docs ← CURRENT
- **P1** — Foundation hardening + ship the common set (proves the STEP premise)
- **P2** — Divider objects (the one targeted refactor)
- **P3** — Rugged box, smkent flagship (`gf_ruggedbox_smkent.py`, CC BY-SA)
- **P4** — Bin feature layers (labels, finger slide, min lip, bottom text)
- **P5** — Baseplate completion (segmentation, connectors, ClickGroove)
- **P6** — Web UI (FastAPI + Three.js), then deploy

**Why the change:** phases were ordered by upstream-project parity, which put the
rugged box (a headline goal) behind wall patterns and label variants. Parity is not
a goal — see the Stop Rule.

## In-Scope Projects (6 + upstream)
- **kennetek/gridfinity-rebuilt-openscad** (MIT) — primary geometry spec
- **ostat/gridfinity_extended_openscad** (GPL) — spec reference ONLY, no code porting
- **smkent/monoscad** (CC BY-SA 4.0) — rugged box variant
- **yawkat/gridflock** (MIT) — segmented baseplates
- **rngcntr/anylid** (license TBD) — universal click-lock lids
- **CullenJWebb/Cullenect-Labels** (MIT) — click-in swappable labels
- **cq-gridfinity** (MIT) — upstream base

## Deferred to Future Phase
- OpenGrid (28mm grid, not Gridfinity-native)
- Underware (cable management, not Gridfinity-native)
- Voronoi patterns (needs scipy)
- Thumbscrew holes (computationally expensive)

## Governance Rules (MUST FOLLOW)
- **Feature Traceability:** Every feature MUST have a row in `documents/FEATURE-SPEC.md` with an upstream source before implementation begins. No row = no implementation.
- **Prefer Existing Over Custom:** Use established standards, libraries, and upstream
  implementations when they exist. Custom work is allowed — but only after saying, out
  loud, what already exists that we could borrow instead, and why we are not.
  - Before building: search for an upstream repo, library, or standard that covers it.
  - If one exists → use it, or state explicitly why we are not (license, quality, fit).
  - If none exists → say so plainly, then build it. Custom is a legitimate outcome,
    not a rule violation.
  - **The failure mode is silence**, not custom code. Never quietly reinvent something
    that already exists, and never present a custom design as if no alternative
    was available.

  **Governance basis:** `coding-quality-supply-chain-solution-integrity` (Supply Chain
  & Solution Integrity — "The Dependency Verification Act"), failure mode **A5:
  Hallucinated or Unnecessary Custom Implementation**. Also **A4: Hallucinated
  Dependencies** — verify a source actually exists and is what you think before
  depending on it. Applied here to upstream designs, not just packages: smkent's
  CC BY-SA license was confirmed on GitHub rather than trusted from our own notes,
  and Clickfinity was rejected after checking that no open-source license exists.

  > **History:** this rule previously read *"Do NOT create features that don't exist
  > in any upstream project — flag it, don't build it."* That absolute prohibition
  > was project-local (added 2026-02-26, `0eddd45`) and stricter than the governance
  > principle it derived from. It caused a legitimate feature request to be refused
  > rather than scoped. Corrected 2026-08-11. **When a local rule blocks something,
  > check it against ai-governance before treating it as binding.**
- **Verify Before Implementing:** If a feature's source file says `[needs verify]`, read the actual upstream source to confirm the feature exists and note the specific file/function before writing code.
- **Phase Gate Validation:** Before starting a new phase, confirm all features in that phase pass the gate checklist in `documents/FEATURE-SPEC.md`.
- **Out of Scope:** Check the Out of Scope list in `documents/FEATURE-SPEC.md` before implementing anything not in the matrix.
- **GPL Isolation:** ostat code is GPL. Read dimensions/behavior only. Write independent CadQuery code. Never translate, port, or adapt ostat code.

### The Stop Rule (admission ≠ obligation)

Feature Traceability is an **admission gate**, not a work queue. A row in
`documents/FEATURE-SPEC.md` grants *permission* to build a feature. It does not
create an *obligation* to build it, and it is not evidence that the feature should exist
in this project.

Every feature must pass **both** gates before implementation:

| Gate | Question | Fails if |
|------|----------|----------|
| **Admission** (existing) | Does it trace to a verified upstream source? | No row, or `[needs verify]` unresolved |
| **Demand** (new) | Would a real user reach for this, and has Jason kept it in triage? | Status is `Cut`, or `Triage` (undecided) |

**Rules:**
1. **Upstream parity is not a goal.** Covering 100% of another project's option list is
   explicitly NOT the objective. Cover what gets used; cut the rest.
2. **Every matrix row carries a Disposition:** `Keep` · `Cut` · `Triage`. Only `Keep`
   rows may be implemented. `Cut` rows stay in the matrix with a one-line reason — the
   record of a deliberate decision is worth more than a deleted row.
3. **Disposition is Jason's call, not Claude's.** Claude proposes a ranking and a
   rationale; Jason decides. Never promote a row from `Triage` to `Keep` autonomously.
4. **Cut is the default for undecided work.** A row sitting in `Triage` at a phase gate
   does not block the gate — it is simply not built.
5. **Adding a row requires a use case**, not just an upstream source. State who wants
   it and why in the Rationale column.
6. **Blocked ≠ deferred.** A feature whose license is unresolved (e.g. anylid) is `Cut`
   until the license is resolved, not carried as pending work.

**Governance basis:** Art. I §5 (Discovery Before Commitment — reassess at milestones),
Art. III §1 (Verification & Validation — define success before starting).

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

## Memory (Cognitive Types)

| Type | File | Purpose |
|------|------|---------|
| Working | SESSION-STATE.md | Current position, next actions |
| Semantic | PROJECT-MEMORY.md | Decisions, constraints, phase gates |
| Episodic | LEARNING-LOG.md | Lessons learned, CadQuery patterns |
| Structural | GRIDFINITY-SPEC.md | Dimensional reference |
| Spec | documents/FEATURE-SPEC.md | Feature traceability matrix |
