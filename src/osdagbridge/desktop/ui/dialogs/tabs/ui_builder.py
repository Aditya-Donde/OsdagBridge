"""Central schema-driven UI builder for Additional Inputs tabs.

The two entry points:

``build_tab(widget)``
    Builds the ENTIRE tab — scroll area, card frames, section boxes, field
    rows — from the schema.  Each tab class only needs to call this once and
    then add any tab-specific widgets (CAD drawings, etc.) on top.

``build(parent_layout)``
    Lower-level entry for embedding a sub-schema into an already existing
    layout (useful when a tab has both auto-generated inputs and custom
    widgets).

Layout is inferred from schema keys:

* ``"description"`` present  →  two-panel layout (inputs left, desc right)
* ``"cards"`` present         →  stacked-cards layout on the left panel
* ``"sections"`` only         →  one framed card per section, no right panel
* ``"rows"`` only             →  flat grid, no cards, no right panel
"""

import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLayout,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style

_log = logging.getLogger(__name__)
_MISSING = object()  # sentinel for bind-overwrite detection

# ---------------------------------------------------------------------------
# Dispatch table — map schema "type" → builder method name.
# Add a new entry here + a build_*() method to support a new field type.
# ---------------------------------------------------------------------------
_TYPE_TO_METHOD: dict[str, str] = {
    "line":          "build_line_edit",
    "number":        "build_line_edit",
    "computed":      "build_computed",
    "combo":         "build_combo",
    "combo_dynamic": "build_combo",
    "checkbox":      "build_checkbox",
    "label":         "build_label",
    "button":        "build_button",
    "mode_line":     "build_mode_line",
}

# Section types that have their own dedicated builder (return a styled
# QFrame on their own — no extra card wrapping).
_SPECIAL_SECTION_TYPES = {
    "checkbox_list",
    "custom_vehicle_table",
    "dynamic_checkbox_list",
    "custom_load_combo_table",
    "cad",
    "cad_row",
    "stacked",
    "diagram",
}

# Section types where the section dict IS the field definition
# (e.g. eccentricity / footpath_pressure in LIVE_LOAD_TAB_SCHEMA).
_FIELD_AS_SECTION_TYPES = {"line", "number", "combo", "mode_line"}

_DEFAULT_LABEL_WIDTH = 180
_DEFAULT_FIELD_WIDTH = 180

_HEADING_STYLE = "font-size: 12px; font-weight: 700; color: #2b2b2b; background: transparent; border: none;"
_LABEL_STYLE   = "font-size: 11px; color: #3a3a3a; background: transparent; border: none;"

_CARD_STYLE = """
    QFrame {
        border: 1px solid #b2b2b2;
        border-radius: 8px;
        background-color: #ffffff;
    }
    QFrame QLabel {
        background: transparent;
        border: none;
        border-radius: 0;
        padding: 0;
    }
"""

_SECTION_BOX_STYLE = """
    QFrame {
        border: 1px solid #9c9c9c;
        border-radius: 6px;
        background-color: #ffffff;
    }
    QFrame QLabel {
        background: transparent;
        border: none;
    }
"""

_RIGHT_CARD_STYLE = """
    QFrame {
        border: 1px solid #9c9c9c;
        border-radius: 10px;
        background-color: #d4d4d4;
    }
    QFrame QLabel {
        background: transparent;
        border: none;
    }
"""


