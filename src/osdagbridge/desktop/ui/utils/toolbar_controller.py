"""
toolbar_controller.py
─────────────────────
This file is the CONTROLLER layer for the shared ToolBarWidget.
It wires each toolbar button to the currently active view (3D CAD or Plots)
without modifying any of those views' source files.

HOW IT FITS IN THE APPLICATION
───────────────────────────────
  ToolBarWidget  (custom_widgets.py)
       │  buttons live here
       ▼
  ToolBarController  ← YOU ARE HERE
       │  binds buttons to the active view
       ├──▶  CAD3DWindow  (cad_3d.py)     — 3D view is active
       └──▶  MplPlotWidget (mpl_plot_widget.py) — Plots view is active

PUBLIC API
──────────
    ctrl = ToolBarController(tool_bar)
    ctrl.bind_to_cad_3d(cad_3d_widget)   # call when 3D CAD view opens
    ctrl.bind_to_plots(plots_widget)      # call when Plots view opens
    ctrl.reset()                          # call when neither view is active

DESIGN NOTES
────────────
• Buttons in ToolBarWidget are identified by their tooltip string.
  _find_button(tooltip) locates them by matching toolTip() on each button.

• Toggle buttons (Grillage, Node, Rotate, Pan, Zoom Window) are made
  checkable when a view is bound. A green highlight shows their active state.

• For 3D CAD overlays (Grillage, Node): we set the hidden checkbox state
  directly with blockSignals and then call selector._apply() — this is
  necessary because cb.click() is unreliable on hidden Qt widgets.

• For 3D CAD navigation (Rotate, Pan, Zoom Window): we call
  BridgeComponentCheckbox._on_rotate_toggled / _on_pan_toggled /
  _on_zoom_window_toggled in cad_3d.py.  Those methods call
  CustomViewer3d.set_navigation_mode() in custom_3dviewer.py.

• For one-shot actions (Zoom Fit, Zoom In, Zoom Out): we call the OCC
  display API (cad_widget.display.*) directly.

• For Plots view (Grillage, Node): clicks are proxied to the internal
  buttons inside MplPlotWidget (mpl_plot_widget.py) via .click().

• reset() removes all connections and restores buttons to plain appearance.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QPushButton

if TYPE_CHECKING:
    from osdagbridge.desktop.ui.utils.custom_widgets import ToolBarWidget
    from osdagbridge.desktop.ui.cad_3d import CAD3DWindow
    from osdagbridge.desktop.ui.mpl_plot_widget import MplPlotWidget


# ─────────────────────────────────────────────────────────────────────────────
#   STYLE CONSTANTS
#   These are applied to toolbar buttons to show whether they are active or not.
#   _STYLE_DEFAULT  — plain transparent style (button is inactive / not a toggle)
#   _STYLE_CHECKABLE — adds a green highlight for the :checked state so the user
#                      can see which toolbar action is currently enabled.
# ─────────────────────────────────────────────────────────────────────────────

# Original ToolBarWidget button style (plain, no checked state)
_STYLE_DEFAULT = """
    QPushButton {
        border: none;
        background: transparent;
        border-radius: 4px;
        outline: none;
    }
    QPushButton:hover {
        background-color: rgba(150, 150, 150, 60);
    }
    QPushButton:focus {
        outline: none;
    }
"""

# Active style applied to toggle buttons — grey background when :checked
_STYLE_CHECKABLE = """
    QPushButton {
        border: none;
        background: transparent;
        border-radius: 4px;
        outline: none;
    }
    QPushButton:hover {
        background-color: rgba(150, 150, 150, 60);
    }
    QPushButton:focus {
        outline: none;
    }
    QPushButton:checked {
        background-color: rgba(130, 130, 130, 80);
        border: none;
        border-radius: 4px;
    }
    QPushButton:checked:hover {
        background-color: rgba(130, 130, 130, 110);
    }
