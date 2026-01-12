
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCC.Core.gp import gp_Trsf, gp_Vec
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse


# Utilities

def translate(shape, x=0, y=0, z=0):
    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(x, y, z))
    return BRepBuilderAPI_Transform(shape, trsf, True).Shape()


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


# Geometry

def create_railing(length, width, height, rail_count):
    BASE_HEIGHT = 100

    body_height = height - BASE_HEIGHT
    if body_height <= 0:
        raise ValueError("Railing height must be > base height")

    base = create_rectangular_prism(length, width, BASE_HEIGHT)

    body = create_rectangular_prism(length, width, body_height)
    body = translate(body, z=BASE_HEIGHT)

    HOLE_LENGTH_RATIO = 1
    HOLE_WIDTH_RATIO = 0.6
    HOLE_HEIGHT_RATIO = 0.5
    HOLE_Y_OFFSET_RATIO = -0.2

    hole_length = HOLE_LENGTH_RATIO * length
    hole_width = HOLE_WIDTH_RATIO * width
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
            y=(width - hole_width) / 2 + HOLE_Y_OFFSET_RATIO * width,
            z=z_center - hole_height / 2
        )

        body_with_holes = BRepAlgoAPI_Cut(
            body_with_holes, hole
        ).Shape()

    return BRepAlgoAPI_Fuse(base, body_with_holes).Shape()


def build_railings(
    *,
    span_length,
    deck_top_z,
    total_deck_width,
    footpath_config,
    railing_width,
    railing_height,
    rail_count
):

    if footpath_config == "NONE":
        return []

    railing_proto = create_railing(
        length=span_length,
        width=railing_width,
        height=railing_height,
        rail_count=rail_count
    )

    deck_half = total_deck_width / 2.0
    railings = []

    if footpath_config in ("LEFT", "BOTH"):
        railings.append(
            translate(
                railing_proto,
                y=-deck_half + railing_width / 2.0,
                z=deck_top_z
            )
        )

    if footpath_config in ("RIGHT", "BOTH"):
        railings.append(
            translate(
                railing_proto,
                y=deck_half - railing_width / 2.0,
                z=deck_top_z
            )
        )

    return railings
