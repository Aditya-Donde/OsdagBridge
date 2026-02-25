import numpy as np
import traceback
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QLineEdit, QFrame, QComboBox, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec

from osdagbridge.core.bridge_types.plate_girder.analysis_results import PlateGirderAnalysisResults

# -------------------------------------------------------------------------------------------------------------------------------------------------
# UI / Visual Configuration
# -------------------------------------------------------------------------------------------------------------------------------------------------
COLOR_PRIMARY_FILL = "#E0F2F1"      # Muted teal fill
COLOR_PRIMARY_STROKE = "#00897B"    # Muted teal stroke
COLOR_ZERO_LINE = "#B0BEC5"         # Soft grey zero line
COLOR_GIRDER_LINE = "#90A4AE"       # Minimal structural line
COLOR_NODE_REF = "#D0D0D0"          # Thicker, slightly darker reference lines for visibility
COLOR_CURSOR = "#546E7A"            # Cursor line
COLOR_SEPARATOR = "#E0E0E0"         # Soft visual boundary / bounding box
COLOR_TEXT_LABEL = "#555555"        # Subtle, medium-weight labels

class Girder2DPlotsWidget(QWidget):
    """
    PySide6 widget representing a generic 2D girder plot.
    Displays vertically stacked plots:
    1. Girder (Structural reference)
    2. Bending Moment Diagram (BMD)
    3. Shear Force Diagram (SFD)
    4. Deflection Diagram
    
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.analyser_model = None
        self.loadcase = None
        self.raw_results = None
        self.ar_helper = None
        self.girder_map = {}
        
        self._x_data = np.array([])
        self._bmd_data = np.array([])
        self._sfd_data = np.array([])
        self._defl_data = np.array([])
        
        self._cursors = []
        
        self._init_ui()

    def _init_ui(self):
        """Initializes the layout, top controls, RHS value boxes, and Matplotlib canvas."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(10)
        
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Top Controls: Girder Selection
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(10, 10, 10, 0)
        
        lbl_select = QLabel("Select Girder:")
        lbl_select.setFont(QFont("Segoe UI", 10, QFont.Bold))
        lbl_select.setStyleSheet("color: #333333;")
        
        self.girder_combo = QComboBox()
        self.girder_combo.setMinimumWidth(200)
        self.girder_combo.setStyleSheet("""
            QComboBox {
                padding: 6px 10px;
                font-size: 13px;
                color: #222222;
                background-color: #FFFFFF;
                border: 1px solid #BBBBBB;
                border-radius: 4px;
            }
            QComboBox::drop-down {
                border-left: 1px solid #CCCCCC;
            }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                color: #222222;
                selection-background-color: #E0E0E0;
                selection-color: #000000;
            }
            QComboBox:disabled {
                background-color: #F0F0F0;
                color: #888888;
            }
        """)
        self.girder_combo.currentTextChanged.connect(self._on_girder_selected)
        self.girder_combo.setEnabled(False) 
        
        lbl_mode = QLabel("Interaction:")
        lbl_mode.setFont(QFont("Segoe UI", 10, QFont.Bold))
        lbl_mode.setStyleSheet("color: #333333;")
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Scroll for Values", "Maximum Values"])
        self.mode_combo.setStyleSheet(self.girder_combo.styleSheet())
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        
        controls_layout.addWidget(lbl_select)
        controls_layout.addWidget(self.girder_combo)
        controls_layout.addSpacing(20)
        controls_layout.addWidget(lbl_mode)
        controls_layout.addWidget(self.mode_combo)
        controls_layout.addStretch()
        
        self.main_layout.addLayout(controls_layout)
        
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Bottom Body: Split between Charts and RHS
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(10)
        
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Left Side: Matplotlib Figure
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        self.figure = Figure(figsize=(8, 10))
        self.figure.patch.set_facecolor('#FFFFFF')
        self.canvas = FigureCanvas(self.figure)
        body_layout.addWidget(self.canvas, stretch=4)
        
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Right Side: Values Display Panel
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        self.val_panel = QFrame()
        self.val_panel.setStyleSheet("QFrame { background-color: #FAFAFA; border: 1px solid #CCCCCC; border-radius: 4px; }")
        self.val_panel.setFixedWidth(180)
        
        val_layout = QVBoxLayout(self.val_panel)
        val_layout.setContentsMargins(10, 0, 10, 0)
        val_layout.setSpacing(0)
        
        self.fields = {}
        
        def create_value_box(label_text, key):
            container = QWidget()
            l = QVBoxLayout(container)
            l.setContentsMargins(5, 5, 5, 5)
            l.setSpacing(6)
            
            lbl = QLabel(label_text)
            lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
            lbl.setStyleSheet("color: #444444; border: None;")
            lbl.setAlignment(Qt.AlignCenter)
            
            val = QLineEdit("-")
            if key == "x":
                val.setReadOnly(False)
                val.setToolTip("Enter X position and press Return")
            else:
                val.setReadOnly(True)
            val.setAlignment(Qt.AlignCenter)
            val.setStyleSheet("""
                QLineEdit {
                    background-color: #FFFFFF;
                    border: 1px solid #CCCCCC;
                    border-radius: 3px;
                    padding: 5px;
                    color: #111111;
                    font-size: 11px;
                    outline: none;
                }
            """)
            
            l.addWidget(lbl)
            l.addWidget(val)
            l.setAlignment(Qt.AlignCenter)
            self.fields[key] = val
            return container

        box_x = create_value_box("X Position (m)", "x")
        self.fields["x"].returnPressed.connect(self._on_user_x_entered)
        box_bmd = create_value_box("BMD (kNm)", "bmd")
        box_sfd = create_value_box("SFD (kN)", "sfd")
        box_defl = create_value_box("Deflection (mm)", "defl")

        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Proportional stretching to align natively with matplotlib axes vertical scales Now that Labels are BELOW the plots, the top stretch starts directly at the Girder plot!
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        val_layout.addStretch(58) 
        val_layout.addWidget(box_x, stretch=80)
        val_layout.addStretch(15) 
        val_layout.addWidget(box_bmd, stretch=300)
        val_layout.addStretch(15)
        val_layout.addWidget(box_sfd, stretch=300)
        val_layout.addStretch(15)
        val_layout.addWidget(box_defl, stretch=300)
        val_layout.addStretch(15)
        val_layout.addStretch(58)
        
        body_layout.addWidget(self.val_panel)
        self.main_layout.addLayout(body_layout, stretch=1)
        
        self._setup_axes()
        self._setup_event_handling()

    def _setup_axes(self):
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Increase 'hspace' to create subtle breathing room between distinct figures visually. Height ratio for label rows (index 1, 3, 5, 7) increased to prevent tight cramping.
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        gs = gridspec.GridSpec(8, 1, figure=self.figure, 
                               height_ratios=[0.5, 0.6, 3, 0.6, 3, 0.6, 3, 0.6], 
                               hspace=0.08)
        
        self.figure.subplots_adjust(left=0.15, right=0.95, top=0.92, bottom=0.10)
        
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Primary reference axis (Girder reintroduced)
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        self.ax_girder = self.figure.add_subplot(gs[0])
        self.ax_lbl_girder = self.figure.add_subplot(gs[1], sharex=self.ax_girder)
        self.ax_girder.set_visible(True)
        self.ax_lbl_girder.set_visible(True)
        
        self.ax_bmd = self.figure.add_subplot(gs[2], sharex=self.ax_girder)
        self.ax_lbl_bmd = self.figure.add_subplot(gs[3], sharex=self.ax_girder)
        
        self.ax_sfd = self.figure.add_subplot(gs[4], sharex=self.ax_girder)
        self.ax_lbl_sfd = self.figure.add_subplot(gs[5], sharex=self.ax_girder)
        
        self.ax_defl = self.figure.add_subplot(gs[6], sharex=self.ax_girder)
        self.ax_lbl_defl = self.figure.add_subplot(gs[7], sharex=self.ax_girder)
        
        self.all_axes = [self.ax_girder, self.ax_lbl_girder,
                         self.ax_bmd, self.ax_lbl_bmd,
                         self.ax_sfd, self.ax_lbl_sfd,
                         self.ax_defl, self.ax_lbl_defl]
                         
        self.plot_axes = [self.ax_bmd, self.ax_sfd, self.ax_defl]
        
    def _apply_axis_styles(self):
        """
        Applies strict engineering design constraints:
        - Soft bounding boxes for visual separation
        - Wipes all chart clutter (ticks, etc.).
        - Ensures deflection axis is inverted (downward positive).
        """
        for ax in self.all_axes:
            ax.set_axis_on()
            ax.set_facecolor('#FFFFFF')
            
            for spine in ax.spines.values():
                spine.set_visible(False)
            
            ax.set_yticks([])
            ax.set_xticks([])
            ax.tick_params(axis='both', which='both', length=0, labelbottom=False, labelleft=False)

        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Soft visually separate plot regions cleanly on all 4 sides for consistent container weight
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        for ax in self.plot_axes:
            for spine in ax.spines.values():
                spine.set_visible(True)
                spine.set_color(COLOR_SEPARATOR)
                spine.set_linewidth(1.0)
                
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # To maintain the solid bottom border despite GridSpec hspace adjustments, we explicitly ensure the bottom spine of plot axes is rendered strongly.
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        for ax in self.plot_axes:
            ax.spines['bottom'].set_color('#CCCCCC')
            ax.spines['bottom'].set_linewidth(1.2)

        if not self.ax_defl.yaxis.get_inverted():
            self.ax_defl.invert_yaxis()

    def set_analyser_data(self, analyser_model, loadcase="girder self weight"):
        """
        Main public interface into the widget.
        The external program calls this passing the loaded OpenSees model.
        Extracts structural networks and populates internal dropdowns.
        """
        self.analyser_model = analyser_model
        self.loadcase = loadcase
        
        try:
            # -------------------------------------------------------------------------------------------------------------------------------------------------
            # Assume opensees engine has finished analysis logic before handing off
            # -------------------------------------------------------------------------------------------------------------------------------------------------
            self.raw_results = self.analyser_model.model.get_results()
            self.ar_helper = PlateGirderAnalysisResults(self.raw_results, self.analyser_model.model)
            self.girder_map, _ = self.ar_helper.build_girders(verbose=False)
            
            # -------------------------------------------------------------------------------------------------------------------------------------------------
            # Sort girders naturally (g1, g2, g3)
            # -------------------------------------------------------------------------------------------------------------------------------------------------
            girders_found = sorted(self.girder_map.keys(), key=lambda x: int(x.replace('g', '')) if 'g' in x else x)
            
            if not girders_found:
                QMessageBox.warning(self, "Data Error", "No continuous girders found in the grillage topology.")
                return
                
            self.girder_combo.blockSignals(True)
            self.girder_combo.clear()
            self.girder_combo.addItems(girders_found)
            self.girder_combo.blockSignals(False)
            self.girder_combo.setEnabled(True)
            
            # -------------------------------------------------------------------------------------------------------------------------------------------------
            # Auto-plot the very first girder in the model
            # -------------------------------------------------------------------------------------------------------------------------------------------------
            self._on_girder_selected(self.girder_combo.currentText())
            
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Engine Failure", f"Failed to parse OpenSees data matrices: {e}")

    def _on_girder_selected(self, girder_name):
        """Extracts continuous structural vector data specifically for the selected girder."""
        if not girder_name or girder_name not in self.girder_map:
            return
            
        girder = self.girder_map[girder_name]
        girder_elements = girder["elements"]
        path_nodes = girder["path"]
        
        try:
            # -------------------------------------------------------------------------------------------------------------------------------------------------
            # Extract absolute spatial ordering of nodes
            # -------------------------------------------------------------------------------------------------------------------------------------------------
            nodes, _, _ = self.ar_helper.build_grillage_connectivity()
            
            x_raw = [nodes[n][0] for n in path_nodes]
            # -------------------------------------------------------------------------------------------------------------------------------------------------
            # Normalizing X-axis span to always commence strictly from 0 natively
            # -------------------------------------------------------------------------------------------------------------------------------------------------
            offset = min(x_raw)
            x_array = np.array([x - offset for x in x_raw])
            
            # -------------------------------------------------------------------------------------------------------------------------------------------------
            # Extract physics force matrices
            # -------------------------------------------------------------------------------------------------------------------------------------------------
            bmd_dict = self.ar_helper.get_beam_element_results(girder_elements, self.loadcase, "Mz_i")
            sfd_dict = self.ar_helper.get_beam_element_results(girder_elements, self.loadcase, "Vy_i")
            
            def safe_float(v):
                if v is None: return 0.0
                try: return float(v)
                except: return 0.0
                
            raw_bmd = [safe_float(bmd_dict.get(eid)) for eid in girder_elements] + [0.0]
            raw_sfd = [safe_float(sfd_dict.get(eid)) for eid in girder_elements] + [0.0]
            
            bmd_array = np.nan_to_num(np.array(raw_bmd))
            sfd_array = np.nan_to_num(np.array(raw_sfd))
            
            # -------------------------------------------------------------------------------------------------------------------------------------------------
            # Vertical Deflection matrix extraction OpenSees matrices map nodes non-sequentially. We must extract by explicit Node ID tags. Z is typically the vertical axis in our 3D bridge grillage, but we fallback to Y if it's 2D.
            # -------------------------------------------------------------------------------------------------------------------------------------------------
            raw_defl = []
            try:
                # -------------------------------------------------------------------------------------------------------------------------------------------------
                # Displacements might be stored as 'y' (vertical), 'dy', or 'dz' depending on grid implementation
                # -------------------------------------------------------------------------------------------------------------------------------------------------
                try: disp_y = self.raw_results.displacements.sel(Loadcase=self.loadcase, Component="y")
                except: disp_y = None
                
                try: disp_dy = self.raw_results.displacements.sel(Loadcase=self.loadcase, Component="dy")
                except: disp_dy = None
                
                try: disp_dz = self.raw_results.displacements.sel(Loadcase=self.loadcase, Component="dz")
                except: disp_dz = None
                
                for n in path_nodes:
                    try:
                        # -------------------------------------------------------------------------------------------------------------------------------------------------
                        # Extract exact node displacement in meters, convert to mm for UI
                        # -------------------------------------------------------------------------------------------------------------------------------------------------
                        val_z = safe_float(disp_dz.sel(Node=n).values.item()) * 1000.0 if disp_dz is not None else 0.0
                        val_dy = safe_float(disp_dy.sel(Node=n).values.item()) * 1000.0 if disp_dy is not None else 0.0
                        val_y = safe_float(disp_y.sel(Node=n).values.item()) * 1000.0 if disp_y is not None else 0.0
                        
                        # -------------------------------------------------------------------------------------------------------------------------------------------------
                        # Use whichever component actually contains vertical bending logic (non-zero)
                        # -------------------------------------------------------------------------------------------------------------------------------------------------
                        val = val_y if abs(val_y) > 0.0 else (val_z if abs(val_z) > abs(val_dy) else val_dy)
                        raw_defl.append(val)
                    except Exception:
                        raw_defl.append(0.0)
            except Exception as e:
                print(f"Warning: Displacements omitted or matrix invalid. Error: {e}")
                raw_defl = np.zeros_like(x_array)
                    
            defl_array = np.nan_to_num(np.array(raw_defl))
            
            self._plot_girder_data(x_array, bmd_array, sfd_array, defl_array)
            
        except Exception as e:
            traceback.print_exc()
            QMessageBox.warning(self, "Data Error", f"Failed to plot data for {girder_name}: {e}")

    def _plot_girder_data(self, x, bmd, sfd, defl):
        """
        Pure rendering engine. Erases old charts and visually repaints strict arrays.
        Enforces identical symmetries between top Girder rendering and bottom Deflection base.
        """
        self._x_data = np.asarray(x)
        self._bmd_data = np.asarray(bmd)
        self._sfd_data = np.asarray(sfd)
        self._defl_data = np.asarray(defl)
        
        for ax in self.all_axes:
            ax.clear()
            
        self._cursors.clear()
        for text_obj in getattr(self, '_max_texts', []):
            try: text_obj.remove()
            except: pass
        self._max_texts = []
        
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Reset visual labels strictly upon UI repaints. Only X gets initial coordinate.
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        if len(self._x_data) > 0:
            self.fields["x"].setText(f"{self._x_data[0]:.3f}")
        for k in ["bmd", "sfd", "defl"]:
            self.fields[k].setText("-")
        
        if len(self._x_data) == 0:
            self._apply_axis_styles()
            self.canvas.draw()
            return

        x_start, x_end = self._x_data[0], self._x_data[-1]
        padding = (x_end - x_start) * 0.05
        
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Consistent label injection (relaxed spacing, slightly lighter weight)
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        LABEL_PROPS = dict(va='center', ha='center', fontsize=10, fontweight='medium', color='#666666')
        
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Shift text up slightly (+0.2 on y-axis of transAxes) inside the label subplots to avoid bottom clipping. It creates artificial visual padding within the dedicated label box.
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        y_label_pos = 0.6
        self.ax_lbl_bmd.text(0.5, y_label_pos, 'Bending Moment Diagram', transform=self.ax_lbl_bmd.transAxes, **LABEL_PROPS)
        self.ax_lbl_sfd.text(0.5, y_label_pos, 'Shear Force Diagram', transform=self.ax_lbl_sfd.transAxes, **LABEL_PROPS)
        self.ax_lbl_defl.text(0.5, y_label_pos, 'Deflection', transform=self.ax_lbl_defl.transAxes, **LABEL_PROPS)

        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Node Reference Lines (Dashed, neutral grey, subtle to not dominate)
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        for node_x in self._x_data:
            for ax in self.plot_axes:
                ax.axvline(node_x, color='#D3D3D3', linestyle='--', linewidth=0.8, zorder=0, alpha=0.9)

        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Top Plot (Girder geometry representation)
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        self.show_girder_diagram = True

        if self.show_girder_diagram:
            # -------------------------------------------------------------------------------------------------------------------------------------------------
            # Revert to standard muted grey weight
            # -------------------------------------------------------------------------------------------------------------------------------------------------
            self.ax_girder.plot([x_start, x_end], [0, 0], color=COLOR_GIRDER_LINE, linewidth=3, zorder=2, alpha=0.9)
            self.ax_girder.set_ylim(-1, 1) 
            self._draw_supports(self.ax_girder, x_start, x_end, is_bottom_plot=False, color=COLOR_GIRDER_LINE, alpha=0.85)

        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Middle Plots (BMD / SFD Matrices)
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        for data, ax in [(self._bmd_data, self.ax_bmd), (self._sfd_data, self.ax_sfd)]:
            ax.fill_between(self._x_data, data, 0, color=COLOR_PRIMARY_FILL, alpha=0.55, zorder=2)
            ax.plot(self._x_data, data, color=COLOR_PRIMARY_STROKE, linewidth=1.5, zorder=3)
            ax.plot([x_start, x_end], [0, 0], color=COLOR_ZERO_LINE, lw=1.2, zorder=1)
            
            y_max, y_min = np.max(data), np.min(data)
            spread = max(abs(y_max), abs(y_min)) * 0.35
            if spread == 0: spread = 1
            ax.set_ylim(min(0, y_min) - spread, max(0, y_max) + spread)

        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Bottom Plot (Deflection Curve)
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        self.ax_defl.fill_between(self._x_data, self._defl_data, 0, color=COLOR_PRIMARY_FILL, alpha=0.35, zorder=2)
        self.ax_defl.plot(self._x_data, self._defl_data, color=COLOR_PRIMARY_STROKE, linewidth=1.8, zorder=3)
        self.ax_defl.plot([x_start, x_end], [0, 0], color=COLOR_ZERO_LINE, lw=1.2, zorder=1)
        
        d_max, d_min = np.max(self._defl_data), np.min(self._defl_data)
        d_pad = max(abs(d_max), abs(d_min)) * 0.4
        if d_pad == 0: d_pad = 1
        
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Physically downward positive inversion applied mathematically
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        self.ax_defl.set_ylim(min(0, d_min) - d_pad, max(0, d_max) + d_pad)

        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Clear generic bounds, implement Figma white gaps constraint loop
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        self.ax_lbl_girder.set_xlim(x_start - padding, x_end + padding)
        self._apply_axis_styles()
        
        self.canvas.draw()

    def _draw_supports(self, ax, x_start, x_end, is_bottom_plot=False, color='#22384C', alpha=1.0):
        """
        Renders primitive structural support diagram physics symmetrically.
        Preserves rigid horizontal proportionality despite wildly shifting Y-axis ranges.
        """
        span = x_end - x_start
        sx = span * 0.012  
        
        ymin, ymax = ax.get_ylim()
        yrange = abs(ymax - ymin)
        
        factor = 0.4
        sy = yrange * factor
        direction = -1
        COLOR_STROKE = color
        
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Minimalist upward-pointing arrows for supports
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        arrow_len = direction * sy * 1.5
        
        for x_loc in [x_start, x_end]:
            ax.annotate('', xy=(x_loc, 0), xytext=(x_loc, arrow_len),
                        arrowprops=dict(arrowstyle='->', color=COLOR_STROKE, lw=1.5, alpha=alpha),
                        zorder=5, annotation_clip=False)
            # -------------------------------------------------------------------------------------------------------------------------------------------------
            # Base horizontal line underneath arrow
            # -------------------------------------------------------------------------------------------------------------------------------------------------
            ax.plot([x_loc - sx*1.5, x_loc + sx*1.5], [arrow_len, arrow_len], color=COLOR_STROKE, lw=1.5, alpha=alpha, zorder=5, clip_on=False)

    def _setup_event_handling(self):
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # We exclusively handle definitive interactions, scrolling is prioritized for continuous flow tracking
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        self.figure.canvas.mpl_connect('button_press_event', self._on_click)
        self.figure.canvas.mpl_connect('scroll_event', self._on_scroll)
        
    def _on_click(self, event):
        """Triggers vertical reference tracking and RHS data population via user click."""
        if self._x_data is None or len(self._x_data) == 0:
            return
        if event.inaxes not in self.plot_axes:
            return
        if event.button != 1:
            return
            
        click_x = max(self._x_data[0], min(self._x_data[-1], event.xdata))
        
        self.mode_combo.blockSignals(True)
        self.mode_combo.setCurrentText("Scroll for Values")
        self.mode_combo.blockSignals(False)
        
        self._set_cursor_x(click_x)

    def _on_scroll(self, event):
        """Scroll interaction moves an invisible preview position, updating the X box ONLY."""
        if len(self._x_data) == 0 or event.inaxes not in self.plot_axes:
            return
            
        try:
            current_x = float(self.fields["x"].text())
        except ValueError:
            current_x = self._x_data[0]
            
        span = self._x_data[-1] - self._x_data[0]
        step = span * 0.05 * event.step 
        new_x = max(self._x_data[0], min(self._x_data[-1], current_x + step))
        
        self.mode_combo.blockSignals(True)
        self.mode_combo.setCurrentText("Scroll for Values")
        self.mode_combo.blockSignals(False)
        
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Only update preview text box; let user confirm
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        self.fields["x"].setText(f"{new_x:.3f}")

    def _on_user_x_entered(self):
        """Handles manual X input routing to update cursor."""
        try:
            val = float(self.fields["x"].text())
            val = max(self._x_data[0], min(self._x_data[-1], val))
            self.mode_combo.blockSignals(True)
            self.mode_combo.setCurrentText("Scroll for Values")
            self.mode_combo.blockSignals(False)
            self._set_cursor_x(val)
        except ValueError:
            pass 

    def _on_mode_changed(self, mode_text):
        """Mode selection driver for finding automatic max thresholds."""
        if len(self._x_data) == 0:
            return
            
        if mode_text == "Scroll for Values":
            # -------------------------------------------------------------------------------------------------------------------------------------------------
            # Do nothing, just wait for user interaction
            # -------------------------------------------------------------------------------------------------------------------------------------------------
            return
            
        if mode_text == "Maximum Values":
            self._show_maximums()

    def _show_maximums(self):
        """Calculates maximums independently, draws 3 vertical lines, updates RHS."""
        idx_bmd = np.argmax(np.abs(self._bmd_data))
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # SFD uses algebraic peak maximum positively
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        idx_sfd = np.argmax(self._sfd_data)
        idx_defl = np.argmax(np.abs(self._defl_data))
        
        x_bmd = self._x_data[idx_bmd]
        x_sfd = self._x_data[idx_sfd]
        x_defl = self._x_data[idx_defl]
        
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Clear maximum text labels if present
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        for text_obj in getattr(self, '_max_texts', []):
            try: text_obj.remove()
            except: pass
        self._max_texts = []
        
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Draw 3 explicit vertical lines
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        self._update_cursors(custom_x_list=[x_bmd, x_sfd, x_defl])
        
        self.fields["x"].setText("Multiple")
        self.fields["bmd"].setText(f"{self._bmd_data[idx_bmd]:.3f}")
        self.fields["sfd"].setText(f"{self._sfd_data[idx_sfd]:.3f}")
        self.fields["defl"].setText(f"{self._defl_data[idx_defl]:.3f}")
        
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Add text labels on the plots for the maximums
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        def add_max_label(ax, x_loc, val, label_name, is_absolute=True):
            y_min, y_max = ax.get_ylim()
            y_pos = y_max - (y_max - y_min) * 0.08
            
            x_span = self._x_data[-1] - self._x_data[0]
            ha = 'center'
            display_x = x_loc
            
            # -------------------------------------------------------------------------------------------------------------------------------------------------
            # Apply padding so the box bounding doesn't touch the plotting perimeter lines
            # -------------------------------------------------------------------------------------------------------------------------------------------------
            if x_loc < self._x_data[0] + x_span * 0.15:
                ha = 'left'
                display_x = x_loc + x_span * 0.02
            elif x_loc > self._x_data[-1] - x_span * 0.15:
                ha = 'right'
                display_x = x_loc - x_span * 0.02
                
            label_text = f"Max |{label_name}|" if is_absolute else f"Max {label_name}"
            val_text = f"{abs(val):.2f}" if is_absolute else f"{val:.2f}"
            
            txt = ax.text(display_x, y_pos, f"{label_text} = {val_text}\nat x = {x_loc:.3f} m",
                          color=COLOR_CURSOR, fontsize=9, fontweight='bold',
                          bbox=dict(facecolor='white', edgecolor=COLOR_SEPARATOR, alpha=0.9, pad=4),
                          ha=ha, va='top', zorder=20)
            self._max_texts.append(txt)
            
        add_max_label(self.ax_bmd, x_bmd, self._bmd_data[idx_bmd], "BMD", True)
        add_max_label(self.ax_sfd, x_sfd, self._sfd_data[idx_sfd], "SFD", False)
        add_max_label(self.ax_defl, x_defl, self._defl_data[idx_defl], "Defl.", True)
        
        self.canvas.draw_idle()

    def _set_cursor_x(self, x_val):
        """Generalized setter mapping UI state cleanly."""
        m_x = np.interp(x_val, self._x_data, self._bmd_data)
        v_x = np.interp(x_val, self._x_data, self._sfd_data)
        d_x = np.interp(x_val, self._x_data, self._defl_data)
        
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Clear maximum text labels if present
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        for text_obj in getattr(self, '_max_texts', []):
            try: text_obj.remove()
            except: pass
        self._max_texts = []
        
        self._update_cursors(custom_x_list=[x_val, x_val, x_val])
        self._update_rhs_display(x_val, m_x, v_x, d_x)
        
    def _update_cursors(self, click_x=None, custom_x_list=None):
        """Draws cursor lines strictly isolated within each plotting boundary. Never cuts labels."""
        if custom_x_list is None:
            custom_x_list = [click_x, click_x, click_x]
            
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Only inject the cursor into axes representing the strict data bodies, preserving white space We ensure no axes lines overlap into the distinct label/gap GridSpec objects we configured above.
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        if not self._cursors:
            for i, ax in enumerate(self.plot_axes):
                cursor = ax.axvline(custom_x_list[i], color='#78909C', linestyle='-', linewidth=1.2, zorder=10, alpha=0.9)
                self._cursors.append(cursor)
        else:
            for i, cursor in enumerate(self._cursors):
                cursor.set_xdata([custom_x_list[i], custom_x_list[i]])
                
        self.canvas.draw_idle()

    def _update_rhs_display(self, x, m, v, d):
        self.fields["x"].setText(f"{x:.3f}")
        self.fields["bmd"].setText(f"{m:.3f}")
        self.fields["sfd"].setText(f"{v:.3f}")
        self.fields["defl"].setText(f"{d:.3f}")
