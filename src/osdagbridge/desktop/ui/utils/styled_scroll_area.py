from PySide6.QtWidgets import QScrollArea, QSizePolicy
from PySide6.QtCore import Qt


class StyledScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.setStyleSheet("""
            QScrollArea {
                background: transparent;
                padding: 0px 5px;
                border-top: 1px solid #909090;
                border-bottom: 1px solid #909090;
            }

            QScrollArea QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 8px;
                margin-left: 2px;
            }

            QScrollArea QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 4px;
                min-height: 20px;
            }

            QScrollArea QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }

            QScrollArea QScrollBar::handle:vertical:pressed {
                background: #808080;
            }

            QScrollArea QScrollBar::add-line:vertical,
            QScrollArea QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }

            QScrollArea QScrollBar::add-page:vertical,
            QScrollArea QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
