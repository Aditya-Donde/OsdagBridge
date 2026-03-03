from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QSizeGrip, QSizePolicy
)
from PySide6.QtCore import Qt

from osdagbridge.desktop.ui.dialogs.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.dialogs.tabs.steel_design_details import SteelDesignDetailsTab
from osdagbridge.desktop.ui.dialogs.tabs.steel_design_analysis import SteelDesignAnalysisTab
from osdagbridge.desktop.ui.dialogs.tabs.steel_design_check import SteelDesignCheckTab


class SteelDesign(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._main_window = parent
        self.setObjectName("SteelDesign")
        self.resize(1024, 720)
        self.setMinimumSize(900, 520)
        self.setSizeGripEnabled(True)
        self.init_ui()
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border: 1px solid #90AF13;
            }
        """)

    def setupWrapper(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        self.title_bar = CustomTitleBar(parent=self)
        self.title_bar.setTitle("Steel Design")
        main_layout.addWidget(self.title_bar)

        self.content_widget = QWidget(self)
        main_layout.addWidget(self.content_widget, 1)

        size_grip = QSizeGrip(self)
        size_grip.setFixedSize(16, 16)

        overlay = QHBoxLayout()
        overlay.setContentsMargins(0, 0, 4, 4)
        overlay.addStretch(1)
        overlay.addWidget(size_grip, 0, Qt.AlignBottom | Qt.AlignRight)
        main_layout.addLayout(overlay)

    def init_ui(self):
        self.setupWrapper()

        main_layout = QVBoxLayout(self.content_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(2)

    

        # ── Tabs ──────────────────────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tabs.setDocumentMode(True)
        self.tabs.tabBar().setExpanding(True)
        self.tabs.tabBar().setUsesScrollButtons(False)
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: none; }
            QTabBar { qproperty-drawBase: 0; }
            QTabBar::tab {
                background: #E6E6E6;
                color: black;
                border: 1px solid #CCCCCC;
                padding: 8px 0px;
                border-radius: 8px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #90AF13;
                color: white;
                font-weight: bold;
                border: 1px solid #90AF13;
            }
            QTabBar::tab:hover { background: #DADADA; }
        """)

        self.details_tab = SteelDesignDetailsTab(self)
        self.tabs.addTab(self.details_tab,             "Details")
        self.tabs.addTab(SteelDesignAnalysisTab(self), "Analysis Results")
        self.tabs.addTab(SteelDesignCheckTab(self),    "Design Check")

        main_layout.addWidget(self.tabs)

        if hasattr(self._main_window, "cad_state"):
            self.details_tab.load_data(self._main_window.cad_state)