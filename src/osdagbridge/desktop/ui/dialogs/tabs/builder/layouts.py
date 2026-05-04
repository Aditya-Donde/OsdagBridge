"""High-level layout builders — two-panel, cards, sections, rows, columns.

These methods are the structural backbone: they decide whether a schema
renders as a two-panel layout, a stack of cards, a row of bordered
sections, or a flat grid of rows/columns. They delegate to
``_dispatch_section`` for special section types.
"""

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QBoxLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLayout,
    QVBoxLayout,
    QWidget,
    QCheckBox,
)

from osdagbridge.desktop.ui.dialogs.tabs.builder.constants import (
    _CARD_STYLE,
    _DEFAULT_FIELD_WIDTH,
    _DEFAULT_LABEL_WIDTH,
    _FIELD_AS_SECTION_TYPES,
    _HEADING_STYLE,
    _LABEL_STYLE,
    _LEGACY_FIELD_LIST_KEYS,
    _RIGHT_CARD_STYLE,
    _SECTION_BOX_STYLE,
    _SPECIAL_SECTION_TYPES,
)

_log = logging.getLogger(__name__)


class LayoutBuildersMixin:
    """Layout-level builders: panels, cards, sections, rows, columns."""

    def _add_section_widget(self, parent_layout: QLayout, widget: QWidget, section: dict) -> None:
        stretch = int(section.get("stretch", 0))
        if isinstance(parent_layout, QBoxLayout):
            parent_layout.addWidget(widget, stretch)
        else:
            parent_layout.addWidget(widget)

    def _build_two_panel(self, page_layout: QLayout) -> None:
        """Left input card (3 parts) + right description card (2 parts)."""
        schema = self.schema
        label_width = int(schema.get("label_width", _DEFAULT_LABEL_WIDTH))
        field_width = int(schema.get("field_width", _DEFAULT_FIELD_WIDTH))

        content_row = QHBoxLayout()
        content_row.setSpacing(16)

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
        elif self._has_legacy_groups(schema):
            self._build_legacy_groups(left_layout)

        left_layout.addStretch()
        left_outer_layout.addWidget(left_content)

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

    def _has_legacy_groups(self, schema: dict) -> bool:
        return bool(schema.get("overview")) or any(schema.get(key) for key in _LEGACY_FIELD_LIST_KEYS)

    def _build_legacy_groups(self, parent_layout: QLayout) -> None:
        """Render older tab schemas that split inputs into overview/input lists."""
        schema = self.schema
        label_width = int(schema.get("label_width", _DEFAULT_LABEL_WIDTH))
        field_width = int(schema.get("field_width", _DEFAULT_FIELD_WIDTH))

        for section in schema.get("overview") or []:
            self._dispatch_section(parent_layout, section, label_width, field_width)

        titles = {
            "section_inputs": "Section Inputs:",
            "stiffener_inputs": "Stiffener Inputs:",
            "web_buckling_inputs": "Web Buckling Inputs:",
        }
        for key in _LEGACY_FIELD_LIST_KEYS:
            fields = schema.get(key) or []
            if not fields:
                continue
            self._dispatch_section(
                parent_layout,
                {
                    "id": key,
                    "type": "section_box",
                    "title": titles.get(key, key.replace("_", " ").title()),
                    "fields": fields,
                },
                label_width,
                field_width,
            )

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
            self._add_section_widget(
                parent_layout, self._build_checkbox_list_section(section, label_width), section
            )
        elif stype == "custom_vehicle_table":
            self._add_section_widget(
                parent_layout,
                self._build_custom_vehicle_table_section(section, label_width),
                section,
            )
        elif stype == "dynamic_checkbox_list":
            self._add_section_widget(
                parent_layout,
                self._build_dynamic_checkbox_list_section(section, label_width),
                section,
            )
        elif stype == "custom_load_combo_table":
            self._add_section_widget(
                parent_layout, self._build_custom_load_combo_table_section(section), section
            )
        elif stype == "cad":
            self._build_cad_section(parent_layout, section)
        elif stype == "cad_row":
            self._build_cad_row_section(parent_layout, section)
        elif stype == "legend":
            self._add_section_widget(parent_layout, self._build_legend_widget(section), section)
        elif stype == "stacked":
            self._build_stacked_section(parent_layout, section, label_width, field_width)
        elif stype == "tab_container":
            self._add_section_widget(parent_layout, self._build_tab_container(section), section)
        elif stype == "diagram":
            self._add_section_widget(parent_layout, self._build_diagram_section(section), section)
        elif stype in {"input_group", "computed_group", "output_group", "section_box"}:
            self._add_section_widget(
                parent_layout, self._make_section_box(section, label_width, field_width), section
            )
        elif stype in _FIELD_AS_SECTION_TYPES:
            self._add_section_widget(
                parent_layout,
                self._build_single_field_section(section, label_width, field_width),
                section,
            )
        else:
            if stype:
                _log.warning(
                    "UIBuilder[%s]: unknown section type=%r (id=%r) — using section_box fallback",
                    type(self.owner).__name__, stype, section.get("id"),
                )
            self._add_section_widget(
                parent_layout, self._make_section_box(section, label_width, field_width), section
            )

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

            rows = section.get("rows")
            if rows:
                self._build_rows(parent_layout, rows, sec_label_width, sec_field_width)
                continue

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
        def row_fields(row):
            if isinstance(row, dict):
                return row.get("fields", []) or []
            if isinstance(row, list):
                return row
            return []

        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(int(self.schema.get("row_vertical_spacing", 10)))
        grid.setColumnMinimumWidth(0, label_width)
        grid.setContentsMargins(0, 0, 0, 0)

        max_columns = max((len(row_fields(row)) * 2 for row in rows), default=0)
        for col in range(max_columns):
            grid.setColumnStretch(col, 0)
        if max_columns > 0:
            # Trailing empty column absorbs extra space so fields stay grouped.
            grid.setColumnStretch(max_columns, 1)

        row_idx = 0
        for row in rows:
            col = 0
            for field_def in row_fields(row):
                if not isinstance(field_def, dict):
                    continue
                ftype = str(field_def.get("type") or "line").strip().lower()
                if ftype == "button":
                    widget = self.build_field(field_def, field_def.get("width", field_width))
                    grid.addWidget(widget, row_idx, col, 1, 2, Qt.AlignLeft | Qt.AlignVCenter)
                    col += 2
                    continue

                if ftype == "checkbox":
                    widget = self.build_field(field_def, field_width)
                    grid.addWidget(widget, row_idx, col, 1, 2, Qt.AlignLeft | Qt.AlignVCenter)
                    col += 2
                    continue

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
