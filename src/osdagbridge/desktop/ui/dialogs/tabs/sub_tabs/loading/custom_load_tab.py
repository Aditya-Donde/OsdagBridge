from PySide6.QtCore import Qt, QSize, QTimer
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
    QButtonGroup,
    QSplitter,
)

from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox, MessageBoxType
from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import CUSTOM_LOAD_TAB_SCHEMA
from osdagbridge.desktop.ui.widgets.custom_load_canvas import CustomLoadCanvas


class CustomLoadTab(QWidget):

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.custom_load_items = getattr(owner, "custom_load_items", [])
        owner.custom_load_items = self.custom_load_items
        self.schema = CUSTOM_LOAD_TAB_SCHEMA
        self._editing_load_data = None
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

        label_style = "font-size: 11px; color: #2a2a2a; background: transparent; border: none;"
        heading_style = "font-size: 11px; font-weight: 700; color: #1a1a1a; background: transparent; border: none;"
        
        label_width = schema.get("label_width", 280)
        field_width = schema.get("field_width", 140)
        
        h_splitter = QSplitter(Qt.Horizontal)
        h_splitter.setHandleWidth(8)
        h_splitter.setChildrenCollapsible(False)

        left_pane = QWidget()
        left_pane.setStyleSheet("background: transparent;")
        left_layout = QVBoxLayout(left_pane)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        diagram = QFrame()
        diagram.setMinimumSize(QSize(400, 300))
        diagram.setStyleSheet(
            "QFrame { border: 1px solid #a0a0a0; border-radius: 3px; background-color: #f8f9fa; }"
        )
        diagram_layout = QVBoxLayout(diagram)
        diagram_layout.setContentsMargins(0, 0, 0, 0)
        
        # View Toggle Buttons
        toggle_layout = QHBoxLayout()
        toggle_layout.setContentsMargins(10, 10, 10, 0)
        
        self.btn_cross_section = QPushButton("Cross-Section")
        self.btn_elevation = QPushButton("Elevation")
        
        self.btn_cross_section.setCheckable(True)
        self.btn_elevation.setCheckable(True)
        self.btn_cross_section.setChecked(True)
        
        self.view_btn_group = QButtonGroup(self)
        self.view_btn_group.addButton(self.btn_cross_section, 0)
        self.view_btn_group.addButton(self.btn_elevation, 1)
        
        btn_style = """
            QPushButton {
                background: #ffffff;
                border: 1px solid #a0a0a0;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 600;
                color: #2a2a2a;
            }
            QPushButton:checked {
                background: #90AF13;
                border: 1px solid #90AF13;
                color: #ffffff;
            }
        """
        self.btn_cross_section.setStyleSheet(btn_style)
        self.btn_elevation.setStyleSheet(btn_style)
        
        toggle_layout.addWidget(self.btn_cross_section)
        toggle_layout.addWidget(self.btn_elevation)
        toggle_layout.addStretch()
        
        diagram_layout.addLayout(toggle_layout)
        
        # 2D view with zoom controls
        canvas_container = QWidget()
        canvas_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        canvas_container_layout = QGridLayout(canvas_container)
        canvas_container_layout.setContentsMargins(0, 0, 0, 0)
        canvas_container_layout.setSpacing(0)

        self.canvas = CustomLoadCanvas()
        canvas_container_layout.addWidget(self.canvas, 0, 0)
    
        self.zoom_overlay_2d = QWidget()
        self.zoom_overlay_2d.setObjectName("zoomControls")
        self.zoom_overlay_2d.setAttribute(Qt.WA_TranslucentBackground)
        zoom_layout = QVBoxLayout(self.zoom_overlay_2d)
        zoom_layout.setContentsMargins(0, 15, 15, 0) # Gap from top-right edge
        zoom_layout.setSpacing(6)
        zoom_layout.setAlignment(Qt.AlignTop | Qt.AlignRight)

        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_out = QPushButton("-")
        self.btn_zoom_reset = QPushButton("Reset")

        zoom_btn_style = """
            QPushButton {
                background: #ffffff;
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                min-width: 32px;
                max-width: 60px;
                padding: 6px;
                font-size: 14px;
                font-weight: bold;
                color: #2a2a2a;
            }
            QPushButton:hover { background: #f8f9fa; border: 1px solid #90AF13; }
            QPushButton:pressed { background: #e9ecef; }
        """
        self.btn_zoom_in.setStyleSheet(zoom_btn_style)
        self.btn_zoom_out.setStyleSheet(zoom_btn_style)
        self.btn_zoom_reset.setStyleSheet(zoom_btn_style.replace("14px", "11px"))

        zoom_layout.addWidget(self.btn_zoom_in)
        zoom_layout.addWidget(self.btn_zoom_out)
        zoom_layout.addWidget(self.btn_zoom_reset)
 
        canvas_container_layout.addWidget(self.zoom_overlay_2d, 0, 0, Qt.AlignTop | Qt.AlignRight)
        
        diagram_layout.addWidget(canvas_container, 1)
        
        # Save Diagram Button
        save_diagram_layout = QHBoxLayout()
        save_diagram_layout.setContentsMargins(10, 0, 10, 10)
        self.btn_save_diagram = QPushButton("Save Diagram")
        self.btn_save_diagram.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                border: 1px solid #a0a0a0;
                border-radius: 3px;
                padding: 4px 10px;
                font-size: 11px;
                color: #2a2a2a;
            }
            QPushButton:hover { background: #f0f0f0; }
        """)
        save_diagram_layout.addStretch()
        save_diagram_layout.addWidget(self.btn_save_diagram)
        
        diagram_layout.addLayout(save_diagram_layout)
        left_layout.addWidget(diagram)

        # info box on the right
        desc_box = QFrame()
        desc_box.setMinimumWidth(260)
        desc_box.setStyleSheet(
            "QFrame { "
            "   border: 1px solid #bcbcbc; "
            "   border-radius: 4px; "
            "   background-color: #ececec; "
            "}"
        )
        desc_box_layout = QVBoxLayout(desc_box)
        desc_box_layout.setContentsMargins(15, 15, 15, 15)
        desc_box_layout.setSpacing(12)

        desc_title = QLabel("Custom Load View & Configuration")
        desc_title.setStyleSheet(
            "font-size: 13px; font-weight: 700; color: #1a1a1a; "
            "background: transparent; border: none; padding-bottom: 5px;"
        )
        desc_box_layout.addWidget(desc_title)

        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Plain)
        line.setStyleSheet("color: #bcbcbc; background: #bcbcbc; max-height: 1px; border: none;")
        desc_box_layout.addWidget(line)

        desc_text = QLabel(
            "<div style='color: #2a2a2a; line-height: 1.5;'>"
            "<p style='margin-bottom: 10px;'>This tab allows for the definition of user-specified loads. "
            "The diagram updates instantly to show the correct load placement relative to the bridge geometry.</p>"
            
            "<b style='color: #90AF13;'>Available View Modes:</b>"
            "<ul style='margin: 5px 0 12px 15px;'>"
            "<li><b>Cross-Section:</b> Shows the transverse position of loads across the bridge width and girders.</li>"
            "<li><b>Elevation:</b> Shows the longitudinal position of loads along the span length.</li>"
            "</ul>"
 
            "<b style='color: #444444;'>How to add a load:</b>"
            "<ol style='margin: 5px 0 12px 15px;'>"
            "<li>Select the <b>Load Case</b> (Dead, Live, etc.) and enter a name.</li>"
            "<li>Choose a <b>Load Type</b> (Point, Line, or Area) from the dropdown.</li>"
            "<li>Enter the <b>Magnitude</b> and <b>Distances</b> from the reference edges.</li>"
            "<li>Click <b>Save</b> to add the current load to the table below.</li>"
            "</ol>"
            
            "<p style='margin-top: 5px; color: #555;'>"
            "Saved loads can be modified using the <b>Edit</b> button or removed using the <b>Delete</b> button.</p>"
            "</div>"
        )
        desc_text.setWordWrap(True)
        desc_text.setTextFormat(Qt.RichText)
        desc_text.setStyleSheet("font-size: 11px; background: transparent; border: none;")
        desc_box_layout.addWidget(desc_text)
        desc_box_layout.addStretch()

        # Assembly into splitters
        h_splitter.addWidget(left_pane)
        h_splitter.addWidget(desc_box)
        h_splitter.setStretchFactor(0, 3)
        h_splitter.setStretchFactor(1, 1)

        input_card = owner._create_card()
        input_card.setStyleSheet(
            "QFrame { "
            "   border: 1px solid #bcbcbc; "
            "   border-radius: 4px; "
            "   background-color: #ececec; "
            "}"
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

        magnitude_row = QHBoxLayout()
        magnitude_row.setSpacing(8)
        
        self.magnitude_label = QLabel("Magnitude (kN):")
        self.magnitude_label.setStyleSheet(label_style)
        self.magnitude_label.setFixedWidth(label_width)
        
        owner.custom_load_magnitude_input = QLineEdit()
        owner.custom_load_magnitude_input.setFixedWidth(field_width * 2 + 8)
        apply_field_style(owner.custom_load_magnitude_input)
        self._apply_validator(owner.custom_load_magnitude_input, {"type": "double_range", "bottom": 0.0, "top": 100000.0, "decimals": 2})
        
        magnitude_row.addWidget(self.magnitude_label)
        magnitude_row.addWidget(owner.custom_load_magnitude_input)
        magnitude_row.addStretch()
        all_fields_layout.addLayout(magnitude_row)

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

        left_layout.addWidget(input_card)

        list_card = owner._create_card()
        list_card.setStyleSheet(
            "QFrame { "
            "   border: 1px solid #bcbcbc; "
            "   border-radius: 4px; "
            "   background-color: #ececec; "
            "}"
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
        
        self.custom_load_table = QTableWidget(0, 5)
    
        self.custom_load_table.setFrameStyle(QFrame.NoFrame)
        self.custom_load_table.setContentsMargins(0, 0, 0, 0)
        self.custom_load_table.viewport().setContentsMargins(0, 0, 0, 0)
        self.custom_load_table.setShowGrid(True)

        self.custom_load_table.setHorizontalHeaderLabels([
            "Load Case",
            "Load Type", 
            "Magnitude",
            "Distance from Left (m)",
            "Distance from Bearing (m)"
        ])
        
        self.custom_load_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
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

        left_layout.addWidget(list_card)
        left_layout.addStretch()

        page_layout.addWidget(h_splitter)

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        owner.custom_load_type_combo.currentTextChanged.connect(self._on_custom_load_type_changed)
        self._on_custom_load_type_changed(owner.custom_load_type_combo.currentText())

        save_btn.clicked.connect(self._on_save_custom_load)
        owner.custom_delete_btn.clicked.connect(self._on_delete_custom_load)
        owner.custom_edit_btn.clicked.connect(self._on_edit_custom_load)
        owner.custom_load_case_combo.currentTextChanged.connect(self._on_load_case_changed)

        self.btn_zoom_in.clicked.connect(self.canvas.zoom_in)
        self.btn_zoom_out.clicked.connect(self.canvas.zoom_out)
        self.btn_zoom_reset.clicked.connect(self.canvas.reset_view)

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

    def _schedule_update(self, *args):
        pass

    def _update_visualization(self, *args):
        pass

    def _on_view_toggled(self, btn):
        pass

    def _on_save_diagram(self):
        pass

    def _on_custom_load_type_changed(self, text):
        if text == "Point":
            self.custom_load_stack.setCurrentIndex(0)
            self.magnitude_label.setText("Magnitude (kN):")
        elif text == "Line":
            self.custom_load_stack.setCurrentIndex(1)
            self.magnitude_label.setText("Magnitude (kN/m):")
        elif text == "Area":
            self.custom_load_stack.setCurrentIndex(1)
            self.magnitude_label.setText("Magnitude (kN/m²):")

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
            
            item = QTableWidgetItem("")
            self.custom_load_table.setItem(row_idx, 2, item)
            
            if load_type == "Point":
                dist_left = load_data.get("point_left", "")
            else:
                start = load_data.get("line_left_start", "")
                end = load_data.get("line_left_end", "")
                dist_left = f"{start} - {end}"
            
            item = QTableWidgetItem(dist_left)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.custom_load_table.setItem(row_idx, 3, item)
            
            if load_type == "Point":
                dist_bearing = load_data.get("point_bearing", "")
            else:
                start = load_data.get("line_bearing_start", "")
                end = load_data.get("line_bearing_end", "")
                dist_bearing = f"{start} - {end}"
            
            item = QTableWidgetItem(dist_bearing)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.custom_load_table.setItem(row_idx, 4, item)

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
        
        self.custom_load_table.clearSelection()
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
