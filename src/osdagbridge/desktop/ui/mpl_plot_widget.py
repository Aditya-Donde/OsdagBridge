import matplotlib
matplotlib.use("QtAgg")

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Path3DCollection 

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

        # Zoom state
        self._zoom_scale  = 1.0
        self._orig_limits = None   

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
        self._canvas.mpl_connect("button_press_event",   lambda e: self._navcube_sync.set_interaction_active(True)  if e.button == 1 else None)
        self._canvas.mpl_connect("button_release_event", lambda e: self._navcube_sync.set_interaction_active(False) if e.button == 1 else None)
        self._canvas.mpl_connect("motion_notify_event",  lambda e: self._navcube_sync.force_sync() if e.button == 1 else None)
        # ──────────────────────────────────────────────────────────

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

            # ==========================================
            # 2. 🚨 RESTORE CAMERA STATE TO NEW PLOT
            # ==========================================
            if old_elev is not None and old_azim is not None:
                ax.view_init(elev=old_elev, azim=old_azim)

            # (Keep your existing native zoom logic)
            if hasattr(ax, 'set_box_aspect'):
                ax.set_box_aspect(aspect=(2.5, 1.2, 1.0), zoom=self._zoom_scale)

            # (Keep your existing anti-clipping loop here)
            for line in ax.lines:
                line.set_clip_on(False)
            for collection in ax.collections:
                collection.set_clip_on(False)
            for text in ax.texts:
                text.set_clip_on(False)

            self._canvas.draw_idle()

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

    def _apply_grid_visibility(self):
        for ax in self._fig.axes:
            if self._show_grid:
                # Turn everything ON and re-apply your custom dashed grid styling
                ax.set_axis_on()
                ax.grid(True, linestyle="--", linewidth=0.4, alpha=0.5)
            else:
                # Throw the invisibility cloak over the panes, cube, labels, and ticks!
                ax.set_axis_off()

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

    def _zoom_reset(self):
        """Snaps back to 100% scale."""
        self._zoom_scale = 1.0
        self._apply_camera_zoom()

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