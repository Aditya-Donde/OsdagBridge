"""Shared schema-driven sub-tab builder for Typical Section inner tabs."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QComboBox, QLineEdit,
    QTableWidget, QHeaderView, QSizePolicy,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator

from osdagbridge.core.utils.common import TYPE_COMBOBOX, TYPE_NOTICE, TYPE_TEXTBOX


class UIBuilder(QWidget):
    """Builds a card + grid from a tab schema dict."""

    def __init__(
        self,
        owner,
        schema: dict,
        card_title: str,
        main_widget_object_name: str,
        additional_input_instance=None,
        *,
        horizontal_spacing: int = 24,
        vertical_spacing: int = 10,
        filler_column_index: int | None = 2,
    ):
        super().__init__(owner)
        self.additional_input_instance = additional_input_instance
        self.owner = owner
        self._schema = schema
        self._card_title = card_title
        self._main_widget_object_name = main_widget_object_name
        self._horizontal_spacing = horizontal_spacing
        self._vertical_spacing = vertical_spacing
        self._filler_column_index = filler_column_index
        self.setStyleSheet("background-color: white;")
        self._build_ui()

    def _build_ui(self):
        owner = self.owner
        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 6, 18, 12)
        outer.setSpacing(0)

        self.main_widget = QWidget(self)
        self.main_widget.setObjectName(self._main_widget_object_name)
        main_layout = QVBoxLayout(self.main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        card, card_layout = owner._create_section_card(self._card_title)
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(self._horizontal_spacing)
        grid.setVerticalSpacing(self._vertical_spacing)

        # Pre-calculate max fields in any row to set column stretches correctly
        all_rows = self._schema.get("rows") or []
        max_fields = max(
            (len(row.get("fields") or []) for row in all_rows),
            default=1
        )
        filler_col = max_fields * 2
        for c in range(filler_col):
            grid.setColumnStretch(c, 0)
        if self._filler_column_index is not None:
            grid.setColumnStretch(filler_col, 1)
        else:
            grid.setColumnStretch(filler_col - 1, 1)

        label_width = self._schema.get("label_width", 200)
        row_idx = 0
        for row in all_rows:
            fields = row.get("fields") or []
            col = 0
            for field_def in fields:
                ftype = field_def.get("type")

                if not ftype:  # empty placeholder — skip label, add empty spacer
                    grid.addWidget(QWidget(), row_idx, col)      # empty label col
                    grid.addWidget(QWidget(), row_idx, col + 1)  # empty field col
                    col += 2
                    continue

                if ftype == "table_with_count":
                    container = self._build_table_with_count(field_def, label_width)
                    grid.addWidget(container, row_idx, 0, 1, -1)
                    grid.setColumnStretch(0, 1)
                    col += 2
                else:
                    label = QLabel(field_def.get("label") or "")
                    label.setStyleSheet("font-size: 11px; color: #000;")
                    label.setMinimumWidth(label_width)
                    label.setObjectName((field_def.get("id") or "") + "_label")
                    grid.addWidget(label, row_idx, col, Qt.AlignLeft)

                    field = self._create_field(field_def, field_width=200)
                    grid.addWidget(field, row_idx, col + 1, Qt.AlignLeft)
                    col += 2

            row_idx += 1

        card_layout.addLayout(grid)
        main_layout.addWidget(card)
        outer.addWidget(self.main_widget)
        outer.addStretch()

    def _create_field(self, field_def, field_width=260):
        owner = self.owner
        ftype = field_def.get("type")

        if ftype == TYPE_COMBOBOX:
            field = QComboBox()
            choices = field_def.get("choices") or []
            field.addItems(choices)
            field.setSizeAdjustPolicy(QComboBox.AdjustToContents)
            field.setMinimumContentsLength(max((len(c) for c in choices), default=0))
            field.view().setMinimumWidth(320)
        elif ftype == TYPE_TEXTBOX:
            field = QLineEdit()
            placeholder = field_def.get("placeholder")
            if placeholder:
                field.setPlaceholderText(placeholder)
            if field_def.get("enabled") is False:
                field.setEnabled(False)
            
            if field_def.get("read_only"):
                field.setReadOnly(True)
                field.setEnabled(False)
                field.setStyleSheet(
                    "QLineEdit { background-color: #f2f2f2; color: #666;"
                    " border: 1px solid #c0c0c0; border-radius: 4px; padding: 4px 6px; }"
                )
        elif ftype == TYPE_NOTICE:
            notice_container, adjust_lbl, warning_lbl = self._build_notice_container()
            setattr(owner, field_def["bind_adjust"],    adjust_lbl)
            setattr(owner, field_def["bind_warning"],   warning_lbl)
            setattr(owner, field_def["bind_container"], notice_container)
            return notice_container
        else:
            return QWidget()

        field.setObjectName(field_def["id"])
        field.setFixedWidth(field_width)
        owner.style_input_field(field)

        tooltip_attr = field_def.get("tooltip")
        if tooltip_attr and hasattr(owner, tooltip_attr):
            field.setToolTip(getattr(owner, tooltip_attr))

        bind_name = field_def.get("bind")
        if bind_name:
            setattr(owner, bind_name, field)

        field_id = field_def["id"]
        ai = self.additional_input_instance

        if ftype == TYPE_COMBOBOX:

            # This will validate the input, either it say nothing or popup warning and set specific valid value
            field.currentTextChanged.connect(lambda text, k=field_id: ai._on_field_edited(k, text))
            
            on_change = field_def.get("on_change")
            if on_change and hasattr(owner, on_change):
                field.currentTextChanged.connect(getattr(owner, on_change))

        elif ftype == TYPE_TEXTBOX:

            # For soft-validation while value is being edited in the textbox
            field.textChanged.connect(lambda text, k=field_id: ai._on_field_editing(text, k))

            # Signal that change in value so to update the input_dictionary
            field.editingFinished.connect(lambda k=field_id, w=field: ai._on_field_edited(k, w))
            
            on_text_changed = field_def.get("on_text_changed")
            if on_text_changed and hasattr(owner, on_text_changed):
                field.textChanged.connect(getattr(owner, on_text_changed))
            on_editing_finished = field_def.get("on_editing_finished")
            if on_editing_finished and hasattr(owner, on_editing_finished):
                field.editingFinished.connect(getattr(owner, on_editing_finished))

        return field

    def _build_table_with_count(self, field_def: dict, label_width: int = 200) -> QWidget:
        """Build a self-contained widget with label, count-combo, and table.

        Object names follow the convention:
          label  -> <id>_label
          combo  -> <count_id>          (already the full schema key, e.g. KEY_WC_LD_LANE_TABLE_COUNT)
          table  -> <id>                (e.g. KEY_WC_LD_LANE_TABLE)
        """
        owner = self.owner
        field_id  = field_def.get("id", "")
        count_id  = field_def.get("count_id", "")

        container = QWidget()
        container.setObjectName(field_id + "_container")
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # ── Row: label + combo ──────────────────────────────────────────────
        from PySide6.QtWidgets import QHBoxLayout
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(8)

        label = QLabel(field_def.get("label") or "")
        label.setObjectName(field_id + "_label")
        label.setStyleSheet("font-size: 11px; color: #000;")
        label.setMinimumWidth(label_width)
        header_row.addWidget(label, 0, Qt.AlignVCenter)

        combo = QComboBox()
        combo.setObjectName(count_id)
        combo.addItems(field_def.get("count_choices") or [])
        combo.setFixedWidth(80)
        owner.style_input_field(combo)
        header_row.addWidget(combo, 0, Qt.AlignVCenter)
        header_row.addStretch()

        layout.addLayout(header_row)

        # ── Table ───────────────────────────────────────────────────────────
        columns = field_def.get("columns", [])
        table = QTableWidget()
        table.setObjectName(field_id)
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels([c["header"] for c in columns])
        table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        resize_map = {
            "contents": QHeaderView.ResizeToContents,
            "stretch":  QHeaderView.Stretch,
            "fixed":    QHeaderView.Fixed,
        }
        h = table.horizontalHeader()
        h.setStretchLastSection(False)
        for i, col in enumerate(columns):
            h.setSectionResizeMode(i, resize_map.get(col.get("resize", "stretch"), QHeaderView.Stretch))

        table.verticalHeader().setVisible(field_def.get("show_vertical_header", False))
        table.setAlternatingRowColors(field_def.get("alternating_rows", True))
        table.setStyleSheet("""
            QTableWidget { background-color:#ffffff; alternate-background-color:#f9f9f9;
                           gridline-color:#e0e0e0; border:1px solid #e0e0e0; color:#333333; }
            QTableWidget::item { padding:8px; border-bottom:1px solid #e0e0e0; color:#333333; }
            QTableWidget::item:hover    { background-color:#e8f4f8; color:#333333; }
            QTableWidget::item:selected { background-color:#d0e8f0; color:#333333; }
            QHeaderView::section { background-color:#f5f5f5; color:#333333; padding:8px;
                                   border:1px solid #e0e0e0; font-weight:bold; font-size:11px; }
        """)
        layout.addWidget(table)

        on_count_change = field_def.get("on_count_change") or ""
        if on_count_change and hasattr(owner, on_count_change):
            combo.currentTextChanged.connect(getattr(owner, on_count_change))

        return container

    def _build_notice_container(self, field_width=280):
        from PySide6.QtWidgets import QVBoxLayout

        adjust_lbl = QLabel()
        adjust_lbl.setStyleSheet(
            "font-size: 10px; font-style: italic; color: #000000; background-color: transparent;"
        )
        adjust_lbl.setWordWrap(True)
        adjust_lbl.setFixedWidth(field_width)
        adjust_lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        adjust_lbl.hide()

        warning_lbl = QLabel()
        warning_lbl.setStyleSheet(
            "font-size: 10px; font-style: italic; color: #cc6600; background-color: transparent;"
        )
        warning_lbl.setWordWrap(True)
        warning_lbl.setFixedWidth(field_width)
        warning_lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        warning_lbl.hide()

        container = QWidget()
        container.setFixedWidth(field_width)
        container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        container.hide()

        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(2)
        vbox.addWidget(adjust_lbl)
        vbox.addWidget(warning_lbl)

        return container, adjust_lbl, warning_lbl