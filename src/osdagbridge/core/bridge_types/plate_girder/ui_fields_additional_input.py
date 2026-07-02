# Main schema: ADDITIONAL_INPUTS_SCHEMA (bottom of file)

from osdagbridge.core.utils.common import *


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
                    "on_editing_finished": "on_layout_width_changed",
                },
                {
                    "id": KEY_TS_FOOTPATH_THICKNESS,
                    "label": "Footpath Thickness (mm):",
                    "type": TYPE_TEXTBOX,
                    "on_editing_finished": "validate_footpath_thickness",
                },
            ]
        },
    ],
}

_CRASH_BARRIER_TAB_SCHEMA = {
    "id": KEY_MP_CB_TAB,
    "label": "Crash Barrier",
    "label_width": 210,
    "top_margin": 20,
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
                    "on_change_compute": {"function": "compute_crash_barrier_values"},
                }
            ]
        },
        {
            "fields": [
                {
                    "id": KEY_CB_DENSITY,
                    "label": "Material Density (kN/m³):",
                    "type": TYPE_TEXTBOX,
                }
            ]
        },
        {
            "fields": [
                {
                    "id": KEY_CB_WIDTH,
                    "label": "Width (m):",
                    "type": TYPE_TEXTBOX,
                    "on_editing_finished": "on_layout_width_changed",
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
                }
            ]
        },
        {
            "fields": [
                {
                    "id": KEY_CB_LOAD,
                    "label": "Load (kN/m):",
                    "type": TYPE_TEXTBOX,
                    "placeholder": "Enter custom load",
                }
            ]
        },
        {
            "fields": [
                {
                    "id": KEY_CB_POST_SPACING,
                    "label": "Spacing between Posts (m):",
                    "type": TYPE_TEXTBOX,
                }
            ]
        },
    ],
}

_MEDIAN_TAB_SCHEMA = {
    "id": KEY_MD_TAB,
    "label": "Median",
    "label_width": 210,
    "top_margin": 20,
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
                    "on_change_compute": {"function": "compute_median_values"},
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
                    "on_editing_finished": "on_layout_width_changed",
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
                }
            ]
        },
    ],
}

_RAILING_TAB_SCHEMA = {
    "id": KEY_RL_TAB,
    "label": "Railing",
    "label_width": 180,
    "top_margin": 20,
    "rows": [
        {
            "fields": [
                {
                    "id": KEY_RL_TYPE,
                    "label": "Type:",
                    "type": TYPE_COMBOBOX,
                    "choices": VALUES_RAILING_TYPE,
                    "on_change": "on_railing_type_changed",
                    "on_change_compute": {"function": "compute_railing_values"},
                }
            ]
        },
        {
            "fields": [
                {
                    "id": KEY_RL_WIDTH,
                    "label": "Width (m):",
                    "type": TYPE_TEXTBOX,
                    "on_editing_finished": "on_layout_width_changed",
                }
            ]
        },
        {
            "fields": [
                {
                    "id": KEY_RL_HEIGHT,
                    "label": "Height (m):",
                    "type": TYPE_TEXTBOX,
                }
            ]
        },
        {
            "fields": [
                {
                    "id": KEY_RL_LOAD_MODE,
                    "label": "Mode:",
                    "type": TYPE_COMBOBOX,
                    "choices": ["As per IRC 6", "Custom"],
                    "on_change": "on_railing_load_mode_changed",
                },
                {
                    "id": KEY_RL_LOAD_VALUE,
                    "label": "Load (kN/m):",
                    "type": TYPE_TEXTBOX,
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
                    "on_change_compute": {"function": "compute_wearing_course_values"},
                }
            ]
        },
        {
            "fields": [
                {
                    "id": KEY_WC_DENSITY,
                    "label": "Density (kN/m³):",
                    "type": TYPE_TEXTBOX,
                    "enabled": False,
                }
            ]
        },
        {
            "fields": [
                {
                    "id": KEY_WC_THICKNESS,
                    "label": "Thickness (mm):",
                    "type": TYPE_TEXTBOX,
                }
            ]
        },
    ],
}

_LANE_DETAILS_TAB_SCHEMA = {
    "id": KEY_WC_LD_TAB,
    "label": "Lane Details",
    "disable": True,
    "top_margin": 20,
    "rows": [
        {
            "fields": [
                {
                    "id": KEY_WC_LD_LANE_TABLE,
                    "label": "No. of Traffic Lanes:",
                    "type": TYPE_TABLE_WITH_COUNTER,
                    "count_id": KEY_WC_LD_LANE_TABLE_COUNT,
                    "count_choices": [str(i) for i in range(1, 3)],
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

from osdagbridge.desktop.ui.docks.cad_cross_section import CrossSectionCADWidget

TYPICAL_SECTION_SCHEMA = {
    "id": KEY_TS_TAB,
    "layout": {"type": "panel"},

    # ── Header: rendered above the scrollable body, no card title ─────────────
    "header": {
        "rows": [
            {
                "fields": [
                    {
                        "id":           KEY_TS_CAD_PREVIEW,
                        "type":         TYPE_DIRECT_WIDGET,
                        "widget_class": CrossSectionCADWidget,
                        "widget_props": {
                            "scale_factor":         0.65,
                            "minimum_height":       200,
                            "wrap_in_scroll":       True,
                            "container_min_height": 280,
                            "container_max_height": 380,
                            "container_margins":    [5, 5, 5, 5],
                            "container_style":      "QWidget { background: transparent; border: 1px solid #b0b0b0; border-radius: 8px; }",
                        },
                    },
                ]
            }
        ],
    },

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
                        "on_editing_finished": "on_no_of_girders_changed",
                    },
                    {
                        "id": KEY_TS_GIRDER_SPACING,
                        "label": "Girder Spacing (m):",
                        "type": TYPE_TEXTBOX,
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
                        "read_only": True,
                    },
                    {
                        "id": KEY_TS_OVERALL_WIDTH,
                        "label": "Overall Bridge Width (m):",
                        "type": TYPE_TEXTBOX,
                        "read_only": True,
                    },
                ],
            },
            {
                "fields": [
                    {},  # empty first field — placeholder for left column
                    {
                        "type": TYPE_NOTICE,
                        "id": "layout_notice",
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
            "title":   "Permanent Loads",
            "text":    (
                "Dead loads are divided into the following categories:\n\n"
                "SW — Self-weight of the girder. The self-weight modification factor entered by the user is multiplied with this case to account for connections and accessories not explicitly modelled.\n"
                "DC — Weight of structural steel components other than the girder, including cross bracing and end diaphragms.\n"
                "DD — Weight of the concrete deck slab.\n"
                "DW — Weight of the wearing course (surfacing) applied on the deck.\n"
                "SIDL — Superimposed Dead Load, comprising crash barriers, median, and railings.\n\n"
                "All load magnitudes are computed internally from member dimensions and material densities. The self-weight modification factor (SW) is the only user-controlled parameter for this load group."
            ),
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
                        # Own key (not the vehicle KEY_LL_IRC_CLASS_SV) so the
                        # Class SV braking opt-in is independent of vehicle selection.
                        "id":              KEY_BL_IRC_CLASS_SV,
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
            "title":   "Live Load (LL)",
            "text": (
                "IRC Vehicles:\n"
                "Live load considers standard IRC 6 vehicle classes: Class A, Class 70R (Wheeled, Tracked, Bogie), Class AA (Wheeled, Tracked), Class SV (Special Vehicle), and Fatigue vehicle. Only checked vehicles are included in the analysis.\n\n"
                "Braking Load (IRC 6 Cl. 211.2):\n"
                "Braking forces are derived from the live load. For single- or two-lane bridges: 20% of the first train of load plus 10% of succeeding trains in one lane.\nFor bridges with more than two lanes: as above for the first two lanes, plus 5% for each additional lane.\nClass SV does not require a braking load by default, but a checkbox is provided if the user wishes to include it.\n\n"
                "Braking Load Eccentricity:\n"
                "As per IRC 6, braking load acts as a horizontal longitudinal force applied at 1.2 m above the top of the deck surface.\n\n"
                "Footpath Pressure:\n"
                "Footpath live load is applied as a uniform pressure per IRC 6. The default value follows the code; the user can switch to 'User-defined' to enter a custom value."
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
            "title":   "Seismic / Earthquake Load (EL)",
            "text":    (
                "Seismic zone is auto-filled from the project location and determines the zone factor (Z) per IRC 6.\n\n"
                "Spectral acceleration coefficient (Sa/g) is taken from IRC 6 response spectra and depends on the soil type and the fundamental time period (T) of the structure.\n\n"
                "Seismic coefficients:\n"
                "Ah = (Z / 2) x (I / R) x (Sa/g)\n"
                "Av = (2/3) x Ah\n"
                "where Z = zone factor, I = importance factor, R = response reduction factor, and the damping percentage governs the Sa/g value. All calculations follow IRC 6 seismic provisions."
            ),
            "stretch": True,
        },
    ],
}

_WIND_LOAD_TAB_SCHEMA = {
    "id":     KEY_WL_TAB,
    "scroll": False,
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
                {
                    "fields": [{
                        "id": KEY_WL_BASIC_WIND_SPEED,
                        "label": "Basic Wind Speed, V<sub>b</sub> (m/s)",
                        "type": TYPE_TEXTBOX,
                        "read_only": True,
                        "bind": "basic_wind_speed_input",
                        "on_change_compute": {"function": "_compute_wind_values"}
                    }]
                },
                {
                    "fields": [{
                        "id": KEY_WL_AVG_EXPOSED_HEIGHT,
                        "label": "Average Exposed Height, H (m)",
                        "type": TYPE_TEXTBOX,
                        "placeholder": "10",
                        "default": "10",
                        "bind": "avg_exposed_height_input",
                        "on_change_compute": {"function": "_compute_wind_values"}
                    }]
                },
                {
                    "fields": [{
                        "id": KEY_WL_TERRAIN_TYPE,
                        "label": "Type of Terrain",
                        "type": TYPE_COMBOBOX,
                        "choices": ["Plain Terrain", "Terrain with Obstructions"],
                        "default": "Plain Terrain",
                        "bind": "terrain_type_combo",
                        "on_change_compute": {"function": "_compute_wind_values"}
                    }]
                },
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
                # {"fields": [{"id": KEY_WL_TRANSVERSE_WIND_FORCE,   "label": "Transverse Wind Force, F<sub>T</sub> (N)",                       "type": TYPE_TEXTBOX, "read_only": True, "bind": "transverse_wind_force_input"}]},
                # {"fields": [{"id": KEY_WL_LONGITUDINAL_WIND_FORCE, "label": "Longitudinal Wind Force, F<sub>L</sub> (N)",                     "type": TYPE_TEXTBOX, "read_only": True, "bind": "longitudinal_wind_force_input"}]},
                # {"fields": [{"id": KEY_WL_VERTICAL_WIND_FORCE,     "label": "Vertical Wind Force, F<sub>V</sub> (N)",                         "type": TYPE_TEXTBOX, "read_only": True, "bind": "vertical_wind_force_input"}]},
                # {"fields": [{"id": KEY_WL_TRANSVERSE_WIND_LL,      "label": "Transverse Wind Force on Live Load, F<sub>TLL</sub> (N)",        "type": TYPE_TEXTBOX, "read_only": True, "bind": "transverse_wind_ll_input"}]},
                # {"fields": [{"id": KEY_WL_LONGITUDINAL_WIND_LL,    "label": "Longitudinal Wind Force on Live Load, F<sub>LLL</sub> (N)", "type": TYPE_TEXTBOX, "read_only": True, "bind": "longitudinal_wind_ll_input"}]},
                # Commented the additional fields here to stop render in 'Computed Values' .
            ],
        },

        # ── Column 1: Description ──────────────────────────────────────────
        {
            "column":  1,
            "type":    TYPE_DESCRIPTION,
            "title":   "Wind Load (WL)",
            "text":    (
                "Basic wind speed is auto-filled from the project location.\n\n"
                "Hourly mean wind speed (Vz) and design wind pressure (Pz) are computed from the basic wind speed, average exposed height (H), terrain type, and site topography per IRC 6.\n\n"
                "Wind forces computed per IRC 6 include:\n"
                "- Transverse wind force on the structure\n"
                "- Longitudinal wind force (typically 25% of transverse)\n"
                "- Vertical (upward) wind force on the deck\n"
                "- Transverse and longitudinal wind forces due to live load\n\n"
                "These forces use the gust factor (G), drag coefficient (CD), lift coefficient (CL), superstructure elevation area, plan area, and exposed frontal area of live load. They are applied at the specified eccentricity or as required by IRC 6."
            ),
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
                {
                    "fields": [{
                        "id": KEY_TL_HIGHEST_MAX_TEMP,
                        "label": "Highest Maximum Air Temperature (°C)",
                        "type": TYPE_TEXTBOX,
                        "placeholder": "From Project Location",
                        "read_only": True,
                        "bind": "highest_max_temp_input",
                        "on_change_compute": {"function": "_compute_temperature_values"}
                    }]
                },
                {
                    "fields": [{
                        "id": KEY_TL_LOWEST_MIN_TEMP,
                        "label": "Lowest Minimum Air Temperature (°C)",
                        "type": TYPE_TEXTBOX,
                        "placeholder": "From Project Location",
                        "read_only": True,
                        "bind": "lowest_min_temp_input",
                        "on_change_compute": {"function": "_compute_temperature_values"}
                    }]
                },
                {"fields": [{"id": KEY_TL_THERMAL_COEFF_STEEL, "label": "Coefficient of Thermal Expansion for Steel (1/°C)",       "type": TYPE_TEXTBOX, "read_only": True, "placeholder": "e.g. 11.7e-6",        "bind": "thermal_coeff_steel_input"}]},
                {"fields": [{"id": KEY_TL_THERMAL_COEFF_RCC,   "label": "Coefficient of Thermal Expansion for RCC (1/°C)",         "type": TYPE_TEXTBOX, "read_only": True, "placeholder": "e.g. 11.7e-6",        "bind": "thermal_coeff_rcc_input"}]},
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
            "title":   "Temperature Load (TL)",
            "text":    (
                "Highest maximum and lowest minimum air shade temperatures are auto-filled from the project location (per IRC 6 Annex B meteorological data).<br><br>"
                "<b>Coefficient of thermal expansion (α):</b><br>"
                "Governs the unit change in length per degree Celsius. IRC 6 Cl. 215 specifies 12 × 10⁻⁶ /°C for steel and 12 × 10⁻⁶ /°C for RCC; values may be revised if site-specific material data is available. Both coefficients are user-editable.<br><br>"
                "<b>Range of effective bridge temperature (EBT):</b><br>"
                "The effective bridge temperature is the uniform temperature through the depth of the bridge cross-section at any instant. The minimum and maximum EBT values are derived from the air shade temperatures using IRC 6 Cl. 215. These are computed automatically and shown read-only.<br><br>"
                "<b>Temperature for design:</b><br>"
                "• Temperature Rise = Maximum EBT − Mean temperature<br>"
                "• Temperature Fall = Mean temperature − Minimum EBT<br>"
                "The Mean temperature is the midpoint of min and max air shade temperatures. The rise and fall values are used to compute thermal expansion and contraction forces, and longitudinal effects throughout the analysis."
            ),
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
    "scroll": False,
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
            "rows": [
                        {
                            "fields": [{
                                "id": "irc6_default_combinations",
                                "type": TYPE_LOAD_COMBINATION,
                            }]
                        }
                    ],
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
            "title":   "Load Combinations (IRC 6)",
            "text":    (
                "Load combinations are formed per IRC 6 Table B.1. The following load cases are considered:\n"
                "SW: Self-weight of steel girder\n"
                "DC: Weight of structural steel components other than the girder, including cross bracing and end diaphragms\n"
                "DD: Deck weight\n"
                "DW: Wearing course\n"
                "SIDL: Crash barriers, median, railing\n"
                "LL: Live load\n"
                "WL: Wind load\n"
                "EL: Seismic / earthquake load\n"
                "TL: Temperature load\n\n"
                "IRC 6 combination types:\n"
                "- Basic combination\n"
                "- Accidental combination\n"
                "- Seismic combination\n"
                "- Frequent combination\n"
                "- Rare combination\n"
                "- Quasi-permanent combination\n\n"
                "Custom load combinations with user-defined partial safety factors can also be added."
            ),
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
                        "label":   "Include default",
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
            "title":  "Construction Stages",
            "text":   (
                "When included ('Yes'), the analysis accounts for three stages.\nIn Stage 1, the steel girder carries its self-weight alone.\nIn Stage 2, the wet concrete deck load (DD) and the weight of other structural steel components act on the bare steel section before composite action is activated.\nIn Stage 3, composite action is fully active, and all remaining loads (superimposed dead load, live load, wind load, seismic load, and temperature load) are applied to the composite section.\nStages 1 and 2 are critical for lateral-torsional buckling (LTB) checks, as the compression flange is unrestrained until the deck provides lateral support.\n\n"
                "When 'No' is selected, only the final composite state is checked and no separate construction-stage verification is performed."
            ),
            "stretch": True,
        },
    ],
}

DESIGN_OPTIONS_CONT_SCHEMA = {
    "id": KEY_DO_TAB,
    "layout": {
        "type":          "columns",
        "columns":       2,
        "column_widths": [3, 2],
    },
    "sections": [

        # ──────────────────── Partial Factor + Description (grid row 0) ────────────────────
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

        # col 1 paired with Partial Factor, spans 3 rows (Partial Factor / Resistance to Fatigue / Deflection Control)
        {
            "column":   1,
            "type":     TYPE_DESCRIPTION,
            "title":    "Design Options",
            "row_span": 3,
            "text":   (
                    "Deflection limit considered for live load case is L/800 and for DL+LL case is L/600 per IRC 6."
            ),
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
                    "fields": [{
                        "id":           KEY_DO_CAMBER,
                        "label":        "Camber (m)",
                        "type":         TYPE_MODE_LINE,
                        "mode_choices": ["Default", "Custom"],
                        "bind_mode":    "camber_mode_combo",
                        "bind_value":   "camber_value_input",
                        "placeholder":  "0 - 4",
                    }]
                },
            ],
        },

        # ──────────────────── Limit States ────────────────────
        {
            "column":   0,
            "col_span": 2,
            "title":    "Limit States",
            "checkbox_groups": [
                {
                    "title":           "Ultimate Limit States",
                    "bind":            "ultimate_checkboxes",
                    "default_checked": True,
                    "items": [
                        {"id": KEY_DO_ULS_BENDING,    "label": "Bending Resistance",                    "type": TYPE_CHECKBOX},
                        {"id": KEY_DO_ULS_SHEAR,      "label": "Resistance to Vertical Shear",          "type": TYPE_CHECKBOX},
                        {"id": KEY_DO_ULS_LTB,        "label": "Resistance to Lateral-torsional Buckling", "type": TYPE_CHECKBOX},
                        {"id": KEY_DO_ULS_TRANSVERSE,  "label": "Resistance to Transverse force",       "type": TYPE_CHECKBOX},
                        {"id": KEY_DO_ULS_LONG_SHEAR,  "label": "Resistance to Longitudinal Shear",     "type": TYPE_CHECKBOX},
                        {"id": KEY_DO_ULS_FATIGUE,     "label": "Resistance to Fatigue",                "type": TYPE_CHECKBOX},
                    ],
                },
                {
                    
                    "title":           "Serviceability Limit States",
                    "default_checked": True,
                    "items": [
                        {"id": KEY_DO_SLS_STRESS,      "label": "Stress Limitation",        "type": TYPE_CHECKBOX},
                        {"id": KEY_DO_SLS_LONG_SHEAR,  "label": "Longitudinal Shear (SLS)", "type": TYPE_CHECKBOX},
                        {"id": KEY_DO_SLS_DEFLECTION,  "label": "Deflection Control",       "type": TYPE_CHECKBOX},
                        {"id": KEY_DO_SLS_CRACK_WIDTH,  "label": "Crack Width Check",       "type": TYPE_CHECKBOX},
                    ],
                },
            ],
        }
    ]
}


