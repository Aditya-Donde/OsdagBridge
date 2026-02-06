"""Layout sub-tab for Typical Section Details (schema-driven)."""
import copy
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator, QIntValidator

from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import LAYOUT_TAB_SCHEMA
from osdagbridge.core.utils.common import DEFAULT_GIRDER_SPACING
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style


class LayoutTab(QWidget):
    """Constructs the Layout tab UI and attaches widgets onto the owner."""

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.setStyleSheet("background-color: white;")
        self._build_ui()

    def _create_field(self, field_def, default_width=180):
        owner = self.owner
        ftype = field_def.get("type")
        field = QLineEdit()

        validator_def = field_def.get("validator")
        if validator_def:
            vtype = validator_def.get("type")
            if vtype == "double_range":
                bottom = validator_def.get("bottom", 0.0)
                top = validator_def.get("top", 1e9)
                decimals = validator_def.get("decimals", 3)
                field.setValidator(QDoubleValidator(bottom, top, decimals))
            elif vtype == "int_range":
                bottom = validator_def.get("bottom", 0)
                top = validator_def.get("top", 1e9)
                field.setValidator(QIntValidator(bottom, top))

        default = field_def.get("default")
        if default is not None:
            field.setText(str(default))

        if field_def.get("read_only"):
            field.setReadOnly(True)

        apply_field_style(field)
        field.setFixedWidth(default_width)
        field.setObjectName(field_def.get("id", ""))

        # Make read-only displays visually disabled without breaking styling
        if field_def.get("id") == "overall_bridge_width_display":
            field.setEnabled(False)
            field.setStyleSheet(
                "QLineEdit { background-color: #f2f2f2; color: #666;"
                " border: 1px solid #c0c0c0; border-radius: 4px; padding: 4px 6px; }"
            )

        bind_name = field_def.get("bind")
        if bind_name:
            setattr(owner, bind_name, field)

        on_text_changed = field_def.get("on_text_changed")
        if on_text_changed and hasattr(owner, on_text_changed):
            field.textChanged.connect(getattr(owner, on_text_changed))

        on_editing_finished = field_def.get("on_editing_finished")
        if on_editing_finished and hasattr(owner, on_editing_finished):
            field.editingFinished.connect(getattr(owner, on_editing_finished))

        return field

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

        schema_rows = copy.deepcopy(LAYOUT_TAB_SCHEMA.get("rows", []))
        for row in schema_rows:
            for field_def in row.get("fields", []):
                if field_def.get("id") == "deck_overhang" and field_def.get("default") is None:
                    field_def["default"] = f"{0.35 * DEFAULT_GIRDER_SPACING:.3f}"

        # Create adjustment notice label (shown when values are auto-adjusted)
        owner.layout_adjust_notice = QLabel()
        owner.layout_adjust_notice.setStyleSheet(
            "font-size: 10px; font-style: italic; color: #000000; background-color: transparent;"
        )
        owner.layout_adjust_notice.setWordWrap(True)
        owner.layout_adjust_notice.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        owner.layout_adjust_notice.setFixedWidth(180)
        owner.layout_adjust_notice.hide()
        
        # Create warning notice label (shown when overhang exceeds spacing)
        owner.layout_warning_notice = QLabel()
        owner.layout_warning_notice.setStyleSheet(
            "font-size: 10px; font-style: italic; color: #cc6600; background-color: transparent;"
        )
        owner.layout_warning_notice.setWordWrap(True)
        owner.layout_warning_notice.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        owner.layout_warning_notice.setFixedWidth(180)
        owner.layout_warning_notice.hide()

        # Container so notices don't resize grid columns (prevents UI shifting)
        owner.layout_notice_container = QWidget()
        owner.layout_notice_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        owner.layout_notice_container.setFixedWidth(180)
        notice_layout = QVBoxLayout(owner.layout_notice_container)
        notice_layout.setContentsMargins(0, 0, 0, 0)
        notice_layout.setSpacing(4)
        notice_layout.addWidget(owner.layout_adjust_notice)
        notice_layout.addWidget(owner.layout_warning_notice)
        owner.layout_notice_container.hide()

        row_idx = 0
        for row_num, row in enumerate(schema_rows):
            col = 0
            for field_def in row.get("fields", []):
                lbl = _label(field_def.get("label", ""))
                grid.addWidget(lbl, row_idx, col, Qt.AlignLeft)
                col += 1

                field = self._create_field(field_def, default_width=180)
                grid.addWidget(field, row_idx, col)
                col += 1

                # Special tooltip for overall width
                if field_def.get("id") == "overall_bridge_width_display":
                    field.setToolTip(owner.overall_bridge_width_formula)

            row_idx += 1

        # Place notices under the "No. of Girders" LABEL (row 0, col 2)
        # Row 1 col 2 is empty in the schema (only left-side field), so it's the ideal anchor.
        grid.addWidget(owner.layout_notice_container, 1, 2, 1, 1, Qt.AlignLeft | Qt.AlignTop)

        layout_layout.addLayout(grid)

        layout_layout.addStretch()

