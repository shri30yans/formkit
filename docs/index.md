# formkit

**Body-centric parametric CAD for Python.** Place solids in space, compose 2D shapes, hull/offset like OpenSCAD, rebuild from a feature timeline, export STL/STEP.

build123d / OpenCascade is a **private** backend — your code never imports it.

```python
from formkit import Document, Frame, Box, Circle, hull

doc = Document("Bracket")
t = doc.param("t", 8)
base = doc.add(Box(60, 40, t, align_z="min"), name="base")
rib = doc.add(Box(4, 40, 20, align_z="min"), at=Frame.translate(0, 0, t), name="rib")
doc.join(base, rib)
base.cut(Circle(6), through=True, on=Frame.offset_z(t / 2))
doc.export("bracket.stl")
```

## Why formkit?

| Idea | What it means |
|------|----------------|
| Bodies first | Name solids, operate on them (`.cut`, `.shell`, `.fillet`) |
| Explicit placement | Every solid sits on a `Frame` — no hidden workplanes |
| Composable 2D | `Rect(...).offset(2).cut(Circle(...))` then extrude |
| CSG power tools | `hull()`, `.offset()`, `extrude(..., twist=, scale=)` |
| Parametric | Change params → rebuild → new mesh |

## Docs map

- [Getting started](getting-started.md) — install and first STL
- [Concepts](concepts.md) — Document, Body, Frame, Shape
- [Guides](guides/shapes.md) — shapes, solids, features, CSG, params
- [Examples](examples.md) — bracket, enclosure, mount
- [API reference](api/index.md) — autodoc from source (mkdocstrings)

## Autodocs

API pages are generated from type hints and docstrings via
[MkDocs](https://www.mkdocs.org/) + [mkdocstrings](https://mkdocstrings.github.io/).

```bash
pip install -e ".[docs]"
mkdocs serve   # http://127.0.0.1:8000
```
