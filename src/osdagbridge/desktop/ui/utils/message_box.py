from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMessageBox


def style_message_box(box: QMessageBox) -> QMessageBox:
    """Apply a compact, readable style for QMessageBox across the desktop UI."""

    box.setOption(QMessageBox.DontUseNativeDialog, True)
    box.setWindowFlag(Qt.Sheet, False)
    box.setWindowFlag(Qt.Dialog, True)
    box.setTextFormat(Qt.PlainText)
    box.setMinimumWidth(360)
    box.setMaximumWidth(560)
    box.setStyleSheet(
        "QMessageBox { background: #f3f3f3; }"
        "QMessageBox QLabel#qt_msgbox_label { color: #111111; font-size: 12px; }"
        "QMessageBox QLabel#qt_msgbox_informativelabel { color: #111111; font-size: 12px; }"
        "QMessageBox QDialogButtonBox { background: transparent; }"
        "QMessageBox QPushButton {"
        " min-width: 84px;"
        " min-height: 28px;"
        " padding: 4px 14px;"
        " background-color: #90AF13;"
        " color: #ffffff;"
        " font-weight: bold;"
        " border: 1px solid #7a9a12;"
        " border-radius: 4px;"
        " }"
        "QMessageBox QPushButton:hover {"
        " background-color: #7a9a12;"
        " border-color: #6b860f;"
        " }"
        "QMessageBox QPushButton:pressed {"
        " background-color: #6f8a11;"
        " border-color: #5d760d;"
        " }"
        "QMessageBox QPushButton:disabled {"
        " background-color: #d0d0d0;"
        " color: #666666;"
        " border-color: #d0d0d0;"
        " }"
    )

    text_label = box.findChild(QLabel, "qt_msgbox_label")
    if text_label is not None:
        text_label.setWordWrap(True)
        text_label.setMinimumWidth(320)
        text_label.setMaximumWidth(480)

    informative_label = box.findChild(QLabel, "qt_msgbox_informativelabel")
    if informative_label is not None:
        informative_label.setWordWrap(True)
        informative_label.setMinimumWidth(320)
        informative_label.setMaximumWidth(480)

    box.adjustSize()
    return box
