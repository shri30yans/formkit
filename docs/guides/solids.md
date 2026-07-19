# Solids & placement

## Primitives

```python
from formkit import Box, Cylinder, Cone, Sphere, Wedge, Frame

doc.add(Box(60, 40, 8, align_z="min"), name="base")
doc.add(Cylinder(height=20, diameter=10, align_z="min"), at=Frame.translate(0, 0, 8))
doc.add(Sphere(radius=5), at=Frame.translate(20, 0, 15))
```

## Stacking (important)

Without `align_z="min"`, boxes are centered on the Frame and stacking is confusing.

```python
t = doc.param("t", 8)
base = doc.add(Box(60, 40, t, align_z="min"), name="base")
rib  = doc.add(Box(4, 40, 20, align_z="min"), at=Frame.translate(0, 0, t), name="rib")
doc.join(base, rib)
```

## Boolean between bodies

```python
doc.join(target, source)       # fuse
doc.cut_body(target, tool)     # subtract
doc.intersect(target, tool)
```

## Patterns

```python
doc.mirror(body, plane="YZ")
doc.pattern_grid(body, count_x=3, count_y=2, spacing_x=20, spacing_y=15)
doc.pattern_polar(body, count=6, radius=30)
```

## Loft

```python
from formkit import Circle, Frame

doc.loft(
    [Circle(15), Circle(8)],
    frames=[Frame.origin, Frame.offset_z(25)],
    name="funnel",
)
```
