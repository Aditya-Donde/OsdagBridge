"""
GeneralizedSchemaSubTab
=======================
A single schema-driven sub-tab widget that replaces every hand-crafted
sub-tab class.  The pattern mirrors input_dock.py:

    Schema dict  →  one build loop  →  widgets

Usage
-----
    tab = GeneralizedSchemaSubTab(LAYOUT_TAB_SCHEMA, owner=typical_section_instance)
    tab.get_values()          # -> {"girder_spacing": "3.0", "no_of_girders": "4", ...}
    tab.reset_defaults()      # restore every widget to its schema default

The ``owner`` object is used for:
  * ``bind``           → setattr(owner, bind_name, widget)
  * ``on_text_changed``, ``on_editing_finished``, ``on_change`` callbacks
    → resolved as getattr(owner, method_name)

Adding a new sub-tab therefore only requires a new schema entry in
``ui_fields_additional_input.py`` — no new Python class needed.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QCheckBox,
    QScrollArea, QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator, QIntValidator

from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style

_LABEL_STYLE   = "font-size: 11px; color: #3a3a3a; background: transparent; border: none;"
_HEADING_STYLE = "font-size: 12px; font-weight: 700; color: #2b2b2b; background: transparent; border: none;"
_DEFAULT_FIELD_WIDTH = 180


class GeneralizedSchemaSubTab(QWidget):
    """Schema-driven sub-tab widget.

    Parameters
    ----------
    schema:
        One of the schema dicts defined in ``ui_fields_additional_input.py``.
        Supported top-level formats: ``"rows"``, ``"sections"``,
        ``"cards"`` (with nested ``"sections"``).
    owner:
        Object onto which ``bind`` attributes are set and from which
        callback methods are resolved.  Defaults to *self*.
    parent:
        Standard Qt parent widget.
    """

    def __init__(self, schema: dict, owner=None, parent=None):
        super().__init__(parent)
        self._schema = schema
        self._owner  = owner or self
        # field_id  ->  primary widget (QLineEdit / QComboBox / QCheckBox)
        self._widget_map: dict[str, QWidget] = {}
        self.setStyleSheet("background-color: white;")
        self._build()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self):
        """Single loop through schema sections — like input_dock._build_field_loop."""
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        content = QWidget()
        content.setStyleSheet("background-color: white;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(12)

        label_width = self._schema.get("label_width", 200)
        field_width = self._schema.get("field_width", _DEFAULT_FIELD_WIDTH)

        for section_title, fields in self._iter_sections():
            if section_title:
                lbl = QLabel(section_title)
                lbl.setStyleSheet(_HEADING_STYLE)
                layout.addWidget(lbl)

            grid = QGridLayout()
            grid.setContentsMargins(0, 4, 0, 0)
            grid.setHorizontalSpacing(12)
            grid.setVerticalSpacing(10)
            grid.setColumnMinimumWidth(0, label_width)

            row_idx = 0
            for field_def in fields:
                # ── inline row (multiple fields on one line) ──────────
                row_fields = field_def.get("row_fields")
                if row_fields:
                    col = 0
                    for rf in row_fields:
                        lbl = QLabel(rf.get("label", ""))
                        lbl.setStyleSheet(_LABEL_STYLE)
                        grid.addWidget(lbl, row_idx, col, Qt.AlignLeft | Qt.AlignVCenter)
                        w = self._make_widget(rf, rf.get("width", field_width))
                        grid.addWidget(w, row_idx, col + 1, Qt.AlignLeft)
                        col += 2
                    row_idx += 1
                    continue

                ftype = field_def.get("type", "line")

                # ── standalone checkbox (no label column) ─────────────
                if ftype == "checkbox":
                    w = self._make_widget(field_def, field_width)
                    grid.addWidget(w, row_idx, 0, 1, 2, Qt.AlignLeft)
                    row_idx += 1
                    continue

                # ── standard label + widget row ───────────────────────
                lbl = QLabel(field_def.get("label", ""))
                lbl.setStyleSheet(_LABEL_STYLE)
                grid.addWidget(lbl, row_idx, 0, Qt.AlignLeft | Qt.AlignVCenter)
                label_bind = field_def.get("label_bind")
                if label_bind:
                    setattr(self._owner, label_bind, lbl)

                w = self._make_widget(field_def, field_def.get("width", field_width))
                grid.addWidget(w, row_idx, 1, Qt.AlignLeft)
                row_idx += 1

            layout.addLayout(grid)

        layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

    # ------------------------------------------------------------------
    # Schema iteration — handles rows / sections / cards formats
    # ------------------------------------------------------------------

    def _iter_sections(self):
        """Yield ``(section_title, [field_def, ...])`` from any schema format."""
        schema = self._schema

        # "rows" format — flat, no section titles
        if "rows" in schema:
            all_fields = []
            for row in schema["rows"]:
                all_fields.extend(row.get("fields", []))
            yield None, all_fields
            return

        # "sections" format
        if "sections" in schema:
            for section in schema["sections"]:
                yield section.get("title"), section.get("fields", [])
            return

        # "cards" → "sections" format
        if "cards" in schema:
            for card in schema["cards"]:
                card_title = card.get("title")
                for section in card.get("sections", []):
                    title = section.get("title") or card_title
                    yield title, section.get("fields", [])
            return

    # ------------------------------------------------------------------
    # Widget factory — one method handles every field type
    # ------------------------------------------------------------------

    def _make_widget(self, field_def: dict, field_width: int = _DEFAULT_FIELD_WIDTH) -> QWidget:
        """Create, register, bind, and wire the widget for *field_def*."""
        ftype  = field_def.get("type", "line")
        fid    = field_def.get("id", "")
        bind   = field_def.get("bind")
        owner  = self._owner

        widget: QWidget

        # ── combo ─────────────────────────────────────────────────────
        if ftype == "combo":
            widget = QComboBox()
            widget.addItems(field_def.get("choices") or [])
            default = field_def.get("default")
            if default is not None:
                widget.setCurrentText(str(default))
            widget.setFixedWidth(field_width)
            apply_field_style(widget)
            on_change = field_def.get("on_change")
            if on_change and hasattr(owner, on_change):
                widget.currentTextChanged.connect(getattr(owner, on_change))

        # ── checkbox ──────────────────────────────────────────────────
        elif ftype == "checkbox":
            widget = QCheckBox(field_def.get("label", ""))
            widget.setChecked(bool(field_def.get("default", False)))
            widget.setStyleSheet(
                "QCheckBox { font-size: 11px; color: #333333; background: transparent; spacing: 8px; }"
            )

        # ── mode_line (mode combo + value input) ──────────────────────
        elif ftype == "mode_line":
            container = QWidget()
            container.setStyleSheet("background: transparent;")
            h = QHBoxLayout(container)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(4)

            mode_combo = QComboBox()
            mode_combo.addItems(field_def.get("mode_choices") or [])
            default_mode = field_def.get("default_mode")
            if default_mode is not None:
                mode_combo.setCurrentText(str(default_mode))
            mode_combo.setFixedWidth(130)
            apply_field_style(mode_combo)
            h.addWidget(mode_combo)

            value_input = QLineEdit()
            default_val = field_def.get("default_value")
            if default_val is not None:
                value_input.setText(str(default_val))
            placeholder = field_def.get("placeholder")
            if placeholder:
                value_input.setPlaceholderText(str(placeholder))
            value_input.setFixedWidth(100)
            apply_field_style(value_input)
            h.addWidget(value_input)

            bind_mode = field_def.get("bind_mode")
            if bind_mode:
                setattr(owner, bind_mode, mode_combo)
            bind_val = field_def.get("bind_value")
            if bind_val:
                setattr(owner, bind_val, value_input)

            on_mode_change = field_def.get("on_mode_change")
            if on_mode_change and hasattr(owner, on_mode_change):
                mode_combo.currentTextChanged.connect(getattr(owner, on_mode_change))

            # Register both parts
            if fid:
                self._widget_map[fid]              = mode_combo
                self._widget_map[fid + "_value"]   = value_input
            if bind:
                setattr(owner, bind, container)
            return container

        # ── line / computed / read_only / unknown ─────────────────────
        else:
            widget = QLineEdit()
            default = field_def.get("default")
            if default is not None:
                widget.setText(str(default))

            read_only = field_def.get("read_only") or ftype == "computed"
            if read_only:
                widget.setReadOnly(True)
                widget.setStyleSheet(
                    "QLineEdit { background-color: #f2f2f2; color: #666;"
                    " border: 1px solid #c0c0c0; border-radius: 4px; padding: 4px 6px; }"
                )

            validator_def = field_def.get("validator")
            if validator_def:
                vtype = validator_def.get("type")
                if vtype == "double_range":
                    widget.setValidator(QDoubleValidator(
                        float(validator_def.get("bottom", 0.0)),
                        float(validator_def.get("top",    1e9)),
                        int(validator_def.get("decimals", 2)),
                    ))
                elif vtype == "int_range":
                    widget.setValidator(QIntValidator(
                        int(validator_def.get("bottom", 0)),
                        int(validator_def.get("top",    999_999)),
                    ))

            placeholder = field_def.get("placeholder")
            if placeholder:
                widget.setPlaceholderText(str(placeholder))

            widget.setFixedWidth(field_width)
            apply_field_style(widget)

            on_text = field_def.get("on_text_changed")
            if on_text and hasattr(owner, on_text):
                widget.textChanged.connect(getattr(owner, on_text))

            on_finished = field_def.get("on_editing_finished")
            if on_finished and hasattr(owner, on_finished):
                widget.editingFinished.connect(getattr(owner, on_finished))

        # ── common registration ───────────────────────────────────────
        if fid:
            widget.setObjectName(fid)
            self._widget_map[fid] = widget
        if bind:
            setattr(owner, bind, widget)

        return widget

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------

    def get_values(self) -> dict:
        """Return ``{field_id: value}`` for every tracked widget."""
        values = {}
        for fid, widget in self._widget_map.items():
            if isinstance(widget, QLineEdit):
                values[fid] = widget.text()
            elif isinstance(widget, QComboBox):
                values[fid] = widget.currentText()
            elif isinstance(widget, QCheckBox):
                values[fid] = widget.isChecked()
        return values

    def reset_defaults(self):
        """Reset every widget to its schema-defined default."""
        for _, fields in self._iter_sections():
            for field_def in fields:
                row_fields = field_def.get("row_fields")
                if row_fields:
                    for rf in row_fields:
                        self._reset_field(rf)
                    continue
                self._reset_field(field_def)

    def _reset_field(self, field_def: dict):
        fid     = field_def.get("id")
        default = field_def.get("default")
        if not fid or default is None:
            return
        widget = self._widget_map.get(fid)
        if widget is None:
            return
        if isinstance(widget, QLineEdit):
            widget.setText(str(default))
        elif isinstance(widget, QComboBox):
            widget.setCurrentText(str(default))
        elif isinstance(widget, QCheckBox):
            widget.setChecked(bool(default))
