"""Spec conformance: does our geometry match the published Gridfinity spec?

The audit tool proves geometry is *well-formed*. These tests prove it is
*correct* -- a different question, and the one that was never asked. Upstream's
offsets being battle-tested says nothing about whether we transcribed them
right.

Oracle is the official drawing set (Stu142/Gridfinity-Documentation, 2023-11-10),
cross-checked against kennetek's standard.scad which cites gridfinity.xyz:

    Bin Bottom Profile:   0.8 | 1.8 | 2.15 run | 2.95 | 4.75 | + 2.25 = 7
    Bin Sharp Lip:        0.7 | 1.8 | 1.9 | height 4.4 | width 2.6 | 45deg
    Bin Total Height:     Grid Z Unit * Height Units + Stacking Lip
                          7*6 + 4.4 = 46.4;  no lip: 7*6 = 42
    Bin Total Width:      Grid X Unit * Grid Size - 0.5;  2*42 - 0.5 = 83.5

Values here are transcribed from those drawings, NOT from our own
constants.py -- testing our code against our own notes would only prove we are
consistently wrong.
"""

import math

import cadquery as cq
import pytest

from cqgridfinity import GridfinityBox
from cqgridfinity.constants import (
    GR_LIP_APEX_SETBACK,
    GR_LIP_FILLET,
    GR_STACKING_LIP_H,
    GRHU,
    GRU,
)

# --- Values transcribed from the official drawings --------------------------
SPEC_GRID_XY = 42.0
SPEC_GRID_Z = 7.0
SPEC_BIN_GAP = 0.5
SPEC_LIP_HEIGHT = 4.4
SPEC_LIP_WIDTH = 2.6
SPEC_LIP_SEG_1 = 0.7
SPEC_LIP_SEG_2 = 1.8
SPEC_LIP_SEG_3 = 1.9
SPEC_BASE_HEIGHT = 4.75
# kennetek h_lip, the ACTUAL (post-fillet) lip height. smkent's rugged box uses
# exactly this to budget lid clearance, so it is an independent check on ours.
KENNETEK_H_LIP = 3.548


def _wall_thickness_at(solid, dz_below_top):
    """Wall thickness (per side) at a depth below the rim."""
    bb = solid.BoundingBox()
    z = bb.zmax - dz_below_top
    plate = cq.Workplane("XY").rect(500, 500).extrude(0.02).translate((0, 0, z))
    sec = solid.intersect(plate.val())
    rings = [
        f for f in sec.Faces()
        if len(f.Wires()) == 2 and abs(f.BoundingBox().xlen - bb.xlen) < 0.01
    ]
    if not rings:
        return None
    inner = sorted(rings[0].Wires(), key=lambda w: w.BoundingBox().xlen)[0]
    return (bb.xlen - inner.BoundingBox().xlen) / 2


# --- Footprint --------------------------------------------------------------


@pytest.mark.parametrize("lu,wu", [(1, 1), (2, 2), (4, 2), (3, 5)])
def test_outer_footprint_matches_spec(lu, wu):
    """Grid X Unit * Grid Size - 0.5. Drawing: 2*42 - 0.5 = 83.5."""
    bb = GridfinityBox(lu, wu, 3).render().val().BoundingBox()
    assert bb.xlen == pytest.approx(lu * SPEC_GRID_XY - SPEC_BIN_GAP, abs=0.01)
    assert bb.ylen == pytest.approx(wu * SPEC_GRID_XY - SPEC_BIN_GAP, abs=0.01)


def test_grid_constants_match_spec():
    assert GRU == pytest.approx(SPEC_GRID_XY)
    assert GRHU == pytest.approx(SPEC_GRID_Z)


# --- Stacking lip -----------------------------------------------------------


def test_nominal_lip_height_matches_spec():
    """Drawing 'Bin Sharp Stacking Lip Profile' gives 4.4mm."""
    assert GR_STACKING_LIP_H == pytest.approx(SPEC_LIP_HEIGHT)


