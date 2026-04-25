"""Railing sub-tab for Typical Section Details."""

from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import (
    RAILING_TAB_SCHEMA,
)
from osdagbridge.desktop.ui.dialogs.tabs.base import SchemaTab


_RAILING_VIEW_SCHEMA = {
    "row_vertical_spacing": 20,
    "cards": [
        {
            "title": "Railing Inputs:",
            "label_width": RAILING_TAB_SCHEMA.get("label_width", 180),
            "field_width": 200,
            "rows": RAILING_TAB_SCHEMA.get("rows", []),
        }
    ]
}


class RailingTab(SchemaTab):
    """Schema-driven railing page bound onto the Typical Section owner."""
    schema = _RAILING_VIEW_SCHEMA

    def __init__(self, owner, parent=None):
        super().__init__(owner, parent)
        self.setStyleSheet("background-color: white;")

    def export_railing_state(self) -> dict:
        return {
            "type": self.widget_current_text("railing_type"),
            "width_mm": self.widget_float("railing_width"),
            "height_m": self.widget_float("railing_height"),
            "load_mode": self.widget_current_text("railing_load_mode"),
            "load_value": self.widget_float("railing_load_value"),
        }

    def apply_defaults(self, *, width_mm=None, height_m=None, force: bool = False) -> None:
        if width_mm is not None and (force or not self.widget_text("railing_width").strip()):
            self.set_widget_text("railing_width", f"{float(width_mm):.0f}")
        if height_m is not None and (force or not self.widget_text("railing_height").strip()):
            self.set_widget_text("railing_height", f"{float(height_m):.2f}")

    def apply_load_mode(self, mode: str) -> None:
        mode_widget = self.get_widget("railing_load_mode")
        if mode_widget is not None and hasattr(mode_widget, "blockSignals"):
            previous = mode_widget.blockSignals(True)
            try:
                self.set_widget_current_text("railing_load_mode", mode)
            finally:
                mode_widget.blockSignals(previous)
        else:
            self.set_widget_current_text("railing_load_mode", mode)
        widget = self.get_widget("railing_load_value")
        if widget is None:
            return

        is_auto = str(mode).startswith("Automatic")
        if is_auto:
            widget.setReadOnly(True)
            widget.setEnabled(True)
            widget.setText("1.5")
            widget.setPlaceholderText("")
            widget.setStyleSheet(
                "QLineEdit { background-color: #f1f1f1; color: #7a7a7a;"
                " border: 1px solid #bfbfbf; border-radius: 4px; padding: 4px 6px; }"
            )
            return

        widget.setReadOnly(False)
        widget.setEnabled(True)
        widget.clear()
        widget.setPlaceholderText("Enter load value")
        widget.setStyleSheet(
            "QLineEdit { background-color: #ffffff; color: #000000;"
            " border: 1px solid #000000; border-radius: 4px; padding: 4px 6px; }"
        )
