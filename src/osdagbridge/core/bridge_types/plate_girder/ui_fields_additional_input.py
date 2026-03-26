"""Consolidated UI schemas for plate girder Additional Inputs dialogs.

This module groups all schema dictionaries used by the Additional Inputs
flow, including Typical Section Details, Support/Design options, and
Member Properties.
"""

from osdagbridge.core.utils.common import (
    MIN_FOOTPATH_WIDTH,
    MIN_RAILING_HEIGHT,
    VALUES_GIRDER_DESIGN_MODE,
    VALUES_GIRDER_SPAN_MODE,
    VALUES_GIRDER_SYMMETRY,
    VALUES_GIRDER_TYPE,
    VALUES_PROFILE_SCOPE,
    VALUES_TORSIONAL_RESTRAINT,
    VALUES_WARPING_RESTRAINT,
    VALUES_WEB_TYPE,
    VALUES_RAILING_TYPE,
    VALUES_WEARING_COAT_MATERIAL,
)
from . import defaults as pg_defaults

_LAYOUT_DEFAULTS = pg_defaults.get_ai_defaults("layout")
_LAYOUT_GIRDER_SPACING = _LAYOUT_DEFAULTS.get(
    "girder_spacing_m",
    pg_defaults.DEFAULT_AI_LAYOUT_GIRDER_SPACING_M,
)
_LAYOUT_NO_OF_GIRDERS = _LAYOUT_DEFAULTS.get(
    "no_of_girders",
    pg_defaults.DEFAULT_AI_LAYOUT_NO_OF_GIRDERS,
)
_LAYOUT_DECK_OVERHANG = _LAYOUT_DEFAULTS.get(
    "deck_overhang_m",
    pg_defaults.DEFAULT_AI_LAYOUT_DECK_OVERHANG_M,
)
_LAYOUT_DECK_THICKNESS = f"{float(_LAYOUT_DEFAULTS.get('deck_thickness_mm', pg_defaults.DEFAULT_AI_LAYOUT_DECK_THICKNESS_MM)):.0f}"
_LAYOUT_FOOTPATH_WIDTH = f"{float(_LAYOUT_DEFAULTS.get('footpath_width_m', pg_defaults.DEFAULT_AI_LAYOUT_FOOTPATH_WIDTH_M)):.2f}"
_LAYOUT_FOOTPATH_THICKNESS = f"{float(_LAYOUT_DEFAULTS.get('footpath_thickness_mm', pg_defaults.DEFAULT_AI_LAYOUT_FOOTPATH_THICKNESS_MM)):.0f}"

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
                    "default": _LAYOUT_GIRDER_SPACING,
                    "bind": "girder_spacing",
                    "on_text_changed": "on_girder_spacing_changed",
                },
                {
                    "id": "no_of_girders",
                    "label": "No. of Girders:",
                    "type": "line",
                    "validator": {"type": "int_range", "bottom": 1, "top": 100},
                    "default": _LAYOUT_NO_OF_GIRDERS,
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
                    "default": _LAYOUT_DECK_OVERHANG,
                    "bind": "deck_overhang",
                    "on_text_changed": "on_deck_overhang_changed",
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
                    "default": _LAYOUT_DECK_THICKNESS,
                    "bind": "deck_thickness",
                    "on_editing_finished": "validate_deck_thickness",
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
                    "default": _LAYOUT_FOOTPATH_WIDTH,
                    "bind": "footpath_width",
                    "on_text_changed": "on_footpath_width_changed",
                },
                {
                    "id": "footpath_thickness",
                    "label": "Footpath Thickness (mm):",
                    "type": "line",
                    "validator": {"type": "double_range", "bottom": 100.0, "top": 500.0, "decimals": 0},
                    "default": _LAYOUT_FOOTPATH_THICKNESS,
                    "bind": "footpath_thickness",
                    "on_editing_finished": "validate_footpath_thickness",
                },
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
                    "default": pg_defaults.DEFAULT_AI_CRASH_BARRIER_WIDTH_M,
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
                    "default": pg_defaults.DEFAULT_AI_CRASH_BARRIER_POST_SPACING_M,
                    "validator": {"type": "double_range", "bottom": 0.0, "top": 10.0, "decimals": 3},
                    "bind": "crash_barrier_post_spacing",
                    "label_bind": "crash_barrier_post_spacing_label",
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
                    "default": pg_defaults.DEFAULT_AI_MEDIAN_POST_SPACING_M,
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
                    "default": pg_defaults.DEFAULT_AI_RAILING_WIDTH_MM,
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
                    "default": pg_defaults.DEFAULT_AI_WEARING_DENSITY_KN_PER_M3,
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
                    "default": pg_defaults.DEFAULT_AI_WEARING_THICKNESS_MM,
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
PERMANENT_LOAD_TAB_SCHEMA = {
    "id": "permanent_load_tab",
    "label_width": 220,
    "sections": [
        {
            "title": "Dead Load (DL):",
            "fields": [
                {
                    "id": "include_self_weight",
                    "label": "Include Member Self Weight:",
                    "type": "combo",
                    "choices": ["Yes", "No"],
                    "default": pg_defaults.DEFAULT_AI_PERM_INCLUDE_SELF_WEIGHT,
                    "bind": "include_self_weight_combo",
                },
                {
                    "id": "self_weight_factor",
                    "label": "Self-weight factor:",
                    "type": "line",
                    "validator": {"type": "double_range", "bottom": 0.0, "top": 10.0, "decimals": 2},
                    "default": pg_defaults.DEFAULT_AI_PERM_SELF_WEIGHT_FACTOR,
                    "bind": "self_weight_factor_input",
                },
                {
                    "id": "include_deck_weight",
                    "label": "Include Concrete Deck Weight:",
                    "type": "combo",
                    "choices": ["Yes", "No"],
                    "default": pg_defaults.DEFAULT_AI_PERM_INCLUDE_DECK_WEIGHT,
                    "bind": "include_deck_weight_combo",
                },
            ],
        },
        {
            "title": "Dead Load for Surfacing (DW):",
            "fields": [
                {
                    "id": "include_wearing_course",
                    "label": "Include Load from Wearing Course:",
                    "type": "combo",
                    "choices": ["Yes", "No"],
                    "default": pg_defaults.DEFAULT_AI_PERM_INCLUDE_WEARING_COURSE,
                    "bind": "include_wearing_course_combo",
                },
            ],
        },
        {
            "title": "Super-Imposed Dead Load (SIDL):",
            "fields": [
                {
                    "id": "include_crash_barrier",
                    "label": "Include Load from Crash Barrier:",
                    "type": "combo",
                    "choices": ["Yes", "No"],
                    "default": pg_defaults.DEFAULT_AI_PERM_INCLUDE_CRASH_BARRIER,
                    "bind": "include_crash_barrier_combo",
                },
                {
                    "id": "include_median",
                    "label": "Include Load from Median:",
                    "type": "combo",
                    "choices": ["Yes", "No"],
                    "default": pg_defaults.DEFAULT_AI_PERM_INCLUDE_MEDIAN,
                    "bind": "include_median_combo",
                },
                {
                    "id": "include_railing",
                    "label": "Include Load from Railing:",
                    "type": "combo",
                    "choices": ["Yes", "No"],
                    "default": pg_defaults.DEFAULT_AI_PERM_INCLUDE_RAILING,
                    "bind": "include_railing_combo",
                },
            ],
        },
    ],
}

