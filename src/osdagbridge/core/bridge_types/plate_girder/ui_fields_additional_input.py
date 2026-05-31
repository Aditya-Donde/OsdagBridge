"""Consolidated UI schemas for plate girder Additional Inputs dialogs.

This module groups all schema dictionaries used by the Additional Inputs
flow, including Typical Section Details, Support/Design options, and
Member Properties.
"""

from osdagbridge.core.utils.common import *

# ── Value Refresh Schema ──────────────────────────────────────────────────────
# These are mainly for populating the data in additional input that comes from Input Dictionary


# ── Typical Section Details Tab ───────────────────────────────────────────────

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
                    "choices": ["As per IRC 6", "User-defined"],
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
                    "type": TYPE_TABLE_WITH_COUNTER,
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
                        "id": KEY_TS_NO_OF_GIRDERS,
                        "label": "No. of Girders:",
                        "type": TYPE_TEXTBOX,
                        "bind": "no_of_girders",
                        "on_editing_finished": "on_no_of_girders_changed",
                    },
                    {
                        "id": KEY_TS_GIRDER_SPACING,
                        "label": "Girder Spacing (m):",
                        "type": TYPE_TEXTBOX,
                        "bind": "girder_spacing",
                        "on_editing_finished": "on_girder_spacing_changed",
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
                        "on_editing_finished": "on_deck_overhang_changed",
                    },
                    {
                        "id": KEY_TS_OVERALL_WIDTH,
                        "label": "Overall Bridge Width (m):",
                        "type": TYPE_TEXTBOX,
                        "read_only": True,
                        "bind": "overall_bridge_width_display",
                    },
                ],
            },
            {
                "fields": [
                    {},  # empty first field — placeholder for left column
                    {
                        "type": TYPE_NOTICE,
                        "id": "layout_notice",
                        "bind_adjust":    "layout_adjust_notice",
                        "bind_warning":   "layout_warning_notice",
                        "bind_container": "layout_notice_container",
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


# ── Loading Tab ───────────────────────────────────────────────────────────────

_COMPUTE_SEISMIC = {"function": "_compute_seismic_values"}

_PERMANENT_LOAD_TAB_SCHEMA = {
    "id":     KEY_PL_TAB,
    "layout": {
        "type":          "columns",
        "columns":       2,
        "column_widths": [3, 2],
    },
    "sections": [
        {
            "column": 0,
            "title":  "Dead Load (DL)",
            "rows": [
                {
                    "fields": [{
                        "id":          KEY_PL_SELF_WEIGHT_FACTOR,
                        "label":       "Self-weight modification factor",
                        "type":        TYPE_TEXTBOX,
                        "placeholder": "",
                        "bind":        "self_weight_factor_input",
                    }]
                },
            ],
        },
        {
            "column":  1,
            "type":    TYPE_DESCRIPTION,
            "title":   "Description Box",
            "text":    "",
            "stretch": True,
        },
    ],
}

_LIVE_LOAD_TAB_SCHEMA = {
    "id":     KEY_LL_TAB,
    "layout": {
        "type":          "columns",
        "columns":       2,
        "column_widths": [3, 2],
    },
    "sections": [

        # ── Column 0: IRC Vehicles ──────────────────────────────────────────
        {
            "column": 0,
            "title":  "Vehicles from IRC 6",
            "rows": [
                {
                    "fields": 
                        [{
                            "id": KEY_LL_IRC_CLASS_A,
                            "label": "Class A",
                            "type": TYPE_CHECKBOX,
                            "label_first": True
                        }]
                },
                {
                    "fields": 
                        [{
                            "id": KEY_LL_IRC_AA_WHEELED,    
                            "label": "Class AA Wheeled",  
                            "type": TYPE_CHECKBOX, 
                            "label_first": True
                        }]
                },
                {
                    "fields": 
                        [{
                            "id": KEY_LL_IRC_AA_TRACKED,    
                            "label": "Class AA Tracked",  
                            "type": TYPE_CHECKBOX, 
                            "label_first": True
                        }]
                },
                {
                    "fields": 
                        [{
                            "id": KEY_LL_IRC_70R_WHEELED,   
                            "label": "Class 70R Wheeled", 
                            "type": TYPE_CHECKBOX, 
                            "label_first": True
                        }]
                },
                {
                    "fields": 
                        [{
                            "id": KEY_LL_IRC_70R_TRACKED,   
                            "label": "Class 70R Tracked", 
                            "type": TYPE_CHECKBOX, 
                            "label_first": True
                        }]
                },
                {
                    "fields": 
                        [{
                            "id": KEY_LL_IRC_70R_BOGIE,     
                            "label": "Class 70R Bogie",   
                            "type": TYPE_CHECKBOX, 
                            "label_first": True
                        }]
                },
                {
                    "fields": 
                        [{
                            "id": KEY_LL_IRC_CLASS_SV,      
                            "label": "Class SV",          
                            "type": TYPE_CHECKBOX, 
                            "label_first": True
                        }]
                },
                {
                    "fields": 
                        [{
                            "id": KEY_LL_IRC_CLASS_FATIGUE, 
                            "label": "Class Fatigue",     
                            "type": TYPE_CHECKBOX, 
                            "label_first": True
                        }]
                },
            ],
        },

        # ── Column 0: Custom Vehicle ────────────────────────────────────────
        # {
        #     "column": 0,
        #     "title":  "Custom Vehicle",
        #     "rows": [
        #         {
        #             "fields": [{
        #                 "id":       KEY_LL_CUSTOM_VEHICLES,
        #                 "type":     TYPE_CUSTOM_VEHICLE,
        #                 "on_click": "_on_add_custom_vehicle",
        #             }]
        #         },
        #     ],
        # },

        # ── Column 0: Braking Load + Eccentricity ──────────────────────────────
        {
            "column": 0,
            "title":  "Braking Load from Vehicles",
            "rows": [
                {
                    "fields": [{
                        "id":              KEY_LL_IRC_CLASS_SV,
                        "label":           "Class SV",
                        "type":            TYPE_CHECKBOX,
                        "default_checked": True,
                        "label_first":     True,
                    }]
                },
                {
                    "fields": [{
                        "id":          KEY_LL_ECCENTRICITY,
                        "label":       "Eccentricity from top of Deck (m)",
                        "type":        TYPE_TEXTBOX,
                        "placeholder": "",
                        "bind":        "eccentricity_input",
                    }]
                },
            ],
        },

        # ── Column 0: Footpath Pressure ────────────────────────────────────────
        {
            "column": 0,
            "title":  "",
            "rows": [
                {
                    "fields": [{
                        "id":             KEY_LL_FOOTPATH_PRESSURE,
                        "label":          "Footpath Pressure (kN/mm²)",
                        "type":           TYPE_MODE_LINE,
                        "mode_choices":   ["As per IRC 6", "Custom"],
                        "bind_mode":      "footpath_mode_combo",
                        "bind_value":     "footpath_value_input",
                        "on_mode_change": "_on_footpath_mode_changed",
                    }]
                },
            ],
        },

        # ── Column 1: Description ───────────────────────────────────────────
        {
            "column":  1,
            "type":    TYPE_DESCRIPTION,
            "title":   "Description Box",
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
            "stretch": True,
        },
    ],
}

_SEISMIC_LOAD_TAB_SCHEMA = {
    "id":     KEY_SL_TAB,
    "layout": {
        "type":          "columns",
        "columns":       2,
        "column_widths": [3, 2],
    },
    "sections": [

        # ── Column 0: Inputs ───────────────────────────────────────────────
        {
            "column": 0,
            "title":  "Seismic/Earthquake Load (EL) Inputs",
            "rows": [
                {
                    "fields": [{
                        "id":       KEY_SL_SEISMIC_ZONE,
                        "label":    "Seismic Zone",
                        "type":     TYPE_TEXTBOX,
                        "read_only": True,
                        "on_change_compute": _COMPUTE_SEISMIC,                        
                    }]
                },
                {
                    "fields": [{
                        "id":          KEY_SL_IMPORTANCE_FACTOR,
                        "label":       "Importance Factor, I",
                        "type":        TYPE_TEXTBOX,
                        "placeholder": "Enter value",
                        "on_change_compute": _COMPUTE_SEISMIC,
                    }]
                },
                {
                    "fields": [{
                        "id":      KEY_SL_SOIL_TYPE,
                        "label":   "Type of Soil",
                        "type":    TYPE_COMBOBOX,
                        "choices": [
                            "Type I \u2013 Rocky or Hard",
                            "Type II \u2013 Medium Soil",
                            "Type III \u2013 Soft Soil",
                        ],
                        "on_change_compute": _COMPUTE_SEISMIC,
                    }]
                },
                {
                    "fields": [{
                        "id":          KEY_SL_TIME_PERIOD,
                        "label":       "Fundamental Time Period, T (sec)",
                        "type":        TYPE_TEXTBOX,
                        "placeholder": "Enter value",
                        "on_change_compute": _COMPUTE_SEISMIC,
                    }]
                },
                {
                    "fields": [{
                        "id":          KEY_SL_DAMPING,
                        "label":       "Damping Percentage",
                        "type":        TYPE_TEXTBOX,
                        "placeholder": "Enter value",
                        "on_change_compute": _COMPUTE_SEISMIC,
                    }]
                },
                {
                    "fields": [{
                        "id":      KEY_SL_RESPONSE_REDUCTION,
                        "label":   "Response Reduction Factor, R",
                        "type":    TYPE_COMBOBOX,
                        "choices": ["1", "2", "3", "4", "5"],
                        "bind":    "response_factor_combo",
                        "on_change_compute": _COMPUTE_SEISMIC,
                    }]
                },
                {
                    "fields": [{
                        "id":             KEY_SL_DEAD_LOAD,
                        "label":          "Dead Load for Seismic Force (kN)",
                        "type":           TYPE_MODE_LINE,
                        "mode_choices":   ["Automatic", "Custom"],
                        "bind_mode":      "dead_load_seismic_combo",
                        "bind_value":     "dead_load_custom_input",
                        "on_mode_change": "_on_seismic_dead_load_mode_changed",
                        "on_change_compute": _COMPUTE_SEISMIC,
                    }]
                },
                {
                    "fields": [{
                        "id":             KEY_SL_LIVE_LOAD,
                        "label":          "Live Load for Seismic Force (kN)",
                        "type":           TYPE_MODE_LINE,
                        "mode_choices":   ["Automatic", "Custom"],
                        "bind_mode":      "live_load_seismic_combo",
                        "bind_value":     "live_load_custom_input",
                        "on_mode_change": "_on_seismic_live_load_mode_changed",
                        "on_change_compute": _COMPUTE_SEISMIC,
                    }]
                },
            ],
        },

        # ── Column 0: Computed Values ──────────────────────────────────────
        {
            "column": 0,
            "title":  "Computed Values",
            "rows": [
                {
                    "fields": [{
                        "id":       KEY_SL_ZONE_FACTOR,
                        "label":    "Zone Factor, Z",
                        "type":     TYPE_TEXTBOX,
                        "bind":     "zone_factor_input",
                        "read_only": True,
                    }]
                },
                {
                    "fields": [{
                        "id":       KEY_SL_SPECTRAL_COEFF,
                        "label":    "Spectral Acceleration Coefficient, S&#x2090;/g",
                        "type":     TYPE_TEXTBOX,
                        "bind":     "spectral_coeff_input",
                        "read_only": True,
                    }]
                },
                {
                    "fields": [{
                        "id":       KEY_SL_HORIZONTAL_COEFF,
                        "label":    "Horizontal Seismic Coefficient, A&#x2095;",
                        "type":     TYPE_TEXTBOX,
                        "bind":     "horizontal_coeff_input",
                        "read_only": True,
                    }]
                },
                {
                    "fields": [{
                        "id":       KEY_SL_VERTICAL_COEFF,
                        "label":    "Vertical Seismic Coefficient, A&#x1D65;",
                        "type":     TYPE_TEXTBOX,
                        "bind":     "vertical_coeff_input",
                        "read_only": True,
                    }]
                },
            ],
        },

        # ── Column 1: Description ──────────────────────────────────────────
        {
            "column":  1,
            "type":    TYPE_DESCRIPTION,
            "title":   "Description Box",
            "text":    (
                "Seismic Zone is auto-filled from software output (project location).\n\n"
                "The spectral acceleration coefficient depends on soil type and "
                "fundamental time period, T."
            ),
            "stretch": True,
        },
    ],
}

_WIND_LOAD_TAB_SCHEMA = {
    "id":     KEY_WL_TAB,
    "label_width": 270,
    "layout": {
        "type":          "columns",
        "columns":       2,
        "column_widths": [3, 2],
    },
    "sections": [

        # ── Column 0: Wind Inputs ──────────────────────────────────────────
        {
            "column": 0,
            "title":  "Wind Load (WL) Inputs",
            "rows": [
                {"fields": [{"id": KEY_WL_BASIC_WIND_SPEED,       "label": "Basic Wind Speed, V<sub>b</sub> (m/s)",                           "type": TYPE_TEXTBOX,  "read_only": True,  "bind": "basic_wind_speed_input"}]},
                {"fields": [{"id": KEY_WL_AVG_EXPOSED_HEIGHT,     "label": "Average Exposed Height, H (m)",                                   "type": TYPE_TEXTBOX,  "placeholder": "10", "bind": "avg_exposed_height_input"}]},
                {"fields": [{"id": KEY_WL_TERRAIN_TYPE,           "label": "Type of Terrain",                                                 "type": TYPE_COMBOBOX, "choices": ["Plain Terrain", "Terrain with Obstructions"], "bind": "terrain_type_combo"}]},
                {"fields": [{"id": KEY_WL_SITE_TOPOGRAPHY,        "label": "Site Topography",                                                 "type": TYPE_COMBOBOX, "choices": ["Flat", "Hill, ridge, escarpment or cliff"], "bind": "site_topography_combo"}]},
                {"fields": [{"id": KEY_WL_GUST_FACTOR,            "label": "Gust Factor, G",                                                  "type": TYPE_MODE_LINE, "mode_choices": ["As per IRC 6", "Custom"], "bind_mode": "gust_factor_combo",       "bind_value": "gust_factor_value",       "on_mode_change": "_toggle_wind_custom_input"}]},
                {"fields": [{"id": KEY_WL_DRAG_COEFF,             "label": "Drag Coefficient, C<sub>D</sub>",                                 "type": TYPE_MODE_LINE, "mode_choices": ["As per IRC 6", "Custom"], "bind_mode": "drag_coeff_combo",         "bind_value": "drag_coeff_value",        "on_mode_change": "_toggle_wind_custom_input"}]},
                {"fields": [{"id": KEY_WL_DRAG_COEFF_LL,          "label": "Drag Coefficient against Live Load, C<sub>DLL</sub>",             "type": TYPE_MODE_LINE, "mode_choices": ["As per IRC 6", "Custom"], "bind_mode": "drag_coeff_ll_combo",      "bind_value": "drag_coeff_ll_value",     "on_mode_change": "_toggle_wind_custom_input"}]},
                {"fields": [{"id": KEY_WL_LIFT_COEFF,             "label": "Lift Coefficient, C<sub>L</sub>",                                 "type": TYPE_MODE_LINE, "mode_choices": ["As per IRC 6", "Custom"], "bind_mode": "lift_coeff_combo",         "bind_value": "lift_coeff_value",        "on_mode_change": "_toggle_wind_custom_input"}]},
                {"fields": [{"id": KEY_WL_SUPER_AREA_ELEV,        "label": "Superstructure Area in Elevation, A<sub>1</sub> (m²)",            "type": TYPE_MODE_LINE, "mode_choices": ["Automatic", "Custom"],   "bind_mode": "super_area_elev_combo",    "bind_value": "super_area_elev_value",   "on_mode_change": "_toggle_wind_custom_input"}]},
                {"fields": [{"id": KEY_WL_SUPER_AREA_PLAIN,       "label": "Superstructure Area in Plain, A<sub>3</sub> (m²)",                "type": TYPE_MODE_LINE, "mode_choices": ["Automatic", "Custom"],   "bind_mode": "super_area_plain_combo",   "bind_value": "super_area_plain_value",  "on_mode_change": "_toggle_wind_custom_input"}]},
                {"fields": [{"id": KEY_WL_EXPOSED_FRONTAL,        "label": "Exposed Frontal Area of Live Load, A<sub>1LL</sub> (m²)",         "type": TYPE_MODE_LINE, "mode_choices": ["Automatic", "Custom"],   "bind_mode": "exposed_frontal_area_combo","bind_value":"exposed_frontal_area_value","on_mode_change": "_toggle_wind_custom_input"}]},
                {"fields": [{"id": KEY_WL_WIND_ECC_DECK,          "label": "Wind Load Eccentricity from Top of Deck (m)",                     "type": TYPE_MODE_LINE, "mode_choices": ["As per IRC 6","Custom"], "bind_mode":"wind_ecc_deck_combo",      "bind_value":"wind_ecc_deck_value",     "on_mode_change":"_toggle_wind_custom_input"}]},
                {"fields": [{"id": KEY_WL_WIND_LL_ECC,            "label": "Wind on Live Load Eccentricity from Top of Deck (m)",             "type": TYPE_MODE_LINE, "mode_choices": ["As per IRC 6", "Custom"], "bind_mode": "wind_ll_ecc_combo",        "bind_value": "wind_ll_ecc_value",       "on_mode_change": "_toggle_wind_custom_input"}]},
            ],
        },

        # ── Column 0: Computed Values ──────────────────────────────────────
        {
            "column": 0,
            "title":  "Computed Values",
            "rows": [
                {"fields": [{"id": KEY_WL_HOURLY_MEAN_WIND,        "label": "Hourly Mean Wind Speed, V<sub>z</sub> (m/s)",                    "type": TYPE_TEXTBOX, "read_only": True, "bind": "hourly_mean_wind_input"}]},
                {"fields": [{"id": KEY_WL_HOURLY_WIND_PRESSURE,    "label": "Hourly Wind Pressure, P<sub>z</sub> (N/m²)",                     "type": TYPE_TEXTBOX, "read_only": True, "bind": "hourly_wind_pressure_input"}]},
                {"fields": [{"id": KEY_WL_TRANSVERSE_WIND_FORCE,   "label": "Transverse Wind Force, F<sub>T</sub> (N)",                       "type": TYPE_TEXTBOX, "read_only": True, "bind": "transverse_wind_force_input"}]},
                {"fields": [{"id": KEY_WL_LONGITUDINAL_WIND_FORCE, "label": "Longitudinal Wind Force, F<sub>L</sub> (N)",                     "type": TYPE_TEXTBOX, "read_only": True, "bind": "longitudinal_wind_force_input"}]},
                {"fields": [{"id": KEY_WL_VERTICAL_WIND_FORCE,     "label": "Vertical Wind Force, F<sub>V</sub> (N)",                         "type": TYPE_TEXTBOX, "read_only": True, "bind": "vertical_wind_force_input"}]},
                {"fields": [{"id": KEY_WL_TRANSVERSE_WIND_LL,      "label": "Transverse Wind Force on Live Load, F<sub>TLL</sub> (N)",        "type": TYPE_TEXTBOX, "read_only": True, "bind": "transverse_wind_ll_input"}]},
                {"fields": [{"id": KEY_WL_LONGITUDINAL_WIND_LL,    "label": "Longitudinal Wind Force on Live Load, F<sub>LLL</sub> (N)", "type": TYPE_TEXTBOX, "read_only": True, "bind": "longitudinal_wind_ll_input"}]},
            ],
        },

        # ── Column 1: Description ──────────────────────────────────────────
        {
            "column":  1,
            "type":    TYPE_DESCRIPTION,
            "title":   "Description Box",
            "text":    "Basic Wind Speed is auto-filled from software output (project location).",
            "stretch": True,
        },
    ],
}

_TEMPERATURE_LOAD_TAB_SCHEMA = {
    "id":     KEY_TL_TAB,
    "layout": {
        "type":          "columns",
        "columns":       2,
        "column_widths": [3, 2],
    },
    "sections": [

        # ── Column 0: Temperature Inputs ───────────────────────────────────
        {
            "column": 0,
            "title":  "Temperature Load (TL) Inputs for Evaluation per IRC6",
            "rows": [
                {"fields": [{"id": KEY_TL_HIGHEST_MAX_TEMP,    "label": "Highest Maximum Air Temperature (°C)",                    "type": TYPE_TEXTBOX, "placeholder": "From Project Location", "enabled": False, "bind": "highest_max_temp_input"}]},
                {"fields": [{"id": KEY_TL_LOWEST_MIN_TEMP,     "label": "Lowest Minimum Air Temperature (°C)",                     "type": TYPE_TEXTBOX, "placeholder": "From Project Location", "enabled": False, "bind": "lowest_min_temp_input"}]},
                {"fields": [{"id": KEY_TL_THERMAL_COEFF_STEEL, "label": "Coefficient of Thermal Expansion for Steel (1/°C)",       "type": TYPE_TEXTBOX, "placeholder": "e.g. 12.0e-6",        "bind": "thermal_coeff_steel_input"}]},
                {"fields": [{"id": KEY_TL_THERMAL_COEFF_RCC,   "label": "Coefficient of Thermal Expansion for RCC (1/°C)",         "type": TYPE_TEXTBOX, "placeholder": "e.g. 12.0e-6",        "bind": "thermal_coeff_rcc_input"}]},
            ],
        },

        # ── Column 0: Bridge Temperature Range ─────────────────────────────
        {
            "column": 0,
            "title":  "Range of Effective Bridge Temperature",
            "rows": [
                {"fields": [{"id": KEY_TL_BRIDGE_TEMP_MIN, "label": "Minimum (°C)", "type": TYPE_TEXTBOX, "read_only": True, "bind": "bridge_temp_min_input"}]},
                {"fields": [{"id": KEY_TL_BRIDGE_TEMP_MAX, "label": "Maximum (°C)", "type": TYPE_TEXTBOX, "read_only": True, "bind": "bridge_temp_max_input"}]},
            ],
        },

        # ── Column 0: Temperature for Design ───────────────────────────────
        {
            "column": 0,
            "title":  "Temperature for Design",
            "rows": [
                {"fields": [{"id": KEY_TL_TEMP_RISE, "label": "Rise (°C)", "type": TYPE_TEXTBOX, "read_only": True, "bind": "temp_rise_input"}]},
                {"fields": [{"id": KEY_TL_TEMP_FALL, "label": "Fall (°C)", "type": TYPE_TEXTBOX, "read_only": True, "bind": "temp_fall_input"}]},
            ],
        },

        # ── Column 1: Description ──────────────────────────────────────────
        {
            "column":  1,
            "type":    TYPE_DESCRIPTION,
            "title":   "Description Box",
            "text":    "",
            "stretch": True,
        },
    ],
}

_CUSTOM_LOAD_TAB_SCHEMA = {
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

_LOAD_COMBINATION_TAB_SCHEMA = {
    "id":     KEY_LC_TAB,
    "layout": {
        "type":          "columns",
        "columns":       2,
        "column_widths": [3, 2],
    },
    "sections": [

        # ── Column 0: IRC Load Combinations ────────────────────────────────
        {
            "column": 0,
            "title":  "Load Combinations from IRC 6",
            "rows":   [],
        },

        # ── Column 0: Custom Load Combination ──────────────────────────────
        {
            "column": 0,
            "title":  "",
            "rows": [
                {
                    "fields": [{
                        "id":       KEY_LC_COMBINATIONS,
                        "type":     TYPE_LOAD_COMBINATION,
                        "on_click": "_on_add_custom_combination",
                    }]
                },
            ],
        },

        # ── Column 1: Description ───────────────────────────────────────────
        {
            "column":  1,
            "type":    TYPE_DESCRIPTION,
            "title":   "Description Box",
            "text":    "",
            "stretch": True,
        },
    ],
}

LOADING_TAB_SCHEMA = {
    "id":     KEY_LOADING_TAB,
    "layout": {"type": "tabs"},
    "tabs": [
        {"title": "Permanent Load",   "schema": _PERMANENT_LOAD_TAB_SCHEMA                    },
        {"title": "Live Load",        "schema": _LIVE_LOAD_TAB_SCHEMA                         },
        {
            "title": "Seismic Load",
            "schema": _SEISMIC_LOAD_TAB_SCHEMA,
            "refresh": [{
                            "widget_id": KEY_SL_SEISMIC_ZONE,
                            "path": ["project.location", "weather_data", "zone"],
                        }],
        },
        {
            "title": "Wind Load",
            "schema": _WIND_LOAD_TAB_SCHEMA,
            "refresh": [{
                            "widget_id": KEY_WL_BASIC_WIND_SPEED,
                            "path": ["project.location", "weather_data", "wind_speed"]
                        }],
        },
        {
            "title": "Temperature Load",
            "schema": _TEMPERATURE_LOAD_TAB_SCHEMA,
            "refresh": [{
                            "widget_id": KEY_TL_HIGHEST_MAX_TEMP, 
                            "path": ["project.location", "weather_data", "max_temp"]
                        },
                        {
                            "widget_id": KEY_TL_LOWEST_MIN_TEMP,
                            "path": ["project.location", "weather_data", "min_temp"]
                        }],
        },
        {"title": "Custom Load",      "schema": _CUSTOM_LOAD_TAB_SCHEMA,      "disable": True },
        {"title": "Load Combination", "schema": _LOAD_COMBINATION_TAB_SCHEMA                  },
    ],
}

from osdagbridge.desktop.ui.dialogs.additional_input.drawings.support_conditions_cad import SupportCADWidget
from osdagbridge.desktop.ui.dialogs.additional_input.drawings.support_detail_cad import SupportDetailCADWidget

SUPPORT_CONDITIONS_SCHEMA = {
    "id":     KEY_SC_TAB,
    "layout": {"type": "rows", "columns": 1},
    "sections": [

        {
            "column": 0,
            "title":  "Support Conditions",
            "rows": [
                {
                    "fields": 
                    [{
                        "id": KEY_SC_LEFT_SUPPORT,  
                        "label": "Left Support",  
                        "type": TYPE_COMBOBOX, 
                        "choices": ["Fixed", "Pinned", "Roller"],
                        "enabled_choices": ["Pinned"],
                        }]},
                {
                    "fields": 
                    [{
                        "id": KEY_SC_RIGHT_SUPPORT, 
                        "label": "Right Support", 
                        "type": TYPE_COMBOBOX, 
                        "choices": ["Fixed", "Pinned", "Roller"],
                        "enabled_choices": ["Roller"],
                    }]},
            ],
        },

        {
            "column": 0,
            "title":  "Bearing Length",
            "rows": [
                {
                    "fields": 
                    [{
                        "id": KEY_SC_BEARING_LENGTH,
                        "label": "Bearing Length Value (mm)",
                        "type": TYPE_TEXTBOX,
                        "placeholder": "0 - 600",
                        "on_text_changed": "_update_support_detail_cad"
                    }]
                },
            ],
        },

        {
            "column": 0,
            "title":  "",
            "rows": [
                {
                    "fields": [
                        {
                            "id":           KEY_SC_LEFT_CAD,
                            "type":         TYPE_DIRECT_WIDGET,
                            "widget_class": SupportCADWidget,
                        },
                        {
                            "id":             KEY_SC_RIGHT_CAD,
                            "type":           TYPE_DIRECT_WIDGET,
                            "widget_class":   SupportDetailCADWidget,
                        },
                    ]
                },
            ],
        },
    ],
}

DESIGN_OPTIONS_SCHEMA = {
    "id":     KEY_DS_TAB,
    "layout": {
        "type":          "columns",
        "columns":       2,
        "column_widths": [3, 2],
    },
    "sections": [

        # ──────────────── Column 0: Construction Stages ────────────────
        {
            "column": 0,
            "title":  "Construction Stages",
            "rows": [
                {
                    "fields": [{
                        "id":      KEY_DS_CONSTRUCTION_STAGE,
                        "label":   "Include automatic",
                        "type":    TYPE_COMBOBOX,
                        "choices": ["Yes", "No"],
                        "bind":    "construction_stage_combo",
                    }]
                },
            ],
        },

        # ──────────────── Column 0: Deck Design ────────────────
        {
            "column": 0,
            "title":  "Deck Design",
            "rows": [
                {
                    "fields": [
                        {
                            "id":             KEY_DS_REINF_BOUNDS,
                            "label":          "Reinforcement Size",
                            "type":           TYPE_BOUND_BTN,
                            "text":           "Set Bounds",
                            "with_increment": False,
                            "lower_limit":    8.0,
                            "upper_limit":    40.0,
                        },
                    ]
                },
                {
                    "fields": [{
                        "id":      KEY_DS_REINF_MATERIAL,
                        "label":   "Reinforcement Material",
                        "type":    TYPE_COMBOBOX,
                        "choices": ["Fe 415", "Fe 415D", "Fe 500", "Fe 500D", "Fe 550", "Fe 550D", "Fe 600"],
                        "bind":    "reinforcement_material_combo",
                    }]
                },
                {
                    "fields": [{
                        "id":          KEY_DS_TOP_CLEAR_COVER,
                        "label":       "Top Clear Cover (mm)",
                        "type":        TYPE_TEXTBOX,
                        "placeholder": "40 - 75",
                        "bind":        "top_clear_cover_input",
                    }]
                },
                {
                    "fields": [{
                        "id":          KEY_DS_BOTTOM_CLEAR_COVER,
                        "label":       "Bottom Clear Cover (mm)",
                        "type":        TYPE_TEXTBOX,
                        "placeholder": "35 - 75",
                        "bind":        "bottom_clear_cover_input",
                    }]
                },
                {
                    "fields": [{
                        "id":          KEY_DS_SIDE_CLEAR_COVER,
                        "label":       "Side Clear Cover (mm)",
                        "type":        TYPE_TEXTBOX,
                        "placeholder": "35 - 75",
                        "bind":        "side_clear_cover_input",
                    }]
                },
            ],
        },

        # ──────────────── Column 0: Shear Studs ────────────────
        {
            "column": 0,
            "title":  "Shear Studs",
            "rows": [
                {
                    "fields": [{
                        "id":          KEY_DS_STUD_YIELD_STRENGTH,
                        "label":       "Yield Strength (MPa)",
                        "type":        TYPE_TEXTBOX,
                        "placeholder": "350 - 600",
                        "bind":        "shear_stud_yield_strength_input",
                    }]
                },
                {
                    "fields": [{
                        "id":          KEY_DS_STUD_ULTIMATE_STRENGTH,
                        "label":       "Ultimate Strength (MPa)",
                        "type":        TYPE_TEXTBOX,
                        "placeholder": "350 - 600",
                        "bind":        "shear_stud_ultimate_strength_input",
                    }]
                },
                {
                    "fields": [{
                        "id":      KEY_DS_STUD_DIAMETER,
                        "label":   "Diameter (mm)",
                        "type":    TYPE_COMBOBOX,
                        "choices": ["12", "16", "20", "22", "25"],
                        "bind":    "shear_stud_diameter_combo",
                    }]
                },
                {
                    "fields": [{
                        "id":          KEY_DS_STUD_HEIGHT,
                        "label":       "Height (mm)",
                        "type":        TYPE_TEXTBOX,
                        "placeholder": "0 - 500",
                        "bind":        "shear_stud_height_input",
                    }]
                },
                {
                    "fields": [{
                        "id":      KEY_DS_STUD_COUNT,
                        "label":   "No. of Shear Studs per Section",
                        "type":    TYPE_COMBOBOX,
                        "choices": [str(i) for i in range(1, 11)],
                        "bind":    "shear_stud_count_combo",
                    }]
                },
                {
                    "fields": [{
                        "id":          KEY_DS_STUD_TRANSVERSE_SPACING,
                        "label":       "Transverse Spacing (mm)",
                        "type":        TYPE_TEXTBOX,
                        "placeholder": "0 - 500",
                        "bind":        "shear_stud_spacing_input",
                    }]
                },
            ],
        },

        # ──────────────── Column 1: Description ────────────────
        {
            "column": 1,
            "type":   TYPE_DESCRIPTION,
            "title":  "Description Box",
            "text":   "",
            "stretch": True,
        },
    ],
}

DESIGN_OPTIONS_CONT_SCHEMA = {
    "id": KEY_DO_TAB,
    "layout": {
        "type":    "rows",   # single column, sections stacked vertically
        "columns": 1,
    },
    "sections": [

        # ──────────────────── Partial Factor ────────────────────
        {
            "column": 0,
            "title":  "Partial Factor",
            "rows": [
                {
                    "fields": [{
                        "id":          KEY_DO_GAMMA_C_BASIC,
                        "label":       "Concrete basic & seismic, &#947;<sub>c</sub>",
                        "type":        TYPE_TEXTBOX,
                        "bind":        "gamma_c_basic_input",
                        "placeholder": "1.0 - 2.0",
                    }]
                },
                {
                    "fields": [{
                        "id":          KEY_DO_GAMMA_C_ACCIDENTAL,
                        "label":       "Concrete Accidental, &#947;<sub>c</sub>",
                        "type":        TYPE_TEXTBOX,
                        "bind":        "gamma_c_accidental_input",
                        "placeholder": "1.0 - 2.0",
                    }]
                },
                {
                    "fields": [{
                        "id":          KEY_DO_GAMMA_M0,
                        "label":       "Structural steel for Yielding and Buckling, &#947;<sub>M0</sub>",
                        "type":        TYPE_TEXTBOX,
                        "bind":        "gamma_m0_input",
                        "placeholder": "1.0 - 2.0",
                    }]
                },
                {
                    "fields": [{
                        "id":          KEY_DO_GAMMA_M1,
                        "label":       "Structural Steel For Ultimate Stress, &#947;<sub>M1</sub>",
                        "type":        TYPE_TEXTBOX,
                        "bind":        "gamma_m1_input",
                        "placeholder": "1.0 - 2.0",
                    }]
                },
                {
                    "fields": [{
                        "id":          KEY_DO_GAMMA_S,
                        "label":       "Reinforcing Steel, &#947;<sub>s</sub>",
                        "type":        TYPE_TEXTBOX,
                        "bind":        "gamma_s_input",
                        "placeholder": "1.0 - 2.0",
                    }]
                },
                {
                    "fields": [{
                        "id":          KEY_DO_GAMMA_V,
                        "label":       "Shear Connectors For Yield, &#947;<sub>v</sub>",
                        "type":        TYPE_TEXTBOX,
                        "bind":        "gamma_v_input",
                        "placeholder": "1.0 - 2.0",
                    }]
                },
                {
                    "fields": [{
                        "id":          KEY_DO_GAMMA_FLT,
                        "label":       "Fatigue Load, &#947;<sub>flt</sub>",
                        "type":        TYPE_TEXTBOX,
                        "bind":        "gamma_flt_input",
                        "placeholder": "1.0 - 2.0",
                    }]
                },
                {
                    "fields": [{
                        "id":          KEY_DO_GAMMA_MF,
                        "label":       "Fatigue Strength, &#947;<sub>Mf,t</sub>",
                        "type":        TYPE_TEXTBOX,
                        "bind":        "gamma_mf_input",
                        "placeholder": "1.0 - 2.0",
                    }]
                },
            ],
        },

        # ──────────────────── Resistance to Fatigue ────────────────────
        {
            "column": 0,
            "title":  "Resistance to Fatigue",
            "rows": [
                {
                    "fields": [{
                        "id":          KEY_DO_LOAD_CYCLES,
                        "label":       "Number of Load Cycles",
                        "type":        TYPE_TEXTBOX,
                        "bind":        "load_cycles_input",
                        "placeholder": "100000 - 100000000",
                    }]
                },
            ],
        },

        # ──────────────────── Deflection Control ────────────────────
        {
            "column": 0,
            "title":  "Deflection Control",
            "rows": [
                {
                    "row_fields": [
                        {"label": "Limit :", "type": "label", "after_spacing": 408},
                        {"label": "L /",    "type": "label"},
                        {
                            "id":          KEY_DO_DEFLECTION_LIMIT,
                            "type":        TYPE_TEXTBOX,
                            "bind":        "limit_input",
                            "width":       150,
                            "placeholder": "300 - 800",
                        },
                        {"label": "m", "type": "label"},
                    ]
                },
            ],
        },

        # ──────────────────── Limit States ────────────────────
        {
            "column": 2,
            "title":  "Ultimate Limit States",
            "rows": [
                {"fields": [{"id": KEY_DO_ULS_BENDING,    "label": "Bending Resistance",                    "type": TYPE_CHECKBOX}]},
                {"fields": [{"id": KEY_DO_ULS_SHEAR,      "label": "Resistance to Vertical Shear",          "type": TYPE_CHECKBOX}]},
                {"fields": [{"id": KEY_DO_ULS_LTB,        "label": "Resistance to Lateral-torsional Buckling", "type": TYPE_CHECKBOX}]},
                {"fields": [{"id": KEY_DO_ULS_TRANSVERSE,  "label": "Resistance to Transverse force",       "type": TYPE_CHECKBOX}]},
                {"fields": [{"id": KEY_DO_ULS_LONG_SHEAR,  "label": "Resistance to Longitudinal Shear",     "type": TYPE_CHECKBOX}]},
                {"fields": [{"id": KEY_DO_ULS_FATIGUE,     "label": "Resistance to Fatigue",                "type": TYPE_CHECKBOX}]},
            ],
        },
        {
            "column": 2,
            "title":  "Serviceability Limit States",
            "rows": [
                {"fields": [{"id": KEY_DO_SLS_STRESS,      "label": "Stress Limitation",        "type": TYPE_CHECKBOX}]},
                {"fields": [{"id": KEY_DO_SLS_LONG_SHEAR,  "label": "Longitudinal Shear (SLS)", "type": TYPE_CHECKBOX}]},
                {"fields": [{"id": KEY_DO_SLS_DEFLECTION,  "label": "Deflection Control",       "type": TYPE_CHECKBOX}]},
                {"fields": [{"id": KEY_DO_SLS_CRACK_WIDTH,  "label": "Crack Width Check",       "type": TYPE_CHECKBOX}]},
            ],
        },
    ],
}


STEEL_DESIGN_DETAILS_SCHEMA = {
    "cad": {
        "top": {
            "id": KEY_SD_DETAILS_CAD_TOP,
            "min_height": 160,
        },
        "bottom": {
            "id": KEY_SD_DETAILS_CAD_BOTTOM,
            "width": 400,
            "height": 200,
        },
    },
    "cards": [
        {
            "id": KEY_SD_DETAILS_DIMENSIONAL_CARD,
            "title": "Dimensional Details:",
            "fields": [
                {
                    "id": KEY_SD_GRADE_OF_MATERIAL,
                    "label": "Grade of Material:",
                    "data_key": "grade_of_material",
                    "group": "member",
                },
                {
                    "id": KEY_SD_SECTION_TYPE,
                    "label": "Type:",
                    "data_key": "section_type",
                    "group": "member",
                },
                {
                    "id": KEY_SD_SECTION_DESIGNATION,
                    "label": "Section Designation",
                    "data_key": "section_designation",
                    "group": "dim",
                },
                {
                    "id": KEY_SD_SECTION_CLASS,
                    "label": "Section Class",
                    "data_key": "section_class",
                    "group": "dim",
                },
                {
                    "id": KEY_SD_TOTAL_DEPTH,
                    "label": "Total Depth (mm)",
                    "data_key": "total_depth",
                    "group": "dim",
                },
                {
                    "id": KEY_SD_WEB_THICKNESS,
                    "label": "Web Thickness (mm)",
                    "data_key": "web_thickness",
                    "group": "dim",
                },
                {
                    "id": KEY_SD_TOP_FLANGE_WIDTH,
                    "label": "Top Flange Width (mm)",
                    "data_key": "top_flange_width",
                    "group": "dim",
                },
                {
                    "id": KEY_SD_TOP_FLANGE_THICKNESS,
                    "label": "Top Flange Thickness (mm)",
                    "data_key": "top_flange_thickness",
                    "group": "dim",
                },
                {
                    "id": KEY_SD_BOTTOM_FLANGE_WIDTH,
                    "label": "Bottom Flange Width (mm)",
                    "data_key": "bottom_flange_width",
                    "group": "dim",
                },
                {
                    "id": KEY_SD_BOTTOM_FLANGE_THICKNESS,
                    "label": "Bottom Flange Thickness (mm)",
                    "data_key": "bottom_flange_thickness",
                    "group": "dim",
                },
                {
                    "id": KEY_SD_TORSIONAL_RESTRAINT,
                    "label": "Torsional Restraint",
                    "data_key": "torsional_restraint",
                    "group": "dim",
                },
                {
                    "id": KEY_SD_WARPING_RESTRAINT,
                    "label": "Warping Restraint",
                    "data_key": "warping_restraint",
                    "group": "dim",
                },
                {
                    "id": KEY_SD_WEB_TYPE,
                    "label": "Web Type",
                    "data_key": "web_type",
                    "group": "dim",
                },
                {
                    "id": KEY_SD_EFFECTIVE_SLAB_WIDTH,
                    "label": "Effective Width of Slab (mm)",
                    "data_key": "effective_slab_width",
                    "group": "dim",
                },
            ],
        },
        {
            "id": KEY_SD_DETAILS_SHEAR_CARD,
            "title": "Shear Connector Details:",
            "fields": [
                {
                    "id": KEY_SD_SHEAR_YIELD_STRENGTH,
                    "label": "Material Yield Strength (MPa)",
                    "data_key": "shear_material_yield_strength",
                    "group": "shear",
                },
                {
                    "id": KEY_SD_SHEAR_ULTIMATE_STRENGTH,
                    "label": "Material Ultimate Strength (MPa)",
                    "data_key": "shear_material_ultimate_strength",
                    "group": "shear",
                },
                {
                    "id": KEY_SD_SHEAR_DIAMETER,
                    "label": "Diameter (mm)",
                    "data_key": "shear_diameter",
                    "group": "shear",
                },
                {
                    "id": KEY_SD_SHEAR_HEIGHT,
                    "label": "Height (mm)",
                    "data_key": "shear_height",
                    "group": "shear",
                },
                {
                    "id": KEY_SD_SHEAR_TRANSVERSE_SPACING,
                    "label": "Transverse Spacing (mm)",
                    "data_key": "shear_transverse_spacing",
                    "group": "shear",
                },
                {
                    "id": KEY_SD_SHEAR_STUDS_PER_SECTION,
                    "label": "No. of Shear Studs per Section",
                    "data_key": "shear_studs_per_section",
                    "group": "shear",
                },
                {
                    "id": KEY_SD_SHEAR_LONGITUDINAL_SPACING,
                    "label": "Average Longitudinal Spacing (mm)",
                    "data_key": "shear_longitudinal_spacing",
                    "group": "shear",
                },
            ],
        },
        {
            "id": KEY_SD_DETAILS_SECTION_PROPERTIES_CARD,
            "title": "Section Properties:",
            "fields": [
                {
                    "id": KEY_SD_SECTION_PROP_MASS,
                    "label": "Mass, M (Kg/m)",
                    "data_key": "mass",
                    "group": "section",
                },
                {
                    "id": KEY_SD_SECTION_PROP_AREA,
                    "label": "Sectional Area, a (cm<sup>2</sup>)",
                    "data_key": "area",
                    "group": "section",
                },
                {
                    "id": KEY_SD_SECTION_PROP_IZ,
                    "label": "2nd Moment of Area, I<sub>z</sub> (cm<sup>4</sup>)",
                    "data_key": "iz",
                    "group": "section",
                },
                {
                    "id": KEY_SD_SECTION_PROP_IV,
                    "label": "2nd Moment of Area, I<sub>y</sub> (cm<sup>4</sup>)",
                    "data_key": "iv",
                    "group": "section",
                },
                {
                    "id": KEY_SD_SECTION_PROP_RZ,
                    "label": "Radius of Gyration, r<sub>z</sub> (cm)",
                    "data_key": "rz",
                    "group": "section",
                },
                {
                    "id": KEY_SD_SECTION_PROP_RV,
                    "label": "Radius of Gyration, r<sub>y</sub> (cm)",
                    "data_key": "rv",
                    "group": "section",
                },
                {
                    "id": KEY_SD_SECTION_PROP_ZZ,
                    "label": "Elastic Modulus, Z<sub>z</sub> (cm<sup>3</sup>)",
                    "data_key": "zz",
                    "group": "section",
                },
                {
                    "id": KEY_SD_SECTION_PROP_ZV,
                    "label": "Elastic Modulus, Z<sub>y</sub> (cm<sup>3</sup>)",
                    "data_key": "zv",
                    "group": "section",
                },
                {
                    "id": KEY_SD_SECTION_PROP_ZUZ,
                    "label": "Plastic Modulus, Z<sub>pz</sub> (cm<sup>3</sup>)",
                    "data_key": "zuz",
                    "group": "section",
                },
                {
                    "id": KEY_SD_SECTION_PROP_ZUV,
                    "label": "Plastic Modulus, Z<sub>py</sub> (cm<sup>3</sup>)",
                    "data_key": "zuv",
                    "group": "section",
                },
                {
                    "id": KEY_SD_SECTION_PROP_IT,
                    "label": "Torsion Constant, I<sub>t</sub> (cm<sup>4</sup>)",
                    "data_key": "it",
                    "group": "section",
                },
                {
                    "id": KEY_SD_SECTION_PROP_IW,
                    "label": "Warping Constant, I<sub>w</sub> (cm<sup>6</sup>)",
                    "data_key": "iw",
                    "group": "section",
                },
            ],
        },
    ],
    "stiffener": {
        "id": KEY_SD_DETAILS_STIFFENER_TABLE,
        "row_height": 40,
        "columns": [
            {"id": "stiffener_type", "label": "Type"},
            {"id": KEY_SD_STIFFENER_COL_GRADE, "label": "Grade of Material", "suffix": "grade"},
            {"id": KEY_SD_STIFFENER_COL_THICKNESS, "label": "Thickness (mm)", "suffix": "thickness"},
            {"id": KEY_SD_STIFFENER_COL_WIDTH, "label": "Width (mm)", "suffix": "width"},
            {"id": KEY_SD_STIFFENER_COL_SPACING, "label": "Spacing (mm)", "suffix": "spacing"},
        ],
        "rows": [
            {
                "id": KEY_SD_STIFFENER_ROW_INTERMEDIATE,
                "label": "Intermediate",
                "data_prefix": "stiff_intermediate",
            },
            {
                "id": KEY_SD_STIFFENER_ROW_LONGITUDINAL,
                "label": "Longitudinal",
                "data_prefix": "stiff_longitudinal",
            },
            {
                "id": KEY_SD_STIFFENER_ROW_BEARING,
                "label": "Bearing",
                "data_prefix": "stiff_bearing",
            },
        ],
    },
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

# Transverse Member Design Dialog Schema

TRANSVERSE_MEMBER_DESIGN_SCHEMA = {
    "id": KEY_TD_DIALOG,
    "title": "Transverse Member Design",
    "window": {"width": 1100, "height": 720, "min_width": 950, "min_height": 550},

    # Global bar - only Member ID + Load Combination
    "global_bar": [
        {"id": KEY_TD_MEMBER_ID,        "label": "Member ID",        "type": "combo"},
        {"id": KEY_TD_LOAD_COMBINATION, "label": "Load Combination", "type": "combo", "default": "Envelope"},
    ],

    # Details Tab
    "details_tab": {
        "id": KEY_TD_DETAILS_TAB,
        "label": "Details",
        "left_panel": {
            "section_inputs": {
                "label": "Section Inputs:",
                "label_width": 100,
                "fields": [
                    {"id": KEY_TD_SECTION_INPUTS_DESIGN,                     "label": "Design:",                            "type": "line",     "read_only": True},
                    {"id": KEY_TD_SECTION_INPUTS_BRACING_TYPE,               "label": "Type of Bracing:",                   "type": "line",     "read_only": True},
                    {"id": KEY_TD_SECTION_INPUTS_BRACING_SECTION_TYPE,       "label": "Bracing Section Type:",              "type": "line",     "read_only": True},
                    {"id": KEY_TD_SECTION_INPUTS_BRACING_SECTION_DESIGNATION,"label": "Bracing Section Designation:",       "type": "line",     "read_only": True},
                    {"id": KEY_TD_SECTION_INPUTS_TOP_CHORD_ENABLED,          "label": "Top Chord",                          "type": "checkbox", "default": True, "enabled": False},
                    {"id": KEY_TD_SECTION_INPUTS_TOP_CHORD_SECTION_TYPE,     "label": "  Top Chord Section Type:",          "type": "line",     "read_only": True},
                    {"id": KEY_TD_SECTION_INPUTS_TOP_CHORD_SECTION_DESIGNATION,"label": "  Top Chord Section Designation:",   "type": "line",     "read_only": True},
                    {"id": KEY_TD_SECTION_INPUTS_BOTTOM_CHORD_ENABLED,       "label": "Bottom Chord",                       "type": "checkbox", "default": True, "enabled": False},
                    {"id": KEY_TD_SECTION_INPUTS_BOTTOM_CHORD_SECTION_TYPE,  "label": "  Bottom Chord Section Type:",       "type": "line",     "read_only": True},
                    {"id": KEY_TD_SECTION_INPUTS_BOTTOM_CHORD_SECTION_DESIGNATION, "label": "  Bottom Chord Section Designation:","type": "line",     "read_only": True},
                    {"id": KEY_TD_SECTION_INPUTS_SPACING,                    "label": "Spacing:",                           "type": "line",     "read_only": True},
                ],
            },
        },
        "right_panel": {
            "bracing_diagram": {"id": KEY_TD_BRACING_DIAGRAM, "height": 170},
            "section_cards": [
                {
                    "id":    KEY_TD_SECTION_PROPS_BRACING,
                    "title": "Bracing",
                    "col1": ["L (m)", "H (m)", "B (m)", "tw (m)", "tF (m)", "rz (cm)"],
                    "col2": ["M (Kg/m)", "A (cm²)", "Iz (cm⁴)", "Iv (cm⁴)", "rv (cm)"],
                    "col3": ["Zz (cm³)", "Zv (cm³)", "Zuz (cm³)", "Zuv (cm³)"],
                },
                {
                    "id":    KEY_TD_SECTION_PROPS_TOP_CHORD,
                    "title": "Top Chord",
                    "col1": ["L (m)", "H (m)", "B (m)", "tw (m)", "tF (m)", "rz (cm)"],
                    "col2": ["M (Kg/m)", "A (cm²)", "Iz (cm⁴)", "Iv (cm⁴)", "rv (cm)"],
                    "col3": ["Zz (cm³)", "Zv (cm³)", "Zuz (cm³)", "Zuv (cm³)"],
                },
                {
                    "id":    KEY_TD_SECTION_PROPS_BOTTOM_CHORD,
                    "title": "Bottom Chord",
                    "col1": ["L (m)", "H (m)", "B (m)", "tw (m)", "tF (m)", "rz (cm)"],
                    "col2": ["M (Kg/m)", "A (cm²)", "Iz (cm⁴)", "Iv (cm⁴)", "rv (cm)"],
                    "col3": ["Zz (cm³)", "Zv (cm³)", "Zuz (cm³)", "Zuv (cm³)"],
                },
            ],
        },
    },

    # Design Check Tab
    "design_check_tab": {
        "id": KEY_TD_DESIGN_CHECK_TAB,
        "label": "Design Check",
        "forces_table": {
            "id":      KEY_TD_DESIGN_CHECK_FORCES_TABLE,
            "title":   "Design Forces Summary:",
            "columns": ["Member", "Tension (kN)", "Compression (kN)", "Gov. LC"],
            "always_visible": True,
        },
        "results_table": {
            "id": KEY_TD_DESIGN_CHECK_RESULTS,
            "title": "Design Check Results:",
            "min_height": 200,
            "columns": [
                "Member",
                "Force Type",
                "Force (kN)",
                "Section",
                "Capacity (kN)",
                "Eff. Ratio",
                "λ (slend.)",
                "Connection",
                "Status",
            ],
        },
    },
}

DECK_DESIGN_SUMMARY_SCHEMA = {
    "properties_card": {
        "title": "Deck Properties:",
        "fields": [
            {"label": "Grade of Material:", "data_key": "deck_grade"},
            {"label": "Thickness (mm):", "data_key": "deck_thickness"},
            {"label": "Deck Overhang (mm):", "data_key": "deck_overhang"},
        ]
    },
    "reinforcement_table": {
        "title": "Reinforcement Details:",
        "columns": [
            "Position",
            "Material Yield\nStrength (MPa)",
            "Diameter (mm)",
            "Spacing (mm)",
            "Clear Cover\n(mm)",
            "Area (mm²)"
        ],
        "rows": [
            {"label": "Top Layer", "prefix": "rebar_top"},
            {"label": "Bottom Layer", "prefix": "rebar_bottom"},
            {"label": "Overhang", "prefix": "rebar_overhang", "is_overhang": True}
        ],
        "data_suffixes": ["yield", "dia", "spacing", "cover", "area"]
    },
    "utilization_card": {
        "title": "Utilization Summary:",
        "checks": [
            {"key": "ur_bot_uls",   "label": "ULS - Bottom (Sagging)",         "is_overhang": False},
            {"key": "ur_top_uls",   "label": "ULS - Top (Hogging)",            "is_overhang": False},
            {"key": "ur_oh_uls",    "label": "ULS - Overhang",                 "is_overhang": True},
            {"key": "ur_bot_sls_c", "label": "SLS - Bottom Concrete Stress",   "is_overhang": False},
            {"key": "ur_bot_sls_s", "label": "SLS - Bottom Steel Stress",      "is_overhang": False},
            {"key": "ur_top_sls_c", "label": "SLS - Top Concrete Stress",      "is_overhang": False},
            {"key": "ur_top_sls_s", "label": "SLS - Top Steel Stress",         "is_overhang": False},
            {"key": "ur_bot_crack", "label": "SLS - Bottom Crack Width",       "is_overhang": False},
            {"key": "ur_top_crack", "label": "SLS - Top Crack Width",          "is_overhang": False},
            {"key": "ur_oh_sls_c",  "label": "SLS - Overhang Concrete Stress", "is_overhang": True},
            {"key": "ur_oh_sls_s",  "label": "SLS - Overhang Steel Stress",    "is_overhang": True},
            {"key": "ur_oh_crack",  "label": "SLS - Overhang Crack Width",     "is_overhang": True},
        ]
    },
    "design_check_card": {
        "title": "Design Check:",
        "data_key": "deck_design_check"
    }
}



"""
Default data schema for Generate Results Table dialog.

Purpose:
Centralized source of table structure (columns) for all result tables.
Rows are intentionally empty — resolvers in generate_results_values_builder.py
populate them with live values when the user has entered the required inputs.
"""

EMPTY = "-"

GENERATE_RESULTS_DEFAULTS = {

    "model_definition": {
        "id": "model_definition",
        "label": "Model Definition",

        "bridge_configuration": {
            "id": "bridge_configuration",
            "label": "Bridge Configuration",

            "bridge_configuration_summary": {
                "id": "bridge_configuration_summary",
                "label": "Bridge Configuration Summary",
                "columns": [
                    "Overall Width (m)",
                    "Span (m)",
                    "No. of Girders",
                    "Girder Spacing (m)",
                    "Deck Overhang (m)",
                    "Skew Angle (deg)",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },

            "material_properties_steel": {
                "id": "material_properties_steel",
                "label": "Material Properties - Steel",
                "columns": [
                    "Component",
                    "Grade",
                    "Ultimate Tensile Strength, Fᵤ (MPa)",
                    "Yield Strength, Fᵧ (MPa)",
                    "Modulus of Elasticity, E (MPa)",
                    "Modulus of Rigidity, G (MPa)",
                    "Poisson's Ratio, ν",
                    "Thermal Expansion Coefficient (×10⁻⁶/°C)",
                ],
                "rows": [
                    ["Girder",        EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                    ["Cross Bracing", EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                    ["End Diaphragm", EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },

            "material_properties_concrete": {
                "id": "material_properties_concrete",
                "label": "Material Properties - Concrete",
                "columns": [
                    "Component",
                    "Grade",
                    "Characteristic Compressive Strength, fₖ (MPa)",
                    "Mean Tensile Strength, fₜₘ (MPa)",
                    "Secant Modulus of Elasticity, Eₘ (MPa)",
                    "Modular Ratio",
                    "Density (kN/m³)",
                    "Poisson's Ratio, ν",
                ],
                "rows": [
                    ["Deck Slab", EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },
        },

        "load_definitions": {
            "id": "load_definitions",
            "label": "Load Definitions",

            "permanent_load_summary": {
                "id": "permanent_load_summary",
                "label": "Permanent Load Summary",
                "columns": [
                    "Dead Load, DL (kN/m)",
                    "Wearing Surface Load, DW (kN/m)",
                    "Secondary Impact Dead Load, SIDL (kN/m)",
                    "Total Load (kN/m)",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },

            "live_load_definitions": {
                "id": "live_load_definitions",
                "label": "Live Load Definitions",
                "columns": [
                    "Vehicle Class",
                    "Impact Factor",
                ],
                "rows": [
                    [EMPTY, EMPTY],
                ],
            },

            "wind_load_parameters": {
                "id": "wind_load_parameters",
                "label": "Wind Load Parameters",
                "columns": [
                    "Basic Wind Speed, Vᵦ (m/s)",
                    "Design Wind Speed at Height z, Vᵤ (m/s)",
                    "Design Wind Pressure at Height z, Pᵤ (N/m²)",
                    "Drag Coefficient, Cᴅ",
                    "Lift Coefficient, Cᴸ",
                    "Gust Factor, G",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },

            "seismic_load_parameters": {
                "id": "seismic_load_parameters",
                "label": "Seismic Load Parameters",
                "columns": [
                    "Zone",
                    "Seismic Zone Factor, Z",
                    "Importance Factor, I",
                    "Spectral Acceleration / g, Sₐ/g",
                    "Horizontal Acceleration Coefficient, Aₕ",
                    "Vertical Acceleration Coefficient, Aᵥ",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },

            "temperature_load_parameters": {
                "id": "temperature_load_parameters",
                "label": "Temperature Load Parameters",
                "columns": [
                    "Maximum Temperature (°C)",
                    "Minimum Temperature (°C)",
                    "Temperature Rise Change, ΔTᵣᵢₛₑ (°C)",
                    "Temperature Fall Change, ΔTfₐₗₗ (°C)",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },

            "load_combinations": {
                "id": "load_combinations",
                "label": "Load Combinations",
                "columns": [
                    "Combination",
                    "Expression",
                ],
                "rows": [
                    [EMPTY, EMPTY],
                ],
            },
        },

        "member_definitions": {
            "id": "member_definitions",
            "label": "Member Definitions",

            "girder_section_properties": {
                "id": "girder_section_properties",
                "label": "Girder Section Properties",
                "columns": [
                    "Girder",
                    "Depth, d (mm)",
                    "Top Flange Width, bfₜₒₚ (mm)",
                    "Bottom Flange Width, bfᵦₒₜ (mm)",
                    "Top Flange Thickness, tfₜₒₚ (mm)",
                    "Bottom Flange Thickness, tfᵦₒₜ (mm)",
                    "Web Thickness, tᵤ (mm)",
                    "Cross-sectional Area, A (mm²)",
                    "Second Moment of Area (z-axis), Iᵤ (mm⁴)",
                    "Cross-section Class",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },

            "cross_bracing_section_properties": {
                "id": "cross_bracing_section_properties",
                "label": "Cross Bracing Section Properties",
                "columns": [
                    "Type",
                    "Section",
                    "Spacing (m)",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY],
                ],
            },

            "end_diaphragm_section_properties": {
                "id": "end_diaphragm_section_properties",
                "label": "End Diaphragm Section Properties",
                "columns": [
                    "Type",
                    "Section",
                ],
                "rows": [
                    [EMPTY, EMPTY],
                ],
            },

            "shear_stud_properties": {
                "id": "shear_stud_properties",
                "label": "Shear Stud Properties",
                "columns": [
                    "Diameter (mm)",
                    "Height (mm)",
                    "Ultimate Tensile Strength, Fᵤ (MPa)",
                    "Yield Strength, Fᵧ (MPa)",
                    "Number per Section",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },

            "deck_slab_properties": {
                "id": "deck_slab_properties",
                "label": "Deck Slab Properties",
                "columns": [
                    "Thickness (mm)",
                    "Top Reinforcement",
                    "Bottom Reinforcement",
                    "Top Cover (mm)",
                    "Bottom Cover (mm)",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },
        },
    },

    "analysis_results": {
        "id": "analysis_results",
        "label": "Analysis Results",

        "load_effects_girder": {
            "id": "load_effects_girder",
            "label": "Load Effects - Girder",

            "bending_moment_envelope": {
                "id": "bending_moment_envelope",
                "label": "Bending Moment Diagram - Envelope",
                "columns": [
                    "Girder",
                    "Maximum Bending Moment, Mₘₐₓ (kNm)",
                    "Minimum Bending Moment, Mₘᵢₙ (kNm)",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY],
                ],
            },

            "shear_force_envelope": {
                "id": "shear_force_envelope",
                "label": "Shear Force Diagram - Envelope",
                "columns": [
                    "Girder",
                    "Maximum Shear Force, Vₘₐₓ (kN)",
                    "Minimum Shear Force, Vₘᵢₙ (kN)",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY],
                ],
            },

            "bending_moment_by_load_case": {
                "id": "bending_moment_by_load_case",
                "label": "Bending Moment - By Load Case",
                "columns": [
                    "Girder",
                    "Dead Load, DL (kNm)",
                    "Wearing Surface, DW (kNm)",
                    "Secondary Impact Dead Load, SIDL (kNm)",
                    "Live Load, LL (kNm)",
                    "Earthquake Load, EL (kNm)",
                    "Wind Load, WL (kNm)",
                    "Temperature Load, TL (kNm)",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },

            "shear_force_by_load_case": {
                "id": "shear_force_by_load_case",
                "label": "Shear Force - By Load Case",
                "columns": [
                    "Girder",
                    "Dead Load, DL (kN)",
                    "Wearing Surface, DW (kN)",
                    "Secondary Impact Dead Load, SIDL (kN)",
                    "Live Load, LL (kN)",
                    "Earthquake Load, EL (kN)",
                    "Wind Load, WL (kN)",
                    "Temperature Load, TL (kN)",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },
        },

        "deflections": {
            "id": "deflections",
            "label": "Deflections",

            "deflection_live_load": {
                "id": "deflection_live_load",
                "label": "Deflection - Live Load",
                "columns": [
                    "Girder",
                    "Deflection due to Live Load, δ_ₗᵢᵥₑ (mm)",
                    "Permissible Limit",
                    "Status",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },

            "deflection_total_load": {
                "id": "deflection_total_load",
                "label": "Deflection - Total Load",
                "columns": [
                    "Girder",
                    "Total Deflection, δₜₒₜₐₗ (mm)",
                    "Permissible Limit",
                    "Status",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },
        },

        "stress_results": {
            "id": "stress_results",
            "label": "Stress Results",

            "stress_steel_service": {
                "id": "stress_steel_service",
                "label": "Stress in Structural Steel - Service",
                "columns": [
                    "Girder",
                    "Compression (MPa)",
                    "Tension (MPa)",
                    "Shear (MPa)",
                    "Allowable",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },

            "stress_concrete_service": {
                "id": "stress_concrete_service",
                "label": "Stress in Concrete Deck - Service",
                "columns": [
                    "Girder",
                    "Stress in Concrete, σc (MPa)",
                    "Allowable Stress (MPa)",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY],
                ],
            },

            "stress_reinf_service": {
                "id": "stress_reinf_service",
                "label": "Stress in Reinforcement - Service",
                "columns": [
                    "Girder",
                    "Stress in Reinforcement, σᵣₑᵢₙf (MPa)",
                    "Allowable Stress (MPa)",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY],
                ],
            },
        },
    },

    "design_results": {
        "id": "design_results",
        "label": "Design Results",

        "uls_checks": {
            "id": "uls_checks",
            "label": "ULS Checks",

            "flexural_resistance_check": {
                "id": "flexural_resistance_check",
                "label": "Flexural Resistance Check",
                "columns": [
                    "Girder",
                    "Ultimate Bending Moment, Mᵤ (kNm)",
                    "Design Bending Moment, Mᵈ (kNm)",
                    "Demand to Capacity Ratio, DCR",
                    "Status",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },

            "shear_resistance_check": {
                "id": "shear_resistance_check",
                "label": "Shear Resistance Check",
                "columns": [
                    "Girder",
                    "Ultimate Shear Force, Vᵤ (kN)",
                    "Design Shear Force, Vᵈ (kN)",
                    "Demand to Capacity Ratio, DCR",
                    "Status",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },

            "bending_shear_interaction_check": {
                "id": "bending_shear_interaction_check",
                "label": "Bending-Shear Interaction Check",
                "columns": [
                    "Girder",
                    "Ultimate Bending Moment, Mᵤ (kNm)",
                    "Reduced Design Bending Resistance, Mᵈᵥ (kNm)",
                    "Demand to Capacity Ratio, DCR",
                    "Clause Reference",
                    "Status",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },

            "lateral_torsional_buckling_check": {
                "id": "lateral_torsional_buckling_check",
                "label": "Lateral Torsional Buckling Check - Construction Stage",
                "columns": [
                    "Girder",
                    "Ultimate Bending Moment, Mᵤ (kNm)",
                    "LTB Design Buckling Resistance, Mᵦ (kNm)",
                    "LTB Reduction Factor, χ_LT",
                    "Non-Dimensional Slenderness, λ̄_LT",
                    "Demand to Capacity Ratio, DCR",
                    "Clause Reference",
                    "Status",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },
        },

        "sls_checks": {
            "id": "sls_checks",
            "label": "SLS Checks",

            "deflection_control_live": {
                "id": "deflection_control_live",
                "label": "Deflection Control - Live Load",
                "columns": [
                    "Girder",
                    "Deflection due to Live Load, δ_ₗᵢᵥₑ (mm)",
                    "Permissible Limit",
                    "Status",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },

            "deflection_control_total": {
                "id": "deflection_control_total",
                "label": "Deflection Control - Total Load",
                "columns": [
                    "Girder",
                    "Total Deflection, δₜₒₜₐₗ (mm)",
                    "Span, L (mm)",
                    "Permissible Limit, L/600 (mm)",
                    "Clause Reference",
                    "Status",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },

            "max_stress_steel": {
                "id": "max_stress_steel",
                "label": "Maximum Stress Limitation - Steel",
                "columns": [
                    "Girder",
                    "Stress in Steel, σₛ (MPa)",
                    "Yield Strength, fyk (MPa)",
                    "Allowable Stress, 0.9·fyk (MPa)",
                    "Clause Reference",
                    "Status",
                ],
                "rows": [
                    ["Girder 1", 180, 350, 315, "IRC 22 Cl. 604.3.1", "PASS"],
                    ["Girder 2", 176, 350, 315, "IRC 22 Cl. 604.3.1", "PASS"],
                    ["Girder 3", 176, 350, 315, "IRC 22 Cl. 604.3.1", "PASS"],
                    ["Girder 4", 180, 350, 315, "IRC 22 Cl. 604.3.1", "PASS"],
                ],
            },

            "max_stress_concrete": {
                "id": "max_stress_concrete",
                "label": "Maximum Stress Limitation - Concrete",
                "columns": [
                    "Girder",
                    "Stress in Concrete, σc (MPa)",
                    "Characteristic Compressive Strength, fck (MPa)",
                    "Allowable Stress, 0.48·fck (MPa)",
                    "Status",
                ],
                "rows": [
                    ["Girder 1", 12.5, 40, 19.2, "PASS"],
                    ["Girder 2", 12.1, 40, 19.2, "PASS"],
                    ["Girder 3", 12.1, 40, 19.2, "PASS"],
                    ["Girder 4", 12.5, 40, 19.2, "PASS"],
                ],
            },

            "max_stress_reinforcement": {
                "id": "max_stress_reinforcement",
                "label": "Maximum Stress Limitation - Reinforcement",
                "columns": [
                    "Girder",
                    "Stress in Reinforcement, σᵣₑᵢₙf (MPa)",
                    "Characteristic Yield Strength, fyk (MPa)",
                    "Allowable Stress, 0.8·fyk (MPa)",
                    "Status",
                ],
                "rows": [
                    ["Girder 1", 220, 500, 400, "PASS"],
                    ["Girder 2", 215, 500, 400, "PASS"],
                    ["Girder 3", 215, 500, 400, "PASS"],
                    ["Girder 4", 220, 500, 400, "PASS"],
                ],
            },
        },

        "fatigue_checks": {
            "id": "fatigue_checks",
            "label": "Fatigue Checks",

            "fatigue_assessment_girder": {
                "id": "fatigue_assessment_girder",
                "label": "Fatigue Assessment - Girder",
                "columns": [
                    "Girder",
                    "Stress Range, Δσ (MPa)",
                    "Fatigue Limit, ffd (MPa)",
                    "Status",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },

            "fatigue_assessment_shear_connectors": {
                "id": "fatigue_assessment_shear_connectors",
                "label": "Fatigue Assessment - Shear Connectors",
                "columns": [
                    "Stud Group",
                    "Shear Stress Range, Δτ (MPa)",
                    "Fatigue Limit for Shear, τfd (MPa)",
                    "Status",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },
        },

        "shear_connector_design": {
            "id": "shear_connector_design",
            "label": "Shear Connector Design",

            "shear_connector_capacity": {
                "id": "shear_connector_capacity",
                "label": "Shear Connector Capacity",
                "columns": [
                    "Girder",
                    "Stud Diameter, d (mm)",
                    "Stud Height, h (mm)",
                    "Ultimate Tensile Strength of Stud, fu (MPa)",
                    "Characteristic Compressive Strength, fck (MPa)",
                    "Modulus of Elasticity of Concrete, Ec (MPa)",
                    "Nominal Capacity per Stud, Qu (kN)",
                    "Design Capacity per Stud, Qd (kN)",
                    "No. of Studs per Section",
                    "Total Design Capacity, ΣQd (kN)",
                    "Clause Reference",
                ],
                "rows": [
                    ["Girder 1", 20, 100, 495, 40, 34000, 98.5, 83.7, 2, 167.4, "IRC 22 Cl. 606.3.1"],
                    ["Girder 2", 20, 100, 495, 40, 34000, 98.5, 83.7, 2, 167.4, "IRC 22 Cl. 606.3.1"],
                    ["Girder 3", 20, 100, 495, 40, 34000, 98.5, 83.7, 2, 167.4, "IRC 22 Cl. 606.3.1"],
                    ["Girder 4", 20, 100, 495, 40, 34000, 98.5, 83.7, 2, 167.4, "IRC 22 Cl. 606.3.1"],
                ],
            },

            "shear_connector_spacing_uls": {
                "id": "shear_connector_spacing_uls",
                "label": "Shear Connector Spacing - ULS Strength",
                "columns": [
                    "Girder",
                    "Design Vertical Shear, VL (kN)",
                    "Total Stud Capacity, ΣQd (kN)",
                    "Spacing from Vertical Shear, SL1 (mm)",
                    "Full Shear Connection Force, H (kN)",
                    "Spacing from Full Shear Force, SL2 (mm)",
                    "Governing ULS Spacing, min(SL1, SL2) (mm)",
                    "Clause Reference",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },

            "shear_connector_spacing_fatigue": {
                "id": "shear_connector_spacing_fatigue",
                "label": "Shear Connector Spacing - Fatigue",
                "columns": [
                    "Girder",
                    "Fatigue Shear Range, Vr (kN)",
                    "Fatigue Capacity per Stud, Qr (kN)",
                    "No. of Studs per Section",
                    "Fatigue Governing Spacing, SR (mm)",
                    "Clause Reference",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },

            "governing_shear_connector_spacing": {
                "id": "governing_shear_connector_spacing",
                "label": "Governing Shear Connector Spacing",
                "columns": [
                    "Girder",
                    "ULS Spacing, SL (mm)",
                    "Fatigue Spacing, SR (mm)",
                    "Governing Spacing, min(SL, SR) (mm)",
                    "Max Permissible — 600 mm",
                    "Max Permissible — 3·t_slab (mm)",
                    "Max Permissible — 4·h_stud (mm)",
                    "Adopted Permissible Limit (mm)",
                    "Status",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },

            "shear_connector_detailing_checks": {
                "id": "shear_connector_detailing_checks",
                "label": "Shear Connector Detailing Checks",
                "columns": [
                    "Girder",
                    "Stud Diameter, d (mm)",
                    "Flange Thickness, tf (mm)",
                    "d ≤ 2·tf Check (mm)",
                    "Stud Height, h (mm)",
                    "h ≥ 4·d Check (mm)",
                    "Longitudinal Edge Distance (mm)",
                    "Min. Edge Distance Required (mm)",
                    "Slab Embedment Above Stud (mm)",
                    "Min. Embedment Required (mm)",
                    "Clause Reference",
                    "Status",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },
        },

        "transverse_and_crack_checks": {
            "id": "transverse_and_crack_checks",
            "label": "Transverse And Crack Checks",

            "transverse_shear_check": {
                "id": "transverse_shear_check",
                "label": "Transverse Shear Check in Concrete Slab",
                "columns": [
                    "Girder",
                    "Design Longitudinal Shear per Unit Length, VL (kN/m)",
                    "Concrete Shear Resistance, 0.9·L·√fck (kN/m)",
                    "Reinforcement Shear Resistance, 0.8·fyk·Ast (kN/m)",
                    "Total Shear Resistance, VRd (kN/m)",
                    "Demand to Capacity Ratio, DCR",
                    "Clause Reference",
                    "Status",
                ],
                "rows": [
                    ["Girder 1", 285, 198, 245, 443, 0.64, "IRC 22 Cl. 606.10", "PASS"],
                    ["Girder 2", 278, 198, 245, 443, 0.63, "IRC 22 Cl. 606.10", "PASS"],
                    ["Girder 3", 278, 198, 245, 443, 0.63, "IRC 22 Cl. 606.10", "PASS"],
                    ["Girder 4", 285, 198, 245, 443, 0.64, "IRC 22 Cl. 606.10", "PASS"],
                ],
            },

            "crack_width_check": {
                "id": "crack_width_check",
                "label": "Crack Width Check",
                "columns": [
                    "Girder",
                    "Calculated Crack Width, wₖ (mm)",
                    "Permissible Crack Width Limit (mm)",
                    "Minimum Reinforcement Area, As,min (mm²)",
                    "Reinforcement Area Provided, As,prov (mm²)",
                    "Bar Diameter, φ (mm)",
                    "Bar Spacing, s (mm)",
                    "Clause Reference",
                    "Status",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },
        },

        "design_summary": {
            "id": "design_summary",
            "label": "Design Summary",

            "design_results_summary": {
                "id": "design_results_summary",
                "label": "Design Results Summary",
                "columns": [
                    "Member",
                    "Check Name",
                    "Demand (Units as applicable)",
                    "Capacity (Units as applicable)",
                    "Demand to Capacity Ratio, DCR",
                    "Status",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },
        },
    },
}