from osdagbridge.desktop.ui.dialogs.additional_input.drawings.cad_preview_widget import CadPreviewWidget
from osdagbridge.desktop.ui.dialogs.additional_input.ui_builder._segment_table_widget import SegmentTableWidget
from osdagbridge.desktop.ui.dialogs.additional_input.drawings.rolled_section_preview import RolledSectionPreview

END_CONNECTORS = [

    #------Origin------------------Target-----------------------Callback---------------------- 
    
    # Update Select Girder (GD sub-tab) Combobox (Target) on change no of girder (Origin)
    (KEY_TS_NO_OF_GIRDERS,     KEY_MP_GD_SELECT_GIRDER,    "_on_girder_count_refreshed"),
    
    # Update Apply buttons visibility
    (KEY_MP_GD_SELECT_GIRDER,  KEY_MP_GD_APPLY_EXTERIOR,   "_update_apply_button_visibility"),
    (KEY_MP_GD_SELECT_GIRDER,  KEY_MP_GD_APPLY_INTERIOR,   "_update_apply_button_visibility"),
    
    # Update Member ID (Target) on interaction with Segment Table (Origin)
    (KEY_MP_GD_SEGMENT_TABLE,  KEY_MP_GD_MEMBER_ID,        "_on_segment_members_refreshed"),

    # Update/load data from dict for related girder in segment table
    (KEY_MP_GD_SELECT_GIRDER,  KEY_MP_GD_SEGMENT_TABLE,    "_on_girder_segments_load"),

    # Populate Stiffener Details member ID combo from all girder segments
    (KEY_MP_GD_SELECT_GIRDER,  KEY_MP_STIFFENER_SELECT_MEMBER_ID, "_on_stiffener_member_ids_refreshed"),
    (KEY_MP_GD_SEGMENT_TABLE,  KEY_MP_STIFFENER_SELECT_MEMBER_ID, "_on_stiffener_member_ids_refreshed"),

    # Show/hide bearing stiffener fields based on whether selected member is first or last in its girder
    (KEY_MP_STIFFENER_SELECT_MEMBER_ID, KEY_MP_STIFFENER_NO_BEARING_STIFFENERS, "_on_stiffener_member_bearing_changed"),

    # Save old member data and load new member data when member ID selection changes
    (KEY_MP_STIFFENER_SELECT_MEMBER_ID, KEY_MP_STIFFENER_DESIGN_METHOD, "_on_stiffener_member_load"),

    # On change of any stiffener input field — save all stiffener fields for the
    # current member so the selection reaches the backend / Steel Design table.
    (KEY_MP_STIFFENER_NO_BEARING_STIFFENERS,  KEY_MP_STIFFENER_SELECT_MEMBER_ID, "_save_stiffener_field_connector"),
    (KEY_MP_STIFFENER_SPACING,                KEY_MP_STIFFENER_SELECT_MEMBER_ID, "_save_stiffener_field_connector"),
    (KEY_MP_STIFFENER_BEARING_THICKNESS,      KEY_MP_STIFFENER_SELECT_MEMBER_ID, "_save_stiffener_field_connector"),
    (KEY_MP_STIFFENER_BEARING_OUTSTAND,       KEY_MP_STIFFENER_SELECT_MEMBER_ID, "_save_stiffener_field_connector"),
    (KEY_MP_STIFFENER_INTERMEDIATE,           KEY_MP_STIFFENER_SELECT_MEMBER_ID, "_save_stiffener_field_connector"),
    (KEY_MP_STIFFENER_INTERMEDIATE_SPACING,   KEY_MP_STIFFENER_SELECT_MEMBER_ID, "_save_stiffener_field_connector"),
    (KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS, KEY_MP_STIFFENER_SELECT_MEMBER_ID, "_save_stiffener_field_connector"),
    (KEY_MP_STIFFENER_INTERMEDIATE_OUTSTAND,  KEY_MP_STIFFENER_SELECT_MEMBER_ID, "_save_stiffener_field_connector"),
    (KEY_MP_STIFFENER_LONGITUDINAL,           KEY_MP_STIFFENER_SELECT_MEMBER_ID, "_save_stiffener_field_connector"),
    (KEY_MP_STIFFENER_LONGITUDINAL_THICKNESS, KEY_MP_STIFFENER_SELECT_MEMBER_ID, "_save_stiffener_field_connector"),
    (KEY_MP_STIFFENER_DESIGN_METHOD,          KEY_MP_STIFFENER_SELECT_MEMBER_ID, "_save_stiffener_field_connector"),

    # On change of member_id the fields below will be changed according to Girder & Member
    (KEY_MP_GD_MEMBER_ID,      KEY_MP_GD_MEMBER_ID,        "_on_member_id_load"),

    # On change origin fields save the data using dynamic keys
    (KEY_MP_GIRDER_TYPE,                    KEY_MP_GD_MEMBER_ID, "_save_member_fields_connector"),
    (KEY_MP_GIRDER_SYMMETRY,                KEY_MP_GD_MEMBER_ID, "_save_member_fields_connector"),
    (KEY_MP_GD_SUPPORT_TYPE,                KEY_MP_GD_MEMBER_ID, "_save_member_fields_connector"),
    (KEY_MP_GD_SUPPORT_WIDTH,               KEY_MP_GD_MEMBER_ID, "_save_member_fields_connector"),
    (KEY_MP_GIRDER_TORSIONAL_RESTRAINT,     KEY_MP_GD_MEMBER_ID, "_save_member_fields_connector"),
    (KEY_MP_GIRDER_WARPING_RESTRAINT,       KEY_MP_GD_MEMBER_ID, "_save_member_fields_connector"),
    (KEY_MP_GIRDER_WEB_TYPE,                KEY_MP_GD_MEMBER_ID, "_save_member_fields_connector"),
    (KEY_MP_GIRDER_IS_SECTION,              KEY_MP_GD_MEMBER_ID, "_save_member_fields_connector"),

    # Adaptive fields — Custom mode (QLineEdit/QComboBox) wired via wire_end_connectors;
    # Optimized mode (TYPE_BOUND_BTN) save is handled directly by _on_bounds_accepted.
    (KEY_MP_GIRDER_DEPTH,                   KEY_MP_GD_MEMBER_ID, "_save_member_fields_connector"),
    (KEY_MP_GIRDER_TOP_FLANGE_WIDTH,        KEY_MP_GD_MEMBER_ID, "_save_member_fields_connector"),
    (KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,    KEY_MP_GD_MEMBER_ID, "_save_member_fields_connector"),
    (KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH,     KEY_MP_GD_MEMBER_ID, "_save_member_fields_connector"),
    (KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS, KEY_MP_GD_MEMBER_ID, "_save_member_fields_connector"),
    (KEY_MP_GIRDER_WEB_THICKNESS,           KEY_MP_GD_MEMBER_ID, "_save_member_fields_connector"),

     # Update Select Girder (End Diaphragm) Combobox (Target) on change no of girder (Origin)
    (KEY_TS_NO_OF_GIRDERS,     KEY_MP_ED_SELECT_GIRDERS,   "_on_ed_girder_count_refreshed"),

    # Update Member ID (End Diaphragm) Textbox (Target) on change Select Girders (Origin)
    (KEY_MP_ED_SELECT_GIRDERS, KEY_MP_ED_MEMBER_ID, "_on_ed_member_id_refreshed"),

    # On change of any ED input field — save all ED fields under current pair's dynamic keys
    (KEY_MP_ED_TYPE,                        KEY_MP_ED_SELECT_GIRDERS, "_save_ed_pair_connector"),
    (KEY_MP_ED_BRACING_TYPE,                KEY_MP_ED_SELECT_GIRDERS, "_save_ed_pair_connector"),
    (KEY_MP_ED_BRACING_CONNECTION,          KEY_MP_ED_SELECT_GIRDERS, "_save_ed_pair_connector"),
    (KEY_MP_ED_BRACING_SECTION,             KEY_MP_ED_SELECT_GIRDERS, "_save_ed_pair_connector"),
    (KEY_MP_ED_BRACING_SECTION_DESIGNATION, KEY_MP_ED_SELECT_GIRDERS, "_save_ed_pair_connector"),
    (KEY_MP_ED_TOP_CHORD_SECTION_TYPE,      KEY_MP_ED_SELECT_GIRDERS, "_save_ed_pair_connector"),
    (KEY_MP_ED_TOP_CHORD_SECTION_DESIG,     KEY_MP_ED_SELECT_GIRDERS, "_save_ed_pair_connector"),
    (KEY_MP_ED_BOTTOM_CHORD_SECTION_TYPE,   KEY_MP_ED_SELECT_GIRDERS, "_save_ed_pair_connector"),
    (KEY_MP_ED_BOTTOM_CHORD_SECTION_DESIG,  KEY_MP_ED_SELECT_GIRDERS, "_save_ed_pair_connector"),
    (KEY_MP_ED_IS_SECTION,                  KEY_MP_ED_SELECT_GIRDERS, "_save_ed_pair_connector"),
    (KEY_MP_ED_SYMMETRY,                    KEY_MP_ED_SELECT_GIRDERS, "_save_ed_pair_connector"),
    (KEY_MP_ED_WEB_THICKNESS,               KEY_MP_ED_SELECT_GIRDERS, "_save_ed_pair_connector"),
    (KEY_MP_ED_TOP_FLANGE_WIDTH,            KEY_MP_ED_SELECT_GIRDERS, "_save_ed_pair_connector"),
    (KEY_MP_ED_TOP_FLANGE_THICKNESS,        KEY_MP_ED_SELECT_GIRDERS, "_save_ed_pair_connector"),
    (KEY_MP_ED_BOTTOM_FLANGE_WIDTH,         KEY_MP_ED_SELECT_GIRDERS, "_save_ed_pair_connector"),
    (KEY_MP_ED_BOTTOM_FLANGE_THICKNESS,     KEY_MP_ED_SELECT_GIRDERS, "_save_ed_pair_connector"),
    # KEY_MP_ED_TOTAL_DEPTH is a QLineEdit — wired via editingFinished, handled by connector
    (KEY_MP_ED_TOTAL_DEPTH,                 KEY_MP_ED_SELECT_GIRDERS, "_save_ed_pair_connector"),
    # Checkboxes — now supported by wire_end_connectors via stateChanged
    (KEY_MP_ED_TOP_CHORD,                   KEY_MP_ED_SELECT_GIRDERS, "_save_ed_pair_connector"),
    (KEY_MP_ED_BOTTOM_CHORD,                KEY_MP_ED_SELECT_GIRDERS, "_save_ed_pair_connector"),

    # ── Cross Bracing connectors ──────────────────────────────────────────────

    # Repopulate Select Girders combo when No. of Girders changes
    (KEY_TS_NO_OF_GIRDERS,           KEY_MP_CB_SELECT_GIRDERS, "_on_cb_girder_count_refreshed"),

    # Update Member ID when Select Girders or No. of Cross Bracings changes
    (KEY_MP_CB_SELECT_GIRDERS,       KEY_MP_CB_MEMBER_ID,      "_on_cb_member_id_refreshed"),
    (KEY_MP_CB_NO_OF_CROSS_BRACINGS, KEY_MP_CB_MEMBER_ID,      "_on_cb_member_id_refreshed"),

    # Compute Spacing = span / (no_of_cross_bracings + 1)
    (KEY_MP_CB_NO_OF_CROSS_BRACINGS, KEY_MP_CB_SPACING,        "_on_cb_spacing_computed"),

    # Bracing layout logic — type, top/bottom chord all route to one handler
    (KEY_MP_CB_TYPE,         KEY_MP_CB_SELECT_GIRDERS, "_on_cb_bracing_layout_changed"),
    (KEY_MP_CB_TOP_CHORD,    KEY_MP_CB_SELECT_GIRDERS, "_on_cb_bracing_layout_changed"),
    (KEY_MP_CB_BOTTOM_CHORD, KEY_MP_CB_SELECT_GIRDERS, "_on_cb_bracing_layout_changed"),

    # Section type → repopulate designation combo
    (KEY_MP_CB_BRACING_SECTION_TYPE,      KEY_MP_CB_BRACING_SECTION_DESIGNATION, "_on_cb_bracing_section_type_changed"),
    (KEY_MP_CB_TOP_CHORD_SECTION_TYPE,    KEY_MP_CB_TOP_CHORD_SECTION_DESIG,     "_on_cb_top_chord_section_type_changed"),
    (KEY_MP_CB_BOTTOM_CHORD_SECTION_TYPE, KEY_MP_CB_BOTTOM_CHORD_SECTION_DESIG,  "_on_cb_bottom_chord_section_type_changed"),

    # Designation → update section CAD preview
    (KEY_MP_CB_BRACING_SECTION_DESIGNATION, KEY_MP_CB_BRACING_PREVIEW,      "_on_cb_bracing_preview_changed"),
    (KEY_MP_CB_TOP_CHORD_SECTION_DESIG,     KEY_MP_CB_TOP_CHORD_PREVIEW,    "_on_cb_top_chord_preview_changed"),
    (KEY_MP_CB_BOTTOM_CHORD_SECTION_DESIG,  KEY_MP_CB_BOTTOM_CHORD_PREVIEW, "_on_cb_bottom_chord_preview_changed"),

    # On change of any CB input field — save all CB fields under current pair's dynamic key
    (KEY_MP_CB_TYPE,                         KEY_MP_CB_SELECT_GIRDERS, "_save_cb_pair_connector"),
    (KEY_MP_CB_BRACING_CONNECTION,           KEY_MP_CB_SELECT_GIRDERS, "_save_cb_pair_connector"),
    (KEY_MP_CB_TOP_CHORD,                    KEY_MP_CB_SELECT_GIRDERS, "_save_cb_pair_connector"),
    (KEY_MP_CB_BOTTOM_CHORD,                 KEY_MP_CB_SELECT_GIRDERS, "_save_cb_pair_connector"),
    (KEY_MP_CB_BRACING_SECTION_TYPE,         KEY_MP_CB_SELECT_GIRDERS, "_save_cb_pair_connector"),
    (KEY_MP_CB_BRACING_SECTION_DESIGNATION,  KEY_MP_CB_SELECT_GIRDERS, "_save_cb_pair_connector"),
    (KEY_MP_CB_TOP_CHORD_SECTION_TYPE,       KEY_MP_CB_SELECT_GIRDERS, "_save_cb_pair_connector"),
    (KEY_MP_CB_TOP_CHORD_SECTION_DESIG,      KEY_MP_CB_SELECT_GIRDERS, "_save_cb_pair_connector"),
    (KEY_MP_CB_BOTTOM_CHORD_SECTION_TYPE,    KEY_MP_CB_SELECT_GIRDERS, "_save_cb_pair_connector"),
    (KEY_MP_CB_BOTTOM_CHORD_SECTION_DESIG,   KEY_MP_CB_SELECT_GIRDERS, "_save_cb_pair_connector"),
    (KEY_MP_CB_NO_OF_CROSS_BRACINGS,         KEY_MP_CB_SELECT_GIRDERS, "_save_cb_pair_connector"),

]

