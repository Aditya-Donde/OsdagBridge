from osdagbridge.core.utils.common import *

class FrontendData:
    """Backend for Highway Bridge Design"""
    
    def __init__(self):
        self.module = KEY_DISP_FINPLATE
        self.design_status = False
        self.design_button_status = False
    
    def input_values(self):
        """Return structured schema for dynamic UI rendering."""

        return [
            {
                "id": "geometric",
                "title": "Geometric Details",
                "fields": [
                    {
                        "id": KEY_SPAN,
                        "label": KEY_DISP_SPAN + "*",
                        "type": "line",
                        "required": True,
                        "validator": {
                            "type": "double_range",
                            "bottom": SPAN_MIN,
                            "top": SPAN_MAX,
                            "decimals": 2,
                        },
                        "placeholder": f"{SPAN_MIN}-{SPAN_MAX} m",
                        "bind": "span_input",
                    },
                    {
                        "id": KEY_CARRIAGEWAY_WIDTH,
                        "label": KEY_DISP_CARRIAGEWAY_WIDTH + "*",
                        "type": "line",
                        "required": True,
                        "validator": {
                            "type": "double_range",
                            "bottom": 0.0,
                            "top": 100.0,
                            "decimals": 2,
                        },
                        "placeholder": "Width",
                        "bind": "carriageway_input",
                        "on_editing_finished": "validate_carriageway_width",
                    },
                    {
                        "id": KEY_INCLUDE_MEDIAN,
                        "label": KEY_INCLUDE_MEDIAN,
                        "type": "combo",
                        "choices": ["No", "Yes"],
                        "default": "No",
                        "bind": "include_median_combo",
                        "on_change": "on_include_median_changed",
                    },
                    {
                        "id": KEY_FOOTPATH,
                        "label": KEY_DISP_FOOTPATH,
                        "type": "combo",
                        "choices": VALUES_FOOTPATH,
                        "default": VALUES_FOOTPATH[0] if VALUES_FOOTPATH else None,
                        "bind": "footpath_combo",
                        "on_change": "on_footpath_changed",
                    },
                    {
                        "id": KEY_SKEW_ANGLE,
                        "label": KEY_DISP_SKEW_ANGLE,
                        "type": "line",
                        "required": True,
                        "validator": {
                            "type": "double_range",
                            "bottom": SKEW_ANGLE_MIN,
                            "top": SKEW_ANGLE_MAX,
                            "decimals": 1,
                        },
                        "placeholder": f"{SKEW_ANGLE_MIN} - {SKEW_ANGLE_MAX}°",
                        "bind": "skew_input",
                    },
                ],
            },
            {
                "id": "material",
                "title": "Material Inputs",
                "fields": [
                    {
                        "id": KEY_GIRDER,
                        "label": KEY_DISP_GIRDER,
                        "type": "combo",
                        "choices": VALUES_MATERIAL,
                        "bind": "girder_combo",
                    },
                    {
                        "id": KEY_CROSS_BRACING,
                        "label": KEY_DISP_CROSS_BRACING,
                        "type": "combo",
                        "choices": VALUES_MATERIAL,
                        "bind": "cross_bracing_combo",
                    },
                    {
                        "id": KEY_END_DIAPHRAGM,
                        "label": KEY_DISP_END_DIAPHRAGM,
                        "type": "combo",
                        "choices": VALUES_MATERIAL,
                        "bind": "end_diaphragm_combo",
                    },
                    {
                        "id": KEY_DECK_CONCRETE_GRADE_BASIC,
                        "label": KEY_DISP_DECK,
                        "type": "combo",
                        "choices": VALUES_DECK_CONCRETE_GRADE,
                        "default": "M 25",
                        "bind": "deck_combo",
                    },
                ],
            },
        ]
    
    def set_osdaglogger(self, key):
        """Logger setup"""
        print("Logger set up (mock)")
    
    def output_values(self, flag):
        """output values List"""
        return []
    
    def func_for_validation(self, design_inputs):
        """Validation Function"""
        return None

