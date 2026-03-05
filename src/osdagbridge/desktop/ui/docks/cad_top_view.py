"""
Top View CAD Widget for OsdagBridge
Handles top/plan view rendering of bridge structures
Author: Arushi
"""

import math
from PySide6.QtWidgets import QWidget, QPushButton, QScrollArea
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QBrush, QPolygonF
from .cad_cross_section import CrossSectionCADWidget

# ---- CAD Grey Palette ----
CAD_DARK_GREY   = QColor(90, 90, 90)
CAD_MEDIUM_GREY = QColor(130, 130, 130)
CAD_LIGHT_GREY  = QColor(180, 180, 180)
CAD_HOVER_GREY  = QColor(110, 110, 110)
GIRDER_HIGHLIGHT = CAD_HOVER_GREY
CROSS_BRACING_HIGHLIGHT = CAD_HOVER_GREY
END_DIAPHRAGM_HIGHLIGHT = CAD_HOVER_GREY
BEARING_HIGHLIGHT = CAD_HOVER_GREY
# ---- Dimension text spacing (CAD standard) ----
DIM_TEXT_GAP = 15          # distance from dimension line to text
DIM_STACK_GAP = 15         # vertical gap between stacked dimensions
LEADER_TEXT_OFFSET = 25    # leader label distance


