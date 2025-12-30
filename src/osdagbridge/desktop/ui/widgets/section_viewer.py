from __future__ import annotations

import math
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
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
        # Only angles are filled; channels stay outline for clearer C shape
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
        # Add generous margin so dimension arrows/text are not clipped.
        margin = 18.0
        combined.adjust(-margin, -margin, margin, margin)

        if combined.width() <= 0 or combined.height() <= 0:
            return

        # Fit to widget
        rw, rh = self.width(), self.height()
        scale = min(rw / combined.width(), rh / combined.height())
        painter.translate(rw / 2.0, rh / 2.0)
        painter.scale(scale, -scale)  # flip Y for engineering orientation
        painter.translate(-combined.center())

        pen = QPen(QColor("#f7d65a"), 1.2 / max(scale, 1e-3))
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
        dim_pen = QPen(QColor("#ffffff"), 1.0 / max(scale, 1e-3))
        painter.setPen(dim_pen)
        painter.setBrush(Qt.NoBrush)

        if info.get("kind") == "angle":
            self._draw_angle_dimensions(painter, bbox, scale, info)
        elif info.get("kind") == "channel":
            self._draw_channel_dimensions(painter, bbox, scale, info)

    def _draw_angle_dimensions(self, painter: QPainter, bbox: QRectF, scale: float, info: dict) -> None:
        x_left, x_right = bbox.left(), bbox.right()
        y_top, y_bottom = bbox.top(), bbox.bottom()
        t = info.get("t", 0.0)
        offset = 16.0 / max(scale, 1e-3)
        text_gap = 6.0 / max(scale, 1e-3)

        # B (leg length along x)
        self._draw_arrow(
            painter,
            QPointF(x_left, y_bottom + offset),
            QPointF(x_right, y_bottom + offset),
            "B",
            QPointF(0, -text_gap * 0.6),
            scale,
        )

        # H (leg length along y)
        self._draw_arrow(
            painter,
            QPointF(x_left - offset, y_top),
            QPointF(x_left - offset, y_bottom),
            "H",
            QPointF(text_gap, 0),
            scale,
        )

        if t > 0:
            # tw across web thickness near the corner top
            self._draw_arrow(
                painter,
                QPointF(x_left, y_top - offset * 0.7),
                QPointF(x_left + t, y_top - offset * 0.7),
                "tw",
                QPointF(0, -text_gap * 0.4),
                scale,
            )

            # tf across flange thickness near the tip of the flange
            self._draw_arrow(
                painter,
                QPointF(x_right + offset * 0.6, y_top),
                QPointF(x_right + offset * 0.6, y_top + t),
                "tf",
                QPointF(text_gap, 0),
                scale,
            )

    def _draw_channel_dimensions(self, painter: QPainter, bbox: QRectF, scale: float, info: dict) -> None:
        x_left, x_right = bbox.left(), bbox.right()
        y_top, y_bottom = bbox.top(), bbox.bottom()
        tw = info.get("tw", 0.0)
        tf = info.get("tf", 0.0)
        d = info.get("d", bbox.height())
        offset = 14.0 / max(scale, 1e-3)
        text_gap = 5.0 / max(scale, 1e-3)

        # B (flange width)
        self._draw_arrow(
            painter,
            QPointF(x_left, y_bottom + offset),
            QPointF(x_right, y_bottom + offset),
            "B",
            QPointF(0, -text_gap),
            scale,
        )

        # H (depth)
        self._draw_arrow(
            painter,
            QPointF(x_left - offset, y_top),
            QPointF(x_left - offset, y_bottom),
            "H",
            QPointF(text_gap, 0),
            scale,
        )

        if tw > 0:
            mid_x = x_left + tw / 2.0
            self._draw_arrow(
                painter,
                QPointF(mid_x - tw / 2.0, y_top + d * 0.4 - offset * 0.4),
                QPointF(mid_x + tw / 2.0, y_top + d * 0.4 - offset * 0.4),
                "tw",
                QPointF(0, -text_gap * 0.1),
                scale,
            )

        if tf > 0:
            self._draw_arrow(
                painter,
                QPointF(x_right + offset * 0.8, y_top),
                QPointF(x_right + offset * 0.8, y_top + tf),
                "tf",
                QPointF(text_gap, 0),
                scale,
            )

    def _draw_arrow(self, painter: QPainter, p1: QPointF, p2: QPointF, label: str, text_offset: QPointF, scale: float) -> None:
        painter.drawLine(p1, p2)

        def _head(base: QPointF, direction: QPointF):
            length = math.hypot(direction.x(), direction.y()) or 1e-6
            ux, uy = direction.x() / length, direction.y() / length
            size = 5.0 / max(scale, 1e-3)
            perp = QPointF(-uy, ux)
            tip1 = QPointF(base.x() - ux * size + perp.x() * size * 0.5, base.y() - uy * size + perp.y() * size * 0.5)
            tip2 = QPointF(base.x() - ux * size - perp.x() * size * 0.5, base.y() - uy * size - perp.y() * size * 0.5)
            painter.drawLine(base, tip1)
            painter.drawLine(base, tip2)

        vec = QPointF(p2.x() - p1.x(), p2.y() - p1.y())
        _head(p1, vec)
        _head(p2, QPointF(-vec.x(), -vec.y()))

        mid = QPointF((p1.x() + p2.x()) / 2.0 + text_offset.x(), (p1.y() + p2.y()) / 2.0 + text_offset.y())
        self._draw_text(painter, mid, label)

    def _draw_text(self, painter: QPainter, point: QPointF, text: str) -> None:
        device_pt = painter.transform().map(point)
        painter.save()
        painter.resetTransform()
        # Draw outline then foreground for better contrast on dark background
        painter.setPen(QPen(QColor("#000000"), 3))
        painter.drawText(device_pt, text)
        painter.setPen(QPen(QColor("#ffffff"), 1))
        painter.drawText(device_pt, text)
        painter.restore()

    # Convenience for external DB access
    @property
    def catalog(self) -> SectionCatalog:
        return self._catalog
