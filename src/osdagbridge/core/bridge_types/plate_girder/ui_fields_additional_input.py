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
                    "on_text_changed": "on_no_of_girders_changed",
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
                    "default": "Fixed",
                    "bind": "left_support_combo",
                },
                {
                    "id": "right_support",
                    "label": "Right Support:",
                    "type": "combo",
                    "choices": ["Fixed", "Pinned", "Roller"],
                    "default": "Pinned",
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
                    "default": "0",
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
                            "default": "Yes",
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
                            "default": "12 mm",
                            "bind": "reinforcement_size_combo",
                        },
                        {
                            "id": "reinforcement_material",
                            "label": "Reinforcement Material:",
                            "type": "combo",
                            "choices": ["Fe 415", "Fe 500", "Fe 550"],
                            "default": "Fe 500",
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
                            "bind": "shear_stud_material_input",
                        },
                        {
                            "id": "shear_stud_diameter",
                            "label": "Diameter (mm):",
                            "type": "line",
                            "bind": "shear_stud_diameter_input",
                        },
                        {
                            "id": "shear_stud_height",
                            "label": "Height (mm):",
                            "type": "line",
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
    "sections": [
        {
            "title": "Partial Safety Factors",
            "field_width": 150,
            "fields": [
                {"id": "gamma_c_basic", "label": "Concrete basic & seismic(Gamma_C)", "type": "line", "bind": "gamma_c_basic_input"},
                {"id": "gamma_c_accidental", "label": "Concrete Accidental (Gamma_C)", "type": "line", "bind": "gamma_c_accidental_input"},
                {"id": "gamma_m0", "label": "Structural steel for Yielding and Buckling(Gamma_M0)", "type": "line", "bind": "gamma_m0_input"},
                {"id": "gamma_m1", "label": "Structural Steel For Ultimate Stress(Gamme_M1)", "type": "line", "bind": "gamma_m1_input"},
                {"id": "gamma_s", "label": "Reinforcing Steel (Gamma_s)", "type": "line", "bind": "gamma_s_input"},
                {"id": "gamma_v", "label": "Shear Connectors For Yield(Gamma_v)", "type": "line", "bind": "gamma_v_input"},
                {"id": "gamma_flt", "label": "Fatigue Load(Gamma_flt)", "type": "line", "bind": "gamma_flt_input"},
                {"id": "gamma_mf", "label": "Fatigue Strength(Gamma_Mf, t)", "type": "line", "bind": "gamma_mf_input"},
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
                        {"id": "k1", "label": "K1:", "type": "line", "bind": "k1_input", "width": 80},
                        {"id": "k3", "label": "K3:", "type": "line", "bind": "k3_input", "width": 80},
                        {"id": "k4", "label": "K4:", "type": "line", "bind": "k4_input", "width": 80},
                        {"id": "k6", "label": "K6:", "type": "line", "bind": "k6_input", "width": 80},
                    ]
                },
                {
                    "row_fields": [
                        {"id": "limit_l", "label": "Limit : L (m)", "type": "line", "bind": "limit_input", "width": 120}
                    ]
                },
                {
                    "row_fields": [
                        {"id": "k3_second", "label": "K3:", "type": "line", "bind": "k3_second_input", "width": 80},
                        {"id": "k4_second", "label": "K4:", "type": "line", "bind": "k4_second_input", "width": 80},
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
            "choices": ["Full Length", "Custom"],
            "bind": "span_combo",
        },
    ],
    "section_inputs": [
        {
            "id": "design",
            "label": "Design:",
            "type": "combo",
            "choices": ["Customized", "Optimized"],
            "bind": "design_combo",
            "visible_for": ["welded"],
        },
        {
            "id": "type",
            "label": "Type:",
            "type": "combo",
            "choices": ["Welded", "Rolled"],
            "bind": "type_combo",
        },
        {
            "id": "symmetry",
            "label": "Symmetry:",
            "type": "combo",
            "choices": ["Girder Symmetric", "Girder Unsymmetric"],
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
            "mode_choices": ["All", "Custom"],
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
            "mode_choices": ["All", "Custom"],
            "default_mode": "All",
            "bind_mode": "bottom_thickness_mode_combo",
            "bind_value": "bottom_thickness_input",
            "visible_for": ["welded"],
        },
        {
            "id": "web_thickness",
            "label": "Web Thickness (mm):",
            "type": "mode_line",
            "mode_choices": ["All", "Custom"],
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
            "choices": [
                "Fully Restrained", "Partially Restrained - Support Connect", "Partially Restrained - Bearing Support",
            ],
            "bind": "torsion_combo",
        },
        {
            "id": "warping_restraint",
            "label": "Warping Restraint:",
            "type": "combo",
            "choices": ["Both Flange Restraint", "No Restraint"],
            "bind": "warping_combo",
        },
        {
            "id": "web_type",
            "label": "Web Type*:",
            "type": "combo",
            "choices": ["Thin Web with ITS", "Thick Web"],
            "bind": "web_type_combo",
        },
    ],
}
