"""Document — params, bodies, feature timeline, rebuild, export."""

from __future__ import annotations

from typing import Any

from formkit.backend.occt import OcctBackend
from formkit.body import Body
from formkit.errors import FeatureError
from formkit.features import (
    ADD_SOLID,
    BOSS,
    CUT_BODY,
    CUT_PROFILE,
    DEBOSS,
    EMBOSS,
    EXTRUDE,
    HULL,
    IMPORT_SVG,
    INTERSECT,
    JOIN,
    LIP,
    LOFT,
    MIRROR,
    PAD,
    PATTERN_BODY_GRID,
    PATTERN_BODY_POLAR,
    REVOLVE,
    SHELL,
    Feature,
    PlaneName,
)
from formkit.frame import Frame
from formkit.param import ParamRef, ParamStore, Scalar
from formkit.profile import Profile
from formkit.solid import Solid


class Document:
    """Part document: parameters + named bodies + rebuildable feature history."""

    def __init__(self, name: str = "Part") -> None:
        self.name = name
        self.params = ParamStore()
        self._features: list[Feature] = []
        self._bodies: dict[str, Body] = {}
        self._solids: dict[str, Any] = {}
        self._dirty = True
        self._backend = OcctBackend()
        self._auto_id = 0

    # --- params -----------------------------------------------------
    def param(
        self,
        name: str,
        value: float | str,
        *,
        unit: str = "mm",
        comment: str = "",
    ) -> ParamRef:
        self._dirty = True
        return self.params.set(name, value, unit=unit, comment=comment)

    def set_params(self, **kwargs: float | str) -> Document:
        self.params.update(**kwargs)
        self._dirty = True
        return self

    def __getitem__(self, name: str) -> float:
        return self.params[name]

    def resolve(self, value: Scalar) -> float:
        return self.params.resolve(value)

    # --- body creation ----------------------------------------------
    def _unique_name(self, base: str) -> str:
        if base not in self._bodies:
            return base
        self._auto_id += 1
        return f"{base}_{self._auto_id}"

    def _register(self, name: str) -> Body:
        body = Body(self, name)
        self._bodies[name] = body
        return body

    def _add_feature(self, feat: Feature) -> None:
        self._features.append(feat)
        self._dirty = True

    def add(
        self,
        solid: Solid,
        *,
        at: Frame | None = None,
        name: str | None = None,
    ) -> Body:
        """Place a primitive solid as a new named body."""
        bname = self._unique_name(name or solid.kind)
        self._register(bname)
        self._add_feature(
            Feature(
                ADD_SOLID,
                {
                    "body": bname,
                    "solid": solid.to_dict(),
                    "frame": (at or Frame.origin).to_dict(),
                },
                name=bname,
            )
        )
        return self._bodies[bname]

    def extrude(
        self,
        profile: Profile,
        *,
        height: Scalar,
        at: Frame | None = None,
        twist: Scalar = 0,
        scale: Scalar | tuple[Scalar, Scalar] = 1.0,
        taper: Scalar = 0,
        name: str | None = None,
    ) -> Body:
        """Extrude a profile into a new body.

        ``twist`` — total rotation in degrees over ``height`` (OpenSCAD-style).
        ``scale`` — end scale factor (float or ``(sx, sy)``).
        ``taper`` — draft angle in degrees (simple extrude only; ignored with twist/scale).
        """
        bname = self._unique_name(name or "extrude")
        self._register(bname)
        self._add_feature(
            Feature(
                EXTRUDE,
                {
                    "body": bname,
                    "profile": profile.to_dict(),
                    "height": height,
                    "frame": (at or Frame.xy).to_dict(),
                    "twist": twist,
                    "scale": scale,
                    "taper": taper,
                },
                name=bname,
            )
        )
        return self._bodies[bname]

    def hull(
        self,
        *items: Body | Solid | tuple[Solid, Frame],
        name: str | None = None,
        consume: bool = True,
    ) -> Body:
        """3D convex hull of bodies and/or placed solids → new body.

        Examples::

            doc.hull((Cylinder(height=4, diameter=12), Frame.origin),
                     (Cylinder(height=4, diameter=12), Frame.translate(40, 0, 0)))
            doc.hull(body_a, body_b, consume=True)
        """
        if len(items) < 2:
            raise ValueError("hull needs ≥ 2 parts")
        parts: list[dict[str, Any]] = []
        for item in items:
            if isinstance(item, Body):
                parts.append({"type": "body", "name": item.name})
            elif isinstance(item, Solid):
                parts.append(
                    {
                        "type": "solid",
                        "solid": item.to_dict(),
                        "frame": Frame.origin.to_dict(),
                    }
                )
            elif isinstance(item, tuple) and len(item) == 2:
                solid, frame = item
                if not isinstance(solid, Solid):
                    raise TypeError("hull tuple must be (Solid, Frame)")
                fr = frame if isinstance(frame, Frame) else Frame.origin
                parts.append(
                    {
                        "type": "solid",
                        "solid": solid.to_dict(),
                        "frame": fr.to_dict(),
                    }
                )
            else:
                raise TypeError(
                    "hull items must be Body, Solid, or (Solid, Frame) — "
                    f"got {type(item)!r}"
                )

        bname = self._unique_name(name or "hull")
        self._register(bname)
        self._add_feature(
            Feature(
                HULL,
                {"body": bname, "parts": parts, "consume": consume},
                name=bname,
            )
        )
        return self._bodies[bname]

    def revolve(
        self,
        profile: Profile,
        *,
        angle: Scalar = 360,
        at: Frame | None = None,
        name: str | None = None,
    ) -> Body:
        bname = self._unique_name(name or "revolve")
        self._register(bname)
        self._add_feature(
            Feature(
                REVOLVE,
                {
                    "body": bname,
                    "profile": profile.to_dict(),
                    "angle": angle,
                    "frame": (at or Frame.xz).to_dict(),
                },
                name=bname,
            )
        )
        return self._bodies[bname]

    def body(self, name: str) -> Body:
        if name not in self._bodies:
            raise KeyError(f"Unknown body {name!r}")
        return self._bodies[name]

    def bodies(self) -> list[str]:
        return list(self._bodies.keys())

    # --- boolean between bodies -------------------------------------
    def join(self, target: Body | str, source: Body | str, *, consume: bool = True) -> Body:
        t = target.name if isinstance(target, Body) else target
        s = source.name if isinstance(source, Body) else source
        self._add_feature(Feature(JOIN, {"target": t, "source": s, "consume": consume}))
        return self._bodies[t]

    def loft(
        self,
        profiles: list[Profile],
        *,
        frames: list[Frame] | None = None,
        name: str | None = None,
    ) -> Body:
        """Loft through a sequence of profiles on successive frames."""
        if len(profiles) < 2:
            raise ValueError("loft needs ≥ 2 profiles")
        if frames is None:
            # stack along Z with unit spacing — caller should pass frames for real designs
            frames = [Frame.offset_z(i * 10) for i in range(len(profiles))]
        if len(frames) != len(profiles):
            raise ValueError("frames length must match profiles")
        bname = self._unique_name(name or "loft")
        self._register(bname)
        self._add_feature(
            Feature(
                LOFT,
                {
                    "body": bname,
                    "profiles": [p.to_dict() for p in profiles],
                    "frames": [f.to_dict() for f in frames],
                },
                name=bname,
            )
        )
        return self._bodies[bname]

    def cut_body(self, target: Body | str, tool: Body | str) -> Body:
        t = target.name if isinstance(target, Body) else target
        s = tool.name if isinstance(tool, Body) else tool
        self._add_feature(Feature(CUT_BODY, {"target": t, "tool": s}))
        return self._bodies[t]

    def intersect(self, target: Body | str, tool: Body | str) -> Body:
        t = target.name if isinstance(target, Body) else target
        s = tool.name if isinstance(tool, Body) else tool
        self._add_feature(Feature(INTERSECT, {"target": t, "tool": s}))
        return self._bodies[t]

    def mirror(self, body: Body | str, *, plane: PlaneName = "YZ", name: str | None = None) -> Body:
        src = body.name if isinstance(body, Body) else body
        bname = self._unique_name(name or f"{src}_mirror")
        self._register(bname)
        self._add_feature(
            Feature(MIRROR, {"body": bname, "source": src, "plane": plane}, name=bname)
        )
        return self._bodies[bname]

    def pattern_grid(
        self,
        body: Body | str,
        *,
        count_x: int,
        count_y: int,
        spacing_x: Scalar,
        spacing_y: Scalar,
        name: str | None = None,
    ) -> Body:
        src = body.name if isinstance(body, Body) else body
        bname = self._unique_name(name or f"{src}_grid")
        self._register(bname)
        self._add_feature(
            Feature(
                PATTERN_BODY_GRID,
                {
                    "body": bname,
                    "source": src,
                    "count_x": count_x,
                    "count_y": count_y,
                    "spacing_x": spacing_x,
                    "spacing_y": spacing_y,
                },
                name=bname,
            )
        )
        return self._bodies[bname]

    def pattern_polar(
        self,
        body: Body | str,
        *,
        count: int,
        radius: Scalar,
        start_angle: Scalar = 0,
        name: str | None = None,
    ) -> Body:
        src = body.name if isinstance(body, Body) else body
        bname = self._unique_name(name or f"{src}_polar")
        self._register(bname)
        self._add_feature(
            Feature(
                PATTERN_BODY_POLAR,
                {
                    "body": bname,
                    "source": src,
                    "count": count,
                    "radius": radius,
                    "start_angle": start_angle,
                },
                name=bname,
            )
        )
        return self._bodies[bname]

    # --- timeline / rebuild -----------------------------------------
    def timeline(self) -> list[dict[str, Any]]:
        return [f.to_dict() for f in self._features]

    def rebuild(self) -> Document:
        if not self._dirty and self._solids:
            return self
        be = self._backend
        r = self.resolve
        solids: dict[str, Any] = {}

        for i, feat in enumerate(self._features):
            k, d = feat.kind, feat.data
            try:
                if k == ADD_SOLID:
                    solids[d["body"]] = be.make_solid(d["solid"], d["frame"], r)
                elif k == EXTRUDE:
                    scale = d.get("scale", 1.0)
                    if isinstance(scale, (list, tuple)):
                        scale_v: float | tuple[float, float] = (
                            r(scale[0]),
                            r(scale[1]),
                        )
                    else:
                        scale_v = r(scale)
                    solids[d["body"]] = be.extrude_profile(
                        d["profile"],
                        r(d["height"]),
                        d["frame"],
                        r,
                        solids,
                        twist=r(d.get("twist", 0)),
                        scale=scale_v,
                        taper=r(d.get("taper", 0)),
                    )
                elif k == HULL:
                    parts_solids = []
                    for p in d["parts"]:
                        if p["type"] == "body":
                            parts_solids.append(solids[p["name"]])
                        else:
                            parts_solids.append(be.make_solid(p["solid"], p["frame"], r))
                    solids[d["body"]] = be.hull_solids(parts_solids)
                    if d.get("consume", True):
                        for p in d["parts"]:
                            if p["type"] == "body" and p["name"] != d["body"]:
                                solids.pop(p["name"], None)
                elif k == REVOLVE:
                    solids[d["body"]] = be.revolve_profile(
                        d["profile"], r(d["angle"]), d["frame"], r, solids
                    )
                elif k == CUT_PROFILE:
                    body = d["body"]
                    solids[body] = be.cut_profile(
                        solids[body],
                        d["profile"],
                        height=None
                        if d["through"]
                        else (r(d["height"]) if d["height"] is not None else None),
                        through=bool(d["through"]),
                        frame=d["frame"],
                        resolve=r,
                        solids=solids,
                    )
                elif k == JOIN:
                    solids[d["target"]] = be.boolean_fuse(
                        solids[d["target"]], solids[d["source"]]
                    )
                elif k == CUT_BODY:
                    solids[d["target"]] = be.boolean_cut(
                        solids[d["target"]], solids[d["tool"]]
                    )
                elif k == INTERSECT:
                    solids[d["target"]] = be.boolean_intersect(
                        solids[d["target"]], solids[d["tool"]]
                    )
                elif k == "hole":
                    at = (r(d["at"][0]), r(d["at"][1]))
                    solids[d["body"]] = be.hole(
                        solids[d["body"]],
                        diameter=r(d["diameter"]),
                        depth=None if d["depth"] is None else r(d["depth"]),
                        face_kind=d["face"]["kind"],
                        at=at,
                    )
                elif k == "counterbore":
                    at = (r(d["at"][0]), r(d["at"][1]))
                    solids[d["body"]] = be.counterbore(
                        solids[d["body"]],
                        diameter=r(d["diameter"]),
                        depth=r(d["depth"]),
                        counter_diameter=r(d["counter_diameter"]),
                        counter_depth=r(d["counter_depth"]),
                        face_kind=d["face"]["kind"],
                        at=at,
                    )
                elif k == "fillet":
                    solids[d["body"]] = be.fillet(
                        solids[d["body"]], r(d["radius"]), d["edges"]["kind"]
                    )
                elif k == "chamfer":
                    solids[d["body"]] = be.chamfer(
                        solids[d["body"]], r(d["length"]), d["edges"]["kind"]
                    )
                elif k == "holes_grid":
                    c = (r(d["center"][0]), r(d["center"][1]))
                    solids[d["body"]] = be.holes_grid(
                        solids[d["body"]],
                        diameter=r(d["diameter"]),
                        count_x=int(d["count_x"]),
                        count_y=int(d["count_y"]),
                        spacing_x=r(d["spacing_x"]),
                        spacing_y=r(d["spacing_y"]),
                        depth=None if d["depth"] is None else r(d["depth"]),
                        face_kind=d["face"]["kind"],
                        center=c,
                    )
                elif k == "holes_polar":
                    c = (r(d["center"][0]), r(d["center"][1]))
                    solids[d["body"]] = be.holes_polar(
                        solids[d["body"]],
                        diameter=r(d["diameter"]),
                        count=int(d["count"]),
                        radius=r(d["radius"]),
                        depth=None if d["depth"] is None else r(d["depth"]),
                        face_kind=d["face"]["kind"],
                        center=c,
                        start_angle=r(d["start_angle"]),
                    )
                elif k == SHELL:
                    solids[d["body"]] = be.shell(
                        solids[d["body"]], r(d["thickness"]), d["open"]["kind"]
                    )
                elif k == PAD:
                    at = (r(d["at"][0]), r(d["at"][1]))
                    solids[d["body"]] = be.pad(
                        solids[d["body"]],
                        d["profile"],
                        height=r(d["height"]),
                        face_kind=d["face"]["kind"],
                        at=at,
                        resolve=r,
                    )
                elif k == EMBOSS:
                    at = (r(d["at"][0]), r(d["at"][1]))
                    solids[d["body"]] = be.emboss(
                        solids[d["body"]],
                        text=str(d["text"]),
                        font_size=r(d["font_size"]),
                        height=r(d["height"]),
                        face_kind=d["face"]["kind"],
                        at=at,
                        font=str(d.get("font", "Arial")),
                    )
                elif k == DEBOSS:
                    at = (r(d["at"][0]), r(d["at"][1]))
                    solids[d["body"]] = be.deboss(
                        solids[d["body"]],
                        text=str(d["text"]),
                        font_size=r(d["font_size"]),
                        depth=r(d["depth"]),
                        face_kind=d["face"]["kind"],
                        at=at,
                        font=str(d.get("font", "Arial")),
                    )
                elif k == LIP:
                    solids[d["body"]] = be.lip(
                        solids[d["body"]],
                        width=r(d["width"]),
                        height=r(d["height"]),
                        mode=str(d["mode"]),
                        face_kind=d["face"]["kind"],
                    )
                elif k == BOSS:
                    at = (r(d["at"][0]), r(d["at"][1]))
                    hole_d = None if d["hole_d"] is None else r(d["hole_d"])
                    solids[d["body"]] = be.boss(
                        solids[d["body"]],
                        outer_d=r(d["outer_d"]),
                        height=r(d["height"]),
                        face_kind=d["face"]["kind"],
                        at=at,
                        hole_d=hole_d,
                        resolve=r,
                    )
                elif k == IMPORT_SVG:
                    at = (r(d["at"][0]), r(d["at"][1]))
                    solids[d["body"]] = be.import_svg(
                        solids[d["body"]],
                        d["path"],
                        height=r(d["height"]),
                        operation=str(d["operation"]),
                        face_kind=d["face"]["kind"],
                        at=at,
                        scale=r(d["scale"]),
                    )
                elif k == LOFT:
                    solids[d["body"]] = be.loft_profiles(
                        d["profiles"], d["frames"], r, solids
                    )
                elif k == MIRROR:
                    solids[d["body"]] = be.mirror(solids[d["source"]], d["plane"])
                elif k == PATTERN_BODY_GRID:
                    solids[d["body"]] = be.pattern_grid(
                        solids[d["source"]],
                        count_x=int(d["count_x"]),
                        count_y=int(d["count_y"]),
                        spacing_x=r(d["spacing_x"]),
                        spacing_y=r(d["spacing_y"]),
                    )
                elif k == PATTERN_BODY_POLAR:
                    solids[d["body"]] = be.pattern_polar(
                        solids[d["source"]],
                        count=int(d["count"]),
                        radius=r(d["radius"]),
                        start_angle=r(d["start_angle"]),
                    )
                else:
                    raise ValueError(f"Unknown feature kind {k!r}")
            except FeatureError:
                raise
            except Exception as exc:
                raise FeatureError(i, k, str(exc)) from exc

        self._solids = solids
        self._dirty = False
        return self

    def primary(self) -> Any:
        self.rebuild()
        if not self._solids:
            raise RuntimeError("Document has no solids")
        if "base" in self._solids:
            return self._solids["base"]
        return next(iter(self._solids.values()))

    def metrics(self, body: Body | str | None = None) -> dict[str, Any]:
        self.rebuild()
        if body is None:
            solid = self.primary()
            name = "base" if "base" in self._solids else next(iter(self._solids))
        else:
            name = body.name if isinstance(body, Body) else body
            solid = self._solids[name]
        m = self._backend.metrics(solid)
        m["body"] = name
        m["timeline"] = self.timeline()
        m["params"] = self.params.as_dict()
        return m

    def inspect(self, body: Body | str | None = None) -> dict[str, Any]:
        """Snapshot for tooling: metrics + feature timeline."""
        m = self.metrics(body)
        return {
            "name": self.name,
            "bodies": list(self._bodies.keys()),
            "feature_count": len(self._features),
            "params": m["params"],
            "bbox_mm": m["bbox_mm"],
            "volume_mm3": m["volume_mm3"],
            "timeline": m["timeline"],
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize feature graph (params as resolved + raw defs)."""
        return {
            "name": self.name,
            "params": {
                n: {
                    "value": self.params._params[n].value,
                    "unit": self.params._params[n].unit,
                }
                for n in self.params.names()
            },
            "features": self.timeline(),
            "bodies": list(self._bodies.keys()),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Document:
        """Restore a Document from ``to_dict()`` (params + feature timeline)."""
        doc = cls(data.get("name", "Part"))
        for name, meta in (data.get("params") or {}).items():
            if isinstance(meta, dict):
                doc.param(name, meta["value"], unit=meta.get("unit", "mm"))
            else:
                doc.param(name, meta)
        for feat in data.get("features") or []:
            f = Feature(feat["kind"], dict(feat.get("data") or {}), name=feat.get("name"))
            body = f.data.get("body")
            if body and body not in doc._bodies and f.kind in (
                ADD_SOLID,
                EXTRUDE,
                REVOLVE,
                LOFT,
                MIRROR,
                PATTERN_BODY_GRID,
                PATTERN_BODY_POLAR,
                HULL,
            ):
                doc._register(str(body))
            # mirror/pattern also create new bodies under "body" key — covered above
            if f.kind == JOIN:
                pass
            doc._features.append(f)
        # Ensure all named bodies from export exist
        for bname in data.get("bodies") or []:
            if bname not in doc._bodies:
                doc._register(bname)
        doc._dirty = True
        return doc

    def export(self, path: str, body: Body | str | None = None) -> None:
        self.rebuild()
        if body is None:
            solid = self.primary()
        else:
            name = body.name if isinstance(body, Body) else body
            solid = self._solids[name]
        self._backend.export(solid, path)
