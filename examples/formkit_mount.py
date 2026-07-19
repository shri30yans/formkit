"""Organic mount — hull + offset + twist (OpenSCAD-class complexity)."""

from pathlib import Path

from formkit import Circle, Cylinder, Document, Frame, Rect, hull

OUT = Path(__file__).resolve().parents[1] / ".formkit_out"
OUT.mkdir(exist_ok=True)


def main() -> None:
    doc = Document("Mount")

    outline = (
        hull(
            Circle(8, center=(-25, -15)),
            Circle(8, center=(25, -15)),
            Circle(8, center=(0, 20)),
        )
        .offset(2)
        .cut(Circle(3.2, center=(-25, -15)))
        .cut(Circle(3.2, center=(25, -15)))
    )
    plate = doc.extrude(outline, height=4, name="plate")
    plate.fillet(radius=1.0, edges=plate.edges.vertical)

    arm = doc.hull(
        (Cylinder(height=6, diameter=10), Frame.translate(0, 20, 4)),
        (Cylinder(height=6, diameter=6), Frame.translate(0, 45, 12)),
        name="arm",
    )
    doc.join(plate, arm)

    boss = doc.extrude(
        Rect(8, 8),
        height=16,
        twist=45,
        at=Frame.translate(0, -15, 4),
        name="boss",
    )
    doc.join(plate, boss)

    path = OUT / "mount.stl"
    doc.export(str(path))
    print(doc.inspect()["bbox_mm"], "→", path)


if __name__ == "__main__":
    main()
