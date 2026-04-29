import math
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QBrush, QPolygonF
from PySide6.QtCore import Qt, QRectF, QPointF

def draw_arrow_down(painter: QPainter, x: float, start_y: float, end_y: float):
    # Draw vertical line
    painter.drawLine(QPointF(x, start_y), QPointF(x, end_y))
    # Draw arrow head
    head_size = 6
    polygon = QPolygonF([
        QPointF(x, end_y),
        QPointF(x - head_size/2, end_y - head_size),
        QPointF(x + head_size/2, end_y - head_size)
    ])
    painter.setBrush(painter.pen().color())
    painter.drawPolygon(polygon)

def draw_horizontal_arrow(painter: QPainter, x_tip: float, y_tip: float, direction: int, length: float = 12):
    """Draw a horizontal arrow with filled triangular arrowhead.
    direction: 1 for right-pointing, -1 for left-pointing
    """
    painter.setBrush(QBrush(painter.pen().color()))
    arrow_w = 7
    arrow_h = 3
    if direction > 0: # >
        p1 = QPointF(x_tip, y_tip)
        p2 = QPointF(x_tip - arrow_w, y_tip - arrow_h)
        p3 = QPointF(x_tip - arrow_w, y_tip + arrow_h)
        x_tail = x_tip - length
    else: # <
        p1 = QPointF(x_tip, y_tip)
        p2 = QPointF(x_tip + arrow_w, y_tip - arrow_h)
        p3 = QPointF(x_tip + arrow_w, y_tip + arrow_h)
        x_tail = x_tip + length
    painter.drawPolygon(QPolygonF([p1, p2, p3]))
    painter.drawLine(x_tail, y_tip, x_tip, y_tip)

def draw_dim_line(painter: QPainter, x1: float, x2: float, y_pos: float, label: str,
                  tick_above: float = 0, tick_below: float = 0, label_below: bool = True):
    """Draw a standardized dimension line with outward-pointing filled arrowheads,
    optional vertical tick extensions, and a centered label.
    Used across ALL diagrams for consistent dimensioning style.
    """
    span = x2 - x1
    arm = min(10, span * 0.35)

    # Outward-pointing arrows at both ends
    draw_horizontal_arrow(painter, x1, y_pos, -1, int(arm))   # left-pointing at left edge
    draw_horizontal_arrow(painter, x2, y_pos, 1, int(arm))    # right-pointing at right edge

    # Connecting line between arrowheads
    painter.drawLine(int(x1 + arm), int(y_pos), int(x2 - arm), int(y_pos))

    # Optional vertical tick lines
    if tick_above > 0:
        painter.drawLine(int(x1), int(y_pos - tick_above), int(x1), int(y_pos))
        painter.drawLine(int(x2), int(y_pos - tick_above), int(x2), int(y_pos))
    if tick_below > 0:
        painter.drawLine(int(x1), int(y_pos), int(x1), int(y_pos + tick_below))
        painter.drawLine(int(x2), int(y_pos), int(x2), int(y_pos + tick_below))

    # Centered label
    if label:
        if label_below:
            label_y = y_pos + 2
        else:
            label_y = y_pos - 14
        painter.drawText(QRectF(x1, label_y, span, 14), Qt.AlignCenter, label)


