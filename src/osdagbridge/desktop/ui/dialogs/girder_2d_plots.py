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
<<<<<<< Updated upstream

# -------------------------------------------------------------------------------------------------------------------------------------------------
# UI / Visual Configuration
# -------------------------------------------------------------------------------------------------------------------------------------------------
COLOR_PRIMARY_FILL = "#355C9A"      # Muted teal fill
COLOR_PRIMARY_STROKE = "#355C9A"    # osdag teal stroke
COLOR_ZERO_LINE = "#B0BEC5"         # Soft grey zero line
COLOR_GIRDER_LINE = "#90A4AE"       # Minimal structural line
COLOR_SEPARATOR = "#E0E0E0"         # Soft visual boundary / bounding box
COLOR_DEFLECTION_LINE = "#C0392B"   # Red stroke
COLOR_DEFLECTION_FILL = "#C0392B"   # Muted Red fill

class Girder2DPlotsWidget(QWidget):
    """
    PySide6 widget representing a generic 2D girder plot.
=======

class Girder2DPlotsWidget(QWidget):
    """
    Production-ready PySide6 widget representing a generic 2D girder plot.
>>>>>>> Stashed changes
    Displays vertically stacked plots:
    1. Girder (Structural reference)
    2. Bending Moment Diagram (BMD)
    3. Shear Force Diagram (SFD)
    4. Deflection Diagram
    
<<<<<<< Updated upstream
=======
    Acts as a single source of truth for extracting, parsing, and rendering
    OpenSees Physics matrices for individual spans. No external helpers required.
>>>>>>> Stashed changes
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
        
<<<<<<< Updated upstream
        self.current_x_position = 0.0
=======
>>>>>>> Stashed changes
        self._cursors = []
        
        self._init_ui()

    def _init_ui(self):
        """Initializes the layout, top controls, RHS value boxes, and Matplotlib canvas."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(10)
        
<<<<<<< Updated upstream
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Top Controls: Girder Selection
        # -------------------------------------------------------------------------------------------------------------------------------------------------
=======
        # ---------------------------------------------------------
        # Top Controls: Girder Selection
        # ---------------------------------------------------------
>>>>>>> Stashed changes
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
        
<<<<<<< Updated upstream
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
=======
        controls_layout.addWidget(lbl_select)
        controls_layout.addWidget(self.girder_combo)
>>>>>>> Stashed changes
        controls_layout.addStretch()
        
        self.main_layout.addLayout(controls_layout)
        
<<<<<<< Updated upstream
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Bottom Body: Split between Charts and RHS
        # -------------------------------------------------------------------------------------------------------------------------------------------------
=======
        # ---------------------------------------------------------
        # Bottom Body: Split between Charts and RHS
        # ---------------------------------------------------------
>>>>>>> Stashed changes
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(10)
        
<<<<<<< Updated upstream
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Left Side: Matplotlib Figure
        # -------------------------------------------------------------------------------------------------------------------------------------------------
=======
        # Left Side: Matplotlib Figure
>>>>>>> Stashed changes
        self.figure = Figure(figsize=(8, 10))
        self.figure.patch.set_facecolor('#FFFFFF')
        self.canvas = FigureCanvas(self.figure)
        body_layout.addWidget(self.canvas, stretch=4)
        
<<<<<<< Updated upstream
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Right Side: Values Display Panel
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        self.val_panel = QFrame()
        self.val_panel.setStyleSheet("QFrame { background-color: #FAFAFA; border: 1px solid #CCCCCC; border-radius: 4px; }")
        self.val_panel.setFixedWidth(250)
=======
        # Right Side: Values Display Panel
        self.val_panel = QFrame()
        self.val_panel.setStyleSheet("QFrame { background-color: #FAFAFA; border: 1px solid #DFDFDF; border-radius: 4px; }")
        self.val_panel.setFixedWidth(180)
>>>>>>> Stashed changes
        
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
<<<<<<< Updated upstream
            if key == "x":
                val.setReadOnly(False)
                val.setToolTip("Enter X position and press Return")
                val.setPlaceholderText("Enter x value")
                val.setText("")
            else:
                val.setReadOnly(True)
=======
            val.setReadOnly(True)
>>>>>>> Stashed changes
            val.setAlignment(Qt.AlignCenter)
            val.setStyleSheet("""
                QLineEdit {
                    background-color: #FFFFFF;
<<<<<<< Updated upstream
                    border: 1px solid #B0B0B0;
=======
                    border: 1px solid #CCCCCC;
>>>>>>> Stashed changes
                    border-radius: 3px;
                    padding: 5px;
                    color: #111111;
                    font-size: 11px;
                }