LIVE_LOAD_TAB_SCHEMA = {
    "id": "live_load_tab",
    "label_width": 220,
    "field_width": 180,
    "field_height": 28,
    "sections": [
        {
            "id": "irc_vehicles_section",
            "title": "Vehicles from IRC 6:",
            "type": "checkbox_list",
            "items": [
                "Class A",
                "Class 70R Wheeled",
                "Class 70R Tracked",
                "Class AA Wheeled",
                "Class AA Tracked",
                "Class SV",
                "Fatigue Truck",
            ],
            "bind": "irc_vehicle_checkboxes",
            "default_checked": pg_defaults.DEFAULT_AI_LIVE_IRC_VEHICLES_CHECKED,
        },
        {
            "id": "custom_vehicle_section",
            "title": "Custom Vehicle:",
            "type": "custom_vehicle_table",
            "bind": "custom_vehicle_table",
            "add_button_bind": "custom_vehicle_add_button",
        },
        {
            "id": "braking_section",
            "title": "Braking Load from Vehicles:",
            "type": "dynamic_checkbox_list",
            "bind": "braking_vehicle_checkboxes",
            "default_checked": pg_defaults.DEFAULT_AI_LIVE_BRAKING_VEHICLES_CHECKED,
        },
        {
            "id": "eccentricity",
            "label": "Eccentricity from top of Deck (m):",
            "type": "line",
            "validator": {"type": "double_range", "bottom": 0.0, "top": 100.0, "decimals": 2},
            "default": pg_defaults.DEFAULT_AI_LIVE_ECCENTRICITY_M,
            "bind": "eccentricity_input",
        },
        {
            "id": "footpath_pressure",
            "label": "Footpath Pressure (kN/mm²):",
            "type": "mode_line",
            "mode_choices": ["Automatic", "User-defined"],
            "default_mode": pg_defaults.DEFAULT_AI_LIVE_FOOTPATH_MODE,
            "bind_mode": "footpath_mode_combo",
            "bind_value": "footpath_value_input",
            "default_value": pg_defaults.DEFAULT_AI_LIVE_FOOTPATH_PRESSURE_KN_PER_MM2,
            "mode_width": 120,
            "value_width": 80,
            "on_mode_change": "_on_footpath_mode_changed",
        },
    ],
    "description": {
        "title": "Description Box",
        "text": (
            "or on any other type of bridge unit shall be assumed to have the following value:\n\n"
            "a) In the case of a single lane or a two lane bridge: twenty percent of the first train "
            "load plus ten percent of the load of the succeeding trains or part thereof, the train "
            "loads in one lane only being considered for the purpose of this subclause. Where the "
            "entire first train is not on the full span, the braking force shall be taken as equal to "
            "twenty percent of the loads actually on the span or continuous unit of spans.\n"
            "b) In the case of bridges having more than two lanes: as in (a) above for the first two "
            "lanes plus five percent of the loads on the lanes in excess of two."
        ),
    },
}

