from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QVBoxLayout,
    QWidget,
)

from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox, MessageBoxType
from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import CUSTOM_LOAD_TAB_SCHEMA


class CustomLoadTab(QWidget):

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.custom_load_items = getattr(owner, "custom_load_items", [])
        owner.custom_load_items = self.custom_load_items
        self.schema = CUSTOM_LOAD_TAB_SCHEMA
        self._build_ui()

    def _build_ui(self):
        owner = self.owner
        schema = self.schema

        self.setStyleSheet("background-color: #f0f0f0;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #f0f0f0; }")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: #f0f0f0;")
        
        page_layout = QVBoxLayout(scroll_content)
        page_layout.setContentsMargins(8, 8, 8, 8)
        page_layout.setSpacing(8)

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(12)

        label_style = "font-size: 11px; color: #2a2a2a; background: transparent; border: none;"
        heading_style = "font-size: 11px; font-weight: 700; color: #1a1a1a; background: transparent; border: none;"
        
        label_width = schema.get("label_width", 280)
        field_width = schema.get("field_width", 140)

        left_column = QVBoxLayout()
        left_column.setContentsMargins(0, 0, 0, 0)
        left_column.setSpacing(8)

        diagram = QFrame()
        diagram.setMinimumSize(QSize(380, 130))
        diagram.setMaximumHeight(130)
        diagram.setStyleSheet(
            "QFrame { border: 1px solid #a0a0a0; border-radius: 4px; background-color: #d0d0d0; }"
        )
        diagram_layout = QVBoxLayout(diagram)
        diagram_layout.setContentsMargins(8, 8, 8, 8)
        diagram_label = QLabel("Bridge Geometry\nDiagram")
        diagram_label.setAlignment(Qt.AlignCenter)
        diagram_label.setStyleSheet(
            "font-size: 11px; font-weight: 600; color: #2a2a2a; background: transparent; border: none;"
        )
        diagram_layout.addWidget(diagram_label, 1)
        left_column.addWidget(diagram)

        input_card = owner._create_card()
        input_card.setStyleSheet(
            "QFrame { border: 1px solid #a0a0a0; border-radius: 4px; background-color: #ffffff; }"
        )
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(10, 10, 10, 10)
        input_layout.setSpacing(8)

        title = QLabel("Custom Load Input Add/Edit:")
        title.setStyleSheet(heading_style)
        input_layout.addWidget(title)

        all_fields_layout = QVBoxLayout()
        all_fields_layout.setContentsMargins(0, 0, 0, 0)
        all_fields_layout.setSpacing(10)

        load_case_field = schema["fields"]["load_case"]
        load_case_row = QHBoxLayout()
        load_case_row.setSpacing(8)
        
        lbl = QLabel(load_case_field["label"])
        lbl.setStyleSheet(label_style)
        lbl.setFixedWidth(label_width)
        
        owner.custom_load_case_combo = QComboBox()
        owner.custom_load_case_combo.addItems(schema["load_case_choices"])
        owner.custom_load_case_combo.setFixedWidth(field_width)
        apply_field_style(owner.custom_load_case_combo)
        
        load_case_row.addWidget(lbl)
        load_case_row.addWidget(owner.custom_load_case_combo)
        
        custom_name_field = schema["fields"]["custom_load_case_name"]
        owner.custom_load_case_name_input = QLineEdit()
        owner.custom_load_case_name_input.setPlaceholderText(custom_name_field["placeholder"])
        owner.custom_load_case_name_input.setFixedWidth(field_width)
        owner.custom_load_case_name_input.setEnabled(custom_name_field["enabled"])
        apply_field_style(owner.custom_load_case_name_input)
        
        load_case_row.addWidget(owner.custom_load_case_name_input)
        load_case_row.addStretch()
        all_fields_layout.addLayout(load_case_row)

        load_type_field = schema["fields"]["load_type"]
        load_type_row = QHBoxLayout()
        load_type_row.setSpacing(8)
        
        lbl = QLabel(load_type_field["label"])
        lbl.setStyleSheet(label_style)
        lbl.setFixedWidth(label_width)
        
        owner.custom_load_type_combo = QComboBox()
        owner.custom_load_type_combo.addItems(schema["load_type_choices"])
        owner.custom_load_type_combo.setFixedWidth(field_width * 2 + 8)
        apply_field_style(owner.custom_load_type_combo)
        
        load_type_row.addWidget(lbl)
        load_type_row.addWidget(owner.custom_load_type_combo)
        load_type_row.addStretch()
        all_fields_layout.addLayout(load_type_row)

        input_layout.addLayout(all_fields_layout)

        self.custom_load_stack = QStackedWidget()
        self.custom_load_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.custom_load_stack.setStyleSheet(
            "QStackedWidget { border: none; background: transparent; }"
            "QWidget#customPointWidget, QWidget#customLineWidget { background: transparent; }"
        )

        point_widget = QWidget()
        point_widget.setObjectName("customPointWidget")
        point_layout = QVBoxLayout(point_widget)
        point_layout.setContentsMargins(0, 0, 0, 0)
        point_layout.setSpacing(10)

        point_left_field = schema["fields"]["point_left"]
        point_left_row = QHBoxLayout()
        point_left_row.setSpacing(8)
        
        lbl = QLabel(point_left_field["label"])
        lbl.setStyleSheet(label_style)
        lbl.setFixedWidth(label_width)
        
        owner.custom_point_left_input = QLineEdit()
        owner.custom_point_left_input.setFixedWidth(field_width * 2 + 8)
        apply_field_style(owner.custom_point_left_input)
        self._apply_validator(owner.custom_point_left_input, point_left_field.get("validator"))
        
        point_left_row.addWidget(lbl)
        point_left_row.addWidget(owner.custom_point_left_input)
        point_left_row.addStretch()
        point_layout.addLayout(point_left_row)

        point_bearing_field = schema["fields"]["point_bearing"]
        point_bearing_row = QHBoxLayout()
        point_bearing_row.setSpacing(8)
        
        lbl = QLabel(point_bearing_field["label"])
        lbl.setStyleSheet(label_style)
        lbl.setFixedWidth(label_width)
        
        owner.custom_point_bearing_input = QLineEdit()
        owner.custom_point_bearing_input.setFixedWidth(field_width * 2 + 8)
        apply_field_style(owner.custom_point_bearing_input)
        self._apply_validator(owner.custom_point_bearing_input, point_bearing_field.get("validator"))
        
        point_bearing_row.addWidget(lbl)
        point_bearing_row.addWidget(owner.custom_point_bearing_input)
        point_bearing_row.addStretch()
        point_layout.addLayout(point_bearing_row)

        self.custom_load_stack.addWidget(point_widget)

        line_widget = QWidget()
        line_widget.setObjectName("customLineWidget")
        line_layout = QVBoxLayout(line_widget)
        line_layout.setContentsMargins(0, 0, 0, 0)
        line_layout.setSpacing(10)

        line_left_start_field = schema["fields"]["line_left_start"]
        line_left_end_field = schema["fields"]["line_left_end"]
        
        left_edge_row = QHBoxLayout()
        left_edge_row.setSpacing(4)
        
        left_label = QLabel(line_left_start_field["label"])
        left_label.setStyleSheet(label_style)
        left_label.setFixedWidth(label_width)
        
        left_start_container = QVBoxLayout()
        left_start_container.setSpacing(4)
        left_start_lbl = QLabel(line_left_start_field["sub_label"])
        left_start_lbl.setStyleSheet("font-size: 9px; color: #505050;")
        left_start_lbl.setAlignment(Qt.AlignCenter)
        owner.custom_line_left_start = QLineEdit()
        owner.custom_line_left_start.setFixedWidth(field_width + 2)
        apply_field_style(owner.custom_line_left_start)
        self._apply_validator(owner.custom_line_left_start, line_left_start_field.get("validator"))
        left_start_container.addWidget(left_start_lbl)
        left_start_container.addWidget(owner.custom_line_left_start)
        
        left_end_container = QVBoxLayout()
        left_end_container.setSpacing(4)
        left_end_lbl = QLabel(line_left_end_field["sub_label"])
        left_end_lbl.setStyleSheet("font-size: 9px; color: #505050;")
        left_end_lbl.setAlignment(Qt.AlignCenter)
        owner.custom_line_left_end = QLineEdit()
        owner.custom_line_left_end.setFixedWidth(field_width + 2)
        apply_field_style(owner.custom_line_left_end)
        self._apply_validator(owner.custom_line_left_end, line_left_end_field.get("validator"))
        left_end_container.addWidget(left_end_lbl)
        left_end_container.addWidget(owner.custom_line_left_end)
        
        left_edge_row.addWidget(left_label)
        left_edge_row.addLayout(left_start_container)
        left_edge_row.addLayout(left_end_container)
        left_edge_row.addStretch()
        line_layout.addLayout(left_edge_row)

        line_bearing_start_field = schema["fields"]["line_bearing_start"]
        line_bearing_end_field = schema["fields"]["line_bearing_end"]
        
        bearing_row = QHBoxLayout()
        bearing_row.setSpacing(4)
        
        bearing_label = QLabel(line_bearing_start_field["label"])
        bearing_label.setStyleSheet(label_style)
        bearing_label.setFixedWidth(label_width)
        
        bearing_start_container = QVBoxLayout()
        bearing_start_container.setSpacing(4)
        bearing_start_lbl = QLabel(line_bearing_start_field["sub_label"])
        bearing_start_lbl.setStyleSheet("font-size: 9px; color: #505050;")
        bearing_start_lbl.setAlignment(Qt.AlignCenter)
        owner.custom_line_bearing_start = QLineEdit()
        owner.custom_line_bearing_start.setFixedWidth(field_width + 2)
        apply_field_style(owner.custom_line_bearing_start)
        self._apply_validator(owner.custom_line_bearing_start, line_bearing_start_field.get("validator"))
        bearing_start_container.addWidget(bearing_start_lbl)
        bearing_start_container.addWidget(owner.custom_line_bearing_start)
        
        bearing_end_container = QVBoxLayout()
        bearing_end_container.setSpacing(4)
        bearing_end_lbl = QLabel(line_bearing_end_field["sub_label"])
        bearing_end_lbl.setStyleSheet("font-size: 9px; color: #505050;")
        bearing_end_lbl.setAlignment(Qt.AlignCenter)
        owner.custom_line_bearing_end = QLineEdit()
        owner.custom_line_bearing_end.setFixedWidth(field_width + 2)
        apply_field_style(owner.custom_line_bearing_end)
        self._apply_validator(owner.custom_line_bearing_end, line_bearing_end_field.get("validator"))
        bearing_end_container.addWidget(bearing_end_lbl)
        bearing_end_container.addWidget(owner.custom_line_bearing_end)
        
        bearing_row.addWidget(bearing_label)
        bearing_row.addLayout(bearing_start_container)
        bearing_row.addLayout(bearing_end_container)
        bearing_row.addStretch()
        line_layout.addLayout(bearing_row)

        self.custom_load_stack.addWidget(line_widget)

        input_layout.addWidget(self.custom_load_stack)

        save_btn = QPushButton("Save")
        save_btn.setMinimumWidth(120) 
        save_btn.setFixedHeight(28)
        save_btn.setStyleSheet(
            "QPushButton { "
            "   background: #ffffff; "
            "   border: 1px solid #a0a0a0; "
            "   border-radius: 3px; "
            "   padding: 3px 8px; "
            "   font-size: 11px; "
            "   color: #2a2a2a; "
            "} "
            "QPushButton:hover { background: #f0f0f0; } "
            "QPushButton:pressed { background: #e0e0e0; }"
        )


        save_row = QHBoxLayout()
        save_row.setContentsMargins(0, 12, 0, 0)

        save_row.addStretch()         
        save_row.addWidget(save_btn) 
        save_row.addStretch()          

        input_layout.addLayout(save_row)


        left_column.addWidget(input_card)

        list_card = owner._create_card()
        list_card.setStyleSheet(
            "QFrame { border: 1px solid #a0a0a0; border-radius: 4px; background-color: #ffffff; }"
        )
        list_card.setMinimumHeight(250)
        list_layout = QVBoxLayout(list_card)
        list_layout.setContentsMargins(4, 10, 10, 10)
        list_layout.setSpacing(8)

        list_title = QLabel("Custom Load Name")
        list_title.setStyleSheet(heading_style)
        list_layout.addWidget(list_title)

        controls_row = QHBoxLayout()
        controls_row.setSpacing(6)
        owner.custom_edit_btn = QPushButton("Edit")
        owner.custom_delete_btn = QPushButton("Delete")
        for btn in (owner.custom_edit_btn, owner.custom_delete_btn):
            btn.setFixedWidth(55)
            btn.setStyleSheet(
                "QPushButton { background: #ffffff; border: 1px solid #a0a0a0; border-radius: 3px; padding: 3px 8px; font-size: 11px; color: #2a2a2a; }"
                "QPushButton:hover { background: #f0f0f0; }"
                "QPushButton:pressed { background: #e0e0e0; }"
            )
            controls_row.addWidget(btn)
        controls_row.addStretch()
        list_layout.addLayout(controls_row)
        # ---- Table wrapper to ensure visible borders ----
        table_frame = QFrame()
        table_frame.setStyleSheet(
            """
            QFrame {
                border: none;
                background: #ffffff;
            }
            """
        )

        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)
        
        self.custom_load_table = QTableWidget(0, 4)
    
        self.custom_load_table.setFrameStyle(QFrame.NoFrame)
        self.custom_load_table.setContentsMargins(0, 0, 0, 0)
        self.custom_load_table.viewport().setContentsMargins(0, 0, 0, 0)
        self.custom_load_table.setShowGrid(True)

        self.custom_load_table.setHorizontalHeaderLabels([
            "Load Case",
            "Load Type", 
            "Distance from Left (m)",
            "Distance from Bearing (m)"
        ])
        
        self.custom_load_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.custom_load_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.custom_load_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.custom_load_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.custom_load_table.verticalHeader().setVisible(False)
        self.custom_load_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.custom_load_table.setSelectionMode(QTableWidget.SingleSelection)
        self.custom_load_table.setCornerButtonEnabled(False)
        self.custom_load_table.setStyleSheet(
            """
            QTableWidget {
                background: #ffffff;
                border: 1px solid #a0a0a0;
                gridline-color: #d0d0d0;
            }

            QTableWidget::viewport {
                border: none;
                background: #ffffff;
            }

            QTableWidget::item {
                padding: 4px;
                font-size: 10px;
                color: #3a3a3a;
                border-bottom: 1px solid #c0c0c0;
            }

            QTableWidget::item:selected {
                background: #d0e8ff;
            }

            QHeaderView::section {
                color: #2a2a2a;
                background: #f0f0f0;
                font-size: 10px;
                font-weight: 600;
                padding: 5px;
                border: none;
                border-right: 1px solid #d0d0d0;
                border-bottom: 1px solid #d0d0d0;
            }
            """
        )

        self.custom_load_table.setMinimumHeight(180)

        table_layout.addWidget(self.custom_load_table)
        list_layout.addWidget(table_frame)

        left_column.addWidget(list_card)

        right_card = owner._create_card()
        right_card.setStyleSheet(
            "QFrame { border: 1px solid #a0a0a0; border-radius: 4px; background-color: #d8d8d8; }"
        )
        right_card.setMinimumWidth(260)
        right_card.setMinimumHeight(480)
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(8)

        desc_title = QLabel("Description Box")
        desc_title.setAlignment(Qt.AlignCenter)
        desc_title.setStyleSheet(
            "font-size: 11px; font-weight: 700; color: #1a1a1a; background: transparent; border: none;"
        )
        right_layout.addWidget(desc_title)
        right_layout.addStretch()

        content_row.addLayout(left_column, 3)
        content_row.addWidget(right_card, 2)
        page_layout.addLayout(content_row)

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        owner.custom_load_type_combo.currentTextChanged.connect(self._on_custom_load_type_changed)
        self._on_custom_load_type_changed(owner.custom_load_type_combo.currentText())

        save_btn.clicked.connect(self._on_save_custom_load)
        owner.custom_delete_btn.clicked.connect(self._on_delete_custom_load)
        owner.custom_edit_btn.clicked.connect(self._on_edit_custom_load)
        owner.custom_load_case_combo.currentTextChanged.connect(
            lambda t: self._on_load_case_changed(t)
        )

        self._refresh_custom_load_table()

    def _apply_validator(self, widget, validator_config):
        if not validator_config:
            return
        
        if validator_config["type"] == "double_range":
            validator = QDoubleValidator(
                validator_config["bottom"],
                validator_config["top"],
                validator_config.get("decimals", 2),
                widget
            )
            validator.setNotation(QDoubleValidator.StandardNotation)
            widget.setValidator(validator)

    def _on_custom_load_type_changed(self, text):
        if text == "Point":
            self.custom_load_stack.setCurrentIndex(0)
        else: 
            self.custom_load_stack.setCurrentIndex(1)

    def _on_load_case_changed(self, text):
        is_custom = (text == "Custom")
        self.owner.custom_load_case_name_input.setEnabled(is_custom)
        if not is_custom:
            self.owner.custom_load_case_name_input.clear()

    def _refresh_custom_load_table(self):
        self.custom_load_table.setRowCount(0)
        
        for row_idx, load_data in enumerate(self.custom_load_items):
            self.custom_load_table.insertRow(row_idx)
            
            load_case = load_data.get("load_case", "")
            if load_case == "Custom":
                load_case_display = load_data.get("custom_load_case_name", "custom")
            else:
                load_case_display = load_case
            
            item = QTableWidgetItem(load_case_display)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.custom_load_table.setItem(row_idx, 0, item)
            
            load_type = load_data.get("load_type", "")
            item = QTableWidgetItem(load_type)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.custom_load_table.setItem(row_idx, 1, item)
            
            if load_type == "Point":
                dist_left = load_data.get("point_left", "")
            else:
                start = load_data.get("line_left_start", "")
                end = load_data.get("line_left_end", "")
                dist_left = f"{start} - {end}"
            
            item = QTableWidgetItem(dist_left)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.custom_load_table.setItem(row_idx, 2, item)
            
            if load_type == "Point":
                dist_bearing = load_data.get("point_bearing", "")
            else:
                start = load_data.get("line_bearing_start", "")
                end = load_data.get("line_bearing_end", "")
                dist_bearing = f"{start} - {end}"
            
            item = QTableWidgetItem(dist_bearing)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.custom_load_table.setItem(row_idx, 3, item)

    def _on_save_custom_load(self):
        owner = self.owner
        
        load_data = {
            "load_case": owner.custom_load_case_combo.currentText(),
            "load_type": owner.custom_load_type_combo.currentText(),
        }
        
        if owner.custom_load_case_combo.currentText() == "Custom":
            custom_name = owner.custom_load_case_name_input.text().strip()
            if not custom_name:
                CustomMessageBox(title="Invalid Input", text="Please provide a name for the Custom load case.", buttons=["OK"], dialogType=MessageBoxType.Warning).exec()
                return
            load_data["custom_load_case_name"] = custom_name
        
        if owner.custom_load_type_combo.currentText() == "Point":
            point_l = owner.custom_point_left_input.text().strip()
            point_b = owner.custom_point_bearing_input.text().strip()
            if not point_l or not point_b:
                CustomMessageBox(title="Invalid Input", text="Please fill in all distance fields for the Point load.", buttons=["OK"], dialogType=MessageBoxType.Warning).exec()
                return
            load_data["point_left"] = point_l
            load_data["point_bearing"] = point_b
        else:
            line_l_start = owner.custom_line_left_start.text().strip()
            line_l_end = owner.custom_line_left_end.text().strip()
            line_b_start = owner.custom_line_bearing_start.text().strip()
            line_b_end = owner.custom_line_bearing_end.text().strip()
            
            if not line_l_start or not line_l_end or not line_b_start or not line_b_end:
                CustomMessageBox(title="Invalid Input", text="Please fill in all distance fields for the Line/Area load.", buttons=["OK"], dialogType=MessageBoxType.Warning).exec()
                return
            
            try:
                if float(line_l_start) > float(line_l_end):
                    CustomMessageBox(title="Invalid Input", text="Distance from Left Edge Start cannot be greater than End.", buttons=["OK"], dialogType=MessageBoxType.Warning).exec()
                    return
                if float(line_b_start) > float(line_b_end):
                    CustomMessageBox(title="Invalid Input", text="Distance from Bearing Start cannot be greater than End.", buttons=["OK"], dialogType=MessageBoxType.Warning).exec()
                    return
            except ValueError:
                CustomMessageBox(title="Invalid Input", text="Distance fields must be numeric.", buttons=["OK"], dialogType=MessageBoxType.Warning).exec()
                return

            load_data["line_left_start"] = line_l_start
            load_data["line_left_end"] = line_l_end
            load_data["line_bearing_start"] = line_b_start
            load_data["line_bearing_end"] = line_b_end
        
        if hasattr(self, '_editing_load_data') and self._editing_load_data:
            for i, item in enumerate(self.custom_load_items):
                if item == self._editing_load_data:
                    self.custom_load_items[i] = load_data
                    break
            self._editing_load_data = None
        else:
            self.custom_load_items.append(load_data)
        
        self._clear_inputs()
        self._refresh_custom_load_table()
        
        CustomMessageBox(title="Saved", text="Custom load has been saved.", buttons=["OK"], dialogType=MessageBoxType.Success).exec()

    def _on_edit_custom_load(self):
        selected_rows = self.custom_load_table.selectionModel().selectedRows()
        
        if len(selected_rows) == 0:
            CustomMessageBox(title="Edit", text="Please select one custom load to edit.", buttons=["OK"], dialogType=MessageBoxType.Information).exec()
            return
        
        if len(selected_rows) > 1:
            CustomMessageBox(title="Edit", text="Please select only one custom load to edit.", buttons=["OK"], dialogType=MessageBoxType.Information).exec()
            return
        
        row_idx = selected_rows[0].row()
        load_data = self.custom_load_items[row_idx]
        self._editing_load_data = load_data
        
        owner = self.owner
        
        load_case = load_data.get("load_case", "DL")
        index = owner.custom_load_case_combo.findText(load_case)
        if index >= 0:
            owner.custom_load_case_combo.setCurrentIndex(index)
        
        if load_case == "Custom":
            owner.custom_load_case_name_input.setText(load_data.get("custom_load_case_name", ""))
        
        load_type = load_data.get("load_type", "Point")
        index = owner.custom_load_type_combo.findText(load_type)
        if index >= 0:
            owner.custom_load_type_combo.setCurrentIndex(index)
        
        if load_type == "Point":
            owner.custom_point_left_input.setText(load_data.get("point_left", ""))
            owner.custom_point_bearing_input.setText(load_data.get("point_bearing", ""))
        else:
            owner.custom_line_left_start.setText(load_data.get("line_left_start", ""))
            owner.custom_line_left_end.setText(load_data.get("line_left_end", ""))
            owner.custom_line_bearing_start.setText(load_data.get("line_bearing_start", ""))
            owner.custom_line_bearing_end.setText(load_data.get("line_bearing_end", ""))

    def _on_delete_custom_load(self):
        selected_rows = self.custom_load_table.selectionModel().selectedRows()
        
        if len(selected_rows) == 0:
            CustomMessageBox(title="Delete", text="Please select at least one custom load to delete.", buttons=["OK"], dialogType=MessageBoxType.Information).exec()
            return
        
        rows_to_delete = sorted([row.row() for row in selected_rows], reverse=True)
        
        for row_idx in rows_to_delete:
            if 0 <= row_idx < len(self.custom_load_items):
                del self.custom_load_items[row_idx]
        
        self._refresh_custom_load_table()
        
        CustomMessageBox(title="Deleted", text=f"{len(rows_to_delete)} custom load(s) deleted.", buttons=["OK"], dialogType=MessageBoxType.Information).exec()

    def _clear_inputs(self):
        owner = self.owner
        owner.custom_load_case_combo.setCurrentIndex(0)
        owner.custom_load_case_name_input.clear()
        owner.custom_load_type_combo.setCurrentIndex(0)
        owner.custom_point_left_input.clear()
        owner.custom_point_bearing_input.clear()
        owner.custom_line_left_start.clear()
        owner.custom_line_left_end.clear()
        owner.custom_line_bearing_start.clear()
        owner.custom_line_bearing_end.clear()

    def reset_defaults(self):
        self._clear_inputs()
        self.owner.custom_load_case_name_input.setEnabled(False)
        self.custom_load_items.clear()
        self._refresh_custom_load_table()
        if hasattr(self, '_editing_load_data'):
            self._editing_load_data = None