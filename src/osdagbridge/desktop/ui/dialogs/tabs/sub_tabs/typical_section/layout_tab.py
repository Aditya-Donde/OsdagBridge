from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import LAYOUT_TAB_SCHEMA
from osdagbridge.desktop.ui.dialogs.tabs.base import SchemaTab


class LayoutTab(SchemaTab):
    schema = LAYOUT_TAB_SCHEMA

    def __init__(self, owner, parent=None):
        super().__init__(owner, parent)

        if hasattr(owner, "overall_bridge_width_display") and hasattr(owner, "overall_bridge_width_formula"):
            owner.overall_bridge_width_display.setToolTip(owner.overall_bridge_width_formula)

        self._create_notice_labels(owner, self.builder.page_layout)

    def _create_notice_labels(self, owner, page_layout):
        self.layout_adjust_notice = self._make_notice_label("#000000")
        self.layout_warning_notice = self._make_notice_label("#cc6600")

        container = QWidget()
        container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        container.setFixedWidth(180)
        vlayout = QVBoxLayout(container)
        vlayout.setContentsMargins(0, 0, 0, 0)
        vlayout.setSpacing(4)
        vlayout.addWidget(self.layout_adjust_notice)
        vlayout.addWidget(self.layout_warning_notice)
        container.hide()
        self.layout_notice_container = container
        owner.layout_adjust_notice = self.layout_adjust_notice
        owner.layout_warning_notice = self.layout_warning_notice
        owner.layout_notice_container = container
        page_layout.insertWidget(page_layout.count() - 1, container)

    def clear_notices(self) -> None:
        self.layout_adjust_notice.hide()
        self.layout_adjust_notice.setText("")
        self.layout_warning_notice.hide()
        self.layout_warning_notice.setText("")
        self.layout_notice_container.hide()

    def set_notices(self, reason: str | None = None, warning: str | None = None) -> None:
        any_visible = bool(reason) or bool(warning)
        if reason:
            self.layout_adjust_notice.setText(f"Values adjusted: {reason}")
            self.layout_adjust_notice.show()
        else:
            self.layout_adjust_notice.hide()
            self.layout_adjust_notice.setText("")

        if warning:
            self.layout_warning_notice.setText(f"Warning: {warning}")
            self.layout_warning_notice.show()
        else:
            self.layout_warning_notice.hide()
            self.layout_warning_notice.setText("")

        self.layout_notice_container.setVisible(any_visible)

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