SEISMIC_LOAD_TAB_SCHEMA = {
    "id": "seismic_load_tab",
    "label_width": 220,
    "field_width": 180,
    "field_height": 28,
    "sections": [
        {
            "id": "seismic_inputs_section",
            "title": "Seismic/Earthquake Load (EL) Inputs:",
            "type": "input_group",
            "fields": [
                {
                    "id": "seismic_zone",
                    "label": "Seismic Zone:",
                    "type": "combo",
                    "choices": ["II", "III", "IV", "V"],
                    "default": pg_defaults.DEFAULT_AI_SEISMIC_ZONE,
                    "bind": "seismic_zone_combo",
                },
                {
                    "id": "importance_factor",
                    "label": "Importance Factor:",
                    "type": "line",
                    "default": pg_defaults.DEFAULT_AI_SEISMIC_IMPORTANCE_FACTOR,
                    "bind": "importance_factor_input",
                },
                {
                    "id": "soil_type",
                    "label": "Type of Soil:",
                    "type": "combo",
                    "choices": [
                        "Type I – Rocky or Hard",
                        "Type II – Medium Soil",
                        "Type III – Soft Soil",
                    ],
                    "default": pg_defaults.DEFAULT_AI_SEISMIC_SOIL_TYPE,
                    "bind": "soil_type_combo",
                },
                {
                    "id": "time_period",
                    "label": "Time Period:",
                    "type": "line",
                    "bind": "time_period_input",
                },
                {
                    "id": "damping",
                    "label": "Damping Percentage:",
                    "type": "line",
                    "default": pg_defaults.DEFAULT_AI_SEISMIC_DAMPING_PERCENT,
                    "bind": "damping_input",
                },
                {
                    "id": "response_reduction_factor",
                    "label": "Response Reduction Factor:",
                    "type": "combo",
                    "choices": ["1", "2", "3", "4", "5"],
                    "default": pg_defaults.DEFAULT_AI_SEISMIC_RESPONSE_REDUCTION_FACTOR,
                    "bind": "response_factor_combo",
                },
                {
                    "id": "dead_load_seismic",
                    "label": "Dead Load for Seismic Force (kN):",
                    "type": "mode_line",
                    "mode_choices": ["Automatic", "Custom"],
                    "default_mode": pg_defaults.DEFAULT_AI_SEISMIC_DEAD_LOAD_MODE,
                    "bind_mode": "dead_load_seismic_combo",
                    "bind_value": "dead_load_custom_input",
                    "placeholder": "Custom Value",
                    "on_mode_change": "_toggle_seismic_custom_inputs",
                },
                {
                    "id": "live_load_seismic",
                    "label": "Live Load for Seismic Force (kN):",
                    "type": "mode_line",
                    "mode_choices": ["Automatic", "Custom"],
                    "default_mode": pg_defaults.DEFAULT_AI_SEISMIC_LIVE_LOAD_MODE,
                    "bind_mode": "live_load_seismic_combo",
                    "bind_value": "live_load_custom_input",
                    "placeholder": "Custom Value",
                    "on_mode_change": "_toggle_seismic_custom_inputs",
                },
            ],
        },
        {
            "id": "computed_values_section",
            "title": "Computed Values",
            "type": "computed_group",
            "fields": [
                {
                    "id": "zone_factor",
                    "label": "Zone Factor:",
                    "type": "computed",
                    "bind": "zone_factor",
                },
                {
                    "id": "spectral_coeff",
                    "label": "Spectral Acceleration Coefficient:",
                    "type": "computed",
                    "bind": "spectral_coeff",
                },
                {
                    "id": "horizontal_coeff",
                    "label": "Horizontal Seismic Coefficient:",
                    "type": "computed",
                    "bind": "horizontal_coeff",
                },
                {
                    "id": "vertical_coeff",
                    "label": "Vertical Seismic Coefficient:",
                    "type": "computed",
                    "bind": "vertical_coeff",
                },
            ],
        },
    ],
    "description": {
        "title": "Description Box",
        "text": (
            "Importance factor for normal, important, and critical bridges.\n\n"
            "Seismic zone factors are defined according to IRC 6 specifications.\n\n"
            "The spectral acceleration coefficient depends on soil type and time period."
        ),
    },
}

