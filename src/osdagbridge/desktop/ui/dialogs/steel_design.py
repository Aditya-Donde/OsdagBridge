from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QSizeGrip, QSizePolicy, QComboBox, QLabel
)
from PySide6.QtCore import Qt

from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.dialogs.tabs.steel_design_details import SteelDesignDetailsTab
from osdagbridge.desktop.ui.dialogs.tabs.steel_design_analysis import SteelDesignAnalysisTab
from osdagbridge.desktop.ui.dialogs.tabs.steel_design_check import SteelDesignCheckTab

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.gridspec as gridspec



def _flatten_node_path(nodes_raw):
    """
    Convert ospgrillage get_element(options='nodes') output to a flat node path.

    ospgrillage returns a list of per-element node pairs:
        [[n_i, n_j], [n_j, n_k], ...]   (or sometimes a nested list structure)

    We flatten it to an ordered path: [n_i, n_j, n_k, ...]
    de-duplicating consecutive shared nodes.
    """
    path = []
    for item in nodes_raw:
        # item may itself be a list/tuple of (i_node, j_node) …
        if hasattr(item, '__iter__') and not isinstance(item, (int, float)):
            for n in item:
                if isinstance(n, (list, tuple)):
                    for nn in n:
                        if not path or path[-1] != nn:
                            path.append(int(nn))
                else:
                    n = int(n)
                    if not path or path[-1] != n:
                        path.append(n)
        else:
            n = int(item)
            if not path or path[-1] != n:
                path.append(n)
    return path


