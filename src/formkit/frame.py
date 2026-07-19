"""Rigid frames / workplanes — explicit placement in 3D."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Union

if TYPE_CHECKING:
    from formkit.param import Scalar
    from formkit.query import FaceQuery


@dataclass(frozen=True)
class Frame:
    """Rigid placement: origin (mm) + roll/pitch/yaw in degrees.

    Use as ``at=`` for solids and ``on=`` for profile extrudes/cuts.
    """

    x: Scalar = 0.0
    y: Scalar = 0.0
    z: Scalar = 0.0
    rx: Scalar = 0.0
    ry: Scalar = 0.0
    rz: Scalar = 0.0

    @classmethod
    def translate(cls, x: Scalar = 0, y: Scalar = 0, z: Scalar = 0) -> Frame:
        return cls(x=x, y=y, z=z)

    @classmethod
    def rotate(cls, *, rx: Scalar = 0, ry: Scalar = 0, rz: Scalar = 0) -> Frame:
        return cls(rx=rx, ry=ry, rz=rz)

    @classmethod
    def from_axes(
        cls,
        *,
        origin: tuple[Scalar, Scalar, Scalar] = (0, 0, 0),
        rx: Scalar = 0,
        ry: Scalar = 0,
        rz: Scalar = 0,
    ) -> Frame:
        return cls(x=origin[0], y=origin[1], z=origin[2], rx=rx, ry=ry, rz=rz)

    @classmethod
    def offset_z(cls, z: Scalar) -> Frame:
        return cls.translate(0, 0, z)

    @classmethod
    def on_face(cls, face: FaceQuery, *, offset: Scalar = 0) -> FaceFrame:
        """Workplane glued to a body face (resolved at rebuild)."""
        return FaceFrame(body=face.body, kind=face.kind, offset=offset)

    def moved(self, x: Scalar = 0, y: Scalar = 0, z: Scalar = 0) -> Frame:
        return Frame(
            x=_add(self.x, x),
            y=_add(self.y, y),
            z=_add(self.z, z),
            rx=self.rx,
            ry=self.ry,
            rz=self.rz,
        )

    def offset(self, *, x: Scalar = 0, y: Scalar = 0, z: Scalar = 0) -> Frame:
        return self.moved(x, y, z)

    def rotated(self, *, rx: Scalar = 0, ry: Scalar = 0, rz: Scalar = 0) -> Frame:
        return Frame(
            x=self.x,
            y=self.y,
            z=self.z,
            rx=_add(self.rx, rx),
            ry=_add(self.ry, ry),
            rz=_add(self.rz, rz),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "frame",
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "rx": self.rx,
            "ry": self.ry,
            "rz": self.rz,
        }


@dataclass(frozen=True)
class FaceFrame:
    """Deferred workplane on a named body's face (Onshape-style query)."""

    body: str
    kind: str
    offset: Scalar = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "face",
            "body": self.body,
            "kind": self.kind,
            "offset": self.offset,
        }


Placement = Union[Frame, FaceFrame]


def _add(a: Scalar, b: Scalar) -> Scalar:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return float(a) + float(b)
    from formkit.param import Expr, ParamRef, _tok

    if isinstance(a, (ParamRef, Expr)) or isinstance(b, (ParamRef, Expr)) or isinstance(a, str) or isinstance(b, str):
        return Expr(f"{_tok(a)} + {_tok(b)}")
    return float(a) + float(b)  # type: ignore[arg-type]


Frame.origin = Frame()  # type: ignore[attr-defined]
Frame.xy = Frame()  # type: ignore[attr-defined]
Frame.xz = Frame(rx=90)  # type: ignore[attr-defined]
Frame.yz = Frame(ry=90)  # type: ignore[attr-defined]
