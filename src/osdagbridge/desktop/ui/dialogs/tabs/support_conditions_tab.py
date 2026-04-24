from PySide6.QtWidgets import QWidget

from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import (
    SUPPORT_CONDITIONS_SCHEMA,
)
from osdagbridge.desktop.ui.dialogs.tabs import schema_io
from osdagbridge.desktop.ui.dialogs.tabs.ui_builder import UIBuilder


class SupportConditionsTab(QWidget):

    def __init__(self, parent_dialog):
        super().__init__()
        self.setObjectName("support_tab_widget")
        self.parent_dialog = parent_dialog
        self.setStyleSheet(
            """
            #support_tab_widget QLabel {
                border: none;
                background: transparent;
                padding: 0;
                border-radius: 0;
            }
            #support_tab_widget {
                background-color: #f5f5f5;
            }
            """
        )
        UIBuilder(owner=self, schema=SUPPORT_CONDITIONS_SCHEMA).build_tab(self)

    def save_values(self):
        return schema_io.collect_values(self, SUPPORT_CONDITIONS_SCHEMA)

    def restore_values(self, data: dict):
        if not isinstance(data, dict):
            return

        restored = dict(data)
        legacy_map = {
            "left_support": "left_support_combo",
            "right_support": "right_support_combo",
            "bearing_length": "bearing_length_input",
        }
        for old_key, bind_name in legacy_map.items():
            if old_key in restored and bind_name not in restored:
                restored[bind_name] = restored[old_key]

        schema_io.restore_values(self, SUPPORT_CONDITIONS_SCHEMA, restored)

    def reset_defaults(self):
        schema_io.reset_defaults(self, SUPPORT_CONDITIONS_SCHEMA)

    def validate_tab(self):
        errors = schema_io.validate(self, SUPPORT_CONDITIONS_SCHEMA)
        errors.extend(self._extra_validation())
        return list(dict.fromkeys(errors))

    def _extra_validation(self):
        widget = getattr(self, "bearing_length_input", None)
        if widget is None:
            return []

        text = widget.text().strip()
        if not text:
            return []

        try:
            if float(text) <= 0:
                return ["Bearing Length must be greater than 0."]
        except ValueError:
            return []

        return []
