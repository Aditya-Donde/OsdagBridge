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

class TrackedBogieDiagram(QWidget):
    def __init__(self, label_force, label_dist, parent=None):
        super().__init__(parent)
        self.label_force = label_force
        self.label_dist = label_dist
        self.setMinimumSize(280, 80)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background and border (gray rounded rect)
        rect = self.rect().adjusted(1, 1, -2, -2)
        painter.setPen(QPen(QColor("#a0a0a0"), 1))
        painter.setBrush(QBrush(QColor("#dfdfdf")))  # Light gray background
        painter.drawRoundedRect(rect, 8, 8)
        
        w, h = self.width(), self.height()
        
        # Left title text
        painter.setPen(QPen(QColor("#cc0000"), 1)) # Red text
        font = QFont("Arial", 9)
        font.setBold(True)
        painter.setFont(font)
        
        if "Tracked" in self.label_force or self.label_force == "P":
            title = "Tracked\nVehicles"
        else:
            title = "Bogie\nCars"
            
        painter.drawText(QRectF(15, 0, 70, h), Qt.AlignLeft | Qt.AlignVCenter, title)
        
        # Coordinates for arrows and lines
        start_x = 90
        end_x = w - 25
        arrow_start_y = 20
        arrow_end_y = 45
        line_y = 52 # dashed line between arrows
        dist_y = 65 # distance line
        
        # Force Labels (Black)
        painter.setPen(QPen(QColor("#000000"), 1))
        font_normal = QFont("Arial", 8)
        font_normal.setBold(False)
        painter.setFont(font_normal)
        painter.drawText(QRectF(start_x-15, 5, 30, 15), Qt.AlignCenter, self.label_force)
        painter.drawText(QRectF(end_x-15, 5, 30, 15), Qt.AlignCenter, self.label_force)
        
        # Arrows (Red)
        painter.setPen(QPen(QColor("#cc0000"), 1.5))
        draw_arrow_down(painter, start_x, arrow_start_y, arrow_end_y)
        draw_arrow_down(painter, end_x, arrow_start_y, arrow_end_y)
        
        # Horizontal dashed line between arrows
        painter.setPen(QPen(QColor("#000000"), 1, Qt.DashLine))
        painter.drawLine(start_x, line_y, end_x, line_y)
        
        # Distance line below (Solid black)
        painter.setPen(QPen(QColor("#000000"), 1))
        painter.drawLine(start_x, dist_y, end_x, dist_y)
        # Vertical ticks for distance
        painter.drawLine(start_x, line_y, start_x, dist_y + 5)
        painter.drawLine(end_x, line_y, end_x, dist_y + 5)
        
        # Distance Label
        painter.drawText(QRectF(start_x, dist_y + 2, end_x - start_x, 15), Qt.AlignCenter, self.label_dist)

class WheeledAxlesDiagram(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 90)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        
        # Fill white background
        painter.setBrush(QBrush(QColor("#ececec"))) # very light gray back box
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
        
        arrow_start_y = 15
        arrow_end_y = 40
        line_y = 47
        dist_y = 70  # moved farther from the dashed line
        
        painter.setFont(QFont("Arial", 8))
        
        for idx, (label, x, dist_label) in enumerate(axles):
            # Force label (black)
            painter.setPen(QPen(QColor("#000000"), 1))
            painter.drawText(QRectF(x-15, 0, 30, 15), Qt.AlignCenter, label)
            
            # Arrow (red)
            painter.setPen(QPen(QColor("#cc0000"), 1.5))
            draw_arrow_down(painter, x, arrow_start_y, arrow_end_y)
            
            painter.setPen(QPen(QColor("#000000"), 1))
            # Vertical tick down to dimension line
            painter.drawLine(x, line_y, x, dist_y + 5)
            
            if dist_label:
                next_x = axles[idx+1][1]
                painter.drawText(QRectF(x, dist_y + 2, next_x - x, 15), Qt.AlignCenter, dist_label)
                painter.drawLine(x, dist_y, next_x, dist_y)
                
                # Arrow points on dimension lines
                painter.drawLine(x, dist_y, x+4, dist_y-3)
                painter.drawLine(x, dist_y, x+4, dist_y+3)
                painter.drawLine(next_x, dist_y, next_x-4, dist_y-3)
                painter.drawLine(next_x, dist_y, next_x-4, dist_y+3)

        # Continuous dashed horizontal road line
        painter.setPen(QPen(QColor("#000000"), 1, Qt.DashLine))
        painter.drawLine(axles[0][1], line_y, axles[-1][1], line_y)
        
        # Dots logic for axle section and distance section
        painter.setPen(QPen(QColor("#cc0000"), 2))
        painter.drawText(QRectF( axles[2][1], 15, axles[3][1]-axles[2][1], 35 ), Qt.AlignCenter, ". . . . . . . .")
        
        # Continuity dots for dimension line
        painter.setPen(QPen(QColor("#000000"), 2))
        painter.drawText(QRectF( axles[2][1], dist_y - 12, axles[3][1]-axles[2][1], 25 ), Qt.AlignCenter, ". . . . . . . .")

