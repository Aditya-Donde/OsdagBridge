
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCC.Core.gp import gp_Trsf, gp_Vec, gp_Ax2, gp_Pnt, gp_Dir
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse


# Utilities

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


def create_rectangular_prism(length, breadth, height):
    """
    Aligned with crash barrier:
    X: 0 → +length
    Y: -breadth/2 → +breadth/2
    Z: 0 → height
    """
    box = BRepPrimAPI_MakeBox(length, breadth, height).Shape()

    trsf = gp_Trsf()
    trsf.SetTranslation(
        gp_Vec(0.0, -breadth / 2.0, 0.0)
    )

    return BRepBuilderAPI_Transform(box, trsf, True).Shape()


def create_cylinder(radius, height):
    """
    Creates a cylinder centered at origin, extending along Z-axis.
    X, Y: centered at 0
    Z: 0 → height
    """
    cylinder = BRepPrimAPI_MakeCylinder(radius, height).Shape()
    return cylinder


# Geometry

def create_rcc_railing(
    *,
    length,
    design_dict,
    side="LEFT"
):

    railing_width = 275 # 
    railing_height = design_dict.get("railing_height")
    if railing_height is None:
        railing_height = 1100
    
    # We can hardcode rail_count for RCC if standard, or get from somewhere.
    # IRC5 RCC is typically 3 rails (including top).
    rail_count = 3 

    BASE_HEIGHT = 100

    body_height = railing_height - BASE_HEIGHT
    if body_height <= 0:
        raise ValueError("Railing height must be > base height")

    base = create_rectangular_prism(length, railing_width, BASE_HEIGHT)

    body = create_rectangular_prism(length, railing_width, body_height)
    body = translate(body, z=BASE_HEIGHT)

    HOLE_LENGTH_RATIO = 1
    HOLE_WIDTH_RATIO = 0.6
    HOLE_HEIGHT_RATIO = 0.5
    HOLE_Y_OFFSET_RATIO = -0.2

    hole_length = HOLE_LENGTH_RATIO * length
    hole_width = HOLE_WIDTH_RATIO * railing_width
    hole_height = HOLE_HEIGHT_RATIO * (body_height / rail_count)

    spacing = body_height / (rail_count + 1)
    body_with_holes = body

    for i in range(rail_count):
        z_center = BASE_HEIGHT + (i + 1) * spacing

        hole = create_rectangular_prism(
            hole_length, hole_width, hole_height
        )

        hole = translate(
            hole,
            x=(length - hole_length) / 2,
            y=(railing_width - hole_width) / 2 + HOLE_Y_OFFSET_RATIO * railing_width,
            z=z_center - hole_height / 2
        )

        body_with_holes = BRepAlgoAPI_Cut(
            body_with_holes, hole
        ).Shape()

    final_shape = BRepAlgoAPI_Fuse(base, body_with_holes).Shape()
    
    # For RCC railing (rectangular usually), mirroring Y might not change much unless Holes are asymmetric.
    # Holes are offset by HOLE_Y_OFFSET_RATIO (-0.2 * width).
    # So yes, we should mirror if RIGHT side.
    
    if side == "RIGHT":
        final_shape = mirror_y(final_shape)
        
    return final_shape


