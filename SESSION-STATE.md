# Session State

**Last Updated:** 2026-08-15 (P3: integrated baseplate complete, 1E.4)
**Memory Type:** Working (transient)
**Lifecycle:** Prune at session start per §7.0.4

> This file tracks CURRENT work state only.
> Historical information → PROJECT-MEMORY.md (decisions) or LEARNING-LOG.md (lessons)

---

## Current Position
- **Phase:** P3 — smkent rugged box. Shell, both latches, seal and baseplate built; **1E.4 complete**
- **Plan:** `documents/ROADMAP.md`
- **Blocker:** None

### P3 progress — 6 of 8

| Item | Status |
|------|--------|
| Shell + parametric walls (1E.8) | ✅ 7 params, GF presets, lip land built, **border now included** |
| Clip latch (1E.1) | ✅ exact hulls, analytic |
| Draw latch (1E.2) | ✅ zero-interference mesh verified |
| Lip seal (1E.3) | ✅ 4 seal types, groove volume measured against material |
| **Integrated baseplate (1E.4)** | ✅ **complete — two booleans, `GridfinityBaseplate` reused, 3 STEPs audit-clean** |
| Third hinge (1E.6) | Next. Auto-activates at ≥5U width |
| Hinge end stops (1E.7) | Prevents the common printed-hinge failure |
| Per-part STEP export | Jason's request |

**Integrated baseplate (2026-08-15).** Four upstream styles ship as two booleans,
`baseplate_magnets` × `baseplate_skeletonized`, per the triage decision. Upstream's
fourth style — "thick", a full slab with no magnet holes — is deliberately
unreachable: pure ballast in a box whose point is being carried. `GridfinityBaseplate`
is reused rather than re-derived, exactly as upstream reuses kennetek's.

Two things are measured rather than asserted: the body gains **exactly** the plate's
volume (a coplanar union that fails to fuse leaves two solids `isValid()` still
passes), and the skeletonized plate is genuinely lighter than a full slab of the same
depth. The plate's pockets vent **upward** into the receptacle, so nothing becomes a
sealed void — `Shells() == 1`, checked against a control solid that does have one.

### 🔴 The interior was missing smkent's 5mm border — corrected 2026-08-15

`int_length` was `length_u * 42`. Upstream is:

```openscad
border = 5;
width  = Width  * l_grid + border;
```

Zero clearance for bins, and the baseplate — 4.0mm corner radius against the
cavity's 3.75mm — would have fouled all four corners. **Found only because the
baseplate had to fit inside it**, which is the same way the 0.6mm lip error
surfaced: an independent consumer asking what it may occupy.

This is the **third** transcription omission in the same module (`wall_thickness`
for `total_lip_thickness`, the absent lip land, now the absent border). All three
were in `rbox_size_adjustments()`-adjacent sizing, all three passed every test,
and all three were found by re-reading the source rather than the code.

**Lip seal + lip land (2026-08-15).** Building the seal exposed two *transcription*
errors — the checkable kind, found by re-reading the source:

1. `box_length`/`box_width` used `wall_thickness` where smkent uses
   `total_lip_thickness`. The box was **6mm undersized** in each direction.
2. **The lip land did not exist.** `total_lip_thickness` and `lip_height` were
   computed and tested, but no geometry consumed them — so 1E.8 was marked done when
   only the *parameters* were. The wall now holds 3.0mm, ramps over
   `lip_thickness × 1.5`, then holds 6.0mm for the top `lip_height`, matching
   smkent's `_box_wall_shape` cross-section. Built as a stepped interior void.

Lid default went 1U → 2U: a 1U lid is shorter than the lip profile itself
(ramp 4.5 + land 6.0 = 10.5mm), so its land never reached full thickness.

**Seal correctness is measured, not asserted.** Before the land existed a moulded
groove removed only a *quarter* of the ring — it would have leaked while looking
correct in CAD. Now wedge/square remove the entire ring from the body
(2320.7 of 2320.7) and the filament seal takes exactly half from each half
(930.3 × 2 = 1860.6 = πr²L). Both are asserted.

**Reusable primitive built:** `_hull_of_circles()` — exact 2D hull of circles
with unequal radii, arcs plus external tangent lines. OpenSCAD leans on `hull()`
constantly and CadQuery has none; `polygon().offset2D(r)` only covers the
equal-radius case. Verified tight, not merely containing.

**Deliberate divergence (agreed):** the grip is **lofted**, not the 10 stacked
polyhedra upstream uses. OpenSCAD cannot loft; the facets are a workaround, not
the design intent.


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

1. **Resume P3 at step 7 of 8 — third hinge (1E.6)**, then hinge end stops
   (1E.7) and per-part STEP export
2. **Assemble the draw latch about its pin joint** — parts are built and mesh
   with zero interference, but nothing yet poses them as a closed assembly
3. **DoD-5 remainder** — purpose/use-case docs for the ~35 pre-existing box
   parameters (the P2 additions are already documented)
4. **DoD-6** — clasp/latch granularity audit, 0.1mm steps, scoped to P3

**Before building 1E.4, re-read `_interior_void()` in `gf_ruggedbox_smkent.py`.**
The baseplate boolean lands on the same stepped void the lip land introduced.


## Open Items

- **Corner radius is the next thing to check in the same family — unverified.**
  Upstream passes `corner_radius = r_base` (kennetek's 4.0) to `rbox()`; ours
  hardcodes 3.75 inside and computes the outer as `3.75 + wall_thickness`, while
  every other outer dimension offsets by `total_lip_thickness`. That makes the
  corner ~7.2mm thick where the flats are 6.0mm. Whether `rbox()`'s
  `corner_radius` is the inner or outer radius was **not** confirmed — it needs
  `rugged-box-library.scad` read directly, which this session did not do
- **`documents/FEATURE-SPEC.md` 1E rows are stale.** 1E.1/1E.2/1E.3/1E.8 are built
  and tested but still read "Not Started". Only 1E.4 was updated, since marking
  work I did not verify this session would be guessing. Jason's call
- **Reduced lip has no rim taper** (found in double-check, pre-existing). Wall is
  a constant 2.60mm from the rim; normal tapers from 1.45mm. They are now the same
  height but do **not** stack interchangeably — recess openings differ ~1.15mm/side.
  See ROADMAP Known Remedies
- `isValid()` coverage audit (from the 1B gate)
- **Repo is still a fork** — PRs default to targeting michaelgale/cq-gridfinity.
  Detaching is a one-time GitHub support request; Jason's call
- Pred's rugged box clearance is a hardcoded `+3`, not derived from any lip
  constant. It works by ~2.8mm of margin rather than by design. Left alone
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
| Tests | **430 passed, 1 skipped, 0 xfailed** (~3m16s) |
| Quarantined failures | **None** — rugged box lid fixed 2026-08-11 |
| Ship set | 32 models, 32 audit-clean, DoD-3 human-verified |
| Local gate | `make check` (3m24s) via pre-push hook; `make check-full` |
| Triage | 42 features → 21 Keep, 21 Cut |
| Modules | 12 (added `gf_divider`, `gf_holegrid`, `gf_ruggedbox_smkent`) |


## Environment
- Conda env: `gridfinity` (activate with `conda activate gridfinity`)
- Python: 3.11.11 | CadQuery: 2.7.0 | cq-kit: 0.5.8
- pytest-xdist: default parallel (`-n auto --dist worksteal`); serial: `-o "addopts="` or `-n 0`
- Editable install: `pip install -e /Users/jasoncollier/Developer/gridfinity-generator`