def draw_text_with_subscript(painter: QPainter, rect: QRectF, base: str, sub: str, alignment=Qt.AlignCenter):
    """Draw text with a subscript character, e.g. P with subscript b."""
    fm = painter.fontMetrics()
    base_w = fm.horizontalAdvance(base)
    
    # Save current font
    orig_font = painter.font()
    sub_font = QFont(orig_font)
    sub_size = max(5, int(orig_font.pointSize() * 0.7))
    sub_font.setPointSize(sub_size)
    sub_fm = painter.fontMetrics()  # we'll measure after setting
    
    # Measure subscript width
    painter.setFont(sub_font)
    sub_w = painter.fontMetrics().horizontalAdvance(sub)
    painter.setFont(orig_font)
    
    total_w = base_w + sub_w
    
    # Compute starting X based on alignment
    if alignment & Qt.AlignCenter:
        start_x = rect.x() + (rect.width() - total_w) / 2
    elif alignment & Qt.AlignRight:
        start_x = rect.x() + rect.width() - total_w
    else:
        start_x = rect.x()
    
    # Draw base text
    base_y = rect.y() + rect.height() * 0.75  # baseline position
    painter.setFont(orig_font)
    painter.drawText(QPointF(start_x, base_y), base)
    
    # Draw subscript (shifted down and smaller)
    painter.setFont(sub_font)
    sub_y = base_y + fm.descent()  # shift down for subscript
    painter.drawText(QPointF(start_x + base_w, sub_y), sub)
    
    # Restore original font
    painter.setFont(orig_font)


class TrackedBogieDiagram(QWidget):
    def __init__(self, label_force, label_dist, parent=None):
        super().__init__(parent)
        self.label_force = label_force
        self.label_dist = label_dist
        self.setMinimumSize(280, 80)

    def _is_bogie(self):
        return "Pb" in self.label_force or self.label_force == "Pb"

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background and border (gray rounded rect)
        rect = self.rect().adjusted(1, 1, -2, -2)
        painter.setPen(QPen(QColor("#a0a0a0"), 1))
        painter.setBrush(QBrush(QColor("#dfdfdf")))  # Light gray background
        painter.drawRoundedRect(rect, 8, 8)
        
        w, h = self.width(), self.height()
        is_bogie = self._is_bogie()
        
        # Left title text
        painter.setPen(QPen(QColor("#cc0000"), 1)) # Red text
        font = QFont("Arial", 9)
        font.setBold(True)
        painter.setFont(font)
        
        if is_bogie:
            title = "Bogie\nCars"
        else:
            title = "Tracked\nVehicles"
            
        painter.drawText(QRectF(15, 0, 70, h), Qt.AlignLeft | Qt.AlignVCenter, title)
        
        # Coordinates for arrows and lines
        start_x = 90
        end_x = w - 25
        arrow_start_y = 20
        arrow_end_y = 45
        line_y = 52 # dashed line between arrows
        dist_y = 65 # distance line
        
        # Labels and Arrows
        if is_bogie:
            # Draw separate P with subscript b
            painter.setPen(QPen(QColor("#000000"), 1))
            draw_text_with_subscript(painter, QRectF(start_x-15, 0, 30, 20), "P", "b")
            draw_text_with_subscript(painter, QRectF(end_x-15, 0, 30, 20), "P", "b")
            
            # Arrows (Red, separate downward arrows)
            painter.setPen(QPen(QColor("#cc0000"), 1.5))
            draw_arrow_down(painter, start_x, arrow_start_y, arrow_end_y)
            draw_arrow_down(painter, end_x, arrow_start_y, arrow_end_y)
        else:
            # Single centered label P
            painter.setPen(QPen(QColor("#000000"), 1))
            span = end_x - start_x
            label_rect = QRectF(start_x, 0, span, 20)
            painter.drawText(label_rect, Qt.AlignCenter, self.label_force)
            
            # Arrows (Red, continuous downward bracket)
            painter.setPen(QPen(QColor("#cc0000"), 1.5))
            painter.drawLine(start_x, arrow_start_y, end_x, arrow_start_y)
            draw_arrow_down(painter, start_x, arrow_start_y, arrow_end_y)
            draw_arrow_down(painter, end_x, arrow_start_y, arrow_end_y)
        
        # Horizontal dashed line between arrows
        painter.setPen(QPen(QColor("#000000"), 1, Qt.DashLine))
        painter.drawLine(start_x - 10, line_y, end_x + 10, line_y)
        
        # Dimension line with proper arrowheads (black, consistent style)
        painter.setPen(QPen(QColor("#000000"), 1))
        font_normal = QFont("Arial", 8)
        painter.setFont(font_normal)
        
        # Vertical ticks from dashed line down to dimension line
        painter.drawLine(start_x, line_y, start_x, dist_y + 5)
        painter.drawLine(end_x, line_y, end_x, dist_y + 5)
        
        # Draw dimension line with outward arrowheads
        if is_bogie:
            draw_dim_line(painter, start_x, end_x, dist_y, "", label_below=True)
            # Draw D with subscript b as the label
            span = end_x - start_x
            draw_text_with_subscript(painter, QRectF(start_x, dist_y + 2, span, 15), "D", "b")
        else:
            draw_dim_line(painter, start_x, end_x, dist_y, self.label_dist, label_below=True)