GIRDER_DETAILS_SCHEMA = {
    "id": KEY_MP_GD_TAB,
    "layout": {
        "type":          "columns",
        "columns":       2,
        "column_widths": [1, 1],
    },
    "sections": [

        # ── CAD preview — full width (col 0, spans both columns) ──────────────
        {
            "column":   0,
            "col_span": 2,
            "title":    "",
            "rows": [
                {
                    "fields": [{
                        "id":           KEY_MP_GD_CAD_PREVIEW,
                        "type":         TYPE_DIRECT_WIDGET,
                        "widget_class": CadPreviewWidget,
                    }]
                },
            ],
        },

        # ── Girder Overview — col 0 ───────────────────────────────────────────
        {
            "column":  0,
            "title":   "Girder Overview",
            "rows": [
                {
                    "fields": [{
                        "id":      KEY_MP_GD_SELECT_GIRDER,
                        "label":   "Select Girder:",
                        "type":    TYPE_COMBOBOX,
                        "choices": [],
                    }]
                },
                {
                    "fields": [{
                        "id":        KEY_MP_GD_TOTAL_SPAN,
                        "label":     "Total Span (m):",
                        "type":      TYPE_TEXTBOX,
                        "read_only": True,
                    }]
                },
                {
                    "fields": [{
                        "id":       KEY_MP_GD_APPLY_EXTERIOR,
                        "type":     TYPE_BUTTON,
                        "text":     "Apply changes to exterior girders",
                        "on_click": "_on_apply_exterior_clicked",
                    }]
                },
                {
                    "fields": [{
                        "id":       KEY_MP_GD_APPLY_INTERIOR,
                        "type":     TYPE_BUTTON,
                        "text":     "Apply changes to interior girders",
                        "on_click": "_on_apply_interior_clicked",
                    }]
                },
            ],
        },

        # ── Segment Table — col 1 ─────────────────────────────────────────────
        {
            "column": 1,
            "title":  "",
            "rows": [
                {
                    "fields": [{
                        "id":                KEY_MP_GD_SEGMENT_TABLE,
                        "type":              TYPE_DIRECT_WIDGET,
                        "widget_class":      SegmentTableWidget,
                        "on_row_select":     "_on_segment_selected",
                        "on_data_changed":   "_on_segment_data_changed",
                    }]
                },
            ],
        },

        # ── Section Inputs — col 0 (spans 2 grid rows: preview + properties) ───
        {
            "column":   0,
            "row_span": 2,
            "title":    "Section Inputs",
            "rows": [

                # Member ID selector
                {
                    "fields": [{
                        "id":        KEY_MP_GD_MEMBER_ID,
                        "label":     "Member ID:",
                        "type":      TYPE_COMBOBOX,
                        "choices":   [],
                    }]
                },

                # Type (Welded / Rolled)
                {
                    "fields": [{
                        "id":        KEY_MP_GIRDER_TYPE,
                        "label":     "Type:",
                        "type":      TYPE_COMBOBOX,
                        "choices":   VALUES_GIRDER_TYPE,
                        "on_change": "_on_girder_type_changed",
                    }]
                },

                # Symmetry — welded only
                {
                    "fields": [{
                        "id":      KEY_MP_GIRDER_SYMMETRY,
                        "label":   "Symmetry:",
                        "type":    TYPE_COMBOBOX,
                        "choices": VALUES_GIRDER_SYMMETRY,
                        "on_change": "_on_symmetry_changed",
                    }]
                },

                # Welded dimensions
                {
                    "fields": [{
                        "id":         KEY_MP_GIRDER_DEPTH,
                        "label":      "Total Depth, d (mm):",
                        "type":       TYPE_ADAPTIVE,
                        "controller": KEY_DESIGN_MODE,
                        "modes": {
                            "Optimized": {
                                "type":           TYPE_BOUND_BTN,
                                "text":           "Set Bounds",
                                "lower_limit":    200.0,
                                "upper_limit":    2000.0,
                                "with_increment": True,
                                "on_accepted":    "_on_bounds_accepted",
                            },
                            "Custom": {
                                "type":              TYPE_TEXTBOX,
                                "placeholder":       "",
                                "on_editing_finished": "_update_section_drawing",
                                "on_change_compute": {"function": "_compute_welded_section_properties"},
                            },
                        },
                    }],
                },
                {
                    "fields": [{
                        "id":         KEY_MP_GIRDER_TOP_FLANGE_WIDTH,
                        "label":      "Width of Top Flange, t<sub>fw</sub> (mm):",
                        "type":       TYPE_ADAPTIVE,
                        "controller": KEY_DESIGN_MODE,
                        "modes": {
                            "Optimized": {
                                "type":           TYPE_BOUND_BTN,
                                "text":           "Set Bounds",
                                "lower_limit":    100.0,
                                "upper_limit":    1000.0,
                                "with_increment": True,
                                "on_accepted": "_on_bounds_accepted",
                            },
                            "Custom": {
                                "type":              TYPE_TEXTBOX,
                                "placeholder":       "",
                                "on_editing_finished": "_on_top_flange_changed",
                                "on_change_compute": {"function": "_compute_welded_section_properties"},
                            },
                        },
                    }],
                },
                {
                    "fields": [{
                        "id":         KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
                        "label":      "Top Flange Thickness, t<sub>ft</sub> (mm):",
                        "type":       TYPE_ADAPTIVE,
                        "controller": KEY_DESIGN_MODE,
                        "modes": {
                            "Optimized": {
                                "type":            TYPE_ALL_CUSTOM,
                                "on_selected":     "_on_all_custom_selected",
                            },
                            "Custom": {
                                "type":              TYPE_COMBOBOX,
                                "choices":           [str(v) for v in SAIL_APPROVED_THICKNESS_VALUES],
                                "on_change":         "_on_top_flange_changed",
                                "on_change_compute": {"function": "_compute_welded_section_properties"},
                            },
                        },
                    }]
                },
                {
                    "fields": [{
                        "id":         KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH,
                        "label":      "Width of Bottom Flange, b<sub>fw</sub> (mm):",
                        "type":       TYPE_ADAPTIVE,
                        "controller": KEY_DESIGN_MODE,
                        "modes": {
                            "Optimized": {
                                "type":           TYPE_BOUND_BTN,
                                "text":           "Set Bounds",
                                "lower_limit":    100.0,
                                "upper_limit":    1000.0,
                                "with_increment": True,
                                "on_accepted": "_on_bounds_accepted",
                            },
                            "Custom": {
                                "type":              TYPE_TEXTBOX,
                                "placeholder":       "",
                                "on_editing_finished": "_update_section_drawing",
                                "on_change_compute": {"function": "_compute_welded_section_properties"},
                            },
                        },
                    }],
                },
                {
                    "fields": [{
                        "id":         KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
                        "label":      "Bottom Flange Thickness, b<sub>ft</sub> (mm):",
                        "type":       TYPE_ADAPTIVE,
                        "controller": KEY_DESIGN_MODE,
                        "modes": {
                            "Optimized": {
                                "type":            TYPE_ALL_CUSTOM,
                                "on_selected":     "_on_all_custom_selected",
                            },
                            "Custom": {
                                "type":              TYPE_COMBOBOX,
                                "choices":           [str(v) for v in SAIL_APPROVED_THICKNESS_VALUES],
                                "on_change":         "_update_section_drawing",
                                "on_change_compute": {"function": "_compute_welded_section_properties"},
                            },
                        },
                    }]
                },
                {
                    "fields": [{
                        "id":         KEY_MP_GIRDER_WEB_THICKNESS,
                        "label":      "Web Thickness, w<sub>t</sub> (mm):",
                        "type":       TYPE_ADAPTIVE,
                        "controller": KEY_DESIGN_MODE,
                        "modes": {
                            "Optimized": {
                                "type":            TYPE_ALL_CUSTOM,
                                "on_selected":     "_on_all_custom_selected",
                            },
                            "Custom": {
                                "type":              TYPE_COMBOBOX,
                                "choices":           [str(v) for v in SAIL_APPROVED_THICKNESS_VALUES],
                                "on_change":         "_update_section_drawing",
                                "on_change_compute": {"function": "_compute_welded_section_properties"},
                            },
                        },
                    }]
                },
                {
                    "fields": [{
                        "id":      KEY_MP_GD_SUPPORT_TYPE,
                        "label":   "Support Type:",
                        "type":    TYPE_COMBOBOX,
                        "choices": VALUES_GIRDER_SUPPORT_TYPE,
                    }]
                },
                {
                    "fields": [{
                        "id":    KEY_MP_GD_SUPPORT_WIDTH,
                        "label": "Support Width (mm):",
                        "type":  TYPE_TEXTBOX,
                    }]
                },

                # Rolled section
                {
                    "fields": [{
                        "id":               KEY_MP_GIRDER_IS_SECTION,
                        "label":            "IS Section:",
                        "type":             TYPE_COMBOBOX,
                        "choices":          get_is_section_list(),
                        "on_change":        "_update_section_drawing",
                        "on_change_compute": {"function": "_compute_rolled_section_properties"},
                    }]
                },

                # Restraints — common to welded + rolled
                {
                    "fields": [{
                        "id":      KEY_MP_GIRDER_TORSIONAL_RESTRAINT,
                        "label":   "Torsional Restraint:",
                        "type":    TYPE_COMBOBOX,
                        "choices": VALUES_TORSIONAL_RESTRAINT,
                        "on_change": "_on_torsional_restraint_changed",
                    }]
                },
                {
                    "fields": [{
                        "id":      KEY_MP_GIRDER_WARPING_RESTRAINT,
                        "label":   "Warping Restraint:",
                        "type":    TYPE_COMBOBOX,
                        "choices": VALUES_WARPING_RESTRAINT,
                        "on_change": "_on_warping_restraint_changed",
                    }]
                },
                {
                    "fields": [{
                        "id":      KEY_MP_GIRDER_WEB_TYPE,
                        "label":   "Web Type:",
                        "type":    TYPE_COMBOBOX,
                        "choices": VALUES_WEB_TYPE,
                    }]
                },
            ],
        },

        # ── Section Preview — col 1, grid row 2 ─────────────────────────────────
        {
            "column": 1,
            "title":  "",
            "id":     KEY_MP_GD_SECTION_DRAWING,
            "rows": [
                {
                    "fields": [{
                        "id":           KEY_MP_GD_SECTION_PREVIEW,
                        "type":         TYPE_DIRECT_WIDGET,
                        "widget_class": RolledSectionPreview,
                    }]
                },
            ],
        },

        # ── Section Properties — col 1, grid row 3 ───────────────────────────
        {
            "column": 1,
            "title":  "Section Properties",
            "id":     KEY_MP_GD_SP,
            "rows": [
                {
                    "fields": 
                        [{
                            "id": KEY_MP_GIRDER_MASS,  
                            "label": "Mass, M (Kg/m)",                                    
                            "type": TYPE_TEXTBOX, "read_only": True,
                        }]},
                {
                    "fields": 
                        [{
                            "id": KEY_MP_GIRDER_SECTIONAL_AREA,  
                            "label": "Sectional Area, a (m<sup>2</sup>)",                
                            "type": TYPE_TEXTBOX, "read_only": True,
                        }]},
                {
                    "fields": 
                        [{
                            "id": KEY_MP_GIRDER_SECTIONAL_IZ,  
                            "label": "2nd Moment of Area, I<sub>z</sub> (m<sup>4</sup>)",  
                            "type": TYPE_TEXTBOX, "read_only": True
                        }]
                },
                {
                    "fields": 
                        [{
                            "id": KEY_MP_GIRDER_SECTIONAL_IY,  
                            "label": "2nd Moment of Area, I<sub>y</sub> (m<sup>4</sup>)",  
                            "type": TYPE_TEXTBOX, "read_only": True
                        }]
                },
                {
                    "fields": 
                        [{
                            "id": KEY_MP_GIRDER_RADIUS_GYRATION_Z,  
                            "label": "Radius of Gyration, r<sub>z</sub> (m)",              
                            "type": TYPE_TEXTBOX, "read_only": True
                        }]
                },
                {
                    "fields": 
                        [{
                            "id": KEY_MP_GIRDER_RADIUS_GYRATION_Y,  
                            "label": "Radius of Gyration, r<sub>y</sub> (m)",              
                            "type": TYPE_TEXTBOX, "read_only": True
                        }]
                },
                {
                    "fields": 
                        [{
                            "id": KEY_MP_GIRDER_ELASTIC_MODULUS_ZZ,  
                            "label": "Elastic Modulus, Z<sub>z</sub> (m<sup>3</sup>)",     
                            "type": TYPE_TEXTBOX, "read_only": True
                        }]
                },
                {
                    "fields": 
                        [{
                            "id": KEY_MP_GIRDER_ELASTIC_MODULUS_ZY,  
                            "label": "Elastic Modulus, Z<sub>y</sub> (m<sup>3</sup>)",     
                            "type": TYPE_TEXTBOX, "read_only": True
                        }]
                },
                {
                    "fields": 
                        [{
                            "id": KEY_MP_GIRDER_PLASTIC_MODULUS_ZUZ,  
                            "label": "Plastic Modulus, Z<sub>pz</sub> (m<sup>3</sup>)",     
                            "type": TYPE_TEXTBOX, "read_only": True
                        }]
                },
                {
                    "fields": 
                        [{
                            "id": KEY_MP_GIRDER_PLASTIC_MODULUS_ZUY,  
                            "label": "Plastic Modulus, Z<sub>py</sub> (m<sup>3</sup>)",     
                            "type": TYPE_TEXTBOX, "read_only": True
                        }]
                },
                {
                    "fields": 
                        [{
                            "id": KEY_MP_GIRDER_TORSION_CONSTANT_IT,  
                            "label": "Torsion Constant, I<sub>t</sub> (m<sup>4</sup>)",     
                            "type": TYPE_TEXTBOX, "read_only": True
                        }]
                },
                {
                    "fields": 
                        [{
                            "id": KEY_MP_GIRDER_WARPING_CONSTANT_IW,  
                            "label": "Warping Constant, I<sub>w</sub> (m<sup>6</sup>)",     
                            "type": TYPE_TEXTBOX, "read_only": True
                        }]
                },
            ],
        },
    ],
}

