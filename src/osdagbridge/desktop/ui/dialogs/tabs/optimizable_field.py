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

class OptimizableField(QWidget):
    """Widget that allows selection between Optimized/Customized/All modes with input field"""

    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(8)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(VALUES_OPTIMIZATION_MODE)
        self.mode_combo.setMinimumWidth(140)
        self.mode_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.input_field = QLineEdit()
        self.input_field.setEnabled(False)
        self.input_field.setVisible(False)
        self.input_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.layout.addWidget(self.mode_combo)
        self.layout.addWidget(self.input_field)

        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        self.on_mode_changed(self.mode_combo.currentText())

    def on_mode_changed(self, text):
        """Enable/disable input field based on selection"""
        if text in ("Optimized", "All", "NA"):
            self.input_field.setEnabled(False)
            self.input_field.clear()
            self.input_field.setVisible(False)
        else:
            self.input_field.setEnabled(True)
            self.input_field.setVisible(True)

    def get_value(self):
        """Returns tuple of (mode, value)"""
        return (self.mode_combo.currentText(), self.input_field.text())

