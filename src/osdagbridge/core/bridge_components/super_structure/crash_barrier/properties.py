"""
Crash barrier self-weight calculations.
Takes area values from geometry.py and converts them to load.
"""

from .geometry import (
    metallic_edge_barrier_area,
    rigid_barrier_with_railing_area,
    rigid_barrier_no_footpath_area,
    high_containment_barrier_area
)

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


# FIG 4 EDGE: METALLIC CRASH BARRIER

def metallic_edge_barrier_load(barrier_type):
    geom = metallic_edge_barrier_area(barrier_type)

    steel_load = load_from_area(geom["steel_area"], STEEL_DENSITY)
    kerb_load = load_from_area(geom["kerb_area"], RCC_DENSITY)

    return {
        "type": geom["type"],
        "steel_load_kN_per_m": round(steel_load, 3),
        "rcc_kerb_load_kN_per_m": round(kerb_load, 3),
        "total_load_kN_per_m": round(steel_load + kerb_load, 3)
    }



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


# FIG 2 — Rigid Barrier without Footpath

def rigid_barrier_no_footpath_load():
    geom = rigid_barrier_no_footpath_area()

    barrier_load = load_from_area(geom["barrier_area"], RCC_DENSITY)

    total = barrier_load

    return {
        "type": geom["type"],
        "rcc_barrier_load_kN_per_m": round(barrier_load, 3),
        "total_load_kN_per_m": round(total, 3)
    }


# FIG 3 — High Containment Barrier

def high_containment_barrier_load():
    geom = high_containment_barrier_area()

    barrier_load = load_from_area(geom["barrier_area"], RCC_DENSITY)

    total = barrier_load

    return {
        "type": geom["type"],
        "rcc_barrier_load_kN_per_m": round(barrier_load, 3),
        "total_load_kN_per_m": round(total, 3)
    }
