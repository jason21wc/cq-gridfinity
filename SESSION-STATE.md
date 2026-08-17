# Session State

**Last Updated:** 2026-08-16 (P3 CLOSED — DoD-3 verified; starting P4)
**Memory Type:** Working (transient)
**Lifecycle:** Prune at session start per §7.0.4

> This file tracks CURRENT work state only.
> Historical information → PROJECT-MEMORY.md (decisions) or LEARNING-LOG.md (lessons)

---

## Current Position
- **Phase:** **P4 — bin feature layers.** P3 closed 2026-08-16 with DoD-3 verified across all 21 models
- **Plan:** `documents/ROADMAP.md`
- **Blocker:** None

### P3 — CLOSED 2026-08-16

**The plan grew mid-session, deliberately.** Step 7 (third hinge) turned out to
be a *placement rule* for hinges that had never been built. The 1E list only ever
captured smkent's additions **over** a rugged box; this module was written from
scratch, so the base attachment layer never came with it. Jason dispositioned it
Keep as 1E.9-1E.13.

| Item | Status |
|------|--------|
| Shell + parametric walls (1E.8) | DONE - rebuilt; wall steps outward, chamfer + edge rounding |
| Clip latch (1E.1) | DONE - exact hulls, analytic, and now mountable |
| Draw latch (1E.2) | DONE - selectable, two printable parts, posed about the pin |
| Lip seal (1E.3) | DONE - 4 types, groove volume measured against material |
| Integrated baseplate (1E.4) | DONE - two booleans, `GridfinityBaseplate` reused |
| Stacking latches (1E.5) | DONE - side mounts reuse the latch boss unchanged |
| Third hinge (1E.6) | DONE - rule and geometry, activates at 5U |
| Hinge end stops (1E.7) | DONE - lower-knuckle tab, body only |
| Support ribs (1E.9) | DONE - side + rear, upstream placement |
| Attachment placement (1E.10) | DONE - shared latch/hinge framework |
| Screw eyelets (1E.11) | DONE - both drill sizes |
| Latch ribs (1E.12) | DONE - what the latches bolt to |
| Hinge ribs (1E.13) | DONE - interleaved, zero interference assembled |
| Per-part STEP export | DONE - `parts()`, `save_step_parts()`, `bom()` |

**Exit criteria:** watertight box, lid and both latch styles - MET (single-shell,
single-solid, 9 STEP exports audit clean). BOM documented - MET (`bom()`).
**DoD-3 human verification is NOT done** - nobody has opened these in CAD.

### The 3D hull question - RESOLVED, it was never 3D

`_box_latch_rib_base` and `_box_hinge_rib_body` hull a Z-extruded prism against
Y-axis eyelet cylinders. Both are prisms along Y over the SAME interval, so the
hull restricted to that slab is exactly the 2D hull of their XZ profiles swept
across it - a theorem about prisms, not an approximation. `_hull_of_circles`
does it, with prism corners passed as zero-radius circles. No divergence needed.

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

### 🔴 Eight sizing defects — six found by the next consumer, two by sweeping

The pattern is now the finding. Each defect was correct-looking, passed every
test, and surfaced only when something downstream needed the thing it depended on:

| # | Defect | Found by |
|---|--------|----------|
| 1 | Stacking lip 0.6mm off spec (2 years) | the rugged box asking for clearance |
| 2 | `wall_thickness` where source says `total_lip_thickness` | the seal |
| 3 | Lip land computed but never built | the seal |
| 4 | Interior missing the 5mm border | the baseplate |
| 5 | Outer heights: a 6U box held 41.35mm against a 45.55mm bin | a bin |
| 6 | Wall cross-section inverted — stepped inward, not outward | the ribs |
| 7 | `size_tolerance` reached no latch geometry — every part 0.4mm too wide | **the audit, not a consumer** |
| 8 | Clip latch missing `_round_shape(edge_radius)` on its profile | **the audit, not a consumer** |
| 9 | `_screw_hole` not centred: latch hole drilled beside its boss, boss left solid | the hinge pin test |
| 10 | Draw latch catch cut into TWO disconnected pieces — unprintable | wiring up `render_latch` |
| 11 | Stacking-latch screw count taken from the body for BOTH halves — lid had 2x the holes | **Jason, by eye in CAD** |

**#7 and #8 broke the pattern** — found by sweeping rather than by waiting.
Two sweeps, both in `documents/SHELL-AUDIT-1E8.md` Part 2: parameters with no
consumer (mechanical), and a term-by-term latch diff. #7 is the worst of the
eight in user terms: the knob our own docstring calls *"the one to reach for
when latches do not fit"* changed nothing but the filename.

**All eight are ours, not smkent's** — transcription errors against a source
that is self-consistent at every point checked. The one exception is not
smkent's either: the 0.6mm lip came from **cq-gridfinity**, our fork base.

**#6 is the one that forced a change of method.** See
`documents/SHELL-AUDIT-1E8.md`: the whole cross-section diffed against
`_box_wall_shape` in one pass instead of waiting for consumer number seven.
Three of its four findings are fixed; reinforced corners stays open as an
unadmitted feature.

Every one of these passed a test that measured the *parameter*, or measured a
quantity that was right in both the correct and the incorrect model. The wall
thickness was 3.00mm whichever surface moved.

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

**P4 — bin feature layers.** All Keep from triage, all independent of P3:

1. **Cullenect click-in labels (1D.3/1D.4)** — MIT, and a *real source* rather
   than dimensions only. Relabel by reprinting a 2g tile instead of a 6-hour bin
2. **Finger slide on any wall (1C.8)** — the current scoop is front-wall-only at
   a fixed radius. An upgrade to an existing slot, not a new feature
3. **Minimum lip (1C.7)** — drawer bins that never stack should not carry 6.6mm
   of interlock. Very low cost, one tuple
4. **Bottom size text (1C.16)** — answers "what size is this" when empty. **Must
   bundle a font** and use `fontPath`; never a system lookup

**Still open from P3, neither blocking:**
- **Reinforced corners** — Jason's disposition. Our corners are weaker than
  smkent's Gridfinity default until called
- **Nothing has been printed.** Fit asserted at 0.05-0.2mm

## Open Items

- ~~Corner radius~~ **checked and correct — closed 2026-08-15.** `rugged-box-library.scad:76`
  documents `corner_radius` as the **interior** radius, and line 544 computes
  `outer_radius = corner_radius + wall_thickness` — our formula exactly. The value
  matches too: smkent passes kennetek's `r_base`, which is `BASE_TOP_RADIUS = 7.5/2
  = 3.75`, the number we hardcode. Not every suspicion in this family is a defect
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
| Tests | **448 passed, 1 skipped, 0 xfailed** (~3m23s) |
| Quarantined failures | **None** — rugged box lid fixed 2026-08-11 |
| Ship set | P1: 32 models. Staged for DoD-3: 21 models (17 smkent + 4 core), all audit-clean |
| Local gate | `make check` (3m24s) via pre-push hook; `make check-full` |
| Triage | 42 features → 21 Keep, 21 Cut |
| Modules | 12 (added `gf_divider`, `gf_holegrid`, `gf_ruggedbox_smkent`) |


## Environment
- Conda env: `gridfinity` (activate with `conda activate gridfinity`)
- Python: 3.11.11 | CadQuery: 2.7.0 | cq-kit: 0.5.8
- pytest-xdist: default parallel (`-n auto --dist worksteal`); serial: `-o "addopts="` or `-n 0`
- Editable install: `pip install -e /Users/jasoncollier/Developer/gridfinity-generator`
