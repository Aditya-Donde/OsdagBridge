"""
Cross bracing builder.

- Angle / Channel / Double Angle / Double Channel sections
- X and K bracing systems
- Geometry + placement 
"""

# OCC imports

import math

from OCC.Core.gp import (
    gp_Pnt, gp_Vec, gp_Trsf, gp_Ax1, gp_Ax2, gp_Dir
)
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform


# SECTION GEOMETRY

def _create_angle_section(length, leg_h, leg_w, thickness):

    leg1 = BRepPrimAPI_MakeBox(length, thickness, leg_h).Shape()
    leg2 = BRepPrimAPI_MakeBox(length, leg_w, thickness).Shape()

    angle = BRepAlgoAPI_Fuse(leg1, leg2).Shape()

    trsf = gp_Trsf()
    trsf.SetTranslation(
        gp_Vec(-length / 2, -leg_w / 2, -leg_h / 2)
    )

    return BRepBuilderAPI_Transform(angle, trsf, True).Shape()


def _create_channel_section(
    length, depth, flange_width, web_thickness, flange_thickness
):

    web = BRepPrimAPI_MakeBox(
        length, web_thickness, depth
    ).Shape()

    bottom = BRepPrimAPI_MakeBox(
        length, flange_width, flange_thickness
    ).Shape()

    top = BRepPrimAPI_MakeBox(
        length, flange_width, flange_thickness
    ).Shape()

    trsf_top = gp_Trsf()
    trsf_top.SetTranslation(
        gp_Vec(0, 0, depth - flange_thickness)
    )
    top = BRepBuilderAPI_Transform(top, trsf_top, True).Shape()

    channel = BRepAlgoAPI_Fuse(web, bottom).Shape()
    channel = BRepAlgoAPI_Fuse(channel, top).Shape()

    trsf = gp_Trsf()
    trsf.SetTranslation(
        gp_Vec(-length / 2, -flange_width / 2, -depth / 2)
    )

    return BRepBuilderAPI_Transform(channel, trsf, True).Shape()


def _create_double_angle_section(
    length, leg_h, leg_w, thickness, connection_type="LONGER_LEG"
):

    base = _create_angle_section(length, leg_h, leg_w, thickness)

    mirror = gp_Trsf()
    mirror.SetMirror(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(0, 1, 0)))
    mirrored = BRepBuilderAPI_Transform(base, mirror, True).Shape()

    offset = leg_h / 2 if connection_type == "LONGER_LEG" else leg_w / 2

    t1 = gp_Trsf()
    t1.SetTranslation(gp_Vec(0, +offset, 0))

    t2 = gp_Trsf()
    t2.SetTranslation(gp_Vec(0, -offset, 0))

    a1 = BRepBuilderAPI_Transform(base, t1, True).Shape()
    a2 = BRepBuilderAPI_Transform(mirrored, t2, True).Shape()

    return BRepAlgoAPI_Fuse(a1, a2).Shape()


def _create_double_channel_section(
    length, depth, flange_width, web_thickness, flange_thickness
):

    base = _create_channel_section(
        length, depth, flange_width, web_thickness, flange_thickness
    )

    mirror = gp_Trsf()
    mirror.SetMirror(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(0, 1, 0)))
    mirrored = BRepBuilderAPI_Transform(base, mirror, True).Shape()

    offset = flange_width / 2

    t1 = gp_Trsf()
    t1.SetTranslation(gp_Vec(0, +offset, 0))

    t2 = gp_Trsf()
    t2.SetTranslation(gp_Vec(0, -offset, 0))

    c1 = BRepBuilderAPI_Transform(base, t1, True).Shape()
    c2 = BRepBuilderAPI_Transform(mirrored, t2, True).Shape()

    return BRepAlgoAPI_Fuse(c1, c2).Shape()


# INTERNAL UTILITIES

def _get_roll_angle(section_type, roll_sign):
    if section_type in ("ANGLE", "CHANNEL"):
        return roll_sign * (math.pi / 2)
    return 0.0


def _create_section_solid(section_type, length, thickness, dims):

    if section_type == "ANGLE":
        return _create_angle_section(
            length, dims["leg_h"], dims["leg_w"], thickness
        )

    if section_type == "CHANNEL":
        return _create_channel_section(
            length,
            dims["depth"],
            dims["flange_width"],
            dims["web_thickness"],
            dims["flange_thickness"]
        )

    if section_type == "DOUBLE_ANGLE":
        return _create_double_angle_section(
            length,
            dims["leg_h"],
            dims["leg_w"],
            thickness,
            dims.get("connection_type", "LONGER_LEG")
        )

    if section_type == "DOUBLE_CHANNEL":
        return _create_double_channel_section(
            length,
            dims["depth"],
            dims["flange_width"],
            dims["web_thickness"],
            dims["flange_thickness"]
        )

    raise ValueError("Unsupported section type")


# MEMBER CREATION

