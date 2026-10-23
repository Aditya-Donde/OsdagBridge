"""Theme and styling helper utilities.

Provides centralized loaders for application QSS stylesheets (light/dark)
and helper methods for applying fallback or component-specific styling when needed.
"""

from PySide6.QtCore import QFile, QTextStream
from PySide6.QtWidgets import QApplication


def get_current_theme() -> str:
    """Return the active theme name ('light' or 'dark'). Defaults to 'light'."""
    app = QApplication.instance()
    return getattr(app, "theme", "light") if app else "light"


def load_stylesheet(theme: str = None) -> str:
    """Load the QSS stylesheet for the given theme from Qt resources.
    
    Args:
        theme: 'light' or 'dark'. If None, reads from QApplication.instance().theme.
        
    Returns:
        The stylesheet string, or empty string if loading failed.
    """
    if theme is None:
        theme = get_current_theme()

    qss_resource = ":/themes/darkstyle.qss" if theme == "dark" else ":/themes/lightstyle.qss"
    file = QFile(qss_resource)
    if file.open(QFile.ReadOnly | QFile.Text):
        stream = QTextStream(file)
        stylesheet = stream.readAll()
        file.close()
        return stylesheet
    return ""


def apply_theme_to_dialog(dialog, theme: str = None):
    """Ensure dialog-specific styles are active on the dialog if not already
    covered by the application stylesheet.
    
    If the dialog defines a custom QSS or needs fallback styling when displayed
    without an application-level stylesheet, this method loads the proper theme.
    """
    if theme is None:
        theme = get_current_theme()
    
    # In standard operation, dialogs inherit styles matching their objectName
    # from the global QApplication stylesheet. If needed, this function can
    # explicitly apply the theme stylesheet directly.
    qss = load_stylesheet(theme)
    if qss and not dialog.styleSheet():
        dialog.setStyleSheet(qss)
