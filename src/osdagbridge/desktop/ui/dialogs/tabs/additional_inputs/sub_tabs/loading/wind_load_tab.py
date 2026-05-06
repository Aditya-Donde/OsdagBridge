from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import (
    WIND_LOAD_TAB_SCHEMA,
)
from osdagbridge.desktop.ui.dialogs.tabs.base import SchemaTab


class WindLoadTab(SchemaTab):
    """Wind Load tab rendered from WIND_LOAD_TAB_SCHEMA."""
    schema = WIND_LOAD_TAB_SCHEMA

    def __init__(self, owner, parent=None):
        super().__init__(owner, parent)

        self.wind_computed_fields = {}
        for section in self.schema.get("sections", []):
            if section.get("type") != "computed_group":
                continue
            for field in section.get("fields", []):
                bind_name = field.get("bind")
                if bind_name and hasattr(self, bind_name):
                    self.wind_computed_fields[bind_name] = getattr(self, bind_name)

    def update_project_location(self, location_data):
        if not location_data:
            return

        weather = location_data.get("weather_data")
        if weather:
            wind = weather.get("wind_speed")
            if wind is not None and hasattr(self, "basic_wind_speed_input"):
                self.basic_wind_speed_input.setText(str(wind))
