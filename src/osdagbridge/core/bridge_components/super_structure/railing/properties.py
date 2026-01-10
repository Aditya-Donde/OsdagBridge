from osdagbridge.core.utils.common import (
    KEY_RAILING_TYPE
)
# MATERIAL DENSITIES
RCC_DENSITY = 25      # kN/m³
STEEL_DENSITY = 78    # kN/m³


def load_from_area(area_mm2, density):
    """
    Convert mm² area per metre → kN/m
    mm² → m²  ( / 1e6 )
    multiply by density
    """
    return (area_mm2 / 1e6) * density

# FIG 1(a) — Rigid Barrier + RCC Railing (with Footpath)

def rcc_railing_load():
    from .geometry import rigid_barrier_with_railing_area
    geom = rigid_barrier_with_railing_area(KEY_RAILING_TYPE[0])

    barrier_load = load_from_area(
        geom["barrier_area"],
        RCC_DENSITY
    )

    return {
        "type": geom["type"],
        "rcc_barrier_load_kN_per_m": round(barrier_load, 3),
        "total_load_kN_per_m": round(barrier_load, 3)
    }

# FIG 1(b) — Rigid Barrier + Steel Railing (with Footpath)

def steel_railing_load():
    from .geometry import rigid_barrier_with_railing_area
    geom = rigid_barrier_with_railing_area(KEY_RAILING_TYPE[1])

    barrier_load = load_from_area(
        geom["barrier_area"],
        RCC_DENSITY      # RCC body, railing material doesn't affect body load
    )

    return {
        "type": geom["type"],
        "rcc_barrier_load_kN_per_m": round(barrier_load, 3),
        "total_load_kN_per_m": round(barrier_load, 3)
    }
