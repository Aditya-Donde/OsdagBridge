"""
Pieces shared by the two places recent projects are listed: the home page's
"Recent Projects" card and the search overlay's results.

Both draw the same row - a module icon, a name, a date - and both grow on hover
to reveal the same three actions, so the icon lookup and the hover animation
live here rather than being written out twice.
"""
from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QSize, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame, QHBoxLayout, QPushButton

from osdagbridge.desktop.data.database.database_config import MODULE_MAP, MODULE_KEY
from osdagbridge.desktop.data.ui_data import Data
from osdagbridge.desktop.ui.utils.custom_cursors import pointing_hand_cursor

ICON_SIZE = QSize(24, 24)
EXPAND_DURATION_MS = 250


def recents_icon(record: dict) -> QIcon:
    """The icon for a record's module: its own artwork if it has any, else the
    navbar glyph in its "recents" variant."""
    parent_navbar = MODULE_MAP.get(record.get(MODULE_KEY))[3]
    artwork = Data.RECENTS_ICONS.get(parent_navbar)
    if artwork:
        return QIcon(artwork)
    # The recents artwork sits beside the nav icons under a different folder
    path = Data.NAVBAR_ICONS.get(parent_navbar)[0].replace("nav_icons", "recents")
    return QIcon(path)


def recents_pixmap(record: dict):
    """``recents_icon`` rendered at the size these rows draw it."""
    return recents_icon(record).pixmap(ICON_SIZE)


class HoverExpandFrame(QFrame):
    """A row that grows on hover to reveal its action buttons.

    Subclasses build their contents in ``setupUI`` and call ``init_expansion``
    once the actions frame exists.
    """

    def __init__(self, collapsed_height, expanded_height, parent=None):
        super().__init__(parent)
        self.original_height = collapsed_height
        self.expanded_height = expanded_height
        self.is_expanded = False
        self.actions_frame = None
        self.expand_animation = None

    def init_expansion(self, actions_frame):
        """Hook up the hover animation for a row that has actions to reveal."""
        self.actions_frame = actions_frame
        self.actions_frame.setVisible(False)

        # Animate minimumHeight and mirror it onto the fixed height: animating
        # maximumHeight alone does nothing while setFixedHeight has pinned the
        # minimum to the collapsed value.
        self.expand_animation = QPropertyAnimation(self, b"minimumHeight")
        self.expand_animation.setDuration(EXPAND_DURATION_MS)
        self.expand_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.expand_animation.valueChanged.connect(
            lambda value: self.setFixedHeight(int(value))
        )

    def _animate_to(self, height):
        self.expand_animation.stop()
        self.expand_animation.setStartValue(self.height())
        self.expand_animation.setEndValue(height)
        self.expand_animation.start()

    def _set_hovered(self, hovered):
        """Style hook: rows that carry a `hovered` QSS property override this."""

    def enterEvent(self, event):
        if self.expand_animation is not None and not self.is_expanded:
            self.is_expanded = True
            self._set_hovered(True)
            self.actions_frame.setVisible(True)
            self.actions_frame.raise_()
            self._animate_to(self.expanded_height)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.expand_animation is not None and self.is_expanded:
            self.is_expanded = False
            self._set_hovered(False)
            self.actions_frame.setVisible(False)
            self._animate_to(self.original_height)
        super().leaveEvent(event)


class ProjectActions(QFrame):
    """The Report / OSI / Open button row revealed under a project."""

    generateReport = Signal(dict)
    downloadOsi = Signal(dict)
    openProject = Signal(dict)

    def __init__(self, record, button_object_name, report_label, margins, parent=None):
        super().__init__(parent)
        self.setObjectName("actionsFrame")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(*margins)
        layout.setSpacing(5)

        for label, signal in (
            (report_label, self.generateReport),
            ("Download OSI", self.downloadOsi),
            ("Open Project", self.openProject),
        ):
            button = QPushButton(label)
            button.setFixedHeight(25)
            button.setCursor(pointing_hand_cursor())
            button.setObjectName(button_object_name)
            button.clicked.connect(
                lambda _checked=False, s=signal, r=record: s.emit(r)
            )
            layout.addWidget(button)
