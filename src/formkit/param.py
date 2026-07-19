"""Expression-aware parameters for formkit documents."""

from __future__ import annotations

import ast
import math
import operator
from dataclasses import dataclass, field
from typing import Any, Union

_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}
_FUNCS = {
    "abs": abs,
    "min": min,
    "max": max,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "radians": math.radians,
    "degrees": math.degrees,
    "pi": math.pi,
}


@dataclass(frozen=True)
class Expr:
    """Lazy arithmetic expression over parameters."""

    text: str

    def __repr__(self) -> str:
        return f"Expr({self.text!r})"

    def __neg__(self) -> Expr:
        return Expr(f"-({self.text})")

    def __add__(self, other: Any) -> Expr:
        return Expr(f"{_tok(self)} + {_tok(other)}")

    def __radd__(self, other: Any) -> Expr:
        return Expr(f"{_tok(other)} + {_tok(self)}")

    def __sub__(self, other: Any) -> Expr:
        return Expr(f"{_tok(self)} - {_tok(other)}")

    def __rsub__(self, other: Any) -> Expr:
        return Expr(f"{_tok(other)} - {_tok(self)}")

    def __mul__(self, other: Any) -> Expr:
        return Expr(f"{_tok(self)} * {_tok(other)}")

    def __rmul__(self, other: Any) -> Expr:
        return Expr(f"{_tok(other)} * {_tok(self)}")

    def __truediv__(self, other: Any) -> Expr:
        return Expr(f"{_tok(self)} / {_tok(other)}")

    def __rtruediv__(self, other: Any) -> Expr:
        return Expr(f"{_tok(other)} / {_tok(self)}")


@dataclass(frozen=True)
class ParamRef:
    """Handle returned by Document.param — supports arithmetic → Expr."""

    name: str

    def __repr__(self) -> str:
        return f"Param({self.name!r})"

    def __neg__(self) -> Expr:
        return Expr(f"-{self.name}")

    def __add__(self, other: Any) -> Expr:
        return Expr(f"{self.name} + {_tok(other)}")

    def __radd__(self, other: Any) -> Expr:
        return Expr(f"{_tok(other)} + {self.name}")

    def __sub__(self, other: Any) -> Expr:
        return Expr(f"{self.name} - {_tok(other)}")

    def __rsub__(self, other: Any) -> Expr:
        return Expr(f"{_tok(other)} - {self.name}")

    def __mul__(self, other: Any) -> Expr:
        return Expr(f"{self.name} * {_tok(other)}")

    def __rmul__(self, other: Any) -> Expr:
        return Expr(f"{_tok(other)} * {self.name}")

    def __truediv__(self, other: Any) -> Expr:
        return Expr(f"{self.name} / {_tok(other)}")

    def __rtruediv__(self, other: Any) -> Expr:
        return Expr(f"{_tok(other)} / {self.name}")


Scalar = Union[float, int, str, ParamRef, Expr]


def _tok(value: Scalar) -> str:
    if isinstance(value, ParamRef):
        return value.name
    if isinstance(value, Expr):
        return f"({value.text})"
    if isinstance(value, str):
        return f"({value})"
    return repr(float(value))


@dataclass
class ParamDef:
    name: str
    value: float | str
    unit: str = "mm"
    comment: str = ""


@dataclass
class ParamStore:
    _params: dict[str, ParamDef] = field(default_factory=dict)

    def set(
        self,
        name: str,
        value: float | str,
        *,
        unit: str = "mm",
        comment: str = "",
    ) -> ParamRef:
        if not name.isidentifier():
            raise ValueError(f"Invalid parameter name: {name!r}")
        self._params[name] = ParamDef(name, value, unit=unit, comment=comment)
        return ParamRef(name)

    def update(self, **kwargs: float | str) -> None:
        for k, v in kwargs.items():
            if k in self._params:
                self._params[k].value = v
            else:
                self.set(k, v)

    def names(self) -> list[str]:
        return list(self._params.keys())

    def __contains__(self, name: str) -> bool:
        return name in self._params

    def __getitem__(self, name: str) -> float:
        return self.resolve(name)

    def resolve(self, value: Scalar | ParamDef) -> float:
        if isinstance(value, ParamDef):
            value = value.value
        if isinstance(value, ParamRef):
            return self.resolve(value.name)
        if isinstance(value, Expr):
            return self._eval(value.text, stack=frozenset())
        if isinstance(value, (int, float)):
            return float(value)
        if not isinstance(value, str):
            raise TypeError(f"Cannot resolve {type(value)}")
        text = value.strip()
        if text in self._params and not any(c in text for c in "+-*/()"):
            raw = self._params[text].value
            if isinstance(raw, str):
                return self._eval(raw, stack=frozenset({text}))
            return float(raw)
        return self._eval(text, stack=frozenset())

    def as_dict(self) -> dict[str, float]:
        return {n: self.resolve(n) for n in self._params}

    def _eval(self, expr: str, *, stack: frozenset[str]) -> float:
        try:
            tree = ast.parse(expr, mode="eval")
        except SyntaxError as exc:
            raise ValueError(f"Bad expression {expr!r}: {exc}") from exc
        return float(self._eval_node(tree.body, stack))

    def _eval_node(self, node: ast.AST, stack: frozenset[str]) -> float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.Name):
            if node.id in _FUNCS and not callable(_FUNCS[node.id]):
                return float(_FUNCS[node.id])  # type: ignore[arg-type]
            if node.id not in self._params:
                raise KeyError(f"Unknown parameter {node.id!r}")
            if node.id in stack:
                raise ValueError(f"Circular parameter reference involving {node.id!r}")
            raw = self._params[node.id].value
            if isinstance(raw, str):
                return self._eval(raw, stack=stack | {node.id})
            return float(raw)
        if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
            return _BINOPS[type(node.op)](
                self._eval_node(node.left, stack),
                self._eval_node(node.right, stack),
            )
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
            return _UNARY[type(node.op)](self._eval_node(node.operand, stack))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            fn = _FUNCS.get(node.func.id)
            if not callable(fn):
                raise ValueError(f"Unknown function {node.func.id!r}")
            args = [self._eval_node(a, stack) for a in node.args]
            return float(fn(*args))
        raise ValueError(f"Unsupported expression node: {ast.dump(node)}")
