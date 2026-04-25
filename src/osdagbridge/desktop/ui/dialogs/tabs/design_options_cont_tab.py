from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import DESIGN_OPTIONS_CONT_SCHEMA
from osdagbridge.desktop.ui.dialogs.tabs.base import SchemaTab


class DesignOptionsContTab(SchemaTab):
    """Design Options (Cont.) Tab — fully rendered from DESIGN_OPTIONS_CONT_SCHEMA."""
    schema = DESIGN_OPTIONS_CONT_SCHEMA

    def __init__(self, parent_dialog):
        super().__init__(owner=self, parent=parent_dialog)
