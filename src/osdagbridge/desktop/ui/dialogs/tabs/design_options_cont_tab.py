from PySide6.QtWidgets import QWidget

from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import DESIGN_OPTIONS_CONT_SCHEMA
from osdagbridge.desktop.ui.dialogs.tabs import schema_io
from osdagbridge.desktop.ui.dialogs.tabs.ui_builder import UIBuilder


class DesignOptionsContTab(QWidget):
    """Design Options (Cont.) Tab — fully rendered from DESIGN_OPTIONS_CONT_SCHEMA."""

    def __init__(self, parent_dialog):
        super().__init__()
        self.parent_dialog = parent_dialog
        UIBuilder(owner=self, schema=DESIGN_OPTIONS_CONT_SCHEMA).build_tab(self)

    def save_values(self):
        return schema_io.collect_values(self, DESIGN_OPTIONS_CONT_SCHEMA)

    def restore_values(self, data: dict):
        schema_io.restore_values(self, DESIGN_OPTIONS_CONT_SCHEMA, data)

    def reset_defaults(self):
        schema_io.reset_defaults(self, DESIGN_OPTIONS_CONT_SCHEMA)

    def validate_tab(self):
        return schema_io.validate(self, DESIGN_OPTIONS_CONT_SCHEMA)
