import matplotlib
matplotlib.use("QtAgg")

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Path3DCollection 
from html import escape
import re

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QSizePolicy, QPushButton,
    QFrame, QLabel, QCheckBox, QScrollArea, QApplication
)
from PySide6.QtCore import Qt, QEvent, QTimer

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
# PLOT TITLE OVERLAY
# =============================================================================
class PlotTitleOverlay(QFrame):
    """Device-consistent title text rendered independently of Matplotlib."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setStyleSheet("""
            PlotTitleOverlay {
                background: transparent;
                border: none;
            }
            QLabel {
                background: transparent;
                border: none;
            }
            QLabel#plotTitle {
                color: #171717;
                font-size: 18px;
                font-weight: normal;
            }
            QLabel#plotSubtitle {
                color: #3f3f3f;
                font-size: 14px;
                font-weight: normal;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.title_label = QLabel()
        self.title_label.setObjectName("plotTitle")
        self.title_label.setTextFormat(Qt.RichText)
        self.title_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        layout.addWidget(self.title_label)

        self.subtitle_label = QLabel()
        self.subtitle_label.setObjectName("plotSubtitle")
        self.subtitle_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        layout.addWidget(self.subtitle_label)

    def update_text(self, title: str, subtitle: str = ""):
        self.title_label.setText(self._to_rich_text(title))
        self.subtitle_label.setText(subtitle)
        self.subtitle_label.setVisible(bool(subtitle))
        self.show()

    @staticmethod
    def _to_rich_text(text: str) -> str:
        """Convert the simple Matplotlib mathtext used in titles into Qt HTML."""
        text = escape(text)
        text = re.sub(r"\$_\{?([^}$]+)\}?\$", r"<sub>\1</sub>", text)
        return re.sub(r"\$\^\{?([^}$]+)\}?\$", r"<sup>\1</sup>", text)


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
        self._show_girder_labels = True
        self._is_summary_checked = False
        self._show_max = False  
        self._show_min = False  
        self._show_all_vals = False 

        # Zoom state
        self._zoom_scale  = 1.0
        self._orig_limits = None

        # Engineering diagram scale (toolbar 0–10, baseline 1.0)
        self._eng_scale = 1.0

        # Pan/Rotate/Zoom Window mode states
        self._pan_active = False
        self._rotate_active = False
        self._zoom_window_active = False
        self._pan_start = None
        self._rotate_start = None
        self._pan_dragging = False
        self._rotate_dragging = False
        self._cid_press = None
        self._cid_motion = None
        self._cid_release = None   
        self._view_dragging   = False
        self._view_drag_start = None 

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

        self._title_overlay = PlotTitleOverlay(self._canvas)
        self._title_overlay.hide()

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
        self._canvas.mpl_connect("button_press_event",   lambda e: self._navcube_sync.set_interaction_active(True)  if e.button == 1 and not self._pan_active and not self._rotate_active else None)
        self._canvas.mpl_connect("button_release_event", lambda e: self._navcube_sync.set_interaction_active(False) if e.button == 1 and not self._pan_active and not self._rotate_active else None)
        self._canvas.mpl_connect("motion_notify_event",  lambda e: self._navcube_sync.force_sync() if e.button == 1 and not self._pan_active and not self._rotate_active else None)
        # ──────────────────────────────────────────────────────────

        # zoom toolbar
        self._btn_zoom_reset = QPushButton("⟳")
        for btn in (self._btn_zoom_reset,):
            btn.setFixedSize(28, 28)
            btn.setFocusPolicy(Qt.NoFocus)
            btn.setStyleSheet(
                "QPushButton { font-size: 16px; border: 1px solid #bbb; border-radius: 4px;"
                " background: #f5f5f5; }"
                "QPushButton:hover { background: #e0e0e0; }"
                "QPushButton:pressed { background: #bdbdbd; }"
            )
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

        self._btn_girder_labels = QPushButton("Girder Labels")
        self._btn_girder_labels.setCheckable(True)
        self._btn_girder_labels.setChecked(True)
        self._btn_girder_labels.setFixedHeight(28)
        self._btn_girder_labels.setFocusPolicy(Qt.NoFocus)
        self._btn_girder_labels.setStyleSheet(btn_style)
        self._btn_girder_labels.toggled.connect(self._on_girder_labels_toggled)
        # self._canvas.mpl_connect('scroll_event', self._on_scroll)

        toolbar_row = QHBoxLayout()
        toolbar_row.setContentsMargins(4, 2, 4, 2)
        toolbar_row.setSpacing(4)
        toolbar_row.addWidget(self._btn_grillage)
        toolbar_row.addWidget(self._btn_nodes)
        toolbar_row.addWidget(self._btn_supports) 
        toolbar_row.addWidget(self._btn_axis) 
        toolbar_row.addWidget(self._btn_grid)
        toolbar_row.addWidget(self._btn_girder_labels)
        toolbar_row.addStretch()
        toolbar_row.addWidget(self._btn_zoom_reset)

        # layout
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addLayout(toolbar_row)
        root.addWidget(self._scroll_area, stretch=1)

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

    def set_engineering_scale(self, scale):
        """Apply display scale for force/deflection diagrams (0–10, baseline 1.0)."""
        try:
            scale = float(scale)
        except (TypeError, ValueError):
            scale = 1.0
        scale = max(0.0, min(10.0, scale))
        if abs(scale - self._eng_scale) < 1e-9:
            return
        self._eng_scale = scale
        if self._grillage_mode:
            return
        self.update_plot()

    def update_plot(self, *_args):
        if self._grillage_mode:
            return

        if self._ds_all is None or self._output_dock is None:
            return

        loadcase  = self._current_loadcase()
        force_key = self._current_force_key()

        if not loadcase or not force_key:
            return

        ds = self._ds_all.sel(Loadcase=loadcase)
        
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
        eng_scale = self._eng_scale
        if force_key in _SFD_KEYS:
            self._fig, self._summary_data = build_figure_sfd(
                ds, force_key, self._nodes, self._members,
                edge_dist=self._edge_dist, eng_scale=eng_scale,
            )
        elif force_key in _DEFL_KEYS:
            self._fig, self._summary_data = build_figure_deflection(
                ds, force_key, self._nodes, self._members,
                edge_dist=self._edge_dist, eng_scale=eng_scale,
            )
        else:
            self._fig, self._summary_data = build_figure_bmd(
                ds, force_key, self._nodes, self._members,
                edge_dist=self._edge_dist, eng_scale=eng_scale,
            )

        self._attach_figure(self._fig)
        
        # (Your existing visibility toggles)
        self._apply_node_visibility()
        self._apply_axis_visibility()
        self._apply_supports_visibility()
        self._apply_grid_visibility()
        self._apply_girder_labels_visibility()
        self._apply_annotation_visibility() 
        
        # (Your existing HUD logic)
        if self._summary_data:
            self._summary_overlay.update_data(self._summary_data)
            if self._is_summary_checked:
                self._summary_overlay.show()
                self._summary_overlay.raise_()
        else:
            self._summary_overlay.hide()
        
        if self._fig:
            self._fig.subplots_adjust(left=0.02, right=0.98, bottom=0.02, top=0.92)
            
            if not self._fig.axes:
                return

            ax = self._fig.axes[0]
            if old_elev is not None and old_azim is not None:
                ax.view_init(elev=old_elev, azim=old_azim)

            title = ax.get_title()
            ax.set_title("")

            # Preserve the box aspect computed by plot_generator (it now depends on engineering scale),
            # and only apply camera zoom.
            if hasattr(ax, 'set_box_aspect'):
                try:
                    cur_aspect = ax.get_box_aspect()
                except Exception:
                    cur_aspect = None
                if cur_aspect is None:
                    cur_aspect = (2.5, 1.2, 1.0)
                ax.set_box_aspect(aspect=cur_aspect, zoom=self._zoom_scale)

            # (Keep your existing anti-clipping loop here)
            for line in ax.lines:
                line.set_clip_on(False)
            for collection in ax.collections:
                collection.set_clip_on(False)
            for text in ax.texts:
                text.set_clip_on(False)

            self._canvas.draw()

            scale_label = self._engineering_scale_label(ax, force_key)
            subtitle = f"Load Case/Combination : {loadcase}"
            if scale_label:
                subtitle = f"{subtitle}  |  {scale_label}"
            self._title_overlay.update_text(title, subtitle)
            self._position_title_overlay()

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
            old_elev, old_azim = None, None
            if self._fig and self._fig.axes and hasattr(self._fig.axes[0], 'elev'):
                old_elev = self._fig.axes[0].elev
                old_azim = self._fig.axes[0].azim
            plt.close(self._fig)
            self._fig = build_figure_grillage(self._nodes, self._members, edge_dist=self._edge_dist)
            self._attach_figure(self._fig)
            if self._fig.axes and old_elev is not None and old_azim is not None:
                self._fig.axes[0].view_init(elev=old_elev, azim=old_azim)
            if self._fig.axes:
                title = self._fig.axes[0].get_title()
                self._fig.axes[0].set_title("")
                self._title_overlay.update_text(title)
                self._position_title_overlay()
            
            self._apply_node_visibility()
            self._apply_axis_visibility()
            self._apply_supports_visibility()
            self._apply_grid_visibility()
            self._apply_girder_labels_visibility()
            self._summary_overlay.hide() 
            
            if self._fig.axes and hasattr(self._fig.axes[0], 'set_box_aspect'):
                self._fig.axes[0].set_box_aspect(
                    aspect=(2.5, 1.2, 1.0),
                    zoom=self._zoom_scale,
                )
            self._canvas.draw()
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
        self._apply_girder_labels_visibility()
        self._canvas.draw_idle()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._summary_overlay:
            self._summary_overlay.move(15, 45) # Keep HUD floating safely under the toolbar
        self._position_title_overlay()

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

    def _apply_grid_visibility(self):
        for ax in self._fig.axes:
            if self._show_grid:
                # Turn everything ON and re-apply your custom dashed grid styling
                ax.set_axis_on()
                ax.grid(True, linestyle="--", linewidth=0.4, alpha=0.5)
            else:
                # Throw the invisibility cloak over the panes, cube, labels, and ticks!
                ax.set_axis_off()

    def _apply_girder_labels_visibility(self):
        for ax in self._fig.axes:
            for text in ax.texts:
                if text.get_gid() == "girder_labels":
                    text.set_visible(self._show_girder_labels)
                    # Enforce a consistent visual style across all plot rebuilds.
                    text.set_fontsize(13)
                    text.set_color("black")

    def _attach_figure(self, fig):
        """Install a rebuilt figure using QtAgg's current DPR-aware canvas size."""
        self._canvas.figure = fig
        fig.set_canvas(self._canvas)
        dpr = float(getattr(self._canvas, "device_pixel_ratio", 1.0))
        width = self._canvas.width() * dpr
        height = self._canvas.height() * dpr
        if width > 10 and height > 10:
            fig.set_size_inches(width / fig.dpi, height / fig.dpi, forward=False)

    def _position_title_overlay(self):
        if not hasattr(self, "_title_overlay"):
            return
        height = 58 if self._title_overlay.subtitle_label.isVisible() else 28
        self._title_overlay.setGeometry(0, 18, self._canvas.width(), height)
        self._title_overlay.raise_()

    def _store_orig_limits(self):
        pass # Not needed for Uniform Render Zoom

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
    
    # REPLACE both eventFilter methods with this single one:
    def eventFilter(self, obj, event):
        if obj is not self._canvas:
            return super().eventFilter(obj, event)
        etype = event.type()

        if etype == QEvent.Type.Resize:                        # NavCube reposition
            self._resize_navcube()
            self._position_navcube()
            self._position_title_overlay()
            if self._navcube.isVisible():
                self._navcube.raise_()

        elif etype == QEvent.Type.Wheel:                       # Zoom
            event.accept()
            if event.angleDelta().y() > 0:
                self._zoom_in()
            else:
                self._zoom_out()
            return True

        elif self._pan_active:                                 # ← NEW: viewport drag
            if etype == QEvent.Type.MouseButtonPress and event.button() == Qt.LeftButton:
                self._view_dragging   = True
                self._view_drag_start = event.pos()
                self._canvas.setCursor(Qt.ClosedHandCursor)
                return True
            elif etype == QEvent.Type.MouseMove and self._view_dragging:
                delta = event.pos() - self._view_drag_start
                self._view_drag_start = event.pos()
                self._scroll_area.horizontalScrollBar().setValue(
                    self._scroll_area.horizontalScrollBar().value() - delta.x())
                self._scroll_area.verticalScrollBar().setValue(
                    self._scroll_area.verticalScrollBar().value() - delta.y())
                return True
            elif etype == QEvent.Type.MouseButtonRelease and self._view_dragging:
                self._view_dragging   = False
                self._view_drag_start = None
                self._canvas.setCursor(Qt.OpenHandCursor)
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
            try:
                cur_aspect = ax.get_box_aspect()
            except Exception:
                cur_aspect = None
            if cur_aspect is None:
                cur_aspect = (2.5, 1.2, 1.0)
            ax.set_box_aspect(aspect=cur_aspect, zoom=self._zoom_scale)
            
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

    def _zoom_reset(self):
        """Reset zoom and auto-fit plot to show all data."""
        self._zoom_scale = 1.0
        if not self._fig or not self._fig.axes:
            return
        ax = self._fig.axes[0]
        if hasattr(ax, 'set_box_aspect'):  # 3D
            fit_zoom = 0.82 if self._show_grid else 1.0
            try:
                cur_aspect = ax.get_box_aspect()
            except Exception:
                cur_aspect = None
            if cur_aspect is None:
                cur_aspect = (2.5, 1.2, 1.0)
            ax.set_box_aspect(aspect=cur_aspect, zoom=fit_zoom)
            ax.autoscale()
        else:  # 2D
            ax.relim()
            ax.autoscale_view()
        self._apply_zoom()
        self._apply_camera_zoom()

    def _toggle_pan(self, enabled: bool):
        """Enable/disable pan mode."""
        if enabled:
            self._disconnect_pan_rotate()
            self._rotate_active = False
            self._zoom_window_active = False
            self._pan_active = True
            self._pan_start = None
            self._canvas.setCursor(Qt.OpenHandCursor)
            self._set_native_3d_mouse(rotate_btn=[], zoom_btn=[])
            self._cid_press = self._canvas.mpl_connect("button_press_event", self._pan_on_press)
            self._cid_motion = self._canvas.mpl_connect("motion_notify_event", self._pan_on_motion)
            self._cid_release = self._canvas.mpl_connect("button_release_event", self._pan_on_release)
        else:
            self._pan_active = False
            self._canvas.setCursor(Qt.ArrowCursor)
            self._pan_dragging = False
            self._disconnect_pan_rotate()
            self._set_native_3d_mouse(rotate_btn=1, zoom_btn=3)

    def _pan_on_press(self, event):
        """Store the starting position for pan."""
        if event.inaxes and event.button == 1:
            self._pan_start = (event.x, event.y)
            self._pan_dragging = True

    def _pan_on_motion(self, event):
        """Pan the plot by shifting axis limits."""
        if not self._pan_active or not self._pan_dragging or not self._pan_start or not event.inaxes:
            return

        ax = event.inaxes

        dx_px = event.x - self._pan_start[0]
        dy_px = event.y - self._pan_start[1]

        axbbox = ax.get_window_extent()
        width_px = axbbox.width
        height_px = axbbox.height

        if width_px > 0 and height_px > 0:
            xl, yl = ax.get_xlim(), ax.get_ylim()
            data_dx = -dx_px * (xl[1] - xl[0]) / width_px
            data_dy = dy_px * (yl[1] - yl[0]) / height_px

            # 3D: shift X with horizontal drag and Z with vertical drag so
            # the full plotted block appears to move in both directions.
            if hasattr(ax, "get_zlim") and hasattr(ax, "set_zlim"):
                zl = ax.get_zlim()
                # Keep drag direction natural: dragging up moves scene up.
                data_dz = -dy_px * (zl[1] - zl[0]) / height_px
                ax.set_xlim(xl[0] + data_dx, xl[1] + data_dx)
                ax.set_ylim(yl[0] + data_dy, yl[1] + data_dy)
                ax.set_zlim(zl[0] + data_dz, zl[1] + data_dz)
            else:
                # 2D fallback
                ax.set_xlim(xl[0] + data_dx, xl[1] + data_dx)
                ax.set_ylim(yl[0] + data_dy, yl[1] + data_dy)

            self._canvas.draw_idle()

        self._pan_start = (event.x, event.y)

    def _pan_on_release(self, event):
        self._pan_start = None
        self._pan_dragging = False

    def _toggle_rotate(self, enabled: bool):
        """Enable/disable rotate mode (3D only)."""
        if enabled:
            self._disconnect_pan_rotate()
            self._pan_active = False
            self._zoom_window_active = False
            self._rotate_active = True
            self._rotate_start = None
            self._set_native_3d_mouse(rotate_btn=1, zoom_btn=3)
            self._canvas.setCursor(Qt.OpenHandCursor)
            self._cid_press = self._canvas.mpl_connect("button_press_event", self._rot_on_press)
            self._cid_motion = self._canvas.mpl_connect("motion_notify_event", self._rot_on_motion)
            self._cid_release = self._canvas.mpl_connect("button_release_event", self._rot_on_release)
        else:
            self._rotate_active = False
            self._canvas.setCursor(Qt.ArrowCursor)
            self._rotate_dragging = False
            self._disconnect_pan_rotate()

    def _rot_on_press(self, event):
        if event.button == 1:
            self._rotate_start = (event.x, event.y)
            self._rotate_dragging = True

    def _rot_on_motion(self, event):
        if not self._rotate_active or not self._rotate_dragging or not self._rotate_start or not self._fig or not self._fig.axes:
            return
        ax = self._fig.axes[0]
        if not hasattr(ax, 'elev'):
            return
        dx = event.x - self._rotate_start[0]
        dy = event.y - self._rotate_start[1]
        self._rotate_start = (event.x, event.y)
        ax.view_init(elev=max(-90, min(90, ax.elev + dy * 0.5)), azim=ax.azim - dx * 0.5)
        self._navcube_sync.force_sync()
        self._canvas.draw_idle()

    def _rot_on_release(self, event):
        self._rotate_start = None
        self._rotate_dragging = False

    def _set_native_3d_mouse(self, rotate_btn=1, zoom_btn=3):
        if not self._fig or not self._fig.axes:
            return
        for ax in self._fig.axes:
            if hasattr(ax, "mouse_init"):
                ax.mouse_init(rotate_btn=rotate_btn, zoom_btn=zoom_btn)

    def _disconnect_pan_rotate(self):
        """Disconnect pan/rotate event handlers."""
        for cid in (self._cid_press, self._cid_motion, self._cid_release):
            if cid is not None:
                try:
                    self._canvas.mpl_disconnect(cid)
                except Exception:
                    pass
        self._cid_press = self._cid_motion = self._cid_release = None

    @staticmethod
    def _value_unit_for_force_key(force_key: str) -> str:
        if force_key in _DEFL_KEYS:
            return "mm"
        if force_key in _SFD_KEYS:
            return "kN"
        return "kNm"

    def _engineering_scale_label(self, ax, force_key: str) -> str:
        """Compute '1 cm = …' from axis limits and rendered height."""
        if not hasattr(ax, "get_zlim"):
            return ""
        eng_scale = self._eng_scale
        if eng_scale < 1e-12:
            return "Scale: N/A"

        z0, z1 = ax.get_zlim()
        zmin = min(z0, z1)
        zmax = max(z0, z1)
        z_span = zmax - zmin
        if z_span < 1e-12:
            return ""

        try:
            renderer = self._canvas.get_renderer()
            bbox = ax.get_window_extent(renderer)
        except Exception:
            return ""

        height_px = bbox.height
        if height_px < 1:
            return ""
        if abs(zmax) < 1e-12:
            return ""

        dpi = float(self._fig.dpi) if self._fig else 110.0
        dpr = float(getattr(self._canvas, "device_pixel_ratio", 1.0))
        # We want "from baseline (0) up to the positive extreme" to match the
        # common engineering meaning of the scale label.
        height_above_zero_px = height_px * (zmax / z_span)
        height_cm = (height_above_zero_px / max(dpi * dpr, 1.0)) * 2.54
        if height_cm < 1e-6:
            return ""

        # z-axis coordinate is already multiplied by eng_scale, so divide back.
        real_per_cm = (zmax / height_cm) / eng_scale
        unit = self._value_unit_for_force_key(force_key)
        return f"Scale: 1 cm = {real_per_cm:.3g} {unit}"

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