"""End diaphragm section-properties UI.

This tab supports Cross Bracing, Rolled Beam and Welded Beam views.
Rolled/Welded views render a live section preview and auto-fill section
properties, matching the behavior used in the Girder tab.
"""

import math
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
from osdagbridge.desktop.ui.utils.rolled_section_preview import RolledSectionPreview
from osdagbridge.desktop.ui.widgets.section_viewer import SectionCatalog, SectionPreviewWidget

# Reuse the same rolled section catalog that backs the Girder tab.
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.girder_details_tab import (  # noqa: E501
    girder_properties,
)

class EndDiaphragmDetailsTab(QWidget):
    """Tab for End Diaphragm Details with type-specific layouts"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Cross bracing uses angle/channel section previews backed by the Osdag DB.
        self._cross_catalog = SectionCatalog()
        self._cross_previews = {}
        self.cross_right_column = None
        self.cross_design_combo = None
        self.cross_bracing_section_type_combo = None
        self.cross_bracing_section_combo = None
        self.cross_top_bracket_type_combo = None
        self.cross_top_bracket_size_combo = None
        self.cross_bottom_bracket_type_combo = None
        self.cross_bottom_bracket_size_combo = None

        self._rolled_property_inputs = {}
        self._welded_property_inputs = {}
        self._rolled_preview = None
        self._welded_preview = None
        self._rolled_caption = None
        self._welded_caption = None
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
            field.setReadOnly(True)
            grid.addWidget(label, row, 0)
            grid.addWidget(field, row, 1)
            inputs[name] = field

        layout.addLayout(grid)
        return box, inputs

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

    def _apply_section_properties(self, inputs, values):
        for key, widget in inputs.items():
            previous = widget.blockSignals(True)
            widget.setText(self._format_property_value(values.get(key)))
            widget.blockSignals(previous)

    def _clear_section_properties(self, inputs):
        for widget in inputs.values():
            previous = widget.blockSignals(True)
            widget.clear()
            widget.blockSignals(previous)

    def _populate_rolled_sections(self, combo: QComboBox) -> None:
        designations = sorted(girder_properties.list_available_sections().keys())
        if not designations:
            designations = [
                "ISMB 500",
                "ISMB 550",
                "ISMB 600",
                "ISWB 500",
                "ISWB 550",
                "ISWB 600",
            ]
        block = combo.blockSignals(True)
        combo.clear()
        combo.addItems(designations)
        combo.setCurrentIndex(0 if designations else -1)
        combo.blockSignals(block)

    def _fetch_rolled_properties(self, designation: str):
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
        }

        area = values.get("Sectional Area, a (cm2)")
        iz = values.get("2nd Moment of Area, Iz (cm4)")
        iy = values.get("2nd Moment of Area, Iy (cm4)")
        if values.get("Radius of Gyration, rz (cm)") is None and area and iz:
            values["Radius of Gyration, rz (cm)"] = math.sqrt(iz / area)
        if values.get("Radius of Gyration, ry (cm)") is None and area and iy:
            values["Radius of Gyration, ry (cm)"] = math.sqrt(iy / area)
        return values

    def _gather_welded_dimensions(self):
        depth = self._parse_float(getattr(self, "welded_total_depth", QLineEdit()).text())
        top_width = self._parse_float(getattr(self, "welded_top_width", QLineEdit()).text())
        bottom_width = self._parse_float(getattr(self, "welded_bottom_width", QLineEdit()).text()) or top_width

        if not depth or not top_width or not bottom_width:
            return None

        # Match Girder welded behavior: infer thicknesses if not explicitly provided.
        web_thickness = max(8.0, depth * 0.02)
        flange_thickness = max(10.0, depth * 0.03)

        return {
            "designation": "Custom Welded End Diaphragm",
            "section_type": "welded",
            "depth_mm": depth,
            "top_flange_width_mm": top_width,
            "bottom_flange_width_mm": bottom_width,
            "web_thickness_mm": web_thickness,
            "top_flange_thickness_mm": flange_thickness,
            "bottom_flange_thickness_mm": flange_thickness,
        }

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

        iz_web = (web_thickness * h_web**3) / 12.0
        iz_top = (top_width * top_thickness**3) / 12.0
        iz_bottom = (bottom_width * bottom_thickness**3) / 12.0
        distance_top = h_web / 2.0 + top_thickness / 2.0
        distance_bottom = h_web / 2.0 + bottom_thickness / 2.0
        iz_top += area_top * distance_top**2
        iz_bottom += area_bottom * distance_bottom**2
        iz_cm4 = (iz_web + iz_top + iz_bottom) / 10000.0

        iy_web = (h_web * web_thickness**3) / 12.0
        iy_top = (top_thickness * top_width**3) / 12.0
        iy_bottom = (bottom_thickness * bottom_width**3) / 12.0
        iy_cm4 = (iy_web + iy_top + iy_bottom) / 10000.0

        rz_cm = math.sqrt(iz_cm4 / area_cm2) if area_cm2 > 0 else None
        ry_cm = math.sqrt(iy_cm4 / area_cm2) if area_cm2 > 0 else None

        depth_cm = depth / 10.0
        width_cm = max(top_width, bottom_width) / 10.0
        zz_cm3 = iz_cm4 / (depth_cm / 2.0) if depth_cm > 0 else None
        zy_cm3 = iy_cm4 / (width_cm / 2.0) if width_cm > 0 else None

        zpl_major = (
            area_top * distance_top + area_bottom * distance_bottom + (web_thickness * h_web**2) / 4.0
        ) / 1000.0
        zpl_minor = (
            (top_thickness * top_width**2) / 4.0
            + (bottom_thickness * bottom_width**2) / 4.0
            + (h_web * web_thickness**2) / 4.0
        ) / 1000.0

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
        }

    def _update_rolled_preview_and_props(self):
        if not self._rolled_preview:
            return

        designation = getattr(self, "rolled_is_section_combo", QComboBox()).currentText()
        beam = girder_properties.get_beam_profile(designation)
        outline = girder_properties.get_rolled_section(designation) if beam is None else None
        has_data = bool(beam or outline)
        caption = f"Rolled section • {designation}" if has_data else "Rolled section unavailable"

        if beam:
            self._rolled_preview.set_section(beam)
        elif outline:
            self._rolled_preview.set_dimensions(
                depth_mm=outline["depth_mm"],
                flange_width_mm=outline["top_flange_width_mm"],
                bottom_flange_width_mm=outline["bottom_flange_width_mm"],
                web_thickness_mm=outline["web_thickness_mm"],
                flange_thickness_mm=outline["top_flange_thickness_mm"],
                bottom_flange_thickness_mm=outline["bottom_flange_thickness_mm"],
            )
        else:
            self._rolled_preview.clear()

        if self._rolled_caption:
            self._rolled_caption.setText(caption)

        values = self._fetch_rolled_properties(designation)
        if values:
            self._apply_section_properties(self._rolled_property_inputs, values)
        else:
            self._clear_section_properties(self._rolled_property_inputs)

    def _update_welded_preview_and_props(self):
        if not self._welded_preview:
            return
        dims = self._gather_welded_dimensions()
        caption = "Welded section preview" if dims else "Enter depth and flange widths"

        if dims:
            self._welded_preview.set_dimensions(
                depth_mm=dims["depth_mm"],
                flange_width_mm=dims["top_flange_width_mm"],
                bottom_flange_width_mm=dims["bottom_flange_width_mm"],
                web_thickness_mm=dims["web_thickness_mm"],
                flange_thickness_mm=dims["top_flange_thickness_mm"],
                bottom_flange_thickness_mm=dims["bottom_flange_thickness_mm"],
                show_welds=True,
            )
            values = self._compute_welded_properties(dims)
            self._apply_section_properties(self._welded_property_inputs, values)
        else:
            self._welded_preview.clear()
            self._clear_section_properties(self._welded_property_inputs)

        if self._welded_caption:
            self._welded_caption.setText(caption)

    # ---- Cross bracing helpers (angle/channel previews) -----------------
    def _cross_map_section_type(self, label: str) -> str:
        mapping = {
            "Angle": "angle",
            "Double Angle (Long Leg)": "double_angle_long",
            "Double Angle (Short Leg)": "double_angle_short",
            "Channel": "channel",
            "Double Channel": "double_channel",
        }
        return mapping.get((label or "").strip(), "angle")

    def _cross_display_name_for(self, designation: str, section_type: str) -> str:
        name = (designation or "").strip()
        if section_type in ("angle", "double_angle_long", "double_angle_short"):
            name = name.lstrip("∠⌒⟡⟠").strip()
            if name and not name.upper().startswith("IS"):
                name = f"IS {name}"
        return name

    def _cross_fill_combo(self, combo: QComboBox, items, section_type: str) -> None:
        if combo is None:
            return
        block = combo.blockSignals(True)
        combo.clear()
        for des in items:
            combo.addItem(self._cross_display_name_for(des, section_type), des)
        combo.setCurrentIndex(0 if combo.count() > 0 else -1)
        combo.blockSignals(block)

    def _cross_update_designations_for(self, combo: QComboBox, type_label: str) -> None:
        stype = self._cross_map_section_type(type_label)
        if stype in ("angle", "double_angle_long", "double_angle_short"):
            items = self._cross_catalog.list_angles()
        else:
            items = self._cross_catalog.list_channels()
        self._cross_fill_combo(combo, items, stype)

    def _cross_populate_designations(self) -> None:
        angles = self._cross_catalog.list_angles()
        self._cross_fill_combo(self.cross_bracing_section_combo, angles, "angle")
        self._cross_fill_combo(self.cross_top_bracket_size_combo, angles, "angle")
        self._cross_fill_combo(self.cross_bottom_bracket_size_combo, angles, "angle")

    def _cross_set_preview(self, key: str, type_combo: QComboBox, size_combo: QComboBox) -> None:
        widget = self._cross_previews.get(key)
        if not widget:
            return
        stype = self._cross_map_section_type(type_combo.currentText())
        designation = size_combo.currentData() or size_combo.currentText()
        # Match CrossBracingDetailsTab behavior: for double angles, don't show total envelope.
        show_double_total = stype not in ("double_angle_long", "double_angle_short")
        widget.set_section(stype, designation, show_double_total)

    def _update_cross_previews(self) -> None:
        if not self.cross_design_combo:
            return

        is_custom = self.cross_design_combo.currentText() == "Customized"
        if not is_custom:
            for widget in self._cross_previews.values():
                widget.set_section("", "")
            return

        self._cross_set_preview(
            "bracing",
            self.cross_bracing_section_type_combo,
            self.cross_bracing_section_combo,
        )
        self._cross_set_preview(
            "top",
            self.cross_top_bracket_type_combo,
            self.cross_top_bracket_size_combo,
        )
        self._cross_set_preview(
            "bottom",
            self.cross_bottom_bracket_type_combo,
            self.cross_bottom_bracket_size_combo,
        )

    def _apply_cross_custom_mode(self, is_custom: bool) -> None:
        if self.cross_right_column is not None:
            self.cross_right_column.setVisible(is_custom)
        for widget in (
            self.cross_bracing_section_type_combo,
            self.cross_bracing_section_combo,
            self.cross_top_bracket_type_combo,
            self.cross_top_bracket_size_combo,
            self.cross_bottom_bracket_type_combo,
            self.cross_bottom_bracket_size_combo,
        ):
            if widget is not None:
                widget.setEnabled(is_custom)

    def _on_cross_design_changed(self, label: str) -> None:
        is_custom = (label or "").strip() == "Customized"
        self._apply_cross_custom_mode(is_custom)
        self._update_cross_previews()

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
        self.cross_design_combo = design_combo

        type_selector = QComboBox()
        type_selector.addItems(VALUES_END_DIAPHRAGM_TYPE)
        type_selector.setCurrentText("Cross Bracing")
        apply_field_style(type_selector)
        row = self._add_grid_row(grid, row, "Type:", type_selector)

        bracing_combo = QComboBox()
        bracing_combo.addItems(["K-Bracing", "X-Bracing", "Diagonal", "Horizontal"])
        apply_field_style(bracing_combo)
        row = self._add_grid_row(grid, row, "Type of Bracing:", bracing_combo)

        section_type_options = [
            "Angle",
            "Double Angle (Long Leg)",
            "Double Angle (Short Leg)",
            "Channel",
            "Double Channel",
        ]

        bracing_section_type = QComboBox()
        bracing_section_type.addItems(section_type_options)
        apply_field_style(bracing_section_type)
        row = self._add_grid_row(grid, row, "Bracing Section Type:", bracing_section_type)
        self.cross_bracing_section_type_combo = bracing_section_type

        bracing_section_size = QComboBox()
        apply_field_style(bracing_section_size)
        row = self._add_grid_row(grid, row, "Bracing Section:", bracing_section_size)
        self.cross_bracing_section_combo = bracing_section_size

        top_bracket_type = QComboBox()
        top_bracket_type.addItems(section_type_options)
        apply_field_style(top_bracket_type)
        row = self._add_grid_row(grid, row, "Top Bracket Section:", top_bracket_type)
        self.cross_top_bracket_type_combo = top_bracket_type

        top_bracket_size = QComboBox()
        apply_field_style(top_bracket_size)
        row = self._add_grid_row(grid, row, "Top Bracket Size:", top_bracket_size)
        self.cross_top_bracket_size_combo = top_bracket_size

        bottom_bracket_type = QComboBox()
        bottom_bracket_type.addItems(section_type_options)
        apply_field_style(bottom_bracket_type)
        row = self._add_grid_row(grid, row, "Bottom Bracket Section:", bottom_bracket_type)
        self.cross_bottom_bracket_type_combo = bottom_bracket_type

        bottom_bracket_size = QComboBox()
        apply_field_style(bottom_bracket_size)
        row = self._add_grid_row(grid, row, "Bottom Bracket Size:", bottom_bracket_size)
        self.cross_bottom_bracket_size_combo = bottom_bracket_size

        inputs_layout.addLayout(grid)
        inputs_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        left_layout.addWidget(inputs_box)
        left_layout.addStretch()

        layout.addWidget(left_column)

        right_column = QWidget()
        self.cross_right_column = right_column
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

        for key, title in [("bracing", "Bracing"), ("top", "Top Bracket"), ("bottom", "Bottom Bracket")]:
            preview_box = self._create_inner_box()
            preview_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            preview_layout = QVBoxLayout(preview_box)
            preview_layout.setContentsMargins(12, 8, 12, 8)
            preview_layout.setSpacing(6)
            # Make these preview titles bolder without affecting other headings
            preview_heading = QLabel(title)
            preview_heading.setStyleSheet("font-size: 12px; font-weight: 700; color: #4b4b4b; border: none;")
            preview_layout.addWidget(preview_heading)
            widget = SectionPreviewWidget()
            widget.setMinimumHeight(110)
            widget.setStyleSheet(
                "QWidget { border: 1px solid #d0d0d0; border-radius: 10px; background-color: #ffffff; }"
            )
            preview_layout.addWidget(widget)
            self._cross_previews[key] = widget
            right_layout.addWidget(preview_box)

        right_layout.addStretch()
        layout.addWidget(right_column)
        layout.setStretch(0, 3)
        layout.setStretch(1, 4)

        # Wire up dynamic designations + previews (same logic as CrossBracingDetailsTab).
        design_combo.currentTextChanged.connect(self._on_cross_design_changed)

        bracing_section_type.currentTextChanged.connect(
            lambda label: (self._cross_update_designations_for(bracing_section_size, label), self._update_cross_previews())
        )
        bracing_section_size.currentTextChanged.connect(self._update_cross_previews)

        top_bracket_type.currentTextChanged.connect(
            lambda label: (self._cross_update_designations_for(top_bracket_size, label), self._update_cross_previews())
        )
        top_bracket_size.currentTextChanged.connect(self._update_cross_previews)

        bottom_bracket_type.currentTextChanged.connect(
            lambda label: (self._cross_update_designations_for(bottom_bracket_size, label), self._update_cross_previews())
        )
        bottom_bracket_size.currentTextChanged.connect(self._update_cross_previews)

        self._cross_populate_designations()
        self._on_cross_design_changed(design_combo.currentText())
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
        apply_field_style(is_section_combo)
        self._populate_rolled_sections(is_section_combo)
        self._add_grid_row(grid, row, "IS Section:", is_section_combo)
        self.rolled_is_section_combo = is_section_combo

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

        self._rolled_preview = RolledSectionPreview()
        image_layout.addWidget(self._rolled_preview, 1)

        self._rolled_caption = QLabel("Select a rolled section")
        self._rolled_caption.setAlignment(Qt.AlignCenter)
        self._rolled_caption.setStyleSheet(
            "QLabel { font-size: 12px; font-weight: 700; color: #1e1e1e; border: none; padding-top: 6px; }"
        )
        image_layout.addWidget(self._rolled_caption)
        right_layout.addWidget(image_box)

        props_box, props_inputs = self._create_section_properties_box("Section Properties:")
        self._rolled_property_inputs = props_inputs
        props_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        right_layout.addWidget(props_box)
        right_layout.addStretch()

        layout.addWidget(right_column)

        is_section_combo.currentTextChanged.connect(self._update_rolled_preview_and_props)
        self._update_rolled_preview_and_props()
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
        total_depth.setValidator(QDoubleValidator(0, 1_000_000, 3))
        row = self._add_grid_row(grid, row, "Total Depth (mm):", total_depth)
        self.welded_total_depth = total_depth

        web_thick_combo = QComboBox()
        web_thick_combo.addItems(["All", "Custom"])
        apply_field_style(web_thick_combo)
        row = self._add_grid_row(grid, row, "Web Thickness (mm):", web_thick_combo)

        top_width = self._create_line_edit()
        top_width.setValidator(QDoubleValidator(0, 1_000_000, 3))
        row = self._add_grid_row(grid, row, "Width of Top Flange (mm):", top_width)
        self.welded_top_width = top_width

        top_thickness_combo = QComboBox()
        top_thickness_combo.addItems(["All", "Custom"])
        apply_field_style(top_thickness_combo)
        row = self._add_grid_row(grid, row, "Top Flange Thickness (mm):", top_thickness_combo)

        bottom_width = self._create_line_edit()
        bottom_width.setValidator(QDoubleValidator(0, 1_000_000, 3))
        row = self._add_grid_row(grid, row, "Width of Bottom Flange (mm):", bottom_width)
        self.welded_bottom_width = bottom_width

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

        self._welded_preview = RolledSectionPreview()
        image_layout.addWidget(self._welded_preview, 1)

        self._welded_caption = QLabel("Enter welded inputs to preview")
        self._welded_caption.setAlignment(Qt.AlignCenter)
        self._welded_caption.setStyleSheet(
            "QLabel { font-size: 12px; font-weight: 700; color: #1e1e1e; border: none; padding-top: 6px; }"
        )
        image_layout.addWidget(self._welded_caption)
        right_layout.addWidget(image_box)

        props_box, props_inputs = self._create_section_properties_box("Section Properties:")
        self._welded_property_inputs = props_inputs
        props_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        right_layout.addWidget(props_box)
        right_layout.addStretch()

        layout.addWidget(right_column)

        for watcher in (total_depth, top_width, bottom_width):
            watcher.textChanged.connect(self._update_welded_preview_and_props)
        self._update_welded_preview_and_props()
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

        # Refresh preview/properties for the active view.
        if target == "Cross Bracing":
            self._update_cross_previews()
        elif target == "Rolled Beam":
            self._update_rolled_preview_and_props()
        elif target == "Welded Beam":
            self._update_welded_preview_and_props()

