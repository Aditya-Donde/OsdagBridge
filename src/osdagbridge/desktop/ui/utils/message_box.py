from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMessageBox


def style_message_box(box: QMessageBox) -> QMessageBox:
    """Apply a simple, native-like setup for QMessageBox across the desktop UI."""

    box.setOption(QMessageBox.DontUseNativeDialog, True)
    box.setWindowFlag(Qt.Sheet, False)
    box.setWindowFlag(Qt.Dialog, True)
    box.setTextFormat(Qt.PlainText)
    box.setStyleSheet(
        "QMessageBox QLabel { color: #000000; }"
        "QMessageBox QPushButton {"
        " background-color: #f0f0f0;"
        " color: #000000;"
        " font-weight: 400;"
        " border: 1px solid #b5b5b5;"
        " border-radius: 2px;"
        " padding: 4px 10px;"
        " min-width: 72px;"
        " }"
        "QMessageBox QPushButton:hover {"
        " background-color: #f0f0f0;"
        " color: #000000;"
        " border: 1px solid #b5b5b5;"
        " }"
        "QMessageBox QPushButton:pressed {"
        " background-color: #f0f0f0;"
        " color: #000000;"
        " border: 1px solid #b5b5b5;"
        " }"
    )

    text_label = box.findChild(QLabel, "qt_msgbox_label")
    if text_label is not None:
        text_label.setWordWrap(True)

    informative_label = box.findChild(QLabel, "qt_msgbox_informativelabel")
    if informative_label is not None:
        informative_label.setWordWrap(True)

    box.adjustSize()
    return box
