"""Crash Barrier sub-tab for Typical Section Details."""

from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import (
    CRASH_BARRIER_TAB_SCHEMA,
)
from osdagbridge.desktop.ui.dialogs.tabs.base import SchemaTab


_CRASH_BARRIER_VIEW_SCHEMA = {
    "row_vertical_spacing": 20,
    "cards": [
        {
            "title": "Crash Barrier Inputs:",
            "label_width": CRASH_BARRIER_TAB_SCHEMA.get("label_width", 210),
            "field_width": 200,
            "rows": CRASH_BARRIER_TAB_SCHEMA.get("rows", []),
        }
    ]
}


class CrashBarrierTab(SchemaTab):
    """Schema-driven crash barrier page bound onto the Typical Section owner."""
    schema = _CRASH_BARRIER_VIEW_SCHEMA

    def __init__(self, owner, parent=None):
        super().__init__(owner, parent)
        self.setStyleSheet("background-color: white;")
