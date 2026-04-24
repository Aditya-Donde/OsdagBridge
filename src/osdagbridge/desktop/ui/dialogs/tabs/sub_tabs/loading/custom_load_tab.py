from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidgetItem, QWidget

from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import (
    CUSTOM_LOAD_TAB_SCHEMA,
)
from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox, MessageBoxType
from osdagbridge.desktop.ui.dialogs.tabs import schema_io
from osdagbridge.desktop.ui.dialogs.tabs.ui_builder import UIBuilder


class CustomLoadTab(QWidget):

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.custom_load_items = getattr(owner, "custom_load_items", [])
        owner.custom_load_items = self.custom_load_items
        self.schema = CUSTOM_LOAD_TAB_SCHEMA
        self._editing_load_data = None

        UIBuilder(owner=self, schema=self.schema).build_tab(self)

        if hasattr(self, "custom_load_table_add_btn"):
            self.custom_load_table_add_btn.hide()
        if hasattr(self, "custom_edit_btn"):
            self.custom_edit_btn.clicked.connect(self._on_edit_custom_load)
        if hasattr(self, "custom_delete_btn"):
            self.custom_delete_btn.clicked.connect(self._on_delete_custom_load)

        self.reset_defaults()

    def reset_defaults(self):
        schema_io.reset_defaults(self, self.schema, before=self._before_reset, after=self._after_reset)

    def _before_reset(self):
        self.custom_load_items.clear()
        self._editing_load_data = None
        if hasattr(self, "custom_load_table"):
            self.custom_load_table.setRowCount(0)

    def _after_reset(self):
        self._reset_form_fields()
        self._refresh_custom_load_table()

    def _reset_form_fields(self):
        if hasattr(self, "custom_load_case_combo"):
            self.custom_load_case_combo.setCurrentText("DL")
        if hasattr(self, "custom_load_case_name_input"):
            self.custom_load_case_name_input.clear()
            self.custom_load_case_name_input.setEnabled(False)
        if hasattr(self, "custom_load_type_combo"):
            self.custom_load_type_combo.setCurrentText("Point")
        for bind_name in (
            "custom_point_left_input",
            "custom_point_bearing_input",
            "custom_line_left_start",
            "custom_line_left_end",
            "custom_line_bearing_start",
            "custom_line_bearing_end",
        ):
            widget = getattr(self, bind_name, None)
            if widget is not None:
                widget.clear()

    def _on_custom_load_type_changed(self, _text):
        # The stacked section switches pages automatically via schema switch_source.
        return

    def _on_load_case_changed(self, text):
        is_custom = text == "Custom"
        self.custom_load_case_name_input.setEnabled(is_custom)
        if not is_custom:
            self.custom_load_case_name_input.clear()

    def _refresh_custom_load_table(self):
        self.custom_load_table.setRowCount(0)

        for row_idx, load_data in enumerate(self.custom_load_items):
            self.custom_load_table.insertRow(row_idx)

            load_case = load_data.get("load_case", "")
            load_case_display = (
                load_data.get("custom_load_case_name", "custom")
                if load_case == "Custom"
                else load_case
            )

            item = QTableWidgetItem(load_case_display)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.custom_load_table.setItem(row_idx, 0, item)

            load_type = load_data.get("load_type", "")
            item = QTableWidgetItem(load_type)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.custom_load_table.setItem(row_idx, 1, item)

            if load_type == "Point":
                dist_left = load_data.get("point_left", "")
                dist_bearing = load_data.get("point_bearing", "")
            else:
                dist_left = f"{load_data.get('line_left_start', '')} - {load_data.get('line_left_end', '')}"
                dist_bearing = f"{load_data.get('line_bearing_start', '')} - {load_data.get('line_bearing_end', '')}"

            item = QTableWidgetItem(dist_left)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.custom_load_table.setItem(row_idx, 2, item)

            item = QTableWidgetItem(dist_bearing)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.custom_load_table.setItem(row_idx, 3, item)

    def _on_save_custom_load(self):
        load_data = {
            "load_case": self.custom_load_case_combo.currentText(),
            "load_type": self.custom_load_type_combo.currentText(),
        }

        if load_data["load_case"] == "Custom":
            custom_name = self.custom_load_case_name_input.text().strip()
            if not custom_name:
                CustomMessageBox(
                    title="Invalid Input",
                    text="Please provide a name for the Custom load case.",
                    buttons=["OK"],
                    dialogType=MessageBoxType.Warning,
                ).exec()
                return
            load_data["custom_load_case_name"] = custom_name

        if load_data["load_type"] == "Point":
            point_l = self.custom_point_left_input.text().strip()
            point_b = self.custom_point_bearing_input.text().strip()
            if not point_l or not point_b:
                CustomMessageBox(
                    title="Invalid Input",
                    text="Please fill in all distance fields for the Point load.",
                    buttons=["OK"],
                    dialogType=MessageBoxType.Warning,
                ).exec()
                return
            load_data["point_left"] = point_l
            load_data["point_bearing"] = point_b
        else:
            line_l_start = self.custom_line_left_start.text().strip()
            line_l_end = self.custom_line_left_end.text().strip()
            line_b_start = self.custom_line_bearing_start.text().strip()
            line_b_end = self.custom_line_bearing_end.text().strip()

            if not line_l_start or not line_l_end or not line_b_start or not line_b_end:
                CustomMessageBox(
                    title="Invalid Input",
                    text="Please fill in all distance fields for the Line/Area load.",
                    buttons=["OK"],
                    dialogType=MessageBoxType.Warning,
                ).exec()
                return

            try:
                if float(line_l_start) > float(line_l_end):
                    CustomMessageBox(
                        title="Invalid Input",
                        text="Distance from Left Edge Start cannot be greater than End.",
                        buttons=["OK"],
                        dialogType=MessageBoxType.Warning,
                    ).exec()
                    return
                if float(line_b_start) > float(line_b_end):
                    CustomMessageBox(
                        title="Invalid Input",
                        text="Distance from Bearing Start cannot be greater than End.",
                        buttons=["OK"],
                        dialogType=MessageBoxType.Warning,
                    ).exec()
                    return
            except ValueError:
                CustomMessageBox(
                    title="Invalid Input",
                    text="Distance fields must be numeric.",
                    buttons=["OK"],
                    dialogType=MessageBoxType.Warning,
                ).exec()
                return

            load_data["line_left_start"] = line_l_start
            load_data["line_left_end"] = line_l_end
            load_data["line_bearing_start"] = line_b_start
            load_data["line_bearing_end"] = line_b_end

        if self._editing_load_data:
            for idx, item in enumerate(self.custom_load_items):
                if item == self._editing_load_data:
                    self.custom_load_items[idx] = load_data
                    break
            self._editing_load_data = None
        else:
            self.custom_load_items.append(load_data)

        self._reset_form_fields()
        self._refresh_custom_load_table()

        CustomMessageBox(
            title="Saved",
            text="Custom load has been saved.",
            buttons=["OK"],
            dialogType=MessageBoxType.Success,
        ).exec()

    def _on_edit_custom_load(self):
        selected_rows = self.custom_load_table.selectionModel().selectedRows()
        if len(selected_rows) == 0:
            CustomMessageBox(
                title="Edit",
                text="Please select one custom load to edit.",
                buttons=["OK"],
                dialogType=MessageBoxType.Information,
            ).exec()
            return
        if len(selected_rows) > 1:
            CustomMessageBox(
                title="Edit",
                text="Please select only one custom load to edit.",
                buttons=["OK"],
                dialogType=MessageBoxType.Information,
            ).exec()
            return

        row_idx = selected_rows[0].row()
        load_data = self.custom_load_items[row_idx]
        self._editing_load_data = load_data

        load_case = load_data.get("load_case", "DL")
        index = self.custom_load_case_combo.findText(load_case)
        if index >= 0:
            self.custom_load_case_combo.setCurrentIndex(index)

        if load_case == "Custom":
            self.custom_load_case_name_input.setText(load_data.get("custom_load_case_name", ""))

        load_type = load_data.get("load_type", "Point")
        index = self.custom_load_type_combo.findText(load_type)
        if index >= 0:
            self.custom_load_type_combo.setCurrentIndex(index)

        if load_type == "Point":
            self.custom_point_left_input.setText(load_data.get("point_left", ""))
            self.custom_point_bearing_input.setText(load_data.get("point_bearing", ""))
        else:
            self.custom_line_left_start.setText(load_data.get("line_left_start", ""))
            self.custom_line_left_end.setText(load_data.get("line_left_end", ""))
            self.custom_line_bearing_start.setText(load_data.get("line_bearing_start", ""))
            self.custom_line_bearing_end.setText(load_data.get("line_bearing_end", ""))

    def _on_delete_custom_load(self):
        selected_rows = self.custom_load_table.selectionModel().selectedRows()
        if len(selected_rows) == 0:
            CustomMessageBox(
                title="Delete",
                text="Please select at least one custom load to delete.",
                buttons=["OK"],
                dialogType=MessageBoxType.Information,
            ).exec()
            return

        rows_to_delete = sorted([row.row() for row in selected_rows], reverse=True)
        for row_idx in rows_to_delete:
            if 0 <= row_idx < len(self.custom_load_items):
                del self.custom_load_items[row_idx]

        self._editing_load_data = None
        self._refresh_custom_load_table()

        CustomMessageBox(
            title="Deleted",
            text=f"{len(rows_to_delete)} custom load(s) deleted.",
            buttons=["OK"],
            dialogType=MessageBoxType.Information,
        ).exec()
