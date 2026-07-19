"""Feature records — typed ops on the document timeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class Feature:
    kind: str
    data: dict[str, Any] = field(default_factory=dict)
    name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "name": self.name, "data": self.data}


# Feature kind constants
ADD_SOLID = "add_solid"
EXTRUDE = "extrude"
CUT_PROFILE = "cut_profile"
REVOLVE = "revolve"
JOIN = "join"
CUT_BODY = "cut_body"
INTERSECT = "intersect"
HOLE = "hole"
COUNTERBORE = "counterbore"
FILLET = "fillet"
CHAMFER = "chamfer"
HOLES_GRID = "holes_grid"
HOLES_POLAR = "holes_polar"
MIRROR = "mirror"
PATTERN_BODY_GRID = "pattern_body_grid"
PATTERN_BODY_POLAR = "pattern_body_polar"
SHELL = "shell"
PAD = "pad"
EMBOSS = "emboss"
LOFT = "loft"
LIP = "lip"
BOSS = "boss"
IMPORT_SVG = "import_svg"
DEBOSS = "deboss"
HULL = "hull"

PlaneName = Literal["XY", "XZ", "YZ"]
