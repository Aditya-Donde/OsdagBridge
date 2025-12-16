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

def get_combobox_style():
    """Return the common stylesheet for dropdowns with the SVG icon from resources."""
    return """
        QComboBox{
            padding: 1px 7px;
            border: 1px solid black;
            border-radius: 5px;
            background-color: white;
            color: black;
        }
        QComboBox::drop-down{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            border-left: 0px;
        }
        QComboBox::down-arrow{
            image: url(:/vectors/arrow_down_light.svg);
            width: 20px;
            height: 20px;
            margin-right: 8px;
        }
        QComboBox::down-arrow:on {
            image: url(:/vectors/arrow_up_light.svg);
            width: 20px;
            height: 20px;
            margin-right: 8px;
        }
        QComboBox QAbstractItemView{
            background-color: white;
            border: 1px solid black;
            outline: none;
        }
        QComboBox QAbstractItemView::item{
            color: black;
            background-color: white;
            border: none;
            border: 1px solid white;
            border-radius: 0;
            padding: 2px;
        }
        QComboBox QAbstractItemView::item:hover{
            border: 1px solid #90AF13;
            background-color: #90AF13;
            color: black;
        }
        QComboBox QAbstractItemView::item:selected{
            background-color: #90AF13;
            color: black;
            border: 1px solid #90AF13;
        }
        QComboBox QAbstractItemView::item:selected:hover{
            background-color: #90AF13;
            color: black;
            border: 1px solid #94b816;
        }
        QComboBox:disabled{
            background: #f1f1f1;
            color: #666;
        }
    """


def get_lineedit_style():
    """Return the shared stylesheet for line edits in the section inputs."""
    return """
        QLineEdit {
            padding: 1px 7px;
            border: 1px solid #070707;
            border-radius: 6px;
            background-color: white;
            color: #000000;
            font-weight: normal;
        }
        QLineEdit:disabled{
            background: #f1f1f1;
            color: #666;
        }
        QLineEdit:hover {
            border: 1px solid #5d5d5d;
        }
    """


def apply_field_style(widget):
    """Apply the appropriate style to combo boxes and line edits."""
    widget.setMinimumHeight(28)
    if isinstance(widget, QComboBox):
        widget.setStyleSheet(get_combobox_style())
    elif isinstance(widget, QLineEdit):
        widget.setStyleSheet(get_lineedit_style())



