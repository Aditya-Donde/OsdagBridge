"""Wearing Course sub-tab for Typical Section Details."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QScrollArea, QVBoxLayout, QWidget

from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import (
    WEARING_COURSE_TAB_SCHEMA,
)
from osdagbridge.desktop.ui.dialogs.tabs.ui_builder import UIBuilder


_WEARING_COURSE_VIEW_SCHEMA = {
    "row_vertical_spacing": 20,
    "cards": [
        {
            "title": "Wearing Course Inputs:",
            "label_width": WEARING_COURSE_TAB_SCHEMA.get("label_width", 200),
            "field_width": 200,
            "rows": WEARING_COURSE_TAB_SCHEMA.get("rows", []),
        }
    ]
}


class WearingCourseTab(QWidget):
    """Schema-driven wearing course page bound onto the Typical Section owner."""

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.setStyleSheet("background-color: white;")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background-color: white; border: none; }")

        page = QWidget()
        page.setStyleSheet("background-color: white;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 12, 18, 18)
        layout.setSpacing(8)

        UIBuilder(owner=owner, schema=_WEARING_COURSE_VIEW_SCHEMA).build(layout)
        layout.addStretch()

        scroll.setWidget(page)
        root.addWidget(scroll)
