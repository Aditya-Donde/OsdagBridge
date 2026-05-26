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
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.typical_section.typical_section_details import TypicalSectionDetailsTab
from osdagbridge.desktop.ui.dialogs.tabs.section_properties_tab import SectionPropertiesTab
from osdagbridge.desktop.ui.utils.custom_widgets import SmartCursorComboBoxView
from osdagbridge.desktop.ui.dialogs.additional_input.common_ui_builder import UIBuilder
from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import (
    DESIGN_OPTIONS_SCHEMA,
    DESIGN_OPTIONS_CONT_SCHEMA,
    SUPPORT_CONDITIONS_SCHEMA,
)

# =================================================================================
#   MAIN IMPLEMENTATION
# =================================================================================

class AdditionalInputs(QDialog):
    """Main dialog for Additional Inputs with tabbed interface"""
    
    update_template_page_2d_cad = Signal(dict)
    
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
    
    def set_input_dictionary(self, input_dict: dict):
        # -- Master input_dict reference (never mutated until Save) ------------------

        # Input dictionary treated as defaults for current scenario
        self.default_input_dict = input_dict
        # Work temporarily on a copy of default dictionary
        self.working_input_dict = deepcopy(input_dict)

        # Update Typical-section sub-tab activate/deactivate state
        self.typical_section_tab._sync_tab_active_states()

        # Populate defaults for deck-details text fields from the dict (widgets start empty)
        self._populate_deck_detail_fields(input_dict)

        # Populate schema-driven tabs (Support Conditions, Design Options, etc.)
        self._populate_schema_tab_fields(input_dict)

        self.typical_section_tab.apply_current_selection_defaults()
        self.default_input_dict.update(self.working_input_dict)

    def _populate_schema_tab_fields(self, input_dict: dict) -> None:
        """Push input_dict values into schema-driven tabs (Support, Design Options, etc.)."""
        tabs_to_populate = [
            getattr(self, "support_tab", None),
            getattr(self, "design_options_tab", None),
            getattr(self, "design_options_cont_tab", None),
        ]

        if hasattr(self, "typical_section_tab") and hasattr(self.typical_section_tab, "_tab_widgets"):
            tabs_to_populate.extend(self.typical_section_tab._tab_widgets.values())

        for tab in tabs_to_populate:
            if not tab:
                continue
            for widget in tab.findChildren(QWidget):
                name = widget.objectName()
                if not name or name not in input_dict:
                    continue
                value = input_dict[name]
                if value is None:
                    continue
                if isinstance(widget, QLineEdit):
                    widget.blockSignals(True)
                    widget.setText(str(value))
                    widget.blockSignals(False)
                elif isinstance(widget, QComboBox):
                    widget.blockSignals(True)
                    widget.setCurrentText(str(value))
                    widget.blockSignals(False)
                elif isinstance(widget, QCheckBox):
                    widget.blockSignals(True)
                    widget.setChecked(bool(value))
                    widget.blockSignals(False)

    def _populate_deck_detail_fields(self, input_dict: dict) -> None:
        """Push deck-detail values from input_dict into the Deck Details widgets."""
        ts = self.typical_section_tab

        def _set_text(key, fmt):
            val = input_dict.get(key)
            widget = ts.findChild(QWidget, key)
            if widget is not None and val is not None:
                try:
                    text = fmt.format(float(val))
                except (TypeError, ValueError):
                    text = str(val)
                widget.blockSignals(True)
                widget.setText(text)
                widget.blockSignals(False)

        # Populate structural values first to ensure they are present before any signals activate
        _set_text(KEY_TS_GIRDER_SPACING, "{:.2f}")
        _set_text(KEY_TS_NO_OF_GIRDERS,  "{:.0f}")
        _set_text(KEY_TS_DECK_OVERHANG,  "{:.2f}")
        _set_text(KEY_TS_OVERALL_WIDTH,  "{:.2f}")

        # Populate secondary deck values
        _set_text(KEY_TS_DECK_THICKNESS,     "{:.0f}")
        _set_text(KEY_TS_FOOTPATH_WIDTH,     "{:.2f}")
        _set_text(KEY_TS_FOOTPATH_THICKNESS, "{:.0f}")

        # Sync downstream girder count after primary fields are populated
        try:
            n_text = ts.no_of_girders.text() if hasattr(ts, "no_of_girders") else ""
            if n_text:
                ts.girder_count_changed.emit(int(float(n_text)))
        except (ValueError, TypeError):
            pass

    #-------------Field Change Handling and Validation Logic-Start-------------------------
    def _on_field_edited(self, key: str, widget: QLineEdit | str | dict):
        """
        Called on editingFinished (QLineEdit) or currentTextChanged (QComboBox).
        - QComboBox: always valid, skip validation, update dict + CAD.
        - QLineEdit: hard validation — corrects widget + input_dict if invalid, shows popup.
        """
        # QComboBox passes str directly via currentTextChanged
        if isinstance(widget, str):
            self._update_input_dict(key, widget)
            self._update_additional_input_cad()
            return
        
        # TYPE_BOUND_BTN passes dict result directly
        if isinstance(widget, dict):
            self._update_input_dict(key, widget)
            return
        
        # TYPE_CHECKBOX passes bool
        if isinstance(widget, bool):
            self._update_input_dict(key, widget)
            self._update_additional_input_cad()
            return
        
        # TYPE_LOAD_COMBINATION passes list of dicts
        if isinstance(widget, list):
            self._update_input_dict(key, widget)
            return
        
        # Rest of code mainly triggers QLineEdit
        current_text = widget.text().strip()

        # Update dict first so validator reads the latest value
        self._update_input_dict(key, current_text)

        # hard-validation start ----------------------
        result = self.validator.validate_additional_inputs(key, self.working_input_dict)
        print(f"@@: After Edited Validation result for {key} = {result}")
        if result is not None:
            corrected, message = result
            CustomMessageBox(
                title="Input Error",
                text=message,
                dialogType=MessageBoxType.Warning
            ).exec()
            # update to valid text
            widget.blockSignals(True)
            widget.setText(str(corrected))
            widget.blockSignals(False)
            self._update_input_dict(key, str(corrected))
        # hard-validation end ----------------------

        # Always update CAD after hard validation
        self._update_additional_input_cad()

    def _on_field_editing(self, current_text: str, key: str):
        """
        Soft validation — called on textChanged (while typing).
        No popups, no corrections. Updates dict + CAD only when valid.
        """

        if not current_text.strip():
            # Empty — fall back to default silently
            self._update_input_dict(key, "")
            self._update_additional_input_cad()
            return

        # Update dict first so validator reads the latest value
        self._update_input_dict(key, current_text)

        # soft-validation start ----------------------
        result = self.validator.validate_additional_inputs(key, self.working_input_dict)
        if result is not None:
            # Still typing, value not valid yet — skip CAD update
            return
        # soft-validation end ------------------------

        # Valid - update CAD
        self._update_additional_input_cad()

    # Update input_dictionary on value changed
    def _update_input_dict(self, key: str, value: str):
        """
        Called on every widget value change.
        If value is empty/None, falls back to default_input_dict which is the initial dictionary.
        Updates working_input_dict and notifies listeners.
        """

        # If Empty or None Value then set the default
        print(f"@@Update Dict: key={key}, value={value}, default: {self.default_input_dict.get(key)}")
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
        print(f"@@Final: {self.working_input_dict[key]}")

    def _update_additional_input_cad(self):
        """
        Collect inputs from InputDock and update 2D-CAD
        """
        print(f"@@: Updating 2D-CAD")
        # Apply state to CAD UI & Update Cad-State
        if hasattr(self, "typical_section_tab"):
            if hasattr(self.typical_section_tab, "cad_preview"):
                self.typical_section_tab.cad_preview.update_from_bridge_inputs(self.working_input_dict)

    #-------------Field Change Handling and Validation Logic-End-------------------------
    
    def _save_inputs(self):
        saved = {}
        """
        Save additional inputs.
        Validate all fields first.
        If errors exist -> show popup and DO NOT close dialog.
        """
        #calls validate_widgets_in_tabs which validates all the fields in the following tabs
        
        #this funciton now asks all tabs to validate themselves
        errors = []

        for tab in [
            self.loading_tab
        ]:
            if hasattr(tab, "validate_tab"):
                tab_errors = tab.validate_tab()
                if tab_errors:
                    errors.extend(tab_errors)

        if errors:
            self._show_validation_errors(errors)
            return
        # If everything is valid → continue saving

        #clears dictionary before saving new values
        self.saved_values.clear()
        #collects all inputs
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

            # save simple UI values
            if hasattr(tab, "save_values"):
                saved.update(tab.save_values() or {})

            # save complex data structures
            if hasattr(tab, "save_properties"):
                saved.update(tab.save_properties() or {})

        self._last_saved_data = saved

        CustomMessageBox(
            title="Saved",
            text="Inputs saved successfully.",
            buttons=["OK"],
            dialogType=MessageBoxType.Success,
        ).exec()

        # Update Main Dictionary with Working Dictionary
        self.default_input_dict.update(self.working_input_dict)

        # Send Signal to Update 2D-CAD in Template Page
        self.update_template_page_2d_cad.emit(self.typical_section_tab.cad_preview.params)

    def _show_validation_errors(self, errors):
        message = "\n\n".join(f"• {err}" for err in errors)

        CustomMessageBox(
            title="Validation Errors",
            text=message,
            buttons=["OK"],
            dialogType=MessageBoxType.Warning,
        ).exec()
    
    def _collect_all_values(self):
        """Collect values from all bound widgets across all tabs."""
        # Qt's findChildren doesn't accept a tuple; grab all QWidget descendants and filter

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
    
    def setupWrapper(self):
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
    
    def style_input_field(self, field):
        apply_field_style(field)

    def init_ui(self):
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
        self.section_properties_tab = SectionPropertiesTab()
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
        self.defaults_button.clicked.connect(self._apply_defaults)
        self.save_button.clicked.connect(self._save_inputs)
        main_layout.addSpacing(6)
        main_layout.addWidget(action_bar)
        
        # Enforce max 2 decimal places for all double validators in the dialog
        self._enforce_decimal_places(2)
        # Normalize existing numeric text to 2 decimal places for consistent display
        self._normalize_numeric_texts(2)

    # Update CAD Method for Support Conditions Tab Drawing
    # This function is implicitly connected using Schema of the Tab
    def _update_support_detail_cad(self):
        from osdagbridge.desktop.ui.dialogs.tabs.drawings.support_detail_cad import SupportDetailCADWidget
        widget = self.findChild(SupportDetailCADWidget, KEY_SC_RIGHT_CAD)
        if widget is None:
            return
        value = self.working_input_dict.get(KEY_SC_BEARING_LENGTH, "400")
        try:
            value = float(value)
        except (ValueError, TypeError):
            value = 400.0
        widget.update_params({"bearing_length": value})
    
    # Click event for "Add Custom Vehicle" button in Live Load Sub-Tab in Loading Tab
    def _on_add_custom_vehicle(self, existing=None, widget=None):
        from osdagbridge.desktop.ui.dialogs.tabs.custom_vehicle_dialog import CustomVehicleDialog
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

    # Click event for "Add Custom Combination" button in Load Combination Sub-Tab in Loading Tab
    def _on_add_custom_combination(self, existing=None, widget=None):
        from osdagbridge.desktop.ui.dialogs.tabs.load_combination_dialog import LoadCombinationDialog
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
        
    def _enforce_decimal_places(self, places=2):
        """Force all QDoubleValidator instances in this dialog to the given decimal places."""
        for line_edit in self.findChildren(QLineEdit):
            validator = line_edit.validator()
            if isinstance(validator, QDoubleValidator):
                # Only enforce standard notation decimals if it's not explicitly scientific
                if validator.notation() != QDoubleValidator.ScientificNotation:
                    validator.setDecimals(places)
                    validator.setNotation(QDoubleValidator.StandardNotation)

    def _normalize_numeric_texts(self, places=2):
        """Format any numeric QLineEdit text to the specified decimal places."""
        fmt = f"{{:.{places}f}}"
        for line_edit in self.findChildren(QLineEdit):
            # Skip fields with scientific validators
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

    def _normalize_member_properties_design_mode(self, mode_str: str) -> str:
        """Map upstream design labels to Member Properties supported values."""
        value = str(mode_str or "").strip().lower()
        if value in {"custom", "customized"}:
            return "Custom"
        if value in {"optimized", "optimised"}:
            return "Optimized"
        return "Optimized"

    def _sync_member_properties_girder_count(self) -> None:
        """Push current girder count from Typical Section to Member Properties."""
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

    def _create_schema_widget(self, field_def, field_width):
        field_type = field_def.get("type")
        widget = None

        if field_type == "combo":
            widget = QComboBox()
            choices = field_def.get("choices") or []

            for choice in choices:
                widget.addItem(choice)

            # apply enabled/disabled states if specified
            enabled_list = field_def.get("enabled_choices")
            if enabled_list is not None:
                # after adding items we can disable the others
                for idx in range(widget.count()):
                    text = widget.itemText(idx)
                    if text not in enabled_list:
                        item = widget.model().item(idx)
                        if item is not None:
                            item.setEnabled(False)
                            # grey out the text
                            item.setForeground(Qt.gray)

            default = field_def.get("default")
            if default:
                widget.setCurrentText(str(default))

            widget.setFixedWidth(field_width)
            # use custom view with smart cursor handling for disabled items
            try:
                custom_view = SmartCursorComboBoxView()
                widget.setView(custom_view)
            except Exception:
                pass

        elif field_type == "checkbox":
            widget = QCheckBox(field_def.get("label", ""))
            widget.setChecked(bool(field_def.get("default", False)))

        elif field_type == "label":
            widget = QLabel(field_def.get("default", ""))
            widget.setFixedWidth(field_width)

        elif field_type == "button":
            widget = QPushButton(field_def.get("text", "Set Bounds"))

            widget.setFixedHeight(28)   
            widget.setFixedWidth(field_width)  

            widget.setCursor(Qt.PointingHandCursor)

            widget.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff;
                    border: 1px solid #b2b2b2;
                    border-radius: 6px;
                    padding: 4px;
                }
                QPushButton:hover {
                    background-color: #e6e6e6;
                    color: #2b2b2b;
                }
                QPushButton:pressed {
                    background-color: #d0d0d0;
                }
            """)     

        elif field_type in ["line", "number"]:
            widget = QLineEdit()

            default = field_def.get("default")
            if default is not None:
                widget.setText(str(default))
                widget.setProperty("default_value", default)
            validator_def = field_def.get("validator")

            if validator_def:
                if validator_def.get("type") == "double_range":
                    bottom = validator_def.get("bottom", 0.0)
                    top = validator_def.get("top", 1e9)
                    decimals = validator_def.get("decimals", 2)
                    validator = QDoubleValidator(bottom, top, decimals)
                    widget.setValidator(validator)
                    # placeholder showing range
                    widget.setPlaceholderText(f"{bottom} - {top}")

                elif validator_def.get("type") == "int_range":
                    bottom = validator_def.get("bottom", 0)
                    top = validator_def.get("top", 1_000_000)
                    validator = QIntValidator(bottom, top)
                    widget.setValidator(validator)
                    widget.setPlaceholderText(f"{bottom} - {top}")

            widget.setFixedWidth(field_width)

        if field_type not in ["checkbox", "label"]:
            apply_field_style(widget)

        bind_name = field_def.get("bind")
        if bind_name:
            setattr(self, bind_name, widget)

        if field_def.get("id"):
            widget.setObjectName(field_def["id"])

        return widget

    def set_member_properties_design_mode(self, mode_str: str):
        normalized_mode = self._normalize_member_properties_design_mode(mode_str)
        if hasattr(self, "section_properties_tab") and hasattr(self.section_properties_tab, "set_design_mode"):
            self.section_properties_tab.set_design_mode(normalized_mode)

    def _apply_defaults(self):
        """Apply defaults only to the currently visible top-level tab.

        Important UX: within Member Properties, Defaults should only reset the
        currently active sub-tab (not the entire Member Properties area).
        """

        try:
            current_widget = self.tabs.currentWidget()
        except Exception:
            current_widget = None

        if current_widget is getattr(self, "typical_section_tab", None):
            if hasattr(self.typical_section_tab, "reset_defaults"):
                self.typical_section_tab.reset_defaults()
            return

        if current_widget is getattr(self, "section_properties_tab", None):
            # Member Properties: reset only active sub-tab.
            if hasattr(self.section_properties_tab, "reset_active_tab_defaults"):
                self.section_properties_tab.reset_active_tab_defaults()
            elif hasattr(self.section_properties_tab, "reset_defaults"):
                # Fallback to legacy behavior.
                self.section_properties_tab.reset_defaults()
            return

        if current_widget is getattr(self, "loading_tab", None):
            for i in range(self.loading_tab.load_tabs.count()):
                tab = self.loading_tab.load_tabs.widget(i)
                if hasattr(tab, "reset_defaults"):
                    tab.reset_defaults()
            return

        if current_widget is getattr(self, "support_tab", None):
            if hasattr(self.support_tab, "reset_defaults"):
                self.support_tab.reset_defaults()
            return

        if current_widget is getattr(self, "design_options_tab", None):
            if hasattr(self.design_options_tab, "reset_defaults"):
                self.design_options_tab.reset_defaults()
            return

        if current_widget is getattr(self, "design_options_cont_tab", None):
            if hasattr(self.design_options_cont_tab, "reset_defaults"):
                self.design_options_cont_tab.reset_defaults()
            return 
        # Confirm save to the user (requested behavior). Use an explicit message box
        # instance so it stays on top of the frameless dialog.
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Information)
        box.setWindowTitle("Saved")
        box.setText("Inputs saved successfully.")
        box.setStandardButtons(QMessageBox.Ok)
        box.setDefaultButton(QMessageBox.Ok)
        box.setWindowModality(Qt.ApplicationModal)
        box.exec()
        """
        Save additional inputs and close dialog.
        Data will be collected by template_page via get_all_values().
        """
        self.accept()
    
    
    def get_all_values(self):
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
            KEY_CROSS_BRACING_SPACING,
            KEY_WC_THICKNESS,
            KEY_WC_DENSITY,
            KEY_WC_MATERIAL,
        )

        values = {}

        # ---- Typical Section tab ----
        ts = self.typical_section_tab

        if hasattr(ts, "no_of_girders") and ts.no_of_girders.text():
            values[KEY_TS_NO_OF_GIRDERS] = int(float(ts.no_of_girders.text()))

        if hasattr(ts, "girder_spacing") and ts.girder_spacing.text():
            values[KEY_TS_GIRDER_SPACING] = float(ts.girder_spacing.text())

        if hasattr(ts, "deck_overhang") and ts.deck_overhang.text():
            values[KEY_TS_DECK_OVERHANG] = float(ts.deck_overhang.text())

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
                values[KEY_CROSS_BRACING_SPACING] = float(bracing_tab.bracing_spacing.text())
            
        except Exception:
            pass

        # Keep Member Properties member/pair dropdowns aligned with restored girder count.
        self._sync_member_properties_girder_count()

        return values

    def _build_sections_from_schema(self, parent_layout, sections, heading_style, label_style, field_width):
        for section in sections:
            title = section.get("title")
            section_field_width = section.get("field_width", field_width)

            checkbox_groups = section.get("checkbox_groups")
            if checkbox_groups:
                groups_layout = QHBoxLayout()
                groups_layout.setSpacing(20)

                for group in checkbox_groups:
                    box = QGroupBox(group.get("title", ""))
                    box.setStyleSheet(
                        "QGroupBox { border: 1px solid #b0b0b0; border-radius: 6px; margin-top: 12px; padding: 8px; background: #ffffff; }"
                        "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 12px; padding: 0 6px; background: #f5f5f5; font-weight: 600; font-size: 11px; color: #333333; }"
                    )
                    vbox = QVBoxLayout(box)
                    vbox.setContentsMargins(16, 24, 16, 16)
                    vbox.setSpacing(12)
                    checkboxes = []
                    default_checked = group.get("default_checked", False)

                    for text in group.get("items", []):
                        cb = QCheckBox(text)
                        cb.setChecked(default_checked)
                        cb.setStyleSheet("QCheckBox { font-size: 11px; color: #333333; background: transparent; spacing: 8px; }")
                        vbox.addWidget(cb)
                        checkboxes.append(cb)
                        

                    bind_name = group.get("bind")
                    if bind_name:
                        setattr(self, bind_name, checkboxes)

                    groups_layout.addWidget(box)

                if title:
                    title_lbl = QLabel(title)
                    title_lbl.setStyleSheet(heading_style)
                    parent_layout.addWidget(title_lbl)

                parent_layout.addLayout(groups_layout)
                continue

            if title:
                title_lbl = QLabel(title)
                title_lbl.setStyleSheet(heading_style)
                parent_layout.addWidget(title_lbl)

            grid = QGridLayout()
            grid.setContentsMargins(0, 8, 0, 0)
            grid.setHorizontalSpacing(12)
            grid.setVerticalSpacing(12)
            grid.setColumnMinimumWidth(0, 120)

            row_index = 0
            for field_def in section.get("fields", []):
                row_fields = field_def.get("row_fields")
                if row_fields:
                    row_layout = QHBoxLayout()
                    row_layout.setSpacing(8)  # reduce gap
                    row_layout.setContentsMargins(0, 0, 0, 0)

                    for i, inline_def in enumerate(row_fields):

                        if inline_def.get("type") == "label":
                            lbl = QLabel(inline_def.get("label", ""))
                            lbl.setStyleSheet(label_style)
                            row_layout.addWidget(lbl)

                            # Add extra spacing only after "Limit :"
                            if inline_def.get("after_spacing"):
                                row_layout.addSpacing(inline_def["after_spacing"])

                        else:
                            widget = self._create_schema_widget(
                                inline_def,
                                inline_def.get("width", section_field_width)
                            )
                            row_layout.addWidget(widget)

                    row_layout.addStretch()  # keep left aligned
                    parent_layout.addLayout(row_layout)
                    continue

                field_type = field_def.get("type")
                if field_type == "checkbox":
                    widget = self._create_schema_widget(field_def, section_field_width)
                    grid.addWidget(widget, row_index, 0, 1, 2, Qt.AlignLeft)
                    row_index += 1
                    continue

                lbl = QLabel(field_def.get("label", ""))
                lbl.setTextFormat(Qt.RichText)
                lbl.setStyleSheet(label_style)
                grid.addWidget(lbl, row_index, 0, Qt.AlignLeft | Qt.AlignVCenter)

                widget = self._create_schema_widget(field_def, section_field_width)
                # Create vertical container for error + field
                field_container = QVBoxLayout()
                field_container.setContentsMargins(0, 0, 0, 0)
                field_container.setSpacing(2)

                error_label = getattr(widget, "_error_label", None)
                if error_label is not None:
                    field_container.addWidget(error_label)

                field_container.addWidget(widget)

                container_widget = QWidget()
                container_widget.setLayout(field_container)

                grid.addWidget(container_widget, row_index, 1, Qt.AlignLeft)
                row_index += 1

            parent_layout.addLayout(grid)

    def _find_inner_tab_index(self, tab_widget, tab_name: str) -> int:
        """
        @author: Faizan
        Return the index of an inner tab by its label, or -1 if not found.
        """
        for i in range(tab_widget.count()):
            if tab_widget.tabText(i).strip().lower() == tab_name.strip().lower():
                return i
        return -1            

    def update_footpath_value(self, footpath_value):
        """
        @author: Faizan
        Update the footpath configuration across UI and CAD preview.

        Propagates the selected footpath value from the Input Dock to the
        Typical Section tab, ensuring the CAD cross-section preview updates
        accordingly (e.g., both sides, left only, or none).
        """
        self.footpath_value = footpath_value
        # Sync into the working dict so _resolve_layout sees the new n_footpaths.
        # default_input_dict shares the reference with template_page.input_dict,
        # which the input dock already updates — no need to touch it here.
        if self.working_input_dict is not None:
            self.working_input_dict[KEY_FOOTPATH] = footpath_value
        self.typical_section_tab.update_footpath_value(footpath_value)


    def update_project_location(self, location_data):
        """Update dependent tabs when project location changes"""
        if hasattr(self, "loading_tab"):
            if hasattr(self.loading_tab, "temperature_load_tab") and hasattr(self.loading_tab.temperature_load_tab, "update_project_location"):
                self.loading_tab.temperature_load_tab.update_project_location(location_data)
            
            if hasattr(self.loading_tab, "seismic_load_tab") and hasattr(self.loading_tab.seismic_load_tab, "update_project_location"):
                self.loading_tab.seismic_load_tab.update_project_location(location_data)
                
            if hasattr(self.loading_tab, "wind_load_tab") and hasattr(self.loading_tab.wind_load_tab, "update_project_location"):
                self.loading_tab.wind_load_tab.update_project_location(location_data)

    def set_member_properties_editable(self, editable: bool) -> None:
        self._member_properties_editable = bool(editable)
        if hasattr(self, "section_properties_tab") and self.section_properties_tab is not None:
            try:
                self.section_properties_tab.set_editable_mode(self._member_properties_editable)
            except Exception:
                pass

    def _on_top_tab_changed(self, index: int) -> None:
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
    
    def get_saved_data(self) -> dict:
        """Get the last saved properties data.
        
        Returns:
            Dictionary containing all saved properties including stiffener details.
        """
        return self._last_saved_data.copy()
    
    def set_properties_data(self, data: dict) -> None:
        """
        @author: Faizan
        Restore previously saved UI and CAD properties across all tabs.

        This method repopulates dialog fields (e.g., girder spacing, deck
        thickness, barrier/railing/median settings) using saved data so that
        the UI and CAD preview resume from the last known state.
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