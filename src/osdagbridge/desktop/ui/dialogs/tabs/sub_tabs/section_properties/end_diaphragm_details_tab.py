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

class EndDiaphragmDetailsTab(QWidget):
    """Tab for End Diaphragm Details with type-specific layouts"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
            "QScrollArea > QWidget > QWidget { background: transparent; }"
        )
        main_layout.addWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(8)

        self.type_stack = QStackedWidget()
        container_layout.addWidget(self.type_stack)

        self.views = {}
        self.view_order = []
        self.type_selector_map = {}
        self.type_selectors = []
        self.current_type = None
        self.block_type_sync = False

        cross_view, cross_selector = self._build_cross_bracing_view()
        self._add_type_view("Cross Bracing", cross_view, cross_selector)
        rolled_view, rolled_selector = self._build_rolled_view()
        self._add_type_view("Rolled Beam", rolled_view, rolled_selector)
        welded_view, welded_selector = self._build_welded_view()
        self._add_type_view("Welded Beam", welded_view, welded_selector)

        self._set_current_type("Cross Bracing")

    def _add_type_view(self, key, widget, type_selector):
        self.views[key] = widget
        self.view_order.append(key)
        self.type_stack.addWidget(widget)
        self.type_selector_map[key] = type_selector
        self.type_selectors.append(type_selector)
        type_selector.currentTextChanged.connect(self._handle_type_selection)

    # ---- Shared helpers ----
    def _create_card_frame(self):
        card = QFrame()
        card.setStyleSheet("QFrame { border: 1px solid #d0d0d0; border-radius: 12px; background-color: #ffffff; }")
        return card

    def _create_inner_box(self):
        box = QFrame()
        box.setStyleSheet(
            "QFrame { border: 1px solid #cfcfcf; border-radius: 8px; background-color: #ffffff; padding: 0px; margin: 0px; }"
            "QFrame QComboBox, QFrame QLineEdit { border: none; border-bottom: 1px solid #d0d0d0; border-radius: 0px; min-height: 28px; padding: 4px 8px; background-color: #ffffff; }"
            "QFrame QComboBox:hover, QFrame QLineEdit:hover { border-bottom: 1px solid #5d5d5d; }"
            "QFrame QComboBox:focus, QFrame QLineEdit:focus { border-bottom: 1px solid #90AF13; }"
            "QFrame QLabel { border: none; padding: 0px; margin: 0px; }"
        )
        return box

    def _create_heading_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("font-size: 12px; font-weight: 600; color: #4b4b4b; border: none; padding: 0px; margin: 0px;")
        return label

    def _create_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("font-size: 11px; color: #4b4b4b; border: none;")
        return label

    def _add_grid_row(self, layout, row, text, widget):
        label = self._create_label(text)
        layout.addWidget(label, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(widget, row, 1)
        return row + 1

    def _create_image_placeholder(self, text, min_height=140):
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setMinimumHeight(min_height)
        label.setStyleSheet("QLabel { border: 1px solid #d0d0d0; border-radius: 10px; background-color: #f7f7f7; font-weight: bold; color: #5b5b5b; }")
        return label

    def _create_line_edit(self, placeholder=""):
        line_edit = QLineEdit()
        if placeholder:
            line_edit.setPlaceholderText(placeholder)
        apply_field_style(line_edit)
        return line_edit

    def _create_selection_box(self):
        box = self._create_inner_box()
        box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout = QGridLayout(box)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(8)
        layout.setColumnMinimumWidth(0, 120)
        layout.setColumnStretch(1, 1)

        girders_combo = QComboBox()
        girders_combo.addItems(["G1 to G2", "G3 to G4", "All"])
        apply_field_style(girders_combo)
        layout.addWidget(self._create_label("Select Girders:"), 0, 0)
        layout.addWidget(girders_combo, 0, 1)

        member_combo = QComboBox()
        member_combo.addItems(["E1-1, E1-2", "E2-1, E2-2", "Custom"])
        apply_field_style(member_combo)
        layout.addWidget(self._create_label("Member ID:"), 1, 0)
        layout.addWidget(member_combo, 1, 1)

        return box

    def _create_section_properties_box(self, title):
        box = self._create_inner_box()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)
        layout.addWidget(self._create_heading_label(title))

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        grid.setColumnMinimumWidth(0, 150)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)

        properties = [
            "Mass, M (Kg/m)",
            "Sectional Area, a (cm2)",
            "2nd Moment of Area, Iz (cm4)",
            "2nd Moment of Area, Iy (cm4)",
            "Radius of Gyration, rz (cm)",
            "Radius of Gyration, ry (cm)",
            "Elastic Modulus, Zz (cm3)",
            "Elastic Modulus, Zy (cm3)",
            "Plastic Modulus, Zuz (cm3)",
            "Plastic Modulus, Zuy (cm3)"
        ]

        inputs = {}
        for row, name in enumerate(properties):
            label = self._create_label(name)
            field = self._create_line_edit()
            grid.addWidget(label, row, 0)
            grid.addWidget(field, row, 1)
            inputs[name] = field

        layout.addLayout(grid)
        return box, inputs

    # ---- View builders ----
    def _build_cross_bracing_view(self):
        view = self._create_card_frame()
        layout = QHBoxLayout(view)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)
        left_layout.addWidget(self._create_selection_box())

        inputs_box = self._create_inner_box()
        inputs_layout = QVBoxLayout(inputs_box)
        inputs_layout.setContentsMargins(12, 4, 12, 8)
        inputs_layout.setSpacing(6)
        title = self._create_heading_label("Section Inputs:")
        title.setStyleSheet("font-size: 12px; font-weight: 600; color: #4b4b4b; border: none; margin-top: 0px; margin-bottom: 2px;")
        inputs_layout.addWidget(title)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        grid.setColumnMinimumWidth(0, 130)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)

        design_combo = QComboBox()
        design_combo.addItems(["Customized", "Optimized"])
        apply_field_style(design_combo)
        row = self._add_grid_row(grid, 0, "Design:", design_combo)

        type_selector = QComboBox()
        type_selector.addItems(VALUES_END_DIAPHRAGM_TYPE)
        type_selector.setCurrentText("Cross Bracing")
        apply_field_style(type_selector)
        row = self._add_grid_row(grid, row, "Type:", type_selector)

        bracing_combo = QComboBox()
        bracing_combo.addItems(["K-Bracing", "X-Bracing", "Diagonal", "Horizontal"])
        apply_field_style(bracing_combo)
        row = self._add_grid_row(grid, row, "Type of Bracing:", bracing_combo)

        section_options = [
            "Double Angles", "Single Angle", "Channel",
            "ISA 100 x 100 x 8", "ISA 110 x 110 x 10"
        ]

        bracing_section = QComboBox()
        bracing_section.addItems(section_options)
        apply_field_style(bracing_section)
        row = self._add_grid_row(grid, row, "Bracing Section:", bracing_section)

        top_bracket = QComboBox()
        top_bracket.addItems(section_options)
        apply_field_style(top_bracket)
        row = self._add_grid_row(grid, row, "Top Bracket Section:", top_bracket)

        bottom_bracket = QComboBox()
        bottom_bracket.addItems(section_options)
        apply_field_style(bottom_bracket)
        row = self._add_grid_row(grid, row, "Bottom Bracket Section:", bottom_bracket)

        spacing_input = self._create_line_edit("Spacing (mm)")
        spacing_input.setValidator(QDoubleValidator(0, 100000, 2))
        self._add_grid_row(grid, row, "Spacing:", spacing_input)

        inputs_layout.addLayout(grid)
        inputs_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        left_layout.addWidget(inputs_box)
        left_layout.addStretch()

        layout.addWidget(left_column)

        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        type_box = self._create_inner_box()
        type_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        type_layout = QVBoxLayout(type_box)
        type_layout.setContentsMargins(12, 8, 12, 10)
        type_layout.setSpacing(6)
        type_layout.addWidget(self._create_heading_label("Type of Bracing"))
        type_layout.addWidget(self._create_image_placeholder("Bracing Layout", 170))
        right_layout.addWidget(type_box)

        for title in ["Bracing", "Top Bracket", "Bottom Bracket"]:
            preview_box = self._create_inner_box()
            preview_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            preview_layout = QVBoxLayout(preview_box)
            preview_layout.setContentsMargins(12, 8, 12, 8)
            preview_layout.setSpacing(6)
            # Make these preview titles bolder without affecting other headings
            preview_heading = QLabel(title)
            preview_heading.setStyleSheet("font-size: 12px; font-weight: 700; color: #4b4b4b; border: none;")
            preview_layout.addWidget(preview_heading)
            preview_layout.addWidget(self._create_image_placeholder("Preview", 110))
            right_layout.addWidget(preview_box)

        right_layout.addStretch()
        layout.addWidget(right_column)
        layout.setStretch(0, 3)
        layout.setStretch(1, 4)
        return view, type_selector

    def _build_rolled_view(self):
        view = self._create_card_frame()
        layout = QHBoxLayout(view)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        left_layout.addWidget(self._create_selection_box())

        inputs_box = self._create_inner_box()
        inputs_layout = QVBoxLayout(inputs_box)
        inputs_layout.setContentsMargins(12, 4, 12, 8)
        inputs_layout.setSpacing(6)
        title = self._create_heading_label("Section Inputs")
        title.setStyleSheet("font-size: 12px; font-weight: 600; color: #4b4b4b; border: none; margin-top: 0px; margin-bottom: 2px;")
        inputs_layout.addWidget(title)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        grid.setColumnMinimumWidth(0, 130)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)

        design_combo = QComboBox()
        design_combo.addItems(["Customized", "Optimized"])
        apply_field_style(design_combo)
        row = self._add_grid_row(grid, 0, "Design:", design_combo)

        type_selector = QComboBox()
        type_selector.addItems(VALUES_END_DIAPHRAGM_TYPE)
        type_selector.setCurrentText("Rolled Beam")
        apply_field_style(type_selector)
        row = self._add_grid_row(grid, row, "Type:", type_selector)

        is_section_combo = QComboBox()
        is_section_combo.addItems([
            "ISMB 500", "ISMB 550", "ISMB 600",
            "ISWB 500", "ISWB 550", "ISWB 600"
        ])
        apply_field_style(is_section_combo)
        self._add_grid_row(grid, row, "IS Section:", is_section_combo)

        inputs_layout.addLayout(grid)
        inputs_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        left_layout.addWidget(inputs_box)
        left_layout.addStretch()
        layout.addWidget(left_column)

        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        image_box = self._create_inner_box()
        image_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        image_layout = QVBoxLayout(image_box)
        image_layout.setContentsMargins(12, 8, 12, 10)
        image_layout.setSpacing(6)
        image_layout.addWidget(self._create_heading_label("Dynamic Image"))
        image_layout.addWidget(self._create_image_placeholder("Rolled Section", 170))
        right_layout.addWidget(image_box)

        props_box, _ = self._create_section_properties_box("Section Properties:")
        props_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        right_layout.addWidget(props_box)
        right_layout.addStretch()

        layout.addWidget(right_column)
        return view, type_selector

    def _build_welded_view(self):
        view = self._create_card_frame()
        layout = QHBoxLayout(view)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        left_layout.addWidget(self._create_selection_box())

        inputs_box = self._create_inner_box()
        inputs_layout = QVBoxLayout(inputs_box)
        inputs_layout.setContentsMargins(12, 8, 12, 10)
        inputs_layout.setSpacing(8)
        inputs_layout.addWidget(self._create_heading_label("Section Inputs:"))

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        grid.setColumnMinimumWidth(0, 150)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)

        design_combo = QComboBox()
        design_combo.addItems(["Customized", "Optimized"])
        apply_field_style(design_combo)
        row = self._add_grid_row(grid, 0, "Design:", design_combo)

        type_selector = QComboBox()
        type_selector.addItems(VALUES_END_DIAPHRAGM_TYPE)
        type_selector.setCurrentText("Welded Beam")
        apply_field_style(type_selector)
        row = self._add_grid_row(grid, row, "Type:", type_selector)

        symmetry_combo = QComboBox()
        symmetry_combo.addItems(["Girder Symmetric", "Girder Unsymmetric"])
        apply_field_style(symmetry_combo)
        row = self._add_grid_row(grid, row, "Symmetry:", symmetry_combo)

        total_depth = self._create_line_edit()
        row = self._add_grid_row(grid, row, "Total Depth (mm):", total_depth)

        web_thick_combo = QComboBox()
        web_thick_combo.addItems(["All", "Custom"])
        apply_field_style(web_thick_combo)
        row = self._add_grid_row(grid, row, "Web Thickness (mm):", web_thick_combo)

        top_width = self._create_line_edit()
        row = self._add_grid_row(grid, row, "Width of Top Flange (mm):", top_width)

        top_thickness_combo = QComboBox()
        top_thickness_combo.addItems(["All", "Custom"])
        apply_field_style(top_thickness_combo)
        row = self._add_grid_row(grid, row, "Top Flange Thickness (mm):", top_thickness_combo)

        bottom_width = self._create_line_edit()
        row = self._add_grid_row(grid, row, "Width of Bottom Flange (mm):", bottom_width)

        bottom_thickness_combo = QComboBox()
        bottom_thickness_combo.addItems(["All", "Custom"])
        apply_field_style(bottom_thickness_combo)
        row = self._add_grid_row(grid, row, "Bottom Flange Thickness (mm):", bottom_thickness_combo)

        bearing_thickness = self._create_line_edit()
        self._add_grid_row(grid, row, "Bearing Stiffener Thickness (mm):", bearing_thickness)

        inputs_layout.addLayout(grid)
        inputs_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        left_layout.addWidget(inputs_box)
        left_layout.addStretch()
        layout.addWidget(left_column)

        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        image_box = self._create_inner_box()
        image_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        image_layout = QVBoxLayout(image_box)
        image_layout.setContentsMargins(12, 8, 12, 10)
        image_layout.setSpacing(6)
        image_layout.addWidget(self._create_heading_label("Dynamic Image"))
        image_layout.addWidget(self._create_image_placeholder("Welded Section", 170))
        right_layout.addWidget(image_box)

        props_box, _ = self._create_section_properties_box("Section Properties:")
        props_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        right_layout.addWidget(props_box)
        right_layout.addStretch()

        layout.addWidget(right_column)
        return view, type_selector

    def _handle_type_selection(self, value):
        if self.block_type_sync:
            return
        if value in self.view_order:
            self._set_current_type(value)

    def _set_current_type(self, target):
        if target not in self.view_order:
            return
        if self.current_type == target:
            return
        self.current_type = target
        index = self.view_order.index(target)
        self.type_stack.setCurrentIndex(index)
        self.block_type_sync = True
        for selector in self.type_selectors:
            selector.setCurrentText(target)
        self.block_type_sync = False
