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
from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import (
    CRASH_BARRIER_TAB_SCHEMA,
    LANE_DETAILS_TAB_SCHEMA,
    LAYOUT_TAB_SCHEMA,
    MEDIAN_TAB_SCHEMA,
    RAILING_TAB_SCHEMA,
    TYPICAL_SECTION_ORCHESTRATOR_SCHEMA,
    WEARING_COURSE_TAB_SCHEMA,
)
from osdagbridge.core.utils.common import *
from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.dialogs.tabs import schema_io
from osdagbridge.desktop.ui.dialogs.tabs.ui_builder import UIBuilder
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.desktop.ui.docks.cad_cross_section import CrossSectionCADWidget
from osdagbridge.desktop.cad.irc5_geometry import (
    CrashBarrierGeometry,
    MedianGeometry,
    RailingGeometry,
)



def _styled_message_box(icon, title, text, parent=None):
    """Create a QMessageBox with explicit styling to ensure visibility."""
    msg = QMessageBox(parent)
    msg.setIcon(icon)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setStyleSheet("""
        QMessageBox {
            background-color: #ffffff;
        }
        QMessageBox QLabel {
            color: #000000;
            font-size: 12px;
            background-color: transparent;
        }
        QMessageBox QPushButton {
            background-color: #f0f0f0;
            color: #000000;
            border: 1px solid #888888;
            border-radius: 4px;
            padding: 6px 20px;
            min-width: 80px;
        }
        QMessageBox QPushButton:hover {
            background-color: #e0e0e0;
        }
        QMessageBox QPushButton:pressed {
            background-color: #d0d0d0;
        }
    """)
    return msg


def show_warning(parent, title, text):
    """Show a styled warning message box."""
    msg = _styled_message_box(QMessageBox.Warning, title, text, parent)
    msg.exec()


def show_critical(parent, title, text):
    """Show a styled critical/error message box."""
    msg = _styled_message_box(QMessageBox.Critical, title, text, parent)
    msg.exec()


def show_info(parent, title, text):
    """Show a styled information message box."""
    msg = _styled_message_box(QMessageBox.Information, title, text, parent)
    msg.exec()

