"""

- Contains geometry creation
- Contains placement logic
- Contains footpath-based positioning logic
"""

from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Trsf, gp_Dir, gp_Ax2, gp_Ax1,gp_Pnt2d, gp_Ax2d, gp_Dir2d
from OCC.Core.BRepBuilderAPI import (
    BRepBuilderAPI_MakePolygon,
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_Transform,
    BRepBuilderAPI_MakeWire,
    BRepBuilderAPI_MakeEdge
)
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCC.Core.GCE2d import GCE2d_MakeArcOfCircle
from OCC.Core.Geom import Geom_Plane
from OCC.Core.gp import gp_Pln
import numpy as np
import math


# Utility transforms

def translate(shape, x=0, y=0, z=0):
    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(x, y, z))
    return BRepBuilderAPI_Transform(shape, trsf, True).Shape()


def mirror_y(shape):
    if shape.IsNull():
        return shape

    trsf = gp_Trsf()
    trsf.SetMirror(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(0, 1, 0)))

    transformer = BRepBuilderAPI_Transform(trsf)
    transformer.Perform(shape, True)
    return transformer.Shape()




def create_rigid_rcc_crash_barrier(
    *,
    length,
    design_dict,
    side="LEFT",
    skew_angle=0
):
    

    # READ IRC DESIGN DATA
    H_total = design_dict.get("crash_barrier_height")
    W_base = design_dict.get("crash_barrier_width")
    W_top = design_dict.get("crash_barrier_top_notch")
    
    H_base = design_dict.get("crash_barrier_base_notch")
    H_mid = design_dict.get("crash_barrier_middle_length")
    wearing = design_dict.get("wearing_course_thickness")

 
   
    H_transition = 250  # Height of transition section (from IRC figure)
    W_at_transition = W_base - 200  # Approximately 250mm at transition level
    
    # Z LEVELS (heights) 
    z0 = 0.0                          # Bottom
    z1 = H_base + wearing             
    z2 = z1 + H_transition            # End of transition slope (150 + 250 = 400)
    z3 = H_total                       # Top (1100)

    #  Y LEVELS (half-widths from centerline) 
    y_base = W_base / 2.0             # 225mm from center
    y_top = W_top / 2.0               # 87.5mm from center
    y_trans = W_at_transition / 2.0   # 125mm from center at transition

    # SKEW LOGIC
    skew_rad = math.radians(skew_angle)
    def get_skew_x(y):
        return y * math.tan(skew_rad)

    #  PROFILE POINTS (YZ PLANE -> SKEWED XY PLANE)
    # Right side is outer edge (road side), Left is inner edge
    
    # Points traced clockwise from bottom-right:
    p1 = gp_Pnt(get_skew_x(y_base), y_base, z0)       # Bottom right
    p2 = gp_Pnt(get_skew_x(-y_base), -y_base, z0)      # Bottom left
    
    p3 = gp_Pnt(get_skew_x(-y_base), -y_base, z1)      # Left side - top of base vertical
    p4 = gp_Pnt(get_skew_x(-y_top), -y_top, z3)       # Left side - top corner (straight slope from base to top)
    
    p5 = gp_Pnt(get_skew_x(y_top), y_top, z3)        # Right side - top corner
    p6 = gp_Pnt(get_skew_x(y_trans), y_trans, z2)      # Right side - end of main slope / start of transition
    p7 = gp_Pnt(get_skew_x(y_base), y_base, z1)       # Right side - top of base vertical

    # Build face 
    poly = BRepBuilderAPI_MakePolygon()
    for p in (p1, p2, p3, p4, p5, p6, p7):
        poly.Add(p)
    poly.Close()

    face = BRepBuilderAPI_MakeFace(poly.Wire()).Face()
    # Extrude along X (length)
    solid = BRepPrimAPI_MakePrism(face, gp_Vec(length, 0, 0)).Shape()

    #  MIRROR FOR RIGHT SIDE 
    if side.upper() == "RIGHT":
        solid = mirror_y(solid)

    return solid



