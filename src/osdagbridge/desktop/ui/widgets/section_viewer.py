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

    def set_section(self, section_type: str, designation: str) -> None:
        """
        section_type: one of [angle, double_angle_long, double_angle_short, channel, double_channel]
        designation: designation string present in the DB (for doubles, pass base designation without the leading 2-)
        """
        self._section_type = section_type
        self._designation = designation
        self._geometry = self._build_geometry(section_type, designation)
        self.update()

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
        d, b, tw, tf = ch.d, ch.b, ch.tw, ch.tf
        offset_x = -b if mirror else 0.0
        path = QPainterPath()
        # outer rectangle with flanges top/bottom thickness tf and web thickness tw centered
        x0 = origin.x() + offset_x
        y0 = origin.y()
        # Draw as polygon (clockwise)
        pts = [
            QPointF(x0, y0),
            QPointF(x0 + b, y0),
            QPointF(x0 + b, y0 + tf),
            QPointF(x0 + (b + tw) / 2.0, y0 + tf),
            QPointF(x0 + (b + tw) / 2.0, y0 + d - tf),
            QPointF(x0 + b, y0 + d - tf),
            QPointF(x0 + b, y0 + d),
            QPointF(x0, y0 + d),
            QPointF(x0, y0 + d - tf),
            QPointF(x0 + (b - tw) / 2.0, y0 + d - tf),
            QPointF(x0 + (b - tw) / 2.0, y0 + tf),
            QPointF(x0, y0 + tf),
        ]
        path.moveTo(pts[0])
        for pt in pts[1:]:
            path.lineTo(pt)
        path.closeSubpath()
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
        combined = QRectF()
        for r in rects:
            combined = combined.united(r)
        margin = 6.0
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
        painter.setBrush(QColor(255, 215, 0, 40))
        for path in self._geometry:
            painter.drawPath(path)

    # Convenience for external DB access
    @property
    def catalog(self) -> SectionCatalog:
        return self._catalog
