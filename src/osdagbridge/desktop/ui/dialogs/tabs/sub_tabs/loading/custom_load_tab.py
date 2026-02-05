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
    QMessageBox,
    QPushButton,

    QScrollArea,
    QStackedWidget,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,

    QStackedWidget,
    QSizePolicy,

    QVBoxLayout,
    QWidget,
)

from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style

from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import CUSTOM_LOAD_TAB_SCHEMA


class CustomLoadTab(QWidget):



class CustomLoadTab(QWidget):
    """Custom load input editor."""


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


        self.setStyleSheet("background-color: #f0f0f0;")
        page_layout = QVBoxLayout(self)

        page_layout.setContentsMargins(8, 8, 8, 8)
        page_layout.setSpacing(8)

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(12)

        label_style = "font-size: 11px; color: #2a2a2a; background: transparent; border: none;"
        heading_style = "font-size: 11px; font-weight: 700; color: #1a1a1a; background: transparent; border: none;"

        
        label_width = schema.get("label_width", 260)
        field_width = schema.get("field_width", 140)

        field_width = 105


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
        owner.custom_load_type_combo.setFixedWidth(field_width)
        apply_field_style(owner.custom_load_type_combo)
        
        load_type_row.addWidget(lbl)
        load_type_row.addWidget(owner.custom_load_type_combo)
        load_type_row.addStretch()
        all_fields_layout.addLayout(load_type_row)

        input_layout.addLayout(all_fields_layout)

        self.custom_load_stack = QStackedWidget()
        self.custom_load_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        form_grid = QGridLayout()
        form_grid.setContentsMargins(0, 0, 0, 0)
        form_grid.setHorizontalSpacing(8)
        form_grid.setVerticalSpacing(8)
        form_grid.setColumnMinimumWidth(0, 120)
        form_grid.setColumnStretch(0, 0)
        form_grid.setColumnStretch(1, 0)
        form_grid.setColumnStretch(2, 0)

        lbl = QLabel("Load Case:")
        lbl.setStyleSheet(label_style)
        owner.custom_load_case_combo = QComboBox()
        owner.custom_load_case_combo.addItems(["", "LL", "DL", "Custom"])
        owner.custom_load_case_combo.setFixedWidth(field_width)
        apply_field_style(owner.custom_load_case_combo)
        form_grid.addWidget(lbl, 0, 0, Qt.AlignLeft | Qt.AlignVCenter)
        form_grid.addWidget(owner.custom_load_case_combo, 0, 1, Qt.AlignLeft)

        owner.custom_load_case_button = QPushButton("Custom")
        owner.custom_load_case_button.setFixedWidth(field_width)
        owner.custom_load_case_button.setStyleSheet(
            "QPushButton { background: #e8e8e8; border: 1px solid #a0a0a0; border-radius: 3px; padding: 3px 8px; font-size: 11px; color: #2a2a2a; }"
            "QPushButton:hover { background: #f0f0f0; }"
            "QPushButton:pressed { background: #d8d8d8; }"
        )
        form_grid.addWidget(owner.custom_load_case_button, 0, 2, Qt.AlignLeft)

        lbl = QLabel("Load Type:")
        lbl.setStyleSheet(label_style)
        owner.custom_load_type_combo = QComboBox()
        owner.custom_load_type_combo.addItems(["Point", "Line/Area"])
        owner.custom_load_type_combo.setFixedWidth(field_width)
        apply_field_style(owner.custom_load_type_combo)
        form_grid.addWidget(lbl, 1, 0, Qt.AlignLeft | Qt.AlignVCenter)
        form_grid.addWidget(owner.custom_load_type_combo, 1, 1, Qt.AlignLeft)

        self.custom_load_stack = QStackedWidget()
        self.custom_load_stack.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.custom_load_stack.setFixedWidth(360)

        self.custom_load_stack.setStyleSheet(
            "QStackedWidget { border: none; background: transparent; }"
            "QWidget#customPointWidget, QWidget#customLineWidget { background: transparent; }"
        )

        point_widget = QWidget()
        point_widget.setObjectName("customPointWidget")

        point_layout = QVBoxLayout(point_widget)
        point_layout.setContentsMargins(0, 8, 0, 0)
        point_layout.setSpacing(10)

        point_left_field = schema["fields"]["point_left"]
        point_left_row = QHBoxLayout()
        point_left_row.setSpacing(8)
        
        lbl = QLabel(point_left_field["label"])
        lbl.setStyleSheet(label_style)
        lbl.setFixedWidth(label_width)
        
        owner.custom_point_left_input = QLineEdit()
        owner.custom_point_left_input.setFixedWidth(field_width)
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
        owner.custom_point_bearing_input.setFixedWidth(field_width)
        apply_field_style(owner.custom_point_bearing_input)
        self._apply_validator(owner.custom_point_bearing_input, point_bearing_field.get("validator"))
        
        point_bearing_row.addWidget(lbl)
        point_bearing_row.addWidget(owner.custom_point_bearing_input)
        point_bearing_row.addStretch()
        point_layout.addLayout(point_bearing_row)

        point_grid = QGridLayout(point_widget)
        point_grid.setContentsMargins(0, 0, 0, 0)
        point_grid.setHorizontalSpacing(8)
        point_grid.setVerticalSpacing(8)
        point_grid.setColumnMinimumWidth(0, 240)
        point_grid.setColumnStretch(0, 0)
        point_grid.setColumnStretch(1, 0)

        lbl = QLabel("Distance from Left Edge of Bridge Cross\nSection (m):")
        lbl.setStyleSheet(label_style)
        owner.custom_point_left_input = QLineEdit()
        owner.custom_point_left_input.setFixedWidth(105)
        apply_field_style(owner.custom_point_left_input)
        point_grid.addWidget(lbl, 0, 0, Qt.AlignLeft | Qt.AlignVCenter)
        point_grid.addWidget(owner.custom_point_left_input, 0, 1, Qt.AlignLeft)

        lbl = QLabel("Distance from Center Line of Bearing\n(m):")
        lbl.setStyleSheet(label_style)
        owner.custom_point_bearing_input = QLineEdit()
        owner.custom_point_bearing_input.setFixedWidth(105)
        apply_field_style(owner.custom_point_bearing_input)
        point_grid.addWidget(lbl, 1, 0, Qt.AlignLeft | Qt.AlignVCenter)
        point_grid.addWidget(owner.custom_point_bearing_input, 1, 1, Qt.AlignLeft)


        self.custom_load_stack.addWidget(point_widget)

        line_widget = QWidget()
        line_widget.setObjectName("customLineWidget")

        line_layout = QVBoxLayout(line_widget)
        line_layout.setContentsMargins(0, 8, 0, 0)
        line_layout.setSpacing(10)

        line_left_start_field = schema["fields"]["line_left_start"]
        line_left_end_field = schema["fields"]["line_left_end"]
        
        left_edge_row = QHBoxLayout()
        left_edge_row.setSpacing(8)
        
        left_label = QLabel(line_left_start_field["label"])
        left_label.setStyleSheet(label_style)
        left_label.setFixedWidth(label_width)
        
        left_start_container = QVBoxLayout()
        left_start_container.setSpacing(4)
        left_start_lbl = QLabel(line_left_start_field["sub_label"])
        left_start_lbl.setStyleSheet("font-size: 9px; color: #505050;")
        left_start_lbl.setAlignment(Qt.AlignCenter)
        owner.custom_line_left_start = QLineEdit()
        owner.custom_line_left_start.setFixedWidth(line_left_start_field["field_width"])
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
        owner.custom_line_left_end.setFixedWidth(line_left_end_field["field_width"])
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
        bearing_row.setSpacing(8)
        
        bearing_label = QLabel(line_bearing_start_field["label"])
        bearing_label.setStyleSheet(label_style)
        bearing_label.setFixedWidth(label_width)
        
        bearing_start_container = QVBoxLayout()
        bearing_start_container.setSpacing(4)
        bearing_start_lbl = QLabel(line_bearing_start_field["sub_label"])
        bearing_start_lbl.setStyleSheet("font-size: 9px; color: #505050;")
        bearing_start_lbl.setAlignment(Qt.AlignCenter)
        owner.custom_line_bearing_start = QLineEdit()
        owner.custom_line_bearing_start.setFixedWidth(line_bearing_start_field["field_width"])
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
        owner.custom_line_bearing_end.setFixedWidth(line_bearing_end_field["field_width"])
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


        line_grid = QGridLayout(line_widget)
        line_grid.setContentsMargins(0, 0, 0, 0)
        line_grid.setHorizontalSpacing(8)
        line_grid.setVerticalSpacing(4)
        line_grid.setColumnMinimumWidth(0, 240)

        def _start_end_row(label_text, start_attr, end_attr, row_idx):
            row_label = QLabel(label_text)
            row_label.setStyleSheet(label_style)
            start_field = QLineEdit()
            end_field = QLineEdit()
            start_field.setFixedWidth(52)
            end_field.setFixedWidth(52)
            apply_field_style(start_field)
            apply_field_style(end_field)

            line_grid.addWidget(row_label, row_idx * 2, 0, Qt.AlignLeft | Qt.AlignVCenter)
            line_grid.addWidget(start_field, row_idx * 2, 1, Qt.AlignLeft)
            line_grid.addWidget(end_field, row_idx * 2, 2, Qt.AlignLeft)

            start_lbl = QLabel("Start")
            start_lbl.setStyleSheet("font-size: 9px; color: #505050;")
            end_lbl = QLabel("End")
            end_lbl.setStyleSheet("font-size: 9px; color: #505050;")
            line_grid.addWidget(start_lbl, row_idx * 2 + 1, 1, Qt.AlignHCenter | Qt.AlignTop)
            line_grid.addWidget(end_lbl, row_idx * 2 + 1, 2, Qt.AlignHCenter | Qt.AlignTop)

            setattr(owner, start_attr, start_field)
            setattr(owner, end_attr, end_field)

        _start_end_row(
            "Distance from Left Edge of Bridge Cross\nSection (m):",
            "custom_line_left_start",
            "custom_line_left_end",
            0,
        )
        _start_end_row(
            "Distance from Center Line of Bearing\n(m):",
            "custom_line_bearing_start",
            "custom_line_bearing_end",
            1,
        )

        self.custom_load_stack.addWidget(line_widget)

        form_grid.addWidget(self.custom_load_stack, 2, 0, 1, 3)

        input_layout.addLayout(form_grid)

        save_btn = QPushButton("Save")
        save_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        save_btn.setStyleSheet(
            "QPushButton { background: #c8c8c8; border: 1px solid #a0a0a0; border-radius: 3px; padding: 5px 16px; font-weight: 600; font-size: 11px; color: #2a2a2a; }"
            "QPushButton:hover { background: #d8d8d8; }"
            "QPushButton:pressed { background: #b8b8b8; }"
        )
        save_row = QHBoxLayout()
        save_row.setContentsMargins(0, 4, 0, 0)
        save_row.addWidget(save_btn)
        input_layout.addLayout(save_row)


        left_column.addWidget(input_card)

        list_card = owner._create_card()
        list_card.setStyleSheet(
            "QFrame { border: 1px solid #a0a0a0; border-radius: 4px; background-color: #ffffff; }"
        )

        list_card.setMinimumHeight(250)

        list_card.setMinimumHeight(120)

        list_layout = QVBoxLayout(list_card)
        list_layout.setContentsMargins(10, 10, 10, 10)
        list_layout.setSpacing(8)

        list_title = QLabel("Custom Load Name")
        list_title.setStyleSheet(heading_style)
        list_layout.addWidget(list_title)

        controls_row = QHBoxLayout()
        controls_row.setSpacing(6)

        owner.custom_edit_btn = QPushButton("Edit")
        owner.custom_delete_btn = QPushButton("Delete")
        for btn in (owner.custom_edit_btn, owner.custom_delete_btn):

        owner.custom_add_btn = QPushButton("Add")
        owner.custom_edit_btn = QPushButton("Edit")
        owner.custom_delete_btn = QPushButton("Delete")
        for btn in (owner.custom_add_btn, owner.custom_edit_btn, owner.custom_delete_btn):

            btn.setFixedWidth(55)
            btn.setStyleSheet(
                "QPushButton { background: #ffffff; border: 1px solid #a0a0a0; border-radius: 3px; padding: 3px 8px; font-size: 11px; color: #2a2a2a; }"
                "QPushButton:hover { background: #f0f0f0; }"
                "QPushButton:pressed { background: #e0e0e0; }"
            )
            controls_row.addWidget(btn)
        controls_row.addStretch()
        list_layout.addLayout(controls_row)


        self.custom_load_table = QTableWidget(0, 4)
        self.custom_load_table.setHorizontalHeaderLabels([
            "Load Case",
            "Load Type", 
            "Distance from Left (m)",
            "Distance from Bearing (m)"
        ])
        
        self.custom_load_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.custom_load_table.verticalHeader().setVisible(False)
        self.custom_load_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.custom_load_table.setSelectionMode(QTableWidget.SingleSelection)
        self.custom_load_table.setStyleSheet(
            "QTableWidget { "
            "   background: #ffffff; "
            "   border: 1px solid #d0d0d0; "
            "   gridline-color: #e0e0e0; "
            "}"
            "QHeaderView::section { "
            "   color: #2a2a2a; "
            "   background: #f0f0f0; "
            "   font-size: 10px; "
            "   font-weight: 600; "
            "   padding: 5px; "
            "   border: 1px solid #d0d0d0; "
            "}"
            "QTableWidget::item { "
            "   padding: 4px; "
            "   font-size: 10px; "
            "   color: #3a3a3a; "
            "}"
            "QTableWidget::item:selected { "
            "   background: #d0e8ff; "
            "}"
        )
        self.custom_load_table.setMinimumHeight(180)
        
        list_layout.addWidget(self.custom_load_table)

        left_column.addWidget(list_card)

        owner.custom_load_list_container = QWidget()
        self.custom_load_list_layout = QVBoxLayout(owner.custom_load_list_container)
        self.custom_load_list_layout.setContentsMargins(2, 2, 2, 2)
        self.custom_load_list_layout.setSpacing(4)
        self.custom_load_list_layout.addStretch()
        list_layout.addWidget(owner.custom_load_list_container)

        left_column.addWidget(list_card)
        left_column.addStretch()

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
            load_data["custom_load_case_name"] = owner.custom_load_case_name_input.text().strip()
        
        if owner.custom_load_type_combo.currentText() == "Point":
            load_data["point_left"] = owner.custom_point_left_input.text().strip()
            load_data["point_bearing"] = owner.custom_point_bearing_input.text().strip()
        else:
            load_data["line_left_start"] = owner.custom_line_left_start.text().strip()
            load_data["line_left_end"] = owner.custom_line_left_end.text().strip()
            load_data["line_bearing_start"] = owner.custom_line_bearing_start.text().strip()
            load_data["line_bearing_end"] = owner.custom_line_bearing_end.text().strip()
        
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
        
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Saved")
        msg.setText("Custom load has been saved.")
        msg.setStyleSheet("QLabel { color: black; }")
        msg.exec()

    def _on_edit_custom_load(self):
        selected_rows = self.custom_load_table.selectionModel().selectedRows()
        
        if len(selected_rows) == 0:
            QMessageBox.information(self, "Edit", "Please select one custom load to edit.")
            return
        
        if len(selected_rows) > 1:
            QMessageBox.information(self, "Edit", "Please select only one custom load to edit.")
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
            QMessageBox.information(self, "Delete", "Please select at least one custom load to delete.")
            return
        
        rows_to_delete = sorted([row.row() for row in selected_rows], reverse=True)
        
        for row_idx in rows_to_delete:
            if 0 <= row_idx < len(self.custom_load_items):
                del self.custom_load_items[row_idx]
        
        self._refresh_custom_load_table()
        
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Deleted")
        msg.setText(f"{len(rows_to_delete)} custom load(s) deleted.")
        msg.setStyleSheet("QLabel { color: black; } QPushButton { color: black; }")
        msg.exec()

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

        owner.custom_load_type_combo.currentTextChanged.connect(self._on_custom_load_type_changed)
        self._on_custom_load_type_changed(owner.custom_load_type_combo.currentText())

        owner.custom_add_btn.clicked.connect(self._on_add_custom_load)
        owner.custom_delete_btn.clicked.connect(self._on_delete_custom_load)
        owner.custom_edit_btn.clicked.connect(
            lambda: QMessageBox.information(self, "Edit", "Edit functionality will be added in a future update.")
        )

        self._refresh_custom_load_list()

    def _on_custom_load_type_changed(self, text):
        if text.lower().startswith("point"):
            self.custom_load_stack.setCurrentIndex(0)
        else:
            self.custom_load_stack.setCurrentIndex(1)

    def _refresh_custom_load_list(self):
        if not hasattr(self, "custom_load_list_layout"):
            return
        while self.custom_load_list_layout.count():
            item = self.custom_load_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.custom_load_checkboxes = []
        for name in self.custom_load_items:
            row = QHBoxLayout()
            row.setContentsMargins(2, 0, 2, 0)
            row.setSpacing(4)
            label = QLabel(name)
            label.setStyleSheet(
                "font-size: 11px; font-style: italic; color: #3a3a3a; background: transparent; border: none;"
            )
            checkbox = QCheckBox()
            row.addWidget(label)
            row.addStretch()
            row.addWidget(checkbox)
            container = QWidget()
            container.setLayout(row)
            self.custom_load_list_layout.addWidget(container)
            self.custom_load_checkboxes.append((name, checkbox))
        self.custom_load_list_layout.addStretch()

    def _on_add_custom_load(self):
        next_index = len(self.custom_load_items) + 1
        new_name = f"Custom Load {next_index}"
        self.custom_load_items.append(new_name)
        self._refresh_custom_load_list()

    def _on_delete_custom_load(self):
        if not getattr(self, "custom_load_checkboxes", None):
            return
        remaining = [name for name, cb in self.custom_load_checkboxes if not cb.isChecked()]
        if len(remaining) == len(self.custom_load_checkboxes):
            QMessageBox.information(self, "Delete", "Select at least one custom load to delete.")
            return
        self.custom_load_items[:] = remaining
        self._refresh_custom_load_list()

