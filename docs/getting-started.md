# Getting started

## Requirements

- Python **3.11+**
- A working C++ toolchain is **not** required at install time — `build123d` wheels include OCCT.

## Install

```bash
git clone https://github.com/shri30yans/formkit.git
cd formkit
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Optional docs tooling:

```bash
pip install -e ".[docs]"
mkdocs serve
```

## First part (30 seconds)

```python
from formkit import Document, Box, Circle, Frame

doc = Document("Plate")
plate = doc.add(Box(50, 30, 4, align_z="min"), name="plate")
plate.hole(diameter=5, depth=4, at=(15, 0))
plate.fillet(radius=2, edges=plate.edges.vertical)
doc.export("plate.stl")
print(doc.inspect())
```

## Verify install

```bash
pytest -q
python examples/formkit_shape.py
```

Outputs land in `.formkit_out/` (gitignored).

## Project layout

```text
src/formkit/     # library
examples/        # runnable demos
tests/           # pytest
docs/            # this MkDocs site
```
