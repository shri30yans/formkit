"""Alignment — borrowed mental model from build123d Align (min/center/max per axis)."""

from __future__ import annotations

from enum import Enum
from typing import Literal


class Align(str, Enum):
    """Where the solid sits relative to its Frame origin on each axis."""

    MIN = "min"
    CENTER = "center"
    MAX = "max"


AlignLike = Align | Literal["min", "center", "max"]
Align3 = tuple[AlignLike, AlignLike, AlignLike]


def normalize_align3(
    align: AlignLike | Align3 | None = None,
    *,
    align_x: AlignLike | None = None,
    align_y: AlignLike | None = None,
    align_z: AlignLike | None = None,
) -> tuple[str, str, str]:
    """Resolve to (ax, ay, az) string triple. Default: all center."""
    if align is None and align_x is None and align_y is None and align_z is None:
        return ("center", "center", "center")
    if isinstance(align, (tuple, list)) and len(align) == 3:
        return (_one(align[0]), _one(align[1]), _one(align[2]))
    if align is not None and not isinstance(align, (tuple, list)):
        # single value applies to all axes
        v = _one(align)
        return (v, v, v)
    return (
        _one(align_x or "center"),
        _one(align_y or "center"),
        _one(align_z or "center"),
    )


def _one(v: AlignLike) -> str:
    if isinstance(v, Align):
        return v.value
    return str(v).lower()
