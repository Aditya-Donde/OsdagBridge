"""Consolidated UI schemas for plate girder Additional Inputs dialogs.

This module groups all schema dictionaries used by the Additional Inputs
flow, including Typical Section Details, Support/Design options, and
Member Properties.
"""

from osdagbridge.core.utils.common import (
    DEFAULT_CRASH_BARRIER_WIDTH,
    DEFAULT_RAILING_WIDTH,
    KEY_INCLUDE_MEDIAN,
    SAIL_APPROVED_THICKNESS_VALUES,
    VALUES_BEARING_STIFFENER_COUNT,
    VALUES_END_DIAPHRAGM_TYPE,
    VALUES_GIRDER_DESIGN_MODE,
    VALUES_GIRDER_SPAN_MODE,
    VALUES_GIRDER_SUPPORT_TYPE,
    VALUES_GIRDER_SYMMETRY,
    VALUES_GIRDER_TYPE,
    VALUES_LONGITUDINAL_STIFFENER,
    VALUES_PROFILE_SCOPE,
    VALUES_STIFFENER_DESIGN,
    VALUES_TORSIONAL_RESTRAINT,
    VALUES_WARPING_RESTRAINT,
    VALUES_WEB_TYPE,
    VALUES_RAILING_TYPE,
    VALUES_WEARING_COAT_MATERIAL,
    VALUES_NO_YES,
    STIFFENER_DETAILS_DEFAULTS,
    TYPE_COMBOBOX,
    TYPE_TEXTBOX,
    KEY_CB_TYPE,
    KEY_CB_DENSITY,
    KEY_CB_WIDTH,
    KEY_CB_HEIGHT,
    KEY_CB_AREA,
    KEY_CB_LOAD,
    KEY_CB_POST_SPACING,
    KEY_CB_TAB,
    KEY_MD_TYPE,
    KEY_MD_DENSITY,
    KEY_MD_WIDTH,
    KEY_MD_HEIGHT,
    KEY_MD_AREA,
    KEY_MD_LOAD,
    KEY_MD_POST_SPACING,
    KEY_MD_TAB,
    KEY_RL_TYPE,
    KEY_RL_WIDTH,
    KEY_RL_HEIGHT,
    KEY_RL_LOAD_MODE,
    KEY_RL_LOAD_VALUE,
    KEY_RL_TAB,
    KEY_WC_MATERIAL,
    KEY_WC_DENSITY,
    KEY_WC_THICKNESS,
    KEY_WC_TAB,
    KEY_WC_LD_TAB,
    KEY_WC_LD_LANE_TABLE,
    KEY_WC_LD_LANE_TABLE_COUNT,
    KEY_TS_TAB,
    KEY_TS_DECK_TAB,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_DECK_OVERHANG,
    KEY_TS_OVERALL_WIDTH,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_TS_FOOTPATH_THICKNESS,
    KEY_FOOTPATH,
    VALUES_FOOTPATH,
)

_DECK_DETAILS_TAB_SCHEMA = {
    "id": KEY_TS_DECK_TAB,
    "label": "Deck Details",
    "label_width": 200,
    "rows": [
        {
            "fields": [
                {
                    "id": KEY_TS_DECK_THICKNESS,
                    "label": "Deck Thickness (mm):",
                    "type": TYPE_TEXTBOX,
                    "bind": "deck_thickness",
                    "on_editing_finished": "validate_deck_thickness",
                },
            ]
        },
        {
            "fields": [
                {
                    "id": KEY_TS_FOOTPATH_WIDTH,
                    "label": "Footpath Width (m):",
                    "type": TYPE_TEXTBOX,
                    "bind": "footpath_width",
                    "on_text_changed": "on_footpath_width_changed",
                },
                {
                    "id": KEY_TS_FOOTPATH_THICKNESS,
                    "label": "Footpath Thickness (mm):",
                    "type": TYPE_TEXTBOX,
                    "bind": "footpath_thickness",
                    "on_editing_finished": "validate_footpath_thickness",
                },
            ]
        },
    ],
}

