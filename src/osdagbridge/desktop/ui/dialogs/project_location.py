from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QWidget,
    QCheckBox, QFrame, QPushButton, QComboBox, QSizePolicy, QSizeGrip,
    QRadioButton, QButtonGroup, QStackedWidget, QSpacerItem, QMessageBox
)
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import Qt, QUrl
from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.core.bridge_types.plate_girder.ui_fields_project_location import (
    get_state_list,
    get_station_list,
    get_default_location,
    get_weather,
)

from PySide6.QtCore import Slot, Signal, QObject, QUrl
from osdagbridge.desktop.ui.widgets.native_map import NativeMapWidget
from osdagbridge.core.data.project_location.zone_lookup import get_zones_for_coordinates, get_temperature_for_coordinates


# Remember last custom weather values during the session so reopening the dialog
# retains user-entered data instead of resetting to defaults.
LAST_CUSTOM_WEATHER_DATA = None




class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()  # Prevent changing selection on scroll

def apply_field_style(widget):
    widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    widget.setMinimumHeight(28)
    
    if isinstance(widget, QComboBox):
        style = """
            QComboBox{
                padding: 1px 7px;
                border: 1px solid black;
                border-radius: 5px;
                background-color: white;
                color: black;
            }
            QComboBox::drop-down{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                border-left: 0px;
            }
            QComboBox::down-arrow{
                image: url(:/vectors/arrow_down_light.svg);
                width: 20px;
                height: 20px;
                margin-right: 8px;
            }
            QComboBox::down-arrow:on {
                image: url(:/vectors/arrow_up_light.svg);
                width: 20px;
                height: 20px;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView{
                background-color: white;
                border: 1px solid black;
                outline: none;
            }
            QComboBox QAbstractItemView::item{
                color: black;
                background-color: white;
                border: none;
                border: 1px solid white;
                border-radius: 0;
                padding: 2px;
            }
            QComboBox QAbstractItemView::item:hover{
                border: 1px solid #90AF13;
                background-color: #90AF13;
                color: black;
            }
            QComboBox QAbstractItemView::item:selected{
                background-color: #90AF13;
                color: black;
                border: 1px solid #90AF13;
            }
            QComboBox QAbstractItemView::item:selected:hover{
                background-color: #90AF13;
                color: black;
                border: 1px solid #94b816;
            } 
        """
        widget.setStyleSheet(style)
    elif isinstance(widget, QLineEdit):
        widget.setStyleSheet("""
            QLineEdit {
                padding: 1px 7px;
                border: 1px solid #070707;
                border-radius: 6px;
                background-color: white;
                color: #000000;
                font-weight: normal;
            }
        """)




