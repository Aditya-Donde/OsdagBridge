"""Shared schema walkers for Additional Inputs reset/save/restore/validate."""

from __future__ import annotations

import html
import logging
import re

from PySide6.QtWidgets import QCheckBox, QComboBox, QLineEdit, QWidget

_log = logging.getLogger(__name__)


_FIELD_SECTION_TYPES = {"line", "number", "combo", "mode_line", "mode_value", "checkbox", "computed", "button", "label"}
_NON_INPUT_FIELD_TYPES = {"button", "label"}


def reset_defaults(owner, schema: dict, before=None, after=None) -> None:
    """Reset bound schema widgets back to their declared defaults."""
    _run_hook(owner, before, "_before_reset")

    def on_section(section: dict) -> None:
        stype = _section_type(section)
        if stype in {"checkbox_list", "dynamic_checkbox_list"}:
            default_checked = bool(section.get("default_checked", False))
            for checkbox in _checkboxes(owner, section.get("bind")):
                checkbox.setChecked(default_checked)

    def on_group(_section: dict, group: dict) -> None:
        default_checked = bool(group.get("default_checked", False))
        for checkbox in _checkboxes(owner, group.get("bind")):
            checkbox.setChecked(default_checked)

    def on_field(field: dict, _section: dict | None) -> None:
        _reset_field(owner, field)

    _walk_schema(schema, on_section=on_section, on_group=on_group, on_field=on_field)
    _run_hook(owner, after, "_after_reset")


def collect_values(owner, schema: dict) -> dict:
    """Collect values from bound widgets following the schema."""
    values: dict = {}

    def on_section(section: dict) -> None:
        stype = _section_type(section)
        if stype not in {"checkbox_list", "dynamic_checkbox_list"}:
            return
        key = _section_state_key(section)
        if not key:
            return
        labels = _section_labels(owner, section)
        checkboxes = _checkboxes(owner, section.get("bind"))
        values[key] = {
            label: checkbox.isChecked()
            for label, checkbox in zip(labels, checkboxes)
        }

    def on_group(_section: dict, group: dict) -> None:
        bind = group.get("bind")
        if not bind:
            return
        checkboxes = _checkboxes(owner, bind)
        values[str(bind)] = {checkbox.text(): checkbox.isChecked() for checkbox in checkboxes}

    def on_field(field: dict, _section: dict | None) -> None:
        values.update(_collect_field_values(owner, field))

    _walk_schema(schema, on_section=on_section, on_group=on_group, on_field=on_field)

    extra_state = getattr(owner, "_extra_state", None)
    if callable(extra_state):
        values.update(extra_state() or {})

    return values


def validate(owner, schema: dict) -> list[str]:
    """Validate editable schema-bound widgets and return error messages."""
    errors: list[str] = []
    seen: set[str] = set()

    def add_error(message: str) -> None:
        if message and message not in seen:
            seen.add(message)
            errors.append(message)

    def on_field(field: dict, _section: dict | None) -> None:
        for message in _validate_field(owner, field):
            add_error(message)

    _walk_schema(schema, on_field=on_field)

    extra_validate = getattr(owner, "_extra_validation", None)
    if callable(extra_validate):
        for message in extra_validate() or []:
            add_error(str(message))

    return errors


def restore_values(owner, schema: dict, data: dict) -> None:
    """Restore saved values into widgets described by the schema."""
    if not isinstance(data, dict):
        return

    def on_section(section: dict) -> None:
        stype = _section_type(section)
        if stype not in {"checkbox_list", "dynamic_checkbox_list"}:
            return
        key = _section_state_key(section)
        state = data.get(key)
        if not isinstance(state, dict):
            return
        labels = _section_labels(owner, section)
        checkboxes = _checkboxes(owner, section.get("bind"))
        for label, checkbox in zip(labels, checkboxes):
            if label in state:
                checkbox.setChecked(bool(state[label]))

    def on_group(_section: dict, group: dict) -> None:
        bind = group.get("bind")
        state = data.get(bind) if bind else None
        if not isinstance(state, dict):
            return
        for checkbox in _checkboxes(owner, bind):
            if checkbox.text() in state:
                checkbox.setChecked(bool(state[checkbox.text()]))

    def on_field(field: dict, _section: dict | None) -> None:
        _restore_field(owner, field, data)

    _walk_schema(schema, on_section=on_section, on_group=on_group, on_field=on_field)

    restore_extra = getattr(owner, "_restore_extra_state", None)
    if callable(restore_extra):
        restore_extra(data)


def _walk_schema(schema, on_section=None, on_group=None, on_field=None) -> None:
    if isinstance(schema, dict):
        for card in schema.get("cards", []) or []:
            _walk_schema(card, on_section=on_section, on_group=on_group, on_field=on_field)

        for column in schema.get("columns", []) or []:
            _walk_schema(column, on_section=on_section, on_group=on_group, on_field=on_field)

        for section in schema.get("sections", []) or []:
            _walk_section(section, on_section=on_section, on_group=on_group, on_field=on_field)

        for row in schema.get("rows", []) or []:
            _walk_field_list(row.get("fields"), None, on_field)

        fields = schema.get("fields")
        if isinstance(fields, dict):
            _walk_field_list(fields.values(), None, on_field)
        elif isinstance(fields, list):
            _walk_field_list(fields, None, on_field)


