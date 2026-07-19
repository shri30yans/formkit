"""Compose a 2D shape from primitives, then extrude."""

from pathlib import Path

from formkit import Circle, Document, Rect, Slot

OUT = Path(__file__).resolve().parents[1] / ".formkit_out"
OUT.mkdir(exist_ok=True)


def main() -> None:
    outline = (
        Rect(60, 40)
        .cut(Circle(4), at=(-20, 12))
        .cut(Circle(4), at=(20, 12))
        .cut(Circle(4), at=(-20, -12))
        .cut(Circle(4), at=(20, -12))
        .cut(Slot(18, 6), at=(0, 0))
    )

    doc = Document("Plate")
    plate = doc.extrude(outline, height=4, name="plate")
    plate.fillet(radius=1.5, edges=plate.edges.vertical)

    path = OUT / "shape_plate.stl"
    doc.export(str(path))
    print(doc.inspect()["bbox_mm"], "→", path)


if __name__ == "__main__":
    main()