from osdagbridge.desktop.ui.dialogs.additional_input.drawings.stiffener_details_cad import StiffenerDetailsCad
STIFFENER_DETAILS_SCHEMA = {
    "id": KEY_MP_SD_TAB,
    "layout": {
        "type":          "columns",
        "columns":       2,
        "column_widths": [2, 3],
    },
    "sections": [

        # ── CAD Preview — full width at top ───────────────────────────────────
        {
            "column":   0,
            "col_span": 2,
            "title":    "",
            "rows": [
                {
                    "fields": [{
                        "id":           KEY_SD_STIFFENER_DETAILS,
                        "type":         TYPE_DIRECT_WIDGET,
                        "widget_class": StiffenerDetailsCad,
                    }]
                },
            ],
        },

        # ── Col 0: Member ID + Apply button ──────────────────────────────────
        {
            "column": 0,
            "title":  "",
            "rows": [
                {
                    "fields": [{
                        "id":      KEY_MP_STIFFENER_SELECT_MEMBER_ID,
                        "label":   "Select Member ID:",
                        "type":    TYPE_COMBOBOX,
                        "choices": [],
                        "on_change": "_on_stiffener_member_changed",
                    }]
                },
                {
                    "fields": [{
                        "id":       KEY_MP_STIFFENER_APPLY_ALL,
                        "type":     TYPE_BUTTON,
                        "text":     "Apply changes to all custom",
                        "on_click": "_on_stiffener_apply_all_clicked",
                    }]
                },
            ],
        },

        # ── Col 1: Description — row_span to cover all col 0 rows below ───────
        {
            "column":   1,
            "row_span": 3,
            "type":     TYPE_DESCRIPTION,
            "title":    "Stiffener Details",
            "text":     (
                "Bearing Stiffeners:\n"
                "Provided at support locations to transfer reaction forces into the web. "
                "Number and spacing are configurable per member end.\n\n"
                "Intermediate Stiffeners:\n"
                "Used to improve shear resistance of slender webs. "
                "Enable and specify spacing when required.\n\n"
                "Longitudinal Stiffeners:\n"
                "Reduce web slenderness for heavily loaded girders. "
                "One or two levels can be added at 1/3 depth intervals.\n\n"
                "Web Buckling:\n"
                "Select between Simple Post Critical and Tension Field methods "
                "per IRC/IS code requirements."
            ),
            "stretch":  True,
        },

        # ── Col 0: Stiffener Inputs ───────────────────────────────────────────
        {
            "column": 0,
            "title":  "Stiffener Inputs",
            "rows": [

                {
                    "fields": [{
                        "id":      KEY_MP_STIFFENER_NO_BEARING_STIFFENERS,
                        "label":   "No. of Bearing Stiffeners<br>(on one side only):",
                        "type":    TYPE_COMBOBOX,
                        "choices": VALUES_BEARING_STIFFENER_COUNT,
                        "on_change": "_on_bearing_stiffener_count_changed",
                    }]
                },
                {
                    "fields": [{
                        "id":    KEY_MP_STIFFENER_SPACING,
                        "label": "Bearing Stiffener Spacing (mm):",
                        "type":  TYPE_TEXTBOX,
                        "on_editing_finished": "_update_stiffener_cad",
                    }]
                },
                {
                    "fields": [{
                        "id":      KEY_MP_STIFFENER_BEARING_THICKNESS,
                        "label":   "Bearing Stiffener Thickness (mm):",
                        "type":    TYPE_COMBOBOX,
                        "choices": [str(v) for v in SAIL_APPROVED_THICKNESS_VALUES],
                        "on_change": "_update_stiffener_cad",
                    }]
                },
                {
                    "fields": [{
                        "id":    KEY_MP_STIFFENER_BEARING_OUTSTAND,
                        "label": "Outstand of Bearing Stiffener (mm):",
                        "type":  TYPE_TEXTBOX,
                        "on_editing_finished": "_update_stiffener_cad",
                    }]
                },
                {
                    "fields": [{
                        "id":      KEY_MP_STIFFENER_INTERMEDIATE,
                        "label":   "Intermediate Stiffener:",
                        "type":    TYPE_COMBOBOX,
                        "choices": VALUES_NO_YES,
                        "on_change": "_on_intermediate_stiffener_changed",
                    }]
                },
                {
                    "fields": [{
                        "id":    KEY_MP_STIFFENER_INTERMEDIATE_SPACING,
                        "label": "Intermediate Stiffener Spacing (mm):",
                        "type":  TYPE_TEXTBOX,
                        "on_editing_finished": "_update_stiffener_cad",
                    }]
                },
                {
                    "fields": [{
                        "id":      KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS,
                        "label":   "Intermediate Stiffener Thickness (mm):",
                        "type":    TYPE_COMBOBOX,
                        "choices": [str(v) for v in SAIL_APPROVED_THICKNESS_VALUES],
                        "on_change": "_update_stiffener_cad",
                    }]
                },
                {
                    "fields": [{
                        "id":    KEY_MP_STIFFENER_INTERMEDIATE_OUTSTAND,
                        "label": "Outstand of Intermediate Stiffener (mm):",
                        "type":  TYPE_TEXTBOX,
                        "on_editing_finished": "_update_stiffener_cad",
                    }]
                },
                {
                    "fields": [{
                        "id":      KEY_MP_STIFFENER_LONGITUDINAL,
                        "label":   "Longitudinal Stiffener:",
                        "type":    TYPE_COMBOBOX,
                        "choices": VALUES_LONGITUDINAL_STIFFENER,
                        "on_change": "_on_longitudinal_stiffener_changed",
                    }]
                },
                {
                    "fields": [{
                        "id":      KEY_MP_STIFFENER_LONGITUDINAL_THICKNESS,
                        "label":   "Longitudinal Stiffener Thickness (mm):",
                        "type":    TYPE_COMBOBOX,
                        "choices": [str(v) for v in SAIL_APPROVED_THICKNESS_VALUES],
                        "on_change": "_update_stiffener_cad",
                    }]
                },
            ],
        },

        # ── Col 0: Web Buckling ───────────────────────────────────────────────
        {
            "column": 0,
            "title":  "Web Buckling Details",
            "rows": [
                {
                    "fields": [{
                        "id":      KEY_MP_STIFFENER_DESIGN_METHOD,
                        "label":   "Shear Buckling Design Method:",
                        "type":    TYPE_COMBOBOX,
                        "choices": VALUES_STIFFENER_DESIGN,
                        "on_change": "_update_stiffener_cad",
                    }]
                },
            ],
        },
    ],
}

