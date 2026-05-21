from PySide6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsPolygonItem,
    QGraphicsRectItem,
    QGraphicsLineItem,
    QGraphicsSimpleTextItem,
)
from PySide6.QtGui import QPen, QBrush, QColor, QPolygonF, QPainter, QFont
from PySide6.QtCore import Qt, QPointF, QRectF, QTimer

_PALETTE = {
    "background": "#f5f7f9",
    "deck": "#afafaf",
    "deck_border": "#3c3c3c",
    "support": "#969696",
    "load": "#D32F2F",
    "text": "#1a1a1a",
    "text_title": "#1e293b",
    "grid": "#d2d7dc",
    "white": "#ffffff"
}

_W = 1000.0
_H = 400.0
_DECK_THICK = 40.0
_MARGIN = 150.0
_GRID_Y_OFFSET = 60.0
_DIM_Y_OFFSET = 120.0
_TITLE_Y = 50.0
_ARROW_LEN = 80.0
_ARROW_HEAD_W = 12.0
_ARROW_HEAD_H = 18.0
_ARROW_STROKE = 6.0
_GIRDER_WIDTH_FRAC = 0.04
_GIRDER_HEIGHT_FRAC = 1.5
_GIRDER_POSITIONS = [0.2, 0.5, 0.8]
_GIRDER_LABELS = ["G1", "G2", "G3"]
_SUPPORT_W = 40.0
_SUPPORT_H = 40.0
_LINE_ARROW_DIST = 60.0


