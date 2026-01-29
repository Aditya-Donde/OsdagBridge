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
                {"label": "Carriageway Width*"},
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
                    "post_rows": [
                        {
                            "type": "material_properties",
                            "label": "Properties",
                            "buttons": [
                                {
                                    "text": "Modify Here",
                                    "action": "show_material_properties_dialog",
                                }
                            ],
                        }
                    ],
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
                {"label": "Deck", "default": "M 25"},
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
                                {"text": "Here", "action": "show_additional_inputs"},
                            ],
                        },
                        {
                            "label": "Deck Design",
                            "buttons": [
                                {"text": "Here", "action": "show_additional_inputs"},
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
