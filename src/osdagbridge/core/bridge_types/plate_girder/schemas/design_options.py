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
                    "rows": [
                        {
                            "fields": [
                                {
                                    "id": "reinforcement_size",
                                    "label": "Reinforcement Size",
                                    "type": "combo",
                                    "choices": ["8 mm", "10 mm", "12 mm", "16 mm", "20 mm", "25 mm", "28 mm", "32 mm", "36 mm", "40 mm"],
                                    "default": "12 mm",
                                    "bind": "reinforcement_size_combo",
                                },
                                {
                                    "id": "reinforcement_bounds",
                                    "label": "Bounds",
                                    "type": "button",
                                    "text": "Set Bounds",
                                    "bind": "reinforcement_bounds_btn",
                                    "on_click": "_open_reinforcement_bounds",
                                    "width": 110,
                                },
                            ],
                        },
                        {
                            "fields": [
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
                                },
                            ],
                        },
                        {
                            "fields": [
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
                    "rows": [
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
                            ],
                        },
                        {
                            "fields": [
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
                            ],
                        },
                        {
                            "fields": [
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
                                    "value_key": "shear_stud_spacing",
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
                        },
                    ],
                }
            ],
        },
    ],
}

DESIGN_OPTIONS_CONT_SCHEMA = {
    "id": "design_options_cont",
    "label_width": 220,
    "field_width": 140,
    "sections": [

        # ---------------- Partial Factor ----------------
        {
            "title": "Partial Factor",
            "label_width": 270,
            "field_width": 100,
            "rows": [
                {
                    "fields": [
                        {
                            "id": "gamma_c_basic",
                            "label": "Concrete basic & seismic, &#947;<sub>c</sub>",
                            "type": "line",
                            "default": "1.50",
                            "bind": "gamma_c_basic_input",
                            "validator": {"type": "double_range", "bottom": 1.0, "top": 2.0, "decimals": 2},
                        },
                        {
                            "id": "gamma_c_accidental",
                            "label": "Concrete Accidental, &#947;<sub>c</sub>",
                            "type": "line",
                            "default": "1.20",
                            "bind": "gamma_c_accidental_input",
                            "validator": {"type": "double_range", "bottom": 1.0, "top": 2.0, "decimals": 2},
                        },
                    ],
                },
                {
                    "fields": [
                        {
                            "id": "gamma_m0",
                            "label": "Structural steel for Yielding and Buckling, &#947;<sub>M0</sub>",
                            "type": "line",
                            "default": "1.10",
                            "bind": "gamma_m0_input",
                            "validator": {"type": "double_range", "bottom": 1.0, "top": 2.0, "decimals": 2},
                        },
                        {
                            "id": "gamma_m1",
                            "label": "Structural Steel For Ultimate Stress, &#947;<sub>M1</sub>",
                            "type": "line",
                            "default": "1.25",
                            "bind": "gamma_m1_input",
                            "validator": {"type": "double_range", "bottom": 1.0, "top": 2.0, "decimals": 2},
                        },
                    ],
                },
                {
                    "fields": [
                        {
                            "id": "gamma_s",
                            "label": "Reinforcing Steel, &#947;<sub>s</sub>",
                            "type": "line",
                            "default": "1.15",
                            "bind": "gamma_s_input",
                            "validator": {"type": "double_range", "bottom": 1.0, "top": 2.0, "decimals": 2},
                        },
                        {
                            "id": "gamma_v",
                            "label": "Shear Connectors For Yield, &#947;<sub>v</sub>",
                            "type": "line",
                            "default": "1.25",
                            "bind": "gamma_v_input",
                            "validator": {"type": "double_range", "bottom": 1.0, "top": 2.0, "decimals": 2},
                        },
                    ],
                },
                {
                    "fields": [
                        {
                            "id": "gamma_flt",
                            "label": "Fatigue Load, &#947;<sub>flt</sub>",
                            "type": "line",
                            "default": "1.00",
                            "bind": "gamma_flt_input",
                            "validator": {"type": "double_range", "bottom": 1.0, "top": 2.0, "decimals": 2},
                        },
                        {
                            "id": "gamma_mf",
                            "label": "Fatigue Strength, &#947;<sub>Mf,t</sub>",
                            "type": "line",
                            "default": "1.35",
                            "bind": "gamma_mf_input",
                            "validator": {"type": "double_range", "bottom": 1.0, "top": 2.0, "decimals": 2},
                        },
                    ],
                },
            ]
        },

        # ---------------- Resistance to Fatigue ----------------
        {
            "title": "Resistance to Fatigue",
            "fields": [
                {
                    "id": "load_cycles",
                    "label": "Number of Load Cycles",
                    "type": "line",
                    "default": "2000000.00",
                    "bind": "load_cycles_input",
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
                        {"label": "Limit :", "type": "label", "after_spacing": 12},
                        {"label": "L /", "type": "label"},
                        {
                            "id": "limit_l",
                            "label": "",
                            "type": "line",
                            "default": "600.00",
                            "bind": "limit_input",
                            "width": 150,
                            "validator": {
                                "type": "int_range",
                                "bottom": 300,
                                "top": 800,
                            },
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

DESIGN_OPTIONS_CONT_SCHEMA["layout"] = {
    "type": "stack",
    "sections": DESIGN_OPTIONS_CONT_SCHEMA["sections"],
    "boxed_fallback": False,
}
