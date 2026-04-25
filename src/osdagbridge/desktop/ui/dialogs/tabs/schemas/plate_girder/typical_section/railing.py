from osdagbridge.core.utils.common import DEFAULT_RAILING_WIDTH, MIN_RAILING_HEIGHT, VALUES_RAILING_TYPE

RAILING_TAB_SCHEMA = {
    "id": "railing_tab",
    "label_width": 180,
    "rows": [
        {
            "fields": [
                {
                    "id": "railing_type",
                    "label": "Type:",
                    "type": "combo",
                    "choices": VALUES_RAILING_TYPE,
                    "bind": "railing_type",
                    "on_change": "on_railing_type_changed",
                }
            ]
        },
        {
            "fields": [
                {
                    "id": "railing_width",
                    "label": "Width (mm):",
                    "type": "line",
                    "default": f"{DEFAULT_RAILING_WIDTH * 1000:.0f}",
                    "validator": {"type": "double_range", "bottom": 0.0, "top": 2000.0, "decimals": 1},
                    "bind": "railing_width",
                    "on_text_changed": "recalculate_girders",
                }
            ]
        },
        {
            "fields": [
                {
                    "id": "railing_height",
                    "label": "Height (m):",
                    "type": "line",
                    "validator": {"type": "double_range", "bottom": MIN_RAILING_HEIGHT, "top": 3.0, "decimals": 3},
                    "bind": "railing_height",
                    "on_editing_finished": "validate_railing_height",
                }
            ]
        },
        {
            "fields": [
                {
                    "id": "railing_load_mode",
                    "label": "Load Mode:",
                    "type": "combo",
                    "choices": ["Automatic (IRC 6)", "User-defined"],
                    "bind": "railing_load_mode",
                    "on_change": "on_railing_load_mode_changed",
                },
                {
                    "id": "railing_load_value",
                    "label": "Load (kN/m):",
                    "type": "line",
                    "validator": {"type": "double_range", "bottom": 0.0, "top": 50.0, "decimals": 2},
                    "placeholder": "Value",
                    "bind": "railing_load_value",
                    "enabled": False,
                },
            ]
        },
    ],
}