from osdagbridge.desktop.ui.dialogs.additional_input.drawings.end_diaphragm_cad import (
    CrossBracingLayoutCad,
    EndDiaphragmBracingLayoutCad,
    BracingSectionPreview,
    TopChordSectionPreview,
    BottomChordSectionPreview,
)

CROSS_BRACING_DETAILS_SCHEMA = {
    "id": KEY_MP_CB_TAB,
    "layout": {
        "type":          "columns",
        "columns":       2,
        "column_widths": [3, 2],
    },
    "sections": [

        # ══════════════ COL 0 — Overview ════════════════════════════════════
        {
            "column": 0,
            "title":  "",
            "rows": [
                {"fields": [{
                    "id":      KEY_MP_CB_SELECT_GIRDERS,
                    "label":   "Select Girders:",
                    "type":    TYPE_COMBOBOX,
                    "choices": [],
                }]},
                {"fields": [{
                    "id":    KEY_MP_CB_NO_OF_CROSS_BRACINGS,
                    "label": "No. of Cross Bracings:",
                    "type":  TYPE_TEXTBOX,
                }]},
                {"fields": [{
                    "id":        KEY_MP_CB_MEMBER_ID,
                    "label":     "Member ID:",
                    "type":      TYPE_TEXTBOX,
                    "read_only": True,
                }]},
            ],
        },

        # ══════════════ COL 0 — Section Inputs ══════════════════════════════
        {
            "column": 0,
            "title":  "Section Inputs",
            "rows": [

                # ── Bracing layout ───────────────────────────────────────────
                {"fields": [{
                    "id":      KEY_MP_CB_TYPE,
                    "label":   "Type of Bracing:",
                    "type":    TYPE_COMBOBOX,
                    "choices": ["K-Bracing", "X-Bracing"],
                }]},
                {"fields": [{
                    "id":      KEY_MP_CB_BRACING_CONNECTION,
                    "label":   "Type of Connection:",
                    "type":    TYPE_COMBOBOX,
                    "choices": ["Bolted", "Welded"],
                }]},

                # ── Bracing section ──────────────────────────────────────────
                {"fields": [{
                    "id":      KEY_MP_CB_BRACING_SECTION_TYPE,
                    "label":   "Bracing Section Type:",
                    "type":    TYPE_COMBOBOX,
                    "choices": [
                                "Angle",
                                "Double Angle (Long Leg)",
                                "Double Angle (Short Leg)",
                                "Channel",
                                "Double Channel",
                            ],
                }]},
                {"fields": [{
                    "id":      KEY_MP_CB_BRACING_SECTION_DESIGNATION,
                    "label":   "Bracing Section Designation:",
                    "type":    TYPE_COMBOBOX,
                    "choices": get_angle_designation_list(),
                }]},

                # ── Top Chord ────────────────────────────────────────────────
                {"fields": [{
                    "id":          KEY_MP_CB_TOP_CHORD,
                    "label":       "Top Chord",
                    "type":        TYPE_CHECKBOX,
                    "label_first": True,
                }]},
                {"fields": [{
                    "id":      KEY_MP_CB_TOP_CHORD_SECTION_TYPE,
                    "label":   "  Top Chord Section Type:",
                    "type":    TYPE_COMBOBOX,
                    "choices": [
                                    "Angle",
                                    "Double Angle (Long Leg)",
                                    "Double Angle (Short Leg)",
                                    "Channel",
                                    "Double Channel",
                                ],
                }]},
                {"fields": [{
                    "id":      KEY_MP_CB_TOP_CHORD_SECTION_DESIG,
                    "label":   "  Top Chord Section Designation:",
                    "type":    TYPE_COMBOBOX,
                    "choices": get_angle_designation_list(),
                }]},

                # ── Bottom Chord ─────────────────────────────────────────────
                {"fields": [{
                    "id":          KEY_MP_CB_BOTTOM_CHORD,
                    "label":       "Bottom Chord",
                    "type":        TYPE_CHECKBOX,
                    "label_first": True,
                }]},
                {"fields": [{
                    "id":      KEY_MP_CB_BOTTOM_CHORD_SECTION_TYPE,
                    "label":   "  Bottom Chord Section Type:",
                    "type":    TYPE_COMBOBOX,
                    "choices": [
                                    "Angle",
                                    "Double Angle (Long Leg)",
                                    "Double Angle (Short Leg)",
                                    "Channel",
                                    "Double Channel",
                                ],
                }]},
                {"fields": [{
                    "id":      KEY_MP_CB_BOTTOM_CHORD_SECTION_DESIG,
                    "label":   "  Bottom Chord Section Designation:",
                    "type":    TYPE_COMBOBOX,
                    "choices": get_angle_designation_list(),
                }]},

                # ── Spacing ──────────────────────────────────────────────────
                {"fields": [{
                    "id":        KEY_MP_CB_SPACING,
                    "label":     "Spacing (m):",
                    "type":      TYPE_TEXTBOX,
                    "read_only": True,
                }]},
            ],
        },

        # ══════════════ COL 1 — CAD: Type of Bracing layout diagram ════════
        {
            "column": 1,
            "title":  "Type of Bracing",
            "rows": [
                {"fields": [{
                    "id":           "member_properties.cross_bracing_details.layout_cad",
                    "type":         TYPE_DIRECT_WIDGET,
                    "widget_class": CrossBracingLayoutCad,
                }]},
            ],
        },

        # ══════════════ COL 1 — CAD: Bracing section preview ═══════════════
        {
            "column": 1,
            "title":  "Bracing",
            "rows": [
                {"fields": [{
                    "id":           KEY_MP_CB_BRACING_PREVIEW,
                    "type":         TYPE_DIRECT_WIDGET,
                    "widget_class": BracingSectionPreview,
                }]},
            ],
        },

        # ══════════════ COL 1 — CAD: Top Chord preview ══════════════════════
        {
            "column": 1,
            "id":     KEY_MP_CB_TOP_CHORD_PREVIEW_SECTION,
            "title":  "Top Chord",
            "rows": [
                {"fields": [{
                    "id":           KEY_MP_CB_TOP_CHORD_PREVIEW,
                    "type":         TYPE_DIRECT_WIDGET,
                    "widget_class": TopChordSectionPreview,
                }]},
            ],
        },

        # ══════════════ COL 1 — CAD: Bottom Chord preview ═══════════════════
        {
            "column": 1,
            "id":     KEY_MP_CB_BOTTOM_CHORD_PREVIEW_SECTION,
            "title":  "Bottom Chord",
            "rows": [
                {"fields": [{
                    "id":           KEY_MP_CB_BOTTOM_CHORD_PREVIEW,
                    "type":         TYPE_DIRECT_WIDGET,
                    "widget_class": BottomChordSectionPreview,
                }]},
            ],
        },
    ],
}

