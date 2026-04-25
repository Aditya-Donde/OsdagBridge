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
        owner = self.owner

        def find_handler(name):
            handler = getattr(owner, str(name), None)
            if callable(handler):
                return handler
            parent_owner = getattr(owner, "owner", None)
            handler = getattr(parent_owner, str(name), None) if parent_owner is not None else None
            return handler if callable(handler) else None

        on_change = field_def.get("on_change")
        if on_change and isinstance(widget, QComboBox):
            handler = find_handler(on_change)
            if handler is None:
                _log.warning("UIBuilder[%s]: on_change=%r not found on owner", type(owner).__name__, on_change)
            else:
                widget.currentTextChanged.connect(handler)

        on_text_changed = field_def.get("on_text_changed")
        if on_text_changed and isinstance(widget, QLineEdit):
            handler = find_handler(on_text_changed)
            if handler is None:
                _log.warning("UIBuilder[%s]: on_text_changed=%r not found on owner", type(owner).__name__, on_text_changed)
            else:
                widget.textChanged.connect(handler)

        on_editing_finished = field_def.get("on_editing_finished")
        if on_editing_finished and isinstance(widget, QLineEdit):
            handler = find_handler(on_editing_finished)
            if handler is None:
                _log.warning("UIBuilder[%s]: on_editing_finished=%r not found on owner", type(owner).__name__, on_editing_finished)
            else:
                widget.editingFinished.connect(handler)

        on_toggled = field_def.get("on_toggled")
        if on_toggled and isinstance(widget, QCheckBox):
            handler = find_handler(on_toggled)
            if handler is None:
                _log.warning("UIBuilder[%s]: on_toggled=%r not found on owner", type(owner).__name__, on_toggled)
            else:
                widget.toggled.connect(handler)

        on_click = field_def.get("on_click")
        if on_click and isinstance(widget, QPushButton):
            handler = find_handler(on_click)
            if handler is None:
                _log.warning("UIBuilder[%s]: on_click=%r not found on owner", type(owner).__name__, on_click)
            else:
                widget.clicked.connect(handler)

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
