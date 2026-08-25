"""Footpath geometry and dead load calculations per IRC 6:2017."""
from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017


def footpath_y_ranges(
    *,
    footpath_config,
    deck_width,
    footpath_width,
    railing_width
):
    """Y ranges occupied by each footpath, measured from the deck centre.

    The footpath sits outboard of the deck edge — the deck is the carriageway
    plus its crash barriers — and carries the railing on its outer edge, so it
    spans ``footpath_width + railing_width`` beyond the deck.

    Returns
    -------
    list[tuple[float, float]]
        ``(y_start, y_end)`` per footpath; empty when there is no footpath.
    """
    if footpath_config == "NONE" or footpath_width <= 0:
        return []

    deck_half = deck_width / 2.0
    strip_width = footpath_width + railing_width
    ranges = []

    if footpath_config in ("LEFT", "BOTH"):
        ranges.append((-deck_half - strip_width, -deck_half))

    if footpath_config in ("RIGHT", "BOTH"):
        ranges.append((deck_half, deck_half + strip_width))

    return ranges


def footpath_dead_load_kN_m2() -> float:
    """Dead load intensity for the footpath / footway (kN/m²).

    Value is taken directly from IRC 6:2017 Cl.206.1 (footway / kerb load).

    Returns
    -------
    float
        Uniform patch load in kN/m².
    """
    return IRC6_2017.cl_206_1_footway_load()
