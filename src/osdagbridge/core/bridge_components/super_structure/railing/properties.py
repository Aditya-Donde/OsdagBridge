"""
Crash barrier self-weight calculations.
Takes area values from geometry.py and converts them to load.
"""

from .geometry import (
    rcc_railing_area,
    steel_railing_area
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
    geom = rcc_railing_area()

    barrier_load = load_from_area(geom["barrier_area"], RCC_DENSITY)

    total = barrier_load

    return {
        "type": geom["type"],
        "rcc_barrier_load_kN_per_m": round(barrier_load, 3),
        "total_load_kN_per_m": round(total, 3)
    }

# FIG 1(b) — Rigid Barrier + Steel Railing (with Footpath)

def steel_railing_load():
    geom = steel_railing_area()

    barrier_load = load_from_area(geom["barrier_area"], RCC_DENSITY)

    total = barrier_load

    return {
        "type": geom["type"],
        "rcc_barrier_load_kN_per_m": round(barrier_load, 3),
        "total_load_kN_per_m": round(total, 3)
    }