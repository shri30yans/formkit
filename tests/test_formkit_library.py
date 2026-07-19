"""Composable shapes + cleaned kernel surface."""

from __future__ import annotations

from pathlib import Path

import pytest

from formkit import (
    Box,
    Circle,
    Document,
    Ellipse,
    FeatureError,
    Frame,
    Rect,
    RegularPolygon,
    Shape,
)


def test_shape_add_and_cut():
    outline = Rect(40, 30).cut(Circle(5), at=(10, 0)).add(Circle(4), at=(-14, 0))
    assert isinstance(outline, Shape)
    assert len(outline.ops) == 3

    doc = Document()
    doc.extrude(outline, height=5, name="plate")
    m = doc.metrics()
    assert m["bbox_mm"]["x"] == pytest.approx(40, abs=1.0)
    assert m["volume_mm3"] > 0


def test_face_frame_cut():
    doc = Document()
    b = doc.add(Box(40, 30, 20, align_z="min"), name="base")
    b.shell(1.5)
    before = doc.metrics()["volume_mm3"]
    b.cut(Circle(4), through=True, on=Frame.on_face(b.faces.y_min))
    assert doc.metrics()["volume_mm3"] < before


def test_lip_male_increases_height():
    doc = Document()
    b = doc.add(Box(40, 30, 15, align_z="min"), name="base")
    b.shell(1.5)
    z0 = doc.metrics()["bbox_mm"]["z"]
    b.lip(width=1.0, height=1.2, mode="male")
    assert doc.metrics()["bbox_mm"]["z"] == pytest.approx(z0 + 1.2, abs=0.3)


def test_boss_with_hole():
    doc = Document()
    b = doc.add(Box(40, 40, 5, align_z="min"), name="base")
    b.boss(outer_d=10, height=8, hole_d=4, at=(0, 0))
    m = doc.metrics()
    assert m["bbox_mm"]["z"] == pytest.approx(13, abs=0.5)
    assert "boss" in {f["kind"] for f in m["timeline"]}


def test_ellipse_and_hex_profiles():
    doc = Document()
    plate = doc.extrude(Ellipse(12, 8), height=3, name="plate")
    plate.cut(RegularPolygon(4, sides=6), height=3, on=Frame.offset_z(1.5))
    assert doc.metrics()["volume_mm3"] > 0


def test_inspect_and_to_dict_roundtrip(tmp_path: Path):
    doc = Document("Round")
    doc.param("w", 40)
    base = doc.add(Box("w", 30, 5, align_z="min"), name="base")
    base.hole(diameter=5, depth=5)
    snap = doc.inspect()
    assert snap["feature_count"] >= 2
    assert "bbox_mm" in snap
    assert "printability" not in snap

    data = doc.to_dict()
    doc2 = Document.from_dict(data)
    assert doc2.metrics()["volume_mm3"] == pytest.approx(doc.metrics()["volume_mm3"], rel=1e-6)
    out = tmp_path / "round.stl"
    doc2.export(str(out))
    assert out.stat().st_size > 100


def test_feature_error_on_unknown_kind():
    from formkit.features import Feature

    doc = Document()
    doc.add(Box(10, 10, 10, align_z="min"), name="base")
    doc._add_feature(Feature("nope", {"body": "base"}))
    with pytest.raises(FeatureError):
        doc.rebuild()


def test_deboss():
    doc = Document()
    p = doc.add(Box(50, 30, 4, align_z="min"), name="plate")
    before = doc.metrics()["volume_mm3"]
    p.deboss("OK", font_size=10, depth=0.5)
    assert doc.metrics()["volume_mm3"] < before
