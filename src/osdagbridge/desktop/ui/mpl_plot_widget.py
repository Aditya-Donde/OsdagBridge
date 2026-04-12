import matplotlib
matplotlib.use("QtAgg")

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
import matplotlib.pyplot as plt

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
)

from osdagbridge.core.bridge_types.plate_girder.plot_generator import (
    build_figure_sfd,
    build_figure_bmd,
    FORCE_MAP,
)

# Forces starting with "F" -> shear (SFD); starting with "M" -> moment (BMD)
_SFD_KEYS = {k for k in FORCE_MAP if k.startswith("F")}


class MplPlotWidget(QWidget):
    """
    PySide6 widget that renders matplotlib analysis plots.

    - Fx / Fy / Fz  -> Shear Force Diagram (step plot)
    - Mx / My / Mz  -> Bending Moment Diagram (curve plot)

    Call setup() after bridge.design() completes to populate the widget.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Data populated by setup()
        self._ds_all = None
        self._nodes = {}
        self._members = {}
        self._edge_dist = 0.0

        # Top control bar
        top = QHBoxLayout()
        top.setContentsMargins(4, 4, 4, 0)
        top.setSpacing(8)

        top.addWidget(QLabel("Load case:"))
        self.combo_lc = QComboBox()
        self.combo_lc.currentTextChanged.connect(self._on_controls_changed)
        top.addWidget(self.combo_lc)

        top.addWidget(QLabel("Force:"))
        self.combo_force = QComboBox()
        self.combo_force.addItems(list(FORCE_MAP.keys()))
        self.combo_force.setCurrentText("Fy")
        self.combo_force.currentTextChanged.connect(self._on_controls_changed)
        top.addWidget(self.combo_force)

        top.addStretch()

        # Matplotlib canvas
        self._fig = plt.figure(figsize=(14, 6), facecolor="white")
        self._canvas = FigureCanvasQTAgg(self._fig)
        self._canvas.setMinimumHeight(300)

        # Navigation toolbar (zoom / pan / save)
        self._toolbar = NavigationToolbar2QT(self._canvas, self)

        # Assemble layout
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addLayout(top)
        root.addWidget(self._toolbar)
        root.addWidget(self._canvas, stretch=1)

    # Public API

    def setup(self, ds_all, loadcases: list, nodes: dict, members: dict, edge_dist: float = 0.0):
        """
        Populate the widget after bridge analysis is complete.

        Parameters
        ----------
        ds_all    : xarray.Dataset  — full results dataset (all load cases)
        loadcases : list[str]       — load case names for the combo box
        nodes     : dict            — {tag: [x, y, z]}
        members   : dict            — {tag: [n1, n2]}
        edge_dist : float           — deck overhang; > 0 means edge beams are present
        """
        self._ds_all = ds_all
        self._nodes = nodes
        self._members = members
        self._edge_dist = edge_dist

        self.combo_lc.blockSignals(True)
        self.combo_lc.clear()
        self.combo_lc.addItems(loadcases)
        self.combo_lc.blockSignals(False)

        self.update_plot()

    def update_plot(self):
        """Rebuild and redraw the current figure from the selected controls."""
        if self._ds_all is None:
            return

        loadcase  = self.combo_lc.currentText()
        force_key = self.combo_force.currentText()

        ds = self._ds_all.sel(Loadcase=loadcase)

        plt.close(self._fig)

        if force_key in _SFD_KEYS:
            self._fig = build_figure_sfd(ds, force_key, self._nodes, self._members, edge_dist=self._edge_dist)
        else:
            self._fig, _ = build_figure_bmd(ds, force_key, self._nodes, self._members, edge_dist=self._edge_dist)

        self._canvas.figure = self._fig
        self._fig.set_canvas(self._canvas)
        self._canvas.draw()

    # Internal slots

    def _on_controls_changed(self):
        self.update_plot()
