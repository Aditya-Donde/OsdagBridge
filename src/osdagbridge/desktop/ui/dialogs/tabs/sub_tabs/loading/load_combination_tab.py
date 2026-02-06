from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtWidgets import QHeaderView

from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style


class LoadCombinationTab(QWidget):
    """Load combination editor with add/edit modal."""

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.load_combo_items = getattr(owner, "load_combo_items", []) or [
            {"name": "DL + LL", "items": [{"case": "DL", "factor": "1.0"}, {"case": "LL", "factor": "1.0"}]},
            {
                "name": "1.35 DL + 1.5 LL",
                "items": [{"case": "DL", "factor": "1.35"}, {"case": "LL", "factor": "1.5"}],
            },
        ]
        owner.load_combo_items = self.load_combo_items
        self._build_ui()

    def _build_ui(self):
        owner = self.owner

        self.setStyleSheet("background-color: #f5f5f5;")
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(12, 12, 12, 12)
        page_layout.setSpacing(12)

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(16)

        heading_style = "font-size: 12px; font-weight: 700; color: #2b2b2b; background: transparent; border: none;"
        label_style = "font-size: 11px; color: #3a3a3a; background: transparent; border: none;"

        left_card = owner._create_card()
        left_card.setStyleSheet(
            "QFrame { border: 1px solid #b2b2b2; border-radius: 10px; background-color: #ffffff; }"
        )
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(10)

        title = QLabel("Inputs:")
        title.setStyleSheet(heading_style)
        left_layout.addWidget(title)

        combo_label = QLabel("Load Combination")
        combo_label.setStyleSheet(
            "font-size: 11px; font-style: italic; color: #2b2b2b; background: transparent; border: none;"
        )
        left_layout.addWidget(combo_label)

        auto_row = QHBoxLayout()
        auto_row.setSpacing(8)
        auto_row.setContentsMargins(0, 0, 0, 0)
        auto_label = QLabel("Auto include all IRC 6 Load Combinations")
        auto_label.setStyleSheet(label_style)
        owner.auto_include_checkbox = QCheckBox()
        auto_row.addWidget(auto_label)
        auto_row.addWidget(owner.auto_include_checkbox)
        auto_row.addStretch()
        left_layout.addLayout(auto_row)

        controls_row = QHBoxLayout()
        controls_row.setSpacing(6)
        owner.load_combo_add_btn = QPushButton("Add")
        owner.load_combo_edit_btn = QPushButton("Edit")
        owner.load_combo_delete_btn = QPushButton("Delete")
        for btn in (owner.load_combo_add_btn, owner.load_combo_edit_btn, owner.load_combo_delete_btn):
            btn.setFixedWidth(60)
            btn.setStyleSheet(
                "QPushButton { background: #ffffff; border: 1px solid #a0a0a0; border-radius: 3px; padding: 4px 10px; font-size: 11px; color: #2a2a2a; }"
                "QPushButton:hover { background: #f0f0f0; }"
                "QPushButton:pressed { background: #e0e0e0; }"
            )
            controls_row.addWidget(btn)
        controls_row.addStretch()
        left_layout.addLayout(controls_row)

        list_card = QFrame()
        list_card.setStyleSheet(
            "QFrame { border: 1px solid #a0a0a0; border-radius: 4px; background-color: #ffffff; }"
        )
        list_layout = QVBoxLayout(list_card)
        list_layout.setContentsMargins(10, 10, 10, 10)
        list_layout.setSpacing(6)

        self.load_combo_list_layout = QVBoxLayout()
        self.load_combo_list_layout.setContentsMargins(2, 2, 2, 2)
        self.load_combo_list_layout.setSpacing(6)
        list_layout.addLayout(self.load_combo_list_layout)
        left_layout.addWidget(list_card)
        left_layout.addStretch()

        right_card = owner._create_card()
        right_card.setStyleSheet(
            "QFrame { border: 1px solid #9c9c9c; border-radius: 10px; background-color: #c8c8c8; }"
        )
        right_card.setMinimumWidth(270)
        right_card.setMinimumHeight(360)
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(18, 18, 18, 18)
        right_layout.setSpacing(12)
        description_label = QLabel("Description Box")
        description_label.setAlignment(Qt.AlignCenter)
        description_label.setStyleSheet("font-size: 12px; font-weight: 700; color: #000000;")
        description_label.setMinimumHeight(320)
        right_layout.addWidget(description_label)

        content_row.addWidget(left_card, 3)
        content_row.addWidget(right_card, 2)

        page_layout.addLayout(content_row)

        owner.load_combo_add_btn.clicked.connect(self._on_add_load_combo)
        owner.load_combo_edit_btn.clicked.connect(self._on_edit_load_combo)
        owner.load_combo_delete_btn.clicked.connect(self._on_delete_load_combo)

        self._refresh_load_combo_list()

    def _refresh_load_combo_list(self):
        if not hasattr(self, "load_combo_list_layout"):
            return
        while self.load_combo_list_layout.count():
            item = self.load_combo_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.load_combo_checkboxes = []
        if not self.load_combo_items:
            empty_lbl = QLabel("No combinations added yet.")
            empty_lbl.setStyleSheet("font-size: 11px; color: #6a6a6a; background: transparent; border: none;")
            self.load_combo_list_layout.addWidget(empty_lbl)
            self.load_combo_list_layout.addStretch()
            return

        for combo in self.load_combo_items:
            row = QHBoxLayout()
            row.setContentsMargins(2, 0, 2, 0)
            row.setSpacing(6)
            label = QLabel(combo.get("name", "Combination"))
            label.setStyleSheet(
                "font-size: 11px; font-style: italic; color: #3a3a3a; background: transparent; border: none;"
            )
            checkbox = QCheckBox()
            row.addWidget(label)
            row.addStretch()
            row.addWidget(checkbox)
            container = QWidget()
            container.setLayout(row)
            self.load_combo_list_layout.addWidget(container)
            self.load_combo_checkboxes.append((combo, checkbox))

        self.load_combo_list_layout.addStretch()

    def _get_selected_load_combos(self):
        if not getattr(self, "load_combo_checkboxes", None):
            return []
        return [idx for idx, (_, cb) in enumerate(self.load_combo_checkboxes) if cb.isChecked()]

    def _on_add_load_combo(self):
        data = self._open_load_combo_dialog()
        if data:
            self.load_combo_items.append(data)
            self._refresh_load_combo_list()

    def _on_edit_load_combo(self):
        selected = self._get_selected_load_combos()
        if not selected:
            return
        if len(selected) > 1:
            return
        index = selected[0]
        current = self.load_combo_items[index]
        data = self._open_load_combo_dialog(existing=current)
        if data:
            self.load_combo_items[index] = data
            self._refresh_load_combo_list()

    def _on_delete_load_combo(self):
        selected = self._get_selected_load_combos()
        if not selected:
            return
        self.load_combo_items = [item for idx, item in enumerate(self.load_combo_items) if idx not in selected]
        self.owner.load_combo_items = self.load_combo_items
        self._refresh_load_combo_list()

    def _open_load_combo_dialog(self, existing=None):
        dialog = QDialog(self)
        dialog.setModal(True)
        dialog.setWindowTitle("Edit Load Combination" if existing else "Add Load Combination")
        dialog.setMinimumWidth(520)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        label_style = "font-size: 11px; color: #2a2a2a; background: transparent; border: none;"

        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        name_label = QLabel("Combination Name:")
        name_label.setStyleSheet(label_style)
        name_input = QLineEdit()
        name_input.setMinimumWidth(220)
        apply_field_style(name_input)
        name_row.addWidget(name_label)
        name_row.addWidget(name_input, 1)
        layout.addLayout(name_row)

        fields_row = QGridLayout()
        fields_row.setContentsMargins(0, 0, 0, 0)
        fields_row.setHorizontalSpacing(10)
        fields_row.setVerticalSpacing(6)

        load_case_label = QLabel("Load Case:")
        load_case_label.setStyleSheet(label_style)
        load_case_combo = QComboBox()
        load_case_combo.addItems(["DL", "SIDL", "LL", "WL", "EL", "IMF", "TL"])
        apply_field_style(load_case_combo)

        factor_label = QLabel("Partial Safety Factor:")
        factor_label.setStyleSheet(label_style)
        factor_input = QLineEdit()
        factor_input.setText("1.0")
        factor_input.setMinimumWidth(80)
        apply_field_style(factor_input)

        fields_row.addWidget(load_case_label, 0, 0, Qt.AlignLeft)
        fields_row.addWidget(load_case_combo, 0, 1, Qt.AlignLeft)
        fields_row.addWidget(factor_label, 0, 2, Qt.AlignLeft)
        fields_row.addWidget(factor_input, 0, 3, Qt.AlignLeft)
        fields_row.setColumnStretch(4, 1)
        layout.addLayout(fields_row)

        table_row = QHBoxLayout()
        table_row.setSpacing(8)

        table = QTableWidget(0, 3)
        table.setHorizontalHeaderLabels(["S.No", "Load Case", "Partial Safety Factor"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.setStyleSheet(
            "QTableWidget { background: #ffffff; } QHeaderView::section { color: #2a2a2a; background: #efefef; font-size: 10px; }"
        )
        table.setMinimumHeight(220)

        button_col = QVBoxLayout()
        button_col.setSpacing(6)
        add_btn = QPushButton("Add")
        modify_btn = QPushButton("Modify")
        delete_btn = QPushButton("Delete")
        for btn in (add_btn, modify_btn, delete_btn):
            btn.setFixedWidth(80)
            btn.setStyleSheet(
                "QPushButton { background: #ffffff; border: 1px solid #a0a0a0; border-radius: 3px; padding: 5px 12px; font-size: 11px; color: #2a2a2a; }"
                "QPushButton:hover { background: #f0f0f0; }"
                "QPushButton:pressed { background: #e0e0e0; }"
            )
            button_col.addWidget(btn)
        button_col.addStretch()

        table_row.addWidget(table, 1)
        table_row.addLayout(button_col)
        layout.addLayout(table_row)

        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, 4, 0, 0)
        action_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        save_btn = QPushButton("Save")
        for btn in (cancel_btn, save_btn):
            btn.setFixedWidth(80)
            btn.setStyleSheet(
                "QPushButton { background: #c8c8c8; border: 1px solid #a0a0a0; border-radius: 3px; padding: 6px 14px; font-weight: 600; font-size: 11px; color: #2a2a2a; }"
                "QPushButton:hover { background: #d8d8d8; }"
                "QPushButton:pressed { background: #b8b8b8; }"
            )
        action_row.addWidget(cancel_btn)
        action_row.addWidget(save_btn)
        layout.addLayout(action_row)

        def refresh_row_numbers():
            for row_idx in range(table.rowCount()):
                item = table.item(row_idx, 0)
                if item:
                    item.setText(str(row_idx + 1))

        def add_row():
            case_text = load_case_combo.currentText().strip()
            factor_text = factor_input.text().strip() or "1.0"
            row_idx = table.rowCount()
            table.insertRow(row_idx)
            table.setItem(row_idx, 0, QTableWidgetItem(str(row_idx + 1)))
            table.setItem(row_idx, 1, QTableWidgetItem(case_text))
            table.setItem(row_idx, 2, QTableWidgetItem(factor_text))
            refresh_row_numbers()

        def modify_row():
            row_idx = table.currentRow()
            if row_idx < 0:
                return
            table.setItem(row_idx, 1, QTableWidgetItem(load_case_combo.currentText().strip()))
            table.setItem(row_idx, 2, QTableWidgetItem(factor_input.text().strip() or "1.0"))
            refresh_row_numbers()

        def delete_row():
            row_idx = table.currentRow()
            if row_idx < 0:
                return
            table.removeRow(row_idx)
            refresh_row_numbers()

        def load_existing():
            if not existing:
                return
            name_input.setText(existing.get("name", ""))
            for item in existing.get("items", []):
                case_text = item.get("case", "")
                factor_text = item.get("factor", "")
                if case_text:
                    load_case_combo.setCurrentText(case_text)
                factor_input.setText(factor_text or "1.0")
                add_row()

        def on_save():
            name_text = name_input.text().strip() or "Load Combination"
            rows = []
            for row_idx in range(table.rowCount()):
                case_item = table.item(row_idx, 1)
                factor_item = table.item(row_idx, 2)
                if not case_item or not factor_item:
                    continue
                rows.append({"case": case_item.text(), "factor": factor_item.text()})
            if not rows:
                return
            dialog.accept()
            dialog.result_data = {"name": name_text, "items": rows}

        add_btn.clicked.connect(add_row)
        modify_btn.clicked.connect(modify_row)
        delete_btn.clicked.connect(delete_row)
        save_btn.clicked.connect(on_save)
        cancel_btn.clicked.connect(dialog.reject)

        load_existing()

        if dialog.exec() == QDialog.Accepted:
            return getattr(dialog, "result_data", None)
        return None
