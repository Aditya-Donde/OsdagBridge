"""
Dual CAD View Widget for OsdagBridge
Combines cross-section and top view in a split layout
Author: Arushi
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QSplitter, QScrollArea, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from .cad_cross_section import CrossSectionCADWidget
from .cad_top_view import TopViewCADWidget

class BridgeDualCADWidget(QWidget):
    """Split view widget showing both cross-section and top view with individual controls"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cross_zoom_level = 1.0
        self.top_zoom_level = 1.0
        self.cross_visible = True
        self.top_visible = True
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the split view layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)
        
        # Create vertical splitter for two views
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.setHandleWidth(5)
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #d0d0d0;
                margin: 1px 0px;
            }
            QSplitter::handle:hover {
                background-color: #90AF13;
            }
        """)
        
        # Create cross-section scroll area
        self.cross_section_widget = CrossSectionCADWidget(self)
        # self.cross_section_widget.setMinimumSize(800, 600)
        
        self.cross_scroll = QScrollArea()
        self.cross_scroll.setWidget(self.cross_section_widget)
        self.cross_scroll.setWidgetResizable(True)
        self.cross_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.cross_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        
        self.splitter.addWidget(self.cross_scroll)
        
        # Create top view scroll area
        self.top_view_widget = TopViewCADWidget(self)
        # self.top_view_widget.setMinimumSize(800, 600)
        
        self.top_scroll = QScrollArea()
        self.top_scroll.setWidget(self.top_view_widget)
        self.top_scroll.setWidgetResizable(True)
        self.top_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.top_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        
        self.splitter.addWidget(self.top_scroll)
        
        # Set equal sizes for both views
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)
        
        layout.addWidget(self.splitter)
    
    def set_cross_section_visible(self, visible):
        self.cross_visible = visible
        self.cross_scroll.setVisible(visible)
        self._restore_splitter()

    def set_top_view_visible(self, visible):
        self.top_visible = visible
        self.top_scroll.setVisible(visible)
        self._restore_splitter()

    def _restore_splitter(self):
        """Reset splitter to correct ratio based on which views are visible."""
        if self.cross_visible and self.top_visible:
            # Both visible — equal split via stretch factors, no fixed sizes
            self.splitter.setStretchFactor(0, 1)
            self.splitter.setStretchFactor(1, 1)
            self.splitter.setSizes([1, 1])   # relative, Qt normalises to available height
        elif self.cross_visible:
            self.splitter.setStretchFactor(0, 1)
            self.splitter.setStretchFactor(1, 0)
            self.splitter.setSizes([1, 0])
        else:
            self.splitter.setStretchFactor(0, 0)
            self.splitter.setStretchFactor(1, 1)
            self.splitter.setSizes([0, 1])
    
    # Cross-section zoom methods
    def cross_zoom_in(self):
        self.cross_zoom_level *= 1.1
        self._apply_cross_zoom()
    
    def cross_zoom_out(self):
        self.cross_zoom_level /= 1.1
        self._apply_cross_zoom()
    
    def cross_zoom_reset(self):
        self.cross_zoom_level = 1.0
        self._apply_cross_zoom()
    
    def _apply_cross_zoom(self):
        base_width = self.cross_scroll.viewport().width()
        base_height = self.cross_scroll.viewport().height()
        self.cross_section_widget.setFixedSize(
            int(base_width * self.cross_zoom_level),
            int(base_height * self.cross_zoom_level)
        )
        self.cross_section_widget.update()
    
    # Top view zoom methods
    def top_zoom_in(self):
        self.top_zoom_level *= 1.15
        self._apply_top_zoom()
    
    def top_zoom_out(self):
        self.top_zoom_level /= 1.15
        self._apply_top_zoom()
    
    def top_zoom_reset(self):
        self.top_zoom_level = 1.0
        self._apply_top_zoom()
    
    def _apply_top_zoom(self):
        base_width = self.top_scroll.viewport().width()
        base_height = self.top_scroll.viewport().height()
        self.top_view_widget.setFixedSize(
            int(base_width * self.top_zoom_level),
            int(base_height * self.top_zoom_level)
        )
        self.top_view_widget.update()
    
    def update_from_osdag_inputs(self, input_dict):
        """
        Update CAD from OsdagBridge input fields
        Maps from OsdagBridge common.py KEY_* fields to CAD widget parameters
        
        Args:
            input_dict: Dictionary with keys from common.py (e.g., KEY_SPAN, KEY_CARRIAGEWAY_WIDTH)
        """
        from osdagbridge.core.utils.common import (
            KEY_SPAN, KEY_CARRIAGEWAY_WIDTH, KEY_SKEW_ANGLE, KEY_FOOTPATH,
            KEY_NO_OF_GIRDERS, KEY_GIRDER_SPACING, KEY_DECK_OVERHANG,
            KEY_DECK_THICKNESS, KEY_FOOTPATH_WIDTH, KEY_FOOTPATH_THICKNESS,
            KEY_CROSS_BRACING_SPACING, KEY_INCLUDE_MEDIAN
        )
        
        params = {}
        
        # Map span (meters to mm)
        if KEY_SPAN in input_dict:
            params['span_length'] = float(input_dict[KEY_SPAN]) * 1000
        
        # Map carriageway width (meters to mm)
        if KEY_CARRIAGEWAY_WIDTH in input_dict:
            params['carriageway_width'] = float(input_dict[KEY_CARRIAGEWAY_WIDTH]) * 1000
        
        # Map skew angle (degrees)
        if KEY_SKEW_ANGLE in input_dict:
            params['skew_angle'] = float(input_dict[KEY_SKEW_ANGLE])
        
        # Map number of girders
        if KEY_NO_OF_GIRDERS in input_dict:
            params['num_girders'] = int(input_dict[KEY_NO_OF_GIRDERS])
        
        # Map girder spacing (meters to mm)
        if KEY_GIRDER_SPACING in input_dict:
            params['girder_spacing'] = float(input_dict[KEY_GIRDER_SPACING]) * 1000
        
        # Map deck overhang (meters to mm)
        if KEY_DECK_OVERHANG in input_dict:
            params['deck_overhang'] = float(input_dict[KEY_DECK_OVERHANG]) * 1000
        
        # Map deck thickness (mm)
        if KEY_DECK_THICKNESS in input_dict:
            params['deck_thickness'] = float(input_dict[KEY_DECK_THICKNESS])
        
        # Map footpath width (meters to mm)
        if KEY_FOOTPATH_WIDTH in input_dict:
            params['footpath_width'] = float(input_dict[KEY_FOOTPATH_WIDTH]) * 1000
        
        # Map footpath thickness (mm)
        if KEY_FOOTPATH_THICKNESS in input_dict:
            params['footpath_thickness'] = float(input_dict[KEY_FOOTPATH_THICKNESS])
        
        # Map footpath configuration
        if KEY_FOOTPATH in input_dict:
            footpath_value = input_dict[KEY_FOOTPATH]
            if footpath_value == "None":
                params['footpath_config'] = 'none'
            elif footpath_value == "Single Sided":
                params['footpath_config'] = 'left'
            elif footpath_value == "Both":
                params['footpath_config'] = 'both'
        
        # Map cross bracing spacing (meters to mm)
        if KEY_CROSS_BRACING_SPACING in input_dict:
            params['cross_bracing_spacing'] = float(input_dict[KEY_CROSS_BRACING_SPACING]) * 1000
        
        # Map median present
        if KEY_INCLUDE_MEDIAN in input_dict:
            params['median_present'] = bool(input_dict[KEY_INCLUDE_MEDIAN])
        
        # Update both widgets with same parameters
        self.cross_section_widget.update_params(params)
        self.top_view_widget.update_params(params)
    
    def update_specific_param(self, param_key, value):
        """
        Update a specific parameter without re-updating everything
        Optimized for real-time updates
        """
        params = {param_key: value}
        self.cross_section_widget.update_params(params)
        self.top_view_widget.update_params(params)