def _create_diagonal_member(p1, p2, thickness, section_type, dims, roll_sign):

    vec = gp_Vec(p1, p2)
    length = vec.Magnitude()

    solid = _create_section_solid(
        section_type, length, thickness, dims
    )

    x_dir = gp_Dir(1, 0, 0)
    tgt = gp_Dir(vec)

    axis = gp_Vec(x_dir.Crossed(tgt))
    angle = x_dir.Angle(tgt)

    if axis.Magnitude() > 1e-6:
        tr = gp_Trsf()
        tr.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(axis)), angle)
        solid = BRepBuilderAPI_Transform(solid, tr, True).Shape()

    roll = _get_roll_angle(section_type, roll_sign)
    if abs(roll) > 1e-6:
        tr = gp_Trsf()
        tr.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), tgt), roll)
        solid = BRepBuilderAPI_Transform(solid, tr, True).Shape()

    mid = gp_Pnt(
        (p1.X() + p2.X()) / 2,
        (p1.Y() + p2.Y()) / 2,
        (p1.Z() + p2.Z()) / 2
    )

    tr = gp_Trsf()
    tr.SetTranslation(gp_Vec(mid.X(), mid.Y(), mid.Z()))

    return BRepBuilderAPI_Transform(solid, tr, True).Shape()


def _create_horizontal_member_y(
    x, yL, yR, z, thickness, flange_width, section_type, dims, roll_sign
):

    y0 = yL 
    y1 = yR
    length = y1 - y0
    y_mid = (y0 + y1) / 2

    solid = _create_section_solid(
        section_type, length, thickness, dims
    )

    tr = gp_Trsf()
    tr.SetRotation(
        gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)),
        math.pi / 2
    )
    solid = BRepBuilderAPI_Transform(solid, tr, True).Shape()

    roll = _get_roll_angle(section_type, roll_sign)
    if abs(roll) > 1e-6:
        tr = gp_Trsf()
        tr.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 1, 0)), roll)
        solid = BRepBuilderAPI_Transform(solid, tr, True).Shape()

    tr = gp_Trsf()
    tr.SetTranslation(gp_Vec(x, y_mid, z))

    return BRepBuilderAPI_Transform(solid, tr, True).Shape()


# BRACING TOPOLOGIES

def _x_bracing(
    x, yL, yR, depth, tf, thickness, flange_w,
    section_type, dims, bracket
):

    # ✅ WEB–FLANGE JUNCTIONS
    z_bot = -depth / 2
    z_top = +depth / 2

    yl = yL
    yr = yR


    braces = [
        # Left TOP → Right BOTTOM
        _create_diagonal_member(
            gp_Pnt(x, yl, z_top), gp_Pnt(x, yr, z_bot),
            thickness, section_type, dims, +1
        ),
        # Left BOTTOM → Right TOP
        _create_diagonal_member(
            gp_Pnt(x, yl, z_bot), gp_Pnt(x, yr, z_top),
            thickness, section_type, dims, -1
        )
    ]

    if bracket in ("LOWER", "BOTH"):
        braces.append(
            _create_horizontal_member_y(
                x, yL, yR, z_bot,
                thickness, flange_w,
                section_type, dims, +1
            )
        )

    if bracket in ("UPPER", "BOTH"):
        braces.append(
            _create_horizontal_member_y(
                x, yL, yR, z_top,
                thickness, flange_w,
                section_type, dims, +1
            )
        )

    return braces


def _k_bracing(
    x, yL, yR, depth, tf, thickness, flange_w,
    section_type, dims, top_bracket
):

    z_bot = -depth / 2
    z_top = +depth / 2

    yl = yL
    yr = yR
    ym = (yl + yr) / 2

    braces = [
        _create_diagonal_member(
            gp_Pnt(x, yl, z_top), gp_Pnt(x, ym, z_bot),
            thickness, section_type, dims, +1
        ),
        _create_diagonal_member(
            gp_Pnt(x, yr, z_top), gp_Pnt(x, ym, z_bot),
            thickness, section_type, dims, -1
        ),
        _create_horizontal_member_y(
            x, yL, yR, z_bot,
            thickness, flange_w,
            section_type, dims, +1
        )
    ]

    if top_bracket:
        braces.append(
            _create_horizontal_member_y(
                x, yL, yR, z_top,
                thickness, flange_w,
                section_type, dims, +1
            )
        )

    return braces

# PUBLIC API

def build_cross_bracings(
    *,
    span_length_L,
    num_girders,
    girder_spacing,
    girder_depth,
    flange_thickness,
    flange_width,

    bracing_type,          # "X" or "K"
    section_type,          # "ANGLE", "CHANNEL", "DOUBLE_ANGLE", "DOUBKE_CHANNEL"
    section_dims,
    thickness,

    panel_spacing,
    bracket_option="BOTH",
    top_bracket=False
):
    """
    Build cross bracings for entire bridge.
    """

    bracings = []

    # Number of bracing frames along span
    n = int(span_length_L / panel_spacing) - 1
    n_total = n + 2
    spacing = span_length_L / (n_total - 1)
    x_positions = [i * spacing for i in range(n_total)]

    total_width = (num_girders - 1) * girder_spacing
    for x in x_positions:
        for i in range(num_girders - 1):

            yL = (i * girder_spacing) - total_width / 2
            yR = yL + girder_spacing

            if bracing_type == "X":
                bracings.extend(
                    _x_bracing(
                        x, yL, yR,
                        girder_depth, flange_thickness,
                        thickness, flange_width,
                        section_type, section_dims,
                        bracket_option
                    )
                )

            elif bracing_type == "K":
                bracings.extend(
                    _k_bracing(
                        x, yL, yR,
                        girder_depth, flange_thickness,
                        thickness, flange_width,
                        section_type, section_dims,
                        top_bracket
                    )
                )

        x += panel_spacing

    return bracings