class UIBuilder:
    """Renders a complete tab UI from a schema dict.

    Parameters
    ----------
    owner:
        QWidget that receives bound widget attributes.  When a schema field
        declares ``"bind": "my_combo"``, the builder does
        ``setattr(owner, "my_combo", widget)``.
    schema:
        Schema dict (from ``ui_fields_additional_input.py``).
    """

    def __init__(self, owner: QWidget, schema: dict) -> None:
        self.owner  = owner
        self.schema = schema

    # ------------------------------------------------------------------ #
    # Public high-level entry — builds an entire tab
    # ------------------------------------------------------------------ #

    def build_tab(self, tab_widget: QWidget) -> None:
        """Build the full tab UI into *tab_widget*.

        Handles scroll area, card framing, section boxes and field rows.
        After calling this the tab class only needs to add custom widgets
        (e.g. CAD drawings) to ``tab_widget``'s layout.
        """
        tab_widget.setStyleSheet("background-color: #f5f5f5;")

        main_layout = QVBoxLayout(tab_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: #f5f5f5; border: none; }")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: #f5f5f5;")

        page_layout = QVBoxLayout(scroll_content)
        page_layout.setContentsMargins(12, 12, 12, 12)
        page_layout.setSpacing(12)

        schema = self.schema
        has_description = "description" in schema
        has_cards       = "cards" in schema
        has_sections    = "sections" in schema

        if has_description:
            # Two-panel: inputs left (3 parts) + description right (2 parts)
            self._build_two_panel(page_layout)
        elif has_cards:
            # Stacked cards, no right description panel
            self._build_cards_column(page_layout, schema["cards"])
        elif has_sections:
            # One bordered card per section
            self._build_section_cards(page_layout, schema["sections"])
        else:
            # Fallback: flat rows/grid
            self.build(page_layout)

        page_layout.addStretch()

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        self._wire_conditions()

    # ------------------------------------------------------------------ #
    # Public lower-level entry — populates an existing layout
    # ------------------------------------------------------------------ #

    def build(self, parent_layout: QLayout) -> None:
        """Populate *parent_layout* from the schema's top-level structure."""
        schema = self.schema
        label_width = int(schema.get("label_width", _DEFAULT_LABEL_WIDTH))
        field_width = int(schema.get("field_width", _DEFAULT_FIELD_WIDTH))

        if "cards" in schema:
            self._build_cards_column(parent_layout, schema["cards"])
        elif "sections" in schema:
            self._build_sections(parent_layout, schema["sections"], label_width, field_width)
        elif "rows" in schema:
            self._build_rows(parent_layout, schema["rows"], label_width, field_width)
        elif "columns" in schema:
            self._build_columns(parent_layout, schema["columns"], label_width, field_width)

    # ------------------------------------------------------------------ #
    # Component builders — one public method per TYPE
    # ------------------------------------------------------------------ #

    def build_line_edit(self, field_def: dict) -> QLineEdit:
        widget = QLineEdit()

        default = field_def.get("default")
        if default is not None:
            widget.setText(str(default))
            widget.setProperty("default_value", default)

        placeholder = field_def.get("placeholder")
        if placeholder:
            widget.setPlaceholderText(str(placeholder))

        if field_def.get("read_only"):
            widget.setReadOnly(True)

        self._apply_validator(widget, field_def.get("validator"))
        apply_field_style(widget)
        return widget

    def build_computed(self, field_def: dict) -> QLineEdit:
        """Read-only display field for computed/output values."""
        widget = QLineEdit()
        widget.setReadOnly(True)
        default = field_def.get("default")
        if default is not None:
            widget.setText(str(default))
        widget.setStyleSheet("""
            QLineEdit {
                background-color: #f0f0f0;
                border: 1px solid #8a8a8a;
                border-radius: 5px;
                padding: 5px 8px;
                color: #5a5a5a;
                font-size: 11px;
            }
        """)
        return widget

    def build_combo(self, field_def: dict) -> QComboBox:
        widget = QComboBox()

        for choice in field_def.get("choices") or []:
            widget.addItem(str(choice))

        if field_def.get("adjust_to_contents"):
            widget.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        minimum_contents_length = field_def.get("minimum_contents_length")
        if minimum_contents_length is not None:
            try:
                widget.setMinimumContentsLength(int(minimum_contents_length))
            except (TypeError, ValueError):
                pass

        popup_min_width = field_def.get("popup_min_width")
        if popup_min_width is not None:
            try:
                widget.view().setMinimumWidth(int(popup_min_width))
            except (TypeError, ValueError, AttributeError):
                pass

        enabled_choices = field_def.get("enabled_choices")
        if enabled_choices is not None:
            for idx in range(widget.count()):
                text = widget.itemText(idx)
                if text not in enabled_choices:
                    item = widget.model().item(idx)
                    if item is not None:
                        item.setEnabled(False)
                        item.setForeground(Qt.gray)

        default = field_def.get("default")
        if default is not None:
            widget.setCurrentText(str(default))

        apply_field_style(widget)
        return widget

    def build_checkbox(self, field_def: dict) -> QCheckBox:
        widget = QCheckBox(str(field_def.get("label") or ""))
        widget.setChecked(bool(field_def.get("default", False)))
        return widget

    def build_label(self, field_def: dict) -> QLabel:
        widget = QLabel(str(field_def.get("default") or field_def.get("label") or ""))
        widget.setStyleSheet(_LABEL_STYLE)
        return widget

    def build_button(self, field_def: dict) -> QPushButton:
        widget = QPushButton(str(field_def.get("text") or "Button"))
        widget.setFixedHeight(28)
        widget.setCursor(Qt.PointingHandCursor)
        widget.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #b2b2b2;
                border-radius: 6px;
                padding: 4px;
            }
            QPushButton:hover  { background-color: #e6e6e6; color: #2b2b2b; }
            QPushButton:pressed { background-color: #d0d0d0; }
        """)
        return widget

    def build_mode_line(self, field_def: dict) -> QWidget:
        """QComboBox + QLineEdit wrapped in a horizontal QWidget."""
        mode_combo = QComboBox()
        for choice in field_def.get("mode_choices") or []:
            mode_combo.addItem(str(choice))
        default_mode = field_def.get("default_mode")
        if default_mode is not None:
            mode_combo.setCurrentText(str(default_mode))
        apply_field_style(mode_combo)

        value_input = QLineEdit()
        default_value = field_def.get("default_value")
        if default_value is not None:
            value_input.setText(str(default_value))
        if field_def.get("placeholder"):
            value_input.setPlaceholderText(str(field_def["placeholder"]))
        self._apply_validator(value_input, field_def.get("validator"))
        apply_field_style(value_input)

        bind_mode = field_def.get("bind_mode")
        if bind_mode:
            setattr(self.owner, str(bind_mode), mode_combo)
            mode_combo.setObjectName(str(bind_mode))

        bind_value = field_def.get("bind_value")
        if bind_value:
            setattr(self.owner, str(bind_value), value_input)
            value_input.setObjectName(str(bind_value))

        self._connect_signals(mode_combo,  {"on_change": field_def.get("on_mode_change")})
        self._connect_signals(value_input, {
            "on_text_changed":     field_def.get("on_text_changed"),
            "on_editing_finished": field_def.get("on_editing_finished"),
        })

        wrapper = QWidget()
        row = QHBoxLayout(wrapper)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        row.addWidget(mode_combo)
        row.addWidget(value_input)
        return wrapper

    # ------------------------------------------------------------------ #
    # Field dispatcher
    # ------------------------------------------------------------------ #

    def build_field(self, field_def: dict, field_width: int = _DEFAULT_FIELD_WIDTH) -> QWidget:
        """Create, style, bind and wire a single field widget."""
        ftype = str(field_def.get("type") or "line").strip().lower()
        method_name = _TYPE_TO_METHOD.get(ftype)
        if method_name is None:
            _log.warning(
                "UIBuilder[%s]: unknown field type=%r (bind=%r) — rendered as QLineEdit",
                type(self.owner).__name__, ftype, field_def.get("bind"),
            )
            method_name = "build_line_edit"
        builder = getattr(self, method_name)
        widget = builder(field_def)

        if ftype != "mode_line":
            self._bind_widget(widget, field_def)
            self._connect_signals(widget, field_def)

        if ftype not in {"mode_line", "checkbox"}:
            width = field_def.get("width", field_width)
            if width:
                try:
                    widget.setFixedWidth(int(width))
                except (TypeError, ValueError):
                    pass

        enabled = field_def.get("enabled")
        if enabled is not None:
            widget.setEnabled(bool(enabled))

        return widget

    # ------------------------------------------------------------------ #
    # Internal layout helpers
    # ------------------------------------------------------------------ #

    def _build_two_panel(self, page_layout: QLayout) -> None:
        """Left input card (3 parts) + right description card (2 parts)."""
        schema = self.schema
        label_width = int(schema.get("label_width", _DEFAULT_LABEL_WIDTH))
        field_width = int(schema.get("field_width", _DEFAULT_FIELD_WIDTH))

        content_row = QHBoxLayout()
        content_row.setSpacing(16)

        # ── Left card ──────────────────────────────────────────────────
        left_outer = QFrame()
        left_outer.setStyleSheet(
            "QFrame { border: 1px solid #b2b2b2; border-radius: 10px; background-color: #ffffff; }"
        )
        left_outer_layout = QVBoxLayout(left_outer)
        left_outer_layout.setContentsMargins(0, 0, 0, 0)

        left_content = QWidget()
        left_content.setStyleSheet("background-color: #ffffff;")
        left_layout = QVBoxLayout(left_content)
        left_layout.setContentsMargins(14, 14, 14, 14)
        left_layout.setSpacing(12)

        if "cards" in schema:
            self._build_cards_column(left_layout, schema["cards"])
        elif "sections" in schema:
            for section in schema["sections"]:
                self._dispatch_section(left_layout, section, label_width, field_width)

        left_layout.addStretch()
        left_outer_layout.addWidget(left_content)

        # ── Right description card ─────────────────────────────────────
        right_card = QFrame()
        right_card.setStyleSheet(_RIGHT_CARD_STYLE)
        right_card.setMinimumWidth(260)
        right_card.setMinimumHeight(420)
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(10)

        desc = schema.get("description", {})
        desc_title = QLabel(desc.get("title", "Description Box"))
        desc_title.setAlignment(Qt.AlignCenter)
        desc_title.setStyleSheet(
            "font-size: 12px; font-weight: 700; color: #000000; background: transparent; border: none;"
        )
        desc_text = QLabel(desc.get("text", ""))
        desc_text.setWordWrap(True)
        desc_text.setStyleSheet(
            "font-size: 11px; color: #4b4b4b; background: transparent; border: none;"
        )
        right_layout.addWidget(desc_title)
        right_layout.addWidget(desc_text)
        right_layout.addStretch()

        content_row.addWidget(left_outer, 3)
        content_row.addWidget(right_card, 2)
        page_layout.addLayout(content_row)

    def _build_section_cards(self, page_layout: QLayout, sections: list) -> None:
        """One bordered QFrame card per section — used when there is no description panel.

        Special section types (those in ``_SPECIAL_SECTION_TYPES``) skip the outer
        card wrapper because their own builder already returns a styled frame.
        """
        schema = self.schema
        label_width = int(schema.get("label_width", _DEFAULT_LABEL_WIDTH))
        field_width = int(schema.get("field_width", _DEFAULT_FIELD_WIDTH))

        for section in sections:
            stype = str(section.get("type") or "").strip().lower()
            sec_label_width = int(section.get("label_width", label_width))
            sec_field_width = int(section.get("field_width", field_width))

            if stype in _SPECIAL_SECTION_TYPES or stype in _FIELD_AS_SECTION_TYPES:
                # Builder returns its own frame — no card wrap.
                self._dispatch_section(page_layout, section, sec_label_width, sec_field_width)
                continue

            card = QFrame()
            card.setStyleSheet(_CARD_STYLE)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 16, 16, 16)
            card_layout.setSpacing(12)

            self._build_sections(card_layout, [section], sec_label_width, sec_field_width)

            page_layout.addWidget(card)

    def _dispatch_section(
        self,
        parent_layout: QLayout,
        section: dict,
        label_width: int,
        field_width: int,
    ) -> None:
        """Route a section dict to the right builder based on its ``type``."""
        stype = str(section.get("type") or "").strip().lower()

        if stype == "checkbox_list":
            parent_layout.addWidget(self._build_checkbox_list_section(section, label_width))
        elif stype == "custom_vehicle_table":
            parent_layout.addWidget(self._build_custom_vehicle_table_section(section, label_width))
        elif stype == "dynamic_checkbox_list":
            parent_layout.addWidget(self._build_dynamic_checkbox_list_section(section, label_width))
        elif stype == "custom_load_combo_table":
            parent_layout.addWidget(self._build_custom_load_combo_table_section(section))
        elif stype == "cad":
            self._build_cad_section(parent_layout, section)
        elif stype == "cad_row":
            self._build_cad_row_section(parent_layout, section)
        elif stype == "stacked":
            self._build_stacked_section(parent_layout, section, label_width, field_width)
        elif stype == "diagram":
            parent_layout.addWidget(self._build_diagram_section(section))
        elif stype in _FIELD_AS_SECTION_TYPES:
            parent_layout.addWidget(
                self._build_single_field_section(section, label_width, field_width)
            )
        else:
            if stype:
                _log.warning(
                    "UIBuilder[%s]: unknown section type=%r (id=%r) — using section_box fallback",
                    type(self.owner).__name__, stype, section.get("id"),
                )
            parent_layout.addWidget(self._make_section_box(section, label_width, field_width))

    def _build_cards_column(self, parent_layout: QLayout, cards: list) -> None:
        """Stacked card QFrames, each with its own sections."""
        for card_schema in cards:
            card = QFrame()
            card.setStyleSheet(_CARD_STYLE)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 14, 16, 14)
            card_layout.setSpacing(10)

            title = card_schema.get("title")
            if title:
                lbl = QLabel(title)
                lbl.setStyleSheet(_HEADING_STYLE)
                card_layout.addWidget(lbl)

            card_label_width = int(card_schema.get("label_width", _DEFAULT_LABEL_WIDTH))
            card_field_width = int(card_schema.get("field_width", _DEFAULT_FIELD_WIDTH))

            if "sections" in card_schema:
                self._build_sections(card_layout, card_schema["sections"], card_label_width, card_field_width)
            elif "rows" in card_schema:
                self._build_rows(card_layout, card_schema["rows"], card_label_width, card_field_width)

            parent_layout.addWidget(card)

    def _make_section_box(self, section: dict, label_width: int, field_width: int) -> QFrame:
        """Return a bordered QFrame for one section (used inside the two-panel left card)."""
        box = QFrame()
        box.setStyleSheet(_SECTION_BOX_STYLE)
        box_layout = QVBoxLayout(box)
        box_layout.setContentsMargins(12, 12, 12, 12)
        box_layout.setSpacing(14)

        sec_label_width = int(section.get("label_width", label_width))
        sec_field_width = int(section.get("field_width", field_width))
        self._build_sections(box_layout, [section], sec_label_width, sec_field_width)
        return box

    def _make_field_label(self, field_def: dict, label_width: int) -> QLabel:
        """Create a QLabel for a field row and bind it when requested."""
        label = QLabel(field_def.get("label", ""))
        label.setTextFormat(Qt.RichText)
        label.setStyleSheet(_LABEL_STYLE)
        label.setMinimumWidth(label_width)

        label_bind = field_def.get("label_bind")
        if label_bind:
            setattr(self.owner, str(label_bind), label)

        return label

    # ── Field-level layout helpers ──────────────────────────────────────

    def _build_sections(
        self,
        parent_layout: QLayout,
        sections: list,
        label_width: int = _DEFAULT_LABEL_WIDTH,
        field_width: int = _DEFAULT_FIELD_WIDTH,
    ) -> None:
        for section in sections:
            sec_field_width = int(section.get("field_width", field_width))
            sec_label_width = int(section.get("label_width", label_width))

            checkbox_groups = section.get("checkbox_groups")
            if checkbox_groups:
                self._build_checkbox_groups(parent_layout, section, checkbox_groups)
                continue

            title = section.get("title")
            if title:
                heading = QLabel(title)
                heading.setStyleSheet(_HEADING_STYLE)
                parent_layout.addWidget(heading)

            grid = QGridLayout()
            grid.setContentsMargins(0, 8, 0, 0)
            grid.setHorizontalSpacing(12)
            grid.setVerticalSpacing(12)
            grid.setColumnMinimumWidth(0, sec_label_width)

            row_idx = 0
            for field_def in section.get("fields", []):
                row_fields = field_def.get("row_fields")
                if row_fields:
                    row_layout = QHBoxLayout()
                    row_layout.setSpacing(8)
                    row_layout.setContentsMargins(0, 0, 0, 0)
                    for inline_def in row_fields:
                        if inline_def.get("type") == "label":
                            lbl = QLabel(inline_def.get("label", ""))
                            lbl.setStyleSheet(_LABEL_STYLE)
                            row_layout.addWidget(lbl)
                            after = inline_def.get("after_spacing")
                            if after:
                                row_layout.addSpacing(after)
                        else:
                            w = self.build_field(inline_def, inline_def.get("width", sec_field_width))
                            row_layout.addWidget(w)
                    row_layout.addStretch()
                    parent_layout.addLayout(row_layout)
                    continue

                ftype = str(field_def.get("type") or "line").strip().lower()

                if ftype == "checkbox":
                    widget = self.build_field(field_def, sec_field_width)
                    grid.addWidget(widget, row_idx, 0, 1, 2, Qt.AlignLeft)
                    row_idx += 1
                    continue

                lbl = self._make_field_label(field_def, sec_label_width)
                grid.addWidget(lbl, row_idx, 0, Qt.AlignLeft | Qt.AlignVCenter)

                widget = self.build_field(field_def, sec_field_width)
                grid.addWidget(widget, row_idx, 1, Qt.AlignLeft | Qt.AlignVCenter)
                row_idx += 1

            parent_layout.addLayout(grid)

    def _build_rows(
        self,
        parent_layout: QLayout,
        rows: list,
        label_width: int = _DEFAULT_LABEL_WIDTH,
        field_width: int = _DEFAULT_FIELD_WIDTH,
    ) -> None:
        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(int(self.schema.get("row_vertical_spacing", 10)))
        grid.setColumnMinimumWidth(0, label_width)
        grid.setContentsMargins(0, 0, 0, 0)

        max_columns = max((len(row.get("fields", [])) * 2 for row in rows), default=0)
        for col in range(max_columns):
            grid.setColumnStretch(col, 0)
        if max_columns > 0:
            # Let a trailing empty column absorb extra space so fields stay grouped.
            grid.setColumnStretch(max_columns, 1)

        row_idx = 0
        for row in rows:
            col = 0
            for field_def in row.get("fields", []):
                lbl = self._make_field_label(field_def, label_width)
                grid.addWidget(lbl, row_idx, col, Qt.AlignLeft | Qt.AlignVCenter)
                col += 1

                widget = self.build_field(field_def, field_width)
                grid.addWidget(widget, row_idx, col, Qt.AlignLeft | Qt.AlignVCenter)
                col += 1
            row_idx += 1

        parent_layout.addLayout(grid)

    def _build_columns(
        self,
        parent_layout: QLayout,
        columns: list,
        label_width: int = _DEFAULT_LABEL_WIDTH,
        field_width: int = _DEFAULT_FIELD_WIDTH,
    ) -> None:
        row_layout = QHBoxLayout()
        row_layout.setSpacing(16)
        row_layout.setContentsMargins(0, 0, 0, 0)

        for col_def in columns:
            col_widget = QWidget()
            col_vbox = QVBoxLayout(col_widget)
            col_vbox.setContentsMargins(0, 0, 0, 0)
            col_vbox.setSpacing(8)

            col_label_width = int(col_def.get("label_width", label_width))
            col_field_width = int(col_def.get("field_width", field_width))

            if "sections" in col_def:
                self._build_sections(col_vbox, col_def["sections"], col_label_width, col_field_width)
            elif "rows" in col_def:
                self._build_rows(col_vbox, col_def["rows"], col_label_width, col_field_width)

            col_vbox.addStretch()
            row_layout.addWidget(col_widget, int(col_def.get("stretch", 1)))

        parent_layout.addLayout(row_layout)

    def _build_checkbox_groups(
        self,
        parent_layout: QLayout,
        section: dict,
        checkbox_groups: list,
    ) -> None:
        title = section.get("title")
        if title:
            heading = QLabel(title)
            heading.setStyleSheet(_HEADING_STYLE)
            parent_layout.addWidget(heading)

        groups_layout = QHBoxLayout()
        groups_layout.setSpacing(20)

        for group in checkbox_groups:
            box = QGroupBox(group.get("title", ""))
            box.setStyleSheet(
                "QGroupBox { border: 1px solid #b0b0b0; border-radius: 6px; "
                "margin-top: 12px; padding: 8px; background: #ffffff; }"
                "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; "
                "left: 12px; padding: 0 6px; background: #f5f5f5; font-weight: 600; "
                "font-size: 11px; color: #333333; }"
            )
            vbox = QVBoxLayout(box)
            vbox.setContentsMargins(16, 24, 16, 16)
            vbox.setSpacing(12)

            checkboxes = []
            default_checked = group.get("default_checked", False)
            for text in group.get("items", []):
                cb = QCheckBox(text)
                cb.setChecked(default_checked)
                cb.setStyleSheet(
                    "QCheckBox { font-size: 11px; color: #333333; background: transparent; spacing: 8px; }"
                )
                vbox.addWidget(cb)
                checkboxes.append(cb)

            bind_name = group.get("bind")
            if bind_name:
                setattr(self.owner, str(bind_name), checkboxes)

            groups_layout.addWidget(box)

        parent_layout.addLayout(groups_layout)

    # ── Special section builders (each returns a styled QFrame) ────────

    def _build_checkbox_list_section(self, section: dict, label_width: int) -> QFrame:
        """Title + [label + checkbox] rows.  Binds ``bind`` (checkboxes list)
        and optional ``label_bind`` (labels list) on the owner."""
        box = QFrame()
        box.setStyleSheet(_SECTION_BOX_STYLE)
        layout = QVBoxLayout(box)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = section.get("title")
        if title:
            heading = QLabel(str(title))
            heading.setStyleSheet(_HEADING_STYLE)
            layout.addWidget(heading)

        checkboxes: list[QCheckBox] = []
        labels: list[QLabel] = []
        default_checked = bool(section.get("default_checked", False))
        row_height = int(section.get("field_height", 28))

        for item_text in section.get("items") or []:
            row = QHBoxLayout()
            row.setSpacing(10)
            lbl = QLabel(str(item_text))
            lbl.setStyleSheet(_LABEL_STYLE)
            lbl.setMinimumWidth(label_width)
            cb = QCheckBox()
            cb.setChecked(default_checked)
            cb.setFixedHeight(row_height)
            row.addWidget(lbl)
            row.addWidget(cb)
            row.addStretch()
            layout.addLayout(row)
            checkboxes.append(cb)
            labels.append(lbl)

        bind = section.get("bind")
        if bind:
            setattr(self.owner, str(bind), checkboxes)
        label_bind = section.get("label_bind")
        if label_bind:
            setattr(self.owner, str(label_bind), labels)

        return box

    def _build_dynamic_checkbox_list_section(self, section: dict, label_width: int) -> QFrame:
        """Title + empty QVBoxLayout container — tabs populate later.

        Binds:
        * ``bind``          — initial empty list (tabs append QCheckBox refs to it)
        * ``label_bind``    — initial empty list for labels
        * ``layout_bind``   — the inner QVBoxLayout (so tabs can addLayout / addWidget)
        * ``container_bind``— the QWidget hosting the layout (handy for show/hide)
        * ``title_bind``    — the QLabel title (handy to toggle visibility)
        """
        box = QFrame()
        box.setStyleSheet(_SECTION_BOX_STYLE)
        outer = QVBoxLayout(box)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(8)

        title_lbl: QLabel | None = None
        title = section.get("title")
        if title:
            title_lbl = QLabel(str(title))
            title_lbl.setStyleSheet(_HEADING_STYLE)
            outer.addWidget(title_lbl)

        container = QWidget()
        inner = QVBoxLayout(container)
        inner.setContentsMargins(0, 0, 0, 0)
        inner.setSpacing(8)
        outer.addWidget(container)

        owner = self.owner
        if section.get("bind"):
            setattr(owner, str(section["bind"]), [])
        if section.get("label_bind"):
            setattr(owner, str(section["label_bind"]), [])
        if section.get("layout_bind"):
            setattr(owner, str(section["layout_bind"]), inner)
        if section.get("container_bind"):
            setattr(owner, str(section["container_bind"]), container)
        if title_lbl is not None and section.get("title_bind"):
            setattr(owner, str(section["title_bind"]), title_lbl)

        return box

    def _build_custom_vehicle_table_section(self, section: dict, label_width: int) -> QFrame:
        """Header (title + Add button) + 4-col QTableWidget (no headers, no grid).

        Columns: [name, checkbox, edit button, delete button] — populated by the
        tab at runtime (e.g. ``LiveLoadTab._add_custom_vehicle``).
        """
        box = QFrame()
        box.setStyleSheet(_SECTION_BOX_STYLE)
        layout = QVBoxLayout(box)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        row_height = int(section.get("field_height", 28))

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(10)

        title_lbl = QLabel(str(section.get("title", "")))
        title_lbl.setStyleSheet(_HEADING_STYLE)
        title_lbl.setMinimumWidth(label_width)
        header_row.addWidget(title_lbl)

        add_button = QPushButton(str(section.get("add_button_text", "Add Custom Vehicle")))
        add_button.setFixedHeight(row_height)
        add_button.setStyleSheet(
            "QPushButton { background-color: white; border: 1px solid #3a3a3a; "
            "border-radius: 3px; font-size: 10px; font-weight: 600; color: #3a3a3a; "
            "padding: 3px 8px; }"
            "QPushButton:hover { background-color: #f8f8f8; }"
        )
        header_row.addWidget(add_button)
        header_row.addStretch()
        layout.addLayout(header_row)

        table = QTableWidget(0, 4)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table.verticalHeader().setDefaultSectionSize(row_height + 4)
        table.verticalHeader().setMinimumSectionSize(row_height + 4)
        table.horizontalHeader().setVisible(False)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.setShowGrid(False)
        table.setFrameShape(QFrame.NoFrame)
        hdr = table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Fixed)
        hdr.setSectionResizeMode(1, QHeaderView.Fixed)
        hdr.setSectionResizeMode(2, QHeaderView.Fixed)
        hdr.setSectionResizeMode(3, QHeaderView.Fixed)
        col_widths = section.get("column_widths") or [label_width + 10, 30, 60, 70]
        for idx, w in enumerate(col_widths[:4]):
            table.setColumnWidth(idx, int(w))
        table.setStyleSheet(
            "QTableWidget { border: none; background-color: transparent; margin-top: 4px; }"
            "QTableWidget::item { padding: 2px 0px; border: none; color: #3a3a3a; font-size: 11px; }"
        )
        layout.addWidget(table)

        owner = self.owner
        for key, widget in (
            (section.get("bind"),              table),
            (section.get("add_button_bind"),   add_button),
            (section.get("frame_bind"),        box),
            (section.get("header_label_bind"), title_lbl),
        ):
            if key:
                setattr(owner, str(key), widget)

        return box

    def _build_custom_load_combo_table_section(self, section: dict) -> QFrame:
        """Title + Edit/Delete/Add buttons + configurable-column QTableWidget.

        Schema-configurable columns via ``columns`` (list of header strings) and
        ``column_widths`` (optional list of ints).  Buttons are bound by
        ``edit_button_bind`` / ``delete_button_bind`` / ``add_button_bind`` so
        the tab hooks its CRUD handlers via ``on_click`` or directly.
        """
        box = QFrame()
        box.setStyleSheet(_SECTION_BOX_STYLE)
        layout = QVBoxLayout(box)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(8)

        title_lbl = QLabel(str(section.get("title", "")))
        title_lbl.setStyleSheet(_HEADING_STYLE)
        header_row.addWidget(title_lbl)
        header_row.addStretch()

        btn_style = (
            "QPushButton { background-color: white; border: 1px solid #3a3a3a; "
            "border-radius: 3px; font-size: 10px; font-weight: 600; color: #3a3a3a; "
            "padding: 3px 10px; }"
            "QPushButton:hover { background-color: #f8f8f8; }"
        )
        row_height = int(section.get("field_height", 28))

        edit_btn   = QPushButton(str(section.get("edit_button_text",   "Edit")))
        delete_btn = QPushButton(str(section.get("delete_button_text", "Delete")))
        add_btn    = QPushButton(str(section.get("add_button_text",    "Add")))
        for btn in (edit_btn, delete_btn, add_btn):
            btn.setFixedHeight(row_height)
            btn.setStyleSheet(btn_style)
            header_row.addWidget(btn)
        layout.addLayout(header_row)

        columns = section.get("columns") or ["Include", "Name", "Values"]
        table = QTableWidget(0, len(columns))
        table.setHorizontalHeaderLabels([str(c) for c in columns])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        hdr = table.horizontalHeader()
        column_widths = section.get("column_widths")
        if column_widths:
            for idx, w in enumerate(column_widths[: len(columns)]):
                hdr.setSectionResizeMode(idx, QHeaderView.Fixed)
                table.setColumnWidth(idx, int(w))
        else:
            for idx in range(len(columns)):
                hdr.setSectionResizeMode(idx, QHeaderView.Stretch)
        table.setStyleSheet(
            "QTableWidget { background: #ffffff; border: 1px solid #a0a0a0; "
            "gridline-color: #d0d0d0; }"
            "QTableWidget::item { padding: 4px; font-size: 10px; color: #3a3a3a; "
            "border-bottom: 1px solid #c0c0c0; }"
            "QTableWidget::item:selected { background: #d0e8ff; }"
            "QHeaderView::section { color: #2a2a2a; background: #f0f0f0; "
            "font-size: 10px; font-weight: 600; padding: 5px; border: none; "
            "border-right: 1px solid #d0d0d0; border-bottom: 1px solid #d0d0d0; }"
        )
        min_h = section.get("min_table_height")
        if min_h:
            table.setMinimumHeight(int(min_h))
        layout.addWidget(table)

        owner = self.owner
        for key, widget in (
            (section.get("bind"),              table),
            (section.get("edit_button_bind"),  edit_btn),
            (section.get("delete_button_bind"), delete_btn),
            (section.get("add_button_bind"),   add_btn),
            (section.get("title_bind"),        title_lbl),
            (section.get("frame_bind"),        box),
        ):
            if key:
                setattr(owner, str(key), widget)

        return box

    def _build_single_field_section(
        self,
        section: dict,
        label_width: int,
        field_width: int,
    ) -> QFrame:
        """For sections whose ``type`` is a field type (``line``, ``combo``,
        ``mode_line`` …) — i.e. the section dict itself IS the field
        definition.  Wraps a single labelled row inside a section box."""
        box = QFrame()
        box.setStyleSheet(_SECTION_BOX_STYLE)
        outer = QVBoxLayout(box)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(8)

        title = section.get("title")
        if title:
            heading = QLabel(str(title))
            heading.setStyleSheet(_HEADING_STYLE)
            outer.addWidget(heading)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)

        lbl = self._make_field_label(section, label_width)
        row.addWidget(lbl)

        widget = self.build_field(section, field_width)
        row.addWidget(widget)
        row.addStretch()
        outer.addLayout(row)

        return box

    def _build_diagram_section(self, section: dict) -> QFrame:
        """Static figure placeholder — dark panel with centred text."""
        frame = QFrame()
        min_size = section.get("min_size") or [380, 130]
        frame.setMinimumSize(int(min_size[0]), int(min_size[1]))
        max_h = section.get("max_height")
        if max_h:
            frame.setMaximumHeight(int(max_h))
        bg = section.get("bg_color", "#d0d0d0")
        border = section.get("border_color", "#a0a0a0")
        frame.setStyleSheet(
            f"QFrame {{ border: 1px solid {border}; border-radius: 4px; background-color: {bg}; }}"
        )

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)

        label = QLabel(str(section.get("text", "")))
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(
            "font-size: 11px; font-weight: 600; color: #2a2a2a; "
            "background: transparent; border: none;"
        )
        layout.addWidget(label, 1)

        bind = section.get("bind")
        if bind:
            setattr(self.owner, str(bind), label)

        return frame

    def _build_stacked_section(
        self,
        parent_layout: QLayout,
        section: dict,
        label_width: int,
        field_width: int,
    ) -> None:
        """QStackedWidget whose active page is driven by a bound combo box.

        Schema shape::

            {
                "type": "stacked",
                "bind": "custom_load_stack",
                "switch_source": "custom_load_type_combo",
                "pages": [
                    {"match": "Point", "sections": [...]},
                    {"match": "Line",  "sections": [...]},
                ],
            }
        """
        stack = QStackedWidget()
        stack.setStyleSheet("QStackedWidget { border: none; background: transparent; }")

        pages = section.get("pages") or []
        matches: list[tuple[str, int]] = []

        for idx, page in enumerate(pages):
            page_widget = QWidget()
            page_widget.setStyleSheet("background: transparent;")
            page_layout = QVBoxLayout(page_widget)
            page_layout.setContentsMargins(0, 0, 0, 0)
            page_layout.setSpacing(10)

            for sub in page.get("sections") or []:
                self._dispatch_section(page_layout, sub, label_width, field_width)

            stack.addWidget(page_widget)
            match = page.get("match")
            if match is not None:
                matches.append((str(match), idx))

        bind = section.get("bind")
        if bind:
            setattr(self.owner, str(bind), stack)

        switch_source = section.get("switch_source")
        if switch_source:
            source = getattr(self.owner, str(switch_source), None)
            if isinstance(source, QComboBox):
                def on_change(text: str, m=matches, s=stack) -> None:
                    for match_text, idx in m:
                        if match_text == text:
                            s.setCurrentIndex(idx)
                            return

                source.currentTextChanged.connect(on_change)
                on_change(source.currentText())

        parent_layout.addWidget(stack)

    # ── CAD builders ────────────────────────────────────────────────────

    _SIZE_POLICY_MAP = {
        "expanding": QSizePolicy.Expanding,
        "preferred": QSizePolicy.Preferred,
        "fixed":     QSizePolicy.Fixed,
        "minimum":   QSizePolicy.Minimum,
    }

    @staticmethod
    def _read_widget_value(widget: QWidget):
        """Extract a plain-Python value from a bound input widget."""
        if widget is None:
            return None
        if isinstance(widget, QLineEdit):
            return widget.text()
        if isinstance(widget, QComboBox):
            return widget.currentText()
        if isinstance(widget, QCheckBox):
            return widget.isChecked()
        return None

    @staticmethod
    def _cast_value(raw, cast: str | None, default):
        if raw is None or raw == "":
            return default
        if not cast:
            return raw
        try:
            if cast == "float":
                return float(raw)
            if cast == "int":
                return int(float(raw))
            if cast == "bool":
                if isinstance(raw, bool):
                    return raw
                return str(raw).strip().lower() in {"1", "true", "yes", "on"}
            if cast == "str":
                return str(raw)
        except (TypeError, ValueError):
            return default
        return raw

    def _build_cad_section(self, parent_layout: QLayout, section: dict) -> QWidget | None:
        """Instantiate a CAD widget from the registry, bind, and wire reactivity.

        Schema shape::

            {
                "type": "cad",
                "widget": "SupportDetailCADWidget",
                "bind": "right_cad",
                "min_size": [150, 200],
                "size_policy": "expanding",
                "update_method": "update_params",
                "params_map": {
                    "bearing_length": {"widget": "bearing_length_input",
                                        "cast": "float", "default": 400}
                },
                "reactive_sources": [
                    {"widget": "bearing_length_input", "signal": "textChanged"}
                ],
            }
        """
        widget_name = section.get("widget")
        if not widget_name:
            return None

        try:
            from osdagbridge.desktop.ui.dialogs.tabs.cad_registry import CAD_WIDGETS
        except ImportError:
            _log.warning("UIBuilder[%s]: cad_registry not importable — CAD widget %r skipped", type(self.owner).__name__, widget_name)
            return None

        widget_cls = CAD_WIDGETS.get(str(widget_name))
        if widget_cls is None:
            _log.warning("UIBuilder[%s]: CAD widget %r not in cad_registry.CAD_WIDGETS", type(self.owner).__name__, widget_name)
            return None

        cad_widget = widget_cls()
        self._apply_cad_sizing(cad_widget, section)

        bind = section.get("bind")
        if bind:
            setattr(self.owner, str(bind), cad_widget)
            cad_widget.setObjectName(str(bind))

        update_method_name = str(section.get("update_method", "update_params"))
        params_map = section.get("params_map") or {}
        reactive_sources = section.get("reactive_sources") or []

        if not hasattr(cad_widget, update_method_name):
            _log.warning(
                "UIBuilder[%s]: CAD widget %s has no method %r",
                type(self.owner).__name__, type(cad_widget).__name__, update_method_name,
            )

        def refresh(*_args) -> None:
            method = getattr(cad_widget, update_method_name, None)
            if not callable(method):
                return
            params: dict = {}
            for param_name, entry in params_map.items():
                if isinstance(entry, str):
                    source_name, cast, default = entry, None, None
                else:
                    source_name = entry.get("widget")
                    cast = entry.get("cast")
                    default = entry.get("default")
                source = getattr(self.owner, str(source_name), None) if source_name else None
                raw = self._read_widget_value(source)
                params[param_name] = self._cast_value(raw, cast, default)
            method(params)

        for src in reactive_sources:
            source_name = src.get("widget") if isinstance(src, dict) else src
            if not source_name:
                continue
            signal_name = src.get("signal", "textChanged") if isinstance(src, dict) else "textChanged"
            source = getattr(self.owner, str(source_name), None)
            if source is None:
                _log.warning(
                    "UIBuilder[%s]: reactive source %r not on owner (bind it before CAD section)",
                    type(self.owner).__name__, source_name,
                )
                continue
            signal = getattr(source, str(signal_name), None)
            if signal is None:
                continue
            signal.connect(refresh)

        if reactive_sources or params_map:
            refresh()

        stretch = int(section.get("stretch", 0))
        if isinstance(parent_layout, QHBoxLayout) and stretch > 0:
            parent_layout.addWidget(cad_widget, stretch)
        else:
            parent_layout.addWidget(cad_widget)
        return cad_widget

    def _build_cad_row_section(self, parent_layout: QLayout, section: dict) -> None:
        """Horizontal row wrapper for multiple CAD widgets (e.g. Support left + detail)."""
        wrap = QFrame()
        wrap.setStyleSheet(_CARD_STYLE)
        row = QHBoxLayout(wrap)
        row.setContentsMargins(10, 10, 10, 10)
        row.setSpacing(int(section.get("spacing", 12)))

        for cad in section.get("cads") or []:
            self._build_cad_section(row, cad)

        parent_layout.addWidget(wrap)

    def _apply_cad_sizing(self, widget: QWidget, section: dict) -> None:
        min_size = section.get("min_size")
        if min_size:
            widget.setMinimumSize(int(min_size[0]), int(min_size[1]))
        max_size = section.get("max_size")
        if max_size:
            widget.setMaximumSize(int(max_size[0]), int(max_size[1]))
        policy_name = str(section.get("size_policy", "expanding")).lower()
        policy = self._SIZE_POLICY_MAP.get(policy_name, QSizePolicy.Expanding)
        widget.setSizePolicy(policy, policy)

    # ── Widget helpers ──────────────────────────────────────────────────

    # ------------------------------------------------------------------ #
    # Conditional visibility — wired from schema "conditions" key
    # ------------------------------------------------------------------ #

    def _wire_conditions(self) -> None:
        """Post-build pass: wire every field with a 'conditions' key."""
        for field in self._iter_fields_with_conditions(self.schema):
            ftype = str(field.get("type") or "").strip().lower()
            target_bind = field.get("bind_value") if ftype == "mode_line" else field.get("bind")
            if not target_bind:
                continue
            target = getattr(self.owner, str(target_bind), None)
            if target is None:
                _log.warning(
                    "UIBuilder[%s]: conditions target bind %r not on owner",
                    type(self.owner).__name__, target_bind,
                )
                continue
            for cond in (field.get("conditions") or []):
                self._connect_condition(cond, target)

    @staticmethod
    def _iter_fields_with_conditions(node):
        """Recursively yield field dicts that carry a 'conditions' key."""
        if not isinstance(node, dict):
            return
        if node.get("conditions"):
            yield node
        fields = node.get("fields")
        if isinstance(fields, dict):
            for f in fields.values():
                yield from UIBuilder._iter_fields_with_conditions(f)
        elif isinstance(fields, list):
            for f in fields:
                if isinstance(f, dict):
                    for rf in (f.get("row_fields") or []):
                        if isinstance(rf, dict):
                            yield from UIBuilder._iter_fields_with_conditions(rf)
                    yield from UIBuilder._iter_fields_with_conditions(f)
        for row in (node.get("rows") or []):
            for f in (row.get("fields") or []):
                if isinstance(f, dict):
                    yield from UIBuilder._iter_fields_with_conditions(f)
        for key in ("sections", "cards", "pages"):
            for sub in (node.get(key) or []):
                yield from UIBuilder._iter_fields_with_conditions(sub)

    def _connect_condition(self, cond: dict, target: QWidget) -> None:
        """Wire one condition dict to the source widget signal."""
        source_bind = cond.get("when")
        if not source_bind:
            return
        source = getattr(self.owner, str(source_bind), None)
        if source is None:
            _log.warning(
                "UIBuilder[%s]: conditions source bind %r not on owner",
                type(self.owner).__name__, source_bind,
            )
            return

        equals_val = cond.get("equals")
        action = str(cond.get("action", "enable")).lower()

        def evaluate(*_args) -> None:
            if isinstance(source, QComboBox):
                val = source.currentText()
            elif isinstance(source, QCheckBox):
                val = source.isChecked()
            elif isinstance(source, QLineEdit):
                val = source.text()
            else:
                return
            met = (val == equals_val)
            if action == "enable":
                target.setEnabled(met)
            elif action == "disable":
                target.setEnabled(not met)
            elif action == "show":
                target.setVisible(met)
            elif action == "hide":
                target.setVisible(not met)

        if isinstance(source, QComboBox):
            source.currentTextChanged.connect(evaluate)
        elif isinstance(source, QCheckBox):
            source.toggled.connect(evaluate)
        elif isinstance(source, QLineEdit):
            source.textChanged.connect(evaluate)

        evaluate()  # set initial state immediately

    def _apply_validator(self, widget: QLineEdit, validator_def: dict | None) -> None:
        if not validator_def:
            return
        vtype = str(validator_def.get("type") or "").strip().lower()
        if vtype == "double_range":
            bottom   = float(validator_def.get("bottom", 0.0))
            top      = float(validator_def.get("top", 1e12))
            decimals = int(validator_def.get("decimals", 3))
            v = QDoubleValidator(bottom, top, decimals, widget)
            if validator_def.get("notation") == "scientific":
                v.setNotation(QDoubleValidator.ScientificNotation)
            else:
                v.setNotation(QDoubleValidator.StandardNotation)
            widget.setValidator(v)
        elif vtype == "int_range":
            bottom = int(validator_def.get("bottom", 0))
            top    = int(validator_def.get("top", 1_000_000_000))
            widget.setValidator(QIntValidator(bottom, top, widget))

    def _connect_signals(self, widget: QWidget, field_def: dict) -> None:
        owner = self.owner

        on_change = field_def.get("on_change")
        if on_change and isinstance(widget, QComboBox):
            handler = getattr(owner, str(on_change), None)
            if handler is None:
                _log.warning("UIBuilder[%s]: on_change=%r not found on owner", type(owner).__name__, on_change)
            elif callable(handler):
                widget.currentTextChanged.connect(handler)

        on_text_changed = field_def.get("on_text_changed")
        if on_text_changed and isinstance(widget, QLineEdit):
            handler = getattr(owner, str(on_text_changed), None)
            if handler is None:
                _log.warning("UIBuilder[%s]: on_text_changed=%r not found on owner", type(owner).__name__, on_text_changed)
            elif callable(handler):
                widget.textChanged.connect(handler)

        on_editing_finished = field_def.get("on_editing_finished")
        if on_editing_finished and isinstance(widget, QLineEdit):
            handler = getattr(owner, str(on_editing_finished), None)
            if handler is None:
                _log.warning("UIBuilder[%s]: on_editing_finished=%r not found on owner", type(owner).__name__, on_editing_finished)
            elif callable(handler):
                widget.editingFinished.connect(handler)

        on_toggled = field_def.get("on_toggled")
        if on_toggled and isinstance(widget, QCheckBox):
            handler = getattr(owner, str(on_toggled), None)
            if handler is None:
                _log.warning("UIBuilder[%s]: on_toggled=%r not found on owner", type(owner).__name__, on_toggled)
            elif callable(handler):
                widget.toggled.connect(handler)

        on_click = field_def.get("on_click")
        if on_click and isinstance(widget, QPushButton):
            handler = getattr(owner, str(on_click), None)
            if handler is None:
                _log.warning("UIBuilder[%s]: on_click=%r not found on owner", type(owner).__name__, on_click)
            elif callable(handler):
                widget.clicked.connect(handler)

    def _bind_widget(self, widget: QWidget, field_def: dict) -> None:
        field_id = field_def.get("id")
        if field_id:
            widget.setObjectName(str(field_id))

        bind_name = field_def.get("bind")
        if bind_name:
            existing = getattr(self.owner, str(bind_name), _MISSING)
            if existing is not _MISSING and existing is not widget:
                _log.warning(
                    "UIBuilder[%s]: bind %r already set (%s) — overwriting with %s",
                    type(self.owner).__name__, bind_name,
                    type(existing).__name__, type(widget).__name__,
                )
            setattr(self.owner, str(bind_name), widget)
