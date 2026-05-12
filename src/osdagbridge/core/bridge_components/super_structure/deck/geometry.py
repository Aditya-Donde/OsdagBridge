"""Deck slab and wearing course dead load calculations."""
from osdagbridge.core.utils.codes.keyfile import DEFAULT_CONCRETE_DENSITY, DEFAULT_BITUMINOUS_DENSITY
from osdagbridge.core.utils.common import *


# IRC 6:2017 / IS 875 Pt 1 — wet reinforced concrete unit weight.
WET_CONCRETE_DENSITY_kN_m3 = DEFAULT_CONCRETE_DENSITY

# IRC 6:2017 / IS 875 Pt 1 — bituminous wearing course unit weight.
BITUMINOUS_DENSITY_kN_m3 = DEFAULT_BITUMINOUS_DENSITY


def slab_dead_load_kN_m2(
    thickness_m: float,
    density_kN_m3: float = WET_CONCRETE_DENSITY_kN_m3,
) -> float:
    """Dead load intensity for the concrete deck slab (kN/m²).

    Parameters
    ----------
    thickness_m : float
        Slab thickness in metres.
    density_kN_m3 : float
        Unit weight of concrete in kN/m³ (default: 25 kN/m³).

    Returns
    -------
    float
        Uniform patch load in kN/m².
    """
    return thickness_m * density_kN_m3


def wearing_course_dead_load_kN_m2(
    thickness_m: float,
    density_kN_m3: float = BITUMINOUS_DENSITY_kN_m3,
) -> float:
    """Dead load intensity for the wearing course / overlay (kN/m²).

    Parameters
    ----------
    thickness_m : float
        Wearing course thickness in metres.
    density_kN_m3 : float
        Unit weight of the wearing course material in kN/m³
        (default: 24 kN/m³ for bituminous; use 25 kN/m³ for concrete overlays).

    Returns
    -------
    float
        Uniform patch load in kN/m².
    """
    return thickness_m * density_kN_m3


# ─── Input extraction ────────────────────────────────────────────────────────

def deck_thickness_from_inputs(additional_inputs: dict, default_mm: float) -> float:
    """Extract deck slab thickness (m) from the additional-inputs dict.

    Parameters
    ----------
    additional_inputs : dict
        The bridge's additional-inputs dictionary (keyed by KEY_TS_DECK_THICKNESS).
    default_mm : float
        Fallback thickness in mm when the key is absent.

    Returns
    -------
    float
        Deck slab thickness in metres.
    """
    t_mm = float(additional_inputs.get(KEY_TS_DECK_THICKNESS, default_mm))
    return t_mm / 1000.0


def wearing_course_params_from_inputs(
    additional_inputs: dict,
    default_t_mm: float,
    default_rho_kN_m3: float,
) -> tuple[float, float]:
    """Extract wearing-course thickness and density from the additional-inputs dict.

    Parameters
    ----------
    additional_inputs : dict
        The bridge's additional-inputs dictionary.
    default_t_mm : float
        Fallback thickness in mm (e.g. 50 mm bituminous default).
    default_rho_kN_m3 : float
        Fallback unit weight in kN/m³ (e.g. 24 kN/m³ for bituminous).

    Returns
    -------
    tuple[float, float]
        ``(thickness_m, density_kN_m3)`` ready to pass to
        ``create_wearing_course_load()``.
    """
    t_mm = float(additional_inputs.get(KEY_WC_THICKNESS, default_t_mm))
    rho = float(additional_inputs.get(KEY_WC_DENSITY, default_rho_kN_m3))
    return t_mm / 1000.0, rho