class WheeledAxlesDiagram(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 90)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        
        # Background with border
        painter.setBrush(QBrush(QColor("#dfdfdf"))) # light gray back box
        painter.setPen(QPen(QColor("#a0a0a0"), 1))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -2, -2), 8, 8)
        
        # Define axles with unicode subscripts and spacing
        axles = [
            ("P₁", 20, "D₁"), 
            ("P₂", 60, "D₂"), 
            ("P₃", 100, ""), 
            ("Pₙ₋₁", 160, "Dₙ₋₁"), 
            ("Pₙ", 200, "")
        ]
        
        arrow_start_y = 22   # top of arrow shaft (raised to avoid label overlap)
        arrow_end_y = 40
        line_y = 47
        dist_y = 70  # moved farther from the dashed line
        
        painter.setFont(QFont("Arial", 8))
        
        for idx, (label, x, dist_label) in enumerate(axles):
            # Force label (black)
            painter.setPen(QPen(QColor("#000000"), 1))
            painter.drawText(QRectF(x-20, 2, 40, 18), Qt.AlignCenter, label)
            
            # Arrow (RED — original color theme)
            painter.setPen(QPen(QColor("#cc0000"), 1.5))
            draw_arrow_down(painter, x, arrow_start_y, arrow_end_y)
            
            painter.setPen(QPen(QColor("#000000"), 1))
            # Vertical tick down to dimension line
            painter.drawLine(x, line_y, x, dist_y + 5)
            
            if dist_label:
                next_x = axles[idx+1][1]
                # Draw dimension line with proper filled arrowheads (black)
                painter.setPen(QPen(QColor("#000000"), 1))
                draw_dim_line(painter, x, next_x, dist_y, "", label_below=True)
                # Dimension label below the line
                painter.drawText(QRectF(x, dist_y + 2, next_x - x, 15), Qt.AlignCenter, dist_label)

        # Continuous dashed horizontal road line (extended slightly)
        painter.setPen(QPen(QColor("#000000"), 1, Qt.DashLine))
        painter.drawLine(axles[0][1] - 15, line_y, axles[-1][1] + 15, line_y)
        
        # Dots for axle continuation (Black)
        painter.setPen(QPen(QColor("#000000"), 2))
        painter.drawText(QRectF( axles[2][1], 15, axles[3][1]-axles[2][1], 35 ), Qt.AlignCenter, ". . . . . . . .")
        
        # Continuity dots for dimension line (black)
        painter.setPen(QPen(QColor("#000000"), 2))
        painter.drawText(QRectF( axles[2][1], dist_y - 12, axles[3][1]-axles[2][1], 25 ), Qt.AlignCenter, ". . . . . . . .")


