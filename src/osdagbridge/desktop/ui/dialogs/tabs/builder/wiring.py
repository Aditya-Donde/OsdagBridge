"""Post-build wiring — schema-driven conditions, signal connections,
validators, and bind-attribute setters.

Conditions wire visibility/enabled state to source widget signals.
``_connect_signals`` resolves named handlers on the owner (or its
``owner.owner`` for nested cases) and connects them to the appropriate
Qt signal based on widget type.
"""

import logging

from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLineEdit,
    QPushButton,
    QWidget,
)

from osdagbridge.desktop.ui.dialogs.tabs.builder.constants import _MISSING

_log = logging.getLogger(__name__)


class WiringMixin:
    """Conditional visibility, signal wiring, validators, attribute binding."""

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
        layout = node.get("layout")
        if isinstance(layout, dict):
            yield from WiringMixin._iter_fields_with_conditions(layout)
            return
        fields = node.get("fields")
        if isinstance(fields, dict):
            for f in fields.values():
                yield from WiringMixin._iter_fields_with_conditions(f)
        elif isinstance(fields, list):
            for f in fields:
                if isinstance(f, dict):
                    for rf in (f.get("row_fields") or []):
                        if isinstance(rf, dict):
                            yield from WiringMixin._iter_fields_with_conditions(rf)
                    yield from WiringMixin._iter_fields_with_conditions(f)
        for row in (node.get("rows") or []):
            if isinstance(row, dict):
                fields = row.get("fields") or []
            elif isinstance(row, list):
                fields = row
            else:
                fields = []
            for f in fields:
                if isinstance(f, dict):
                    yield from WiringMixin._iter_fields_with_conditions(f)
        for child in (node.get("children") or []):
            yield from WiringMixin._iter_fields_with_conditions(child)
        for key in ("left", "center", "right", "content", "body"):
            child = node.get(key)
            if isinstance(child, dict):
                yield from WiringMixin._iter_fields_with_conditions(child)
        for key in ("sections", "cards", "pages"):
            for sub in (node.get(key) or []):
                yield from WiringMixin._iter_fields_with_conditions(sub)

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

        evaluate()

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
        """Wire schema-declared handlers to the widget's signals.

        ``on_change`` is the universal hook: it fires on whatever change signal
        is natural for the widget type. The specific verbs (``on_text_changed``,
        ``on_editing_finished``, ``on_toggled``, ``on_click``) are escape hatches
        for when you need a non-default signal (e.g. editingFinished instead of
        textChanged on QLineEdit). Specifying both is fine; both connect.
        """
        owner = self.owner

        def find_handler(name):
            handler = getattr(owner, str(name), None)
            if callable(handler):
                return handler
            parent_owner = getattr(owner, "owner", None)
            handler = getattr(parent_owner, str(name), None) if parent_owner is not None else None
            return handler if callable(handler) else None

        def connect_if(handler_name, signal_attr):
            if not handler_name:
                return
            handler = find_handler(handler_name)
            if handler is None:
                _log.warning("UIBuilder[%s]: handler %r not found on owner", type(owner).__name__, handler_name)
                return
            signal = getattr(widget, signal_attr, None)
            if signal is not None:
                signal.connect(handler)

        # on_change: pick the natural signal per widget type
        on_change = field_def.get("on_change")
        if isinstance(widget, QComboBox):
            connect_if(on_change, "currentTextChanged")
        elif isinstance(widget, QLineEdit):
            connect_if(on_change, "textChanged")
        elif isinstance(widget, QCheckBox):
            connect_if(on_change, "toggled")
        elif isinstance(widget, QPushButton):
            connect_if(on_change, "clicked")

        # Specific verbs (back-compat + escape hatches for non-default signals)
        if isinstance(widget, QLineEdit):
            connect_if(field_def.get("on_text_changed"),     "textChanged")
            connect_if(field_def.get("on_editing_finished"), "editingFinished")
        if isinstance(widget, QCheckBox):
            connect_if(field_def.get("on_toggled"), "toggled")
        if isinstance(widget, QPushButton):
            connect_if(field_def.get("on_click"), "clicked")

    def _bind_widget(self, widget: QWidget, field_def: dict) -> None:
        field_id = field_def.get("id")
        if field_id:
            widget.setObjectName(str(field_id))

        bind_name = field_def.get("bind")
        if bind_name:
            existing = getattr(self.owner, str(bind_name), _MISSING)
            if existing is not _MISSING and existing is not widget:
                _log.debug(
                    "UIBuilder[%s]: bind %r already set (%s) — overwriting with %s",
                    type(self.owner).__name__, bind_name,
                    type(existing).__name__, type(widget).__name__,
                )
            setattr(self.owner, str(bind_name), widget)
