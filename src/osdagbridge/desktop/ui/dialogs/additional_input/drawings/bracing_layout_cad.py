from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen, QColor

from osdagbridge.desktop.ui.utils.cad_palette import CAD_DIMENSION


class BracingLayoutCadWidget(QWidget):
    """Simple CAD-like bracing layout preview for K/X bracing."""

    def __init__(self, min_height: int = 170, parent=None):
        super().__init__(parent)
        self._bracing_type = "K-Bracing"
        self._top_chord = False
        self._bottom_chord = True
        self._member_label = ""
        self._girder_pair = ""
        self.setMinimumHeight(int(min_height))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_layout(
        self,
        bracing_type: str,
        top_chord: bool,
        bottom_chord: bool,
        member_label: str = "",
        girder_pair: str = "",
    ) -> None:
        self._bracing_type = (bracing_type or "K-Bracing").strip() or "K-Bracing"
        self._top_chord = bool(top_chord)
        self._bottom_chord = bool(bottom_chord)
        self._member_label = (member_label or "").strip()
        self._girder_pair = (girder_pair or "").strip()
        self.update()

    def paintEvent(self, _event):  # noqa: N802
        from PySide6.QtCore import QPointF
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        canvas = self.rect()
        painter.fillRect(canvas, QColor("#ffffff"))

        draw = canvas.adjusted(24, 14, -24, -38)
        if draw.width() <= 10 or draw.height() <= 10:
            return

        x_left  = draw.left()  + int(draw.width()  * 0.15)
        x_right = draw.right() - int(draw.width()  * 0.15)
        y_top    = draw.top()   + int(draw.height() * 0.10)
        y_bottom = draw.bottom()- int(draw.height() * 0.14)

        fw = 40
        ft = 8
        wt = 6

        x_l_conn = x_left  + wt // 2
        x_r_conn = x_right - wt // 2

        strut_offset = 12
        y_T_WP = y_top    + strut_offset if self._top_chord    else y_top    + 15
        y_B_WP = y_bottom - strut_offset if self._bottom_chord else y_bottom - 15

        wp_tl = QPointF(x_l_conn, y_T_WP)
        wp_tr = QPointF(x_r_conn, y_T_WP)
        wp_bl = QPointF(x_l_conn, y_B_WP)
        wp_br = QPointF(x_r_conn, y_B_WP)

        line_color = QColor("#000000")

        painter.setPen(QPen(line_color, 2))
        if self._top_chord:
            painter.drawLine(wp_tl, wp_tr)
        if self._bottom_chord:
            painter.drawLine(wp_bl, wp_br)

        brace_pen = QPen(line_color, 2)
        brace_pen.setCapStyle(Qt.RoundCap)
        brace_pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(brace_pen)

        if self._bracing_type == "K-Bracing":
            if self._top_chord and not self._bottom_chord:
                apex = QPointF((x_l_conn + x_r_conn) / 2.0, y_T_WP)
                painter.drawLine(wp_bl, apex)
                painter.drawLine(wp_br, apex)
            else:
                apex = QPointF((x_l_conn + x_r_conn) / 2.0, y_B_WP)
                painter.drawLine(wp_tl, apex)
                painter.drawLine(wp_tr, apex)
        else:
            painter.drawLine(wp_tl, wp_br)
            painter.drawLine(wp_bl, wp_tr)

        painter.setPen(QPen(line_color, 1.6))
        painter.setBrush(Qt.NoBrush)

        painter.drawRect(int(x_left  - fw//2), int(y_top - ft), fw, ft)
        painter.drawRect(int(x_left  - fw//2), int(y_bottom),   fw, ft)
        painter.drawRect(int(x_left  - wt//2), int(y_top),      wt, int(y_bottom - y_top))

        painter.drawRect(int(x_right - fw//2), int(y_top - ft), fw, ft)
        painter.drawRect(int(x_right - fw//2), int(y_bottom),   fw, ft)
        painter.drawRect(int(x_right - wt//2), int(y_top),      wt, int(y_bottom - y_top))

        def compact_member_label(raw_text: str) -> str:
            text = (raw_text or "").strip()
            if " to " in text:
                parts = [p.strip() for p in text.split(" to ", 1)]
                if len(parts) == 2 and parts[0] and parts[1]:
                    return f"{parts[0]} - {parts[1]}"
            return text or "B1M1"

        pair_text = self._girder_pair or "G1-G2"
        left_girder, right_girder = "G1", "G2"
        sep = " to " if " to " in pair_text else ("-" if "-" in pair_text else None)
        if sep:
            parts = [p.strip() for p in pair_text.split(sep, 1)]
            if len(parts) == 2 and parts[0] and parts[1]:
                left_girder, right_girder = parts[0], parts[1]

        pen = QPen(CAD_DIMENSION, 1.1)
        painter.setPen(pen)

        label_bg = QColor(255, 255, 255, 225)
        pad_x = 6
        pad_y = 3

        def draw_label_box(text: str, center_x: float, box_y: float, font_size: int = 8) -> None:
            if not text:
                return
            f = painter.font()
            f.setPointSize(font_size)
            f.setBold(True)
            painter.setFont(f)
            fm = painter.fontMetrics()

            txt_w = fm.horizontalAdvance(text)
            txt_h = fm.height()
            box_w = txt_w + (2 * pad_x)
            box_h = txt_h + (2 * pad_y)

            box_x = center_x - (box_w / 2.0)
            box_x = max(8.0, min(box_x, self.width() - box_w - 8.0))
            box_y = max(8.0, min(box_y, self.height() - box_h - 8.0))

            painter.setPen(Qt.NoPen)
            painter.setBrush(label_bg)
            painter.drawRoundedRect(int(box_x), int(box_y), int(box_w), int(box_h), 4, 4)
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(CAD_DIMENSION, 1.0))
            painter.drawText(int(box_x + pad_x), int(box_y + box_h - pad_y - 2), text)

        member_text = compact_member_label(self._member_label)
        label_y = y_bottom + ft + 12
        mid_x = (x_left + x_right) / 2.0

        draw_label_box(f"Girder {left_girder}", x_left,  label_y, 8)
        draw_label_box(member_text,             mid_x,   label_y, 11)
        draw_label_box(f"Girder {right_girder}", x_right, label_y, 8)

