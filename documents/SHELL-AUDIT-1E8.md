# Module Audit — smkent Rugged Box (1E.8 shell, then everything else)

> **Part 2 (the latch and the parameter sweep) is at the bottom of this file.**
> Part 1 audits the shell cross-section, which is what triggered the exercise.

---

# Part 1 — Wall Cross-Section (1E.8)

**Created:** 2026-08-15
**Scope:** every term of `gf_ruggedbox_smkent.py`'s shell, diffed against
smkent `rugged-box/rugged-box-library.scad` (commit fetched 2026-08-15).
**Why:** five defects in this module were found one at a time, each by a
downstream consumer discovering that what it depended on was wrong. The
sixth was found the same way. This audit is the attempt to stop finding
them one at a time — the whole cross-section, compared once.

**Upstream modules read:** `_box_wall_shape` (935) · `_box_extrude` (873) ·
`_box_wall_interior_shape` (925) · `_box_wall_outer_chamfer_shape` (908) ·
`_box_interior_shape` (955) · `_box_center_base` (970) · `_box_sides` (1043) ·
`_box_body` (767) · `_round_shape` (649) · `_box_seal_shape` (982).

---

## The cross-section

Upstream builds one 2D profile and sweeps it around the rounded rectangle.
In that profile, **x = 0 is the corner-arc centre**, the interior surface is
at `x = corner_radius`, and the outer surface at `x = corner_radius +
total_lip_thickness`. The profile is a full block minus three cuts:

| Cut | Effect |
|-----|--------|
| polygon at `+corner_radius` | removes the **outer** material below the lip |
| `_box_wall_outer_chamfer_shape()` | chamfers the bottom outer edge |
| `_box_wall_interior_shape()` | removes the interior above the floor |

The whole result is then rounded by `_round_shape($b_edge_radius)`, and a
small square block is added back so the inner floor edge stays crisp.

---

## Findings

| # | Term | Upstream | Ours | Status |
|---|------|----------|------|--------|
| 1 | **Wall direction** | interior constant at `inner` for the full height; the **outer** steps out at the lip | was: outer constant, interior widening below the lip | ✅ **fixed** — inverted to match |
| 2 | Edge rounding | entire cross-section rounded by `edge_radius = wall/5 = 0.6` | was: none | ✅ fixed — the five section-change loops are filleted |
| 3 | Outer bottom chamfer | 3.5625 horizontal × 5.34375 vertical, at the part's outward end | was: none, a plain extrusion | ✅ fixed |
| 4 | Reinforced corners | a flag; **the Gridfinity wrapper sets it true** | not implemented (library default `false`) | ⚠ **open** — unadmitted feature, Jason's call |
| 5 | Ramp height | `1.5 × lip_thickness` (from `outer_h − 3.5·lip_th` to `outer_h − lip_height`) | `1.5 × lip_thickness` | ✅ |
| 6 | Lip land height | `lip_height = 2 × lip_thickness` | same | ✅ |
| 7 | Interior corner radius | `corner_radius` = kennetek `r_base` = `BASE_TOP_RADIUS` = 3.75 | 3.75 | ✅ |
| 8 | Outer corner radius | `corner_radius + wall_thickness` | same | ✅ |
| 9 | Outer dimensions | `inner + 2 × total_lip_thickness` | same | ✅ |
| 10 | Seal position | `corner_radius + total_lip_thickness / 2` — centred in the land | inset `total_lip_thickness / 2` from the outer face — the same line | ✅ |
| 11 | Floor | `_box_center_base` + the wall profile's own base, `wall_thickness` thick | prism minus a cavity starting at `wall_thickness` | ✅ equivalent |
| 12 | Half heights | `outer = inner + wall_thickness` per half | same | ✅ *(fixed 2026-08-15, c041728)* |
| 13 | Interior footprint | `n × 42 + border`, border = 5 | same | ✅ *(fixed 2026-08-15, ce33906)* |

### What #1 costs

- The box is **6mm oversized** in both directions over most of its height.
- Bins get 3mm/side of slop below the lip and touch the wall only at the land.
- **The ribs have nowhere to live.** A rib profile runs from the inner surface
  out to `total_lip_thickness`; it *is* the local thickening of a thin wall.
  With the wall already at full thickness everywhere, a rib is buried inside
  the solid. This is what blocked 1E.9 and forced the audit.

### On #4 — reinforced corners

`Reinforced_Corners = true` in the Gridfinity wrapper, and `_box_sides()`
adds a second corner sweep with the subtraction polygon shifted out by
`lip_thickness`, so corners keep full thickness for their whole height.

It is **not an admitted feature** — `UPSTREAM-REFERENCE.md` lists it under
"Additional smkent Features (Not in Phase 1E)". The rebuild therefore
implements the library default (`reinforced_corners = false`, corners step
with the flats). Our box will be structurally weaker at the corners than
smkent's Gridfinity default until this is dispositioned. **Proposed as a row
for Jason's call.**

---

## Outcome

