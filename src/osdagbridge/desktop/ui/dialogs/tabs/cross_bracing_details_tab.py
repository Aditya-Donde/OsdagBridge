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

class CrossBracingDetailsTab(QWidget):
    """Tab for Cross-Bracing Details with visual previews"""

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
        container_layout.setSpacing(16)

        primary_card = self._create_card_frame()
        card_layout = QHBoxLayout(primary_card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(10)

        # Left column (inputs)
        left_column = QWidget()
        left_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        selection_box = self._create_inner_box()
        selection_layout = QGridLayout(selection_box)
        selection_layout.setContentsMargins(8, 4, 8, 4)
        selection_layout.setHorizontalSpacing(8)
        selection_layout.setVerticalSpacing(4)
        selection_layout.setColumnMinimumWidth(0, 130)
        selection_layout.setColumnStretch(1, 1)

        self.select_girders_combo = QComboBox()
        self.select_girders_combo.addItems(["G1 to G2", "G3 to G4", "All"])
        apply_field_style(self.select_girders_combo)
        selection_layout.addWidget(self._create_label("Select Girders:"), 0, 0)
        selection_layout.addWidget(self.select_girders_combo, 0, 1)

        self.member_id_combo = QComboBox()
        self.member_id_combo.addItems(["B1-1 to B1-15", "B2-1 to B2-10", "Custom"])
        apply_field_style(self.member_id_combo)
        selection_layout.addWidget(self._create_label("Member ID:"), 1, 0)
        selection_layout.addWidget(self.member_id_combo, 1, 1)

        left_layout.addWidget(selection_box)

        inputs_box = self._create_inner_box()
        inputs_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        inputs_layout = QVBoxLayout(inputs_box)
        inputs_layout.setContentsMargins(12, 8, 12, 8)
        inputs_layout.setSpacing(6)
        inputs_layout.addWidget(self._create_heading_label("Section Inputs:"))

        inputs_grid = QGridLayout()
        inputs_grid.setContentsMargins(0, 0, 0, 0)
        inputs_grid.setHorizontalSpacing(16)
        inputs_grid.setVerticalSpacing(12)
        inputs_grid.setColumnMinimumWidth(0, 130)
        inputs_grid.setColumnStretch(0, 0)
        inputs_grid.setColumnStretch(1, 1)

        self.design_combo = QComboBox()
        self.design_combo.addItems(["Customized", "Optimized"])
        apply_field_style(self.design_combo)
        row = self._add_grid_row(inputs_grid, 0, "Design:", self.design_combo)

        self.bracing_type_combo = QComboBox()
        self.bracing_type_combo.addItems(["K-Bracing", "X-Bracing", "Diagonal", "Horizontal"])
        apply_field_style(self.bracing_type_combo)
        row = self._add_grid_row(inputs_grid, row, "Type of Bracing:", self.bracing_type_combo)

        section_options = [
            "ISA 50 x 50 x 6", "ISA 65 x 65 x 6", "ISA 75 x 75 x 6",
            "ISA 90 x 90 x 8", "ISA 100 x 100 x 8", "ISA 110 x 110 x 10",
            "ISA 130 x 130 x 10", "ISMC 75", "ISMC 100", "ISMC 125",
            "ISMC 150", "2-ISA 65 x 65 x 6", "2-ISA 75 x 75 x 6"
        ]

        self.bracing_section_combo = QComboBox()
        self.bracing_section_combo.addItems(section_options)
        apply_field_style(self.bracing_section_combo)
        row = self._add_grid_row(inputs_grid, row, "Bracing Section:", self.bracing_section_combo)

        self.top_bracket_type_combo = QComboBox()
        self.top_bracket_type_combo.addItems(["Double Angles", "Single Angle", "Channel"])
        apply_field_style(self.top_bracket_type_combo)
        row = self._add_grid_row(inputs_grid, row, "Top Bracket Section:", self.top_bracket_type_combo)

        self.top_bracket_size_combo = QComboBox()
        self.top_bracket_size_combo.addItems(section_options)
        apply_field_style(self.top_bracket_size_combo)
        row = self._add_grid_row(inputs_grid, row, "Top Bracket Size:", self.top_bracket_size_combo)

        self.bottom_bracket_type_combo = QComboBox()
        self.bottom_bracket_type_combo.addItems(["Double Angles", "Single Angle", "Channel"])
        apply_field_style(self.bottom_bracket_type_combo)
        row = self._add_grid_row(inputs_grid, row, "Bottom Bracket Section:", self.bottom_bracket_type_combo)

        self.bottom_bracket_size_combo = QComboBox()
        self.bottom_bracket_size_combo.addItems(section_options)
        apply_field_style(self.bottom_bracket_size_combo)
        row = self._add_grid_row(inputs_grid, row, "Bottom Bracket Size:", self.bottom_bracket_size_combo)

        self.spacing_input = QLineEdit()
        self.spacing_input.setPlaceholderText("Spacing (mm)")
        self.spacing_input.setValidator(QDoubleValidator(0, 100000, 2))
        apply_field_style(self.spacing_input)
        self._add_grid_row(inputs_grid, row, "Spacing:", self.spacing_input)

        inputs_layout.addLayout(inputs_grid)
        left_layout.addWidget(inputs_box)

        card_layout.addWidget(left_column)

        # Right column (previews)
        right_column = QWidget()
        right_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(14)

        type_box = self._create_inner_box()
        type_layout = QVBoxLayout(type_box)
        type_layout.setContentsMargins(12, 10, 12, 10)
        type_layout.setSpacing(10)
        type_layout.addWidget(self._create_heading_label("Type of Bracing"))
        self.bracing_image_label = self._create_image_placeholder(210)
        type_layout.addWidget(self.bracing_image_label)
        right_layout.addWidget(type_box)

        self.bracing_preview_box, self.bracing_preview_label = self._create_preview_box("Bracing")
        right_layout.addWidget(self.bracing_preview_box)

        self.top_bracket_preview_box, self.top_bracket_preview_label = self._create_preview_box("Top Bracket")
        right_layout.addWidget(self.top_bracket_preview_box)

        self.bottom_bracket_preview_box, self.bottom_bracket_preview_label = self._create_preview_box("Bottom Bracket")
        right_layout.addWidget(self.bottom_bracket_preview_box)

        card_layout.addWidget(right_column)
        card_layout.setStretch(0, 3)
        card_layout.setStretch(1, 2)
        container_layout.addWidget(primary_card)
        container_layout.addStretch()

        self.bracing_type_combo.currentTextChanged.connect(self._update_previews)
        self.bracing_section_combo.currentTextChanged.connect(self._update_previews)
        self.top_bracket_size_combo.currentTextChanged.connect(self._update_previews)
        self.bottom_bracket_size_combo.currentTextChanged.connect(self._update_previews)
        self._update_previews()

    def _create_card_frame(self):
        card = QFrame()
        card.setStyleSheet("QFrame { border: 1px solid #d0d0d0; border-radius: 12px; background-color: #ffffff; }")
        return card

    def _create_inner_box(self):
        box = QFrame()
        box.setStyleSheet(
            "QFrame { border: 1px solid #cfcfcf; border-radius: 8px; background-color: #ffffff; }"
            "QFrame QComboBox, QFrame QLineEdit { border: none; border-bottom: 1px solid #d0d0d0; border-radius: 0px; min-height: 28px; padding: 4px 8px; background-color: #ffffff; }"
            "QFrame QComboBox:hover, QFrame QLineEdit:hover { border-bottom: 1px solid #5d5d5d; }"
            "QFrame QComboBox:focus, QFrame QLineEdit:focus { border-bottom: 1px solid #90AF13; }"
            "QFrame QLabel { border: none; }"
        )
        return box

    def _create_heading_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("font-size: 12px; font-weight: 600; color: #4b4b4b; border: none;")
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

    def _create_image_placeholder(self, height):
        label = QLabel("Bracing Preview")
        label.setAlignment(Qt.AlignCenter)
        label.setMinimumHeight(height)
        label.setStyleSheet("QLabel { border: 1px solid #d0d0d0; border-radius: 10px; background-color: #f7f7f7; font-weight: bold; color: #5b5b5b; }")
        return label

    def _create_preview_box(self, title):
        box = self._create_inner_box()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        layout.addWidget(self._create_heading_label(title))
        image = self._create_image_placeholder(120)
        layout.addWidget(image)
        return box, image

    def _update_previews(self):
        self.bracing_image_label.setText(self.bracing_type_combo.currentText())
        self.bracing_preview_label.setText(self.bracing_section_combo.currentText())
        self.top_bracket_preview_label.setText(self.top_bracket_size_combo.currentText())
        self.bottom_bracket_preview_label.setText(self.bottom_bracket_size_combo.currentText())