<<<<<<< Updated upstream
                QLineEdit:read-only {
                    background-color: #F8F9FA;
                    color: #444444;
                }
=======
>>>>>>> Stashed changes
            """)
            
            l.addWidget(lbl)
            l.addWidget(val)
            l.setAlignment(Qt.AlignCenter)
            self.fields[key] = val
            return container

<<<<<<< Updated upstream
        box_x = create_value_box("x = _ (m)", "x")
        self.fields["x"].returnPressed.connect(self._on_user_x_entered)
        box_bmd = create_value_box("BMD = _ (kNm)", "bmd")
        box_sfd = create_value_box("SFD = _ (kN)", "sfd")
        box_defl = create_value_box("Deflection = _ (mm)", "defl")

        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Proportional UI Layout: Stretch factors synchronize PySide RHS boxes visually with Matplotlib axes heights
        # -------------------------------------------------------------------------------------------------------------------------------------------------
=======
        box_x = create_value_box("X Position (m)", "x")
        box_bmd = create_value_box("BMD (kNm)", "bmd")
        box_sfd = create_value_box("SFD (kN)", "sfd")
        box_defl = create_value_box("Deflection (mm)", "defl")

        # Proportional stretching to align natively with matplotlib axes vertical scales
        # Now that Labels are BELOW the plots, the top stretch starts directly at the Girder plot!
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Subplot Layout: Adjust 'hspace' and label row height-ratios to prevent visual cramping between separate charts
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        gs = gridspec.GridSpec(8, 1, figure=self.figure, 
                               height_ratios=[0.5, 0.8, 3, 0.8, 3, 0.8, 3, 0.8], 
                               hspace=0.15)
        
        self.figure.subplots_adjust(left=0.15, right=0.95, top=0.92, bottom=0.10)
        
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Primary reference axis (Girder reintroduced)
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        self.ax_girder = self.figure.add_subplot(gs[0])
        self.ax_lbl_girder = self.figure.add_subplot(gs[1], sharex=self.ax_girder)
        self.ax_girder.set_visible(True)
        self.ax_lbl_girder.set_visible(True)
=======
        """
        Configures the axes using GridSpec to stack the 4 sections.
        Ensures HSpace=0 to maintain single coherent reference lines.
        """
        gs = gridspec.GridSpec(8, 1, figure=self.figure, 
                               height_ratios=[0.8, 0.15, 3, 0.15, 3, 0.15, 3, 0.15], 
                               hspace=0)
        
        self.figure.subplots_adjust(left=0.08, right=0.95, top=0.95, bottom=0.05)
        
        # Primary reference axis
        self.ax_girder = self.figure.add_subplot(gs[0])
        self.ax_lbl_girder = self.figure.add_subplot(gs[1], sharex=self.ax_girder)
>>>>>>> Stashed changes
        
        self.ax_bmd = self.figure.add_subplot(gs[2], sharex=self.ax_girder)
        self.ax_lbl_bmd = self.figure.add_subplot(gs[3], sharex=self.ax_girder)
        
        self.ax_sfd = self.figure.add_subplot(gs[4], sharex=self.ax_girder)
        self.ax_lbl_sfd = self.figure.add_subplot(gs[5], sharex=self.ax_girder)
        
        self.ax_defl = self.figure.add_subplot(gs[6], sharex=self.ax_girder)
        self.ax_lbl_defl = self.figure.add_subplot(gs[7], sharex=self.ax_girder)
        
<<<<<<< Updated upstream
        self.all_axes = [self.ax_girder, self.ax_lbl_girder,
                         self.ax_bmd, self.ax_lbl_bmd,
                         self.ax_sfd, self.ax_lbl_sfd,
                         self.ax_defl, self.ax_lbl_defl]
                         
        self.plot_axes = [self.ax_bmd, self.ax_sfd, self.ax_defl]
=======
        self.all_axes = [self.ax_lbl_girder, self.ax_girder, 
                         self.ax_lbl_bmd, self.ax_bmd, 
                         self.ax_lbl_sfd, self.ax_sfd, 
                         self.ax_lbl_defl, self.ax_defl]
                         
        self.plot_axes = [self.ax_girder, self.ax_bmd, self.ax_sfd, self.ax_defl]
>>>>>>> Stashed changes
        
    def _apply_axis_styles(self):
        """
        Applies strict engineering design constraints:
