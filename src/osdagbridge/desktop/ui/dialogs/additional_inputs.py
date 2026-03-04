"""
Additional Inputs Widget for Highway Bridge Design
Provides detailed input fields for manual bridge parameter definition
"""
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
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style, create_action_button_bar
from osdagbridge.desktop.ui.dialogs.tabs.typical_section_details import TypicalSectionDetailsTab
from osdagbridge.desktop.ui.dialogs.tabs.optimizable_field import OptimizableField
from osdagbridge.desktop.ui.dialogs.tabs.section_properties_tab import SectionPropertiesTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.girder_details_tab import GirderDetailsTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.stiffener_details_tab import StiffenerDetailsTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.cross_bracing_details_tab import CrossBracingDetailsTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.end_diaphragm_details_tab import EndDiaphragmDetailsTab
from osdagbridge.desktop.ui.dialogs.tabs.custom_vehicle_dialog import CustomVehicleDialog
from osdagbridge.desktop.ui.dialogs.tabs.loading_tab import LoadingTab
from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import (
    SUPPORT_CONDITIONS_SCHEMA,
    DESIGN_OPTIONS_SCHEMA,
    DESIGN_OPTIONS_CONT_SCHEMA,
)

# =================================================================================
#   MAIN IMPLEMENTATION
# =================================================================================

