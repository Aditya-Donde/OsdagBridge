"""SegmentTableWidget — replaces the inline QTableWidget + action-button logic
from GirderDetailsTab._build_overview_card().

UIBuilder creates this via TYPE_SEGMENT_TABLE.

Public API:
    refresh(segments, selected_index)   — repopulate all rows
    set_selected_row(index)             — highlight a row
    current_row() -> int
"""
from __future__ import annotations
from typing import Callable, List, Optional

from PySide6.QtCore  import Qt, QSize, Signal, QTimer
from PySide6.QtGui   import QColor, QDoubleValidator, QIcon, QPainter, QPalette, QPen, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)


# ── Delegates (identical to GirderDetailsTab) ─────────────────────────────────

class _ReadOnlyCellDelegate(QStyledItemDelegate):
    _bg   = QColor("#fafafa")
    _text = QColor("#666666")

    def paint(self, painter, option, index):
        opt = QStyleOptionViewItem(option)
        if opt.state & QStyle.State_Selected:
            opt.state &= ~QStyle.State_Selected
        opt.backgroundBrush = self._bg
        opt.palette.setColor(QPalette.Base, self._bg)
        opt.palette.setColor(QPalette.Text, self._text)
        super().paint(painter, opt, index)


class _EndDistanceDelegate(QStyledItemDelegate):
    _bg     = QColor("#ffffff")
    _border = QColor("#c0c0c0")

    def paint(self, painter, option, index):
        opt = QStyleOptionViewItem(option)
        if opt.state & QStyle.State_Selected:
            opt.state &= ~QStyle.State_Selected
        opt.backgroundBrush = self._bg
        opt.palette.setColor(QPalette.Base, self._bg)
        super().paint(painter, opt, index)
        painter.save()
        pen = QPen(self._border); pen.setWidth(1); painter.setPen(pen)
        painter.drawRoundedRect(opt.rect.adjusted(3, 3, -3, -3), 4, 4)
        painter.restore()

    def createEditor(self, parent, option, index):
        ed = QLineEdit(parent)
        ed.setAlignment(Qt.AlignCenter)
        ed.setValidator(QDoubleValidator(0.0, 1e12, 3, ed))
        ed.setStyleSheet(
            "QLineEdit { padding: 0px 4px; border: 2px solid #90AF13; border-radius: 4px;"
            " background: #ffffff; color: #000000;"
            " selection-background-color: #90AF13; selection-color: #ffffff; }"
        )
        return ed

    def setEditorData(self, editor, index):
        editor.setText(str(index.data() or ""))
        editor.selectAll()

    def setModelData(self, editor, model, index):
        model.setData(index, editor.text())


# ── SegmentTableWidget ────────────────────────────────────────────────────────

