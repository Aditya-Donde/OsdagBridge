from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHeaderView, QWidget

from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import (
    LOAD_COMBINATION_TAB_SCHEMA,
)
from osdagbridge.desktop.ui.dialogs.tabs import schema_io
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.loading.load_combo_dialog import LoadComboDialog
from osdagbridge.desktop.ui.dialogs.tabs.ui_builder import UIBuilder


class LoadCombinationTab(QWidget):

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.load_combo_items = getattr(owner, "load_combo_items", [])
        owner.load_combo_items = self.load_combo_items

        UIBuilder(owner=self, schema=LOAD_COMBINATION_TAB_SCHEMA).build_tab(self)

        self.load_combo_table = self.custom_load_combo_table
        self._configure_table()

        self.load_combo_add_btn.clicked.connect(self._on_add_load_combo)
        self.load_combo_edit_btn.clicked.connect(self._on_edit_load_combo)
        self.load_combo_delete_btn.clicked.connect(self._on_delete_load_combo)
        self.load_combo_table.itemSelectionChanged.connect(self._on_table_selection_changed)

        self.reset_defaults()

    def reset_defaults(self):
        schema_io.reset_defaults(self, LOAD_COMBINATION_TAB_SCHEMA, before=self._before_reset, after=self._after_reset)

    def _before_reset(self):
        self.load_combo_items.clear()
        if hasattr(self, "load_combo_table"):
            self.load_combo_table.setRowCount(0)

    def _after_reset(self):
        self._refresh_load_combo_table()
        self._on_table_selection_changed()

    def _configure_table(self):
        header = self.load_combo_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        self.load_combo_table.setColumnWidth(0, 80)
        self.load_combo_table.setColumnWidth(2, 100)
        self.load_combo_table.verticalHeader().setDefaultSectionSize(40)

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
            self._refresh_load_combo_table()
            self._on_table_selection_changed()

    def _on_edit_load_combo(self):
        index = self._get_selected_load_combo_index()
        if index is None:
            return
        data = self._open_load_combo_dialog(existing=self.load_combo_items[index])
        if data:
            self.load_combo_items[index] = data
            self._refresh_load_combo_table()
            self._on_table_selection_changed()

    def _on_delete_load_combo(self):
        index = self._get_selected_load_combo_index()
        if index is None:
            return
        self.load_combo_items.pop(index)
        self.owner.load_combo_items = self.load_combo_items
        self._refresh_load_combo_table()
        self._on_table_selection_changed()

    def _open_load_combo_dialog(self, existing=None):
        names = [item.get("name") for item in self.load_combo_items if item != existing]
        dialog = LoadComboDialog(self, existing=existing, existing_names=names)
        if dialog.exec() == QDialog.Accepted:
            return dialog.result_data()
        return None
