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
    QSizePolicy,
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

    def _description_has_content(self, desc: dict | None) -> bool:
        if not isinstance(desc, dict):
            return bool(desc)
        if not bool(desc.get("hide_when_empty", True)):
            return True
        return bool(str(desc.get("text", "")).strip())

    def _build_description_card(self, desc: dict | None = None) -> QFrame | None:
        """Build an optional right-side description card.

        Empty description panels are hidden by default. A schema can force the
        old placeholder behavior with ``{"hide_when_empty": False}``.
        """
        if desc is None:
            desc = self.schema.get("description", {})
        if not self._description_has_content(desc):
            return None

        right_card = QFrame()
        right_card.setStyleSheet(_RIGHT_CARD_STYLE)
        right_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_card.setMinimumWidth(int(desc.get("min_width", 260)))
        min_height = desc.get("min_height", 420)
        if min_height:
            right_card.setMinimumHeight(int(min_height))
        max_width = desc.get("max_width")
        if max_width:
            right_card.setMaximumWidth(int(max_width))
        max_height = desc.get("max_height")
        if max_height:
            right_card.setMaximumHeight(int(max_height))

        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(10)

        title = str(desc.get("title", "Description Box"))
        if title and bool(desc.get("show_title", True)):
            desc_title = QLabel(title)
            desc_title.setAlignment(Qt.AlignCenter)
            desc_title.setStyleSheet(
                "font-size: 12px; font-weight: 700; color: #000000; "
                "background: transparent; border: none;"
            )
            right_layout.addWidget(desc_title)

        text = str(desc.get("text", ""))
        if text:
            desc_text = QLabel(text)
            desc_text.setWordWrap(True)
            desc_text.setStyleSheet(
                "font-size: 11px; color: #4b4b4b; background: transparent; border: none;"
            )
            right_layout.addWidget(desc_text)

        right_layout.addStretch()
        return right_card

    def _add_section_widget(self, parent_layout: QLayout, widget: QWidget, section: dict) -> None:
        stretch = int(section.get("stretch", 0))
        if isinstance(parent_layout, QBoxLayout):
            parent_layout.addWidget(widget, stretch)
        else:
            parent_layout.addWidget(widget)

    def _build_layout_node(
        self,
        parent_layout: QLayout,
        node,
        label_width: int = _DEFAULT_LABEL_WIDTH,
        field_width: int = _DEFAULT_FIELD_WIDTH,
    ) -> None:
        """Render schema composition nodes such as stack, split and card.

        These nodes let schemas describe old hand-built tab composition without
        tab-specific Python builders.
        """
        if isinstance(node, list):
            for child in node:
                self._build_layout_node(parent_layout, child, label_width, field_width)
            return
        if not isinstance(node, dict):
            return

        ntype = str(node.get("type") or "stack").strip().lower()
        node_label_width = int(node.get("label_width", label_width))
        node_field_width = int(node.get("field_width", field_width))

        if ntype == "split":
            self._build_split_layout(parent_layout, node, node_label_width, node_field_width)
            return
        if ntype == "stack":
            self._build_stack_layout(parent_layout, node, node_label_width, node_field_width)
            return
        if ntype == "card":
            parent_layout.addWidget(self._build_layout_card(node, node_label_width, node_field_width))
            return
        if ntype == "description":
            card = self._build_description_card(node.get("description", self.schema.get("description", {})))
            if card is not None:
                parent_layout.addWidget(card)
            return
        if ntype == "spacer":
            size = int(node.get("size", 0))
            if size > 0:
                if isinstance(parent_layout, QBoxLayout):
                    parent_layout.addSpacing(size)
            elif bool(node.get("stretch", True)) and isinstance(parent_layout, QBoxLayout):
                parent_layout.addStretch()
            return

        if "children" in node:
            self._build_stack_layout(parent_layout, node, node_label_width, node_field_width)
        elif "cards" in node:
            self._build_cards_column(parent_layout, node["cards"])
        elif "sections" in node:
            self._build_section_sequence(
                parent_layout,
                node["sections"],
                node_label_width,
                node_field_width,
                boxed_fallback=bool(node.get("boxed_fallback", True)),
            )
        elif "rows" in node:
            self._build_rows(parent_layout, node["rows"], node_label_width, node_field_width)
        elif "columns" in node:
            self._build_columns(parent_layout, node["columns"], node_label_width, node_field_width)

    def _build_stack_layout(
        self,
        parent_layout: QLayout,
        node: dict,
        label_width: int,
        field_width: int,
    ) -> None:
        children = node.get("children")
        if children is not None:
            for child in children:
                self._build_layout_node(parent_layout, child, label_width, field_width)
            return

        if "sections" in node:
            self._build_section_sequence(
                parent_layout,
                node["sections"],
                label_width,
                field_width,
                boxed_fallback=bool(node.get("boxed_fallback", True)),
            )
        if "cards" in node:
            self._build_cards_column(parent_layout, node["cards"])
        if "rows" in node:
            self._build_rows(parent_layout, node["rows"], label_width, field_width)
        if "columns" in node:
            self._build_columns(parent_layout, node["columns"], label_width, field_width)

    def _build_split_layout(
        self,
        parent_layout: QLayout,
        node: dict,
        label_width: int,
        field_width: int,
    ) -> None:
        content_row = QHBoxLayout()
        content_row.setSpacing(int(node.get("spacing", 16)))
        content_row.setContentsMargins(*[int(v) for v in node.get("margins", [0, 0, 0, 0])])

        children = node.get("children")
        if children is None:
            children = []
            for key in ("left", "center", "right"):
                child = node.get(key)
                if child is not None:
                    children.append(child)

        for child in children or []:
            widget = self._layout_node_to_widget(child, label_width, field_width)
            if widget is None:
                continue
            stretch = int(child.get("stretch", 1)) if isinstance(child, dict) else 1
            content_row.addWidget(widget, stretch)

        if content_row.count():
            stretch = int(node.get("layout_stretch", 1 if bool(node.get("fill_height", False)) else 0))
            if isinstance(parent_layout, QBoxLayout):
                parent_layout.addLayout(content_row, stretch)
            else:
                parent_layout.addLayout(content_row)

    def _layout_node_to_widget(self, node, label_width: int, field_width: int) -> QWidget | None:
        if isinstance(node, dict) and str(node.get("type") or "").strip().lower() == "description":
            widget = self._build_description_card(node.get("description", self.schema.get("description", {})))
            if widget is not None:
                self._apply_layout_sizing(widget, node)
            return widget

        container = QWidget()
        container.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(container)
        margins = node.get("margins", [0, 0, 0, 0]) if isinstance(node, dict) else [0, 0, 0, 0]
        layout.setContentsMargins(*[int(v) for v in margins])
        spacing = node.get("spacing", 8) if isinstance(node, dict) else 8
        layout.setSpacing(int(spacing))

        self._build_layout_node(layout, node, label_width, field_width)
        if isinstance(node, dict) and bool(node.get("add_stretch", False)):
            layout.addStretch()

        if layout.count() == 0:
            return None
        self._apply_layout_sizing(container, node if isinstance(node, dict) else {})
        return container

    def _apply_layout_sizing(self, widget: QWidget, node: dict) -> None:
        for key, setter in (
            ("min_width", widget.setMinimumWidth),
            ("max_width", widget.setMaximumWidth),
            ("min_height", widget.setMinimumHeight),
            ("max_height", widget.setMaximumHeight),
        ):
            value = node.get(key)
            if value:
                setter(int(value))

        policy = str(node.get("size_policy", "")).strip().lower()
        if policy == "expanding":
            widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        elif policy == "horizontal_expanding":
            widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        elif policy == "fixed":
            widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def _build_layout_card(self, node: dict, label_width: int, field_width: int) -> QFrame:
        card = QFrame()
        card.setStyleSheet(_CARD_STYLE)
        self._apply_layout_sizing(card, node)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(*[int(v) for v in node.get("card_margins", [16, 14, 16, 14])])
        card_layout.setSpacing(int(node.get("card_spacing", 10)))

        title = node.get("title")
        if title:
            lbl = QLabel(str(title))
            lbl.setStyleSheet(_HEADING_STYLE)
            card_layout.addWidget(lbl)

        self._build_stack_layout(card_layout, node, label_width, field_width)
        if bool(node.get("add_stretch", False)):
            card_layout.addStretch()
        return card

    def _build_section_sequence(
        self,
        parent_layout: QLayout,
        sections: list,
        label_width: int,
        field_width: int,
        *,
        boxed_fallback: bool = True,
    ) -> None:
        for section in sections:
            if not isinstance(section, dict):
                continue
            stype = str(section.get("type") or "").strip().lower()
            sec_label_width = int(section.get("label_width", label_width))
            sec_field_width = int(section.get("field_width", field_width))
            if stype in _SPECIAL_SECTION_TYPES or stype in _FIELD_AS_SECTION_TYPES:
                self._dispatch_section(parent_layout, section, sec_label_width, sec_field_width)
                continue
            if boxed_fallback:
                self._add_section_widget(
                    parent_layout,
                    self._make_section_box(section, sec_label_width, sec_field_width),
                    section,
                )
            else:
                self._build_sections(parent_layout, [section], sec_label_width, sec_field_width)

    def _build_two_panel(self, page_layout: QLayout) -> None:
        """Left input card (3 parts) + right description card (2 parts)."""
        schema = self.schema
        label_width = int(schema.get("label_width", _DEFAULT_LABEL_WIDTH))
        field_width = int(schema.get("field_width", _DEFAULT_FIELD_WIDTH))

        content_row = QHBoxLayout()
        content_row.setSpacing(16)

        left_outer = QFrame()
        left_outer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_outer.setStyleSheet(
            "QFrame { border: 1px solid #b2b2b2; border-radius: 10px; background-color: #ffffff; }"
        )
        left_outer_layout = QVBoxLayout(left_outer)
        left_outer_layout.setContentsMargins(0, 0, 0, 0)

        left_content = QWidget()
        left_content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
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
        left_outer_layout.addWidget(left_content, 1)

        right_card = self._build_description_card(schema.get("description", {}))

        content_row.addWidget(left_outer, 3)
        if right_card is not None:
            content_row.addWidget(right_card, 2)
        if isinstance(page_layout, QBoxLayout):
            page_layout.addLayout(content_row, 1)
        else:
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

    def _make_section_box(self, section: dict, label_width: int, field_width: int) -> QWidget:
        """Return a bordered QFrame for one section (used inside the two-panel left card)."""
        boxed = bool(section.get("boxed", True))
        box = QFrame() if boxed else QWidget()
        if boxed:
            box.setStyleSheet(_SECTION_BOX_STYLE)
        else:
            box.setStyleSheet("background: transparent; border: none;")
        box_layout = QVBoxLayout(box)
        margins = section.get("margins", [12, 12, 12, 12] if boxed else [0, 0, 0, 0])
        box_layout.setContentsMargins(*[int(v) for v in margins])
        box_layout.setSpacing(int(section.get("spacing", 14 if boxed else 8)))

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
                            label_width_override = inline_def.get("width")
                            if label_width_override:
                                lbl.setFixedWidth(int(label_width_override))
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