class ClearCarriagewayWidthDiagram(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(460, 260)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # White background with subtle border
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.setPen(QPen(QColor("#a0a0a0"), 1))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -2, -2), 8, 8)

        w, h = self.width(), self.height()
        pen = QColor("#000000")

        # ────────────────────────────────────
        # Layout constants
        # ────────────────────────────────────
        start_x = 40                          # left kerb boundary
        end_x = w - 40                        # right kerb boundary
        y_title = 28                          # title / top dimension arrow Y
        y_road = h - 52                       # road surface (zigzag baseline) Y
        y_kerb_line = y_road - 20             # kerb top horizontal line Y
        y_w_dim = h - 18                      # w dimension line Y

        # Vehicle geometry
        h_body = 80                           # vehicle body height
        w_body = 110                          # vehicle body width
        h_connector = 8                       # small connector rectangle height
        road_clearance = 0                    # gap between vehicle assembly and road
        h_wheel = 28                          # wheel height
        w_wheel = 16                          # wheel width
        wheel_inset = 16                      # wheel offset from body edge

        # Derived Y positions
        y_wheel_bottom = y_road - road_clearance  # road_clearance is 0 now
        y_wheel_top = y_wheel_bottom - h_wheel
        
        body_gap = 0                          # Wheels touch the main body directly
        y_body_bottom = y_wheel_top - body_gap
        y_body_top = y_body_bottom - h_body

        # f/g dimension line – at midpoint of wheel area
        y_fg = y_wheel_top + h_wheel // 2

        # ────────────────────────────────────
        # 1. TITLE: "CLEAR CARRIAGEWAY WIDTH" – BOLD
        # ────────────────────────────────────
        font_title = QFont("Arial", 8)
        font_title.setBold(True)
        painter.setFont(font_title)
        painter.setPen(QPen(pen, 1))

        title = "CLEAR CARRIAGEWAY WIDTH"
        fm = painter.fontMetrics()
        title_w = fm.horizontalAdvance(title)
        title_x = (w - title_w) / 2

        painter.drawText(QRectF(title_x, y_title - 7, title_w, 14),
                         Qt.AlignCenter, title)

        # Reset to non-bold for everything else
        font8 = QFont("Arial", 8)
        painter.setFont(font8)

        # Left arrow: from start_x to just before text
        left_arm = int(title_x - 8 - start_x)
        if left_arm > 0:
            draw_horizontal_arrow(painter, start_x, y_title, -1, left_arm)
        # Right arrow: from just after text to end_x
        right_arm = int(end_x - (title_x + title_w + 8))
        if right_arm > 0:
            draw_horizontal_arrow(painter, end_x, y_title, 1, right_arm)

        # ────────────────────────────────────
        # 2. VERTICAL BOUNDARY LINES (left & right kerb edges)
        #    Extended down past the f/g dimension line so f-arrows touch
        # ────────────────────────────────────
        painter.setPen(QPen(pen, 1))
        painter.drawLine(start_x, y_title - 7, start_x, y_road)
        painter.drawLine(end_x, y_title - 7, end_x, y_road)

        # ────────────────────────────────────
        # 3. KERB: horizontal line + diagonal hatching (left & right)
        # ────────────────────────────────────
        kerb_left_start = 1
        kerb_right_end = w - 1

        # Left kerb
        painter.drawLine(kerb_left_start, y_kerb_line, start_x, y_kerb_line)
        for gx in range(kerb_left_start, int(start_x) + 1, 6):
            painter.drawLine(gx, y_kerb_line, gx - 3, y_kerb_line + 5)

        # Right kerb
        painter.drawLine(end_x, y_kerb_line, kerb_right_end, y_kerb_line)
        for gx in range(int(end_x) + 6, kerb_right_end + 1, 6):
            painter.drawLine(gx, y_kerb_line, gx - 3, y_kerb_line + 5)

        # ────────────────────────────────────
        # 4. ROAD SURFACE: bold zigzag between kerb boundaries
        # ────────────────────────────────────
        painter.setPen(QPen(pen, 1.8))
        zz_step = 5
        zz_amp = 4
        zx = float(start_x)
        zx_end = float(end_x)
        while zx < zx_end:
            pk = min(zx + zz_step, zx_end)
            vl = min(zx + 2 * zz_step, zx_end)
            painter.drawLine(QPointF(zx, y_road),
                             QPointF(pk, y_road - zz_amp))
            if pk < zx_end:
                painter.drawLine(QPointF(pk, y_road - zz_amp),
                                 QPointF(vl, y_road))
            zx = vl
            if zx >= zx_end:
                break
        painter.setPen(QPen(pen, 1))

        # ────────────────────────────────────
        # 5. VEHICLES (two identical trucks)
        # ────────────────────────────────────
        available = end_x - start_x

        def draw_vehicle(vx):
            painter.setBrush(QBrush(QColor("#ffffff")))
            painter.setPen(QPen(pen, 1))

            # Main body rectangle (tall box)
            painter.drawRect(int(vx), int(y_body_top), w_body, h_body)

            # Central horizontal block attached to the big block
            w_center_block = 30
            h_center_block = 14
            cx = vx + (w_body - w_center_block) / 2
            painter.drawRect(int(cx), int(y_body_bottom), w_center_block, h_center_block)

            # Left side: wheel (straight lines)
            wl = vx + wheel_inset
            # Wheel rectangle
            painter.drawRect(int(wl), int(y_wheel_top), w_wheel, h_wheel)
            # Wheel center axle line (extended down to touch the road)
            painter.drawLine(QPointF(wl + w_wheel / 2, y_wheel_top),
                             QPointF(wl + w_wheel / 2, y_road))

            # Right side: wheel (straight lines)
            wr = vx + w_body - wheel_inset - w_wheel
            # Wheel rectangle
            painter.drawRect(int(wr), int(y_wheel_top), w_wheel, h_wheel)
            # Wheel center axle line (extended down to touch the road)
            painter.drawLine(QPointF(wr + w_wheel / 2, y_wheel_top),
                             QPointF(wr + w_wheel / 2, y_road))

            return wl, wr

        # Increase f space to 12% of available width
        f_prop = 0.12
        vx1 = start_x + available * f_prop
        wl1, wr1 = draw_vehicle(vx1)

        vx2 = end_x - available * f_prop - w_body
        wl2, wr2 = draw_vehicle(vx2)

        # ────────────────────────────────────
        # 6. f / g DIMENSION LINES (consistent arrowhead style)
        # ────────────────────────────────────
        painter.setPen(QPen(pen, 1))
        painter.setFont(font8)

        # f: from left boundary to left wheel of vehicle 1
        draw_dim_line(painter, start_x, wl1, y_fg, "f", label_below=False)
        # g: from right wheel of vehicle 1 to left wheel of vehicle 2
        draw_dim_line(painter, wr1 + w_wheel, wl2, y_fg, "g", label_below=False)
        # f: from right wheel of vehicle 2 to right boundary
        draw_dim_line(painter, wr2 + w_wheel, end_x, y_fg, "f", label_below=False)

        # ────────────────────────────────────
        # 7. w DIMENSION LINES (consistent arrowhead style)
        # ────────────────────────────────────
        wheels = [
            (wl1, wl1 + w_wheel),
            (wr1, wr1 + w_wheel),
            (wl2, wl2 + w_wheel),
            (wr2, wr2 + w_wheel),
        ]

        painter.setPen(QPen(pen, 1))
        painter.setFont(font8)

        for wx1, wx2 in wheels:
            # Vertical tick lines at wheel edges (extending up from w-dim line)
            tick_up = 18
            painter.drawLine(int(wx1), y_w_dim - tick_up,
                             int(wx1), y_w_dim)
            painter.drawLine(int(wx2), y_w_dim - tick_up,
                             int(wx2), y_w_dim)
            
            # Dimension line with outward arrowheads + overshoot extensions
            overshoot = 14
            # Continuous horizontal line across the wheel and extensions
            painter.drawLine(int(wx1 - overshoot), y_w_dim, int(wx2 + overshoot), y_w_dim)
            
            # Inward-pointing filled arrowheads at wheel edges
            draw_horizontal_arrow(painter, wx1, y_w_dim, 1, 10)   # right-pointing at left edge
            draw_horizontal_arrow(painter, wx2, y_w_dim, -1, 10)  # left-pointing at right edge
            
            # Label "w" below
            painter.drawText(QRectF(wx1, y_w_dim + 6, wx2 - wx1, 14),
                             Qt.AlignCenter, "w")
