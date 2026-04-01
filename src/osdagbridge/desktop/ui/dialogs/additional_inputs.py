"""
Additional Inputs Widget for Highway Bridge Design
Provides detailed input fields for manual bridge parameter definition
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTabBar, QLabel, QLineEdit,
    QComboBox, QGroupBox, QFormLayout, QPushButton, QScrollArea,
    QCheckBox, QMessageBox, QSizePolicy, QSpacerItem, QStackedWidget,
    QFrame, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QDialog, QSizePolicy, QSizeGrip, QListView, QStyledItemDelegate
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QDoubleValidator, QIntValidator, QColor, QValidator

from osdagbridge.core.utils.common import *
from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style, create_action_button_bar
from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox, MessageBoxType
from osdagbridge.desktop.ui.dialogs.tabs.typical_section_details import TypicalSectionDetailsTab, show_warning
from osdagbridge.desktop.ui.dialogs.tabs.section_properties_tab import SectionPropertiesTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.girder_details_tab import GirderDetailsTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.stiffener_details_tab import StiffenerDetailsTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.cross_bracing_details_tab import CrossBracingDetailsTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.end_diaphragm_details_tab import EndDiaphragmDetailsTab
from osdagbridge.desktop.ui.dialogs.tabs.custom_vehicle_dialog import CustomVehicleDialog
from osdagbridge.desktop.ui.dialogs.tabs.loading_tab import LoadingTab
from osdagbridge.desktop.ui.dialogs.tabs.support_conditions_tab import SupportConditionsTab
from osdagbridge.desktop.ui.dialogs.tabs.design_options_tab import DesignOptionsTab
from osdagbridge.desktop.ui.dialogs.tabs.design_options_cont_tab import DesignOptionsContTab
from osdagbridge.desktop.ui.utils.combobox_utils import SmartCursorComboBoxView





# =================================================================================
#   MAIN IMPLEMENTATION
# =================================================================================

class AdditionalInputs(QDialog):
    """Main dialog for Additional Inputs with tabbed interface"""
    
    def __init__(self, footpath_value="None", carriageway_width=7.5, parent=None, initial_cad_state=None):
        self._initial_cad_state = initial_cad_state or {}
        super().__init__(parent)
        self.setObjectName("AdditionalInputs")
        self.resize(1024, 720)
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
            self.loading_tab,
            self.support_tab,
            self.design_options_tab,
            self.design_options_cont_tab,
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

        # self.accept() 

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
    
    def get_saved_values(self):
        """Return the dictionary of saved values."""
        return self.saved_values.copy()

    # compatibility helper used elsewhere in codebase
    def get_all_values(self):
        """Alias to get_saved_values for older callers."""
        return self.get_saved_values()
    
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
        self.typical_section_tab = TypicalSectionDetailsTab(self.footpath_value, self.carriageway_width, initial_cad_state=self._initial_cad_state)
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
        self.loading_tab = LoadingTab()
        self.tabs.addTab(self.loading_tab, "Loading")
        
        # Sub-Tab 4: Support Conditions
        self.support_tab = SupportConditionsTab(self)
        self.tabs.addTab(self.support_tab, "Support Conditions")
        
        # Sub-Tab 5: Analysis/Design Options
        self.design_options_tab = DesignOptionsTab(self)
        self.tabs.addTab(self.design_options_tab, "Analysis/Design Options")
        
        # Sub-Tab 6: Design Options (Cont.)
        self.design_options_cont_tab = DesignOptionsContTab(self)
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
            KEY_NO_OF_GIRDERS,
            KEY_GIRDER_SPACING,
            KEY_DECK_OVERHANG,
            KEY_DECK_THICKNESS,
            KEY_FOOTPATH_WIDTH,
            KEY_FOOTPATH_THICKNESS,
            KEY_CROSS_BRACING_SPACING,
            KEY_WEARING_COAT_THICKNESS,
            KEY_WEARING_COAT_DENSITY,
            KEY_WEARING_COAT_MATERIAL,
        )

        values = {}

        # ---- Typical Section tab ----
        ts = self.typical_section_tab

        if hasattr(ts, "no_of_girders") and ts.no_of_girders.text():
            values[KEY_NO_OF_GIRDERS] = int(float(ts.no_of_girders.text()))

        if hasattr(ts, "girder_spacing") and ts.girder_spacing.text():
            values[KEY_GIRDER_SPACING] = float(ts.girder_spacing.text())

        if hasattr(ts, "deck_overhang") and ts.deck_overhang.text():
            values[KEY_DECK_OVERHANG] = float(ts.deck_overhang.text())

        if hasattr(ts, "deck_thickness") and ts.deck_thickness.text():
            values[KEY_DECK_THICKNESS] = float(ts.deck_thickness.text())

        if hasattr(ts, "footpath_width") and ts.footpath_width.text():
            values[KEY_FOOTPATH_WIDTH] = float(ts.footpath_width.text())

        if hasattr(ts, "footpath_thickness") and ts.footpath_thickness.text():
            values[KEY_FOOTPATH_THICKNESS] = float(ts.footpath_thickness.text())
            
        if hasattr(ts, "wearing_material"):
            values[KEY_WEARING_COAT_MATERIAL] = ts.wearing_material.currentText()
            
        if hasattr(ts, "wearing_thickness") and ts.wearing_thickness.text():
            values[KEY_WEARING_COAT_THICKNESS] = float(ts.wearing_thickness.text())

        if hasattr(ts, "wearing_density") and ts.wearing_density.text():
            values[KEY_WEARING_COAT_DENSITY] = float(ts.wearing_density.text())
            
         # ---- Crash Barrier ----
        if hasattr(ts, "crash_barrier_type"):
            values["crash_barrier_type"] = ts.crash_barrier_type.currentText()
            
        if hasattr(ts, "crash_barrier_width") and ts.crash_barrier_width.text():
            values["crash_barrier_width"] = float(ts.crash_barrier_width.text())

        if hasattr(ts, "crash_barrier_height") and ts.crash_barrier_height.text():
            values["crash_barrier_height"] = float(ts.crash_barrier_height.text())
            
        # ---- Railing ----
        if hasattr(ts, "railing_type"):
            values["railing_type"] = ts.railing_type.currentText()
            
        if hasattr(ts, "railing_height") and ts.railing_height.text():
            values["railing_height"] = float(ts.railing_height.text())
            
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
        if hasattr(ts, "median_type"):
            values["median_type"] = ts.median_type.currentText()
            
        if hasattr(ts, "median_width") and ts.median_width.text():
            values["median_width"] = float(ts.median_width.text())
        
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

    def apply_tab_visibility(self, footpath_value: str, include_median: str) -> None:
        """
        @author: Faizan
        Enable or disable Railing and Median sub-tabs based on user selections.

        - Railing tab is enabled only if footpath is present.
        - Median tab is enabled only if median is included.

        After updating tab visibility, the CAD cross-section preview is
        refreshed to reflect the changes immediately.
        """
        inner_tabs = self.typical_section_tab.input_tabs

        # Railing tab 
        railing_index = self._find_inner_tab_index(inner_tabs, "Railing")
        if railing_index >= 0:
            railing_enabled = (footpath_value != "None")
            inner_tabs.setTabEnabled(railing_index, railing_enabled)

        #  Median tab 
        median_index = self._find_inner_tab_index(inner_tabs, "Median")
        if median_index >= 0:
            median_enabled = (include_median != "No")
            inner_tabs.setTabEnabled(median_index, median_enabled)
        
        # Trigger CAD update to reflect visibility changes
        if hasattr(self.typical_section_tab, "_update_cad_preview"):
            self.typical_section_tab._update_cad_preview()
            


    def update_footpath_value(self, footpath_value):
        """
        @author: Faizan
        Update the footpath configuration across UI and CAD preview.

        Propagates the selected footpath value from the Input Dock to the
        Typical Section tab, ensuring the CAD cross-section preview updates
        accordingly (e.g., both sides, left only, or none).
        """
        self.footpath_value = footpath_value
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

    def _show_placeholder_message(self, action_name):
        CustomMessageBox(
            title="Coming soon",
            text=f"{action_name} action not implemented yet.",
            buttons=["OK"],
            dialogType=MessageBoxType.Information,
        ).exec()

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