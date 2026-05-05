import matplotlib
matplotlib.use("QtAgg")

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Path3DCollection 

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QSizePolicy, QPushButton,
    QFrame, QLabel, QCheckBox, QScrollArea
)
from PySide6.QtCore import Qt, QEvent

from osdagbridge.core.bridge_types.plate_girder.plot_generator import (
    build_figure_sfd,
    build_figure_bmd,
    build_figure_deflection,
    build_figure_grillage,
    FORCE_MAP,
    DISP_MAP,
)

# Forces starting with "F" -> shear (SFD); starting with "M" -> moment (BMD)
_SFD_KEYS  = {k for k in FORCE_MAP if k.startswith("F")}
_DEFL_KEYS = set(DISP_MAP.keys())   # "Dx", "Dy", "Dz"

# Map from the HTML labels used in OutputDock's radio grid -> plot keys
_RICH_LABEL_TO_FORCE = {
    "F<sub>x</sub>": "Fx",
    "V<sub>y</sub>": "Fy",
    "V<sub>z</sub>": "Fz",
    "T<sub>x</sub>": "Mx",
    "M<sub>y</sub>": "My",
    "M<sub>z</sub>": "Mz",
    "D<sub>x</sub>": "Dx",
    "D<sub>y</sub>": "Dy",
    "D<sub>z</sub>": "Dz",
}

_DEFAULT_FORCE_LABEL = "V<sub>y</sub>"   # pre-checked on first link