class CustomWeatherDataDialog(QDialog):
    """
    Dialog to manually input weather/seismic data.
    """
    def __init__(self, parent=None, initial_data=None):
        super().__init__(parent)
        self.setWindowTitle("Custom Weather Data")
        self.setFixedSize(400, 420)
        self.data = initial_data or {}
        
        # Apply Osdag Theme
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border: 1px solid #90AF13;
            }
            QLabel {
                color: #2d2d2d;
                font-size: 12px;
                font-weight: 500;
            }
            QLineEdit {
                padding: 4px 8px;
                border: 1px solid #dcdcdc;
                border-radius: 4px;
                background-color: white;
                color: black;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #90AF13;
            }
            QPushButton#primary {
                background-color: #90AF13;
                color: white;
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: 600;
                border: none;
            }
            QPushButton#primary:hover { background-color: #7a9b0f; }
            QPushButton#ghost {
                background-color: #f1f1f1;
                color: #1d1d1d;
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: 600;
                border: none;
            }
            QPushButton#ghost:hover { background-color: #e6e6e6; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(25, 25, 25, 25)
        
        title = QLabel("Enter Custom Values")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #90AF13; margin-bottom: 5px;")
        layout.addWidget(title)

        # Basic Wind Speed
        wind_layout = QVBoxLayout()
        wind_layout.setSpacing(6)
        wind_layout.addWidget(QLabel("Basic Wind Speed (m/s)"))
        self.wind_input = QLineEdit()
        self.wind_input.setPlaceholderText("e.g. 50")
        if self.data.get("wind_speed"):
            self.wind_input.setText(str(self.data.get("wind_speed")))
        wind_layout.addWidget(self.wind_input)
        layout.addLayout(wind_layout)

        # Seismic Zone
        zone_layout = QVBoxLayout()
        zone_layout.setSpacing(6)
        zone_layout.addWidget(QLabel("Seismic Zone"))
        self.zone_combo = NoScrollComboBox()
        self.zone_combo.addItems(["Select Zone", "II", "III", "IV", "V"])
        if self.data.get("zone"):
            index = self.zone_combo.findText(self.data.get("zone"))
            if index >= 0:
                self.zone_combo.setCurrentIndex(index)
        # Apply specific combo style locally or via stylesheet above
        self.zone_combo.setStyleSheet("""
            QComboBox{
                padding: 4px 8px;
                border: 1px solid #dcdcdc;
                border-radius: 4px;
                background-color: white;
                color: black;
            }
            QComboBox::drop-down{ border: 0px; }
            QComboBox::down-arrow{ 
                image: url(:/vectors/arrow_down_light.svg); width: 12px; height: 12px; margin-right: 8px; 
            }
        """)
        zone_layout.addWidget(self.zone_combo)
        layout.addLayout(zone_layout)

        # Zone Factor (Z)
        z_layout = QVBoxLayout()
        z_layout.setSpacing(6)
        z_layout.addWidget(QLabel("Zone Factor (Z)"))
        self.z_input = QLineEdit()
        self.z_input.setPlaceholderText("e.g. 0.36")
        if self.data.get("z_value"):
             self.z_input.setText(str(self.data.get("z_value")))
        z_layout.addWidget(self.z_input)
        layout.addLayout(z_layout)

        # Shade Air Temperature
        temp_lbl = QLabel("Shade Air Temperature (°C)")
        layout.addWidget(temp_lbl)
        
        temp_layout = QHBoxLayout()
        temp_layout.setSpacing(15)
        
        max_col = QVBoxLayout()
        max_col.setSpacing(6)
        self.max_temp_input = QLineEdit()
        self.max_temp_input.setPlaceholderText("Max")
        if self.data.get("max_temp"):
             self.max_temp_input.setText(str(self.data.get("max_temp")))
        max_col.addWidget(self.max_temp_input)
        
        min_col = QVBoxLayout()
        min_col.setSpacing(6)
        self.min_temp_input = QLineEdit()
        self.min_temp_input.setPlaceholderText("Min")
        if self.data.get("min_temp"):
             self.min_temp_input.setText(str(self.data.get("min_temp")))
        min_col.addWidget(self.min_temp_input)
        
        temp_layout.addLayout(max_col)
        temp_layout.addLayout(min_col)
        layout.addLayout(temp_layout)

        layout.addStretch()

        # Build Footer
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()
        
        save_btn = QPushButton("Save")
        save_btn.setObjectName("primary")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("ghost")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)

    def get_data(self):
        return {
            "wind_speed": self.wind_input.text(),
            "zone": self.zone_combo.currentText() if self.zone_combo.currentText() != "Select Zone" else "",
            "z_value": self.z_input.text(),
            "max_temp": self.max_temp_input.text(),
            "min_temp": self.min_temp_input.text()
        }


