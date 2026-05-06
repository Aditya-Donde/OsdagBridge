from osdagbridge.core.utils.common import (
    KEY_END_DIAPHRAGM_SECTION,
    KEY_END_DIAPHRAGM_TYPE,
    VALUES_END_DIAPHRAGM_TYPE,
    VALUES_GIRDER_DESIGN_MODE,
    VALUES_GIRDER_SYMMETRY,
)

END_DIAPHRAGM_DETAILS_SCHEMA = {
    "id": "end_diaphragm_details_tab",
    "sections": [
        {
            "id": "selector_section",
            "rows": [
                [
                    {
                        "id": "type_selector",
                        "label": "Type:",
                        "type": "combo",
                        "choices": VALUES_END_DIAPHRAGM_TYPE,
                        "default": "Cross Bracing",
                        "bind": "type_selector_combo",
                        "input_key": KEY_END_DIAPHRAGM_TYPE,
                    },
                    {
                        "id": "select_girders",
                        "label": "Select Girders:",
                        "type": "combo_dynamic",
                        "bind": "select_girders_combo",
                        "on_change": "_on_girder_pair_changed",
                    }
                ]
            ]
        },
        {
            "id": "view_stack",
            "type": "stacked",
            "switch_source": "type_selector_combo",
            "pages": [
                {
                    "match": "Cross Bracing",
                    "sections": [
                        {
                            "id": "cross_bracing_cad",
                            "type": "cad",
                            "widget": "BracingLayoutCadWidget",
                            "bind": "cross_bracing_cad_preview",
                            "update_method": "set_layout",
                            "min_height": 200,
                        },
                        {
                            "id": "cross_section_inputs",
                            "title": "Section Inputs:",
                            "fields": [
                                {
                                    "id": "design",
                                    "label": "Design:",
                                    "type": "combo",
                                    "choices": VALUES_GIRDER_DESIGN_MODE,
                                    "default": "Optimized",
                                    "bind": "cross_design_combo",
                                },
                                {
                                    "id": "bracing_type",
                                    "label": "Type of Bracing:",
                                    "type": "combo",
                                    "choices": ["K-Bracing", "X-Bracing"],
                                    "bind": "cross_bracing_type_combo",
                                },
                                {
                                    "id": "bracing_section_type",
                                    "label": "Bracing Section Type:",
                                    "type": "combo",
                                    "choices": [
                                        "Angle",
                                        "Double Angle (Long Leg)",
                                        "Double Angle (Short Leg)",
                                        "Channel",
                                        "Double Channel",
                                    ],
                                    "bind": "cross_bracing_section_type_combo",
                                },
                                {
                                    "id": "bracing_section",
                                    "label": "Bracing Section Designation:",
                                    "type": "combo_dynamic",
                                    "bind": "cross_bracing_section_combo",
                                    "input_key": KEY_END_DIAPHRAGM_SECTION,
                                },
                                {
                                    "id": "top_chord_enabled",
                                    "label": "Top Chord:",
                                    "type": "checkbox",
                                    "default": False,
                                    "bind": "cross_top_chord_checkbox",
                                },
                                {
                                    "id": "top_chord_type",
                                    "label": "Top Chord Section Type:",
                                    "type": "combo",
                                    "choices": [
                                        "Angle",
                                        "Double Angle (Long Leg)",
                                        "Double Angle (Short Leg)",
                                        "Channel",
                                        "Double Channel",
                                    ],
                                    "bind": "cross_top_chord_type_combo",
                                },
                                {
                                    "id": "top_chord_size",
                                    "label": "Top Chord Section Designation:",
                                    "type": "combo_dynamic",
                                    "bind": "cross_top_chord_size_combo",
                                },
                                {
                                    "id": "bottom_chord_enabled",
                                    "label": "Bottom Chord:",
                                    "type": "checkbox",
                                    "default": True,
                                    "bind": "cross_bottom_chord_checkbox",
                                },
                                {
                                    "id": "bottom_chord_type",
                                    "label": "Bottom Chord Section Type:",
                                    "type": "combo",
                                    "choices": [
                                        "Angle",
                                        "Double Angle (Long Leg)",
                                        "Double Angle (Short Leg)",
                                        "Channel",
                                        "Double Channel",
                                    ],
                                    "bind": "cross_bottom_chord_type_combo",
                                },
                                {
                                    "id": "bottom_chord_size",
                                    "label": "Bottom Chord Section Designation:",
                                    "type": "combo_dynamic",
                                    "bind": "cross_bottom_chord_size_combo",
                                },
                            ],
                        }
                    ]
                },
                {
                    "match": "Rolled Beam",
                    "sections": [
                        {
                            "id": "rolled_design_section",
                            "fields": [
                                {
                                    "id": "design",
                                    "label": "Design:",
                                    "type": "combo",
                                    "choices": VALUES_GIRDER_DESIGN_MODE,
                                    "default": "Optimized",
                                    "bind": "rolled_design_combo",
                                },
                                {
                                    "id": "is_section",
                                    "label": "IS Section:",
                                    "type": "combo_dynamic",
                                    "bind": "rolled_is_section_combo",
                                    "input_key": KEY_END_DIAPHRAGM_SECTION,
                                },
                            ]
                        }
                    ]
                },
                {
                    "match": "Welded Beam",
                    "sections": [
                        {
                            "id": "welded_design_section",
                            "fields": [
                                {
                                    "id": "design",
                                    "label": "Design:",
                                    "type": "combo",
                                    "choices": VALUES_GIRDER_DESIGN_MODE,
                                    "default": "Optimized",
                                    "bind": "welded_design_combo",
                                },
                                {
                                    "id": "symmetry",
                                    "label": "Symmetry:",
                                    "type": "combo",
                                    "choices": VALUES_GIRDER_SYMMETRY,
                                    "bind": "welded_symmetry_combo",
                                },
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}
