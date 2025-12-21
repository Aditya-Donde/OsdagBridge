from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QComboBox,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QFrame,
)

from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style


class LiveLoadTab(QWidget):
    """Live Load tab content extracted from LoadingTab."""

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

        # Wrap the tall content in a scroll area so long vehicle lists stay usable on smaller windows.
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; } QScrollArea > QWidget > QWidget { background: transparent; }")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: #ffffff;")
        left_layout = QVBoxLayout(scroll_content)
        left_layout.setContentsMargins(14, 14, 14, 14)
        left_layout.setSpacing(8)

        title = QLabel("Live Load (LL) Inputs:")
        title.setStyleSheet("font-size: 12px; font-weight: 700; color: #3a3a3a; background: transparent; border: none;")
        left_layout.addWidget(title)

        irc_vehicles = [
            "Class A", "Class 70R Wheeled", "Class 70R Tracked",
            "Class AA Wheeled", "Class AA Tracked", "Class SV", "Fatigue Truck"
        ]
        owner._add_checkbox_section(left_layout, "Vehicles from IRC 6:", irc_vehicles)

        custom_header = QHBoxLayout()
        custom_header.setSpacing(8)
        custom_label = QLabel("Custom Vehicle:")
        custom_label.setStyleSheet("font-size: 12px; font-weight: 700; color: #3a3a3a; background: transparent; border: none;")
        custom_header.addWidget(custom_label)
        custom_header.addStretch()
        owner.custom_vehicle_add_button = QPushButton("Add")
        owner.custom_vehicle_edit_button = QPushButton("Edit")
        for btn in (owner.custom_vehicle_add_button, owner.custom_vehicle_edit_button):
            btn.setFixedWidth(50)
            btn.setStyleSheet(
                "QPushButton { background: #ffffff; color: #2f2f2f; border: 1px solid #7a7a7a; border-radius: 4px; padding: 4px 10px; }"
                "QPushButton:hover { background: #f0f0f0; }"
                "QPushButton:pressed { background: #e0e0e0; }"
            )
            custom_header.addWidget(btn)
        left_layout.addLayout(custom_header)

        owner.custom_vehicle_checkboxes = []
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
            owner.custom_vehicle_checkboxes.append(checkbox)

        braking_vehicles = irc_vehicles + ["Vehicle Name 1", "Vehicle Name 2"]
        owner._add_checkbox_section(left_layout, "Braking Load from Vehicles:", braking_vehicles)

        input_width = 120

        ecc_row = QHBoxLayout()
        ecc_row.setSpacing(10)
        ecc_label = QLabel("Eccentricity from top of Deck (m):")
        ecc_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #3a3a3a; background: transparent; border: none;")
        ecc_label.setMinimumWidth(200)
        owner.eccentricity_input = QLineEdit()
        owner.eccentricity_input.setFixedWidth(input_width)
        apply_field_style(owner.eccentricity_input)
        ecc_row.addWidget(ecc_label)
        ecc_row.addWidget(owner.eccentricity_input)
        ecc_row.addStretch()
        left_layout.addLayout(ecc_row)

        footpath_row = QHBoxLayout()
        footpath_row.setSpacing(10)
        footpath_label = QLabel("Footpath Pressure (kN/mm2 ):")
        footpath_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #3a3a3a; background: transparent; border: none;")
        footpath_label.setMinimumWidth(200)
        owner.footpath_mode_combo = QComboBox()
        owner.footpath_mode_combo.addItems(["Automatic", "User-defined"])
        owner.footpath_mode_combo.setFixedWidth(input_width)
        apply_field_style(owner.footpath_mode_combo)
        footpath_row.addWidget(footpath_label)
        footpath_row.addWidget(owner.footpath_mode_combo)
        footpath_row.addStretch()
        left_layout.addLayout(footpath_row)

        value_row = QHBoxLayout()
        value_row.setContentsMargins(0, 0, 0, 0)
        value_row.setSpacing(10)
        value_spacer = QLabel("")
        value_spacer.setMinimumWidth(200)
        owner.footpath_value_input = QLineEdit()
        owner.footpath_value_input.setPlaceholderText("Value")
        owner.footpath_value_input.setFixedWidth(input_width)
        apply_field_style(owner.footpath_value_input)
        value_row.addWidget(value_spacer)
        value_row.addWidget(owner.footpath_value_input)
        value_row.addStretch()
        left_layout.addLayout(value_row)

        left_layout.addStretch()

        scroll.setWidget(scroll_content)
        left_card_layout.addWidget(scroll)

        right_card = owner._create_card()
        right_card.setStyleSheet("QFrame { border: 1px solid #9c9c9c; border-radius: 10px; background-color: #d4d4d4; }")
        right_card.setMinimumWidth(260)
        right_card.setMinimumHeight(420)
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(10)

        desc_label = QLabel("Description Box")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("font-size: 12px; font-weight: 700; color: #000000; background: transparent; border: none;")
        right_layout.addWidget(desc_label)

        description_text = (
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

        owner.custom_vehicle_add_button.clicked.connect(owner.show_custom_vehicle_dialog)
        owner.custom_vehicle_edit_button.clicked.connect(owner.show_custom_vehicle_dialog)
        owner.footpath_mode_combo.currentTextChanged.connect(owner._on_footpath_mode_changed)
        owner._on_footpath_mode_changed(owner.footpath_mode_combo.currentText())
