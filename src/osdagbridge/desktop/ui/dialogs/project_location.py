from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QWidget,
    QFrame, QPushButton, QComboBox, QSizePolicy, QSizeGrip,
    QRadioButton, QButtonGroup, QStackedWidget, QSpacerItem
)
from PySide6.QtCore import Qt
from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox, MessageBoxType
from osdagbridge.core.bridge_types.plate_girder.ui_fields_project_location import (
    get_state_list,
    get_station_list,
    get_default_location,
    get_weather,
)
from osdagbridge.desktop.ui.widgets.native_map import NativeMapWidget
from osdagbridge.core.data.project_location.zone_lookup import get_zones_for_coordinates, get_temperature_for_coordinates

# Session-level state to persist values across dialog open/close cycles
# so that reopening the dialog retains user-entered or looked-up data.
LAST_CUSTOM_WEATHER_DATA = None  # Custom data entered via the Custom Data dialog
LAST_WEATHER_DATA = None  # Looked-up or persisted weather data (wind, seismic, temp)
LAST_LOCATION_METHOD = None  # "location_name" or "map"
LAST_LOCATION_DATA = None  # {"state": ..., "district": ...} or {"latitude": ..., "longitude": ...}

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


class ProjectLocationDialog(QDialog):
    """Dialog for selecting project location with multiple input methods."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(780)
        self.setMinimumHeight(520)
        self.setObjectName("project_location_dialog")
        self.default_location = get_default_location()
        self._session_committed = False
        self._initial_session_state = None
        
        # Restore session-level state
        self.custom_weather_data = LAST_CUSTOM_WEATHER_DATA
        self._current_weather_data = LAST_WEATHER_DATA  # Track current displayed weather

        self.setStyleSheet("""
            QDialog#project_location_dialog {
                background-color: #ffffff;
                border: 1px solid #90AF13;
            }
            QLabel#headline { font-size: 15px; font-weight: 700; color: #2d2d2d; }
            QLabel#hint { color: #4a4a4a; }
            QLabel { color: #1f1f1f; }
            QRadioButton { font-size: 12px; color: #1f1f1f; }
            QRadioButton::indicator { width: 16px; height: 16px; }
            QRadioButton::indicator::unchecked { border: 2px solid #90AF13; border-radius: 9px; background: transparent; }
            QRadioButton::indicator::checked { border: 2px solid #90AF13; background: #90AF13; border-radius: 9px; }
            QCheckBox { font-size: 12px; color: #1f1f1f; }
            QPushButton#primary {
                background-color: #ffffff;
                color: #1f1f1f;
                border-radius: 6px;
                padding: 8px 18px;
                font-weight: 600;
            }
            QPushButton#primary:hover { background-color: #90AF13; }
            QPushButton#primary:pressed { background-color: #64850c; }
            QPushButton#ghost {
                background-color: #ffffff;
                color: #1d1d1d;
                border-radius: 6px;
                padding: 8px 14px;
                font-weight: 600;
            }
            QPushButton#ghost:hover { background-color: #90AF13; }
            QPushButton#ghost:pressed { background-color: #d9d9d9; }
        """)

        self._setup_ui()
        self._connect_signals()
        
        # Restore previous session state if available, otherwise apply defaults
        self._restore_session_state()
        self._capture_initial_session_state()

    def _capture_initial_session_state(self):
        """Capture module-level session state at dialog open time for cancel rollback."""
        self._initial_session_state = {
            "custom_weather": LAST_CUSTOM_WEATHER_DATA,
            "weather": LAST_WEATHER_DATA,
            "location_method": LAST_LOCATION_METHOD,
            "location_data": LAST_LOCATION_DATA,
        }

    def _restore_initial_session_state(self):
        """Restore module-level session state captured when dialog was opened."""
        global LAST_CUSTOM_WEATHER_DATA, LAST_WEATHER_DATA, LAST_LOCATION_METHOD, LAST_LOCATION_DATA
        if not self._initial_session_state:
            return

        LAST_CUSTOM_WEATHER_DATA = self._initial_session_state.get("custom_weather")
        LAST_WEATHER_DATA = self._initial_session_state.get("weather")
        LAST_LOCATION_METHOD = self._initial_session_state.get("location_method")
        LAST_LOCATION_DATA = self._initial_session_state.get("location_data")

    def accept(self):
        self._session_committed = True
        super().accept()

    def reject(self):
        if not self._session_committed:
            self._restore_initial_session_state()
        super().reject()

    def closeEvent(self, event):
        if not self._session_committed:
            self._restore_initial_session_state()
        super().closeEvent(event)
    
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

        self._add_method_toggle(main_layout)
        self._build_body(main_layout)
        self._add_footer_buttons(main_layout)
    
    def _add_code_selector(self, layout):
        self.code_widget = QWidget()
        row = QHBoxLayout(self.code_widget)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)
        code_label = QLabel("Design Code")
        code_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #2d2d2d;")
        self.code_combo = NoScrollComboBox()
        self.code_combo.addItems(["IRC 6 (2017)"])
        apply_field_style(self.code_combo)
        self.code_combo.setFixedWidth(200)
        row.addWidget(code_label)
        row.addWidget(self.code_combo)
        row.addStretch()
        layout.addWidget(self.code_widget)

    def _add_method_toggle(self, layout):
        bar = QHBoxLayout()
        bar.setSpacing(18)

        self.method_group = QButtonGroup(self)
        self.method_radio_location = QRadioButton("Enter Location Name")
        self.method_radio_map = QRadioButton("Select on Map") 
        self.method_custom_data = QRadioButton("Input Custom Data")

        for radio in (self.method_radio_location, self.method_radio_map, self.method_custom_data):
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

        self._add_code_selector(left_layout)

        self.method_stack = QStackedWidget()
        self._add_location_page()
        self._add_map_page()
        self._add_custom_data_page()
        self.method_stack.setCurrentIndex(0)
        left_layout.addWidget(self.method_stack)

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

        self.irc_title_label = QLabel("IRC 6 (2017) Values:")
        self.irc_title_label.setObjectName("valueTitle")
        right_layout.addWidget(self.irc_title_label)

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

        # Zone Legend (shown when overlay is active)
        self.legend_container = QWidget()
        self.legend_container.setVisible(False)
        legend_layout = QVBoxLayout(self.legend_container)
        legend_layout.setContentsMargins(0, 10, 0, 0)
        legend_layout.setSpacing(4)
        
        self.legend_title = QLabel("Legend:")
        self.legend_title.setStyleSheet("font-weight: 700; font-size: 11px; color: #2d2d2d; border: none;")
        legend_layout.addWidget(self.legend_title)
        
        self.legend_items_widget = QWidget()
        self.legend_items_layout = QVBoxLayout(self.legend_items_widget)
        self.legend_items_layout.setContentsMargins(0, 0, 0, 0)
        self.legend_items_layout.setSpacing(3)
        legend_layout.addWidget(self.legend_items_widget)
        
        right_layout.addWidget(self.legend_container)
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

        self.zone_overlay_combo = NoScrollComboBox()
        self.zone_overlay_combo.addItems(["None", "Seismic Zone", "Wind Zone"])

        self.map_view = NativeMapWidget()
        vbox.addWidget(self.map_view, 1)

        # Coordinate inputs
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

    def _add_custom_data_page(self):
        page = QWidget()
        vbox = QVBoxLayout(page)
        vbox.setContentsMargins(2, 2, 2, 2)
        vbox.setSpacing(10)

        label = QLabel("Enter Custom Weather Data")
        label.setObjectName("hint")
        label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        label.setStyleSheet("font-weight: 700; color: #2d2d2d;")
        vbox.addWidget(label)

        # Basic Wind Speed
        wind_row = QHBoxLayout()
        wind_row.setSpacing(10)
        wind_lbl = QLabel("Basic Wind Speed (m/s)")
        wind_lbl.setFixedWidth(200)
        self.custom_wind_input = QLineEdit()
        self.custom_wind_input.setPlaceholderText("e.g. 50")
        apply_field_style(self.custom_wind_input)
        wind_row.addWidget(wind_lbl)
        wind_row.addWidget(self.custom_wind_input)
        vbox.addLayout(wind_row)

        # Seismic Zone + Zone Factor
        zone_row = QHBoxLayout()
        zone_row.setSpacing(10)
        zone_lbl = QLabel("Seismic Zone")
        zone_lbl.setFixedWidth(200)
        self.custom_zone_combo = NoScrollComboBox()
        self.custom_zone_combo.addItems(["Select Zone", "II", "III", "IV", "V"])
        apply_field_style(self.custom_zone_combo)
        self.custom_zone_value = QLineEdit()
        self.custom_zone_value.setReadOnly(True)
        self.custom_zone_value.setPlaceholderText("Zone Factor (Z)")
        self.custom_zone_value.setFixedWidth(100)
        apply_field_style(self.custom_zone_value)
        self.custom_zone_value.setStyleSheet("""
            QLineEdit {
                padding: 1px 7px;
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                background-color: #f5f5f5;
                color: #707070;
            }
        """)
        _zone_to_z = {"II": "0.10", "III": "0.16", "IV": "0.24", "V": "0.36"}
        self.custom_zone_combo.currentTextChanged.connect(
            lambda text: self.custom_zone_value.setText(_zone_to_z.get(text, ""))
        )
        zone_row.addWidget(zone_lbl)
        zone_row.addWidget(self.custom_zone_combo, 1)
        zone_row.addWidget(self.custom_zone_value)
        vbox.addLayout(zone_row)

        # Shade Air Temperature
        temp_lbl = QLabel("Shade Air Temperature (°C)")
        vbox.addWidget(temp_lbl)
        temp_row = QHBoxLayout()
        temp_row.setSpacing(10)
        self.custom_max_temp = QLineEdit()
        self.custom_max_temp.setPlaceholderText("Max")
        apply_field_style(self.custom_max_temp)
        self.custom_min_temp = QLineEdit()
        self.custom_min_temp.setPlaceholderText("Min")
        apply_field_style(self.custom_min_temp)
        temp_row.addWidget(self.custom_max_temp)
        temp_row.addWidget(self.custom_min_temp)
        vbox.addLayout(temp_row)

        # Apply button
        apply_btn = QPushButton("Apply")
        apply_btn.setObjectName("primary")
        apply_btn.setCursor(Qt.PointingHandCursor)
        apply_btn.setAutoDefault(False)
        apply_btn.clicked.connect(self._apply_custom_data_inline)
        vbox.addWidget(apply_btn, 0, Qt.AlignLeft)

        vbox.addStretch()
        self.method_stack.addWidget(page)

    def _apply_custom_data_inline(self):
        """Validate and apply the inline custom data fields."""
        global LAST_CUSTOM_WEATHER_DATA, LAST_WEATHER_DATA, LAST_LOCATION_METHOD, LAST_LOCATION_DATA
        wind = self.custom_wind_input.text().strip()
        zone = self.custom_zone_combo.currentText()
        max_t = self.custom_max_temp.text().strip()
        min_t = self.custom_min_temp.text().strip()

        if not wind or not max_t or not min_t or zone == "Select Zone":
            CustomMessageBox(
                title="Incomplete Data",
                text="Please fill in all fields (Wind Speed, Seismic Zone, Max/Min Temperature).",
                dialogType=MessageBoxType.Warning
            ).exec()
            return

        _zone_to_z = {"II": "0.10", "III": "0.16", "IV": "0.24", "V": "0.36"}
        data = {
            "wind_speed": wind,
            "zone": zone,
            "z_value": _zone_to_z.get(zone, ""),
            "max_temp": max_t,
            "min_temp": min_t,
        }
        self.custom_weather_data = data
        LAST_CUSTOM_WEATHER_DATA = data
        LAST_WEATHER_DATA = data
        LAST_LOCATION_METHOD = None
        LAST_LOCATION_DATA = None
        self._current_weather_data = data
        self._update_irc_values(data)

    def validate_and_save(self):
        # If custom_data radio is selected, auto-apply first
        if self.method_custom_data.isChecked():
            self._apply_custom_data_inline()
            if not self._current_weather_data:
                return

        if not self._current_weather_data:
            CustomMessageBox(
                title="Incomplete Data",
                text="Please select a location either on the map or from the dropdown menu.",
                dialogType=MessageBoxType.Warning
            ).exec()
            return

        # Ensure all critical fields are present
        w = self._current_weather_data
        missing = []
        if not w.get("wind_speed") and w.get("wind_speed") != 0:
            missing.append("Wind Speed")
        if not w.get("zone"):
            missing.append("Seismic Zone")
        if w.get("max_temp") is None or w.get("min_temp") is None:
            missing.append("Temperature")
        if missing:
            CustomMessageBox(
                title="Incomplete Data",
                text=f"Missing data: {', '.join(missing)}.\nPlease select a different location or use Custom Data to enter values manually.",
                dialogType=MessageBoxType.Warning
            ).exec()
            return

        self.accept()

    def _add_footer_buttons(self, layout):
        footer = QHBoxLayout()
        footer.addStretch()

        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("primary")
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.setMinimumWidth(90)
        ok_btn.clicked.connect(self.validate_and_save)
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
        self.method_custom_data.toggled.connect(lambda: self._set_active_method("custom_data"))
        self.state_combo.currentTextChanged.connect(self._on_state_changed)
        # Auto-update on district change
        self.district_combo.currentTextChanged.connect(self._on_district_changed)
        
        # Enter key on coordinates updates map
        self.latitude_input.returnPressed.connect(self._sync_map_from_inputs)
        self.longitude_input.returnPressed.connect(self._sync_map_from_inputs)
        
        # Zone overlay dropdown
        self.zone_overlay_combo.currentTextChanged.connect(self._on_zone_overlay_changed)

    def _set_active_method(self, method):
        if method == "location_name" and self.method_radio_location.isChecked():
            self.method_stack.setCurrentIndex(0)
            self.code_widget.setVisible(True)
            self.latitude_input.setEnabled(False)
            self.longitude_input.setEnabled(False)
            self.state_combo.setEnabled(True)
            self.district_combo.setEnabled(True)
            self.map_view.setEnabled(False)
            self.irc_title_label.setText("IRC 6 (2017) Values:")
        elif method == "map" and self.method_radio_map.isChecked():
            self.method_stack.setCurrentIndex(1)
            self.code_widget.setVisible(True)
            self.latitude_input.setEnabled(True)
            self.longitude_input.setEnabled(True)
            self.state_combo.setEnabled(False)
            self.district_combo.setEnabled(False)
            self.map_view.setEnabled(True)
            self.irc_title_label.setText("IRC 6 (2017) Values:")
        elif method == "custom_data" and self.method_custom_data.isChecked():
            self.method_stack.setCurrentIndex(2)
            self.code_widget.setVisible(False)
            self.latitude_input.setEnabled(False)
            self.longitude_input.setEnabled(False)
            self.state_combo.setEnabled(False)
            self.district_combo.setEnabled(False)
            self.map_view.setEnabled(False)
            self.irc_title_label.setText("Custom Values:")
            # Pre-fill inline fields from any previously saved custom data
            if self.custom_weather_data:
                self.custom_wind_input.setText(str(self.custom_weather_data.get("wind_speed", "")))
                zone = self.custom_weather_data.get("zone", "")
                idx = self.custom_zone_combo.findText(zone)
                if idx >= 0:
                    self.custom_zone_combo.setCurrentIndex(idx)
                self.custom_max_temp.setText(str(self.custom_weather_data.get("max_temp", "")))
                self.custom_min_temp.setText(str(self.custom_weather_data.get("min_temp", "")))

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

    def _restore_session_state(self):
        """Restore previous session state or apply defaults if first open."""
        global LAST_LOCATION_METHOD, LAST_LOCATION_DATA, LAST_WEATHER_DATA

        if self.custom_weather_data:
            self._clear_map_selection()
            self._clear_location_selection()
            LAST_LOCATION_METHOD = None
            LAST_LOCATION_DATA = None
            self._current_weather_data = self.custom_weather_data
            self._update_irc_values(self.custom_weather_data)
            return

        if LAST_LOCATION_METHOD and LAST_LOCATION_DATA:
            # Restore the previously selected method
            if LAST_LOCATION_METHOD == "location_name":
                self.method_radio_location.setChecked(True)
                self._set_active_method("location_name")
                
                # Restore state and district
                self.state_combo.blockSignals(True)
                self.district_combo.blockSignals(True)
                
                state = LAST_LOCATION_DATA.get("state", "")
                district = LAST_LOCATION_DATA.get("district", "")
                
                if state:
                    idx = self.state_combo.findText(state)
                    if idx >= 0:
                        self.state_combo.setCurrentIndex(idx)
                        # Populate districts for selected state
                        districts = get_station_list(state, include_placeholder=True)
                        self.district_combo.clear()
                        self.district_combo.addItems(districts)
                
                if district:
                    idx = self.district_combo.findText(district)
                    if idx >= 0:
                        self.district_combo.setCurrentIndex(idx)
                
                self.state_combo.blockSignals(False)
                self.district_combo.blockSignals(False)
                
            elif LAST_LOCATION_METHOD == "map":
                self.method_radio_map.setChecked(True)
                self._set_active_method("map")
                
                # Restore coordinates
                lat = LAST_LOCATION_DATA.get("latitude", "")
                lon = LAST_LOCATION_DATA.get("longitude", "")
                
                if lat:
                    self.latitude_input.setText(str(lat))
                if lon:
                    self.longitude_input.setText(str(lon))
                
                # Update map marker if coordinates are valid
                try:
                    if lat and lon:
                        self.map_view.set_marker_location(float(lat), float(lon))
                except (ValueError, TypeError):
                    pass
            
            # Restore weather data (custom or looked-up)
            if self.custom_weather_data:
                self._update_irc_values(self.custom_weather_data)
            elif LAST_WEATHER_DATA:
                self._update_irc_values(LAST_WEATHER_DATA)
        else:
            # First time opening - apply defaults
            self._apply_default_location()
            self._set_active_method("location_name")

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
    
    def _on_zone_overlay_changed(self, text: str):
        """Handle zone overlay dropdown change."""
        overlay_map = {
            "None": "none",
            "Seismic Zone": "seismic",
            "Wind Zone": "wind"
        }
        overlay_type = overlay_map.get(text, "none")
        self.map_view.set_overlay_type(overlay_type, opacity=0.5)
        
        # Update legend
        self._update_zone_legend(overlay_type)
    
    def _update_zone_legend(self, overlay_type: str):
        """Update the legend display based on overlay type."""
        # Clear existing legend items
        while self.legend_items_layout.count():
            item = self.legend_items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if overlay_type == "none":
            self.legend_container.setVisible(False)
            return
        
        self.legend_container.setVisible(True)
        
        if overlay_type == "seismic":
            # Seismic zone legend colors (from the seismic map image)
            zones = [
                ("Zone II", "#a8d8f0"),   # Light blue
                ("Zone III", "#f5f5a0"),  # Light yellow
                ("Zone IV", "#90d090"),   # Light green
                ("Zone V", "#f0a060"),    # Orange
            ]
        elif overlay_type == "wind":
            # Wind zone legend colors (from the wind map image)
            zones = [
                ("56 m/s", "#f2b6c8"),  # Light pink
                ("50 m/s", "#e57373"),  # Red / salmon
                ("47 m/s", "#c6e6b8"),  # Light green
                ("44 m/s", "#cfe8f3"),  # Light blue / cyan
                ("39 m/s", "#fff3b0"),  # Pale yellow
                ("33 m/s", "#d6cfee"),  # Light lavender
            ]

        else:
            return
        
        for label_text, color in zones:
            self._add_legend_item(label_text, color)
    
    def _add_legend_item(self, label_text: str, color: str):
        """Add a single legend item with a colored box and label."""
        item_widget = QWidget()
        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(0, 0, 0, 0)
        item_layout.setSpacing(6)
        
        # Color box
        color_box = QLabel()
        color_box.setFixedSize(16, 12)
        color_box.setStyleSheet(f"background-color: {color}; border: 1px solid #888; border-radius: 2px;")
        item_layout.addWidget(color_box)
        
        # Label
        label = QLabel(label_text)
        label.setStyleSheet("font-size: 10px; color: #333; border: none;")
        item_layout.addWidget(label)
        item_layout.addStretch()
        
        self.legend_items_layout.addWidget(item_widget)
    
    def _clear_map_selection(self):
        """Clear map marker and coordinate inputs."""
        # Clear the map marker
        self.map_view.marker_lat = None
        self.map_view.marker_lon = None
        self.map_view.update()
        
        # Clear coordinate inputs
        self.latitude_input.clear()
        self.longitude_input.clear()
    
    def _clear_location_selection(self):
        """Reset location name dropdowns to default state."""
        # Block signals to prevent triggering data fetch
        self.state_combo.blockSignals(True)
        self.district_combo.blockSignals(True)
        
        # Reset to first item ("Select State")
        if self.state_combo.count() > 0:
            self.state_combo.setCurrentIndex(0)
        
        # Reset district to placeholder
        self.district_combo.clear()
        self.district_combo.addItems(["Select District"])
        
        self.state_combo.blockSignals(False)
        self.district_combo.blockSignals(False)
    
    def _lookup_zones_for_coordinates(self, lat: float, lon: float):
        """Lookup wind, seismic zones and temperature for given coordinates and update UI."""
        global LAST_CUSTOM_WEATHER_DATA, LAST_WEATHER_DATA, LAST_LOCATION_METHOD, LAST_LOCATION_DATA
        
        zone_data = get_zones_for_coordinates(lat, lon)
        temp_data = get_temperature_for_coordinates(lat, lon)
        # Assuming that valid locations within India will always have a seismic zone/wind speed
        missing_zone = not zone_data.get("seismic_zone")
        missing_wind = zone_data.get("wind_Vb") in (None, "")
        missing_max_temp = temp_data.get("max_temp") is None
        missing_min_temp = temp_data.get("min_temp") is None
        if missing_zone or missing_wind or missing_max_temp or missing_min_temp:
            CustomMessageBox(
                title="Location Error",
                text="Data for this location is not available.\n (Outside of India)",
                dialogType=MessageBoxType.Critical
            ).exec()
            # Clear the pin from the map
            self._clear_map_selection()
            # Clear IRC values
            self._update_irc_values(None)
            # Clear global session variables
            self.custom_weather_data = None
            LAST_CUSTOM_WEATHER_DATA = None
            LAST_WEATHER_DATA = None
            LAST_LOCATION_METHOD = None
            LAST_LOCATION_DATA = None
            self._current_weather_data = None
            return
        # Convert to weather dict format for _update_irc_values
        weather = {
            "wind_speed": zone_data.get("wind_Vb"),
            "zone": zone_data.get("seismic_zone"),
            "z_value": zone_data.get("zone_factor"),
            "max_temp": temp_data.get("max_temp"),
            "min_temp": temp_data.get("min_temp"),
        }
        
        # Clear location name selection since we're using map method
        self._clear_location_selection()
        
        self.custom_weather_data = None 
        LAST_CUSTOM_WEATHER_DATA = None
        
        # Save looked-up weather and location data
        LAST_WEATHER_DATA = weather
        LAST_LOCATION_METHOD = "map"
        LAST_LOCATION_DATA = {
            "latitude": self.latitude_input.text(),
            "longitude": self.longitude_input.text()
        }
        self._current_weather_data = weather
        self._update_irc_values(weather)
    
    def _on_state_changed(self, state_name):
        global LAST_WEATHER_DATA, LAST_LOCATION_METHOD, LAST_LOCATION_DATA

        districts = get_station_list(state_name, include_placeholder=True)
        self.district_combo.blockSignals(True) # Prevent premature triggering
        self.district_combo.clear()
        self.district_combo.addItems(districts)
        self.district_combo.blockSignals(False)
        self._current_weather_data = None
        LAST_WEATHER_DATA = None
        LAST_LOCATION_METHOD = None
        LAST_LOCATION_DATA = None
        self._update_irc_values(None) # Clear values on state change

    def _on_district_changed(self, district_name):
        global LAST_CUSTOM_WEATHER_DATA, LAST_WEATHER_DATA, LAST_LOCATION_METHOD, LAST_LOCATION_DATA

        if not district_name or district_name == "Select District":
            self.custom_weather_data = None
            LAST_CUSTOM_WEATHER_DATA = None
            LAST_WEATHER_DATA = None
            LAST_LOCATION_METHOD = None
            LAST_LOCATION_DATA = None
            self._current_weather_data = None
            self._update_irc_values(None)
            return
        
        state = self.state_combo.currentText()
        if not state or state == "Select State":
            return # Should not happen if logic is correct
            
        weather = get_weather(state, district_name)
        
        # If DB is missing zone/wind data, use lat/long to query shapefiles
        if weather and (not weather.get("zone") or not weather.get("wind_speed")):
            lat = weather.get("latitude")
            lon = weather.get("longitude")
            if lat is not None and lon is not None:
                # Use coordinates to fetch from shapefiles
                zone_data = get_zones_for_coordinates(float(lat), float(lon))
                
                # Fill in missing values
                if not weather.get("zone") and zone_data.get("seismic_zone"):
                    weather["zone"] = zone_data.get("seismic_zone")
                    if zone_data.get("zone_factor"):
                        weather["z_value"] = zone_data.get("zone_factor")
                
                if not weather.get("wind_speed") and zone_data.get("wind_Vb"):
                     weather["wind_speed"] = zone_data.get("wind_Vb")
        
        # Clear map selection since we're using location name method
        self._clear_map_selection()
        
        # Clear custom data if user selects a new district, implying they want database values
        self.custom_weather_data = None 
        LAST_CUSTOM_WEATHER_DATA = None
        
        # Save looked-up weather and location data
        LAST_WEATHER_DATA = weather
        LAST_LOCATION_METHOD = "location_name"
        LAST_LOCATION_DATA = {
            "state": state,
            "district": district_name
        }
        self._current_weather_data = weather
        self._update_irc_values(weather)


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

    # To extract the location selected in popup
    def get_selected_location(self):
        result = {'method': None, 'data': {}, 'weather_data': None}

        if self.method_radio_location.isChecked():
            result['method'] = 'location_name'
            result['data'] = {
                'state': self.state_combo.currentText(),
                'district': self.district_combo.currentText()
            }
        elif self.method_radio_map.isChecked():
            result['method'] = 'map'
            result['data'] = {
                'latitude': self.latitude_input.text(),
                'longitude': self.longitude_input.text()
            }
        elif self.method_custom_data.isChecked():
            result['method'] = 'custom_data'
            result['data'] = {}
        
        # Include weather data (custom or looked-up) for backend calculations
        if self.custom_weather_data:
            result['weather_data'] = self.custom_weather_data
        elif self._current_weather_data:
            result['weather_data'] = self._current_weather_data
        
        # Deprecated: kept for backward compatibility
        if self.custom_weather_data:
            result['custom_weather_data'] = self.custom_weather_data

        return result