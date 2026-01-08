"""
Crash barrier geometry calculations.
Takes dimensions from IRC5_2015 and computes areas only.
"""

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


# FIG 4 : EDGE METALLIC BARRIER 

def metallic_edge_barrier_area(barrier_type):

    metallic_type = (
        KEY_METALLIC_CRASH_BARRIER_TYPE[1]
        if barrier_type == "Double"
        else KEY_METALLIC_CRASH_BARRIER_TYPE[0]
    )

    geom = IRC5_2015.cl_109_6_3_shapes(
        barrier_type=KEY_CRASH_BARRIER_TYPE[1],   # Semi-rigid
        footpath=KEY_FOOTPATH[0],
        railing_type=None,
        design_dict={},
        crash_barrier_type=metallic_type
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
        "type": "Edge Metallic Barrier",
        "steel_area": post_area + beam_area,
        "kerb_area": kerb_area
    }

import math

def circular_segment_area(R, theta):
    """
    Circular segment area based on PPT formula:
    A = R^2 (tan(theta/2) - theta/2)
    theta must be in radians
    """
    return (R**2) * (math.tan(theta/2) - theta/2)

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

# FIG 1(a) : RCC Railing + Footpath
# def rigid_barrier_with_railing_area(railing_type):
#     """
#     Computes RCC rigid crash barrier area (Fig 1a RCC railing, Fig 1b Steel railing)
#     Only RCC barrier body is calculated (since railing load handled separately)
#     """

#     geom = IRC5_2015.cl_109_6_3_shapes(
#         barrier_type=KEY_CRASH_BARRIER_TYPE[2],   # Rigid
#         footpath=KEY_FOOTPATH[1],                 # With footpath (same for fig 1a & 1b)
#         railing_type=railing_type,
#         design_dict={},
#         crash_barrier_type=None
#     )

#     W  = geom["crash_barrier_width"]
#     Hm = geom["crash_barrier_middle_length"]
#     T  = geom["crash_barrier_top_notch"]
#     B  = geom["crash_barrier_base_notch"]
#     R1 = geom["crash_barrier_radius1"]
#     R2 = geom["crash_barrier_radius2"]

#     #  TOP TRAPEZOID 
#     top_bottom_width = (T + 50) / 2
#     A_top = ((T + top_bottom_width) / 2) * Hm

#     # MIDDLE REGION 

#     A_middle_rect = 250 * top_bottom_width
#     A_middle_tri  = 0.5 * 250 * top_bottom_width

#     # BOTTOM RECTANGLE 
#     A_bottom = W * B

#     # CURVED PORTIONS 

#     import math

#     A_curve_big  = (math.pi * R2 * R2 / 4) - (R2 * R2 / 2)
#     A_curve_small = (math.pi * R1 * R1 / 4) - (R1 * R1 / 2)

#     A_curve = A_curve_big + A_curve_small

#     total_area = A_top + A_middle_rect + A_middle_tri + A_bottom + A_curve

#     return {
#         "type": "Rigid Barrier with RCC Railing (Fig 1a)"
#         if railing_type == KEY_RAILING_TYPE[0]
#         else "Rigid Barrier with Steel Railing (Fig 1b)",
#         "barrier_area": total_area
#     }

# fig 1

def rigid_barrier_with_railing_area(railing):
    """
    IRC 5 Fig 1(a) & 1(b)
    Computes accurate geometric area of rigid crash barrier
    using:
        - 3 trapezoids (same logic as manual calc)
        - Circular segment areas using PPT formula
    railing = "RCC" or "Steel"
    """

    import math

    # RAILING TYPE 
    if railing.lower() == "rcc":
        railing_key = KEY_RAILING_TYPE[0]
        barrier_name = "Rigid Barrier with RCC Railing (Fig 1a)"
    elif railing.lower() == "steel":
        railing_key = KEY_RAILING_TYPE[1]
        barrier_name = "Rigid Barrier with Steel Railing (Fig 1b)"
    else:
        raise ValueError("railing must be RCC or Steel")

    # DIMENSIONS FROM IRC FILE 
    geom = IRC5_2015.cl_109_6_3_shapes(
        barrier_type=KEY_CRASH_BARRIER_TYPE[2],   # Rigid Barrier
        footpath=KEY_FOOTPATH[1],                 # Footpath present
        railing_type=railing_key,
        design_dict={},
        crash_barrier_type=None
    )

    W   = geom["crash_barrier_width"]             # 450
    T   = geom["crash_barrier_top_notch"]         # 175
    M   = geom["crash_barrier_middle_length"]     # 550
    B   = geom["crash_barrier_base_notch"]        # 100
    R1  = geom["crash_barrier_radius1"]           # 50
    R2  = geom["crash_barrier_radius2"]           # 250

    wearing = geom["wearing_course_thickness"]    # 50
    base_effective = B + wearing                  # 150  (same as manual)

    # TRAPEZOID CALCULATIONS (EXACTLY LIKE YOUR NOTEBOOK)

    theta = math.atan(50/950)     # slope tiny angle ≈ 0.052 rad

    L1 = T + 50 + 50 - 400 * theta
    L2 = 225 + 175 + 50 - 150 * theta
    L3 = W

    # Heights
    H1 = 550
    H2 = 250
    H3 = base_effective

    A1 = 0.5 * (T + L1) * H1
    A2 = 0.5 * (L1 + L2) * H2
    A3 = 0.5 * (L2 + L3) * H3

    A_trapezoids = A1 + A2 + A3


    # CURVED SEGMENT AREAS (PPT FORMULA)

    def segment_area(R, theta):
        return (R**2) * (math.tan(theta/2) - theta/2)

    # x = tan⁻¹(50/550)
    x = math.atan(50/550)

    # y = tan⁻¹(175/250)
    y = math.atan(175/250)

    theta_big = y - x          # ≈ 0.52 rad  (same as your hand calc)

    A_big_curve = segment_area(R2, theta_big)

    # θsmall ≈ 0.61  (same logic you used)
    theta_small = math.atan(175/250)
    A_small_curve = segment_area(R1, theta_small)

    A_curve = A_big_curve - A_small_curve

    total_area = A_trapezoids + A_curve

    return {
        "type": barrier_name,
        "barrier_area": round(total_area, 3)
    }


