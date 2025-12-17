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
from osdagbridge.desktop.ui.dialogs.tabs.optimizable_field import OptimizableField

class StiffenerDetailsTab(QWidget):
    """Tab for Stiffener Details with compact layout"""

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
        container.setStyleSheet("background-color: #f4f4f4;")

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(4)

        # Combined card for inputs and description
        card_frame = self._create_card_frame()
        card_layout = QHBoxLayout(card_frame)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(18)

        # Left column - inputs
        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        girder_row = QHBoxLayout()
        girder_row.setContentsMargins(0, 0, 0, 0)
        girder_row.setSpacing(10)

        girder_label = QLabel("Select Girder Member:")
        girder_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #3a3a3a; border: none;")
        girder_row.addWidget(girder_label)

        self.girder_member_combo = QComboBox()
        self.girder_member_combo.addItems(["G1-1", "G1-2", "G1-3", "All"])
        apply_field_style(self.girder_member_combo)
        self.girder_member_combo.setFixedWidth(190)
        self.girder_member_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        girder_row.addWidget(self.girder_member_combo, 1)

        left_layout.addLayout(girder_row)

        stiffener_heading = QLabel("Stiffener Inputs")
        stiffener_heading.setStyleSheet("font-size: 11px; font-weight: 700; color: #000000; border: none; margin-top: 4px;")
        left_layout.addWidget(stiffener_heading)

        inputs_grid = QGridLayout()
        inputs_grid.setContentsMargins(0, 0, 0, 0)
        inputs_grid.setHorizontalSpacing(12)
        inputs_grid.setVerticalSpacing(10)
        inputs_grid.setColumnMinimumWidth(0, 180)
        inputs_grid.setColumnStretch(0, 0)
        inputs_grid.setColumnStretch(1, 1)

        self.intermediate_combo = QComboBox()
        self.intermediate_combo.addItems(["No", "Yes - At Supports", "Yes - Spaced"])
        apply_field_style(self.intermediate_combo)
        row = self._add_form_row(inputs_grid, 0, "Intermediate Stiffener:", self.intermediate_combo)

        self.spacing_field = OptimizableField("Intermediate Stiffener Spacing")
        self.spacing_field.mode_combo.clear()
        self.spacing_field.mode_combo.addItems(["NA", "Optimized", "Customized"])
        self.spacing_field.on_mode_changed(self.spacing_field.mode_combo.currentText())
        self._prepare_optimizable_field(self.spacing_field)
        row = self._add_form_row(inputs_grid, row, "Intermediate Stiffener Spacing:", self.spacing_field)

        self.longitudinal_combo = QComboBox()
        self.longitudinal_combo.addItems(["None", "Yes and 1 stiffener", "Yes and 2 stiffeners"])
        apply_field_style(self.longitudinal_combo)
        row = self._add_form_row(inputs_grid, row, "Longitudinal Stiffener:", self.longitudinal_combo)

        self.intermediate_thick_combo = QComboBox()
        self.intermediate_thick_combo.addItems(["All", "Custom"])
        apply_field_style(self.intermediate_thick_combo)
        row = self._add_form_row(inputs_grid, row, "Intermediate Stiffener Thickness:", self.intermediate_thick_combo)

        self.long_thick_combo = QComboBox()
        self.long_thick_combo.addItems(["All", "Custom"])
        self.long_thick_combo.setEnabled(False)
        apply_field_style(self.long_thick_combo)
        row = self._add_form_row(inputs_grid, row, "Longitudinal Stiffener Thickness:", self.long_thick_combo)

        left_layout.addLayout(inputs_grid)

        buckling_heading = QLabel("Web Buckling Details")
        buckling_heading.setStyleSheet("font-size: 11px; font-weight: 700; color: #000000; border: none; margin-top: 4px;")
        left_layout.addWidget(buckling_heading)

        buckling_grid = QGridLayout()
        buckling_grid.setContentsMargins(0, 0, 0, 0)
        buckling_grid.setHorizontalSpacing(12)
        buckling_grid.setVerticalSpacing(10)
        buckling_grid.setColumnMinimumWidth(0, 180)

        self.method_combo = QComboBox()
        self.method_combo.addItems(VALUES_STIFFENER_DESIGN)
        apply_field_style(self.method_combo)
        self._add_form_row(buckling_grid, 0, "Shear Buckling Design Method:", self.method_combo)

        left_layout.addLayout(buckling_grid)

        card_layout.addWidget(left_column, 2)

        # Right column - description
        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        desc_heading = QLabel("Description")
        desc_heading.setStyleSheet("font-size: 11px; font-weight: 700; color: #000000; border: none;")
        right_layout.addWidget(desc_heading)

        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        self.description_text.setPlaceholderText("Describe stiffener assumptions or notes here.")
        self.description_text.setMinimumHeight(210)
        self.description_text.setStyleSheet(
            "QTextEdit { border: 1px solid #d0d0d0; border-radius: 6px; background: #ffffff; color: #3a3a3a; font-size: 11px; }"
        )
        right_layout.addWidget(self.description_text, 1)

        card_layout.addWidget(right_column, 3)

        container_layout.addWidget(card_frame)

        # Dynamic image box
        image_box = self._create_card_frame()
        image_layout = QVBoxLayout(image_box)
        image_layout.setContentsMargins(16, 16, 16, 16)
        image_layout.setSpacing(8)

        self.dynamic_image_label = QLabel("Dynamic Image")
        self.dynamic_image_label.setAlignment(Qt.AlignCenter)
        self.dynamic_image_label.setMinimumHeight(140)
        self.dynamic_image_label.setStyleSheet(
            "QLabel { border: 1px solid #d8d8d8; border-radius: 8px; background-color: #f8f8f8; "
            "font-weight: 600; color: #5b5b5b; font-size: 11px; }"
        )
        image_layout.addWidget(self.dynamic_image_label)
        container_layout.addWidget(image_box)


        # Signals
        self.longitudinal_combo.currentTextChanged.connect(self.on_longitudinal_changed)

    def _create_card_frame(self):
        card = QFrame()
        card.setStyleSheet(
            "QFrame { border: 1px solid #d6d6d6; border-radius: 8px; background-color: #f7f7f7; }"
        )
        return card

    def _create_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("font-size: 11px; color: #3a3a3a; border: none;")
        return label

    def _add_form_row(self, layout, row, text, widget):
        label = self._create_label(text)
        layout.addWidget(label, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(widget, row, 1)
        return row + 1

    def _prepare_optimizable_field(self, field):
        field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        apply_field_style(field.mode_combo)
        apply_field_style(field.input_field)

    def on_longitudinal_changed(self, text):
        has_longitudinal = text.lower().startswith("yes")
        self.long_thick_combo.setEnabled(has_longitudinal)

