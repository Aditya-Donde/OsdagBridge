"""
Cross Bracing Builder for Plate Girder Bridges
===============================================

This module provides functionality to create cross bracing systems for steel plate girder bridges.
It supports multiple section types and bracing configurations with skew angle capability.

Supported Section Types:
    - ANGLE: Single angle section (L-shape)
    - CHANNEL: Channel section (C-shape)
    - DOUBLE_ANGLE: Back-to-back double angle
    - DOUBLE_CHANNEL: Back-to-back double channel
    - I_SECTION: I-beam or H-beam section

Supported Bracing Patterns:
    - X-bracing: Diagonal cross pattern
    - K-bracing: K-pattern with central node
    - Horizontal Diaphragm: Rolled or welded beam diaphragms

Features:
    - Skew angle support for skewed bridges
    - Configurable bracket options
    - End diaphragm customization


"""

import math
from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Trsf, gp_Ax1, gp_Ax2, gp_Dir
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform


# SECTION GEOMETRY CREATORS

def _create_angle_section(length, leg_h, leg_w, thickness):
    """
    Create a single angle section (L-shape).
    
    Args:
        length: Length of the section along X-axis
        leg_h: Height of the vertical leg (longer leg)
        leg_w: Width of the horizontal leg (shorter leg)
        thickness: Thickness of the angle
        
    Returns:
        TopoDS_Shape: The angle section at origin
    """
    # Create two perpendicular legs
    # Vertical leg (longer)
    leg1 = BRepPrimAPI_MakeBox(length, thickness, leg_h).Shape()
    
    # Horizontal leg (shorter)
    leg2 = BRepPrimAPI_MakeBox(length, leg_w, thickness).Shape()
    
    # Fuse the two legs to form L-shape
    angle = BRepAlgoAPI_Fuse(leg1, leg2).Shape()
    
    return angle


def _create_channel_section(length, depth, flange_width, web_thickness, flange_thickness):
    """
    Create a channel section (C-shape).
    
    Args:
        length: Length of the section along X-axis
        depth: Overall depth of the channel
        flange_width: Width of top and bottom flanges
        web_thickness: Thickness of the web
        flange_thickness: Thickness of the flanges
        
    Returns:
        TopoDS_Shape: The channel section centered at origin
    """
    # Create web
    web = BRepPrimAPI_MakeBox(length, web_thickness, depth).Shape()
    
    # Create bottom flange
    bottom = BRepPrimAPI_MakeBox(length, flange_width, flange_thickness).Shape()
    
    # Create top flange
    top = BRepPrimAPI_MakeBox(length, flange_width, flange_thickness).Shape()
    
    # Position top flange
    trsf_top = gp_Trsf()
    trsf_top.SetTranslation(gp_Vec(0, 0, depth - flange_thickness))
    top = BRepBuilderAPI_Transform(top, trsf_top, True).Shape()
    
    # Fuse all components
    channel = BRepAlgoAPI_Fuse(web, bottom).Shape()
    channel = BRepAlgoAPI_Fuse(channel, top).Shape()
    
    # Center the section at origin
    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(-length / 2, -flange_width / 2, -depth / 2))
    
    return BRepBuilderAPI_Transform(channel, trsf, True).Shape()

