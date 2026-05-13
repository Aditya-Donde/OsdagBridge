from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_CARRIAGEWAY_WIDTH,
    KEY_SKEW_ANGLE,
    KEY_NO_OF_GIRDERS,
    KEY_GIRDER_SPACING,
    KEY_DECK_OVERHANG,
)


def resolve_bridge_config_summary(input_dict: dict) -> dict:
    return {
        "id":    "bridge_configuration_summary",
        "label": "Bridge Configuration Summary",
        "columns": [
            "Overall Width (m)",
            "Span (m)",
            "No. of Girders",
            "Girder Spacing (m)",
            "Deck Overhang (m)",
            "Skew Angle (deg)",
        ],
        "rows": [[
            _num(input_dict.get(KEY_CARRIAGEWAY_WIDTH)),
            _num(input_dict.get(KEY_SPAN)),
            _val(input_dict.get(KEY_NO_OF_GIRDERS)),   # from Additional Inputs
            _num(input_dict.get(KEY_GIRDER_SPACING)),  # from Additional Inputs
            _num(input_dict.get(KEY_DECK_OVERHANG)),   # from Additional Inputs
            _num(input_dict.get(KEY_SKEW_ANGLE, 0)),
        ]],
    }


def _num(value, fallback="—"):
    """Return float rounded to 2dp, or fallback if missing/invalid."""
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return fallback


def _val(value, fallback="—"):
    """Return value as-is if present, else fallback."""
    return value if value not in (None, "", [], {}) else fallback