WIND_LOAD_TAB_SCHEMA = {
    "id": "wind_load_tab",
    "label_width": 260,
    "field_width": 140,
    "field_height": 28,
    "sections": [
        {
            "id": "wind_inputs_section",
            "title": "Wind Load (WL) Inputs:",
            "type": "input_group",
            "fields": [
                {
                    "id": "basic_wind_speed",
                    "label": "Basic Wind Speed (m/s):",
                    "type": "line",
                    "bind": "basic_wind_speed_input",
                },
                {
                    "id": "avg_exposed_height",
                    "label": "Average Exposed Height (m):",
                    "type": "line",
                    "default": pg_defaults.DEFAULT_AI_WIND_AVG_EXPOSED_HEIGHT_M,
                    "placeholder": pg_defaults.DEFAULT_AI_WIND_AVG_EXPOSED_HEIGHT_M,
                    "bind": "avg_exposed_height_input",
                },
                {
                    "id": "terrain_type",
                    "label": "Type of Terrain:",
                    "type": "combo",
                    "choices": ["Plain Terrain", "Terrain with Obstructions"],
                    "default": pg_defaults.DEFAULT_AI_WIND_TERRAIN_TYPE,
                    "bind": "terrain_type_combo",
                },
                {
                    "id": "site_topography",
                    "label": "Site Topography:",
                    "type": "combo",
                    "choices": ["Flat", "Hill, ridge, escarpment or cliff"],
                    "default": pg_defaults.DEFAULT_AI_WIND_SITE_TOPOGRAPHY,
                    "bind": "site_topography_combo",
                },
                {
                    "id": "gust_factor",
                    "label": "Gust Factor, G:",
                    "type": "mode_line",
                    "mode_choices": ["Automatic", "Custom"],
                    "default_mode": pg_defaults.DEFAULT_AI_WIND_GUST_FACTOR_MODE,
                    "bind_mode": "gust_factor_combo",
                    "bind_value": "gust_factor_value",
                    "default_value": pg_defaults.DEFAULT_AI_WIND_GUST_FACTOR,
                    "placeholder": pg_defaults.DEFAULT_AI_WIND_GUST_FACTOR,
                    "on_mode_change": "_toggle_wind_custom_input",
                },
                {
                    "id": "drag_coeff",
                    "label": "Drag Coefficient, CD:",
                    "type": "mode_line",
                    "mode_choices": ["Automatic", "Custom"],
                    "default_mode": pg_defaults.DEFAULT_AI_WIND_DRAG_COEFF_MODE,
                    "bind_mode": "drag_coeff_combo",
                    "bind_value": "drag_coeff_value",
                    "placeholder": "Custom Value",
                    "on_mode_change": "_toggle_wind_custom_input",
                },
                {
                    "id": "drag_coeff_ll",
                    "label": "Drag Coefficient against Live Load, CDLL:",
                    "type": "mode_line",
                    "mode_choices": ["Automatic", "Custom"],
                    "default_mode": pg_defaults.DEFAULT_AI_WIND_DRAG_COEFF_LL_MODE,
                    "bind_mode": "drag_coeff_ll_combo",
                    "bind_value": "drag_coeff_ll_value",
                    "default_value": pg_defaults.DEFAULT_AI_WIND_DRAG_COEFF_LL,
                    "placeholder": pg_defaults.DEFAULT_AI_WIND_DRAG_COEFF_LL,
                    "on_mode_change": "_toggle_wind_custom_input",
                },
                {
                    "id": "lift_coeff",
                    "label": "Lift Coefficient, CL:",
                    "type": "mode_line",
                    "mode_choices": ["Automatic", "Custom"],
                    "default_mode": pg_defaults.DEFAULT_AI_WIND_LIFT_COEFF_MODE,
                    "bind_mode": "lift_coeff_combo",
                    "bind_value": "lift_coeff_value",
                    "default_value": pg_defaults.DEFAULT_AI_WIND_LIFT_COEFF,
                    "placeholder": pg_defaults.DEFAULT_AI_WIND_LIFT_COEFF,
                    "on_mode_change": "_toggle_wind_custom_input",
                },
                {
                    "id": "super_area_elev",
                    "label": "Superstructure Area in Elevation (m²):",
                    "type": "mode_line",
                    "mode_choices": ["Automatic", "Custom"],
                    "default_mode": pg_defaults.DEFAULT_AI_WIND_SUPER_AREA_ELEV_MODE,
                    "bind_mode": "super_area_elev_combo",
                    "bind_value": "super_area_elev_value",
                    "placeholder": "Custom Value",
                    "on_mode_change": "_toggle_wind_custom_input",
                },
                {
                    "id": "super_area_plain",
                    "label": "Superstructure Area in Plain (m²):",
                    "type": "mode_line",
                    "mode_choices": ["Automatic", "Custom"],
                    "default_mode": pg_defaults.DEFAULT_AI_WIND_SUPER_AREA_PLAIN_MODE,
                    "bind_mode": "super_area_plain_combo",
                    "bind_value": "super_area_plain_value",
                    "placeholder": "Custom Value",
                    "on_mode_change": "_toggle_wind_custom_input",
                },
                {
                    "id": "exposed_frontal_area",
                    "label": "Exposed Frontal Area of Live Load (m²):",
                    "type": "mode_line",
                    "mode_choices": ["Automatic", "Custom"],
                    "default_mode": pg_defaults.DEFAULT_AI_WIND_EXPOSED_FRONTAL_AREA_MODE,
                    "bind_mode": "exposed_frontal_area_combo",
                    "bind_value": "exposed_frontal_area_value",
                    "placeholder": "Custom Value",
                    "on_mode_change": "_toggle_wind_custom_input",
                },
                {
                    "id": "wind_ecc_deck",
                    "label": "Wind Load Eccentricity from Top of Deck (m):",
                    "type": "mode_line",
                    "mode_choices": ["Automatic", "Custom"],
                    "default_mode": pg_defaults.DEFAULT_AI_WIND_ECC_DECK_MODE,
                    "bind_mode": "wind_ecc_deck_combo",
                    "bind_value": "wind_ecc_deck_value",
                    "placeholder": "Custom Value",
                    "on_mode_change": "_toggle_wind_custom_input",
                },
                {
                    "id": "wind_ll_ecc",
                    "label": "Wind on Live Load Eccentricity from Top of Deck (m):",
                    "type": "mode_line",
                    "mode_choices": ["Automatic", "Custom"],
                    "default_mode": pg_defaults.DEFAULT_AI_WIND_LL_ECC_MODE,
                    "bind_mode": "wind_ll_ecc_combo",
                    "bind_value": "wind_ll_ecc_value",
                    "placeholder": "Custom Value",
                    "on_mode_change": "_toggle_wind_custom_input",
                },
            ],
        },
        {
            "id": "computed_values_section",
            "title": "Computed Values",
            "type": "computed_group",
            "fields": [
                {
                    "id": "hourly_mean_wind",
                    "label": "Hourly Mean Wind Speed (m/s):",
                    "type": "computed",
                    "bind": "hourly_mean_wind",
                },
                {
                    "id": "hourly_wind_pressure",
                    "label": "Hourly Wind Pressure N/m²:",
                    "type": "computed",
                    "bind": "hourly_wind_pressure",
                },
                {
                    "id": "transverse_wind_force",
                    "label": "Transverse Wind Force N:",
                    "type": "computed",
                    "bind": "transverse_wind_force",
                },
                {
                    "id": "longitudinal_wind_force",
                    "label": "Longitudinal Wind Force N:",
                    "type": "computed",
                    "bind": "longitudinal_wind_force",
                },
                {
                    "id": "vertical_wind_force",
                    "label": "Vertical Wind Force N:",
                    "type": "computed",
                    "bind": "vertical_wind_force",
                },
                {
                    "id": "transverse_wind_ll",
                    "label": "Transverse Wind Force on Live Load N:",
                    "type": "computed",
                    "bind": "transverse_wind_ll",
                },
                {
                    "id": "longitudinal_wind_ll",
                    "label": "Longitudinal Wind Force on Live Load N:",
                    "type": "computed",
                    "bind": "longitudinal_wind_ll",
                },
            ],
        },
    ],
    "description": {
        "title": "Description Box",
        "text": (
            "Wind load calculations per IRC 6 specifications.\n\n"
            "The basic wind speed should be obtained from relevant meteorological data.\n\n"
            "Gust factor accounts for wind fluctuations.\n\n"
            "Note: Wind load eccentricity values should be negative for positions below the deck."
        ),
    },
}