class ClearCarriagewayWidthDiagram(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(380, 200)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())
        
        w, h = self.width(), self.height()
        
        painter.setPen(QPen(QColor("#000000"), 1))
        painter.setFont(QFont("Arial", 8))
        
        # Dimensions setup
        y_carr = h - 65
        y_dim = h - 25
        y_top_dim = 40
        
        # Left and right bounds
        start_x = w/2 - 120
        end_x = w/2 + 120
        
        # Title
        painter.setPen(QPen(QColor("#003399"), 1)) # Dark blue like Figma
        font_title = QFont("Arial", 8)
        font_title.setBold(True)
        painter.setFont(font_title)
        painter.drawText(QRectF(0, y_top_dim - 20, w, 20), Qt.AlignCenter, "CLEAR CARRIAGEWAY WIDTH")
        
        painter.setPen(QPen(QColor("#000000"), 1))
        painter.setFont(QFont("Arial", 8))
        
        # Top dimension line for carriageway
        # Vertical boundary gap with the road
        painter.drawLine(start_x, 30, start_x, y_carr - 15)
        painter.drawLine(end_x, 30, end_x, y_carr - 15)
        # Horizontal top dimension
        painter.drawLine(start_x, y_top_dim, end_x, y_top_dim)
        # Arrows for carriageway
        painter.drawLine(start_x, y_top_dim, start_x+8, y_top_dim-4)
        painter.drawLine(start_x, y_top_dim, start_x+8, y_top_dim+4)
        painter.drawLine(end_x, y_top_dim, end_x-8, y_top_dim-4)
        painter.drawLine(end_x, y_top_dim, end_x-8, y_top_dim+4)
        
        # Carriageway line
        painter.drawLine(start_x, y_carr, end_x, y_carr)
        # Ground hatching
        for gx in range(int(start_x), int(end_x), 10):
            painter.drawLine(gx, y_carr, gx-5, y_carr+5)
            
        # Left vehicle
        vx1 = start_x + 20
        painter.drawRect(vx1, y_carr - 40, 60, 30) # Body
        painter.drawRect(vx1 + 10, y_carr - 10, 10, 10) # Left wheel
        painter.drawRect(vx1 + 40, y_carr - 10, 10, 10) # Right wheel
        
        # Right vehicle
        vx2 = end_x - 80
        painter.drawRect(vx2, y_carr - 40, 60, 30) # Body
        painter.drawRect(vx2 + 10, y_carr - 10, 10, 10) # Left wheel
        painter.drawRect(vx2 + 40, y_carr - 10, 10, 10) # Right wheel
        
        # Bottom dimension line
        painter.setPen(QPen(QColor("#000000"), 1, Qt.DashLine))
        painter.drawLine(start_x, y_dim, end_x, y_dim)
        
        # Solid vertical ticks down to bottom dimension
        painter.setPen(QPen(QColor("#000000"), 1))
        
        # Correctly map ticks based on outer limits of the wheels
        t_wl1 = vx1 + 10
        t_wr1 = vx1 + 50
        t_wl2 = vx2 + 10
        t_wr2 = vx2 + 50
        
        # Vertical boundary guides from wheels towards the dashed line
        painter.setPen(QPen(QColor("#a0a0a0"), 1, Qt.DashLine))
        painter.drawLine(t_wl1, y_carr + 5, t_wl1, y_dim - 8)
        painter.drawLine(t_wr1, y_carr + 5, t_wr1, y_dim - 8)
        painter.drawLine(t_wl2, y_carr + 5, t_wl2, y_dim - 8)
        painter.drawLine(t_wr2, y_carr + 5, t_wr2, y_dim - 8)
        
        # Draw explicit end guides that match the road start/end
        painter.drawLine(start_x, y_carr + 5, start_x, y_dim - 8)
        painter.drawLine(end_x, y_carr + 5, end_x, y_dim - 8)
        
        painter.setPen(QPen(QColor("#000000"), 1))
        
        ticks = [
            (start_x, t_wl1, "f"),
            (t_wl1, t_wr1, "w"),
            (t_wr1, t_wl2, "g"),
            (t_wl2, t_wr2, "w"),
            (t_wr2, end_x, "f")
        ]
        
        font_dim = QFont("Arial", 8)
        font_dim.setBold(True)
        painter.setFont(font_dim)
        
        for t1, t2, lab in ticks:
            # Tick marks
            painter.setPen(QPen(QColor("#000000"), 1))
            painter.drawLine(t1, y_dim-6, t1, y_dim+6)
            painter.drawLine(t2, y_dim-6, t2, y_dim+6)
            
            # Label in the center of the span
            painter.setPen(QPen(QColor("#b06b00"), 1)) # Brown/orange text color matching figma
            painter.drawText(QRectF(t1, y_dim + 4, t2 - t1, 15), Qt.AlignCenter, lab)
            
            # Underline the w labels
            if lab == "w":
                painter.setPen(QPen(QColor("#808080"), 1))
                painter.drawLine(t1+3, y_dim+18, t2-3, y_dim+18)
