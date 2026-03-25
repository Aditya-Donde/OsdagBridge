"""
Cross-Section CAD Widget for OsdagBridge
Handles cross-sectional view rendering of bridge structures
Author: Arushi
"""

import math
from PySide6.QtWidgets import QWidget, QPushButton, QScrollArea
from PySide6.QtCore import Qt, QRectF, QPointF, QTimer
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QBrush, QPolygonF
from PySide6.QtGui import QPixmap
from osdagbridge.desktop.cad.irc5_geometry import (
    CrashBarrierGeometry,
    RailingGeometry,
    MedianGeometry,
)
from osdagbridge.core.utils.common import (
    KEY_WEARING_COAT_THICKNESS,
    KEY_WEARING_COAT_DENSITY,
    KEY_WEARING_COAT_MATERIAL,
)
import random

class CrossSectionCADWidget(QWidget):
    """Widget for drawing bridge cross-section view"""
    # ===== SHARED CAD COLORS =====
    GIRDER_COLOR = QColor(179, 180, 160) 
    STIFFENER_COLOR = QColor(79, 78, 70) 
    CROSS_BRACING_COLOR = QColor(235, 236, 211)
    RAILING_COLOR = QColor(210, 210, 210)
    BARRIER_COLOR = QColor(220, 220, 220)

    
    END_DIAPHRAGM_COLOR = QColor(134, 134, 100)

    CONCRETE_COLOR = QColor(225, 225, 225)
    MEDIAN_COLOR = QColor(221, 221, 221)

    BEARING_COLOR = QColor(255, 0, 0)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.show_dimensions = True
        self.show_span_values = False
        self.show_carriageway_values = False
        self.setMouseTracking(True)  # enable mouse tracking for hover
        self.concrete_brush = self.create_concrete_brush()
        self.crash_barrier_params = {}
        self.crash_barrier_type = "IRC 5 - RCC Crash Barrier"
        self.railing_type = None
        self.median_type = None
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
            'railing_width': 375,
            'median_present': False,
            'median_width': 1200,
        }
        
        # girder dimensions (mm)
        self.girder = {
            'depth': 500,
            'top_flange_width': 180,
            'top_flange_thickness': 22,
            'bottom_flange_width': 180,
            'bottom_flange_thickness': 22,
            'web_thickness': 15,
            # Legacy support for symmetric sections
            'flange_width': 180,
            'flange_thickness': 22,
        }
        
        # stiffener dimensions
        self.stiffener = {
            'width': 312,
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
    
    def _position_zoom_buttons(self):
        """Lock zoom buttons to fixed viewport position - improved version"""
        if not hasattr(self, 'zoom_in_btn'):
            return

        # Find scroll area once
        if self.scroll_area is None:
            parent = self.parent()
            while parent:
                if isinstance(parent, QScrollArea):
                    self.scroll_area = parent
                    # Install event filter on viewport to catch resize events
                    if self.scroll_area.viewport():
                        self.scroll_area.viewport().installEventFilter(self)
                    break
                parent = parent.parent()

        # Return early if scroll area not found yet
        if not self.scroll_area:
            return

        viewport = self.scroll_area.viewport()
        
        # Check if viewport is valid
        if not viewport or viewport.width() == 0:
            return
        
        # Re-parent buttons to viewport if not already
        if self.zoom_in_btn.parent() != viewport:
            self.zoom_in_btn.setParent(viewport)
            self.zoom_out_btn.setParent(viewport)
            self.zoom_reset_btn.setParent(viewport)

        # Position in top-right corner of VIEWPORT
        margin = 10
        x = viewport.width() - 50
        y = margin

        self.zoom_in_btn.move(x + 10, y)
        self.zoom_out_btn.move(x + 10, y + 30)
        self.zoom_reset_btn.move(x, y + 60)

        # Ensure buttons are visible and on top
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


    def showEvent(self, event):
        """Standardize size and center after widget is shown"""
        super().showEvent(event)
        # Check if this is a preview
        is_preview = self.scale_factor < 1.0 if hasattr(self, 'scale_factor') else False
        # Only show zoom buttons and center if NOT a preview
        if not is_preview:
            # Position zoom buttons
            self._position_zoom_buttons()
            # Single-shot timer to center after layout is complete
            QTimer.singleShot(200, self.zoom_reset)
    
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
        # Check if this is a preview
        is_preview = self.scale_factor < 1.0 if hasattr(self, 'scale_factor') else False
        
        if is_preview:
            # For dialog previews, don't force a large minimum size
            # The preview widget will conform to the dialog's layout
            return

        base_width = 1200
        base_height = 800
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
    
    def update_params(self, params: dict):
        self.params.update(params)

        if "span_length" in params:
            self.show_span_values = True

        if "carriageway_width" in params:
            self.show_carriageway_values = True

        if "crash_barrier_type" in params:
            self.crash_barrier_type = params["crash_barrier_type"]
 
        if "railing_type" in params:
            self.railing_type = params["railing_type"]

        if "median_type" in params:
            self.median_type = params["median_type"]

        self.show_dimensions = True
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
        # Position buttons on first paint if not done yet
        if hasattr(self, 'zoom_in_btn') and not hasattr(self, '_buttons_positioned'):
            self._position_zoom_buttons()
            self._buttons_positioned = True
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
            
            font = QFont('Arial', 9, QFont.Normal)
            metrics = painter.fontMetrics()
            text_width = metrics.boundingRect(text).width()
            
            self.draw_text_with_background(painter, text_x - text_width/2, text_y, text, 
                                        QColor(255, 255, 255, 255), QColor(0, 0, 0), 9, False)
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
            
            painter.save()
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

            
            self.draw_text_with_background(painter, text_x, text_y, text,
                                        QColor(255, 255, 255, 255), QColor(0, 0, 0), 9, False)
            painter.restore()

    
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
                
            font = QFont('Arial', 9, QFont.Normal)
            painter.setFont(font)
            metrics = painter.fontMetrics()
            text_width = metrics.boundingRect(text).width()
            
            self.draw_text_with_background(painter, text_x - text_width/2, text_y, text, 
                                        QColor(255, 255, 255, 255), QColor(0, 0, 0), 9, False)
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
                                        QColor(255, 255, 255, 255), QColor(0, 0, 0), 9, False)
        
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
        
        self.draw_text_with_background(painter, from_x - 5, from_y - 5, text, bg_color, text_color, 9, False)
    
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
        font = QFont('Arial', 9, QFont.Normal)
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
                                       QColor(255, 255, 255, 255), text_color, 9, False)
    
    def compute_deck_total_width(self):

        carriageway = self.params.get('carriageway_width', 10500)
        crash_barrier = self.params.get('crash_barrier_width', 500)
        footpath_width = self.params.get('footpath_width', 1500)
        fp_config = self.params.get('footpath_config', 'both')
        median_present = self.params.get('median_present', False)
        median_width = self.params.get('median_width', 1200)
        railing_width = self.params.get('railing_width', 375)

        num_fp = {'both':2, 'left':1, 'right':1, 'none':0}.get(fp_config, 0)

        carriageway_total = carriageway * 2 if median_present else carriageway
        median = median_width if median_present else 0

        deck_total = (
            carriageway_total +
            median +
            2 * crash_barrier +
            num_fp * (footpath_width + railing_width)
        )

        return deck_total, num_fp
    
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

    def draw_median(self, painter, median_start_x, median_end_x, deck_top_y, scale, median_color):
        """Dispatcher for different median types based on IRC 5 geometry"""
        geo = MedianGeometry.get_geometry(self.median_type)
        if not geo:
            return

        if geo["type"] == "kerb":
            self.draw_raised_kerb_median(painter, median_start_x, median_end_x, deck_top_y, scale, median_color, geo)
        elif geo["type"] == "rcc_barrier":
            self.draw_rcc_barrier_median(painter, median_start_x, median_end_x, deck_top_y, scale, median_color, geo)
        elif geo["type"] == "metallic":
            self.draw_metallic_median(painter, median_start_x, median_end_x, deck_top_y, scale, median_color, geo)

    def draw_railing(self, painter, x, y, scale, side):
        """Dispatcher for different railing types based on IRC 5 geometry"""
        geo = RailingGeometry.get_geometry(self.railing_type)
        if not geo:
            # Fallback to existing RCC railing if type is not recognized
            return self.draw_rcc_railing(painter, x, y, scale, side)

        if geo["type"] == "rcc":
            return self.draw_rcc_railing(painter, x, y, scale, side, geo)
        elif geo["type"] == "steel":
            return self.draw_steel_railing(painter, x, y, scale, side, geo)
        
        return self.draw_rcc_railing(painter, x, y, scale, side)

    def draw_rcc_railing(self, painter, x_start, y_base, scale, side='left', geo=None):
        """Draw standard RCC railing based on IRC diagrams"""
        # Dimensions for RCC railing (mm)
        OUTER_WIDTH_MM = self.params.get('railing_width', 375)
        RAILING_HEIGHT_MM = self.params.get('railing_height', 1000)
        INNER_SPACING_MM = 275 # Default for RCC
        BASE_THICKNESS_MM = 100 # Default for RCC
        
        wall_thickness_mm = (OUTER_WIDTH_MM - INNER_SPACING_MM) / 2
        
        total_h = RAILING_HEIGHT_MM * scale
        outer_w = max(4, OUTER_WIDTH_MM * scale)
        inner_w = max(2, INNER_SPACING_MM * scale)
        base_h = max(3, BASE_THICKNESS_MM * scale)
        wall_t = max(1, wall_thickness_mm * scale)
        
        post_h = total_h - base_h
        
        rect_x = x_start
        base_top_y = y_base - base_h
        post_top_y = y_base - total_h
        
        corner_radius = min(outer_w * 0.05, 4)
        
        painter.setBrush(QBrush(QColor(220, 220, 220))) # Light grey base
        painter.setPen(QPen(QColor(34, 34, 34), max(1.5, scale * 2)))
        base_rect = QRectF(rect_x, base_top_y, outer_w, base_h)
        painter.drawRect(base_rect)
        
        painter.setBrush(QBrush(QColor(220, 220, 220))) # Light grey post body
        painter.setPen(QPen(QColor(34, 34, 34), max(1.5, scale * 2)))
        post_rect = QRectF(rect_x, post_top_y, outer_w, post_h)
        painter.drawRoundedRect(post_rect, corner_radius, corner_radius)
        
        inner_x = rect_x + wall_t
        inner_top_margin = post_h * 0.03
        inner_bottom_margin = post_h * 0.03
        inner_height = post_h - inner_top_margin - inner_bottom_margin
        
        if inner_w > 3 and inner_height > 5:
            # Removed inner rectangle lining as requested
            
            n_voids = 3
            void_w = inner_w * 0.7
            void_h = void_w # Make them squares
            
            # Vertical spacing to distribute voids evenly
            void_spacing = (inner_height - n_voids * void_h) / (n_voids + 1)
            
            painter.setBrush(QBrush(QColor(170, 170, 170))) # Dark grey
            painter.setPen(QPen(QColor(30, 30, 30), max(1, scale)))
            
            for i in range(n_voids):
                v_y = post_top_y + inner_top_margin + (i + 1) * void_spacing + i * void_h
                v_x = inner_x + (inner_w - void_w) / 2
                void_rect = QRectF(v_x, v_y, void_w, void_h)
                
                # Apply rounded corners to voids
                v_radius = corner_radius * 0.8
                painter.drawRoundedRect(void_rect, v_radius, v_radius)
        
        return (rect_x, post_top_y, rect_x + outer_w, y_base, outer_w)

    def draw_steel_railing(self, painter, x, y, scale, side, geo):
        """Draw Steel railing with:
        - Concrete base: 100mm height, 375mm width
        - Steel posts: 150mm x 150mm
        - Steel rails: 40mm x 40mm (Top and Mid)
        """
        RAILING_HEIGHT_MM = geo.get("height", 1100)
        BASE_HEIGHT_MM = geo.get("base_height", 100)
        BASE_WIDTH_MM = geo.get("base_width", 375)
        POST_SIZE_MM = geo.get("post_size", 150)
        RAIL_SIZE_MM = geo.get("rail_size", 20)
        
        total_h = RAILING_HEIGHT_MM * scale
        base_h = max(3, BASE_HEIGHT_MM * scale)
        base_w = max(4, BASE_WIDTH_MM * scale)
        post_size = max(2, POST_SIZE_MM * scale)
        rail_size = max(1, RAIL_SIZE_MM * scale)
        
        rect_x = x
        base_top_y = y - base_h
        railing_top_y = y - total_h
        
        # 1. Concrete Base
        painter.setBrush(QBrush(QColor(126, 126, 126)))
        painter.setPen(QPen(QColor(34, 34, 34), max(1.5, scale * 2)))
        base_rect = QRectF(rect_x, base_top_y, base_w, base_h)
        painter.drawRect(base_rect)
        
        # 2. Steel Post (center aligned on base in cross-section)
        post_x = rect_x + (base_w - post_size) / 2
        post_h = total_h - base_h
        
        # Draw post outline only (no fill) so areas between rails are transparent
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(30, 30, 30), max(1.5, scale * 2)))
        post_rect = QRectF(post_x, railing_top_y, post_size, post_h)
        painter.drawRect(post_rect)
        
        # 3. Rails
        # Top Rail (positioned relative to total railing height)
        top_rail_y = railing_top_y + rail_size # Slightly down from very top 
        top_rail_rect = QRectF(post_x, top_rail_y, post_size, rail_size)
        painter.setBrush(QBrush(QColor(80, 80, 80)))
        painter.drawRect(top_rail_rect)
        
        # Mid Rail
        mid_rail_y = base_top_y - (post_h * 0.5) - rail_size / 2
        mid_rail_rect = QRectF(post_x, mid_rail_y, post_size, rail_size)
        painter.drawRect(mid_rail_rect)
        
        return (rect_x, railing_top_y, rect_x + base_w, y, base_w)

    def draw_raised_kerb_median(self, painter, median_start_x, median_end_x, deck_top_y, scale, median_color, geo):
        """Draw Raised Kerb median (trapezoid shape)"""
        h = geo.get("kerb_height", 225) * scale
        top_w = geo.get("kerb_top_width", 1200) * scale
        bottom_w = geo.get("kerb_bottom_width", 1200) * scale
        
        median_width_px = median_end_x - median_start_x
        offset = (median_width_px - bottom_w) / 2
        
        y_bottom = deck_top_y
        y_top = deck_top_y - h
        
        x_bl = median_start_x + offset
        x_br = x_bl + bottom_w
        x_tl = x_bl + (bottom_w - top_w) / 2
        x_tr = x_tl + top_w
        
        points = [QPointF(x_bl, y_bottom), QPointF(x_br, y_bottom), QPointF(x_tr, y_top), QPointF(x_tl, y_top)]
        
        if self.hovered_element == 'median':
            painter.setBrush(QBrush(QColor(255, 250, 220)))
        else:
            painter.setBrush(QBrush(median_color))
            
        painter.setPen(QPen(QColor(0, 0, 0), max(1.5, scale * 1.5)))
        painter.drawPolygon(QPolygonF(points))
        
        hover_rect = QRectF(median_start_x, y_top, median_width_px, h)
        self.cross_section_hover_zones.append((hover_rect, 'median'))

    def draw_rcc_barrier_median(self, painter, median_start_x, median_end_x, deck_top_y, scale, median_color, geo):
        """Draw two RCC crash barriers for median following standard shape"""
        barrier_h_mm = geo.get("barrier_height", 900.0)
        bottom_w_mm = geo.get("bottom_width", 450.0)
        top_w_mm = geo.get("top_width", 175.0)
        
        h = barrier_h_mm * scale
        bottom_w = bottom_w_mm * scale
        median_width_px = median_end_x - median_start_x
        
        # Shape offsets proportional to standard HC barrier (350mm bottom)
        shape_scale = bottom_w_mm / 350.0
        base_v = 100.0 * scale
        mid_y_off = 350.0 * scale
        right_at_mid = 250.0 * scale * shape_scale
        left_at_top = 50.0 * scale * shape_scale
        right_at_top = 225.0 * scale * shape_scale
        
        y_bottom = deck_top_y
        y_base_top = y_bottom - base_v
        y_mid = y_bottom - mid_y_off
        y_top = y_bottom - h
        
        barrier_brush = QBrush(QColor(255, 250, 220)) if self.hovered_element == 'median' else QBrush(QColor(220, 220, 220))
        painter.setBrush(barrier_brush)
        painter.setPen(QPen(Qt.black, max(1.5, scale * 1.5)))
        
        # LEFT assembly (faces LEFT)
        x_l = median_start_x + bottom_w
        points_l = [
            QPointF(x_l - bottom_w, y_bottom), QPointF(x_l, y_bottom), QPointF(x_l, y_base_top),
            QPointF(x_l - left_at_top, y_top), QPointF(x_l - right_at_top, y_top),
            QPointF(x_l - right_at_mid, y_mid), QPointF(x_l - bottom_w, y_base_top)
        ]
        painter.drawPolygon(QPolygonF(points_l))
        
        # RIGHT assembly (faces RIGHT)
        x_r = median_end_x - bottom_w
        points_r = [
            QPointF(x_r, y_bottom), QPointF(x_r + bottom_w, y_bottom), QPointF(x_r + bottom_w, y_base_top),
            QPointF(x_r + right_at_mid, y_mid), QPointF(x_r + right_at_top, y_top),
            QPointF(x_r + left_at_top, y_top), QPointF(x_r, y_base_top)
        ]
        painter.drawPolygon(QPolygonF(points_r))
        
        hover_rect = QRectF(median_start_x, y_top, median_width_px, h)
        self.cross_section_hover_zones.append((hover_rect, 'median'))

    def draw_metallic_median(self, painter, median_start_x, median_end_x, deck_top_y, scale, median_color, geo):
        """Draw Metallic median with a common kerb base and beams on both sides"""
        post_h_mm = geo.get("post_height", 950)
        n_beams = geo.get("w_beams", 1)
        median_width_mm = geo.get("median_width", 1200)
        median_width_px = median_end_x - median_start_x
        
        kerb_h_mm = 225.0
        h_kerb = kerb_h_mm * scale
        top_w = (median_width_mm - 50.0) * scale
        bottom_w = median_width_mm * scale
        post_h = post_h_mm * scale
        
        y_bottom = deck_top_y
        y_top_kerb = deck_top_y - h_kerb
        x_bl, x_br = median_start_x, median_end_x
        x_tl = x_bl + (bottom_w - top_w) / 2
        x_tr = x_tl + top_w
        
        painter.setBrush(QBrush(QColor(220, 220, 220)))
        painter.setPen(QPen(Qt.black, max(1.0, scale)))
        painter.drawPolygon(QPolygonF([QPointF(x_bl, y_bottom), QPointF(x_br, y_bottom), QPointF(x_tr, y_top_kerb), QPointF(x_tl, y_top_kerb)]))
        
        post_w, post_offset = 150.0 * scale, 75.0 * scale
        spacer_w, spacer_h = 200.0 * scale, 330.0 * scale
        w_beam_h, w_beam_depth, w_beam_thk = 330.0 * scale, 83.0 * scale, 3.0 * scale
        post_color = QColor(255, 250, 220) if self.hovered_element == 'median' else QColor(220, 220, 220)
        
        def draw_side_assembly(is_left):
            # Assembly on Left side of median (near x_tl): [Beam] [Spacer] [Post] -> Facing left carriageway
            # Assembly on Right side of median (near x_tr): [Post] [Spacer] [Beam] -> Facing right carriageway
            
            if is_left:
                # x_tl is the left kerb end. Order: Beam (outer), Spacer (mid), Post (inner)
                b_root_x = x_tl + w_beam_depth
                s_x = x_tl + w_beam_depth
                p_x = s_x + spacer_w
            else:
                # x_tr is the right kerb end. Order: Post (inner), Spacer (mid), Beam (outer)
                b_root_x = x_tr - w_beam_depth
                s_x = b_root_x - spacer_w
                p_x = s_x - post_w

            # Draw Post
            painter.setBrush(QBrush(post_color))
            painter.setPen(QPen(Qt.black, 1))
            painter.drawRect(QRectF(p_x, y_top_kerb - post_h, post_w, post_h))
            
            h_centers = [post_h_mm - 165] if n_beams == 1 else [post_h_mm - 165, post_h_mm - 165 - 145 - 330]
            for hc_mm in h_centers:
                sy = y_top_kerb - hc_mm * scale - spacer_h / 2
                
                # Draw Spacer
                painter.setBrush(QBrush(post_color))
                painter.drawRect(QRectF(s_x, sy, spacer_w, spacer_h))
                
                # Draw W-Beam Profile (Wave)
                num_pts = 15
                outer_wave, inner_wave = [], []
                for i in range(num_pts + 1):
                    z_rel = (i / num_pts) * w_beam_h
                    wave_val = (w_beam_depth * 1.5) * (math.exp(-((z_rel - w_beam_h*0.25)**2)/(2*(w_beam_h/10)**2)) + math.exp(-((z_rel - w_beam_h*0.75)**2)/(2*(w_beam_h/10)**2)))
                    curr_y = sy + (w_beam_h - z_rel)
                    
                    if is_left:
                        wx = b_root_x - wave_val  # Faces LEFT
                        outer_wave.append(QPointF(wx, curr_y))
                        inner_wave.insert(0, QPointF(wx + w_beam_thk, curr_y))
                    else:
                        wx = b_root_x + wave_val  # Faces RIGHT
                        outer_wave.append(QPointF(wx, curr_y))
                        inner_wave.insert(0, QPointF(wx - w_beam_thk, curr_y))
                
                painter.setBrush(QBrush(QColor(120, 120, 120)))
                painter.drawPolygon(QPolygonF(outer_wave + inner_wave))

        draw_side_assembly(True)
        draw_side_assembly(False)
        hover_rect = QRectF(median_start_x, y_top_kerb - post_h, median_width_px, post_h + h_kerb)
        self.cross_section_hover_zones.append((hover_rect, 'median'))

    def draw_median_crash_barriers(self, painter, median_start_x, median_end_x, deck_top_y, scale, median_color):
        """DEPRECATED: Use draw_rcc_barrier_median or dispatcher instead."""
        pass
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
        # ---- Register hover zone for median ----
        hover_rect = QRectF(
            median_start_x,
            y_top,
            median_end_x - median_start_x,
            h
        )
        self.cross_section_hover_zones.append((hover_rect, 'median'))

    def draw_cross_section(self, painter):
        """Draw cross-section with median support and hover highlighting"""
        
        GIRDER_COLOR = QColor(130, 130, 130)
        STIFFENER_COLOR = QColor(210, 210, 205)
        CROSS_BRACING_COLOR = QColor(250, 240, 211)
        RAILING_COLOR = QColor(225, 225, 225)
        BARRIER_COLOR = QColor(220, 220, 220)


        MEDIAN_GREY = QColor(221, 221, 221) 
        CONCRETE_COLOR = QColor(225, 225, 225)

        END_DIAPHRAGM_COLOR = QColor(134, 134, 100)
        BARRIER_GREY = QColor(221, 221, 221)  # slightly dark grey
        RAILING_GREY = QColor(221, 221, 221)
        
        is_preview = self.scale_factor < 1.0 if hasattr(self, 'scale_factor') else False

        if is_preview:
            # Fit inside the actual widget dimensions for the dialog preview
            width = self.width()
            height = self.height()
        else:
            base_width = 1200
            base_height = 800
            width = base_width * self.zoom_level
            height = base_height * self.zoom_level

        fp_config = self.params.get('footpath_config', 'both')
        left_fp_width = self.params['footpath_width'] if fp_config in ['left', 'both'] else 0
        right_fp_width = self.params['footpath_width'] if fp_config in ['right', 'both'] else 0

        total_deck_width, num_fp = self.compute_deck_total_width()

        # Reduced margins for better space utilization
        margin_x = 10 if is_preview else 80
        margin_y = 10 if is_preview else 80
        
        scale_x = (width - 2 * margin_x) / total_deck_width
        scale_y = (height - 2 * margin_y - (40 if is_preview else 80)) / (self.girder['depth'] * self.girder_visual_scale['depth'] +
                                                self.params['deck_thickness'] +
                                                self.params['footpath_thickness'] + 1500)
        
        scale = min(scale_x, scale_y)
        
        # Apply scale factor for size adjustment (zoom_level already applied to width/height)
        scale = scale * self.scale_factor
        
        DIM_OFFSET = 510 * scale
        DIM_OFFSET_SMALL = 588 * scale

        center_x = self.width() / 2
        # Position bridge in the center vertically
        total_bridge_height = (self.girder['depth'] * scale * self.girder_visual_scale['depth'] +
                              self.params['deck_thickness'] * scale +
                              self.params['footpath_thickness'] * scale +
                              self.crash_barrier['height'] * scale + 
                              self.railing['height'] * scale)
        
        # Ensure proper positioning
        if is_preview:
            # Perfectly center within the preview height, slightly shifted up for bottom labels
            base_y = (height + total_bridge_height) / 2 - 20
        else:
            base_y = (height + total_bridge_height) / 2 - 70

        girder_depth_visual = self.girder['depth'] * scale * self.girder_visual_scale['depth']
        girder_top_y = base_y - girder_depth_visual
        deck_thick_px = self.params['deck_thickness'] * scale
        fp_thick_px = self.params['footpath_thickness'] * scale
        deck_bottom_y = girder_top_y
        deck_top_y = deck_bottom_y - deck_thick_px
        
        '''# ===== WEARING COURSE =====
        wc_thickness_mm = self.params.get(KEY_WEARING_COAT_THICKNESS, 0)
        wc_thickness_px = wc_thickness_mm * scale

        wc_bottom_y = deck_top_y
        wc_top_y = wc_bottom_y - wc_thickness_px'''
        
        fp_bottom_y = deck_bottom_y
        fp_top_y = fp_bottom_y - fp_thick_px

        deck_start_x = center_x - (total_deck_width * scale) / 2
        deck_left_x = deck_start_x
        deck_right_x = deck_start_x + total_deck_width * scale
        
        # Calculate all widths in pixels
        railing_width_px = self.params['railing_width'] * scale
        crash_barrier_width_px = self.params['crash_barrier_width'] * scale
        left_fp_width_px = left_fp_width * scale
        right_fp_width_px = right_fp_width * scale
        
        # LAYOUT FROM LEFT TO RIGHT
        left_railing_present = (fp_config in ['left', 'both'])
        right_railing_present = (fp_config in ['right', 'both'])
        
        left_rail_w_px = railing_width_px if left_railing_present else 0
        right_rail_w_px = railing_width_px if right_railing_present else 0

        # 1. Left footpath starts after left railing (if exists)
        left_fp_x = deck_left_x + left_rail_w_px
        
        # 2. Left crash barrier starts after left footpath clear width
        left_barrier_x = left_fp_x + left_fp_width_px
        left_barrier_end_x = left_barrier_x + crash_barrier_width_px
        
        # 3. Right footpath starts after right crash barrier and ends before right railing (if exists)
        right_fp_x = deck_right_x - right_rail_w_px - right_fp_width_px
        
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

        # Draw deck slab
        railing_outer_width_px = self.params.get('railing_width', 375) * scale
        railing_width_px = railing_outer_width_px

        # Draw deck slab
        deck_slab_left = deck_left_x
        deck_slab_right = deck_right_x
        
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
            
        '''if wc_thickness_px > 0 and not median_present:
            painter.setBrush(QBrush(QColor(90, 90, 90)))
            painter.setPen(Qt.NoPen)

            painter.drawRect(QRectF(
                carriageway_start_x,
                wc_top_y,
                carriageway_end_x - carriageway_start_x,
                wc_thickness_px
            ))
            
        if wc_thickness_px > 0 and median_present:
            painter.setBrush(QBrush(QColor(90, 90, 90)))
            painter.setPen(Qt.NoPen)

            # Left carriageway wearing course
            painter.drawRect(QRectF(
                carriageway_start_x,
                wc_top_y,
                median_start_x - carriageway_start_x,
                wc_thickness_px
            ))

            # Right carriageway wearing course
            painter.drawRect(QRectF(
                median_end_x,
                wc_top_y,
                carriageway_end_x - median_end_x,
                wc_thickness_px
            ))
            
        if wc_thickness_px > 0:
            wc_hover_rect = QRectF(
                carriageway_start_x,
                wc_top_y,
                carriageway_end_x - carriageway_start_x,
                wc_thickness_px
            )
            self.cross_section_hover_zones.append((wc_hover_rect, 'wearing_course'))'''
        
        # Register hover zone for deck - full width
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
            # Draw footpath fill only SIT ON TOP of the main slab
            painter.setBrush(self.concrete_brush)

            painter.setPen(Qt.NoPen)
            # sit one pixel higher or precisely on top y edge
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
        #cb_y = deck_top_y - 1
        # Left barrier: x is where it STARTS (left edge)
        #self.draw_crash_barrier(painter, left_barrier_x, cb_y, scale, side='left')
        # Right barrier: x is where it ENDS (right edge) = right_barrier_end_x
        #self.draw_crash_barrier(painter, right_barrier_end_x, cb_y, scale, side='right')
        
        if median_present:
            self.draw_median(painter, median_start_x, median_end_x, deck_top_y, scale, MEDIAN_GREY)

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
        # painter.setPen(QPen(QColor(0, 0, 0), 1.0, Qt.DashLine))
        # painter.setBrush(Qt.NoBrush)

        # for girder_x in positions:
        #     painter.drawLine(
        #         QPointF(girder_x, base_y),
        #         QPointF(girder_x, deck_bottom_y)
        #     )
            
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


            
            '''# Mid of top & bottom flange (REFERENCE POINTS)
            top_flange_mid_y = girder_top_edge + tf_top / 2
            bottom_flange_mid_y = girder_bottom_edge - tf_bottom / 2
            # --- Correct connection points (flange-web junction) ---
            top_connection_y = girder_top_edge + tf_top + (0.02 * girder_depth_visual)
            bottom_connection_y = girder_bottom_edge - tf_bottom + (0.02 * girder_depth_visual)'''


            
            
        for i in range(n - 1):
            # Web offset
            web_thickness_px = (
                self.girder['web_thickness'] * scale *
                self.girder_visual_scale['web_thickness']
            )
            half_web = web_thickness_px / 2.0

            # X locations
            x1 = positions[i]     + half_web
            x2 = positions[i + 1] - half_web

            # Girder edges
            girder_top_left    = base_y  - girder_depth_visual
            girder_bottom_left = base_y - bf_thickness

            girder_top_right    = base_y - girder_depth_visual
            girder_bottom_right = base_y - bf_thickness

            # Connection points
            top_L    = girder_top_left    + tf_top    + 0.02 * girder_depth_visual
            bottom_L = girder_bottom_left - tf_bottom + 0.02 * girder_depth_visual

            top_R    = girder_top_right    + tf_top    + 0.02 * girder_depth_visual
            bottom_R = girder_bottom_right - tf_bottom + 0.02 * girder_depth_visual

            # Geometry vector (true bracing direction)
            dx = x2 - x1
            thickness = 3.5 * (self.zoom_level / 1.2)

            # ===== CROSS BRACING (\) =====
            dy_bs = bottom_R - top_L
            L_bs = math.hypot(dx, dy_bs)
            if L_bs > 0:
                perp_x_bs = -dy_bs / L_bs
                perp_y_bs = dx / L_bs
                
                off_x_bs = perp_x_bs * thickness / 2
                off_y_bs = perp_y_bs * thickness / 2
                
                p1 = QPointF(x1 + off_x_bs, top_L    + off_y_bs)
                p2 = QPointF(x2 + off_x_bs, bottom_R + off_y_bs)
                p3 = QPointF(x2 - off_x_bs, bottom_R - off_y_bs)
                p4 = QPointF(x1 - off_x_bs, top_L    - off_y_bs)

                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(CROSS_BRACING_COLOR))
                painter.drawPolygon(QPolygonF([p1, p2, p3, p4]))

                painter.setPen(QPen(CROSS_BRACING_COLOR.darker(220), 1.5))
                painter.drawLine(p1, p2)
                painter.drawLine(p4, p3)

            # ===== CROSS BRACING (/) =====
            dy_sl = top_R - bottom_L
            L_sl = math.hypot(dx, dy_sl)
            if L_sl > 0:
                perp_x_sl = -dy_sl / L_sl
                perp_y_sl = dx / L_sl
                
                off_x_sl = perp_x_sl * thickness / 2
                off_y_sl = perp_y_sl * thickness / 2
                
                p1 = QPointF(x1 + off_x_sl, bottom_L + off_y_sl)
                p2 = QPointF(x2 + off_x_sl, top_R    + off_y_sl)
                p3 = QPointF(x2 - off_x_sl, top_R    - off_y_sl)
                p4 = QPointF(x1 - off_x_sl, bottom_L - off_y_sl)

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
            left_railing_rect = self.draw_railing(painter, railing_x, fp_top_y, scale, "left")
            
        if fp_config in ['right', 'both'] and right_fp_width > 0:
            railing_x = deck_right_x - railing_outer_width_px
            right_railing_rect = self.draw_railing(painter, railing_x, fp_top_y, scale, "right")
        # Draw crash barriers
        cb_y = deck_top_y
        # Left barrier: x is where it STARTS (left edge)
        self.draw_crash_barrier(painter, left_barrier_x, cb_y, scale, side='left')
        # Right barrier: x is where it ENDS (right edge) = right_barrier_end_x
        self.draw_crash_barrier(painter, right_barrier_end_x, cb_y, scale, side='right')
        # Add dimensions
        if self.show_dimensions:
            self.add_professional_cross_section_dimensions(
                painter, deck_left_x, deck_right_x, carriageway_start_x, carriageway_end_x,
                left_barrier_x, right_barrier_x, deck_top_y, deck_bottom_y, fp_top_y,
                base_y, scale, positions, n, fp_config, left_fp_width, right_fp_width,
                left_fp_x, right_fp_x, railing_width_px, girder_depth_visual,
                median_present, median_start_x, median_end_x, median_width,
                crash_barrier_width_px, left_barrier_end_x, right_barrier_end_x,
                DIM_OFFSET, DIM_OFFSET_SMALL
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
        
        # Calculate barrier positions if not passed
        if crash_barrier_width_px is None:
            crash_barrier_width_px = self.params['crash_barrier_width'] * scale
        if left_barrier_end_x is None:
            left_barrier_end_x = left_barrier_x + crash_barrier_width_px
        if right_barrier_end_x is None:
            right_barrier_end_x = right_barrier_x + crash_barrier_width_px
        
        # Left barrier starts at left_barrier_x and extends RIGHT by crash_barrier_width_px
        left_barrier_visual_end = left_barrier_x + crash_barrier_width_px
        
        # Right barrier ENDS at right_barrier_end_x and extends LEFT by crash_barrier_width_px
        right_barrier_visual_start = right_barrier_end_x - crash_barrier_width_px

        
        # DIMENSION LEVELS (Bottom)
        Y_OVERHANG = base_y + 35
        Y_GIRDER_SPACING = base_y + 35
        Y_OVERALL = base_y + 70
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
        label_text = "Overall Bridge Width"
        if self.show_carriageway_values:
            label_text += f" = {total_width_m:.2f} m"

        font = QFont('Arial', 9, QFont.Normal)
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
            False
        )

        # LEVEL 2: Footpath dimensions
        left_railing_present = (fp_config in ['left', 'both'])
        right_railing_present = (fp_config in ['right', 'both'])
        left_rail_w_px = railing_width_px if left_railing_present else 0
        right_rail_w_px = railing_width_px if right_railing_present else 0

        Y_TOP_COMMON = deck_top_y - (3.2 * DIM_OFFSET)
        
        if left_railing_present and left_fp_width > 0:
            fp_start_x = deck_left_x + left_rail_w_px
            fp_end_x = left_barrier_x
            fp_visible_mm = (fp_end_x - fp_start_x) / scale
            fp_visible_mm = round(fp_visible_mm, 1)

            fp_visible_m = round(fp_visible_mm / 1000.0, 2)
            if fp_visible_m > 0:
                label_text = "Footpath Width"
                if self.show_carriageway_values:
                    label_text += f" = {fp_visible_m:.2f} m"
                
                self.draw_dimension_arrow(painter, fp_start_x, Y_TOP_COMMON, 
                                        fp_end_x, Y_TOP_COMMON,
                                        label_text, True, 
                                        extension_direction='down',
                                        extension_end_y=fp_top_y)
        
        # LEVEL 2c: Carriageway/Median Dimensions
        # Already defined above as Y_TOP_COMMON
    
        actual_cw_start = left_barrier_visual_end
        actual_cw_end = right_barrier_visual_start
        
        if median_present and median_start_x is not None and median_end_x is not None:
            cw_m = self.params['carriageway_width'] / 1000
            
            # Left carriageway - starts exactly at left barrier visual end
            label_cw = "Carriageway"
            if self.show_carriageway_values:
                label_cw += f" = {cw_m:.2f} m"
            
            self.draw_dimension_arrow(painter, actual_cw_start, Y_TOP_COMMON, median_start_x, Y_TOP_COMMON,
                                    label_cw, True, 
                                    extension_direction='down',
                                    extension_end_y=deck_top_y)
            
            # Median dimension
            median_m = median_width / 1000
            label_median = "Median"
            if self.show_carriageway_values:
                label_median += f" = {median_m:.2f} m"
                
            self.draw_dimension_arrow(painter, median_start_x, Y_TOP_COMMON - 35, median_end_x, Y_TOP_COMMON - 35,
                                    label_median, True, 
                                    extension_direction='down',
                                    extension_end_y=deck_top_y)
            
            # Right carriageway - ends exactly at right barrier visual start
            self.draw_dimension_arrow(painter, median_end_x, Y_TOP_COMMON, actual_cw_end, Y_TOP_COMMON,
                                    label_cw, True, 
                                    extension_direction='down',
                                    extension_end_y=deck_top_y)
        else:
            # Single carriageway
            cw_m = self.params['carriageway_width'] / 1000
            # From left barrier visual end to right barrier visual start
            label_cw = "Carriageway Width"
            if self.show_carriageway_values:
                label_cw += f" = {cw_m:.2f} m"
            
            self.draw_dimension_arrow(painter, actual_cw_start, Y_TOP_COMMON, actual_cw_end, Y_TOP_COMMON,
                                    label_cw, True, 
                                    extension_direction='down',
                                    extension_end_y=deck_top_y)
        
        # Right footpath dimension
        if right_railing_present and right_fp_width > 0:
            fp_start_x = right_barrier_end_x
            fp_end_x = deck_right_x - right_rail_w_px
            fp_visible_mm = (fp_end_x - fp_start_x) / scale
            fp_visible_mm = round(fp_visible_mm, 1)

            fp_visible_m = round(fp_visible_mm / 1000.0, 2)
            if fp_visible_m > 0:
                label_fp = "Footpath Width"
                if self.show_carriageway_values:
                    label_fp += f" = {fp_visible_m:.2f} m"
                
                self.draw_dimension_arrow(painter, fp_start_x, Y_TOP_COMMON, 
                                        fp_end_x, Y_TOP_COMMON,
                                        label_fp, True, 
                                        extension_direction='down',
                                        extension_end_y=fp_top_y)
        
        # LEVEL 3: Below bridge - Overhang
        #y_level3 = base_y + 30  # Moved up
        Y_BOTTOM_COMMON = base_y + (1.2 * DIM_OFFSET)
        
        if n > 0 and len(positions) > 0:
            first_girder_x = positions[0]
            overhang_m = self.params.get('deck_overhang', 1000) / 1000
            label_overhang = "Overhang"
            if self.show_carriageway_values:
                label_overhang += f" = {overhang_m:.2f} m"
                
            self.draw_dimension_arrow(painter, deck_left_x, Y_OVERHANG, first_girder_x, Y_OVERHANG,
                                    label_overhang, True,
                                    extension_direction='up',
                                    extension_end_y=deck_bottom_y)
        
        # Girder spacing
        if n > 1 and len(positions) >= 2:
            # Shift to second pair if available to avoid overlap with overhang label
            if n > 2:
                x_left = positions[1]
                x_right = positions[2]
            else:
                x_left = positions[0]
                x_right = positions[1]
                
            gs_m = self.params['girder_spacing'] / 1000
            label_gs = "Girder Spacing"
            if self.show_carriageway_values:
                label_gs += f" = {gs_m:.2f} m"
                
            self.draw_dimension_arrow(painter, x_left, Y_GIRDER_SPACING, x_right, Y_GIRDER_SPACING,
                                    label_gs, True, 
                                    extension_direction='up',
                                    extension_end_y=base_y)
        
        # FOOTPATH THICKNESS DIMENSION 
        fp_t_mm = self.params['footpath_thickness']
        
        if fp_config in ['left', 'both'] and left_fp_width > 0 and fp_thick_px > 5:
            x_dim = deck_left_x - 8
            label_ft = "Footpath\nThickness"
            if self.show_carriageway_values:
                label_ft += f" = {fp_t_mm:.0f} mm"
            self.draw_vertical_dimension_with_arrow(painter, x_dim, fp_top_y, deck_bottom_y,
                                                    label_ft, 'left')
        
        if fp_config == 'right' and right_fp_width > 0 and fp_thick_px > 5:
            x_dim = deck_right_x + 8
            label_ft = "Footpath\nThickness"
            if self.show_carriageway_values:
                label_ft += f" = {fp_t_mm:.0f} mm"
            self.draw_vertical_dimension_with_arrow(painter, x_dim, fp_top_y, deck_bottom_y,
                                                    label_ft, 'right')
        
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
            text = "Deck Thickness"
            if self.show_carriageway_values:
                text += f" = {deck_t_mm:.0f} mm"
            font = QFont('Arial', 9, QFont.Normal)
            painter.setFont(font)
            metrics = painter.fontMetrics()
            text_width = metrics.boundingRect(text).width()
            text_x = deck_center_x - text_width / 2
            text_y = deck_top_y - 8
            
            self.draw_text_with_background(painter, text_x, text_y, text,
                                        QColor(255, 255, 255, 255), QColor(0, 0, 0), 9, False)
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
        
        # Median - text on top of figure (like railing or crash barrier)
        if median_present and median_start_x is not None:
            # Get actual median height for correct label positioning
            m_geo = MedianGeometry.get_geometry(self.median_type)
            m_h = 0
            if m_geo:
                if m_geo.get("type") == "kerb":
                    m_h = m_geo.get("kerb_height", 225) * scale
                elif m_geo.get("type") == "rcc_barrier":
                    m_h = m_geo.get("barrier_height", 900) * scale
                elif m_geo.get("type") == "metallic":
                    m_h = m_geo.get("post_height", 950) * scale
            
            if m_h == 0:
                m_h = cb_height # Fallback

            median_rect = QRectF(
                median_start_x,
                deck_top_y - m_h,
                median_end_x - median_start_x,
                m_h
            )
            median_center_x = (median_start_x + median_end_x) / 2
            median_top_y = deck_top_y - m_h

            components.append((
                median_rect,
                "Median",
                median_center_x,
                median_top_y,
                'on_figure_top',
                None
            ))
        
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
                font = QFont('Arial', 9, QFont.Normal)
                painter.setFont(font)
                metrics = painter.fontMetrics()
                text_width = metrics.boundingRect(name).width()
                text_height = metrics.height()
                
                text_x = target_x - text_width / 2
                text_y = target_y - 5
                
                self.draw_text_with_background(painter, text_x, text_y, name,
                                            QColor(255, 255, 255, 220), QColor(60, 60, 60), 9, False)
            
            elif label_type == 'straight_line':
                painter.setPen(QPen(QColor(100, 100, 100), 1.0, Qt.DotLine))
                painter.drawLine(QPointF(target_x, target_y), QPointF(target_x, label_line_y))
                
                painter.setPen(QPen(QColor(100, 100, 100), 1.5))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(QPointF(target_x, target_y), 3, 3)
                
                font = QFont('Arial', 9, QFont.Normal)
                painter.setFont(font)
                metrics = painter.fontMetrics()
                text_width = metrics.boundingRect(name).width()
                
                text_x = target_x - text_width / 2
                text_y = label_line_y + 6
                
                self.draw_text_with_background(painter, text_x, text_y, name,
                                            QColor(255, 255, 255, 255), QColor(60, 60, 60), 9, False)
            
            elif label_type == 'tilted_line_left':
                label_x = target_x - 25
                label_y = label_line_y - 30
                
                painter.setPen(QPen(QColor(100, 100, 100), 1.0, Qt.DotLine))
                painter.drawLine(QPointF(target_x, target_y), QPointF(label_x, label_y))
                
                painter.setPen(QPen(QColor(100, 100, 100), 1.5))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(QPointF(target_x, target_y), 3, 3)
                
                font = QFont('Arial', 9, QFont.Normal)
                painter.setFont(font)
                metrics = painter.fontMetrics()
                text_width = metrics.boundingRect(name).width()
                
                text_x = label_x - text_width - 5
                text_y = label_y + 4
                
                self.draw_text_with_background(painter, text_x, text_y, name,
                                            QColor(255, 255, 255, 255), QColor(60, 60, 60), 9, False)
            
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
        font = QFont('Arial', 9, QFont.Normal)
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

        '''stiff_w = (
            (min(self.girder['top_flange_width'], self.girder['bottom_flange_width'])
            - self.girder['web_thickness']) / 2
        ) * scale * visual['web_thickness'] '''
        stiff_w = self.stiffener['width'] * scale

        stiff_h = (
            self.girder['depth']
            - self.girder['top_flange_thickness']
            - self.girder['bottom_flange_thickness']
        ) * scale * visual['depth']

        tw = self.girder['web_thickness'] * scale * visual['web_thickness']

        # Flange thickness (top) — MUST match depth scaling
        if 'top_flange_thickness' in self.girder:
            flange_thick = self.girder['top_flange_thickness'] * scale * visual['depth']
        else:
            flange_thick = self.girder['flange_thickness'] * scale * visual['depth']

        girder_depth_visual = self.girder['depth'] * scale * visual['depth']

        painter.setBrush(QBrush(stiffener_color))
        painter.setPen(QPen(QColor(0, 0, 0), 1))

        # --- vertical limits of stiffener ---

        stiff_top_y = (
            base_y
            - girder_depth_visual
            + self.girder['top_flange_thickness'] * scale * visual['flange_thickness']
        )

        stiff_bottom_y = (
            base_y
            - self.girder['bottom_flange_thickness'] * scale * visual['flange_thickness']
        )

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
        """Draw crash barrier cross-section using IRC 5 geometry spec.
        """
        cb_type = self.crash_barrier_type
        geo = CrashBarrierGeometry.get_geometry(cb_type)

        if not geo:
            return

        barrier_color = QColor(220, 220, 220)
        if self.hovered_element == 'crash_barrier':
            barrier_color = QColor(255, 250, 220)

        # ------- RCC CRASH BARRIER --------
        if geo["type"] == "rcc":
            TOTAL_HEIGHT = geo["total_height"]
            BOTTOM_WIDTH = geo["bottom_width"]
            BASE_VERTICAL = geo["base_vertical"]
            MID_OFFSET = geo["mid_offset"]

            h = TOTAL_HEIGHT * scale
            bottom_w = BOTTOM_WIDTH * scale
            base_v = BASE_VERTICAL * scale

            y_bottom = y
            y_base_top = y - base_v
            y_mid = y - MID_OFFSET * scale
            y_top = y - h

            
            # Reference shape is High Containment (bottom_width=350 mm).
            # All offsets scale proportionally to the actual bottom_width.
            shape_scale  = BOTTOM_WIDTH / 525.0
            right_at_mid = 300 * scale * shape_scale   # outer wall x at inflection
            left_at_top  = 50  * scale * shape_scale   # inner wall x at top (lean)
            right_at_top = 225 * scale * shape_scale   # outer wall x at top

            painter.setBrush(QBrush(barrier_color))
            painter.setPen(QPen(QColor(0, 0, 0), max(1.5, scale * 1.5)))

            if side == 'left':
                # Same as median RIGHT barrier (carriageway-facing curve on the right)
                points = [
                    QPointF(x, y_bottom),    # BL
                    QPointF(x + bottom_w, y_bottom),    # BR
                    QPointF(x + bottom_w, y_base_top),  # R1 (outer, vertical base)
                    QPointF(x + right_at_mid, y_mid),       # R2 (outer wall kink)
                    QPointF(x + right_at_top, y_top),       # TR (outer wall top)
                    QPointF(x + left_at_top, y_top),       # TL (inner wall top, leans in)
                    QPointF(x, y_base_top),  # L1 (inner, vertical base)
                ]
                hover_rect = QRectF(x, y_top, bottom_w, h)
            else:
                # Same as median LEFT barrier (carriageway-facing curve on the left)
                # x is the RIGHT edge of this barrier
                points = [
                    QPointF(x - bottom_w, y_bottom),    # BL
                    QPointF(x, y_bottom),    # BR
                    QPointF(x, y_base_top),  # R1 (inner, vertical base)
                    QPointF(x - left_at_top, y_top),       # TR (inner wall top, leans in)
                    QPointF(x - right_at_top, y_top),       # TL (outer wall top)
                    QPointF(x - right_at_mid, y_mid),       # L2 (outer wall kink)
                    QPointF(x - bottom_w, y_base_top),  # L1 (outer, vertical base)
                ]
                hover_rect = QRectF(x - bottom_w, y_top, bottom_w, h)

            self.cross_section_hover_zones.append((hover_rect, 'crash_barrier'))
            painter.drawPolygon(QPolygonF(points))
            return


        # METALLIC W-BEAM CRASH BARRIER 
        post_h_mm   = geo.get("post_height", 750)
        kerb_h_mm   = geo.get("kerb_height", 150)
        n_beams     = geo.get("w_beams", 1)

        # Fallback dimensions from 3D CAD/IRC 5 standards for missing details
        kerb_top_w_mm    = 500.0
        kerb_bottom_w_mm = 550.0
        post_w_mm        = 150.0
        post_offset_mm   = 75.0   # Offset from kerb edge
        spacer_w_mm      = 200.0
        spacer_h_mm      = 330.0
        w_beam_h_mm      = 330.0  
        w_beam_depth_mm  = 83.0   
        w_beam_thk_mm    = 3.0

        # Scale all dimensions
        post_h         = post_h_mm * scale
        kerb_h         = kerb_h_mm * scale
        kerb_top_w     = kerb_top_w_mm * scale
        kerb_bottom_w  = kerb_bottom_w_mm * scale
        post_w         = post_w_mm * scale
        post_offset    = post_offset_mm * scale
        spacer_w       = spacer_w_mm * scale
        spacer_h       = spacer_h_mm * scale
        w_beam_h       = w_beam_h_mm * scale
        w_beam_depth   = w_beam_depth_mm * scale
        w_beam_thk     = w_beam_thk_mm * scale

        # Calculate positioning
        if side == 'left':
            base_x = x
            # Points for kerb (Trapezoid: outer wall vertical, inner wall slopes)
            # Symmetric trapezoid as per 3D code logic
            kerb_points = [
                QPointF(x, y),                                  # Bottom Left
                QPointF(x + kerb_bottom_w, y),                  # Bottom Right
                QPointF(x + (kerb_bottom_w + kerb_top_w)/2, y - kerb_h), # Top Right
                QPointF(x + (kerb_bottom_w - kerb_top_w)/2, y - kerb_h)  # Top Left
            ]
            
            # Post positioning (75mm from left end of kerb)
            post_rect_x = x + post_offset
            
            # Spacer starts at post right edge and grows right
            spacer_x_start = post_rect_x + post_w
            spacer_width_val = spacer_w
            
            # W-Beam starts at spacer right edge
            beam_root_x = spacer_x_start + spacer_w
            
        else:
            # Mirror for right side
            base_x = x - kerb_bottom_w
            kerb_points = [
                QPointF(x - kerb_bottom_w, y),
                QPointF(x, y),
                QPointF(x - (kerb_bottom_w - kerb_top_w)/2, y - kerb_h),
                QPointF(x - (kerb_bottom_w + kerb_top_w)/2, y - kerb_h)
            ]
            
            # Post positioning (75mm from right end of kerb)
            # x is the bottom-right coordinate of the kerb
            post_rect_x = x - post_offset - post_w
            
            # Spacer starts at post left edge and grows left
            spacer_x_start = post_rect_x
            spacer_width_val = -spacer_w
            
            # W-Beam starts at spacer left edge (which is spacer_x_start - spacer_w)
            beam_root_x = post_rect_x - spacer_w
            
        # Draw Kerb
        painter.setBrush(QBrush(QColor(180, 180, 180)))
        painter.setPen(QPen(Qt.black, max(1.0, scale)))
        painter.drawPolygon(QPolygonF(kerb_points))
        
        # Draw Post
        post_color = QColor(80, 80, 80) # Steel color
        if self.hovered_element == 'crash_barrier':
            post_color = QColor(255, 250, 220)
        painter.setBrush(QBrush(post_color))
        painter.drawRect(QRectF(post_rect_x, y - kerb_h - post_h, post_w, post_h))
        
        # Draw Spacer and W-Beam
        if n_beams == 1:
            h_centers = [post_h_mm - spacer_h_mm / 2.0]
        else:
            # Upper beam at top, lower beam below with 145mm gap (from 3D logic)
            h_upper = post_h_mm - spacer_h_mm / 2.0
            h_lower = h_upper - spacer_h_mm - 145
            h_centers = [h_lower, h_upper]

        for h_center_mm in h_centers:
            h_center = h_center_mm * scale
            spacer_y = y - kerb_h - h_center - spacer_h / 2
            
            # Draw Spacer
            painter.setBrush(QBrush(post_color))
            painter.drawRect(QRectF(spacer_x_start, spacer_y, spacer_width_val, spacer_h))
            
            # Draw W-Beam Profile (The double wave)
            # Generate wave points
            num_pts = 20 # Increased points for smoother wave
            
            def get_wave_y(z_rel): # z_rel from 0 to w_beam_h
                sigma = w_beam_h / 10.0
                mu1 = w_beam_h * 0.25
                mu2 = w_beam_h * 0.75
                amp = w_beam_depth * 1.5
                
                wave = (
                    amp * math.exp(-((z_rel - mu1) ** 2) / (2 * sigma ** 2)) +
                    amp * math.exp(-((z_rel - mu2) ** 2) / (2 * sigma ** 2))
                )
                return wave
            
            outer_wave = []
            inner_wave = []
            
            for pt_idx in range(num_pts + 1):
                z_rel = (pt_idx / num_pts) * w_beam_h
                wave_val = get_wave_y(z_rel)
                
                curr_y = spacer_y + (w_beam_h - z_rel)
                
                if side == 'left':
                    outer_wave.append(QPointF(beam_root_x + wave_val, curr_y))
                    inner_wave.insert(0, QPointF(beam_root_x + wave_val - w_beam_thk, curr_y))
                else:
                    outer_wave.append(QPointF(beam_root_x - wave_val, curr_y))
                    inner_wave.insert(0, QPointF(beam_root_x - wave_val + w_beam_thk, curr_y))
            
            w_beam_polygon = QPolygonF(outer_wave + inner_wave)
            painter.setBrush(QBrush(QColor(120, 120, 120)))
            painter.drawPolygon(w_beam_polygon)

        # Hover rect for the whole assembly
        assembly_top_y = y - kerb_h - post_h
        assembly_bottom_y = y
        if side == 'left':
            assembly_width = max(kerb_bottom_w, (beam_root_x + w_beam_depth - x))
            hover_rect = QRectF(x, assembly_top_y, abs(assembly_width), assembly_bottom_y - assembly_top_y)
        else:
            assembly_width = max(kerb_bottom_w, (x - (beam_root_x - w_beam_depth)))
            hover_rect = QRectF(x - assembly_width, assembly_top_y, abs(assembly_width), assembly_bottom_y - assembly_top_y)
            
        self.cross_section_hover_zones.append((hover_rect, 'crash_barrier'))

