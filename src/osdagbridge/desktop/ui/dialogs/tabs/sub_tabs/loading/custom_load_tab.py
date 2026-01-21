from PySide6.QtCore import Qt, QSize
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
    QVBoxLayout,
    QWidget,
)

from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style


class CustomLoadTab(QWidget):
    """Custom load input editor."""

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.custom_load_items = getattr(owner, "custom_load_items", [])
        owner.custom_load_items = self.custom_load_items
        self._build_ui()

    def _build_ui(self):
        owner = self.owner

        self.setStyleSheet("background-color: #f0f0f0;")
        
        # Main layout with scroll area
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #f0f0f0; }")
        
        # Create scrollable content widget
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
        field_width = 140

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

        # Create a vertical layout for all fields
        all_fields_layout = QVBoxLayout()
        all_fields_layout.setContentsMargins(0, 0, 0, 0)
        all_fields_layout.setSpacing(10)

        # --- Load Case ---
        load_case_row = QHBoxLayout()
        load_case_row.setSpacing(8)
        
        lbl = QLabel("Load Case:")
        lbl.setStyleSheet(label_style)
        lbl.setFixedWidth(260)  # Fixed width to align with longer labels below
        
        owner.custom_load_case_combo = QComboBox()
        owner.custom_load_case_combo.addItems([
            "DL", "DW", "SIDL", "LL", "EL", "WL", "TL", "Custom"
        ])
        owner.custom_load_case_combo.setFixedWidth(field_width)
        apply_field_style(owner.custom_load_case_combo)
        
        load_case_row.addWidget(lbl)
        load_case_row.addWidget(owner.custom_load_case_combo)
        load_case_row.addStretch()
        all_fields_layout.addLayout(load_case_row)

        # --- Custom Load Case Name ---
        custom_name_row = QHBoxLayout()
        custom_name_row.setSpacing(8)
        
        spacer_label = QLabel(" ")
        spacer_label.setFixedWidth(260)
        spacer_label.setStyleSheet("background: transparent; color: transparent; border: none;")

        owner.custom_load_case_name_input = QLineEdit()
        owner.custom_load_case_name_input.setPlaceholderText("custom")
        owner.custom_load_case_name_input.setFixedWidth(field_width)
        owner.custom_load_case_name_input.setEnabled(False)
        apply_field_style(owner.custom_load_case_name_input)
        
        custom_name_row.addWidget(spacer_label)
        custom_name_row.addWidget(owner.custom_load_case_name_input)
        custom_name_row.addStretch()
        all_fields_layout.addLayout(custom_name_row)

        # --- Load Type ---
        load_type_row = QHBoxLayout()
        load_type_row.setSpacing(8)
        
        lbl = QLabel("Load Type:")
        lbl.setStyleSheet(label_style)
        lbl.setFixedWidth(260)
        
        owner.custom_load_type_combo = QComboBox()
        owner.custom_load_type_combo.addItems(["Point", "Line", "Area"])
        owner.custom_load_type_combo.setFixedWidth(field_width)
        apply_field_style(owner.custom_load_type_combo)
        
        load_type_row.addWidget(lbl)
        load_type_row.addWidget(owner.custom_load_type_combo)
        load_type_row.addStretch()
        all_fields_layout.addLayout(load_type_row)

        input_layout.addLayout(all_fields_layout)

        # Stacked widget for Point/Line/Area inputs
        self.custom_load_stack = QStackedWidget()
        self.custom_load_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.custom_load_stack.setStyleSheet(
            "QStackedWidget { border: none; background: transparent; }"
            "QWidget#customPointWidget, QWidget#customLineWidget { background: transparent; }"
        )

        # Point Widget
        point_widget = QWidget()
        point_widget.setObjectName("customPointWidget")
        point_layout = QVBoxLayout(point_widget)
        point_layout.setContentsMargins(0, 8, 0, 0)
        point_layout.setSpacing(10)

        # Point - Distance from Left Edge
        point_left_row = QHBoxLayout()
        point_left_row.setSpacing(8)
        
        lbl = QLabel("Distance from Left Edge of Bridge (m):")
        lbl.setStyleSheet(label_style)
        lbl.setFixedWidth(260)
        
        owner.custom_point_left_input = QLineEdit()
        owner.custom_point_left_input.setFixedWidth(field_width)
        apply_field_style(owner.custom_point_left_input)
        
        point_left_row.addWidget(lbl)
        point_left_row.addWidget(owner.custom_point_left_input)
        point_left_row.addStretch()
        point_layout.addLayout(point_left_row)

        # Point - Distance from Center Line
        point_bearing_row = QHBoxLayout()
        point_bearing_row.setSpacing(8)
        
        lbl = QLabel("Distance from Center Line of Bearing (m):")
        lbl.setStyleSheet(label_style)
        lbl.setFixedWidth(260)
        
        owner.custom_point_bearing_input = QLineEdit()
        owner.custom_point_bearing_input.setFixedWidth(field_width)
        apply_field_style(owner.custom_point_bearing_input)
        
        point_bearing_row.addWidget(lbl)
        point_bearing_row.addWidget(owner.custom_point_bearing_input)
        point_bearing_row.addStretch()
        point_layout.addLayout(point_bearing_row)

        self.custom_load_stack.addWidget(point_widget)

        # Line Widget
        line_widget = QWidget()
        line_widget.setObjectName("customLineWidget")
        line_layout = QVBoxLayout(line_widget)
        line_layout.setContentsMargins(0, 8, 0, 0)
        line_layout.setSpacing(10)

        # Distance from Left Edge of Bridge
        left_edge_row = QHBoxLayout()
        left_edge_row.setSpacing(8)
        
        left_label = QLabel("Distance from Left Edge of Bridge (m):")
        left_label.setStyleSheet(label_style)
        left_label.setFixedWidth(260)
        
        # Start field
        left_start_container = QVBoxLayout()
        left_start_container.setSpacing(4)
        left_start_lbl = QLabel("Start")
        left_start_lbl.setStyleSheet("font-size: 9px; color: #505050;")
        left_start_lbl.setAlignment(Qt.AlignCenter)
        owner.custom_line_left_start = QLineEdit()
        owner.custom_line_left_start.setFixedWidth(70)
        apply_field_style(owner.custom_line_left_start)
        left_start_container.addWidget(left_start_lbl)
        left_start_container.addWidget(owner.custom_line_left_start)
        
        # End field
        left_end_container = QVBoxLayout()
        left_end_container.setSpacing(4)
        left_end_lbl = QLabel("End")
        left_end_lbl.setStyleSheet("font-size: 9px; color: #505050;")
        left_end_lbl.setAlignment(Qt.AlignCenter)
        owner.custom_line_left_end = QLineEdit()
        owner.custom_line_left_end.setFixedWidth(70)
        apply_field_style(owner.custom_line_left_end)
        left_end_container.addWidget(left_end_lbl)
        left_end_container.addWidget(owner.custom_line_left_end)
        
        left_edge_row.addWidget(left_label)
        left_edge_row.addLayout(left_start_container)
        left_edge_row.addLayout(left_end_container)
        left_edge_row.addStretch()
        line_layout.addLayout(left_edge_row)

        # Distance from Center Line of Bearing
        bearing_row = QHBoxLayout()
        bearing_row.setSpacing(8)
        
        bearing_label = QLabel("Distance from Center Line of Bearing (m):")
        bearing_label.setStyleSheet(label_style)
        bearing_label.setFixedWidth(260)
        
        # Start field
        bearing_start_container = QVBoxLayout()
        bearing_start_container.setSpacing(4)
        bearing_start_lbl = QLabel("Start")
        bearing_start_lbl.setStyleSheet("font-size: 9px; color: #505050;")
        bearing_start_lbl.setAlignment(Qt.AlignCenter)
        owner.custom_line_bearing_start = QLineEdit()
        owner.custom_line_bearing_start.setFixedWidth(70)
        apply_field_style(owner.custom_line_bearing_start)
        bearing_start_container.addWidget(bearing_start_lbl)
        bearing_start_container.addWidget(owner.custom_line_bearing_start)
        
        # End field
        bearing_end_container = QVBoxLayout()
        bearing_end_container.setSpacing(4)
        bearing_end_lbl = QLabel("End")
        bearing_end_lbl.setStyleSheet("font-size: 9px; color: #505050;")
        bearing_end_lbl.setAlignment(Qt.AlignCenter)
        owner.custom_line_bearing_end = QLineEdit()
        owner.custom_line_bearing_end.setFixedWidth(70)
        apply_field_style(owner.custom_line_bearing_end)
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
        save_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        save_btn.setStyleSheet(
            "QPushButton { background: #c8c8c8; border: 1px solid #a0a0a0; border-radius: 3px; padding: 5px 16px; font-weight: 600; font-size: 11px; color: #2a2a2a; }"
            "QPushButton:hover { background: #d8d8d8; }"
            "QPushButton:pressed { background: #b8b8b8; }"
        )
        save_row = QHBoxLayout()
        save_row.setContentsMargins(0, 8, 0, 0)
        save_row.addWidget(save_btn)
        input_layout.addLayout(save_row)

        left_column.addWidget(input_card)

        # Second box for saved loads
        list_card = owner._create_card()
        list_card.setStyleSheet(
            "QFrame { border: 1px solid #a0a0a0; border-radius: 4px; background-color: #ffffff; }"
        )
        list_card.setMinimumHeight(200)
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
            btn.setFixedWidth(55)
            btn.setStyleSheet(
                "QPushButton { background: #ffffff; border: 1px solid #a0a0a0; border-radius: 3px; padding: 3px 8px; font-size: 11px; color: #2a2a2a; }"
                "QPushButton:hover { background: #f0f0f0; }"
                "QPushButton:pressed { background: #e0e0e0; }"
            )
            controls_row.addWidget(btn)
        controls_row.addStretch()
        list_layout.addLayout(controls_row)

        owner.custom_load_list_container = QWidget()
        self.custom_load_list_layout = QVBoxLayout(owner.custom_load_list_container)
        self.custom_load_list_layout.setContentsMargins(2, 2, 2, 2)
        self.custom_load_list_layout.setSpacing(4)
        self.custom_load_list_layout.addStretch()
        list_layout.addWidget(owner.custom_load_list_container)

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

        # Set scroll content and add to main layout
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

        self._refresh_custom_load_list()

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


    def _refresh_custom_load_list(self):
        if not hasattr(self, "custom_load_list_layout"):
            return
        while self.custom_load_list_layout.count():
            item = self.custom_load_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.custom_load_checkboxes = []
        for load_data in self.custom_load_items:
            # load_data is now a dict with name and other properties
            case = load_data.get("load_case", "")
            ltype = load_data.get("load_type", "")
            name = f"{case} - {ltype}"

            row = QHBoxLayout()
            row.setContentsMargins(2, 0, 2, 0)
            row.setSpacing(4)
            
            checkbox = QCheckBox()
            label = QLabel(name)
            label.setStyleSheet(
                "font-size: 11px; font-style: italic; color: #3a3a3a; background: transparent; border: none;"
            )
            
            row.addWidget(checkbox)
            row.addWidget(label)
            row.addStretch()
            
            container = QWidget()
            container.setLayout(row)
            self.custom_load_list_layout.addWidget(container)
            self.custom_load_checkboxes.append((load_data, checkbox))
        self.custom_load_list_layout.addStretch()

    def _on_save_custom_load(self):
        owner = self.owner
        
        # Collect load data
        load_data = {
            "load_case": owner.custom_load_case_combo.currentText(),
            "load_type": owner.custom_load_type_combo.currentText(),
        }
        
        # Add custom load case name if applicable
        if owner.custom_load_case_combo.currentText() == "Custom":
            load_data["custom_load_case_name"] = owner.custom_load_case_name_input.text().strip()
        
        # Add type-specific data
        if owner.custom_load_type_combo.currentText() == "Point":
            load_data["point_left"] = owner.custom_point_left_input.text().strip()
            load_data["point_bearing"] = owner.custom_point_bearing_input.text().strip()
        else:  # Line or Area
            load_data["line_left_start"] = owner.custom_line_left_start.text().strip()
            load_data["line_left_end"] = owner.custom_line_left_end.text().strip()
            load_data["line_bearing_start"] = owner.custom_line_bearing_start.text().strip()
            load_data["line_bearing_end"] = owner.custom_line_bearing_end.text().strip()
        
        # Check if we're editing an existing load
        if hasattr(self, '_editing_load_data') and self._editing_load_data:
            # Update existing load
            for i, item in enumerate(self.custom_load_items):
                if item == self._editing_load_data:
                    self.custom_load_items[i] = load_data
                    break
            self._editing_load_data = None
        else:
            # Add new load
            self.custom_load_items.append(load_data)
        
        # Clear inputs and refresh list
        self._clear_inputs()
        self._refresh_custom_load_list()
        
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Saved")
        msg.setText("Custom load has been saved.")
        msg.setStyleSheet("QLabel { color: black; }")
        msg.exec()

    def _on_edit_custom_load(self):
        if not hasattr(self, "custom_load_checkboxes"):
            return
        
        # Find selected items
        selected = [load_data for load_data, cb in self.custom_load_checkboxes if cb.isChecked()]
        
        if len(selected) == 0:
            QMessageBox.information(self, "Edit", "Please select one custom load to edit.")
            return
        
        if len(selected) > 1:
            QMessageBox.information(self, "Edit", "Please select only one custom load to edit.")
            return
        
        # Load the selected item into the form
        load_data = selected[0]
        self._editing_load_data = load_data
        
        owner = self.owner
        
        # Set load case
        load_case = load_data.get("load_case", "DL")
        index = owner.custom_load_case_combo.findText(load_case)
        if index >= 0:
            owner.custom_load_case_combo.setCurrentIndex(index)
        
        if load_case == "Custom":
            owner.custom_load_case_name_input.setText(load_data.get("custom_load_case_name", ""))
        
        # Set load type
        load_type = load_data.get("load_type", "Point")
        index = owner.custom_load_type_combo.findText(load_type)
        if index >= 0:
            owner.custom_load_type_combo.setCurrentIndex(index)
        
        # Load type-specific data
        if load_type == "Point":
            owner.custom_point_left_input.setText(load_data.get("point_left", ""))
            owner.custom_point_bearing_input.setText(load_data.get("point_bearing", ""))
        else:
            owner.custom_line_left_start.setText(load_data.get("line_left_start", ""))
            owner.custom_line_left_end.setText(load_data.get("line_left_end", ""))
            owner.custom_line_bearing_start.setText(load_data.get("line_bearing_start", ""))
            owner.custom_line_bearing_end.setText(load_data.get("line_bearing_end", ""))

    def _on_delete_custom_load(self):
        if not hasattr(self, "custom_load_checkboxes"):
            return
        
        # Find selected items
        selected = [load_data for load_data, cb in self.custom_load_checkboxes if cb.isChecked()]
        
        if len(selected) == 0:
            QMessageBox.information(self, "Delete", "Please select at least one custom load to delete.")
            return
        
        # Remove selected items
        for load_data in selected:
            if load_data in self.custom_load_items:
                self.custom_load_items.remove(load_data)
        
        self._refresh_custom_load_list()
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Deleted")
        msg.setText(f"{len(selected)} custom load(s) deleted.")
        msg.setStyleSheet("""
        QLabel { color: black; }
        QPushButton { color: black; }
        """)
        msg.exec()


    def _clear_inputs(self):
        """Clear all input fields"""
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
        """Reset Custom Load inputs to default values"""
        # Clear inputs
        self._clear_inputs()
        
        # Disable custom load case field
        self.owner.custom_load_case_name_input.setEnabled(False)
        
        # Clear custom load items list
        self.custom_load_items.clear()
        self._refresh_custom_load_list()
        
        # Clear editing state
        if hasattr(self, '_editing_load_data'):
            self._editing_load_data = None