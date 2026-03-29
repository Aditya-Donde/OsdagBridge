from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QTabBar, QWidget, QSizeGrip,
    QSizePolicy, QRadioButton, QLabel, QFrame
)
from PySide6.QtCore import Qt

from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.dialogs.tabs.steel_design_details import SteelDesignDetailsTab
from osdagbridge.desktop.ui.dialogs.tabs.steel_design_analysis import SteelDesignAnalysisTab
from osdagbridge.desktop.ui.dialogs.tabs.steel_design_check import SteelDesignCheckTab

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from osdagbridge.core.bridge_types.plate_girder.graph_engine import GirderGraphEngine


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

        self.title_bar = CustomTitleBar()
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
        main_layout.setContentsMargins(5, 5, 5, 5)

        # ── Tab widget ────────────────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.stretching_tab_bar = QTabBar()
        self.stretching_tab_bar.setElideMode(Qt.ElideRight)
        self.tabs.setTabBar(self.stretching_tab_bar)
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #d1d1d1;
                background-color: #ffffff;
                border-radius: 6px;
            }
            QTabBar::tab {
                font-weight: bold;
                font-size: 12px;
                background: #ffffff;
                color: #3a3a3a;
                border: 1px solid #d1d1d1;
                padding: 10px 22px;
            }
            QTabBar::tab:selected {
                background: #90AF13;
                color: #ffffff;
                border: 1px solid #90AF13;
            }
            QTabBar::tab:hover {
                background: #90AF13;
                color: #ffffff;
            }
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
        # ── Figure + canvas ─────────────────────────�
        self.figure = Figure(figsize=(8, 6), dpi=100, facecolor='#ffffff')
        self.canvas = FigureCanvas(self.figure)

        # ── Interaction mode: label + styled radio container ─────────────────
        # radio_container visually matches the Component combo box:
        # same border, radius, background, min-height, padding, font-size.
        # ── Display Location titled card ──────────────────────────────────────
        disp_card = QFrame()
        disp_card.setObjectName("controlCard")
        disp_card.setStyleSheet("""
            QFrame#controlCard {
                background-color : white;
                border           : 1px solid #b0b0b0;
                border-radius    : 6px;
            }
            QLabel {
                border      : none;
                background  : transparent;
            }
            QRadioButton {
                border      : none;
                background  : transparent;
                font-size   : 11px;
                color       : #333333;
            }
            QRadioButton:focus {
                outline: none;
            }
            QRadioButton::indicator {
                width: 12px;
                height: 12px;
                border: 1px solid #b0b0b0;
                border-radius: 6px;
                background: white;
            }
            QRadioButton::indicator:checked {
                background: #90AF13;
                border: 1px solid #90AF13;
            }
        """)
        disp_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        disp_card_layout = QVBoxLayout(disp_card)
        disp_card_layout.setContentsMargins(23, 10, 14, 12)
        disp_card_layout.setSpacing(4)

        disp_title = QLabel("Display Location")
        disp_title.setStyleSheet(
            "font-size: 13px; color: #2B2B2B; font-weight: bold;"
            " background: transparent; border: none;"
        )
        disp_card_layout.addWidget(disp_title)

        radio_row_widget = QWidget()
        radio_row_widget.setStyleSheet(
            "background: transparent; border: none;"
        )
        radio_row_widget.setFixedHeight(28)   # matches combo min-height so both cards are identical height
        radio_row_layout = QHBoxLayout(radio_row_widget)
        radio_row_layout.setContentsMargins(0, 0, 0, 0)
        radio_row_layout.setSpacing(16)

        self.radio_max    = QRadioButton("Maximum Values")
        self.radio_scroll = QRadioButton("Scroll for Values")
        self.radio_max.setChecked(True)
        self.radio_max.toggled.connect(self._on_interaction_mode_changed)
        self.radio_scroll.toggled.connect(self._on_interaction_mode_changed)

        radio_row_layout.addWidget(self.radio_max)
        radio_row_layout.addWidget(self.radio_scroll)
        radio_row_layout.addStretch()

        disp_card_layout.addWidget(radio_row_widget)

        # Add to controls_row with stretch=1 so it equals the Component card width
        self.analysis_tab.controls_row.addWidget(disp_card, 1)

        # Canvas wrapper: expands to fill available space — canvas only, no extra row
        canvas_wrapper = QWidget()
        canvas_wrapper.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        vbox = QVBoxLayout(canvas_wrapper)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        vbox.addWidget(self.canvas, 1)  # stretch=1 so canvas claims all height

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
        gs = self.figure.add_gridspec(4, 1, height_ratios=[0.45, 1, 1, 1], hspace=0.32)
        self.ax_scheme = self.figure.add_subplot(gs[0])
        self.ax_bmd    = self.figure.add_subplot(gs[1])
        self.ax_sfd    = self.figure.add_subplot(gs[2])
        self.ax_defl   = self.figure.add_subplot(gs[3])
        self.figure.subplots_adjust(left=0.08, right=0.96, top=0.94, bottom=0.12)

        # ── Graph engine: owns all render/draw logic ──────────────────────────
        self.graph_engine = GirderGraphEngine(
            self.figure, self.ax_scheme, self.ax_bmd, self.ax_sfd, self.ax_defl
        )

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

        # ── Side-fields: swap QLineEdit → QLabel for multi-line HTML display ──
        # Spacers are now baked as fixed addSpacing() in steel_design_analysis.py —
        # this loop only performs the widget swap; no spacer manipulation needed.
        _VALUE_LABEL_STYLE = """
            QLabel {
                background-color: #f4f4f4;
                border: 1px solid black;
                border-radius: 5px;
                color: #000000;
                font-size: 11px;
                padding: 1px 7px;
            }
        """

        for key, field in list(self.analysis_tab.x_fields.items()):
            lbl = QLabel()
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setWordWrap(True)
            lbl.setMinimumWidth(110)
            lbl.setStyleSheet(_VALUE_LABEL_STYLE)
            lbl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

            parent_widget = field.parentWidget()
            if parent_widget and parent_widget.layout():
                parent_layout = parent_widget.layout()
                for i in range(parent_layout.count()):
                    item = parent_layout.itemAt(i)
                    if item and item.layout():
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
            self.analysis_tab.component_combo.currentIndexChanged.connect(
                self.analysis_tab.update_rhs_labels
            )
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

        # ── UI initialisation state ───────────────────────────────────────────
        self._data_initialized = False

    # =========================================================================
    #   EVENT HANDLERS
    # =========================================================================

    def _on_tab_changed(self, index):
        """
        Entry point for the Analysis Results tab (index 1).
        Delegates all data discovery and extraction to the graph engine.
        Populates dropdowns on first visit, then triggers a plot render.
        """
        if index != 1:
            return

        engine = self.graph_engine

        if engine._cached_model is None:
            engine.discover_model(self._main_window)

        if engine._cached_model is not None and engine._cached_results is None:
            engine.fetch_results()

        if engine._cached_results is not None and not engine._girder_map:
            engine.build_girder_map()

        if engine._girder_map and not self._data_initialized:
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
        self.graph_engine.draw_cursors(
            self._interaction_mode,
            getattr(self, '_cursor_x', None),
            self._current_x,
            getattr(self, '_current_max_dict', {}),
            self.canvas,
        )

    def _on_canvas_click(self, event):
        """
        Handle mouse clicks on the matplotlib canvas.
        In Scroll for Values mode, moves the cursor to the exact click x-position
        (clamped to the girder span) and interpolates BMD / SFD / Deflection values.
        Works for any x, not just mesh node positions.
        """
        if self._interaction_mode != "Scroll for Values":
            return
        if event.xdata is None or self._current_x is None:
            return

        # Accept any x within the span; values are interpolated in _update_right_panel_for_mode
        self._cursor_x = float(np.clip(event.xdata, self._current_x[0], self._current_x[-1]))
        # Track nearest node index for arrow-key navigation continuity
        idx = int(np.searchsorted(self._current_x, self._cursor_x, side='right')) - 1
        self._cursor_idx = max(0, min(len(self._current_x) - 1, idx))

        self._update_right_panel_for_mode()
        self.graph_engine.draw_cursors(
            self._interaction_mode,
            getattr(self, '_cursor_x', None),
            self._current_x,
            getattr(self, '_current_max_dict', {}),
            self.canvas,
        )

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
        self.graph_engine.draw_cursors(
            self._interaction_mode,
            getattr(self, '_cursor_x', None),
            self._current_x,
            getattr(self, '_current_max_dict', {}),
            self.canvas,
        )



    # =========================================================================
    #   DROPDOWN POPULATION HELPERS
    # =========================================================================

    def _populate_member_combo(self):
        """Populate the member dropdown with 'Girder 1', 'Girder 2', … entries."""
        combo = self.analysis_tab.member_combo
        combo.blockSignals(True)
        combo.clear()
        for idx, key in enumerate(self.graph_engine.get_girder_keys()):
            combo.addItem(f"Girder {idx + 1}", userData=key)
        combo.blockSignals(False)

    def _populate_load_combo(self):
        """
        Populate the load combination dropdown from the actual load cases
        present in the cached results. Ensures 'girder self weight' appears first.
        """
        combo     = self.analysis_tab.load_combo
        loadcases = self.graph_engine.get_available_loadcases()
        preferred = "girder self weight"
        if preferred in loadcases:
            loadcases.remove(preferred)
            loadcases = [preferred] + loadcases
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(loadcases)
        combo.blockSignals(False)

    # =========================================================================
    #   PLOT RENDERING
    # =========================================================================

    def _update_analysis_plots(self, *_args):
        """
        Master orchestrator called when the girder, load combination, or component
        selection changes. Delegates data extraction and peak computation to the
        graph engine, then renders all plots and refreshes the right-hand panel.
        """
        engine = self.graph_engine

        if engine._cached_results is None or not engine._girder_map:
            engine.show_blank_state(self.canvas)
            return

        combo      = self.analysis_tab.member_combo
        member_key = combo.currentData() or combo.currentText()
        loadcase   = self.analysis_tab.load_combo.currentText()

        if not member_key or member_key not in engine._girder_map:
            return

        # ── Determine active component ────────────────────────────────────────
        comp_idx = 0
        if hasattr(self.analysis_tab, "component_combo"):
            comp_idx = self.analysis_tab.component_combo.currentIndex()

        # Maps: (bmd_force_key, sfd_force_key, defl_disp_key, rhs_labels, max_field_keys)
        # rhs_labels use HTML subscripts for the side-row label text
        _COMPONENT_CFG = [
            # Major
            ("Mz_i", "Vy_i", "dy",
             ("M<sub>z</sub> (kNm)", "V<sub>y</sub> (kN)", "D<sub>y</sub> (mm)"),
             ("M_z",                  "V_y",                 "D_y")),
            # Minor
            ("My_i", "Vz_i", "dz",
             ("M<sub>y</sub> (kNm)", "V<sub>z</sub> (kN)", "D<sub>z</sub> (mm)"),
             ("M_y",                  "V_z",                 "D_z")),
            # Axial
            ("Mx_i", "Fx_i", "dx",
             ("M<sub>x</sub> (kNm)", "F<sub>x</sub> (kN)", "D<sub>x</sub> (mm)"),
             ("M_x",                  "F_x",                 "D_x")),
        ]
        bmd_key, sfd_key, defl_key, rhs_labels, max_keys = _COMPONENT_CFG[min(comp_idx, 2)]

        result = engine.extract_member_results(member_key, loadcase, bmd_key, sfd_key, defl_key)
        if result is None:
            engine.show_blank_state(self.canvas)
            return

        xs, bmd_values, sfd_values, defl_values, all_data = result
        self._current_x    = xs
        self._current_bmd  = bmd_values
        self._current_sfd  = sfd_values
        self._current_defl = defl_values

        self._current_max_dict = engine.compute_maximums(
            xs, bmd_values, sfd_values, defl_values, all_data
        )

        # ── Update RHS field labels to match the active component ─────────────
        # Rebuild x_fields mapping so that _update_right_panel_for_mode uses
        # the correct keys regardless of which component is selected.
        fields   = list(self.analysis_tab.x_fields.values())
        new_keys = list(max_keys)   # e.g. ["M_z", "V_y", "D_y"]
        self.analysis_tab.x_fields = dict(zip(new_keys, fields))

        # Update the side-row label widgets text
        lbl_texts = list(rhs_labels)
        for field, lbl_text in zip(fields, lbl_texts):
            parent_widget = field.parentWidget()
            if parent_widget and parent_widget.layout():
                sub = parent_widget.layout()
                for j in range(sub.count()):
                    w = sub.itemAt(j).widget() if sub.itemAt(j) else None
                    if isinstance(w, QLabel) and w is not field:
                        w.setText(lbl_text)
                        break

        self._current_max_keys = max_keys

        engine.clear_axes(self.canvas)
        engine.render_plots(xs, bmd_values, sfd_values, defl_values, self.canvas)
        self._update_value_fields(self._current_max_dict, max_keys)
        self._on_interaction_mode_changed()

    # =========================================================================
    #   UI UPDATE HELPERS
    # =========================================================================

    def _update_value_fields(self, max_dict, max_keys=None):
        """
        Populate the left-panel summary result fields with the computed maximum
        values for all components.
        """
        mapping = [
            # Units stripped from value text — unit is shown in the row label.
            ("T_x",   "T_x",    "{:.2f}"),
            ("M_y",   "M_y",    "{:.2f}"),
            ("M_z",   "M_z",    "{:.2f}"),
            ("F_x",   "F_x",    "{:.2f}"),
            ("V_y",   "V_y",    "{:.2f}"),
            ("V_z",   "V_z",    "{:.2f}"),
            ("D_x",   "D_x",    "{:.2f}"),
            ("D_y",   "D_y",    "{:.2f}"),
            ("D_z",   "D_z",    "{:.2f}"),
        ]
        for dict_key, field_key, fmt in mapping:
            if field_key in self.analysis_tab.result_fields:
                val = max_dict.get(dict_key, 0.0)
                self.analysis_tab.result_fields[field_key].setText(fmt.format(val))

    def _update_right_panel_for_mode(self):
        """
        Refresh the right-column position/value labels based on the active mode.

        Maximum Values mode : shows each diagram's peak value and x-position
                              on two lines; expands label height to 55 px.
        Interactive mode    : shows the value at the current cursor index
                              on a single line; compresses label height to 35 px.

        This method is component-agnostic: it reads x_fields keys that are
        remapped by _update_analysis_plots whenever the component changes.
        """
        if self._current_x is None:
            return

        mode    = self._interaction_mode
        xf      = self.analysis_tab.x_fields   # {bmd_key: label, sfd_key: label, defl_key: label}
        keys    = list(xf.keys())              # [bmd_key, sfd_key, defl_key]

        # Unit suffix helpers for single-line interactive labels
        def _unit(k):
            if k.startswith("D"):
                return "mm"
            elif k.startswith("M"):
                return "kNm"
            return "kN"

        if mode == "Maximum Values":
            max_d  = getattr(self, "_current_max_dict", {})
            vals   = [max_d.get("M_max", 0.0), max_d.get("V_max", 0.0), max_d.get("D_max", 0.0)]
            x_pos  = [max_d.get("x_M", 0.0),   max_d.get("x_V", 0.0),   max_d.get("x_D", 0.0)]
            # Value unit stripped — shown in row label ("M_z (kNm)" etc.).
            # Position '... at x = N.NN m' keeps 'm' (positional context, not force unit).
            fmts   = ["{:.2f}<br>at x = {x:.2f} m",
                      "{:.2f}<br>at x = {x:.2f} m",
                      "{:.2f}<br>at x = {x:.2f} m"]

            if hasattr(self.analysis_tab, "x_input"):
                self.analysis_tab.x_input.setText("Multiple")
                self.analysis_tab.x_input.setFixedHeight(55)

            for key, val, xp, fmt in zip(keys, vals, x_pos, fmts):
                if key in xf:
                    xf[key].setFixedHeight(55)
                    xf[key].setText(fmt.format(val, x=xp))

        else:  # "Scroll for Values"
            # Use the exact cursor x-position (set by click or arrow key).
            # Fall back to node 0 if not yet set.
            cx = getattr(self, "_cursor_x", None)
            if cx is None:
                self._cursor_idx = getattr(self, "_cursor_idx", 0)
                self._cursor_idx = max(0, min(len(self._current_x) - 1, self._cursor_idx))
                cx = float(self._current_x[self._cursor_idx])
                self._cursor_x = cx

            # Linearly interpolate each diagram at the exact cursor x
            interp_data = [self._current_bmd, self._current_sfd, self._current_defl]
            # Value unit stripped — shown in row label. Precision unchanged.
            fmts_scalar = ["{:.2f}", "{:.2f}", "{:.2f}"]

            if hasattr(self.analysis_tab, "x_input"):
                self.analysis_tab.x_input.setText(f"{cx:.2f}")  # numerical position only
                self.analysis_tab.x_input.setFixedHeight(35)

            for key, data, fmt in zip(keys, interp_data, fmts_scalar):
                if key in xf:
                    val = float(np.interp(cx, self._current_x, data))
                    xf[key].setFixedHeight(35)
                    xf[key].setText(fmt.format(val))