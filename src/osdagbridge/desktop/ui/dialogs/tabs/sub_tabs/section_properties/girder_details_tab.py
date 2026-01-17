from __future__ import annotations

import math
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from osdagbridge.core.utils.common import (
    VALUES_GIRDER_DESIGN_MODE,
    VALUES_GIRDER_SPAN_MODE,
    VALUES_GIRDER_SYMMETRY,
    VALUES_GIRDER_TYPE,
    VALUES_PROFILE_SCOPE,
    VALUES_TORSIONAL_RESTRAINT,
    VALUES_WARPING_RESTRAINT,
    VALUES_WEB_TYPE,
)
from osdagbridge.desktop.ui.dialogs.tabs.common import CheckableComboBox, apply_field_style
from osdagbridge.desktop.ui.utils.rolled_section_preview import RolledSectionPreview


DEFAULT_MEMBER_LENGTH_M = 30.0
DEFAULT_DISTANCE_START_M = 0.0


def _locate_database() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "core" / "data" / "ResourceFiles" / "Intg_osdag.sqlite"
        if candidate.exists():
            return candidate
    # Fall back to the repo-relative location even if it does not exist to avoid crashes.
    return current.parents[1] / "core" / "data" / "ResourceFiles" / "Intg_osdag.sqlite"


DB_PATH = _locate_database()


@dataclass(frozen=True)
class BeamSection:
    """Data container for rolled beam properties."""

    designation: str
    type_name: str
    mass_per_meter_kg: float
    area_cm2: float
    depth_mm: float
    flange_width_mm: float
    web_thickness_mm: float
    flange_thickness_mm: float
    root_radius_mm: float
    toe_radius_mm: float
    moment_of_inertia_zz_cm4: float
    moment_of_inertia_yy_cm4: float
    radius_of_gyration_z_cm: float
    radius_of_gyration_y_cm: float
    elastic_section_modulus_z_cm3: float
    elastic_section_modulus_y_cm3: float
    plastic_section_modulus_z_cm3: float
    plastic_section_modulus_y_cm3: float
    torsion_constant_cm4: float
    warping_constant_cm6: float


class GirderSectionCatalog:
    """Loads rolled girder information from the bundled SQLite database."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self._sections: Dict[str, BeamSection] = {}
        self._outlines: Dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if not self.db_path.exists():
            return
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT
                    Designation, Type, Mass, Area, D, B, tw, T,
                    R1, R2, Iz, Iy, rz, ry, Zz, Zy, Zpz, Zpy, It, Iw
                FROM Beams
                """
            )
            for row in cursor.fetchall():
                (
                    designation,
                    type_name,
                    mass,
                    area,
                    depth,
                    flange_width,
                    web_thickness,
                    flange_thickness,
                    r1,
                    r2,
                    iz,
                    iy,
                    rz,
                    ry,
                    zz,
                    zy,
                    zpz,
                    zpy,
                    it,
                    iw,
                ) = row
                section = BeamSection(
                    designation=str(designation).strip(),
                    type_name=str(type_name or "").strip(),
                    mass_per_meter_kg=float(mass or 0.0),
                    area_cm2=float(area or 0.0),
                    depth_mm=float(depth or 0.0),
                    flange_width_mm=float(flange_width or 0.0),
                    web_thickness_mm=float(web_thickness or 0.0),
                    flange_thickness_mm=float(flange_thickness or 0.0),
                    root_radius_mm=float(r1 or 0.0),
                    toe_radius_mm=float(r2 or 0.0),
                    moment_of_inertia_zz_cm4=float(iz or 0.0),
                    moment_of_inertia_yy_cm4=float(iy or 0.0),
                    radius_of_gyration_z_cm=float(rz or 0.0),
                    radius_of_gyration_y_cm=float(ry or 0.0),
                    elastic_section_modulus_z_cm3=float(zz or 0.0),
                    elastic_section_modulus_y_cm3=float(zy or 0.0),
                    plastic_section_modulus_z_cm3=float(zpz or 0.0),
                    plastic_section_modulus_y_cm3=float(zpy or 0.0),
                    torsion_constant_cm4=float(it or 0.0),
                    warping_constant_cm6=float(iw or 0.0),
                )
                self._sections[section.designation] = section
                self._outlines[section.designation] = {
                    "designation": section.designation,
                    "depth_mm": section.depth_mm,
                    "top_flange_width_mm": section.flange_width_mm,
                    "bottom_flange_width_mm": section.flange_width_mm,
                    "web_thickness_mm": section.web_thickness_mm,
                    "top_flange_thickness_mm": section.flange_thickness_mm,
                    "bottom_flange_thickness_mm": section.flange_thickness_mm,
                }
        finally:
            connection.close()

    def list_available_sections(self) -> Dict[str, BeamSection]:
        return dict(self._sections)

    def get_beam_profile(self, designation: str) -> Optional[BeamSection]:
        if not designation:
            return None
        return self._sections.get(designation.strip())

    def get_rolled_section(self, designation: str) -> Optional[dict]:
        if not designation:
            return None
        return self._outlines.get(designation.strip())


girder_properties = GirderSectionCatalog()


