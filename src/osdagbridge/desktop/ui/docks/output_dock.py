"""
Output dock widget for Highway Bridge Design GUI.

Design principles (mirrors InputDock):
  - No named widget references — all widgets found via _w(key) / findChild.
  - Zero key-specific logic in OutputDock — all per-section behaviour is
    driven by the ui_config_dict declared in frontend_data.output_values().
  - One flat loop: TYPE_TITLE opens a group (analysis or design);
    fields below it belong to that group until the next TYPE_TITLE.
  - Field types supported:
      TYPE_COMBOBOX       — labelled dropdown
      TYPE_CHECKBOX       — single checkbox
      TYPE_CHECKBOX_ROW   — horizontal row of checkboxes  (exclusive: bool)
      TYPE_CHECKBOX_GRID  — N-column grid of checkboxes   (exclusive: bool)
      TYPE_BUTTON         — label + action button (design sections)

ui_config_dict extra keys for analysis fields:
    group_title : str  — opens a nested bordered QGroupBox with this title;
                         all following fields land inside it until group_end.
    group_end   : bool — closes the current nested group after this field.
    exclusive   : bool — for checkbox types; only one can be checked at a time.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy,
    QPushButton, QGroupBox, QCheckBox, QScrollArea, QFrame, QComboBox,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

from osdagbridge.core.utils.common import (
    TYPE_TITLE, TYPE_BUTTON, TYPE_COMBOBOX,
    TYPE_CHECKBOX, TYPE_CHECKBOX_ROW, TYPE_CHECKBOX_GRID,
)
from osdagbridge.desktop.ui.utils.custom_buttons import DockCustomButton
from osdagbridge.desktop.ui.docks.dock_utils import apply_field_style


# ── Styles ────────────────────────────────────────────────────────────────────

GROUPBOX_STYLE = (
    "QGroupBox { border:1px solid #90AF13; border-radius:4px; background-color:white;"
    "  padding:8px; margin-top:12px; font-size:10px; font-weight:bold; color:#333; }"
    "QGroupBox::title { subcontrol-origin:margin; subcontrol-position:top left;"
    "  left:8px; padding:0 4px; margin-top:4px; background-color:white; color:#333; }"
)
SUBGROUP_STYLE = (
    "QGroupBox { border:1px solid #90AF13; border-radius:4px; background-color:white;"
    "  padding:6px; margin-top:10px; font-size:10px; font-weight:bold; color:#333; }"
    "QGroupBox::title { subcontrol-origin:margin; subcontrol-position:top left;"
    "  left:8px; padding:0 4px; margin-top:4px; background-color:white; color:#333; }"
)
ACTION_BTN_STYLE = (
    "QPushButton { background-color:#90AF13; color:white; font-weight:bold; border:none;"
    "  border-radius:4px; padding:8px 20px; font-size:11px; min-width:80px; }"
    "QPushButton:hover { background-color:#7a9a12; }"
    "QPushButton:disabled { background:#D0D0D0; color:#666; }"
)
LABEL_STYLE       = "QLabel { color:#000; font-size:12px; background:transparent; }"
SMALL_LABEL_STYLE = "QLabel { color:#333; font-size:10px; font-weight:normal; background:transparent; }"


class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()


# ── OutputDock ────────────────────────────────────────────────────────────────

class OutputDock(QWidget):
    """
    Output dock widget. Built entirely from output_values() schema.
    Civil engineer edits output_values() only — never this file.
    """

    def __init__(self, backend=None, parent=None):
        super().__init__()
        self.parent  = parent
        self.backend = backend
        self.setStyleSheet("background: transparent;")

        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self._build_toggle_strip()

        content_container = QWidget()
        content_container.setStyleSheet("background-color: white;")
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(10)

        content_layout.addLayout(self._build_top_bar())
        content_layout.addWidget(self._build_scroll_area())
        content_layout.addLayout(self._build_bottom_buttons())

        self.main_layout.addWidget(content_container)

    # ── Toggle strip ─────────────────────────────────────────────────────────

    def _build_toggle_strip(self):
        self.toggle_strip = QWidget()
        self.toggle_strip.setStyleSheet("background-color: #90AF13;")
        self.toggle_strip.setFixedWidth(6)
        sl = QVBoxLayout(self.toggle_strip)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(0)
        sl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        self.toggle_btn = QPushButton("❯")
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setFixedSize(6, 60)
        self.toggle_btn.setToolTip("Hide panel")
        self.toggle_btn.clicked.connect(self.toggle_output_dock)
        self.toggle_btn.setStyleSheet("""
            QPushButton       { background-color:#6c8408; color:white; font-size:12px;
                                font-weight:bold; padding:0px; border:none; }
            QPushButton:hover { background-color:#5e7407; }
        """)
        sl.addStretch()
        sl.addWidget(self.toggle_btn)
        sl.addStretch()
        self.main_layout.addWidget(self.toggle_strip)

    # ── Top bar ───────────────────────────────────────────────────────────────

    def _build_top_bar(self) -> QHBoxLayout:
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)
        top_bar.setContentsMargins(0, 0, 0, 15)

        title_btn = QPushButton("Output Dock")
        title_btn.setStyleSheet("""
            QPushButton { background-color:#90AF13; color:white; font-weight:bold;
                          font-size:13px; border:none; border-radius:4px; padding:7px 20px; }
        """)
        title_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        top_bar.addWidget(title_btn)
        top_bar.addStretch()
        return top_bar

    # ── Scroll area ───────────────────────────────────────────────────────────

    def _build_scroll_area(self) -> QScrollArea:
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scroll_area.setStyleSheet("""
            QScrollArea { background:transparent; padding:0px 5px;
                          border-top:1px solid #909090; border-bottom:1px solid #909090; }
            QScrollArea QScrollBar:vertical { border:none; background:#f0f0f0; width:8px; }
            QScrollArea QScrollBar::handle:vertical { background:#c0c0c0; border-radius:4px; min-height:20px; }
            QScrollArea QScrollBar::handle:vertical:hover { background:#a0a0a0; }
            QScrollArea QScrollBar::add-line:vertical,
            QScrollArea QScrollBar::sub-line:vertical { border:none; background:none; }
        """)

        self.output_widget = QWidget()
        root_layout = QVBoxLayout(self.output_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(12)

        self._build_field_loop(root_layout)

        root_layout.addStretch()
        self.scroll_area.setWidget(self.output_widget)
        return self.scroll_area

    # ── Bottom buttons ────────────────────────────────────────────────────────

    def _build_bottom_buttons(self) -> QHBoxLayout:
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 15, 0, 0)
        btn_layout.setSpacing(10)

        results_btn = DockCustomButton("Generate Results Table", ":/vectors/design_report.svg")
        results_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn_layout.addWidget(results_btn)

        report_btn = DockCustomButton("Generate Report", ":/vectors/design_report.svg")
        report_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn_layout.addWidget(report_btn)

        return btn_layout

    # ── Main build loop ───────────────────────────────────────────────────────

    def _build_field_loop(self, root_layout: QVBoxLayout):
        """
        Single flat loop — mirrors InputDock._build_field_loop exactly.
        TYPE_TITLE opens a group (analysis or design).
        Every field after it belongs to that group until the next TYPE_TITLE.

        Inside analysis groups, group_title opens a nested bordered subgroup;
        group_end closes it after that field.
        """
        field_list = []
        if self.backend and hasattr(self.backend, "output_values"):
            try:
                field_list = self.backend.output_values() or []
            except Exception:
                pass

        track        = False
        group        = None
        glayout      = None
        # nested subgroup state
        subgroup     = None
        sub_layout   = None

        def close_group():
            nonlocal track, group, glayout, subgroup, sub_layout
            if track and group:
                group.setLayout(glayout)
                track = False
            subgroup   = None
            sub_layout = None

        for defn in field_list:
            if len(defn) < 7:
                continue
            key, label, ftype, values, is_visible, _, meta = defn
            meta = meta or {}

            if not is_visible:
                continue

            # ── Section boundary ───────────────────────────────────────────
            if ftype == TYPE_TITLE:
                close_group()
                kind  = meta.get("kind", "design")
                group, glayout = self._open_group(label, kind)
                root_layout.addWidget(group)
                track = True
                continue

            if not track:
                continue

            # ── Open nested subgroup if group_title declared ───────────────
            if meta.get("group_title"):
                subgroup   = QGroupBox(meta["group_title"])
                subgroup.setStyleSheet(SUBGROUP_STYLE)
                sub_layout = QVBoxLayout()
                sub_layout.setContentsMargins(8, 8, 8, 8)
                sub_layout.setSpacing(6)
                subgroup.setLayout(sub_layout)
                glayout.addWidget(subgroup)

            # Route to subgroup if open, otherwise to section layout
            target = sub_layout if subgroup is not None else glayout

            # ── Field dispatch ─────────────────────────────────────────────
            if ftype == TYPE_BUTTON:
                target.addLayout(self._make_button_row(label, meta))

            elif ftype == TYPE_COMBOBOX:
                target.addLayout(self._make_combobox_row(key, label, values, meta))

            elif ftype == TYPE_CHECKBOX_GRID:
                target.addLayout(self._make_checkbox_grid(key, label, values, meta))

            elif ftype == TYPE_CHECKBOX_ROW:
                target.addLayout(self._make_checkbox_row(key, label, values, meta))

            elif ftype == TYPE_CHECKBOX:
                cb = QCheckBox(label or "")
                cb.setObjectName(key)
                target.addWidget(cb)

            # ── Close nested subgroup if group_end declared ────────────────
            if meta.get("group_end"):
                subgroup   = None
                sub_layout = None

        close_group()

    # ── Group factories ───────────────────────────────────────────────────────

    def _open_group(self, title: str, kind: str) -> tuple[QWidget, QVBoxLayout]:
        if kind == "analysis":
            return self._make_analysis_shell(title)
        return self._make_design_shell(title)

    def _make_analysis_shell(self, title: str) -> tuple[QGroupBox, QVBoxLayout]:
        """Plain QGroupBox — same style as InputDock section groups."""
        group = QGroupBox(title)
        group.setStyleSheet(GROUPBOX_STYLE)
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        return group, layout

    def _make_design_shell(self, title: str) -> tuple[QWidget, QVBoxLayout]:
        """Collapsible group — mirrors InputDock._make_container."""
        outer = QGroupBox()
        outer.setStyleSheet(
            "QGroupBox { border:1px solid #90AF13; border-radius:5px;"
            " margin-top:0px; padding-top:5px; background-color:white; }"
        )
        ol = QVBoxLayout()
        ol.setContentsMargins(10, 10, 10, 10)
        ol.setSpacing(10)

        header = QHBoxLayout()
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size:13px; font-weight:bold; color:#333;")
        header.addWidget(title_lbl)
        header.addStretch()

        toggle = QPushButton()
        toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        toggle.setCheckable(True)
        toggle.setChecked(True)
        toggle.setIcon(QIcon(":/vectors/arrow_up_light.svg"))
        toggle.setIconSize(QSize(20, 20))
        toggle.setStyleSheet(
            "QPushButton { background:transparent; border:none; padding:2px; }"
            "QPushButton:hover, QPushButton:pressed { background:transparent; }"
        )
        header.addWidget(toggle)
        ol.addLayout(header)

        body = QFrame()
        body.setFrameShape(QFrame.NoFrame)
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(8)
        ol.addWidget(body)

        toggle.toggled.connect(lambda checked: (
            body.setVisible(checked),
            toggle.setIcon(QIcon(
                ":/vectors/arrow_up_light.svg" if checked
                else ":/vectors/arrow_down_light.svg"
            )),
        ))

        outer.setLayout(ol)
        return outer, body_layout

    # ── Widget factories ──────────────────────────────────────────────────────

    def _make_button_row(self, label: str, meta: dict) -> QHBoxLayout:
        """[Label | Action Button] — mirrors InputDock._make_button_row."""
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        lbl = QLabel(label)
        lbl.setStyleSheet(LABEL_STYLE)
        lbl.setMinimumWidth(110)
        row.addWidget(lbl)

        btn = QPushButton(meta.get("button_label", "Here"))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn.setStyleSheet(ACTION_BTN_STYLE)
        cb = getattr(self, meta.get("action", ""), None)
        if callable(cb):
            btn.clicked.connect(cb)
        else:
            btn.setEnabled(False)
        row.addWidget(btn, 1)
        return row

    def _make_combobox_row(self, key: str, label: str, values, meta: dict) -> QHBoxLayout:
        """[Label | Dropdown] row."""
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        lbl = QLabel(label)
        lbl.setStyleSheet(LABEL_STYLE)
        lbl.setMinimumWidth(110)
        row.addWidget(lbl)

        combo = NoScrollComboBox()
        combo.setObjectName(key)
        items = list(values or [])
        combo.addItems(items)
        default = meta.get("default")
        if default and str(default) in items:
            combo.setCurrentText(str(default))
        apply_field_style(combo)
        row.addWidget(combo, 1)
        return row

    def _make_checkbox_grid(self, key: str, label: str, values, meta: dict) -> QVBoxLayout:
        """
        N-column grid of checkboxes, aligned in rows using QGridLayout.
        values    = [["Fx","Mx","Dx"], ["Fy","My","Dy"], ...]
        label     = None means no label row is added.
        exclusive : bool — if True only one checkbox can be checked at a time.
        """
        from PySide6.QtWidgets import QGridLayout

        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(4)

        if label:
            lbl = QLabel(label)
            lbl.setStyleSheet(LABEL_STYLE)
            outer.addWidget(lbl)

        columns  = values if isinstance(values, list) else []
        all_cbs: list[QCheckBox] = []
        num_cols = len(columns)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(4)

        # Set equal stretch on every column so they fill the width evenly
        for c in range(num_cols):
            grid.setColumnStretch(c, 1)

        # Fill row by row: row index = position within column
        num_rows = max((len(col) for col in columns), default=0)
        for row in range(num_rows):
            for col, col_items in enumerate(columns):
                if row < len(col_items):
                    cb = QCheckBox(str(col_items[row]))
                    all_cbs.append(cb)
                    grid.addWidget(cb, row, col, alignment=Qt.AlignCenter)

        outer.addLayout(grid)

        if meta.get("exclusive", False):
            self._wire_exclusive(all_cbs)

        return outer

    def _make_checkbox_row(self, key: str, label: str, values, meta: dict) -> QHBoxLayout:
        """
        Horizontal row of checkboxes.
        values    = ["Max", "Min", ...]
        exclusive : bool — if True only one checkbox can be checked at a time.
        """
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)

        if label:
            lbl = QLabel(label)
            lbl.setStyleSheet(LABEL_STYLE)
            lbl.setMinimumWidth(110)
            row.addWidget(lbl)

        options = list(values or [])
        cbs: list[QCheckBox] = []
        for text in options:
            cb = QCheckBox(str(text))
            cbs.append(cb)
            row.addWidget(cb)

        row.addStretch()

        if meta.get("exclusive", False):
            self._wire_exclusive(cbs)

        return row

    # ── Exclusive checkbox wiring ─────────────────────────────────────────────

    @staticmethod
    def _wire_exclusive(checkboxes: list[QCheckBox]):
        """Make a group of checkboxes mutually exclusive (radio-button behaviour)."""
        def _on_clicked(checked, clicked_cb):
            if checked:
                for cb in checkboxes:
                    if cb is not clicked_cb:
                        cb.setChecked(False)
        for box in checkboxes:
            box.clicked.connect(lambda checked, b=box: _on_clicked(checked, b))

    # ── Widget lookup ─────────────────────────────────────────────────────────

    def _w(self, key) -> QWidget | None:
        return self.output_widget.findChild(QWidget, key) if self.output_widget else None

    # ── Panel toggle ──────────────────────────────────────────────────────────

    def toggle_output_dock(self):
        if hasattr(self.parent, "toggle_animate"):
            collapsing = self.width() > 0
            self.parent.toggle_animate(show=not collapsing, dock="output")
            self.toggle_btn.setText("❮" if collapsing else "❯")
            self.toggle_btn.setToolTip("Show panel" if collapsing else "Hide panel")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.parent and hasattr(self.parent, "update_docking_icons"):
            self.parent.update_docking_icons(output_is_active=self.width() > 0)

    # ── Action handlers (called by name from schema) ──────────────────────────

    def open_steel_design(self):
        from osdagbridge.desktop.ui.dialogs.steel_design import SteelDesign
        SteelDesign(parent=self.parent).exec()

    def open_deck_design(self):
        from osdagbridge.desktop.ui.dialogs.deck_design import DeckDesign
        DeckDesign(parent=self.parent).exec()