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
from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import (
    LOAD_COMBINATION_TAB_SCHEMA,
)

class LoadCombinationTab(QWidget):
    """Load combination editor with add/edit modal."""

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

        # Build auto-include checkbox from schema
        auto_row = self._build_auto_include_row(label_style)
        left_layout.addLayout(auto_row)

        # Build control buttons from schema
        controls_row = self._build_controls_row()
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
        owner.load_combo_default_btn.clicked.connect(self._on_reset_to_default)

        self._refresh_load_combo_list()

    def _build_auto_include_row(self, label_style):
        """Build the auto-include checkbox row from schema."""
        schema = LOAD_COMBINATION_TAB_SCHEMA
        auto_row = QHBoxLayout()
        auto_row.setSpacing(8)
        auto_row.setContentsMargins(0, 0, 0, 0)
        
        # Get field config from schema
        field_config = schema["rows"][0]["fields"][0]
        
        auto_label = QLabel(field_config["label"])
        auto_label.setStyleSheet(label_style)
        
        # Create checkbox and bind to owner
        checkbox = QCheckBox()
        setattr(self.owner, field_config["bind"], checkbox)
        
        auto_row.addWidget(auto_label)
        auto_row.addWidget(checkbox)
        auto_row.addStretch()
        
        return auto_row

    def _build_controls_row(self):
        """Build control buttons row from schema."""
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
            btn = QPushButton(btn_config["label"])
            btn.setFixedWidth(btn_config["width"])
            btn.setStyleSheet(button_style)
            
            # Bind to owner
            setattr(self.owner, btn_config["bind"], btn)
            controls_row.addWidget(btn)
        
        controls_row.addStretch()
        return controls_row

    def _on_reset_to_default(self):
        """Reset load combinations to default values."""
        self.load_combo_items = self._get_default_combos()
        self.owner.load_combo_items = self.load_combo_items
        
        # Reset the auto-include checkbox if it exists
        if hasattr(self.owner, 'auto_include_checkbox'):
            self.owner.auto_include_checkbox.setChecked(False)
        
        self._refresh_load_combo_list()

    def _get_default_combos(self):
        """Return default load combinations (placeholder implementation)."""
        return []

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
        """
        Opens the Add/Edit Load Combination dialog.
        Enhanced with better table visibility and styling.
        """
        dialog = QDialog(self)
        dialog.setModal(True)
        dialog.setWindowTitle("Edit Load Combination" if existing else "Add Load Combination")
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(500)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        label_style = "font-size: 11px; color: #2a2a2a; background: transparent; border: none;"

        # Combination Name
        name_row = QHBoxLayout()
        name_row.setSpacing(10)
        name_label = QLabel("Combination Name:")
        name_label.setStyleSheet(label_style)
        name_label.setFixedWidth(140)
        name_input = QLineEdit()
        name_input.setMinimumWidth(300)
        apply_field_style(name_input)
        name_row.addWidget(name_label)
        name_row.addWidget(name_input, 1)
        layout.addLayout(name_row)

        # Input fields section
        input_section = QFrame()
        input_section.setStyleSheet(
            "QFrame { border: 1px solid #c0c0c0; border-radius: 4px; background-color: #f8f8f8; padding: 8px; }"
        )
        input_section_layout = QVBoxLayout(input_section)
        input_section_layout.setContentsMargins(12, 12, 12, 12)
        input_section_layout.setSpacing(10)

        fields_row = QHBoxLayout()
        fields_row.setSpacing(12)

        # Load Case
        load_case_label = QLabel("Load Case:")
        load_case_label.setStyleSheet(label_style)
        load_case_combo = QComboBox()
        load_case_combo.addItems(["DL", "SIDL", "LL", "WL", "EL", "IMF", "TL"])
        load_case_combo.setMinimumWidth(100)
        apply_field_style(load_case_combo)

        # Partial Safety Factor
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

        # Table section
        table_container = QFrame()
        table_container.setStyleSheet(
            "QFrame { border: 1px solid #c0c0c0; border-radius: 4px; background-color: #ffffff; }"
        )
        table_container_layout = QHBoxLayout(table_container)
        table_container_layout.setContentsMargins(10, 10, 10, 10)
        table_container_layout.setSpacing(10)

        # Enhanced Table Widget
        table = QTableWidget(0, 3)
        table.setHorizontalHeaderLabels(["S.No", "Load Case", "Partial Safety Factor"])
        
        # Set column widths for better visibility
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        table.setColumnWidth(0, 60)
        
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        
        # Enhanced table styling for better visibility
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

        # Button column
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

        # Action buttons
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
            """Update S.No column for all rows."""
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
            """Add a new row to the table."""
            case_text = load_case_combo.currentText().strip()
            factor_text = factor_input.text().strip() or "1.0"
            
            if not case_text:
                return
            
            row_idx = table.rowCount()
            table.insertRow(row_idx)
            
            # S.No
            s_no_item = QTableWidgetItem(str(row_idx + 1))
            s_no_item.setTextAlignment(Qt.AlignCenter)
            s_no_item.setFlags(s_no_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row_idx, 0, s_no_item)
            
            # Load Case
            case_item = QTableWidgetItem(case_text)
            case_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            case_item.setFlags(case_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row_idx, 1, case_item)
            
            # Partial Safety Factor
            factor_item = QTableWidgetItem(factor_text)
            factor_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            factor_item.setFlags(factor_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row_idx, 2, factor_item)
            
            refresh_row_numbers()
            
            # Clear input fields after adding
            factor_input.setText("1.0")

        def modify_row():
            """Modify the selected row."""
            row_idx = table.currentRow()
            if row_idx < 0:
                return
            
            case_text = load_case_combo.currentText().strip()
            factor_text = factor_input.text().strip() or "1.0"
            
            # Update Load Case
            case_item = QTableWidgetItem(case_text)
            case_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            case_item.setFlags(case_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row_idx, 1, case_item)
            
            # Update Partial Safety Factor
            factor_item = QTableWidgetItem(factor_text)
            factor_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            factor_item.setFlags(factor_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row_idx, 2, factor_item)

        def delete_row():
            """Delete the selected row."""
            row_idx = table.currentRow()
            if row_idx < 0:
                return
            table.removeRow(row_idx)
            refresh_row_numbers()

        def on_table_selection_changed():
            """Load selected row data into input fields."""
            row_idx = table.currentRow()
            if row_idx >= 0:
                case_item = table.item(row_idx, 1)
                factor_item = table.item(row_idx, 2)
                
                if case_item:
                    load_case_combo.setCurrentText(case_item.text())
                if factor_item:
                    factor_input.setText(factor_item.text())

        def load_existing():
            """Load existing data into the dialog."""
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
            """Save the load combination."""
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

        # Connect signals
        add_btn.clicked.connect(add_row)
        modify_btn.clicked.connect(modify_row)
        delete_btn.clicked.connect(delete_row)
        save_btn.clicked.connect(on_save)
        cancel_btn.clicked.connect(dialog.reject)
        table.itemSelectionChanged.connect(on_table_selection_changed)

        # Load existing data if editing
        load_existing()

        if dialog.exec() == QDialog.Accepted:
            return getattr(dialog, "result_data", None)
        return None