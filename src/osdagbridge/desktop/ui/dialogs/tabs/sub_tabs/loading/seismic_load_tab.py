from PySide6.QtWidgets import QComboBox, QLineEdit

from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import SEISMIC_LOAD_TAB_SCHEMA
from osdagbridge.desktop.ui.dialogs.tabs.base import SchemaTab


class SeismicLoadTab(SchemaTab):
    """Seismic Load tab — fully rendered from SEISMIC_LOAD_TAB_SCHEMA."""
    schema = SEISMIC_LOAD_TAB_SCHEMA

    def __init__(self, owner, parent=None):
        super().__init__(owner, parent)

        # Build lookup dict for computed output fields so update_project_location can set them
        self.seismic_computed_fields = {}
        for section in SEISMIC_LOAD_TAB_SCHEMA.get("sections", []):
            if section.get("type") == "computed_group":
                for field in section.get("fields", []):
                    bind_name = field.get("bind")
                    if bind_name and hasattr(owner, bind_name):
                        self.seismic_computed_fields[bind_name] = getattr(owner, bind_name)

        # Sync seismic zone from project output if already available
        if hasattr(owner, "project_seismic_zone") and hasattr(owner, "seismic_zone_combo"):
            zone_val = str(owner.project_seismic_zone)
            widget = owner.seismic_zone_combo
            if isinstance(widget, QComboBox):
                widget.setCurrentText(zone_val)
            elif isinstance(widget, QLineEdit):
                widget.setText(zone_val)

    def update_project_location(self, location_data):
        if not location_data:
            return
        weather = location_data.get("weather_data")
        if not weather:
            return
        zone = weather.get("zone")
        z_val = weather.get("z_value")
        if zone is not None and hasattr(self.owner, "seismic_zone_combo"):
            widget = self.owner.seismic_zone_combo
            if isinstance(widget, QComboBox):
                idx = widget.findText(str(zone))
                if idx >= 0:
                    widget.setCurrentIndex(idx)
            elif isinstance(widget, QLineEdit):
                widget.setText(str(zone))
        if z_val is not None and "zone_factor" in self.seismic_computed_fields:
            self.seismic_computed_fields["zone_factor"].setText(str(z_val))