Findings 1–3 were rebuilt in one pass (2026-08-15). Measured on the rendered
body, not asserted: outer 221.0 below the lip and 227.0 at the land, interior
a constant 215.0 at both heights, chamfer slope `2·hc/vc` through its linear
stretch. 431 tests pass; three STEP exports audit clean.

Finding 4 remains open by design — see above.

## Rebuild plan (executed)

1. Outer = rounded rect at `inner + 2·wall_thickness`, radius `cr + wall`,
   full height.
2. Lip land = rounded rect at `inner + 2·total_lip_thickness`, radius
   `cr + total_lip`, over the top `lip_height`, with a ruled loft down to (1)
   over `1.5 × lip_thickness`.
3. Interior void = constant rounded rect at `inner`, radius `cr`, from
   `z = wall_thickness` upward.
4. Cut the outer bottom chamfer at the part's outward end.
5. Round by `edge_radius`.

Verification must be **measured, not asserted**: outer width sampled at a
low z and at the lip, and the interior sampled at both, since the defect this
replaces was invisible to every dimensional test in the suite.

---

# Part 2 — The Rest of the Module (2026-08-15)

Part 1 fixed the shell but answered only the question it was asked. The
follow-up question — *are we sure that is all of them?* — needed a different
method, because a cross-section diff only covers geometry that exists. Two
sweeps were run instead.

## Sweep A — parameters with no consumer

Mechanical: for every `__init__` attribute and every `@property`, count the
uses elsewhere in the module. This catches the failure mode that produced the
missing lip land — a value computed, exposed, unit-tested, and read by nothing.

| Name | Uses | Verdict |
|------|------|---------|
| `latch_amount_on_top` | **0** | ⏳ **scheduled** — upstream consumes it in `_latch_offset_from_base()` to set the screw height per half. Its consumer is the latch rib (1E.12), not yet built. Deliberately left as a bare parameter rather than given a computed property, since another computed-but-unbuilt value is the very thing this sweep exists to find |
| `size_tolerance` | 5 | ❌ **defect — fixed** (see below) |
| everything else | ≥1 | ✅ consumed by geometry |

## Sweep B — term-by-term, clip latch

| # | Term | Upstream | Ours | Status |
|---|------|----------|------|--------|
| 14 | **Latch part width** | every latch extrusion uses `_latch_width() = latch_width − size_tolerance × 2` (10 call sites: 1662, 1670, 1758, 1830, 1847, 1978, 1995, 2101) | used the **raw** `latch_width` at all ten of ours | ❌ **fixed** |
| 15 | **Profile rounding** | `_round_shape($b_edge_radius)` wraps `_clip_latch_shape` — a second, smaller rounding than the end-face break | only the end-face break was applied | ❌ **fixed** |
| 16 | `bw = latch_base_size − screw_hole_diameter / 2` | 3.0 | same | ✅ |
| 17 | `shd = screw_hole_diameter + (−0.1)` | 2.9 | same | ✅ |
| 18 | Hinge hole `shd + screw_hole_diameter_fit` | 3.5 | same | ✅ |
| 19 | Catch hole: hull of three `shd` circles | at `(0,sep)`, `(r + bw/1.6, 0)`, `((shd+bw)·2, sep−shd)` | same | ✅ |
| 20 | Hull of hinge circle + short spine | tangent to the corner `(−r+bw, sep)` | same, exact tangent | ✅ |
| 21 | Grip saddle `deg = |y−lw/2|/lw/2·360·0.8`, `cos(deg)·R·0.9` | `lw = _latch_width()` | same (and `lw` now the part width) | ✅ |
| 22 | Draw latch constants (thickness, handle length, eyelet/pin radii, sep, vsep, angles, curve radii, 5 segments) | lines 484–510, 1672 | all match | ✅ |
| 23 | Seal position / thickness / four types | `corner_radius + total_lip_thickness/2`, `total_lip/3` or 1.75 | same | ✅ |

### #14 — the one that mattered

`size_tolerance` is documented in our own class docstring as *"the one to reach
for when latches or hinges do not fit on your printer"*. It reached **no latch
geometry at all**. Every latch part came out `2 × size_tolerance` (0.4mm at the
Gridfinity preset) too wide to drop between its own ribs, and turning the knob
changed nothing but the filename.

The test that should have caught it asserted the rendered latch width equalled
the raw parameter — encoding the defect as the expectation. It now asserts the
clearance, and a second test checks that changing the tolerance actually moves
metal.

This is also DoD-6: the fine-granularity requirement is worthless if the knob
is not wired to anything.

## Where the defects came from

**All of them are ours, not smkent's.** Every finding above is a transcription
error between `rugged-box-library.scad` and our port — a term dropped, a
direction reversed, a function used where upstream uses a different one.
smkent's source is self-consistent at every point checked.

The single exception is not a smkent defect either: the 0.6mm stacking-lip
error came from **cq-gridfinity**, our fork base, which disagreed with the
official Gridfinity drawings from its first commit. That one we inherited.