def test_lip_max_width_matches_spec():
    """Lip protrudes 2.6mm into the bin, INCLUDING wall thickness."""
    solid = GridfinityBox(2, 2, 6).render().val()
    widths = [
        _wall_thickness_at(solid, dz) for dz in (4.0, 4.5, 5.0, 5.5, 6.0)
    ]
    assert max(w for w in widths if w is not None) == pytest.approx(
        SPEC_LIP_WIDTH, abs=0.02
    )


def test_lip_segments_match_spec():
    """0.7 @45 -> 1.8 vertical -> 1.9 @45, measured on real geometry.

    Regression: the final segment was 1.3mm from cq-gridfinity's first commit
    until 2026-08-12, making the lip 3.8mm instead of 4.4mm.
    """
    solid = GridfinityBox(2, 2, 6).render().val()
    # The vertical section shows as a plateau in wall thickness.
    samples = [(dz, _wall_thickness_at(solid, dz)) for dz in
               [x / 10 for x in range(3, 62)]]
    samples = [(z, w) for z, w in samples if w is not None]
    plateau = [z for z, w in samples if abs(w - 1.90) < 0.02]
    assert plateau, "no vertical section found in the lip profile"
    vertical_span = max(plateau) - min(plateau)
    assert vertical_span == pytest.approx(SPEC_LIP_SEG_2, abs=0.15)
    # Above the plateau lies the 1.9mm 45-degree run down from the tip -- less
    # the setback, since the fillet removed the apex that depth is measured from.
    assert min(plateau) == pytest.approx(
        SPEC_LIP_SEG_3 - GR_LIP_APEX_SETBACK, abs=0.15
    )


# --- Fillet and the nominal/actual distinction ------------------------------


def test_apex_setback_is_exact_not_fitted():
    """Fillet lowers the apex by r*sqrt(2).

    The outer wall (vertical) meets the final 45-degree face, so the included
    angle is 45 and the half-angle 22.5. setback = r*(cot(22.5) - 1) = r*sqrt(2).
    """
    assert GR_LIP_APEX_SETBACK == pytest.approx(GR_LIP_FILLET * math.sqrt(2))


def test_actual_lip_height_agrees_with_kennetek():
    """Independent corroboration.

    kennetek publishes h_lip = 3.548 as the actual filleted lip height, and
    smkent's rugged box uses it to budget lid clearance. Ours is derived
    geometrically from the spec nominal minus the fillet setback. They must
    agree, or one of us has the lip wrong.
    """
    ours = SPEC_LIP_HEIGHT - GR_LIP_APEX_SETBACK
    assert ours == pytest.approx(KENNETEK_H_LIP, abs=0.01)


def test_actual_height_is_below_nominal_by_the_setback():
    b = GridfinityBox(2, 2, 6)
    assert b.height == pytest.approx(6 * SPEC_GRID_Z + SPEC_LIP_HEIGHT)
    assert b.actual_height == pytest.approx(b.height - GR_LIP_APEX_SETBACK)


@pytest.mark.parametrize("u", [2, 3, 6])
def test_rendered_part_matches_actual_height(u):
    """The number we report must be the number the part measures."""
    b = GridfinityBox(2, 2, u)
    bb = b.render().val().BoundingBox()
    assert bb.zlen == pytest.approx(b.actual_height, abs=0.01)


# --- Total height equations -------------------------------------------------


@pytest.mark.parametrize("u", [1, 3, 6])
def test_total_height_equation_with_lip(u):
    """Drawing: Grid Z Unit * Height Units + Stacking Lip."""
    assert GridfinityBox(2, 2, u).height == pytest.approx(
        u * SPEC_GRID_Z + SPEC_LIP_HEIGHT
    )


@pytest.mark.parametrize("u", [2, 3, 6])
def test_total_height_equation_without_lip(u):
    """Drawing: 'For no stacking lip: Grid Z Unit * height units = total height'.

    Regression: no-lip bins used to carry the 4.4mm lip allowance anyway, so a
    6U no-lip bin came out 46.4mm instead of 42.0mm.
    """
    b = GridfinityBox(2, 2, u, lip_style="none")
    assert b.height == pytest.approx(u * SPEC_GRID_Z)
    assert b.render().val().BoundingBox().zlen == pytest.approx(
        u * SPEC_GRID_Z, abs=0.01
    )


