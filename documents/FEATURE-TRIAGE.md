# Feature Triage — Disposition Record

**Created:** 2026-08-09
**Purpose:** Records the Keep/Cut decision for every bolt-on feature from
non-cq-gridfinity upstreams, per the Stop Rule in `CLAUDE.md`.
**Authority:** Dispositions are Jason's decisions. Claude proposes; Jason decides.

> **Baseline assumption:** every feature already implemented in cq-gridfinity is
> auto-**Keep**. It is the stable foundation. Only bolt-ons from other upstream
> projects require triage.

---

## Strategic Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | **smkent is the flagship rugged box** | Better-engineered (support-free printing, filament lip seals, hinge stops, library architecture); actively maintained; **CC BY-SA 4.0 permits commercial use** |
| D2 | **Pred's rugged box (`gf_ruggedbox.py`) stays as-is** | Works, tested, 1230 LOC. Remains available for non-commercial use. Not extended — a derivative of an NC work stays NC |
| D3 | **New module `gf_ruggedbox_smkent.py` under CC BY-SA 4.0** | Already anticipated in `LICENSE-COMPONENTS.md:57`. Clean-room build gets `isValid()` discipline from line one |
| D4 | **Top interface stays a pure profile swap** | Sliding lid was cut, so no wall-modifier widening is needed. `lip_style` remains data-driven (tuples in `constants.py`) |
| D5 | **Every feature must ship with a stated purpose/use case** | Docs must answer "why would I pick this?" — thin wall vs standard, radiused bottom, lip seal, etc. |
| D6 | **STEP output is the differentiator, not feature breadth** | Perplexing Labs already ships a polished web generator on smkent's box — with **STL output**. The format gap holds against the best in the ecosystem |
| D7 | **Fine dimensional granularity is a first-class requirement** | See below. Jason has used the Perplexing Labs rugged box in practice and hit this as a real limitation |

### D7 — Dimensional granularity (applies project-wide)

Perplexing Labs restricts fit-critical dimensions (e.g. latch sizes) to **1mm
increments**. That is too coarse to be useful: it is larger than the entire
adjustment range most fit problems live in.

Filament shrinkage by material is roughly PLA 0.2–0.3%, PETG ~0.4%, ABS 0.7–0.8%.
On a 22mm latch that is **0.04–0.18mm** of dimensional change — every real
correction is smaller than one 1mm step.

**Requirements:**
1. All dimensional parameters accept **floats**. Never quantize or round user input.
2. **Scope (narrowed by Jason 2026-08-11):** this applies to the **smkent clasp and
   latch dimensions** — the ones Perplexing Labs restricts to 1mm steps. **0.1mm is
   the target granularity; do not go finer.** Everything else in the library is fine
   as it is. This is a **P3** concern, not a library-wide sweep.
3. Phase 2 UI: numeric entry, not steppers alone. Any slider must have a typed-value
   companion field.
4. `size_tolerance` (1E.8) is the designated global fit knob and must accept
   values well below 1mm — smkent's own presets are 0.05 and 0.20mm.

**Why this matters strategically:** the same users who want STEP are the users who
tune fits. Coarse increments are a real, observed weakness in the best generator in
the ecosystem. It is cheap to be better here.

### Licensing position

| Component | License | Commercial |
|-----------|---------|------------|
| Core (`gf_box`, `gf_baseplate`, `gf_obj`, …) | MIT | Yes |
| `gf_ruggedbox.py` (Pred) | CC BY-**NC**-SA 4.0 | **No** |
| `gf_ruggedbox_smkent.py` (planned) | CC BY-SA 4.0 | Yes |
| Cullenect labels | MIT | Yes |
| ostat-sourced features | GPL — **spec reference only**, independent CadQuery code | Yes |

**Donations under CC BY-NC-SA:** grey area, fact-dependent, not legal advice.
Low risk for a free tool with a donate button; risk rises with paid tiers or
sponsorship. D1/D3 retire the question for the flagship box.

---

## Disposition: KEEP

