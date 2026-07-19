"""formkit core — body-centric CAD kernel tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from formkit import (
    Box,
    Circle,
    Cylinder,
    Document,
    Frame,
    Rect,
    RoundedRect,
    Slot,
)


def test_params_and_expr_arithmetic():
    doc = Document()
    w = doc.param("w", 80)
    doc.param("h", "w / 2")
    assert doc["h"] == 40
    half = w / 2
    assert doc.resolve(half) == 40


def test_placed_bodies_join_and_mid_cut(tmp_path: Path):
    doc = Document("Bracket")
    w = doc.param("w", 60)
    h = doc.param("h", 40)
    t = doc.param("t", 8)

    base = doc.add(Box(w, h, t), at=Frame.origin, name="base")
    rib = doc.add(Box(4, h, 20), at=Frame.translate(0, 0, t), name="rib")
    doc.join(base, rib)

    mid = Frame.translate(0, 0, t / 2)
    base.cut(Circle(6), through=True, on=mid)
    base.fillet(radius=1.2, edges=base.edges.vertical)
    base.holes_polar(diameter=3.2, count=4, radius=18, depth=t)

    m = doc.metrics()
    assert m["bbox_mm"]["x"] == pytest.approx(60, abs=0.5)
    assert m["bbox_mm"]["z"] == pytest.approx(28, abs=1.0) or m["bbox_mm"]["z"] > 20
    assert m["volume_mm3"] > 1000

    out = tmp_path / "bracket.stl"
    doc.export(str(out))
    assert out.exists() and out.stat().st_size > 100


def test_extrude_profile_and_hole():
    doc = Document("Plate")
    doc.param("t", 4)
    plate = doc.extrude(RoundedRect(50, 30, 3), height="t", name="plate")
    plate.hole(diameter=5, on=plate.faces.z_max, at=(0, 0), depth="t")
    m = doc.metrics("plate")
    assert m["bbox_mm"]["x"] == pytest.approx(50, abs=0.5)
    assert m["volume_mm3"] < 50 * 30 * 4


def test_holes_grid():
    doc = Document("Vent")
    base = doc.add(Box(80, 60, 3), name="base")
    before = doc.metrics()["volume_mm3"]
    base.holes_grid(4, count_x=5, count_y=4, spacing_x=12, spacing_y=10, depth=3)
    after = doc.metrics()["volume_mm3"]
    assert after < before * 0.95


def test_param_rebuild_changes_volume():
    doc = Document()
    doc.param("w", 40)
    doc.param("t", 5)
    doc.add(Box("w", 20, "t"), name="base")
    v1 = doc.metrics()["volume_mm3"]
    doc.set_params(w=80)
    v2 = doc.metrics()["volume_mm3"]
    assert v2 == pytest.approx(v1 * 2, rel=0.05)


def test_cut_body_boolean():
    doc = Document()
    block = doc.add(Box(30, 30, 30), name="block")
    tool = doc.add(Cylinder(40, diameter=10), at=Frame.origin, name="tool")
    doc.cut_body(block, tool)
    m = doc.metrics("block")
    assert m["volume_mm3"] < 30 * 30 * 30


def test_pattern_polar_body():
    doc = Document()
    peg = doc.add(Cylinder(5, diameter=3), at=Frame.translate(10, 0, 0), name="peg")
    ring = doc.pattern_polar(peg, count=6, radius=10, name="ring")
    m = doc.metrics(ring)
    assert m["volume_mm3"] > 0


def test_mirror():
    doc = Document()
    doc.add(Box(10, 20, 5), at=Frame.translate(15, 0, 0), name="half")
    mirrored = doc.mirror("half", plane="YZ", name="full")
    # mirrored body exists
    assert "full" in doc.bodies()
    assert doc.metrics(mirrored)["volume_mm3"] > 0


def test_slot_cut():
    doc = Document()
    base = doc.add(Box(40, 20, 4), name="base")
    base.cut(Slot(16, 4), height=4, on=Frame.xy)
    assert doc.metrics()["volume_mm3"] < 40 * 20 * 4


def test_no_build123d_leak_in_public_namespace():
    import formkit

    public = set(formkit.__all__)
    assert "BuildPart" not in public
    assert "Mode" not in public
    assert "Plane" not in dir(formkit)