TEMPERATURE_LOAD_TAB_SCHEMA = {
    "id": "temperature_load_tab",
    "label_width": 240,
    "field_width": 140,
    "sections": [
        {
            "id": "temperature_inputs_section",
            "title": "Temperature Load (TL) Inputs for Evaluation per IRC6",
            "type": "input_group",
            "fields": [
                {
                    "id": "highest_max_temp",
                    "label": "Highest Maximum Air Temperature\n(°C):",
                    "type": "line",
                    "placeholder": "From Project Location",
                    "bind": "highest_max_temp_input",
                    "validator": {"type": "double_range", "bottom": -50.0, "top": 100.0, "decimals": 2},
                },
                {
                    "id": "lowest_min_temp",
                    "label": "Lowest Minimum Air Temperature\n(°C):",
                    "type": "line",
                    "placeholder": "From Project Location",
                    "bind": "lowest_min_temp_input",
                    "validator": {"type": "double_range", "bottom": -50.0, "top": 100.0, "decimals": 2},
                },
                {
                    "id": "thermal_coeff_steel",
                    "label": "Coefficient of Thermal Expansion for Steel\n(1/°C):",
                    "type": "line",
                    "default": pg_defaults.DEFAULT_AI_TEMP_THERMAL_COEFF_STEEL_PER_C,
                    "bind": "thermal_coeff_steel_input",
                    "validator": {"type": "double_range", "bottom": 0.0, "top": 1.0, "decimals": 8},
                },
                {
                    "id": "thermal_coeff_rcc",
                    "label": "Coefficient of Thermal Expansion for RCC\n(1/°C):",
                    "type": "line",
                    "default": pg_defaults.DEFAULT_AI_TEMP_THERMAL_COEFF_RCC_PER_C,
                    "bind": "thermal_coeff_rcc_input",
                    "validator": {"type": "double_range", "bottom": 0.0, "top": 1.0, "decimals": 8},
                },
            ],
        },
        {
            "id": "bridge_temp_range_section",
            "title": "Range of Effective Bridge Temperature:",
            "type": "output_group",
            "fields": [
                {
                    "id": "bridge_temp_min",
                    "label": "Minimum (°C):",
                    "type": "line",
                    "read_only": True,
                    "bind": "bridge_temp_min_input",
                },
                {
                    "id": "bridge_temp_max",
                    "label": "Maximum (°C):",
                    "type": "line",
                    "read_only": True,
                    "bind": "bridge_temp_max_input",
                },
            ],
        },
        {
            "id": "temp_design_section",
            "title": "Temperature for Design:",
            "type": "output_group",
            "fields": [
                {
                    "id": "temp_rise",
                    "label": "Rise (°C):",
                    "type": "line",
                    "read_only": True,
                    "bind": "temp_rise_input",
                },
                {
                    "id": "temp_fall",
                    "label": "Fall (°C):",
                    "type": "line",
                    "read_only": True,
                    "bind": "temp_fall_input",
                },
            ],
        },
    ],
}

CUSTOM_LOAD_TAB_SCHEMA = {
    "id": "custom_load_tab",
    "label_width": 260,
    "field_width": 140,
    "load_case_choices": [
        "DL", "DW", "SIDL", "LL", "EL", "WL", "TL", "Custom"
    ],
    "load_type_choices": ["Point", "Line", "Area"],
    "fields": {
        "load_case": {
            "id": "custom_load_case",
            "label": "Load Case:",
            "type": "combo",
            "bind": "custom_load_case_combo",
        },
        "custom_load_case_name": {
            "id": "custom_load_case_name",
            "label": "",  # Hidden label, uses spacer
            "type": "line",
            "placeholder": "custom",
            "bind": "custom_load_case_name_input",
            "enabled": False,
        },
        "load_type": {
            "id": "custom_load_type",
            "label": "Load Type:",
            "type": "combo",
            "bind": "custom_load_type_combo",
        },
        "point_left": {
            "id": "custom_point_left",
            "label": "Distance from Left Edge of Bridge (m):",
            "type": "line",
            "bind": "custom_point_left_input",
            "validator": {"type": "double_range", "bottom": 0.0, "top": 1000.0, "decimals": 3},
        },
        "point_bearing": {
            "id": "custom_point_bearing",
            "label": "Distance from Center Line of Bearing (m):",
            "type": "line",
            "bind": "custom_point_bearing_input",
            "validator": {"type": "double_range", "bottom": -1000.0, "top": 1000.0, "decimals": 3},
        },
        "line_left_start": {
            "id": "custom_line_left_start",
            "label": "Distance from Left Edge of Bridge (m):",
            "sub_label": "Start",
            "type": "line",
            "bind": "custom_line_left_start",
            "field_width": 70,
            "validator": {"type": "double_range", "bottom": 0.0, "top": 1000.0, "decimals": 3},
        },
        "line_left_end": {
            "id": "custom_line_left_end",
            "sub_label": "End",
            "type": "line",
            "bind": "custom_line_left_end",
            "field_width": 70,
            "validator": {"type": "double_range", "bottom": 0.0, "top": 1000.0, "decimals": 3},
        },
        "line_bearing_start": {
            "id": "custom_line_bearing_start",
            "label": "Distance from Center Line of Bearing (m):",
            "sub_label": "Start",
            "type": "line",
            "bind": "custom_line_bearing_start",
            "field_width": 70,
            "validator": {"type": "double_range", "bottom": -1000.0, "top": 1000.0, "decimals": 3},
        },
        "line_bearing_end": {
            "id": "custom_line_bearing_end",
            "sub_label": "End",
            "type": "line",
            "bind": "custom_line_bearing_end",
            "field_width": 70,
            "validator": {"type": "double_range", "bottom": -1000.0, "top": 1000.0, "decimals": 3},
        },
    },
}

LOAD_COMBINATION_TAB_SCHEMA = {
    "id": "load_combination_tab",
    "label_width": 280,
    "rows": [
        {
            "fields": [
                {
                    "id": "auto_include_irc6",
                    "label": "Auto include all IRC 6 Load Combinations",
                    "type": "checkbox",
                    "bind": "auto_include_checkbox",
                }
            ]
        },
    ],
    "controls": [
        {
            "id": "add",
            "label": "Add",
            "type": "button",
            "bind": "load_combo_add_btn",
            "width": 60,
        },
        {
            "id": "edit",
            "label": "Edit",
            "type": "button",
            "bind": "load_combo_edit_btn",
            "width": 60,
        },
        {
            "id": "delete",
            "label": "Delete",
            "type": "button",
            "bind": "load_combo_delete_btn",
            "width": 60,
        },
        {
            "id": "default",
            "label": "Default",
            "type": "button",
            "bind": "load_combo_default_btn",
            "width": 60,
        },
    ],
}

