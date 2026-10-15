"""
Rolled Beam Girder Geometry Builder (Geometry Only)

- Builds a rolled I-section girder from the section catalog (common.py)
- Reuses stiffener, shear stud and support plates of the plate girder builder
- Returns raw TopoDS_Shapes in the same dict layout as the plate girder builder
"""

import math

from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Trsf, gp_Ax1, gp_Dir
from OCC.Core.GC import GC_MakeArcOfCircle
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCC.Core.BRepBuilderAPI import (
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeWire,
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_Transform
)

from osdagbridge.core.bridge_components.super_structure.plate_girder.builder import (
    build_plate_girder_geometry, GirderSegment
)

# Result keys that move together when the girder is shifted in Z
SHIFTED_KEYS = (
    "web", "intermediate_stiffeners", "bearing_stiffeners", "longitudinal_stiffeners",
    "shear_studs", "supports_vertical", "supports_wide_horiz", "supports_long_horiz",
    "supports_cyl",
)


def _pnt(p):
    return gp_Pnt(p[0], 0.0, p[1])


def _unit(a, b):
    """Unit vector pointing from a to b (2D, X-Z plane)."""
    d = math.dist(a, b)
    return ((b[0] - a[0]) / d, (b[1] - a[1]) / d)


def _fillet_corner(p_prev, p_vertex, p_next, radius):
    """
    Round a polygon corner with a circular arc.

    Returns:
        (tangent_in, arc_mid, tangent_out) as 2D points
    """
    u1 = _unit(p_vertex, p_prev)
    u2 = _unit(p_vertex, p_next)
    half = math.acos(max(-1.0, min(1.0, u1[0] * u2[0] + u1[1] * u2[1]))) / 2.0
    t = radius / math.tan(half)
    bis = (u1[0] + u2[0], u1[1] + u2[1])
    n = math.hypot(*bis)
    bis = (bis[0] / n, bis[1] / n)
    d = radius / math.sin(half)
    centre = (p_vertex[0] + bis[0] * d, p_vertex[1] + bis[1] * d)
    mid = (centre[0] - bis[0] * radius, centre[1] - bis[1] * radius)
    t_in = (p_vertex[0] + u1[0] * t, p_vertex[1] + u1[1] * t)
    t_out = (p_vertex[0] + u2[0] * t, p_vertex[1] + u2[1] * t)
    return t_in, mid, t_out


def _make_i_section_wire(section):
    """
    Closed I-section outline (X-Z plane, centred on the origin) with the
    catalog root radius (web-flange) and toe radius (flange tip) rounded.
    """
    b = section.flange_width_mm / 2.0
    w = section.web_thickness_mm / 2.0
    z_out = section.depth_mm / 2.0
    z_in = z_out - section.flange_thickness_mm
    r1 = section.root_radius_mm
    r2 = section.toe_radius_mm

    # Clockwise in X-Z so the prism along +Y has outward face normals
    corners = [
        ((-b, z_out), 0.0), ((b, z_out), 0.0), ((b, z_in), r2), ((w, z_in), r1),
        ((w, -z_in), r1), ((b, -z_in), r2), ((b, -z_out), 0.0), ((-b, -z_out), 0.0),
        ((-b, -z_in), r2), ((-w, -z_in), r1), ((-w, z_in), r1), ((-b, z_in), r2),
    ]

    n = len(corners)
    rounded = []
    for i, (pt, r) in enumerate(corners):
        if r > 0:
            rounded.append(_fillet_corner(corners[i - 1][0], pt, corners[(i + 1) % n][0], r))
        else:
            rounded.append((pt, None, pt))

    wire = BRepBuilderAPI_MakeWire()
    for i, (t_in, mid, t_out) in enumerate(rounded):
        prev_out = rounded[i - 1][2]
        if math.dist(prev_out, t_in) > 1e-9:
            wire.Add(BRepBuilderAPI_MakeEdge(_pnt(prev_out), _pnt(t_in)).Edge())
        if mid is not None:
            arc = GC_MakeArcOfCircle(_pnt(t_in), _pnt(mid), _pnt(t_out)).Value()
            wire.Add(BRepBuilderAPI_MakeEdge(arc).Edge())
    return wire.Wire()


def _make_rolled_solid(section, length):
    """I-section solid extruded along Y, rotated -90 deg about Z like the plate girder shapes."""
    face = BRepBuilderAPI_MakeFace(_make_i_section_wire(section)).Face()
    solid = BRepPrimAPI_MakePrism(face, gp_Vec(0, length, 0)).Shape()
    trsf = gp_Trsf()
    trsf.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)), math.radians(-90))
    return BRepBuilderAPI_Transform(solid, trsf, True).Shape()


def _translate_z(shape, dz):
    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(0, 0, dz))
    return BRepBuilderAPI_Transform(shape, trsf, True).Shape()


def build_rolled_girder_geometry(*, section, reference_top_z, **kwargs):
    """
    Geometry-only rolled beam girder builder for Osdag Bridge.

    Args:
        section: BeamSection from girder_catalog (dimensions in mm)
        reference_top_z: Z of the girder top the deck is placed on
        **kwargs: same keyword arguments as build_plate_girder_geometry

    Returns:
        dict with the same keys as build_plate_girder_geometry
    """
    depth = section.depth_mm
    tf = section.flange_thickness_mm
    tw = section.web_thickness_mm
    bf = section.flange_width_mm
    web_depth = depth - 2 * tf
    length = kwargs["length"]

    # Equivalent clear web / flange dims keep stiffeners, studs and supports on the rolled profile
    kwargs.update(
        D=web_depth, tw=tw, T_ft=tf, T_fb=tf, B_ft=bf, B_fb=bf,
        segments=[GirderSegment(length=length, D=web_depth, tw=tw, T_ft=tf, T_fb=tf, B_ft=bf, B_fb=bf)],
    )
    # Stiffener chamfer must stay below half the clear web depth
    kwargs["chamfer_length"] = min(kwargs.get("chamfer_length", 40), web_depth / 4.0)
    pg = build_plate_girder_geometry(**kwargs)

    pg["web"] = [_make_rolled_solid(section, length)]
    pg["top_flange"] = []
    pg["bottom_flange"] = []

    # Keep the girder top flush with the deck reference
    dz = reference_top_z - depth / 2.0
    if abs(dz) > 1e-9:
        for key in SHIFTED_KEYS:
            pg[key] = [_translate_z(s, dz) for s in pg[key]]
        pg["stiffeners"] = (
            pg["intermediate_stiffeners"] + pg["bearing_stiffeners"] + pg["longitudinal_stiffeners"]
        )
        pg["supports_tri"] = (
            pg["supports_vertical"] + pg["supports_wide_horiz"] + pg["supports_long_horiz"]
        )

    return pg