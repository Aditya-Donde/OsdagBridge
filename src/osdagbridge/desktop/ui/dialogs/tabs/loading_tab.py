"""Auto-generated tab module extracted from additional_inputs."""
import sys
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTabBar, QLabel, QLineEdit,
    QComboBox, QGroupBox, QFormLayout, QPushButton, QScrollArea,
    QCheckBox, QMessageBox, QSizePolicy, QSpacerItem, QStackedWidget,
    QFrame, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QDialog, QSizePolicy, QSizeGrip
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QDoubleValidator, QIntValidator

from osdagbridge.core.utils.common import *
from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.dialogs.tabs.custom_vehicle_dialog import CustomVehicleDialog

def get_combobox_style():
    """Return the common stylesheet for dropdowns with the SVG icon from resources."""
    return """
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
        QComboBox:disabled{
            background: #f1f1f1;
            color: #666;
        }
    """


def get_lineedit_style():
    """Return the shared stylesheet for line edits in the section inputs."""
    return """
        QLineEdit {
            padding: 1px 7px;
            border: 1px solid #070707;
            border-radius: 6px;
            background-color: white;
            color: #000000;
            font-weight: normal;
        }
        QLineEdit:disabled{
            background: #f1f1f1;
            color: #666;
        }
        QLineEdit:hover {
            border: 1px solid #5d5d5d;
        }
    """


def apply_field_style(widget):
    """Apply the appropriate style to combo boxes and line edits."""
    widget.setMinimumHeight(28)
    if isinstance(widget, QComboBox):
        widget.setStyleSheet(get_combobox_style())
    elif isinstance(widget, QLineEdit):
        widget.setStyleSheet(get_lineedit_style())



