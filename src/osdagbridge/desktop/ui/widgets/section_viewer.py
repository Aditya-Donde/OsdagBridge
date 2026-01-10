from __future__ import annotations

import math
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget


DB_PATH = Path(__file__).resolve().parents[3] / "core" / "data" / "ResourceFiles" / "Intg_osdag.sqlite"


@dataclass
class AngleSection:
    designation: str
    a: float  # leg 1 (mm)
    b: float  # leg 2 (mm)
    t: float  # thickness (mm)
    r1: float  # root radius (mm)
    r2: float  # toe radius (mm)


@dataclass
class ChannelSection:
    designation: str
    d: float  # depth (mm)
    b: float  # flange width (mm)
    tw: float  # web thickness (mm)
    tf: float  # flange thickness (mm)
    r1: float  # root radius (mm)
    r2: float  # toe radius (mm)


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
            cur.execute(f"SELECT Designation, a, b, t, R1, R2 FROM {table}")
            for des, a, b, t, r1, r2 in cur.fetchall():
                self._angles[des.strip()] = AngleSection(
                    designation=des.strip(),
                    a=float(a),
                    b=float(b),
                    t=float(t),
                    r1=float(r1),
                    r2=float(r2),
                )

        # Channels
        cur.execute("SELECT Designation, D, B, tw, T, R1, R2 FROM Channels")
        for des, d, b, tw, tf, r1, r2 in cur.fetchall():
            self._channels[des.strip()] = ChannelSection(
                designation=des.strip(),
                d=float(d),
                b=float(b),
                tw=float(tw),
                tf=float(tf),
                r1=float(r1),
                r2=float(r2),
            )

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
        self.setMinimumHeight(150)
        self.setMinimumWidth(140)
        self._section_type: str = ""
        self._designation: str = ""
        self._geometry: List[QPainterPath] = []
        self._catalog = SectionCatalog()
        self._dimension_info: Optional[dict] = None
        self._section_fill = True

    def set_section(self, section_type: str, designation: str, show_double_total: bool = True) -> None:
        """
        section_type: one of [angle, double_angle_long, double_angle_short, channel, double_channel]
        designation: designation string present in the DB (for doubles, pass base designation without the leading 2-)
        show_double_total: for double-angle/channel, whether to show total envelope width/height (default True).
        """
        self._section_type = section_type
        self._designation = designation
        self._geometry = self._build_geometry(section_type, designation)
        self._dimension_info = self._dimension_for(section_type, designation, show_double_total)
        self._section_fill = section_type in (
            "angle",
            "double_angle_long",
            "double_angle_short",
            "channel",
            "double_channel",
        )
        self.update()

    def _dimension_for(self, section_type: str, designation: str, show_double_total: bool = True) -> Optional[dict]:
        if not designation:
            return None
        if section_type in ("angle", "double_angle_long", "double_angle_short"):
            angle = self._catalog.get_angle(designation)
            if not angle:
                return None
            # For single angles: take 'a' as horizontal (W) and 'b' as vertical (H)
            dims = {"kind": "angle", "w": angle.a, "h": angle.b, "t": angle.t}
            # For double angles, optionally report total envelope or single-leg width
            if section_type == "double_angle_long":
                if show_double_total:
                    dims.update({"w": angle.b * 2.0, "h": angle.a})  # long leg (a) vertical
                else:
                    dims.update({"w": angle.b, "h": angle.a, "single_span": True})
            elif section_type == "double_angle_short":
                if show_double_total:
                    dims.update({"w": angle.a * 2.0, "h": angle.b})  # short leg (b) vertical
                else:
                    dims.update({"w": angle.a, "h": angle.b, "single_span": True})
            return dims
        if section_type in ("channel", "double_channel"):
            ch = self._catalog.get_channel(designation)
            if not ch:
                return None
            dims = {"kind": "channel", "b": ch.b, "d": ch.d, "tw": ch.tw, "tf": ch.tf, "r1": ch.r1, "r2": ch.r2}
            if section_type == "double_channel":
                dims["is_double"] = True
            return dims
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
                # Long legs connected back-to-back vertically, short legs extend horizontally
                path1 = self._build_double_angle_long_path(angle, mirrored=False)
                path2 = self._build_double_angle_long_path(angle, mirrored=True)
                return [path1, path2]
            else:
                # Short legs connected back-to-back vertically, long legs extend horizontally  
                path1 = self._build_double_angle_short_path(angle, mirrored=False)
                path2 = self._build_double_angle_short_path(angle, mirrored=True)
                return [path1, path2]

        if section_type in ("channel", "double_channel"):
            ch = self._catalog.get_channel(designation)
            if not ch:
                return []
            if section_type == "channel":
                return [self._build_channel_path(ch, QPointF(0, 0))]
            else:
                # Back-to-back: two Cs touching at web outer faces
                p1 = self._build_channel_path(ch, QPointF(0, 0))
                p2 = self._build_channel_path(ch, QPointF(0, 0), mirror=True)
                return [p1, p2]

        return []

    def _build_angle_path(self, angle: AngleSection, origin: QPointF, mirror_axis: str = None) -> QPainterPath:
        # Outer L profile anchored at origin (0,0) at corner; legs along +x/+y.
        # mirror_axis: "y" mirrors about Y (long-leg back-to-back), "x" mirrors about X (short-leg back-to-back).
        a, b, t = angle.a, angle.b, angle.t
        sign_x = -1.0 if mirror_axis == "y" else 1.0
        sign_y = -1.0 if mirror_axis == "x" else 1.0
        x0, y0 = origin.x(), origin.y()

        path = QPainterPath()
        # Outline for solid L (union of two rectangles) without inner cutout lines.
        pts_outer = [
            QPointF(x0, y0),
            QPointF(x0 + sign_x * a, y0),
            QPointF(x0 + sign_x * a, y0 + sign_y * t),
            QPointF(x0 + sign_x * t, y0 + sign_y * t),
            QPointF(x0 + sign_x * t, y0 + sign_y * b),
            QPointF(x0, y0 + sign_y * b),
        ]
        path.moveTo(pts_outer[0])
        for pt in pts_outer[1:]:
            path.lineTo(pt)
        path.closeSubpath()
        return path

    def _build_double_angle_long_path(self, angle: AngleSection, mirrored: bool = False) -> QPainterPath:
        """Double angle with long legs connected (Figure 2).
        Long leg (a) is vertical, short leg (b) extends horizontally.
        The two angles are back-to-back along the long leg.
        Uses r1 radius at the inner corner.
        """
        a, b, t, r1 = angle.a, angle.b, angle.t, max(angle.r1, 0.0)
        sign = -1.0 if mirrored else 1.0
        
        # Clamp radius to fit
        r = min(r1, min(a - t, b - t) / 2)
        r = max(r, 2.0)  # minimum visible curve
        
        path = QPainterPath()
        # L-shape: vertical long leg, horizontal short leg
        path.moveTo(QPointF(0, 0))                        # top of long leg at connection
        path.lineTo(QPointF(sign * t, 0))                 # across thickness at top
        path.lineTo(QPointF(sign * t, a - t - r))         # down inner face, stop before curve
        # Inner corner fillet
        path.quadTo(QPointF(sign * t, a - t), QPointF(sign * (t + r), a - t))
        path.lineTo(QPointF(sign * b, a - t))             # out along short leg inner
        path.lineTo(QPointF(sign * b, a))                 # down short leg thickness
        path.lineTo(QPointF(0, a))                        # back to long leg outer
        path.closeSubpath()
        return path

    def _build_double_angle_short_path(self, angle: AngleSection, mirrored: bool = False) -> QPainterPath:
        """Double angle with short legs connected (Figure 3).
        Short leg (b) is vertical, long leg (a) extends horizontally.
        The two angles are back-to-back along the short leg.
        Uses r1 radius at the inner corner.
        """
        a, b, t, r1 = angle.a, angle.b, angle.t, max(angle.r1, 0.0)
        sign = -1.0 if mirrored else 1.0
        
        # Clamp radius to fit
        r = min(r1, min(a - t, b - t) / 2)
        r = max(r, 2.0)  # minimum visible curve
        
        path = QPainterPath()
        # L-shape: vertical short leg, horizontal long leg
        path.moveTo(QPointF(0, 0))                        # top of short leg at connection
        path.lineTo(QPointF(sign * t, 0))                 # across thickness at top
        path.lineTo(QPointF(sign * t, b - t - r))         # down inner face, stop before curve
        # Inner corner fillet
        path.quadTo(QPointF(sign * t, b - t), QPointF(sign * (t + r), b - t))
        path.lineTo(QPointF(sign * a, b - t))             # out along long leg inner
        path.lineTo(QPointF(sign * a, b))                 # down long leg thickness
        path.lineTo(QPointF(0, b))                        # back to short leg outer
        path.closeSubpath()
        return path

    def _build_channel_path(self, ch: ChannelSection, origin: QPointF, mirror: bool = False) -> QPainterPath:
        # d = depth (vertical), b = flange width (horizontal from web outer to flange tip)
        # tw = web thickness (horizontal), tf = flange thickness (vertical)
        d, b, tw, tf, r1 = ch.d, ch.b, ch.tw, ch.tf, max(ch.r1, 0.0)
        sign = -1.0 if mirror else 1.0
        x0 = origin.x()
        y0 = origin.y()

        # Use a visible fillet radius (clamped to fit)
        r = min(r1, (d - 2 * tf) / 4, b - tw - 1)
        r = max(r, 2.0)  # minimum visible curve

        def px(x: float) -> float:
            return x0 + sign * x

        path = QPainterPath()
        # Outer profile: start at web outer top corner
        path.moveTo(px(0), y0)
        path.lineTo(px(b), y0)                  # top flange outer (horizontal)
        path.lineTo(px(b), y0 + tf)             # down flange thickness at tip
        path.lineTo(px(tw + r), y0 + tf)        # inward along flange inner, stop before curve

        # Top inner fillet (quarter circle)
        path.quadTo(QPointF(px(tw), y0 + tf), QPointF(px(tw), y0 + tf + r))

        # Web inner face down (vertical)
        path.lineTo(px(tw), y0 + d - tf - r)

        # Bottom inner fillet (quarter circle)
        path.quadTo(QPointF(px(tw), y0 + d - tf), QPointF(px(tw + r), y0 + d - tf))

        path.lineTo(px(b), y0 + d - tf)         # outward along bottom flange inner
        path.lineTo(px(b), y0 + d)              # down to bottom flange outer tip
        path.lineTo(px(0), y0 + d)              # back to web outer bottom
        path.closeSubpath()
        return path

    # ---- Painting ----------------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # Force a light background for clarity in embedded previews
        painter.fillRect(self.rect(), QColor("#ffffff"))

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
        margin = 45.0
        combined.adjust(-margin, -margin, margin, margin)

        if combined.width() <= 0 or combined.height() <= 0:
            return

        # Fit to widget
        rw, rh = self.width(), self.height()
        scale = min(rw / combined.width(), rh / combined.height())
        painter.translate(rw / 2.0, rh / 2.0)
        painter.scale(scale, -scale)  # flip Y for engineering orientation
        painter.translate(-combined.center())

        pen = QPen(QColor("#90AF13"), 1.8 / max(scale, 1e-3))
        fill_brush = QColor("#BBE31A")

        for path in self._geometry:
            painter.setPen(pen)
            if self._section_fill:
                painter.setBrush(fill_brush)
            else:
                painter.setBrush(Qt.NoBrush)
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
        is_double = info.get("single_span", False)
        # For single-side display on double angles, limit the width dimension to the left section only.
        if is_double:
            x_right = (x_left + x_right) / 2.0
        y_top, y_bottom = bbox.top(), bbox.bottom()
        t = info.get("t", 0.0)
        # Use explicit total envelope dimensions when provided (double angles), otherwise fall back to single-leg values.
        a_val = info.get("h", info.get("a", bbox.height()))
        b_val = info.get("w", info.get("b", bbox.width()))

        offset = 15.0

        # W dimension (horizontal at bottom for double angles, at top for single)
        if is_double:
            self._draw_dim_line_h(painter, scale, x_left, x_right, y_bottom + offset,
                                  "W", self._fmt_val(b_val), label_pos="above")
        else:
            self._draw_dim_line_h(painter, scale, x_left, x_right, y_top - offset,
                                  "W", self._fmt_val(b_val), label_pos="below")

        # H dimension (vertical on left)
        self._draw_dim_line_v(painter, scale, y_top, y_bottom, x_left - offset,
                              "H", self._fmt_val(a_val))

        # t dimension (thickness) — place at the center vertical stem for double angles, at the vertical leg for single angle.
        if t > 0:
            if is_double:
                # For double angles, place t at the top above the center stem where the two angles meet.
                self._draw_dim_line_h(painter, scale, 0, t, y_top - offset,
                                      "t", self._fmt_val(t), outer_arrows=True, label_pos="below")
            else:
                # Single angle: t at bottom near the vertical leg
                self._draw_dim_line_h(painter, scale, x_left, x_left + t, y_bottom + offset,
                                      "t", self._fmt_val(t), outer_arrows=True)

    def _draw_channel_dimensions(self, painter: QPainter, bbox: QRectF, scale: float, info: dict) -> None:
        x_left, x_right = bbox.left(), bbox.right()
        y_top, y_bottom = bbox.top(), bbox.bottom()
        tw = info.get("tw", 0.0)  # web thickness (horizontal)
        tf = info.get("tf", 0.0)  # flange thickness (vertical)
        d = info.get("d", bbox.height())
        b = info.get("b", bbox.width())
        is_double = info.get("is_double", False)

        offset = 15.0

        # B dimension (horizontal at bottom - flange width)
        if is_double:
            # For double channels, show B over a single channel width (use left channel span)
            single_right = x_left + b
            self._draw_dim_line_h(painter, scale, x_left, single_right, y_bottom + offset,
                                  "B", self._fmt_val(b))
        else:
            self._draw_dim_line_h(painter, scale, x_left, x_right, y_bottom + offset,
                                  "B", self._fmt_val(b))

        # D dimension (vertical on left - depth)
        self._draw_dim_line_v(painter, scale, y_top, y_bottom, x_left - offset,
                              "D", self._fmt_val(d))

        # tw dimension (web thickness)
        if tw > 0:
            if is_double:
                # For double channel, show tw at the center where the two webs meet, but keep it visible
                self._draw_dim_line_h(painter, scale, -tw, 0, y_top - offset,
                                      "t", self._fmt_val(tw), subscript="w", outer_arrows=True, label_pos="below")
                helper_pen = QPen(QColor("#000000"), 1.2 / max(scale, 1e-3))
                painter.setPen(helper_pen)
                start_y = y_top 
                painter.drawLine(QPointF(-tw, start_y), QPointF(0, start_y))
                # Dashed leader lines from the web edges up to the dimension line to show what tw measures
                dash_pen = QPen(QColor("#000000"), 0.9 / max(scale, 1e-3), Qt.DashLine)
                painter.setPen(dash_pen)
                # Draw from bottom of flange (y_top + tf) to dimension line (y_top - offset) 
                painter.drawLine(QPointF(-tw, start_y + tf), QPointF(-tw, y_top - offset))
                painter.drawLine(QPointF(0, start_y + tf), QPointF(0, y_top - offset))
            else:
                # For single channel, place tw at left aligned with the web
                self._draw_dim_line_h(painter, scale, x_left, x_left + tw, y_top - offset,
                                      "t", self._fmt_val(tw), subscript="w", outer_arrows=True, label_pos="below")

        # tf dimension (flange thickness - vertical on the right side, label on right)
        if tf > 0:
            self._draw_dim_line_v(painter, scale, y_top, y_top + tf, x_right + 12.0,
                                  "t", self._fmt_val(tf), subscript="f", outer_arrows=True, label_right=True)

    def _draw_dim_line_h(self, painter: QPainter, scale: float,
                         x1: float, x2: float, y: float,
                         symbol: str, value: str, subscript: str = None,
                         outer_arrows: bool = False, label_pos: str = "above") -> None:
        """Draw horizontal dimension line with arrows and label."""
        dim_pen = QPen(QColor("#000000"), 0.8 / max(scale, 1e-3))
        painter.setPen(dim_pen)
        painter.setBrush(Qt.NoBrush)

        # Main dimension line
        painter.drawLine(QPointF(x1, y), QPointF(x2, y))

        # Extension lines
        ext = 5.0
        painter.drawLine(QPointF(x1, y - ext), QPointF(x1, y + ext))
        painter.drawLine(QPointF(x2, y - ext), QPointF(x2, y + ext))

        # Arrowheads - standard engineering 3:1 ratio (length:half-width)
        arrow_length = 9.0
        arrow_half_width = 3.0  # 3:1 ratio
        painter.setBrush(QColor("#000000"))  # Fill the arrowheads
        if outer_arrows:
            # Arrows pointing inward from outside (for small dimensions)
            ext_len = 12.0
            painter.drawLine(QPointF(x1 - ext_len, y), QPointF(x1, y))
            painter.drawLine(QPointF(x2 + ext_len, y), QPointF(x2, y))
            # Left arrow pointing right (filled triangle)
            left_arrow = QPainterPath()
            left_arrow.moveTo(x1, y)
            left_arrow.lineTo(x1 - arrow_length, y - arrow_half_width)
            left_arrow.lineTo(x1 - arrow_length, y + arrow_half_width)
            left_arrow.closeSubpath()
            painter.drawPath(left_arrow)
            # Right arrow pointing left (filled triangle)
            right_arrow = QPainterPath()
            right_arrow.moveTo(x2, y)
            right_arrow.lineTo(x2 + arrow_length, y - arrow_half_width)
            right_arrow.lineTo(x2 + arrow_length, y + arrow_half_width)
            right_arrow.closeSubpath()
            painter.drawPath(right_arrow)
        else:
            # Internal arrows (for large dimensions)
            # Left arrow pointing right (filled triangle)
            left_arrow = QPainterPath()
            left_arrow.moveTo(x1, y)
            left_arrow.lineTo(x1 + arrow_length, y - arrow_half_width)
            left_arrow.lineTo(x1 + arrow_length, y + arrow_half_width)
            left_arrow.closeSubpath()
            painter.drawPath(left_arrow)
            # Right arrow pointing left (filled triangle)
            right_arrow = QPainterPath()
            right_arrow.moveTo(x2, y)
            right_arrow.lineTo(x2 - arrow_length, y - arrow_half_width)
            right_arrow.lineTo(x2 - arrow_length, y + arrow_half_width)
            right_arrow.closeSubpath()
            painter.drawPath(right_arrow)
        painter.setBrush(Qt.NoBrush)  # Reset brush

        # Label
        mid_x = (x1 + x2) / 2.0
        self._draw_subscript_label(painter, scale, mid_x, y, symbol, value, subscript, align_center=True, valign=label_pos)

    def _draw_dim_line_v(self, painter: QPainter, scale: float,
                         y1: float, y2: float, x: float,
                         symbol: str, value: str, subscript: str = None,
                         outer_arrows: bool = False, label_right: bool = False) -> None:
        """Draw vertical dimension line with arrows and label."""
        dim_pen = QPen(QColor("#000000"), 0.8 / max(scale, 1e-3))
        painter.setPen(dim_pen)
        painter.setBrush(Qt.NoBrush)

        # Main dimension line
        painter.drawLine(QPointF(x, y1), QPointF(x, y2))

        # Extension lines
        ext = 5.0
        painter.drawLine(QPointF(x - ext, y1), QPointF(x + ext, y1))
        painter.drawLine(QPointF(x - ext, y2), QPointF(x + ext, y2))

        # Arrowheads - standard engineering 3:1 ratio (length:half-width)
        arrow_length = 9.0
        arrow_half_width = 3.0  # 3:1 ratio
        painter.setBrush(QColor("#000000"))  # Fill the arrowheads
        if outer_arrows:
            # Arrows pointing inward from outside (for small dimensions)
            ext_len = 12.0
            painter.drawLine(QPointF(x, y1 - ext_len), QPointF(x, y1))
            painter.drawLine(QPointF(x, y2 + ext_len), QPointF(x, y2))
            # Top arrow pointing down (filled triangle)
            top_arrow = QPainterPath()
            top_arrow.moveTo(x, y1)
            top_arrow.lineTo(x - arrow_half_width, y1 - arrow_length)
            top_arrow.lineTo(x + arrow_half_width, y1 - arrow_length)
            top_arrow.closeSubpath()
            painter.drawPath(top_arrow)
            # Bottom arrow pointing up (filled triangle)
            bottom_arrow = QPainterPath()
            bottom_arrow.moveTo(x, y2)
            bottom_arrow.lineTo(x - arrow_half_width, y2 + arrow_length)
            bottom_arrow.lineTo(x + arrow_half_width, y2 + arrow_length)
            bottom_arrow.closeSubpath()
            painter.drawPath(bottom_arrow)
        else:
            # Internal arrows (for large dimensions)
            # Top arrow pointing down (filled triangle)
            top_arrow = QPainterPath()
            top_arrow.moveTo(x, y1)
            top_arrow.lineTo(x - arrow_half_width, y1 + arrow_length)
            top_arrow.lineTo(x + arrow_half_width, y1 + arrow_length)
            top_arrow.closeSubpath()
            painter.drawPath(top_arrow)
            # Bottom arrow pointing up (filled triangle)
            bottom_arrow = QPainterPath()
            bottom_arrow.moveTo(x, y2)
            bottom_arrow.lineTo(x - arrow_half_width, y2 - arrow_length)
            bottom_arrow.lineTo(x + arrow_half_width, y2 - arrow_length)
            bottom_arrow.closeSubpath()
            painter.drawPath(bottom_arrow)
        painter.setBrush(Qt.NoBrush)  # Reset brush

        # Label to the side
        mid_y = (y1 + y2) / 2.0
        if label_right:
            label_x = x + 8.0
            self._draw_subscript_label(painter, scale, label_x, mid_y, symbol, value, subscript, align_right=False)
        else:
            label_x = x - 8.0
            self._draw_subscript_label(painter, scale, label_x, mid_y, symbol, value, subscript, align_right=True)

    def _draw_subscript_label(self, painter: QPainter, scale: float,
                              x: float, y: float, symbol: str, value: str,
                              subscript: str = None, superscript: str = None,
                              align_right: bool = False, align_center: bool = False, valign: str = None) -> None:
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

        if valign in ("center", "middle"):
            py += 4
        elif valign == "above":
            # Lift labels slightly further off the dimension line to avoid overlap
            py -= 8
        elif valign == "below":
            py += 18

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
        elif align_center:
            start_x = px - total_width / 2.0
        else:
            start_x = px

        # Draw background if needed to clear lines
        if valign in ("center", "middle"):
            fm_main = QFontMetrics(main_font)
            text_height = fm_main.height()
            # Background rect: slightly padded
            bg_rect = QRectF(start_x - 2, py - text_height + 4, total_width + 4, text_height)
            painter.fillRect(bg_rect, QColor("#0f0f0f"))

        # Draw function for a single pass
        def draw_segments(color: QColor, offset_x: float = 0, offset_y: float = 0):
            painter.setPen(QPen(color))
            cursor_x = start_x + offset_x
            for text, font, y_shift in segments:
                painter.setFont(font)
                fm = painter.fontMetrics()
                painter.drawText(QPointF(cursor_x, py + y_shift + offset_y), text)
                cursor_x += fm.horizontalAdvance(text)

        draw_segments(QColor("#000000"))

        painter.restore()

    # Convenience for external DB access
    @property
    def catalog(self) -> SectionCatalog:
        return self._catalog
