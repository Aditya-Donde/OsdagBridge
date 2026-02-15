"""Auto-generated tab module extracted from additional_inputs."""
import sys
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTabBar, QLabel, QLineEdit,
    QComboBox, QGroupBox, QFormLayout, QPushButton, QScrollArea,
    QCheckBox, QMessageBox, QSizePolicy, QSpacerItem, QStackedWidget,
    QFrame, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QDialog, QSizePolicy, QSizeGrip
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QDoubleValidator, QIntValidator

from osdagbridge.core.utils.common import *
from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.desktop.ui.widgets.vehicle_viewer import VehicleViewer

class CustomVehicleDialog(QDialog):
    """Dialog for adding or editing custom live load vehicles"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Live Load Custom Vehicle Add/Edit")
        self.setModal(True)
        self.setMinimumWidth(420)
        self.setMinimumHeight(500)
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; }
            QLabel { color: #2b2b2b; font-size: 11px; background: transparent; }
            QLineEdit { 
                background-color: #ffffff; 
                border: 1px solid #8a8a8a; 
                border-radius: 4px; 
                padding: 4px 8px; 
                min-height: 24px;
                color: #2b2b2b;
            }
            QLineEdit:focus { border: 1px solid #5a5a5a; }
            QLineEdit:read-only { background-color: #f0f0f0; color: #5a5a5a; }
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
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Vehicle Name row
        name_row = QHBoxLayout()
        name_row.setSpacing(10)
        name_label = QLabel("Vehicle Name:")
        name_label.setStyleSheet("font-weight: 600;")
        self.vehicle_name_input = QLineEdit()
        self.vehicle_name_input.setFixedWidth(120)
        name_row.addWidget(name_label)
        name_row.addWidget(self.vehicle_name_input)
        name_row.addStretch()
        layout.addLayout(name_row)

        # P# D# row with Add/Modify/Delete buttons
        pd_button_row = QHBoxLayout()
        pd_button_row.setSpacing(8)

        p_label = QLabel("P#")
        self.P_input = QLineEdit()
        self.P_input.setFixedWidth(50)
        pd_button_row.addWidget(p_label)
        pd_button_row.addWidget(self.P_input)

        d_label = QLabel("D#")
        self.D_input = QLineEdit()
        self.D_input.setFixedWidth(50)
        pd_button_row.addWidget(d_label)
        pd_button_row.addWidget(self.D_input)

        pd_button_row.addStretch()

        self.add_axle_button = QPushButton("Add")
        self.modify_axle_button = QPushButton("Modify")
        self.delete_axle_button = QPushButton("Delete")
        pd_button_row.addWidget(self.add_axle_button)
        pd_button_row.addWidget(self.modify_axle_button)
        pd_button_row.addWidget(self.delete_axle_button)

        layout.addLayout(pd_button_row)

        # Table and diagram row
        table_diagram_row = QHBoxLayout()
        table_diagram_row.setSpacing(12)

        # Axle table
        self.axle_table = QTableWidget()
        self.axle_table.setColumnCount(3)
        self.axle_table.setHorizontalHeaderLabels(["No.", "Load (kN)", "Spacing (m)"])
        self.axle_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.axle_table.verticalHeader().setVisible(False)
        self.axle_table.setMinimumHeight(120)
        self.axle_table.setMaximumHeight(140)
        table_diagram_row.addWidget(self.axle_table, 1)

        # Axle diagram placeholder
        axle_diagram = QLabel("Axle Layout Diagram")
        axle_diagram.setAlignment(Qt.AlignCenter)
        axle_diagram.setMinimumHeight(120)
        axle_diagram.setStyleSheet("""
            QLabel {
                border: 1px solid #8a8a8a;
                border-radius: 4px;
                background: #ffffff;
                color: #6a6a6a;
                font-size: 10px;
            }
        """)
        table_diagram_row.addWidget(axle_diagram, 1)

        layout.addLayout(table_diagram_row)

        # Input fields grid
        fields_grid = QGridLayout()
        fields_grid.setContentsMargins(0, 8, 0, 0)
        fields_grid.setHorizontalSpacing(12)
        fields_grid.setVerticalSpacing(10)
        fields_grid.setColumnMinimumWidth(0, 240)

        field_labels = [
            "Minimum nose to tail distance (m):",
            "Width of Wheel, w (mm):",
            "Minimum Clearance from Carriageway\nEdge, f (mm):",
            "Minimum Clearance from Crossing Vehicles,\ng (mm):",
            "Wheel Spacing in Transverse Direction (m):",
            "Impact Factor:",
        ]

        self.custom_fields = {}
        for row, text in enumerate(field_labels):
            lbl = QLabel(text)
            field = QLineEdit()
            if "Impact" in text:
                field.setText("0.25")
                field.setReadOnly(True)
            field.setFixedWidth(100)
            fields_grid.addWidget(lbl, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
            fields_grid.addWidget(field, row, 1, Qt.AlignLeft | Qt.AlignVCenter)
            self.custom_fields[text] = field

        layout.addLayout(fields_grid)

        # Bottom diagram - Clear Carriageway Width
        bottom_diagram_label = QLabel("CLEAR CARRIAGEWAY WIDTH")
        bottom_diagram_label.setAlignment(Qt.AlignCenter)
        bottom_diagram_label.setStyleSheet("font-size: 9px; font-weight: 600; color: #5a5a5a; background: transparent;")
        layout.addWidget(bottom_diagram_label)

        # Vehicle CAD Viewer
        self.bottom_viewer = VehicleViewer()
        self.bottom_viewer.setMinimumHeight(140)
        layout.addWidget(self.bottom_viewer)

        layout.addStretch()

        # Default values for preview
        self.custom_fields["Width of Wheel, w (mm):"].setText("2500")
        self.custom_fields["Minimum Clearance from Carriageway\nEdge, f (mm):"].setText("600")
        self.custom_fields["Minimum Clearance from Crossing Vehicles,\ng (mm):"].setText("1200")

        # Connect fields (static update on finish)
        self.custom_fields["Width of Wheel, w (mm):"].editingFinished.connect(self.update_vehicle_view)
        self.custom_fields["Minimum Clearance from Carriageway\nEdge, f (mm):"].editingFinished.connect(self.update_vehicle_view)
        self.custom_fields["Minimum Clearance from Crossing Vehicles,\ng (mm):"].editingFinished.connect(self.update_vehicle_view)

        # Initial draw
        self.update_vehicle_view()


    def update_vehicle_view(self):
        try:
            w = float(self.custom_fields["Width of Wheel, w (mm):"].text() or 0)
            f = float(self.custom_fields["Minimum Clearance from Carriageway\nEdge, f (mm):"].text() or 0)
            g = float(self.custom_fields["Minimum Clearance from Crossing Vehicles,\ng (mm):"].text() or 0)

            print("Updating viewer:", w, f, g)   # <-- debug line

            self.bottom_viewer.set_data(w, f, g)
        except ValueError:
            pass
