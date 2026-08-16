# Shell Audit — smkent Rugged Box Wall Cross-Section (1E.8)

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
