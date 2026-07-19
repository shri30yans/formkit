"""Electronics-style enclosure built with formkit (complex multi-feature part).

Demonstrates: Align.MIN stacking, shell, side cut, vent grid, holes, pad boss.
"""

from pathlib import Path

from formkit import Box, Circle, Document, Frame, Rect

OUT = Path(__file__).resolve().parents[1] / ".formkit_out"
OUT.mkdir(exist_ok=True)


def build_enclosure() -> Document:
    doc = Document("Enclosure")
    L = doc.param("L", 70)
    W = doc.param("W", 45)
    H = doc.param("H", 25)
    wall = doc.param("wall", 1.6)

    box = doc.add(Box(L, W, H, align_z="min"), name="base")
    box.fillet(radius=2.0, edges=box.edges.vertical)
    box.shell(wall, open_face=box.faces.z_max)

    # USB cut on front wall
    front = Frame.from_axes(origin=(0, -(W / 2), 8), rx=90)
    box.cut(Rect(12, 7), through=True, on=front)

    # Lid vents
    box.holes_grid(3.5, count_x=5, count_y=3, spacing_x=8, spacing_y=7, depth=wall * 2)

    # Corner M3 holes from bottom
    m = wall + 4
    for dx, dy in (
        (L / 2 - m, W / 2 - m),
        (-(L / 2 - m), W / 2 - m),
        (L / 2 - m, -(W / 2 - m)),
        (-(L / 2 - m), -(W / 2 - m)),
    ):
        box.hole(diameter=3.2, on=box.faces.z_min, at=(dx, dy), depth=H)

    # PCB standoff boss
    box.pad(Circle(4), height=4, at=(0, -5))
    box.emboss("FK", font_size=8, height=0.6, at=(0, 12))

    return doc


def main() -> None:
    doc = build_enclosure()
    path = OUT / "enclosure.stl"
    doc.export(str(path))
    print(doc.metrics()["bbox_mm"], doc.metrics()["volume_mm3"])
    print("wrote", path)

    doc.set_params(L=90, W=55)
    doc.export(str(OUT / "enclosure_wide.stl"))
    print("wide", doc.metrics()["bbox_mm"])


if __name__ == "__main__":
    main()
