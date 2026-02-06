"""
Creates median barriers.
Median geometry is independent of edge crash barriers (IRC Fig 5 series).
Supports three types per IRC 5:2015:
  - Raised Kerb (Fig 5a)
  - RCC Crash Barrier (Fig 5b)
  - Metallic Crash Barrier (Fig 5c)
"""

from OCC.Core.gp import gp_Trsf, gp_Vec, gp_Pnt, gp_Dir, gp_Ax2, gp_Ax1
from OCC.Core.BRepBuilderAPI import (
    BRepBuilderAPI_Transform,
    BRepBuilderAPI_MakePolygon,
    BRepBuilderAPI_MakeFace
)
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakePrism
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse
import math
import numpy as np


def _translate(shape, x=0.0, y=0.0, z=0.0):
    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(x, y, z))
    return BRepBuilderAPI_Transform(shape, trsf, True).Shape()


def _mirror_y(shape):
    """Mirror shape about YZ plane (flip in Y direction)."""
    trsf = gp_Trsf()
    trsf.SetMirror(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(0, 1, 0)))
    return BRepBuilderAPI_Transform(shape, trsf, True).Shape()


def _create_channel_section(length, depth, flange_width, web_thickness, flange_thickness):
    """
    Creates a C-channel section extruded along Z-axis (initially).
    Origin at center of the back of the web.
    """
    # Re-using the logic from crash_barrier/builder.py
    
    y_web_back = -web_thickness / 2.0
    y_web_front = web_thickness / 2.0
    y_flange_tip = depth - web_thickness / 2.0 
    
    z_bottom = -flange_width / 2.0
    z_top = flange_width / 2.0
    
    # Points for C-shape (facing +Y) in YZ plane
    p1 = gp_Pnt(0, y_flange_tip, z_bottom)
    p2 = gp_Pnt(0, y_web_back, z_bottom)
    p3 = gp_Pnt(0, y_web_back, z_top)
    p4 = gp_Pnt(0, y_flange_tip, z_top)
    p5 = gp_Pnt(0, y_flange_tip, z_top - flange_thickness)
    p6 = gp_Pnt(0, y_web_front, z_top - flange_thickness)
    p7 = gp_Pnt(0, y_web_front, z_bottom + flange_thickness)
    p8 = gp_Pnt(0, y_flange_tip, z_bottom + flange_thickness)
    
    poly = BRepBuilderAPI_MakePolygon()
    for p in (p1, p2, p3, p4, p5, p6, p7, p8):
        poly.Add(p)
    poly.Close()
    
    face = BRepBuilderAPI_MakeFace(poly.Wire()).Face()
    solid = BRepPrimAPI_MakePrism(face, gp_Vec(length, 0, 0)).Shape()
    
    return solid


def create_raised_kerb(length, design_dict):
    """
    Creates raised kerb median (IRC Fig 5a).
    Trapezoidal profile extruded along span.
    """
    kerb_height = design_dict.get("kerb_height")
    kerb_top_width = design_dict.get("kerb_top_width")
    kerb_bottom_width = design_dict.get("kerb_bottom_width")
    
    # Profile in YZ plane
    z0 = 0.0
    z1 = kerb_height
    
    y_bottom_l = -kerb_bottom_width / 2.0
    y_bottom_r = kerb_bottom_width / 2.0
    y_top_l = -kerb_top_width / 2.0
    y_top_r = kerb_top_width / 2.0
    
    # Trapezoidal profile (counter-clockwise)
    p1 = gp_Pnt(0, y_bottom_l, z0)
    p2 = gp_Pnt(0, y_bottom_r, z0)
    p3 = gp_Pnt(0, y_top_r, z1)
    p4 = gp_Pnt(0, y_top_l, z1)
    
    poly = BRepBuilderAPI_MakePolygon()
    for p in (p1, p2, p3, p4):
        poly.Add(p)
    poly.Close()
    
    face = BRepBuilderAPI_MakeFace(poly.Wire()).Face()
    solid = BRepPrimAPI_MakePrism(face, gp_Vec(length, 0, 0)).Shape()
    
    return solid


