"""Dialog for adding or editing custom live load vehicles."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar

class CustomVehicleDialog(QDialog):
    """Dialog for adding or editing custom live load vehicles"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.vehicle_data = None
        self._selected_axle_row = None
        self.setWindowTitle("Live Load Custom Vehicle Add/Edit")
        self.setObjectName("custom_vehicle_dialog")
        self.setModal(True)
        self.resize(640, 580)
        self.setMinimumSize(620, 560)
        self.setMaximumSize(16777215, 16777215)
        self.setStyleSheet("""
            QDialog#custom_vehicle_dialog {
                background-color: #ffffff;
                border: 1px solid #90AF13;
            }
            QDialog#custom_vehicle_dialog QWidget#CustomTitleBar {
                background-color: #ffffff;
            }
            QDialog#custom_vehicle_dialog QLabel#TitleLabel {
                color: #2b2b2b;
            }
            QDialog#custom_vehicle_dialog QWidget#BottomLine {
                background-color: #90AF13;
            }
            QDialog#custom_vehicle_dialog QToolButton#CloseButton {
                background: transparent;
                color: #1f1f1f;
                border: none;
            }
            QDialog#custom_vehicle_dialog QToolButton#CloseButton:hover {
                background: #e81123;
                color: #ffffff;
            }
            QDialog#custom_vehicle_dialog QToolButton#CloseButton:pressed {
                background: #c50f1f;
                color: #ffffff;
            }
            QLabel { color: #2b2b2b; font-size: 11px; background: transparent; }
            QPushButton {
                background-color: #ffffff;
                color: #2b2b2b;
                border: 1px solid #8a8a8a;
                border-radius: 4px;
                padding: 5px 12px;
                min-width: 50px;
            }
            QPushButton:hover { background-color: #e8e8e8; }
            QPushButton:pressed { background-color: #d8d8d8; }
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #8a8a8a;
                gridline-color: #d0d0d0;
                color: #2b2b2b;
            }
            QTableWidget::item { padding: 4px; }
            QHeaderView::section {
                background-color: #f0f0f0;
                color: #2b2b2b;
                border: 1px solid #d0d0d0;
                padding: 4px;
                font-weight: 600;
            }
        """)
        self.setupWrapper()
        self.init_ui()
        self._setup_validators()
        self._connect_signals()
        self._refresh_axle_buttons_state()
        self._on_vehicle_type_changed(self.vehicle_type_combo.currentText())

    def setupWrapper(self):
        # Keep frameless behavior but avoid native min/max tracking glitches on Windows.
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        self.title_bar = CustomTitleBar(parent=self)
        self.title_bar.setTitle("Live Load Custom Vehicle Add/Edit")
        main_layout.addWidget(self.title_bar)

        self.content_widget = QWidget(self)
        self.content_widget.setStyleSheet("background-color: #ffffff;")
        main_layout.addWidget(self.content_widget, 1)

    def init_ui(self):
        layout = QVBoxLayout(self.content_widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Vehicle Name row
        name_row = QHBoxLayout()
        name_row.setSpacing(10)
        name_label = QLabel("Vehicle Name:")
        name_label.setStyleSheet("font-weight: 600;")
        self.vehicle_name_input = QLineEdit()
        self.vehicle_name_input.setFixedWidth(165)
        apply_field_style(self.vehicle_name_input)
        name_row.addWidget(name_label)
        name_row.addWidget(self.vehicle_name_input)

        name_row.addSpacing(20)
        type_label = QLabel("Vehicle Type:")
        type_label.setStyleSheet("font-weight: 600;")
        self.vehicle_type_combo = QComboBox()
        self.vehicle_type_combo.addItems(["Wheeled", "Tracked", "Bogie"])
        self.vehicle_type_combo.setFixedWidth(120)
        apply_field_style(self.vehicle_type_combo)
        name_row.addWidget(type_label)
        name_row.addWidget(self.vehicle_type_combo)

        name_row.addStretch()
        layout.addLayout(name_row)

        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)

        # --- Page 1: Wheeled ---
        self.wheeled_page = QWidget()
        wheeled_layout = QVBoxLayout(self.wheeled_page)
        wheeled_layout.setContentsMargins(0, 0, 0, 0)
        wheeled_layout.setSpacing(8)
        wheeled_layout.setAlignment(Qt.AlignTop)

        # P# D# row with Add/Modify/Delete buttons
        pd_button_row = QHBoxLayout()
        pd_button_row.setSpacing(8)

        self.p_label = QLabel("Load, P# (kN)")
        self.P_input = QLineEdit()
        self.P_input.setFixedWidth(68)
        apply_field_style(self.P_input)
        pd_button_row.addWidget(self.p_label)
        pd_button_row.addWidget(self.P_input)

        self.d_label = QLabel("Spacing, D# (m)")
        self.D_input = QLineEdit()
        self.D_input.setFixedWidth(68)
        apply_field_style(self.D_input)
        pd_button_row.addWidget(self.d_label)
        pd_button_row.addWidget(self.D_input)

        pd_button_row.addStretch()

        self.add_axle_button = QPushButton("Add")
        self.modify_axle_button = QPushButton("Modify")
        self.delete_axle_button = QPushButton("Delete")
        pd_button_row.addWidget(self.add_axle_button)
        pd_button_row.addWidget(self.modify_axle_button)
        pd_button_row.addWidget(self.delete_axle_button)

        wheeled_layout.addLayout(pd_button_row)

        # Table and diagram row
        table_diagram_row = QHBoxLayout()
        table_diagram_row.setSpacing(10)

        # Axle table
        self.axle_table = QTableWidget()
        self.axle_table.setColumnCount(3)
        self.axle_table.setHorizontalHeaderLabels(["S.No.", "Load (kN)", "Spacing (m)"])
        self.axle_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.axle_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.axle_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.axle_table.setColumnWidth(0, 52)
        self.axle_table.verticalHeader().setVisible(False)
        self.axle_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.axle_table.setSelectionMode(QTableWidget.SingleSelection)
        self.axle_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.axle_table.setShowGrid(True)
        self.axle_table.setFrameShape(QTableWidget.StyledPanel)
        self.axle_table.setLineWidth(1)
        self.axle_table.setMinimumHeight(118)
        self.axle_table.setMaximumHeight(118)
        table_diagram_row.addWidget(self.axle_table, 1)

        # Axle diagram placeholder
        self.axle_diagram = QLabel("Axle Layout Diagram")
        self.axle_diagram.setAlignment(Qt.AlignCenter)
        self.axle_diagram.setMinimumHeight(118)
        self.axle_diagram.setMaximumHeight(118)
        self.axle_diagram.setStyleSheet("""
            QLabel {
                border: 1px solid #8a8a8a;
                border-radius: 4px;
                background: #ffffff;
                color: #6a6a6a;
                font-size: 10px;
            }
        """)
        table_diagram_row.addWidget(self.axle_diagram, 1)

        wheeled_layout.addLayout(table_diagram_row)
        self.stacked_widget.addWidget(self.wheeled_page)

        # --- Page 2: Tracked / Bogie ---
        self.tb_page = QWidget()
        tb_layout = QVBoxLayout(self.tb_page)
        tb_layout.setContentsMargins(0, 0, 0, 0)
        tb_layout.setSpacing(8)
        tb_layout.setAlignment(Qt.AlignTop)
        
        # Spacer strictly balancing the top buttons row from wheeled_page
        top_spacer = QWidget()
        top_spacer.setFixedHeight(30)
        tb_layout.addWidget(top_spacer)

        tb_bottom_row = QHBoxLayout()
        tb_bottom_row.setSpacing(10)

        # Left side inputs (P, D)
        tb_inputs_layout = QVBoxLayout()
        tb_inputs_layout.setSpacing(8)
        tb_inputs_layout.setContentsMargins(0, 0, 0, 0)
        
        tb_inputs_layout.addStretch()
        
        tb_p_row = QHBoxLayout()
        self.tb_p_label = QLabel("P (kN)")
        self.tb_p_label.setFixedWidth(50)
        self.tb_P_input = QLineEdit()
        self.tb_P_input.setFixedWidth(68)
        apply_field_style(self.tb_P_input)
        tb_p_row.addWidget(self.tb_p_label)
        tb_p_row.addWidget(self.tb_P_input)
        tb_p_row.addStretch()
        
        tb_d_row = QHBoxLayout()
        self.tb_d_label = QLabel("D (m)")
        self.tb_d_label.setFixedWidth(50)
        self.tb_D_input = QLineEdit()
        self.tb_D_input.setFixedWidth(68)
        apply_field_style(self.tb_D_input)
        tb_d_row.addWidget(self.tb_d_label)
        tb_d_row.addWidget(self.tb_D_input)
        tb_d_row.addStretch()

        tb_inputs_layout.addLayout(tb_p_row)
        tb_inputs_layout.addLayout(tb_d_row)
        tb_inputs_layout.addStretch()
        
        left_widget = QWidget()
        left_widget.setLayout(tb_inputs_layout)
        tb_bottom_row.addWidget(left_widget, 1)

        # Right side diagram
        self.tb_axle_diagram = QLabel("Tracked Layout Diagram")
        self.tb_axle_diagram.setAlignment(Qt.AlignCenter)
        self.tb_axle_diagram.setMinimumHeight(118)
        self.tb_axle_diagram.setMaximumHeight(118)
        self.tb_axle_diagram.setStyleSheet("""
            QLabel {
                border: 1px solid #8a8a8a;
                border-radius: 4px;
                background: #ffffff;
                color: #6a6a6a;
                font-size: 10px;
            }
        """)
        tb_bottom_row.addWidget(self.tb_axle_diagram, 1)
        
        tb_layout.addLayout(tb_bottom_row)
        
        self.stacked_widget.addWidget(self.tb_page)

        # Input fields grid
        fields_grid = QGridLayout()
        fields_grid.setContentsMargins(0, 6, 0, 0)
        fields_grid.setHorizontalSpacing(10)
        fields_grid.setVerticalSpacing(12)
        fields_grid.setColumnMinimumWidth(0, 340)

        field_labels = [
            "Minimum nose to tail distance (m)",
            "Width of Wheel, w (mm)",
            "Minimum Clearance from Carriageway Edge, f (mm)",
            "Minimum Clearance from Crossing Vehicles, g (mm)",
            "Wheel Spacing in Transverse Direction (m)",
            "Impact Factor",
        ]
        self._required_labels = field_labels[:-1]

        self.custom_fields = {}
        for row, text in enumerate(field_labels):
            lbl = QLabel(text)
            lbl.setWordWrap(False)
            lbl.setFixedWidth(340)
            field = QLineEdit()
            if "Impact" in text:
                field.setText("0.25")
                field.setReadOnly(True)
            field.setFixedWidth(150)
            field.setFixedHeight(28)
            apply_field_style(field)
            fields_grid.setRowMinimumHeight(row, 32)
            fields_grid.addWidget(lbl, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
            fields_grid.addWidget(field, row, 1, Qt.AlignLeft | Qt.AlignVCenter)
            self.custom_fields[text] = field

        layout.addLayout(fields_grid)

        # Keep heading clear from the last input row.
        layout.addSpacing(16)

        bottom_diagram = QLabel("")
        bottom_diagram.setAlignment(Qt.AlignCenter)
        bottom_diagram.setMinimumHeight(62)
        bottom_diagram.setStyleSheet("""
            QLabel {
                border: 1px solid #8a8a8a;
                border-radius: 4px;
                background: #ffffff;
            }
        """)
        layout.addWidget(bottom_diagram)

        button_row = QHBoxLayout()
        button_row.addStretch()
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        self.save_button.setFixedWidth(90)
        self.cancel_button.setFixedWidth(90)
        button_row.addWidget(self.save_button)
        button_row.addWidget(self.cancel_button)
        layout.addLayout(button_row)

    def _setup_validators(self):
        numeric = QDoubleValidator(0.0, 1_000_000.0, 3, self)
        numeric.setNotation(QDoubleValidator.StandardNotation)
        self.P_input.setValidator(numeric)
        self.D_input.setValidator(numeric)
        self.tb_P_input.setValidator(numeric)
        self.tb_D_input.setValidator(numeric)

        for label, field in self.custom_fields.items():
            if "Impact" in label:
                continue
            validator = QDoubleValidator(0.0, 1_000_000.0, 3, self)
            validator.setNotation(QDoubleValidator.StandardNotation)
            field.setValidator(validator)

    def _connect_signals(self):
        self.add_axle_button.clicked.connect(self._add_axle)
        self.modify_axle_button.clicked.connect(self._modify_axle)
        self.delete_axle_button.clicked.connect(self._delete_axle)
        self.axle_table.itemSelectionChanged.connect(self._on_axle_selection_changed)
        self.save_button.clicked.connect(self._save_and_accept)
        self.cancel_button.clicked.connect(self.reject)
        self.vehicle_type_combo.currentTextChanged.connect(self._on_vehicle_type_changed)

    def _on_vehicle_type_changed(self, text):
        is_wheeled = text == "Wheeled"
        if is_wheeled:
            self.stacked_widget.setCurrentIndex(0)
            self._refresh_axle_buttons_state()
        else:
            self.stacked_widget.setCurrentIndex(1)
            is_bogie = text == "Bogie"
            self.tb_p_label.setText("P<sub>b</sub> (kN)" if is_bogie else "P (kN)")
            self.tb_d_label.setText("D<sub>b</sub> (m)" if is_bogie else "D (m)")
            self.tb_axle_diagram.setText("Bogie Layout Diagram" if is_bogie else "Tracked Layout Diagram")

    def _refresh_axle_buttons_state(self):
        enabled = self._selected_axle_row is not None
        self.modify_axle_button.setEnabled(enabled)
        self.delete_axle_button.setEnabled(enabled)

    @staticmethod
    def _fmt(value):
        text = f"{value:.3f}".rstrip("0").rstrip(".")
        return text if text else "0"

    def _validate_axle_inputs(self):
        p_text = self.P_input.text().strip()
        d_text = self.D_input.text().strip()
        if not p_text or not d_text:
            QMessageBox.warning(self, "Invalid Axle", "Please enter both P# and D# values.")
            return None

        try:
            p_value = float(p_text)
            d_value = float(d_text)
        except ValueError:
            QMessageBox.warning(self, "Invalid Axle", "P# and D# must be numeric values.")
            return None

        if p_value <= 0:
            QMessageBox.warning(self, "Invalid Axle", "P# must be greater than 0.")
            return None
        if d_value < 0:
            QMessageBox.warning(self, "Invalid Axle", "D# cannot be negative.")
            return None
        return p_value, d_value

    def _set_axle_row(self, row, load_value, spacing_value):
        load_item = QTableWidgetItem(self._fmt(load_value))
        spacing_item = QTableWidgetItem(self._fmt(spacing_value))
        for item in (load_item, spacing_item):
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            item.setTextAlignment(Qt.AlignCenter)
        self.axle_table.setItem(row, 1, load_item)
        self.axle_table.setItem(row, 2, spacing_item)

    def _renumber_rows(self):
        for row in range(self.axle_table.rowCount()):
            serial_item = QTableWidgetItem(str(row + 1))
            serial_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            serial_item.setTextAlignment(Qt.AlignCenter)
            self.axle_table.setItem(row, 0, serial_item)

    def _on_axle_selection_changed(self):
        selected = self.axle_table.selectedItems()
        if not selected:
            self._selected_axle_row = None
            self._refresh_axle_buttons_state()
            return

        row = selected[0].row()
        self._selected_axle_row = row
        load_item = self.axle_table.item(row, 1)
        spacing_item = self.axle_table.item(row, 2)
        self.P_input.setText(load_item.text() if load_item else "")
        self.D_input.setText(spacing_item.text() if spacing_item else "")
        self._refresh_axle_buttons_state()

    def _add_axle(self):
        values = self._validate_axle_inputs()
        if values is None:
            return
        load_value, spacing_value = values
        row = self.axle_table.rowCount()
        self.axle_table.insertRow(row)
        self._set_axle_row(row, load_value, spacing_value)
        self._renumber_rows()
        self.axle_table.selectRow(row)

    def _modify_axle(self):
        if self._selected_axle_row is None:
            QMessageBox.information(self, "No Selection", "Select an axle row to modify.")
            return
        values = self._validate_axle_inputs()
        if values is None:
            return
        load_value, spacing_value = values
        self._set_axle_row(self._selected_axle_row, load_value, spacing_value)

    def _delete_axle(self):
        if self._selected_axle_row is None:
            QMessageBox.information(self, "No Selection", "Select an axle row to delete.")
            return
        self.axle_table.removeRow(self._selected_axle_row)
        self._selected_axle_row = None
        self._renumber_rows()
        self.P_input.clear()
        self.D_input.clear()
        self._refresh_axle_buttons_state()

    def _field_float(self, label_text):
        text = self.custom_fields[label_text].text().strip()
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None

    def _save_and_accept(self):
        name = self.vehicle_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Invalid Vehicle", "Please enter vehicle name.")
            return

        vtype = self.vehicle_type_combo.currentText()
        if vtype in ["Tracked", "Bogie"]:
            p_text = self.tb_P_input.text().strip()
            d_text = self.tb_D_input.text().strip()
            if not p_text or not d_text:
                QMessageBox.warning(self, "Invalid Vehicle", "Please enter both Load and Spacing.")
                return
            try:
                load_kN = float(p_text)
                spacing_m = float(d_text)
            except ValueError:
                QMessageBox.warning(self, "Invalid Vehicle", "Load and Spacing must be numeric values.")
                return
            if load_kN <= 0:
                QMessageBox.warning(self, "Invalid Vehicle", "Load must be greater than 0.")
                return
            if spacing_m < 0:
                QMessageBox.warning(self, "Invalid Vehicle", "Spacing cannot be negative.")
                return
            axles = [{"load_kN": load_kN, "spacing_m": spacing_m}]
        else:
            if self.axle_table.rowCount() == 0:
                QMessageBox.warning(self, "Invalid Vehicle", "Please add at least one axle.")
                return
            axles = []
            for row in range(self.axle_table.rowCount()):
                load_item = self.axle_table.item(row, 1)
                spacing_item = self.axle_table.item(row, 2)
                if not load_item or not spacing_item:
                    continue
                axles.append({"load_kN": float(load_item.text()), "spacing_m": float(spacing_item.text())})

        for label in self._required_labels:
            if self._field_float(label) is None:
                QMessageBox.warning(
                    self,
                    "Incomplete Inputs",
                    f"Please enter a valid value for: {label.replace(chr(10), ' ')}",
                )
                return

        self.vehicle_data = {
            "name": name,
            "vehicle_type": self.vehicle_type_combo.currentText(),
            "axles": axles,
            "axle_loads": [a["load_kN"] for a in axles],
            "axle_spacings": [a["spacing_m"] for a in axles],
            "minimum_nose_to_tail_distance_m": self._field_float("Minimum nose to tail distance (m)"),
            "wheel_width_mm": self._field_float("Width of Wheel, w (mm)"),
            "minimum_clearance_carriageway_edge_mm": self._field_float("Minimum Clearance from Carriageway Edge, f (mm)"),
            "minimum_clearance_crossing_vehicles_mm": self._field_float("Minimum Clearance from Crossing Vehicles, g (mm)"),
            "wheel_spacing_transverse_m": self._field_float("Wheel Spacing in Transverse Direction (m)"),
            "impact_factor": self._field_float("Impact Factor") or 0.25,
        }
        self.accept()

    def load_vehicle_data(self, vehicle_data):
        self.vehicle_name_input.setText(str(vehicle_data.get("name", "")))
        vtype = vehicle_data.get("vehicle_type", "Wheeled")
        idx = self.vehicle_type_combo.findText(vtype)
        if idx >= 0:
            self.vehicle_type_combo.setCurrentIndex(idx)
        self.axle_table.setRowCount(0)
        self._selected_axle_row = None

        axles = vehicle_data.get("axles")
        if not axles:
            loads = vehicle_data.get("axle_loads", [])
            spacings = vehicle_data.get("axle_spacings", [])
            axles = [
                {"load_kN": loads[i], "spacing_m": spacings[i]}
                for i in range(min(len(loads), len(spacings)))
            ]

        if vtype in ["Tracked", "Bogie"]:
            if axles:
                self.tb_P_input.setText(self._fmt(float(axles[0].get("load_kN", 0.0))))
                self.tb_D_input.setText(self._fmt(float(axles[0].get("spacing_m", 0.0))))
        else:
            for axle in axles:
                row = self.axle_table.rowCount()
                self.axle_table.insertRow(row)
                self._set_axle_row(row, float(axle.get("load_kN", 0.0)), float(axle.get("spacing_m", 0.0)))
            self._renumber_rows()

        mapping = {
            "Minimum nose to tail distance (m)": "minimum_nose_to_tail_distance_m",
            "Width of Wheel, w (mm)": "wheel_width_mm",
            "Minimum Clearance from Carriageway Edge, f (mm)": "minimum_clearance_carriageway_edge_mm",
            "Minimum Clearance from Crossing Vehicles, g (mm)": "minimum_clearance_crossing_vehicles_mm",
            "Wheel Spacing in Transverse Direction (m)": "wheel_spacing_transverse_m",
            "Impact Factor": "impact_factor",
        }
        for label, key in mapping.items():
            value = vehicle_data.get(key)
            self.custom_fields[label].setText("") if value is None else self.custom_fields[label].setText(self._fmt(float(value)))

        self._refresh_axle_buttons_state()
        self._on_vehicle_type_changed(vtype)

