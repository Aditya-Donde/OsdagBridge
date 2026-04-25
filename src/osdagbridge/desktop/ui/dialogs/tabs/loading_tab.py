from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QLineEdit,
    QComboBox,
    QCheckBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator, QIntValidator, QValidator
import copy

from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import LOADING_ORCHESTRATOR_SCHEMA
from osdagbridge.desktop.ui.dialogs.tabs.ui_builder import UIBuilder


class LoadingTab(QWidget):
    """Container for all load sub-tabs."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # REQUIRED for Live Load defaults (referenced by sub-tabs)
        self.irc_vehicle_checkboxes = []
        self.irc_vehicle_labels = []
        self.braking_vehicle_checkboxes = []
        self.braking_vehicle_labels = []

        self._build_ui()

    def _build_ui(self):
        # Build UI from orchestrator schema
        UIBuilder(owner=self, schema=LOADING_ORCHESTRATOR_SCHEMA).build_tab(self)
        
        # UIBuilder sets objectName for the tab container
        self.load_tabs = self.findChild(QTabWidget, "loading_tabs")
        if self.load_tabs:
            self.load_tabs.setDocumentMode(True)
            self.load_tabs.setUsesScrollButtons(True)
            self.load_tabs.tabBar().setExpanding(False)
            self.load_tabs.setMovable(False)
            self.load_tabs.setStyleSheet(
                "QTabBar::scroller { width: 24px; }"
                "QTabBar::right-arrow { image: none; border: none; background: transparent; }"
                "QTabBar::left-arrow { image: none; border: none; background: transparent; }"
                "QTabBar::left-arrow:!enabled { width: 0px; }"
            )

    def collect_data(self) -> dict:
        """Unified data collection from all loading sub-tabs."""
        data = {}
        for attr in ["permanent_load_tab", "live_load_tab", "seismic_load_tab", 
                     "wind_load_tab", "temperature_load_tab", "custom_load_tab", "load_combination_tab"]:
            tab = getattr(self, attr, None)
            if hasattr(tab, "collect_data"):
                data.update(tab.collect_data())
        return data

    def restore_data(self, data: dict) -> None:
        """Unified data restoration to all loading sub-tabs."""
        for attr in ["permanent_load_tab", "live_load_tab", "seismic_load_tab", 
                     "wind_load_tab", "temperature_load_tab", "custom_load_tab", "load_combination_tab"]:
            tab = getattr(self, attr, None)
            if hasattr(tab, "restore_data"):
                tab.restore_data(data)

    def update_permanent_load_dependencies(self, has_median: bool, has_footpath: bool):
        """Forward dependency updates to sub-tabs."""
        if hasattr(self, "load_tabs"):
            for i in range(self.load_tabs.count()):
                tab = self.load_tabs.widget(i)
                if hasattr(tab, "update_dependency_states"):
                    tab.update_dependency_states(
                        has_median=has_median,
                        has_footpath=has_footpath
                    )

    def reset_defaults(self):
        """Reset all loading sub-tabs to default values"""
        for tab_attr in ["permanent_load_tab", "live_load_tab", "seismic_load_tab", 
                         "wind_load_tab", "temperature_load_tab", "custom_load_tab"]:
            tab = getattr(self, tab_attr, None)
            if tab and hasattr(tab, "reset_defaults"):
                tab.reset_defaults()

    def _format_field_name(self, name: str) -> str:
        return str(name or "field").replace("_", " ").strip().title()

    def _build_named_widget_map(self):
        named_widgets = {}

        def collect(scope_obj, prefix=""):
            for attr_name, value in vars(scope_obj).items():
                if isinstance(value, (QLineEdit, QComboBox, QCheckBox)):
                    key = f"{prefix}.{attr_name}" if prefix else attr_name
                    named_widgets[key] = value

        collect(self)
        for tab_name in (
            "permanent_load_tab",
            "live_load_tab",
            "seismic_load_tab",
            "wind_load_tab",
            "temperature_load_tab",
            "custom_load_tab",
            "load_combination_tab",
        ):
            tab = getattr(self, tab_name, None)
            if tab is not None:
                collect(tab, tab_name)

        return named_widgets

    def _sync_load_combo_included_flags(self):
        tab = getattr(self, "load_combination_tab", None)
        table = getattr(tab, "load_combo_table", None) if tab else None
        if not tab or table is None:
            return

        for row_idx in range(table.rowCount()):
            if row_idx >= len(self.load_combo_items):
                break
            included = False
            checkbox_widget = table.cellWidget(row_idx, 2)
            if checkbox_widget is not None:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox is not None:
                    included = checkbox.isChecked()
            self.load_combo_items[row_idx]["included"] = included

    def validate_tab(self):
        errors = []
        named_widgets = self._build_named_widget_map()
        active_tab = self.load_tabs.currentWidget() if hasattr(self, "load_tabs") else None
        active_tab_name = None
        for tab_name in (
            "permanent_load_tab",
            "live_load_tab",
            "seismic_load_tab",
            "wind_load_tab",
            "temperature_load_tab",
            "custom_load_tab",
            "load_combination_tab",
        ):
            if getattr(self, tab_name, None) is active_tab:
                active_tab_name = tab_name
                break

        custom_entry_fields = {
            "custom_load_case_name_input",
            "custom_point_left_input",
            "custom_point_bearing_input",
            "custom_line_left_start",
            "custom_line_left_end",
            "custom_line_bearing_start",
            "custom_line_bearing_end",
        }

        for key, widget in named_widgets.items():
            if not isinstance(widget, QLineEdit):
                continue

            key_parts = key.split(".", 1)
            if len(key_parts) == 2:
                key_tab_name, attr_name = key_parts
                if active_tab_name and key_tab_name != active_tab_name:
                    continue
            else:
                attr_name = key_parts[0]

            if active_tab_name == "custom_load_tab" and attr_name in custom_entry_fields:
                continue

            if not widget.isEnabled() or widget.isReadOnly():
                continue
            if not widget.isVisible():
                continue

            field_name = self._format_field_name(key.split(".")[-1])
            text = widget.text().strip()
            if not text:
                errors.append(f"{field_name} cannot be empty.")
                continue

            validator = widget.validator()
            if validator is None:
                continue

            state = validator.validate(text, 0)[0]
            if state == QValidator.Acceptable:
                continue

            if isinstance(validator, (QDoubleValidator, QIntValidator)):
                errors.append(
                    f"{field_name} must be between {validator.bottom()} and {validator.top()}."
                )
            else:
                errors.append(f"{field_name} has invalid value.")

        custom_load_tab = getattr(self, "custom_load_tab", None)
        if custom_load_tab is not None and hasattr(custom_load_tab, "_editing_load_data"):
            if getattr(custom_load_tab, "_editing_load_data", None):
                errors.append("Please save or clear the Custom Load currently being edited.")

        return list(dict.fromkeys(errors))

    def save_values(self):
        values = {}
        named_widgets = self._build_named_widget_map()

        for key, widget in named_widgets.items():
            if isinstance(widget, QLineEdit):
                values[key] = widget.text()
            elif isinstance(widget, QComboBox):
                values[key] = widget.currentText()
            elif isinstance(widget, QCheckBox):
                values[key] = widget.isChecked()

        if getattr(self, "irc_vehicle_labels", None) and getattr(self, "irc_vehicle_checkboxes", None):
            values["loading.irc_vehicle_checks"] = {
                lbl.text(): cb.isChecked()
                for lbl, cb in zip(self.irc_vehicle_labels, self.irc_vehicle_checkboxes)
            }

        if getattr(self, "braking_vehicle_labels", None) and getattr(self, "braking_vehicle_checkboxes", None):
            values["loading.braking_vehicle_checks"] = {
                lbl.text(): cb.isChecked()
                for lbl, cb in zip(self.braking_vehicle_labels, self.braking_vehicle_checkboxes)
            }

        self._sync_load_combo_included_flags()
        values["loading.custom_load_items"] = copy.deepcopy(self.custom_load_items)
        values["loading.load_combo_items"] = copy.deepcopy(self.load_combo_items)

        live_tab = getattr(self, "live_load_tab", None)
        if live_tab is not None:
            values["loading.live_custom_vehicles"] = copy.deepcopy(getattr(live_tab, "custom_vehicles", {}))
            values["loading.live_has_real_custom_vehicle"] = bool(getattr(live_tab, "has_real_custom_vehicle", False))

        return values

    def restore_values(self, data: dict):
        if not isinstance(data, dict):
            return

        named_widgets = self._build_named_widget_map()
        for key, value in data.items():
            if key not in named_widgets:
                continue
            widget = named_widgets[key]
            if isinstance(widget, QLineEdit):
                widget.setText(str(value))
            elif isinstance(widget, QComboBox):
                widget.setCurrentText(str(value))
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))

        custom_load_items = data.get("loading.custom_load_items")
        if isinstance(custom_load_items, list):
            self.custom_load_items.clear()
            self.custom_load_items.extend(copy.deepcopy(custom_load_items))
            if hasattr(self, "custom_load_tab") and hasattr(self.custom_load_tab, "_refresh_custom_load_table"):
                self.custom_load_tab._refresh_custom_load_table()

        load_combo_items = data.get("loading.load_combo_items")
        if isinstance(load_combo_items, list):
            self.load_combo_items.clear()
            self.load_combo_items.extend(copy.deepcopy(load_combo_items))
            if hasattr(self, "load_combination_tab") and hasattr(self.load_combination_tab, "_refresh_load_combo_table"):
                self.load_combination_tab._refresh_load_combo_table()

        irc_states = data.get("loading.irc_vehicle_checks")
        if isinstance(irc_states, dict):
            for lbl, cb in zip(getattr(self, "irc_vehicle_labels", []), getattr(self, "irc_vehicle_checkboxes", [])):
                cb.setChecked(bool(irc_states.get(lbl.text(), cb.isChecked())))

        braking_states = data.get("loading.braking_vehicle_checks")
        if isinstance(braking_states, dict):
            for lbl, cb in zip(getattr(self, "braking_vehicle_labels", []), getattr(self, "braking_vehicle_checkboxes", [])):
                cb.setChecked(bool(braking_states.get(lbl.text(), cb.isChecked())))

        live_tab = getattr(self, "live_load_tab", None)
        custom_vehicles = data.get("loading.live_custom_vehicles")
        if live_tab is not None and isinstance(custom_vehicles, dict):
            if hasattr(live_tab, "custom_vehicle_table"):
                live_tab.custom_vehicle_table.setRowCount(0)
                live_tab.custom_vehicles.clear()
                live_tab.has_real_custom_vehicle = bool(data.get("loading.live_has_real_custom_vehicle", bool(custom_vehicles)))
                for vehicle_name, vehicle_data in custom_vehicles.items():
                    merged = dict(vehicle_data)
                    merged["name"] = vehicle_name
                    if hasattr(live_tab, "_add_custom_vehicle"):
                        live_tab._add_custom_vehicle(merged)
