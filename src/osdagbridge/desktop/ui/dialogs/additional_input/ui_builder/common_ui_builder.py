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

from PySide6.QtWidgets import QStackedWidget
class AdaptiveWidget(QStackedWidget):
    """Switches between different field types based on a controller value."""

    def __init__(self, controller_id: str, mode_widgets: dict, ai, field_id: str):
        super().__init__()
        self._controller_id = controller_id
        self._mode_widgets  = mode_widgets
        self._ai            = ai
        self._field_id      = field_id
        for widget in mode_widgets.values():
            self.addWidget(widget)

    def switch_mode(self, mode: str) -> None:
        keys = list(self._mode_widgets.keys())
        idx  = keys.index(mode) if mode in keys else 0
        self.setCurrentIndex(idx)
        if not self._ai or not hasattr(self._ai, "working_input_dict"):
            return
        value  = self._ai.working_input_dict.get(self._field_id)
        active = self.currentWidget()
        if isinstance(active, QLineEdit):
            active.blockSignals(True)
            active.setText("" if isinstance(value, dict) or value is None else str(value))
            active.blockSignals(False)

    def setText(self, value: str) -> None:
        if not self._ai or not hasattr(self._ai, "working_input_dict"):
            return
        mode = str(self._ai.working_input_dict.get(self._controller_id) or "")
        self.switch_mode(mode)

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

        if layout_type == "tabs":
            self._build_tabs_layout(main_layout)
        elif layout_type == "columns":
            self._build_columns_layout(main_layout, layout_def)
        elif layout_type == "rows" and "sections" in self._schema:
            for section in self._schema["sections"]:
                self._build_section(section, main_layout)
        elif "sections" in self._schema:
            for section in self._schema["sections"]:
                self._build_section(section, main_layout)
        elif "cards" in self._schema:
            for card_schema in self._schema["cards"]:
                card, card_layout = self._create_section_card(card_schema.get("title", ""))
                for section in card_schema.get("sections", []):
                    self._build_grid(section, card_layout)
                main_layout.addWidget(card)
        else:
            card, card_layout = self._create_section_card(self._card_title)
            self._build_grid(self._schema, card_layout)
            main_layout.addWidget(card)

        if self._with_scroll:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setStyleSheet(ADDITIONAL_INPUTS_SCROLL_STYLE)
            if not self._schema.get("scroll", True):
                scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setWidget(self.main_widget)
            outer.addWidget(scroll)
        else:
            outer.addWidget(self.main_widget)

    # ──────────────────────────────────────────────────────────────────────────
    # Layout strategies
    # ──────────────────────────────────────────────────────────────────────────

    # ════════════════════════════════════════════════════════════════════════════
    # Patch for common_ui_builder.py
    #
    # Two methods to add/replace inside UIBuilder:
    #   1. _group_sections_into_rows  — new method, place just above _build_columns_layout
    #   2. _build_columns_layout      — replace existing method
    # ════════════════════════════════════════════════════════════════════════════

    def _group_sections_into_rows(self, sections: list, n_cols: int) -> list:
        """
        Group a flat sections list into visual grid rows.
        Only used when the schema opts in via col_span on any section.
 
        Rules:
          - col_span > 1  → own full-width row.
          - col 0 with row_span > 1 → paired with next N col-1 sections
            across multiple grid rows (col-0 widget spans them all).
          - col 0 followed immediately by col 1 → paired into the same row.
          - col 0 with no col-1 partner         → own row.
 
        Returns list of rows, each row is list of (section, grid_row, row_span).
        For simple case returns list of lists of sections (backward compat).
        """
        rows         = []
        pending_col0 = None
        pending_row_span = 1
        i            = 0
 
        while i < len(sections):
            sec      = sections[i]
            col      = int(sec.get("column", 0))
            col_span = int(sec.get("col_span", 1))
            row_span = int(sec.get("row_span", 1))
 
            if col_span > 1:
                if pending_col0 is not None:
                    rows.append([pending_col0])
                    pending_col0 = None
                rows.append([sec])
 
            elif col == 0:
                if pending_col0 is not None:
                    rows.append([pending_col0])
                pending_col0     = sec
                pending_row_span = row_span
 
            elif col == 1:
                if pending_col0 is not None:
                    rows.append([pending_col0, sec])
                    pending_col0 = None
                    pending_row_span = 1
                else:
                    rows.append([sec])
 
            else:
                if pending_col0 is not None:
                    rows.append([pending_col0])
                    pending_col0 = None
                rows.append([sec])
 
            i += 1
 
        if pending_col0 is not None:
            rows.append([pending_col0])
 
        return rows
 
    def _build_columns_layout(self, parent_layout, layout_def):
        """Place sections into columns.
 
        Two modes selected automatically:
 
        INDEPENDENT COLUMNS (default — preserves all existing tab behaviour)
            Each column gets its own QVBoxLayout.  Sections are appended to
            their column's layout independently, so multiple col-0 sections
            stack freely while a single col-1 Description spans the full
            column height.  This is exactly the original behaviour.
 
        GRID MODE (opt-in — used when any section has "col_span" > 1)
            Sections are grouped into visual rows by _group_sections_into_rows
            and placed with QGridLayout.addWidget(w, row, col, 1, col_span).
            This allows a section to span both columns (e.g. CAD preview) while
            the rows below remain two-column.
        """
        num_cols   = layout_def.get("columns", 2)
        col_widths = layout_def.get("column_widths", [1] * num_cols)
        sections   = self._schema.get("sections", [])
 
        # Decide mode: grid if any section requests col_span > 1
        use_grid = any(int(s.get("col_span", 1)) > 1 for s in sections)
 
        if use_grid:
            self._build_columns_layout_grid(parent_layout, sections, num_cols, col_widths)
        else:
            self._build_columns_layout_independent(parent_layout, sections, num_cols, col_widths)
 
    def _build_columns_layout_independent(self, parent_layout, sections, num_cols, col_widths):
        """Original independent-column behaviour — unchanged for all existing tabs."""
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
 
        for section in sections:
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
 
    def _build_columns_layout_grid(self, parent_layout, sections, num_cols, col_widths):
        """Grid mode — supports col_span for full-width rows (e.g. Girder Details)."""
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(12)
        grid.setContentsMargins(0, 0, 0, 0)
 
        for col_idx in range(num_cols):
            stretch = col_widths[col_idx] if col_idx < len(col_widths) else 1
            grid.setColumnStretch(col_idx, stretch)
 
        visual_rows = self._group_sections_into_rows(sections, num_cols)
        for grid_row in range(len(visual_rows)):
            grid.setRowStretch(grid_row, 0)
 
        for grid_row, row_group in enumerate(visual_rows):
            for section in row_group:
                col      = int(section.get("column", 0))
                col_span = int(section.get("col_span", 1))
                stype    = section.get("type")
                stretch  = 1 if section.get("stretch") else 0
 
                if stype == TYPE_DESCRIPTION:
                    wrapper = QWidget()
                    wrapper.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                    wrapper_layout = QVBoxLayout(wrapper)
                    wrapper_layout.setContentsMargins(0, 0, 0, 0)
                    self._build_description_box(section, wrapper_layout, stretch=stretch)
                    row_span = int(section.get("row_span", 1))
                    grid.addWidget(wrapper, grid_row, col, row_span, col_span)
                else:
                    section_widget = QWidget()
                    section_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                    section_id = section.get("id", "")
                    if section_id:
                        section_widget.setObjectName(section_id)
                    section_layout = QVBoxLayout(section_widget)
                    section_layout.setContentsMargins(0, 0, 0, 0)
                    section_layout.setSpacing(12)
                    self._build_section(section, section_layout)
                    row_span = int(section.get("row_span", 1))
                    grid.addWidget(section_widget, grid_row, col, row_span, col_span, Qt.AlignTop)
 
        parent_layout.addLayout(grid)

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

        if section.get("checkbox_groups"):
            # ── Checkbox groups (side-by-side QGroupBox) ──────────────────
            title = section.get("title")
            if title:
                lbl = QLabel(title)
                lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #000;")
                parent_layout.addWidget(lbl)

            groups_layout = QHBoxLayout()
            groups_layout.setSpacing(20)

            for group in section["checkbox_groups"]:
                box = QGroupBox(group.get("title", ""))
                box.setStyleSheet("""
                    QGroupBox {
                        border: 1px solid #000; border-radius: 8px;
                        margin-top: 12px; padding: 8px; background-color: #fff;
                    }
                    QGroupBox::title {
                        subcontrol-origin: margin; subcontrol-position: top left;
                        left: 12px; padding: 0 6px; background-color: #fff;
                        font-weight: 600; font-size: 11px; color: #000;
                    }
                """)
                vbox = QVBoxLayout(box)
                vbox.setContentsMargins(16, 20, 16, 16)
                vbox.setSpacing(8)

                checkboxes = []
                default_checked = group.get("default_checked", False)
                for item in group.get("items", []):
                    label = item["label"] if isinstance(item, dict) else item
                    cb_id = item.get("id") if isinstance(item, dict) else None
                    cb = QCheckBox(label)
                    cb.setChecked(default_checked)
                    if cb_id:
                        cb.setObjectName(cb_id)
                    cb.setStyleSheet("""
                        QCheckBox { font-size: 11px; color: #333; spacing: 6px; }
                        QCheckBox:disabled { font-size: 11px; color: #aaaaaa; spacing: 6px; }
                        QCheckBox::indicator { width: 14px; height: 14px; }
                        QCheckBox::indicator:disabled {
                            border: 1px solid #c8c8c8;
                            background-color: #ebebeb;
                        }
                    """)
                    vbox.addWidget(cb)
                    checkboxes.append(cb)
                vbox.addStretch()

                bind_name = group.get("bind")
                if bind_name:
                    setattr(self.owner, bind_name, checkboxes)
                groups_layout.addWidget(box)

            parent_layout.addLayout(groups_layout)
            return

        # ── Normal card with grid ──────────────────────────────────────────
        card, card_layout = self._create_section_card(section.get("title", ""))
        self._build_grid(section, card_layout)
        section_id = section.get("id", "")
        if section_id:
            # Wrap card so the section can be found/hidden by section_id without
            # overwriting "sectionCard" on the QFrame (which would break its CSS border).
            wrapper = QWidget()
            wrapper.setObjectName(section_id)
            wrapper.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            wl = QVBoxLayout(wrapper)
            wl.setContentsMargins(0, 0, 0, 0)
            wl.setSpacing(0)
            wl.addWidget(card)
            parent_layout.addWidget(wrapper)
        else:
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
                    field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                    grid.addWidget(field, row_idx, col, 1, 2)
                    col += 2
                elif ftype == TYPE_LOAD_COMBINATION:
                    field = self._create_field(field_def)
                    field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                    grid.addWidget(field, row_idx, col, 1, 2)
                    col += 2
                elif ftype == TYPE_CUSTOM_VEHICLE:
                    from osdagbridge.desktop.ui.dialogs.additional_input.ui_builder._custom_vehicle_widget import CustomVehicleWidget
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
                        label.setObjectName((field_def.get("id") or "") + "_label")
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
            field.setObjectName(field_def.get("id"))
            field.setChecked(field_def.get("default_checked", False))
            field.setStyleSheet("""
                QCheckBox { font-size: 11px; color: #333; spacing: 6px; }
                QCheckBox:disabled { font-size: 11px; color: #aaaaaa; spacing: 6px; }
                QCheckBox::indicator { width: 14px; height: 14px; }
                QCheckBox::indicator:disabled {
                    border: 1px solid #c8c8c8;
                    background-color: #ebebeb;
                }
            """)
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
            notice_id = field_def.get("id", "")
            if notice_id:
                notice_container.setObjectName(notice_id)
                adjust_lbl.setObjectName(notice_id + ".adjust")
                warning_lbl.setObjectName(notice_id + ".warning")
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
                QPushButton:hover    { background-color: #e6e6e6; color: #2b2b2b; }
                QPushButton:pressed  { background-color: #d0d0d0; }
                QPushButton:disabled {
                    background-color: #f0f0f0;
                    border: 1px solid #d0d0d0;
                    color: #a8a8a8;
                }
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

        elif ftype == TYPE_ALL_CUSTOM:
            return self._create_all_custom_field(field_def, owner, ai)
        
        elif ftype == TYPE_ADAPTIVE:
            ctrl_id     = field_def.get("controller", "")
            field_id    = field_def.get("id", "")
            modes       = field_def.get("modes", {})

            mode_widgets = {}
            for mode_name, mode_def in modes.items():
                # merge field_id into mode_def for proper binding
                merged = {**mode_def, "id": field_id}
                mode_widgets[mode_name] = self._create_field(merged, field_width=field_width)

            widget = AdaptiveWidget(ctrl_id, mode_widgets, ai, field_id)
            widget.setObjectName(field_id)

            return widget

        elif ftype == TYPE_DIRECT_WIDGET:
            cls = field_def.get("widget_class")
            if cls is None:
                return QWidget()
 
            widget = cls(parent=owner)
            field_id = str(field_def.get("id", ""))
            if field_id:
                widget.setObjectName(field_id)
 
            # Wire any Signal connections declared in the schema as string method names.
            for signal_name, method_key in [
                ("row_selected",  "on_row_select"),
                ("data_changed",  "on_data_changed"),
            ]:
                method_str = field_def.get(method_key, "")
                if not method_str:
                    continue
                signal = getattr(widget, signal_name, None)
                if signal is None:
                    continue
                # Resolve handler on owner then ai
                handler = (
                    getattr(owner, method_str, None)
                    or (getattr(ai, method_str, None) if ai else None)
                )
                if callable(handler):
                    signal.connect(handler)
 
            return widget

        elif ftype == TYPE_MODE_LINE:
            return self._create_mode_line_field(field_def, owner, ai)

        elif ftype == TYPE_MODE_VALUE:
            return self._create_mode_value_field(field_def, owner, ai)

        elif ftype == TYPE_SEGMENT_TABLE:
            return self._create_segment_table_field(field_def, owner, ai)

        elif ftype == TYPE_LOAD_COMBINATION:
            from osdagbridge.desktop.ui.dialogs.additional_input.ui_builder._load_combination_widget import LoadCombinationWidget
            return LoadCombinationWidget(
                field_id=field_def.get("id", ""),
                on_click=field_def.get("on_click", ""),
                owner=self.additional_input_instance,
                ai=self.additional_input_instance,
            )
        
        elif ftype == TYPE_CUSTOM_VEHICLE:
            from osdagbridge.desktop.ui.dialogs.additional_input.ui_builder._custom_vehicle_widget import CustomVehicleWidget
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
        if ftype in (TYPE_COMBOBOX):
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

        # ── on_change_compute wiring ───────────────────────────────────────
        on_change_compute = field_def.get("on_change_compute")
        if on_change_compute and ai:
            func_name = on_change_compute.get("function", "")
            if func_name and hasattr(ai, func_name):
                def _trigger_compute(_val, _ai=ai, _fn=func_name, _root=self):
                    result = getattr(_ai, _fn)(_ai.working_input_dict)
                    if not isinstance(result, dict):
                        return
                    for widget_id, value in result.items():
                        w = _root.findChild(QLineEdit, widget_id)
                        if w:
                            w.setText(str(value) if value is not None else "")
                if ftype == TYPE_COMBOBOX:
                    field.currentTextChanged.connect(_trigger_compute)
                elif ftype == TYPE_TEXTBOX:
                    field.textChanged.connect(_trigger_compute)

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
            QPushButton:disabled {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                color: #a8a8a8;
            }
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
                if result:
                    # Update working_input_dict via standard pipeline
                    if _ai:
                        _ai._on_field_edited(_field_id, result)
                    # Domain callback on owner
                    if _on_accepted and hasattr(_owner, _on_accepted):
                        getattr(_owner, _on_accepted)(_field_id, result)

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
        wrapper.setFixedWidth(200)
        wrapper.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        h = QHBoxLayout(wrapper)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)

        mode_combo = QComboBox()
        mode_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        mode_combo.addItems(choices)
        mode_combo.setObjectName(field_id + ".mode")
        if hasattr(owner, "style_input_field"):
            owner.style_input_field(mode_combo)
        else:
            from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
            apply_field_style(mode_combo)

        value_input = QLineEdit()
        value_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        value_input.setObjectName(field_id + ".value")
        value_input.setEnabled(False)
        if hasattr(owner, "style_input_field"):
            owner.style_input_field(value_input)
        else:
            from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
            apply_field_style(value_input)

        if bind_mode:
            setattr(owner, bind_mode, mode_combo)
        if bind_value:
            setattr(owner, bind_value, value_input)

        def _on_mode_changed(text, _vi=value_input, _choices=choices, _h=h):
            if _choices and text == _choices[0]:
                _vi.hide()
                _vi.setEnabled(False)
                _h.setStretch(0, 1)
                _h.setStretch(1, 0)
            else:
                _vi.show()
                _vi.setEnabled(True)
                _h.setStretch(0, 1)
                _h.setStretch(1, 1)

        mode_combo.currentTextChanged.connect(_on_mode_changed)

        if on_change and hasattr(owner, on_change):
            mode_combo.currentTextChanged.connect(getattr(owner, on_change))

        if ai and field_id:
            mode_combo.currentTextChanged.connect(
                lambda text, k=field_id + ".mode": ai._on_field_edited(k, text)
            )
            value_input.editingFinished.connect(
                lambda k=field_id + ".value", w=value_input: ai._on_field_edited(k, w)
            )

        # ── on_change_compute wiring ───────────────────────────────────────
        on_change_compute = field_def.get("on_change_compute")
        if on_change_compute and ai:
            func_name = on_change_compute.get("function", "")
            if func_name and hasattr(ai, func_name):
                def _trigger_compute(_val, _ai=ai, _fn=func_name, _root=self, _vi=value_input, _fid=field_id):
                    # Sync current value_input text into working_input_dict before computing
                    if _vi.isVisible() and _vi.isEnabled():
                        _ai._on_field_editing(_vi.text(), _fid + ".value")
                    result = getattr(_ai, _fn)(_ai.working_input_dict)
                    if not isinstance(result, dict):
                        return
                    for widget_id, value in result.items():
                        w = _root.findChild(QLineEdit, widget_id)
                        if w:
                            w.setText(str(value) if value is not None else "")

                mode_combo.currentTextChanged.connect(_trigger_compute)
                value_input.editingFinished.connect(lambda: _trigger_compute(None))

        h.addWidget(mode_combo, 1)
        h.addWidget(value_input, 1)

        # Set initial state
        if choices:
            value_input.hide()
            h.setStretch(0, 1)
            h.setStretch(1, 0)
        else:
            value_input.show()
            h.setStretch(0, 1)
            h.setStretch(1, 1)

        return wrapper

    # ──────────────────────────────────────────────────────────────────────────
    # TYPE_MODE_VALUE — mode combo + value combo (Stiffener thickness pattern)
    # ──────────────────────────────────────────────────────────────────────────

    def _create_mode_value_field(self, field_def: dict, owner, ai) -> QWidget:
        """Combo (mode) + Combo (value) pair.

        Mirrors _create_mode_line_field but uses a QComboBox on the value side
        instead of a QLineEdit. First mode_choice = "All" → hides value combo;
        other choices show it.

        Schema fields:
            id             : str           — composite; widgets get '<id>.mode' and '<id>.value'
            mode_choices   : list[str]
            value_choices  : list[str]     — pre-populated; tab may call addItems later
            bind_mode      : str optional
            bind_value     : str optional
            on_mode_change : str optional  — owner method name
        """
        field_id      = field_def.get("id", "")
        bind_mode     = field_def.get("bind_mode")
        bind_value    = field_def.get("bind_value")
        on_change     = field_def.get("on_mode_change") or ""
        mode_choices  = field_def.get("mode_choices", [])
        value_choices = [str(v) for v in (field_def.get("value_choices") or [])]

        wrapper = QWidget()
        wrapper.setFixedWidth(200)
        wrapper.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        h = QHBoxLayout(wrapper)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)

        mode_combo = QComboBox()
        mode_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        mode_combo.addItems(mode_choices)
        mode_combo.setObjectName(field_id + ".mode")
        if hasattr(owner, "style_input_field"):
            owner.style_input_field(mode_combo)
        else:
            from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
            apply_field_style(mode_combo)

        value_combo = QComboBox()
        value_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        value_combo.addItems(value_choices)
        value_combo.setObjectName(field_id + ".value")
        value_combo.setEnabled(False)
        if hasattr(owner, "style_input_field"):
            owner.style_input_field(value_combo)
        else:
            from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
            apply_field_style(value_combo)

        if bind_mode:
            setattr(owner, bind_mode, mode_combo)
        if bind_value:
            setattr(owner, bind_value, value_combo)

        def _on_mode_changed(text, _vc=value_combo, _choices=mode_choices, _h=h):
            if _choices and text == _choices[0]:
                _vc.hide()
                _vc.setEnabled(False)
                _h.setStretch(0, 1)
                _h.setStretch(1, 0)
            else:
                _vc.show()
                _vc.setEnabled(True)
                _h.setStretch(0, 1)
                _h.setStretch(1, 1)

        mode_combo.currentTextChanged.connect(_on_mode_changed)

        if on_change and hasattr(owner, on_change):
            mode_combo.currentTextChanged.connect(getattr(owner, on_change))

        if ai and field_id:
            mode_combo.currentTextChanged.connect(
                lambda text, k=field_id + ".mode": ai._on_field_edited(k, text)
            )
            value_combo.currentTextChanged.connect(
                lambda text, k=field_id + ".value": ai._on_field_edited(k, text)
            )

        # ── on_change_compute wiring ───────────────────────────────────────
        on_change_compute = field_def.get("on_change_compute")
        if on_change_compute and ai:
            func_name = on_change_compute.get("function", "")
            if func_name and hasattr(ai, func_name):
                def _trigger_compute(_val, _ai=ai, _fn=func_name, _root=self):
                    result = getattr(_ai, _fn)(_ai.working_input_dict)
                    if not isinstance(result, dict):
                        return
                    for widget_id, value in result.items():
                        w = _root.findChild(QLineEdit, widget_id)
                        if w:
                            w.setText(str(value) if value is not None else "")
                mode_combo.currentTextChanged.connect(_trigger_compute)
                value_combo.currentTextChanged.connect(_trigger_compute)

        h.addWidget(mode_combo, 1)
        h.addWidget(value_combo, 1)

        # Initial state — value combo hidden when first mode choice selected
        if mode_choices:
            value_combo.hide()
            h.setStretch(0, 1)
            h.setStretch(1, 0)
        else:
            value_combo.show()
            h.setStretch(0, 1)
            h.setStretch(1, 1)

        return wrapper

    # ──────────────────────────────────────────────────────────────────────────
    # TYPE_SEGMENT_TABLE — master-detail segment table with +/− row actions
    # ──────────────────────────────────────────────────────────────────────────

    def _create_segment_table_field(self, field_def: dict, owner, ai) -> QWidget:
        """Instantiate SegmentTableWidget and bind callbacks to owner/ai.

        Schema fields:
            id              : str — objectName
            bind            : str — owner attribute name
            on_row_select   : str — owner/ai method(row_index, member_id)
            on_data_changed : str — owner/ai method(segments_list)
            min_rows        : int — minimum rows (disable remove below this)
        """
        from osdagbridge.desktop.ui.dialogs.additional_input.ui_builder._segment_table_widget import (
            SegmentTableWidget,
        )

        field_id        = field_def.get("id", "")
        bind            = field_def.get("bind")
        on_row_select   = field_def.get("on_row_select") or ""
        on_data_changed = field_def.get("on_data_changed") or ""
        min_rows        = int(field_def.get("min_rows", 1))

        def _resolve(name):
            if not name:
                return None
            target = (
                getattr(owner, name, None)
                or (getattr(ai, name, None) if ai else None)
            )
            return target if callable(target) else None

        widget = SegmentTableWidget(
            on_row_select=_resolve(on_row_select),
            on_data_changed=_resolve(on_data_changed),
            min_rows=min_rows,
            parent=owner,
        )
        widget.setObjectName(field_id)

        if bind:
            setattr(owner, bind, widget)

        return widget

    def _build_tabs_layout(self, parent_layout):
        from PySide6.QtWidgets import QTabWidget
        tab_widget = QTabWidget()
        tab_widget.setDocumentMode(True)
        tab_widget.setUsesScrollButtons(True)
        tab_widget.tabBar().setExpanding(False)
        tab_widget.setMovable(False)
        tab_widget.setStyleSheet(
            "QTabBar::scroller { width: 24px; }"
            "QTabBar::right-arrow { image:none; border:none; background:transparent; }"
            "QTabBar::left-arrow  { image:none; border:none; background:transparent; }"
            "QTabBar::left-arrow:!enabled { width: 0px; }"
            "QTabBar::tab:disabled { color: #a0a0a0; }"
        )

        tabs_def = self._schema.get("tabs", [])

        for tab_def in tabs_def:
            title        = tab_def.get("title", "")
            schema       = tab_def.get("schema")
            widget_class = tab_def.get("widget_class")
            is_disbled   = tab_def.get("disable", False)

            if widget_class:
                widget = widget_class(self.owner)
            elif schema:
                widget = UIBuilder(
                    owner=self.owner,
                    schema=schema,
                    card_title="",
                    with_scroll=True,
                    main_widget_object_name=schema.get("id", title),
                    additional_input_instance=self.additional_input_instance,
                )
            else:
                continue

            tab_widget.addTab(widget, title)
            if is_disbled:
                tab_widget.setTabEnabled(tab_widget.count() - 1, False)

        def _refresh_tab(idx):
            if idx >= len(tabs_def):
                return
            ai = self.additional_input_instance
            if not ai or not hasattr(ai, "working_input_dict"):
                return
            current_widget = tab_widget.currentWidget()
            if not current_widget:
                return

            # existing refresh logic
            refresh_list = tabs_def[idx].get("refresh", [])
            for entry in refresh_list:
                widget_id = entry.get("widget_id")
                path      = entry.get("path", [])
                val = ai.working_input_dict
                for key in path:
                    if isinstance(val, dict):
                        val = val.get(key)
                    else:
                        val = None
                        break
                if val is None:
                    continue
                # Persist the synced value so it survives save and reaches
                # Generate Results (input_dict), not just the displayed widget.
                ai.working_input_dict[widget_id] = val
                w = current_widget.findChild(QLineEdit, widget_id)
                if w:
                    w.setText(str(val))

        # ── Connect tab change signal ──────────────────────────────────────────
        # Triggered whenever user switches tabs
        tab_widget.currentChanged.connect(_refresh_tab)

        # ── Expose refresh method for dialog open ─────────────────────────────
        # Call tab_widget.refresh_active_tab() after dialog is shown to
        # ensure the initially visible tab also gets refreshed.
        # Usage in AdditionalInputs.showEvent or wherever dialog is opened:
        #     self.findChild(QTabWidget).refresh_active_tab()  # or keep a reference
        def _refresh_active_tab():
            """Manually trigger refresh for currently active tab — call on dialog open."""
            _refresh_tab(tab_widget.currentIndex())

        tab_widget.refresh_active_tab = _refresh_active_tab

        parent_layout.addWidget(tab_widget)

    def _create_all_custom_field(self, field_def: dict, owner, ai) -> QComboBox:
        """Combo with ['All', 'Custom'].
        Selecting 'Custom' opens CustomMultiSelectDialog internally.
        Selected values are stored in ai.working_input_dict under field_id + '.selected'.

        Schema:
            id   : str
            bind : str optional
        """
        from osdagbridge.core.utils.common import SAIL_APPROVED_THICKNESS_VALUES

        field_id = field_def.get("id", "")
        bind     = field_def.get("bind")

        combo = QComboBox()
        combo.addItems(["All", "Custom"])
        combo.setObjectName(field_id)

        if hasattr(owner, "style_input_field"):
            owner.style_input_field(combo)
        else:
            from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
            apply_field_style(combo)

        if bind:
            setattr(owner, bind, combo)

        if ai and field_id:
            combo.currentTextChanged.connect(
                lambda text, k=field_id: ai._on_field_edited(k, text)
            )

        def _on_changed(text, _combo=combo, _ai=ai, _fid=field_id):
            if text != "Custom":
                return
            
            from osdagbridge.desktop.ui.dialogs.additional_input.dialogs.multi_select_dialog import CustomMultiSelectDialog

            current_raw = (_ai.working_input_dict.get(_fid + ".selected", [])
                            if _ai and hasattr(_ai, "working_input_dict") else [])
        
            if isinstance(current_raw, str):
                current_raw = [v.strip() for v in current_raw.split(",") if v.strip()]

            allowed = [str(v) for v in SAIL_APPROVED_THICKNESS_VALUES]
            dlg = CustomMultiSelectDialog(
                title="Select Thickness Values",
                selected_values=current_raw,
                allowed_values=allowed,
                parent=_combo,
            )
            if dlg.exec():
                chosen = dlg.selected_values()
                if _ai and hasattr(_ai, "working_input_dict"):
                    _ai.working_input_dict[_fid + ".selected"] = chosen
                
                # Domain callback — passes field_id and chosen to owner
                on_selected = field_def.get("on_selected") or ""
                if on_selected and hasattr(owner, on_selected):
                    getattr(owner, on_selected)(_fid, chosen)

            else:
                # user cancelled — revert combo to "All"
                _combo.blockSignals(True)
                _combo.setCurrentText("All")
                _combo.blockSignals(False)

        combo.currentTextChanged.connect(_on_changed)
        return combo
    
    @staticmethod
    def wire_end_connectors(connectors: list, ai: QWidget) -> None:
        """Wire end connectors after all UIBuilder instances are built.
        
        connectors: list of (origin_key, target_key, handler_name) tuples
        ai: the AdditionalInputs instance that owns the handler methods & all the widgets
        """
        for origin_key, target_key, handler_name in connectors:
            handler = getattr(ai, handler_name)

            origin_widget = ai.findChild(QWidget, origin_key)
            target_widget = ai.findChild(QWidget, target_key)

            from osdagbridge.desktop.ui.dialogs.additional_input.ui_builder._segment_table_widget import SegmentTableWidget

            # Connect origin signal → handler(origin_key, target_widget)
            if isinstance(origin_widget, QLineEdit):
                origin_widget.editingFinished.connect(
                    lambda k=origin_key, obj=target_widget, h=handler: h(k, obj)
                )
            
            elif isinstance(origin_widget, AdaptiveWidget):
                # Connect whichever child widget is currently active,
                # and also connect all child widgets so mode switches are covered.
                for mode_widget in origin_widget._mode_widgets.values():
                    if isinstance(mode_widget, QLineEdit):
                        mode_widget.editingFinished.connect(
                            lambda k=origin_key, obj=target_widget, h=handler: h(k, obj)
                        )
                    elif isinstance(mode_widget, QComboBox):
                        mode_widget.currentTextChanged.connect(
                            lambda _val, k=origin_key, obj=target_widget, h=handler: h(k, obj)
                        )

            elif isinstance(origin_widget, QComboBox):
                origin_widget.currentTextChanged.connect(
                    lambda _val, k=origin_key, obj=target_widget, h=handler: h(k, obj)
                )
            
            elif isinstance(origin_widget, QCheckBox):
                origin_widget.stateChanged.connect(
                    lambda _state, k=origin_key, obj=target_widget, h=handler: h(k, obj)
                )

            elif isinstance(origin_widget, SegmentTableWidget):
                origin_widget.data_changed.connect(
                    lambda data, k=origin_key, obj=target_widget, h=handler: h(k, obj)
                )

            # Trigger immediately to populate target with current working_input_dict value
            handler(origin_key, target_widget)
