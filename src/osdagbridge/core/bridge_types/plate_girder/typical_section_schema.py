"""Schemas for Typical Section Details sub-tabs (plate girder)."""

from osdagbridge.core.utils.common import (
    DEFAULT_CRASH_BARRIER_WIDTH,
    DEFAULT_GIRDER_SPACING,
    DEFAULT_RAILING_WIDTH,
    MIN_FOOTPATH_WIDTH,
    MIN_RAILING_HEIGHT,
    VALUES_RAILING_TYPE,
    VALUES_WEARING_COAT_MATERIAL,
)

LAYOUT_TAB_SCHEMA = {
    "id": "layout_tab",
    "rows": [
        {
            "fields": [
                {
                    "id": "girder_spacing",
                    "label": "Girder Spacing (m):",
                    "type": "line",
                    "validator": {"type": "double_range", "bottom": 0.01, "top": 50.0, "decimals": 3},
                    "default": DEFAULT_GIRDER_SPACING,
                    "bind": "girder_spacing",
                    "on_editing_finished": "on_girder_spacing_changed",
                },
                {
                    "id": "no_of_girders",
                    "label": "No. of Girders:",
                    "type": "line",
                    "validator": {"type": "int_range", "bottom": 2, "top": 100},
                    "bind": "no_of_girders",
                    "on_editing_finished": "on_no_of_girders_changed",
                },
            ]
        },
        {
            "fields": [
                {
                    "id": "deck_overhang",
                    "label": "Deck Overhang Width (m):",
                    "type": "line",
                    "validator": {"type": "double_range", "bottom": 0.0, "top": 100.0, "decimals": 3},
                    "bind": "deck_overhang",
                    "on_editing_finished": "on_deck_overhang_changed",
                }
            ]
        },
        {
            "fields": [
                {
                    "id": "overall_bridge_width_display",
                    "label": "Overall Bridge Width (m):",
                    "type": "line",
                    "read_only": True,
                    "bind": "overall_bridge_width_display",
                    "on_text_changed": "_reject_overall_width_override",
                }
            ]
        },
        {
            "fields": [
                {
                    "id": "deck_thickness",
                    "label": "Deck Thickness (mm):",
                    "type": "line",
                    "validator": {"type": "double_range", "bottom": 100.0, "top": 500.0, "decimals": 0},
                    "default": "200",
                    "bind": "deck_thickness",
                    "on_editing_finished": "validate_deck_thickness",
                },
                {
                    "id": "footpath_thickness",
                    "label": "Footpath Thickness (mm):",
                    "type": "line",
                    "validator": {"type": "double_range", "bottom": 100.0, "top": 500.0, "decimals": 0},
                    "default": "200",
                    "bind": "footpath_thickness",
                    "on_editing_finished": "validate_footpath_thickness",
                },
            ]
        },
        {
            "fields": [
                {
                    "id": "footpath_width",
                    "label": "Footpath Width (m):",
                    "type": "line",
                    "validator": {"type": "double_range", "bottom": MIN_FOOTPATH_WIDTH, "top": 5.0, "decimals": 3},
                    "default": f"{MIN_FOOTPATH_WIDTH:.2f}",
                    "bind": "footpath_width",
                    "on_text_changed": "on_footpath_width_changed",
                }
            ]
        },
    ],
}

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
                }
            ]
        },
    ],
}

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
                    "default": "1",
                }
            ]
        },
    ],
}

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

WEARING_COURSE_TAB_SCHEMA = {
    "id": "wearing_course_tab",
    "label_width": 200,
    "rows": [
        {
            "fields": [
                {
                    "id": "wearing_material",
                    "label": "Material:",
                    "type": "combo",
                    "choices": VALUES_WEARING_COAT_MATERIAL,
                    "bind": "wearing_material",
                    "on_change": "on_wearing_material_changed",
                }
            ]
        },
        {
            "fields": [
                {
                    "id": "wearing_density",
                    "label": "Density (kN/m³):",
                    "type": "line",
                    "validator": {"type": "double_range", "bottom": 0.0, "top": 40.0, "decimals": 2},
                    "bind": "wearing_density",
                    "default": "24.0",
                }
            ]
        },
        {
            "fields": [
                {
                    "id": "wearing_thickness",
                    "label": "Thickness (mm):",
                    "type": "line",
                    "validator": {"type": "double_range", "bottom": 0.0, "top": 200.0, "decimals": 1},
                    "bind": "wearing_thickness",
                    "default": "50",
                }
            ]
        },
    ],
}

LANE_DETAILS_TAB_SCHEMA = {
    "id": "lane_details_tab",
    "rows": [
        {
            "fields": [
                {
                    "id": "lane_count",
                    "label": "No. of Traffic Lanes:",
                    "type": "combo",
                    "choices": [str(i) for i in range(1, 7)],
                    "bind": "lane_count_combo",
                    "on_change": "on_lane_count_changed",
                }
            ]
        }
    ],
}
