"""
Additional Inputs Widget for Highway Bridge Design
Provides detailed input fields for manual bridge parameter definition
"""
from copy import deepcopy

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTabBar, QLabel, QLineEdit,
    QComboBox, QGroupBox, QPushButton, QCheckBox, QMessageBox, QSizePolicy,
    QGridLayout, QDialog, QSizePolicy, QSizeGrip, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDoubleValidator, QIntValidator

from osdagbridge.core.bridge_types.plate_girder.validator import BridgeInputValidator
from osdagbridge.core.utils.common import *
from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style, create_action_button_bar
from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox, MessageBoxType
from osdagbridge.desktop.ui.dialogs.additional_input.tabs.typical_section.typical_section_details import TypicalSectionDetailsTab
from osdagbridge.desktop.ui.dialogs.tabs.section_properties_tab import SectionPropertiesTab
from osdagbridge.desktop.ui.utils.custom_widgets import SmartCursorComboBoxView
from osdagbridge.desktop.ui.dialogs.additional_input.ui_builder.common_ui_builder import UIBuilder
from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import (
    DESIGN_OPTIONS_SCHEMA,
    DESIGN_OPTIONS_CONT_SCHEMA,
    SUPPORT_CONDITIONS_SCHEMA,
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

        # Sub-Tab 1: Typical Section Details
        self.typical_section_tab = TypicalSectionDetailsTab(
            self.carriageway_width,
            additional_input_instance=self)
        self.typical_section_tab.update_footpath_value(self.footpath_value)
        self.tabs.addTab(self.typical_section_tab, "Typical Section Details")

        # Sub-Tab 2: Member Properties
        self.section_properties_tab = SectionPropertiesTab(
            additiona_input_instance=self
        )
        self.tabs.addTab(self.section_properties_tab, "Member Properties")
        self.section_properties_tab.set_editable_mode(self._member_properties_editable)

        # Keep girder count in sync across tabs
        try:
            self.typical_section_tab.girder_count_changed.connect(self.section_properties_tab.set_girder_count)
            self._sync_member_properties_girder_count()
        except Exception:
            pass

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

        self.tabs.currentChanged.connect(self._on_top_tab_changed)
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

        self.typical_section_tab._sync_tab_active_states()
        self.set_defaults()

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

    def _on_top_tab_changed(self, index: int) -> None:  # on_change: prompts save when leaving Member Properties with unsaved changes
        if index < 0:
            return

        previous = getattr(self, "_last_top_tab_index", 0)
        if previous == index:
            return

        leaving_member_properties = (
            previous == self.tabs.indexOf(getattr(self, "section_properties_tab", None))
        )
        if leaving_member_properties:
            try:
                if hasattr(self, "section_properties_tab") and hasattr(self.section_properties_tab, "has_unsaved_changes"):
                    if self.section_properties_tab.has_unsaved_changes():
                        CustomMessageBox(
                            title="Unsaved Inputs",
                            text="Please save Member Properties before switching tabs.",
                            buttons=["OK"],
                            dialogType=MessageBoxType.Warning,
                        ).exec()
                        prev = self.tabs.blockSignals(True)
                        self.tabs.setCurrentIndex(previous)
                        self.tabs.blockSignals(prev)
                        return

                if hasattr(self, "section_properties_tab") and hasattr(self.section_properties_tab, "save_properties"):
                    self._last_saved_data = self.section_properties_tab.save_properties() or {}
            except Exception:
                pass

        self._last_top_tab_index = index

    # ── Dialog Persistence ───────────────────────────────────────────────────────

    def _save_inputs(self):  # on_change: validates all tabs then commits working_input_dict and emits CAD update signal
        saved = {}
        """
        Save additional inputs.
        Validate all fields first.
        If errors exist -> show popup and DO NOT close dialog.
        """
        errors = []

        for tab in [self.loading_tab]:
            if hasattr(tab, "validate_tab"):
                tab_errors = tab.validate_tab()
                if tab_errors:
                    errors.extend(tab_errors)

        if errors:
            self._show_validation_errors(errors)
            return

        self.saved_values.clear()
        self._collect_all_values()

        saved = self.saved_values.copy()

        tabs = [
            getattr(self, "typical_section_tab", None),
            getattr(self, "section_properties_tab", None),
            getattr(self, "loading_tab", None),
            getattr(self, "support_tab", None),
            getattr(self, "design_options_tab", None),
            getattr(self, "design_options_cont_tab", None),
        ]

        for tab in tabs:
            if not tab:
                continue
            if hasattr(tab, "save_values"):
                saved.update(tab.save_values() or {})
            if hasattr(tab, "save_properties"):
                saved.update(tab.save_properties() or {})

        self._last_saved_data = saved

        CustomMessageBox(
            title="Saved",
            text="Inputs saved successfully.",
            buttons=["OK"],
            dialogType=MessageBoxType.Success,
        ).exec()

        self.default_input_dict.update(self.working_input_dict)
        self.update_template_page_2d_cad.emit(self.typical_section_tab.cad_preview.params)

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

    def set_properties_data(self, data: dict) -> None:  # public API: restores all tab widgets from a previously saved data dict
        """
        @author: Faizan
        Restore previously saved UI and CAD properties across all tabs.
        """
        tabs = [
            getattr(self, "typical_section_tab", None),
            getattr(self, "section_properties_tab", None),
            getattr(self, "loading_tab", None),
            getattr(self, "support_tab", None),
            getattr(self, "design_options_tab", None),
            getattr(self, "design_options_cont_tab", None),
        ]

        for tab in tabs:
            if not tab:
                continue
            if hasattr(tab, "restore_values"):
                try:
                    tab.restore_values(data)
                except Exception:
                    pass
            if hasattr(tab, "restore_properties"):
                try:
                    tab.restore_properties(data)
                except Exception:
                    pass

        # Generic restore fallback
        try:
            for widget in self.findChildren(QWidget):
                name = widget.objectName()
                if not name or name not in data:
                    continue
                value = data[name]
                if isinstance(widget, QLineEdit):
                    widget.setText(str(value))
                elif isinstance(widget, QComboBox):
                    widget.setCurrentText(str(value))
                elif isinstance(widget, QCheckBox):
                    widget.setChecked(bool(value))
        except Exception:
            pass

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
        if hasattr(self, "typical_section_tab"):
            if hasattr(self.typical_section_tab, "cad_preview"):
                self.typical_section_tab.cad_preview.update_from_bridge_inputs(self.working_input_dict)

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
            current_object.addItem(f"Girder {i}", f"G{i}")
        idx = current_object.findText(current)
        current_object.setCurrentIndex(idx if idx >= 0 else 0)
        print(f"@@: Update Girder List")

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
        print(f"[SAVE_MEMBER_FIELDS] G{gi}.M{mi}")

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
        print(f"[LOAD] G{gi}.M{mi}")

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

    def _on_apply_exterior_clicked(self) -> None:  # on_change: applies current girder settings to first and last girders (stub)
        from osdagbridge.core.utils.common import KEY_MP_GD_SELECT_GIRDER
        girder_w = self.findChild(QWidget, KEY_MP_GD_SELECT_GIRDER)
        pass

    def _on_apply_interior_clicked(self) -> None:  # on_change: applies current girder settings to all interior girders (stub)
        from osdagbridge.core.utils.common import KEY_MP_GD_SEGMENT_TABLE
        table = self.findChild(QWidget, KEY_MP_GD_SEGMENT_TABLE)
        pass

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

        return {
            KEY_MP_GIRDER_MASS:                str(section.mass_per_meter_kg),
            KEY_MP_GIRDER_SECTIONAL_AREA:      str(section.area_cm2),
            KEY_MP_GIRDER_SECTIONAL_IZ:        str(section.moment_of_inertia_zz_cm4),
            KEY_MP_GIRDER_SECTIONAL_IY:        str(section.moment_of_inertia_yy_cm4),
            KEY_MP_GIRDER_RADIUS_GYRATION_Z:   str(section.radius_of_gyration_z_cm),
            KEY_MP_GIRDER_RADIUS_GYRATION_Y:   str(section.radius_of_gyration_y_cm),
            KEY_MP_GIRDER_ELASTIC_MODULUS_ZZ:  str(section.elastic_section_modulus_z_cm3),
            KEY_MP_GIRDER_ELASTIC_MODULUS_ZY:  str(section.elastic_section_modulus_y_cm3),
            KEY_MP_GIRDER_PLASTIC_MODULUS_ZUZ: str(section.plastic_section_modulus_z_cm3),
            KEY_MP_GIRDER_PLASTIC_MODULUS_ZUY: str(section.plastic_section_modulus_y_cm3),
            KEY_MP_GIRDER_TORSION_CONSTANT_IT: str(section.torsion_constant_cm4),
            KEY_MP_GIRDER_WARPING_CONSTANT_IW: str(section.warping_constant_cm6),
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

        # Outputs are in SI metres; convert to cm-based display units
        return {
            KEY_MP_GIRDER_MASS:                f"{result['Mass']:.4f}",
            KEY_MP_GIRDER_SECTIONAL_AREA:      f"{result['Area']  * 1e4:.4f}",   # m²  → cm²
            KEY_MP_GIRDER_SECTIONAL_IZ:        f"{result['I_z']   * 1e8:.4f}",   # m⁴  → cm⁴
            KEY_MP_GIRDER_SECTIONAL_IY:        f"{result['I_y']   * 1e8:.4f}",   # m⁴  → cm⁴
            KEY_MP_GIRDER_RADIUS_GYRATION_Z:   f"{result['r_z']   * 1e2:.4f}",   # m   → cm
            KEY_MP_GIRDER_RADIUS_GYRATION_Y:   f"{result['r_y']   * 1e2:.4f}",   # m   → cm
            KEY_MP_GIRDER_ELASTIC_MODULUS_ZZ:  f"{result['Z_ez']  * 1e6:.4f}",   # m³  → cm³
            KEY_MP_GIRDER_ELASTIC_MODULUS_ZY:  f"{result['Z_ey']  * 1e6:.4f}",   # m³  → cm³
            KEY_MP_GIRDER_PLASTIC_MODULUS_ZUZ: f"{result['Z_pz']  * 1e6:.4f}",   # m³  → cm³
            KEY_MP_GIRDER_PLASTIC_MODULUS_ZUY: f"{result['Z_py']  * 1e6:.4f}",   # m³  → cm³
            KEY_MP_GIRDER_TORSION_CONSTANT_IT: f"{result['I_t']   * 1e8:.4f}",   # m⁴  → cm⁴
            KEY_MP_GIRDER_WARPING_CONSTANT_IW: f"{result['I_w']   * 1e12:.4f}",  # m⁶  → cm⁶
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

        if hasattr(self, "section_properties_tab") and hasattr(self.section_properties_tab, "set_girder_count"):
            self.section_properties_tab.set_girder_count(int(result.no_of_girders))

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

        # ---- Typical Section tab ----
        ts = self.typical_section_tab

        no_of_girders = self.findChild(QLineEdit, KEY_TS_NO_OF_GIRDERS)
        if no_of_girders is not None and no_of_girders.text():
            values[KEY_TS_NO_OF_GIRDERS] = int(float(no_of_girders.text()))

        girder_spacing = self.findChild(QLineEdit, KEY_TS_GIRDER_SPACING)
        if girder_spacing is not None and girder_spacing.text():
            values[KEY_TS_GIRDER_SPACING] = float(girder_spacing.text())

        deck_overhang = self.findChild(QLineEdit, KEY_TS_DECK_OVERHANG)
        if deck_overhang is not None and deck_overhang.text():
            values[KEY_TS_DECK_OVERHANG] = float(deck_overhang.text())

        if hasattr(ts, "deck_thickness") and ts.deck_thickness.text():
            values[KEY_TS_DECK_THICKNESS] = float(ts.deck_thickness.text())

        if hasattr(ts, "footpath_width") and ts.footpath_width.text():
            values[KEY_TS_FOOTPATH_WIDTH] = float(ts.footpath_width.text())

        if hasattr(ts, "footpath_thickness") and ts.footpath_thickness.text():
            values[KEY_TS_FOOTPATH_THICKNESS] = float(ts.footpath_thickness.text())

        wearing_material = ts._find_wearing_widget(KEY_WC_MATERIAL)
        if wearing_material:
            values[KEY_WC_MATERIAL] = wearing_material.currentText()

        wearing_thickness = ts._find_wearing_widget(KEY_WC_THICKNESS)
        if wearing_thickness and wearing_thickness.text():
            values[KEY_WC_THICKNESS] = float(wearing_thickness.text())

        wearing_density = ts._find_wearing_widget(KEY_WC_DENSITY)
        if wearing_density and wearing_density.text():
            values[KEY_WC_DENSITY] = float(wearing_density.text())

         # ---- Crash Barrier ----
        crash_barrier_type = ts._find_crash_barrier_widget(KEY_CB_TYPE)
        if crash_barrier_type:
            values["crash_barrier_type"] = crash_barrier_type.currentText()

        crash_barrier_width = ts._find_crash_barrier_widget(KEY_CB_WIDTH)
        if crash_barrier_width and crash_barrier_width.text():
            values[KEY_CB_WIDTH] = float(crash_barrier_width.text())

        crash_barrier_height = ts._find_crash_barrier_widget(KEY_CB_HEIGHT)
        if crash_barrier_height and crash_barrier_height.text():
            values["crash_barrier_height"] = float(crash_barrier_height.text())

        # ---- Railing ----
        railing_type = ts._find_railing_widget(KEY_RL_TYPE)
        if railing_type:
            values[KEY_RL_TYPE] = railing_type.currentText()

        railing_width = ts._find_railing_widget(KEY_RL_WIDTH)
        if railing_width and railing_width.text():
            values[KEY_RL_WIDTH] = float(railing_width.text())

        railing_height = ts._find_railing_widget(KEY_RL_HEIGHT)
        if railing_height and railing_height.text():
            values["railing_height"] = float(railing_height.text())

        if hasattr(ts, "railing_post_spacing") and ts.railing_post_spacing.text():
            values["railing_post_spacing"] = float(ts.railing_post_spacing.text())

        if hasattr(ts, "railing_rail_count") and ts.railing_rail_count.text():
            values["railing_rail_count"] = int(float(ts.railing_rail_count.text()))

        if hasattr(ts, "railing_post_dia") and ts.railing_post_dia.text():
            values["railing_post_dia"] = float(ts.railing_post_dia.text())

        if hasattr(ts, "railing_top_width") and ts.railing_top_width.text():
            values["railing_top_width"] = float(ts.railing_top_width.text())

        if hasattr(ts, "railing_bottom_width") and ts.railing_bottom_width.text():
            values["railing_bottom_width"] = float(ts.railing_bottom_width.text())

        # ---- Median ----
        median_type = ts._find_median_widget(KEY_MD_TYPE)
        if median_type:
            values[KEY_MD_TYPE] = median_type.currentText()

        median_width = ts._find_median_widget(KEY_MD_WIDTH)
        if median_width and median_width.text():
            values[KEY_MD_WIDTH] = float(median_width.text())

        if hasattr(ts, "median_kerb_height") and ts.median_kerb_height.text():
            values["median_kerb_height"] = float(ts.median_kerb_height.text())

        if hasattr(ts, "median_top_width") and ts.median_top_width.text():
            values["median_top_width"] = float(ts.median_top_width.text())

        if hasattr(ts, "median_bottom_width") and ts.median_bottom_width.text():
            values["median_bottom_width"] = float(ts.median_bottom_width.text())

        if hasattr(ts, "median_barrier_height") and ts.median_barrier_height.text():
            values["median_barrier_height"] = float(ts.median_barrier_height.text())

        if hasattr(ts, "median_post_height") and ts.median_post_height.text():
            values["median_post_height"] = float(ts.median_post_height.text())

        # ---- Cross bracing spacing (Section Properties tab) ----
        try:
            bracing_tab = self.section_properties_tab.cross_bracing_details_tab
            if hasattr(bracing_tab, "bracing_spacing") and bracing_tab.bracing_spacing.text():
                values[KEY_MP_CB_SPACING] = float(bracing_tab.bracing_spacing.text())
        except Exception:
            pass

        self._sync_member_properties_girder_count()

        return values

    def update_footpath_value(self, footpath_value):  # public API: propagates footpath configuration change to Typical Section tab and CAD preview
        """
        @author: Faizan
        Update the footpath configuration across UI and CAD preview.
        """
        self.footpath_value = footpath_value
        # Sync into the working dict so recalculate_girders sees the new n_footpaths.
        # default_input_dict shares the reference with template_page.input_dict,
        # which the input dock already updates — no need to touch it here.

        if self.working_input_dict is not None:
            self.working_input_dict[KEY_FOOTPATH] = footpath_value
        self.typical_section_tab.update_footpath_value(footpath_value)

    def update_project_location(self, location_data):  # public API: propagates project location change to temperature, seismic, and wind Loading sub-tabs
        if hasattr(self, "loading_tab"):
            if hasattr(self.loading_tab, "temperature_load_tab") and hasattr(self.loading_tab.temperature_load_tab, "update_project_location"):
                self.loading_tab.temperature_load_tab.update_project_location(location_data)
            if hasattr(self.loading_tab, "seismic_load_tab") and hasattr(self.loading_tab.seismic_load_tab, "update_project_location"):
                self.loading_tab.seismic_load_tab.update_project_location(location_data)
            if hasattr(self.loading_tab, "wind_load_tab") and hasattr(self.loading_tab.wind_load_tab, "update_project_location"):
                self.loading_tab.wind_load_tab.update_project_location(location_data)

    def set_member_properties_editable(self, editable: bool) -> None:  # public API: enables or disables all Member Properties fields
        self._member_properties_editable = bool(editable)
        if hasattr(self, "section_properties_tab") and self.section_properties_tab is not None:
            try:
                self.section_properties_tab.set_editable_mode(self._member_properties_editable)
            except Exception:
                pass

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

    def _sync_member_properties_girder_count(self) -> None:  # utility: pushes current girder count from Typical Section to Member Properties tab
        try:
            count_text = ""
            if hasattr(self, "typical_section_tab") and hasattr(self.typical_section_tab, "no_of_girders"):
                count_text = str(self.typical_section_tab.no_of_girders.text() or "").strip()
            if not count_text:
                return
            count = int(float(count_text))
            if hasattr(self, "section_properties_tab") and hasattr(self.section_properties_tab, "set_girder_count"):
                self.section_properties_tab.set_girder_count(count)
        except Exception:
            pass

    def _find_inner_tab_index(self, tab_widget, tab_name: str) -> int:  # utility: returns the index of an inner tab by its label text, or -1 if not found
        """
        @author: Faizan
        Return the index of an inner tab by its label, or -1 if not found.
        """
        for i in range(tab_widget.count()):
            if tab_widget.tabText(i).strip().lower() == tab_name.strip().lower():
                return i
        return -1
