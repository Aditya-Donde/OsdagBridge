"""Crash Barrier sub-tab for Typical Section Details (schema-driven)."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QComboBox, QLineEdit
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator

from osdagbridge.core.bridge_types.plate_girder.typical_section_schema import CRASH_BARRIER_TAB_SCHEMA


class CrashBarrierTab(QWidget):
    """Constructs the Crash Barrier tab UI and binds fields to the owner."""

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.setStyleSheet("background-color: white;")
        self._build_ui()

    def _create_field(self, field_def, field_width=200):
        owner = self.owner
        ftype = field_def.get("type")

        if ftype == "combo":
            field = QComboBox()
            field.addItems(field_def.get("choices") or [])
        else:
            field = QLineEdit()
            validator_def = field_def.get("validator")
            if validator_def:
                vtype = validator_def.get("type")
                if vtype == "double_range":
                    bottom = validator_def.get("bottom", 0.0)
                    top = validator_def.get("top", 1e9)
                    decimals = validator_def.get("decimals", 3)
                    field.setValidator(QDoubleValidator(bottom, top, decimals))

            default = field_def.get("default")
            if default is not None:
                field.setText(str(default))

        field.setObjectName(field_def.get("id", ""))
        field.setFixedWidth(field_width)
        owner.style_input_field(field)

        bind_name = field_def.get("bind")
        if bind_name:
            setattr(owner, bind_name, field)

        on_change = field_def.get("on_change")
        if on_change and hasattr(owner, on_change) and ftype == "combo":
            field.currentTextChanged.connect(getattr(owner, on_change))

        on_text_changed = field_def.get("on_text_changed")
        if on_text_changed and hasattr(owner, on_text_changed) and ftype != "combo":
            field.textChanged.connect(getattr(owner, on_text_changed))

        on_editing_finished = field_def.get("on_editing_finished")
        if on_editing_finished and hasattr(owner, on_editing_finished) and ftype != "combo":
            field.editingFinished.connect(getattr(owner, on_editing_finished))

        return field

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

        label_width = CRASH_BARRIER_TAB_SCHEMA.get("label_width", 200)

        row_idx = 0
        for row in CRASH_BARRIER_TAB_SCHEMA.get("rows", []):
            col = 0
            for field_def in row.get("fields", []):
                label = QLabel(field_def.get("label", ""))
                label.setStyleSheet("font-size: 11px; color: #000;")
                label.setMinimumWidth(label_width)
                grid.addWidget(label, row_idx, col, Qt.AlignLeft)
                col += 1

                # Preserve label handles used by visibility logic
                fid = field_def.get("id")
                if fid == "crash_barrier_density":
                    self.owner.crash_barrier_density_label = label
                if fid == "crash_barrier_area":
                    self.owner.crash_barrier_area_label = label
                if fid == "crash_barrier_post_spacing":
                    self.owner.crash_barrier_post_spacing_label = label

                field = self._create_field(field_def, field_width=200)
                grid.addWidget(field, row_idx, col)
                col += 1
            row_idx += 1

        card_layout.addLayout(grid)
        crash_layout.addWidget(card)
        crash_layout.addStretch()