SUPPORT_CONDITIONS_SCHEMA = {
    "id": "support_conditions",
    "title": "Support Conditions",
    "sections": [
        {
            "title": "Support Condition*",
            "fields": [
                {
                    "id": "left_support",
                    "label": "Left Support:",
                    "type": "combo",
                    "choices": ["Fixed", "Pinned", "Roller"],
                    "default": pg_defaults.DEFAULT_AI_SUPPORT_LEFT,
                    "bind": "left_support_combo",
                },
                {
                    "id": "right_support",
                    "label": "Right Support:",
                    "type": "combo",
                    "choices": ["Fixed", "Pinned", "Roller"],
                    "default": pg_defaults.DEFAULT_AI_SUPPORT_RIGHT,
                    "bind": "right_support_combo",
                },
            ],
        },
        {
            "title": "Bearing length*",
            "fields": [
                {
                    "id": "bearing_length",
                    "label": "Bearing Length Value",
                    "type": "line",
                    "default": pg_defaults.DEFAULT_AI_SUPPORT_BEARING_LENGTH,
                    "placeholder": "Length",
                    "bind": "bearing_length_input",
                    "validator": {
                        "type": "double_range",
                        "bottom": 0.0,
                        "top": 1e6,
                        "decimals": 3,
                    },
                }
            ],
        },
    ],
}

DESIGN_OPTIONS_SCHEMA = {
    "id": "design_options",
    "live_validation": {
        "enabled": True,
        "fields": ["shear_stud_diameter", "shear_stud_height"],
    },
    "cards": [
        {
            "title": "Construction Stage",
            "field_width": 150,
            "sections": [
                {
                    "fields": [
                        {
                            "id": "construction_stage",
                            "label": "Included:",
                            "type": "combo",
                            "choices": ["Yes", "No"],
                            "default": pg_defaults.DEFAULT_AI_DESIGN_CONSTRUCTION_STAGE,
                            "bind": "construction_stage_combo",
                        }
                    ]
                }
            ],
        },
        {
            "title": "Deck and Shear Studs",
            "field_width": 150,
            "sections": [
                {
                    "title": "Deck Design:",
                    "fields": [
                        {
                            "id": "reinforcement_size",
                            "label": "Reinforcement Size:",
                            "type": "combo",
                            "choices": ["8 mm", "10 mm", "12 mm", "16 mm", "20 mm"],
                            "default": pg_defaults.DEFAULT_AI_DESIGN_REINFORCEMENT_SIZE,
                            "bind": "reinforcement_size_combo",
                        },
                        {
                            "id": "reinforcement_material",
                            "label": "Reinforcement Material:",
                            "type": "combo",
                            "choices": ["Fe 415", "Fe 500", "Fe 550"],
                            "default": pg_defaults.DEFAULT_AI_DESIGN_REINFORCEMENT_MATERIAL,
                            "bind": "reinforcement_material_combo",
                        },
                    ],
                },
                {
                    "title": "Shear Studs:",
                    "fields": [
                        {
                            "id": "shear_stud_material",
                            "label": "Material:",
                            "type": "line",
                            "placeholder": "Material",
                            "default": pg_defaults.DEFAULT_AI_DESIGN_SHEAR_STUD_MATERIAL,
                            "bind": "shear_stud_material_input",
                        },
                        {
                            "id": "shear_stud_diameter",
                            "label": "Diameter (mm):",
                            "type": "line",
                            "default": pg_defaults.DEFAULT_AI_DESIGN_SHEAR_STUD_DIAMETER,
                            "bind": "shear_stud_diameter_input",
                        },
                        {
                            "id": "shear_stud_height",
                            "label": "Height (mm):",
                            "type": "line",
                            "default": pg_defaults.DEFAULT_AI_DESIGN_SHEAR_STUD_HEIGHT,
                            "bind": "shear_stud_height_input",
                        },
                    ],
                },
            ],
        },
    ],
}

