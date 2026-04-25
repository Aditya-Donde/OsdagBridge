from PySide6.QtWidgets import QWidget, QTabWidget

from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import LOADING_ORCHESTRATOR_SCHEMA
from osdagbridge.desktop.ui.dialogs.tabs.ui_builder import UIBuilder

_LOADING_TAB_ATTRS = (
    "permanent_load_tab",
    "live_load_tab",
    "seismic_load_tab",
    "wind_load_tab",
    "temperature_load_tab",
    "custom_load_tab",
    "load_combination_tab",
)


class LoadingTab(QWidget):
    """Container for all load sub-tabs."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # REQUIRED for Live Load defaults (referenced by sub-tabs)
        self.irc_vehicle_checkboxes = []
        self.irc_vehicle_labels = []
        self.braking_vehicle_checkboxes = []
        self.braking_vehicle_labels = []

        self._build_ui()

    def _build_ui(self):
        # Build UI from orchestrator schema
        UIBuilder(owner=self, schema=LOADING_ORCHESTRATOR_SCHEMA).build_tab(self)
        
        # UIBuilder sets objectName for the tab container
        self.load_tabs = self.findChild(QTabWidget, "loading_tabs")
        if self.load_tabs:
            self.load_tabs.setDocumentMode(True)
            self.load_tabs.setUsesScrollButtons(True)
            self.load_tabs.tabBar().setExpanding(False)
            self.load_tabs.setMovable(False)
            self.load_tabs.setStyleSheet(
                "QTabBar::scroller { width: 24px; }"
                "QTabBar::right-arrow { image: none; border: none; background: transparent; }"
                "QTabBar::left-arrow { image: none; border: none; background: transparent; }"
                "QTabBar::left-arrow:!enabled { width: 0px; }"
            )

    def _iter_child_tabs(self):
        for attr in _LOADING_TAB_ATTRS:
            tab = getattr(self, attr, None)
            if tab is not None:
                yield tab

    def collect_data(self) -> dict:
        """Unified data collection from all loading sub-tabs."""
        data = {}
        for tab in self._iter_child_tabs():
            collector = getattr(tab, "collect_data", None)
            if callable(collector):
                data.update(collector())
        return data

    def restore_data(self, data: dict) -> None:
        """Unified data restoration to all loading sub-tabs."""
        for tab in self._iter_child_tabs():
            restore = getattr(tab, "restore_data", None)
            if callable(restore):
                restore(data)

    def update_permanent_load_dependencies(self, has_median: bool, has_footpath: bool):
        """Forward dependency updates to sub-tabs."""
        for tab in self._iter_child_tabs():
            update = getattr(tab, "update_dependency_states", None)
            if callable(update):
                update(has_median=has_median, has_footpath=has_footpath)

    def reset_defaults(self):
        """Reset all loading sub-tabs to default values"""
        for tab in self._iter_child_tabs():
            reset = getattr(tab, "reset_defaults", None)
            if callable(reset):
                reset()

    def validate_tab(self):
        errors = []
        for tab in self._iter_child_tabs():
            validate = getattr(tab, "validate_tab", None)
            if callable(validate):
                errors.extend(validate())
        return list(dict.fromkeys(errors))
