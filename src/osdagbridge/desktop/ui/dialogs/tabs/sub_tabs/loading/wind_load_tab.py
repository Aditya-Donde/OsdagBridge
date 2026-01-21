from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QFrame,
    QGridLayout,
    QScrollArea,
)

from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style

IRC_WIND_LOAD_DEFAULTS = {
    "avg_exposed_height": "10",
    "terrain_type": "Plain Terrain",
    "site_topography": "Flat",
    "gust_factor_mode": "Automatic",
    "gust_factor_value": "2",
    "drag_coeff_mode": "Automatic",
    "drag_coeff_ll_mode": "Automatic",
    "drag_coeff_ll_value": "1.2",
    "lift_coeff_mode": "Automatic",
    "lift_coeff_value": "0.75",
    "wind_ecc_deck_mode": "Automatic",
}


class WindLoadTab(QWidget):
    """Wind Load tab content extracted from LoadingTab."""

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self._build_ui()

    def _build_ui(self):
        owner = self.owner

        self.setStyleSheet("background-color: #f5f5f5;")
        
        # Main layout with scroll area
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { background-color: #f5f5f5; border: none; }")

        # Scrollable content widget
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: #f5f5f5;")
        page_layout = QVBoxLayout(scroll_content)
        page_layout.setContentsMargins(12, 12, 12, 12)
        page_layout.setSpacing(12)

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(16)

        # ============ LEFT CARD ============
        left_card = owner._create_card()
        left_card.setStyleSheet("QFrame { border: 1px solid #b2b2b2; border-radius: 10px; background-color: #ffffff; }")
        left_card_layout = QVBoxLayout(left_card)
        left_card_layout.setContentsMargins(0, 0, 0, 0)
        left_card_layout.setSpacing(0)

        content_wrapper = QWidget()
        content_wrapper.setStyleSheet("background-color: #ffffff;")
        left_layout = QVBoxLayout(content_wrapper)
        left_layout.setContentsMargins(14, 14, 14, 14)
        left_layout.setSpacing(12)

        label_style = "font-size: 11px; font-weight: 600; color: #3a3a3a; background: transparent; border: none;"
        field_width = 140
        combo_width = 140

        # ============ WIND INPUTS BOX ============
        wind_inputs_box = QFrame()
        wind_inputs_box.setStyleSheet("""
            QFrame {
                border: 1px solid #9c9c9c;
                border-radius: 6px;
                background-color: #ffffff;
                padding: 0px;
            }
        """)
        wind_inputs_layout = QVBoxLayout(wind_inputs_box)
        wind_title = QLabel("Wind Load (WL) Inputs:")
        wind_title.setStyleSheet("""
            font-size: 12px;
            font-weight: 700;
            color: #3a3a3a;
            background: transparent;
            border: none;
        """)
        wind_inputs_layout.addWidget(wind_title)

        wind_inputs_layout.setContentsMargins(12, 12, 12, 12)
        wind_inputs_layout.setSpacing(14)

        def add_input_row(label_text, attr_name, is_combo=False, items=None, placeholder=None, width_override=None):
            """Add a single input row with label and field"""
            row_layout = QHBoxLayout()
            row_layout.setSpacing(10)
            
            lbl = QLabel(label_text)
            lbl.setStyleSheet(label_style)
            lbl.setMinimumWidth(260)
            
            if is_combo:
                widget = QComboBox()
                widget.setFixedWidth(width_override if width_override else combo_width)
                if items:
                    widget.addItems(items)
            else:
                widget = QLineEdit()
                widget.setFixedWidth(width_override if width_override else field_width)
                if placeholder:
                    widget.setPlaceholderText(placeholder)
            
            widget.setFixedHeight(28)
            apply_field_style(widget)
            
            row_layout.addWidget(lbl)
            row_layout.addWidget(widget)
            row_layout.addStretch()
            
            wind_inputs_layout.addLayout(row_layout)
            setattr(owner, attr_name, widget)
            return widget

        def add_dual_input_row(label_text, combo_attr, value_attr, placeholder="Custom Value"):
            """Add a row with combo + value field"""
            row_layout = QHBoxLayout()
            row_layout.setSpacing(10)
            
            lbl = QLabel(label_text)
            lbl.setStyleSheet(label_style)
            lbl.setMinimumWidth(260)
            
            combo = QComboBox()
            combo.addItems(["Automatic", "Custom"])
            combo.setFixedWidth(combo_width)
            combo.setFixedHeight(28)
            apply_field_style(combo)
            
            value_field = QLineEdit()
            value_field.setPlaceholderText(placeholder)
            value_field.setFixedWidth(field_width)
            value_field.setFixedHeight(28)
            value_field.setEnabled(False)
            apply_field_style(value_field)
            
            row_layout.addWidget(lbl)
            row_layout.addWidget(combo)
            row_layout.addWidget(value_field)
            row_layout.addStretch()
            
            wind_inputs_layout.addLayout(row_layout)
            setattr(owner, combo_attr, combo)
            setattr(owner, value_attr, value_field)
            return combo, value_field

        # Basic inputs
        add_input_row("Basic Wind Speed (m/s):", "basic_wind_speed_input")
        avg_height = add_input_row("Average Exposed Height (m):", "avg_exposed_height_input", placeholder="10")
        avg_height.setText("10")
        
        add_input_row("Type of Terrain:", "terrain_type_combo", is_combo=True, 
                     items=["Plain Terrain", "Terrain with Obstructions"])
        owner.terrain_type_combo.setCurrentText("Plain Terrain")
        
        add_input_row("Site Topography:", "site_topography_combo", is_combo=True,
                     items=["Flat", "Hill, ridge, escarpment or cliff"])
        owner.site_topography_combo.setCurrentText("Flat")

        # Coefficients with dual inputs
        owner.gust_factor_combo, owner.gust_factor_value = add_dual_input_row(
            "Gust Factor, G:", "gust_factor_combo", "gust_factor_value", "2"
        )
        owner.gust_factor_combo.setCurrentText("Automatic")
        owner.gust_factor_value.setText("2")

        owner.drag_coeff_combo, owner.drag_coeff_value = add_dual_input_row(
            "Drag Coefficient, CD:", "drag_coeff_combo", "drag_coeff_value"
        )

        owner.drag_coeff_ll_combo, owner.drag_coeff_ll_value = add_dual_input_row(
            "Drag Coefficient against Live Load, CDLL:", "drag_coeff_ll_combo", 
            "drag_coeff_ll_value", "1.2"
        )
        owner.drag_coeff_ll_value.setText("1.2")

        owner.lift_coeff_combo, owner.lift_coeff_value = add_dual_input_row(
            "Lift Coefficient, CL:", "lift_coeff_combo", "lift_coeff_value", "0.75"
        )
        owner.lift_coeff_value.setText("0.75")

        # Area inputs
        owner.super_area_elev_combo, owner.super_area_elev_value = add_dual_input_row(
            "Superstructure Area in Elevation (m²):", "super_area_elev_combo", 
            "super_area_elev_value"
        )

        owner.super_area_plain_combo, owner.super_area_plain_value = add_dual_input_row(
            "Superstructure Area in Plain (m²):", "super_area_plain_combo", 
            "super_area_plain_value"
        )

        owner.exposed_frontal_area_combo, owner.exposed_frontal_area_value = add_dual_input_row(
            "Exposed Frontal Area of Live Load (m²):", "exposed_frontal_area_combo", 
            "exposed_frontal_area_value"
        )

        # Eccentricity inputs
        owner.wind_ecc_deck_combo, owner.wind_ecc_deck_value = add_dual_input_row(
            "Wind Load Eccentricity from Top of Deck (m):", "wind_ecc_deck_combo", 
            "wind_ecc_deck_value", "Custom Value"
        )

        owner.wind_ll_ecc_combo, owner.wind_ll_ecc_value = add_dual_input_row(
            "Wind on Live Load Eccentricity from Top of Deck (m):", "wind_ll_ecc_combo", 
            "wind_ll_ecc_value", "Custom Value"
        )

        left_layout.addWidget(wind_inputs_box)

        # ============ COMPUTED VALUES BOX ============
        computed_box = QFrame()
        computed_box.setStyleSheet("""
            QFrame {
                border: 1px solid #9c9c9c;
                border-radius: 6px;
                background-color: #ffffff;
                padding: 0px;
            }
        """)
        computed_box_layout = QVBoxLayout(computed_box)
        computed_box_layout.setContentsMargins(12, 12, 12, 12)
        computed_box_layout.setSpacing(14)

        # Add "Computed Values" title
        computed_title = QLabel("Computed Values")
        computed_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #3a3a3a; background: transparent; border: none;")
        computed_box_layout.addWidget(computed_title)

        computed_fields = [
            ("Hourly Mean Wind Speed (m/s):", "hourly_mean_wind"),
            ("Hourly Wind Pressure N/m²:", "hourly_wind_pressure"),
            ("Transverse Wind Force N:", "transverse_wind_force"),
            ("Longitudinal Wind Force N:", "longitudinal_wind_force"),
            ("Vertical Wind Force N:", "vertical_wind_force"),
            ("Transverse Wind Force on Live Load N:", "transverse_wind_ll"),
            ("Longitudinal Wind Force on Live Load N:", "longitudinal_wind_ll"),
        ]

        owner.wind_computed_fields = {}
        for label_text, field_name in computed_fields:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(10)
            
            lbl = QLabel(label_text)
            lbl.setStyleSheet(label_style)
            lbl.setMinimumWidth(260)
            
            field = QLineEdit()
            field.setFixedWidth(field_width)
            field.setFixedHeight(28)
            field.setReadOnly(True)
            field.setStyleSheet("""
                QLineEdit {
                    background-color: #f0f0f0;
                    border: 1px solid #8a8a8a;
                    border-radius: 5px;
                    padding: 5px 8px;
                    color: #5a5a5a;
                    font-size: 11px;
                }
            """)
            
            row_layout.addWidget(lbl)
            row_layout.addWidget(field)
            row_layout.addStretch()
            
            computed_box_layout.addLayout(row_layout)
            owner.wind_computed_fields[field_name] = field

        left_layout.addWidget(computed_box)
        left_layout.addStretch()
        left_card_layout.addWidget(content_wrapper)

        # ============ RIGHT CARD - Description Box ============
        right_card = owner._create_card()
        right_card.setStyleSheet("QFrame { border: 1px solid #9c9c9c; border-radius: 10px; background-color: #d4d4d4; }")
        right_card.setMinimumWidth(260)
        right_card.setMinimumHeight(420)
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(10)

        desc_title = QLabel("Description Box")
        desc_title.setAlignment(Qt.AlignCenter)
        desc_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #000000; background: transparent; border: none;")
        right_layout.addWidget(desc_title)

        desc_text = QLabel(
            "Wind load calculations per IRC 6 specifications.\n\n"
            "The basic wind speed should be obtained from relevant meteorological data.\n\n"
            "Gust factor accounts for wind fluctuations.\n\n"
            "Note: Wind load eccentricity values should be negative for positions below the deck."
        )
        desc_text.setWordWrap(True)
        desc_text.setStyleSheet("font-size: 11px; color: #4b4b4b; background: transparent; border: none;")
        right_layout.addWidget(desc_text)
        right_layout.addStretch()

        content_row.addWidget(left_card, 3)
        content_row.addWidget(right_card, 2)

        page_layout.addLayout(content_row)

        # Set scroll content and add to main layout
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # Connect signals
        owner.gust_factor_combo.currentTextChanged.connect(lambda t: owner.gust_factor_value.setEnabled(t == "Custom"))
        owner.drag_coeff_combo.currentTextChanged.connect(lambda t: owner.drag_coeff_value.setEnabled(t == "Custom"))
        owner.drag_coeff_ll_combo.currentTextChanged.connect(lambda t: owner.drag_coeff_ll_value.setEnabled(t == "Custom"))
        owner.lift_coeff_combo.currentTextChanged.connect(lambda t: owner.lift_coeff_value.setEnabled(t == "Custom"))
        owner.super_area_elev_combo.currentTextChanged.connect(lambda t: owner.super_area_elev_value.setEnabled(t == "Custom"))
        owner.super_area_plain_combo.currentTextChanged.connect(lambda t: owner.super_area_plain_value.setEnabled(t == "Custom"))
        owner.exposed_frontal_area_combo.currentTextChanged.connect(lambda t: owner.exposed_frontal_area_value.setEnabled(t == "Custom"))
        owner.wind_ecc_deck_combo.currentTextChanged.connect(lambda t: owner.wind_ecc_deck_value.setEnabled(t == "Custom"))
        owner.wind_ll_ecc_combo.currentTextChanged.connect(lambda t: owner.wind_ll_ecc_value.setEnabled(t == "Custom"))

        self.reset_defaults()

    def _block(self, widgets, block=True):
        """Temporarily block signals for a list of widgets"""
        for w in widgets:
            if w is not None:
                w.blockSignals(block)

    def reset_defaults(self):
        """Reset Wind Load inputs to IRC default values"""

        # Block signals to avoid auto-enabling
        self._block([
            self.owner.gust_factor_combo,
            self.owner.drag_coeff_combo,
            self.owner.drag_coeff_ll_combo,
            self.owner.lift_coeff_combo,
            self.owner.super_area_elev_combo,
            self.owner.super_area_plain_combo,
            self.owner.exposed_frontal_area_combo,
            self.owner.wind_ecc_deck_combo,
            self.owner.wind_ll_ecc_combo,
        ], True)

        # Simple fields
        self.owner.avg_exposed_height_input.setText("10")
        self.owner.terrain_type_combo.setCurrentText("Plain Terrain")
        self.owner.site_topography_combo.setCurrentText("Flat")

        # Gust factor
        self.owner.gust_factor_combo.setCurrentText("Automatic")
        self.owner.gust_factor_value.setText("2")
        self.owner.gust_factor_value.setEnabled(False)

        # Drag coefficient
        self.owner.drag_coeff_combo.setCurrentText("Automatic")
        self.owner.drag_coeff_value.clear()
        self.owner.drag_coeff_value.setEnabled(False)

        # Drag coeff against live load
        self.owner.drag_coeff_ll_combo.setCurrentText("Automatic")
        self.owner.drag_coeff_ll_value.clear()
        self.owner.drag_coeff_ll_value.setEnabled(False)

        # Lift coefficient
        self.owner.lift_coeff_combo.setCurrentText("Automatic")
        self.owner.lift_coeff_value.setText("0.75")
        self.owner.lift_coeff_value.setEnabled(False)

        # Areas
        self.owner.super_area_elev_combo.setCurrentText("Automatic")
        self.owner.super_area_elev_value.clear()
        self.owner.super_area_elev_value.setEnabled(False)

        self.owner.super_area_plain_combo.setCurrentText("Automatic")
        self.owner.super_area_plain_value.clear()
        self.owner.super_area_plain_value.setEnabled(False)

        self.owner.exposed_frontal_area_combo.setCurrentText("Automatic")
        self.owner.exposed_frontal_area_value.clear()
        self.owner.exposed_frontal_area_value.setEnabled(False)

        # Eccentricities
        self.owner.wind_ecc_deck_combo.setCurrentText("Automatic")
        self.owner.wind_ecc_deck_value.clear()
        self.owner.wind_ecc_deck_value.setEnabled(False)

        self.owner.wind_ll_ecc_combo.setCurrentText("Automatic")
        self.owner.wind_ll_ecc_value.clear()
        self.owner.wind_ll_ecc_value.setEnabled(False)

        # Unblock signals
        self._block([
            self.owner.gust_factor_combo,
            self.owner.drag_coeff_combo,
            self.owner.drag_coeff_ll_combo,
            self.owner.lift_coeff_combo,
            self.owner.super_area_elev_combo,
            self.owner.super_area_plain_combo,
            self.owner.exposed_frontal_area_combo,
            self.owner.wind_ecc_deck_combo,
            self.owner.wind_ll_ecc_combo,
        ], False)