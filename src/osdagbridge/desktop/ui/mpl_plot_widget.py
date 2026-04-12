import matplotlib
matplotlib.use("QtAgg")

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
import matplotlib.pyplot as plt

from PySide6.QtWidgets import QWidget, QVBoxLayout, QComboBox, QSizePolicy

from osdagbridge.core.bridge_types.plate_girder.plot_generator import (
    build_figure_sfd,
    build_figure_bmd,
    FORCE_MAP,
)

# Forces starting with "F" -> shear (SFD); starting with "M" -> moment (BMD)
_SFD_KEYS = {k for k in FORCE_MAP if k.startswith("F")}

# Map from the HTML labels used in OutputDock's force checkbox grid -> FORCE_MAP keys
_RICH_LABEL_TO_FORCE = {
    "F<sub>x</sub>": "Fx",
    "V<sub>y</sub>": "Fy",
    "V<sub>z</sub>": "Fz",
    "T<sub>x</sub>": "Mx",
    "M<sub>y</sub>": "My",
    "M<sub>z</sub>": "Mz",
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

        # matplotlib canvas
        self._fig    = plt.figure(figsize=(14, 6), facecolor="white")
        self._canvas = FigureCanvasQTAgg(self._fig)
        self._canvas.setMinimumHeight(300)
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # layout
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
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

        # pre-check default force + connect all force checkboxes
        from osdagbridge.desktop.ui.utils.combobox_utils import RichCheckBox
        force_cbs = [
            cb for cb in output_dock.output_widget.findChildren(RichCheckBox)
            if cb.text() in _RICH_LABEL_TO_FORCE
        ]
        for cb in force_cbs:
            cb.setChecked(cb.text() == _DEFAULT_FORCE_LABEL)
            cb.stateChanged.connect(self.update_plot)

        self.update_plot()

    def update_plot(self, *_args):
        """Rebuild and redraw the current figure from the OutputDock controls."""
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
        else:
            self._fig, _ = build_figure_bmd(
                ds, force_key, self._nodes, self._members,
                edge_dist=self._edge_dist
            )

        self._canvas.figure = self._fig
        self._fig.set_canvas(self._canvas)
        self._fit_figure_to_canvas()
        self._canvas.draw()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_figure_to_canvas()
        self._canvas.draw_idle()

    # private helpers

    def _fit_figure_to_canvas(self):
        """Resize the matplotlib figure to match the current canvas widget size."""
        w_px = self._canvas.width()
        h_px = self._canvas.height()
        if w_px > 10 and h_px > 10:
            dpi = self._fig.dpi
            self._fig.set_size_inches(w_px / dpi, h_px / dpi, forward=False)

    def _current_loadcase(self) -> str:
        """Read the selected load case from the OutputDock combobox."""
        combo = self._output_dock.output_widget.findChild(
            QComboBox, "analysis.load_combination"
        )
        return combo.currentText() if combo else (self._loadcases[0] if self._loadcases else "")

    def _current_force_key(self) -> str:
        """Return the FORCE_MAP key for the currently checked force checkbox."""
        from osdagbridge.desktop.ui.utils.combobox_utils import RichCheckBox
        for cb in self._output_dock.output_widget.findChildren(RichCheckBox):
            if cb.isChecked() and cb.text() in _RICH_LABEL_TO_FORCE:
                return _RICH_LABEL_TO_FORCE[cb.text()]
        return "Fy"   # fallback
