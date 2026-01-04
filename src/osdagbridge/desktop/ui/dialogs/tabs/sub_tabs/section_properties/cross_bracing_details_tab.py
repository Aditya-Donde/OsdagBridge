import sys
import os
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
from osdagbridge.desktop.ui.widgets.section_viewer import SectionPreviewWidget, SectionCatalog

class CrossBracingDetailsTab(QWidget):
    """Tab for Cross-Bracing Details with visual previews"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.catalog = SectionCatalog()
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
        container_layout.setContentsMargins(6, 6, 6, 6)
        container_layout.setSpacing(8)

        primary_card = self._create_card_frame()
        card_layout = QHBoxLayout(primary_card)
        card_layout.setContentsMargins(10, 8, 10, 8)
        card_layout.setSpacing(8)

        # Left column (inputs)
        left_column = QWidget()
        left_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        selection_box = self._create_inner_box()
        selection_layout = QGridLayout(selection_box)
        selection_layout.setContentsMargins(8, 4, 8, 4)
        selection_layout.setHorizontalSpacing(6)
        selection_layout.setVerticalSpacing(2)
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

        selection_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        left_layout.addWidget(selection_box)

        inputs_box = self._create_inner_box()
        inputs_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        inputs_layout = QVBoxLayout(inputs_box)
        inputs_layout.setContentsMargins(12, 8, 12, 8)
        inputs_layout.setSpacing(6)
        inputs_layout.addWidget(self._create_heading_label("Section Inputs:"))

        inputs_grid = QGridLayout()
        inputs_grid.setContentsMargins(0, 0, 0, 0)
        inputs_grid.setHorizontalSpacing(12)
        inputs_grid.setVerticalSpacing(8)
        inputs_grid.setColumnMinimumWidth(0, 130)
        inputs_grid.setColumnStretch(0, 0)
        inputs_grid.setColumnStretch(1, 1)

        self.design_combo = QComboBox()
        self.design_combo.addItems(["Customized", "Optimized"])
        if self.design_combo.count() > 1:
            self.design_combo.setCurrentIndex(1)  # Default to Optimized
        apply_field_style(self.design_combo)
        row = self._add_grid_row(inputs_grid, 0, "Design:", self.design_combo)

        self.bracing_type_combo = QComboBox()
        self.bracing_type_combo.addItems(["K-Bracing", "X-Bracing"])
        apply_field_style(self.bracing_type_combo)
        row = self._add_grid_row(inputs_grid, row, "Type of Bracing:", self.bracing_type_combo)

        section_type_options = [
            "Angle",
            "Double Angle (Long Leg)",
            "Double Angle (Short Leg)",
            "Channel",
            "Double Channel",
        ]

        self.bracing_section_type_combo = QComboBox()
        self.bracing_section_type_combo.addItems(section_type_options)
        apply_field_style(self.bracing_section_type_combo)
        row = self._add_grid_row(inputs_grid, row, "Bracing Section Type:", self.bracing_section_type_combo)

        self.bracing_section_combo = QComboBox()
        apply_field_style(self.bracing_section_combo)
        row = self._add_grid_row(inputs_grid, row, "Bracing Section:", self.bracing_section_combo)

        self.top_bracket_type_combo = QComboBox()
        self.top_bracket_type_combo.addItems(section_type_options)
        apply_field_style(self.top_bracket_type_combo)
        row = self._add_grid_row(inputs_grid, row, "Top Bracket Section:", self.top_bracket_type_combo)

        self.top_bracket_size_combo = QComboBox()
        apply_field_style(self.top_bracket_size_combo)
        row = self._add_grid_row(inputs_grid, row, "Top Bracket Size:", self.top_bracket_size_combo)

        self.bottom_bracket_type_combo = QComboBox()
        self.bottom_bracket_type_combo.addItems(section_type_options)
        apply_field_style(self.bottom_bracket_type_combo)
        row = self._add_grid_row(inputs_grid, row, "Bottom Bracket Section:", self.bottom_bracket_type_combo)

        self.bottom_bracket_size_combo = QComboBox()
        apply_field_style(self.bottom_bracket_size_combo)
        row = self._add_grid_row(inputs_grid, row, "Bottom Bracket Size:", self.bottom_bracket_size_combo)

        self.spacing_input = QLineEdit()
        self.spacing_input.setPlaceholderText("Spacing (mm)")
        self.spacing_input.setValidator(QDoubleValidator(0, 100000, 2))
        apply_field_style(self.spacing_input)
        self._add_grid_row(inputs_grid, row, "Spacing:", self.spacing_input)

        inputs_layout.addLayout(inputs_grid)
        left_layout.addWidget(inputs_box)
        left_layout.addStretch(1)

        card_layout.addWidget(left_column)

        # Right column (previews)
        right_column = QWidget()
        self.right_column = right_column
        right_column.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(14)

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
        self.bracing_section_type_combo.currentTextChanged.connect(self._on_bracing_type_changed)
        self.bracing_section_combo.currentTextChanged.connect(self._update_previews)
        self.top_bracket_type_combo.currentTextChanged.connect(self._on_top_bracket_type_changed)
        self.top_bracket_size_combo.currentTextChanged.connect(self._update_previews)
        self.bottom_bracket_type_combo.currentTextChanged.connect(self._on_bottom_bracket_type_changed)
        self.bottom_bracket_size_combo.currentTextChanged.connect(self._update_previews)
        self.design_combo.currentTextChanged.connect(self._on_design_changed)
        self._populate_designations()
        self._on_design_changed(self.design_combo.currentText())

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
        widget = SectionPreviewWidget()
        widget.setMinimumHeight(height)
        widget.setStyleSheet("QWidget { border: 1px solid #d0d0d0; border-radius: 10px; background-color: #0f0f0f; }")
        return widget

    def _create_preview_box(self, title):
        box = self._create_inner_box()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        layout.addWidget(self._create_heading_label(title))
        image = self._create_image_placeholder(150)
        layout.addWidget(image)
        return box, image

    def _update_previews(self):
        if self.design_combo.currentText() != "Customized":
            # Hide geometry when optimization controls the section selection.
            for widget in [
                self.bracing_preview_label,
                self.top_bracket_preview_label,
                self.bottom_bracket_preview_label,
            ]:
                widget.set_section("", "")
            return
        self._set_preview(self.bracing_preview_label, self.bracing_section_type_combo, self.bracing_section_combo)
        self._set_preview(self.top_bracket_preview_label, self.top_bracket_type_combo, self.top_bracket_size_combo)
        self._set_preview(self.bottom_bracket_preview_label, self.bottom_bracket_type_combo, self.bottom_bracket_size_combo)

    def _apply_custom_mode(self, is_custom: bool):
        # Only allow manual section selection (and show previews) in Customized mode.
        self.right_column.setVisible(is_custom)
        for widget in [
            self.bracing_section_type_combo,
            self.bracing_section_combo,
            self.top_bracket_type_combo,
            self.top_bracket_size_combo,
            self.bottom_bracket_type_combo,
            self.bottom_bracket_size_combo,
        ]:
            widget.setEnabled(is_custom)

    def _on_design_changed(self, label: str):
        is_custom = label == "Customized"
        self._apply_custom_mode(is_custom)
        self._update_previews()

    # ---- Helpers for section labels -------------------------------------
    def _display_name_for(self, designation: str, section_type: str) -> str:
        name = (designation or "").strip()
        if section_type in ("angle", "double_angle_long", "double_angle_short"):
            name = name.lstrip("∠⌒⟡⟠").strip()
            if not name.upper().startswith("IS"):
                name = f"IS {name}"
        return name

    def _fill_combo(self, combo: QComboBox, items, section_type: str):
        combo.blockSignals(True)
        combo.clear()
        for des in items:
            combo.addItem(self._display_name_for(des, section_type), des)
        combo.blockSignals(False)

    def _set_preview(self, widget: SectionPreviewWidget, type_combo: QComboBox, size_combo: QComboBox):
        stype = self._map_section_type(type_combo.currentText())
        designation = size_combo.currentData() or size_combo.currentText()
        show_double_total = True
        if widget is self.bracing_preview_label and stype in ("double_angle_long", "double_angle_short"):
            show_double_total = False
        widget.set_section(stype, designation, show_double_total)

    def _populate_designations(self):
        angles = self.catalog.list_angles()

        self._fill_combo(self.bracing_section_combo, angles, "angle")
        self._fill_combo(self.top_bracket_size_combo, angles, "angle")
        self._fill_combo(self.bottom_bracket_size_combo, angles, "angle")

    def _map_section_type(self, label: str) -> str:
        mapping = {
            "Angle": "angle",
            "Double Angle (Long Leg)": "double_angle_long",
            "Double Angle (Short Leg)": "double_angle_short",
            "Channel": "channel",
            "Double Channel": "double_channel",
        }
        return mapping.get(label, "angle")

    def _on_bracing_type_changed(self, label: str):
        self._update_designations_for(self.bracing_section_combo, label)
        self._update_previews()

    def _on_top_bracket_type_changed(self, label: str):
        self._update_designations_for(self.top_bracket_size_combo, label)
        self._update_previews()

    def _on_bottom_bracket_type_changed(self, label: str):
        self._update_designations_for(self.bottom_bracket_size_combo, label)
        self._update_previews()

    def _update_designations_for(self, combo: QComboBox, type_label: str):
        stype = self._map_section_type(type_label)
        if stype in ("angle", "double_angle_long", "double_angle_short"):
            items = self.catalog.list_angles()
        else:
            items = self.catalog.list_channels()
        self._fill_combo(combo, items, stype)

    # ---- External API -----------------------------------------------------
    def reset_defaults(self):
        # Reset types to single angle and reload designations
        for combo in [self.bracing_section_type_combo, self.top_bracket_type_combo, self.bottom_bracket_type_combo]:
            combo.blockSignals(True)
            combo.setCurrentIndex(0)
            combo.blockSignals(False)
        self._populate_designations()
        # Select first designation for each
        for combo in [self.bracing_section_combo, self.top_bracket_size_combo, self.bottom_bracket_size_combo]:
            combo.setCurrentIndex(0 if combo.count() > 0 else -1)
        self._update_previews()

    def collect_data(self):
        return {
            "select_girders": self.select_girders_combo.currentText(),
            "member_id": self.member_id_combo.currentText(),
            "design": self.design_combo.currentText(),
            "bracing_type": self.bracing_type_combo.currentText(),
            "bracing_section_type": self.bracing_section_type_combo.currentText(),
            "bracing_section": self.bracing_section_combo.currentText(),
            "top_bracket_type": self.top_bracket_type_combo.currentText(),
            "top_bracket_size": self.top_bracket_size_combo.currentText(),
            "bottom_bracket_type": self.bottom_bracket_type_combo.currentText(),
            "bottom_bracket_size": self.bottom_bracket_size_combo.currentText(),
            "spacing": self.spacing_input.text(),
        }