def _create_double_angle_section(length, leg_h, leg_w, thickness, connection_type="SHORTER_LEG"):
    """
    Create a double angle section (back-to-back angles).
    
    Args:
        length: Length of the section along X-axis
        leg_h: Height of the longer leg
        leg_w: Width of the shorter leg
        thickness: Thickness of each angle
        connection_type: "LONGER_LEG" or "SHORTER_LEG"
        
    Returns:
        TopoDS_Shape: The double angle section centered at origin
    """
    if connection_type == "SHORTER_LEG":
        # SHORTER_LEG connection: shorter legs are back-to-back (vertical)
        # Longer legs point OUTWARD horizontally in opposite directions
        
        # First angle: L shape
        # Shorter leg (vertical) - back-to-back part
        vertical_leg1 = BRepPrimAPI_MakeBox(
            gp_Pnt(0, -thickness/2, 0), 
            gp_Pnt(length, thickness/2, leg_w)
        ).Shape()
        # Longer leg (horizontal) - pointing RIGHT
        horizontal_leg1 = BRepPrimAPI_MakeBox(
            gp_Pnt(0, thickness/2, leg_w - thickness), 
            gp_Pnt(length, thickness/2 + leg_h, leg_w)
        ).Shape()
        angle1 = BRepAlgoAPI_Fuse(vertical_leg1, horizontal_leg1).Shape()
        
        # Second angle: Mirrored L
        # Shorter leg (vertical) - back-to-back part (same position as first)
        vertical_leg2 = BRepPrimAPI_MakeBox(
            gp_Pnt(0, -thickness/2, 0), 
            gp_Pnt(length, thickness/2, leg_w)
        ).Shape()
        # Longer leg (horizontal) - pointing LEFT
        horizontal_leg2 = BRepPrimAPI_MakeBox(
            gp_Pnt(0, -thickness/2 - leg_h, leg_w - thickness), 
            gp_Pnt(length, -thickness/2, leg_w)
        ).Shape()
        angle2 = BRepAlgoAPI_Fuse(vertical_leg2, horizontal_leg2).Shape()
        
        # Fuse both angles
        double_angle = BRepAlgoAPI_Fuse(angle1, angle2).Shape()
        
        # Center at origin
        center_trsf = gp_Trsf()
        center_trsf.SetTranslation(gp_Vec(-length/2, 0, -leg_w/2))
        
    else:  # LONGER_LEG connection
        # LONGER_LEG connection: longer legs are back-to-back (vertical)
        # Shorter legs point OUTWARD horizontally in opposite directions
        
        # First angle: L shape
        # Longer leg (vertical) - back-to-back part
        vertical_leg1 = BRepPrimAPI_MakeBox(
            gp_Pnt(0, -thickness/2, 0), 
            gp_Pnt(length, thickness/2, leg_h)
        ).Shape()
        # Shorter leg (horizontal) - pointing RIGHT
        horizontal_leg1 = BRepPrimAPI_MakeBox(
            gp_Pnt(0, thickness/2, leg_h - thickness), 
            gp_Pnt(length, thickness/2 + leg_w, leg_h)
        ).Shape()
        angle1 = BRepAlgoAPI_Fuse(vertical_leg1, horizontal_leg1).Shape()
        
        # Second angle: Mirrored L
        # Longer leg (vertical) - back-to-back part (same position as first)
        vertical_leg2 = BRepPrimAPI_MakeBox(
            gp_Pnt(0, -thickness/2, 0), 
            gp_Pnt(length, thickness/2, leg_h)
        ).Shape()
        # Shorter leg (horizontal) - pointing LEFT
        horizontal_leg2 = BRepPrimAPI_MakeBox(
            gp_Pnt(0, -thickness/2 - leg_w, leg_h - thickness), 
            gp_Pnt(length, -thickness/2, leg_h)
        ).Shape()
        angle2 = BRepAlgoAPI_Fuse(vertical_leg2, horizontal_leg2).Shape()
        
        # Fuse both angles
        double_angle = BRepAlgoAPI_Fuse(angle1, angle2).Shape()
        
        # Center at origin
        center_trsf = gp_Trsf()
        center_trsf.SetTranslation(gp_Vec(-length/2, 0, -leg_h/2))
    
    return BRepBuilderAPI_Transform(double_angle, center_trsf, True).Shape()


def _create_double_channel_section(length, depth, flange_width, web_thickness, flange_thickness):
    """
    Create a double channel section (back-to-back channels).
    
    Args:
        length: Length of the section along X-axis
        depth: Overall depth of each channel
        flange_width: Width of flanges
        web_thickness: Thickness of the web
        flange_thickness: Thickness of the flanges
        
    Returns:
        TopoDS_Shape: The double channel section centered at origin
    """
    # Create base channel
    base = _create_channel_section(length, depth, flange_width, web_thickness, flange_thickness)
    
    # Create mirrored channel
    mirror = gp_Trsf()
    mirror.SetMirror(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(0, 1, 0)))
    mirrored = BRepBuilderAPI_Transform(base, mirror, True).Shape()
    
    # Spacing between channels
    offset = flange_width / 2
    
    # Position first channel
    t1 = gp_Trsf()
    t1.SetTranslation(gp_Vec(0, +offset, 0))
    c1 = BRepBuilderAPI_Transform(base, t1, True).Shape()
    
    # Position second channel
    t2 = gp_Trsf()
    t2.SetTranslation(gp_Vec(0, -offset, 0))
    c2 = BRepBuilderAPI_Transform(mirrored, t2, True).Shape()
    
    # Fuse both channels
    return BRepAlgoAPI_Fuse(c1, c2).Shape()


