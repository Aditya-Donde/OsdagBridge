"""Interactive beam preview widget with CAD-style annotations."""

from __future__ import annotations

import math
from typing import Dict, Optional

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QPainter, QPaintEvent, QPen, QTextDocument
from PySide6.QtWidgets import QSizePolicy, QWidget

from osdagbridge.core.bridge_components.super_structure.girder.properties import BeamSection


OSDAG_BRAND_GREEN = QColor("#90AF13")
OSDAG_FONT_FAMILY = "Ubuntu Sans"


class RolledSectionPreview(QWidget):
    """Render a rolled section with CAD-style dimension annotations."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._section: Optional[BeamSection] = None
        self._dimensions: Dict[str, float] = {}

        self._outline_color = QColor("#1b1b1b")
        self._outline_width = 3.0
        self._brand_color = QColor(OSDAG_BRAND_GREEN)
        self._dimension_color = QColor(OSDAG_BRAND_GREEN)
        self._dimension_keys = ("tfw", "tft", "bfw", "bft", "d", "wt")
        self._dimension_palette = {key: QColor(OSDAG_BRAND_GREEN) for key in self._dimension_keys}
        self._label_bg = QColor(255, 255, 255, 230)
        self._text_color = QColor("#0f0f0f")
        self._brand_font_family = OSDAG_FONT_FAMILY

        self._outer_margin = 16
        self._annotation_margin_top = 36
        self._annotation_margin_bottom = 28
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
            self._outer_margin + 20,  # extra left space for labels
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

        font = QFont(self.font())
        font.setFamily(self._brand_font_family)
        font.setPointSizeF(max(9.0, font.pointSizeF()))
        painter.setFont(font)

        # --- Top flange width dimension ---
        tfw_color = self._set_dimension_pen(painter, "tfw")
        width_dim_y = top_flange.top() - self._dim_gap
        painter.drawLine(QPointF(top_flange.left(), top_flange.top()), QPointF(top_flange.left(), width_dim_y))
        painter.drawLine(QPointF(top_flange.right(), top_flange.top()), QPointF(top_flange.right(), width_dim_y))
        self._draw_dimension_line(
            painter,
            QPointF(top_flange.left(), width_dim_y),
            QPointF(top_flange.right(), width_dim_y),
            tfw_color,
        )
        self._draw_label(
            painter,
            self._format_label_markup("tfw", top_width),
            QPointF(top_flange.center().x(), width_dim_y - 6),
            Qt.AlignHCenter | Qt.AlignBottom,
            with_background=False,
            color=tfw_color,
        )

        # --- Top flange thickness dimension ---
        tft_color = self._set_dimension_pen(painter, "tft")
        self._draw_vertical_thickness_dimension(
            painter,
            top_flange.left(),
            top_flange.top(),
            top_flange.bottom(),
            top_thickness,
            tft_color,
            label_symbol="tft",
            label_align=Qt.AlignRight | Qt.AlignVCenter,
        )

        # --- Bottom flange width dimension ---
        bfw_color = self._set_dimension_pen(painter, "bfw")
        bottom_width_dim_y = bottom_flange.bottom() + self._dim_gap
        painter.drawLine(QPointF(bottom_flange.left(), bottom_flange.bottom()), QPointF(bottom_flange.left(), bottom_width_dim_y))
        painter.drawLine(QPointF(bottom_flange.right(), bottom_flange.bottom()), QPointF(bottom_flange.right(), bottom_width_dim_y))
        self._draw_dimension_line(
            painter,
            QPointF(bottom_flange.left(), bottom_width_dim_y),
            QPointF(bottom_flange.right(), bottom_width_dim_y),
            bfw_color,
        )
        self._draw_label(
            painter,
            self._format_label_markup("bfw", bottom_width),
            QPointF(bottom_flange.center().x(), bottom_width_dim_y + 6),
            Qt.AlignHCenter | Qt.AlignTop,
            with_background=False,
            color=bfw_color,
        )

        # --- Bottom flange thickness dimension ---
        bft_color = self._set_dimension_pen(painter, "bft")
        self._draw_vertical_thickness_dimension(
            painter,
            bottom_flange.left(),
            bottom_flange.top(),
            bottom_flange.bottom(),
            bottom_thickness,
            bft_color,
            label_symbol="bft",
            label_align=Qt.AlignRight | Qt.AlignVCenter,
        )

        # --- Overall depth dimension ---
        depth_color = self._set_dimension_pen(painter, "d")
        depth_dim_x = bottom_flange.right() + self._dim_gap
        painter.drawLine(QPointF(bottom_flange.right(), top_flange.top()), QPointF(depth_dim_x, top_flange.top()))
        painter.drawLine(QPointF(bottom_flange.right(), bottom_flange.bottom()), QPointF(depth_dim_x, bottom_flange.bottom()))
        self._draw_dimension_line(
            painter,
            QPointF(depth_dim_x, top_flange.top()),
            QPointF(depth_dim_x, bottom_flange.bottom()),
            depth_color,
        )
        self._draw_label(
            painter,
            self._format_label_markup("d", depth),
            QPointF(depth_dim_x + 10, (top_flange.top() + bottom_flange.bottom()) / 2.0),
            Qt.AlignLeft | Qt.AlignVCenter,
            with_background=False,
            color=depth_color,
        )

        # --- Web thickness dimension ---
        wt_color = self._set_dimension_pen(painter, "wt")
        self._draw_web_thickness_dimension(
            painter,
            web.left(),
            web.right(),
            web.center().y(),
            web_thickness,
            wt_color,
            label_symbol="wt",
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
        font.setFamily(self._brand_font_family)
        font.setPointSizeF(max(font.pointSizeF(), 10.0))
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, "Select a rolled section to preview")
        painter.restore()

    def _set_dimension_pen(self, painter: QPainter, key: str) -> QColor:
        color = self._dimension_palette.get(key, self._dimension_color)
        pen = QPen(color, 1.6)
        pen.setCosmetic(True)
        pen.setCapStyle(Qt.FlatCap)
        painter.setPen(pen)
        return color

    def _draw_vertical_thickness_dimension(
        self,
        painter: QPainter,
        flange_edge_x: float,
        top_y: float,
        bottom_y: float,
        thickness: Optional[float],
        color: QColor,
        *,
        label_symbol: str,
        label_align: Qt.Alignment,
    ) -> None:
        extension = self._dim_gap * 0.9
        arrow_length = max(self._dim_gap * 1.2, self._arrow_size * 1.4)
        dimension_x = flange_edge_x - extension
        top_extension = QPointF(dimension_x, top_y)
        bottom_extension = QPointF(dimension_x, bottom_y)

        painter.drawLine(QPointF(flange_edge_x, top_y), top_extension)
        painter.drawLine(QPointF(flange_edge_x, bottom_y), bottom_extension)
        painter.drawLine(top_extension, bottom_extension)

        painter.drawLine(QPointF(dimension_x, top_y - arrow_length), top_extension)
        painter.drawLine(bottom_extension, QPointF(dimension_x, bottom_y + arrow_length))
        self._draw_arrow_head(painter, top_extension, QPointF(0, -1), color)
        self._draw_arrow_head(painter, bottom_extension, QPointF(0, 1), color)

        label_anchor = QPointF(dimension_x - self._dim_gap * 0.4, (top_y + bottom_y) / 2.0)
        self._draw_label(
            painter,
            self._format_label_markup(label_symbol, thickness),
            label_anchor,
            label_align,
            with_background=False,
            color=color,
        )

    def _draw_web_thickness_dimension(
        self,
        painter: QPainter,
        left_x: float,
        right_x: float,
        mid_y: float,
        thickness: Optional[float],
        color: QColor,
        *,
        label_symbol: str,
    ) -> None:
        extension = self._dim_gap * 0.7
        arrow_length = max(self._dim_gap * 1.2, self._arrow_size * 1.4)

        painter.drawLine(QPointF(left_x, mid_y - extension), QPointF(left_x, mid_y + extension))
        painter.drawLine(QPointF(right_x, mid_y - extension), QPointF(right_x, mid_y + extension))

        painter.drawLine(QPointF(left_x - arrow_length, mid_y), QPointF(left_x, mid_y))
        painter.drawLine(QPointF(right_x, mid_y), QPointF(right_x + arrow_length, mid_y))
        self._draw_arrow_head(painter, QPointF(left_x, mid_y), QPointF(-1, 0), color)
        self._draw_arrow_head(painter, QPointF(right_x, mid_y), QPointF(1, 0), color)

        label_offset = self._dim_gap * 0.6
        label_anchor = QPointF(left_x - arrow_length - label_offset, mid_y)
        self._draw_label(
            painter,
            self._format_label_markup(label_symbol, thickness),
            label_anchor,
            Qt.AlignRight | Qt.AlignVCenter,
            with_background=False,
            color=color,
        )

    def _draw_dimension_line(
        self,
        painter: QPainter,
        start: QPointF,
        end: QPointF,
        color: QColor,
        *,
        external: bool = False,
    ) -> None:
        direction = QPointF(end.x() - start.x(), end.y() - start.y())
        length = math.hypot(direction.x(), direction.y())
        if length == 0:
            return
        unit = QPointF(direction.x() / length, direction.y() / length)
        if external:
            painter.drawLine(start, end)
            outward = self._arrow_size * 0.9
            outer_start = QPointF(start.x() - unit.x() * outward, start.y() - unit.y() * outward)
            outer_end = QPointF(end.x() + unit.x() * outward, end.y() + unit.y() * outward)
            self._draw_arrow_head(painter, outer_start, direction, color)
            self._draw_arrow_head(painter, outer_end, QPointF(-direction.x(), -direction.y()), color)
        else:
            offset = unit * (self._arrow_size * 0.7)
            painter.drawLine(start + offset, end - offset)
            self._draw_arrow_head(painter, start, direction, color)
            self._draw_arrow_head(painter, end, QPointF(-direction.x(), -direction.y()), color)

    def _draw_arrow_head(self, painter: QPainter, tip: QPointF, direction: QPointF, color: QColor) -> None:
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
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawPolygon([tip, left, right])
        painter.restore()

    def _draw_label(
        self,
        painter: QPainter,
        text: str,
        anchor: QPointF,
        align: Qt.Alignment,
        *,
        with_background: bool = True,
        color: Optional[QColor] = None,
    ) -> None:
        text_color = color or self._text_color
        html_text = text if color is None else f'<span style="color:{self._color_to_hex(text_color)}">{text}</span>'

        doc = QTextDocument()
        doc.setDefaultFont(painter.font())
        doc.setHtml(html_text)
        text_size = doc.size()
        padding_x = 6
        padding_y = 4
        rect = QRectF(0, 0, text_size.width() + padding_x * 2, text_size.height() + padding_y * 2)

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

        content_rect = QRectF(
            rect.left() + padding_x,
            rect.top() + padding_y,
            text_size.width(),
            text_size.height(),
        )

        if with_background:
            painter.save()
            painter.setPen(Qt.NoPen)
            painter.setBrush(self._label_bg)
            painter.drawRoundedRect(rect, 4, 4)
            painter.restore()

        painter.save()
        painter.translate(content_rect.topLeft())
        doc.drawContents(painter)
        painter.restore()

    def _format_label_markup(self, symbol: str, value: Optional[float] = None) -> str:
        formatted_symbol = self._format_symbol_markup(symbol)
        if value is None:
            return formatted_symbol
        return f"{formatted_symbol} = {self._format_mm(value)}"

    @staticmethod
    def _format_symbol_markup(symbol: str) -> str:
        clean = symbol.lower().strip()
        if len(clean) <= 1:
            return clean or symbol
        return f"{clean[0]}<sub>{clean[1:]}</sub>"

    @staticmethod
    def _color_to_hex(color: QColor) -> str:
        return color.name(QColor.HexRgb)

    @staticmethod
    def _format_mm(value: float) -> str:
        rounded = round(value)
        if abs(value - rounded) < 0.01:
            return f"{rounded} mm"
        return f"{value:.1f} mm"
