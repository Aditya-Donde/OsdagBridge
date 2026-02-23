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
        TopoDS_Shape: The angle section centered at origin
    """
    # Create two perpendicular legs
    # Vertical leg (longer)
    leg1 = BRepPrimAPI_MakeBox(length, thickness, leg_h).Shape()
    
    # Horizontal leg (shorter)
    leg2 = BRepPrimAPI_MakeBox(length, leg_w, thickness).Shape()
    
    # Fuse the two legs to form L-shape
    angle = BRepAlgoAPI_Fuse(leg1, leg2).Shape()
    
    # Center the section at origin (similar to channel and double angle sections)
    # The angle should be centered around the X-axis
    # Move it so the inner corner is at the centroid
    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(-length / 2, -leg_w / 2, -leg_h / 2))
    
    return BRepBuilderAPI_Transform(angle, trsf, True).Shape()


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

def _x_bracing(x, yL, yR, depth, tf, flange_w,
               diagonal_thickness, diagonal_section_type, diagonal_dims,
               top_chord_thickness, top_chord_section_type, top_chord_dims,
               bottom_chord_thickness, bottom_chord_section_type, bottom_chord_dims,
               bracket, skew_angle=0):
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
        flange_w: Flange width
        
        diagonal_thickness: Thickness of diagonal members
        diagonal_section_type: Section type for diagonal members
        diagonal_dims: Section dimensions for diagonal members
        
        top_chord_thickness: Thickness of top chord/bracket
        top_chord_section_type: Section type for top chord/bracket
        top_chord_dims: Section dimensions for top chord/bracket
        
        bottom_chord_thickness: Thickness of bottom chord/bracket
        bottom_chord_section_type: Section type for bottom chord/bracket
        bottom_chord_dims: Section dimensions for bottom chord/bracket
        
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
    
    # Create main X-diagonals using diagonal section
    braces = [
        # Left TOP → Right BOTTOM diagonal
        _create_diagonal_member(
            gp_Pnt(x_l, yL, z_top), 
            gp_Pnt(x_r, yR, z_bot),
            diagonal_thickness, diagonal_section_type, diagonal_dims, +1
        ),
        # Left BOTTOM → Right TOP diagonal
        _create_diagonal_member(
            gp_Pnt(x_l, yL, z_bot), 
            gp_Pnt(x_r, yR, z_top),
            diagonal_thickness, diagonal_section_type, diagonal_dims, -1
        )
    ]
    
    # Add optional bottom bracket using bottom chord section
    if bracket in ("LOWER", "BOTH"):
        braces.append(
            _create_diagonal_member(
                gp_Pnt(x_l, yL, z_bot), 
                gp_Pnt(x_r, yR, z_bot),
                bottom_chord_thickness, bottom_chord_section_type, bottom_chord_dims, +1
            )
        )
    
    # Add optional top bracket using top chord section
    if bracket in ("UPPER", "BOTH"):
        braces.append(
            _create_diagonal_member(
                gp_Pnt(x_l, yL, z_top), 
                gp_Pnt(x_r, yR, z_top),
                top_chord_thickness, top_chord_section_type, top_chord_dims, +1
            )
        )
    
    return braces


def _k_bracing(x, yL, yR, depth, tf, flange_w,
               diagonal_thickness, diagonal_section_type, diagonal_dims,
               top_chord_thickness, top_chord_section_type, top_chord_dims,
               bottom_chord_thickness, bottom_chord_section_type, bottom_chord_dims,
               top_bracket, skew_angle=0):
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
        flange_w: Flange width
        
        diagonal_thickness: Thickness of diagonal members
        diagonal_section_type: Section type for diagonal members
        diagonal_dims: Section dimensions for diagonal members
        
        top_chord_thickness: Thickness of top chord/bracket
        top_chord_section_type: Section type for top chord/bracket
        top_chord_dims: Section dimensions for top chord/bracket
        
        bottom_chord_thickness: Thickness of bottom chord/bracket
        bottom_chord_section_type: Section type for bottom chord/bracket
        bottom_chord_dims: Section dimensions for bottom chord/bracket
        
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
        # Left TOP → Middle BOTTOM diagonal (using diagonal section)
        _create_diagonal_member(
            gp_Pnt(x_l, yL, z_top), 
            gp_Pnt(x_m, ym, z_bot),
            diagonal_thickness, diagonal_section_type, diagonal_dims, +1
        ),
        # Right TOP → Middle BOTTOM diagonal (using diagonal section)
        _create_diagonal_member(
            gp_Pnt(x_r, yR, z_top), 
            gp_Pnt(x_m, ym, z_bot),
            diagonal_thickness, diagonal_section_type, diagonal_dims, -1
        ),
        # Bottom horizontal (mandatory for K-bracing, using bottom chord section)
        _create_diagonal_member(
            gp_Pnt(x_l, yL, z_bot), 
            gp_Pnt(x_r, yR, z_bot),
            bottom_chord_thickness, bottom_chord_section_type, bottom_chord_dims, +1
        )
    ]
    
    # Add optional top bracket using top chord section
    if top_bracket:
        braces.append(
            _create_diagonal_member(
                gp_Pnt(x_l, yL, z_top), 
                gp_Pnt(x_r, yR, z_top),
                top_chord_thickness, top_chord_section_type, top_chord_dims, +1
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
    girder_depths,          # Can be float (uniform) or List[List[float]] [panel_idx][girder_idx]
    reference_depth,        # Reference web depth for vertical alignment
    flange_thickness,
    flange_width,
    
    # Internal bracing configuration
    bracing_type,          # "X" or "K"
    
    # Diagonal member configuration
    diagonal_section_type,
    diagonal_section_dims,
    diagonal_thickness,
    
    # Top chord/bracket configuration
    top_chord_section_type,
    top_chord_section_dims,
    top_chord_thickness,
    
    # Bottom chord/bracket configuration
    bottom_chord_section_type,
    bottom_chord_section_dims,
    bottom_chord_thickness,
    
    # Spacing and options
    panel_spacing,         # Spacing between bracing frames
    bracket_option="BOTH", # For X-bracing: "NONE", "UPPER", "LOWER", "BOTH"
    top_bracket=False,     # For K-bracing: include top horizontal
    skew_angle=0,          # Bridge skew angle in degrees
    
    # End diaphragm configuration
    end_diaphragm_type="Cross Bracing",  # "Cross Bracing", "Rolled Beam", "Welded Beam"
    end_diaphragm_bracing_type=None,     # If None, use bracing_type
    
    # End diaphragm diagonal configuration
    end_diaphragm_diagonal_section_type=None,  # If None, error
    end_diaphragm_diagonal_section_dims=None,
    end_diaphragm_diagonal_thickness=None,
    
    # End diaphragm top chord configuration
    end_diaphragm_top_chord_section_type=None,
    end_diaphragm_top_chord_section_dims=None,
    end_diaphragm_top_chord_thickness=None,
    
    # End diaphragm bottom chord configuration
    end_diaphragm_bottom_chord_section_type=None,
    end_diaphragm_bottom_chord_section_dims=None,
    end_diaphragm_bottom_chord_thickness=None,
    
    # For Rolled/Welded beam diaphragms
    end_diaphragm_section="I_SECTION",
    end_diaphragm_dims=None,
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
            
            # Get girder depths for this bay
            if isinstance(girder_depths, (int, float)):
                d_L = girder_depths
                d_R = girder_depths
            else:
                # depths[panel_idx][girder_idx]
                d_L = girder_depths[idx_x][i]
                d_R = girder_depths[idx_x][i+1]
            
            # The smaller girder depth controls the bracing height
            eff_depth = min(d_L, d_R)
            
            # Calculate vertical offset to keep top flush with reference web top
            # reference_depth/2 is the Z-coord of the top of the reference web
            # eff_depth/2 is the Z-coord of the top of the bracing frame (at center)
            z_offset = (reference_depth - eff_depth) / 2.0
            
            def _apply_z_offset(shapes, dz):
                if not dz: return shapes
                trsf = gp_Trsf()
                trsf.SetTranslation(gp_Vec(0, 0, dz))
                return [BRepBuilderAPI_Transform(s, trsf, True).Shape() for s in shapes]

            # Check if this is an end position (first or last frame)
            is_end = (x == x_positions[0] or x == x_positions[-1])
            is_first = (x == x_positions[0])
            is_last = (x == x_positions[-1])
            
            # END DIAPHRAGM HANDLING
            if is_end:
                # Apply longitudinal offset for end diaphragms
                # Base offset from parameters or default
                base_offset = end_diaphragm_spacing if end_diaphragm_spacing > 0 else 200.0
                
                # Skew-aware adjustment:
                # Stiffeners are perpendicular to the girder axis (global Y in girder local coords).
                # Diaphragms are skewed (parallel to skew).
                # To clear the stiffener tip (which extends ~200mm from web), 
                # we need an extra shift equal to (stiffener_width * tan(skew)).
                
                # We use a hardcoded 200mm for stiffener width for now to match cad_generator defaults
                stiffener_width = 300.0
                skew_rad = math.radians(abs(skew_angle))
                extra_offset = stiffener_width * math.tan(skew_rad)
                
                offset = base_offset + extra_offset
                
                if is_first:
                    x_eff = x + offset
                else: # is_last
                    x_eff = x - offset

                if end_diaphragm_type == "Cross Bracing":
                    # Use end diaphragm section configurations
                    if end_diaphragm_bracing_type == "X":
                        frame = _x_bracing(
                                x_eff, yL, yR,
                                eff_depth, flange_thickness, flange_width,
                                end_diaphragm_diagonal_thickness,
                                end_diaphragm_diagonal_section_type,
                                end_diaphragm_diagonal_section_dims,
                                end_diaphragm_top_chord_thickness,
                                end_diaphragm_top_chord_section_type,
                                end_diaphragm_top_chord_section_dims,
                                end_diaphragm_bottom_chord_thickness,
                                end_diaphragm_bottom_chord_section_type,
                                end_diaphragm_bottom_chord_section_dims,
                                bracket_option,
                                skew_angle=skew_angle
                        )
                        bracings.extend(_apply_z_offset(frame, z_offset))
                    elif end_diaphragm_bracing_type == "K":
                        frame = _k_bracing(
                                x_eff, yL, yR,
                                eff_depth, flange_thickness, flange_width,
                                end_diaphragm_diagonal_thickness,
                                end_diaphragm_diagonal_section_type,
                                end_diaphragm_diagonal_section_dims,
                                end_diaphragm_top_chord_thickness,
                                end_diaphragm_top_chord_section_type,
                                end_diaphragm_top_chord_section_dims,
                                end_diaphragm_bottom_chord_thickness,
                                end_diaphragm_bottom_chord_section_type,
                                end_diaphragm_bottom_chord_section_dims,
                                top_bracket,
                                skew_angle=skew_angle
                        )
                        bracings.extend(_apply_z_offset(frame, z_offset))
                
                elif end_diaphragm_type == "Rolled Beam" or end_diaphragm_type == "Welded Beam":
                    # Use I-section for rolled beam diaphragm
                    diaphragm_dims = end_diaphragm_dims if end_diaphragm_dims is not None else {
                        "depth": eff_depth * 0.8,
                        "flange_width": 200,
                        "web_thickness": 10,
                        "flange_thickness": 15
                    }
                    
                    # Validate dimensions or use defaults (slightly larger than rolled)
                    if "depth" not in diaphragm_dims or "flange_width" not in diaphragm_dims:
                        diaphragm_dims = {
                            "depth": eff_depth * 0.85,  
                            "flange_width": 250,            
                            "web_thickness": 12,            
                            "flange_thickness": 20          
                        }
                    frame = _diaphragm_bracing(
                                x_eff, yL, yR,
                                eff_depth, flange_thickness,
                                end_diaphragm_thickness,
                                end_diaphragm_section,
                                end_diaphragm_dims,
                                skew_angle=skew_angle
                    )
                    bracings.extend(_apply_z_offset(frame, z_offset))
                
                continue
            
            # INTERNAL BRACING HANDLING
            # Build normal X or K bracing for internal panels using separate sections
            if bracing_type == "X":
                frame = _x_bracing(
                    x, yL, yR,
                    eff_depth, flange_thickness, flange_width,
                    diagonal_thickness, diagonal_section_type, diagonal_section_dims,
                    top_chord_thickness, top_chord_section_type, top_chord_section_dims,
                    bottom_chord_thickness, bottom_chord_section_type, bottom_chord_section_dims,
                    bracket_option,
                    skew_angle=skew_angle
                )
                bracings.extend(_apply_z_offset(frame, z_offset))
            
            elif bracing_type == "K":
                frame = _k_bracing(
                    x, yL, yR,
                    eff_depth, flange_thickness, flange_width,
                    diagonal_thickness, diagonal_section_type, diagonal_section_dims,
                    top_chord_thickness, top_chord_section_type, top_chord_section_dims,
                    bottom_chord_thickness, bottom_chord_section_type, bottom_chord_section_dims,
                    top_bracket,
                    skew_angle=skew_angle
                )
                bracings.extend(_apply_z_offset(frame, z_offset))
    
    return bracings