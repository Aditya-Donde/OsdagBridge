from osdagbridge.core.utils.common import VALUES_WEARING_COAT_MATERIAL

WEARING_COURSE_TAB_SCHEMA = {
    "id": "wearing_course_tab",
    "label_width": 200,
    "rows": [
        {
            "fields": [
                {
                    "id": "wearing_material",
                    "label": "Material:",
                    "type": "combo",
                    "choices": VALUES_WEARING_COAT_MATERIAL,
                    "bind": "wearing_material",
                    "on_change": "on_wearing_material_changed",
                }
            ]
        },
        {
            "fields": [
                {
                    "id": "wearing_density",
                    "label": "Density (kN/m³):",
                    "type": "line",
                    "validator": {"type": "double_range", "bottom": 0.0, "top": 40.0, "decimals": 2},
                    "bind": "wearing_density",
                    "default": "24.0",
                }
            ]
        },
        {
            "fields": [
                {
                    "id": "wearing_thickness",
                    "label": "Thickness (mm):",
                    "type": "line",
                    "validator": {"type": "double_range", "bottom": 0.0, "top": 200.0, "decimals": 1},
                    "bind": "wearing_thickness",
                    "default": "50",
                }
            ]
        },
    ],
}