END_DIAPHRAGM_DETAILS_SCHEMA = {
    "id": KEY_MP_ED_TAB,
    "layout": {
        "type":          "columns",
        "columns":       2,
        "column_widths": [3, 2],
    },
    "sections": [
 
        # ── Overview — col 0, always visible ────────────────────────────
        {
            "column": 0,
            "title":  "",
            "rows": [
                {"fields": [{
                    "id": KEY_MP_ED_SELECT_GIRDERS,
                    "label": "Select Girders:",
                    "type": TYPE_COMBOBOX,
                    "choices": [],
                }]},
                {"fields": [{
                    "id": KEY_MP_ED_MEMBER_ID,
                    "label": "Member ID:",
                    "type": TYPE_TEXTBOX,
                    "read_only": True,
                }]},
            ],
        },
 
        # ── Section Inputs — col 0, single card; rows toggle by Type ────
        {
            "column": 0,
            "title":  "Section Inputs",
            "rows": [
                {"fields": [{
                    "id": KEY_MP_ED_TYPE,
                    "label": "Type:",
                    "type": TYPE_COMBOBOX,
                    "choices": VALUES_END_DIAPHRAGM_TYPE,
                    "enabled_choices": ["Cross Bracing"],
                    "on_change": "_on_end_diaphragm_type_changed",
                }]},
 
                # ═══ Cross Bracing rows — shown/hidden via _on_ed_type_visibility ═══
                {
                    "fields": [{
                        "id": KEY_MP_ED_BRACING_TYPE,
                        "label": "Type of Bracing:",
                        "type": TYPE_COMBOBOX,
                        "choices": ["K-Bracing", "X-Bracing"],
                        "on_change": "_on_ed_bracing_layout_changed",
                    }],
                },
                {
                    "fields": [{
                        "id": KEY_MP_ED_BRACING_CONNECTION,
                        "label": "Type of Connection:",
                        "type": TYPE_COMBOBOX,
                        "choices": ["Bolted", "Welded"],
                    }],
                },
                {
                    "fields": [{
                        "id": KEY_MP_ED_BRACING_SECTION,
                        "label": "Bracing Section Type:",
                        "type": TYPE_COMBOBOX,
                        "choices": ["Angle", "Double Angle (Long Leg)", "Double Angle (Short Leg)", "Channel", "Double Channel"],
                        "on_change": "_on_ed_bracing_section_type_changed",
                    }],
                },
                {
                    "fields": [{
                        "id": KEY_MP_ED_BRACING_SECTION_DESIGNATION,
                        "label": "Bracing Section Designation:",
                        "type": TYPE_COMBOBOX,
                        "choices": get_angle_designation_list(),
                        "on_change": "_on_ed_bracing_preview_changed",
                    }],
                },
                {
                    "fields": [{
                        "id": KEY_MP_ED_TOP_CHORD,
                        "label": "Top Chord",
                        "type": TYPE_CHECKBOX,
                        "label_first": True,
                        "on_change": "_on_ed_bracing_layout_changed",
                    }],
                },
                {
                    "fields": [{
                        "id": KEY_MP_ED_TOP_CHORD_SECTION_TYPE,
                        "label": "  Top Chord Section Type:",
                        "type": TYPE_COMBOBOX,
                        "choices": ["Angle", "Double Angle (Long Leg)", "Double Angle (Short Leg)", "Channel", "Double Channel"],
                        "on_change": "_on_ed_top_chord_section_type_changed",
                    }],
                },
                {
                    "fields": [{
                        "id": KEY_MP_ED_TOP_CHORD_SECTION_DESIG,
                        "label": "  Top Chord Section Designation:",
                        "type": TYPE_COMBOBOX,
                        "choices": get_angle_designation_list(),
                        "on_change": "_on_ed_top_chord_preview_changed",
                    }],
                },
                {
                    "fields": [{
                        "id": KEY_MP_ED_BOTTOM_CHORD,
                        "label": "Bottom Chord",
                        "type": TYPE_CHECKBOX,
                        "label_first": True,
                        "on_change": "_on_ed_bracing_layout_changed",
                    }],
                },
                {
                    "fields": [{
                        "id": KEY_MP_ED_BOTTOM_CHORD_SECTION_TYPE,
                        "label": "  Bottom Chord Section Type:",
                        "type": TYPE_COMBOBOX,
                        "choices": ["Angle", "Double Angle (Long Leg)", "Double Angle (Short Leg)", "Channel", "Double Channel"],
                        "on_change": "_on_ed_bottom_chord_section_type_changed",
                    }],
                },
                {
                    "fields": [{
                        "id": KEY_MP_ED_BOTTOM_CHORD_SECTION_DESIG,
                        "label": "  Bottom Chord Section Designation:",
                        "type": TYPE_COMBOBOX,
                        "choices": get_angle_designation_list(),
                        "on_change": "_on_ed_bottom_chord_preview_changed",
                    }],
                },
 
                # ═══ Rolled Beam row — shown/hidden via _on_ed_type_visibility ═══
                {
                    "fields": [{
                        "id": KEY_MP_ED_IS_SECTION,
                        "label": "IS Section:",
                        "type": TYPE_COMBOBOX,
                        "choices": get_is_section_list(),
                        "on_change": "_update_ed_section_drawing",
                        "on_change_compute": {"function": "_compute_ed_rolled_section_properties"},
                    }],
                },

                # ═══ Welded Beam rows — shown/hidden via _on_ed_type_visibility ═══
                # Order matches reference layout: Symmetry, Total Depth, Web Thickness,
                # Top Flange Width, Top Flange Thickness, Bottom Flange Width, Bottom Flange Thickness.
                {
                    "fields": [{
                        "id": KEY_MP_ED_SYMMETRY, "label": "Symmetry:", "type": TYPE_COMBOBOX,
                        "choices": VALUES_GIRDER_SYMMETRY,
                    }],
                },
                {
                    "fields": [{
                        "id": KEY_MP_ED_TOTAL_DEPTH, "label": "Total Depth, d (mm):", "type": TYPE_TEXTBOX,
                        "on_editing_finished": "_update_ed_section_drawing",
                        "on_change_compute": {"function": "_compute_ed_welded_section_properties"},
                    }],
                },
                {
                    "fields": [{
                        "id": KEY_MP_ED_WEB_THICKNESS, "label": "Web Thickness, w<sub>t</sub> (mm):", "type": TYPE_COMBOBOX,
                        "choices": [str(v) for v in SAIL_APPROVED_THICKNESS_VALUES],
                        "on_change": "_update_ed_section_drawing",
                        "on_change_compute": {"function": "_compute_ed_welded_section_properties"},
                    }],
                },
                {
                    "fields": [{
                        "id": KEY_MP_ED_TOP_FLANGE_WIDTH, "label": "Width of Top Flange, t<sub>fw</sub> (mm):", "type": TYPE_TEXTBOX,
                        "on_editing_finished": "_update_ed_section_drawing",
                        "on_change_compute": {"function": "_compute_ed_welded_section_properties"},
                    }],
                },
                {
                    "fields": [{
                        "id": KEY_MP_ED_TOP_FLANGE_THICKNESS, "label": "Top Flange Thickness, t<sub>ft</sub> (mm):", "type": TYPE_COMBOBOX,
                        "choices": [str(v) for v in SAIL_APPROVED_THICKNESS_VALUES],
                        "on_change": "_update_ed_section_drawing",
                        "on_change_compute": {"function": "_compute_ed_welded_section_properties"},
                    }],
                },
                {
                    "fields": [{
                        "id": KEY_MP_ED_BOTTOM_FLANGE_WIDTH, "label": "Width of Bottom Flange, b<sub>fw</sub> (mm):", "type": TYPE_TEXTBOX,
                        "on_editing_finished": "_update_ed_section_drawing",
                        "on_change_compute": {"function": "_compute_ed_welded_section_properties"},
                    }],
                },
                {
                    "fields": [{
                        "id": KEY_MP_ED_BOTTOM_FLANGE_THICKNESS, "label": "Bottom Flange Thickness, b<sub>ft</sub> (mm):", "type": TYPE_COMBOBOX,
                        "choices": [str(v) for v in SAIL_APPROVED_THICKNESS_VALUES],
                        "on_change": "_update_ed_section_drawing",
                        "on_change_compute": {"function": "_compute_ed_welded_section_properties"},
                    }],
                },
            ],
        },
 
        # ══════════════ COL 1 — CAD: Type of Bracing layout diagram ════════
        {
            "column": 1,
            "title":  "Type of Bracing",
            "id":     KEY_MP_ED_BRACING_LAYOUT_SECTION,
            "rows": [
                {"fields": [{
                    "id": KEY_MP_ED_BRACING_LAYOUT_CAD,
                    "type": TYPE_DIRECT_WIDGET,
                    "widget_class": EndDiaphragmBracingLayoutCad,
                }]},
            ],
        },
 
        # ══════════════ COL 1 — CAD: Bracing section preview ═══════════════
        {
            "column": 1,
            "title":  "Bracing",
            "id":     KEY_MP_ED_BRACING_PREVIEW_SECTION,
            "rows": [
                {"fields": [{
                    "id": KEY_MP_ED_BRACING_SECTION_PREVIEW,
                    "type": TYPE_DIRECT_WIDGET,
                    "widget_class": BracingSectionPreview,
                }]},
            ],
        },
 
        # ══════════════ COL 1 — CAD: Top Chord preview — only if checked ═══
        {
            "column": 1,
            "title":  "Top Chord",
            "id":     KEY_MP_ED_TOP_CHORD_PREVIEW_SECTION,
            "rows": [
                {"fields": [{
                    "id": KEY_MP_ED_TOP_CHORD_PREVIEW,
                    "type": TYPE_DIRECT_WIDGET,
                    "widget_class": TopChordSectionPreview,
                }]},
            ],
        },
 
        # ══════════════ COL 1 — CAD: Bottom Chord preview — only if checked ═
        {
            "column": 1,
            "title":  "Bottom Chord",
            "id":     KEY_MP_ED_BOTTOM_CHORD_PREVIEW_SECTION,
            "rows": [
                {"fields": [{
                    "id": KEY_MP_ED_BOTTOM_CHORD_PREVIEW,
                    "type": TYPE_DIRECT_WIDGET,
                    "widget_class": BottomChordSectionPreview,
                }]},
            ],
        },
 
        # ══════════════ COL 1 — CAD: Rolled section preview ════════════════
        {
            "column": 1,
            "title":  "",
            "id":     KEY_MP_ED_ROLLED_PREVIEW_SECTION,
            "rows": [
                {"fields": [{
                    "id": KEY_MP_ED_ROLLED_PREVIEW,
                    "type": TYPE_DIRECT_WIDGET,
                    "widget_class": RolledSectionPreview,
                }]},
            ],
        },
 
        # ══════════════ COL 1 — CAD: Welded section preview ════════════════
        {
            "column": 1,
            "title":  "",
            "id":     KEY_MP_ED_WELDED_PREVIEW_SECTION,
            "rows": [
                {"fields": [{
                    "id": KEY_MP_ED_WELDED_PREVIEW,
                    "type": TYPE_DIRECT_WIDGET,
                    "widget_class": RolledSectionPreview,
                }]},
            ],
        },
 
        # ══════════════ COL 1 — Section Properties, below active preview ═══
        {
            "column": 1,
            "title":  "Section Properties",
            "id":     KEY_MP_ED_SECTION_PROPERTIES_SECTION,
            "rows": [
                {"fields": [{"id": KEY_MP_ED_MASS,               "label": "Mass, M (Kg/m)",               "type": TYPE_TEXTBOX, "read_only": True}]},
                {"fields": [{"id": KEY_MP_ED_SECTIONAL_AREA,      "label": "Sectional Area, a (cm²)",      "type": TYPE_TEXTBOX, "read_only": True}]},
                {"fields": [{"id": KEY_MP_ED_SECTIONAL_IZ,        "label": "2nd Moment of Area, Iz (cm⁴)", "type": TYPE_TEXTBOX, "read_only": True}]},
                {"fields": [{"id": KEY_MP_ED_SECTIONAL_IY,        "label": "2nd Moment of Area, Iy (cm⁴)", "type": TYPE_TEXTBOX, "read_only": True}]},
                {"fields": [{"id": KEY_MP_ED_RADIUS_GYRATION_Z,   "label": "Radius of Gyration, rz (cm)",  "type": TYPE_TEXTBOX, "read_only": True}]},
                {"fields": [{"id": KEY_MP_ED_RADIUS_GYRATION_Y,   "label": "Radius of Gyration, ry (cm)",  "type": TYPE_TEXTBOX, "read_only": True}]},
                {"fields": [{"id": KEY_MP_ED_ELASTIC_MODULUS_ZZ,  "label": "Elastic Modulus, Zz (cm³)",    "type": TYPE_TEXTBOX, "read_only": True}]},
                {"fields": [{"id": KEY_MP_ED_ELASTIC_MODULUS_ZY,  "label": "Elastic Modulus, Zy (cm³)",    "type": TYPE_TEXTBOX, "read_only": True}]},
                {"fields": [{"id": KEY_MP_ED_PLASTIC_MODULUS_ZUZ, "label": "Plastic Modulus, Zpz (cm³)",   "type": TYPE_TEXTBOX, "read_only": True}]},
                {"fields": [{"id": KEY_MP_ED_PLASTIC_MODULUS_ZUY, "label": "Plastic Modulus, Zpy (cm³)",   "type": TYPE_TEXTBOX, "read_only": True}]},
            ],
        },
    ],
}

MEMBER_PROPERTIES_SCHEMA = {
    "id":     "member_properties.main",
    "layout": {"type": "tabs"},
    "tabs": [
        {"title": "Girder Details",        "schema": GIRDER_DETAILS_SCHEMA},
        {"title": "Stiffener Details",     "schema": STIFFENER_DETAILS_SCHEMA},
        {"title": "Cross-Bracing Details", "schema": CROSS_BRACING_DETAILS_SCHEMA},
        {"title": "End Diaphragm Details", "schema": END_DIAPHRAGM_DETAILS_SCHEMA},
    ],
}

# ── Main Schema ───────────────────────────────────────────────────────────────