# FIG 2 — RIGID BARRIER WITHOUT FOOTPATH

def rigid_barrier_no_footpath_area():

    geom = IRC5_2015.cl_109_6_3_shapes(
        barrier_type=KEY_CRASH_BARRIER_TYPE[2],   # Rigid
        footpath=KEY_FOOTPATH[0],                 # No footpath
        railing_type=None,
        design_dict={},
        crash_barrier_type=KEY_RIGID_CRASH_BARRIER_TYPE[0]
    )

    import math

    # --------- GEOMETRY ----------
    H_top  = geom["crash_barrier_middle_length"]      # 750
    H_mid  = 250
    H_bot  = geom["crash_barrier_base_notch"]         # 100
    wearing = geom.get("wearing_course_thickness", 50)
    H_bot_eff = H_bot + wearing                       # 150

    W_tot  = geom["crash_barrier_width"]              # 450
    W_top  = geom["crash_barrier_top_notch"]          # 175
    W_mid  = 225

    R1 = geom["crash_barrier_radius1"]                # 50
    R2 = geom["crash_barrier_radius2"]                # 250

    # --------- TRAPEZOIDS ----------
    A1 = 0.5 * (W_top + W_mid) * H_top
    A2 = 0.5 * (W_mid + W_tot) * H_mid
    A3 = W_tot * H_bot_eff

    A_trap = A1 + A2 + A3

    # --------- CURVES ----------
    def seg_area(R, theta):
        return (R**2) * (math.tan(theta/2) - theta/2)

    x = math.atan(R1 / H_top)      # atan(50 / 750)
    y = math.atan(W_top / R2)      # atan(175 / 250)

    theta = y - x

    A_big   = seg_area(R2, theta)
    A_small = seg_area(R1, y)

    A_curve = A_big - A_small

    total = A_trap + A_curve

    return {
        "type": "Rigid Barrier without Footpath (Fig 2)",
        "barrier_area": round(total, 3)
    }


# FIG 3 — HIGH CONTAINMENT CRASH BARRIER

def high_containment_barrier_area():

    geom = IRC5_2015.cl_109_6_3_shapes(
        barrier_type=KEY_CRASH_BARRIER_TYPE[2],
        footpath=KEY_FOOTPATH[0],
        railing_type=None,
        design_dict={},
        crash_barrier_type=KEY_RIGID_CRASH_BARRIER_TYPE[1]
    )

    import math

    # --------- GEOMETRY ----------
    H_top  = geom["crash_barrier_middle_length"]      # 1200
    H_mid  = 250
    H_bot  = geom["crash_barrier_base_notch"]         # 100
    wearing = geom.get("wearing_course_thickness", 50)
    H_bot_eff = H_bot + wearing                       # 150

    W_tot  = geom["crash_barrier_width"]              # 525
    W_top  = geom["crash_barrier_top_notch"]          # 250
    W_mid  = 225

    R1 = geom["crash_barrier_radius1"]                # 50
    R2 = geom["crash_barrier_radius2"]                # 250

    # --------- TRAPEZOIDS ----------
    A1 = 0.5 * (W_top + W_mid) * H_top
    A2 = 0.5 * (W_mid + W_tot) * H_mid
    A3 = W_tot * H_bot_eff

    A_trap = A1 + A2 + A3

    # --------- CURVES ----------
    def seg_area(R, theta):
        return (R**2) * (math.tan(theta/2) - theta/2)

    x = math.atan(R1 / H_top)      # atan(50 / 1200)
    y = math.atan(W_top / R2)      # atan(250 / 250)

    theta = y - x

    A_big   = seg_area(R2, theta)
    A_small = seg_area(R1, y)

    A_curve = A_big - A_small

    total = A_trap + A_curve

    return {
        "type": "High Containment Crash Barrier (Fig 3)",
        "barrier_area": round(total, 3)
    }