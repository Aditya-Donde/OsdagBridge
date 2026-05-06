CUSTOM_LOAD_TAB_SCHEMA = {
    "id": "custom_load_tab",
    "label_width": 260,
    "field_width": 140,
    "description": {"title": "Description Box", "text": "", "hide_when_empty": False, "min_height": 480},
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
    "layout": {
        "type": "split",
        "spacing": 12,
        "fill_height": True,
        "left": {
            "type": "stack",
            "stretch": 3,
            "spacing": 8,
            "children": [
                {
                    "sections": [
                        {
                            "id": "custom_load_diagram",
                            "type": "diagram",
                            "text": "Bridge Geometry\nDiagram",
                            "min_size": [380, 130],
                            "max_height": 130,
                            "bind": "custom_load_diagram_placeholder",
                        },
                    ],
                    "boxed_fallback": False,
                },
                {
                    "type": "stack",
                    "spacing": 8,
                    "children": [
                        {
                            "type": "card",
                            "title": "Custom Load Input Add/Edit:",
                            "label_width": 220,
                            "field_width": 140,
                            "stretch": 3,
                            "sections": [
                        {
                            "id": "custom_load_case_section",
                            "boxed": False,
                            "fields": [
                                {
                                    "row_fields": [
                                        {"label": "Load Case", "type": "label", "width": 220},
                                        {
                                            "id": "custom_load_case",
                                            "type": "combo",
                                            "choices": ["DL", "DW", "SIDL", "LL", "EL", "WL", "TL", "Custom"],
                                            "default": "DL",
                                            "bind": "custom_load_case_combo",
                                            "on_change": "_on_load_case_changed",
                                        },
                                        {
                                            "id": "custom_load_case_name",
                                            "type": "line",
                                            "placeholder": "Custom",
                                            "bind": "custom_load_case_name_input",
                                            "enabled": False,
                                            "width": 140,
                                            "conditions": [{"when": "custom_load_case_combo", "equals": "Custom", "action": "enable"}],
                                        },
                                    ],
                                },
                                {
                                    "row_fields": [
                                        {"label": "Load Type", "type": "label", "width": 220},
                                        {
                                            "id": "custom_load_type",
                                            "type": "combo",
                                            "choices": ["Point", "Line", "Area"],
                                            "default": "Point",
                                            "bind": "custom_load_type_combo",
                                            "on_change": "_on_custom_load_type_changed",
                                            "width": 288,
                                        },
                                    ],
                                },
                            ],
                        },
                        {
                            "id": "custom_load_stack_section",
                            "type": "stacked",
                            "bind": "custom_load_stack",
                            "switch_source": "custom_load_type_combo",
                            "max_height": 130,
                            "size_policy": "fixed",
                            "pages": [
                                {
                                    "match": "Point",
                                    "sections": [
                                        {
                                            "boxed": False,
                                            "label_width": 220,
                                            "field_width": 220,
                                            "fields": [
                                                {
                                                    "id": "custom_point_left",
                                                    "label": "Distance from Left Edge (m)",
                                                    "type": "line",
                                                    "bind": "custom_point_left_input",
                                                    "validator": {"type": "double_range", "bottom": 0.0, "top": 1000.0, "decimals": 3},
                                                },
                                                {
                                                    "id": "custom_point_bearing",
                                                    "label": "Distance from Bearing CL (m)",
                                                    "type": "line",
                                                    "bind": "custom_point_bearing_input",
                                                    "validator": {"type": "double_range", "bottom": -1000.0, "top": 1000.0, "decimals": 3},
                                                },
                                            ],
                                        },
                                    ],
                                },
                                {
                                    "match": "Line",
                                    "sections": [
                                        {
                                            "id": "custom_line_left_range",
                                            "title": "Distance from Left Edge of Bridge (m):",
                                            "boxed": False,
                                            "fields": [
                                                {
                                                    "row_fields": [
                                                        {"label": "Start", "type": "label"},
                                                        {
                                                            "id": "custom_line_left_start",
                                                            "type": "line",
                                                            "bind": "custom_line_left_start",
                                                            "width": 110,
                                                            "validator": {"type": "double_range", "bottom": 0.0, "top": 1000.0, "decimals": 3},
                                                        },
                                                        {"label": "End", "type": "label"},
                                                        {
                                                            "id": "custom_line_left_end",
                                                            "type": "line",
                                                            "bind": "custom_line_left_end",
                                                            "width": 110,
                                                            "validator": {"type": "double_range", "bottom": 0.0, "top": 1000.0, "decimals": 3},
                                                        },
                                                    ]
                                                }
                                            ],
                                        },
                                        {
                                            "id": "custom_line_bearing_range",
                                            "title": "Distance from Center Line of Bearing (m):",
                                            "boxed": False,
                                            "fields": [
                                                {
                                                    "row_fields": [
                                                        {"label": "Start", "type": "label"},
                                                        {
                                                            "id": "custom_line_bearing_start",
                                                            "type": "line",
                                                            "bind": "custom_line_bearing_start",
                                                            "width": 110,
                                                            "validator": {"type": "double_range", "bottom": -1000.0, "top": 1000.0, "decimals": 3},
                                                        },
                                                        {"label": "End", "type": "label"},
                                                        {
                                                            "id": "custom_line_bearing_end",
                                                            "type": "line",
                                                            "bind": "custom_line_bearing_end",
                                                            "width": 110,
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
                                            "boxed": False,
                                            "fields": [
                                                {
                                                    "row_fields": [
                                                        {"label": "Start", "type": "label"},
                                                        {
                                                            "id": "custom_area_left_start",
                                                            "type": "line",
                                                            "bind": "custom_area_left_start",
                                                            "width": 110,
                                                            "validator": {"type": "double_range", "bottom": 0.0, "top": 1000.0, "decimals": 3},
                                                        },
                                                        {"label": "End", "type": "label"},
                                                        {
                                                            "id": "custom_area_left_end",
                                                            "type": "line",
                                                            "bind": "custom_area_left_end",
                                                            "width": 110,
                                                            "validator": {"type": "double_range", "bottom": 0.0, "top": 1000.0, "decimals": 3},
                                                        },
                                                    ]
                                                }
                                            ],
                                        },
                                        {
                                            "id": "custom_area_bearing_range",
                                            "title": "Distance from Center Line of Bearing (m):",
                                            "boxed": False,
                                            "fields": [
                                                {
                                                    "row_fields": [
                                                        {"label": "Start", "type": "label"},
                                                        {
                                                            "id": "custom_area_bearing_start",
                                                            "type": "line",
                                                            "bind": "custom_area_bearing_start",
                                                            "width": 110,
                                                            "validator": {"type": "double_range", "bottom": -1000.0, "top": 1000.0, "decimals": 3},
                                                        },
                                                        {"label": "End", "type": "label"},
                                                        {
                                                            "id": "custom_area_bearing_end",
                                                            "type": "line",
                                                            "bind": "custom_area_bearing_end",
                                                            "width": 110,
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
                            "boxed": False,
                            "rows": [
                                {
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
                            ],
                        },
                            ],
                        },
                        {
                            "sections": [
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
                            "boxed_fallback": False,
                            "stretch": 2,
                        },
                    ],
                },
            ],
        },
        "right": {
            "type": "description",
            "stretch": 2,
            "description": {"title": "Description Box", "text": "", "hide_when_empty": False, "min_height": 480},
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
                    "conditions": [{"when": "custom_load_case_combo", "equals": "Custom", "action": "enable"}],
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
                                            "bind": "custom_area_left_start",
                                            "width": 70,
                                            "validator": {"type": "double_range", "bottom": 0.0, "top": 1000.0, "decimals": 3},
                                        },
                                        {"label": "End", "type": "label"},
                                        {
                                            "id": "custom_area_left_end",
                                            "type": "line",
                                            "bind": "custom_area_left_end",
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
                                            "bind": "custom_area_bearing_start",
                                            "width": 70,
                                            "validator": {"type": "double_range", "bottom": -1000.0, "top": 1000.0, "decimals": 3},
                                        },
                                        {"label": "End", "type": "label"},
                                        {
                                            "id": "custom_area_bearing_end",
                                            "type": "line",
                                            "bind": "custom_area_bearing_end",
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
