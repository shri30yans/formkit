# formkit

Body-centric parametric CAD for Python — compose shapes, hull/offset, place solids, export STL/STEP.

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,docs]"
pytest -q
mkdocs serve          # docs at http://127.0.0.1:8000
python examples/formkit_mount.py
```

```python
from formkit import Document, Frame, Box, Circle, hull, Rect

# Placement-first solids
doc = Document("Bracket")
t = doc.param("t", 8)
base = doc.add(Box(60, 40, t, align_z="min"), name="base")
rib = doc.add(Box(4, 40, 20, align_z="min"), at=Frame.translate(0, 0, t), name="rib")
doc.join(base, rib)
base.cut(Circle(6), through=True, on=Frame.offset_z(t / 2))

# CSG: hull + offset + twist
outline = hull(Circle(8, center=(-20, 0)), Circle(8, center=(20, 0))).offset(2)
doc.extrude(outline, height=4, name="link")
doc.extrude(Rect(10, 10), height=20, twist=45, name="twist")
doc.export("part.stl")
```

## Documentation

| | |
|--|--|
| Guides + API | `mkdocs serve` (MkDocs Material + **mkdocstrings** autodoc) |
| Examples | `examples/` |

## Install

```bash
pip install -e .
```

Requires Python 3.11+. Geometry backend is build123d/OCCT (private).

## License

MIT
