"""
Input dock widget for Highway Bridge Design GUI.

Design principles:
  - No named widget references — all widgets found via _w(key) / findChild(QWidget, key).
  - Label comes only from tuple[1]. No metadata["label"] duplication.
  - Defaults live in input_values() metadata["default"]. No prime_defaults needed.
  - TYPE_BUTTON and TYPE_NOTE are first-class field rows, not hidden in TYPE_TITLE metadata.
  - One flat loop: TYPE_TITLE opens a group; COMBOBOX/TEXTBOX/BUTTON/NOTE add rows.
  - Zero key-specific logic in InputDock — all per-field behaviour is driven by
    the ui_config_dict declared in frontend_data.input_values().
"""

import json
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QComboBox, QScrollArea, QLabel, QLineEdit, QGroupBox, QSizePolicy,
    QDialog, QFrame, QToolButton,
)
from PySide6.QtCore import Qt, QRegularExpression, QSize, QTimer, QPoint, QEvent, Signal
from PySide6.QtGui import QDoubleValidator, QRegularExpressionValidator, QIcon, QColor, QBrush

from osdagbridge.core.utils.common import *
from osdagbridge.desktop.ui.dialogs.additional_inputs import AdditionalInputs
from osdagbridge.desktop.ui.utils.custom_buttons import DockCustomButton
from osdagbridge.desktop.ui.dialogs.project_location import ProjectLocationDialog
from osdagbridge.desktop.ui.docks.dock_utils import apply_field_style
from osdagbridge.desktop.ui.dialogs.material_properties import (
    MaterialPropertiesDialog, sync_custom_materials_across_steel_members,
)
from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox, MessageBoxType
from osdagbridge.core.bridge_types.plate_girder.defaults import DEFAULTS_DICT


MATERIAL_CUSTOM_OPTION = "Custom"

GROUPBOX_STYLE = (
    "QGroupBox { border:1px solid #90AF13; border-radius:4px; background-color:white;"
    "  padding:8px; margin-top:12px; font-size:10px; font-weight:bold; color:#333; }"
    "QGroupBox::title { subcontrol-origin:margin; subcontrol-position:top left;"
    "  left:8px; padding:0 4px; margin-top:4px; background-color:white; color:#333; }"
)
ACTION_BTN_STYLE = (
    "QPushButton { background-color:#90AF13; color:white; font-weight:bold; border:none;"
    "  border-radius:4px; padding:8px 20px; font-size:11px; min-width:80px; }"
    "QPushButton:hover { background-color:#7a9a12; }"
    "QPushButton:disabled { background:#D0D0D0; color:#666; }"
)
LABEL_STYLE = "QLabel { color:#000; font-size:12px; background:transparent; }"


class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()


