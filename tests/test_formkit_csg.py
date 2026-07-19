"""CSG parity — offset, hull (2D/3D), extrude twist/scale/taper."""

from __future__ import annotations

from pathlib import Path

import pytest

from formkit import (
    Circle,
    Cylinder,
    Document,
    Frame,
    Rect,
    Sphere,
    hull,
)


def test_offset_grows_bbox():
    sharp = Document()
    sharp.extrude(Rect(40, 20), height=3, name="sharp")
    rounded = Document()
    rounded.extrude(Rect(40, 20).offset(3), height=3, name="round")
    assert rounded.metrics()["bbox_mm"]["x"] == pytest.approx(
        sharp.metrics()["bbox_mm"]["x"] + 6, abs=0.5
    )
    assert rounded.metrics()["volume_mm3"] > sharp.metrics()["volume_mm3"]


def test_hull_2d_capsule():
    link = hull(Circle(6, center=(-20, 0)), Circle(6, center=(20, 0)))
    doc = Document()
    doc.extrude(link, height=4, name="link")
    m = doc.metrics()
    assert m["bbox_mm"]["x"] == pytest.approx(52, abs=1.0)
    assert m["volume_mm3"] > 400


def test_hull_2d_then_cut_holes():
    outline = hull(
        Circle(8, center=(-25, -15)),
        Circle(8, center=(25, -15)),
        Circle(8, center=(0, 20)),
    ).offset(2).cut(Circle(3.2, center=(-25, -15)))
    doc = Document()
    doc.extrude(outline, height=4)
    assert doc.metrics()["volume_mm3"] > 0


def test_hull_3d_cylinders():
    doc = Document()
    bar = doc.hull(
        (Cylinder(height=4, diameter=12), Frame.origin),
        (Cylinder(height=4, diameter=12), Frame.translate(40, 0, 0)),
        name="bar",
    )
    m = doc.metrics(bar)
    assert m["bbox_mm"]["x"] == pytest.approx(52, abs=2.0)
    assert m["volume_mm3"] > 1000


def test_hull_3d_bodies_consume():
    doc = Document()
    a = doc.add(Sphere(radius=8), at=Frame.origin, name="a")
    b = doc.add(Sphere(radius=8), at=Frame.translate(30, 0, 0), name="b")
    blob = doc.hull(a, b, name="blob", consume=True)
    doc.rebuild()
    assert "blob" in doc._solids
    assert "a" not in doc._solids
    assert doc.metrics(blob)["volume_mm3"] > 0


def test_extrude_twist():
    doc = Document()
    doc.extrude(Rect(20, 20), height=40, twist=90, name="twist")
    m = doc.metrics()
    assert m["bbox_mm"]["z"] == pytest.approx(40, abs=0.5)
    # Twisted square spans more than 20 in XY diagonal sense
    assert m["bbox_mm"]["x"] > 20


def test_extrude_scale():
    scaled = Document()
    scaled.extrude(Circle(15), height=30, scale=0.3, name="coneish")
    m = scaled.metrics()
    assert m["bbox_mm"]["z"] == pytest.approx(30, abs=0.5)
    cyl = Document()
    cyl.extrude(Circle(15), height=30)
    assert m["volume_mm3"] < cyl.metrics()["volume_mm3"] * 0.7


def test_extrude_taper():
    doc = Document()
    doc.extrude(Rect(30, 20), height=25, taper=5, name="draft")
    assert doc.metrics()["volume_mm3"] > 0


def test_complex_mount_example(tmp_path: Path):
    doc = Document("Mount")
    outline = hull(
        Circle(8, center=(-25, -15)),
        Circle(8, center=(25, -15)),
        Circle(8, center=(0, 20)),
    ).offset(2).cut(Circle(3.2, center=(-25, -15))).cut(Circle(3.2, center=(25, -15)))
    plate = doc.extrude(outline, height=4, name="plate")
    arm = doc.hull(
        (Cylinder(height=6, diameter=10), Frame.translate(0, 20, 4)),
        (Cylinder(height=6, diameter=6), Frame.translate(0, 45, 12)),
        name="arm",
    )
    doc.join(plate, arm)
    boss = doc.extrude(
        Rect(8, 8), height=12, twist=45, at=Frame.translate(0, -15, 4), name="boss"
    )
    doc.join(plate, boss)
    out = tmp_path / "mount.stl"
    doc.export(str(out))
    assert out.stat().st_size > 500
    assert doc.inspect()["volume_mm3"] > 0
