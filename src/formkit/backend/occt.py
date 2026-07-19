"""Private OCCT adapter via build123d — never import this from public formkit API users."""

from __future__ import annotations

import math
from typing import Any, Callable

from build123d import (
    Align as BDAlign,
    Axis,
    Box as BDBox,
    BuildPart,
    BuildSketch,
    Circle as BDCircle,
    Cone as BDCone,
    Cylinder as BDCylinder,
    Ellipse as BDEllipse,
    Face,
    GridLocations,
    Kind,
    Location,
    Locations,
    Mode,
    Plane,
    PolarLocations,
    Polygon as BDPolygon,
    Rectangle,
    RegularPolygon as BDRegularPolygon,
    Rot,
    Shell,
    Solid as BDSolid,
    Sphere as BDSphere,
    SlotOverall,
    Text,
    Vector,
    Wire,
    add,
    chamfer as bd_chamfer,
    export_step,
    export_stl,
    extrude,
    fillet as bd_fillet,
    loft as bd_loft,
    make_hull,
    mirror as bd_mirror,
    offset as bd_offset,
    revolve,
    scale as bd_scale,
)



Resolve = Callable[[Any], float]

_ALIGN = {
    "min": BDAlign.MIN,
    "center": BDAlign.CENTER,
    "max": BDAlign.MAX,
}


def _align3(spec: dict) -> tuple:
    ax, ay, az = spec.get("align", ("center", "center", "center"))
    return (_ALIGN[str(ax)], _ALIGN[str(ay)], _ALIGN[str(az)])


def _loc(frame: dict, resolve: Resolve) -> Location:
    x, y, z = resolve(frame["x"]), resolve(frame["y"]), resolve(frame["z"])
    rx, ry, rz = resolve(frame["rx"]), resolve(frame["ry"]), resolve(frame["rz"])
    return Location((x, y, z)) * Rot(X=rx, Y=ry, Z=rz)


def _plane_from_frame(frame: dict, resolve: Resolve) -> Plane:
    return Plane(_loc(frame, resolve))