# =============================================================================
# PROFESSIONAL SUMMARY OVERLAY WIDGET (HTML/RichText based)
# =============================================================================
class SummaryOverlay(QFrame):
    """A floating HUD that sits on top of the Matplotlib canvas."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            SummaryOverlay {
                background-color: rgba(33, 37, 43, 215);
                border: 1px solid rgba(255, 255, 255, 50);
                border-radius: 6px;
            }
            QLabel {
                color: white;
                font-size: 13px;
                font-family: Consolas, 'Courier New', monospace;
                padding: 12px;
                background: transparent;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.text_label = QLabel()
        self.text_label.setTextFormat(Qt.RichText)
        self.text_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        layout.addWidget(self.text_label)

    def update_data(self, summary_data):
        hud_text = "<b>Extreme Values Summary</b><br>" + "-" * 38 + "<br>"
        
        h_girder = "Girder".ljust(8).replace(" ", "&nbsp;")
        h_max = "Max".rjust(10).replace(" ", "&nbsp;")
        h_min = "Min".rjust(12).replace(" ", "&nbsp;")
        
        hud_text += f"<b>{h_girder}</b> | <span style='color: #FF4136;'><b>{h_max}</b></span> | <span style='color: #00E5FF;'><b>{h_min}</b></span><br>" + "-" * 38 + "<br>"

        for girder, vals in summary_data.items():
            g_str = girder.ljust(8).replace(" ", "&nbsp;")
            max_str = f"{vals['max']:.2f}".rjust(10).replace(" ", "&nbsp;")
            min_str = f"{vals['min']:.2f}".rjust(12).replace(" ", "&nbsp;")
            
            hud_text += f"<b>{g_str}</b> | <span style='color: #FF4136;'>{max_str}</span> | <span style='color: #00E5FF;'>{min_str}</span><br>"

        self.text_label.setText(hud_text)
        self.adjustSize()


# =============================================================================
# MAIN PLOT WIDGET
# =============================================================================
class MplPlotWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Data populated by setup()
        self._ds_all    = None
        self._loadcases = []
        self._nodes     = {}
        self._members   = {}
        self._edge_dist = 0.0
        self._output_dock = None
        self._summary_data = {}

        # Display States
        self._grillage_mode = False
        self._show_nodes = True 
        self._show_axis = True  
        self._show_supports = True 
        self._show_grid = True  
        self._is_summary_checked = False
        self._show_max = False  
        self._show_min = False  
        self._show_all_vals = False 

        # Zoom state
        self._zoom_scale  = 1.0
        self._orig_limits = None   

        # matplotlib canvas
        self._fig    = plt.figure(figsize=(14, 6), facecolor="white")
        self._canvas = FigureCanvasQTAgg(self._fig)
        self._canvas.setMinimumHeight(300)
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._canvas.installEventFilter(self)

        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setWidget(self._canvas)
        self._scroll_area.setFrameShape(QFrame.NoFrame)

        # Initialize the Summary Overlay
        self._summary_overlay = SummaryOverlay(self._canvas)
        self._summary_overlay.hide()

        # zoom toolbar
        self._btn_zoom_in  = QPushButton("+")
        self._btn_zoom_out = QPushButton("−")
        self._btn_zoom_reset = QPushButton("⟳")
        for btn in (self._btn_zoom_in, self._btn_zoom_out, self._btn_zoom_reset):
            btn.setFixedSize(28, 28)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.setStyleSheet(
                "QPushButton { font-size: 16px; border: 1px solid #bbb; border-radius: 4px;"
                " background: #f5f5f5; }"
                "QPushButton:hover { background: #e0e0e0; }"
                "QPushButton:pressed { background: #bdbdbd; }"
            )
        self._btn_zoom_in.clicked.connect(self._zoom_in)
        self._btn_zoom_out.clicked.connect(self._zoom_out)
        self._btn_zoom_reset.clicked.connect(self._zoom_reset)

        # TOOBAR BUTTONS
        btn_style = (
            "QPushButton { font-size: 12px; border: 1px solid #bbb; border-radius: 4px;"
            " background: #f5f5f5; padding: 0 8px; }"
            "QPushButton:hover { background: #e0e0e0; }"
            "QPushButton:pressed { background: #bdbdbd; }"
            "QPushButton:checked { background: #1565C0; color: white;"
            " border: 1px solid #0D47A1; }"
        )

        self._btn_grillage = QPushButton("Grillage")
        self._btn_grillage.setCheckable(True)
        self._btn_grillage.setFixedHeight(28)
        self._btn_grillage.setFocusPolicy(Qt.NoFocus)
        self._btn_grillage.setStyleSheet(btn_style)
        self._btn_grillage.toggled.connect(self._on_grillage_toggled)

        self._btn_nodes = QPushButton("Nodes")
        self._btn_nodes.setCheckable(True)
        self._btn_nodes.setChecked(True) 
        self._btn_nodes.setFixedHeight(28)
        self._btn_nodes.setFocusPolicy(Qt.NoFocus)
        self._btn_nodes.setStyleSheet(btn_style)
        self._btn_nodes.toggled.connect(self._on_nodes_toggled)

        self._btn_supports = QPushButton("Supports")
        self._btn_supports.setCheckable(True)
        self._btn_supports.setChecked(True) 
        self._btn_supports.setFixedHeight(28)
        self._btn_supports.setFocusPolicy(Qt.NoFocus)
        self._btn_supports.setStyleSheet(btn_style)
        self._btn_supports.toggled.connect(self._on_supports_toggled)

        self._btn_axis = QPushButton("Axis")
        self._btn_axis.setCheckable(True)
        self._btn_axis.setChecked(True) 
        self._btn_axis.setFixedHeight(28)
        self._btn_axis.setFocusPolicy(Qt.NoFocus)
        self._btn_axis.setStyleSheet(btn_style)
        self._btn_axis.toggled.connect(self._on_axis_toggled)

        self._btn_grid = QPushButton("Grid")
        self._btn_grid.setCheckable(True)
        self._btn_grid.setChecked(True) 
        self._btn_grid.setFixedHeight(28)
        self._btn_grid.setFocusPolicy(Qt.NoFocus)
        self._btn_grid.setStyleSheet(btn_style)
        self._btn_grid.toggled.connect(self._on_grid_toggled)
        self._canvas.mpl_connect('scroll_event', self._on_scroll)

        toolbar_row = QHBoxLayout()
        toolbar_row.setContentsMargins(4, 2, 4, 2)
        toolbar_row.setSpacing(4)
        toolbar_row.addWidget(self._btn_grillage)
        toolbar_row.addWidget(self._btn_nodes)
        toolbar_row.addWidget(self._btn_supports) 
        toolbar_row.addWidget(self._btn_axis) 
        toolbar_row.addWidget(self._btn_grid) 
        toolbar_row.addStretch()
        toolbar_row.addWidget(self._btn_zoom_out)
        toolbar_row.addWidget(self._btn_zoom_in)
        toolbar_row.addWidget(self._btn_zoom_reset)

        # layout
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addLayout(toolbar_row)
        root.addWidget(self._scroll_area, stretch=1)

    # public API

    def setup(self, ds_all, loadcases: list, nodes: dict, members: dict,
              edge_dist: float = 0.0):
        self._ds_all    = ds_all
        self._loadcases = list(loadcases)
        self._nodes     = nodes
        self._members   = members
        self._edge_dist = edge_dist

    def link_output_dock(self, output_dock):
        self._output_dock = output_dock

        # 1. Connect Load Combinations
        combo_lc = output_dock.output_widget.findChild(QComboBox, "analysis.load_combination")
        if combo_lc is not None:
            combo_lc.blockSignals(True)
            combo_lc.clear()
            combo_lc.addItems(self._loadcases)
            combo_lc.blockSignals(False)
            combo_lc.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            combo_lc.setMinimumContentsLength(12)
            combo_lc.currentTextChanged.connect(self.update_plot)

        # 2. Connect Force Radios
        from osdagbridge.desktop.ui.utils.custom_widgets import CustomRadioButton
        force_rbs = [
            rb for rb in output_dock.output_widget.findChildren(CustomRadioButton)
            if rb.text() in _RICH_LABEL_TO_FORCE
        ]
        for rb in force_rbs:
            rb.setChecked(rb.text() == _DEFAULT_FORCE_LABEL)
            rb.toggled.connect(self.update_plot)

        # Create placeholders to store the checkboxes
        self._cb_max = None
        self._cb_min = None

        for cb in output_dock.output_widget.findChildren(QCheckBox):
            text = cb.text().strip().lower()
            if "summary" in text:
                cb.toggled.connect(self._on_summary_toggled)
                self._is_summary_checked = cb.isChecked()
            elif "max" in text:
                self._cb_max = cb  # Store the reference
                cb.toggled.connect(self._on_max_toggled)
                self._show_max = cb.isChecked()
            elif "min" in text:
                self._cb_min = cb  # Store the reference
                cb.toggled.connect(self._on_min_toggled)
                self._show_min = cb.isChecked()
            elif "all" in text:
                cb.toggled.connect(self._on_all_vals_toggled)
                self._show_all_vals = cb.isChecked()

        self.update_plot()

    def update_plot(self, *_args):
        if self._grillage_mode:
            return

        if self._ds_all is None or self._output_dock is None:
            return

        loadcase  = self._current_loadcase()
        force_key = self._current_force_key()

        if not loadcase or not force_key:
            return

        ds = self._ds_all.sel(Loadcase=loadcase)
        plt.close(self._fig)
        
        self._summary_data = {} 

        if force_key in _SFD_KEYS:
            self._fig = build_figure_sfd(ds, force_key, self._nodes, self._members, edge_dist=self._edge_dist)
        elif force_key in _DEFL_KEYS:
            self._fig = build_figure_deflection(ds, force_key, self._nodes, self._members, edge_dist=self._edge_dist)
        else:
            self._fig, self._summary_data = build_figure_bmd(ds, force_key, self._nodes, self._members, edge_dist=self._edge_dist)

        self._canvas.figure = self._fig
        self._fig.set_canvas(self._canvas)
        
        # Apply visual states
        self._apply_node_visibility()
        self._apply_axis_visibility()
        self._apply_supports_visibility()
        self._apply_grid_visibility() 
        self._apply_annotation_visibility() 
        
        # Update HUD
        if self._summary_data:
            self._summary_overlay.update_data(self._summary_data)
            if self._is_summary_checked:
                self._summary_overlay.show()
                self._summary_overlay.raise_()
        else:
            self._summary_overlay.hide()
        
        if self._fig:
            # Strip margins globally before handing the figure to the canvas
            self._fig.subplots_adjust(left=0.0, right=1.0, bottom=0.0, top=1.0)
        
        self._fit_figure_to_canvas()
        self._canvas.draw()

        self._zoom_scale = 1.0
        self._store_orig_limits()

    # NATIVE SLOTS: The 'checked' variable is now passed instantly by Qt!
    def _on_summary_toggled(self, checked):
        self._is_summary_checked = checked
        if self._is_summary_checked and self._summary_data:
            self._summary_overlay.show()
            self._summary_overlay.raise_()
        else:
            self._summary_overlay.hide()

    def _on_max_toggled(self, checked):
        self._show_max = checked
        self._apply_annotation_visibility()
        self._canvas.draw_idle()

    def _on_min_toggled(self, checked):
        self._show_min = checked
        self._apply_annotation_visibility()
        self._canvas.draw_idle()

    def _on_all_vals_toggled(self, checked):
        self._show_all_vals = checked
        
        # Disable the Max and Min checkboxes when "All" is active
        if self._cb_max:
            self._cb_max.setEnabled(not checked)
        if self._cb_min:
            self._cb_min.setEnabled(not checked)
            
        self._apply_annotation_visibility()
        self._canvas.draw_idle()

    # Toolbar Slots
    def _on_grillage_toggled(self, checked: bool):
        self._grillage_mode = checked
        if checked:
            if not self._nodes: return
            plt.close(self._fig)
            self._fig = build_figure_grillage(self._nodes, self._members, edge_dist=self._edge_dist)
            self._canvas.figure = self._fig
            self._fig.set_canvas(self._canvas)
            
            self._apply_node_visibility()
            self._apply_axis_visibility()
            self._apply_supports_visibility()
            self._apply_grid_visibility()
            self._summary_overlay.hide() 
            
            self._fit_figure_to_canvas()
            self._canvas.draw()
            self._zoom_scale = 1.0
            self._store_orig_limits()
        else:
            self.update_plot()

    def _on_nodes_toggled(self, checked: bool):
        self._show_nodes = checked
        self._apply_node_visibility()
        self._canvas.draw_idle() 

    def _on_axis_toggled(self, checked: bool):
        self._show_axis = checked
        self._apply_axis_visibility()
        self._canvas.draw_idle()

    def _on_supports_toggled(self, checked: bool):
        self._show_supports = checked
        self._apply_supports_visibility()
        self._canvas.draw_idle()

    def _on_grid_toggled(self, checked: bool):
        self._show_grid = checked
        self._apply_grid_visibility()
        self._canvas.draw_idle()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._summary_overlay:
            self._summary_overlay.move(15, 45) # Keep HUD floating safely under the toolbar

    # private helpers
    def _apply_node_visibility(self):
        for ax in self._fig.axes:
            for collection in ax.collections:
                if isinstance(collection, Path3DCollection):
                    if collection.get_gid() != "supports":
                        collection.set_visible(self._show_nodes)

    def _apply_supports_visibility(self):
        for ax in self._fig.axes:
            for collection in ax.collections:
                if collection.get_gid() == "supports":
                    collection.set_visible(self._show_supports)

    def _apply_axis_visibility(self):
        for ax in self._fig.axes:
            for collection in ax.collections:
                if collection.get_gid() == "coord_triad":
                    collection.set_visible(self._show_axis)
            
            for line in ax.lines:
                if line.get_gid() == "coord_triad":
                    line.set_visible(self._show_axis)

            for text in ax.texts:
                if text.get_gid() == "coord_triad":
                    text.set_visible(self._show_axis)

    def _apply_annotation_visibility(self):
        for ax in self._fig.axes:
            for line in ax.lines:
                if line.get_gid() == "max_line": 
                    line.set_visible(self._show_max or self._show_all_vals)
                elif line.get_gid() == "min_line": 
                    line.set_visible(self._show_min or self._show_all_vals)
            for text in ax.texts:
                if text.get_gid() == "max_line": 
                    text.set_visible(self._show_max or self._show_all_vals)
                elif text.get_gid() == "min_line": 
                    text.set_visible(self._show_min or self._show_all_vals)
                elif text.get_gid() == "all_vals": 
                    text.set_visible(self._show_all_vals)

    def _apply_grid_visibility(self):
        for ax in self._fig.axes:
            if self._show_grid:
                ax.grid(True, linestyle="--", linewidth=0.4, alpha=0.5)
            else:
                ax.grid(False)

    def _fit_figure_to_canvas(self):
        w_px = self._canvas.width()
        h_px = self._canvas.height()
        if w_px > 10 and h_px > 10:
            dpi = self._fig.dpi
            self._fig.set_size_inches(w_px / dpi, h_px / dpi, forward=False)

    def _store_orig_limits(self):
        pass # Not needed for Uniform Render Zoom

    def _apply_zoom(self):
        """Zooms the 2D canvas dynamically, creating scrollbars for perfect panning!"""
        if self._zoom_scale <= 1.0:
            self._zoom_scale = 1.0
            self._scroll_area.setWidgetResizable(True)
            self._canvas.setMinimumSize(0, 0)
            self._canvas.setMaximumSize(16777215, 16777215)
        else:
            self._scroll_area.setWidgetResizable(False)
            base_w = self._scroll_area.width() - 2
            base_h = self._scroll_area.height() - 2
            # Physically resize the canvas like zooming a photo
            self._canvas.setFixedSize(int(base_w * self._zoom_scale), int(base_h * self._zoom_scale))
        self._canvas.draw_idle()

    # def eventFilter(self, obj, event):
    #     if obj is self._canvas and event.type() == QEvent.Type.Wheel:
    #         event.accept() 
            
    #         # 1. Capture the exact mouse position BEFORE zooming
    #         pos = event.position()
    #         mouse_x, mouse_y = pos.x(), pos.y()
            
    #         old_width = self._canvas.width()
    #         old_height = self._canvas.height()

    #         # 2. Calculate the zoom
    #         delta = event.angleDelta().y()
    #         if delta > 0:
    #             self._zoom_scale = min(self._zoom_scale * 1.05, 8.0) # Zoom IN
    #         else:
    #             self._zoom_scale = max(self._zoom_scale * 0.95, 1.0) # Zoom OUT
                
    #         self._apply_zoom()

    #         # 3. Calculate how much the canvas grew/shrank
    #         new_width = self._canvas.width()
    #         new_height = self._canvas.height()

    #         if old_width == 0 or old_height == 0: return True

    #         # 4. Smart Scrollbar Math: Shift the view to keep the mouse anchored!
    #         h_bar = self._scroll_area.horizontalScrollBar()
    #         v_bar = self._scroll_area.verticalScrollBar()

    #         new_x = (mouse_x / old_width) * new_width
    #         new_y = (mouse_y / old_height) * new_height

    #         h_bar.setValue(int(h_bar.value() + (new_x - mouse_x)))
    #         v_bar.setValue(int(v_bar.value() + (new_y - mouse_y)))

    #         return True   
    #     return super().eventFilter(obj, event)

    def _zoom_step(self, factor):
        """Natively zooms the Matplotlib 3D camera by scaling the axis limits."""
        if not hasattr(self, '_fig') or not self._fig or not self._fig.axes:
            return
            
        ax = self._fig.axes[0]
        
        # 1. Get current boundaries
        x0, x1 = ax.get_xlim()
        y0, y1 = ax.get_ylim()
        z0, z1 = ax.get_zlim()
        
        # 2. Find the exact center of the current view
        xc, yc, zc = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
        
        # 3. Scale the ranges by the zoom factor
        xr, yr, zr = (x1 - x0) * factor, (y1 - y0) * factor, (z1 - z0) * factor
        
        # 4. Apply the new narrowed/widened limits
        ax.set_xlim(xc - xr / 2, xc + xr / 2)
        ax.set_ylim(yc - yr / 2, yc + yr / 2)
        ax.set_zlim(zc - zr / 2, zc + zr / 2)
        
        self._canvas.draw_idle()

    def _zoom_in(self):
        # 85% of current view size (zooms in)
        self._zoom_step(0.85) 

    def _zoom_out(self):
        # 115% of current view size (zooms out)
        self._zoom_step(1.15) 
    def _on_scroll(self, event):
        """Native Matplotlib scroll wheel support."""
        if event.button == 'up':
            self._zoom_step(0.85)  # Scroll wheel up = Zoom in
        elif event.button == 'down':
            self._zoom_step(1.15)  # Scroll wheel down = Zoom out
        
    def _zoom_reset(self):
        # The safest and cleanest way to reset is just to re-trigger the plot update!
        self.update_plot()

    def _current_loadcase(self) -> str:
        combo = self._output_dock.output_widget.findChild(
            QComboBox, "analysis.load_combination"
        )
        return combo.currentText() if combo else (self._loadcases[0] if self._loadcases else "")

    def _current_force_key(self) -> str:
        from osdagbridge.desktop.ui.utils.custom_widgets import CustomRadioButton
        for rb in self._output_dock.output_widget.findChildren(CustomRadioButton):
            if rb.isChecked() and rb.text() in _RICH_LABEL_TO_FORCE:
                return _RICH_LABEL_TO_FORCE[rb.text()]
        return "Fy"