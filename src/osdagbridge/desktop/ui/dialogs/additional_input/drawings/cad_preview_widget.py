"""
CadPreviewWidget
================
Self-contained CAD preview widget: GirderCadView canvas + view-mode buttons.
See CadPreviewWidget docstring for public API.
"""
from __future__ import annotations
from typing import List

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui  import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QHBoxLayout, QPushButton, QSizePolicy, QVBoxLayout, QWidget,
)

class GirderCadView(QWidget):
    """Simple 2-D segmented girder view driven by member lengths."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(160)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet(
            "QWidget { background: #f8f8f8; border: 1px solid #d8d8d8; border-radius: 8px; }"
        )
        self._segments: List[dict] = []
        self._selected_member_id: str = ""
        self._flange_thickness: float = 15.0
        self._view_mode: str = "side"

    # ── public API ────────────────────────────────────────────────────────────

    def set_segments(self, segments: List[dict]) -> None:
        cleaned = []
        for seg in segments or []:
            start  = float(seg.get("start", 0.0))
            end    = float(seg.get("end",   0.0))
            length = max(0.0, end - start)
            if length <= 0.0:
                continue
            cleaned.append({"id": str(seg.get("id") or ""), "length": length})
        self._segments = cleaned
        self.update()

    def set_selected_member(self, member_id: str) -> None:
        self._selected_member_id = str(member_id or "").strip()
        self.update()

    def set_view_mode(self, mode: str) -> None:
        normalized = str(mode or "").strip().lower()
        if normalized not in {"cross", "side"}:
            normalized = "side"
        if self._view_mode != normalized:
            self._view_mode = normalized
            self.update()

    # ── painting ──────────────────────────────────────────────────────────────

    @staticmethod
    def _fmt(length_m: float) -> str:
        text = f"{float(length_m):.3f}".rstrip("0").rstrip(".")
        return text or "0"

    def paintEvent(self, event):  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        rect = QRectF(self.rect()).adjusted(10.0, 24.0, -10.0, -18.0)
        if rect.width() <= 0 or rect.height() <= 0:
            return

        painter.setPen(QPen(QColor("#d0d0d0")))
        painter.setBrush(QColor("#f4f4f4"))
        painter.drawRect(rect)

        if not self._segments:
            painter.setPen(QPen(QColor("#5a5a5a")))
            painter.drawText(rect, Qt.AlignCenter, "No member segments")
            return

        total = sum(float(s["length"]) for s in self._segments)
        if total <= 0.0:
            return

        if self._view_mode == "cross":
            self._paint_cross(painter, rect)
        else:
            self._paint_side(painter, rect, total)

    def _paint_cross(self, painter: QPainter, rect: QRectF) -> None:
        painter.setPen(QPen(QColor("#d0d0d0")))
        painter.setBrush(QColor("#ffffff"))
        painter.drawRect(rect)

        usable = rect.adjusted(rect.width() * 0.18, 12.0, -rect.width() * 0.18, -22.0)
        if usable.width() <= 0 or usable.height() <= 0:
            return

        tw  = usable.width() * 0.82
        bw  = usable.width() * 0.74
        ft  = max(10.0, min(self._flange_thickness, usable.height() * 0.20))
        wt  = max(8.0,  min(20.0, usable.width() * 0.10))
        cx  = usable.center().x()

        top    = QRectF(cx - tw / 2, usable.top(),            tw, ft)
        bottom = QRectF(cx - bw / 2, usable.bottom() - ft,    bw, ft)
        web    = QRectF(cx - wt / 2, top.bottom(), wt, max(2.0, bottom.top() - top.bottom()))

        painter.setPen(Qt.NoPen)
        for color, part in [("#c9c9c9", top), ("#dcdcdc", web), ("#c9c9c9", bottom)]:
            painter.setBrush(QColor(color))
            painter.drawRect(part)

        outline = QPen(QColor("#5e5e5e"))
        outline.setWidth(1)
        painter.setPen(outline)
        painter.setBrush(Qt.NoBrush)
        for part in (top, web, bottom):
            painter.drawRect(part)

        label = self._selected_member_id or (
            str(self._segments[0].get("id") or "") if self._segments else ""
        )
        title = f"Cross Section • {label}" if label else "Cross Section"
        painter.setPen(QPen(QColor("#2a2a2a")))
        painter.drawText(rect.adjusted(8, 0, -8, -2), Qt.AlignHCenter | Qt.AlignBottom, title)

    def _paint_side(self, painter: QPainter, rect: QRectF, total: float) -> None:
        ft  = max(10.0, min(self._flange_thickness, rect.height() * 0.24))
        wt  = rect.top() + ft
        wb  = rect.bottom() - ft

        flange_pen  = QPen(QColor("#3a3a3a")); flange_pen.setWidth(1)
        outline_pen = QPen(QColor("#3a3a3a")); outline_pen.setWidth(1)
        part_pen    = QPen(QColor("#888888")); part_pen.setWidth(1)

        x = rect.left()
        partition_xs: List[float] = []

        for idx, seg in enumerate(self._segments):
            ratio = float(seg["length"]) / total
            w     = rect.width() * ratio
            if idx == len(self._segments) - 1:
                w = max(1.0, rect.right() - x)

            sr  = QRectF(x, rect.top(), w, rect.height())
            top = QRectF(sr.left(), sr.top(),  sr.width(), ft)
            web = QRectF(sr.left(), wt,         sr.width(), max(2.0, wb - wt))
            bot = QRectF(sr.left(), wb,          sr.width(), ft)
            mid = str(seg.get("id") or "")
            sel = bool(self._selected_member_id) and mid == self._selected_member_id

            painter.setPen(Qt.NoPen)
            for color, part in [("#c9c9c9", top), ("#dcdcdc", web), ("#c9c9c9", bot)]:
                painter.setBrush(QColor(color))
                painter.drawRect(part)

            painter.setPen(flange_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawLine(top.bottomLeft(), top.bottomRight())
            painter.drawLine(bot.topLeft(),    bot.topRight())

            if sel:
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(144, 175, 19, 42))
                painter.drawRect(sr.adjusted(2, 2, -2, -2))
                sp = QPen(QColor("#6f850f")); sp.setWidth(2)
                painter.setPen(sp)
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(sr.adjusted(1.5, 1.5, -1.5, -1.5))

            painter.setPen(QPen(QColor("#121212")))
            label = f"{seg['id']} ({self._fmt(seg['length'])} m)"
            tr    = sr.adjusted(6, 0, -6, 0)
            if tr.width() > 18:
                elided = painter.fontMetrics().elidedText(label, Qt.ElideRight, int(tr.width()))
                painter.drawText(tr, Qt.AlignCenter, elided)

            if idx < len(self._segments) - 1:
                partition_xs.append(sr.right())
            x = sr.right()

        painter.setPen(outline_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(rect)
        painter.drawLine(rect.left(), wt, rect.right(), wt)
        painter.drawLine(rect.left(), wb, rect.right(), wb)

        painter.setPen(part_pen)
        for px in partition_xs:
            painter.drawLine(
                QRectF(px, rect.top(), 0, rect.height()).topLeft(),
                QRectF(px, rect.top(), 0, rect.height()).bottomLeft(),
            )


class CadPreviewWidget(QWidget):
    """
    Self-contained CAD preview: GirderCadView canvas + Cross Section / Side View buttons.

    All internal wiring (button clicks → view mode switch) is handled inside.
    Only one public method is exposed to the outside:

        update_from_bridge_inputs(working_input_dict)
            Called by AdditionalInputs whenever data changes.
            Extracts segment chain and selected member from the dict,
            then redraws the canvas.

    Instantiated via TYPE_DIRECT_WIDGET in GIRDER_DETAILS_SCHEMA.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._view_mode: str = "side"
        self._mode_buttons: dict[str, QPushButton] = {}
        self._build()
        self._wire()

    # ── public update methods — called from AdditionalInputs connectors ────────

    def update_segments(self, segments: list) -> None:
        """Redraw canvas with a new segment chain."""
        self._cad.set_segments(segments)

    def update_selected_member(self, member_id: str) -> None:
        """Highlight the selected member on the canvas."""
        self._cad.set_selected_member(member_id)

    # ── internal ──────────────────────────────────────────────────────────────

    def _build(self) -> None:
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(12)

        self._cad = GirderCadView(self)
        outer.addWidget(self._cad, 1)

        btn_col = QVBoxLayout()
        btn_col.setContentsMargins(0, 0, 0, 0)
        btn_col.setSpacing(8)

        for label, mode in [("Cross Section", "cross"), ("Side View", "side")]:
            btn = QPushButton(label, self)
            btn.setCheckable(True)
            btn.setFixedWidth(130)
            btn.setFixedHeight(32)
            self._mode_buttons[mode] = btn
            btn_col.addWidget(btn)

        btn_col.addStretch(1)
        outer.addLayout(btn_col)

    def _wire(self) -> None:
        """Connect buttons to view mode switch — all internal."""
        self._mode_buttons["cross"].clicked.connect(
            lambda: self._set_view_mode("cross")
        )
        self._mode_buttons["side"].clicked.connect(
            lambda: self._set_view_mode("side")
        )
        self._set_view_mode("side")

    def _set_view_mode(self, mode: str) -> None:
        self._view_mode = mode
        self._cad.set_view_mode(mode)
        self._sync_button_styles()

    def _sync_button_styles(self) -> None:
        active = (
            "QPushButton { background: #f2f2f2; border: 1px solid #4a4a4a; border-radius: 2px;"
            " color: #1f1f1f; font-size: 12px; font-weight: 600; }"
            "QPushButton:hover { background: #f2f2f2; }"
            "QPushButton:pressed { background: #e7e7e7; }"
        )
        inactive = (
            "QPushButton { background: #ffffff; border: 1px solid #8f8f8f; border-radius: 2px;"
            " color: #2f2f2f; font-size: 12px; font-weight: 500; }"
            "QPushButton:hover { background: #f5f5f5; }"
            "QPushButton:pressed { background: #ececec; }"
        )
        for mode, btn in self._mode_buttons.items():
            is_active = mode == self._view_mode
            btn.blockSignals(True)
            btn.setChecked(is_active)
            btn.setStyleSheet(active if is_active else inactive)
            btn.blockSignals(False)