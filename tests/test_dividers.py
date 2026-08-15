"""Divider object tests (P2).

Compartments used to be two integers, which could only make evenly-spaced
full-height walls. They are now `Divider` objects, so unequal spacing, notches,
per-divider height/thickness and angled tops all come from one representation.

Per tests/conftest.py: tests asserting isValid() or topology use default
fillets. Wall-level tests bypass the box render entirely, so they are cheap.
"""

import math

import pytest

from cqgridfinity import Divider, GridfinityBox, dividers_from_counts


def _wall(box, index=0):
    """Render a single divider wall in isolation (no fillets, fast)."""
    return box._render_divider_wall(box.divider_list[index])


def _vol(box, index=0):
    return _wall(box, index).val().Volume()


# --- Divider validation -----------------------------------------------------


def test_divider_rejects_bad_axis():
    with pytest.raises(ValueError, match="axis must be"):
        Divider("z", 0.5)


@pytest.mark.parametrize("pos", [0.0, 1.0, -0.1, 1.5, 42.0])
def test_divider_rejects_out_of_range_pos(pos):
    """pos is a FRACTION, not millimetres -- 42.0 is a likely user error."""
    with pytest.raises(ValueError, match="fraction"):
        Divider("x", pos)


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"thickness": 0}, "thickness"),
        ({"height": 0}, "height"),
        ({"notch_depth": -1}, "notch_depth"),
        ({"top_angle": 90}, "top_angle"),
    ],
)
def test_divider_rejects_bad_attributes(kwargs, match):
    with pytest.raises(ValueError, match=match):
        Divider("x", 0.5, **kwargs)


# --- Backward compatibility: counts are sugar -------------------------------


def test_counts_generate_even_dividers():
    ds = dividers_from_counts(2, 1)
    assert [(d.axis, round(d.pos, 6)) for d in ds] == [
        ("x", round(1 / 3, 6)),
        ("x", round(2 / 3, 6)),
        ("y", 0.5),
    ]


def test_count_sugar_matches_legacy_placement():
    """The integer path must place walls exactly where it always did.

    Legacy arithmetic was (i + 1) * inner/(n + 1) - half_in.
    """
    b = GridfinityBox(3, 2, 6, length_div=2, width_div=1)
    xl = b.inner_l / 3
    expected_x = [(i + 1) * xl - b.half_in for i in range(2)]
    got_x = [b._divider_offset(d) for d in b._dividers_on("x")]
    assert got_x == pytest.approx(expected_x)

    yl = b.inner_w / 2
    assert [b._divider_offset(d) for d in b._dividers_on("y")] == pytest.approx(
        [yl - b.half_in]
    )


def test_explicit_dividers_override_counts():
    b = GridfinityBox(3, 2, 6, length_div=5, dividers=[Divider("x", 0.5)])
    assert len(b.divider_list) == 1
    assert b.has_dividers


def test_no_dividers_by_default():
    assert GridfinityBox(2, 2, 6).divider_list == []
    assert not GridfinityBox(2, 2, 6).has_dividers


# --- Unequal compartments ---------------------------------------------------


def test_unequal_compartment_spans():
    """A 25/50/25 layout must produce those spans, not three equal ones."""
    b = GridfinityBox(3, 2, 6, dividers=[Divider("x", 0.25), Divider("x", 0.75)])
    spans = b._compartment_spans("x")
    lengths = [l for _, l in spans]
    assert lengths == pytest.approx(
        [b.inner_l * 0.25, b.inner_l * 0.5, b.inner_l * 0.25]
    )
    # Compartments tile the interior exactly, no gaps or overlaps.
    assert sum(lengths) == pytest.approx(b.inner_l)
    assert spans[0][0] == pytest.approx(-b.half_in)


def test_even_spans_match_legacy_arithmetic():
    b = GridfinityBox(3, 2, 6, length_div=2)
    assert [l for _, l in b._compartment_spans("x")] == pytest.approx(
        [b.inner_l / 3] * 3
    )


# --- Geometry: each modifier removes the material it should -----------------


def test_notch_removes_exact_volume():
    """Notch volume is thickness x width x depth; width auto = span/2."""
    plain = GridfinityBox(3, 2, 6, dividers=[Divider("x", 0.5)])
    notched = GridfinityBox(3, 2, 6, dividers=[Divider("x", 0.5, notch_depth=5)])
    d = notched.divider_list[0]
    expected = d.thickness * (notched.outer_w / 2) * 5
    assert _vol(plain) - _vol(notched) == pytest.approx(expected, rel=1e-6)


def test_notch_explicit_width():
    plain = GridfinityBox(3, 2, 6, dividers=[Divider("x", 0.5)])
    notched = GridfinityBox(
        3, 2, 6, dividers=[Divider("x", 0.5, notch_depth=6, notch_width=20)]
    )
    expected = notched.divider_list[0].thickness * 20 * 6
    assert _vol(plain) - _vol(notched) == pytest.approx(expected, rel=1e-6)


@pytest.mark.parametrize("angle", [45, 65, 80])
def test_roof_removes_exact_volume(angle):
    """Symmetric ridge: two triangles of (th/2 x rise), across the wall span."""
    plain = GridfinityBox(3, 2, 6, dividers=[Divider("x", 0.5)])
    roofed = GridfinityBox(3, 2, 6, dividers=[Divider("x", 0.5, top_angle=angle)])
    d = roofed.divider_list[0]
    rise = (d.thickness / 2) * math.tan(math.radians(angle))
    expected = 2 * (0.5 * (d.thickness / 2) * rise) * roofed.outer_w
    assert _vol(plain) - _vol(roofed) == pytest.approx(expected, rel=1e-6)


