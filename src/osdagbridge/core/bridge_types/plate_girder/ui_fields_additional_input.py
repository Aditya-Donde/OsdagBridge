"""Consolidated UI schemas for plate girder Additional Inputs dialogs.

This module groups all schema dictionaries used by the Additional Inputs
flow, including Typical Section Details, Support/Design options, and
Member Properties.
"""

from osdagbridge.core.utils.common import (
    DEFAULT_CRASH_BARRIER_WIDTH,
    DEFAULT_GIRDER_SPACING,
    DEFAULT_RAILING_WIDTH,
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
                    "on_text_changed": "on_girder_spacing_changed",
                },
                {
                    "id": "no_of_girders",
                    "label": "No. of Girders:",
                    "type": "line",
                    "validator": {"type": "int_range", "bottom": 1, "top": 100},
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
                    "default": "200",
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
                    "default": f"{MIN_FOOTPATH_WIDTH:.2f}",
                    "bind": "footpath_width",
                    "on_text_changed": "on_footpath_width_changed",
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
PERMANENT_LOAD_TAB_SCHEMA = {
    "id": "permanent_load_tab",
    "label_width": 220,
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

LIVE_LOAD_TAB_SCHEMA = {
    "id": "live_load_tab",
    "label_width": 220,
    "field_width": 180,
    "field_height": 28,
    "sections": [
        {
            "id": "irc_vehicles_section",
            "title": "Vehicles from IRC 6",
            "type": "checkbox_list",
            "items": [
                "Class A",
                "Class 70R Wheeled",
                "Class 70R Tracked",
                "Class AA Wheeled",
                "Class AA Tracked",
                "Class SV",
                "Class 70R Bogie",
            ],
            "bind": "irc_vehicle_checkboxes",
            "default_checked": True,
        },
        {
            "id": "custom_vehicle_section",
            "title": "Custom Vehicle",
            "type": "custom_vehicle_table",
            "bind": "custom_vehicle_table",
            "add_button_bind": "custom_vehicle_add_button",
        },
        {
            "id": "braking_section",
            "title": "Braking Load from Vehicles",
            "type": "dynamic_checkbox_list",
            "bind": "braking_vehicle_checkboxes",
            "default_checked": True,
        },
        {
            "id": "eccentricity",
            "label": "Eccentricity from top of Deck (m)",
            "type": "line",
            "validator": {"type": "double_range", "bottom": 0.0, "top": 100.0, "decimals": 2},
            "default": "0.00",
            "bind": "eccentricity_input",
        },
        {
            "id": "footpath_pressure",
            "label": "Footpath Pressure (kN/mm²)",
            "type": "mode_line",
            "mode_choices": ["Automatic", "User-defined"],
            "default_mode": "Automatic",
            "bind_mode": "footpath_mode_combo",
            "bind_value": "footpath_value_input",
            "default_value": "5.00",
            "mode_width": 120,
            "value_width": 80,
            "on_mode_change": "_on_footpath_mode_changed",
        },
    ],
    "description": {
        "title": "Description Box",
        "text": (
            "211.2 The braking effect on a simply supported span or a continuous unit of spans or on any other type of bridge unit shall be assumed to have the following value:\n\n"
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
            "title": "Seismic/Earthquake Load (EL) Inputs",
            "type": "input_group",
            "fields": [
                {
                    "id": "seismic_zone",
                    "label": "Seismic Zone",
                    "type": "line",
                    "bind": "seismic_zone_combo",
                },
                {
                    "id": "importance_factor",
                    "label": "Importance Factor, I",
                    "type": "line",
                    "default": "1.0",
                    "bind": "importance_factor_input",
                },
                {
                    "id": "soil_type",
                    "label": "Type of Soil",
                    "type": "combo",
                    "choices": [
                        "Type I – Rocky or Hard",
                        "Type II – Medium Soil",
                        "Type III – Soft Soil",
                    ],
                    "default": "Type I – Rocky or Hard Soil",
                    "bind": "soil_type_combo",
                },
                {
                    "id": "time_period",
                    "label": "Fundamental Time Period, T (sec)",
                    "type": "line",
                    "bind": "time_period_input",
                },
                {
                    "id": "damping",
                    "label": "Damping Percentage",
                    "type": "line",
                    "default": "2",
                    "bind": "damping_input",
                },
                {
                    "id": "response_reduction_factor",
                    "label": "Response Reduction Factor, R",
                    "type": "combo",
                    "choices": ["1", "2", "3", "4", "5"],
                    "default": "1",
                    "bind": "response_factor_combo",
                },
                {
                    "id": "dead_load_seismic",
                    "label": "Dead Load for Seismic Force (kN)",
                    "type": "mode_line",
                    "mode_choices": ["Automatic", "Custom"],
                    "default_mode": "Automatic",
                    "bind_mode": "dead_load_seismic_combo",
                    "bind_value": "dead_load_custom_input",
                    "placeholder": "Custom Value",
                    "on_mode_change": "_toggle_seismic_custom_inputs",
                },
                {
                    "id": "live_load_seismic",
                    "label": "Live Load for Seismic Force (kN)",
                    "type": "mode_line",
                    "mode_choices": ["Automatic", "Custom"],
                    "default_mode": "Automatic",
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
                    "label": "Zone Factor, Z",
                    "type": "computed",
                    "bind": "zone_factor",
                },
                {
                    "id": "spectral_coeff",
                    "label": "Spectral Acceleration Coefficient, S<sub>a</sub>/g",
                    "type": "computed",
                    "bind": "spectral_coeff",
                },
                {
                    "id": "horizontal_coeff",
                    "label": "Horizontal Seismic Coefficient, A<sub>h</sub>",
                    "type": "computed",
                    "bind": "horizontal_coeff",
                },
                {
                    "id": "vertical_coeff",
                    "label": "Vertical Seismic Coefficient, A<sub>v</sub>",
                    "type": "computed",
                    "bind": "vertical_coeff",
                },
            ],
        },
    ],
    "description": {
        "title": "Description Box",
        "text": (
            "Seismic Zone is auto-filled from software output (project location).\n\n"
            "The spectral acceleration coefficient depends on soil type and "
            "fundamental time period, T.\n\n"
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
            "title": "Wind Load (WL) Inputs",
            "type": "input_group",
            "fields": [
                {
                    "id": "basic_wind_speed",
                    "label": "Basic Wind Speed, V<sub>b</sub> (m/s)",
                    "type": "line",
                    "read_only": True,
                    "enabled": False,
                    "bind": "basic_wind_speed_input",
                },
                {
                    "id": "avg_exposed_height",
                    "label": "Average Exposed Height, H (m)",
                    "type": "line",
                    "default": "10",
                    "placeholder": "10",
                    "bind": "avg_exposed_height_input",
                },
                {
                    "id": "terrain_type",
                    "label": "Type of Terrain",
                    "type": "combo",
                    "choices": ["Plain Terrain", "Terrain with \nObstructions"],
                    "default": "Plain Terrain",
                    "bind": "terrain_type_combo",
                },
                {
                    "id": "site_topography",
                    "label": "Site Topography",
                    "type": "combo",
                    "choices": ["Flat", "Hill, ridge, escarpment or cliff"],
                    "default": "Flat",
                    "bind": "site_topography_combo",
                },
                {
                    "id": "gust_factor",
                    "label": "Gust Factor, G",
                    "type": "mode_line",
                    "mode_choices": ["As per Code", "Custom"],
                    "default_mode": "As per Code",
                    "bind_mode": "gust_factor_combo",
                    "bind_value": "gust_factor_value",
                    "default_value": "2",
                    "placeholder": "2",
                    "on_mode_change": "_toggle_wind_custom_input",
                },
                {
                    "id": "drag_coeff",
                    "label": "Drag Coefficient, C<sub>D</sub>",
                    "type": "mode_line",
                    "mode_choices": ["As per Code", "Custom"],
                    "default_mode": "As per Code",
                    "bind_mode": "drag_coeff_combo",
                    "bind_value": "drag_coeff_value",
                    "placeholder": "Custom Value",
                    "on_mode_change": "_toggle_wind_custom_input",
                },
                {
                    "id": "drag_coeff_ll",
                    "label": "Drag Coefficient against Live Load, C<sub>DLL</sub>",
                    "type": "mode_line",
                    "mode_choices": ["As per Code", "Custom"],
                    "default_mode": "As per Code",
                    "bind_mode": "drag_coeff_ll_combo",
                    "bind_value": "drag_coeff_ll_value",
                    "default_value": "1.2",
                    "placeholder": "1.2",
                    "on_mode_change": "_toggle_wind_custom_input",
                },
                {
                    "id": "lift_coeff",
                    "label": "Lift Coefficient, C<sub>L</sub>",
                    "type": "mode_line",
                    "mode_choices": ["As per Code", "Custom"],
                    "default_mode": "As per Code",
                    "bind_mode": "lift_coeff_combo",
                    "bind_value": "lift_coeff_value",
                    "default_value": "0.75",
                    "placeholder": "0.75",
                    "on_mode_change": "_toggle_wind_custom_input",
                },
                {
                    "id": "super_area_elev",
                    "label": "Superstructure Area in Elevation, A<sub>1</sub> (m²)",
                    "type": "mode_line",
                    "mode_choices": ["Automatic", "Custom"],
                    "default_mode": "Automatic",
                    "bind_mode": "super_area_elev_combo",
                    "bind_value": "super_area_elev_value",
                    "placeholder": "Custom Value",
                    "on_mode_change": "_toggle_wind_custom_input",
                },
                {
                    "id": "super_area_plain",
                    "label": "Superstructure Area in Plain, A<sub>3</sub> (m²)",
                    "type": "mode_line",
                    "mode_choices": ["Automatic", "Custom"],
                    "default_mode": "Automatic",
                    "bind_mode": "super_area_plain_combo",
                    "bind_value": "super_area_plain_value",
                    "placeholder": "Custom Value",
                    "on_mode_change": "_toggle_wind_custom_input",
                },
                {
                    "id": "exposed_frontal_area",
                    "label": "Exposed Frontal Area of Live Load, A<sub>1LL</sub> (m²)",
                    "type": "mode_line",
                    "mode_choices": ["Automatic", "Custom"],
                    "default_mode": "Automatic",
                    "bind_mode": "exposed_frontal_area_combo",
                    "bind_value": "exposed_frontal_area_value",
                    "placeholder": "Custom Value",
                    "on_mode_change": "_toggle_wind_custom_input",
                },
                {
                    "id": "wind_ecc_deck",
                    "label": "Wind Load Eccentricity from \nTop of Deck (m)",
                    "type": "mode_line",
                    "mode_choices": ["As per Code", "Custom"],
                    "default_mode": "As per Code",
                    "bind_mode": "wind_ecc_deck_combo",
                    "bind_value": "wind_ecc_deck_value",
                    "placeholder": "Custom Value",
                    "on_mode_change": "_toggle_wind_custom_input",
                },
                {
                    "id": "wind_ll_ecc",
                    "label": "Wind on Live Load Eccentricity from \nTop of Deck (m)",
                    "type": "mode_line",
                    "mode_choices": ["As per Code", "Custom"],
                    "default_mode": "As per Code",
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
                    "label": "Hourly Mean Wind Speed, V<sub>z</sub> (m/s)",
                    "type": "computed",
                    "bind": "hourly_mean_wind",
                },
                {
                    "id": "hourly_wind_pressure",
                    "label": "Hourly Wind Pressure, P<sub>z</sub> (N/m²)",
                    "type": "computed",
                    "bind": "hourly_wind_pressure",
                },
                {
                    "id": "transverse_wind_force",
                    "label": "Transverse Wind Force, F<sub>T</sub> (N)",
                    "type": "computed",
                    "bind": "transverse_wind_force",
                },
                {
                    "id": "longitudinal_wind_force",
                    "label": "Longitudinal Wind Force, F<sub>L</sub> (N)",
                    "type": "computed",
                    "bind": "longitudinal_wind_force",
                },
                {
                    "id": "vertical_wind_force",
                    "label": "Vertical Wind Force, F<sub>V</sub> (N)",
                    "type": "computed",
                    "bind": "vertical_wind_force",
                },
                {
                    "id": "transverse_wind_ll",
                    "label": "Transverse Wind Force on Live Load, F<sub>TLL</sub> (N)",
                    "type": "computed",
                    "bind": "transverse_wind_ll",
                },
                {
                    "id": "longitudinal_wind_ll",
                    "label": "Longitudinal Wind Force on Live Load, F<sub>LLL</sub> (N)",
                    "type": "computed",
                    "bind": "longitudinal_wind_ll",
                },
            ],
        },
    ],
    "description": {
        "title": "Description Box",
        "text": (
            "Basic Wind Speed is auto-filled from software output (project location).\n\n"
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
                    "label": "Highest Maximum Air Temperature (°C)",
                    "type": "line",
                    "placeholder": "From Project Location",
                    "bind": "highest_max_temp_input",
                    "validator": {"type": "double_range", "bottom": -50.0, "top": 100.0, "decimals": 2},
                    "enabled": False,
                },
                {
                    "id": "lowest_min_temp",
                    "label": "Lowest Minimum Air Temperature (°C)",
                    "type": "line",
                    "placeholder": "From Project Location",
                    "bind": "lowest_min_temp_input",
                    "validator": {"type": "double_range", "bottom": -50.0, "top": 100.0, "decimals": 2},
                    "enabled": False,
                },
                {
                    "id": "thermal_coeff_steel",
                    "label": "Coefficient of Thermal Expansion for Steel (1/°C)",
                    "type": "line",
                    "default": "12.0e-6",
                    "bind": "thermal_coeff_steel_input",
                    "validator": {"type": "double_range", "bottom": 0.0, "top": 1.0, "decimals": 8, "notation": "scientific"},
                },
                {
                    "id": "thermal_coeff_rcc",
                    "label": "Coefficient of Thermal Expansion for RCC (1/°C)",
                    "type": "line",
                    "default": "12.0e-6",
                    "bind": "thermal_coeff_rcc_input",
                    "validator": {"type": "double_range", "bottom": 0.0, "top": 1.0, "decimals": 8, "notation": "scientific"},
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
                    "label": "Minimum (°C)",
                    "type": "line",
                    "read_only": True,
                    "bind": "bridge_temp_min_input",
                },
                {
                    "id": "bridge_temp_max",
                    "label": "Maximum (°C)",
                    "type": "line",
                    "read_only": True,
                    "bind": "bridge_temp_max_input",
                },
            ],
        },
        {
            "id": "temp_design_section",
            "title": "Temperature for Design",
            "type": "output_group",
            "fields": [
                {
                    "id": "temp_rise",
                    "label": "Rise (°C)",
                    "type": "line",
                    "read_only": True,
                    "bind": "temp_rise_input",
                },
                {
                    "id": "temp_fall",
                    "label": "Fall (°C)",
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
            "label": "Load Case",
            "type": "combo",
            "bind": "custom_load_case_combo",
        },
        "custom_load_case_name": {
            "id": "custom_load_case_name",
            "label": "",  # Hidden label, uses spacer
            "type": "line",
            "placeholder": "Custom",
            "bind": "custom_load_case_name_input",
            "enabled": False,
        },
        "load_type": {
            "id": "custom_load_type",
            "label": "Load Type",
            "type": "combo",
            "bind": "custom_load_type_combo",
        },
        "point_left": {
            "id": "custom_point_left",
            "label": "Distance from Left Edge of Bridge (m)",
            "type": "line",
            "bind": "custom_point_left_input",
            "validator": {"type": "double_range", "bottom": 0.0, "top": 1000.0, "decimals": 3},
        },
        "point_bearing": {
            "id": "custom_point_bearing",
            "label": "Distance from Center Line of Bearing (m)",
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
    "sections": [
        {
            "id": "irc_load_combos_section",
            "title": "Load Combinations from IRC 6",
            "type": "dynamic_checkbox_list",
            "bind": "irc_load_combos_checkboxes",
            "default_checked": False,
        },
        {
            "id": "custom_load_combo_section",
            "title": "Custom Load Combination",
            "type": "custom_load_combo_table",
            "bind": "custom_load_combo_table",
            "add_button_bind": "load_combo_add_btn",
        },
    ],
}

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
    ],
}

DESIGN_OPTIONS_SCHEMA = {
    "id": "design_options",
    "cards": [

        # ---------------- Construction ----------------
        {
            "title": "Construction Stages",
            "field_width": 150,
            "sections": [
                {
                    "fields": [
                        {
                            "id": "construction_stage",
                            "label": "Include automatic",
                            "type": "combo",
                            "choices": ["Yes", "No"],
                            "default": "Yes",
                            "bind": "construction_stage_combo",
                        }
                    ]
                }
            ],
        },

        # ---------------- Deck Design ----------------
        {
            "title": "Deck Design",
            "field_width": 150,
            "sections": [
                {
                    "fields": [
                        {
                            "id": "reinforcement_size",
                            "label": "Reinforcement Size",
                            "type": "combo",
                            "choices": [ "4 mm", "5 mm", "6 mm", "8 mm","10 mm","12 mm", "16 mm","20 mm","25 mm","28 mm","32 mm","36 mm","40 mm"],
                            "default": "12 mm",
                            "bind": "reinforcement_size_combo",
                            
                        },
                        {
                            "id": "reinforcement_material",
                            "label": "Reinforcement Material",
                            "type": "combo",
                            "choices": [
                                "Fe 415",
                                "Fe 415D",
                                "Fe 500",
                                "Fe 500D",
                                "Fe 550",
                                "Fe 550D",
                                "Fe 600"
                            ],
                            "default": "Fe 500",
                            "bind": "reinforcement_material_combo",
                        },
                        {
                            
                            "id": "top_clear_cover",
                            "bind": "top_clear_cover_input",
                            "label": "Top Clear Cover (mm)",
                            "type": "number",
                            "default": 50.00,
                            "validator": {
                                "type": "double_range",
                                "bottom": 40.00,
                                "top": 75.0,
                                "decimals": 1,
                            },
                            "bind": "top_clear_cover_input",
                        },

                        {
                            "id": "bottom_clear_cover",
                            "label": "Bottom Clear Cover (mm)",
                            "type": "number",
                            "default": 40.00,
                            "validator": {
                                "type": "double_range",
                                "bottom": 35.0,
                                "top": 75.0,
                                "decimals": 1,
                            },
                            "bind": "bottom_clear_cover_input",
                        },

                        {
                            "id": "side_clear_cover",
                            "label": "Side Clear Cover (mm)",
                            "type": "number",
                            "default": 40.0,
                            "validator": {
                                "type": "double_range",
                                "bottom": 35.0,
                                "top": 75.0,
                                "decimals": 1,
                            },
                            "bind": "side_clear_cover_input",
                        },
                    ],
                }
            ],
        },

        # ---------------- Shear Studs ----------------
        {
            "title": "Shear Studs",
            "field_width": 150,
            "sections": [
                {
                    "fields": [
                        {
                            "id": "shear_stud_yield_strength",
                            "label": "Yield Strength (MPa)",
                            "type": "line",
                            "default": "385.00",
                            "validator": {
                                "type": "double_range",
                                "bottom": 350,
                                "top": 600,
                                "decimals": 2,
                            },
                            "bind": "shear_stud_yield_strength_input",
                        },
                        {
                            "id": "shear_stud_ultimate_strength",
                            "label": "Ultimate Strength (MPa)",
                            "type": "line",
                            "default": "495.00",
                            "validator": {
                                "type": "double_range",
                                "bottom": 350,
                                "top": 600,
                                "decimals": 2,
                            },
                            "bind": "shear_stud_ultimate_strength_input",
                        },
                        {
                            "id": "shear_stud_diameter",
                            "label": "Diameter (mm)",
                            "type": "combo",
                            "choices": ["12", "16", "20", "22", "25"],
                            "default": "20",
                            "bind": "shear_stud_diameter_combo",
                        },
                        {
                            "id": "shear_stud_height",
                            "label": "Height (mm)",
                            "type": "line",
                            "default": "100.00",
                            "validator": {
                                "type": "double_range",
                                "bottom": 0.0,
                                "top": 500.0,
                                "decimals": 2,
                            },
                            "bind": "shear_stud_height_input",
                        },
                        {
                            "id": "shear_stud_count",
                            "label": "No. of Shear Studs per Section",
                            "type": "combo",
                            "choices": [str(i) for i in range(1, 11)],
                            "default": "2",
                            "bind": "shear_stud_count_combo",
                        },
                        {
                            "id": "shear_stud_transverse_spacing",
                            "label": "Transverse Spacing (mm)",
                            "type": "line",
                            "default": "100.00",
                            "validator": {
                                "type": "double_range",
                                "bottom": 0.0,
                                "top": 5000.0,
                                "decimals": 2,
                            },
                            "bind": "shear_stud_spacing_input",
                        },
                    ],
                }
            ],
        },
    ],
}

DESIGN_OPTIONS_CONT_SCHEMA = {
    "id": "design_options_cont",
    "sections": [

        # ---------------- Partial Factor ----------------
        {
            "title": "Partial Factor",
            "fields": [

                {
                    "id": "gamma_c_basic",
                    "label": "Concrete basic & seismic, &#947;<sub>c</sub>",
                    "type": "line",
                    "default": "1.50",
                    "bind": "gamma_c_basic_input",
                    "validator": {
                        "type": "double_range",
                        "bottom": 1.0,
                        "top": 2.0,
                        "decimals": 2,
                    },
                },

                {
                    "id": "gamma_c_accidental",
                    "label": "Concrete Accidental, &#947;<sub>c</sub>",
                    "type": "line",
                    "default": "1.20",
                    "bind": "gamma_c_accidental_input",
                    "validator": {
                        "type": "double_range",
                        "bottom": 1.0,
                        "top": 2.0,
                        "decimals": 2,
                    },
                },

                {
                    "id": "gamma_m0",
                    "label": "Structural steel for Yielding and Buckling, &#947;<sub>M0</sub>",
                    "type": "line",
                    "default": "1.10",
                    "bind": "gamma_m0_input",
                    "validator": {
                        "type": "double_range",
                        "bottom": 1.0,
                        "top": 2.0,
                        "decimals": 2,
                    },
                },

                {
                    "id": "gamma_m1",
                    "label": "Structural Steel For Ultimate Stress, &#947;<sub>M1</sub>",
                    "type": "line",
                    "default": "1.25",
                    "bind": "gamma_m1_input",
                    "validator": {
                        "type": "double_range",
                        "bottom": 1.0,
                        "top": 2.0,
                        "decimals": 2,
                    },
                },

                {
                    "id": "gamma_s",
                    "label": "Reinforcing Steel, &#947;<sub>s</sub>",
                    "type": "line",
                    "default": "1.15",
                    "bind": "gamma_s_input",
                    "validator": {
                        "type": "double_range",
                        "bottom": 1.0,
                        "top": 2.0,
                        "decimals": 2,
                    },
                },

                {
                    "id": "gamma_v",
                    "label": "Shear Connectors For Yield, &#947;<sub>v</sub>",
                    "type": "line",
                    "default": "1.25",
                    "bind": "gamma_v_input",
                    "validator": {
                        "type": "double_range",
                        "bottom": 1.0,
                        "top": 2.0,
                        "decimals": 2,
                    },
                },

                {
                    "id": "gamma_flt",
                    "label": "Fatigue Load, &#947;<sub>flt</sub>",
                    "type": "line",
                    "default": "1.00",
                    "bind": "gamma_flt_input",
                    "validator": {
                        "type": "double_range",
                        "bottom": 1.0,
                        "top": 2.0,
                        "decimals": 2,
                    },
                },

                {
                    "id": "gamma_mf",
                    "label": "Fatigue Strength, &#947;<sub>Mf,t</sub>",
                    "type": "line",
                    "default": "1.35",
                    "bind": "gamma_mf_input",
                    "validator": {
                        "type": "double_range",
                        "bottom": 1.0,
                        "top": 2.0,
                        "decimals": 2,
                    },
                },
            ]
        },

        # ---------------- Resistance to Fatigue ----------------
        {
            "title": "Resistance to Fatigue",
            "fields": [
                {"id": "load_cycles", "label": "Number of Load Cycles", "type": "line", "default": "2000000.00", "bind": "load_cycles_input",
                 "validator": {
                        "type": "double_range",
                        "bottom": 100000,
                        "top": 100000000,
                        "decimals": 2,
                    },
                },
            ],
        },

        # ---------------- Deflection Control ----------------
        {
            "title": "Deflection Control",
            "fields": [
                {
                    "row_fields": [
                        {"label": "Limit :", "type": "label","after_spacing": 408},
                        {"label": "L /", "type": "label"},
                        {"id": "limit_l", "label": "", "type": "line", "default": "600.00", "bind": "limit_input", "width": 150,
                        "validator": {
                            "type": "int_range",
                            "bottom": 300,
                            "top": 800,
                            }
                        },
                        {"label": "m", "type": "label"},
                    ]
                },
            ],
        },

        # ---------------- Limit States ----------------
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
                    "default_checked": True,
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
                    "default_checked": True,
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
            "default_mode": "Optimized",
            "bind_mode": "depth_mode_combo",
            "bind_value": "depth_input",
            "visible_for": ["welded"],
        },
        {
            "id": "top_flange_width",
            "label": "Top Flange Width (mm):",
            "type": "mode_line",
            "mode_choices": ["Optimized", "Customized"],
            "default_mode": "Optimized",
            "bind_mode": "top_width_mode_combo",
            "bind_value": "top_width_input",
            "visible_for": ["welded"],
        },
        {
            "id": "top_flange_thickness",
            "label": "Top Flange Thickness (mm):",
            "type": "mode_line",
            "mode_choices": VALUES_PROFILE_SCOPE,
            "default_mode": "All",
            "bind_mode": "top_thickness_mode_combo",
            "bind_value": "top_thickness_input",
            "visible_for": ["welded"],
        },
        {
            "id": "bottom_flange_width",
            "label": "Bottom Flange Width (mm):",
            "type": "mode_line",
            "mode_choices": ["Optimized", "Customized"],
            "default_mode": "Optimized",
            "bind_mode": "bottom_width_mode_combo",
            "bind_value": "bottom_width_input",
            "visible_for": ["welded"],
        },
        {
            "id": "bottom_flange_thickness",
            "label": "Bottom Flange Thickness (mm):",
            "type": "mode_line",
            "mode_choices": VALUES_PROFILE_SCOPE,
            "default_mode": "All",
            "bind_mode": "bottom_thickness_mode_combo",
            "bind_value": "bottom_thickness_input",
            "visible_for": ["welded"],
        },
        {
            "id": "web_thickness",
            "label": "Web Thickness (mm):",
            "type": "mode_line",
            "mode_choices": VALUES_PROFILE_SCOPE,
            "default_mode": "All",
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
