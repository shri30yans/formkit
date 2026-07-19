# API reference

Generated from source with **mkdocstrings** (type hints + docstrings).

| Module | Contents |
|--------|----------|
| [Document](document.md) | Params, timeline, rebuild, export, hull, extrude |
| [Body](body.md) | Cut, hole, shell, fillet, boss, … |
| [Frame](frame.md) | Placement and face frames |
| [Profile & Shape](profile.md) | 2D primitives, compose, offset, hull |
| [Solids](solid.md) | Box, Cylinder, … |
| [Params](param.md) | ParamRef, Expr |
| [Queries](query.md) | Face / edge selectors |
| [Errors](errors.md) | FeatureError, ValidationError |

```bash
pip install -e ".[docs]"
mkdocs build
mkdocs serve
```
