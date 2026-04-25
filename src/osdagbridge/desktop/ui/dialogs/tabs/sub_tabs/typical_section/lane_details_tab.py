from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem, QWidget

from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import LANE_DETAILS_TAB_SCHEMA
from osdagbridge.desktop.ui.dialogs.tabs.base import SchemaTab


class LaneDetailsTab(SchemaTab):
    schema = LANE_DETAILS_TAB_SCHEMA

    def __init__(self, owner, parent=None):
        super().__init__(owner, parent)
        self._inject_lane_table(owner, self.builder.page_layout)
        self.table.cellChanged.connect(self._on_table_cell_changed)

    @property
    def table(self) -> QTableWidget:
        return self.lane_table

    def export_lane_table_state(self) -> dict:
        return {"lane_table_data": self.get_lane_rows()}

    def collect_data(self) -> dict:
        data = super().collect_data()
        data["lane_table_data"] = self.get_lane_rows()
        return data

    def restore_data(self, data: dict) -> None:
        super().restore_data(data)
        lane_rows = data.get("lane_table_data")
        if not isinstance(lane_rows, list):
            return
        self.set_lane_rows(lane_rows)

    def get_lane_rows(self) -> list[dict]:
        rows = []
        for row in range(self.table.rowCount()):
            rows.append(
                {
                    "lane_number": self.table.item(row, 0).text() if self.table.item(row, 0) else "",
                    "start": self.table.item(row, 1).text() if self.table.item(row, 1) else "",
                    "width": self.table.item(row, 2).text() if self.table.item(row, 2) else "",
                }
            )
        return rows

    def set_lane_count(self, count: int) -> None:
        try:
            lane_count = max(0, int(count))
        except (TypeError, ValueError):
            return
        self.table.setRowCount(lane_count)
        for row in range(lane_count):
            lane_num_item = QTableWidgetItem(str(row + 1))
            lane_num_item.setFlags(lane_num_item.flags() & ~Qt.ItemIsEditable)
            lane_num_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, lane_num_item)

            for column in (1, 2):
                item = self.table.item(row, column)
                if item is None:
                    item = QTableWidgetItem("")
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row, column, item)

    def set_lane_rows(self, lane_rows: list[dict]) -> None:
        previous = self.table.blockSignals(True)
        try:
            self.set_lane_count(len(lane_rows))
            for row, row_data in enumerate(lane_rows):
                if not isinstance(row_data, dict):
                    continue
                self._set_cell(row, 0, str(row_data.get("lane_number", row + 1)))
                self._set_cell(row, 1, str(row_data.get("start", "")))
                self._set_cell(row, 2, str(row_data.get("width", "")))
        finally:
            self.table.blockSignals(previous)

    def populate_defaults(self, lane_count: int, design_width: float) -> None:
        previous = self.table.blockSignals(True)
        try:
            self.set_lane_count(lane_count)
            start = 0.0
            for row in range(lane_count):
                self._set_cell(row, 1, f"{start:.2f}")
                self._set_cell(row, 2, f"{design_width:.2f}")
                start += design_width
        finally:
            self.table.blockSignals(previous)

    def recompute_lane_starts(self, design_width: float) -> float:
        previous = self.table.blockSignals(True)
        total_width = 0.0
        try:
            start = 0.0
            for row in range(self.table.rowCount()):
                width = self._parse_float(row, 2)
                width = width if width is not None and width >= design_width else design_width
                self._set_cell(row, 1, f"{start:.2f}")
                self._set_cell(row, 2, f"{width:.2f}")
                total_width += width
                start += width
        finally:
            self.table.blockSignals(previous)
        return total_width

    def validate_lane_rows(self, design_width: float, carriageway_width: float | None = None) -> list[str]:
        errors = []
        expected_start = 0.0
        total_width = 0.0
        for row in range(self.table.rowCount()):
            start_text = self.table.item(row, 1).text().strip() if self.table.item(row, 1) else ""
            width_text = self.table.item(row, 2).text().strip() if self.table.item(row, 2) else ""

            if not start_text:
                errors.append(f"Lane {row + 1} start cannot be empty.")
                continue
            if not width_text:
                errors.append(f"Lane {row + 1} width cannot be empty.")
                continue

            try:
                start_value = float(start_text)
            except ValueError:
                errors.append(f"Lane {row + 1} start must be a valid number.")
                continue

            try:
                width_value = float(width_text)
            except ValueError:
                errors.append(f"Lane {row + 1} width must be a valid number.")
                continue

            if width_value + 1e-6 < design_width:
                errors.append(f"Lane {row + 1} width must be at least {design_width:.2f} m.")
            if abs(start_value - expected_start) > 1e-3:
                errors.append(f"Lane {row + 1} start must be {expected_start:.2f} m.")

            expected_start = start_value + width_value
            total_width += width_value

        if carriageway_width and total_width - carriageway_width > 1e-6:
            errors.append(
                f"Sum of lane widths ({total_width:.2f} m) exceeds carriageway width ({carriageway_width:.2f} m)."
            )

        return list(dict.fromkeys(errors))

    def _set_cell(self, row: int, column: int, value: str) -> None:
        item = self.table.item(row, column)
        if item is None:
            item = QTableWidgetItem()
            item.setTextAlignment(Qt.AlignCenter)
            if column == 0:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, column, item)
        item.setText(value)

    def _parse_float(self, row: int, column: int):
        try:
            item = self.table.item(row, column)
            if item and item.text():
                return float(item.text())
        except ValueError:
            return None
        return None

    def _on_table_cell_changed(self, row: int, column: int) -> None:
        owner = getattr(self, "owner", None)
        callback = getattr(owner, "_on_lane_cell_changed", None) if owner is not None else None
        if callable(callback):
            callback(row, column)

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
        table.setObjectName("lane_table")
        self.lane_table = table
        owner.lane_table = table
        page_layout.insertWidget(page_layout.count() - 1, table)