def test_no_lip_1u_has_no_interior():
    """A 1U no-lip bin is exactly 7.0mm: the base profile and floor consume it
    entirely, leaving no cavity. Rejecting it is correct."""
    with pytest.raises(ValueError, match="no interior cavity"):
        GridfinityBox(2, 2, 1, lip_style="none").render()


def test_reduced_lip_stacks_with_normal_lip():
    """A "reduced" lip is a printability variant, not a different size."""
    a = GridfinityBox(2, 2, 6)
    b = GridfinityBox(2, 2, 6, lip_style="reduced")
    assert b.actual_height == pytest.approx(a.actual_height, abs=0.01)


def test_reduced_lip_recess_opens_at_the_rim():
    """Equal height is not enough -- the RECESS has to accept a bin's base.

    Regression: the reduced profile ran straight to the rim, leaving a constant
    2.60mm wall for 5.6mm below the top. The recess never opened, so a
    reduced-lip bin could not actually be stacked on despite matching heights.
    The rim opening must track the normal lip's.
    """
    def rim_wall(solid, dz=0.3):
        # Local probe: inside the tip fillet the cross-section is narrower than
        # the bin's full width, so _wall_thickness_at's strict width filter
        # rejects it. Take the largest ring instead of demanding full width.
        bb = solid.BoundingBox()
        pl = (cq.Workplane("XY").rect(500, 500).extrude(0.02)
              .translate((0, 0, bb.zmax - dz)))
        rings = [f for f in solid.intersect(pl.val()).Faces()
                 if len(f.Wires()) == 2]
        if not rings:
            return None
        f = max(rings, key=lambda x: x.BoundingBox().xlen)
        inner = sorted(f.Wires(), key=lambda w: w.BoundingBox().xlen)[0]
        return (f.BoundingBox().xlen - inner.BoundingBox().xlen) / 2

    a = GridfinityBox(2, 2, 6).render().val()
    b = GridfinityBox(2, 2, 6, lip_style="reduced").render().val()
    rim_a = rim_wall(a)
    rim_b = rim_wall(b)
    assert rim_a is not None and rim_b is not None
    # Thin at the rim, nowhere near the 2.6mm maximum.
    assert rim_b < 1.8, "reduced lip does not taper at the rim"
    # And within a fraction of a mm of the normal lip it substitutes for.
    assert rim_b == pytest.approx(rim_a, abs=0.15)


def test_reduced_lip_net_travel_matches_normal():
    """The profile's net horizontal travel sets the recess shape. Normal is
    +1.6 - 0.7 - 1.9 = -1.0; reduced collapses the two inward segments into one
    2.6mm taper for the same -1.0. Mismatching it produced an invalid solid."""
    from cqgridfinity.constants import (
        GR_LIP_PROFILE, GR_REDUCED_LIP_PROFILE, SQRT2,
    )

    def net(profile):
        return sum(
            (seg[0] / SQRT2) * (1 if seg[1] > 0 else -1)
            for seg in profile if isinstance(seg, tuple)
        )

    assert net(GR_REDUCED_LIP_PROFILE) == pytest.approx(net(GR_LIP_PROFILE))


# --- Base profile -----------------------------------------------------------


def test_base_profile_height_matches_spec():
    """Drawing 'Bin Bottom Profile': 4.75 profile + 2.25 bridge = 7 (U1)."""
    from cqgridfinity.constants import GR_BASE_HEIGHT, GR_BOT_H

    assert GR_BASE_HEIGHT == pytest.approx(SPEC_BASE_HEIGHT)
    assert GR_BOT_H == pytest.approx(SPEC_GRID_Z)


# --- Magnet / screw holes ---------------------------------------------------


def test_hole_dimensions_match_spec():
    """Magnets are 6mm x 2mm; the hole is 6.5 x 2.4 (0.5 clearance, 2 layers)."""
    from cqgridfinity.constants import GR_HOLE_D, GR_HOLE_H, GR_BOLT_D

    assert GR_HOLE_D == pytest.approx(6.5)
    assert GR_HOLE_H == pytest.approx(2.4)
    assert GR_BOLT_D == pytest.approx(3.0)  # M3
