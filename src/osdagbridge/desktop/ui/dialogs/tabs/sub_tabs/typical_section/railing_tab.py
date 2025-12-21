"""Railing sub-tab for Typical Section Details."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QComboBox, QLineEdit, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator

from osdagbridge.core.utils.common import DEFAULT_RAILING_WIDTH, MIN_RAILING_HEIGHT, VALUES_RAILING_TYPE


class RailingTab(QWidget):
    """Constructs the Railing tab UI and binds fields to the owner."""

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.setStyleSheet("background-color: white;")
        self._build_ui()

    def _build_ui(self):
        owner = self.owner

        railing_layout = QVBoxLayout(self)
        railing_layout.setContentsMargins(18, 6, 18, 12)
        railing_layout.setSpacing(0)

        card, card_layout = owner._create_section_card("Railing Inputs:")
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(10)
        grid.setColumnStretch(1, 1)

        def add_row(row, label_text, widget):
            label = QLabel(label_text)
            label.setStyleSheet("font-size: 11px; color: #000;")
            label.setMinimumWidth(180)
            grid.addWidget(label, row, 0, Qt.AlignLeft)
            grid.addWidget(widget, row, 1)

        owner.railing_type = QComboBox()
        owner.railing_type.addItems(VALUES_RAILING_TYPE)
        owner.style_input_field(owner.railing_type)
        add_row(0, "Type:", owner.railing_type)

        owner.railing_width = QLineEdit()
        owner.railing_width.setValidator(QDoubleValidator(0.0, 2000.0, 1))
        owner.railing_width.setText(f"{DEFAULT_RAILING_WIDTH * 1000:.0f}")
        owner.style_input_field(owner.railing_width)
        owner.railing_width.textChanged.connect(owner.recalculate_girders)
        add_row(1, "Width (mm):", owner.railing_width)

        owner.railing_height = QLineEdit()
        owner.railing_height.setValidator(QDoubleValidator(MIN_RAILING_HEIGHT, 3.0, 3))
        owner.style_input_field(owner.railing_height)
        owner.railing_height.editingFinished.connect(owner.validate_railing_height)
        add_row(2, "Height (m):", owner.railing_height)

        load_row = QHBoxLayout()
        load_row.setContentsMargins(0, 0, 0, 0)
        load_row.setSpacing(12)

        owner.railing_load_mode = QComboBox()
        owner.railing_load_mode.addItems(["Automatic (IRC 6)", "User-defined"])
        owner.style_input_field(owner.railing_load_mode)
        owner.railing_load_mode.currentTextChanged.connect(owner.on_railing_load_mode_changed)
        load_row.addWidget(owner.railing_load_mode)

        owner.railing_load_value = QLineEdit()
        owner.railing_load_value.setValidator(QDoubleValidator(0.0, 50.0, 2))
        owner.railing_load_value.setPlaceholderText("Value")
        owner.railing_load_value.setEnabled(False)
        owner.style_input_field(owner.railing_load_value)
        load_row.addWidget(owner.railing_load_value)

        load_container = QWidget()
        load_container.setLayout(load_row)
        add_row(3, "Load (kN/m):", load_container)

        card_layout.addLayout(grid)
        railing_layout.addWidget(card)
        railing_layout.addStretch()

