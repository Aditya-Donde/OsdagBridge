# Adding a New Additional Inputs Tab

This guide explains how to add a new tab to the **Additional Inputs** dialog.
There are two paths depending on the complexity of the tab you need.

---

## Which path do you need?

| Your tab needs… | Path |
|---|---|
| Labels + input fields (text, combo, checkbox) | **Path A — Pure Schema** (no Python class, ~20 lines) |
| A table, CRUD panel, mode-toggle sections, or embedded sub-dialog | **Path B — Custom Class** (write a `QWidget` subclass) |

When in doubt, start with Path A. If it can't express your UI, switch to Path B.

---

## Path A — Pure Schema Tab

This is the zero-boilerplate path. You define your fields as a Python dict,
register one entry in the tab registry, and you're done. The
`GeneralizedSchemaSubTab` class builds the full UI automatically.

### Step 1 — Define the schema

Add your schema to
`src/osdagbridge/core/bridge_types/plate_girder/ui_fields_additional_input.py`.

```python
MY_NEW_TAB_SCHEMA = {
    "id":          "my_new_tab",       # unique identifier
    "label_width": 200,                # pixel width of the label column
    "field_width": 180,                # pixel width of input widgets
    "sections": [                      # or "rows" — see Formats below
        {
            "title": "My Section Heading",
            "fields": [
                {
                    "id":        "some_value",
                    "label":     "Some Value (m):",
                    "type":      "line",
                    "default":   "1.00",
                    "validator": {"type": "double_range", "bottom": 0.0, "top": 100.0, "decimals": 2},
                    "bind":      "some_value",
                },
                {
                    "id":      "some_choice",
                    "label":   "Choose Option:",
                    "type":    "combo",
                    "choices": ["Option A", "Option B", "Option C"],
                    "default": "Option A",
                    "bind":    "some_choice",
                },
            ],
        },
    ],
}
```

### Step 2 — Register the tab

In `src/osdagbridge/desktop/ui/dialogs/additional_inputs.py`, import your
schema at the top and add one entry to `_TAB_REGISTRY`:

```python
# At the top of the file, add to the existing import block:
from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import (
    ...,
    MY_NEW_TAB_SCHEMA,     # ← add this
)

# In _TAB_REGISTRY, append:
{
    "id":      "my_new_tab",
    "label":   "My New Tab",
    "factory": lambda dlg: GeneralizedSchemaSubTab(MY_NEW_TAB_SCHEMA),
},
```

That's it. The dialog will build the tab, collect its values via `get_values()`,
and include them in the nested dict returned by `get_all_values()`.

---

## Path B — Custom Class Tab

Use this when your tab needs a table, CRUD operations, dynamic section
show/hide, or anything `GeneralizedSchemaSubTab` cannot express.

### Step 1 — Write the widget class

Create a file under the appropriate sub-directory:

```
src/osdagbridge/desktop/ui/dialogs/tabs/sub_tabs/
    typical_section/   ← typical section sub-tabs
    loading/           ← loading sub-tabs
    section_properties/← member properties sub-tabs
    my_new_tab.py      ← or a new sub-directory
```

Your class must implement two methods so the dialog can use it uniformly:

```python
from PySide6.QtWidgets import QWidget, QVBoxLayout

class MyNewTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        # build your UI here — tables, combos, anything you need
        ...

    def get_values(self) -> dict:
        """Return {field_id: value} for every input in this tab."""
        return {
            "some_field": self.some_widget.text(),
            "another":    self.combo.currentText(),
        }

    def reset_defaults(self):
        """Restore all fields to their default values."""
        self.some_widget.setText("1.00")
        self.combo.setCurrentIndex(0)
```

### Step 2 — Register the tab

```python
# Import your class in additional_inputs.py:
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.my_new_tab import MyNewTab

# Append to _TAB_REGISTRY:
{
    "id":      "my_new_tab",
    "label":   "My New Tab",
    "factory": lambda dlg: MyNewTab(),
},
```

If your tab needs data from the dialog (e.g. carriageway width), pass it via
the lambda:

```python
"factory": lambda dlg: MyNewTab(dlg.carriageway_width),
```

---

## Schema field reference

Every field dict supports the following keys.

### Common keys (all field types)

| Key | Required | Description |
|---|---|---|
| `id` | ✓ | Unique key used in `get_values()` output |
| `label` | ✓ | Text shown to the left of the field |
| `type` | ✓ | See field types below |
| `default` | — | Initial value shown in the widget |
| `bind` | — | If set, the widget is stored as `setattr(owner, bind, widget)` so callbacks on the owner can reference it directly |
| `label_bind` | — | If set, the *label* widget is also stored as `setattr(owner, label_bind, label)` — useful for show/hide callbacks |
| `width` | — | Override the schema-level `field_width` for this field only |

### Field types

#### `"line"` — single-line text input

```python
{
    "id":        "span_length",
    "label":     "Span Length (m):",
    "type":      "line",
    "default":   "30.00",
    "validator": {"type": "double_range", "bottom": 1.0, "top": 200.0, "decimals": 2},
    "bind":      "span_length",
    "on_text_changed":    "my_callback",   # fires on every keystroke
    "on_editing_finished":"my_callback",   # fires when focus leaves
}
```

Validator options:

| `type` | Extra keys |
|---|---|
| `"double_range"` | `bottom`, `top`, `decimals` |
| `"int_range"` | `bottom`, `top` |

