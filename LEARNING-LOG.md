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
