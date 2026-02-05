"""
Crash barrier self-weight calculations.
Takes area values from geometry.py and converts them to load.
"""

from .geometry import (
    median_raised_kerb_area,
    median_rcc_barrier_area,
    median_metallic_barrier_area,
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

# FIG 5(a): MEDIAN RAISED KERB

def median_raised_kerb_load():
    geom = median_raised_kerb_area()

    kerb_load = load_from_area(geom["kerb_area"], RCC_DENSITY)

    return {
        "type": geom["type"],
        "rcc_kerb_load_kN_per_m": round(kerb_load, 3),
        "total_load_kN_per_m": round(kerb_load, 3)
    }


# FIG 5(b): MEDIAN RCC CRASH BARRIER

def median_rcc_barrier_load():
    geom = median_rcc_barrier_area()

    barrier_load_single = load_from_area(geom["rcc_barrier_area_single"], RCC_DENSITY)
    kerb_load_single = load_from_area(geom["kerb_area_single"], RCC_DENSITY)

    total_barrier = 2 * barrier_load_single
    total_kerb = 2 * kerb_load_single
    total = total_barrier + total_kerb

    return {
        "type": geom["type"],
        "single_barrier_load_kN_per_m": round(barrier_load_single, 3),
        "single_kerb_load_kN_per_m": round(kerb_load_single, 3),
        "total_barrier_load_kN_per_m": round(total_barrier, 3),
        "total_kerb_load_kN_per_m": round(total_kerb, 3),
        "total_load_kN_per_m": round(total, 3)
    }


# FIG 5(c): MEDIAN METALLIC CRASH BARRIER

def median_metallic_barrier_load(barrier_type):
    geom = median_metallic_barrier_area(barrier_type)

    steel_load = 2 * load_from_area(geom["steel_area"], STEEL_DENSITY)
    kerb_load = 2 * load_from_area(geom["kerb_area"], RCC_DENSITY)

    total = steel_load + kerb_load

    return {
        "type": geom["type"],
        "steel_load_kN_per_m": round(steel_load, 3),
        "rcc_kerb_load_kN_per_m": round(kerb_load, 3),
        "total_load_kN_per_m": round(total, 3)
    }