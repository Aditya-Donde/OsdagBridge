"""Special section builders — bespoke section types that return their own
styled QFrame and handle their own layout.

Includes the public CRUD utilities ``rebuild_dynamic_checkbox_list`` and
``build_table_row`` used by tabs that mutate dynamic content at runtime.
"""

import inspect
import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLayout,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from osdagbridge.desktop.ui.dialogs.tabs.builder.constants import (
    _HEADING_STYLE,
    _LABEL_STYLE,
    _SECTION_BOX_STYLE,
)


def _default_tab_class_resolver(class_name: str):
    """Lazy fallback resolver — preserves the original additional-inputs registry."""
    from osdagbridge.desktop.ui.dialogs.tabs.additional_inputs.tab_registry import get_tab_class
    return get_tab_class(class_name)

_log = logging.getLogger(__name__)


class SpecialSectionsMixin:
    """Bespoke section types + table/checkbox-list CRUD helpers."""

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

    def _build_tab_container(self, section: dict) -> QWidget:
        """Build a QTabWidget and populate it with registered sub-tabs."""
        tabs = QTabWidget()
        tabs.setObjectName(str(section.get("id", "")))
        tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        min_height = section.get("min_height")
        if min_height:
            tabs.setMinimumHeight(int(min_height))
        max_height = section.get("max_height")
        if max_height:
            tabs.setMaximumHeight(int(max_height))
        min_width = section.get("min_width")
        if min_width:
            tabs.setMinimumWidth(int(min_width))
        max_width = section.get("max_width")
        if max_width:
            tabs.setMaximumWidth(int(max_width))

        tabs.setStyleSheet(
            "QTabWidget::pane { border: 1px solid #b0b0b0; background: #f5f5f5; }"
            "QTabBar::tab { background: #e8e8e8; color: #555555; padding: 8px 16px; "
            "border: 1px solid #b0b0b0; border-bottom: none; font-size: 11px; }"
            "QTabBar::tab:selected { background: #90AF13; color: #ffffff; "
            "font-weight: 700; border-color: #90AF13; }"
            "QTabBar::tab:disabled { color: #bfbfbf; background: #e6e6e6; }"
            "QTabBar::tab:hover:!selected { background: #d0d0d0; }"
        )

        for tab_def in section.get("tabs", []):
            label = str(tab_def.get("label", "Tab"))
            class_name = tab_def.get("widget_class")
            bind_name = tab_def.get("bind")

            if not class_name:
                _log.warning("UIBuilder[%s]: Tab definition missing 'widget_class'", type(self.owner).__name__)
                continue

            try:
                resolver = getattr(self, "tab_class_resolver", None) or _default_tab_class_resolver
                tab_cls = resolver(class_name)
                sig = inspect.signature(tab_cls.__init__)
                kwargs = {}
                if "owner" in sig.parameters:
                    kwargs["owner"] = self.owner

                tab_widget = tab_cls(parent=self.owner, **kwargs)

                if bind_name:
                    setattr(self.owner, str(bind_name), tab_widget)

                tabs.addTab(tab_widget, label)
            except Exception as e:
                _log.error("UIBuilder[%s]: Failed to build tab %r: %s", type(self.owner).__name__, class_name, e)

        return tabs

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

    @staticmethod
    def rebuild_dynamic_checkbox_list(
        layout: QLayout,
        items: list,
        *,
        default_checked: bool = True,
        label_width: int = 220,
        field_height: int = 28,
    ) -> tuple:
        """Clear *layout* and rebuild one label+checkbox row per item.

        Returns (checkboxes, labels).
        """
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                while child.layout().count():
                    sub = child.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

        checkboxes: list[QCheckBox] = []
        labels: list[QLabel] = []
        for text in items:
            row = QHBoxLayout()
            row.setSpacing(10)

            lbl = QLabel(str(text))
            lbl.setStyleSheet(
                "font-size: 11px; font-weight: 600; color: #3a3a3a;"
                " background: transparent; border: none;"
            )
            lbl.setMinimumWidth(label_width)

            cb = QCheckBox()
            cb.setChecked(default_checked)
            cb.setFixedHeight(field_height)

            row.addWidget(lbl)
            row.addWidget(cb)
            row.addStretch()
            layout.addLayout(row)

            checkboxes.append(cb)
            labels.append(lbl)

        return checkboxes, labels

    @staticmethod
    def build_table_row(
        table: QTableWidget,
        columns: list,
        row_height: int = 32,
    ) -> int:
        """Append a row to *table* and return its index.

        Each column dict supports:
          type        "text" | "checkbox" | "button"
          value       str — cell text (type=text)
          alignment   Qt.AlignmentFlag — text cell alignment
          checked     bool — initial state (type=checkbox)
          text        str — button label (type=button)
          width       int — button fixed width (type=button)
          on_click    callable — button clicked handler (type=button)
          align       Qt.AlignmentFlag — cell-wrapper alignment (checkbox/button)
        """
        row_idx = table.rowCount()
        table.insertRow(row_idx)

        for col_idx, col in enumerate(columns):
            col_type = str(col.get("type", "text")).lower()

            if col_type == "text":
                item = QTableWidgetItem(str(col.get("value", "")))
                item.setTextAlignment(int(col.get("alignment", Qt.AlignLeft | Qt.AlignVCenter)))
                item.setFlags(Qt.ItemIsEnabled)
                table.setItem(row_idx, col_idx, item)

            elif col_type == "checkbox":
                cb = QCheckBox()
                cb.setChecked(bool(col.get("checked", True)))
                align = col.get("align", Qt.AlignCenter)
                table.setCellWidget(row_idx, col_idx, SpecialSectionsMixin._wrap_cell(cb, align))

            elif col_type == "button":
                btn = QPushButton(str(col.get("text", "")))
                w = int(col.get("width", 60))
                btn.setFixedSize(w, max(row_height - 4, 20))
                btn.setStyleSheet(SpecialSectionsMixin._table_button_style())
                on_click = col.get("on_click")
                if callable(on_click):
                    btn.clicked.connect(on_click)
                align = col.get("align", Qt.AlignVCenter)
                table.setCellWidget(row_idx, col_idx, SpecialSectionsMixin._wrap_cell(btn, align))

        table.setRowHeight(row_idx, row_height)
        return row_idx

    @staticmethod
    def _wrap_cell(widget: QWidget, alignment=Qt.AlignCenter) -> QWidget:
        """Wrap *widget* in a centred cell container."""
        container = QWidget()
        lay = QHBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        if alignment == Qt.AlignCenter:
            lay.setAlignment(Qt.AlignCenter)
            lay.addWidget(widget)
        else:
            lay.addWidget(widget, 0, alignment)
            lay.addStretch()
        return container

    @staticmethod
    def _table_button_style() -> str:
        return (
            "QPushButton { background-color: white; border: 1px solid #3a3a3a;"
            " border-radius: 3px; font-size: 10px; font-weight: 600;"
            " color: #3a3a3a; padding: 0px; }"
            " QPushButton:hover { background-color: #f8f8f8; }"
        )
