from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHeaderView, QWidget, QCheckBox

from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import (
    LOAD_COMBINATION_TAB_SCHEMA,
)
from osdagbridge.desktop.ui.dialogs.tabs import schema_io
from osdagbridge.desktop.ui.dialogs.tabs.additional_inputs.sub_tabs.loading.load_combo_dialog import LoadComboDialog
from osdagbridge.desktop.ui.dialogs.tabs.base import SchemaTab
from osdagbridge.desktop.ui.dialogs.tabs.builder import UIBuilder
import copy


class LoadCombinationTab(SchemaTab):
    schema = LOAD_COMBINATION_TAB_SCHEMA

    def __init__(self, owner, parent=None):
        super().__init__(owner, parent)
        self.load_combo_items = []
        self._sync_owner_items()

        self.load_combo_table = self.custom_load_combo_table
        self._configure_table()

        self.load_combo_add_btn.clicked.connect(self._on_add_load_combo)
        self.load_combo_edit_btn.clicked.connect(self._on_edit_load_combo)
        self.load_combo_delete_btn.clicked.connect(self._on_delete_load_combo)
        self.load_combo_table.itemSelectionChanged.connect(self._on_table_selection_changed)

        self.reset_defaults()

    def collect_data(self) -> dict:
        data = super().collect_data()
        self._sync_load_combo_included_flags()
        data["loading.load_combo_items"] = copy.deepcopy(self.load_combo_items)
        return data

    def restore_data(self, data: dict) -> None:
        super().restore_data(data)
        items = data.get("loading.load_combo_items")
        if isinstance(items, list):
            self.load_combo_items = copy.deepcopy(items)
            self._sync_owner_items()
            self._refresh_load_combo_table()

    def reset_defaults(self):
        schema_io.reset_defaults(self, LOAD_COMBINATION_TAB_SCHEMA, before=self._before_reset, after=self._after_reset)

    def _before_reset(self):
        self.load_combo_items.clear()
        self._sync_owner_items()
        if hasattr(self, "load_combo_table"):
            self.load_combo_table.setRowCount(0)

    def _after_reset(self):
        self._sync_owner_items()
        self._refresh_load_combo_table()
        self._on_table_selection_changed()

    def _sync_owner_items(self):
        owner = getattr(self, "owner", None)
        if owner is not None:
            owner.load_combo_items = self.load_combo_items

    def _configure_table(self):
        header = self.load_combo_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        self.load_combo_table.setColumnWidth(0, 80)
        self.load_combo_table.setColumnWidth(2, 100)
        self.load_combo_table.verticalHeader().setDefaultSectionSize(40)

    def _sync_load_combo_included_flags(self):
        for row_idx in range(self.load_combo_table.rowCount()):
            if row_idx >= len(self.load_combo_items):
                break
            included = False
            checkbox_widget = self.load_combo_table.cellWidget(row_idx, 2)
            if checkbox_widget is not None:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox is not None:
                    included = checkbox.isChecked()
            self.load_combo_items[row_idx]["included"] = included

    def _refresh_load_combo_table(self):
        has_items = bool(self.load_combo_items)
        self.custom_combo_title.setVisible(has_items)

        self.load_combo_table.setRowCount(0)
        if not has_items:
            self.load_combo_table.setVisible(False)
            return

        self.load_combo_table.setVisible(True)
        for idx, combo in enumerate(self.load_combo_items):
            UIBuilder.build_table_row(self.load_combo_table, [
                {"type": "text", "value": str(idx + 1), "alignment": Qt.AlignCenter},
                {"type": "text", "value": combo.get("name", "Combination")},
                {"type": "checkbox", "checked": combo.get("included", False), "align": Qt.AlignCenter},
            ], row_height=40)

        row_count = self.load_combo_table.rowCount()
        row_h = self.load_combo_table.verticalHeader().defaultSectionSize()
        header_h = self.load_combo_table.horizontalHeader().height()
        self.load_combo_table.setFixedHeight(max(180, min(header_h + row_count * row_h + 8, 260)))

    def _get_selected_load_combo_index(self):
        current_row = self.load_combo_table.currentRow()
        if current_row < 0 or current_row >= len(self.load_combo_items):
            return None
        return current_row

    def _on_table_selection_changed(self):
        has_selection = bool(self.load_combo_table.selectedItems())
        self.load_combo_edit_btn.setVisible(has_selection)
        self.load_combo_delete_btn.setVisible(has_selection)

    def _on_add_load_combo(self):
        data = self._open_load_combo_dialog()
        if data:
            self.load_combo_items.append(data)
            self._sync_owner_items()
            self._refresh_load_combo_table()
            self._on_table_selection_changed()

    def _on_edit_load_combo(self):
        index = self._get_selected_load_combo_index()
        if index is None:
            return
        data = self._open_load_combo_dialog(existing=self.load_combo_items[index])
        if data:
            self.load_combo_items[index] = data
            self._sync_owner_items()
            self._refresh_load_combo_table()
            self._on_table_selection_changed()

    def _on_delete_load_combo(self):
        index = self._get_selected_load_combo_index()
        if index is None:
            return
        self.load_combo_items.pop(index)
        self._sync_owner_items()
        self._refresh_load_combo_table()
        self._on_table_selection_changed()

    def _open_load_combo_dialog(self, existing=None):
        names = [item.get("name") for item in self.load_combo_items if item != existing]
        dialog = LoadComboDialog(self, existing=existing, existing_names=names)
        if dialog.exec() == QDialog.Accepted:
            return dialog.result_data()
        return None
