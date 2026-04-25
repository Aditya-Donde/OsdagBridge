from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import PERMANENT_LOAD_TAB_SCHEMA
from osdagbridge.desktop.ui.dialogs.tabs.base import SchemaTab


class PermanentLoadTab(SchemaTab):
    """Permanent Load tab — fully rendered from PERMANENT_LOAD_TAB_SCHEMA."""
    schema = PERMANENT_LOAD_TAB_SCHEMA

    def __init__(self, owner, parent=None):
        super().__init__(owner, parent)
