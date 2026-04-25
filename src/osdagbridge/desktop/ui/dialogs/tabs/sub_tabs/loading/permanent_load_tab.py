from PySide6.QtWidgets import QWidget

from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import PERMANENT_LOAD_TAB_SCHEMA
from osdagbridge.desktop.ui.dialogs.tabs import schema_io
from osdagbridge.desktop.ui.dialogs.tabs.ui_builder import UIBuilder


class PermanentLoadTab(QWidget):
    """Permanent Load tab — fully rendered from PERMANENT_LOAD_TAB_SCHEMA."""

    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        UIBuilder(owner=self, schema=PERMANENT_LOAD_TAB_SCHEMA).build_tab(self)

    def reset_defaults(self):
        schema_io.reset_defaults(self, PERMANENT_LOAD_TAB_SCHEMA)