def _create_i_section(length, depth, flange_width, web_thickness, flange_thickness):
    """
    Create an I-section (I-beam or H-beam).
    
    Args:
        length: Length of the section along X-axis
        depth: Overall depth of the I-section
        flange_width: Width of top and bottom flanges
        web_thickness: Thickness of the web
        flange_thickness: Thickness of the flanges
        
    Returns:
        TopoDS_Shape: The I-section centered at origin
    """
    # Create web
    web = BRepPrimAPI_MakeBox(length, web_thickness, depth).Shape()
    
    # Create bottom flange
    bottom = BRepPrimAPI_MakeBox(length, flange_width, flange_thickness).Shape()
    
    # Create top flange
    top = BRepPrimAPI_MakeBox(length, flange_width, flange_thickness).Shape()
    
    # Position top flange
    trsf_top = gp_Trsf()
    trsf_top.SetTranslation(
        gp_Vec(0, -flange_width / 2 + web_thickness / 2, depth - flange_thickness)
    )
    top = BRepBuilderAPI_Transform(top, trsf_top, True).Shape()
    
    # Position bottom flange
    trsf_bot = gp_Trsf()
    trsf_bot.SetTranslation(
        gp_Vec(0, -flange_width / 2 + web_thickness / 2, 0)
    )
    bottom = BRepBuilderAPI_Transform(bottom, trsf_bot, True).Shape()
    
    # Fuse all components
    i_section = BRepAlgoAPI_Fuse(web, bottom).Shape()
    i_section = BRepAlgoAPI_Fuse(i_section, top).Shape()
    
    # Center the section at origin
    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(-length / 2, -web_thickness / 2, -depth / 2))
    
    return BRepBuilderAPI_Transform(i_section, trsf, True).Shape()


# UTILITY FUNCTIONS

def _get_roll_angle(section_type, roll_sign):
    """
    Determine the roll angle for section orientation.
    
    Args:
        section_type: Type of section ("ANGLE", "CHANNEL", etc.)
        roll_sign: Sign indicating roll direction (+1 or -1)
        
    Returns:
        float: Roll angle in radians
    """
    if section_type in ("ANGLE", "CHANNEL"):
        return roll_sign * (math.pi / 2)
    return 0.0


def _create_section_solid(section_type, length, thickness, dims):
    """
    Create a section solid based on type and dimensions.
    
    Args:
        section_type: Type of section to create
        length: Length of the section
        thickness: Thickness parameter (used for angles)
        dims: Dictionary containing section dimensions
        
    Returns:
        TopoDS_Shape: The created section
        
    Raises:
        ValueError: If section type is not supported
    """
    if section_type == "ANGLE":
        # Support both angle-specific and generic dimension keys
        h = dims.get("leg_h", dims.get("depth", 100))
        w = dims.get("leg_w", dims.get("flange_width", 50))
        return _create_angle_section(length, h, w, thickness)
    
    if section_type == "CHANNEL":
        d = dims.get("depth", 100)
        wf = dims.get("flange_width", 50)
        tw = dims.get("web_thickness", 5)
        tf = dims.get("flange_thickness", 7)
        return _create_channel_section(length, d, wf, tw, tf)
    
    if section_type == "DOUBLE_ANGLE":
        h = dims.get("leg_h", dims.get("depth", 100))
        w = dims.get("leg_w", dims.get("flange_width", 50))
        return _create_double_angle_section(
            length, h, w, thickness,
            dims.get("connection_type", "LONGER_LEG")
        )
    
    if section_type == "DOUBLE_CHANNEL":
        d = dims.get("depth", 100)
        wf = dims.get("flange_width", 50)
        tw = dims.get("web_thickness", 5)
        tf = dims.get("flange_thickness", 7)
        return _create_double_channel_section(length, d, wf, tw, tf)
    
    if section_type == "I_SECTION":
        d = dims.get("depth", 100)
        wf = dims.get("flange_width", 50)
        tw = dims.get("web_thickness", 10)
        tf = dims.get("flange_thickness", 15)
        return _create_i_section(length, d, wf, tw, tf)
    
    raise ValueError(f"Unsupported section type: {section_type}")


# MEMBER CREATION FUNCTIONS

