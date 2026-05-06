"""
Additional Inputs Widget for Highway Bridge Design
Provides detailed input fields for manual bridge parameter definition
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTabBar, QLabel, QLineEdit,
    QComboBox, QGroupBox, QFormLayout, QPushButton, QScrollArea,
    QCheckBox, QSizePolicy, QSpacerItem, QStackedWidget,
    QFrame, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QDialog, QSizeGrip, QListView, QStyledItemDelegate
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QDoubleValidator, QIntValidator, QColor, QValidator

from osdagbridge.core.utils.common import *
from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style, create_action_button_bar
from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox, MessageBoxType
from osdagbridge.desktop.ui.dialogs.tabs.additional_inputs.typical_section_details import show_warning
from osdagbridge.desktop.ui.dialogs.tabs.builder import UIBuilder
from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import (
    ADDITIONAL_INPUTS_ORCHESTRATOR_SCHEMA,
)
from osdagbridge.desktop.ui.utils.custom_widgets import SmartCursorComboBoxView
from osdagbridge.desktop.ui.dialogs.tabs import schema_io


def _top_tab_attrs(schema: dict) -> tuple:
    """Extract bind-attribute names for every top-level tab in an orchestrator schema."""
    return tuple(
        entry["bind"]
        for section in schema.get("sections", [])
        if section.get("type") == "tab_container"
        for entry in section.get("tabs", [])
        if entry.get("bind")
    )


# Default top-level tab attribute names for the plate-girder dialog. Used when
# no orchestrator schema override is supplied.
_TOP_TAB_ATTRS = _top_tab_attrs(ADDITIONAL_INPUTS_ORCHESTRATOR_SCHEMA)

_TAB_BAR_STYLE = """
    QTabWidget::pane {
        border: 1px solid #d1d1d1;
        background-color: #ffffff;
        border-radius: 4px;
    }
    QTabBar::tab {
        font-weight: 600;
        font-size: 11px;
        background: #ffffff;
        color: #3a3a3a;
        border: 1px solid #d1d1d1;
        padding: 8px 14px;
    }
    QTabBar::tab:selected {
        background: #90AF13;
        color: #ffffff;
        border: 1px solid #90AF13;
    }
    QTabBar::tab:hover:!selected {
        background: #e8efcf;
    }
