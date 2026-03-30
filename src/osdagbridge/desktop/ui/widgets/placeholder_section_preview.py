from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QStackedLayout, QWidget

from osdagbridge.desktop.ui.widgets.section_viewer import SectionPreviewWidget


class PlaceholderSectionPreviewWidget(QWidget):
    """A SectionPreviewWidget that shows a placeholder when empty.

    The underlying SectionPreviewWidget renders nothing when no section is set,
    which can look like a blank/disabled UI. This wrapper keeps a consistent
    placeholder text (e.g. "Bracing", "Top Chord") until a section is set.
    """

    def __init__(self, placeholder_text: str, min_height: int = 110, parent: QWidget | None = None):
        super().__init__(parent)

        self._placeholder = QLabel(placeholder_text)
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.setMinimumHeight(min_height)
        self._placeholder.setStyleSheet(
            "QLabel { border: 1px solid #d0d0d0; border-radius: 10px; "
            "background-color: #f7f7f7; font-weight: bold; color: #5b5b5b; }"
        )

        self._preview = SectionPreviewWidget(min_height=min_height)
        self._preview.setMinimumHeight(min_height)
        self._preview.setStyleSheet(
            "QWidget { border: 1px solid #d0d0d0; border-radius: 10px; background-color: #ffffff; }"
        )

        self._stack = QStackedLayout(self)
        self._stack.setContentsMargins(0, 0, 0, 0)
        self._stack.addWidget(self._placeholder)
        self._stack.addWidget(self._preview)

        self.set_section("", "")

    def set_section(self, section_type: str, designation: str, *args):
        section_type = (section_type or "").strip()
        designation = (designation or "").strip()

        if not section_type and not designation:
            # Ensure placeholder is visible.
            self._stack.setCurrentWidget(self._placeholder)
            try:
                self._preview.set_section("", "")
            except Exception:
                pass
            return

        self._stack.setCurrentWidget(self._preview)
        try:
            self._preview.set_section(section_type, designation, *args)
        except TypeError:
            # Some call sites may pass an optional third argument.
            self._preview.set_section(section_type, designation)

    def clear(self) -> None:
        self.set_section("", "")

    @property
    def preview(self) -> SectionPreviewWidget:
        return self._preview