class CustomLoadCanvas(QGraphicsView):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self._first_render = True

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

        self._load_data = None
        self._bridge_width = 10.0
        self._span_length = 20.0
        self._view = "cross_section"
        self._last_bw = 0.0

        self.setStyleSheet("background-color: transparent; border: none;")
        self.setAlignment(Qt.AlignCenter)
        self._updating = False

    def set_load_data(self, data, bridge_width=10.0, span_length=20.0):
        self._load_data = data
        self._bridge_width = bridge_width if bridge_width > 0 else 10.0
        self._span_length = span_length if span_length > 0 else 20.0

        phys_len = self._bridge_width if self._view == "cross_section" else self._span_length
        bw = max(phys_len, 1.0)

        significant_change = abs(bw - self._last_bw) / bw > 0.01 if self._last_bw > 0 else True

        self.draw_scene(fit_view=(self._first_render or significant_change))

        self._first_render = False
        self._last_bw = bw

    def set_view(self, view_mode):
        mode_changed = (self._view != view_mode)
        self._view = view_mode
        self.draw_scene(fit_view=mode_changed)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(50, lambda: self.draw_scene(fit_view=True))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.draw_scene()

    def zoom_in(self):
        self.scale(1.5, 1.5)

    def zoom_out(self):
        self.scale(1 / 1.5, 1 / 1.5)

    def reset_view(self):
        self.draw_scene(fit_view=True)

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()
        event.accept()

    def draw_dimension_line(self, px1, px2, text, y_pos):
        # Draw dimension lines
        pen_dash = QPen(QColor(_PALETTE["text"]), 3, Qt.DashLine)
        pen_solid = QPen(QColor(_PALETTE["text"]), 3, Qt.SolidLine)

        line = QGraphicsLineItem(px1, y_pos, px2, y_pos)
        line.setPen(pen_dash)
        self._scene.addItem(line)

        for px in (px1, px2):
            tick = QGraphicsLineItem(px, y_pos - 10, px, y_pos + 10)
            tick.setPen(pen_solid)
            self._scene.addItem(tick)

        if text:
            font = QFont("Arial", 18)
            txt = QGraphicsSimpleTextItem(text)
            txt.setFont(font)
            txt.setBrush(QBrush(QColor(_PALETTE["text"])))

            txt_w = txt.boundingRect().width()
            txt_h = txt.boundingRect().height()
            cx = (px1 + px2) / 2

            bg_rect = QGraphicsRectItem(cx - txt_w / 2 - 8, y_pos - txt_h / 2 - 4, txt_w + 16, txt_h + 8)
            bg_rect.setBrush(QBrush(QColor(_PALETTE["white"])))
            bg_rect.setPen(QPen(Qt.NoPen))
            bg_rect.setZValue(1)
            self._scene.addItem(bg_rect)

            txt.setPos(cx - txt_w / 2, y_pos - txt_h / 2)
            txt.setZValue(2)
            self._scene.addItem(txt)

    def draw_scene(self, fit_view=False):
        if getattr(self, "_updating", False):
            return
        self._updating = True

        try:
            # Clear scene
            self._scene.clear()
            self._scene.setBackgroundBrush(QColor(_PALETTE["background"]))

            w, h = _W, _H

            if not self._load_data:
                self._zoom_empty(w, h)
                return

            load_type = self._load_data.get("type", "").lower()
            if load_type not in ("point", "line", "area"):
                self._zoom_empty(w, h)
                return

            # Get bridge dimensions
            phys_len = (
                self._bridge_width if self._view == "cross_section" else self._span_length
            )
            bw = max(phys_len, 1.0)

            if self._view == "cross_section":
                x1 = float(self._load_data.get("dist_left_start", 0.0))
                x2 = float(self._load_data.get("dist_left_end", 0.0))
            else:
                x1 = float(self._load_data.get("dist_bear_start", 0.0))
                x2 = float(self._load_data.get("dist_bear_end", 0.0))

            x1 = max(0.0, min(x1, bw))
            x2 = max(0.0, min(x2, bw))
            if x1 > x2:
                x1, x2 = x2, x1

            if load_type == "area" and abs(x2 - x1) < 0.1:
                x2 = x1 + 0.1

            deck_top = h / 2.0
            deck_thick = _DECK_THICK
            deck_bot = deck_top + deck_thick

            # Scale factor
            margin = _MARGIN
            scale_x = (w - 2 * margin) / bw

            def map_x(x):
                return margin + x * scale_x

            px_left = map_x(0)
            px_right = map_x(bw)
            deck_w = px_right - px_left

            self._draw_grid(w, h, bw, margin, scale_x, deck_bot + _GRID_Y_OFFSET)

            deck_color = QColor(_PALETTE["deck"])
            deck_pen = QColor(_PALETTE["deck_border"])
            load_color = QColor(_PALETTE["load"])

            deck_rect = QGraphicsRectItem(px_left, deck_top, deck_w, deck_thick)
            deck_rect.setBrush(QBrush(deck_color))
            deck_rect.setPen(QPen(deck_pen, 2))
            deck_rect.setZValue(0)
            self._scene.addItem(deck_rect)

            # Draw girders/supports
            if self._view == "cross_section":
                g_w = max(20.0, deck_w * _GIRDER_WIDTH_FRAC)
                g_h = deck_thick * _GIRDER_HEIGHT_FRAC
                for i, label in zip(_GIRDER_POSITIONS, _GIRDER_LABELS):
                    gx = px_left + deck_w * i - g_w / 2.0
                    g_rect = QGraphicsRectItem(gx, deck_bot, g_w, g_h)
                    g_rect.setBrush(QBrush(deck_color))
                    g_rect.setPen(QPen(deck_pen, 2))
                    g_rect.setZValue(0)
                    self._scene.addItem(g_rect)

                    lbl = QGraphicsSimpleTextItem(label)
                    lbl.setFont(QFont("Arial", 14, QFont.Bold))
                    lbl.setBrush(QBrush(QColor(_PALETTE["text"])))
                    lbl.setZValue(1)
                    lbl_h = lbl.boundingRect().height()
                    lbl.setPos(gx + g_w / 2 - lbl.boundingRect().width() / 2,
                                deck_bot + g_h / 2 - lbl_h / 2)
                    self._scene.addItem(lbl)
            else:
                sup_w = _SUPPORT_W
                sup_h = _SUPPORT_H
                for px in (px_left, px_right):
                    poly = QPolygonF(
                        [
                            QPointF(px, deck_bot),
                            QPointF(px - sup_w / 2, deck_bot + sup_h),
                            QPointF(px + sup_w / 2, deck_bot + sup_h),
                        ]
                    )
                    sup = QGraphicsPolygonItem(poly)
                    sup.setBrush(QBrush(QColor(_PALETTE["support"])))
                    sup.setPen(QPen(deck_pen, 2))
                    sup.setZValue(0)
                    self._scene.addItem(sup)

            title_text = {"point": "Point Load", "line": "Line Load", "area": "Area Load"}.get(load_type, "Load")
            title_item = QGraphicsSimpleTextItem(title_text)
            title_item.setFont(QFont("Arial", 20, QFont.Bold))
            title_item.setBrush(QBrush(QColor(_PALETTE["text_title"])))
            title_item.setZValue(2)
            title_item.setPos(w / 2.0 - title_item.boundingRect().width() / 2.0, _TITLE_Y)
            self._scene.addItem(title_item)

            # Draw load arrows
            y_end = deck_top
            y_start = y_end - _ARROW_LEN

            mag = self._load_data.get("magnitude", "")
            unit = {"line": "kN/m", "area": "kN/m²"}.get(load_type, "kN")
            mag_txt = f"{mag} {unit}" if mag else ""

            def draw_arrow(x):
                line = QGraphicsLineItem(x, y_start, x, y_end)
                line.setPen(QPen(load_color, _ARROW_STROKE))
                line.setZValue(1)
                self._scene.addItem(line)

                head = QGraphicsPolygonItem(
                    QPolygonF(
                        [
                            QPointF(x, y_end),
                            QPointF(x - _ARROW_HEAD_W, y_end - _ARROW_HEAD_H),
                            QPointF(x + _ARROW_HEAD_W, y_end - _ARROW_HEAD_H),
                        ]
                    )
                )
                head.setBrush(QBrush(load_color))
                head.setPen(QPen(Qt.NoPen))
                head.setZValue(1)
                self._scene.addItem(head)

            def add_small_label(t, mag_text, cx):
                combined = f"{t} = {mag_text}" if mag_text else t
                txt = QGraphicsSimpleTextItem(combined)
                txt.setFont(QFont("Arial", 16, QFont.Bold))
                txt.setBrush(QBrush(load_color))
                txt.setZValue(2)
                txt.setPos(cx - txt.boundingRect().width() / 2, y_start - 35)
                self._scene.addItem(txt)

            px1 = map_x(x1)
            px2 = map_x(x2)

            if load_type == "point":
                draw_arrow(px1)
                add_small_label("P", mag_txt, px1)
                self.draw_dimension_line(px_left, px1, f"x = {x1:.1f} m", deck_bot + _DIM_Y_OFFSET)

            elif load_type == "line":
                dist = px2 - px1
                if dist < 40:
                    draw_arrow((px1 + px2) / 2.0)
                else:
                    num_arrows = max(2, int(dist / _LINE_ARROW_DIST) + 1)
                    for i in range(num_arrows):
                        draw_arrow(px1 + dist * (i / (num_arrows - 1)))

                    horiz = QGraphicsLineItem(px1, y_start, px2, y_start)
                    horiz.setPen(QPen(load_color, 4))
                    horiz.setZValue(1)
                    self._scene.addItem(horiz)
                add_small_label("w", mag_txt, (px1 + px2) / 2)
                self.draw_dimension_line(px1, px2, f"x\u2081 = {x1:.1f} m to x\u2082 = {x2:.1f} m", deck_bot + _DIM_Y_OFFSET)

            elif load_type == "area":
                dist = px2 - px1
                w_rect = max(dist, 2.0)
                area = QGraphicsRectItem(px1, y_start, w_rect, y_end - y_start)
                col = QColor(load_color)
                col.setAlpha(80)
                area.setBrush(QBrush(col))
                if dist < 40:
                    area.setPen(QPen(Qt.NoPen))
                else:
                    area.setPen(QPen(load_color, 2, Qt.DashLine))
                area.setZValue(1)
                self._scene.addItem(area)

                if dist < 40:
                    draw_arrow((px1 + px2) / 2.0)
                else:
                    num_arrows = max(2, int(dist / _LINE_ARROW_DIST) + 1)
                    for i in range(num_arrows):
                        draw_arrow(px1 + dist * (i / (num_arrows - 1)))
                add_small_label("q", mag_txt, px1 + w_rect / 2.0)
                self.draw_dimension_line(px1, px2, f"A = {x1:.1f} m \u2013 {x2:.1f} m", deck_bot + _DIM_Y_OFFSET)

            rect = QRectF(0, 0, w, h)
            self._scene.setSceneRect(rect)
            if fit_view:
                self.fitInView(rect, Qt.KeepAspectRatio)

        finally:
            self._updating = False

    def _draw_grid(self, logical_w, logical_h, bw, margin, scale_x, axis_y):
        # Draw grid background
        grid_pen = QPen(QColor(_PALETTE["grid"]), 1, Qt.SolidLine)
        grid_step_m = bw / 10.0
        if grid_step_m < 0.1:
            grid_step_m = 0.1

        px_left = margin
        px_right = margin + bw * scale_x

        for i in range(11):
            x_m = i * grid_step_m
            px = margin + x_m * scale_x
            line = self._scene.addLine(px, axis_y - 200, px, axis_y + 50, grid_pen)
            line.setZValue(-1)

        axis_line = QGraphicsLineItem(px_left, axis_y, px_right, axis_y)
        axis_line.setPen(QPen(QColor(_PALETTE["text"]), 2))
        axis_line.setZValue(0)
        self._scene.addItem(axis_line)

        tick_font = QFont("Arial", 14, QFont.Bold)
        for i in range(11):
            if i % 2 != 0 and i != 10:
                continue
            x_m = i * grid_step_m
            px = margin + x_m * scale_x
            tick = QGraphicsLineItem(px, axis_y - 6, px, axis_y + 6)
            tick.setPen(QPen(QColor(_PALETTE["text"]), 2))
            tick.setZValue(0)
            self._scene.addItem(tick)

            lbl_text = f"{x_m:g} m"
            txt = QGraphicsSimpleTextItem(lbl_text)
            txt.setFont(tick_font)
            txt.setBrush(QBrush(QColor(_PALETTE["text"])))
            txt.setPos(px - txt.boundingRect().width() / 2, axis_y + 10)
            self._scene.addItem(txt)

    def _zoom_empty(self, logical_w, logical_h):
        rect = QRectF(0, 0, logical_w, logical_h)
        self._scene.setSceneRect(rect)
        self.fitInView(rect, Qt.KeepAspectRatio)
