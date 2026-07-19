# Body features

Operate on a named body after it exists:

```python
body = doc.add(Box(50, 40, 30, align_z="min"), name="base")
body.fillet(radius=2, edges=body.edges.vertical)
body.shell(1.6, open_face=body.faces.z_max)
body.cut(Rect(12, 7), through=True, on=Frame.from_axes(origin=(0, -20, 10), rx=90))
body.holes_grid(3.5, count_x=4, count_y=3, spacing_x=8, spacing_y=7, depth=3)
body.pad(Circle(5), height=6, at=(0, 0))
body.boss(outer_d=10, height=8, hole_d=4, at=(10, 10))
body.lip(width=1.0, height=1.2, mode="male")
body.emboss("OK", font_size=8, height=0.6)
body.deboss("ID", font_size=6, depth=0.4)
```

## Face & edge queries

```python
body.faces.z_max / z_min / x_max / y_min / largest
body.edges.vertical / horizontal / top / bottom / all
```

Workplane on a face:

```python
body.cut(Circle(5), through=True, on=Frame.on_face(body.faces.y_min))
```

## Holes

```python
body.hole(diameter=3.2, depth=8, at=(10, 10))
body.counterbore(diameter=3.2, depth=8, counter_diameter=6, counter_depth=3, at=(0, 0))
body.holes_polar(diameter=3.2, count=4, radius=18, depth=t)
```
