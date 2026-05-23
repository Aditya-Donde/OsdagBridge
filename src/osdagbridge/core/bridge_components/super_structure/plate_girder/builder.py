"""
Plate Girder Geometry Builder (Geometry Only)

- NO welds
- NO viewer
- NO fusion
- Returns raw TopoDS_Shapes for Bridge CAD pipeline
"""

import math
import numpy as np
from dataclasses import dataclass

from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Trsf, gp_Ax3, gp_Dir, gp_Ax2
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism, BRepPrimAPI_MakeCylinder
from OCC.Core.BRepBuilderAPI import (
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeWire,
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_Transform
)
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse

@dataclass
class GirderSegment:
    length: float
    D: float
    tw: float
    T_ft: float
    T_fb: float
    B_ft: float
    B_fb: float



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
    segments=None,                      # Optional list of GirderSegment
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
    shear_stud_pitch=200,                   # Pitch (longitudinal spacing) of shear stud rows
    right_guided=False                     # If True: add tansverse constraints plate at the right and left end (for guided support conditions)
):
    """
    Geometry-only Plate Girder builder for Osdag Bridge.
    """

    # Directions 
    u_dir = np.array([0., 0., 1.])
    w_dir = np.array([0., 1., 0.])

    if segments is None:
        segments = [
            GirderSegment(
                length=length,
                D=D,
                tw=tw,
                T_ft=T_ft,
                T_fb=T_fb,
                B_ft=B_ft,
                B_fb=B_fb
            )
        ]

    # Reference top of girder (used to keep top flanges flush)
    Z_top = D / 2 + T_ft

    web_shapes = []
    top_flange_shapes = []
    bottom_flange_shapes = []

    current_y = 0.0
    for seg in segments:
        seg_z_web_center = Z_top - seg.T_ft - seg.D / 2
        
        # Web plate
        seg_web = _make_plate(
            origin=np.array([0., current_y, seg_z_web_center]),
            length=seg.tw,
            width=seg.length,
            thickness=seg.D,
            u_dir=u_dir,
            w_dir=w_dir
        )
        web_shapes.append(seg_web)

        # Top flange
        seg_tf_center = Z_top - seg.T_ft / 2
        seg_top_flange = _make_plate(
            origin=np.array([0., current_y, seg_tf_center]),
            length=seg.B_ft,
            width=seg.length,
            thickness=seg.T_ft,
            u_dir=u_dir,
            w_dir=w_dir
        )
        top_flange_shapes.append(seg_top_flange)

        # Bottom flange
        seg_bf_center = Z_top - seg.T_ft - seg.D - seg.T_fb / 2
        seg_bottom_flange = _make_plate(
            origin=np.array([0., current_y, seg_bf_center]),
            length=seg.B_fb,
            width=seg.length,
            thickness=seg.T_fb,
            u_dir=u_dir,
            w_dir=w_dir
        )
        bottom_flange_shapes.append(seg_bottom_flange)

        current_y += seg.length

    # Stiffeners
    stiffeners = []
    
    def get_segment_at(y):
        curr = 0.0
        for s in segments:
            if y <= curr + s.length + 1e-6:
                return s, Z_top - s.T_ft - s.D / 2
            curr += s.length
        return segments[-1], Z_top - segments[-1].T_ft - segments[-1].D / 2
    
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

            seg, seg_z_center = get_segment_at(y)

            stiffeners.append(
                _create_stiffener_plate(
                    position=[ seg.tw / 2, y, seg_z_center ],
                    width=int_stiff_width,
                    height=seg.D,
                    thickness=intermediate_stiffener_thickness,
                    chamfer=chamfer_length,
                    side="right"
                )
            )

            stiffeners.append(
                _create_stiffener_plate(
                    position=[ -seg.tw / 2, y, seg_z_center ],
                    width=int_stiff_width,
                    height=seg.D,
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
        seg, seg_z_center = get_segment_at(y)
        stiffeners.append(
            _create_stiffener_plate(
                position=[ seg.tw / 2, y, seg_z_center ],
                width=end_stiff_width,
                height=seg.D,
                thickness=T_es,
                chamfer=chamfer_length,
                side="right"
            )
        )

        stiffeners.append(
            _create_stiffener_plate(
                position=[ -seg.tw / 2, y, seg_z_center ],
                width=end_stiff_width,
                height=seg.D,
                thickness=T_es,
                chamfer=chamfer_length,
                side="left"
            )
        )

    # Longitudinal Stiffeners
    if include_longitudinal_stiffeners:
        long_stiff_width = longitudinal_stiffener_outstand if longitudinal_stiffener_outstand is not None else default_stiff_width
        long_stiff_start = T_es

        # We need to build longitudinal stiffeners segment by segment since their height/offset might change based on D
        curr_y = 0.0
        for seg in segments:
            # Calculate segment-specific start and length, considering exclusion zones
            seg_start_y = max(curr_y, long_stiff_start)
            seg_end_y = min(curr_y + seg.length, length - T_es)
            seg_len = seg_end_y - seg_start_y
            
            if seg_len > 0:
                seg_z_web_center = Z_top - seg.T_ft - seg.D / 2
                
                heights = []
                if num_longitudinal_stiffeners == 1:
                    heights.append(seg_z_web_center + seg.D / 2 - seg.D / 3)
                elif num_longitudinal_stiffeners == 2:
                    heights.append(seg_z_web_center + seg.D / 2 - seg.D / 3)
                    heights.append(seg_z_web_center + seg.D / 2 - 2 * seg.D / 3)
                    
                for h in heights:
                    long_stiff = _make_plate(
                        origin=np.array([seg.tw / 2 + long_stiff_width / 2, seg_start_y, h]),
                        length=long_stiff_width,
                        width=seg_len,
                        thickness=longitudinal_stiffener_thickness,
                        u_dir=np.array([0., 0., 1.]),
                        w_dir=np.array([0., 1., 0.])
                    )
                    stiffeners.append(long_stiff)
            
            curr_y += seg.length

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

    # SUPPORTS - wireframe rectangular frames, border only, no fill.
    # supports_tri = all constraints frames (accent colour in viewer)
    # supports_cyl : always empty – cylinders/pins removed
    #
    # Coordinate note (builder space, before -90° Z-rotation):
    #   Builder X  = transverse   →  World Y  after rotation
    #   Builder Y  = bridge span  →  World X  after rotation
    #   Builder Z  = vertical     →  World Z  (unchanged)
    #
    # Rectangle layout per support end:
    #   Vertical bar   (Y restraint, portrait)  : builder X-Z plane at y_end
    #   Wide horiz bar (transverse restraint)   : same builder X-Z plane, landscape
    #   Long horiz bar (longitudinal restraint) : builder Y-Z plane at x=0, landscape
    #
    # Present at:
    #   Left  (pin)        : vertical + wide-horiz(only if right_guided) + long-horiz
    #   Right guided roller: vertical + wide-horiz
    #   Right free roller  : vertical only

    supports_tri = []
    supports_cyl = []

    # Calculate actual contact levels from the end segments
    Z_top = D / 2 + T_ft
    seg_left = segments[0]
    seg_right = segments[-1]
    
    # Left support Z level
    z_contact_left = Z_top - seg_left.T_ft - seg_left.D - seg_left.T_fb

    # Right support Z level
    z_contact_right = Z_top - seg_right.T_ft - seg_right.D - seg_right.T_fb

    # Support width spans flange width
    support_width_left = max(seg_left.B_ft, seg_left.B_fb)
    support_width_right = max(seg_right.B_ft, seg_right.B_fb)
    
    

    base_dim = min(0.10 * length, 0.75 * D)
    h_supp   = base_dim / 1.5                       # full support height -> tall dimension of vertical bar
    w_supp   = base_dim / 2.0                       # used for longitudinal bar depth and transverse bar width
    h_tall   = h_supp                               # vertical bar height
    h_short  = h_supp * 0.35                        # horizontal bar height
    w_narrow = h_supp * 0.25                        # vertical bar width

    def _rect_wire(p0, p1, p2, p3):
        """Closed rectangular wireframe through four corners (border only, no fill)."""
        return BRepBuilderAPI_MakeWire(
            BRepBuilderAPI_MakeEdge(p0, p1).Edge(),
            BRepBuilderAPI_MakeEdge(p1, p2).Edge(),
            BRepBuilderAPI_MakeEdge(p2, p3).Edge(),
            BRepBuilderAPI_MakeEdge(p3, p0).Edge(),
        ).Wire()
    
    '''
    # ── LEFT (PIN) SUPPORT at builder y = 0 ──────────────────────────────────
    z_L  = z_contact_left
    sw_L = support_width_left

    # 1. Vertical bar – Z restraint (portrait, builder X-Z plane)
    supports_tri.append(_rect_wire(
        gp_Pnt(-w_narrow/2, 0, z_L),
        gp_Pnt( w_narrow/2, 0, z_L),
        gp_Pnt( w_narrow/2, 0, z_L - h_tall),
        gp_Pnt(-w_narrow/2, 0, z_L - h_tall),
    ))

    # 2. Wide horizontal bar – transverse restraint (guided girders only, same builder X-Z plane)
    #if right_guided:
    supports_tri.append(_rect_wire(
        gp_Pnt(-sw_L/2, 0, z_L),
        gp_Pnt( sw_L/2, 0, z_L),
        gp_Pnt( sw_L/2, 0, z_L - h_short),
        gp_Pnt(-sw_L/2, 0, z_L - h_short),
    ))

    # 3. Longitudinal bar – span-direction restraint (landscape, builder Y-Z plane at x=0)
    supports_tri.append(_rect_wire(
        gp_Pnt(0, 0,       z_L),
        gp_Pnt(0, w_supp,  z_L),
        gp_Pnt(0, w_supp,  z_L - h_short),
        gp_Pnt(0, 0,       z_L - h_short),
    ))

    # ── RIGHT (ROLLER) SUPPORT at builder y = length ──────────────────────────
    z_R  = z_contact_right
    sw_R = support_width_right

    # 1. Vertical bar – Z restraint (always)
    supports_tri.append(_rect_wire(
        gp_Pnt(-w_narrow/2, length, z_R),
        gp_Pnt( w_narrow/2, length, z_R),
        gp_Pnt( w_narrow/2, length, z_R - h_tall),
        gp_Pnt(-w_narrow/2, length, z_R - h_tall),
    ))

    # 2. Wide horizontal bar – transverse restraint (guided rollers only)
    #if right_guided:
    supports_tri.append(_rect_wire(
        gp_Pnt(-sw_R/2, length, z_R),
        gp_Pnt( sw_R/2, length, z_R),
        gp_Pnt( sw_R/2, length, z_R - h_short),
        gp_Pnt(-sw_R/2, length, z_R - h_short),
    ))

    # 3. Longitudinal bar – span-direction restraint (landscape, builder Y-Z plane at x=0)
    supports_tri.append(_rect_wire(
        gp_Pnt(0, length,           z_R),
        gp_Pnt(0, length - w_supp,  z_R),
        gp_Pnt(0, length - w_supp,  z_R - h_short),
        gp_Pnt(0, length,           z_R - h_short),
    ))
    '''

    web_shapes = [ _rotate_about_z(w, -90) for w in web_shapes ]
    top_flange_shapes = [ _rotate_about_z(tf, -90) for tf in top_flange_shapes ]
    bottom_flange_shapes = [ _rotate_about_z(bf, -90) for bf in bottom_flange_shapes ]

    stiffeners = [
        _rotate_about_z(s, -90) for s in stiffeners
    ]

    '''supports_tri = [
        _rotate_about_z(s, -90) for s in supports_tri
    ]'''

    supports_cyl = [
        _rotate_about_z(s, -90) for s in supports_cyl
    ]

    shear_studs = [
        _rotate_about_z(s, -90) for s in shear_studs
    ]
    

    supports_vertical = []
    supports_wide_horiz = []
    supports_long_horiz = []

    # ── LEFT (PIN) SUPPORT at builder y = 0 ──────────────────────────────────
    z_L  = z_contact_left
    sw_L = support_width_left

    # 1. Vertical bar
    supports_vertical.append(_rect_wire(
        gp_Pnt(-w_narrow/2, 0, z_L),
        gp_Pnt( w_narrow/2, 0, z_L),
        gp_Pnt( w_narrow/2, 0, z_L - h_tall),
        gp_Pnt(-w_narrow/2, 0, z_L - h_tall),
    ))

    # 2. Wide horizontal bar
    if right_guided:
        supports_wide_horiz.append(_rect_wire(
            gp_Pnt(-sw_L/2, 0, z_L),
            gp_Pnt( sw_L/2, 0, z_L),
            gp_Pnt( sw_L/2, 0, z_L - h_short),
            gp_Pnt(-sw_L/2, 0, z_L - h_short),
        ))

    # 3. Longitudinal bar
    supports_long_horiz.append(_rect_wire(
        gp_Pnt(0, 0,      z_L),
        gp_Pnt(0, w_supp, z_L),
        gp_Pnt(0, w_supp, z_L - h_short),
        gp_Pnt(0, 0,      z_L - h_short),
    ))

    # ── RIGHT (ROLLER) SUPPORT at builder y = length ─────────────────────────
    z_R  = z_contact_right
    sw_R = support_width_right

    # 1. Vertical bar
    supports_vertical.append(_rect_wire(
        gp_Pnt(-w_narrow/2, length, z_R),
        gp_Pnt( w_narrow/2, length, z_R),
        gp_Pnt( w_narrow/2, length, z_R - h_tall),
        gp_Pnt(-w_narrow/2, length, z_R - h_tall),
    ))

    # 2. Wide horizontal bar
    if right_guided:
        supports_wide_horiz.append(_rect_wire(
            gp_Pnt(-sw_R/2, length, z_R),
            gp_Pnt( sw_R/2, length, z_R),
            gp_Pnt( sw_R/2, length, z_R - h_short),
            gp_Pnt(-sw_R/2, length, z_R - h_short),
        ))

    # Rotate all three
    supports_vertical   = [_rotate_about_z(s, -90) for s in supports_vertical]
    supports_wide_horiz = [_rotate_about_z(s, -90) for s in supports_wide_horiz]
    supports_long_horiz = [_rotate_about_z(s, -90) for s in supports_long_horiz]


    return {
        "web": web_shapes,
        "top_flange": top_flange_shapes,
        "bottom_flange": bottom_flange_shapes,
        "stiffeners": stiffeners,
        "supports_tri": supports_vertical + supports_wide_horiz + supports_long_horiz,  # backward compat
        "supports_vertical": supports_vertical,
        "supports_wide_horiz": supports_wide_horiz,
        "supports_long_horiz": supports_long_horiz,
        "supports_cyl": supports_cyl,
        "shear_studs": shear_studs
    }
