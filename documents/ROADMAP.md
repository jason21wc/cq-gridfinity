# Roadmap — Re-sequenced

**Created:** 2026-08-09
**Supersedes:** the phase plan in `CLAUDE.md` (1A → 1B → 1C → 1D → 1E → 1F)
**Companion:** `documents/FEATURE-TRIAGE.md` (what we build and why), `CLAUDE.md` Stop Rule

---

## 1. Purpose

**Generate native B-Rep STEP files for the Gridfinity ecosystem.**

The ecosystem is mature and well served for mesh output. Perplexing Labs ships a
polished parametric web generator with live 3D preview covering Gridfinity Rebuilt,
Extended, Rugged Box, GRIPS, and openGrid — **and it outputs STL**. So does every
other generator.

**The gap is the format, and it holds against the best in the ecosystem.**

Two consequences that shape everything below:

1. **Feature breadth is not the differentiator and never was.** We will not win a
   feature-count race against ostat or Perplexing Labs, and we do not need to.
2. **Anything that degrades B-Rep quality costs more here than elsewhere.** Face-count
   explosion, fillet failures, and non-watertight solids attack the actual value
   proposition. This is why wall patterns were deferred — see `FEATURE-TRIAGE.md`.

### Why the old sequence was wrong

The previous plan ordered phases by **upstream-project parity**: 1B = Kennetek
parity, 1C = ostat extended features, 1E = rugged box, 1F = GridFlock. That
guaranteed we would build `fit-to-drawer align-left` and `z-snap` before building
the rugged box — which is a headline goal.

Parity is not a goal (see Stop Rule). **The new sequence is ordered by user value.**

---

## 2. Definition of Done

The old plan measured feature counts and reference-model counts. Those are production
volume, not value. Project-level success criteria, defined before execution per
Art. III §1:

