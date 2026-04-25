"""Median sub-tab for Typical Section Details."""

from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import (
    MEDIAN_TAB_SCHEMA,
)
from osdagbridge.desktop.ui.dialogs.tabs.base import SchemaTab


_MEDIAN_VIEW_SCHEMA = {
    "row_vertical_spacing": 20,
    "cards": [
        {
            "title": "Median Inputs:",
            "label_width": MEDIAN_TAB_SCHEMA.get("label_width", 210),
            "field_width": 200,
            "rows": MEDIAN_TAB_SCHEMA.get("rows", []),
        }
    ]
}


class MedianTab(SchemaTab):
    """Schema-driven median page bound onto the Typical Section owner."""
    schema = _MEDIAN_VIEW_SCHEMA

    def __init__(self, owner, parent=None):
        super().__init__(owner, parent)
        self.setStyleSheet("background-color: white;")
