# Project Memory

**Project:** Gridfinity STEP Generator
**Started:** 2026-02-22
**Mode:** Standard
**Memory Type:** Semantic (accumulates)
**Lifecycle:** Prune when decisions superseded

> Preserves significant decisions and rationale.
> Mark superseded decisions with date and replacement link.

---

## Specification Summary

- **Problem:** No Gridfinity generator produces native STEP files (only STL or OpenSCAD)
- **Users:** Makers, engineers, designers who need editable Gridfinity geometry for CAD workflows
- **Core Features:** Baseplates, bins, rugged boxes, lids, labels, patterns, segmented baseplates — all as STEP
- **Out of Scope:** See `documents/FEATURE-SPEC.md` § Out of Scope

## Calibration

| Question | Answer | Implication |
|----------|--------|-------------|
| Novelty | PARTIALLY — CadQuery + Gridfinity is adapted from existing OpenSCAD generators | Use established patterns where they exist |
| Requirements Certainty | HIGH — upstream OpenSCAD code defines exact geometry | Specs are concrete, minimal ambiguity |
| Stakes | MEDIUM — production tool, real users, open-source | Standard quality gates |
| Longevity | LONG-TERM — multi-year maintenance | Invest in architecture and testing |
| **Mode** | **Standard** | Full specification components, phase gates, traceability |

## Decisions Log

| Date | Decision | Rationale | Status |
|------|----------|-----------|--------|
| 2026-02-22 | Fork cq-gridfinity, don't rewrite | 60-70% coverage already done, MIT license, tedious base geometry already implemented | Final |
| 2026-02-22 | CadQuery over OpenSCAD | Native B-Rep STEP output, exact analytic geometry vs polygon mesh | Final |
| 2026-02-22 | GPL isolation for ostat code | Use as spec reference only, write independent code | Final |
| 2026-02-22 | Phase 1 library-first approach | Geometry must be correct before wrapping in UI | Final |
| 2026-02-26 | Per-module licensing | Different upstream sources have different licenses; track in LICENSE-COMPONENTS.md | Final |
| 2026-02-26 | Expand scope to 6 Perplexing Labs projects | Cover full Gridfinity ecosystem, not just kennetek | Final |
| 2026-02-26 | Extensible filename() pattern | Subclasses override `_filename_prefix`/`_filename_suffix()` instead of isinstance chains | Final |
| 2026-02-26 | Shared gf_holes.py module | Hole geometry shared by baseplates and bins; foundation for enhanced hole types | Final |
| 2026-02-26 | Feature Traceability Spec | Every feature must trace to upstream source; prevents AI-invented scope creep | Final |
| 2026-02-26 | Standard governance mode | Based on calibration: PARTIALLY novel, HIGH certainty, MEDIUM stakes, LONG-TERM | Final |
| 2026-02-28 | Test suite optimization: xdist + fillet-skip | 734s→82s (9x). Topology tests keep full fillets (@slow). OBB acceleration abandoned (8% slower). | Final |

## Technical Stack

- **Language:** Python 3.11+
- **CAD Kernel:** CadQuery 2.0+ (wraps OpenCASCADE via OCP)
- **Helpers:** cq-kit 0.5.8
- **Testing:** pytest + pytest-xdist (parallel, `-n auto --dist worksteal`)
- **Output:** STEP (primary), STL, SVG
- **Environment:** Conda (`gridfinity` env)

## Constraints & Standards

- **Licensing:** MIT for core; CC BY-NC-SA 4.0 for Pred ruggedbox; see LICENSE-COMPONENTS.md
- **GPL isolation:** ostat code is GPL — dimensional spec reference only, no code porting
- **Dependencies:** CadQuery 2.0+, cq-kit, Python 3.11+
- **OpenCASCADE:** Heavy dependency (~500MB+), affects Docker image size in Phase 3
- **Performance:** Complex models may take 30-60s to generate; full test suite ~82s parallel, ~373s serial
- **Traceability:** Every feature must have a row in `documents/FEATURE-SPEC.md` with upstream source

## Key Artifacts

| Artifact | Location | Status |
|----------|----------|--------|
| Feature Specification | `documents/FEATURE-SPEC.md` | Active |
| Upstream Reference | `documents/UPSTREAM-REFERENCE.md` | Active |
| Dimensional Reference | `GRIDFINITY-SPEC.md` | Stable |
| Component Licenses | `LICENSE-COMPONENTS.md` | Active |
| Product Guide | `PRODUCTS.md` | Active |
| Learning Log | `LEARNING-LOG.md` | Active |
| Session State | `SESSION-STATE.md` | Active |

