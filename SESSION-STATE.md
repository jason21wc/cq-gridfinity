# Session State

**Last Updated:** 2026-08-09 (Architecture review + full feature triage + re-sequenced roadmap)
**Memory Type:** Working (transient)
**Lifecycle:** Prune at session start per §7.0.4

> This file tracks CURRENT work state only.
> Historical information → PROJECT-MEMORY.md (decisions) or LEARNING-LOG.md (lessons)

---

## Current Position
- **Phase:** P1 in progress — ship set built and audited
- **Plan:** `documents/ROADMAP.md` (supersedes the old 1C–1F parity sequence)
- **Blocker:** **DoD-3 needs Jason** — open `~/Downloads/gridfinity-shipset/` in
  Shapr3D and Fusion 360. Everything else in P1 is unblocked

### P1 status

| Item | Status |
|------|--------|
| `tools/step_audit.py` | ✅ surface-type census; exits non-zero on flags (CI-ready) |
| `examples/scripts/generate_shipset.py` | ✅ 32 models, `--out` configurable |
| DoD-2 watertight | ✅ 32/32 |
| DoD-4 B-Rep quality | ✅ **32/32 clean, 0 flagged** — ~47–55% planar, balance in cylinders/cones/tori/spheres |
| **DoD-3 opens in CAD** | ⏳ **awaiting Jason** |
| DoD-5 / DoD-6 | Outstanding |

**Priority files to open:** `bin_2x2x6_scoop_label` (most-printed combo),
`bin_2x3x6_div2` (divider fillet intersections — carries sphere surfaces),
`baseplate_4x4_magnet` (repeated cylinders at scale), `ruggedbox_4x3x6`
(**19.8 MB, 5,468 faces** — may load slowly).

> The audit reports the rugged box *valid* despite the known non-watertight lid
> `xfail`. The assembly export likely does not surface the defect the way the unit
> test does. **Do not read that as clearing the xfail.**

## What Changed This Session

A fresh-eyes architecture review found the project's problem was **not** the code —
it was the plan. Three outcomes:

**1. Diagnosis corrected.** The working hypothesis was "we built a unique generator
per bin type." False for the code: `GridfinityBox` is already one class with ~35
composable kwargs and a staged `render()`. It was true of the *reference-model output*
(71 enumerated permutations) and of three real divergence points: `VaseBox` overriding
`render()` wholesale, `cylindrical` mode bypassing the pipeline, and compatibility
rules scattered as inline `raise ValueError`.

**2. Stop Rule added** (`CLAUDE.md`). Feature traceability was an admission gate with
no demand gate — the matrix could only grow. Rows now carry `Keep`/`Cut`/`Triage`;
only `Keep` may be built; disposition is Jason's call; upstream parity is explicitly
not a goal.

**3. Full triage done.** All 42 bolt-on features from ostat/smkent/yawkat/Cullenect/
anylid dispositioned in 8 batches → **21 Keep, 21 Cut**. See
`documents/FEATURE-TRIAGE.md`.

## Phase 1B — CLOSED (2026-08-09)

- 230 passed, 1 skipped, 1 xfailed in 138.57s
- One checklist item closed as *partial*, not ticked: `isValid()` coverage is
  substantial but not universal (`test_box.py` 29 renders vs 20 assertions). Audit
  carried into P1

## Key Decisions

| # | Decision |
|---|----------|
| D1–D3 | **smkent is the flagship rugged box** — new module `gf_ruggedbox_smkent.py`, CC BY-SA 4.0. Pred's `gf_ruggedbox.py` stays as-is (CC BY-**NC**-SA, non-commercial only, cannot be extended without inheriting NC) |
| D4 | Top interface stays a **pure profile swap** — sliding lid was cut, so no wall-modifier widening needed |
| D5 | **Every feature ships with a stated purpose/use case** in docs |
| D6 | **STEP output is the differentiator, not feature breadth** — Perplexing Labs already ships a polished web generator on smkent's box, with STL output |
| D7 | **Fine dimensional granularity is a first-class requirement** — floats everywhere, ≤0.1mm on fit-critical dims, 0.05mm for press/sliding fits. Perplexing Labs' 1mm latch increments are a real observed weakness; shrinkage corrections are 0.04–0.18mm |

## Next Actions

1. **Start P1** — ship set generator (~35 models), then **DoD-3: open STEP files in
   Shapr3D and Fusion 360.** Never verified to date and it is the whole premise
2. **Build `tools/step_audit.py`** — surface-type census (real B-Rep stores a magnet
   hole as one cylindrical face; tessellation stores it as hundreds of planar facets).
   Automates DoD-4; run over the ship set in CI
3. **Then P2** (divider objects) or **P3** (rugged box) — independent; P2 recommended
   first as it is smaller and unlocks P4

## Open Items

- `isValid()` coverage audit (from the 1B gate)
- Wall/floor patterns deferred, not permanently cut — revisit only on demonstrated
  need. B-Rep cost (face count, fillet interaction) is unmeasured
- Wall cutouts (1C.11) cut *for now* — cheap to revisit after P2, since collision
  checks against divider objects are far simpler than against two integers
- Magnet-free retention: Clickfinity/CLICKbase have the better architecture
  (baseplate-only, grips stock bins) but are **STL-only with no open-source license**.
  ClickGroove (MIT) is what we can legally build

## Quick Reference

| Metric | Value |
|--------|-------|
| Tests | **230 passed, 1 skipped, 1 xfailed** (138.57s) |
| xfail | Rugged box lid non-watertight (pre-existing upstream) |
| Phase 1B | **CLOSED** — 17/17 Verified |
| Triage | 42 features → 21 Keep, 21 Cut |
| LOC | ~4,900 across 9 modules |

## Environment
- Conda env: `gridfinity` (activate with `conda activate gridfinity`)
- Python: 3.11.11 | CadQuery: 2.7.0 | cq-kit: 0.5.8
- pytest-xdist: default parallel (`-n auto --dist worksteal`); serial: `-o "addopts="` or `-n 0`
- Editable install: `pip install -e /Users/jasoncollier/Developer/gridfinity-generator`
