"""

- Contains geometry creation
- Contains placement logic
- Contains footpath-based positioning logic
"""

from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Trsf, gp_Dir, gp_Ax2
from OCC.Core.BRepBuilderAPI import (
    BRepBuilderAPI_MakePolygon,
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_Transform
)
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism


# Utility transforms

def translate(shape, x=0, y=0, z=0):
    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(x, y, z))
    return BRepBuilderAPI_Transform(shape, trsf, True).Shape()


def mirror_y(shape):
    trsf = gp_Trsf()
    trsf.SetMirror(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(0, 1, 0)))
    return BRepBuilderAPI_Transform(shape, trsf, True).Shape()


# Crash barrier geometry

def create_crash_barrier_left(
    length,
    width,
    height,
    base_width
):
    """
    Creates LEFT crash barrier solid aligned along +X
    """

    base_h = 100.0
    slope_mid_z = 325.0

    z0 = 0.0
    z1 = base_h
    z2 = slope_mid_z
    z3 = height

    y_left_base = -base_width / 2.0
    y_right_base = base_width / 2.0

    y_left_top = -width / 2.0
    y_right_top = width / 2.0

    mid_width = 250.0
    y_right_mid = mid_width / 2.0

    # Profile (YZ plane)
    p1 = gp_Pnt(0, y_right_base, z0)
    p2 = gp_Pnt(0, y_left_base, z0)

    p3 = gp_Pnt(0, y_left_base, z1)
    p4 = gp_Pnt(0, y_left_top, z3)

    p5 = gp_Pnt(0, y_right_top, z3)
    p6 = gp_Pnt(0, y_right_mid, z2)
    p7 = gp_Pnt(0, y_right_mid, z2)
    p8 = gp_Pnt(0, y_right_base, z1)

    poly = BRepBuilderAPI_MakePolygon()
    for p in (p1, p2, p3, p4, p5, p6, p7, p8):
        poly.Add(p)
    poly.Close()

    face = BRepBuilderAPI_MakeFace(poly.Wire()).Face()

    return BRepPrimAPI_MakePrism(
        face,
        gp_Vec(length, 0, 0)
    ).Shape()


def create_crash_barrier_right(
    length,
    width,
    height,
    base_width
):
    return mirror_y(
        create_crash_barrier_left(
            length, width, height, base_width
        )
    )



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
        return (footpath_width + railing_width) / 2.0

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
    crash_barrier_width,
    crash_barrier_height,
    crash_barrier_base_width,
    footpath_width,
    railing_width
):
    """
    Returns list of crash barrier shapes
    """

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

        y_r = deck_half - crash_barrier_base_width / 2.0
        y_l = -deck_half + crash_barrier_base_width / 2.0

    # LEFT footpath
    elif footpath_config == "LEFT":

        y_r = deck_half - crash_barrier_base_width / 2.0
        y_l = cw_left - crash_barrier_base_width / 2.0

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

    # Right barrier
    crash_barriers.append(
        translate(
            create_crash_barrier_right(
                span_length_L,
                crash_barrier_width,
                crash_barrier_height,
                crash_barrier_base_width
            ),
            y=y_r,
            z=deck_top_z
        )
    )

    # Left barrier
    crash_barriers.append(
        translate(
            create_crash_barrier_left(
                span_length_L,
                crash_barrier_width,
                crash_barrier_height,
                crash_barrier_base_width
            ),
            y=y_l,
            z=deck_top_z
        )
    )

    return crash_barriers