class InputDock(QWidget):
    input_value_changed = Signal()

    def __init__(self, backend, parent):
        super().__init__()
        self.parent  = parent
        self.backend = backend

        self.is_locked            = False
        self._current_design_mode = "Optimized"
        self.additional_inputs    = None
        self.additional_input_values       = {}
        self._additional_inputs_saved_data = {}
        self._material_combo_map           = {}   # key → QComboBox  (is_material_field only)
        self._material_member_type         = {}   # key → "Girder"|"Deck"
        self._material_custom_fields       = {}
        self._material_previous_selection  = {}
        # key → list of (widget_ref, placeholder_method_name) for dynamic placeholders
        self._dynamic_placeholder_map: dict[str, tuple[QLineEdit, str]] = {}

        self._basic_inputs_saved_list:      list[dict] = []
        self._additional_inputs_saved_list: list[dict] = []

        self.setStyleSheet("background: transparent;")
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.left_container = QWidget()
        self.build_left_panel(self.backend.input_values())
        self.main_layout.addWidget(self.left_container)
        self._build_toggle_strip()

    # ── Widget lookup ─────────────────────────────────────────────────────────

    def _w(self, key) -> QWidget | None:
        return self.input_widget.findChild(QWidget, key) if self.input_widget else None

    def _text(self, key) -> str:
        w = self._w(key)
        if isinstance(w, QLineEdit):  return w.text().strip()
        if isinstance(w, QComboBox):  return w.currentText()
        return ""

    def _float(self, key, fallback=None):
        try:    return float(self._text(key))
        except: return fallback

    # ── Panel construction ────────────────────────────────────────────────────

    def build_left_panel(self, field_list):
        left_layout = QVBoxLayout(self.left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.left_panel = QWidget()
        self.left_panel.setStyleSheet("background-color: white;")
        panel_layout = QVBoxLayout(self.left_panel)
        panel_layout.setContentsMargins(15, 10, 15, 10)
        panel_layout.setSpacing(0)

        panel_layout.addLayout(self._build_top_bar())
        panel_layout.addWidget(self._build_scroll_area(field_list))
        panel_layout.addLayout(self._build_bottom_buttons())

        h_scroll = QScrollArea()
        h_scroll.setWidgetResizable(True)
        h_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        h_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        h_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        h_scroll.setStyleSheet("""
            QScrollArea { background:transparent; }
            QScrollBar:horizontal { background:#E0E0E0; height:8px; border-radius:2px; }
            QScrollBar::handle:horizontal { background:#A0A0A0; min-width:30px; border-radius:2px; }
            QScrollBar::handle:horizontal:hover { background:#707070; }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width:0px; }
        """)
        h_scroll.setWidget(self.left_panel)
        left_layout.addWidget(h_scroll)
        self._apply_lock_state()

    def _build_top_bar(self) -> QHBoxLayout:
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)
        top_bar.setContentsMargins(0, 0, 0, 15)

        basic_btn = QPushButton("Basic Inputs")
        basic_btn.setStyleSheet("""
            QPushButton { background-color:#90AF13; color:white; font-weight:bold;
                          font-size:13px; border:none; border-radius:4px; padding:7px 20px; }
        """)
        basic_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        top_bar.addWidget(basic_btn)

        self.additional_inputs_btn = QPushButton("Additional Inputs")
        self.additional_inputs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.additional_inputs_btn.setStyleSheet("""
            QPushButton { background-color:white; color:black; font-weight:bold; font-size:13px;
                          border-radius:5px; border:1px solid black; padding:7px 20px; }
            QPushButton:hover  { background-color:#90AF13; border-color:#90AF13; color:white; }
            QPushButton:pressed { color:black; background-color:white; border:1px solid black; }
        """)
        self.additional_inputs_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.additional_inputs_btn.clicked.connect(self.show_additional_inputs)
        top_bar.addWidget(self.additional_inputs_btn)

        self.lock_btn = QPushButton()
        self.lock_btn.setStyleSheet("""
            QPushButton          { background-color:#f4f4f4; border:none; padding:7px; border-radius:4px; }
            QPushButton:hover    { background-color:#e0e0e0; }
            QPushButton:checked  { background-color:#FFA500; }
            QPushButton:checked:hover { background-color:#fa7a02; }
        """)
        self.lock_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lock_btn.setObjectName("lock_btn")
        self.lock_btn.setCheckable(True)
        self.lock_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.lock_btn.clicked.connect(self.toggle_lock)
        top_bar.addWidget(self.lock_btn)

        self.lock_btn_tooltip = QLabel("Unlock to Edit")
        self.lock_btn_tooltip.setStyleSheet("""
            QLabel { background-color:#f1f1f1; color:#000; border:1px solid #90AF13;
                     padding:4px; font-size:15px; border-radius:0px; }
        """)
        self.lock_btn_tooltip.setWindowFlags(Qt.ToolTip)
        self.lock_btn_tooltip.hide()
        return top_bar

    def _build_scroll_area(self, field_list) -> QScrollArea:
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scroll_area.installEventFilter(self)
        self.scroll_area.setStyleSheet("""
            QScrollArea { background:transparent; padding:0px 5px;
                          border-top:1px solid #909090; border-bottom:1px solid #909090; }
            QScrollArea QScrollBar:vertical { border:none; background:#f0f0f0; width:8px; }
            QScrollArea QScrollBar::handle:vertical { background:#c0c0c0; border-radius:4px; min-height:20px; }
            QScrollArea QScrollBar::handle:vertical:hover { background:#a0a0a0; }
            QScrollArea QScrollBar::add-line:vertical,
            QScrollArea QScrollBar::sub-line:vertical { border:none; background:none; }
        """)
        self.input_widget = QWidget()
        root_layout = QVBoxLayout(self.input_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(12)

        self._build_field_loop(field_list, root_layout)

        root_layout.addStretch()
        self.scroll_area.setWidget(self.input_widget)
        return self.scroll_area

    def _build_bottom_buttons(self) -> QHBoxLayout:
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 15, 0, 0)
        btn_layout.setSpacing(10)

        self.save_input_btn = DockCustomButton("Save Input", ":/vectors/save.svg")
        self.save_input_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.save_input_btn.clicked.connect(self._on_save_input_clicked)
        btn_layout.addWidget(self.save_input_btn)

        self.design_btn = DockCustomButton("Design", ":/vectors/design.svg")
        self.design_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.design_btn.clicked.connect(self._on_design_clicked)
        btn_layout.addWidget(self.design_btn)
        return btn_layout

    # ── Main build loop ───────────────────────────────────────────────────────

    def _build_field_loop(self, field_list, root_layout: QVBoxLayout):
        """
        Single flat loop — every TYPE is handled generically from ui_config_dict.
        No key-specific branches anywhere in this method.
        """
        container_layouts: dict[str, QVBoxLayout] = {}
        track   = False
        group   = None
        glayout = None

        def close_group():
            nonlocal track, group, glayout
            if track and group:
                group.setLayout(glayout)
                track = False

        def parent_for(meta) -> QVBoxLayout:
            c = (meta or {}).get("container", "main")
            if not c or c == "main":
                return root_layout
            if c not in container_layouts:
                container_layouts[c] = self._make_container(c, root_layout, meta)
            return container_layouts[c]

        for defn in field_list:
            key, label, ftype, values, _, validator, meta = (
                (*defn, {}) if len(defn) == 6 else defn
            )
            meta = meta or {}

            if ftype == TYPE_MODULE:
                continue

            if ftype == TYPE_TITLE:
                close_group()
                show_title = meta.get("show_group_title", True)
                group      = QGroupBox(label if show_title else "")
                group.setObjectName((key or label) + "_group")
                group.setStyleSheet(GROUPBOX_STYLE)
                glayout = QVBoxLayout()
                glayout.setContentsMargins(8, 8, 8, 8)
                glayout.setSpacing(8)
                track = True
                parent_for(meta).addWidget(group)
                continue

            if not track:
                continue

            if ftype == TYPE_COMBOBOX:
                glayout.addLayout(self._field_row(label, self._make_combobox(key, values, meta), meta))

            elif ftype == TYPE_TEXTBOX:
                glayout.addLayout(self._field_row(label, self._make_textbox(key, validator, meta), meta))

            elif ftype == TYPE_BUTTON:
                glayout.addLayout(self._make_button_row(label, meta))

            elif ftype == TYPE_NOTE:
                note = QLabel(label or "")
                note.setStyleSheet(LABEL_STYLE)
                note.setVisible(False)
                if meta.get("attr"):
                    setattr(self, meta["attr"], note)
                glayout.addWidget(note)

        close_group()

        # Post-loop: sync custom materials across all Girder-type material combos.
        sync_custom_materials_across_steel_members(self._material_combo_map, self._ensure_material_option)

        # Resolve all dynamic placeholders now that all widgets exist.
        self._refresh_all_dynamic_placeholders()

    # ── Widget factories ──────────────────────────────────────────────────────

    def _make_combobox(self, key, values, meta) -> NoScrollComboBox:
        widget = NoScrollComboBox()
        widget.setObjectName(key)
        apply_field_style(widget)

        if values:
            items = [str(v) for v in values]
            # Material fields: move Custom to end.
            if meta.get("is_material_field"):
                items = [i for i in items if i != MATERIAL_CUSTOM_OPTION] + [MATERIAL_CUSTOM_OPTION]
            widget.addItems(items)

            # Grey-out any options listed in disabled_options.
            disabled = set(meta.get("disabled_options") or [])
            for i, t in enumerate(items):
                if t in disabled:
                    item = widget.model().item(i) if hasattr(widget.model(), "item") else None
                    if item:
                        item.setEnabled(False)
                    widget.setItemData(i, QBrush(QColor("gray")), Qt.ItemDataRole.ForegroundRole)

        # Apply default.
        default = meta.get("default")
        if default is not None:
            idx = widget.findText(str(default))
            if idx < 0 and meta.get("is_material_field"):
                self._ensure_material_option(widget, str(default))
                idx = widget.findText(str(default))
            if idx >= 0:
                widget.setCurrentIndex(idx)

        # Always wire backend sync + change signal.
        widget.currentTextChanged.connect(
            lambda text, k=key: self.backend.set_input_value(k, text)
            if hasattr(self.backend, "set_input_value") else None
        )
        widget.currentTextChanged.connect(self.input_value_changed)

        # Wire generic on_changed callbacks declared in schema.
        for cb_name in self._as_list(meta.get("on_changed")):
            cb = getattr(self, cb_name, None)
            if callable(cb):
                widget.currentTextChanged.connect(cb)

        # Material field wiring.
        if meta.get("is_material_field"):
            member = meta.get("member_type", "Girder")
            self._material_combo_map[key] = widget
            self._material_member_type[key] = member
            if widget.currentText() and widget.currentText() != MATERIAL_CUSTOM_OPTION:
                self._material_previous_selection[key] = widget.currentText()
            widget.currentTextChanged.connect(
                lambda text, k=key, w=widget: self._on_material_changed(k, w, text)
            )

        # Fire on_changed handler(s) once with the current value if requested.
        if meta.get("trigger_on_init"):
            for cb_name in self._as_list(meta.get("on_changed")):
                cb = getattr(self, cb_name, None)
                if callable(cb):
                    cb(widget.currentText())

        return widget

    def _make_textbox(self, key, validator, meta) -> QLineEdit:
        widget = QLineEdit()
        widget.setObjectName(key)
        apply_field_style(widget)

        # Validator
        if validator == "Int Validator":
            widget.setValidator(QRegularExpressionValidator(QRegularExpression(r"^(0|[1-9]\d*)(\.\d+)?$")))
        elif validator == "Double Validator":
            widget.setValidator(QDoubleValidator())

        # Placeholder
        if meta.get("placeholder"):
            widget.setPlaceholderText(meta["placeholder"])
        if meta.get("placeholder_dynamic"):
            self._dynamic_placeholder_map[key] = (widget, meta["placeholder_dynamic"])

        # Default
        default = meta.get("default")
        if default is not None:
            widget.setText(str(default))

        # Backend sync
        widget.editingFinished.connect(
            lambda k=key, w=widget: self.backend.set_input_value(k, w.text())
            if hasattr(self.backend, "set_input_value") else None
        )   
        widget.textChanged.connect(self.input_value_changed)

        # Extra callbacks declared in schema
        for cb_name in self._as_list(meta.get("on_editing_finished")):
            cb = getattr(self, cb_name, None)
            if callable(cb):
                widget.editingFinished.connect(cb)

        return widget

    def _make_button_row(self, label: str, meta: dict) -> QHBoxLayout:
        """
        [Label | Action Button] row.
        label    → tuple[1]
        action   → meta["action"]   — InputDock method name
        btn_text → meta["button_label"] (default "Modify Here")
        """
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        lbl = QLabel(label)
        lbl.setStyleSheet(LABEL_STYLE)
        lbl.setMinimumWidth(110)
        row.addWidget(lbl)

        btn_text = meta.get("button_label")
        btn = QPushButton(btn_text)
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

    def _field_row(self, label: str, widget: QWidget, meta: dict) -> QHBoxLayout:
        """[Label | widget] row. Material combos get an extra info (ℹ) button."""
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        lbl = QLabel(label)
        lbl.setStyleSheet(LABEL_STYLE)
        lbl.setMinimumWidth(110)
        row.addWidget(lbl)

        if meta.get("is_material_field") and isinstance(widget, QComboBox):
            container = QWidget()
            clo = QHBoxLayout(container)
            clo.setContentsMargins(0, 0, 0, 0)
            clo.setSpacing(4)
            clo.addWidget(widget, 1)
            info = QToolButton()
            info.setCursor(Qt.CursorShape.PointingHandCursor)
            info.setAutoRaise(True)
            info.setIcon(QIcon(":/vectors/msg_about.svg"))
            info.setFixedSize(20, 20)
            info.setToolTip("View material properties")
            info.setStyleSheet("QToolButton { border:none; padding:0px; background:transparent; }")
            if info.icon().isNull():
                info.setText("i")
            info.clicked.connect(lambda _=False, k=widget.objectName(): self._show_material_info(k))
            clo.addWidget(info)
            row.addWidget(container, 1)
        else:
            row.addWidget(widget, 1)
        return row

    # ── Collapsible container ─────────────────────────────────────────────────

    def _make_container(self, key: str, root_layout: QVBoxLayout, meta: dict) -> QVBoxLayout:
        name = (meta.get("container_label") or
                meta.get("container_title") or
                key.replace("_", " ").title())
        outer = QGroupBox()
        outer.setStyleSheet(
            "QGroupBox { border:1px solid #90AF13; border-radius:5px;"
            " margin-top:0px; padding-top:5px; background-color:white; }"
        )
        ol = QVBoxLayout()
        ol.setContentsMargins(10, 10, 10, 10)
        ol.setSpacing(10)

        header = QHBoxLayout()
        title_lbl = QLabel(name)
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
        body_layout.setSpacing(10)
        ol.addWidget(body)

        toggle.toggled.connect(lambda checked: (
            body.setVisible(checked),
            toggle.setIcon(QIcon(":/vectors/arrow_up_light.svg" if checked else ":/vectors/arrow_down_light.svg")),
        ))

        outer.setLayout(ol)
        root_layout.addWidget(outer)
        return body_layout

    def _build_toggle_strip(self):
        self.toggle_strip = QWidget()
        self.toggle_strip.setStyleSheet("background-color: #90AF13;")
        self.toggle_strip.setFixedWidth(6)
        sl = QVBoxLayout(self.toggle_strip)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(0)
        sl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        self.toggle_btn = QPushButton("❮")
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setFixedSize(6, 60)
        self.toggle_btn.setToolTip("Hide panel")
        self.toggle_btn.clicked.connect(self.toggle_input_dock)
        self.toggle_btn.setStyleSheet("""
            QPushButton       { background-color:#6c8408; color:white; font-size:12px;
                                font-weight:bold; padding:0px; border:none; }
            QPushButton:hover { background-color:#5e7407; }
        """)
        sl.addStretch()
        sl.addWidget(self.toggle_btn)
        sl.addStretch()
        self.main_layout.addWidget(self.toggle_strip)

    # ══════════════════════════════════════════════════════════════════════════
    # Dynamic placeholder helpers
    # ══════════════════════════════════════════════════════════════════════════

    def _refresh_all_dynamic_placeholders(self):
        """Call all registered dynamic placeholder methods to set initial text."""
        for key, (widget, method_name) in self._dynamic_placeholder_map.items():
            self._apply_dynamic_placeholder(widget, method_name)

    def _apply_dynamic_placeholder(self, widget: QLineEdit, method_name: str):
        method = getattr(self, method_name, None)
        if callable(method):
            try:
                text = method()
                if text:
                    widget.setPlaceholderText(str(text))
            except Exception:
                pass

    def _update_carriageway_placeholder(self, *_):
        """Re-resolve all dynamic placeholders (called when a dependency changes)."""
        self._refresh_all_dynamic_placeholders()

    def _carriageway_placeholder_text(self) -> str:
        """Returns the current placeholder string for the carriageway width field."""
        min_w, max_w = self._carriageway_limits()
        suffix = " per side" if self._is_median_included() else ""
        return f"{min_w:.2f}–{max_w:.1f} m{suffix}"

    # ══════════════════════════════════════════════════════════════════════════
    # Domain event handlers  (called by name from schema on_changed / on_editing_finished)
    # ══════════════════════════════════════════════════════════════════════════

    def _on_footpath_changed(self, value=None):
        if value is None:
            value = self._text(KEY_FOOTPATH)
        if self.additional_inputs and self.additional_inputs.isVisible():
            try:
                self.additional_inputs.update_footpath_value(value)
            except Exception:
                pass

    def _on_design_mode_changed(self, mode_text: str = ""):
        self._current_design_mode = str(mode_text or "Optimized").strip()
        if self.additional_inputs:
            try:
                self.additional_inputs.set_member_properties_design_mode(self._current_design_mode)
            except Exception:
                pass
        if self._current_design_mode.lower() == "custom":
            self._open_additional_inputs(target_tab="Member Properties")

    def _validate_carriageway_width_silent(self, *_):
        """Silent validation (no message box) — called from schema on_changed."""
        self.validate_carriageway_width(show_message=False)

    # ══════════════════════════════════════════════════════════════════════════
    # Carriageway validation
    # ══════════════════════════════════════════════════════════════════════════

    def _is_median_included(self) -> bool:
        return self._text(KEY_INCLUDE_MEDIAN).lower() == "yes"

    def _carriageway_limits(self):
        min_w = CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN if self._is_median_included() else CARRIAGEWAY_WIDTH_MIN
        return min_w, CARRIAGEWAY_WIDTH_MAX_LIMIT

    def validate_carriageway_width(self, show_message=True):
        w = self._w(KEY_CARRIAGEWAY_WIDTH)
        if not isinstance(w, QLineEdit) or not w.text().strip():
            return
        try:
            value = float(w.text())
        except ValueError:
            w.clear()
            if show_message:
                CustomMessageBox(
                    title="Carriageway Width",
                    text="Please enter a numeric value.",
                    dialogType=MessageBoxType.Warning
                ).exec()
            return
        min_w, max_w = self._carriageway_limits()
        msg = None
        if value < min_w:
            msg = ("IRC 5 Cl.104.3.1: min carriageway width with median is 7.5 m per side."
                   if self._is_median_included() else
                   "IRC 5 Cl.104.3.1: min carriageway width is 4.25 m.")
            value = min_w
        elif value > max_w:
            msg = "Software limits carriageway width to 23.6 m."
            value = max_w
        w.setText(f"{value:.2f}")
        if msg and show_message:
            CustomMessageBox(
                title="Carriageway Width",
                text=msg,
                dialogType=MessageBoxType.Warning
            ).exec()

    def _get_effective_carriageway_width(self) -> float:
        min_w, max_w = self._carriageway_limits()
        width = max(min_w, min(self._float(KEY_CARRIAGEWAY_WIDTH, min_w), max_w))
        return width * 2.0 if self._is_median_included() else width

    # ══════════════════════════════════════════════════════════════════════════
    # Material helpers
    # ══════════════════════════════════════════════════════════════════════════

    def _ensure_material_option(self, combo: QComboBox, name: str):
        name = str(name or "").strip()
        if not name or combo.findText(name) >= 0:
            return
        idx = combo.findText(MATERIAL_CUSTOM_OPTION)
        combo.insertItem(idx if idx >= 0 else combo.count(), name)

    def _on_material_changed(self, key: str, combo: QComboBox, text: str):
        if not text or text == MATERIAL_CUSTOM_OPTION:
            member   = self._material_member_type.get(key, "Girder")
            previous = self._material_previous_selection.get(key, "")
            dialog   = MaterialPropertiesDialog(read_only=False, selected_material=previous, member=member)
            if dialog.exec() == QDialog.Accepted:
                fd  = getattr(dialog, "form_data", {})
                mat = str(fd.get("material", "") or "").strip()
                if mat:
                    self._material_custom_fields[mat] = dict(fd.get("fields") or {})
                    self._ensure_material_option(combo, mat)
                    if member == "Girder":
                        sync_custom_materials_across_steel_members(
                            self._material_combo_map, self._ensure_material_option, mat)
                    self._set_combo_silently(combo, mat)
                    self._material_previous_selection[key] = mat
                    self.backend.set_input_value(key, mat)
                    self.input_value_changed.emit()
                    return
            fallback = self._material_previous_selection.get(key, "")
            if not fallback:
                for i in range(combo.count()):
                    v = combo.itemText(i)
                    if v and v != MATERIAL_CUSTOM_OPTION:
                        fallback = v
                        break
            if fallback:
                self._set_combo_silently(combo, fallback)
        else:
            self._material_previous_selection[key] = text

    def _set_combo_silently(self, combo: QComboBox, text: str):
        idx = combo.findText(text)
        if idx < 0:
            return
        blocked = combo.blockSignals(True)
        try:
            combo.setCurrentIndex(idx)
        finally:
            combo.blockSignals(blocked)

    def _show_material_info(self, key: str):
        combo = self._material_combo_map.get(key)
        if not combo:
            return
        selected = combo.currentText().strip()
        if not selected or selected == MATERIAL_CUSTOM_OPTION:
            CustomMessageBox(
                title="Material Data Unavailable",
                text="No material selected.",
                dialogType=MessageBoxType.Warning
            ).exec()
            return
        member = self._material_member_type.get(key, "Girder")
        MaterialPropertiesDialog(
            read_only=True, selected_material=selected, member=member,
            custom_fields=self._material_custom_fields.get(selected),
        ).exec()

    # ══════════════════════════════════════════════════════════════════════════
    # Dialogs
    # ══════════════════════════════════════════════════════════════════════════

    def show_project_location_dialog(self):
        dialog = ProjectLocationDialog()
        if dialog.exec() == QDialog.Accepted:
            self.backend.set_input_value(KEY_PROJECT_LOCATION, dialog.get_selected_location())

    def show_additional_inputs(self):
        self._open_additional_inputs()

    def _open_additional_inputs(self, target_tab=None):
        footpath_value    = self._text(KEY_FOOTPATH) or "None"
        carriageway_width = self._get_effective_carriageway_width()

        self.additional_inputs = AdditionalInputs(footpath_value, carriageway_width)

        if self._additional_inputs_saved_data:
            try:
                self.additional_inputs.set_properties_data(self._additional_inputs_saved_data)
            except Exception:
                pass
        try:
            self.additional_inputs.set_member_properties_design_mode(self._current_design_mode)
        except Exception:
            pass
        if target_tab:
            try:
                for i in range(self.additional_inputs.tabs.count()):
                    if self.additional_inputs.tabs.tabText(i).strip().lower() == target_tab.lower():
                        self.additional_inputs.tabs.setCurrentIndex(i)
                        break
            except Exception:
                pass

        self.additional_inputs.finished.connect(self._on_additional_inputs_closed)

        if self.additional_inputs.exec_() == AdditionalInputs.Accepted:
            values = self.additional_inputs.get_all_values()
            if values:
                self.additional_input_values = values
                self.input_value_changed.emit()

    def _on_additional_inputs_closed(self):
        try:
            saved = self.additional_inputs.get_saved_data()
            if isinstance(saved, dict) and saved:
                self._additional_inputs_saved_data = saved
        except Exception:
            pass
        self.additional_inputs = None

    # ══════════════════════════════════════════════════════════════════════════
    # Lock / unlock
    # ══════════════════════════════════════════════════════════════════════════

    def toggle_lock(self):
        self.is_locked = not self.is_locked
        self.lock_btn.setChecked(self.is_locked)
        self.scroll_area.setDisabled(self.is_locked)
        self._sync_lock_icon()

    def _apply_lock_state(self):
        self._sync_lock_icon()

    def _sync_lock_icon(self):
        if self.lock_btn:
            self.lock_btn.setIcon(QIcon(
                ":/vectors/lock_close.svg" if self.is_locked else ":/vectors/lock_open.svg"
            ))

    def show_lock_tooltip(self):
        if hasattr(self, "tooltip_timer") and self.tooltip_timer.isActive():
            self.tooltip_timer.stop()
        pos = self.lock_btn.mapToGlobal(self.lock_btn.rect().topRight()) + QPoint(5, 0)
        self.lock_btn_tooltip.adjustSize()
        self.lock_btn_tooltip.move(pos)
        self.lock_btn_tooltip.show()
        self.lock_btn_tooltip.raise_()
        if not hasattr(self, "tooltip_timer"):
            self.tooltip_timer = QTimer()
            self.tooltip_timer.setSingleShot(True)
            self.tooltip_timer.timeout.connect(self.lock_btn_tooltip.hide)
        self.tooltip_timer.start(3000)

    def eventFilter(self, obj, event):
        if obj == self.scroll_area and event.type() == QEvent.MouseButtonPress:
            if self.is_locked:
                self.show_lock_tooltip()
            return True
        return super().eventFilter(obj, event)

    # ══════════════════════════════════════════════════════════════════════════
    # Panel toggle
    # ══════════════════════════════════════════════════════════════════════════

    def toggle_input_dock(self):
        if hasattr(self.parent, "toggle_animate"):
            collapsing = self.width() > 0
            self.parent.toggle_animate(show=not collapsing, dock="input")
            self.toggle_btn.setText("❯" if collapsing else "❮")
            self.toggle_btn.setToolTip("Show panel" if collapsing else "Hide panel")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.parent and hasattr(self.parent, "update_docking_icons"):
            self.parent.update_docking_icons(input_is_active=self.width() > 0)

    # ══════════════════════════════════════════════════════════════════════════
    # Input serialization
    # ══════════════════════════════════════════════════════════════════════════

    def _collect_basic_inputs(self) -> list[dict]:
        out = []
        for defn in self.backend.input_values():
            key, _, ftype = defn[0], defn[1], defn[2]
            if ftype in (TYPE_MODULE, TYPE_TITLE, TYPE_BUTTON, TYPE_NOTE):
                continue
            if not isinstance(key, str):
                continue
            w = self._w(key)
            if isinstance(w, QLineEdit):
                val = w.text().strip()
            elif isinstance(w, QComboBox):
                val = w.currentText()
            else:
                continue
            if val:
                out.append({key: val})
                if hasattr(self.backend, "set_input_value"):
                    self.backend.set_input_value(key, val)
        return out

    def _collect_additional_inputs(self) -> list[dict]:
        snapshot = {}
        try:
            if self.additional_inputs and hasattr(self.additional_inputs, "section_properties_tab"):
                tab = self.additional_inputs.section_properties_tab
                if tab and hasattr(tab, "save_properties"):
                    snapshot = tab.save_properties() or {}
        except Exception:
            pass
        if not snapshot:
            snapshot = self._additional_inputs_saved_data or {}
        ordered = ("girder_details", "stiffener_details", "cross_bracing", "end_diaphragm")
        out  = [{k: snapshot[k]} for k in ordered if k in snapshot]
        out += [{k: v} for k, v in snapshot.items() if k not in ordered]
        return out

    def _on_save_input_clicked(self):
        self._basic_inputs_saved_list      = self._collect_basic_inputs()
        self._additional_inputs_saved_list = self._collect_additional_inputs()
        final = self._basic_inputs_saved_list + self._additional_inputs_saved_list
        if hasattr(self.backend, "set_final_design_inputs"):
            self.backend.set_final_design_inputs(final)
        CustomMessageBox(
            title="Inputs Saved",
            text="Basic + Additional inputs saved for this session.",
            dialogType=MessageBoxType.Warning
        ).exec()

    def _on_design_clicked(self):
        final = self._collect_basic_inputs() + self._collect_additional_inputs()
        if hasattr(self.backend, "set_final_design_inputs"):
            self.backend.set_final_design_inputs(final)
        CustomMessageBox(
            title="Design Input Ready",
            text="Final input payload prepared.",
            dialogType=MessageBoxType.Warning
        ).exec()
        try:
            print(f"[OsdagBridge] {len(final)} items")
            print(json.dumps(final, indent=2, ensure_ascii=False, default=str)[:12000])
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    # CAD update helper
    # ══════════════════════════════════════════════════════════════════════════

    def get_all_input_values(self) -> dict:
        values = {
            KEY_SPAN:              self._float(KEY_SPAN),
            KEY_CARRIAGEWAY_WIDTH: self._float(KEY_CARRIAGEWAY_WIDTH),
            KEY_SKEW_ANGLE:        self._float(KEY_SKEW_ANGLE, 0.0),
            KEY_FOOTPATH:          self._text(KEY_FOOTPATH),
            KEY_INCLUDE_MEDIAN:    self._is_median_included(),
        }
        # Fill remaining defaults from DEFAULTS_DICT — single source of truth.
        for key, val in DEFAULTS_DICT.items():
            values.setdefault(key, val)
        # Overlay any values captured from the Additional Inputs dialog.
        if self.additional_input_values:
            values.update(self.additional_input_values)
        return values

    def emit_value_changed(self):
        self.input_value_changed.emit()

    # ══════════════════════════════════════════════════════════════════════════
    # Utilities
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _as_list(value) -> list:
        """Normalise a schema callback value to a list of strings."""
        if not value:
            return []
        return value if isinstance(value, list) else [value]