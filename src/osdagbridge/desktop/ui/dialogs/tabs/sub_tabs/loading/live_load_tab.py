from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QComboBox,
    QLineEdit, QPushButton, QScrollArea, QFrame, QTableWidget,
    QTableWidgetItem, QMessageBox, QDialog, QHeaderView, QStyledItemDelegate
)
from PySide6.QtGui import QPainter, QPen
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.desktop.ui.dialogs.tabs.custom_vehicle_dialog import CustomVehicleDialog
from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import LIVE_LOAD_TAB_SCHEMA

class BorderDelegate(QStyledItemDelegate):
    """Custom delegate to draw borders only between items, not after the last one"""
    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        if index.row() < index.model().rowCount() - 1:
            painter.save()
            pen = QPen(Qt.GlobalColor.lightGray)
            pen.setWidth(1)
            painter.setPen(pen)
            painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())
            painter.restore()


class LiveLoadTab(QWidget):
    """Live Load tab content extracted from LoadingTab."""

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.custom_vehicles = {}
        self.has_real_custom_vehicle = False
        self.schema = LIVE_LOAD_TAB_SCHEMA
        self._build_ui()

    def _build_ui(self):
        owner = self.owner
        schema = self.schema
        
        LABEL_MIN_WIDTH = schema.get("label_width", 220)
        FIELD_WIDTH = schema.get("field_width", 180)
        FIELD_HEIGHT = schema.get("field_height", 28)
        
        self.setStyleSheet("background-color: #f5f5f5;")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { background-color: #f5f5f5; border: none; }")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: #f5f5f5;")
        page_layout = QVBoxLayout(scroll_content)
        page_layout.setContentsMargins(12, 12, 12, 12)
        page_layout.setSpacing(12)

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(16)

        # LEFT CARD
        left_card = owner._create_card()
        left_card.setStyleSheet("QFrame { border: 1px solid #b2b2b2; border-radius: 10px; background-color: #ffffff; }")
        left_card_layout = QVBoxLayout(left_card)
        left_card_layout.setContentsMargins(0, 0, 0, 0)
        left_card_layout.setSpacing(0)

        content_wrapper = QWidget()
        content_wrapper.setStyleSheet("background-color: #ffffff;")
        left_layout = QVBoxLayout(content_wrapper)
        left_layout.setContentsMargins(14, 14, 14, 14)
        left_layout.setSpacing(12)

        title = QLabel("Live Load (LL) Inputs:")
        title.setStyleSheet("font-size: 12px; font-weight: 700; color: #3a3a3a; background: transparent; border: none;")
        left_layout.addWidget(title)

        label_style = "font-size: 11px; font-weight: 600; color: #3a3a3a; background: transparent; border: none;"

        for section in schema.get("sections", []):
            section_type = section.get("type")
            
            # IRC VEHICLES SECTION
            if section_type == "checkbox_list" and section.get("id") == "irc_vehicles_section":
                irc_box = QFrame()
                irc_box.setStyleSheet("QFrame { border: 1px solid #9c9c9c; border-radius: 6px; background-color: #ffffff; padding: 0px; }")
                irc_box_layout = QVBoxLayout(irc_box)
                irc_box_layout.setContentsMargins(12, 12, 12, 12)
                irc_box_layout.setSpacing(8)

                irc_title = QLabel(section.get("title", ""))
                irc_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #3a3a3a; background: transparent; border: none;")
                irc_box_layout.addWidget(irc_title)

                owner.irc_vehicle_checkboxes = []
                owner.irc_vehicle_labels = []
                default_checked = section.get("default_checked", False)
                
                for vehicle in section.get("items", []):
                    row = QHBoxLayout()
                    row.setSpacing(10)
                    label = QLabel(vehicle)
                    label.setStyleSheet(label_style)
                    label.setMinimumWidth(LABEL_MIN_WIDTH)
                    checkbox = QCheckBox()
                    checkbox.setChecked(default_checked)
                    checkbox.setFixedHeight(FIELD_HEIGHT)
                    row.addWidget(label)
                    row.addWidget(checkbox)
                    row.addStretch()
                    irc_box_layout.addLayout(row)
                    owner.irc_vehicle_checkboxes.append(checkbox)
                    owner.irc_vehicle_labels.append(label)

                left_layout.addWidget(irc_box)
            
            # CUSTOM VEHICLE SECTION
            elif section_type == "custom_vehicle_table" and section.get("id") == "custom_vehicle_section":
                self.custom_vehicle_box = QFrame()
                self.custom_vehicle_box.setStyleSheet("QFrame { border: 1px solid #9c9c9c; border-radius: 6px; background-color: #ffffff; padding: 0px; }")
                custom_box_layout = QVBoxLayout(self.custom_vehicle_box)
                custom_box_layout.setContentsMargins(12, 12, 12, 12)
                custom_box_layout.setSpacing(8)

                header_row = QHBoxLayout()
                header_row.setContentsMargins(0, 0, 0, 0)
                header_row.setSpacing(10)
                
                header_label = QLabel(section.get("title", ""))
                header_label.setStyleSheet("font-size: 11px; font-weight: 700; color: #3a3a3a; background: transparent; border: none;")
                header_label.setMinimumWidth(LABEL_MIN_WIDTH)
                header_row.addWidget(header_label)
                
                add_button_bind = section.get("add_button_bind")
                if add_button_bind:
                    setattr(owner, add_button_bind, QPushButton("Add"))
                    add_button = getattr(owner, add_button_bind)
                    add_button.setStyleSheet("QPushButton { background-color: white; border: 1px solid #3a3a3a; border-radius: 3px; font-size: 10px; font-weight: 600; color: #3a3a3a; padding: 3px 8px; } QPushButton:hover { background-color: #f8f8f8; }")
                    add_button.setFixedHeight(FIELD_HEIGHT)
                    header_row.addWidget(add_button)
                
                header_row.addStretch()
                custom_box_layout.addLayout(header_row)
                
                table_bind = section.get("bind")
                if table_bind:
                    setattr(self, table_bind, QTableWidget(0, 4))
                    self.custom_vehicle_table = getattr(self, table_bind)
                    
                self.custom_vehicle_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                self.custom_vehicle_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                self.custom_vehicle_table.verticalHeader().setDefaultSectionSize(FIELD_HEIGHT + 4)
                self.custom_vehicle_table.verticalHeader().setMinimumSectionSize(FIELD_HEIGHT + 4)
                self.custom_vehicle_table.horizontalHeader().setVisible(False)
                self.custom_vehicle_table.verticalHeader().setVisible(False)
                self.custom_vehicle_table.setEditTriggers(QTableWidget.NoEditTriggers)
                self.custom_vehicle_table.setSelectionMode(QTableWidget.NoSelection)
                self.custom_vehicle_table.setShowGrid(False)
                self.custom_vehicle_table.setFrameShape(QFrame.NoFrame)
                self.custom_vehicle_table.setContentsMargins(0, 0, 0, 0)

                header = self.custom_vehicle_table.horizontalHeader()
                header.setSectionResizeMode(0, QHeaderView.Fixed)
                header.setSectionResizeMode(1, QHeaderView.Fixed)
                header.setSectionResizeMode(2, QHeaderView.Fixed)
                header.setSectionResizeMode(3, QHeaderView.Fixed)
                self.custom_vehicle_table.setColumnWidth(0, LABEL_MIN_WIDTH + 10)
                self.custom_vehicle_table.setColumnWidth(1, 30)
                self.custom_vehicle_table.setColumnWidth(2, 60)
                self.custom_vehicle_table.setColumnWidth(3, 70)

                self.custom_vehicle_table.setStyleSheet("QTableWidget { border: none; background-color: transparent; margin-top: 4px; } QTableWidget::item { padding: 2px 0px; border: none; color: #3a3a3a; font-size: 11px; }")

                custom_box_layout.addWidget(self.custom_vehicle_table)
                left_layout.addWidget(self.custom_vehicle_box)
                self._update_custom_vehicle_box_height()

        remaining_box = QFrame()
        remaining_box.setStyleSheet("QFrame { border: 1px solid #9c9c9c; border-radius: 6px; background-color: #ffffff; padding: 0px; }")
        self.remaining_box_layout = QVBoxLayout(remaining_box)
        self.remaining_box_layout.setContentsMargins(12, 12, 12, 12)
        self.remaining_box_layout.setSpacing(8)

        braking_section = next((s for s in schema.get("sections", []) if s.get("id") == "braking_section"), None)
        if braking_section:
            self.braking_section_label = QLabel(braking_section.get("title", ""))
            self.braking_section_label.setStyleSheet("font-size: 11px; font-weight: 700; color: #3a3a3a; background: transparent; border: none;")
            self.remaining_box_layout.addWidget(self.braking_section_label)
            
            self.braking_checkboxes_container = QWidget()
            self.braking_checkboxes_layout = QVBoxLayout(self.braking_checkboxes_container)
            self.braking_checkboxes_layout.setContentsMargins(0, 0, 0, 0)
            self.braking_checkboxes_layout.setSpacing(8)
            self.remaining_box_layout.addWidget(self.braking_checkboxes_container)
            self._update_braking_vehicles_section()

        ecc_section = next((s for s in schema.get("sections", []) if s.get("id") == "eccentricity"), None)
        if ecc_section:
            ecc_row = QHBoxLayout()
            ecc_row.setSpacing(10)
            ecc_label = QLabel(ecc_section.get("label", ""))
            ecc_label.setStyleSheet(label_style)
            ecc_label.setMinimumWidth(LABEL_MIN_WIDTH)
            
            bind_name = ecc_section.get("bind")
            if bind_name:
                setattr(owner, bind_name, QLineEdit())
                ecc_input = getattr(owner, bind_name)
                ecc_input.setFixedSize(FIELD_WIDTH, FIELD_HEIGHT)
                ecc_input.setText(ecc_section.get("default", ""))
                apply_field_style(ecc_input)
                
            ecc_row.addWidget(ecc_label)
            ecc_row.addWidget(ecc_input)
            ecc_row.addStretch()
            self.remaining_box_layout.addLayout(ecc_row)

        footpath_section = next((s for s in schema.get("sections", []) if s.get("id") == "footpath_pressure"), None)
        if footpath_section:
            footpath_row = QHBoxLayout()
            footpath_row.setSpacing(10)
            footpath_label = QLabel(footpath_section.get("label", ""))
            footpath_label.setStyleSheet(label_style)
            footpath_label.setMinimumWidth(LABEL_MIN_WIDTH)

            mode_bind = footpath_section.get("bind_mode")
            if mode_bind:
                setattr(owner, mode_bind, QComboBox())
                mode_combo = getattr(owner, mode_bind)
                mode_combo.addItems(footpath_section.get("mode_choices", []))
                mode_combo.setCurrentText(footpath_section.get("default_mode", ""))
                mode_combo.setFixedSize(footpath_section.get("mode_width", 120), FIELD_HEIGHT)
                apply_field_style(mode_combo)

            value_bind = footpath_section.get("bind_value")
            if value_bind:
                setattr(owner, value_bind, QLineEdit())
                value_input = getattr(owner, value_bind)
                value_input.setFixedSize(footpath_section.get("value_width", 80), FIELD_HEIGHT)
                value_input.setText(footpath_section.get("default_value", ""))
                apply_field_style(value_input)

            footpath_row.addWidget(footpath_label)
            footpath_row.addWidget(mode_combo)
            footpath_row.addWidget(value_input)
            footpath_row.addStretch()
            self.remaining_box_layout.addLayout(footpath_row)

        left_layout.addWidget(remaining_box)
        left_layout.addStretch()
        left_card_layout.addWidget(content_wrapper)

        right_card = owner._create_card()
        right_card.setStyleSheet("QFrame { border: 1px solid #9c9c9c; border-radius: 10px; background-color: #d4d4d4; }")
        right_card.setMinimumWidth(260)
        right_card.setMinimumHeight(420)
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(10)

        description = schema.get("description", {})
        desc_label = QLabel(description.get("title", ""))
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("font-size: 12px; font-weight: 700; color: #000000; background: transparent; border: none;")
        right_layout.addWidget(desc_label)

        description_label = QLabel(description.get("text", ""))
        description_label.setWordWrap(True)
        description_label.setStyleSheet("font-size: 11px; color: #4b4b4b; background: transparent; border: none;")
        right_layout.addWidget(description_label)
        right_layout.addStretch()

        content_row.addWidget(left_card, 3)
        content_row.addWidget(right_card, 2)
        page_layout.addLayout(content_row)

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        owner.custom_vehicle_add_button.clicked.connect(self.show_custom_vehicle_dialog)
        
        footpath_section = next((s for s in schema.get("sections", []) if s.get("id") == "footpath_pressure"), None)
        if footpath_section:
            on_mode_change = footpath_section.get("on_mode_change")
            if on_mode_change and hasattr(owner, on_mode_change):
                owner.footpath_mode_combo.currentTextChanged.connect(getattr(owner, on_mode_change))
                getattr(owner, on_mode_change)(owner.footpath_mode_combo.currentText())

    def _update_braking_vehicles_section(self):
        """Update the braking vehicles checkbox section with IRC + custom vehicles"""
        while self.braking_checkboxes_layout.count():
            item = self.braking_checkboxes_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub_item = item.layout().takeAt(0)
                    if sub_item.widget():
                        sub_item.widget().deleteLater()
        
        irc_section = next((s for s in self.schema.get("sections", []) if s.get("id") == "irc_vehicles_section"), None)
        irc_vehicles = irc_section.get("items", []) if irc_section else []
        custom_vehicle_names = list(self.custom_vehicles.keys()) if self.has_real_custom_vehicle else []
        all_braking_vehicles = irc_vehicles + custom_vehicle_names
        
        self.owner.braking_vehicle_checkboxes = []
        self.owner.braking_vehicle_labels = []
        label_style = "font-size: 11px; font-weight: 600; color: #3a3a3a; background: transparent; border: none;"
        LABEL_MIN_WIDTH = self.schema.get("label_width", 220)
        FIELD_HEIGHT = self.schema.get("field_height", 28)
        braking_section = next((s for s in self.schema.get("sections", []) if s.get("id") == "braking_section"), None)
        default_checked = braking_section.get("default_checked", True) if braking_section else True
        
        for vehicle in all_braking_vehicles:
            row = QHBoxLayout()
            row.setSpacing(10)
            label = QLabel(vehicle)
            label.setStyleSheet(label_style)
            label.setMinimumWidth(LABEL_MIN_WIDTH)
            checkbox = QCheckBox()
            checkbox.setChecked(default_checked)
            checkbox.setFixedHeight(FIELD_HEIGHT)
            row.addWidget(label)
            row.addWidget(checkbox)
            row.addStretch()
            self.braking_checkboxes_layout.addLayout(row)
            self.owner.braking_vehicle_checkboxes.append(checkbox)
            self.owner.braking_vehicle_labels.append(label)


    def show_custom_vehicle_dialog(self):
        dialog = CustomVehicleDialog(self)
        if dialog.exec() == QDialog.Accepted:
            vehicle_data = dialog.vehicle_data
            self._add_custom_vehicle(vehicle_data)

    def _add_custom_vehicle(self, vehicle_data):
        if not self.has_real_custom_vehicle:
            self.custom_vehicle_table.setRowCount(0)
            self.custom_vehicles.clear()
            self.has_real_custom_vehicle = True

        name = vehicle_data["name"]
        if name in self.custom_vehicles:
            QMessageBox.warning(self, "Duplicate Vehicle", f"Custom vehicle '{name}' already exists.")
            return

        self.custom_vehicles[name] = vehicle_data
        row = self.custom_vehicle_table.rowCount()
        self.custom_vehicle_table.insertRow(row)
        FIELD_HEIGHT = self.schema.get("field_height", 28)

        name_item = QTableWidgetItem(name)
        name_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        name_item.setFlags(Qt.ItemIsEnabled)
        self.custom_vehicle_table.setItem(row, 0, name_item)

        checkbox = QCheckBox()
        checkbox.setChecked(True)
        checkbox_container = QWidget()
        checkbox_layout = QHBoxLayout(checkbox_container)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        checkbox_layout.setSpacing(0)
        checkbox_layout.addWidget(checkbox, 0, Qt.AlignVCenter)
        checkbox_layout.addStretch()
        self.custom_vehicle_table.setCellWidget(row, 1, checkbox_container)

        edit_btn = QPushButton("Edit")
        edit_btn.setFixedSize(48, FIELD_HEIGHT)
        edit_btn.setStyleSheet("QPushButton { background-color: white; border: 1px solid #3a3a3a; border-radius: 3px; font-size: 10px; font-weight: 600; color: #3a3a3a; padding: 0px; } QPushButton:hover { background-color: #f8f8f8; }")
        edit_btn.clicked.connect(lambda _, n=name: self._edit_custom_vehicle(n))
        edit_container = QWidget()
        edit_layout = QHBoxLayout(edit_container)
        edit_layout.setContentsMargins(0, 0, 0, 0)
        edit_layout.setSpacing(0)
        edit_layout.addWidget(edit_btn, 0, Qt.AlignVCenter)
        edit_layout.addStretch()
        self.custom_vehicle_table.setCellWidget(row, 2, edit_container)

        delete_btn = QPushButton("Delete")
        delete_btn.setFixedSize(60, FIELD_HEIGHT)
        delete_btn.setStyleSheet("QPushButton { background-color: white; border: 1px solid #3a3a3a; border-radius: 3px; font-size: 10px; font-weight: 600; color: #3a3a3a; padding: 0px; } QPushButton:hover { background-color: #f8f8f8; }")
        delete_btn.clicked.connect(lambda _, n=name: self._delete_custom_vehicle(n))
        delete_container = QWidget()
        delete_layout = QHBoxLayout(delete_container)
        delete_layout.setContentsMargins(0, 0, 0, 0)
        delete_layout.setSpacing(0)
        delete_layout.addWidget(delete_btn, 0, Qt.AlignVCenter)
        delete_layout.addStretch()
        self.custom_vehicle_table.setCellWidget(row, 3, delete_container)

        self.custom_vehicle_table.setRowHeight(row, FIELD_HEIGHT + 4)
        self._update_custom_vehicle_table_height()
        self._update_custom_vehicle_box_height()
        self._update_braking_vehicles_section()

    def _update_row_borders(self):
        """Force table to repaint with updated borders"""
        self.custom_vehicle_table.viewport().update()

    def _edit_custom_vehicle(self, name):
        vehicle_data = self.custom_vehicles[name]
        dialog = CustomVehicleDialog(self)
        dialog.load_vehicle_data(vehicle_data)

        if dialog.exec() == QDialog.Accepted:
            new_data = dialog.vehicle_data
            new_name = new_data["name"]

            if new_name != name:
                if new_name in self.custom_vehicles:
                    QMessageBox.warning(self, "Duplicate Vehicle", f"Custom vehicle '{new_name}' already exists.")
                    return

                self.custom_vehicles.pop(name)
                self.custom_vehicles[new_name] = new_data

                for row in range(self.custom_vehicle_table.rowCount()):
                    item = self.custom_vehicle_table.item(row, 0)
                    if item and item.text() == name:
                        item.setText(new_name)
                        break
                
                self._update_braking_vehicles_section()
            else:
                self.custom_vehicles[name] = new_data

    def _delete_custom_vehicle(self, name):
        msg = QMessageBox(self)
        msg.setWindowTitle("Delete Vehicle")
        msg.setText(f"Delete custom vehicle '{name}'?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setStyleSheet("QLabel { color: black; font-size: 12px; } QPushButton { min-width: 70px; font-size: 11px; }")
        reply = msg.exec()

        if reply == QMessageBox.Yes:
            self.custom_vehicles.pop(name, None)
            
            for row in range(self.custom_vehicle_table.rowCount()):
                item = self.custom_vehicle_table.item(row, 0)
                if item and item.text() == name:
                    self.custom_vehicle_table.removeRow(row)
                    break

            if self.custom_vehicle_table.rowCount() == 0:
                self.has_real_custom_vehicle = False
            else:
                self._update_row_borders()

            self._update_custom_vehicle_table_height()
            self._update_custom_vehicle_box_height()
            self._update_braking_vehicles_section()

    def reset_defaults(self):
        """Reset Live Load inputs to schema default values"""
        irc_section = next((s for s in self.schema.get("sections", []) if s.get("id") == "irc_vehicles_section"), None)
        if irc_section:
            default_checked = irc_section.get("default_checked", True)
            for checkbox in self.owner.irc_vehicle_checkboxes:
                checkbox.setChecked(default_checked)

        ecc_section = next((s for s in self.schema.get("sections", []) if s.get("id") == "eccentricity"), None)
        if ecc_section:
            self.owner.eccentricity_input.setText(ecc_section.get("default", ""))

        footpath_section = next((s for s in self.schema.get("sections", []) if s.get("id") == "footpath_pressure"), None)
        if footpath_section:
            self.owner.footpath_mode_combo.setCurrentText(footpath_section.get("default_mode", ""))
            self.owner.footpath_value_input.setText(footpath_section.get("default_value", ""))
            self.owner.footpath_value_input.setDisabled(True)

        self.custom_vehicle_table.setRowCount(0)
        self.custom_vehicles.clear()
        self.has_real_custom_vehicle = False
        self._update_custom_vehicle_table_height()
        self._update_custom_vehicle_box_height()
        self._update_braking_vehicles_section()
        
        braking_section = next((s for s in self.schema.get("sections", []) if s.get("id") == "braking_section"), None)
        if braking_section:
            default_checked = braking_section.get("default_checked", True)
            for checkbox in self.owner.braking_vehicle_checkboxes:
                checkbox.setChecked(default_checked)

    def _update_custom_vehicle_table_height(self):
        rows = self.custom_vehicle_table.rowCount()
        if rows == 0:
            self.custom_vehicle_table.setFixedHeight(0)
            return

        total_height = 0
        for row in range(rows):
            total_height += self.custom_vehicle_table.rowHeight(row)
        total_height += 4
        total_height = min(total_height, 150)
        self.custom_vehicle_table.setFixedHeight(total_height)
    
    def _update_custom_vehicle_box_height(self):
        """Update the custom vehicle box height based on content"""
        rows = self.custom_vehicle_table.rowCount()
        FIELD_HEIGHT = self.schema.get("field_height", 28)
        base_height = FIELD_HEIGHT + 24 + 8
        
        if rows == 0:
            self.custom_vehicle_box.setFixedHeight(base_height)
        else:
            table_height = self.custom_vehicle_table.height()
            total_height = base_height + table_height
            self.custom_vehicle_box.setFixedHeight(total_height)