"""

_INPUT_KEY_ALIASES = {
    "girder_spacing": KEY_GIRDER_SPACING,
    "deck_overhang": KEY_DECK_OVERHANG,
    "no_of_girders": KEY_NO_OF_GIRDERS,
    "deck_thickness": KEY_DECK_THICKNESS,
    "footpath_width": KEY_FOOTPATH_WIDTH,
    "footpath_thickness": KEY_FOOTPATH_THICKNESS,
    "railing_width": KEY_RAILING_WIDTH,
    "railing_height": KEY_RAILING_HEIGHT,
    "crash_barrier_density": KEY_CRASH_BARRIER_DENSITY,
    "crash_barrier_width": KEY_CRASH_BARRIER_WIDTH,
    "crash_barrier_area": KEY_CRASH_BARRIER_AREA,
    "wearing_material": KEY_WEARING_COAT_MATERIAL,
    "wearing_density": KEY_WEARING_COAT_DENSITY,
    "wearing_thickness": KEY_WEARING_COAT_THICKNESS,
    "self_weight_factor": KEY_SELF_WEIGHT_FACTOR,
    "footpath_pressure": KEY_FOOTPATH_PRESSURE_VALUE,
    "left_support": KEY_LEFT_SUPPORT,
    "right_support": KEY_RIGHT_SUPPORT,
    "bearing_length": KEY_BEARING_LENGTH,
    "reinforcement_size": KEY_DECK_REINF_SIZE,
    "reinforcement_material": KEY_DECK_REINF_MATERIAL,
    "overall_bridge_width_display": "overall_bridge_width",
    "shear_stud_diameter": "stud_diameter",
    "shear_stud_height": "stud_height",
}


def with_additional_input_key_aliases(values: dict) -> dict:
    """Add legacy/common input_dict keys alongside schema bind keys."""
    enriched = dict(values or {})
    for schema_key, input_key in _INPUT_KEY_ALIASES.items():
        if schema_key in enriched and input_key not in enriched:
            enriched[input_key] = enriched[schema_key]
    return enriched


def with_additional_input_restore_aliases(values: dict) -> dict:
    """Add schema keys when restoring from legacy/common input_dict keys."""
    enriched = dict(values or {})
    for schema_key, input_key in _INPUT_KEY_ALIASES.items():
        if input_key in enriched and schema_key not in enriched:
            enriched[schema_key] = enriched[input_key]
    return enriched


class AdditionalInputs(QDialog):
    """Main dialog for Additional Inputs with tabbed interface"""

    def __init__(self, footpath_value="None", carriageway_width=7.5, parent=None,
                 initial_cad_state=None, orchestrator_schema=None,
                 tab_class_resolver=None):
        self._initial_cad_state = initial_cad_state or {}
        self._orchestrator_schema = orchestrator_schema or ADDITIONAL_INPUTS_ORCHESTRATOR_SCHEMA
        self._tab_class_resolver = tab_class_resolver
        self._top_tab_attrs = _top_tab_attrs(self._orchestrator_schema) or _TOP_TAB_ATTRS
        super().__init__(parent)
        self.setObjectName("AdditionalInputs")
        self.resize(1024, 720)
        self.setMinimumSize(900, 520)
        self.setSizeGripEnabled(True)
        self.footpath_value = footpath_value
        self.carriageway_width = carriageway_width
        self._member_properties_editable = True
        self._last_saved_data = {}
        self.saved_values = {}
        self.init_ui()
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border: 1px solid #90AF13;
            }
        """)

    def _save_inputs(self):
        """
        Save additional inputs.
        Validate all fields first.
        If errors exist -> show popup and DO NOT close dialog.
        """
        errors = []
        for tab in self._iter_top_tabs():
            if hasattr(tab, "validate_tab"):
                tab_errors = tab.validate_tab()
                if tab_errors:
                    errors.extend(tab_errors)

        if errors:
            self._show_validation_errors(errors)
            return

        self._collect_all_values()

        saved = self.saved_values.copy()
        self._last_saved_data = saved

        CustomMessageBox(
            title="Saved",
            text="Inputs saved successfully.",
            buttons=["OK"],
            dialogType=MessageBoxType.Success,
        ).exec()
        self.accept()

    def _show_validation_errors(self, errors):
        message = "\n\n".join(f"• {err}" for err in errors)

        CustomMessageBox(
            title="Validation Errors",
            text=message,
            buttons=["OK"],
            dialogType=MessageBoxType.Warning,
        ).exec()

    def _collect_all_values(self):
        """Collect values from all top-level tabs."""
        values = {}
        for tab in self._iter_top_tabs():
            if hasattr(tab, "collect_data"):
                values.update(tab.collect_data())

        self.saved_values = with_additional_input_key_aliases(values)

    def _iter_top_tabs(self):
        for attr in self._top_tab_attrs:
            tab = getattr(self, attr, None)
            if tab is not None:
                yield tab

    def setupWrapper(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        self.title_bar = CustomTitleBar(parent=self)
        self.title_bar.setTitle("Additional Inputs")
        main_layout.addWidget(self.title_bar)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(10)

        # The orchestrator schema describes the tab bar; UIBuilder constructs
        # every top-level tab via the configured tab-class resolver and binds
        # each one onto self.
        tab_host = QWidget()
        tab_host.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        UIBuilder(
            owner=self,
            schema=self._orchestrator_schema,
            tab_class_resolver=self._tab_class_resolver,
        ).build_tab(tab_host)
        content_layout.addWidget(tab_host, 1)

        self.tab_widget = tab_host.findChild(QTabWidget, "additional_inputs_tabs")
        if self.tab_widget is not None:
            self.tabs = self.tab_widget
            self._last_top_tab_index = self.tab_widget.currentIndex()
            self.tab_widget.currentChanged.connect(self._on_top_tab_changed)
            self.tab_widget.setStyleSheet(_TAB_BAR_STYLE)

        # Push bridge context that used to be a constructor argument; this
        # keeps tab construction uniform (parent-only) so they all flow through
        # tab_container the same way.
        ts = getattr(self, "typical_section_tab", None)
        if ts is not None and hasattr(ts, "set_bridge_context"):
            ts.set_bridge_context(
                footpath_value=self.footpath_value,
                carriageway_width=self.carriageway_width,
                initial_cad_state=self._initial_cad_state,
            )
        section_tab = getattr(self, "section_properties_tab", None)
        if ts is not None and section_tab is not None:
            try:
                ts.girder_count_changed.connect(section_tab.set_girder_count)
                self._sync_member_properties_girder_count()
            except Exception:
                pass

        buttons = create_action_button_bar(
            self,
            on_save=self._save_inputs,
            on_reset=self._on_reset_clicked,
            on_cancel=self.reject
        )
        content_layout.addWidget(buttons)

        main_layout.addWidget(content)

    def init_ui(self):
        self.setupWrapper()

    def _on_reset_clicked(self):
        res = CustomMessageBox(
            title="Reset Defaults",
            text="Are you sure you want to reset all fields to their default values?",
            buttons=["Yes", "No"],
            dialogType=MessageBoxType.Question
        ).exec()

        if res == "Yes":
            self._apply_defaults()

    def reset_defaults(self):
        for tab in self._iter_top_tabs():
            if hasattr(tab, "reset_defaults"):
                tab.reset_defaults()

    def _apply_defaults(self):
        """Apply defaults to the currently visible top-level tab."""
        try:
            current_widget = self.tab_widget.currentWidget()
        except Exception:
            current_widget = None

        if current_widget is None:
            self.reset_defaults()
            return

        if current_widget is getattr(self, "section_properties_tab", None):
            reset_active = getattr(self.section_properties_tab, "reset_active_tab_defaults", None)
            if callable(reset_active):
                reset_active()
                return

        reset = getattr(current_widget, "reset_defaults", None)
        if callable(reset):
            reset()

    def get_saved_data(self) -> dict:
        return self._last_saved_data.copy()

    def set_properties_data(self, data: dict) -> None:
        if not data:
            return

        data = with_additional_input_restore_aliases(data)
        for tab in self._iter_top_tabs():
            if hasattr(tab, "restore_data"):
                tab.restore_data(data)

    def update_footpath_value(self, value) -> None:
        self.footpath_value = value
        tab = getattr(self, "typical_section_tab", None)
        if tab is not None:
            fn = getattr(tab, "update_footpath_value", None)
            if callable(fn):
                fn(value)

    def set_member_properties_design_mode(self, mode: str) -> None:
        mode = self._normalize_member_properties_design_mode(mode)
        tab = getattr(self, "section_properties_tab", None)
        if tab is not None:
            fn = getattr(tab, "set_design_mode", None)
            if callable(fn):
                fn(mode)

    def _normalize_member_properties_design_mode(self, mode: str) -> str:
        value = str(mode or "").strip().lower()
        if value in {"custom", "customized"}:
            return "Custom"
        if value in {"optimized", "optimised"}:
            return "Optimized"
        return "Optimized"

    def set_member_properties_editable(self, editable: bool) -> None:
        self._member_properties_editable = bool(editable)
        tab = getattr(self, "section_properties_tab", None)
        if tab is not None:
            fn = getattr(tab, "set_editable_mode", None)
            if callable(fn):
                fn(self._member_properties_editable)

    def _sync_member_properties_girder_count(self) -> None:
        try:
            count_text = ""
            typical = getattr(self, "typical_section_tab", None)
            if typical is not None and hasattr(typical, "no_of_girders"):
                count_text = str(typical.no_of_girders.text() or "").strip()
            if not count_text:
                return
            section = getattr(self, "section_properties_tab", None)
            setter = getattr(section, "set_girder_count", None) if section is not None else None
            if callable(setter):
                setter(int(float(count_text)))
        except Exception:
            pass

    @staticmethod
    def _find_inner_tab_index(tab_widget, tab_name: str) -> int:
        try:
            for idx in range(tab_widget.count()):
                if tab_widget.tabText(idx).strip().lower() == tab_name.strip().lower():
                    return idx
        except Exception:
            return -1
        return -1

    def apply_tab_visibility(self, footpath_value: str, include_median) -> None:
        typical = getattr(self, "typical_section_tab", None)
        inner_tabs = getattr(typical, "input_tabs", None) if typical is not None else None
        if inner_tabs is None:
            return

        self.footpath_value = footpath_value
        if typical is not None:
            typical.footpath_value = footpath_value

        railing_index = self._find_inner_tab_index(inner_tabs, "Railing")
        if railing_index >= 0:
            inner_tabs.setTabEnabled(railing_index, str(footpath_value) != "None")

        median_index = self._find_inner_tab_index(inner_tabs, "Median")
        if median_index >= 0:
            median_enabled = str(include_median).strip().lower() not in {"no", "false", "0"}
            inner_tabs.setTabEnabled(median_index, median_enabled)

        if inner_tabs.currentIndex() >= 0 and not inner_tabs.isTabEnabled(inner_tabs.currentIndex()):
            for idx in range(inner_tabs.count()):
                if inner_tabs.isTabEnabled(idx):
                    inner_tabs.setCurrentIndex(idx)
                    break

        sync = getattr(typical, "_sync_child_tabs_from_parent_state", None)
        if callable(sync):
            sync(force=False)
        recalculate = getattr(typical, "recalculate_girders", None)
        if callable(recalculate):
            recalculate()
        else:
            refresh = getattr(typical, "_update_cad_preview", None)
            if callable(refresh):
                refresh()

    def update_project_location(self, location_data) -> None:
        loading = getattr(self, "loading_tab", None)
        for attr in ("temperature_load_tab", "seismic_load_tab", "wind_load_tab"):
            tab = getattr(loading, attr, None) if loading is not None else None
            fn = getattr(tab, "update_project_location", None) if tab is not None else None
            if callable(fn):
                fn(location_data)

    def _on_top_tab_changed(self, index: int) -> None:
        if index < 0:
            return

        previous = getattr(self, "_last_top_tab_index", 0)
        if previous == index:
            return

        tab_widget = getattr(self, "tab_widget", None)
        section_tab = getattr(self, "section_properties_tab", None)
        leaving_member_properties = (
            tab_widget is not None
            and section_tab is not None
            and previous == tab_widget.indexOf(section_tab)
        )
        if leaving_member_properties:
            try:
                has_unsaved = getattr(section_tab, "has_unsaved_changes", None)
                if callable(has_unsaved) and has_unsaved():
                    CustomMessageBox(
                        title="Unsaved Inputs",
                        text="Please save Member Properties before switching tabs.",
                        buttons=["OK"],
                        dialogType=MessageBoxType.Warning,
                    ).exec()
                    blocked = tab_widget.blockSignals(True)
                    tab_widget.setCurrentIndex(previous)
                    tab_widget.blockSignals(blocked)
                    return

                save_properties = getattr(section_tab, "save_properties", None)
                if callable(save_properties):
                    self._last_saved_data.update(save_properties() or {})
            except Exception:
                pass

        self._last_top_tab_index = index

    def get_all_values(self) -> dict:
        return dict(self.saved_values)