"""


# ─────────────────────────────────────────────────────────────────────────────
#   TOOLBAR CONTROLLER
# ─────────────────────────────────────────────────────────────────────────────

class ToolBarController:
    """
    Manages context-sensitive behaviour of the shared ToolBarWidget.

    Call bind_to_cad_3d() when the 3D CAD view becomes active,
    bind_to_plots() when the Plots view becomes active, and reset()
    when returning to the dual 2D CAD (or any other view).
    """

    # ── TOOLTIP STRINGS ────────────────────────────────────────────────────────
    # These must exactly match the tooltip strings passed to create_button()
    # inside ToolBarWidget (custom_widgets.py).  _find_button() searches by
    # tooltip to locate the correct QPushButton in the toolbar layout.
    _TIP_GRILLAGE     = "Grillage View"
    _TIP_NODE         = "Node"
    _TIP_NODE_NUMBER  = "Node Number"
    _TIP_ELEMENT_NUMBER= "Element Number"   # Element Number toggle (both CAD and Plots)
    _TIP_ZOOM_WIN     = "Zoom Window"  # toggle — activates drag-to-zoom rect mode
    _TIP_PAN          = "Pan"          # toggle — activates pan navigation mode
    _TIP_ROTATE       = "Rotate"       # toggle — activates rotate navigation mode
    _TIP_ZOOM_FIT     = "Zoom Fit"    # one-shot action — not a toggle
    _TIP_ZOOM_IN      = "Zoom In"     # one-shot action — not a toggle
    _TIP_ZOOM_OUT     = "Zoom Out"    # one-shot action — not a toggle
    _TIP_AXIS         = "Axis"
    _TIP_GRID         = "Grid Lines"
    _TIP_SUPPORTS     = "Supports"
    _TIP_LOADS        = "Loads"
    _TIP_GIRDER_LABELS= "Girder Labels"

    def __init__(self, tool_bar: "ToolBarWidget") -> None:
        self._toolbar = tool_bar

        # (button, handler) pairs — tracked so _disconnect_all() can cleanly
        # remove exactly the handlers this controller added, nothing more.
        self._active_connections: list[tuple[QPushButton, object]] = []

        # ── Resolve toolbar buttons from the ToolBarWidget layout ──────────────
        # Each button is found once at construction by its tooltip string.
        # Toggle buttons — these become checkable when a view is bound:
        self._btn_grillage:      QPushButton | None = self._find_button(self._TIP_GRILLAGE)
        self._btn_node:          QPushButton | None = self._find_button(self._TIP_NODE)
        self._btn_node_number:   QPushButton | None = self._find_button(self._TIP_NODE_NUMBER)
        self._btn_element_number: QPushButton | None = self._find_button(self._TIP_ELEMENT_NUMBER)
        self._btn_zoom_win:      QPushButton | None = self._find_button(self._TIP_ZOOM_WIN)
        self._btn_pan:           QPushButton | None = self._find_button(self._TIP_PAN)
        self._btn_rotate:        QPushButton | None = self._find_button(self._TIP_ROTATE)

        # One-shot buttons — always plain, never checkable:
        self._btn_zoom_fit: QPushButton | None = self._find_button(self._TIP_ZOOM_FIT)
        self._btn_zoom_in:  QPushButton | None = self._find_button(self._TIP_ZOOM_IN)
        self._btn_zoom_out: QPushButton | None = self._find_button(self._TIP_ZOOM_OUT)

        # Plot-only toggle buttons — hidden in CAD view, shown in Plots view:
        self._btn_axis:          QPushButton | None = self._find_button(self._TIP_AXIS)
        self._btn_grid:          QPushButton | None = self._find_button(self._TIP_GRID)
        self._btn_supports:      QPushButton | None = self._find_button(self._TIP_SUPPORTS)
        self._btn_loads:         QPushButton | None = self._find_button(self._TIP_LOADS)
        self._btn_girder_labels: QPushButton | None = self._find_button(self._TIP_GIRDER_LABELS)

        # Managed toggle buttons — bulk checkable/restore in reset() and bind_to_*()
        # NOTE: _btn_loads is intentionally excluded — it is never made checkable,
        #       it is simply hidden in CAD view and shown in Plots view.
        self._managed_buttons: list[QPushButton] = [
            b for b in (
                self._btn_grillage, self._btn_node, self._btn_node_number,
                self._btn_element_number,
                self._btn_zoom_win, self._btn_pan, self._btn_rotate,
                self._btn_axis, self._btn_grid, self._btn_supports,
                self._btn_girder_labels,
            )
            if b is not None
        ]

    # ── BUTTON RETRIEVAL ──────────────────────────────────────────────────────
    # Searches the ToolBarWidget scroll-area layout (custom_widgets.py) for a
    # QPushButton whose toolTip() matches the given string.  Called once per
    # button at construction time.

    def _find_button(self, tooltip: str) -> QPushButton | None:
        """
        Walk the ToolBarWidget scroll-area container layout and return the
        first QPushButton whose toolTip() matches *tooltip*.
        The ToolBarWidget and its layout are defined in custom_widgets.py.
        """
        try:
            container = self._toolbar.scroll_area.widget()
            if container is None:
                return None
            layout = container.layout()
            if layout is None:
                return None
            for i in range(layout.count()):
                item   = layout.itemAt(i)
                widget = item.widget() if item else None
                if isinstance(widget, QPushButton) and widget.toolTip() == tooltip:
                    return widget
        except Exception:
            pass
        return None

    # ── PLOTS-ONLY WIDGET VISIBILITY ─────────────────────────────────────────
    # Grid Lines, Supports, Loads, Girder Labels, and the Scale spinner are
    # only meaningful in the Plots view.  They are hidden when the 3D CAD view
    # is active and restored when the Plots view (or no view) is active.

    def _hide_plots_only_widgets(self) -> None:
        """Hide toolbar widgets that are irrelevant in the 3D CAD view."""
        for btn in (self._btn_grid, self._btn_supports,
                    self._btn_loads, self._btn_girder_labels):
            if btn is not None:
                btn.hide()
        try:
            self._toolbar.spin_scale.hide()
            self._toolbar.scale_label.hide()
        except Exception:
            pass

    def _show_plots_only_widgets(self) -> None:
        """Restore toolbar widgets that are only used in Plots / reset state."""
        for btn in (self._btn_grid, self._btn_supports,
                    self._btn_loads, self._btn_girder_labels):
            if btn is not None:
                btn.show()
        try:
            self._toolbar.spin_scale.show()
            self._toolbar.scale_label.show()
        except Exception:
            pass

    # ── STYLE / CHECKABLE HELPERS ─────────────────────────────────────────────
    # These helpers centralise all style and checkable state changes so no
    # handler has to set styles manually.

    def _make_checkable(self, btn: QPushButton | None, initial: bool = False) -> None:
        """Enable checkable mode + green active-highlight style on *btn*.
        Called at the start of bind_to_cad_3d() / bind_to_plots() for each
        toggle button so it shows its checked state visually."""
        if btn is None:
            return
        btn.setCheckable(True)
        btn.setChecked(initial)
        btn.setStyleSheet(_STYLE_CHECKABLE)

    def _restore_plain(self, btn: QPushButton | None) -> None:
        """Restore *btn* to its original non-checkable plain appearance.
        Called by reset() when no view is active."""
        if btn is None:
            return
        btn.blockSignals(True)
        btn.setChecked(False)
        btn.blockSignals(False)
        btn.setCheckable(False)
        btn.setStyleSheet(_STYLE_DEFAULT)

    def _sync_btn_to(self, btn: QPushButton | None, state: bool) -> None:
        """Force *btn* checked state to *state* without emitting a signal.
        Used after a handler runs to keep the toolbar button in sync with
        whatever state the underlying view method settled on."""
        if btn is None:
            return
        btn.blockSignals(True)
        btn.setChecked(state)
        btn.blockSignals(False)

    # ── CONNECTION MANAGEMENT ─────────────────────────────────────────────────
    # All connections made by this controller go through _connect() so they
    # are recorded and can be removed cleanly by _disconnect_all().

    def _connect(self, btn: QPushButton | None, handler) -> None:
        """Connect *handler* to *btn*.clicked and record the pair for teardown."""
        if btn is None:
            return
        btn.clicked.connect(handler)
        self._active_connections.append((btn, handler))

    def _disconnect_all(self) -> None:
        """Disconnect every handler this controller has connected.
        Called at the start of bind_to_cad_3d() / bind_to_plots() / reset()
        to ensure there are no leftover connections from the previous view."""
        for btn, handler in self._active_connections:
            try:
                btn.clicked.disconnect(handler)
            except (RuntimeError, TypeError):
                pass
        self._active_connections.clear()
        
        # Note: We no longer reset button states here to preserve user selections
        # Button states are now managed by the specific view binding methods

    # ── PUBLIC API ────────────────────────────────────────────────────────────

    def reset(self) -> None:
        """
        Tear down all connections and restore buttons to their original
        non-checkable, plain appearance.  Call when no special view is active.
        """
        self._disconnect_all()
        for btn in self._managed_buttons:
            self._restore_plain(btn)
        # Show all widgets — reset is the neutral state where everything is visible
        self._show_plots_only_widgets()

    def bind_to_cad_3d(self, cad_widget: "CAD3DWindow") -> None:
        """
        Disconnect any existing bindings, then wire all toolbar buttons to the
        3D CAD view (CAD3DWindow in cad_3d.py).

        OVERLAY TOGGLES — Grillage View & Node
        ───────────────────────────────────────
        These show/hide pre-built AIS objects in the OCC 3D context.
        The actual rendering logic (creating the AIS objects) is in cad_3d.py:
          • CAD3DWindow._render_grillage()  — builds edge lines between nodes
          • CAD3DWindow._render_nodes()     — builds sphere markers at each node
          • CAD3DWindow.update_component_visibility() — shows/hides AIS objects

        HOW WE DRIVE THEM FROM HERE:
        1.  Find the hidden "Grillage view" / "Node" QCheckBox inside
            BridgeComponentCheckbox._checkboxes (cad_3d.py).
        2.  Set its checked state with blockSignals so its own toggled signal
            does not fire (avoids double-execution).
        3.  Call BridgeComponentCheckbox._apply() directly — that method calls
            CAD3DWindow.update_component_visibility() regardless of whether
            the checkbox widget itself is visible on screen.

        NAVIGATION TOGGLES — Rotate, Pan, Zoom Window
        ───────────────────────────────────────────────
        These change how mouse input is interpreted by the OCC 3D viewer.
        The actual viewer mode switching is in cad_3d.py / custom_3dviewer.py:
          • BridgeComponentCheckbox._on_rotate_toggled() → NavMode.ROTATE
          • BridgeComponentCheckbox._on_pan_toggled()    → NavMode.PAN
          • BridgeComponentCheckbox._on_zoom_window_toggled() → NavMode.ZOOM_WINDOW
        Each of those methods calls CustomViewer3d.set_navigation_mode()
        which is defined in custom_3dviewer.py.

        ONE-SHOT ACTIONS — Zoom Fit, Zoom In, Zoom Out
        ────────────────────────────────────────────────
        Call the OCC display API on CAD3DWindow.display (pythonocc) directly:
          • display.FitAll()        — zoom to fit all geometry
          • display.ZoomFactor(f)   — zoom in/out by factor f
        """
        self._disconnect_all()

        # Hide buttons that are only useful in the Plots view
        self._hide_plots_only_widgets()

        # NOTE: _btn_axis is NOT hidden — it is active in CAD view (controls the 3D axis triad)

        # ── Read initial checkbox state from BridgeComponentCheckbox (cad_3d.py) ──
        # The "Grillage view", "Node", and "Node Numbers" checkboxes are read so
        # the toolbar buttons start in the correct checked/unchecked state.
        def _initial_cb_state(label: str) -> bool:
            try:
                for cb in cad_widget.component_selector._checkboxes:
                    if cb.text() == label:
                        return cb.isChecked()
            except Exception:
                pass
            return False

        self._make_checkable(self._btn_grillage,    _initial_cb_state("Grillage view"))
        self._make_checkable(self._btn_node,         _initial_cb_state("Node"))
        self._make_checkable(self._btn_node_number,  _initial_cb_state("Node Numbers"))

        # ── Axis triad toggle — initial state: on if the triad widget is already started ──
        def _initial_axis_state() -> bool:
            try:
                return getattr(cad_widget.viewer._axis_triad, "_started", False)
            except Exception:
                return False

        self._make_checkable(self._btn_axis, _initial_axis_state())

        # ── Grillage toggle ───────────────────────────────────────────────────
        # RENDERING LOGIC: cad_3d.py → CAD3DWindow._render_grillage()
        # VISIBILITY LOGIC: cad_3d.py → CAD3DWindow.update_component_visibility()
        # DATA SOURCE: node positions from CAD3DWindow._render_nodes(), which
        #   calls results_data._build_nodes_members() → ops.nodeCoord(n)
        def _cad_toggle_grillage():
            """
            Qt has already auto-toggled the toolbar button.  Read its new state
            and drive the BridgeComponentCheckbox (cad_3d.py) to match, then
            call _apply() so update_component_visibility() is triggered.
            """
            want = self._btn_grillage.isChecked()
            try:
                selector = cad_widget.component_selector
                for cb in selector._checkboxes:
                    if cb.text() == "Grillage view":
                        # Set checkbox state without emitting its own signal
                        cb.blockSignals(True)
                        cb.setChecked(want)
                        cb.blockSignals(False)
                        # Apply selection directly — this calls update_component_visibility
                        selector._apply()
                        # Sync toolbar button to checkbox's settled state
                        self._sync_btn_to(self._btn_grillage, cb.isChecked())
                        break
            except Exception:
                pass

        # ── Node toggle ───────────────────────────────────────────────────────
        # RENDERING LOGIC: cad_3d.py → CAD3DWindow._render_nodes()
        # VISIBILITY LOGIC: cad_3d.py → CAD3DWindow.update_component_visibility()
        # DATA SOURCE: node coordinates from results_data._build_nodes_members()
        #   which calls ops.getNodeTags() and ops.nodeCoord(n) from openseespy.
        def _cad_toggle_node():
            """Same pattern as _cad_toggle_grillage — drives the hidden Node checkbox."""
            want = self._btn_node.isChecked()
            try:
                selector = cad_widget.component_selector
                for cb in selector._checkboxes:
                    if cb.text() == "Node":
                        cb.blockSignals(True)
                        cb.setChecked(want)
                        cb.blockSignals(False)
                        selector._apply()
                        self._sync_btn_to(self._btn_node, cb.isChecked())
                        break
            except Exception:
                pass

        # ── Node Number toggle ────────────────────────────────────────────────
        # Fully independent of BridgeComponentCheckbox — logic lives here only.
        #
        # ON  → call cad_widget._render_node_numbers() directly.
        #       That method builds AIS_TextLabel objects (one per node) at
        #       deck_top_z + 80 mm and registers them in
        #       cad_widget.viewer.model_ais_objects["NodeNumbers"].
        #       It also erases the Node sphere markers while labels are shown.
        #
        # OFF → erase every AIS object stored in model_ais_objects["NodeNumbers"]
        #       directly via the OCC context, then repaint.
        #       Node spheres are NOT automatically restored here — that is left
        #       to the existing Node button so the two toggles stay independent.
        #
        # DATA SOURCE: cad_widget._node_data populated by _render_nodes().
        def _cad_toggle_node_number():
            """
            Independent node-number toggle.
            Does NOT touch BridgeComponentCheckbox or call _apply().
            All logic is self-contained in toolbar_controller.py.
            """
            want = self._btn_node_number.isChecked()
            try:
                if want:
                    # Render labels directly — no checkbox involved
                    cad_widget._render_node_numbers()
                else:
                    # Erase all NodeNumbers AIS objects directly
                    context = cad_widget.viewer.context
                    for ais in cad_widget.viewer.model_ais_objects.pop("NodeNumbers", []):
                        try:
                            context.Erase(ais, False)
                        except Exception:
                            pass
                    try:
                        cad_widget.display.Repaint()
                    except Exception:
                        pass
            except Exception:
                pass
            self._sync_btn_to(self._btn_node_number, want)

        # ── Element Number toggle ——————————————————————————————————————————————————
        # RENDERING LOGIC: cad_3d.py → CAD3DWindow._render_element_numbers()
        # DATA SOURCE: self._members populated by _render_nodes() (openseespy)
        self._make_checkable(self._btn_element_number, initial=False)

        def _cad_toggle_element_number():
            """
            Independent element-number toggle — same pattern as _cad_toggle_node_number.
            ON  → call cad_widget._render_element_numbers() which builds one
                   AIS_TextLabel per element at the member midpoint and registers
                   them in cad_widget.viewer.model_ais_objects["ElementNumbers"].
            OFF → erase every AIS object stored in model_ais_objects["ElementNumbers"]
                   directly via the OCC context, then repaint.
            DATA SOURCE: cad_widget._node_data and cad_widget._members from _render_nodes().
            """
            want = self._btn_element_number.isChecked()
            try:
                if want:
                    cad_widget._render_element_numbers()
                else:
                    context = cad_widget.viewer.context
                    for ais in cad_widget.viewer.model_ais_objects.pop("ElementNumbers", []):
                        try:
                            context.Erase(ais, False)
                        except Exception:
                            pass
                    try:
                        cad_widget.display.Repaint()
                    except Exception:
                        pass
            except Exception:
                pass
            self._sync_btn_to(self._btn_element_number, want)

        self._connect(self._btn_element_number, _cad_toggle_element_number)

        # ── Axis Triad toggle ─────────────────────────────────────────────────
        # RENDERING:  custom_3dviewer.py → AxisTriadOverlay.start() / .stop()
        # The overlay is parented to the same host widget as the NavCube and
        # polls V3d_View.Eye/At/Up every 50 ms to stay in sync with the camera.
        # ON  → call start() which shows the widget and starts the poll timer.
        # OFF → call stop()  which hides the widget and stops the poll timer.
        def _cad_toggle_axis():
            """
            Show/hide the 3D axis triad overlay.
            start() / stop() are defined on AxisTriadOverlay in custom_3dviewer.py.
            They control both widget visibility and the 50-ms poll timer.
            """
            want = self._btn_axis.isChecked()
            try:
                triad = cad_widget.viewer._axis_triad
                if triad is not None:
                    if want:
                        # Re-position before showing in case the viewer was resized
                        cad_widget.viewer._position_axis_triad()
                        triad.start()
                    else:
                        triad.stop()
            except Exception:
                pass
            self._sync_btn_to(self._btn_axis, want)

        self._connect(self._btn_axis, _cad_toggle_axis)

        self._connect(self._btn_grillage,   _cad_toggle_grillage)
        self._connect(self._btn_node,        _cad_toggle_node)
        self._connect(self._btn_node_number, _cad_toggle_node_number)

        # ── Zoom Window toggle ────────────────────────────────────────────────
        # NAVIGATION LOGIC: cad_3d.py → BridgeComponentCheckbox._on_zoom_window_toggled()
        # VIEWER MODE: custom_3dviewer.py → CustomViewer3d.set_navigation_mode(NavMode.ZOOM_WINDOW)
        self._make_checkable(self._btn_zoom_win, initial=False)

        def _cad_toggle_zoom_window():
            """
            Qt has already auto-toggled the toolbar button.
            Delegates to BridgeComponentCheckbox._on_zoom_window_toggled() (cad_3d.py)
            which calls CustomViewer3d.set_navigation_mode() (custom_3dviewer.py).
            If the selector is unavailable, falls back to calling the viewer directly.
            Mutually exclusive with Pan and Rotate — unchecks those buttons when activated.
            """
            want = self._btn_zoom_win.isChecked()
            # Mutual exclusion: deactivate the other navigation toggles
            if want:
                self._sync_btn_to(self._btn_pan, False)
                self._sync_btn_to(self._btn_rotate, False)
            try:
                selector = cad_widget.component_selector
                # _on_zoom_window_toggled is defined in BridgeComponentCheckbox (cad_3d.py)
                # It calls CustomViewer3d.set_navigation_mode(NavMode.ZOOM_WINDOW)
                selector._on_zoom_window_toggled(want)
                # Keep the internal _zoom_win_btn in sync so state is consistent
                selector._zoom_win_btn.blockSignals(True)
                selector._zoom_win_btn.setChecked(want)
                selector._zoom_win_btn.blockSignals(False)
            except Exception:
                # Fallback: call viewer directly if selector unavailable
                try:
                    from osdagbridge.desktop.ui.utils.custom_3dviewer import NavMode
                    if cad_widget.viewer is not None:
                        cad_widget.viewer.set_navigation_mode(
                            NavMode.ZOOM_WINDOW if want else None
                        )
                except Exception:
                    pass
            self._sync_btn_to(self._btn_zoom_win, want)

        self._connect(self._btn_zoom_win, _cad_toggle_zoom_window)

        # ── Pan toggle ────────────────────────────────────────────────────────
        # NAVIGATION LOGIC: cad_3d.py → BridgeComponentCheckbox._on_pan_toggled()
        # VIEWER MODE: custom_3dviewer.py → CustomViewer3d.set_navigation_mode(NavMode.PAN)
        self._make_checkable(self._btn_pan, initial=False)

        def _cad_toggle_pan():
            """
            Delegates to BridgeComponentCheckbox._on_pan_toggled() (cad_3d.py)
            which calls CustomViewer3d.set_navigation_mode(NavMode.PAN).
            Falls back to calling the viewer directly if the selector is unavailable.
            Mutually exclusive with Rotate and Zoom Window — unchecks those buttons when activated.
            """
            want = self._btn_pan.isChecked()
            # Mutual exclusion: deactivate the other navigation toggles
            if want:
                self._sync_btn_to(self._btn_rotate, False)
                self._sync_btn_to(self._btn_zoom_win, False)
            try:
                selector = cad_widget.component_selector
                # _on_pan_toggled is defined in BridgeComponentCheckbox (cad_3d.py)
                selector._on_pan_toggled(want)
            except Exception:
                # Fallback: call viewer directly
                try:
                    from osdagbridge.desktop.ui.utils.custom_3dviewer import NavMode
                    if cad_widget.viewer is not None:
                        cad_widget.viewer.set_navigation_mode(
                            NavMode.PAN if want else None
                        )
                except Exception:
                    pass
            self._sync_btn_to(self._btn_pan, want)

        self._connect(self._btn_pan, _cad_toggle_pan)

        # ── Rotate toggle ─────────────────────────────────────────────────────
        # NAVIGATION LOGIC: cad_3d.py → BridgeComponentCheckbox._on_rotate_toggled()
        # VIEWER MODE: custom_3dviewer.py → CustomViewer3d.set_navigation_mode(NavMode.ROTATE)
        self._make_checkable(self._btn_rotate, initial=False)

        def _cad_toggle_rotate():
            """
            Delegates to BridgeComponentCheckbox._on_rotate_toggled() (cad_3d.py)
            which calls CustomViewer3d.set_navigation_mode(NavMode.ROTATE).
            Falls back to calling the viewer directly if the selector is unavailable.
            Mutually exclusive with Pan and Zoom Window — unchecks those buttons when activated.
            """
            want = self._btn_rotate.isChecked()
            # Mutual exclusion: deactivate the other navigation toggles
            if want:
                self._sync_btn_to(self._btn_pan, False)
                self._sync_btn_to(self._btn_zoom_win, False)
            try:
                selector = cad_widget.component_selector
                # _on_rotate_toggled is defined in BridgeComponentCheckbox (cad_3d.py)
                selector._on_rotate_toggled(want)
            except Exception:
                # Fallback: call viewer directly
                try:
                    from osdagbridge.desktop.ui.utils.custom_3dviewer import NavMode
                    if cad_widget.viewer is not None:
                        cad_widget.viewer.set_navigation_mode(
                            NavMode.ROTATE if want else None
                        )
                except Exception:
                    pass
            self._sync_btn_to(self._btn_rotate, want)

        self._connect(self._btn_rotate, _cad_toggle_rotate)

        # ── Zoom Fit (one-shot) ────────────────────────────────────────────────
        # Calls CAD3DWindow.display.FitAll() — the OCC pythonocc display API.
        # cad_widget.display is the OCC display object on CAD3DWindow (cad_3d.py).
        def _cad_zoom_fit():
            """Fit all visible geometry in the OCC view.
            Calls CAD3DWindow.display.FitAll() — defined by pythonocc (not cad_3d.py)."""
            try:
                if cad_widget.display is not None and not cad_widget._cad_init_pending:
                    cad_widget.display.FitAll()
            except Exception:
                pass

        self._connect(self._btn_zoom_fit, _cad_zoom_fit)

        # ── Zoom In (one-shot) ─────────────────────────────────────────────────
        # Calls CAD3DWindow.display.ZoomFactor(1.1) — 10% zoom in.
        def _cad_zoom_in():
            """Zoom into the OCC view by a fixed 10% step.
            Calls CAD3DWindow.display.ZoomFactor() from the pythonocc API."""
            try:
                if cad_widget.display is not None and not cad_widget._cad_init_pending:
                    cad_widget.display.ZoomFactor(1.1)
            except Exception:
                pass

        self._connect(self._btn_zoom_in, _cad_zoom_in)

        # ── Zoom Out (one-shot) ────────────────────────────────────────────────
        # Calls CAD3DWindow.display.ZoomFactor(1/1.1) — 10% zoom out.
        def _cad_zoom_out():
            """Zoom out of the OCC view by a fixed 10% step.
            Calls CAD3DWindow.display.ZoomFactor() from the pythonocc API."""
            try:
                if cad_widget.display is not None and not cad_widget._cad_init_pending:
                    cad_widget.display.ZoomFactor(1 / 1.1)
            except Exception:
                pass

        self._connect(self._btn_zoom_out, _cad_zoom_out)

    def bind_to_plots(self, plots_widget: "MplPlotWidget") -> None:
        """
        Disconnect any existing bindings, then wire Grillage and Node toolbar
        buttons to the Plots view (MplPlotWidget in mpl_plot_widget.py).

        HOW IT WORKS
        ─────────────
        MplPlotWidget has its own internal checkable buttons (_btn_grillage,
        _btn_nodes) that are always visible when the Plots view is active.
        We proxy toolbar clicks directly to those internal buttons via .click().
        The .click() call fires all existing toggle/render logic already wired
        inside MplPlotWidget — we do not duplicate any of that logic here.

        Navigation buttons (Rotate, Pan, Zoom Window) are connected here to the
        equivalent MplPlotWidget methods (_toggle_rotate / _toggle_pan /
        _toggle_zoom_window) and are mutually exclusive. The one-shot zoom
        actions (Zoom Fit, Zoom In, Zoom Out) map to MplPlotWidget._zoom_reset /
        _zoom_in / _zoom_out at the bottom of this method.
        """
        self._disconnect_all()

        # Show all plots-only widgets now that we are in Plots view
        self._show_plots_only_widgets()

        # Read the current state of MplPlotWidget's internal state variables so the
        # toolbar buttons start in the correct checked/unchecked state.
        def _initial_plot_state(attr_name: str, default: bool = False) -> bool:
            try:
                return getattr(plots_widget, attr_name) if hasattr(plots_widget, attr_name) else default
            except Exception:
                return default

        grillage_init      = _initial_plot_state('_grillage_mode', False)
        node_init          = _initial_plot_state('_show_nodes', True)
        node_number_init   = _initial_plot_state('_show_node_numbers', False)
        axis_init          = _initial_plot_state('_show_axis', False)
        grid_init          = _initial_plot_state('_show_grid', False)
        supports_init      = _initial_plot_state('_show_supports', True)
        pan_init           = _initial_plot_state('_pan_active', False)
        rotate_init        = _initial_plot_state('_rotate_active', False)
        zoom_window_init   = _initial_plot_state('_zoom_window_active', False)
        girder_labels_init = _initial_plot_state('_show_girder_labels', True)

        self._make_checkable(self._btn_grillage,      grillage_init)
        self._make_checkable(self._btn_node,           node_init)
        self._make_checkable(self._btn_node_number,    node_number_init)
        self._make_checkable(self._btn_element_number,  False)           # always off on bind
        self._make_checkable(self._btn_axis,           axis_init)
        self._make_checkable(self._btn_grid,           grid_init)
        self._make_checkable(self._btn_supports,       supports_init)
        self._make_checkable(self._btn_pan,            pan_init)
        self._make_checkable(self._btn_rotate,         rotate_init)
        self._make_checkable(self._btn_zoom_win,       zoom_window_init)
        self._make_checkable(self._btn_girder_labels,  girder_labels_init)

        # ── Grillage — direct call to MplPlotWidget._on_grillage_toggled ──────
        def _plots_toggle_grillage():
            """
            Direct call to MplPlotWidget._on_grillage_toggled method.
            This bypasses the internal button and calls the toggle logic directly.
            Then sync the toolbar button to match the new state.
            """
            try:
                # Get current state from toolbar button
                checked = self._btn_grillage.isChecked()
                plots_widget._on_grillage_toggled(checked)
                # Sync the state back to the button
                self._sync_btn_to(self._btn_grillage, checked)
            except Exception:
                pass

        # ── Node — direct call to MplPlotWidget._on_nodes_toggled ────────────
        def _plots_toggle_node():
            """Direct call to MplPlotWidget._on_nodes_toggled method."""
            try:
                # Get current state from toolbar button
                checked = self._btn_node.isChecked()
                plots_widget._on_nodes_toggled(checked)
                # Sync the state back to the button
                self._sync_btn_to(self._btn_node, checked)
            except Exception:
                pass

        self._connect(self._btn_grillage, _plots_toggle_grillage)
        self._connect(self._btn_node,     _plots_toggle_node)

        # ── Node Number — direct call to MplPlotWidget._on_node_numbers_toggled ──
        # RENDERING LOGIC: plot_generator._add_node_number_labels() draws text with
        #   gid="node_number" at each node position, initially hidden.
        # TOGGLE LOGIC: MplPlotWidget._on_node_numbers_toggled() / _apply_node_number_visibility()
        #   walks ax.texts and sets visible=True/False for every gid="node_number" text.
        def _plots_toggle_node_number():
            """Direct call to MplPlotWidget._on_node_numbers_toggled method."""
            try:
                checked = self._btn_node_number.isChecked()
                plots_widget._on_node_numbers_toggled(checked)
                self._sync_btn_to(self._btn_node_number, checked)
            except Exception:
                pass

        self._connect(self._btn_node_number, _plots_toggle_node_number)

        # ── Element Number — direct call to MplPlotWidget._on_element_numbers_toggled ──
        # RENDERING LOGIC: plot_generator._add_element_number_labels() draws text with
        #   gid="element_number" at each element midpoint, initially hidden.
        #   DATA SOURCE: members dict from results_data._build_nodes_members()
        #   (ops.getEleTags() / ops.eleNodes()) passed via MplPlotWidget.setup().
        # TOGGLE LOGIC: MplPlotWidget._on_element_numbers_toggled() /
        #   _apply_element_number_visibility() walks ax.texts and sets
        #   visible=True/False for every gid="element_number" text.
        def _plots_toggle_element_numbers():
            """Direct call to MplPlotWidget._on_element_numbers_toggled method."""
            try:
                checked = self._btn_element_number.isChecked()
                plots_widget._on_element_numbers_toggled(checked)
                self._sync_btn_to(self._btn_element_number, checked)
            except Exception:
                pass

        self._connect(self._btn_element_number, _plots_toggle_element_numbers)

        # ── Axis — direct call to MplPlotWidget._on_axis_toggled ──────────────
        def _plots_toggle_axis():
            try:
                # Get current state from toolbar button
                checked = self._btn_axis.isChecked()
                plots_widget._on_axis_toggled(checked)
                # Sync the state back to the button
                self._sync_btn_to(self._btn_axis, checked)
            except Exception:
                pass

        self._connect(self._btn_axis, _plots_toggle_axis)

        # ── Grid — direct call to MplPlotWidget._on_grid_toggled ────────────────
        def _plots_toggle_grid():
            try:
                # Get current state from toolbar button
                checked = self._btn_grid.isChecked()
                plots_widget._on_grid_toggled(checked)
                # Sync the state back to the button
                self._sync_btn_to(self._btn_grid, checked)
            except Exception:
                pass

        self._connect(self._btn_grid, _plots_toggle_grid)

        # ── Supports — direct call to MplPlotWidget._on_supports_toggled ─────────
        def _plots_toggle_supports():
            try:
                # Get current state from toolbar button
                checked = self._btn_supports.isChecked()
                plots_widget._on_supports_toggled(checked)
                # Sync the state back to the button
                self._sync_btn_to(self._btn_supports, checked)
            except Exception:
                pass

        self._connect(self._btn_supports, _plots_toggle_supports)

        # ── Pan — direct call to MplPlotWidget._toggle_pan ─────────────────────
        def _plots_toggle_pan():
            checked = self._btn_pan.isChecked()
            # Mutual exclusion: deactivate Rotate and Zoom Window when Pan is activated
            if checked:
                self._sync_btn_to(self._btn_rotate, False)
                self._sync_btn_to(self._btn_zoom_win, False)
            try:
                plots_widget._toggle_pan(checked)
                self._sync_btn_to(self._btn_pan, checked)
            except Exception:
                pass

        self._connect(self._btn_pan, _plots_toggle_pan)

        # ── Rotate — direct call to MplPlotWidget._toggle_rotate ───────────────
        def _plots_toggle_rotate():
            checked = self._btn_rotate.isChecked()
            # Mutual exclusion: deactivate Pan and Zoom Window when Rotate is activated
            if checked:
                self._sync_btn_to(self._btn_pan, False)
                self._sync_btn_to(self._btn_zoom_win, False)
            try:
                plots_widget._toggle_rotate(checked)
                self._sync_btn_to(self._btn_rotate, checked)
            except Exception:
                pass

        self._connect(self._btn_rotate, _plots_toggle_rotate)

        # ── Zoom Window — direct call to MplPlotWidget._toggle_zoom_window ──────
        # TOGGLE LOGIC: MplPlotWidget._toggle_zoom_window() arms rubber-band mode;
        #   on release MplPlotWidget._execute_zoom_window() scales the canvas so
        #   the selected rectangle fills the QScrollArea viewport (mpl_plot_widget.py).
        #   This mirrors the CAD 3D Zoom Window result (custom_3dviewer.py) without
        #   a true camera WindowFit, which Matplotlib 3D does not provide.
        def _plots_toggle_zoom_window():
            checked = self._btn_zoom_win.isChecked()
            # Mutual exclusion: deactivate Pan and Rotate when Zoom Window is activated
            if checked:
                self._sync_btn_to(self._btn_pan, False)
                self._sync_btn_to(self._btn_rotate, False)
            try:
                plots_widget._toggle_zoom_window(checked)
                self._sync_btn_to(self._btn_zoom_win, checked)
            except Exception:
                pass

        self._connect(self._btn_zoom_win, _plots_toggle_zoom_window)

        # ── Girder Labels — direct call to MplPlotWidget._on_girder_labels_toggled ──
        # TOGGLE LOGIC: MplPlotWidget._on_girder_labels_toggled() / _apply_girder_labels_visibility()
        #   walks ax.texts and sets visible=True/False for every gid="girder_labels" text.
        # INITIAL STATE: True — girder labels (G1, G2, …) are shown by default.
        def _plots_toggle_girder_labels():
            """Direct call to MplPlotWidget._on_girder_labels_toggled method."""
            try:
                checked = self._btn_girder_labels.isChecked()
                plots_widget._on_girder_labels_toggled(checked)
                self._sync_btn_to(self._btn_girder_labels, checked)
            except Exception:
                pass

        self._connect(self._btn_girder_labels, _plots_toggle_girder_labels)

        # ------------------------------------------------------------            # One‑shot zoom actions for the Plot view – map directly to the
        # MplPlotWidget's internal zoom methods. These are not toggle
        # buttons; they perform an immediate action when clicked.
        # ------------------------------------------------------------
        self._connect(self._btn_zoom_fit, plots_widget._zoom_reset)
        self._connect(self._btn_zoom_in,  plots_widget._zoom_in)
        self._connect(self._btn_zoom_out, plots_widget._zoom_out)
