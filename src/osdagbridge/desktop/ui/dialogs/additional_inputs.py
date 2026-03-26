"""
Additional Inputs dialog for Highway Bridge Design.

Architecture
------------
Every top-level tab is declared once in ``_TAB_REGISTRY`` as a single dict::

    {"id": ..., "label": ..., "factory": lambda dlg: <widget>}

``init_ui`` iterates the registry to build and register every tab — no per-tab
code anywhere else.  ``get_all_values`` does the same to collect values.
Adding a new tab = one entry in the registry.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTabBar, QLineEdit,
    QComboBox, QPushButton, QCheckBox, QMessageBox, QSizePolicy,
    QFrame, QDialog, QSizeGrip,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDoubleValidator

from osdagbridge.core.utils.common import *
from osdagbridge.core.bridge_types.plate_girder.validator import BridgeInputValidator
from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox, MessageBoxType
from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.dialogs.tabs.typical_section_details import TypicalSectionDetailsTab
from osdagbridge.desktop.ui.dialogs.tabs.section_properties_tab import SectionPropertiesTab
from osdagbridge.desktop.ui.dialogs.tabs.loading_tab import LoadingTab
from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import (
    SUPPORT_CONDITIONS_SCHEMA,
    DESIGN_OPTIONS_SCHEMA,
    DESIGN_OPTIONS_CONT_SCHEMA,
)
from osdagbridge.desktop.ui.dialogs.tabs.generalized_schema_tab import GeneralizedSchemaSubTab


def _make_schema_tab(schema: dict):
    """Build a generalized schema tab with dialog-managed validation hooks."""
    return lambda dlg: GeneralizedSchemaSubTab(
        schema,
        validation_handler=dlg._validate_schema_field,
    )

# ── Tab registry ──────────────────────────────────────────────────────────────
# One entry per top-level tab.  ``factory(dlg)`` receives the dialog instance
# so it can pass constructor args (e.g. footpath_value) without any per-tab
# hardcoding in init_ui.
#
# To add a new tab: append one dict here.  Nothing else needs to change.
# ─────────────────────────────────────────────────────────────────────────────
_TAB_REGISTRY = [
    {
        "id":      "typical_section",
        "label":   "Typical Section Details",
        "factory": lambda dlg: TypicalSectionDetailsTab(dlg.footpath_value, dlg.carriageway_width),
    },
    {
        "id":      "member_properties",
        "label":   "Member Properties",
        "factory": lambda dlg: SectionPropertiesTab(),
    },
    {
        "id":      "loading",
        "label":   "Loading",
        "factory": lambda dlg: LoadingTab(),
    },
    {
        "id":      "support_conditions",
        "label":   "Support Conditions",
        "factory": _make_schema_tab(SUPPORT_CONDITIONS_SCHEMA),
    },
    {
        "id":      "design_options",
        "label":   "Analysis/Design Options",
        "factory": _make_schema_tab(DESIGN_OPTIONS_SCHEMA),
    },
    {
        "id":      "design_options_cont",
        "label":   "Design Options (Cont.)",
        "factory": _make_schema_tab(DESIGN_OPTIONS_CONT_SCHEMA),
    },
]

# Button styles ───────────────────────────────────────────────────────────────
_BTN_STYLE = (
    "QPushButton { background:#ffffff; color:#2f2f2f; font-weight:600;"
    "  border:1px solid #8c8c8c; border-radius:4px; padding:6px 24px; min-width:110px; }"
    "QPushButton:hover { background:#f6f6f6; }"
    "QPushButton:pressed { background:#e0e0e0; }"
)
_BTN_PRIMARY_STYLE = (
    "QPushButton { background:#90AF13; color:#ffffff; font-weight:600;"
    "  border:1px solid #7a9a12; border-radius:4px; padding:6px 24px; min-width:120px; }"
    "QPushButton:hover { background:#7a9a12; }"
    "QPushButton:pressed { background:#6b8a10; }"
)
_TAB_STYLE = """
    QTabWidget::pane {
        border: 1px solid #d1d1d1;
        background-color: #ffffff;
        border-radius: 6px;
    }
    QTabBar::tab {
        font-weight: bold;
        font-size: 12px;
        background: #ffffff;
        color: #3a3a3a;
        border: 1px solid #d1d1d1;
        padding: 10px 22px;
    }
    QTabBar::tab:selected {
        background: #90AF13;
        color: #ffffff;
        border: 1px solid #90AF13;
    }
    QTabBar::tab:hover {
        background: #90AF13;
        color: #ffffff;
    }