class LoadingTab(QWidget):
    """Loading tab with permanent load layout and load-type subtabs"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.custom_vehicle_dialog = CustomVehicleDialog(self)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.load_tabs = QTabWidget()
        self.load_tabs.setDocumentMode(True)
        self.load_tabs.setStyleSheet(
            "QTabWidget::pane { border: none; background: #f5f5f5; }"
            "QTabBar::tab { background: #e8e8e8; color: #4b4b4b; border: 1px solid #cfcfcf;"
            " border-bottom: none; padding: 8px 20px; margin-right: 2px; min-width: 120px;"
            " font-size: 11px; }"
            "QTabBar::tab:selected { background: #90AF13; color: #ffffff; font-weight: bold; }"
            "QTabBar::tab:!selected { margin-top: 2px; }"
        )

        self.load_tabs.addTab(self._build_permanent_load_tab(), "Permanent Load")
        self.load_tabs.addTab(self._build_live_load_tab(), "Live Load")
        self.load_tabs.addTab(self._build_seismic_load_tab(), "Seismic Load")
        self.load_tabs.addTab(self._build_wind_load_tab(), "Wind Load")
        self.load_tabs.addTab(self._build_temperature_load_tab(), "Temperature Load")
        self.load_tabs.addTab(self._build_custom_load_tab(), "Custom Load")
        self.load_tabs.addTab(self._build_load_combination_tab(), "Load Combination")
        main_layout.addWidget(self.load_tabs)

    def _build_permanent_load_tab(self):
        page = QWidget()
        page.setStyleSheet("background-color: #f5f5f5;")
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(12, 12, 12, 12)
        page_layout.setSpacing(12)

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(16)

        left_card = self._create_card()
        left_card.setStyleSheet(
            "QFrame { border: 1px solid #b2b2b2; border-radius: 10px; background-color: #ffffff; }"
        )
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(16)

        self._add_load_section(left_layout, "Dead Load (DL):", [
            ("Include Member Self Weight:", self._create_yes_no_combo()),
            ("Self-weight factor:", self._create_line_edit()),
            ("Include Concrete Deck Weight:", self._create_yes_no_combo()),
        ])

        self._add_load_section(left_layout, "Dead Load for Surfacing (DW):", [
            ("Include Load from Wearing Course:", self._create_yes_no_combo()),
        ])

        self._add_load_section(left_layout, "Super-Imposed Dead Load (SIDL):", [
            ("Include Load from Crash Barrier:", self._create_yes_no_combo()),
            ("Include Load from Median:", self._create_yes_no_combo()),
            ("Include Load from Railing:", self._create_yes_no_combo()),
        ])

        left_layout.addStretch()

        right_card = self._create_card()
        right_card.setStyleSheet(
            "QFrame { border: 1px solid #9c9c9c; border-radius: 10px; background-color: #c8c8c8; }"
        )
        right_card.setMinimumWidth(270)
        right_card.setMinimumHeight(360)
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(18, 18, 18, 18)
        right_layout.setSpacing(12)
        description_label = QLabel("Description Box")
        description_label.setAlignment(Qt.AlignCenter)
        description_label.setStyleSheet("font-size: 12px; font-weight: 700; color: #000000;")
        description_label.setMinimumHeight(320)
        right_layout.addWidget(description_label)

        content_row.addWidget(left_card, 3)
        content_row.addWidget(right_card, 2)

        page_layout.addLayout(content_row)
        page_layout.addSpacing(4)
        return page

    def _build_live_load_tab(self):
        page = QWidget()
        page.setStyleSheet("background-color: #f5f5f5;")
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(12, 12, 12, 12)
        page_layout.setSpacing(12)

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(16)

        left_card = self._create_card()
        left_card.setStyleSheet("QFrame { border: 1px solid #b2b2b2; border-radius: 10px; background-color: #ffffff; }")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(14, 14, 14, 14)
        left_layout.setSpacing(8)

        # Title without box
        title = QLabel("Live Load (LL) Inputs:")
        title.setStyleSheet("font-size: 12px; font-weight: 700; color: #3a3a3a; background: transparent; border: none;")
        left_layout.addWidget(title)

        irc_vehicles = [
            "Class A", "Class 70R Wheeled", "Class 70R Tracked",
            "Class AA Wheeled", "Class AA Tracked", "Class SV", "Fatigue Truck"
        ]
        self._add_checkbox_section(left_layout, "Vehicles from IRC 6:", irc_vehicles)

        # Custom Vehicle header with Add/Edit buttons
        custom_header = QHBoxLayout()
        custom_header.setSpacing(8)
        custom_label = QLabel("Custom Vehicle:")
        custom_label.setStyleSheet("font-size: 12px; font-weight: 700; color: #3a3a3a; background: transparent; border: none;")
        custom_header.addWidget(custom_label)
        custom_header.addStretch()
        self.custom_vehicle_add_button = QPushButton("Add")
        self.custom_vehicle_edit_button = QPushButton("Edit")
        for btn in (self.custom_vehicle_add_button, self.custom_vehicle_edit_button):
            btn.setFixedWidth(50)
            btn.setStyleSheet(
                "QPushButton { background: #ffffff; color: #2f2f2f; border: 1px solid #7a7a7a; border-radius: 4px; padding: 4px 10px; }"
                "QPushButton:hover { background: #f0f0f0; }"
                "QPushButton:pressed { background: #e0e0e0; }"
            )
            custom_header.addWidget(btn)
        left_layout.addLayout(custom_header)

        # Vehicle Name 1 and 2 as simple checkbox rows (like reference image 2)
        self.custom_vehicle_checkboxes = []
        for index in range(2):
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)
            label = QLabel(f"Vehicle Name {index + 1}")
            label.setStyleSheet("font-size: 11px; font-style: italic; color: #4b4b4b; background: transparent; border: none;")
            checkbox = QCheckBox()
            checkbox.setChecked(False)
            row_layout.addWidget(label)
            row_layout.addStretch()
            row_layout.addWidget(checkbox)
            left_layout.addLayout(row_layout)
            self.custom_vehicle_checkboxes.append(checkbox)

        # Braking Load from Vehicles section - includes IRC vehicles + Vehicle Name 1/2
        braking_vehicles = irc_vehicles + ["Vehicle Name 1", "Vehicle Name 2"]
        self._add_checkbox_section(left_layout, "Braking Load from Vehicles:", braking_vehicles)

        # Bottom inputs with aligned widths
        input_width = 120

        # Eccentricity row
        ecc_row = QHBoxLayout()
        ecc_row.setSpacing(10)
        ecc_label = QLabel("Eccentricity from top of Deck (m):")
        ecc_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #3a3a3a; background: transparent; border: none;")
        ecc_label.setMinimumWidth(200)
        self.eccentricity_input = QLineEdit()
        self.eccentricity_input.setFixedWidth(input_width)
        apply_field_style(self.eccentricity_input)
        ecc_row.addWidget(ecc_label)
        ecc_row.addWidget(self.eccentricity_input)
        ecc_row.addStretch()
        left_layout.addLayout(ecc_row)

        # Footpath Pressure row with dropdown
        footpath_row = QHBoxLayout()
        footpath_row.setSpacing(10)
        footpath_label = QLabel("Footpath Pressure (kN/mm2 ):")
        footpath_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #3a3a3a; background: transparent; border: none;")
        footpath_label.setMinimumWidth(200)
        self.footpath_mode_combo = QComboBox()
        self.footpath_mode_combo.addItems(["Automatic", "User-defined"])
        self.footpath_mode_combo.setFixedWidth(input_width)
        apply_field_style(self.footpath_mode_combo)
        footpath_row.addWidget(footpath_label)
        footpath_row.addWidget(self.footpath_mode_combo)
        footpath_row.addStretch()
        left_layout.addLayout(footpath_row)

        # Value input below footpath (aligned with dropdown above)
        value_row = QHBoxLayout()
        value_row.setContentsMargins(0, 0, 0, 0)
        value_row.setSpacing(10)
        value_spacer = QLabel("")
        value_spacer.setMinimumWidth(200)
        self.footpath_value_input = QLineEdit()
        self.footpath_value_input.setPlaceholderText("Value")
        self.footpath_value_input.setFixedWidth(input_width)
        apply_field_style(self.footpath_value_input)
        value_row.addWidget(value_spacer)
        value_row.addWidget(self.footpath_value_input)
        value_row.addStretch()
        left_layout.addLayout(value_row)

        left_layout.addStretch()

        # Right description card
        right_card = self._create_card()
        right_card.setStyleSheet("QFrame { border: 1px solid #9c9c9c; border-radius: 10px; background-color: #d4d4d4; }")
        right_card.setMinimumWidth(260)
        right_card.setMinimumHeight(420)
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(10)

        # Description Box title - no box around it
        desc_label = QLabel("Description Box")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("font-size: 12px; font-weight: 700; color: #000000; background: transparent; border: none;")
        right_layout.addWidget(desc_label)

        description_text = (
            "211.2 The braking effect on a simply supported span or a continuous unit of spans "
            "or on any other type of bridge unit shall be assumed to have the following value:\n\n"
            "a) In the case of a single lane or a two lane bridge: twenty percent of the first train "
            "load plus ten percent of the load of the succeeding trains or part thereof, the train "
            "loads in one lane only being considered for the purpose of this subclause. Where the "
            "entire first train is not on the full span, the braking force shall be taken as equal to "
            "twenty percent of the loads actually on the span or continuous unit of spans.\n"
            "b) In the case of bridges having more than two lanes: as in (a) above for the first two "
            "lanes plus five percent of the loads on the lanes in excess of two."
        )
        description_label = QLabel(description_text)
        description_label.setWordWrap(True)
        description_label.setStyleSheet("font-size: 11px; color: #4b4b4b; background: transparent; border: none;")
        right_layout.addWidget(description_label)
        right_layout.addStretch()

        content_row.addWidget(left_card, 3)
        content_row.addWidget(right_card, 2)
        page_layout.addLayout(content_row)
        page_layout.addSpacing(4)

        self.custom_vehicle_add_button.clicked.connect(self.show_custom_vehicle_dialog)
        self.custom_vehicle_edit_button.clicked.connect(self.show_custom_vehicle_dialog)
        self.footpath_mode_combo.currentTextChanged.connect(self._on_footpath_mode_changed)
        self._on_footpath_mode_changed(self.footpath_mode_combo.currentText())

        return page

    def _build_seismic_load_tab(self):
        """Build the Seismic/Earthquake Load tab matching reference design"""
        page = QWidget()
        page.setStyleSheet("background-color: #f5f5f5;")
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(12, 12, 12, 12)
        page_layout.setSpacing(12)

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(16)

        # Left card with inputs
        left_card = self._create_card()
        left_card.setStyleSheet("QFrame { border: 1px solid #b2b2b2; border-radius: 10px; background-color: #ffffff; }")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(12)

        # Title
        title = QLabel("Seismic/Earthquake Load (EL) Inputs for Evaluation per IRC 6")
        title.setStyleSheet("font-size: 12px; font-weight: 700; color: #2b2b2b; background: transparent; border: none;")
        left_layout.addWidget(title)

        label_style = "font-size: 11px; color: #3a3a3a; background: transparent; border: none;"
        field_width = 120

        # ===== Seismic Inputs Box =====
        seismic_inputs_box = QFrame()
        seismic_inputs_box.setStyleSheet("QFrame { border: 1px solid #b2b2b2; border-radius: 8px; background-color: #ffffff; }")
        seismic_inputs_layout = QGridLayout(seismic_inputs_box)
        seismic_inputs_layout.setContentsMargins(12, 16, 12, 16)
        seismic_inputs_layout.setHorizontalSpacing(16)
        seismic_inputs_layout.setVerticalSpacing(6)
        seismic_inputs_layout.setColumnMinimumWidth(0, 200)

        row = 0
        field_height = 28

        # Seismic Zone
        lbl = QLabel("Seismic Zone:")
        lbl.setStyleSheet(label_style)
        lbl.setFixedHeight(field_height)
        self.seismic_zone_combo = QComboBox()
        self.seismic_zone_combo.addItems(["II", "III", "IV", "V"])
        self.seismic_zone_combo.setFixedSize(field_width, field_height)
        apply_field_style(self.seismic_zone_combo)
        seismic_inputs_layout.addWidget(lbl, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        seismic_inputs_layout.addWidget(self.seismic_zone_combo, row, 1, Qt.AlignLeft)
        row += 1

        # Importance Factor
        lbl = QLabel("Importance Factor:")
        lbl.setStyleSheet(label_style)
        lbl.setFixedHeight(field_height)
        self.importance_factor_input = QLineEdit()
        self.importance_factor_input.setText("1")
        self.importance_factor_input.setFixedSize(field_width, field_height)
        apply_field_style(self.importance_factor_input)
        seismic_inputs_layout.addWidget(lbl, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        seismic_inputs_layout.addWidget(self.importance_factor_input, row, 1, Qt.AlignLeft)
        row += 1

        # Type of Soil
        lbl = QLabel("Type of Soil:")
        lbl.setStyleSheet(label_style)
        lbl.setFixedHeight(field_height)
        self.soil_type_combo = QComboBox()
        self.soil_type_combo.addItems([
            "Type I – Rocky or Hard",
            "Type II – Medium Soil",
            "Type III – Soft Soil"
        ])
        self.soil_type_combo.setFixedSize(field_width + 30, field_height)
        apply_field_style(self.soil_type_combo)
        seismic_inputs_layout.addWidget(lbl, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        seismic_inputs_layout.addWidget(self.soil_type_combo, row, 1, Qt.AlignLeft)
        row += 1

        # Time Period
        lbl = QLabel("Time Period:")
        lbl.setStyleSheet(label_style)
        lbl.setFixedHeight(field_height)
        self.time_period_input = QLineEdit()
        self.time_period_input.setFixedSize(field_width, field_height)
        apply_field_style(self.time_period_input)
        seismic_inputs_layout.addWidget(lbl, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        seismic_inputs_layout.addWidget(self.time_period_input, row, 1, Qt.AlignLeft)
        row += 1

        # Damping Percentage
        lbl = QLabel("Damping Percentage:")
        lbl.setStyleSheet(label_style)
        lbl.setFixedHeight(field_height)
        self.damping_input = QLineEdit()
        self.damping_input.setText("2")
        self.damping_input.setFixedSize(field_width, field_height)
        apply_field_style(self.damping_input)
        seismic_inputs_layout.addWidget(lbl, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        seismic_inputs_layout.addWidget(self.damping_input, row, 1, Qt.AlignLeft)
        row += 1

        # Response Reduction Factor
        lbl = QLabel("Response Reduction Factor:")
        lbl.setStyleSheet(label_style)
        lbl.setFixedHeight(field_height)
        self.response_factor_combo = QComboBox()
        self.response_factor_combo.addItems(["1", "2", "3", "4", "5"])
        self.response_factor_combo.setCurrentText("1")
        self.response_factor_combo.setFixedSize(field_width, field_height)
        apply_field_style(self.response_factor_combo)
        seismic_inputs_layout.addWidget(lbl, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        seismic_inputs_layout.addWidget(self.response_factor_combo, row, 1, Qt.AlignLeft)
        row += 1

        # Dead Load for Seismic Force
        lbl = QLabel("Dead Load for Seismic Force (kN):")
        lbl.setStyleSheet(label_style)
        lbl.setFixedHeight(field_height)
        self.dead_load_seismic_combo = QComboBox()
        self.dead_load_seismic_combo.addItems(["Automatic", "Custom"])
        self.dead_load_seismic_combo.setFixedSize(field_width, field_height)
        apply_field_style(self.dead_load_seismic_combo)
        seismic_inputs_layout.addWidget(lbl, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        seismic_inputs_layout.addWidget(self.dead_load_seismic_combo, row, 1, Qt.AlignLeft)
        row += 1

        # Custom Value for Dead Load
        self.dead_load_custom_input = QLineEdit()
        self.dead_load_custom_input.setPlaceholderText("Custom Value")
        self.dead_load_custom_input.setFixedSize(field_width, field_height)
        self.dead_load_custom_input.setEnabled(False)
        apply_field_style(self.dead_load_custom_input)
        seismic_inputs_layout.addWidget(self.dead_load_custom_input, row, 1, Qt.AlignLeft)
        row += 1

        # Live Load for Seismic Force
        lbl = QLabel("Live Load for Seismic Force (kN):")
        lbl.setStyleSheet(label_style)
        lbl.setFixedHeight(field_height)
        self.live_load_seismic_combo = QComboBox()
        self.live_load_seismic_combo.addItems(["Automatic", "Custom"])
        self.live_load_seismic_combo.setFixedSize(field_width, field_height)
        apply_field_style(self.live_load_seismic_combo)
        seismic_inputs_layout.addWidget(lbl, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        seismic_inputs_layout.addWidget(self.live_load_seismic_combo, row, 1, Qt.AlignLeft)
        row += 1

        # Custom Value for Live Load
        self.live_load_custom_input = QLineEdit()
        self.live_load_custom_input.setPlaceholderText("Custom Value")
        self.live_load_custom_input.setFixedSize(field_width, field_height)
        self.live_load_custom_input.setEnabled(False)
        apply_field_style(self.live_load_custom_input)
        seismic_inputs_layout.addWidget(self.live_load_custom_input, row, 1, Qt.AlignLeft)

        left_layout.addWidget(seismic_inputs_box)

        # ===== Computed Values Box =====
        computed_box = QFrame()
        computed_box.setStyleSheet("QFrame { border: 1px solid #b2b2b2; border-radius: 8px; background-color: #ffffff; }")
        computed_layout = QGridLayout(computed_box)
        computed_layout.setContentsMargins(12, 16, 12, 16)
        computed_layout.setHorizontalSpacing(16)
        computed_layout.setVerticalSpacing(6)
        computed_layout.setColumnMinimumWidth(0, 200)

        computed_fields = [
            ("Zone Factor:", "zone_factor"),
            ("Spectral Acceleration Coefficient:", "spectral_coeff"),
            ("Horizontal Seismic Coefficient:", "horizontal_coeff"),
            ("Vertical Seismic Coefficient:", "vertical_coeff"),
        ]

        self.seismic_computed_fields = {}
        for idx, (label_text, field_name) in enumerate(computed_fields):
            lbl = QLabel(label_text)
            lbl.setStyleSheet(label_style)
            lbl.setFixedHeight(field_height)
            field = QLineEdit()
            field.setFixedSize(field_width, field_height)
            field.setReadOnly(True)
            apply_field_style(field)
            computed_layout.addWidget(lbl, idx, 0, Qt.AlignLeft | Qt.AlignVCenter)
            computed_layout.addWidget(field, idx, 1, Qt.AlignLeft)
            self.seismic_computed_fields[field_name] = field

        left_layout.addWidget(computed_box)
        left_layout.addStretch()

        # Right description card
        right_card = self._create_card()
        right_card.setStyleSheet("QFrame { border: 1px solid #9c9c9c; border-radius: 10px; background-color: #d4d4d4; }")
        right_card.setMinimumWidth(200)
        right_card.setMinimumHeight(400)
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(10)

        desc_title = QLabel("Description Box")
        desc_title.setAlignment(Qt.AlignCenter)
        desc_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #2b2b2b; background: transparent; border: none;")
        right_layout.addWidget(desc_title)

        desc_text = QLabel("Importance factor for normal, important, and critical bridges.")
        desc_text.setWordWrap(True)
        desc_text.setStyleSheet("font-size: 11px; color: #4b4b4b; background: transparent; border: none;")
        right_layout.addWidget(desc_text)
        right_layout.addStretch()

        content_row.addWidget(left_card, 3)
        content_row.addWidget(right_card, 2)

        page_layout.addLayout(content_row)

        # Connect signals for enabling/disabling custom inputs
        self.dead_load_seismic_combo.currentTextChanged.connect(self._on_dead_load_mode_changed)
        self.live_load_seismic_combo.currentTextChanged.connect(self._on_live_load_mode_changed)

        return page

    def _on_dead_load_mode_changed(self, mode):
        is_custom = mode == "Custom"
        self.dead_load_custom_input.setEnabled(is_custom)
        if not is_custom:
            self.dead_load_custom_input.clear()

    def _on_live_load_mode_changed(self, mode):
        is_custom = mode == "Custom"
        self.live_load_custom_input.setEnabled(is_custom)
        if not is_custom:
            self.live_load_custom_input.clear()

    def _add_load_section(self, parent_layout, title, rows):
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #3e3e3e; background: transparent; border: none;")
        parent_layout.addWidget(title_label)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        grid.setColumnMinimumWidth(0, 230)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)

        field_width = 170

        for row_index, (label_text, widget) in enumerate(rows):
            label = QLabel(label_text)
            label.setStyleSheet("font-size: 11px; color: #4b4b4b; background: transparent; border: none;")
            grid.addWidget(label, row_index, 0, Qt.AlignLeft | Qt.AlignVCenter)
            widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            if isinstance(widget, QComboBox):
                widget.setFixedWidth(field_width)
            elif isinstance(widget, QLineEdit):
                widget.setFixedWidth(field_width)
            grid.addWidget(widget, row_index, 1)

        parent_layout.addLayout(grid)

    def _add_checkbox_section(self, parent_layout, title, items):
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #3e3e3e; background: transparent; border: none;")
        parent_layout.addWidget(title_label)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        grid.setColumnStretch(0, 1)


        for row, name in enumerate(items):
            label = QLabel(name)
            # Make Vehicle Name entries italic
            if "Vehicle Name" in name:
                label.setStyleSheet("font-size: 11px; font-style: italic; color: #4b4b4b; background: transparent; border: none; padding: 0px;")
            else:
                label.setStyleSheet("font-size: 11px; color: #4b4b4b; background: transparent; border: none; padding: 0px;")
            checkbox = QCheckBox()
            checkbox.setChecked(False)
            grid.addWidget(label, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
            grid.addWidget(checkbox, row, 1, Qt.AlignRight | Qt.AlignVCenter)

        parent_layout.addLayout(grid)

    def _on_footpath_mode_changed(self, mode):
        is_custom = mode == "User-defined"
        self.footpath_value_input.setEnabled(is_custom)
        if not is_custom:
            self.footpath_value_input.clear()

    def show_custom_vehicle_dialog(self):
        self.custom_vehicle_dialog.show()
        self.custom_vehicle_dialog.raise_()
        self.custom_vehicle_dialog.activateWindow()

    def _create_yes_no_combo(self):
        combo = QComboBox()
        combo.addItems(VALUES_YES_NO)
        combo.setCurrentText("Yes")
        apply_field_style(combo)
        return combo

    def _create_line_edit(self):
        line_edit = QLineEdit()
        apply_field_style(line_edit)
        return line_edit

    def _create_card(self):
        card = QFrame()
        card.setStyleSheet("QFrame { border: 1px solid #cfcfcf; border-radius: 12px; background-color: #ffffff; }")
        return card

    def _build_wind_load_tab(self):
        """Build the Wind Load tab matching reference design"""
        page = QWidget()
        page.setStyleSheet("background-color: #f5f5f5;")
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(12, 12, 12, 12)
        page_layout.setSpacing(12)

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(16)

        # Left card with inputs - use scroll area for many fields
        left_card = self._create_card()
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

        # ===== Wind Load Inputs Box =====
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

        # Basic Wind Speed
        lbl = QLabel("Basic Wind Speed (m/s):")
        lbl.setStyleSheet(label_style)
        self.basic_wind_speed_input = QLineEdit()
        self.basic_wind_speed_input.setFixedWidth(field_width)
        apply_field_style(self.basic_wind_speed_input)
        wind_grid.addWidget(lbl, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        wind_grid.addWidget(self.basic_wind_speed_input, row, 1, Qt.AlignLeft)
        row += 1

        # Average Exposed Height
        lbl = QLabel("Average Exposed Height (m):")
        lbl.setStyleSheet(label_style)
        self.avg_exposed_height_input = QLineEdit()
        self.avg_exposed_height_input.setFixedWidth(field_width)
        apply_field_style(self.avg_exposed_height_input)
        wind_grid.addWidget(lbl, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        wind_grid.addWidget(self.avg_exposed_height_input, row, 1, Qt.AlignLeft)
        row += 1

        # Type of Terrain
        lbl = QLabel("Type of Terrain:")
        lbl.setStyleSheet(label_style)
        self.terrain_type_combo = QComboBox()
        self.terrain_type_combo.addItems(["Plain", "Hilly", "Coastal"])
        self.terrain_type_combo.setFixedWidth(field_width)
        apply_field_style(self.terrain_type_combo)
        wind_grid.addWidget(lbl, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        wind_grid.addWidget(self.terrain_type_combo, row, 1, Qt.AlignLeft)
        row += 1

        # Site Topography
        lbl = QLabel("Site Topography:")
        lbl.setStyleSheet(label_style)
        self.site_topography_combo = QComboBox()
        self.site_topography_combo.addItems(["Flat", "Hilly", "Ridge", "Valley"])
        self.site_topography_combo.setFixedWidth(field_width)
        apply_field_style(self.site_topography_combo)
        wind_grid.addWidget(lbl, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        wind_grid.addWidget(self.site_topography_combo, row, 1, Qt.AlignLeft)
        row += 1

        # Gust Factor, G
        lbl = QLabel("Gust Factor, G:")
        lbl.setStyleSheet(label_style)
        self.gust_factor_combo = QComboBox()
        self.gust_factor_combo.addItems(["Automatic", "Custom"])
        self.gust_factor_combo.setFixedWidth(field_width)
        apply_field_style(self.gust_factor_combo)
        wind_grid.addWidget(lbl, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        wind_grid.addWidget(self.gust_factor_combo, row, 1, Qt.AlignLeft)
        row += 1
        self.gust_factor_value = QLineEdit()
        self.gust_factor_value.setPlaceholderText("Value")
        self.gust_factor_value.setFixedWidth(field_width)
        self.gust_factor_value.setEnabled(False)
        apply_field_style(self.gust_factor_value)
        wind_grid.addWidget(self.gust_factor_value, row, 1, Qt.AlignLeft)
        row += 1

        # Drag Coefficient, CD
        lbl = QLabel("Drag Coefficient, CD:")
        lbl.setStyleSheet(label_style)
        self.drag_coeff_combo = QComboBox()
        self.drag_coeff_combo.addItems(["Automatic", "Custom"])
        self.drag_coeff_combo.setFixedWidth(field_width)
        apply_field_style(self.drag_coeff_combo)
        wind_grid.addWidget(lbl, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        wind_grid.addWidget(self.drag_coeff_combo, row, 1, Qt.AlignLeft)
        row += 1
        self.drag_coeff_value = QLineEdit()
        self.drag_coeff_value.setPlaceholderText("Custom Value")
        self.drag_coeff_value.setFixedWidth(field_width)
        self.drag_coeff_value.setEnabled(False)
        apply_field_style(self.drag_coeff_value)
        wind_grid.addWidget(self.drag_coeff_value, row, 1, Qt.AlignLeft)
        row += 1

        # Drag Coefficient against Live Load, CDLL
        lbl = QLabel("Drag Coefficient against Live Load, CDLL:")
        lbl.setStyleSheet(label_style)
        self.drag_coeff_ll_combo = QComboBox()
        self.drag_coeff_ll_combo.addItems(["Automatic", "Custom"])
        self.drag_coeff_ll_combo.setFixedWidth(field_width)
        apply_field_style(self.drag_coeff_ll_combo)
        wind_grid.addWidget(lbl, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        wind_grid.addWidget(self.drag_coeff_ll_combo, row, 1, Qt.AlignLeft)
        row += 1
        self.drag_coeff_ll_value = QLineEdit()
        self.drag_coeff_ll_value.setPlaceholderText("Value")
        self.drag_coeff_ll_value.setFixedWidth(field_width)
        self.drag_coeff_ll_value.setEnabled(False)
        apply_field_style(self.drag_coeff_ll_value)
        wind_grid.addWidget(self.drag_coeff_ll_value, row, 1, Qt.AlignLeft)
        row += 1

        # Lift Coefficient, CL
        lbl = QLabel("Lift Coefficient, CL:")
        lbl.setStyleSheet(label_style)
        self.lift_coeff_combo = QComboBox()
        self.lift_coeff_combo.addItems(["Automatic", "Custom"])
        self.lift_coeff_combo.setFixedWidth(field_width)
        apply_field_style(self.lift_coeff_combo)
        wind_grid.addWidget(lbl, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        wind_grid.addWidget(self.lift_coeff_combo, row, 1, Qt.AlignLeft)
        row += 1
        self.lift_coeff_value = QLineEdit()
        self.lift_coeff_value.setPlaceholderText("Value")
        self.lift_coeff_value.setFixedWidth(field_width)
        self.lift_coeff_value.setEnabled(False)
        apply_field_style(self.lift_coeff_value)
        wind_grid.addWidget(self.lift_coeff_value, row, 1, Qt.AlignLeft)
        row += 1

        # Superstructure Area in Elevation
        lbl = QLabel("Superstructure Area in Elevation (m2):")
        lbl.setStyleSheet(label_style)
        self.super_area_elev_combo = QComboBox()
        self.super_area_elev_combo.addItems(["Automatic", "Custom"])
        self.super_area_elev_combo.setFixedWidth(field_width)
        apply_field_style(self.super_area_elev_combo)
        wind_grid.addWidget(lbl, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        wind_grid.addWidget(self.super_area_elev_combo, row, 1, Qt.AlignLeft)
        row += 1
        self.super_area_elev_value = QLineEdit()
        self.super_area_elev_value.setPlaceholderText("Custom Value")
        self.super_area_elev_value.setFixedWidth(field_width)
        self.super_area_elev_value.setEnabled(False)
        apply_field_style(self.super_area_elev_value)
        wind_grid.addWidget(self.super_area_elev_value, row, 1, Qt.AlignLeft)
        row += 1

        # Superstructure Area in Plain
        lbl = QLabel("Superstructure Area in Plain (m2):")
        lbl.setStyleSheet(label_style)
        self.super_area_plain_combo = QComboBox()
        self.super_area_plain_combo.addItems(["Automatic", "Custom"])
        self.super_area_plain_combo.setFixedWidth(field_width)
        apply_field_style(self.super_area_plain_combo)
        wind_grid.addWidget(lbl, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        wind_grid.addWidget(self.super_area_plain_combo, row, 1, Qt.AlignLeft)
        row += 1
        self.super_area_plain_value = QLineEdit()
        self.super_area_plain_value.setPlaceholderText("Custom Value")
        self.super_area_plain_value.setFixedWidth(field_width)
        self.super_area_plain_value.setEnabled(False)
        apply_field_style(self.super_area_plain_value)
        wind_grid.addWidget(self.super_area_plain_value, row, 1, Qt.AlignLeft)
        row += 1

        # Exposed Frontal Area of Live Load
        lbl = QLabel("Exposed Frontal Area of Live Load (m2):")
        lbl.setStyleSheet(label_style)
        self.exposed_frontal_area_combo = QComboBox()
        self.exposed_frontal_area_combo.addItems(["Automatic", "Custom"])
        self.exposed_frontal_area_combo.setFixedWidth(field_width)
        apply_field_style(self.exposed_frontal_area_combo)
        wind_grid.addWidget(lbl, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        wind_grid.addWidget(self.exposed_frontal_area_combo, row, 1, Qt.AlignLeft)
        row += 1
        self.exposed_frontal_area_value = QLineEdit()
        self.exposed_frontal_area_value.setPlaceholderText("Custom Value")
        self.exposed_frontal_area_value.setFixedWidth(field_width)
        self.exposed_frontal_area_value.setEnabled(False)
        apply_field_style(self.exposed_frontal_area_value)
        wind_grid.addWidget(self.exposed_frontal_area_value, row, 1, Qt.AlignLeft)
        row += 1

        # Wind Load Eccentricity from Top of Deck
        lbl = QLabel("Wind Load Eccentricity from Top of Deck\n(m): Negative for below deck")
        lbl.setStyleSheet(label_style)
        self.wind_ecc_deck_combo = QComboBox()
        self.wind_ecc_deck_combo.addItems(["Automatic", "Custom"])
        self.wind_ecc_deck_combo.setFixedWidth(field_width)
        apply_field_style(self.wind_ecc_deck_combo)
        wind_grid.addWidget(lbl, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        wind_grid.addWidget(self.wind_ecc_deck_combo, row, 1, Qt.AlignLeft)
        row += 1
        self.wind_ecc_deck_value = QLineEdit()
        self.wind_ecc_deck_value.setPlaceholderText("Value")
        self.wind_ecc_deck_value.setFixedWidth(field_width)
        self.wind_ecc_deck_value.setEnabled(False)
        apply_field_style(self.wind_ecc_deck_value)
        wind_grid.addWidget(self.wind_ecc_deck_value, row, 1, Qt.AlignLeft)
        row += 1

        # Wind on Live Load Eccentricity from Top of Deck
        lbl = QLabel("Wind on Live Load Eccentricity from Top\nof Deck (m):")
        lbl.setStyleSheet(label_style)
        self.wind_ll_ecc_combo = QComboBox()
        self.wind_ll_ecc_combo.addItems(["Automatic", "Custom"])
        self.wind_ll_ecc_combo.setFixedWidth(field_width)
        apply_field_style(self.wind_ll_ecc_combo)
        wind_grid.addWidget(lbl, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        wind_grid.addWidget(self.wind_ll_ecc_combo, row, 1, Qt.AlignLeft)
        row += 1
        self.wind_ll_ecc_value = QLineEdit()
        self.wind_ll_ecc_value.setPlaceholderText("Value")
        self.wind_ll_ecc_value.setFixedWidth(field_width)
        self.wind_ll_ecc_value.setEnabled(False)
        apply_field_style(self.wind_ll_ecc_value)
        wind_grid.addWidget(self.wind_ll_ecc_value, row, 1, Qt.AlignLeft)

        wind_inputs_layout.addLayout(wind_grid)
        left_layout.addWidget(wind_inputs_box)

        # ===== Computed Values Box =====
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

        self.wind_computed_fields = {}
        for idx, (label_text, field_name) in enumerate(computed_fields):
            lbl = QLabel(label_text)
            lbl.setStyleSheet(label_style)
            field = QLineEdit()
            field.setFixedWidth(field_width)
            field.setReadOnly(True)
            apply_field_style(field)
            computed_layout.addWidget(lbl, idx, 0, Qt.AlignLeft | Qt.AlignVCenter)
            computed_layout.addWidget(field, idx, 1, Qt.AlignLeft)
            self.wind_computed_fields[field_name] = field

        left_layout.addWidget(computed_box)
        left_layout.addStretch()

        scroll.setWidget(scroll_content)
        left_card_layout.addWidget(scroll)

        # Right description card
        right_card = self._create_card()
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

        # Connect signals for enabling/disabling custom inputs
        self.gust_factor_combo.currentTextChanged.connect(lambda t: self.gust_factor_value.setEnabled(t == "Custom"))
        self.drag_coeff_combo.currentTextChanged.connect(lambda t: self.drag_coeff_value.setEnabled(t == "Custom"))
        self.drag_coeff_ll_combo.currentTextChanged.connect(lambda t: self.drag_coeff_ll_value.setEnabled(t == "Custom"))
        self.lift_coeff_combo.currentTextChanged.connect(lambda t: self.lift_coeff_value.setEnabled(t == "Custom"))
        self.super_area_elev_combo.currentTextChanged.connect(lambda t: self.super_area_elev_value.setEnabled(t == "Custom"))
        self.super_area_plain_combo.currentTextChanged.connect(lambda t: self.super_area_plain_value.setEnabled(t == "Custom"))
        self.exposed_frontal_area_combo.currentTextChanged.connect(lambda t: self.exposed_frontal_area_value.setEnabled(t == "Custom"))
        self.wind_ecc_deck_combo.currentTextChanged.connect(lambda t: self.wind_ecc_deck_value.setEnabled(t == "Custom"))
        self.wind_ll_ecc_combo.currentTextChanged.connect(lambda t: self.wind_ll_ecc_value.setEnabled(t == "Custom"))

        return page

    def _build_temperature_load_tab(self):
        """Build the Temperature Load tab matching reference design"""
        page = QWidget()
        page.setStyleSheet("background-color: #f5f5f5;")
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(12, 12, 12, 12)
        page_layout.setSpacing(12)

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(16)

        # Left card with inputs
        left_card = self._create_card()
        left_card.setStyleSheet("QFrame { border: 1px solid #b2b2b2; border-radius: 10px; background-color: #ffffff; }")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(12)

        label_style = "font-size: 11px; color: #3a3a3a; background: transparent; border: none;"
        heading_style = "font-size: 12px; font-weight: 700; color: #2b2b2b; background: transparent; border: none;"
        field_width = 140

        # ===== Temperature Load (TL) Inputs box =====
        tl_box = QFrame()
        tl_box.setStyleSheet("QFrame { border: 1px solid #b2b2b2; border-radius: 8px; background-color: #ffffff; }")
        tl_layout = QVBoxLayout(tl_box)
        tl_layout.setContentsMargins(12, 12, 12, 12)
        tl_layout.setSpacing(10)

        tl_title = QLabel("Temperature Load (TL) Inputs for evaluation per IRC6")
        tl_title.setStyleSheet(heading_style)
        tl_layout.addWidget(tl_title)

        tl_grid = QGridLayout()
        tl_grid.setContentsMargins(0, 4, 0, 0)
        tl_grid.setHorizontalSpacing(12)
        tl_grid.setVerticalSpacing(10)
        tl_grid.setColumnMinimumWidth(0, 240)

        # Highest Maximum Air Temperature
        lbl = QLabel("Highest Maximum Air Temperature\n(°C):")
        lbl.setStyleSheet(label_style)
        self.highest_max_temp_input = QLineEdit()
        self.highest_max_temp_input.setFixedWidth(field_width)
        apply_field_style(self.highest_max_temp_input)
        tl_grid.addWidget(lbl, 0, 0, Qt.AlignLeft | Qt.AlignVCenter)
        tl_grid.addWidget(self.highest_max_temp_input, 0, 1, Qt.AlignLeft)

        # Lowest Minimum Air Temperature
        lbl = QLabel("Lowest Minimum Air Temperature\n(°C):")
        lbl.setStyleSheet(label_style)
        self.lowest_min_temp_input = QLineEdit()
        self.lowest_min_temp_input.setFixedWidth(field_width)
        apply_field_style(self.lowest_min_temp_input)
        tl_grid.addWidget(lbl, 1, 0, Qt.AlignLeft | Qt.AlignVCenter)
        tl_grid.addWidget(self.lowest_min_temp_input, 1, 1, Qt.AlignLeft)

        # Coefficient of Thermal Expansion for Steel
        lbl = QLabel("Coefficient of Thermal Expansion for Steel\n(1/°C):")
        lbl.setStyleSheet(label_style)
        self.thermal_coeff_steel_input = QLineEdit()
        self.thermal_coeff_steel_input.setFixedWidth(field_width)
        apply_field_style(self.thermal_coeff_steel_input)
        tl_grid.addWidget(lbl, 2, 0, Qt.AlignLeft | Qt.AlignVCenter)
        tl_grid.addWidget(self.thermal_coeff_steel_input, 2, 1, Qt.AlignLeft)

        # Coefficient of Thermal Expansion for RCC
        lbl = QLabel("Coefficient of Thermal Expansion for RCC\n(1/°C):")
        lbl.setStyleSheet(label_style)
        self.thermal_coeff_rcc_input = QLineEdit()
        self.thermal_coeff_rcc_input.setFixedWidth(field_width)
        apply_field_style(self.thermal_coeff_rcc_input)
        tl_grid.addWidget(lbl, 3, 0, Qt.AlignLeft | Qt.AlignVCenter)
        tl_grid.addWidget(self.thermal_coeff_rcc_input, 3, 1, Qt.AlignLeft)

        tl_layout.addLayout(tl_grid)
        left_layout.addWidget(tl_box)

        # ===== Range of Effective Bridge Temperature Box =====
        range_box = QFrame()
        range_box.setStyleSheet("QFrame { border: 1px solid #b2b2b2; border-radius: 8px; background-color: #ffffff; }")
        range_layout = QVBoxLayout(range_box)
        range_layout.setContentsMargins(12, 12, 12, 12)
        range_layout.setSpacing(10)

        range_title = QLabel("Range of Effective Bridge Temperature:")
        range_title.setStyleSheet(heading_style)
        range_layout.addWidget(range_title)

        range_grid = QGridLayout()
        range_grid.setContentsMargins(0, 4, 0, 0)
        range_grid.setHorizontalSpacing(12)
        range_grid.setVerticalSpacing(10)
        range_grid.setColumnMinimumWidth(0, 200)

        lbl = QLabel("Minimum (°C):")
        lbl.setStyleSheet(label_style)
        self.bridge_temp_min_input = QLineEdit()
        self.bridge_temp_min_input.setFixedWidth(field_width)
        apply_field_style(self.bridge_temp_min_input)
        range_grid.addWidget(lbl, 0, 0, Qt.AlignLeft | Qt.AlignVCenter)
        range_grid.addWidget(self.bridge_temp_min_input, 0, 1, Qt.AlignLeft)

        lbl = QLabel("Maximum (°C):")
        lbl.setStyleSheet(label_style)
        self.bridge_temp_max_input = QLineEdit()
        self.bridge_temp_max_input.setFixedWidth(field_width)
        apply_field_style(self.bridge_temp_max_input)
        range_grid.addWidget(lbl, 1, 0, Qt.AlignLeft | Qt.AlignVCenter)
        range_grid.addWidget(self.bridge_temp_max_input, 1, 1, Qt.AlignLeft)

        # Temperature for Design heading
        temp_design_label = QLabel("Temperature for Design:")
        temp_design_label.setStyleSheet(label_style + " font-weight: 600;")
        range_grid.addWidget(temp_design_label, 2, 0, 1, 2, Qt.AlignLeft)

        lbl = QLabel("Rise (°C):")
        lbl.setStyleSheet(label_style)
        self.temp_rise_input = QLineEdit()
        self.temp_rise_input.setFixedWidth(field_width)
        apply_field_style(self.temp_rise_input)
        range_grid.addWidget(lbl, 3, 0, Qt.AlignLeft | Qt.AlignVCenter)
        range_grid.addWidget(self.temp_rise_input, 3, 1, Qt.AlignLeft)

        lbl = QLabel("Fall (°C):")
        lbl.setStyleSheet(label_style)
        self.temp_fall_input = QLineEdit()
        self.temp_fall_input.setFixedWidth(field_width)
        apply_field_style(self.temp_fall_input)
        range_grid.addWidget(lbl, 4, 0, Qt.AlignLeft | Qt.AlignVCenter)
        range_grid.addWidget(self.temp_fall_input, 4, 1, Qt.AlignLeft)

        range_layout.addLayout(range_grid)
        left_layout.addWidget(range_box)
        left_layout.addStretch()

        # Right description card
        right_card = self._create_card()
        right_card.setStyleSheet("QFrame { border: 1px solid #9c9c9c; border-radius: 10px; background-color: #d4d4d4; }")
        right_card.setMinimumWidth(230)
        right_card.setMinimumHeight(520)
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(10)

        desc_title = QLabel("Description Box")
        desc_title.setAlignment(Qt.AlignCenter)
        desc_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #2b2b2b; background: transparent; border: none;")
        right_layout.addWidget(desc_title)
        right_layout.addStretch()

        content_row.addWidget(left_card, 3)
        content_row.addWidget(right_card, 2)

        page_layout.addLayout(content_row)

        return page

    def _build_custom_load_tab(self):
        """Build the Custom Load tab matching the provided layouts."""
        page = QWidget()
        page.setStyleSheet("background-color: #f0f0f0;")
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(8, 8, 8, 8)
        page_layout.setSpacing(8)

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(12)

        label_style = "font-size: 11px; color: #2a2a2a; background: transparent; border: none;"
        heading_style = "font-size: 11px; font-weight: 700; color: #1a1a1a; background: transparent; border: none;"
        field_width = 105

        # Left column
        left_column = QVBoxLayout()
        left_column.setContentsMargins(0, 0, 0, 0)
        left_column.setSpacing(8)

        # Diagram placeholder
        diagram = QFrame()
        diagram.setMinimumSize(QSize(380, 130))
        diagram.setMaximumHeight(130)
        diagram.setStyleSheet("QFrame { border: 1px solid #a0a0a0; border-radius: 4px; background-color: #d0d0d0; }")
        diagram_layout = QVBoxLayout(diagram)
        diagram_layout.setContentsMargins(8, 8, 8, 8)
        diagram_label = QLabel("Bridge Geometry\nDiagram")
        diagram_label.setAlignment(Qt.AlignCenter)
        diagram_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #2a2a2a; background: transparent; border: none;")
        diagram_layout.addWidget(diagram_label, 1)
        left_column.addWidget(diagram)

        # Input card
        input_card = self._create_card()
        input_card.setStyleSheet("QFrame { border: 1px solid #a0a0a0; border-radius: 4px; background-color: #ffffff; }")
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(10, 10, 10, 10)
        input_layout.setSpacing(8)

        title = QLabel("Custom Load Input Add/Edit:")
        title.setStyleSheet(heading_style)
        input_layout.addWidget(title)

        form_grid = QGridLayout()
        form_grid.setContentsMargins(0, 0, 0, 0)
        form_grid.setHorizontalSpacing(8)
        form_grid.setVerticalSpacing(8)
        form_grid.setColumnMinimumWidth(0, 120)
        form_grid.setColumnStretch(0, 0)
        form_grid.setColumnStretch(1, 0)
        form_grid.setColumnStretch(2, 0)

        # Load Case row
        lbl = QLabel("Load Case:")
        lbl.setStyleSheet(label_style)
        self.custom_load_case_combo = QComboBox()
        self.custom_load_case_combo.addItems(["", "LL", "DL", "Custom"])
        self.custom_load_case_combo.setFixedWidth(field_width)
        apply_field_style(self.custom_load_case_combo)
        form_grid.addWidget(lbl, 0, 0, Qt.AlignLeft | Qt.AlignVCenter)
        form_grid.addWidget(self.custom_load_case_combo, 0, 1, Qt.AlignLeft)

        self.custom_load_case_button = QPushButton("Custom")
        self.custom_load_case_button.setFixedWidth(field_width)
        self.custom_load_case_button.setStyleSheet(
            "QPushButton { background: #e8e8e8; border: 1px solid #a0a0a0; border-radius: 3px; padding: 3px 8px; font-size: 11px; color: #2a2a2a; }"
            "QPushButton:hover { background: #f0f0f0; }"
            "QPushButton:pressed { background: #d8d8d8; }"
        )
        form_grid.addWidget(self.custom_load_case_button, 0, 2, Qt.AlignLeft)

        # Load Type row
        lbl = QLabel("Load Type:")
        lbl.setStyleSheet(label_style)
        self.custom_load_type_combo = QComboBox()
        self.custom_load_type_combo.addItems(["Point", "Line/Area"])
        self.custom_load_type_combo.setFixedWidth(field_width)
        apply_field_style(self.custom_load_type_combo)
        form_grid.addWidget(lbl, 1, 0, Qt.AlignLeft | Qt.AlignVCenter)
        form_grid.addWidget(self.custom_load_type_combo, 1, 1, Qt.AlignLeft)

        # Stacked inputs for Point vs Line/Area
        self.custom_load_stack = QStackedWidget()
        self.custom_load_stack.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.custom_load_stack.setFixedWidth(360)
        self.custom_load_stack.setStyleSheet(
            "QStackedWidget { border: none; background: transparent; }"
            "QWidget#customPointWidget, QWidget#customLineWidget { background: transparent; }"
        )

        # Point layout
        point_widget = QWidget()
        point_widget.setObjectName("customPointWidget")
        point_grid = QGridLayout(point_widget)
        point_grid.setContentsMargins(0, 0, 0, 0)
        point_grid.setHorizontalSpacing(8)
        point_grid.setVerticalSpacing(8)
        point_grid.setColumnMinimumWidth(0, 240)
        point_grid.setColumnStretch(0, 0)
        point_grid.setColumnStretch(1, 0)

        lbl = QLabel("Distance from Left Edge of Bridge Cross\nSection (m):")
        lbl.setStyleSheet(label_style)
        self.custom_point_left_input = QLineEdit()
        self.custom_point_left_input.setFixedWidth(105)
        apply_field_style(self.custom_point_left_input)
        point_grid.addWidget(lbl, 0, 0, Qt.AlignLeft | Qt.AlignVCenter)
        point_grid.addWidget(self.custom_point_left_input, 0, 1, Qt.AlignLeft)

        lbl = QLabel("Distance from Center Line of Bearing\n(m):")
        lbl.setStyleSheet(label_style)
        self.custom_point_bearing_input = QLineEdit()
        self.custom_point_bearing_input.setFixedWidth(105)
        apply_field_style(self.custom_point_bearing_input)
        point_grid.addWidget(lbl, 1, 0, Qt.AlignLeft | Qt.AlignVCenter)
        point_grid.addWidget(self.custom_point_bearing_input, 1, 1, Qt.AlignLeft)

        self.custom_load_stack.addWidget(point_widget)

        # Line/Area layout
        line_widget = QWidget()
        line_widget.setObjectName("customLineWidget")
        line_grid = QGridLayout(line_widget)
        line_grid.setContentsMargins(0, 0, 0, 0)
        line_grid.setHorizontalSpacing(8)
        line_grid.setVerticalSpacing(4)
        line_grid.setColumnMinimumWidth(0, 240)

        def _start_end_row(label_text, start_attr, end_attr, row_idx):
            row_label = QLabel(label_text)
            row_label.setStyleSheet(label_style)
            start_field = QLineEdit()
            end_field = QLineEdit()
            start_field.setFixedWidth(52)
            end_field.setFixedWidth(52)
            apply_field_style(start_field)
            apply_field_style(end_field)

            line_grid.addWidget(row_label, row_idx * 2, 0, Qt.AlignLeft | Qt.AlignVCenter)
            line_grid.addWidget(start_field, row_idx * 2, 1, Qt.AlignLeft)
            line_grid.addWidget(end_field, row_idx * 2, 2, Qt.AlignLeft)

            start_lbl = QLabel("Start")
            start_lbl.setStyleSheet("font-size: 9px; color: #505050;")
            end_lbl = QLabel("End")
            end_lbl.setStyleSheet("font-size: 9px; color: #505050;")
            line_grid.addWidget(start_lbl, row_idx * 2 + 1, 1, Qt.AlignHCenter | Qt.AlignTop)
            line_grid.addWidget(end_lbl, row_idx * 2 + 1, 2, Qt.AlignHCenter | Qt.AlignTop)

            setattr(self, start_attr, start_field)
            setattr(self, end_attr, end_field)

        _start_end_row("Distance from Left Edge of Bridge Cross\nSection (m):", "custom_line_left_start", "custom_line_left_end", 0)
        _start_end_row("Distance from Center Line of Bearing\n(m):", "custom_line_bearing_start", "custom_line_bearing_end", 1)

        self.custom_load_stack.addWidget(line_widget)

        # Place stack in grid
        form_grid.addWidget(self.custom_load_stack, 2, 0, 1, 3)

        input_layout.addLayout(form_grid)

        # Save button bar
        save_btn = QPushButton("Save")
        save_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        save_btn.setStyleSheet(
            "QPushButton { background: #c8c8c8; border: 1px solid #a0a0a0; border-radius: 3px; padding: 5px 16px; font-weight: 600; font-size: 11px; color: #2a2a2a; }"
            "QPushButton:hover { background: #d8d8d8; }"
            "QPushButton:pressed { background: #b8b8b8; }"
        )
        save_row = QHBoxLayout()
        save_row.setContentsMargins(0, 4, 0, 0)
        save_row.addWidget(save_btn)
        input_layout.addLayout(save_row)

        left_column.addWidget(input_card)

        # Custom Load Name list card
        list_card = self._create_card()
        list_card.setStyleSheet("QFrame { border: 1px solid #a0a0a0; border-radius: 4px; background-color: #ffffff; }")
        list_card.setMinimumHeight(120)
        list_layout = QVBoxLayout(list_card)
        list_layout.setContentsMargins(10, 10, 10, 10)
        list_layout.setSpacing(8)

        list_title = QLabel("Custom Load Name")
        list_title.setStyleSheet(heading_style)
        list_layout.addWidget(list_title)

        controls_row = QHBoxLayout()
        controls_row.setSpacing(6)
        self.custom_add_btn = QPushButton("Add")
        self.custom_edit_btn = QPushButton("Edit")
        self.custom_delete_btn = QPushButton("Delete")
        for btn in (self.custom_add_btn, self.custom_edit_btn, self.custom_delete_btn):
            btn.setFixedWidth(55)
            btn.setStyleSheet(
                "QPushButton { background: #ffffff; border: 1px solid #a0a0a0; border-radius: 3px; padding: 3px 8px; font-size: 11px; color: #2a2a2a; }"
                "QPushButton:hover { background: #f0f0f0; }"
                "QPushButton:pressed { background: #e0e0e0; }"
            )
            controls_row.addWidget(btn)
        controls_row.addStretch()
        list_layout.addLayout(controls_row)

        self.custom_load_items = []
        self.custom_load_list_container = QWidget()
        self.custom_load_list_layout = QVBoxLayout(self.custom_load_list_container)
        self.custom_load_list_layout.setContentsMargins(2, 2, 2, 2)
        self.custom_load_list_layout.setSpacing(4)
        self.custom_load_list_layout.addStretch()
        list_layout.addWidget(self.custom_load_list_container)

        left_column.addWidget(list_card)
        left_column.addStretch()

        # Right description card
        right_card = self._create_card()
        right_card.setStyleSheet("QFrame { border: 1px solid #a0a0a0; border-radius: 4px; background-color: #d8d8d8; }")
        right_card.setMinimumWidth(260)
        right_card.setMinimumHeight(480)
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(8)

        desc_title = QLabel("Description Box")
        desc_title.setAlignment(Qt.AlignCenter)
        desc_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #1a1a1a; background: transparent; border: none;")
        right_layout.addWidget(desc_title)
        right_layout.addStretch()

        content_row.addLayout(left_column, 3)
        content_row.addWidget(right_card, 2)
        page_layout.addLayout(content_row)

        self._refresh_custom_load_list()

        # Connections
        self.custom_load_type_combo.currentTextChanged.connect(self._on_custom_load_type_changed)
        self._on_custom_load_type_changed(self.custom_load_type_combo.currentText())

        self.custom_add_btn.clicked.connect(self._on_add_custom_load)
        self.custom_delete_btn.clicked.connect(self._on_delete_custom_load)
        self.custom_edit_btn.clicked.connect(lambda: QMessageBox.information(self, "Edit", "Edit functionality will be added in a future update."))

        return page

    def _on_custom_load_type_changed(self, text):
        """Toggle between point and line/area input layouts."""
        if text.lower().startswith("point"):
            self.custom_load_stack.setCurrentIndex(0)
        else:
            self.custom_load_stack.setCurrentIndex(1)

    def _refresh_custom_load_list(self):
        if not hasattr(self, "custom_load_list_layout"):
            return
        while self.custom_load_list_layout.count():
            item = self.custom_load_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.custom_load_checkboxes = []
        for name in self.custom_load_items:
            row = QHBoxLayout()
            row.setContentsMargins(2, 0, 2, 0)
            row.setSpacing(4)
            label = QLabel(name)
            label.setStyleSheet("font-size: 11px; font-style: italic; color: #3a3a3a; background: transparent; border: none;")
            checkbox = QCheckBox()
            row.addWidget(label)
            row.addStretch()
            row.addWidget(checkbox)
            container = QWidget()
            container.setLayout(row)
            self.custom_load_list_layout.addWidget(container)
            self.custom_load_checkboxes.append((name, checkbox))
        self.custom_load_list_layout.addStretch()

    def _on_add_custom_load(self):
        next_index = len(self.custom_load_items) + 1
        new_name = f"Custom Load {next_index}"
        self.custom_load_items.append(new_name)
        self._refresh_custom_load_list()

    def _on_delete_custom_load(self):
        if not getattr(self, "custom_load_checkboxes", None):
            return
        remaining = [name for name, cb in self.custom_load_checkboxes if not cb.isChecked()]
        if len(remaining) == len(self.custom_load_checkboxes):
            QMessageBox.information(self, "Delete", "Select at least one custom load to delete.")
            return
        self.custom_load_items = remaining
        self._refresh_custom_load_list()
        if not getattr(self, "custom_load_checkboxes", None):
            return
        remaining = [name for name, cb in self.custom_load_checkboxes if not cb.isChecked()]
        if len(remaining) == len(self.custom_load_checkboxes):
            QMessageBox.information(self, "Delete", "Select at least one custom load to delete.")
            return
        self.custom_load_items = remaining
        self._refresh_custom_load_list()

    def _build_load_combination_tab(self):
        """Build the Load Combination tab and wire the Add/Edit modal."""
        page = QWidget()
        page.setStyleSheet("background-color: #f5f5f5;")
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(12, 12, 12, 12)
        page_layout.setSpacing(12)

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(16)

        heading_style = "font-size: 12px; font-weight: 700; color: #2b2b2b; background: transparent; border: none;"
        label_style = "font-size: 11px; color: #3a3a3a; background: transparent; border: none;"

        if not hasattr(self, "load_combo_items"):
            self.load_combo_items = [
                {"name": "DL + LL", "items": [{"case": "DL", "factor": "1.0"}, {"case": "LL", "factor": "1.0"}]},
                {"name": "1.35 DL + 1.5 LL", "items": [{"case": "DL", "factor": "1.35"}, {"case": "LL", "factor": "1.5"}]},
            ]

        # Left card - combination list and controls
        left_card = self._create_card()
        left_card.setStyleSheet("QFrame { border: 1px solid #b2b2b2; border-radius: 10px; background-color: #ffffff; }")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(10)

        title = QLabel("Inputs:")
        title.setStyleSheet(heading_style)
        left_layout.addWidget(title)

        combo_label = QLabel("Load Combination")
        combo_label.setStyleSheet("font-size: 11px; font-style: italic; color: #2b2b2b; background: transparent; border: none;")
        left_layout.addWidget(combo_label)

        auto_row = QHBoxLayout()
        auto_row.setSpacing(8)
        auto_row.setContentsMargins(0, 0, 0, 0)
        auto_label = QLabel("Auto include all IRC 6 Load Combinations")
        auto_label.setStyleSheet(label_style)
        self.auto_include_checkbox = QCheckBox()
        auto_row.addWidget(auto_label)
        auto_row.addWidget(self.auto_include_checkbox)
        auto_row.addStretch()
        left_layout.addLayout(auto_row)

        controls_row = QHBoxLayout()
        controls_row.setSpacing(6)
        self.load_combo_add_btn = QPushButton("Add")
        self.load_combo_edit_btn = QPushButton("Edit")
        self.load_combo_delete_btn = QPushButton("Delete")
        for btn in (self.load_combo_add_btn, self.load_combo_edit_btn, self.load_combo_delete_btn):
            btn.setFixedWidth(60)
            btn.setStyleSheet(
                "QPushButton { background: #ffffff; border: 1px solid #a0a0a0; border-radius: 3px; padding: 4px 10px; font-size: 11px; color: #2a2a2a; }"
                "QPushButton:hover { background: #f0f0f0; }"
                "QPushButton:pressed { background: #e0e0e0; }"
            )
            controls_row.addWidget(btn)
        controls_row.addStretch()
        left_layout.addLayout(controls_row)

        list_card = QFrame()
        list_card.setStyleSheet("QFrame { border: 1px solid #a0a0a0; border-radius: 4px; background-color: #ffffff; }")
        list_layout = QVBoxLayout(list_card)
        list_layout.setContentsMargins(10, 10, 10, 10)
        list_layout.setSpacing(6)

        self.load_combo_list_layout = QVBoxLayout()
        self.load_combo_list_layout.setContentsMargins(2, 2, 2, 2)
        self.load_combo_list_layout.setSpacing(6)
        list_layout.addLayout(self.load_combo_list_layout)
        left_layout.addWidget(list_card)
        left_layout.addStretch()

        # Right description card
        right_card = self._create_card()
        right_card.setStyleSheet("QFrame { border: 1px solid #9c9c9c; border-radius: 10px; background-color: #c8c8c8; }")
        right_card.setMinimumWidth(270)
        right_card.setMinimumHeight(360)
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(18, 18, 18, 18)
        right_layout.setSpacing(12)
        description_label = QLabel("Description Box")
        description_label.setAlignment(Qt.AlignCenter)
        description_label.setStyleSheet("font-size: 12px; font-weight: 700; color: #000000;")
        description_label.setMinimumHeight(320)
        right_layout.addWidget(description_label)

        content_row.addWidget(left_card, 3)
        content_row.addWidget(right_card, 2)

        page_layout.addLayout(content_row)

        self._refresh_load_combo_list()

        self.load_combo_add_btn.clicked.connect(self._on_add_load_combo)
        self.load_combo_edit_btn.clicked.connect(self._on_edit_load_combo)
        self.load_combo_delete_btn.clicked.connect(self._on_delete_load_combo)

        return page

    def _refresh_load_combo_list(self):
        if not hasattr(self, "load_combo_list_layout"):
            return
        while self.load_combo_list_layout.count():
            item = self.load_combo_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.load_combo_checkboxes = []
        if not getattr(self, "load_combo_items", None):
            empty_lbl = QLabel("No combinations added yet.")
            empty_lbl.setStyleSheet("font-size: 11px; color: #6a6a6a; background: transparent; border: none;")
            self.load_combo_list_layout.addWidget(empty_lbl)
            self.load_combo_list_layout.addStretch()
            return

        for combo in self.load_combo_items:
            row = QHBoxLayout()
            row.setContentsMargins(2, 0, 2, 0)
            row.setSpacing(6)
            label = QLabel(combo.get("name", "Combination"))
            label.setStyleSheet("font-size: 11px; font-style: italic; color: #3a3a3a; background: transparent; border: none;")
            checkbox = QCheckBox()
            row.addWidget(label)
            row.addStretch()
            row.addWidget(checkbox)
            container = QWidget()
            container.setLayout(row)
            self.load_combo_list_layout.addWidget(container)
            self.load_combo_checkboxes.append((combo, checkbox))

        self.load_combo_list_layout.addStretch()

    def _get_selected_load_combos(self):
        if not getattr(self, "load_combo_checkboxes", None):
            return []
        return [idx for idx, (_, cb) in enumerate(self.load_combo_checkboxes) if cb.isChecked()]

    def _on_add_load_combo(self):
        data = self._open_load_combo_dialog()
        if data:
            self.load_combo_items.append(data)
            self._refresh_load_combo_list()

    def _on_edit_load_combo(self):
        selected = self._get_selected_load_combos()
        if not selected:
            QMessageBox.information(self, "Edit", "Select one load combination to edit.")
            return
        if len(selected) > 1:
            QMessageBox.information(self, "Edit", "Select only one load combination to edit.")
            return
        index = selected[0]
        current = self.load_combo_items[index]
        data = self._open_load_combo_dialog(existing=current)
        if data:
            self.load_combo_items[index] = data
            self._refresh_load_combo_list()

    def _on_delete_load_combo(self):
        selected = self._get_selected_load_combos()
        if not selected:
            QMessageBox.information(self, "Delete", "Select at least one load combination to delete.")
            return
        self.load_combo_items = [item for idx, item in enumerate(self.load_combo_items) if idx not in selected]
        self._refresh_load_combo_list()

    def _open_load_combo_dialog(self, existing=None):
        dialog = QDialog(self)
        dialog.setModal(True)
        dialog.setWindowTitle("Edit Load Combination" if existing else "Add Load Combination")
        dialog.setMinimumWidth(520)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        label_style = "font-size: 11px; color: #2a2a2a; background: transparent; border: none;"

        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        name_label = QLabel("Combination Name:")
        name_label.setStyleSheet(label_style)
        name_input = QLineEdit()
        name_input.setMinimumWidth(220)
        apply_field_style(name_input)
        name_row.addWidget(name_label)
        name_row.addWidget(name_input, 1)
        layout.addLayout(name_row)

        fields_row = QGridLayout()
        fields_row.setContentsMargins(0, 0, 0, 0)
        fields_row.setHorizontalSpacing(10)
        fields_row.setVerticalSpacing(6)

        load_case_label = QLabel("Load Case:")
        load_case_label.setStyleSheet(label_style)
        load_case_combo = QComboBox()
        load_case_combo.addItems(["DL", "SIDL", "LL", "WL", "EL", "IMF", "TL"])
        apply_field_style(load_case_combo)

        factor_label = QLabel("Partial Safety Factor:")
        factor_label.setStyleSheet(label_style)
        factor_input = QLineEdit()
        factor_input.setText("1.0")
        factor_input.setMinimumWidth(80)
        apply_field_style(factor_input)

        fields_row.addWidget(load_case_label, 0, 0, Qt.AlignLeft)
        fields_row.addWidget(load_case_combo, 0, 1, Qt.AlignLeft)
        fields_row.addWidget(factor_label, 0, 2, Qt.AlignLeft)
        fields_row.addWidget(factor_input, 0, 3, Qt.AlignLeft)
        fields_row.setColumnStretch(4, 1)
        layout.addLayout(fields_row)

        table_row = QHBoxLayout()
        table_row.setSpacing(8)

        table = QTableWidget(0, 3)
        table.setHorizontalHeaderLabels(["S.No", "Load Case", "Partial Safety Factor"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.setStyleSheet("QTableWidget { background: #ffffff; } QHeaderView::section { color: #2a2a2a; background: #efefef; font-size: 10px; }")
        table.setMinimumHeight(220)

        button_col = QVBoxLayout()
        button_col.setSpacing(6)
        add_btn = QPushButton("Add")
        modify_btn = QPushButton("Modify")
        delete_btn = QPushButton("Delete")
        for btn in (add_btn, modify_btn, delete_btn):
            btn.setFixedWidth(80)
            btn.setStyleSheet(
                "QPushButton { background: #ffffff; border: 1px solid #a0a0a0; border-radius: 3px; padding: 5px 12px; font-size: 11px; color: #2a2a2a; }"
                "QPushButton:hover { background: #f0f0f0; }"
                "QPushButton:pressed { background: #e0e0e0; }"
            )
            button_col.addWidget(btn)
        button_col.addStretch()

        table_row.addWidget(table, 1)
        table_row.addLayout(button_col)
        layout.addLayout(table_row)

        action_row = QHBoxLayout()
        action_row.setContentsMargins(0, 4, 0, 0)
        action_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        save_btn = QPushButton("Save")
        for btn in (cancel_btn, save_btn):
            btn.setFixedWidth(80)
            btn.setStyleSheet(
                "QPushButton { background: #c8c8c8; border: 1px solid #a0a0a0; border-radius: 3px; padding: 6px 14px; font-weight: 600; font-size: 11px; color: #2a2a2a; }"
                "QPushButton:hover { background: #d8d8d8; }"
                "QPushButton:pressed { background: #b8b8b8; }"
            )
        action_row.addWidget(cancel_btn)
        action_row.addWidget(save_btn)
        layout.addLayout(action_row)

        def refresh_row_numbers():
            for row_idx in range(table.rowCount()):
                item = table.item(row_idx, 0)
                if item:
                    item.setText(str(row_idx + 1))

        def add_row():
            case_text = load_case_combo.currentText().strip()
            factor_text = factor_input.text().strip() or "1.0"
            row_idx = table.rowCount()
            table.insertRow(row_idx)
            table.setItem(row_idx, 0, QTableWidgetItem(str(row_idx + 1)))
            table.setItem(row_idx, 1, QTableWidgetItem(case_text))
            table.setItem(row_idx, 2, QTableWidgetItem(factor_text))
            refresh_row_numbers()

        def modify_row():
            row_idx = table.currentRow()
            if row_idx < 0:
                QMessageBox.information(dialog, "Modify", "Select one row to modify.")
                return
            table.setItem(row_idx, 1, QTableWidgetItem(load_case_combo.currentText().strip()))
            table.setItem(row_idx, 2, QTableWidgetItem(factor_input.text().strip() or "1.0"))
            refresh_row_numbers()

        def delete_row():
            row_idx = table.currentRow()
            if row_idx < 0:
                QMessageBox.information(dialog, "Delete", "Select one row to delete.")
                return
            table.removeRow(row_idx)
            refresh_row_numbers()

        def load_existing():
            if not existing:
                return
            name_input.setText(existing.get("name", ""))
            for item in existing.get("items", []):
                case_text = item.get("case", "")
                factor_text = item.get("factor", "")
                if case_text:
                    load_case_combo.setCurrentText(case_text)
                factor_input.setText(factor_text or "1.0")
                add_row()

        def on_save():
            name_text = name_input.text().strip() or "Load Combination"
            rows = []
            for row_idx in range(table.rowCount()):
                case_item = table.item(row_idx, 1)
                factor_item = table.item(row_idx, 2)
                if not case_item or not factor_item:
                    continue
                rows.append({"case": case_item.text(), "factor": factor_item.text()})
            if not rows:
                QMessageBox.information(dialog, "Save", "Add at least one load case entry.")
                return
            dialog.accept()
            dialog.result_data = {"name": name_text, "items": rows}

        add_btn.clicked.connect(add_row)
        modify_btn.clicked.connect(modify_row)
        delete_btn.clicked.connect(delete_row)
        save_btn.clicked.connect(on_save)
        cancel_btn.clicked.connect(dialog.reject)

        load_existing()

        if dialog.exec() == QDialog.Accepted:
            return getattr(dialog, "result_data", None)
        return None

    def _create_placeholder_page(self, title):
        page = QWidget()
        page.setStyleSheet("background-color: #f5f5f5;")
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(20, 20, 20, 20)

        label = QLabel(f"{title} inputs will be added soon.")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 12px; color: #6a6a6a;")
        layout.addWidget(label)
        return page

