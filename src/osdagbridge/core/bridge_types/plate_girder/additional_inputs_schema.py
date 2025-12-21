"""Schemas for Additional Inputs dialog (plate girder bridge)."""

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
