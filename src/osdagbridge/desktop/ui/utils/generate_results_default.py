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
                    [12.50, 30.00, 4, 3.00, 0.75, 0],
                    [12.50, 30.00, 4, 3.00, 0.75, 0],
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
                    ["Girder",    "E350", 490, 350, 200000, 76900, 0.30, 12e-6],
                    ["Cross Bracing",       "E350", 490, 350, 200000, 76900, 0.30, 12e-6],
                    ["End Diagram",       "E350", 490, 350, 200000, 76900, 0.30, 12e-6],
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
                    ["Girder",    "M40", 40, 3.5, 34000, 6.0, 25.0, 0.20],
                    ["Cross Bracing",     "M35", 35, 3.2, 32000, 6.5, 25.0, 0.20],
                    ["End Diaphram",     "M30", 30, 2.9, 30000, 7.0, 25.0, 0.20],
                ],
            },
        },

        "load_definitions": {

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
                    [55.0, 8.5, 12.0, 75.5],
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
                    ["Class A",     1.10],
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
                    [39, 42, 1100, 1.8, 0.75, 2.0],
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
                    ["III", 0.16, 1.0, 2.5, 0.08, 0.04],
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
                    [45, 5, 18, -20],
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
                    ["X-Bracing", "ISA100x100x10", 5.0],
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
                    ["Plate Girder", "PL 500x12"],
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
                    [20, 100, 495, 385, 2],
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
                    [220, "16@150", "12@200", 40, 30],
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
                    "Maximum Bending Moment, Mₘₐₓ (kNm)",
                    "Minimum Bending Moment, Mₘᵢₙ (kNm)",
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
                    "Maximum Shear Force, Vₘₐₓ (kN)",
                    "Minimum Shear Force, Vₘᵢₙ (kN)",
                ],
                "rows": [
                    ["Girder 1", 1420, -310],
                    ["Girder 2", 1395, -300],
                    ["Girder 3", 1395, -300],
                    ["Girder 4", 1420, -310],
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
                    ["Girder 1", 2850, 450, 950, 4200, 120, 180, 250],
                    ["Girder 2", 2800, 440, 930, 4100, 115, 175, 240],
                    ["Girder 3", 2800, 440, 930, 4100, 115, 175, 240],
                    ["Girder 4", 2850, 450, 950, 4200, 120, 180, 250],
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
                    ["Girder 1", 440, 70, 150, 680, 25, 40, 50],
                    ["Girder 2", 430, 68, 145, 665, 24, 38, 48],
                    ["Girder 3", 430, 68, 145, 665, 24, 38, 48],
                    ["Girder 4", 440, 70, 150, 680, 25, 40, 50],
                ],
            },
        },

        "deflections": {

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
                    "Total Deflection, δₜₒₜₐₗ (mm)",
                    "Permissible Limit",
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
                    "Stress in Concrete, σc (MPa)",
                    "Allowable Stress (MPa)",
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
                    "Stress in Reinforcement, σᵣₑᵢₙf (MPa)",
                    "Allowable Stress (MPa)",
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
                    "Ultimate Bending Moment, Mᵤ (kNm)",
                    "Design Bending Moment, Mᵈ (kNm)",
                    "Demand to Capacity Ratio, DCR",
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
                    "Ultimate Shear Force, Vᵤ (kN)",
                    "Design Shear Force, Vᵈ (kN)",
                    "Demand to Capacity Ratio, DCR",
                    "Status",
                ],
                "rows": [
                    ["Girder 1", 1420, 1850, 0.77, "PASS"],
                    ["Girder 2", 1395, 1850, 0.75, "PASS"],
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
                    ["Girder 1", 9250, 11200, 0.83, "IRC 22 Cl. 603.3.3.3", "PASS"],
                    ["Girder 2", 9100, 11200, 0.81, "IRC 22 Cl. 603.3.3.3", "PASS"],
                    ["Girder 3", 9100, 11200, 0.81, "IRC 22 Cl. 603.3.3.3", "PASS"],
                    ["Girder 4", 9250, 11200, 0.83, "IRC 22 Cl. 603.3.3.3", "PASS"],
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
                    ["Girder 1", 4100, 9800, 0.78, 0.62, 0.42, "IRC 22 Cl. 603.3.3.1", "PASS"],
                    ["Girder 2", 4050, 9800, 0.78, 0.62, 0.41, "IRC 22 Cl. 603.3.3.1", "PASS"],
                    ["Girder 3", 4050, 9800, 0.78, 0.62, 0.41, "IRC 22 Cl. 603.3.3.1", "PASS"],
                    ["Girder 4", 4100, 9800, 0.78, 0.62, 0.42, "IRC 22 Cl. 603.3.3.1", "PASS"],
                ],
            },
        },

        "sls_checks": {

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
                    ["Girder 1", 28, "L/800", "PASS"],
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
                    ["Girder 1", 42, 30000, 50.0, "IRC 22 Cl. 604.3.2", "PASS"],
                    ["Girder 2", 41, 30000, 50.0, "IRC 22 Cl. 604.3.2", "PASS"],
                    ["Girder 3", 41, 30000, 50.0, "IRC 22 Cl. 604.3.2", "PASS"],
                    ["Girder 4", 42, 30000, 50.0, "IRC 22 Cl. 604.3.2", "PASS"],
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
                    ["Girder 1", 72, 110, "PASS"],
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
                    ["Stud Group 1", 38, 65, "PASS"],
                ],
            },
        },
        "shear_connector_design": {

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
                    ["Girder 1", 1420, 167.4, 118, 7840, 145, 118, "IRC 22 Cl. 606.4.1"],
                    ["Girder 2", 1395, 167.4, 120, 7840, 145, 120, "IRC 22 Cl. 606.4.1"],
                    ["Girder 3", 1395, 167.4, 120, 7840, 145, 120, "IRC 22 Cl. 606.4.1"],
                    ["Girder 4", 1420, 167.4, 118, 7840, 145, 118, "IRC 22 Cl. 606.4.1"],
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
                    ["Girder 1", 420, 52.4, 2, 250, "IRC 22 Cl. 606.4.2"],
                    ["Girder 2", 410, 52.4, 2, 256, "IRC 22 Cl. 606.4.2"],
                    ["Girder 3", 410, 52.4, 2, 256, "IRC 22 Cl. 606.4.2"],
                    ["Girder 4", 420, 52.4, 2, 250, "IRC 22 Cl. 606.4.2"],
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
                    ["Girder 1", 118, 250, 118, 600, 660, 400, 400, "PASS"],
                    ["Girder 2", 120, 256, 120, 600, 660, 400, 400, "PASS"],
                    ["Girder 3", 120, 256, 120, 600, 660, 400, 400, "PASS"],
                    ["Girder 4", 118, 250, 118, 600, 660, 400, 400, "PASS"],
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
                    ["Girder 1", 20, 25, "20 ≤ 50 ✓", 100, "100 ≥ 80 ✓", 42, 25, 35, 30, "IRC 22 Cl. 606.6", "PASS"],
                    ["Girder 2", 20, 25, "20 ≤ 50 ✓", 100, "100 ≥ 80 ✓", 42, 25, 35, 30, "IRC 22 Cl. 606.6", "PASS"],
                    ["Girder 3", 20, 25, "20 ≤ 50 ✓", 100, "100 ≥ 80 ✓", 42, 25, 35, 30, "IRC 22 Cl. 606.6", "PASS"],
                    ["Girder 4", 20, 25, "20 ≤ 50 ✓", 100, "100 ≥ 80 ✓", 42, 25, 35, 30, "IRC 22 Cl. 606.6", "PASS"],
                ],
            },
        },
        "transverse_and_crack_checks": {

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
                    ["Girder 1", 0.22, 0.30, 1050, 1340, 16, 150, "IRC 22 Cl. 604.4", "PASS"],
                    ["Girder 2", 0.21, 0.30, 1050, 1340, 16, 150, "IRC 22 Cl. 604.4", "PASS"],
                    ["Girder 3", 0.21, 0.30, 1050, 1340, 16, 150, "IRC 22 Cl. 604.4", "PASS"],
                    ["Girder 4", 0.22, 0.30, 1050, 1340, 16, 150, "IRC 22 Cl. 604.4", "PASS"],
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
                    "Demand (Units as applicable)",
                    "Capacity (Units as applicable)",
                    "Demand to Capacity Ratio, DCR",
                    "Status",
                ],
                "rows": [
                    ["Girder 1", "Flexural Resistance", 9250, 12800, 0.72, "PASS"],
                    ["Girder 1", "Shear Resistance",    1420, 1850,  0.77, "PASS"],
                    ["Girder 1", "Live Load Deflection", 28, "L/800", "-", "PASS"],
                ],
            },
        },
    },
}