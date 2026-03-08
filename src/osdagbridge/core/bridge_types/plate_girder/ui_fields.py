from osdagbridge.core.utils.common import *
from osdagbridge.core.bridge_types.plate_girder.defaults import DEFAULTS_DICT

"""
Field definition tuple schema:
    (key, display_label, ui_type, values, is_visible, validator, ui_config_dict)

ui_type values:
    TYPE_MODULE   → module marker, skipped by dock
    TYPE_TITLE    → opens a new QGroupBox section
    TYPE_COMBOBOX → dropdown field
    TYPE_TEXTBOX  → text/numeric input field
    TYPE_BUTTON   → action button row
    TYPE_NOTE     → hidden label, shown/hidden by domain logic

ui_config_dict recognised keys:
    # Layout / container
    container           : "main" | "superstructure" | ...
    show_group_title    : bool (default True) — for TYPE_TITLE only
    container_label     : str  — display name for the collapsible wrapper
    add_stretch         : bool — adds stretch after widget in the row

    # Initial value
    default             : initial widget value — single source of truth

    # TYPE_TEXTBOX — placeholder
    placeholder         : str  — static placeholder text
    placeholder_dynamic : str  — name of an InputDock method that returns
                                  the placeholder string; called on init and
                                  whenever a dependency changes.
                                  e.g. "_carriageway_placeholder_text"

    # TYPE_TEXTBOX — callbacks
    on_editing_finished : str | list[str] — InputDock method name(s) called
                          on editingFinished signal

    # TYPE_COMBOBOX — behaviour
    disabled_options    : list[str] — option text values that are greyed-out
                          and non-selectable in the dropdown
    is_material_field   : bool — enables Custom material flow + info (ℹ) button
    member_type         : "Girder" | "Deck" — used when is_material_field=True
                          to route MaterialPropertiesDialog + sync logic

    # TYPE_COMBOBOX — callbacks
    on_changed          : str | list[str] — InputDock method name(s) connected
                          to currentTextChanged signal
    trigger_on_init     : bool — fire on_changed handler(s) once on widget
                          creation with the initial value (default False)

    # TYPE_BUTTON
    action              : str  — InputDock method name called on click
    button_label        : str  — button face text (default "Modify Here")

    # TYPE_NOTE
    attr                : str  — attribute name to set on InputDock so domain
                          logic can call .setVisible() on the label
"""