def _create_diagonal_member(p1, p2, thickness, section_type, dims, roll_sign):
    """
    Create a diagonal bracing member between two points.
    
    
    Args:
        p1: Starting point (gp_Pnt)
        p2: Ending point (gp_Pnt)
        thickness: Section thickness
        section_type: Type of section
        dims: Section dimensions dictionary
        roll_sign: Roll direction indicator
        
    Returns:
        TopoDS_Shape: The positioned bracing member
    """
    # Calculate vector and length
    vec = gp_Vec(p1, p2)
    length = vec.Magnitude()
    
    # Create section at origin
    solid = _create_section_solid(section_type, length, thickness, dims)
    
    # Calculate rotation to align with target vector
    x_dir = gp_Dir(1, 0, 0)  # Initial direction
    tgt = gp_Dir(vec)         # Target direction
    
    axis = gp_Vec(x_dir.Crossed(tgt))
    angle = x_dir.Angle(tgt)
    
    # Apply rotation if needed
    if axis.Magnitude() > 1e-6:
        tr = gp_Trsf()
        tr.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(axis)), angle)
        solid = BRepBuilderAPI_Transform(solid, tr, True).Shape()
    
    # Apply roll angle for proper orientation
    roll = _get_roll_angle(section_type, roll_sign)
    if abs(roll) > 1e-6:
        tr = gp_Trsf()
        tr.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), tgt), roll)
        solid = BRepBuilderAPI_Transform(solid, tr, True).Shape()
    
    # Calculate midpoint
    mid = gp_Pnt(
        (p1.X() + p2.X()) / 2,
        (p1.Y() + p2.Y()) / 2,
        (p1.Z() + p2.Z()) / 2
    )
    
    # Translate to position
    tr = gp_Trsf()
    tr.SetTranslation(gp_Vec(mid.X(), mid.Y(), mid.Z()))
    
    return BRepBuilderAPI_Transform(solid, tr, True).Shape()


# BRACING PATTERN FUNCTIONS

def _x_bracing(x, yL, yR, depth, tf, thickness, flange_w, 
               section_type, dims, bracket, skew_angle=0):
    """
    Create X-bracing pattern between two girders.
    
    X-bracing consists of two diagonal members crossing each other,
    with optional horizontal brackets at top and/or bottom.
    
    Args:
        x: Longitudinal position
        yL: Left girder lateral position
        yR: Right girder lateral position
        depth: Girder depth
        tf: Flange thickness
        thickness: Bracing member thickness
        flange_w: Flange width
        section_type: Section type for bracing
        dims: Section dimensions
        bracket: Bracket option ("NONE", "UPPER", "LOWER", "BOTH")
        skew_angle: Bridge skew angle in degrees
        
    Returns:
        list: List of bracing member shapes
    """
    # Calculate vertical positions (top and bottom of web)
    z_bot = -depth / 2
    z_top = +depth / 2
    
    def get_skew_x(y):
        """Calculate longitudinal offset due to skew."""
        if skew_angle == 0:
            return 0.0
        return y * math.tan(math.radians(skew_angle))
    
    # Apply skew offsets
    x_l = x + get_skew_x(yL)
    x_r = x + get_skew_x(yR)
    
    # Create main X-diagonals
    braces = [
        # Left TOP → Right BOTTOM diagonal
        _create_diagonal_member(
            gp_Pnt(x_l, yL, z_top), 
            gp_Pnt(x_r, yR, z_bot),
            thickness, section_type, dims, +1
        ),
        # Left BOTTOM → Right TOP diagonal
        _create_diagonal_member(
            gp_Pnt(x_l, yL, z_bot), 
            gp_Pnt(x_r, yR, z_top),
            thickness, section_type, dims, -1
        )
    ]
    
    # Add optional brackets
    if bracket in ("LOWER", "BOTH"):
        braces.append(
            _create_diagonal_member(
                gp_Pnt(x_l, yL, z_bot), 
                gp_Pnt(x_r, yR, z_bot),
                thickness, section_type, dims, +1
            )
        )
    
    if bracket in ("UPPER", "BOTH"):
        braces.append(
            _create_diagonal_member(
                gp_Pnt(x_l, yL, z_top), 
                gp_Pnt(x_r, yR, z_top),
                thickness, section_type, dims, +1
            )
        )
    
    return braces


