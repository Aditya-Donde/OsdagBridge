PERMANENT_LOAD_TAB_SCHEMA = {
    "id": "permanent_load_tab",
    "label_width": 220,
    "description": {"title": "Description Box", "text": "", "hide_when_empty": False, "min_height": 420},
    "sections": [
        {
            "title": "Dead Load (DL)",
            "fields": [
                {
                    "id": "self_weight_factor",
                    "label": "Self-weight modification factor",
                    "type": "line",
                    "validator": {"type": "double_range", "bottom": 0.0, "top": 10.0, "decimals": 2},
                    "default": "1.00",
                    "bind": "self_weight_factor_input",
                },
            ],
        },
    ],
}