class SegmentTableWidget(QWidget):
    """
    Self-contained master-detail segment table with +/− per-row action buttons.

    No constructor args — instantiated directly by TYPE_DIRECT_WIDGET.
    Seeded with one default segment (G1M1, 0–30 m) on init.

    Public API (called from outside with data):
        refresh(segments, selected_index)  — repopulate from segment chain
        set_selected_row(index)            — highlight a row
        current_row() -> int
    """

    _HEADERS          = ["Member ID", "Start (m)", "End (m)", "Length (m)", "Action"]
    _ACTION_COL_WIDTH = 132
    _DEFAULT_SEGMENTS = [{"id": "G1M1", "start": 0.0, "end": 30.0}]

    # Signals — connect from outside to react to user actions
    row_selected   = Signal(int, str)   # (row_index, member_id)
    data_changed   = Signal(object)     # segments list or {action, row, segments}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._segments:    List[dict] = []
        self._min_rows:    int        = 1
        self._icon_cache:  dict       = {}
        self._build()
        QTimer.singleShot(0, lambda: self.refresh(self._DEFAULT_SEGMENTS))

    # ── public API ────────────────────────────────────────────────────────────

    def refresh(self, segments: List[dict], selected_index: int = 0) -> None:
        """Repopulate all rows from segments list."""
        self._segments = list(segments or [])
        self._min_rows = 1
        self._repopulate(selected_index)
        self.data_changed.emit(list(self._segments))

    def set_selected_row(self, index: int) -> None:
        if 0 <= index < self._table.rowCount():
            self._table.blockSignals(True)
            self._table.setCurrentCell(index, 0)
            self._table.blockSignals(False)
            self._update_action_highlight(index)

    def current_row(self) -> int:
        return max(0, self._table.currentRow())

    # ── build ─────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._table = QTableWidget(0, len(self._HEADERS))
        self._table.setHorizontalHeaderLabels(self._HEADERS)
        hh = self._table.horizontalHeader()
        hh.setVisible(True)
        hh.setMinimumHeight(34)
        for col in range(4):
            hh.setSectionResizeMode(col, QHeaderView.Stretch)
        hh.setSectionResizeMode(4, QHeaderView.Fixed)
        self._table.setColumnWidth(4, self._ACTION_COL_WIDTH)

        self._table.verticalHeader().setVisible(False)
        self._table.verticalHeader().setDefaultSectionSize(38)
        self._table.verticalHeader().setMinimumSectionSize(34)

        self._table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._table.setShowGrid(True)
        self._table.setGridStyle(Qt.SolidLine)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setSelectionMode(QTableWidget.SingleSelection)
        self._table.setEditTriggers(
            QTableWidget.DoubleClicked | QTableWidget.SelectedClicked | QTableWidget.EditKeyPressed
        )

        # show ~2 rows then scroll
        row_h = int(self._table.verticalHeader().defaultSectionSize() or 34)

        self._table.setStyleSheet(
            "QTableWidget { background: #ffffff; border: 1px solid #d6d6d6;"
            " border-radius: 6px; gridline-color: #d0d0d0; }"
            "QTableWidget::item { color: #1f1f1f; padding: 4px 6px; }"
            "QTableWidget::item:selected { background: #e8f0c9; color: #1a1a1a; }"
            "QTableWidget::item:focus { outline: none; }"
            "QTableWidget QLineEdit { background: #ffffff; color: #000000; }"
            "QHeaderView::section { background: #f3f3f3; color: #2b2b2b;"
            " font-weight: 700; border: 1px solid #d0d0d0; padding: 6px; }"
            "QTableCornerButton::section { background: #f3f3f3; border: 1px solid #d0d0d0; }"
        )

        ro = _ReadOnlyCellDelegate(self._table)
        self._table.setItemDelegateForColumn(0, ro)
        self._table.setItemDelegateForColumn(1, ro)
        self._table.setItemDelegateForColumn(3, ro)
        self._table.setItemDelegateForColumn(2, _EndDistanceDelegate(self._table))

        self._table.currentCellChanged.connect(self._on_current_cell_changed)
        self._table.cellClicked.connect(self._on_cell_clicked)
        self._table.itemChanged.connect(self._on_item_changed)

        layout.addWidget(self._table, 1)

    # ── internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _fmt(value: float) -> str:
        text = f"{float(value):.3f}".rstrip("0").rstrip(".")
        return text or "0"

    def _repopulate(self, selected_index: int = 0) -> None:
        self._table.blockSignals(True)
        try:
            self._table.clearContents()
            self._table.setRowCount(0)
            self._table.setRowCount(len(self._segments))

            can_remove = len(self._segments) > self._min_rows

            for row, seg in enumerate(self._segments):
                for col in range(4):
                    if self._table.cellWidget(row, col):
                        self._table.removeCellWidget(row, col)

                seg_id = str(seg.get("id") or "")
                start  = float(seg.get("start", 0.0))
                end    = float(seg.get("end",   0.0))
                length = max(0.0, end - start)

                def _ro_item(text: str) -> QTableWidgetItem:
                    it = QTableWidgetItem(text)
                    it.setTextAlignment(Qt.AlignCenter)
                    it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                    return it

                self._table.setItem(row, 0, _ro_item(seg_id))
                self._table.setItem(row, 1, _ro_item(self._fmt(start)))

                end_item = QTableWidgetItem(self._fmt(end))
                end_item.setTextAlignment(Qt.AlignCenter)
                self._table.setItem(row, 2, end_item)

                self._table.setItem(row, 3, _ro_item(self._fmt(length)))
                self._table.setCellWidget(row, 4, self._make_action_widget(row, can_remove))
        finally:
            self._table.blockSignals(False)

        self._update_action_highlight(selected_index)
        if 0 <= selected_index < self._table.rowCount():
            self._table.blockSignals(True)
            self._table.setCurrentCell(selected_index, 0)
            self._table.blockSignals(False)

    def _make_action_widget(self, row: int, can_remove: bool) -> QWidget:
        container = QWidget()
        container.setObjectName("segmentActionCell")
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        container.setMinimumHeight(28)
        container.setMaximumHeight(34)
        container.setStyleSheet("QWidget#segmentActionCell { background: transparent; border: none; }")

        layout = QHBoxLayout(container)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignCenter)

        add_btn = QPushButton("")
        add_btn.setObjectName("segmentAddBtn")
        add_btn.setFixedSize(36, 24)
        add_btn.setIcon(self._icon("add"))
        add_btn.setIconSize(QSize(12, 12))
        add_btn.setFocusPolicy(Qt.NoFocus)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setToolTip("Split/Add segment")
        add_btn.setStyleSheet(
            "QPushButton { background-color: #90AF13; border: 1px solid #6f850f; border-radius: 8px; }"
            "QPushButton:hover { background-color: #7a9410; }"
            "QPushButton:pressed { background-color: #6a840d; }"
        )
        add_btn.clicked.connect(lambda _=False, r=row: self._on_add_clicked(r))

        rem_btn = QPushButton("")
        rem_btn.setObjectName("segmentRemoveBtn")
        rem_btn.setFixedSize(36, 24)
        rem_btn.setIcon(self._icon("remove"))
        rem_btn.setIconSize(QSize(12, 12))
        rem_btn.setFocusPolicy(Qt.NoFocus)
        rem_btn.setCursor(Qt.PointingHandCursor)
        rem_btn.setEnabled(can_remove)
        rem_btn.setToolTip("Remove this segment" if can_remove else "At least one segment is required")
        rem_btn.setStyleSheet(
            "QPushButton { background-color: #c72626; border: 1px solid #8f1c1c; border-radius: 8px; }"
            "QPushButton:hover { background-color: #ae1f1f; }"
            "QPushButton:pressed { background-color: #991a1a; }"
            "QPushButton:disabled { background-color: #d6d6d6; color: #8c8c8c; border-color: #d6d6d6; }"
        )
        rem_btn.clicked.connect(lambda _=False, r=row: self._on_remove_clicked(r))

        layout.addWidget(add_btn)
        layout.addWidget(rem_btn)
        return container

    def _icon(self, kind: str) -> QIcon:
        if kind in self._icon_cache:
            return self._icon_cache[kind]
        px = QPixmap(12, 12)
        px.fill(Qt.transparent)
        p = QPainter(px)
        try:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#ffffff"))
            p.drawRect(1, 5, 10, 2)
            if kind == "add":
                p.drawRect(5, 1, 2, 10)
        finally:
            p.end()
        icon = QIcon(px)
        self._icon_cache[kind] = icon
        return icon

    def _update_action_highlight(self, selected_row: int) -> None:
        for row in range(self._table.rowCount()):
            w = self._table.cellWidget(row, 4)
            if w is None:
                continue
            bg = "#e8f0c9" if row == selected_row else "transparent"
            w.setStyleSheet(
                f"QWidget#segmentActionCell {{ background: {bg}; border: none; }}"
            )

    # ── slot handlers ─────────────────────────────────────────────────────────

    def _on_current_cell_changed(self, cur_row, _cur_col, _prev_row, _prev_col):
        if cur_row < 0:
            return
        self._update_action_highlight(cur_row)
        seg_id = str(self._segments[cur_row].get("id", "")) if cur_row < len(self._segments) else ""
        self.row_selected.emit(cur_row, seg_id)

    def _on_cell_clicked(self, row: int, column: int) -> None:
        if column != 2:
            return
        item = self._table.item(row, column)
        if item:
            self._table.setCurrentCell(row, column)
            self._table.editItem(item)

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if item.column() != 2 or item.row() < 0:
            return
        row = item.row()
        if row >= len(self._segments):
            return
        try:
            new_end = float(item.text())
        except ValueError:
            self._table.blockSignals(True)
            item.setText(self._fmt(self._segments[row].get("end", 0.0)))
            self._table.blockSignals(False)
            return

        current    = self._segments[row]
        start      = float(current.get("start", 0.0))
        old_end    = float(current.get("end",   0.0))
        total_span = float(self._segments[-1].get("end", old_end))  # last segment's end = total span
        is_last    = row == len(self._segments) - 1

        # Clamp below start
        if new_end < start:
            new_end = start

        if is_last:
            # Cannot exceed total span
            new_end = min(new_end, total_span)
        else:
            # Cannot exceed next segment's end
            next_end = float(self._segments[row + 1].get("end", total_span))
            new_end  = min(new_end, next_end)

        current["end"] = new_end

        if not is_last:
            # Ripple: next segment start = this end
            self._segments[row + 1]["start"] = new_end
        else:
            # Last segment shortened → create fill segment
            if new_end < old_end and new_end < total_span:
                girder   = str(self._segments[0].get("id", "G1M1")).rsplit("M", 1)[0]
                next_id  = f"{girder}M{len(self._segments) + 1}"
                self._segments.append({"id": next_id, "start": new_end, "end": total_span})

        # Renormalize all starts
        self._segments[0]["start"] = 0.0
        for i in range(1, len(self._segments)):
            self._segments[i]["start"] = float(self._segments[i - 1].get("end", 0.0))

        # Enforce last end == total_span
        self._segments[-1]["end"] = total_span

        QTimer.singleShot(0, lambda: self._deferred_refresh(row))
        self.data_changed.emit(list(self._segments))

    def _refresh_row(self, row: int) -> None:
        """Update displayed values for a single row after an edit."""
        if row >= len(self._segments):
            return
        seg    = self._segments[row]
        start  = float(seg.get("start", 0.0))
        end    = float(seg.get("end",   0.0))
        length = max(0.0, end - start)

        self._table.blockSignals(True)
        # Start (read-only)
        start_item = self._table.item(row, 1)
        if start_item:
            start_item.setText(self._fmt(start))
        # End (editable — only update if not currently being edited)
        end_item = self._table.item(row, 2)
        if end_item:
            end_item.setText(self._fmt(end))
        # Length (read-only)
        len_item = self._table.item(row, 3)
        if len_item:
            len_item.setText(self._fmt(length))
        self._table.blockSignals(False)

    def _on_add_clicked(self, row: int) -> None:
        """Split segment at row into two equal halves.
        Refresh is deferred via QTimer so the button signal fully completes
        before the cell widget is destroyed and recreated by _repopulate.
        """
        if row >= len(self._segments):
            return

        seg    = self._segments[row]
        start  = float(seg.get("start", 0.0))
        end    = float(seg.get("end",   0.0))
        length = end - start

        if length <= 0.01:
            return  # too small to split

        mid = start + length / 2.0
        seg["end"] = mid

        new_seg = {"id": "", "start": mid, "end": end}
        self._segments.insert(row + 1, new_seg)
        self._reindex_segments()

        QTimer.singleShot(0, lambda: self._deferred_refresh(row + 1))

    def _deferred_refresh(self, selected_index: int) -> None:
        self.refresh(self._segments, selected_index=selected_index)
        self.data_changed.emit(list(self._segments))

    def _on_remove_clicked(self, row: int) -> None:
        """Remove segment at row (minimum 1 segment enforced).
        Refresh deferred for the same reason as _on_add_clicked.
        """
        if len(self._segments) <= self._min_rows:
            return
        self._segments.pop(row)
        self._reindex_segments()
        new_sel = max(0, row - 1)
        QTimer.singleShot(0, lambda: self._deferred_refresh(new_sel))

    def _reindex_segments(self) -> None:
        """Renumber segment ids (G1M1, G1M2, …) and fix start/end chain."""
        if not self._segments:
            return
        # Derive girder prefix from first segment id
        first_id = str(self._segments[0].get("id", "G1M1"))
        # Extract girder part (everything before last 'M')
        girder = first_id.rsplit("M", 1)[0] if "M" in first_id else "G1"

        for i, seg in enumerate(self._segments, start=1):
            seg["id"] = f"{girder}M{i}"
            if i > 1:
                seg["start"] = float(self._segments[i - 2].get("end", 0.0))