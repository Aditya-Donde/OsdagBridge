"""Plate girder geometry and dead load calculations."""
from osdagbridge.core.utils.codes.keyfile import DEFAULT_STEEL_DENSITY


def make_girder():
    return {}


# IS 875 (Part 1) — structural steel unit weight used for self-weight dead load.
STEEL_UNIT_WEIGHT_kN_m3 = DEFAULT_STEEL_DENSITY


def girder_self_weight_kN_m(area_m2: float, density_kN_m3: float = STEEL_UNIT_WEIGHT_kN_m3) -> float:
    """Dead load intensity for a steel plate girder (kN/m).

    Parameters
    ----------
    area_m2 : float
        Cross-sectional area of the girder in m².
    density_kN_m3 : float
        Unit weight of steel in kN/m³ (default: IS 875 Pt.1 = 78.5 kN/m³).

    Returns
    -------
    float
        Line load in kN/m.
    """
    return area_m2 * density_kN_m3
