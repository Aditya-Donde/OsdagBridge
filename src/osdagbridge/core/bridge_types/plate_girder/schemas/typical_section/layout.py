from osdagbridge.core.utils.common import DEFAULT_GIRDER_SPACING

LAYOUT_TAB_SCHEMA = {
    "id": "layout_tab",
    "label_width": 190,
    "field_width": 180,
    "row_vertical_spacing": 14,
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
                    "on_editing_finished": "on_no_of_girders_changed",
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
                    "default": f"{0.35 * DEFAULT_GIRDER_SPACING:.3f}",
                    "bind": "deck_overhang",
                    "on_text_changed": "on_deck_overhang_changed",
                },
                {
                    "id": "overall_bridge_width_display",
                    "label": "Overall Bridge Width (m):",
                    "type": "computed",
                    "enabled": False,
                    "bind": "overall_bridge_width_display",
                    "on_text_changed": "_reject_overall_width_override",
                },
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
                    "validator": {"type": "double_range", "bottom": 1.5, "top": 5.0, "decimals": 3},
                    "default": "1.50",
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