def create_rcc_crash_barrier_median(length, design_dict):
    """
    Creates RCC crash barrier median (IRC Fig 5b).
    Single New Jersey barrier profile (will be mirrored for the other side).
    Uses the same IRC-5R profile geometry as the edge crash barrier.
    """
    barrier_height = design_dict.get("barrier_height", 900)
    barrier_top_width = design_dict.get("barrier_top_width", 175)
    barrier_bottom_width = design_dict.get("barrier_bottom_width", 450)
    
    # Profile heights from IRC
    barrier_base_h = design_dict.get("barrier_split_h3", 100)
    barrier_mid_h = design_dict.get("barrier_split_h2", 250) + design_dict.get("barrier_split_h1", 500)
    
    wearing = design_dict.get("wearing_course_thickness", 50)
    
    # Calculate intermediate width at transition point
    H_transition = 250  # Height of transition section
    W_at_transition = barrier_bottom_width - 200
    
    # Z levels
    z0 = 0.0  # Start at structural deck level
    z1 = wearing + barrier_base_h     # Top of base vertical
    z2 = z1 + H_transition            # End of transition slope
    z3 = barrier_height               # Top
    
    # Y levels (half-widths) - Centered System
    y_base = barrier_bottom_width / 2.0
    y_top = barrier_top_width / 2.0
    y_trans = W_at_transition / 2.0
    
    # 1. Bottom Right (Road side base)
    p1 = gp_Pnt(0, y_base, z0)
    
    # 2. Bottom Left (Median side base)
    p2 = gp_Pnt(0, -y_base, z0)
    
    # 3. Base Top Left (Median side)
    p3 = gp_Pnt(0, -y_base, z1)
    
    # 4. Top Left (Median side) - Sloped back face
    p4 = gp_Pnt(0, -y_top, z3)
    
    # 5. Top Right (Road side)
    p5 = gp_Pnt(0, y_top, z3)
    
    # 6. Transition Top Right (End of main slope)
    p6 = gp_Pnt(0, y_trans, z2)
    
    # 7. Base Top Right (Start of transition)
    p7 = gp_Pnt(0, y_base, z1)
    
    # Create Polygon
    poly = BRepBuilderAPI_MakePolygon()
    for p in (p1, p2, p3, p4, p5, p6, p7):
        poly.Add(p)
    poly.Close()
    
    face = BRepBuilderAPI_MakeFace(poly.Wire()).Face()
    solid = BRepPrimAPI_MakePrism(face, gp_Vec(length, 0, 0)).Shape()
    
    return solid


