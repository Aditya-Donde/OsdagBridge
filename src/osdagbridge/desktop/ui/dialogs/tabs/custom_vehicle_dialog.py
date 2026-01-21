"""Auto-generated tab module extracted from additional_inputs."""
import sys
import os
from PySide6.QtCore import Signal

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTabBar, QLabel, QLineEdit,
    QComboBox, QGroupBox, QFormLayout, QPushButton, QScrollArea,
    QCheckBox, QMessageBox, QSizePolicy, QSpacerItem, QStackedWidget,
    QFrame, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QDialog, QSizeGrip
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QDoubleValidator, QIntValidator

from osdagbridge.core.utils.common import *
from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style

class CustomVehicleDialog(QDialog):
    """Dialog for adding or editing custom live load vehicles"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Live Load Custom Vehicle Add/Edit")
        self.setModal(True)
        self.setFixedSize(600, 740)

        self.setStyleSheet("""
            QDialog { 
                background-color: #ffffff; 
            }

            QLabel {
                color: #2b2b2b;
                font-size: 11px;
                background: transparent;
            }

            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #8a8a8a;
                border-radius: 5px;
                padding: 5px 8px;
                min-height: 24px;
                color: #2b2b2b;
                font-size: 11px;
            }

            QLineEdit:focus { 
                border: 1px solid #5a5a5a; 
            }
            
            QLineEdit:read-only { 
                background-color: #f0f0f0; 
                color: #5a5a5a; 
            }

            QPushButton {
                background-color: #ffffff;
                color: #2b2b2b;
                border: 1px solid #8a8a8a;
                border-radius: 5px;
                padding: 4px 11px;
                min-width: 70px;
                min-height: 28px;
                font-size: 11px;
            }

            QPushButton:hover { 
                background-color: #e8e8e8; 
            }
            
            QCheckBox:hover {
                background-color: transparent;
            }
            
            QPushButton:pressed { 
                background-color: #d8d8d8; 
            }

            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #8a8a8a;
                gridline-color: #d0d0d0;
                color: #2b2b2b;
                font-size: 11px;
            }

            QTableWidget::item { 
                padding: 4px; 
            }

            QTableWidget::item:hover {
                background-color: transparent;
            }

            QTableWidget::item:selected {
                background-color: transparent;
                color: #2b2b2b;
            }

            QHeaderView::section {
                background-color: #f2f2f2;
                border: 1px solid #d0d0d0;
                padding: 5px;
                font-weight: 600;
                color: #2b2b2b;
                font-size: 11px;
            }

            QCheckBox {
                spacing: 0px;
            }

            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """)

        self.init_ui()
        
        self.add_axle_button.clicked.connect(self.on_add_axle)
        self.modify_axle_button.clicked.connect(self.on_modify_axle)
        self.delete_axle_button.clicked.connect(self.on_delete_axle)
        self.save_button.clicked.connect(self.on_save)


    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        name_row = QHBoxLayout()
        name_row.setSpacing(10)

        name_label = QLabel("Vehicle Name:")
        name_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        name_row.addWidget(name_label)
        
        self.vehicle_name_input = QLineEdit()
        self.vehicle_name_input.setFixedHeight(28)
        self.vehicle_name_input.setFixedWidth(210)
        name_row.addWidget(self.vehicle_name_input)
        name_row.addStretch()

        layout.addLayout(name_row)
        layout.addSpacing(4)

        pd_row = QHBoxLayout()
        pd_row.setSpacing(10)

        p_label = QLabel("P#")
        p_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        pd_row.addWidget(p_label)
        
        self.P_input = QLineEdit()
        self.P_input.setFixedWidth(70)
        self.P_input.setFixedHeight(28)
        self.P_input.setPlaceholderText("Load")
        pd_row.addWidget(self.P_input)

        pd_row.addSpacing(15)

        d_label = QLabel("D#")
        d_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        pd_row.addWidget(d_label)
        
        self.D_input = QLineEdit()
        self.D_input.setFixedWidth(70)
        self.D_input.setFixedHeight(28)
        self.D_input.setPlaceholderText("Spacing")
        pd_row.addWidget(self.D_input)

        pd_row.addStretch()

        self.add_axle_button = QPushButton("Add")
        self.add_axle_button.setFixedWidth(66)
        self.add_axle_button.setFixedHeight(24)
        
        self.modify_axle_button = QPushButton("Modify")
        self.modify_axle_button.setFixedWidth(66)
        self.modify_axle_button.setFixedHeight(24)
        
        self.delete_axle_button = QPushButton("Delete")
        self.delete_axle_button.setFixedWidth(66)
        self.delete_axle_button.setFixedHeight(24)

        pd_row.addWidget(self.add_axle_button)
        pd_row.addWidget(self.modify_axle_button)
        pd_row.addWidget(self.delete_axle_button)

        layout.addLayout(pd_row)
        layout.addSpacing(8)

        table_diagram_row = QHBoxLayout()
        table_diagram_row.setSpacing(12)

        self.axle_table = QTableWidget(0, 4)
        self.axle_table.setHorizontalHeaderLabels(["", "No.", "Load (kN)", "Spacing (m)"])
        
        for i in range(self.axle_table.columnCount()):
            item = self.axle_table.horizontalHeaderItem(i)
            if item:
                item.setTextAlignment(Qt.AlignCenter)

        self.axle_table.setColumnWidth(0, 30) 
        self.axle_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.axle_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.axle_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        
        self.axle_table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.axle_table.verticalHeader().setVisible(False)
        self.axle_table.setAlternatingRowColors(True)
        self.axle_table.setFixedHeight(140)
        self.axle_table.setFixedWidth(290) 

        self.axle_table.cellClicked.connect(self.on_table_cell_clicked)

        table_diagram_row.addWidget(self.axle_table)
        diagram_container = QVBoxLayout()
        diagram_container.setSpacing(4)
        diagram_container.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        
        diagram_label = QLabel("Axle Layout Diagram")
        diagram_label.setAlignment(Qt.AlignCenter)
        diagram_label.setStyleSheet("font-size: 10px; font-weight: normal; color: #5a5a5a; background: transparent; border: none;")
        diagram_container.addWidget(diagram_label)

        axle_diagram = QLabel()
        axle_diagram.setAlignment(Qt.AlignCenter)
        axle_diagram.setFixedHeight(120)
        axle_diagram.setMinimumWidth(250)
        axle_diagram.setStyleSheet("""
            QLabel {
                border: 1px solid #8a8a8a;
                border-radius: 3px;
                background: #ffffff;
            }
        """)
        diagram_container.addWidget(axle_diagram)

        table_diagram_row.addLayout(diagram_container)
        
        layout.addLayout(table_diagram_row)
       
        grid_container = QWidget()
        grid_container.setStyleSheet("background: transparent;")
        
        grid_layout = QGridLayout(grid_container)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setHorizontalSpacing(10)
        grid_layout.setVerticalSpacing(10)

        grid_layout.setColumnMinimumWidth(0, 260)
        grid_layout.setColumnStretch(0, 0)
        grid_layout.setColumnStretch(1, 1)


        self.custom_fields = {}

        field_data = [
            ("Minimum nose to tail distance (m):", "30", False),
            ("Width of Wheel, w (mm):", "500", False),
            ("Minimum Clearance from Carriageway Edge, f (mm):", "150", False),
            ("Minimum Clearance from Crossing Vehicles, g (mm):", "1200", False),
            ("Wheel Spacing in Transverse Direction (m):", "1.8", False),
            ("Impact Factor:", "0.25", False),
        ]

        for row, (label_text, default, readonly) in enumerate(field_data):
            label = QLabel(label_text)
            label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            
            field = QLineEdit()
            field.setFixedWidth(240)
            field.setFixedHeight(28)
            

            if default is not None:
                field.setText(default)
            if readonly:
                field.setReadOnly(True)
            
            grid_layout.addWidget(label, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
            grid_layout.addWidget(field, row, 1, Qt.AlignLeft | Qt.AlignVCenter)
            
            self.custom_fields[label_text] = field

        layout.addWidget(grid_container)
        layout.addSpacing(8)

        bottom_diagram = QLabel()
        bottom_diagram.setFixedHeight(90)
        bottom_diagram.setStyleSheet("""
            QLabel {
                border: 1px solid #8a8a8a;
                border-radius: 3px;
                background: #ffffff;
            }
        """)
        layout.addWidget(bottom_diagram)

        layout.addSpacing(6)

        button_row = QHBoxLayout()
        button_row.setSpacing(12)
        button_row.addStretch()
        
        self.save_button = QPushButton("Save")
        self.save_button.setFixedWidth(110)
        self.save_button.setFixedHeight(32)
        button_row.addWidget(self.save_button)
        
        button_row.addStretch()
        
        layout.addLayout(button_row)
        layout.addSpacing(4)

    def on_checkbox_clicked(self, row):
        """Handle checkbox click - uncheck others and load data"""
        for r in range(self.axle_table.rowCount()):
            if r != row:
                checkbox_widget = self.axle_table.cellWidget(r, 0)
                if checkbox_widget:
                    checkbox = checkbox_widget.findChild(QCheckBox)
                    if checkbox:
                        checkbox.setChecked(False)
        
        load_item = self.axle_table.item(row, 2)
        spacing_item = self.axle_table.item(row, 3)
        
        if load_item:
            self.P_input.setText(load_item.text())
        if spacing_item:
            self.D_input.setText(spacing_item.text())

    def on_table_cell_clicked(self, row, column):
        """Load the selected row's data into P# and D# input fields"""
        for r in range(self.axle_table.rowCount()):
            checkbox_widget = self.axle_table.cellWidget(r, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(False)
        
        checkbox_widget = self.axle_table.cellWidget(row, 0)
        if checkbox_widget:
            checkbox = checkbox_widget.findChild(QCheckBox)
            if checkbox:
                checkbox.setChecked(True)
        
        load_item = self.axle_table.item(row, 2)
        spacing_item = self.axle_table.item(row, 3)
        
        if load_item:
            self.P_input.setText(load_item.text())
        if spacing_item:
            self.D_input.setText(spacing_item.text())

    def on_add_axle(self):
        """Add a new axle to the table"""
        load = self.P_input.text().strip()
        spacing = self.D_input.text().strip()

        if not load:
            QMessageBox.warning(self, "Input Error", "Please enter a Load value (P#).")
            return

        row_count = self.axle_table.rowCount()
        axle_no = row_count + 1

        self.axle_table.insertRow(row_count)

        checkbox_widget = QWidget()
        checkbox_layout = QHBoxLayout(checkbox_widget)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        checkbox_layout.setAlignment(Qt.AlignCenter)
        checkbox = QCheckBox()
        checkbox.clicked.connect(lambda checked, r=row_count: self.on_checkbox_clicked(r))
        checkbox_layout.addWidget(checkbox)
        self.axle_table.setCellWidget(row_count, 0, checkbox_widget)

        no_item = QTableWidgetItem(str(axle_no))
        no_item.setTextAlignment(Qt.AlignCenter)
        self.axle_table.setItem(row_count, 1, no_item)

        load_item = QTableWidgetItem(load)
        load_item.setTextAlignment(Qt.AlignCenter)
        self.axle_table.setItem(row_count, 2, load_item)

        spacing_item = QTableWidgetItem(spacing if spacing else "0")
        spacing_item.setTextAlignment(Qt.AlignCenter)
        self.axle_table.setItem(row_count, 3, spacing_item)

        self.P_input.clear()
        self.D_input.clear()

    def on_modify_axle(self):
        """Modify the selected axle in the table"""
        selected_row = -1
        for row in range(self.axle_table.rowCount()):
            checkbox_widget = self.axle_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    selected_row = row
                    break
        
        if selected_row < 0:
            QMessageBox.warning(self, "Selection Error", "Please select a row (check the checkbox) to modify.")
            return
        
        load = self.P_input.text().strip()
        spacing = self.D_input.text().strip()

        if not load:
            QMessageBox.warning(self, "Input Error", "Please enter a Load value (P#).")
            return

        load_item = QTableWidgetItem(load)
        load_item.setTextAlignment(Qt.AlignCenter)
        self.axle_table.setItem(selected_row, 2, load_item)

        spacing_item = QTableWidgetItem(spacing if spacing else "0")
        spacing_item.setTextAlignment(Qt.AlignCenter)
        self.axle_table.setItem(selected_row, 3, spacing_item)

        self.P_input.clear()
        self.D_input.clear()

    def on_delete_axle(self):
        """Delete the selected axle from the table"""
        selected_row = -1
        for row in range(self.axle_table.rowCount()):
            checkbox_widget = self.axle_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    selected_row = row
                    break
        
        if selected_row < 0:
            QMessageBox.warning(self, "Selection Error", "Please select a row (check the checkbox) to delete.")
            return

        reply = QMessageBox.question(
            self, 
            "Confirm Delete", 
            f"Are you sure you want to delete Axle No. {selected_row + 1}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.axle_table.removeRow(selected_row)
            
            for row in range(self.axle_table.rowCount()):
                no_item = QTableWidgetItem(str(row + 1))
                no_item.setTextAlignment(Qt.AlignCenter)
                self.axle_table.setItem(row, 1, no_item)

    def on_save(self):
        vehicle_name = self.vehicle_name_input.text().strip()

        if not vehicle_name:
            QMessageBox.warning(self, "Input Error", "Please enter a Vehicle Name.")
            return

        if self.axle_table.rowCount() == 0:
            QMessageBox.warning(self, "Input Error", "Please add at least one axle.")
            return

        self.vehicle_data = {
            "name": vehicle_name,
            "axles": self.get_axle_data(),
            "parameters": self.get_vehicle_parameters()
        }

        self.accept()

    def get_axle_data(self):
        axles = []
        for row in range(self.axle_table.rowCount()):
            axles.append({
                "no": self.axle_table.item(row, 1).text() if self.axle_table.item(row, 1) else "",
                "load": self.axle_table.item(row, 2).text() if self.axle_table.item(row, 2) else "",
                "spacing": self.axle_table.item(row, 3).text() if self.axle_table.item(row, 3) else "",
            })
        return axles

    def get_vehicle_parameters(self):
        return {label: field.text() for label, field in self.custom_fields.items()}

    def load_vehicle_data(self, vehicle_data):
        """Load existing vehicle data into the dialog (EDIT mode)"""

        # Set vehicle name
        self.vehicle_name_input.setText(vehicle_data.get("name", ""))

        # Load axles
        self.axle_table.setRowCount(0)

        for axle in vehicle_data.get("axles", []):
            row = self.axle_table.rowCount()
            self.axle_table.insertRow(row)

            # Checkbox
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            checkbox = QCheckBox()
            checkbox_layout.addWidget(checkbox)
            self.axle_table.setCellWidget(row, 0, checkbox_widget)

            # Axle No
            no_item = QTableWidgetItem(axle.get("no", str(row + 1)))
            no_item.setTextAlignment(Qt.AlignCenter)
            self.axle_table.setItem(row, 1, no_item)

            # Load (P)
            load_item = QTableWidgetItem(axle.get("load", ""))
            load_item.setTextAlignment(Qt.AlignCenter)
            self.axle_table.setItem(row, 2, load_item)

            # Spacing (D)
            spacing_item = QTableWidgetItem(axle.get("spacing", ""))
            spacing_item.setTextAlignment(Qt.AlignCenter)
            self.axle_table.setItem(row, 3, spacing_item)

        # Load vehicle parameters
        for label, field in self.custom_fields.items():
            field.setText(vehicle_data.get("parameters", {}).get(label, ""))