def test_roof_works_on_y_axis():
    """Regression: the cutter was positioned by a guessed extrude direction and
    landed clear of the wall entirely, silently removing nothing."""
    plain = GridfinityBox(3, 2, 6, dividers=[Divider("y", 0.5)])
    roofed = GridfinityBox(3, 2, 6, dividers=[Divider("y", 0.5, top_angle=65)])
    d = roofed.divider_list[0]
    rise = (d.thickness / 2) * math.tan(math.radians(65))
    expected = 2 * (0.5 * (d.thickness / 2) * rise) * roofed.outer_l
    assert _vol(plain) - _vol(roofed) == pytest.approx(expected, rel=1e-6)


def test_per_divider_thickness_and_height():
    thick = GridfinityBox(3, 2, 6, dividers=[Divider("x", 0.5, thickness=2.4)])
    thin = GridfinityBox(3, 2, 6, dividers=[Divider("x", 0.5, thickness=1.2)])
    assert _vol(thick) == pytest.approx(2 * _vol(thin), rel=1e-6)

    short = GridfinityBox(3, 2, 6, dividers=[Divider("x", 0.5, height=10)])
    full = GridfinityBox(3, 2, 6, dividers=[Divider("x", 0.5)])
    assert _vol(short) < _vol(full)
    assert _vol(short) == pytest.approx(
        _vol(full) * 10 / full.max_height, rel=1e-6
    )


def test_height_clamped_to_max():
    b = GridfinityBox(3, 2, 6, dividers=[Divider("x", 0.5, height=10_000)])
    full = GridfinityBox(3, 2, 6, dividers=[Divider("x", 0.5)])
    assert _vol(b) == pytest.approx(_vol(full), rel=1e-6)


# --- Whole-box validity (default fillets, per conftest policy) --------------


@pytest.mark.parametrize(
    "dividers",
    [
        [Divider("x", 0.5)],
        [Divider("x", 0.25), Divider("x", 0.75)],
        [Divider("x", 0.5, notch_depth=8)],
        [Divider("x", 0.33, top_angle=65), Divider("x", 0.66, top_angle=65)],
        [Divider("x", 0.4), Divider("y", 0.5)],
    ],
)
def test_box_renders_valid_with_dividers(dividers):
    r = GridfinityBox(3, 2, 6, dividers=dividers).render()
    assert r.val().isValid()
    assert len(r.solids().vals()) == 1


def test_dividers_compose_with_labels_and_scoops():
    """Scoops follow y-dividers and labels follow x-compartments; both must
    still work when the layout is unequal rather than evenly spaced."""
    r = GridfinityBox(
        3, 2, 6, labels=True, scoops=True,
        dividers=[Divider("x", 0.4), Divider("x", 0.7), Divider("y", 0.5)],
    ).render()
    assert r.val().isValid()


def test_solid_box_ignores_dividers():
    assert GridfinityBox(3, 2, 6, solid=True,
                         dividers=[Divider("x", 0.5)]).render_dividers() is None


# --- Fillet radius clamping -------------------------------------------------


def test_explicit_dividers_get_the_same_fillet_clamp_as_counts():
    """Regression from the P2 refactor.

    safe_fillet_rad tested the raw length_div/width_div integers, so a bin
    built from explicit Divider objects skipped the divider-aware clamp and
    asked for a radius larger than the wall it had to blend into. Latent at the
    default wall thickness; only visible once the clamp actually binds.
    """
    counts = GridfinityBox(3, 2, 6, length_div=1, wall_th=1.6)
    objects = GridfinityBox(3, 2, 6, dividers=[Divider("x", 0.5)], wall_th=1.6)
    assert objects.safe_fillet_rad == pytest.approx(counts.safe_fillet_rad)


def test_notched_divider_clamps_the_fillet_radius():
    """A notch leaves topology the kernel cannot blend at 1.1mm. Clamping keeps
    the blend instead of dropping it -- measured: 0.8 fails, 0.5 succeeds."""
    from cqgridfinity.constants import GR_NOTCH_FILLET_MAX

    plain = GridfinityBox(3, 2, 6, dividers=[Divider("x", 0.5)])
    notched = GridfinityBox(3, 2, 6, dividers=[Divider("x", 0.5, notch_depth=8)])
    assert notched.safe_fillet_rad <= GR_NOTCH_FILLET_MAX
    assert notched.safe_fillet_rad < plain.safe_fillet_rad


def test_notched_divider_fillet_actually_applies():
    """The clamp is only worth having if the fillet then succeeds."""
    import warnings as _w

    with _w.catch_warnings(record=True) as caught:
        _w.simplefilter("always")
        r = GridfinityBox(
            3, 2, 6, dividers=[Divider("x", 0.5, notch_depth=8)]
        ).render()
        assert not [c for c in caught if "fillet" in str(c.message)], (
            "fillet still failing on a notched divider"
        )
    assert r.val().isValid()


# --- Filenames --------------------------------------------------------------


def test_filename_marks_explicit_layout():
    """An unequal layout must not be named like an evenly divided bin."""
    even = GridfinityBox(3, 2, 6, length_div=2)
    uneven = GridfinityBox(3, 2, 6, dividers=[Divider("x", 0.25), Divider("x", 0.75)])
    assert even.filename() == "gf_bin_3x2x6_div2"
    assert uneven.filename() == "gf_bin_3x2x6_divu2"
    assert even.filename() != uneven.filename()