def _k_bracing(x, yL, yR, depth, tf, thickness, flange_w,
               section_type, dims, top_bracket, skew_angle=0):
    """
    Create K-bracing pattern between two girders.
    
    K-bracing consists of two diagonal members meeting at a central
    bottom node, with a mandatory bottom horizontal and optional top horizontal.
    
    Args:
        x: Longitudinal position
        yL: Left girder lateral position
        yR: Right girder lateral position
        depth: Girder depth
        tf: Flange thickness
        thickness: Bracing member thickness
        flange_w: Flange width
        section_type: Section type for bracing
        dims: Section dimensions
        top_bracket: Whether to include top horizontal bracket
        skew_angle: Bridge skew angle in degrees
        
    Returns:
        list: List of bracing member shapes
    """
    # Calculate vertical positions
    z_bot = -depth / 2
    z_top = +depth / 2
    
    # Calculate midpoint between girders
    ym = (yL + yR) / 2
    
    def get_skew_x(y):
        """Calculate longitudinal offset due to skew."""
        if skew_angle == 0:
            return 0.0
        return y * math.tan(math.radians(skew_angle))
    
    # Apply skew offsets
    x_l = x + get_skew_x(yL)
    x_r = x + get_skew_x(yR)
    x_m = x + get_skew_x(ym)
    
    # Create K-pattern members
    braces = [
        # Left TOP → Middle BOTTOM diagonal
        _create_diagonal_member(
            gp_Pnt(x_l, yL, z_top), 
            gp_Pnt(x_m, ym, z_bot),
            thickness, section_type, dims, +1
        ),
        # Right TOP → Middle BOTTOM diagonal
        _create_diagonal_member(
            gp_Pnt(x_r, yR, z_top), 
            gp_Pnt(x_m, ym, z_bot),
            thickness, section_type, dims, -1
        ),
        # Bottom horizontal (mandatory for K-bracing)
        _create_diagonal_member(
            gp_Pnt(x_l, yL, z_bot), 
            gp_Pnt(x_r, yR, z_bot),
            thickness, section_type, dims, +1
        )
    ]
    
    # Add optional top bracket
    if top_bracket:
        braces.append(
            _create_diagonal_member(
                gp_Pnt(x_l, yL, z_top), 
                gp_Pnt(x_r, yR, z_top),
                thickness, section_type, dims, +1
            )
        )
    
    return braces


def _diaphragm_bracing(x, yL, yR, depth, tf, thickness, section_type, dims, skew_angle=0):
    """
    Create a horizontal diaphragm member (rolled or welded beam).
    
    Diaphragm is placed at the top of the girder depth, typically used
    at bridge ends for load distribution and stability.
    
    Args:
        x: Longitudinal position
        yL: Left girder lateral position
        yR: Right girder lateral position
        depth: Girder depth
        tf: Flange thickness
        thickness: Diaphragm thickness
        section_type: Section type (typically I_SECTION)
        dims: Section dimensions
        skew_angle: Bridge skew angle in degrees
        
    Returns:
        list: List containing the diaphragm member shape
    """
    # Place exactly at the bottom of the girder top flange
    # top edge of web is at +depth / 2
    # diaphragm is centered at gp_Pnt, so center = (top_edge) - (member_depth / 2)
    member_depth = dims.get("depth", 100)
    z_center = (depth / 2) - (member_depth / 2)
    
    def get_skew_x(y):
        """Calculate longitudinal offset due to skew."""
        if skew_angle == 0:
            return 0.0
        return y * math.tan(math.radians(skew_angle))
    
    # Apply skew offsets
    x_l = x + get_skew_x(yL)
    x_r = x + get_skew_x(yR)
    
    # Create horizontal diaphragm member
    return [
        _create_diagonal_member(
            gp_Pnt(x_l, yL, z_center), 
            gp_Pnt(x_r, yR, z_center),
            thickness, 
            section_type, 
            dims, 
            +1
        )
    ]




