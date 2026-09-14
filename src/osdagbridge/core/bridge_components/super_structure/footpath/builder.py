"""
Author: Om Pathania
Creates footpath slabs.

The footpath builds its own base outboard of the deck edge — the deck is the
carriageway plus its crash barriers — and carries the railing on its outer
edge.  It is the same concrete as the deck slab and springs from the same
level (the deck soffit, i.e. the top of the girders), but its thickness is
driven by Additional Inputs > Typical Section > Footpath Thickness: thicker
than the deck slab means the footpath stands proud of the carriageway,
thinner means it steps down.
"""
from osdagbridge.core.bridge_components.super_structure.footpath.geometry import (
    footpath_y_ranges,
)
# The footpath is the same concrete as the deck, finish included.
from osdagbridge.core.bridge_components.super_structure.deck.builder import (
    _generate_deck_texture,
)
from OCC.Core.gp import gp_Trsf, gp_Vec, gp_Pnt
from OCC.Core.BRepBuilderAPI import (
    BRepBuilderAPI_Transform,
    BRepBuilderAPI_MakePolygon,
    BRepBuilderAPI_MakeFace
)
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism
import math


def _translate(shape, x=0.0, y=0.0, z=0.0):
    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(x, y, z))
    return BRepBuilderAPI_Transform(shape, trsf, True).Shape()


def create_footpath_slab(
    *,
    length,
    y_start,
    y_end,
    thickness,
    z_bottom,
    skew_angle=0
):
    """
    Creates one footpath slab: a full-length prism between two Y offsets.

    Uses the same plan-view convention as the deck slab — X runs
    0 -> length, sheared by the skew angle about Y = 0.
    """
    tan_skew = math.tan(math.radians(skew_angle)) if skew_angle else 0.0

    shift_start = y_start * tan_skew
    shift_end = y_end * tan_skew

    poly = BRepBuilderAPI_MakePolygon()
    poly.Add(gp_Pnt(shift_start, y_start, 0))
    poly.Add(gp_Pnt(length + shift_start, y_start, 0))
    poly.Add(gp_Pnt(length + shift_end, y_end, 0))
    poly.Add(gp_Pnt(shift_end, y_end, 0))
    poly.Close()

    face = BRepBuilderAPI_MakeFace(poly.Wire()).Face()
    slab = BRepPrimAPI_MakePrism(face, gp_Vec(0, 0, thickness)).Shape()

    return _translate(slab, 0, 0, z_bottom)


def build_footpaths(
    *,
    span_length_L,
    girder_section_d,
    deck_thickness,
    deck_width,
    footpath_config,
    footpath_width,
    footpath_thickness,
    railing_width,
    skew_angle=0
):
    """
    Returns the footpath slabs and the Z level of the walking surface.

    Parameters
    ----------
    girder_section_d : float
        Girder depth — the deck soffit, which the footpath springs from.
    deck_width : float
        Width of the deck slab (carriageway + crash barriers); the footpaths
        sit outboard of its edges.
    footpath_thickness : float
        Footpath slab thickness in mm, measured from the deck soffit.

    Returns
    -------
    dict
        footpath_slabs : list of TopoDS_Shape (one per footpath)
        footpath_top_z : Z of the walking surface; the railing sits here.
                         Falls back to the deck top when there is no footpath.
        footpath_y_ranges : (y_start, y_end) per footpath, for railing placement
    """
    deck_top_z = girder_section_d + deck_thickness

    y_ranges = footpath_y_ranges(
        footpath_config=footpath_config,
        deck_width=deck_width,
        footpath_width=footpath_width,
        railing_width=railing_width
    )

    if not y_ranges or footpath_thickness <= 0:
        return {
            "footpath_slabs": [],
            "footpath_textures": [],
            "footpath_top_z": deck_top_z,
            "footpath_y_ranges": []
        }

    footpath_top_z = girder_section_d + footpath_thickness
    tan_skew = math.tan(math.radians(skew_angle)) if skew_angle else 0.0

    footpath_slabs = []
    footpath_textures = []

    for y_start, y_end in y_ranges:
        footpath_slabs.append(
            create_footpath_slab(
                length=span_length_L,
                y_start=y_start,
                y_end=y_end,
                thickness=footpath_thickness,
                z_bottom=girder_section_d,
                skew_angle=skew_angle
            )
        )

        # Same concrete finish as the deck slab.  The texture is generated
        # centred on Y = 0, so shift it onto this footpath — following the
        # skew shear, as the slab itself does.
        y_centre = (y_start + y_end) / 2.0
        footpath_textures.extend(
            _translate(element, y_centre * tan_skew, y_centre, 0)
            for element in _generate_deck_texture(
                deck_length=span_length_L,
                deck_width=y_end - y_start,
                deck_thickness=footpath_thickness,
                deck_top_z=footpath_top_z,
                skew_angle=skew_angle
            )
        )

    return {
        "footpath_slabs": footpath_slabs,
        "footpath_textures": footpath_textures,
        "footpath_top_z": footpath_top_z,
        "footpath_y_ranges": y_ranges
    }
