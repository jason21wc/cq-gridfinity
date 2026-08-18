# Geometry Rules — what the generator refuses to build

**Created:** 2026-08-17
**Question this answers:** *are the rules captured, so we can't build something
that breaks through negative overlaps, features creeping onto other features,
and so on?*

**Short answer: partly, and now the gap is closed by checking the invariant
rather than by trying to enumerate every rule.**

---

## Two kinds of rule

### 1. Range rules — a parameter is nonsense on its own

Checked in `_validate()` at construction. These were always present.

| Rule | Enforced |
|------|----------|
| `wall_thickness`, `lip_thickness` in 0.4–10mm | raises |
| `rib_width` 1–20mm · `latch_width` 5–50mm | raises |
| `latch_screw_separation` 5–40mm · `size_tolerance` 0–1mm | raises |
| `length_u`, `width_u` ≥ 1 · `height_u` ≥ 2 | raises |
| `lip_seal_type` and `latch_type` from their known sets | raises |
| `height_u` > `lid_height_u` — the lid is carved out of the total | raises |
| `lid_height_u` ≥ 1 | raises |
| Cullenect socket needs a label shelf to cut into | raises |
| Cullenect socket must fit the shelf it is cut into | raises — **and is reachable**: a tab `label_style` gives a ~42mm shelf |
| Cullenect tile is sized from the SHELF, not the bin | `cullenect_label_u = 0` (auto) picks the largest tile that fits |

### 2. Combination rules — every value is legal, the COMBINATION is not

**These were not captured.** A boundary sweep on 2026-08-17 found five
combinations that rendered "successfully" while producing geometry that
cannot be printed:

| Combination | What actually came out |
|-------------|------------------------|
| 1U × 1U box | **5 disconnected pieces** — the latch and hinge ribs land past the wall's corner and never touch it |
| 10U × 1U box | **5 disconnected pieces** — 1U deep leaves no flat wall for the side ribs |
| `height_u=3` with `lid_height_u=2` | **3 disconnected pieces** — the body is too short to carry its own attachments |
| `rib_width` ≥ 13 | **3 pieces** — measured: 12 builds, 13 does not. Not the rib pitch as first assumed (a plain rib spans only 79% of it); the body's own hinge knuckles are what run together |
| `latch_width=50` on a 1U box | **5 pieces** — the latch is wider than the wall it mounts on |
| `wall_thickness=2.4`, `lip_thickness=2.0` | 1 solid but **4 sealed voids**, one per hinge knuckle |

Every one passed `isValid()`. Every dimensional assertion still held. This is
the same shape as six of this module's earlier defects: the failure is
structural, and nothing was checking structure.

---

## How it is captured now

Enumerating combination rules analytically was tried and **abandoned on
purpose**. The derived thresholds were wrong twice in an hour: a 1U×2U box
survives its ribs marginally overhanging the corner arc, while 2U×1U does
not, and the thin-wall failure turned out to be in the lid rather than the
body. A rule derived from partial understanding gives false confidence in
both directions.

So the **invariant** is asserted instead, on the way out of every render:

```
_assert_sound(shape, "body" | "lid")
    exactly one solid
    exactly one shell   (a second shell is a sealed void)
    isValid()
```

Anything that fails raises a `ValueError` naming the four parameter groups
most likely to be responsible, with the caller's actual values substituted in.
The geometry cannot say which knob was wrong, so the message lists them in
order of likelihood rather than guessing.

This is deliberately a **check of the thing we care about, not a proxy for
it**. It catches combinations nobody has thought of yet, including any this
document does not list.

---

## Known limitation, stated rather than hidden

`wall_thickness=2.4` with `lip_thickness=2.0` — smkent's **generic (non-
Gridfinity) preset** — produces four sealed voids where the hinge knuckles
meet the wall, and is therefore refused. The Gridfinity preset (3.0 / 3.0,
which this module defaults to and exists to build) is unaffected, as are
1.0/1.0, 1.5/1.5, 2.0/2.0, 2.0/1.0 and 1.5/2.5.

The cause is the knuckle/rib/wall interaction at reduced wall thickness; it is
a real defect rather than an over-strict guard, and it is **not fixed**. It is
refused loudly instead of shipped quietly. Anyone who needs the generic preset
should treat this as the open item it is.

---

## A branch of the upstream design that was never ported

Sweeping `rib_width` to find the pitch threshold found something better than a
threshold. `_box_hinge_ribs_top` has **two** branches: the interleaved pair we
built, and a **single-module hinge** used when
`top_hinge_width - rib_width*2 <= 0` — once the centre knuckle is no wider than
the pair that would flank it, interleaving is no longer possible.

Only the first branch was ported. At the Gridfinity default (`rib_width=6`,
`top_hinge_width=15.4`) the interleaved branch is the correct one, so nothing
ever exercised the other. Between `rib_width` 7 and 12 the port silently built
the wrong hinge topology and got away with it; at 13 it collapsed into loose
pieces. Both branches now exist, and `top_hinge_width <= 0` raises rather than
producing a degenerate knuckle.

The lesson is about how it was found: a sweep aimed at one rule (rib pitch)
surfaced a different and more important one, because the sweep tested the
GEOMETRY rather than the rule being hypothesised. The pitch hypothesis was
wrong — a rib spans only 79% of the pitch at the failure point.

## A rule I documented that was not true

The first version of this file listed "socket must fit the shelf" as an enforced
rule. Re-testing every claim in it against the code found the check **could not
fire**: the tile was sized from `length_u`, the shelf spans the bin, so the two
always agreed by construction. A guard that cannot fire is not a guard.

It became reachable — and immediately useful — once `label_style` was varied. A
tab style ("auto", "left", "center", "right") gives a shelf about one grid unit
long whatever the bin's width, and the socket then demanded a 120mm tile for a
42mm tab and refused to build. The real rule was the opposite of what was
written down: **the tile is sized from the shelf, not from the bin.** Fixed, and
the guard now backs it up rather than standing in for it.

Recorded because it is the same failure this project keeps finding, one level
up: a rule can be stated, documented and believed while nothing exercises it.

## What is still NOT guarded

Honest list, so nobody assumes more than is true:

- **The bin (`GridfinityBox`) has no equivalent structural guard.** Only the
  smkent rugged box does. The bin's own combinations — dividers, scoops,
  raised floors and label shelves interacting — are covered by tests but not
  by a runtime invariant.
- **Print manufacturability is not checked at all.** Overhang angles, minimum
  feature sizes against a nozzle diameter, and bridging distances are not
  modelled. The generator guarantees a closed solid, not a printable one.
- **Kernel failures short of the guard.** Combinations that collapse a sketch
  before the shape exists (very thin walls on the lid) cannot reach the
  structural check. They are now wrapped with the same diagnosis rather than
  surfacing as `No pending wires present`, but they are caught later and more
  crudely than the invariant.
- **Fit is asserted, not measured.** Clearances are correct by construction at
  0.05–0.2mm; only a printer settles whether they are right.
