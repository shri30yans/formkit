# Hull, offset & extrude

OpenSCAD-class generative tools, mapped onto formkit’s value + timeline model.

## 2D hull

```python
from formkit import hull, Circle, Document

link = hull(
    Circle(6, center=(-20, 0)),
    Circle(6, center=(20, 0)),
)
doc = Document("Link")
doc.extrude(link, height=4)
```

## Offset

```python
outline = hull(
    Circle(8, center=(-25, -15)),
    Circle(8, center=(25, -15)),
    Circle(8, center=(0, 20)),
).offset(2).cut(Circle(3.2, center=(-25, -15)))
```

Prefer `.offset()` for rounded outlines — do **not** use 3D minkowski for printable boxes.

## 3D hull

```python
from formkit import Cylinder, Frame

arm = doc.hull(
    (Cylinder(height=6, diameter=10), Frame.origin),
    (Cylinder(height=6, diameter=6), Frame.translate(40, 0, 8)),
    name="arm",
)

# Or existing bodies
blob = doc.hull(body_a, body_b, consume=True)
```

## Rich extrude

```python
doc.extrude(profile, height=h)                    # plain
doc.extrude(Rect(20, 20), height=60, twist=90)    # degrees over height
doc.extrude(Circle(15), height=40, scale=0.3)     # end scale (float or (sx, sy))
doc.extrude(Rect(30, 20), height=25, taper=5)     # draft degrees
```

`taper` applies on the simple extrude path. `twist` / `scale` use lofted sections under the hood.
