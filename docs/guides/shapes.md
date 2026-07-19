# Shapes & profiles

## Primitives

```python
from formkit import Rect, Rectangle, RoundedRect, Circle, Ellipse, Slot, Polygon, RegularPolygon

Rect(40, 30)
Rect(40, 30).fillet(3)          # → RoundedRect
Circle(10)                      # radius
Circle(diameter=20)
Ellipse(12, 8)
Slot(18, 6)
RegularPolygon(8, sides=6)
Polygon([(0, 0), (10, 0), (5, 8)])
```

`Rectangle` is an alias of `Rect`.

## Compose

```python
outline = (
    Rect(60, 40)
    .add(Circle(6), at=(20, 0))
    .cut(Circle(4), at=(-20, 12))
    .cut(Slot(18, 6))
)
doc.extrude(outline, height=4)
```

## Offset

Grow or shrink the resolved outline (OpenSCAD `offset` — prefer this over minkowski):

```python
rounded = Rect(40, 20).offset(3)     # grow
inset   = Rect(50, 30).offset(-1)    # shrink
```

## Helpers

```python
from formkit import profile_union, profile_cut

profile_union(Rect(20, 20), Circle(8))   # same as .add
profile_cut(Rect(20, 20), Circle(5))     # same as .cut
```

See also [Hull, offset & extrude](csg.md).
