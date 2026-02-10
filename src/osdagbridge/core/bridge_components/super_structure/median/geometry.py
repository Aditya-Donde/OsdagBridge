"""
Median geometry calculations.
Takes dimensions from IRC5_2015 and computes areas only.

@author: Sweta Pal
"""

import math
from osdagbridge.core.utils.codes.irc5_2015 import IRC5_2015
from osdagbridge.core.utils.codes.keyfile import (
    KEY_METALLIC_CRASH_BARRIER_TYPE,
    KEY_MEDIAN_TYPE,
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

def median_rcc_crash_barrier_area():
    """
    IRC Fig 5(b) Median with RCC crash barrier.
    Area calculation using:
      - TAN-based trapezoid splitting (3 trapezoids)
      - curve correction via segment formula:
            Aseg = R^2 ( tan(theta/2) - theta/2 )
      - multiply by 2 (median has 2 barriers)
    """

    import math

    geom = IRC5_2015.cl_109_6_3_shapes(
        barrier_type=KEY_MEDIAN_TYPE[1],  # RCC Crash Barrier
        footpath=None,
        railing_type=None,
        design_dict={},
        crash_barrier_type=None
    )

    H_total = geom["barrier_height"]
    W_base  = geom["barrier_bottom_width"]
    W_top   = geom["barrier_top_width"]

    H1 = geom["barrier_split_h1"]
    H2 = geom["barrier_split_h2"]

    wearing = geom["wearing_course_thickness"]
    H3 = geom["barrier_split_h3"] + wearing

    R_small = geom["barrier_radius_small"]
    R_big   = geom["barrier_radius_big"]

    # x = atan(offset / H1)
    curve_offset = geom["barrier_curve_offset"]

    side_increase_total = (W_base - W_top) / 2
    theta = math.atan(side_increase_total / H_total)

    # Width at key heights
    W1 = W_top + 2 * (H1 * math.tan(theta))
    W2 = W_top + 2 * ((H1 + H2) * math.tan(theta))
    W3 = W_base

    # AREAS OF 3 TRAPEZOIDS 
    A1 = 0.5 * (W_top + W1) * H1
    A2 = 0.5 * (W1 + W2) * H2
    A3 = 0.5 * (W2 + W3) * H3

    A_traps = A1 + A2 + A3

    # CURVE SEGMENT AREA FUNCTION
    def seg_area(R, ang):
        return (R**2) * (math.tan(ang/2) - ang/2)

    # angles from IRC-based dimensions
    x = math.atan(curve_offset / H1)
    y = math.atan(W_top / H2)

    theta_big = y - x
    A_big = seg_area(R_big, theta_big)

    theta_small = math.atan(W_top / H2)
    A_small = seg_area(R_small, theta_small)

    A_curve = A_big - A_small

    # TOTAL AREAS 
    area_one = A_traps + A_curve
    area_total = 2 * area_one   # median has 2 barriers

    return {
        "type": "Median RCC Crash Barrier (Fig 5b)",
        "one_side_area": round(area_one, 3),
        "total_area": round(area_total, 3),
        "theta_rad": round(theta, 6),
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