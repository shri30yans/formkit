"""Topological queries — handles resolved against a body at rebuild time."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


FaceKind = Literal["z_max", "z_min", "x_max", "x_min", "y_max", "y_min", "largest"]
EdgeKind = Literal["vertical", "horizontal", "all", "top", "bottom"]


@dataclass(frozen=True)
class FaceQuery:
    body: str
    kind: FaceKind

    def to_dict(self) -> dict:
        return {"body": self.body, "kind": self.kind, "type": "face"}


@dataclass(frozen=True)
class EdgeQuery:
    body: str
    kind: EdgeKind

    def to_dict(self) -> dict:
        return {"body": self.body, "kind": self.kind, "type": "edge"}


class FaceQueries:
    def __init__(self, body_name: str) -> None:
        self._body = body_name

    @property
    def z_max(self) -> FaceQuery:
        return FaceQuery(self._body, "z_max")

    @property
    def z_min(self) -> FaceQuery:
        return FaceQuery(self._body, "z_min")

    @property
    def x_max(self) -> FaceQuery:
        return FaceQuery(self._body, "x_max")

    @property
    def x_min(self) -> FaceQuery:
        return FaceQuery(self._body, "x_min")

    @property
    def y_max(self) -> FaceQuery:
        return FaceQuery(self._body, "y_max")

    @property
    def y_min(self) -> FaceQuery:
        return FaceQuery(self._body, "y_min")

    @property
    def largest(self) -> FaceQuery:
        return FaceQuery(self._body, "largest")

    # Fusion-friendly aliases
    @property
    def top(self) -> FaceQuery:
        return self.z_max

    @property
    def bottom(self) -> FaceQuery:
        return self.z_min


class EdgeQueries:
    def __init__(self, body_name: str) -> None:
        self._body = body_name

    @property
    def vertical(self) -> EdgeQuery:
        return EdgeQuery(self._body, "vertical")

    @property
    def horizontal(self) -> EdgeQuery:
        return EdgeQuery(self._body, "horizontal")

    @property
    def all(self) -> EdgeQuery:
        return EdgeQuery(self._body, "all")

    @property
    def top(self) -> EdgeQuery:
        return EdgeQuery(self._body, "top")

    @property
    def bottom(self) -> EdgeQuery:
        return EdgeQuery(self._body, "bottom")