class GirderDetailsTab(QWidget):
    """Tab for Girder Details styled to match the provided reference."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.welded_rows = []
        self.rolled_rows = []
        self.symmetry_row = []
        self.web_type_row = []
        self.section_property_inputs = {}
        self.segment_chain = {}
        self._suppress_distance_updates = False
        self.available_girders = [f"G{i}" for i in range(1, 6)]
        self._girder_combo_connected = False
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
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)

        self.select_girder_combo = CheckableComboBox()
        self.select_girder_combo.addItems(["All"] + self.available_girders)
        apply_field_style(self.select_girder_combo)
        self._set_field_width(self.select_girder_combo)
        layout.addWidget(self._create_label("Select Girder:"), 0, 0, Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(self.select_girder_combo, 0, 1, 1, 3)

        self.span_combo = QComboBox()
        self.span_combo.addItems(VALUES_GIRDER_SPAN_MODE)
        apply_field_style(self.span_combo)
        self._set_field_width(self.span_combo)
        self.span_combo.currentTextChanged.connect(self._on_span_changed)
        layout.addWidget(self._create_label("Span:"), 1, 0, Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(self.span_combo, 1, 1, Qt.AlignLeft)

        self.member_id_input = QLineEdit()
        self.member_id_input.setPlaceholderText("G1-1")
        apply_field_style(self.member_id_input)
        self._set_field_width(self.member_id_input)
        self.member_id_input.textChanged.connect(self._on_member_id_changed)
        layout.addWidget(self._create_label("Member ID:"), 1, 2, Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(self.member_id_input, 1, 3, Qt.AlignLeft)

        self.distance_start_input = QLineEdit("0")
        self.distance_end_input = QLineEdit("30")
        apply_field_style(self.distance_start_input)
        apply_field_style(self.distance_end_input)
        self._set_field_width(self.distance_start_input, 80)
        self._set_field_width(self.distance_end_input, 80)
        self.distance_start_input.editingFinished.connect(self._on_distance_start_changed)
        self.distance_end_input.editingFinished.connect(self._on_distance_end_changed)
        distance_row = self._build_distance_row()
        layout.addWidget(self._create_label("Distance from left edge (m):"), 2, 0, Qt.AlignLeft | Qt.AlignTop)
        layout.addLayout(distance_row, 2, 1, Qt.AlignLeft)

        self.length_input = QLineEdit("30")
        apply_field_style(self.length_input)
        self._set_field_width(self.length_input)
        self.length_input.setReadOnly(True)
        self.length_input.textChanged.connect(self._on_length_changed)
        layout.addWidget(self._create_label("Length (m):"), 2, 2, Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(self.length_input, 2, 3, Qt.AlignLeft)

        self._setup_girder_selector()
        self._on_span_changed(self.span_combo.currentText())

        return card

    def _build_distance_row(self):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(16)

        def _build_column(line_edit, caption):
            column = QVBoxLayout()
            column.setContentsMargins(0, 0, 0, 0)
            column.setSpacing(2)
            column.addWidget(line_edit)
            label = self._create_small_label(caption)
            label.setAlignment(Qt.AlignCenter)
            column.addWidget(label, alignment=Qt.AlignCenter)
            return column

        row.addLayout(_build_column(self.distance_start_input, "Start"))
        row.addLayout(_build_column(self.distance_end_input, "End"))
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
        self.design_combo.addItems(VALUES_GIRDER_DESIGN_MODE)
        apply_field_style(self.design_combo)
        row = self._add_box_row(inputs_grid, 0, "Design:", self.design_combo)

        self.type_combo = QComboBox()
        self.type_combo.addItems(VALUES_GIRDER_TYPE)
        apply_field_style(self.type_combo)
        row = self._add_box_row(inputs_grid, row, "Type:", self.type_combo)

        self.symmetry_combo = QComboBox()
        self.symmetry_combo.addItems(VALUES_GIRDER_SYMMETRY)
        apply_field_style(self.symmetry_combo)
        row = self._add_box_row(inputs_grid, row, "Symmetry:", self.symmetry_combo, self.symmetry_row)

        self.total_depth_input = self._create_line_edit()
        row = self._add_box_row(
            inputs_grid,
            row,
            "Total Depth (d, mm):",
            self.total_depth_input,
            self.welded_rows,
        )

        self.web_thickness_combo = QComboBox()
        self.web_thickness_combo.addItems(VALUES_PROFILE_SCOPE)
        apply_field_style(self.web_thickness_combo)
        row = self._add_box_row(
            inputs_grid,
            row,
            "Web Thickness (w<sub>t</sub>, mm):",
            self.web_thickness_combo,
            self.welded_rows,
        )

        self.top_width_input = self._create_line_edit()
        row = self._add_box_row(
            inputs_grid,
            row,
            "Width of Top Flange (t<sub>fw</sub>, mm):",
            self.top_width_input,
            self.welded_rows,
        )

        self.top_thickness_combo = QComboBox()
        self.top_thickness_combo.addItems(VALUES_PROFILE_SCOPE)
        apply_field_style(self.top_thickness_combo)
        row = self._add_box_row(
            inputs_grid,
            row,
            "Top Flange Thickness (t<sub>ft</sub>, mm):",
            self.top_thickness_combo,
            self.welded_rows,
        )

        self.bottom_width_input = self._create_line_edit()
        row = self._add_box_row(
            inputs_grid,
            row,
            "Width of Bottom Flange (b<sub>fw</sub>, mm):",
            self.bottom_width_input,
            self.welded_rows,
        )

        self.bottom_thickness_combo = QComboBox()
        self.bottom_thickness_combo.addItems(VALUES_PROFILE_SCOPE)
        apply_field_style(self.bottom_thickness_combo)
        row = self._add_box_row(
            inputs_grid,
            row,
            "Bottom Flange Thickness (b<sub>ft</sub>, mm):",
            self.bottom_thickness_combo,
            self.welded_rows,
        )

        self.is_section_combo = QComboBox()
        self._populate_rolled_section_combo()
        apply_field_style(self.is_section_combo)
        self._add_box_row(inputs_grid, row, "IS Section:", self.is_section_combo, self.rolled_rows)

        section_inputs_layout.addLayout(inputs_grid)
        left_column_layout.addWidget(section_inputs_box)

        # Restraint/Web details box
        restraint_box = self._create_inner_box()
        restraint_layout = QVBoxLayout(restraint_box)
        restraint_layout.setContentsMargins(12, 6, 12, 10)
        restraint_layout.setSpacing(6)

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
        apply_field_style(self.torsion_combo)
        row = self._add_box_row(restraint_grid, 0, "Torsional Restraint:", self.torsion_combo)

        self.warping_combo = QComboBox()
        apply_field_style(self.warping_combo)
        row = self._add_box_row(restraint_grid, row, "Warping Restraint:", self.warping_combo)

        self.web_type_combo = QComboBox()
        apply_field_style(self.web_type_combo)
        self._add_box_row(restraint_grid, row, "Web Type*:", self.web_type_combo, self.web_type_row)

        restraint_layout.addLayout(restraint_grid)
        restraint_layout.addStretch(1)
        left_column_layout.addWidget(restraint_box)
        self._configure_restraint_fields()

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

        self.section_preview = RolledSectionPreview()
        image_layout.addWidget(self.section_preview, 1)

        self.preview_caption = QLabel("Provide girder inputs to preview")
        self.preview_caption.setAlignment(Qt.AlignCenter)
        self.preview_caption.setStyleSheet(
            "QLabel { font-size: 13px; font-weight: 700; color: #1e1e1e; border: none; padding-top: 6px; font-family: 'Ubuntu Sans', 'Segoe UI', sans-serif; }"
        )
        image_layout.addWidget(self.preview_caption)

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

        self.design_combo.currentTextChanged.connect(self._on_design_changed)
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        self.is_section_combo.currentTextChanged.connect(self._update_preview)
        for watcher in (self.total_depth_input, self.top_width_input, self.bottom_width_input):
            watcher.textChanged.connect(self._update_preview)
        self._on_design_changed(self.design_combo.currentText())
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

    def _setup_girder_selector(self):
        if not hasattr(self, "select_girder_combo"):
            return
        if not self._girder_combo_connected:
            if hasattr(self.select_girder_combo, "checkedItemsChanged"):
                self.select_girder_combo.checkedItemsChanged.connect(self._on_girders_selection_changed)
            else:
                self.select_girder_combo.currentTextChanged.connect(self._on_girders_selection_changed)
            self._girder_combo_connected = True
        self._on_girders_selection_changed()

    def _refresh_girder_combo_items(self, preferred_selection: Optional[List[str]] = None) -> None:
        if not hasattr(self, "select_girder_combo"):
            return
        if hasattr(self.select_girder_combo, "checked_items"):
            # Preserve multi-selection if possible.
            current_selection = preferred_selection or self.select_girder_combo.checked_items() or []
            desired = [g for g in current_selection if g in self.available_girders]

            block = self.select_girder_combo.blockSignals(True)
            try:
                # Temporarily suppress the internal toggle handler while rebuilding.
                if hasattr(self.select_girder_combo, "_updating_selection"):
                    self.select_girder_combo._updating_selection = True  # type: ignore[attr-defined]
                self.select_girder_combo.clear()
                self.select_girder_combo.addItems(["All"] + self.available_girders)

                if desired:
                    # Uncheck 'All', then check desired girders.
                    for row in range(self.select_girder_combo.model().rowCount()):
                        item = self.select_girder_combo.model().item(row)
                        if not item:
                            continue
                        if item.text().strip().lower() == "all":
                            item.setCheckState(Qt.Unchecked)
                        elif item.text() in desired:
                            item.setCheckState(Qt.Checked)
                        else:
                            item.setCheckState(Qt.Unchecked)
            finally:
                if hasattr(self.select_girder_combo, "_updating_selection"):
                    self.select_girder_combo._updating_selection = False  # type: ignore[attr-defined]
                self.select_girder_combo.blockSignals(block)
        else:
            current_text = self.select_girder_combo.currentText().strip()
            current_selection = preferred_selection or []
            candidate = next((girder for girder in current_selection if girder in self.available_girders), None)
            if not candidate and current_text in self.available_girders:
                candidate = current_text

            block = self.select_girder_combo.blockSignals(True)
            self.select_girder_combo.clear()
            self.select_girder_combo.addItems(["All"] + self.available_girders)
            if candidate:
                index = self.select_girder_combo.findText(candidate, Qt.MatchFixedString)
                self.select_girder_combo.setCurrentIndex(index if index != -1 else 0)
            else:
                self.select_girder_combo.setCurrentIndex(0)
            self.select_girder_combo.blockSignals(block)

    def _on_girders_selection_changed(self, *args):
        if self.span_combo.currentText() == "Full Length":
            self._update_member_id_edit_state()
            return
        current_text = self.member_id_input.text().strip()
        if not self._is_valid_segment_id(current_text):
            default_id = self._default_member_segment_id()
            self._set_member_id_text(default_id)
        self._update_member_id_edit_state()

    def _get_selected_girders(self):
        if not hasattr(self, "select_girder_combo"):
            return self.available_girders.copy()
        if hasattr(self.select_girder_combo, "checked_items"):
            # In this widget, checked_items() returns [] when "All" is selected.
            checked = [g for g in self.select_girder_combo.checked_items() if g in self.available_girders]
            return checked or self.available_girders.copy()

        current = self.select_girder_combo.currentText().strip()
        if not current or current.lower() == "all":
            return self.available_girders.copy()
        if current in self.available_girders:
            return [current]
        return self.available_girders.copy()

    def _default_member_segment_id(self, girders=None):
        girders = girders or self._get_selected_girders()
        base = girders[0] if girders else "G1"
        return f"{base}-1"

    def _set_member_id_text(self, value, block_signals=False):
        if block_signals:
            previous = self.member_id_input.blockSignals(True)
            self.member_id_input.setText(value)
            self.member_id_input.blockSignals(previous)
        else:
            self.member_id_input.setText(value)

    def _is_valid_segment_id(self, member_id):
        if not member_id or "-" not in member_id:
            return False
        base, index = self._split_member_id(member_id)
        return bool(base and isinstance(index, int))

    def _update_member_id_edit_state(self):
        is_full_span = self.span_combo.currentText() == "Full Length"
        self.member_id_input.setReadOnly(is_full_span)
        if is_full_span:
            girders = self._get_selected_girders()
            display = ", ".join(girders) if girders else "G1"
            self._set_member_id_text(display, block_signals=True)
        else:
            current_text = self.member_id_input.text().strip()
            if not self._is_valid_segment_id(current_text):
                default_id = self._default_member_segment_id()
                self._set_member_id_text(default_id)
        self._update_distance_field_states()

    def _on_design_changed(self, text):
        is_custom = text.lower() == "customized"
        toggle_targets = (
            self.type_combo,
            self.symmetry_combo,
            self.total_depth_input,
            self.top_width_input,
            self.bottom_width_input,
        )
        for widget in toggle_targets:
            widget.setEnabled(is_custom)
        if not is_custom:
            self._lock_type_to_welded()
            self._reset_section_state()
        self._apply_type_state()

    def _on_type_changed(self, text):
        self._apply_type_state()
        self._update_preview()

    def _apply_type_state(self):
        is_welded = self.type_combo.currentText().lower() == "welded"
        is_custom = self.design_combo.currentText().lower() == "customized"

        self._set_row_visibility(self.welded_rows, is_welded)
        self._set_row_visibility(self.rolled_rows, not is_welded)

        for label, widget in self.symmetry_row:
            label.setVisible(is_welded)
            widget.setVisible(is_welded)
        self.symmetry_combo.setEnabled(is_welded and is_custom)

        plate_widgets = (
            self.total_depth_input,
            self.web_thickness_combo,
            self.top_width_input,
            self.top_thickness_combo,
            self.bottom_width_input,
            self.bottom_thickness_combo,
        )
        for widget in plate_widgets:
            widget.setEnabled(is_welded and is_custom)
            widget.setVisible(is_welded)

        for label, widget in self.web_type_row:
            label.setVisible(is_welded)
            widget.setVisible(is_welded)
            widget.setEnabled(is_welded and is_custom)

        self.is_section_combo.setVisible(not is_welded)
        self.is_section_combo.setEnabled(not is_welded)

    def _lock_type_to_welded(self):
        welded_index = self.type_combo.findText("Welded", Qt.MatchFixedString)
        if welded_index != -1 and self.type_combo.currentIndex() != welded_index:
            previous = self.type_combo.blockSignals(True)
            self.type_combo.setCurrentIndex(welded_index)
            self.type_combo.blockSignals(previous)

    def _reset_section_state(self):
        for widget in (self.total_depth_input, self.top_width_input, self.bottom_width_input):
            previous = widget.blockSignals(True)
            widget.clear()
            widget.blockSignals(previous)
        self._update_preview()

    def _update_distance_field_states(self):
        member_id = self.member_id_input.text().strip()
        is_full_span = self.span_combo.currentText() == "Full Length"
        if is_full_span:
            self.distance_start_input.setReadOnly(True)
            self.distance_end_input.setReadOnly(True)
            return
        if not self._is_valid_segment_id(member_id):
            self.distance_start_input.setReadOnly(True)
            self.distance_end_input.setReadOnly(True)
            return
        self.distance_start_input.setReadOnly(self._is_first_segment(member_id))
        self.distance_end_input.setReadOnly(False)

    def _on_span_changed(self, span_text):
        is_full = span_text == "Full Length"
        self.length_input.setReadOnly(not is_full)
        if is_full:
            self._apply_full_length_distances()
        else:
            member_id = self.member_id_input.text().strip()
            if not self._is_valid_segment_id(member_id):
                member_id = self._default_member_segment_id()
                self._set_member_id_text(member_id)
            self._load_segment_distances(member_id)
        self._update_member_id_edit_state()

    def _on_length_changed(self, _):
        if self.span_combo.currentText() == "Full Length":
            self._apply_full_length_distances()

    def _apply_full_length_distances(self):
        self._suppress_distance_updates = True
        try:
            total_span = self._get_total_span()
            self._set_line_edit_value(self.distance_start_input, 0.0)
            self._set_line_edit_value(self.distance_end_input, total_span)
        finally:
            self._suppress_distance_updates = False

    def _on_member_id_changed(self, member_id):
        member_id = member_id.strip()
        if not member_id or self.span_combo.currentText() == "Full Length":
            return
        if not self._is_valid_segment_id(member_id):
            self._update_distance_field_states()
            return
        if self._is_first_segment(member_id):
            self._update_segment_record(member_id, start=0.0)
        else:
            previous_id = self._get_previous_segment_id(member_id)
            previous_end = self.segment_chain.get(previous_id, {}).get("end") if previous_id else None
            if previous_end is not None:
                self._update_segment_record(member_id, start=previous_end)
        self._load_segment_distances(member_id)
        self._update_distance_field_states()

    def _on_distance_start_changed(self):
        if self._suppress_distance_updates:
            return
        current_id = self.member_id_input.text().strip()
        if not current_id or not self._is_valid_segment_id(current_id):
            return
        if self._is_first_segment(current_id):
            self._suppress_distance_updates = True
            try:
                self._set_line_edit_value(self.distance_start_input, 0.0)
            finally:
                self._suppress_distance_updates = False
            self._update_segment_record(current_id, start=0.0)
            return
        value = self._parse_float(self.distance_start_input.text()) or 0.0
        self._update_segment_record(current_id, start=value)

    def _on_distance_end_changed(self):
        if self._suppress_distance_updates:
            return
        current_id = self.member_id_input.text().strip()
        if not current_id or self.span_combo.currentText() == "Full Length" or not self._is_valid_segment_id(current_id):
            return
        end_value = self._parse_float(self.distance_end_input.text())
        if end_value is None:
            end_value = 0.0

        start_value = self._parse_float(self.distance_start_input.text())
        if start_value is None:
            start_value = self.segment_chain.get(current_id, {}).get("start")
        if start_value is None and self._is_first_segment(current_id):
            start_value = 0.0

        if start_value is not None:
            self._update_segment_record(current_id, start=start_value)
        self._update_segment_record(current_id, end=end_value)
        self._propagate_next_segment_start(current_id, end_value)

    def _propagate_next_segment_start(self, member_id, next_start_value):
        next_id = self._get_next_segment_id(member_id)
        if not next_id:
            return
        self._update_segment_record(next_id, start=next_start_value)
        if next_id == self.member_id_input.text().strip() and self.span_combo.currentText() != "Full Length":
            self._load_segment_distances(next_id)

    def _load_segment_distances(self, member_id):
        if not member_id or not self._is_valid_segment_id(member_id):
            return
        record = self.segment_chain.setdefault(member_id, {})
        if self._is_first_segment(member_id):
            record.setdefault("start", 0.0)
        elif "start" not in record:
            previous_id = self._get_previous_segment_id(member_id)
            if previous_id:
                previous = self.segment_chain.get(previous_id, {})
                if "end" in previous:
                    record["start"] = previous["end"]

        self._suppress_distance_updates = True
        try:
            if "start" in record:
                self._set_line_edit_value(self.distance_start_input, record["start"])
            else:
                self.distance_start_input.clear()
            if "end" in record:
                self._set_line_edit_value(self.distance_end_input, record["end"])
            else:
                self.distance_end_input.clear()
        finally:
            self._suppress_distance_updates = False

    def _update_segment_record(self, member_id, start=None, end=None):
        if not member_id or not self._is_valid_segment_id(member_id):
            return
        record = self.segment_chain.setdefault(member_id, {})
        if start is not None:
            record["start"] = start
        if end is not None:
            record["end"] = end

    def _get_total_span(self):
        return self._parse_float(self.length_input.text()) or 0.0

    def _is_first_segment(self, member_id):
        _, index = self._split_member_id(member_id)
        return index == 1

    def _get_next_segment_id(self, member_id):
        base, index = self._split_member_id(member_id)
        if base is None or index is None:
            return None
        return f"{base}-{index + 1}"

    def _get_previous_segment_id(self, member_id):
        base, index = self._split_member_id(member_id)
        if base is None or index is None or index <= 1:
            return None
        return f"{base}-{index - 1}"

    def _split_member_id(self, member_id):
        if "-" not in member_id:
            return member_id, None
        base, index = member_id.rsplit("-", 1)
        try:
            return base, int(index)
        except ValueError:
            return base, None

    def _set_line_edit_value(self, line_edit, value):
        if value is None:
            return
        text = f"{value:.3f}".rstrip("0").rstrip(".")
        if not text:
            text = "0"
        previous_state = line_edit.blockSignals(True)
        line_edit.setText(text)
        line_edit.blockSignals(previous_state)

    def validate_member_properties(self) -> bool:
        if self.design_combo.currentText() != "Customized":
            return True
        required_fields = [
            (self.total_depth_input, "Total Depth (d, mm)"),
            (self.top_width_input, "Width of Top Flange (t_fw, mm)"),
            (self.bottom_width_input, "Width of Bottom Flange (b_fw, mm)"),
        ]
        missing = []
        for field, label in required_fields:
            value = self._parse_float(field.text())
            if value is None or value <= 0:
                missing.append(label)
        if missing:
            QMessageBox.critical(
                self,
                "Incomplete Girder Inputs",
                f"Please provide valid values for: {', '.join(missing)}.",
            )
            return False
        return True

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

    def _populate_rolled_section_combo(self):
        designations = sorted(girder_properties.list_available_sections().keys())
        if not designations:
            designations = [
                "ISMB 500", "ISMB 550", "ISMB 600",
                "ISWB 500", "ISWB 550", "ISWB 600",
            ]
        self.is_section_combo.clear()
        self.is_section_combo.addItems(designations)

    def _configure_restraint_fields(self):
        torsion_items = self._constant_items("VALUES_TORSIONAL_RESTRAINT")
        warping_items = self._constant_items("VALUES_WARPING_RESTRAINT")
        web_type_items = self._constant_items("VALUES_WEB_TYPE")

        self._reload_combo_items(self.torsion_combo, torsion_items)
        self._reload_combo_items(self.warping_combo, warping_items)
        self._reload_combo_items(self.web_type_combo, web_type_items)

    @staticmethod
    def _reload_combo_items(combo, items):
        block = combo.blockSignals(True)
        combo.clear()
        combo.addItems(items)
        combo.setCurrentIndex(0 if items else -1)
        combo.blockSignals(block)

    @staticmethod
    def _constant_items(constant_name):
        return list(globals().get(constant_name, []))

    def _update_preview(self):
        if not hasattr(self, "section_preview"):
            return

        is_welded = self.type_combo.currentText().lower() == "welded"
        if is_welded:
            dims = self._gather_welded_dimensions()
            caption = "Welded girder preview" if dims else "Enter depth and flange widths"
            if dims:
                self.section_preview.set_dimensions(
                    depth_mm=dims["depth_mm"],
                    flange_width_mm=dims["top_flange_width_mm"],
                    bottom_flange_width_mm=dims["bottom_flange_width_mm"],
                    web_thickness_mm=dims["web_thickness_mm"],
                    flange_thickness_mm=dims["top_flange_thickness_mm"],
                    bottom_flange_thickness_mm=dims["bottom_flange_thickness_mm"],
                    show_welds=True,
                )
            else:
                self.section_preview.clear()
        else:
            designation = self.is_section_combo.currentText()
            beam = girder_properties.get_beam_profile(designation)
            outline = girder_properties.get_rolled_section(designation) if beam is None else None
            has_data = bool(beam or outline)
            caption = f"Rolled section • {designation}" if has_data else "Rolled section unavailable"
            if beam:
                self.section_preview.set_section(beam)
            elif outline:
                self.section_preview.set_dimensions(
                    depth_mm=outline["depth_mm"],
                    flange_width_mm=outline["top_flange_width_mm"],
                    bottom_flange_width_mm=outline["bottom_flange_width_mm"],
                    web_thickness_mm=outline["web_thickness_mm"],
                    flange_thickness_mm=outline["top_flange_thickness_mm"],
                    bottom_flange_thickness_mm=outline["bottom_flange_thickness_mm"],
                )
            else:
                self.section_preview.clear()

        if hasattr(self, "preview_caption"):
            self.preview_caption.setText(caption)
        self._update_section_properties()

    def _gather_welded_dimensions(self):
        depth = self._parse_float(self.total_depth_input.text())
        top_width = self._parse_float(self.top_width_input.text())
        bottom_width = self._parse_float(self.bottom_width_input.text()) or top_width

        if not depth or not top_width or not bottom_width:
            return None

        web_thickness = max(8.0, depth * 0.02)
        flange_thickness = max(10.0, depth * 0.03)

        return {
            "designation": "Custom Welded Girder",
            "section_type": "welded",
            "depth_mm": depth,
            "top_flange_width_mm": top_width,
            "bottom_flange_width_mm": bottom_width,
            "web_thickness_mm": web_thickness,
            "top_flange_thickness_mm": flange_thickness,
            "bottom_flange_thickness_mm": flange_thickness,
        }

    def _update_section_properties(self):
        if not self.section_property_inputs:
            return
        values = None
        if self.type_combo.currentText().lower() == "welded":
            dims = self._gather_welded_dimensions()
            if dims:
                values = self._compute_welded_properties(dims)
        else:
            designation = self.is_section_combo.currentText()
            values = self._fetch_rolled_properties(designation)
        if values:
            self._apply_section_properties(values)
        else:
            self._clear_section_properties()

    def _fetch_rolled_properties(self, designation):
        if not designation:
            return None
        beam = girder_properties.get_beam_profile(designation)
        if not beam:
            return None
        values = {
            "Mass, M (Kg/m)": beam.mass_per_meter_kg,
            "Sectional Area, a (cm2)": beam.area_cm2,
            "2nd Moment of Area, Iz (cm4)": beam.moment_of_inertia_zz_cm4,
            "2nd Moment of Area, Iy (cm4)": beam.moment_of_inertia_yy_cm4,
            "Radius of Gyration, rz (cm)": beam.radius_of_gyration_z_cm,
            "Radius of Gyration, ry (cm)": beam.radius_of_gyration_y_cm,
            "Elastic Modulus, Zz (cm3)": beam.elastic_section_modulus_z_cm3,
            "Elastic Modulus, Zy (cm3)": beam.elastic_section_modulus_y_cm3,
            "Plastic Modulus, Zuz (cm3)": beam.plastic_section_modulus_z_cm3,
            "Plastic Modulus, Zuy (cm3)": beam.plastic_section_modulus_y_cm3,
            "Torsion Constant, It (cm4)": beam.torsion_constant_cm4,
            "Warping Constant, Iw (cm6)": beam.warping_constant_cm6,
        }
        area = values.get("Sectional Area, a (cm2)")
        iz = values.get("2nd Moment of Area, Iz (cm4)")
        iy = values.get("2nd Moment of Area, Iy (cm4)")
        if values.get("Radius of Gyration, rz (cm)") is None and area and iz:
            values["Radius of Gyration, rz (cm)"] = math.sqrt(iz / area)
        if values.get("Radius of Gyration, ry (cm)") is None and area and iy:
            values["Radius of Gyration, ry (cm)"] = math.sqrt(iy / area)
        return values

    def _compute_welded_properties(self, dims):
        depth = dims["depth_mm"]
        top_width = dims["top_flange_width_mm"]
        bottom_width = dims["bottom_flange_width_mm"]
        web_thickness = dims["web_thickness_mm"]
        top_thickness = dims["top_flange_thickness_mm"]
        bottom_thickness = dims["bottom_flange_thickness_mm"]

        h_web = max(depth - top_thickness - bottom_thickness, 1.0)
        area_top = top_width * top_thickness
        area_bottom = bottom_width * bottom_thickness
        area_web = web_thickness * h_web
        area_total_mm2 = area_top + area_bottom + area_web
        area_cm2 = area_total_mm2 / 100.0
        mass_kg_per_m = (area_total_mm2 / 1_000_000.0) * 7850.0

        iz_web = (web_thickness * h_web ** 3) / 12.0
        iz_top = (top_width * top_thickness ** 3) / 12.0
        iz_bottom = (bottom_width * bottom_thickness ** 3) / 12.0
        distance_top = h_web / 2.0 + top_thickness / 2.0
        distance_bottom = h_web / 2.0 + bottom_thickness / 2.0
        iz_top += area_top * distance_top ** 2
        iz_bottom += area_bottom * distance_bottom ** 2
        iz_cm4 = (iz_web + iz_top + iz_bottom) / 10000.0

        iy_web = (h_web * web_thickness ** 3) / 12.0
        iy_top = (top_thickness * top_width ** 3) / 12.0
        iy_bottom = (bottom_thickness * bottom_width ** 3) / 12.0
        iy_cm4 = (iy_web + iy_top + iy_bottom) / 10000.0

        rz_cm = math.sqrt(iz_cm4 / area_cm2) if area_cm2 > 0 else None
        ry_cm = math.sqrt(iy_cm4 / area_cm2) if area_cm2 > 0 else None

        depth_cm = depth / 10.0
        width_cm = max(top_width, bottom_width) / 10.0
        zz_cm3 = iz_cm4 / (depth_cm / 2.0) if depth_cm > 0 else None
        zy_cm3 = iy_cm4 / (width_cm / 2.0) if width_cm > 0 else None

        zpl_major = (
            area_top * distance_top +
            area_bottom * distance_bottom +
            (web_thickness * h_web ** 2) / 4.0
        ) / 1000.0
        zpl_minor = (
            (top_thickness * top_width ** 2) / 4.0 +
            (bottom_thickness * bottom_width ** 2) / 4.0 +
            (h_web * web_thickness ** 2) / 4.0
        ) / 1000.0

        torsion_constant_cm4 = (
            (top_width * top_thickness ** 3) / 3.0 +
            (bottom_width * bottom_thickness ** 3) / 3.0 +
            (h_web * web_thickness ** 3) / 3.0
        ) / 10000.0

        warping_constant_cm6 = (
            ((top_width * top_thickness ** 3) + (bottom_width * bottom_thickness ** 3)) * h_web ** 2 / 24.0
        ) / 1_000_000.0

        return {
            "Mass, M (Kg/m)": mass_kg_per_m,
            "Sectional Area, a (cm2)": area_cm2,
            "2nd Moment of Area, Iz (cm4)": iz_cm4,
            "2nd Moment of Area, Iy (cm4)": iy_cm4,
            "Radius of Gyration, rz (cm)": rz_cm,
            "Radius of Gyration, ry (cm)": ry_cm,
            "Elastic Modulus, Zz (cm3)": zz_cm3,
            "Elastic Modulus, Zy (cm3)": zy_cm3,
            "Plastic Modulus, Zuz (cm3)": zpl_major,
            "Plastic Modulus, Zuy (cm3)": zpl_minor,
            "Torsion Constant, It (cm4)": torsion_constant_cm4,
            "Warping Constant, Iw (cm6)": warping_constant_cm6,
        }

    def _apply_section_properties(self, values):
        for label, widget in self.section_property_inputs.items():
            display = self._format_property_value(values.get(label))
            previous = widget.blockSignals(True)
            widget.setText(display)
            widget.blockSignals(previous)

    def _clear_section_properties(self):
        for widget in self.section_property_inputs.values():
            previous = widget.blockSignals(True)
            widget.clear()
            widget.blockSignals(previous)

    @staticmethod
    def _format_property_value(value):
        if value is None:
            return ""
        if isinstance(value, (int, float)):
            return f"{value:.2f}"
        return str(value)

    @staticmethod
    def _parse_float(text):
        try:
            return float(text)
        except (TypeError, ValueError):
            return None

    def _segment_belongs_to_available_girder(self, member_id: str) -> bool:
        if not member_id:
            return False
        girder, _ = self._split_member_id(member_id)
        return girder in self.available_girders

    def set_girder_count(self, count: Optional[int]) -> None:
        if not hasattr(self, "select_girder_combo"):
            return
        try:
            total = int(count) if count is not None else len(self.available_girders)
        except (TypeError, ValueError):
            total = len(self.available_girders)
        total = max(1, total)
        previous_selection = self._get_selected_girders()
        self.available_girders = [f"G{i}" for i in range(1, total + 1)]
        self.segment_chain = {
            member_id: dict(values)
            for member_id, values in self.segment_chain.items()
            if self._segment_belongs_to_available_girder(member_id)
        }
        self._refresh_girder_combo_items(previous_selection)
        self._set_member_id_text(self._default_member_segment_id(), block_signals=True)
        self._update_member_id_edit_state()

    def reset_defaults(self) -> None:
        self.segment_chain.clear()
        self._refresh_girder_combo_items()

        def _reset_combo(combo: QComboBox, index: int = 0):
            previous = combo.blockSignals(True)
            combo.setCurrentIndex(index if combo.count() > index >= 0 else 0)
            combo.blockSignals(previous)

        for combo in (
            self.span_combo,
            self.design_combo,
            self.type_combo,
            self.symmetry_combo,
            self.web_thickness_combo,
            self.top_thickness_combo,
            self.bottom_thickness_combo,
            self.torsion_combo,
            self.warping_combo,
            self.web_type_combo,
        ):
            _reset_combo(combo)

        if self.is_section_combo.count() > 0:
            _reset_combo(self.is_section_combo)

        self._set_line_edit_value(self.distance_start_input, DEFAULT_DISTANCE_START_M)
        self._set_line_edit_value(self.distance_end_input, DEFAULT_MEMBER_LENGTH_M)
        self._set_line_edit_value(self.length_input, DEFAULT_MEMBER_LENGTH_M)
        self._set_member_id_text(self._default_member_segment_id(), block_signals=True)

        for field in (
            self.total_depth_input,
            self.top_width_input,
            self.bottom_width_input,
        ):
            previous = field.blockSignals(True)
            field.clear()
            field.blockSignals(previous)

        self._on_design_changed(self.design_combo.currentText())
        self._on_type_changed(self.type_combo.currentText())
        self._update_preview()
        self._update_section_properties()
        self._update_member_id_edit_state()

    def collect_data(self) -> dict:
        welded_inputs = {
            "total_depth_mm": self.total_depth_input.text().strip(),
            "top_flange_width_mm": self.top_width_input.text().strip(),
            "bottom_flange_width_mm": self.bottom_width_input.text().strip(),
            "web_thickness_mode": self.web_thickness_combo.currentText(),
            "top_thickness_mode": self.top_thickness_combo.currentText(),
            "bottom_thickness_mode": self.bottom_thickness_combo.currentText(),
        }
        properties_snapshot = {
            label: field.text().strip()
            for label, field in self.section_property_inputs.items()
        }
        return {
            "selected_girders": self._get_selected_girders(),
            "span_mode": self.span_combo.currentText(),
            "member_id": self.member_id_input.text().strip(),
            "distance_start_m": self._parse_float(self.distance_start_input.text()),
            "distance_end_m": self._parse_float(self.distance_end_input.text()),
            "length_m": self._parse_float(self.length_input.text()),
            "design_mode": self.design_combo.currentText(),
            "girder_type": self.type_combo.currentText(),
            "symmetry": self.symmetry_combo.currentText(),
            "torsional_restraint": self.torsion_combo.currentText(),
            "warping_restraint": self.warping_combo.currentText(),
            "web_type": self.web_type_combo.currentText(),
            "rolled_section": self.is_section_combo.currentText(),
            "welded_inputs": welded_inputs,
            "segment_chain": {
                key: {"start": value.get("start"), "end": value.get("end")}
                for key, value in self.segment_chain.items()
            },
            "section_properties": properties_snapshot,
        }