class TopViewCADWidget(QWidget):
    """Widget for drawing bridge top view"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.show_dimensions = False
        self.setMouseTracking(True)  # enable mouse tracking for hover
        
        # top view hover tracking 
        self.top_view_hover_zones = []  # list of (QRectF, element_type)
        self.hovered_top_view_element = None
        
        # Zoom level for this widget
        self.zoom_level = 1.0
        
        # Setup zoom controls inside this widget
        self.setup_zoom_controls()
        
        # Track scroll area for fixed button positioning
        self.scroll_area = None
        
        # bridge parameters with default values (all in mm)
        # These are the CAD state variables
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
        
        # Set minimum size for visibility (reduced for better shrinking)
        self.setMinimumSize(400, 300)
    
    def zoom_in(self):
        """Zoom in while keeping view centered"""
        # Store old center position before zoom
        old_center = self._get_scroll_center()
        
        # Apply zoom
        self.zoom_level *= 1.1
        self._update_widget_size()
        self.update()
        
        # Restore center position after zoom
        self._set_scroll_center(old_center, 1.1)

    def zoom_out(self):
        """Zoom out while keeping view centered"""
        # Store old center position before zoom
        old_center = self._get_scroll_center()
        
        # Apply zoom
        self.zoom_level /= 1.1
        self._update_widget_size()
        self.update()
        
        # Restore center position after zoom
        self._set_scroll_center(old_center, 1/1.1)

    def zoom_reset(self):
        """Reset zoom to 1.0 while keeping view centered"""
        # Store old center position before zoom
        old_center = self._get_scroll_center()
        zoom_ratio = 1.0 / self.zoom_level
        
        # Apply zoom
        self.zoom_level = 1.0
        self._update_widget_size()
        self.update()
        
        # Restore center position after zoom
        self._set_scroll_center(old_center, zoom_ratio)

    def _get_scroll_center(self):
        """Get the current center point of the visible viewport in widget coordinates"""
        if not self.scroll_area:
            return (0.5, 0.5)  # Default to center
        
        h_scrollbar = self.scroll_area.horizontalScrollBar()
        v_scrollbar = self.scroll_area.verticalScrollBar()
        viewport = self.scroll_area.viewport()
        
        # Get current scroll position
        h_value = h_scrollbar.value()
        v_value = v_scrollbar.value()
        
        # Get viewport dimensions
        viewport_width = viewport.width()
        viewport_height = viewport.height()
        
        # Calculate center point in widget coordinates
        center_x = h_value + viewport_width / 2
        center_y = v_value + viewport_height / 2
        
        # Get widget dimensions
        widget_width = self.width()
        widget_height = self.height()
        
        # Return normalized center position (0.0 to 1.0)
        if widget_width > 0 and widget_height > 0:
            return (center_x / widget_width, center_y / widget_height)
        else:
            return (0.5, 0.5)

    def _set_scroll_center(self, old_center, zoom_ratio):
        """Set scroll position to keep the same center point visible after zoom"""
        if not self.scroll_area:
            return
        
        h_scrollbar = self.scroll_area.horizontalScrollBar()
        v_scrollbar = self.scroll_area.verticalScrollBar()
        viewport = self.scroll_area.viewport()
        
        # Get new widget dimensions after zoom
        new_width = self.width()
        new_height = self.height()
        
        # Calculate new center position in pixels
        new_center_x = old_center[0] * new_width
        new_center_y = old_center[1] * new_height
        
        # Calculate new scroll positions to center on the same point
        viewport_width = viewport.width()
        viewport_height = viewport.height()
        
        new_h_value = int(new_center_x - viewport_width / 2)
        new_v_value = int(new_center_y - viewport_height / 2)
        
        # Clamp to valid range
        new_h_value = max(0, min(new_h_value, h_scrollbar.maximum()))
        new_v_value = max(0, min(new_v_value, v_scrollbar.maximum()))
        
        # Apply new scroll positions
        h_scrollbar.setValue(new_h_value)
        v_scrollbar.setValue(new_v_value)
    
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
        """Position zoom buttons fixed in viewport - improved version"""
        if not hasattr(self, 'zoom_in_btn'):
            return
                
        # Get scroll area if not already set
        if self.scroll_area is None:
            parent = self.parent()
            while parent:
                if isinstance(parent, QScrollArea):
                    self.scroll_area = parent
                    # Install event filter on viewport
                    if self.scroll_area.viewport():
                        self.scroll_area.viewport().installEventFilter(self)
                    break
                parent = parent.parent()
        
        if not self.scroll_area:
            return
        
        # Get viewport
        viewport = self.scroll_area.viewport()
        if not viewport or viewport.width() == 0:
            return
        
        # Re-parent buttons to viewport if needed
        if self.zoom_in_btn.parent() != viewport:
            self.zoom_in_btn.setParent(viewport)
            self.zoom_out_btn.setParent(viewport)
            self.zoom_reset_btn.setParent(viewport)
        
        # Position buttons at top-right of viewport
        button_margin = 10
        button_width = 50
        
        x = viewport.width() - button_width - button_margin
        y = button_margin
        
        self.zoom_in_btn.move(int(x + 10), int(y))
        self.zoom_out_btn.move(int(x + 10), int(y + 30))
        self.zoom_reset_btn.move(int(x), int(y + 60))
        
        # Ensure buttons are visible on top
        self.zoom_in_btn.show()
        self.zoom_out_btn.show()
        self.zoom_reset_btn.show()
        self.zoom_in_btn.raise_()
        self.zoom_out_btn.raise_()
        self.zoom_reset_btn.raise_()


    def eventFilter(self, obj, event):
        """Filter events to catch viewport resize"""
        if obj == (self.scroll_area.viewport() if self.scroll_area else None):
            if event.type() == event.Type.Resize:
                # Viewport resized - reposition buttons
                self._position_zoom_buttons()
        return super().eventFilter(obj, event)

    def update_params(self, params):
        self.params.update(params)

        # Show dimensions once user provides inputs
        if params:
            self.show_dimensions = True

        self.update()
    
    def mouseMoveEvent(self, event):
        """Handle mouse hover for top view"""
        pos = event.position() if hasattr(event, 'position') else event.pos()
        
        # top view hover logic
        new_hovered = None
        for rect, element_type in self.top_view_hover_zones:
            if rect.contains(pos):
                new_hovered = element_type
                break
        
        if new_hovered != self.hovered_top_view_element:
            self.hovered_top_view_element = new_hovered
            self.update()

    def paintEvent(self, event):
        # clear hover zones at start of each paint
        self.top_view_hover_zones = []
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        
        self.draw_top_view(painter)
        
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
        
        arrow_len = 6          # you can tune this, ratio stays correct
        arrow_half = arrow_len / 3

        painter.setBrush(QBrush(QColor(0, 0, 0)))
        
        if horizontal:
            left_arrow = [
                QPointF(x1, y1),
                QPointF(x1 + arrow_len, y1 - arrow_half),
                QPointF(x1 + arrow_len, y1 + arrow_half)
            ]
            painter.drawPolygon(QPolygonF(left_arrow))
            
            right_arrow = [
                QPointF(x2, y2),
                QPointF(x2 - arrow_len, y2 - arrow_half),
                QPointF(x2 - arrow_len, y2 + arrow_half)
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
                
                painter.setPen(QPen(QColor(0, 0, 0), 0.8))
            
            text_x = (x1 + x2) / 2
            text_y = y1 - 8 + text_offset if offset >= 0 else y1 + 15 + text_offset
            
            font = QFont('Arial', 9, QFont.Bold)
            metrics = painter.fontMetrics()
            text_width = metrics.boundingRect(text).width()
            
            self.draw_text_with_background(painter, text_x - text_width/2, text_y, text, 
                                        QColor(255, 255, 255, 240), QColor(0, 0, 0), 9, True)
        else:
            top_arrow = [
                QPointF(x1, y1),
                QPointF(x1 - arrow_half, y1 + arrow_len),
                QPointF(x1 + arrow_half, y1 + arrow_len)
            ]

            painter.drawPolygon(QPolygonF(top_arrow))
            
            bottom_arrow = [
                QPointF(x2, y2),
                QPointF(x2 - arrow_half, y2 - arrow_len),
                QPointF(x2 + arrow_half, y2 - arrow_len)
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
                
                painter.setPen(QPen(QColor(0, 0, 0), 0.8))
            
            text_x = x1 + (12 if offset >= 0 else -45) + text_offset
            text_y = (y1 + y2) / 2 + 3
            
            self.draw_text_with_background(painter, text_x, text_y, text,
                                        QColor(255, 255, 255, 240), QColor(0, 0, 0), 9, True)
    
    def draw_dimension_arrow_text_outside(self, painter, x1, y1, x2, y2, text, horizontal=True, 
                                          text_side='right', text_offset=15):
        """Dimension line with arrows"""
        painter.setPen(QPen(QColor(0, 0, 0), 0.8))
        
        painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        
        ext_len = 6
        arrow_len = 6
        arrow_half = arrow_len / 3

        painter.setBrush(QBrush(QColor(0, 0, 0)))
        
        if horizontal:
            painter.drawLine(QPointF(x1, y1 - ext_len), QPointF(x1, y1 + ext_len))
            painter.drawLine(QPointF(x2, y2 - ext_len), QPointF(x2, y2 + ext_len))
            
            left_arrow = [
                QPointF(x1, y1),
                QPointF(x1 + arrow_len, y1 - arrow_half),
                QPointF(x1 + arrow_len, y1 + arrow_half)
            ]
            painter.drawPolygon(QPolygonF(left_arrow))
            
            right_arrow = [
                QPointF(x2, y2),
                QPointF(x2 - arrow_len, y2 - arrow_half),
                QPointF(x2 - arrow_len, y2 + arrow_half)
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
                                        QColor(255, 255, 255, 240), QColor(0, 0, 0), 9, True)
        else:
            painter.drawLine(QPointF(x1 - ext_len, y1), QPointF(x1 + ext_len, y1))
            painter.drawLine(QPointF(x2 - ext_len, y2), QPointF(x2 + ext_len, y2))
            
            top_arrow = [
                QPointF(x1, y1),
                QPointF(x1 - arrow_half, y1 + arrow_len),
                QPointF(x1 + arrow_half, y1 + arrow_len)
            ]

            painter.drawPolygon(QPolygonF(top_arrow))
            
            bottom_arrow = [
                QPointF(x2, y2),
                QPointF(x2 - arrow_half, y2 - arrow_len),
                QPointF(x2 + arrow_half, y2 - arrow_len)
            ]

            painter.drawPolygon(QPolygonF(bottom_arrow))
            
            text_y = (y1 + y2) / 2 + 3
            if text_side == 'left':
                text_x = x1 - text_offset - 35
            else:
                text_x = x1 + text_offset
            
            self.draw_text_with_background(painter, text_x, text_y, text,
                                        QColor(255, 255, 255, 240), QColor(0, 0, 0), 9, True)
        
    def draw_leader_arrow(self, painter, from_x, from_y, to_x, to_y, text, bg_color=QColor(255, 255, 255, 250), text_color=QColor(0, 0, 0)):
        """a leader line with arrow pointing to component"""
        painter.setPen(QPen(QColor(0, 0, 0), 1.0))
        painter.drawLine(QPointF(from_x, from_y), QPointF(to_x, to_y))
        
        arrow_len = 9
        arrow_half = arrow_len / 3

        angle = math.atan2(to_y - from_y, to_x - from_x)
        
        arrow_points = [
            QPointF(to_x, to_y),
            QPointF(
                to_x - arrow_len * math.cos(angle) + arrow_half * math.sin(angle),
                to_y - arrow_len * math.sin(angle) - arrow_half * math.cos(angle)
            ),
            QPointF(
                to_x - arrow_len * math.cos(angle) - arrow_half * math.sin(angle),
                to_y - arrow_len * math.sin(angle) + arrow_half * math.cos(angle)
            )
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
                                       QColor(255, 255, 255, 240), text_color, 9, True)
    
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

    def draw_median_crash_barriers(self, painter, median_start_x, median_end_x, deck_top_y, scale):
        """Draw two crash barriers for median, facing outward"""
        
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
        
        painter.setBrush(QBrush(QColor(255, 210, 160)))
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
        
        painter.setBrush(QBrush(QColor(255, 210, 160)))
        painter.setPen(QPen(QColor(0, 0, 0), max(1.5, scale * 1.5)))
        painter.drawPolygon(QPolygonF(points_right))

    def draw_top_view(self, painter):
        """Draw top view with hover labels"""
        # Clear top view hover zones
        self.top_view_hover_zones = []
        
        # Define colors
        GIRDER_COLOR = CrossSectionCADWidget.GIRDER_COLOR
        CROSS_BRACING_COLOR = CrossSectionCADWidget.CROSS_BRACING_COLOR
        END_DIAPHRAGM_COLOR = CrossSectionCADWidget.END_DIAPHRAGM_COLOR

        
        # Highlight colors 
        GIRDER_HIGHLIGHT = CAD_HOVER_GREY
        CROSS_BRACING_HIGHLIGHT = CAD_HOVER_GREY
        END_DIAPHRAGM_HIGHLIGHT = CAD_HOVER_GREY
        BEARING_HIGHLIGHT = CAD_HOVER_GREY
        
        # Use base canvas dimensions for consistent drawing regardless of zoom
        width = 800 * self.zoom_level
        height = 600 * self.zoom_level

        # Reduced margins for better space utilization in split view
        margin = 60
        available_width = width - 2 * margin
        available_height = height - 2 * margin - 60

        n = self.params['num_girders']
        
        if n > 1:
            total_girder_width = (n - 1) * self.params['girder_spacing'] + 2 * self.params['deck_overhang']
        else:
            total_girder_width = 2 * self.params['deck_overhang']
        
        total_model_width = total_girder_width

        span_scale = available_width / max(self.params['span_length'], 1.0)
        width_scale = available_height / max(total_model_width, 1.0)
        scale = min(span_scale, width_scale)  # zoom_level already applied to width/height

        center_x = self.width() / 2
        center_y = self.height() / 2

        # FIX: Negate the skew angle
        skew_rad = math.radians(-self.params['skew_angle'])  # CHANGED: Added negative sign
        
        girder_positions_y = []
        
        if n > 1:
            spacing_px = self.params['girder_spacing'] * scale
            total_width_px = (n - 1) * spacing_px
            start_y = center_y - total_width_px / 2
            for i in range(n):
                y_pos = start_y + i * spacing_px
                girder_positions_y.append(y_pos)
        else:
            girder_positions_y = [center_y]

        span_length_px = self.params['span_length'] * scale
        start_x_base = center_x - span_length_px / 2
        end_x_base = center_x + span_length_px / 2

        # Check hover states
        girder_hovered = self.hovered_top_view_element == 'girder'
        bracing_hovered = self.hovered_top_view_element == 'cross_bracing'
        diaphragm_hovered = self.hovered_top_view_element == 'end_diaphragm'
        bearing_hovered = self.hovered_top_view_element == 'bearing'

        # Draw girders
        girder_color = GIRDER_HIGHLIGHT if girder_hovered else GIRDER_COLOR
        girder_width = 4.5 if girder_hovered else 2.5
        painter.setPen(QPen(girder_color, girder_width))
        
        girder_lines = []
        for y_pos in girder_positions_y:
            y_offset_from_first = y_pos - girder_positions_y[0]
            x_offset = y_offset_from_first * math.tan(skew_rad)
            
            x1 = start_x_base + x_offset
            x2 = end_x_base + x_offset
            
            painter.drawLine(QPointF(x1, y_pos), QPointF(x2, y_pos))
            girder_lines.append({'y': y_pos, 'x1': x1, 'x2': x2})
            
            # Register hover zone with larger padding for easier selection
            hover_padding = 15
            self.top_view_hover_zones.append((
                QRectF(x1, y_pos - hover_padding, x2 - x1, hover_padding * 2), 'girder'
            ))

        # Calculate bearing line positions
        bearing_gap_px = max(30, 0.3 * self.params['girder_spacing'] * scale)

        top_extent = girder_positions_y[0] - bearing_gap_px
        bottom_extent = girder_positions_y[-1] + bearing_gap_px if n > 1 else girder_positions_y[0] + bearing_gap_px

        left_bearing_base_x = start_x_base
        right_bearing_base_x = end_x_base

        left_top_x = left_bearing_base_x + (top_extent - girder_positions_y[0]) * math.tan(skew_rad)
        left_bottom_x = left_bearing_base_x + (bottom_extent - girder_positions_y[0]) * math.tan(skew_rad)

        right_top_x = right_bearing_base_x + (top_extent - girder_positions_y[0]) * math.tan(skew_rad)
        right_bottom_x = right_bearing_base_x + (bottom_extent - girder_positions_y[0]) * math.tan(skew_rad)

        # Draw END DIAPHRAGMS
        if n > 1:
            diaphragm_color = END_DIAPHRAGM_HIGHLIGHT if diaphragm_hovered else END_DIAPHRAGM_COLOR
            diaphragm_width = 4.0 if diaphragm_hovered else 3.0
            
            # Use solid line with slight offset for double-line effect
            painter.setBrush(Qt.NoBrush)
            
            # Left end diaphragm
            for i in range(len(girder_positions_y) - 1):
                y1 = girder_positions_y[i]
                y2 = girder_positions_y[i + 1]
                
                y1_offset = y1 - girder_positions_y[0]
                y2_offset = y2 - girder_positions_y[0]
                
                x1 = left_bearing_base_x + y1_offset * math.tan(skew_rad)
                x2 = left_bearing_base_x + y2_offset * math.tan(skew_rad)
                
                # Draw double solid lines for end diaphragm
                line_offset = 2
                dx = x2 - x1
                dy = y2 - y1
                length = math.sqrt(dx*dx + dy*dy)
                if length > 0:
                    perp_x = -dy / length * line_offset
                    perp_y = dx / length * line_offset
                    
                    painter.setPen(QPen(diaphragm_color, diaphragm_width, Qt.SolidLine))
                    painter.drawLine(QPointF(x1 + perp_x, y1 + perp_y), QPointF(x2 + perp_x, y2 + perp_y))
                    painter.drawLine(QPointF(x1 - perp_x, y1 - perp_y), QPointF(x2 - perp_x, y2 - perp_y))
                
                
                # Register hover zone with larger padding
                hover_padding = 20
                min_x, max_x = min(x1, x2) - hover_padding, max(x1, x2) + hover_padding
                min_y, max_y = min(y1, y2), max(y1, y2)
                self.top_view_hover_zones.append((
                    QRectF(min_x, min_y, max_x - min_x, max_y - min_y), 'end_diaphragm'
                ))
            
            # Right end diaphragm
            for i in range(len(girder_positions_y) - 1):
                y1 = girder_positions_y[i]
                y2 = girder_positions_y[i + 1]
                
                y1_offset = y1 - girder_positions_y[0]
                y2_offset = y2 - girder_positions_y[0]
                
                x1 = right_bearing_base_x + y1_offset * math.tan(skew_rad)
                x2 = right_bearing_base_x + y2_offset * math.tan(skew_rad)
                
                # Draw double solid lines
                line_offset = 2
                dx = x2 - x1
                dy = y2 - y1
                length = math.sqrt(dx*dx + dy*dy)
                if length > 0:
                    perp_x = -dy / length * line_offset
                    perp_y = dx / length * line_offset
                    
                    painter.setPen(QPen(diaphragm_color, diaphragm_width, Qt.SolidLine))
                    painter.drawLine(QPointF(x1 + perp_x, y1 + perp_y), QPointF(x2 + perp_x, y2 + perp_y))
                    painter.drawLine(QPointF(x1 - perp_x, y1 - perp_y), QPointF(x2 - perp_x, y2 - perp_y))
                
                
                hover_padding = 20
                min_x, max_x = min(x1, x2) - hover_padding, max(x1, x2) + hover_padding
                min_y, max_y = min(y1, y2), max(y1, y2)
                self.top_view_hover_zones.append((
                    QRectF(min_x, min_y, max_x - min_x, max_y - min_y), 'end_diaphragm'
                ))

        # Draw center line of bearings
        bearing_color = BEARING_HIGHLIGHT if bearing_hovered else CAD_DARK_GREY
        bearing_width = 2.5 if bearing_hovered else 1.5
        
        pen = QPen(bearing_color, bearing_width, Qt.CustomDashLine)
        pen.setDashPattern([8, 8])
        painter.setPen(pen)
        
        painter.drawLine(QPointF(left_top_x, top_extent), 
                        QPointF(left_bottom_x, bottom_extent))
        painter.drawLine(QPointF(right_top_x, top_extent), 
                        QPointF(right_bottom_x, bottom_extent))
        
        # Register bearing hover zones with larger padding
        hover_padding = 20
        self.top_view_hover_zones.append((
            QRectF(min(left_top_x, left_bottom_x) - hover_padding, top_extent, 
                abs(left_top_x - left_bottom_x) + hover_padding * 2, bottom_extent - top_extent), 'bearing'
        ))
        self.top_view_hover_zones.append((
            QRectF(min(right_top_x, right_bottom_x) - hover_padding, top_extent,
                abs(right_top_x - right_bottom_x) + hover_padding * 2, bottom_extent - top_extent), 'bearing'
        ))

        # Cross bracing
        bracing_positions_x = []
        if self.params['cross_bracing_spacing'] > 0 and n > 1:
            span_length = self.params['span_length']
            bracing_spacing = self.params['cross_bracing_spacing']
            
            num_braces = max(1, int(math.ceil(span_length / bracing_spacing)))
            actual_spacing_px = span_length_px / num_braces
            
            bracing_color = CROSS_BRACING_HIGHLIGHT if bracing_hovered else CROSS_BRACING_COLOR
            bracing_width = 3.5 if bracing_hovered else 1.8
            painter.setPen(QPen(bracing_color, bracing_width))
            
            for section in range(1, num_braces):
                brace_x_base = start_x_base + section * actual_spacing_px
                
                for i in range(len(girder_positions_y) - 1):
                    y1 = girder_positions_y[i]
                    y2 = girder_positions_y[i + 1]
                    
                    y1_offset = y1 - girder_positions_y[0]
                    y2_offset = y2 - girder_positions_y[0]
                    
                    x1 = brace_x_base + y1_offset * math.tan(skew_rad)
                    x2 = brace_x_base + y2_offset * math.tan(skew_rad)
                    
                    painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
                    
                    # Register hover zone with larger padding
                    hover_padding = 15
                    min_x, max_x = min(x1, x2) - hover_padding, max(x1, x2) + hover_padding
                    min_y, max_y = min(y1, y2), max(y1, y2)
                    self.top_view_hover_zones.append((
                        QRectF(min_x, min_y, max_x - min_x, max_y - min_y), 'cross_bracing'
                    ))
                    
                    if i == 0:
                        bracing_positions_x.append(brace_x_base)

        # Draw skew angle indicator
        if abs(self.params['skew_angle']) > 0.1:
            self.draw_skew_angle_indicator(painter, girder_lines[0]['x1'], girder_positions_y[0], 
                                        skew_rad, scale, left_bearing_base_x)

        # Add dimensions (always visible) and hover labels (only on hover)
        if self.show_dimensions:
            self.add_clean_top_view_dimensions(
                painter, girder_lines, girder_positions_y, scale, n, bracing_positions_x,
                skew_rad, start_x_base, end_x_base, left_bearing_base_x, right_bearing_base_x,
                top_extent, bottom_extent, left_top_x, right_top_x,
                GIRDER_COLOR, CROSS_BRACING_COLOR, END_DIAPHRAGM_COLOR
            )

        # Notes removed for cleaner layout in split view


    def draw_skew_angle_indicator(self, painter, girder_start_x, girder_y, skew_rad, scale, bearing_x):
        """Draw skew angle indicator with arc and proper sign display"""
        skew_deg = self.params['skew_angle']  # CHANGED
        
        if abs(skew_deg) < 0.1:
            return
        
        # Reference point at the first girder on the bearing line
        ref_x = bearing_x
        ref_y = girder_y
        
        arc_radius = 70
        
        # Draw vertical reference line (what 0 skew would look like)
        painter.setPen(QPen(QColor(0, 0, 0), 1.5, Qt.DashLine))
        painter.drawLine(QPointF(ref_x, ref_y), QPointF(ref_x, ref_y - arc_radius - 20))
        
        # Draw the actual skewed bearing line direction
        # The skew causes the bearing line to rotate, so we show that angle
        skewed_end_x = ref_x - arc_radius * math.sin(skew_rad)
        skewed_end_y = ref_y - arc_radius * math.cos(skew_rad)
        
        painter.setPen(QPen(QColor(0, 0, 0), 2.0))
        painter.drawLine(QPointF(ref_x, ref_y), QPointF(skewed_end_x, skewed_end_y))
        
        # Draw arc from vertical to skewed line
        # Qt uses 1/16 degree units, angles measured counter-clockwise from 3 o'clock
        # 90 degrees (in Qt) = pointing up
        arc_rect = QRectF(ref_x - arc_radius, ref_y - arc_radius, arc_radius * 2, arc_radius * 2)
        
        # Start angle is 90 degrees (pointing up/vertical)
        start_angle_deg = 90
        # Span angle is the skew angle (use original input value for arc direction)
        span_angle_deg = skew_deg
        
        painter.setPen(QPen(QColor(0,0,0), 2.5))
        painter.drawArc(arc_rect, int(start_angle_deg * 16), int(-span_angle_deg * 16))
        
        # Draw arrow at end of arc
        arrow_angle_rad = math.radians(90 - skew_deg)
        arrow_x = ref_x + arc_radius * math.cos(arrow_angle_rad)
        arrow_y = ref_y - arc_radius * math.sin(arrow_angle_rad)
        
        # -------- SHARP SKEW ARROW (CAD STYLE) --------

        # Arrow geometry (tuned for sharpness)
        shaft_len = 12      # length of arrow shaft
        head_len  = 10      # length of arrow head
        head_half_angle = math.radians(18)  # narrow = sharp tip

        # Tangent direction (exact)
        tangent_angle = arrow_angle_rad

        # Shaft start
        shaft_start_x = arrow_x - shaft_len * math.cos(tangent_angle)
        shaft_start_y = arrow_y + shaft_len * math.sin(tangent_angle)

        # Draw shaft
        painter.setPen(QPen(QColor(0, 0, 0), 2.0))
        painter.drawLine(
            QPointF(shaft_start_x, shaft_start_y),
            QPointF(arrow_x, arrow_y)
        )

        # Arrowhead points
        left_x = arrow_x - head_len * math.cos(tangent_angle - head_half_angle)
        left_y = arrow_y + head_len * math.sin(tangent_angle - head_half_angle)

        right_x = arrow_x - head_len * math.cos(tangent_angle + head_half_angle)
        right_y = arrow_y + head_len * math.sin(tangent_angle + head_half_angle)

        arrow_head = QPolygonF([
            QPointF(arrow_x, arrow_y),
            QPointF(left_x, left_y),
            QPointF(right_x, right_y)
        ])

        painter.setBrush(QBrush(QColor(0, 0, 0)))
        painter.drawPolygon(arrow_head)

        
        # Add angle label with proper sign - using ORIGINAL input value
        # Position label near the arc
        label_radius = arc_radius + 25
        label_angle_rad = math.radians(90 - skew_deg/2)  # Middle of the arc
        label_x = ref_x + label_radius * math.cos(label_angle_rad)
        label_y = ref_y - label_radius * math.sin(label_angle_rad)
        
        # Format with explicit sign (+ or -) - showing ORIGINAL input value
        if skew_deg >= 0:
            angle_text = f"Skew = +{abs(skew_deg):.1f}°"
        else:
            angle_text = f"Skew = {skew_deg:.1f}°"
        
        # Adjust label position based on skew direction
        if skew_deg > 0:
            label_x -= 10
        else:
            label_x -= 70
        
        self.draw_text_with_background(
            painter, label_x, label_y,
            angle_text,
            QColor(255, 255, 255, 240),
            QColor(0, 0, 0),
            9, True)


    def add_clean_top_view_dimensions(self, painter, girder_lines, girder_positions_y,
                            scale, n, bracing_positions, skew_rad,
                            start_x_base, end_x_base, left_bearing_base_x, right_bearing_base_x,
                            top_extent, bottom_extent, left_top_x, right_top_x,
                            girder_color, cross_bracing_color, end_diaphragm_color):
        """Add dimensions (always visible) and hover labels (only on hover)"""
        
        if not girder_lines:
            return
        
        # Get last girder for reference
        last_girder_idx = len(girder_lines) - 1
        last_girder = girder_lines[last_girder_idx]
        last_girder_y = last_girder['y']
        
        y_offset_last = last_girder_y - girder_positions_y[0]
        x_offset_last = y_offset_last * math.tan(skew_rad)
        
        #dim_y_base = last_girder_y + 50
        dim_y_base = last_girder_y + 28
        
        # SPAN LENGTH dimension (always visible)
        dim_y1 = dim_y_base
        x1_span = last_girder['x1']
        x2_span = last_girder['x2']
        span_m = self.params['span_length'] / 1000
        
        self.draw_dimension_arrow_with_extensions_up(
            painter, x1_span, dim_y1, x2_span, dim_y1,
            f"Span Length = {span_m:.1f} m", last_girder_y
        )

        # BRACING SPACING dimension (always visible)
        if self.params['cross_bracing_spacing'] > 0 and len(bracing_positions) > 1:
            #dim_y2 = dim_y_base + 15
            dim_y2 = dim_y_base + DIM_STACK_GAP
            cb_spacing_m = self.params['cross_bracing_spacing'] / 1000
            
            x1_brace = bracing_positions[0] + x_offset_last
            x2_brace = bracing_positions[1] + x_offset_last
            
            self.draw_dimension_arrow_with_extensions_up(
                painter, x1_brace, dim_y2, x2_brace, dim_y2,
                f"Bracing Spacing = {cb_spacing_m:.2f} m", last_girder_y
            )

        # GIRDER SPACING dimension (always visible)
        if n > 1:
            y1 = girder_positions_y[0]
            y2 = girder_positions_y[1]
            
            y1_offset = y1 - girder_positions_y[0]
            y2_offset = y2 - girder_positions_y[0]
            x1_at_end = end_x_base + y1_offset * math.tan(skew_rad) + 30
            x2_at_end = end_x_base + y2_offset * math.tan(skew_rad) + 30
            
            gs_m = self.params['girder_spacing'] / 1000

            # just the skewed dimension line + arrows, no text on it
            self.draw_skewed_dimension_arrow(
                painter, x1_at_end, y1, x2_at_end, y2,
                "",  # no inline text
                skew_rad
            )
            
            # Girder Spacing label + value (3 lines)
            label_x = max(x1_at_end, x2_at_end) + 12
            LABEL_OFFSET = 14  # tweak 10–18 if needed
            label_y = (y1 + y2) / 2 + LABEL_OFFSET

            label_text = f"Girder\nSpacing\n= {gs_m:.2f} m"

            self.draw_text_with_background(
                painter, label_x, label_y,
                label_text,
                QColor(255, 255, 255, 250),
                CAD_DARK_GREY, 9, True
            )

        # CL OF BEARING labels - ALWAYS VISIBLE (moved outside hover condition)
        label_y_bearing = top_extent - 8
        
        left_label_x = left_top_x - 45
        right_label_x = right_top_x - 45
        
        self.draw_text_with_background(painter, left_label_x, label_y_bearing,
                                    "CL of Bearing", QColor(255, 255, 255, 250),
                                    CAD_DARK_GREY, 9, True)
        
        self.draw_text_with_background(painter, right_label_x, label_y_bearing,
                                    "CL of Bearing", QColor(255, 255, 255, 250),
                                    CAD_DARK_GREY, 9, True)

        # HOVER LABELS (only shown when hovered) 
        
        # 1. GIRDER label - show only when girder is hovered
        if len(girder_lines) > 0 and self.hovered_top_view_element == 'girder':
            first_girder = girder_lines[0]
            target_x = (first_girder['x1'] + first_girder['x2']) / 2
            target_y = first_girder['y']
            
            label_x = target_x
            
            label_y = target_y - LEADER_TEXT_OFFSET
            label_offset = LEADER_TEXT_OFFSET
            
            self.draw_clean_leader_line(painter, target_x, target_y, label_x, label_y,
                                    "Girder", CAD_DARK_GREY, CAD_DARK_GREY)

        # 2. CROSS BRACING label - show only when cross bracing is hovered
        if n > 1 and len(bracing_positions) > 0 and self.hovered_top_view_element == 'cross_bracing':
            brace_index = min(6, len(bracing_positions) - 1)
            brace_x_base = bracing_positions[brace_index]
            
            y1 = girder_positions_y[0]
            y2 = girder_positions_y[1]
            
            y1_offset = y1 - girder_positions_y[0]
            y2_offset = y2 - girder_positions_y[0]
            x1 = brace_x_base + y1_offset * math.tan(skew_rad)
            x2 = brace_x_base + y2_offset * math.tan(skew_rad)
            
            target_x = (x1 + x2) / 2
            target_y = (y1 + y2) / 2
            
            label_offset = 30
            label_x = target_x - label_offset * math.sin(skew_rad)
            label_y = target_y - label_offset
            
            self.draw_clean_leader_line(painter, target_x, target_y, label_x, label_y,
                                    "Cross Bracing", CAD_DARK_GREY, CAD_DARK_GREY)
        
        # 3. END DIAPHRAGM label - show only when end diaphragm is hovered
        if n > 1 and len(girder_positions_y) >= 2 and self.hovered_top_view_element == 'end_diaphragm':
            y1 = girder_positions_y[0]
            y2 = girder_positions_y[1]
            
            y1_offset = y1 - girder_positions_y[0]
            y2_offset = y2 - girder_positions_y[0]
            x1 = left_bearing_base_x + y1_offset * math.tan(skew_rad)
            x2 = left_bearing_base_x + y2_offset * math.tan(skew_rad)
            
            target_x = (x1 + x2) / 2
            target_y = (y1 + y2) / 2
            
            label_offset = 10
            label_x = target_x - label_offset - 10
            label_y = target_y + 5
            
            self.draw_clean_leader_line(painter, target_x, target_y, label_x, label_y,
                                    "End Diaphragm", CAD_DARK_GREY, QColor(139, 69, 19))

    def draw_dimension_arrow_with_extensions_up(self, painter, x1, y1, x2, y2, text, girder_y):
        """Dimension line with arrows and extension lines going UP to girder level (dimension below)"""
        painter.setPen(QPen(QColor(0, 0, 0), 0.8))
        
        # Draw main dimension line
        painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        
        # Draw extension lines going UP to girder (y1 > girder_y since dimension is below)
        painter.setPen(QPen(QColor(100, 100, 100), 0.8, Qt.DotLine))
        painter.drawLine(QPointF(x1, y1), QPointF(x1, girder_y))
        painter.drawLine(QPointF(x2, y2), QPointF(x2, girder_y))
        
        # Reset pen for arrows
        painter.setPen(QPen(QColor(0, 0, 0), 0.8))
        
        # Draw end ticks
        ext_len = 6
        painter.drawLine(QPointF(x1, y1 - ext_len), QPointF(x1, y1 + ext_len))
        painter.drawLine(QPointF(x2, y2 - ext_len), QPointF(x2, y2 + ext_len))
        
        # Draw arrows
        arrow_len = 6
        arrow_half = arrow_len / 3

        painter.setBrush(QBrush(QColor(0, 0, 0)))
        
        left_arrow = [
            QPointF(x1, y1),
            QPointF(x1 + arrow_len, y1 - arrow_half),
            QPointF(x1 + arrow_len, y1 + arrow_half)
        ]

        painter.drawPolygon(QPolygonF(left_arrow))
        
        right_arrow = [
            QPointF(x2, y2),
            QPointF(x2 - arrow_len, y2 - arrow_half),
            QPointF(x2 - arrow_len, y2 + arrow_half)
        ]

        painter.drawPolygon(QPolygonF(right_arrow))
        
        # Draw text BELOW the dimension line (above in terms of value since we add to y)
        text_x = (x1 + x2) / 2
        text_y = y1 + DIM_TEXT_GAP  # Below the dimension line
        
        font = QFont('Arial', 9, QFont.Bold)
        painter.setFont(font)
        metrics = painter.fontMetrics()
        text_width = metrics.boundingRect(text).width()
        
        self.draw_text_with_background(painter, text_x - text_width/2, text_y, text, 
                                    QColor(255, 255, 255, 240), QColor(0, 0, 0), 9, True)


    def draw_skewed_dimension_arrow(self, painter, x1, y1, x2, y2, text, skew_rad):
        """Draw a dimension arrow that follows skew angle with horizontal text"""
        painter.setPen(QPen(QColor(0, 0, 0), 0.8))
        
        painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx * dx + dy * dy)
        
        if length == 0:
            return
        
        nx = dx / length
        ny = dy / length
        
        px = -ny
        py = nx
        
        tick_len = 5
        
        painter.drawLine(QPointF(x1 - px * tick_len, y1 - py * tick_len),
                        QPointF(x1 + px * tick_len, y1 + py * tick_len))
        painter.drawLine(QPointF(x2 - px * tick_len, y2 - py * tick_len),
                        QPointF(x2 + px * tick_len, y2 + py * tick_len))
        
        arrow_len = 6
        arrow_half = arrow_len / 3

        painter.setBrush(QBrush(QColor(0, 0, 0)))
        
        angle1 = math.atan2(dy, dx)
        arrow1 = [
            QPointF(x1, y1),
            QPointF(
                x1 + arrow_len * math.cos(angle1) - arrow_half * math.sin(angle1),
                y1 + arrow_len * math.sin(angle1) + arrow_half * math.cos(angle1)
            ),
            QPointF(
                x1 + arrow_len * math.cos(angle1) + arrow_half * math.sin(angle1),
                y1 + arrow_len * math.sin(angle1) - arrow_half * math.cos(angle1)
            )
        ]

        painter.drawPolygon(QPolygonF(arrow1))
        
        angle2 = math.atan2(-dy, -dx)
        arrow2 = [
            QPointF(x2, y2),
            QPointF(
                x2 + arrow_len * math.cos(angle2) - arrow_half * math.sin(angle2),
                y2 + arrow_len * math.sin(angle2) + arrow_half * math.cos(angle2)
            ),
            QPointF(
                x2 + arrow_len * math.cos(angle2) + arrow_half * math.sin(angle2),
                y2 + arrow_len * math.sin(angle2) - arrow_half * math.cos(angle2)
            )
        ]

        painter.drawPolygon(QPolygonF(arrow2))
        
        # Draw text horizontally at midpoint, offset to the right
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        
        text_x = mid_x + DIM_TEXT_GAP
        text_y = mid_y
        
        self.draw_text_with_background(painter, text_x, text_y, text,
                                    QColor(255, 255, 255, 240), QColor(0, 0, 0), 9, True)

    def add_clean_top_view_notes(self, painter, height):
        """Add professional notes"""
        notes_y = height - 160
        
        self.draw_text_with_background(painter, 30, notes_y + 5,
                                    "NOTES:", QColor(240, 245, 250, 250),
                                    QColor(0, 0, 0), 9, True)
        
        notes = [
            f"1. Green lines: Girders (Qty = {self.params['num_girders']})",
            f"2. Orange lines: Cross bracing (ISA 100×100×8)",
            f"3. Brown lines: End diaphragms at bearing locations",
            f"4. Red dashed: Centerline of bearings",
            f"5. Skew angle: {self.params['skew_angle']:.1f}°",
            f"6. All dimensions in meters",
        ]
        
        painter.setFont(QFont('Arial', 9))
        painter.setPen(QPen(QColor(40, 40, 40), 1))
        
        for i, note in enumerate(notes):
            note_y = notes_y + 22 + i * 13
            painter.drawText(32, note_y, note)