from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

from osdagbridge.core.bridge_types.plate_girder.schemas import LAYOUT_TAB_SCHEMA
from osdagbridge.desktop.ui.dialogs.tabs import schema_io
from osdagbridge.desktop.ui.dialogs.tabs.ui_builder import UIBuilder


class LayoutTab(QWidget):

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        builder = UIBuilder(owner=owner, schema=LAYOUT_TAB_SCHEMA)
        builder.build_tab(self)

        if hasattr(owner, "overall_bridge_width_display") and hasattr(owner, "overall_bridge_width_formula"):
            owner.overall_bridge_width_display.setToolTip(owner.overall_bridge_width_formula)

        self._create_notice_labels(owner, builder.page_layout)

    def reset_defaults(self):
        schema_io.reset_defaults(self.owner, LAYOUT_TAB_SCHEMA)

    def _create_notice_labels(self, owner, page_layout):
        owner.layout_adjust_notice = self._make_notice_label("#000000")
        owner.layout_warning_notice = self._make_notice_label("#cc6600")

        container = QWidget()
        container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        container.setFixedWidth(180)
        vlayout = QVBoxLayout(container)
        vlayout.setContentsMargins(0, 0, 0, 0)
        vlayout.setSpacing(4)
        vlayout.addWidget(owner.layout_adjust_notice)
        vlayout.addWidget(owner.layout_warning_notice)
        container.hide()
        owner.layout_notice_container = container
        page_layout.insertWidget(page_layout.count() - 1, container)

    @staticmethod
    def _make_notice_label(color: str) -> QLabel:
        lbl = QLabel()
        lbl.setStyleSheet(
            f"font-size: 10px; font-style: italic; color: {color}; background-color: transparent;"
        )
        lbl.setWordWrap(True)
        lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        lbl.setFixedWidth(180)
        lbl.hide()
        return lbl
