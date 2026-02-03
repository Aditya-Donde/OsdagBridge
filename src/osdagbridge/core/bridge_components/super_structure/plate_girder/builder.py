"""
Plate Girder Geometry Builder (Geometry Only)

- NO welds
- NO viewer
- NO fusion
- Returns raw TopoDS_Shapes for Bridge CAD pipeline
"""

import math
import numpy as np

from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Trsf, gp_Ax3, gp_Dir, gp_Ax2
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism, BRepPrimAPI_MakeCylinder
from OCC.Core.BRepBuilderAPI import (
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeWire,
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_Transform
)


# Helper geometry utilities (

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




def build_plate_girder_geometry(
    *,
    D,                                  # Total depth       
    tw,                                 # Web thickness
    length,                             # Length along Y axis
    T_ft,                               # Top flange thickness
    T_fb,                               # Bottom flange thickness
    B_ft,                               # Top flange width
    B_fb,                               # Bottom flange width
    stiffener_spacing,                  # Space between each stiffener plate
    T_is,                               # Stiffener thickness
    chamfer_length,                     # Triangular chamfer length
    include_end_stiffeners=False,       # Whether to include end stiffeners
    T_es=None                           # End stiffener thickness
):
    """
    Geometry-only Plate Girder builder for Osdag Bridge.
    """

    # Directions 
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

    start_y = 0.0
    end_y = length

    if include_end_stiffeners:
        end_stiffener_gap = T_es / 2.0
        start_y = end_stiffener_gap + 50.0
        end_y = length - (end_stiffener_gap + 50.0)


    for i in range(1, num_panels):
        y = i * stiffener_spacing

        if y <= start_y or y >= end_y:
            continue

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

    # End stiffeners 
    if include_end_stiffeners:
        if T_es is None:
            T_es = T_is

        end_stiffener_gap = (T_es / 2.0)

        end_positions = [
            end_stiffener_gap,
            end_stiffener_gap + 50.0,
            length - (end_stiffener_gap + 50.0),
            length - end_stiffener_gap,
        ]

        for y in end_positions:
            stiffeners.append(
                _create_stiffener_plate(
                    position=[ tw / 2, y, 0 ],
                    width=stiff_width,
                    height=D,
                    thickness=T_es,
                    chamfer=chamfer_length,
                    side="right"
                )
            )

            stiffeners.append(
                _create_stiffener_plate(
                    position=[ -tw / 2, y, 0 ],
                    width=stiff_width,
                    height=D,
                    thickness=T_es,
                    chamfer=chamfer_length,
                    side="left"
                )
            )

    # SUPPORTS 

    supports_tri = []
    supports_cyl = []

    # Contact level (bottom of bottom flange)
    z_contact = -(D / 2.0 + T_fb)

    # Support width spans flange width
    support_width = max(B_ft, B_fb)

    
    base_dim = min(0.10 * length, 0.75 * D)

    # Triangle proportions
    h_supp = base_dim / 1.5
    w_supp = base_dim / 2.0

    # Cylinder radius
    r_cyl = h_supp / 2.0

    # TRIANGULAR SUPPORT (LEFT)

    y_apex = w_supp
    z_apex = z_contact
    x_face = -support_width / 2.0

    p1 = gp_Pnt(x_face, y_apex, z_apex)
    p2 = gp_Pnt(x_face, y_apex - w_supp, z_apex - h_supp)
    p3 = gp_Pnt(x_face, y_apex + w_supp, z_apex - h_supp)

    e1 = BRepBuilderAPI_MakeEdge(p1, p2).Edge()
    e2 = BRepBuilderAPI_MakeEdge(p2, p3).Edge()
    e3 = BRepBuilderAPI_MakeEdge(p3, p1).Edge()

    wire = BRepBuilderAPI_MakeWire()
    wire.Add(e1)
    wire.Add(e2)
    wire.Add(e3)

    face = BRepBuilderAPI_MakeFace(wire.Wire()).Face()

    tri_support = BRepPrimAPI_MakePrism(
        face,
        gp_Vec(support_width, 0, 0)
    ).Shape()

    supports_tri.append(tri_support)

    # CYLINDRICAL SUPPORT (RIGHT)

    y_cyl = length - r_cyl
    z_cyl_center = z_contact - r_cyl

    pt_cyl = gp_Pnt(-support_width / 2.0, y_cyl, z_cyl_center)
    axis = gp_Ax2(pt_cyl, gp_Dir(1, 0, 0))

    cyl_support = BRepPrimAPI_MakeCylinder(
        axis,
        r_cyl,
        support_width
    ).Shape()

    supports_cyl.append(cyl_support)



    web = _rotate_about_z(web, -90)
    top_flange = _rotate_about_z(top_flange, -90)
    bottom_flange = _rotate_about_z(bottom_flange, -90)

    stiffeners = [
        _rotate_about_z(s, -90) for s in stiffeners
    ]

    supports_tri = [
        _rotate_about_z(s, -90) for s in supports_tri
    ]

    supports_cyl = [
        _rotate_about_z(s, -90) for s in supports_cyl
    ]



    return {
        "web": web,
        "top_flange": top_flange,
        "bottom_flange": bottom_flange,
        "stiffeners": stiffeners,
        "supports_tri": supports_tri,
        "supports_cyl": supports_cyl
    }
