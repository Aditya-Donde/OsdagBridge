from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPen, QColor, QFont
from PySide6.QtCore import Qt


class VehicleViewer(QWidget):
    """
    Static transverse vehicle layout viewer.

    Draws:
    | f | Vehicle | g | Vehicle | f |

    Features:
    - Fixed scale (no auto-stretching)
    - Always centered
    - Extra margins for dimensions
    - Reduced drawing size
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(180)

        # Default values (mm)
        self.w = 2500
        self.f = 600
        self.g = 1200

        # Static drawing scale (mm → pixels)
        # Adjust between 0.04 – 0.06 if needed
        self.scale = 0.05

    # -------------------------------------------------
    # Data from dialog
    # -------------------------------------------------
    def set_data(self, w, f, g):
        # If width invalid → don't draw
        if w <= 0:
            self.w = None
            self.update()
            return

        self.w = w
        self.f = max(f, 0)
        self.g = max(g, 0)
        self.update()

    # -------------------------------------------------
    # Dimension helper (with arrows)
    # -------------------------------------------------
    def draw_dim_line(self, p, x1, x2, y, text):
        p.drawLine(x1, y, x2, y)

        arrow = 6

        # Left arrow
        p.drawLine(x1, y, x1 + arrow, y - arrow / 2)
        p.drawLine(x1, y, x1 + arrow, y + arrow / 2)

        # Right arrow
        p.drawLine(x2, y, x2 - arrow, y - arrow / 2)
        p.drawLine(x2, y, x2 - arrow, y + arrow / 2)

        # Center text properly
        fm = p.fontMetrics()
        text_width = fm.horizontalAdvance(text)
        p.drawText((x1 + x2) / 2 - text_width / 2, y + 14, text)

    # -------------------------------------------------
    # Painting
    # -------------------------------------------------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#ffffff"))

        width = self.width()
        height = self.height()
        y_center = height // 2

        # Total carriageway width (mm)
        total = self.f + self.w + self.g + self.w + self.f
        if total <= 0:
            return

        # -------- STATIC SCALE (fixed) --------
        scale = 0.04   # adjust once if needed

        drawing_width = total * scale

        # Center horizontally
        x = (width - drawing_width) / 2

        pen = QPen(Qt.black, 1.5)
        p.setPen(pen)

        # Carriageway boundary
        top = y_center - 35
        bottom = y_center + 35
        p.drawRect(x, top, drawing_width, bottom - top)

        # Vehicle positions
        x_vehicle1 = x + self.f * scale
        vehicle_w = self.w * scale
        vehicle_h = 30

        # Vehicle 1
        p.drawRect(x_vehicle1, y_center - vehicle_h/2, vehicle_w, vehicle_h)

        # Gap
        gap_start = x_vehicle1 + vehicle_w
        gap_width = self.g * scale

        # Vehicle 2
        x_vehicle2 = gap_start + gap_width
        p.drawRect(x_vehicle2, y_center - vehicle_h/2, vehicle_w, vehicle_h)
