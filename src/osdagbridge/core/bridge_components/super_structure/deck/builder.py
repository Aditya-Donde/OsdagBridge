"""
Deck builder.

- Deck slab geometry
- Deck texture geometry
- Deck width logic

"""

# OCC imports

from OCC.Core.BRepPrimAPI import (
    BRepPrimAPI_MakeBox,
    BRepPrimAPI_MakeCylinder,
    BRepPrimAPI_MakePrism
)
from OCC.Core.BRepBuilderAPI import (
    BRepBuilderAPI_Transform,
    BRepBuilderAPI_MakePolygon,
    BRepBuilderAPI_MakeFace
)
from OCC.Core.gp import (
    gp_Vec, gp_Trsf, gp_Pnt,
    gp_Ax1, gp_Dir
)

import random
import math


# Constants 

DOT_RADIUS = 6
DOT_HEIGHT = 3

TRI_SIZE_MAX = 120
TRI_HEIGHT = 0.4

EDGE_GAP = 15
Z_GAP = 15


# Utility

def _translate(shape, x=0, y=0, z=0):
    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(x, y, z))
    return BRepBuilderAPI_Transform(shape, trsf, True).Shape()


# Deck width logic

def calculate_deck_width(
    *,
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


# Deck slab geometry

def _create_deck_slab(
    *,
    span_length,
    deck_width,
    deck_thickness,
    girder_depth
):
    slab = BRepPrimAPI_MakeBox(
        span_length,
        deck_width,
        deck_thickness
    ).Shape()

    # center X and Y, bottom at Z=0
    slab = _translate(
        slab,
        -span_length / 2,
        -deck_width / 2,
        0
    )

    # move to final position
    return _translate(
        slab,
        span_length / 2,
        0,
        girder_depth
    )


# Texture primitives (exact logic from deck_texture.py)

def _create_dot(x, y, z):
    dot = BRepPrimAPI_MakeCylinder(DOT_RADIUS, DOT_HEIGHT).Shape()
    return _translate(dot, x, y, z)


def _create_dot_z(x, y, z, up=True):
    h = DOT_HEIGHT if up else -DOT_HEIGHT
    dot = BRepPrimAPI_MakeCylinder(DOT_RADIUS, abs(h)).Shape()
    return _translate(dot, x, y, z)


def _create_triangle(x, y, z, rot_axis=None, rot_angle=0):
    size = random.uniform(80, TRI_SIZE_MAX)

    p1 = gp_Pnt(0, 0, 0)
    p2 = gp_Pnt(size, random.uniform(10, size), 0)
    p3 = gp_Pnt(random.uniform(10, size), size, 0)

    poly = BRepBuilderAPI_MakePolygon()
    poly.Add(p1)
    poly.Add(p2)
    poly.Add(p3)
    poly.Close()

    face = BRepBuilderAPI_MakeFace(poly.Wire()).Face()
    prism = BRepPrimAPI_MakePrism(
        face, gp_Vec(0, 0, TRI_HEIGHT)
    ).Shape()

    prism = _translate(
        prism,
        -size / 2,
        -size / 2,
        -TRI_HEIGHT / 2
    )

    trsf = gp_Trsf()
    if rot_axis:
        trsf.SetRotation(rot_axis, rot_angle)
    trsf.SetTranslationPart(gp_Vec(x, y, z))

    return BRepBuilderAPI_Transform(prism, trsf, True).Shape()


def _create_triangle_xy(x, y, z, up=True):
    size = random.uniform(80, TRI_SIZE_MAX)

    p1 = gp_Pnt(0, 0, 0)
    p2 = gp_Pnt(size, random.uniform(10, size), 0)
    p3 = gp_Pnt(random.uniform(10, size), size, 0)

    poly = BRepBuilderAPI_MakePolygon()
    poly.Add(p1)
    poly.Add(p2)
    poly.Add(p3)
    poly.Close()

    face = BRepBuilderAPI_MakeFace(poly.Wire()).Face()
    h = TRI_HEIGHT if up else -TRI_HEIGHT

    prism = BRepPrimAPI_MakePrism(
        face, gp_Vec(0, 0, h)
    ).Shape()

    return _translate(prism, x - size / 2, y - size / 2, z)



def _generate_deck_texture(
    *,
    deck_length,
    deck_width,
    deck_thickness,
    deck_top_z
):
    elements = []

    z_min = Z_GAP
    z_max = deck_thickness - Z_GAP - max(DOT_HEIGHT, TRI_HEIGHT)

    # FRONT & BACK (Y faces)
    rot_y = gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(1, 0, 0))

    for y in (0.2, deck_width - 0.2):
        for _ in range(120):
            elements.append(
                _create_dot(
                    random.uniform(EDGE_GAP, deck_length - EDGE_GAP),
                    y,
                    random.uniform(z_min, z_max)
                )
            )

        for _ in range(15):
            elements.append(
                _create_triangle(
                    random.uniform(EDGE_GAP, deck_length - EDGE_GAP),
                    y,
                    random.uniform(z_min, z_max),
                    rot_y,
                    math.pi / 2
                )
            )

    # LEFT & RIGHT (X faces)
    rot_x = gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 1, 0))

    for x in (0.2, deck_length - 0.2):
        for _ in range(100):
            elements.append(
                _create_dot(
                    x,
                    random.uniform(EDGE_GAP, deck_width - EDGE_GAP),
                    random.uniform(z_min, z_max)
                )
            )

        for _ in range(20):
            elements.append(
                _create_triangle(
                    x,
                    random.uniform(EDGE_GAP, deck_width - EDGE_GAP),
                    random.uniform(z_min, z_max),
                    rot_x,
                    -math.pi / 2
                )
            )

    # TOP & BOTTOM
    for z, up in (
        (deck_thickness - 0.2, True),
        (0.2, False)
    ):
        for _ in range(150):
            elements.append(
                _create_dot_z(
                    random.uniform(EDGE_GAP, deck_length - EDGE_GAP),
                    random.uniform(EDGE_GAP, deck_width - EDGE_GAP),
                    z,
                    up
                )
            )

        for _ in range(50):
            elements.append(
                _create_triangle_xy(
                    random.uniform(EDGE_GAP, deck_length - EDGE_GAP),
                    random.uniform(EDGE_GAP, deck_width - EDGE_GAP),
                    z,
                    up
                )
            )

    # Center in Y
    elements = [
        _translate(e, 0, -deck_width / 2, 0)
        for e in elements
    ]

    # Lift to deck position
    elements = [
        _translate(e, 0, 0, deck_top_z - deck_thickness)
        for e in elements
    ]

    return elements



def build_deck(
    *,
    span_length_L,
    girder_section_d,
    deck_thickness,

    footpath_config,
    carriageway_width,
    crash_barrier_base_width,
    footpath_width,
    railing_width
):
    total_deck_width = calculate_deck_width(
        footpath_config=footpath_config,
        carriageway_width=carriageway_width,
        crash_barrier_base_width=crash_barrier_base_width,
        footpath_width=footpath_width,
        railing_width=railing_width
    )

    deck_slab = _create_deck_slab(
        span_length=span_length_L,
        deck_width=total_deck_width,
        deck_thickness=deck_thickness,
        girder_depth=girder_section_d
    )

    deck_top_z = girder_section_d + deck_thickness

    deck_textures = _generate_deck_texture(
        deck_length=span_length_L,
        deck_width=total_deck_width,
        deck_thickness=deck_thickness,
        deck_top_z=deck_top_z
    )

    return {
        "deck_slab": deck_slab,
        "deck_textures": deck_textures,
        "deck_top_z": deck_top_z,
        "total_deck_width": total_deck_width
    }
