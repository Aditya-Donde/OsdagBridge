from __future__ import annotations

from typing import Dict, List, Optional

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QSizePolicy,
    QWidget,
)


class GirderCad2DView(QWidget):
    """Simple 2D segmented girder view driven by member lengths."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(160)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet("QWidget { background: #f8f8f8; border: 1px solid #d8d8d8; border-radius: 8px; }")
        self._segments: List[dict] = []
        self._selected_member_id: str = ""
        self._flange_thickness: float = 15.0
        self._view_mode: str = "side"

    @staticmethod
    def _fmt_length(length_m: float) -> str:
        text = f"{float(length_m):.3f}".rstrip("0").rstrip(".")
        return text if text else "0"

    def set_segments(self, segments: List[Dict[str, float]]) -> None:
        cleaned: List[dict] = []
        for segment in segments or []:
            try:
                start = float(segment.get("start", 0.0))
                end = float(segment.get("end", 0.0))
            except Exception:
                continue
            length = max(0.0, end - start)
            if length <= 0.0:
                continue
            cleaned.append(
                {
                    "id": str(segment.get("id") or ""),
                    "length": float(length),
                }
            )
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

    def _paint_cross_section(self, painter: QPainter, drawing_rect: QRectF) -> None:
        clear_pen = QPen(QColor("#d0d0d0"))
        clear_pen.setWidth(1)
        painter.setPen(clear_pen)
        painter.setBrush(QColor("#ffffff"))
        painter.drawRect(drawing_rect)

        usable = drawing_rect.adjusted(drawing_rect.width() * 0.18, 12.0, -drawing_rect.width() * 0.18, -22.0)
        if usable.width() <= 0.0 or usable.height() <= 0.0:
            return

        top_width = usable.width() * 0.82
        bottom_width = usable.width() * 0.74
        flange_thickness = max(10.0, min(self._flange_thickness, usable.height() * 0.20))
        web_thickness = max(8.0, min(20.0, usable.width() * 0.10))

        center_x = usable.center().x()
        top_flange = QRectF(center_x - (top_width / 2.0), usable.top(), top_width, flange_thickness)
        bottom_flange = QRectF(center_x - (bottom_width / 2.0), usable.bottom() - flange_thickness, bottom_width, flange_thickness)
        web_top = top_flange.bottom()
        web_bottom = bottom_flange.top()
        web = QRectF(center_x - (web_thickness / 2.0), web_top, web_thickness, max(2.0, web_bottom - web_top))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#c9c9c9"))
        painter.drawRect(top_flange)
        painter.setBrush(QColor("#dcdcdc"))
        painter.drawRect(web)
        painter.setBrush(QColor("#c9c9c9"))
        painter.drawRect(bottom_flange)

        outline = QPen(QColor("#5e5e5e"))
        outline.setWidth(1)
        painter.setPen(outline)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(top_flange)
        painter.drawRect(web)
        painter.drawRect(bottom_flange)

        label_member = self._selected_member_id or (str(self._segments[0].get("id") or "") if self._segments else "")
        label = f"Cross Section • {label_member}" if label_member else "Cross Section"
        painter.setPen(QPen(QColor("#2a2a2a")))
        painter.drawText(drawing_rect.adjusted(8.0, 0.0, -8.0, -2.0), Qt.AlignHCenter | Qt.AlignBottom, label)

    def paintEvent(self, event):  # noqa: N802 (Qt naming)
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        drawing_rect = QRectF(self.rect()).adjusted(10.0, 24.0, -10.0, -18.0)
        if drawing_rect.width() <= 0 or drawing_rect.height() <= 0:
            return

        outer_fill = QColor("#f4f4f4")
        outer_border = QPen(QColor("#d0d0d0"))
        outer_border.setWidth(1)
        painter.setPen(outer_border)
        painter.setBrush(outer_fill)
        painter.drawRect(drawing_rect)

        if not self._segments:
            painter.setPen(QPen(QColor("#5a5a5a")))
            painter.drawText(drawing_rect, Qt.AlignCenter, "No member segments")
            return

        total_length = sum(float(segment["length"]) for segment in self._segments)
        if total_length <= 0.0:
            return

        if self._view_mode == "cross":
            self._paint_cross_section(painter, drawing_rect)
            return

        # Monochrome palette for a clean technical look.
        fill_palette = [QColor("#f5f5f5"), QColor("#eeeeee"), QColor("#e7e7e7")]
        partition_pen = QPen(QColor("#888888"))
        partition_pen.setWidth(1)
        partition_pen.setStyle(Qt.SolidLine)

        # Keep flanges visually meaningful even for compact/tall drawing areas.
        flange_thickness = max(10.0, min(self._flange_thickness, drawing_rect.height() * 0.24))
        web_top = drawing_rect.top() + flange_thickness
        web_bottom = drawing_rect.bottom() - flange_thickness
        web_height = max(2.0, web_bottom - web_top)

        # Flange-web boundary lines improve structural readability in grayscale.
        flange_boundary_pen = QPen(QColor("#3a3a3a"))
        flange_boundary_pen.setWidth(1)
        girder_outline_pen = QPen(QColor("#3a3a3a"))
        girder_outline_pen.setWidth(1)

        x = drawing_rect.left()
        partition_xs: List[float] = []
        for index, segment in enumerate(self._segments):
            ratio = float(segment["length"]) / total_length
            segment_width = drawing_rect.width() * ratio
            if index == len(self._segments) - 1:
                segment_width = max(1.0, drawing_rect.right() - x)

            segment_rect = QRectF(x, drawing_rect.top(), segment_width, drawing_rect.height())
            top_flange_rect = QRectF(segment_rect.left(), segment_rect.top(), segment_rect.width(), flange_thickness)
            web_rect = QRectF(segment_rect.left(), web_top, segment_rect.width(), web_height)
            bottom_flange_rect = QRectF(segment_rect.left(), web_bottom, segment_rect.width(), flange_thickness)
            member_id = str(segment.get("id") or "")
            is_selected = bool(self._selected_member_id) and member_id == self._selected_member_id

            top_fill = QColor("#c9c9c9")
            web_fill = QColor("#dcdcdc")
            bottom_fill = QColor("#c9c9c9")

            painter.setPen(Qt.NoPen)
            painter.setBrush(top_fill)
            painter.drawRect(top_flange_rect)
            painter.setBrush(web_fill)
            painter.drawRect(web_rect)
            painter.setBrush(bottom_fill)
            painter.drawRect(bottom_flange_rect)

            # Draw flange boundaries explicitly so thickness is always visible.
            painter.setPen(flange_boundary_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawLine(top_flange_rect.bottomLeft(), top_flange_rect.bottomRight())
            painter.drawLine(bottom_flange_rect.topLeft(), bottom_flange_rect.topRight())

            if is_selected:
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(144, 175, 19, 42))
                painter.drawRect(segment_rect.adjusted(2.0, 2.0, -2.0, -2.0))

                selected_pen = QPen(QColor("#6f850f"))
                selected_pen.setWidth(2)
                painter.setPen(selected_pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(segment_rect.adjusted(1.5, 1.5, -1.5, -1.5))

            label = f"{segment['id']} ({self._fmt_length(segment['length'])} m)"
            painter.setPen(QPen(QColor("#121212")))
            text_margin = 6
            text_rect = segment_rect.adjusted(text_margin, 0, -text_margin, 0)
            if text_rect.width() > 18:
                elided = painter.fontMetrics().elidedText(label, Qt.ElideRight, int(text_rect.width()))
                painter.drawText(text_rect, Qt.AlignCenter, elided)

            if index < len(self._segments) - 1:
                partition_xs.append(segment_rect.right())

            x = segment_rect.right()

        # Draw partitions in a final pass so fills/selection cannot hide them.
        painter.setPen(girder_outline_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(drawing_rect)
        painter.drawLine(drawing_rect.left(), web_top, drawing_rect.right(), web_top)
        painter.drawLine(drawing_rect.left(), web_bottom, drawing_rect.right(), web_bottom)

        painter.setPen(partition_pen)
        for px in partition_xs:
            painter.drawLine(
                QRectF(px, drawing_rect.top(), 0.0, drawing_rect.height()).topLeft(),
                QRectF(px, drawing_rect.top(), 0.0, drawing_rect.height()).bottomLeft(),
            )