<<<<<<< Updated upstream
        - Soft bounding boxes for visual separation
=======
        - No black edges/boundaries. All borders invisible.
>>>>>>> Stashed changes
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

<<<<<<< Updated upstream
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Visual Containment: Apply unheavy bounding boxes around primary plotting areas to group the diagrams
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        for ax in self.plot_axes:
            for spine in ax.spines.values():
                spine.set_visible(True)
                spine.set_color(COLOR_SEPARATOR)
                spine.set_linewidth(1.0)
                
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Layout Edge Case Fix: Explicitly reinforce bottom spines to counteract GridSpec hspace gaps
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
            
            # -------------------------------------------------------------------------------------------------------------------------------------------------
            # Convert raw OpenSees values from base SI (N, N.m) to display units (kN, kN.m)
            # -------------------------------------------------------------------------------------------------------------------------------------------------
            bmd_array = np.array(raw_bmd, dtype=float) / 1000.0
            sfd_array = np.array(raw_sfd, dtype=float) / 1000.0

            # -------------------------------------------------------------------------------------------------------------------------------------------------
            # BMD Validation: Enforce flat zero line for fully NaN arrays, clean partial NaNs
            # -------------------------------------------------------------------------------------------------------------------------------------------------
            if np.all(np.isnan(bmd_array)):
                bmd_array = np.zeros_like(bmd_array)
            elif np.any(np.isnan(bmd_array)):
                bmd_array = np.nan_to_num(bmd_array)

            # -------------------------------------------------------------------------------------------------------------------------------------------------
            # SFD Validation: Enforce flat zero line for fully NaN arrays, clean partial NaNs
            # -------------------------------------------------------------------------------------------------------------------------------------------------
            if np.all(np.isnan(sfd_array)):
                sfd_array = np.zeros_like(sfd_array)
            elif np.any(np.isnan(sfd_array)):
                sfd_array = np.nan_to_num(sfd_array)

            # -------------------------------------------------------------------------------------------------------------------------------------------------
            # Vertical Deflection Extraction: OpenSees matrices map nodes non-sequentially, requiring explicit lookup by Node Tag. Vertical is typically 'dy'.
            # -------------------------------------------------------------------------------------------------------------------------------------------------
            raw_defl = []
            component_used = "dy"
            
            try:
                # -------------------------------------------------------------------------------------------------------------------------------------------------
                # Explicit Component Binding: Lock to 'dy' (vertical) to prevent silent fallback errors across UI configurations
                # -------------------------------------------------------------------------------------------------------------------------------------------------
                disp_dy = self.raw_results.displacements.sel(Loadcase=self.loadcase, Component=component_used)
                
                for n in path_nodes:
                    try:
                        # Extract exact node displacement in meters, convert to mm for UI
                        val_dy = float(disp_dy.sel(Node=n).values.item()) * 1000.0
                        raw_defl.append(val_dy)
                    except Exception:
                        raw_defl.append(np.nan)
            except Exception as e:
                # Fallback to NaN arrays if extraction fails
                raw_defl = np.full(len(x_array), np.nan).tolist()

            defl_array = np.array(raw_defl, dtype=float)

            # -------------------------------------------------------------------------------------------------------------------------------------------------
            # Deflection Validation: Enforce flat zero line for fully NaN arrays, clean partial NaNs
            # -------------------------------------------------------------------------------------------------------------------------------------------------
            if np.all(np.isnan(defl_array)):
                defl_array = np.zeros_like(x_array)
            elif np.any(np.isnan(defl_array)):
                defl_array = np.nan_to_num(defl_array)

            self._plot_girder_data(x_array, bmd_array, sfd_array, defl_array)
            
        except Exception as e:
            traceback.print_exc()
            QMessageBox.warning(self, "Data Error", f"Failed to plot data for {girder_name}: {e}")

