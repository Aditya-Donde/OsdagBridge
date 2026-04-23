import matplotlib
matplotlib.use("QtAgg")

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Path3DCollection 

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QSizePolicy, QPushButton
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


class MplPlotWidget(QWidget):
    """
    PySide6 widget that renders matplotlib analysis plots.

    Controls (load-case combo + force radio buttons) live in the OutputDock.
    Call setup() after bridge.design() completes, then link_output_dock() to
    wire the dock controls to this widget.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Data populated by setup()
        self._ds_all    = None
        self._loadcases = []
        self._nodes     = {}
        self._members   = {}
        self._edge_dist = 0.0

        # Set by link_output_dock()
        self._output_dock = None

        # Display States
        self._grillage_mode = False
        self._show_nodes = True 
        self._show_axis = True  # Track axis visibility state

        # Zoom state
        self._zoom_scale  = 1.0
        self._orig_limits = None   

        # matplotlib canvas
        self._fig    = plt.figure(figsize=(14, 6), facecolor="white")
        self._canvas = FigureCanvasQTAgg(self._fig)
        self._canvas.setMinimumHeight(300)
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._canvas.installEventFilter(self)

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
        self._btn_zoom_in.setToolTip("Zoom In")
        self._btn_zoom_out.setToolTip("Zoom Out")
        self._btn_zoom_reset.setToolTip("Reset Zoom")
        self._btn_zoom_in.clicked.connect(self._zoom_in)
        self._btn_zoom_out.clicked.connect(self._zoom_out)
        self._btn_zoom_reset.clicked.connect(self._zoom_reset)

        # grillage toggle button
        self._btn_grillage = QPushButton("Grillage")
        self._btn_grillage.setCheckable(True)
        self._btn_grillage.setFixedHeight(28)
        self._btn_grillage.setFocusPolicy(Qt.NoFocus)
        self._btn_grillage.setToolTip("Show bridge grillage only")
        self._btn_grillage.setStyleSheet(
            "QPushButton { font-size: 12px; border: 1px solid #bbb; border-radius: 4px;"
            " background: #f5f5f5; padding: 0 8px; }"
            "QPushButton:hover { background: #e0e0e0; }"
            "QPushButton:pressed { background: #bdbdbd; }"
            "QPushButton:checked { background: #1565C0; color: white;"
            " border: 1px solid #0D47A1; }"
        )
        self._btn_grillage.toggled.connect(self._on_grillage_toggled)

        # nodes toggle button
        self._btn_nodes = QPushButton("Nodes")
        self._btn_nodes.setCheckable(True)
        self._btn_nodes.setChecked(True) 
        self._btn_nodes.setFixedHeight(28)
        self._btn_nodes.setFocusPolicy(Qt.NoFocus)
        self._btn_nodes.setToolTip("Show or hide node markers")
        self._btn_nodes.setStyleSheet(
            "QPushButton { font-size: 12px; border: 1px solid #bbb; border-radius: 4px;"
            " background: #f5f5f5; padding: 0 8px; }"
            "QPushButton:hover { background: #e0e0e0; }"
            "QPushButton:pressed { background: #bdbdbd; }"
            "QPushButton:checked { background: #1565C0; color: white;"
            " border: 1px solid #0D47A1; }"
        )
        self._btn_nodes.toggled.connect(self._on_nodes_toggled)

        # NEW: axis toggle button
        self._btn_axis = QPushButton("Axis")
        self._btn_axis.setCheckable(True)
        self._btn_axis.setChecked(True) 
        self._btn_axis.setFixedHeight(28)
        self._btn_axis.setFocusPolicy(Qt.NoFocus)
        self._btn_axis.setToolTip("Show or hide coordinate axis")
        self._btn_axis.setStyleSheet(
            "QPushButton { font-size: 12px; border: 1px solid #bbb; border-radius: 4px;"
            " background: #f5f5f5; padding: 0 8px; }"
            "QPushButton:hover { background: #e0e0e0; }"
            "QPushButton:pressed { background: #bdbdbd; }"
            "QPushButton:checked { background: #1565C0; color: white;"
            " border: 1px solid #0D47A1; }"
        )
        self._btn_axis.toggled.connect(self._on_axis_toggled)

        toolbar_row = QHBoxLayout()
        toolbar_row.setContentsMargins(4, 2, 4, 2)
        toolbar_row.setSpacing(4)
        toolbar_row.addWidget(self._btn_grillage)
        toolbar_row.addWidget(self._btn_nodes)
        toolbar_row.addWidget(self._btn_axis) # Added next to Nodes
        toolbar_row.addStretch()
        toolbar_row.addWidget(self._btn_zoom_out)
        toolbar_row.addWidget(self._btn_zoom_in)
        toolbar_row.addWidget(self._btn_zoom_reset)

        # layout
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addLayout(toolbar_row)
        root.addWidget(self._canvas, stretch=1)

    # public API

    def setup(self, ds_all, loadcases: list, nodes: dict, members: dict,
              edge_dist: float = 0.0):
        """
        Store analysis results.  Does NOT redraw - call link_output_dock()
        (or update_plot() directly) after this.
        """
        self._ds_all    = ds_all
        self._loadcases = list(loadcases)
        self._nodes     = nodes
        self._members   = members
        self._edge_dist = edge_dist

    def link_output_dock(self, output_dock):
        """
        Wire the OutputDock's load-combination combobox and force checkboxes
        to this widget, populate them with live data, and draw the first plot.

        Call once after setup() completes.
        """
        self._output_dock = output_dock

        # populate & connect load-combination combobox
        combo_lc = output_dock.output_widget.findChild(
            QComboBox, "analysis.load_combination"
        )
        if combo_lc is not None:
            combo_lc.blockSignals(True)
            combo_lc.clear()
            combo_lc.addItems(self._loadcases)
            combo_lc.blockSignals(False)
            # Prevent long item text from widening the dock
            combo_lc.setSizeAdjustPolicy(
                QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
            )
            combo_lc.setMinimumContentsLength(12)
            combo_lc.currentTextChanged.connect(self.update_plot)

        # pre-check default force + connect all force radio buttons
        from osdagbridge.desktop.ui.utils.custom_widgets import CustomRadioButton
        force_rbs = [
            rb for rb in output_dock.output_widget.findChildren(CustomRadioButton)
            if rb.text() in _RICH_LABEL_TO_FORCE
        ]
        for rb in force_rbs:
            rb.setChecked(rb.text() == _DEFAULT_FORCE_LABEL)
            rb.toggled.connect(self.update_plot)

        self.update_plot()

    def update_plot(self, *_args):
        """Rebuild and redraw the current figure from the OutputDock controls."""
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

        if force_key in _SFD_KEYS:
            self._fig = build_figure_sfd(
                ds, force_key, self._nodes, self._members,
                edge_dist=self._edge_dist
            )
        elif force_key in _DEFL_KEYS:
            self._fig = build_figure_deflection(
                ds, force_key, self._nodes, self._members,
                edge_dist=self._edge_dist
            )
        else:
            self._fig, _ = build_figure_bmd(
                ds, force_key, self._nodes, self._members,
                edge_dist=self._edge_dist
            )

        self._canvas.figure = self._fig
        self._fig.set_canvas(self._canvas)
        
        # Ensure toggles match their current state
        self._apply_node_visibility()
        self._apply_axis_visibility()
        
        self._fit_figure_to_canvas()
        self._canvas.draw()

        # reset zoom and capture fresh axis limits
        self._zoom_scale = 1.0
        self._store_orig_limits()

    def _on_grillage_toggled(self, checked: bool):
        """Show grillage-only plot when checked; restore force diagram when unchecked."""
        self._grillage_mode = checked
        if checked:
            if not self._nodes:
                return
            plt.close(self._fig)
            self._fig = build_figure_grillage(self._nodes, self._members)
            self._canvas.figure = self._fig
            self._fig.set_canvas(self._canvas)
            
            # Ensure toggles match their current state
            self._apply_node_visibility()
            self._apply_axis_visibility()
            
            self._fit_figure_to_canvas()
            self._canvas.draw()
            self._zoom_scale = 1.0
            self._store_orig_limits()
        else:
            self.update_plot()

    def _on_nodes_toggled(self, checked: bool):
        """Instantly toggle the visibility of scatter plot nodes without rebuilding the figure."""
        self._show_nodes = checked
        self._apply_node_visibility()
        self._canvas.draw_idle() 

    def _on_axis_toggled(self, checked: bool):
        """Instantly toggle the visibility of the XYZ coordinate triad."""
        self._show_axis = checked
        self._apply_axis_visibility()
        self._canvas.draw_idle()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_figure_to_canvas()
        self._canvas.draw_idle()

    # private helpers

    def _apply_node_visibility(self):
        """Finds all scatter point collections (Path3DCollection) and toggles their visibility."""
        for ax in self._fig.axes:
            for collection in ax.collections:
                if isinstance(collection, Path3DCollection):
                    collection.set_visible(self._show_nodes)

    def _apply_axis_visibility(self):
        """Finds all collections and text tagged as 'coord_triad' and toggles them."""
        for ax in self._fig.axes:
            for collection in ax.collections:
                if collection.get_gid() == "coord_triad":
                    collection.set_visible(self._show_axis)
            for text in ax.texts:
                if text.get_gid() == "coord_triad":
                    text.set_visible(self._show_axis)

    def _fit_figure_to_canvas(self):
        """Resize the matplotlib figure to match the current canvas widget size."""
        w_px = self._canvas.width()
        h_px = self._canvas.height()
        if w_px > 10 and h_px > 10:
            dpi = self._fig.dpi
            self._fig.set_size_inches(w_px / dpi, h_px / dpi, forward=False)

    def _store_orig_limits(self):
        """Snapshot current 3-D axis limits so zoom can scale relative to them."""
        self._orig_limits = {}
        for i, ax in enumerate(self._fig.axes):
            if hasattr(ax, "get_zlim"):
                self._orig_limits[i] = {
                    "x": ax.get_xlim(),
                    "y": ax.get_ylim(),
                    "z": ax.get_zlim(),
                }

    def _apply_zoom(self):
        """Scale each 3-D axis uniformly around its centre by _zoom_scale."""
        if not self._orig_limits:
            return
        for i, ax in enumerate(self._fig.axes):
            if i not in self._orig_limits:
                continue
            lims = self._orig_limits[i]
            for axis_key, set_lim in [
                ("x", ax.set_xlim),
                ("y", ax.set_ylim),
                ("z", ax.set_zlim),
            ]:
                lo, hi = lims[axis_key]
                centre = (lo + hi) / 2.0
                half   = (hi - lo) / 2.0 * self._zoom_scale
                set_lim(centre - half, centre + half)
        self._canvas.draw_idle()

    def eventFilter(self, obj, event):
        """Intercept scroll wheel on the canvas to zoom."""
        if obj is self._canvas and event.type() == QEvent.Type.Wheel:
            delta = event.angleDelta().y()
            if delta > 0:
                self._zoom_scale = max(self._zoom_scale * 0.8, 0.05)
            else:
                self._zoom_scale = min(self._zoom_scale * 1.25, 20.0)
            self._apply_zoom()
            return True   # consume — prevent parent scroll area from scrolling
        return super().eventFilter(obj, event)

    def _zoom_in(self):
        self._zoom_scale = max(self._zoom_scale * 0.8, 0.05)
        self._apply_zoom()

    def _zoom_out(self):
        self._zoom_scale = min(self._zoom_scale * 1.25, 20.0)
        self._apply_zoom()

    def _zoom_reset(self):
        self._zoom_scale = 1.0
        self._apply_zoom()

    def _current_loadcase(self) -> str:
        """Read the selected load case from the OutputDock combobox."""
        combo = self._output_dock.output_widget.findChild(
            QComboBox, "analysis.load_combination"
        )
        return combo.currentText() if combo else (self._loadcases[0] if self._loadcases else "")

    def _current_force_key(self) -> str:
        """Return the FORCE_MAP key for the currently checked force radio button."""
        from osdagbridge.desktop.ui.utils.custom_widgets import CustomRadioButton
        for rb in self._output_dock.output_widget.findChildren(CustomRadioButton):
            if rb.isChecked() and rb.text() in _RICH_LABEL_TO_FORCE:
                return _RICH_LABEL_TO_FORCE[rb.text()]
        return "Fy"   # fallback