from PySide6.QtWidgets import QWidget, QComboBox, QLineEdit

from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import SEISMIC_LOAD_TAB_SCHEMA
from osdagbridge.desktop.ui.dialogs.tabs import schema_io
from osdagbridge.desktop.ui.dialogs.tabs.ui_builder import UIBuilder


class SeismicLoadTab(QWidget):
    """Seismic Load tab — fully rendered from SEISMIC_LOAD_TAB_SCHEMA."""

    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        UIBuilder(owner=self, schema=SEISMIC_LOAD_TAB_SCHEMA).build_tab(self)

        # Build lookup dict for computed output fields so update_project_location can set them
        self.seismic_computed_fields = {}
        for section in SEISMIC_LOAD_TAB_SCHEMA.get("sections", []):
            if section.get("type") == "computed_group":
                for field in section.get("fields", []):
                    bind_name = field.get("bind")
                    if bind_name and hasattr(self, bind_name):
                        self.seismic_computed_fields[bind_name] = getattr(self, bind_name)

        # Sync seismic zone from project output if already available
        if hasattr(owner, "project_seismic_zone") and hasattr(self, "seismic_zone_combo"):
            zone_val = str(owner.project_seismic_zone)
            widget = self.seismic_zone_combo
            if isinstance(widget, QComboBox):
                widget.setCurrentText(zone_val)
            elif isinstance(widget, QLineEdit):
                widget.setText(zone_val)

        self.reset_defaults()

    def _toggle_seismic_custom_inputs(self):
        if hasattr(self, "dead_load_seismic_combo") and hasattr(self, "dead_load_custom_input"):
            self.dead_load_custom_input.setEnabled(
                self.dead_load_seismic_combo.currentText() == "Custom"
            )
        if hasattr(self, "live_load_seismic_combo") and hasattr(self, "live_load_custom_input"):
            self.live_load_custom_input.setEnabled(
                self.live_load_seismic_combo.currentText() == "Custom"
            )

    def reset_defaults(self):
        schema_io.reset_defaults(self, SEISMIC_LOAD_TAB_SCHEMA, after=self._toggle_seismic_custom_inputs)

    def update_project_location(self, location_data):
        if not location_data:
            return
        weather = location_data.get("weather_data")
        if not weather:
            return
        zone = weather.get("zone")
        z_val = weather.get("z_value")
        if zone is not None and hasattr(self, "seismic_zone_combo"):
            widget = self.seismic_zone_combo
            if isinstance(widget, QComboBox):
                idx = widget.findText(str(zone))
                if idx >= 0:
                    widget.setCurrentIndex(idx)
            elif isinstance(widget, QLineEdit):
                widget.setText(str(zone))
        if z_val is not None and "zone_factor" in self.seismic_computed_fields:
            self.seismic_computed_fields["zone_factor"].setText(str(z_val))