| # | Feature | Source | Purpose / why you'd want it |
|---|---------|--------|------------------------------|
| 1C.12 + 1C.13 | **Unequal compartments + divider notches** | ostat (GPL, spec ref) | Real bins hold one big thing and several small things; even splits are the exception. Notches let long tools bridge compartments. Both are attributes of one divider object |
| 1D.3 + 1D.4 | **Cullenect click-in labels** | CullenJWebb (**MIT**) | Swap a label by reprinting a 2g tile instead of a 6-hour bin. Most widely adopted label system in the ecosystem |
| — | **Solid-bin lid** (`GridfinitySolidBox`, already built) | cq-gridfinity | Community-standard lid: a solid bin sits on top, held by the stacking lip. Dust cover for shelf bins. **Zero cost — needs documenting, not building** |
| 1C.8 | **Finger slide on any wall** | ostat (GPL, spec ref) | Current scoop is front-wall-only at fixed 14mm. Per-wall + proportional radius means a 1x4 can be scooped on its long side, and a short bin doesn't lose its whole interior |
| 1C.7 | **Minimum lip** | ostat (GPL, spec ref) | Drawer bins that never stack shouldn't carry 6.6mm of interlock. Saves height and filament |
| — | **Hole grid** (shape · size · rows · cols) | ostat (GPL, spec ref) | Batteries, hex bits, cards, anything arrayed. **Generic primitive — no named preset table.** Shape = circle / hex / rectangle. **Subsumes `cylindrical` mode**, removing a pipeline bypass |
| 1C.16 | **Bottom size text** | ostat (GPL, spec ref) | Answers "what size is this bin" when empty — fitting and reordering. Distinct from labels, which answer "what's in it". **Must bundle a font** and use `fontPath`; never rely on system font lookup (Docker portability) |
| 1E.3 | **Lip seal (4 types)** | smkent (BY-SA) | Turns a sturdy box into a weather-resistant one. Filament-gasket variant uses 1.75mm stock you already own — TPU for a softer seal |
| 1E.2 | **Draw latch** | smkent (BY-SA) | Over-center toggle (Pelican mechanism). **Dependency, not preference:** a seal only seals under compression, and this is the only latch that clamps |
| 1E.8 | **Parametric walls (7 params)** | smkent (BY-SA) | Constants promoted to parameters. `size_tolerance` (0.05 vs 0.20mm) is the knob that makes latches and hinges fit on a given printer |
| 1E.1 | **Clip latch** | smkent (BY-SA) | A latch *style*, not a subsystem — see the latch model below |

### Latch model (style × mounting context)

A latch is a latch; what differs is where it mounts and what it clamps.

| Style | Mechanism | Hardware | Clamping force | Lid closure | Box-to-box |
|-------|-----------|----------|----------------|-------------|------------|
| Clasp (Pred) | Slide-in, ratchets over channel ribs | None | Low | ✅ | ✅ *when `stackable=True`* |
| Clip (smkent) | Pivoting flexure, snaps over catch | M3×40 | Medium | ✅ | ✅ |
| Draw (smkent) | Over-center toggle on a pin joint | M3×40 | **High** | ✅ | ✅ |

Pred's design **already** places clasp ribs at the box bottom when `stackable=True`
(`gf_ruggedbox.py:650`), so one latch part can span box-to-box. Style × context is
partially implemented already — 1E.5 is a mounting site, not a new mechanism.

---

## Disposition: CUT

| # | Feature | Source | Reason |
|---|---------|--------|--------|
| 1D.8 | Sliding lid | ostat | CAD is easy; **tolerance tuning is not** and doesn't converge across printers. Conflicts with the stacking lip for the same 4–6mm of rim. Solid-bin lid covers the need at zero cost |
| 1D.1, 1D.2 | Anylid snap lids | rngcntr | **License unresolved** — no GitHub repo, MakerWorld only. Per the Stop Rule, blocked ≠ deferred. Designing our own would violate No Invented Features |
| 1C.7b | Reduced-double lip | ostat | No constructible user story. If the case can't be explained, it's a Cut |
| 1C.11 | Wall cutouts | ostat | **Revisit after the divider refactor.** Genuinely useful (cable drape, reach-in, long tools) but collides with dividers; the collision check is cheap against divider objects and expensive against two integers |
| 1C.14 | Split bins for small printers | ostat | **Weak specifically for a STEP generator** — STEP users have CAD open and can split a body in a minute, where *they* want the seam. This exists upstream because STL users can't |
| — | Named hole-size preset table | ostat | Modular shape/size/grid preferred over a catalogue of names |

---

## Disposition: KEEP (continued — batches 5–8)

