"""Wearing Course sub-tab for Typical Section Details."""

from osdagbridge.core.utils.common import (
    KEY_WEARING_COAT_DENSITY,
    KEY_WEARING_COAT_MATERIAL,
    KEY_WEARING_COAT_THICKNESS,
)
from osdagbridge.core.bridge_types.plate_girder.schemas import (
    WEARING_COURSE_TAB_SCHEMA,
)
from osdagbridge.desktop.ui.dialogs.tabs.base import SchemaTab


def _compact_rows(schema: dict) -> list[dict]:
    fields = [
        field
        for row in schema.get("rows", []) or []
        for field in row.get("fields", []) or []
    ]
    return [
        {"fields": fields[0:2]},
        {"fields": fields[2:3]},
    ]


_WEARING_COURSE_VIEW_SCHEMA = {
    "row_vertical_spacing": 20,
    "cards": [
        {
            "title": "Wearing Course Inputs:",
            "label_width": 170,
            "field_width": 200,
            "rows": _compact_rows(WEARING_COURSE_TAB_SCHEMA),
        }
    ]
}


class WearingCourseTab(SchemaTab):
    """Schema-driven wearing course page bound onto the Typical Section owner."""
    schema = _WEARING_COURSE_VIEW_SCHEMA

    def __init__(self, owner, parent=None):
        super().__init__(owner, parent)
        self.setStyleSheet("background-color: white;")
        self._wire_owner_preview_updates()

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

    def apply_material_defaults(self, material: str, *, force: bool = False) -> None:
        if material == "Concrete":
            self.set_widget_text("wearing_density", "24.0")
        elif material == "Bituminous":
            self.set_widget_text("wearing_density", "22.0")
        else:
            self.set_widget_text("wearing_density", "")

        if force or not self.widget_text("wearing_thickness").strip():
            self.set_widget_text("wearing_thickness", "50")

    def sync_from_parent_material(self, material: str, *, force: bool = False) -> dict:
        self.apply_material_defaults(material, force=force)
        return self.export_cad_params()

    def sync_from_parent_state(self) -> dict:
        material = self.export_wearing_state().get("material") or ""
        return self.sync_from_parent_material(material)

    def on_wearing_material_changed(self, material) -> None:
        owner = getattr(self, "owner", None)
        params = self.sync_from_parent_material(material)
        push = getattr(owner, "_push_cad_params", None) if owner is not None else None
        if callable(push):
            push(params)

    def _wire_owner_preview_updates(self) -> None:
        owner = getattr(self, "owner", None)
        update_preview = getattr(owner, "_update_cad_preview", None) if owner is not None else None
        if not callable(update_preview):
            return
        for bind_name in ("wearing_thickness", "wearing_density"):
            widget = self.get_widget(bind_name)
            if widget is not None and hasattr(widget, "editingFinished"):
                widget.editingFinished.connect(update_preview)
