from PySide6.QtWidgets import QWidget

from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import TEMPERATURE_LOAD_TAB_SCHEMA
from osdagbridge.desktop.ui.dialogs.tabs import schema_io
from osdagbridge.desktop.ui.dialogs.tabs.ui_builder import UIBuilder


class TemperatureLoadTab(QWidget):
    """Temperature load inputs — fully rendered from TEMPERATURE_LOAD_TAB_SCHEMA."""

    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        UIBuilder(owner=self, schema=TEMPERATURE_LOAD_TAB_SCHEMA).build_tab(self)

    def update_project_location(self, location_data):
        if not location_data:
            return
        weather = location_data.get("weather_data")
        if weather:
            max_t = weather.get("max_temp")
            min_t = weather.get("min_temp")
            if max_t is not None and hasattr(self, "highest_max_temp_input"):
                self.highest_max_temp_input.setText(str(max_t))
            if min_t is not None and hasattr(self, "lowest_min_temp_input"):
                self.lowest_min_temp_input.setText(str(min_t))

    def reset_defaults(self):
        schema_io.reset_defaults(self, TEMPERATURE_LOAD_TAB_SCHEMA)
