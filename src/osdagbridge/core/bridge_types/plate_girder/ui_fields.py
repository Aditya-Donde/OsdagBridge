from osdagbridge.core.utils.common import *
"""
(
    key,
    display_name,
    ui_type,
    values,
    is_visible,
    validator,
    ui_config_dict
)

"""
class FrontendData:
    """Backend for Highway Bridge Design"""
    
    def __init__(self):
        self.module = KEY_DISP_FINPLATE
        self.design_status = False
        self.design_button_status = False

        # Simple UI state store (input/output docks).
        # The docks can set values here, and `input_values()` can use them as defaults.
        self._input_state: dict[str, object] = {}
        self._output_state: dict[str, object] = {}

    # -----------------------------
    # Generic state getters/setters
    # -----------------------------
    def set_input_value(self, key: str, value):
        if not key:
            return
        self._input_state[key] = value
        # print(f"DEBUG: Backend updated -> {key}: {value}")

    def get_input_value(self, key: str, default=None):
        if not key:
            return default
        return self._input_state.get(key, default)

    def set_output_value(self, key: str, value):
        if not key:
            return
        self._output_state[key] = value

    def get_output_value(self, key: str, default=None):
        if not key:
            return default
        return self._output_state.get(key, default)

    def set_input_values(self, values: dict):
        """Bulk update input state (e.g., when loading a saved project)."""
        if not isinstance(values, dict):
            return
        for k, v in values.items():
            if isinstance(k, str):
                self._input_state[k] = v
                

    def get_input_values_dict(self, include_empty: bool = False) -> dict:
        """Export current input state; can be fed into analyzers/designers later."""
        if include_empty:
            return dict(self._input_state)
        return {k: v for k, v in self._input_state.items() if v not in (None, "")}

    def _iter_defined_input_keys(self):
        """Yield keys that represent actual inputs (not titles/modules)."""
        for item in self.input_values():
            if not isinstance(item, tuple) or len(item) < 3:
                continue
            key, _label, ui_type = item[0], item[1], item[2]
            if not isinstance(key, str):
                continue
            if ui_type in (TYPE_TITLE, TYPE_MODULE):
                continue
            yield key

    def list_input_keys(self) -> list[str]:
        """Return input keys in UI definition order."""
        seen: set[str] = set()
        ordered: list[str] = []
        for key in self._iter_defined_input_keys():
            if key in seen:
                continue
            seen.add(key)
            ordered.append(key)
        return ordered

    def export_basic_inputs_as_list(self, include_empty: bool = False) -> list[dict]:
        """Export basic inputs as a list of single-key dictionaries.

        Example: [{"span": 30.0}, {"carriageway_width": 7.5}, ...]
        """
        values = self.get_input_values_dict(include_empty=include_empty)
        out: list[dict] = []
        for key in self.list_input_keys():
            if key not in values:
                continue
            value = values.get(key)
            if not include_empty and value in (None, ""):
                continue
            out.append({key: value})
        return out

    def set_final_design_inputs(self, final_inputs: list[dict]) -> None:
        """Persist the final merged input payload for design execution."""
        if not isinstance(final_inputs, list):
            return
        self.set_input_value("final_design_inputs", final_inputs)
    
    def input_values(self):
        """Return structured list of input definitions for the UI"""
        options_list = []

        options_list.append(
            (KEY_MODULE, KEY_DISP_FINPLATE, TYPE_MODULE, None, True, 'No Validator', {})
        )

        # Type of Structure
        options_list.append(
            (
                "section_structure",
                DISP_TITLE_STRUCTURE,
                TYPE_TITLE,
                None,
                True,
                'No Validator',
                {
                    "container": "main",
                    "post_note": {
                        "text": "*Other structures not included",
                        "attr": "structure_note",
                    },
                },
            )
        )
        options_list.append(
            (
                KEY_STRUCTURE_TYPE,
                KEY_DISP_STRUCTURE_TYPE,
                TYPE_COMBOBOX,
                VALUES_STRUCTURE_TYPE,
                True,
                'No Validator',
                {},
            )
        )

        # Project Location (custom content handled in dock)
        options_list.append(
            (
                "section_project_location",
                DISP_TITLE_PROJECT,
                TYPE_TITLE,
                None,
                True,
                'No Validator',
                {
                    "container": "main",
                    "custom_content": "project_location",
                    "show_group_title": False,
                    "header_label": "Project Location*",
                    "button_rows": [
                        {
                            "type": "project_location",
                            "buttons": [
                                {
                                    "text": "Add Here",
                                    "action": "show_project_location_dialog",
                                }
                            ],
                        }
                    ],
                },
            )
        )

        # Geometric Details
        options_list.append(
            (
                "section_geometric",
                DISP_TITLE_GEOMETRIC,
                TYPE_TITLE,
                None,
                True,
                'No Validator',
                {
                    "container": "superstructure",
                },
            )
        )
        options_list.append(
            (
                KEY_SPAN,
                KEY_DISP_SPAN,
                TYPE_TEXTBOX,
                None,
                True,
                'Double Validator',
                {"label": "Span*"},
            )
        )
        options_list.append(
            (
                KEY_CARRIAGEWAY_WIDTH,
                KEY_DISP_CARRIAGEWAY_WIDTH,
                TYPE_TEXTBOX,
                None,
                True,
                'Double Validator',
                {"label": "Carriageway Width*\n(Each way)"},
            )
        )
        options_list.append(
            (
                KEY_INCLUDE_MEDIAN,
                "Include Median",
                TYPE_COMBOBOX,
                VALUES_YES_NO,
                True,
                'No Validator',
                {"label": "Include Median", "default": "No", "add_stretch": True},
            )
        )
        options_list.append(
            (
                KEY_FOOTPATH,
                KEY_DISP_FOOTPATH,
                TYPE_COMBOBOX,
                VALUES_FOOTPATH,
                True,
                'No Validator',
                {"label": "Footpath", "default": "None"},
            )
        )
        options_list.append(
            (
                KEY_SKEW_ANGLE,
                KEY_DISP_SKEW_ANGLE,
                TYPE_TEXTBOX,
                None,
                True,
                'Double Validator',
                {"label": "Skew Angle"},
            )
        )
        options_list.append(
            (
                "section_additional_geometry",
                "",
                TYPE_TITLE,
                None,
                True,
                'No Validator',
                {
                    "container": "superstructure",
                    "show_group_title": False,
                    "post_rows": [
                        {
                            "type": "additional_geometry",
                            "label": "Additional Geometry",
                            "buttons": [
                                {
                                    "text": "Modify Here",
                                    "action": "show_additional_inputs",
                                }
                            ],
                        }
                    ],
                },
            )
        )
        options_list.append(
            (
                "section_design_type",
                "",
                TYPE_TITLE,
                None,
                True,
                'No Validator',
                {
                    "container": "superstructure",
                    "show_group_title": False,
                },
            )
        )
        options_list.append(
            (
                "Design",
                "Design Type",
                TYPE_COMBOBOX,
                ["Optimized", "Custom"],
                True,
                'No Validator',
                {"label": "Design Type", "default": "Optimized"},
            )
        )

        # Material Inputs
        options_list.append(
            (
                "section_material",
                DISP_TITLE_MATERIAL,
                TYPE_TITLE,
                None,
                True,
                'No Validator',
                {
                    "container": "superstructure",
                },
            )
        )
        material_values = connectdb("Material")
        options_list.append(
            (
                KEY_GIRDER,
                KEY_DISP_GIRDER,
                TYPE_COMBOBOX,
                material_values,
                True,
                'No Validator',
                {"label": "Girder"},
            )
        )
        options_list.append(
            (
                KEY_CROSS_BRACING,
                KEY_DISP_CROSS_BRACING,
                TYPE_COMBOBOX,
                material_values,
                True,
                'No Validator',
                {"label": "Cross Bracing"},
            )
        )
        options_list.append(
            (
                KEY_END_DIAPHRAGM,
                KEY_DISP_END_DIAPHRAGM,
                TYPE_COMBOBOX,
                material_values,
                True,
                'No Validator',
                {"label": "End Diaphragm"},
            )
        )
        options_list.append(
            (
                KEY_DECK_CONCRETE_GRADE_BASIC,
                KEY_DISP_DECK_CONCRETE_GRADE,
                TYPE_COMBOBOX,
                VALUES_DECK_CONCRETE_GRADE,
                True,
                'No Validator',
                {"label": "Deck"},
            )
        )

        return options_list
    
    def set_osdaglogger(self, key):
        """Logger setup"""
        print("Logger set up (mock)")
    
    def output_values(self, flag=None):
        """Return output dock definitions using the same tuple structure as input_values."""
        outputs = []

        outputs.append(
            (
                "section_output_analysis",
                "Analysis Results",
                TYPE_TITLE,
                None,
                True,
                "No Validator",
                {
                    "kind": "analysis",
                    "fields": [
                        (
                            "analysis_member",
                            "Member:",
                            "combobox",
                            ["All"],
                            True,
                            "No Validator",
                            {"label_min_width": 100},
                        ),
                        (
                            "analysis_load_combination",
                            "Load Combination:",
                            "combobox",
                            ["Envelope"],
                            True,
                            "No Validator",
                            {"label_min_width": 100},
                        ),
                        (
                            "analysis_forces",
                            "Forces",
                            "checkbox_grid",
                            [
                                ["Fx", "Mx", "Dx"],
                                ["Fy", "My", "Dy"],
                                ["Fz", "Mz", "Dz"],
                            ],
                            True,
                            "No Validator",
                            {},
                        ),
                        (
                            "analysis_display_options",
                            "Display Options:",
                            "checkbox_row",
                            ["Max", "Min"],
                            True,
                            "No Validator",
                            {},
                        ),
                        (
                            "analysis_utilization",
                            "Controlling Utilization Ratio",
                            "checkbox",
                            None,
                            True,
                            "No Validator",
                            {},
                        ),
                    ],
                },
            )
        )

        outputs.append(
            (
                "section_output_superstructure",
                "Superstructure",
                TYPE_TITLE,
                None,
                True,
                "No Validator",
                {
                    "kind": "design",
                    "rows": [
                        {
                            "label": "Steel Design",
                            "buttons": [
                                {"text": "Here", "action": "open_steel_design"},
                            ],
                        },
                        {
                            "label": "Deck Design",
                            "buttons": [
                                {"text": "Here", "action": "open_deck_design"},
                            ],
                        },
                    ]
                },
            )
        )

        outputs.append(
            (
                "section_output_substructure",
                "Substructure",
                TYPE_TITLE,
                None,
                True,
                "No Validator",
                {
                    "kind": "design",
                    "rows": [],
                },
            )
        )

        return outputs
    
    def func_for_validation(self, design_inputs):
        """Validation Function"""
        return None

    def prime_defaults_from_definitions(self):
        """Populate state with any defaults declared in `input_values()` metadata."""
        for item in self.input_values():
            if not isinstance(item, tuple) or len(item) < 7:
                continue
            key, _label, ui_type, values, _required, _validator, metadata = item
            if not isinstance(key, str):
                continue
            if ui_type in (TYPE_TITLE, TYPE_MODULE):
                continue
            if key in self._input_state:
                continue
            default = (metadata or {}).get("default")
            if default is not None:
                self._input_state[key] = default
            elif ui_type == TYPE_COMBOBOX and isinstance(values, (list, tuple)) and values:
                # If no explicit default is provided, keep the first item as a sensible initial value.
                self._input_state[key] = values[0]