class OcctBackend:
    """build123d-backed geometry. All public methods return opaque Solid/Compound."""

    def _face(self, solid: Any, face_kind: str):
        faces = solid.faces()
        if face_kind in ("z_max", "top"):
            return faces.sort_by(Axis.Z)[-1]
        if face_kind in ("z_min", "bottom"):
            return faces.sort_by(Axis.Z)[0]
        if face_kind == "x_max":
            return faces.sort_by(Axis.X)[-1]
        if face_kind == "x_min":
            return faces.sort_by(Axis.X)[0]
        if face_kind == "y_max":
            return faces.sort_by(Axis.Y)[-1]
        if face_kind == "y_min":
            return faces.sort_by(Axis.Y)[0]
        if face_kind == "largest":
            return max(faces, key=lambda f: f.area)
        return faces.sort_by(Axis.Z)[-1]

    def resolve_plane(
        self,
        frame: dict,
        resolve: Resolve,
        solids: dict[str, Any] | None = None,
    ) -> Plane:
        """Resolve a Frame or FaceFrame dict to a build123d Plane."""
        if frame.get("type") == "face":
            if not solids or frame["body"] not in solids:
                raise ValueError(f"Face frame references missing body {frame.get('body')!r}")
            face = self._face(solids[frame["body"]], frame["kind"])
            plane = Plane(face)
            off = resolve(frame.get("offset", 0))
            if abs(off) > 1e-9:
                plane = plane.offset(off)
            return plane
        # legacy frames may omit type
        return _plane_from_frame(frame, resolve)

    def make_solid(self, solid_spec: dict, frame: dict, resolve: Resolve) -> Any:
        kind = solid_spec["kind"]
        loc = _loc(frame, resolve)
        align = _align3(solid_spec)
        if kind == "box":
            w, d, h = resolve(solid_spec["width"]), resolve(solid_spec["depth"]), resolve(solid_spec["height"])
            shape = BDBox(w, d, h, align=align)
        elif kind == "cylinder":
            r, h = resolve(solid_spec["radius"]), resolve(solid_spec["height"])
            shape = BDCylinder(r, h, align=align)
        elif kind == "cone":
            shape = BDCone(
                resolve(solid_spec["bottom_radius"]),
                resolve(solid_spec["top_radius"]),
                resolve(solid_spec["height"]),
                align=align,
            )
        elif kind == "sphere":
            shape = BDSphere(resolve(solid_spec["radius"]), align=align)
        elif kind == "wedge":
            w, d, h = resolve(solid_spec["width"]), resolve(solid_spec["depth"]), resolve(solid_spec["height"])
            with BuildPart() as bp:
                with BuildSketch():
                    BDPolygon((-w / 2, -d / 2), (w / 2, -d / 2), (-w / 2, d / 2))
                extrude(amount=h)
            shape = bp.part
            # shift for align_z min: bottom at z=0
            if solid_spec.get("align", ("c", "c", "center"))[2] == "min":
                shape = Location((0, 0, 0)) * shape  # already extruded from z=0
        else:
            raise ValueError(f"Unknown solid kind {kind!r}")
        return loc * shape

    def _sketch_face(self, profile_spec: dict, plane: Plane, resolve: Resolve):
        kind = profile_spec["kind"]
        if kind == "offset":
            inner = self._sketch_face(profile_spec["inner"], plane, resolve)
            kind_map = {
                "arc": Kind.ARC,
                "intersection": Kind.INTERSECTION,
            }
            k = kind_map.get(str(profile_spec.get("offset_kind", "arc")), Kind.ARC)
            return bd_offset(inner, amount=resolve(profile_spec["amount"]), kind=k)
        if kind == "hull":
            with BuildSketch(plane) as sk:
                for p in profile_spec.get("profiles") or []:
                    self._build_profile(p, resolve, mode=Mode.ADD)
                make_hull()
            return sk.sketch
        if kind == "rounded_rect":
            with BuildSketch(plane) as sk:
                with Locations((resolve(profile_spec["cx"]), resolve(profile_spec["cy"]))):
                    Rectangle(resolve(profile_spec["width"]), resolve(profile_spec["height"]))
                try:
                    bd_fillet(sk.vertices(), radius=resolve(profile_spec["radius"]))
                except Exception:
                    pass
            return sk.sketch
        if kind == "shape":
            with BuildSketch(plane) as sk:
                for op in profile_spec.get("ops") or []:
                    mode = Mode.ADD if op.get("op", "add") == "add" else Mode.SUBTRACT
                    at = op.get("at", (0, 0))
                    dx, dy = resolve(at[0]), resolve(at[1])
                    prof = op["profile"]
                    if prof.get("kind") in ("offset", "hull", "shape", "rounded_rect", "bool"):
                        face = self._sketch_face(prof, plane, resolve)
                        with Locations((dx, dy)):
                            add(face, mode=mode)
                    else:
                        with Locations((dx, dy)):
                            self._build_profile(prof, resolve, mode=mode)
            return sk.sketch
        if kind == "bool":
            with BuildSketch(plane) as sk:
                self._build_profile(profile_spec["a"], resolve, mode=Mode.ADD)
                mode = Mode.SUBTRACT if profile_spec.get("op") == "cut" else Mode.ADD
                if profile_spec.get("op") == "intersect":
                    raise ValueError("Profile intersect not supported; use sequential cuts")
                self._build_profile(profile_spec["b"], resolve, mode=mode)
            return sk.sketch
        with BuildSketch(plane) as sk:
            self._build_profile(profile_spec, resolve)
        return sk.sketch

    def _build_profile(
        self, profile_spec: dict, resolve: Resolve, *, mode: Mode = Mode.ADD
    ) -> None:
        """Emit sketch entities into current BuildSketch context."""
        kind = profile_spec["kind"]
        if kind == "shape":
            for op in profile_spec.get("ops") or []:
                nested = Mode.ADD if op.get("op", "add") == "add" else Mode.SUBTRACT
                at = op.get("at", (0, 0))
                with Locations((resolve(at[0]), resolve(at[1]))):
                    self._build_profile(
                        op["profile"],
                        resolve,
                        mode=nested if mode == Mode.ADD else Mode.SUBTRACT,
                    )
            return
        if kind in ("offset", "hull"):
            raise ValueError(
                f"Profile kind {kind!r} must be resolved via _sketch_face, not _build_profile"
            )
        if kind == "rect":
            with Locations((resolve(profile_spec["cx"]), resolve(profile_spec["cy"]))):
                Rectangle(resolve(profile_spec["width"]), resolve(profile_spec["height"]), mode=mode)
        elif kind == "circle":
            with Locations((resolve(profile_spec["cx"]), resolve(profile_spec["cy"]))):
                BDCircle(resolve(profile_spec["radius"]), mode=mode)
        elif kind == "slot":
            with Locations((resolve(profile_spec["cx"]), resolve(profile_spec["cy"]))):
                SlotOverall(
                    resolve(profile_spec["length"]),
                    resolve(profile_spec["width"]),
                    rotation=resolve(profile_spec.get("rotation", 0)),
                    mode=mode,
                )
        elif kind == "polygon":
            pts = [(resolve(p[0]), resolve(p[1])) for p in profile_spec["points"]]
            BDPolygon(*pts, mode=mode)
        elif kind == "ellipse":
            with Locations((resolve(profile_spec["cx"]), resolve(profile_spec["cy"]))):
                BDEllipse(
                    resolve(profile_spec["x_radius"]),
                    resolve(profile_spec["y_radius"]),
                    rotation=resolve(profile_spec.get("rotation", 0)),
                    mode=mode,
                )
        elif kind == "regular_polygon":
            with Locations((resolve(profile_spec["cx"]), resolve(profile_spec["cy"]))):
                BDRegularPolygon(
                    resolve(profile_spec["radius"]),
                    int(profile_spec["sides"]),
                    rotation=resolve(profile_spec.get("rotation", 0)),
                    mode=mode,
                )
        elif kind == "rounded_rect":
            with Locations((resolve(profile_spec["cx"]), resolve(profile_spec["cy"]))):
                Rectangle(resolve(profile_spec["width"]), resolve(profile_spec["height"]), mode=mode)
        else:
            raise ValueError(f"Unknown profile kind {kind!r}")

    def extrude_profile(
        self,
        profile_spec: dict,
        height: float,
        frame: dict,
        resolve: Resolve,
        solids=None,
        *,
        twist: float = 0.0,
        scale: float | tuple[float, float] = 1.0,
        taper: float = 0.0,
    ) -> Any:
        plane = self.resolve_plane(frame, resolve, solids)
        face = self._sketch_face(profile_spec, plane, resolve)

        if isinstance(scale, (tuple, list)):
            sx, sy = float(scale[0]), float(scale[1])
        else:
            sx = sy = float(scale)

        simple = abs(twist) < 1e-9 and abs(sx - 1.0) < 1e-9 and abs(sy - 1.0) < 1e-9
        if simple:
            with BuildPart() as bp:
                extrude(face, amount=height, taper=taper)
            return bp.part

        # Twist / end-scale via lofted sections (OpenSCAD linear_extrude parity)
        n = max(8, int(abs(twist) / 12) + 4)
        if abs(sx - 1.0) > 1e-9 or abs(sy - 1.0) > 1e-9:
            n = max(n, 8)
        sections = []
        base_loc = plane.location
        for i in range(n + 1):
            t = i / n
            z = height * t
            ang = twist * t
            sxi = 1.0 + (sx - 1.0) * t
            syi = 1.0 + (sy - 1.0) * t
            loc = base_loc * Location((0, 0, z)) * Rot(Z=ang)
            sec = self._sketch_face(profile_spec, Plane(loc), resolve)
            if abs(sxi - 1.0) > 1e-9 or abs(syi - 1.0) > 1e-9:
                sec = bd_scale(sec, by=(sxi, syi, 1.0))
            sections.append(sec)
        with BuildPart() as bp:
            bd_loft(sections)
        return bp.part

    def hull_solids(self, solids: list[Any]) -> Any:
        """3D convex hull of solids (sampled vertices/edges → BREP solid)."""
        import numpy as np
        from scipy.spatial import ConvexHull

        if len(solids) < 1:
            raise ValueError("hull needs ≥ 1 solid")
        if len(solids) == 1:
            return solids[0]

        pts: list[tuple[float, float, float]] = []
        for s in solids:
            pts.extend(self._sample_solid_points(s))
        arr = np.asarray(pts, dtype=float)
        if len(arr) < 4:
            raise ValueError("not enough points for 3D hull")
        # Dedupe near-duplicates
        arr = np.unique(np.round(arr, 6), axis=0)
        if len(arr) < 4:
            raise ValueError("not enough unique points for 3D hull")

        try:
            hull = ConvexHull(arr)
        except Exception as exc:
            # Coplanar / flat — joggle slightly
            jitter = arr + np.random.default_rng(0).normal(0, 1e-5, arr.shape)
            try:
                hull = ConvexHull(jitter)
                arr = jitter
            except Exception as exc2:
                raise ValueError(f"3D hull failed: {exc}") from exc2

        faces = []
        for tri in hull.simplices:
            p0, p1, p2 = [Vector(*arr[i]) for i in tri]
            # Ensure outward-ish winding using hull equations if available
            w = Wire.make_polygon([p0, p1, p2], close=True)
            faces.append(Face(w))
        shell = Shell(faces)
        solid = BDSolid(shell)
        if not solid.is_valid or solid.volume < 0:
            # reverse orientation attempt
            faces_r = []
            for tri in hull.simplices:
                p0, p1, p2 = [Vector(*arr[i]) for i in tri]
                w = Wire.make_polygon([p0, p2, p1], close=True)
                faces_r.append(Face(w))
            solid = BDSolid(Shell(faces_r))
        return solid

    def _sample_solid_points(self, solid: Any, n_edge: int = 10) -> list[tuple[float, float, float]]:
        pts: list[tuple[float, float, float]] = []
        for v in solid.vertices():
            pts.append((float(v.X), float(v.Y), float(v.Z)))
        for e in solid.edges():
            for i in range(n_edge):
                t = (i + 0.5) / n_edge
                try:
                    p = e.position_at(t)
                    pts.append((float(p.X), float(p.Y), float(p.Z)))
                except Exception:
                    continue
        for f in solid.faces():
            try:
                c = f.center()
                pts.append((float(c.X), float(c.Y), float(c.Z)))
            except Exception:
                continue
        return pts

    def revolve_profile(
        self, profile_spec: dict, angle_deg: float, frame: dict, resolve: Resolve, solids=None
    ) -> Any:
        plane = self.resolve_plane(frame, resolve, solids)
        face = self._sketch_face(profile_spec, plane, resolve)
        with BuildPart() as bp:
            revolve(face, axis=Axis.Y, revolution_arc=angle_deg)
        return bp.part

    def cut_profile(
        self,
        target: Any,
        profile_spec: dict,
        *,
        height: float | None,
        through: bool,
        frame: dict,
        resolve: Resolve,
        solids: dict | None = None,
    ) -> Any:
        plane = self.resolve_plane(frame, resolve, solids)
        face = self._sketch_face(profile_spec, plane, resolve)
        if through or height is None:
            bb = target.bounding_box()
            amount = max(bb.size.X, bb.size.Y, bb.size.Z) + 2
            with BuildPart() as bp:
                add(target)
                extrude(face, amount=amount, both=True, mode=Mode.SUBTRACT)
            return bp.part
        with BuildPart() as bp:
            add(target)
            extrude(face, amount=-abs(height), mode=Mode.SUBTRACT)
        return bp.part

    def boolean_fuse(self, a: Any, b: Any) -> Any:
        with BuildPart() as bp:
            add(a)
            add(b, mode=Mode.ADD)
        return bp.part

    def boolean_cut(self, a: Any, b: Any) -> Any:
        with BuildPart() as bp:
            add(a)
            add(b, mode=Mode.SUBTRACT)
        return bp.part

    def boolean_intersect(self, a: Any, b: Any) -> Any:
        with BuildPart() as bp:
            add(a)
            add(b, mode=Mode.INTERSECT)
        return bp.part

    def _edges(self, solid: Any, edge_kind: str):
        if edge_kind == "all":
            return solid.edges()
        if edge_kind == "vertical":
            return solid.edges().filter_by(Axis.Z)
        if edge_kind == "horizontal":
            return solid.edges().filter_by(Axis.X) + solid.edges().filter_by(Axis.Y)
        if edge_kind == "top":
            return solid.edges().group_by(Axis.Z)[-1]
        if edge_kind == "bottom":
            return solid.edges().group_by(Axis.Z)[0]
        return solid.edges()

    def hole(
        self,
        target: Any,
        *,
        diameter: float,
        depth: float | None,
        face_kind: str,
        at: tuple[float, float],
    ) -> Any:
        face = self._face(target, face_kind)
        plane = Plane(face)
        r = diameter / 2
        with BuildPart() as bp:
            add(target)
            with BuildSketch(plane):
                with Locations(at):
                    BDCircle(r)
            if depth is None:
                bb = target.bounding_box()
                cut = max(bb.size.X, bb.size.Y, bb.size.Z) + 1
                extrude(amount=-cut, mode=Mode.SUBTRACT)
            else:
                extrude(amount=-abs(depth), mode=Mode.SUBTRACT)
        return bp.part

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
    ) -> Any:
        face = self._face(target, face_kind)
        plane = Plane(face)
        with BuildPart() as bp:
            add(target)
            with BuildSketch(plane):
                with Locations(at):
                    BDCircle(counter_diameter / 2)
            extrude(amount=-abs(counter_depth), mode=Mode.SUBTRACT)
            with BuildSketch(plane):
                with Locations(at):
                    BDCircle(diameter / 2)
            extrude(amount=-abs(depth), mode=Mode.SUBTRACT)
        return bp.part

    def fillet(self, target: Any, radius: float, edge_kind: str) -> Any:
        edges = self._edges(target, edge_kind)
        if not edges:
            return target
        with BuildPart() as bp:
            add(target)
            try:
                bd_fillet(edges, radius=radius)
            except Exception:
                try:
                    bd_fillet(edges, radius=min(radius, 1.0))
                except Exception:
                    pass
        return bp.part

    def chamfer(self, target: Any, length: float, edge_kind: str) -> Any:
        edges = self._edges(target, edge_kind)
        if not edges:
            return target
        with BuildPart() as bp:
            add(target)
            try:
                bd_chamfer(edges, length=length)
            except Exception:
                pass
        return bp.part

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
    ) -> Any:
        face = self._face(target, face_kind)
        plane = Plane(face)
        r = diameter / 2
        with BuildPart() as bp:
            add(target)
            with BuildSketch(plane):
                with Locations(center):
                    with GridLocations(spacing_x, spacing_y, count_x, count_y):
                        BDCircle(r)
            if depth is None:
                bb = target.bounding_box()
                cut = max(bb.size.X, bb.size.Y, bb.size.Z) + 1
                extrude(amount=-cut, mode=Mode.SUBTRACT)
            else:
                extrude(amount=-abs(depth), mode=Mode.SUBTRACT)
        return bp.part

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
    ) -> Any:
        face = self._face(target, face_kind)
        plane = Plane(face)
        r = diameter / 2
        with BuildPart() as bp:
            add(target)
            with BuildSketch(plane):
                with Locations(center):
                    with PolarLocations(radius, count, start_angle=start_angle):
                        BDCircle(r)
            if depth is None:
                bb = target.bounding_box()
                cut = max(bb.size.X, bb.size.Y, bb.size.Z) + 1
                extrude(amount=-cut, mode=Mode.SUBTRACT)
            else:
                extrude(amount=-abs(depth), mode=Mode.SUBTRACT)
        return bp.part

    def mirror(self, target: Any, plane: str) -> Any:
        plane_map = {"XY": Plane.XY, "XZ": Plane.XZ, "YZ": Plane.YZ}
        pl = plane_map.get(plane.upper(), Plane.YZ)
        with BuildPart() as bp:
            add(target)
            bd_mirror(about=pl)
        return bp.part

    def pattern_grid(
        self,
        seed: Any,
        *,
        count_x: int,
        count_y: int,
        spacing_x: float,
        spacing_y: float,
    ) -> Any:
        with BuildPart() as bp:
            for i in range(count_x):
                for j in range(count_y):
                    ox = (i - (count_x - 1) / 2) * spacing_x
                    oy = (j - (count_y - 1) / 2) * spacing_y
                    add(Location((ox, oy, 0)) * seed)
        return bp.part

    def pattern_polar(
        self,
        seed: Any,
        *,
        count: int,
        radius: float,
        start_angle: float,
    ) -> Any:
        with BuildPart() as bp:
            for i in range(count):
                ang = math.radians(start_angle + i * (360.0 / count))
                ox = radius * math.cos(ang)
                oy = radius * math.sin(ang)
                add(Location((ox, oy, 0)) * seed)
        return bp.part

    def metrics(self, solid: Any) -> dict[str, Any]:
        bb = solid.bounding_box()
        try:
            vol = float(solid.volume)
        except Exception:
            vol = 0.0
        return {
            "bbox_mm": {
                "x": round(bb.size.X, 3),
                "y": round(bb.size.Y, 3),
                "z": round(bb.size.Z, 3),
            },
            "center_mm": {
                "x": round(bb.center().X, 3),
                "y": round(bb.center().Y, 3),
                "z": round(bb.center().Z, 3),
            },
            "volume_mm3": round(vol, 2),
        }

    def export(self, solid: Any, path: str) -> None:
        p = path.lower()
        if p.endswith(".step") or p.endswith(".stp"):
            export_step(solid, path)
        else:
            export_stl(solid, path)

    def shell(self, target: Any, thickness: float, face_kind: str) -> Any:
        with BuildPart() as bp:
            add(target)
            opening = self._face(bp.part, face_kind)
            bd_offset(amount=-abs(thickness), openings=[opening])
        return bp.part

    def pad(
        self,
        target: Any,
        profile_spec: dict,
        *,
        height: float,
        face_kind: str,
        at: tuple[float, float],
        resolve: Resolve,
    ) -> Any:
        face = self._face(target, face_kind)
        plane = Plane(face)
        # shift profile center via at=
        spec = dict(profile_spec)
        if "cx" in spec:
            spec = {
                **spec,
                "cx": at[0] + (0 if not isinstance(spec.get("cx"), (int, float)) else 0),
            }
        # Build profile centered at `at` on the face
        kind = profile_spec["kind"]
        with BuildPart() as bp:
            add(target)
            with BuildSketch(plane) as sk:
                with Locations(at):
                    if kind == "circle":
                        BDCircle(resolve(profile_spec["radius"]))
                    elif kind == "rect":
                        Rectangle(resolve(profile_spec["width"]), resolve(profile_spec["height"]))
                    elif kind == "rounded_rect":
                        Rectangle(resolve(profile_spec["width"]), resolve(profile_spec["height"]))
                        try:
                            bd_fillet(sk.vertices(), radius=resolve(profile_spec["radius"]))
                        except Exception:
                            pass
                    elif kind == "slot":
                        SlotOverall(resolve(profile_spec["length"]), resolve(profile_spec["width"]))
                    else:
                        self._build_profile(profile_spec, resolve)
            extrude(amount=abs(height), mode=Mode.ADD)
        return bp.part

    def emboss(
        self,
        target: Any,
        *,
        text: str,
        font_size: float,
        height: float,
        face_kind: str,
        at: tuple[float, float],
        font: str,
    ) -> Any:
        from build123d import Align as A

        face = self._face(target, face_kind)
        plane = Plane(face)
        with BuildPart() as bp:
            add(target)
            with BuildSketch(plane):
                with Locations(at):
                    Text(text, font_size=font_size, font=font, align=(A.CENTER, A.CENTER))
            extrude(amount=abs(height), mode=Mode.ADD)
        return bp.part

    def loft_profiles(
        self,
        profiles: list[dict],
        frames: list[dict],
        resolve: Resolve,
        solids=None,
    ) -> Any:
        sections = []
        for prof, fr in zip(profiles, frames):
            plane = self.resolve_plane(fr, resolve, solids)
            sections.append(self._sketch_face(prof, plane, resolve))
        with BuildPart() as bp:
            bd_loft(sections)
        return bp.part

    def lip(
        self,
        target: Any,
        *,
        width: float,
        height: float,
        mode: str,
        face_kind: str,
    ) -> Any:
        """Male ridge or female groove near the perimeter of an open face."""
        face = self._face(target, face_kind)
        plane = Plane(face)
        bb = target.bounding_box()
        # Approximate outer size from bbox projected on XY of face — use world bbox
        ox, oy = bb.size.X, bb.size.Y
        # inset ring: outer slightly inside outer wall, inner inset by width
        outer_w = max(ox - 0.4, 1)
        outer_h = max(oy - 0.4, 1)
        inner_w = max(outer_w - 2 * width, 0.5)
        inner_h = max(outer_h - 2 * width, 0.5)
        with BuildPart() as bp:
            add(target)
            with BuildSketch(plane) as sk:
                Rectangle(outer_w, outer_h)
                Rectangle(inner_w, inner_h, mode=Mode.SUBTRACT)
            if mode == "female":
                extrude(amount=-abs(height), mode=Mode.SUBTRACT)
            else:
                extrude(amount=abs(height), mode=Mode.ADD)
        return bp.part

    def boss(
        self,
        target: Any,
        *,
        outer_d: float,
        height: float,
        face_kind: str,
        at: tuple[float, float],
        hole_d: float | None,
        resolve: Resolve,
    ) -> Any:
        face = self._face(target, face_kind)
        plane = Plane(face)
        with BuildPart() as bp:
            add(target)
            with BuildSketch(plane):
                with Locations(at):
                    BDCircle(outer_d / 2)
            extrude(amount=abs(height), mode=Mode.ADD)
            if hole_d is not None:
                with BuildSketch(plane):
                    with Locations(at):
                        BDCircle(hole_d / 2)
                extrude(amount=-abs(height) - 0.1, mode=Mode.SUBTRACT)
        return bp.part

    def import_svg(
        self,
        target: Any,
        path: str,
        *,
        height: float,
        operation: str,
        face_kind: str,
        at: tuple[float, float],
        scale: float,
    ) -> Any:
        from build123d import import_svg as bd_import_svg

        face = self._face(target, face_kind)
        plane = Plane(face)
        shapes = bd_import_svg(path)
        with BuildPart() as bp:
            add(target)
            with BuildSketch(plane) as sk:
                with Locations(at):
                    for shape in shapes:
                        add(shape.scale(scale) if hasattr(shape, "scale") else shape)
                try:
                    from build123d import make_face

                    make_face()
                except Exception:
                    pass
            mode = Mode.SUBTRACT if operation == "cut" else Mode.ADD
            amt = -abs(height) if operation == "cut" else abs(height)
            extrude(amount=amt, mode=mode)
        return bp.part

    def deboss(
        self,
        target: Any,
        *,
        text: str,
        font_size: float,
        depth: float,
        face_kind: str,
        at: tuple[float, float],
        font: str,
    ) -> Any:
        from build123d import Align as A

        face = self._face(target, face_kind)
        plane = Plane(face)
        with BuildPart() as bp:
            add(target)
            with BuildSketch(plane):
                with Locations(at):
                    Text(text, font_size=font_size, font=font, align=(A.CENTER, A.CENTER))
            extrude(amount=-abs(depth), mode=Mode.SUBTRACT)
        return bp.part
