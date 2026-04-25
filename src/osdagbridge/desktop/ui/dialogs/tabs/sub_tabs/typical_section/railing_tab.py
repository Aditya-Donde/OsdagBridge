"""Railing sub-tab for Typical Section Details."""

from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import (
    RAILING_TAB_SCHEMA,
)
from osdagbridge.desktop.ui.dialogs.tabs.base import SchemaTab


_RAILING_VIEW_SCHEMA = {
    "row_vertical_spacing": 20,
    "cards": [
        {
            "title": "Railing Inputs:",
            "label_width": RAILING_TAB_SCHEMA.get("label_width", 180),
            "field_width": 200,
            "rows": RAILING_TAB_SCHEMA.get("rows", []),
        }
    ]
}


class RailingTab(SchemaTab):
    """Schema-driven railing page bound onto the Typical Section owner."""
    schema = _RAILING_VIEW_SCHEMA

    def __init__(self, owner, parent=None):
        super().__init__(owner, parent)
        self.setStyleSheet("background-color: white;")
