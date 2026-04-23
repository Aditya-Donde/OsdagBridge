"""
Crash barrier geometry calculations.
Takes dimensions from IRC5_2015 and computes areas only.

@author: Sweta Pal
"""

from osdagbridge.core.utils.codes.irc5_2015 import IRC5_2015
from osdagbridge.core.utils.codes.keyfile import (
    KEY_CRASH_BARRIER_TYPE,
    KEY_FOOTPATH,
    KEY_METALLIC_CRASH_BARRIER_TYPE,
    KEY_RIGID_CRASH_BARRIER_TYPE,
    KEY_RAILING_TYPE,
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

    # CURVES
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


# ─── Dead load ───────────────────────────────────────────────────────────────

# IRC 5:2015 / IS 875 Pt 2 — typical RCC edge barrier self-weight (Type P3/P4).
DEFAULT_CRASH_BARRIER_LOAD_kN_m = 6.54


def crash_barrier_dead_load_kN_m(load_kN_per_m: float | None = None) -> float:
    """Dead load intensity for a crash barrier (kN/m).

    Parameters
    ----------
    load_kN_per_m : float, optional
        User-specified barrier self-weight per unit length (kN/m). When
        ``None`` the IRC 5:2015 default for an RCC edge barrier is used.

    Returns
    -------
    float
        Line load in kN/m.
    """
    return load_kN_per_m if load_kN_per_m is not None else DEFAULT_CRASH_BARRIER_LOAD_kN_m


_KEY_CRASH_BARRIER_LOAD = "crash_barrier_load"


def crash_barrier_load_from_inputs(additional_inputs: dict) -> float | None:
    """Extract user-specified crash barrier load (kN/m) from additional-inputs dict.

    Returns ``None`` when the key is absent, in which case
    ``crash_barrier_dead_load_kN_m()`` will apply the IRC 5 default.
    """
    val = additional_inputs.get(_KEY_CRASH_BARRIER_LOAD)
    return float(val) if val is not None else None