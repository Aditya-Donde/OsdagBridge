"""Wearing Course sub-tab for Typical Section Details."""

from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import (
    WEARING_COURSE_TAB_SCHEMA,
)
from osdagbridge.desktop.ui.dialogs.tabs.base import SchemaTab


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


class WearingCourseTab(SchemaTab):
    """Schema-driven wearing course page bound onto the Typical Section owner."""
    schema = _WEARING_COURSE_VIEW_SCHEMA

    def __init__(self, owner, parent=None):
        super().__init__(owner, parent)
        self.setStyleSheet("background-color: white;")
