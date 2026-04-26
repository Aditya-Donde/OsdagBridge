from PySide6.QtWidgets import QDialog, QWidget

from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import (
    LIVE_LOAD_TAB_SCHEMA,
)
from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox, MessageBoxType
from osdagbridge.desktop.ui.dialogs.tabs import schema_io
from osdagbridge.desktop.ui.dialogs.tabs.custom_vehicle_dialog import CustomVehicleDialog
from osdagbridge.desktop.ui.dialogs.tabs.builder import UIBuilder
from osdagbridge.desktop.ui.dialogs.tabs.base import SchemaTab


class LiveLoadTab(SchemaTab):
    schema = LIVE_LOAD_TAB_SCHEMA

    def __init__(self, owner, parent=None):
        super().__init__(owner, parent)
        self.custom_vehicles = {}
        self.has_real_custom_vehicle = False

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
        self._on_footpath_mode_changed(
            self.footpath_mode_combo.currentText() if hasattr(self, "footpath_mode_combo") else ""
        )
        self._sync_owner_refs()

    def _sync_owner_refs(self):
        self.owner.irc_vehicle_checkboxes = list(getattr(self, "irc_vehicle_checkboxes", []))
        self.owner.irc_vehicle_labels = list(getattr(self, "irc_vehicle_labels", []))
        self.owner.braking_vehicle_checkboxes = list(getattr(self, "braking_vehicle_checkboxes", []))
        self.owner.braking_vehicle_labels = list(getattr(self, "braking_vehicle_labels", []))

    def _extra_state(self):
        return {
            "loading.live_custom_vehicles": dict(self.custom_vehicles),
            "loading.live_has_real_custom_vehicle": bool(self.has_real_custom_vehicle),
            "loading.irc_vehicle_checks": {
                label.text(): checkbox.isChecked()
                for label, checkbox in zip(
                    getattr(self, "irc_vehicle_labels", []),
                    getattr(self, "irc_vehicle_checkboxes", []),
                )
            },
            "loading.braking_vehicle_checks": {
                label.text(): checkbox.isChecked()
                for label, checkbox in zip(
                    getattr(self, "braking_vehicle_labels", []),
                    getattr(self, "braking_vehicle_checkboxes", []),
                )
            },
        }

    def _restore_extra_state(self, data: dict):
        custom_vehicles = data.get("loading.live_custom_vehicles")
        if isinstance(custom_vehicles, dict):
            self.custom_vehicles = dict(custom_vehicles)
            self.has_real_custom_vehicle = bool(
                data.get("loading.live_has_real_custom_vehicle", bool(custom_vehicles))
            )
            if hasattr(self, "custom_vehicle_table"):
                self.custom_vehicle_table.setRowCount(0)
                for vehicle_name, vehicle_data in self.custom_vehicles.items():
                    merged = dict(vehicle_data)
                    merged["name"] = vehicle_name
                    self._add_custom_vehicle(merged)

        for state_key, labels_name, boxes_name in (
            ("loading.irc_vehicle_checks", "irc_vehicle_labels", "irc_vehicle_checkboxes"),
            ("loading.braking_vehicle_checks", "braking_vehicle_labels", "braking_vehicle_checkboxes"),
        ):
            states = data.get(state_key)
            if not isinstance(states, dict):
                continue
            for label, checkbox in zip(getattr(self, labels_name, []), getattr(self, boxes_name, [])):
                checkbox.setChecked(bool(states.get(label.text(), checkbox.isChecked())))

    def _on_footpath_mode_changed(self, mode):
        if mode != "User-defined" and hasattr(self, "footpath_value_input"):
            self.footpath_value_input.clear()

    def _update_braking_vehicles_section(self):
        layout = getattr(self, "braking_checkboxes_layout", None)
        if layout is None:
            return

        irc_section = next(
            (s for s in self.schema.get("sections", []) if s.get("id") == "irc_vehicles_section"), None
        )
        irc_vehicles = irc_section.get("items", []) if irc_section else []
        braking_section = next(
            (s for s in self.schema.get("sections", []) if s.get("id") == "braking_section"), None
        )
        default_checked = braking_section.get("default_checked", True) if braking_section else True
        all_vehicles = [v for v in irc_vehicles if v == "Class SV"] + (
            list(self.custom_vehicles.keys()) if self.has_real_custom_vehicle else []
        )

        self.braking_vehicle_checkboxes, self.braking_vehicle_labels = (
            UIBuilder.rebuild_dynamic_checkbox_list(
                layout,
                all_vehicles,
                default_checked=default_checked,
                label_width=self.schema.get("label_width", 220),
                field_height=self.schema.get("field_height", 28),
            )
        )
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
        field_height = self.schema.get("field_height", 28)
        UIBuilder.build_table_row(self.custom_vehicle_table, [
            {"type": "text", "value": name},
            {"type": "checkbox", "checked": True},
            {"type": "button", "text": "Edit",   "width": 48, "on_click": lambda _, n=name: self._edit_custom_vehicle(n)},
            {"type": "button", "text": "Delete", "width": 60, "on_click": lambda _, n=name: self._delete_custom_vehicle(n)},
        ], row_height=field_height + 4)

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
        total = sum(self.custom_vehicle_table.rowHeight(r) for r in range(rows)) + 4
        self.custom_vehicle_table.setFixedHeight(min(total, 150))

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
        else:
            self.custom_vehicle_box.setFixedHeight(base_height + self.custom_vehicle_table.height())
