from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import (
    SUPPORT_CONDITIONS_SCHEMA,
)
from osdagbridge.desktop.ui.dialogs.tabs.base import SchemaTab


class SupportConditionsTab(SchemaTab):
    schema = SUPPORT_CONDITIONS_SCHEMA

    def __init__(self, parent=None, owner=None):
        # owner is accepted for the tab_container builder's signature inspection
        # but intentionally not forwarded to super so SchemaTab uses self as owner.
        super().__init__(parent=parent)
        self.setObjectName("support_tab_widget")
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

    def validate_tab(self):
        return super().validate_tab()

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
