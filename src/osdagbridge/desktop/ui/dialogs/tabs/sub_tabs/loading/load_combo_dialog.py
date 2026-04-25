from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox, MessageBoxType
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar


class LoadComboDialog(QDialog):
    """Dialog for adding / editing a single load combination entry."""

    def __init__(self, parent, existing=None, existing_names=None):
        super().__init__(parent)
        self._existing_names = existing_names or []
        self._result = None

        self.setObjectName("LoadCombinationDialog")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        self.setStyleSheet(
            """
            QDialog#LoadCombinationDialog, QWidget#LoadCombinationContent {
                background-color: #ffffff;
            }
            QDialog#LoadCombinationDialog {
                border: 1px solid rgba(144, 175, 19, 140);
                border-radius: 4px;
            }
            """
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        title_bar = CustomTitleBar()
        title_bar.setObjectName("LoadComboTitleBar")
        title_bar.setTitle("Edit Load Combination" if existing else "Add Load Combination")
        title_bar.setStyleSheet(
            """
            QWidget#LoadComboTitleBar { background-color: transparent; }
            QToolButton#CloseButton {
                background-color: transparent; border: none;
                color: #2b2b2b; font-size: 16px;
            }
            QToolButton#CloseButton:hover { background-color: #e81123; color: white; }
            QToolButton#CloseButton:pressed { background-color: #c50d1c; }
            """
        )
        main_layout.addWidget(title_bar)

        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: rgba(144, 175, 19, 85);")
        main_layout.addWidget(separator)

        content = QWidget(self)
        content.setObjectName("LoadCombinationContent")
        main_layout.addWidget(content, 1)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        label_style = "font-size: 11px; color: #2a2a2a; background: transparent; border: none;"

        # ── Name row ────────────────────────────────────────────────────
        name_row = QHBoxLayout()
        name_row.setSpacing(10)
        name_lbl = QLabel("Combination Name:")
        name_lbl.setStyleSheet(label_style)
        name_lbl.setFixedWidth(140)
        self._name_input = QLineEdit()
        self._name_input.setMinimumWidth(120)
        apply_field_style(self._name_input)
        name_row.addWidget(name_lbl)
        name_row.addWidget(self._name_input)
        name_row.addStretch()
        layout.addLayout(name_row)

        # ── Load-case + factor inputs ────────────────────────────────────
        input_section = QFrame()
        input_section.setStyleSheet("QFrame { border: none; background-color: transparent; }")
        input_layout = QVBoxLayout(input_section)
        input_layout.setContentsMargins(12, 12, 12, 12)
        input_layout.setSpacing(10)

        fields_row = QHBoxLayout()
        fields_row.setSpacing(12)

        load_case_lbl = QLabel("Load Case:")
        load_case_lbl.setStyleSheet(label_style)
        self._load_case_combo = QComboBox()
        self._load_case_combo.addItems(self._build_load_case_choices(parent))
        self._load_case_combo.setMinimumWidth(100)
        apply_field_style(self._load_case_combo)

        factor_lbl = QLabel("Partial Safety Factor:")
        factor_lbl.setStyleSheet(label_style)
        self._factor_input = QLineEdit()
        self._factor_input.setText("1.0")
        self._factor_input.setFixedWidth(100)
        apply_field_style(self._factor_input)

        fields_row.addWidget(load_case_lbl)
        fields_row.addWidget(self._load_case_combo)
        fields_row.addSpacing(20)
        fields_row.addWidget(factor_lbl)
        fields_row.addWidget(self._factor_input)
        fields_row.addStretch()
        input_layout.addLayout(fields_row)
        layout.addWidget(input_section)

        # ── Table + side buttons ─────────────────────────────────────────
        table_container = QFrame()
        table_container.setStyleSheet(
            "QFrame { border: 1px solid #c0c0c0; border-radius: 4px; background-color: #ffffff; }"
        )
        tc_layout = QHBoxLayout(table_container)
        tc_layout.setContentsMargins(10, 10, 10, 10)
        tc_layout.setSpacing(10)

        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["S.No", "Load Case", "Partial Safety Factor"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self._table.setColumnWidth(0, 60)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setSelectionMode(QTableWidget.SingleSelection)
        self._table.setMinimumHeight(250)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet(
            """
            QTableWidget {
                background-color: #ffffff; border: 1px solid #d0d0d0;
                gridline-color: #e0e0e0; selection-background-color: #d0e8ff;
            }
            QTableWidget::item {
                padding: 6px; color: #2a2a2a; font-size: 11px;
                border-bottom: 1px solid #e8e8e8;
            }
            QTableWidget::item:selected { background-color: #d0e8ff; color: #1a1a1a; }
            QHeaderView::section {
                background-color: #f0f0f0; color: #2a2a2a; font-size: 11px;
                font-weight: 600; padding: 8px; border: 1px solid #d0d0d0;
                border-bottom: 2px solid #a0a0a0;
            }
            QHeaderView::section:horizontal { border-top: none; }
            """
        )

        btn_style = (
            "QPushButton { background: #ffffff; border: 1px solid #a0a0a0; border-radius: 4px;"
            " padding: 6px 12px; font-size: 11px; font-weight: 500; color: #2a2a2a; }"
            " QPushButton:hover { background: #f0f0f0; border: 1px solid #808080; }"
            " QPushButton:pressed { background: #e0e0e0; }"
        )

        button_col = QVBoxLayout()
        button_col.setSpacing(8)
        for label, handler in (
            ("Add", self._add_row),
            ("Modify", self._modify_row),
            ("Delete", self._delete_row),
        ):
            btn = QPushButton(label)
            btn.setFixedWidth(90)
            btn.setFixedHeight(32)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(handler)
            button_col.addWidget(btn)
        button_col.addStretch()

        tc_layout.addWidget(self._table, 1)
        tc_layout.addLayout(button_col)
        layout.addWidget(table_container)

        # ── Cancel / Save ────────────────────────────────────────────────
        action_style = (
            "QPushButton { background: #c8c8c8; border: 1px solid #a0a0a0; border-radius: 4px;"
            " padding: 8px 16px; font-weight: 600; font-size: 11px; color: #2a2a2a; }"
            " QPushButton:hover { background: #d8d8d8; }"
            " QPushButton:pressed { background: #b8b8b8; }"
        )
        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, 8, 0, 0)
        action_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        save_btn = QPushButton("Save")
        for btn in (cancel_btn, save_btn):
            btn.setFixedWidth(100)
            btn.setFixedHeight(36)
            btn.setStyleSheet(action_style)
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self._on_save)
        action_row.addWidget(cancel_btn)
        action_row.addSpacing(8)
        action_row.addWidget(save_btn)
        layout.addLayout(action_row)

        self._table.itemSelectionChanged.connect(self._on_table_selection_changed)

        self._load_existing(existing)

    # ------------------------------------------------------------------ #

    def result_data(self):
        return self._result

    @staticmethod
    def _build_load_case_choices(parent):
        base = ["DL", "DW", "SIDL", "LL", "WL", "EL", "TL"]
        custom = []
        for item in getattr(getattr(parent, "owner", parent), "custom_load_items", []):
            case = item.get("load_case", "")
            if case == "Custom":
                name = item.get("custom_load_case_name", "")
                if name and name not in custom and name not in base:
                    custom.append(name)
            elif case and case not in custom and case not in base:
                custom.append(case)
        return base + custom

    def _add_row(self):
        case = self._load_case_combo.currentText().strip()
        factor = self._factor_input.text().strip() or "1.0"
        if not case:
            return
        row_idx = self._table.rowCount()
        self._table.insertRow(row_idx)
        self._table.setItem(row_idx, 0, self._make_item(str(row_idx + 1), Qt.AlignCenter))
        self._table.setItem(row_idx, 1, self._make_item(case))
        self._table.setItem(row_idx, 2, self._make_item(factor))
        self._refresh_row_numbers()
        self._factor_input.setText("1.0")

    def _modify_row(self):
        row_idx = self._table.currentRow()
        if row_idx < 0:
            return
        case = self._load_case_combo.currentText().strip()
        factor = self._factor_input.text().strip() or "1.0"
        self._table.setItem(row_idx, 1, self._make_item(case))
        self._table.setItem(row_idx, 2, self._make_item(factor))

    def _delete_row(self):
        row_idx = self._table.currentRow()
        if row_idx < 0:
            return
        self._table.removeRow(row_idx)
        self._refresh_row_numbers()

    def _on_table_selection_changed(self):
        row_idx = self._table.currentRow()
        if row_idx < 0:
            return
        case_item = self._table.item(row_idx, 1)
        factor_item = self._table.item(row_idx, 2)
        if case_item:
            self._load_case_combo.setCurrentText(case_item.text())
        if factor_item:
            self._factor_input.setText(factor_item.text())

    def _on_save(self):
        name = self._name_input.text().strip() or "Load Combination"
        if name in self._existing_names:
            CustomMessageBox(
                title="Duplicate Name",
                text=f"A load combination named '{name}' already exists. Please choose a different name.",
                buttons=["OK"],
                dialogType=MessageBoxType.Warning,
            ).exec()
            return
        rows = []
        for row_idx in range(self._table.rowCount()):
            c = self._table.item(row_idx, 1)
            f = self._table.item(row_idx, 2)
            if c and f:
                rows.append({"case": c.text(), "factor": f.text()})
        if not rows:
            return
        self._result = {"name": name, "items": rows}
        self.accept()

    def _load_existing(self, existing):
        if not existing:
            return
        self._name_input.setText(existing.get("name", ""))
        for item in existing.get("items", []):
            case = item.get("case", "")
            factor = item.get("factor", "1.0")
            if case:
                self._load_case_combo.setCurrentText(case)
                self._factor_input.setText(factor)
                self._add_row()

    def _refresh_row_numbers(self):
        for row_idx in range(self._table.rowCount()):
            item = self._table.item(row_idx, 0)
            if item:
                item.setText(str(row_idx + 1))
            else:
                self._table.setItem(row_idx, 0, self._make_item(str(row_idx + 1), Qt.AlignCenter))

    @staticmethod
    def _make_item(text: str, alignment=Qt.AlignLeft | Qt.AlignVCenter) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setTextAlignment(alignment)
        item.setFlags(Qt.ItemIsEnabled)
        return item
