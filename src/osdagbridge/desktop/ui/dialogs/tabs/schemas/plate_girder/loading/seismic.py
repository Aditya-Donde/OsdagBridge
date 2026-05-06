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
                    "validator": {"type": "double_range", "bottom": 0.1, "top": 10.0, "decimals": 2},
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
                    "default": "Type I – Rocky or Hard",
                    "bind": "soil_type_combo",
                },
                {
                    "id": "time_period",
                    "label": "Fundamental Time Period, T (sec)",
                    "type": "line",
                    "validator": {"type": "double_range", "bottom": 0.01, "top": 100.0, "decimals": 3},
                    "bind": "time_period_input",
                },
                {
                    "id": "damping",
                    "label": "Damping Percentage",
                    "type": "line",
                    "default": "2",
                    "validator": {"type": "double_range", "bottom": 0.0, "top": 100.0, "decimals": 2},
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
                    "validator": {"type": "double_range", "bottom": 0.0, "top": 1.0e9, "decimals": 3},
                    "conditions": [{"when": "dead_load_seismic_combo", "equals": "Custom", "action": "enable"}],
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
                    "validator": {"type": "double_range", "bottom": 0.0, "top": 1.0e9, "decimals": 3},
                    "conditions": [{"when": "live_load_seismic_combo", "equals": "Custom", "action": "enable"}],
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
