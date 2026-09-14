"""
Top right button bar for OsdagBridge GUI.
Contains custom animated buttons and dropdowns for quick actions, along with
the small helpers their menu entries call.
"""
import os
import shutil
import subprocess
import sys
import webbrowser
from importlib import resources

from PySide6.QtWidgets import (
    QMenu, QPushButton
)
from PySide6.QtCore import Qt, QSize, QPoint, QPropertyAnimation, QEasingCurve, QTimer, Signal
from PySide6.QtGui import QIcon, QAction
from osdagbridge.desktop.ui.utils.custom_cursors import pointing_hand_cursor
from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox, MessageBoxType
from osdagbridge import __version__ as VERSION

DISCUSSIONS_URL = "https://github.com/osdag-admin/Osdag/discussions"
DOWNLOADS_URL = "https://osdag.fossee.in/resources/downloads"

# Button widths, icon-only and with the label shown
COLLAPSED_WIDTH = 40
EXPANDED_WIDTH = 120

# Section-database submenus: menu label -> [(entry label, database table)]
SECTION_DATABASES = {
    "Databases (IS 808:2021)": [
        ("Column", "Columns"), ("Beam", "Beams"),
        ("Channel", "Channels"), ("Angle", "Angles"),
    ],
    "Databases (IS 4923:2017)": [("SHS", "SHS"), ("RHS", "RHS")],
    "Databases (IS 1161:2014)": [("CHS", "CHS")],
}


def design_examples(*_args):
    """Open the bundled design-example documentation in the default browser."""
    try:
        resource_dir = resources.files(
            "osdag_core.data.ResourceFiles.design_example._build.html"
        )

        with resources.as_file(resource_dir) as temp_path:

            app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            target_dir = os.path.join(app_dir, "design_examples")

            # Copy once
            if not os.path.exists(target_dir):
                shutil.copytree(temp_path, target_dir, dirs_exist_ok=True)

            index_file = os.path.join(target_dir, "index.html")

            if sys.platform.startswith("win"):
                os.startfile(index_file)
            elif sys.platform == "darwin":
                subprocess.call(["open", index_file])
            else:
                subprocess.call(["xdg-open", index_file])

    except Exception as e:
        print("Error opening design examples:", e)


def open_url(url: str):
    """Open a URL in the user's browser, ignoring failures."""
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"[ERROR] Failed to open {url}: {e}")


