from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QTabBar, QWidget, QSizeGrip,
    QSizePolicy, QRadioButton, QLabel, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.dialogs.tabs.steel_design_details import SteelDesignDetailsTab
from osdagbridge.desktop.ui.dialogs.tabs.steel_design_analysis import SteelDesignAnalysisTab
from osdagbridge.desktop.ui.dialogs.tabs.steel_design_check import SteelDesignCheckTab
from osdagbridge.desktop.ui.docks.output_dock import NoScrollComboBox

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from osdagbridge.core.bridge_types.plate_girder.graph_engine import GirderGraphEngine

# Prefix used to identify non-selectable category header items in combo boxes.
_COMBO_HEADER_PREFIX = "──"

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

    def __init__(self, parent=None, result_handler=None):
        super().__init__(None)
        self._main_window    = parent
        
        # Auto-fetch if missing (handles legacy callers like output_dock)
        if result_handler is None and hasattr(self._main_window, "backend"):
            try:
                result_handler = self._main_window.backend.get_result_handler()
            except (RuntimeError, AttributeError):
                pass
                
        self._result_handler = result_handler  # PlateGirderAnalysisResults or None
        self._checks_ran   = False
        self._last_handler = None
        self.setObjectName("SteelDesign")
        self.resize(1024, 720)
        self.setMinimumSize(900, 520)
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
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint | Qt.Window)

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

        main_layout.addWidget(self._build_global_selection_bar())
        main_layout.addWidget(self.tabs)

        if hasattr(self._main_window, "cad_state"):
            self.details_tab.load_data(self._main_window.cad_state)

        if self._result_handler is not None:
            # Inject the matplotlib canvas into the Analysis Results tab
            self._setup_analysis_plots()
        else:
            self.analysis_tab.diagram_placeholder.setText("Create a design first to see analysis results.")

    def _build_global_selection_bar(self):
        """Build the global Member ID and Load Combination bar."""
        # Shared card stylesheet
        _CARD_STYLE = (
            "QFrame#controlCard {"
            "  background-color: white;"
            "  border: 1px solid #b0b0b0;"
            "  border-radius: 6px;"
            "}"
            "QFrame#controlCard > QLabel {"
            "  border: none;"
            "  background: transparent;"
            "}"
        )
        _TITLE_STYLE = (
            "font-size: 13px; color: #2B2B2B; font-weight: bold;"
            " background: transparent; border: none;"
        )
        _COMBO_STYLE = """
            QComboBox {
                padding: 1px 7px;
                border: 1px solid black;
                border-radius: 5px;
                background-color: white;
                color: black;
                font-size: 11px;
                min-height: 28px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                border-left: 0px;
            }
            QComboBox::down-arrow {
                image: url(:/vectors/arrow_down_light.svg);
                width: 20px;
                height: 20px;
                margin-right: 8px;
            }
            QComboBox::down-arrow:on {
                image: url(:/vectors/arrow_up_light.svg);
                width: 20px;
                height: 20px;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                border: 1px solid black;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                color: black;
                background-color: white;
                border: 1px solid white;
                border-radius: 0;
                padding: 2px;
            }
            QComboBox QAbstractItemView::item:hover {
                border: 1px solid #90AF13;
                background-color: #90AF13;
                color: black;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #90AF13;
                color: black;
                border: 1px solid #90AF13;
            }
            QComboBox QAbstractItemView QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 8px;
                margin-left: 2px;
            }
            QComboBox QAbstractItemView QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 4px;
                min-height: 20px;
            }
            QComboBox QAbstractItemView QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            QComboBox QAbstractItemView QScrollBar::handle:vertical:pressed {
                background: #808080;
            }
            QComboBox QAbstractItemView QScrollBar::add-line:vertical,
            QComboBox QAbstractItemView QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QComboBox QAbstractItemView QScrollBar::add-page:vertical,
            QComboBox QAbstractItemView QScrollBar::sub-page:vertical {
                background: none;
            }
        """

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 6)
        row.setSpacing(16)

        # - Member ID card -
        member_card = QFrame()
        member_card.setObjectName("controlCard")
        member_card.setStyleSheet(_CARD_STYLE)
        member_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        mc_layout = QVBoxLayout(member_card)
        mc_layout.setContentsMargins(23, 10, 14, 12)
        mc_layout.setSpacing(4)

        member_title = QLabel("Member ID")
        member_title.setStyleSheet(_TITLE_STYLE)
        mc_layout.addWidget(member_title)

        self.member_combo = NoScrollComboBox()
        self.member_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.member_combo.setFixedHeight(28)
        self.member_combo.setStyleSheet(_COMBO_STYLE)
        mc_layout.addWidget(self.member_combo)

        # - Load Combination card -
        load_card = QFrame()
        load_card.setObjectName("controlCard")
        load_card.setStyleSheet(_CARD_STYLE)
        load_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lc_layout = QVBoxLayout(load_card)
        lc_layout.setContentsMargins(23, 10, 14, 12)
        lc_layout.setSpacing(4)

        load_title = QLabel("Load Combination")
        load_title.setStyleSheet(_TITLE_STYLE)
        lc_layout.addWidget(load_title)

        self.load_combo = NoScrollComboBox()
        self.load_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.load_combo.setFixedHeight(28)
        self.load_combo.setStyleSheet(_COMBO_STYLE)
        lc_layout.addWidget(self.load_combo)

        row.addWidget(member_card, 1)
        row.addWidget(load_card, 1)

        return container

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
        gs = self.figure.add_gridspec(4, 1, height_ratios=[0.55, 1, 1, 1], hspace=0.70)
        self.ax_scheme = self.figure.add_subplot(gs[0])
        self.ax_bmd    = self.figure.add_subplot(gs[1])
        self.ax_sfd    = self.figure.add_subplot(gs[2])
        self.ax_defl   = self.figure.add_subplot(gs[3])
        self.figure.subplots_adjust(left=0.12, right=0.96, top=0.97, bottom=0.08)

        # ── Graph engine: owns all render/draw logic ──────────────────────────
        if hasattr(self._main_window, "backend") and hasattr(self._main_window.backend, "build_graph_engine"):
            self.graph_engine = self._main_window.backend.build_graph_engine(
                self.figure, self.ax_scheme, self.ax_bmd, self.ax_sfd, self.ax_defl, 
                result_handler=self._result_handler,
            )
        else:
            self.graph_engine = GirderGraphEngine(
                self.figure, self.ax_scheme, self.ax_bmd, self.ax_sfd, self.ax_defl,
                result_handler=self._result_handler,
            )
            
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
        # NOTE: member_combo and load_combo are now fully interactive
        self.member_combo.currentIndexChanged.connect(self._update_analysis_plots)
        self.load_combo.currentIndexChanged.connect(self._on_load_combo_changed)
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
        self._cursor_idx   = 0      # nearest node index for arrow-key navigation

        # ── UI initialisation state ───────────────────────────────────────────
        self._data_initialized = False

        # ── Performance: skip redundant re-renders ────────────────────────────
        # Track the last plotted (member, loadcase, component) to avoid
        # expensive matplotlib re-renders when nothing has changed.
        self._last_plot_key: tuple | None = None

        # Track the last member key for which DCR was computed so the
        # Design Check tab can skip re-running the full pipeline.
        self._last_dcr_member_key: str | None = None

        # Flag set when member/LC selection changes — tells the Design Check
        # tab that cached DCR values are stale and need recomputation.
        self._dcr_dirty = True

        # ── Populate dropdowns immediately so they show values on launch ──────
        if self._result_handler is not None:
            self._populate_member_combo()
            self._populate_load_combo()
            self._data_initialized = True

            # Pre-populate Design Check tab with the default girder's DCR values
            # so results are visible without switching tabs first.
            self._run_design_checks()



    def _on_tab_changed(self, index):
        """
        Entry point for the Analysis Results tab (index 1) and
        the Design Check tab (index 2).
        Populates dropdowns on first visit, then triggers a plot render.
        All data comes from the injected PlateGirderAnalysisResults instance.
        """
        if index == 2:
            # Design Check tab — only recompute if selection changed.
            if self._dcr_dirty:
                self._run_design_checks()
            return

        if index != 1:
            return

        if self._result_handler is None:
            if hasattr(self, 'canvas'):
                self.graph_engine.show_blank_state(self.canvas, message="Create a design first to see analysis results.")
            else:
                self.analysis_tab.diagram_placeholder.setText("Create a design first to see analysis results.")
            return

        # Combos are populated at launch; guard prevents double-population
        # if the dialog was opened without a result handler initially.
        if not self._data_initialized:
            self._populate_member_combo()
            self._populate_load_combo()
            self._data_initialized = True

        self._update_analysis_plots()

    def _run_design_checks(self) -> None:
        """
        Populate the Design Check tab for the currently selected member.

        Uses a dirty-flag + member-key cache to avoid re-running the full
        DCR pipeline when nothing has changed.  The first call falls back
        to the pre-computed engine stored on the backend; subsequent calls
        dynamically recompute for the selected member.
        """
        combo      = self.member_combo
        member_key = combo.currentData() or combo.currentText() or ""

        # Fast path: nothing changed since the last computation.
        if not self._dcr_dirty and member_key == self._last_dcr_member_key:
            return

        # If a member is selected, compute DCR dynamically for that girder.
        if member_key:
            self._update_design_checks_for_member(member_key)
            return

        # Fallback for first launch: use the backend's pre-computed engine
        # (produced during design() → _run_dcr_checks()).
        if self._checks_ran and (self._result_handler is self._last_handler):
            return

        try:
            backend = getattr(self._main_window, "backend", None)
            engine  = getattr(backend, "_dcr_engine", None) if backend else None
            if engine is None:
                return

            self.check_tab.populate_from_results(
                engine.demand, engine.capacity, engine,
            )

            self._checks_ran          = True
            self._last_handler        = self._result_handler
            self._dcr_dirty           = False
            self._last_dcr_member_key = member_key

        except Exception:
            import traceback
            err = f"Design check error:\n{traceback.format_exc()}"
            for key in ("flexure", "shear", "interaction", "ltb",
                        "shear_long_trans", "fatigue", "stress", "deflection"):
                self.check_tab.set_check_result(key, err)

    def _update_design_checks_for_member(self, member_key: str) -> None:
        """
        Re-run the DCR pipeline for the selected girder member.

        Skips if *member_key* matches the last-computed key and the dirty
        flag is not set, providing O(1) repeated tab visits.

        Imports and calls classes from designer.py (read-only — no modifications
        to that module).  The pipeline is:
            1. BridgeConfig from backend
            2. DemandExtractor.from_analysis_results() for the specific girder
            3. IRC22CapacityCalculator.compute_all()
            4. DCREngine.run_all_checks()
            5. check_tab.populate_from_results()
        """
        # Skip if already computed for this exact selection.
        if member_key == self._last_dcr_member_key and not self._dcr_dirty:
            return

        try:
            backend = getattr(self._main_window, "backend", None)
            if backend is None or self._result_handler is None:
                return

            from osdagbridge.core.bridge_types.plate_girder.designer import (
                BridgeConfig,
                DemandExtractor,
                IRC22CapacityCalculator,
                DCREngine,
                _composite_stiffness_ratio,
            )

            # Step 1: BridgeConfig
            config = BridgeConfig.from_plate_girder_bridge(backend)

            # Step 2: Resolve girder elements/nodes for the selected member
            girders, _ = self._result_handler.build_girders(verbose=False)
            girder_info = girders.get(member_key)
            if girder_info is None:
                # member_key not found — keep the existing checks
                return

            element_ids = list(girder_info.get("elements", []))
            node_ids    = list(girder_info.get("path", []))
            if not element_ids:
                return

            # Step 3: Extract demands for this specific girder
            Ze_steel_mm3 = float(config.section.Ze_steel)
            Aw_mm2       = float(config.section.Aw)
            Nsc          = int(config.fatigue.Nsc)
            ratio        = _composite_stiffness_ratio(config)

            demand = DemandExtractor.from_analysis_results(
                results=self._result_handler,
                element_ids=element_ids,
                node_ids=node_ids,
                Ze_steel_mm3=Ze_steel_mm3,
                Aw_mm2=Aw_mm2,
                Nsc=Nsc,
                member_name=member_key,
                stiffness_ratio=ratio,
            )

            # Step 4: Compute capacity
            calculator = IRC22CapacityCalculator(config)
            capacity = calculator.compute_all(
                Vu_kN=demand.Vu_kN,
                stress_range_MPa=demand.stress_range_MPa,
            )

            # Step 5: Run DCR checks
            engine = DCREngine(demand, capacity)
            engine.run_all_checks()

            # Store the dynamic engine so _run_design_checks uses it
            self._dynamic_dcr_engine = engine

            # Step 6: Update the Design Check tab
            self.check_tab.populate_from_results(
                engine.demand, engine.capacity, engine,
            )

            # Mark as clean for this member.
            self._dcr_dirty           = False
            self._last_dcr_member_key = member_key

        except Exception:
            import traceback
            traceback.print_exc()

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
    #   LOAD COMBO CHANGE HANDLER
    # =========================================================================

    def _on_load_combo_changed(self, index: int) -> None:
        """
        Called when the load combination dropdown selection changes.

        If the user navigates onto a category header item (which is
        disabled / non-selectable), this handler automatically advances
        the selection to the next real load case in the appropriate
        direction, then delegates to ``_update_analysis_plots``.
        """
        combo = self.load_combo
        model = combo.model()
        n     = combo.count()

        if n == 0:
            return

        # Check whether the current item is a non-selectable header
        item = model.item(index) if model and 0 <= index < n else None
        if item and not item.isEnabled():
            # Try scanning forward first, then backward
            for direction in (+1, -1):
                candidate = index + direction
                while 0 <= candidate < n:
                    cand_item = model.item(candidate)
                    if cand_item and cand_item.isEnabled():
                        combo.blockSignals(True)
                        combo.setCurrentIndex(candidate)
                        combo.blockSignals(False)
                        break
                    candidate += direction
                else:
                    continue
                break   # found a valid candidate — stop scanning
            return      # setCurrentIndex will re-trigger this slot

        self._update_analysis_plots()

    # =========================================================================
    #   DROPDOWN POPULATION HELPERS
    # =========================================================================

    def _populate_member_combo(self):
        """Populate the member dropdown with human-readable girder names."""
        def _girder_display_name(key: str, idx: int) -> str:
            """
            Map raw BFS girder key to a human-readable dropdown label.
            EB1/EB2  → 'Edge Beam 1' / 'Edge Beam 2'
            G1…Gn   → 'Girder 1' … 'Girder n'
            Anything else → key as-is (safe fallback)
            """
            if key == "EB1":
                return "Edge Beam 1"
            if key == "EB2":
                return "Edge Beam 2"
            if key.startswith("G") and key[1:].isdigit():
                return f"Girder {key[1:]}"
            return key   # fallback: show raw key

        combo = self.member_combo
        combo.blockSignals(True)
        combo.clear()
        for idx, key in enumerate(self.graph_engine.get_girder_keys()):
            combo.addItem(_girder_display_name(key, idx), userData=key)
        combo.blockSignals(False)

    # ── Category-header helper ────────────────────────────────────────────────
    @staticmethod
    def _add_combo_header(combo, text: str) -> None:
        """
        Add a non-selectable bold category header to *combo*.
        The item is styled to look like a section separator.
        """
        combo.addItem(text)
        model = combo.model()
        idx   = combo.count() - 1
        item  = model.item(idx)
        if item:
            item.setEnabled(False)
            f = QFont()
            f.setBold(True)
            f.setPointSize(9)
            item.setFont(f)
            item.setForeground(QColor("#6c6c6c"))

    def _populate_load_combo(self):
        """
        Populate the load combination dropdown from the actual load cases
        present in the cached results, grouped into three categories:

          ── Dead Loads ──
            girder self weight
            Deck slab load
            …
          ── Static Vehicle Loads ──
            Case1 ClassA L1
            …
          ── Moving Vehicle Loads ──
            Moving Case1 ClassA L1 at global position …
            …

        Category headers are bold and non-selectable.  Each group is only
        added when it contains at least one item.  The first real (selectable)
        load case is selected after population.
        """
        combo    = self.load_combo
        classified = self.graph_engine.get_classified_loadcases()

        dead_lcs    = classified.get("dead", [])
        static_lcs  = classified.get("vehicle_static", [])
        moving_lcs  = classified.get("vehicle_moving", [])

        # Ensure 'girder self weight' is first among dead loads
        preferred = "girder self weight"
        if preferred in dead_lcs:
            dead_lcs.remove(preferred)
            dead_lcs = [preferred] + dead_lcs

        combo.blockSignals(True)
        combo.clear()

        first_selectable_idx = None

        # ── Dead Loads ────────────────────────────────────────────────────────
        if dead_lcs:
            self._add_combo_header(combo, f"{_COMBO_HEADER_PREFIX} Dead Loads {_COMBO_HEADER_PREFIX}")
            for lc in dead_lcs:
                combo.addItem(lc)
                if first_selectable_idx is None:
                    first_selectable_idx = combo.count() - 1

        # ── Static Vehicle Loads ──────────────────────────────────────────────
        if static_lcs:
            self._add_combo_header(combo, f"{_COMBO_HEADER_PREFIX} Static Vehicle Loads {_COMBO_HEADER_PREFIX}")
            for lc in static_lcs:
                combo.addItem(lc)
                if first_selectable_idx is None:
                    first_selectable_idx = combo.count() - 1

        # ── Moving Vehicle Loads ──────────────────────────────────────────────
        if moving_lcs:
            self._add_combo_header(combo, f"{_COMBO_HEADER_PREFIX} Moving Vehicle Loads {_COMBO_HEADER_PREFIX}")
            for lc in moving_lcs:
                combo.addItem(lc)
                if first_selectable_idx is None:
                    first_selectable_idx = combo.count() - 1

        # Select the first real item so nothing tries to look up a header
        if first_selectable_idx is not None:
            combo.setCurrentIndex(first_selectable_idx)
        elif combo.count() > 0:
            combo.setCurrentIndex(0)

        combo.blockSignals(False)



    # =========================================================================
    #   PLOT RENDERING
    # =========================================================================

    def _update_analysis_plots(self, *_args):
        """
        Master orchestrator called when the girder, load combination, or component
        selection changes. Delegates data extraction and peak computation to the
        graph engine, then renders all plots and refreshes the right-hand panel.

        Includes a state-change guard: if the (member, loadcase, component)
        triple is identical to the last render, the expensive matplotlib
        redraw is skipped entirely.
        """
        engine = self.graph_engine

        if self._result_handler is None:
            engine.show_blank_state(self.canvas)
            return

        combo      = self.member_combo
        member_key = combo.currentData() or combo.currentText()
        loadcase   = self.load_combo.currentText()

        # Reject header/separator items (they start with '──')
        if not loadcase or loadcase.startswith(_COMBO_HEADER_PREFIX):
            return

        if not member_key or not self.graph_engine.get_girder_keys():
            return

        # ── Determine active component ────────────────────────────────────────
        comp_idx = 0
        if hasattr(self.analysis_tab, "component_combo"):
            comp_idx = self.analysis_tab.component_combo.currentIndex()

        # ── Skip redundant re-renders ─────────────────────────────────────────
        plot_key = (member_key, loadcase, comp_idx)
        if plot_key == self._last_plot_key and self._current_x is not None:
            return
        self._last_plot_key = plot_key

        # Mark DCR as stale whenever the analysis inputs change.
        self._dcr_dirty = True

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

        result = engine.extract_member_results(member_key, loadcase, bmd_key, sfd_key)
        if result is None:
            engine.show_blank_state(self.canvas)
            return

        xs, bmd_values, sfd_values, defl_values, all_data = result
        self._current_x    = xs
        self._current_bmd  = bmd_values
        self._current_sfd  = sfd_values
        self._current_defl = defl_values

        self._current_max_dict = engine.compute_maximums(
            xs, bmd_values, sfd_values, all_data
        )

        # ── Append support reactions to dict ──────────────────────────────────
        try:
            if len(sfd_values) >= 2:
                # The first value is the shear strictly at the left support (x=0)
                # The second-to-last value is the shear at the right support (x=L) 
                # (since the very last value at index -1 was padded with 0.0)
                self._current_max_dict["R_A"] = float(abs(sfd_values[0]))
                self._current_max_dict["R_B"] = float(abs(sfd_values[-2]))
        except Exception:
            pass

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

        # ── Gather reactions for scheme label overlay ─────────────────────────────
        _reactions = None
        try:
            _reactions = engine.extract_reactions(loadcase, member_key)
        except Exception:
            pass  # Non-fatal: scheme renders without reaction labels

        # ── Gather load descriptors for scheme load overlay ───────────────────────
        _loads = None
        try:
            _loads = engine.extract_loads(loadcase) or None
        except Exception:
            pass  # Non-fatal: scheme renders without load overlays

        engine.render_plots(
            xs, bmd_values, sfd_values, self.canvas,
            reactions=_reactions,
            loads=_loads,
            defl_values=defl_values,
        )
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
            ("R_A",   "R_A",    "{:.2f}"),
            ("R_B",   "R_B",    "{:.2f}"),
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
            interp_data = [self._current_bmd, self._current_sfd]
            # Only include deflection if it's a real array, not None
            if self._current_defl is not None and len(self._current_defl) == len(self._current_x):
                interp_data.append(self._current_defl)
            else:
                interp_data.append(np.zeros_like(self._current_x))
            
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