"""


class AdditionalInputs(QDialog):
    """Tabbed dialog for additional bridge design inputs.

    All tabs are declared in ``_TAB_REGISTRY``.  The dialog loops through the
    registry to build the UI and to collect values — there is no per-tab logic
    anywhere in this class.
    """

    values_changed = Signal(dict)  # emitted whenever any field changes

    def __init__(self, footpath_value="None", carriageway_width=7.5, base_values=None, parent=None):
        super().__init__(parent)
        self.setObjectName("AdditionalInputs")
        self.resize(1024, 720)
        self.setMinimumSize(900, 520)
        self.setSizeGripEnabled(True)
        self.footpath_value    = footpath_value
        self.carriageway_width = carriageway_width
        self._base_input_context = dict(base_values or {})
        self._validator = BridgeInputValidator()
        self._working_values = {}
        self._member_properties_editable = True
        self._last_saved_data = {}
        self._init_ui()
        self.setStyleSheet("QDialog { background-color:#ffffff; border:1px solid #90AF13; }")

    # ── Shell / wrapper ───────────────────────────────────────────────────────

    def _setup_shell(self):
        """Frameless window chrome with custom title bar and size grip."""
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)

        root = QVBoxLayout(self)
        root.setContentsMargins(1, 1, 1, 1)
        root.setSpacing(0)

        self.title_bar = CustomTitleBar()
        self.title_bar.setTitle("Additional Inputs")
        root.addWidget(self.title_bar)

        self.content_widget = QWidget(self)
        root.addWidget(self.content_widget, 1)

        grip = QSizeGrip(self)
        grip.setFixedSize(16, 16)
        overlay = QHBoxLayout()
        overlay.setContentsMargins(0, 0, 4, 4)
        overlay.addStretch(1)
        overlay.addWidget(grip, 0, Qt.AlignBottom | Qt.AlignRight)
        root.addLayout(overlay)

    # ── UI construction ───────────────────────────────────────────────────────

    def _init_ui(self):
        self._setup_shell()

        layout = QVBoxLayout(self.content_widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Tab widget
        tab_bar = QTabBar()
        tab_bar.setElideMode(Qt.ElideRight)
        self.tabs = QTabWidget()
        self.tabs.setTabBar(tab_bar)
        self.tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tabs.setStyleSheet(_TAB_STYLE)
        self.tabs.currentChanged.connect(self._on_tab_changed)

        # Build every tab from the registry — single loop, no per-tab code
        self._build_tabs()

        layout.addWidget(self.tabs)
        layout.addSpacing(6)
        layout.addWidget(self._build_action_bar())

        self._enforce_decimal_places(2)
        self._normalize_numeric_texts(2)
        self._refresh_working_values()

    def _build_tabs(self):
        """Instantiate and register every tab from ``_TAB_REGISTRY``."""
        for cfg in _TAB_REGISTRY:
            widget = cfg["factory"](self)
            setattr(self, f"{cfg['id']}_tab", widget)
            self.tabs.addTab(widget, cfg["label"])
        self._post_tab_wiring()
        self._connect_value_watchers()

    def _post_tab_wiring(self):
        """Cross-tab connections that require both tabs to already exist."""
        try:
            self.typical_section_tab.girder_count_changed.connect(
                self.member_properties_tab.set_girder_count
            )
        except Exception:
            pass
        try:
            self.member_properties_tab.set_editable_mode(self._member_properties_editable)
        except Exception:
            pass

    def _build_action_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("actionButtonBar")
        bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        bar.setStyleSheet(
            "QFrame#actionButtonBar { background:#ededed; border:1px solid #c8c8c8; border-radius:6px; }"
        )
        hl = QHBoxLayout(bar)
        hl.setContentsMargins(22, 10, 22, 10)
        hl.setSpacing(12)
        hl.addStretch()

        self.defaults_button = QPushButton("Defaults")
        self.defaults_button.setStyleSheet(_BTN_STYLE)
        self.defaults_button.clicked.connect(self._apply_defaults)
        hl.addWidget(self.defaults_button)

        self.save_button = QPushButton("Save")
        self.save_button.setStyleSheet(_BTN_PRIMARY_STYLE)
        self.save_button.setToolTip("Save inputs and move to next tab")
        self.save_button.clicked.connect(self._save_and_next)
        hl.addWidget(self.save_button)

        hl.addStretch()
        return bar

    # ── Post-init normalization ───────────────────────────────────────────────

    def _enforce_decimal_places(self, places=2):
        for le in self.findChildren(QLineEdit):
            v = le.validator()
            if isinstance(v, QDoubleValidator):
                v.setDecimals(places)
                v.setNotation(QDoubleValidator.StandardNotation)

    def _normalize_numeric_texts(self, places=2):
        fmt = f"{{:.{places}f}}"
        for le in self.findChildren(QLineEdit):
            text = le.text().strip()
            if not text:
                continue
            try:
                normalized = fmt.format(float(text))
                le.setText(normalized)
                le.setProperty("last_valid_text", normalized)
            except ValueError:
                pass

    # ── Actions ───────────────────────────────────────────────────────────────

    def _apply_defaults(self):
        """Reset the current tab.  Duck-typed — no per-tab branches."""
        widget = self.tabs.currentWidget()
        if widget is None:
            return
        if hasattr(widget, "reset_active_tab_defaults"):
            widget.reset_active_tab_defaults()
        elif hasattr(widget, "reset_defaults"):
            widget.reset_defaults()

    def _save_inputs(self):
        """Persist member properties in memory without closing."""
        try:
            sp = getattr(self, "member_properties_tab", None)
            if sp and hasattr(sp, "save_properties"):
                self._last_saved_data.update(sp.save_properties() or {})
        except Exception:
            pass

    def _save_and_next(self):
        """Save current tab then advance to the next tab; close on the last tab."""
        self._save_inputs()
        current = self.tabs.currentIndex()
        total   = self.tabs.count()
        if current < total - 1:
            self.tabs.setCurrentIndex(current + 1)
        else:
            self.accept()

    def _connect_value_watchers(self):
        """Connect every input widget's change signal to _on_any_value_changed."""
        for le in self.findChildren(QLineEdit):
            le.textChanged.connect(self._on_any_value_changed)
        for cb in self.findChildren(QComboBox):
            cb.currentTextChanged.connect(self._on_any_value_changed)
        for ck in self.findChildren(QCheckBox):
            ck.stateChanged.connect(self._on_any_value_changed)

    def _on_any_value_changed(self, *args):
        """Collect all current values and emit so callers can update in real-time."""
        try:
            self.values_changed.emit(self._refresh_working_values())
        except Exception:
            pass

    def _refresh_working_values(self) -> dict:
        """Snapshot the current dialog state for real-time consumers."""
        self._working_values = self.get_all_values()
        return self._working_values

    def get_working_values(self) -> dict:
        return self._refresh_working_values()

    def _build_validation_context(self) -> dict:
        """Merge external inputs with the dialog's current working values."""
        context = dict(self._base_input_context)
        current_values = self._refresh_working_values()

        for top_tab_data in current_values.values():
            if not isinstance(top_tab_data, dict):
                continue
            for sub_tab_data in top_tab_data.values():
                if isinstance(sub_tab_data, dict):
                    context.update(sub_tab_data)

        return context

    def _validation_fallback_for(self, widget: QLineEdit) -> str:
        last_valid = widget.property("last_valid_text")
        if last_valid not in (None, ""):
            return str(last_valid)

        default = widget.property("schema_default")
        if default not in (None, ""):
            return str(default)

        return ""

    def _validate_schema_field(self, tab_id: str, field_id: str, widget: QLineEdit) -> bool:
        """Focus-out validation bridge for schema-driven tabs."""
        result = self._validator.validate_additional_inputs(
            str(tab_id or "").strip(),
            str(field_id or "").strip(),
            self._build_validation_context(),
        )
        if result is None:
            current_text = widget.text().strip()
            if current_text:
                widget.setProperty("last_valid_text", current_text)
            return True

        corrected, message = result
        replacement = self._validation_fallback_for(widget) if corrected is None else str(corrected)
        if widget.text() != replacement:
            widget.setText(replacement)
        if replacement:
            widget.setProperty("last_valid_text", replacement)

        self._refresh_working_values()
        CustomMessageBox(
            title="Input Error",
            text=message,
            dialogType=MessageBoxType.Warning,
        ).exec()
        return False

    # ── Value collection ──────────────────────────────────────────────────────

    def get_all_values(self) -> dict:
        """Return ``{tab_id: {sub_tab_id: {field: value}}}`` for every tab.

        ``GeneralizedSchemaSubTab.get_values()`` returns a flat
        ``{field: value}`` dict (no sub-tab nesting).  It is wrapped one
        level so all callers can iterate uniformly at two levels.
        """
        result = {}
        for cfg in _TAB_REGISTRY:
            widget = getattr(self, f"{cfg['id']}_tab", None)
            if widget is None or not hasattr(widget, "get_values"):
                continue
            vals = widget.get_values()
            # Normalize: GeneralizedSchemaSubTab returns flat {field: val}.
            # Complex tabs already return {sub_tab: {field: val}}.
            if isinstance(widget, GeneralizedSchemaSubTab):
                result[cfg["id"]] = {cfg["id"]: vals}
            else:
                result[cfg["id"]] = vals
        return result

    # ── Tab signal ────────────────────────────────────────────────────────────

    def _on_tab_changed(self, index: int) -> None:
        pass  # reserved for future use (e.g. lazy loading)

    # ── Public API for input_dock ─────────────────────────────────────────────

    def update_footpath_value(self, footpath_value):
        self.footpath_value = footpath_value
        ts = getattr(self, "typical_section_tab", None)
        if ts and hasattr(ts, "update_footpath_value"):
            ts.update_footpath_value(footpath_value)

    def set_member_properties_design_mode(self, mode_str: str):
        sp = getattr(self, "member_properties_tab", None)
        if sp and hasattr(sp, "set_design_mode"):
            sp.set_design_mode(mode_str)

    def set_member_properties_editable(self, editable: bool) -> None:
        self._member_properties_editable = bool(editable)
        sp = getattr(self, "member_properties_tab", None)
        if sp:
            try:
                sp.set_editable_mode(self._member_properties_editable)
            except Exception:
                pass

    def get_saved_data(self) -> dict:
        return self._last_saved_data

    def set_properties_data(self, data: dict) -> None:
        sp = getattr(self, "member_properties_tab", None)
        if sp and hasattr(sp, "restore_properties"):
            try:
                sp.restore_properties(data)
            except Exception:
                pass
