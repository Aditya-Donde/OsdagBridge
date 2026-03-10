from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QSizeGrip,
    QSizePolicy, QGroupBox, QRadioButton, QLabel
)
from PySide6.QtCore import Qt

from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.dialogs.tabs.steel_design_details import SteelDesignDetailsTab
from osdagbridge.desktop.ui.dialogs.tabs.steel_design_analysis import SteelDesignAnalysisTab
from osdagbridge.desktop.ui.dialogs.tabs.steel_design_check import SteelDesignCheckTab

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas


# =============================================================================
#   DIALOG: Steel Design
# =============================================================================

class SteelDesign(QDialog):
    """
    Main dialog window for the Steel Design module.

    Provides three tabs:
      - Details       : Girder geometry and section properties
      - Analysis Results : Interactive BMD / SFD / Deflection plots
      - Design Check  : Code compliance results

    The Analysis Results tab injects a matplotlib figure into the placeholder
    defined by SteelDesignAnalysisTab, wires all signals, and manages the
    full data pipeline from ospgrillage model discovery to plot rendering.
    """

    # =========================================================================
    #   UI INITIALISATION
    # =========================================================================

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
        """
        Configure a frameless window with a custom title bar and a resize grip.
        The content_widget acts as the root container for the tab layout.
        """
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
        """
        Build the top-level layout: tab widget containing the three main sections.
        Also triggers plot canvas injection and loads existing details data.
        """
        self.setupWrapper()

        main_layout = QVBoxLayout(self.content_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(2)

        # ── Tab widget ────────────────────────────────────────────────────────
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

        # Inject the matplotlib canvas into the Analysis Results tab
        self._setup_analysis_plots()

    def _setup_analysis_plots(self):
        """
        Build and inject the matplotlib figure canvas into the Analysis Results tab.

        Responsibilities:
          - Create a 4-panel figure (schematic + BMD + SFD + Deflection)
          - Replace the diagram_placeholder with the canvas widget
          - Replace QLineEdit side-fields with word-wrapping QLabels
          - Wire all Qt and matplotlib event signals
          - Initialise interaction state and data caches
        """
        # ── Figure + canvas ───────────────────────────────────────────────────
        self.figure = Figure(figsize=(6, 8))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: transparent;")
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ── Interaction mode radio buttons ────────────────────────────────────
        mode_group = QGroupBox("Display Location")
        mode_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #555555;
                border: 1px solid #cccccc;
                border-radius: 4px;
                margin-top: 6px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
                color: #777777;
                font-size: 10px;
            }
        """)
        mode_layout = QHBoxLayout(mode_group)
        mode_layout.setContentsMargins(10, 5, 10, 5)
        
        self.radio_max = QRadioButton("Maximum Values")
        self.radio_scroll = QRadioButton("Scroll for Values")
        
        # Default to Maximum Values
        self.radio_max.setChecked(True)
        
        # Connect signals
        self.radio_max.toggled.connect(self._on_interaction_mode_changed)
        self.radio_scroll.toggled.connect(self._on_interaction_mode_changed)
        
        mode_layout.addWidget(self.radio_max)
        mode_layout.addSpacing(15)
        mode_layout.addWidget(self.radio_scroll)
        mode_layout.addStretch()

        combo_layout = QHBoxLayout()
        combo_layout.addStretch()
        combo_layout.addWidget(mode_group)

        # Canvas wrapper: fixed height so it doesn't push surrounding layout
        canvas_wrapper = QWidget()
        canvas_wrapper.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        canvas_wrapper.setFixedHeight(580)
        vbox = QVBoxLayout(canvas_wrapper)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.addLayout(combo_layout)
        vbox.addWidget(self.canvas, 1)  # stretch=1 so canvas claims remaining height

        # ── Swap placeholder with canvas wrapper ──────────────────────────────
        placeholder    = self.analysis_tab.diagram_placeholder
        diagram_layout = placeholder.parentWidget().layout()
        diagram_layout.replaceWidget(placeholder, canvas_wrapper)
        placeholder.hide()

        # Give canvas_wrapper vertical priority; lock the right panel to fixed
        if diagram_layout is not None:
            for i in range(diagram_layout.count()):
                item = diagram_layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    if widget is canvas_wrapper:
                        diagram_layout.setStretchFactor(widget, 1)
                    else:
                        widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                        diagram_layout.setStretchFactor(widget, 0)

        # ── Four stacked subplots ─────────────────────────────────────────────
        gs = self.figure.add_gridspec(4, 1, height_ratios=[0.4, 1, 1, 1])
        self.ax_scheme = self.figure.add_subplot(gs[0])
        self.ax_bmd    = self.figure.add_subplot(gs[1])
        self.ax_sfd    = self.figure.add_subplot(gs[2])
        self.ax_defl   = self.figure.add_subplot(gs[3])
        self.figure.subplots_adjust(left=0.08, right=0.96, top=0.95, bottom=0.08, hspace=0.35)

        # Schematic: frameless
        self.ax_scheme.set_facecolor('#ffffff')
        self.ax_scheme.grid(False)
        for spine in self.ax_scheme.spines.values():
            spine.set_visible(False)
        self.ax_scheme.set_yticks([])
        self.ax_scheme.set_ylabel("")
        
        # Data axes: show all four spines as a visible frame
        for ax in (self.ax_bmd, self.ax_sfd, self.ax_defl):
            ax.set_facecolor('#ffffff')
            ax.grid(False)
            for spine in ax.spines.values():
                spine.set_visible(True)
                spine.set_linewidth(0.8)
                spine.set_color('#cccccc')
            ax.set_yticks([])
            ax.set_ylabel("")
            ax.axhline(0, color='black', linewidth=0, clip_on=True)

        self.ax_defl.invert_yaxis()

        # ── Replace QLineEdit side-fields with QLabels (supports HTML/two lines) ──
        # Spacer heights align each label with the vertical centre of its diagram band.
        # Tuned to the [0.4, 1, 1, 1] gridspec running inside a 580px canvas.
        _SPACER_HEIGHTS = [90, 100, 100]

        for key, field in list(self.analysis_tab.x_fields.items()):
            lbl = QLabel()
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setWordWrap(True)
            lbl.setMinimumWidth(120)
            lbl.setStyleSheet("""
                QLabel {
                    background-color: #f9f9f9;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    color: #555555;
                    padding: 2px 4px;
                }
            """)
            lbl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

            parent_widget = field.parentWidget()
            if parent_widget and parent_widget.layout():
                parent_layout = parent_widget.layout()
                spacer_idx = 0
                for i in range(parent_layout.count()):
                    item = parent_layout.itemAt(i)
                    if item and item.spacerItem() and spacer_idx < len(_SPACER_HEIGHTS):
                        item.spacerItem().changeSize(
                            0, _SPACER_HEIGHTS[spacer_idx], QSizePolicy.Fixed, QSizePolicy.Fixed
                        )
                        spacer_idx += 1
                    elif item and item.layout():
                        sub_layout = item.layout()
                        for j in range(sub_layout.count()):
                            if sub_layout.itemAt(j).widget() == field:
                                sub_layout.replaceWidget(field, lbl)
                                field.hide()
                                field.deleteLater()
                                self.analysis_tab.x_fields[key] = lbl
                                break

        # Apply uniform alignment/policy to all result and position fields
        all_rhs_fields = (
            list(self.analysis_tab.result_fields.values())
            + list(self.analysis_tab.x_fields.values())
            + [getattr(self.analysis_tab, "x_input", None)]
        )
        for field in all_rhs_fields:
            if field:
                field.setAlignment(Qt.AlignCenter)
                field.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        # ── Signal wiring ─────────────────────────────────────────────────────
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.analysis_tab.member_combo.currentIndexChanged.connect(self._update_analysis_plots)
        self.analysis_tab.load_combo.currentIndexChanged.connect(self._update_analysis_plots)
        if hasattr(self.analysis_tab, "component_combo"):
            self.analysis_tab.component_combo.currentIndexChanged.connect(self._update_analysis_plots)
        self.canvas.mpl_connect('button_press_event', self._on_canvas_click)
        self.canvas.mpl_connect('key_press_event', self._on_key_press)
        self.canvas.setFocusPolicy(Qt.StrongFocus)

        # ── Interactive cursor state ──────────────────────────────────────────
        self._current_x    = None
        self._current_bmd  = None
        self._current_sfd  = None
        self._current_defl = None
        self._cursor_lines = []
        self._cursor_x     = None   # exact x position (may be between nodes)

        # ── Analysis data caches ──────────────────────────────────────────────
        self._cached_model     = None
        self._cached_results   = None
        self._girder_map       = {}
        self._data_initialized = False

    # =========================================================================
    #   EVENT HANDLERS
    # =========================================================================

    def _on_tab_changed(self, index):
        """
        Entry point for the Analysis Results tab (index 1).
        Discovers the ospgrillage model on first visit, builds girder map,
        populates dropdowns, and triggers the initial plot render.
        """
        if index != 1:
            return

        # TEMPORARY: auto-run analysis for UI testing
        # This will be removed once the core–UI workflow is connected.
        if self._cached_model is None:
            try:
                import sys
                from unittest.mock import MagicMock
                mock_cad = MagicMock()
                mock_cad.export_step = lambda *args, **kwargs: None
                sys.modules["osdagbridge.core.bridge_types.plate_girder.cad_generator"] = mock_cad

                mock_designer = MagicMock()
                mock_designer.design = lambda *args, **kwargs: None
                sys.modules["osdagbridge.core.bridge_types.plate_girder.designer"] = mock_designer

                mock_report = MagicMock()
                mock_report.section_report = lambda *args, **kwargs: None
                sys.modules["osdagbridge.core.bridge_types.plate_girder.report_generator"] = mock_report

                from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import PlateGirderBridge
                if hasattr(self._main_window, 'cad_state') and self._main_window.cad_state:
                    bridge = PlateGirderBridge(
                        basic_inputs=self._main_window.cad_state,
                        additional_inputs=self._main_window.cad_state
                    )
                    # mock the model type selection so it works cleanly internally
                    self._main_window.cad_state['Model Selection'] = "M35"
                    bridge.run(run_analysis=True)
                    self._main_window.backend = bridge._analysis_engine
                    self._cached_model = bridge._analysis_engine.model
            except BaseException as e:
                import traceback
                print(f"Auto-run analysis failed:\n{traceback.format_exc()}")

        if self._cached_model is None:
            self._discover_and_cache_model()

        if self._cached_model is not None and self._cached_results is None:
            try:
                self._cached_results = self._cached_model.get_results()
            except Exception:
                pass

        if self._cached_results is not None and not self._girder_map:
            self._build_girder_map()

        if self._girder_map and not self._data_initialized:
            self._populate_member_combo()
            self._populate_load_combo()
            self._data_initialized = True

        self._update_analysis_plots()

    @property
    def _interaction_mode(self) -> str:
        """Return the active display mode based on radio button selection."""
        return "Maximum Values" if getattr(self, "radio_max", None) and self.radio_max.isChecked() else "Scroll for Values"

    def _on_interaction_mode_changed(self, checked=None):
        """
        Respond to radio button selection changes.
        Resets cursor to position 0 when switching to Scroll for Values mode,
        then refreshes the right-panel fields and redraws cursor lines.
        """
        if checked is False:
            return
        if self._interaction_mode == "Scroll for Values":
            self._cursor_idx = 0
            self._cursor_x   = None
        self._update_right_panel_for_mode()
        self._draw_cursors()

    def _on_canvas_click(self, event):
        """
        Handle mouse clicks on the matplotlib canvas.
        If in Scroll for Values mode, determines which structural node is closest
        to the click's x-coordinate and snaps the cursor to that node.
        """
        if self._interaction_mode != "Scroll for Values":
            return
        if event.xdata is None or self._current_x is None:
            return

        idx = (np.abs(self._current_x - event.xdata)).argmin()
        self._cursor_idx = int(idx)
        self._cursor_x = float(self._current_x[self._cursor_idx])
        
        self._update_right_panel_for_mode()
        self._draw_cursors()

    def _on_key_press(self, event):
        """
        Move the interactive cursor left or right through structural nodes
        using the arrow keys. Each step snaps to the next/previous node.
        Only active in Scroll for Values mode.
        """
        if self._interaction_mode != "Scroll for Values":
            return
        if self._current_x is None:
            return

        idx = getattr(self, "_cursor_idx", 0)
        if event.key == "left":
            self._cursor_idx = max(0, idx - 1)
        elif event.key == "right":
            self._cursor_idx = min(len(self._current_x) - 1, idx + 1)
        else:
            return

        # Arrow keys snap exactly to node positions
        self._cursor_x = float(self._current_x[self._cursor_idx])
        self._update_right_panel_for_mode()
        self._draw_cursors()

    # =========================================================================
    #   DATA PIPELINE
    # =========================================================================

    def _discover_and_cache_model(self):
        """
        Locate the ospgrillage model from the application's *already-completed*
        analysis engine. Walks cad_state and backend for any PlateGirderBridge
        or BridgeGrillageModel whose _analysis_engine is populated.

        Does NOT re-run analysis. If no engine is found, leaves
        _cached_model as None so the blank-state message is shown.
        """
        mw = self._main_window

        # ── 1. Walk cad_state values ──────────────────────────────────────────
        if hasattr(mw, 'cad_state') and mw.cad_state:
            for val in mw.cad_state.values():
                # PlateGirderBridge stores completed engine at ._analysis_engine
                engine = getattr(val, '_analysis_engine', None)
                if engine is not None:
                    model = getattr(engine, 'model', None)
                    if model is not None:
                        self._cached_model = model
                        return

                # BridgeGrillageModel stored directly in cad_state
                model = getattr(val, 'model', None)
                if model is not None and hasattr(model, 'get_results'):
                    self._cached_model = model
                    return

        # ── 2. Try backend's run result or direct attribute ───────────────────
        if hasattr(mw, 'backend') and mw.backend:
            try:
                # Some backend implementations expose the last run result
                result = getattr(mw.backend, 'last_run_result', None)
                if result is None and hasattr(mw.backend, 'get_run_result'):
                    result = mw.backend.get_run_result()

                for source in (result, mw.backend):
                    if source is None:
                        continue
                    engine = getattr(source, '_analysis_engine', None)
                    if engine is not None:
                        model = getattr(engine, 'model', None)
                        if model is not None:
                            self._cached_model = model
                            return
            except Exception:
                pass

        # No completed engine found — _cached_model stays None.

    def _build_girder_map(self):
        """
        Populate self._girder_map by discovering all longitudinal girder lines
        from the ospgrillage mesh topology.

        The mesh stores longitudinal elements in Mesh_obj.z_group_to_ele, grouped
        by z_group (one z_group = one girder line). Elements in each group are
        sorted longitudinally by x-coordinate to form an ordered element list and
        node path.

        Resulting structure:
            self._girder_map = {
                "g1": {"elements": [ele_tag, ...], "path": [node_tag, ...]},
                "g2": {...},
                ...
            }
        """
        self._girder_map = {}
        mesh      = self._cached_model.Mesh_obj
        node_spec = mesh.node_spec  # {tag: {"coordinate": [x, y, z], ...}}

        try:
            z_group_to_ele = mesh.z_group_to_ele
        except AttributeError:
            return

        def _z_coord_of_group(z_group):
            """Return z-coordinate of first node in group for left→right sorting."""
            elems = z_group_to_ele.get(z_group, [])
            if not elems:
                return 0.0
            ni = elems[0][1]
            try:
                return float(node_spec[ni]["coordinate"][2])
            except (KeyError, IndexError):
                return 0.0

        sorted_z_groups = sorted(z_group_to_ele.keys(), key=_z_coord_of_group)

        for girder_idx, z_group in enumerate(sorted_z_groups):
            raw_elems = z_group_to_ele[z_group]
            if not raw_elems:
                continue

            def _x_of_elem(elem):
                """Return x-coordinate of element's i-node for longitudinal ordering."""
                ni = elem[1]
                try:
                    return float(node_spec[ni]["coordinate"][0])
                except (KeyError, IndexError):
                    return 0.0

            sorted_elems = sorted(raw_elems, key=_x_of_elem)
            element_ids  = [int(e[0]) for e in sorted_elems]
            node_path    = [int(e[1]) for e in sorted_elems]
            node_path.append(int(sorted_elems[-1][2]))  # append j-node of last element

            girder_key = f"g{girder_idx + 1}"
            self._girder_map[girder_key] = {
                "elements": element_ids,
                "path":     node_path,
            }

    def _extract_member_results(self, member_key, loadcase):
        """
        Extract x-coordinate, BMD, SFD, and deflection arrays for a given
        girder and load case directly from the cached ospgrillage results xarray.

        Args:
            member_key (str): Girder identifier key, e.g. "g1".
            loadcase   (str): Load case label as stored in results.forces.

        Returns:
            tuple (xs, bmd, sfd, defl) of numpy arrays, or None on failure.
            Units: xs [m], bmd [kNm], sfd [kN], defl [mm].
        """
        if member_key not in self._girder_map:
            return None

        girder     = self._girder_map[member_key]
        element_ids = girder["elements"]
        node_path   = girder["path"]

        try:
            node_spec = self._cached_model.Mesh_obj.node_spec

            # Build x-coordinate array from node positions, zeroed at first node
            x_raw = []
            for node_tag in node_path:
                try:
                    x_raw.append(float(node_spec[node_tag]["coordinate"][0]))
                except (KeyError, IndexError, TypeError):
                    x_raw.append(0.0)

            if not x_raw:
                return None

            x_offset = min(x_raw)
            xs = np.array([x - x_offset for x in x_raw], dtype=float)

            # Extract force components from the results xarray
            forces = self._cached_results.forces

            def _get_force_array(component):
                """Extract one per-element force component for the given loadcase."""
                values = []
                try:
                    selected = forces.sel(Loadcase=loadcase, Component=component)
                    for eid in element_ids:
                        try:
                            v = float(selected.sel(Element=eid).values.item())
                        except Exception:
                            v = 0.0
                        values.append(v)
                except Exception:
                    values = [0.0] * len(element_ids)
                values.append(0.0)  # pad to match node_path length (n_elements + 1)
                return values

            bmd_values = np.nan_to_num(
                _match_length(np.array(_get_force_array("Mz_i"), dtype=float) / 1000.0, len(xs))
            )  # N·m → kNm
            sfd_values = np.nan_to_num(
                _match_length(np.array(_get_force_array("Vy_i"), dtype=float) / 1000.0, len(xs))
            )  # N → kN

            # Extract vertical displacements per node
            disp     = self._cached_results.displacements
            defl_raw = []
            try:
                disp_dy = disp.sel(Loadcase=loadcase, Component="dy")
                for node_tag in node_path:
                    try:
                        v = float(disp_dy.sel(Node=node_tag).values.item()) * 1000.0  # m → mm
                        defl_raw.append(v)
                    except Exception:
                        defl_raw.append(np.nan)
            except Exception:
                defl_raw = [np.nan] * len(node_path)

            defl_values = np.nan_to_num(
                _match_length(np.array(defl_raw, dtype=float), len(xs))
            )

            return xs, bmd_values, sfd_values, defl_values

        except Exception:
            return None

    # =========================================================================
    #   DROPDOWN POPULATION HELPERS
    # =========================================================================

    def _populate_member_combo(self):
        """Populate the member dropdown with 'Girder 1', 'Girder 2', … entries."""
        combo = self.analysis_tab.member_combo
        combo.blockSignals(True)
        combo.clear()
        for idx, key in enumerate(self._girder_map):
            combo.addItem(f"Girder {idx + 1}", userData=key)
        combo.blockSignals(False)

    def _populate_load_combo(self):
        """
        Populate the load combination dropdown from the actual load cases
        present in the cached results. Ensures 'girder self weight' appears first.
        """
        combo = self.analysis_tab.load_combo
        try:
            loadcases = list(self._cached_results.forces.coords["Loadcase"].values)
            preferred = "girder self weight"
            if preferred in loadcases:
                loadcases.remove(preferred)
                loadcases = [preferred] + loadcases
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(loadcases)
            combo.blockSignals(False)
        except Exception:
            pass

    # =========================================================================
    #   PLOT RENDERING
    # =========================================================================

    def _update_analysis_plots(self, *_args):
        """
        Master orchestrator called when the girder or load combination selection
        changes. Extracts data arrays, computes maximums, renders all plots,
        and refreshes the right-hand result panel.
        """
        if self._cached_results is None or not self._girder_map:
            self._show_blank_state()
            return

        combo      = self.analysis_tab.member_combo
        member_key = combo.currentData() or combo.currentText()
        loadcase   = self.analysis_tab.load_combo.currentText()

        if not member_key or member_key not in self._girder_map:
            return

        result = self._extract_member_results(member_key, loadcase)
        if result is None:
            self._show_blank_state()
            return

        xs, bmd_values, sfd_values, defl_values = result
        self._current_x    = xs
        self._current_bmd  = bmd_values
        self._current_sfd  = sfd_values
        self._current_defl = defl_values

        self._current_max_dict = self._compute_maximums(xs, bmd_values, sfd_values, defl_values)

        self._clear_axes()
        self._render_plots(xs, bmd_values, sfd_values, defl_values)
        self._update_value_fields(self._current_max_dict)
        self._on_interaction_mode_changed()

    def _render_plots(self, xs, bmd_values, sfd_values, defl_values):
        """
        Draw the girder schematic and BMD / SFD / Deflection diagrams onto
        the four matplotlib axes. Does not recompute any structural values.
        """
        # ── Girder schematic ─────────────────────────────────────────────────
        self.ax_scheme.plot([xs[0], xs[-1]], [0, 0], color='#90A4AE', linewidth=3)
        self.ax_scheme.annotate("", xy=(xs[0], 0), xytext=(xs[0], -0.2),
                                arrowprops=dict(arrowstyle="->", color='#90A4AE', lw=2))
        self.ax_scheme.annotate("", xy=(xs[-1], 0), xytext=(xs[-1], -0.2),
                                arrowprops=dict(arrowstyle="->", color='#90A4AE', lw=2))
        self.ax_scheme.set_ylim(-0.25, 0.1)
        self.ax_scheme.axis('off')

        # Vertical node grid lines (clipped for data axes)
        for ax in (self.ax_bmd, self.ax_sfd, self.ax_defl):
            for x in xs[1:-1]:  # Skip the very first and very last nodes to avoid spine overlap
                ax.axvline(x, linestyle=":", linewidth=0.5, color="#bfbfbf", clip_on=True)
            ax.set_xlim(xs[0], xs[-1])  # Constrain data axes perfectly to the girder span
            
        # Schematic node grid lines (unclipped as schematic has no frame)
        for x in xs:
            self.ax_scheme.axvline(x, linestyle=":", linewidth=0.5, color="#bfbfbf")
        self.ax_scheme.set_xlim(xs[0], xs[-1])

        # ── Bending Moment Diagram ────────────────────────────────────────────
        self.ax_bmd.plot(xs, bmd_values, color='#4C72B0', linewidth=1.5)
        self.ax_bmd.fill_between(xs, bmd_values, 0, color='#4C72B0', alpha=0.25)
        self.ax_bmd.axhline(0, color='#B0BEC5', linewidth=1.0, clip_on=True)
        self.ax_bmd.set_title("Bending Moment Diagram", fontsize=10, pad=5, y=-0.25)
        self.ax_bmd.get_xaxis().set_visible(False)

        # ── Shear Force Diagram ───────────────────────────────────────────────
        self.ax_sfd.plot(xs, sfd_values, color='#4C72B0', linewidth=1.5)
        self.ax_sfd.fill_between(xs, sfd_values, 0, color='#4C72B0', alpha=0.25)
        self.ax_sfd.axhline(0, color='#B0BEC5', linewidth=1.0, clip_on=True)
        self.ax_sfd.set_title("Shear Force Diagram", fontsize=10, pad=5, y=-0.25)
        self.ax_sfd.get_xaxis().set_visible(False)

        # ── Deflection Diagram ────────────────────────────────────────────────
        self.ax_defl.plot(xs, defl_values, color='#4C72B0', linewidth=1.5)
        self.ax_defl.fill_between(xs, defl_values, 0, color='#4C72B0', alpha=0.25)
        self.ax_defl.axhline(0, color='#B0BEC5', linewidth=1.0, clip_on=True)
        if not self.ax_defl.yaxis.get_inverted():
            self.ax_defl.invert_yaxis()  # y-axis reset after clear; re-invert
        self.ax_defl.set_title("Deflection", fontsize=10, pad=5, y=-0.4)
        self.ax_defl.get_xaxis().set_visible(False)

        self.canvas.draw()

    def _clear_axes(self):
        """Clear all axes and restore baseline formatting before re-render."""
        for ax in (self.ax_scheme, self.ax_bmd, self.ax_sfd, self.ax_defl):
            ax.clear()
            ax.set_facecolor('#ffffff')
            ax.grid(False)
            ax.set_yticks([])
            ax.set_ylabel("")
            ax.axis('on')
            
        # Schematic: frameless
        for spine in self.ax_scheme.spines.values():
            spine.set_visible(False)
            
        # Data axes: show all four spines as a visible frame
        for ax in (self.ax_bmd, self.ax_sfd, self.ax_defl):
            for spine in ax.spines.values():
                spine.set_visible(True)
                spine.set_linewidth(0.8)
                spine.set_color('#cccccc')
                
        self.canvas.draw()

    def _show_blank_state(self):
        """
        Show a placeholder message when no analysis results are available.
        Directs the user to run the analysis before viewing the tab.
        """
        self._clear_axes()
        for ax in (self.ax_scheme, self.ax_bmd, self.ax_sfd, self.ax_defl):
            ax.axis('off')
        self.ax_sfd.text(
            0.5, 0.5,
            "Run the analysis first to see results.",
            ha='center', va='center', transform=self.ax_sfd.transAxes,
            color='#666666', fontsize=11, style='italic',
        )
        self.canvas.draw()

    # =========================================================================
    #   CALCULATION UTILITIES
    # =========================================================================

    def _compute_maximums(self, xs, bmd_values, sfd_values, defl_values):
        """
        Find the peak absolute values for BMD, SFD, and Deflection and the
        corresponding x-positions along the girder.

        Returns:
            dict with keys M_max, V_max, D_max (signed values) and
            x_M, x_V, x_D (positions in metres).
        """
        idx_m = int(np.argmax(np.abs(bmd_values)))
        idx_v = int(np.argmax(np.abs(sfd_values)))
        idx_d = int(np.argmax(np.abs(defl_values)))
        return {
            "M_max": bmd_values[idx_m],
            "V_max": sfd_values[idx_v],
            "D_max": defl_values[idx_d],
            "x_M":  float(xs[idx_m]),
            "x_V":  float(xs[idx_v]),
            "x_D":  float(xs[idx_d]),
        }

    # =========================================================================
    #   UI UPDATE HELPERS
    # =========================================================================

    def _update_value_fields(self, max_dict):
        """
        Populate the left-panel summary result fields with the computed maximum
        values for bending moment, shear force, and deflection.
        """
        mapping = [
            ("T_x", "T_x", "{:.2f} kNm"),
            ("M_y", "M_y", "{:.2f} kNm"),
            ("M_max", "M_z", "{:.2f} kNm"),
            ("V_x", "V_x", "{:.2f} kN"),
            ("V_max", "V_y", "{:.2f} kN"),
            ("V_z", "V_z", "{:.2f} kN"),
            ("D_x", "D_x", "{:.4f} mm"),
            ("D_max", "D_y", "{:.4f} mm"),
            ("D_z", "D_z", "{:.4f} mm"),
        ]
        for dict_key, field_key, fmt in mapping:
            if field_key in self.analysis_tab.result_fields:
                val = max_dict.get(dict_key, 0.0)
                self.analysis_tab.result_fields[field_key].setText(fmt.format(val))

    def _update_right_panel_for_mode(self):
        """
        Refresh the right-column position/value labels based on the active mode.

        Maximum Values mode : shows each diagram's peak value and x-position
                              on two lines; expands label height to 42 px.
        Interactive mode    : shows the value at the current cursor index
                              on a single line; compresses label height to 28 px.
        """
        if self._current_x is None:
            return

        mode = self._interaction_mode

        if mode == "Maximum Values":
            max_d = getattr(self, "_current_max_dict", {})
            m_val = max_d.get("M_max", 0.0)
            v_val = max_d.get("V_max", 0.0)
            d_val = max_d.get("D_max", 0.0)

            if hasattr(self.analysis_tab, "x_input"):
                self.analysis_tab.x_input.setText("Multiple")

            if "M_z" in self.analysis_tab.x_fields:
                self.analysis_tab.x_fields["M_z"].setMinimumHeight(55)
                self.analysis_tab.x_fields["M_z"].setText(
                    f"{m_val:.2f} kNm<br>at x = {max_d.get('x_M', 0.0):.2f} m"
                )
            if "V_y" in self.analysis_tab.x_fields:
                self.analysis_tab.x_fields["V_y"].setMinimumHeight(55)
                self.analysis_tab.x_fields["V_y"].setText(
                    f"{v_val:.2f} kN<br>at x = {max_d.get('x_V', 0.0):.2f} m"
                )
            if "D_y" in self.analysis_tab.x_fields:
                self.analysis_tab.x_fields["D_y"].setMinimumHeight(55)
                self.analysis_tab.x_fields["D_y"].setText(
                    f"{d_val:.4f} mm<br>at x = {max_d.get('x_D', 0.0):.2f} m"
                )

        else:  # Interactive mode
            # Use the exact cursor x-position (set by click or arrow key).
            # Fall back to node 0 if not yet set.
            cx = getattr(self, "_cursor_x", None)
            if cx is None:
                self._cursor_idx = getattr(self, "_cursor_idx", 0)
                self._cursor_idx = max(0, min(len(self._current_x) - 1, self._cursor_idx))
                cx = float(self._current_x[self._cursor_idx])
                self._cursor_x = cx

            # Linearly interpolate each diagram at the exact cursor x
            m_val = float(np.interp(cx, self._current_x, self._current_bmd))
            v_val = float(np.interp(cx, self._current_x, self._current_sfd))
            d_val = float(np.interp(cx, self._current_x, self._current_defl))

            if hasattr(self.analysis_tab, "x_input"):
                self.analysis_tab.x_input.setText(f"{cx:.2f} m")

            if "M_z" in self.analysis_tab.x_fields:
                self.analysis_tab.x_fields["M_z"].setMinimumHeight(35)
                self.analysis_tab.x_fields["M_z"].setText(f"{m_val:.2f} kNm")
            if "V_y" in self.analysis_tab.x_fields:
                self.analysis_tab.x_fields["V_y"].setMinimumHeight(35)
                self.analysis_tab.x_fields["V_y"].setText(f"{v_val:.2f} kN")
            if "D_y" in self.analysis_tab.x_fields:
                self.analysis_tab.x_fields["D_y"].setMinimumHeight(35)
                self.analysis_tab.x_fields["D_y"].setText(f"{d_val:.4f} mm")

    def _draw_cursors(self):
        """
        Draw vertical dashed cursor lines on the BMD, SFD, and Deflection axes.

        Maximum Values mode: Draws a line at the peak absolute value location for each respective diagram.
        Scroll for Values mode: Draws a shared vertical line across all three diagrams at the current scroll position.
        """
        for line in self._cursor_lines:
            try:
                line.remove()
            except Exception:
                pass
        self._cursor_lines = []

        if self._current_x is None or len(self._current_x) == 0:
            self.canvas.draw()
            return

        mode = self._interaction_mode

        if mode == "Scroll for Values":
            # Draw cursor at the exact x-position (may be between nodes)
            cx = getattr(self, "_cursor_x", None)
            if cx is None:
                idx = getattr(self, "_cursor_idx", 0)
                idx = max(0, min(len(self._current_x) - 1, idx))
                cx = float(self._current_x[idx])
            for ax in (self.ax_bmd, self.ax_sfd, self.ax_defl):
                self._cursor_lines.append(
                    ax.axvline(cx, color='#1f4e79', linestyle='--', linewidth=1.5, clip_on=True)
                )

        elif mode == "Maximum Values" and hasattr(self, "_current_max_dict"):
            max_d = self._current_max_dict
            self._cursor_lines.append(
                self.ax_bmd.axvline(max_d.get("x_M", 0.0), color='#1f4e79', linestyle='--', linewidth=1.5, clip_on=True)
            )
            self._cursor_lines.append(
                self.ax_sfd.axvline(max_d.get("x_V", 0.0), color='#1f4e79', linestyle='--', linewidth=1.5, clip_on=True)
            )
            self._cursor_lines.append(
                self.ax_defl.axvline(max_d.get("x_D", 0.0), color='#1f4e79', linestyle='--', linewidth=1.5, clip_on=True)
            )

        self.canvas.draw()


# =============================================================================
#   MODULE-LEVEL UTILITY
# =============================================================================

def _match_length(arr: np.ndarray, target_len: int) -> np.ndarray:
    """
    Trim or zero-pad *arr* to exactly *target_len* elements.

    Used to reconcile the force array length (n_elements) with the node path
    length (n_elements + 1) after boundary padding.
    """
    n = len(arr)
    if n == target_len:
        return arr
    if n > target_len:
        return arr[:target_len]
    return np.concatenate([arr, np.zeros(target_len - n, dtype=arr.dtype)])
