"""Crash Barrier sub-tab for Typical Section Details."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QComboBox, QLineEdit
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator

from osdagbridge.core.utils.common import DEFAULT_CRASH_BARRIER_WIDTH


class CrashBarrierTab(QWidget):
    """Constructs the Crash Barrier tab UI and binds fields to the owner."""

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.setStyleSheet("background-color: white;")
        self._build_ui()

    def _build_ui(self):
        owner = self.owner

        crash_layout = QVBoxLayout(self)
        crash_layout.setContentsMargins(18, 6, 18, 12)
        crash_layout.setSpacing(0)

        card, card_layout = owner._create_section_card("Crash Barrier Inputs:")
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

        owner.crash_barrier_type = QComboBox()
        owner.crash_barrier_types = [
            "IRC 5 RCC",
            "IRC 5 High Containment RCC",
            "IRC 5 Metallic (Single W-Beam)",
            "IRC 5 Metallic (Double W-Beam)",
            "Custom",
        ]
        owner.crash_barrier_type.addItems(owner.crash_barrier_types)
        owner.style_input_field(owner.crash_barrier_type)
        owner.crash_barrier_type.currentTextChanged.connect(owner.on_crash_barrier_type_changed)
        add_row(0, "Type:", owner.crash_barrier_type)

        owner.crash_barrier_density = QLineEdit()
        owner.crash_barrier_density.setValidator(QDoubleValidator(0.0, 100.0, 2))
        owner.style_input_field(owner.crash_barrier_density)
        owner.crash_barrier_density.editingFinished.connect(owner._auto_compute_crash_barrier_load)
        owner.crash_barrier_density_label = add_row(1, "Material Density (kN/m^3):", owner.crash_barrier_density)

        owner.crash_barrier_width = QLineEdit()
        owner.crash_barrier_width.setValidator(QDoubleValidator(0.0, 2.0, 3))
        owner.crash_barrier_width.setText(str(DEFAULT_CRASH_BARRIER_WIDTH))
        owner.style_input_field(owner.crash_barrier_width)
        owner.crash_barrier_width.textChanged.connect(owner.recalculate_girders)
        add_row(2, "Width (m):", owner.crash_barrier_width)

        owner.crash_barrier_height = QLineEdit()
        owner.crash_barrier_height.setValidator(QDoubleValidator(0.0, 3.0, 3))
        owner.style_input_field(owner.crash_barrier_height)
        add_row(3, "Height (m):", owner.crash_barrier_height)

        owner.crash_barrier_area = QLineEdit()
        owner.crash_barrier_area.setValidator(QDoubleValidator(0.0, 10.0, 4))
        owner.style_input_field(owner.crash_barrier_area)
        owner.crash_barrier_area.editingFinished.connect(owner._auto_compute_crash_barrier_load)
        owner.crash_barrier_area_label = add_row(4, "Area (m^2):", owner.crash_barrier_area)

        owner.crash_barrier_load = QLineEdit()
        owner.crash_barrier_load.setValidator(QDoubleValidator(0.0, 500.0, 3))
        owner.style_input_field(owner.crash_barrier_load)
        owner.crash_barrier_load_label = add_row(5, "Load (kN/m):", owner.crash_barrier_load)

        owner.crash_barrier_post_spacing = QLineEdit()
        owner.crash_barrier_post_spacing.setValidator(QDoubleValidator(0.0, 10.0, 3))
        owner.style_input_field(owner.crash_barrier_post_spacing)
        owner.crash_barrier_post_spacing_label = add_row(6, "Spacing between Posts (m):", owner.crash_barrier_post_spacing)

        card_layout.addLayout(grid)
        crash_layout.addWidget(card)
        crash_layout.addStretch()

