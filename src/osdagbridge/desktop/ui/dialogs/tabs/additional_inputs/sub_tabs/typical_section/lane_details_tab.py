import math

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem, QWidget

from osdagbridge.desktop.ui.dialogs.tabs.schemas.plate_girder import LANE_DETAILS_TAB_SCHEMA
from osdagbridge.desktop.ui.dialogs.tabs.base import SchemaTab


class LaneDetailsTab(SchemaTab):
    schema = LANE_DETAILS_TAB_SCHEMA

    def __init__(self, owner, parent=None):
        super().__init__(owner, parent)
        self._updating_lane_table = False
        self._inject_lane_table(owner, self.builder.page_layout)
        self.initialize_defaults(self._carriageway_width())
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
        if isinstance(lane_rows, list):
            max_allowed = self.max_lane_count_allowed(self._carriageway_width())
            restored_count = min(len(lane_rows), max_allowed)
            self._configure_lane_count_combo(
                max_allowed,
                selected_count=restored_count,
            )
            self.set_lane_rows(lane_rows[:restored_count])
            return
        self.initialize_defaults(self._carriageway_width())

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
        was_updating = self._updating_lane_table
        self._updating_lane_table = True
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
            self._updating_lane_table = was_updating

    def populate_defaults(self, lane_count: int, design_width: float | None = None) -> None:
        design_width = self.design_lane_width_m() if design_width is None else float(design_width)
        was_updating = self._updating_lane_table
        self._updating_lane_table = True
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
            self._updating_lane_table = was_updating

    def recompute_lane_starts(self, design_width: float | None = None) -> float:
        design_width = self.design_lane_width_m() if design_width is None else float(design_width)
        was_updating = self._updating_lane_table
        self._updating_lane_table = True
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
            self._updating_lane_table = was_updating

        carriageway_width = self._carriageway_width()
        if carriageway_width and total_width - carriageway_width > 1e-6:
            self._show_owner_warning(
                "Lane Width Exceeds Carriageway",
                f"Sum of lane widths ({total_width:.2f} m) exceeds carriageway width provided "
                f"({carriageway_width:.2f} m).\nAdjust lane count or widths per IRC 5 Clause 104.3.1.",
            )
        return total_width

    def validate_lane_rows(
        self,
        design_width: float | None = None,
        carriageway_width: float | None = None,
    ) -> list[str]:
        design_width = self.design_lane_width_m() if design_width is None else float(design_width)
        if carriageway_width is None:
            carriageway_width = self._carriageway_width()
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

    def reset_defaults(self) -> None:
        super().reset_defaults()
        self.initialize_defaults(self._carriageway_width())

    def validate_tab(self) -> list[str]:
        errors = list(super().validate_tab())
        errors.extend(self.validate_lane_rows())
        return list(dict.fromkeys(errors))

    @staticmethod
    def design_lane_width_m() -> float:
        return 3.5

    def max_lane_count_allowed(self, carriageway_width: float | None = None) -> int:
        try:
            width = float(self._carriageway_width() if carriageway_width is None else carriageway_width)
            max_lanes = int(math.floor(width / self.design_lane_width_m()))
            return max(1, min(6, max_lanes if max_lanes > 0 else 1))
        except Exception:
            return 1

    def initialize_defaults(self, carriageway_width: float | None = None) -> None:
        max_allowed = self.max_lane_count_allowed(carriageway_width)
        self._configure_lane_count_combo(max_allowed, selected_count=max_allowed)
        self.populate_defaults(max_allowed)

    def sync_from_bridge_context(self, carriageway_width: float | None, *, force: bool = False) -> None:
        """Refresh lane choices when the parent bridge width changes.

        The tab is constructed before AdditionalInputs pushes the actual
        carriageway width into its parent. Without this sync, Lane Details keeps
        the constructor default width and can offer too many lanes.
        """
        max_allowed = self.max_lane_count_allowed(carriageway_width)
        current_count = self.table.rowCount() or self._selected_lane_count()
        selected_count = max_allowed if force else min(max(1, current_count), max_allowed)
        items_before = self._lane_count_items()
        self._configure_lane_count_combo(max_allowed, selected_count=selected_count)
        items_after = self._lane_count_items()

        if force or current_count != selected_count or items_before != items_after:
            self.populate_defaults(selected_count)
        else:
            self.recompute_lane_starts()

    def on_lane_count_changed(self, text) -> None:
        if self._updating_lane_table:
            return
        try:
            lane_count = min(max(1, int(text)), self.max_lane_count_allowed(self._carriageway_width()))
        except (TypeError, ValueError):
            return
        if str(lane_count) != str(text):
            self._configure_lane_count_combo(self.max_lane_count_allowed(self._carriageway_width()), selected_count=lane_count)
        self.populate_defaults(lane_count)

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
        if self._updating_lane_table:
            return
        if column == 2:
            self._validate_lane_width(row)
            self.recompute_lane_starts()
        elif column == 1:
            self._validate_lane_start(row)
            self.recompute_lane_starts()

    def _configure_lane_count_combo(self, max_allowed: int, *, selected_count: int) -> None:
        upper_bound = max(1, min(6, int(max_allowed)))
        previous = self.lane_count_combo.blockSignals(True)
        try:
            self.lane_count_combo.clear()
            for count in range(1, upper_bound + 1):
                self.lane_count_combo.addItem(str(count))
            self.lane_count_combo.setCurrentText(str(max(1, min(upper_bound, int(selected_count)))))
        finally:
            self.lane_count_combo.blockSignals(previous)

    def _selected_lane_count(self) -> int:
        try:
            return int(self.lane_count_combo.currentText())
        except (TypeError, ValueError):
            return 1

    def _lane_count_items(self) -> list[str]:
        return [self.lane_count_combo.itemText(index) for index in range(self.lane_count_combo.count())]

    def _validate_lane_width(self, row: int) -> None:
        design_width = self.design_lane_width_m()
        width = self._parse_float(row, 2)
        if width is None:
            self._set_cell(row, 2, f"{design_width:.2f}")
            return
        if width + 1e-6 < design_width:
            self._show_owner_critical(
                "Lane Width Below IRC Minimum",
                f"IRC 5 Clause 104.3.1 requires a lane width of at least {design_width:.2f} m.",
            )
            self._set_cell(row, 2, f"{design_width:.2f}")

    def _validate_lane_start(self, row: int) -> None:
        design_width = self.design_lane_width_m()
        start = self._parse_float(row, 1)
        if start is None:
            self.recompute_lane_starts()
            return

        if row == 0:
            if abs(start) > 1e-6:
                self._show_owner_warning(
                    "Lane Start Offset",
                    "First lane must start at 0 m from inner edge of crash barrier by default.",
                )
                self.recompute_lane_starts()
            return

        prev_start = self._parse_float(row - 1, 1) or 0.0
        prev_width = self._parse_float(row - 1, 2) or design_width
        expected = prev_start + prev_width
        if abs(start - expected) > 1e-3:
            self._show_owner_warning(
                "Lane Start Sequence",
                "Each lane start must equal previous lane start plus previous lane width per IRC guidance.",
            )
            self.recompute_lane_starts()

    def _carriageway_width(self) -> float | None:
        owner = getattr(self, "owner", None)
        try:
            value = getattr(owner, "carriageway_width", None)
            return float(value) if value is not None else None
        except Exception:
            return None

    def _show_owner_warning(self, title: str, text: str) -> None:
        owner = getattr(self, "owner", None)
        callback = getattr(owner, "show_warning_message", None) if owner is not None else None
        if callable(callback):
            callback(title, text)

    def _show_owner_critical(self, title: str, text: str) -> None:
        owner = getattr(self, "owner", None)
        callback = getattr(owner, "show_critical_message", None) if owner is not None else None
        if callable(callback):
            callback(title, text)

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
