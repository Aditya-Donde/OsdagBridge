from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QSizePolicy,
)


class CustomVehicleWidget(QWidget):

    def __init__(self, field_id: str, on_click: str, owner, ai, parent=None):
        super().__init__(parent)
        self._field_id = field_id
        self._on_click = on_click
        self._owner    = owner
        self._ai       = ai
        self._data: list = []
        self.setObjectName(field_id)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        _btn_style = (
            "QPushButton { background:white; border:1px solid #3a3a3a;"
            " border-radius:3px; font-size:10px; font-weight:600;"
            " color:#3a3a3a; padding:3px 8px; }"
            "QPushButton:hover { background:#f8f8f8; }"
        )

        LABEL_WIDTH = 220

        # ── Header row ────────────────────────────────────────────────────────
        header_row = QHBoxLayout()
        header_row.setSpacing(10)
        header_row.setContentsMargins(0, 0, 0, 0)

        self._header_label = QLabel("Custom Vehicle")
        self._header_label.setStyleSheet(
            "font-size: 11px; font-weight: 700; color: #3a3a3a;"
            " background: transparent; border: none;"
        )
        self._header_label.setFixedWidth(LABEL_WIDTH)
        self._header_label.setVisible(False)
        header_row.addWidget(self._header_label)
        
        self.add_btn = QPushButton("Add Custom Vehicle")
        self.add_btn.setStyleSheet(_btn_style)
        self.add_btn.setFixedHeight(28)
        header_row.addWidget(self.add_btn)
        header_row.addStretch()
        layout.addLayout(header_row)

        # ── Table ─────────────────────────────────────────────────────────────
        self.table = QTableWidget(0, 4)
        self.table.setObjectName(self._field_id + "_table")
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setShowGrid(False)
        self.table.setFrameShape(QTableWidget.NoFrame)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.table.setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(32)
        self.table.horizontalHeader().setStretchLastSection(False)

        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Fixed)
        h.setSectionResizeMode(1, QHeaderView.Fixed)
        h.setSectionResizeMode(2, QHeaderView.Fixed)
        h.setSectionResizeMode(3, QHeaderView.Fixed)
        self.table.setColumnWidth(0, LABEL_WIDTH)
        self.table.setColumnWidth(1, 36)
        self.table.setColumnWidth(2, 52)
        self.table.setColumnWidth(3, 64)

        self.table.setStyleSheet("""
            QTableWidget { border:none; background:transparent; }
            QTableWidget::item { padding:2px 0; border:none;
                color:#3a3a3a; font-size:11px; }
        """)
        layout.addWidget(self.table)

        self.add_btn.clicked.connect(self._on_add)

    # ── Public ─────────────────────────────────────────────────────────────

    def update(self, data: list):
        self._data = list(data)
        self.table.setRowCount(0)

        has = bool(data)
        self.table.setVisible(has)
        self._header_label.setVisible(has)
        self.add_btn.setText("Add" if has else "Add Custom Vehicle")

        _btn_style = (
            "QPushButton { background:white; border:1px solid #3a3a3a;"
            " border-radius:3px; font-size:10px; font-weight:600;"
            " color:#3a3a3a; padding:0px; }"
            "QPushButton:hover { background:#f8f8f8; }"
        )

        for idx, vehicle in enumerate(data):
            name = vehicle.get("name", "")
            self.table.insertRow(idx)
            self.table.setRowHeight(idx, 32)

            name_item = QTableWidgetItem(name)
            name_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            name_item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(idx, 0, name_item)

            cb = QCheckBox()
            cb.setChecked(vehicle.get("included", True))
            cb.setStyleSheet("QCheckBox { spacing:0; background:transparent; }")
            cb_container = QWidget()
            cb_container.setStyleSheet("background:transparent;")
            cb_layout = QHBoxLayout(cb_container)
            cb_layout.setContentsMargins(0, 0, 0, 0)
            cb_layout.addWidget(cb, 0, Qt.AlignVCenter)
            cb_layout.addStretch()
            cb.stateChanged.connect(
                lambda state, i=idx: self._on_included_changed(i, bool(state))
            )
            self.table.setCellWidget(idx, 1, cb_container)

            edit_btn = QPushButton("Edit")
            edit_btn.setFixedSize(48, 28)
            edit_btn.setStyleSheet(_btn_style)
            edit_btn.clicked.connect(lambda _, i=idx: self._on_edit(i))
            edit_container = QWidget()
            edit_container.setStyleSheet("background:transparent;")
            edit_layout = QHBoxLayout(edit_container)
            edit_layout.setContentsMargins(0, 0, 0, 0)
            edit_layout.addWidget(edit_btn, 0, Qt.AlignVCenter)
            edit_layout.addStretch()
            self.table.setCellWidget(idx, 2, edit_container)

            del_btn = QPushButton("Delete")
            del_btn.setFixedSize(60, 28)
            del_btn.setStyleSheet(_btn_style)
            del_btn.clicked.connect(lambda _, i=idx: self._on_delete(i))
            del_container = QWidget()
            del_container.setStyleSheet("background:transparent;")
            del_layout = QHBoxLayout(del_container)
            del_layout.setContentsMargins(0, 0, 0, 0)
            del_layout.addWidget(del_btn, 0, Qt.AlignVCenter)
            del_layout.addStretch()
            self.table.setCellWidget(idx, 3, del_container)

        self._adjust_table_height()

    # ── Private ────────────────────────────────────────────────────────────

    def _adjust_table_height(self):
        rows = self.table.rowCount()
        if rows == 0:
            self.table.setFixedHeight(0)
            return
        total = sum(self.table.rowHeight(r) for r in range(rows)) + 4
        self.table.setFixedHeight(min(total, 150))

    def _current_data(self) -> list:
        return list(self._data)

    def _save_data(self, data: list):
        if self._ai:
            self._ai._on_field_edited(self._field_id, data)
        self.update(data)

    def _on_add(self):
        if self._on_click and hasattr(self._owner, self._on_click):
            getattr(self._owner, self._on_click)(existing=None, widget=self)

    def _on_edit(self, idx: int):
        data = self._current_data()
        if idx < len(data):
            if self._on_click and hasattr(self._owner, self._on_click):
                getattr(self._owner, self._on_click)(existing=data[idx], widget=self)

    def _on_delete(self, idx: int):
        data = self._current_data()
        if idx < len(data):
            data.pop(idx)
            self._save_data(data)

    def _on_included_changed(self, idx: int, checked: bool):
        data = self._current_data()
        if idx < len(data):
            data[idx]["included"] = checked
            self._data = data
            if self._ai:
                self._ai._on_field_edited(self._field_id, data)