import math
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

def circular_segment_area(R, theta):
    """Area of circular segment: (R²/2)(theta - sin theta), theta in radians"""
    return 0.5 * R**2 * (theta - math.sin(theta))
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
        barrier_type=KEY_MEDIAN_TYPE[1],   # RCC Crash Barrier
        footpath=None,
        railing_type=None,
        design_dict={},
        crash_barrier_type=None
    )

    # Static dims from IRC5 
    H  = geom["barrier_height"]          # 900
    Wt = geom["barrier_top_width"]       # 175
    Wb = geom["barrier_bottom_width"]    # 450

    kerb_h  = geom["kerb_height"]        # 100
    kerb_wt = geom["kerb_top_width"]     # 500
    kerb_wb = geom["kerb_bottom_width"]  # 550

    R1 = geom.get("crash_barrier_radius1", 50)     # 50
    R2 = geom.get("crash_barrier_radius2", 250)    # 250

    h1 = 550
    h2 = 250
    h3 = H - h1 - h2   # should become 100

    W1_top = Wt               # 175
    W1_bot = Wt + 50          # 225

    W2_top = W1_bot           # 225
    W2_bot = Wb               # 450

    W3_top = Wb               # 450
    W3_bot = Wb               # 450

    A1 = trapezoidal_area(W1_top, W1_bot, h1)
    A2 = trapezoidal_area(W2_top, W2_bot, h2)
    A3 = trapezoidal_area(W3_top, W3_bot, h3)


    # Here we assume 90° curves for first version → theta = pi/2
    # If you want exact theta, we can compute using your derived tan formula.
    theta1 = math.pi / 2
    theta2 = math.pi / 2

    curve_R50  = circular_segment_area(R1, theta1)
    curve_R250 = circular_segment_area(R2, theta2)

    # barrier body area for ONE barrier
    barrier_area_single = A1 + A2 + A3 + curve_R50 + curve_R250

    # Kerb area 
    kerb_area_single = trapezoidal_area(kerb_wt, kerb_wb, kerb_h)

    return {
        "type": "Median RCC Crash Barrier (Fig 5b)",
        "rcc_barrier_area_single": barrier_area_single,
        "kerb_area_single": kerb_area_single,
        "rcc_barrier_area_total": 2 * barrier_area_single,
        "kerb_area_total": 2 * kerb_area_single
    }


# def median_rcc_barrier_area():

#     geom = IRC5_2015.cl_109_6_3_shapes(
#         barrier_type=KEY_MEDIAN_TYPE[1],
#         footpath=None,
#         railing_type=None,
#         design_dict={},
#         crash_barrier_type=None
#     )

#     barrier_area = trapezoidal_area(
#         geom['barrier_top_width'],
#         geom['barrier_bottom_width'],
#         geom['barrier_height']
#     )

#     kerb_area = trapezoidal_area(
#         geom['kerb_top_width'],
#         geom['kerb_bottom_width'],
#         geom['kerb_height']
#     )

#     return {
#         "type": "RCC Crash Barrier",
#         "rcc_barrier_area": barrier_area,
#         "kerb_area": kerb_area
#     }

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