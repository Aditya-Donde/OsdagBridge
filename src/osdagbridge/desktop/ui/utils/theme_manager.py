"""
Theme Manager for OsdagBridge GUI.
Loads the light theme and persists UI preferences.
"""
from PySide6.QtCore import QSettings, QObject
from PySide6.QtCore import QFile, QTextStream
from PySide6.QtGui import QPalette, QColor


class ThemeManager(QObject):
    """Applies the application theme and stores UI preferences."""

    THEME_PATH = ":/themes/lightstyle.qss"

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.settings = QSettings("OsdagBridge", "OsdagBridge-Desktop")
        self.control_btn_pos = self.settings.value("control_btn_pos", "right")
        self.stylesheet = self._read_stylesheet()

    def set_always_close_all_tabs(self, always_close):
        """always_close: bool - whether to always close all tabs without asking."""
        self.settings.setValue("always_close_all_tabs", always_close)

    def get_always_close_all_tabs(self):
        """Return whether to always close all tabs without asking."""
        return self.settings.value("always_close_all_tabs", False, type=bool)

    def set_control_btn_pos(self, position):
        """Set control button position ('left' or 'right')."""
        if position not in ["left", "right"]:
            print(f"Invalid button position: {position}")
            return False

        self.control_btn_pos = position
        self.settings.setValue("control_btn_pos", position)
        print(f"Button position changed to: {position}")
        return True

    def is_control_btn_left(self):
        """Check if buttons are on the left."""
        return self.control_btn_pos == "left"

    def _read_stylesheet(self):
        """Read and cache the theme stylesheet."""
        file = QFile(self.THEME_PATH)
        if file.open(QFile.ReadOnly | QFile.Text):
            stream = QTextStream(file)
            stylesheet = stream.readAll()
            file.close()
            return stylesheet

        print(f"Failed to load theme from {self.THEME_PATH}")
        return ""

    def load_theme(self):
        """Apply the theme stylesheet and palette."""
        if not self.stylesheet:
            return False

        self.app.setStyleSheet(self.stylesheet)
        self.set_palette()
        return True

    def set_palette(self):
        """Set the application palette to match the theme."""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#f4f4f4"))
        palette.setColor(QPalette.WindowText, QColor("#000000"))
        palette.setColor(QPalette.Base, QColor("#ffffff"))
        palette.setColor(QPalette.AlternateBase, QColor("#f4f4f4"))
        palette.setColor(QPalette.ToolTipBase, QColor("#ffffff"))
        palette.setColor(QPalette.ToolTipText, QColor("#000000"))
        palette.setColor(QPalette.Text, QColor("#000000"))
        palette.setColor(QPalette.Button, QColor("#f4f4f4"))
        palette.setColor(QPalette.ButtonText, QColor("#000000"))
        palette.setColor(QPalette.BrightText, QColor("#ff0000"))
        palette.setColor(QPalette.Link, QColor("#2a82da"))
        palette.setColor(QPalette.Highlight, QColor("#90AF13"))
        palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))

        self.app.setPalette(palette)
