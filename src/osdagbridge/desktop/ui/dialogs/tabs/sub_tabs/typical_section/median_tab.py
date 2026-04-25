"""Median sub-tab for Typical Section Details."""

from osdagbridge.core.utils.common import DEFAULT_CONCRETE_DENSITY
from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import (
    MEDIAN_TAB_SCHEMA,
)
from osdagbridge.desktop.ui.dialogs.tabs.base import SchemaTab


_MEDIAN_VIEW_SCHEMA = {
    "row_vertical_spacing": 20,
    "cards": [
        {
            "title": "Median Inputs:",
            "label_width": MEDIAN_TAB_SCHEMA.get("label_width", 210),
            "field_width": 200,
            "rows": MEDIAN_TAB_SCHEMA.get("rows", []),
        }
    ]
}


class MedianTab(SchemaTab):
    """Schema-driven median page bound onto the Typical Section owner."""
    schema = _MEDIAN_VIEW_SCHEMA

    def __init__(self, owner, parent=None):
        super().__init__(owner, parent)
        self.setStyleSheet("background-color: white;")

    def export_median_state(self, *, include_median: bool = True) -> dict:
        return {
            "included": bool(include_median),
            "type": self.widget_current_text("median_type"),
            "width_m": self.widget_float("median_width"),
            "height_m": self.widget_float("median_height"),
            "density": self.widget_float("median_density"),
            "area": self.widget_float("median_area"),
            "load": self.widget_float("median_load"),
            "post_spacing_m": self.widget_float("median_post_spacing"),
        }

    def is_metallic(self, median_type: str) -> bool:
        return str(median_type).startswith("IRC 5 - Metallic Crash Barrier")

    def is_rcc(self, median_type: str) -> bool:
        median_type = str(median_type)
        return median_type.startswith("IRC 5 - RCC Crash Barrier") or median_type.startswith("IRC 5 - Raised Kerb")

    def effective_type(self, median_type: str) -> str:
        return "IRC 5 - Raised Kerb" if median_type == "Custom" else str(median_type)

    def auto_compute_load(self, median_type: str) -> None:
        if not self.is_rcc(median_type):
            return
        try:
            density = float(self.widget_text("median_density").strip() or 0.0)
            area = float(self.widget_text("median_area").strip() or 0.0)
            self.set_widget_text("median_load", f"{density * area:.2f}")
        except Exception:
            self.set_widget_text("median_load", "")

    def apply_defaults(self, median_type: str, geom: dict | None, *, force: bool = False, include_median: bool = True) -> None:
        is_rcc = self.is_rcc(median_type)
        is_metallic = self.is_metallic(median_type)
        is_custom = median_type == "Custom"

        def maybe_set(bind_name: str, value: str) -> None:
            if force or not self.widget_text(bind_name).strip():
                self.set_widget_text(bind_name, value)

        if is_rcc and geom:
            maybe_set("median_density", f"{DEFAULT_CONCRETE_DENSITY:.1f}")
            if geom.get("median_width") is not None:
                maybe_set("median_width", f"{geom['median_width'] / 1000:.2f}")
            if geom.get("barrier_height") is not None:
                maybe_set("median_height", f"{geom['barrier_height'] / 1000:.2f}")
            elif geom.get("kerb_height") is not None:
                maybe_set("median_height", f"{geom['kerb_height'] / 1000:.2f}")
            if self.widget_float("median_width") is not None and self.widget_float("median_height") is not None:
                area = self.widget_float("median_width", 0.0) * self.widget_float("median_height", 0.0)
                maybe_set("median_area", f"{area:.2f}")
            self.auto_compute_load(median_type)
        elif is_metallic:
            maybe_set("median_post_spacing", "1")
            if force:
                self.set_widget_text("median_load", "")
        elif is_custom:
            if geom and geom.get("median_width") is not None:
                maybe_set("median_width", f"{geom['median_width'] / 1000:.2f}")
            if geom and geom.get("barrier_height") is not None:
                maybe_set("median_height", f"{geom['barrier_height'] / 1000:.2f}")
            elif geom and geom.get("kerb_height") is not None:
                maybe_set("median_height", f"{geom['kerb_height'] / 1000:.2f}")
            if force:
                self.set_widget_text("median_load", "")

        self.update_visibility(median_type, include_median=include_median)

    def update_visibility(self, median_type: str, *, include_median: bool = True) -> None:
        is_metallic = self.is_metallic(median_type)
        is_rcc = self.is_rcc(median_type)
        is_custom = median_type == "Custom"
        active = bool(include_median)

        for bind_name in (
            "median_type",
            "median_density",
            "median_width",
            "median_height",
            "median_area",
            "median_load",
            "median_post_spacing",
            "median_density_label",
            "median_area_label",
            "median_post_spacing_label",
        ):
            widget = self.get_widget(bind_name)
            if widget is not None:
                widget.setEnabled(active)

        hide_density_area = is_metallic or is_custom
        for bind_name in ("median_density", "median_density_label", "median_area", "median_area_label"):
            widget = self.get_widget(bind_name)
            if widget is not None:
                widget.setVisible(active and not hide_density_area)
        if hide_density_area:
            self.set_widget_text("median_density", "")
            self.set_widget_text("median_area", "")

        for bind_name in ("median_post_spacing", "median_post_spacing_label"):
            widget = self.get_widget(bind_name)
            if widget is not None:
                widget.setVisible(active and is_metallic)
        if active and is_metallic and not self.widget_text("median_post_spacing").strip():
            self.set_widget_text("median_post_spacing", "1")
        if active and not is_metallic:
            self.set_widget_text("median_post_spacing", "")

        load_widget = self.get_widget("median_load")
        if load_widget is not None:
            load_widget.setEnabled(active)
            load_widget.setReadOnly(active and is_rcc)
            if active:
                load_widget.setPlaceholderText("" if not is_custom else "Enter custom load per IRC 6 guidance")
        if active and is_rcc:
            self.auto_compute_load(median_type)
        elif active and load_widget is not None:
            load_widget.setReadOnly(False)
