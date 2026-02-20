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
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse



# END STIFFENER SPACING
END_STIFFENER_SPACING = 50.0  # Spacing between end stiffener pairs (mm)


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





def create_shear_stud(base_dia, base_height, top_dia, top_height):
    """Create stepped cylindrical shape"""
    base_radius = base_dia / 2.0
    top_radius = top_dia / 2.0

    # Base cylinder at origin
    base_axis = gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1))
    base_cyl = BRepPrimAPI_MakeCylinder(base_axis, base_radius, base_height).Shape()

    # Top cylinder placed on base
    top_axis = gp_Ax2(gp_Pnt(0, 0, base_height), gp_Dir(0, 0, 1))
    top_cyl = BRepPrimAPI_MakeCylinder(top_axis, top_radius, top_height).Shape()

    # Fuse both
    stepped_shape = BRepAlgoAPI_Fuse(base_cyl, top_cyl).Shape()

    return stepped_shape


def build_plate_girder_geometry(
    *,
    D,                                  # Total depth       
    tw,                                 # Web thickness
    length,                             # Length along Y axis
    T_ft,                               # Top flange thickness
    T_fb,                               # Bottom flange thickness
    B_ft,                               # Top flange width
    B_fb,                               # Bottom flange width
    include_intermediate_stiffeners=True,  # Whether to include intermediate stiffeners
    intermediate_stiffener_spacing=750,    # Space between intermediate stiffeners (mm)
    intermediate_stiffener_thickness=20,   # Intermediate stiffener thickness (mm)
    chamfer_length=40,                     # Triangular chamfer length
    num_end_stiffener_pairs=2,             # Number of end stiffener pairs on each end
    T_es=25,                                # End stiffener thickness (mm)
    intermediate_stiffener_outstand=None,  # Custom outstand for intermediate stiffeners
    end_stiffener_outstand=None,            # Custom outstand for end stiffeners
    include_longitudinal_stiffeners=False, # Whether to include longitudinal stiffeners
    num_longitudinal_stiffeners=1,         # Number of longitudinal stiffeners (1 or 2)
    longitudinal_stiffener_thickness=20,   # Thickness of longitudinal stiffeners (mm)
    longitudinal_stiffener_outstand=None,  # Custom outstand for longitudinal stiffeners
    shear_stud_base_diameter=16,           # Diameter of the shear stud base (mm)
    shear_stud_top_diameter=25,            # Diameter of the shear stud top head (mm)
    shear_stud_base_height=135,            # Height of the shear stud base (mm)
    shear_stud_top_height=15,              # Height of the shear stud top head (mm)
    num_shear_studs_per_section=2,         # Number of shear studs in the transverse direction
    shear_stud_transverse_spacing=100,     # Spacing between shear studs in the transverse direction
    shear_stud_pitch=200                   # Pitch (longitudinal spacing) of shear stud rows
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

    # Stiffeners
    stiffeners = []
    eff_depth = D - T_ft - T_fb
    
    # Calculate default outstand if not provided
    default_stiff_width = (min(B_ft, B_fb) - tw) / 2
    
    int_stiff_width = intermediate_stiffener_outstand if intermediate_stiffener_outstand is not None else default_stiff_width
    end_stiff_width = end_stiffener_outstand if end_stiffener_outstand is not None else default_stiff_width

    # Intermediate stiffeners (only if enabled)
    if include_intermediate_stiffeners:
        num_panels = max(1, int(length // intermediate_stiffener_spacing))

        # Calculate exclusion zone for end stiffeners
        end_stiffener_gap = T_es / 2.0
        end_stiffener_zone = end_stiffener_gap + (num_end_stiffener_pairs - 1) * END_STIFFENER_SPACING + END_STIFFENER_SPACING
        start_y = end_stiffener_zone
        end_y = length - end_stiffener_zone


        for i in range(1, num_panels):
            y = i * intermediate_stiffener_spacing

            if y <= start_y or y >= end_y:
                continue

            stiffeners.append(
                _create_stiffener_plate(
                    position=[ tw / 2, y, 0 ],
                    width=int_stiff_width,
                    height=D,
                    thickness=intermediate_stiffener_thickness,
                    chamfer=chamfer_length,
                    side="right"
                )
            )

            stiffeners.append(
                _create_stiffener_plate(
                    position=[ -tw / 2, y, 0 ],
                    width=int_stiff_width,
                    height=D,
                    thickness=intermediate_stiffener_thickness,
                    chamfer=chamfer_length,
                    side="left"
                )
            )

    # End stiffeners (always present)
    end_stiffener_gap = (T_es / 2.0)

    # Generate positions for the specified number of pairs
    end_positions = []
    
    # Left end stiffeners
    for i in range(num_end_stiffener_pairs):
        y_pos = end_stiffener_gap + i * END_STIFFENER_SPACING
        end_positions.append(y_pos)
    
    # Right end stiffeners
    for i in range(num_end_stiffener_pairs):
        y_pos = length - end_stiffener_gap - i * END_STIFFENER_SPACING
        end_positions.append(y_pos)

    for y in end_positions:
        stiffeners.append(
            _create_stiffener_plate(
                position=[ tw / 2, y, 0 ],
                width=end_stiff_width,
                height=D,
                thickness=T_es,
                chamfer=chamfer_length,
                side="right"
            )
        )

        stiffeners.append(
            _create_stiffener_plate(
                position=[ -tw / 2, y, 0 ],
                width=end_stiff_width,
                height=D,
                thickness=T_es,
                chamfer=chamfer_length,
                side="left"
            )
        )

    # Longitudinal Stiffeners
    if include_longitudinal_stiffeners:
        long_stiff_width = longitudinal_stiffener_outstand if longitudinal_stiffener_outstand is not None else default_stiff_width
        
        # Start after the first end stiffener and end before the last one
        long_stiff_start = T_es
        long_stiff_len = length - 2 * long_stiff_start

        # Calculate vertical positions from the web top (D/2)
        heights = []
        if num_longitudinal_stiffeners == 1:
            # 1/3 height from web top
            heights.append(D / 2 - D / 3)
        elif num_longitudinal_stiffeners == 2:
            # 1/3 and 2/3 height from web top
            heights.append(D / 2 - D / 3)
            heights.append(D / 2 - 2 * D / 3)
            
        for h in heights:
            long_stiff = _make_plate(
                origin=np.array([tw / 2 + long_stiff_width / 2, long_stiff_start, h]),
                length=long_stiff_width,
                width=long_stiff_len,
                thickness=longitudinal_stiffener_thickness,
                u_dir=np.array([0., 0., 1.]), # Thickness along Z
                w_dir=np.array([0., 1., 0.])  # Length along Y
            )
            stiffeners.append(long_stiff)

    # Shear Studs
    shear_studs = []
    if num_shear_studs_per_section > 0 and shear_stud_pitch > 0:
        base_stud = create_shear_stud(shear_stud_base_diameter, shear_stud_base_height, shear_stud_top_diameter, shear_stud_top_height)
        z_stud = D / 2.0 + T_ft  # Place ON TOP of the top flange
        
        # Longitudinal stud placement (Y direction) 
        min_edge = 50.0

        if length > 2 * min_edge:

            # Maximum intervals ensuring edge ≥ 50 mm
            max_intervals = int((length - 2 * min_edge) // shear_stud_pitch)

            # Compute symmetric edge distance
            edge = (length - max_intervals * shear_stud_pitch) / 2.0

            start_y = edge
            num_rows = max_intervals + 1

        else:
            # Very short girder → single centered stud row
            start_y = length / 2.0
            num_rows = 1
            
        # Transverse stud placement (X direction)
        transverse_positions = []
        if num_shear_studs_per_section == 1:
            transverse_positions = [0.0]
        else:
            # Ensure the studs do not exceed the width of the top flange (B_ft)
            min_edge_margin = max(50.0, shear_stud_base_diameter)
            max_total_transverse_width = max(0.0, B_ft - 2 * min_edge_margin)
            
            desired_total_width = (num_shear_studs_per_section - 1) * shear_stud_transverse_spacing
            actual_total_width = min(desired_total_width, max_total_transverse_width)
            
            actual_spacing = actual_total_width / (num_shear_studs_per_section - 1)
            start_x = -actual_total_width / 2.0
            
            for k in range(num_shear_studs_per_section):
                transverse_positions.append(start_x + k * actual_spacing)

        for i in range(num_rows):
            y_pos = start_y + i * shear_stud_pitch
            for x_pos in transverse_positions:
                trsf = gp_Trsf()
                trsf.SetTranslation(gp_Vec(x_pos, y_pos, z_stud))
                stud = BRepBuilderAPI_Transform(base_stud, trsf, True).Shape()
                shear_studs.append(stud)

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

    shear_studs = [
        _rotate_about_z(s, -90) for s in shear_studs
    ]



    return {
        "web": web,
        "top_flange": top_flange,
        "bottom_flange": bottom_flange,
        "stiffeners": stiffeners,
        "supports_tri": supports_tri,
        "supports_cyl": supports_cyl,
        "shear_studs": shear_studs
    }
