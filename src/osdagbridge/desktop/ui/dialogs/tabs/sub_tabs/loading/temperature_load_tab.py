from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style


class TemperatureLoadTab(QWidget):
    """Temperature load inputs for evaluation per IRC 6."""

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
        left_card.setStyleSheet(
            "QFrame { border: 1px solid #b2b2b2; border-radius: 10px; background-color: #ffffff; }"
        )
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(12)

        label_style = "font-size: 11px; color: #3a3a3a; background: transparent; border: none;"
        heading_style = "font-size: 12px; font-weight: 700; color: #2b2b2b; background: transparent; border: none;"
        field_width = 140

        tl_box = QFrame()
        tl_box.setStyleSheet(
            "QFrame { border: 1px solid #b2b2b2; border-radius: 8px; background-color: #ffffff; }"
        )
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

        lbl = QLabel("Highest Maximum Air Temperature\n(°C):")
        lbl.setStyleSheet(label_style)
        owner.highest_max_temp_input = QLineEdit()
        owner.highest_max_temp_input.setFixedWidth(field_width)
        apply_field_style(owner.highest_max_temp_input)
        tl_grid.addWidget(lbl, 0, 0, Qt.AlignLeft | Qt.AlignVCenter)
        tl_grid.addWidget(owner.highest_max_temp_input, 0, 1, Qt.AlignLeft)

        lbl = QLabel("Lowest Minimum Air Temperature\n(°C):")
        lbl.setStyleSheet(label_style)
        owner.lowest_min_temp_input = QLineEdit()
        owner.lowest_min_temp_input.setFixedWidth(field_width)
        apply_field_style(owner.lowest_min_temp_input)
        tl_grid.addWidget(lbl, 1, 0, Qt.AlignLeft | Qt.AlignVCenter)
        tl_grid.addWidget(owner.lowest_min_temp_input, 1, 1, Qt.AlignLeft)

        lbl = QLabel("Coefficient of Thermal Expansion for Steel\n(1/°C):")
        lbl.setStyleSheet(label_style)
        owner.thermal_coeff_steel_input = QLineEdit()
        owner.thermal_coeff_steel_input.setFixedWidth(field_width)
        apply_field_style(owner.thermal_coeff_steel_input)
        tl_grid.addWidget(lbl, 2, 0, Qt.AlignLeft | Qt.AlignVCenter)
        tl_grid.addWidget(owner.thermal_coeff_steel_input, 2, 1, Qt.AlignLeft)

        lbl = QLabel("Coefficient of Thermal Expansion for RCC\n(1/°C):")
        lbl.setStyleSheet(label_style)
        owner.thermal_coeff_rcc_input = QLineEdit()
        owner.thermal_coeff_rcc_input.setFixedWidth(field_width)
        apply_field_style(owner.thermal_coeff_rcc_input)
        tl_grid.addWidget(lbl, 3, 0, Qt.AlignLeft | Qt.AlignVCenter)
        tl_grid.addWidget(owner.thermal_coeff_rcc_input, 3, 1, Qt.AlignLeft)

        tl_layout.addLayout(tl_grid)
        left_layout.addWidget(tl_box)

        range_box = QFrame()
        range_box.setStyleSheet(
            "QFrame { border: 1px solid #b2b2b2; border-radius: 8px; background-color: #ffffff; }"
        )
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
        owner.bridge_temp_min_input = QLineEdit()
        owner.bridge_temp_min_input.setFixedWidth(field_width)
        apply_field_style(owner.bridge_temp_min_input)
        range_grid.addWidget(lbl, 0, 0, Qt.AlignLeft | Qt.AlignVCenter)
        range_grid.addWidget(owner.bridge_temp_min_input, 0, 1, Qt.AlignLeft)

        lbl = QLabel("Maximum (°C):")
        lbl.setStyleSheet(label_style)
        owner.bridge_temp_max_input = QLineEdit()
        owner.bridge_temp_max_input.setFixedWidth(field_width)
        apply_field_style(owner.bridge_temp_max_input)
        range_grid.addWidget(lbl, 1, 0, Qt.AlignLeft | Qt.AlignVCenter)
        range_grid.addWidget(owner.bridge_temp_max_input, 1, 1, Qt.AlignLeft)

        temp_design_label = QLabel("Temperature for Design:")
        temp_design_label.setStyleSheet(label_style + " font-weight: 600;")
        range_grid.addWidget(temp_design_label, 2, 0, 1, 2, Qt.AlignLeft)

        lbl = QLabel("Rise (°C):")
        lbl.setStyleSheet(label_style)
        owner.temp_rise_input = QLineEdit()
        owner.temp_rise_input.setFixedWidth(field_width)
        apply_field_style(owner.temp_rise_input)
        range_grid.addWidget(lbl, 3, 0, Qt.AlignLeft | Qt.AlignVCenter)
        range_grid.addWidget(owner.temp_rise_input, 3, 1, Qt.AlignLeft)

        lbl = QLabel("Fall (°C):")
        lbl.setStyleSheet(label_style)
        owner.temp_fall_input = QLineEdit()
        owner.temp_fall_input.setFixedWidth(field_width)
        apply_field_style(owner.temp_fall_input)
        range_grid.addWidget(lbl, 4, 0, Qt.AlignLeft | Qt.AlignVCenter)
        range_grid.addWidget(owner.temp_fall_input, 4, 1, Qt.AlignLeft)

        range_layout.addLayout(range_grid)
        left_layout.addWidget(range_box)
        left_layout.addStretch()

        right_card = owner._create_card()
        right_card.setStyleSheet(
            "QFrame { border: 1px solid #9c9c9c; border-radius: 10px; background-color: #d4d4d4; }"
        )
        right_card.setMinimumWidth(230)
        right_card.setMinimumHeight(520)
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(10)

        desc_title = QLabel("Description Box")
        desc_title.setAlignment(Qt.AlignCenter)
        desc_title.setStyleSheet(
            "font-size: 12px; font-weight: 700; color: #2b2b2b; background: transparent; border: none;"
        )
        right_layout.addWidget(desc_title)
        right_layout.addStretch()

        content_row.addWidget(left_card, 3)
        content_row.addWidget(right_card, 2)

        page_layout.addLayout(content_row)
