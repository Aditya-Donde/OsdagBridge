"""
Field Type for Custom-Load-Combinations in Additional Inputs dialog. Shows a table of combinations with Add/Modify/Delete buttons.
Part of UI-Builder
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QSizePolicy,
)
from osdagbridge.core.bridge_types.plate_girder.load_combinations import default_load_combination_entries

class LoadCombinationWidget(QWidget):
    """
    Self-contained widget — table + Add/Modify/Delete buttons.
    Populated from a list of dicts:
        [{"name": str, "included": bool, "items": [{"case": str, "factor": str}]}]
    """

    def __init__(self, field_id: str, on_click: str, owner, ai, parent=None):
        super().__init__(parent)
        self._field_id = field_id
        self._is_irc6_widget = (
            self._field_id == "irc6_default_combinations"
        )

        self._on_click = on_click
        self._owner    = owner
        self._ai       = ai
        self._data: list = []

        self.setObjectName(field_id)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # ── Button row ─────────────────────────────────────────────────────
        if not self._is_irc6_widget:
            btn_row = QHBoxLayout()
            btn_row.setSpacing(8)

            btn_style = (
                "QPushButton { background:#ffffff; border:1px solid #a0a0a0;"
                " border-radius:3px; padding:4px 10px; font-size:11px; color:#2a2a2a; }"
                "QPushButton:hover { background:#f0f0f0; }"
                "QPushButton:pressed { background:#e0e0e0; }"
            )

            self.add_btn    = QPushButton("Add Custom Combination")
            self.modify_btn = QPushButton("Modify")
            self.delete_btn = QPushButton("Delete")

            self.modify_btn.setVisible(False)
            self.delete_btn.setVisible(False)

            for btn in (self.add_btn, self.modify_btn, self.delete_btn):
                btn.setStyleSheet(btn_style)
                btn_row.addWidget(btn)

            btn_row.addStretch()
            layout.addLayout(btn_row)

        # ── Table ─────────────────────────────────────────────────────────
        self.table = QTableWidget(0, 2)
        self.table.setObjectName(self._field_id + "_table")
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 1200)
        self.table.setColumnWidth(1, 80)

        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(False)
        self.table.setVisible(False)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.table.setStyleSheet("""
            QTableWidget { background-color: transparent; border: none; }
            QTableWidget::item { padding: 6px; color: #000000; font-size: 11px; border: none; }
            QTableWidget::item:selected { background-color: transparent; color: #000000; }
        """)
        layout.addWidget(self.table)

        # ── Signals ────────────────────────────────────────────────────────
        if not self._is_irc6_widget:
            self.add_btn.clicked.connect(self._on_add)
            self.modify_btn.clicked.connect(self._on_modify)
            self.delete_btn.clicked.connect(self._on_delete)
            self.table.itemSelectionChanged.connect(self._on_selection_changed)
        else:
            self._populate_default_combinations()

    # ── Public ─────────────────────────────────────────────────────────────

    def update(self, data: list):
        """Refresh table from list of combination dicts."""
        self._data = list(data)
        self.table.setRowCount(0)

        if not data:
            self.table.setVisible(False)
            return

        self.table.setVisible(True)

        for idx, combo in enumerate(data):
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)

            name = QTableWidgetItem(combo.get("name", ""))
            name.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            name.setFlags(name.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_idx, 0, name)

            cb_container = QWidget()
            cb_container.setStyleSheet("background: transparent;")
            cb_layout = QHBoxLayout(cb_container)
            cb_layout.setContentsMargins(0, 0, 0, 0)
            cb_layout.setAlignment(Qt.AlignCenter)
            cb = QCheckBox()
            cb.setChecked(combo.get("included", True))
            cb.setStyleSheet("QCheckBox { spacing:0; background:transparent; }")
            cb.stateChanged.connect(
                lambda state, i=idx: self._on_included_changed(i, bool(state))
            )
            cb_layout.addWidget(cb)
            self.table.setCellWidget(row_idx, 1, cb_container)

        self._adjust_table_height()

    def collect(self) -> list:
        """Read current table state back into list of dicts."""
        if self._ai and hasattr(self._ai, "working_input_dict"):
            return self._ai.working_input_dict.get(self._field_id, [])
        return []
    
    def _on_included_changed(self, idx: int, checked: bool):
        if idx < len(self._data):
            self._data[idx]["included"] = checked
            if self._ai:
                self._ai._on_field_edited(self._field_id, self._data)

    # ── Private ────────────────────────────────────────────────────────────

    def _adjust_table_height(self):
        rows        = self.table.rowCount()
        row_height  = self.table.verticalHeader().defaultSectionSize()
        hdr_height  = self.table.horizontalHeader().height()
        new_height  = hdr_height + rows * row_height + 8
        new_height  = max(80, new_height)
        self.table.setFixedHeight(new_height)

    def _on_selection_changed(self):
        has = bool(self.table.selectedItems())
        self.modify_btn.setVisible(has)
        self.delete_btn.setVisible(has)

    def _current_data(self) -> list:
        return list(self._data)

    def _save_data(self, data: list):
        self._data = list(data)
        if self._ai:
            self._ai._on_field_edited(self._field_id, data)
        self.update(data)

    def _on_add(self):
        if self._on_click and hasattr(self._owner, self._on_click):
            getattr(self._owner, self._on_click)(widget=self)

    def _on_modify(self):
        row = self.table.currentRow()
        if row < 0:
            return
        data = self._current_data()
        if row < len(data):
            if self._on_click and hasattr(self._owner, self._on_click):
                getattr(self._owner, self._on_click)(existing=data[row], widget=self)

    def _on_delete(self):
        row = self.table.currentRow()
        if row < 0:
            return
        data = self._current_data()
        if row < len(data):
            data.pop(row)
            self._save_data(data)  

    def _populate_default_combinations(self):
        """
        Populate the table from the shared IRC6 combination expansion
        (single source of truth in ``default_load_combination_entries``,
        also used by the backend to build the results table).
        """
        self.table.setRowCount(0)
        self._data = [dict(e) for e in default_load_combination_entries()]

        for entry in self._data:
            row = self.table.rowCount()
            self.table.insertRow(row)

            name_item = QTableWidgetItem(entry['name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, name_item)

            cb_container = QWidget()
            cb_layout = QHBoxLayout(cb_container)
            cb_layout.setContentsMargins(0, 0, 0, 0)
            cb_layout.setAlignment(Qt.AlignCenter)
            cb = QCheckBox()
            cb.setChecked(bool(entry.get('included', True)))
            cb.stateChanged.connect(
                lambda state, i=row: self._on_included_changed(i, bool(state))
            )
            cb_layout.addWidget(cb)
            self.table.setCellWidget(row, 1, cb_container)

        self.table.setVisible(True)
        self._adjust_table_height()   

        if self._ai:
            self._ai._on_field_edited(self._field_id, self._data)