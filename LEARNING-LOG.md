# Learning Log

**Project:** Gridfinity STEP Generator
**Memory Type:** Episodic (experiences)
**Lifecycle:** Graduate to methods when pattern emerges per §7.0.4

> **Entry rules:** Each entry ≤5 lines. State what happened, then the actionable rule.
> Record conclusions, not evidence. Prune entries that lack a future-actionable rule.

---

## Active Lessons

### CadQuery / OpenCASCADE

#### Coplanar Face Boolean Cuts (2026-02-22)
When two solids share an exact face (e.g., pocket bottom at Z=0 and baseplate bottom at Z=0), OpenCASCADE's boolean `cut()` silently fails — returns the original solid unchanged.
**Rule:** Offset the cutting tool by EPS (1e-5) past the shared face to ensure proper intersection.

#### Extrude Profile Extends Shape, Not Slab (2026-02-25)
In cq-gridfinity's `extrude_profile()`, adding `ext_depth` to the profile extends the receptacle shape deeper — it does NOT add a solid slab below.
**Rule:** When features need solid material below the receptacle (magnet holes, weight pockets), use ONLY the standard profile; let the outer block provide the solid slab.

#### Volume Comparison for Boolean Verification (2026-02-25)
Debugging a boolean cut that appeared to succeed but removed no material. Only caught by checking volume before/after.
**Rule:** Compare `r.val().Volume()` before and after `cut()`. If volume doesn't change, the cut isn't working (coplanar faces, wrong coordinates, or non-overlapping solids).

#### CadQuery Workplane Extrude Directions (2026-02-25)
`Workplane("XZ").extrude(h)` goes **-Y** (counterintuitive). `Workplane("XZ").extrude(-h)` goes +Y. `Workplane("YZ").extrude(h)` goes +X.
**Rule:** Always verify with `.val().BoundingBox()` when cutting through walls at specific orientations.

