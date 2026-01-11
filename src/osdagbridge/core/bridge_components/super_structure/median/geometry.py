import math
from osdagbridge.core.utils.codes.irc5_2015 import IRC5_2015
from osdagbridge.core.utils.common import (

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
    Accurate area calculation using:
      - TAN-based trapezoid splitting (3 trapezoids)
      - curve correction via segment formula:
            Aseg = R^2 ( tan(theta/2) - theta/2 )
      - multiply by 2 (two barriers in median)

    Returns area for 1 barrier and total area for 2 barriers.
    """

    import math

    geom = IRC5_2015.cl_109_6_3_shapes(
        barrier_type=KEY_MEDIAN_TYPE[1],  # RCC Crash Barrier
        footpath=None,
        railing_type=None,
        design_dict={},
        crash_barrier_type=None
    )

    # ----- BASIC DIMENSIONS FROM IRC -----
    H_total = geom["barrier_height"]          # 900
    W_base  = geom["barrier_bottom_width"]    # 450
    W_top   = geom["barrier_top_width"]       # 175

    # Split heights from figure
    H1 = 500     # top portion
    H2 = 250     # middle portion
    H3 = 100     # base portion
    assert H1 + H2 + H3 == H_total

    # Curve radii
    R_small = 50
    R_big   = 250

    # Total widening = (450 - 175) = 275.
    # tan(theta) = side_increase / height
    side_increase_total = (W_base - W_top) / 2  # = 137.5
    theta = math.atan(side_increase_total / H_total)

    # W(h) = W_top + 2 * (h * tan(theta))

    # Level after H1
    W1 = W_top + 2 * (H1 * math.tan(theta))

    W2 = W_top + 2 * ((H1 + H2) * math.tan(theta))

    # Bottom should match base width approximately
    W3 = W_base

    # 3 TAN-BASED TRAPEZOIDS

    A1 = 0.5 * (W_top + W1) * H1
    A2 = 0.5 * (W1 + W2) * H2
    A3 = 0.5 * (W2 + W3) * H3

    A_traps = A1 + A2 + A3

    def seg_area(R, ang):
        return (R**2) * (math.tan(ang/2) - ang/2)

    # x = atan(50/500)   (small offset)
    # y = atan(W_top/250)
    x = math.atan(50 / H1)         # atan(50/500)
    y = math.atan(W_top / H2)      # atan(175/250)

    theta_big = y - x
    A_big = seg_area(R_big, theta_big)

    theta_small = math.atan(W_top / H2)
    A_small = seg_area(R_small, theta_small)

    A_curve = A_big - A_small

    # TOTAL AREA

    area_one = A_traps + A_curve
    area_total = 2 * area_one  # median has 2 barriers

    return {
        "type": "Median RCC Crash Barrier (Fig 5b)",
        "theta_rad": round(theta, 6),
        "one_side_area_mm2": round(area_one, 3),
        "total_area_mm2": round(area_total, 3),
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