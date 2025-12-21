"""Median sub-tab for Typical Section Details."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QComboBox, QLineEdit
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator


class MedianTab(QWidget):
    """Constructs the Median tab UI and binds fields to the owner."""

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.setStyleSheet("background-color: white;")
        self._build_ui()

    def _build_ui(self):
        owner = self.owner

        median_layout = QVBoxLayout(self)
        median_layout.setContentsMargins(18, 6, 18, 12)
        median_layout.setSpacing(0)

        card, card_layout = owner._create_section_card("Median Inputs:")
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(10)
        grid.setColumnStretch(1, 1)

        def add_row(row, label_text, widget):
            label = QLabel(label_text)
            label.setStyleSheet("font-size: 11px; color: #000;")
            label.setMinimumWidth(210)
            grid.addWidget(label, row, 0, Qt.AlignLeft)
            grid.addWidget(widget, row, 1)
            return label

        owner.median_type = QComboBox()
        owner.median_types = [
            "IRC 5 RCC",
            "IRC 5 High Containment RCC",
            "IRC 5 Metallic (Single W-Beam)",
            "IRC 5 Metallic (Double W-Beam)",
            "Custom",
        ]
        owner.median_type.addItems(owner.median_types)
        owner.style_input_field(owner.median_type)
        owner.median_type.currentTextChanged.connect(owner.on_median_type_changed)
        add_row(0, "Type:", owner.median_type)

        owner.median_density = QLineEdit()
        owner.median_density.setValidator(QDoubleValidator(0.0, 100.0, 2))
        owner.style_input_field(owner.median_density)
        owner.median_density_label = add_row(1, "Material Density (kN/m^3):", owner.median_density)

        owner.median_width = QLineEdit()
        owner.median_width.setValidator(QDoubleValidator(0.0, 3.0, 3))
        owner.style_input_field(owner.median_width)
        add_row(2, "Width (m):", owner.median_width)

        owner.median_height = QLineEdit()
        owner.median_height.setValidator(QDoubleValidator(0.0, 3.0, 3))
        owner.style_input_field(owner.median_height)
        add_row(3, "Height (m):", owner.median_height)

        owner.median_area = QLineEdit()
        owner.median_area.setValidator(QDoubleValidator(0.0, 10.0, 4))
        owner.style_input_field(owner.median_area)
        owner.median_area_label = add_row(4, "Area (m^2):", owner.median_area)

        owner.median_load = QLineEdit()
        owner.median_load.setValidator(QDoubleValidator(0.0, 500.0, 3))
        owner.style_input_field(owner.median_load)
        add_row(5, "Load (kN/m):", owner.median_load)

        owner.median_post_spacing = QLineEdit()
        owner.median_post_spacing.setValidator(QDoubleValidator(0.0, 10.0, 3))
        owner.style_input_field(owner.median_post_spacing)
        owner.median_post_spacing_label = add_row(6, "Spacing between Posts (m):", owner.median_post_spacing)

        card_layout.addLayout(grid)
        median_layout.addWidget(card)
        median_layout.addStretch()