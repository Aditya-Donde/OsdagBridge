from PySide6.QtWidgets import QGridLayout, QWidget

from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import (
    DESIGN_OPTIONS_SCHEMA,
)
from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox, MessageBoxType
from osdagbridge.desktop.ui.dialogs.tabs import schema_io
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.girder_details_tab import (
    _BoundsDialog,
)
from osdagbridge.desktop.ui.dialogs.tabs.ui_builder import UIBuilder


class DesignOptionsTab(QWidget):
    """Analysis/Design Options tab rendered from DESIGN_OPTIONS_SCHEMA."""

    def __init__(self, parent_dialog):
        super().__init__()
        self.parent_dialog = parent_dialog
        self._reset_reinforcement_bounds()
        UIBuilder(owner=self, schema=DESIGN_OPTIONS_SCHEMA).build_tab(self)
        self._sync_reinforcement_combo()

    def save_values(self):
        return schema_io.collect_values(self, DESIGN_OPTIONS_SCHEMA)

    def restore_values(self, data: dict):
        schema_io.restore_values(self, DESIGN_OPTIONS_SCHEMA, data)

    def restore_properties(self, data: dict):
        self._restore_extra_state(data)

    def reset_defaults(self):
        schema_io.reset_defaults(self, DESIGN_OPTIONS_SCHEMA, after=self._after_reset)

    def validate_tab(self):
        errors = schema_io.validate(self, DESIGN_OPTIONS_SCHEMA)
        errors.extend(self._extra_validation())
        return list(dict.fromkeys(errors))

    def _extra_state(self):
        return {"reinforcement_bounds": dict(self._reinforcement_bounds)}

    def _restore_extra_state(self, data: dict):
        bounds = data.get("reinforcement_bounds") if isinstance(data, dict) else None
        if bounds:
            self._reinforcement_bounds = {
                "lower": float(bounds.get("lower", 8.0)),
                "upper": float(bounds.get("upper", 40.0)),
                "increment": float(bounds.get("increment", 1.0)),
            }
            self._reinforcement_values = [
                value
                for value in self._standard_reinforcement_values()
                if self._reinforcement_bounds["lower"] <= value <= self._reinforcement_bounds["upper"]
            ]
        else:
            self._reset_reinforcement_bounds()

        self._sync_reinforcement_combo()

    def _after_reset(self):
        self._reset_reinforcement_bounds()
        self._sync_reinforcement_combo()

    def _extra_validation(self):
        diameter_widget = getattr(self, "shear_stud_diameter_combo", None)
        spacing_widget = getattr(self, "shear_stud_spacing_input", None)
        if diameter_widget is None or spacing_widget is None:
            return []
        if not spacing_widget.isVisible() or not spacing_widget.isEnabled():
            return []

        try:
            diameter = float(diameter_widget.currentText())
            spacing = float(spacing_widget.text())
        except ValueError:
            return []

        if spacing < 4 * diameter:
            return [
                f"Shear Stud Spacing must be at least {4 * diameter:.2f} mm for diameter {diameter:.2f} mm."
            ]

        return []

    def _open_reinforcement_bounds(self):
        dialog = BoundsDialogNoIncrement(
            "Reinforcement Size",
            self._reinforcement_bounds,
            self,
        )

        if dialog.exec():
            result = dialog.result_bounds()
            if result:
                self._reinforcement_bounds = {
                    "lower": result["lower"],
                    "upper": result["upper"],
                    "increment": 1.0,
                }
                self._reinforcement_values = [
                    value
                    for value in self._standard_reinforcement_values()
                    if result["lower"] <= value <= result["upper"]
                ]
                self._sync_reinforcement_combo()

    def _reset_reinforcement_bounds(self):
        self._reinforcement_bounds = {
            "lower": 8.0,
            "upper": 40.0,
            "increment": 1.0,
        }
        self._reinforcement_values = self._standard_reinforcement_values()

    def _standard_reinforcement_values(self):
        return [8, 10, 12, 16, 20, 25, 28, 32, 36, 40]

    def _sync_reinforcement_combo(self):
        combo = getattr(self, "reinforcement_size_combo", None)
        if combo is None:
            return

        combo.clear()
        for value in self._reinforcement_values:
            combo.addItem(f"{value} mm")


class BoundsDialogNoIncrement(_BoundsDialog):
    def __init__(self, title, bounds, parent=None):
        super().__init__(title, bounds, parent)

        self.increment_input.hide()

        layout = self.findChild(QGridLayout)
        if layout:
            item = layout.itemAtPosition(2, 0)
            if item and item.widget():
                item.widget().hide()

    def _on_accept(self):
        errors = []

        lower = self._parse_positive(self.lower_input.text())
        upper = self._parse_positive(self.upper_input.text())

        if lower is None or upper is None:
            errors.append("Please enter valid numeric values.")
        else:
            if lower < 8:
                errors.append("Lower bound cannot be less than 8 mm.")
            if upper > 40:
                errors.append("Upper bound cannot be greater than 40 mm.")
            if upper <= lower:
                errors.append("Upper bound must be greater than lower bound.")

        if errors:
            message = "\n\n".join(f"• {err}" for err in errors)
            CustomMessageBox(
                title="Validation Errors",
                text=message,
                buttons=["OK"],
                dialogType=MessageBoxType.Warning,
            ).exec()
            return

        self._result = {
            "lower": float(lower),
            "upper": float(upper),
            "increment": 1.0,
        }

        self.accept()
