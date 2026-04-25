"""Railing sub-tab for Typical Section Details."""

from osdagbridge.core.utils.common import MIN_RAILING_HEIGHT
from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import (
    RAILING_TAB_SCHEMA,
)
from osdagbridge.desktop.ui.dialogs.tabs.base import SchemaTab
from osdagbridge.desktop.cad.irc5_geometry import RailingGeometry


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

    def export_cad_params(self) -> dict:
        state = self.export_railing_state()
        params = {}
        if state.get("type"):
            params["railing_type"] = state["type"]
        if state.get("width_mm") is not None:
            params["railing_width"] = float(state["width_mm"])
        if state.get("height_m") is not None:
            params["railing_height"] = float(state["height_m"]) * 1000
        return params

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

    def sync_from_parent_geometry(
        self,
        railing_type: str,
        *,
        width_mm=None,
        height_m=None,
        force: bool = False,
        load_mode: str = "Automatic (IRC 6)",
    ) -> dict:
        self.apply_defaults(width_mm=width_mm, height_m=height_m, force=force)
        self.apply_load_mode(load_mode)
        params = self.export_cad_params()
        if railing_type:
            params["railing_type"] = railing_type
        return params

    def sync_from_parent_state(self, *, force: bool = False) -> dict:
        railing_type = self.export_railing_state().get("type")
        if not railing_type:
            return {}
        effective_railing_type = "IRC 5 - RCC Railing" if railing_type == "Custom" else railing_type
        geom = RailingGeometry.get_geometry(effective_railing_type)
        return self.sync_from_parent_geometry(
            railing_type,
            width_mm=geom.get("width") if geom else None,
            height_m=(geom.get("height") / 1000.0) if geom and geom.get("height") is not None else None,
            force=force,
            load_mode="Automatic (IRC 6)",
        )

    def on_railing_type_changed(self, railing_type) -> None:
        owner = getattr(self, "owner", None)
        params = self.sync_from_parent_state(force=True)
        push = getattr(owner, "_push_cad_params", None) if owner is not None else None
        if callable(push):
            push(params)

        recalculate = getattr(owner, "recalculate_girders", None) if owner is not None else None
        if callable(recalculate):
            recalculate()

    def on_railing_load_mode_changed(self, mode) -> None:
        self.apply_load_mode(mode)

    def validate_railing_height(self) -> None:
        try:
            height = self.widget_float("railing_height")
            if height is not None and height < MIN_RAILING_HEIGHT:
                owner = getattr(self, "owner", None)
                callback = getattr(owner, "show_critical_message", None) if owner is not None else None
                if callable(callback):
                    callback(
                        "Railing Height Error",
                        f"Railing height must be at least {MIN_RAILING_HEIGHT} m as per IRC 5 "
                        "Clauses 109.7.2.3 and 109.7.2.4.",
                    )
        except Exception:
            return