class TopButton(QPushButton):
    """
    Custom QPushButton that changes style on hover and provides a momentary
    color change on click, instead of a persistent selected state.
    """
    def __init__(self, black_icon_path, white_icon_path, label, parent=None):
        super().__init__(parent)
        self.black_icon_path = black_icon_path
        self.white_icon_path = white_icon_path
        self.black_icon = QIcon(black_icon_path)
        self.white_icon = QIcon(white_icon_path)
        self.label_text = label

        # Internal flag to track if the mouse is currently hovering over the button
        self.is_hovering = False

        # Timer for reverting the style after a click
        self.click_animation_timer = QTimer(self)
        self.click_animation_timer.setSingleShot(True)
        self.click_animation_timer.timeout.connect(self._reset_style_after_click)

        # Set up initial button properties
        self.setObjectName("TopButton")
        self.setMinimumSize(40, 40) # Initial collapsed size
        self.setMaximumHeight(40)
        self.setIconSize(QSize(20, 20))

        # Initialize width animation for smooth expansion/collapse
        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(200) # milliseconds
        self.animation.setEasingCurve(QEasingCurve.OutCubic) # Smooth transition

        self.animation_max_width = QPropertyAnimation(self, b"maximumWidth")
        self.animation_max_width.setDuration(200)
        self.animation_max_width.setEasingCurve(QEasingCurve.OutCubic)

        self.setText("")
        self.setIcon(self.black_icon)
        # Apply the default style sheet initially
        self.apply_default_style()
        self.setCursor(pointing_hand_cursor()) # Indicate clickable element

        # Enable hover tracking for enterEvent and leaveEvent
        self.setAttribute(Qt.WA_Hover, True)

    def apply_default_style(self):
        """Apply default style"""
        self.setProperty("hover", "false")
        self.setProperty("pressed", "false")
        self.style().unpolish(self)
        self.style().polish(self)

    def apply_hover_style(self):
        """Apply hover style"""
        self.setProperty("hover", "true")
        self.setProperty("pressed", "false")
        self.style().unpolish(self)
        self.style().polish(self)

    def apply_pressed_style(self):
        """Apply pressed style"""
        self.setProperty("hover", "false")
        self.setProperty("pressed", "true")
        self.style().unpolish(self)
        self.style().polish(self)

    def _apply_animated_style(self, style_func, target_width, label_text=None, icon=None):
        """
        Applies a given style and animates the button's width.
        Stops any ongoing animations before starting new ones.
        """
        self.animation.stop()
        self.animation_max_width.stop()

        current_width = self.width()

        self.animation.setStartValue(current_width)
        self.animation.setEndValue(target_width)
        self.animation_max_width.setStartValue(current_width)
        self.animation_max_width.setEndValue(target_width)

        # Apply the style
        style_func()

        # Update icon and text if provided
        if icon is not None:
            self.setIcon(icon)
        if label_text is not None:
            self.setText(label_text)

        # Start the width animations
        self.animation.start()
        self.animation_max_width.start()

    def _expand(self, style_func=None):
        """Grow to the labelled state, in whichever style is asked for."""
        self._apply_animated_style(style_func or self.apply_hover_style,
                                   EXPANDED_WIDTH, self.label_text, self.white_icon)

    def _collapse(self):
        """Shrink back to the icon-only state."""
        self._apply_animated_style(self.apply_default_style,
                                   COLLAPSED_WIDTH, "", self.black_icon)

    def enterEvent(self, event):
        """
        Handles mouse entering the button area.
        Changes style to hover state if no click animation is active.
        """
        self.is_hovering = True
        # Only apply hover style if the button is not currently in a "clicked" animation
        if not self.click_animation_timer.isActive():
            self._expand()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """
        Handles mouse leaving the button area.
        Reverts style to default state if no click animation is active.
        """
        self.is_hovering = False
        if not self._stays_expanded() and not self.click_animation_timer.isActive():
            self._collapse()
        super().leaveEvent(event)

    def _stays_expanded(self):
        """Whether something other than hover is holding the button open."""
        return False

    def mousePressEvent(self, event):
        """
        Handles mouse button press event.
        Applies a momentary 'pressed' style and starts a timer to revert it.
        """
        if event.button() == Qt.LeftButton:
            # Apply the pressed style immediately
            self._expand(self.apply_pressed_style)
            # Start the timer to reset the style after a short delay
            self.click_animation_timer.start(150) # Revert after 150 milliseconds
        super().mousePressEvent(event)

    def _reset_style_after_click(self):
        """
        Callback function for `click_animation_timer`.
        Resets the button's style based on whether the mouse is still hovering or not.
        """
        if self.is_hovering or self._stays_expanded():
            self._expand()
        else:
            self._collapse()


class TopButton1(TopButton):
    """
    A TopButton that also stays expanded for as long as its dropdown is open.

    Everything else - the hover styling, the width animation and the momentary
    click feedback - is inherited unchanged.
    """

    def _stays_expanded(self):
        return getattr(self, "menu_is_open", False)

    def set_submenu(self, menu):
        """
        Sets the submenu and connects its show/hide signals.
        """
        self.submenu = menu
        self.menu_is_open = False
        self.submenu.aboutToShow.connect(self._on_menu_show)
        self.submenu.aboutToHide.connect(self._on_menu_hide)

    def _on_menu_show(self):
        """
        Called when submenu is about to show. Sets flag to keep expanded state.
        """
        self.menu_is_open = True
        self._expand()

    def _on_menu_hide(self):
        """
        Called when submenu is hidden. Reverts to collapsed state if not hovering.
        """
        self.menu_is_open = False
        if not self.is_hovering:
            self._collapse()

    def mousePressEvent(self, event):
        """
        Handles mouse press to trigger a momentary click animation.

        Unlike the base button this uses the hover style rather than the pressed
        one, and a shorter timer, so the button reads as "open" not "clicked".
        """
        self._expand()
        self.click_animation_timer.start(100) # 100ms for click feedback
        # Skip TopButton's own press handling; go straight to QPushButton's.
        QPushButton.mousePressEvent(self, event)