def create_semi_rigid_metallic_barrier(
    *,
    length,
    design_dict,
    side="LEFT",
    skew_angle=0
):
    """
    Creates semi-rigid metallic crash barrier (IRC Fig 4).
    Geometry: RCC kerb base + steel post channel + spacer channel + W-beam(s).
    """

    import numpy as np
    import math

    # READ DESIGN DATA
    kerb_height = design_dict.get("kerb_height", 100)
    kerb_top_width = design_dict.get("kerb_top_width", 500)
    kerb_bottom_width = design_dict.get("kerb_bottom_width", 550)

    post_height = design_dict.get("post_height", 950)
    post_spacing = design_dict.get("post_spacing", 1000)
    spacer_height = design_dict.get("spacer_height", 330)

    number_of_w_beams = design_dict.get("number_of_w_beams", 1)



    # SKEW LOGIC
    skew_rad = math.radians(skew_angle)
    def get_skew_x(y):
        return y * math.tan(skew_rad)

    # RCC KERB
    z0 = 0.0
    z1 = kerb_height

    y_bottom_l = -kerb_bottom_width / 2.0
    y_bottom_r = kerb_bottom_width / 2.0
    y_top_l = -kerb_top_width / 2.0
    y_top_r = kerb_top_width / 2.0

    p1 = gp_Pnt(get_skew_x(y_bottom_l), y_bottom_l, z0)
    p2 = gp_Pnt(get_skew_x(y_bottom_r), y_bottom_r, z0)
    p3 = gp_Pnt(get_skew_x(y_top_r), y_top_r, z1)
    p4 = gp_Pnt(get_skew_x(y_top_l), y_top_l, z1)

    kerb_poly = BRepBuilderAPI_MakePolygon()
    for p in (p1, p2, p3, p4):
        kerb_poly.Add(p)
    kerb_poly.Close()

    kerb_face = BRepBuilderAPI_MakeFace(kerb_poly.Wire()).Face()
    kerb_solid = BRepPrimAPI_MakePrism(
        kerb_face, gp_Vec(length, 0, 0)
    ).Shape()

    # POSTS (ISMC 150)
    post_depth = design_dict.get("post_depth", 100)  # Along X (Bridge Length)
    post_width = design_dict.get("post_width", 150)   # Along Y (Transverse)
    post_web_thk = design_dict.get("post_web_thickness", 5.0)
    post_flange_thk = design_dict.get("post_flange_thickness", 7.8)
    post_offset_from_edge = design_dict.get("post_offset_from_edge", 75) # From outer edge

    # Calculate Post Y (Center of Post)
    post_y_center = (
        -kerb_top_width / 2.0 
        + post_offset_from_edge 
        + post_width / 2.0
    )

    # SKEW ADJUSTMENT FOR POSTS/SPACERS
    # Use absolute skew to ensure symmetric offsets for left/right alignment.
    # We use the maximum possible kerb shift to ensure all parts stay inside.
    skew_rad_abs = math.radians(abs(skew_angle))
    safe_skew_shift = (kerb_bottom_width / 2.0) * math.tan(skew_rad_abs)
    
    # Added end offset (margin) to stay well within deck
    end_offset = 150.0  
    total_start_offset = safe_skew_shift + end_offset
    
    start_x = total_start_offset + post_web_thk / 2.0
    end_x = length - total_start_offset - (post_depth - post_web_thk / 2.0)
    
    post_range = end_x - start_x
    if post_range < 0:
        post_range = 0
        
    num_posts = int(length / post_spacing) + 1
    if num_posts < 2:
        num_posts = 2
        
    actual_spacing = post_range / (num_posts - 1) if num_posts > 1 else 0

    posts_combined = None

    def create_vertical_channel(h, d, w, tw, tf):
        # Creates a C-channel prism along Z.
        # d is along X, w is along Y.
        x_web_back = -tw / 2.0
        x_web_front = tw / 2.0
        x_flange_tip = d - tw / 2.0
        y_left = -w / 2.0
        y_right = w / 2.0

        pts = [
            gp_Pnt(x_flange_tip, y_left, 0),
            gp_Pnt(x_web_back, y_left, 0),
            gp_Pnt(x_web_back, y_right, 0),
            gp_Pnt(x_flange_tip, y_right, 0),
            gp_Pnt(x_flange_tip, y_right - tf, 0),
            gp_Pnt(x_web_front, y_right - tf, 0),
            gp_Pnt(x_web_front, y_left + tf, 0),
            gp_Pnt(x_flange_tip, y_left + tf, 0),
        ]
        poly = BRepBuilderAPI_MakePolygon()
        for p in pts:
            poly.Add(p)
        poly.Close()
        face = BRepBuilderAPI_MakeFace(poly.Wire()).Face()
        return BRepPrimAPI_MakePrism(face, gp_Vec(0, 0, h)).Shape()

    # LEFT SIDE LOGIC (Default)
    # Post is on the Left (Outer) side.
    # Spacer is to the Right of Post.
    # Beam is to the Right of Spacer.
    

    for i in range(num_posts):
        x_pos = start_x + (i * actual_spacing)

        post_solid = create_vertical_channel(
            post_height, post_depth,
            post_width, post_web_thk, post_flange_thk
        )

        post_solid = translate(
            post_solid,
            x=x_pos,
            y=post_y_center,
            z=kerb_height
        )

        posts_combined = (
            post_solid if posts_combined is None
            else BRepAlgoAPI_Fuse(posts_combined, post_solid).Shape()
        )

    spacer_depth = design_dict.get("spacer_depth", 150)
    spacer_width = design_dict.get("spacer_width", 200)
    spacer_web_thk = design_dict.get("spacer_web_thickness", 5.0)
    spacer_flange_thk = design_dict.get("spacer_flange_thickness", 7.8)
    
    spacers_combined = None

    # W-BEAM 
    # Corrected Geometry: Vertical orientation (W-profile in Y-Z plane)
    
    W_BEAM_HEIGHT = spacer_height  # Aligned with spacer height as requested
    W_BEAM_DEPTH = 83.0    
    W_BEAM_THICKNESS = design_dict.get("w_beam_thickness", 3.0)

    sigma = W_BEAM_HEIGHT / 10.0
    mu1 = W_BEAM_HEIGHT * 0.25
    mu2 = W_BEAM_HEIGHT * 0.75
    amp = W_BEAM_DEPTH * 1.5
    
    from OCC.Core.GeomAPI import GeomAPI_PointsToBSpline
    from OCC.Core.TColgp import TColgp_Array1OfPnt
    from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeWire
    from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge

    def make_w_beam_face():
        points = 40
        zs = np.linspace(0, W_BEAM_HEIGHT, points)

        # OUTER CURVE 
        outer_pts = TColgp_Array1OfPnt(1, points)
        for i, z in enumerate(zs, start=1):
            y_wave = (
                amp * math.exp(-((z - mu1) ** 2) / (2 * sigma ** 2)) +
                amp * math.exp(-((z - mu2) ** 2) / (2 * sigma ** 2))
            )
            # Offset X by y_wave * tan(skew)
            outer_pts.SetValue(i, gp_Pnt(get_skew_x(y_wave), y_wave, z))
        
        y_top_outer = y_wave
        y_bottom_outer = (
            amp * math.exp(-((zs[0] - mu1) ** 2) / (2 * sigma ** 2)) +
            amp * math.exp(-((zs[0] - mu2) ** 2) / (2 * sigma ** 2))
        )

        outer_curve = GeomAPI_PointsToBSpline(outer_pts).Curve()

        # INNER CURVE (OFFSET) 
        inner_pts = TColgp_Array1OfPnt(1, points)
        for i, z in enumerate(zs, start=1):
            y_wave_inner = (
                amp * math.exp(-((z - mu1) ** 2) / (2 * sigma ** 2)) +
                amp * math.exp(-((z - mu2) ** 2) / (2 * sigma ** 2))
            ) - W_BEAM_THICKNESS
            # Offset X by y_wave_inner * tan(skew)
            inner_pts.SetValue(i, gp_Pnt(get_skew_x(y_wave_inner), y_wave_inner, z))
        
        y_top_inner = y_wave_inner
        y_bottom_inner = (
            amp * math.exp(-((zs[0] - mu1) ** 2) / (2 * sigma ** 2)) +
            amp * math.exp(-((zs[0] - mu2) ** 2) / (2 * sigma ** 2))
        ) - W_BEAM_THICKNESS

        inner_curve = GeomAPI_PointsToBSpline(inner_pts).Curve()

        # COMBINE INTO CLOSED WIRE 
        wire = BRepBuilderAPI_MakeWire()
        wire.Add(BRepBuilderAPI_MakeEdge(outer_curve).Edge())
        wire.Add(BRepBuilderAPI_MakeEdge(
            gp_Pnt(get_skew_x(y_top_outer), y_top_outer, W_BEAM_HEIGHT),
            gp_Pnt(get_skew_x(y_top_inner), y_top_inner, W_BEAM_HEIGHT)
        ).Edge())
        wire.Add(BRepBuilderAPI_MakeEdge(inner_curve).Edge())
        wire.Add(BRepBuilderAPI_MakeEdge(
            gp_Pnt(get_skew_x(y_bottom_inner), y_bottom_inner, 0.0),
            gp_Pnt(get_skew_x(y_bottom_outer), y_bottom_outer, 0.0)
        ).Edge())

        return BRepBuilderAPI_MakeFace(wire.Wire()).Face()

    beams_combined = None

    if number_of_w_beams == 1:
        # Top of beam/spacer aligns with post top
        # Center = post_height - height / 2.0
        beam_center_heights = [post_height - spacer_height / 2.0]
    else:
        # Upper beam/spacer starts at post top
        h_upper = post_height - spacer_height / 2.0
        # Lower beam/spacer comes after 145mm gap
        # Lower Top = Upper Bottom - 145 = (h_upper - spacer_height/2) - 145
        # Lower Center = Lower Top - spacer_height/2 = h_upper - spacer_height - 145
        h_lower = h_upper - spacer_height - 145
        beam_center_heights = [h_lower, h_upper]

    for h_center in beam_center_heights: # Take min of required locally
        if beams_combined is not None and number_of_w_beams == 1: break 
        
        # beam_z is bottom of the beam
        beam_z = kerb_height + h_center - W_BEAM_HEIGHT / 2.0
        
        # SPACER GENERATION (Per Beam)
        spacer_z = kerb_height + h_center - spacer_height / 2.0
        spacer_y_center = post_y_center + post_width / 2.0 + spacer_width / 2.0

        # Spacers (one per post)
        for i in range(num_posts):
            x_pos = start_x + (i * actual_spacing)

            spacer_solid = create_vertical_channel(
                spacer_height, spacer_depth,
                spacer_width, spacer_web_thk, spacer_flange_thk
            )

            spacer_solid = translate(
                spacer_solid,
                x=x_pos,
                y=spacer_y_center,
                z=spacer_z
            )

            spacers_combined = (
                spacer_solid if spacers_combined is None
                else BRepAlgoAPI_Fuse(spacers_combined, spacer_solid).Shape()
            )

        # BEAM GENERATION
        beam_y_pos = spacer_y_center + spacer_width / 2.0
        
        beam_face = make_w_beam_face()
        
        beam_solid = BRepPrimAPI_MakePrism(
            beam_face, gp_Vec(length, 0, 0)
        ).Shape()

        beam_solid = translate(
            beam_solid,
            y=beam_y_pos,
            z=beam_z
        )

        beams_combined = (
            beam_solid if beams_combined is None
            else BRepAlgoAPI_Fuse(beams_combined, beam_solid).Shape()
        )

    # IF RIGHT SIDE: MIRROR
    res = {
        "kerb": kerb_solid,
        "posts": posts_combined,
        "spacers": spacers_combined,
        "w_beams": beams_combined
    }

    if side.upper() == "RIGHT":
        res = {k: mirror_y(v) for k, v in res.items() if v}

    return res




