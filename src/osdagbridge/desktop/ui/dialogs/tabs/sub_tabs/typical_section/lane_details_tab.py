from PySide6.QtWidgets import QHeaderView, QTableWidget, QWidget

from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import LANE_DETAILS_TAB_SCHEMA
from osdagbridge.desktop.ui.dialogs.tabs import schema_io
from osdagbridge.desktop.ui.dialogs.tabs.ui_builder import UIBuilder


class LaneDetailsTab(QWidget):

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        builder = UIBuilder(owner=owner, schema=LANE_DETAILS_TAB_SCHEMA)
        builder.build_tab(self)
        self._inject_lane_table(owner, builder.page_layout)

    def reset_defaults(self):
        schema_io.reset_defaults(self.owner, LANE_DETAILS_TAB_SCHEMA)

    def _inject_lane_table(self, owner, page_layout):
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels([
            "Traffic Lane Number",
            "Distance from inner edge of crash barrier to left edge of lane (m)",
            "Lane Width (m)",
        ])
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        owner.lane_table = table
        page_layout.insertWidget(page_layout.count() - 1, table)
