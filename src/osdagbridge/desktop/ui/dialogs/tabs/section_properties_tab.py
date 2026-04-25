"""Member Properties container tab."""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QTabWidget, QVBoxLayout, QWidget

from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import (
    MEMBER_PROPERTIES_SCHEMA_V1,
)
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.cross_bracing_details_tab import (
    CrossBracingDetailsTab,
)
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.end_diaphragm_details_tab import (
    EndDiaphragmDetailsTab,
)
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.girder_details_tab import (
    GirderDetailsTab,
)
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.stiffener_details_tab import (
    StiffenerDetailsTab,
)


_TAB_CLASS_REGISTRY = {
    "girder_details": GirderDetailsTab,
    "stiffener_details": StiffenerDetailsTab,
    "cross_bracing_details": CrossBracingDetailsTab,
    "end_diaphragm_details": EndDiaphragmDetailsTab,
}

_TAB_SPECS = (
    {
        "key": "girder_details",
        "attr": "girder_details_tab",
        "title": "Girder Details",
        "save_key": "girder_details",
        "collect_method": "collect_data",
        "restore_method": "restore_data",
    },
    {
        "key": "stiffener_details",
        "attr": "stiffener_details_tab",
        "title": "Stiffener Details",
        "save_key": "stiffener_details",
        "collect_method": "collect_data",
        "restore_method": "restore_data",
        "refresh_method": "refresh_girder_members",
        "validate_method": "validate",
    },
    {
        "key": "cross_bracing_details",
        "attr": "cross_bracing_tab",
        "title": "Cross-Bracing Details",
        "save_key": "cross_bracing",
        "collect_method": "collect_data",
        "restore_method": "restore_data",
        "refresh_method": "refresh_girder_options",
        "legacy_alias": "cross_bracing_details_tab",
    },
    {
        "key": "end_diaphragm_details",
        "attr": "end_diaphragm_tab",
        "title": "End Diaphragm Details",
        "save_key": "end_diaphragm",
        "collect_method": "collect_data",
        "restore_method": "restore_data",
        "refresh_method": "refresh_girder_options",
        "legacy_alias": "end_diaphragm_details_tab",
    },
)