ADDITIONAL_INPUTS_SCHEMA = [
    {
        "label":    "Typical Section Details",
        "schema":   TYPICAL_SECTION_SCHEMA,
        "main_id":  KEY_TS_TAB + ".main",
        "filler_column_index": None,
    },
    {
        "label":   "Member Properties",
        "schema":  MEMBER_PROPERTIES_SCHEMA,
        "main_id": "member_properties.main",
        "with_scroll": False,
    },
    {
        "label":   "Loading",
        "schema":  LOADING_TAB_SCHEMA,
        "main_id": "loading.main",
        "with_scroll": False,
    },
    {
        "label":   "Support Conditions",
        "schema":  SUPPORT_CONDITIONS_SCHEMA,
        "main_id": "support_conditions.main",
        "with_scroll": True,
    },
    {
        "label":   "Analysis/Design Options",
        "schema":  DESIGN_OPTIONS_SCHEMA,
        "main_id": "design_options.main",
        "with_scroll": True,
    },
    {
        "label":   "Design Options (Cont.)",
        "schema":  DESIGN_OPTIONS_CONT_SCHEMA,
        "main_id": "design_options_cont.main",
        "with_scroll": True,
    },
]


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
                    "id": KEY_MP_GIRDER_MASS,
                    "label": "Mass, M (Kg/m)",
                    "data_key": "mass",
                    "group": "section",
                },
                {
                    "id": KEY_MP_GIRDER_SECTIONAL_AREA,
                    "label": "Sectional Area, a (m<sup>2</sup>)",
                    "data_key": "area",
                    "group": "section",
                },
                {
                    "id": KEY_MP_GIRDER_SECTIONAL_IZ,
                    "label": "2nd Moment of Area, I<sub>z</sub> (m<sup>4</sup>)",
                    "data_key": "iz",
                    "group": "section",
                },
                {
                    "id": KEY_MP_GIRDER_SECTIONAL_IY,
                    "label": "2nd Moment of Area, I<sub>y</sub> (m<sup>4</sup>)",
                    "data_key": "iv",
                    "group": "section",
                },
                {
                    "id": KEY_MP_GIRDER_RADIUS_GYRATION_Z,
                    "label": "Radius of Gyration, r<sub>z</sub> (m)",
                    "data_key": "rz",
                    "group": "section",
                },
                {
                    "id": KEY_MP_GIRDER_RADIUS_GYRATION_Y,
                    "label": "Radius of Gyration, r<sub>y</sub> (m)",
                    "data_key": "rv",
                    "group": "section",
                },
                {
                    "id": KEY_MP_GIRDER_ELASTIC_MODULUS_ZZ,
                    "label": "Elastic Modulus, Z<sub>z</sub> (m<sup>3</sup>)",
                    "data_key": "zz",
                    "group": "section",
                },
                {
                    "id": KEY_MP_GIRDER_ELASTIC_MODULUS_ZY,
                    "label": "Elastic Modulus, Z<sub>y</sub> (m<sup>3</sup>)",
                    "data_key": "zv",
                    "group": "section",
                },
                {
                    "id": KEY_MP_GIRDER_PLASTIC_MODULUS_ZUZ,
                    "label": "Plastic Modulus, Z<sub>pz</sub> (m<sup>3</sup>)",
                    "data_key": "zuz",
                    "group": "section",
                },
                {
                    "id": KEY_MP_GIRDER_PLASTIC_MODULUS_ZUY,
                    "label": "Plastic Modulus, Z<sub>py</sub> (m<sup>3</sup>)",
                    "data_key": "zuv",
                    "group": "section",
                },
                {
                    "id": KEY_MP_GIRDER_TORSION_CONSTANT_IT,
                    "label": "Torsion Constant, I<sub>t</sub> (m<sup>4</sup>)",
                    "data_key": "it",
                    "group": "section",
                },
                {
                    "id": KEY_MP_GIRDER_WARPING_CONSTANT_IW,
                    "label": "Warping Constant, I<sub>w</sub> (m<sup>6</sup>)",
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

TRANSVERSE_MEMBER_DESIGN_SCHEMA = {
    "id": KEY_TD_DIALOG,
    "title": "Transverse Member Design",
    "window": {"width": 1100, "height": 720, "min_width": 950, "min_height": 550},
    "global_bar": [
        {"id": KEY_TD_SELECT_GIRDER, "label": "Select Girder", "type": "combo"},
        {"id": KEY_TD_LOAD_COMBINATION, "label": "Load Combination", "type": "combo", "default": "Envelope"},
    ],
    # Unified Crossbracing Tab
    "crossbracing_tab": {
        "id": KEY_TD_CB_TAB,
        "label": "Crossbracing",
        "left_panel": {
            "section_inputs": {
                "label": "Section Inputs:",
                "label_width": 100,
                "fields": [
                    {"id": KEY_TD_CB_SECTION_INPUTS_DESIGN, "label": "Design:", "type": "line", "read_only": True},
                    {"id": KEY_TD_CB_SECTION_INPUTS_NO_OF_CB, "label": "No. of Crossbracing:", "type": "line", "read_only": True},
                    {"id": KEY_TD_CB_SECTION_INPUTS_BRACING_TYPE, "label": "Type of Bracing:", "type": "line", "read_only": True},
                    {"id": KEY_TD_CB_SECTION_INPUTS_CONNECTION_TYPE, "label": "Type of Connection:", "type": "line", "read_only": True},
                    {"id": KEY_TD_CB_SECTION_INPUTS_BRACING_SECTION_TYPE, "label": "Bracing Section Type:", "type": "line", "read_only": True},
                    {"id": KEY_TD_CB_SECTION_INPUTS_BRACING_SECTION_DESIGNATION, "label": "Bracing Section Designation:", "type": "line", "read_only": True},
                    {"id": KEY_TD_CB_SECTION_INPUTS_TOP_CHORD_ENABLED, "label": "Top Chord", "type": "checkbox", "default": True, "enabled": False},
                    {"id": KEY_TD_CB_SECTION_INPUTS_TOP_CHORD_SECTION_TYPE, "label": " Top Chord Section Type:", "type": "line", "read_only": True},
                    {"id": KEY_TD_CB_SECTION_INPUTS_TOP_CHORD_SECTION_DESIGNATION, "label": " Top Chord Section Designation:", "type": "line", "read_only": True},
                    {"id": KEY_TD_CB_SECTION_INPUTS_BOTTOM_CHORD_ENABLED, "label": "Bottom Chord", "type": "checkbox", "default": True, "enabled": False},
                    {"id": KEY_TD_CB_SECTION_INPUTS_BOTTOM_CHORD_SECTION_TYPE, "label": " Bottom Chord Section Type:", "type": "line", "read_only": True},
                    {"id": KEY_TD_CB_SECTION_INPUTS_BOTTOM_CHORD_SECTION_DESIGNATION, "label": " Bottom Chord Section Designation:", "type": "line", "read_only": True},
                    {"id": KEY_TD_CB_SECTION_INPUTS_SPACING, "label": "Spacing:", "type": "line", "read_only": True},
                ],
            },
        },
        "right_panel": {
            "bracing_diagram": {"id": KEY_TD_CB_BRACING_DIAGRAM, "height": 170},
            "section_cards": [
                {"id": KEY_TD_CB_SECTION_PROPS_BRACING, "title": "Bracing", "col1": ["L (m)", "H (m)", "B (m)", "tw (m)", "tF (m)", "rz (cm)"], "col2": ["M (Kg/m)", "A (cm²)", "Iz (cm⁴)", "Iv (cm⁴)", "rv (cm)"], "col3": ["Zz (cm³)", "Zv (cm³)", "Zuz (cm³)", "Zuv (cm³)"]},
                {"id": KEY_TD_CB_SECTION_PROPS_TOP_CHORD, "title": "Top Chord", "col1": ["L (m)", "H (m)", "B (m)", "tw (m)", "tF (m)", "rz (cm)"], "col2": ["M (Kg/m)", "A (cm²)", "Iz (cm⁴)", "Iv (cm⁴)", "rv (cm)"], "col3": ["Zz (cm³)", "Zv (cm³)", "Zuz (cm³)", "Zuv (cm³)"]},
                {"id": KEY_TD_CB_SECTION_PROPS_BOTTOM_CHORD, "title": "Bottom Chord", "col1": ["L (m)", "H (m)", "B (m)", "tw (m)", "tF (m)", "rz (cm)"], "col2": ["M (Kg/m)", "A (cm²)", "Iz (cm⁴)", "Iv (cm⁴)", "rv (cm)"], "col3": ["Zz (cm³)", "Zv (cm³)", "Zuz (cm³)", "Zuv (cm³)"]},
            ],
        },
        "results_table": {
            "id": KEY_TD_CB_DESIGN_CHECK_RESULTS,
            "title": "Design Check Results:",
            "min_height": 200,
            "columns": [
                "Member",
                "Force Type",
                "Force (kN)",
                "Section",
                "Connection",
                "λ (slend.)",
                "Capacity (kN)",
                "Utilization Ratio",
                "Status",
            ],
        },
    },
    "end_diaphragm_tab": {
        "id": KEY_TD_ED_TAB,
        "label": "End Diaphragm",
        "left_panel": {
            "section_inputs": {
                "label": "Section Inputs:",
                "label_width": 100,
                "fields": [
                    {"id": KEY_TD_ED_SECTION_INPUTS_DESIGN,      "label": "Design:",               "type": "line",     "read_only": True,  "group": None},
                    {"id": KEY_TD_ED_SECTION_INPUTS_TYPE,         "label": "Type:",                 "type": "line",     "read_only": True,  "group": None, "on_change": "_on_ed_type_changed"},
                    {"id": KEY_TD_ED_SECTION_INPUTS_NO_OF_CB,     "label": "No. of End-Diaphragms:",  "type": "line",     "read_only": True,  "group": None},
                    {"id": KEY_TD_ED_SECTION_INPUTS_CONNECTION_TYPE, "label": "Type of Connection:", "type": "line",    "read_only": True,  "group": None},

                    # ── Cross Bracing group ───────────────────────────────────────────────
                    {"id": KEY_TD_ED_SECTION_INPUTS_BRACING_TYPE,                "label": "Type of Bracing:",               "type": "line", "read_only": True, "group": "crossbracing"},
                    {"id": KEY_TD_ED_SECTION_INPUTS_BRACING_SECTION_TYPE,        "label": "Bracing Section Type:",          "type": "line", "read_only": True, "group": "crossbracing"},
                    {"id": KEY_TD_ED_SECTION_INPUTS_BRACING_SECTION_DESIGNATION, "label": "Bracing Section Designation:",   "type": "line", "read_only": True, "group": "crossbracing"},
                    {"id": KEY_TD_ED_SECTION_INPUTS_TOP_CHORD_ENABLED,           "label": "Top Chord",                      "type": "checkbox", "default": True, "enabled": False, "group": "crossbracing"},
                    {"id": KEY_TD_ED_SECTION_INPUTS_TOP_CHORD_SECTION_TYPE,      "label": "Top Chord Section Type:",        "type": "line", "read_only": True, "group": "crossbracing"},
                    {"id": KEY_TD_ED_SECTION_INPUTS_TOP_CHORD_SECTION_DESIGNATION, "label": "Top Chord Section Designation:", "type": "line", "read_only": True, "group": "crossbracing"},
                    {"id": KEY_TD_ED_SECTION_INPUTS_BOTTOM_CHORD_ENABLED,        "label": "Bottom Chord",                   "type": "checkbox", "default": True, "enabled": False, "group": "crossbracing"},
                    {"id": KEY_TD_ED_SECTION_INPUTS_BOTTOM_CHORD_SECTION_TYPE,   "label": "Bottom Chord Section Type:",     "type": "line", "read_only": True, "group": "crossbracing"},
                    {"id": KEY_TD_ED_SECTION_INPUTS_BOTTOM_CHORD_SECTION_DESIGNATION, "label": "Bottom Chord Section Designation:", "type": "line", "read_only": True, "group": "crossbracing"},

                    # ── Welded Beam group ─────────────────────────────────────────────────
                    {"id": KEY_TD_ED_SECTION_INPUTS_IS_SECTION,              "label": "IS Section Designation:", "type": "line", "read_only": True, "group": "welded_beam"},
                    {"id": KEY_TD_ED_SECTION_INPUTS_SYMMETRY,                "label": "Symmetry:",               "type": "line", "read_only": True, "group": "welded_beam"},
                    {"id": KEY_TD_ED_SECTION_INPUTS_TOTAL_DEPTH,             "label": "Total Depth (mm):",       "type": "line", "read_only": True, "group": "welded_beam"},
                    {"id": KEY_TD_ED_SECTION_INPUTS_WEB_THICKNESS,           "label": "Web Thickness (mm):",     "type": "line", "read_only": True, "group": "welded_beam"},
                    {"id": KEY_TD_ED_SECTION_INPUTS_TOP_FLANGE_WIDTH,        "label": "Top Flange Width (mm):",  "type": "line", "read_only": True, "group": "welded_beam"},
                    {"id": KEY_TD_ED_SECTION_INPUTS_TOP_FLANGE_THICKNESS,    "label": "Top Flange Thickness (mm):", "type": "line", "read_only": True, "group": "welded_beam"},
                    {"id": KEY_TD_ED_SECTION_INPUTS_BOTTOM_FLANGE_WIDTH,     "label": "Bottom Flange Width (mm):",  "type": "line", "read_only": True, "group": "welded_beam"},
                    {"id": KEY_TD_ED_SECTION_INPUTS_BOTTOM_FLANGE_THICKNESS, "label": "Bottom Flange Thickness (mm):", "type": "line", "read_only": True, "group": "welded_beam"},
                ],
            },
        },
        "right_panel": {
            "bracing_diagram": {"id": KEY_TD_ED_BRACING_DIAGRAM, "height": 170},
            "section_cards": [
                {"id": KEY_TD_ED_SECTION_PROPS_BRACING, "title": "End Diaphragm", "col1": ["L (m)", "H (m)", "B (m)", "tw (m)", "tF (m)", "rz (cm)"], "col2": ["M (Kg/m)", "A (cm²)", "Iz (cm⁴)", "Iv (cm⁴)", "rv (cm)"], "col3": ["Zz (cm³)", "Zv (cm³)", "Zuz (cm³)", "Zuv (cm³)"]},
                {"id": KEY_TD_ED_SECTION_PROPS_TOP_CHORD, "title": "Top Chord", "col1": ["L (m)", "H (m)", "B (m)", "tw (m)", "tF (m)", "rz (cm)"], "col2": ["M (Kg/m)", "A (cm²)", "Iz (cm⁴)", "Iv (cm⁴)", "rv (cm)"], "col3": ["Zz (cm³)", "Zv (cm³)", "Zuz (cm³)", "Zuv (cm³)"]},
                {"id": KEY_TD_ED_SECTION_PROPS_BOTTOM_CHORD, "title": "Bottom Chord", "col1": ["L (m)", "H (m)", "B (m)", "tw (m)", "tF (m)", "rz (cm)"], "col2": ["M (Kg/m)", "A (cm²)", "Iz (cm⁴)", "Iv (cm⁴)", "rv (cm)"], "col3": ["Zz (cm³)", "Zv (cm³)", "Zuz (cm³)", "Zuv (cm³)"]},
            ],
        },
        "results_table": {
            "id": KEY_TD_ED_DESIGN_CHECK_RESULTS,
            "title": "Design Check Results:",
            "min_height": 200,
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
            {"key": "ur_bot_shear", "label": "ULS - One-Way Shear (Interior)", "is_overhang": False},
            {"key": "ur_bot_punch", "label": "ULS - Punching Shear (Interior)","is_overhang": False},
            {"key": "ur_oh_uls",    "label": "ULS - Overhang (Flexure)",       "is_overhang": True},
            {"key": "ur_oh_shear",  "label": "ULS - One-Way Shear (Overhang)", "is_overhang": True},
            {"key": "ur_oh_punch",  "label": "ULS - Punching Shear (Overhang)","is_overhang": True},
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
                ],
                "rows": [
                    [EMPTY],
                ],
            },

            "live_load_definitions": {
                "id": "live_load_definitions",
                "label": "Live Load Definitions",
                "columns": [
                    "Type of Live Load",
                    "Value / Status",
                ],
                "rows": [
                    ["Class A",                           EMPTY],
                    ["Class AA Wheeled",                  EMPTY],
                    ["Class AA Tracked",                  EMPTY],
                    ["Class 70R Wheeled",                 EMPTY],
                    ["Class 70R Tracked",                 EMPTY],
                    ["Class 70R Bogie",                   EMPTY],
                    ["Class SV",                          EMPTY],
                    ["Class Fatigue",                     EMPTY],
                    ["Breaking Load : Class A",           EMPTY],
                    ["Breaking Load : Class AA Wheeled",  EMPTY],
                    ["Breaking Load : Class AA Tracked",  EMPTY],
                    ["Breaking Load : Class 70R Wheeled", EMPTY],
                    ["Breaking Load : Class 70R Tracked", EMPTY],
                    ["Breaking Load : Class 70R Bogie",   EMPTY],
                    ["Breaking Load : Class SV",          EMPTY],
                    ["Breaking Load : Class Fatigue",     EMPTY],
                    ["Breaking Load : Eccentricity",      EMPTY],
                    ["Footpath Pressure (kN/mm²)",        EMPTY],
                ],
            },

            "wind_load_parameters": {
                "id": "wind_load_parameters",
                "label": "Wind Load Parameters",
                "columns": [
                    "Girder",
                    "Basic Wind Speed, Vᵦ (m/s)",
                    "Average Exposed Height, H (m)",
                    "Type of Terrain",
                    "Site Topography",
                    "Gust Factor, G",
                    "Drag Coefficient, Cᴅ",
                    "Drag Coefficient against Live Load, Cᴅʟʟ",
                    "Lift Coefficient, Cᴸ",
                    "Superstructure Area in Elevation, A₁ (m²)",
                    "Superstructure Area in Plain, A₃ (m²)",
                    "Exposed Frontal Area of Live Load, A₁ʟʟ (m²)",
                    "Wind Load Eccentricity from Top of Deck (m)",
                    "Wind on Live Load Eccentricity from Top of Deck (m)",
                    "Hourly Mean Wind Speed, Vᵤ (m/s)",
                    "Hourly Wind Pressure, Pᵤ (N/m²)",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY,
                    EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },

            "seismic_load_parameters": {
                "id": "seismic_load_parameters",
                "label": "Seismic Load Parameters",
                "columns": [
                    "Girder",
                    "Zone",
                    "Seismic Zone Factor, Z",
                    "Importance Factor, I",
                    "Soil Type",
                    "Time Period (s)",
                    "Damping (%)",
                    "Response Reduction Factor",
                    "Spectral Acceleration / g, Sₐ/g",
                    "Horizontal Acceleration Coefficient, Aₕ",
                    "Vertical Acceleration Coefficient, Aᵥ",
                    "Dead Load Considered for Seismic (kN/m)",
                    "Live Load Considered for Seismic (kN/m)",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },

            "temperature_load_parameters": {
                "id": "temperature_load_parameters",
                "label": "Temperature Load Parameters",
                "columns": [
                    "Highest Maximum Air Temperature (°C)",
                    "Lowest Minimum Air Temperature (°C)",
                    "Coefficient of Thermal Expansion for Steel (1/°C)",
                    "Coefficient of Thermal Expansion for RCC (1/°C)",
                    "Effective Bridge Temperature - Minimum (°C)",
                    "Effective Bridge Temperature - Maximum (°C)",
                    "Temperature for Design - Rise (°C)",
                    "Temperature for Design - Fall (°C)",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },

            "load_combinations": {
                "id": "load_combinations",
                "label": "Load Combinations",
                "columns": [
                    "Combination",
                    "Expression",
                    "Selected",
                ],
                "rows": [
                    # ULS Basic
                    ["basic_1", "1.35DL + 1.75DW + 1.5LL + 0.9WL + 0.9TL",  EMPTY],
                    ["basic_2", "1.0DL + 1.0DW + 1.5LL + 0.9WL + 0.9TL",    EMPTY],
                    ["basic_3", "1.35DL + 1.75DW + 1.15LL + 1.5WL + 0.9TL", EMPTY],
                    ["basic_4", "1.0DL + 1.0DW + 1.15LL + 1.5WL + 0.9TL",   EMPTY],
                    ["basic_5", "1.35DL + 1.75DW + 1.15LL + 0.9WL + 1.5TL", EMPTY],
                    ["basic_6", "1.0DL + 1.0DW + 1.15LL + 0.9WL + 1.5TL",   EMPTY],
                    # ULS Accidental
                    ["accidental_1", "1.0DL + 1.0DW + 0.75LL + 0.5TL + 1.0VC", EMPTY],
                    ["accidental_2", "1.0DL + 1.0DW + 0.75LL + 0.5TL + 1.0BI", EMPTY],
                    ["accidental_3", "1.0DL + 1.0DW + 0.75LL + 0.5TL + 1.0FB", EMPTY],
                    # ULS Seismic
                    ["seismic_1", "1.35DL + 1.75DW + 0.2LL + 0.5TL + 1.5EL",  EMPTY],
                    ["seismic_2", "1.0DL + 1.0DW + 0.2LL + 0.5TL + 1.5EL",    EMPTY],
                    ["seismic_3", "1.35DL + 1.75DW + 0.2LL + 0.5TL + 0.75EL", EMPTY],
                    ["seismic_4", "1.0DL + 1.0DW + 0.2LL + 0.5TL + 0.75EL",   EMPTY],
                    # SLS Rare
                    ["rare_1", "1.0DL + 1.2DW + 1.0LL + 0.6WL + 0.6TL",   EMPTY],
                    ["rare_2", "1.0DL + 1.0DW + 1.0LL + 0.6WL + 0.6TL",   EMPTY],
                    ["rare_3", "1.0DL + 1.2DW + 0.75LL + 1.0WL + 0.6TL",  EMPTY],
                    ["rare_4", "1.0DL + 1.0DW + 0.75LL + 1.0WL + 0.6TL",  EMPTY],
                    ["rare_5", "1.0DL + 1.2DW + 0.75LL + 0.6WL + 1.0TL",  EMPTY],
                    ["rare_6", "1.0DL + 1.0DW + 0.75LL + 0.6WL + 1.0TL",  EMPTY],
                    # SLS Frequent
                    ["frequent_1", "1.0DL + 1.2DW + 0.75LL + 0.5WL + 0.5TL", EMPTY],
                    ["frequent_2", "1.0DL + 1.0DW + 0.75LL + 0.5WL + 0.5TL", EMPTY],
                    ["frequent_3", "1.0DL + 1.2DW + 0.2LL + 0.6WL + 0.5TL",  EMPTY],
                    ["frequent_4", "1.0DL + 1.0DW + 0.2LL + 0.6WL + 0.5TL",  EMPTY],
                    ["frequent_5", "1.0DL + 1.2DW + 0.2LL + 0.5WL + 0.6TL",  EMPTY],
                    ["frequent_6", "1.0DL + 1.0DW + 0.2LL + 0.5WL + 0.6TL",  EMPTY],
                    # SLS Quasi-permanent
                    ["quasi_permanent_1", "1.0DL + 1.2DW + 0.5TL", EMPTY],
                    ["quasi_permanent_2", "1.0DL + 1.0DW + 0.5TL", EMPTY],
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
                    "Member",
                    "Total Span (m)",
                    "Type",
                    "Symmetry",
                    "Total Depth, d (mm)",
                    "Width of Top Flange (mm)",
                    "Top Flange Thickness (mm)",
                    "Width of Bottom Flange (mm)",
                    "Bottom Flange Thickness (mm)",
                    "Support Type",
                    "Support Width (mm)",
                    "Web Thickness (mm)",
                    "Torsional Restraint",
                    "Warping Restraint",
                    "Web Type",
                    "Mass, M (kg/m)",
                    "Sectional Area, a (cm²)",
                    "2nd Moment of Area, Iᵤ (cm⁴)",
                    "2nd Moment of Area, Iᵧ (cm⁴)",
                    "Radius of Gyration, rᵤ (cm)",
                    "Radius of Gyration, rᵧ (cm)",
                    "Elastic Modulus, Zᵤ (cm³)",
                    "Elastic Modulus, Zᵧ (cm³)",
                    "Plastic Modulus, Zₚᵤ (cm³)",
                    "Plastic Modulus, Zₚᵧ (cm³)",
                    "Torsion Constant, Iₜ (cm⁴)",
                    "Warping Constant, Iᵥᵥ (cm⁶)",
                ],
                "rows": [
                    [EMPTY] * 27,
                ],
            },

            "cross_bracing_section_properties": {
                "id": "cross_bracing_section_properties",
                "label": "Cross Bracing Section Properties",
                "columns": [
                    "Member",
                    "Type of Bracing",
                    "Bracing Section Type",
                    "Bracing Section Designation",
                    "Top Chord",
                    "Top Chord Section Type",
                    "Top Chord Section Designation",
                    "Bottom Chord",
                    "Bottom Chord Section Type",
                    "Bottom Chord Section Designation",
                    "Spacing (m)",
                ],
                "rows": [[EMPTY] * 11],
            },

            "end_diaphragm_section_properties": {
                "id": "end_diaphragm_section_properties",
                "label": "End Diaphragm Section Properties",
                "columns": [
                    "Member ID",
                    "Type",
                    "Symmetry",
                    "Total Depth, d(mm)",
                    "Web Thickness, wt(mm)",
                    "Width of Top Flange(mm)",
                    "Top Flange Thickness (mm)",
                    "Width of Bottom Flange(mm)",
                    "Bottom Flange Thickness (mm)",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },

            "shear_stud_properties": {
                "id": "shear_stud_properties",
                "label": "Shear Connector Details",
                "columns": [
                    "Material Yield Strength (MPa)",
                    "Material Ultimate Strength (MPa)",
                    "Diameter (mm)",
                    "Height (mm)",
                    "Transverse Spacing (mm)",
                    "No. of Shear Studs per Section",
                    "Average Longitudinal Spacing (mm)",
                ],
                "rows": [[EMPTY] * 7],
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
                    "Design Moment, Mᵈ (kNm)",
                    "Moment Resistance, Mᵣ (kNm)",
                    "Utilization Ratio",
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
                    "Design Shear, Vᵈ (kN)",
                    "Shear Resistance, Vᵣ (kN)",
                    "Utilization Ratio",
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
                    "Design Moment, Mᵈ (kNm)",
                    "Reduced Resistance, Mᵈᵥ (kNm)",
                    "Utilization Ratio",
                    "Status",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },

            "lateral_torsional_buckling_check": {
                "id": "lateral_torsional_buckling_check",
                "label": "Lateral Torsional Buckling Check - Construction Stage",
                "columns": [
                    "Girder",
                    "Design Moment, Mᵈ (kNm)",
                    "LTB Resistance, Mᵦ (kNm)",
                    "Utilization Ratio",
                    "Status",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },
        },

        "sls_checks": {
            "id": "sls_checks",
            "label": "SLS Checks",

            "deflection_live_load": {
                "id": "deflection_live_load",
                "label": "Deflection - Live Load",
                "columns": [
                    "Girder",
                    "Deflection due to Live Load, δ_ₗᵢᵥₑ (mm)",
                    "Permissible Limit",
                    "Utilization Ratio",
                    "Status",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },

            "deflection_total_load": {
                "id": "deflection_total_load",
                "label": "Deflection - Total Load",
                "columns": [
                    "Girder",
                    "Total Deflection, δₜₒₜₐₗ (mm)",
                    "Permissible Limit",
                    "Utilization Ratio",
                    "Status",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },

            "stress_steel_service": {
                "id": "stress_steel_service",
                "label": "Stress in Structural Steel - Service",
                "columns": [
                    "Member",
                    "Steel Stress (MPa)",
                    "Allowable Stress (MPa)",
                    "Utilization Ratio",
                    "Status",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },

            "stress_concrete_service": {
                "id": "stress_concrete_service",
                "label": "Stress in Concrete Deck - Service",
                "columns": [
                    "Member",
                    "Concrete Stress (MPa)",
                    "Allowable Stress (MPa)",
                    "Utilization Ratio",
                    "Status",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },

            "stress_reinf_service": {
                "id": "stress_reinf_service",
                "label": "Stress in Reinforcement - Service",
                "columns": [
                    "Member",
                    "Rebar Stress (MPa)",
                    "Allowable Stress (MPa)",
                    "Utilization Ratio",
                    "Status",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
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
                    "Utilization Ratio",
                    "Status",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
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
                    [EMPTY] * 11
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
                    "Concrete Shear Resistance (kN/m)",
                    "Concrete + Reinforcement Shear Resistance (kN/m)",
                    "Total Shear Resistance, VRd (kN/m)",
                    "Utilization Ratio",
                    "Clause Reference",
                    "Status",
                ],
                "rows": [
                    [EMPTY] * 8
                ],
            },

            "crack_width_check": {
                "id": "crack_width_check",
                "label": "Crack Width Check",
                "columns": [
                    "Member",
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
                    "Controlling Load Case / Combination",
                    "Controlling Design Check",
                    "Demand",
                    "Capacity",
                    "Utilization Ratio",
                    "Status",
                ],
                "rows": [
                    [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
                ],
            },
        },
    },
}