class FrontendData:
    """Backend state store for Highway Bridge Design."""

    def __init__(self):
        self.module_key           = KEY_MODULE_PLATE_GIRDER
        self.design_status        = False
        self.design_button_status = False
        self._input_state:  dict[str, object] = {}
        self._output_state: dict[str, object] = {}

    # ── State getters / setters ───────────────────────────────────────────────

    def set_input_value(self, key: str, value):
        if key:
            self._input_state[key] = value

    def get_input_value(self, key: str, default=None):
        return self._input_state.get(key, default) if key else default

    def set_output_value(self, key: str, value):
        if key:
            self._output_state[key] = value

    def get_output_value(self, key: str, default=None):
        return self._output_state.get(key, default) if key else default

    def set_final_design_inputs(self, final_inputs: list[dict]) -> None:
        if isinstance(final_inputs, list):
            self._input_state["final_design_inputs"] = final_inputs

    # ── UI field definitions ──────────────────────────────────────────────────

    def input_values(self):
        """
        Structured list of input field definitions for the InputDock.

        Rules:
          - tuple[1] is the sole display label.
          - metadata["default"] is the sole source of initial widget values.
          - TYPE_BUTTON rows sit inline like any other field.
          - TYPE_NOTE rows are hidden labels revealed by domain logic.
          - TYPE_TITLE metadata carries only container/show_group_title.
          - All per-field validation, placeholders, callbacks, and material
            behaviour are declared here — InputDock has no key-specific logic.
        """
        material_values = connectdb("Material")

        return [
            # ── Module marker ─────────────────────────────────────────────────
            (KEY_MODULE_PLATE_GIRDER, None, TYPE_MODULE, None, True, "No Validator", {}),

            # ── Type of Structure ─────────────────────────────────────────────
            (KEY_SECTION_STRUCTURE, DISP_TITLE_STRUCTURE, TYPE_TITLE, None, True, "No Validator",
                {"container": "main"}),

            (KEY_STRUCTURE_TYPE, KEY_DISP_STRUCTURE_TYPE, TYPE_COMBOBOX, VALUES_STRUCTURE_TYPE,
                True, "No Validator",
                {
                    "default":          DEFAULTS_DICT.get(KEY_STRUCTURE_TYPE),
                    "disabled_options": ["Other"],
                }),

            # ── Project Location ──────────────────────────────────────────────
            (KEY_SECTION_PROJECT, DISP_TITLE_PROJECT, TYPE_TITLE, None, True, "No Validator",
                {"container": "main", "show_group_title": False}),

            (KEY_PROJECT_LOCATION, "Project Location*", TYPE_BUTTON, None, True, "No Validator",
                {
                    "action":       "show_project_location_dialog",
                    "button_label": "Select Location",
                }),

            # ── Geometric Details ─────────────────────────────────────────────
            (KEY_SECTION_GEOMETRIC, DISP_TITLE_GEOMETRIC, TYPE_TITLE, None, True, "No Validator",
                {"container": "superstructure"}),

            (KEY_SPAN, KEY_DISP_SPAN, TYPE_TEXTBOX, None, True, "Double Validator",
                {
                    "placeholder": f"{SPAN_MIN}–{SPAN_MAX} m",
                }),

            (KEY_CARRIAGEWAY_WIDTH, KEY_DISP_CARRIAGEWAY_WIDTH, TYPE_TEXTBOX, None,
                True, "Double Validator",
                {
                    "placeholder_dynamic": "_carriageway_placeholder_text",
                    "on_editing_finished": "validate_carriageway_width",
                }),

            (KEY_INCLUDE_MEDIAN, "Include Median", TYPE_COMBOBOX, VALUES_YES_NO,
                True, "No Validator",
                {
                    "default":         DEFAULTS_DICT.get(KEY_INCLUDE_MEDIAN),
                    "add_stretch":     True,
                    # When median toggle changes, refresh the carriageway placeholder
                    # and silently re-validate the carriageway width.
                    "on_changed":      [
                        "_update_carriageway_placeholder",
                        "_validate_carriageway_width_silent",
                    ],
                }),

            (KEY_FOOTPATH, KEY_DISP_FOOTPATH, TYPE_COMBOBOX, VALUES_FOOTPATH,
                True, "No Validator",
                {
                    "default":    DEFAULTS_DICT.get(KEY_FOOTPATH),
                    "on_changed": "_on_footpath_changed",
                }),

            (KEY_SKEW_ANGLE, KEY_DISP_SKEW_ANGLE, TYPE_TEXTBOX, None,
                True, "Double Validator",
                {
                    "placeholder": f"{SKEW_ANGLE_MIN}–{SKEW_ANGLE_MAX}°",
                }),

            # ── Additional Geometry ───────────────────────────────────────────
            (KEY_SECTION_ADDITIONAL_GEOMETRY, None, TYPE_TITLE, None, True, "No Validator",
                {"container": "superstructure", "show_group_title": False}),

            (KEY_ADDITIONAL_GEOMETRY, "Additional Geometry", TYPE_BUTTON, None, True, "No Validator",
                {
                    "action":       "show_additional_inputs",
                    "button_label": "Modify Here",
                }),

            # ── Design Type ───────────────────────────────────────────────────
            (KEY_SECTION_DESIGN_TYPE, "Design Type", TYPE_TITLE, None, True, "No Validator",
                {"container": "superstructure", "show_group_title": False}),

            (KEY_DESIGN_MODE, "Design Type", TYPE_COMBOBOX, ["Optimized", "Custom"],
                True, "No Validator",
                {
                    "default":        DEFAULTS_DICT.get(KEY_DESIGN_MODE),
                    "on_changed":     "_on_design_mode_changed",
                    "trigger_on_init": True,
                }),

            # ── Material Inputs ───────────────────────────────────────────────
            (KEY_SECTION_MATERIAL, DISP_TITLE_MATERIAL, TYPE_TITLE, None, True, "No Validator",
                {"container": "superstructure"}),

            (KEY_GIRDER, KEY_DISP_GIRDER, TYPE_COMBOBOX, material_values,
                True, "No Validator",
                {
                    "is_material_field": True,
                    "member_type":       "Girder",
                }),

            (KEY_CROSS_BRACING, KEY_DISP_CROSS_BRACING, TYPE_COMBOBOX, material_values,
                True, "No Validator",
                {
                    "is_material_field": True,
                    "member_type":       "Girder",
                }),

            (KEY_END_DIAPHRAGM, KEY_DISP_END_DIAPHRAGM, TYPE_COMBOBOX, material_values,
                True, "No Validator",
                {
                    "is_material_field": True,
                    "member_type":       "Girder",
                }),

            (KEY_DECK_CONCRETE_GRADE_BASIC, KEY_DISP_DECK_CONCRETE_GRADE, TYPE_COMBOBOX,
                VALUES_DECK_CONCRETE_GRADE, True, "No Validator",
                {
                    "default":           DEFAULTS_DICT.get(KEY_DECK_CONCRETE_GRADE_BASIC),
                    "is_material_field": True,
                    "member_type":       "Deck",
                }),
        ]

    # ── Output field definitions ──────────────────────────────────────────────

    def output_values(self, flag=None):
        return [
            (
                "section_output_analysis", "Analysis Results",
                TYPE_TITLE, None, True, "No Validator",
                {
                    "kind": "analysis",
                    "fields": [
                        ("analysis_member",           "Member:",                       "combobox",      ["All"],                                              True, "No Validator", {}),
                        ("analysis_load_combination", "Load Combination:",             "combobox",      ["Envelope"],                                         True, "No Validator", {}),
                        ("analysis_forces",           "Forces",                        "checkbox_grid", [["Fx","Mx","Dx"], ["Fy","My","Dy"], ["Fz","Mz","Dz"]], True, "No Validator", {}),
                        ("analysis_display_options",  "Display Options:",              "checkbox_row",  ["Max", "Min"],                                       True, "No Validator", {}),
                        ("analysis_utilization",      "Controlling Utilization Ratio", "checkbox",      None,                                                 True, "No Validator", {}),
                    ],
                },
            ),
            (
                "section_output_superstructure", "Superstructure",
                TYPE_TITLE, None, True, "No Validator",
                {
                    "kind": "design",
                    "rows": [
                        {"label": "Steel Design", "buttons": [{"text": "Here", "action": "open_steel_design"}]},
                        {"label": "Deck Design",  "buttons": [{"text": "Here", "action": "open_deck_design"}]},
                    ],
                },
            ),
            (
                "section_output_substructure", "Substructure",
                TYPE_TITLE, None, True, "No Validator",
                {"kind": "design", "rows": []},
            ),
        ]

    # ── Domain hooks ──────────────────────────────────────────────────────────

    def set_osdaglogger(self, key):
        pass

    def func_for_validation(self, design_inputs):
        return None