class SectionPropertiesTab(QWidget):
    """Sub-tab for Member Properties with schema-backed tab registration."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_section_tab_index = 0
        self._init_ui()
        self._bind_dependents()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._content_frame = QFrame()
        self._content_frame.setFrameShape(QFrame.NoFrame)
        content_layout = QVBoxLayout(self._content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.section_tabs = QTabWidget()
        self.section_tabs.setDocumentMode(True)
        self.section_tabs.setStyleSheet(
            "QTabWidget::pane { border: none; background: #f5f5f5; }"
            "QTabBar::tab { background: #e8e8e8; color: #4b4b4b; border: 1px solid #cfcfcf;"
            " border-bottom: none; padding: 8px 20px; margin-right: 2px; min-width: 120px;"
            " font-size: 11px; }"
            "QTabBar::tab:selected { background: #90AF13; color: #ffffff; font-weight: bold; }"
            "QTabBar::tab:!selected { margin-top: 2px; }"
        )

        tabs_schema = (MEMBER_PROPERTIES_SCHEMA_V1.get("tabs") or {})
        for spec in _TAB_SPECS:
            key = spec["key"]
            tab_schema = tabs_schema.get(key, {})
            tab_cls = _TAB_CLASS_REGISTRY[key]
            widget = tab_cls()
            setattr(self, spec["attr"], widget)

            legacy_alias = spec.get("legacy_alias")
            if legacy_alias:
                setattr(self, str(legacy_alias), widget)

            title = tab_schema.get("title") or spec["title"]
            self.section_tabs.addTab(widget, title)

        content_layout.addWidget(self.section_tabs)
        main_layout.addWidget(self._content_frame)

        try:
            self.section_tabs.currentChanged.connect(self._on_section_tab_changed)
            self._last_section_tab_index = self.section_tabs.currentIndex()
        except Exception:
            self._last_section_tab_index = 0

    def _bind_dependents(self) -> None:
        girder = getattr(self, "girder_details_tab", None)
        if girder is None:
            return

        for attr in ("stiffener_details_tab", "cross_bracing_tab", "end_diaphragm_tab"):
            tab = getattr(self, attr, None)
            bind_method = getattr(tab, "bind_girder_details_tab", None) if tab is not None else None
            if callable(bind_method):
                try:
                    bind_method(girder)
                except Exception:
                    pass

        cross_bracing = getattr(self, "cross_bracing_tab", None)
        if cross_bracing is not None and hasattr(cross_bracing, "spacing_input"):
            try:
                setattr(cross_bracing, "bracing_spacing", cross_bracing.spacing_input)
            except Exception:
                pass

    def _dependent_specs(self):
        return [spec for spec in _TAB_SPECS if spec["key"] != "girder_details"]

    def _refresh_from_girder(self, *keys: str) -> None:
        refresh_keys = set(keys) if keys else {spec["key"] for spec in self._dependent_specs()}
        for spec in self._dependent_specs():
            if spec["key"] not in refresh_keys:
                continue
            widget = getattr(self, spec["attr"], None)
            refresh = getattr(widget, spec.get("refresh_method", ""), None) if widget is not None else None
            if callable(refresh):
                try:
                    refresh()
                except Exception:
                    pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_lock_overlay_geometry()

    def _update_lock_overlay_geometry(self):
        return

    def set_editable_mode(self, editable: bool) -> None:
        for spec in _TAB_SPECS:
            widget = getattr(self, spec["attr"], None)
            setter = getattr(widget, "set_editable_mode", None) if widget is not None else None
            if callable(setter):
                try:
                    setter(bool(editable))
                except Exception:
                    pass

    def set_design_mode(self, mode_str: str) -> None:
        for key in ("girder_details", "cross_bracing_details", "end_diaphragm_details"):
            spec = next((entry for entry in _TAB_SPECS if entry["key"] == key), None)
            if spec is None:
                continue
            widget = getattr(self, spec["attr"], None)
            setter = getattr(widget, "set_design_mode", None) if widget is not None else None
            if callable(setter):
                try:
                    setter(mode_str)
                except Exception:
                    pass

    def has_unsaved_changes(self) -> bool:
        girder = getattr(self, "girder_details_tab", None)
        checker = getattr(girder, "has_unsaved_changes", None) if girder is not None else None
        if callable(checker):
            try:
                return bool(checker())
            except Exception:
                return False
        return False

    def _on_section_tab_changed(self, index: int) -> None:
        previous = getattr(self, "_last_section_tab_index", 0)
        girder_tab = getattr(self, "girder_details_tab", None)

        if previous != index and girder_tab is not None:
            try:
                leaving_girder = previous == self.section_tabs.indexOf(girder_tab)
                commit = getattr(girder_tab, "_commit_current_member_state", None)
                if leaving_girder and callable(commit):
                    commit()
            except Exception:
                pass

        try:
            widget = self.section_tabs.widget(index)
        except Exception:
            return

        self._last_section_tab_index = index

        for spec in self._dependent_specs():
            if widget is getattr(self, spec["attr"], None):
                self._refresh_from_girder(spec["key"])
                break

    def set_girder_count(self, count):
        girder = getattr(self, "girder_details_tab", None)
        setter = getattr(girder, "set_girder_count", None) if girder is not None else None
        if callable(setter):
            setter(count)
        self._refresh_from_girder()

    def reset_defaults(self):
        girder = getattr(self, "girder_details_tab", None)
        reset = getattr(girder, "reset_defaults", None) if girder is not None else None
        if callable(reset):
            reset()

        self._refresh_from_girder()

        for spec in self._dependent_specs():
            widget = getattr(self, spec["attr"], None)
            reset = getattr(widget, "reset_defaults", None) if widget is not None else None
            if callable(reset):
                try:
                    reset()
                except Exception:
                    pass

        try:
            self.section_tabs.setCurrentIndex(0)
        except Exception:
            pass

    def reset_active_tab_defaults(self) -> None:
        try:
            active_widget = self.section_tabs.currentWidget()
        except Exception:
            active_widget = None

        if active_widget is None:
            return

        girder = getattr(self, "girder_details_tab", None)
        if active_widget is girder:
            try:
                girder.reset_defaults(preserve_selection=True, preserve_segments=True)
            except TypeError:
                girder.reset_defaults()
            return

        for spec in self._dependent_specs():
            if active_widget is getattr(self, spec["attr"], None):
                self._refresh_from_girder(spec["key"])
                break

        reset = getattr(active_widget, "reset_defaults", None)
        if callable(reset):
            try:
                reset()
            except Exception:
                pass

    def save_properties(self):
        data = {}
        for spec in _TAB_SPECS:
            widget = getattr(self, spec["attr"], None)
            if widget is None:
                continue

            validate = getattr(widget, spec.get("validate_method", ""), None)
            if callable(validate):
                try:
                    validate()
                except Exception:
                    pass

            collect = getattr(widget, spec.get("collect_method", ""), None)
            if callable(collect):
                try:
                    data[spec["save_key"]] = collect()
                except Exception:
                    pass

        return data

    def restore_properties(self, data: dict) -> None:
        if not isinstance(data, dict):
            return

        girder = getattr(self, "girder_details_tab", None)
        girder_restore = getattr(girder, "restore_data", None) if girder is not None else None
        girder_data = data.get("girder_details")
        if isinstance(girder_data, dict) and callable(girder_restore):
            try:
                girder_restore(girder_data)
            except Exception:
                pass

        self._refresh_from_girder()

        for spec in self._dependent_specs():
            widget = getattr(self, spec["attr"], None)
            restore = getattr(widget, spec.get("restore_method", ""), None) if widget is not None else None
            payload = data.get(spec["save_key"])
            if isinstance(payload, dict) and callable(restore):
                try:
                    restore(payload)
                except Exception:
                    pass

        self._refresh_from_girder()
