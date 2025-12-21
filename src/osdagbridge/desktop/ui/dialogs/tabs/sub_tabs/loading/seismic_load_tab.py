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
)

from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style


class SeismicLoadTab(QWidget):
    """Seismic/Earthquake Load tab content extracted from LoadingTab."""

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
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(12)

        title = QLabel("Seismic/Earthquake Load (EL) Inputs for Evaluation per IRC 6")
        title.setStyleSheet("font-size: 12px; font-weight: 700; color: #2b2b2b; background: transparent; border: none;")
        left_layout.addWidget(title)

        label_style = "font-size: 11px; color: #3a3a3a; background: transparent; border: none;"
        field_width = 120
        field_height = 28

        seismic_inputs_box = QFrame()
        seismic_inputs_box.setStyleSheet("QFrame { border: 1px solid #b2b2b2; border-radius: 8px; background-color: #ffffff; }")
        seismic_inputs_layout = QGridLayout(seismic_inputs_box)
        seismic_inputs_layout.setContentsMargins(12, 16, 12, 16)
        seismic_inputs_layout.setHorizontalSpacing(12)
        seismic_inputs_layout.setVerticalSpacing(6)
        seismic_inputs_layout.setColumnMinimumWidth(0, 200)
        seismic_inputs_layout.setColumnMinimumWidth(1, 140)
        seismic_inputs_layout.setColumnMinimumWidth(2, 140)
        seismic_inputs_layout.setColumnStretch(2, 1)

        row = 0

        def add_combo(label_text, combo_items, attr_name, with_custom=False, placeholder="Custom Value"):
            nonlocal row
            lbl = QLabel(label_text)
            lbl.setStyleSheet(label_style)
            lbl.setFixedHeight(field_height)
            combo = QComboBox()
            combo.addItems(combo_items)
            combo.setFixedSize(field_width, field_height)
            apply_field_style(combo)
            seismic_inputs_layout.addWidget(lbl, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
            seismic_inputs_layout.addWidget(combo, row, 1, Qt.AlignLeft)
            setattr(owner, attr_name, combo)

            if with_custom:
                custom = QLineEdit()
                custom.setPlaceholderText(placeholder)
                custom.setFixedSize(field_width, field_height)
                custom.setEnabled(False)
                apply_field_style(custom)
                seismic_inputs_layout.addWidget(custom, row, 2, Qt.AlignLeft)
                row += 1
                return combo, custom

            row += 1

            return combo, None

        def add_line_edit(label_text, attr_name, default=None):
            nonlocal row
            lbl = QLabel(label_text)
            lbl.setStyleSheet(label_style)
            lbl.setFixedHeight(field_height)
            line = QLineEdit()
            if default is not None:
                line.setText(default)
            line.setFixedSize(field_width, field_height)
            apply_field_style(line)
            seismic_inputs_layout.addWidget(lbl, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
            seismic_inputs_layout.addWidget(line, row, 1, Qt.AlignLeft)
            setattr(owner, attr_name, line)
            row += 1

        add_combo("Seismic Zone:", ["II", "III", "IV", "V"], "seismic_zone_combo")
        add_line_edit("Importance Factor:", "importance_factor_input", "1")
        add_combo("Type of Soil:", [
            "Type I – Rocky or Hard",
            "Type II – Medium Soil",
            "Type III – Soft Soil"
        ], "soil_type_combo")
        add_line_edit("Time Period:", "time_period_input")
        add_line_edit("Damping Percentage:", "damping_input", "2")
        add_combo("Response Reduction Factor:", ["1", "2", "3", "4", "5"], "response_factor_combo")
        owner.response_factor_combo.setCurrentText("1")
        _, owner.dead_load_custom_input = add_combo(
            "Dead Load for Seismic Force (kN):",
            ["Automatic", "Custom"],
            "dead_load_seismic_combo",
            with_custom=True,
        )

        _, owner.live_load_custom_input = add_combo(
            "Live Load for Seismic Force (kN):",
            ["Automatic", "Custom"],
            "live_load_seismic_combo",
            with_custom=True,
        )

        left_layout.addWidget(seismic_inputs_box)

        computed_box = QFrame()
        computed_box.setStyleSheet("QFrame { border: 1px solid #b2b2b2; border-radius: 8px; background-color: #ffffff; }")
        computed_layout = QGridLayout(computed_box)
        computed_layout.setContentsMargins(12, 16, 12, 16)
        computed_layout.setHorizontalSpacing(12)
        computed_layout.setVerticalSpacing(6)
        computed_layout.setColumnMinimumWidth(0, 200)

        computed_fields = [
            ("Zone Factor:", "zone_factor"),
            ("Spectral Acceleration Coefficient:", "spectral_coeff"),
            ("Horizontal Seismic Coefficient:", "horizontal_coeff"),
            ("Vertical Seismic Coefficient:", "vertical_coeff"),
        ]

        owner.seismic_computed_fields = {}
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
            owner.seismic_computed_fields[field_name] = field

        left_layout.addWidget(computed_box)
        left_layout.addStretch()

        right_card = owner._create_card()
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

        owner.dead_load_seismic_combo.currentTextChanged.connect(owner._on_dead_load_mode_changed)
        owner.live_load_seismic_combo.currentTextChanged.connect(owner._on_live_load_mode_changed)
