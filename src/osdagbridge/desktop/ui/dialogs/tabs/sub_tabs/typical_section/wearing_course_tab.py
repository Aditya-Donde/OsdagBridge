"""Wearing Course sub-tab for Typical Section Details."""

from osdagbridge.core.utils.common import (
    KEY_WEARING_COAT_DENSITY,
    KEY_WEARING_COAT_MATERIAL,
    KEY_WEARING_COAT_THICKNESS,
)
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

    def export_cad_params(self) -> dict:
        state = self.export_wearing_state()
        params = {}
        if state.get("thickness_mm") is not None:
            thickness = float(state["thickness_mm"])
            params[KEY_WEARING_COAT_THICKNESS] = thickness
            params["wearing_course_thickness"] = thickness
        if state.get("density") is not None:
            density = float(state["density"])
            params[KEY_WEARING_COAT_DENSITY] = density
            params["wearing_course_density"] = density
        if state.get("material"):
            params[KEY_WEARING_COAT_MATERIAL] = state["material"]
            params["wearing_course_material"] = state["material"]
        return params

    def apply_material_defaults(self, material: str) -> None:
        if material == "Concrete":
            self.set_widget_text("wearing_density", "24.0")
        elif material == "Bituminous":
            self.set_widget_text("wearing_density", "22.0")
        else:
            self.set_widget_text("wearing_density", "")

        if not self.widget_text("wearing_thickness").strip():
            self.set_widget_text("wearing_thickness", "50")

    def sync_from_parent_material(self, material: str) -> dict:
        self.apply_material_defaults(material)
        return self.export_cad_params()

    def sync_from_parent_state(self) -> dict:
        material = self.export_wearing_state().get("material") or ""
        return self.sync_from_parent_material(material)
