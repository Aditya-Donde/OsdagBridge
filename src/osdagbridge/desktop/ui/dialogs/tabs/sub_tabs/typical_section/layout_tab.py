"""Layout sub-tab for Typical Section Details."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator, QIntValidator

from osdagbridge.core.utils.common import DEFAULT_GIRDER_SPACING, MIN_FOOTPATH_WIDTH


class LayoutTab(QWidget):
    """Constructs the Layout tab UI and attaches widgets onto the owner."""

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.setStyleSheet("background-color: white;")
        self._build_ui()

    def _build_ui(self):
        owner = self.owner

        layout_layout = QVBoxLayout(self)
        layout_layout.setContentsMargins(18, 6, 18, 12)
        layout_layout.setSpacing(0)

        title_label = QLabel("Inputs:")
        title_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #000;")
        layout_layout.addWidget(title_label)
        layout_layout.addSpacing(8)

        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(10)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        grid.setContentsMargins(0, 0, 0, 0)

        def _label(text):
            lbl = QLabel(text)
            lbl.setStyleSheet("font-size: 11px; color: #000;")
            lbl.setMinimumWidth(180)
            return lbl

        owner.girder_spacing = QLineEdit()
        owner.girder_spacing.setValidator(QDoubleValidator(0.01, 50.0, 3))
        owner.girder_spacing.setText(str(DEFAULT_GIRDER_SPACING))
        owner.style_input_field(owner.girder_spacing)
        owner.girder_spacing.textChanged.connect(owner.on_girder_spacing_changed)

        owner.no_of_girders = QLineEdit()
        owner.no_of_girders.setValidator(QIntValidator(2, 100))
        owner.style_input_field(owner.no_of_girders)
        owner.no_of_girders.textChanged.connect(owner.on_no_of_girders_changed)

        grid.addWidget(_label("Girder Spacing (m):"), 0, 0, Qt.AlignLeft)
        grid.addWidget(owner.girder_spacing, 0, 1)
        grid.addWidget(_label("No. of Girders:"), 0, 2, Qt.AlignLeft)
        grid.addWidget(owner.no_of_girders, 0, 3)

        owner.deck_overhang = QLineEdit()
        owner.deck_overhang.setValidator(QDoubleValidator(0.0, 100.0, 3))
        default_overhang = 0.35 * DEFAULT_GIRDER_SPACING
        owner.deck_overhang.setText(f"{default_overhang:.3f}")
        owner.style_input_field(owner.deck_overhang)
        owner.deck_overhang.textChanged.connect(owner.on_deck_overhang_changed)

        grid.addWidget(_label("Deck Overhang Width (m):"), 1, 0, Qt.AlignLeft)
        grid.addWidget(owner.deck_overhang, 1, 1)

        owner.overall_bridge_width_display = QLineEdit()
        owner.style_input_field(owner.overall_bridge_width_display)
        owner.overall_bridge_width_display.setReadOnly(True)
        owner.overall_bridge_width_display.setToolTip(owner.overall_bridge_width_formula)
        owner.overall_bridge_width_display.textChanged.connect(owner._reject_overall_width_override)

        grid.addWidget(_label("Overall Bridge Width (m):"), 2, 0, Qt.AlignLeft)
        grid.addWidget(owner.overall_bridge_width_display, 2, 1)

        owner.deck_thickness = QLineEdit()
        owner.deck_thickness.setValidator(QDoubleValidator(100.0, 500.0, 0))
        owner.deck_thickness.setText("200")
        owner.style_input_field(owner.deck_thickness)
        owner.deck_thickness.editingFinished.connect(owner.validate_deck_thickness)

        owner.footpath_thickness = QLineEdit()
        owner.footpath_thickness.setValidator(QDoubleValidator(100.0, 500.0, 0))
        owner.footpath_thickness.setText("200")
        owner.style_input_field(owner.footpath_thickness)
        owner.footpath_thickness.editingFinished.connect(owner.validate_footpath_thickness)

        grid.addWidget(_label("Deck Thickness (mm):"), 3, 0, Qt.AlignLeft)
        grid.addWidget(owner.deck_thickness, 3, 1)
        grid.addWidget(_label("Footpath Thickness (mm):"), 4, 2, Qt.AlignLeft)
        grid.addWidget(owner.footpath_thickness, 4, 3)

        owner.footpath_width = QLineEdit()
        owner.footpath_width.setValidator(QDoubleValidator(MIN_FOOTPATH_WIDTH, 5.0, 3))
        owner.footpath_width.textChanged.connect(owner.on_footpath_width_changed)
        owner.style_input_field(owner.footpath_width)
        owner.footpath_width.setText(f"{MIN_FOOTPATH_WIDTH:.2f}")

        grid.addWidget(_label("Footpath Width (m):"), 4, 0, Qt.AlignLeft)
        grid.addWidget(owner.footpath_width, 4, 1)

        layout_layout.addLayout(grid)
        layout_layout.addStretch()

