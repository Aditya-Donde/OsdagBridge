from __future__ import annotations

import logging
from typing import Optional

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QFrame, QComboBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

logger = logging.getLogger(__name__)

class Girder2DPlotsWidget(QWidget):
    """
    Standalone PySide6 widget — four-panel girder diagram (schematic, BMD,
    SFD, deflection) with interactive girder selector and cursor overlay.

    Isolation contract
    ------------------
    This widget has no knowledge of OpenSees, ospgrillage, xarray, or any
    bridge model type.  Its sole interface to the analysis layer is a
    ``GirderGraphEngine`` instance injected via :meth:`set_engine`.  No
    other bridge between this widget and the analysis layer exists.

    Lifecycle
    ---------
    1.  Instantiate the widget — no engine is required at construction time.
        The girder selector is disabled and the canvas shows a blank state.
    2.  After ``PlateGirderBridge.design()`` completes, call
        ``PlateGirderBridge.build_graph_engine(fig, axes...)`` to obtain an
        engine, then pass it to :meth:`set_engine`.
    3.  The widget auto-populates the girder combo and renders the first
        available girder immediately.

    Parameters
    ----------
    parent : QWidget, optional
        Owning Qt parent widget.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        # ── Engine reference — injected via set_engine() ──────────────────
        self._engine = None          # GirderGraphEngine; None until injected
        self._loadcase: str = ""     # active load case name

        # ── Cached plot data — empty arrays are the safe initial state ────
        self._x_data:    np.ndarray = np.array([])
        self._bmd_data:  np.ndarray = np.array([])
        self._sfd_data:  np.ndarray = np.array([])
        self._defl_data: np.ndarray = np.array([])  # empty until PENDING-1
        self._all_data:  dict       = {}
        self._reactions: dict | None = None
        self._loads:     list[dict] | None = None

        self.current_x_position: float = 0.0

        self._init_ui()

    def _init_ui(self) -> None:
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0,0,0,0)

        # Combo Box 
        def create_combo_box():
            combo = QComboBox()
            combo.setStyleSheet("""
                QComboBox {
                    border: 1px solid #CCCCCC;
                    border-radius: 4px;
                    padding: 4px 8px;
                    background-color: white;
                }
                QComboBox:hover {
                    border-color: #0078D7;
                }
                QComboBox:disabled {
                    background-color: #F0F0F0;
                    color: #A0A0A0;
                }
                QComboBox::drop-down {
                    subcontrol-origin: padding;
                    subcontrol-position: top right;
                    width: 20px;
                    border-left-width: 1px;
                    border-left-color: darkgray;
                    border-left-style: solid;
                    border-top-right-radius: 3px;
                    border-bottom-right-radius: 3px;
                }
            """)
            return combo

        top_layout = QHBoxLayout()
        top_layout.setAlignment(Qt.AlignLeft)

        lbl1 = QLabel("Girder Element:")
        font = QFont()
        font.setBold(True)
        lbl1.setFont(font)
        
        self.girder_combo = create_combo_box()
        self.girder_combo.setMinimumWidth(100)
        self.girder_combo.currentTextChanged.connect(self._on_girder_selected)
        self.girder_combo.setEnabled(False) 

        top_layout.addWidget(lbl1)
        top_layout.addWidget(self.girder_combo)
        top_layout.addSpacing(20)
        
        lbl2 = QLabel("Interaction:")
        lbl2.setFont(font)
        
        self.mode_combo = create_combo_box()
        self.mode_combo.addItems(["Scroll for Values", "Maximum Values"])
        self.mode_combo.setMinimumWidth(150)
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)

        top_layout.addWidget(lbl2)
        top_layout.addWidget(self.mode_combo)

        self.main_layout.addLayout(top_layout)

        # Plot Region
        body_layout = QHBoxLayout()
        
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.figure.patch.set_facecolor('#ffffff')
        self.canvas = FigureCanvas(self.figure)
        body_layout.addWidget(self.canvas, stretch=4)
        
        # Right Value Display
        self.val_panel = QFrame()
        self.val_panel.setFixedWidth(250)
        self.val_panel.setStyleSheet("background-color: #FAFAFA; border: 1px solid #CCCCCC; border-radius: 4px;")
        val_layout = QVBoxLayout(self.val_panel)
        val_layout.setContentsMargins(15, 15, 15, 15)

        title = QLabel("Cursor Values")
        title.setFont(font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("border: none; background: transparent; color: #333333;")
        val_layout.addWidget(title)
        
        val_layout.addSpacing(10)
        
        def create_value_box(label_str, unit_str):
            box = QFrame()
            box.setStyleSheet("border: none; background: transparent;")
            box_layout = QVBoxLayout(box)
            box_layout.setContentsMargins(0,0,0,0)
            box_layout.setSpacing(2)
            
            lbl = QLabel(label_str)
            small_font = QFont()
            small_font.setBold(True)
            lbl.setFont(small_font)
            lbl.setStyleSheet("color: #666666;")
            
            val = QLineEdit("-")
            val.setReadOnly(True)
            val.setAlignment(Qt.AlignCenter)
            val.setStyleSheet("""
                QLineEdit {
                    background-color: #E8F0FE;
                    border: 1px solid #B0C4DE;
                    border-radius: 4px;
                    padding: 4px;
                    color: #000000;
                    font-weight: bold;
                }
                QLineEdit:read-only {
                    background-color: #F8F9FA;
                }
            """)
            
            box_layout.addWidget(lbl)
            box_layout.addWidget(val)
            return box, val

        box_x, self.field_x = create_value_box("Distance from Start", "m")
        box_bmd, self.field_bmd = create_value_box("Bending Moment", "kNm")
        box_sfd, self.field_sfd = create_value_box("Shear Force", "kN")
        box_defl, self.field_defl = create_value_box("Deflection", "mm")
        
        self.field_x.setReadOnly(False)
        self.field_x.setToolTip("Enter target position and press Enter")
        self.field_x.editingFinished.connect(self._on_user_x_entered)

        # Setup fields dict
        self.fields = {
            "x": self.field_x,
            "bmd": self.field_bmd,
            "sfd": self.field_sfd,
            "defl": self.field_defl
        }
        
        # Align boxes precisely with the height ratios 1:3:3:3, hspace 0.4
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

    def _setup_axes(self) -> None:
        """
        Create the four matplotlib axes inside a 4:1 height-ratio GridSpec.

        The engine is NOT created here.  It is injected later via
        :meth:`set_engine` once the analysis dataset is available.
        """
        gs = gridspec.GridSpec(
            4, 1, figure=self.figure,
            height_ratios=[1, 3, 3, 3],
            hspace=0.4,
        )
        self.figure.subplots_adjust(left=0.15, right=0.95, top=0.92, bottom=0.10)

        self.ax_girder = self.figure.add_subplot(gs[0])
        self.ax_bmd    = self.figure.add_subplot(gs[1], sharex=self.ax_girder)
        self.ax_sfd    = self.figure.add_subplot(gs[2], sharex=self.ax_girder)
        self.ax_defl   = self.figure.add_subplot(gs[3], sharex=self.ax_girder)

        self.all_axes  = [self.ax_girder, self.ax_bmd, self.ax_sfd, self.ax_defl]
        self.plot_axes = [self.ax_bmd, self.ax_sfd, self.ax_defl]
        # Engine injected via set_engine(); canvas shows blank state until then.
        self.canvas.draw()

    def set_engine(self, engine, loadcase: str = "girder self weight") -> None:
        """
        Inject a fully initialised GirderGraphEngine and trigger the initial plot.

        Call this once after ``PlateGirderBridge.build_graph_engine()`` returns.
        The widget resets all state, re-populates the girder combo, and
        auto-renders the first available girder immediately.

        Parameters
        ----------
        engine : GirderGraphEngine
            The fully initialised engine.  Must already have a result handler
            injected; if result_handler is None on the engine,
            ``get_girder_keys()`` will return an empty list and the widget
            will display the blank state with a logged warning.
        loadcase : str
            Load case name passed to ``engine.extract_member_results()``.
            Defaults to ``"girder self weight"``.

        Notes
        -----
        It is safe to call ``set_engine()`` more than once (e.g. after a
        re-analysis).  Each call fully resets widget state before
        re-populating.
        """
        self._engine   = engine
        self._loadcase = loadcase
        self._reset_state()

        girders = self._engine.get_girder_keys()
        if not girders:
            logger.warning(
                "set_engine: engine.get_girder_keys() returned an empty list. "
                "result_handler may be uninitialised or the model contains no "
                "continuous girders.  Showing blank state."
            )
            self._engine.show_blank_state(
                self.canvas, "No girders found in model."
            )
            return

        self.girder_combo.blockSignals(True)
        self.girder_combo.clear()
        self.girder_combo.addItems(girders)
        self.girder_combo.blockSignals(False)
        self.girder_combo.setEnabled(True)

        # Auto-plot the first girder immediately — no user action required.
        self._on_girder_selected(self.girder_combo.currentText())

    def _reset_state(self) -> None:
        """
        Reset all cached plot arrays to empty and disable the girder selector.

        Called at the start of every :meth:`set_engine` call so that stale
        data from a previous analysis cannot bleed into the new render.
        """
        self._x_data    = np.array([])
        self._bmd_data  = np.array([])
        self._sfd_data  = np.array([])
        self._defl_data = np.array([])
        self._all_data  = {}
        self._reactions = None
        self._loads     = None
        self.current_x_position = 0.0

        self.girder_combo.blockSignals(True)
        self.girder_combo.clear()
        self.girder_combo.blockSignals(False)
        self.girder_combo.setEnabled(False)

    def _on_girder_selected(self, girder_name: str) -> None:
        """
        Slot — called when the user picks a different girder from the combo.

        Extracts force arrays for the selected girder and re-renders all
        diagram panels.  Silently returns if no engine is injected or the
        girder name is empty.

        Parameters
        ----------
        girder_name : str
            Girder identifier as returned by ``engine.get_girder_keys()``,
            e.g. ``"G1"`` or ``"EB1"``.
        """
        if not girder_name or self._engine is None:
            return

        res = self._engine.extract_member_results(girder_name, self._loadcase)
        if res is None:
            logger.warning(
                "_on_girder_selected: extract_member_results returned None "
                "for girder=%r, loadcase=%r.",
                girder_name, self._loadcase,
            )
            self._engine.show_blank_state(
                self.canvas, f"No data for girder {girder_name!r}."
            )
            return

        x_array, bmd_array, sfd_array, defl_array, all_data = res
        self._x_data    = np.asarray(x_array)
        self._bmd_data  = np.asarray(bmd_array)
        self._sfd_data  = np.asarray(sfd_array)
        self._defl_data = np.asarray(defl_array)
        self._all_data  = all_data
        self._reactions = self._engine.extract_reactions(self._loadcase, girder_name)
        self._loads     = self._engine.extract_loads(self._loadcase)

        self._plot_current_data()

    def _plot_current_data(self) -> None:
        """
        Clear all axes and re-render the current cached plot arrays.

        Delegates all drawing to the engine.  After rendering, updates the
        RHS value panel according to the active interaction mode.
        """
        if self._engine is None:
            return
        self._engine.clear_axes(self.canvas)
        self._engine.render_plots(
            self._x_data, self._bmd_data, self._sfd_data, self.canvas, 
            reactions=self._reactions, loads=self._loads, defl_values=self._defl_data
        )

        if self.mode_combo.currentText() == "Maximum Values":
            self._show_maximums()
        else:
            self.fields["x"].clear()
            for k in ("bmd", "sfd", "defl"):
                self.fields[k].setText("-")

    def _setup_event_handling(self) -> None:
        self.canvas.mpl_connect('button_press_event', self._on_click)
        self.canvas.setFocusPolicy(Qt.ClickFocus)
        self.canvas.mpl_connect('key_press_event', self._on_key_press)

    def move_cursor_to_x(self, x_val: float) -> None:
        """
        Move the scroll cursor to an x-position and update the RHS panel.

        Safe to call at any time — silently returns if no data is loaded.
        Clamps ``x_val`` to the available span so out-of-range inputs are
        handled gracefully.

        Parameters
        ----------
        x_val : float
            Target x-position in metres.
        """
        if self._x_data is None or len(self._x_data) == 0:
            return

        self.current_x_position = float(
            np.clip(x_val, self._x_data[0], self._x_data[-1])
        )

        m_x = float(np.interp(self.current_x_position, self._x_data, self._bmd_data))
        v_x = float(np.interp(self.current_x_position, self._x_data, self._sfd_data))

        # Deflection: only interpolate when PENDING-1 has been resolved and
        # _defl_data is populated to match _x_data length.
        d_x = (
            float(np.interp(self.current_x_position, self._x_data, self._defl_data))
            if len(self._defl_data) == len(self._x_data)
            else float("nan")
        )

        self.mode_combo.blockSignals(True)
        self.mode_combo.setCurrentText("Scroll for Values")
        self.mode_combo.blockSignals(False)

        if self._engine is not None:
            self._engine.draw_cursors(
                "Scroll for Values", self.current_x_position, self._x_data, {}, self.canvas
            )
        self._update_rhs_display(self.current_x_position, m_x, v_x, d_x)

    def _update_rhs_display(self, x: float, m: float, v: float, d: float) -> None:
        """
        Update the four read-only value fields in the RHS panel.

        Parameters
        ----------
        x : float
            Cursor x-position (m).
        m : float
            Bending moment at x (kNm).
        v : float
            Shear force at x (kN).
        d : float
            Deflection at x (mm), or ``float('nan')`` when unavailable.
        """
        self.fields["x"].setText(f"{x:.3f}")
        self.fields["bmd"].setText(f"{m:.2f} kNm")
        self.fields["sfd"].setText(f"{v:.2f} kN")
        # nan != nan is the standard float NaN check — no math import needed.
        defl_text = (
            "Unavailable"
            if d != d
            else f"{d:.2f} mm"
        )
        self.fields["defl"].setText(defl_text)

    def _on_click(self, event) -> None:
        if event.button != 1:
            return
        if event.inaxes in self.plot_axes:
            if event.xdata is not None:
                self.move_cursor_to_x(event.xdata)
                self.canvas.setFocus()

    def _on_key_press(self, event) -> None:
        if self.mode_combo.currentText() != "Scroll for Values":
            return
            
        if len(self._x_data) == 0:
            return
            
        nearest_idx = int((np.abs(self._x_data - self.current_x_position)).argmin())

        if event.key == 'right':
            next_idx = min(len(self._x_data) - 1, nearest_idx + 1)
            self.move_cursor_to_x(float(self._x_data[next_idx]))
        elif event.key == 'left':
            prev_idx = max(0, nearest_idx - 1)
            self.move_cursor_to_x(float(self._x_data[prev_idx]))

    def _on_user_x_entered(self) -> None:
        text = self.fields["x"].text()
        try:
            val = float(text)
            self.move_cursor_to_x(val)
        except ValueError:
            pass 

    def _on_mode_changed(self, mode_text: str) -> None:
        if len(self._x_data) == 0 or self._engine is None:
            return
            
        if mode_text == "Scroll for Values":
            self._engine.draw_cursors("Scroll for Values", None, self._x_data, {}, self.canvas)
            self.fields["x"].clear()
            for k in ["bmd", "sfd", "defl"]:
                self.fields[k].setText("-")
            return
            
        if mode_text == "Maximum Values":
            self._show_maximums()

    def _show_maximums(self) -> None:
        if len(self._x_data) == 0 or self._engine is None:
            return
            
        max_dict = self._engine.compute_maximums(self._x_data, self._bmd_data, self._sfd_data, self._all_data)
        
        self._engine.draw_cursors("Maximum Values", None, self._x_data, max_dict, self.canvas)
        
        x_bmd  = max_dict.get("x_M", 0.0)
        x_sfd  = max_dict.get("x_V", 0.0)
        x_defl = max_dict.get("x_D", 0.0)

        if abs(x_bmd - x_sfd) < 1e-4:
            self.fields["x"].setText(f"{x_bmd:.2f}")
        else:
            self.fields["x"].setText("Multiple")

        self.fields["bmd"].setText(f"max = {max_dict.get('M_max', 0.0):.2f} kNm at x = {x_bmd:.2f} m")
        self.fields["sfd"].setText(f"max = {max_dict.get('V_max', 0.0):.2f} kN at x = {x_sfd:.2f} m")
        
        if "D_max" in max_dict:
            self.fields["defl"].setText(f"max = {max_dict.get('D_max', 0.0):.2f} mm at x = {x_defl:.2f} m")
        else:
            self.fields["defl"].setText("Unavailable")
        
        self.canvas.draw_idle()
