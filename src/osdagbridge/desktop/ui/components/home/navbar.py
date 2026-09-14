"""
Vertical navigation bar for OsdagBridge GUI.
Handles navigation buttons and logo display.
"""
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel,
    QVBoxLayout, QFrame, QSizePolicy, QSpacerItem
)
from PySide6.QtGui import QCursor, QIcon, QPainter, QColor
from PySide6.QtCore import Qt, QSize, QEvent, Signal
from osdagbridge.desktop.ui.utils.custom_cursors import pointing_hand_cursor
from PySide6.QtSvgWidgets import QSvgWidget

from osdagbridge import __version__ as VERSION
import osdagbridge.desktop.resources.mainPageIcons_rc

class CustomButton(QPushButton):
    def __init__(self, text, icon_path_default, icon_path_clicked, under_dev=False, group=None, parent=None):
        super().__init__(text, parent)
        self.group = group
        self.is_clicked = False
        self.setCursor(pointing_hand_cursor())
        self.setFocusPolicy(Qt.NoFocus)

        self.default_icon = QIcon(icon_path_default)
        self.clicked_icon = QIcon(icon_path_clicked)
        self.setIcon(self.default_icon)
        self.set_default_style()

    def mousePressEvent(self, event):
        if self.group:
            for btn in self.group:
                btn.set_default_style()
                btn.setIcon(btn.default_icon)
                btn.is_clicked = False
        self.set_active_style()
        self.setIcon(self.clicked_icon)
        self.is_clicked = True
        super().mousePressEvent(event)

    def set_font_size(self, size):
        font = self.font()
        font.setPointSize(size)
        self.setFont(font)
        # Ensure the stylesheet doesn't override the programmatic font. Assign
        # rather than append: this runs on every resize, and appending grew the
        # stylesheet string without bound.
        self.setStyleSheet(f"font-size: {size}px;")

    def set_default_style(self):
        # Base style for default state
        self.setProperty("state", "default")
        self.style().unpolish(self)
        self.style().polish(self)

    def set_active_style(self):
        # Base style for active state
        self.setProperty("state", "active")
        self.style().unpolish(self)
        self.style().polish(self)

