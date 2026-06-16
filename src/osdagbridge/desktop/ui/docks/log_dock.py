"""
Log dock widget for Osdag GUI.
Displays log messages and status updates.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel, QApplication
from PySide6.QtCore import Qt, QDateTime

from osdagbridge.core.utils.logger import bridge_logger


class LogDock(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Ensures automatic deletion when closed
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setObjectName("logs_dock")
        self.init_ui()
        # Register with the singleton logger so log messages arrive in real time
        bridge_logger.add_callback(self.append_log)

    def closeEvent(self, event):
        # Deregister callback when the dock is closed to prevent stale references
        bridge_logger.remove_callback(self.append_log)
        super().closeEvent(event)

    def init_ui(self):
        # Create layout for the log dock
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 0)
        layout.setSpacing(0)

        # Create a top strip for "Log Window"
        self.log_window_title = QLabel("Log Window")
        self.log_window_title.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.log_window_title)

        # Create log display area
        self.log_display = QTextEdit()
        self.log_display.setObjectName("textEdit")
        self.log_display.setReadOnly(True)
        self.log_display.setOverwriteMode(True)
        layout.addWidget(self.log_display)

        # Add init log text matching
        self.append_log(
            f"[{QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')}] Log initialized",
            "info",
        )

        self.setLayout(layout)
        self.show()  # Show init text

    def append_log(self, message, log_level="info"):
        """Append a message to the log display with specified color."""
        if log_level == "progress":
            try:
                pct = int(message.replace("__progress__", ""))
                if pct == 0:
                    self.log_window_title.setText("Log Window")
                    self.log_display.verticalScrollBar().setValue(
                        self.log_display.verticalScrollBar().maximum()
                    )
                elif pct >= 100:
                    self.log_window_title.setText("Log Window  –  Complete (100%)")
                else:
                    self.log_window_title.setText(f"Log Window  –  Analysing… {pct}%")
            except ValueError:
                pass
            QApplication.processEvents()
            return

        if log_level == "error":
            color = "#FF0000"  # Red for errors
        elif log_level == "info" or log_level == "stdout_print":
            color = "#A6A6A6"  # Black/Grey for info
        elif log_level == "success":
            color = "#008000"  # Green for success
        elif log_level == "warning":
            color = "#FFA500"  # Orange for warnings
        else:
            color = "#A6A6A6"

        # Smart scroll down only if the user was already at the bottom (with a 15px tolerance)
        scrollbar = self.log_display.verticalScrollBar()
        was_at_bottom = scrollbar.value() >= scrollbar.maximum() - 15

        # Escape HTML symbols to avoid rendering issues
        escaped_message = (
            message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        )
        formatted_message = (
            f'<span style="color: {color}; white-space: pre;">{escaped_message}</span>'
        )
        self.log_display.append(formatted_message)

        if was_at_bottom:
            scrollbar.setValue(scrollbar.maximum())
        QApplication.processEvents()