class SteelDesign(QDialog):
    """
    Main dialog window for the Steel Design section.
    Provides tabs for Details, Analysis Results (with interactive plots), and Design Check.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._main_window = parent
        self.setObjectName("SteelDesign")
        self.resize(1024, 720)
        self.setMinimumSize(900, 520)
        self.setSizeGripEnabled(True)
        self.init_ui()
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border: 1px solid #90AF13;
            }
        """)

    def setupWrapper(self):
        """Sets up the custom frameless window wrapper with a title bar and size grip."""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        self.title_bar = CustomTitleBar(parent=self)
        self.title_bar.setTitle("Steel Design")
        main_layout.addWidget(self.title_bar)

        self.content_widget = QWidget(self)
        main_layout.addWidget(self.content_widget, 1)

        size_grip = QSizeGrip(self)
        size_grip.setFixedSize(16, 16)

        overlay = QHBoxLayout()
        overlay.setContentsMargins(0, 0, 4, 4)
        overlay.addStretch(1)
        overlay.addWidget(size_grip, 0, Qt.AlignBottom | Qt.AlignRight)
        main_layout.addLayout(overlay)

    def init_ui(self):
        """Initializes the main UI components including the tab widget and its contents."""
        self.setupWrapper()

        main_layout = QVBoxLayout(self.content_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(2)

        # ── Tabs ──────────────────────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tabs.setDocumentMode(True)
        self.tabs.tabBar().setExpanding(True)
        self.tabs.tabBar().setUsesScrollButtons(False)
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: none; }
            QTabBar { qproperty-drawBase: 0; }
            QTabBar::tab {
                background: #E6E6E6;
                color: black;
                border: 1px solid #CCCCCC;
                padding: 8px 0px;
                border-radius: 8px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #90AF13;
                color: white;
                font-weight: bold;
                border: 1px solid #90AF13;
            }
            QTabBar::tab:hover { background: #DADADA; }
        """)

        self.details_tab  = SteelDesignDetailsTab(self)
        self.analysis_tab = SteelDesignAnalysisTab(self)
        self.check_tab    = SteelDesignCheckTab(self)

        self.tabs.addTab(self.details_tab,  "Details")
        self.tabs.addTab(self.analysis_tab, "Analysis Results")
        self.tabs.addTab(self.check_tab,    "Design Check")

        main_layout.addWidget(self.tabs)

        if hasattr(self._main_window, "cad_state"):
            self.details_tab.load_data(self._main_window.cad_state)

        # ── Inject plot canvas ───────────────────────────────────────────────
        self._setup_analysis_plots()

    # =========================================================================
    #   PLOT SETUP
    # =========================================================================

    def _setup_analysis_plots(self):
        """Analytical plotting inside the empty UI placeholder."""

        # 1. Figure + Canvas
        self.figure = Figure(figsize=(6, 8))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: transparent;")
        
        # 1.5 Interaction combobox
        self.interaction_combo = QComboBox()
        self.interaction_combo.addItems(["Maximum Values", "Interactive"])
        self.interaction_combo.setFixedWidth(160)
        self.interaction_combo.setMinimumHeight(28)
        self.interaction_combo.setStyleSheet(self.analysis_tab.member_combo.styleSheet())
        self.interaction_combo.currentTextChanged.connect(self._on_interaction_mode_changed)
        
        combo_layout = QHBoxLayout()
        combo_layout.addStretch()
        lbl_mode = QLabel("Interaction:")
        lbl_mode.setStyleSheet("font-size: 11px; font-weight: bold; color: #333;")
        combo_layout.addWidget(lbl_mode)
        combo_layout.addWidget(self.interaction_combo)
        
        canvas_wrapper = QWidget()
        vbox = QVBoxLayout(canvas_wrapper)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.addLayout(combo_layout)
        vbox.addWidget(self.canvas)

        # 2. Swap into the analysis tab's diagram placeholder
        placeholder    = self.analysis_tab.diagram_placeholder
        diagram_layout = placeholder.parentWidget().layout()
        diagram_layout.replaceWidget(placeholder, canvas_wrapper)
        placeholder.hide()

        # 3. Four stacked subplots (Girder schematic + BMD + SFD + Deflection)
        gs = self.figure.add_gridspec(4, 1, height_ratios=[0.4, 1, 1, 1])
        self.ax_scheme = self.figure.add_subplot(gs[0])
        self.ax_bmd  = self.figure.add_subplot(gs[1])
        self.ax_sfd  = self.figure.add_subplot(gs[2])
        self.ax_defl = self.figure.add_subplot(gs[3])
        self.figure.subplots_adjust(left=0.08, right=0.96, top=0.95, bottom=0.08, hspace=0.35)

        for ax in (self.ax_scheme, self.ax_bmd, self.ax_sfd, self.ax_defl):
            ax.set_facecolor('#ffffff')
            ax.grid(False)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.set_yticks([])
            ax.set_ylabel("")
            ax.axhline(0, color='black', linewidth=0)

        self.ax_defl.invert_yaxis()

        # Apply UI styling to RHS fields (expanding and centered)
        for field in list(self.analysis_tab.result_fields.values()) + list(self.analysis_tab.x_fields.values()) + [getattr(self.analysis_tab, "x_input", None)]:
            if field:
                field.setAlignment(Qt.AlignCenter)
                field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # 4. Signal wiring
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.analysis_tab.member_combo.currentIndexChanged.connect(self._update_analysis_plots)
        self.analysis_tab.load_combo.currentIndexChanged.connect(self._update_analysis_plots)
        self.canvas.mpl_connect('button_press_event', self._on_canvas_click)
        self.canvas.mpl_connect('key_press_event', self._on_key_press)
        
        # Give canvas focus so it can capture keys
        self.canvas.setFocusPolicy(Qt.StrongFocus)

        # 5. Interactive state
        self._current_x    = None
        self._current_bmd  = None
        self._current_sfd  = None
        self._current_defl = None

        # 6. Cache flags
        self._cached_model   = None
        self._cached_results = None
        self._girder_map     = {}
        self._data_initialized = False

    # =========================================================================
    #   TAB CHANGE TRIGGER — main pipeline entry point
    # =========================================================================

    def _on_tab_changed(self, index):
        """Triggered when user switches to Analysis Results tab (index 1)."""
        if index != 1:
            return

        # ── Step 1: Discover & cache model ────────────────────────────────────
        if self._cached_model is None:
            self._discover_and_cache_model()

        if self._cached_model is None:
            return

        # ── Step 2: Cache results ──────────────────────────────────────────────
        if self._cached_results is None:
            try:
                self._cached_results = self._cached_model.get_results()
            except Exception as e:
                return

        # ── Step 3: Build girder map (once) ───────────────────────────────────
        if not self._girder_map:
            self._build_girder_map()

        # ── Step 4: Populate member dropdown ──────────────────────────────────
        if self._girder_map and not self._data_initialized:
            self._populate_member_combo()
            self._populate_load_combo()
            self._data_initialized = True

        # ── Step 5: Render ─────────────────────────────────────────────────────
        self._update_analysis_plots()

        # Run our diagnostic checks to compare analyser and UI data
        self._verify_analysis_results()

    # ── Model discovery ───────────────────────────────────────────────────────

    def _discover_and_cache_model(self):
        """
        Locate the ospgrillage model from the application cad_state.
        If analysis has not run yet, instantiate PlateGirderBridge and run it automatically.
        """
        mw = self._main_window

        input_data = {}
        if hasattr(mw, 'backend') and mw.backend:
            try:
                defaults = mw.backend.get_input_values_dict(include_empty=True)
                if defaults:
                    input_data.update(defaults)
            except Exception as e:
                pass

        if hasattr(mw, 'cad_state') and mw.cad_state:
            input_data.update(mw.cad_state)

        if not input_data:
            return

        from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import PlateGirderBridge
        
        bridge_obj = PlateGirderBridge(basic_inputs=input_data, additional_inputs=input_data)
        
        try:
            # .run() handles the DTO, initial sizing, and _prepare_or_run_analysis
            bridge_obj.run(run_analysis=True, include_live_load=True)
        except Exception as e:
            return

        engine = getattr(bridge_obj, '_analysis_engine', None)
        if engine is None:
            return

        model = getattr(engine, 'model', None)
        
        if model is not None:
            self._cached_model = model
            try:
                self._cached_results = self._cached_model.get_results()
            except Exception as e:
                pass

    # ── Girder map construction ────────────────────────────────────────────────

    def _build_girder_map(self):
        """
        Discover all longitudinal girder lines from the ospgrillage mesh topology.

        ospgrillage stores longitudinal elements in `Mesh_obj.long_ele` as:
            [ele_tag, i_node, j_node, z_group, transform_tag]
        and groups them by z_group in `Mesh_obj.z_group_to_ele`.

        Each unique z_group represents one distinct longitudinal beam line (girder).
        Node coordinates are in `Mesh_obj.node_spec[tag]["coordinate"] = [x, y, z]`.
        """
        self._girder_map = {}
        mesh = self._cached_model.Mesh_obj
        node_spec = mesh.node_spec   # {tag: {"coordinate": [x, y, z], "z_group": int, ...}}

        try:
            z_group_to_ele = mesh.z_group_to_ele   # {z_group_int: [[ele_tag, ni, nj, z_group, xfm], ...]}
        except AttributeError:
            return

        # Sort z-groups by the z-coordinate of the first node in the first element
        # so girders are ordered left→right across the bridge width.
        def _z_coord_of_group(z_group):
            elems = z_group_to_ele.get(z_group, [])
            if not elems:
                return 0.0
            first_elem = elems[0]
            ni = first_elem[1]
            try:
                return float(node_spec[ni]["coordinate"][2])  # z-coord
            except (KeyError, IndexError):
                return 0.0

        sorted_z_groups = sorted(z_group_to_ele.keys(), key=_z_coord_of_group)

        for girder_idx, z_group in enumerate(sorted_z_groups):
            raw_elems = z_group_to_ele[z_group]  # list of [ele_tag, ni, nj, z_group, xfm]
            if not raw_elems:
                continue

            # Sort elements by x-coordinate of i-node to get longitudinal order
            def _x_of_elem(elem):
                ni = elem[1]
                try:
                    return float(node_spec[ni]["coordinate"][0])
                except (KeyError, IndexError):
                    return 0.0

            sorted_elems = sorted(raw_elems, key=_x_of_elem)

            # Build element list and ordered node path
            elements = [int(e[0]) for e in sorted_elems]
            path     = [int(e[1]) for e in sorted_elems]   # i-nodes in order
            path.append(int(sorted_elems[-1][2]))           # j-node of last element

            girder_key = f"g{girder_idx + 1}"
            self._girder_map[girder_key] = {
                "elements": elements,
                "path":     path,
            }

    # ── Dropdown helpers ──────────────────────────────────────────────────────

    def _populate_member_combo(self):
        """Fill member_combo with 'Girder 1', 'Girder 2', … labels."""
        combo = self.analysis_tab.member_combo
        combo.blockSignals(True)
        combo.clear()
        for idx, key in enumerate(self._girder_map):
            label = f"Girder {idx + 1}"
            combo.addItem(label, userData=key)   # userData = raw key "g1", "g2", …
        combo.blockSignals(False)

    def _populate_load_combo(self):
        """
        Fill load_combo from actual loadcases present in results.forces.
        Falls back to the static LOAD_COMBINATIONS list if extraction fails.
        """
        combo = self.analysis_tab.load_combo
        try:
            loadcases = list(self._cached_results.forces.coords["Loadcase"].values)
            # Sort: put 'girder self weight' first if present
            preferred_first = "girder self weight"
            if preferred_first in loadcases:
                loadcases.remove(preferred_first)
                loadcases = [preferred_first] + loadcases
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(loadcases)
            combo.blockSignals(False)
        except Exception as e:
            pass

    # =========================================================================
    #   PLOT UPDATE ORCHESTRATOR
    # =========================================================================

    def _update_analysis_plots(self, *args):
        """Master orchestrator — triggered by member or loadcase change."""
        if self._cached_results is None or not self._girder_map:
            self._show_blank_state()
            return

        # Resolve selected member key (raw ospgrillage name)
        combo = self.analysis_tab.member_combo
        member_key = combo.currentData()     # userData set by _populate_member_combo
        if member_key is None:
            member_key = combo.currentText()  # fallback: raw text

        selected_loadcase = self.analysis_tab.load_combo.currentText()

        if not member_key or member_key not in self._girder_map:
            return

        # 1. Extract data arrays
        data = self._extract_member_results(member_key, selected_loadcase)
        if data is None:
            self._show_blank_state()
            return

        xs, bmd, sfd, defl = data
        self._current_x    = xs
        self._current_bmd  = bmd
        self._current_sfd  = sfd
        self._current_defl = defl

        # 2. Maximum bounds
        self._current_max_dict = self._compute_maximums(xs, bmd, sfd, defl)

        # 3. Render
        self._clear_axes()
        
        self._render_plots(xs, bmd, sfd, defl)

        # 4. RHS result panel
        self._update_rhs_fields(self._current_max_dict)
        self._on_interaction_mode_changed()

    # =========================================================================
    #   DATA EXTRACTION
    # =========================================================================

    def _extract_member_results(self, member_key, loadcase):
        """
        Extract x, BMD, SFD, deflection arrays for a given member + loadcase.
        Uses ospgrillage results xarray directly (no PlateGirderAnalysisResults).
        """
        if member_key not in self._girder_map:
            return None

        girder   = self._girder_map[member_key]
        elements = girder["elements"]
        path_nodes = girder["path"]

        try:
            # ── X coordinates ─────────────────────────────────────────────────
            # ospgrillage stores node data in Mesh_obj.node_spec:
            #   {tag: {"coordinate": [x, y, z], "x_group": int, "z_group": int}}
            node_spec = self._cached_model.Mesh_obj.node_spec
            x_raw = []
            for n in path_nodes:
                try:
                    x_raw.append(float(node_spec[n]["coordinate"][0]))
                except (KeyError, IndexError, TypeError):
                    x_raw.append(0.0)

            if not x_raw:
                return None

            offset = min(x_raw)
            xs = np.array([x - offset for x in x_raw], dtype=float)

            # ── BMD & SFD ──────────────────────────────────────────────────────
            forces = self._cached_results.forces

            def _get_force_array(component):
                """Extract per-element scalar from forces xarray for this loadcase."""
                out = []
                try:
                    sel = forces.sel(Loadcase=loadcase, Component=component)
                    for eid in elements:
                        try:
                            v = float(sel.sel(Element=eid).values.item())
                        except Exception:
                            v = 0.0
                        out.append(v)
                except Exception as e:
                    out = [0.0] * len(elements)
                # Append 0.0 to match path_nodes length (n_elements + 1 nodes)
                out.append(0.0)
                return out

            raw_bmd = _get_force_array("Mz_i")
            raw_sfd = _get_force_array("Vy_i")

            bmd = np.array(raw_bmd, dtype=float) / 1000.0   # N·m → kNm
            sfd = np.array(raw_sfd, dtype=float) / 1000.0   # N   → kN

            bmd = np.nan_to_num(bmd)
            sfd = np.nan_to_num(sfd)

            # Trim/pad to match xs length
            bmd = _match_length(bmd, len(xs))
            sfd = _match_length(sfd, len(xs))

            # ── Deflection ────────────────────────────────────────────────────
            disp     = self._cached_results.displacements
            raw_defl = []
            try:
                disp_dy = disp.sel(Loadcase=loadcase, Component="dy")
                for n in path_nodes:
                    try:
                        v = float(disp_dy.sel(Node=n).values.item()) * 1000.0  # m → mm
                        raw_defl.append(v)
                    except Exception:
                        raw_defl.append(np.nan)
            except Exception as e:
                raw_defl = [np.nan] * len(path_nodes)

            defl = np.array(raw_defl, dtype=float)
            defl = np.nan_to_num(defl)
            defl = _match_length(defl, len(xs))

            return xs, bmd, sfd, defl

        except Exception as e:
            return None

    # =========================================================================
    #   COMPUTE MAXIMUMS
    # =========================================================================

    def _compute_maximums(self, xs, bmd, sfd, defl):
        """Find the maximum absolute values for BMD, SFD, and Deflection and their corresponding x-coordinates."""
        idx_m = int(np.argmax(np.abs(bmd)))
        idx_v = int(np.argmax(np.abs(sfd)))
        idx_d = int(np.argmax(np.abs(defl)))
        return {
            "M_max": bmd[idx_m],
            "V_max": sfd[idx_v],
            "D_max": defl[idx_d],
            "x_M": float(xs[idx_m]),
            "x_V": float(xs[idx_v]),
            "x_D": float(xs[idx_d]),
        }

    # =========================================================================
    #   RENDERING
    # =========================================================================

    def _render_plots(self, xs, bmd, sfd, defl):
        """Render BMD / SFD / Deflection on the four stacked axes."""

        # ── Schematic ────────────────────────────────────────────────────────
        self.ax_scheme.plot([xs[0], xs[-1]], [0, 0], color='#90A4AE', linewidth=3)
        self.ax_scheme.annotate("", xy=(xs[0], 0), xytext=(xs[0], -0.2), arrowprops=dict(arrowstyle="->", color='#90A4AE', lw=2))
        self.ax_scheme.annotate("", xy=(xs[-1], 0), xytext=(xs[-1], -0.2), arrowprops=dict(arrowstyle="->", color='#90A4AE', lw=2))
        self.ax_scheme.set_ylim(-0.25, 0.1)
        self.ax_scheme.axis('off')

        for ax in (self.ax_scheme, self.ax_bmd, self.ax_sfd, self.ax_defl):
            for x in xs:
                ax.axvline(x, linestyle=":", linewidth=0.5, color="#bfbfbf")

        # ── BMD ───────────────────────────────────────────────────────────────
        self.ax_bmd.plot(xs, bmd, color='#4C72B0', linewidth=1.5)
        self.ax_bmd.fill_between(xs, bmd, 0, color='#4C72B0', alpha=0.25)
        self.ax_bmd.axhline(0, color='#B0BEC5', linewidth=1.0)
        self.ax_bmd.set_title("Bending Moment Diagram", fontsize=10, pad=5, y=-0.25)
        self.ax_bmd.get_xaxis().set_visible(False)

        # ── SFD ───────────────────────────────────────────────────────────────
        self.ax_sfd.plot(xs, sfd, color='#4C72B0', linewidth=1.5)
        self.ax_sfd.fill_between(xs, sfd, 0, color='#4C72B0', alpha=0.25)
        self.ax_sfd.axhline(0, color='#B0BEC5', linewidth=1.0)
        self.ax_sfd.set_title("Shear Force Diagram", fontsize=10, pad=5, y=-0.25)
        self.ax_sfd.get_xaxis().set_visible(False)

        # ── Deflection ────────────────────────────────────────────────────────
        self.ax_defl.plot(xs, defl, color='#4C72B0', linewidth=1.5)
        self.ax_defl.fill_between(xs, defl, 0, color='#4C72B0', alpha=0.25)
        self.ax_defl.axhline(0, color='#B0BEC5', linewidth=1.0)
        # Re-invert after clear (clear resets inversion)
        if not self.ax_defl.yaxis.get_inverted():
            self.ax_defl.invert_yaxis()
        self.ax_defl.set_title("Deflection", fontsize=10, pad=5, y=-0.4)
        self.ax_defl.get_xaxis().set_visible(False)

        self.canvas.draw()

    def _clear_axes(self):
        """Safely clear all axes and restore baseline formatting."""
        for ax in (self.ax_scheme, self.ax_bmd, self.ax_sfd, self.ax_defl):
            ax.clear()
            ax.set_facecolor('#ffffff')
            ax.grid(False)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_visible(False)
            ax.set_yticks([])
            ax.set_ylabel("")
            ax.axis('on')  # Reset in case they were hidden by empty state
        self.canvas.draw()

    def _show_blank_state(self):
        """Display an empty state message when analysis results are missing."""
        self._clear_axes()
        for ax in (self.ax_scheme, self.ax_bmd, self.ax_sfd, self.ax_defl):
            ax.axis('off')
        
        self.ax_sfd.text(0.5, 0.5, "Run analysis to generate structural results.",
                         ha='center', va='center', transform=self.ax_sfd.transAxes,
                         color='#666666', fontsize=11, style='italic')
        self.canvas.draw()

    # =========================================================================
    #   RHS FIELD UPDATES
    # =========================================================================

    def _update_rhs_fields(self, max_dict):
        """Sync maximum values into the left-panel result fields."""
        mapping = [
            ("M_max", "M_max", "{:.2f} kNm"),
            ("V_max", "V_max", "{:.2f} kN"),
            ("D_max", "D_max", "{:.4f} mm"),
        ]
        for key, field_key, fmt in mapping:
            if field_key in self.analysis_tab.result_fields:
                val = max_dict.get(key, 0.0)
                self.analysis_tab.result_fields[field_key].setText(fmt.format(abs(val)))

    # =========================================================================
    #   MODE SWITCHING AND CANVAS INTERACTION
    # =========================================================================

    def _on_interaction_mode_changed(self, index=None):
        """Handle changes to the interaction mode dropdown (Maximum Values vs Interactive)."""
        self._update_right_panel_for_mode()
        self._draw_cursors()

    def _update_right_panel_for_mode(self):
        """Update the value fields on the right panel based on the selected interaction mode."""
        if getattr(self, "_current_x", None) is None:
            return

        mode = self.interaction_combo.currentText()
        if mode == "Maximum Values":
            max_d = getattr(self, "_current_max_dict", {})
            mx = max_d.get("M_max", 0.0)
            vx = max_d.get("V_max", 0.0)
            dx = max_d.get("D_max", 0.0)
            
            if hasattr(self.analysis_tab, "x_input"):
                self.analysis_tab.x_input.setText("Multiple")
            if "M_x" in self.analysis_tab.x_fields:
                self.analysis_tab.x_fields["M_x"].setText(f"max = {mx:.2f} kNm at x = {max_d.get('x_M', 0.0):.2f} m")
            if "V_x" in self.analysis_tab.x_fields:
                self.analysis_tab.x_fields["V_x"].setText(f"max = {vx:.2f} kN at x = {max_d.get('x_V', 0.0):.2f} m")
            if "D_x" in self.analysis_tab.x_fields:
                self.analysis_tab.x_fields["D_x"].setText(f"max = {dx:.4f} mm at x = {max_d.get('x_D', 0.0):.2f} m")
        else:
            # Interactive mode
            idx = getattr(self, "_cursor_idx", 0)
            idx = max(0, min(len(self._current_x) - 1, idx))
            
            x_snap = float(self._current_x[idx])
            mx = float(self._current_bmd[idx])
            vx = float(self._current_sfd[idx])
            dx = float(self._current_defl[idx])

            if hasattr(self.analysis_tab, "x_input"):
                self.analysis_tab.x_input.setText(f"{x_snap:.2f} m")

            if "M_x" in self.analysis_tab.x_fields:
                self.analysis_tab.x_fields["M_x"].setText(f"{mx:.2f} kNm")
            if "V_x" in self.analysis_tab.x_fields:
                self.analysis_tab.x_fields["V_x"].setText(f"{vx:.2f} kN")
            if "D_x" in self.analysis_tab.x_fields:
                self.analysis_tab.x_fields["D_x"].setText(f"{dx:.4f} mm")

    def _on_canvas_click(self, event):
        """Snap cursor to nearest structural node and update value fields."""
        if self.interaction_combo.currentText() != "Interactive":
            return
            
        if event.xdata is None or getattr(self, "_current_x", None) is None:
            return

        x_val = event.xdata
        self._cursor_idx = int(np.argmin(np.abs(self._current_x - x_val)))
        
        self._update_right_panel_for_mode()
        self._draw_cursors()

    def _on_key_press(self, event):
        """Cycle through nodes using left/right arrows."""
        if self.interaction_combo.currentText() != "Interactive":
            return
        if getattr(self, "_current_x", None) is None:
            return
            
        idx = getattr(self, "_cursor_idx", 0)
        if event.key == "left":
            self._cursor_idx = max(0, idx - 1)
        elif event.key == "right":
            self._cursor_idx = min(len(self._current_x) - 1, idx + 1)
        else:
            return
            
        self._update_right_panel_for_mode()
        self._draw_cursors()

    def _draw_cursors(self):
        """Render the vertical crosshair line across the diagrams if in Interactive mode."""
        for line in getattr(self, "_cursor_lines", []):
            try:
                line.remove()
            except Exception:
                pass
        self._cursor_lines = []
        
        if self.interaction_combo.currentText() == "Interactive" and hasattr(self, "_cursor_idx"):
            cx = self._current_x[self._cursor_idx]
            self._cursor_lines.append(self.ax_bmd.axvline(cx, color='#1f4e79', linestyle='--', linewidth=1.5))
            self._cursor_lines.append(self.ax_sfd.axvline(cx, color='#1f4e79', linestyle='--', linewidth=1.5))
            self._cursor_lines.append(self.ax_defl.axvline(cx, color='#1f4e79', linestyle='--', linewidth=1.5))
            
        self.canvas.draw()


    def _verify_analysis_results(self):
        """Debug verification for checking model paths and results extraction."""
        print("\n--- Steel Design Verification ---")
        
        if self._cached_model is None or self._cached_results is None:
            print("No cached model or results found. Analysis may have failed to run or complete.")
            print("---------------------------------\n")
            return
            
        print("DEBUG: Successfully found model and results cached in UI.")
        results_obj = self._cached_results
        
        if not hasattr(results_obj, 'forces'):
            print("Results object has no 'forces' attribute.")
            print("---------------------------------\n")
            return
            
        forces = results_obj.forces
        
        try:
            first_lc = forces.coords['Loadcase'].values[0]
            
            # Instead of blindly taking the first element from the forces array (which might be a support/transverse beam),
            # let's pick the first valid element from our own parsed girder map to guarantee a match.
            if not self._girder_map:
                print("No girders found in the girder map. Cannot verify.")
                print("---------------------------------\n")
                return
                
            first_girder_key = list(self._girder_map.keys())[0]
            first_ele = self._girder_map[first_girder_key]["elements"][0]
            idx = 0  # This is the 0th index in the UI girder array
            
            sample_mz = forces.sel(Loadcase=first_lc, Element=first_ele, Component="Mz_i").item()
            print(f"Raw Analyser Backend -> Element {first_ele}, Loadcase '{first_lc}', Mz_i = {sample_mz}")
            
            # Extract the same way UI does it
            xs, bmd, sfd, defl = self._extract_member_results(first_girder_key, first_lc)
            
            # bmd arrays are in kNm (divided by 1000)
            ui_bmd_val = bmd[idx] * 1000.0  # Convert back to Nm for direct comparison
            print(f"UI Extraction Backend  -> Girder {first_girder_key}, Index {idx}, Mz_i = {ui_bmd_val}")
            
            if abs(float(sample_mz) - float(ui_bmd_val)) < 1e-4:
                print("\nVerification: MATCH - UI successfully reads raw forces directly from the analyser!")
            else:
                print(f"\nVerification: MISMATCH (Analyser: {sample_mz} != UI: {ui_bmd_val})")
                
        except Exception as e:
            import traceback
            print(f"Verification Error: {e}")
            traceback.print_exc()

        print("---------------------------------\n")


# ─── Utility ──────────────────────────────────────────────────────────────────

def _match_length(arr: np.ndarray, target_len: int) -> np.ndarray:
    """Trim or zero-pad `arr` so it has exactly `target_len` elements."""
    n = len(arr)
    if n == target_len:
        return arr
    elif n > target_len:
        return arr[:target_len]
    else:
        return np.concatenate([arr, np.zeros(target_len - n, dtype=arr.dtype)])
