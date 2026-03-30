"""
Support Detail CAD Widget for OsdagBridge
Draws the end bearing detail of a plate girder.
Layout is pixel-proportional to the widget size.
Only the bearing plate arrow width is driven by bearing_length.

Author: OsdagBridge
"""

import math
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPointF, QRectF, QSize
from PySide6.QtGui import (
    QPainter, QPen, QColor, QFont, QBrush, QPolygonF, QPixmap
)


class SupportDetailCADWidget(QWidget):
    """
    Dynamic 2D CAD of the plate girder end bearing detail.
    Only `bearing_length` is dynamic; everything else is fixed.
    """

    DEFAULT_PARAMS = {
        "bearing_length": 400,
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.params = dict(self.DEFAULT_PARAMS)
        self.setMinimumSize(200, 250)
        self.concrete_brush = self.create_concrete_brush()

    def sizeHint(self):
        """Return preferred size for the widget."""
        return QSize(280, 300)

    def update_params(self, params: dict):
        self.params.update(params)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.fillRect(self.rect(), QColor(255, 255, 255))
            self._draw(painter)
        finally:
            painter.end()    

    def _draw(self, painter: QPainter):
        scale_factor = 0.75
        W = self.width()
        H = self.height()

        # Scale down the drawing with vertical centering
        horizontal_padding = W * (1 - scale_factor) / 2
        vertical_padding = H * (1 - scale_factor) / 2
        
        painter.translate(horizontal_padding, vertical_padding)
        painter.scale(scale_factor, scale_factor)

        bearing_len = max(50, min(600, float(self.params["bearing_length"])))

        
        cx = W * 0.32
        
        #concrete block
        conc_w = W * 0.3
        conc_left  = cx - conc_w / 2
        conc_right = cx + conc_w / 2

        #bearing plate
        max_bp_px = conc_w * 0.90
        bp_px     = max_bp_px * (bearing_len / 600.0)
        bp_left  = cx - bp_px / 2
        bp_right = cx + bp_px / 2

        #flange lines — start from bearing plate left
        fl_left = bp_left                 
        fl_right = cx + W * 0.30    



        # Stiffener lines — narrow pair around centre
        stiff_offset = W * 0.03
        stiff_half_px = W * 0.014
        # stiff_left  = cx - stiff_half_px - stiff_offset
        stiff_right = cx + stiff_half_px - stiff_offset

        # Zigzag x — fixed gap beyond flange right edge
        zigzag_x = fl_right

        # Vertical positions as fractions of H
        tf_top_y      = H * 0.05
        tf_bot_y      = tf_top_y  + H * 0.025
        bf_top_y      = tf_bot_y  + H * 0.5
        bf_bot_y      = bf_top_y  + H * 0.025
        bearing_top_y = bf_bot_y
        bearing_bot_y = bearing_top_y + H * 0.068
        conc_top_y    = bearing_bot_y
        conc_bot_y    = conc_top_y + H * 0.20

        zz_top = tf_top_y + H * 0.05
        zz_bot = bf_bot_y - H * 0.05

        # Dimension arrow y — midpoint of the gap

        dim_y = conc_bot_y + H * 0.10

        pen_main = QPen(QColor(0, 0, 0), 1)

        #Start Vertical line
        painter.setPen(QPen(QColor(0, 0, 0), 1.2))

        painter.drawLine(
            QPointF(bp_left, tf_top_y),     
            QPointF(bp_left, bearing_bot_y)
        )

        #TOP FLANGE
        painter.setPen(pen_main)
        painter.setBrush(Qt.NoBrush)
        painter.drawLine(QPointF(fl_left, tf_top_y), QPointF(fl_right, tf_top_y))
        painter.drawLine(QPointF(fl_left, tf_bot_y), QPointF(fl_right, tf_bot_y))


        #END BEARING STIFFENER
        stiff_width = W * 0.02
        stiff_x = cx

        painter.drawRect(QRectF(
            stiff_x - stiff_width/2,
            tf_bot_y,
            stiff_width,
            bf_top_y - tf_bot_y
        ))

        #BOTTOM FLANGE
        painter.setPen(pen_main)
        painter.drawLine(QPointF(fl_left, bf_top_y), QPointF(fl_right, bf_top_y))
        painter.drawLine(QPointF(fl_left, bf_bot_y), QPointF(fl_right, bf_bot_y))

        # BEARING PLATE 
        bp_h = bearing_bot_y - bearing_top_y
        bp_rect = QRectF(bp_left, bearing_top_y, bp_right - bp_left, bp_h)

        painter.save()
        painter.setClipRect(bp_rect)

        # Hatch (bold grey)
        painter.setPen(QPen(QColor(170, 170, 170), 2.2))

        hatch_spacing = 7
        x_start = bp_left - bp_h

        while x_start < bp_right:
            painter.drawLine(
                QPointF(x_start, bearing_bot_y),
                QPointF(x_start + bp_h, bearing_top_y)
            )
            x_start += hatch_spacing

        painter.restore()

        painter.setPen(QPen(QColor(150, 150, 150), 2.4))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(bp_rect)

        # CONCRETE BLOCK (TEXTURED)
        painter.setPen(pen_main)
        painter.setBrush(self.concrete_brush)

        painter.drawRect(QRectF(
            conc_left,
            conc_top_y,
            conc_w,
            conc_bot_y - conc_top_y
        ))

        dash_pen = QPen(QColor(0, 0, 0), 1)
        dash_pen.setStyle(Qt.DashLine)
        painter.setPen(dash_pen)

        # left projection
        painter.drawLine(
            QPointF(bp_left, bearing_bot_y),
            QPointF(bp_left, dim_y)
        )

        # right projection
        painter.drawLine(
            QPointF(bp_right, bearing_bot_y),
            QPointF(bp_right, dim_y)
        )

        #DIMENSION ARROW 
        self._draw_dim_arrow(painter, bp_left, dim_y, bp_right, dim_y)

        # Bottom zigzag
        ext = W * 0.05

        # left extension
        painter.drawLine(QPointF(conc_left - ext, conc_bot_y),
                          QPointF(conc_left - 1, conc_bot_y))

        # zigzag
        self._draw_h_zigzag(
            painter,
            conc_left + 1,
            conc_bot_y,
            conc_right,
            conc_bot_y,
            amplitude=12,
            steps=2,
            segments=2,
            pen=QPen(QColor(0, 0, 0), 1)
        )

        # right extension
        painter.drawLine(
            QPointF(conc_right, conc_bot_y),
            QPointF(conc_right + ext, conc_bot_y)
        )

        # 8. RIGHT-SIDE VERTICAL ZIGZAG
        ext = W * 0.05

        # top extension
        painter.drawLine(
            QPointF(zigzag_x, zz_top - ext),
            QPointF(zigzag_x, zz_top)
        )

        # zigzag
        self._draw_v_zigzag(
            painter,
            zigzag_x,
            zz_top,
            zz_bot,
            amplitude=12,
            steps=2,
            segments=2,
            pen=QPen(QColor(0, 0, 0), 1)
        )

        # bottom extension
        painter.drawLine(
            QPointF(zigzag_x, zz_bot),
            QPointF(zigzag_x, zz_bot + ext)
        )

        #same arrow length for all labels
        arrow_dx = W * 0.04
        arrow_dy = H * 0.08

        #LABELS
        stiff_mid_y = (tf_bot_y + bf_top_y) / 2

        # End bearing stiffener — leader from upper-right toward stiffener mid
        self._draw_leader(
            painter,
            stiff_right + arrow_dx,
            stiff_mid_y - arrow_dy,
            stiff_right + W * 0.02,
            stiff_mid_y,
            "End bearing\nstiffener"
        )

        # Bearing plate — label always anchored beyond zigzag to avoid overlap
        bp_mid_y = (bearing_top_y + bearing_bot_y) / 2

        self._draw_leader(
            painter,
            bp_right + arrow_dx,
            bp_mid_y - arrow_dy,
            bp_right,
            bp_mid_y,
            "Bearing plate"
        )
        
        mid_bp_x = (bp_left + bp_right) / 2

        rect = QRectF(
            mid_bp_x - 50,
            dim_y + H * 0.03,
            100,
            30
        )

        text = f"Bearing\nlength = {int(bearing_len)} mm"

        painter.setFont(QFont("Arial", 10))
        painter.drawText(rect, Qt.AlignCenter, "Bearing\nlength")

        # Plate girder — right of zigzag, above bearing plate label
        pg_mid_y = (zz_top + zz_bot) / 2

        self._draw_leader(
            painter,
            zigzag_x + arrow_dx,
            pg_mid_y - arrow_dy,
            zigzag_x,
            pg_mid_y,
            "Plate girder"
        )


    def _draw_dim_arrow(self, painter, x1, y, x2, y2, text=None):
        """Double-headed horizontal dimension arrow, no text."""
        painter.setPen(QPen(QColor(0, 0, 0), 1.0))
        painter.drawLine(QPointF(x1, y), QPointF(x2, y))
        tick = 4
        painter.drawLine(QPointF(x1, y - tick), QPointF(x1, y + tick))
        painter.drawLine(QPointF(x2, y - tick), QPointF(x2, y + tick))
        al, ah = 7.0, 7.0 / 3.0
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        painter.drawPolygon(QPolygonF([
            QPointF(x1, y),
            QPointF(x1 + al, y - ah),
            QPointF(x1 + al, y + ah),
        ]))
        painter.drawPolygon(QPolygonF([
            QPointF(x2, y),
            QPointF(x2 - al, y - ah),
            QPointF(x2 - al, y + ah),
        ]))

        if text:
            mid_x = (x1 + x2) / 2
            painter.setFont(QFont("Arial", 9))
            painter.drawText(QPointF(mid_x - 30, y - 5), text)

    def _draw_h_zigzag(self, painter, x1, y, x2, y2,
                            amplitude=12, steps=2, segments=2, pen=None):
        """
        Draws: straight → zigzag → straight → zigzag → straight (horizontal)
        """
        if pen:
            painter.setPen(pen)

        total_w = x2 - x1

        parts = [0.5, 0.6, 3.0, 0.6, 0.5] 

        total_parts = sum(parts)
        unit_w = total_w / total_parts

        current_x = x1

        for i, part in enumerate(parts):
            seg_w = part * unit_w

            if i % 2 == 0:
                # S (straight)
                painter.drawLine(QPointF(current_x, y),
                                QPointF(current_x + seg_w, y))
            else:
                # Z (zigzag)
                step_w = seg_w / steps
                pts = [QPointF(current_x, y)]

                for j in range(steps):
                    pts.append(QPointF(
                        current_x + (j + 0.5) * step_w,
                        y + (amplitude if j % 2 == 0 else -amplitude)
                    ))
                    pts.append(QPointF(
                        current_x + (j + 1) * step_w,
                        y
                    ))

                for k in range(len(pts) - 1):
                    painter.drawLine(pts[k], pts[k + 1])

            current_x += seg_w

    def _draw_v_zigzag(self, painter, x, y1, y2,
                            amplitude=12, steps=2, segments=2, pen=None):
        """
        Draws: straight → zigzag → straight → zigzag → straight
        segments = number of zigzag sections
        """
        if pen:
            painter.setPen(pen)

        total_h = y2 - y1

        parts = [1.0, 0.6, 2.5, 0.6, 1.0]

        total_parts = sum(parts)
        unit_h = total_h / total_parts

        current_y = y1

        for i, part in enumerate(parts):
            seg_h = part * unit_h

            if i % 2 == 0:
                #STRAIGHT (S)
                painter.drawLine(
                    QPointF(x, current_y),
                    QPointF(x, current_y + seg_h)
                )

            else:
                #ZIGZAG (Z)
                step_h = seg_h / steps
                pts = [QPointF(x, current_y)]

                for j in range(steps):
                    pts.append(QPointF(
                        x + (amplitude if j % 2 == 0 else -amplitude),
                        current_y + (j + 0.5) * step_h
                    ))
                    pts.append(QPointF(
                        x,
                        current_y + (j + 1) * step_h
                    ))

                for k in range(len(pts) - 1):
                    painter.drawLine(pts[k], pts[k + 1])

            current_y += seg_h

    def _draw_text_bg(self, painter, x, y, text,
                    bg=QColor(240, 240, 240, 230),
                    fg=QColor(0, 0, 0),
                    font_size=11, bold=False):

        font = QFont("Arial", 10)
        font.setWeight(QFont.Normal)
        painter.setFont(font)

        fm    = painter.fontMetrics()
        lines = text.split("\n")
        lh    = fm.height()
        mw    = max(fm.boundingRect(ln).width() for ln in lines)
        th    = lh * len(lines)
        pad   = 3

        painter.setPen(QPen(fg, 1.0))
        for i, ln in enumerate(lines):
            painter.drawText(
                int(x),
                int(y - th + fm.ascent() + i * lh),
                ln
            )

    def _draw_leader(self, painter, from_x, from_y, to_x, to_y, text,
                     text_color=QColor(0, 0, 0)):
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawLine(QPointF(from_x, from_y), QPointF(to_x, to_y))
        angle = math.atan2(to_y - from_y, to_x - from_x)
        al, ah = 6.0, 2.0
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        painter.drawPolygon(QPolygonF([
            QPointF(to_x, to_y),
            QPointF(to_x - al * math.cos(angle) + ah * math.sin(angle),
                    to_y - al * math.sin(angle) - ah * math.cos(angle)),
            QPointF(to_x - al * math.cos(angle) - ah * math.sin(angle),
                    to_y - al * math.sin(angle) + ah * math.cos(angle)),
        ]))
        self._draw_text_bg(painter, from_x + 3, from_y + 4, text,
                           fg=text_color, font_size=15, bold=True)

    def create_concrete_brush(self):
        import random, math
        

        SIZE = 120
        DOT_COUNT = 100
        TRI_COUNT = 30
        rng = random.Random(42)  # ← seeded RNG so tiles are deterministic

        def rand(): return rng.random()
        def rr(a, b): return a + rand() * (b - a)

        # ── Draw one copy of the content, offset by (ox, oy)
        def draw_content(p: QPainter, ox: float, oy: float):
            p.save()
            p.translate(ox, oy)

            # Fine aggregate — dots (sand / grit)
            p.setPen(Qt.NoPen)
            for _ in range(DOT_COUNT):
                x, y = rr(0, SIZE), rr(0, SIZE)
                r = rr(0.6, 2.2)
                h = int(rr(40, 110))
                p.setBrush(QColor(h, h, h))
                p.drawEllipse(QPointF(x, y), r, r)

            # Coarse aggregate — irregular triangles
            for _ in range(TRI_COUNT):
                cx, cy = rr(0, SIZE), rr(0, SIZE)
                base_angle = rr(0, 2 * math.pi)
                h = int(rr(70, 140))
                sat = int(rr(0, 10))

                poly = QPolygonF()
                for v in range(3):
                    ang = base_angle + v * (2 * math.pi / 3) + rr(-0.45, 0.45)
                    dist = rr(SIZE * 0.032, SIZE * 0.072)
                    poly.append(QPointF(cx + math.cos(ang) * dist,
                                        cy + math.sin(ang) * dist))

                fill_col = QColor(h + sat, h, h - sat)
                alpha = int(rr(64, 140))         # 25–55 % opacity stroke
                stroke_col = QColor(20, 20, 20, alpha)
                lw = rr(0.4, 0.8)

                p.setBrush(fill_col)
                p.setPen(QPen(stroke_col, lw))
                p.drawPolygon(poly)

            # Micro-scratches — cement paste surface texture
            p.setBrush(Qt.NoBrush)
            scratch_count = int(SIZE * 0.3)
            for _ in range(scratch_count):
                x, y = rr(0, SIZE), rr(0, SIZE)
                length = rr(2, SIZE * 0.08)
                ang = rr(0, math.pi * 2)
                alpha = int(rr(10, 31))           # 4–12 % opacity
                p.setPen(QPen(QColor(90, 85, 80, alpha), rr(0.3, 0.7)))
                p.drawLine(QPointF(x, y),
                        QPointF(x + math.cos(ang) * length,
                                y + math.sin(ang) * length))

            p.restore()

        # ── Build tile pixmap
        pixmap = QPixmap(SIZE, SIZE)
        pixmap.fill(QColor(225, 225, 225))     

        p = QPainter(pixmap)
        p.setRenderHint(QPainter.Antialiasing)

        # Draw all 9 offset copies so shapes that straddle any edge
        # are completed on the opposite side → perfect seamless wrap
        for dx in (-SIZE, 0, SIZE):
            for dy in (-SIZE, 0, SIZE):
                draw_content(p, dx, dy)

        # Very subtle wash to unify everything
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(100, 95, 88, 10))
        p.drawRect(0, 0, SIZE, SIZE)

        p.end()
        return QBrush(pixmap)                        