=======
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
            # Assume opensees engine has finished analysis logic before handing off
            self.raw_results = self.analyser_model.model.get_results()
            self.ar_helper = PlateGirderAnalysisResults(self.raw_results, self.analyser_model.model)
            self.girder_map, _ = self.ar_helper.build_girders(verbose=False)
            
            # Sort girders naturally (g1, g2, g3)
            girders_found = sorted(self.girder_map.keys(), key=lambda x: int(x.replace('g', '')) if 'g' in x else x)
            
            if not girders_found:
                QMessageBox.warning(self, "Data Error", "No continuous girders found in the grillage topology.")
                return
                
            self.girder_combo.blockSignals(True)
            self.girder_combo.clear()
            self.girder_combo.addItems(girders_found)
            self.girder_combo.blockSignals(False)
            self.girder_combo.setEnabled(True)
            
            # Auto-plot the very first girder in the model
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
            # Extract absolute spatial ordering of nodes
            nodes, _, _ = self.ar_helper.build_grillage_connectivity()
            
            x_raw = [nodes[n][0] for n in path_nodes]
            # Normalizing X-axis span to always commence strictly from 0 natively
            offset = min(x_raw)
            x_array = np.array([x - offset for x in x_raw])
            
            # Extract physics force matrices
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
            
            # Vertical Deflection matrix extraction
            # OpenSees matrices map nodes non-sequentially. We must extract by explicit Node ID tags.
            # Z is typically the vertical axis in our 3D bridge grillage, but we fallback to Y if it's 2D.
            raw_defl = []
            try:
                # Displacements might be stored as 'y' (vertical), 'dy', or 'dz' depending on grid implementation
                try: disp_y = self.raw_results.displacements.sel(Loadcase=self.loadcase, Component="y")
                except: disp_y = None
                
                try: disp_dy = self.raw_results.displacements.sel(Loadcase=self.loadcase, Component="dy")
                except: disp_dy = None
                
                try: disp_dz = self.raw_results.displacements.sel(Loadcase=self.loadcase, Component="dz")
                except: disp_dz = None
                
                for n in path_nodes:
                    try:
                        # Extract exact node displacement in meters, convert to mm for UI
                        val_z = safe_float(disp_dz.sel(Node=n).values.item()) * 1000.0 if disp_dz is not None else 0.0
                        val_dy = safe_float(disp_dy.sel(Node=n).values.item()) * 1000.0 if disp_dy is not None else 0.0
                        val_y = safe_float(disp_y.sel(Node=n).values.item()) * 1000.0 if disp_y is not None else 0.0
                        
                        # Use whichever component actually contains vertical bending logic (non-zero)
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

>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
        for text_obj in getattr(self, '_max_texts', []):
            try: text_obj.remove()
            except: pass
        self._max_texts = []
        
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Reset visual labels strictly upon UI repaints. Only X gets initial coordinate.
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        if len(self._x_data) == 0:
            for k in ["bmd", "sfd", "defl"]:
                self.fields[k].setText("-")
            self.fields["x"].clear()
=======
        
        # Reset visual labels strictly upon UI repaints
        self._update_rhs_display(0, 0, 0, 0)
        
        if len(self._x_data) == 0:
>>>>>>> Stashed changes
            self._apply_axis_styles()
            self.canvas.draw()
            return

        x_start, x_end = self._x_data[0], self._x_data[-1]
        padding = (x_end - x_start) * 0.05
        
<<<<<<< Updated upstream
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Consistent label injection (relaxed spacing, slightly lighter weight)
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        LABEL_PROPS = dict(va='center', ha='center', fontsize=10, fontweight='medium', color='#666666')
        
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Typographic Adjustment: Shift Y-axis position to prevent bottom clipping inside narrow GridSpec label boxes
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        y_label_pos = 0.5
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
            self.ax_girder.set_ylim(-3.0, 1.0) 
            self._draw_supports(self.ax_girder, x_start, x_end, is_bottom_plot=False, color=COLOR_GIRDER_LINE, alpha=0.85)

        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Middle Plots (BMD / SFD Matrices)
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        for data, ax, c_line, c_fill in [
            (self._bmd_data, self.ax_bmd, COLOR_PRIMARY_STROKE, COLOR_PRIMARY_FILL),
            (self._sfd_data, self.ax_sfd, COLOR_PRIMARY_STROKE, COLOR_PRIMARY_FILL)
        ]:
            ax.fill_between(self._x_data, data, 0, color=c_fill, alpha=0.25, zorder=2)
            ax.plot(self._x_data, data, color=c_line, linewidth=1.5, zorder=3)
            ax.plot([x_start, x_end], [0, 0], color=COLOR_ZERO_LINE, lw=1.2, zorder=1)
            
            y_max, y_min = np.max(data), np.min(data)
            spread = max(abs(y_max), abs(y_min)) * 0.35
            if spread == 0: spread = 1
            ax.set_ylim(min(0, y_min) - spread, max(0, y_max) + spread)

        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Bottom Plot (Deflection Curve)
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        self.ax_defl.fill_between(self._x_data, self._defl_data, 0, color=COLOR_DEFLECTION_FILL, alpha=0.35, zorder=2)
        self.ax_defl.plot(self._x_data, self._defl_data, color=COLOR_DEFLECTION_LINE, linewidth=1.8, zorder=3)
        self.ax_defl.plot([x_start, x_end], [0, 0], color=COLOR_ZERO_LINE, lw=1.2, zorder=1)
        
        d_max, d_min = np.max(self._defl_data), np.min(self._defl_data)
        d_pad = max(abs(d_max), abs(d_min)) * 0.4
        if d_pad == 0: d_pad = 1
        
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Y-Axis Inversion: Mathematically apply padding to deflection bounds while honoring downward-positive rendering
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        self.ax_defl.set_ylim(min(0, d_min) - d_pad, max(0, d_max) + d_pad)

        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Visual Bounds: Apply constraint loop to enforce Figma-specified white gaps
        # -------------------------------------------------------------------------------------------------------------------------------------------------
