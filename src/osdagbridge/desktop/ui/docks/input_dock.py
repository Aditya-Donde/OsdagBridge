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
    QDialog, QFrame, QToolButton
)
from PySide6.QtCore import Qt, QRegularExpression, QSize, QTimer, QPoint, QEvent, Signal
from PySide6.QtGui import QDoubleValidator, QRegularExpressionValidator, QIcon, QColor, QBrush, QFontMetrics

from osdagbridge.core.utils.common import *
from osdagbridge.desktop.ui.utils.custom_buttons import DockCustomButton
from osdagbridge.desktop.ui.dialogs.project_location import ProjectLocationDialog
from osdagbridge.desktop.ui.docks.dock_utils import apply_field_style
from osdagbridge.desktop.ui.dialogs.material_properties import (
    MaterialPropertiesDialog, sync_custom_materials_across_steel_members,
)
from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox, MessageBoxType
from osdagbridge.core.bridge_types.plate_girder.defaults import BASIC_INPUT_DICT
from osdagbridge.core.bridge_types.plate_girder.validator import BridgeInputValidator
from osdagbridge.desktop.ui.utils.custom_cursors import pointing_hand_cursor


MATERIAL_CUSTOM_OPTION = "Custom"

GROUPBOX_STYLE = (
    "QGroupBox { border:1px solid #90AF13; border-radius:4px; background-color:white;"
    "  padding:8px; margin-top:12px; font-size:10px; font-weight:bold; color:#333; }"
    "QGroupBox::title { subcontrol-origin:margin; subcontrol-position:top left;"
    "  left:8px; padding:0 4px; margin-top:4px; background-color:white; color:#333; }"
)
ACTION_BTN_STYLE = (
    "QPushButton { background-color:#90AF13; border: 1px solid #90AF13; color:white; font-weight:bold; border:none;"
    "  border-radius:4px; padding:8px 20px; font-size:11px; min-width:80px; }"
    "QPushButton:hover { background-color:#7a9a12; border: 1px solid #7a9a12;}"
    "QPushButton:disabled { background:#D0D0D0; color:#666; border: 1px solid #D0D0D0;}"
    "QPushButton[error='true'] { background:#FF0000; color:#FFFFFF; border: 1px solid #FF0000;}"
    "QPushButton[error='true']:disabled { background:#D0D0D0; color:#666; border: 1px solid #FF0000; }"
)
LABEL_STYLE = "QLabel { color:#000; font-size:12px; background:transparent; }"
READONLY_FIELD_STYLE = (
    "QLineEdit { padding: 1px 7px;border: 1px solid #d0d0d0; border-radius: 6px; background-color: #ededed; color: #2f2f2f; font-weight: normal; }"
)

class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()


