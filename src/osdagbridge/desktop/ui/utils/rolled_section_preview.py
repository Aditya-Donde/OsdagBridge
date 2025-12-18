"""Interactive beam preview widget with CAD-style annotations."""

from __future__ import annotations

import math
from typing import Dict, Optional

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from osdagbridge.core.bridge_components.super_structure.girder.properties import BeamSection


class RolledSectionPreview(QWidget):
    """Render a rolled section with dimension annotations."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._section: Optional[BeamSection] = None
        self._dimensions: Dict[str, float] = {}

        self._outline_color = QColor("#1b1b1b")
        self._outline_width = 3.0
        self._dimension_color = QColor("#1e88ff")
        self._label_bg = QColor(255, 255, 255, 230)
        self._text_color = QColor("#0f0f0f")

        self._outer_margin = 16
        self._annotation_margin_top = 36
        self._annotation_margin_bottom = 26
        self._annotation_margin_left = 52
        self._annotation_margin_right = 74
        self._dim_gap = 12
        self._arrow_size = 9

        self.setMinimumSize(360, 260)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def set_section(self, section: Optional[BeamSection]) -> None:
        """Update the preview to show the supplied ``BeamSection``."""

        self._section = section
        if section is None:
            self._dimensions = {}
        else:
            self._dimensions = {
                "depth": float(section.depth_mm),
                "top_flange_width": float(section.flange_width_mm),
                "bottom_flange_width": float(section.flange_width_mm),
                "web_thickness": float(section.web_thickness_mm),
                "top_flange_thickness": float(section.flange_thickness_mm),
                "bottom_flange_thickness": float(section.flange_thickness_mm),
            }
        self.update()

    def set_dimensions(
        self,
        *,
        depth_mm: float,
        flange_width_mm: float,
        web_thickness_mm: float,
        flange_thickness_mm: float,
        bottom_flange_width_mm: Optional[float] = None,
        bottom_flange_thickness_mm: Optional[float] = None,
    ) -> None:
        """Feed custom dimensions (e.g., welded sections) directly."""

        self._section = None
        self._dimensions = {
            "depth": float(depth_mm),
            "top_flange_width": float(flange_width_mm),
            "bottom_flange_width": float(bottom_flange_width_mm or flange_width_mm),
            "web_thickness": float(web_thickness_mm),
            "top_flange_thickness": float(flange_thickness_mm),
            "bottom_flange_thickness": float(bottom_flange_thickness_mm or flange_thickness_mm),
        }
        self.update()

    def clear(self) -> None:
        """Reset the preview to an empty placeholder."""

        self._section = None
        self._dimensions = {}
        self.update()

    # ------------------------------------------------------------------
    # QWidget overrides
    # ------------------------------------------------------------------
    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: D401 - Qt override
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), self.palette().window())

        if not self._dimensions:
            self._draw_placeholder(painter)
            return

        dims = self._dimensions
        depth = max(dims.get("depth", 0.0), 1.0)
        top_width = max(dims.get("top_flange_width", 0.0), 1.0)
        bottom_width = max(dims.get("bottom_flange_width", top_width), 1.0)
        web_thickness = max(dims.get("web_thickness", 0.0), 0.5)
        top_thickness = max(dims.get("top_flange_thickness", 0.0), 0.5)
        bottom_thickness = max(dims.get("bottom_flange_thickness", top_thickness), 0.5)

        usable_rect = self.rect().adjusted(
            self._outer_margin,
            self._outer_margin,
            -self._outer_margin,
            -self._outer_margin,
        )
        beam_rect = QRectF(
            usable_rect.left() + self._annotation_margin_left,
            usable_rect.top() + self._annotation_margin_top,
            max(20.0, usable_rect.width() - self._annotation_margin_left - self._annotation_margin_right),
            max(20.0, usable_rect.height() - self._annotation_margin_top - self._annotation_margin_bottom),
        )

        max_width = max(top_width, bottom_width)
        scale_w = beam_rect.width() / max_width
        scale_h = beam_rect.height() / depth
        scale = min(scale_w, scale_h) * 0.92

        beam_height = depth * scale
        top_height = min(top_thickness * scale, beam_height * 0.4)
        bottom_height = min(bottom_thickness * scale, beam_height * 0.4)
        web_height = max(beam_height - top_height - bottom_height, scale * 2.0)

        center_x = beam_rect.center().x()
        top_y = beam_rect.center().y() - (top_height + web_height + bottom_height) / 2.0

        top_flange = QRectF(
            center_x - (top_width * scale) / 2.0,
            top_y,
            top_width * scale,
            top_height,
        )
        web = QRectF(
            center_x - (web_thickness * scale) / 2.0,
            top_flange.bottom(),
            max(1.0, web_thickness * scale),
            web_height,
        )
        bottom_flange = QRectF(
            center_x - (bottom_width * scale) / 2.0,
            web.bottom(),
            bottom_width * scale,
            bottom_height,
        )

        painter.save()
        outline_pen = QPen(self._outline_color, self._outline_width)
        outline_pen.setJoinStyle(Qt.MiterJoin)
        painter.setPen(outline_pen)
        painter.setBrush(QColor("#fefefe"))
        painter.drawRect(top_flange)
        painter.drawRect(web)
        painter.drawRect(bottom_flange)
        painter.restore()

        dim_pen = QPen(self._dimension_color, 1.6)
        dim_pen.setCosmetic(True)
        dim_pen.setCapStyle(Qt.FlatCap)
        painter.setPen(dim_pen)

        font = QFont(self.font())
        font.setPointSizeF(max(9.0, font.pointSizeF()))
        painter.setFont(font)
        painter.setPen(dim_pen)

        # --- Top flange width dimension ---
        width_dim_y = top_flange.top() - self._dim_gap
        painter.drawLine(QPointF(top_flange.left(), top_flange.top()), QPointF(top_flange.left(), width_dim_y))
        painter.drawLine(QPointF(top_flange.right(), top_flange.top()), QPointF(top_flange.right(), width_dim_y))
        self._draw_dimension_line(
            painter,
            QPointF(top_flange.left(), width_dim_y),
            QPointF(top_flange.right(), width_dim_y),
        )
        self._draw_label(
            painter,
            f"Top flange width: {self._format_mm(top_width)}",
            QPointF(top_flange.center().x(), width_dim_y - 10),
            Qt.AlignHCenter | Qt.AlignBottom,
        )

        # --- Flange thickness dimension (top) ---
        flange_dim_x = top_flange.left() - self._dim_gap
        painter.drawLine(QPointF(top_flange.left(), top_flange.top()), QPointF(flange_dim_x, top_flange.top()))
        painter.drawLine(QPointF(top_flange.left(), top_flange.bottom()), QPointF(flange_dim_x, top_flange.bottom()))
        self._draw_dimension_line(
            painter,
            QPointF(flange_dim_x, top_flange.top()),
            QPointF(flange_dim_x, top_flange.bottom()),
        )
        self._draw_label(
            painter,
            f"Top flange thickness: {self._format_mm(top_thickness)}",
            QPointF(flange_dim_x - 8, top_flange.center().y()),
            Qt.AlignRight | Qt.AlignVCenter,
        )

        # --- Bottom flange width dimension ---
        bottom_width_dim_y = bottom_flange.bottom() + self._dim_gap
        painter.drawLine(QPointF(bottom_flange.left(), bottom_flange.bottom()), QPointF(bottom_flange.left(), bottom_width_dim_y))
        painter.drawLine(QPointF(bottom_flange.right(), bottom_flange.bottom()), QPointF(bottom_flange.right(), bottom_width_dim_y))
        self._draw_dimension_line(
            painter,
            QPointF(bottom_flange.left(), bottom_width_dim_y),
            QPointF(bottom_flange.right(), bottom_width_dim_y),
        )
        self._draw_label(
            painter,
            f"Bottom flange width: {self._format_mm(bottom_width)}",
            QPointF(bottom_flange.center().x(), bottom_width_dim_y + 10),
            Qt.AlignHCenter | Qt.AlignTop,
        )

        # --- Flange thickness dimension (bottom) ---
        bottom_thickness_dim_x = bottom_flange.right() + self._dim_gap + self._arrow_size * 1.5
        painter.drawLine(QPointF(bottom_flange.right(), bottom_flange.top()), QPointF(bottom_thickness_dim_x, bottom_flange.top()))
        painter.drawLine(QPointF(bottom_flange.right(), bottom_flange.bottom()), QPointF(bottom_thickness_dim_x, bottom_flange.bottom()))
        self._draw_dimension_line(
            painter,
            QPointF(bottom_thickness_dim_x, bottom_flange.top()),
            QPointF(bottom_thickness_dim_x, bottom_flange.bottom()),
        )
        self._draw_label(
            painter,
            f"Bottom flange thickness: {self._format_mm(bottom_thickness)}",
            QPointF(bottom_thickness_dim_x + 8, bottom_flange.center().y()),
            Qt.AlignLeft | Qt.AlignVCenter,
        )

        # --- Overall depth dimension ---
        depth_dim_x = bottom_thickness_dim_x + self._dim_gap + self._arrow_size * 2.0
        painter.drawLine(QPointF(bottom_flange.right(), top_flange.top()), QPointF(depth_dim_x, top_flange.top()))
        painter.drawLine(QPointF(bottom_flange.right(), bottom_flange.bottom()), QPointF(depth_dim_x, bottom_flange.bottom()))
        self._draw_dimension_line(
            painter,
            QPointF(depth_dim_x, top_flange.top()),
            QPointF(depth_dim_x, bottom_flange.bottom()),
        )
        self._draw_label(
            painter,
            f"Depth: {self._format_mm(depth)}",
            QPointF(depth_dim_x + 10, (top_flange.top() + bottom_flange.bottom()) / 2.0),
            Qt.AlignLeft | Qt.AlignVCenter,
        )

        # --- Web thickness dimension ---
        mid_y = web.center().y()
        self._draw_dimension_line(
            painter,
            QPointF(web.left(), mid_y),
            QPointF(web.right(), mid_y),
        )
        painter.drawLine(QPointF(web.left(), mid_y), QPointF(web.left(), mid_y + self._dim_gap * 0.7))
        painter.drawLine(QPointF(web.right(), mid_y), QPointF(web.right(), mid_y + self._dim_gap * 0.7))
        self._draw_label(
            painter,
            f"Web thickness: {self._format_mm(web_thickness)}",
            QPointF(web.center().x(), mid_y + self._dim_gap * 0.7 + 6),
            Qt.AlignHCenter | Qt.AlignTop,
        )

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------
    def _draw_placeholder(self, painter: QPainter) -> None:
        painter.save()
        pen = QPen(QColor("#b7b7b7"), 1.2, Qt.DashLine)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.drawRect(self.rect().adjusted(12, 12, -12, -12))
        painter.setPen(QColor("#6f6f6f"))
        font = QFont(self.font())
        font.setPointSizeF(max(font.pointSizeF(), 10.0))
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, "Select a rolled section to preview")
        painter.restore()

    def _draw_dimension_line(self, painter: QPainter, start: QPointF, end: QPointF) -> None:
        direction = QPointF(end.x() - start.x(), end.y() - start.y())
        length = math.hypot(direction.x(), direction.y())
        if length == 0:
            return
        unit = QPointF(direction.x() / length, direction.y() / length)
        offset = unit * (self._arrow_size * 0.7)
        painter.drawLine(start + offset, end - offset)
        self._draw_arrow_head(painter, start, direction)
        self._draw_arrow_head(painter, end, QPointF(-direction.x(), -direction.y()))

    def _draw_arrow_head(self, painter: QPainter, tip: QPointF, direction: QPointF) -> None:
        length = math.hypot(direction.x(), direction.y())
        if length == 0:
            return
        unit = QPointF(direction.x() / length, direction.y() / length)
        normal = QPointF(-unit.y(), unit.x())
        arrow = self._arrow_size
        base = tip + unit * (arrow * 0.9)
        left = base + normal * (arrow * 0.45)
        right = base - normal * (arrow * 0.45)
        painter.save()
        painter.setBrush(self._dimension_color)
        painter.setPen(Qt.NoPen)
        painter.drawPolygon([tip, left, right])
        painter.restore()

    def _draw_label(self, painter: QPainter, text: str, anchor: QPointF, align: Qt.Alignment) -> None:
        metrics = QFontMetricsF(painter.font())
        text_rect = metrics.boundingRect(text).adjusted(-6, -3, 6, 3)
        rect = QRectF(0, 0, text_rect.width(), text_rect.height())

        if align & Qt.AlignLeft:
            rect.moveLeft(anchor.x())
        elif align & Qt.AlignRight:
            rect.moveRight(anchor.x())
        else:
            rect.moveCenter(QPointF(anchor.x(), rect.center().y()))

        if align & Qt.AlignTop:
            rect.moveTop(anchor.y())
        elif align & Qt.AlignBottom:
            rect.moveBottom(anchor.y())
        else:
            rect.moveCenter(QPointF(rect.center().x(), anchor.y()))

        painter.save()
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._label_bg)
        painter.drawRoundedRect(rect, 4, 4)
        painter.restore()

        painter.save()
        painter.setPen(self._text_color)
        painter.drawText(rect, Qt.AlignCenter, text)
        painter.restore()

    @staticmethod
    def _format_mm(value: float) -> str:
        rounded = round(value)
        if abs(value - rounded) < 0.01:
            return f"{rounded} mm"
        return f"{value:.1f} mm"
