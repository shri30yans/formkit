# Examples

Run from the repo root with the venv active. STLs write to `.formkit_out/`.

## Shape plate

Compose rect − circles − slot, extrude, fillet.

```bash
python examples/formkit_shape.py
```

## Bracket

Stacked boxes with `align_z="min"`, mid cut, polar holes, param rebuild.

```bash
python examples/formkit_bracket.py
```

## Enclosure

Shell, USB side cut, vent grid, corner holes, pad boss, emboss.

```bash
python examples/formkit_enclosure.py
```

## Mount (CSG)

2D hull + offset + holes, 3D hull arm, twisted boss.

```bash
python examples/formkit_mount.py
```

```python
from formkit import Circle, Cylinder, Document, Frame, Rect, hull

doc = Document("Mount")
outline = hull(
    Circle(8, center=(-25, -15)),
    Circle(8, center=(25, -15)),
    Circle(8, center=(0, 20)),
).offset(2)
plate = doc.extrude(outline, height=4, name="plate")
arm = doc.hull(
    (Cylinder(height=6, diameter=10), Frame.translate(0, 20, 4)),
    (Cylinder(height=6, diameter=6), Frame.translate(0, 45, 12)),
    name="arm",
)
doc.join(plate, arm)
```
