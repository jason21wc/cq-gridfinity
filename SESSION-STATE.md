# Session State

**Last Updated:** 2026-08-13 (Spec conformance: stacking lip corrected)
**Memory Type:** Working (transient)
**Lifecycle:** Prune at session start per §7.0.4

> This file tracks CURRENT work state only.
> Historical information → PROJECT-MEMORY.md (decisions) or LEARNING-LOG.md (lessons)

---

## Current Position
- **Phase:** P3 (smkent rugged box) — steps 1–2 of 8 done. Interrupted by a
  spec-conformance detour that turned out to be load-bearing
- **Plan:** `documents/ROADMAP.md`
- **Blocker:** None

### 🔴 Stacking lip was 0.6mm off spec for two years — corrected 2026-08-13

Upstream's final 45° lip segment was **1.3mm**; the official drawings
(Stu142/Gridfinity-Documentation) specify **1.9mm**. Present since
cq-gridfinity's first commit (2023-11-09), one day *before* the drawings were
published, never revisited.

It survived 341 tests, `isValid()`, the B-Rep audit and a human CAD inspection
because the code was **internally consistent** — profile said 3.8, height
formula said 3.8. `constants.py` even contradicted itself in plain sight
(`GR_STACKING_LIP_H = 4.4` beside a profile summing to 3.8) with nothing
comparing them.

| | Nominal (drawings) | Actual (finished part) |
|---|---|---|
| Lip height | 4.4 | **3.5515** |
| Bin height | `7u + 4.4` | `7u + 3.5515` |
| kennetek `h_lip` | — | 3.548 → **agrees to 0.0035mm** |

`height` = construction (to the theoretical sharp apex, what drawings
dimension). `actual_height` = the finished part. Fillet lowers the apex by
exactly `r·√2`. Modes 2/3 compensate, so an explicit external height is
delivered exactly — this matters most for `as_lid()`.

**Found by asking what the rugged box uses for clearance** — an independent
consumer, corroborating from a different direction. Measuring the bin alone
never would have.


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

1. **Choose P2 or P3** — independent, either order:
   - **P2 divider objects** — smaller; replaces `length_div`/`width_div` integers,
     unlocks unequal compartments + notches + angled tops, folds `cylindrical` into a
     hole-grid modifier (removes a pipeline bypass), moves compatibility rules out of
     inline `raise ValueError` into declared metadata
   - **P3 rugged box** — the headline goal; new `gf_ruggedbox_smkent.py` (CC BY-SA)
2. **Finish DoD-5/DoD-6** — parameter purpose pass and granularity audit. Can run
   alongside either
3. **Wire `step_audit.py` into CI** — now calibrated against a human CAD verdict

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
