"""Footpath dead load calculations per IRC 6:2017."""
from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017


def footpath_dead_load_kN_m2() -> float:
    """Dead load intensity for the footpath / footway (kN/m²).

    Value is taken directly from IRC 6:2017 Cl.206.1 (footway / kerb load).

    Returns
    -------
    float
        Uniform patch load in kN/m².
    """
    return IRC6_2017.cl_206_1_footway_load()