class TypicalSectionDetailsTab(QWidget):
    """Sub-tab for Typical Section Details inputs"""

    footpath_changed = Signal(str)
    girder_count_changed = Signal(int)

    def __init__(self, footpath_value="None", carriageway_width=7.5, parent=None, initial_cad_state=None):
        self._initial_cad_state = initial_cad_state or {}
        super().__init__(parent)
        self.footpath_value = footpath_value
        self.carriageway_width = carriageway_width
        self.updating_fields = False
        self._updating_overall_width_display = False
        self._updating_lane_table = False
        self._lane_cell_signal_connected = False
        self._expose_child_schema_binds = True
        # Track last known numeric values to avoid spurious recalculations on text-only edits
        self._last_spacing_value: float | None = None
        self._last_overhang_value: float | None = None
        self._last_girders_value: int | None = None
        self.crash_barrier_count = 2  # Assume two crash barriers at carriageway edges
        self.overall_bridge_width_formula = (
            "OverallBridgeWidth = CrossSectionLayout.total_width = (2 x CarriagewayWidth if Median else CarriagewayWidth) + "
            "2 x CrashBarrierWidth + MedianWidth + (NoOfFootpaths x FootpathWidth) + "
            "(NoOfFootpaths x RailingWidth)"
        )
        self.init_ui()
        # Apply homepage CAD state so the preview starts in sync
        if self._initial_cad_state:
            self.cad_preview.update_params(self._initial_cad_state)

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

    def _schema_chunks(self):
        return (
            LAYOUT_TAB_SCHEMA,
            CRASH_BARRIER_TAB_SCHEMA,
            MEDIAN_TAB_SCHEMA,
            RAILING_TAB_SCHEMA,
            WEARING_COURSE_TAB_SCHEMA,
            LANE_DETAILS_TAB_SCHEMA,
        )

    def _lane_table_state(self):
        lane_tab = getattr(self, "lane_details_tab", None)
        export_state = getattr(lane_tab, "export_lane_table_state", None) if lane_tab is not None else None
        if callable(export_state):
            return export_state()
        return {"lane_table_data": []}

    def _restore_lane_table_state(self, data: dict) -> None:
        lane_rows = data.get("lane_table_data")
        if not isinstance(lane_rows, list):
            lane_count = getattr(self, "lane_count_combo", None)
            if lane_count is not None:
                self.on_lane_count_changed(lane_count.currentText())
            return

        lane_tab = getattr(self, "lane_details_tab", None)
        restore_rows = getattr(lane_tab, "set_lane_rows", None) if lane_tab is not None else None
        if callable(restore_rows):
            was_updating = self._updating_lane_table
            self._updating_lane_table = True
            try:
                restore_rows(lane_rows)
            finally:
                self._updating_lane_table = was_updating

    def _sync_restored_state(self) -> None:
        if hasattr(self, "footpath_width"):
            enabled = self.footpath_value != "None"
            self.footpath_width.setEnabled(enabled)
            self.footpath_thickness.setEnabled(enabled)

        crash_state = self._crash_barrier_state()
        barrier_type = crash_state.get("type")
        if barrier_type:
            self._update_crash_barrier_visibility(barrier_type)
            self._apply_crash_barrier_defaults(barrier_type, force=False)

        median_state = self._median_state()
        median_type = median_state.get("type")
        if median_type:
            median_index = self.input_tabs.indexOf(self.median_tab) if hasattr(self, "median_tab") else -1
            include_median = median_index < 0 or self.input_tabs.isTabEnabled(median_index)
            self._update_median_visibility(median_type, include_median=include_median)
            self._apply_median_defaults(median_type, force=False)

        if self._railing_state().get("type"):
            self._apply_railing_defaults(force=False)

        wearing_state = self._wearing_state()
        if wearing_state.get("material"):
            self.on_wearing_material_changed(wearing_state["material"])

        self._update_overall_bridge_width_display()
        self._update_cad_preview()

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
        # Build UI from orchestrator schema
        UIBuilder(owner=self, schema=TYPICAL_SECTION_ORCHESTRATOR_SCHEMA).build_tab(self)

        # The orchestrator schema binds cad_preview and the sub-tabs.
        # We need to ensure input_tabs exists for some logic below.
        # UIBuilder._build_tab_container sets the objectName to typical_section_tabs.
        # Let's find it.
        self.input_tabs = self.findChild(QTabWidget, "typical_section_tabs")

        # CONNECT COMBO BOXES TO IRC DEFAULT HANDLERS

        if hasattr(self, "crash_barrier_type"):
            self.crash_barrier_type.currentTextChanged.connect(
                self.on_crash_barrier_type_changed
            )

        # CONNECT MEDIAN TAB DROPDOWN
        if hasattr(self.median_tab, "median_type"):
            self.median_tab.median_type.currentTextChanged.connect(
                self.on_median_type_changed
            )

        # CONNECT RAILING TAB DROPDOWN
        if hasattr(self.railing_tab, "railing_type"):
            self.railing_tab.railing_type.currentTextChanged.connect(
                self.on_railing_type_changed
            )

        if hasattr(self, "wearing_thickness"):
            self.wearing_thickness.editingFinished.connect(self._update_cad_preview)

        if hasattr(self, "wearing_density"):
            self.wearing_density.editingFinished.connect(self._update_cad_preview)

        if hasattr(self, "wearing_material"):
            self.wearing_material.currentTextChanged.connect(self._update_cad_preview)
            
        # Initialize lane defaults per IRC 5 Clause 104.3.1
        self._initialize_lane_defaults()

        self.deck_thickness.textChanged.connect(self.update_footpath_thickness)
        self.recalculate_girders()
        
        # Update CAD when fields change
        if hasattr(self, "girder_spacing"):
            self.girder_spacing.editingFinished.connect(self._update_cad_preview)
        if hasattr(self, "no_of_girders"):
            self.no_of_girders.editingFinished.connect(self._update_cad_preview)
        if hasattr(self, "deck_overhang"):
            self.deck_overhang.editingFinished.connect(self._update_cad_preview)
        if hasattr(self, "deck_thickness"):
            self.deck_thickness.editingFinished.connect(self._update_cad_preview)
        if hasattr(self, "footpath_width"):
            self.footpath_width.editingFinished.connect(self._update_cad_preview)
        if hasattr(self, "footpath_thickness"):
            self.footpath_thickness.editingFinished.connect(self._update_cad_preview)

        # Initialize crash barrier visibility/load state
        if hasattr(self, "crash_barrier_type"):
            barrier_type = self.crash_barrier_type.currentText()
            self._update_crash_barrier_visibility(barrier_type)
            self._apply_crash_barrier_defaults(barrier_type, force=False)
        if hasattr(self, "median_type"):
            median_type = self.median_type.currentText()
            self._apply_median_defaults(median_type, force=False)
        if hasattr(self, "railing_load_mode"):
            self._apply_railing_defaults(force=False)
        if hasattr(self, "wearing_material"):
            self.on_wearing_material_changed(self.wearing_material.currentText())
        # Propagate initial girder count to other tabs
        try:
            if hasattr(self, "no_of_girders") and self.no_of_girders.text():
                self.girder_count_changed.emit(int(self.no_of_girders.text()))
        except Exception:
            pass
        
    def _update_cad_preview(self):
        """
        @author: Faizan
        Collect all current UI field values — girder count, girder spacing,
        deck overhang, deck thickness etc.
        — convert units to millimetres where required, and push the assembled
        params dict to CrossSectionCADWidget.update_params() to trigger an
        immediate redraw of the 2D cross-section.
        """

        if not hasattr(self, 'cad_preview'):
            return

        params = {}

        # Carriageway Width (always needed for overall width calculation in CAD)
        if hasattr(self, "carriageway_width"):
            params['carriageway_width'] = float(self.carriageway_width) * 1000

        # Footpath Config
        if hasattr(self, "footpath_value"):
            fp_map = {
                "Both Sides": "both",
                "Single Side": "left",
                "None": "none"
            }
            params['footpath_config'] = fp_map.get(self.footpath_value, "none")

        if hasattr(self, "no_of_girders") and self.no_of_girders.text():
            params['num_girders'] = int(float(self.no_of_girders.text()))

        if hasattr(self, "girder_spacing") and self.girder_spacing.text():
            params['girder_spacing'] = float(self.girder_spacing.text()) * 1000

        if hasattr(self, "deck_overhang") and self.deck_overhang.text():
            params['deck_overhang'] = float(self.deck_overhang.text()) * 1000

        if hasattr(self, "deck_thickness") and self.deck_thickness.text():
            params['deck_thickness'] = float(self.deck_thickness.text())

        if hasattr(self, "footpath_width") and self.footpath_width.text():
            params['footpath_width'] = float(self.footpath_width.text()) * 1000

        if hasattr(self, "footpath_thickness") and self.footpath_thickness.text():
            params['footpath_thickness'] = float(self.footpath_thickness.text())
            
        crash_state = self._crash_barrier_state()
        if crash_state.get("type"):
            params["crash_barrier_type"] = crash_state["type"]
            
        # ---- Wearing Course ----
        wearing_state = self._wearing_state()
        if wearing_state.get("thickness_mm") is not None:
            wearing_thickness = float(wearing_state["thickness_mm"])
            params[KEY_WEARING_COAT_THICKNESS] = wearing_thickness
            params["wearing_course_thickness"] = wearing_thickness

        if wearing_state.get("density") is not None:
            wearing_density = float(wearing_state["density"])
            params[KEY_WEARING_COAT_DENSITY] = wearing_density
            params["wearing_course_density"] = wearing_density

        if wearing_state.get("material"):
            wearing_material = wearing_state["material"]
            params[KEY_WEARING_COAT_MATERIAL] = wearing_material
            params["wearing_course_material"] = wearing_material
        
        # ---- Median ----
        median_state = self._median_state()
        if median_state.get("type"):
            params["median_type"] = median_state["type"]

        if median_state.get("width_m") is not None:
            params["median_width"] = float(median_state["width_m"]) * 1000

        if median_state.get("height_m") is not None:
            params["median_height"] = float(median_state["height_m"]) * 1000
            
        # ---- Crash Barrier ----
        if crash_state.get("width_m") is not None:
            params["crash_barrier_width"] = float(crash_state["width_m"]) * 1000

        if crash_state.get("height_m") is not None:
            params["crash_barrier_height"] = float(crash_state["height_m"]) * 1000

        # ---- Railing ----
        railing_state = self._railing_state()
        if railing_state.get("type"):
            params["railing_type"] = railing_state["type"]

        if railing_state.get("width_mm") is not None:
            params["railing_width"] = float(railing_state["width_mm"])

        if railing_state.get("height_m") is not None:
            params["railing_height"] = float(railing_state["height_m"]) * 1000
            
        # ---- Median presence ----
        if hasattr(self, "median_tab"):
            median_idx = self.input_tabs.indexOf(self.median_tab)
            is_median_enabled = self.input_tabs.isTabEnabled(median_idx)
            params["median_present"] = is_median_enabled
        elif median_state.get("type"):
            params["median_present"] = median_state["type"] != "None"

        if params:
            self.cad_preview.update_params(params)

    

    def _get_footpath_count(self):
        if self.footpath_value == "Both Sides":
            return 2
        if self.footpath_value == "Single Side":
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
        lane_tab = getattr(self, "lane_details_tab", None)
        setter = getattr(lane_tab, "set_lane_count", None) if lane_tab is not None else None
        if not callable(setter):
            return
        was_updating = self._updating_lane_table
        self._updating_lane_table = True
        try:
            setter(count)
        finally:
            self._updating_lane_table = was_updating

    def _renumber_lanes(self):
        if not hasattr(self, "lane_table"):
            return
        rows = self.lane_table.rowCount()
        for i in range(rows):
            lane_num_item = QTableWidgetItem(str(i + 1))
            lane_num_item.setFlags(lane_num_item.flags() & ~Qt.ItemIsEditable)
            lane_num_item.setTextAlignment(Qt.AlignCenter)
            self.lane_table.setItem(i, 0, lane_num_item)

    def _design_lane_width_m(self):
        """IRC 5 Clause 104.3.1 design lane width (m)."""
        return 3.5

    def _max_lane_count_allowed(self):
        try:
            width = float(self.carriageway_width) if self.carriageway_width else 0.0
            max_lanes = int(math.floor(width / self._design_lane_width_m()))
            return max(1, min(6, max_lanes if max_lanes > 0 else 1))
        except Exception:
            return 1

    def _initialize_lane_defaults(self):
        """Initialize lane table with IRC 5 Clause 104.3.1 defaults."""
        if not hasattr(self, "lane_count_combo") or not hasattr(self, "lane_table"):
            return
        
        max_allowed = self._max_lane_count_allowed()
        
        # Update combo choices to only show valid options
        self._updating_lane_table = True
        try:
            self.lane_count_combo.blockSignals(True)
            self.lane_count_combo.clear()
            for i in range(1, max_allowed + 1):
                self.lane_count_combo.addItem(str(i))
            self.lane_count_combo.setCurrentText(str(max_allowed))
            self.lane_count_combo.blockSignals(False)
            
            lane_tab = getattr(self, "lane_details_tab", None)
            populate = getattr(lane_tab, "populate_defaults", None) if lane_tab is not None else None
            if callable(populate):
                populate(max_allowed, self._design_lane_width_m())
        finally:
            self._updating_lane_table = False
        
        # Connect cell change signal for validation
        if not self._lane_cell_signal_connected:
            try:
                self.lane_table.cellChanged.connect(self._on_lane_cell_changed)
                self._lane_cell_signal_connected = True
            except Exception:
                pass

    def _set_lane_value(self, row, column, text):
        lane_tab = getattr(self, "lane_details_tab", None)
        setter = getattr(lane_tab, "_set_cell", None) if lane_tab is not None else None
        if callable(setter):
            setter(row, column, text)

    def _parse_lane_float(self, row, column):
        lane_tab = getattr(self, "lane_details_tab", None)
        parser = getattr(lane_tab, "_parse_float", None) if lane_tab is not None else None
        if callable(parser):
            return parser(row, column)
        return None

    def _populate_lane_defaults(self, lane_count):
        lane_tab = getattr(self, "lane_details_tab", None)
        populate = getattr(lane_tab, "populate_defaults", None) if lane_tab is not None else None
        if not callable(populate) or lane_count <= 0:
            return
        was_updating = self._updating_lane_table
        self._updating_lane_table = True
        try:
            populate(lane_count, self._design_lane_width_m())
        finally:
            self._updating_lane_table = was_updating

    def _recompute_lane_starts(self):
        lane_tab = getattr(self, "lane_details_tab", None)
        recompute = getattr(lane_tab, "recompute_lane_starts", None) if lane_tab is not None else None
        if not callable(recompute):
            return
        was_updating = self._updating_lane_table
        self._updating_lane_table = True
        try:
            total_width = recompute(self._design_lane_width_m())
        finally:
            self._updating_lane_table = was_updating

        try:
            carriageway = float(self.carriageway_width) if self.carriageway_width else None
        except Exception:
            carriageway = None
        if carriageway and total_width - carriageway > 1e-6:
            show_warning(
                self,
                "Lane Width Exceeds Carriageway",
                f"Sum of lane widths ({total_width:.2f} m) exceeds carriageway width provided ({carriageway:.2f} m).\n"
                "Adjust lane count or widths per IRC 5 Clause 104.3.1.",
            )

    def _validate_lane_width(self, row):
        design_width = self._design_lane_width_m()
        width = self._parse_lane_float(row, 2)
        if width is None:
            self._set_lane_value(row, 2, f"{design_width:.2f}")
            return
        if width + 1e-6 < design_width:
            show_critical(
                self,
                "Lane Width Below IRC Minimum",
                f"IRC 5 Clause 104.3.1 requires a lane width of at least {design_width:.2f} m.",
            )
            self._set_lane_value(row, 2, f"{design_width:.2f}")

    def _validate_lane_start(self, row):
        design_width = self._design_lane_width_m()
        start = self._parse_lane_float(row, 1)
        if start is None:
            self._recompute_lane_starts()
            return

        if row == 0:
            if abs(start) > 1e-6:
                show_warning(
                    self,
                    "Lane Start Offset",
                    "First lane must start at 0 m from inner edge of crash barrier by default.",
                )
                self._recompute_lane_starts()
            return

        prev_start = self._parse_lane_float(row - 1, 1) or 0.0
        prev_width = self._parse_lane_float(row - 1, 2) or design_width
        expected = prev_start + prev_width
        if abs(start - expected) > 1e-3:
            show_warning(
                self,
                "Lane Start Sequence",
                "Each lane start must equal previous lane start plus previous lane width per IRC guidance.",
            )
            self._recompute_lane_starts()

    def _on_lane_cell_changed(self, row, column):
        if self._updating_lane_table:
            return
        if column == 2:
            self._validate_lane_width(row)
            self._recompute_lane_starts()
        elif column == 1:
            self._validate_lane_start(row)
            self._recompute_lane_starts()

    def update_footpath_value(self, footpath_value):
        self.footpath_value = footpath_value
        if hasattr(self, "footpath_width"):
            self.footpath_width.setEnabled(footpath_value != "None")
            self.footpath_thickness.setEnabled(footpath_value != "None")
        self.recalculate_girders()
        self.footpath_changed.emit(footpath_value)

    def _calculate_overall_bridge_width(self):
        carriageway_width = float(self.carriageway_width) if self.carriageway_width else 0.0
        crash_state = self._crash_barrier_state()
        railing_state = self._railing_state()
        median_state = self._median_state()
        crash_barrier_width = self._parse_length_value(
            None,
            default=crash_state.get("width_m", DEFAULT_CRASH_BARRIER_WIDTH),
        )
        footpath_width = self._parse_length_value(
            getattr(self, "footpath_width", None),
            default=0.0,
        )
        railing_width = self._parse_length_value(
            None,
            default=(railing_state.get("width_mm", DEFAULT_RAILING_WIDTH * 1000.0) or 0.0),
            scale=1000.0,
        )
        median_width = self._parse_length_value(
            None,
            default=median_state.get("width_m", 0.0),
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

    def _crash_barrier_state(self) -> dict:
        tab = getattr(self, "crash_barrier_tab", None)
        exporter = getattr(tab, "export_barrier_state", None) if tab is not None else None
        return exporter() if callable(exporter) else {}

    def _median_state(self) -> dict:
        tab = getattr(self, "median_tab", None)
        exporter = getattr(tab, "export_median_state", None) if tab is not None else None
        include_median = True
        if hasattr(self, "median_tab") and hasattr(self, "input_tabs"):
            try:
                median_index = self.input_tabs.indexOf(self.median_tab)
                include_median = median_index < 0 or self.input_tabs.isTabEnabled(median_index)
            except Exception:
                include_median = True
        return exporter(include_median=include_median) if callable(exporter) else {}

    def _railing_state(self) -> dict:
        tab = getattr(self, "railing_tab", None)
        exporter = getattr(tab, "export_railing_state", None) if tab is not None else None
        return exporter() if callable(exporter) else {}

    def _wearing_state(self) -> dict:
        tab = getattr(self, "wearing_course_tab", None)
        exporter = getattr(tab, "export_wearing_state", None) if tab is not None else None
        return exporter() if callable(exporter) else {}

    def _format_spacing(self, spacing):
        return f"{spacing:.2f}"

    def _format_overhang(self, overhang):
        return f"{overhang:.2f}"

    def _clear_adjust_notice(self):
        layout_tab = getattr(self, "layout_tab", None)
        clear_notices = getattr(layout_tab, "clear_notices", None) if layout_tab is not None else None
        if callable(clear_notices):
            clear_notices()
            return
        if hasattr(self, "layout_adjust_notice"):
            self.layout_adjust_notice.hide()
            self.layout_adjust_notice.setText("")
        if hasattr(self, "layout_warning_notice"):
            self.layout_warning_notice.hide()
            self.layout_warning_notice.setText("")
        if hasattr(self, "layout_notice_container"):
            self.layout_notice_container.hide()

    def _clear_layout_entry_fields(self, message: str) -> None:
        """Clear layout inputs together when any of them is emptied and show an error."""
        if self.updating_fields:
            return
        self.updating_fields = True
        try:
            for field in (
                getattr(self, "girder_spacing", None),
                getattr(self, "deck_overhang", None),
                getattr(self, "no_of_girders", None),
            ):
                if field is not None:
                    field.clear()
            # Reset tracked values
            self._last_spacing_value = None
            self._last_overhang_value = None
            self._last_girders_value = None
        finally:
            self.updating_fields = False
        self._clear_adjust_notice()
        show_warning(self, "Layout", message)

    def _show_adjust_notice(self, reason, warning=None):
        layout_tab = getattr(self, "layout_tab", None)
        set_notices = getattr(layout_tab, "set_notices", None) if layout_tab is not None else None
        if callable(set_notices):
            set_notices(reason=reason, warning=warning)
            return
        any_visible = bool(reason) or bool(warning)
        if hasattr(self, "layout_adjust_notice"):
            if reason:
                self.layout_adjust_notice.setText(f"Values adjusted: {reason}")
                self.layout_adjust_notice.show()
            else:
                self.layout_adjust_notice.hide()
                self.layout_adjust_notice.setText("")
        if hasattr(self, "layout_warning_notice"):
            if warning:
                self.layout_warning_notice.setText(f"⚠ Warning: {warning}")
                self.layout_warning_notice.show()
            else:
                self.layout_warning_notice.hide()
                self.layout_warning_notice.setText("")
        if hasattr(self, "layout_notice_container"):
            if any_visible:
                self.layout_notice_container.show()
            else:
                self.layout_notice_container.hide()

    def _set_layout_fields(self, spacing, overhang, girders):
        self.updating_fields = True
        try:
            self.girder_spacing.setText(self._format_spacing(spacing))
            self.deck_overhang.setText(self._format_overhang(overhang))
            self.no_of_girders.setText(str(int(girders)))
            # Update tracked values to prevent spurious recalculations
            self._last_spacing_value = spacing
            self._last_overhang_value = overhang
            self._last_girders_value = int(girders)
            try:
                self.girder_count_changed.emit(int(girders))
            except Exception:
                pass
        finally:
            self.updating_fields = False

    def _deck_overhang_range(self, overall_width):
        if overall_width <= 0:
            return 0.0, 0.0
        return 0.0, overall_width / 2.0

    def _spacing_candidates_for_overhang(self, overall_width, overhang, spacing_bounds):
        """Find best (n, spacing) combination for a FIXED overhang.
        
        When user changes overhang, we keep overhang fixed and only adjust
        girder spacing and number of girders.
        
        Formula: overall_width = 2 * overhang + (n - 1) * spacing
        => spacing = (overall_width - 2 * overhang) / (n - 1)  for n >= 2
        """
        spacing_min, spacing_max = spacing_bounds
        max_n = int(math.floor(overall_width / spacing_min) + 2) if spacing_min > 0 else 50
        
        best = None
        for n in range(2, max(2, max_n) + 1):
            # For n >= 2: spacing = (overall_width - 2 * overhang) / (n - 1)
            raw_spacing = (overall_width - 2.0 * overhang) / (n - 1)
            if raw_spacing <= 0:
                continue
            
            # Round spacing to 2 decimal places for display
            s_rounded = round(raw_spacing, 2)
            
            # Check if rounded spacing is within valid bounds
            if s_rounded < spacing_min - 1e-6 or s_rounded > spacing_max + 1e-6:
                continue
            
            s_rounded = self._clamp(s_rounded, spacing_min, spacing_max)
            
            # Prefer n values that result in overhang being 0.35-0.5 of spacing (ideal range)
            ideal_min = 0.35 * s_rounded
            ideal_max = 0.5 * s_rounded
            if ideal_min <= overhang <= ideal_max:
                score = (0, n)  # Ideal range, prefer lower n
            else:
                # Not in ideal range but still valid
                score = (1, n)
            
            if best is None or score < best[0]:
                best = (score, s_rounded, overhang, n)
        
        return best

    def _pick_n_for_spacing(self, overall_width, spacing, spacing_bounds):
        """Find best (n, overhang) combination for a FIXED spacing.
        
        When user changes spacing, we keep spacing fixed and only adjust
        number of girders and overhang.
        
        Formula: overall_width = 2 * overhang + (n - 1) * spacing
        => overhang = (overall_width - (n - 1) * spacing) / 2
        
        Ideally overhang should be 0.35 to 0.5 of spacing. If not possible,
        allow overhang to vary between 0 and overall_width/2.
        """
        spacing_min, spacing_max = spacing_bounds
        spacing = self._clamp(round(spacing, 2), spacing_min, spacing_max)
        
        o_min, o_max = self._deck_overhang_range(overall_width)
        max_n = int(math.floor(overall_width / spacing) + 2) if spacing > 0 else 1
        
        # Ideal overhang range: 0.35 to 0.5 of spacing
        ideal_overhang_min = 0.35 * spacing
        ideal_overhang_max = 0.5 * spacing
        
        best = None
        for n in range(2, max(2, max_n) + 1):
            if (n - 1) * spacing > overall_width + 1e-6:
                break
            
            overhang = (overall_width - (n - 1) * spacing) / 2.0
            
            # Check if overhang is within valid range (0 to overall_width/2)
            if overhang < o_min - 1e-6 or overhang > o_max + 1e-6:
                continue
            
            # Score: prefer overhang in ideal range (0.35-0.5 of spacing)
            if ideal_overhang_min <= overhang <= ideal_overhang_max:
                # In ideal range
                score = (0, abs(overhang - (ideal_overhang_min + ideal_overhang_max) / 2), n)
            elif overhang <= spacing:
                # Not in ideal range but overhang <= spacing (acceptable)
                score = (1, abs(overhang - ideal_overhang_max), n)
            else:
                # Overhang > spacing (less desirable but valid)
                score = (2, overhang - spacing, n)
            
            if best is None or score < best[0]:
                best = (score, n, spacing, overhang)
        
        return best

    def _solve_layout(self, changed_field="width"):
        if self.updating_fields:
            return
        self._clear_adjust_notice()
        overall_width = self.get_overall_bridge_width()
        if overall_width <= 0:
            show_warning(self, "Layout", "Overall bridge width must be positive.")
            return

        spacing_bounds = self._spacing_bounds(overall_width)
        spacing_input = self._parse_length_value(self.girder_spacing, default=DEFAULT_GIRDER_SPACING)
        overhang_input = self._parse_length_value(self.deck_overhang, default=0.35 * spacing_input)
        girders_input = None
        if self.no_of_girders.text().strip():
            try:
                girders_input = int(self.no_of_girders.text().strip())
            except ValueError:
                girders_input = None

        o_min, o_max = self._deck_overhang_range(overall_width)

        if changed_field == "spacing":
            pick = self._pick_n_for_spacing(overall_width, spacing_input, spacing_bounds)
            if not pick:
                show_warning(self, "Layout", "Cannot satisfy constraints with the selected girder spacing.")
                self._update_overall_bridge_width_display()
                return
            _, n, spacing_use, overhang_use = pick
            # Capture old values BEFORE setting new ones
            old_girders = girders_input
            old_overhang = overhang_input
            old_spacing = spacing_input
            self._set_layout_fields(spacing_use, overhang_use, n)
            reason_parts = []
            # Spacing should be kept as user specified (only minor rounding allowed)
            if abs(spacing_use - old_spacing) > 0.01:
                reason_parts.append(f"spacing {old_spacing:.2f}→{spacing_use:.2f}")
            if abs(overhang_use - old_overhang) > 1e-6:
                reason_parts.append(f"overhang {old_overhang:.2f}→{overhang_use:.2f}")
            if old_girders is not None and n != old_girders:
                reason_parts.append(f"girders {old_girders}→{n}")
            
            # Check if overhang exceeds girder spacing and show warning
            warning_msg = None
            if overhang_use > spacing_use + 1e-6:
                warning_msg = f"Overhang ({overhang_use:.2f} m) exceeds girder spacing ({spacing_use:.2f} m)"
            
            if reason_parts:
                self._show_adjust_notice(", ".join(reason_parts), warning_msg)
            elif warning_msg:
                self._show_adjust_notice(None, warning_msg)
            self._update_overall_bridge_width_display()
            return

        if changed_field == "overhang":
            # Check if user entered a value exceeding the maximum possible overhang
            if overhang_input < o_min - 1e-6 or overhang_input > o_max + 1e-6:
                show_warning(
                    self,
                    "Deck Overhang Width Error",
                    f"Deck overhang width must be between {o_min:.2f} m and {o_max:.2f} m "
                    f"(half of Overall Bridge Width).\n\n"
                    f"Valid range: {o_min:.2f} m to {o_max:.2f} m\n"
                    f"You entered: {overhang_input:.2f} m\n\n"
                    "To change deck overhang limits, you need to adjust the Overall Bridge Width "
                    "(by modifying carriageway width, crash barriers, footpaths, etc.)."
                )
                self._update_overall_bridge_width_display()
                return
            
            # Keep overhang fixed as user specified
            overhang_use = overhang_input
            pick = self._spacing_candidates_for_overhang(overall_width, overhang_use, spacing_bounds)
            if not pick:
                show_warning(self, "Layout", "Cannot satisfy constraints with the selected deck overhang.")
                self._update_overall_bridge_width_display()
                return
            _, spacing_use, _, n = pick
            # Capture old values for comparison
            old_overhang = overhang_input
            old_spacing = spacing_input
            old_girders = girders_input
            self._set_layout_fields(spacing_use, overhang_use, n)
            reason_parts = []
            # Overhang should not change since user specified it
            if abs(spacing_use - old_spacing) > 1e-6:
                reason_parts.append(f"spacing {old_spacing:.2f}→{spacing_use:.2f}")
            if old_girders is not None and n != old_girders:
                reason_parts.append(f"girders {old_girders}→{n}")
            
            # Check if overhang exceeds girder spacing and show warning
            warning_msg = None
            if overhang_use > spacing_use + 1e-6:
                warning_msg = f"Overhang ({overhang_use:.2f} m) exceeds girder spacing ({spacing_use:.2f} m)"
            
            if reason_parts:
                self._show_adjust_notice(", ".join(reason_parts), warning_msg)
            elif warning_msg:
                self._show_adjust_notice(None, warning_msg)
            self._update_overall_bridge_width_display()
            return

        if changed_field == "girders":
            if girders_input is None or girders_input < 2:
                show_warning(self, "Layout", "Number of girders must be an integer greater than or equal to 2.")
                if girders_input is None:
                    return
                girders_input = 2
                self._set_layout_fields(spacing_input, overhang_input, girders_input)
            n = girders_input
            # Capture old values for comparison
            old_overhang = overhang_input
            old_spacing = spacing_input

            # If the selected number of girders cannot fit within the current
            # overall bridge width, clamp to the maximum feasible count.
            # With minimum spacing and non-negative overhang:
            # overall_width >= (n-1) * spacing_min  =>  n_max = floor(overall_width/spacing_min) + 1
            try:
                spacing_min = float(spacing_bounds[0])
            except Exception:
                spacing_min = 1.0
            if spacing_min <= 0:
                spacing_min = 1.0
            n_max = int(math.floor((overall_width + 1e-9) / spacing_min) + 1)
            n_max = max(2, n_max)
            if n > n_max:
                # Clamp and proceed with a valid solution rather than leaving
                # the UI with an impossible n value.
                n = n_max

            # For n >= 2: overall_width = 2*overhang + (n-1)*spacing
            # Keep n fixed, try to find spacing and overhang such that overhang is in ideal range
            # Ideal overhang = 0.35 to 0.5 of spacing
            
            # Try to keep overhang in ideal range (0.35-0.5 of spacing)
            # From formula: spacing = (overall_width - 2*overhang) / (n-1)
            # If overhang = 0.35*spacing => spacing = overall_width / (n-1 + 0.7)
            # If overhang = 0.5*spacing => spacing = overall_width / (n-1 + 1.0) = overall_width / n
            
            # Try target spacing that gives overhang in ideal range
            ideal_spacing_for_0_35 = overall_width / (n - 1 + 0.7)
            ideal_spacing_for_0_50 = overall_width / n
            
            # Pick spacing that's in the middle of the ideal range
            target_spacing = (ideal_spacing_for_0_35 + ideal_spacing_for_0_50) / 2.0
            spacing_use = self._clamp(round(target_spacing, 2), *spacing_bounds)
            overhang_use = (overall_width - (n - 1) * spacing_use) / 2.0
            
            # Check if overhang is within valid range
            if overhang_use < o_min - 1e-6 or overhang_use > o_max + 1e-6:
                show_warning(
                    self,
                    "Layout",
                    "Cannot satisfy constraints with the selected number of girders. "
                    f"For the current overall width ({overall_width:.2f} m) and minimum spacing ({spacing_min:.2f} m), "
                    f"maximum feasible girders is {n_max}.",
                )
                # Revert to a safe fallback (previous value if available, else 2)
                fallback_n = int(getattr(self, "_last_girders_value", 2) or 2)
                fallback_n = max(2, min(fallback_n, n_max))
                pick = self._pick_n_for_spacing(overall_width, spacing_use, spacing_bounds)
                if pick:
                    _, fallback_n2, spacing_f, overhang_f = pick
                    fallback_n = max(2, min(int(fallback_n2), n_max))
                    self._set_layout_fields(spacing_f, overhang_f, fallback_n)
                else:
                    self._set_layout_fields(self._clamp(spacing_use, *spacing_bounds), self._clamp(max(0.0, overhang_use), o_min, o_max), fallback_n)
                self._update_overall_bridge_width_display()
                return
            
            self._set_layout_fields(spacing_use, overhang_use, n)
            reason_parts = []
            if abs(spacing_use - old_spacing) > 0.01:
                reason_parts.append(f"spacing {old_spacing:.2f}→{spacing_use:.2f}")
            if abs(overhang_use - old_overhang) > 1e-6:
                reason_parts.append(f"overhang {old_overhang:.2f}→{overhang_use:.2f}")
            if girders_input is not None and n != girders_input:
                reason_parts.append(f"girders {girders_input}→{n}")
            
            # Check if overhang exceeds girder spacing and show warning
            warning_msg = None
            if overhang_use > spacing_use + 1e-6:
                warning_msg = f"Overhang ({overhang_use:.2f} m) exceeds girder spacing ({spacing_use:.2f} m)"
            
            if reason_parts:
                self._show_adjust_notice(", ".join(reason_parts), warning_msg)
            elif warning_msg:
                self._show_adjust_notice(None, warning_msg)
            self._update_overall_bridge_width_display()
            return

        # Default / overall width change: try to keep current spacing if feasible
        # Capture old values for comparison
        old_spacing = spacing_input
        old_overhang = overhang_input
        old_girders = girders_input
        pick = self._pick_n_for_spacing(overall_width, old_spacing, spacing_bounds)
        if not pick:
            # Fallback to default spacing
            pick = self._pick_n_for_spacing(overall_width, DEFAULT_GIRDER_SPACING, spacing_bounds)
        if pick:
            _, n, spacing_use, overhang_use = pick
            self._set_layout_fields(spacing_use, overhang_use, n)
            reason_parts = []
            if abs(spacing_use - old_spacing) > 0.01:
                reason_parts.append(f"spacing {old_spacing:.2f}→{spacing_use:.2f}")
            if abs(overhang_use - old_overhang) > 1e-6:
                reason_parts.append(f"overhang {old_overhang:.2f}→{overhang_use:.2f}")
            if old_girders is not None and n != old_girders:
                reason_parts.append(f"girders {old_girders}→{n}")
            
            # Check if overhang exceeds girder spacing and show warning
            warning_msg = None
            if overhang_use > spacing_use + 1e-6:
                warning_msg = f"Overhang ({overhang_use:.2f} m) exceeds girder spacing ({spacing_use:.2f} m)"
            
            if reason_parts:
                self._show_adjust_notice(", ".join(reason_parts), warning_msg)
            elif warning_msg:
                self._show_adjust_notice(None, warning_msg)
        else:
            show_warning(self, "Layout", "Cannot satisfy layout constraints for the current overall width.")
        self._update_overall_bridge_width_display()

    def _reset_crash_barrier_defaults(self):
        if hasattr(self, "crash_barrier_type"):
            self.crash_barrier_type.setCurrentText("IRC 5 - RCC Crash Barrier")
        if hasattr(self, "crash_barrier_type"):
            barrier_type = self.crash_barrier_type.currentText()
            self._update_crash_barrier_visibility(barrier_type)
            self._apply_crash_barrier_defaults(barrier_type, force=True)

    def save_values(self):
        values = {}
        for schema in self._schema_chunks():
            values.update(schema_io.collect_values(self, schema))
        values.update(self._lane_table_state())
        return values

    def collect_data(self) -> dict:
        return self.save_values()

    def restore_values(self, data: dict):
        if not isinstance(data, dict):
            return

        for schema in self._schema_chunks():
            schema_io.restore_values(self, schema, data)

        self._restore_lane_table_state(data)
        self._sync_restored_state()

    def restore_data(self, data: dict) -> None:
        self.restore_values(data)

    def validate_tab(self):
        errors = []
        seen = set()

        for schema in self._schema_chunks():
            for message in schema_io.validate(self, schema):
                if message and message not in seen:
                    seen.add(message)
                    errors.append(message)

        lane_tab = getattr(self, "lane_details_tab", None)
        validate_lanes = getattr(lane_tab, "validate_lane_rows", None) if lane_tab is not None else None
        if callable(validate_lanes):
            try:
                carriageway = float(self.carriageway_width) if self.carriageway_width else 0.0
            except Exception:
                carriageway = 0.0
            for msg in validate_lanes(self._design_lane_width_m(), carriageway):
                if msg not in seen:
                    seen.add(msg)
                    errors.append(msg)

        return errors

    def reset_defaults(self):
        # Layout defaults
        if hasattr(self, "girder_spacing"):
            self.girder_spacing.setText(self._format_spacing(DEFAULT_GIRDER_SPACING))
        if hasattr(self, "deck_overhang"):
            self.deck_overhang.setText(self._format_overhang(0.35 * DEFAULT_GIRDER_SPACING))
        if hasattr(self, "no_of_girders"):
            self.no_of_girders.setText("2")
        self._clear_adjust_notice()
        self._solve_layout("spacing")

        # Crash barrier defaults
        self._reset_crash_barrier_defaults()

        # Median defaults
        if hasattr(self, "median_type"):
            self.median_type.setCurrentText("IRC 5 - Raised Kerb")
            median_type = self.median_type.currentText()
            self._apply_median_defaults(median_type, force=True)

        # Railing defaults
        if hasattr(self, "railing_type"):
            self.railing_type.setCurrentText("IRC 5 - RCC Railing")
            self._apply_railing_defaults(force=True)

        # Wearing course defaults
        if hasattr(self, "wearing_material"):
            self.wearing_material.setCurrentText("Concrete")
            self.on_wearing_material_changed(self.wearing_material.currentText())
        if hasattr(self, "wearing_thickness") and not self.wearing_thickness.text():
            self.wearing_thickness.setText("50")

    def _auto_compute_crash_barrier_load(self):
        barrier_type = self._crash_barrier_state().get("type", "")
        crash_tab = getattr(self, "crash_barrier_tab", None)
        compute = getattr(crash_tab, "auto_compute_load", None) if crash_tab is not None else None
        if callable(compute):
            compute(barrier_type)

    def _apply_crash_barrier_defaults(self, barrier_type: str, force: bool = False):
        """Populate recommended defaults per IRC 5 selections.

        force=True overwrites existing values (used on reset). Otherwise, only fill missing fields.
        """
        crash_tab = getattr(self, "crash_barrier_tab", None)
        if crash_tab is None:
            return
        effective_barrier_type = self._effective_crash_barrier_type(barrier_type)
        geom = CrashBarrierGeometry.get_geometry(effective_barrier_type)
        crash_tab.apply_defaults(barrier_type, geom, force=force)
        # ----  CAD UPDATE AFTER DEFAULTS CHANGE ----
        if hasattr(self, "cad_preview"):
            params = {
                "crash_barrier_type": barrier_type,
            }

            crash_state = self._crash_barrier_state()
            if crash_state.get("width_m") is not None:
                params["crash_barrier_width"] = float(crash_state["width_m"]) * 1000

            if crash_state.get("height_m") is not None:
                params["crash_barrier_height"] = float(crash_state["height_m"]) * 1000

            self.cad_preview.update_params(params)

    def _apply_median_defaults(self, median_type: str, force: bool = False):
        median_tab = getattr(self, "median_tab", None)
        if median_tab is None:
            return
        effective_median_type = self._effective_median_type(median_type)
        geom = MedianGeometry.get_geometry(effective_median_type)
        median_tab.apply_defaults(median_type, geom, force=force, include_median=True)

        geom = MedianGeometry.get_geometry(effective_median_type)

        params = {
            "median_type": median_type,
        }

        if geom:
            if "median_width" in geom:
                params["median_width"] = geom["median_width"]

            if "barrier_height" in geom:
                params["median_height"] = geom["barrier_height"]
            elif "kerb_height" in geom:
                params["median_height"] = geom["kerb_height"]

            self.cad_preview.update_params(params)
            
        if hasattr(self, "cad_preview"):
            params = {
                "median_present": True,
                "median_type": median_type,
            }

            median_state = self._median_state()
            if median_state.get("width_m") is not None:
                params["median_width"] = float(median_state["width_m"]) * 1000

            if median_state.get("height_m") is not None:
                params["median_height"] = float(median_state["height_m"]) * 1000

            self.cad_preview.update_params(params)

    def _apply_railing_defaults(self, force: bool = False):
        if not hasattr(self, "railing_type"):
            return

        railing_type = self._railing_state().get("type") or self.railing_type.currentText()
        effective_railing_type = self._effective_railing_type(railing_type)
        geom = RailingGeometry.get_geometry(effective_railing_type)
        railing_tab = getattr(self, "railing_tab", None)
        apply_defaults = getattr(railing_tab, "apply_defaults", None) if railing_tab is not None else None
        apply_load_mode = getattr(railing_tab, "apply_load_mode", None) if railing_tab is not None else None

        if callable(apply_defaults) and geom:
            apply_defaults(
                width_mm=geom.get("width"),
                height_m=(geom.get("height") / 1000.0) if geom.get("height") is not None else None,
                force=force,
            )

        if callable(apply_load_mode):
            apply_load_mode("Automatic (IRC 6)")

        geom = RailingGeometry.get_geometry(effective_railing_type)

        params = {
            "railing_type": railing_type,
        }

        if geom:
            if "height" in geom:
                params["railing_height"] = geom["height"]

            if "width" in geom:
                params["railing_width"] = geom["width"]

            self.cad_preview.update_params(params)

    def _is_metallic_barrier(self, barrier_type):
        crash_tab = getattr(self, "crash_barrier_tab", None)
        checker = getattr(crash_tab, "is_metallic", None) if crash_tab is not None else None
        return checker(barrier_type) if callable(checker) else barrier_type.startswith("IRC 5 - Metallic Crash Barrier")

    def _effective_crash_barrier_type(self, barrier_type):
        crash_tab = getattr(self, "crash_barrier_tab", None)
        helper = getattr(crash_tab, "effective_type", None) if crash_tab is not None else None
        return helper(barrier_type) if callable(helper) else ("IRC 5 - RCC Crash Barrier" if barrier_type == "Custom" else barrier_type)

    def _effective_median_type(self, median_type):
        median_tab = getattr(self, "median_tab", None)
        helper = getattr(median_tab, "effective_type", None) if median_tab is not None else None
        return helper(median_type) if callable(helper) else ("IRC 5 - Raised Kerb" if median_type == "Custom" else median_type)

    def _effective_railing_type(self, railing_type):
        return "IRC 5 - RCC Railing" if railing_type == "Custom" else railing_type

    def _is_rcc_barrier(self, barrier_type):
        crash_tab = getattr(self, "crash_barrier_tab", None)
        checker = getattr(crash_tab, "is_rcc", None) if crash_tab is not None else None
        if callable(checker):
            return checker(barrier_type)
        return (
            barrier_type.startswith("IRC 5 - RCC Crash Barrier")
            or barrier_type.startswith("IRC 5 - High Containment RCC Crash Barrier")
        )

    def _update_crash_barrier_visibility(self, barrier_type):
        crash_tab = getattr(self, "crash_barrier_tab", None)
        updater = getattr(crash_tab, "update_visibility", None) if crash_tab is not None else None
        if callable(updater):
            updater(barrier_type)

    def _is_metallic_median(self, median_type):
        median_tab = getattr(self, "median_tab", None)
        checker = getattr(median_tab, "is_metallic", None) if median_tab is not None else None
        return checker(median_type) if callable(checker) else median_type.startswith("IRC 5 - Metallic Crash Barrier")

    def _is_rcc_median(self, median_type):
        median_tab = getattr(self, "median_tab", None)
        checker = getattr(median_tab, "is_rcc", None) if median_tab is not None else None
        return checker(median_type) if callable(checker) else (median_type.startswith("IRC 5 - RCC Crash Barrier") or median_type.startswith("IRC 5 - Raised Kerb"))

    def _auto_compute_median_load(self):
        median_type = self._median_state().get("type", "")
        median_tab = getattr(self, "median_tab", None)
        compute = getattr(median_tab, "auto_compute_load", None) if median_tab is not None else None
        if callable(compute):
            compute(median_type)

    def on_median_type_changed(self, median_type):
        print(f"Median type changed to: {median_type}")
        self._apply_median_defaults(median_type, force=True)

        if hasattr(self, "cad_preview"):
            params = {"median_type": median_type}
            self.cad_preview.update_params(params)

        self.recalculate_girders()
        
    def on_railing_type_changed(self, railing_type):
        print(f"Railing type changed to: {railing_type}")
        self._apply_railing_defaults(force=True)

        if hasattr(self, "cad_preview"):
            params = {"railing_type": railing_type}
            self.cad_preview.update_params(params)

        self.recalculate_girders()

    def _update_median_visibility(self, median_type, include_median=True):
        median_tab = getattr(self, "median_tab", None)
        updater = getattr(median_tab, "update_visibility", None) if median_tab is not None else None
        if callable(updater):
            updater(median_type, include_median=include_median)

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
                self.overall_bridge_width_display.setText(f"{overall_width:.2f}")
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
                show_warning(
                    self,
                    "Overall Bridge Width Locked",
                    "Overall Bridge Width is auto-calculated using:\n"
                    f"{self.overall_bridge_width_formula}",
                )
            self._update_overall_bridge_width_display()

    def recalculate_girders(self):
        self._update_overall_bridge_width_display()
        self._solve_layout("width")
        self._update_cad_preview()


    def on_girder_spacing_changed(self):
        if self.updating_fields:
            return
        if not self.girder_spacing.text().strip():
            self._clear_layout_entry_fields("Girder spacing, deck overhang, and number of girders are linked. Please enter all three.")
            self._last_spacing_value = None
            return
        try:
            new_val = float(self.girder_spacing.text().strip())
        except ValueError:
            return
        # Skip recalculation if numeric value unchanged (e.g., "2.50" -> "2.5")
        if self._last_spacing_value is not None and abs(new_val - self._last_spacing_value) < 1e-6:
            return
        self._last_spacing_value = new_val
        self._solve_layout("spacing")

    def on_deck_overhang_changed(self):
        if self.updating_fields:
            return
        if not self.deck_overhang.text().strip():
            self._clear_layout_entry_fields("Girder spacing, deck overhang, and number of girders are linked. Please enter all three.")
            self._last_overhang_value = None
            return
        try:
            new_val = float(self.deck_overhang.text().strip())
        except ValueError:
            return
        # Skip recalculation if numeric value unchanged (e.g., "1.31" -> "1.310")
        if self._last_overhang_value is not None and abs(new_val - self._last_overhang_value) < 1e-6:
            return
        self._last_overhang_value = new_val
        self._solve_layout("overhang")

    def on_no_of_girders_changed(self):
        if self.updating_fields:
            return
        if not self.no_of_girders.text().strip():
            self._clear_layout_entry_fields("Girder spacing, deck overhang, and number of girders are linked. Please enter all three.")
            self._last_girders_value = None
            return
        try:
            new_val = int(float(self.no_of_girders.text().strip()))
        except ValueError:
            return
        # Skip recalculation if numeric value unchanged (e.g., "2.00" -> "2")
        if self._last_girders_value is not None and new_val == self._last_girders_value:
            return
        self._last_girders_value = new_val
        self._solve_layout("girders")

    def on_footpath_width_changed(self):
        if not self.updating_fields:
            self.recalculate_girders()

    def validate_footpath_width(self):
        try:
            if self.footpath_width.text():
                width = float(self.footpath_width.text())
                if width < MIN_FOOTPATH_WIDTH:
                    show_critical(self, "Footpath Width Error",
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
                show_critical(self, "Thickness Error", too_small_msg)
                field.setText(str(int(min_val)))
            elif value > max_val:
                show_critical(self, "Thickness Error", too_large_msg)
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
                    show_critical(self, "Railing Height Error",
                                         f"Railing height must be at least {MIN_RAILING_HEIGHT} m as per IRC 5 Clauses 109.7.2.3 and 109.7.2.4.")
        except:
            pass

    def update_footpath_thickness(self):
        if self.deck_thickness.text() and not self.footpath_thickness.text():
            self.footpath_thickness.setText(self.deck_thickness.text())

    def on_crash_barrier_type_changed(self, barrier_type):
        if (barrier_type in ["Flexible", "Semi-Rigid"]) and (self.footpath_value == "None"):
            show_critical(
                self,
                "Crash Barrier Type Not Permitted",
                f"{barrier_type} crash barriers are not permitted on bridges without an outer footpath per IRC 5 Clause 109.6.4.",
            )

        # IMPORTANT: force=True so layout recalculation cannot override geometry
        self._update_crash_barrier_visibility(barrier_type)
        self._apply_crash_barrier_defaults(barrier_type, force=True)

        # Recalculate AFTER geometry is locked
        self.recalculate_girders()

        # Refresh CAD preview to show the newly selected barrier shape
        self._update_cad_preview()


    def on_railing_load_mode_changed(self, mode):
        railing_tab = getattr(self, "railing_tab", None)
        apply_load_mode = getattr(railing_tab, "apply_load_mode", None) if railing_tab is not None else None
        if callable(apply_load_mode):
            apply_load_mode(mode)

    def on_lane_count_changed(self, text):
        """Handle lane count selection change."""
        if self._updating_lane_table:
            return
        try:
            num_lanes = int(text)
        except (TypeError, ValueError):
            return

        self._update_lane_details_rows(num_lanes)
        self._populate_lane_defaults(num_lanes)

    def on_wearing_material_changed(self, material):
        wearing_tab = getattr(self, "wearing_course_tab", None)
        apply_defaults = getattr(wearing_tab, "apply_material_defaults", None) if wearing_tab is not None else None
        if callable(apply_defaults):
            apply_defaults(material)

    def _show_placeholder_message(self, action_name):
        show_info(self, action_name, "This action will be available in an upcoming update.")
