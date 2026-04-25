PERMANENT_LOAD_TAB_SCHEMA = {
    "id": "permanent_load_tab",
    "label_width": 220,
    "description": {"title": "Description Box", "text": ""},
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
            "label_bind": "irc_vehicle_labels",
            "default_checked": True,
        },
        {
            "id": "custom_vehicle_section",
            "title": "Custom Vehicle",
            "type": "custom_vehicle_table",
            "bind": "custom_vehicle_table",
            "add_button_bind": "custom_vehicle_add_button",
            "frame_bind": "custom_vehicle_box",
            "header_label_bind": "custom_vehicle_header_label",
        },
        {
            "id": "braking_section",
            "title": "Braking Load from Vehicles",
            "type": "dynamic_checkbox_list",
            "bind": "braking_vehicle_checkboxes",
            "layout_bind": "braking_checkboxes_layout",
            "title_bind": "braking_section_label",
            "label_bind": "braking_vehicle_labels",
            "container_bind": "braking_checkboxes_container",
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
                    "default_value": "",
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
                    "default_value": "",
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
                    "default_value": "",
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
                    "default_value": "",
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
                    "default_value": "",
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
                    "default_value": "",
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
    "description": {"title": "Description Box", "text": ""},
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
    "description": {"title": "Description Box", "text": ""},
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
            "label": "",
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
    "sections": [
        {
            "id": "custom_load_diagram",
            "type": "diagram",
            "text": "Bridge Geometry\nDiagram",
            "min_size": [380, 130],
            "max_height": 130,
            "bind": "custom_load_diagram_placeholder",
        },
        {
            "id": "custom_load_case_section",
            "title": "Custom Load Input Add/Edit:",
            "fields": [
                {
                    "id": "custom_load_case",
                    "label": "Load Case",
                    "type": "combo",
                    "choices": ["DL", "DW", "SIDL", "LL", "EL", "WL", "TL", "Custom"],
                    "default": "DL",
                    "bind": "custom_load_case_combo",
                    "on_change": "_on_load_case_changed",
                },
                {
                    "id": "custom_load_case_name",
                    "label": "Custom Load Name",
                    "type": "line",
                    "placeholder": "Custom",
                    "bind": "custom_load_case_name_input",
                    "enabled": False,
                },
                {
                    "id": "custom_load_type",
                    "label": "Load Type",
                    "type": "combo",
                    "choices": ["Point", "Line", "Area"],
                    "default": "Point",
                    "bind": "custom_load_type_combo",
                    "on_change": "_on_custom_load_type_changed",
                },
            ],
        },
        {
            "id": "custom_load_stack_section",
            "type": "stacked",
            "bind": "custom_load_stack",
            "switch_source": "custom_load_type_combo",
            "pages": [
                {
                    "match": "Point",
                    "sections": [
                        {
                            "id": "custom_point_left",
                            "label": "Distance from Left Edge of Bridge (m)",
                            "type": "line",
                            "bind": "custom_point_left_input",
                            "validator": {"type": "double_range", "bottom": 0.0, "top": 1000.0, "decimals": 3},
                        },
                        {
                            "id": "custom_point_bearing",
                            "label": "Distance from Center Line of Bearing (m)",
                            "type": "line",
                            "bind": "custom_point_bearing_input",
                            "validator": {"type": "double_range", "bottom": -1000.0, "top": 1000.0, "decimals": 3},
                        },
                    ],
                },
                {
                    "match": "Line",
                    "sections": [
                        {
                            "id": "custom_line_left_range",
                            "title": "Distance from Left Edge of Bridge (m):",
                            "fields": [
                                {
                                    "row_fields": [
                                        {"label": "Start", "type": "label"},
                                        {
                                            "id": "custom_line_left_start",
                                            "type": "line",
                                            "bind": "custom_line_left_start",
                                            "width": 70,
                                            "validator": {"type": "double_range", "bottom": 0.0, "top": 1000.0, "decimals": 3},
                                        },
                                        {"label": "End", "type": "label"},
                                        {
                                            "id": "custom_line_left_end",
                                            "type": "line",
                                            "bind": "custom_line_left_end",
                                            "width": 70,
                                            "validator": {"type": "double_range", "bottom": 0.0, "top": 1000.0, "decimals": 3},
                                        },
                                    ]
                                }
                            ],
                        },
                        {
                            "id": "custom_line_bearing_range",
                            "title": "Distance from Center Line of Bearing (m):",
                            "fields": [
                                {
                                    "row_fields": [
                                        {"label": "Start", "type": "label"},
                                        {
                                            "id": "custom_line_bearing_start",
                                            "type": "line",
                                            "bind": "custom_line_bearing_start",
                                            "width": 70,
                                            "validator": {"type": "double_range", "bottom": -1000.0, "top": 1000.0, "decimals": 3},
                                        },
                                        {"label": "End", "type": "label"},
                                        {
                                            "id": "custom_line_bearing_end",
                                            "type": "line",
                                            "bind": "custom_line_bearing_end",
                                            "width": 70,
                                            "validator": {"type": "double_range", "bottom": -1000.0, "top": 1000.0, "decimals": 3},
                                        },
                                    ]
                                }
                            ],
                        },
                    ],
                },
                {
                    "match": "Area",
                    "sections": [
                        {
                            "id": "custom_area_left_range",
                            "title": "Distance from Left Edge of Bridge (m):",
                            "fields": [
                                {
                                    "row_fields": [
                                        {"label": "Start", "type": "label"},
                                        {
                                            "id": "custom_area_left_start",
                                            "type": "line",
                                            "bind": "custom_line_left_start",
                                            "width": 70,
                                            "validator": {"type": "double_range", "bottom": 0.0, "top": 1000.0, "decimals": 3},
                                        },
                                        {"label": "End", "type": "label"},
                                        {
                                            "id": "custom_area_left_end",
                                            "type": "line",
                                            "bind": "custom_line_left_end",
                                            "width": 70,
                                            "validator": {"type": "double_range", "bottom": 0.0, "top": 1000.0, "decimals": 3},
                                        },
                                    ]
                                }
                            ],
                        },
                        {
                            "id": "custom_area_bearing_range",
                            "title": "Distance from Center Line of Bearing (m):",
                            "fields": [
                                {
                                    "row_fields": [
                                        {"label": "Start", "type": "label"},
                                        {
                                            "id": "custom_area_bearing_start",
                                            "type": "line",
                                            "bind": "custom_line_bearing_start",
                                            "width": 70,
                                            "validator": {"type": "double_range", "bottom": -1000.0, "top": 1000.0, "decimals": 3},
                                        },
                                        {"label": "End", "type": "label"},
                                        {
                                            "id": "custom_area_bearing_end",
                                            "type": "line",
                                            "bind": "custom_line_bearing_end",
                                            "width": 70,
                                            "validator": {"type": "double_range", "bottom": -1000.0, "top": 1000.0, "decimals": 3},
                                        },
                                    ]
                                }
                            ],
                        },
                    ],
                },
            ],
        },
        {
            "id": "custom_load_save_section",
            "fields": [
                {
                    "id": "custom_load_save",
                    "label": "",
                    "type": "button",
                    "text": "Save",
                    "bind": "custom_save_btn",
                    "on_click": "_on_save_custom_load",
                    "width": 120,
                },
            ],
        },
        {
            "id": "custom_load_table",
            "title": "Custom Load Name",
            "type": "custom_load_combo_table",
            "bind": "custom_load_table",
            "add_button_bind": "custom_load_table_add_btn",
            "edit_button_bind": "custom_edit_btn",
            "delete_button_bind": "custom_delete_btn",
            "title_bind": "custom_load_table_title",
            "columns": ["Load Case", "Load Type", "Distance 1", "Distance 2"],
            "min_table_height": 180,
        },
    ],
}

LOAD_COMBINATION_TAB_SCHEMA = {
    "id": "load_combination_tab",
    "label_width": 280,
    "description": {"title": "Description Box", "text": ""},
    "sections": [
        {
            "id": "irc_load_combos_section",
            "title": "Load Combinations from IRC 6",
            "type": "dynamic_checkbox_list",
            "bind": "irc_load_combos_checkboxes",
            "layout_bind": "irc_content_layout",
            "title_bind": "irc_load_combos_title",
            "default_checked": False,
        },
        {
            "id": "custom_load_combo_section",
            "title": "Custom Load Combination",
            "type": "custom_load_combo_table",
            "bind": "custom_load_combo_table",
            "columns": ["S.No.", "Combination Name", "Include"],
            "add_button_bind": "load_combo_add_btn",
            "add_button_text": "Add Custom Combination",
            "edit_button_bind": "load_combo_edit_btn",
            "edit_button_text": "Modify",
            "delete_button_bind": "load_combo_delete_btn",
            "delete_button_text": "Delete",
            "title_bind": "custom_combo_title",
            "min_table_height": 180,
        },
    ],
}