def create_steel_railing(
    *,
    length,
    design_dict,
    side="LEFT"
):
    """
    Creates a steel railing with posts and rails on a concrete base.
    aligned with typical railing coordinate system.
    """
    railing_width = 200
    railing_height = design_dict.get("railing_height")
    if railing_height is None:
        railing_height = 1100

    # Concrete base dimensions
    BASE_HEIGHT = 100  # 100mm height as per IRC standards
    BASE_WIDTH = 375   # 375mm width for concrete base
    
    # Create concrete base with 375mm width
    base = create_rectangular_prism(length, BASE_WIDTH, BASE_HEIGHT)
    
    # Parameters for steel railing (sits on top of base)
    POST_DIAMETER = 150  # Circular post diameter in mm
    POST_RADIUS = POST_DIAMETER / 2.0
    POST_SPACING = 1000
    RAIL_SIZE = 80
    
    # Posts height (from top of base to top of railing)
    post_height = railing_height - BASE_HEIGHT
    
    # Calculate number of gaps  
    # Safe length for posts center-to-beginning
    effective_length = length - POST_DIAMETER
    if effective_length < 0:
        effective_length = 0
        
    num_spaces = int(effective_length / POST_SPACING)
    if num_spaces < 1:
        num_spaces = 1
    
    actual_spacing = effective_length / num_spaces
    
    posts_shape = None
    
    # Create circular posts (starting from top of base)
    # We need num_spaces + 1 posts to cover 0 to effective_length
    for i in range(num_spaces + 1):
        x = i * actual_spacing + POST_RADIUS  # Center the cylinder at x position
        
        # Clamp x to be safe 
        if x > length - POST_RADIUS:
            x = length - POST_RADIUS
            
        # Create cylindrical post
        post = create_cylinder(POST_RADIUS, post_height)
        post = translate(post, x=x, z=BASE_HEIGHT)
        
        if posts_shape is None:
            posts_shape = post
        else:
            posts_shape = BRepAlgoAPI_Fuse(posts_shape, post).Shape()

    # Rails (positioned relative to total railing height)
    # Top Rail
    top_rail = create_rectangular_prism(length, RAIL_SIZE, RAIL_SIZE)
    top_rail = translate(top_rail, z=railing_height - 2 * RAIL_SIZE)
    
    # Mid Rail
    mid_rail = create_rectangular_prism(length, RAIL_SIZE, RAIL_SIZE)
    mid_rail = translate(mid_rail, z=BASE_HEIGHT + (post_height * 0.5))

    rails_fused = BRepAlgoAPI_Fuse(top_rail, mid_rail).Shape()
    
    # Combine all components
    if posts_shape:
        steel_structure = BRepAlgoAPI_Fuse(posts_shape, rails_fused).Shape()
    else:
        steel_structure = rails_fused
    
    # Fuse concrete base with steel structure
    final_shape = BRepAlgoAPI_Fuse(base, steel_structure).Shape()
    
    if side == "RIGHT":
         final_shape = mirror_y(final_shape)
         
    return final_shape


def build_railings(
    *,
    span_length,
    deck_top_z,
    total_deck_width,
    footpath_config,
    design_dict,
    skew_angle=0
):
    import math

    if footpath_config == "NONE":
        return []

    # Extract railing type from design_dict (populated by IRC5 logic)
    # Default to RCC if not found
    railing_type = design_dict.get("railing_type", "RCC")
    
    # Use the actual base width for positioning
    if railing_type == "steel":
        railing_width = 375  # Steel railing base width
    else:
        railing_width = 275  # RCC railing width

    deck_half = total_deck_width / 2.0
    railings = []

    # Helper to create correct type
    def create_shape(side):
        if railing_type == "steel":
            return create_steel_railing(length=span_length, design_dict=design_dict, side=side)
        else:
            return create_rcc_railing(length=span_length, design_dict=design_dict, side=side)

    # SKEW OFFSET CALCULATION
    def get_skew_x(y):
        if skew_angle == 0:
            return 0.0
        return y * math.tan(math.radians(skew_angle))

    # Placement Logic
    # Left Railing:
    # Center Y = -deck_half + width/2
    if footpath_config in ("LEFT", "BOTH"):
        shape = create_shape("LEFT")
        y_pos = -deck_half + railing_width / 2.0
        railings.append(
            translate(
                shape,
                x=get_skew_x(y_pos),
                y=y_pos,
                z=deck_top_z
            )
        )

    # Right Railing:
    # Center Y = +deck_half - width/2
    if footpath_config in ("RIGHT", "BOTH"):
        shape = create_shape("RIGHT")
        y_pos = deck_half - railing_width / 2.0
        railings.append(
            translate(
                shape,
                x=get_skew_x(y_pos),
                y=y_pos,
                z=deck_top_z
            )
        )

    return railings
