"""Auto-generated tab module extracted from additional_inputs."""
import sys
import os
import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTabBar, QLabel, QLineEdit,
    QComboBox, QGroupBox, QFormLayout, QPushButton, QScrollArea,
    QCheckBox, QMessageBox, QSizePolicy, QSpacerItem, QStackedWidget,
    QFrame, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QDialog, QSizePolicy, QSizeGrip
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QDoubleValidator, QIntValidator

from osdagbridge.core.bridge_types.plate_girder.bridge_geometry import CrossSectionLayout
from osdagbridge.core.utils.common import *
from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.typical_section.layout_tab import LayoutTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.typical_section.crash_barrier_tab import CrashBarrierTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.typical_section.median_tab import MedianTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.typical_section.railing_tab import RailingTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.typical_section.wearing_course_tab import WearingCourseTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.typical_section.lane_details_tab import LaneDetailsTab

class TypicalSectionDetailsTab(QWidget):
    """Sub-tab for Typical Section Details inputs"""

    footpath_changed = Signal(str)

    def __init__(self, footpath_value="None", carriageway_width=7.5, parent=None):
        super().__init__(parent)
        self.footpath_value = footpath_value
        self.carriageway_width = carriageway_width
        self.updating_fields = False
        self._updating_overall_width_display = False
        self.crash_barrier_count = 2  # Assume two crash barriers at carriageway edges
        self.overall_bridge_width_formula = (
            "OverallBridgeWidth = CrossSectionLayout.total_width = CarriagewayWidth + "
            "2 x CrashBarrierWidth + MedianWidth + (NoOfFootpaths x FootpathWidth) + "
            "(NoOfFootpaths x RailingWidth)"
        )
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
                background-color: white;
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

        self.layout_tab = LayoutTab(self)
        self.input_tabs.addTab(self.layout_tab, "Layout")

        self.crash_barrier_tab = CrashBarrierTab(self)
        self.input_tabs.addTab(self.crash_barrier_tab, "Crash Barrier")

        self.median_tab = MedianTab(self)
        self.input_tabs.addTab(self.median_tab, "Median")

        self.railing_tab = RailingTab(self)
        self.input_tabs.addTab(self.railing_tab, "Railing")

        self.wearing_course_tab = WearingCourseTab(self)
        self.input_tabs.addTab(self.wearing_course_tab, "Wearing Course")

        self.lane_details_tab = LaneDetailsTab(self)
        self.input_tabs.addTab(self.lane_details_tab, "Lane Details")

        input_layout.addWidget(self.input_tabs)
        main_layout.addWidget(input_container)

        self.deck_thickness.textChanged.connect(self.update_footpath_thickness)
        self.recalculate_girders()
        # Initialize crash barrier visibility/load state
        if hasattr(self, "crash_barrier_type"):
            self._update_crash_barrier_visibility(self.crash_barrier_type.currentText())
        if hasattr(self, "median_type"):
            self._update_median_visibility(self.median_type.currentText(), include_median=True)

    def _get_footpath_count(self):
        if self.footpath_value == "Both":
            return 2
        if self.footpath_value == "Single Sided":
            return 1
        return 0

    def _get_flange_width_limit(self):
        # Widths are defined elsewhere (Girder Details) in mm; if unavailable, assume 0
        top_width_mm = getattr(self, "top_flange_width_mm", 0) or 0
        bottom_width_mm = getattr(self, "bottom_flange_width_mm", 0) or 0
        return max(top_width_mm, bottom_width_mm) / 1000.0

    def _spacing_bounds(self, overall_width):
        min_spacing = 1.0
        max_spacing = max(min_spacing, overall_width - self._get_flange_width_limit())
        return min_spacing, max_spacing

    def _clamp(self, value, lo, hi):
        return max(lo, min(hi, value))

    def _parse_length_value(self, field, default=0.0, scale=1.0):
        try:
            text = field.text().strip() if field else ""
            if text:
                return float(text) / scale
        except (ValueError, AttributeError):
            pass
        return default

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

    def _calculate_overall_bridge_width(self):
        carriageway_width = float(self.carriageway_width) if self.carriageway_width else 0.0
        crash_barrier_width = self._parse_length_value(
            getattr(self, "crash_barrier_width", None),
            default=DEFAULT_CRASH_BARRIER_WIDTH,
        )
        footpath_width = self._parse_length_value(
            getattr(self, "footpath_width", None),
            default=0.0,
        )
        railing_width = self._parse_length_value(
            getattr(self, "railing_width", None),
            default=DEFAULT_RAILING_WIDTH,
            scale=1000.0,
        )
        median_width = self._parse_length_value(
            getattr(self, "median_width", None),
            default=0.0,
        )
        footpath_count = self._get_footpath_count()

        layout = CrossSectionLayout(
            carriageway_width=carriageway_width,
            crash_barrier_width=crash_barrier_width,
            railing_width=railing_width,
            footpath_width=footpath_width,
            median_width=median_width,
            no_of_footpaths=footpath_count,
        )
        return layout.total_width

    def _format_spacing(self, spacing):
        return f"{spacing:.1f}"

    def _format_overhang(self, overhang):
        return f"{overhang:.3f}"

    def _set_layout_fields(self, spacing, overhang, girders):
        self.updating_fields = True
        try:
            self.girder_spacing.setText(self._format_spacing(spacing))
            self.deck_overhang.setText(self._format_overhang(overhang))
            self.no_of_girders.setText(str(int(girders)))
        finally:
            self.updating_fields = False

    def _deck_overhang_range(self, overall_width):
        if overall_width <= 0:
            return 0.0, 0.0
        return 0.0, overall_width / 2.0

    def _spacing_candidates_for_overhang(self, overall_width, overhang, spacing_bounds):
        spacing_min, spacing_max = spacing_bounds
        max_n = int(math.floor(overall_width / spacing_min) + 2) if spacing_min > 0 else 50
        target_spacing = self._parse_length_value(self.girder_spacing, default=DEFAULT_GIRDER_SPACING)
        best = None
        for n in range(1, max(2, max_n) + 1):
            if n == 1:
                # Formula reduces to overall_width = 2 * overhang
                required_overhang = overall_width / 2.0
                if abs(required_overhang - overhang) < 1e-6:
                    s_rounded = self._clamp(round(target_spacing, 1), spacing_min, spacing_max)
                    o_calc = (overall_width - (n - 1) * s_rounded) / 2.0
                    score = (0.0, abs(s_rounded - target_spacing), n)
                    best = (score, s_rounded, o_calc, n)
                continue

            raw_spacing = (overall_width - 2.0 * overhang) / (n - 1)
            if raw_spacing <= 0:
                continue
            s_rounded = self._clamp(round(raw_spacing, 1), spacing_min, spacing_max)
            o_calc = (overall_width - (n - 1) * s_rounded) / 2.0
            o_min, o_max = self._deck_overhang_range(overall_width)
            if o_calc < o_min - 1e-6 or o_calc > o_max + 1e-6:
                continue
            spacing_diff = abs(s_rounded - target_spacing)
            overhang_diff = abs(o_calc - overhang)
            score = (overhang_diff, spacing_diff, n)
            if best is None or score < best[0]:
                best = (score, s_rounded, o_calc, n)
        return best

    def _pick_n_for_spacing(self, overall_width, spacing, spacing_bounds):
        spacing_min, spacing_max = spacing_bounds
        spacing = self._clamp(round(spacing, 1), spacing_min, spacing_max)
        target_overhang = self._clamp(0.35 * spacing, *self._deck_overhang_range(overall_width))
        max_n = int(math.floor(overall_width / spacing) + 2) if spacing > 0 else 1
        best = None
        for n in range(1, max(2, max_n) + 1):
            if (n - 1) * spacing > overall_width + 1e-6:
                break
            overhang = (overall_width - (n - 1) * spacing) / 2.0
            o_min, o_max = self._deck_overhang_range(overall_width)
            if overhang < o_min - 1e-6 or overhang > o_max + 1e-6:
                continue
            score = (abs(overhang - target_overhang), abs(n - 2))
            if best is None or score < best[0]:
                best = (score, n, spacing, overhang)
        return best

    def _solve_layout(self, changed_field="width"):
        if self.updating_fields:
            return
        overall_width = self.get_overall_bridge_width()
        if overall_width <= 0:
            QMessageBox.warning(self, "Layout", "Overall bridge width must be positive.")
            return

        spacing_bounds = self._spacing_bounds(overall_width)
        spacing_input = self._parse_length_value(self.girder_spacing, default=DEFAULT_GIRDER_SPACING)
        overhang_input = self._parse_length_value(self.deck_overhang, default=0.35 * spacing_input)
        girders_input = None
        if self.no_of_girders.text():
            try:
                girders_input = int(self.no_of_girders.text())
            except ValueError:
                girders_input = None

        o_min, o_max = self._deck_overhang_range(overall_width)

        if changed_field == "spacing":
            pick = self._pick_n_for_spacing(overall_width, spacing_input, spacing_bounds)
            if not pick:
                QMessageBox.warning(self, "Layout", "Cannot satisfy constraints with the selected girder spacing.")
                self._update_overall_bridge_width_display()
                return
            _, n, spacing_use, overhang_use = pick
            self._set_layout_fields(spacing_use, overhang_use, n)
            self._update_overall_bridge_width_display()
            return

        if changed_field == "overhang":
            overhang_use = self._clamp(overhang_input, o_min, o_max)
            pick = self._spacing_candidates_for_overhang(overall_width, overhang_use, spacing_bounds)
            if not pick:
                QMessageBox.warning(self, "Layout", "Cannot satisfy constraints with the selected deck overhang.")
                self._update_overall_bridge_width_display()
                return
            _, spacing_use, overhang_resolved, n = pick
            self._set_layout_fields(spacing_use, overhang_resolved, n)
            self._update_overall_bridge_width_display()
            return

        if changed_field == "girders":
            if girders_input is None or girders_input < 1:
                QMessageBox.warning(self, "Layout", "Number of girders must be an integer greater than or equal to 1.")
                return
            n = girders_input
            if n == 1:
                overhang_use = overall_width / 2.0
                spacing_use = self._clamp(round(spacing_input, 1), *spacing_bounds)
                self._set_layout_fields(spacing_use, overhang_use, n)
                self._update_overall_bridge_width_display()
                return

            target_overhang = self._clamp(0.35 * spacing_input, o_min, o_max)
            raw_spacing = (overall_width - 2.0 * target_overhang) / (n - 1)
            spacing_use = self._clamp(round(raw_spacing, 1), *spacing_bounds)
            overhang_use = (overall_width - (n - 1) * spacing_use) / 2.0
            if overhang_use < o_min - 1e-6 or overhang_use > o_max + 1e-6:
                QMessageBox.warning(self, "Layout", "Cannot satisfy constraints with the selected number of girders.")
                return
            self._set_layout_fields(spacing_use, overhang_use, n)
            self._update_overall_bridge_width_display()
            return

        # Default / overall width change: try to keep current spacing if feasible
        pick = self._pick_n_for_spacing(overall_width, spacing_input, spacing_bounds)
        if not pick:
            # Fallback to default spacing
            pick = self._pick_n_for_spacing(overall_width, DEFAULT_GIRDER_SPACING, spacing_bounds)
        if pick:
            _, n, spacing_use, overhang_use = pick
            self._set_layout_fields(spacing_use, overhang_use, n)
        else:
            QMessageBox.warning(self, "Layout", "Cannot satisfy layout constraints for the current overall width.")
        self._update_overall_bridge_width_display()

    def _auto_compute_crash_barrier_load(self):
        barrier_type = self.crash_barrier_type.currentText() if hasattr(self, "crash_barrier_type") else ""
        if barrier_type.startswith("IRC 5 RCC"):
            try:
                density = float(self.crash_barrier_density.text()) if self.crash_barrier_density.text() else 0.0
                area = float(self.crash_barrier_area.text()) if self.crash_barrier_area.text() else 0.0
                load = density * area
                self.crash_barrier_load.setText(f"{load:.3f}")
            except:
                self.crash_barrier_load.clear()
        # For other types load is user-entered; do not overwrite

    def _is_metallic_barrier(self, barrier_type):
        return barrier_type.startswith("IRC 5 Metallic")

    def _is_rcc_barrier(self, barrier_type):
        return barrier_type.startswith("IRC 5 RCC") or barrier_type.startswith("IRC 5 High Containment RCC")

    def _update_crash_barrier_visibility(self, barrier_type):
        is_metallic = self._is_metallic_barrier(barrier_type)
        is_rcc = self._is_rcc_barrier(barrier_type)

        # Density & Area hidden for metallic
        for widget in [self.crash_barrier_density, self.crash_barrier_density_label, self.crash_barrier_area, self.crash_barrier_area_label]:
            widget.setVisible(not is_metallic)

        # Post spacing only for metallic
        for widget in [self.crash_barrier_post_spacing, self.crash_barrier_post_spacing_label]:
            widget.setVisible(is_metallic)

        # Load behavior
        self.crash_barrier_load.setEnabled(True)
        self.crash_barrier_load.setReadOnly(is_rcc)
        if is_rcc:
            self._auto_compute_crash_barrier_load()

    def _warn_if_custom_barrier(self, barrier_type):
        if barrier_type == "Custom":
            QMessageBox.warning(
                self,
                "Custom Crash Barrier",
                "Verify crash barrier design using IRC 6 Clause 206.6",
            )

    def _is_metallic_median(self, median_type):
        return median_type.startswith("IRC 5 Metallic")

    def _is_rcc_median(self, median_type):
        return median_type.startswith("IRC 5 RCC") or median_type.startswith("IRC 5 High Containment RCC")

    def _auto_compute_median_load(self):
        median_type = self.median_type.currentText() if hasattr(self, "median_type") else ""
        if self._is_rcc_median(median_type):
            try:
                density = float(self.median_density.text()) if self.median_density.text() else 0.0
                area = float(self.median_area.text()) if self.median_area.text() else 0.0
                load = density * area
                self.median_load.setText(f"{load:.3f}")
            except:
                self.median_load.clear()

    def on_median_type_changed(self, median_type):
        self._update_median_visibility(median_type, include_median=True)

    def _update_median_visibility(self, median_type, include_median=True):
        is_metallic = self._is_metallic_median(median_type)
        is_rcc = self._is_rcc_median(median_type)
        active = bool(include_median)

        # Gray-out: disable entire card when not included
        for widget in [
            self.median_type,
            self.median_density,
            self.median_width,
            self.median_height,
            self.median_area,
            self.median_load,
            self.median_post_spacing,
            self.median_density_label,
            self.median_area_label,
            self.median_post_spacing_label,
        ]:
            if widget is not None:
                widget.setEnabled(active)

        # Density & Area hidden for metallic
        for widget in [self.median_density, self.median_density_label, self.median_area, self.median_area_label]:
            if widget is not None:
                widget.setVisible(active and not is_metallic)

        # Post spacing only for metallic
        for widget in [self.median_post_spacing, self.median_post_spacing_label]:
            if widget is not None:
                widget.setVisible(active and is_metallic)

        # Load behavior
        self.median_load.setEnabled(active)
        self.median_load.setReadOnly(active and is_rcc)
        if active and is_rcc:
            self._auto_compute_median_load()

    def get_overall_bridge_width(self):
        try:
            return self._calculate_overall_bridge_width()
        except:
            return self.carriageway_width

    def _update_overall_bridge_width_display(self):
        if hasattr(self, "overall_bridge_width_display"):
            try:
                overall_width = self.get_overall_bridge_width()
                self._updating_overall_width_display = True
                self.overall_bridge_width_display.setText(f"{overall_width:.3f}")
                self._updating_overall_width_display = False
            except:
                self._updating_overall_width_display = False
                self.overall_bridge_width_display.clear()

    def _reject_overall_width_override(self, text):
        if self._updating_overall_width_display:
            return
        try:
            entered_value = float(text) if text else None
        except ValueError:
            entered_value = None

        expected_value = self._calculate_overall_bridge_width()
        if entered_value is None or abs(expected_value - entered_value) > 1e-6:
            if self.overall_bridge_width_display.hasFocus():
                QMessageBox.warning(
                    self,
                    "Overall Bridge Width Locked",
                    "Overall Bridge Width is auto-calculated using:\n"
                    f"{self.overall_bridge_width_formula}",
                )
            self._update_overall_bridge_width_display()

    def recalculate_girders(self):
        self._update_overall_bridge_width_display()
        self._solve_layout("width")

    def on_girder_spacing_changed(self):
        if not self.updating_fields:
            self._solve_layout("spacing")

    def on_deck_overhang_changed(self):
        if not self.updating_fields:
            self._solve_layout("overhang")

    def on_no_of_girders_changed(self):
        if not self.updating_fields:
            self._solve_layout("girders")

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

    def _validate_thickness_field(self, field, min_val, max_val, default_val, too_small_msg, too_large_msg):
        try:
            text = field.text().strip()
            if not text:
                field.setText(str(int(default_val)))
                return
            value = float(text)
            if value < min_val:
                QMessageBox.critical(self, "Thickness Error", too_small_msg)
                field.setText(str(int(min_val)))
            elif value > max_val:
                QMessageBox.critical(self, "Thickness Error", too_large_msg)
                field.setText(str(int(max_val)))
        except:
            field.setText(str(int(default_val)))

    def validate_deck_thickness(self):
        self._validate_thickness_field(
            self.deck_thickness,
            100,
            500,
            200,
            "Deck thickness too small",
            "Deck thickness too large",
        )

    def validate_footpath_thickness(self):
        self._validate_thickness_field(
            self.footpath_thickness,
            100,
            500,
            200,
            "Footpath thickness too small",
            "Footpath thickness too large",
        )

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
        # Apply new visibility and load rules
        self._update_crash_barrier_visibility(barrier_type)
        self._warn_if_custom_barrier(barrier_type)

    def on_railing_load_mode_changed(self, mode):
        if not hasattr(self, "railing_load_value"):
            return
        is_auto = mode.startswith("Automatic")
        self.railing_load_value.setEnabled(not is_auto)
        if is_auto:
            self.railing_load_value.clear()

    def on_lane_count_changed(self, text):
        self._update_lane_details_rows(text)

    def _show_placeholder_message(self, action_name):
        QMessageBox.information(self, action_name, "This action will be available in an upcoming update.")

