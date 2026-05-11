from osdagbridge.core.utils.common import DEFAULT_CRASH_BARRIER_WIDTH

CRASH_BARRIER_TAB_SCHEMA = {
    "id": "crash_barrier_tab",
    "label_width": 210,
    "rows": [
        {
            "fields": [
                {
                    "id": "crash_barrier_type",
                    "label": "Type:",
                    "type": "combo",
                    "choices": [
                        "IRC 5 - RCC Crash Barrier",
                        "IRC 5 - High Containment RCC Crash Barrier",
                        "IRC 5 - Metallic Crash Barrier with Single W-Beam",
                        "IRC 5 - Metallic Crash Barrier with Double W-Beam",
                        "Custom",
                    ],
                    "adjust_to_contents": True,
                    "minimum_contents_length": 42,
                    "popup_min_width": 320,
                    "bind": "crash_barrier_type",
                    "on_change": "on_crash_barrier_type_changed",
                }
            ]
        },
        {
            "fields": [
                {
                    "id": "crash_barrier_density",
                    "label": "Material Density (kN/m³):",
                    "type": "line",
                    "validator": {"type": "double_range", "bottom": 0.0, "top": 100.0, "decimals": 2},
                    "bind": "crash_barrier_density",
                    "label_bind": "crash_barrier_density_label",
                    "on_editing_finished": "_auto_compute_crash_barrier_load",
                }
            ]
        },
        {
            "fields": [
                {
                    "id": "crash_barrier_width",
                    "label": "Width (m):",
                    "type": "line",
                    "default": DEFAULT_CRASH_BARRIER_WIDTH,
                    "validator": {"type": "double_range", "bottom": 0.0, "top": 2.0, "decimals": 3},
                    "bind": "crash_barrier_width",
                    "on_text_changed": "recalculate_girders",
                }
            ]
        },
        {
            "fields": [
                {
                    "id": "crash_barrier_height",
                    "label": "Height (m):",
                    "type": "line",
                    "validator": {"type": "double_range", "bottom": 0.0, "top": 3.0, "decimals": 3},
                    "bind": "crash_barrier_height",
                }
            ]
        },
        {
            "fields": [
                {
                    "id": "crash_barrier_area",
                    "label": "Area (m²):",
                    "type": "line",
                    "validator": {"type": "double_range", "bottom": 0.0, "top": 10.0, "decimals": 4},
                    "bind": "crash_barrier_area",
                    "label_bind": "crash_barrier_area_label",
                    "on_editing_finished": "_auto_compute_crash_barrier_load",
                }
            ]
        },
        {
            "fields": [
                {
                    "id": "crash_barrier_load",
                    "label": "Load (kN/m):",
                    "type": "line",
                    "validator": {"type": "double_range", "bottom": 0.0, "top": 500.0, "decimals": 3},
                    "bind": "crash_barrier_load",
                }
            ]
        },
        {
            "fields": [
                {
                    "id": "crash_barrier_post_spacing",
                    "label": "Spacing between Posts (m):",
                    "type": "line",
                    "default": "1",
                    "validator": {"type": "double_range", "bottom": 0.0, "top": 10.0, "decimals": 3},
                    "bind": "crash_barrier_post_spacing",
                    "label_bind": "crash_barrier_post_spacing_label",
                }
            ]
        },
    ],
}