DESIGN_OPTIONS_CONT_SCHEMA = {
    "id": "design_options_cont",
    "live_validation": {
        "enabled": True,
        "fields": [
            "gamma_c_basic",
            "gamma_c_accidental",
            "gamma_m0",
            "gamma_m1",
            "gamma_s",
            "gamma_v",
            "gamma_flt",
            "gamma_mf",
            "load_cycles",
            "k1",
            "k3",
            "k4",
            "k6",
            "limit_l",
            "k3_second",
            "k4_second",
        ],
    },
    "sections": [
        {
            "title": "Partial Safety Factors",
            "field_width": 150,
            "fields": [
                {"id": "gamma_c_basic", "label": "Concrete basic & seismic(Gamma_C)", "type": "line", "default": pg_defaults.DEFAULT_AI_DESIGN_CONT_GAMMA_C_BASIC, "bind": "gamma_c_basic_input"},
                {"id": "gamma_c_accidental", "label": "Concrete Accidental (Gamma_C)", "type": "line", "default": pg_defaults.DEFAULT_AI_DESIGN_CONT_GAMMA_C_ACCIDENTAL, "bind": "gamma_c_accidental_input"},
                {"id": "gamma_m0", "label": "Structural steel for Yielding and Buckling(Gamma_M0)", "type": "line", "default": pg_defaults.DEFAULT_AI_DESIGN_CONT_GAMMA_M0, "bind": "gamma_m0_input"},
                {"id": "gamma_m1", "label": "Structural Steel For Ultimate Stress(Gamme_M1)", "type": "line", "default": pg_defaults.DEFAULT_AI_DESIGN_CONT_GAMMA_M1, "bind": "gamma_m1_input"},
                {"id": "gamma_s", "label": "Reinforcing Steel (Gamma_s)", "type": "line", "default": pg_defaults.DEFAULT_AI_DESIGN_CONT_GAMMA_S, "bind": "gamma_s_input"},
                {"id": "gamma_v", "label": "Shear Connectors For Yield(Gamma_v)", "type": "line", "default": pg_defaults.DEFAULT_AI_DESIGN_CONT_GAMMA_V, "bind": "gamma_v_input"},
                {"id": "gamma_flt", "label": "Fatigue Load(Gamma_flt)", "type": "line", "default": pg_defaults.DEFAULT_AI_DESIGN_CONT_GAMMA_FLT, "bind": "gamma_flt_input"},
                {"id": "gamma_mf", "label": "Fatigue Strength(Gamma_Mf, t)", "type": "line", "default": pg_defaults.DEFAULT_AI_DESIGN_CONT_GAMMA_MF, "bind": "gamma_mf_input"},
            ],
        },
        {
            "title": "Number of Load Cycles",
            "field_width": 200,
            "fields": [
                {
                    "id": "load_cycles",
                    "label": "Number of Load Cycles(Cl605.3,Cl605.4)",
                    "type": "line",
                    "default": pg_defaults.DEFAULT_AI_DESIGN_CONT_LOAD_CYCLES,
                    "bind": "load_cycles_input",
                }
            ],
        },
        {
            "title": "K Factors",
            "field_width": 120,
            "fields": [
                {
                    "row_fields": [
                        {"id": "k1", "label": "K1:", "type": "line", "default": pg_defaults.DEFAULT_AI_DESIGN_CONT_K1, "bind": "k1_input", "width": 80},
                        {"id": "k3", "label": "K3:", "type": "line", "default": pg_defaults.DEFAULT_AI_DESIGN_CONT_K3, "bind": "k3_input", "width": 80},
                        {"id": "k4", "label": "K4:", "type": "line", "default": pg_defaults.DEFAULT_AI_DESIGN_CONT_K4, "bind": "k4_input", "width": 80},
                        {"id": "k6", "label": "K6:", "type": "line", "default": pg_defaults.DEFAULT_AI_DESIGN_CONT_K6, "bind": "k6_input", "width": 80},
                    ]
                },
                {
                    "row_fields": [
                        {"id": "limit_l", "label": "Limit : L (m)", "type": "line", "default": pg_defaults.DEFAULT_AI_DESIGN_CONT_LIMIT_L, "bind": "limit_input", "width": 120}
                    ]
                },
                {
                    "row_fields": [
                        {"id": "k3_second", "label": "K3:", "type": "line", "default": pg_defaults.DEFAULT_AI_DESIGN_CONT_K3_SECOND, "bind": "k3_second_input", "width": 80},
                        {"id": "k4_second", "label": "K4:", "type": "line", "default": pg_defaults.DEFAULT_AI_DESIGN_CONT_K4_SECOND, "bind": "k4_second_input", "width": 80},
                        {"id": "exposure", "label": "Exposure:", "type": "line", "bind": "exposure_input", "width": 100},
                    ]
                },
            ],
        },
        {
            "title": "Post-buckling",
            "fields": [
                {
                    "id": "post_buckling",
                    "label": "Post-buckling Tension Field Action for Shear Resistance",
                    "type": "checkbox",
                    "bind": "post_buckling_checkbox",
                }
            ],
        },
        {
            "title": "Limit States",
            "checkbox_groups": [
                {
                    "title": "Ultimate Limit States",
                    "items": [
                        "Bending Resistance",
                        "Resistance to Vertical Shear",
                        "Resistance to Lateral-torsional Buckling",
                        "Resistance to Transverse force",
                        "Resistance to Longitudinal Shear",
                        "Resistance to Fatigue",
                    ],
                    "bind": "ultimate_checkboxes",
                },
                {
                    "title": "Serviceability Limit States",
                    "items": [
                        "Stress Limitation",
                        "Longitudinal Shear (SLS)",
                        "Deflection Control",
                        "Crack Width Check",
                    ],
                    "bind": "service_checkboxes",
                },
            ],
        },
    ],
}

GIRDER_DETAILS_SCHEMA = {
    "overview": [
        {
            "id": "select_girder",
            "label": "Select Girder:",
            "type": "combo_dynamic",
            "bind": "select_girder_combo",
            "include_all": True,
        },
        {
            "id": "span",
            "label": "Span:",
            "type": "combo",
            "choices": VALUES_GIRDER_SPAN_MODE,
            "bind": "span_combo",
        },
    ],
    "section_inputs": [
        {
            "id": "design",
            "label": "Design:",
            "type": "combo",
            "choices": VALUES_GIRDER_DESIGN_MODE,
            "bind": "design_combo",
            "visible_for": ["welded"],
        },
        {
            "id": "type",
            "label": "Type:",
            "type": "combo",
            "choices": VALUES_GIRDER_TYPE,
            "bind": "type_combo",
        },
        {
            "id": "symmetry",
            "label": "Symmetry:",
            "type": "combo",
            "choices": VALUES_GIRDER_SYMMETRY,
            "bind": "symmetry_combo",
            "visible_for": ["welded"],
        },
        {
            "id": "depth",
            "label": "Total Depth (mm):",
            "type": "mode_line",
            "mode_choices": ["Optimized", "Customized"],
            "default_mode": pg_defaults.DEFAULT_AI_GIRDER_DEPTH_MODE,
            "bind_mode": "depth_mode_combo",
            "bind_value": "depth_input",
            "visible_for": ["welded"],
        },
        {
            "id": "top_flange_width",
            "label": "Top Flange Width (mm):",
            "type": "mode_line",
            "mode_choices": ["Optimized", "Customized"],
            "default_mode": pg_defaults.DEFAULT_AI_GIRDER_TOP_FLANGE_WIDTH_MODE,
            "bind_mode": "top_width_mode_combo",
            "bind_value": "top_width_input",
            "visible_for": ["welded"],
        },
        {
            "id": "top_flange_thickness",
            "label": "Top Flange Thickness (mm):",
            "type": "mode_line",
            "mode_choices": VALUES_PROFILE_SCOPE,
            "default_mode": pg_defaults.DEFAULT_AI_GIRDER_TOP_FLANGE_THICKNESS_MODE,
            "bind_mode": "top_thickness_mode_combo",
            "bind_value": "top_thickness_input",
            "visible_for": ["welded"],
        },
        {
            "id": "bottom_flange_width",
            "label": "Bottom Flange Width (mm):",
            "type": "mode_line",
            "mode_choices": ["Optimized", "Customized"],
            "default_mode": pg_defaults.DEFAULT_AI_GIRDER_BOTTOM_FLANGE_WIDTH_MODE,
            "bind_mode": "bottom_width_mode_combo",
            "bind_value": "bottom_width_input",
            "visible_for": ["welded"],
        },
        {
            "id": "bottom_flange_thickness",
            "label": "Bottom Flange Thickness (mm):",
            "type": "mode_line",
            "mode_choices": VALUES_PROFILE_SCOPE,
            "default_mode": pg_defaults.DEFAULT_AI_GIRDER_BOTTOM_FLANGE_THICKNESS_MODE,
            "bind_mode": "bottom_thickness_mode_combo",
            "bind_value": "bottom_thickness_input",
            "visible_for": ["welded"],
        },
        {
            "id": "web_thickness",
            "label": "Web Thickness (mm):",
            "type": "mode_line",
            "mode_choices": VALUES_PROFILE_SCOPE,
            "default_mode": pg_defaults.DEFAULT_AI_GIRDER_WEB_THICKNESS_MODE,
            "bind_mode": "web_thickness_mode_combo",
            "bind_value": "web_thickness_input",
            "visible_for": ["welded"],
        },
        {
            "id": "is_section",
            "label": "IS Section:",
            "type": "combo",
            "choices": [
                "ISMB 500", "ISMB 550", "ISMB 600",
                "ISWB 500", "ISWB 550", "ISWB 600",
            ],
            "bind": "is_section_combo",
            "visible_for": ["rolled"],
        },
        {
            "id": "torsional_restraint",
            "label": "Torsional Restraint:",
            "type": "combo",
            "choices": VALUES_TORSIONAL_RESTRAINT,
            "bind": "torsion_combo",
        },
        {
            "id": "warping_restraint",
            "label": "Warping Restraint:",
            "type": "combo",
            "choices": VALUES_WARPING_RESTRAINT,
            "bind": "warping_combo",
        },
        {
            "id": "web_type",
            "label": "Web Type*:",
            "type": "combo",
            "choices": VALUES_WEB_TYPE,
            "bind": "web_type_combo",
        },
    ],
}

