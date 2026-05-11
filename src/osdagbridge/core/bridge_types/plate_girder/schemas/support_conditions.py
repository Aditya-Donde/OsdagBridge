SUPPORT_CONDITIONS_SCHEMA = {
    "id": "support_conditions",
    "title": "Support Conditions",
    "sections": [
        {
            "title": "Support Conditions",
            "fields": [
                {
                    "id": "left_support",
                    "label": "Left Support",
                    "type": "combo",
                    "choices": ["Fixed", "Pinned", "Roller"],
                    "default": "Pinned",
                    "enabled_choices": ["Pinned"],
                    "bind": "left_support_combo",
                },
                {
                    "id": "right_support",
                    "label": "Right Support",
                    "type": "combo",
                    "choices": ["Fixed", "Pinned", "Roller"],
                    "default": "Roller",
                    "enabled_choices": ["Roller"],
                    "bind": "right_support_combo",
                },
            ],
        },
        {
            "title": "Bearing length",
            "fields": [
                {
                    "id": "bearing_length",
                    "label": "Bearing Length Value (mm)",
                    "type": "line",
                    "default": "400.00",
                    "placeholder": "Length",
                    "bind": "bearing_length_input",
                    "validator": {
                        "type": "double_range",
                        "bottom": 0.00,
                        "top": 600.00,
                        "decimals": 3,
                    },
                }
            ],
        },
        {
            "id": "support_cad_row",
            "type": "cad_row",
            "cads": [
                {
                    "id": "left_support_cad",
                    "type": "cad",
                    "widget": "SupportCADWidget",
                    "bind": "left_cad",
                    "min_size": [300, 250],
                    "size_policy": "expanding",
                    "stretch": 1,
                },
                {
                    "id": "support_detail_cad",
                    "type": "cad",
                    "widget": "SupportDetailCADWidget",
                    "bind": "right_cad",
                    "min_size": [150, 200],
                    "size_policy": "expanding",
                    "stretch": 1,
                    "params_map": {
                        "bearing_length": {
                            "widget": "bearing_length_input",
                            "cast": "float",
                            "default": 400,
                        },
                    },
                    "reactive_sources": [
                        {"widget": "bearing_length_input", "signal": "textChanged"},
                    ],
                },
            ],
        },
    ],
}
