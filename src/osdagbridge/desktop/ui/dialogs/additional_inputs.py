"""
Additional Inputs Widget for Highway Bridge Design
Provides detailed input fields for manual bridge parameter definition
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTabBar, QLabel, QLineEdit,
    QComboBox, QGroupBox, QFormLayout, QPushButton, QScrollArea,
    QCheckBox, QMessageBox, QSizePolicy, QSpacerItem, QStackedWidget,
    QFrame, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QDialog, QSizeGrip, QListView, QStyledItemDelegate
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QDoubleValidator, QIntValidator, QColor, QValidator

from osdagbridge.core.utils.common import *
from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style, create_action_button_bar
from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox, MessageBoxType
from osdagbridge.desktop.ui.dialogs.tabs.typical_section_details import TypicalSectionDetailsTab, show_warning
from osdagbridge.desktop.ui.dialogs.tabs.section_properties_tab import SectionPropertiesTab
from osdagbridge.desktop.ui.dialogs.tabs.loading_tab import LoadingTab
from osdagbridge.desktop.ui.dialogs.tabs.support_conditions_tab import SupportConditionsTab
from osdagbridge.desktop.ui.dialogs.tabs.design_options_tab import DesignOptionsTab
from osdagbridge.desktop.ui.dialogs.tabs.design_options_cont_tab import DesignOptionsContTab
from osdagbridge.desktop.ui.utils.custom_widgets import SmartCursorComboBoxView
from osdagbridge.desktop.ui.dialogs.tabs import schema_io
from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import (
    DESIGN_OPTIONS_SCHEMA,
    DESIGN_OPTIONS_CONT_SCHEMA,
)

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
        tabs = [
            getattr(self, "typical_section_tab", None),
            getattr(self, "section_properties_tab", None),
            getattr(self, "loading_tab", None),
            getattr(self, "support_tab", None),
            getattr(self, "design_options_tab", None),
            getattr(self, "design_options_cont_tab", None),
        ]

        for tab in tabs:
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

            # Unified collection
            if hasattr(tab, "collect_data"):
                values.update(tab.collect_data())
            
            # Legacy collection fallback
            if hasattr(tab, "save_values"):
                values.update(tab.save_values() or {})
            if hasattr(tab, "save_properties"):
                values.update(tab.save_properties() or {})

        self.saved_values.update(values)
    
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

        # Tab instances
        self.typical_section_tab = TypicalSectionDetailsTab(
            footpath_value=self.footpath_value,
            carriageway_width=self.carriageway_width,
            parent=self,
            initial_cad_state=self._initial_cad_state
        )
        self.section_properties_tab = SectionPropertiesTab(parent=self)
        self.loading_tab = LoadingTab(parent=self)
        self.support_tab = SupportConditionsTab(parent_dialog=self)
        self.design_options_tab = DesignOptionsTab(parent_dialog=self)
        self.design_options_cont_tab = DesignOptionsContTab(parent_dialog=self)

        self.tab_widget.addTab(self.typical_section_tab, "Typical Section Details")
        self.tab_widget.addTab(self.section_properties_tab, "Member Properties")
        self.tab_widget.addTab(self.loading_tab, "Loading")
        self.tab_widget.addTab(self.support_tab, "Support Conditions")
        self.tab_widget.addTab(self.design_options_tab, "Design Options")
        self.tab_widget.addTab(self.design_options_cont_tab, "Design Options (Cont.)")

        content_layout.addWidget(self.tab_widget)

        # Action buttons
        buttons = create_action_button_bar(
            self,
            on_save=self._save_inputs,
            on_reset=self._on_reset_clicked,
            on_cancel=self.reject
        )
        content_layout.addLayout(buttons)

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

        if res == QMessageBox.Yes:
            self.reset_defaults()

    def reset_defaults(self):
        tabs = [
            self.typical_section_tab,
            self.section_properties_tab,
            self.loading_tab,
            self.support_tab,
            self.design_options_tab,
            self.design_options_cont_tab,
        ]
        for tab in tabs:
            if hasattr(tab, "reset_defaults"):
                tab.reset_defaults()

    def get_saved_data(self) -> dict:
        return self._last_saved_data.copy()
    
    def set_properties_data(self, data: dict) -> None:
        if not data:
            return

        tabs = [
            self.typical_section_tab,
            self.section_properties_tab,
            self.loading_tab,
            self.support_tab,
            self.design_options_tab,
            self.design_options_cont_tab,
        ]

        for tab in tabs:
            if not tab:
                continue

            if hasattr(tab, "restore_data"):
                tab.restore_data(data)
            
            if hasattr(tab, "restore_values"):
                try: tab.restore_values(data)
                except Exception: pass
            if hasattr(tab, "restore_properties"):
                try: tab.restore_properties(data)
                except Exception: pass

        # Generic restore fallback for non-schema widgets
        try:
            for widget in self.findChildren(QWidget):
                name = widget.objectName()
                if not name or name not in data:
                    continue
                value = data[name]
                if isinstance(widget, QLineEdit) and not widget.isReadOnly():
                    widget.setText(str(value))
                elif isinstance(widget, QComboBox):
                    widget.setCurrentText(str(value))
                elif isinstance(widget, QCheckBox):
                    widget.setChecked(bool(value))
        except Exception:
            pass
