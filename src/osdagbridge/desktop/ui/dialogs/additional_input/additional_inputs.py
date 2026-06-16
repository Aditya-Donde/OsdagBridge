"""
Additional Inputs Widget for Highway Bridge Design
Provides detailed input fields for manual bridge parameter definition
"""
from copy import deepcopy

import math
from osdagbridge.core.utils.common import *


from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTabBar, QLabel, QLineEdit,
    QComboBox, QPushButton, QCheckBox, QSizePolicy,
    QDialog, QSizeGrip, QFrame, QScrollArea, QTableWidget, QTableWidgetItem
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QDoubleValidator, QIntValidator

from osdagbridge.core.bridge_types.plate_girder.validator import BridgeInputValidator
from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style, create_action_button_bar
from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox, MessageBoxType
from osdagbridge.desktop.ui.utils.custom_widgets import SmartCursorComboBoxView
from osdagbridge.desktop.ui.dialogs.additional_input.ui_builder.common_ui_builder import UIBuilder
from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import (
    DESIGN_OPTIONS_SCHEMA,
    DESIGN_OPTIONS_CONT_SCHEMA,
    SUPPORT_CONDITIONS_SCHEMA,
    MEMBER_PROPERTIES_SCHEMA,
)
from osdagbridge.desktop.ui.dialogs.additional_input.ui_builder._load_combination_widget import LoadCombinationWidget
from osdagbridge.desktop.ui.dialogs.additional_input.ui_builder.common_ui_builder import AdaptiveWidget

# =================================================================================
#   MAIN IMPLEMENTATION
# =================================================================================

