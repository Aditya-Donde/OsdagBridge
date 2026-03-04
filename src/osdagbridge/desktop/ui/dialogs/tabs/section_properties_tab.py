"""Auto-generated tab module extracted from additional_inputs."""
import sys
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTabBar, QLabel, QLineEdit,
    QComboBox, QGroupBox, QFormLayout, QPushButton, QScrollArea,
    QCheckBox, QMessageBox, QSizePolicy, QSpacerItem, QStackedWidget,
    QFrame, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QDialog, QSizePolicy, QSizeGrip, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QDoubleValidator, QIntValidator, QColor

from osdagbridge.core.utils.common import *
from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.girder_details_tab import GirderDetailsTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.stiffener_details_tab import StiffenerDetailsTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.cross_bracing_details_tab import CrossBracingDetailsTab
from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.end_diaphragm_details_tab import EndDiaphragmDetailsTab

class SectionPropertiesTab(QWidget):
    """Sub-tab for Section Properties with QTabWidget navigation like Loading tab."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Initialize styled tab navigation matching Loading subtabs."""
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

        self.girder_details_tab = GirderDetailsTab()
        self.stiffener_details_tab = StiffenerDetailsTab()
        self.cross_bracing_tab = CrossBracingDetailsTab()
        self.end_diaphragm_tab = EndDiaphragmDetailsTab()

        self.section_tabs.addTab(self.girder_details_tab, "Girder Details")
        self.section_tabs.addTab(self.stiffener_details_tab, "Stiffener Details")
        self.section_tabs.addTab(self.cross_bracing_tab, "Cross-Bracing Details")
        self.section_tabs.addTab(self.end_diaphragm_tab, "End Diaphragm Details")
        self._last_section_tab_index = self.section_tabs.currentIndex()

        content_layout.addWidget(self.section_tabs)
        main_layout.addWidget(self._content_frame)

        # Bind stiffener tab to the girder tab for member list + optimized state.
        try:
            self.stiffener_details_tab.bind_girder_details_tab(self.girder_details_tab)
        except Exception:
            pass

        # Bind Cross Bracing + End Diaphragm to Girder Details for dynamic girder options.
        try:
            self.cross_bracing_tab.bind_girder_details_tab(self.girder_details_tab)
        except Exception:
            pass
        try:
            self.end_diaphragm_tab.bind_girder_details_tab(self.girder_details_tab)
        except Exception:
            pass

        # Refresh stiffener members whenever the tab becomes active.
        try:
            self.section_tabs.currentChanged.connect(self._on_section_tab_changed)
        except Exception:
            pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_lock_overlay_geometry()

    def _update_lock_overlay_geometry(self):
        return

    def set_editable_mode(self, editable: bool) -> None:
        pass

    def set_design_mode(self, mode_str: str) -> None:
        if hasattr(self, "girder_details_tab") and hasattr(self.girder_details_tab, "set_design_mode"):
            self.girder_details_tab.set_design_mode(mode_str)
        if hasattr(self, "cross_bracing_tab") and hasattr(self.cross_bracing_tab, "set_design_mode"):
            self.cross_bracing_tab.set_design_mode(mode_str)
        if hasattr(self, "end_diaphragm_tab") and hasattr(self.end_diaphragm_tab, "set_design_mode"):
            self.end_diaphragm_tab.set_design_mode(mode_str)

    def has_unsaved_changes(self) -> bool:
        try:
            if hasattr(self, "girder_details_tab") and hasattr(self.girder_details_tab, "has_unsaved_changes"):
                return bool(self.girder_details_tab.has_unsaved_changes())
        except Exception:
            pass
        return False

    def _on_section_tab_changed(self, index: int) -> None:
        previous = getattr(self, "_last_section_tab_index", 0)
        if previous != index:
            try:
                leaving_girder_tab = previous == self.section_tabs.indexOf(getattr(self, "girder_details_tab", None))
                if leaving_girder_tab and hasattr(self, "girder_details_tab") and hasattr(self.girder_details_tab, "has_unsaved_changes"):
                    if self.girder_details_tab.has_unsaved_changes():
                        box = QMessageBox(self)
                        box.setIcon(QMessageBox.Warning)
                        box.setWindowTitle("Unsaved Inputs")
                        box.setText("Please save Member Properties before switching tabs.")
                        box.setStandardButtons(QMessageBox.Ok)
                        box.setDefaultButton(QMessageBox.Ok)
                        box.setWindowModality(Qt.ApplicationModal)
                        box.exec()
                        prev = self.section_tabs.blockSignals(True)
                        self.section_tabs.setCurrentIndex(previous)
                        self.section_tabs.blockSignals(prev)
                        return
            except Exception:
                pass

        try:
            widget = self.section_tabs.widget(index)
        except Exception:
            return

        self._last_section_tab_index = index

        if widget is getattr(self, "stiffener_details_tab", None):
            try:
                self.stiffener_details_tab.refresh_girder_members()
            except Exception:
                pass
        elif widget is getattr(self, "cross_bracing_tab", None):
            try:
                self.cross_bracing_tab.refresh_girder_options()
            except Exception:
                pass
        elif widget is getattr(self, "end_diaphragm_tab", None):
            try:
                self.end_diaphragm_tab.refresh_girder_options()
            except Exception:
                pass

    def set_girder_count(self, count):
        if hasattr(self, "girder_details_tab") and hasattr(self.girder_details_tab, "set_girder_count"):
            self.girder_details_tab.set_girder_count(count)
        # Keep dependent tabs in sync.
        try:
            self.stiffener_details_tab.refresh_girder_members()
        except Exception:
            pass
        try:
            self.cross_bracing_tab.refresh_girder_options()
        except Exception:
            pass
        try:
            self.end_diaphragm_tab.refresh_girder_options()
        except Exception:
            pass

    def reset_defaults(self):
        """Reset the entire Member Properties area back to its initial/default state."""

        # Reset girder first so dependent tabs get a fresh member/pair list.
        if hasattr(self, "girder_details_tab") and hasattr(self.girder_details_tab, "reset_defaults"):
            self.girder_details_tab.reset_defaults()

        # Ensure dependent tabs see updated girder/member options.
        try:
            self.stiffener_details_tab.refresh_girder_members()
        except Exception:
            pass
        try:
            self.cross_bracing_tab.refresh_girder_options()
        except Exception:
            pass
        try:
            self.end_diaphragm_tab.refresh_girder_options()
        except Exception:
            pass

        # Now reset each dependent tab's own stored state.
        if hasattr(self, "stiffener_details_tab") and hasattr(self.stiffener_details_tab, "reset_defaults"):
            self.stiffener_details_tab.reset_defaults()
        if hasattr(self, "cross_bracing_tab") and hasattr(self.cross_bracing_tab, "reset_defaults"):
            self.cross_bracing_tab.reset_defaults()
        if hasattr(self, "end_diaphragm_tab") and hasattr(self.end_diaphragm_tab, "reset_defaults"):
            self.end_diaphragm_tab.reset_defaults()

        # Default to the first sub-tab for a consistent UX.
        try:
            self.section_tabs.setCurrentIndex(0)
        except Exception:
            pass

    def reset_active_tab_defaults(self) -> None:
        """Reset only the currently active Member Properties sub-tab.

        This is used by the dialog-level Defaults button to avoid wiping other
        Member Properties tabs' inputs.
        """

        try:
            active_widget = self.section_tabs.currentWidget()
        except Exception:
            active_widget = None

        if active_widget is None:
            return

        # Girder Details has extra selection widgets (girder selector + segment table)
        # that should not be reset when applying defaults for just this tab.
        if active_widget is getattr(self, "girder_details_tab", None):
            try:
                self.girder_details_tab.reset_defaults(preserve_selection=True, preserve_segments=True)
            except TypeError:
                # Backward compatibility if signature differs.
                self.girder_details_tab.reset_defaults()
            return

        # Dependent tabs rely on Girder Details for member/girder options.
        # Ensure options are fresh but do not alter Girder Details state.
        if active_widget is getattr(self, "stiffener_details_tab", None):
            try:
                self.stiffener_details_tab.refresh_girder_members()
            except Exception:
                pass
        elif active_widget is getattr(self, "cross_bracing_tab", None):
            try:
                self.cross_bracing_tab.refresh_girder_options()
            except Exception:
                pass
        elif active_widget is getattr(self, "end_diaphragm_tab", None):
            try:
                self.end_diaphragm_tab.refresh_girder_options()
            except Exception:
                pass

        if hasattr(active_widget, "reset_defaults"):
            try:
                active_widget.reset_defaults()
            except Exception:
                pass

    def save_properties(self):
        data = {}
        if hasattr(self, "girder_details_tab") and hasattr(self.girder_details_tab, "collect_data"):
            data["girder_details"] = self.girder_details_tab.collect_data()
        if hasattr(self, "stiffener_details_tab"):
            # Validate stiffener inputs before saving.
            if hasattr(self.stiffener_details_tab, "validate"):
                self.stiffener_details_tab.validate()
            if hasattr(self.stiffener_details_tab, "collect_data"):
                data["stiffener_details"] = self.stiffener_details_tab.collect_data()
        if hasattr(self, "cross_bracing_tab") and hasattr(self.cross_bracing_tab, "collect_data"):
            data["cross_bracing"] = self.cross_bracing_tab.collect_data()
        if hasattr(self, "end_diaphragm_tab") and hasattr(self.end_diaphragm_tab, "collect_data"):
            data["end_diaphragm"] = self.end_diaphragm_tab.collect_data()
        return data

    def restore_properties(self, data: dict) -> None:
        """Restore previously saved properties into the sub-tabs."""
        if not isinstance(data, dict):
            return

        girder_data = data.get("girder_details")
        if isinstance(girder_data, dict) and hasattr(self, "girder_details_tab") and hasattr(self.girder_details_tab, "restore_data"):
            try:
                self.girder_details_tab.restore_data(girder_data)
            except Exception:
                pass

        stiffener_data = data.get("stiffener_details")
        if isinstance(stiffener_data, dict) and hasattr(self, "stiffener_details_tab") and hasattr(self.stiffener_details_tab, "restore_data"):
            try:
                self.stiffener_details_tab.restore_data(stiffener_data)
            except Exception:
                pass

        cross_data = data.get("cross_bracing")
        if isinstance(cross_data, dict) and hasattr(self, "cross_bracing_tab") and hasattr(self.cross_bracing_tab, "restore_data"):
            try:
                self.cross_bracing_tab.restore_data(cross_data)
            except Exception:
                pass

        end_data = data.get("end_diaphragm")
        if isinstance(end_data, dict) and hasattr(self, "end_diaphragm_tab") and hasattr(self.end_diaphragm_tab, "restore_data"):
            try:
                self.end_diaphragm_tab.restore_data(end_data)
            except Exception:
                pass

        # If stiffeners were restored, refresh member list (depends on girder segments).
        try:
            if hasattr(self, "stiffener_details_tab") and hasattr(self.stiffener_details_tab, "refresh_girder_members"):
                self.stiffener_details_tab.refresh_girder_members()
        except Exception:
            pass

        # Dependent tabs rely on Girder Details for selector options.
        try:
            if hasattr(self, "cross_bracing_tab") and hasattr(self.cross_bracing_tab, "refresh_girder_options"):
                self.cross_bracing_tab.refresh_girder_options()
        except Exception:
            pass
        try:
            if hasattr(self, "end_diaphragm_tab") and hasattr(self.end_diaphragm_tab, "refresh_girder_options"):
                self.end_diaphragm_tab.refresh_girder_options()
        except Exception:
            pass

