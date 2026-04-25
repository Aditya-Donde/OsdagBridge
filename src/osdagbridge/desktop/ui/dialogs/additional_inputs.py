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
from osdagbridge.desktop.ui.dialogs.tabs.typical_section_details import show_warning
from osdagbridge.desktop.ui.dialogs.tabs.top_level_config import ADDITIONAL_INPUTS_TAB_CONFIG
from osdagbridge.desktop.ui.utils.custom_widgets import SmartCursorComboBoxView
from osdagbridge.desktop.ui.dialogs.tabs import schema_io

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
        """
        Save additional inputs.
        Validate all fields first.
        If errors exist -> show popup and DO NOT close dialog.
        """
        #this funciton now asks all tabs to validate themselves
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

        self.saved_values = dict(values)

    def _iter_top_tabs(self):
        for entry in ADDITIONAL_INPUTS_TAB_CONFIG:
            tab = getattr(self, entry["attr"], None)
            if tab is not None:
                yield tab
    
    def setupWrapper(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        # Title bar
        self.title_bar = CustomTitleBar(parent=self)
        self.title_bar.setTitle("Additional Inputs")
        main_layout.addWidget(self.title_bar)

        # Content area
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(10)

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #C2C7CB; border-radius: 4px; }
            QTabBar::tab { background: #f0f0f0; border: 1px solid #C2C7CB; padding: 8px 12px; }
            QTabBar::tab:selected { background: #ffffff; border-bottom-color: #ffffff; }
        """)

        # Build top-level tabs from config
        for entry in ADDITIONAL_INPUTS_TAB_CONFIG:
            widget = entry["factory"](self)
            setattr(self, entry["attr"], widget)
            self.tab_widget.addTab(widget, entry["title"])

        content_layout.addWidget(self.tab_widget)

        # Action buttons
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
            self.reset_defaults()

    def reset_defaults(self):
        for tab in self._iter_top_tabs():
            if hasattr(tab, "reset_defaults"):
                tab.reset_defaults()

    def get_saved_data(self) -> dict:
        return self._last_saved_data.copy()
    
    def set_properties_data(self, data: dict) -> None:
        if not data:
            return

        for tab in self._iter_top_tabs():
            if hasattr(tab, "restore_data"):
                tab.restore_data(data)

    def update_footpath_value(self, value) -> None:
        tab = getattr(self, "typical_section_tab", None)
        if tab is not None:
            fn = getattr(tab, "update_footpath_value", None)
            if callable(fn):
                fn(value)

    def set_member_properties_design_mode(self, mode: str) -> None:
        tab = getattr(self, "section_properties_tab", None)
        if tab is not None:
            fn = getattr(tab, "set_design_mode", None)
            if callable(fn):
                fn(mode)

    def get_all_values(self) -> dict:
        return dict(self.saved_values)
