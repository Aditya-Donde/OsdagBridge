"""Leaf field builders — one method per schema field type.

Add a new field type by adding an entry to ``_TYPE_TO_METHOD`` in
``constants.py`` and a ``build_*`` method here.
"""

import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)

from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.desktop.ui.dialogs.tabs.builder.constants import (
    _DEFAULT_FIELD_WIDTH,
    _LABEL_STYLE,
    _TYPE_TO_METHOD,
)
from osdagbridge.desktop.ui.utils.custom_widgets import SmartCursorComboBoxView

_log = logging.getLogger(__name__)


class FieldBuildersMixin:
    """One ``build_*`` method per field type, plus the dispatcher."""

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
            widget.setView(SmartCursorComboBoxView(widget))
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

    def build_line_with_bounds(self, field_def: dict) -> QWidget:
        """QLineEdit with a side '...' button for dimension bounds."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        input_widget = QLineEdit()
        input_widget.setObjectName(str(field_def.get("id", "")))
        default = field_def.get("default")
        if default is not None:
            input_widget.setText(str(default))
        if field_def.get("placeholder"):
            input_widget.setPlaceholderText(str(field_def["placeholder"]))
        if field_def.get("read_only"):
            input_widget.setReadOnly(True)
        self._apply_validator(input_widget, field_def.get("validator"))
        apply_field_style(input_widget)
        layout.addWidget(input_widget)

        bind_name = field_def.get("bind")
        if bind_name:
            setattr(self.owner, str(bind_name), input_widget)

        bounds_btn = QPushButton("...")
        bounds_btn.setFixedSize(28, 28)
        bounds_btn.setStyleSheet(
            "QPushButton { background: #f8f8f8; border: 1px solid #d0d0d0; border-radius: 4px; color: #555; font-weight: bold; }"
            "QPushButton:hover { background: #eeeeee; border-color: #b0b0b0; }"
        )
        layout.addWidget(bounds_btn)

        bounds_key = field_def.get("bounds_key")
        if bounds_key:
            handler = getattr(self.owner, "_on_bounds_clicked", None)
            if callable(handler):
                bounds_btn.clicked.connect(lambda: handler(bounds_key))

        bind_widget = field_def.get("bind_widget")
        if bind_widget:
            setattr(self.owner, str(bind_widget), widget)
        bind_btn = field_def.get("bind_bounds_button")
        if bind_btn:
            setattr(self.owner, str(bind_btn), bounds_btn)

        self._connect_signals(input_widget, field_def)
        return widget

    def build_mode_line(self, field_def: dict) -> QWidget:
        """QComboBox + QLineEdit wrapped in a horizontal QWidget.

        ``default_mode`` defaults the combo (e.g. "Auto"). ``default_value``
        defaults the line edit; for consistency with simpler field types it
        falls back to ``default`` when not set explicitly.
        """
        mode_combo = QComboBox()
        for choice in field_def.get("mode_choices") or []:
            mode_combo.addItem(str(choice))
        default_mode = field_def.get("default_mode")
        if default_mode is not None:
            mode_combo.setCurrentText(str(default_mode))
        mode_width = field_def.get("mode_width")
        if mode_width:
            mode_combo.setFixedWidth(int(mode_width))
        apply_field_style(mode_combo)

        value_input = QLineEdit()
        default_value = field_def.get("default_value", field_def.get("default"))
        if default_value is not None:
            value_input.setText(str(default_value))
        if field_def.get("placeholder"):
            value_input.setPlaceholderText(str(field_def["placeholder"]))
        value_width = field_def.get("value_width")
        if value_width:
            value_input.setFixedWidth(int(value_width))
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

        if ftype not in {"mode_line", "line_with_bounds"}:
            self._bind_widget(widget, field_def)
            self._connect_signals(widget, field_def)

        if ftype not in {"mode_line", "checkbox"}:
            width = field_def.get("width", field_def.get("field_width", field_width))
            if width:
                try:
                    widget.setFixedWidth(int(width))
                except (TypeError, ValueError):
                    pass

        enabled = field_def.get("enabled")
        if enabled is not None:
            widget.setEnabled(bool(enabled))

        return widget

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
