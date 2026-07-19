"""Immutable 3D primitive solids (values placed via Frame)."""

from __future__ import annotations

from dataclasses import dataclass, field

from formkit.align import Align3, AlignLike, normalize_align3
from formkit.param import Scalar


@dataclass(frozen=True)
class Solid:
    kind: str
    data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"kind": self.kind, **self.data}


@dataclass(frozen=True)
class Box(Solid):
    width: Scalar = 10
    depth: Scalar = 10
    height: Scalar = 10

    def __init__(
        self,
        width: Scalar,
        depth: Scalar,
        height: Scalar,
        *,
        align: AlignLike | Align3 | None = None,
        align_x: AlignLike | None = None,
        align_y: AlignLike | None = None,
        align_z: AlignLike | None = None,
    ) -> None:
        """Box size X=width, Y=depth, Z=height.

        Use ``align_z="min"`` so the box sits on the XY plane of its Frame
        (build123d-style Align.MIN) — essential for stacking parts.
        """
        ax, ay, az = normalize_align3(align, align_x=align_x, align_y=align_y, align_z=align_z)
        object.__setattr__(self, "kind", "box")
        object.__setattr__(self, "width", width)
        object.__setattr__(self, "depth", depth)
        object.__setattr__(self, "height", height)
        object.__setattr__(
            self,
            "data",
            {
                "width": width,
                "depth": depth,
                "height": height,
                "align": (ax, ay, az),
            },
        )


@dataclass(frozen=True)
class Cylinder(Solid):
    radius: Scalar = 5
    height: Scalar = 10

    def __init__(
        self,
        height: Scalar,
        *,
        radius: Scalar | None = None,
        diameter: Scalar | None = None,
        align_z: AlignLike = "center",
    ) -> None:
        if radius is None and diameter is None:
            raise ValueError("Cylinder requires radius= or diameter=")
        if radius is None:
            from formkit.param import Expr, _tok

            r: Scalar = (
                Expr(f"{_tok(diameter)} / 2")
                if not isinstance(diameter, (int, float))
                else float(diameter) / 2.0
            )
        else:
            r = radius
        az = normalize_align3(align_z=align_z)[2]
        object.__setattr__(self, "kind", "cylinder")
        object.__setattr__(self, "radius", r)
        object.__setattr__(self, "height", height)
        object.__setattr__(self, "data", {"radius": r, "height": height, "align": ("center", "center", az)})


@dataclass(frozen=True)
class Cone(Solid):
    bottom_radius: Scalar = 5
    top_radius: Scalar = 0
    height: Scalar = 10

    def __init__(
        self,
        height: Scalar,
        *,
        bottom_radius: Scalar,
        top_radius: Scalar = 0,
        align_z: AlignLike = "center",
    ) -> None:
        az = normalize_align3(align_z=align_z)[2]
        object.__setattr__(self, "kind", "cone")
        object.__setattr__(self, "bottom_radius", bottom_radius)
        object.__setattr__(self, "top_radius", top_radius)
        object.__setattr__(self, "height", height)
        object.__setattr__(
            self,
            "data",
            {
                "bottom_radius": bottom_radius,
                "top_radius": top_radius,
                "height": height,
                "align": ("center", "center", az),
            },
        )


@dataclass(frozen=True)
class Sphere(Solid):
    radius: Scalar = 5

    def __init__(self, radius: Scalar) -> None:
        object.__setattr__(self, "kind", "sphere")
        object.__setattr__(self, "radius", radius)
        object.__setattr__(self, "data", {"radius": radius, "align": ("center", "center", "center")})


@dataclass(frozen=True)
class Wedge(Solid):
    width: Scalar = 10
    depth: Scalar = 10
    height: Scalar = 10

    def __init__(
        self,
        width: Scalar,
        depth: Scalar,
        height: Scalar,
        *,
        align_z: AlignLike = "min",
    ) -> None:
        az = normalize_align3(align_z=align_z)[2]
        object.__setattr__(self, "kind", "wedge")
        object.__setattr__(self, "width", width)
        object.__setattr__(self, "depth", depth)
        object.__setattr__(self, "height", height)
        object.__setattr__(
            self,
            "data",
            {"width": width, "depth": depth, "height": height, "align": ("center", "center", az)},
        )
