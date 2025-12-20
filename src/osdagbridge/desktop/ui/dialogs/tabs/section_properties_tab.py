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

        self.section_tabs.addTab(GirderDetailsTab(), "Girder Details")
        self.section_tabs.addTab(StiffenerDetailsTab(), "Stiffener Details")
        self.section_tabs.addTab(CrossBracingDetailsTab(), "Cross-Bracing Details")
        self.section_tabs.addTab(EndDiaphragmDetailsTab(), "End Diaphragm Details")

        main_layout.addWidget(self.section_tabs)

