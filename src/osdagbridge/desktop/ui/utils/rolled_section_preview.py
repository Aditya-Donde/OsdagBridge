"""Interactive section preview widget shared across Additional Inputs tabs."""
from __future__ import annotations

import math
from typing import Any, Dict, Optional

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPaintEvent, QPainterPath, QPen, QTextDocument
from PySide6.QtWidgets import QSizePolicy, QWidget

from osdagbridge.desktop.ui.utils.cad_palette import (
    CAD_CANVAS_BG,
    CAD_DIMENSION,
    CAD_LABEL_BG,
    CAD_OUTLINE,
    CAD_PLACEHOLDER_BORDER,
    CAD_PLACEHOLDER_TEXT,
    CAD_SHAPE_FILL,
    CAD_TEXT,
    OSDAG_BRAND_GREEN,
    OSDAG_FONT_FAMILY,
)

try:  # pragma: no cover - optional dependency
    from osdagbridge.core.bridge_components.super_structure.girder.properties import BeamSection  # type: ignore
except Exception:  # pragma: no cover - fallback when module missing in current build
    BeamSection = Any  # type: ignore[misc,assignment]

class RolledSectionPreview(QWidget):
    """Render a rolled or welded section with CAD-style dimension annotations."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._section: Optional[BeamSection] = None
        self._dimensions: Dict[str, float] = {}

        self._outline_color = QColor(CAD_OUTLINE)
        self._outline_width = 3.0
        self._brand_color = QColor(OSDAG_BRAND_GREEN)
        self._dimension_color = QColor(CAD_DIMENSION)
        self._dimension_keys = ("tfw", "tft", "bfw", "bft", "d", "wt")
        self._dimension_palette = {key: QColor(CAD_DIMENSION) for key in self._dimension_keys}
        self._label_bg = QColor(CAD_LABEL_BG)
        self._text_color = QColor(CAD_TEXT)
        self._brand_font_family = OSDAG_FONT_FAMILY
        self._show_welds = False

        self._outer_margin = 16
        self._annotation_margin_top = 36
        self._annotation_margin_bottom = 28
        self._annotation_margin_left = 52
        self._annotation_margin_right = 74
        self._dim_gap = 12
        self._arrow_size = 9

        self._min_root_radius_px = 8.0
        self._min_toe_radius_px = 4.0

        self.setMinimumSize(360, 260)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def set_section(self, section: Optional[BeamSection]) -> None:
        """Update the preview to show the supplied rolled ``BeamSection``."""

        self._section = section
        if section is None:
            self._dimensions = {}
        else:
            self._dimensions = {
                "depth": self._extract_dimension(section, ("depth_mm", "depth"), 0.0),
                "top_flange_width": self._extract_dimension(section, ("flange_width_mm", "top_flange_width_mm"), 0.0),
                "bottom_flange_width": self._extract_dimension(section, ("flange_width_mm", "bottom_flange_width_mm"), 0.0),
                "web_thickness": self._extract_dimension(section, ("web_thickness_mm", "web_thickness"), 0.0),
                "top_flange_thickness": self._extract_dimension(section, ("flange_thickness_mm", "top_flange_thickness_mm"), 0.0),
                "bottom_flange_thickness": self._extract_dimension(section, ("flange_thickness_mm", "bottom_flange_thickness_mm"), 0.0),
                "root_radius_mm": self._extract_dimension(section, ("root_radius_r1_mm", "root_radius_mm", "root_radius"), 0.0),
                "toe_radius_mm": self._extract_dimension(section, ("root_radius_r2_mm", "toe_radius_mm", "toe_radius"), 0.0),
            }
        self._show_welds = False
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
        show_welds: bool = False,
    ) -> None:
        """Feed custom dimensions directly (e.g., for welded sections)."""

        self._section = None
        self._dimensions = {
            "depth": float(depth_mm),
            "top_flange_width": float(flange_width_mm),
            "bottom_flange_width": float(bottom_flange_width_mm or flange_width_mm),
            "web_thickness": float(web_thickness_mm),
            "top_flange_thickness": float(flange_thickness_mm),
            "bottom_flange_thickness": float(bottom_flange_thickness_mm or flange_thickness_mm),
            "root_radius_mm": 0.0,
            "toe_radius_mm": 0.0,
        }
        self._show_welds = show_welds
        self.update()

    def clear(self) -> None:
        """Reset the preview to an empty placeholder."""

        self._section = None
        self._dimensions = {}
        self._show_welds = False
        self.update()

    # ------------------------------------------------------------------
    # QWidget overrides
    # ------------------------------------------------------------------
    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: D401 - Qt override
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        # Force a light canvas so the widget stays readable even when the
        # application uses a dark palette.
        painter.fillRect(self.rect(), QColor(CAD_CANVAS_BG))

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
            self._outer_margin + 20,
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

        root_radius_px = float(dims.get("root_radius_mm", 0.0)) * scale
        toe_radius_px = float(dims.get("toe_radius_mm", 0.0)) * scale

        section_path = self._build_section_path(
            top_flange,
            web,
            bottom_flange,
            root_radius_px,
            toe_radius_px,
        )

        painter.save()
        outline_pen = QPen(self._outline_color, self._outline_width)
        outline_pen.setJoinStyle(Qt.MiterJoin)
        painter.setPen(outline_pen)
        painter.setBrush(QColor(CAD_SHAPE_FILL))
        if section_path is not None:
            painter.drawPath(section_path)
        else:
            painter.drawRect(top_flange)
            painter.drawRect(web)
            painter.drawRect(bottom_flange)
        painter.restore()

        if self._show_welds:
            self._draw_welds(painter, top_flange, web, bottom_flange)

        font = QFont(self.font())
        font.setFamily(self._brand_font_family)
        font.setPointSizeF(max(9.0, font.pointSizeF()))
        painter.setFont(font)

        tfw_color = self._set_dimension_pen(painter, "tfw")
        width_dim_y = self._snap_coordinate(top_flange.top() - self._dim_gap)
        left_extension_end = QPointF(self._snap_coordinate(top_flange.left()), width_dim_y)
        right_extension_end = QPointF(self._snap_coordinate(top_flange.right()), width_dim_y)
        painter.drawLine(QPointF(left_extension_end.x(), top_flange.top()), left_extension_end)
        painter.drawLine(QPointF(right_extension_end.x(), top_flange.top()), right_extension_end)
        self._draw_dimension_line(
            painter,
            left_extension_end,
            right_extension_end,
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

        bfw_color = self._set_dimension_pen(painter, "bfw")
        bottom_width_dim_y = self._snap_coordinate(bottom_flange.bottom() + self._dim_gap)
        bottom_left_extension = QPointF(self._snap_coordinate(bottom_flange.left()), bottom_width_dim_y)
        bottom_right_extension = QPointF(self._snap_coordinate(bottom_flange.right()), bottom_width_dim_y)
        painter.drawLine(QPointF(bottom_left_extension.x(), bottom_flange.bottom()), bottom_left_extension)
        painter.drawLine(QPointF(bottom_right_extension.x(), bottom_flange.bottom()), bottom_right_extension)
        self._draw_dimension_line(
            painter,
            bottom_left_extension,
            bottom_right_extension,
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

        depth_color = self._set_dimension_pen(painter, "d")
        anchor_x = self._snap_coordinate(bottom_flange.right())
        depth_dim_x = self._snap_coordinate(anchor_x + self._dim_gap)
        top_depth_extension = QPointF(depth_dim_x, self._snap_coordinate(top_flange.top()))
        bottom_depth_extension = QPointF(depth_dim_x, self._snap_coordinate(bottom_flange.bottom()))
        painter.drawLine(QPointF(anchor_x, top_depth_extension.y()), top_depth_extension)
        painter.drawLine(QPointF(anchor_x, bottom_depth_extension.y()), bottom_depth_extension)
        self._draw_dimension_line(
            painter,
            top_depth_extension,
            bottom_depth_extension,
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
    def _build_section_path(
        self,
        top_flange: QRectF,
        web: QRectF,
        bottom_flange: QRectF,
        root_radius: float,
        toe_radius: float,
    ) -> Optional[QPainterPath]:
        if min(top_flange.width(), bottom_flange.width(), web.width()) <= 0:
            return None

        tf_left, tf_right = top_flange.left(), top_flange.right()
        tf_top, tf_bottom = top_flange.top(), top_flange.bottom()
        bf_left, bf_right = bottom_flange.left(), bottom_flange.right()
        bf_top, bf_bottom = bottom_flange.top(), bottom_flange.bottom()
        web_left, web_right = web.left(), web.right()

        top_root = self._effective_root_radius_px(root_radius, top_flange, web)
        bottom_root = self._effective_root_radius_px(root_radius, bottom_flange, web)
        top_toe = self._effective_toe_radius_px(toe_radius, top_flange)
        bottom_toe = self._effective_toe_radius_px(toe_radius, bottom_flange)

        path = QPainterPath()
        path.moveTo(tf_left, tf_top)
        path.lineTo(tf_right, tf_top)
        path.lineTo(tf_right, tf_bottom - top_toe)
        if top_toe > 0:
            rect = QRectF(tf_right - 2 * top_toe, tf_bottom - 2 * top_toe, 2 * top_toe, 2 * top_toe)
            path.arcTo(rect, 0, -90)
        else:
            path.lineTo(tf_right, tf_bottom)
        path.lineTo(web_right + top_root, tf_bottom)
        if top_root > 0:
            rect = QRectF(web_right, tf_bottom, 2 * top_root, 2 * top_root)
            path.arcTo(rect, 90, 90)
        else:
            path.lineTo(web_right, tf_bottom)
        path.lineTo(web_right, bf_top - bottom_root)
        if bottom_root > 0:
            rect = QRectF(web_right, bf_top - 2 * bottom_root, 2 * bottom_root, 2 * bottom_root)
            path.arcTo(rect, 180, 90)
        else:
            path.lineTo(web_right, bf_top)
        path.lineTo(bf_right - bottom_toe, bf_top)
        if bottom_toe > 0:
            rect = QRectF(bf_right - 2 * bottom_toe, bf_top, 2 * bottom_toe, 2 * bottom_toe)
            path.arcTo(rect, 90, -90)
        else:
            path.lineTo(bf_right, bf_top)
        path.lineTo(bf_right, bf_bottom)
        path.lineTo(bf_left, bf_bottom)
        path.lineTo(bf_left, bf_top + bottom_toe)
        if bottom_toe > 0:
            rect = QRectF(bf_left, bf_top, 2 * bottom_toe, 2 * bottom_toe)
            path.arcTo(rect, 180, -90)
        else:
            path.lineTo(bf_left, bf_top)
        path.lineTo(web_left - bottom_root, bf_top)
        if bottom_root > 0:
            rect = QRectF(web_left - 2 * bottom_root, bf_top - 2 * bottom_root, 2 * bottom_root, 2 * bottom_root)
            path.arcTo(rect, 270, 90)
        else:
            path.lineTo(web_left, bf_top)
        path.lineTo(web_left, tf_bottom + top_root)
        if top_root > 0:
            rect = QRectF(web_left - 2 * top_root, tf_bottom, 2 * top_root, 2 * top_root)
            path.arcTo(rect, 0, 90)
        else:
            path.lineTo(web_left, tf_bottom)
        path.lineTo(tf_left + top_toe, tf_bottom)
        if top_toe > 0:
            rect = QRectF(tf_left, tf_bottom - 2 * top_toe, 2 * top_toe, 2 * top_toe)
            path.arcTo(rect, 270, -90)
        else:
            path.lineTo(tf_left, tf_bottom)
        path.lineTo(tf_left, tf_top)
        path.closeSubpath()
        return path

    def _snap_coordinate(self, value: float, *, precision: float = 0.5) -> float:
        if not precision or precision <= 0:
            return value
        return round(value / precision) * precision

    def _effective_toe_radius_px(self, requested: float, flange: QRectF) -> float:
        if self._show_welds:
            return 0.0
        max_radius = max(0.0, min(flange.width() / 2.0, flange.height()))
        if max_radius == 0.0:
            return 0.0
        val = max(requested, self._min_toe_radius_px)
        return self._snap_coordinate(min(val, max_radius))

    def _effective_root_radius_px(self, requested: float, flange: QRectF, web: QRectF) -> float:
        if self._show_welds:
            return 0.0
        flange_overhang = (flange.width() - web.width()) / 2.0
        max_radius = max(0.0, min(flange_overhang, web.height() / 2.0))
        if max_radius == 0.0:
            return 0.0
        val = max(requested, self._min_root_radius_px)
        return self._snap_coordinate(min(val, max_radius))

    def _draw_welds(self, painter: QPainter, top_flange: QRectF, web: QRectF, bottom_flange: QRectF) -> None:
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        # Keep weld triangles visible on a light theme.
        fill_color = QColor("#111111")
        outline_pen = QPen(QColor("#111111"), 0.9)
        outline_pen.setCosmetic(True)
        painter.setBrush(fill_color)
        painter.setPen(outline_pen)

        horizontal_leg = max(4.0, min(web.width() * 0.8, 24.0))
        top_vertical_leg = max(4.0, min(top_flange.height() * 0.9, 22.0))
        bottom_vertical_leg = max(4.0, min(bottom_flange.height() * 0.9, 22.0))

        for sign in (-1, 1):
            top_corner_x = web.left() if sign < 0 else web.right()
            top_corner = QPointF(top_corner_x, top_flange.bottom())
            painter.drawPath(
                self._build_fillet_path(
                    top_corner,
                    horizontal_leg,
                    top_vertical_leg,
                    horizontal_sign=sign,
                    vertical_sign=1.0,
                )
            )

            bottom_corner_x = web.left() if sign < 0 else web.right()
            bottom_corner = QPointF(bottom_corner_x, bottom_flange.top())
            painter.drawPath(
                self._build_fillet_path(
                    bottom_corner,
                    horizontal_leg,
                    bottom_vertical_leg,
                    horizontal_sign=sign,
                    vertical_sign=-1.0,
                )
            )

        painter.restore()

    def _build_fillet_path(
        self,
        corner: QPointF,
        horizontal_leg: float,
        vertical_leg: float,
        *,
        horizontal_sign: float,
        vertical_sign: float,
    ) -> QPainterPath:
        leg_x = horizontal_leg * horizontal_sign
        leg_y = vertical_leg * vertical_sign
        path = QPainterPath(corner)
        path.lineTo(QPointF(corner.x() + leg_x, corner.y()))
        control = QPointF(corner.x() + leg_x * 0.55, corner.y() + leg_y * 0.55)
        path.quadTo(control, QPointF(corner.x(), corner.y() + leg_y))
        path.closeSubpath()
        return path

    def _draw_placeholder(self, painter: QPainter) -> None:
        painter.save()
        pen = QPen(QColor(CAD_PLACEHOLDER_BORDER), 1.2, Qt.DashLine)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.drawRect(self.rect().adjusted(12, 12, -12, -12))
        painter.setPen(QColor(CAD_PLACEHOLDER_TEXT))
        font = QFont(self.font())
        font.setFamily(self._brand_font_family)
        font.setPointSizeF(max(font.pointSizeF(), 10.0))
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, "Select a section to preview")
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
        anchor_x = self._snap_coordinate(flange_edge_x)
        dimension_x = self._snap_coordinate(anchor_x - extension)
        snapped_top_y = self._snap_coordinate(top_y)
        snapped_bottom_y = self._snap_coordinate(bottom_y)
        top_extension = QPointF(dimension_x, snapped_top_y)
        bottom_extension = QPointF(dimension_x, snapped_bottom_y)

        painter.drawLine(QPointF(anchor_x, snapped_top_y), top_extension)
        painter.drawLine(QPointF(anchor_x, snapped_bottom_y), bottom_extension)
        painter.drawLine(top_extension, bottom_extension)
        self._draw_arrow_head(painter, top_extension, QPointF(0, -1), color)
        self._draw_arrow_head(painter, bottom_extension, QPointF(0, 1), color)

        label_anchor = QPointF(
            dimension_x - self._dim_gap * 0.4,
            (snapped_top_y + snapped_bottom_y) / 2.0,
        )
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
        snapped_mid_y = self._snap_coordinate(mid_y)
        left_point = QPointF(self._snap_coordinate(left_x), snapped_mid_y)
        right_point = QPointF(self._snap_coordinate(right_x), snapped_mid_y)
        painter.drawLine(left_point, right_point)
        self._draw_arrow_head(painter, left_point, QPointF(-1, 0), color)
        self._draw_arrow_head(painter, right_point, QPointF(1, 0), color)

        label_offset = self._dim_gap * 0.6
        label_anchor = QPointF(left_point.x() - label_offset, snapped_mid_y)
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
        painter.drawLine(start, end)
        self._draw_arrow_head(painter, start, direction, color)
        self._draw_arrow_head(painter, end, QPointF(-direction.x(), -direction.y()), color)

    def _draw_arrow_head(self, painter: QPainter, tip: QPointF, direction: QPointF, color: QColor) -> None:
        length = math.hypot(direction.x(), direction.y())
        if length == 0:
            return

        unit = QPointF(direction.x() / length, direction.y() / length)
        normal = QPointF(-unit.y(), unit.x())

        arrow = self._arrow_size
        arrow_length = arrow * 1.3
        arrow_half_width = arrow * 0.25

        base = tip + unit * arrow_length
        left = base + normal * arrow_half_width
        right = base - normal * arrow_half_width

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

    @staticmethod
    def _extract_dimension(section: BeamSection, names, default: float) -> float:
        for attr in names if isinstance(names, (tuple, list)) else (names,):
            if hasattr(section, attr):
                raw = getattr(section, attr)
                if raw is not None:
                    try:
                        return float(raw)
                    except (TypeError, ValueError):
                        continue
        return float(default)