=======
        # Figma Standard Colors
        COLOR_GIRDER = '#22384C'    
        COLOR_FILL = '#6B9CCC'      
        COLOR_STROKE = '#2F5A82'    
        COLOR_DEFL = '#0A0A0A'      
        COLOR_SUPPORT = '#D0D0D0'   # Light Grey boundaries, NOT black
        COLOR_ZERO = '#8C8C8C'      
        
        # Consistent label injection (center alignment strictly forced above the active chart)
        LABEL_PROPS = dict(va='center', ha='center', fontsize=10, fontweight='bold', color='#333333')
        self.ax_lbl_girder.text(0.5, 0.5, '', transform=self.ax_lbl_girder.transAxes, **LABEL_PROPS)
        self.ax_lbl_bmd.text(0.5, 0.5, 'BMD', transform=self.ax_lbl_bmd.transAxes, **LABEL_PROPS)
        self.ax_lbl_sfd.text(0.5, 0.5, 'SFD', transform=self.ax_lbl_sfd.transAxes, **LABEL_PROPS)
        self.ax_lbl_defl.text(0.5, 0.5, 'Deflections', transform=self.ax_lbl_defl.transAxes, **LABEL_PROPS)

        # ------------------------------------------------------------------
        # Top Plot (Girder geometry representation)
        # ------------------------------------------------------------------
        self.ax_girder.plot([x_start, x_end], [0, 0], color=COLOR_GIRDER, linewidth=7, zorder=2)
        self.ax_girder.set_ylim(-1, 1) 
        self._draw_supports(self.ax_girder, x_start, x_end, is_bottom_plot=False, color=COLOR_GIRDER)

        # ------------------------------------------------------------------
        # Middle Plots (BMD / SFD Matrices)
        # ------------------------------------------------------------------
        for data, ax in [(self._bmd_data, self.ax_bmd), (self._sfd_data, self.ax_sfd)]:
            ax.fill_between(self._x_data, data, 0, color=COLOR_FILL, alpha=0.55, zorder=2)
            ax.plot(self._x_data, data, color=COLOR_STROKE, linewidth=1.5, zorder=3)
            ax.plot([x_start, x_end], [0, 0], color=COLOR_ZERO, lw=1.2, zorder=1)
            
            y_max, y_min = np.max(data), np.min(data)
            spread = max(abs(y_max), abs(y_min)) * 0.2
            if spread == 0: spread = 1
            ax.set_ylim(min(0, y_min) - spread, max(0, y_max) + spread)

        # ------------------------------------------------------------------
        # Bottom Plot (Deflection Curve)
        # ------------------------------------------------------------------
        # Deflection vector displacement
        self.ax_defl.plot(self._x_data, self._defl_data, color=COLOR_DEFL, linewidth=1.8, zorder=3)
        self.ax_defl.plot([x_start, x_end], [0, 0], color=COLOR_ZERO, lw=1.2, zorder=1)
        
        d_max, d_min = np.max(self._defl_data), np.min(self._defl_data)
        d_pad = max(abs(d_max), abs(d_min)) * 0.4
        if d_pad == 0: d_pad = 1
        
        # Physically downward positive inversion applied mathematically
        self.ax_defl.set_ylim(min(0, d_min) - d_pad, max(0, d_max) + d_pad)
        self._draw_supports(self.ax_defl, x_start, x_end, is_bottom_plot=True, color=COLOR_GIRDER)

        # ------------------------------------------------------------------
        # Standardized Dotted Reference Lines (Left/Right boundaries)
        # ------------------------------------------------------------------
        # Passes downward smoothly from the top Girder plot, stopping at the bottom label
        vertical_span_axes = [self.ax_girder, self.ax_lbl_girder,
                              self.ax_bmd, self.ax_lbl_bmd, 
                              self.ax_sfd, self.ax_lbl_sfd, 
                              self.ax_defl, self.ax_lbl_defl]
        
        for ax in vertical_span_axes:
            ax.axvline(x_start, color=COLOR_SUPPORT, linestyle=':', linewidth=1.5, zorder=0)
            ax.axvline(x_end, color=COLOR_SUPPORT, linestyle=':', linewidth=1.5, zorder=0)

        # Clear generic bounds, implement Figma white gaps constraint loop
