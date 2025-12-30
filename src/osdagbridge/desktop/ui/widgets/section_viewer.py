from __future__ import annotations

import math
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget


DB_PATH = Path(__file__).resolve().parents[3] / "core" / "data" / "ResourceFiles" / "Intg_osdag.sqlite"


@dataclass
class AngleSection:
    designation: str
    a: float  # leg 1 (mm)
    b: float  # leg 2 (mm)
    t: float  # thickness (mm)


@dataclass
class ChannelSection:
    designation: str
    d: float  # depth (mm)
    b: float  # flange width (mm)
    tw: float  # web thickness (mm)
    tf: float  # flange thickness (mm)


class SectionCatalog:
    """Lightweight access to Osdag section database."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self._angles: Dict[str, AngleSection] = {}
        self._channels: Dict[str, ChannelSection] = {}
        self._load()

    def _load(self) -> None:
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()

        # Equal and unequal angles
        for table in ("EqualAngle", "UnequalAngle"):
            cur.execute(f"SELECT Designation, a, b, t FROM {table}")
            for des, a, b, t in cur.fetchall():
                self._angles[des.strip()] = AngleSection(designation=des.strip(), a=float(a), b=float(b), t=float(t))

        # Channels
        cur.execute("SELECT Designation, D, B, tw, T FROM Channels")
        for des, d, b, tw, tf in cur.fetchall():
            self._channels[des.strip()] = ChannelSection(designation=des.strip(), d=float(d), b=float(b), tw=float(tw), tf=float(tf))

        con.close()

    def list_angles(self) -> List[str]:
        return sorted(self._angles.keys())

    def list_channels(self) -> List[str]:
        return sorted(self._channels.keys())

    def get_angle(self, designation: str) -> Optional[AngleSection]:
        return self._angles.get(designation.strip())

    def get_channel(self, designation: str) -> Optional[ChannelSection]:
        return self._channels.get(designation.strip())


class SectionPreviewWidget(QWidget):
    """Simple 2D outline renderer for angle/channel variants."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(120)
        self.setMinimumWidth(120)
        self._section_type: str = ""
        self._designation: str = ""
        self._geometry: List[QPainterPath] = []
        self._catalog = SectionCatalog()
        self._dimension_info: Optional[dict] = None
        self._section_fill = True

    def set_section(self, section_type: str, designation: str) -> None:
        """
        section_type: one of [angle, double_angle_long, double_angle_short, channel, double_channel]
        designation: designation string present in the DB (for doubles, pass base designation without the leading 2-)
        """
        self._section_type = section_type
        self._designation = designation
        self._geometry = self._build_geometry(section_type, designation)
        self._dimension_info = self._dimension_for(section_type, designation)
        self._section_fill = section_type.startswith("angle")
        self.update()

    def _dimension_for(self, section_type: str, designation: str) -> Optional[dict]:
        if not designation:
            return None
        if section_type in ("angle", "double_angle_long", "double_angle_short"):
            angle = self._catalog.get_angle(designation)
            if not angle:
                return None
            return {"kind": "angle", "a": angle.a, "b": angle.b, "t": angle.t}
        if section_type in ("channel", "double_channel"):
            ch = self._catalog.get_channel(designation)
            if not ch:
                return None
            return {"kind": "channel", "b": ch.b, "d": ch.d, "tw": ch.tw, "tf": ch.tf}
        return None

    # ---- Geometry builders -------------------------------------------------
    def _build_geometry(self, section_type: str, designation: str) -> List[QPainterPath]:
        if not designation:
            return []
        if section_type in ("angle", "double_angle_long", "double_angle_short"):
            angle = self._catalog.get_angle(designation)
            if not angle:
                return []
            if section_type == "angle":
                return [self._build_angle_path(angle, QPointF(0, 0))]
            elif section_type == "double_angle_long":
                # back-to-back along long leg: mirror across Y axis
                path1 = self._build_angle_path(angle, QPointF(0, 0))
                mirror = self._build_angle_path(angle, QPointF(0, 0), mirror_long_leg=True)
                return [path1, mirror]
            else:
                # back-to-back along short leg: swap legs before mirroring
                swapped = AngleSection(angle.designation, angle.b, angle.a, angle.t)
                path1 = self._build_angle_path(swapped, QPointF(0, 0))
                mirror = self._build_angle_path(swapped, QPointF(0, 0), mirror_long_leg=True)
                return [path1, mirror]

        if section_type in ("channel", "double_channel"):
            ch = self._catalog.get_channel(designation)
            if not ch:
                return []
            if section_type == "channel":
                return [self._build_channel_path(ch, QPointF(0, 0))]
            else:
                # Back-to-back about web centerline (S=0)
                p1 = self._build_channel_path(ch, QPointF(0, 0))
                p2 = self._build_channel_path(ch, QPointF(0, 0), mirror=True)
                return [p1, p2]

        return []

    def _build_angle_path(self, angle: AngleSection, origin: QPointF, mirror_long_leg: bool = False) -> QPainterPath:
        # Outer L profile anchored at origin (0,0) at corner; legs along +x/+y.
        # When mirrored, flip across the Y-axis and offset by thickness so the two angles sit back-to-back without overlapping lines.
        a, b, t = angle.a, angle.b, angle.t
        sign = -1.0 if mirror_long_leg else 1.0
        offset_x = -t if mirror_long_leg else 0.0
        x0, y0 = origin.x() + offset_x, origin.y()

        path = QPainterPath()
        # Outline for solid L (union of two rectangles) without inner cutout lines.
        pts_outer = [
            QPointF(x0, y0),
            QPointF(x0 + sign * a, y0),
            QPointF(x0 + sign * a, y0 + t),
            QPointF(x0 + sign * t, y0 + t),
            QPointF(x0 + sign * t, y0 + b),
            QPointF(x0, y0 + b),
        ]
        path.moveTo(pts_outer[0])
        for pt in pts_outer[1:]:
            path.lineTo(pt)
        path.closeSubpath()
        return path

    def _build_channel_path(self, ch: ChannelSection, origin: QPointF, mirror: bool = False) -> QPainterPath:
        # C-section outline: web at x=0..tw, flanges extend to +B; mirror flips about Y for doubles.
        d, b, tw, tf = ch.d, ch.b, ch.tw, ch.tf
        sign = -1.0 if mirror else 1.0
        x0 = origin.x()
        y0 = origin.y()

        def px(x: float) -> float:
            return x0 + sign * x

        path = QPainterPath()
        path.moveTo(px(0), y0)                  # start at top of web outer
        path.lineTo(px(b), y0)                  # along top flange to tip
        path.lineTo(px(b), y0 + tf)             # down flange thickness
        path.lineTo(px(tw), y0 + tf)            # step to web inner face
        path.lineTo(px(tw), y0 + d - tf)        # down web inner
        path.lineTo(px(b), y0 + d - tf)         # out along bottom flange inner
        path.lineTo(px(b), y0 + d)              # down to flange tip
        path.lineTo(px(0), y0 + d)              # back to web outer bottom
        path.lineTo(px(0), y0)                  # up web outer
        return path

    # ---- Painting ----------------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#0f0f0f"))

        if not self._geometry:
            painter.setPen(QPen(QColor("#ffffff"), 1, Qt.DashLine))
            painter.drawText(self.rect(), Qt.AlignCenter, "No section")
            return

        # Compute combined bounding box
        rects = [path.boundingRect() for path in self._geometry]
        geom_bbox = QRectF()
        for r in rects:
            geom_bbox = geom_bbox.united(r)
        combined = QRectF(geom_bbox)
        margin = 35.0
        combined.adjust(-margin, -margin, margin, margin)

        if combined.width() <= 0 or combined.height() <= 0:
            return

        # Fit to widget
        rw, rh = self.width(), self.height()
        scale = min(rw / combined.width(), rh / combined.height())
        painter.translate(rw / 2.0, rh / 2.0)
        painter.scale(scale, -scale)  # flip Y for engineering orientation
        painter.translate(-combined.center())

        pen = QPen(QColor("#f7d65a"), 1.5 / max(scale, 1e-3))
        painter.setPen(pen)
        brush = QColor(255, 215, 0, 40) if self._section_fill else Qt.NoBrush
        painter.setBrush(brush)
        for path in self._geometry:
            painter.drawPath(path)

        self._draw_dimensions(painter, geom_bbox, scale)

    # ---- Dimension annotations -------------------------------------------
    def _draw_dimensions(self, painter: QPainter, bbox: QRectF, scale: float) -> None:
        info = self._dimension_info
        if not info or bbox.isNull():
            return

        if info.get("kind") == "angle":
            self._draw_angle_dimensions(painter, bbox, scale, info)
        elif info.get("kind") == "channel":
            self._draw_channel_dimensions(painter, bbox, scale, info)

    def _fmt_val(self, val: float) -> str:
        """Format dimension value cleanly."""
        if val == int(val):
            return str(int(val))
        return f"{val:.1f}".rstrip("0").rstrip(".")

    def _draw_angle_dimensions(self, painter: QPainter, bbox: QRectF, scale: float, info: dict) -> None:
        x_left, x_right = bbox.left(), bbox.right()
        y_top, y_bottom = bbox.top(), bbox.bottom()
        t = info.get("t", 0.0)
        a_val = info.get("a", bbox.height())
        b_val = info.get("b", bbox.width())

        offset = 15.0

        # W dimension (horizontal at bottom)
        self._draw_dim_line_h(painter, scale, x_left, x_right, y_bottom + offset,
                              "W", self._fmt_val(b_val))

        # H dimension (vertical on left)
        self._draw_dim_line_v(painter, scale, y_top, y_bottom, x_left - offset,
                              "H", self._fmt_val(a_val))

        # t dimension (thickness at top)
        if t > 0:
            self._draw_dim_line_h(painter, scale, x_left, x_left + t, y_top - offset * 0.8,
                                  "t", self._fmt_val(t))

    def _draw_channel_dimensions(self, painter: QPainter, bbox: QRectF, scale: float, info: dict) -> None:
        x_left, x_right = bbox.left(), bbox.right()
        y_top, y_bottom = bbox.top(), bbox.bottom()
        tw = info.get("tw", 0.0)
        tf = info.get("tf", 0.0)
        d = info.get("d", bbox.height())
        b = info.get("b", bbox.width())

        offset = 15.0

        # B dimension (horizontal at bottom)
        self._draw_dim_line_h(painter, scale, x_left, x_right, y_bottom + offset,
                              "B", self._fmt_val(b))

        # D dimension (vertical on left)
        self._draw_dim_line_v(painter, scale, y_top, y_bottom, x_left - offset,
                              "D", self._fmt_val(d))

        # tw dimension (web thickness)
        if tw > 0:
            mid_y = (y_top + y_bottom) / 2.0
            self._draw_dim_line_h(painter, scale, x_left, x_left + tw, mid_y,
                                  "t", self._fmt_val(tw), subscript="w")

        # tf dimension (flange thickness on right)
        if tf > 0:
            self._draw_dim_line_v(painter, scale, y_top, y_top + tf, x_right + offset * 0.7,
                                  "t", self._fmt_val(tf), subscript="f")

    def _draw_dim_line_h(self, painter: QPainter, scale: float,
                         x1: float, x2: float, y: float,
                         symbol: str, value: str, subscript: str = None) -> None:
        """Draw horizontal dimension line with arrows and label."""
        dim_pen = QPen(QColor("#ffffff"), 0.8 / max(scale, 1e-3))
        painter.setPen(dim_pen)
        painter.setBrush(Qt.NoBrush)

        # Main dimension line
        painter.drawLine(QPointF(x1, y), QPointF(x2, y))

        # Extension lines
        ext = 5.0
        painter.drawLine(QPointF(x1, y - ext), QPointF(x1, y + ext))
        painter.drawLine(QPointF(x2, y - ext), QPointF(x2, y + ext))

        # Arrowheads
        arrow_size = 3.0
        # Left arrow
        painter.drawLine(QPointF(x1, y), QPointF(x1 + arrow_size, y + arrow_size * 0.5))
        painter.drawLine(QPointF(x1, y), QPointF(x1 + arrow_size, y - arrow_size * 0.5))
        # Right arrow
        painter.drawLine(QPointF(x2, y), QPointF(x2 - arrow_size, y + arrow_size * 0.5))
        painter.drawLine(QPointF(x2, y), QPointF(x2 - arrow_size, y - arrow_size * 0.5))

        # Label above the line
        mid_x = (x1 + x2) / 2.0
        label_y = y + 6.0
        self._draw_subscript_label(painter, scale, mid_x, label_y, symbol, value, subscript)

    def _draw_dim_line_v(self, painter: QPainter, scale: float,
                         y1: float, y2: float, x: float,
                         symbol: str, value: str, subscript: str = None) -> None:
        """Draw vertical dimension line with arrows and label."""
        dim_pen = QPen(QColor("#ffffff"), 0.8 / max(scale, 1e-3))
        painter.setPen(dim_pen)
        painter.setBrush(Qt.NoBrush)

        # Main dimension line
        painter.drawLine(QPointF(x, y1), QPointF(x, y2))

        # Extension lines
        ext = 5.0
        painter.drawLine(QPointF(x - ext, y1), QPointF(x + ext, y1))
        painter.drawLine(QPointF(x - ext, y2), QPointF(x + ext, y2))

        # Arrowheads
        arrow_size = 3.0
        # Top arrow
        painter.drawLine(QPointF(x, y1), QPointF(x + arrow_size * 0.5, y1 + arrow_size))
        painter.drawLine(QPointF(x, y1), QPointF(x - arrow_size * 0.5, y1 + arrow_size))
        # Bottom arrow
        painter.drawLine(QPointF(x, y2), QPointF(x + arrow_size * 0.5, y2 - arrow_size))
        painter.drawLine(QPointF(x, y2), QPointF(x - arrow_size * 0.5, y2 - arrow_size))

        # Label to the side
        mid_y = (y1 + y2) / 2.0
        label_x = x - 8.0
        self._draw_subscript_label(painter, scale, label_x, mid_y, symbol, value, subscript, align_right=True)

    def _draw_subscript_label(self, painter: QPainter, scale: float,
                              x: float, y: float, symbol: str, value: str,
                              subscript: str = None, superscript: str = None,
                              align_right: bool = False) -> None:
        """Draw label with proper subscript/superscript using QPainter only.
        
        - Subscript: smaller font, shifted down
        - Superscript: smaller font, shifted up
        - Uses QFontMetrics.horizontalAdvance() for correct positioning
        """
        device_pt = painter.transform().map(QPointF(x, y))
        painter.save()
        painter.resetTransform()

        # Font setup
        main_font = QFont("Arial", 9)
        script_font = QFont("Arial", 6)  # Smaller for sub/superscript

        px, py = device_pt.x(), device_pt.y()

        # Build text segments: [(text, font, y_offset), ...]
        segments = []
        
        # Main symbol
        segments.append((symbol, main_font, 0))
        
        # Subscript (shifted down by ~3px)
        if subscript:
            segments.append((subscript, script_font, 3))
        
        # Superscript (shifted up by ~-5px) - for future use
        if superscript:
            segments.append((superscript, script_font, -5))
        
        # Value part
        segments.append((f" = {value} mm", main_font, 0))

        # Calculate total width for right alignment
        total_width = 0
        for text, font, _ in segments:
            painter.setFont(font)
            fm = painter.fontMetrics()
            total_width += fm.horizontalAdvance(text)

        # Starting x position
        if align_right:
            start_x = px - total_width
        else:
            start_x = px

        # Draw function for a single pass
        def draw_segments(color: QColor, offset_x: float = 0, offset_y: float = 0):
            painter.setPen(QPen(color))
            cursor_x = start_x + offset_x
            for text, font, y_shift in segments:
                painter.setFont(font)
                fm = painter.fontMetrics()
                painter.drawText(QPointF(cursor_x, py + y_shift + offset_y), text)
                cursor_x += fm.horizontalAdvance(text)

        # Outline pass (black, 4 directions)
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            draw_segments(QColor("#000000"), dx, dy)

        # Foreground pass (white)
        draw_segments(QColor("#ffffff"))

        painter.restore()

    # Convenience for external DB access
    @property
    def catalog(self) -> SectionCatalog:
        return self._catalog