class VerticalMenuBar(QWidget):
    nav_bar_trigger = Signal(object, object)
    def __init__(self, data: dict, icons: dict):
        super().__init__()
        # Ensures automatic deletion when closed
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        # Set size policy to expanding so it grows/shrinks with its parent layout
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(2, 5, 2, 0)
        self.main_layout.setSpacing(0)

        # Header section
        self.header = QFrame()
        self.header.setObjectName("navbar_header")
        self.header_layout = QVBoxLayout(self.header)
        self.header_layout.setSpacing(5)
        self.header_layout.setAlignment(Qt.AlignCenter) # Center logo in header

        self.osdag_logo = QSvgWidget(":/vectors/Osdag_logo.svg", parent=self)
        # Remove fixed size here, will be set dynamically in resizeEvent
        self.header_layout.addWidget(self.osdag_logo, alignment=Qt.AlignCenter)

        self.version_label = QLabel(VERSION)
        self.version_label.setObjectName("version_label")

        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_layout.addWidget(self.version_label)

        self.main_layout.addWidget(self.header)

        # Add a spacer to push content down if header is small
        self.main_layout.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Buttons section
        self.button_group = []

        names = list(data.keys())
        for name in names:
            icon = icons.get(name)
            # If list is empty, Grey It
            if isinstance(data.get(name), list) and len(data.get(name)) <= 0:
                btn = CustomButton("  " + name, icon[0], icon[0], under_dev=True, group=self.button_group)
                btn.setDisabled(True)
                btn.setObjectName("navbar_button_under_dev")
                btn.setToolTip("Under Development")
                btn.setCursor(QCursor(Qt.CursorShape.ForbiddenCursor))
            else:
                btn = CustomButton("  " + name, icon[0], icon[0], group=self.button_group)
                btn.setObjectName("navbar_button")
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Make buttons expand vertically
            btn.clicked.connect(lambda _, label=name, data=data.get(name): self._on_nav_button_clicked(data, label))
            btn.setCursor(pointing_hand_cursor())
            self.button_group.append(btn)
            self.main_layout.addWidget(btn)

        # Set initial active button
        if self.button_group:
            self.button_group[0].set_active_style()
            self.button_group[0].setIcon(self.button_group[0].clicked_icon)
            self.button_group[0].is_clicked = True

        # Add a spacer to push content up if buttons are small
        self.main_layout.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Bottom section
        self.bottom_frame = QFrame()
        self.bottom_layout = QVBoxLayout(self.bottom_frame)
        self.bottom_layout.setSpacing(5)

        self.iitb_logo = QSvgWidget(parent=self)
        self.iitb_logo.load(":/vectors/IITB_logo_light.svg")
        # Remove fixed size here, will be set dynamically in resizeEvent
        self.bottom_layout.addWidget(self.iitb_logo, alignment=Qt.AlignmentFlag.AlignCenter)

        self.main_layout.addWidget(self.bottom_frame)

        # Last (button font, version font, logo) sizes actually applied, so a
        # resize that doesn't change them can skip the restyling work.
        self._applied_metrics = None

        # Initial update of sizes and fonts
        self.update_responsive_elements()

    def _on_nav_button_clicked(self, data, name):
        """
        Internal slot to handle button clicks and emit the custom signal.
        """
        self.nav_bar_trigger.emit(data, name)

    def update_responsive_elements(self):
        """Updates font sizes and SVG sizes based on current widget dimensions."""
        widget_height = self.height()
        widget_width = self.width()

        if widget_height <= 0 or widget_width <= 0:
            return # Avoid division by zero or invalid sizes

        # --- Responsive Font Sizes ---
        button_font_size = max(10, int(widget_height / 55)) # Buttons can be slightly smaller
        version_font_size = max(6, int(widget_height / 100)) # Version label can be smaller
        logo_size = max(40, int(min(widget_width, widget_height) / 3))

        # Restyling every button means an unpolish/polish pass each time, and a
        # drag-resize delivers a resizeEvent per pixel. Most of those land on
        # the same rounded-down sizes, so only redo the work when they change.
        metrics = (button_font_size, version_font_size, logo_size)
        if metrics == self._applied_metrics:
            return
        self._applied_metrics = metrics

        for btn in self.button_group:
            btn.set_font_size(button_font_size)
            # Adjust icon size based on button font size or a direct proportion
            icon_size = max(30, int(button_font_size * 2.5))
            btn.setIconSize(QSize(icon_size, icon_size))

            # Reapply style to ensure font update takes effect if style sheets override it
            if btn.is_clicked:
                btn.set_active_style()
            else:
                btn.set_default_style()

        self.version_label.setStyleSheet(f"""
            QLabel {{
                font-size: {version_font_size}pt; /* Apply font size directly via stylesheet for consistency */
            }}
        """)

        # --- Responsive SVG Sizes ---
        self.osdag_logo.setFixedSize(logo_size, logo_size)
        self.iitb_logo.setFixedSize(logo_size, logo_size)

        # Set header's fixed height based on the logo size + version label + spacing
        version_label_height = version_font_size + 8  # Font size + padding
        header_height = logo_size + version_label_height + 15  # Logo + version + spacing + padding
        self.header.setFixedHeight(header_height)

    def resizeEvent(self, event: QEvent):
        """Called when the widget is resized."""
        super().resizeEvent(event)
        self.update_responsive_elements() # Recalculate and apply sizes

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawRect(self.rect())
        super().paintEvent(event)

    def set_active_button_by_name(self, name):
        for btn in self.button_group:
            if btn.text().strip() == name:
                btn.set_active_style()
                btn.setIcon(btn.clicked_icon)
                btn.is_clicked = True
                btn.click()
            else:
                btn.set_default_style()
                btn.setIcon(btn.default_icon)
                btn.is_clicked = False