#### `"combo"` — dropdown

```python
{
    "id":      "girder_type",
    "label":   "Girder Type:",
    "type":    "combo",
    "choices": ["Rolled", "Welded", "Hybrid"],
    "default": "Welded",
    "bind":    "girder_type",
    "on_change": "on_girder_type_changed",   # fires on selection change
}
```

#### `"checkbox"` — boolean toggle

```python
{
    "id":      "include_footpath",
    "label":   "Include Footpath",
    "type":    "checkbox",
    "default": False,
    "bind":    "include_footpath_cb",
}
```

Checkboxes span both columns (no separate label column).

#### `"computed"` / `"read_only"` — display-only output

```python
{
    "id":    "total_load",
    "label": "Total Load (kN/m):",
    "type":  "computed",   # rendered greyed-out, read-only
    "bind":  "total_load_display",
}
```

Your callback writes to it via `self.total_load_display.setText("42.50")`.

#### `"mode_line"` — mode selector + value input side by side

```python
{
    "id":           "dead_load",
    "label":        "Dead Load (kN):",
    "type":         "mode_line",
    "mode_choices": ["Automatic", "Custom"],
    "default_mode": "Automatic",
    "bind_mode":    "dead_load_mode_combo",
    "bind_value":   "dead_load_value_input",
    "placeholder":  "Enter value",
    "on_mode_change": "on_dead_load_mode_changed",
}
```

`get_values()` returns two keys: `"dead_load"` (the mode combo) and
`"dead_load_value"` (the value input).

### Inline multi-field rows (`row_fields`)

Place multiple fields side by side in one grid row:

```python
{
    "row_fields": [
        {"id": "width", "label": "Width (m):", "type": "line", "width": 100},
        {"id": "height","label": "Height (m):","type": "line", "width": 100},
    ]
}
```

---

## Schema layout formats

### `"rows"` — flat list, no section titles

```python
MY_SCHEMA = {
    "id":   "my_tab",
    "rows": [
        {"fields": [field_def, ...]},
        {"fields": [field_def, ...]},
    ],
}
```

Use for simple tabs with one logical group of fields (crash barrier, railing,
wearing course pattern).

### `"sections"` — named sections

```python
MY_SCHEMA = {
    "id":       "my_tab",
    "sections": [
        {"title": "Group A", "fields": [field_def, ...]},
        {"title": "Group B", "fields": [field_def, ...]},
    ],
}
```

Use when fields are logically grouped under headings (temperature load, support
conditions, design options pattern).

### `"cards"` → `"sections"` — card groups each with sections

```python
MY_SCHEMA = {
    "id":    "my_tab",
    "cards": [
        {
            "title":    "Card Heading",
            "sections": [
                {"title": "Sub Group", "fields": [field_def, ...]},
            ],
        },
    ],
}
```

Use for design option panels with multiple card groups (design options pattern).

---

## Callbacks

Callbacks are method names (strings) resolved on the **owner** at build time.
For sub-tabs inside `TypicalSectionDetailsTab` the owner is that class.
For top-level tabs registered directly in `_TAB_REGISTRY` with no explicit
owner, the owner is the tab widget itself.

```python
# In the schema:
"on_editing_finished": "validate_span_length"

# On the owner class:
def validate_span_length(self):
    try:
        val = float(self.span_length.text())
        if val < 1.0:
            self.span_length.setText("1.00")
    except ValueError:
        pass
```

If the owner does not have the named method, the callback is silently skipped
— no crash.

---

## Label visibility (show/hide)

Use `label_bind` to expose a field's label widget on the owner, then toggle
visibility in a callback:

```python
# Schema:
{"id": "my_field", "label": "My Field:", ..., "bind": "my_field", "label_bind": "my_field_label"}

# Callback on owner:
def on_type_changed(self, value):
    show = (value == "Custom")
    self.my_field.setVisible(show)
    self.my_field_label.setVisible(show)
```

---

## Defaults

Define field-level defaults in two places:

1. **`ui_fields_additional_input.py`** — the `"default"` key in the schema dict.
   This is what `reset_defaults()` restores.

2. **`defaults.py`** — the `AI_DEFAULTS` nested dict.
   This seeds the `input_dict` at application startup so every key has a value
   before the user opens the dialog.

Both should always be in sync. The convention is to read from `AI_DEFAULTS` when
building the schema:

```python
# In ui_fields_additional_input.py:
_DEFAULTS = pg_defaults.get_ai_defaults("my_section")

MY_NEW_TAB_SCHEMA = {
    ...
    "fields": [
        {
            "id":      "my_value",
            "default": _DEFAULTS.get("my_value", 1.0),
            ...
        },
    ],
}
```

---

## Value collection

`get_all_values()` on the dialog returns:

```python
{
    "my_new_tab": {
        "my_new_tab": {          # GeneralizedSchemaSubTab wraps one level
            "some_value":  "2.50",
            "some_choice": "Option B",
        }
    },
    "typical_section": {
        "layout":        {"girder_spacing": "3.00", ...},
        "crash_barrier": {"crash_barrier_type": "...", ...},
        ...
    },
    ...
}
```

`input_dock` flattens this two-level structure into the flat `input_dict` used
by the design engine. Every `field["id"]` becomes a key in that dict.

**Field `id` values must therefore be globally unique** across all schemas —
they become keys in the shared design dictionary.

---