| # | Feature | Source | Purpose / why you'd want it |
|---|---------|--------|------------------------------|
| 1E.4 | **Integrated baseplate: magnets × skeletonized** | smkent (BY-SA) | The baseplate inside the rugged box floor holds bins. Magnets matter most here — this box gets **carried**, and unmagnetized bins dump their contents in transit. Skeletonizing saves weight on something you lift. **Expose two booleans, not four named styles** — reuses existing `gf_baseplate.py` building blocks |
| 1E.5 | **Stacking latch mounting** | smkent (BY-SA) | Locks boxes together vertically so a carried stack doesn't slide apart. Requires height >40mm. Cheap under the style × context latch model — a mounting site, not a mechanism |
| 1E.6 | **Third hinge** | smkent (BY-SA) | **Structural correctness, not a feature.** A ≥5U-wide lid on two corner hinges racks under its own weight, gapping the seal and side-loading the pins. Auto-activates by width |
| 1E.7 | **Hinge end stops** | smkent (BY-SA) | Limits lid rotation. Over-rotation is the most common failure mode of printed hinges. Also keeps the lid where you put it instead of falling open past vertical |
| 1E.9–1E.13 | **Box attachment system** (support ribs · attachment placement · screw eyelets · latch ribs · hinge ribs) | smkent (BY-SA) | **Dispositioned 2026-08-15, mid-P3.** Not a feature the user opts into — it is the structure that makes the rest work. Discovered when 1E.6 (third hinge) turned out to be a *placement rule* for hinges that had never been built: the 1E list only ever captured smkent's additions *over* a rugged box, and this module was written from scratch, so the base layer never came with it. Without it the box has no hinge, and the two finished latches have nothing to bolt to. P3's exit criteria already assume it — they require a BOM of M3×40 screws, which implies eyelets to take them |
| 1D.12 *(partial)* | **Angled divider tops (65°)** | ostat (GPL, spec ref) | Filing flat items upright — sandpaper, sockets, PCBs, wrenches. Angled tops let items drop in without catching. **Kept as a `Divider` attribute; the separate bin type is Cut** |
| 1F.1 | **Baseplate segmentation** | yawkat (**MIT**) | **Completes fit-to-drawer (1B.11)**, which can currently generate a plate too large to print. Auto-splits to bed size |
| 1F.3 | **Edge puzzle connector** | yawkat (**MIT**) | Joins segments. 10 × 2.5mm with a 3 × 1.2mm bridge, 0.15mm gap. Fully specified by dimensions |
| 1F.6 | **Dynamic filler** | yawkat (**MIT**) | Turns leftover sub-42mm space into usable fractional cells instead of dead padding, while avoiding unusably narrow slivers. **One filler policy only** |
| 1F.7 | **ClickGroove magnet-free retention** | yawkat (**MIT**) | Bins click into the baseplate — no magnets to buy or insert. **One optional groove on the bin (off by default); the recess does not break standard-baseplate compatibility.** Genuinely "just another option, like a lip style" |

### ClickGroove — landscape and material caveat

Magnet-free retention is effectively a community standard by convergence:
Clickfinity (jerrymk / NoWarrenty) → remixes (James Boone, daniel.g68) → CLICKbase
(John Hall). ~2,700 collections on the original.

**The dominant design puts retention entirely in the baseplate and grips stock,
unmodified bins** — architecturally better than ClickGroove. But the entire
Clickfinity family is **STL-only with no open-source license**, so it cannot be
legally derived from. ClickGroove is the only magnet-free retention with an MIT
license and available source.

> **License note:** "no open-source license" ≠ NonCommercial. **ND (NoDerivatives)**
> and *no grant at all* both block derivative works regardless of whether money
> changes hands. Non-commercial use only cures NC. This is why Clickfinity is out
> and ClickGroove is in.

**Material requirement (applies to any spring-retention geometry we generate):**
**do not print in PLA.** PLA creeps under sustained load and the arms lose grip.
Use PETG, ABS, ASA, or nylon. Must appear in generated docs.

---

## Disposition: CUT (continued — batches 5–8)

| # | Feature | Source | Reason |
|---|---------|--------|--------|
| 1C.1–1C.6, 1C.17–1C.18 | Wall + floor patterns (all 8) | ostat | **Deferred entirely.** Cheap in mesh, potentially expensive in B-Rep: face-count explosion in STEP, interaction with filleting (already 89% of box render time), and watertightness risk. Benefit is filament savings and aesthetics. Revisit only on demonstrated need |
| 1C.9 | Finger slide, chamfered | ostat | Style variant of 1C.8, which is kept. No functional difference |
| 1C.10 | Tapered bin corners | ostat | Cosmetic; interacts with the label shelf and stacking lip, which occupy the same corner region |
| 1D.11 | Catch-all tray | ostat | **Subsumed** — a 1U bin with dividers *is* a catch-all tray. Redundant once unequal compartments exist |
| 1D.12 *(as a bin type)* | Vertical divider bin | ostat | Capability kept as a divider attribute; the packaging is redundant |
| 1D.9, 1D.10 | Drawer chest + sliding drawers | ostat | Separate product line, not a bin feature. Tolerance-critical sliding fit at large scale — the sliding-lid problem on an 8-hour print. `GridfinityDrawerSpacer` already covers fitting Gridfinity into drawers you own |
| 1F.2 | Intersection puzzle connector | yawkat | Geometry is **defined by an SVG file**, not dimensions — the only feature in the ecosystem not expressible parametrically. 1F.3 already joins segments |
| 1F.4, 1F.5 | Filler modes: none, integer-fraction | yawkat | Need *a* filler policy, not three |

---

## Triage Complete

All 42 bolt-on features dispositioned across 8 batches. Nothing remains in Triage.

---

## Revision History

| Date | Change |
|------|--------|
| 2026-08-09 | Created. Batches 1–4 triaged. Strategic decisions D1–D6 recorded. Licensing position established after verifying smkent rugged-box is CC BY-SA 4.0 (not NC) directly from GitHub |