def _walk_section(section: dict, on_section=None, on_group=None, on_field=None) -> None:
    if not isinstance(section, dict):
        return

    if callable(on_section):
        on_section(section)

    stype = _section_type(section)
    if stype == "stacked":
        for page in section.get("pages", []) or []:
            _walk_schema(page, on_section=on_section, on_group=on_group, on_field=on_field)
        return

    for group in section.get("checkbox_groups", []) or []:
        if callable(on_group):
            on_group(section, group)

    if stype in _FIELD_SECTION_TYPES:
        if callable(on_field):
            on_field(section, None)
        return

    _walk_field_list(section.get("fields"), section, on_field)


def _walk_field_list(fields, section: dict | None, on_field) -> None:
    if not callable(on_field):
        return

    if isinstance(fields, dict):
        fields = fields.values()

    for field in fields or []:
        if not isinstance(field, dict):
            continue
        row_fields = field.get("row_fields")
        if row_fields:
            for inline_field in row_fields:
                if isinstance(inline_field, dict):
                    on_field(inline_field, section)
            continue
        on_field(field, section)


def _reset_field(owner, field: dict) -> None:
    ftype = _field_type(field)
    if ftype in _NON_INPUT_FIELD_TYPES:
        return

    if ftype in {"mode_line", "mode_value"}:
        for bind_key, default_key in (("bind_mode", "default_mode"), ("bind_value", "default_value")):
            bind = field.get(bind_key)
            if bind:
                widget = getattr(owner, str(bind), None)
                if widget is None:
                    _log.warning("schema_io[%s]: bind %r declared in schema but not set on owner", type(owner).__name__, bind)
                _set_widget_value(widget, field.get(default_key))
        return

    if ftype == "checkbox":
        bind = field.get("bind")
        if bind:
            widget = getattr(owner, str(bind), None)
            if widget is None:
                _log.warning("schema_io[%s]: bind %r declared in schema but not set on owner", type(owner).__name__, bind)
            _set_widget_value(widget, field.get("default", False))
        return

    bind = field.get("bind")
    if bind is not None:
        widget = getattr(owner, str(bind), None)
        if widget is None:
            _log.warning("schema_io[%s]: bind %r declared in schema but not set on owner", type(owner).__name__, bind)
        _set_widget_value(widget, field.get("default"))


def _collect_field_values(owner, field: dict) -> dict:
    ftype = _field_type(field)
    if ftype in _NON_INPUT_FIELD_TYPES:
        return {}

    if ftype in {"mode_line", "mode_value"}:
        values = {}
        mode_bind = field.get("bind_mode")
        value_bind = field.get("bind_value")
        if mode_bind:
            values[str(mode_bind)] = _widget_value(getattr(owner, str(mode_bind), None))
        if value_bind:
            values[str(value_bind)] = _widget_value(getattr(owner, str(value_bind), None))
        return values

    bind = field.get("bind")
    if not bind:
        return {}

    widget = getattr(owner, str(bind), None)
    if widget is None:
        _log.warning("schema_io[%s]: bind %r declared in schema but not set on owner", type(owner).__name__, bind)
        return {}
    return {str(bind): _widget_value(widget)}


def _restore_field(owner, field: dict, data: dict) -> None:
    ftype = _field_type(field)
    if ftype in _NON_INPUT_FIELD_TYPES:
        return

    if ftype in {"mode_line", "mode_value"}:
        mode_bind = field.get("bind_mode")
        value_bind = field.get("bind_value")
        if mode_bind and mode_bind in data:
            _set_widget_value(getattr(owner, str(mode_bind), None), data.get(mode_bind))
        if value_bind and value_bind in data:
            _set_widget_value(getattr(owner, str(value_bind), None), data.get(value_bind))
        return

    bind = field.get("bind")
    if bind and bind in data:
        _set_widget_value(getattr(owner, str(bind), None), data.get(bind))


