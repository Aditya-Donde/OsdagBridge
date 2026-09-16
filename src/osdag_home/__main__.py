"""
Entry point for Osdag GUI application.
Handles splash screen and main window launch.
"""

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QFile, QTextStream, QTimer
from PySide6.QtGui import QFontDatabase, QFont, QIcon

# Disable native file dialogs globally to prevent OpenGL context conflicts
# This is critical for Linux systems with Intel/Mesa graphics drivers
QApplication.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs, True)
from .ui.utils.theme_manager import ThemeManager
from .resources import resources_rc
import sys

def gui():

    from .data.database.database_config import refactor_database, create_user_database
    # Create user database if not exist
    create_user_database()
    # Clean up user database to ensure 10 records and atmost 60 days older with path exist
    refactor_database()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    # Load bundled Ubuntu Sans font - works on all OS without needing font installed
    fid = QFontDatabase.addApplicationFont(":/fonts/UbuntuSans-Regular.ttf")
    if fid != -1:
        font_family = QFontDatabase.applicationFontFamilies(fid)[0]
        app.setFont(QFont(font_family, 10))  # Set as default app font
    else:
        print("[WARNING] Failed to load Ubuntu Sans font from resources")

    app.theme_manager = ThemeManager(app)
    app.theme_manager.load_theme(app.theme_manager.current_theme)

    if app.theme_manager.is_light():
        file = QFile(":/themes/lightstyle.qss")
    else:
        file = QFile(":/themes/darkstyle.qss")

    if file.open(QFile.ReadOnly | QFile.Text):
        stream = QTextStream(file)
        stylesheet = stream.readAll()
        file.close()
        app.setStyleSheet(stylesheet)
    
    def show_main_window():
        from .main_window import MainWindow
        app.main_window = MainWindow()
        # To ensure no Jittering on startup
        def show_final():
            app.main_window.show()
            app.setQuitOnLastWindowClosed(True)
        QTimer.singleShot(50, show_final)
        app.setWindowIcon(QIcon(":/images/osdag_logo.png"))

    app.setQuitOnLastWindowClosed(False)
    show_main_window()
    sys.exit(app.exec())

if __name__ == "__main__":
    gui()