#function -> store in dict design dict

# ---------------------------------------------------------------------------
# ADDITIONAL INPUTS TAB HIERARCHY CONFIG
# ---------------------------------------------------------------------------
# Declarative map of top-level tabs → sub-tabs used throughout the codebase
# to build and track the nested inputs dictionary:
#   { top_tab_id: { sub_tab_id: { field_key: value } } }
#
# Tabs that delegate to custom widget classes list "schema": None; schema-driven
# tabs reference their schema constant by name for documentation purposes.
# ---------------------------------------------------------------------------

ADDITIONAL_INPUTS_TAB_CONFIG = [
    {
        "id": "typical_section",
        "label": "Typical Section Details",
        "sub_tabs": [
            {"id": "layout",        "label": "Layout",        "schema": "LAYOUT_TAB_SCHEMA"},
            {"id": "crash_barrier", "label": "Crash Barrier", "schema": "CRASH_BARRIER_TAB_SCHEMA"},
            {"id": "median",        "label": "Median",        "schema": "MEDIAN_TAB_SCHEMA"},
            {"id": "railing",       "label": "Railing",       "schema": "RAILING_TAB_SCHEMA"},
            {"id": "wearing_course","label": "Wearing Course","schema": "WEARING_COURSE_TAB_SCHEMA"},
            {"id": "lane_details",  "label": "Lane Details",  "schema": "LANE_DETAILS_TAB_SCHEMA"},
        ],
    },
    {
        "id": "member_properties",
        "label": "Member Properties",
        "sub_tabs": [
            {"id": "girder_details",    "label": "Girder Details",     "schema": "GIRDER_DETAILS_SCHEMA"},
            {"id": "stiffener_details", "label": "Stiffener Details",  "schema": "STIFFENER_DETAILS_SCHEMA"},
            {"id": "cross_bracing",     "label": "Cross-Bracing",      "schema": "CROSS_BRACING_DETAILS_SCHEMA"},
            {"id": "end_diaphragm",     "label": "End Diaphragm",      "schema": "END_DIAPHRAGM_DETAILS_SCHEMA"},
        ],
    },
    {
        "id": "loading",
        "label": "Loading",
        "sub_tabs": [
            {"id": "permanent_load",   "label": "Permanent Load",    "schema": "PERMANENT_LOAD_TAB_SCHEMA"},
            {"id": "live_load",        "label": "Live Load",          "schema": "LIVE_LOAD_TAB_SCHEMA"},
            {"id": "seismic_load",     "label": "Seismic Load",       "schema": "SEISMIC_LOAD_TAB_SCHEMA"},
            {"id": "wind_load",        "label": "Wind Load",          "schema": "WIND_LOAD_TAB_SCHEMA"},
            {"id": "temperature_load", "label": "Temperature Load",   "schema": "TEMPERATURE_LOAD_TAB_SCHEMA"},
            {"id": "custom_load",      "label": "Custom Load",        "schema": "CUSTOM_LOAD_TAB_SCHEMA"},
            {"id": "load_combination", "label": "Load Combination",   "schema": "LOAD_COMBINATION_TAB_SCHEMA"},
        ],
    },
    {
        "id": "support_conditions",
        "label": "Support Conditions",
        "sub_tabs": [
            {"id": "support_conditions", "label": "Support Conditions", "schema": "SUPPORT_CONDITIONS_SCHEMA"},
        ],
    },
    {
        "id": "design_options",
        "label": "Analysis/Design Options",
        "sub_tabs": [
            {"id": "design_options", "label": "Design Options", "schema": "DESIGN_OPTIONS_SCHEMA"},
        ],
    },
    {
        "id": "design_options_cont",
        "label": "Design Options (Cont.)",
        "sub_tabs": [
            {"id": "design_options_cont", "label": "Design Options (Cont.)", "schema": "DESIGN_OPTIONS_CONT_SCHEMA"},
        ],
    },
]
