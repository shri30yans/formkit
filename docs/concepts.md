# Concepts

## Document

A `Document` owns:

1. **Parameters** (`doc.param("w", 60)`)
2. **Named bodies** (`base`, `lid`, …)
3. A **feature timeline** (add → cut → fillet → …)
4. Rebuild + export

```python
doc = Document("Part")
w = doc.param("w", 60)
body = doc.add(Box(w, 40, 8, align_z="min"), name="base")
doc.set_params(w=80)   # marks dirty → next metrics/export rebuilds
```

`inspect()`, `to_dict()`, and `from_dict()` support tooling / agent loops.

## Body

A `Body` is a handle into the timeline. Methods append features; they return `self` for chaining.

```python
body.shell(1.6).cut(Circle(4), through=True).fillet(radius=1.5)
```

## Frame

A `Frame` is an explicit pose: origin + Euler angles (degrees).

| Helper | Use |
|--------|-----|
| `Frame.origin` / `Frame.xy` | Default workplane |
| `Frame.translate(x, y, z)` | Move |
| `Frame.offset_z(z)` | Stack along Z |
| `Frame.from_axes(origin=..., rx=90)` | Angled plane |
| `Frame.on_face(body.faces.y_min)` | Glue to a body face |

Use **`align_z="min"`** on boxes/cylinders so they sit on the Frame XY plane (critical for stacking).

## Profile / Shape

2D regions are immutable values:

- Primitives: `Rect`, `Circle`, `Slot`, …
- Compose: `.add()`, `.cut()`, `.offset()`
- Hull: `hull(p1, p2, …)`
- Then `doc.extrude(...)` or `body.cut(...)`

## Backend boundary

Only `formkit.backend.occt` imports build123d. Public code stays portable and agent-friendly.