def create_metallic_barrier_system(length, design_dict, kerb_top_width, kerb_height):
    """
    Creates metallic crash barrier system (IRC Fig 5c) - posts, spacers, and W-beams only.
    Single side system (will be positioned on each side of the central kerb).
    Kerb is created separately.
    
    Args:
        length: Length of the barrier along the span
        design_dict: Design parameters
        kerb_top_width: Width of the kerb top (for positioning)
        kerb_height: Height of the kerb (needed for positioning)
    
    Returns:
        Combined shape of posts, spacers, and W-beams
    """
    # Post dimensions
    post_height = design_dict.get("post_height", 950)
    post_spacing = design_dict.get("post_spacing", 1000)
    spacer_height = design_dict.get("spacer_height", 330)
    
    # W-beam
    number_of_w_beams = design_dict.get("number_of_w_beams", 1)
    w_beam_thickness = design_dict.get("w_beam_thickness", 3.0)
    
    #  CREATE POSTS (ISMC 150 as per IRC 5 Fig 5c)
    post_depth = design_dict.get("post_depth", 170)
    post_width = design_dict.get("post_width", 150)
    post_web_thk = design_dict.get("post_web_thickness", 5.0)
    post_flange_thk = design_dict.get("post_flange_thickness", 7.8)
    post_offset = design_dict.get("post_offset_from_edge", 75)  # From kerb edge
    
    num_posts = int(length / post_spacing) + 1
    
    #  SPACER PARAMETERS
    spacer_width = design_dict.get("spacer_width", 200)
    spacer_depth = design_dict.get("spacer_depth", 150)
    spacer_web_thk = design_dict.get("spacer_web_thickness", 5.0)
    spacer_flange_thk = design_dict.get("spacer_flange_thickness", 7.8)
    
    #  W-BEAM PARAMETERS
    W_BEAM_HEIGHT = spacer_height  # Aligned with spacer height 
    W_BEAM_DEPTH = 83.0            
    W_BEAM_THICKNESS = w_beam_thickness
    
    # Gaussian parameters for wave profile
    sigma = W_BEAM_HEIGHT / 10.0
    mu1 = W_BEAM_HEIGHT * 0.25
    mu2 = W_BEAM_HEIGHT * 0.75
    amp = W_BEAM_DEPTH * 1.5       # Effective depth of the W-beam wave
    
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
            outer_pts.SetValue(i, gp_Pnt(0.0, y_wave, z))
        
        y_top_outer = y_wave # Last y_wave value
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
            inner_pts.SetValue(i, gp_Pnt(0.0, y_wave_inner, z))
        
        y_top_inner = y_wave_inner
        y_bottom_inner = (
            amp * math.exp(-((zs[0] - mu1) ** 2) / (2 * sigma ** 2)) +
            amp * math.exp(-((zs[0] - mu2) ** 2) / (2 * sigma ** 2))
        ) - W_BEAM_THICKNESS

        inner_curve = GeomAPI_PointsToBSpline(inner_pts).Curve()

        # COMBINE INTO CLOSED WIRE 
        wire = BRepBuilderAPI_MakeWire()
        # Outer curve (upwards)
        wire.Add(BRepBuilderAPI_MakeEdge(outer_curve).Edge())
        # Top connecting edge
        wire.Add(BRepBuilderAPI_MakeEdge(
            gp_Pnt(0.0, y_top_outer, W_BEAM_HEIGHT),
            gp_Pnt(0.0, y_top_inner, W_BEAM_HEIGHT)
        ).Edge())
        # Inner curve (downwards)
        wire.Add(BRepBuilderAPI_MakeEdge(inner_curve).Edge())
        # Bottom connecting edge
        wire.Add(BRepBuilderAPI_MakeEdge(
            gp_Pnt(0.0, y_bottom_inner, 0.0),
            gp_Pnt(0.0, y_bottom_outer, 0.0)
        ).Edge())

        return BRepBuilderAPI_MakeFace(wire.Wire()).Face()



    #  ARRANGEMENT CALCULATIONS
    # Right side template: Post -> Spacer -> W-beam -> 75mm gap -> Kerb edge
    # Kerb edge is at +kerb_top_width / 2.0
    gap_from_edge = 5.0
    kerb_edge_y = kerb_top_width / 2.0
    
    # Beam peak face should be at gap_from_edge from kerb edge
    beam_back_y = kerb_edge_y - gap_from_edge - amp
    
    # Spacer is attached to the back of the beam
    spacer_y_center = beam_back_y - spacer_width / 2.0
    
    # Post is attached to the back of the spacer
    post_y_center = beam_back_y - spacer_width - post_width / 2.0

    #  GENERATE POSTS
    posts_combined = None
    for i in range(num_posts):
        x_pos = i * post_spacing
        if x_pos > length: break
        
        def create_vertical_channel(h, d, w, tw, tf):
            x_web_back, x_web_front = -tw / 2.0, tw / 2.0
            x_flange_tip = d - tw / 2.0
            y_left, y_right = -w / 2.0, w / 2.0
            pts = [
                gp_Pnt(x_flange_tip, y_left, 0), gp_Pnt(x_web_back, y_left, 0),
                gp_Pnt(x_web_back, y_right, 0), gp_Pnt(x_flange_tip, y_right, 0),
                gp_Pnt(x_flange_tip, y_right - tf, 0), gp_Pnt(x_web_front, y_right - tf, 0),
                gp_Pnt(x_web_front, y_left + tf, 0), gp_Pnt(x_flange_tip, y_left + tf, 0)
            ]
            poly = BRepBuilderAPI_MakePolygon()
            for p in pts: poly.Add(p)
            poly.Close()
            return BRepPrimAPI_MakePrism(BRepBuilderAPI_MakeFace(poly.Wire()).Face(), gp_Vec(0, 0, h)).Shape()

        post_solid = create_vertical_channel(post_height, post_depth, post_width, post_web_thk, post_flange_thk)
        post_solid = _translate(post_solid, x=x_pos, y=post_y_center, z=kerb_height)
        posts_combined = post_solid if posts_combined is None else BRepAlgoAPI_Fuse(posts_combined, post_solid).Shape()

    #  GENERATE BEAMS AND SPACERS
    spacers_combined = None
    beams_combined = None
    
    if number_of_w_beams == 1:
        beam_heights = [post_height - spacer_height / 2.0]
    else:
        h_upper = post_height - spacer_height / 2.0
        h_lower = h_upper - spacer_height - 145
        beam_heights = [h_lower, h_upper]
    
    for beam_h in beam_heights[:number_of_w_beams]:
        beam_z = kerb_height + beam_h - W_BEAM_HEIGHT / 2.0
        spacer_z = kerb_height + beam_h - spacer_height / 2.0

        # Spacers (one per post)
        for i in range(num_posts):
            x_pos = i * post_spacing
            if x_pos > length: break
            
            def create_vertical_spacer(h, d, w, tw, tf):
                x_web_back, x_web_front = -tw / 2.0, tw / 2.0
                x_flange_tip = d - tw / 2.0
                y_left, y_right = -w / 2.0, w / 2.0
                pts = [
                    gp_Pnt(x_flange_tip, y_left, 0), gp_Pnt(x_web_back, y_left, 0),
                    gp_Pnt(x_web_back, y_right, 0), gp_Pnt(x_flange_tip, y_right, 0),
                    gp_Pnt(x_flange_tip, y_right - tf, 0), gp_Pnt(x_web_front, y_right - tf, 0),
                    gp_Pnt(x_web_front, y_left + tf, 0), gp_Pnt(x_flange_tip, y_left + tf, 0)
                ]
                poly = BRepBuilderAPI_MakePolygon()
                for p in pts: poly.Add(p)
                poly.Close()
                return BRepPrimAPI_MakePrism(BRepBuilderAPI_MakeFace(poly.Wire()).Face(), gp_Vec(0, 0, h)).Shape()

            spacer_solid = create_vertical_spacer(spacer_height, spacer_depth, spacer_width, spacer_web_thk, spacer_flange_thk)
            spacer_solid = _translate(spacer_solid, x=x_pos, y=spacer_y_center, z=spacer_z)
            spacers_combined = spacer_solid if spacers_combined is None else BRepAlgoAPI_Fuse(spacers_combined, spacer_solid).Shape()

        # Beam solid (HOLLOW W-BEAM)
        beam_face = make_w_beam_face()

        beam_solid = BRepPrimAPI_MakePrism(
            beam_face,
            gp_Vec(length, 0, 0)
        ).Shape()

        beam_solid = _translate(
            beam_solid,
            x=0, y=beam_back_y, z=beam_z
        )

        beams_combined = (
            beam_solid if beams_combined is None
            else BRepAlgoAPI_Fuse(beams_combined, beam_solid).Shape()
        )

    
    return {
        "posts": posts_combined,
        "spacers": spacers_combined,
        "w_beams": beams_combined
    }