class GirderDetailsTab(QWidget):
    """Tab for Girder Details styled to match the provided reference."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.welded_rows = []
        self.rolled_rows = []
        self.section_property_inputs = {}
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        main_layout.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        content.setStyleSheet("background-color: white;")

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(10, 0, 10, 10)
        content_layout.setSpacing(12)

        content_layout.addWidget(self._build_overview_card())
        content_layout.addWidget(self._build_section_card())
        content_layout.addStretch()

    def _build_overview_card(self):
        card = self._create_card_frame()
        layout = QGridLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setHorizontalSpacing(20)
        layout.setVerticalSpacing(12)

        self.select_girder_combo = QComboBox()
        self.select_girder_combo.addItems(["Girder 1", "Girder 2", "Girder 3", "Girder 4", "Girder 5", "All"])
        apply_field_style(self.select_girder_combo)
        self._set_field_width(self.select_girder_combo)

        self.span_combo = QComboBox()
        self.span_combo.addItems(["Custom", "Full Length"])
        apply_field_style(self.span_combo)
        self._set_field_width(self.span_combo)

        self.member_id_input = QLineEdit("G1-1")
        apply_field_style(self.member_id_input)
        self._set_field_width(self.member_id_input)

        self.member_select_combo = QComboBox()
        self.member_select_combo.addItems(["Girder 1", "Girder 2", "Girder 3", "Girder 4", "Girder 5"])
        apply_field_style(self.member_select_combo)
        self._set_field_width(self.member_select_combo)

        self.distance_start_input = QLineEdit("0")
        self.distance_end_input = QLineEdit("30")
        apply_field_style(self.distance_start_input)
        apply_field_style(self.distance_end_input)
        self._set_field_width(self.distance_start_input, 80)
        self._set_field_width(self.distance_end_input, 80)

        self.length_input = QLineEdit("30")
        apply_field_style(self.length_input)
        self._set_field_width(self.length_input)

        layout.addWidget(self._create_label("Select Girder:"), 0, 0)
        layout.addWidget(self.select_girder_combo, 0, 1)
        layout.addWidget(self._create_label("Span:"), 0, 2)
        layout.addWidget(self.span_combo, 0, 3)

        layout.addWidget(self._create_label("Member ID:"), 1, 0)
        layout.addWidget(self.member_id_input, 1, 1)
        layout.addWidget(self._create_label("Length (m):"), 1, 2)
        layout.addWidget(self.length_input, 1, 3)

        layout.addWidget(self._create_label("Distance from left edge (m):"), 2, 0)
        layout.addLayout(self._build_distance_row(), 2, 1)

        layout.addWidget(self._create_label("Member:"), 2, 2)
        layout.addWidget(self.member_select_combo, 2, 3)

        return card

    def _build_distance_row(self):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        row.addWidget(self._create_small_label("Start"))
        row.addWidget(self.distance_start_input)
        row.addWidget(self._create_small_label("End"))
        row.addWidget(self.distance_end_input)
        return row

    def _build_section_card(self):
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        main_layout = QHBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(16)

        # Left side - two bordered boxes stacked vertically
        left_column = QWidget()
        left_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        left_column_layout = QVBoxLayout(left_column)
        left_column_layout.setContentsMargins(0, 0, 0, 0)
        left_column_layout.setSpacing(12)

        # Section Inputs box (single frame containing all fields)
        section_inputs_box = self._create_inner_box()
        section_inputs_layout = QVBoxLayout(section_inputs_box)
        section_inputs_layout.setContentsMargins(12, 8, 12, 12)
        section_inputs_layout.setSpacing(8)

        section_inputs_title = self._create_label("Section Inputs:")
        section_inputs_layout.addWidget(section_inputs_title)

        inputs_grid = QGridLayout()
        inputs_grid.setContentsMargins(0, 0, 0, 0)
        inputs_grid.setHorizontalSpacing(16)
        inputs_grid.setVerticalSpacing(12)
        inputs_grid.setColumnMinimumWidth(0, 150)
        inputs_grid.setColumnStretch(0, 0)
        inputs_grid.setColumnStretch(1, 1)

        self.design_combo = QComboBox()
        self.design_combo.addItems(["Customized", "Optimized"])
        apply_field_style(self.design_combo)
        row = self._add_box_row(inputs_grid, 0, "Design:", self.design_combo)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Welded", "Rolled"])
        apply_field_style(self.type_combo)
        row = self._add_box_row(inputs_grid, row, "Type:", self.type_combo)

        self.symmetry_combo = QComboBox()
        self.symmetry_combo.addItems(["Girder Symmetric", "Girder Unsymmetric"])
        apply_field_style(self.symmetry_combo)
        row = self._add_box_row(inputs_grid, row, "Symmetry:", self.symmetry_combo)

        self.total_depth_input = self._create_line_edit()
        row = self._add_box_row(inputs_grid, row, "Total Depth (mm):", self.total_depth_input, self.welded_rows)

        self.web_thickness_combo = QComboBox()
        self.web_thickness_combo.addItems(["All", "Custom"])
        apply_field_style(self.web_thickness_combo)
        row = self._add_box_row(inputs_grid, row, "Web Thickness (mm):", self.web_thickness_combo, self.welded_rows)

        self.top_width_input = self._create_line_edit()
        row = self._add_box_row(inputs_grid, row, "Width of Top Flange (mm):", self.top_width_input, self.welded_rows)

        self.top_thickness_combo = QComboBox()
        self.top_thickness_combo.addItems(["All", "Custom"])
        apply_field_style(self.top_thickness_combo)
        row = self._add_box_row(inputs_grid, row, "Top Flange Thickness (mm):", self.top_thickness_combo, self.welded_rows)

        self.bottom_width_input = self._create_line_edit()
        row = self._add_box_row(inputs_grid, row, "Width of Bottom Flange (mm):", self.bottom_width_input, self.welded_rows)

        self.bottom_thickness_combo = QComboBox()
        self.bottom_thickness_combo.addItems(["All", "Custom"])
        apply_field_style(self.bottom_thickness_combo)
        row = self._add_box_row(inputs_grid, row, "Bottom Flange Thickness (mm):", self.bottom_thickness_combo, self.welded_rows)

        self.is_section_combo = QComboBox()
        self.is_section_combo.addItems([
            "ISMB 500", "ISMB 550", "ISMB 600",
            "ISWB 500", "ISWB 550", "ISWB 600"
        ])
        apply_field_style(self.is_section_combo)
        self._add_box_row(inputs_grid, row, "IS Section:", self.is_section_combo, self.rolled_rows)

        section_inputs_layout.addLayout(inputs_grid)
        left_column_layout.addWidget(section_inputs_box)

        # Restraint/Web details box
        restraint_box = self._create_inner_box()
        restraint_layout = QVBoxLayout(restraint_box)
        restraint_layout.setContentsMargins(12, 8, 12, 12)
        restraint_layout.setSpacing(8)

        restraint_title = self._create_label("Restraint & Web Details:")
        restraint_layout.addWidget(restraint_title)

        restraint_grid = QGridLayout()
        restraint_grid.setContentsMargins(0, 0, 0, 0)
        restraint_grid.setHorizontalSpacing(16)
        restraint_grid.setVerticalSpacing(12)
        restraint_grid.setColumnMinimumWidth(0, 150)
        restraint_grid.setColumnStretch(0, 0)
        restraint_grid.setColumnStretch(1, 1)

        self.torsion_combo = QComboBox()
        self.torsion_combo.addItems(VALUES_TORSIONAL_RESTRAINT)
        apply_field_style(self.torsion_combo)
        row = self._add_box_row(restraint_grid, 0, "Torsional Restraint:", self.torsion_combo)

        self.warping_combo = QComboBox()
        self.warping_combo.addItems(VALUES_WARPING_RESTRAINT)
        apply_field_style(self.warping_combo)
        row = self._add_box_row(restraint_grid, row, "Warping Restraint:", self.warping_combo)

        self.web_type_combo = QComboBox()
        self.web_type_combo.addItems(["Thin Web with ITS", "Thick Web"])
        apply_field_style(self.web_type_combo)
        self._add_box_row(restraint_grid, row, "Web Type*:", self.web_type_combo)

        restraint_layout.addLayout(restraint_grid)
        left_column_layout.addWidget(restraint_box)

        main_layout.addWidget(left_column)

        # Right side - image + section properties box
        right_column = QWidget()
        right_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        right_column_layout = QVBoxLayout(right_column)
        right_column_layout.setContentsMargins(0, 0, 0, 0)
        right_column_layout.setSpacing(12)

        # Dynamic image box
        image_box = self._create_inner_box()
        image_layout = QVBoxLayout(image_box)
        image_layout.setContentsMargins(10, 10, 10, 10)
        image_layout.setSpacing(5)

        self.dynamic_image_label = QLabel("Welded Girder")
        self.dynamic_image_label.setAlignment(Qt.AlignCenter)
        self.dynamic_image_label.setMinimumSize(240, 140)
        self.dynamic_image_label.setStyleSheet("QLabel { border: 1px solid #d0d0d0; border-radius: 4px; background-color: #fafafa; font-weight: bold; color: #5b5b5b; }")
        image_layout.addWidget(self.dynamic_image_label)

        right_column_layout.addWidget(image_box)

        # Section Properties box
        props_box = self._create_inner_box()
        props_layout = QVBoxLayout(props_box)
        props_layout.setContentsMargins(12, 10, 12, 10)
        props_layout.setSpacing(10)

        props_title = self._create_label("Section Properties:")
        props_layout.addWidget(props_title)

        properties_grid = QGridLayout()
        properties_grid.setContentsMargins(0, 0, 0, 0)
        properties_grid.setHorizontalSpacing(12)
        properties_grid.setVerticalSpacing(10)
        properties_grid.setColumnMinimumWidth(0, 140)
        properties_grid.setColumnStretch(0, 0)
        properties_grid.setColumnStretch(1, 1)

        property_fields = [
            "Mass, M (Kg/m)",
            "Sectional Area, a (cm2)",
            "2nd Moment of Area, Iz (cm4)",
            "2nd Moment of Area, Iy (cm4)",
            "Radius of Gyration, rz (cm)",
            "Radius of Gyration, ry (cm)",
            "Elastic Modulus, Zz (cm3)",
            "Elastic Modulus, Zy (cm3)",
            "Plastic Modulus, Zuz (cm3)",
            "Plastic Modulus, Zuy (cm3)",
            "Torsion Constant, It (cm4)",
            "Warping Constant, Iw (cm6)"
        ]

        for index, text in enumerate(property_fields):
            label = self._create_small_label(text)
            line_edit = self._create_line_edit()
            line_edit.setPlaceholderText("")
            properties_grid.addWidget(label, index, 0)
            properties_grid.addWidget(line_edit, index, 1)
            self.section_property_inputs[text] = line_edit

        props_layout.addLayout(properties_grid)
        right_column_layout.addWidget(props_box)

        main_layout.addWidget(right_column)

        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        self._on_type_changed(self.type_combo.currentText())

        return container

    def _create_card_frame(self):
        frame = QFrame()
        frame.setObjectName("girderCard")
        frame.setStyleSheet("QFrame#girderCard { background-color: white; border: 1px solid #cfcfcf; border-radius: 10px; }")
        return frame

    def _create_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("font-size: 12px; color: #2f2f2f; font-weight: 600; background: transparent;")
        label.setAutoFillBackground(False)
        return label

    def _create_small_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("font-size: 10px; color: #5a5a5a; background: transparent;")
        label.setAutoFillBackground(False)
        return label

    def _create_line_edit(self):
        line_edit = QLineEdit()
        apply_field_style(line_edit)
        return line_edit

    def _add_section_row(self, layout, row, text, widget, tracker=None):
        label = self._create_label(text)
        widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._set_field_width(widget)
        layout.addWidget(label, row, 0)
        layout.addWidget(widget, row, 1)
        if tracker is not None:
            tracker.append((label, widget))
        return row + 1

    def _set_field_width(self, widget, width=230):
        widget.setMaximumWidth(width)
        widget.setMinimumWidth(min(width, 160))

    def _on_type_changed(self, text):
        is_welded = text.lower() == "welded"
        self._set_row_visibility(self.welded_rows, is_welded)
        self._set_row_visibility(self.rolled_rows, not is_welded)
        if is_welded:
            self.dynamic_image_label.setText("Welded Girder")
        else:
            self.dynamic_image_label.setText("Rolled Section")

    def _create_inner_box(self):
        """Create a bordered box for grouped controls"""
        box = QFrame()
        box.setStyleSheet("""
            QFrame {
               border: 1px solid #b0b0b0;
               border-radius: 6px;
               background-color: #ffffff;
            }
            QFrame QComboBox, QFrame QLineEdit {
               border: none;
               border-bottom: 1px solid #d0d0d0;
               border-radius: 0px;
               min-height: 28px;
               padding: 4px 8px;
               background-color: #ffffff;
            }
            QFrame QComboBox:hover, QFrame QLineEdit:hover {
               border-bottom: 1px solid #5d5d5d;
            }
            QFrame QComboBox:focus, QFrame QLineEdit:focus {
               border-bottom: 1px solid #90AF13;
            }
            QFrame QLabel {
               border: none;
               padding: 0px;
               margin: 0px;
            }
        """)
        return box

    def _create_small_label(self, text):
        """Create a smaller label for compact layouts"""
        label = QLabel(text)
        label.setStyleSheet("""
            QLabel {
               color: #2b2b2b;
               font-size: 11px;
               font-weight: 500;
               background: transparent;
               border: none;
               padding: 0px;
               margin: 0px;
            }
        """)
        label.setAutoFillBackground(False)
        return label

    def _add_box_row(self, layout, row, label_text, widget, visibility_list=None):
        """Add a row to a box grid layout"""
        label = self._create_small_label(label_text)
        layout.addWidget(label, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(widget, row, 1)
        if visibility_list is not None:
            visibility_list.append((label, widget))
        return row + 1

    def _set_row_visibility(self, rows, visible):
        for label, widget in rows:
            label.setVisible(visible)
            widget.setVisible(visible)

