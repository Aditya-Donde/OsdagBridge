"""Member Properties container tab."""

from __future__ import annotations

from PySide6.QtWidgets import QTabWidget, QWidget

from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import (
    SECTION_PROPERTIES_ORCHESTRATOR_SCHEMA,
)
from osdagbridge.desktop.ui.dialogs.tabs.ui_builder import UIBuilder


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
        # Build UI from orchestrator schema
        UIBuilder(owner=self, schema=SECTION_PROPERTIES_ORCHESTRATOR_SCHEMA).build_tab(self)
        
        # Find the QTabWidget built by UIBuilder
        self.section_tabs = self.findChild(QTabWidget, "section_properties_tabs")
        if self.section_tabs:
            self.section_tabs.setDocumentMode(True)
            self.section_tabs.setStyleSheet(
                "QTabWidget::pane { border: none; background: #f5f5f5; }"
                "QTabBar::tab { background: #e8e8e8; color: #4b4b4b; border: 1px solid #cfcfcf;"
                " border-bottom: none; padding: 8px 20px; margin-right: 2px; min-width: 120px;"
                " font-size: 11px; }"
                "QTabBar::tab:selected { background: #90AF13; color: #ffffff; font-weight: bold; }"
                "QTabBar::tab:!selected { margin-top: 2px; }"
            )
            try:
                self.section_tabs.currentChanged.connect(self._on_section_tab_changed)
                self._last_section_tab_index = self.section_tabs.currentIndex()
            except Exception:
                self._last_section_tab_index = 0

        # Handle legacy aliases if needed
        for spec in _TAB_SPECS:
            legacy_alias = spec.get("legacy_alias")
            if legacy_alias:
                widget = getattr(self, spec["attr"], None)
                if widget:
                    setattr(self, str(legacy_alias), widget)

    def collect_data(self) -> dict:
        """Unified data collection from all section sub-tabs."""
        data = {}
        for spec in _TAB_SPECS:
            tab = getattr(self, spec["attr"], None)
            if hasattr(tab, "collect_data"):
                data.update(tab.collect_data())
        return data

    def save_properties(self) -> dict:
        """Compatibility wrapper used by the dock while the migration is in flight."""
        return self.collect_data()

    def restore_data(self, data: dict) -> None:
        """Unified data restoration to all section sub-tabs."""
        for spec in _TAB_SPECS:
            tab = getattr(self, spec["attr"], None)
            if hasattr(tab, "restore_data"):
                tab.restore_data(data)
        self._refresh_dependency_state()

    def restore_properties(self, data: dict) -> None:
        self.restore_data(data)

    def reset_defaults(self):
        """Unified reset for all section sub-tabs."""
        for spec in _TAB_SPECS:
            tab = getattr(self, spec["attr"], None)
            if hasattr(tab, "reset_defaults"):
                tab.reset_defaults()
        self._refresh_dependency_state()
        try:
            self.section_tabs.setCurrentIndex(0)
        except Exception:
            pass

    def validate_tab(self):
        """Unified validation for all section sub-tabs."""
        errors = []
        for spec in _TAB_SPECS:
            tab = getattr(self, spec["attr"], None)
            validate_method = spec.get("validate_method", "validate_tab")
            method = getattr(tab, validate_method, None)
            if callable(method):
                try:
                    result = method()
                except Exception as exc:
                    errors.append(str(exc))
                    continue
                if isinstance(result, (list, tuple, set)):
                    errors.extend(str(item) for item in result if item)
                elif result:
                    errors.append(str(result))
        return list(dict.fromkeys(errors))

    def _bind_dependents(self) -> None:
        girder = getattr(self, "girder_details_tab", None)
        if girder is None:
            return

        signal = getattr(girder, "dependency_state_changed", None)
        if signal is not None and hasattr(signal, "connect"):
            try:
                signal.connect(self._refresh_dependents_from_state)
            except Exception:
                pass

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
        self._refresh_dependency_state()

    def _refresh_dependents_from_state(self, state: dict) -> None:
        state = dict(state or {})
        for attr in ("stiffener_details_tab", "cross_bracing_tab", "end_diaphragm_tab"):
            tab = getattr(self, attr, None)
            if tab is None:
                continue
            refresh = getattr(tab, "refresh_from_girder_state", None)
            if callable(refresh):
                try:
                    refresh(dict(state))
                except Exception:
                    pass

    def _refresh_dependency_state(self) -> None:
        girder = getattr(self, "girder_details_tab", None)
        if girder is None:
            return

        export_state = getattr(girder, "export_dependency_state", None)
        state = export_state() if callable(export_state) else {}
        self._refresh_dependents_from_state(state)

    def _dependent_specs(self):
        return [spec for spec in _TAB_SPECS if spec["key"] != "girder_details"]

    def _refresh_dependent_tabs(self, *keys: str) -> None:
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

    def _refresh_from_girder(self, *keys: str) -> None:
        self._refresh_dependency_state()
        self._refresh_dependent_tabs(*keys)

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
                commit = getattr(girder_tab, "commit_active_state", None)
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
                self._refresh_dependent_tabs(spec["key"])
                break

    def set_girder_count(self, count):
        girder = getattr(self, "girder_details_tab", None)
        setter = getattr(girder, "set_girder_count", None) if girder is not None else None
        if callable(setter):
            setter(count)

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
                self._refresh_dependent_tabs(spec["key"])
                break

        reset = getattr(active_widget, "reset_defaults", None)
        if callable(reset):
            try:
                reset()
            except Exception:
                pass
