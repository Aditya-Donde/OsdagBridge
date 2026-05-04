"""
Default data schema for Generate Results Table dialog.

Purpose:
Temporary centralized source of default values for all result tables until
real bindings / calculations are connected.

Usage:
table = GENERATE_RESULTS_DEFAULTS["model_definition"]["bridge_configuration"]["bridge_configuration_summary"]

columns = table["columns"]
rows = table["rows"]
"""



GENERATE_RESULTS_DEFAULTS = {

    "model_definition": {

        "bridge_configuration": {

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
                    [12.50, 30.00, 4, 3.00, 0.75, 0]
                ],
            },

            "material_properties_steel": {
                "id": "material_properties_steel",
                "label": "Material Properties - Steel",
                "columns": [
                    "Grade",
                    "Fu (MPa)",
                    "Fy (MPa)",
                    "E (MPa)",
                    "G (MPa)",
                    "ν",
                    "Thermal Coefficient",
                ],
                "rows": [
                    ["E350", 490, 350, 200000, 76900, 0.30, 12e-6]
                ],
            },

            "material_properties_concrete": {
                "id": "material_properties_concrete",
                "label": "Material Properties - Concrete",
                "columns": [
                    "Grade",
                    "fck (MPa)",
                    "fctm (MPa)",
                    "Ecm (MPa)",
                    "Modular Ratio",
                ],
                "rows": [
                    ["M40", 40, 3.5, 34000, 6.0]
                ],
            },
        },

        "load_definitions": {

            "permanent_load_summary": {
                "id": "permanent_load_summary",
                "label": "Permanent Load Summary",
                "columns": [
                    "DL (kN/m)",
                    "DW (kN/m)",
                    "SIDL (kN/m)",
                    "Total (kN/m)",
                ],
                "rows": [
                    [55.0, 8.5, 12.0, 75.5]
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
                    ["70R Wheeled", 1.25],
                    ["Class A", 1.10],
                ],
            },

            "wind_load_parameters": {
                "id": "wind_load_parameters",
                "label": "Wind Load Parameters",
                "columns": [
                    "Vb (m/s)",
                    "Vz (m/s)",
                    "Pz (N/m²)",
                    "CD",
                    "CL",
                    "G",
                ],
                "rows": [
                    [39, 42, 1100, 1.8, 0.75, 2.0]
                ],
            },

            "seismic_load_parameters": {
                "id": "seismic_load_parameters",
                "label": "Seismic Load Parameters",
                "columns": [
                    "Zone",
                    "Z",
                    "I",
                    "Sa/g",
                    "Ah",
                    "Av",
                ],
                "rows": [
                    ["III", 0.16, 1.0, 2.5, 0.08, 0.04]
                ],
            },

            "temperature_load_parameters": {
                "id": "temperature_load_parameters",
                "label": "Temperature Load Parameters",
                "columns": [
                    "Max Temp (°C)",
                    "Min Temp (°C)",
                    "ΔT Rise (°C)",
                    "ΔT Fall (°C)",
                ],
                "rows": [
                    [45, 5, 18, -20]
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
                    ["ULS-1", "1.35DL + 1.5LL"],
                    ["SLS-1", "1.0DL + 1.0LL"],
                ],
            },
        },


        "member_definitions": {

            "girder_section_properties": {
                "id": "girder_section_properties",
                "label": "Girder Section Properties",
                "columns": [
                    "Girder",
                    "Depth (mm)",
                    "bf_top (mm)",
                    "bf_bot (mm)",
                    "tf_top (mm)",
                    "tf_bot (mm)",
                    "tw (mm)",
                    "Area (mm²)",
                    "Iz (mm⁴)",
                    "Class",
                ],
                "rows": [
                    ["Girder 1", 1800, 500, 500, 25, 30, 16, 42000, 2.1e11, "Plastic"],
                    ["Girder 2", 1800, 500, 500, 25, 30, 16, 42000, 2.1e11, "Plastic"],
                    ["Girder 3", 1800, 500, 500, 25, 30, 16, 42000, 2.1e11, "Plastic"],
                    ["Girder 4", 1800, 500, 500, 25, 30, 16, 42000, 2.1e11, "Plastic"],
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
                    ["X-Bracing", "ISA100x100x10", 5.0]
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
                    ["Plate Girder", "PL 500x12"]
                ],
            },

            "shear_stud_properties": {
                "id": "shear_stud_properties",
                "label": "Shear Stud Properties",
                "columns": [
                    "Diameter (mm)",
                    "Height (mm)",
                    "Fu (MPa)",
                    "Fy (MPa)",
                    "No./Section",
                ],
                "rows": [
                    [20, 100, 495, 385, 2]
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
                    [220, "16@150", "12@200", 40, 30]
                ],
            },
        },
    },

    "analysis_results": {

        "load_effects_girder": {

            "bending_moment_envelope": {
                "id": "bending_moment_envelope",
                "label": "Bending Moment Diagram - Envelope",
                "columns": [
                    "Girder",
                    "Mmax (kNm)",
                    "Mmin (kNm)",
                ],
                "rows": [
                    ["Girder 1", 9250, -1200],
                    ["Girder 2", 9100, -1180],
                    ["Girder 3", 9100, -1180],
                    ["Girder 4", 9250, -1200],
                ],
            },

            "shear_force_envelope": {
                "id": "shear_force_envelope",
                "label": "Shear Force Diagram - Envelope",
                "columns": [
                    "Girder",
                    "Vmax (kN)",
                    "Vmin (kN)",
                ],
                "rows": [
                    ["Girder 1", 1420, -310],
                    ["Girder 2", 1395, -300],
                    ["Girder 3", 1395, -300],
                    ["Girder 4", 1420, -310],
                ],
            },
        },

        "deflections": {

            "deflection_live_load": {
                "id": "deflection_live_load",
                "label": "Deflection - Live Load",
                "columns": [
                    "Girder",
                    "δ_live (mm)",
                    "Limit",
                    "Status",
                ],
                "rows": [
                    ["Girder 1", 28, "L/800", "PASS"],
                    ["Girder 2", 27, "L/800", "PASS"],
                    ["Girder 3", 27, "L/800", "PASS"],
                    ["Girder 4", 28, "L/800", "PASS"],
                ],
            },

            "deflection_total_load": {
                "id": "deflection_total_load",
                "label": "Deflection - Total Load",
                "columns": [
                    "Girder",
                    "δ_total (mm)",
                    "Limit",
                    "Status",
                ],
                "rows": [
                    ["Girder 1", 42, "L/600", "PASS"],
                    ["Girder 2", 41, "L/600", "PASS"],
                    ["Girder 3", 41, "L/600", "PASS"],
                    ["Girder 4", 42, "L/600", "PASS"],
                ],
            },
        },

        "stress_results": {

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
                    ["Girder 1", 180, 165, 72, 315],
                    ["Girder 2", 176, 162, 70, 315],
                ],
            },

            "stress_concrete_service": {
                "id": "stress_concrete_service",
                "label": "Stress in Concrete Deck - Service",
                "columns": [
                    "Girder",
                    "σc (MPa)",
                    "Allowable",
                ],
                "rows": [
                    ["Girder 1", 12.5, 19.2],
                    ["Girder 2", 12.1, 19.2],
                ],
            },

            "stress_reinf_service": {
                "id": "stress_reinf_service",
                "label": "Stress in Reinforcement - Service",
                "columns": [
                    "Girder",
                    "σreinf (MPa)",
                    "Allowable",
                ],
                "rows": [
                    ["Girder 1", 220, 400],
                    ["Girder 2", 215, 400],
                ],
            },
        },
    },


    "design_results": {

        "uls_checks": {

            "flexural_resistance_check": {
                "id": "flexural_resistance_check",
                "label": "Flexural Resistance Check",
                "columns": [
                    "Girder",
                    "Mu",
                    "Md",
                    "DCR",
                    "Status",
                ],
                "rows": [
                    ["Girder 1", 9250, 12800, 0.72, "PASS"],
                    ["Girder 2", 9100, 12800, 0.71, "PASS"],
                ],
            },

            "shear_resistance_check": {
                "id": "shear_resistance_check",
                "label": "Shear Resistance Check",
                "columns": [
                    "Girder",
                    "Vu",
                    "Vd",
                    "DCR",
                    "Status",
                ],
                "rows": [
                    ["Girder 1", 1420, 1850, 0.77, "PASS"],
                    ["Girder 2", 1395, 1850, 0.75, "PASS"],
                ],
            },
        },

        "sls_checks": {

            "deflection_control_live": {
                "id": "deflection_control_live",
                "label": "Deflection Control - Live Load",
                "columns": [
                    "Girder",
                    "δ_live",
                    "Limit",
                    "Status",
                ],
                "rows": [
                    ["Girder 1", 28, "L/800", "PASS"]
                ],
            },

            "max_stress_steel": {
                "id": "max_stress_steel",
                "label": "Maximum Stress Limitation - Steel",
                "columns": [
                    "Girder",
                    "σs",
                    "Allowable",
                    "Status",
                ],
                "rows": [
                    ["Girder 1", 180, 315, "PASS"]
                ],
            },
        },

        "fatigue_checks": {

            "fatigue_assessment_girder": {
                "id": "fatigue_assessment_girder",
                "label": "Fatigue Assessment - Girder",
                "columns": [
                    "Girder",
                    "Δσ",
                    "ffd",
                    "Status",
                ],
                "rows": [
                    ["Girder 1", 72, 110, "PASS"]
                ],
            },

            "fatigue_assessment_shear_connectors": {
                "id": "fatigue_assessment_shear_connectors",
                "label": "Fatigue Assessment - Shear Connectors",
                "columns": [
                    "Stud",
                    "Δτ",
                    "τfd",
                    "Status",
                ],
                "rows": [
                    ["Stud Group 1", 38, 65, "PASS"]
                ],
            },
        },

        "design_summary": {

            "design_results_summary": {
                "id": "design_results_summary",
                "label": "Design Results Summary",
                "columns": [
                    "Member",
                    "Check Name",
                    "Demand",
                    "Capacity",
                    "DCR",
                    "Status",
                ],
                "rows": [
                    ["Girder 1", "Flexural Resistance", 9250, 12800, 0.72, "PASS"],
                    ["Girder 1", "Shear Resistance", 1420, 1850, 0.77, "PASS"],
                    ["Girder 1", "Live Load Deflection", 28, "L/800", "-", "PASS"],
                ],
            },
        },
    },
}