from osdagbridge.core.utils.codes.irc5_2015 import IRC5_2015
from osdagbridge.core.utils.codes.keyfile import (
    KEY_CRASH_BARRIER_TYPE,
    KEY_FOOTPATH,
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


    # CURVED SEGMENT AREAS 

    def segment_area(R, theta):
        return (R**2) * (math.tan(theta/2) - theta/2)

    # x = tan⁻¹(50/550)
    x = math.atan(50/550)

    # y = tan⁻¹(175/250)
    y = math.atan(175/250)

    theta_big = y - x          # ≈ 0.52 rad 

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

