# Params & rebuild

## Parameters

```python
w = doc.param("w", 60, unit="mm", comment="width")
doc.param("h", "w / 2")          # expression string
half = w / 2                     # Expr from ParamRef
doc.resolve(half)                # → float
doc["w"]                         # → 60.0
doc.set_params(w=80)             # dirty → rebuild on next metrics/export
```

Use param names (or `ParamRef` / `Expr`) anywhere a size is accepted: `Box("w", 40, "t")`.

## Inspect & serialize

```python
print(doc.inspect())   # bbox, volume, timeline, params
data = doc.to_dict()
doc2 = Document.from_dict(data)
doc2.export("roundtrip.stl")
```

## Errors

Failed features raise `FeatureError` with timeline index and kind — they do not silently no-op.

```python
from formkit import FeatureError

try:
    doc.rebuild()
except FeatureError as e:
    print(e.index, e.kind, e.message)
```
