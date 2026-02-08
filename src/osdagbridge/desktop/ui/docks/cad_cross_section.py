"""
Cross-Section CAD Widget for OsdagBridge
Handles cross-sectional view rendering of bridge structures
Author: Arushi
"""

import math
from PySide6.QtWidgets import QWidget, QPushButton, QScrollArea
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QBrush, QPolygonF
from PySide6.QtGui import QPixmap
import random

class CrossSectionCADWidget(QWidget):
    """Widget for drawing bridge cross-section view"""
    
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)  # enable mouse tracking for hover
        self.concrete_brush = self.create_concrete_brush()
        # hover label regions: list of (QRectF, text, bg_color, text_color)
        self.hover_labels = []
        self.hovered_label_index = -1
        self.hovered_element = None  # Track hovered element for highlighting
        self.cross_section_hover_zones = []  # Store hover zones as (QRectF, element_type)
        
        # Scale factor for diagram size (1.0 = normal, <1.0 = smaller)
        self.scale_factor = 1.0
        
        # Zoom level for this widget
        self.zoom_level = 1.0
        
        # Setup zoom controls inside this widget (but not for previews inside scroll areas)
        # Will be called after widget is fully initialized
        self._zoom_controls_setup = False
        
        # bridge parameters with default values (all in mm)
        self.params = {
            'span_length': 35000,
            'num_girders': 4,
            'girder_spacing': 2750,
            'cross_bracing_spacing': 3500,
            'carriageway_width': 10500,
            'skew_angle': 0,
            'deck_thickness': 200,
            'footpath_width': 1500,
            'footpath_thickness': 200,
            'crash_barrier_width': 500,
            'railing_height': 1000,
            'footpath_config': 'both',
            'deck_overhang': 1000,
            'railing_width': 100,
            'median_present': False,
            'median_width': 1200,
        }
        
        # girder dimensions (mm)
        self.girder = {
            'depth': 500,
            'top_flange_width': 180,
            'top_flange_thickness': 17.2,
            'bottom_flange_width': 180,
            'bottom_flange_thickness': 17.2,
            'web_thickness': 10.2,
            # Legacy support for symmetric sections
            'flange_width': 180,
            'flange_thickness': 17.2,
        }
        
        # stiffener dimensions
        self.stiffener = {
            'width': 84.9,
            'height': 465.6,
        }

        self.girder_visual_scale = {
            'depth': 3.0,
            'flange_width': 3.75,
            'flange_thickness': 4.05,
            'web_thickness': 3.75,
        }
        
        # crash barrier dimensions (mm) 
        self.crash_barrier = {
            'width': 500,
            'height': 800,
            'base_width': 300,
        }
        
        # railing dimensions
        self.railing = {
            'post_dia': 50,
            'height': 1000,
            'rail_count': 3,
            'width': 100,
        }
        
        # Setup zoom controls (buttons will be hidden initially)
        self.setup_zoom_controls()
        
        # Track scroll area for fixed button positioning
        self.scroll_area = None
        
    def setup_zoom_controls(self):
        """Create zoom controls inside the widget"""
        self.zoom_in_btn = QPushButton("+", self)
        self.zoom_in_btn.setFixedSize(25, 25)
        self.zoom_in_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 200);
                border: 1px solid #999;
                border-radius: 3px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(144, 175, 19, 200);
                color: white;
            }
        """)
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.zoom_in_btn.hide()  # Hide initially, show in showEvent for non-previews
        
        self.zoom_out_btn = QPushButton("-", self)
        self.zoom_out_btn.setFixedSize(25, 25)
        self.zoom_out_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 200);
                border: 1px solid #999;
                border-radius: 3px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(144, 175, 19, 200);
                color: white;
            }
        """)
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.zoom_out_btn.hide()  # Hide initially
        
        self.zoom_reset_btn = QPushButton("Reset", self)
        self.zoom_reset_btn.setFixedSize(45, 25)
        self.zoom_reset_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 200);
                border: 1px solid #999;
                border-radius: 3px;
                font-size: 9px;
            }
            QPushButton:hover {
                background-color: rgba(144, 175, 19, 200);
                color: white;
            }
        """)
        self.zoom_reset_btn.clicked.connect(self.zoom_reset)
        self.zoom_reset_btn.hide()  # Hide initially
        
        # Set minimum size for visibility
        self.setMinimumSize(400, 300)
    
    def showEvent(self, event):
        """Setup zoom controls on first show, but not if inside a scroll area with small size"""
        super().showEvent(event)
        if not self._zoom_controls_setup:
            self._zoom_controls_setup = True
            # Check if this is a preview (has scroll area parent and small scale_factor)
            parent = self.parent()
            is_preview = self.scale_factor < 1.0
            # Only create zoom buttons if NOT a preview
            if not is_preview and hasattr(self, 'zoom_in_btn'):
                self.zoom_in_btn.show()
                self.zoom_out_btn.show()
                self.zoom_reset_btn.show()
    
    def zoom_in(self):
        self.zoom_level *= 1.1
        self._update_widget_size()
        self.update()
    
    def zoom_out(self):
        self.zoom_level /= 1.1
        self._update_widget_size()
        self.update()
    
    def zoom_reset(self):
        self.zoom_level = 1.0
        self._update_widget_size()
        self.update()
    
    def _update_widget_size(self):
        """Update widget size based on zoom level for proper scrolling"""
        base_width = 800
        base_height = 600
        # Add extra padding (20%) to ensure scrollbar reaches beyond content
        padding_factor = 1.2
        new_width = int(base_width * self.zoom_level * padding_factor)
        new_height = int(base_height * self.zoom_level)
        self.setMinimumSize(new_width, new_height)
        self.resize(new_width, new_height)
    
    def resizeEvent(self, event):
        """Position zoom controls in top-right corner"""
        super().resizeEvent(event)
        self._position_zoom_buttons()
    
    def _position_zoom_buttons(self):
        """Lock zoom buttons to fixed viewport position"""
        if not hasattr(self, 'zoom_in_btn'):
            return

        # Find scroll area once
        if self.scroll_area is None:
            parent = self.parent()
            while parent:
                if isinstance(parent, QScrollArea):
                    self.scroll_area = parent
                    break
                parent = parent.parent()

        if not self.scroll_area:
            return

        if self.scroll_area:
            viewport = self.scroll_area.viewport()
            self.zoom_in_btn.setParent(viewport)
            self.zoom_out_btn.setParent(viewport)
            self.zoom_reset_btn.setParent(viewport)


        margin = 10
        x = viewport.width() - 50
        y = margin

        self.zoom_in_btn.move(x, y)
        self.zoom_out_btn.move(x, y + 30)
        self.zoom_reset_btn.move(x, y + 60)

        self.zoom_in_btn.raise_()
        self.zoom_out_btn.raise_()
        self.zoom_reset_btn.raise_()

        
    def update_params(self, params):
        self.params.update(params)
        self.update()
    
    def mouseMoveEvent(self, event):
        """Handle mouse hover for both labels and structural elements"""
        pos = event.position() if hasattr(event, 'position') else event.pos()
        
        # Check label hover first
        new_hovered = -1
        for i, (rect, text, bg_color, text_color) in enumerate(self.hover_labels):
            if rect.contains(pos):
                new_hovered = i
                break
        
        if new_hovered != self.hovered_label_index:
            self.hovered_label_index = new_hovered
            self.update()
        
        # Check element hover
        new_hovered_element = None
        for rect, element_type in self.cross_section_hover_zones:
            if rect.contains(pos):
                new_hovered_element = element_type
                break
        
        if new_hovered_element != self.hovered_element:
            self.hovered_element = new_hovered_element
            self.update()

    def register_hover_label(self, x, y, text, bg_color, text_color, font_size=9):
        """lables for catching hover hovering"""
        font = QFont('Arial', font_size, QFont.Bold)
        metrics = self.fontMetrics()
        text_rect = metrics.boundingRect(text)
        
        padding = 5
        hover_rect = QRectF(x - padding, y - text_rect.height() - padding,
                            text_rect.width() + 2*padding + 20, text_rect.height() + 2*padding + 10)
        
        self.hover_labels.append((hover_rect, text, bg_color, text_color))
        return len(self.hover_labels) - 1

    def draw_hover_label_if_active(self, painter, label_index, x, y, text, bg_color, text_color, font_size=9):
        """label only if its being hovered"""
        if self.hovered_label_index == label_index:
            self.draw_text_with_background(painter, x, y, text, bg_color, text_color, font_size, True)
        
    def paintEvent(self, event):
        # clear hover labels and zones at start of each paint
        self.hover_labels = []
        self.cross_section_hover_zones = []
        
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.fillRect(self.rect(), QColor(255, 255, 255))
            self.draw_cross_section(painter)
        except Exception as e:
            print(" PAINT ERROR:", repr(e))
        finally:
            painter.end() 
    def draw_text_with_background(self, painter, x, y, text,
                              bg_color=QColor(255, 255, 255, 230), 
                              text_color=QColor(0, 0, 0), font_size=9, bold=False):

        font_weight = QFont.Bold if bold else QFont.Normal
        font = QFont('Arial', font_size, font_weight)
        painter.setFont(font)
        metrics = painter.fontMetrics()

        # breaking text in 2 to space be space
        lines = text.split("\n")

        line_height = metrics.height()
        max_width = max(metrics.boundingRect(line).width() for line in lines)
        total_height = line_height * len(lines)

        padding = 2

        # background rectangle
        bg_rect = QRectF(
            x - padding,
            y - total_height - padding,
            max_width + 2 * padding,
            total_height + 2 * padding
        )

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRect(bg_rect)

        # Draw each text line
        painter.setPen(QPen(text_color, 0.8))
        first_line_y = y - total_height + metrics.ascent()

        for i, line in enumerate(lines):
            painter.drawText(int(x), int(first_line_y + i * line_height), line)

    
    def draw_dimension_arrow(self, painter, x1, y1, x2, y2, text, horizontal=True, offset=0, text_offset=0, draw_extensions=True, extension_direction='down', extension_end_y=None):
        """dimension line with arrows and text with extension lines"""
        painter.setPen(QPen(QColor(0, 0, 0), 0.8))
        
        painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        
        ext_len = 6
        if horizontal:
            painter.drawLine(QPointF(x1, y1 - ext_len), QPointF(x1, y1 + ext_len))
            painter.drawLine(QPointF(x2, y2 - ext_len), QPointF(x2, y2 + ext_len))
        else:
            painter.drawLine(QPointF(x1 - ext_len, y1), QPointF(x1 + ext_len, y1))
            painter.drawLine(QPointF(x2 - ext_len, y2), QPointF(x2 + ext_len, y2))
        
        arrow_size = 4
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        
        if horizontal:
            left_arrow = [
                QPointF(x1, y1),
                QPointF(x1 + arrow_size, y1 - arrow_size/2),
                QPointF(x1 + arrow_size, y1 + arrow_size/2)
            ]
            painter.drawPolygon(QPolygonF(left_arrow))
            
            right_arrow = [
                QPointF(x2, y2),
                QPointF(x2 - arrow_size, y2 - arrow_size/2),
                QPointF(x2 - arrow_size, y2 + arrow_size/2)
            ]
            painter.drawPolygon(QPolygonF(right_arrow))
            
            if draw_extensions:
                painter.setPen(QPen(QColor(100, 100, 100), 0.8, Qt.DotLine))
                
                if extension_end_y is not None:
                    # Draw extension lines to specified y coordinate
                    if extension_direction == 'up':
                        painter.drawLine(QPointF(x1, y1), QPointF(x1, extension_end_y))
                        painter.drawLine(QPointF(x2, y2), QPointF(x2, extension_end_y))
                    else:
                        painter.drawLine(QPointF(x1, y1), QPointF(x1, extension_end_y))
                        painter.drawLine(QPointF(x2, y2), QPointF(x2, extension_end_y))
                else:
                    extension_length = 40
                    if extension_direction == 'up':
                        painter.drawLine(QPointF(x1, y1), QPointF(x1, y1 - extension_length))
                        painter.drawLine(QPointF(x2, y2), QPointF(x2, y2 - extension_length))
                    else:
                        painter.drawLine(QPointF(x1, y1), QPointF(x1, y1 + extension_length))
                        painter.drawLine(QPointF(x2, y2), QPointF(x2, y2 + extension_length))
                
                painter.setPen(QPen(QColor(0, 0, 0), 1.1))
            
            text_x = (x1 + x2) / 2
            if extension_direction == 'down':
            # Dimension line is ABOVE the figure -> text BELOW line
                 text_y = y1 + 18 + text_offset

            else:
            # Dimension line is BELOW the figure -> text ABOVE line
                 text_y = y1 - 6 + text_offset
            
            font = QFont('Arial', 9, QFont.Bold)
            metrics = painter.fontMetrics()
            text_width = metrics.boundingRect(text).width()
            
            self.draw_text_with_background(painter, text_x - text_width/2, text_y, text, 
                                        QColor(255, 255, 255, 255), QColor(0, 0, 0), 9, True)
        else:
            top_arrow = [
                QPointF(x1, y1),
                QPointF(x1 - arrow_size/2, y1 + arrow_size),
                QPointF(x1 + arrow_size/2, y1 + arrow_size)
            ]
            painter.drawPolygon(QPolygonF(top_arrow))
            
            bottom_arrow = [
                QPointF(x2, y2),
                QPointF(x2 - arrow_size/2, y2 - arrow_size),
                QPointF(x2 + arrow_size/2, y2 - arrow_size)
            ]
            painter.drawPolygon(QPolygonF(bottom_arrow))
            
            if draw_extensions:
                painter.setPen(QPen(QColor(100, 100, 100), 0.8, Qt.DotLine))
                extension_length = 20
                
                if extension_direction == 'left':
                    painter.drawLine(QPointF(x1, y1), QPointF(x1 - extension_length, y1))
                    painter.drawLine(QPointF(x2, y2), QPointF(x2 - extension_length, y2))
                else:
                    painter.drawLine(QPointF(x1, y1), QPointF(x1 + extension_length, y1))
                    painter.drawLine(QPointF(x2, y2), QPointF(x2 + extension_length, y2))
                
                painter.setPen(QPen(QColor(0, 0, 0), 1.1))
            
            text_x = x1 + (12 if offset >= 0 else -45) + text_offset
            text_y = (y1 + y2) / 2 + 3
            
            self.draw_text_with_background(painter, text_x, text_y, text,
                                        QColor(255, 255, 255, 255), QColor(0, 0, 0), 9, True)
    
    def draw_dimension_arrow_text_outside(self, painter, x1, y1, x2, y2, text, horizontal=True, 
                                          text_side='right', text_offset=15):
        """Dimension line with arrows"""
        painter.setPen(QPen(QColor(0, 0, 0), 0.8))
        
        painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        
        ext_len = 6
        arrow_size = 4
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        
        if horizontal:
            painter.drawLine(QPointF(x1, y1 - ext_len), QPointF(x1, y1 + ext_len))
            painter.drawLine(QPointF(x2, y2 - ext_len), QPointF(x2, y2 + ext_len))
            
            left_arrow = [
                QPointF(x1, y1),
                QPointF(x1 + arrow_size, y1 - arrow_size/2),
                QPointF(x1 + arrow_size, y1 + arrow_size/2)
            ]
            painter.drawPolygon(QPolygonF(left_arrow))
            
            right_arrow = [
                QPointF(x2, y2),
                QPointF(x2 - arrow_size, y2 - arrow_size/2),
                QPointF(x2 - arrow_size, y2 + arrow_size/2)
            ]
            painter.drawPolygon(QPolygonF(right_arrow))
            
            if text_side == 'top':
                text_x = (x1 + x2) / 2
                text_y = y1 - text_offset
            else:
                text_x = (x1 + x2) / 2
                text_y = y1 + text_offset + 10
                
            font = QFont('Arial', 9, QFont.Bold)
            painter.setFont(font)
            metrics = painter.fontMetrics()
            text_width = metrics.boundingRect(text).width()
            
            self.draw_text_with_background(painter, text_x - text_width/2, text_y, text, 
                                        QColor(255, 255, 255, 255), QColor(0, 0, 0), 9, True)
        else:
            painter.drawLine(QPointF(x1 - ext_len, y1), QPointF(x1 + ext_len, y1))
            painter.drawLine(QPointF(x2 - ext_len, y2), QPointF(x2 + ext_len, y2))
            
            top_arrow = [
                QPointF(x1, y1),
                QPointF(x1 - arrow_size/2, y1 + arrow_size),
                QPointF(x1 + arrow_size/2, y1 + arrow_size)
            ]
            painter.drawPolygon(QPolygonF(top_arrow))
            
            bottom_arrow = [
                QPointF(x2, y2),
                QPointF(x2 - arrow_size/2, y2 - arrow_size),
                QPointF(x2 + arrow_size/2, y2 - arrow_size)
            ]
            painter.drawPolygon(QPolygonF(bottom_arrow))
            
            text_y = (y1 + y2) / 2 + 3
            if text_side == 'left':
                text_x = x1 - text_offset - 35
            else:
                text_x = x1 + text_offset
            
            self.draw_text_with_background(painter, text_x, text_y, text,
                                        QColor(255, 255, 255, 255), QColor(0, 0, 0), 9, True)
        
    def draw_leader_arrow(self, painter, from_x, from_y, to_x, to_y, text, bg_color=QColor(255, 255, 255, 250), text_color=QColor(0, 0, 0)):
        """a leader line with arrow pointing to component"""
        painter.setPen(QPen(QColor(0, 0, 0), 1.0))
        painter.drawLine(QPointF(from_x, from_y), QPointF(to_x, to_y))
        
        arrow_size = 3
        angle = math.atan2(to_y - from_y, to_x - from_x)
        
        arrow_points = [
            QPointF(to_x, to_y),
            QPointF(to_x - arrow_size * math.cos(angle - math.pi/6), 
                   to_y - arrow_size * math.sin(angle - math.pi/6)),
            QPointF(to_x - arrow_size * math.cos(angle + math.pi/6), 
                   to_y - arrow_size * math.sin(angle + math.pi/6))
        ]
        
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        painter.drawPolygon(QPolygonF(arrow_points))
        
        self.draw_text_with_background(painter, from_x - 5, from_y - 5, text, bg_color, text_color, 9, True)
    
    def draw_clean_leader_line(self, painter, target_x, target_y, label_x, label_y, text, 
                                text_color=QColor(0, 0, 0), line_color=QColor(100, 100, 100)):
        """draw a clean leader line from target point to label with dotted line"""
        # Draw dotted line from target to label
        pen = QPen(line_color, 1.0, Qt.DotLine)
        painter.setPen(pen)
        painter.drawLine(QPointF(target_x, target_y), QPointF(label_x, label_y))
        
        # Draw small circle at target point
        painter.setPen(QPen(line_color, 1.5))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(target_x, target_y), 3, 3)
        
        # Draw text at label position
        font = QFont('Arial', 9, QFont.Bold)
        painter.setFont(font)
        metrics = painter.fontMetrics()
        text_width = metrics.boundingRect(text).width()
        text_height = metrics.height()
        
        # Determine text alignment based on relative position
        if label_x > target_x:
            text_x = label_x + 5
        else:
            text_x = label_x - text_width - 5
        
        text_y = label_y + text_height / 4
        
        # Draw text with background
        self.draw_text_with_background(painter, text_x, text_y, text,
                                       QColor(255, 255, 255, 255), text_color, 9, True)
    
    def compute_deck_total_width(self):
        """Compute total deck width including median if present"""
        carriageway = self.params.get('carriageway_width', 10500)
        crash_barrier = self.params.get('crash_barrier_width', 500)
        footpath_width = self.params.get('footpath_width', 1500)
        fp_config = self.params.get('footpath_config', 'both')
        median_present = self.params.get('median_present', False)
        median_width = self.params.get('median_width', 1200)
        
        if fp_config == 'both':
            num_fp = 2
        elif fp_config in ['left', 'right']:
            num_fp = 1
        else:
            num_fp = 0
        
        # If median is present, we have full carriageway on each side
        if median_present:
            deck_total = (carriageway * 2 +  # Full carriageway on each side
                          median_width +
                          2 * crash_barrier + 
                          num_fp * footpath_width)
        else:
            deck_total = (carriageway + 
                          2 * crash_barrier + 
                          num_fp * footpath_width)
        
        return deck_total, num_fp
    
    def create_concrete_brush(self):
        """Concrete hatch pattern brush (aggregate look)"""
        size = 25  # pattern tile size
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)

        p = QPainter(pixmap)
        p.setRenderHint(QPainter.Antialiasing)

        # light grey base (optional)
        p.fillRect(0, 0, size, size, QColor(245, 245, 245))

        # dots (sand)
        p.setPen(QPen(QColor(150, 150, 150), 1))
        for i in range(35):
            x = random.randint(0, size - 1)
            y = random.randint(0, size - 1)
            p.drawPoint(x, y)
        
        #Angular stones
        p.setPen(QPen(QColor(130, 130, 130), 1.2))
        for _ in range(6):
            cx = random.randint(6, size - 6)
            cy = random.randint(6, size - 6)

            poly = QPolygonF()
            sides = random.randint(3, 5)
            base_angle = random.uniform(0, 2 * math.pi)

            for _ in range(sides):
                angle = base_angle + random.uniform(-0.8, 0.8)
                radius = random.uniform(3, 7)
                poly.append(
                    QPointF(
                        cx + radius * math.cos(angle),
                        cy + radius * math.sin(angle)
                    )
                )

            p.drawPolygon(poly)

        p.end()
        return QBrush(pixmap)

    def draw_median_crash_barriers(self, painter, median_start_x, median_end_x, deck_top_y, scale, median_color):
        """Draw two crash barriers for median, facing outward"""
        painter.setBrush(QBrush(median_color))
        MEDIAN_GREY = QColor(221, 221, 221)
        CONCRETE_COLOR = QColor(225, 225, 225)

        
        # Dimensions
        TOTAL_HEIGHT = 900.0
        TOP_WIDTH = 175.0
        BOTTOM_WIDTH = 350.0
        BASE_VERTICAL = 100.0
        
        h = TOTAL_HEIGHT * scale
        top_w = TOP_WIDTH * scale
        bottom_w = BOTTOM_WIDTH * scale
        base_v = BASE_VERTICAL * scale
        
        median_width_px = median_end_x - median_start_x
        
        # Check if barriers fit
        if bottom_w * 2 > median_width_px:
            fit_scale = median_width_px / (bottom_w * 2) * 0.9
            h *= fit_scale
            top_w *= fit_scale
            bottom_w *= fit_scale
            base_v *= fit_scale
        
        gap = median_width_px - 2 * bottom_w
        if gap < 5:
            gap = 5
            bottom_w = (median_width_px - gap) / 2
            ratio = bottom_w / (BOTTOM_WIDTH * scale)
            h *= ratio
            top_w *= ratio
            base_v *= ratio
        
        y = deck_top_y
        y_base_top = y - base_v
        y_mid = y - (350 * scale * (h / (TOTAL_HEIGHT * scale)))  # proportional
        y_top = y - h
        
        # Offsets 
        scale_ratio = bottom_w / (BOTTOM_WIDTH * scale) if BOTTOM_WIDTH * scale > 0 else 1
        right_at_mid = 250 * scale * scale_ratio
        left_at_top = 50 * scale * scale_ratio
        right_at_top = 225 * scale * scale_ratio
        
        # LEFT barrier - front faces LEFT (toward left carriageway)
        # This is the mirrored version
        x_left = median_start_x
        
        points_left = [
            QPointF(x_left, y),                                      # bottom-left
            QPointF(x_left + bottom_w, y),                           # bottom-right
            QPointF(x_left + bottom_w, y_base_top),                  # right after base
            QPointF(x_left + bottom_w - left_at_top, y_top),         # top-right
            QPointF(x_left + bottom_w - right_at_top, y_top),        # top-left
            QPointF(x_left + bottom_w - right_at_mid, y_mid),        # left at middle
            QPointF(x_left, y_base_top),                             # left after base
        ]
        
        painter.setBrush(QBrush(MEDIAN_GREY))
        painter.setPen(QPen(QColor(0, 0, 0), max(1.5, scale * 1.5)))
        painter.drawPolygon(QPolygonF(points_left))
        
        # RIGHT barrier - front faces RIGHT (toward right carriageway)
        # This is the original orientation
        x_right = median_end_x - bottom_w
        
        points_right = [
            QPointF(x_right, y),                           # bottom-left
            QPointF(x_right + bottom_w, y),                # bottom-right
            QPointF(x_right + bottom_w, y_base_top),       # right after base
            QPointF(x_right + right_at_mid, y_mid),        # right at middle
            QPointF(x_right + right_at_top, y_top),        # top-right
            QPointF(x_right + left_at_top, y_top),         # top-left
            QPointF(x_right, y_base_top),                  # left after base
        ]
        
        painter.setBrush(QBrush(MEDIAN_GREY))
        painter.setPen(QPen(QColor(0, 0, 0), max(1.5, scale * 1.5)))
        painter.drawPolygon(QPolygonF(points_right))

    def draw_cross_section(self, painter):
        """Draw cross-section with median support and hover highlighting"""
        
        GIRDER_COLOR = QColor(179, 180, 160)           # girder → dark olive-grey
        STIFFENER_COLOR = QColor(79, 78, 70)         # stiffener → very dark olive
        CROSS_BRACING_COLOR = QColor(235, 236, 211)     # cross bracing → light olive
        END_DIAPHRAGM_COLOR = QColor(134, 134, 100)
        BARRIER_GREY = QColor(221, 221, 221)  # slightly dark grey
        RAILING_GREY = QColor(221, 221, 221)
        MEDIAN_GREY = QColor(221, 221, 221) 
        CONCRETE_COLOR = QColor(225, 225, 225)
        
        
        # Use base canvas dimensions scaled by zoom for proper scrolling
        width = self.width()
        height = self.height()

        fp_config = self.params.get('footpath_config', 'both')
        left_fp_width = self.params['footpath_width'] if fp_config in ['left', 'both'] else 0
        right_fp_width = self.params['footpath_width'] if fp_config in ['right', 'both'] else 0

        total_deck_width, num_fp = self.compute_deck_total_width()

        # Reduced margins for better space utilization
        margin = 80
        scale = min((width - 2*margin) / total_deck_width,
                (height - 2*margin - 80) / (self.girder['depth'] * self.girder_visual_scale['depth'] +
                                                self.params['deck_thickness'] +
                                                self.params['footpath_thickness'] + 1500))
        
        # Apply scale factor for size adjustment (zoom_level already applied to width/height)
        scale = scale * self.scale_factor
        
        DIM_OFFSET = 510 * scale
        DIM_OFFSET_SMALL = 588 * scale

        CENTER_OFFSET_X = 80  # try 40–80 depending on look
        center_x = width / 2 + CENTER_OFFSET_X
        # Position bridge in the center vertically
        total_bridge_height = (self.girder['depth'] * scale * self.girder_visual_scale['depth'] +
                              self.params['deck_thickness'] * scale +
                              self.params['footpath_thickness'] * scale +
                              self.crash_barrier['height'] * scale + 
                              self.railing['height'] * scale)
        
        # Ensure proper positioning - use margin from top instead of centering for small heights
        top_margin = 40
        if height < 300:  # For small heights (like Additional Inputs), position from top
            base_y = height - top_margin
        else:
            base_y = (height + total_bridge_height) / 2 - 30

        girder_depth_visual = self.girder['depth'] * scale * self.girder_visual_scale['depth']
        girder_top_y = base_y - girder_depth_visual
        deck_thick_px = self.params['deck_thickness'] * scale
        fp_thick_px = self.params['footpath_thickness'] * scale
        deck_bottom_y = girder_top_y
        deck_top_y = deck_bottom_y - deck_thick_px
        fp_bottom_y = deck_bottom_y
        fp_top_y = fp_bottom_y - fp_thick_px

        deck_start_x = center_x - (total_deck_width * scale) / 2
        deck_left_x = deck_start_x
        deck_right_x = deck_start_x + total_deck_width * scale
        
        # Calculate all widths in pixels
        crash_barrier_width_px = self.params['crash_barrier_width'] * scale
        left_fp_width_px = left_fp_width * scale
        right_fp_width_px = right_fp_width * scale
        
        # LAYOUT FROM LEFT TO RIGHT
        # 1. Left footpath starts at deck_left_x
        left_fp_x = deck_left_x
        
        # 2. Left crash barrier starts after left footpath
        left_barrier_x = left_fp_x + left_fp_width_px
        left_barrier_end_x = left_barrier_x + crash_barrier_width_px
        
        # 3. Right footpath ends at deck_right_x
        right_fp_x = deck_right_x - right_fp_width_px
        
        # 4. Right crash barrier ENDS where right footpath STARTS
        right_barrier_end_x = right_fp_x
        right_barrier_x = right_barrier_end_x - crash_barrier_width_px
        
        # 5. Carriageway
        carriageway_start_x = left_barrier_end_x
        carriageway_end_x = right_barrier_x
        
        median_present = self.params.get('median_present', False)
        median_width = self.params.get('median_width', 1200)
        
        if median_present:
            cw_full = self.params['carriageway_width']
            cw_width_px = cw_full * scale
            median_width_px = median_width * scale
            
            cw1_start_x = left_barrier_end_x
            cw1_end_x = cw1_start_x + cw_width_px
            median_start_x = cw1_end_x
            median_end_x = median_start_x + median_width_px
            cw2_start_x = median_end_x
            cw2_end_x = cw2_start_x + cw_width_px
            
            carriageway_start_x = cw1_start_x
            carriageway_end_x = cw2_end_x
        else:
            median_start_x = None
            median_end_x = None

        n = max(1, int(self.params['num_girders']))
        deck_overhang_px = self.params.get('deck_overhang', 1000) * scale
        
        if n > 1:
            first_girder_x = deck_left_x + deck_overhang_px
            last_girder_x = deck_right_x - deck_overhang_px
            available_for_spacing = last_girder_x - first_girder_x
            actual_spacing_px = available_for_spacing / (n - 1) if n > 1 else 0
            positions = [first_girder_x + i * actual_spacing_px for i in range(n)]
        else:
            positions = [center_x]

        flange_half_px = (self.girder['flange_width'] * scale * self.girder_visual_scale['flange_width']) / 2.0
        min_allowed_x = deck_left_x + flange_half_px + 1
        max_allowed_x = deck_right_x - flange_half_px - 1
        positions = [max(min_allowed_x, min(max_allowed_x, p)) for p in positions]

        RAILING_OUTER_WIDTH_MM = 375
        railing_outer_width_px = RAILING_OUTER_WIDTH_MM * scale
        railing_width_px = railing_outer_width_px

        # Draw deck slab
        deck_slab_left = left_barrier_x
        deck_slab_right = right_barrier_end_x
        
        # Check if deck is hovered (visible brightness)
        deck_hovered = (self.hovered_element == 'deck')
        deck_color = QColor(240, 240, 240) if deck_hovered else CONCRETE_COLOR
        
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(QRectF(deck_slab_left, deck_top_y,
                            deck_slab_right - deck_slab_left, deck_thick_px))
        
        # ---- DRAW FULL DECK SLAB (ONCE) ----
        painter.setBrush(self.concrete_brush)
        painter.setPen(Qt.NoPen)
        painter.drawRect(QRectF(
            deck_slab_left,
            deck_top_y,
            deck_slab_right - deck_slab_left,
            deck_thick_px
        ))


        if median_present:
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(QRectF(deck_slab_left, deck_top_y,
                                    deck_slab_right - deck_slab_left, deck_thick_px))

        else:
            painter.setBrush(self.concrete_brush)
            painter.setPen(Qt.NoPen)
            painter.drawRect(QRectF(carriageway_start_x, deck_top_y,
                                carriageway_end_x - carriageway_start_x, deck_thick_px))
        
        # Register hover zone for deck
        deck_hover_rect = QRectF(deck_slab_left, deck_top_y,
                                deck_slab_right - deck_slab_left, deck_thick_px)
        self.cross_section_hover_zones.append((deck_hover_rect, 'deck'))

        # Crash barrier deck zones
        painter.setBrush(self.concrete_brush)


        painter.drawRect(QRectF(left_barrier_x, deck_top_y,
                                crash_barrier_width_px, deck_thick_px))
        painter.drawRect(QRectF(right_barrier_x, deck_top_y,
                                crash_barrier_width_px, deck_thick_px))

        # footpath to deck connecting line
        dashed_pen = QPen(QColor(0, 0, 0), 1.5, Qt.DashLine)
        dashed_pen.setDashPattern([2, 2])  # Tiny dashes

        # making the line dashed
        if fp_config in ['left', 'both'] and left_fp_width > 0:
            # Draw footpath fill only (no border)
            painter.setBrush(self.concrete_brush)

            painter.setPen(Qt.NoPen)
            painter.drawRect(QRectF(left_fp_x, fp_top_y,
                                left_fp_width_px, fp_thick_px))
            
            # Draw horizontal edges as solid
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            painter.setBrush(Qt.NoBrush)
            # Top edge
            painter.drawLine(QPointF(left_fp_x, fp_top_y), 
                            QPointF(left_fp_x + left_fp_width_px, fp_top_y))
            # Bottom edge
            painter.drawLine(QPointF(left_fp_x, fp_top_y + fp_thick_px), 
                            QPointF(left_fp_x + left_fp_width_px, fp_top_y + fp_thick_px))
            
            # Left edge 
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            painter.drawLine(QPointF(left_fp_x, fp_top_y), 
                            QPointF(left_fp_x, fp_top_y + fp_thick_px))
            
            # Right edge
            painter.setPen(dashed_pen)
            painter.drawLine(QPointF(left_fp_x + left_fp_width_px, fp_top_y), 
                            QPointF(left_fp_x + left_fp_width_px, fp_top_y + fp_thick_px))

        if fp_config in ['right', 'both'] and right_fp_width > 0:
            # Draw footpath fill
            painter.setBrush(self.concrete_brush)
            painter.setPen(Qt.NoPen)
            painter.drawRect(QRectF(right_fp_x, fp_top_y,
                                right_fp_width_px, fp_thick_px))
            
            # Draw horizontal edges as solid
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            painter.setBrush(Qt.NoBrush)
            # Top edge
            painter.drawLine(QPointF(right_fp_x, fp_top_y), 
                            QPointF(right_fp_x + right_fp_width_px, fp_top_y))
            # Bottom edge
            painter.drawLine(QPointF(right_fp_x, fp_top_y + fp_thick_px), 
                            QPointF(right_fp_x + right_fp_width_px, fp_top_y + fp_thick_px))
            
            # Left edge (inner edge connecting to deck) - DASHED
            painter.setPen(dashed_pen)
            painter.drawLine(QPointF(right_fp_x, fp_top_y), 
                            QPointF(right_fp_x, fp_top_y + fp_thick_px))
            
            # Right edge (outer edge where railing sits) - SOLID
            painter.setPen(QPen(QColor(0, 0, 0), 2))
            painter.drawLine(QPointF(right_fp_x + right_fp_width_px, fp_top_y), 
                            QPointF(right_fp_x + right_fp_width_px, fp_top_y + fp_thick_px))
        # Draw crash barriers
        cb_y = deck_top_y
        # Left barrier: x is where it STARTS (left edge)
        self.draw_crash_barrier(painter, left_barrier_x, cb_y, scale, side='left')
        # Right barrier: x is where it ENDS (right edge) = right_barrier_end_x
        self.draw_crash_barrier(painter, right_barrier_end_x, cb_y, scale, side='right')
        
        if median_present:
            self.draw_median_crash_barriers(painter, median_start_x, median_end_x, deck_top_y, scale, MEDIAN_GREY)

        # Draw the main deck bottom line solid (only the deck slab portion)
        painter.setPen(QPen(QColor(0, 0, 0), 1.5))
        painter.drawLine(QPointF(deck_slab_left, deck_bottom_y), 
                        QPointF(deck_slab_right, deck_bottom_y))

        # Draw dashed lines for footpath area bottom and vertical connections
        # Left footpath area
        if fp_config in ['left', 'both'] and left_fp_width > 0:
            painter.setPen(dashed_pen)
            # Bottom line under footpath area (dashed)
            painter.drawLine(QPointF(deck_left_x, deck_bottom_y), 
                            QPointF(deck_slab_left, deck_bottom_y))
            # Outer vertical line from footpath bottom to deck bottom level (dashed)
            painter.drawLine(QPointF(deck_left_x, fp_top_y + fp_thick_px), 
                            QPointF(deck_left_x, deck_bottom_y))

        # Right footpath area
        if fp_config in ['right', 'both'] and right_fp_width > 0:
            painter.setPen(dashed_pen)
            # Bottom line under footpath area (dashed)
            painter.drawLine(QPointF(deck_slab_right, deck_bottom_y), 
                            QPointF(deck_right_x, deck_bottom_y))
            # Outer vertical line from footpath bottom to deck bottom level (dashed)
            painter.drawLine(QPointF(deck_right_x, fp_top_y + fp_thick_px), 
                            QPointF(deck_right_x, deck_bottom_y))

        # Draw girders and stiffeners
        for girder_x in positions:
            self.draw_i_section(painter, girder_x, base_y, scale, GIRDER_COLOR)
            self.draw_stiffeners(painter, girder_x, base_y, scale, STIFFENER_COLOR)
            
        # -------- 4.d CL OF BEARING (DASHED BLACK) --------
        painter.setPen(QPen(QColor(0, 0, 0), 1.0, Qt.DashLine))
        painter.setBrush(Qt.NoBrush)

        for girder_x in positions:
            painter.drawLine(
                QPointF(girder_x, base_y),
                QPointF(girder_x, deck_bottom_y)
            )
            
            # ---- Flange thickness (same as I-section) ----
            if 'top_flange_thickness' in self.girder and 'bottom_flange_thickness' in self.girder:
                tf_top = self.girder['top_flange_thickness'] * scale * self.girder_visual_scale['flange_thickness']
                tf_bottom = self.girder['bottom_flange_thickness'] * scale * self.girder_visual_scale['flange_thickness']
            else:
                tf_top = tf_bottom = self.girder['flange_thickness'] * scale * self.girder_visual_scale['flange_thickness']



        # Draw cross bracing between girders (AFTER girders so it's on top)
        if n > 1:
            # Get bottom flange thickness to calculate actual girder bottom
            if 'bottom_flange_thickness' in self.girder:
                bf_thickness = self.girder['bottom_flange_thickness'] * scale * self.girder_visual_scale['flange_thickness']
            else:
                bf_thickness = self.girder['flange_thickness'] * scale * self.girder_visual_scale['flange_thickness']
            
            girder_top_edge = base_y - girder_depth_visual
            # Correct bottom edge: above base_y by bottom flange thickness
            girder_bottom_edge = base_y - bf_thickness
            
            # Mid of top & bottom flange (REFERENCE POINTS)
            top_flange_mid_y = girder_top_edge + tf_top / 2
            bottom_flange_mid_y = girder_bottom_edge - tf_bottom / 2

            
            
            for i in range(n - 1):
                x1 = positions[i]
                x2 = positions[i + 1]
                
                # Draw cross bracing lines
                line_spacing = 3
                painter.setBrush(Qt.NoBrush)
                painter.setPen(QPen(CROSS_BRACING_COLOR, 1.0))
                
                dx = x2 - x1
                dy = girder_bottom_edge - girder_top_edge
                length = math.sqrt(dx * dx + dy * dy)
                
                if length > 0:
                    perp_x = -dy / length
                    perp_y = dx / length

                    thickness = 3.0              # visual thickness of bracing
                    half_t = thickness / 2

                    off_x = perp_x * half_t
                    off_y = perp_y * half_t


                    # CROSS BRACING 1 (\ direction)

                    p1 = QPointF(x1 + off_x, top_flange_mid_y + off_y)
                    p2 = QPointF(x2 + off_x, bottom_flange_mid_y + off_y)
                    p3 = QPointF(x2 - off_x, bottom_flange_mid_y - off_y)
                    p4 = QPointF(x1 - off_x, top_flange_mid_y - off_y)

                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QBrush(CROSS_BRACING_COLOR))
                    painter.drawPolygon(QPolygonF([p1, p2, p3, p4]))

                    # DARK BOUNDARY LINES
                    painter.setPen(QPen(CROSS_BRACING_COLOR.darker(220), 1.5))
                    painter.drawLine(p1, p2)
                    painter.drawLine(p4, p3)

                    # CROSS BRACING 2 (/ direction)

                    p1 = QPointF(x1 + off_x, bottom_flange_mid_y + off_y)
                    p2 = QPointF(x2 + off_x, top_flange_mid_y + off_y)
                    p3 = QPointF(x2 - off_x, top_flange_mid_y - off_y)
                    p4 = QPointF(x1 - off_x, bottom_flange_mid_y - off_y)

                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QBrush(CROSS_BRACING_COLOR))
                    painter.drawPolygon(QPolygonF([p1, p2, p3, p4]))

                    painter.setPen(QPen(CROSS_BRACING_COLOR.darker(220), 1.5))
                    painter.drawLine(p1, p2)
                    painter.drawLine(p4, p3)

        # Draw railings
        left_railing_rect = None
        right_railing_rect = None

        if fp_config in ['left', 'both'] and left_fp_width > 0:
            railing_x = deck_left_x
            left_railing_rect = self.draw_railing_post_fixed(painter, railing_x, fp_top_y, scale, "left")
            
        if fp_config in ['right', 'both'] and right_fp_width > 0:
            railing_x = deck_right_x - railing_outer_width_px
            right_railing_rect = self.draw_railing_post_fixed(painter, railing_x, fp_top_y, scale, "right")

        # Add dimensions
        self.add_professional_cross_section_dimensions(
            painter, deck_left_x, deck_right_x, carriageway_start_x, carriageway_end_x,
            left_barrier_x, right_barrier_x, deck_top_y, deck_bottom_y, fp_top_y,
            base_y, scale, positions, n, fp_config, left_fp_width, right_fp_width,
            left_fp_x, right_fp_x, railing_width_px, girder_depth_visual,
            median_present, median_start_x, median_end_x, median_width,
            crash_barrier_width_px, left_barrier_end_x, right_barrier_end_x, DIM_OFFSET, DIM_OFFSET_SMALL
        )

        # Add hover labels
        self.add_cross_section_hover_labels(
            painter, carriageway_start_x, carriageway_end_x, left_barrier_x, right_barrier_x,
            deck_top_y, deck_bottom_y, deck_thick_px, positions, base_y, scale, n, fp_config,
            deck_left_x, deck_right_x, left_fp_width, right_fp_width, fp_top_y, fp_thick_px,
            left_fp_x, right_fp_x, left_railing_rect, right_railing_rect, railing_width_px,
            median_present, median_start_x, median_end_x, median_width, deck_slab_left, deck_slab_right,
            crash_barrier_width_px, left_barrier_end_x, right_barrier_end_x
        )



    def draw_railing_post_fixed(self, painter, x, y, scale, side):
        """Draw RCC railing with exact dimensions:
        - Height: 1100 mm
        - Outer width: 375 mm
        - Inner spacing: 275 mm
        - Base thickness: 100 mm
        """
        RAILING_HEIGHT_MM = 1100
        OUTER_WIDTH_MM = 375
        INNER_SPACING_MM = 275
        BASE_THICKNESS_MM = 100
        
        wall_thickness_mm = (OUTER_WIDTH_MM - INNER_SPACING_MM) / 2
        
        total_h = RAILING_HEIGHT_MM * scale
        outer_w = max(4, OUTER_WIDTH_MM * scale)
        inner_w = max(2, INNER_SPACING_MM * scale)
        base_h = max(3, BASE_THICKNESS_MM * scale)
        wall_t = max(1, wall_thickness_mm * scale)
        
        post_h = total_h - base_h
        
        rect_x = x
        base_bottom_y = y
        base_top_y = y - base_h
        post_top_y = y - total_h
        
        corner_radius = min(outer_w * 0.05, 4)
        
        painter.setBrush(QBrush(QColor(126,126,126) ))

        painter.setPen(QPen(QColor(34, 34, 34), max(1.5, scale * 2)))
        base_rect = QRectF(rect_x, base_top_y, outer_w, base_h)
        painter.drawRect(base_rect)
        
        painter.setBrush(QBrush(QColor(126,126,126) ))

        painter.setPen(QPen(QColor(34, 34, 34), max(1.5, scale * 2)))
        post_rect = QRectF(rect_x, post_top_y, outer_w, post_h)
        painter.drawRoundedRect(post_rect, corner_radius, corner_radius)
        
        inner_x = rect_x + wall_t
        inner_top_margin = post_h * 0.08
        inner_bottom_margin = post_h * 0.05
        inner_height = post_h - inner_top_margin - inner_bottom_margin
        
        if inner_w > 3 and inner_height > 5:
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.setPen(QPen(QColor(120, 120, 120), max(1, scale)))
            
            inner_rect = QRectF(inner_x, post_top_y + inner_top_margin, inner_w, inner_height)
            painter.drawRoundedRect(inner_rect, corner_radius * 0.5, corner_radius * 0.5)
            
            n_rails = 4
            rail_spacing = inner_height / (n_rails + 1)
            rail_height = max(2, 3 * scale)
            
            painter.setBrush(QBrush(QColor(180, 180, 180)))
            painter.setPen(QPen(QColor(100, 100, 100), max(0.5, scale * 0.5)))
            
            for i in range(1, n_rails + 1):
                rail_y = post_top_y + inner_top_margin + i * rail_spacing - rail_height/2
                rail_rect = QRectF(inner_x + 2, rail_y, inner_w - 4, rail_height)
                painter.drawRect(rail_rect)
        
        painter.setPen(QPen(QColor(150, 150, 150), 1, Qt.DashLine))
        painter.setBrush(Qt.NoBrush)
        outline_margin = 2
        outline_rect = QRectF(rect_x - outline_margin,
                            post_top_y - outline_margin,
                            outer_w + 2 * outline_margin,
                            total_h + 2 * outline_margin)
        painter.drawRoundedRect(outline_rect, corner_radius + 2, corner_radius + 2)
        
        # Return bounding box with actual outer width
        return (rect_x, post_top_y, rect_x + outer_w, y, outer_w)

    def add_professional_cross_section_dimensions(self, painter, deck_left_x, deck_right_x,
                        carriageway_start_x, carriageway_end_x,
                            left_barrier_x, right_barrier_x,
                            deck_top_y, deck_bottom_y, fp_top_y,
                            base_y, scale, positions, n,
                            fp_config, left_fp_width, right_fp_width,
                            left_fp_x, right_fp_x, railing_width_px, girder_depth_visual,
                            median_present=False, median_start_x=None, median_end_x=None, median_width=1200,
                            crash_barrier_width_px=None, left_barrier_end_x=None, right_barrier_end_x=None, DIM_OFFSET=0, DIM_OFFSET_SMALL=0 ):
        """Add organized dimension lines with extension lines - with median support"""
        
        fp_thick_px = self.params['footpath_thickness'] * scale
        deck_thick_px = self.params['deck_thickness'] * scale
        
        CRASH_BARRIER_VISUAL_WIDTH = 350.0  # BOTTOM_WIDTH
        crash_barrier_visual_px = CRASH_BARRIER_VISUAL_WIDTH * scale
        
        # Calculate barrier positions if not passed
        if crash_barrier_width_px is None:
            crash_barrier_width_px = self.params['crash_barrier_width'] * scale
        if left_barrier_end_x is None:
            left_barrier_end_x = left_barrier_x + crash_barrier_width_px
        if right_barrier_end_x is None:
            right_barrier_end_x = right_barrier_x + crash_barrier_width_px
        
        # Left barrier starts at left_barrier_x and extends RIGHT by crash_barrier_visual_px
        left_barrier_visual_end = left_barrier_x + crash_barrier_visual_px
        
        # Right barrier ENDS at right_barrier_end_x and extends LEFT by crash_barrier_visual_px
        right_barrier_visual_start = right_barrier_end_x - crash_barrier_visual_px
        
        # LEVEL 1: Overall Bridge Width
        #y_level1 = deck_top_y - 115
        Y_OVERALL = base_y + 55
        total_width_m = (deck_right_x - deck_left_x) / scale / 1000.0

        self.draw_dimension_arrow(
            painter,
            deck_left_x, Y_OVERALL,
            deck_right_x, Y_OVERALL,
            "", True,
            extension_direction='down',
            extension_end_y=fp_top_y
        )

        mid_x = (deck_left_x + deck_right_x) / 2.0
        label_text = f"Overall Bridge Width = {total_width_m:.2f} m"

        font = QFont('Arial', 9, QFont.Bold)
        painter.setFont(font)
        metrics = painter.fontMetrics()
        text_w = metrics.boundingRect(label_text).width()
        text_y = Y_OVERALL - 5  # Moved down more

        self.draw_text_with_background(
            painter,
            mid_x - text_w / 2.0,
            text_y,
            label_text,
            QColor(255, 255, 255, 255),
            QColor(0, 0, 0),
            9,
            True
        )

        # LEVEL 2: Footpath dimensions
        #y_level2 = deck_top_y - 65  # Moved down more
        Y_TOP_COMMON = deck_top_y - (3.2 * DIM_OFFSET)
        
        if fp_config in ['left', 'both'] and left_fp_width > 0:
            fp_start_x = deck_left_x + railing_width_px
            fp_end_x = left_barrier_x
            fp_visible_mm = (fp_end_x - fp_start_x) / scale
            fp_visible_m = fp_visible_mm / 1000
            if fp_visible_m > 0:
                self.draw_dimension_arrow(painter, fp_start_x, Y_TOP_COMMON, 
                                        fp_end_x, Y_TOP_COMMON,
                                        f"Footpath Width = {fp_visible_m:.2f} m", True, 
                                        extension_direction='down',
                                        extension_end_y=fp_top_y)
        
        # LEVEL 2c: Carriageway/Median Dimensions
        #y_level2c = deck_top_y - 35  # Moved down more
        Y_TOP_COMMON = deck_top_y - (3.2 * DIM_OFFSET)
    
        actual_cw_start = left_barrier_visual_end
        actual_cw_end = right_barrier_visual_start
        
        if median_present and median_start_x is not None and median_end_x is not None:
            cw_m = self.params['carriageway_width'] / 1000
            
            # Left carriageway - starts exactly at left barrier visual end
            self.draw_dimension_arrow(painter, actual_cw_start, Y_TOP_COMMON, median_start_x, Y_TOP_COMMON,
                                    f"Carriageway = {cw_m:.2f} m", True, 
                                    extension_direction='down',
                                    extension_end_y=deck_top_y)
            
            # Median dimension
            median_m = median_width / 1000
            self.draw_dimension_arrow(painter, median_start_x, Y_TOP_COMMON - 35, median_end_x, Y_TOP_COMMON - 35,
                                    f"Median = {median_m:.2f} m", True, 
                                    extension_direction='down',
                                    extension_end_y=deck_top_y)
            
            # Right carriageway - ends exactly at right barrier visual start
            self.draw_dimension_arrow(painter, median_end_x, Y_TOP_COMMON, actual_cw_end, Y_TOP_COMMON,
                                    f"Carriageway = {cw_m:.2f} m", True, 
                                    extension_direction='down',
                                    extension_end_y=deck_top_y)
        else:
            # Single carriageway
            cw_m = self.params['carriageway_width'] / 1000
            # From left barrier visual end to right barrier visual start
            self.draw_dimension_arrow(painter, actual_cw_start, Y_TOP_COMMON, actual_cw_end, Y_TOP_COMMON,
                                    f"Carriageway Width = {cw_m:.2f} m", True, 
                                    extension_direction='down',
                                    extension_end_y=deck_top_y)
        
        # Right footpath dimension
        if fp_config in ['right', 'both'] and right_fp_width > 0:
            fp_start_x = right_barrier_end_x
            fp_end_x = deck_right_x - railing_width_px
            fp_visible_mm = (fp_end_x - fp_start_x) / scale
            fp_visible_m = fp_visible_mm / 1000
            if fp_visible_m > 0:
                self.draw_dimension_arrow(painter, fp_start_x, Y_TOP_COMMON, 
                                        fp_end_x, Y_TOP_COMMON,
                                        f"Footpath Width = {fp_visible_m:.2f} m", True, 
                                        extension_direction='down',
                                        extension_end_y=fp_top_y)
        
        # LEVEL 3: Below bridge - Overhang
        #y_level3 = base_y + 30  # Moved up
        Y_BOTTOM_COMMON = base_y + (1.2 * DIM_OFFSET)
        
        if n > 0 and len(positions) > 0:
            first_girder_x = positions[0]
            overhang_m = self.params.get('deck_overhang', 1000) / 1000
            self.draw_dimension_arrow(painter, deck_left_x, Y_BOTTOM_COMMON, first_girder_x, Y_BOTTOM_COMMON,
                                    f"Overhang = {overhang_m:.2f} m", True,
                                    extension_direction='up',
                                    extension_end_y=deck_bottom_y)
        
        # Girder spacing
        if n > 1 and len(positions) >= 2:
            #y_level4 = base_y + 60  # Moved up
            Y_BOTTOM_COMMON = base_y + (1.2 * DIM_OFFSET)
            
            x_left = positions[0]
            x_right = positions[1]
            
            gs_m = self.params['girder_spacing'] / 1000
            self.draw_dimension_arrow(painter, x_left, Y_BOTTOM_COMMON, x_right, Y_BOTTOM_COMMON,
                                    f"Girder Spacing = {gs_m:.2f} m", True, 
                                    extension_direction='up',
                                    extension_end_y=base_y)
        
        # FOOTPATH THICKNESS DIMENSION 
        fp_t_mm = self.params['footpath_thickness']
        
        if fp_config in ['left', 'both'] and left_fp_width > 0 and fp_thick_px > 5:
            x_dim = deck_left_x - 8
            self.draw_vertical_dimension_with_arrow(painter, x_dim, fp_top_y, deck_bottom_y,
                                                    f"Footpath\nThickness = {fp_t_mm:.0f} mm", 'left')
        
        if fp_config == 'right' and right_fp_width > 0 and fp_thick_px > 5:
            x_dim = deck_right_x + 8
            self.draw_vertical_dimension_with_arrow(painter, x_dim, fp_top_y, deck_bottom_y,
                                                    f"Footpath\nThickness = {fp_t_mm:.0f} mm", 'right')
        
        # DECK THICKNESS DIMENSION - position adjusted for median
        deck_t_mm = self.params['deck_thickness']
        deck_slab_left = left_barrier_x
        deck_slab_right = right_barrier_end_x
        
        # If median is present, move deck thickness dimension to the left carriageway area
        if median_present and median_start_x is not None:
            # Position in the left carriageway (between left barrier and median)
            deck_center_x = (left_barrier_visual_end + median_start_x) / 2
        else:
            deck_center_x = (deck_slab_left + deck_slab_right) / 2

        if deck_thick_px > 5:
            painter.setPen(QPen(QColor(0, 0, 0), 0.8))
            painter.drawLine(QPointF(deck_center_x, deck_top_y), QPointF(deck_center_x, deck_bottom_y))
            
            arrow_size = 3.5
            arrow_gap = 2
            half_w     = arrow_size / 2
            painter.setBrush(QBrush(QColor(0, 0, 0)))
            
            top_arrow = [
                QPointF(deck_center_x, deck_top_y - arrow_gap),
                QPointF(deck_center_x - half_w, deck_top_y - arrow_gap - arrow_size),
                QPointF(deck_center_x + half_w, deck_top_y - arrow_gap - arrow_size),
            ]
            painter.drawPolygon(QPolygonF(top_arrow))
            
            bottom_arrow = [
                QPointF(deck_center_x, deck_bottom_y + arrow_gap),
                QPointF(deck_center_x - half_w, deck_bottom_y + arrow_gap + arrow_size),
                QPointF(deck_center_x + half_w, deck_bottom_y + arrow_gap + arrow_size),
            ]
            painter.drawPolygon(QPolygonF(bottom_arrow))
            
            tick_len = 4
            painter.drawLine(QPointF(deck_center_x - tick_len, deck_top_y), 
                            QPointF(deck_center_x + tick_len, deck_top_y))
            painter.drawLine(QPointF(deck_center_x - tick_len, deck_bottom_y), 
                            QPointF(deck_center_x + tick_len, deck_bottom_y))
            
            # Renamed to "Deck Thickness"
            text = f"Deck Thickness = {deck_t_mm:.0f} mm"
            font = QFont('Arial', 9, QFont.Bold)
            painter.setFont(font)
            metrics = painter.fontMetrics()
            text_width = metrics.boundingRect(text).width()
            text_x = deck_center_x - text_width / 2
            text_y = deck_top_y - 8
            
            self.draw_text_with_background(painter, text_x, text_y, text,
                                        QColor(255, 255, 255, 255), QColor(0, 0, 0), 9, True)
    def add_cross_section_hover_labels(self, painter, carriageway_start_x, carriageway_end_x,
                    left_barrier_x, right_barrier_x, deck_top_y, deck_bottom_y,
                    deck_thick_px, positions, base_y, scale, n, fp_config,
                    deck_left_x, deck_right_x, left_fp_width, 
                    right_fp_width, fp_top_y, fp_thick_px,
                    left_fp_x, right_fp_x, left_railing_rect, right_railing_rect,
                    railing_width_px, median_present, median_start_x, median_end_x, median_width,
                    deck_slab_left, deck_slab_right,
                    crash_barrier_width_px=None, left_barrier_end_x=None, right_barrier_end_x=None):
        """Hover labels with specific positioning requirements"""
        
        # Calculate if not passed
        if crash_barrier_width_px is None:
            crash_barrier_width_px = self.params['crash_barrier_width'] * scale
        if left_barrier_end_x is None:
            left_barrier_end_x = left_barrier_x + crash_barrier_width_px
        if right_barrier_end_x is None:
            right_barrier_end_x = right_barrier_x + crash_barrier_width_px
        
        cb_height = self.crash_barrier['height'] * scale
        visual = self.girder_visual_scale
        girder_depth_visual = self.girder['depth'] * scale * visual['depth']
        bf = self.girder['flange_width'] * scale * visual['flange_width']
        
        # Common label line Y position (below girders)
        label_line_y = base_y + 25
        
        components = []
        
        # Deck slab - straight line below girder
        deck_rect = QRectF(deck_slab_left, deck_top_y, deck_slab_right - deck_slab_left, deck_thick_px)
        deck_center_x = (deck_slab_left + deck_slab_right) / 2
        components.append((deck_rect, "Deck", deck_center_x, deck_bottom_y, 'straight_line', None))
        
        # Left crash barrier - text on top of figure
        left_cb_rect = QRectF(left_barrier_x, deck_top_y - cb_height,
                            crash_barrier_width_px, cb_height)
        left_cb_center_x = left_barrier_x + crash_barrier_width_px / 2
        left_cb_top_y = deck_top_y - cb_height
        components.append((left_cb_rect, "Crash Barrier", left_cb_center_x, left_cb_top_y, 'on_figure_top', None))
        
        # Right crash barrier - text on top of figure
        right_cb_rect = QRectF(right_barrier_x, deck_top_y - cb_height,
                            crash_barrier_width_px, cb_height)
        right_cb_center_x = right_barrier_x + crash_barrier_width_px / 2
        right_cb_top_y = deck_top_y - cb_height
        components.append((right_cb_rect, "Crash Barrier", right_cb_center_x, right_cb_top_y, 'on_figure_top', None))
        
        # Left footpath - tilted line towards left
        if fp_config in ['left', 'both'] and left_fp_width > 0 and fp_thick_px > 5:
            left_fp_rect = QRectF(left_fp_x + railing_width_px, fp_top_y, 
                                left_fp_width * scale - railing_width_px, fp_thick_px)
            fp_center_x = (left_fp_x + railing_width_px + left_barrier_x) / 2
            fp_center_y = fp_top_y + fp_thick_px / 2
            components.append((left_fp_rect, "Footpath", fp_center_x, fp_center_y, 'tilted_line_left', None))
        
        # Right footpath - straight line same level as deck
        if fp_config in ['right', 'both'] and right_fp_width > 0 and fp_thick_px > 5:
            # Right footpath starts at right_barrier_end_x and ends at deck_right_x
            right_fp_rect = QRectF(right_barrier_end_x, fp_top_y,
                                deck_right_x - right_barrier_end_x - railing_width_px, fp_thick_px)
            fp_center_x = (right_barrier_end_x + deck_right_x - railing_width_px) / 2
            fp_center_y = fp_top_y + fp_thick_px / 2
            components.append((right_fp_rect, "Footpath", fp_center_x, fp_center_y, 'straight_line', None))
        
        # Left railing - text on top of figure
        if left_railing_rect is not None:
            railing_rect = QRectF(left_railing_rect[0], left_railing_rect[1],
                                left_railing_rect[4], left_railing_rect[3] - left_railing_rect[1])
            railing_center_x = left_railing_rect[0] + left_railing_rect[4] / 2
            railing_top_y = left_railing_rect[1]
            components.append((railing_rect, "Railing", railing_center_x, railing_top_y, 'on_figure_top', None))
        
        # Right railing - text on top of figure
        if right_railing_rect is not None:
            railing_rect = QRectF(right_railing_rect[0], right_railing_rect[1],
                                right_railing_rect[4], right_railing_rect[3] - right_railing_rect[1])
            railing_center_x = right_railing_rect[0] + right_railing_rect[4] / 2
            railing_top_y = right_railing_rect[1]
            components.append((railing_rect, "Railing", railing_center_x, railing_top_y, 'on_figure_top', None))
        
        # Median barriers - straight line same level as deck
        if median_present and median_start_x is not None:
            median_rect = QRectF(median_start_x, deck_top_y - cb_height,
                                median_end_x - median_start_x, cb_height)
            median_center_x = (median_start_x + median_end_x) / 2
            components.append((median_rect, "Median",
                            median_center_x, deck_bottom_y, 'straight_line', None))
        
        # Girders with stiffeners - pointer 50 below
        for i, girder_x in enumerate(positions):
            stiff_w = self.stiffener['width'] * scale * visual['flange_width']
            tw = self.girder['web_thickness'] * scale * visual['web_thickness']
            total_width = bf + 2 * stiff_w
            girder_rect = QRectF(girder_x - total_width/2, base_y - girder_depth_visual, 
                                total_width, girder_depth_visual)
            components.append((girder_rect, "Girder",
                            girder_x, base_y - girder_depth_visual / 2, 'lower_pointer', None))
        
        # Cross bracing zones - pointer 50 below
        if n > 1:
            for i in range(n - 1):
                x1 = positions[i] + bf/2
                x2 = positions[i + 1] - bf/2
                if x2 > x1:
                    bracing_rect = QRectF(x1, base_y - girder_depth_visual, x2 - x1, girder_depth_visual)
                    center_x = (x1 + x2) / 2
                    components.append((bracing_rect, "Cross Bracing",
                                    center_x, base_y - girder_depth_visual / 2, 'lower_pointer', None))
        
        # Register all for hover detection
        for rect, name, tx, ty, ltype, extra in components:
            self.hover_labels.append((rect, name, QColor(255, 255, 255, 255), QColor(60, 60, 60)))
        
        # Draw label only for hovered component
        if self.hovered_label_index >= 0 and self.hovered_label_index < len(components):
            rect, name, target_x, target_y, label_type, extra = components[self.hovered_label_index]
            
            if label_type == 'on_figure_top':
                font = QFont('Arial', 9, QFont.Bold)
                painter.setFont(font)
                metrics = painter.fontMetrics()
                text_width = metrics.boundingRect(name).width()
                text_height = metrics.height()
                
                text_x = target_x - text_width / 2
                text_y = target_y - 5
                
                self.draw_text_with_background(painter, text_x, text_y, name,
                                            QColor(255, 255, 255, 220), QColor(60, 60, 60), 9, True)
            
            elif label_type == 'straight_line':
                painter.setPen(QPen(QColor(100, 100, 100), 1.0, Qt.DotLine))
                painter.drawLine(QPointF(target_x, target_y), QPointF(target_x, label_line_y))
                
                painter.setPen(QPen(QColor(100, 100, 100), 1.5))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(QPointF(target_x, target_y), 3, 3)
                
                font = QFont('Arial', 9, QFont.Bold)
                painter.setFont(font)
                metrics = painter.fontMetrics()
                text_width = metrics.boundingRect(name).width()
                
                text_x = target_x - text_width / 2
                text_y = label_line_y + 6
                
                self.draw_text_with_background(painter, text_x, text_y, name,
                                            QColor(255, 255, 255, 255), QColor(60, 60, 60), 9, True)
            
            elif label_type == 'tilted_line_left':
                label_x = target_x - 25
                label_y = label_line_y - 30
                
                painter.setPen(QPen(QColor(100, 100, 100), 1.0, Qt.DotLine))
                painter.drawLine(QPointF(target_x, target_y), QPointF(label_x, label_y))
                
                painter.setPen(QPen(QColor(100, 100, 100), 1.5))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(QPointF(target_x, target_y), 3, 3)
                
                font = QFont('Arial', 9, QFont.Bold)
                painter.setFont(font)
                metrics = painter.fontMetrics()
                text_width = metrics.boundingRect(name).width()
                
                text_x = label_x - text_width - 5
                text_y = label_y + 4
                
                self.draw_text_with_background(painter, text_x, text_y, name,
                                            QColor(255, 255, 255, 255), QColor(60, 60, 60), 9, True)
            
            elif label_type == 'lower_pointer':
                label_y = target_y + 35
                
                if target_x < self.width() / 2:
                    label_x = target_x + 40
                else:
                    label_x = target_x - 40
                
                self.draw_clean_leader_line(painter, target_x, target_y, label_x, label_y,
                                            name, QColor(60, 60, 60), QColor(120, 120, 120))

    def draw_vertical_dimension_with_arrow(self, painter, x, y1, y2, text, side='left'):
        """Draw vertical dimension with arrow and text"""
        painter.setPen(QPen(QColor(0, 0, 0), 0.8))
        
        # Main vertical line
        painter.drawLine(QPointF(x, y1), QPointF(x, y2))
        
        tick_len = 3
        painter.drawLine(QPointF(x - tick_len, y1), QPointF(x + tick_len, y1))
        painter.drawLine(QPointF(x - tick_len, y2), QPointF(x + tick_len, y2))
        arrow_gap = 2
        arrow_size = 3      # height of arrow
        arrow_half = 1      # half width → gives ~3:1 ratio

        painter.setBrush(QBrush(QColor(0, 0, 0)))
        
        top_arrow = [
            QPointF(x, y1 - arrow_gap),
            QPointF(x - arrow_size/2, y1 - arrow_gap - arrow_size),
            QPointF(x + arrow_size/2, y1 - arrow_gap - arrow_size)
        ]
        painter.drawPolygon(QPolygonF(top_arrow))
        
        bottom_arrow = [
            QPointF(x, y2 + arrow_gap),
            QPointF(x - arrow_size/2, y2 + arrow_gap + arrow_size),
            QPointF(x + arrow_size/2, y2 + arrow_gap + arrow_size)
        ]
        painter.drawPolygon(QPolygonF(bottom_arrow))
        
        # TEXT PART (multi-line)
        font = QFont('Arial', 9, QFont.Bold)
        painter.setFont(font)
        metrics = painter.fontMetrics()
        
        # Split into lines using \n
        lines = text.split('\n')
        line_height = metrics.height()
        max_width = max(metrics.boundingRect(line).width() for line in lines)
        total_height = line_height * len(lines)
        
        # Center vertically between y1 & y2
        center_y = (y1 + y2) / 2.0
        
        # First baseline y (use ascent to keep text nicely placed)
        first_baseline_y = center_y - total_height / 2.0 + metrics.ascent()
        
        # X placement left or right
        if side == 'left':
            text_x = x - max_width - 8
        else:
            text_x = x + 8
        
        # Background rect
        margin = 2
        bg_rect = QRectF(
            text_x - margin,
            center_y - total_height / 2.0 - margin,
            max_width + 2 * margin,
            total_height + 2 * margin
        )
        
        painter.save()
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(255, 255, 255, 255)))
        painter.drawRect(bg_rect)
        painter.restore()
        
        # Draw each line
        painter.setPen(QPen(QColor(0, 0, 0), 1.1))
        for i, line in enumerate(lines):
            painter.drawText(
                QPointF(text_x, first_baseline_y + i * line_height),
                line
            )

    def draw_i_section(self, painter, x, base_y, scale, girder_color):
        """Draw I-section girder (supports asymmetric sections)"""
        visual = self.girder_visual_scale
        d = self.girder['depth'] * scale * visual['depth']
        
        # Use top/bottom flange dimensions if available, else fall back to symmetric
        if 'top_flange_width' in self.girder and 'bottom_flange_width' in self.girder:
            bf_top = self.girder['top_flange_width'] * scale * visual['flange_width']
            tf_top = self.girder['top_flange_thickness'] * scale * visual['flange_thickness'] 
            bf_bottom = self.girder['bottom_flange_width'] * scale * visual['flange_width']
            tf_bottom = self.girder['bottom_flange_thickness'] * scale * visual['flange_thickness'] 
        else:
            # Legacy symmetric section
            bf_top = bf_bottom = self.girder['flange_width'] * scale * visual['flange_width']
            tf_top = tf_bottom = self.girder['flange_thickness'] * scale * visual['flange_thickness']
        
        tw = self.girder['web_thickness'] * scale * visual['web_thickness']
        
        # Check if this girder is hovered (more visible brightness)
        girder_hovered = (self.hovered_element == 'girder')
        if girder_hovered:
            # Strong brightness increase (lighter by 70 units)
            r, g, b = girder_color.red(), girder_color.green(), girder_color.blue()
            highlight_color = QColor(min(255, r + 70), min(255, g + 70), min(255, b + 70))
            painter.setBrush(QBrush(highlight_color))
        else:
            painter.setBrush(QBrush(girder_color))
        
        painter.setPen(QPen(QColor(0, 0, 0), 1.5))
        
        # Draw bottom flange
        painter.drawRect(QRectF(x - bf_bottom/2, base_y - tf_bottom, bf_bottom, tf_bottom))
        
        # Draw web
        web_height = d - tf_top - tf_bottom
        painter.drawRect(QRectF(x - tw/2, base_y - d + tf_top, tw, web_height))
        
        # Draw top flange
        painter.drawRect(QRectF(x - bf_top/2, base_y - d, bf_top, tf_top))
        
        # Register hover zone for this girder (use the widest flange as width)
        max_flange = max(bf_top, bf_bottom)
        hover_padding = 10
        hover_rect = QRectF(x - max_flange/2 - hover_padding, 
                           base_y - d - hover_padding,
                           max_flange + 2*hover_padding, 
                           d + 2*hover_padding)
        self.cross_section_hover_zones.append((hover_rect, 'girder'))
        
    def draw_stiffeners(self, painter, x, base_y, scale, stiffener_color):
        """Draw vertical stiffeners with chamfered inner corners"""
        visual = self.girder_visual_scale

        stiff_w = self.stiffener['width'] * scale * visual['flange_width']
        stiff_h = self.stiffener['height'] * scale * visual['depth'] * 0.976

        tw = self.girder['web_thickness'] * scale * visual['web_thickness']

        # Flange thickness (top)
        if 'top_flange_thickness' in self.girder:
            flange_thick = self.girder['top_flange_thickness'] * scale * visual['flange_thickness']
        else:
            flange_thick = self.girder['flange_thickness'] * scale * visual['flange_thickness']

        girder_depth_visual = self.girder['depth'] * scale * visual['depth']

        painter.setBrush(QBrush(stiffener_color))
        painter.setPen(QPen(QColor(0, 0, 0), 1))

        stiff_top_y = base_y - girder_depth_visual + flange_thick
        stiff_bottom_y = stiff_top_y + stiff_h

        #  Chamfer size (small & proportional)
        chamfer = min(stiff_w, flange_thick) * 1.3

        # ================= LEFT STIFFENER =================
        lx = x - tw / 2 - stiff_w
        rx = x - tw / 2

        left_stiffener = QPolygonF([
            QPointF(lx, stiff_top_y),                         # top-left
            QPointF(rx - chamfer, stiff_top_y),               # chamfer start (top inner)
            QPointF(rx, stiff_top_y + chamfer),               # chamfer end
            QPointF(rx, stiff_bottom_y - chamfer),            # chamfer start (bottom inner)
            QPointF(rx - chamfer, stiff_bottom_y),             # chamfer end
            QPointF(lx, stiff_bottom_y),                       # bottom-left
        ])

        painter.drawPolygon(left_stiffener)

        # ================= RIGHT STIFFENER =================
        lx = x + tw / 2
        rx = x + tw / 2 + stiff_w

        right_stiffener = QPolygonF([
             QPointF(lx + chamfer, stiff_top_y),               # chamfer start
             QPointF(rx, stiff_top_y),                          # top-right
             QPointF(rx, stiff_bottom_y),                       # bottom-right
             QPointF(lx + chamfer, stiff_bottom_y),             # chamfer end
             QPointF(lx, stiff_bottom_y - chamfer),             # chamfer start
             QPointF(lx, stiff_top_y + chamfer),                # chamfer end
        ])

        painter.drawPolygon(right_stiffener)

    def draw_crash_barrier(self, painter, x, y, scale, side='left'):
        """Draw RCC crash barrier matching the exact irc diamentions."""
        
        # DIMENSIONS (in mm)
        TOTAL_HEIGHT = 900.0
        TOP_WIDTH = 175.0
        BOTTOM_WIDTH = 350.0
        BASE_VERTICAL = 100.0
        
        # Scale everything
        h = TOTAL_HEIGHT * scale
        top_w = TOP_WIDTH * scale
        bottom_w = BOTTOM_WIDTH * scale
        base_v = BASE_VERTICAL * scale
        
        # Key Y positions (from deck going up, so negative)
        y_bottom = y
        y_base_top = y - base_v
        y_mid = y - (1000 - 650) * scale
        y_top = y - h
        
        # Offsets 
        right_at_mid = (400 - 150) * scale   # 250 * scale
        left_at_top = (200 - 150) * scale    # 50 * scale
        right_at_top = (375 - 150) * scale   # 225 * scale
        
        # Check if crash barrier is hovered (more visible brightness)
        barrier_hovered = (self.hovered_element == 'crash_barrier')
        if barrier_hovered:
            barrier_color = QColor(255, 250, 220)  # Strong glow effect
        else:
            barrier_color = QColor(126,126,126)
        
        if side == 'left':
            # Left barrier: x is the LEFT edge (where barrier starts)
            # Barrier extends to the RIGHT from x
            
            p0 = QPointF(x, y_bottom)                          # bottom-left
            p1 = QPointF(x + bottom_w, y_bottom)               # bottom-right
            p2 = QPointF(x + bottom_w, y_base_top)             # right after base
            p3 = QPointF(x + right_at_mid, y_mid)              # right at middle
            p4 = QPointF(x + right_at_top, y_top)              # top-right
            p5 = QPointF(x + left_at_top, y_top)               # top-left
            p6 = QPointF(x, y_base_top)                        # left after base
            
            points = [p0, p1, p2, p3, p4, p5, p6]
            
            # Register hover zone for left crash barrier
            hover_rect = QRectF(x, y_top, bottom_w, h)
            self.cross_section_hover_zones.append((hover_rect, 'crash_barrier'))
            
        else:  # right side
            # Right barrier: x is the RIGHT edge (where barrier ends)
            # Barrier extends to the LEFT from x
            # The shape is mirrored so front (sloped side) faces left toward carriageway
            
            x_right = x                    # Right edge of barrier
            x_left = x - bottom_w          # Left edge of barrier at bottom
            
            p0 = QPointF(x_left, y_bottom)                              # bottom-left
            p1 = QPointF(x_right, y_bottom)                             # bottom-right
            p2 = QPointF(x_right, y_base_top)                           # right after base
            p3 = QPointF(x_right - left_at_top, y_top)                  # top-right (mirrored)
            p4 = QPointF(x_right - right_at_top, y_top)                 # top-left (mirrored)
            p5 = QPointF(x_right - right_at_mid, y_mid)                 # left at middle (mirrored)
            p6 = QPointF(x_left, y_base_top)                            # left after base
            
            points = [p0, p1, p2, p3, p4, p5, p6]
            
            # Register hover zone for right crash barrier
            hover_rect = QRectF(x_left, y_top, bottom_w, h)
            self.cross_section_hover_zones.append((hover_rect, 'crash_barrier'))
        
        # Draw the barrier
        painter.setBrush(QBrush(barrier_color))
        painter.setPen(QPen(QColor(0, 0, 0), max(1.5, scale * 1.5)))
        painter.drawPolygon(QPolygonF(points))