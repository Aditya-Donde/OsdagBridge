"""
Dual CAD View Widget for OsdagBridge
Combines cross-section and top view in a split layout
Author: Arushi
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QSplitter, QScrollArea, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from .cad_cross_section import CrossSectionCADWidget
from .cad_top_view import TopViewCADWidget
from osdagbridge.desktop.cad.irc5_geometry import (
    CrashBarrierGeometry,
    MedianGeometry,
    RailingGeometry,
)

class BridgeDualCADWidget(QWidget):
    """Split view widget showing both cross-section and top view with individual controls"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cross_zoom_level = 1.0
        self.top_zoom_level = 1.0
        self.cross_visible = True
        self.top_visible = True
        # Last mapped params from input dock; used to push only real changes.
        self._last_mapped_params = {}
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
            KEY_CROSS_BRACING_SPACING, KEY_INCLUDE_MEDIAN, KEY_WEARING_COAT_THICKNESS, KEY_WEARING_COAT_DENSITY, KEY_WEARING_COAT_MATERIAL,
        )
        
        params = {}
        
        # Map span (meters to mm)
        if KEY_SPAN in input_dict:
            if input_dict[KEY_SPAN] is not None:
                params['span_length'] = float(input_dict[KEY_SPAN]) * 1000
        
        # Map carriageway width (meters to mm)
        if KEY_CARRIAGEWAY_WIDTH in input_dict:
            if input_dict[KEY_CARRIAGEWAY_WIDTH] is not None:
                params['carriageway_width'] = float(input_dict[KEY_CARRIAGEWAY_WIDTH]) * 1000
        
        # Map skew angle (degrees)
        if KEY_SKEW_ANGLE in input_dict:
            if input_dict[KEY_SKEW_ANGLE] is not None:
                params['skew_angle'] = float(input_dict[KEY_SKEW_ANGLE])
        
        # Map number of girders
        if KEY_NO_OF_GIRDERS in input_dict:
            params['num_girders'] = int(input_dict[KEY_NO_OF_GIRDERS])
        else:
            params['num_girders'] = 4 # Add default values if not present

        # Map girder spacing (meters to mm)
        if KEY_GIRDER_SPACING in input_dict:
            params['girder_spacing'] = float(input_dict[KEY_GIRDER_SPACING]) * 1000
        else:
            params['girder_spacing'] = 2.75 * 1000 # Add default values if not present

        # Map deck overhang (meters to mm)
        if KEY_DECK_OVERHANG in input_dict:
            params['deck_overhang'] = float(input_dict[KEY_DECK_OVERHANG]) * 1000
        else:
            params['deck_overhang'] = 1.0 * 1000 # Add default values if not present

        # Map deck thickness (mm)
        if KEY_DECK_THICKNESS in input_dict:
            params['deck_thickness'] = float(input_dict[KEY_DECK_THICKNESS])
        else:
            params['deck_thickness'] = 200 # Add default values if not present

        # Map footpath width (meters to mm)
        if KEY_FOOTPATH_WIDTH in input_dict:
            params['footpath_width'] = float(input_dict[KEY_FOOTPATH_WIDTH]) * 1000
        else:
            params['footpath_width'] = 1.5 * 1000 # Add default values if not present

        # Map footpath thickness (mm)
        if KEY_FOOTPATH_THICKNESS in input_dict:
            params['footpath_thickness'] = float(input_dict[KEY_FOOTPATH_THICKNESS])
        else:
            params['footpath_thickness'] = 200 # Add default values if not present

        if "crash_barrier_type" in input_dict:
            params['crash_barrier_type'] = input_dict["crash_barrier_type"]
            
        if "crash_barrier_height" in input_dict:
            params['crash_barrier_height'] = float(input_dict["crash_barrier_height"]) * 1000
            
        if "crash_barrier_width" in input_dict:
            params['crash_barrier_width'] = float(input_dict["crash_barrier_width"]) * 1000
            
        if "railing_type" in input_dict:
            railing_type = input_dict["railing_type"]
            geom = RailingGeometry.get_geometry(railing_type)

            params["railing_type"] = railing_type

            if geom:
                if "height" in geom:
                    params["railing_height"] = geom["height"]

                if "width" in geom:
                    params["railing_width"] = geom["width"]


        if "median_type" in input_dict:
            median_type = input_dict["median_type"]
            geom = MedianGeometry.get_geometry(median_type)

            params["median_type"] = median_type

            if geom:
                if "median_width" in geom:
                    params["median_width"] = geom["median_width"]

                if "barrier_height" in geom:
                    params["median_height"] = geom["barrier_height"]
                elif "kerb_height" in geom:
                    params["median_height"] = geom["kerb_height"]
                    
        # ---- Wearing Coat ----
        if KEY_WEARING_COAT_THICKNESS in input_dict:
            wearing_thickness = float(input_dict[KEY_WEARING_COAT_THICKNESS])
            params[KEY_WEARING_COAT_THICKNESS] = wearing_thickness
            params["wearing_course_thickness"] = wearing_thickness

        if KEY_WEARING_COAT_DENSITY in input_dict:
            wearing_density = float(input_dict[KEY_WEARING_COAT_DENSITY])
            params[KEY_WEARING_COAT_DENSITY] = wearing_density
            params["wearing_course_density"] = wearing_density

        if KEY_WEARING_COAT_MATERIAL in input_dict:
            wearing_material = input_dict[KEY_WEARING_COAT_MATERIAL]
            params[KEY_WEARING_COAT_MATERIAL] = wearing_material
            params["wearing_course_material"] = wearing_material

        
        # Map footpath configuration
        if KEY_FOOTPATH in input_dict:
            footpath_value = input_dict[KEY_FOOTPATH]
            if footpath_value == "None":
                params['footpath_config'] = 'none'
            elif footpath_value == "Single Side":
                params['footpath_config'] = 'left'
            elif footpath_value == "Both Sides":
                params['footpath_config'] = 'both'
        
        # Map cross bracing spacing (meters to mm)
        if KEY_CROSS_BRACING_SPACING in input_dict:
            params['cross_bracing_spacing'] = float(input_dict[KEY_CROSS_BRACING_SPACING]) * 1000
        else:
            params['cross_bracing_spacing'] = 3.5 * 1000 # Add default values if not present

        # Map median present
        if KEY_INCLUDE_MEDIAN in input_dict:
            params['median_present'] = bool(input_dict[KEY_INCLUDE_MEDIAN] == "Yes")
            # When enabling median from homepage and no median_type was set yet,
            # provide a sensible default so the CAD can draw a shape.
            if params['median_present'] and 'median_type' not in input_dict:
                default_type = "IRC 5 - Raised Kerb"
                params['median_type'] = default_type
                geom = MedianGeometry.get_geometry(default_type)
                if geom:
                    if "median_width" in geom:
                        params["median_width"] = geom["median_width"]
                    if "kerb_height" in geom:
                        params["median_height"] = geom["kerb_height"]
                    elif "barrier_height" in geom:
                        params["median_height"] = geom["barrier_height"]
        
        # Propagate only keys that actually changed to avoid unnecessary redraw/zoom resets.
        changed_params = {
            k: v for k, v in params.items()
            if self._last_mapped_params.get(k) != v
        }
        if not changed_params:
            return

        self._last_mapped_params.update(changed_params)

        # Span length only affects the top view plan geometry; avoid cross-section retriggers.
        cross_section_params = {k: v for k, v in changed_params.items() if k != 'span_length'}

        if cross_section_params:
            self.cross_section_widget.update_params(cross_section_params)
        self.top_view_widget.update_params(changed_params)


    
    # def update_specific_param(self, param_key, value):
    #     """
    #     Update a specific parameter without re-updating everything
    #     Optimized for real-time updates
    #     """
    #     if self._last_mapped_params.get(param_key) == value:
    #         return

    #     params = {param_key: value}
    #     self._last_mapped_params[param_key] = value
    #     if param_key != 'span_length':
    #         self.cross_section_widget.update_params(params)
    #     self.top_view_widget.update_params(params)