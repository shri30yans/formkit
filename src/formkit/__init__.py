"""formkit — body-centric parametric CAD with composable shapes."""

from formkit.align import Align
from formkit.body import Body
from formkit.document import Document
from formkit.errors import FeatureError, FormkitError, ValidationError
from formkit.frame import FaceFrame, Frame
from formkit.param import Expr, ParamRef
from formkit.profile import (
    Circle,
    Ellipse,
    HullProfile,
    OffsetProfile,
    Polygon,
    Profile,
    Rect,
    Rectangle,
    RegularPolygon,
    RoundedRect,
    Shape,
    Slot,
    hull,
    profile_cut,
    profile_union,
)
from formkit.query import EdgeQuery, FaceQuery
from formkit.solid import Box, Cone, Cylinder, Solid, Sphere, Wedge

__all__ = [
    "Document",
    "Body",
    "Frame",
    "FaceFrame",
    "Align",
    "ParamRef",
    "Expr",
    "Box",
    "Cylinder",
    "Cone",
    "Sphere",
    "Wedge",
    "Solid",
    "Rect",
    "Rectangle",
    "RoundedRect",
    "Circle",
    "Ellipse",
    "Slot",
    "Polygon",
    "RegularPolygon",
    "Profile",
    "Shape",
    "OffsetProfile",
    "HullProfile",
    "hull",
    "profile_union",
    "profile_cut",
    "FaceQuery",
    "EdgeQuery",
    "FormkitError",
    "FeatureError",
    "ValidationError",
    "__version__",
]

__version__ = "0.5.0"
