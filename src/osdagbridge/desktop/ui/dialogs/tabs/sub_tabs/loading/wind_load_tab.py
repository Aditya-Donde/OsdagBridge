from PySide6.QtWidgets import QWidget

from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import (
    WIND_LOAD_TAB_SCHEMA,
)
from osdagbridge.desktop.ui.dialogs.tabs import schema_io
from osdagbridge.desktop.ui.dialogs.tabs.ui_builder import UIBuilder


class WindLoadTab(QWidget):
    """Wind Load tab rendered from WIND_LOAD_TAB_SCHEMA."""

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.schema = WIND_LOAD_TAB_SCHEMA
        UIBuilder(owner=self, schema=self.schema).build_tab(self)

        self.wind_computed_fields = {}
        for section in self.schema.get("sections", []):
            if section.get("type") != "computed_group":
                continue
            for field in section.get("fields", []):
                bind_name = field.get("bind")
                if bind_name and hasattr(self, bind_name):
                    self.wind_computed_fields[bind_name] = getattr(self, bind_name)

        self.reset_defaults()

    def reset_defaults(self):
        schema_io.reset_defaults(self, self.schema)

    def update_project_location(self, location_data):
        if not location_data:
            return

        weather = location_data.get("weather_data")
        if weather:
            wind = weather.get("wind_speed")
            if wind is not None and hasattr(self, "basic_wind_speed_input"):
                self.basic_wind_speed_input.setText(str(wind))
