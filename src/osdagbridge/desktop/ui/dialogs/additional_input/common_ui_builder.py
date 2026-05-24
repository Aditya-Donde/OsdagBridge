"""Shared schema-driven sub-tab builder for Typical Section inner tabs."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QComboBox, QLineEdit,
    QTableWidget, QHeaderView, QSizePolicy, QCheckBox, QGroupBox,
    QHBoxLayout, QFrame, QPushButton, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator, QIntValidator

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QComboBox, QLineEdit,
    QTableWidget, QHeaderView, QSizePolicy, QCheckBox,
    QHBoxLayout, QFrame, QPushButton, QScrollArea
)

from osdagbridge.core.utils.common import *

ADDITIONAL_INPUTS_SCROLL_STYLE = """
    QScrollArea { background:transparent; padding:0px 5px; border:none}
    QScrollArea QScrollBar:vertical { border:none; background:#f0f0f0; width:8px; }
    QScrollArea QScrollBar::handle:vertical { background:#c0c0c0; border-radius:4px; min-height:20px; }
    QScrollArea QScrollBar::handle:vertical:hover { background:#a0a0a0; }
    QScrollArea QScrollBar::add-line:vertical,
    QScrollArea QScrollBar::sub-line:vertical { border:none; background:none; }
"""

class UIBuilder(QWidget):
    """Builds a card + grid from a tab schema dict."""

    def __init__(
        self,
        owner,
        schema: dict,
        card_title: str,
        main_widget_object_name: str,
        additional_input_instance,
        *,
        with_scroll: bool = False,
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
        self._with_scroll = with_scroll
        self.setStyleSheet("background-color: white;")
        self._build_ui()

    # ──────────────────────────────────────────────────────────────────────────
    # Top-level build — routes to correct layout strategy
    # ──────────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 6, 18, 12)
        outer.setSpacing(0)

        self.main_widget = QWidget(self)
        self.main_widget.setObjectName(self._main_widget_object_name)
        main_layout = QVBoxLayout(self.main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        layout_def  = self._schema.get("layout", {})
        layout_type = layout_def.get("type", "rows")

        if layout_type == "columns":
            self._build_columns_layout(main_layout, layout_def)
        elif layout_type == "rows" and "sections" in self._schema:
            # Explicit rows layout with sections
            for section in self._schema["sections"]:
                self._build_section(section, main_layout)
        elif "sections" in self._schema:
            # sections present, no layout key — default stacked
            for section in self._schema["sections"]:
                self._build_section(section, main_layout)
        elif "cards" in self._schema:
            for card_schema in self._schema["cards"]:
                card, card_layout = self._create_section_card(card_schema.get("title", ""))
                for section in card_schema.get("sections", []):
                    self._build_grid(section, card_layout)
                main_layout.addWidget(card)
        else:
            # Single card — Typical Section subtabs (has "rows" directly)
            card, card_layout = self._create_section_card(self._card_title)
            self._build_grid(self._schema, card_layout)
            main_layout.addWidget(card)

        if self._with_scroll:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setStyleSheet(ADDITIONAL_INPUTS_SCROLL_STYLE)
            scroll.setWidget(self.main_widget)
            outer.addWidget(scroll)
        else:
            outer.addWidget(self.main_widget)
            outer.addStretch()

    # ──────────────────────────────────────────────────────────────────────────
    # Layout strategies
    # ──────────────────────────────────────────────────────────────────────────

    def _build_columns_layout(self, parent_layout, layout_def):
        """Place sections into columns based on their 'column' key."""
        num_cols   = layout_def.get("columns", 2)
        col_widths = layout_def.get("column_widths", [1] * num_cols)

        row = QHBoxLayout()
        row.setSpacing(16)

        col_layouts = []
        for i in range(num_cols):
            col_widget = QWidget()
            col_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            col_layout = QVBoxLayout(col_widget)
            col_layout.setContentsMargins(0, 0, 0, 0)
            col_layout.setSpacing(12)
            col_layouts.append(col_layout)
            stretch = col_widths[i] if i < len(col_widths) else 1
            row.addWidget(col_widget, stretch)

        for section in self._schema.get("sections", []):
            col_idx = section.get("column", 0)
            col_idx = max(0, min(col_idx, num_cols - 1))
            stype   = section.get("type")
            stretch = 1 if section.get("stretch") else 0

            if stype == TYPE_DESCRIPTION:
                self._build_description_box(section, col_layouts[col_idx], stretch=stretch)
            else:
                self._build_section(section, col_layouts[col_idx])

        for col_layout in col_layouts:
            col_layout.addStretch()

        parent_layout.addLayout(row)

    def _build_description_box(self, section: dict, parent_layout, stretch: int = 0):
        """Styled grey description box."""
        box = QFrame()
        box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        box.setStyleSheet("""
            QFrame {
                border: 1px solid #9c9c9c;
                border-radius: 10px;
                background-color: #d4d4d4;
            }
        """)
        layout = QVBoxLayout(box)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = section.get("title", "")
        if title:
            lbl = QLabel(title)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(
                "font-size: 12px; font-weight: 700; color: #000; border: none;"
            )
            layout.addWidget(lbl)

        text = section.get("text", "")
        if text:
            txt = QLabel(text)
            txt.setWordWrap(True)
            txt.setStyleSheet("font-size: 11px; color: #4b4b4b; border: none;")
            layout.addWidget(txt)

        layout.addStretch()
        parent_layout.addWidget(box, stretch)

    def _build_section(self, section: dict, parent_layout):
        """Build one section — checkbox groups or a normal card with grid."""

        # ── Normal card with grid ──────────────────────────────────────────
        card, card_layout = self._create_section_card(section.get("title", ""))
        self._build_grid(section, card_layout)
        parent_layout.addWidget(card)

    def _create_section_card(self, title: str):
        """Create a bordered card frame with optional title."""
        card = QFrame()
        card.setObjectName("sectionCard")
        card.setStyleSheet("""
            QFrame#sectionCard {
                background-color: white;
                border: 1px solid #b2b2b2;
                border-radius: 8px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(12)
        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet(
                "font-size: 12px; font-weight: bold; color: #000;"
                " border: none; background: transparent;"
            )
            card_layout.addWidget(title_label)
        return card, card_layout

    def _build_grid(self, schema: dict, card_layout):
        """Build a QGridLayout from schema rows and add it to card_layout."""
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(self._horizontal_spacing)
        grid.setVerticalSpacing(self._vertical_spacing)

        all_rows = schema.get("rows") or []
        max_fields = max(
            (len(row.get("fields") or []) for row in all_rows if not row.get("row_fields")),
            default=1
        )
        filler_col = max_fields * 2
        for c in range(filler_col):
            grid.setColumnStretch(c, 0)

        label_width = schema.get("label_width", self._schema.get("label_width", 200))
        row_idx = 0

        for row in all_rows:

            # ── Inline row_fields (e.g. "Limit : L / [field] m") ──────────
            if row.get("row_fields"):
                h = QHBoxLayout()
                h.setContentsMargins(0, 0, 0, 0)
                h.setSpacing(8)
                for item in row["row_fields"]:
                    if item.get("type") == "label":
                        lbl = QLabel(item.get("label", ""))
                        lbl.setStyleSheet("font-size: 11px; color: #000;")
                        h.addWidget(lbl)
                        if item.get("after_spacing"):
                            h.addSpacing(item["after_spacing"])
                    else:
                        f = self._create_field(item, field_width=item.get("width", 150))
                        h.addWidget(f)
                h.addStretch()
                wrapper = QWidget()
                wrapper.setLayout(h)
                grid.addWidget(wrapper, row_idx, 0, 1, -1)
                row_idx += 1
                continue

            # ── Normal fields row ──────────────────────────────────────────
            fields = row.get("fields") or []
            col = 0
            for field_def in fields:
                ftype = field_def.get("type")

                if not ftype:
                    # Empty placeholder
                    grid.addWidget(QWidget(), row_idx, col)
                    grid.addWidget(QWidget(), row_idx, col + 1)
                    col += 2
                    continue

                if ftype == TYPE_TABLE_WITH_COUNTER:
                    container = self._build_table_with_count(field_def, label_width)
                    grid.addWidget(container, row_idx, 0, 1, -1)
                    grid.setColumnStretch(0, 1)
                    col += 2
                elif ftype == TYPE_NOTICE:
                    # Notice has no label
                    field = self._create_field(field_def, field_width=200)
                    grid.addWidget(field, row_idx, col + 1, Qt.AlignLeft)
                    col += 2
                elif ftype == TYPE_DIRECT_WIDGET:
                    field = self._create_field(field_def)
                    field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                    field.setMinimumSize(200, 200)
                    grid.addWidget(field, row_idx, col, 1, 2)
                    col += 2
                elif ftype == TYPE_LOAD_COMBINATION:
                    field = self._create_field(field_def)
                    field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                    grid.addWidget(field, row_idx, col, 1, 2)
                    col += 2
                elif ftype == TYPE_CUSTOM_VEHICLE:
                    from osdagbridge.desktop.ui.dialogs.additional_input._custom_vehicle_widget import CustomVehicleWidget
                    field = CustomVehicleWidget(
                        field_id=field_def.get("id", ""),
                        on_click=field_def.get("on_click", ""),
                        owner=self.additional_input_instance,
                        ai=self.additional_input_instance,
                    )
                    grid.addWidget(field, row_idx, col, 1, 2)
                    col += 2
                elif ftype == TYPE_CHECKBOX:
                    label_first = field_def.get("label_first", False)
                    if label_first:
                        # label on left, checkbox on right
                        label = QLabel(field_def.get("label") or "")
                        label.setStyleSheet("font-size: 11px; color: #000;")
                        label.setMinimumWidth(label_width)
                        grid.addWidget(label, row_idx, col, Qt.AlignLeft)
                        field = self._create_field(field_def)
                        grid.addWidget(field, row_idx, col + 1, Qt.AlignLeft)
                    else:
                        # checkbox with label built in — spans both cols
                        field = self._create_field(field_def)
                        grid.addWidget(field, row_idx, col, 1, 2)
                    col += 2
                else:
                    label = QLabel(field_def.get("label") or "")
                    label.setTextFormat(Qt.RichText)
                    label.setStyleSheet("font-size: 11px; color: #000;")
                    label.setMinimumWidth(label_width)
                    label.setObjectName((field_def.get("id") or "") + "_label")
                    grid.addWidget(label, row_idx, col, Qt.AlignLeft)

                    field = self._create_field(field_def, field_width=200)
                    grid.addWidget(field, row_idx, col + 1, Qt.AlignLeft)
                    col += 2

            row_idx += 1

        card_layout.addLayout(grid)

    # ──────────────────────────────────────────────────────────────────────────
    # Field factory
    # ──────────────────────────────────────────────────────────────────────────

    def _create_field(self, field_def, field_width=260):
        """Create and wire a single field widget from a field_def dict."""
        owner = self.owner
        ftype = field_def.get("type")
        ai    = self.additional_input_instance

        # Normalize type aliases
        if ftype == "line":
            ftype = TYPE_TEXTBOX

        # ── Build widget ───────────────────────────────────────────────────
        if ftype == TYPE_COMBOBOX:
            field = QComboBox()
            choices = field_def.get("choices") or []
            field.addItems(choices)
            field.setSizeAdjustPolicy(QComboBox.AdjustToContents)
            field.setMinimumContentsLength(max((len(c) for c in choices), default=0))

            # enabled_choices — disable others with grey + forbidden cursor
            enabled_choices = field_def.get("enabled_choices")
            if enabled_choices is not None:
                for idx in range(field.count()):
                    text = field.itemText(idx)
                    if text not in enabled_choices:
                        item = field.model().item(idx)
                        if item is not None:
                            item.setEnabled(False)
                            item.setForeground(Qt.gray)
                from osdagbridge.desktop.ui.utils.custom_widgets import SmartCursorComboBoxView
                field.setView(SmartCursorComboBoxView())

        elif ftype == TYPE_CHECKBOX:
            label_first = field_def.get("label_first", False)
            label_text  = "" if label_first else field_def.get("label", "")
            field = QCheckBox(label_text)
            field.setObjectName(field_def.get("id", ""))
            field.setChecked(field_def.get("default_checked", False))
            field.setStyleSheet("QCheckBox { font-size: 11px; color: #333; spacing: 6px; }")
            bind_name = field_def.get("bind")
            if bind_name:
                setattr(owner, bind_name, field)
            if ai and field_def.get("id"):
                field.stateChanged.connect(
                    lambda state, k=field_def.get("id"): ai._on_field_edited(k, bool(state))
                )
            on_change = field_def.get("on_change") or ""
            if on_change and hasattr(owner, on_change):
                field.stateChanged.connect(getattr(owner, on_change))
            return field

        elif ftype == TYPE_TEXTBOX:
            field = QLineEdit()
            placeholder = field_def.get("placeholder")
            if placeholder:
                field.setPlaceholderText(str(placeholder))
            if field_def.get("enabled") is False:
                field.setEnabled(False)
            if field_def.get("read_only"):
                field.setReadOnly(True)
                field.setEnabled(False)
                field.setStyleSheet(
                    "QLineEdit { background-color: #f2f2f2; color: #666;"
                    " border: 1px solid #c0c0c0; border-radius: 4px; padding: 4px 6px; }"
                )
            validator_def = field_def.get("validator")
            if validator_def:
                vtype = validator_def.get("type")
                if vtype == "double_range":
                    field.setValidator(QDoubleValidator(
                        validator_def.get("bottom", 0.0),
                        validator_def.get("top", 1e9),
                        validator_def.get("decimals", 2),
                    ))
                elif vtype == "int_range":
                    field.setValidator(QIntValidator(
                        validator_def.get("bottom", 0),
                        validator_def.get("top", 999999),
                    ))

        elif ftype == TYPE_NOTICE:
            notice_container, adjust_lbl, warning_lbl = self._build_notice_container()
            setattr(owner, field_def["bind_adjust"],    adjust_lbl)
            setattr(owner, field_def["bind_warning"],   warning_lbl)
            setattr(owner, field_def["bind_container"], notice_container)
            return notice_container

        elif ftype == TYPE_BUTTON:
            btn = QPushButton(field_def.get("text", ""))
            btn.setObjectName(field_def.get("id", ""))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff;
                    border: 1px solid #b2b2b2;
                    border-radius: 6px;
                    padding: 4px 12px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover   { background-color: #e6e6e6; color: #2b2b2b; }
                QPushButton:pressed { background-color: #d0d0d0; }
            """)
            bind_name = field_def.get("bind")
            if bind_name:
                setattr(owner, bind_name, btn)
            on_click = field_def.get("on_click") or ""
            if on_click:
                btn.clicked.connect(getattr(self.additional_input_instance, on_click))
            return btn
        
        elif ftype == TYPE_BOUND_BTN:
            return self._create_bound_btn_field(field_def, owner, ai)

        elif ftype == TYPE_DIRECT_WIDGET:
            widget_class = field_def.get("widget_class")
            widget = widget_class()
            widget.setObjectName(field_def.get("id"))
            return widget

        elif ftype == TYPE_MODE_LINE:
            return self._create_mode_line_field(field_def, owner, ai)
        
        elif ftype == TYPE_LOAD_COMBINATION:
            from osdagbridge.desktop.ui.dialogs.additional_input._load_combination_widget import LoadCombinationWidget
            return LoadCombinationWidget(
                field_id=field_def.get("id", ""),
                on_click=field_def.get("on_click", ""),
                owner=self.additional_input_instance,
                ai=self.additional_input_instance,
            )
        
        elif ftype == TYPE_CUSTOM_VEHICLE:
            from osdagbridge.desktop.ui.dialogs.additional_input._custom_vehicle_widget import CustomVehicleWidget
            return CustomVehicleWidget(
                field_id=field_def.get("id", ""),
                on_click=field_def.get("on_click", ""),
                owner=self.additional_input_instance,
                ai=self.additional_input_instance,
            )

        else:
            return QWidget()

        # ── Common post-build ──────────────────────────────────────────────
        field.setObjectName(field_def.get("id"))
        if field_width is not None:
            field.setFixedWidth(field_width)
        else:
            field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        if hasattr(owner, "style_input_field"):
            owner.style_input_field(field)
        else:
            from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
            apply_field_style(field)

        tooltip_attr = field_def.get("tooltip")
        if tooltip_attr and hasattr(owner, tooltip_attr):
            field.setToolTip(getattr(owner, tooltip_attr))

        bind_name = field_def.get("bind")
        if bind_name:
            setattr(owner, bind_name, field)

        field_id = field_def.get("id", "")

        # ── Signal wiring ──────────────────────────────────────────────────
        if ftype == TYPE_COMBOBOX:
            if ai and field_id:
                field.currentTextChanged.connect(
                    lambda text, k=field_id: ai._on_field_edited(k, text)
                )
            on_change = field_def.get("on_change") or ""
            if on_change and hasattr(owner, on_change):
                field.currentTextChanged.connect(getattr(owner, on_change))

        elif ftype == TYPE_TEXTBOX:
            if ai and field_id:
                field.textChanged.connect(
                    lambda text, k=field_id: ai._on_field_editing(text, k)
                )
                field.editingFinished.connect(
                    lambda k=field_id, w=field: ai._on_field_edited(k, w)
                )
            on_text_changed = field_def.get("on_text_changed") or ""
            if on_text_changed and hasattr(owner, on_text_changed):
                field.textChanged.connect(getattr(owner, on_text_changed))
            on_editing_finished = field_def.get("on_editing_finished") or ""
            if on_editing_finished and hasattr(owner, on_editing_finished):
                field.editingFinished.connect(getattr(owner, on_editing_finished))

        return field

    # ──────────────────────────────────────────────────────────────────────────
    # Specialised widget builders
    # ──────────────────────────────────────────────────────────────────────────

    def _build_table_with_count(self, field_def: dict, label_width: int = 200) -> QWidget:
        owner    = self.owner
        field_id = field_def.get("id", "")
        count_id = field_def.get("count_id", "")

        container = QWidget()
        container.setObjectName(field_id + "_container")
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

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
        if hasattr(owner, "style_input_field"):
            owner.style_input_field(combo)
        header_row.addWidget(combo, 0, Qt.AlignVCenter)
        header_row.addStretch()
        layout.addLayout(header_row)

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

    def _create_bound_btn_field(self, field_def: dict, owner, ai) -> QPushButton:
        """Create a Set Bounds button that opens BoundsSelectorDialog."""
        from osdagbridge.desktop.ui.utils.bounds_selector import BoundsSelectorDialog

        field_id    = field_def.get("id", "")
        bind_name   = field_def.get("bind")
        with_inc    = field_def.get("with_increment", True)
        lower_limit = field_def.get("lower_limit")
        upper_limit = field_def.get("upper_limit")
        title       = field_def.get("text", "Set Bounds")
        on_accepted = field_def.get("on_accepted") or ""

        btn = QPushButton(title)
        btn.setObjectName(field_id)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        btn.setFixedHeight(28)
        btn.setFixedWidth(200)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #b2b2b2;
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover   { background-color: #e6e6e6; color: #2b2b2b; }
            QPushButton:pressed { background-color: #d0d0d0; }
        """)

        if bind_name:
            setattr(owner, bind_name, btn)

        def _open_bounds(
            _checked,
            _ai=ai,
            _owner=owner,
            _field_id=field_id,
            _with_inc=with_inc,
            _lower_limit=lower_limit,
            _upper_limit=upper_limit,
            _title=title,
            _on_accepted=on_accepted,
        ):
            # Read current bounds from working_input_dict
            current = {}
            if _ai and hasattr(_ai, "working_input_dict"):
                stored = _ai.working_input_dict.get(_field_id)
                if isinstance(stored, dict):
                    current = stored

            dlg = BoundsSelectorDialog(
                title=_title,
                bounds=current or {
                    "lower":     _lower_limit,
                    "upper":     _upper_limit,
                    "increment": 1.0,
                },
                with_increment=_with_inc,
                lower_limit=_lower_limit,
                upper_limit=_upper_limit,
            )
            if dlg.exec():
                result = dlg.result_bounds()
                print(f"@P0@: {result}")
                if result:
                    print(f"@P1@: {_ai}")
                    # Update working_input_dict via standard pipeline
                    if _ai:
                        print(f"@P2@: {result}")
                        _ai._on_field_edited(_field_id, result)
                    # Domain callback on owner
                    if _on_accepted and hasattr(_owner, _on_accepted):
                        getattr(_owner, _on_accepted)(result)

        btn.clicked.connect(_open_bounds)
        return btn
    
    def _create_mode_line_field(self, field_def: dict, owner, ai) -> QWidget:
        """Combo (mode) + QLineEdit (value) pair."""
        field_id   = field_def.get("id", "")
        bind_mode  = field_def.get("bind_mode")
        bind_value = field_def.get("bind_value")
        on_change  = field_def.get("on_mode_change") or ""
        choices    = field_def.get("mode_choices", [])

        wrapper = QWidget()
        h = QHBoxLayout(wrapper)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)

        mode_combo = QComboBox()
        mode_combo.addItems(choices)
        mode_combo.setObjectName(field_id + ".mode")
        mode_combo.setFixedWidth(96)
        if hasattr(owner, "style_input_field"):
            owner.style_input_field(mode_combo)
        else:
            from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
            apply_field_style(mode_combo)

        value_input = QLineEdit()
        value_input.setObjectName(field_id + ".value")
        value_input.setEnabled(False)
        value_input.setFixedWidth(96)
        if hasattr(owner, "style_input_field"):
            owner.style_input_field(value_input)
        else:
            from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
            apply_field_style(value_input)

        if bind_mode:
            setattr(owner, bind_mode, mode_combo)
        if bind_value:
            setattr(owner, bind_value, value_input)

        def _on_mode_changed(text, _vi=value_input, _choices=choices):
            if _choices and text == _choices[0]:  # first = auto → hide
                _vi.hide()
                _vi.setEnabled(False)
            else:                                  # anything else → show
                _vi.show()
                _vi.setEnabled(True)

        mode_combo.currentTextChanged.connect(_on_mode_changed)

        # Set initial state
        if choices:
            value_input.hide()  # first choice is always selected initially → hide
        else:
            value_input.show()

        if ai and field_id:
            mode_combo.currentTextChanged.connect(
                lambda text, k=field_id + ".mode": ai._on_field_edited(k, text)
            )
            value_input.editingFinished.connect(
                lambda k=field_id + ".value", w=value_input: ai._on_field_edited(k, w)
            )

        h.addWidget(mode_combo, 1)
        h.addWidget(value_input, 1)
        return wrapper