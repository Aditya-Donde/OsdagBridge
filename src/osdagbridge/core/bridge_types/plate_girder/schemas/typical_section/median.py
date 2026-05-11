MEDIAN_TAB_SCHEMA = {
    "id": "median_tab",
    "label_width": 210,
    "rows": [
        {
            "fields": [
                {
                    "id": "median_type",
                    "label": "Type:",
                    "type": "combo",
                    "choices": [
                        "IRC 5 - Raised Kerb",
                        "IRC 5 - RCC Crash Barrier",
                        "IRC 5 - Metallic Crash Barrier with Single W-Beam",
                        "IRC 5 - Metallic Crash Barrier with Double W-Beam",
                        "Custom",
                    ],
                    "adjust_to_contents": True,
                    "minimum_contents_length": 42,
                    "popup_min_width": 320,
                    "bind": "median_type",
                    "on_change": "on_median_type_changed",
                }
            ]
        },
        {
            "fields": [
                {
                    "id": "median_density",
                    "label": "Material Density (kN/m³):",
                    "type": "line",
                    "validator": {"type": "double_range", "bottom": 0.0, "top": 100.0, "decimals": 2},
                    "bind": "median_density",
                    "label_bind": "median_density_label",
                }
            ]
        },
        {
            "fields": [
                {
                    "id": "median_width",
                    "label": "Width (m):",
                    "type": "line",
                    "validator": {"type": "double_range", "bottom": 0.0, "top": 3.0, "decimals": 3},
                    "bind": "median_width",
                }
            ]
        },
        {
            "fields": [
                {
                    "id": "median_height",
                    "label": "Height (m):",
                    "type": "line",
                    "validator": {"type": "double_range", "bottom": 0.0, "top": 3.0, "decimals": 3},
                    "bind": "median_height",
                }
            ]
        },
        {
            "fields": [
                {
                    "id": "median_area",
                    "label": "Area (m²):",
                    "type": "line",
                    "validator": {"type": "double_range", "bottom": 0.0, "top": 10.0, "decimals": 4},
                    "bind": "median_area",
                    "label_bind": "median_area_label",
                }
            ]
        },
        {
            "fields": [
                {
                    "id": "median_load",
                    "label": "Load (kN/m):",
                    "type": "line",
                    "validator": {"type": "double_range", "bottom": 0.0, "top": 500.0, "decimals": 3},
                    "bind": "median_load",
                }
            ]
        },
        {
            "fields": [
                {
                    "id": "median_post_spacing",
                    "label": "Spacing between Posts (m):",
                    "type": "line",
                    "validator": {"type": "double_range", "bottom": 0.0, "top": 10.0, "decimals": 3},
                    "bind": "median_post_spacing",
                    "label_bind": "median_post_spacing_label",
                    "default": "1",
                }
            ]
        },
    ],
}