def calculate_deck_width(
    footpath_config,
    carriageway_width,
    crash_barrier_base_width,
    footpath_width,
    railing_width
):
    if footpath_config == "NONE":
        return carriageway_width + 2 * crash_barrier_base_width

    elif footpath_config in ("LEFT", "RIGHT"):
        return (
            carriageway_width
            + 2 * crash_barrier_base_width
            + footpath_width
            + railing_width
        )

    elif footpath_config == "BOTH":
        return (
            carriageway_width
            + 2 * crash_barrier_base_width
            + 2 * footpath_width
            + 2 * railing_width
        )

    else:
        raise ValueError(f"Invalid footpath_config: {footpath_config}")


def calculate_carriageway_offset(
    footpath_config,
    footpath_width,
    railing_width
):
    if footpath_config in ("NONE", "BOTH"):
        return 0.0

    elif footpath_config == "LEFT":
        return (footpath_width + railing_width ) / 2.0

    elif footpath_config == "RIGHT":
        return -(footpath_width + railing_width) / 2.0

    else:
        raise ValueError(f"Invalid footpath_config: {footpath_config}")



def build_crash_barriers(
    *,
    span_length_L,
    deck_top_z,
    footpath_config,
    carriageway_width,
    footpath_width,
    railing_width,
    design_dict,
    barrier_type="Rigid",
    skew_angle=0
):
    """
    Returns list of crash barrier shapes.
    
    Parameters
    ----------
    barrier_type : str
        Type of crash barrier: "Rigid" (RCC) or "Semi-Rigid" (metallic W-beam)
    """

    # READ IRC DESIGN DATA 
    # For rigid barriers, use crash_barrier dimensions
    # For semi-rigid, use kerb dimensions
    if barrier_type == "Rigid":
        crash_barrier_height = design_dict.get("crash_barrier_height")
        crash_barrier_width = design_dict.get("crash_barrier_top_notch")
        crash_barrier_base_width = design_dict.get("crash_barrier_width")
        
    else:
        # Semi-rigid uses kerb as base
        crash_barrier_height = design_dict.get("crash_barrier_height", 1050)
        crash_barrier_base_width = design_dict.get("kerb_bottom_width", 550)
        crash_barrier_width = design_dict.get("kerb_top_width", 500)

    crash_barriers = []

    total_deck_width = calculate_deck_width(
        footpath_config,
        carriageway_width,
        crash_barrier_base_width,
        footpath_width,
        railing_width
    )

    deck_half = total_deck_width / 2.0

    carriageway_offset = calculate_carriageway_offset(
        footpath_config,
        footpath_width,
        railing_width
    )

    cw_half = carriageway_width / 2.0
    cw_left = carriageway_offset - cw_half
    cw_right = carriageway_offset + cw_half

    # NONE
    if footpath_config == "NONE":

        y_r = deck_half - crash_barrier_base_width/2
        y_l = -deck_half + crash_barrier_base_width/2

    # LEFT footpath
    elif footpath_config == "LEFT":

        y_r = deck_half - crash_barrier_base_width / 2.0 
        y_l = cw_left + crash_barrier_base_width / 2.0

    # RIGHT footpath
    elif footpath_config == "RIGHT":

        y_l = -deck_half + crash_barrier_base_width / 2.0
        y_r = cw_right + crash_barrier_base_width / 2.0

    # BOTH footpaths
    elif footpath_config == "BOTH":

        y_r = cw_right + crash_barrier_base_width / 2.0
        y_l = cw_left - crash_barrier_base_width / 2.0

    else:
        raise ValueError(f"Invalid footpath_config: {footpath_config}")

    # SKEW OFFSET CALCULATION
    def get_skew_x(y):
        if skew_angle == 0:
            return 0.0
        return y * math.tan(math.radians(skew_angle))

    # SELECT GEOMETRY BASED ON BARRIER TYPE
    if barrier_type == "Rigid":
        right_shape = create_rigid_rcc_crash_barrier(
            length=span_length_L,
            design_dict=design_dict,
            side="RIGHT",
            skew_angle=-skew_angle
        )
        left_shape = create_rigid_rcc_crash_barrier(
            length=span_length_L,
            design_dict=design_dict,
            side="LEFT",
            skew_angle=skew_angle
        )
        
        crash_barriers.append(translate(right_shape, x=get_skew_x(y_r), y=y_r, z=deck_top_z))
        crash_barriers.append(translate(left_shape, x=get_skew_x(y_l), y=y_l, z=deck_top_z))

    elif barrier_type == "Semi-Rigid":
        right_parts = create_semi_rigid_metallic_barrier(
            length=span_length_L,
            design_dict=design_dict,
            side="RIGHT",
            skew_angle=-skew_angle
        )

        left_parts = create_semi_rigid_metallic_barrier(
            length=span_length_L,
            design_dict=design_dict,
            side="LEFT",
            skew_angle=skew_angle
        )

        # Apply translations and store as dictionaries for coloring
        right_dict = {k: translate(v, x=get_skew_x(y_r), y=y_r, z=deck_top_z) for k, v in right_parts.items() if v}
        left_dict = {k: translate(v, x=get_skew_x(y_l), y=y_l, z=deck_top_z) for k, v in left_parts.items() if v}
        
        crash_barriers.append(right_dict)
        crash_barriers.append(left_dict)
        
    else:
        raise ValueError(f"Invalid barrier_type: {barrier_type}. Use 'Rigid' or 'Semi-Rigid'")

    return crash_barriers
