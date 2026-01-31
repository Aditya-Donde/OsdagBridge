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
def create_rcc_crash_barrier_median(length, design_dict):
    """
    Creates RCC crash barrier median (IRC Fig 5b).
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
    
    

def create_metallic_crash_barrier_median(length, design_dict):
    """
    Creates metallic crash barrier median (IRC Fig 5c).
    Single side (will be mirrored).
    """
    # Kerb dimensions
    kerb_height = design_dict.get("kerb_height", 100)
    kerb_top_width = design_dict.get("kerb_top_width", 500)
    kerb_bottom_width = design_dict.get("kerb_bottom_width", 550)
    
    # Post dimensions
    post_height = design_dict.get("post_height", 950)
    post_spacing = design_dict.get("post_spacing", 1000)
    spacer_height = design_dict.get("spacer_height", 330)
    
    # W-beam
    number_of_w_beams = design_dict.get("number_of_w_beams", 1)
    w_beam_thickness = design_dict.get("w_beam_thickness", 3.0)
    
    # Guard rail heights (Computed dynamically below)
    # guard_rail_height_single = 620
    # guard_rail_height_double_lower = 330
    # guard_rail_height_double_upper = 805
    
    #  CREATE KERB 
    z0 = 0.0
    z1 = kerb_height
    
    y_bottom_l = -kerb_bottom_width / 2.0
    y_bottom_r = kerb_bottom_width / 2.0
    y_top_l = -kerb_top_width / 2.0
    y_top_r = kerb_top_width / 2.0
    
    p1 = gp_Pnt(0, y_bottom_l, z0)
    p2 = gp_Pnt(0, y_bottom_r, z0)
    p3 = gp_Pnt(0, y_top_r, z1)
    p4 = gp_Pnt(0, y_top_l, z1)
    
    kerb_poly = BRepBuilderAPI_MakePolygon()
    for p in (p1, p2, p3, p4):
        kerb_poly.Add(p)
    kerb_poly.Close()
    
    kerb_face = BRepBuilderAPI_MakeFace(kerb_poly.Wire()).Face()
    kerb_solid = BRepPrimAPI_MakePrism(kerb_face, gp_Vec(length, 0, 0)).Shape()
    
    #  CREATE POSTS (ISMC 150 as per IRC 5 Fig 5c)
    post_depth = design_dict.get("post_depth", 150)
    post_width = design_dict.get("post_width", 75)
    post_web_thk = design_dict.get("post_web_thickness", 5.0)
    post_flange_thk = design_dict.get("post_flange_thickness", 7.8)
    post_offset = design_dict.get("post_offset_from_edge", 75)  # From kerb edge
    
    num_posts = int(length / post_spacing) + 1
    posts_combined = None
    
    for i in range(num_posts):
        x_pos = i * post_spacing
        if x_pos > length:
            break
        
        # Post on outer side (road facing)
        # Center of post in Y
        post_y_center = kerb_top_width / 2.0 - post_offset - post_depth / 2.0
        
        # Create vertical channel post
        def create_vertical_channel(h, d, w, tw, tf):
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
                gp_Pnt(x_flange_tip, y_left + tf, 0)
            ]
            poly = BRepBuilderAPI_MakePolygon()
            for p in pts:
                poly.Add(p)
            poly.Close()
            face = BRepBuilderAPI_MakeFace(poly.Wire()).Face()
            return BRepPrimAPI_MakePrism(face, gp_Vec(0, 0, h)).Shape()

        post_solid = create_vertical_channel(post_height, post_depth, post_width, post_web_thk, post_flange_thk)
        
        
        tr_rot = gp_Trsf()
        tr_rot.SetRotation(gp_Ax1(gp_Pnt(0,0,0), gp_Dir(0,0,1)), 0.0)
        post_solid = BRepBuilderAPI_Transform(post_solid, tr_rot, True).Shape()
        
        post_solid = _translate(post_solid, x=x_pos, y=post_y_center, z=kerb_height)
        
        if posts_combined is None:
            posts_combined = post_solid
        else:
            posts_combined = BRepAlgoAPI_Fuse(posts_combined, post_solid).Shape()
    
    #  CREATE SPACER CHANNELS PARAMETERS (ISMC 150)
    spacer_width = design_dict.get("spacer_width", 75)
    spacer_depth = design_dict.get("spacer_depth", 150)
    spacer_web_thk = design_dict.get("spacer_web_thickness", 5.0)
    spacer_flange_thk = design_dict.get("spacer_flange_thickness", 7.8)
    
    spacers_combined = None
    
    #  CREATE W-BEAMS
    import numpy as np
    
    W_BEAM_HEIGHT = spacer_height  # Aligned with spacer height 
    W_BEAM_DEPTH = 83.0    # Standard W-beam depth
    W_BEAM_THICKNESS = w_beam_thickness
    
    def make_w_beam_wire():
        points = 40
        zs = np.linspace(0, W_BEAM_HEIGHT, points)
        
        # Double Wave Profile
        # Two guassians or sin waves in Y based on Z
        
        # Sum of gaussians as before, but on Z
        sigma = W_BEAM_HEIGHT / 6.0
        mu1 = W_BEAM_HEIGHT * 0.25
        mu2 = W_BEAM_HEIGHT * 0.75
        amp = W_BEAM_DEPTH
        
        poly = BRepBuilderAPI_MakePolygon()
        
        for z in zs:
            # Gaussian bumps
            y = (amp * math.exp(-((z - mu1) ** 2) / (2 * sigma ** 2)) + 
                 amp * math.exp(-((z - mu2) ** 2) / (2 * sigma ** 2)))
            
            poly.Add(gp_Pnt(0.0, y, z))
        
        # Close the back face (flat at y=0) to form a solid cross-section
        poly.Add(gp_Pnt(0.0, 0.0, W_BEAM_HEIGHT))
        poly.Add(gp_Pnt(0.0, 0.0, 0.0))
        poly.Close()
            
        return poly.Wire()
    
    beams_combined = None
    
    if number_of_w_beams == 1:
        # Top of beam/spacer aligns with post top
        beam_heights = [post_height - spacer_height / 2.0]
    else:
        # Upper beam/spacer starts at post top
        h_upper = post_height - spacer_height / 2.0
        # Lower beam/spacer comes after 145mm gap
        h_lower = h_upper - spacer_height - 145
        beam_heights = [h_lower, h_upper]
    
    for beam_h in beam_heights[:number_of_w_beams]:
        # Beam Z is bottom of the beam
        beam_z = kerb_height + beam_h - W_BEAM_HEIGHT / 2.0

        # Post Position
        post_y_center = kerb_top_width / 2.0 - post_offset - post_depth / 2.0
        
        # SPACER GENERATION (Per Beam)
        # Spacer Center aligned with Beam Center
        # Spacer Z (base) = kerb_height + beam_h - spacer_height / 2.0
        spacer_z = kerb_height + beam_h - spacer_height / 2.0
        
        # Spacer Y ends at: post_y_center + post_width/2 + spacer_width
        spacer_y_center = post_y_center + post_width/2.0 + spacer_width/2.0

        for i in range(num_posts):
            x_pos = i * post_spacing
            if x_pos > length:
                break
            
            def create_vertical_spacer(h, d, w, tw, tf):
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
                    gp_Pnt(x_flange_tip, y_left + tf, 0)
                ]
                poly = BRepBuilderAPI_MakePolygon()
                for p in pts:
                    poly.Add(p)
                poly.Close()
                face = BRepBuilderAPI_MakeFace(poly.Wire()).Face()
                return BRepPrimAPI_MakePrism(face, gp_Vec(0, 0, h)).Shape()

            spacer_solid = create_vertical_spacer(spacer_height, spacer_depth, spacer_width, spacer_web_thk, spacer_flange_thk)
            
            # Rotate 0 deg (C faces +X)
            tr_rot = gp_Trsf()
            tr_rot.SetRotation(gp_Ax1(gp_Pnt(0,0,0), gp_Dir(0,0,1)), 0.0)
            spacer_solid = BRepBuilderAPI_Transform(spacer_solid, tr_rot, True).Shape()
            
            spacer_solid = _translate(spacer_solid, x=x_pos, y=spacer_y_center, z=spacer_z)
            
            if spacers_combined is None:
                spacers_combined = spacer_solid
            else:
                spacers_combined = BRepAlgoAPI_Fuse(spacers_combined, spacer_solid).Shape()



        
        beam_y_pos = spacer_y_center + spacer_width / 2.0
        
        # Create Wire -> Face -> Solid
        wire = make_w_beam_wire()
        beam_face = BRepBuilderAPI_MakeFace(wire).Face()
        beam_solid = BRepPrimAPI_MakePrism(beam_face, gp_Vec(length, 0, 0)).Shape()
        
        # Translate to position
        beam_solid = _translate(
            beam_solid,
            x=0,
            y=beam_y_pos,
            z=beam_z
        )
        
        if beams_combined is None:
            beams_combined = beam_solid
        else:
            beams_combined = BRepAlgoAPI_Fuse(beams_combined, beam_solid).Shape()
    
    # COMBINE 
    combined = kerb_solid
    if posts_combined is not None:
        combined = BRepAlgoAPI_Fuse(combined, posts_combined).Shape()
    if spacers_combined is not None:
        combined = BRepAlgoAPI_Fuse(combined, spacers_combined).Shape()
    if beams_combined is not None:
        combined = BRepAlgoAPI_Fuse(combined, beams_combined).Shape()
    
    return combined


def build_median(
    span_length,
    deck_top_z,
    carriageway_center_y,
    design_dict,
    median_type="RCC Crash Barrier"
):
    """
    Build median barriers.
    Always creates TWO barriers separated by the median width.
    """

    median_barriers = []
    
    # Get median width from design_dict (default 1200)
    median_total_width = design_dict.get("median_width", 1200)
    
    # Create the base shape (one side)
    if median_type == "Raised Kerb":
        barrier_shape = create_raised_kerb(span_length, design_dict)
        barrier_base_width = design_dict.get("kerb_bottom_width", 550)
    elif median_type == "RCC Crash Barrier":
        barrier_shape = create_rcc_crash_barrier_median(span_length, design_dict)
        barrier_base_width = design_dict.get("barrier_bottom_width", 450)
    elif median_type == "Metallic Crash Barrier":
        barrier_shape = create_metallic_crash_barrier_median(span_length, design_dict)
        barrier_base_width = design_dict.get("kerb_bottom_width", 550)
    else:
        raise ValueError(f"Invalid median_type: {median_type}")

    
    offset = (median_total_width ) - (barrier_base_width / 2.0)

    
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
