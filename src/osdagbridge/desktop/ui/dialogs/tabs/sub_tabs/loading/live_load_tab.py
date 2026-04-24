from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QPushButton,
    QTableWidgetItem,
    QWidget,
)

from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import (
    LIVE_LOAD_TAB_SCHEMA,
)
from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox, MessageBoxType
from osdagbridge.desktop.ui.dialogs.tabs import schema_io
from osdagbridge.desktop.ui.dialogs.tabs.custom_vehicle_dialog import CustomVehicleDialog
from osdagbridge.desktop.ui.dialogs.tabs.ui_builder import UIBuilder


class LiveLoadTab(QWidget):
    """Live Load tab rendered from LIVE_LOAD_TAB_SCHEMA."""

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.schema = LIVE_LOAD_TAB_SCHEMA
        self.custom_vehicles = {}
        self.has_real_custom_vehicle = False

        UIBuilder(owner=self, schema=self.schema).build_tab(self)

        if hasattr(self, "custom_vehicle_add_button"):
            self.custom_vehicle_add_button.clicked.connect(self.show_custom_vehicle_dialog)

        self.reset_defaults()

    def reset_defaults(self):
        schema_io.reset_defaults(self, self.schema, before=self._before_reset, after=self._after_reset)

    def _before_reset(self):
        if hasattr(self, "custom_vehicle_table"):
            self.custom_vehicle_table.setRowCount(0)
        self.custom_vehicles.clear()
        self.has_real_custom_vehicle = False

    def _after_reset(self):
        self._update_custom_vehicle_table_height()
        self._update_custom_vehicle_box_height()
        self._update_custom_vehicle_header()
        self._update_braking_vehicles_section()
        self._on_footpath_mode_changed(getattr(self, "footpath_mode_combo", None).currentText() if hasattr(self, "footpath_mode_combo") else "")
        self._sync_owner_refs()

    def _sync_owner_refs(self):
        self.owner.irc_vehicle_checkboxes = list(getattr(self, "irc_vehicle_checkboxes", []))
        self.owner.irc_vehicle_labels = list(getattr(self, "irc_vehicle_labels", []))
        self.owner.braking_vehicle_checkboxes = list(getattr(self, "braking_vehicle_checkboxes", []))
        self.owner.braking_vehicle_labels = list(getattr(self, "braking_vehicle_labels", []))

    def _on_footpath_mode_changed(self, mode):
        is_custom = mode == "User-defined"
        if hasattr(self, "footpath_value_input"):
            self.footpath_value_input.setEnabled(is_custom)
            if not is_custom:
                self.footpath_value_input.clear()

    def _update_braking_vehicles_section(self):
        layout = getattr(self, "braking_checkboxes_layout", None)
        if layout is None:
            return

        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub_item = item.layout().takeAt(0)
                    if sub_item.widget():
                        sub_item.widget().deleteLater()

        irc_section = next((s for s in self.schema.get("sections", []) if s.get("id") == "irc_vehicles_section"), None)
        irc_vehicles = irc_section.get("items", []) if irc_section else []
        irc_braking_vehicles = [vehicle for vehicle in irc_vehicles if vehicle == "Class SV"]
        custom_vehicle_names = list(self.custom_vehicles.keys()) if self.has_real_custom_vehicle else []
        all_braking_vehicles = irc_braking_vehicles + custom_vehicle_names

        self.braking_vehicle_checkboxes = []
        self.braking_vehicle_labels = []
        label_width = self.schema.get("label_width", 220)
        field_height = self.schema.get("field_height", 28)
        braking_section = next((s for s in self.schema.get("sections", []) if s.get("id") == "braking_section"), None)
        default_checked = braking_section.get("default_checked", True) if braking_section else True

        for vehicle in all_braking_vehicles:
            row = QHBoxLayout()
            row.setSpacing(10)

            label = self._make_plain_label(vehicle)
            label.setMinimumWidth(label_width)

            checkbox = QCheckBox()
            checkbox.setChecked(default_checked)
            checkbox.setFixedHeight(field_height)

            row.addWidget(label)
            row.addWidget(checkbox)
            row.addStretch()
            layout.addLayout(row)

            self.braking_vehicle_checkboxes.append(checkbox)
            self.braking_vehicle_labels.append(label)

        self._sync_owner_refs()

    def show_custom_vehicle_dialog(self):
        dialog = CustomVehicleDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self._add_custom_vehicle(dialog.vehicle_data)

    def _add_custom_vehicle(self, vehicle_data):
        if not self.has_real_custom_vehicle:
            self.custom_vehicle_table.setRowCount(0)
            self.custom_vehicles.clear()
            self.has_real_custom_vehicle = True

        name = vehicle_data["name"]
        if name in self.custom_vehicles:
            CustomMessageBox(
                title="Duplicate Vehicle",
                text=f"Custom vehicle '{name}' already exists.",
                buttons=["OK"],
                dialogType=MessageBoxType.Warning,
            ).exec()
            return

        self.custom_vehicles[name] = vehicle_data
        row = self.custom_vehicle_table.rowCount()
        self.custom_vehicle_table.insertRow(row)
        field_height = self.schema.get("field_height", 28)

        name_item = QTableWidgetItem(name)
        name_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        name_item.setFlags(Qt.ItemIsEnabled)
        self.custom_vehicle_table.setItem(row, 0, name_item)

        checkbox = QCheckBox()
        checkbox.setChecked(True)
        self.custom_vehicle_table.setCellWidget(row, 1, self._wrap_cell_widget(checkbox))

        edit_btn = QPushButton("Edit")
        edit_btn.setFixedSize(48, field_height)
        edit_btn.setStyleSheet(self._table_button_style())
        edit_btn.clicked.connect(lambda _, vehicle_name=name: self._edit_custom_vehicle(vehicle_name))
        self.custom_vehicle_table.setCellWidget(row, 2, self._wrap_cell_widget(edit_btn))

        delete_btn = QPushButton("Delete")
        delete_btn.setFixedSize(60, field_height)
        delete_btn.setStyleSheet(self._table_button_style())
        delete_btn.clicked.connect(lambda _, vehicle_name=name: self._delete_custom_vehicle(vehicle_name))
        self.custom_vehicle_table.setCellWidget(row, 3, self._wrap_cell_widget(delete_btn))

        self.custom_vehicle_table.setRowHeight(row, field_height + 4)
        self._update_custom_vehicle_table_height()
        self._update_custom_vehicle_box_height()
        self._update_custom_vehicle_header()
        self._update_braking_vehicles_section()

    def _edit_custom_vehicle(self, name):
        vehicle_data = self.custom_vehicles[name]
        dialog = CustomVehicleDialog(self)
        dialog.load_vehicle_data(vehicle_data)

        if dialog.exec() != QDialog.Accepted:
            return

        new_data = dialog.vehicle_data
        new_name = new_data["name"]

        if new_name != name and new_name in self.custom_vehicles:
            CustomMessageBox(
                title="Duplicate Vehicle",
                text=f"Custom vehicle '{new_name}' already exists.",
                buttons=["OK"],
                dialogType=MessageBoxType.Warning,
            ).exec()
            return

        if new_name != name:
            self.custom_vehicles.pop(name)
            self.custom_vehicles[new_name] = new_data
            for row in range(self.custom_vehicle_table.rowCount()):
                item = self.custom_vehicle_table.item(row, 0)
                if item and item.text() == name:
                    item.setText(new_name)
                    break
            self._update_braking_vehicles_section()
            return

        self.custom_vehicles[name] = new_data

    def _delete_custom_vehicle(self, name):
        reply = CustomMessageBox(
            title="Delete Vehicle",
            text=f"Delete custom vehicle '{name}'?",
            buttons=["Yes", "No"],
            dialogType=MessageBoxType.Warning,
        ).exec()

        if reply != "Yes":
            return

        self.custom_vehicles.pop(name, None)

        for row in range(self.custom_vehicle_table.rowCount()):
            item = self.custom_vehicle_table.item(row, 0)
            if item and item.text() == name:
                self.custom_vehicle_table.removeRow(row)
                break

        self.has_real_custom_vehicle = self.custom_vehicle_table.rowCount() > 0
        self.custom_vehicle_table.viewport().update()
        self._update_custom_vehicle_table_height()
        self._update_custom_vehicle_box_height()
        self._update_custom_vehicle_header()
        self._update_braking_vehicles_section()

    def _update_custom_vehicle_table_height(self):
        if not hasattr(self, "custom_vehicle_table"):
            return
        rows = self.custom_vehicle_table.rowCount()
        if rows == 0:
            self.custom_vehicle_table.setFixedHeight(0)
            return

        total_height = sum(self.custom_vehicle_table.rowHeight(row) for row in range(rows)) + 4
        self.custom_vehicle_table.setFixedHeight(min(total_height, 150))

    def _update_custom_vehicle_header(self):
        has_vehicles = hasattr(self, "custom_vehicle_table") and self.custom_vehicle_table.rowCount() > 0
        if hasattr(self, "custom_vehicle_header_label"):
            self.custom_vehicle_header_label.setVisible(has_vehicles)
        if hasattr(self, "custom_vehicle_add_button"):
            self.custom_vehicle_add_button.setText("Add" if has_vehicles else "Add Custom Vehicle")

    def _update_custom_vehicle_box_height(self):
        if not hasattr(self, "custom_vehicle_box"):
            return

        rows = self.custom_vehicle_table.rowCount() if hasattr(self, "custom_vehicle_table") else 0
        field_height = self.schema.get("field_height", 28)
        base_height = field_height + 24 + 8

        if rows == 0:
            self.custom_vehicle_box.setFixedHeight(base_height)
            return

        table_height = self.custom_vehicle_table.height()
        self.custom_vehicle_box.setFixedHeight(base_height + table_height)

    @staticmethod
    def _make_plain_label(text: str):
        from PySide6.QtWidgets import QLabel

        label = QLabel(text)
        label.setStyleSheet(
            "font-size: 11px; font-weight: 600; color: #3a3a3a; background: transparent; border: none;"
        )
        return label

    @staticmethod
    def _wrap_cell_widget(widget):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(widget, 0, Qt.AlignVCenter)
        layout.addStretch()
        return container

    @staticmethod
    def _table_button_style():
        return (
            "QPushButton { background-color: white; border: 1px solid #3a3a3a; "
            "border-radius: 3px; font-size: 10px; font-weight: 600; color: #3a3a3a; padding: 0px; } "
            "QPushButton:hover { background-color: #f8f8f8; }"
        )
