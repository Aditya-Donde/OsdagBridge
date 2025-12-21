"""Wearing Course sub-tab for Typical Section Details."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QComboBox, QLineEdit
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator

from osdagbridge.core.utils.common import VALUES_WEARING_COAT_MATERIAL


class WearingCourseTab(QWidget):
    """Constructs the Wearing Course tab UI and binds fields to the owner."""

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.setStyleSheet("background-color: white;")
        self._build_ui()

    def _build_ui(self):
        owner = self.owner

        wearing_layout = QVBoxLayout(self)
        wearing_layout.setContentsMargins(18, 6, 18, 12)
        wearing_layout.setSpacing(0)

        card, card_layout = owner._create_section_card("Wearing Course Inputs:")
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(10)
        grid.setColumnStretch(1, 1)

        def add_row(row, label_text, widget):
            label = QLabel(label_text)
            label.setStyleSheet("font-size: 11px; color: #000;")
            label.setMinimumWidth(200)
            grid.addWidget(label, row, 0, Qt.AlignLeft)
            grid.addWidget(widget, row, 1)

        owner.wearing_material = QComboBox()
        owner.wearing_material.addItems(VALUES_WEARING_COAT_MATERIAL)
        owner.style_input_field(owner.wearing_material)
        add_row(0, "Material:", owner.wearing_material)

        owner.wearing_density = QLineEdit()
        owner.wearing_density.setValidator(QDoubleValidator(0.0, 40.0, 2))
        owner.style_input_field(owner.wearing_density)
        add_row(1, "Density (kN/m^3):", owner.wearing_density)

        owner.wearing_thickness = QLineEdit()
        owner.wearing_thickness.setValidator(QDoubleValidator(0.0, 200.0, 1))
        owner.style_input_field(owner.wearing_thickness)
        add_row(2, "Thickness (mm):", owner.wearing_thickness)

        card_layout.addLayout(grid)
        wearing_layout.addWidget(card)
        wearing_layout.addStretch()

