from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
import numpy as np


class Girder2DPlotsWidget(QWidget):
    """
    Osdag Bridge – Girder 2D Analysis Plots

    Displays:
    - BMD
    - SFD
    - Deflections

    Cursor movement emits values for RHS result boxes.
    """

    # --------------------------------------------------
    # SIGNALS (connect this to RHS UI later)
    # --------------------------------------------------
    cursorMoved = Signal(float, float, float, float)
    # emits: x, M, V, d

    def __init__(self, parent=None):
        super().__init__(parent)

        # Data containers
        self.x_data = None
        self.bmd_data = None
        self.sfd_data = None
        self.def_data = None

        self.cursor_lines = []

        self.__init__ui()
        self.__init__axes()
        self._connect_events()

    # --------------------------------------------------
    # UI
    # --------------------------------------------------
    def __init__ui(self):
        layout = QVBoxLayout(self)

        self.figure = Figure(figsize=(6.2, 8.5))
        self.canvas = FigureCanvas(self.figure)

        layout.addWidget(self.canvas)

    # --------------------------------------------------
    # AXES LAYOUT (UI-LOCKED)
    # --------------------------------------------------
    def __init__axes(self):
        gs = GridSpec(3, 1, hspace=0.06)

        self.ax_bmd = self.figure.add_subplot(gs[0])
        self.ax_sfd = self.figure.add_subplot(gs[1], sharex=self.ax_bmd)
        self.ax_def = self.figure.add_subplot(gs[2], sharex=self.ax_bmd)

        # Engineering convention
        self.ax_def.invert_yaxis()

        # Remove chart look
        for ax in (self.ax_bmd, self.ax_sfd, self.ax_def):
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_visible(False)
            ax.tick_params(axis="y", left=False, labelleft=False)
            ax.tick_params(axis="x", length=0)

        self.ax_bmd.tick_params(labelbottom=False)
        self.ax_sfd.tick_params(labelbottom=False)

        # Zero reference lines
        self.ax_bmd.axhline(0, color="black", linewidth=0.9)
        self.ax_sfd.axhline(0, color="black", linewidth=0.9)

    # --------------------------------------------------
    # EVENTS
    # --------------------------------------------------
    def _connect_events(self):
        self.canvas.mpl_connect("motion_notify_event", self._on_mouse_move)

    def _on_mouse_move(self, event):
        if event.xdata is None or self.x_data is None:
            return

        # Clamp cursor inside span
        x = max(self.x_data[0], min(event.xdata, self.x_data[-1]))

        # Move cursor lines
        for line in self.cursor_lines:
            line.set_xdata([x])

        # Interpolate values
        m = np.interp(x, self.x_data, self.bmd_data)
        v = np.interp(x, self.x_data, self.sfd_data)
        d = np.interp(x, self.x_data, self.def_data)

        # Emit for RHS UI
        self.cursorMoved.emit(x, m, v, d)

        self.canvas.draw_idle()

    # --------------------------------------------------
    # MAIN API (THIS IS WHAT analysis_results.py CALLS)
    # --------------------------------------------------
    def plot_girder_results(self, x, bmd, sfd, defl):
        """
        UPDATE POINT:
        Call this method from analysis_results.py

        Parameters
        ----------
        x     : array-like (span positions)
        bmd   : bending moment values
        sfd   : shear force values
        defl  : deflection values
        """

        self.x_data = np.asarray(x)
        self.bmd_data = np.asarray(bmd)
        self.sfd_data = np.asarray(sfd)
        self.def_data = np.asarray(defl)

        xmin, xmax = self.x_data[0], self.x_data[-1]

        # Clear axes
        self.ax_bmd.clear()
        self.ax_sfd.clear()
        self.ax_def.clear()

        # Lock x-range everywhere
        for ax in (self.ax_bmd, self.ax_sfd, self.ax_def):
            ax.set_xlim(xmin, xmax)
            ax.margins(x=0)

        fill_color = "#4f79d8"

        # --- BMD ---
        self.ax_bmd.fill_between(self.x_data, self.bmd_data, color=fill_color, alpha=0.9)
        self.ax_bmd.axhline(0, color="black", linewidth=0.9)

        # --- SFD ---
        self.ax_sfd.fill_between(self.x_data, self.sfd_data, color=fill_color, alpha=0.9)
        self.ax_sfd.axhline(0, color="black", linewidth=0.9)

        # --- DEFLECTION ---
        self.ax_def.plot(self.x_data, self.def_data, color="black", linewidth=1.8)

        # Support dotted lines
        for ax in (self.ax_bmd, self.ax_sfd, self.ax_def):
            ax.axvline(xmin, color="#9e9e9e", linestyle=":", linewidth=1.2)
            ax.axvline(xmax, color="#9e9e9e", linestyle=":", linewidth=1.2)

        # Center labels (figma-style)
        self._center_label(self.ax_bmd, "BMD")
        self._center_label(self.ax_sfd, "SFD")
        self._center_label(self.ax_def, "Deflections")

        # Mark max moment
        imax = np.argmax(self.bmd_data)
        xm, mm = self.x_data[imax], self.bmd_data[imax]
        self.ax_bmd.plot(xm, mm, "ko", markersize=4)
        self.ax_bmd.text(xm + 0.4, mm, "Mᵤ", fontsize=9, va="bottom")

        # Span arrow (bottom only)
        self.ax_def.annotate(
            "",
            xy=(xmax, 0),
            xytext=(xmin, 0),
            xycoords=("data", "axes fraction"),
            arrowprops=dict(arrowstyle="<->", linewidth=1),
        )

        self.ax_def.text(
            (xmin + xmax) / 2,
            -0.13,
            "Span (m)",
            transform=self.ax_def.get_xaxis_transform(),
            ha="center",
            va="top",
            fontsize=9,
        )

        # Cursor initialization
        self.cursor_lines = []
        for ax in (self.ax_bmd, self.ax_sfd, self.ax_def):
            line = ax.axvline(
                x=xmin,
                color="black",
                linestyle=(0, (4, 4)),
                linewidth=1,
                alpha=0.6,
            )
            self.cursor_lines.append(line)

        self.canvas.draw()

    # --------------------------------------------------
    # HELPER
    # --------------------------------------------------
    def _center_label(self, ax, text):
        ax.text(
            0.5,
            0.86,
            text,
            transform=ax.transAxes,
            fontsize=9,
            fontweight="bold",
            ha="center",
            va="center",
            color="white",
            bbox=dict(
                boxstyle="round,pad=0.25",
                facecolor="#4a4a4a",
                edgecolor="none",
                alpha=0.9,
            ),
        )