_CRASH_BARRIER_TAB_SCHEMA = {
    "id": KEY_CB_TAB,
    "label": "Crash Barrier",
    "label_width": 210,
    "rows": [
        {
            "fields": [
                {
                    "id": KEY_CB_TYPE,
                    "label": "Type:",
                    "type": TYPE_COMBOBOX,
                    "choices": [
                        "IRC 5 - RCC Crash Barrier",
                        "IRC 5 - High Containment RCC Crash Barrier",
                        "IRC 5 - Metallic Crash Barrier with Single W-Beam",
                        "IRC 5 - Metallic Crash Barrier with Double W-Beam",
                        "Custom",
                    ],
                    "on_change": "on_crash_barrier_type_changed",
                }
            ]
        },
        {
            "fields": [
                {
                    "id": KEY_CB_DENSITY,
                    "label": "Material Density (kN/m³):",
                    "type": TYPE_TEXTBOX,
                    "on_editing_finished": "_auto_compute_crash_barrier_load",
                }
            ]
        },
        {
            "fields": [
                {
                    "id": KEY_CB_WIDTH,
                    "label": "Width (m):",
                    "type": TYPE_TEXTBOX,
                    "default": DEFAULT_CRASH_BARRIER_WIDTH,
                    "on_text_changed": "recalculate_girders",
                }
            ]
        },
        {
            "fields": [
                {
                    "id": KEY_CB_HEIGHT,
                    "label": "Height (m):",
                    "type": TYPE_TEXTBOX,
                }
            ]
        },
        {
            "fields": [
                {
                    "id": KEY_CB_AREA,
                    "label": "Area (m²):",
                    "type": TYPE_TEXTBOX,
                    "on_editing_finished": "_auto_compute_crash_barrier_load",
                }
            ]
        },
        {
            "fields": [
                {
                    "id": KEY_CB_LOAD,
                    "label": "Load (kN/m):",
                    "type": TYPE_TEXTBOX,
                }
            ]
        },
        {
            "fields": [
                {
                    "id": KEY_CB_POST_SPACING,
                    "label": "Spacing between Posts (m):",
                    "type": TYPE_TEXTBOX,
                    "default": "1",
                }
            ]
        },
    ],
}

_MEDIAN_TAB_SCHEMA = {
    "id": KEY_MD_TAB,
    "label": "Median",
    "label_width": 210,
    "active": 
        {
            "id": KEY_INCLUDE_MEDIAN, # key to check in working_input_dict
            "values":                 # tab enabled when current value is IN this list
            [
                VALUES_NO_YES[1]
            ],
        },
    "rows": [
        {
            "fields": [
                {
                    "id": KEY_MD_TYPE,
                    "label": "Type:",
                    "type": TYPE_COMBOBOX,
                    "choices": [
                        "IRC 5 - Raised Kerb",
                        "IRC 5 - RCC Crash Barrier",
                        "IRC 5 - Metallic Crash Barrier with Single W-Beam",
                        "IRC 5 - Metallic Crash Barrier with Double W-Beam",
                        "Custom",
                    ],
                    "on_change": "on_median_type_changed",
                }
            ]
        },
        {
            "fields": [
                {
                    "id": KEY_MD_DENSITY,
                    "label": "Material Density (kN/m³):",
                    "type": TYPE_TEXTBOX,
                }
            ]
        },
        {
            "fields": [
                {
                    "id": KEY_MD_WIDTH,
                    "label": "Width (m):",
                    "type": TYPE_TEXTBOX,
                }
            ]
        },
        {
            "fields": [
                {
                    "id": KEY_MD_HEIGHT,
                    "label": "Height (m):",
                    "type": TYPE_TEXTBOX,
                }
            ]
        },
        {
            "fields": [
                {
                    "id": KEY_MD_AREA,
                    "label": "Area (m²):",
                    "type": TYPE_TEXTBOX,
                }
            ]
        },
        {
            "fields": [
                {
                    "id": KEY_MD_LOAD,
                    "label": "Load (kN/m):",
                    "type": TYPE_TEXTBOX,
                }
            ]
        },
        {
            "fields": [
                {
                    "id": KEY_MD_POST_SPACING,
                    "label": "Spacing between Posts (m):",
                    "type": TYPE_TEXTBOX,
                    "default": "1",
                }
            ]
        },
    ],
}

