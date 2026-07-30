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
import os
import logging

logger = logging.getLogger(__name__)

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy,
    QPushButton, QGroupBox, QCheckBox, QScrollArea, QFrame, QComboBox,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

from osdagbridge.core.utils.common import (
    TYPE_TITLE, TYPE_BUTTON, TYPE_COMBOBOX, TYPE_PERCENT_BAR, TYPE_RADIO_GRID,
    TYPE_CHECKBOX, TYPE_CHECKBOX_ROW, TYPE_CHECKBOX_GRID, TYPE_ONLY_BUTTON,
    KEY_UTIL_FLEXURE, KEY_UTIL_SHEAR, KEY_UTIL_INTERACTION, KEY_UTIL_LTB,
    KEY_UTIL_LONG_TRANS_SHEAR, KEY_UTIL_FATIGUE, KEY_UTIL_STRESS_LIMITATION,
    KEY_UTIL_DEFLECTION_CRACK, KEY_ANALYSIS_LOAD_COMBINATION,
    KEY_OUTPUT_DOCK_MEMBER_ID, KEY_OUTPUT_DOCK_LOAD_COMBINATION,
    KEY_TS_NO_OF_GIRDERS,
)
from osdagbridge.desktop.ui.utils.custom_buttons import DockCustomButton
from osdagbridge.desktop.ui.docks.dock_utils import apply_field_style
from osdagbridge.desktop.ui.utils.custom_widgets import RichCheckBox, PercentBarWidget, CustomRadioButton
from osdagbridge.desktop.ui.dialogs.generate_results_dialog import GenerateResultsDialog
from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox, MessageBoxType
from osdagbridge.desktop.ui.utils.custom_cursors import pointing_hand_cursor
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
        self.toggle_btn.setCursor(pointing_hand_cursor())
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

        results_btn = DockCustomButton("Generate Results Table", ":/vectors/design_result_table.svg")
        results_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        results_btn.clicked.connect(self.open_generate_results_dialog)
        btn_layout.addWidget(results_btn)

        self.report_btn = DockCustomButton("Generate Report", ":/vectors/design_report.svg")
        self.report_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.report_btn.clicked.connect(self._on_report_clicked)
        btn_layout.addWidget(self.report_btn)

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

            elif ftype == TYPE_RADIO_GRID:
                target.addLayout(self._make_radio_grid(key, label, values, meta))

            elif ftype == TYPE_CHECKBOX_ROW:
                target.addLayout(self._make_checkbox_row(key, label, values, meta))

            elif ftype == TYPE_CHECKBOX:
                cb = QCheckBox(label or "")
                cb.setObjectName(key)
                target.addWidget(cb)
            
            elif ftype == TYPE_PERCENT_BAR:
                bar = PercentBarWidget(label=label or "", value=0.0)
                bar.setObjectName(key)
                target.addWidget(bar)
            
            elif ftype == TYPE_ONLY_BUTTON:
                target.addLayout(self._make_only_button_row(label, meta))

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
        toggle.setCursor(pointing_hand_cursor())
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
        btn.setCursor(pointing_hand_cursor())
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn.setStyleSheet(ACTION_BTN_STYLE)
        cb = getattr(self, meta.get("action", ""), None)
        if callable(cb):
            btn.clicked.connect(cb)
        else:
            btn.setEnabled(False)
        row.addWidget(btn, 1)
        return row

    def _make_only_button_row(self, label: str, meta: dict) -> QHBoxLayout:
        """Single button with no label."""
        row = QHBoxLayout()
        row.setContentsMargins(0, 8, 0, 0)
        row.setSpacing(8)

        btn = QPushButton(label)
        btn.setCursor(pointing_hand_cursor())
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
        all_cbs: list[RichCheckBox] = []
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
                    cb = RichCheckBox(str(col_items[row]))
                    all_cbs.append(cb)
                    grid.addWidget(cb, row, col, alignment=Qt.AlignCenter)

        outer.addLayout(grid)

        if meta.get("exclusive", False):
            self._wire_exclusive(all_cbs)

        return outer

    def _make_radio_grid(self, key: str, label: str, values, meta: dict):
        """
        N-column grid of CustomRadioButtons, aligned in rows using QGridLayout.
    
        values    = [["Fx","Mx","Dx"], ["Fy","My","Dy"], ...]   (column-first list)
        label     = section label string, or None to skip the label row.
        exclusive : bool (in meta) — when True, selecting one button unchecks all
                    others in the grid (standard radio behaviour).  Defaults True.
        """
        from PySide6.QtWidgets import QVBoxLayout, QGridLayout, QLabel
    
        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(4)
    
        if label:
            lbl = QLabel(label)
            lbl.setStyleSheet(LABEL_STYLE)
            outer.addWidget(lbl)
    
        columns  = values if isinstance(values, list) else []
        all_rbs: list[CustomRadioButton] = []
        num_cols = len(columns)
    
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(4)
    
        for c in range(num_cols):
            grid.setColumnStretch(c, 1)
    
        num_rows = max((len(col) for col in columns), default=0)
        for row in range(num_rows):
            for col, col_items in enumerate(columns):
                if row < len(col_items):
                    rb = CustomRadioButton(str(col_items[row]))
                    all_rbs.append(rb)
                    grid.addWidget(rb, row, col, alignment=Qt.AlignCenter)
    
        outer.addLayout(grid)    
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

    def _require_design(self) -> bool:
        """Return True if a design result is available; show an error and return False otherwise."""
        input_dock = getattr(self.parent, "input_dock", None)
        if input_dock is None or not input_dock.is_locked:
            CustomMessageBox(
                title="Run Design",
                text="Please run the design first.",
                dialogType=MessageBoxType.Warning,
            ).exec()
            return False
        return True

    def _on_report_clicked(self):
        """
        Resolve Qt-side objects then delegate entirely to
        template_page.open_report_dialog(). OutputDock owns
        no report logic — it captures CAD figures on the main
        thread (Qt-safe) and passes paths to the report worker.
        """
        if not self._require_design():
            return
        import os

        # Find cad_3d_widget
        cad_3d_widget = None
        main_window = self.parent
        while main_window and not hasattr(main_window, 'cad_3d_widget'):
            main_window = getattr(main_window, 'parent', None)
        if main_window and hasattr(main_window, 'cad_3d_widget'):
            cad_3d_widget = main_window.cad_3d_widget

        # Capture figures on the main thread — bytes only, nothing written to disk
        cad_generator = None
        if cad_3d_widget is not None:
            # 3D views: OCC → NamedTemporaryFile → bytes → temp file deleted
            try:
                figure_data = cad_3d_widget.capture_for_report()
            except Exception as exc:
                logger.warning("Could not capture CAD figures: %s", exc)
                figure_data = {}

            # Figure 6.1.3 — Top View: generated by TopViewCADWidget.render_to_bytes()
            # (the widget's own drawing code), not a live-screen grab. A fresh
            # widget is fed the live bridge params, then renders itself off-screen.
            try:
                from osdagbridge.desktop.ui.docks.cad_top_view import TopViewCADWidget
                cad_comp = getattr(main_window, 'cad_comp_widget', None)
                top_view = getattr(cad_comp, 'top_view_widget', None)
                if top_view is not None:
                    tmp = TopViewCADWidget()
                    tmp.params.update(top_view.params)      # same bridge as live
                    tmp.girder = dict(top_view.girder)
                    tmp.stiffener = dict(top_view.stiffener)
                    figure_data['girder_top'] = tmp.render_to_bytes()
                    tmp.deleteLater()
            except Exception as exc:
                logger.warning("Could not capture top view: %s", exc)

            # Figure 6.2.2 — Cross Section of Plate Girder: RolledSectionPreview off-screen
            try:
                from PySide6.QtCore import QBuffer, QIODevice
                from osdagbridge.desktop.ui.dialogs.additional_input.drawings.rolled_section_preview import RolledSectionPreview
                _out = dict(getattr(self.backend, 'output_dict', {}) or {})
                def _f(v):
                    try: return float(v)
                    except: return None
                _d   = _f(_out.get('steeldesign.details.total_depth'))    or 0.0
                _tfw = _f(_out.get('steeldesign.details.top_flange_width'))    or 0.0
                _tft = _f(_out.get('steeldesign.details.top_flange_thickness')) or 0.0
                _bfw = _f(_out.get('steeldesign.details.bottom_flange_width'))  or _tfw
                _bft = _f(_out.get('steeldesign.details.bottom_flange_thickness')) or _tft
                _wt  = _f(_out.get('steeldesign.details.web_thickness'))   or 0.0
                _st  = str(_out.get('steeldesign.details.section_type', '')).lower()
                if _d and _tfw and _tft and _wt:
                    _w = RolledSectionPreview()
                    _w.resize(700, 500)
                    _w.set_dimensions(depth_mm=_d, flange_width_mm=_tfw, bottom_flange_width_mm=_bfw,
                                      web_thickness_mm=_wt, flange_thickness_mm=_tft,
                                      bottom_flange_thickness_mm=_bft, show_welds=(_st == 'welded'))
                    _buf = QBuffer()
                    _buf.open(QIODevice.WriteOnly)
                    _w.grab().save(_buf, 'PNG')
                    figure_data['section_preview'] = bytes(_buf.data())
                    _buf.close()
            except Exception as exc:
                logger.warning("Could not capture girder cross section: %s", exc)

            # Figure 6.2.3 — Side View of Girder: StiffenerCadPreviewWidget off-screen
            try:
                from PySide6.QtCore import QBuffer, QIODevice
                from osdagbridge.desktop.ui.dialogs.additional_input.drawings.stiffener_cad_preview import StiffenerCadPreviewWidget
                _gen = getattr(cad_3d_widget, 'generator', None)
                _out = getattr(_gen, 'output_dict', {}) if _gen else {}
                _depth = _f(_out.get('steeldesign.details.total_depth')) or 0.0
                _tf_t  = _f(_out.get('steeldesign.details.top_flange_thickness')) or 0.0
                _bf_t  = _f(_out.get('steeldesign.details.bottom_flange_thickness')) or 0.0
                try: _length_m = float(_out.get('geometry.length') or 30.0)
                except: _length_m = 30.0
                _segments = [{'id': 'G1M1', 'start': 0.0, 'end': _length_m, 'length': _length_m}]
                _stiff = {
                    'bearing_stiffeners_each_end': str(_out.get('bearing_stiffeners_each_end', '2')),
                    'bearing_spacing_mm':          str(_out.get('bearing_spacing_mm', '')),
                    'intermediate_stiffener':      str(_out.get('intermediate_stiffener', 'No')),
                    'intermediate_spacing_mm':     str(_out.get('intermediate_spacing_mm', 'NA')),
                    'longitudinal_stiffener':      str(_out.get('longitudinal_stiffener', 'No')),
                }
                _dims = {'G1M1': {'depth_mm': _depth, 'top_flange_thickness_mm': _tf_t, 'bottom_flange_thickness_mm': _bf_t}}
                _w = StiffenerCadPreviewWidget()
                _w.resize(700, 300)
                _w.set_data(segments=_segments, stiffener_by_member={'G1M1': _stiff},
                            active_member_id='G1M1', section_dims_by_member=_dims)
                _buf = QBuffer()
                _buf.open(QIODevice.WriteOnly)
                _w.grab().save(_buf, 'PNG')
                figure_data['stiffener_preview'] = bytes(_buf.data())
                _buf.close()
            except Exception as exc:
                logger.warning("Could not capture stiffener preview: %s", exc)

            # Section 6.3 — Cross Bracing Detail: 4 pictures from the crossbracing
            # tab. The dialog's __init__ auto-loads data from the backend and
            # populates these widgets; we just resize + grab each, same as above.
            try:
                from PySide6.QtCore import QBuffer, QIODevice
                from osdagbridge.desktop.ui.dialogs.transverse_member_design import TransverseMemberDesign
                _tmd = TransverseMemberDesign(parent=self.parent)   # auto-loads + populates widgets
                def _grab_cb(_widget, _key, _wpx, _hpx):
                    if _widget is None:
                        return
                    try:
                        _widget.resize(_wpx, _hpx)
                        _b = QBuffer()
                        _b.open(QIODevice.WriteOnly)
                        _widget.grab().save(_b, 'PNG')
                        figure_data[_key] = bytes(_b.data())
                        _b.close()
                    except Exception as exc:
                        logger.warning("Could not capture %s: %s", _key, exc)
                _grab_cb(_tmd._tab_bracing_widgets.get('cb'),        'cb_diagram',      700, 250)  # cross bracing layout
                _grab_cb(_tmd._section_previews.get('Bracing'),      'cb_bracing',      300, 300)  # bracing section
                _grab_cb(_tmd._section_previews.get('Top Chord'),    'cb_top_chord',    300, 300)  # top chord section
                _grab_cb(_tmd._section_previews.get('Bottom Chord'), 'cb_bottom_chord', 300, 300)  # bottom chord section

                # Section 6.4 — End Diaphragm Detail: same 4 pictures from the ED tab.
                # The ED bracing diagram only fills when the ED tab is current, so
                # switch to it and refresh before grabbing.
                try:
                    _tmd.tabs.setCurrentIndex(1)
                    _tmd._refresh_bracing_layout()
                except Exception as exc:
                    logger.warning("Could not activate ED tab: %s", exc)
                _grab_cb(_tmd._tab_bracing_widgets.get('ed'),           'ed_diagram',      700, 250)  # end diaphragm layout
                _grab_cb(_tmd._section_previews.get('ed_End Diaphragm'),'ed_bracing',      300, 300)  # bracing section
                _grab_cb(_tmd._section_previews.get('ed_Top Chord'),    'ed_top_chord',    300, 300)  # top chord section
                _grab_cb(_tmd._section_previews.get('ed_Bottom Chord'), 'ed_bottom_chord', 300, 300)  # bottom chord section
                _tmd.deleteLater()
            except Exception as exc:
                logger.warning("Could not capture cross bracing / end diaphragm figures: %s", exc)

            # Analysis envelope plot: live plot widget → temp PNG → bytes → deleted.
            # Switch the central area to the plots view first (like the CAD does) so
            # the widget is visible and renders the right condition before capture.
            try:
                plots_widget = getattr(main_window, 'plots_widget', None)
                if plots_widget is not None and getattr(plots_widget, '_ds_all', None) is not None:
                    from osdagbridge.core.bridge_types.plate_girder.plot_generator import (
                        capture_report_figures,
                    )
                    figure_data.update(capture_report_figures(
                        plots_widget._ds_all, plots_widget._nodes, plots_widget._members,
                        edge_dist=plots_widget._edge_dist, eng_scale=plots_widget._eng_scale,
                    ))
            except Exception as exc:
                logger.warning("Could not capture envelope plot: %s", exc)

            cad_generator = {
                'generator':   getattr(cad_3d_widget, 'generator', None),
                'figure_data': figure_data,
            }
            # figure_data local var goes out of scope here; cad_generator holds the only ref

        # Find dialog host and trigger
        main_window = self.parent
        while main_window and not hasattr(main_window, 'open_report_dialog'):
            main_window = getattr(main_window, 'parent', None)
        if main_window and hasattr(main_window, 'open_report_dialog'):
            main_window.open_report_dialog(cad_generator=cad_generator)


    def reset(self):
        """Reset output dock to blank defaults when the lock is released."""
        dcr_keys = (
            KEY_UTIL_FLEXURE, KEY_UTIL_SHEAR, KEY_UTIL_INTERACTION, KEY_UTIL_LTB,
            KEY_UTIL_LONG_TRANS_SHEAR, KEY_UTIL_FATIGUE, KEY_UTIL_STRESS_LIMITATION,
            KEY_UTIL_DEFLECTION_CRACK,
        )
        for key in dcr_keys:
            bar = self._w(key)
            if bar is not None:
                bar.setVisible(True)
                bar.set_value(0.0)

        for key in (KEY_ANALYSIS_LOAD_COMBINATION, KEY_OUTPUT_DOCK_LOAD_COMBINATION,
                    KEY_OUTPUT_DOCK_MEMBER_ID):
            combo = self._w(key)
            if combo is not None:
                combo.blockSignals(True)
                combo.clear()
                combo.blockSignals(False)

    def refresh_loadcase_dropdowns(self):
        """Populate both Load Case dropdowns with real load cases after design completes."""
        if not self.backend or not hasattr(self.backend, "get_available_loadcases"):
            return
        loadcases = [
            lc for lc in self.backend.get_available_loadcases()
            if " at global position " not in lc.lower()
        ]
        for key in (KEY_ANALYSIS_LOAD_COMBINATION, KEY_OUTPUT_DOCK_LOAD_COMBINATION):
            combo = self._w(key)
            if combo is not None:
                combo.blockSignals(True)
                combo.clear()
                combo.addItems(loadcases)
                # "Design Envelope" is a UI-only pseudo load case — worst utilization
                # per check across the load cases that affect it. It drives the DCR
                # bars only, so it goes in the design dropdown, not the analysis one
                # (which plots real dataset load cases).
                if key == KEY_OUTPUT_DOCK_LOAD_COMBINATION:
                    combo.addItem("Design Envelope")
                    combo.setCurrentText("Design Envelope")  # default for design dropdown
                else:
                    combo.setCurrentIndex(0)  # first real load case is default
                combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
                combo.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
                combo.blockSignals(False)

    def refresh_member_dropdown(self):
        """Populate the Girder Design Member dropdown after design completes."""
        if not self.backend or not hasattr(self.backend, "input_dict"):
            return
        combo = self._w(KEY_OUTPUT_DOCK_MEMBER_ID)
        if combo is None:
            return

        n_girders = int(self.backend.input_dict.get(KEY_TS_NO_OF_GIRDERS, 1))

        # Currently 1 member per girder (M1 only).
        # When multiple members per girder are introduced, extend the
        # members_per_girder list below, e.g. [1, 2, 3], and the items
        # will automatically expand to G1M1, G1M2, ..., GnM3.
        members_per_girder = [1]

        if len(members_per_girder) == 1:
            # Simple case: one member per girder — just show G1, G2, ..., Gn
            items = [f"G{g}" for g in range(1, n_girders + 1)]
        else:
            # Multiple members per girder — show GnMm entries
            items = [
                f"G{g}M{m}"
                for g in range(1, n_girders + 1)
                for m in members_per_girder
            ]

        # 1. Update Design Girder dropdown
        combo_design = self._w(KEY_OUTPUT_DOCK_MEMBER_ID)
        if combo_design is not None:
            combo_design.blockSignals(True)
            combo_design.clear()
            combo_design.addItems(items)
            combo_design.setCurrentIndex(0)
            combo_design.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
            combo_design.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            combo_design.blockSignals(False)

        # 2. Update Analysis Member dropdown
        from osdagbridge.core.utils.common import KEY_ANALYSIS_MEMBER
        combo_analysis = self._w(KEY_ANALYSIS_MEMBER)
        if combo_analysis is not None:
            combo_analysis.blockSignals(True)
            combo_analysis.clear()
            combo_analysis.addItems(["All"] + items)
            combo_analysis.setCurrentIndex(0)
            combo_analysis.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
            combo_analysis.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
            combo_analysis.blockSignals(False)
   
    def connect_design_dropdowns(self):
        """Connect Member and Load Case dropdowns to refresh DCR bars on change."""
        for key in (KEY_OUTPUT_DOCK_MEMBER_ID, KEY_OUTPUT_DOCK_LOAD_COMBINATION):
            combo = self._w(key)
            if combo is not None:
                combo.currentTextChanged.connect(self._on_design_selection_changed)

    def _on_design_selection_changed(self):
        """Called when either the Member or Load Case dropdown changes."""
        if not self.backend or not hasattr(self.backend, "get_dcr_for_selection"):
            return
        member_combo = self._w(KEY_OUTPUT_DOCK_MEMBER_ID)
        lc_combo     = self._w(KEY_OUTPUT_DOCK_LOAD_COMBINATION)
        girder_name  = member_combo.currentText() if member_combo else "All"
        load_case    = lc_combo.currentText()     if lc_combo     else "Envelope"

        dcr_values = self.backend.get_dcr_for_selection(girder_name, load_case)
        if not dcr_values:
            return

        for key, value in dcr_values.items():
            bar = self._w(key)
            if bar is None:
                continue
            if value is None:
                bar.setVisible(False)
            else:
                bar.setVisible(True)
                bar.set_value(float(value))

    def open_steel_design(self):
        if not self._require_design():
            return
        from osdagbridge.desktop.ui.dialogs.steel_design import SteelDesign
        SteelDesign(parent=self.parent).exec()

    def open_transverse_design(self):
        if not self._require_design():
            return
        from osdagbridge.desktop.ui.dialogs.transverse_member_design import TransverseMemberDesign
        TransverseMemberDesign(parent=self.parent).exec()

    def open_deck_design(self):
        if not self._require_design():
            return
        from osdagbridge.desktop.ui.dialogs.deck_design import DeckDesign
        DeckDesign(parent=self.parent).exec()

    # ── Checkbox Interfaces ──────────────────────────────────────────────

    def get_checkbox_state(self, label: str) -> bool:
        """Returns True if the checkbox with the exact label is checked."""
        for cb in self.output_widget.findChildren(QCheckBox):
            if cb.text() == label:
                return cb.isChecked()
        return False

    def connect_checkbox_signal(self, label: str, callback):
        """Connects a callback function to a checkbox toggle event."""
        for cb in self.output_widget.findChildren(QCheckBox):
            if cb.text() == label:
                # Use a lambda to absorb the boolean argument and call the callback
                cb.toggled.connect(lambda _: callback())

    def open_generate_results_dialog(self):
        if not self._require_design():
            return

        input_dict   = getattr(self.parent, "input_dict", {})
        input_d_values = getattr(self.parent.input_dock, "input_dock_values", {})

        ai_dlg  = getattr(self.parent, '_additional_inputs_dialog', None)
        ai_dict = getattr(ai_dlg, 'working_input_dict', {}) if ai_dlg else {}
        out_dict = dict(getattr(self.backend, 'output_dict', {}) or {})

        merged = {**input_dict, **ai_dict, **input_d_values, **out_dict}
        dlg = GenerateResultsDialog(parent=None, input_dict=merged, bridge = self.backend)
        dlg.exec()




