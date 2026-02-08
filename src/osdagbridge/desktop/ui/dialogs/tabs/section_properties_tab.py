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

from osdagbridge.core.utils.common import *
from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.girder_details_tab import GirderDetailsTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.stiffener_details_tab import StiffenerDetailsTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.cross_bracing_details_tab import CrossBracingDetailsTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.end_diaphragm_details_tab import EndDiaphragmDetailsTab

class SectionPropertiesTab(QWidget):
    """Sub-tab for Section Properties with QTabWidget navigation like Loading tab."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Initialize styled tab navigation matching Loading subtabs."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.section_tabs = QTabWidget()
        self.section_tabs.setDocumentMode(True)
        self.section_tabs.setStyleSheet(
            "QTabWidget::pane { border: none; background: #f5f5f5; }"
            "QTabBar::tab { background: #e8e8e8; color: #4b4b4b; border: 1px solid #cfcfcf;"
            " border-bottom: none; padding: 8px 20px; margin-right: 2px; min-width: 120px;"
            " font-size: 11px; }"
            "QTabBar::tab:selected { background: #90AF13; color: #ffffff; font-weight: bold; }"
            "QTabBar::tab:!selected { margin-top: 2px; }"
        )

        self.girder_details_tab = GirderDetailsTab()
        self.stiffener_details_tab = StiffenerDetailsTab()
        self.cross_bracing_tab = CrossBracingDetailsTab()
        self.end_diaphragm_tab = EndDiaphragmDetailsTab()

        self.section_tabs.addTab(self.girder_details_tab, "Girder Details")
        self.section_tabs.addTab(self.stiffener_details_tab, "Stiffener Details")
        self.section_tabs.addTab(self.cross_bracing_tab, "Cross-Bracing Details")
        self.section_tabs.addTab(self.end_diaphragm_tab, "End Diaphragm Details")

        main_layout.addWidget(self.section_tabs)

    def set_girder_count(self, count):
        if hasattr(self, "girder_details_tab") and hasattr(self.girder_details_tab, "set_girder_count"):
            self.girder_details_tab.set_girder_count(count)

    def reset_defaults(self):
        if hasattr(self, "girder_details_tab") and hasattr(self.girder_details_tab, "reset_defaults"):
            self.girder_details_tab.reset_defaults()
        if hasattr(self, "cross_bracing_tab") and hasattr(self.cross_bracing_tab, "reset_defaults"):
            self.cross_bracing_tab.reset_defaults()

    def save_properties(self):
        data = {}
        if hasattr(self, "girder_details_tab") and hasattr(self.girder_details_tab, "collect_data"):
            data["girder_details"] = self.girder_details_tab.collect_data()
        if hasattr(self, "cross_bracing_tab") and hasattr(self.cross_bracing_tab, "collect_data"):
            data["cross_bracing"] = self.cross_bracing_tab.collect_data()
        return data
