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


class WindLoadTab(QWidget):
    """Wind Load tab content extracted from LoadingTab."""

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self._build_ui()

    def _build_ui(self):
        owner = self.owner

        self.setStyleSheet("background-color: #f5f5f5;")
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(12, 12, 12, 12)
        page_layout.setSpacing(12)

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(16)

        left_card = owner._create_card()
        left_card.setStyleSheet("QFrame { border: 1px solid #b2b2b2; border-radius: 10px; background-color: #ffffff; }")
        left_card_layout = QVBoxLayout(left_card)
        left_card_layout.setContentsMargins(0, 0, 0, 0)
        left_card_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
            "QScrollArea > QWidget > QWidget { background: transparent; }"
        )

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: #ffffff;")
        left_layout = QVBoxLayout(scroll_content)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(12)

        label_style = "font-size: 11px; color: #3a3a3a; background: transparent; border: none;"
        field_width = 120

        wind_inputs_box = QFrame()
        wind_inputs_box.setStyleSheet("QFrame { border: 1px solid #b2b2b2; border-radius: 8px; background-color: #ffffff; }")
        wind_inputs_layout = QVBoxLayout(wind_inputs_box)
        wind_inputs_layout.setContentsMargins(12, 12, 12, 12)
        wind_inputs_layout.setSpacing(10)

        wind_title = QLabel("Wind Load (WL) Inputs for Evaluation per IRC6")
        wind_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #2b2b2b; background: transparent; border: none;")
        wind_inputs_layout.addWidget(wind_title)

        wind_grid = QGridLayout()
        wind_grid.setContentsMargins(0, 4, 0, 0)
        wind_grid.setHorizontalSpacing(12)
        wind_grid.setVerticalSpacing(8)
        wind_grid.setColumnMinimumWidth(0, 220)

        row = 0

        def add_line(label_text, attr_name, is_combo=False, items=None, placeholder=None, enable_on_custom=False):
            nonlocal row
            lbl = QLabel(label_text)
            lbl.setStyleSheet(label_style)
            widget = QComboBox() if is_combo else QLineEdit()
            if is_combo and items:
                widget.addItems(items)
            if placeholder and not is_combo:
                widget.setPlaceholderText(placeholder)
            widget.setFixedWidth(field_width)
            apply_field_style(widget)
            wind_grid.addWidget(lbl, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
            wind_grid.addWidget(widget, row, 1, Qt.AlignLeft)
            setattr(owner, attr_name, widget)
            row += 1
            return widget

        add_line("Basic Wind Speed (m/s):", "basic_wind_speed_input")
        add_line("Average Exposed Height (m):", "avg_exposed_height_input")
        add_line("Type of Terrain:", "terrain_type_combo", is_combo=True, items=["Plain", "Hilly", "Coastal"])
        add_line("Site Topography:", "site_topography_combo", is_combo=True, items=["Flat", "Hilly", "Ridge", "Valley"])
        owner.gust_factor_combo = add_line("Gust Factor, G:", "gust_factor_combo", is_combo=True, items=["Automatic", "Custom"], enable_on_custom=True)
        owner.gust_factor_value = add_line("", "gust_factor_value", placeholder="Value")
        owner.gust_factor_value.setEnabled(False)
        owner.drag_coeff_combo = add_line("Drag Coefficient, CD:", "drag_coeff_combo", is_combo=True, items=["Automatic", "Custom"], enable_on_custom=True)
        owner.drag_coeff_value = add_line("", "drag_coeff_value", placeholder="Custom Value")
        owner.drag_coeff_value.setEnabled(False)
        owner.drag_coeff_ll_combo = add_line("Drag Coefficient against Live Load, CDLL:", "drag_coeff_ll_combo", is_combo=True, items=["Automatic", "Custom"], enable_on_custom=True)
        owner.drag_coeff_ll_value = add_line("", "drag_coeff_ll_value", placeholder="Value")
        owner.drag_coeff_ll_value.setEnabled(False)
        owner.lift_coeff_combo = add_line("Lift Coefficient, CL:", "lift_coeff_combo", is_combo=True, items=["Automatic", "Custom"], enable_on_custom=True)
        owner.lift_coeff_value = add_line("", "lift_coeff_value", placeholder="Value")
        owner.lift_coeff_value.setEnabled(False)
        owner.super_area_elev_combo = add_line("Superstructure Area in Elevation (m2):", "super_area_elev_combo", is_combo=True, items=["Automatic", "Custom"], enable_on_custom=True)
        owner.super_area_elev_value = add_line("", "super_area_elev_value", placeholder="Custom Value")
        owner.super_area_elev_value.setEnabled(False)
        owner.super_area_plain_combo = add_line("Superstructure Area in Plain (m2):", "super_area_plain_combo", is_combo=True, items=["Automatic", "Custom"], enable_on_custom=True)
        owner.super_area_plain_value = add_line("", "super_area_plain_value", placeholder="Custom Value")
        owner.super_area_plain_value.setEnabled(False)
        owner.exposed_frontal_area_combo = add_line("Exposed Frontal Area of Live Load (m2):", "exposed_frontal_area_combo", is_combo=True, items=["Automatic", "Custom"], enable_on_custom=True)
        owner.exposed_frontal_area_value = add_line("", "exposed_frontal_area_value", placeholder="Custom Value")
        owner.exposed_frontal_area_value.setEnabled(False)
        owner.wind_ecc_deck_combo = add_line("Wind Load Eccentricity from Top of Deck\n(m): Negative for below deck", "wind_ecc_deck_combo", is_combo=True, items=["Automatic", "Custom"], enable_on_custom=True)
        owner.wind_ecc_deck_value = add_line("", "wind_ecc_deck_value", placeholder="Value")
        owner.wind_ecc_deck_value.setEnabled(False)
        owner.wind_ll_ecc_combo = add_line("Wind on Live Load Eccentricity from Top\nof Deck (m):", "wind_ll_ecc_combo", is_combo=True, items=["Automatic", "Custom"], enable_on_custom=True)
        owner.wind_ll_ecc_value = add_line("", "wind_ll_ecc_value", placeholder="Value")
        owner.wind_ll_ecc_value.setEnabled(False)

        wind_inputs_layout.addLayout(wind_grid)
        left_layout.addWidget(wind_inputs_box)

        computed_box = QFrame()
        computed_box.setStyleSheet("QFrame { border: 1px solid #b2b2b2; border-radius: 8px; background-color: #ffffff; }")
        computed_layout = QGridLayout(computed_box)
        computed_layout.setContentsMargins(12, 12, 12, 12)
        computed_layout.setHorizontalSpacing(12)
        computed_layout.setVerticalSpacing(8)
        computed_layout.setColumnMinimumWidth(0, 220)

        computed_fields = [
            ("Hourly Mean Wind Speed (m/s):", "hourly_mean_wind"),
            ("Hourly Wind Pressure in N/m2:", "hourly_wind_pressure"),
            ("Transverse Wind Force in N:", "transverse_wind_force"),
            ("Longitudinal Wind Force in N:", "longitudinal_wind_force"),
            ("Vertical Wind Force in N:", "vertical_wind_force"),
            ("Transverse Wind Force on Live\nLoad in N:", "transverse_wind_ll"),
            ("Longitudinal Wind Force on Live\nLoad in N:", "longitudinal_wind_ll"),
        ]

        owner.wind_computed_fields = {}
        for idx, (label_text, field_name) in enumerate(computed_fields):
            lbl = QLabel(label_text)
            lbl.setStyleSheet(label_style)
            field = QLineEdit()
            field.setFixedWidth(field_width)
            field.setReadOnly(True)
            apply_field_style(field)
            computed_layout.addWidget(lbl, idx, 0, Qt.AlignLeft | Qt.AlignVCenter)
            computed_layout.addWidget(field, idx, 1, Qt.AlignLeft)
            owner.wind_computed_fields[field_name] = field

        left_layout.addWidget(computed_box)
        left_layout.addStretch()

        scroll.setWidget(scroll_content)
        left_card_layout.addWidget(scroll)

        right_card = owner._create_card()
        right_card.setStyleSheet("QFrame { border: 1px solid #9c9c9c; border-radius: 10px; background-color: #d4d4d4; }")
        right_card.setMinimumWidth(150)
        right_card.setMaximumWidth(200)
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(10)

        desc_title = QLabel("Description\nBox")
        desc_title.setAlignment(Qt.AlignCenter)
        desc_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #2b2b2b; background: transparent; border: none;")
        right_layout.addWidget(desc_title)
        right_layout.addStretch()

        content_row.addWidget(left_card, 3)
        content_row.addWidget(right_card, 1)

        page_layout.addLayout(content_row)

        owner.gust_factor_combo.currentTextChanged.connect(lambda t: owner.gust_factor_value.setEnabled(t == "Custom"))
        owner.drag_coeff_combo.currentTextChanged.connect(lambda t: owner.drag_coeff_value.setEnabled(t == "Custom"))
        owner.drag_coeff_ll_combo.currentTextChanged.connect(lambda t: owner.drag_coeff_ll_value.setEnabled(t == "Custom"))
        owner.lift_coeff_combo.currentTextChanged.connect(lambda t: owner.lift_coeff_value.setEnabled(t == "Custom"))
        owner.super_area_elev_combo.currentTextChanged.connect(lambda t: owner.super_area_elev_value.setEnabled(t == "Custom"))
        owner.super_area_plain_combo.currentTextChanged.connect(lambda t: owner.super_area_plain_value.setEnabled(t == "Custom"))
        owner.exposed_frontal_area_combo.currentTextChanged.connect(lambda t: owner.exposed_frontal_area_value.setEnabled(t == "Custom"))
        owner.wind_ecc_deck_combo.currentTextChanged.connect(lambda t: owner.wind_ecc_deck_value.setEnabled(t == "Custom"))
        owner.wind_ll_ecc_combo.currentTextChanged.connect(lambda t: owner.wind_ll_ecc_value.setEnabled(t == "Custom"))
