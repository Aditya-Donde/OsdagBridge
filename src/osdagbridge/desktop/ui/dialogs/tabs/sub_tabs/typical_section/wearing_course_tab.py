"""Wearing Course sub-tab for Typical Section Details."""

from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import (
    WEARING_COURSE_TAB_SCHEMA,
)
from osdagbridge.desktop.ui.dialogs.tabs.base import SchemaTab


_WEARING_COURSE_VIEW_SCHEMA = {
    "row_vertical_spacing": 20,
    "cards": [
        {
            "title": "Wearing Course Inputs:",
            "label_width": WEARING_COURSE_TAB_SCHEMA.get("label_width", 200),
            "field_width": 200,
            "rows": WEARING_COURSE_TAB_SCHEMA.get("rows", []),
        }
    ]
}


class WearingCourseTab(SchemaTab):
    """Schema-driven wearing course page bound onto the Typical Section owner."""
    schema = _WEARING_COURSE_VIEW_SCHEMA

    def __init__(self, owner, parent=None):
        super().__init__(owner, parent)
        self.setStyleSheet("background-color: white;")

    def export_wearing_state(self) -> dict:
        return {
            "material": self.widget_current_text("wearing_material"),
            "thickness_mm": self.widget_float("wearing_thickness"),
            "density": self.widget_float("wearing_density"),
        }

    def apply_material_defaults(self, material: str) -> None:
        if material == "Concrete":
            self.set_widget_text("wearing_density", "24.0")
        elif material == "Bituminous":
            self.set_widget_text("wearing_density", "22.0")
        else:
            self.set_widget_text("wearing_density", "")

        if not self.widget_text("wearing_thickness").strip():
            self.set_widget_text("wearing_thickness", "50")
