from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
)
from osdagbridge.desktop.ui.dialogs.additional_input.common_ui_builder import UIBuilder

class LoadingTab(QWidget):
    """Container for all load sub-tabs."""

    def __init__(
            self, 
            additional_input_instance,
            parent=None):
        super().__init__(parent)
        
        self.additional_input_instance = additional_input_instance
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.load_tabs = QTabWidget()
        self.load_tabs.setDocumentMode(True)

        self.load_tabs.setUsesScrollButtons(True)
        self.load_tabs.tabBar().setExpanding(False)

        self.load_tabs.setMovable(False)

        self.load_tabs.setStyleSheet(
           "QTabBar::scroller {"
            " width: 24px;"
            "}"

            "QTabBar::right-arrow {"
            " image: none;"
            " border: none;"
            " background: transparent;"
            "}"

            "QTabBar::left-arrow {"
            " image: none;"
            " border: none;"
            " background: transparent;"
            "}"

            "QTabBar::left-arrow:!enabled {"
            " width: 0px;"
            "}"

        )

        from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import PERMANENT_LOAD_TAB_SCHEMA
        self.permanent_load_tab = UIBuilder(
            owner=self,
            schema=PERMANENT_LOAD_TAB_SCHEMA,
            card_title="",
            with_scroll=True,
            main_widget_object_name="permanent_load.main",
            additional_input_instance=self.additional_input_instance,
        )
        self.load_tabs.addTab(self.permanent_load_tab, "Permanent Load")

        from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import LIVE_LOAD_TAB_SCHEMA
        self.live_load_tab = UIBuilder(
            owner=self,
            schema=LIVE_LOAD_TAB_SCHEMA,
            card_title="",
            with_scroll=True,
            main_widget_object_name="live_load.main",
            additional_input_instance=self.additional_input_instance,
        )
        self.load_tabs.addTab(self.live_load_tab, "Live Load")

        from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import SEISMIC_LOAD_TAB_SCHEMA
        self.seismic_load_tab = UIBuilder(
            owner=self,
            schema=SEISMIC_LOAD_TAB_SCHEMA,
            card_title="",
            with_scroll=True,
            main_widget_object_name="seismic_load.main",
            additional_input_instance=self.additional_input_instance,
        )
        self.load_tabs.addTab(self.seismic_load_tab, "Seismic Load")

        from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import WIND_LOAD_TAB_SCHEMA
        self.wind_load_tab = UIBuilder(
            owner=self,
            schema=WIND_LOAD_TAB_SCHEMA,
            card_title="",
            with_scroll=True,
            main_widget_object_name="wind_load.main",
            additional_input_instance=self.additional_input_instance,
        )
        self.load_tabs.addTab(self.wind_load_tab, "Wind Load")

        from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import TEMPERATURE_LOAD_TAB_SCHEMA
        self.temperature_load_tab = UIBuilder(
            owner=self,
            schema=TEMPERATURE_LOAD_TAB_SCHEMA,
            card_title="",
            with_scroll=True,
            main_widget_object_name="temperature_load.main",
            additional_input_instance=self.additional_input_instance,
        )
        self.load_tabs.addTab(self.temperature_load_tab, "Temperature Load")

        from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import LOAD_COMBINATION_TAB_SCHEMA
        self.load_combination_tab = UIBuilder(
            owner=self,
            schema=LOAD_COMBINATION_TAB_SCHEMA,
            card_title="",
            with_scroll=True,
            main_widget_object_name="load_combination.main",
            additional_input_instance=self.additional_input_instance,
        )
        self.load_tabs.addTab(self.load_combination_tab, "Load Combination")
        
        layout.addWidget(self.load_tabs)
