"""2D profiles and composable shapes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Sequence

from formkit.param import Scalar


@dataclass(frozen=True)
class Profile:
    """Base 2D closed region on a workplane."""

    kind: str
    data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"kind": self.kind, **self.data}

    def add(self, other: Profile, *, at: tuple[Scalar, Scalar] = (0, 0)) -> Shape:
        return Shape.from_profile(self).add(other, at=at)

    def cut(self, other: Profile, *, at: tuple[Scalar, Scalar] = (0, 0)) -> Shape:
        return Shape.from_profile(self).cut(other, at=at)

    def offset(self, amount: Scalar, *, kind: Literal["arc", "intersection"] = "arc") -> Profile:
        """Grow (amount>0) or shrink (amount<0) the outline. Prefer over minkowski."""
        return OffsetProfile(self, amount, kind=kind)


@dataclass(frozen=True)
class Shape(Profile):
    """Composable 2D region built by adding/cutting primitive profiles.

    Example::

        outline = (
            Rect(40, 30)
            .add(Circle(6), at=(12, 0))
            .cut(Circle(3), at=(-10, 8))
        )
        doc.extrude(outline, height=4)
    """

    ops: tuple[dict, ...] = ()

    def __init__(self, ops: Sequence[dict] | None = None) -> None:
        object.__setattr__(self, "kind", "shape")
        object.__setattr__(self, "ops", tuple(ops or ()))
        object.__setattr__(self, "data", {"ops": list(self.ops)})

    @classmethod
    def from_profile(cls, profile: Profile) -> Shape:
        if isinstance(profile, Shape):
            return profile
        return cls([{"op": "add", "profile": profile.to_dict(), "at": (0, 0)}])

    def add(self, other: Profile, *, at: tuple[Scalar, Scalar] = (0, 0)) -> Shape:
        if isinstance(other, Shape):
            shifted = [
                {
                    "op": op["op"],
                    "profile": op["profile"],
                    "at": (_add_s(op["at"][0], at[0]), _add_s(op["at"][1], at[1])),
                }
                for op in other.ops
            ]
            return Shape([*self.ops, *shifted])
        return Shape([*self.ops, {"op": "add", "profile": other.to_dict(), "at": at}])

    def cut(self, other: Profile, *, at: tuple[Scalar, Scalar] = (0, 0)) -> Shape:
        if isinstance(other, Shape):
            # Cut the positive regions of the other shape
            shifted = [
                {
                    "op": "cut",
                    "profile": op["profile"],
                    "at": (_add_s(op["at"][0], at[0]), _add_s(op["at"][1], at[1])),
                }
                for op in other.ops
                if op.get("op", "add") == "add"
            ]
            return Shape([*self.ops, *shifted])
        return Shape([*self.ops, {"op": "cut", "profile": other.to_dict(), "at": at}])


@dataclass(frozen=True)
class OffsetProfile(Profile):
    """Resolved outline grown or shrunk by ``amount`` mm."""

    def __init__(
        self,
        inner: Profile,
        amount: Scalar,
        *,
        kind: Literal["arc", "intersection"] = "arc",
    ) -> None:
        object.__setattr__(self, "kind", "offset")
        object.__setattr__(
            self,
            "data",
            {"inner": inner.to_dict(), "amount": amount, "offset_kind": kind},
        )


@dataclass(frozen=True)
class HullProfile(Profile):
    """2D convex hull of two or more profiles."""

    def __init__(self, profiles: Sequence[Profile]) -> None:
        if len(profiles) < 2:
            raise ValueError("hull needs ≥ 2 profiles")
        object.__setattr__(self, "kind", "hull")
        object.__setattr__(self, "data", {"profiles": [p.to_dict() for p in profiles]})


def hull(*profiles: Profile) -> HullProfile:
    """2D convex hull — returns a Profile (extrude/cut like any other)."""
    return HullProfile(profiles)


def _add_s(a: Scalar, b: Scalar) -> Scalar:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return float(a) + float(b)
    from formkit.param import Expr, ParamRef, _tok

    if isinstance(a, (ParamRef, Expr)) or isinstance(b, (ParamRef, Expr)) or isinstance(a, str) or isinstance(b, str):
        return Expr(f"{_tok(a)} + {_tok(b)}")
    return float(a) + float(b)  # type: ignore[arg-type]


@dataclass(frozen=True)
class Rect(Profile):
    width: Scalar = 10
    height: Scalar = 10
    cx: Scalar = 0
    cy: Scalar = 0

    def __init__(
        self,
        width: Scalar,
        height: Scalar,
        *,
        center: tuple[Scalar, Scalar] = (0, 0),
    ) -> None:
        object.__setattr__(self, "kind", "rect")
        object.__setattr__(self, "width", width)
        object.__setattr__(self, "height", height)
        object.__setattr__(self, "cx", center[0])
        object.__setattr__(self, "cy", center[1])
        object.__setattr__(
            self,
            "data",
            {"width": width, "height": height, "cx": center[0], "cy": center[1]},
        )

    def fillet(self, radius: Scalar) -> RoundedRect:
        return RoundedRect(self.width, self.height, radius, center=(self.cx, self.cy))


# Friendly alias
Rectangle = Rect


@dataclass(frozen=True)
class RoundedRect(Profile):
    width: Scalar = 10
    height: Scalar = 10
    radius: Scalar = 1
    cx: Scalar = 0
    cy: Scalar = 0

    def __init__(
        self,
        width: Scalar,
        height: Scalar,
        radius: Scalar,
        *,
        center: tuple[Scalar, Scalar] = (0, 0),
    ) -> None:
        object.__setattr__(self, "kind", "rounded_rect")
        object.__setattr__(self, "width", width)
        object.__setattr__(self, "height", height)
        object.__setattr__(self, "radius", radius)
        object.__setattr__(self, "cx", center[0])
        object.__setattr__(self, "cy", center[1])
        object.__setattr__(
            self,
            "data",
            {
                "width": width,
                "height": height,
                "radius": radius,
                "cx": center[0],
                "cy": center[1],
            },
        )


@dataclass(frozen=True)
class Circle(Profile):
    radius: Scalar = 5
    cx: Scalar = 0
    cy: Scalar = 0

    def __init__(
        self,
        radius: Scalar | None = None,
        *,
        diameter: Scalar | None = None,
        center: tuple[Scalar, Scalar] = (0, 0),
    ) -> None:
        if radius is None and diameter is None:
            raise ValueError("Circle requires radius= or diameter=")
        if radius is None:
            from formkit.param import Expr, _tok

            r: Scalar = (
                Expr(f"{_tok(diameter)} / 2")
                if not isinstance(diameter, (int, float))
                else float(diameter) / 2.0
            )
        else:
            r = radius
        object.__setattr__(self, "kind", "circle")
        object.__setattr__(self, "radius", r)
        object.__setattr__(self, "cx", center[0])
        object.__setattr__(self, "cy", center[1])
        object.__setattr__(self, "data", {"radius": r, "cx": center[0], "cy": center[1]})


@dataclass(frozen=True)
class Slot(Profile):
    length: Scalar = 10
    width: Scalar = 4
    cx: Scalar = 0
    cy: Scalar = 0
    rotation: Scalar = 0

    def __init__(
        self,
        length: Scalar,
        width: Scalar,
        *,
        center: tuple[Scalar, Scalar] = (0, 0),
        rotation: Scalar = 0,
    ) -> None:
        object.__setattr__(self, "kind", "slot")
        object.__setattr__(self, "length", length)
        object.__setattr__(self, "width", width)
        object.__setattr__(self, "cx", center[0])
        object.__setattr__(self, "cy", center[1])
        object.__setattr__(self, "rotation", rotation)
        object.__setattr__(
            self,
            "data",
            {
                "length": length,
                "width": width,
                "cx": center[0],
                "cy": center[1],
                "rotation": rotation,
            },
        )


@dataclass(frozen=True)
class Polygon(Profile):
    points: tuple[tuple[Scalar, Scalar], ...] = ()

    def __init__(self, points: list[tuple[Scalar, Scalar]] | tuple[tuple[Scalar, Scalar], ...]) -> None:
        pts = tuple(points)
        if len(pts) < 3:
            raise ValueError("Polygon needs ≥ 3 points")
        object.__setattr__(self, "kind", "polygon")
        object.__setattr__(self, "points", pts)
        object.__setattr__(self, "data", {"points": pts})


@dataclass(frozen=True)
class Ellipse(Profile):
    x_radius: Scalar = 5
    y_radius: Scalar = 3
    cx: Scalar = 0
    cy: Scalar = 0
    rotation: Scalar = 0

    def __init__(
        self,
        x_radius: Scalar,
        y_radius: Scalar,
        *,
        center: tuple[Scalar, Scalar] = (0, 0),
        rotation: Scalar = 0,
    ) -> None:
        object.__setattr__(self, "kind", "ellipse")
        object.__setattr__(self, "x_radius", x_radius)
        object.__setattr__(self, "y_radius", y_radius)
        object.__setattr__(self, "cx", center[0])
        object.__setattr__(self, "cy", center[1])
        object.__setattr__(self, "rotation", rotation)
        object.__setattr__(
            self,
            "data",
            {
                "x_radius": x_radius,
                "y_radius": y_radius,
                "cx": center[0],
                "cy": center[1],
                "rotation": rotation,
            },
        )


@dataclass(frozen=True)
class RegularPolygon(Profile):
    radius: Scalar = 5
    sides: int = 6
    cx: Scalar = 0
    cy: Scalar = 0
    rotation: Scalar = 0

    def __init__(
        self,
        radius: Scalar,
        sides: int = 6,
        *,
        center: tuple[Scalar, Scalar] = (0, 0),
        rotation: Scalar = 0,
    ) -> None:
        if sides < 3:
            raise ValueError("RegularPolygon needs ≥ 3 sides")
        object.__setattr__(self, "kind", "regular_polygon")
        object.__setattr__(self, "radius", radius)
        object.__setattr__(self, "sides", int(sides))
        object.__setattr__(self, "cx", center[0])
        object.__setattr__(self, "cy", center[1])
        object.__setattr__(self, "rotation", rotation)
        object.__setattr__(
            self,
            "data",
            {
                "radius": radius,
                "sides": int(sides),
                "cx": center[0],
                "cy": center[1],
                "rotation": rotation,
            },
        )


def profile_union(a: Profile, b: Profile) -> Shape:
    return Shape.from_profile(a).add(b)


def profile_cut(a: Profile, b: Profile) -> Shape:
    return Shape.from_profile(a).cut(b)
