from PySide6.QtWidgets import QHeaderView, QTableWidget, QWidget

from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import LANE_DETAILS_TAB_SCHEMA
from osdagbridge.desktop.ui.dialogs.tabs.base import SchemaTab


class LaneDetailsTab(SchemaTab):
    schema = LANE_DETAILS_TAB_SCHEMA

    def __init__(self, owner, parent=None):
        super().__init__(owner, parent)
        self._inject_lane_table(owner, self.builder.page_layout)

    def collect_data(self) -> dict:
        data = super().collect_data()
        rows = []
        if hasattr(self.owner, "lane_table"):
            table = self.owner.lane_table
            for row in range(table.rowCount()):
                rows.append({
                    "lane_number": table.item(row, 0).text() if table.item(row, 0) else "",
                    "start": table.item(row, 1).text() if table.item(row, 1) else "",
                    "width": table.item(row, 2).text() if table.item(row, 2) else "",
                })
        data["lane_table_data"] = rows
        return data

    def restore_data(self, data: dict) -> None:
        super().restore_data(data)
        if not hasattr(self.owner, "lane_table"):
            return
            
        lane_rows = data.get("lane_table_data")
        if not isinstance(lane_rows, list):
            return

        table = self.owner.lane_table
        table.setRowCount(len(lane_rows))
        for row, row_data in enumerate(lane_rows):
            for col, key in enumerate(["lane_number", "start", "width"]):
                from PySide6.QtWidgets import QTableWidgetItem
                val = str(row_data.get(key, ""))
                table.setItem(row, col, QTableWidgetItem(val))

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
