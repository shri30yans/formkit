"""Success-criteria bracket — stacked with align_z=min (build123d Align lesson)."""

from pathlib import Path

from formkit import Box, Circle, Document, Frame

OUT = Path(__file__).resolve().parents[1] / ".formkit_out"
OUT.mkdir(exist_ok=True)


def main() -> None:
    doc = Document("Bracket")
    w = doc.param("w", 60)
    h = doc.param("h", 40)
    t = doc.param("t", 8)

    base = doc.add(Box(w, h, t, align_z="min"), at=Frame.origin, name="base")
    rib = doc.add(Box(4, h, 20, align_z="min"), at=Frame.translate(0, 0, t), name="rib")
    doc.join(base, rib)

    base.cut(Circle(6), through=True, on=Frame.offset_z(t / 2))
    base.fillet(radius=1.5, edges=base.edges.vertical)
    base.holes_polar(diameter=3.2, count=4, radius=18, depth=t)

    path = OUT / "bracket.stl"
    doc.export(str(path))
    print(doc.metrics())
    print("wrote", path)

    doc.set_params(w=80)
    doc.export(str(OUT / "bracket_wide.stl"))
    print("wide bbox", doc.metrics()["bbox_mm"])


if __name__ == "__main__":
    main()