#### CadQuery Parallelism & Multi-Core (2026-02-28)
Boolean ops already parallel via `SetRunParallel(True)` (CadQuery default since `shapes.py:1297`). OCCT spawns 12-thread pool on this machine. Fillet is the real bottleneck — single-threaded kernel, no parallelism possible, 89% of box render time. Python threading useless because OCP never releases the GIL. `multiprocessing.Pool` with `copyreg` BREP serialization is viable for batch STEP generation (4-8x reported per CadQuery #579, #1600) — defer to Phase 2 web UI. Thread pool tunable via `OCP.OSD.OSD_ThreadPool.DefaultPool_s(N)` if oversubscription ever becomes a measured problem.
**Rule:** Don't add parallelism infrastructure until Phase 2 creates a batch generation use case. Current single-process performance is sufficient (tests 82s with xdist, individual renders sub-second). Re-read this entry before building Phase 2 job queue.

### OpenSCAD → CadQuery Translation

#### Known Translation Gotchas (2026-02-22)
Multiple OpenSCAD constructs have no direct CadQuery equivalent: `hull()`, `minkowski()`, `$fn`.
**Rule:** `hull()` → `.loft()` / `.sweep()` / manual convex construction. `minkowski()` rounding → `.fillet()` / `.chamfer()`; offset → `.shell()`. `$fn` → not needed (CadQuery uses exact analytic geometry). `cube(center=true)` → CadQuery `.box()` is always centered.

### Gridfinity Geometry

#### Skeleton Cutout — Subtract vs Direct Construction (2026-02-28)
Naive approach (subtract oversized squares from inner square) fails because subtracted squares completely cover the inner square, leaving empty result. CadQuery Sketch throws "No pending wires" on extrude.
**Rule:** Directly construct the 4 corner pocket cutouts (material to REMOVE) as individual rectangles at `±(rib_half_w + cut_size/2)` from cell center. Use `composite_from_pts` to tile across cells.

#### CadQuery Sketch Subtraction Pitfall (2026-02-28)
`cq.Sketch().rect(A, A).push(pts).rect(B, B, mode="s")` — if subtracted rects cover the original rect, result is empty. CadQuery doesn't error; fails later at `.placeSketch().extrude()`.
**Rule:** Always verify that sketch subtraction leaves residual geometry before extruding.

### Test Performance

#### Interior Fillet = 89% of Box Render Time (2026-02-28)
Profiling: 2x2x3 box takes 5.6s with fillet, 0.67s without (88% reduction). Coarser `fillet_rad=0.5` gives negligible speedup — the OCC fillet kernel dominates regardless of radius. OBB boolean acceleration (`SetUseOBB(True)`) made things 8% *slower*.
**Rule:** Use `fillet_interior=False` for tests that don't check topology (face/edge counts). Keep full fillets on topology tests and mark them `@pytest.mark.slow`. Never skip fillets on `isValid()` + topology combination tests.

### Architecture Hygiene

#### Shared Utility Must Be the Only Path (2026-02-28)
`cut_enhanced_holes()` existed in `gf_holes.py` but the box's `render_holes()` manually imported `enhanced_magnet_hole` + `screw_hole` and did its own union + cut. Baseplate used the shared function; box didn't. The two paths diverged silently.
**Rule:** When creating a shared utility for an operation, refactor ALL callers to use it in the same PR. Search for direct imports of the underlying primitives to catch stragglers.

#### Silent kwargs Swallowing Hides Typos (2026-02-28)
All 5 classes used `for k, v in kwargs: if k in self.__dict__: ...` with no `else`. A typo like `hole=True` (missing 's') produced no output and no error — a debugging nightmare.
**Rule:** Every `for k, v in kwargs` loop that sets `self.__dict__` must `warnings.warn()` in the `else` branch for unknown keys. Apply this to any new class with kwargs.

#### Temporary State Mutation Needs try/finally (2026-02-28)
`render()` mutated `self.length_div`/`self.width_div` for lite_style, with restore at method end. If `render()` raised (e.g., `solid=True` + `lite_style=True`), the object was left in corrupted state.
**Rule:** Any method that temporarily mutates `self` attributes must wrap the body in `try/finally` with restoration in `finally`. Save originals *before* the `try`.

#### Duplicated Branching = Extract Helper (2026-02-28)
`render_labels()` had identical full-vs-tab branching for back walls and divider walls — 4 code paths doing the same 2 things.
**Rule:** When a method repeats the same if/else branching for different inputs, extract a helper immediately. Don't wait for it to become painful.

#### Combinatorial Feature Tests Catch Interaction Bugs (2026-02-28)
Individual feature tests all passed, but multi-feature combinations (scoop + label + divider, raised floor + scoop, etc.) were untested. These interactions are where fillets fail and geometry becomes invalid.
**Rule:** After implementing a batch of features, add parametrized `@pytest.mark.parametrize` combination tests. Use `fillet_interior=False` + `isValid()` for fast coverage.

#### VaseBox Stacking Lip — Inner Cut Formula (2026-03-02)
Stacking lip ring was 2.4mm wide (double wall thickness) because `ri_inner` used
`in_l - 2*wall_th` instead of `in_l`. The 1.2mm interior overhang appeared as a
rectangular void/ceiling at every top corner when viewed from above in a CAD viewer.
**Rule:** Lip ring inner cut = bin interior dimensions (`in_l × in_w`). Width of ring
= wall_th. Do not subtract wall_th again from a dimension that's already interior.

#### Dead Code Risk from Abandoned Approaches (2026-03-02)
VaseBox had a `scoop` variable built with `revolve(0)` that was never used — a leftover
from a scrapped approach. The `revolve(0)` didn't error, so tests passed while dead code
accumulated in the render path.
**Rule:** When switching implementation approaches mid-function, delete the old approach
entirely. Don't leave dead variables "for reference" — they confuse future readers and
can silently carry broken imports (e.g., `GR_LIP_PROFILE` was imported only for this).

#### Documenting a Feature Before Generating It Once (2026-08-09)
`PRODUCTS.md` documented solid-bin lids as the project's entire lid story — with a
rationale for why sliding and snap lids were cut — before a single 1U solid box had
ever been generated. All four crashed on the first ship-set run
(`Standard_Failure: BRepSweep_Translation::Constructor`).
**Rule:** a feature is not documented until it has been generated and validated once.
If docs claim a capability, the ship set must contain an instance of it.

#### Derived Dimensions Break at Range Edges (2026-08-09)
`max_height` is `int_height + GR_UNDER_H + GR_TOPSIDE_H`. At `height_u=1`,
`int_height` is **negative** (-2.8mm) and `max_height` collapses to exactly **0**.
`render_interior()` already handled this with a fallback cavity profile, but the
solid-fill branch a few lines below still referenced `max_height` — so the two
disagreed about how tall the cavity was, and `extrude(0)` raised.
**Rule:** when a derived dimension has a fallback branch, every consumer must use the
same source of truth. Extract it as a property (`cavity_height`) rather than
recomputing per call site. Test geometry at the **minimum** of every unit range, not
just typical values — `height_u=1`, `length_u=1`, `solid_ratio=0`.

#### Fixing One Instance Is Not Fixing the Class (2026-08-10)
The 1U lid crash (`extrude(0)`) was fixed at the solid-fill site. Jason then probed a
neighbouring height and found a **second** instance in the cavity profile; a range
sweep found a **third** in the shell wall extrude. Three separate zero-length
extrudes, all surfacing as the same `Standard_Failure:
BRepSweep_Translation::Constructor`, at three heights:

| Boundary | Collapsed |
|----------|-----------|
| `height <= GR_BASE_HEIGHT + GR_BASE_CLR` (5.0) | shell wall extrude |
| `height <= GR_BOT_H` (7.0) | cavity profile |
| `height_u == 1` unit mode | solid fill (`max_height == 0`) |

**Rule:** when a bug is "a derived dimension hit zero," it is a *class*, not an
instance. Sweep the whole input range in both modes before declaring it fixed —
`for h in range(...): try: render()`. A five-line sweep found two more bugs than
careful reading did.

**Corollary — distinguish "valid" from "correct".** Sub-7mm lids were `isValid()`
before the real fix, but only because a *negative*-height extrude happened not to
remove material anywhere harmful. Passing validation while relying on an accident is
not a fix. `render_interior()` now returns `None` and callers skip their cut
deliberately.

#### Validation Batch Sizing — Diverse, Not Numerous (2026-08-10)
The first ship set generated **32 models before a single human looked at one**. Jason
pushed back: if his first review had surfaced a systemic problem, most of those 32
would be scrap and he'd have reviewed nothing useful. Same anti-pattern the roadmap
re-sequencing was meant to kill — producing volume ahead of validation.

**Rule:** every item in a review batch must be able to fail *independently*. Each one
either (a) exercises a distinct failure mode, or (b) **is** the axis under comparison
(e.g. three lid thicknesses when thickness is the open question). Never ship eight
variations that share one assumption — if the assumption is wrong you have spent eight
reviews to learn one fact. Small and diverse beats large and redundant.

#### "Valid" Has Several Meanings — Check the Right One (2026-08-11)
The rugged box lid was carried as `xfail` labelled *"non-watertight"* for months. It
was not non-watertight: its shell was **closed**, its volume correct. `BRepCheck` was
rejecting **48 individual faces** — all `Cone`, all at z=1.83, all exactly 0.517mm²,
i.e. 4 chamfers per cell × 12 cells on the lid's integrated Gridfinity baseplate.
`ShapeFix_Shape` corrected the face parametrisation with **zero** change to volume or
face count (76752.852mm³ and 1510 faces, before and after).

**Rule:** distinguish *shell closed* from *faces valid* from *is a solid*. They fail
independently and a single `isValid()` collapses them. When triaging, enumerate which
sub-shapes fail and what they have in common — 48 identical faces at one height named
the culprit feature immediately, where months of "non-watertight" never did.

**Corollary:** a defect parked as `xfail` stops being investigated. This one had a
real user-visible consequence — CAD would not treat the lid as a selectable body —
that nobody connected to the quarantined test.

#### Do Not Hypothesise About Third-Party Tool Behaviour (2026-08-11)
Asked why Shapr3D would not select the lid on double-click, I guessed it was a
"tangent face chain" selection. Jason told me to go read actual sources. Shapr3D's
own docs: *"Double tap is for selecting whole bodies... select an entire body by
double-clicking any face"*, and imported STEP retains its hierarchy. So double-click
**is** body selection — my guess was wrong, and the real story was that the lid was
not a valid body at all, which pointed straight at the defect above.

**Rule:** behaviour of an external tool is a fact to look up, not a mechanism to
reason out. Guessing wrong sends the investigation away from the real defect. A
labelled hypothesis is still a wrong answer if the truth was one search away.

#### Every Significant Bug This Session Was a Silent Success (2026-08-12)
Reviewed together, the failures share one shape: **the thing reported healthy while
being wrong.**

| Bug | What it reported |
|-----|------------------|
| Divider roof cut nothing (cutter landed 100mm off) | `isValid() == True` |
| Sub-7mm lid worked via a negative-height extrude | `isValid() == True` |
| Rugged lid mislabelled "non-watertight" for ~6 months | quarantined as `xfail`, never re-examined |
| Edge chamfer silently skipped by `except: pass` | no error at all |

None were caught by a validity check. **Every one was caught by asserting a
quantity** — volume removed, tangent position, dimension, surface-type count.

**Rule:** `isValid()` proves a solid is well-formed, not that it is *correct*. For
any feature whose job is to add or remove material, assert **how much** and **where**,
ideally against a hand-computed figure. Validity is a floor, not a test.

**Second-order lesson:** a defect parked as `xfail` stops being investigated. The
rugged lid carried a wrong diagnosis for six months and had a real user-visible
consequence nobody connected to it. Quarantine hides the symptom *and* the clue.

#### Verifying Against Your Own Transcription Proves Nothing (2026-08-12)
Planned to test generated geometry against `GRIDFINITY-SPEC.md` — until noticing that
document is *our* transcription of the community spec. Testing our code against our
own notes only proves we are **consistently** wrong. Verify the notes against the
canonical source first, then test code against the notes.

Generalises: whenever a test's oracle was produced by the same process as the thing
under test, the test is circular. Find an independent oracle.

### Debugging

#### Safe Fillet Pattern (2026-02-27)
Raised floors and positioned labels create edges the OCP fillet kernel can't handle. Fillet height selectors must account for `_floor_raise`.
**Rule:** Use `safe_fillet()` wrapper that catches OCP exceptions. Compute effective floor as `GR_FLOOR + _floor_raise` when selecting fillet edges.

#### Hybrid Hole Strategy (2026-02-28)
Standard holes use `.cboreHole()` (exact upstream match). Enhanced holes use `gf_holes` boolean cutting. The two paths remove different amounts of material (~840mm³ difference on multi-unit shells).
**Rule:** Don't compare volumes between `.cboreHole()` and `gf_holes` boolean cut paths — they are different strategies by design.

---

## Graduated Patterns

| Pattern | Graduated To | Date |
|---------|-------------|------|
| (none yet) | — | — |
