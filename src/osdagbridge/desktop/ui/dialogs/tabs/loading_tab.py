from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QFrame,
    QGridLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QCheckBox,
    QSizePolicy,
)
from PySide6.QtCore import Qt

from osdagbridge.core.utils.common import VALUES_YES_NO
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.desktop.ui.dialogs.tabs.custom_vehicle_dialog import CustomVehicleDialog
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.loading.permanent_load_tab import PermanentLoadTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.loading.live_load_tab import LiveLoadTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.loading.seismic_load_tab import SeismicLoadTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.loading.wind_load_tab import WindLoadTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.loading.temperature_load_tab import TemperatureLoadTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.loading.custom_load_tab import CustomLoadTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.loading.load_combination_tab import LoadCombinationTab


class LoadingTab(QWidget):
    """Container for all load sub-tabs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.custom_vehicle_dialog = CustomVehicleDialog(self)
        self.custom_load_items = []
        self.load_combo_items = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.load_tabs = QTabWidget()
        self.load_tabs.setDocumentMode(True)
        self.load_tabs.setStyleSheet(
            "QTabWidget::pane { border: none; background: #f5f5f5; }"
            "QTabBar::tab { background: #e8e8e8; color: #4b4b4b; border: 1px solid #cfcfcf;"
            " border-bottom: none; padding: 8px 20px; margin-right: 2px; min-width: 120px;"
            " font-size: 11px; }"
            "QTabBar::tab:selected { background: #90AF13; color: #ffffff; font-weight: bold; }"
            "QTabBar::tab:!selected { margin-top: 2px; }"
        )

        self.load_tabs.addTab(PermanentLoadTab(self), "Permanent Load")
        self.load_tabs.addTab(LiveLoadTab(self), "Live Load")
        self.load_tabs.addTab(SeismicLoadTab(self), "Seismic Load")
        self.load_tabs.addTab(WindLoadTab(self), "Wind Load")
        self.load_tabs.addTab(TemperatureLoadTab(self), "Temperature Load")
        self.load_tabs.addTab(CustomLoadTab(self), "Custom Load")
        self.load_tabs.addTab(LoadCombinationTab(self), "Load Combination")

        layout.addWidget(self.load_tabs)

    def _create_card(self):
        card = QFrame()
        card.setStyleSheet("QFrame { border: 1px solid #cfcfcf; border-radius: 12px; background-color: #ffffff; }")
        return card

    def _create_yes_no_combo(self):
        combo = QComboBox()
        combo.addItems(VALUES_YES_NO)
        combo.setCurrentText("Yes")
        apply_field_style(combo)
        return combo

    def _create_line_edit(self):
        line_edit = QLineEdit()
        apply_field_style(line_edit)
        return line_edit

    def _add_load_section(self, parent_layout, title, rows):
        title_label = QLabel(title)
        title_label.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: #3e3e3e; background: transparent; border: none;"
        )
        parent_layout.addWidget(title_label)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        grid.setColumnMinimumWidth(0, 230)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)

        field_width = 170

        for row_index, (label_text, widget) in enumerate(rows):
            label = QLabel(label_text)
            label.setStyleSheet("font-size: 11px; color: #4b4b4b; background: transparent; border: none;")
            grid.addWidget(label, row_index, 0, Qt.AlignLeft | Qt.AlignVCenter)
            widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            if isinstance(widget, (QComboBox, QLineEdit)):
                widget.setFixedWidth(field_width)
            grid.addWidget(widget, row_index, 1)

        parent_layout.addLayout(grid)

    def _add_checkbox_section(self, parent_layout, title, items):
        title_label = QLabel(title)
        title_label.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: #3e3e3e; background: transparent; border: none;"
        )
        parent_layout.addWidget(title_label)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        grid.setColumnStretch(0, 1)

        for row, name in enumerate(items):
            label = QLabel(name)
            if "Vehicle Name" in name:
                label.setStyleSheet(
                    "font-size: 11px; font-style: italic; color: #4b4b4b; background: transparent; border: none; padding: 0px;"
                )
            else:
                label.setStyleSheet(
                    "font-size: 11px; color: #4b4b4b; background: transparent; border: none; padding: 0px;"
                )
            checkbox = QCheckBox()
            checkbox.setChecked(False)
            grid.addWidget(label, row, 0, Qt.AlignLeft | Qt.AlignVCenter)
            grid.addWidget(checkbox, row, 1, Qt.AlignRight | Qt.AlignVCenter)

        parent_layout.addLayout(grid)

    def _on_footpath_mode_changed(self, mode):
        is_custom = mode == "User-defined"
        if hasattr(self, "footpath_value_input"):
            self.footpath_value_input.setEnabled(is_custom)
            if not is_custom:
                self.footpath_value_input.clear()

    def _on_dead_load_mode_changed(self, mode):
        is_custom = mode == "Custom"
        if hasattr(self, "dead_load_custom_input"):
            self.dead_load_custom_input.setEnabled(is_custom)
            if not is_custom:
                self.dead_load_custom_input.clear()

    def _on_live_load_mode_changed(self, mode):
        is_custom = mode == "Custom"
        if hasattr(self, "live_load_custom_input"):
            self.live_load_custom_input.setEnabled(is_custom)
            if not is_custom:
                self.live_load_custom_input.clear()

    def show_custom_vehicle_dialog(self):
        self.custom_vehicle_dialog.show()
        self.custom_vehicle_dialog.raise_()
        self.custom_vehicle_dialog.activateWindow()
