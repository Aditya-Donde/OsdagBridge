"""Module-level constants for the schema-driven UI builder.

Style strings, default sizes, schema-type dispatch tables, and a
sentinel object used by bind-overwrite detection. Kept in one place so
the mixin modules don't each carry their own copies.
"""

_MISSING = object()  # sentinel for bind-overwrite detection

# Schema "type" → builder method name on UIBuilder.
# Add a new entry here + a build_*() method to support a new field type.
_TYPE_TO_METHOD: dict[str, str] = {
    "line":             "build_line_edit",
    "number":           "build_line_edit",
    "computed":         "build_computed",
    "combo":            "build_combo",
    "combo_dynamic":    "build_combo",
    "checkbox":         "build_checkbox",
    "label":            "build_label",
    "button":           "build_button",
    "mode_line":        "build_mode_line",
    "mode_value":       "build_mode_line",
    "line_with_bounds": "build_line_with_bounds",
}

# Section types whose dedicated builder returns a styled QFrame on its own;
# the outer card wrapper is skipped.
_SPECIAL_SECTION_TYPES = {
    "checkbox_list",
    "custom_vehicle_table",
    "dynamic_checkbox_list",
    "custom_load_combo_table",
    "cad",
    "cad_row",
    "legend",
    "stacked",
    "diagram",
    "tab_container",
    "input_group",
    "computed_group",
    "output_group",
    "section_box",
}

# Section types where the section dict IS the field definition
# (e.g. eccentricity / footpath_pressure in LIVE_LOAD_TAB_SCHEMA).
_FIELD_AS_SECTION_TYPES = set(_TYPE_TO_METHOD)

_LEGACY_FIELD_LIST_KEYS = ("section_inputs", "stiffener_inputs", "web_buckling_inputs")

_DEFAULT_LABEL_WIDTH = 180
_DEFAULT_FIELD_WIDTH = 180

_HEADING_STYLE = "font-size: 12px; font-weight: 700; color: #2b2b2b; background: transparent; border: none;"
_LABEL_STYLE   = "font-size: 11px; color: #3a3a3a; background: transparent; border: none;"

_CARD_STYLE = """
    QFrame {
        border: 1px solid #b2b2b2;
        border-radius: 8px;
        background-color: #ffffff;
    }
    QFrame QLabel {
        background: transparent;
        border: none;
        border-radius: 0;
        padding: 0;
    }
"""

_SECTION_BOX_STYLE = """
    QFrame {
        border: 1px solid #9c9c9c;
        border-radius: 6px;
        background-color: #ffffff;
    }
    QFrame QLabel {
        background: transparent;
        border: none;
    }
"""

_RIGHT_CARD_STYLE = """
    QFrame {
        border: 1px solid #9c9c9c;
        border-radius: 10px;
        background-color: #d4d4d4;
    }
    QFrame QLabel {
        background: transparent;
        border: none;
    }
"""
