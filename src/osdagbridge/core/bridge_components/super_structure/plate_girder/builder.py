"""
Plate girder builder.

- I-section geometry
- stiffener geometry
- girder + stiffener assembly

"""

# OCC imports

from OCC.Core.gp import gp_Vec, gp_Trsf
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform


# I-SECTION GEOMETRY

def create_i_section(
    length,
    width,
    depth,
    flange_thickness,
    web_thickness
):
    """
    Create an I-section CAD solid aligned along +X axis.
    """

    web_height = depth - 2 * flange_thickness

    # Bottom flange
    bottom_flange = BRepPrimAPI_MakeBox(
        length, width, flange_thickness
    ).Shape()

    # Top flange
    top_flange = BRepPrimAPI_MakeBox(
        length, width, flange_thickness
    ).Shape()

    trsf = gp_Trsf()
    trsf.SetTranslation(
        gp_Vec(0, 0, depth - flange_thickness)
    )
    top_flange = BRepBuilderAPI_Transform(
        top_flange, trsf, True
    ).Shape()

    # Web
    web = BRepPrimAPI_MakeBox(
        length,
        web_thickness,
        web_height
    ).Shape()

    trsf = gp_Trsf()
    trsf.SetTranslation(
        gp_Vec(
            0,
            (width - web_thickness) / 2,
            flange_thickness
        )
    )
    web = BRepBuilderAPI_Transform(
        web, trsf, True
    ).Shape()

    # Fuse
    section = BRepAlgoAPI_Fuse(
        bottom_flange, top_flange
    ).Shape()
    section = BRepAlgoAPI_Fuse(
        section, web
    ).Shape()

    return section


# STIFFENER GEOMETRY

def _translate(shape, dx=0, dy=0, dz=0):
    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(dx, dy, dz))
    return BRepBuilderAPI_Transform(
        shape, trsf, True
    ).Shape()


def create_girder_stiffeners(
    *,
    girder_depth,
    girder_flange_thickness,
    girder_web_thickness,
    girder_flange_width,
    stiffener_width,
    stiffener_length,
    x_offset=0.0
):
    """
    Create LEFT and RIGHT web stiffeners
    consistent with create_i_section().
    """

    stiffener_height = (
        girder_depth - 2 * girder_flange_thickness
    )

    plate = BRepPrimAPI_MakeBox(
        stiffener_length,
        stiffener_width,
        stiffener_height
    ).Shape()

    z_offset = girder_flange_thickness

    web_left_y = (
        girder_flange_width - girder_web_thickness
    ) / 2
    web_right_y = web_left_y + girder_web_thickness

    left = _translate(
        plate,
        dx=x_offset,
        dy=web_left_y - stiffener_width,
        dz=z_offset
    )

    right = _translate(
        plate,
        dx=x_offset,
        dy=web_right_y,
        dz=z_offset
    )

    return left, right


# GIRDER ASSEMBLY

def build_girders(
    *,
    span_length_L,
    girder_section_d,
    girder_section_bf,
    girder_section_tf,
    girder_section_tw,
    num_girders,
    girder_spacing,
    stiffener_width,
    stiffener_length
):
    """
    Builds girders symmetrically about centerline
    and places stiffeners at both ends.
    """

    girders = []
    stiffeners = []

    total_width = (num_girders - 1) * girder_spacing

    for i in range(num_girders):

        # 1. Girder
        girder = create_i_section(
            span_length_L,
            girder_section_bf,
            girder_section_d,
            girder_section_tf,
            girder_section_tw
        )

        # 2. Stiffeners (start)
        s_l, s_r = create_girder_stiffeners(
            girder_depth=girder_section_d,
            girder_flange_width=girder_section_bf,
            girder_web_thickness=girder_section_tw,
            girder_flange_thickness=girder_section_tf,
            stiffener_width=stiffener_width,
            stiffener_length=stiffener_length,
            x_offset=0.0
        )

        # 3. Stiffeners (end)
        e_l, e_r = create_girder_stiffeners(
            girder_depth=girder_section_d,
            girder_flange_width=girder_section_bf,
            girder_web_thickness=girder_section_tw,
            girder_flange_thickness=girder_section_tf,
            stiffener_width=stiffener_width,
            stiffener_length=stiffener_length,
            x_offset=span_length_L - stiffener_length
        )

        local_stiffeners = [s_l, s_r, e_l, e_r]

        # 4. Y placement
        y_offset = (i * girder_spacing) - (total_width / 2)

        trsf = gp_Trsf()
        trsf.SetTranslation(gp_Vec(0, y_offset, 0))

        girders.append(
            BRepBuilderAPI_Transform(
                girder, trsf, True
            ).Shape()
        )

        for stiff in local_stiffeners:
            stiffeners.append(
                BRepBuilderAPI_Transform(
                    stiff, trsf, True
                ).Shape()
            )

    return girders, stiffeners