>>>>>>> Stashed changes
        self.ax_lbl_girder.set_xlim(x_start - padding, x_end + padding)
        self._apply_axis_styles()
        
        self.canvas.draw()
<<<<<<< Updated upstream
        
        if self.mode_combo.currentText() == "Maximum Values":
            self._show_maximums()
        else:
            self.fields["x"].clear()
            for k in ["bmd", "sfd", "defl"]:
                self.fields[k].setText("-")

    def _draw_supports(self, ax, x_start, x_end, is_bottom_plot=False, color='#22384C', alpha=1.0):
        """
        Renders primitive structural support diagram physics symmetrically.
        """
        # TODO: Actual support conditions (and future reactions/loads) will be extracted 
        # from analysis_results. For now, display simple vertical upward arrows to represent generic supports.
        
        COLOR_STROKE = color
        
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Support Graphics: Utilize absolute point-offsets to guarantee visible arrow shafts regardless of axis aspect ratio
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        for x_loc in [x_start, x_end]:
            # Use 26pt length total, and 12pt arrowhead -> always yields a distinct 14pt shaft.
            ax.annotate('', xy=(x_loc, 0), xycoords='data',
                        xytext=(0, -26), textcoords='offset points',
                        arrowprops=dict(arrowstyle='->', color=COLOR_STROKE, lw=2.0, mutation_scale=12, shrinkA=0, shrinkB=0, alpha=alpha),
                        zorder=5, annotation_clip=False)

    def _setup_event_handling(self):
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # We exclusively handle definitive interactions based on discrete Structural Nodes.
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        self.figure.canvas.mpl_connect('button_press_event', self._on_click)
        self.figure.canvas.mpl_connect('key_press_event', self._on_key_press)
        # Scroll event explicitly disconnected from cursor movement
        self.figure.canvas.mpl_connect('scroll_event', self._on_scroll)
        
    def move_cursor_to_x(self, x_val):
        """
        SINGLE SOURCE OF TRUTH for cursor movement and RHS value updates.
        Allows exact continuous position inspection between discrete structural nodes.
        """
        if self._x_data is None or len(self._x_data) == 0:
            return
            
        # Ensure position bounds
        self.current_x_position = max(self._x_data[0], min(self._x_data[-1], float(x_val)))
        
        # Extract continuous values via linear interpolation
        m_x = np.interp(self.current_x_position, self._x_data, self._bmd_data)
        v_x = np.interp(self.current_x_position, self._x_data, self._sfd_data)
        d_x = np.interp(self.current_x_position, self._x_data, self._defl_data)
        
        # Switch mode visually if necessary
        self.mode_combo.blockSignals(True)
        self.mode_combo.setCurrentText("Scroll for Values")
        self.mode_combo.blockSignals(False)

        # Clear maximum text labels if present
        for text_obj in getattr(self, '_max_texts', []):
            try: text_obj.remove()
            except: pass
        self._max_texts = []
        
        # Update UI Subcomponents
        self._update_cursors(custom_x_list=[self.current_x_position, self.current_x_position, self.current_x_position])
        self._update_rhs_display(self.current_x_position, m_x, v_x, d_x)
        
    def _on_key_press(self, event):
        """Allows discrete node-to-node navigation using Arrow keys for quick scanning."""
        if self._x_data is None or len(self._x_data) == 0:
            return
            
        # Find which discrete node we are at or closest to
        nearest_idx = (np.abs(self._x_data - self.current_x_position)).argmin()
            
        if event.key == 'right':
            next_idx = min(len(self._x_data) - 1, nearest_idx + 1)
            self.move_cursor_to_x(self._x_data[next_idx])
        elif event.key == 'left':
            prev_idx = max(0, nearest_idx - 1)
            self.move_cursor_to_x(self._x_data[prev_idx])
        
    def _on_click(self, event):
        """Places the cursor exactly at the clicked geometric X-coordinate."""
        if self._x_data is None or len(self._x_data) == 0:
            return
        if event.inaxes not in self.plot_axes:
            return
        if event.button != 1:
            return
            
        # Exact position interaction
        self.move_cursor_to_x(event.xdata)
        
        # Focus on canvas to capture arrow key presses seamlessly
        self.canvas.setFocus()

    def _on_scroll(self, event):
        """
        Scroll wheel interaction intentionally disabled for cursor movement.
        Enforces click/arrow navigation for strict engineering UX without floating errors.
        """
        pass

    def _on_user_x_entered(self):
        """Handles manual X input routing to perfectly place the cursor at any exact coordinate."""
        try:
            val = float(self.fields["x"].text())
            self.move_cursor_to_x(val)
        except ValueError:
            pass 

    def _on_mode_changed(self, mode_text):
        """Mode selection driver for finding automatic max thresholds."""
        if len(self._x_data) == 0:
            return
            
        if mode_text == "Scroll for Values":
            for cursor in self._cursors:
                try: cursor.remove()
                except: pass
            self._cursors.clear()
            
            for text_obj in getattr(self, '_max_texts', []):
                try: text_obj.remove()
                except: pass
            self._max_texts = []
            
            self.fields["x"].clear()
            for k in ["bmd", "sfd", "defl"]:
                self.fields[k].setText("-")
                
            self.canvas.draw_idle()
            return
            
        if mode_text == "Maximum Values":
            self._show_maximums()

    def _show_maximums(self):
        """Calculates maximums independently, draws 3 vertical lines, updates RHS."""
        idx_bmd = np.argmax(np.abs(self._bmd_data))
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # SFD uses true mathematical maximum, not absolute maximum
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
        
        if abs(x_bmd - x_sfd) < 1e-4 and abs(x_sfd - x_defl) < 1e-4:
            self.fields["x"].setText(f"{x_bmd:.2f}")
        else:
            self.fields["x"].setText("Multiple")
            
        self.fields["bmd"].setText(f"max = {self._bmd_data[idx_bmd]:.2f} kNm at x = {x_bmd:.2f} m")
        self.fields["sfd"].setText(f"max = {self._sfd_data[idx_sfd]:.2f} kN at x = {x_sfd:.2f} m")
        self.fields["defl"].setText(f"max = {self._defl_data[idx_defl]:.2f} mm at x = {x_defl:.2f} m")
        
        self.canvas.draw_idle()
        
    def _update_cursors(self, click_x=None, custom_x_list=None):
        """Draws cursor lines strictly isolated within each plotting boundary. Never cuts labels."""
        if custom_x_list is None:
            custom_x_list = [click_x, click_x, click_x]
            
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        # Cursor Injection: Target strict data axes exclusively to prevent cursor lines from bleeding into whitespace gaps
        # -------------------------------------------------------------------------------------------------------------------------------------------------
        if not self._cursors:
            for i, ax in enumerate(self.plot_axes):
                cursor = ax.axvline(custom_x_list[i], color='#78909C', linestyle='--', linewidth=1.2, zorder=10, alpha=0.9)
                self._cursors.append(cursor)
        else:
            for i, cursor in enumerate(self._cursors):
                cursor.set_xdata([custom_x_list[i], custom_x_list[i]])
