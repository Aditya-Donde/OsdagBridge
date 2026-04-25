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

from osdagbridge.core.bridge_types.plate_girder.bridge_geometry import CrossSectionLayout
from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import (
    TYPICAL_SECTION_ORCHESTRATOR_SCHEMA,
)
from osdagbridge.core.utils.common import *
from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.dialogs.tabs.base import SchemaTab
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.desktop.ui.docks.cad_cross_section import CrossSectionCADWidget

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

class TypicalSectionDetailsTab(SchemaTab):
    """Sub-tab for Typical Section Details inputs"""

    schema = TYPICAL_SECTION_ORCHESTRATOR_SCHEMA

    footpath_changed = Signal(str)
    girder_count_changed = Signal(int)

    def __init__(self, parent=None, owner=None):
        # owner accepted for tab_container signature inspection; not forwarded to
        # super so SchemaTab uses self as owner (needed for child-bind mirroring).
        # State must exist before super().__init__() because the schema build
        # triggered there constructs child tabs that read these attributes.
        self._initial_cad_state = {}
        self.footpath_value = "None"
        self.carriageway_width = 7.5
        self.updating_fields = False
        self._updating_overall_width_display = False
        self._expose_child_schema_binds = True
        self.crash_barrier_count = 2
        self.overall_bridge_width_formula = (
            "OverallBridgeWidth = CrossSectionLayout.total_width = (2 x CarriagewayWidth if Median else CarriagewayWidth) + "
            "2 x CrashBarrierWidth + MedianWidth + (NoOfFootpaths x FootpathWidth) + "
            "(NoOfFootpaths x RailingWidth)"
        )

        super().__init__(parent=parent)

        self.input_tabs = self.findChild(QTabWidget, "typical_section_tabs")
        self._apply_bridge_context()

    def set_bridge_context(
        self,
        *,
        footpath_value: str = "None",
        carriageway_width: float = 7.5,
        initial_cad_state: dict | None = None,
    ) -> None:
        """Push bridge-level state from the dialog after construction.

        Construction is uniform (parent-only) so all top-level tabs can be
        instantiated by the orchestrator's tab_container. Bridge context that
        used to be constructor args lands here instead.
        """
        self.footpath_value = footpath_value
        self.carriageway_width = carriageway_width
        self._initial_cad_state = initial_cad_state or {}
        self._apply_bridge_context()

    def _apply_bridge_context(self) -> None:
        """Run the post-context-update sync; safe to call from __init__ or
        set_bridge_context."""
        self._sync_child_tabs_from_parent_state(force=True)
        self.recalculate_girders()
        try:
            if hasattr(self, "no_of_girders") and self.no_of_girders.text():
                self.girder_count_changed.emit(int(self.no_of_girders.text()))
        except Exception:
            pass
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

    def show_warning_message(self, title: str, text: str) -> None:
        show_warning(self, title, text)

    def show_critical_message(self, title: str, text: str) -> None:
        show_critical(self, title, text)

    def show_info_message(self, title: str, text: str) -> None:
        show_info(self, title, text)

    def _child_tabs(self):
        return tuple(
            tab for tab in (
                getattr(self, "layout_tab", None),
                getattr(self, "crash_barrier_tab", None),
                getattr(self, "median_tab", None),
                getattr(self, "railing_tab", None),
                getattr(self, "wearing_course_tab", None),
                getattr(self, "lane_details_tab", None),
            ) if tab is not None
        )

    def _sync_restored_state(self) -> None:
        self._sync_child_tabs_from_parent_state(force=False)
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
        params.update(self._layout_bridge_context_cad_params())
        params.update(self._layout_cad_params())
        params.update(self._wearing_cad_params())
        params.update(self._median_cad_params())
        params.update(self._crash_barrier_cad_params())
        params.update(self._railing_cad_params())

        self._push_cad_params(params)

    

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

    def update_footpath_value(self, footpath_value):
        self.footpath_value = footpath_value
        layout_tab = getattr(self, "layout_tab", None)
        sync = getattr(layout_tab, "sync_from_bridge_context", None) if layout_tab is not None else None
        if callable(sync):
            sync(footpath_value)
        elif hasattr(self, "footpath_width"):
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
        return exporter(include_median=self._median_is_included()) if callable(exporter) else {}

    def _railing_state(self) -> dict:
        tab = getattr(self, "railing_tab", None)
        exporter = getattr(tab, "export_railing_state", None) if tab is not None else None
        return exporter() if callable(exporter) else {}

    def _wearing_state(self) -> dict:
        tab = getattr(self, "wearing_course_tab", None)
        exporter = getattr(tab, "export_wearing_state", None) if tab is not None else None
        return exporter() if callable(exporter) else {}

    def _layout_cad_params(self) -> dict:
        tab = getattr(self, "layout_tab", None)
        exporter = getattr(tab, "export_cad_params", None) if tab is not None else None
        return exporter() if callable(exporter) else {}

    def _layout_bridge_context_cad_params(self) -> dict:
        tab = getattr(self, "layout_tab", None)
        exporter = getattr(tab, "export_bridge_context_cad_params", None) if tab is not None else None
        if not callable(exporter):
            return {}
        return exporter(self.carriageway_width, self.footpath_value)

    def _crash_barrier_cad_params(self) -> dict:
        tab = getattr(self, "crash_barrier_tab", None)
        exporter = getattr(tab, "export_cad_params", None) if tab is not None else None
        return exporter() if callable(exporter) else {}

    def _median_cad_params(self) -> dict:
        tab = getattr(self, "median_tab", None)
        exporter = getattr(tab, "export_cad_params", None) if tab is not None else None
        if not callable(exporter):
            return {}
        return exporter(include_median=self._median_is_included())

    def _railing_cad_params(self) -> dict:
        tab = getattr(self, "railing_tab", None)
        exporter = getattr(tab, "export_cad_params", None) if tab is not None else None
        return exporter() if callable(exporter) else {}

    def _wearing_cad_params(self) -> dict:
        tab = getattr(self, "wearing_course_tab", None)
        exporter = getattr(tab, "export_cad_params", None) if tab is not None else None
        return exporter() if callable(exporter) else {}

    def _push_cad_params(self, params: dict) -> None:
        if hasattr(self, "cad_preview") and params:
            self.cad_preview.update_params(params)

    def _median_is_included(self) -> bool:
        include_median = True
        if hasattr(self, "median_tab") and hasattr(self, "input_tabs"):
            try:
                median_index = self.input_tabs.indexOf(self.median_tab)
                include_median = median_index < 0 or self.input_tabs.isTabEnabled(median_index)
            except Exception:
                include_median = True
        return include_median

    def _sync_child_tabs_from_parent_state(self, *, force: bool = False) -> None:
        layout_tab = getattr(self, "layout_tab", None)
        layout_sync = getattr(layout_tab, "sync_from_bridge_context", None) if layout_tab is not None else None
        if callable(layout_sync):
            layout_sync(self.footpath_value)

        crash_tab = getattr(self, "crash_barrier_tab", None)
        crash_sync = getattr(crash_tab, "sync_from_parent_state", None) if crash_tab is not None else None
        if callable(crash_sync):
            crash_sync(force=force)

        median_tab = getattr(self, "median_tab", None)
        median_sync = getattr(median_tab, "sync_from_parent_state", None) if median_tab is not None else None
        if callable(median_sync):
            median_sync(include_median=self._median_is_included(), force=force)

        railing_tab = getattr(self, "railing_tab", None)
        railing_sync = getattr(railing_tab, "sync_from_parent_state", None) if railing_tab is not None else None
        if callable(railing_sync):
            railing_sync(force=force)

        wearing_tab = getattr(self, "wearing_course_tab", None)
        wearing_sync = getattr(wearing_tab, "sync_from_parent_state", None) if wearing_tab is not None else None
        if callable(wearing_sync):
            wearing_sync()

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
            layout_tab = getattr(self, "layout_tab", None)
            clearer = getattr(layout_tab, "clear_linked_inputs", None) if layout_tab is not None else None
            if callable(clearer):
                clearer()
            else:
                for field in (
                    getattr(self, "girder_spacing", None),
                    getattr(self, "deck_overhang", None),
                    getattr(self, "no_of_girders", None),
                ):
                    if field is not None:
                        field.clear()
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
            layout_tab = getattr(self, "layout_tab", None)
            applier = getattr(layout_tab, "apply_layout_solution", None) if layout_tab is not None else None
            if callable(applier):
                applier(spacing, overhang, girders)
            else:
                self.girder_spacing.setText(f"{float(spacing):.2f}")
                self.deck_overhang.setText(f"{float(overhang):.2f}")
                self.no_of_girders.setText(str(int(girders)))
            try:
                self.girder_count_changed.emit(int(girders))
            except Exception:
                pass
        finally:
            self.updating_fields = False

    def _solve_layout(self, changed_field="width"):
        if self.updating_fields:
            return
        self._clear_adjust_notice()
        overall_width = self.get_overall_bridge_width()
        spacing_bounds = self._spacing_bounds(overall_width)
        layout_tab = getattr(self, "layout_tab", None)
        planner = getattr(layout_tab, "solve_layout_plan", None) if layout_tab is not None else None
        if not callable(planner):
            show_warning(self, "Layout", "Layout planner is unavailable.")
            return

        result = planner(
            overall_width=overall_width,
            changed_field=changed_field,
            spacing_bounds=spacing_bounds,
            default_spacing=DEFAULT_GIRDER_SPACING,
        )
        error = result.get("error")
        if error:
            show_warning(self, "Layout", error)

        solution = result.get("solution")
        if solution:
            self._set_layout_fields(
                solution["spacing"],
                solution["overhang"],
                solution["girders"],
            )
            if result.get("reason"):
                self._show_adjust_notice(result["reason"], result.get("warning"))
            elif result.get("warning"):
                self._show_adjust_notice(None, result["warning"])
        self._update_overall_bridge_width_display()

    def _reset_crash_barrier_defaults(self):
        if hasattr(self, "crash_barrier_type"):
            self.crash_barrier_type.setCurrentText("IRC 5 - RCC Crash Barrier")
        if hasattr(self, "crash_barrier_type"):
            barrier_type = self.crash_barrier_type.currentText()
            self._apply_crash_barrier_defaults(barrier_type, force=True)

    def save_values(self):
        values = {}
        for tab in self._child_tabs():
            collector = getattr(tab, "collect_data", None)
            if callable(collector):
                values.update(collector())
        return values

    def collect_data(self) -> dict:
        return self.save_values()

    def restore_values(self, data: dict):
        if not isinstance(data, dict):
            return

        for tab in self._child_tabs():
            restorer = getattr(tab, "restore_data", None)
            if callable(restorer):
                restorer(data)
        self._sync_restored_state()

    def restore_data(self, data: dict) -> None:
        self.restore_values(data)

    def validate_tab(self):
        errors = []
        seen = set()

        for tab in self._child_tabs():
            validator = getattr(tab, "validate_tab", None)
            if not callable(validator):
                continue
            for msg in validator():
                if msg not in seen:
                    seen.add(msg)
                    errors.append(msg)

        return errors

    def reset_defaults(self):
        # Layout defaults
        self._set_layout_fields(DEFAULT_GIRDER_SPACING, 0.35 * DEFAULT_GIRDER_SPACING, 2)
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
            wearing_tab = getattr(self, "wearing_course_tab", None)
            sync = getattr(wearing_tab, "sync_from_parent_material", None) if wearing_tab is not None else None
            params = sync(self.wearing_material.currentText()) if callable(sync) else {}
            self._push_cad_params(params)
        if hasattr(self, "wearing_thickness") and not self.wearing_thickness.text():
            self.wearing_thickness.setText("50")

        lane_tab = getattr(self, "lane_details_tab", None)
        reset_lanes = getattr(lane_tab, "reset_defaults", None) if lane_tab is not None else None
        if callable(reset_lanes):
            reset_lanes()

    def _apply_crash_barrier_defaults(self, barrier_type: str, force: bool = False):
        """Populate recommended defaults per IRC 5 selections.

        force=True overwrites existing values (used on reset). Otherwise, only fill missing fields.
        """
        crash_tab = getattr(self, "crash_barrier_tab", None)
        if crash_tab is None:
            return
        sync = getattr(crash_tab, "sync_from_parent_state", None)
        params = sync(force=force) if callable(sync) else {}
        self._push_cad_params(params)

    def _apply_median_defaults(self, median_type: str, force: bool = False):
        median_tab = getattr(self, "median_tab", None)
        if median_tab is None:
            return
        sync = getattr(median_tab, "sync_from_parent_state", None)
        params = sync(force=force, include_median=True) if callable(sync) else {}
        self._push_cad_params(params)

    def _apply_railing_defaults(self, force: bool = False):
        railing_tab = getattr(self, "railing_tab", None)
        sync = getattr(railing_tab, "sync_from_parent_state", None) if railing_tab is not None else None
        params = sync(force=force) if callable(sync) else {}
        self._push_cad_params(params)

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

    def recalculate_girders(self):
        self._update_overall_bridge_width_display()
        self._solve_layout("width")
        self._update_cad_preview()

    def validate_footpath_width(self):
        try:
            if self.footpath_width.text():
                width = float(self.footpath_width.text())
                if width < MIN_FOOTPATH_WIDTH:
                    show_critical(self, "Footpath Width Error",
                                         f"Footpath width must be at least {MIN_FOOTPATH_WIDTH} m as per IRC 5 Clause 104.3.6.")
        except:
            pass

    def _show_placeholder_message(self, action_name):
        show_info(self, action_name, "This action will be available in an upcoming update.")
