"""Crash Barrier sub-tab for Typical Section Details."""

from osdagbridge.core.utils.common import DEFAULT_CONCRETE_DENSITY
from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import (
    CRASH_BARRIER_TAB_SCHEMA,
)
from osdagbridge.desktop.ui.dialogs.tabs.base import SchemaTab


_CRASH_BARRIER_VIEW_SCHEMA = {
    "row_vertical_spacing": 20,
    "cards": [
        {
            "title": "Crash Barrier Inputs:",
            "label_width": CRASH_BARRIER_TAB_SCHEMA.get("label_width", 210),
            "field_width": 200,
            "rows": CRASH_BARRIER_TAB_SCHEMA.get("rows", []),
        }
    ]
}


class CrashBarrierTab(SchemaTab):
    """Schema-driven crash barrier page bound onto the Typical Section owner."""
    schema = _CRASH_BARRIER_VIEW_SCHEMA

    def __init__(self, owner, parent=None):
        super().__init__(owner, parent)
        self.setStyleSheet("background-color: white;")

    def export_barrier_state(self) -> dict:
        return {
            "type": self.widget_current_text("crash_barrier_type"),
            "width_m": self.widget_float("crash_barrier_width"),
            "height_m": self.widget_float("crash_barrier_height"),
            "density": self.widget_float("crash_barrier_density"),
            "area": self.widget_float("crash_barrier_area"),
            "load": self.widget_float("crash_barrier_load"),
            "post_spacing_m": self.widget_float("crash_barrier_post_spacing"),
        }

    def is_metallic(self, barrier_type: str) -> bool:
        return str(barrier_type).startswith("IRC 5 - Metallic Crash Barrier")

    def is_rcc(self, barrier_type: str) -> bool:
        barrier_type = str(barrier_type)
        return (
            barrier_type.startswith("IRC 5 - RCC Crash Barrier")
            or barrier_type.startswith("IRC 5 - High Containment RCC Crash Barrier")
        )

    def effective_type(self, barrier_type: str) -> str:
        return "IRC 5 - RCC Crash Barrier" if barrier_type == "Custom" else str(barrier_type)

    def auto_compute_load(self, barrier_type: str) -> None:
        if not self.is_rcc(barrier_type):
            return
        try:
            density = float(self.widget_text("crash_barrier_density").strip() or 0.0)
            area = float(self.widget_text("crash_barrier_area").strip() or 0.0)
            self.set_widget_text("crash_barrier_load", f"{density * area:.2f}")
        except Exception:
            self.set_widget_text("crash_barrier_load", "")

    def apply_defaults(self, barrier_type: str, geom: dict | None, *, force: bool = False) -> None:
        is_rcc = self.is_rcc(barrier_type)
        is_metallic = self.is_metallic(barrier_type)
        is_custom = barrier_type == "Custom"

        def maybe_set(bind_name: str, value: str) -> None:
            if force or not self.widget_text(bind_name).strip():
                self.set_widget_text(bind_name, value)

        if is_rcc and geom:
            maybe_set("crash_barrier_density", f"{DEFAULT_CONCRETE_DENSITY:.1f}")
            if geom.get("bottom_width") is not None:
                maybe_set("crash_barrier_width", f"{geom['bottom_width'] / 1000:.2f}")
            if geom.get("total_height") is not None:
                maybe_set("crash_barrier_height", f"{geom['total_height'] / 1000:.2f}")
            if self.widget_float("crash_barrier_width") is not None and self.widget_float("crash_barrier_height") is not None:
                area = self.widget_float("crash_barrier_width", 0.0) * self.widget_float("crash_barrier_height", 0.0)
                maybe_set("crash_barrier_area", f"{area:.2f}")
            self.auto_compute_load(barrier_type)
        elif is_metallic:
            maybe_set("crash_barrier_post_spacing", "1")
            if force:
                self.set_widget_text("crash_barrier_load", "")
        elif is_custom:
            if geom and geom.get("bottom_width") is not None:
                maybe_set("crash_barrier_width", f"{geom['bottom_width'] / 1000:.2f}")
            if geom and geom.get("total_height") is not None:
                maybe_set("crash_barrier_height", f"{geom['total_height'] / 1000:.2f}")
            if force:
                self.set_widget_text("crash_barrier_load", "")

        self.update_visibility(barrier_type)

    def update_visibility(self, barrier_type: str) -> None:
        is_metallic = self.is_metallic(barrier_type)
        is_rcc = self.is_rcc(barrier_type)
        is_custom = barrier_type == "Custom"

        hide_density_area = is_metallic or is_custom
        for bind_name in ("crash_barrier_density", "crash_barrier_density_label", "crash_barrier_area", "crash_barrier_area_label"):
            widget = self.get_widget(bind_name)
            if widget is not None:
                widget.setVisible(not hide_density_area)
        if hide_density_area:
            self.set_widget_text("crash_barrier_density", "")
            self.set_widget_text("crash_barrier_area", "")

        for bind_name in ("crash_barrier_post_spacing", "crash_barrier_post_spacing_label"):
            widget = self.get_widget(bind_name)
            if widget is not None:
                widget.setVisible(is_metallic)
        if is_metallic and not self.widget_text("crash_barrier_post_spacing").strip():
            self.set_widget_text("crash_barrier_post_spacing", "1")
        if not is_metallic:
            self.set_widget_text("crash_barrier_post_spacing", "")

        load_widget = self.get_widget("crash_barrier_load")
        if load_widget is not None:
            load_widget.setEnabled(True)
            load_widget.setReadOnly(is_rcc)
            load_widget.setPlaceholderText("" if not is_custom else "Enter custom load per IRC 6 guidance")
        if is_rcc:
            self.auto_compute_load(barrier_type)
