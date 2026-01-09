from osdagbridge.core.utils.codes.irc5_2015 import IRC5_2015
from osdagbridge.core.utils.common import (
    KEY_CRASH_BARRIER_TYPE,
    KEY_FOOTPATH,
    KEY_METALLIC_CRASH_BARRIER_TYPE,
    KEY_MEDIAN_TYPE,
    KEY_RIGID_CRASH_BARRIER_TYPE,
    KEY_RAILING_TYPE
)

#  BASIC AREA UTILITIES

def trapezoidal_area(top_w, bottom_w, height):
    return ((top_w + bottom_w) / 2) * height

def rectangular_area(width, height):
    return width * height

def post_and_spacer_area(section_area, post_height, spacer_height, spacing):
    return section_area * (post_height + spacer_height) / spacing

def w_beam_area(thickness, dev_length, n):
    return n * thickness * dev_length
# FIG 5(a)

def median_raised_kerb_area():

    geom = IRC5_2015.cl_109_6_3_shapes(
        barrier_type=KEY_MEDIAN_TYPE[0],
        footpath=None,
        railing_type=None,
        design_dict={},
        crash_barrier_type=None
    )

    kerb_area = trapezoidal_area(
        geom['kerb_top_width'],
        geom['kerb_bottom_width'],
        geom['kerb_height']
    )

    return {
        "type": "Raised Kerb",
        "kerb_area": kerb_area
    }


# FIG 5(b)

def median_rcc_barrier_area():

    geom = IRC5_2015.cl_109_6_3_shapes(
        barrier_type=KEY_MEDIAN_TYPE[1],
        footpath=None,
        railing_type=None,
        design_dict={},
        crash_barrier_type=None
    )

    barrier_area = trapezoidal_area(
        geom['barrier_top_width'],
        geom['barrier_bottom_width'],
        geom['barrier_height']
    )

    kerb_area = trapezoidal_area(
        geom['kerb_top_width'],
        geom['kerb_bottom_width'],
        geom['kerb_height']
    )

    return {
        "type": "RCC Crash Barrier",
        "rcc_barrier_area": barrier_area,
        "kerb_area": kerb_area
    }

# FIG 5 (C)

def median_metallic_barrier_area(barrier_type):
    """
    barrier_type:
        "Single"  → Single W-beam
        "Double"  → Double W-beam
    """

    if barrier_type == "Double":
        cb_type = KEY_METALLIC_CRASH_BARRIER_TYPE[1]   # Double W-beam
    else:
        cb_type = KEY_METALLIC_CRASH_BARRIER_TYPE[0]   # Single W-beam

    geom = IRC5_2015.cl_109_6_3_shapes(
        barrier_type=KEY_MEDIAN_TYPE[2],   # Metallic Median
        footpath=None,
        railing_type=None,
        design_dict={},
        crash_barrier_type=cb_type
    )

    kerb_area = trapezoidal_area(
        geom['kerb_top_width'],
        geom['kerb_bottom_width'],
        geom['kerb_height']
    )

    post_area = post_and_spacer_area(
        geom['post_section_area'],
        geom['post_height'],
        geom['spacer_height'],
        geom['post_spacing']
    )

    beam_area = w_beam_area(
        geom['w_beam_thickness'],
        geom['w_beam_developed_length'],
        geom['number_of_w_beams']
    )

    return {
        "type": f"Median Metallic Barrier ({barrier_type})",
        "steel_area": post_area + beam_area,
        "kerb_area": kerb_area
    }