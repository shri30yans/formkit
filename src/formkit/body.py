"""Named body handle — features target this body."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from formkit.features import (
    CHAMFER,
    COUNTERBORE,
    CUT_PROFILE,
    FILLET,
    HOLE,
    HOLES_GRID,
    HOLES_POLAR,
    Feature,
)
from formkit.frame import FaceFrame, Frame, Placement
from formkit.param import Scalar
from formkit.profile import Profile
from formkit.query import EdgeQueries, FaceQueries, FaceQuery, EdgeQuery

if TYPE_CHECKING:
    from formkit.document import Document


class Body:
    """Handle to a named solid in a Document. Methods append features to the timeline."""

    def __init__(self, doc: Document, name: str) -> None:
        self._doc = doc
        self.name = name

    def __repr__(self) -> str:
        return f"Body({self.name!r})"

    @property
    def faces(self) -> FaceQueries:
        return FaceQueries(self.name)

    @property
    def edges(self) -> EdgeQueries:
        return EdgeQueries(self.name)

    def cut(
        self,
        profile: Profile,
        *,
        height: Scalar | None = None,
        through: bool = False,
        on: Placement | None = None,
    ) -> Body:
        """Remove material using a profile on a workplane or body face."""
        if height is None and not through:
            through = True
        placement = on or Frame.xy
        self._doc._add_feature(
            Feature(
                CUT_PROFILE,
                {
                    "body": self.name,
                    "profile": profile.to_dict(),
                    "height": height,
                    "through": through,
                    "frame": placement.to_dict(),
                },
            )
        )
        return self

    def hole(
        self,
        *,
        diameter: Scalar,
        on: FaceQuery | None = None,
        at: tuple[Scalar, Scalar] = (0, 0),
        depth: Scalar | None = None,
    ) -> Body:
        face = on or self.faces.z_max
        self._doc._add_feature(
            Feature(
                HOLE,
                {
                    "body": self.name,
                    "diameter": diameter,
                    "depth": depth,
                    "face": face.to_dict(),
                    "at": at,
                },
            )
        )
        return self

    def counterbore(
        self,
        *,
        diameter: Scalar,
        depth: Scalar,
        counter_diameter: Scalar,
        counter_depth: Scalar,
        on: FaceQuery | None = None,
        at: tuple[Scalar, Scalar] = (0, 0),
    ) -> Body:
        face = on or self.faces.z_max
        self._doc._add_feature(
            Feature(
                COUNTERBORE,
                {
                    "body": self.name,
                    "diameter": diameter,
                    "depth": depth,
                    "counter_diameter": counter_diameter,
                    "counter_depth": counter_depth,
                    "face": face.to_dict(),
                    "at": at,
                },
            )
        )
        return self

    def fillet(
        self,
        *,
        radius: Scalar,
        edges: EdgeQuery | None = None,
    ) -> Body:
        eq = edges or self.edges.vertical
        self._doc._add_feature(
            Feature(
                FILLET,
                {"body": self.name, "radius": radius, "edges": eq.to_dict()},
            )
        )
        return self

    def chamfer(
        self,
        *,
        length: Scalar,
        edges: EdgeQuery | None = None,
    ) -> Body:
        eq = edges or self.edges.top
        self._doc._add_feature(
            Feature(
                CHAMFER,
                {"body": self.name, "length": length, "edges": eq.to_dict()},
            )
        )
        return self

    def holes_grid(
        self,
        diameter: Scalar,
        *,
        count_x: int,
        count_y: int,
        spacing_x: Scalar,
        spacing_y: Scalar,
        depth: Scalar | None = None,
        on: FaceQuery | None = None,
        center: tuple[Scalar, Scalar] = (0, 0),
    ) -> Body:
        face = on or self.faces.z_max
        self._doc._add_feature(
            Feature(
                HOLES_GRID,
                {
                    "body": self.name,
                    "diameter": diameter,
                    "count_x": count_x,
                    "count_y": count_y,
                    "spacing_x": spacing_x,
                    "spacing_y": spacing_y,
                    "depth": depth,
                    "face": face.to_dict(),
                    "center": center,
                },
            )
        )
        return self

    def holes_polar(
        self,
        diameter: Scalar,
        *,
        count: int,
        radius: Scalar,
        depth: Scalar | None = None,
        on: FaceQuery | None = None,
        center: tuple[Scalar, Scalar] = (0, 0),
        start_angle: Scalar = 0,
    ) -> Body:
        face = on or self.faces.z_max
        self._doc._add_feature(
            Feature(
                HOLES_POLAR,
                {
                    "body": self.name,
                    "diameter": diameter,
                    "count": count,
                    "radius": radius,
                    "depth": depth,
                    "face": face.to_dict(),
                    "center": center,
                    "start_angle": start_angle,
                },
            )
        )
        return self

    def shell(
        self,
        thickness: Scalar,
        *,
        open_face: FaceQuery | None = None,
    ) -> Body:
        """Hollow the body (build123d offset). Default opening: top face."""
        from formkit.features import SHELL

        face = open_face or self.faces.z_max
        self._doc._add_feature(
            Feature(
                SHELL,
                {"body": self.name, "thickness": thickness, "open": face.to_dict()},
            )
        )
        return self

    def pad(
        self,
        profile: Profile,
        *,
        height: Scalar,
        on: FaceQuery | None = None,
        at: tuple[Scalar, Scalar] = (0, 0),
    ) -> Body:
        """Extrude a profile from a face and fuse into this body (boss / rib)."""
        from formkit.features import PAD

        face = on or self.faces.z_max
        self._doc._add_feature(
            Feature(
                PAD,
                {
                    "body": self.name,
                    "profile": profile.to_dict(),
                    "height": height,
                    "face": face.to_dict(),
                    "at": at,
                },
            )
        )
        return self

    def emboss(
        self,
        text: str,
        *,
        font_size: Scalar = 10,
        height: Scalar = 0.8,
        on: FaceQuery | None = None,
        at: tuple[Scalar, Scalar] = (0, 0),
        font: str = "Arial",
    ) -> Body:
        """Raise text from a face."""
        from formkit.features import EMBOSS

        face = on or self.faces.z_max
        self._doc._add_feature(
            Feature(
                EMBOSS,
                {
                    "body": self.name,
                    "text": text,
                    "font_size": font_size,
                    "height": height,
                    "face": face.to_dict(),
                    "at": at,
                    "font": font,
                },
            )
        )
        return self

    def deboss(
        self,
        text: str,
        *,
        font_size: Scalar = 10,
        depth: Scalar = 0.6,
        on: FaceQuery | None = None,
        at: tuple[Scalar, Scalar] = (0, 0),
        font: str = "Arial",
    ) -> Body:
        """Recess text into a face."""
        from formkit.features import DEBOSS

        face = on or self.faces.z_max
        self._doc._add_feature(
            Feature(
                DEBOSS,
                {
                    "body": self.name,
                    "text": text,
                    "font_size": font_size,
                    "depth": depth,
                    "face": face.to_dict(),
                    "at": at,
                    "font": font,
                },
            )
        )
        return self

    def lip(
        self,
        *,
        width: Scalar = 1.0,
        height: Scalar = 1.2,
        mode: str = "male",
        on: FaceQuery | None = None,
    ) -> Body:
        """Add a ridge (male) or groove (female) near the face perimeter."""
        from formkit.features import LIP

        face = on or self.faces.z_max
        self._doc._add_feature(
            Feature(
                LIP,
                {
                    "body": self.name,
                    "width": width,
                    "height": height,
                    "mode": mode,
                    "face": face.to_dict(),
                },
            )
        )
        return self

    def boss(
        self,
        *,
        outer_d: Scalar,
        height: Scalar,
        at: tuple[Scalar, Scalar] = (0, 0),
        on: FaceQuery | None = None,
        hole_d: Scalar | None = None,
    ) -> Body:
        """Cylindrical boss, optional axial hole."""
        from formkit.features import BOSS

        face = on or self.faces.z_max
        self._doc._add_feature(
            Feature(
                BOSS,
                {
                    "body": self.name,
                    "outer_d": outer_d,
                    "height": height,
                    "at": at,
                    "face": face.to_dict(),
                    "hole_d": hole_d,
                },
            )
        )
        return self

    def import_svg(
        self,
        path: str,
        *,
        height: Scalar = 1.0,
        operation: str = "cut",
        on: FaceQuery | None = None,
        at: tuple[Scalar, Scalar] = (0, 0),
        scale: Scalar = 1.0,
    ) -> Body:
        """Import an SVG outline and extrude as cut or join on a face."""
        from formkit.features import IMPORT_SVG

        face = on or self.faces.z_max
        self._doc._add_feature(
            Feature(
                IMPORT_SVG,
                {
                    "body": self.name,
                    "path": path,
                    "height": height,
                    "operation": operation,
                    "face": face.to_dict(),
                    "at": at,
                    "scale": scale,
                },
            )
        )
        return self

    def join_into(self, target: Body) -> Body:
        """Fuse this body into target; this body is consumed."""
        return self._doc.join(target, self)

    def solid(self) -> Any:
        """Opaque backend solid (for advanced use). Prefer metrics/export on Document."""
        self._doc.rebuild()
        return self._doc._solids[self.name]