class DropDownButton(TopButton1):
    """
    A specialized TopButton for "Resources" that opens a dropdown menu on click.
    It inherits the momentary click effect from TopButton.
    """
    downloadDatabase = Signal(str, str)
    importSection = Signal(str)
    def __init__(self, black_icon_path, white_icon_path, label, data, parent=None):
        super().__init__(black_icon_path, white_icon_path, label, parent)
        self.setup_menu(data)

    def setup_menu(self, menu_items):
        """
        Sets up the dropdown menu with Osdag-themed styling and actions.
        """
        self.menu = QMenu(self)

        for text in menu_items:
            if text in SECTION_DATABASES:
                db_menu = QMenu(text, self)
                for label, table in SECTION_DATABASES[text]:
                    action = QAction(label, self)
                    action.triggered.connect(
                        lambda _=False, t=table: self.downloadDatabase.emit(t, "database"))
                    db_menu.addAction(action)
                self.menu.addMenu(db_menu)

            elif text == "Custom Database":
                cdb_menu = QMenu(text, self)

                download = QAction("Download xlsx", self)
                download.triggered.connect(
                    lambda: self.downloadDatabase.emit("Beams", "header"))
                cdb_menu.addAction(download)

                import_xlsx = QAction("Import xlsx", self)
                import_xlsx.triggered.connect(lambda: self.importSection.emit("Beams"))
                cdb_menu.addAction(import_xlsx)

                self.menu.addMenu(cdb_menu)

            else:
                action = QAction(text, self)
                handler = self._simple_actions().get(text)
                if handler:
                    action.triggered.connect(handler)
                self.menu.addAction(action)

        # Set the menu to the button
        self.set_submenu(self.menu)

    def _simple_actions(self):
        """Menu entries that map straight onto a single callable."""
        return {
            "Design Examples": design_examples,
            "Ask us a question": lambda: open_url(DISCUSSIONS_URL),
            "About OsdagBridge": self._about,
            "Check for Update": self._check_for_update,
        }

    def _about(self):
        CustomMessageBox(
            title="About OsdagBridge",
            text=f"OsdagBridge {VERSION}",
            informativeText=(
                "Open steel bridge design and graphics.\n\n"
                "A plugin for Osdag, developed by FOSSEE, IIT Bombay, and supported by\n"
                "the Ministry of Education, the Ministry of Steel, constructsteel and INSDAG."
            ),
            dialogType=MessageBoxType.About
        ).exec()

    def _check_for_update(self):
        result = CustomMessageBox(
            title="Check for Update",
            text=f"You are running OsdagBridge {VERSION}.",
            informativeText="Updates are published on the Osdag downloads page.",
            buttons=["Open Downloads", "Close"],
            dialogType=MessageBoxType.Information
        ).exec()
        if result == "Open Downloads":
            open_url(DOWNLOADS_URL)

    def mousePressEvent(self, event):
        """
        Overrides mousePressEvent to show the dropdown menu when the button is clicked.
        Also calls the super class's mousePressEvent to get the momentary click animation.
        """
        super().mousePressEvent(event) # Call parent's method for click animation
        # Use singleShot to ensure the menu pops up slightly after the click visual feedback
        QTimer.singleShot(50, lambda: self.menu.popup(self.mapToGlobal(QPoint(0, self.height()))))