| # | Criterion | How verified |
|---|-----------|--------------|
| DoD-1 | A user can generate the common Gridfinity parts from one command | CLI produces the full ship set (§4) |
| DoD-2 | Every generated solid is watertight | `isValid()` on every ship-set model in CI |
| DoD-3 | **STEP files open cleanly in real CAD** | Manual check in **Shapr3D** and **Fusion 360** (Jason's tools), ≥1 per category. FreeCAD as a free-tool sanity check. *Never verified to date* |
| DoD-4 | Geometry is B-Rep, not dense tessellation | **Automated** — surface-type census per model (see below), plus face count and file size |
| DoD-5 | Every parameter documents *why you'd choose it* | Doc review — no parameter ships without a use case |
| DoD-6 | Fit-critical dimensions adjust in ≤0.1mm steps | Parameter audit against D7 |

**DoD-3 is the most important and the most neglected.** The entire premise is
"editable CAD geometry." Nothing to date has tested that claim in the CAD packages
users actually run.

### Automating the B-Rep quality check (DoD-4)

Most of "is this real CAD geometry?" is machine-checkable with tooling already
installed — no plugin or external service required. OCP/OpenCASCADE can introspect a
STEP file directly:

```python
from OCP.BRepAdaptor import BRepAdaptor_Surface
# classify every face: PLANE / CYLINDER / CONE / SPHERE / TORUS / BSPLINE ...
```

**The surface-type census is the definitive test.** Genuine B-Rep represents a magnet
hole as *one cylindrical face*. Tessellated geometry wearing a STEP extension
represents it as *hundreds of tiny planar facets*. The distinction is unambiguous and
needs no human eye.

Build `tools/step_audit.py` in P1 to report per model: solid count, `isValid()`,
closed/watertight, face and edge counts, **surface-type histogram**, bounding box,
and file size. Run it over the whole ship set in CI; flag any model where planar
faces dominate a feature that should be curved.

**What still needs a human:** whether Shapr3D or Fusion *imports* it without
complaint, and whether the resulting body is pleasant to edit. Automate the objective
half; eyeball the rest.

---

## 3. Phase Sequence

| Phase | Goal | Depends on |
|-------|------|------------|
| **P0** | Close Phase 1B | — |
| **P1** | Foundation hardening + ship the common set | P0 |
| **P2** | Divider objects (the one targeted refactor) | P1 |
| **P3** | Rugged box — smkent flagship | P1 |
| **P4** | Bin feature layers | P2 |
| **P5** | Baseplate completion | P1 |
| **P6** | Web UI | P1–P5 |

P2 and P3 are independent and may run in either order. **Recommended: P2 first** —
it is much smaller, and it unlocks P4. If the rugged box is the priority you want
moving, swap them; nothing breaks.

---

### P0 — Close Phase 1B

Status: gate is passing but was never formally closed, and P1C work was queued
behind it anyway. Honor the gate.

- [x] All tests pass — **230 passed, 1 skipped, 1 xfailed** (138s, 2026-08-09)
- [x] xfail justified — rugged box lid non-watertight, pre-existing upstream
- [ ] Mark 1B Exit Gate complete in `FEATURE-SPEC.md`
- [ ] Reconcile `FEATURE-SPEC.md` rows with `FEATURE-TRIAGE.md` dispositions
- [ ] Update `CLAUDE.md` phase plan to point at this roadmap
- [ ] Fix doc drift: `CLAUDE.md` architecture tree lists six directories that do not
      exist (`patterns/`, `lids/`, `labels/`, `holders/`, `drawers/`, `gridflock/`)

---

### P1 — Foundation Hardening

**Goal:** cq-gridfinity fully operational, documented, and shipping the common set.
This is the phase that tests the purpose statement for the first time.

Per Jason: *"build out cq-gridfinity completely and fully operational for testing and
using as the stable foundation for the rest."*

**Scope**
1. **Ship set generator** — one command emits §4, all validated watertight
2. **DoD-3 verification** — open representative STEP files in FreeCAD and Fusion 360.
   Record findings. If B-Rep quality is poor, that is the highest-priority bug in the
   project
3. **Document the solid-bin lid** — `GridfinitySolidBox` is the community-standard lid
   and already works. It needs documenting, not building
4. **Parameter documentation pass** — every parameter gets purpose and use case (D5):
   why thin wall vs standard, why lite style, why a reduced lip, why raise a floor
5. **Granularity audit** (D7) — confirm all fit-critical dimensions accept floats and
   nothing quantizes input
6. **Prune reference models** — 71 generated models is enumerated output, not a
   product. Cut list (carried forward from the pre-triage session analysis):

   | Model | Reason |
   |-------|--------|
   | `0.15_baseplate_mag-screw` | Magnets vs. screws is pick-one in practice |
   | `1B09_skeleton_mag-screw` | Same |
   | `1B10_screw-together_n2` | `n_screws` is a parameter; no visual difference |
   | `0.02_baseplate_ext-depth` | Rare; most users never need it |
   | `1B11_fit-to-drawer_align-left` | Alignment is one parameter; one model proves it |
   | `1B11_fit-to-drawer_align-right` | Same |

   **Keep:** plain / skeleton / weighted (three genuinely different structures),
   magnets and screws separately (two anchoring philosophies, visually distinct),
   screw-together (plates join each other, not a surface), one fit-to-drawer,
   corner screws (surface mounting, distinct from cell anchoring).

**Exit criteria:** DoD-1 through DoD-6 pass for the ship set.

**Explicitly not in scope:** new geometry features. P1 adds no capability. It makes
what exists usable and proves the premise.

---

### P2 — Divider Objects (targeted refactor)

**Goal:** replace `length_div` / `width_div` integers with divider objects.

**The driver is concrete, not aesthetic.** Four kept features are attributes of one
data structure — ostat's own separator config proves it, carrying `position`,
`cut_depth`, `cut_width`, `wall_thickness`, `bend_angle` on each separator:

- Unequal compartments (1C.12)
- Divider notches (1C.13)
- Angled divider tops, 65° (from 1D.12)
- Per-divider height and thickness

Building these against two integers means writing collision logic three times and
rewriting it later. Wall cutouts (1C.11) were cut on the same reasoning and become
cheap to revisit afterwards.

**Compatibility rules move out of `render()`.** Today they are inline `raise
ValueError` calls (lite+solid, lite+holes, wall thickness bounds). They become
declared metadata — `requires` / `conflicts_with` — evaluated in one place.

**Backward compatibility is mandatory.** `length_div=2` keeps working and becomes
sugar emitting two evenly-spaced dividers. No existing call site changes.

**Also folded in:** `cylindrical` mode currently bypasses the entire render pipeline
(`gf_box.py:520`). It becomes a hole-grid interior modifier — shape (circle / hex /
rectangle), size, rows, cols. **Generic primitive, no named size presets.** This
*removes* a parallel code path rather than adding one.

**Exit criteria:** all 230 tests still pass; unequal compartments, notches, and angled
tops demonstrated; no compatibility rule remains inline in `render()`.

---

### P3 — Rugged Box (smkent flagship)

**Goal:** new module `gf_ruggedbox_smkent.py`, CC BY-SA 4.0.

**Why a new module rather than extending Pred's box:** a derivative of an NC work
stays NC. Grafting features onto `gf_ruggedbox.py` produces a more capable box that
is still commercially blocked. smkent's is also the better-engineered design —
support-free printing as a hard constraint, filament lip seals, hinge stops, explicit
library architecture — and is independently corroborated by Perplexing Labs having
chosen it. See D1–D3.

Pred's box stays exactly as-is: working, tested, available for non-commercial use.

**Scope:** lip seal (1E.3) · draw latch (1E.2) · clip latch (1E.1) · parametric walls
(1E.8) · integrated baseplate as magnets × skeletonized booleans (1E.4) · stacking
latch mounting (1E.5) · third hinge (1E.6) · hinge end stops (1E.7).

**Latch architecture — style × mounting context.** A latch is a latch; what differs is
where it mounts and what it clamps. Three styles (clasp / clip / draw) × two contexts
(lid closure / box-to-box). Pred's design already places clasp ribs at the box bottom
when `stackable=True` (`gf_ruggedbox.py:650`), so this pattern is partly proven.

**Seal and draw latch are a dependency pair,** not independent choices: a seal only
seals under compression, and the over-center draw latch is the only style that clamps.

**Watertight from line one.** Pred's lid has a known non-watertight defect we
inherited and quarantined as `xfail`. The new module carries `isValid()` checks from
the first commit.

**Exit criteria:** watertight box, lid, and every latch style; DoD-3 verified;
BOM documented (M3×40 DIN 912; M3×55 where handles attach).

---

### P4 — Bin Feature Layers

Layered options on the standard bin. All are Keep decisions from triage; all depend
on P2 or are independent additions to existing slots.

| Feature | Why | Cost |
|---------|-----|------|
| Cullenect click-in labels (1D.3/1D.4) | Relabel by reprinting a 2g tile, not a 6-hour bin. **MIT — real source, not just dimensions** | Low |
| Finger slide on any wall (1C.8) | Current scoop is front-wall-only at fixed radius. Upgrade, not new feature | Low |
| Minimum lip (1C.7) | Drawer bins that never stack shouldn't carry 6.6mm of interlock | Very low — one tuple |
| Bottom size text (1C.16) | Answers "what size is this" when empty. **Must bundle a font**, use `fontPath`, never system lookup | Low–medium |

**Top interface stays a pure profile swap** (D4). Sliding lid was cut, so no wall
modifiers are needed; `lip_style` remains data-driven tuples in `constants.py`.

---

### P5 — Baseplate Completion

**Goal:** finish what fit-to-drawer (1B.11) started. That feature can currently
generate a baseplate physically too large to print.

- **Segmentation (1F.1)** — auto-split to bed size
- **Edge puzzle connector (1F.3)** — joins segments; fully specified by dimensions
- **Dynamic filler (1F.6)** — leftover space becomes usable fractional cells rather
  than dead padding, without producing unusable slivers
- **ClickGroove retention (1F.7)** — magnet-free. One optional groove on the bin, off
  by default; the recess does not break standard-baseplate compatibility

All four are **MIT** (yawkat/GridFlock).

**Docs must warn: do not print retention geometry in PLA** — it creeps under sustained
load and loses grip. PETG, ABS, ASA, or nylon.

---

### P6 — Web UI

Unchanged in intent. Two requirements now fixed by earlier decisions:

- **D7 granularity** — numeric entry, not steppers alone. Any slider needs a typed
  companion field. Perplexing Labs' 1mm increments on latch sizing are a real,
  observed weakness; filament shrinkage corrections are 0.04–0.18mm.
- **Presets configure the engine; they are not separate models.** "Parts Bin",
  "Battery Holder", "Tote" are parameter sets over the same geometry.

---

## 4. The Ship Set (P1 deliverable)

Concrete definition of "the common set." Roughly 35 models.

| Category | Models |
|----------|--------|
| **Baseplates** | plain and magnet, at 2x2 · 3x3 · 4x4 · 2x4 |
| **Bins — footprints** | 1x1 · 1x2 · 2x1 · 1x3 · 2x2 · 2x3 · 3x2 |
| **Bins — heights** | 3U and 6U |
| **Feature combos** | plain · scoop · label · scoop+label · 2-compartment · magnet holes · lite style |
| **Lids** | solid bins at 1U for the common footprints |
| **Rugged box** | one reference size |

> **Note:** this is the *minimum*, not the ceiling. Layering more options onto the
> standard bin is the point of the architecture — this set exists to prove the
> pipeline end to end, not to bound it.

---

## 5. What Changed and Why

| Change | Reason |
|--------|--------|
| Sequenced by user value, not upstream parity | Parity is not a goal (Stop Rule). Old order put the rugged box behind wall patterns |
| Rugged box moved from 1E to P3 | It is a headline goal, and cq-gridfinity already provides a parametric rugged box — the work is a variant, not a from-scratch build |
| smkent replaces Pred as flagship | Better engineering, active maintenance, and **CC BY-SA instead of CC BY-NC-SA** |
| Wall/floor patterns deferred entirely (8 features) | B-Rep cost unmeasured and potentially severe; benefit is filament and aesthetics |
| Drawer system cut | Separate product line; tolerance-critical sliding fit at large scale |
| Sliding lid cut | Tolerance tuning does not converge across printers; solid-bin lid already works at zero cost |
| 42 bolt-on features → 21 Keep, 21 Cut | The Stop Rule applied |
| DoD added | The old plan had per-feature acceptance criteria but no project-level definition of success |

---

## Revision History

| Date | Change |
|------|--------|
| 2026-08-09 | Created. Re-sequenced from parity-ordered (1A–1F) to value-ordered (P0–P6) following full feature triage and the addition of the Stop Rule |