## Key Upstream References

- **cq-gridfinity:** github.com/michaelgale/cq-gridfinity (v0.5.7, Nov 2024, MIT)
- **kennetek:** github.com/kennetek/gridfinity-rebuilt-openscad (MIT) — primary spec
- **ostat:** github.com/ostat/gridfinity_extended_openscad (GPL) — spec reference only
- **smkent:** github.com/smkent/monoscad (CC BY-SA 4.0) — rugged box variant
- **yawkat:** github.com/yawkat/gridflock (MIT) — segmented baseplates
- **rngcntr:** anylid (license TBD) — universal click-lock lids
- **CullenJWebb:** Cullenect-Labels (MIT) — click-in swappable labels

## Known Gotchas

| # | Issue | Solution |
|---|-------|----------|
| 1 | **AI scope creep** — Previous sessions invented features (lids, cutouts, item holders, trays, drawers) not from any upstream source, requiring multiple reverts | Every feature must trace to `documents/FEATURE-SPEC.md`. If no row exists, do not implement. If source says `[needs verify]`, verify before implementing. |
| 2 | **Coplanar face boolean failure** — OpenCASCADE silently fails when cutting solids share an exact face | Offset cutting tool by EPS (1e-5) past shared face |
| 3 | **extrude_profile extends shape, not slab** — Adding ext_depth to profile extends receptacle, doesn't add solid below | Keep standard profile; outer block provides solid slab |
| 4 | **GPL contamination risk** — ostat's code is GPL; any code porting creates license obligation | Read dimensions and behavior only; write independent CadQuery code |
| 5 | **CadQuery XZ workplane direction** — `Workplane("XZ").extrude(h)` goes -Y (counterintuitive) | Always verify with `.val().BoundingBox()` |
| 6 | **Silent kwargs swallowing** — `for k,v in kwargs` with no else branch hides typos (e.g., `hole=True` vs `holes=True`) | All kwargs loops must `warnings.warn()` on unknown keys |
| 7 | **Temporary self-mutation without try/finally** — Methods that mutate then restore `self` attributes corrupt state on exception | Wrap in try/finally; save originals before the try block |
| 8 | **Shared utility bypass** — Creating a shared function but leaving some callers using inline implementations | When creating a shared utility, refactor ALL callers in the same PR |

## Phase Gates

### Phase 1A: Foundation — COMPLETE (2026-02-26)

| Gate | Status | Date | Notes |
|------|--------|------|-------|
| Licensing setup | Passed | 2026-02-26 | LICENSE-COMPONENTS.md, ruggedbox attribution |
| Architecture refactor | Passed | 2026-02-26 | Extensible filename(), shared gf_holes.py |
| Docs updated | Passed | 2026-02-26 | All project docs reflect new scope |
| Tests passing | Passed | 2026-02-26 | 28/28 pass |
| Governance setup | Passed | 2026-02-26 | Feature spec, calibration, phase gates |

### Phase 1B: Kennetek Feature Parity — IN PROGRESS

| Gate | Status | Date | Notes |
|------|--------|------|-------|
| Feature spec verified | Passed | 2026-02-26 | All `[needs verify]` resolved for 1B features |
| 1B.1-1B.4 Enhanced holes | Verified | 2026-02-28 | crush ribs, chamfered, refined, printable top — now on baseplates AND bins |
| 1B.5-1B.8 Bin features | Verified | 2026-02-28 | scoop scaling, tab positioning, custom depth, cylindrical |
| 1B.9 Skeletonized baseplate | Verified | 2026-02-28 | 16 tests, 4 corner pocket cutouts per cell, cross ribs |
| 1B.10-1B.11 Baseplate features | Verified | 2026-02-28 | screw-together, fit-to-drawer |
| 1B.12-1B.15 Grid flexibility | Pending | — | non-integer, half-grid, height modes, Z-snap |
| 1B.16-1B.17 Spiral vase | Pending | — | shell + base insert |
| Implement -> Complete | Pending | — | All 1B features pass acceptance |

### Phase 1C-1F: See documents/FEATURE-SPEC.md

### Phase 2: Local Web UI — DEFERRED
Deferred until Phase 1 library is feature-complete. No UI work until geometry is solid.

### Phase 3: Deploy — DEFERRED
Deferred until Phase 2 web UI exists. Docker image size (~500MB+ for OpenCASCADE) requires planning.