class AdditionalInputs(QDialog):
    """Main dialog for Additional Inputs with tabbed interface"""

    update_template_page_2d_cad = Signal(dict)

    # ── Dialog Setup ──────────────────────────────────────────────────────────────

    def __init__(
        self,
        footpath_value="None",
        carriageway_width=7.5,
        parent=None,
    ):
        super().__init__(parent)

        # For on spot validation of input fields when changed
        self.validator = BridgeInputValidator()

        # Just initializing for intial refernce
        # Input dictionary treated as defaults for current scenario
        self.default_input_dict = {}
        # Work temporarily on a copy of default dictionary
        self.working_input_dict = {}

        # TO tract additional input is opened first time or not.
        # This is required for end connectors
        self.interacted_first = True

        self.setObjectName("AdditionalInputs")
        self.resize(1024, 850)
        self.setMinimumSize(900, 520)
        self.setSizeGripEnabled(True)
        self.footpath_value = footpath_value
        self.carriageway_width = carriageway_width
        self._member_properties_editable = True
        self._last_saved_data = {}
        self.saved_values = {}  # Store all input values here
        self.init_ui()
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border: 1px solid #90AF13;
            }
        """)

    def setupWrapper(self):  # setup: frameless window wrapper with custom title bar and size grip
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        self.title_bar = CustomTitleBar()
        self.title_bar.setTitle("Additional Inputs")
        main_layout.addWidget(self.title_bar)

        self.content_widget = QWidget(self)
        main_layout.addWidget(self.content_widget, 1)

        size_grip = QSizeGrip(self)
        size_grip.setFixedSize(16, 16)

        overlay = QHBoxLayout()
        overlay.setContentsMargins(0, 0, 4, 4)
        overlay.addStretch(1)
        overlay.addWidget(size_grip, 0, Qt.AlignBottom | Qt.AlignRight)
        main_layout.addLayout(overlay)

    def init_ui(self):  # setup: builds all top-level tabs and wires dialog-level signals
        self.setupWrapper()

        main_layout = QVBoxLayout(self.content_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Main tab widget
        self.tabs = QTabWidget()
        self.tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.stretching_tab_bar = QTabBar()
        self.stretching_tab_bar.setElideMode(Qt.ElideRight)
        self.tabs.setTabBar(self.stretching_tab_bar)
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #d1d1d1;
                background-color: #ffffff;
                border-radius: 6px;
            }
            QTabBar::tab {
                font-weight: bold;
                font-size: 12px;
                background: #ffffff;
                color: #3a3a3a;
                border: 1px solid #d1d1d1;
                padding: 10px 22px;
            }
            QTabBar::tab:selected {
                background: #90AF13;
                color: #ffffff;
                border: 1px solid #90AF13;
            }
            QTabBar::tab:hover {
                background: #90AF13;
                color: #ffffff;
            }
        """)

        self._last_top_tab_index = 0

        # Sub-Tab 1: Typical Section Details (built inline)
        self.typical_section_tab = self._build_typical_section_tab()
        self.tabs.addTab(self.typical_section_tab, "Typical Section Details")

        # Sub-Tab 2: Member Properties
        self.section_properties_tab = UIBuilder(
            owner=self,
            schema=MEMBER_PROPERTIES_SCHEMA,
            card_title="",
            with_scroll=False,
            main_widget_object_name="member_properties.main",
            additional_input_instance=self,
        )
        self.tabs.addTab(self.section_properties_tab, "Member Properties")

        # Sub-Tab 3: Loading
        from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import LOADING_TAB_SCHEMA
        self.loading_tab = UIBuilder(
            owner=self,
            schema=LOADING_TAB_SCHEMA,
            card_title="",
            with_scroll=False,
            main_widget_object_name="loading.main",
            additional_input_instance=self,
        )
        self.tabs.addTab(self.loading_tab, "Loading")

        self.support_tab = UIBuilder(
            owner=self,
            schema=SUPPORT_CONDITIONS_SCHEMA,
            card_title="",
            with_scroll=True,
            main_widget_object_name="support_conditions.main",
            additional_input_instance=self,
        )
        self.tabs.addTab(self.support_tab, "Support Conditions")

        # Sub-Tab 5: Analysis/Design Options
        self.design_options_tab = UIBuilder(
            owner=self,
            schema=DESIGN_OPTIONS_SCHEMA,
            card_title="",
            with_scroll=True,
            main_widget_object_name="design_options.main",
            additional_input_instance=self,
        )
        self.tabs.addTab(self.design_options_tab, "Analysis/Design Options")

        # Sub-Tab 6: Design Options (Cont.)
        self.design_options_cont_tab = UIBuilder(
            owner=self,
            schema=DESIGN_OPTIONS_CONT_SCHEMA,
            card_title="",
            with_scroll=True,
            main_widget_object_name="design_options_cont.main",
            additional_input_instance=self,
        )
        self.tabs.addTab(self.design_options_cont_tab, "Design Options (Cont.)")

        main_layout.addWidget(self.tabs)

        action_bar, self.defaults_button, self.save_button = create_action_button_bar()
        self.defaults_button.clicked.connect(self.reset_active_tab_defaults)

        from pprint import pprint
        self.defaults_button.clicked.connect(lambda: pprint(self.working_input_dict))

        self.save_button.clicked.connect(self._save_inputs)
        main_layout.addSpacing(6)
        main_layout.addWidget(action_bar)

        # Enforce max 2 decimal places for all double validators in the dialog
        self._enforce_decimal_places(2)
        # Normalize existing numeric text to 2 decimal places for consistent display
        self._normalize_numeric_texts(2)

    # ── Dialog Lifecycle ─────────────────────────────────────────────────────────

    def set_input_dictionary(self, input_dict: dict):  # lifecycle: sets default/working dicts and wires END_CONNECTORS on first open
        self.default_input_dict = input_dict
        self.working_input_dict = deepcopy(input_dict)

        self._sync_tab_active_states()
        self.set_defaults()
        for key, handler in ((KEY_CB_TYPE, self.on_crash_barrier_type_changed),
                             (KEY_MD_TYPE, self.on_median_type_changed),
                             (KEY_RL_TYPE, self.on_railing_type_changed)):
            w = self.findChild(QComboBox, key)
            if w:
                handler(w.currentText(), force=False)

        self.default_input_dict.update(self.working_input_dict)

        if self.interacted_first:
            self.interacted_first = False
            from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import END_CONNECTORS
            UIBuilder.wire_end_connectors(END_CONNECTORS, ai=self)

    def set_defaults(self) -> None:  # lifecycle: populates all widgets from working_input_dict; called at init time only
        """
        Central function to populate all widgets in the dialog from working_input_dict.
        Called at init time (from set_input_dictionary) when working_input_dict
        is a fresh copy of the defaults. NOT used by the Defaults button.
        """
        for widget in self.findChildren(QWidget):
            name = widget.objectName()
            if not name or name not in self.working_input_dict:
                continue
            value = self.working_input_dict.get(name)
            if value is None:
                continue

            if isinstance(widget, QLineEdit):
                if isinstance(value, dict):
                    continue
                try:
                    if name == "design_options_cont.fatigue.load_cycles":
                        text = str(int(value))
                    else:
                        text = f"{float(value):.2f}"
                except (ValueError, TypeError):
                    text = str(value)
                widget.blockSignals(True)
                widget.setText(text)
                widget.blockSignals(False)

            elif isinstance(widget, QComboBox):
                widget.blockSignals(True)
                widget.setCurrentText(str(value))
                widget.blockSignals(False)

            elif isinstance(widget, QCheckBox):
                widget.blockSignals(True)
                widget.setChecked(bool(value))
                widget.blockSignals(False)

        # ── Sync AdaptiveWidgets from working_input_dict ──────────────────────
        from osdagbridge.desktop.ui.dialogs.additional_input.ui_builder.common_ui_builder import AdaptiveWidget
        for adaptive in self.findChildren(AdaptiveWidget):
            ctrl_id = getattr(adaptive, "_controller_id", "")
            if not ctrl_id:
                continue
            mode = str(self.working_input_dict.get(ctrl_id) or "")
            adaptive.switch_mode(mode)

    def design_mode_trigger(self, mode_str: str):  # lifecycle: syncs Optimized/Custom mode across all affected widgets and AdaptiveWidgets
        # Ensures IS Section hidden and welded fields shown correctly on first open
        gd_type_w = self.findChild(QComboBox, KEY_MP_GIRDER_TYPE)
        if gd_type_w:
            self._on_girder_type_changed(gd_type_w.currentText())

        value = str(mode_str or "").strip().lower()
        if value in {"custom", "customized"}:
            normalized = "Custom"
        else:
            normalized = "Optimized"

        self.working_input_dict[KEY_DESIGN_MODE] = normalized
        is_optimized = normalized == "Optimized"

        # Sync AdaptiveWidgets (depth, flange widths, thickness fields)
        from osdagbridge.desktop.ui.dialogs.additional_input.ui_builder.common_ui_builder import AdaptiveWidget
        for adaptive in self.findChildren(AdaptiveWidget):
            if getattr(adaptive, "_controller_id", "") == KEY_DESIGN_MODE:
                adaptive.switch_mode(normalized)

        # Type & Symmetry — disabled when Optimized
        for key in [KEY_MP_GIRDER_TYPE, KEY_MP_GIRDER_SYMMETRY]:
            w = self.findChild(QWidget, key)
            if w:
                w.setEnabled(not is_optimized)

        # Web Type — read-only and forced to "Thin Web with ITS" when Optimized
        web_type_w = self.findChild(QComboBox, KEY_MP_GIRDER_WEB_TYPE)
        if web_type_w:
            web_type_w.setEnabled(not is_optimized)
            if is_optimized:
                web_type_w.blockSignals(True)
                web_type_w.setCurrentText("Thin Web with ITS")
                web_type_w.blockSignals(False)

        # Section Properties card — hide entirely when Optimized
        wrapper = self.findChild(QWidget, KEY_MP_GD_SP)
        if wrapper:
            wrapper.setVisible(not is_optimized)

        # Hide section drawing when Optimized — only visible in Custom mode
        wrapper = self.findChild(QWidget, KEY_MP_GD_SECTION_DRAWING)
        if wrapper:
            wrapper.setVisible(not is_optimized)

        # Stiffener fields — all greyed out when Optimized
        stiffener_keys = [
            KEY_MP_STIFFENER_NO_BEARING_STIFFENERS, KEY_MP_STIFFENER_SPACING,
            KEY_MP_STIFFENER_BEARING_THICKNESS, KEY_MP_STIFFENER_BEARING_OUTSTAND,
            KEY_MP_STIFFENER_INTERMEDIATE, KEY_MP_STIFFENER_INTERMEDIATE_SPACING,
            KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS, KEY_MP_STIFFENER_INTERMEDIATE_OUTSTAND,
            KEY_MP_STIFFENER_LONGITUDINAL, KEY_MP_STIFFENER_LONGITUDINAL_THICKNESS,
            KEY_MP_STIFFENER_DESIGN_METHOD, KEY_MP_STIFFENER_APPLY_ALL
        ]
        for key in stiffener_keys:
            w = self.findChild(QWidget, key)
            if w:
                w.setEnabled(not is_optimized)

        # In Custom mode re-apply conditional sub-field states.
        if not is_optimized:
            w = self.findChild(QComboBox, KEY_MP_STIFFENER_INTERMEDIATE)
            if w:
                self._on_intermediate_stiffener_changed(w.currentText())
            w = self.findChild(QComboBox, KEY_MP_STIFFENER_LONGITUDINAL)
            if w:
                self._on_longitudinal_stiffener_changed(w.currentText())

        # TODO: Must move it to refresh functionality after section_properties.py is removed
        widget = self.findChild(QLineEdit, KEY_MP_GD_TOTAL_SPAN)
        if widget:
            widget.setText(str(self.working_input_dict.get(KEY_SPAN)))

        # Sync segment table total span from KEY_SPAN so reopening with a changed span
        # updates the last segment's end to match the new bridge span.
        from osdagbridge.desktop.ui.dialogs.additional_input.ui_builder._segment_table_widget import SegmentTableWidget
        seg_table = self.findChild(SegmentTableWidget, KEY_MP_GD_SEGMENT_TABLE)
        if seg_table is not None:
            total_span = float(self.working_input_dict.get(KEY_SPAN))
            seg_table.set_total_span(total_span)

        # End Diaphragm fields — disabled when Optimized
        from osdagbridge.core.utils.common import (
            KEY_MP_ED_BRACING_SECTION, KEY_MP_ED_BRACING_SECTION_DESIGNATION,
            KEY_MP_ED_TOP_CHORD_SECTION_TYPE, KEY_MP_ED_TOP_CHORD_SECTION_DESIG,
            KEY_MP_ED_BOTTOM_CHORD_SECTION_TYPE, KEY_MP_ED_BOTTOM_CHORD_SECTION_DESIG,
            KEY_MP_ED_IS_SECTION,
            KEY_MP_ED_TOTAL_DEPTH, KEY_MP_ED_WEB_THICKNESS,
            KEY_MP_ED_TOP_FLANGE_WIDTH, KEY_MP_ED_TOP_FLANGE_THICKNESS,
            KEY_MP_ED_BOTTOM_FLANGE_WIDTH, KEY_MP_ED_BOTTOM_FLANGE_THICKNESS,
        )
        ed_disable_keys = [
            KEY_MP_ED_BRACING_SECTION,           KEY_MP_ED_BRACING_SECTION_DESIGNATION,
            KEY_MP_ED_TOP_CHORD_SECTION_TYPE,    KEY_MP_ED_TOP_CHORD_SECTION_DESIG,
            KEY_MP_ED_BOTTOM_CHORD_SECTION_TYPE, KEY_MP_ED_BOTTOM_CHORD_SECTION_DESIG,
            KEY_MP_ED_IS_SECTION,
            KEY_MP_ED_TOTAL_DEPTH,        KEY_MP_ED_WEB_THICKNESS,
            KEY_MP_ED_TOP_FLANGE_WIDTH,   KEY_MP_ED_TOP_FLANGE_THICKNESS,
            KEY_MP_ED_BOTTOM_FLANGE_WIDTH, KEY_MP_ED_BOTTOM_FLANGE_THICKNESS,
        ]
        for key in ed_disable_keys:
            w = self.findChild(QWidget, key)
            if w:
                w.setEnabled(not is_optimized)

        # Re-apply End Diaphragm bracing layout state (K-Bracing disables bottom chord, CAD sync)
        self._on_ed_bracing_layout_changed()
        # Refresh the Girder Details cross-section preview with live bridge inputs.
        # design_mode_trigger runs on every dialog open, so this also seeds it.
        cad = self.findChild(QWidget, KEY_MP_GD_CAD_PREVIEW)
        if cad:
            cad.update_cad_state(self.working_input_dict)

        # Cross Bracing section fields — disabled when Optimized
        cb_disable_keys = [
            KEY_MP_CB_BRACING_SECTION_TYPE,       KEY_MP_CB_BRACING_SECTION_DESIGNATION,
            KEY_MP_CB_TOP_CHORD_SECTION_TYPE,      KEY_MP_CB_TOP_CHORD_SECTION_DESIG,
            KEY_MP_CB_BOTTOM_CHORD_SECTION_TYPE,   KEY_MP_CB_BOTTOM_CHORD_SECTION_DESIG,
        ]
        for key in cb_disable_keys:
            w = self.findChild(QWidget, key)
            if w:
                w.setEnabled(not is_optimized)

        # Re-apply CB layout state so checkbox-gating is respected on top of mode
        self._on_cb_bracing_layout_changed("", None)

        # Recompute CB spacing from current span and no. of cross bracings
        spacing_w = self.findChild(QLineEdit, KEY_MP_CB_SPACING)
        self._on_cb_spacing_computed("", spacing_w)

    def reset_active_tab_defaults(self) -> None:  # lifecycle: resets current tab's fields to default_input_dict values
        """
        Reset only the currently active tab's fields to their default values
        sourced from default_input_dict (populated from defaults.py at startup).
        Does NOT affect fields on other tabs.
        """
        active_tab = self.tabs.currentWidget()
        if active_tab is None:
            return

        if hasattr(active_tab, "reset_active_tab_defaults"):
            active_tab.reset_active_tab_defaults()
            return
        elif hasattr(active_tab, "reset_defaults"):
            active_tab.reset_defaults()
            return

        for widget in active_tab.findChildren(QWidget):
            name = widget.objectName()
            if not name or name not in self.default_input_dict:
                continue
            value = self.default_input_dict.get(name)
            if value is None:
                continue

            if isinstance(widget, QLineEdit):
                try:
                    if name == "design_options_cont.fatigue.load_cycles":
                        text = str(int(value))
                    else:
                        text = f"{float(value):.2f}"
                except (ValueError, TypeError):
                    text = str(value)
                widget.blockSignals(True)
                widget.setText(text)
                widget.blockSignals(False)

            elif isinstance(widget, QComboBox):
                widget.blockSignals(True)
                widget.setCurrentText(str(value))
                widget.blockSignals(False)

            elif isinstance(widget, QCheckBox):
                widget.blockSignals(True)
                widget.setChecked(bool(value))
                widget.blockSignals(False)

            self.working_input_dict[name] = value

    def showEvent(self, event):  # Qt event: refreshes active sub-tabs when dialog is shown or reopened
        super().showEvent(event)
        from PySide6.QtWidgets import QTabWidget
        for tab_widget in self.findChildren(QTabWidget):
            if hasattr(tab_widget, "refresh_active_tab"):
                tab_widget.refresh_active_tab()

    # ── Dialog Persistence ───────────────────────────────────────────────────────

    def _save_inputs(self):  # on_change: validates all tabs then commits working_input_dict and emits CAD update signal

        self.default_input_dict.update(self.working_input_dict)
        self.update_template_page_2d_cad.emit(self.cad_preview.params)

        CustomMessageBox(
            title="Saved",
            text="Inputs saved successfully.",
            buttons=["OK"],
            dialogType=MessageBoxType.Success,
        ).exec()
    def _show_validation_errors(self, errors):  # utility: displays validation error list in a warning popup
        message = "\n\n".join(f"• {err}" for err in errors)
        CustomMessageBox(
            title="Validation Errors",
            text=message,
            buttons=["OK"],
            dialogType=MessageBoxType.Warning,
        ).exec()

    def _collect_all_values(self):  # utility: harvests current widget values into saved_values dict across all tabs
        for widget in self.findChildren(QWidget):
            widget_name = widget.objectName()
            if not widget_name:
                continue
            if isinstance(widget, QLineEdit):
                self.saved_values[widget_name] = widget.text()
            elif isinstance(widget, QComboBox):
                self.saved_values[widget_name] = widget.currentText()
            elif isinstance(widget, QCheckBox):
                self.saved_values[widget_name] = widget.isChecked()
            elif isinstance(widget, LoadCombinationWidget):
                self.saved_values[widget_name] = widget._data

    def get_saved_data(self) -> dict:  # public API: returns the last saved properties snapshot
        """Get the last saved properties data."""
        return self._last_saved_data.copy()

    # ── Field Change Handling ────────────────────────────────────────────────────

    def _on_field_edited(self, key: str, widget: QLineEdit | str | dict):  # on_change: hard-validates and commits a field value after editing finishes
        """
        Called on editingFinished (QLineEdit) or currentTextChanged (QComboBox).
        - QComboBox: always valid, skip validation, update dict + CAD.
        - QLineEdit: hard validation — corrects widget + input_dict if invalid, shows popup.
        """
        if isinstance(widget, str):
            self._update_input_dict(key, widget)
            self._update_additional_input_cad()
            return

        if isinstance(widget, dict):
            self._update_input_dict(key, widget)
            return

        if isinstance(widget, bool):
            self._update_input_dict(key, widget)
            self._update_additional_input_cad()
            return

        if isinstance(widget, list):
            self._update_input_dict(key, widget)
            return

        current_text = widget.text().strip()
        self._update_input_dict(key, current_text)

        result = self.validator.validate_additional_inputs(key, self.working_input_dict)
        print(f"@@: After Edited Validation result for {key} = {result}")
        if result is not None:
            corrected, message = result
            CustomMessageBox(
                title="Input Error",
                text=message,
                dialogType=MessageBoxType.Warning
            ).exec()
            widget.blockSignals(True)
            widget.setText(str(corrected))
            widget.blockSignals(False)
            self._update_input_dict(key, str(corrected))

        self._update_additional_input_cad()

    def _on_field_editing(self, current_text: str, key: str):  # on_change: soft validation while typing — updates dict/CAD only when valid, no popups
        if not current_text.strip():
            self._update_input_dict(key, "")
            self._update_additional_input_cad()
            return

        self._update_input_dict(key, current_text)

        result = self.validator.validate_additional_inputs(key, self.working_input_dict)
        if result is not None:
            return  # still typing, value not valid yet

        self._update_additional_input_cad()

    def _update_input_dict(self, key: str, value: str):  # utility: writes a value to working_input_dict, falling back to default if empty
        if value is None or value == "":
            self.working_input_dict[key] = self.default_input_dict.get(key)
        else:
            try:
                self.working_input_dict[key] = int(value)
            except (ValueError, TypeError):
                try:
                    self.working_input_dict[key] = float(value)
                except (ValueError, TypeError):
                    self.working_input_dict[key] = value

    def _update_additional_input_cad(self):  # compute: pushes current working_input_dict to the Typical Section CAD preview
        self.cad_preview.update_from_bridge_inputs(self.working_input_dict)

    def update_internal_cad_state(self, cad_state):  # public API: syncs homepage CAD state into the cross-section preview
        self._initial_cad_state = cad_state
        self.cad_preview.update_params(self._initial_cad_state)

    def update_carriageway_width(self, carriageway_width):  # public API: updates carriageway width and re-initializes lane defaults
        if carriageway_width and carriageway_width != self.carriageway_width:
            self.carriageway_width = carriageway_width
            self._initialize_lane_defaults()

    # ── Member Properties > Girder Details ───────────────────────────────────────

    # Keys stored per-member (G{i}.M{j}) for Girder Details tab save/load
    _MEMBER_FIELD_KEYS = [
        KEY_MP_GIRDER_TYPE, KEY_MP_GIRDER_SYMMETRY, KEY_MP_GIRDER_DEPTH,
        KEY_MP_GIRDER_TOP_FLANGE_WIDTH, KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
        KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH, KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
        KEY_MP_GD_SUPPORT_TYPE, KEY_MP_GD_SUPPORT_WIDTH, KEY_MP_GIRDER_WEB_THICKNESS,
        KEY_MP_GIRDER_IS_SECTION, KEY_MP_GIRDER_TORSIONAL_RESTRAINT,
        KEY_MP_GIRDER_WARPING_RESTRAINT, KEY_MP_GIRDER_WEB_TYPE,
        KEY_MP_GIRDER_MASS, KEY_MP_GIRDER_SECTIONAL_AREA,
        KEY_MP_GIRDER_SECTIONAL_IY, KEY_MP_GIRDER_SECTIONAL_IZ,
        KEY_MP_GIRDER_RADIUS_GYRATION_Y, KEY_MP_GIRDER_RADIUS_GYRATION_Z,
        KEY_MP_GIRDER_ELASTIC_MODULUS_ZZ, KEY_MP_GIRDER_ELASTIC_MODULUS_ZY,
        KEY_MP_GIRDER_PLASTIC_MODULUS_ZUZ, KEY_MP_GIRDER_PLASTIC_MODULUS_ZUY,
        KEY_MP_GIRDER_TORSION_CONSTANT_IT, KEY_MP_GIRDER_WARPING_CONSTANT_IW,
    ]

    def _update_apply_button_visibility(self, origin_key: str, target_widget: QWidget) -> None:  # END_CONNECTOR: shows Exterior/Interior Apply button based on selected girder position
        """Show/hide Apply Exterior or Apply Interior button based on selected girder index."""
        count = int(float(str(self.working_input_dict.get(KEY_TS_NO_OF_GIRDERS) or 1)))

        combo = self.findChild(QComboBox, KEY_MP_GD_SELECT_GIRDER)
        if combo is None:
            return
        idx = combo.currentIndex()
        is_exterior = (count <= 1) or (idx == 0 or idx == count - 1)

        widget_id = target_widget.objectName()
        if widget_id == KEY_MP_GD_APPLY_EXTERIOR:
            target_widget.setVisible(is_exterior)
        elif widget_id == KEY_MP_GD_APPLY_INTERIOR:
            target_widget.setVisible(not is_exterior)

    def _on_girder_count_refreshed(self, origin_key: str, current_object: QComboBox) -> None:  # END_CONNECTOR: repopulates Select Girder combo when girder count changes
        value = self.working_input_dict.get(origin_key)
        if value is None:
            return

        count = int(float(str(value)))
        current = current_object.currentText()
        current_object.clear()
        for i in range(1, count + 1):
            if i == 1 or i == count:
                current_object.addItem(f"Girder {i} (Exterior)", f"G{i}")
            else:
                current_object.addItem(f"Girder {i} (Interior)", f"G{i}")
        idx = current_object.findText(current)
        current_object.setCurrentIndex(idx if idx >= 0 else 0)

        cad = self.findChild(QWidget, KEY_MP_GD_CAD_PREVIEW)
        if cad:
            cad.update_cad_state(self.working_input_dict)

    def _on_girder_type_changed(self, girder_type: str) -> None:  # on_change: shows welded or rolled section fields based on girder type selection
        is_welded = girder_type.strip().lower() == "welded"

        welded_keys = [
            KEY_MP_GIRDER_SYMMETRY, KEY_MP_GIRDER_DEPTH, KEY_MP_GIRDER_TOP_FLANGE_WIDTH,
            KEY_MP_GIRDER_TOP_FLANGE_THICKNESS, KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH,
            KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS, KEY_MP_GD_SUPPORT_TYPE,
            KEY_MP_GD_SUPPORT_WIDTH, KEY_MP_GIRDER_WEB_THICKNESS, KEY_MP_GIRDER_WEB_TYPE,
        ]
        rolled_keys = [KEY_MP_GIRDER_IS_SECTION]

        for key in welded_keys:
            w   = self.findChild(QWidget, key)
            lbl = self.findChild(QLabel, key + "_label")
            if w:   w.setVisible(is_welded)
            if lbl: lbl.setVisible(is_welded)

        for key in rolled_keys:
            w   = self.findChild(QWidget, key)
            lbl = self.findChild(QLabel, key + "_label")
            if w:   w.setVisible(not is_welded)
            if lbl: lbl.setVisible(not is_welded)

        self._update_section_drawing()

    def _on_girder_segments_load(self, origin_key: str, target_widget: QWidget) -> None:  # END_CONNECTOR: loads stored segments for the selected girder into SegmentTableWidget
        from osdagbridge.desktop.ui.dialogs.additional_input.ui_builder._segment_table_widget import SegmentTableWidget
        if not isinstance(target_widget, SegmentTableWidget):
            return

        combo = self.findChild(QComboBox, origin_key)
        if combo is None:
            print(f"@@: Girder selection combo not found for loading segments.")
            return

        girder_id = f"G{combo.currentIndex() + 1}"
        seg_key   = f"{KEY_MP_GD_SEGMENT_TABLE}.{girder_id}"

        segments = self.working_input_dict.get(seg_key)
        print(f"@@: Loading segments for {girder_id} with key={seg_key}, segments={segments}")
        total_span = float(self.working_input_dict.get(KEY_SPAN))
        if not segments:
            segments = [{"id": f"{girder_id}M1", "start": 0.0, "end": total_span}]
            self.working_input_dict[seg_key] = segments

        target_widget.set_total_span(total_span)
        target_widget.refresh(segments)

        # Highlight the selected girder in the cross-section preview.
        cad = self.findChild(QWidget, KEY_MP_GD_CAD_PREVIEW)
        if cad:
            cad.update_selected_girder(combo.currentIndex())

    def _on_segment_selected(self, row: int, member_id: str) -> None:  # on_change: highlights the clicked segment member on the CAD preview canvas
        from osdagbridge.core.utils.common import KEY_MP_GD_CAD_PREVIEW
        cad = self.findChild(QWidget, KEY_MP_GD_CAD_PREVIEW)
        if cad and hasattr(cad, "update_selected_member"):
            cad.update_selected_member(member_id)

    def _on_segment_data_changed(self, segments) -> None:  # on_change: writes updated segment list to working_input_dict and refreshes CAD preview
        if not isinstance(segments, list):
            return

        combo = self.findChild(QComboBox, KEY_MP_GD_SELECT_GIRDER)
        if combo is None:
            return

        idx = combo.currentIndex()   # 0-based → G1 = index 0
        girder_key = f"{KEY_MP_GD_SEGMENT_TABLE}.G{idx + 1}"

        self.working_input_dict[girder_key] = segments

        cad = self.findChild(QWidget, KEY_MP_GD_CAD_PREVIEW)
        cad.update_segments(segments)

    def _on_segment_members_refreshed(self, origin_key: str, target_widget: QWidget) -> None:  # END_CONNECTOR: populates Member ID combo from the current girder's segment list
        if not isinstance(target_widget, QComboBox):
            return

        idx       = self.findChild(QComboBox, KEY_MP_GD_SELECT_GIRDER)
        girder_id = f"G{idx.currentIndex() + 1}" if idx else "G1"
        seg_key   = f"{KEY_MP_GD_SEGMENT_TABLE}.{girder_id}"
        segments  = self.working_input_dict.get(seg_key, [])

        member_ids = [str(seg.get("id", "")) for seg in segments if seg.get("id")]

        current = target_widget.currentText()
        target_widget.clear()
        target_widget.addItems(member_ids)
        idx_restore = target_widget.findText(current)
        target_widget.setCurrentIndex(idx_restore if idx_restore >= 0 else 0)

        from osdagbridge.core.bridge_types.plate_girder.defaults import _extend_member_field_keys
        _extend_member_field_keys(
            working_input_dict = self.working_input_dict,
            girder_id          = girder_id,
            member_field_keys  = self._MEMBER_FIELD_KEYS,
        )

        self._update_stiffener_cad()

    def _on_member_id_load(self, origin_key: str, target_widget: QWidget) -> None:  # END_CONNECTOR: loads stored girder field values for the newly selected member
        import re
        if not isinstance(target_widget, QComboBox):
            return
        value = target_widget.currentText()
        match = re.match(r"G(\d+)M(\d+)", str(value or "").strip())
        if not match:
            return
        gi, mi = int(match.group(1)), int(match.group(2))
        print(f"[MEMBER_ID_LOAD] G{gi}.M{mi}")
        self._load_member_fields(gi, mi)
        self._update_section_drawing()

    def _save_member_fields_connector(self, origin_key: str, target_widget: QWidget) -> None:  # END_CONNECTOR: triggers save of current member's girder fields on any section input change
        self._save_member_fields()

    def _get_current_girder_member_indices(self) -> tuple[int, int]:  # utility: returns (girder_index, member_index) 1-based from current combo selections
        girder_combo = self.findChild(QComboBox, KEY_MP_GD_SELECT_GIRDER)
        member_combo = self.findChild(QComboBox, KEY_MP_GD_MEMBER_ID)
        gi = (girder_combo.currentIndex() + 1) if girder_combo else 1
        mi = (member_combo.currentIndex() + 1) if member_combo else 1
        return gi, mi

    def _save_member_fields(self) -> None:  # utility: serialises all Girder Details widget values into working_input_dict under G{i}.M{j} keys
        gi, mi = self._get_current_girder_member_indices()
        suffix = f".G{gi}.M{mi}"
        # print(f"[SAVE_MEMBER_FIELDS] G{gi}.M{mi}")

        for key in self._MEMBER_FIELD_KEYS:
            w = self.findChild(QWidget, key)

            if isinstance(w, AdaptiveWidget):
                active = w.currentWidget()
                if isinstance(active, QComboBox):
                    mode = active.currentText()
                    self.working_input_dict[key + suffix] = mode
                elif isinstance(active, QLineEdit):
                    self.working_input_dict[key + suffix] = active.text()
                elif isinstance(active, QPushButton):
                    existing = self.working_input_dict.get(key)
                    if existing is not None:
                        self.working_input_dict[key + suffix] = existing
                else:
                    print(f"  [SAVE] {key} — AdaptiveWidget active child unknown: {type(active)}")

            elif isinstance(w, QComboBox):
                self.working_input_dict[key + suffix] = w.currentText()

            elif isinstance(w, QLineEdit):
                self.working_input_dict[key + suffix] = w.text()

            else:
                if isinstance(w, QWidget):
                    inner_combo = w.findChild(QComboBox)
                    inner_line  = w.findChild(QLineEdit)
                    if inner_combo:
                        self.working_input_dict[key + suffix + ".mode"] = inner_combo.currentText()
                    if inner_line:
                        text = inner_line.text().strip()
                        if text:
                            self.working_input_dict[key + suffix + ".value"] = text
                else:
                    print(f"  [SAVE] {key} — widget not found: {type(w)}")

    def _load_member_fields(self, gi: int, mi: int) -> None:  # utility: restores Girder Details widgets from working_input_dict G{i}.M{j} keys
        suffix = f".G{gi}.M{mi}"
        # print(f"[LOAD] G{gi}.M{mi}")

        for key in self._MEMBER_FIELD_KEYS:
            value = self.working_input_dict.get(key + suffix)
            if value is None:
                continue

            w = self.findChild(QWidget, key)

            if isinstance(w, AdaptiveWidget):
                active = w.currentWidget()
                if isinstance(active, QComboBox):
                    active.blockSignals(True)
                    active.setCurrentText(str(value))
                    active.blockSignals(False)
                    self.working_input_dict[key] = value
                    selected = self.working_input_dict.get(key + ".selected" + suffix)
                    if selected is not None:
                        self.working_input_dict[key + ".selected"] = selected
                elif isinstance(active, QLineEdit):
                    active.blockSignals(True)
                    active.setText(str(value))
                    active.blockSignals(False)
                elif isinstance(active, QPushButton):
                    if value is not None:
                        self.working_input_dict[key] = value
                else:
                    print(f"  [LOAD] {key} — AdaptiveWidget active child unknown: {type(active)}")

            elif isinstance(w, QComboBox):
                w.blockSignals(True)
                w.setCurrentText(str(value))
                w.blockSignals(False)

            elif isinstance(w, QLineEdit):
                w.blockSignals(True)
                if ("section_properties" in key or "material_properties" in key) and isinstance(value, (int, float)):
                    w.setText(f"{value:.2e}")
                else:
                    w.setText(str(value))
                w.blockSignals(False)

            else:
                if isinstance(w, QWidget):
                    inner_combo = w.findChild(QComboBox)
                    inner_line  = w.findChild(QLineEdit)
                    mode_val  = self.working_input_dict.get(key + suffix + ".mode")
                    value_val = self.working_input_dict.get(key + suffix + ".value")
                    if inner_combo and mode_val:
                        inner_combo.blockSignals(True)
                        inner_combo.setCurrentText(str(mode_val))
                        inner_combo.blockSignals(False)
                    if inner_line and value_val:
                        inner_line.blockSignals(True)
                        inner_line.setText(str(value_val))
                        inner_line.blockSignals(False)
                else:
                    print(f"  [LOAD] {key} — widget not found: {type(w)}")

        # Update symmetry-dependent widget states after loading
        self._on_symmetry_changed()

    def _on_bounds_accepted(self, field_id: str, result: dict) -> None:  # on_change: stores BoundsButton result under the current member's dynamic key
        gi, mi = self._get_current_girder_member_indices()
        suffix = f".G{gi}.M{mi}"
        self.working_input_dict[field_id + suffix] = result
        print(f"[BOUNDS_ACCEPTED] {field_id + suffix} = {result}")

    def _on_all_custom_selected(self, field_id: str, chosen: list) -> None:  # on_change: stores TYPE_ALL_CUSTOM selection list under the current member's dynamic key
        gi, mi = self._get_current_girder_member_indices()
        suffix = f".G{gi}.M{mi}"
        self.working_input_dict[field_id + ".selected" + suffix] = chosen
        self.working_input_dict[field_id + suffix] = "Custom"
        print(f"[ALL_CUSTOM_SELECTED] {field_id}.selected{suffix} = {chosen}")

    def _copy_girder_properties(self, source_g: int, target_g: int) -> None:
        import copy, re
        pattern = re.compile(rf"\.G{source_g}\.M(\d+)$")
        keys_to_copy = [k for k in self.working_input_dict.keys() if pattern.search(k)]
        for k in keys_to_copy:
            new_key = k.replace(f".G{source_g}.", f".G{target_g}.")
            self.working_input_dict[new_key] = copy.deepcopy(self.working_input_dict[k])

    def _on_apply_exterior_clicked(self) -> None:  # on_change: applies current girder settings to first and last girders
        gi, _ = self._get_current_girder_member_indices()
        count = int(float(str(self.working_input_dict.get(KEY_TS_NO_OF_GIRDERS, 1))))
        targets = {1, count} - {gi}
        for target_g in targets:
            self._copy_girder_properties(gi, target_g)
        print(f"@@: Applied Girder {gi} settings to exterior girders: {targets}")

    def _on_apply_interior_clicked(self) -> None:  # on_change: applies current girder settings to all interior girders
        gi, _ = self._get_current_girder_member_indices()
        count = int(float(str(self.working_input_dict.get(KEY_TS_NO_OF_GIRDERS, 1))))
        targets = set(range(2, count)) - {gi}
        for target_g in targets:
            self._copy_girder_properties(gi, target_g)
        print(f"@@: Applied Girder {gi} settings to interior girders: {targets}")

    def _on_top_flange_changed(self) -> None:
        gi, mi = self._get_current_girder_member_indices()
        suffix = f".G{gi}.M{mi}"

        # Always update drawing with the changed top flange value
        self._update_section_drawing()

        sym_val = self.working_input_dict.get(KEY_MP_GIRDER_SYMMETRY + suffix, "Girder Symmetric")
        if sym_val.strip().lower() != "girder symmetric":
            return  # unsymmetric — nothing to mirror

        # Read live widget values
        tw_w = self.findChild(QWidget, KEY_MP_GIRDER_TOP_FLANGE_WIDTH)
        tt_w = self.findChild(QWidget, KEY_MP_GIRDER_TOP_FLANGE_THICKNESS)
        bw_w = self.findChild(QWidget, KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH)
        bt_w = self.findChild(QWidget, KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS)

        def _read(w):
            if isinstance(w, QLineEdit): return w.text().strip() or None
            if isinstance(w, QComboBox): return w.currentText() or None
            if isinstance(w, AdaptiveWidget):
                a = w.currentWidget()
                if isinstance(a, QLineEdit): return a.text().strip() or None
                if isinstance(a, QComboBox): return a.currentText() or None
            return None

        def _write(w, val):
            if isinstance(w, QLineEdit): w.setText(str(val))
            elif isinstance(w, QComboBox): w.setCurrentText(str(val))
            elif isinstance(w, AdaptiveWidget):
                a = w.currentWidget()
                if isinstance(a, QLineEdit): a.setText(str(val))
                elif isinstance(a, QComboBox): a.setCurrentText(str(val))

        tw_val = _read(tw_w)
        tt_val = _read(tt_w)

        if tw_val is not None:
            _write(bw_w, tw_val)
            self.working_input_dict[KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH + suffix] = tw_val
            self.working_input_dict[KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH] = tw_val

        if tt_val is not None:
            _write(bt_w, tt_val)
            self.working_input_dict[KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS + suffix] = tt_val
            self.working_input_dict[KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS] = tt_val

        self._update_section_drawing()

    def _on_symmetry_changed(self, symmetry: str = None) -> None:
        gi, mi = self._get_current_girder_member_indices()
        suffix = f".G{gi}.M{mi}"

        if symmetry is None:
            symmetry = str(self.working_input_dict.get(KEY_MP_GIRDER_SYMMETRY + suffix, "Girder Symmetric"))

        self.working_input_dict[KEY_MP_GIRDER_SYMMETRY + suffix] = symmetry

        is_symmetric = symmetry.strip().lower() == "girder symmetric"

        bw = self.findChild(QWidget, KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH)
        bt = self.findChild(QWidget, KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS)
        if bw: bw.setEnabled(not is_symmetric)
        if bt: bt.setEnabled(not is_symmetric)

        if is_symmetric:
            self._on_top_flange_changed()  # reuse — does the mirror + drawing update
        else:
            self._update_section_drawing()

    def _on_torsional_restraint_changed(self, restraint: str) -> None:
        gi, mi = self._get_current_girder_member_indices()

        from osdagbridge.core.utils.common import KEY_MP_GIRDER_WARPING_RESTRAINT

        # If the restraint is one of the "Partially Restrained" options (the bottom two)
        if restraint.startswith("Partially Restrained"):
            warping_val = "No Restraint"
            suffix = f".G{gi}.M{mi}"

            # Update the widget if it exists
            wr_widget = self.findChild(QWidget, KEY_MP_GIRDER_WARPING_RESTRAINT)
            if wr_widget and isinstance(wr_widget, QComboBox):
                wr_widget.setCurrentText(warping_val)

            # Update the working dict
            self.working_input_dict[KEY_MP_GIRDER_WARPING_RESTRAINT + suffix] = warping_val

    def _on_warping_restraint_changed(self, warping: str) -> None:
        gi, mi = self._get_current_girder_member_indices()

        from osdagbridge.core.utils.common import KEY_MP_GIRDER_TORSIONAL_RESTRAINT

        if warping.strip().lower() == "both flanges restrained":
            torsional_val = "Fully Restrained"
            suffix = f".G{gi}.M{mi}"

            # Update the widget if it exists
            tr_widget = self.findChild(QWidget, KEY_MP_GIRDER_TORSIONAL_RESTRAINT)
            if tr_widget and isinstance(tr_widget, QComboBox):
                tr_widget.setCurrentText(torsional_val)

            # Update the working dict
            self.working_input_dict[KEY_MP_GIRDER_TORSIONAL_RESTRAINT + suffix] = torsional_val

    def _update_section_drawing(self) -> None:  # compute: rebuilds the Girder Details section drawing preview from live widget values
        from osdagbridge.core.utils.common import KEY_MP_GD_SECTION_PREVIEW
        from osdagbridge.desktop.ui.dialogs.additional_input.drawings.rolled_section_preview import RolledSectionPreview
        widget = self.findChild(RolledSectionPreview, KEY_MP_GD_SECTION_PREVIEW)
        if widget is None:
            return

        # Build snapshot — prefer live widget value over working_input_dict
        # because on_change fires before _on_field_edited updates the dict.
        snapshot = dict(self.working_input_dict)

        from osdagbridge.core.utils.common import (
            KEY_MP_GIRDER_TYPE, KEY_MP_GIRDER_IS_SECTION,
            KEY_MP_GIRDER_DEPTH, KEY_MP_GIRDER_TOP_FLANGE_WIDTH, KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH,
            KEY_MP_GIRDER_TOP_FLANGE_THICKNESS, KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
            KEY_MP_GIRDER_WEB_THICKNESS,
        )

        for key in [
            KEY_MP_GIRDER_TYPE, KEY_MP_GIRDER_IS_SECTION,
            KEY_MP_GIRDER_DEPTH, KEY_MP_GIRDER_TOP_FLANGE_WIDTH, KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH,
            KEY_MP_GIRDER_TOP_FLANGE_THICKNESS, KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
            KEY_MP_GIRDER_WEB_THICKNESS,
        ]:
            w = self.findChild(QWidget, key)
            if isinstance(w, QComboBox):
                snapshot[key] = w.currentText()
            elif isinstance(w, QLineEdit):
                snapshot[key] = w.text().strip()
            elif isinstance(w, AdaptiveWidget):
                active = w.currentWidget()
                if isinstance(active, QComboBox):
                    snapshot[key] = active.currentText()
                elif isinstance(active, QLineEdit):
                    snapshot[key] = active.text().strip()

        widget.update_section(snapshot)

    def _compute_rolled_section_properties(self, working_input_dict: dict) -> dict:  # compute: looks up rolled I-section properties from catalog by designation
        from osdagbridge.core.utils.common import GirderSectionCatalog

        designation = working_input_dict.get(KEY_MP_GIRDER_IS_SECTION, "")
        if not designation:
            return {}

        girder_properties = GirderSectionCatalog()
        section = girder_properties.get_beam_profile(str(designation).strip())
        if section is None:
            return {}

        # DB columns are _cm2, _cm4, _cm, _cm3, _cm6 → convert to m², m⁴, m, m³, m⁶ (match UI labels)
        return {
            KEY_MP_GIRDER_MASS:                f"{section.mass_per_meter_kg:.2e}",
            KEY_MP_GIRDER_SECTIONAL_AREA:      f"{section.area_cm2 * 1e-4:.2e}",          # cm² → m²
            KEY_MP_GIRDER_SECTIONAL_IZ:        f"{section.moment_of_inertia_zz_cm4 * 1e-8:.2e}",  # cm⁴ → m⁴
            KEY_MP_GIRDER_SECTIONAL_IY:        f"{section.moment_of_inertia_yy_cm4 * 1e-8:.2e}",  # cm⁴ → m⁴
            KEY_MP_GIRDER_RADIUS_GYRATION_Z:   f"{section.radius_of_gyration_z_cm * 1e-2:.2e}",  # cm → m
            KEY_MP_GIRDER_RADIUS_GYRATION_Y:   f"{section.radius_of_gyration_y_cm * 1e-2:.2e}",  # cm → m
            KEY_MP_GIRDER_ELASTIC_MODULUS_ZZ:  f"{section.elastic_section_modulus_z_cm3 * 1e-6:.2e}",  # cm³ → m³
            KEY_MP_GIRDER_ELASTIC_MODULUS_ZY:  f"{section.elastic_section_modulus_y_cm3 * 1e-6:.2e}",  # cm³ → m³
            KEY_MP_GIRDER_PLASTIC_MODULUS_ZUZ: f"{section.plastic_section_modulus_z_cm3 * 1e-6:.2e}",  # cm³ → m³
            KEY_MP_GIRDER_PLASTIC_MODULUS_ZUY: f"{section.plastic_section_modulus_y_cm3 * 1e-6:.2e}",  # cm³ → m³
            KEY_MP_GIRDER_TORSION_CONSTANT_IT: f"{section.torsion_constant_cm4 * 1e-8:.2e}",  # cm⁴ → m⁴
            KEY_MP_GIRDER_WARPING_CONSTANT_IW: f"{section.warping_constant_cm6 * 1e-12:.2e}", # cm⁶ → m⁶
        }

    def _compute_welded_section_properties(self, working_input_dict: dict) -> dict:  # compute: derives welded I-section properties from flange/web dimensions
        from osdagbridge.core.bridge_types.plate_girder.initial_sizing import BridgeConfigurationSolver

        def _to_m(key: str) -> float:
            val = working_input_dict.get(key)
            if val is None or isinstance(val, (dict, list)):
                return 0.0
            try:
                return float(val) / 1000.0
            except (ValueError, TypeError):
                return 0.0

        depth_m  = _to_m(KEY_MP_GIRDER_DEPTH)
        b_top_m  = _to_m(KEY_MP_GIRDER_TOP_FLANGE_WIDTH)
        b_bot_m  = _to_m(KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH)
        tf_top_m = _to_m(KEY_MP_GIRDER_TOP_FLANGE_THICKNESS)
        tf_bot_m = _to_m(KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS)
        tw_m     = _to_m(KEY_MP_GIRDER_WEB_THICKNESS)

        if not depth_m or not b_top_m:
            return {}

        try:
            span_m = float(working_input_dict.get(KEY_MP_GD_TOTAL_SPAN) or 30.0)
        except (ValueError, TypeError):
            span_m = 30.0

        symmetry = str(working_input_dict.get(KEY_MP_GIRDER_SYMMETRY) or "Girder Symmetric")

        try:
            result = BridgeConfigurationSolver(carriageway_width=1.0).compute_section_properties(
                span=span_m,
                symmetry=symmetry,
                user_depth=depth_m,
                B_top=b_top_m,
                B_bot=b_bot_m,
                t_f_top=tf_top_m,
                t_f_bot=tf_bot_m,
                t_w=tw_m,
            )
        except Exception:
            return {}

        # Outputs are already in SI (m², m⁴, m³, m⁶) — same as UI labels
        return {
            KEY_MP_GIRDER_MASS:                f"{result['Mass']:.2e}",
            KEY_MP_GIRDER_SECTIONAL_AREA:      f"{result['Area']:.2e}",
            KEY_MP_GIRDER_SECTIONAL_IZ:        f"{result['I_z']:.2e}",
            KEY_MP_GIRDER_SECTIONAL_IY:        f"{result['I_y']:.2e}",
            KEY_MP_GIRDER_RADIUS_GYRATION_Z:   f"{result['r_z']:.2e}",
            KEY_MP_GIRDER_RADIUS_GYRATION_Y:   f"{result['r_y']:.2e}",
            KEY_MP_GIRDER_ELASTIC_MODULUS_ZZ:  f"{result['Z_ez']:.2e}",
            KEY_MP_GIRDER_ELASTIC_MODULUS_ZY:  f"{result['Z_ey']:.2e}",
            KEY_MP_GIRDER_PLASTIC_MODULUS_ZUZ: f"{result['Z_pz']:.2e}",
            KEY_MP_GIRDER_PLASTIC_MODULUS_ZUY: f"{result['Z_py']:.2e}",
            KEY_MP_GIRDER_TORSION_CONSTANT_IT: f"{result['I_t']:.2e}",
            KEY_MP_GIRDER_WARPING_CONSTANT_IW: f"{result['I_w']:.2e}",
        }

    # ── Member Properties > Stiffener Details ────────────────────────────────────

    # Keys stored per-member (G{i}.M{j}) for Stiffener Details tab save/load
    _STIFFENER_FIELD_KEYS = [
        KEY_MP_STIFFENER_NO_BEARING_STIFFENERS,
        KEY_MP_STIFFENER_SPACING,
        KEY_MP_STIFFENER_BEARING_THICKNESS,
        KEY_MP_STIFFENER_BEARING_OUTSTAND,
        KEY_MP_STIFFENER_INTERMEDIATE,
        KEY_MP_STIFFENER_INTERMEDIATE_SPACING,
        KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS,
        KEY_MP_STIFFENER_INTERMEDIATE_OUTSTAND,
        KEY_MP_STIFFENER_LONGITUDINAL,
        KEY_MP_STIFFENER_LONGITUDINAL_THICKNESS,
        KEY_MP_STIFFENER_DESIGN_METHOD,
    ]

    def _on_stiffener_member_ids_refreshed(self, origin_key: str, target_widget: QWidget) -> None:  # END_CONNECTOR: collects member IDs from all girders and populates Stiffener member ID combo
        if not isinstance(target_widget, QComboBox):
            return

        girder_count = int(float(str(self.working_input_dict.get(KEY_TS_NO_OF_GIRDERS) or 1)))
        all_member_ids = []
        for gi in range(1, girder_count + 1):
            seg_key  = f"{KEY_MP_GD_SEGMENT_TABLE}.G{gi}"
            segments = self.working_input_dict.get(seg_key) or []
            for seg in segments:
                mid = str(seg.get("id") or "")
                if mid:
                    all_member_ids.append(mid)

        current = target_widget.currentText()
        target_widget.blockSignals(True)
        target_widget.clear()
        target_widget.addItems(all_member_ids)
        idx = target_widget.findText(current)
        target_widget.setCurrentIndex(idx if idx >= 0 else 0)
        target_widget.blockSignals(False)

    def _on_stiffener_member_bearing_changed(self, origin_key: str, target_widget: QWidget) -> None:  # END_CONNECTOR: shows bearing stiffener fields only for first (M1) or last (Mn) member in the girder
        import re
        combo = self.findChild(QComboBox, origin_key)
        if combo is None:
            return
        member_id = combo.currentText().strip()
        match = re.match(r"G(\d+)M(\d+)", member_id)
        if not match:
            return
        gi      = int(match.group(1))
        mi      = int(match.group(2))
        total   = len(self.working_input_dict.get(f"{KEY_MP_GD_SEGMENT_TABLE}.G{gi}") or [])
        is_bearing = (total <= 1) or (mi == 1 or mi == total)

        lbl = self.findChild(QLabel, KEY_MP_STIFFENER_NO_BEARING_STIFFENERS + "_label")
        target_widget.setVisible(is_bearing)
        if lbl: lbl.setVisible(is_bearing)

        for key in [KEY_MP_STIFFENER_SPACING, KEY_MP_STIFFENER_BEARING_THICKNESS, KEY_MP_STIFFENER_BEARING_OUTSTAND]:
            w   = self.findChild(QWidget, key)
            lbl = self.findChild(QLabel,  key + "_label")
            if w:   w.setVisible(is_bearing)
            if lbl: lbl.setVisible(is_bearing)

    def _on_stiffener_member_load(self, origin_key: str, target_widget: QWidget) -> None:  # END_CONNECTOR: saves previous member's stiffener data then loads the newly selected member's data
        combo = self.findChild(QComboBox, origin_key)
        if combo is None:
            return
        new_member_id  = combo.currentText().strip()
        prev_member_id = getattr(self, "_last_stiffener_member_id", None)

        if prev_member_id:
            self._save_stiffener_member_data(prev_member_id)

        self._load_stiffener_member_data(new_member_id)
        self._last_stiffener_member_id = new_member_id

        w = self.findChild(QComboBox, KEY_MP_STIFFENER_INTERMEDIATE)
        if w:
            self._on_intermediate_stiffener_changed(w.currentText())
        w = self.findChild(QComboBox, KEY_MP_STIFFENER_LONGITUDINAL)
        if w:
            self._on_longitudinal_stiffener_changed(w.currentText())

        self._update_stiffener_cad()

    def _on_intermediate_stiffener_changed(self, value: str) -> None:  # on_change: enables or disables intermediate stiffener sub-fields based on Yes/No selection
        is_yes = str(value).strip() == "Yes"
        for key in [
            KEY_MP_STIFFENER_INTERMEDIATE_SPACING,
            KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS,
            KEY_MP_STIFFENER_INTERMEDIATE_OUTSTAND,
        ]:
            w   = self.findChild(QWidget, key)
            lbl = self.findChild(QLabel,  key + "_label")
            if w:   w.setEnabled(is_yes)
            if lbl: lbl.setEnabled(is_yes)

        self._update_stiffener_cad()

    def _on_longitudinal_stiffener_changed(self, value: str) -> None:  # on_change: enables or disables longitudinal thickness field based on selection
        is_yes = str(value).strip() != "No"
        w   = self.findChild(QWidget, KEY_MP_STIFFENER_LONGITUDINAL_THICKNESS)
        lbl = self.findChild(QLabel,  KEY_MP_STIFFENER_LONGITUDINAL_THICKNESS + "_label")
        if w:   w.setEnabled(is_yes)
        if lbl: lbl.setEnabled(is_yes)
        self._update_stiffener_cad()

    def _save_stiffener_member_data(self, member_id: str) -> None:  # utility: serialises stiffener widget values into working_input_dict under G{i}.M{j} suffix
        import re
        m = re.match(r"G(\d+)M(\d+)", str(member_id or "").strip())
        suffix = f".G{m.group(1)}.M{m.group(2)}" if m else ""

        if not suffix:
            return
        for key in self._STIFFENER_FIELD_KEYS:
            w = self.findChild(QWidget, key)
            if isinstance(w, QComboBox):
                self.working_input_dict[f"{key}{suffix}"] = w.currentText()
            elif isinstance(w, QLineEdit):
                self.working_input_dict[f"{key}{suffix}"] = w.text()

    def _load_stiffener_member_data(self, member_id: str) -> None:  # utility: restores stiffener widgets from working_input_dict G{i}.M{j} entries
        import re
        m = re.match(r"G(\d+)M(\d+)", str(member_id or "").strip())
        suffix = f".G{m.group(1)}.M{m.group(2)}" if m else ""

        if not suffix:
            return
        for key in self._STIFFENER_FIELD_KEYS:
            stored = self.working_input_dict.get(f"{key}{suffix}")
            if stored is None:
                continue
            w = self.findChild(QWidget, key)
            if isinstance(w, QComboBox):
                w.setCurrentText(str(stored))
            elif isinstance(w, QLineEdit):
                w.setText(str(stored))

    def _update_stiffener_cad(self) -> None:  # compute: pushes current working_input_dict and active member ID to the Stiffener Details CAD widget
        from osdagbridge.desktop.ui.dialogs.additional_input.drawings.stiffener_details_cad import StiffenerDetailsCad
        widget = self.findChild(StiffenerDetailsCad, KEY_SD_STIFFENER_DETAILS)
        if widget is None:
            return
        combo = self.findChild(QComboBox, KEY_MP_STIFFENER_SELECT_MEMBER_ID)
        active_member_id = combo.currentText().strip() if combo else ""
        widget.update_stiffener(self.working_input_dict, active_member_id)

    # ── Member Properties > EndDiaphragm SubTab ────────────────────────────────────

    def _on_ed_girder_count_refreshed(self, origin_key: str, current_object: QComboBox) -> None:
        """Repopulate End Diaphragm 'Select Girders' combo with girder pairs
        (G1 to G2, G2 to G3, ...) when No. of Girders changes.

        origin_key      : KEY_TS_NO_OF_GIRDERS — reads count from working_input_dict
        current_object  : KEY_MP_ED_SELECT_GIRDERS combo to repopulate
        """
        value = self.working_input_dict.get(origin_key)
        try:
            count = int(float(str(value or 0)))
        except (ValueError, TypeError):
            count = 0

        girders = [f"G{i}" for i in range(1, count + 1)] if count > 0 else []
        if not girders:
            girders = ["G1", "G2"]

        pairs = [f"{girders[i]} to {girders[i + 1]}" for i in range(len(girders) - 1)] or ["G1 to G2"]

        current = current_object.currentText()
        current_object.clear()
        current_object.addItems(pairs)
        idx = current_object.findText(current)
        current_object.setCurrentIndex(idx if idx >= 0 else 0)

    def _on_ed_member_id_refreshed(self, origin_key: str, current_object: QLineEdit) -> None:
        """Update End Diaphragm Member ID display when Select Girders changes.

        origin_key      : KEY_MP_ED_SELECT_GIRDERS — combo holding the girder pair
        current_object  : KEY_MP_ED_MEMBER_ID read-only textbox to update

        Member ID is software-generated as E{pair_index}M1 / E{pair_index}M2,
        where pair_index = 1-based position of the selected pair in the combo
        (G1 to G2 -> 1, G2 to G3 -> 2, ...).
        """
        combo = self.findChild(QComboBox, KEY_MP_ED_SELECT_GIRDERS)
        pair_index = (combo.currentIndex() + 1) if combo is not None else 1

        text = f"E{pair_index}M1 / E{pair_index}M2"
        current_object.setText(text)

        new_pair_label = combo.currentText().strip() if combo else ""
        self._load_ed_pair(new_pair_label)

    def _save_ed_pair_connector(self, origin_key: str, target_widget: QWidget) -> None:  # END_CONNECTOR: triggers save of current pair's ED fields on any input change
        self._save_ed_pair()

    def _save_ed_pair(self) -> None:  # utility: serialises all ED widget values into working_input_dict under G{n}G{n+1}.E{n}M1 and E{n}M2 keys
        combo = self.findChild(QComboBox, KEY_MP_ED_SELECT_GIRDERS)
        if combo is None:
            return
        import re
        m = re.match(r"G(\d+) to G(\d+)", combo.currentText().strip())
        if not m:
            return
        gi, gj = int(m.group(1)), int(m.group(2))
        for mi in (1, 2):
            suffix = f".G{gi}G{gj}.E{gi}M{mi}"
            for key in self._ED_FIELD_KEYS:
                w = self.findChild(QWidget, key)
                if isinstance(w, QComboBox):
                    self.working_input_dict[key + suffix] = w.currentText()
                elif isinstance(w, QCheckBox):
                    self.working_input_dict[key + suffix] = w.isChecked()
                elif isinstance(w, QLineEdit):
                    self.working_input_dict[key + suffix] = w.text()

    def _load_ed_pair(self, pair_label: str) -> None:
        import re
        from osdagbridge.core.utils.common import (
            KEY_MP_ED_BRACING_SECTION,           KEY_MP_ED_BRACING_SECTION_DESIGNATION,
            KEY_MP_ED_TOP_CHORD_SECTION_TYPE,    KEY_MP_ED_TOP_CHORD_SECTION_DESIG,
            KEY_MP_ED_BOTTOM_CHORD_SECTION_TYPE, KEY_MP_ED_BOTTOM_CHORD_SECTION_DESIG,
        )
        m = re.match(r"G(\d+) to G(\d+)", str(pair_label or "").strip())
        if not m:
            return
        gi, gj = int(m.group(1)), int(m.group(2))
        suffix = f".G{gi}G{gj}.E{gi}M1"

        # Collect all ED widgets and block their signals to prevent cascade calls mid-load
        ed_widgets = []
        for key in self._ED_FIELD_KEYS:
            w = self.findChild(QWidget, key)
            if w is not None:
                w.blockSignals(True)
                ed_widgets.append(w)

        try:
            # Restore all saved values with signals blocked
            for key in self._ED_FIELD_KEYS:
                value = self.working_input_dict.get(key + suffix)
                if value is None:
                    continue
                w = self.findChild(QWidget, key)
                if isinstance(w, QComboBox):
                    w.setCurrentText(str(value))
                elif isinstance(w, QCheckBox):
                    w.setChecked(bool(value))
                elif isinstance(w, QLineEdit) and not w.isReadOnly():
                    w.setText(str(value))

            # Repopulate designation combos based on the now-loaded section type values,
            # then restore the saved designation (repopulation resets combo to index 0)
            _desig_pairs = [
                (KEY_MP_ED_BRACING_SECTION,        KEY_MP_ED_BRACING_SECTION_DESIGNATION),
                (KEY_MP_ED_TOP_CHORD_SECTION_TYPE,  KEY_MP_ED_TOP_CHORD_SECTION_DESIG),
                (KEY_MP_ED_BOTTOM_CHORD_SECTION_TYPE, KEY_MP_ED_BOTTOM_CHORD_SECTION_DESIG),
            ]
            for type_key, desig_key in _desig_pairs:
                type_w  = self.findChild(QComboBox, type_key)
                desig_w = self.findChild(QComboBox, desig_key)
                if type_w is None or desig_w is None:
                    continue
                self._ed_repopulate_designation_combo(desig_w, type_w.currentText())
                saved_desig = self.working_input_dict.get(desig_key + suffix)
                if saved_desig is not None:
                    desig_w.setCurrentText(str(saved_desig))
        finally:
            for w in ed_widgets:
                w.blockSignals(False)

        # All widgets fully restored — fire refresh once with complete state
        self._on_ed_bracing_layout_changed()
        self._update_ed_section_drawing()
        self._refresh_ed_section_properties()

    # Maps each End Diaphragm field/CAD to (required Type values, optional checkbox key).
    _ED_VISIBILITY_MAP = {
        # Cross Bracing — fields
        KEY_MP_ED_BRACING_TYPE:                (["Cross Bracing"], None, None),
        KEY_MP_ED_BRACING_CONNECTION:          (["Cross Bracing"], None, None),
        KEY_MP_ED_BRACING_SECTION:             (["Cross Bracing"], None, None),
        KEY_MP_ED_BRACING_SECTION_DESIGNATION: (["Cross Bracing"], None, None),
        KEY_MP_ED_TOP_CHORD:                   (["Cross Bracing"], None, None),
        KEY_MP_ED_TOP_CHORD_SECTION_TYPE:      (["Cross Bracing"], None, None),
        KEY_MP_ED_TOP_CHORD_SECTION_DESIG:     (["Cross Bracing"], None, None),
        KEY_MP_ED_BOTTOM_CHORD:                (["Cross Bracing"], None, None),
        KEY_MP_ED_BOTTOM_CHORD_SECTION_TYPE:   (["Cross Bracing"], None, None),
        KEY_MP_ED_BOTTOM_CHORD_SECTION_DESIG:  (["Cross Bracing"], None, None),

        # Rolled Beam — field
        KEY_MP_ED_IS_SECTION: (["Rolled Beam"], None, None),

        # Welded Beam — fields
        KEY_MP_ED_SYMMETRY:                (["Welded Beam"], None, None),
        KEY_MP_ED_TOTAL_DEPTH:             (["Welded Beam"], None, None),
        KEY_MP_ED_WEB_THICKNESS:           (["Welded Beam"], None, None),
        KEY_MP_ED_TOP_FLANGE_WIDTH:        (["Welded Beam"], None, None),
        KEY_MP_ED_TOP_FLANGE_THICKNESS:    (["Welded Beam"], None, None),
        KEY_MP_ED_BOTTOM_FLANGE_WIDTH:     (["Welded Beam"], None, None),
        KEY_MP_ED_BOTTOM_FLANGE_THICKNESS: (["Welded Beam"], None, None),

        # CAD previews — whole section, hidden via section id
        KEY_MP_ED_BRACING_LAYOUT_CAD:      (["Cross Bracing"], None, KEY_MP_ED_BRACING_LAYOUT_SECTION),
        KEY_MP_ED_BRACING_SECTION_PREVIEW: (["Cross Bracing"], None, KEY_MP_ED_BRACING_PREVIEW_SECTION),
        KEY_MP_ED_TOP_CHORD_PREVIEW:       (["Cross Bracing"], KEY_MP_ED_TOP_CHORD, KEY_MP_ED_TOP_CHORD_PREVIEW_SECTION),
        KEY_MP_ED_BOTTOM_CHORD_PREVIEW:    (["Cross Bracing"], KEY_MP_ED_BOTTOM_CHORD, KEY_MP_ED_BOTTOM_CHORD_PREVIEW_SECTION),
        KEY_MP_ED_ROLLED_PREVIEW:          (["Rolled Beam"], None, KEY_MP_ED_ROLLED_PREVIEW_SECTION),
        KEY_MP_ED_WELDED_PREVIEW:          (["Welded Beam"], None, KEY_MP_ED_WELDED_PREVIEW_SECTION),

        # Section Properties — whole section, hidden via section id (one representative field; all 10 share the card)
        KEY_MP_ED_MASS: (["Rolled Beam", "Welded Beam"], None, KEY_MP_ED_SECTION_PROPERTIES_SECTION),
    }

    def _apply_ed_visibility(self) -> None:
        """Apply _ED_VISIBILITY_MAP against the current Type + chord checkbox
        state. Re-run wholesale on every change — idempotent, no per-trigger
        bookkeeping needed."""
        type_combo = self.findChild(QComboBox, KEY_MP_ED_TYPE)
        current_type = type_combo.currentText() if type_combo else None

        for target_key, (required_types, checkbox_key, section_id) in self._ED_VISIBILITY_MAP.items():
            visible = current_type in required_types

            if visible and checkbox_key is not None:
                cb = self.findChild(QCheckBox, checkbox_key)
                visible = bool(cb and cb.isChecked())

            if section_id is not None:
                wrapper = self.findChild(QWidget, section_id)
                if wrapper:
                    wrapper.setVisible(visible)
            else:
                w = self.findChild(QWidget, target_key)
                lbl = self.findChild(QLabel, target_key + "_label")
                if w:   w.setVisible(visible)
                if lbl: lbl.setVisible(visible)

    def _on_end_diaphragm_type_changed(self, type_str: str) -> None:  # on_change: shows Cross Bracing / Rolled Beam / Welded Beam fields + CAD previews + Section Properties based on Type
        self._apply_ed_visibility()
        self._update_ed_section_drawing()
        self._on_ed_bracing_layout_changed()
        self._refresh_ed_section_properties()

    def _refresh_ed_section_properties(self) -> None:
        from osdagbridge.core.utils.common import KEY_MP_ED_TYPE
        type_w  = self.findChild(QComboBox, KEY_MP_ED_TYPE)
        ed_type = type_w.currentText() if type_w else ""
        if ed_type == "Rolled Beam":
            result = self._compute_ed_rolled_section_properties(self.working_input_dict)
        elif ed_type == "Welded Beam":
            result = self._compute_ed_welded_section_properties(self.working_input_dict)
        else:
            return
        if not isinstance(result, dict):
            return
        for widget_id, value in result.items():
            w = self.findChild(QLineEdit, widget_id)
            if w:
                w.setText(str(value) if value is not None else "")

    def _on_ed_bracing_layout_changed(self, _value=None) -> None:  # on_change: syncs bracing layout CAD + K-Bracing disables bottom chord + enables/disables chord sub-fields
        bracing_combo = self.findChild(QComboBox, KEY_MP_ED_BRACING_TYPE)
        bracing_type  = bracing_combo.currentText() if bracing_combo else "K-Bracing"
        is_k_bracing  = (bracing_type == "K-Bracing")

        top_cb    = self.findChild(QCheckBox, KEY_MP_ED_TOP_CHORD)
        bottom_cb = self.findChild(QCheckBox, KEY_MP_ED_BOTTOM_CHORD)
        bottom_lbl = self.findChild(QLabel, KEY_MP_ED_BOTTOM_CHORD + "_label")

        # K-Bracing: disable + uncheck bottom chord and gray its label
        if is_k_bracing:
            if bottom_cb:
                bottom_cb.blockSignals(True)
                bottom_cb.setChecked(True)
                bottom_cb.setEnabled(False)
                bottom_cb.blockSignals(False)
            if bottom_lbl:
                bottom_lbl.setStyleSheet("font-size: 11px; color: #aaaaaa;")
        else:
            if bottom_cb:
                bottom_cb.setEnabled(True)
            if bottom_lbl:
                bottom_lbl.setStyleSheet("font-size: 11px; color: #000;")

        top_checked          = bool(top_cb    and top_cb.isChecked())
        bottom_checked       = bool(bottom_cb and bottom_cb.isChecked())
        bottom_props_enabled = bottom_checked

        is_custom = str(self.working_input_dict.get(KEY_DESIGN_MODE, "Optimized")).strip() == "Custom"
        for key in (KEY_MP_ED_TOP_CHORD_SECTION_TYPE, KEY_MP_ED_TOP_CHORD_SECTION_DESIG):
            w = self.findChild(QWidget, key)
            if w:
                w.setEnabled(is_custom and top_checked)

        for key in (KEY_MP_ED_BOTTOM_CHORD_SECTION_TYPE, KEY_MP_ED_BOTTOM_CHORD_SECTION_DESIG):
            w = self.findChild(QWidget, key)
            if w:
                w.setEnabled(is_custom and bottom_props_enabled)

        cad = self.findChild(QWidget, KEY_MP_ED_BRACING_LAYOUT_CAD)
        if cad and hasattr(cad, "set_layout"):
            member_id_w = self.findChild(QLineEdit, KEY_MP_ED_MEMBER_ID)
            pair_combo  = self.findChild(QComboBox, KEY_MP_ED_SELECT_GIRDERS)
            cad.set_layout(
                bracing_type=bracing_type,
                top_chord=top_checked,
                bottom_chord=bottom_checked,
                member_label=member_id_w.text() if member_id_w else "",
                girder_pair=pair_combo.currentText() if pair_combo else "",
            )

        self._apply_ed_visibility()
        self._refresh_ed_bracing_previews()

    def _refresh_ed_bracing_previews(self) -> None:
        from osdagbridge.core.utils.common import (
            KEY_MP_ED_BRACING_SECTION, KEY_MP_ED_BRACING_SECTION_DESIGNATION, KEY_MP_ED_BRACING_SECTION_PREVIEW,
            KEY_MP_ED_TOP_CHORD_SECTION_TYPE, KEY_MP_ED_TOP_CHORD_SECTION_DESIG, KEY_MP_ED_TOP_CHORD_PREVIEW,
            KEY_MP_ED_BOTTOM_CHORD_SECTION_TYPE, KEY_MP_ED_BOTTOM_CHORD_SECTION_DESIG, KEY_MP_ED_BOTTOM_CHORD_PREVIEW,
        )
        for type_key, desig_key, preview_key in [
            (KEY_MP_ED_BRACING_SECTION,        KEY_MP_ED_BRACING_SECTION_DESIGNATION, KEY_MP_ED_BRACING_SECTION_PREVIEW),
            (KEY_MP_ED_TOP_CHORD_SECTION_TYPE,  KEY_MP_ED_TOP_CHORD_SECTION_DESIG,    KEY_MP_ED_TOP_CHORD_PREVIEW),
            (KEY_MP_ED_BOTTOM_CHORD_SECTION_TYPE, KEY_MP_ED_BOTTOM_CHORD_SECTION_DESIG, KEY_MP_ED_BOTTOM_CHORD_PREVIEW),
        ]:
            type_w  = self.findChild(QComboBox, type_key)
            desig_w = self.findChild(QComboBox, desig_key)
            if type_w and desig_w:
                self._ed_update_preview(type_w.currentText(), desig_w.currentText(), preview_key)

    _ED_SECTION_TYPE_MAP = {
        "Angle":                    "angle",
        "Double Angle (Long Leg)":  "double_angle_long",
        "Double Angle (Short Leg)": "double_angle_short",
        "Channel":                  "channel",
        "Double Channel":           "double_channel",
    }

    def _ed_update_preview(self, type_label: str, designation: str, preview_key: str) -> None:
        from osdagbridge.desktop.ui.widgets.placeholder_section_preview import PlaceholderSectionPreviewWidget
        widget = self.findChild(PlaceholderSectionPreviewWidget, preview_key)
        if widget is None:
            return
        stype = self._ED_SECTION_TYPE_MAP.get(type_label, "angle")
        show_double_total = stype not in ("double_angle_long", "double_angle_short")
        widget.set_section(stype, designation, show_double_total)

    def _on_ed_bracing_preview_changed(self, designation: str) -> None:
        from osdagbridge.core.utils.common import KEY_MP_ED_BRACING_SECTION, KEY_MP_ED_BRACING_SECTION_PREVIEW
        type_w = self.findChild(QComboBox, KEY_MP_ED_BRACING_SECTION)
        self._ed_update_preview(type_w.currentText() if type_w else "Angle", designation, KEY_MP_ED_BRACING_SECTION_PREVIEW)

    def _on_ed_top_chord_preview_changed(self, designation: str) -> None:
        from osdagbridge.core.utils.common import KEY_MP_ED_TOP_CHORD_SECTION_TYPE, KEY_MP_ED_TOP_CHORD_PREVIEW
        type_w = self.findChild(QComboBox, KEY_MP_ED_TOP_CHORD_SECTION_TYPE)
        self._ed_update_preview(type_w.currentText() if type_w else "Angle", designation, KEY_MP_ED_TOP_CHORD_PREVIEW)

    def _on_ed_bottom_chord_preview_changed(self, designation: str) -> None:
        from osdagbridge.core.utils.common import KEY_MP_ED_BOTTOM_CHORD_SECTION_TYPE, KEY_MP_ED_BOTTOM_CHORD_PREVIEW
        type_w = self.findChild(QComboBox, KEY_MP_ED_BOTTOM_CHORD_SECTION_TYPE)
        self._ed_update_preview(type_w.currentText() if type_w else "Angle", designation, KEY_MP_ED_BOTTOM_CHORD_PREVIEW)

    def _ed_repopulate_designation_combo(self, desig_w: QComboBox, type_label: str) -> None:
        """Repopulate a designation combo with angle or channel designations based on section type."""
        from osdagbridge.core.utils.common import get_angle_designation_list, get_channel_section_list
        stype = self._ED_SECTION_TYPE_MAP.get(type_label, "angle")
        items = get_channel_section_list() if stype in ("channel", "double_channel") else get_angle_designation_list()
        prev = desig_w.blockSignals(True)
        try:
            desig_w.clear()
            desig_w.addItems(items)
            if items:
                desig_w.setCurrentIndex(0)
        finally:
            desig_w.blockSignals(prev)

    def _on_ed_bracing_section_type_changed(self, type_label: str) -> None:
        from osdagbridge.core.utils.common import KEY_MP_ED_BRACING_SECTION_DESIGNATION, KEY_MP_ED_BRACING_SECTION_PREVIEW
        desig_w = self.findChild(QComboBox, KEY_MP_ED_BRACING_SECTION_DESIGNATION)
        if desig_w is not None:
            self._ed_repopulate_designation_combo(desig_w, type_label)
        self._ed_update_preview(type_label, desig_w.currentText() if desig_w else "", KEY_MP_ED_BRACING_SECTION_PREVIEW)

    def _on_ed_top_chord_section_type_changed(self, type_label: str) -> None:
        from osdagbridge.core.utils.common import KEY_MP_ED_TOP_CHORD_SECTION_DESIG, KEY_MP_ED_TOP_CHORD_PREVIEW
        desig_w = self.findChild(QComboBox, KEY_MP_ED_TOP_CHORD_SECTION_DESIG)
        if desig_w is not None:
            self._ed_repopulate_designation_combo(desig_w, type_label)
        self._ed_update_preview(type_label, desig_w.currentText() if desig_w else "", KEY_MP_ED_TOP_CHORD_PREVIEW)

    def _on_ed_bottom_chord_section_type_changed(self, type_label: str) -> None:
        from osdagbridge.core.utils.common import KEY_MP_ED_BOTTOM_CHORD_SECTION_DESIG, KEY_MP_ED_BOTTOM_CHORD_PREVIEW
        desig_w = self.findChild(QComboBox, KEY_MP_ED_BOTTOM_CHORD_SECTION_DESIG)
        if desig_w is not None:
            self._ed_repopulate_designation_combo(desig_w, type_label)
        self._ed_update_preview(type_label, desig_w.currentText() if desig_w else "", KEY_MP_ED_BOTTOM_CHORD_PREVIEW)

    def _update_ed_section_drawing(self, *args) -> None:  # on_change/on_editing_finished: updates rolled or welded ED section CAD preview from live widget values
        from osdagbridge.desktop.ui.dialogs.additional_input.drawings.rolled_section_preview import RolledSectionPreview
        from osdagbridge.core.utils.common import (
            KEY_MP_ED_TYPE,
            KEY_MP_ED_IS_SECTION,
            KEY_MP_ED_TOTAL_DEPTH, KEY_MP_ED_WEB_THICKNESS,
            KEY_MP_ED_TOP_FLANGE_WIDTH, KEY_MP_ED_TOP_FLANGE_THICKNESS,
            KEY_MP_ED_BOTTOM_FLANGE_WIDTH, KEY_MP_ED_BOTTOM_FLANGE_THICKNESS,
            KEY_MP_ED_ROLLED_PREVIEW, KEY_MP_ED_WELDED_PREVIEW,
        )

        ed_type_w = self.findChild(QComboBox, KEY_MP_ED_TYPE)
        ed_type   = ed_type_w.currentText() if ed_type_w else "Rolled Beam"

        if ed_type == "Rolled Beam":
            widget = self.findChild(RolledSectionPreview, KEY_MP_ED_ROLLED_PREVIEW)
            if widget is None:
                return
            is_w = self.findChild(QComboBox, KEY_MP_ED_IS_SECTION)
            designation = is_w.currentText() if is_w else self.working_input_dict.get(KEY_MP_ED_IS_SECTION, "")
            if not designation:
                widget.clear()
                return
            from osdagbridge.core.utils.common import GirderSectionCatalog
            catalog = GirderSectionCatalog()
            beam    = catalog.get_beam_profile(str(designation).strip())
            if beam:
                widget.set_section(beam)
                widget._caption = f"Rolled Section • {designation}"
                widget.update()
            else:
                outline = catalog.get_rolled_section(str(designation).strip())
                if outline:
                    widget.set_dimensions(
                        depth_mm=outline["depth_mm"],
                        flange_width_mm=outline["top_flange_width_mm"],
                        bottom_flange_width_mm=outline["bottom_flange_width_mm"],
                        web_thickness_mm=outline["web_thickness_mm"],
                        flange_thickness_mm=outline["top_flange_thickness_mm"],
                        bottom_flange_thickness_mm=outline["bottom_flange_thickness_mm"],
                    )
                    widget._caption = f"Rolled Section • {designation}"
                    widget.update()
                else:
                    widget.clear()

        else:  # Welded Beam
            widget = self.findChild(RolledSectionPreview, KEY_MP_ED_WELDED_PREVIEW)
            if widget is None:
                return

            def _get(key):
                w = self.findChild(QWidget, key)
                if isinstance(w, QComboBox): return w.currentText()
                if isinstance(w, QLineEdit): return w.text().strip()
                return self.working_input_dict.get(key, "")

            def _f(v, default=0.0):
                try:   return float(v) if v else default
                except (ValueError, TypeError): return default

            depth = _f(_get(KEY_MP_ED_TOTAL_DEPTH))
            top_w = _f(_get(KEY_MP_ED_TOP_FLANGE_WIDTH))
            if not depth or not top_w:
                widget.clear()
                return

            bot_w = _f(_get(KEY_MP_ED_BOTTOM_FLANGE_WIDTH)) or top_w
            web_t = _f(_get(KEY_MP_ED_WEB_THICKNESS))
            top_t = _f(_get(KEY_MP_ED_TOP_FLANGE_THICKNESS))
            bot_t = _f(_get(KEY_MP_ED_BOTTOM_FLANGE_THICKNESS)) or top_t

            widget.set_dimensions(
                depth_mm=depth,
                flange_width_mm=top_w,
                bottom_flange_width_mm=bot_w,
                web_thickness_mm=web_t or max(8.0, depth * 0.02),
                flange_thickness_mm=top_t or max(10.0, depth * 0.03),
                bottom_flange_thickness_mm=bot_t or max(10.0, depth * 0.03),
                show_welds=True,
            )
            widget._caption = "Welded section preview"
            widget.update()

    def _compute_ed_rolled_section_properties(self, working_input_dict: dict) -> dict:  # compute: looks up rolled I-section properties from catalog by designation
        from osdagbridge.core.utils.common import (
            GirderSectionCatalog, KEY_MP_ED_IS_SECTION,
            KEY_MP_ED_MASS, KEY_MP_ED_SECTIONAL_AREA,
            KEY_MP_ED_SECTIONAL_IZ, KEY_MP_ED_SECTIONAL_IY,
            KEY_MP_ED_RADIUS_GYRATION_Z, KEY_MP_ED_RADIUS_GYRATION_Y,
            KEY_MP_ED_ELASTIC_MODULUS_ZZ, KEY_MP_ED_ELASTIC_MODULUS_ZY,
            KEY_MP_ED_PLASTIC_MODULUS_ZUZ, KEY_MP_ED_PLASTIC_MODULUS_ZUY,
        )
        designation = working_input_dict.get(KEY_MP_ED_IS_SECTION, "")
        if not designation:
            return {}
        section = GirderSectionCatalog().get_beam_profile(str(designation).strip())
        if section is None:
            return {}
        return {
            KEY_MP_ED_MASS:                str(section.mass_per_meter_kg),
            KEY_MP_ED_SECTIONAL_AREA:      str(section.area_cm2),
            KEY_MP_ED_SECTIONAL_IZ:        str(section.moment_of_inertia_zz_cm4),
            KEY_MP_ED_SECTIONAL_IY:        str(section.moment_of_inertia_yy_cm4),
            KEY_MP_ED_RADIUS_GYRATION_Z:   str(section.radius_of_gyration_z_cm),
            KEY_MP_ED_RADIUS_GYRATION_Y:   str(section.radius_of_gyration_y_cm),
            KEY_MP_ED_ELASTIC_MODULUS_ZZ:  str(section.elastic_section_modulus_z_cm3),
            KEY_MP_ED_ELASTIC_MODULUS_ZY:  str(section.elastic_section_modulus_y_cm3),
            KEY_MP_ED_PLASTIC_MODULUS_ZUZ: str(section.plastic_section_modulus_z_cm3),
            KEY_MP_ED_PLASTIC_MODULUS_ZUY: str(section.plastic_section_modulus_y_cm3),
        }

    def _compute_ed_welded_section_properties(self, working_input_dict: dict) -> dict:  # compute: derives welded I-section properties for end diaphragm from flange/web dimensions
        from osdagbridge.core.bridge_types.plate_girder.initial_sizing import BridgeConfigurationSolver
        from osdagbridge.core.utils.common import (
            KEY_SPAN, KEY_MP_ED_SYMMETRY,
            KEY_MP_ED_TOTAL_DEPTH, KEY_MP_ED_WEB_THICKNESS,
            KEY_MP_ED_TOP_FLANGE_WIDTH, KEY_MP_ED_TOP_FLANGE_THICKNESS,
            KEY_MP_ED_BOTTOM_FLANGE_WIDTH, KEY_MP_ED_BOTTOM_FLANGE_THICKNESS,
            KEY_MP_ED_MASS, KEY_MP_ED_SECTIONAL_AREA,
            KEY_MP_ED_SECTIONAL_IZ, KEY_MP_ED_SECTIONAL_IY,
            KEY_MP_ED_RADIUS_GYRATION_Z, KEY_MP_ED_RADIUS_GYRATION_Y,
            KEY_MP_ED_ELASTIC_MODULUS_ZZ, KEY_MP_ED_ELASTIC_MODULUS_ZY,
            KEY_MP_ED_PLASTIC_MODULUS_ZUZ, KEY_MP_ED_PLASTIC_MODULUS_ZUY,
        )

        def _to_m(key: str) -> float:
            val = working_input_dict.get(key)
            if val is None or isinstance(val, (dict, list)):
                return 0.0
            try:   return float(val) / 1000.0
            except (ValueError, TypeError): return 0.0

        depth_m  = _to_m(KEY_MP_ED_TOTAL_DEPTH)
        b_top_m  = _to_m(KEY_MP_ED_TOP_FLANGE_WIDTH)
        b_bot_m  = _to_m(KEY_MP_ED_BOTTOM_FLANGE_WIDTH)
        tf_top_m = _to_m(KEY_MP_ED_TOP_FLANGE_THICKNESS)
        tf_bot_m = _to_m(KEY_MP_ED_BOTTOM_FLANGE_THICKNESS)
        tw_m     = _to_m(KEY_MP_ED_WEB_THICKNESS)

        if not depth_m or not b_top_m:
            return {}

        span_m = float(working_input_dict.get(KEY_SPAN))
        symmetry = str(working_input_dict.get(KEY_MP_ED_SYMMETRY) or "Girder Symmetric")

        result = BridgeConfigurationSolver(carriageway_width=1.0).compute_section_properties(
            span=span_m, symmetry=symmetry,
            user_depth=depth_m, B_top=b_top_m, B_bot=b_bot_m,
            t_f_top=tf_top_m, t_f_bot=tf_bot_m, t_w=tw_m,
        )

        return {
            KEY_MP_ED_MASS:                f"{result['Mass']:.4f}",
            KEY_MP_ED_SECTIONAL_AREA:      f"{result['Area']  * 1e4:.4f}",
            KEY_MP_ED_SECTIONAL_IZ:        f"{result['I_z']   * 1e8:.4f}",
            KEY_MP_ED_SECTIONAL_IY:        f"{result['I_y']   * 1e8:.4f}",
            KEY_MP_ED_RADIUS_GYRATION_Z:   f"{result['r_z']   * 1e2:.4f}",
            KEY_MP_ED_RADIUS_GYRATION_Y:   f"{result['r_y']   * 1e2:.4f}",
            KEY_MP_ED_ELASTIC_MODULUS_ZZ:  f"{result['Z_ez']  * 1e6:.4f}",
            KEY_MP_ED_ELASTIC_MODULUS_ZY:  f"{result['Z_ey']  * 1e6:.4f}",
            KEY_MP_ED_PLASTIC_MODULUS_ZUZ: f"{result['Z_pz']  * 1e6:.4f}",
            KEY_MP_ED_PLASTIC_MODULUS_ZUY: f"{result['Z_py']  * 1e6:.4f}",
        }

    # Keys saved/restored per girder-pair (G{n}G{n+1}.E1M1/M2). TYPE first so its on_change fires before sub-fields are set.
    _ED_FIELD_KEYS = [
        KEY_MP_ED_TYPE,
        KEY_MP_ED_BRACING_TYPE,              KEY_MP_ED_BRACING_CONNECTION,
        KEY_MP_ED_TOP_CHORD,                 KEY_MP_ED_BOTTOM_CHORD,
        KEY_MP_ED_BRACING_SECTION,           KEY_MP_ED_BRACING_SECTION_DESIGNATION,
        KEY_MP_ED_TOP_CHORD_SECTION_TYPE,    KEY_MP_ED_TOP_CHORD_SECTION_DESIG,
        KEY_MP_ED_BOTTOM_CHORD_SECTION_TYPE, KEY_MP_ED_BOTTOM_CHORD_SECTION_DESIG,
        KEY_MP_ED_IS_SECTION,
        KEY_MP_ED_SYMMETRY,
        KEY_MP_ED_TOTAL_DEPTH,               KEY_MP_ED_WEB_THICKNESS,
        KEY_MP_ED_TOP_FLANGE_WIDTH,          KEY_MP_ED_TOP_FLANGE_THICKNESS,
        KEY_MP_ED_BOTTOM_FLANGE_WIDTH,       KEY_MP_ED_BOTTOM_FLANGE_THICKNESS,
    ]

    # Keys saved/restored per girder-pair (G{n}G{n+1}) for Cross Bracing.
    # KEY_MP_CB_NO_OF_CROSS_BRACINGS is stored at pair-level (.G1G2, .G2G3) — handled separately.
    _CB_FIELD_KEYS = [
        KEY_MP_CB_TYPE,              KEY_MP_CB_BRACING_CONNECTION,
        KEY_MP_CB_TOP_CHORD,         KEY_MP_CB_BOTTOM_CHORD,
        KEY_MP_CB_BRACING_SECTION_TYPE,      KEY_MP_CB_BRACING_SECTION_DESIGNATION,
        KEY_MP_CB_TOP_CHORD_SECTION_TYPE,    KEY_MP_CB_TOP_CHORD_SECTION_DESIG,
        KEY_MP_CB_BOTTOM_CHORD_SECTION_TYPE, KEY_MP_CB_BOTTOM_CHORD_SECTION_DESIG,
    ]

    # ── Member Properties > Cross Bracing SubTab ──────────────────────────────────

    def _on_cb_spacing_computed(self, origin_key: str, target_widget: QLineEdit) -> None:
        if target_widget is None:
            return
        no_bracings_w = self.findChild(QLineEdit, KEY_MP_CB_NO_OF_CROSS_BRACINGS)
        count = int(float(no_bracings_w.text() or "1")) if no_bracings_w else 1

        span = float(self.working_input_dict.get(KEY_SPAN))
        if span > 0:
            target_widget.setText(f"{span / (count + 1):.3f}")
        else:
            target_widget.setText("")

        if count > 0:
            girder_count = int(float(str(self.working_input_dict.get(KEY_TS_NO_OF_GIRDERS) or 1)))
            # Write count at pair-level for every pair — same value for all
            for gi in range(1, girder_count):
                pair_key = f"{KEY_MP_CB_NO_OF_CROSS_BRACINGS}.G{gi}G{gi + 1}"
                self.working_input_dict[pair_key] = count
            from osdagbridge.core.bridge_types.plate_girder.defaults import extend_cb_dynamic_keys
            extend_cb_dynamic_keys(self.working_input_dict, girder_count, count)

    def _on_cb_girder_count_refreshed(self, origin_key: str, current_object: QComboBox) -> None:
        if current_object is None:
            return
        value = self.working_input_dict.get(origin_key)
        try:
            count = int(float(str(value or 0)))
        except (ValueError, TypeError):
            count = 0
        girders = [f"G{i}" for i in range(1, count + 1)] if count > 0 else ["G1", "G2"]
        pairs = [f"{girders[i]} to {girders[i + 1]}" for i in range(len(girders) - 1)] or ["G1 to G2"]
        current = current_object.currentText()
        current_object.clear()
        current_object.addItems(pairs)
        idx = current_object.findText(current)
        current_object.setCurrentIndex(idx if idx >= 0 else 0)

    def _on_cb_member_id_refreshed(self, origin_key: str, target_widget: QLineEdit) -> None:
        if target_widget is None:
            return
        import re
        girder_combo   = self.findChild(QComboBox,  KEY_MP_CB_SELECT_GIRDERS)
        no_bracings_w  = self.findChild(QLineEdit,   KEY_MP_CB_NO_OF_CROSS_BRACINGS)
        pair_text = girder_combo.currentText().strip() if girder_combo else "G1 to G2"
        m = re.match(r"G(\d+) to G(\d+)", pair_text)
        pair_index = int(m.group(1)) if m else 1
        try:
            count = int(float(no_bracings_w.text() or "0")) if no_bracings_w else 0
        except (ValueError, TypeError):
            count = 0
        member_id = f"B{pair_index}M1" if count <= 1 else f"B{pair_index}M1 to B{pair_index}M{count}"
        target_widget.setText(member_id)

        if origin_key == KEY_MP_CB_SELECT_GIRDERS:
            self._load_cb_pair(pair_text)
        else:
            self._update_cb_layout_cad(member_id, pair_text)

    def _save_cb_pair_connector(self, origin_key: str, target_widget: QWidget) -> None:  # END_CONNECTOR: triggers save of current pair's CB fields on any input change
        self._save_cb_pair()

    def _save_cb_pair(self) -> None:  # utility: serialises all CB widget values into working_input_dict under G{n}G{n+1}.B{n}Mk per-member keys
        combo = self.findChild(QComboBox, KEY_MP_CB_SELECT_GIRDERS)
        if combo is None:
            return
        import re
        m = re.match(r"G(\d+) to G(\d+)", combo.currentText().strip())
        if not m:
            return
        gi, gj = int(m.group(1)), int(m.group(2))
        g_pair = f"G{gi}G{gj}"

        no_bracings_w = self.findChild(QLineEdit, KEY_MP_CB_NO_OF_CROSS_BRACINGS)
        try:
            count = max(1, int(float(no_bracings_w.text() or "1"))) if no_bracings_w else 1
        except (ValueError, TypeError):
            count = 1

        values = {}
        for key in self._CB_FIELD_KEYS:
            w = self.findChild(QWidget, key)
            if isinstance(w, QComboBox):
                values[key] = w.currentText()
            elif isinstance(w, QCheckBox):
                values[key] = w.isChecked()
            elif isinstance(w, QLineEdit):
                values[key] = w.text()

        for mk in range(1, count + 1):
            suffix = f".{g_pair}.B{gi}M{mk}"
            for key, value in values.items():
                self.working_input_dict[key + suffix] = value

    def _load_cb_pair(self, pair_label: str) -> None:  # utility: restores CB widgets from first member's (B{n}M1) per-member keys, then refreshes CAD
        import re
        m = re.match(r"G(\d+) to G(\d+)", str(pair_label or "").strip())
        if not m:
            return
        gi, gj = int(m.group(1)), int(m.group(2))
        # Load from the first member as representative — all members share the same values
        suffix = f".G{gi}G{gj}.B{gi}M1"

        cb_widgets = []
        for key in self._CB_FIELD_KEYS:
            w = self.findChild(QWidget, key)
            if w is not None:
                w.blockSignals(True)
                cb_widgets.append(w)

        try:
            for key in self._CB_FIELD_KEYS:
                value = self.working_input_dict.get(key + suffix)
                if value is None:
                    continue
                w = self.findChild(QWidget, key)
                if isinstance(w, QComboBox):
                    w.setCurrentText(str(value))
                elif isinstance(w, QCheckBox):
                    w.setChecked(bool(value))
                elif isinstance(w, QLineEdit) and not w.isReadOnly():
                    w.setText(str(value))

            _desig_pairs = [
                (KEY_MP_CB_BRACING_SECTION_TYPE,      KEY_MP_CB_BRACING_SECTION_DESIGNATION),
                (KEY_MP_CB_TOP_CHORD_SECTION_TYPE,    KEY_MP_CB_TOP_CHORD_SECTION_DESIG),
                (KEY_MP_CB_BOTTOM_CHORD_SECTION_TYPE, KEY_MP_CB_BOTTOM_CHORD_SECTION_DESIG),
            ]
            for type_key, desig_key in _desig_pairs:
                type_w  = self.findChild(QComboBox, type_key)
                desig_w = self.findChild(QComboBox, desig_key)
                if type_w is None or desig_w is None:
                    continue
                self._cb_repopulate_designation(desig_w, type_w.currentText())
                saved_desig = self.working_input_dict.get(desig_key + suffix)
                if saved_desig is not None:
                    desig_w.setCurrentText(str(saved_desig))
        finally:
            for w in cb_widgets:
                w.blockSignals(False)

        self._on_cb_bracing_layout_changed("", None)
        self._refresh_cb_section_previews()

    def _update_cb_layout_cad(self, member_label: str, girder_pair: str) -> None:
        cad_w = self.findChild(QWidget, "member_properties.cross_bracing_details.layout_cad")
        if cad_w is None or not hasattr(cad_w, "set_layout"):
            return
        bracing_combo = self.findChild(QComboBox, KEY_MP_CB_TYPE)
        top_cb        = self.findChild(QCheckBox, KEY_MP_CB_TOP_CHORD)
        bottom_cb     = self.findChild(QCheckBox, KEY_MP_CB_BOTTOM_CHORD)
        cad_w.set_layout(
            bracing_type = bracing_combo.currentText() if bracing_combo else "K-Bracing",
            top_chord    = top_cb.isChecked()    if top_cb    else False,
            bottom_chord = bottom_cb.isChecked() if bottom_cb else True,
            member_label = member_label,
            girder_pair  = girder_pair,
        )

    def _on_cb_bracing_layout_changed(self, origin_key: str, _target_widget) -> None:
        bracing_combo = self.findChild(QComboBox, KEY_MP_CB_TYPE)
        bracing_type  = bracing_combo.currentText() if bracing_combo else "K-Bracing"
        is_k_bracing  = (bracing_type == "K-Bracing")

        top_cb     = self.findChild(QCheckBox, KEY_MP_CB_TOP_CHORD)
        bottom_cb  = self.findChild(QCheckBox, KEY_MP_CB_BOTTOM_CHORD)
        bottom_lbl = self.findChild(QLabel,    KEY_MP_CB_BOTTOM_CHORD + "_label")

        # K-Bracing: force bottom chord checked and disable it
        if is_k_bracing:
            if bottom_cb:
                bottom_cb.blockSignals(True)
                bottom_cb.setChecked(True)
                bottom_cb.setEnabled(False)
                bottom_cb.blockSignals(False)
            if bottom_lbl:
                bottom_lbl.setStyleSheet("font-size: 11px; color: #aaaaaa;")
        else:
            if bottom_cb:
                bottom_cb.setEnabled(True)
            if bottom_lbl:
                bottom_lbl.setStyleSheet("font-size: 11px; color: #000;")

        top_checked    = bool(top_cb    and top_cb.isChecked())
        bottom_checked = bool(bottom_cb and bottom_cb.isChecked())
        is_custom      = str(self.working_input_dict.get(KEY_DESIGN_MODE, "Optimized")).strip() == "Custom"

        # Enable/disable Bracing section type & designation
        for key in (KEY_MP_CB_BRACING_SECTION_TYPE, KEY_MP_CB_BRACING_SECTION_DESIGNATION):
            w = self.findChild(QWidget, key)
            if w:
                w.setEnabled(is_custom)

        # Enable/disable Top Chord section type & designation
        for key in (KEY_MP_CB_TOP_CHORD_SECTION_TYPE, KEY_MP_CB_TOP_CHORD_SECTION_DESIG):
            w = self.findChild(QWidget, key)
            if w:
                w.setEnabled(is_custom and top_checked)

        # Enable/disable Bottom Chord section type & designation
        for key in (KEY_MP_CB_BOTTOM_CHORD_SECTION_TYPE, KEY_MP_CB_BOTTOM_CHORD_SECTION_DESIG):
            w = self.findChild(QWidget, key)
            if w:
                w.setEnabled(is_custom and bottom_checked)

        # Show/hide Top Chord CAD section card
        top_section = self.findChild(QWidget, KEY_MP_CB_TOP_CHORD_PREVIEW_SECTION)
        if top_section:
            top_section.setVisible(top_checked)

        # Show/hide Bottom Chord CAD section card
        bottom_section = self.findChild(QWidget, KEY_MP_CB_BOTTOM_CHORD_PREVIEW_SECTION)
        if bottom_section:
            bottom_section.setVisible(bottom_checked)

        # Sync layout CAD diagram
        member_id_w  = self.findChild(QLineEdit, KEY_MP_CB_MEMBER_ID)
        girder_combo = self.findChild(QComboBox, KEY_MP_CB_SELECT_GIRDERS)
        self._update_cb_layout_cad(
            member_label = member_id_w.text()         if member_id_w  else "",
            girder_pair  = girder_combo.currentText() if girder_combo else "",
        )

        # Sync section preview CADs
        self._refresh_cb_section_previews()

    _CB_SECTION_TYPE_MAP = {
        "Angle":                    "angle",
        "Double Angle (Long Leg)":  "double_angle_long",
        "Double Angle (Short Leg)": "double_angle_short",
        "Channel":                  "channel",
        "Double Channel":           "double_channel",
    }

    def _cb_update_preview(self, type_label: str, designation: str, preview_key: str) -> None:
        from osdagbridge.desktop.ui.widgets.placeholder_section_preview import PlaceholderSectionPreviewWidget
        widget = self.findChild(PlaceholderSectionPreviewWidget, preview_key)
        if widget is None:
            return
        stype = self._CB_SECTION_TYPE_MAP.get(type_label, "angle")
        show_double_total = stype not in ("double_angle_long", "double_angle_short")
        widget.set_section(stype, designation, show_double_total)

    def _refresh_cb_section_previews(self) -> None:
        for type_key, desig_key, preview_key in [
            (KEY_MP_CB_BRACING_SECTION_TYPE,      KEY_MP_CB_BRACING_SECTION_DESIGNATION, KEY_MP_CB_BRACING_PREVIEW),
            (KEY_MP_CB_TOP_CHORD_SECTION_TYPE,     KEY_MP_CB_TOP_CHORD_SECTION_DESIG,    KEY_MP_CB_TOP_CHORD_PREVIEW),
            (KEY_MP_CB_BOTTOM_CHORD_SECTION_TYPE,  KEY_MP_CB_BOTTOM_CHORD_SECTION_DESIG, KEY_MP_CB_BOTTOM_CHORD_PREVIEW),
        ]:
            type_w  = self.findChild(QComboBox, type_key)
            desig_w = self.findChild(QComboBox, desig_key)
            if type_w and desig_w:
                self._cb_update_preview(type_w.currentText(), desig_w.currentText(), preview_key)

    def _cb_repopulate_designation(self, desig_w: QComboBox, type_label: str) -> None:
        from osdagbridge.core.utils.common import get_angle_designation_list, get_channel_section_list
        stype = self._CB_SECTION_TYPE_MAP.get(type_label, "angle")
        items = get_channel_section_list() if stype in ("channel", "double_channel") else get_angle_designation_list()
        prev = desig_w.blockSignals(True)
        try:
            desig_w.clear()
            desig_w.addItems(items)
            if items:
                desig_w.setCurrentIndex(0)
        finally:
            desig_w.blockSignals(prev)

    def _on_cb_bracing_section_type_changed(self, origin_key: str, target_widget: QComboBox) -> None:
        type_w = self.findChild(QComboBox, origin_key)
        type_label = type_w.currentText() if type_w else "Angle"
        if target_widget:
            self._cb_repopulate_designation(target_widget, type_label)
        self._cb_update_preview(type_label, target_widget.currentText() if target_widget else "", KEY_MP_CB_BRACING_PREVIEW)

    def _on_cb_top_chord_section_type_changed(self, origin_key: str, target_widget: QComboBox) -> None:
        type_w = self.findChild(QComboBox, origin_key)
        type_label = type_w.currentText() if type_w else "Angle"
        if target_widget:
            self._cb_repopulate_designation(target_widget, type_label)
        self._cb_update_preview(type_label, target_widget.currentText() if target_widget else "", KEY_MP_CB_TOP_CHORD_PREVIEW)

    def _on_cb_bottom_chord_section_type_changed(self, origin_key: str, target_widget: QComboBox) -> None:
        type_w = self.findChild(QComboBox, origin_key)
        type_label = type_w.currentText() if type_w else "Angle"
        if target_widget:
            self._cb_repopulate_designation(target_widget, type_label)
        self._cb_update_preview(type_label, target_widget.currentText() if target_widget else "", KEY_MP_CB_BOTTOM_CHORD_PREVIEW)

    def _on_cb_bracing_preview_changed(self, origin_key: str, _target_widget) -> None:
        desig_w = self.findChild(QComboBox, origin_key)
        type_w  = self.findChild(QComboBox, KEY_MP_CB_BRACING_SECTION_TYPE)
        self._cb_update_preview(
            type_w.currentText()  if type_w  else "Angle",
            desig_w.currentText() if desig_w else "",
            KEY_MP_CB_BRACING_PREVIEW,
        )

    def _on_cb_top_chord_preview_changed(self, origin_key: str, _target_widget) -> None:
        desig_w = self.findChild(QComboBox, origin_key)
        type_w  = self.findChild(QComboBox, KEY_MP_CB_TOP_CHORD_SECTION_TYPE)
        self._cb_update_preview(
            type_w.currentText()  if type_w  else "Angle",
            desig_w.currentText() if desig_w else "",
            KEY_MP_CB_TOP_CHORD_PREVIEW,
        )

    def _on_cb_bottom_chord_preview_changed(self, origin_key: str, _target_widget) -> None:
        desig_w = self.findChild(QComboBox, origin_key)
        type_w  = self.findChild(QComboBox, KEY_MP_CB_BOTTOM_CHORD_SECTION_TYPE)
        self._cb_update_preview(
            type_w.currentText()  if type_w  else "Angle",
            desig_w.currentText() if desig_w else "",
            KEY_MP_CB_BOTTOM_CHORD_PREVIEW,
        )

    # ── Loading Tab ───────────────────────────────────────────────────────────────

    def _on_add_custom_vehicle(self, existing=None, widget=None):  # on_change: opens Custom Vehicle dialog and appends or updates the vehicle list
        from osdagbridge.desktop.ui.dialogs.additional_input.dialogs.custom_vehicle_dialog import CustomVehicleDialog
        from PySide6.QtWidgets import QDialog
        current_list = self.working_input_dict.get(KEY_LL_CUSTOM_VEHICLES)
        dlg = CustomVehicleDialog(self)
        if existing:
            dlg.load_vehicle_data(existing)
        if dlg.exec() == QDialog.Accepted:
            result  = dlg.vehicle_data
            updated = list(current_list)
            if existing and existing in updated:
                updated[updated.index(existing)] = result
            else:
                updated.append(result)
            self._on_field_edited(KEY_LL_CUSTOM_VEHICLES, updated)
            if widget:
                widget.update(updated)

    def _on_add_custom_combination(self, existing=None, widget=None):  # on_change: opens Load Combination dialog and appends or updates the combination list
        from osdagbridge.desktop.ui.dialogs.additional_input.dialogs.load_combination_dialog import LoadCombinationDialog
        from PySide6.QtWidgets import QDialog
        current_list = self.working_input_dict.get(KEY_LC_COMBINATIONS)
        dlg = LoadCombinationDialog(
            owner=self,
            existing=existing,
            load_combo_items=current_list,
            parent=self,
        )
        if dlg.exec() == QDialog.Accepted:
            result  = dlg._collect()
            updated = list(current_list)
            if existing and existing in updated:
                idx          = updated.index(existing)
                updated[idx] = result
            else:
                updated.append(result)
            self._on_field_edited(KEY_LC_COMBINATIONS, updated)
            if widget:
                widget.update(updated)

    def _compute_seismic_values(self, working_input_dict: dict) -> dict:  # compute: derives Ah, Av and spectral coefficients from IRC 6 seismic inputs
        from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

        zone     = working_input_dict.get(KEY_SL_SEISMIC_ZONE)
        soil_str = working_input_dict.get(KEY_SL_SOIL_TYPE, "")
        period   = working_input_dict.get(KEY_SL_TIME_PERIOD)
        damping  = working_input_dict.get(KEY_SL_DAMPING, "5")

        if not zone:
            return {}

        zone_map = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V"}
        zone = str(zone).strip().upper()
        if zone.isdigit():
            zone = zone_map.get(zone)

        soil_map = {
            "Type I – Rocky or Hard":  1,
            "Type II – Medium Soil":   2,
            "Type III – Soft Soil":    3,
        }
        soil_type = soil_map.get(soil_str, 1)

        dead_mode  = working_input_dict.get(KEY_SL_DEAD_LOAD_MODE, "Automatic")
        dead_value = working_input_dict.get(KEY_SL_DEAD_LOAD_VALUE)
        dead_load  = float(dead_value) if dead_mode == "Custom" and dead_value else 0.0

        live_mode  = working_input_dict.get(KEY_SL_LIVE_LOAD_MODE, "Automatic")
        live_value = working_input_dict.get(KEY_SL_LIVE_LOAD_VALUE)
        live_load  = float(live_value) if live_mode == "Custom" and live_value else 0.0

        result = IRC6_2017.cl_218_5_1(
            zone=f"Zone {zone}",
            soil_type=soil_type,
            dead_load_kN=dead_load,
            live_load_kN=live_load,
            period_T=float(period) if period else None,
            damping_percent=float(damping) if damping else 5.0,
        )

        Ah = result.get("Ah", 0)
        Av = round(Ah * 2 / 3, 4)  # Vertical = 2/3 horizontal per IRC 6

        return {
            KEY_SL_ZONE_FACTOR:       str(result.get("Z", "")),
            KEY_SL_SPECTRAL_COEFF:    str(result.get("Sa_g_adjusted", "")),
            KEY_SL_HORIZONTAL_COEFF:  str(Ah),
            KEY_SL_VERTICAL_COEFF:    str(Av),
        }

    def _compute_wind_values(self, working_input_dict: dict) -> dict:  # compute: derives hourly mean wind speed and pressure from IRC 6 wind inputs
        from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

        basic_wind_speed_str = working_input_dict.get(KEY_WL_BASIC_WIND_SPEED)
        height_str = working_input_dict.get(KEY_WL_AVG_EXPOSED_HEIGHT)
        terrain_str = working_input_dict.get(KEY_WL_TERRAIN_TYPE)

        if not basic_wind_speed_str or not height_str or not terrain_str:
            return {}

        try:
            height = float(height_str)
            basic_wind_speed = float(basic_wind_speed_str)
        except ValueError:
            return {}

        terrain_map = {
            "Plain Terrain": "plain",
            "Terrain with Obstructions": "obstructed"
        }
        terrain = terrain_map.get(terrain_str, "plain")

        result = IRC6_2017.table_12(height, terrain, basic_wind_speed)
        return {
            KEY_WL_HOURLY_MEAN_WIND: f"{result['Vz']:.2f}",
            KEY_WL_HOURLY_WIND_PRESSURE: f"{result['Pz']:.2f}",
        }

    def _compute_temperature_values(self, working_input_dict: dict) -> dict:  # compute: derives effective bridge temperature range and rise/fall from IRC 6 thermal inputs
        from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

        max_str = working_input_dict.get(KEY_TL_HIGHEST_MAX_TEMP)
        min_str = working_input_dict.get(KEY_TL_LOWEST_MIN_TEMP)
        if not max_str or not min_str or max_str == "—" or min_str == "—":
            return {}

        try:
            max_temp = float(max_str)
            min_temp = float(min_str)
        except ValueError:
            return {}

        res = IRC6_2017.cl_215_2_effective_bridge_temperature(max_temp, min_temp, 'metallic', False)
        t_min = res.get('T_min', 0)
        t_max = res.get('T_max', 0)

        mean_temp = (t_max + t_min) / 2.0
        rise = t_max - mean_temp
        fall = mean_temp - t_min

        return {
            KEY_TL_BRIDGE_TEMP_MIN: f"{t_min:.2f}",
            KEY_TL_BRIDGE_TEMP_MAX: f"{t_max:.2f}",
            KEY_TL_TEMP_RISE: f"{rise:.2f}",
            KEY_TL_TEMP_FALL: f"{fall:.2f}"
        }

    # ── Support Conditions Tab ────────────────────────────────────────────────────

    def _update_support_detail_cad(self):  # compute: updates the Support Detail CAD widget from the current bearing length value
        from osdagbridge.desktop.ui.dialogs.additional_input.drawings.support_detail_cad import SupportDetailCADWidget
        widget = self.findChild(SupportDetailCADWidget, KEY_SC_RIGHT_CAD)
        if widget is None:
            return
        value = self.working_input_dict.get(KEY_SC_BEARING_LENGTH, "400")
        try:
            value = float(value)
        except (ValueError, TypeError):
            value = 400.0
        widget.update_params({"bearing_length": value})

    # ── Typical Section Tab ───────────────────────────────────────────────────────

    def recalculate_girders(self, changed_field=None):  # on_text_changed: recalculates linked girder layout fields from current Typical Section widths
        allowed_fields = {"spacing", "overhang", "girders"}
        primary_edit = changed_field in allowed_fields
        if not primary_edit:
            changed_field = "girders"

        for notice_name in ("layout_notice.adjust", "layout_notice.warning"):
            label = self.findChild(QLabel, notice_name)
            if label is not None:
                label.hide()
                label.setText("")
        container = self.findChild(QWidget, "layout_notice")
        if container is not None:
            container.hide()

        required_keys = (
            KEY_TS_GIRDER_SPACING,
            KEY_TS_DECK_OVERHANG,
            KEY_TS_NO_OF_GIRDERS,
        )
        if primary_edit:
            for key in required_keys:
                field = self.findChild(QLineEdit, key)
                if field is not None and not field.text().strip():
                    for clear_key in required_keys:
                        clear_field = self.findChild(QLineEdit, clear_key)
                        if clear_field is not None:
                            clear_field.blockSignals(True)
                            clear_field.clear()
                            clear_field.blockSignals(False)
                        self.working_input_dict[clear_key] = ""
                    CustomMessageBox(
                        title="Layout",
                        text="Girder spacing, deck overhang, and number of girders are linked. Please enter all three.",
                        buttons=["OK"],
                        dialogType=MessageBoxType.Warning,
                    ).exec()
                    return False

        d = self.working_input_dict
        if not d.get(KEY_CARRIAGEWAY_WIDTH):
            return False

        def number_value(key, default=0.0):
            value = d.get(key)
            if value is None or value == "":
                return default
            if isinstance(value, (int, float)):
                return float(value)
            text = str(value).strip()
            scan = text[1:] if text[:1] in "+-" else text
            left, dot, right = scan.partition(".")
            if dot:
                return float(text) if bool(left or right) and (not left or left.isdigit()) and (not right or right.isdigit()) else default
            return float(text) if left.isdigit() else default

        rl_raw = number_value(KEY_RL_WIDTH, DEFAULT_RAILING_WIDTH)
        railing_width = rl_raw / 1000.0 if rl_raw > 10 else rl_raw

        footpath_str = str(d.get(KEY_FOOTPATH, "None")).strip()
        if footpath_str in ("None", ""):
            n_footpaths = 0
        elif "Both" in footpath_str:
            n_footpaths = 2
        else:
            n_footpaths = 1

        from osdagbridge.core.bridge_types.plate_girder.initial_sizing import BridgeConfigurationSolver
        solver = BridgeConfigurationSolver(
            carriageway_width=number_value(KEY_CARRIAGEWAY_WIDTH, float(self.carriageway_width or 0.0)),
            crash_barrier_width=number_value(KEY_CB_WIDTH, DEFAULT_CRASH_BARRIER_WIDTH),
            footpath_width=number_value(KEY_TS_FOOTPATH_WIDTH, 0.0),
            railing_width=railing_width,
            median_width=number_value(KEY_MD_WIDTH, 0.0),
            n_footpaths=n_footpaths,
        )

        spacing_old = number_value(KEY_TS_GIRDER_SPACING, DEFAULT_GIRDER_SPACING)
        overhang_old = number_value(KEY_TS_DECK_OVERHANG, 0.0)
        girders_old = int(number_value(KEY_TS_NO_OF_GIRDERS, 2))

        try:
            result = solver._solve_layout(
                no_of_girders=girders_old,
                girder_spacing=spacing_old,
                deck_overhang=overhang_old,
                changed_field=changed_field,
            )
        except ValueError as exc:
            CustomMessageBox(
                title="Layout",
                text=str(exc),
                buttons=["OK"],
                dialogType=MessageBoxType.Warning,
            ).exec()
            return False

        field_values = (
            (KEY_TS_GIRDER_SPACING, f"{result.girder_spacing:.2f}"),
            (KEY_TS_DECK_OVERHANG, f"{result.deck_overhang:.2f}"),
            (KEY_TS_NO_OF_GIRDERS, str(int(result.no_of_girders))),
            (KEY_TS_OVERALL_WIDTH, f"{result.overall_width:.2f}"),
        )
        for key, value in field_values:
            field = self.findChild(QLineEdit, key)
            if field is not None:
                field.blockSignals(True)
                field.setText(value)
                field.blockSignals(False)

        d[KEY_TS_GIRDER_SPACING] = result.girder_spacing
        d[KEY_TS_DECK_OVERHANG] = result.deck_overhang
        d[KEY_TS_NO_OF_GIRDERS] = result.no_of_girders
        d[KEY_TS_OVERALL_WIDTH] = result.overall_width
        d[KEY_TS_NO_OF_FOOTPATHS] = n_footpaths

        reason_parts = []
        if abs(result.girder_spacing - spacing_old) > 0.01:
            reason_parts.append(f"spacing {spacing_old:.2f}->{result.girder_spacing:.2f}")
        if abs(result.deck_overhang - overhang_old) > 1e-6:
            reason_parts.append(f"overhang {overhang_old:.2f}->{result.deck_overhang:.2f}")
        if result.no_of_girders != girders_old:
            reason_parts.append(f"girders {girders_old}->{result.no_of_girders}")

        warning_msg = None
        if result.deck_overhang > result.girder_spacing + 1e-6:
            warning_msg = (
                f"Overhang ({result.deck_overhang:.2f} m) exceeds girder spacing "
                f"({result.girder_spacing:.2f} m)"
            )

        adjust_label = self.findChild(QLabel, "layout_notice.adjust")
        warning_label = self.findChild(QLabel, "layout_notice.warning")
        notice_container = self.findChild(QWidget, "layout_notice")
        if reason_parts and not warning_msg and adjust_label is not None:
            adjust_label.setText(f"Values adjusted: {', '.join(reason_parts)}")
            adjust_label.show()
            if notice_container is not None:
                notice_container.show()
        if warning_msg and warning_label is not None:
            warning_label.setText(f"Warning: {warning_msg}")
            warning_label.show()
            if notice_container is not None:
                notice_container.show()

        if notice_container is not None and notice_container.isVisible():
            QTimer.singleShot(4000, notice_container.hide)

        return True

    def on_girder_spacing_changed(self):  # on_editing_finished: recalculates deck overhang after girder spacing changes
        field = self.findChild(QLineEdit, KEY_TS_GIRDER_SPACING)
        if field is None:
            return
        text = field.text().strip()
        scan = text[1:] if text[:1] in "+-" else text
        if text and not (scan.isdigit() or (scan.count(".") == 1 and scan.replace(".", "").isdigit())):
            return
        self.recalculate_girders("spacing")

    def on_deck_overhang_changed(self):  # on_editing_finished: recalculates girder spacing after deck overhang changes
        field = self.findChild(QLineEdit, KEY_TS_DECK_OVERHANG)
        if field is None:
            return
        text = field.text().strip()
        scan = text[1:] if text[:1] in "+-" else text
        if text and not (scan.isdigit() or (scan.count(".") == 1 and scan.replace(".", "").isdigit())):
            return
        self.recalculate_girders("overhang")

    def on_no_of_girders_changed(self):  # on_editing_finished: recalculates layout and dynamic girder keys after girder count changes
        field = self.findChild(QLineEdit, KEY_TS_NO_OF_GIRDERS)
        if field is None:
            return
        text = field.text().strip()
        scan = text[1:] if text[:1] in "+-" else text
        if text and not (scan.isdigit() or (scan.count(".") == 1 and scan.replace(".", "").isdigit())):
            return
        if self.recalculate_girders("girders"):
            from osdagbridge.core.bridge_types.plate_girder.defaults import _on_no_of_girders_changed
            _on_no_of_girders_changed(self.working_input_dict)

    # ── Public API ────────────────────────────────────────────────────────────────

    def get_all_values(self):  # public API: collects all CAD-relevant numeric parameters from the Typical Section Details tab
        """
        @author: Faizan
        Collect and return all CAD-relevant numeric parameters from the
        Typical Section Details tab.

        Includes values such as girder spacing, deck thickness, crash barrier,
        railing, median, wearing course, and cross bracing spacing.

        Used by InputDock to update and redraw the CAD cross-section.
        """

        from osdagbridge.core.utils.common import (
            KEY_TS_NO_OF_GIRDERS,
            KEY_TS_GIRDER_SPACING,
            KEY_TS_DECK_OVERHANG,
            KEY_TS_DECK_THICKNESS,
            KEY_TS_FOOTPATH_WIDTH,
            KEY_TS_FOOTPATH_THICKNESS,
            KEY_MP_CB_SPACING,
            KEY_WC_THICKNESS,
            KEY_WC_DENSITY,
            KEY_WC_MATERIAL,
        )

        values = {}

        no_of_girders = self.findChild(QLineEdit, KEY_TS_NO_OF_GIRDERS)
        if no_of_girders is not None and no_of_girders.text():
            values[KEY_TS_NO_OF_GIRDERS] = int(float(no_of_girders.text()))

        girder_spacing = self.findChild(QLineEdit, KEY_TS_GIRDER_SPACING)
        if girder_spacing is not None and girder_spacing.text():
            values[KEY_TS_GIRDER_SPACING] = float(girder_spacing.text())

        deck_overhang = self.findChild(QLineEdit, KEY_TS_DECK_OVERHANG)
        if deck_overhang is not None and deck_overhang.text():
            values[KEY_TS_DECK_OVERHANG] = float(deck_overhang.text())

        deck_thickness = self.findChild(QLineEdit, KEY_TS_DECK_THICKNESS)
        if deck_thickness is not None and deck_thickness.text():
            values[KEY_TS_DECK_THICKNESS] = float(deck_thickness.text())

        footpath_width = self.findChild(QLineEdit, KEY_TS_FOOTPATH_WIDTH)
        if footpath_width is not None and footpath_width.text():
            values[KEY_TS_FOOTPATH_WIDTH] = float(footpath_width.text())

        footpath_thickness = self.findChild(QLineEdit, KEY_TS_FOOTPATH_THICKNESS)
        if footpath_thickness is not None and footpath_thickness.text():
            values[KEY_TS_FOOTPATH_THICKNESS] = float(footpath_thickness.text())

        wearing_material = self.findChild(QWidget, KEY_WC_MATERIAL)
        if wearing_material:
            values[KEY_WC_MATERIAL] = wearing_material.currentText()

        wearing_thickness = self.findChild(QWidget, KEY_WC_THICKNESS)
        if wearing_thickness and wearing_thickness.text():
            values[KEY_WC_THICKNESS] = float(wearing_thickness.text())

        wearing_density = self.findChild(QWidget, KEY_WC_DENSITY)
        if wearing_density and wearing_density.text():
            values[KEY_WC_DENSITY] = float(wearing_density.text())

        # ---- Crash Barrier ----
        crash_barrier_type = self.findChild(QWidget, KEY_CB_TYPE)
        if crash_barrier_type:
            values["crash_barrier_type"] = crash_barrier_type.currentText()

        crash_barrier_width = self.findChild(QWidget, KEY_CB_WIDTH)
        if crash_barrier_width and crash_barrier_width.text():
            values[KEY_CB_WIDTH] = float(crash_barrier_width.text())

        crash_barrier_height = self.findChild(QWidget, KEY_CB_HEIGHT)
        if crash_barrier_height and crash_barrier_height.text():
            values["crash_barrier_height"] = float(crash_barrier_height.text())

        # ---- Railing ----
        railing_type = self.findChild(QWidget, KEY_RL_TYPE)
        if railing_type:
            values[KEY_RL_TYPE] = railing_type.currentText()

        railing_width = self.findChild(QWidget, KEY_RL_WIDTH)
        if railing_width and railing_width.text():
            values[KEY_RL_WIDTH] = float(railing_width.text())

        railing_height = self.findChild(QWidget, KEY_RL_HEIGHT)
        if railing_height and railing_height.text():
            values["railing_height"] = float(railing_height.text())

        # ---- Median ----
        median_type = self.findChild(QWidget, KEY_MD_TYPE)
        if median_type:
            values[KEY_MD_TYPE] = median_type.currentText()

        median_width = self.findChild(QWidget, KEY_MD_WIDTH)
        if median_width and median_width.text():
            values[KEY_MD_WIDTH] = float(median_width.text())

        return values

    # --------------------- Deck Details sub-tab functionality (Migrated) ---------------------

    def on_layout_width_changed(self, *_):
        self.recalculate_girders()

    def update_footpath_thickness(self):
        deck_thickness = self.findChild(QLineEdit, KEY_TS_DECK_THICKNESS)
        footpath_thickness = self.findChild(QLineEdit, KEY_TS_FOOTPATH_THICKNESS)
        if deck_thickness and footpath_thickness:
            if deck_thickness.text() and not footpath_thickness.text():
                footpath_thickness.setText(deck_thickness.text())

    # --- Typical Section Tab Build & Handlers ---

    _TS_SCROLL_STYLE = (
        "QScrollArea { background:transparent; padding:0px 5px; border:none}"
        " QScrollArea QScrollBar:vertical { border:none; background:#f0f0f0; width:8px; }"
        " QScrollArea QScrollBar::handle:vertical { background:#c0c0c0; border-radius:4px; min-height:20px; }"
        " QScrollArea QScrollBar::handle:vertical:hover { background:#a0a0a0; }"
        " QScrollArea QScrollBar::add-line:vertical,"
        " QScrollArea QScrollBar::sub-line:vertical { border:none; background:none; }"
    )

    def _build_typical_section_tab(self):
        from osdagbridge.desktop.ui.docks.cad_cross_section import CrossSectionCADWidget
        from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import TYPICAL_SECTION_SCHEMA

        self.cad_preview = CrossSectionCADWidget()
        self.cad_preview.scale_factor = 0.65
        self.cad_preview.setMinimumHeight(200)
        self._initial_cad_state = {}

        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(0)

        # ── CAD Preview ───────────────────────────────────────────────────────
        diagram = QWidget()
        diagram.setStyleSheet("QWidget { background: transparent; border: 1px solid #b0b0b0; border-radius: 8px; }")
        diagram.setMinimumHeight(280)
        diagram.setMaximumHeight(380)
        diagram_layout = QVBoxLayout(diagram)
        diagram_layout.setContentsMargins(5, 5, 5, 5)
        cad_scroll = QScrollArea()
        cad_scroll.setWidgetResizable(True)
        cad_scroll.setFrameShape(QFrame.NoFrame)
        cad_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        cad_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        cad_scroll.setStyleSheet(self._TS_SCROLL_STYLE)
        cad_scroll.setWidget(self.cad_preview)
        diagram_layout.addWidget(cad_scroll)
        layout.addWidget(diagram)
        layout.addSpacing(5)

        # ── Input container ───────────────────────────────────────────────────
        input_container = QWidget()
        input_container.setStyleSheet("QWidget { background-color: white; border: none;}")
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(0, 10, 0, 0)
        input_layout.setSpacing(10)

        schema = TYPICAL_SECTION_SCHEMA
        self._ts_tab_widgets = {}

        if "primary_fields" in schema:
            primary = UIBuilder(
                owner=self, schema=schema["primary_fields"],
                card_title="Inputs:", main_widget_object_name="primary_fields.main",
                additional_input_instance=self, filler_column_index=None,
            )
            primary.setAutoFillBackground(True)
            primary.setObjectName("layout_primary_fields")
            primary.setStyleSheet("QWidget#layout_primary_fields { border: none; }")
            primary.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
            input_layout.addWidget(primary)

        # ── Sub-tabs ──────────────────────────────────────────────────────────
        self._ts_input_tabs = None
        if "tabs" in schema:
            self._ts_input_tabs = QTabWidget()
            self._ts_input_tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            self._ts_input_tabs.setTabBarAutoHide(False)
            self._ts_input_tabs.setStyleSheet("""
                QTabBar { background-color: #e8e8e8; border: 1px solid red; }
                QTabWidget::pane { border: none; background-color: #f5f5f5; }
                QTabBar::tab {
                    background-color: #e8e8e8; color: #555; padding: 10px 20px;
                    border: 1px solid #b0b0b0; border-bottom: none; border-right: none;
                    font-size: 11px; min-width: 80px;
                }
                QTabBar::tab:disabled { color: #bfbfbf; background: #e6e6e6; }
                QTabBar::tab:last { border-right: 1px solid #b0b0b0; }
                QTabBar::tab:selected {
                    background-color: #90AF13; color: white; font-weight: bold;
                    border: 1px solid #90AF13; border-bottom: none;
                }
                QTabBar::tab:hover:!selected { background-color: #d0d0d0; }
            """)
            self._ts_input_tabs.tabBar().setElideMode(Qt.ElideNone)
            self._ts_input_tabs.tabBar().setExpanding(False)
            self._ts_input_tabs.tabBar().setUsesScrollButtons(True)
            self._ts_input_tabs.tabBar().setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            for tab_def in schema["tabs"]:
                tab_id = tab_def["id"]
                sub_tab = UIBuilder(
                    owner=self, schema=tab_def,
                    card_title="Inputs:", main_widget_object_name=tab_id + ".main",
                    additional_input_instance=self, filler_column_index=2,
                )
                self._ts_tab_widgets[tab_id] = sub_tab
                self._ts_input_tabs.addTab(sub_tab, tab_def["label"])

            self._ts_input_tabs.currentChanged.connect(self._on_ts_subtab_changed)
            self._on_ts_subtab_changed(self._ts_input_tabs.currentIndex())
            input_layout.addWidget(self._ts_input_tabs)

        # ── Scroll wrapper ────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet(self._TS_SCROLL_STYLE +
            " QScrollArea { border: 1px solid #b0b0b0; border-radius: 0px 0px 8px 8px; background: white; }")
        scroll.setWidget(input_container)
        layout.addWidget(scroll)

        return tab

    def _on_ts_subtab_changed(self, index):
        if not self._ts_input_tabs:
            return
        for i in range(self._ts_input_tabs.count()):
            w = self._ts_input_tabs.widget(i)
            if i == index:
                w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            else:
                w.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self._ts_input_tabs.updateGeometry()

    def _sync_tab_active_states(self):
        from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import TYPICAL_SECTION_SCHEMA
        if not self._ts_input_tabs:
            return
        for tab_def in TYPICAL_SECTION_SCHEMA["tabs"]:
            active_def = tab_def.get("active")
            if not active_def:
                continue
            tab_widget = self._ts_tab_widgets.get(tab_def["id"])
            if not tab_widget:
                continue
            enabled = self.working_input_dict.get(active_def["id"]) in active_def["values"]
            self._ts_input_tabs.setTabEnabled(self._ts_input_tabs.indexOf(tab_widget), enabled)

    def _auto_compute_crash_barrier_load(self):
        from osdagbridge.core.bridge_components.super_structure.crash_barrier.properties import metallic_edge_barrier_load
        crash_barrier_type = self.findChild(QWidget, KEY_CB_TYPE)
        crash_barrier_density = self.findChild(QWidget, KEY_CB_DENSITY)
        crash_barrier_area = self.findChild(QWidget, KEY_CB_AREA)
        crash_barrier_load = self.findChild(QWidget, KEY_CB_LOAD)
        barrier_type = crash_barrier_type.currentText() if crash_barrier_type else ""

        is_rcc = barrier_type.startswith("IRC 5 - RCC") or barrier_type.startswith("IRC 5 - High")
        is_metallic = barrier_type.startswith("IRC 5 - Metallic")

        if is_rcc:
            d_text = crash_barrier_density.text() if crash_barrier_density and crash_barrier_density.text() else ""
            a_text = crash_barrier_area.text() if crash_barrier_area and crash_barrier_area.text() else ""
            if d_text.replace('.', '', 1).replace('-', '', 1).isdigit() and a_text.replace('.', '', 1).replace('-', '', 1).isdigit():
                load = float(d_text) * float(a_text)
                if crash_barrier_load:
                    crash_barrier_load.setText(f"{load:.2f}")
            else:
                if crash_barrier_load:
                    crash_barrier_load.clear()
        elif is_metallic:
            metallic_variant = "Double" if "Double" in barrier_type else "Single"
            load_data = metallic_edge_barrier_load(metallic_variant)
            if load_data and 'total_load_kN_per_m' in load_data and crash_barrier_load:
                crash_barrier_load.setText(f"{load_data['total_load_kN_per_m']:.2f}")

    def on_crash_barrier_type_changed(self, barrier_type, force=True):
        from osdagbridge.desktop.cad.irc5_geometry import CrashBarrierGeometry

        is_rcc = barrier_type.startswith("IRC 5 - RCC") or barrier_type.startswith("IRC 5 - High")
        is_metallic = barrier_type.startswith("IRC 5 - Metallic")
        is_custom = barrier_type == "Custom"

        crash_barrier_density = self.findChild(QWidget, KEY_CB_DENSITY)
        crash_barrier_density_label = self.findChild(QWidget, f"{KEY_CB_DENSITY}_label")
        crash_barrier_width = self.findChild(QWidget, KEY_CB_WIDTH)
        crash_barrier_height = self.findChild(QWidget, KEY_CB_HEIGHT)
        crash_barrier_area = self.findChild(QWidget, KEY_CB_AREA)
        crash_barrier_area_label = self.findChild(QWidget, f"{KEY_CB_AREA}_label")
        crash_barrier_load = self.findChild(QWidget, KEY_CB_LOAD)
        crash_barrier_post_spacing = self.findChild(QWidget, KEY_CB_POST_SPACING)
        crash_barrier_post_spacing_label = self.findChild(QWidget, f"{KEY_CB_POST_SPACING}_label")

        if not crash_barrier_density:
            return

        # --- Populate defaults from IRC 5 geometry ---
        effective_type = "IRC 5 - RCC Crash Barrier" if is_custom else barrier_type
        geom = CrashBarrierGeometry.get_geometry(effective_type)

        def _set(widget, value):
            if widget is None:
                return
            if force or not widget.text():
                widget.setText(value)

        if is_rcc and geom:
            _set(crash_barrier_density, f"{DEFAULT_CONCRETE_DENSITY:.1f}")
            if "bottom_width" in geom:
                _set(crash_barrier_width, f"{geom['bottom_width'] / 1000:.2f}")
            if "total_height" in geom:
                _set(crash_barrier_height, f"{geom['total_height'] / 1000:.2f}")
            if crash_barrier_width and crash_barrier_height:
                w_text = crash_barrier_width.text() or ""
                h_text = crash_barrier_height.text() or ""
                if w_text.replace('.', '', 1).isdigit() and h_text.replace('.', '', 1).isdigit():
                    _set(crash_barrier_area, f"{float(w_text) * float(h_text):.2f}")
        elif is_metallic:
            if crash_barrier_post_spacing:
                _set(crash_barrier_post_spacing, "1")
        elif is_custom:
            if geom:
                if "bottom_width" in geom:
                    _set(crash_barrier_width, f"{geom['bottom_width'] / 1000:.2f}")
                if "total_height" in geom:
                    _set(crash_barrier_height, f"{geom['total_height'] / 1000:.2f}")
            if force and crash_barrier_load:
                crash_barrier_load.clear()

        # --- Visibility: density/area hidden for metallic/custom ---
        hide_density_area = is_metallic or is_custom
        for w in [crash_barrier_density, crash_barrier_density_label, crash_barrier_area, crash_barrier_area_label]:
            if w:
                w.setVisible(not hide_density_area)
        if hide_density_area:
            if crash_barrier_density:
                crash_barrier_density.clear()
            if crash_barrier_area:
                crash_barrier_area.clear()

        # Post spacing only for metallic
        for w in [crash_barrier_post_spacing, crash_barrier_post_spacing_label]:
            if w:
                w.setVisible(is_metallic)
        if is_metallic and crash_barrier_post_spacing and not crash_barrier_post_spacing.text():
            crash_barrier_post_spacing.setText("1")
        if not is_metallic and crash_barrier_post_spacing:
            crash_barrier_post_spacing.clear()

        # --- Load behavior ---
        if crash_barrier_load:
            crash_barrier_load.setVisible(True)
            crash_barrier_load.setEnabled(not is_custom)
            crash_barrier_load.setReadOnly(True)
            crash_barrier_load.setPlaceholderText("" if not is_custom else "Enter custom load per IRC 6 guidance")
        if is_rcc or is_metallic:
            self._auto_compute_crash_barrier_load()
        else:
            if crash_barrier_load:
                crash_barrier_load.setReadOnly(False)
                crash_barrier_load.setEnabled(True)

        # Grey out fixed parameters per IRC 5
        for w in [crash_barrier_density, crash_barrier_width, crash_barrier_height, crash_barrier_area]:
            if w:
                w.setEnabled(is_custom)

        # --- CAD preview ---
        params = {KEY_CB_TYPE: barrier_type}
        if crash_barrier_width and crash_barrier_width.text():
            params[KEY_CB_WIDTH] = float(crash_barrier_width.text()) * 1000
        if crash_barrier_height and crash_barrier_height.text():
            params[KEY_CB_HEIGHT] = float(crash_barrier_height.text()) * 1000
        self.cad_preview.update_params(params)

        self.recalculate_girders()


    def on_median_type_changed(self, median_type, force=True):
        from osdagbridge.desktop.cad.irc5_geometry import MedianGeometry
        from osdagbridge.core.bridge_components.super_structure.median.properties import median_metallic_barrier_load

        is_rcc = median_type.startswith("IRC 5 - RCC") or median_type.startswith("IRC 5 - Raised")
        is_metallic = median_type.startswith("IRC 5 - Metallic")
        is_custom = median_type == "Custom"

        median_density = self.findChild(QWidget, KEY_MD_DENSITY)
        median_density_label = self.findChild(QWidget, f"{KEY_MD_DENSITY}_label")
        median_width = self.findChild(QWidget, KEY_MD_WIDTH)
        median_height = self.findChild(QWidget, KEY_MD_HEIGHT)
        median_area = self.findChild(QWidget, KEY_MD_AREA)
        median_area_label = self.findChild(QWidget, f"{KEY_MD_AREA}_label")
        median_load = self.findChild(QWidget, KEY_MD_LOAD)
        median_post_spacing = self.findChild(QWidget, KEY_MD_POST_SPACING)
        median_post_spacing_label = self.findChild(QWidget, f"{KEY_MD_POST_SPACING}_label")

        if not median_density:
            return

        # --- Populate defaults from IRC 5 geometry ---
        effective_type = "IRC 5 - Raised Kerb" if is_custom else median_type
        geom = MedianGeometry.get_geometry(effective_type)

        def _set(widget, value):
            if widget is None:
                return
            if force or not widget.text():
                widget.setText(value)

        if is_rcc and geom:
            _set(median_density, f"{DEFAULT_CONCRETE_DENSITY:.1f}")
            if KEY_MD_WIDTH in geom:
                _set(median_width, f"{geom[KEY_MD_WIDTH] / 1000:.2f}")
            if "barrier_height" in geom:
                _set(median_height, f"{geom['barrier_height'] / 1000:.2f}")
            elif "kerb_height" in geom:
                _set(median_height, f"{geom['kerb_height'] / 1000:.2f}")
            if median_width and median_height:
                w_text = median_width.text() or ""
                h_text = median_height.text() or ""
                if w_text.replace('.', '', 1).isdigit() and h_text.replace('.', '', 1).isdigit():
                    _set(median_area, f"{float(w_text) * float(h_text):.2f}")
        elif is_metallic:
            if median_post_spacing:
                _set(median_post_spacing, "1")
        elif is_custom:
            if geom:
                if KEY_MD_WIDTH in geom:
                    _set(median_width, f"{geom[KEY_MD_WIDTH] / 1000:.2f}")
                if "barrier_height" in geom:
                    _set(median_height, f"{geom['barrier_height'] / 1000:.2f}")
                elif "kerb_height" in geom:
                    _set(median_height, f"{geom['kerb_height'] / 1000:.2f}")
            if force and median_load:
                median_load.clear()

        # --- Compute load inline ---
        if is_rcc:
            d_text = median_density.text() if median_density and median_density.text() else ""
            a_text = median_area.text() if median_area and median_area.text() else ""
            if d_text.replace('.', '', 1).replace('-', '', 1).isdigit() and a_text.replace('.', '', 1).replace('-', '', 1).isdigit():
                load = float(d_text) * float(a_text)
                if median_load:
                    median_load.setText(f"{load:.2f}")
            else:
                if median_load:
                    median_load.clear()
        elif is_metallic:
            load_data = median_metallic_barrier_load(median_type)
            if load_data and 'total_load_kN_per_m' in load_data and median_load:
                median_load.setText(f"{load_data['total_load_kN_per_m']:.2f}")

        # --- Visibility: density/area hidden for metallic/custom ---
        hide_density_area = is_metallic or is_custom
        for w in [median_density, median_density_label, median_area, median_area_label]:
            if w is not None:
                w.setVisible(not hide_density_area)
        if hide_density_area:
            if median_density:
                median_density.clear()
            if median_area:
                median_area.clear()

        # Post spacing only for metallic
        for w in [median_post_spacing, median_post_spacing_label]:
            if w is not None:
                w.setVisible(is_metallic)
        if is_metallic and median_post_spacing and not median_post_spacing.text():
            median_post_spacing.setText("1")
        if not is_metallic and median_post_spacing:
            median_post_spacing.clear()

        # --- Load behavior ---
        if median_load:
            median_load.setVisible(True)
            median_load.setEnabled(True)
            median_load.setReadOnly(is_rcc)
            median_load.setPlaceholderText("" if not is_custom else "Enter custom load per IRC 6 guidance")
        if not is_rcc and not is_metallic and median_load:
            median_load.setReadOnly(False)

        # Grey out fixed parameters per IRC 5
        for w in [median_density, median_width, median_height, median_area, median_load]:
            if w:
                w.setEnabled(is_custom)
        if median_post_spacing:
            median_post_spacing.setEnabled(is_custom or is_metallic)

        # --- CAD preview ---
        params = {"median_present": True, KEY_MD_TYPE: median_type}
        if median_width and median_width.text():
            params[KEY_MD_WIDTH] = float(median_width.text()) * 1000
        if median_height and median_height.text():
            params[KEY_MD_HEIGHT] = float(median_height.text()) * 1000
        self.cad_preview.update_params(params)

        self.recalculate_girders()



    def on_railing_type_changed(self, railing_type, force=True):
        from osdagbridge.desktop.cad.irc5_geometry import RailingGeometry

        railing_type_w = self.findChild(QWidget, KEY_RL_TYPE)
        if not railing_type_w:
            return

        railing_type = railing_type_w.currentText()
        is_custom = railing_type == "Custom"
        effective_type = "IRC 5 - RCC Railing" if is_custom else railing_type
        geom = RailingGeometry.get_geometry(effective_type)

        railing_width = self.findChild(QWidget, KEY_RL_WIDTH)
        railing_height = self.findChild(QWidget, KEY_RL_HEIGHT)
        railing_load_mode = self.findChild(QWidget, KEY_RL_LOAD_MODE)

        def _set(widget, value):
            if widget is None:
                return
            if force or not widget.text():
                widget.setText(value)

        if geom:
            if "width" in geom:
                _set(railing_width, f"{geom['width']:.0f}")
            if "height" in geom:
                _set(railing_height, f"{geom['height'] / 1000:.2f}")

        # Grey out fixed parameters per IRC 5
        if railing_width:
            railing_width.setEnabled(is_custom)
        if railing_height:
            railing_height.setEnabled(is_custom)
        if railing_load_mode:
            railing_load_mode.setEnabled(is_custom)

        if railing_load_mode:
            railing_load_mode.blockSignals(True)
            railing_load_mode.setCurrentText("As per IRC 6")
            railing_load_mode.blockSignals(False)
            self.on_railing_load_mode_changed("As per IRC 6")

        # --- CAD preview ---
        params = {KEY_RL_TYPE: railing_type}
        if geom:
            if "height" in geom:
                params["railing_height"] = geom["height"]
            if "width" in geom:
                params["railing_width"] = geom["width"]
        self.cad_preview.update_params(params)

        self.recalculate_girders()


    def on_railing_load_mode_changed(self, mode):
        railing_load_value = self.findChild(QWidget, KEY_RL_LOAD_VALUE)
        if not railing_load_value:
            return
        is_auto = mode.startswith("As per") or mode.startswith("Automatic")
        if is_auto:
            railing_load_value.setReadOnly(True)
            railing_load_value.setEnabled(True)
            railing_load_value.setText("1.5")
            railing_load_value.setPlaceholderText("")
            # Subtle disabled styling for auto mode
            railing_load_value.setStyleSheet(
                "QLineEdit { background-color: #f1f1f1; color: #7a7a7a;"
                " border: 1px solid #bfbfbf; border-radius: 4px; padding: 4px 6px; }"
            )
        else:
            # User-defined mode - allow user to enter value
            railing_load_value.setReadOnly(False)
            railing_load_value.setEnabled(True)
            railing_load_value.clear()
            railing_load_value.setPlaceholderText("Enter load value")
            # Restore normal styling
            railing_load_value.setStyleSheet(
                "QLineEdit { background-color: #ffffff; color: #000000;"
                " border: 1px solid #000000; border-radius: 4px; padding: 4px 6px; }"
            )



    def on_wearing_material_changed(self, material):
        wearing_density = self.findChild(QWidget, KEY_WC_DENSITY)
        wearing_thickness = self.findChild(QWidget, KEY_WC_THICKNESS)
        if not wearing_density or not wearing_thickness:
            return
        # Defaults per material; allow user edits afterward
        if material == "Concrete":
            wearing_density.setText("24.0")
        elif material == "Bituminous":
            wearing_density.setText("22.0")
        else:
            wearing_density.clear()

        # Grey out density for fixed-density materials; enable for Other and Custom
        wearing_density.setEnabled(material not in ("Concrete", "Bituminous"))

        if not wearing_thickness.text():
            wearing_thickness.setText("50")

    def _initialize_lane_defaults(self):
        """Populate combo + table with IRC 5 Clause 104.3.1 defaults on first open."""
        lane_count_combo = self.findChild(QComboBox, KEY_WC_LD_LANE_TABLE_COUNT)
        lane_table       = self.findChild(QTableWidget, KEY_WC_LD_LANE_TABLE)
        if not lane_count_combo or not lane_table:
            return

        max_allowed = 1
        cw_str = str(self.carriageway_width).strip()
        if cw_str.replace('.', '', 1).isdigit():
            max_allowed = max(1, min(6, int(math.floor(float(cw_str) / 3.5))))

        self._updating_lane_table = True
        lane_count_combo.blockSignals(True)
        lane_count_combo.clear()
        for i in range(1, max_allowed + 1):
            lane_count_combo.addItem(str(i))
        lane_count_combo.setCurrentText(str(max_allowed))
        lane_count_combo.blockSignals(False)
        self._reset_lane_rows(lane_table, max_allowed)
        self._fill_lane_defaults(lane_table, max_allowed)
        self._updating_lane_table = False

        if not getattr(self, "_lane_cell_signal_connected", False):
            lane_table.cellChanged.connect(self._on_lane_cell_changed)
            self._lane_cell_signal_connected = True


    def _reset_lane_rows(self, lane_table, num_lanes):
        """Resize the table and stamp lane-number items in column 0."""
        lane_table.setRowCount(num_lanes)
        for i in range(num_lanes):
            num_item = QTableWidgetItem(str(i + 1))
            num_item.setFlags(num_item.flags() & ~Qt.ItemIsEditable)
            num_item.setTextAlignment(Qt.AlignCenter)
            lane_table.setItem(i, 0, num_item)
            for col in (1, 2):
                cell = QTableWidgetItem("")
                cell.setTextAlignment(Qt.AlignCenter)
                lane_table.setItem(i, col, cell)


    def _fill_lane_defaults(self, lane_table, lane_count):
        """Write default start positions and widths (IRC 5: 3.5 m each)."""
        start = 0.0
        for i in range(lane_count):
            self._set_cell(lane_table, i, 1, f"{start:.2f}")
            self._set_cell(lane_table, i, 2, f"{3.5:.2f}")
            start += 3.5


    def _set_cell(self, lane_table, row, col, text):
        """Write text into a table cell, creating the item if needed."""
        item = lane_table.item(row, col)
        if item is None:
            item = QTableWidgetItem()
            item.setTextAlignment(Qt.AlignCenter)
            lane_table.setItem(row, col, item)
        item.setText(text)


    def _recompute_lane_starts(self):
        """Recompute cumulative start positions from current widths; warn if total > carriageway."""
        lane_table = self.findChild(QTableWidget, KEY_WC_LD_LANE_TABLE)
        if not lane_table or lane_table.rowCount() == 0:
            return

        start = 0.0
        total = 0.0
        self._updating_lane_table = True
        for i in range(lane_table.rowCount()):
            item = lane_table.item(i, 2)
            w_text = item.text() if item and item.text() else ""
            w = 3.5
            if w_text.replace('.', '', 1).isdigit():
                w = float(w_text)
            if w < 3.5:
                w = 3.5
                self._set_cell(lane_table, i, 2, f"{w:.2f}")
            self._set_cell(lane_table, i, 1, f"{start:.2f}")
            start += w
            total += w
        self._updating_lane_table = False

        carriageway = None
        cw_str = str(self.carriageway_width).strip() if self.carriageway_width else ""
        if cw_str.replace('.', '', 1).isdigit():
            carriageway = float(cw_str)
        if carriageway and total - carriageway > 1e-6:
            CustomMessageBox(
                title="Lane Width Exceeds Carriageway",
                text=f"Sum of lane widths ({total:.2f} m) exceeds carriageway width ({carriageway:.2f} m).\n"
                      "Adjust lane count or widths per IRC 5 Clause 104.3.1.",
                buttons=["OK"],
                dialogType=MessageBoxType.Warning,
            ).exec()


    def _on_lane_cell_changed(self, row, column):
        """Validate the edited cell and recompute start positions."""
        if self._updating_lane_table:
            return
        lane_table = self.findChild(QTableWidget, KEY_WC_LD_LANE_TABLE)
        if not lane_table:
            return

        if column == 2:
            # Validate width >= IRC minimum
            item = lane_table.item(row, 2)
            w_text = item.text() if item and item.text() else ""
            w = None
            if w_text.replace('.', '', 1).isdigit():
                w = float(w_text)
            if w is None or w + 1e-6 < 3.5:
                if w is not None:
                    CustomMessageBox(
                        title="Lane Width Below IRC Minimum",
                        text=f"IRC 5 Clause 104.3.1 requires a lane width of at least {3.5:.2f} m.",
                        buttons=["OK"],
                        dialogType=MessageBoxType.Critical,
                    ).exec()
                self._set_cell(lane_table, row, 2, f"{3.5:.2f}")

        elif column == 1:
            # Validate start position continuity
            item = lane_table.item(row, 1)
            s_text = item.text() if item and item.text() else ""
            start = None
            if s_text.replace('.', '', 1).replace('-', '', 1).isdigit():
                start = float(s_text)

            if start is None:
                self._recompute_lane_starts()
                return
            if row == 0:
                if abs(start) > 1e-6:
                    CustomMessageBox(
                        title="Lane Start Offset",
                        text="First lane must start at 0 m from inner edge of crash barrier.",
                        buttons=["OK"],
                        dialogType=MessageBoxType.Warning,
                    ).exec()
                    self._recompute_lane_starts()
                return
            prev_s_item = lane_table.item(row - 1, 1)
            prev_w_item = lane_table.item(row - 1, 2)
            prev_s = float(prev_s_item.text()) if prev_s_item and prev_s_item.text() else 0.0
            prev_w = float(prev_w_item.text()) if prev_w_item and prev_w_item.text() else 3.5
            if abs(start - (prev_s + prev_w)) > 1e-3:
                CustomMessageBox(
                    title="Lane Start Sequence",
                    text="Each lane start must equal previous lane start plus previous lane width.",
                    buttons=["OK"],
                    dialogType=MessageBoxType.Warning,
                ).exec()
                self._recompute_lane_starts()
                return

        self._recompute_lane_starts()


    def on_lane_count_changed(self, text):
        """Handle lane count combo change — resize table and fill defaults."""
        if self._updating_lane_table:
            return
        if not str(text).isdigit():
            return
        num_lanes = int(text)
        lane_table = self.findChild(QTableWidget, KEY_WC_LD_LANE_TABLE)
        if lane_table:
            self._reset_lane_rows(lane_table, num_lanes)
            self._fill_lane_defaults(lane_table, num_lanes)


    def _on_lane_table_ready(self, origin_key, target_widget):
        if getattr(self, "_lane_table_connected", False):
            target_widget.cellChanged.disconnect(self._on_lane_cell_changed)
        self._lane_table_connected = True
        target_widget.cellChanged.connect(self._on_lane_cell_changed)

    def update_footpath_value(self, footpath_value):
        self.footpath_value = footpath_value
        if self.working_input_dict is not None:
            self.working_input_dict[KEY_FOOTPATH] = footpath_value

        fw = self.findChild(QLineEdit, KEY_TS_FOOTPATH_WIDTH)
        ft = self.findChild(QLineEdit, KEY_TS_FOOTPATH_THICKNESS)
        if fw:
            fw.setEnabled(footpath_value != "None")
        if ft:
            ft.setEnabled(footpath_value != "None")

        fp_map = {"Both Sides": "both", "Single Side": "left", "None": "none"}
        self._initial_cad_state["footpath_config"] = fp_map.get(footpath_value, "none")

        if self._ts_input_tabs:
            for i in range(self._ts_input_tabs.count()):
                if "Railing" in self._ts_input_tabs.tabText(i):
                    self._ts_input_tabs.setTabEnabled(i, str(footpath_value).lower() != "none")
                    break

        self.recalculate_girders()

    # ── Utilities ─────────────────────────────────────────────────────────────────

    def style_input_field(self, field):  # utility: applies standard field stylesheet
        apply_field_style(field)

    def _enforce_decimal_places(self, places=2):  # utility: caps QDoubleValidator decimal places for all standard-notation line edits
        for line_edit in self.findChildren(QLineEdit):
            validator = line_edit.validator()
            if isinstance(validator, QDoubleValidator):
                if validator.notation() != QDoubleValidator.ScientificNotation:
                    validator.setDecimals(places)
                    validator.setNotation(QDoubleValidator.StandardNotation)

    def _normalize_numeric_texts(self, places=2):  # utility: reformats existing numeric QLineEdit text to the given decimal places
        fmt = f"{{:.{places}f}}"
        for line_edit in self.findChildren(QLineEdit):
            validator = line_edit.validator()
            if isinstance(validator, QDoubleValidator) and validator.notation() == QDoubleValidator.ScientificNotation:
                continue
            text = line_edit.text().strip()
            if not text:
                continue
            try:
                val = float(text)
                line_edit.setText(fmt.format(val))
            except ValueError:
                continue

    def _find_inner_tab_index(self, tab_widget, tab_name: str) -> int:  # utility: returns the index of an inner tab by its label text, or -1 if not found
        """
        @author: Faizan
        Return the index of an inner tab by its label, or -1 if not found.
        """
        for i in range(tab_widget.count()):
            if tab_widget.tabText(i).strip().lower() == tab_name.strip().lower():
                return i
        return -1