def build_cross_bracings(
    *,
    # Bridge geometry parameters
    span_length_L,
    num_girders,
    girder_spacing,
    girder_depth,
    flange_thickness,
    flange_width,
    
    # Bracing configuration
    bracing_type,          # "X" or "K"
    section_type,          # "ANGLE", "CHANNEL", "DOUBLE_ANGLE", etc.
    section_dims,          # Dictionary with section dimensions
    thickness,             # Member thickness
    
    # Spacing and options
    panel_spacing,         # Spacing between bracing frames
    bracket_option="BOTH", # For X-bracing: "NONE", "UPPER", "LOWER", "BOTH"
    top_bracket=False,     # For K-bracing: include top horizontal
    skew_angle=0,          # Bridge skew angle in degrees
    
    # End diaphragm configuration
    end_diaphragm_type="Cross Bracing",  # "Cross Bracing", "Rolled Beam", "Welded Beam"
    end_diaphragm_section="I_SECTION",   # Section type for diaphragm
    end_diaphragm_dims=None,             # Custom dimensions for diaphragm
    end_diaphragm_spacing=0            
):

    bracings = []
    
    # Calculate bracing frame positions along the span
    # Number of internal panels
    n_internal = int(span_length_L / panel_spacing) - 1
    # Total number of frames (internal + 2 end frames)
    n_total = n_internal + 2
    # Actual spacing (may differ slightly from panel_spacing)
    spacing = span_length_L / (n_total - 1)
    # Generate longitudinal positions
    x_positions = [i * spacing for i in range(n_total)]
    
    # Calculate total transverse width
    total_width = (num_girders - 1) * girder_spacing
    
    # Loop through all bracing frames
    for idx_x, x in enumerate(x_positions):
        # Loop through all bays between girders
        for i in range(num_girders - 1):
            # Calculate lateral positions of left and right girders
            yL = (i * girder_spacing) - total_width / 2
            yR = yL + girder_spacing
            
            # Check if this is an end position (first or last frame)
            is_end = (x == x_positions[0] or x == x_positions[-1])
            is_first = (x == x_positions[0])
            is_last = (x == x_positions[-1])
            
            # END DIAPHRAGM HANDLING
            if is_end:
                # Apply longitudinal offset for end diaphragms
                # Default offset if spacing is 0
                offset = end_diaphragm_spacing if end_diaphragm_spacing > 0 else 200.0
                
                if is_first:
                    x_eff = x + offset
                else: # is_last
                    x_eff = x - offset

                if end_diaphragm_type == "Cross Bracing":
                    # Use the same bracing type (X or K) as internal panels
                    if bracing_type == "X":
                        bracings.extend(
                            _x_bracing(
                                x_eff, yL, yR,
                                girder_depth, flange_thickness,
                                thickness, flange_width,
                                section_type, section_dims,
                                bracket_option,
                                skew_angle=skew_angle
                            )
                        )
                    elif bracing_type == "K":
                        bracings.extend(
                            _k_bracing(
                                x_eff, yL, yR,
                                girder_depth, flange_thickness,
                                thickness, flange_width,
                                section_type, section_dims,
                                top_bracket,
                                skew_angle=skew_angle
                            )
                        )
                
                elif end_diaphragm_type == "Rolled Beam":
                    # Use I-section for rolled beam diaphragm
                    diaphragm_dims = end_diaphragm_dims if end_diaphragm_dims is not None else section_dims
                    
                    # Validate dimensions or use defaults
                    if "depth" not in diaphragm_dims or "flange_width" not in diaphragm_dims:
                        diaphragm_dims = {
                            "depth": girder_depth * 0.8,
                            "flange_width": 200,
                            "web_thickness": 10,
                            "flange_thickness": 15
                        }
                    
                    bracings.extend(
                        _diaphragm_bracing(
                            x_eff, yL, yR,
                            girder_depth, flange_thickness,
                            thickness,
                            "I_SECTION",
                            diaphragm_dims,
                            skew_angle=skew_angle
                        )
                    )
                
                elif end_diaphragm_type == "Welded Beam":
                    # Use I-section for welded beam diaphragm
                    # Welded beams can have different proportions than rolled
                    diaphragm_dims = end_diaphragm_dims if end_diaphragm_dims is not None else section_dims
                    
                    # Validate dimensions or use defaults (slightly larger than rolled)
                    if "depth" not in diaphragm_dims or "flange_width" not in diaphragm_dims:
                        diaphragm_dims = {
                            "depth": girder_depth * 0.85,  # Slightly deeper
                            "flange_width": 250,            # Wider flange
                            "web_thickness": 12,            # Thicker web
                            "flange_thickness": 20          # Thicker flange
                        }
                    
                    bracings.extend(
                        _diaphragm_bracing(
                            x_eff, yL, yR,
                            girder_depth, flange_thickness,
                            thickness,
                            "I_SECTION",
                            diaphragm_dims,
                            skew_angle=skew_angle
                        )
                    )
                
                continue
            
            # INTERNAL BRACING HANDLING
            # Build normal X or K bracing for internal panels
            if bracing_type == "X":
                bracings.extend(
                    _x_bracing(
                        x, yL, yR,
                        girder_depth, flange_thickness,
                        thickness, flange_width,
                        section_type, section_dims,
                        bracket_option,
                        skew_angle=skew_angle
                    )
                )
            
            elif bracing_type == "K":
                bracings.extend(
                    _k_bracing(
                        x, yL, yR,
                        girder_depth, flange_thickness,
                        thickness, flange_width,
                        section_type, section_dims,
                        top_bracket,
                        skew_angle=skew_angle
                    )
                )
    
    return bracings