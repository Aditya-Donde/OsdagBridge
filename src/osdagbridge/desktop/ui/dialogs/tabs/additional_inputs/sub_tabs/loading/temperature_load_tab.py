from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import TEMPERATURE_LOAD_TAB_SCHEMA
from osdagbridge.desktop.ui.dialogs.tabs.base import SchemaTab


class TemperatureLoadTab(SchemaTab):
    """Temperature load inputs — fully rendered from TEMPERATURE_LOAD_TAB_SCHEMA."""
    schema = TEMPERATURE_LOAD_TAB_SCHEMA

    def __init__(self, owner, parent=None):
        super().__init__(owner, parent)

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
