"""
Plate Girder Geometry Builder (Geometry Only)

- Based on standalone Osdag CAD plate girder logic
- NO welds
- NO viewer
- NO fusion
- Returns raw TopoDS_Shapes for Bridge CAD pipeline
"""

import math
import numpy as np

from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Trsf, gp_Ax3, gp_Dir
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCC.Core.BRepBuilderAPI import (
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeWire,
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_Transform
)


# ------------------------------------------------------------------
# Helper geometry utilities (from standalone code)
# ------------------------------------------------------------------

def _make_edge(p1, p2):
    return BRepBuilderAPI_MakeEdge(p1, p2).Edge()


def _make_wire_from_points(points):
    wire_maker = BRepBuilderAPI_MakeWire()
    for i in range(len(points)):
        p_start = points[i]
        p_end = points[(i + 1) % len(points)]
        wire_maker.Add(_make_edge(p_start, p_end))
    return wire_maker.Wire()


def _make_plate(origin, length, width, thickness, u_dir, w_dir):
    """
    Generic rectangular plate creator using face + prism.
    """
    v_dir = np.cross(w_dir, u_dir)

    a1 = origin + (thickness / 2) * u_dir + (length / 2) * v_dir
    a2 = origin - (thickness / 2) * u_dir + (length / 2) * v_dir
    a3 = origin - (thickness / 2) * u_dir - (length / 2) * v_dir
    a4 = origin + (thickness / 2) * u_dir - (length / 2) * v_dir

    pts = [
        gp_Pnt(*a1),
        gp_Pnt(*a2),
        gp_Pnt(*a3),
        gp_Pnt(*a4),
    ]

    wire = _make_wire_from_points(pts)
    face = BRepBuilderAPI_MakeFace(wire).Face()

    extrude_vec = gp_Vec(*(width * w_dir))
    return BRepPrimAPI_MakePrism(face, extrude_vec).Shape()


from OCC.Core.gp import gp_Ax1, gp_Dir
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform

def _rotate_about_z(shape, angle_deg):
    trsf = gp_Trsf()
    trsf.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)),
                     math.radians(angle_deg))
    return BRepBuilderAPI_Transform(shape, trsf, True).Shape()


def _create_stiffener_plate(position, width, height, thickness, chamfer, side):
    """
    Creates a single stiffener plate (left or right).
    Geometry copied from standalone logic (no welds).
    """
    x, y, z = map(float, position)
    c = chamfer

    if side == "right":
        pts = [
            gp_Pnt(0, 0,  height/2 - c),
            gp_Pnt(c, 0,  height/2),
            gp_Pnt(width, 0,  height/2),
            gp_Pnt(width, 0, -height/2),
            gp_Pnt(c, 0, -height/2),
            gp_Pnt(0, 0, -height/2 + c),
        ]
    else:  # left
        pts = [
            gp_Pnt(0, 0,  height/2 - c),
            gp_Pnt(0, 0, -height/2 + c),
            gp_Pnt(-c, 0, -height/2),
            gp_Pnt(-width, 0, -height/2),
            gp_Pnt(-width, 0,  height/2),
            gp_Pnt(-c, 0,  height/2),
        ]

    wire = BRepBuilderAPI_MakeWire()
    for i in range(len(pts)):
        wire.Add(BRepBuilderAPI_MakeEdge(pts[i], pts[(i + 1) % len(pts)]).Edge())

    face = BRepBuilderAPI_MakeFace(wire.Wire()).Face()
    solid = BRepPrimAPI_MakePrism(face, gp_Vec(0, thickness, 0)).Shape()

    local_ax = gp_Ax3(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1), gp_Dir(0, 1, 0))
    global_ax = gp_Ax3(gp_Pnt(x, y - thickness / 2, z), gp_Dir(0, 0, 1), gp_Dir(0, 1, 0))

    trsf = gp_Trsf()
    trsf.SetDisplacement(local_ax, global_ax)

    return BRepBuilderAPI_Transform(solid, trsf, True).Shape()


# ------------------------------------------------------------------
# MAIN API — this replaces old I-section builder
# ------------------------------------------------------------------

def build_plate_girder_geometry(
    *,
    D,
    tw,
    length,
    T_ft,
    T_fb,
    B_ft,
    B_fb,
    stiffener_spacing,
    T_is,
    chamfer_length
):
    """
    Geometry-only Plate Girder builder for Osdag Bridge.
    """

    # Directions (same as standalone)
    u_dir = np.array([0., 0., 1.])
    w_dir = np.array([0., 1., 0.])

    # Web plate
    web = _make_plate(
        origin=np.array([0., 0., 0.]),
        length=tw,
        width=length,
        thickness=D,
        u_dir=u_dir,
        w_dir=w_dir
    )

    # Top flange
    top_flange = _make_plate(
        origin=np.array([0., 0., (D + T_ft) / 2]),
        length=B_ft,
        width=length,
        thickness=T_ft,
        u_dir=u_dir,
        w_dir=w_dir
    )

    # Bottom flange
    bottom_flange = _make_plate(
        origin=np.array([0., 0., -(D + T_fb) / 2]),
        length=B_fb,
        width=length,
        thickness=T_fb,
        u_dir=u_dir,
        w_dir=w_dir
    )

    # Stiffeners (intermediate only, no end stiffeners)
    stiffeners = []
    eff_depth = D - T_ft - T_fb
    stiff_width = (min(B_ft, B_fb) - tw) / 2

    num_panels = max(1, int(length // stiffener_spacing))

    for i in range(1, num_panels):
        y = i * stiffener_spacing

        stiffeners.append(
            _create_stiffener_plate(
                position=[ tw / 2, y, 0 ],
                width=stiff_width,
                height=D,
                thickness=T_is,
                chamfer=chamfer_length,
                side="right"
            )
        )

        stiffeners.append(
            _create_stiffener_plate(
                position=[ -tw / 2, y, 0 ],
                width=stiff_width,
                height=D,
                thickness=T_is,
                chamfer=chamfer_length,
                side="left"
            )
        )


    web = _rotate_about_z(web, -90)
    top_flange = _rotate_about_z(top_flange, -90)
    bottom_flange = _rotate_about_z(bottom_flange, -90)

    stiffeners = [
        _rotate_about_z(s, -90) for s in stiffeners
    ]


    return {
        "web": web,
        "top_flange": top_flange,
        "bottom_flange": bottom_flange,
        "stiffeners": stiffeners
    }
