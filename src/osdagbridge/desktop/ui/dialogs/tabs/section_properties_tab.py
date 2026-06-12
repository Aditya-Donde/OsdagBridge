"""Section Properties tab — four sub-tabs for Member Properties."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame, QTabWidget,
)
from PySide6.QtCore import Qt

from osdagbridge.core.utils.common import *
from osdagbridge.desktop.ui.dialogs.additional_input.ui_builder.common_ui_builder import UIBuilder

from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.cross_bracing_details_tab import CrossBracingDetailsTab


class SectionPropertiesTab(QWidget):
    """Member Properties dialog tab — Girder / Stiffener / Cross-Bracing / End Diaphragm."""

    def __init__(self, additiona_input_instance, parent=None):
        super().__init__(parent)
        self.additional_input_instance = additiona_input_instance
        self.init_ui()

    # ── init ──────────────────────────────────────────────────────────────────

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        content_frame = QFrame()
        content_frame.setFrameShape(QFrame.NoFrame)
        content_layout = QVBoxLayout(content_frame)
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

        # ── Tab 1: Girder Details — built by UIBuilder from schema ────────────
        # owner and additional_input_instance are AdditionalInputs so that
        # bind attrs and _on_field_edited signals land on the correct object.
        from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import GIRDER_DETAILS_SCHEMA
        self.girder_details_tab = UIBuilder(
            owner=self.additional_input_instance,
            schema=GIRDER_DETAILS_SCHEMA,
            card_title="",
            main_widget_object_name=GIRDER_DETAILS_SCHEMA["id"],
            additional_input_instance=self.additional_input_instance,
            with_scroll=True,
        )
        self.girder_details_tab.setObjectName(GIRDER_DETAILS_SCHEMA["id"])

        # ── Tab 1: Girder Details — built by UIBuilder from schema ────────────
        from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import STIFFENER_DETAILS_SCHEMA
        self.stiffener_details_tab = UIBuilder(
            owner=self.additional_input_instance,
            schema=STIFFENER_DETAILS_SCHEMA,
            card_title="",
            main_widget_object_name=STIFFENER_DETAILS_SCHEMA["id"],
            additional_input_instance=self.additional_input_instance,
            with_scroll=True,
        )

        # ── Tabs 3-4: unchanged specialist tabs ───────────────────────────────
        self.cross_bracing_tab     = CrossBracingDetailsTab()

        from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import END_DIAPHRAGM_DETAILS_SCHEMA
        self.end_diaphragm_tab = UIBuilder(
            owner=self.additional_input_instance,
            schema=END_DIAPHRAGM_DETAILS_SCHEMA,
            card_title="",
            main_widget_object_name=END_DIAPHRAGM_DETAILS_SCHEMA["id"],
            additional_input_instance=self.additional_input_instance,
            with_scroll=True,
        )

        self.section_tabs.addTab(self.girder_details_tab,     "Girder Details")
        self.section_tabs.addTab(self.stiffener_details_tab,  "Stiffener Details")
        self.section_tabs.addTab(self.cross_bracing_tab,      "Cross-Bracing Details")
        self.section_tabs.addTab(self.end_diaphragm_tab,      "End Diaphragm Details")
        self._last_section_tab_index = self.section_tabs.currentIndex()

        content_layout.addWidget(self.section_tabs)
        main_layout.addWidget(content_frame)

        # Cross-tab bindings
        try:
            self.stiffener_details_tab.bind_girder_details_tab(self.girder_details_tab)
        except Exception:
            pass
        try:
            self.cross_bracing_tab.bind_girder_details_tab(self.girder_details_tab)
        except Exception:
            pass
        try:
            self.end_diaphragm_tab.bind_girder_details_tab(self.girder_details_tab)
        except Exception:
            pass

        self.section_tabs.currentChanged.connect(self._on_section_tab_changed)

    # ── tab-switch handler ────────────────────────────────────────────────────

    def _on_section_tab_changed(self, index: int) -> None:
        previous = getattr(self, "_last_section_tab_index", 0)

        if previous != index:
            try:
                if previous == self.section_tabs.indexOf(self.girder_details_tab):
                    if hasattr(self.girder_details_tab, "_commit_current_member_state"):
                        self.girder_details_tab._commit_current_member_state()
            except Exception:
                pass

        self._last_section_tab_index = index
        widget = self.section_tabs.widget(index)

        if widget is self.stiffener_details_tab:
            try:
                self.stiffener_details_tab.refresh_girder_members()
            except Exception:
                pass
        elif widget is self.cross_bracing_tab:
            try:
                self.cross_bracing_tab.refresh_girder_options()
            except Exception:
                pass
        elif widget is self.end_diaphragm_tab:
            try:
                self.end_diaphragm_tab.refresh_girder_options()
            except Exception:
                pass

    # ── public API (forwarded to sub-tabs) ───────────────────────────────────

    def set_editable_mode(self, editable: bool) -> None:
        pass

    def has_unsaved_changes(self) -> bool:
        try:
            if hasattr(self.girder_details_tab, "has_unsaved_changes"):
                return bool(self.girder_details_tab.has_unsaved_changes())
        except Exception:
            pass
        return False

    def set_girder_count(self, count) -> None:
        if hasattr(self.girder_details_tab, "set_girder_count"):
            try:
                self.girder_details_tab.set_girder_count(count)
            except Exception:
                pass
        for tab in (self.stiffener_details_tab, self.cross_bracing_tab, self.end_diaphragm_tab):
            for method in ("refresh_girder_members", "refresh_girder_options"):
                if hasattr(tab, method):
                    try:
                        getattr(tab, method)()
                    except Exception:
                        pass

    def reset_defaults(self) -> None:
        if hasattr(self.girder_details_tab, "reset_defaults"):
            try:
                self.girder_details_tab.reset_defaults()
            except Exception:
                pass
        for tab in (self.stiffener_details_tab, self.cross_bracing_tab, self.end_diaphragm_tab):
            for method in ("refresh_girder_members", "refresh_girder_options"):
                if hasattr(tab, method):
                    try:
                        getattr(tab, method)()
                    except Exception:
                        pass
            if hasattr(tab, "reset_defaults"):
                try:
                    tab.reset_defaults()
                except Exception:
                    pass
        try:
            self.section_tabs.setCurrentIndex(0)
        except Exception:
            pass

    def reset_active_tab_defaults(self) -> None:
        try:
            active = self.section_tabs.currentWidget()
        except Exception:
            return

        if active is self.girder_details_tab:
            try:
                self.girder_details_tab.reset_defaults(preserve_selection=True, preserve_segments=True)
            except TypeError:
                try:
                    self.girder_details_tab.reset_defaults()
                except Exception:
                    pass
            return

        if active is self.stiffener_details_tab:
            try:
                self.stiffener_details_tab.refresh_girder_members()
            except Exception:
                pass
        elif active is self.cross_bracing_tab:
            try:
                self.cross_bracing_tab.refresh_girder_options()
            except Exception:
                pass
        elif active is self.end_diaphragm_tab:
            try:
                self.end_diaphragm_tab.refresh_girder_options()
            except Exception:
                pass

        if hasattr(active, "reset_defaults"):
            try:
                active.reset_defaults()
            except Exception:
                pass

    def save_properties(self) -> dict:
        data = {}
        for key, tab, method in [
            ("girder_details",   self.girder_details_tab,    "collect_data"),
            ("stiffener_details",self.stiffener_details_tab, "collect_data"),
            ("cross_bracing",    self.cross_bracing_tab,     "collect_data"),
            ("end_diaphragm",    self.end_diaphragm_tab,     "collect_data"),
        ]:
            if key == "stiffener_details" and hasattr(self.stiffener_details_tab, "validate"):
                try:
                    self.stiffener_details_tab.validate()
                except Exception:
                    pass
            if hasattr(tab, method):
                try:
                    data[key] = getattr(tab, method)()
                except Exception:
                    pass
        return data

    def restore_properties(self, data: dict) -> None:
        if not isinstance(data, dict):
            return
        for key, tab in [
            ("girder_details",    self.girder_details_tab),
            ("stiffener_details", self.stiffener_details_tab),
            ("cross_bracing",     self.cross_bracing_tab),
            ("end_diaphragm",     self.end_diaphragm_tab),
        ]:
            value = data.get(key)
            if isinstance(value, dict) and hasattr(tab, "restore_data"):
                try:
                    tab.restore_data(value)
                except Exception:
                    pass

        for tab, method in [
            (self.stiffener_details_tab, "refresh_girder_members"),
            (self.cross_bracing_tab,     "refresh_girder_options"),
            (self.end_diaphragm_tab,     "refresh_girder_options"),
        ]:
            if hasattr(tab, method):
                try:
                    getattr(tab, method)()
                except Exception:
                    pass