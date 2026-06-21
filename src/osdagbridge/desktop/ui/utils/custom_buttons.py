"""
Custom button widgets for Osdag GUI.
Includes menu and action buttons with custom styles.
"""
from PySide6.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QApplication, QGridLayout,
    QLabel, QMainWindow, QSizePolicy, QFrame
)
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtCore import Qt, Signal, QSize, QEvent, QRect, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QIcon, QPainter
from osdagbridge.desktop.ui.utils.custom_cursors import pointing_hand_cursor

class DockCustomButton(QPushButton):
    def __init__(self, text: str, icon_path: str, parent=None):
        super().__init__(parent)
        self.setCursor(pointing_hand_cursor())
        self.setObjectName("dock_custom_button")
        self.setStyleSheet("""
            QPushButton {
                background-color: #90AF13;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7a9a12;
            }
        """)

        # Layout for icons and text
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(0)

        # Left icon
        left_icon = QSvgWidget()
        left_icon.load(icon_path)
        left_icon.setFixedSize(18, 18)
        left_icon.setObjectName("button_icon")
        left_icon.setStyleSheet("""
            QSvgWidget {
                background: transparent;
            }
        """)
        layout.addWidget(left_icon)

        # Center text
        text_label = QLabel(text)
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setObjectName("button_label")
        text_label.setStyleSheet("""
            QLabel {
                background: transparent;
                color: white;
            }
        """)
        layout.addWidget(text_label)

        layout.setAlignment(Qt.AlignVCenter)
        self.setLayout(layout)
        
        # Calculate minimum width to prevent overlap
        text_width = text_label.sizeHint().width()
        icon_width = 18
        margins = layout.contentsMargins().left() + layout.contentsMargins().right()
        padding = 20
        min_width = text_width + icon_width + margins + padding
        self.setMinimumWidth(min_width)