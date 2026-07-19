"""Complex formkit designs — enclosure, grille, lofted cup, stacked bosses."""

from __future__ import annotations

from pathlib import Path

import pytest

from formkit import (
    Box,
    Circle,
    Document,
    Frame,
    Rect,
    Slot,
)


def test_align_min_stacks_on_bed():
    """build123d lesson: Align.MIN puts the part on the XY plane of its Frame."""
    doc = Document()
    t = doc.param("t", 8)
    base = doc.add(Box(40, 30, t, align_z="min"), at=Frame.origin, name="base")
    rib = doc.add(Box(4, 30, 12, align_z="min"), at=Frame.translate(0, 0, t), name="rib")
    doc.join(base, rib)
    m = doc.metrics()
    # Bottom should sit near z=0, top near t+12
    assert m["bbox_mm"]["z"] == pytest.approx(20, abs=0.5)
    c = m["center_mm"]["z"]
    assert c > 5  # not centered at 0


def test_shell_hollows_box():
    doc = Document()
    box = doc.add(Box(50, 40, 30, align_z="min"), name="box")
    solid_vol = doc.metrics()["volume_mm3"]
    box.shell(2.0, open_face=box.faces.z_max)
    hollow = doc.metrics()["volume_mm3"]
    assert hollow < solid_vol * 0.5
    assert hollow > 1000


def test_pad_boss_on_face():
    doc = Document()
    base = doc.add(Box(40, 40, 5, align_z="min"), name="base")
    base.pad(Circle(6), height=10, at=(0, 0))
    m = doc.metrics()
    assert m["bbox_mm"]["z"] == pytest.approx(15, abs=0.5)


def test_emboss_text():
    doc = Document()
    plate = doc.add(Box(60, 30, 3, align_z="min"), name="plate")
    plate.emboss("FK", font_size=12, height=0.8, at=(0, 0))
    m = doc.metrics()
    assert m["bbox_mm"]["z"] >= 3.5


def test_loft_between_circles():
    doc = Document()
    body = doc.loft(
        [Circle(15), Circle(8)],
        frames=[Frame.origin, Frame.offset_z(25)],
        name="funnel",
    )
    m = doc.metrics(body)
    assert m["bbox_mm"]["z"] == pytest.approx(25, abs=0.5)
    assert m["volume_mm3"] > 0


def test_complex_electronics_enclosure(tmp_path: Path):
    """Multi-feature enclosure: shell, USB cut, vents, heat-set holes, lid lip boss."""
    doc = Document("Enclosure")
    L = doc.param("L", 70)
    W = doc.param("W", 45)
    H = doc.param("H", 25)
    wall = doc.param("wall", 1.6)
    clear = doc.param("clear", 0.4)

    # Outer shell — sit on bed
    box = doc.add(Box(L, W, H, align_z="min"), name="base")
    box.fillet(radius=2, edges=box.edges.vertical)
    box.shell(wall, open_face=box.faces.z_max)

    # USB port cut on front (Y-min face) via mid-height frame rotated
    # Approximate: cut rectangle through Y from front using a side workplane
    usb = Rect(12, 7)
    # Place cut on XZ plane at y = -W/2
    front = Frame.from_axes(origin=(0, -(W / 2), H / 2), rx=90)
    box.cut(usb, through=True, on=front)

    # Vent grille on lid plane (near top, cut down)
    box.holes_grid(
        3.5,
        count_x=5,
        count_y=3,
        spacing_x=8,
        spacing_y=7,
        depth=wall * 2,
        on=box.faces.z_max,
        center=(0, 5),
    )

    # Corner mounting holes (M3 clearance)
    margin = wall + 4
    for dx, dy in [
        (L / 2 - margin, W / 2 - margin),
        (-(L / 2 - margin), W / 2 - margin),
        (L / 2 - margin, -(W / 2 - margin)),
        (-(L / 2 - margin), -(W / 2 - margin)),
    ]:
        box.hole(diameter=3.2, on=box.faces.z_min, at=(dx, dy), depth=H)

    # Interior boss pad for PCB standoff
    box.pad(Circle(4), height=3, at=(0, 0))

    m = doc.metrics()
    assert m["bbox_mm"]["x"] == pytest.approx(70, abs=5.0)  # fillet may shrink slightly
    assert m["volume_mm3"] > 2000
    kinds = {f["kind"] for f in m["timeline"]}
    assert {"add_solid", "shell", "cut_profile", "holes_grid", "hole", "pad"} <= kinds

    out = tmp_path / "enclosure.stl"
    doc.export(str(out))
    assert out.stat().st_size > 500


def test_complex_l_bracket():
    """Two plates at 90° joined — classic multi-body placement design."""
    doc = Document("LBracket")
    w = doc.param("w", 50)
    t = doc.param("t", 4)
    arm = doc.param("arm", 40)

    horizontal = doc.add(Box(w, arm, t, align_z="min"), name="horiz")
    # Vertical plate: rotate 90° about X, sit at end of arm
    vertical = doc.add(
        Box(w, arm, t, align_z="min"),
        at=Frame.from_axes(origin=(0, arm / 2, 0), rx=90),
        name="vert",
    )
    doc.join(horizontal, vertical)
    horizontal.holes_polar(diameter=4.2, count=2, radius=12, depth=t)

    m = doc.metrics()
    assert m["bbox_mm"]["z"] > 20  # arm ~40 vertical
    assert m["volume_mm3"] > 0


def test_grille_slot_pattern():
    doc = Document("Grille")
    plate = doc.add(Box(80, 50, 2.5, align_z="min"), name="plate")
    # Unit slot body then pattern — or cut slots in a grid via repeated cuts
    for i in range(-2, 3):
        for j in range(-1, 2):
            plate.cut(
                Slot(12, 3),
                height=2.5,
                on=Frame.translate(i * 14, j * 14, 1.25),
            )
    assert doc.metrics()["volume_mm3"] < 80 * 50 * 2.5


def test_counterbore_mount():
    doc = Document()
    plate = doc.add(Box(40, 40, 8, align_z="min"), name="plate")
    plate.counterbore(
        diameter=3.2,
        depth=8,
        counter_diameter=6,
        counter_depth=3,
        at=(10, 10),
    )
    assert doc.metrics()["volume_mm3"] < 40 * 40 * 8
