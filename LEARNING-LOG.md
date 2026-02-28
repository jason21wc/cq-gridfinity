# Learning Log

## CadQuery / OpenCASCADE

### Coplanar Face Boolean Cuts
When two solids share an exact face (e.g., pocket bottom at Z=0 and baseplate bottom at Z=0), OpenCASCADE's boolean `cut()` may silently fail — returning the original solid unchanged. **Fix:** offset the cutting tool by a small epsilon (EPS=1e-5) past the shared face to ensure proper intersection.

### Extrude Profile Extends the Shape, Doesn't Add a Slab
In cq-gridfinity's `extrude_profile()`, adding `ext_depth` to the profile with `[*profile, ext_depth]` extends the receptacle shape itself deeper — it does NOT add a solid slab below. When features need solid material below the receptacle (magnet holes, weight pockets), the receptacle must use ONLY the standard profile, and the outer block provides the solid slab at the bottom.

## OpenSCAD → CadQuery Translation

### Known Gotchas
- `hull()` has no direct CadQuery equivalent — use `.loft()`, `.sweep()`, or manual convex construction
- `minkowski()` → common case of rounding uses `.fillet()` or `.chamfer()`; offset uses `.shell()`
- OpenSCAD `$fn` controls polygon resolution; CadQuery uses exact geometry — no equivalent needed
- OpenSCAD coordinates are center-based for `cube(center=true)` but corner-based by default; CadQuery `.box()` is always centered

## Gridfinity Geometry

### Baseplate Receptacle Floor
The receptacle floor (where bins sit) is at Z=ext_depth when using the "solid slab" approach. For the original "extended profile" approach, the receptacle cuts all the way to Z=0, leaving material only at cell boundaries and perimeter.

### Hole Positions in Baseplates
Hole positions must be computed in the centered coordinate system. Cell centers for a length_u × width_u baseplate: `((i - (length_u-1)/2) * 42, (j - (width_u-1)/2) * 42)`. Holes are at ±GR_HOLE_DIST (13mm) from each cell center. This gives 4 holes per cell.

### Skeleton Cutout Geometry — Subtract vs Direct Construction
When creating a cross-shaped rib pattern (skeleton baseplate), the naive approach — subtract oversized squares at hole positions from an inner square — fails because the 4 subtracted squares completely cover the inner square, leaving an empty result. CadQuery Sketch throws "No pending wires present" when attempting to extrude the empty sketch. **Fix:** Directly construct the 4 corner pocket cutouts (the material to REMOVE) as individual rectangles, placed at `±(rib_half_w + cut_size/2)` from cell center. This produces the correct cross/rib pattern without sketch subtraction issues. Use `composite_from_pts` to tile the single cutout across all cell positions.

### CadQuery Sketch Subtraction Pitfall
`cq.Sketch().rect(A, A).push(pts).rect(B, B, mode="s")` — if the union of all subtracted rects covers the original rect, the result is an empty sketch. CadQuery does not error on this; it only fails later when `.placeSketch().extrude()` finds no wires. Always verify that subtraction leaves residual geometry.

## Debugging

### Volume Comparison for Boolean Verification
When debugging boolean operations, compare `r.val().Volume()` before and after the cut. If volume doesn't change, the cut isn't working (coplanar faces, wrong coordinates, or non-overlapping solids).

### CadQuery Workplane Extrude Directions
- `Workplane("XY").extrude(h)` → +Z direction
- `Workplane("XZ").extrude(h)` → **-Y direction** (counterintuitive!)
- `Workplane("XZ").extrude(-h)` → +Y direction
- `Workplane("YZ").extrude(h)` → +X direction
Always verify with `.val().BoundingBox()` when cutting through walls at specific orientations.
