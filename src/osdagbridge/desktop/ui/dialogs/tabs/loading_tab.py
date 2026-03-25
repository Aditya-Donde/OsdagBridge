from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QFrame,
    QGridLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QCheckBox,
    QSizePolicy,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator, QIntValidator, QValidator
import copy

from osdagbridge.core.utils.common import VALUES_YES_NO
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.loading.permanent_load_tab import PermanentLoadTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.loading.live_load_tab import LiveLoadTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.loading.seismic_load_tab import SeismicLoadTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.loading.wind_load_tab import WindLoadTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.loading.temperature_load_tab import TemperatureLoadTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.loading.custom_load_tab import CustomLoadTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.loading.load_combination_tab import LoadCombinationTab


class LoadingTab(QWidget):
    """Container for all load sub-tabs."""

    def __init__(self, parent=None):
        super().__init__(parent)

    # REQUIRED for Live Load defaults (MUST be before _build_ui)
        self.irc_vehicle_checkboxes = []
        self.irc_vehicle_labels = []
        self.braking_vehicle_checkboxes = []
        self.braking_vehicle_labels = []

        self.custom_load_items = []
        self.load_combo_items = []

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.load_tabs = QTabWidget()
        self.load_tabs.setDocumentMode(True)

        self.load_tabs.setUsesScrollButtons(True)
        self.load_tabs.tabBar().setExpanding(False)

        self.load_tabs.setMovable(False)

        self.load_tabs.setStyleSheet(
           "QTabBar::scroller {"
            " width: 24px;"
            "}"

            "QTabBar::right-arrow {"
            " image: none;"
            " border: none;"
            " background: transparent;"
            "}"

            "QTabBar::left-arrow {"
            " image: none;"
            " border: none;"
            " background: transparent;"
            "}"

            "QTabBar::left-arrow:!enabled {"
            " width: 0px;"
            "}"

        )
        self.permanent_load_tab = PermanentLoadTab(self)
        self.live_load_tab = LiveLoadTab(self)
        self.seismic_load_tab = SeismicLoadTab(self)
        self.wind_load_tab = WindLoadTab(self)
        self.temperature_load_tab = TemperatureLoadTab(self)
        self.custom_load_tab = CustomLoadTab(self)
        self.load_combination_tab = LoadCombinationTab(self)

        self.load_tabs.addTab(self.permanent_load_tab, "Permanent Load")
        self.load_tabs.addTab(self.live_load_tab, "Live Load")
        self.load_tabs.addTab(self.seismic_load_tab, "Seismic Load")
        self.load_tabs.addTab(self.wind_load_tab, "Wind Load")
        self.load_tabs.addTab(self.temperature_load_tab, "Temperature Load")
        self.load_tabs.addTab(self.custom_load_tab, "Custom Load")
        self.load_tabs.addTab(self.load_combination_tab, "Load Combination")
        

        layout.addWidget(self.load_tabs)

    def _create_card(self):
        card = QFrame()
        card.setStyleSheet("QFrame { border: 1px solid #cfcfcf; border-radius: 12px; background-color: #ffffff; }")
        return card

    def _create_yes_no_combo(self):
        combo = QComboBox()
        combo.addItems(VALUES_YES_NO)
        combo.setCurrentText("Yes")
        apply_field_style(combo)
        return combo

    def _create_line_edit(self):
        line_edit = QLineEdit()
        apply_field_style(line_edit)
        return line_edit

    def _add_load_section(self, parent_layout, title, rows):
        title_label = QLabel(title)
        title_label.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: #3e3e3e; background: transparent; border: none;"
        )
        parent_layout.addWidget(title_label)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        grid.setColumnMinimumWidth(0, 230)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)

        field_width = 170

        for row_index, (label_text, widget) in enumerate(rows):
            label = QLabel(label_text)
            label.setStyleSheet("font-size: 11px; color: #4b4b4b; background: transparent; border: none;")
            grid.addWidget(label, row_index, 0, Qt.AlignLeft | Qt.AlignVCenter)
            widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            if isinstance(widget, (QComboBox, QLineEdit)):
                widget.setFixedWidth(field_width)
            grid.addWidget(widget, row_index, 1)

        parent_layout.addLayout(grid)

    def _add_checkbox_section(self, parent_layout, title, items):
        title_label = QLabel(title)
        title_label.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: #3e3e3e; background: transparent; border: none;"
        )
        parent_layout.addWidget(title_label)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        grid.setColumnStretch(0, 1)

        for row, name in enumerate(items):
            label = QLabel(name)
            if "Vehicle Name" in name:
                label.setStyleSheet(
                    "font-size: 11px; font-style: italic; color: #4b4b4b; background: transparent; border: none; padding: 0px;"
                )
            else:
                label.setStyleSheet(
                    "font-size: 11px; color: #4b4b4b; background: transparent; border: none; padding: 0px;"
                )
            checkbox = QCheckBox()
            checkbox.setChecked(False)

        # Store references for Live Load defaults
            if "Vehicles from IRC 6" in title:
                self.irc_vehicle_checkboxes.append(checkbox)
                self.irc_vehicle_labels.append(label)

            elif "Braking Load" in title:
                self.braking_vehicle_checkboxes.append(checkbox)
                self.braking_vehicle_labels.append(label)

            grid.addWidget(label, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
            grid.addWidget(checkbox, row, 1, Qt.AlignRight | Qt.AlignVCenter)

        parent_layout.addLayout(grid)

    def _on_footpath_mode_changed(self, mode):
        is_custom = mode == "User-defined"
        if hasattr(self, "footpath_value_input"):
            self.footpath_value_input.setEnabled(is_custom)
            if not is_custom:
                self.footpath_value_input.clear()

    def _on_dead_load_mode_changed(self, mode):
        is_custom = mode == "Custom"
        if hasattr(self, "dead_load_custom_input"):
            self.dead_load_custom_input.setEnabled(is_custom)
            if not is_custom:
                self.dead_load_custom_input.clear()

    def _on_live_load_mode_changed(self, mode):
        is_custom = mode == "Custom"
        if hasattr(self, "live_load_custom_input"):
            self.live_load_custom_input.setEnabled(is_custom)
            if not is_custom:
                self.live_load_custom_input.clear()

    def update_permanent_load_dependencies(self, has_median: bool, has_footpath: bool):
        """
        Forward dependency updates to PermanentLoadTab
        """
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

        if hasattr(self, "permanent_load_tab"):
            self.permanent_load_tab.reset_defaults()

        if hasattr(self, "live_load_tab") and hasattr(self.live_load_tab, "reset_defaults"):
            self.live_load_tab.reset_defaults()
        if hasattr(self, "seismic_load_tab") and hasattr(self.seismic_load_tab, "reset_defaults"):
            self.seismic_load_tab.reset_defaults()

        if hasattr(self, "wind_load_tab") and hasattr(self.wind_load_tab, "reset_defaults"):
            self.wind_load_tab.reset_defaults()

        if hasattr(self, "temperature_load_tab") and hasattr(self.temperature_load_tab, "reset_defaults"):
            self.temperature_load_tab.reset_defaults()
        if hasattr(self, "custom_load_tab") and hasattr(self.custom_load_tab, "reset_defaults"):
            self.custom_load_tab.reset_defaults()

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
        #Validate only fields from the currently active Loading sub-tab.
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

            # Validate only fields from the currently active Loading sub-tab.
            key_parts = key.split(".", 1)
            if len(key_parts) == 2:
                key_tab_name, attr_name = key_parts
                if active_tab_name and key_tab_name != active_tab_name:
                    continue
            else:
                attr_name = key_parts[0]

            # Custom Load Add/Edit inputs are transient and validated on tab-level Save.
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

        # Additional consistency checks for custom collections used in Loading.
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

        # Persist checkbox list states that are dynamically generated.
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