=======

    def _draw_supports(self, ax, x_start, x_end, is_bottom_plot=False, color='#22384C'):
        """
        Renders primitive structural support diagram physics symmetrically.
        Preserves rigid horizontal proportionality despite wildly shifting Y-axis ranges.
        """
        span = x_end - x_start
        sx = span * 0.012  
        
        ymin, ymax = ax.get_ylim()
        yrange = abs(ymax - ymin)
        
        height_ratio = 3.0 if is_bottom_plot else 0.8
        factor = 0.4 * (0.8 / height_ratio)
        sy = yrange * factor
        
        # Deflection plot computes visually downward using positive mathematics due to y-inversion
        direction = 1 if is_bottom_plot else -1

        COLOR_FILL = '#DFDFDF'
        COLOR_STROKE = color
        
        # --- Left Support: Pin ---
        base_y_pin = direction * sy
        ax.fill([x_start, x_start-sx, x_start+sx], [0, base_y_pin, base_y_pin], 
                color=COLOR_FILL, edgecolor=COLOR_STROKE, lw=1.2, zorder=5, clip_on=False)
        ax.plot([x_start-sx*1.5, x_start+sx*1.5], [base_y_pin, base_y_pin], 
                color=COLOR_STROKE, lw=1.5, zorder=5, clip_on=False)

        # --- Right Support: Roller ---
        roller_sy = sy * 0.75
        base_y_roller = direction * roller_sy
        ax.fill([x_end, x_end-sx, x_end+sx], [0, base_y_roller, base_y_roller], 
                color=COLOR_FILL, edgecolor=COLOR_STROKE, lw=1.2, zorder=5, clip_on=False)
        
        r_radius = sy * 0.125
        cy = base_y_roller + direction * r_radius
        ax.plot(x_end - sx*0.5, cy, marker='o', markersize=4, color='white', 
                markeredgecolor=COLOR_STROKE, zorder=5, clip_on=False)
        ax.plot(x_end + sx*0.5, cy, marker='o', markersize=4, color='white', 
                markeredgecolor=COLOR_STROKE, zorder=5, clip_on=False)
                
        floor_y = cy + direction * r_radius
        ax.plot([x_end-sx*1.5, x_end+sx*1.5], [floor_y, floor_y], 
                color=COLOR_STROKE, lw=1.5, zorder=5, clip_on=False)

    def _setup_event_handling(self):
        # We exclusively handle definitive mouse clicks, prohibiting passive hovering per requirement.
        self.figure.canvas.mpl_connect('button_press_event', self._on_click)
        
    def _on_click(self, event):
        """
        Triggers vertical reference tracking and RHS RHS data population exclusively via user click.
        Cursor persists structurally until next event overrides it.
        """
        if self._x_data is None or len(self._x_data) == 0:
            return
            
        if event.inaxes not in self.plot_axes:
            return
            
        # Register clicks exclusively from left mouse button
        if event.button != 1:
            return
            
        click_x = event.xdata
        if click_x is None:
            return
            
        click_x = max(self._x_data[0], min(self._x_data[-1], click_x))
        
        m_x = np.interp(click_x, self._x_data, self._bmd_data)
        v_x = np.interp(click_x, self._x_data, self._sfd_data)
        d_x = np.interp(click_x, self._x_data, self._defl_data)
        
        self._update_cursors(click_x)
        self._update_rhs_display(click_x, m_x, v_x, d_x)
        
    def _update_cursors(self, click_x):
        """
        Calculates and draws a single structural vertical tracer spanning exclusively through
        physics regions while omitting exterior white spaces.
        """
        vertical_span_axes = [self.ax_girder, self.ax_lbl_girder,
                              self.ax_bmd, self.ax_lbl_bmd, 
                              self.ax_sfd, self.ax_lbl_sfd, 
                              self.ax_defl, self.ax_lbl_defl]
                              
        if not self._cursors:
            for ax in vertical_span_axes:
                cursor = ax.axvline(click_x, color='#444444', linestyle='--', linewidth=1.2, zorder=10)
                self._cursors.append(cursor)
        else:
            for cursor in self._cursors:
                cursor.set_xdata([click_x, click_x])
>>>>>>> Stashed changes
                
        self.canvas.draw_idle()

    def _update_rhs_display(self, x, m, v, d):
<<<<<<< Updated upstream
        self.fields["x"].setText(f"{x:.3f}")
        self.fields["bmd"].setText(f"{m:.2f} kNm")
        self.fields["sfd"].setText(f"{v:.2f} kN")
        self.fields["defl"].setText(f"{d:.2f} mm")
        
# @VT - March 1, 2026
=======
        """Drives payload vectors directly into the physical screen blocks."""
        self.fields["x"].setText(f"{x:.3f}")
        self.fields["bmd"].setText(f"{m:.3f}")
        self.fields["sfd"].setText(f"{v:.3f}")
        self.fields["defl"].setText(f"{d:.3f}")
>>>>>>> Stashed changes