class InputDock(QWidget):
    input_value_changed = Signal()

    def __init__(self, backend, parent):
        super().__init__()
        self.parent  = parent
        self.backend = backend

        # For on spot validation of input fields when changed
        self.validator = BridgeInputValidator()

        # Flag to track if any required field was changed
        # Use to reset the additonal input defaults from common design function
        self.is_require_field_changed = True

        self.is_locked            = False
        self._current_design_mode = "Optimized"
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
        self.additional_inputs_btn.setCursor(pointing_hand_cursor())
        self.additional_inputs_btn.setStyleSheet("""
            QPushButton { background-color:white; color:black; font-weight:bold; font-size:13px;
                          border-radius:5px; border:1px solid black; padding:7px 20px; }
            QPushButton:hover  { background-color:#90AF13; border-color:#90AF13; color:white; }
            QPushButton:pressed { color:black; background-color:white; border:1px solid black; }
        """)
        self.additional_inputs_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # Call from template_page
        self.additional_inputs_btn.clicked.connect(lambda: self.parent.common_design_func("Additional Inputs"))
        top_bar.addWidget(self.additional_inputs_btn)

        self.lock_btn = QPushButton()
        self.lock_btn.setStyleSheet("""
            QPushButton          { background-color:#f4f4f4; border:none; padding:7px; border-radius:4px; }
            QPushButton:hover    { background-color:#e0e0e0; }
            QPushButton:checked  { background-color:#FFA500; }
            QPushButton:checked:hover { background-color:#fa7a02; }
        """)
        self.lock_btn.setCursor(pointing_hand_cursor())
        self.lock_btn.setObjectName("lock_btn")
        self.lock_btn.setCheckable(True)
        self.lock_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.lock_btn.clicked.connect(lambda _: self.toggle_lock())
        top_bar.addWidget(self.lock_btn)

        self.lock_btn_tooltip = QLabel("🔒 Unlock to Edit")
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
        self.save_input_btn.clicked.connect(lambda: self.parent.common_design_func("Save"))
        btn_layout.addWidget(self.save_input_btn)

        self.design_btn = DockCustomButton("Design", ":/vectors/design.svg")
        self.design_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.design_btn.clicked.connect(lambda _, trigger="Design": self.parent.common_design_func(trigger))
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

            # If "required": True, add '*' to Label
            if meta.get("required", False):
                if '\n' in label: # for case like Carriageway Width\n(Each way)
                    idx = label.index('\n')
                    label = label[:idx] + '*' + label[idx:]
                else:
                    label = label + '*'

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
                glayout.addLayout(self._make_button_row(key, label, meta))

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

        # Prime the shared input_dict with the default DB-backed material values so
        # the canonical material keys exist even before the user changes anything.
        self._prime_material_inputs()

        # Resolve all dynamic placeholders now that all widgets exist.
        self._refresh_all_dynamic_placeholders()

    def _prime_material_inputs(self):
        """Populate input_dict with the current material defaults from the dialog."""
        for key, combo in self._material_combo_map.items():
            selected = combo.currentText().strip()
            if not selected or selected == MATERIAL_CUSTOM_OPTION:
                continue

            try:
                # Pass the actual key (e.g. KEY_CROSS_BRACING) as member
                # so the dialog's get_export_fields() uses the correct prefix.
                custom_flds = self._material_custom_fields.get(selected)
                dlg = MaterialPropertiesDialog(read_only=True, selected_material=selected, member=key, custom_fields=custom_flds)
                # Use exported, member-prefixed keys
                fields = dlg.get_export_fields() or {}
                for fld_key, fld_val in fields.items():
                    self._update_input_dict(fld_key, fld_val)
                self._update_input_dict(key, selected)
            except Exception as e:
                print(f"[DEBUG] _prime_material_inputs error for {key}: {e}")

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

        # Signal that change in value so to update the input_dictionary
        widget.currentTextChanged.connect(
            lambda text, k=key: self._on_field_edited(k, text)
        )

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
            double_val = QDoubleValidator()
            double_val.setNotation(QDoubleValidator.StandardNotation)
            widget.setValidator(double_val)

        # Placeholder
        if meta.get("placeholder"):
            widget.setPlaceholderText(meta["placeholder"])
        if meta.get("placeholder_dynamic"):
            self._dynamic_placeholder_map[key] = (widget, meta["placeholder_dynamic"])

        # Default
        default = meta.get("default")
        if default is not None:
            widget.setText(str(default))

        # Validation on focus-out — mandatory for all textbox fields
        # This will validate the input, either it say nothing or popup warning and set specific valid value
        widget.editingFinished.connect(
            lambda k=key, w=widget: self._on_field_edited(k, w)
        )

        # For soft-validation while value is being edited in the textbox
        widget.textChanged.connect(
            lambda text, k=key: self._on_field_editing(text, k)
        )

        # Extra callbacks declared in schema
        for cb_name in self._as_list(meta.get("on_editing_finished")):
            cb = getattr(self, cb_name, None)
            if callable(cb):
                widget.editingFinished.connect(cb)

        return widget

    def _make_button_row(self, key: str, label: str, meta: dict) -> QVBoxLayout | QHBoxLayout:
        if key != KEY_PROJECT_LOCATION:
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(8)

            lbl = QLabel(label)
            lbl.setStyleSheet(LABEL_STYLE)
            lbl.setMinimumWidth(110)
            row.addWidget(lbl)

            btn_text = meta.get("button_label")
            btn = QPushButton(btn_text)
            btn.setObjectName(key)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setStyleSheet(ACTION_BTN_STYLE)
            cb = getattr(self, meta.get("action", ""), None)
            if callable(cb):
                btn.clicked.connect(cb)
            else:
                btn.setEnabled(False)
            btn.clicked.connect(lambda _, widget=btn: self.reset_error_state(widget))
            row.addWidget(btn, 1)
            return row

        # KEY_PROJECT_LOCATION: button + station + state rows stacked
        container = QVBoxLayout()
        container.setContentsMargins(0, 0, 0, 0)
        container.setSpacing(6)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(8)

        lbl = QLabel(label)
        lbl.setStyleSheet(LABEL_STYLE)
        lbl.setMinimumWidth(110)
        top_row.addWidget(lbl)

        btn_text = meta.get("button_label")
        btn = QPushButton(btn_text)
        btn.setObjectName(key)
        btn.setCursor(pointing_hand_cursor())
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn.setStyleSheet(ACTION_BTN_STYLE)
        cb = getattr(self, meta.get("action", ""), None)
        if callable(cb):
            btn.clicked.connect(cb)
        else:
            btn.setEnabled(False)
        btn.clicked.connect(lambda _, widget=btn: self.reset_error_state(widget))
        top_row.addWidget(btn, 1)
        container.addLayout(top_row)

        # Single location display row
        self.project_location_display_row = QWidget()
        loc_row = QHBoxLayout(self.project_location_display_row)
        loc_row.setContentsMargins(0, 10, 0, 0)
        loc_row.setSpacing(6)
        
        loc_row.addStretch()
        
        self.location_pin_label = QLabel()
        self.location_pin_label.setPixmap(QIcon(":/vectors/locate-location-pin.svg").pixmap(20, 20))
        self.location_pin_label.setStyleSheet("background: transparent;")
        loc_row.addWidget(self.location_pin_label)

        self.location_text_label = QLabel("")
        self.location_text_label.setStyleSheet("font-size: 13px; font-weight: normal ; color: #333; background: transparent;")
        self.location_text_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        loc_row.addWidget(self.location_text_label)
        
        loc_row.addStretch()

        container.addWidget(self.project_location_display_row)
        self.project_location_display_row.setVisible(False)

        return container

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
            info.setCursor(pointing_hand_cursor())
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
        self.toggle_btn.setCursor(pointing_hand_cursor())
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
        # Footpath toggle changes overall bridge width — force defaults re-solve
        # on next Additional Inputs open so the dict has the new geometry.
        self.is_require_field_changed = True
        self.parent.notify_additional_inputs_footpath(value)

    def _on_include_median_changed(self, value=None):
        # Median toggle also changes overall bridge width and the Median sub-tab's
        # enabled state — flag so solve_extend_basic_input_dict runs on next open.
        self.is_require_field_changed = True

    def _validate_carriageway_width_silent(self, value=None):
        self._validate_field_silently(KEY_CARRIAGEWAY_WIDTH)

    def _on_design_mode_changed(self, mode_text: str = ""):
        self._current_design_mode = str(mode_text or "Optimized").strip()
        self.is_require_field_changed = True
        if self._current_design_mode.lower() == "custom":
            self.parent.common_design_func("Additional Inputs", target_tab="Member Properties")
    # ══════════════════════════════════════════════════════════════════════════
    # Carriageway validation
    # ══════════════════════════════════════════════════════════════════════════

    def _is_median_included(self) -> bool:
        return self._text(KEY_INCLUDE_MEDIAN).lower() == "yes"

    def _carriageway_limits(self):
        min_w = CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN if self._is_median_included() else CARRIAGEWAY_WIDTH_MIN
        return min_w, CARRIAGEWAY_WIDTH_MAX_LIMIT

    def _get_effective_carriageway_width(self) -> float:
        min_w, max_w = self._carriageway_limits()
        width = max(min_w, min(self._float(KEY_CARRIAGEWAY_WIDTH, min_w), max_w))
        return width * 2.0 if self._is_median_included() else width

    def _validate_field_silently(self, key):
        # Validates and corrects a field after a dependency change — no popup.
        widget = self._w(key)
        if not widget:
            return
        self._update_input_dict(key, widget.text().strip())
        result = self.validator.validate_basic_inputs(key, self.parent.input_dict)
        if result is not None:
            corrected, _ = result
            widget.blockSignals(True)
            widget.setText(str(corrected))
            widget.blockSignals(False)
            self._update_input_dict(key, str(corrected))

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
            # Always pass the input key (e.g. KEY_GIRDER, KEY_CROSS_BRACING)
            # to the dialog so it can map exported fields to the correct
            # member-specific canonical keys (material.girder.*, material.cross_bracing.*, ...)
            member   = key
            previous = self._material_previous_selection.get(key, "")
            dialog   = MaterialPropertiesDialog(read_only=False, selected_material=previous, member=member)
            if dialog.exec() == QDialog.Accepted:
                fd  = getattr(dialog, "form_data", {})
                mat = str(fd.get("material", "") or "").strip()
                if mat:
                    # store BASE fields for this custom material
                    # DO NOT store exported fields so they can be reused by other members
                    self._material_custom_fields[mat] = dict(fd.get("fields") or {})
                    self._ensure_material_option(combo, mat)
                    if self._material_member_type.get(key) == "Girder":
                        sync_custom_materials_across_steel_members(
                            self._material_combo_map, self._ensure_material_option, mat)
                    self._set_combo_silently(combo, mat)
                    self._material_previous_selection[key] = mat
                    # Apply custom fields into the shared input dictionary
                    exported = dialog.get_export_fields()
                    for fld_key, fld_val in (exported or {}).items():
                        # Use update helper to ensure defaults handling
                        self._update_input_dict(fld_key, fld_val)
                    # Also update the material combo key itself
                    self._update_input_dict(key, mat)
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
            # Non-custom selection: populate input_dict with DB-sourced defaults
            try:
                # Pass the input key so exported fields are member-prefixed correctly
                # Pass custom_fields so previously created custom materials can be correctly parsed
                custom_flds = self._material_custom_fields.get(text)
                dlg = MaterialPropertiesDialog(read_only=True, selected_material=text, member=key, custom_fields=custom_flds)
                # dialog constructs form_data on init; request exported/member-prefixed fields
                fields = dlg.get_export_fields() or {}
                # Write each field into the input dictionary
                for fld_key, fld_val in fields.items():
                    self._update_input_dict(fld_key, fld_val)
                # Also ensure the combo selection is recorded
                self._update_input_dict(key, text)
                self.input_value_changed.emit()
                # Ensure material property widgets for these fields are read-only (DB sourced)
                self._set_material_fields_editable(list(fields.keys()), False)
            except Exception:
                # Fail gracefully; do not block material selection
                pass

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
        # pass the input key as member so dialog shows member-specific fields
        MaterialPropertiesDialog(
            read_only=True, selected_material=selected, member=key,
            custom_fields=self._material_custom_fields.get(selected),
        ).exec()

    # ══════════════════════════════════════════════════════════════════════════
    # Dialogs
    # ══════════════════════════════════════════════════════════════════════════

    def show_project_location_dialog(self):
        dialog = ProjectLocationDialog()
        if dialog.exec() != QDialog.Accepted:
            return

        loc = dialog.get_selected_location()
        self._update_input_dict(KEY_PROJECT_LOCATION, loc)

        method = loc.get("method")
        data = loc.get("data", {}) if isinstance(loc, dict) else {}

        if method == "location_name":
            station = data.get("district", "")
            state = data.get("state", "")
            show_rows = True
        elif method == "map":
            station = data.get("station", "")
            state = data.get("state", "")
            show_rows = True
        else:  # custom_data
            station = ""
            state = ""
            show_rows = False

        if hasattr(self, "location_text_label"):
            if station and state:
                self.location_text_label.setText(f"{station}, {state}")
            elif station:
                self.location_text_label.setText(station)
            elif state:
                self.location_text_label.setText(state)
            else:
                self.location_text_label.setText("Location not selected")

        if hasattr(self, "project_location_display_row"):
            self.project_location_display_row.setVisible(show_rows)

    # To open additional input from additional geometry
    def show_additional_inputs(self):
        self.parent.common_design_func("Additional Inputs")

    # ══════════════════════════════════════════════════════════════════════════
    # Lock / unlock
    # ══════════════════════════════════════════════════════════════════════════

    def toggle_lock(self, confirm=True):

        if self.is_locked and confirm:
            result = CustomMessageBox(
                title="Clear Results",
                text="Unlocking will delete all results and plots.",
                informativeText="Do you want to continue?",
                buttons=["Continue", "Cancel"],
                dialogType=MessageBoxType.Warning,
            ).exec()
            if result != "Continue":
                self.lock_btn.setChecked(True)
                return

        self.is_locked = not self.is_locked

        # Update Additional Input State (Lock/Unlock)
        self.parent._additional_inputs_dialog.lock(lock=self.is_locked)

        if not self.is_locked:
            # Clear 3D-Cad
            self.parent.cad_3d_widget.clear_3d_cad()
            # Resync toolbar so the Legend / Axis toggles no longer look selected
            if hasattr(self.parent, "toolbar_ctrl"):
                self.parent.toolbar_ctrl.sync_cad_overlays_off()
            # Clear plots and reset output dock values
            self.parent.plots_widget.clear()
            self.parent.output_dock.reset()

        self.lock_btn.setChecked(self.is_locked)
        self.scroll_area.setDisabled(self.is_locked)
        self.design_btn.setDisabled(self.is_locked)
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

    def reset_error_state(self, widget: QWidget):
        """Reset error='true' property to remove red highlight."""
        if widget and widget.property("error"):
            widget.setProperty("error", False)
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    def _is_require_field(self, key_required: str) -> bool:
        """
        Check if a field is required field of Input dock
        Useful to track change in any required field in Input dock
        To reset the additional Input Defaults
        """
        for tupple in self.backend.input_values():
            key, label, _, _, _, _, meta_data = tupple
            if key == key_required:
                if meta_data.get("required", False):
                    return True
        
        # by default return False
        return False

    def _on_field_edited(self, key: str, widget: QLineEdit | str):
        """
        Called on editingFinished (QLineEdit) or currentTextChanged (QComboBox).
        - QComboBox: always valid, skip validation, update dict + CAD.
        - QLineEdit: hard validation — corrects widget + input_dict if invalid, shows popup.
        """

        if self._is_require_field(key):
            self.is_require_field_changed = True

        # QComboBox passes str directly via currentTextChanged
        if isinstance(widget, str):
            self._update_input_dict(key, widget)
            # Defer CAD refresh so all other currentTextChanged handlers
            # (e.g., median/footpath re-solve callbacks) finish first.
            QTimer.singleShot(0, self.input_value_changed.emit)
            return

        current_text = widget.text().strip()

        # Update dict first so validator reads the latest value
        self._update_input_dict(key, current_text)

        # hard-validation start ----------------------
        result = self.validator.validate_basic_inputs(key, self.parent.input_dict)
        if result is not None:
            corrected, message = result
            CustomMessageBox(
                title="Input Error",
                text=message,
                dialogType=MessageBoxType.Warning
            ).exec()
            # update to valid text
            widget.blockSignals(True)
            widget.setText(str(corrected))
            widget.blockSignals(False)
            self._update_input_dict(key, str(corrected))
        # hard-validation end ----------------------

        # Always update CAD after hard validation
        self.input_value_changed.emit()


    def _on_field_editing(self, current_text: str, key: str):
        """
        Soft validation — called on textChanged (while typing).
        No popups, no corrections. Updates dict + CAD only when valid.
        """

        # Always reset error state while typing
        widget = self.input_widget.findChild(QWidget, key)
        if widget and widget.property("error"):
            widget.setProperty("error", False)
            widget.style().unpolish(widget)
            widget.style().polish(widget)

        if not current_text.strip():
            # Empty — fall back to default silently
            self._update_input_dict(key, "")
            self.input_value_changed.emit()
            return

        # Update dict first so validator reads the latest value
        self._update_input_dict(key, current_text)

        # soft-validation start ----------------------
        result = self.validator.validate_basic_inputs(key, self.parent.input_dict)
        if result is not None:
            # Still typing, value not valid yet — skip CAD update
            return
        # soft-validation end ----------------------

        # Valid - update CAD
        self.input_value_changed.emit()
        
    # ══════════════════════════════════════════════════════════════════════════
    # Inputs Saving using input_dictionary
    # ══════════════════════════════════════════════════════════════════════════
    
    # Update input_dictionary on value changed
    def _update_input_dict(self, key: str, value: str):
        """
        Called on every widget value change.
        If value is empty/None, falls back to BASIC_INPUT_DICT.
        Updates parent input_dict and notifies listeners.
        """

        if hasattr(self.parent, "input_dict"):
            # If Empty or None Value then set the default
            # print(f"@Change: {value}, default: {BASIC_INPUT_DICT.get(key)}")
            if value is None or value == "":
                self.parent.input_dict[key] = BASIC_INPUT_DICT.get(key)
            else:
                self.parent.input_dict[key] = value
            # print(f"@Final: {self.parent.input_dict[key]}")
            
        else:
            print("[ERROR]: template_page.input_dictionary Not Found")

    def populate_from_dict(self, data: dict) -> None:
        """
        Push all values from *data* into the input dock widgets and parent.input_dict.
        Called after loading an OSI file.  Signals are blocked while setting
        widget values to avoid cascading validation callbacks.
        """
        if not self.input_widget:
            return

        # Replace input_dict contents in-place (keep same object reference)
        if hasattr(self.parent, "input_dict"):
            self.parent.input_dict.clear()
            self.parent.input_dict.update(data)

        # Walk every widget that has an objectName matching a key in data
        for widget in self.input_widget.findChildren(QWidget):
            key = widget.objectName()
            if not key or key not in data:
                continue
            value = data[key]
            if value is None:
                continue
            text = str(value)
            if isinstance(widget, QLineEdit):
                widget.blockSignals(True)
                widget.setText(text)
                widget.blockSignals(False)
            elif isinstance(widget, QComboBox):
                # Ensure the saved value exists as an option (handles custom materials)
                if widget.findText(text) < 0:
                    widget.addItem(text)
                self._set_combo_silently(widget, text)

        # Mark required fields as changed so solve_extend_basic_input_dict
        # runs on the next Design call and derives all computed defaults.
        self.is_require_field_changed = True
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