from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QFrame, QTableWidget, QTableWidgetItem,
    QWidget,
)
from PySide6.QtWidgets import QHeaderView

from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox, MessageBoxType


class LoadCombinationDialog(QDialog):
    """
    Dialog for adding/editing a load combination.

    Call _collect() after exec() == Accepted to get result dict:
        {"name": str, "included": True, "items": [{"case": str, "factor": str}]}
    """

    def __init__(self, owner, existing: dict | None = None, load_combo_items: list | None = None, parent=None):
        super().__init__(parent)
        self._owner            = owner
        self._existing         = existing
        self._load_combo_items = load_combo_items or []
        self._build_ui()

    def _build_ui(self):
        self.setObjectName("LoadCombinationDialog")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self.setStyleSheet("""
            QDialog#LoadCombinationDialog, QWidget#LoadCombinationContent {
                background-color: #ffffff;
            }
            QDialog#LoadCombinationDialog {
                border: 1px solid rgba(144, 175, 19, 140);
                border-radius: 4px;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        title_bar = CustomTitleBar()
        title_bar.setObjectName("LoadComboTitleBar")
        title_bar.setTitle("Edit Load Combination" if self._existing else "Add Load Combination")
        title_bar.setStyleSheet("""
            QWidget#LoadComboTitleBar { background-color: transparent; }
            QToolButton#CloseButton {
                background-color: transparent; border: none;
                color: #2b2b2b; font-size: 16px;
            }
            QToolButton#CloseButton:hover { background-color: #e81123; color: white; }
            QToolButton#CloseButton:pressed { background-color: #c50d1c; }
        """)
        main_layout.addWidget(title_bar)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: rgba(144, 175, 19, 85);")
        main_layout.addWidget(sep)

        content = QWidget(self)
        content.setObjectName("LoadCombinationContent")
        main_layout.addWidget(content, 1)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        _label_style = "font-size: 11px; color: #2a2a2a; background: transparent; border: none;"
        _btn_style = (
            "QPushButton { background:#ffffff; border:1px solid #a0a0a0; border-radius:4px;"
            " padding:6px 12px; font-size:11px; font-weight:500; color:#2a2a2a; }"
            "QPushButton:hover { background:#f0f0f0; border:1px solid #808080; }"
            "QPushButton:pressed { background:#e0e0e0; }"
        )

        # ── Name ──────────────────────────────────────────────────────────
        name_row = QHBoxLayout()
        name_row.setSpacing(10)
        name_lbl = QLabel("Combination Name:")
        name_lbl.setStyleSheet(_label_style)
        name_lbl.setFixedWidth(140)
        self.name_input = QLineEdit()
        self.name_input.setMinimumWidth(120)
        apply_field_style(self.name_input)
        name_row.addWidget(name_lbl)
        name_row.addWidget(self.name_input)
        name_row.addStretch()
        layout.addLayout(name_row)

        # ── Input fields ──────────────────────────────────────────────────
        inp_frame = QFrame()
        inp_frame.setStyleSheet("QFrame { border: none; background: transparent; }")
        inp_layout = QVBoxLayout(inp_frame)
        inp_layout.setContentsMargins(12, 12, 12, 12)
        inp_layout.setSpacing(10)

        fields_row = QHBoxLayout()
        fields_row.setSpacing(12)

        load_case_lbl = QLabel("Load Case:")
        load_case_lbl.setStyleSheet(_label_style)
        self.load_case_combo = QComboBox()

        base_items   = ["DL", "DW", "SIDL", "LL", "WL", "EL", "TL"]
        custom_items = []
        if hasattr(self._owner, "custom_load_items"):
            for item in self._owner.custom_load_items:
                case = item.get("load_case", "")
                if case == "Custom":
                    cn = item.get("custom_load_case_name", "")
                    if cn and cn not in custom_items and cn not in base_items:
                        custom_items.append(cn)
                elif case and case not in custom_items and case not in base_items:
                    custom_items.append(case)

        self.load_case_combo.addItems(base_items + custom_items)
        self.load_case_combo.setMinimumWidth(100)
        apply_field_style(self.load_case_combo)

        factor_lbl = QLabel("Partial Safety Factor:")
        factor_lbl.setStyleSheet(_label_style)
        self.factor_input = QLineEdit()
        self.factor_input.setText("1.0")
        self.factor_input.setFixedWidth(100)
        apply_field_style(self.factor_input)

        fields_row.addWidget(load_case_lbl)
        fields_row.addWidget(self.load_case_combo)
        fields_row.addSpacing(20)
        fields_row.addWidget(factor_lbl)
        fields_row.addWidget(self.factor_input)
        fields_row.addStretch()
        inp_layout.addLayout(fields_row)
        layout.addWidget(inp_frame)

        # ── Table container ───────────────────────────────────────────────
        tbl_frame = QFrame()
        tbl_frame.setStyleSheet(
            "QFrame { border: 1px solid #c0c0c0; border-radius: 4px; background: #ffffff; }"
        )
        tbl_layout = QHBoxLayout(tbl_frame)
        tbl_layout.setContentsMargins(10, 10, 10, 10)
        tbl_layout.setSpacing(10)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["S.No", "Load Case", "Partial Safety Factor"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 60)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setMinimumHeight(250)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget { background:#ffffff; border:1px solid #d0d0d0;
                gridline-color:#e0e0e0; selection-background-color:#d0e8ff; }
            QTableWidget::item { padding:6px; color:#2a2a2a; font-size:11px;
                border-bottom:1px solid #e8e8e8; }
            QTableWidget::item:selected { background:#d0e8ff; color:#1a1a1a; }
            QHeaderView::section { background:#f0f0f0; color:#2a2a2a;
                font-size:11px; font-weight:600; padding:8px;
                border:1px solid #d0d0d0; border-bottom:2px solid #a0a0a0; }
        """)

        btn_col = QVBoxLayout()
        btn_col.setSpacing(8)
        self._add_row_btn    = QPushButton("Add")
        self._modify_row_btn = QPushButton("Modify")
        self._delete_row_btn = QPushButton("Delete")
        for btn in (self._add_row_btn, self._modify_row_btn, self._delete_row_btn):
            btn.setFixedWidth(90)
            btn.setFixedHeight(32)
            btn.setStyleSheet(_btn_style)
            btn_col.addWidget(btn)
        btn_col.addStretch()

        tbl_layout.addWidget(self.table, 1)
        tbl_layout.addLayout(btn_col)
        layout.addWidget(tbl_frame)

        # ── Action buttons ────────────────────────────────────────────────
        _action_style = (
            "QPushButton { background:#c8c8c8; border:1px solid #a0a0a0; border-radius:4px;"
            " padding:8px 16px; font-weight:600; font-size:11px; color:#2a2a2a; }"
            "QPushButton:hover { background:#d8d8d8; }"
            "QPushButton:pressed { background:#b8b8b8; }"
        )
        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, 8, 0, 0)
        action_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        save_btn   = QPushButton("Save")
        for btn in (cancel_btn, save_btn):
            btn.setFixedWidth(100)
            btn.setFixedHeight(36)
            btn.setStyleSheet(_action_style)
        action_row.addWidget(cancel_btn)
        action_row.addSpacing(8)
        action_row.addWidget(save_btn)
        layout.addLayout(action_row)

        # ── Connections ───────────────────────────────────────────────────
        self._add_row_btn.clicked.connect(self._add_row)
        self._modify_row_btn.clicked.connect(self._modify_row)
        self._delete_row_btn.clicked.connect(self._delete_row)
        save_btn.clicked.connect(self._on_save)
        cancel_btn.clicked.connect(self.reject)
        self.table.itemSelectionChanged.connect(self._on_table_selection_changed)

        self._load_existing()

    # ── Table operations ───────────────────────────────────────────────────

    def _refresh_row_numbers(self):
        for i in range(self.table.rowCount()):
            item = self.table.item(i, 0)
            if item:
                item.setText(str(i + 1))
            else:
                it = QTableWidgetItem(str(i + 1))
                it.setTextAlignment(Qt.AlignCenter)
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(i, 0, it)

    def _add_row(self):
        case   = self.load_case_combo.currentText().strip()
        factor = self.factor_input.text().strip() or "1.0"
        
        if not case:
            return

        # Partial safety factor validation
        try:
            factor_val = float(factor)
            if not (1.0 <= factor_val <= 2.0):
                CustomMessageBox(
                    title="Invalid Factor",
                    text="Partial Safety Factor must be between 1.0 and 2.0.",
                    buttons=["OK"],
                    dialogType=MessageBoxType.Warning,
                ).exec()
                return
        except ValueError:
            CustomMessageBox(
                title="Invalid Factor",
                text="Partial Safety Factor must be a number.",
                buttons=["OK"],
                dialogType=MessageBoxType.Warning,
            ).exec()
            return

        row = self.table.rowCount()
        self.table.insertRow(row)
        for col, (text, align) in enumerate([
            (str(row + 1), Qt.AlignCenter),
            (case,         Qt.AlignLeft | Qt.AlignVCenter),
            (factor,       Qt.AlignLeft | Qt.AlignVCenter),
        ]):
            it = QTableWidgetItem(text)
            it.setTextAlignment(align)
            it.setFlags(it.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, col, it)
        self._refresh_row_numbers()
        self.factor_input.setText("1.0")

    def _modify_row(self):
        row = self.table.currentRow()
        if row < 0:
            return
        case   = self.load_case_combo.currentText().strip()
        factor = self.factor_input.text().strip() or "1.0"
        for col, text in [(1, case), (2, factor)]:
            it = QTableWidgetItem(text)
            it.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            it.setFlags(it.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, col, it)

    def _delete_row(self):
        row = self.table.currentRow()
        if row < 0:
            return
        self.table.removeRow(row)
        self._refresh_row_numbers()

    def _on_table_selection_changed(self):
        row = self.table.currentRow()
        if row >= 0:
            case_item   = self.table.item(row, 1)
            factor_item = self.table.item(row, 2)
            if case_item:
                self.load_case_combo.setCurrentText(case_item.text())
            if factor_item:
                self.factor_input.setText(factor_item.text())

    def _load_existing(self):
        if not self._existing:
            return
        self.name_input.setText(self._existing.get("name", ""))
        for item in self._existing.get("items", []):
            self.load_case_combo.setCurrentText(item.get("case", ""))
            self.factor_input.setText(item.get("factor", "1.0"))
            self._add_row()

    # ── Save / Collect ─────────────────────────────────────────────────────
    def _on_save(self):
        name = self.name_input.text().strip() or "Load Combination"
        
        # Duplicate name check
        existing_names = [
            item.get("name") for item in self._load_combo_items
            if item != self._existing
        ]
        if name in existing_names:
            CustomMessageBox(
                title="Duplicate Name",
                text=f"A load combination named '{name}' already exists.",
                buttons=["OK"],
                dialogType=MessageBoxType.Warning,
            ).exec()
            return

        # Empty table check
        if self.table.rowCount() == 0:
            CustomMessageBox(
                title="Empty Combination",
                text="Please add at least one load case.",
                buttons=["OK"],
                dialogType=MessageBoxType.Warning,
            ).exec()
            return

        self.accept()

    def _collect(self) -> dict:
        """Call after exec() == Accepted. Returns combination dict."""
        name  = self.name_input.text().strip() or "Load Combination"
        items = []
        for row in range(self.table.rowCount()):
            case_item   = self.table.item(row, 1)
            factor_item = self.table.item(row, 2)
            if case_item and factor_item:
                items.append({
                    "case":   case_item.text(),
                    "factor": factor_item.text(),
                })
        return {
            "name":     name,
            "included": self._existing.get("included", True) if self._existing else True,
            "items":    items,
        }