class ProjectLocationDialog(QDialog):
    """Dialog for selecting project location with multiple input methods."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(780)
        self.setMinimumHeight(520)
        self.setObjectName("project_location_dialog")
        self.default_location = get_default_location()
        
        # Restore any previously entered custom weather data in this session
        self.custom_weather_data = LAST_CUSTOM_WEATHER_DATA

        self.setStyleSheet("""
            QDialog#project_location_dialog {
                background-color: #ffffff;
                border: 1px solid #90AF13;
            }
            QLabel#headline { font-size: 15px; font-weight: 700; color: #2d2d2d; }
            QLabel#hint { color: #4a4a4a; }
            QRadioButton { font-size: 12px; color: #1f1f1f; }
            QRadioButton::indicator { width: 16px; height: 16px; }
            QRadioButton::indicator::unchecked { border: 2px solid #90AF13; border-radius: 9px; background: transparent; }
            QRadioButton::indicator::checked { border: 2px solid #90AF13; background: #90AF13; border-radius: 9px; }
            QCheckBox { font-size: 12px; color: #1f1f1f; }
            QPushButton#primary {
                background-color: #90AF13;
                color: white;
                border-radius: 6px;
                padding: 8px 18px;
                font-weight: 600;
            }
            QPushButton#primary:hover { background-color: #7a9b0f; }
            QPushButton#primary:pressed { background-color: #64850c; }
            QPushButton#ghost {
                background-color: #f1f1f1;
                color: #1d1d1d;
                border-radius: 6px;
                padding: 8px 14px;
                font-weight: 600;
            }
            QPushButton#ghost:hover { background-color: #e6e6e6; }
            QPushButton#ghost:pressed { background-color: #d9d9d9; }
        """)

        self._setup_ui()
        self._connect_signals()
        self._apply_default_location()
        self._set_active_method("location_name")

        # If user had entered custom data earlier in the session, show it
        if self.custom_weather_data:
            self._update_irc_values(self.custom_weather_data)
        # Removed _lookup_weather call as it will be handled by signal
    
    def setupWrapper(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)
        
        self.title_bar = CustomTitleBar()
        self.title_bar.setTitle("Project Location")
        main_layout.addWidget(self.title_bar)
        
        self.content_widget = QWidget(self)
        main_layout.addWidget(self.content_widget, 1)

        size_grip = QSizeGrip(self)
        size_grip.setFixedSize(16, 16)

        overlay = QHBoxLayout()
        overlay.setContentsMargins(0, 0, 4, 4)
        overlay.addStretch(1)
        overlay.addWidget(size_grip, 0, Qt.AlignBottom | Qt.AlignRight)
        main_layout.addLayout(overlay)
    
    def _setup_ui(self):
        self.setupWrapper()
        main_layout = QVBoxLayout(self.content_widget)
        main_layout.setContentsMargins(18, 18, 18, 14)
        main_layout.setSpacing(12)

        header = QLabel("Project Location")
        header.setObjectName("headline")
        main_layout.addWidget(header)

        self._add_method_toggle(main_layout)
        self._build_body(main_layout)
        self._add_footer_buttons(main_layout)
    
    def _add_method_toggle(self, layout):
        bar = QHBoxLayout()
        bar.setSpacing(18)

        self.method_group = QButtonGroup(self)
        self.method_radio_location = QRadioButton("Enter Location Name")
        self.method_radio_map = QRadioButton("Select on Map") # Merged coordinates into this

        for radio in (self.method_radio_location, self.method_radio_map):
            radio.setCursor(Qt.PointingHandCursor)
            self.method_group.addButton(radio)
            bar.addWidget(radio)

        self.method_radio_location.setChecked(True)
        bar.addStretch()

        layout.addLayout(bar)

    def _build_body(self, layout):
        body = QHBoxLayout()
        body.setSpacing(14)

        left_card = QFrame()
        left_card.setObjectName("leftCard")
        left_card.setStyleSheet("""
            QFrame#leftCard {
                background-color: #ffffff;
                border: 1px solid #d8e2c4;
                border-radius: 10px;
            }
        """)
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(14, 12, 14, 12)
        left_layout.setSpacing(12)

        self.method_stack = QStackedWidget()
        self._add_location_page()
        self._add_map_page()
        self.method_stack.setCurrentIndex(0)
        left_layout.addWidget(self.method_stack)

        # Removed Lookup and Clear buttons row

        body.addWidget(left_card, 2)

        right_card = QFrame()
        right_card.setObjectName("ircCard")
        right_card.setStyleSheet("""
            QFrame#ircCard {
                background-color: #f7fbf1;
                border: 1px solid #90AF13;
                border-radius: 10px;
            }
            QFrame#ircCard QLabel { border: none; background: transparent; }
            QLabel#valueTitle { font-size: 12px; color: #4c6b10; font-weight: 700; }
            QLabel#valueLabel { font-size: 12px; color: #1f1f1f; }
            QLabel#valueStrong { font-size: 14px; font-weight: 800; color: #0f3e0a; }
        """)
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(14, 12, 14, 12)
        right_layout.setSpacing(8)

        title = QLabel("IRC 6 (2017) Values:")
        title.setObjectName("valueTitle")
        right_layout.addWidget(title)

        self.wind_speed_label = QLabel("Basic Wind Speed (m/sec): —")
        self.wind_speed_label.setObjectName("valueLabel")
        right_layout.addWidget(self.wind_speed_label)

        self.seismic_zone_label = QLabel("Seismic Zone: —    Z = —")
        self.seismic_zone_label.setObjectName("valueLabel")
        right_layout.addWidget(self.seismic_zone_label)

        self.temp_label = QLabel("Shade Air Temperature (°C): — / —")
        self.temp_label.setObjectName("valueLabel")
        right_layout.addWidget(self.temp_label)

        right_layout.addItem(QSpacerItem(0, 6))

        self.btn_custom_data = QPushButton("Custom Data")
        self.btn_custom_data.setObjectName("primary")
        self.btn_custom_data.setCursor(Qt.PointingHandCursor)
        self.btn_custom_data.setMinimumWidth(150)
        self.btn_custom_data.setAutoDefault(False)
        right_layout.addWidget(self.btn_custom_data)
        
        hint = QLabel("Manually overwrite wind, seismic zone & zone factor, and shade temps.")
        hint.setWordWrap(True)
        hint.setObjectName("hint")
        right_layout.addWidget(hint)
        right_layout.addStretch()
        
        body.addWidget(right_card, 1)

        layout.addLayout(body)


    def _add_location_page(self):
        page = QWidget()
        vbox = QVBoxLayout(page)
        vbox.setContentsMargins(2, 2, 2, 2)
        vbox.setSpacing(10)

        label = QLabel("Search by location name")
        label.setObjectName("hint")
        label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        label.setStyleSheet("font-weight: 700; color: #2d2d2d;")
        vbox.addWidget(label)

        state_col = QVBoxLayout()
        state_lbl = QLabel("State")
        self.state_combo = NoScrollComboBox()
        self.state_combo.addItems(get_state_list())
        apply_field_style(self.state_combo)
        state_col.addWidget(state_lbl)
        state_col.addWidget(self.state_combo)

        district_col = QVBoxLayout()
        district_lbl = QLabel("District")
        self.district_combo = NoScrollComboBox()
        self.district_combo.addItems(["Select District"])
        apply_field_style(self.district_combo)
        district_col.addWidget(district_lbl)
        district_col.addWidget(self.district_combo)

        row = QHBoxLayout()
        row.setSpacing(10)
        row.addLayout(state_col)
        row.addLayout(district_col)
        row.addStretch()
        vbox.addLayout(row)
        vbox.addStretch()

        self.method_stack.addWidget(page)

    def _add_map_page(self):
        page = QWidget()
        page.setStyleSheet("background-color: #f5f8f2;")
        vbox = QVBoxLayout(page)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(6)

        self.map_view = NativeMapWidget()
        vbox.addWidget(self.map_view, 1)

        # Coordinate inputs integrated here
        coord_container = QWidget()
        coord_container.setStyleSheet("background-color: #ffffff; border-top: 1px solid #d8e2c4;")
        coord_layout = QVBoxLayout(coord_container)
        coord_layout.setContentsMargins(10, 10, 10, 10)
        
        coord_label = QLabel("Enter Coordinates or Select on Map")
        coord_label.setStyleSheet("font-weight: bold; color: #2d2d2d;")
        coord_layout.addWidget(coord_label)

        row = QHBoxLayout()
        row.setSpacing(10)

        lat_col = QVBoxLayout()
        lat_lbl = QLabel("Latitude (°)")
        self.latitude_input = QLineEdit()
        apply_field_style(self.latitude_input)
        lat_col.addWidget(lat_lbl)
        lat_col.addWidget(self.latitude_input)

        lng_col = QVBoxLayout()
        lng_lbl = QLabel("Longitude (°)")
        self.longitude_input = QLineEdit()
        apply_field_style(self.longitude_input)
        lng_col.addWidget(lng_lbl)
        lng_col.addWidget(self.longitude_input)

        row.addLayout(lat_col)
        row.addLayout(lng_col)
        coord_layout.addLayout(row)
        
        vbox.addWidget(coord_container)

        # Connect map signal
        self.map_view.locationSelected.connect(self._on_map_location_selected)

        self.method_stack.addWidget(page)

    def _add_footer_buttons(self, layout):
        footer = QHBoxLayout()
        footer.addStretch()

        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("primary")
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.setMinimumWidth(90)
        ok_btn.clicked.connect(self.accept)
        ok_btn.setAutoDefault(False)
        footer.addWidget(ok_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("ghost")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setMinimumWidth(90)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setAutoDefault(False)
        footer.addWidget(cancel_btn)

        layout.addLayout(footer)
    
    def _connect_signals(self):
        self.method_radio_location.toggled.connect(lambda: self._set_active_method("location_name"))
        self.method_radio_map.toggled.connect(lambda: self._set_active_method("map"))
        self.state_combo.currentTextChanged.connect(self._on_state_changed)
        # Auto-update on district change
        self.district_combo.currentTextChanged.connect(self._on_district_changed)
        
        # New Signals
        self.btn_custom_data.clicked.connect(self._open_custom_dialog)
        
        # Enter key on coordinates updates map
        self.latitude_input.returnPressed.connect(self._sync_map_from_inputs)
        self.longitude_input.returnPressed.connect(self._sync_map_from_inputs)

    def _set_active_method(self, method):
        if method == "location_name" and self.method_radio_location.isChecked():
            self.method_stack.setCurrentIndex(0)
            self.latitude_input.setEnabled(False)
            self.longitude_input.setEnabled(False)
            self.state_combo.setEnabled(True)
            self.district_combo.setEnabled(True)
            self.map_view.setEnabled(False)
        elif method == "map" and self.method_radio_map.isChecked():
            self.method_stack.setCurrentIndex(1)
            self.latitude_input.setEnabled(True)
            self.longitude_input.setEnabled(True)
            self.state_combo.setEnabled(False)
            self.district_combo.setEnabled(False)
            self.map_view.setEnabled(True)

    def _apply_default_location(self):
        state = self.default_location.get("state", "")
        station = self.default_location.get("station", "")

        # Block signals to avoid overwriting persisted custom data during initialization
        self.state_combo.blockSignals(True)
        self.district_combo.blockSignals(True)

        if state:
            idx = self.state_combo.findText(state)
            if idx >= 0:
                self.state_combo.setCurrentIndex(idx)

        if station:
            idx = self.district_combo.findText(station)
            if idx >= 0:
                self.district_combo.setCurrentIndex(idx)

        self.state_combo.blockSignals(False)
        self.district_combo.blockSignals(False)

    def _on_map_location_selected(self, lat, lng):
        self.latitude_input.setText(f"{lat:.6f}")
        self.longitude_input.setText(f"{lng:.6f}")
        # Perform zone lookup for coordinates
        self._lookup_zones_for_coordinates(lat, lng)
        
    def _sync_map_from_inputs(self):
        """Called when Enter is pressed on manual coordinate inputs."""
        try:
            lat = float(self.latitude_input.text())
            lon = float(self.longitude_input.text())
            # Update map
            self.map_view.set_marker_location(lat, lon)
            # Perform zone lookup for coordinates
            self._lookup_zones_for_coordinates(lat, lon)
        except ValueError:
            # Optionally show error or just ignore invalid input until valid
            pass
    
    def _lookup_zones_for_coordinates(self, lat: float, lon: float):
        """Lookup wind, seismic zones and temperature for given coordinates and update UI."""
        zone_data = get_zones_for_coordinates(lat, lon)
        temp_data = get_temperature_for_coordinates(lat, lon)
        # Convert to weather dict format for _update_irc_values
        weather = {
            "wind_speed": zone_data.get("wind_Vb"),
            "zone": zone_data.get("seismic_zone"),
            "z_value": zone_data.get("zone_factor"),
            "max_temp": temp_data.get("max_temp"),
            "min_temp": temp_data.get("min_temp"),
        }
        global LAST_CUSTOM_WEATHER_DATA
        self.custom_weather_data = None 
        LAST_CUSTOM_WEATHER_DATA = None
        self._update_irc_values(weather)
    
    def _on_state_changed(self, state_name):
        districts = get_station_list(state_name, include_placeholder=True)
        self.district_combo.blockSignals(True) # Prevent premature triggering
        self.district_combo.clear()
        self.district_combo.addItems(districts)
        self.district_combo.blockSignals(False)
        self._update_irc_values(None) # Clear values on state change

    def _on_district_changed(self, district_name):
        if not district_name or district_name == "Select District":
            self._update_irc_values(None)
            return
        
        state = self.state_combo.currentText()
        if not state or state == "Select State":
            return # Should not happen if logic is correct
            
        weather = get_weather(state, district_name)
        # Clear custom data if user selects a new district, implying they want database values
        global LAST_CUSTOM_WEATHER_DATA
        self.custom_weather_data = None 
        LAST_CUSTOM_WEATHER_DATA = None
        self._update_irc_values(weather)

    def _open_custom_dialog(self):
        dlg = CustomWeatherDataDialog(self, self.custom_weather_data)
        if dlg.exec() == QDialog.Accepted:
            self.custom_weather_data = dlg.get_data()
            global LAST_CUSTOM_WEATHER_DATA
            LAST_CUSTOM_WEATHER_DATA = self.custom_weather_data
            self._update_irc_values(self.custom_weather_data)

    def _update_irc_values(self, weather):
        if not weather:
            self.wind_speed_label.setText("Basic Wind Speed (m/sec): —")
            self.seismic_zone_label.setText("Seismic Zone: —    Z = —")
            self.temp_label.setText("Shade Air Temperature (°C): — / —")
            return

        wind_txt = "—" if weather.get("wind_speed") is None else f"{weather['wind_speed']}"
        zone_txt = weather.get("zone") if weather.get("zone") else "—"
        z_val = weather.get("z_value")
        z_txt = "—" if z_val is None else f"{z_val}"
        if not z_txt or z_txt == "None": z_txt = "—"

        max_temp = weather.get("max_temp")
        min_temp = weather.get("min_temp")
        max_txt = "—" if max_temp is None else f"{max_temp}"
        min_txt = "—" if min_temp is None else f"{min_temp}"

        self.wind_speed_label.setText(f"Basic Wind Speed (m/sec): {wind_txt}")
        self.seismic_zone_label.setText(f"Seismic Zone: {zone_txt}    Z = {z_txt}")
        self.temp_label.setText(f"Shade Air Temperature (°C): {max_txt} / {min_txt}")

    def get_selected_location(self):
        result = {'method': None, 'data': {}}

        if self.method_radio_location.isChecked():
            result['method'] = 'location_name'
            result['data'] = {
                'state': self.state_combo.currentText(),
                'district': self.district_combo.currentText()
            }
        elif self.method_radio_map.isChecked():
            result['method'] = 'map'
            # Both map clicks and manual coordinate entry populate these fields
            result['data'] = {
                'latitude': self.latitude_input.text(),
                'longitude': self.longitude_input.text()
            }
        
        # Helper to merge custom weather data if present
        if self.custom_weather_data:
            result['custom_weather_data'] = self.custom_weather_data

        return result
