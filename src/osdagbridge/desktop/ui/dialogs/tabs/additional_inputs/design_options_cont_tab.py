from osdagbridge.core.bridge_types.plate_girder.schemas import DESIGN_OPTIONS_CONT_SCHEMA
from osdagbridge.desktop.ui.dialogs.tabs.base import SchemaTab


class DesignOptionsContTab(SchemaTab):
    """Design Options (Cont.) Tab — fully rendered from DESIGN_OPTIONS_CONT_SCHEMA."""
    schema = DESIGN_OPTIONS_CONT_SCHEMA

    def __init__(self, parent=None, owner=None):
        # owner accepted for tab_container signature inspection; not forwarded.
        super().__init__(parent=parent)
