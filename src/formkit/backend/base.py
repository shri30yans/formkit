"""Backend protocol — no OCCT types escape this boundary."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Backend(Protocol):
    """Private geometry engine. Implementations must not leak engine types to callers
    of Document — only through opaque handles stored inside Document._solids.
    """

    def make_solid(self, solid_spec: dict, frame: dict, resolve) -> Any: ...

    def extrude_profile(
        self, profile_spec: dict, height: float, frame: dict, resolve
    ) -> Any: ...

    def revolve_profile(
        self, profile_spec: dict, angle_deg: float, frame: dict, resolve
    ) -> Any: ...

    def cut_profile(
        self,
        target: Any,
        profile_spec: dict,
        *,
        height: float | None,
        through: bool,
        frame: dict,
        resolve,
    ) -> Any: ...

    def boolean_fuse(self, a: Any, b: Any) -> Any: ...

    def boolean_cut(self, a: Any, b: Any) -> Any: ...

    def boolean_intersect(self, a: Any, b: Any) -> Any: ...

    def hole(
        self,
        target: Any,
        *,
        diameter: float,
        depth: float | None,
        face_kind: str,
        at: tuple[float, float],
    ) -> Any: ...

    def counterbore(
        self,
        target: Any,
        *,
        diameter: float,
        depth: float,
        counter_diameter: float,
        counter_depth: float,
        face_kind: str,
        at: tuple[float, float],
    ) -> Any: ...

    def fillet(self, target: Any, radius: float, edge_kind: str) -> Any: ...

    def chamfer(self, target: Any, length: float, edge_kind: str) -> Any: ...

    def holes_grid(
        self,
        target: Any,
        *,
        diameter: float,
        count_x: int,
        count_y: int,
        spacing_x: float,
        spacing_y: float,
        depth: float | None,
        face_kind: str,
        center: tuple[float, float],
    ) -> Any: ...

    def holes_polar(
        self,
        target: Any,
        *,
        diameter: float,
        count: int,
        radius: float,
        depth: float | None,
        face_kind: str,
        center: tuple[float, float],
        start_angle: float,
    ) -> Any: ...

    def mirror(self, target: Any, plane: str) -> Any: ...

    def pattern_grid(
        self,
        seed: Any,
        *,
        count_x: int,
        count_y: int,
        spacing_x: float,
        spacing_y: float,
    ) -> Any: ...

    def pattern_polar(
        self,
        seed: Any,
        *,
        count: int,
        radius: float,
        start_angle: float,
    ) -> Any: ...

    def metrics(self, solid: Any) -> dict[str, Any]: ...

    def export(self, solid: Any, path: str) -> None: ...
