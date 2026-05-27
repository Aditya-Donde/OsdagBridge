import matplotlib
matplotlib.use("QtAgg")

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Path3DCollection 

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QSizePolicy, QPushButton,
    QFrame, QLabel, QCheckBox, QScrollArea, QApplication, QLineEdit 
)
from PySide6.QtCore import Qt, QEvent, QTimer

# ══════════════════════════════════════════════
# ADDED: QDoubleValidator for scale input validation
# ══════════════════════════════════════════════
from PySide6.QtGui import QDoubleValidator

from navcube import NavCubeOverlay, NavCubeStyle
from osdagbridge.desktop.ui.utils.mpl_widget_navcube_sync import MatplotlibNavCubeSync

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


# =============================================================================
# PROFESSIONAL SUMMARY OVERLAY WIDGET (HTML/RichText based)
# =============================================================================
class SummaryOverlay(QFrame):
    """A floating HUD that sits on top of the Matplotlib canvas."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            SummaryOverlay {
                background-color: rgba(33, 37, 43, 215);
                border: 1px solid rgba(255, 255, 255, 50);
                border-radius: 6px;
            }
            QLabel {
                color: white;
                font-size: 13px;
                font-family: Consolas, 'Courier New', monospace;
                padding: 12px;
                background: transparent;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.text_label = QLabel()
        self.text_label.setTextFormat(Qt.RichText)
        self.text_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        layout.addWidget(self.text_label)

    def update_data(self, summary_data):
        hud_text = "<b>Extreme Values Summary</b><br>" + "-" * 38 + "<br>"
        
        h_girder = "Girder".ljust(8).replace(" ", "&nbsp;")
        h_max = "Max".rjust(10).replace(" ", "&nbsp;")
        h_min = "Min".rjust(12).replace(" ", "&nbsp;")
        
        hud_text += f"<b>{h_girder}</b> | <span style='color: #FF4136;'><b>{h_max}</b></span> | <span style='color: #00E5FF;'><b>{h_min}</b></span><br>" + "-" * 38 + "<br>"

        for girder, vals in summary_data.items():
            g_str = girder.ljust(8).replace(" ", "&nbsp;")
            max_str = f"{vals['max']:.2f}".rjust(10).replace(" ", "&nbsp;")
            min_str = f"{vals['min']:.2f}".rjust(12).replace(" ", "&nbsp;")
            
            hud_text += f"<b>{g_str}</b> | <span style='color: #FF4136;'>{max_str}</span> | <span style='color: #00E5FF;'>{min_str}</span><br>"

        self.text_label.setText(hud_text)
        self.adjustSize()


# =============================================================================
# MAIN PLOT WIDGET
# =============================================================================
class MplPlotWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Data populated by setup()
        self._ds_all    = None
        self._loadcases = []
        self._nodes     = {}
        self._members   = {}
        self._edge_dist = 0.0
        self._output_dock = None
        self._summary_data = {}

        # Display States
        self._grillage_mode = False
        self._show_nodes = True 
        self._show_axis = False 
        self._show_supports = True 
        self._show_grid = False  
        self._is_summary_checked = False
        self._show_max = False  
        self._show_min = False  
        self._show_all_vals = False 
        self._show_girder_labels = False

        # Zoom state
        self._zoom_scale  = 1.0
        
        # ══════════════════════════════════════════════
        # ADDED: Default orientation tracking for rotate + reset
        # ══════════════════════════════════════════════
        self._default_elev = 30.0
        self._default_azim = -60.0
        self._current_azim = -60.0
        
        self._orig_limits = None   
        
        # ══════════════════════════════════════════════
        # Interaction mode state for view-control buttons
        # ══════════════════════════════════════════════
        self._pan_active         = False
        self._zoom_window_active = False
        self._pan_start          = None  # pixel (x,y) on press
        self._zoom_rect_start    = None  # data coords for rubber-band
        self._zoom_rect_patch    = None  # Rectangle drawn on canvas
        self._cid_press          = None  # mpl event ids – disconnected when mode off
        self._cid_release        = None
        self._cid_motion         = None
        

        # matplotlib canvas
        self._fig    = plt.figure(figsize=(14, 6), facecolor="white")
        self._canvas = FigureCanvasQTAgg(self._fig)
        self._canvas.setMinimumHeight(300)
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._canvas.installEventFilter(self)

        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setWidget(self._canvas)
        self._scroll_area.setFrameShape(QFrame.NoFrame)

        # Initialize the Summary Overlay
        self._summary_overlay = SummaryOverlay(self._canvas)
        self._summary_overlay.hide()

        # ── NavCube: create overlay + sync bridge ──────────────────
        self._navcube = NavCubeOverlay(self._canvas, overlay=False, style=NavCubeStyle(
            size=65, theme="light",
            face_color=(242, 244, 247), edge_color=(218, 224, 232),
            corner_color=(228, 232, 238), text_color=(45, 55, 72),
            border_color=(30, 30, 30), border_secondary_color=(80, 80, 80),
            border_width_main=1.6, border_width_secondary=0.9,
            hover_color=(145, 176, 20, 235), hover_text_color=(255, 255, 255),
            dot_color=(60, 60, 60, 180), shadow_color=(20, 20, 20, 45),
            shadow_offset_x=2.0, shadow_offset_y=2.5,
            face_color_dark=(52, 62, 76), edge_color_dark=(42, 52, 65),
            corner_color_dark=(47, 57, 70), text_color_dark=(210, 220, 232),
            border_color_dark=(200, 200, 200), border_secondary_color_dark=(130, 130, 130),
            hover_color_dark=(145, 176, 20, 235),
            show_gizmo=False, inactive_opacity=0.70, animation_ms=300,
            light_direction=(-0.5, -1.0, -1.5),
        ))
        self._navcube.hide()
        self._navcube_sync = MatplotlibNavCubeSync(self._canvas, self._navcube)


        self._canvas.mpl_connect("button_press_event",   lambda e: self._navcube_sync.set_interaction_active(True)  if e.button == 1 and not self._any_mode_active() else None)
        self._canvas.mpl_connect("button_release_event", lambda e: self._navcube_sync.set_interaction_active(False) if e.button == 1 and not self._any_mode_active() else None)
        self._canvas.mpl_connect("motion_notify_event",  lambda e: self._navcube_sync.force_sync() if e.button == 1 and not self._any_mode_active() else None)


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
        self._btn_zoom_in.clicked.connect(self._zoom_in)
        self._btn_zoom_out.clicked.connect(self._zoom_out)
        self._btn_zoom_reset.clicked.connect(self._zoom_reset)

        # TOOBAR BUTTONS
        btn_style = (
            "QPushButton { font-size: 12px; border: 1px solid #bbb; border-radius: 4px;"
            " background: #f5f5f5; padding: 0 8px; }"
            "QPushButton:hover { background: #e0e0e0; }"
            "QPushButton:pressed { background: #bdbdbd; }"
            "QPushButton:checked { background: #1565C0; color: white;"
            " border: 1px solid #0D47A1; }"
        )

        self._btn_grillage = QPushButton("Grillage")
        self._btn_grillage.setCheckable(True)
        self._btn_grillage.setFixedHeight(28)
        self._btn_grillage.setFocusPolicy(Qt.NoFocus)
        self._btn_grillage.setStyleSheet(btn_style)
        self._btn_grillage.toggled.connect(self._on_grillage_toggled)

        self._btn_nodes = QPushButton("Nodes")
        self._btn_nodes.setCheckable(True)
        self._btn_nodes.setChecked(True) 
        self._btn_nodes.setFixedHeight(28)
        self._btn_nodes.setFocusPolicy(Qt.NoFocus)
        self._btn_nodes.setStyleSheet(btn_style)
        self._btn_nodes.toggled.connect(self._on_nodes_toggled)

        self._btn_supports = QPushButton("Supports")
        self._btn_supports.setCheckable(True)
        self._btn_supports.setChecked(True) 
        self._btn_supports.setFixedHeight(28)
        self._btn_supports.setFocusPolicy(Qt.NoFocus)
        self._btn_supports.setStyleSheet(btn_style)
        self._btn_supports.toggled.connect(self._on_supports_toggled)

        self._btn_axis = QPushButton("Axis")
        self._btn_axis.setCheckable(True)
        self._btn_axis.setChecked(False) 
        self._btn_axis.setFixedHeight(28)
        self._btn_axis.setFocusPolicy(Qt.NoFocus)
        self._btn_axis.setStyleSheet(btn_style)
        self._btn_axis.toggled.connect(self._on_axis_toggled)

        self._btn_grid = QPushButton("Grid")
        self._btn_grid.setCheckable(True)
        self._btn_grid.setChecked(False) 
        self._btn_grid.setFixedHeight(28)
        self._btn_grid.setFocusPolicy(Qt.NoFocus)
        self._btn_grid.setStyleSheet(btn_style)
        self._btn_grid.toggled.connect(self._on_grid_toggled)
        # self._canvas.mpl_connect('scroll_event', self._on_scroll)

        # ══════════════════════════════════════════════
        # View-control buttons
        # ══════════════════════════════════════════════
        self._btn_zoom_fit    = QPushButton("Zoom Fit")
        self._btn_zoom_window = QPushButton("Zoom Window")
        self._btn_pan         = QPushButton("Pan")
        self._btn_rotate      = QPushButton("Rotate")
        self._btn_girder_labels = QPushButton("Girder Labels")

    
        # ══════════════════════════════════════════════
        # View-control button styles and connections
        # Zoom Window / Pan are exclusive toggles
        # Rotate is a plain click (45° per click)
        # ══════════════════════════════════════════════
        for btn in (self._btn_zoom_fit, self._btn_zoom_window,
            self._btn_pan, self._btn_rotate, self._btn_girder_labels):            
            btn.setFixedHeight(28)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.setStyleSheet(btn_style)

        
        self._btn_zoom_window.setCheckable(True)
        self._btn_pan.setCheckable(True)
        self._btn_girder_labels.setCheckable(True)
        

        self._btn_zoom_fit.clicked.connect(self._on_zoom_fit)
        self._btn_zoom_window.toggled.connect(self._on_zoom_window_toggled)
        self._btn_pan.toggled.connect(self._on_pan_toggled)
        self._btn_rotate.clicked.connect(self._on_rotate_click)
       
        self._btn_girder_labels.toggled.connect(self._on_girder_labels_toggled)

        
        # ══════════════════════════════════════════════
        # ADDED | Scale spinbox setup
        # Default: 100, Range: 1–10000
        # Replaces old plain Scale button with spinbox + arrow controls
        # ══════════════════════════════════════════════
        self._scale_value = 100.0

        _spin_btn_style = (
            "QPushButton { font-size: 9px; border: 1px solid #bbb; background: #f5f5f5;"
            " padding: 0; min-width: 16px; max-width: 16px; }"
            "QPushButton:hover { background: #e0e0e0; }"
            "QPushButton:pressed { background: #bdbdbd; }"
        )
        _input_style = (
            "QLineEdit { font-size: 11px; border: 1px solid #bbb; border-radius: 2px;"
            " background: #fff; padding: 0 2px; }"
        )

        scale_label = QLabel("Scale")
        scale_label.setStyleSheet("QLabel { font-size: 12px; color: #333; }")
        scale_label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)

        self._scale_input = QLineEdit(f"{self._scale_value:.0f}")
        self._scale_input.setFixedSize(52, 28)
        self._scale_input.setAlignment(Qt.AlignCenter)
        self._scale_input.setValidator(QDoubleValidator(1.0, 10000.0, 0, self._scale_input))
        self._scale_input.setStyleSheet(_input_style)
        self._scale_input.setFocusPolicy(Qt.ClickFocus)
        self._scale_input.editingFinished.connect(self._on_scale_input_edited)

        self._btn_scale_up   = QPushButton("▲")
        self._btn_scale_down = QPushButton("▼")
        for b in (self._btn_scale_up, self._btn_scale_down):
            b.setFixedSize(16, 14)
            b.setFocusPolicy(Qt.NoFocus)
            b.setStyleSheet(_spin_btn_style)

        self._scale_timer = QTimer(self)
        self._scale_timer.setInterval(80)
        self._scale_direction = 0

        self._btn_scale_up.pressed.connect(lambda: self._start_scale_change(+1))
        self._btn_scale_up.released.connect(self._stop_scale_change)
        self._btn_scale_down.pressed.connect(lambda: self._start_scale_change(-1))
        self._btn_scale_down.released.connect(self._stop_scale_change)
        self._scale_timer.timeout.connect(self._tick_scale_change)

        arrow_col = QVBoxLayout()
        arrow_col.setContentsMargins(0, 0, 0, 0)
        arrow_col.setSpacing(0)
        arrow_col.addWidget(self._btn_scale_up)
        arrow_col.addWidget(self._btn_scale_down)

        self._scale_widget = QFrame()
        self._scale_widget.setFixedHeight(28)
        scale_inner = QHBoxLayout(self._scale_widget)
        scale_inner.setContentsMargins(0, 0, 0, 0)
        scale_inner.setSpacing(2)
        scale_inner.addWidget(scale_label)
        scale_inner.addWidget(self._scale_input)
        scale_inner.addLayout(arrow_col)
        # ══════════════════════════════════════════════
    

        # ══════════════════════════════════════════════
        # MODIFIED | Toolbar split into two rows
        # Row 1: display toggles + zoom controls + scale (right-aligned)
        # Row 2: view-control buttons (fit, window, pan, rotate)
        # ══════════════════════════════════════════════

        # ── Row 1: original display-toggle buttons (UNCHANGED) ─────
        toolbar_row = QHBoxLayout()
        toolbar_row.setContentsMargins(4, 2, 4, 2)
        toolbar_row.setSpacing(4)
        toolbar_row.addWidget(self._btn_grillage)
        toolbar_row.addWidget(self._btn_nodes)
        toolbar_row.addWidget(self._btn_supports) 
        toolbar_row.addWidget(self._btn_axis) 
        toolbar_row.addWidget(self._btn_grid) 
        toolbar_row.addStretch()
        toolbar_row.addWidget(self._btn_zoom_out)
        toolbar_row.addWidget(self._btn_zoom_in)
        toolbar_row.addWidget(self._btn_zoom_reset)
        toolbar_row.addWidget(self._scale_widget)


        
        # ── Row 2: new view-control buttons ────────────────────────
        toolbar_row2 = QHBoxLayout()
        toolbar_row2.setContentsMargins(4, 2, 4, 2)
        toolbar_row2.setSpacing(4)
        toolbar_row2.addWidget(self._btn_zoom_fit)
        toolbar_row2.addWidget(self._btn_zoom_window)
        toolbar_row2.addWidget(self._btn_pan)
        toolbar_row2.addWidget(self._btn_rotate)
        toolbar_row2.addWidget(self._btn_girder_labels)
        toolbar_row2.addStretch()

        # layout
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addLayout(toolbar_row)
        root.addLayout(toolbar_row2)   # second row added here
        root.addWidget(self._scroll_area, stretch=1)
        # END CHANGE 4-----------------------------------------------------------------------------

    # public API

    def setup(self, ds_all, loadcases: list, nodes: dict, members: dict,
              edge_dist: float = 0.0):
        self._ds_all    = ds_all
        self._loadcases = list(loadcases)
        self._nodes     = nodes
        self._members   = members
        self._edge_dist = edge_dist

        if hasattr(self, '_fig') and self._fig.axes:
            ax = self._fig.axes[0]
            
            # 1. Switch to Orthographic projection (NO MORE CLIPPING)
            # ax.set_proj_type('ortho')
            
            # 2. Force the 3D box to stretch across the entire PySide6 widget
            # We use slight negative values to push the invisible bounding box 
            # off the edges of the screen, maximizing the bridge resolution.
            self._fig.subplots_adjust(left=-0.05, right=1.05, bottom=-0.05, top=1.05)

    def link_output_dock(self, output_dock):
        self._output_dock = output_dock

        # 1. Connect Load Combinations
        combo_lc = output_dock.output_widget.findChild(QComboBox, "analysis.load_combination")
        if combo_lc is not None:
            combo_lc.blockSignals(True)
            combo_lc.clear()
            combo_lc.addItems(self._loadcases)
            combo_lc.blockSignals(False)
            combo_lc.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            combo_lc.setMinimumContentsLength(12)
            combo_lc.currentTextChanged.connect(self.update_plot)

        # 2. Connect Force Radios
        from osdagbridge.desktop.ui.utils.custom_widgets import CustomRadioButton
        force_rbs = [
            rb for rb in output_dock.output_widget.findChildren(CustomRadioButton)
            if rb.text() in _RICH_LABEL_TO_FORCE
        ]
        for rb in force_rbs:
            rb.setChecked(rb.text() == _DEFAULT_FORCE_LABEL)
            rb.toggled.connect(self.update_plot)

        # Create placeholders to store the checkboxes
        self._cb_max = None
        self._cb_min = None

        for cb in output_dock.output_widget.findChildren(QCheckBox):
            text = cb.text().strip().lower()
            if "summary" in text:
                cb.toggled.connect(self._on_summary_toggled)
                self._is_summary_checked = cb.isChecked()
            elif "max" in text:
                self._cb_max = cb  # Store the reference
                cb.toggled.connect(self._on_max_toggled)
                self._show_max = cb.isChecked()
            elif "min" in text:
                self._cb_min = cb  # Store the reference
                cb.toggled.connect(self._on_min_toggled)
                self._show_min = cb.isChecked()
            elif "all" in text:
                cb.toggled.connect(self._on_all_vals_toggled)
                self._show_all_vals = cb.isChecked()

        self.update_plot()

    def update_plot(self, *_args):
        if self._grillage_mode:
            return

        if self._ds_all is None or self._output_dock is None:
            return
        
        # ══════════════════════════════════════════════
        # ADDED | Reset scale to default on plot switch
        # ══════════════════════════════════════════════
        self._scale_value = 100.0
        self._scale_input.setText("100")
        self._apply_scale_value() 
        
        loadcase  = self._current_loadcase()
        force_key = self._current_force_key()

        if not loadcase or not force_key:
            return

        ds = self._ds_all.sel(Loadcase=loadcase)
        
        # ==========================================
        # 1. 🚨 CAPTURE CAMERA STATE BEFORE CLOSING
        # ==========================================
        old_elev, old_azim = None, None
        if hasattr(self, '_fig') and self._fig and self._fig.axes:
            old_ax = self._fig.axes[0]
            if hasattr(old_ax, 'elev'):
                old_elev = old_ax.elev
                old_azim = old_ax.azim

        # NOW we can safely destroy the old plot
        plt.close(self._fig)
        
        self._summary_data = {} 

        # (Your existing if/elif/else block to build the new figures)
        if force_key in _SFD_KEYS:
            self._fig, self._summary_data = build_figure_sfd(ds, force_key, self._nodes, self._members, edge_dist=self._edge_dist)
        elif force_key in _DEFL_KEYS:
            self._fig, self._summary_data = build_figure_deflection(ds, force_key, self._nodes, self._members, edge_dist=self._edge_dist)
        else:
            self._fig, self._summary_data = build_figure_bmd(ds, force_key, self._nodes, self._members, edge_dist=self._edge_dist)

        self._canvas.figure = self._fig
        self._fig.set_canvas(self._canvas)
        # Ensure the figure size matches the current canvas (DPI-aware)
        QTimer.singleShot(0, self._fit_figure_to_canvas)
        
        # (Your existing visibility toggles)
        self._apply_node_visibility()
        self._apply_axis_visibility()
        self._apply_supports_visibility()
        self._apply_grid_visibility() 
        self._apply_annotation_visibility() 
        self._apply_girder_label_visibility()
        
        # (Your existing HUD logic)
        if self._summary_data:
            self._summary_overlay.update_data(self._summary_data)
            if self._is_summary_checked:
                self._summary_overlay.show()
                self._summary_overlay.raise_()
        else:
            self._summary_overlay.hide()

        # (Your existing HUD logic)
        # if self._summary_data:
        #     self._summary_overlay.update_data(self._summary_data)
        # else:
        #     self._summary_overlay.hide()
        
        if self._fig:
            self._fig.subplots_adjust(left=0.02, right=0.98, bottom=0.02, top=0.92)
            
            if not self._fig.axes:
                return

            ax = self._fig.axes[0]

            # ==========================================
            # 2. 🚨 RESTORE CAMERA STATE TO NEW PLOT
            # ==========================================
            if old_elev is not None and old_azim is not None:
                ax.view_init(elev=old_elev, azim=old_azim)

            # (Keep your existing native zoom logic)
            # if hasattr(ax, 'set_box_aspect'):
            #     ax.set_box_aspect(aspect=(2.5, 1.2, 1.0), zoom=self._zoom_scale)

            # ══════════════════════════════════════════════
            # MODIFIED | 3D box aspect + zoom window persistence on plot rebuild
            # Resets zoom if zoom window active; reconnects events so
            # zoom window works without re-toggling after plot switch
            # ══════════════════════════════════════════════
            if hasattr(ax, 'set_box_aspect'):
                # Reset zoom scale when plot rebuilds so the new graph
                # always starts at default view, even if Zoom Window is active
                if self._zoom_window_active:
                    self._zoom_scale = 1.0
                ax.set_box_aspect(aspect=(2.5, 1.2, 1.0), zoom=self._zoom_scale)

            # If Zoom Window mode is active, reconnect events and disable
            # rotation on the new axis so it works without re-toggling
            if self._zoom_window_active:
                if hasattr(ax, 'disable_mouse_rotation'):
                    ax.disable_mouse_rotation()
                self._disconnect_canvas_events()
                self._cid_press   = self._canvas.mpl_connect("button_press_event",   self._zw_on_press)
                self._cid_motion  = self._canvas.mpl_connect("motion_notify_event",  self._zw_on_motion)
                self._cid_release = self._canvas.mpl_connect("button_release_event", self._zw_on_release)   
            # ══════════════════════════════════════════════ 

            # (Keep your existing anti-clipping loop here)
            for line in ax.lines:
                line.set_clip_on(False)
            for collection in ax.collections:
                collection.set_clip_on(False)
            for text in ax.texts:
                text.set_clip_on(False)

             # ── Load case subtitle ────────────────────────────────────
            for txt in self._fig.texts[:]:
                if getattr(txt, "_lc_subtitle", False):
                    txt.remove()

            if loadcase:
                subtitle = self._fig.text(
                    0.5, 0.910,
                    f"Load Combination:  {loadcase}",
                    ha="center", va="top",
                    fontsize=11, fontweight="bold",
                    color="#000000",
                    transform=self._fig.transFigure,
                )
                subtitle._lc_subtitle = True
            # ── End load case subtitle ────────────────────────────────

            self._canvas.draw_idle()

            # # Defer show()/raise_() to AFTER draw_idle() so the renderer
            # # buffer is populated before Qt processes the canvas repaint.
            # if self._summary_data and self._is_summary_checked:
            #     self._summary_overlay.show()
            #     self._summary_overlay.raise_()


        # Show NavCube for 3-D plots only, hide for 2-D.
        QTimer.singleShot(100, self._update_navcube_visibility)

    # ── NavCube helpers ────────────────────────────────────────────

    def _update_navcube_visibility(self):
        from mpl_toolkits.mplot3d import Axes3D
        has_3d = any(isinstance(ax, Axes3D) for ax in self._fig.axes)
        if has_3d:
            self._resize_navcube()
            self._position_navcube()
            self._navcube.mark_ready()
            self._navcube.show()
            self._navcube.raise_()
            self._navcube_sync.force_sync()
        else:
            self._navcube.hide()

    def _resize_navcube(self):
        """Scale NavCube to 8% of the shorter canvas edge, DPI-aware. (mirrors CustomViewer3d)"""
        vp_logical = min(self._canvas.width(), self._canvas.height())
        if vp_logical < 10:
            return
        nc = self._navcube
        app = QApplication.instance()
        screen = nc.screen() if nc.isVisible() else None
        if screen is None and app:
            screen = app.primaryScreen()
        dpr          = max(1.0, screen.devicePixelRatio())  if screen else 1.0
        physical_dpi = max(72.0, min(screen.physicalDotsPerInch(), 400.0)) if screen else 96.0
        vp_physical  = vp_logical * dpr
        ref_size    = max(40, min(round(vp_physical * 0.08 * 96.0 / physical_dpi), 90))
        ref_padding = round(10 * 96.0 / physical_dpi)
        ref_scale   = round(25.0 * ref_size / 100.0, 2)
        if (nc._style.size == ref_size and nc._style.padding == ref_padding
                and abs(nc._style.scale - ref_scale) < 0.05):
            return
        nc._style.size    = ref_size
        nc._style.padding = ref_padding
        nc._style.scale   = ref_scale
        nc._update_dpi()

    def _position_navcube(self):
        padding = 10
        x = max(0, self._canvas.width() - self._navcube.width() - padding)
        self._navcube.move(x, padding)

    def eventFilter(self, obj, event):
        if obj is self._canvas and event.type() == QEvent.Type.Resize:
            self._resize_navcube()
            self._position_navcube()
            if self._navcube.isVisible():
                self._navcube.raise_()
        return super().eventFilter(obj, event)

    # ──────────────────────────────────────────────────────────────

    # NATIVE SLOTS: The 'checked' variable is now passed instantly by Qt!
    def _on_summary_toggled(self, checked):
        self._is_summary_checked = checked
        if self._is_summary_checked and self._summary_data:
            self._summary_overlay.show()
            self._summary_overlay.raise_()
        else:
            self._summary_overlay.hide()

    def _on_max_toggled(self, checked):
        self._show_max = checked
        self._apply_annotation_visibility()
        self._canvas.draw_idle()

    def _on_min_toggled(self, checked):
        self._show_min = checked
        self._apply_annotation_visibility()
        self._canvas.draw_idle()

    def _on_all_vals_toggled(self, checked):
        self._show_all_vals = checked
        
        # Disable the Max and Min checkboxes when "All" is active
        if self._cb_max:
            self._cb_max.setEnabled(not checked)
        if self._cb_min:
            self._cb_min.setEnabled(not checked)
            
        self._apply_annotation_visibility()
        self._canvas.draw_idle()

    # Toolbar Slots
    def _on_grillage_toggled(self, checked: bool):
        self._grillage_mode = checked
        if checked:
            if not self._nodes: return
            plt.close(self._fig)
            self._fig = build_figure_grillage(self._nodes, self._members, edge_dist=self._edge_dist)
            self._canvas.figure = self._fig
            self._fig.set_canvas(self._canvas)
            
            self._apply_node_visibility()
            self._apply_axis_visibility()
            self._apply_supports_visibility()
            self._apply_grid_visibility()
            self._apply_girder_label_visibility()
            self._summary_overlay.hide() 
            
            self._fit_figure_to_canvas()
            self._canvas.draw()
            self._zoom_scale = 1.0
            self._store_orig_limits()
            QTimer.singleShot(100, self._update_navcube_visibility)
        else:
            self.update_plot()

    def _on_nodes_toggled(self, checked: bool):
        self._show_nodes = checked
        self._apply_node_visibility()
        self._canvas.draw_idle() 

    def _on_axis_toggled(self, checked: bool):
        self._show_axis = checked
        self._apply_axis_visibility()
        self._canvas.draw_idle()

    def _on_supports_toggled(self, checked: bool):
        self._show_supports = checked
        self._apply_supports_visibility()
        self._canvas.draw_idle()

    def _on_grid_toggled(self, checked: bool):
        self._show_grid = checked
        self._apply_grid_visibility()
        self._canvas.draw_idle()

    def _on_girder_labels_toggled(self, checked: bool):
        self._show_girder_labels = checked
        self._apply_girder_label_visibility()
        self._canvas.draw_idle()

    def _apply_girder_label_visibility(self):
        """Show or hide all text artists tagged with gid='girder_label'."""
        for ax in self._fig.axes:
            for text in ax.texts:
                if text.get_gid() == "girder_label":
                    text.set_visible(self._show_girder_labels)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._summary_overlay:
            self._summary_overlay.move(15, 45) # Keep HUD floating safely under the toolbar
        # Debounced resize: adjust Matplotlib figure to match the canvas size
        QTimer.singleShot(150, self._on_delayed_resize)

    # private helpers
    def _apply_node_visibility(self):
        for ax in self._fig.axes:
            for collection in ax.collections:
                if isinstance(collection, Path3DCollection):
                    if collection.get_gid() != "supports":
                        collection.set_visible(self._show_nodes)

    def _apply_supports_visibility(self):
        for ax in self._fig.axes:
            for collection in ax.collections:
                if collection.get_gid() == "supports":
                    collection.set_visible(self._show_supports)

    def _apply_axis_visibility(self):
        for ax in self._fig.axes:
            for collection in ax.collections:
                if collection.get_gid() == "coord_triad":
                    collection.set_visible(self._show_axis)
            
            for line in ax.lines:
                if line.get_gid() == "coord_triad":
                    line.set_visible(self._show_axis)

            for text in ax.texts:
                if text.get_gid() == "coord_triad":
                    text.set_visible(self._show_axis)

    def _apply_annotation_visibility(self):
        for ax in self._fig.axes:
            for line in ax.lines:
                if line.get_gid() == "max_line": 
                    line.set_visible(self._show_max or self._show_all_vals)
                elif line.get_gid() == "min_line": 
                    line.set_visible(self._show_min or self._show_all_vals)
            for text in ax.texts:
                if text.get_gid() == "max_line": 
                    text.set_visible(self._show_max or self._show_all_vals)
                elif text.get_gid() == "min_line": 
                    text.set_visible(self._show_min or self._show_all_vals)
                elif text.get_gid() == "all_vals": 
                    text.set_visible(self._show_all_vals)


    
    # ══════════════════════════════════════════════
    # ADDED | Grid visibility with 3D zoom correction
    # ══════════════════════════════════════════════
    def _apply_grid_visibility(self):
        for ax in self._fig.axes:
            if self._show_grid:
                ax.set_axis_on()
                ax.grid(True, linestyle="--", linewidth=0.4, alpha=0.5)
                if hasattr(ax, 'set_box_aspect'):
                    ax.set_box_aspect(aspect=(2.5, 1.2, 1.0), zoom=self._zoom_scale * 0.82)
            else:
                ax.set_axis_off()
                if hasattr(ax, 'set_box_aspect'):
                    ax.set_box_aspect(aspect=(2.5, 1.2, 1.0), zoom=self._zoom_scale)
    # ══════════════════════════════════════════════                


    def _fit_figure_to_canvas(self):
        # Resize the Matplotlib Figure to match the widget canvas in physical pixels
        if not hasattr(self, '_fig') or not self._fig:
            return
        w_px = self._canvas.width()
        h_px = self._canvas.height()
        if w_px > 10 and h_px > 10:
            # Prefer the canvas/device DPR when available to support HiDPI displays
            try:
                dpr = float(self._canvas.devicePixelRatioF())
            except Exception:
                app = QApplication.instance()
                screen = app.primaryScreen() if app else None
                dpr = float(screen.devicePixelRatio()) if screen else 1.0

            physical_w = max(1, int(w_px * dpr))
            physical_h = max(1, int(h_px * dpr))
            dpi = float(getattr(self._fig, 'dpi', 100.0))
            # Apply new size in inches and forward the change so Matplotlib updates internals
            self._fig.set_size_inches(physical_w / dpi, physical_h / dpi, forward=True)

    def _on_delayed_resize(self):
        # Called via QTimer.singleShot to avoid rapid redraws while resizing
        try:
            self._fit_figure_to_canvas()
            if hasattr(self, '_canvas') and self._canvas:
                self._canvas.draw_idle()
        except Exception:
            pass

    def _store_orig_limits(self):
        pass # Not needed for Uniform Render Zoom


    # ══════════════════════════════════════════════
    # ADDED | View-control button handlers
    # ══════════════════════════════════════════════

    def _any_mode_active(self):
        """Returns True when any exclusive mode (Pan/Rotate/ZoomWindow) is on."""
        # return self._pan_active or self._rotate_active or self._zoom_window_active
        return self._pan_active or self._zoom_window_active


    def _deactivate_all_modes(self, except_btn=None):
        """Uncheck all exclusive toggle buttons and disconnect canvas events."""
        # for btn in (self._btn_zoom_window, self._btn_pan, self._btn_rotate):
        for btn in (self._btn_zoom_window, self._btn_pan):
            if btn is not except_btn and btn.isChecked():
                btn.blockSignals(True)
                btn.setChecked(False)
                btn.blockSignals(False)
        self._pan_active         = False
        self._rotate_active      = False
        self._zoom_window_active = False
        self._disconnect_canvas_events()
        # Re-enable matplotlib's built-in 3D rotation now that no exclusive
        # mode is active
        if self._fig and self._fig.axes:
            ax = self._fig.axes[0]
            if hasattr(ax, 'mouse_init'):
                ax.mouse_init()   



    def _disconnect_canvas_events(self):
        """Safely disconnect the three per-mode mpl event callbacks."""
        for cid in (self._cid_press, self._cid_release, self._cid_motion):
            if cid is not None:
                try:
                    self._canvas.mpl_disconnect(cid)
                except Exception:
                    pass
        self._cid_press = self._cid_release = self._cid_motion = None
        # Remove zoom-window rubber-band rect if still on canvas
        if self._zoom_rect_patch is not None:
            try:
                self._zoom_rect_patch.remove()
            except Exception:
                pass
            self._zoom_rect_patch = None
            self._canvas.draw_idle()

    # ── Zoom Fit ──────────────────────────────────────────────────────────────
    def _on_zoom_fit(self):
        """Reset zoom to 1.0 and restore auto-scale limits."""
        self._deactivate_all_modes()
        self._zoom_scale = 1.0
        self._scale_value = 100.0                    
        self._scale_input.setText("100")             

        if not self._fig or not self._fig.axes:
            return
        ax = self._fig.axes[0]
        if hasattr(ax, 'set_box_aspect'):   # 3-D axis
            fit_zoom = 0.82 if self._show_grid else 1.0
            ax.set_box_aspect(aspect=(2.5, 1.2, 1.0), zoom=fit_zoom)
            ax.autoscale()
        else: 
            ax.set_aspect('auto')        #added line                      # 2-D axis
            ax.relim()
            ax.autoscale_view()

        self._scroll_area.setWidgetResizable(True)
        self._canvas.setMinimumSize(0, 0)
        self._canvas.setMaximumSize(16777215, 16777215)
        self._canvas.draw_idle()


    # # ── Zoom Window ───────────────────────────────────────────────────────────

    def _on_zoom_window_toggled(self, checked: bool):
        """Enable rubber-band rectangle zoom on the plot."""
        if checked:
            self._deactivate_all_modes(except_btn=self._btn_zoom_window)
            self._zoom_window_active = True
            # Disable matplotlib's built-in 3D rotation/pan so it doesn't
            # fight the rubber-band drag
            if self._fig and self._fig.axes:
                ax = self._fig.axes[0]
                if hasattr(ax, 'mouse_init'):
                    ax.disable_mouse_rotation()
            self._cid_press   = self._canvas.mpl_connect("button_press_event",   self._zw_on_press)
            self._cid_motion  = self._canvas.mpl_connect("motion_notify_event",  self._zw_on_motion)
            self._cid_release = self._canvas.mpl_connect("button_release_event", self._zw_on_release)
        else:
            self._zoom_window_active = False
            self._deactivate_all_modes()


    def _zw_on_press(self, event):
        if event.button == 1:
            # Use pixel coords — works reliably on both 2D and 3D axes
            self._zoom_rect_start = (event.x, event.y)

    def _zw_on_motion(self, event):
        if self._zoom_rect_start is None or event.button != 1:
            return
        x0_px, y0_px = self._zoom_rect_start
        x1_px, y1_px = event.x, event.y

        # Convert pixel coords to axes fraction for the Rectangle overlay
        fig_w = self._fig.get_figwidth()  * self._fig.dpi
        fig_h = self._fig.get_figheight() * self._fig.dpi

        # Remove old rubber-band
        if self._zoom_rect_patch is not None:
            try:
                self._zoom_rect_patch.remove()
            except Exception:
                pass

        from matplotlib.patches import Rectangle
        # Draw in figure-pixel coords using a figure-level axes (transFigure)
        ax = self._fig.axes[0]
        # Convert mpl pixel (origin bottom-left) → axes display fraction
        x0_f = min(x0_px, x1_px) / fig_w
        y0_f = min(y0_px, y1_px) / fig_h
        w_f  = abs(x1_px - x0_px) / fig_w
        h_f  = abs(y1_px - y0_px) / fig_h

        self._zoom_rect_patch = Rectangle(
            (x0_f, y0_f), w_f, h_f,
            linewidth=1.4, edgecolor="#1565C0", facecolor="#1565C0",
            alpha=0.15, zorder=10,
            transform=self._fig.transFigure
        )
        self._fig.add_artist(self._zoom_rect_patch)
        self._canvas.draw_idle()

    # def _zw_on_release(self, event):
    #     if self._zoom_rect_start is None or event.button != 1:
    #         return
    #     x0_px, y0_px = self._zoom_rect_start
    #     self._zoom_rect_start = None

    #     # Remove rubber-band rect
    #     if self._zoom_rect_patch is not None:
    #         try:
    #             self._zoom_rect_patch.remove()
    #         except Exception:
    #             pass
    #         self._zoom_rect_patch = None

    #     x1_px, y1_px = event.x, event.y

    #     # Ignore accidental tiny drags (< 5 pixels)
    #     if abs(x1_px - x0_px) < 5 or abs(y1_px - y0_px) < 5:
    #         self._canvas.draw_idle()
    #         return

    #     ax = self._fig.axes[0]

    #     if hasattr(ax, 'set_box_aspect'):
    #         # 3D axis: compute how much of the figure the rectangle covers,
    #         # then zoom the camera proportionally
    #         fig_w = self._fig.get_figwidth()  * self._fig.dpi
    #         fig_h = self._fig.get_figheight() * self._fig.dpi
    #         frac_w = abs(x1_px - x0_px) / fig_w
    #         frac_h = abs(y1_px - y0_px) / fig_h
    #         # Zoom in by the inverse of the smaller fraction (tightest fit)
    #         zoom_factor = 1.0 / max(min(frac_w, frac_h), 0.05)
    #         self._zoom_scale *= zoom_factor
    #         fit_zoom = self._zoom_scale * (0.82 if self._show_grid else 1.0)
    #         ax.set_box_aspect(aspect=(2.5, 1.2, 1.0), zoom=fit_zoom)
    #     else:
    #         # 2D axis: convert pixel → data coords and set limits directly
    #         inv = ax.transData.inverted()
    #         # mpl pixel origin is bottom-left; Qt is top-left — no conversion needed
    #         # since mpl event coords are already in mpl display space
    #         x0_d, y0_d = inv.transform((min(x0_px, x1_px), min(y0_px, y1_px)))
    #         x1_d, y1_d = inv.transform((max(x0_px, x1_px), max(y0_px, y1_px)))
    #         ax.set_xlim(x0_d, x1_d)
    #         ax.set_ylim(y0_d, y1_d)

    #     self._canvas.draw_idle()

    def _zw_on_release(self, event):
        if self._zoom_rect_start is None or event.button != 1:
            return
        x0_px, y0_px = self._zoom_rect_start
        self._zoom_rect_start = None

        # Remove rubber-band rect
        if self._zoom_rect_patch is not None:
            try:
                self._zoom_rect_patch.remove()
            except Exception:
                pass
            self._zoom_rect_patch = None

        x1_px, y1_px = event.x, event.y

        # Ignore accidental tiny drags (< 5 pixels)
        if abs(x1_px - x0_px) < 5 or abs(y1_px - y0_px) < 5:
            self._canvas.draw_idle()
            return

        ax = self._fig.axes[0]

        if hasattr(ax, 'set_box_aspect'):
            # ── 3D axis ───────────────────────────────────────────────
            fig_w = self._fig.get_figwidth()  * self._fig.dpi
            fig_h = self._fig.get_figheight() * self._fig.dpi

            # Fraction of figure the rectangle covers
            frac_w = abs(x1_px - x0_px) / fig_w
            frac_h = abs(y1_px - y0_px) / fig_h

            # Zoom: inverse of rectangle size relative to full figure
            zoom_factor = 1.0 / max(min(frac_w, frac_h), 0.05)
            self._zoom_scale *= zoom_factor
            fit_zoom = self._zoom_scale * (0.82 if self._show_grid else 1.0)
            ax.set_box_aspect(aspect=(2.5, 1.2, 1.0), zoom=fit_zoom)

            # ── Shift camera to center on the selected rectangle ──────
            # Rectangle center in figure fraction (0=left/bottom, 1=right/top)
            cx_f = (min(x0_px, x1_px) + abs(x1_px - x0_px) / 2.0) / fig_w
            cy_f = (min(y0_px, y1_px) + abs(y1_px - y0_px) / 2.0) / fig_h

            # Figure center is at (0.5, 0.5).
            # Offset from center: positive cx_f-0.5 means rect is right of center
            # Map this offset to azim/elev adjustment:
            #   horizontal offset → azim shift (left/right rotation)
            #   vertical offset   → elev shift (up/down tilt)
            # Scale factor: larger zoom = finer angular correction needed
            angular_scale = 60.0 / zoom_factor  # degrees, shrinks as zoom grows

            dx_frac = cx_f - 0.5   # >0 = rect is right of center
            dy_frac = cy_f - 0.5   # >0 = rect is above center

            new_azim = ax.azim - dx_frac * angular_scale
            new_elev = max(-90, min(90, ax.elev + dy_frac * angular_scale))
            ax.view_init(elev=new_elev, azim=new_azim)
            self._current_azim = new_azim
            self._navcube_sync.force_sync()

        else:
            # ── 2D axis: exact pixel → data coords ───────────────────
            inv = ax.transData.inverted()
            x0_d, y0_d = inv.transform((min(x0_px, x1_px), min(y0_px, y1_px)))
            x1_d, y1_d = inv.transform((max(x0_px, x1_px), max(y0_px, y1_px)))
            ax.set_xlim(x0_d, x1_d)
            ax.set_ylim(y0_d, y1_d)

        self._canvas.draw_idle()

        # Auto-deactivate after one zoom
        self._btn_zoom_window.blockSignals(True)
        self._btn_zoom_window.setChecked(False)
        self._btn_zoom_window.blockSignals(False)
        self._zoom_window_active = False
        self._deactivate_all_modes()

        self._canvas.draw_idle()
        #Mode stays active — user must click the button again to deactivate
        

        ###CHANGES FOR ZOOM WINDOW______________________________________
        # if hasattr(ax, 'set_box_aspect'):
        #     # ── 3D: crop data limits to the selected screen rectangle ──
        #     # Works because at DEFAULT_ELEV=10, AZIM=-90:
        #     #   screen X → data X (span length)
        #     #   screen Y → data Z (force/displacement)
        #     #
        #     # Get the axes bounding box in display pixels
        #     bbox = ax.get_window_extent()
        #     ax_w = bbox.x1 - bbox.x0
        #     ax_h = bbox.y1 - bbox.y0

        #     if ax_w < 1 or ax_h < 1:
        #         self._canvas.draw_idle()
        #         return

        #     # Clamp rectangle coords to axes bbox
        #     rx0 = max(min(x0_px, x1_px), bbox.x0)
        #     rx1 = min(max(x0_px, x1_px), bbox.x1)
        #     ry0 = max(min(y0_px, y1_px), bbox.y0)
        #     ry1 = min(max(y0_px, y1_px), bbox.y1)

        #     # Fraction within axes bbox (0=left/bottom, 1=right/top)
        #     fx0 = (rx0 - bbox.x0) / ax_w
        #     fx1 = (rx1 - bbox.x0) / ax_w
        #     fy0 = (ry0 - bbox.y0) / ax_h
        #     fy1 = (ry1 - bbox.y0) / ax_h

        #     # Current data limits
        #     xl = ax.get_xlim3d()
        #     zl = ax.get_zlim3d()
        #     x_span = xl[1] - xl[0]
        #     z_span = zl[1] - zl[0]

        #     # Map screen fractions → new data limits
        #     new_x0 = xl[0] + fx0 * x_span
        #     new_x1 = xl[0] + fx1 * x_span
        #     new_z0 = zl[0] + fy0 * z_span
        #     new_z1 = zl[0] + fy1 * z_span

        #     ax.set_xlim3d(new_x0, new_x1)
        #     ax.set_zlim3d(new_z0, new_z1)

        #     # Update zoom scale to reflect new zoom level
        #     zoom_factor = 1.0 / max(min(fx1 - fx0, fy1 - fy0), 0.05)
        #     self._zoom_scale *= zoom_factor
        #     fit_zoom = self._zoom_scale * (0.82 if self._show_grid else 1.0)
        #     ax.set_box_aspect(aspect=(2.5, 1.2, 1.0), zoom=fit_zoom)
        # else:
        #     # 2D axis: convert pixel → data coords and set limits directly
        #     inv = ax.transData.inverted()
        #     # mpl pixel origin is bottom-left; Qt is top-left — no conversion needed
        #     # since mpl event coords are already in mpl display space
        #     x0_d, y0_d = inv.transform((min(x0_px, x1_px), min(y0_px, y1_px)))
        #     x1_d, y1_d = inv.transform((max(x0_px, x1_px), max(y0_px, y1_px)))
        #     ax.set_xlim(x0_d, x1_d)
        #     ax.set_ylim(y0_d, y1_d)

        # self._canvas.draw_idle()

        # # # Auto-deactivate after one zoom
        # # self._btn_zoom_window.blockSignals(True)
        # # self._btn_zoom_window.setChecked(False)
        # # self._btn_zoom_window.blockSignals(False)
        # # self._zoom_window_active = False
        # # self._deactivate_all_modes()

        # self._canvas.draw_idle()
        # # Mode stays active — user must click the button again to deactivate
         ###CHANGES FOR ZOOM WINDOW______________________________________
    
    
    # ── Pan ───────────────────────────────────────────────────────────────────
    def _on_pan_toggled(self, checked: bool):
        """Enable drag-to-pan on the plot axes."""
        if checked:
            self._deactivate_all_modes(except_btn=self._btn_pan)
            self._pan_active = True
            self._cid_press   = self._canvas.mpl_connect("button_press_event",   self._pan_on_press)
            self._cid_motion  = self._canvas.mpl_connect("motion_notify_event",  self._pan_on_motion)
            self._cid_release = self._canvas.mpl_connect("button_release_event", self._pan_on_release)
        else:
            self._pan_active = False
            self._deactivate_all_modes()

    def _pan_on_press(self, event):
        if event.inaxes and event.button == 1:
            self._pan_start = (event.xdata, event.ydata)

    def _pan_on_motion(self, event):
        if self._pan_start is None or not event.inaxes or event.xdata is None:
            return
        ax  = event.inaxes
        dx  = self._pan_start[0] - event.xdata
        dy  = self._pan_start[1] - event.ydata
        xl  = ax.get_xlim()
        yl  = ax.get_ylim()
        ax.set_xlim(xl[0] + dx, xl[1] + dx)
        ax.set_ylim(yl[0] + dy, yl[1] + dy)
        self._canvas.draw_idle()

    def _pan_on_release(self, event):
        self._pan_start = None

  
    # ── Rotate ───────────────────────────────────────────────
    def _on_rotate_click(self):
        if not self._fig or not self._fig.axes:
            return
        ax = self._fig.axes[0]
        if not hasattr(ax, 'elev'):
            return
        self._current_azim = getattr(self, '_current_azim', -60.0) + 45
        ax.view_init(elev=ax.elev, azim=self._current_azim)
        self._navcube_sync.force_sync()
        self._canvas.draw_idle()    

    # ── Scale ─────────────────────────────────────────────────────────────────
    def _on_scale_reset(self):
        pass  # replaced by spinbox

    def _start_scale_change(self, direction: int):
        self._scale_direction = direction
        self._tick_scale_change()
        self._scale_timer.start(300)

    def _stop_scale_change(self):
        self._scale_timer.stop()
        self._scale_direction = 0

    def _tick_scale_change(self):
        step = 1.0 * self._scale_direction
        self._scale_value = round(max(1.0, min(10000.0, self._scale_value + step)), 0)
        self._scale_input.setText(f"{self._scale_value:.0f}")
        self._apply_scale_value()

    def _on_scale_input_edited(self):
        try:
            val = float(self._scale_input.text())
            self._scale_value = round(max(1.0, min(10000.0, val)), 0)
        except ValueError:
            pass
        self._scale_input.setText(f"{self._scale_value:.0f}")
        self._apply_scale_value()

    def _apply_scale_value(self):
        if not self._fig or not self._fig.axes:
            return
        ax = self._fig.axes[0]
        factor = self._scale_value / 100.0
        if hasattr(ax, 'set_box_aspect'):   # 3-D
            ax.set_box_aspect(
                aspect=(2.5 * factor, 1.2, 1.0),
                zoom=self._zoom_scale
            )
        else:                               # 2-D
            ax.set_aspect('auto' if self._scale_value == 100.0 else factor)
        self._canvas.draw_idle()    


    def _apply_zoom(self):
        """Zooms the 2D canvas dynamically, creating scrollbars for perfect panning!"""
        if self._zoom_scale <= 1.0:
            self._zoom_scale = 1.0
            self._scroll_area.setWidgetResizable(True)
            self._canvas.setMinimumSize(0, 0)
            self._canvas.setMaximumSize(16777215, 16777215)
        else:
            self._scroll_area.setWidgetResizable(False)
            base_w = self._scroll_area.width() - 2
            base_h = self._scroll_area.height() - 2
            # Physically resize the canvas like zooming a photo
            self._canvas.setFixedSize(int(base_w * self._zoom_scale), int(base_h * self._zoom_scale))
            self._canvas.draw_idle()

    # def eventFilter(self, obj, event):
    #     if obj is self._canvas and event.type() == QEvent.Type.Wheel:
    #         event.accept() 
            
    #         # 1. Capture the exact mouse position BEFORE zooming
    #         pos = event.position()
    #         mouse_x, mouse_y = pos.x(), pos.y()
            
    #         old_width = self._canvas.width()
    #         old_height = self._canvas.height()

    #         # 2. Calculate the zoom
    #         delta = event.angleDelta().y()
    #         if delta > 0:
    #             self._zoom_scale = min(self._zoom_scale * 1.05, 8.0) # Zoom IN
    #         else:
    #             self._zoom_scale = max(self._zoom_scale * 0.95, 1.0) # Zoom OUT
                
    #         self._apply_zoom()

    #         # 3. Calculate how much the canvas grew/shrank
    #         new_width = self._canvas.width()
    #         new_height = self._canvas.height()

    #         if old_width == 0 or old_height == 0: return True

    #         # 4. Smart Scrollbar Math: Shift the view to keep the mouse anchored!
    #         h_bar = self._scroll_area.horizontalScrollBar()
    #         v_bar = self._scroll_area.verticalScrollBar()

    #         new_x = (mouse_x / old_width) * new_width
    #         new_y = (mouse_y / old_height) * new_height

    #         h_bar.setValue(int(h_bar.value() + (new_x - mouse_x)))
    #         v_bar.setValue(int(v_bar.value() + (new_y - mouse_y)))

    #         return True   
    #     return super().eventFilter(obj, event)
    def eventFilter(self, obj, event):
        """Intercepts the mouse wheel at the OS level to guarantee zoom triggers."""
        from PySide6.QtCore import QEvent
        
        if obj is self._canvas and event.type() == QEvent.Type.Wheel:
            event.accept() # Tell PySide6 "I handled this, do not scroll the window!"
            
            delta = event.angleDelta().y()
            if delta > 0:
                self._zoom_in()
            else:
                self._zoom_out()
                
            return True   
        return super().eventFilter(obj, event)

    # def _zoom_step(self, factor):
    #     """Natively zooms the Matplotlib 3D camera without clipping the data."""
    #     if not hasattr(self, '_fig') or not self._fig or not self._fig.axes:
    #         return
            
    #     ax = self._fig.axes[0]
        
    #     # Multiply the current zoom scale
    #     self._zoom_scale *= factor
        
    #     # Add safety limits so the user can't zoom in infinitely or zoom out to a dot
    #     self._zoom_scale = max(0.5, min(self._zoom_scale, 5.0))
        
    #     # Apply the new optical zoom while preserving your rigid 3D bridge shape!
    #     if hasattr(ax, 'set_box_aspect'):
    #         ax.set_box_aspect(aspect=(2.5, 1.2, 1.0), zoom=self._zoom_scale)
            
    #     self._canvas.draw_idle()

    # ==========================================
    # BUTTERY SMOOTH CAMERA ZOOMING
    # ==========================================

    def _apply_camera_zoom(self):
        """Applies zoom to the EXISTING figure without rebuilding it from scratch!"""
        if not hasattr(self, '_fig') or not self._fig or not self._fig.axes:
            return
            
        ax = self._fig.axes[0]
        
        # Change the optical zoom instantly without touching limits or layout
        if hasattr(ax, 'set_box_aspect'):
            ax.set_box_aspect(aspect=(2.5, 1.2, 1.0), zoom=self._zoom_scale)
            
        self._canvas.draw_idle()

    def _zoom_in(self):
        """Zooms the camera strictly inward."""
        self._zoom_scale *= 1.2  # Increase zoom parameter by 20%
        self._apply_camera_zoom() # Call our lightweight function, NOT update_plot()

    def _zoom_out(self):
        """Zooms the camera strictly outward."""
        self._zoom_scale /= 1.2  # Decrease zoom parameter by 20%
        if self._zoom_scale < 0.1: 
            self._zoom_scale = 0.1
        self._apply_camera_zoom()

    # def _zoom_reset(self):
    #     """Snaps back to 100% scale."""
    #     self._zoom_scale = 1.0
    #     self._apply_camera_zoom()

    def _zoom_reset(self):
        """Snaps back to 100% scale."""
        self._zoom_scale = 1.0
        self._current_azim = self._default_azim          # ← add
        self._scale_value = 100.0                        # ← add
        self._scale_input.setText("100")                 # ← add

        if not self._fig or not self._fig.axes:
            return
        ax = self._fig.axes[0]
        if hasattr(ax, 'elev'):                          # ← add
            ax.view_init(elev=self._default_elev,        # ← add
                        azim=self._default_azim)        # ← add
            self._navcube_sync.force_sync()              # ← add
        self._apply_camera_zoom()                        # keep as-is 

    # ==========================================
    # STATE HELPERS
    # ==========================================

    def _current_loadcase(self) -> str:
        combo = self._output_dock.output_widget.findChild(
            QComboBox, "analysis.load_combination"
        )
        return combo.currentText() if combo else (self._loadcases[0] if self._loadcases else "")

    def _current_force_key(self) -> str:
        from osdagbridge.desktop.ui.utils.custom_widgets import CustomRadioButton
        for rb in self._output_dock.output_widget.findChildren(CustomRadioButton):
            if rb.isChecked() and rb.text() in _RICH_LABEL_TO_FORCE:
                return _RICH_LABEL_TO_FORCE[rb.text()]
        return "Fy"        