_RAILING_TAB_SCHEMA = {
    "id": KEY_RL_TAB,
    "label": "Railing",
    "label_width": 180,
    "active": 
        {
            "id": KEY_FOOTPATH,
            "values": 
            [
                VALUES_FOOTPATH[1],
                VALUES_FOOTPATH[2],
            ],
        },
    "rows": [
        {
            "fields": [
                {
                    "id": KEY_RL_TYPE,
                    "label": "Type:",
                    "type": TYPE_COMBOBOX,
                    "choices": VALUES_RAILING_TYPE,
                    "on_change": "on_railing_type_changed",
                }
            ]
        },
        {
            "fields": [
                {
                    "id": KEY_RL_WIDTH,
                    "label": "Width (mm):",
                    "type": TYPE_TEXTBOX,
                    "default": f"{DEFAULT_RAILING_WIDTH * 1000:.0f}",
                    "on_text_changed": "recalculate_girders",
                }
            ]
        },
        {
            "fields": [
                {
                    "id": KEY_RL_HEIGHT,
                    "label": "Height (m):",
                    "type": TYPE_TEXTBOX,
                    "on_editing_finished": "validate_railing_height",
                }
            ]
        },
        {
            "fields": [
                {
                    "id": KEY_RL_LOAD_MODE,
                    "label": "Load Mode:",
                    "type": TYPE_COMBOBOX,
                    "choices": ["Automatic (IRC 6)", "User-defined"],
                    "on_change": "on_railing_load_mode_changed",
                },
                {
                    "id": KEY_RL_LOAD_VALUE,
                    "label": "Load (kN/m):",
                    "type": TYPE_TEXTBOX,
                    "placeholder": "Value",
                    "enabled": False,
                },
            ]
        },
    ],
}

_WEARING_COURSE_TAB_SCHEMA = {
    "id": KEY_WC_TAB,
    "label": "Wearing Course",
    "label_width": 200,
    "rows": [
        {
            "fields": [
                {
                    "id": KEY_WC_MATERIAL,
                    "label": "Material:",
                    "type": TYPE_COMBOBOX,
                    "choices": VALUES_WEARING_COAT_MATERIAL,
                    "on_change": "on_wearing_material_changed",
                }
            ]
        },
        {
            "fields": [
                {
                    "id": KEY_WC_DENSITY,
                    "label": "Density (kN/m³):",
                    "type": TYPE_TEXTBOX,
                    "default": "24.0",
                }
            ]
        },
        {
            "fields": [
                {
                    "id": KEY_WC_THICKNESS,
                    "label": "Thickness (mm):",
                    "type": TYPE_TEXTBOX,
                    "default": "50",
                }
            ]
        },
    ],
}

_LANE_DETAILS_TAB_SCHEMA = {
    "id": KEY_WC_LD_TAB,
    "label": "Lane Details",
    "rows": [
        {
            "fields": [
                {
                    "id": KEY_WC_LD_LANE_TABLE,
                    "label": "No. of Traffic Lanes:",
                    "type": "table_with_count",
                    "count_id": KEY_WC_LD_LANE_TABLE_COUNT,
                    "count_choices": [str(i) for i in range(1, 7)],
                    "on_count_change": "on_lane_count_changed",
                    "columns": [
                        {"header": "Traffic Lane Number",                                                "resize": "contents"},
                        {"header": "Distance from inner edge of crash barrier to left edge of lane (m)", "resize": "stretch"},
                        {"header": "Lane Width (m)",                                                     "resize": "contents"},
                    ],
                    "alternating_rows": True,
                    "show_vertical_header": False,
                }
            ]
        },
    ],
}

