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

class TypicalSectionDetailsTab(QWidget):
    """Sub-tab for Typical Section Details inputs"""

    footpath_changed = Signal(str)

    def __init__(self, footpath_value="None", carriageway_width=7.5, parent=None):
        super().__init__(parent)
        self.footpath_value = footpath_value
        self.carriageway_width = carriageway_width
        self.updating_fields = False
        self.init_ui()

    def style_input_field(self, field):
        apply_field_style(field)

    def style_group_box(self, group_box):
        group_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #d0d0d0;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 15px;
                background-color: #f9f9f9;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 5px;
                background-color: white;
                color: #4a7ba7;
            }
        """)

    def _create_section_card(self, title):
        card = QFrame()
        card.setObjectName("sectionCard")
        card.setStyleSheet("""
            QFrame#sectionCard {
                background-color: #f5f5f5;
                border: none;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(12)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #000;")
        card_layout.addWidget(title_label)

        return card, card_layout

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)

        diagram_widget = QWidget()
        diagram_widget.setStyleSheet("""
            QWidget {
                background: transparent;
                border: 1px solid #b0b0b0;
                border-radius: 8px;
            }
        """)
        diagram_widget.setMinimumHeight(150)
        diagram_widget.setMaximumHeight(200)
        diagram_layout = QVBoxLayout(diagram_widget)
        diagram_layout.setContentsMargins(20, 20, 20, 20)
        diagram_layout.setAlignment(Qt.AlignCenter)

        diagram_label = QLabel("Typical Section Details\nDiagram")
        diagram_label.setAlignment(Qt.AlignCenter)
        diagram_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: none;
                padding: 20px;
                font-size: 13px;
                color: #333;
            }
        """)
        diagram_layout.addWidget(diagram_label)

        main_layout.addWidget(diagram_widget)
        main_layout.addSpacing(10)

        input_container = QWidget()
        input_container.setStyleSheet("QWidget { background-color: white; }")
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(0)

        self.input_tabs = QTabWidget()
        self.input_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #b0b0b0;
                border-top: none;
                background-color: #f5f5f5;
                border-radius: 0px 0px 8px 8px;
            }
            QTabBar::tab {
                background-color: #e8e8e8;
                color: #555;
                padding: 10px 20px;
                border: 1px solid #b0b0b0;
                border-bottom: none;
                border-right: none;
                font-size: 11px;
                min-width: 80px;
            }
            QTabBar::tab:last {
                border-right: 1px solid #b0b0b0;
            }
            QTabBar::tab:selected {
                background-color: #90AF13;
                color: white;
                font-weight: bold;
                border: 1px solid #90AF13;
                border-bottom: none;
            }
            QTabBar::tab:hover:!selected {
                background-color: #d0d0d0;
            }
        """)

        self.create_layout_tab()
        self.create_crash_barrier_tab()
        self.create_median_tab()
        self.create_railing_tab()
        self.create_wearing_course_tab()
        self.create_lane_details_tab()

        input_layout.addWidget(self.input_tabs)
        main_layout.addWidget(input_container)

        self.deck_thickness.textChanged.connect(self.update_footpath_thickness)
        self.recalculate_girders()

    def create_layout_tab(self):
        layout_widget = QWidget()
        layout_widget.setStyleSheet("background-color: #f5f5f5;")
        layout_layout = QVBoxLayout(layout_widget)
        layout_layout.setContentsMargins(18, 6, 18, 12)
        layout_layout.setSpacing(0)

        title_label = QLabel("Inputs:")
        title_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #000;")
        layout_layout.addWidget(title_label)
        layout_layout.addSpacing(8)

        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(10)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        grid.setContentsMargins(0, 0, 0, 0)

        def _label(text):
            lbl = QLabel(text)
            lbl.setStyleSheet("font-size: 11px; color: #000;")
            lbl.setMinimumWidth(180)
            return lbl

        self.girder_spacing = QLineEdit()
        self.girder_spacing.setValidator(QDoubleValidator(0.01, 50.0, 3))
        self.girder_spacing.setText(str(DEFAULT_GIRDER_SPACING))
        self.style_input_field(self.girder_spacing)
        self.girder_spacing.textChanged.connect(self.on_girder_spacing_changed)

        self.no_of_girders = QLineEdit()
        self.no_of_girders.setValidator(QIntValidator(2, 100))
        self.style_input_field(self.no_of_girders)
        self.no_of_girders.textChanged.connect(self.on_no_of_girders_changed)

        grid.addWidget(_label("Girder Spacing (m):"), 0, 0, Qt.AlignLeft)
        grid.addWidget(self.girder_spacing, 0, 1)
        grid.addWidget(_label("No. of Girders:"), 0, 2, Qt.AlignLeft)
        grid.addWidget(self.no_of_girders, 0, 3)

        self.deck_overhang = QLineEdit()
        self.deck_overhang.setValidator(QDoubleValidator(0.0, 10.0, 3))
        self.deck_overhang.setText(str(DEFAULT_DECK_OVERHANG))
        self.style_input_field(self.deck_overhang)
        self.deck_overhang.textChanged.connect(self.on_deck_overhang_changed)

        values_adjusted_label = QLabel("Values adjusted for:")
        values_adjusted_label.setStyleSheet("font-size: 11px; color: #5b5b5b; font-style: italic;")

        grid.addWidget(_label("Deck Overhang Width (m):"), 1, 0, Qt.AlignLeft)
        grid.addWidget(self.deck_overhang, 1, 1)
        #grid.addWidget(values_adjusted_label, 1, 2, 1, 2, Qt.AlignLeft)

        self.overall_bridge_width_display = QLineEdit()
        self.style_input_field(self.overall_bridge_width_display)
        self.overall_bridge_width_display.setReadOnly(True)
        self.overall_bridge_width_display.setEnabled(False)

        grid.addWidget(_label("Overall Bridge Width (m):"), 2, 0, Qt.AlignLeft)
        grid.addWidget(self.overall_bridge_width_display, 2, 1)

        self.deck_thickness = QLineEdit()
        self.deck_thickness.setValidator(QDoubleValidator(0.0, 500.0, 0))
        self.style_input_field(self.deck_thickness)

        self.footpath_thickness = QLineEdit()
        self.footpath_thickness.setValidator(QDoubleValidator(0.0, 500.0, 0))
        self.style_input_field(self.footpath_thickness)

        grid.addWidget(_label("Deck Thickness (mm):"), 3, 0, Qt.AlignLeft)
        grid.addWidget(self.deck_thickness, 3, 1)
        grid.addWidget(_label("Footpath Thickness (mm):"), 4, 2, Qt.AlignLeft)
        grid.addWidget(self.footpath_thickness, 4, 3)

        self.footpath_width = QLineEdit()
        self.footpath_width.setValidator(QDoubleValidator(MIN_FOOTPATH_WIDTH, 5.0, 3))
        self.footpath_width.textChanged.connect(self.on_footpath_width_changed)
        self.style_input_field(self.footpath_width)
        self.footpath_width.setText(f"{MIN_FOOTPATH_WIDTH:.2f}")

        grid.addWidget(_label("Footpath Width (m):"), 4, 0, Qt.AlignLeft)
        grid.addWidget(self.footpath_width, 4, 1)

        layout_layout.addLayout(grid)
        # CHANGED: Add stretch at bottom to push content up
        layout_layout.addStretch()
        
        self.input_tabs.addTab(layout_widget, "Layout")
    def create_crash_barrier_tab(self):
        crash_widget = QWidget()
        crash_widget.setStyleSheet("background-color: #f5f5f5;")
        crash_layout = QVBoxLayout(crash_widget)
        crash_layout.setContentsMargins(18, 6, 18, 12)
        crash_layout.setSpacing(0)

        card, card_layout = self._create_section_card("Crash Barrier Inputs:")
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(10)
        grid.setColumnStretch(1, 1)

        def add_row(row, label_text, widget):
            label = QLabel(label_text)
            label.setStyleSheet("font-size: 11px; color: #000;")
            label.setMinimumWidth(210)
            grid.addWidget(label, row, 0, Qt.AlignLeft)
            grid.addWidget(widget, row, 1)

        self.crash_barrier_type = QComboBox()
        self.crash_barrier_type.addItems(VALUES_CRASH_BARRIER_TYPE)
        self.style_input_field(self.crash_barrier_type)
        self.crash_barrier_type.currentTextChanged.connect(self.on_crash_barrier_type_changed)
        add_row(0, "Type:", self.crash_barrier_type)

        self.crash_barrier_density = QLineEdit()
        self.crash_barrier_density.setValidator(QDoubleValidator(0.0, 100.0, 2))
        self.style_input_field(self.crash_barrier_density)
        add_row(1, "Material Density (kN/m^3):", self.crash_barrier_density)

        self.crash_barrier_width = QLineEdit()
        self.crash_barrier_width.setValidator(QDoubleValidator(0.0, 2.0, 3))
        self.crash_barrier_width.setText(str(DEFAULT_CRASH_BARRIER_WIDTH))
        self.style_input_field(self.crash_barrier_width)
        self.crash_barrier_width.textChanged.connect(self.recalculate_girders)
        add_row(2, "Width (m):", self.crash_barrier_width)

        self.crash_barrier_height = QLineEdit()
        self.crash_barrier_height.setValidator(QDoubleValidator(0.0, 3.0, 3))
        self.style_input_field(self.crash_barrier_height)
        add_row(3, "Height (m):", self.crash_barrier_height)

        self.crash_barrier_area = QLineEdit()
        self.crash_barrier_area.setValidator(QDoubleValidator(0.0, 10.0, 4))
        self.style_input_field(self.crash_barrier_area)
        add_row(4, "Area (m^2):", self.crash_barrier_area)

        card_layout.addLayout(grid)
        crash_layout.addWidget(card)
        crash_layout.addStretch()
        self.input_tabs.addTab(crash_widget, "Crash Barrier")

    def create_median_tab(self):
        median_widget = QWidget()
        median_widget.setStyleSheet("background-color: #f5f5f5;")
        median_layout = QVBoxLayout(median_widget)
        median_layout.setContentsMargins(18, 6, 18, 12)
        median_layout.setSpacing(0)

        card, card_layout = self._create_section_card("Median Inputs:")
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(10)
        grid.setColumnStretch(1, 1)

        def add_row(row, label_text, widget):
            label = QLabel(label_text)
            label.setStyleSheet("font-size: 11px; color: #000;")
            label.setMinimumWidth(210)
            grid.addWidget(label, row, 0, Qt.AlignLeft)
            grid.addWidget(widget, row, 1)

        self.median_type = QComboBox()
        self.median_type.addItems(VALUES_MEDIAN_TYPE)
        self.style_input_field(self.median_type)
        add_row(0, "Type:", self.median_type)

        self.median_density = QLineEdit()
        self.median_density.setValidator(QDoubleValidator(0.0, 100.0, 2))
        self.style_input_field(self.median_density)
        add_row(1, "Material Density (kN/m^3):", self.median_density)

        self.median_width = QLineEdit()
        self.median_width.setValidator(QDoubleValidator(0.0, 3.0, 3))
        self.style_input_field(self.median_width)
        add_row(2, "Width (m):", self.median_width)

        self.median_height = QLineEdit()
        self.median_height.setValidator(QDoubleValidator(0.0, 3.0, 3))
        self.style_input_field(self.median_height)
        add_row(3, "Height (m):", self.median_height)

        self.median_area = QLineEdit()
        self.median_area.setValidator(QDoubleValidator(0.0, 10.0, 4))
        self.style_input_field(self.median_area)
        add_row(4, "Area (m^2):", self.median_area)

        card_layout.addLayout(grid)
        median_layout.addWidget(card)
        median_layout.addStretch()
        self.input_tabs.addTab(median_widget, "Median")

    def create_railing_tab(self):
        railing_widget = QWidget()
        railing_widget.setStyleSheet("background-color: #f5f5f5;")
        railing_layout = QVBoxLayout(railing_widget)
        railing_layout.setContentsMargins(18, 6, 18, 12)
        railing_layout.setSpacing(0)

        card, card_layout = self._create_section_card("Railing Inputs:")
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(10)
        grid.setColumnStretch(1, 1)

        def add_row(row, label_text, widget):
            label = QLabel(label_text)
            label.setStyleSheet("font-size: 11px; color: #000;")
            label.setMinimumWidth(180)
            grid.addWidget(label, row, 0, Qt.AlignLeft)
            grid.addWidget(widget, row, 1)

        self.railing_type = QComboBox()
        self.railing_type.addItems(VALUES_RAILING_TYPE)
        self.style_input_field(self.railing_type)
        add_row(0, "Type:", self.railing_type)

        self.railing_width = QLineEdit()
        self.railing_width.setValidator(QDoubleValidator(0.0, 2000.0, 1))
        self.railing_width.setText(f"{DEFAULT_RAILING_WIDTH * 1000:.0f}")
        self.style_input_field(self.railing_width)
        self.railing_width.textChanged.connect(self.recalculate_girders)
        add_row(1, "Width (mm):", self.railing_width)

        self.railing_height = QLineEdit()
        self.railing_height.setValidator(QDoubleValidator(MIN_RAILING_HEIGHT, 3.0, 3))
        self.style_input_field(self.railing_height)
        self.railing_height.editingFinished.connect(self.validate_railing_height)
        add_row(2, "Height (m):", self.railing_height)

        load_row = QHBoxLayout()
        load_row.setContentsMargins(0, 0, 0, 0)
        load_row.setSpacing(12)

        self.railing_load_mode = QComboBox()
        self.railing_load_mode.addItems(["Automatic (IRC 6)", "User-defined"])
        self.style_input_field(self.railing_load_mode)
        self.railing_load_mode.currentTextChanged.connect(self.on_railing_load_mode_changed)
        load_row.addWidget(self.railing_load_mode)

        self.railing_load_value = QLineEdit()
        self.railing_load_value.setValidator(QDoubleValidator(0.0, 50.0, 2))
        self.railing_load_value.setPlaceholderText("Value")
        self.railing_load_value.setEnabled(False)
        self.style_input_field(self.railing_load_value)
        load_row.addWidget(self.railing_load_value)

        load_container = QWidget()
        load_container.setLayout(load_row)
        add_row(3, "Load (kN/m):", load_container)

        card_layout.addLayout(grid)
        railing_layout.addWidget(card)
        railing_layout.addStretch()
        self.input_tabs.addTab(railing_widget, "Railing")

    def create_wearing_course_tab(self):
        wearing_widget = QWidget()
        wearing_widget.setStyleSheet("background-color: #f5f5f5;")
        wearing_layout = QVBoxLayout(wearing_widget)
        wearing_layout.setContentsMargins(18, 6, 18, 12)
        wearing_layout.setSpacing(0)

        card, card_layout = self._create_section_card("Wearing Course Inputs:")
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(10)
        grid.setColumnStretch(1, 1)

        def add_row(row, label_text, widget):
            label = QLabel(label_text)
            label.setStyleSheet("font-size: 11px; color: #000;")
            label.setMinimumWidth(200)
            grid.addWidget(label, row, 0, Qt.AlignLeft)
            grid.addWidget(widget, row, 1)

        self.wearing_material = QComboBox()
        self.wearing_material.addItems(VALUES_WEARING_COAT_MATERIAL)
        self.style_input_field(self.wearing_material)
        add_row(0, "Material:", self.wearing_material)

        self.wearing_density = QLineEdit()
        self.wearing_density.setValidator(QDoubleValidator(0.0, 40.0, 2))
        self.style_input_field(self.wearing_density)
        add_row(1, "Density (kN/m^3):", self.wearing_density)

        self.wearing_thickness = QLineEdit()
        self.wearing_thickness.setValidator(QDoubleValidator(0.0, 200.0, 1))
        self.style_input_field(self.wearing_thickness)
        add_row(2, "Thickness (mm):", self.wearing_thickness)

        card_layout.addLayout(grid)
        wearing_layout.addWidget(card)
        wearing_layout.addStretch()
        self.input_tabs.addTab(wearing_widget, "Wearing Course")

    def create_lane_details_tab(self):
        lane_widget = QWidget()
        lane_widget.setStyleSheet("background-color: #f5f5f5;")
        lane_layout = QVBoxLayout(lane_widget)
        lane_layout.setContentsMargins(18, 6, 18, 12)
        lane_layout.setSpacing(0)

        card, card_layout = self._create_section_card("Inputs:")

        selector_layout = QHBoxLayout()
        selector_layout.setContentsMargins(0, 0, 0, 0)
        selector_layout.setSpacing(12)

        lanes_label = QLabel("No. of Traffic Lanes:")
        lanes_label.setStyleSheet("font-size: 11px; color: #000;")
        selector_layout.addWidget(lanes_label)

        self.lane_count_combo = QComboBox()
        self.lane_count_combo.addItems([str(i) for i in range(1, 7)])
        self.style_input_field(self.lane_count_combo)
        self.lane_count_combo.currentTextChanged.connect(self.on_lane_count_changed)
        selector_layout.addWidget(self.lane_count_combo)
        selector_layout.addStretch()

        card_layout.addLayout(selector_layout)

        self.lane_table = QTableWidget()
        self.lane_table.setColumnCount(3)
        self.lane_table.setHorizontalHeaderLabels([
            "Traffic Lane Number",
            "Distance from inner edge of crash barrier to left edge of lane (m)",
            "Lane Width (m)"
        ])
        header = self.lane_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.lane_table.verticalHeader().setVisible(False)
        self.lane_table.setAlternatingRowColors(True)
        self.lane_table.setStyleSheet("""
            QTableWidget { 
                background-color: #ffffff;
                alternate-background-color: #f9f9f9;
                gridline-color: #e0e0e0;
                border: 1px solid #e0e0e0;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e0e0e0;
            }
            QTableWidget::item:hover {
                background-color: #e8f4f8;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                color: #333;
                padding: 8px;
                border: 1px solid #e0e0e0;
                font-weight: bold;
                font-size: 11px;
            }
        """)

        card_layout.addWidget(self.lane_table)
        lane_layout.addWidget(card)
        lane_layout.addStretch()

        self.input_tabs.addTab(lane_widget, "Lane Details")
        self._update_lane_details_rows(self.lane_count_combo.currentText())
    
    def _update_lane_details_rows(self, count):
        try:
            num_lanes = int(count)
            self.lane_table.setRowCount(num_lanes)
            
            for i in range(num_lanes):
                # Lane number (non-editable)
                lane_num_item = QTableWidgetItem(str(i + 1))
                lane_num_item.setFlags(lane_num_item.flags() & ~Qt.ItemIsEditable)
                lane_num_item.setTextAlignment(Qt.AlignCenter)
                self.lane_table.setItem(i, 0, lane_num_item)
                
                # Distance field (editable)
                if not self.lane_table.item(i, 1):
                    self.lane_table.setItem(i, 1, QTableWidgetItem(""))
                
                # Width field (editable)
                if not self.lane_table.item(i, 2):
                    self.lane_table.setItem(i, 2, QTableWidgetItem(""))
        except ValueError:
            pass

    def update_footpath_value(self, footpath_value):
        self.footpath_value = footpath_value
        if hasattr(self, "footpath_width"):
            self.footpath_width.setEnabled(footpath_value != "None")
            self.footpath_thickness.setEnabled(footpath_value != "None")
        self.recalculate_girders()
        self.footpath_changed.emit(footpath_value)

    def get_overall_bridge_width(self):
        try:
            overall_width = self.carriageway_width
            if self.footpath_value != "None":
                footpath_width = float(self.footpath_width.text()) if self.footpath_width.text() else 0
                num_footpaths = 2 if self.footpath_value == "Both" else (1 if self.footpath_value == "Single Sided" else 0)
                overall_width += footpath_width * num_footpaths

            crash_barrier_width = float(self.crash_barrier_width.text()) if self.crash_barrier_width.text() else DEFAULT_CRASH_BARRIER_WIDTH
            overall_width += crash_barrier_width * 2

            if self.footpath_value != "None":
                railing_width_text = self.railing_width.text() if hasattr(self, "railing_width") else ""
                if railing_width_text:
                    railing_width = float(railing_width_text) / 1000.0
                else:
                    railing_width = DEFAULT_RAILING_WIDTH
                overall_width += railing_width * 2

            return overall_width
        except:
            return self.carriageway_width

    def _update_overall_bridge_width_display(self):
        if hasattr(self, "overall_bridge_width_display"):
            try:
                overall_width = self.get_overall_bridge_width()
                self.overall_bridge_width_display.setText(f"{overall_width:.3f}")
            except:
                self.overall_bridge_width_display.clear()

    def recalculate_girders(self):
        if self.updating_fields:
            return
        try:
            self._update_overall_bridge_width_display()
            overall_width = self.get_overall_bridge_width()
            spacing = float(self.girder_spacing.text()) if self.girder_spacing.text() else DEFAULT_GIRDER_SPACING
            overhang = float(self.deck_overhang.text()) if self.deck_overhang.text() else DEFAULT_DECK_OVERHANG
            if spacing >= overall_width or overhang >= overall_width:
                self.no_of_girders.setText("")
                return
            if spacing > 0:
                no_girders = int(round((overall_width - 2 * overhang) / spacing)) + 1
                if no_girders >= 2:
                    self.updating_fields = True
                    self.no_of_girders.setText(str(no_girders))
                    self.updating_fields = False
        except:
            pass

    def on_girder_spacing_changed(self):
        if not self.updating_fields:
            try:
                overall_width = self.get_overall_bridge_width()
                spacing_text = self.girder_spacing.text()
                if spacing_text:
                    spacing = float(spacing_text)
                    if spacing >= overall_width:
                        QMessageBox.warning(self, "Invalid Girder Spacing",
                                             f"Girder spacing ({spacing:.2f} m) must be less than overall bridge width ({overall_width:.2f} m).")
                        return
                self.recalculate_girders()
            except:
                pass

    def on_deck_overhang_changed(self):
        if not self.updating_fields:
            try:
                overall_width = self.get_overall_bridge_width()
                overhang_text = self.deck_overhang.text()
                if overhang_text:
                    overhang = float(overhang_text)
                    if overhang >= overall_width:
                        QMessageBox.warning(self, "Invalid Deck Overhang",
                                             f"Deck overhang ({overhang:.2f} m) must be less than overall bridge width ({overall_width:.2f} m).")
                        return
                self.recalculate_girders()
            except:
                pass

    def on_no_of_girders_changed(self):
        if not self.updating_fields:
            try:
                no_girders_text = self.no_of_girders.text()
                if no_girders_text:
                    no_girders = int(no_girders_text)
                    if no_girders < 2:
                        QMessageBox.warning(self, "Invalid Number of Girders",
                                             "Number of girders must be at least 2.")
                        return
                    overall_width = self.get_overall_bridge_width()
                    overhang = float(self.deck_overhang.text()) if self.deck_overhang.text() else DEFAULT_DECK_OVERHANG
                    if no_girders > 1:
                        new_spacing = (overall_width - 2 * overhang) / (no_girders - 1)
                        self.updating_fields = True
                        self.girder_spacing.setText(f"{new_spacing:.3f}")
                        self.updating_fields = False
            except:
                pass

    def on_footpath_width_changed(self):
        if not self.updating_fields:
            self.recalculate_girders()

    def validate_footpath_width(self):
        try:
            if self.footpath_width.text():
                width = float(self.footpath_width.text())
                if width < MIN_FOOTPATH_WIDTH:
                    QMessageBox.critical(self, "Footpath Width Error",
                                         f"Footpath width must be at least {MIN_FOOTPATH_WIDTH} m as per IRC 5 Clause 104.3.6.")
        except:
            pass

    def validate_railing_height(self):
        try:
            if self.railing_height.text():
                height = float(self.railing_height.text())
                if height < MIN_RAILING_HEIGHT:
                    QMessageBox.critical(self, "Railing Height Error",
                                         f"Railing height must be at least {MIN_RAILING_HEIGHT} m as per IRC 5 Clauses 109.7.2.3 and 109.7.2.4.")
        except:
            pass

    def update_footpath_thickness(self):
        if self.deck_thickness.text() and not self.footpath_thickness.text():
            self.footpath_thickness.setText(self.deck_thickness.text())

    def on_crash_barrier_type_changed(self, barrier_type):
        if (barrier_type in ["Flexible", "Semi-Rigid"]) and (self.footpath_value == "None"):
            QMessageBox.critical(self, "Crash Barrier Type Not Permitted",
                                 f"{barrier_type} crash barriers are not permitted on bridges without an outer footpath per IRC 5 Clause 109.6.4.")

    def on_railing_load_mode_changed(self, mode):
        if not hasattr(self, "railing_load_value"):
            return
        is_auto = mode.startswith("Automatic")
        self.railing_load_value.setEnabled(not is_auto)
        if is_auto:
            self.railing_load_value.clear()

    def on_lane_count_changed(self, text):
        self._update_lane_details_rows(text)

    def _update_lane_details_rows(self, count):
        try:
            total_rows = int(count)
        except (TypeError, ValueError):
            total_rows = 1
        if not hasattr(self, "lane_table"):
            return
        self.lane_table.setRowCount(total_rows)
        for row in range(total_rows):
            lane_item = QTableWidgetItem(str(row + 1))
            lane_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.lane_table.setItem(row, 0, lane_item)
            for col in range(1, self.lane_table.columnCount()):
                existing_item = self.lane_table.item(row, col)
                if existing_item is None:
                    self.lane_table.setItem(row, col, QTableWidgetItem(""))

    def _show_placeholder_message(self, action_name):
        QMessageBox.information(self, action_name, "This action will be available in an upcoming update.")

