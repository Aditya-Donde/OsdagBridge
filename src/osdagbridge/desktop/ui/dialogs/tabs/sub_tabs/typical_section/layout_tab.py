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

    def __init__(self, owner, row_indices=None, show_title=True, add_bottom_stretch=True):
        super().__init__(owner)
        self.owner = owner
        self.row_indices = row_indices
        self.show_title = show_title
        self.add_bottom_stretch = add_bottom_stretch
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

        if self.show_title:
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

        all_schema_rows = copy.deepcopy(LAYOUT_TAB_SCHEMA.get("rows", []))
        if self.row_indices is None:
            schema_rows = all_schema_rows
            selected_indices = set(range(len(all_schema_rows)))
        else:
            selected_indices = set(self.row_indices)
            schema_rows = [
                row for idx, row in enumerate(all_schema_rows)
                if idx in selected_indices
            ]

        for row in schema_rows:
            for field_def in row.get("fields", []):
                if field_def.get("id") == "deck_overhang" and field_def.get("default") is None:
                    field_def["default"] = f"{0.35 * DEFAULT_GIRDER_SPACING:.3f}"

        includes_primary_layout_rows = 0 in selected_indices or 1 in selected_indices
        if includes_primary_layout_rows and not hasattr(owner, "layout_notice_container"):
            # Create adjustment notice label (shown when values are auto-adjusted)
            owner.layout_adjust_notice = QLabel()
            owner.layout_adjust_notice.setStyleSheet(
                "font-size: 10px; font-style: italic; color: #000000; background-color: transparent;"
            )
            owner.layout_adjust_notice.setWordWrap(False)
            owner.layout_adjust_notice.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            owner.layout_adjust_notice.setFixedWidth(180)
            owner.layout_adjust_notice.setFixedHeight(16)
            owner.layout_adjust_notice.hide()

            # Create warning notice label (shown when overhang exceeds spacing)
            owner.layout_warning_notice = QLabel()
            owner.layout_warning_notice.setStyleSheet(
                "font-size: 10px; font-style: italic; color: #cc6600; background-color: transparent;"
            )
            owner.layout_warning_notice.setWordWrap(False)
            owner.layout_warning_notice.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            owner.layout_warning_notice.setFixedWidth(180)
            owner.layout_warning_notice.setFixedHeight(16)
            owner.layout_warning_notice.hide()

            # Container so notices don't resize grid columns (prevents UI shifting)
            owner.layout_notice_container = QWidget()
            owner.layout_notice_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            owner.layout_notice_container.setFixedWidth(180)
            owner.layout_notice_container.setFixedHeight(16)
            notice_layout = QVBoxLayout(owner.layout_notice_container)
            notice_layout.setContentsMargins(0, 0, 0, 0)
            notice_layout.setSpacing(0)
            notice_layout.addWidget(owner.layout_adjust_notice)
            notice_layout.addWidget(owner.layout_warning_notice)
            owner.layout_notice_container.hide()

        is_primary_grid = selected_indices == {0, 1, 2}
        if is_primary_grid:
            field_defs_by_id = {}
            for row in schema_rows:
                for field_def in row.get("fields", []):
                    field_defs_by_id[field_def.get("id")] = field_def

            # Keep top block balanced: two fields on left, two on right.
            ordered_positions = [
                ("girder_spacing", 0, 0),
                ("no_of_girders", 0, 2),
                ("overall_bridge_width_display", 1, 2),
                ("deck_overhang", 1, 0),
            ]

            for field_id, row_idx, label_col in ordered_positions:
                field_def = field_defs_by_id.get(field_id)
                if not field_def:
                    continue

                lbl = _label(field_def.get("label", ""))
                grid.addWidget(lbl, row_idx, label_col, Qt.AlignLeft)

                field = self._create_field(field_def, default_width=180)
                grid.addWidget(field, row_idx, label_col + 1)

                if field_id == "overall_bridge_width_display":
                    field.setToolTip(owner.overall_bridge_width_formula)
        else:
            row_idx = 0
            for row in schema_rows:
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

        if includes_primary_layout_rows and hasattr(owner, "layout_notice_container"):
            # Place notices under the "No. of Girders" label for the primary layout fields.
            notice_row = 2 if is_primary_grid else 1
            grid.addWidget(owner.layout_notice_container, notice_row, 2, 1, 1, Qt.AlignLeft | Qt.AlignTop)

        layout_layout.addLayout(grid)

        if self.add_bottom_stretch:
            layout_layout.addStretch()