class AdditionalInputs(QDialog):
    """Main dialog for Additional Inputs with tabbed interface"""
    
    def __init__(self, footpath_value="None", carriageway_width=7.5, parent=None):
        super().__init__(parent)
        self.setObjectName("AdditionalInputs")
        self.resize(1024, 720)
        self.setMinimumSize(900, 520)
        self.setSizeGripEnabled(True)
        self.footpath_value = footpath_value
        self.carriageway_width = carriageway_width
        self._member_properties_editable = True
        self._last_saved_data = {}  # Track last saved state
        self.init_ui()
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border: 1px solid #90AF13;
            }
        """)

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
        self.typical_section_tab = TypicalSectionDetailsTab(self.footpath_value, self.carriageway_width)
        self.tabs.addTab(self.typical_section_tab, "Typical Section Details")
        
        # Sub-Tab 2: Member Properties
        self.section_properties_tab = SectionPropertiesTab()
        self.tabs.addTab(self.section_properties_tab, "Member Properties")
        self.section_properties_tab.set_editable_mode(self._member_properties_editable)

        # Keep girder count in sync across tabs
        try:
            self.typical_section_tab.girder_count_changed.connect(self.section_properties_tab.set_girder_count)
        except Exception:
            pass
        
        # Sub-Tab 3: Loading
        self.loading_tab = LoadingTab()
        self.tabs.addTab(self.loading_tab, "Loading")
        
        # Sub-Tab 4: Support Conditions
        support_tab = self._build_support_conditions_tab()
        self.tabs.addTab(support_tab, "Support Conditions")
        
        # Sub-Tab 5: Analysis/Design Options
        design_options_tab = self._build_design_options_tab()
        self.tabs.addTab(design_options_tab, "Analysis/Design Options")
        
        # Sub-Tab 6: Design Options (Cont.)
        analysis_design_tab = self._build_design_options_cont_tab()
        self.tabs.addTab(analysis_design_tab, "Design Options (Cont.)")
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
                validator.setDecimals(places)
                validator.setNotation(QDoubleValidator.StandardNotation)

    def _normalize_numeric_texts(self, places=2):
        """Format any numeric QLineEdit text to the specified decimal places."""
        fmt = f"{{:.{places}f}}"
        for line_edit in self.findChildren(QLineEdit):
            text = line_edit.text().strip()
            if not text:
                continue
            try:
                val = float(text)
                line_edit.setText(fmt.format(val))
            except ValueError:
                continue

    def _create_schema_widget(self, field_def, field_width):
        field_type = field_def.get("type")
        widget = None

        if field_type == "combo":
            widget = QComboBox()
            widget.addItems(field_def.get("choices") or [])
            default = field_def.get("default")
            if default:
                widget.setCurrentText(str(default))
            widget.setFixedWidth(field_width)
        elif field_type == "checkbox":
            widget = QCheckBox(field_def.get("label", ""))
            widget.setChecked(bool(field_def.get("default", False)))
        else:
            widget = QLineEdit()
            default = field_def.get("default")
            if default is not None:
                widget.setText(str(default))
            validator_def = field_def.get("validator")
            if validator_def and validator_def.get("type") == "double_range":
                bottom = validator_def.get("bottom", 0.0)
                top = validator_def.get("top", 1e9)
                decimals = validator_def.get("decimals", 2)
                widget.setValidator(QDoubleValidator(bottom, top, decimals))
            placeholder = field_def.get("placeholder")
            if placeholder:
                widget.setPlaceholderText(placeholder)
            widget.setFixedWidth(field_width)

        if field_type != "checkbox":
            apply_field_style(widget)

        bind_name = field_def.get("bind")
        if bind_name:
            setattr(self, bind_name, widget)

        if field_def.get("id"):
            widget.setObjectName(field_def["id"])

        return widget

    def set_member_properties_design_mode(self, mode_str: str):
        if hasattr(self, "section_properties_tab") and hasattr(self.section_properties_tab, "set_design_mode"):
            self.section_properties_tab.set_design_mode(mode_str)

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

        # Other tabs: best-effort reset if supported.
        if current_widget is not None and hasattr(current_widget, "reset_defaults"):
            try:
                current_widget.reset_defaults()
                return
            except Exception:
                pass

        self._show_placeholder_message("Defaults")

    def _save_inputs(self):
        saved = {}
        try:
            if hasattr(self, "section_properties_tab") and hasattr(self.section_properties_tab, "save_properties"):
                saved.update(self.section_properties_tab.save_properties() or {})
        except Exception as exc:
            # If saving fails, the old code would never reach the confirmation popup.
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Critical)
            box.setWindowTitle("Save Failed")
            box.setText(f"Could not save inputs.\n\n{exc}")
            box.setStandardButtons(QMessageBox.Ok)
            box.exec()
            return

        # Store the saved data for later retrieval
        self._last_saved_data = saved
        
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
                    for text in group.get("items", []):
                        cb = QCheckBox(text)
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
                    col = 0
                    for inline_def in row_fields:
                        lbl = QLabel(inline_def.get("label", ""))
                        lbl.setStyleSheet(label_style)
                        grid.addWidget(lbl, row_index, col, Qt.AlignLeft | Qt.AlignVCenter)
                        widget = self._create_schema_widget(inline_def, inline_def.get("width", section_field_width))
                        grid.addWidget(widget, row_index, col + 1, Qt.AlignLeft)
                        col += 2
                    row_index += 1
                    continue

                field_type = field_def.get("type")
                if field_type == "checkbox":
                    widget = self._create_schema_widget(field_def, section_field_width)
                    grid.addWidget(widget, row_index, 0, 1, 2, Qt.AlignLeft)
                    row_index += 1
                    continue

                lbl = QLabel(field_def.get("label", ""))
                lbl.setStyleSheet(label_style)
                grid.addWidget(lbl, row_index, 0, Qt.AlignLeft | Qt.AlignVCenter)

                widget = self._create_schema_widget(field_def, section_field_width)
                grid.addWidget(widget, row_index, 1, Qt.AlignLeft)
                row_index += 1

            parent_layout.addLayout(grid)

    def _build_support_conditions_tab(self):
        """Build the Support Conditions tab using schema-driven sections."""
        widget = QWidget()
        widget.setStyleSheet("background-color: #f5f5f5;")

        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        card_style = "QFrame { border: 1px solid #b2b2b2; border-radius: 8px; background-color: #ffffff; }"
        heading_style = "font-size: 12px; font-weight: 700; color: #2b2b2b; background: transparent; border: none;"
        label_style = "font-size: 11px; color: #3a3a3a; background: transparent; border: none;"
        field_width = 160

        card = QFrame()
        card.setStyleSheet(card_style)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(12)

        self._build_sections_from_schema(
            card_layout,
            SUPPORT_CONDITIONS_SCHEMA.get("sections", []),
            heading_style,
            label_style,
            field_width,
        )

        card_layout.addStretch()
        main_layout.addWidget(card)
        main_layout.addStretch()

        return widget

    def _build_design_options_tab(self):
        """Build the Design Options tab matching reference design"""
        widget = QWidget()
        widget.setStyleSheet("background-color: #f5f5f5;")
        
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)
        card_style = "QFrame { border: 1px solid #b2b2b2; border-radius: 8px; background-color: #ffffff; }"
        label_style = "font-size: 11px; color: #3a3a3a; background: transparent; border: none;"
        heading_style = "font-size: 12px; font-weight: 700; color: #2b2b2b; background: transparent; border: none;"
        default_field_width = 150

        for card_schema in DESIGN_OPTIONS_SCHEMA.get("cards", []):
            card = QFrame()
            card.setStyleSheet(card_style)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 14, 16, 14)
            card_layout.setSpacing(10)

            card_title = card_schema.get("title")
            if card_title:
                title_lbl = QLabel(f"{card_title}:")
                title_lbl.setStyleSheet(heading_style)
                card_layout.addWidget(title_lbl)

            self._build_sections_from_schema(
                card_layout,
                card_schema.get("sections", []),
                heading_style,
                label_style,
                card_schema.get("field_width", default_field_width),
            )

            main_layout.addWidget(card)

        main_layout.addStretch()

        return widget

    def _build_design_options_cont_tab(self):
        """Build the Design Options (Cont.) tab to match provided layout"""
        widget = QWidget()
        widget.setStyleSheet("background-color: #f5f5f5;")
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: #f5f5f5;")
        main_layout = QVBoxLayout(scroll_content)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        label_style = "font-size: 11px; color: #333333; background: transparent; border: none;"
        heading_style = "font-size: 12px; font-weight: 700; color: #2b2b2b; background: transparent; border: none;"

        self._build_sections_from_schema(
            main_layout,
            DESIGN_OPTIONS_CONT_SCHEMA.get("sections", []),
            heading_style,
            label_style,
            140,
        )

        main_layout.addStretch()

        scroll.setWidget(scroll_content)
        
        outer_layout = QVBoxLayout(widget)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll)

        return widget

    def update_footpath_value(self, footpath_value):
        """Update footpath value across all tabs"""
        self.footpath_value = footpath_value
        self.typical_section_tab.update_footpath_value(footpath_value)

    def set_member_properties_editable(self, editable: bool) -> None:
        self._member_properties_editable = bool(editable)
        if hasattr(self, "section_properties_tab") and self.section_properties_tab is not None:
            try:
                self.section_properties_tab.set_editable_mode(self._member_properties_editable)
            except Exception:
                pass

    def _show_placeholder_message(self, action_name):
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Information)
        box.setWindowTitle("Coming soon")
        box.setText(f"{action_name} action not implemented yet.")
        box.setStandardButtons(QMessageBox.Ok)
        box.exec()

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
                        box = QMessageBox(self)
                        box.setIcon(QMessageBox.Warning)
                        box.setWindowTitle("Unsaved Inputs")
                        box.setText("Please save Member Properties before switching tabs.")
                        box.setStandardButtons(QMessageBox.Ok)
                        box.setDefaultButton(QMessageBox.Ok)
                        box.setWindowModality(Qt.ApplicationModal)
                        box.exec()
                        prev = self.tabs.blockSignals(True)
                        self.tabs.setCurrentIndex(previous)
                        self.tabs.blockSignals(prev)
                        return
            except Exception:
                pass

        self._last_top_tab_index = index
    
    def get_saved_data(self) -> dict:
        """Get the last saved properties data.
        
        Returns:
            Dictionary containing all saved properties including stiffener details.
        """
        return self._last_saved_data
    
    def set_properties_data(self, data: dict) -> None:
        """Restore properties data from a previous save.
        
        Args:
            data: Dictionary containing properties to restore.
        """
        if hasattr(self, "section_properties_tab") and hasattr(self.section_properties_tab, "restore_properties"):
            try:
                self.section_properties_tab.restore_properties(data)
            except Exception:
                pass
