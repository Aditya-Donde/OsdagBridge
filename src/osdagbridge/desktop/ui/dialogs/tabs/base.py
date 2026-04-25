"""Base class for schema-driven tabs."""

from PySide6.QtWidgets import QWidget
from osdagbridge.desktop.ui.dialogs.tabs import schema_io
from osdagbridge.desktop.ui.dialogs.tabs.ui_builder import UIBuilder

_BIND_KEYS = (
    "bind",
    "label_bind",
    "bind_mode",
    "bind_value",
    "bind_widget",
    "bind_bounds_button",
    "add_button_bind",
    "edit_button_bind",
    "delete_button_bind",
    "frame_bind",
    "header_label_bind",
    "title_bind",
    "layout_bind",
    "container_bind",
)
_LEGACY_FIELD_LIST_KEYS = ("section_inputs", "stiffener_inputs", "web_buckling_inputs")


class SchemaTab(QWidget):
    """Base class for tabs that are fully defined by a schema."""
    schema = None

    def __init__(self, owner, parent=None):
        super().__init__(parent or owner)
        self.owner = owner
        self.builder = None
        if self.schema:
            # Bind schema widgets and signal handlers to the concrete tab. The
            # parent/container remains available as ``self.owner`` for cross-tab
            # coordination.
            self.builder = UIBuilder(owner=self, schema=self.schema)
            self.builder.build_tab(self)
            if getattr(owner, "_expose_child_schema_binds", False):
                self._expose_schema_binds_to(owner)

    def _expose_schema_binds_to(self, target) -> None:
        """Mirror schema-bound attributes to a parent controller when requested."""
        if target is None or target is self:
            return
        for bind_name in self._iter_schema_bind_names(self.schema):
            if hasattr(self, bind_name):
                setattr(target, bind_name, getattr(self, bind_name))

    @classmethod
    def _iter_schema_bind_names(cls, node):
        if isinstance(node, list):
            for item in node:
                yield from cls._iter_schema_bind_names(item)
            return
        if not isinstance(node, dict):
            return

        for key in _BIND_KEYS:
            value = node.get(key)
            if value:
                yield str(value)

        for group in node.get("checkbox_groups", []) or []:
            yield from cls._iter_schema_bind_names(group)
        for item in node.get("widgets", []) or []:
            yield from cls._iter_schema_bind_names(item)
        for item in node.get("cads", []) or []:
            yield from cls._iter_schema_bind_names(item)
        for field in node.get("row_fields", []) or []:
            yield from cls._iter_schema_bind_names(field)

        for key in ("cards", "sections", "columns", "pages", "overview"):
            for child in node.get(key, []) or []:
                yield from cls._iter_schema_bind_names(child)
        for key in _LEGACY_FIELD_LIST_KEYS:
            for child in node.get(key, []) or []:
                yield from cls._iter_schema_bind_names(child)

        rows = node.get("rows", []) or []
        for row in rows:
            if isinstance(row, dict):
                yield from cls._iter_schema_bind_names(row.get("fields", []) or [])
            elif isinstance(row, list):
                yield from cls._iter_schema_bind_names(row)

        fields = node.get("fields")
        if isinstance(fields, dict):
            fields = fields.values()
        for field in fields or []:
            yield from cls._iter_schema_bind_names(field)

    def collect_data(self) -> dict:
        if self.schema:
            return schema_io.collect_values(self, self.schema)
        return {}

    def save_values(self) -> dict:
        """Compatibility wrapper for older callers."""
        return self.collect_data()

    def save_properties(self) -> dict:
        """Compatibility wrapper for older callers."""
        return self.collect_data()

    def get_widget(self, bind_name: str, default=None):
        return getattr(self, str(bind_name), default)

    def widget_text(self, bind_name: str, default: str = "") -> str:
        widget = self.get_widget(bind_name)
        if widget is None:
            return default
        if hasattr(widget, "text"):
            try:
                return str(widget.text())
            except Exception:
                return default
        return default

    def widget_current_text(self, bind_name: str, default: str = "") -> str:
        widget = self.get_widget(bind_name)
        if widget is None:
            return default
        if hasattr(widget, "currentText"):
            try:
                return str(widget.currentText())
            except Exception:
                return default
        return default

    def widget_float(self, bind_name: str, default=None):
        text = self.widget_text(bind_name, "")
        try:
            text = text.strip()
            return float(text) if text else default
        except Exception:
            return default

    def set_widget_text(self, bind_name: str, value) -> None:
        widget = self.get_widget(bind_name)
        if widget is not None and hasattr(widget, "setText"):
            widget.setText("" if value is None else str(value))

    def set_widget_current_text(self, bind_name: str, value) -> None:
        widget = self.get_widget(bind_name)
        if widget is not None and hasattr(widget, "setCurrentText"):
            widget.setCurrentText("" if value is None else str(value))

    def export_dependency_state(self) -> dict:
        return {}

    def sync_from_parent_state(self, state: dict) -> None:
        _ = state

    def refresh_from_girder_state(self, state: dict) -> None:
        self.sync_from_parent_state(state)

    def restore_data(self, data: dict) -> None:
        if self.schema and isinstance(data, dict):
            schema_io.restore_values(self, self.schema, data)

    def restore_values(self, data: dict) -> None:
        """Compatibility wrapper for older callers."""
        self.restore_data(data)

    def restore_properties(self, data: dict) -> None:
        """Compatibility wrapper for older callers."""
        self.restore_data(data)

    def reset_defaults(self) -> None:
        if self.schema:
            schema_io.reset_defaults(self, self.schema)

    def validate_tab(self) -> list[str]:
        if self.schema:
            return schema_io.validate(self, self.schema)
        return []