def create_median_kerb(length, median_width, design_dict):
    """
    Creates a single continuous median kerb with specified total width.
    Used for metallic crash barrier median as per IRC Fig 5c.
    
    Args:
        length: Length of the kerb along the span
        median_width: Total width of the median (center to center distance)
        design_dict: Design parameters containing kerb dimensions
    
    Returns:
        Kerb solid centered at y=0
    """
    kerb_height = design_dict.get("kerb_height", 100)
    # Use the median_width as the total kerb width
    kerb_top_width = median_width
    kerb_bottom_width = median_width + 50  # Slight taper at base
    
    z0 = 0.0
    z1 = kerb_height
    
    y_bottom_l = -kerb_bottom_width / 2.0
    y_bottom_r = kerb_bottom_width / 2.0
    y_top_l = -kerb_top_width / 2.0
    y_top_r = kerb_top_width / 2.0
    
    # Trapezoidal profile (counter-clockwise)
    p1 = gp_Pnt(0, y_bottom_l, z0)
    p2 = gp_Pnt(0, y_bottom_r, z0)
    p3 = gp_Pnt(0, y_top_r, z1)
    p4 = gp_Pnt(0, y_top_l, z1)
    
    poly = BRepBuilderAPI_MakePolygon()
    for p in (p1, p2, p3, p4):
        poly.Add(p)
    poly.Close()
    
    face = BRepBuilderAPI_MakeFace(poly.Wire()).Face()
    solid = BRepPrimAPI_MakePrism(face, gp_Vec(length, 0, 0)).Shape()
    
    return solid


