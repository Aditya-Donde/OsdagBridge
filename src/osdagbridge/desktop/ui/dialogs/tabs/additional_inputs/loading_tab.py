from PySide6.QtWidgets import QTabWidget

from osdagbridge.desktop.ui.dialogs.tabs.base import SchemaTab
from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import LOADING_ORCHESTRATOR_SCHEMA

_LOADING_TAB_ATTRS = (
    "permanent_load_tab",
    "live_load_tab",
    "seismic_load_tab",
    "wind_load_tab",
    "temperature_load_tab",
    "custom_load_tab",
    "load_combination_tab",
)


class LoadingTab(SchemaTab):
    """Container for all load sub-tabs."""

    schema = LOADING_ORCHESTRATOR_SCHEMA

    def __init__(self, parent=None):
        # Vehicle lists must exist before super().__init__() because sub-tabs
        # reference them during the schema build triggered by SchemaTab.__init__.
        self.irc_vehicle_checkboxes = []
        self.irc_vehicle_labels = []
        self.braking_vehicle_checkboxes = []
        self.braking_vehicle_labels = []
        self.custom_load_items = []
        self.load_combo_items = []

        super().__init__(parent=parent)

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
        for attr in _LOADING_TAB_ATTRS:
            tab = getattr(self, attr, None)
            if tab is None:
                continue
            restore = getattr(tab, "restore_data", None)
            if callable(restore):
                restore(self._with_legacy_prefixed_keys(data, attr))

    @staticmethod
    def _with_legacy_prefixed_keys(data: dict, tab_attr: str) -> dict:
        if not isinstance(data, dict):
            return {}
        enriched = dict(data)
        prefix = f"{tab_attr}."
        for key, value in data.items():
            if isinstance(key, str) and key.startswith(prefix):
                enriched.setdefault(key[len(prefix):], value)
        return enriched

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