def _validate_field(owner, field: dict) -> list[str]:
    ftype = _field_type(field)
    if ftype in _NON_INPUT_FIELD_TYPES:
        return []

    if ftype in {"mode_line", "mode_value"}:
        widget = getattr(owner, str(field.get("bind_value")), None)
    else:
        widget = getattr(owner, str(field.get("bind")), None)

    if not isinstance(widget, QLineEdit):
        return []
    if not widget.isVisible() or not widget.isEnabled() or widget.isReadOnly():
        return []

    label = _field_label(field)
    text = widget.text().strip()
    if not text:
        return [f"{label} cannot be empty."]

    validator = field.get("validator")
    if not validator:
        return []

    try:
        value = float(text)
    except ValueError:
        return [f"{label} must be a valid number."]

    vtype = str(validator.get("type") or "").strip().lower()
    if vtype == "double_range":
        bottom = float(validator.get("bottom", 0.0))
        top = float(validator.get("top", 0.0))
        if value < bottom or value > top:
            return [f"{label} must be between {_fmt_number(bottom)} and {_fmt_number(top)}."]
    elif vtype == "int_range":
        bottom = int(validator.get("bottom", 0))
        top = int(validator.get("top", 0))
        if not value.is_integer():
            return [f"{label} must be a whole number."]
        int_value = int(value)
        if int_value < bottom or int_value > top:
            return [f"{label} must be between {bottom} and {top}."]

    return []


def _widget_value(widget: QWidget):
    if isinstance(widget, QLineEdit):
        return widget.text()
    if isinstance(widget, QComboBox):
        return widget.currentText()
    if isinstance(widget, QCheckBox):
        return widget.isChecked()
    return None


def _set_widget_value(widget: QWidget | None, value) -> None:
    if widget is None:
        return
    if isinstance(widget, QLineEdit):
        widget.setText("" if value is None else str(value))
    elif isinstance(widget, QComboBox):
        if value is not None:
            widget.setCurrentText(str(value))
    elif isinstance(widget, QCheckBox):
        widget.setChecked(bool(value))


def _checkboxes(owner, bind_name) -> list[QCheckBox]:
    if not bind_name:
        return []
    widgets = getattr(owner, str(bind_name), None)
    if not isinstance(widgets, list):
        return []
    return [widget for widget in widgets if isinstance(widget, QCheckBox)]


def _section_labels(owner, section: dict) -> list[str]:
    label_bind = section.get("label_bind")
    if label_bind:
        labels = getattr(owner, str(label_bind), None)
        if isinstance(labels, list):
            label_texts = []
            for label in labels:
                if hasattr(label, "text"):
                    label_texts.append(str(label.text()))
            if label_texts:
                return label_texts

    checkboxes = _checkboxes(owner, section.get("bind"))
    label_texts = [checkbox.text() for checkbox in checkboxes if checkbox.text()]
    if label_texts:
        return label_texts

    return [str(item) for item in section.get("items", []) or []]


def _section_state_key(section: dict) -> str | None:
    for key in ("id", "bind", "title"):
        value = section.get(key)
        if value:
            return str(value)
    return None


def _field_type(field: dict) -> str:
    return str(field.get("type") or "line").strip().lower()


def _section_type(section: dict) -> str:
    return str(section.get("type") or "").strip().lower()


def _field_label(field: dict) -> str:
    label = field.get("label") or field.get("id") or field.get("bind") or "Field"
    text = html.unescape(str(label))
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip(" :")
    return text or "Field"


def _fmt_number(value) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _run_hook(owner, explicit_hook, attr_name: str) -> None:
    hook = explicit_hook if callable(explicit_hook) else getattr(owner, attr_name, None)
    if callable(hook):
        hook()


def describe_binds(owner, schema: dict) -> str:
    """Diagnostic dump of bind state — call from REPL or a debug button.

    Example output::

        Schema binds for WindLoadTab (12 fields):
          BOUND   basic_wind_speed_input    QLineEdit   text=''
          BOUND   terrain_type_combo        QComboBox   current='Plain Terrain'
          MISSING footpath_value_input      (not set on owner)
          SKIP    save_button               (non-input: button)
    """
    lines: list[str] = []
    count = 0

    def on_field(field: dict, _section) -> None:
        nonlocal count
        ftype = _field_type(field)
        binds: list[tuple[str, str]] = []  # (bind_name, role)

        if ftype in _NON_INPUT_FIELD_TYPES:
            bind = field.get("bind")
            if bind:
                lines.append(f"  SKIP    {bind:<40} (non-input: {ftype})")
            return

        if ftype in {"mode_line", "mode_value"}:
            for bkey in ("bind_mode", "bind_value"):
                b = field.get(bkey)
                if b:
                    binds.append((str(b), bkey))
        else:
            b = field.get("bind")
            if b:
                binds.append((str(b), "bind"))

        for bind_name, _role in binds:
            count += 1
            widget = getattr(owner, bind_name, None)
            if widget is None:
                lines.append(f"  MISSING {bind_name:<40} (not set on owner)")
            else:
                wtype = type(widget).__name__
                if isinstance(widget, QLineEdit):
                    detail = f"text={widget.text()!r}"
                elif isinstance(widget, QComboBox):
                    detail = f"current={widget.currentText()!r}"
                elif isinstance(widget, QCheckBox):
                    detail = f"checked={widget.isChecked()}"
                else:
                    detail = ""
                lines.append(f"  BOUND   {bind_name:<40} {wtype:<20} {detail}")

    _walk_schema(schema, on_field=on_field)

    header = f"Schema binds for {type(owner).__name__} ({count} fields):"
    return "\n".join([header] + lines)