def build_median(
    span_length,
    deck_top_z,
    carriageway_center_y,
    design_dict,
    median_type="RCC Crash Barrier"
):
    """
    Build median barriers.
    - Raised Kerb: Creates ONE central barrier.
    - RCC Crash Barrier: Creates TWO barriers separated by the median width.
    - Metallic Crash Barrier: Creates ONE continuous kerb with TWO metallic barrier systems 
      (posts + spacers + W-beams) on either side.
    """

    median_barriers = []
    
    # Get median width from design_dict (default 1200)
    median_total_width = design_dict.get("median_width", 1200)
    
    # CASE 1: RAISED KERB (Single Central)
    if median_type == "Raised Kerb":
        barrier_shape = create_raised_kerb(span_length, design_dict)
        # Centralized single barrier
        central_barrier = _translate(
            barrier_shape,
            x=0.0,
            y=carriageway_center_y,
            z=deck_top_z
        )
        median_barriers.append(central_barrier)
        return median_barriers

    # CASE 2: RCC CRASH BARRIER (Double Side mirrored)
    elif median_type == "RCC Crash Barrier":
        barrier_shape = create_rcc_crash_barrier_median(span_length, design_dict)
        barrier_base_width = design_dict.get("barrier_bottom_width", 450)
        
        # Calculate offset so outer edges are at median_total_width / 2
        # offset is the distance from center to barrier center
        offset = (median_total_width - barrier_base_width) / 2.0

        left_barrier = _mirror_y(barrier_shape)
        left_barrier = _translate(
            left_barrier,
            x=0.0,
            y=carriageway_center_y - offset,
            z=deck_top_z
        )
        median_barriers.append(left_barrier)

        right_barrier = _translate(
            barrier_shape,
            x=0.0,
            y=carriageway_center_y + offset,
            z=deck_top_z
        )
        median_barriers.append(right_barrier)
        return median_barriers
    
    # CASE 3: METALLIC CRASH BARRIER (Single continuous kerb + two barrier systems)
    elif median_type == "Metallic Crash Barrier":
        kerb_height = design_dict.get("kerb_height", 100)
        
        # Create single continuous kerb with total width = median_width
        kerb_shape = create_median_kerb(span_length, median_total_width, design_dict)
        kerb_positioned = _translate(
            kerb_shape,
            x=0.0,
            y=carriageway_center_y,
            z=deck_top_z
        )
        median_barriers.append({"kerb": kerb_positioned})
        
        # Create metallic barrier system (posts, spacers, W-beams) for one side
        barrier_system_parts = create_metallic_barrier_system(
            span_length, 
            design_dict, 
            median_total_width,  # Pass the total median width as kerb_top_width
            kerb_height
        )
        
        # Position left barrier system (mirrored)
        left_dict = {
            k: _translate(_mirror_y(v), x=0.0, y=carriageway_center_y, z=deck_top_z) 
            for k, v in barrier_system_parts.items() if v
        }
        median_barriers.append(left_dict)
        
        # Position right barrier system
        right_dict = {
            k: _translate(v, x=0.0, y=carriageway_center_y, z=deck_top_z) 
            for k, v in barrier_system_parts.items() if v
        }
        median_barriers.append(right_dict)
        
        return median_barriers
    
    else:
        raise ValueError(f"Invalid median_type: {median_type}")