TYPICAL_SECTION_SCHEMA = {
    "id": KEY_TS_TAB,

    # ── Rendered ABOVE the subtab bar ─────────────────────────────────────────
    # Two rows of two fields each, in a 2-column grid.
    "primary_fields": {
        "label_width": 200,
        "rows": [
            {
                "fields": [
                    {
                        "id": KEY_TS_GIRDER_SPACING,
                        "label": "Girder Spacing (m):",
                        "type": TYPE_TEXTBOX,
                        "bind": "girder_spacing",
                        "on_text_changed": "on_girder_spacing_changed",
                    },
                    {
                        "id": KEY_TS_NO_OF_GIRDERS,
                        "label": "No. of Girders:",
                        "type": TYPE_TEXTBOX,
                        "bind": "no_of_girders",
                        "on_editing_finished": "on_no_of_girders_changed",
                    },
                ]
            },
            {
                "fields": [
                    {
                        "id": KEY_TS_DECK_OVERHANG,
                        "label": "Deck Overhang Width (m):",
                        "type": TYPE_TEXTBOX,
                        "bind": "deck_overhang",
                        "on_text_changed": "on_deck_overhang_changed",
                    },
                    {
                        "id": KEY_TS_OVERALL_WIDTH,
                        "label": "Overall Bridge Width (m):",
                        "type": TYPE_TEXTBOX,
                        "read_only": True,
                        "bind": "overall_bridge_width_display",
                        "on_text_changed": "_reject_overall_width_override",
                    },
                ]
            },
        ],
    },

    # ── Subtabs ────────────────────────────────────────────────────────────────
    "tabs": [
        _DECK_DETAILS_TAB_SCHEMA,
        _CRASH_BARRIER_TAB_SCHEMA,
        _MEDIAN_TAB_SCHEMA,
        _RAILING_TAB_SCHEMA,
        _WEARING_COURSE_TAB_SCHEMA,
        _LANE_DETAILS_TAB_SCHEMA,
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
                            "id": "reinforcement_bounds",
                            "label": "Reinforcement Size",
                            "type": "button",
                            "text": "Set Bounds",
                            "bind": "reinforcement_bounds_btn"
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
    "id": "girder_details_tab",
    "defaults": {
        "member_length_m": 30.0,
        "distance_start_m": 0.0,
        "max_girder_count": 20,
    },
    "SAIL_APPROVED_THICKNESS_VALUES": SAIL_APPROVED_THICKNESS_VALUES,
    "thickness_values_mm": SAIL_APPROVED_THICKNESS_VALUES,
    "overview": [
        {
            "id": "select_girder",
            "label": "Select Girder:",
            "type": "combo_dynamic",
            "bind": "girder_dropdown",
            "include_all": True,
        },
        {
            "id": "span",
            "label": "Span:",
            "type": "combo",
            "choices": VALUES_GIRDER_SPAN_MODE,
            "bind": "span_combo",
        },
        {
            "id": "total_span",
            "label": "Total Span (m):",
            "type": "line",
            "default": "30",
            "read_only": True,
            "bind": "length_input",
        },
    ],
    "segment_manager": {
        "table_headers": ["Member ID", "Start (m)", "End (m)", "Length (m)", "Action"],
        "action_column_width": 132,
    },
    "cad_view": {
        "buttons": [
            {"id": "cross_section", "label": "Cross Section", "mode": "cross", "width": 130, "height": 32},
            {"id": "side_view", "label": "Side View", "mode": "side", "width": 130, "height": 32},
        ]
    },
    "section_inputs": [
        {
            "id": "design",
            "label": "Design:",
            "type": "combo",
            "choices": VALUES_GIRDER_DESIGN_MODE,
            "bind": "design_combo",
            "legacy_payload_key": "design_mode",
            "visible_for": ["welded"],
        },
        {
            "id": "type",
            "label": "Type:",
            "type": "combo",
            "choices": VALUES_GIRDER_TYPE,
            "bind": "type_combo",
            "legacy_payload_key": "girder_type",
        },
        {
            "id": "symmetry",
            "label": "Symmetry:",
            "type": "combo",
            "choices": VALUES_GIRDER_SYMMETRY,
            "bind": "symmetry_combo",
            "row_bucket": "symmetry_row",
            "legacy_payload_key": "symmetry",
            "visible_for": ["welded"],
        },
        {
            "id": "depth",
            "label": "Total Depth, d (mm):",
            "type": "line_with_bounds",
            "bounds_key": "total_depth",
            "bounds_default": {"lower": 200.0, "upper": 2000.0, "increment": 25.0},
            "bind": "total_depth_input",
            "bind_widget": "total_depth_widget",
            "bind_bounds_button": "total_depth_bounds_button",
            "legacy_welded_key": "total_depth_mm",
            "legacy_welded_bounds_key": "total_depth_bounds",
            "visible_for": ["welded"],
        },
        {
            "id": "top_flange_width",
            "label": "Width of Top Flange, t<sub>fw</sub> (mm):",
            "type": "line_with_bounds",
            "bounds_key": "top_width",
            "bounds_default": {"lower": 100.0, "upper": 1000.0, "increment": 10.0},
            "bind": "top_width_input",
            "bind_widget": "top_width_widget",
            "bind_bounds_button": "top_width_bounds_button",
            "legacy_welded_key": "top_flange_width_mm",
            "legacy_welded_bounds_key": "top_flange_width_bounds",
            "visible_for": ["welded"],
        },
        {
            "id": "top_flange_thickness",
            "label": "Top Flange Thickness, t<sub>ft</sub> (mm):",
            "type": "mode_line",
            "mode_choices": VALUES_PROFILE_SCOPE,
            "default_mode": "All",
            "bind_mode": "top_thickness_combo",
            "bind_value": "top_thickness_value_input",
            "bind_wrapper": "top_thickness_widget",
            "thickness_key": "top_thickness",
            "legacy_welded_mode_key": "top_thickness_mode",
            "legacy_welded_value_key": "top_thickness_value_mm",
            "visible_for": ["welded"],
        },
        {
            "id": "bottom_flange_width",
            "label": "Width of Bottom Flange, b<sub>fw</sub> (mm):",
            "type": "line_with_bounds",
            "bounds_key": "bottom_width",
            "bounds_default": {"lower": 100.0, "upper": 1000.0, "increment": 10.0},
            "bind": "bottom_width_input",
            "bind_widget": "bottom_width_widget",
            "bind_bounds_button": "bottom_width_bounds_button",
            "legacy_welded_key": "bottom_flange_width_mm",
            "legacy_welded_bounds_key": "bottom_flange_width_bounds",
            "visible_for": ["welded"],
        },
        {
            "id": "bottom_flange_thickness",
            "label": "Bottom Flange Thickness, b<sub>ft</sub> (mm):",
            "type": "mode_line",
            "mode_choices": VALUES_PROFILE_SCOPE,
            "default_mode": "All",
            "bind_mode": "bottom_thickness_combo",
            "bind_value": "bottom_thickness_value_input",
            "bind_wrapper": "bottom_thickness_widget",
            "thickness_key": "bottom_thickness",
            "legacy_welded_mode_key": "bottom_thickness_mode",
            "legacy_welded_value_key": "bottom_thickness_value_mm",
            "visible_for": ["welded"],
        },
        {
            "id": "support_type",
            "label": "Support Type:",
            "type": "combo",
            "choices": VALUES_GIRDER_SUPPORT_TYPE,
            "bind": "support_type_combo",
            "visible_for": ["welded"],
        },
        {
            "id": "support_width",
            "label": "Support Width (mm):",
            "type": "line",
            "validator": {"type": "double_range", "bottom": 0.0, "top": 1000000.0, "decimals": 3},
            "bind": "support_width_input",
            "legacy_welded_key": "support_width_mm",
            "visible_for": ["welded"],
        },
        {
            "id": "web_thickness",
            "label": "Web Thickness, w<sub>t</sub> (mm):",
            "type": "mode_line",
            "mode_choices": VALUES_PROFILE_SCOPE,
            "default_mode": "All",
            "bind_mode": "web_thickness_combo",
            "bind_value": "web_thickness_value_input",
            "bind_wrapper": "web_thickness_widget",
            "thickness_key": "web_thickness",
            "legacy_welded_mode_key": "web_thickness_mode",
            "legacy_welded_value_key": "web_thickness_value_mm",
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
            "legacy_payload_key": "rolled_section",
            "visible_for": ["rolled"],
        },
        {
            "id": "torsional_restraint",
            "label": "Torsional Restraint:",
            "type": "combo",
            "choices": VALUES_TORSIONAL_RESTRAINT,
            "bind": "torsion_combo",
            "aliases": ["torsion"],
            "legacy_payload_key": "torsional_restraint",
        },
        {
            "id": "warping_restraint",
            "label": "Warping Restraint:",
            "type": "combo",
            "choices": VALUES_WARPING_RESTRAINT,
            "bind": "warping_combo",
            "aliases": ["warping"],
            "legacy_payload_key": "warping_restraint",
        },
        {
            "id": "web_type",
            "label": "Web Type:",
            "type": "combo",
            "choices": VALUES_WEB_TYPE,
            "bind": "web_type_combo",
            "row_bucket": "web_type_row",
            "legacy_payload_key": "web_type",
            "visible_for": ["welded"],
        },
    ],
}

STIFFENER_DETAILS_SCHEMA = {
    "id": "stiffener_details_tab",
    "overview": [
        {
            "id": "member_id",
            "label": "Select Member ID:",
            "type": "combo_dynamic",
            "bind": "girder_member_combo",
        },
    ],
    "stiffener_inputs": [
        {
            "id": "bearing_stiffeners_each_end",
            "label": "No. of Bearing Stiffeners\n(on one side only):",
            "type": "combo",
            "choices": VALUES_BEARING_STIFFENER_COUNT,
            "default": str(STIFFENER_DETAILS_DEFAULTS.get("bearing_stiffeners_each_end", "2")),
            "bind": "bearing_count_combo",
        },
        {
            "id": "bearing_spacing_mm",
            "label": "Bearing Stiffener Spacing (mm):",
            "type": "line",
            "validator": {"type": "int_range", "bottom": 1, "top": 1000000000},
            "bind": "bearing_spacing_input",
        },
        {
            "id": "bearing_thickness",
            "label": "Bearing Stiffener Thickness (mm):",
            "type": "mode_value",
            "mode_choices": VALUES_PROFILE_SCOPE,
            "default_mode": VALUES_PROFILE_SCOPE[0],
            "bind_mode": "bearing_thick_combo",
            "bind_value": "bearing_thick_value_combo",
        },
        {
            "id": "bearing_outstand_mm",
            "label": "Outstand of Bearing Stiffener (mm):",
            "type": "line",
            "bind": "bearing_outstand_input",
        },
        {
            "id": "intermediate_stiffener",
            "label": "Intermediate Stiffener:",
            "type": "combo",
            "choices": VALUES_NO_YES,
            "bind": "intermediate_combo",
        },
        {
            "id": "intermediate_spacing_mm",
            "label": "Intermediate Stiffener Spacing:",
            "type": "line",
            "validator": {"type": "int_range", "bottom": 1, "top": 1000000000},
            "default": "NA",
            "bind": "intermediate_spacing_input",
        },
        {
            "id": "intermediate_thickness",
            "label": "Intermediate Stiffener Thickness (mm):",
            "type": "mode_value",
            "mode_choices": VALUES_PROFILE_SCOPE,
            "default_mode": VALUES_PROFILE_SCOPE[0],
            "bind_mode": "intermediate_thick_combo",
            "bind_value": "intermediate_thick_value_combo",
        },
        {
            "id": "intermediate_outstand_mm",
            "label": "Outstand of Intermediate Stiffener (mm):",
            "type": "line",
            "bind": "intermediate_outstand_input",
        },
        {
            "id": "longitudinal_stiffener",
            "label": "Longitudinal Stiffener:",
            "type": "combo",
            "choices": VALUES_LONGITUDINAL_STIFFENER,
            "bind": "longitudinal_combo",
        },
        {
            "id": "longitudinal_thickness",
            "label": "Longitudinal Stiffener Thickness (mm):",
            "type": "mode_value",
            "mode_choices": VALUES_PROFILE_SCOPE,
            "default_mode": VALUES_PROFILE_SCOPE[0],
            "bind_mode": "long_thick_combo",
            "bind_value": "long_thick_value_combo",
        },
    ],
    "web_buckling_inputs": [
        {
            "id": "shear_buckling_method",
            "label": "Shear Buckling Design Method:",
            "type": "combo",
            "choices": VALUES_STIFFENER_DESIGN,
            "bind": "method_combo",
        },
    ],
}

CROSS_BRACING_DETAILS_SCHEMA = {
    "id": "cross_bracing_details_tab",
    "overview": [
        {
            "id": "select_girders",
            "label": "Select Girders:",
            "type": "combo_dynamic",
            "bind": "select_girders_combo",
        },
        {
            "id": "member_id",
            "label": "Member ID:",
            "type": "line",
            "read_only": True,
            "bind": "member_id_display",
        },
    ],
    "section_inputs": [
        {
            "id": "design",
            "label": "Design:",
            "type": "combo",
            "choices": VALUES_GIRDER_DESIGN_MODE,
            "bind": "design_combo",
            "default": "Optimized",
        },
        {
            "id": "bracing_type",
            "label": "Type of Bracing:",
            "type": "combo",
            "choices": ["K-Bracing", "X-Bracing"],
            "bind": "bracing_type_combo",
        },
        {
            "id": "bracing_section_type",
            "label": "Bracing Section Type:",
            "type": "combo",
            "choices": [
                "Angle",
                "Double Angle (Long Leg)",
                "Double Angle (Short Leg)",
                "Channel",
                "Double Channel",
            ],
            "bind": "bracing_section_type_combo",
        },
        {
            "id": "bracing_section",
            "label": "Bracing Section Designation:",
            "type": "combo_dynamic",
            "bind": "bracing_section_combo",
        },
        {
            "id": "top_chord_enabled",
            "label": "Top Chord:",
            "type": "checkbox",
            "bind": "top_chord_checkbox",
            "default": False,
        },
        {
            "id": "top_chord_type",
            "label": "Top Chord Section Type:",
            "type": "combo",
            "choices": [
                "Angle",
                "Double Angle (Long Leg)",
                "Double Angle (Short Leg)",
                "Channel",
                "Double Channel",
            ],
            "bind": "top_chord_type_combo",
        },
        {
            "id": "top_chord_size",
            "label": "Top Chord Section Designation:",
            "type": "combo_dynamic",
            "bind": "top_chord_size_combo",
        },
        {
            "id": "bottom_chord_enabled",
            "label": "Bottom Chord:",
            "type": "checkbox",
            "bind": "bottom_chord_checkbox",
            "default": True,
        },
        {
            "id": "bottom_chord_type",
            "label": "Bottom Chord Section Type:",
            "type": "combo",
            "choices": [
                "Angle",
                "Double Angle (Long Leg)",
                "Double Angle (Short Leg)",
                "Channel",
                "Double Channel",
            ],
            "bind": "bottom_chord_type_combo",
        },
        {
            "id": "bottom_chord_size",
            "label": "Bottom Chord Section Designation:",
            "type": "combo_dynamic",
            "bind": "bottom_chord_size_combo",
        },
        {
            "id": "spacing",
            "label": "Spacing (m):",
            "type": "line",
            "default": "3",
            "validator": {"type": "double_range", "bottom": 0.01, "top": 100000.0, "decimals": 2},
            "bind": "spacing_input",
        },
    ],
}

END_DIAPHRAGM_DETAILS_SCHEMA = {
    "id": "end_diaphragm_details_tab",
    "views": {
        "Cross Bracing": {
            "overview": [
                {
                    "id": "type_selector",
                    "label": "Type:",
                    "type": "combo",
                    "choices": VALUES_END_DIAPHRAGM_TYPE,
                    "default": "Cross Bracing",
                },
            ],
            "section_inputs": [
                {
                    "id": "design",
                    "label": "Design:",
                    "type": "combo",
                    "choices": VALUES_GIRDER_DESIGN_MODE,
                    "default": "Optimized",
                    "bind": "cross_design_combo",
                },
                {
                    "id": "bracing_type",
                    "label": "Type of Bracing:",
                    "type": "combo",
                    "choices": ["K-Bracing", "X-Bracing"],
                    "bind": "cross_bracing_type_combo",
                },
                {
                    "id": "bracing_section_type",
                    "label": "Bracing Section Type:",
                    "type": "combo",
                    "choices": [
                        "Angle",
                        "Double Angle (Long Leg)",
                        "Double Angle (Short Leg)",
                        "Channel",
                        "Double Channel",
                    ],
                    "bind": "cross_bracing_section_type_combo",
                },
                {
                    "id": "bracing_section",
                    "label": "Bracing Section Designation:",
                    "type": "combo_dynamic",
                    "bind": "cross_bracing_section_combo",
                },
                {
                    "id": "top_chord_enabled",
                    "label": "Top Chord:",
                    "type": "checkbox",
                    "default": False,
                    "bind": "cross_top_chord_checkbox",
                },
                {
                    "id": "top_chord_type",
                    "label": "Top Chord Section Type:",
                    "type": "combo",
                    "choices": [
                        "Angle",
                        "Double Angle (Long Leg)",
                        "Double Angle (Short Leg)",
                        "Channel",
                        "Double Channel",
                    ],
                    "bind": "cross_top_chord_type_combo",
                },
                {
                    "id": "top_chord_size",
                    "label": "Top Chord Section Designation:",
                    "type": "combo_dynamic",
                    "bind": "cross_top_chord_size_combo",
                },
                {
                    "id": "bottom_chord_enabled",
                    "label": "Bottom Chord:",
                    "type": "checkbox",
                    "default": True,
                    "bind": "cross_bottom_chord_checkbox",
                },
                {
                    "id": "bottom_chord_type",
                    "label": "Bottom Chord Section Type:",
                    "type": "combo",
                    "choices": [
                        "Angle",
                        "Double Angle (Long Leg)",
                        "Double Angle (Short Leg)",
                        "Channel",
                        "Double Channel",
                    ],
                    "bind": "cross_bottom_chord_type_combo",
                },
                {
                    "id": "bottom_chord_size",
                    "label": "Bottom Chord Section Designation:",
                    "type": "combo_dynamic",
                    "bind": "cross_bottom_chord_size_combo",
                },
            ],
        },
        "Rolled Beam": {
            "overview": [
                {
                    "id": "type_selector",
                    "label": "Type:",
                    "type": "combo",
                    "choices": VALUES_END_DIAPHRAGM_TYPE,
                    "default": "Rolled Beam",
                },
            ],
            "section_inputs": [
                {
                    "id": "design",
                    "label": "Design:",
                    "type": "combo",
                    "choices": VALUES_GIRDER_DESIGN_MODE,
                    "default": "Optimized",
                    "bind": "rolled_design_combo",
                },
                {
                    "id": "is_section",
                    "label": "IS Section:",
                    "type": "combo_dynamic",
                    "bind": "rolled_is_section_combo",
                },
            ],
        },
        "Welded Beam": {
            "overview": [
                {
                    "id": "type_selector",
                    "label": "Type:",
                    "type": "combo",
                    "choices": VALUES_END_DIAPHRAGM_TYPE,
                    "default": "Welded Beam",
                },
            ],
            "section_inputs": [
                {
                    "id": "design",
                    "label": "Design:",
                    "type": "combo",
                    "choices": VALUES_GIRDER_DESIGN_MODE,
                    "default": "Optimized",
                    "bind": "welded_design_combo",
                },
                {
                    "id": "symmetry",
                    "label": "Symmetry:",
                    "type": "combo",
                    "choices": VALUES_GIRDER_SYMMETRY,
                    "bind": "welded_symmetry_combo",
                },
            ],
        },
    },
}

# Versioned contract for schema-driven Member Properties migration.
# This keeps existing schema constants intact while providing a single
# top-level structure that builders can consume incrementally.
MEMBER_PROPERTIES_SCHEMA_V1 = {
    "version": 1,
    "tabs": {
        "girder_details": {
            "id": "girder_details",
            "title": "Girder Details",
            "overview": GIRDER_DETAILS_SCHEMA.get("overview", []),
            "section_inputs": GIRDER_DETAILS_SCHEMA.get("section_inputs", []),
        },
        "stiffener_details": {
            "id": "stiffener_details",
            "title": "Stiffener Details",
            "overview": STIFFENER_DETAILS_SCHEMA.get("overview", []),
            "stiffener_inputs": STIFFENER_DETAILS_SCHEMA.get("stiffener_inputs", []),
            "web_buckling_inputs": STIFFENER_DETAILS_SCHEMA.get("web_buckling_inputs", []),
        },
        "cross_bracing_details": {
            "id": "cross_bracing_details",
            "title": "Cross-Bracing Details",
            "overview": CROSS_BRACING_DETAILS_SCHEMA.get("overview", []),
            "section_inputs": CROSS_BRACING_DETAILS_SCHEMA.get("section_inputs", []),
        },
        "end_diaphragm_details": {
            "id": "end_diaphragm_details",
            "title": "End Diaphragm Details",
            "views": END_DIAPHRAGM_DETAILS_SCHEMA.get("views", {}),
        },
    },
}

#function -> store in dict design dict