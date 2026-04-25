"""Base class for schema-driven tabs."""

from PySide6.QtWidgets import QWidget
from osdagbridge.desktop.ui.dialogs.tabs import schema_io
from osdagbridge.desktop.ui.dialogs.tabs.ui_builder import UIBuilder

class SchemaTab(QWidget):
    """Base class for tabs that are fully defined by a schema."""
    schema = None

    def __init__(self, owner, parent=None):
        super().__init__(parent or owner)
        self.owner = owner
        self.builder = None
        if self.schema:
            self.builder = UIBuilder(owner=owner, schema=self.schema)
            self.builder.build_tab(self)

    def collect_data(self) -> dict:
        if self.schema:
            return schema_io.collect_values(self.owner, self.schema)
        return {}

    def restore_data(self, data: dict) -> None:
        if self.schema and isinstance(data, dict):
            schema_io.restore_values(self.owner, self.schema, data)

    def reset_defaults(self) -> None:
        if self.schema:
            schema_io.reset_defaults(self.owner, self.schema)

    def validate_tab(self) -> list[str]:
        if self.schema:
            return schema_io.validate(self.owner, self.schema)
        return []
