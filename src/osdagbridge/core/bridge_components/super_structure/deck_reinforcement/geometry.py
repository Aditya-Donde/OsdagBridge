"""Deck reinforcement geometry — bar area and provided steel area per metre width."""
import math


def bar_area_mm2(dia_mm: float) -> float:
    """Cross-sectional area of a single reinforcement bar (mm²).

    a_bar = pi * d^2 / 4  — nominal bar area (IS 1786).

    Parameters
    ----------
    dia_mm : float
        Bar diameter in mm.

    Returns
    -------
    float
        Area of one bar in mm².
    """
    return math.pi * dia_mm ** 2 / 4.0


def reinforcement_area_per_m_mm2(dia_mm: float, spacing_mm: float) -> float:
    """Provided steel area per metre width (mm²/m).

    For bars of diameter ``dia_mm`` at centre-to-centre ``spacing_mm``:
        As = a_bar * 1000 / spacing

    Parameters
    ----------
    dia_mm : float
        Bar diameter in mm.
    spacing_mm : float
        Centre-to-centre bar spacing in mm.

    Returns
    -------
    float
        Provided reinforcement area in mm² per metre width.

    Raises
    ------
    ValueError
        If ``spacing_mm`` is not positive.
    """
    if spacing_mm <= 0:
        raise ValueError(
            f"spacing_mm must be > 0 to compute reinforcement area per metre, got {spacing_mm!r}."
        )
    return bar_area_mm2(dia_mm) * 1000.0 / spacing_mm
