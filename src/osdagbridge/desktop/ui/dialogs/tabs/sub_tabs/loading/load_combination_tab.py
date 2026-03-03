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
from osdagbridge.desktop.ui.dialogs.custom_titlebar import CustomTitleBar
from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import (
    LOAD_COMBINATION_TAB_SCHEMA,
)

class LoadCombinationTab(QWidget):

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.load_combo_items = getattr(owner, "load_combo_items", [])
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

        left_card = owner._create_card()
        left_card.setStyleSheet(
            "QFrame { border: 1px solid #b2b2b2; border-radius: 10px; background-color: #ffffff; }"
        )
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(10)

        title = QLabel("Load Combination Inputs")
        title.setStyleSheet(heading_style)
        left_layout.addWidget(title)

        controls_row = self._build_controls_row()
        left_layout.addLayout(controls_row)

        self.load_combo_table = QTableWidget(0, 3)
        self.load_combo_table.setHorizontalHeaderLabels(["Sr. No.", "Combination Name", "Include"])
        self.load_combo_table.verticalHeader().setDefaultSectionSize(40)
        
        self.load_combo_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.load_combo_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.load_combo_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.load_combo_table.setColumnWidth(0, 80)
        self.load_combo_table.setColumnWidth(2, 100)
        
        self.load_combo_table.verticalHeader().setVisible(False)
        self.load_combo_table.horizontalHeader().setStretchLastSection(True)
        self.load_combo_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.load_combo_table.setSelectionMode(QTableWidget.SingleSelection)
        self.load_combo_table.setShowGrid(True)
        
        self.load_combo_table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #a0a0a0;
                border-radius: 4px;
                gridline-color: #d0d0d0;
                selection-background-color: #e3f2fd;
            }
            QTableWidget::item {
                padding: 8px;
                color: #2a2a2a;
                font-size: 11px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #1a1a1a;
            }
            QHeaderView::section {
                background-color: #f8f8f8;
                color: #2a2a2a;
                font-size: 11px;
                font-weight: 600;
                padding: 8px;
                border: none;
                border-right: 1px solid #d0d0d0;
                border-bottom: 1px solid #d0d0d0;
            }
            QHeaderView::section:last {
    
            }
        """)
        self.load_combo_table.setFixedHeight(180)
        self.load_combo_table.setMaximumHeight(260)
        self.load_combo_table.setAlternatingRowColors(False)
        
        left_layout.addWidget(self.load_combo_table)
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

        self._refresh_load_combo_table()

    def _build_controls_row(self):
        schema = LOAD_COMBINATION_TAB_SCHEMA
        controls_row = QHBoxLayout()
        controls_row.setSpacing(6)
        
        button_style = (
            "QPushButton { background: #ffffff; border: 1px solid #a0a0a0; border-radius: 3px; "
            "padding: 4px 10px; font-size: 11px; color: #2a2a2a; }"
            "QPushButton:hover { background: #f0f0f0; }"
            "QPushButton:pressed { background: #e0e0e0; }"
        )
        
        for btn_config in schema["controls"]:
            if btn_config["label"] == "Default":
                continue
            btn = QPushButton(btn_config["label"])
            btn.setFixedWidth(btn_config["width"])
            btn.setStyleSheet(button_style)
            setattr(self.owner, btn_config["bind"], btn)
            controls_row.addWidget(btn)
        
        controls_row.addStretch()
        return controls_row

    def _get_default_combos(self):
        return []

    def _refresh_load_combo_table(self):
        if not hasattr(self, "load_combo_table"):
            return
        
        self.load_combo_table.setRowCount(0)
        
        if not self.load_combo_items:
            self.load_combo_table.setFixedHeight(180)
            return

        
        for idx, combo in enumerate(self.load_combo_items):
            row_idx = self.load_combo_table.rowCount()
            self.load_combo_table.insertRow(row_idx)
            
            sr_no_item = QTableWidgetItem(str(idx + 1))
            sr_no_item.setTextAlignment(Qt.AlignCenter)
            sr_no_item.setFlags(sr_no_item.flags() & ~Qt.ItemIsEditable)
            self.load_combo_table.setItem(row_idx, 0, sr_no_item)
            
            name_item = QTableWidgetItem(combo.get("name", "Combination"))
            name_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.load_combo_table.setItem(row_idx, 1, name_item)
            
            checkbox_widget = QWidget()
            checkbox_widget.setStyleSheet("background-color: transparent;")
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            checkbox_layout.setSpacing(0)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            
            checkbox = QCheckBox()
            checkbox.setChecked(combo.get("included", False))
            checkbox.setFixedHeight(28)   
            checkbox.setStyleSheet("""
            QCheckBox {
                spacing: 0px;
                background-color: transparent;
            }
            """)
            checkbox.setChecked(combo.get("included", False))
            checkbox_layout.addWidget(checkbox)
            
            self.load_combo_table.setCellWidget(row_idx, 2, checkbox_widget)
                

        row_height = self.load_combo_table.verticalHeader().defaultSectionSize()
        header_height = self.load_combo_table.horizontalHeader().height()
        row_count = self.load_combo_table.rowCount()

        extra = 8
        new_height = header_height + (row_count * row_height) + extra
        new_height = max(180, min(new_height, 260))
        self.load_combo_table.setFixedHeight(new_height)


    def _get_selected_load_combo_index(self):
        current_row = self.load_combo_table.currentRow()
        if current_row < 0 or current_row >= len(self.load_combo_items):
            return None
        return current_row

    def _get_included_load_combos(self):
        included = []
        for row_idx in range(self.load_combo_table.rowCount()):
            checkbox_widget = self.load_combo_table.cellWidget(row_idx, 2)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    included.append(row_idx)
        return included

    def _on_add_load_combo(self):
        data = self._open_load_combo_dialog()
        if data:
            self.load_combo_items.append(data)
            self._refresh_load_combo_table()

    def _on_edit_load_combo(self):
        index = self._get_selected_load_combo_index()
        if index is None:
            return
        
        current = self.load_combo_items[index]
        data = self._open_load_combo_dialog(existing=current)
        if data:
            self.load_combo_items[index] = data
            self._refresh_load_combo_table()

    def _on_delete_load_combo(self):
        index = self._get_selected_load_combo_index()
        if index is None:
            return
        
        self.load_combo_items.pop(index)
        self.owner.load_combo_items = self.load_combo_items
        self._refresh_load_combo_table()

    def _open_load_combo_dialog(self, existing=None):
        dialog = QDialog(self)
        dialog.setObjectName("LoadCombinationDialog")
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        dialog.setModal(True)
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(500)
        
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)
        
        title_bar = CustomTitleBar()
        title_bar.setObjectName("LoadComboTitleBar")
        title_bar.setTitle("Edit Load Combination" if existing else "Add Load Combination")
        main_layout.addWidget(title_bar)
        
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: rgba(144, 175, 19, 85);")
        main_layout.addWidget(separator)

        content_widget = QWidget(dialog)
        main_layout.addWidget(content_widget, 1)
        
        dialog.setStyleSheet("""
        QDialog#LoadCombinationDialog {
            background-color: #ffffff;
            border: 1px solid rgba(144, 175, 19, 140);
            border-radius: 4px;
        }
        """)
        
        title_bar.setStyleSheet("""
            QWidget#LoadComboTitleBar {
                background-color: transparent;
            }
            QToolButton#CloseButton {
                background-color: transparent;
                border: none;
                color: #2b2b2b;
                font-size: 16px;
            }
            QToolButton#CloseButton:hover {
                background-color: #e81123;
                color: white;
            }
            QToolButton#CloseButton:pressed {
                background-color: #c50d1c;
            }
        """)

        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        label_style = "font-size: 11px; color: #2a2a2a; background: transparent; border: none;"

        name_row = QHBoxLayout()
        name_row.setSpacing(10)
        name_label = QLabel("Combination Name:")
        name_label.setStyleSheet(label_style)
        name_label.setFixedWidth(140)
        name_input = QLineEdit()
        name_input.setMinimumWidth(120)
        apply_field_style(name_input)
        name_row.addWidget(name_label)
        name_row.addWidget(name_input)
        name_row.addStretch()
        layout.addLayout(name_row)

        input_section = QFrame()
        input_section.setStyleSheet(
            "QFrame { border: 1px solid #c0c0c0; border-radius: 4px; background-color: #f8f8f8; padding: 8px; }"
        )
        input_section_layout = QVBoxLayout(input_section)
        input_section_layout.setContentsMargins(12, 12, 12, 12)
        input_section_layout.setSpacing(10)

        fields_row = QHBoxLayout()
        fields_row.setSpacing(12)

        load_case_label = QLabel("Load Case:")
        load_case_label.setStyleSheet(label_style)
        load_case_combo = QComboBox()
        load_case_combo.addItems(["DL", "SIDL", "LL", "WL", "EL", "IMF", "TL"])
        load_case_combo.setMinimumWidth(100)
        apply_field_style(load_case_combo)

        factor_label = QLabel("Partial Safety Factor:")
        factor_label.setStyleSheet(label_style)
        factor_input = QLineEdit()
        factor_input.setText("1.0")
        factor_input.setFixedWidth(100)
        apply_field_style(factor_input)

        fields_row.addWidget(load_case_label)
        fields_row.addWidget(load_case_combo)
        fields_row.addSpacing(20)
        fields_row.addWidget(factor_label)
        fields_row.addWidget(factor_input)
        fields_row.addStretch()

        input_section_layout.addLayout(fields_row)
        layout.addWidget(input_section)

        table_container = QFrame()
        table_container.setStyleSheet(
            "QFrame { border: 1px solid #c0c0c0; border-radius: 4px; background-color: #ffffff; }"
        )
        table_container_layout = QHBoxLayout(table_container)
        table_container_layout.setContentsMargins(10, 10, 10, 10)
        table_container_layout.setSpacing(10)

        table = QTableWidget(0, 3)
        table.setHorizontalHeaderLabels(["Sr.No", "Load Case", "Partial Safety Factor"])
        
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        table.setColumnWidth(0, 60)
        
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        
        table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #d0d0d0;
                gridline-color: #e0e0e0;
                selection-background-color: #d0e8ff;
            }
            QTableWidget::item {
                padding: 6px;
                color: #2a2a2a;
                font-size: 11px;
                border-bottom: 1px solid #e8e8e8;
            }
            QTableWidget::item:selected {
                background-color: #d0e8ff;
                color: #1a1a1a;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                color: #2a2a2a;
                font-size: 11px;
                font-weight: 600;
                padding: 8px;
                border: 1px solid #d0d0d0;
                border-bottom: 2px solid #a0a0a0;
            }
            QHeaderView::section:horizontal {
                border-top: none;
            }
        """)
        
        table.setMinimumHeight(250)
        table.setAlternatingRowColors(True)

        button_col = QVBoxLayout()
        button_col.setSpacing(8)
        add_btn = QPushButton("Add")
        modify_btn = QPushButton("Modify")
        delete_btn = QPushButton("Delete")
        
        for btn in (add_btn, modify_btn, delete_btn):
            btn.setFixedWidth(90)
            btn.setFixedHeight(32)
            btn.setStyleSheet(
                "QPushButton { "
                "   background: #ffffff; "
                "   border: 1px solid #a0a0a0; "
                "   border-radius: 4px; "
                "   padding: 6px 12px; "
                "   font-size: 11px; "
                "   font-weight: 500; "
                "   color: #2a2a2a; "
                "}"
                "QPushButton:hover { "
                "   background: #f0f0f0; "
                "   border: 1px solid #808080; "
                "}"
                "QPushButton:pressed { "
                "   background: #e0e0e0; "
                "}"
            )
            button_col.addWidget(btn)
        
        button_col.addStretch()

        table_container_layout.addWidget(table, 1)
        table_container_layout.addLayout(button_col)
        
        layout.addWidget(table_container)

        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, 8, 0, 0)
        action_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        save_btn = QPushButton("Save")
        
        for btn in (cancel_btn, save_btn):
            btn.setFixedWidth(100)
            btn.setFixedHeight(36)
            btn.setStyleSheet(
                "QPushButton { "
                "   background: #c8c8c8; "
                "   border: 1px solid #a0a0a0; "
                "   border-radius: 4px; "
                "   padding: 8px 16px; "
                "   font-weight: 600; "
                "   font-size: 11px; "
                "   color: #2a2a2a; "
                "}"
                "QPushButton:hover { "
                "   background: #d8d8d8; "
                "}"
                "QPushButton:pressed { "
                "   background: #b8b8b8; "
                "}"
            )
        
        action_row.addWidget(cancel_btn)
        action_row.addSpacing(8)
        action_row.addWidget(save_btn)
        layout.addLayout(action_row)

        def refresh_row_numbers():
            for row_idx in range(table.rowCount()):
                item = table.item(row_idx, 0)
                if item:
                    item.setText(str(row_idx + 1))
                else:
                    new_item = QTableWidgetItem(str(row_idx + 1))
                    new_item.setTextAlignment(Qt.AlignCenter)
                    new_item.setFlags(new_item.flags() & ~Qt.ItemIsEditable)
                    table.setItem(row_idx, 0, new_item)

        def add_row():
            case_text = load_case_combo.currentText().strip()
            factor_text = factor_input.text().strip() or "1.0"
            
            if not case_text:
                return
            
            row_idx = table.rowCount()
            table.insertRow(row_idx)
            
            s_no_item = QTableWidgetItem(str(row_idx + 1))
            s_no_item.setTextAlignment(Qt.AlignCenter)
            s_no_item.setFlags(s_no_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row_idx, 0, s_no_item)
            
            case_item = QTableWidgetItem(case_text)
            case_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            case_item.setFlags(case_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row_idx, 1, case_item)
            
            factor_item = QTableWidgetItem(factor_text)
            factor_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            factor_item.setFlags(factor_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row_idx, 2, factor_item)
            
            refresh_row_numbers()
            factor_input.setText("1.0")

        def modify_row():
            row_idx = table.currentRow()
            if row_idx < 0:
                return
            
            case_text = load_case_combo.currentText().strip()
            factor_text = factor_input.text().strip() or "1.0"
            
            case_item = QTableWidgetItem(case_text)
            case_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            case_item.setFlags(case_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row_idx, 1, case_item)
            
            factor_item = QTableWidgetItem(factor_text)
            factor_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            factor_item.setFlags(factor_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row_idx, 2, factor_item)

        def delete_row():
            row_idx = table.currentRow()
            if row_idx < 0:
                return
            table.removeRow(row_idx)
            refresh_row_numbers()

        def on_table_selection_changed():
            row_idx = table.currentRow()
            if row_idx >= 0:
                case_item = table.item(row_idx, 1)
                factor_item = table.item(row_idx, 2)
                
                if case_item:
                    load_case_combo.setCurrentText(case_item.text())
                if factor_item:
                    factor_input.setText(factor_item.text())

        def load_existing():
            if not existing:
                return
            
            name_input.setText(existing.get("name", ""))
            
            for item in existing.get("items", []):
                case_text = item.get("case", "")
                factor_text = item.get("factor", "1.0")
                
                if case_text:
                    load_case_combo.setCurrentText(case_text)
                    factor_input.setText(factor_text)
                    add_row()

        def on_save():
            name_text = name_input.text().strip() or "Load Combination"
            rows = []
            
            for row_idx in range(table.rowCount()):
                case_item = table.item(row_idx, 1)
                factor_item = table.item(row_idx, 2)
                
                if not case_item or not factor_item:
                    continue
                
                rows.append({
                    "case": case_item.text(),
                    "factor": factor_item.text()
                })
            
            if not rows:
                return
            
            dialog.accept()
            dialog.result_data = {"name": name_text, "items": rows}

        add_btn.clicked.connect(add_row)
        modify_btn.clicked.connect(modify_row)
        delete_btn.clicked.connect(delete_row)
        save_btn.clicked.connect(on_save)
        cancel_btn.clicked.connect(dialog.reject)
        table.itemSelectionChanged.connect(on_table_selection_changed)

        load_existing()

        if dialog.exec() == QDialog.Accepted:
            return getattr(dialog, "result_data", None)
        return None