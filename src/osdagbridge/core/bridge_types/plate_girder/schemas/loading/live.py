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
            "conditions": [{"when": "footpath_mode_combo", "equals": "User-defined", "action": "enable"}],
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
