"""
toolbar_controller.py
─────────────────────
Wires the shared ``ToolBarWidget`` to whichever central view is currently
active (3D CAD or Plots).  All logic lives here — no existing files are
modified.

Public API
──────────
    ctrl = ToolBarController(tool_bar)
    ctrl.bind_to_cad_3d(cad_3d_widget)   # call when 3D CAD view opens
    ctrl.bind_to_plots(plots_widget)      # call when Plots view opens
    ctrl.reset()                          # call when neither view is active

Design notes
────────────
• Buttons in ToolBarWidget are anonymous (no stored references).
  ``_find_button(tooltip)`` locates them by matching toolTip() strings.

• Toggle buttons (Grillage, Node) are made checkable when a view is bound
  and get a green active-highlight so the user sees the current state.

• For 3D CAD toggles: we directly set the checkbox state with blockSignals
  and then call selector._apply() — this bypasses the hidden-widget signal
  limitation (cb.click() on a hidden QWidget is unreliable in Qt).

• For 3D CAD one-shot actions (Zoom Fit, Zoom In): we call the OCC display
  method directly after checking display readiness.

• For Plots: clicks are proxied to MplPlotWidget's own checkable buttons
  via .click() (those widgets are visible), then toolbar state is synced.

• reset() unchecks all managed buttons and restores plain appearance.
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
# ─────────────────────────────────────────────────────────────────────────────

# Original ToolBarWidget button style (plain, no checked state)
_STYLE_DEFAULT = """
    QPushButton {
        border: none;
        background: transparent;
        border-radius: 4px;
    }
    QPushButton:hover {
        background-color: rgba(150, 150, 150, 60);
    }
"""

# Active style: adds a green highlight for the :checked state so the user
# can see at a glance which toolbar actions are currently enabled.
_STYLE_CHECKABLE = """
    QPushButton {
        border: none;
        background: transparent;
        border-radius: 4px;
    }
    QPushButton:hover {
        background-color: rgba(150, 150, 150, 60);
    }
    QPushButton:checked {
        background-color: rgba(46, 125, 50, 140);
        border: 1px solid rgba(46, 125, 50, 200);
        border-radius: 4px;
    }
    QPushButton:checked:hover {
        background-color: rgba(46, 125, 50, 180);
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

    # Must match exactly the tooltip strings passed to create_button() in ToolBarWidget
    _TIP_GRILLAGE  = "Grillage View"
    _TIP_NODE      = "Node"
    _TIP_ZOOM_WIN  = "Zoom Window"  # toggle — activates drag-to-zoom rect mode
    _TIP_PAN       = "Pan"          # toggle — activates pan navigation mode
    _TIP_ZOOM_FIT  = "Zoom Fit"    # one-shot action — not a toggle
    _TIP_ZOOM_IN   = "Zoom In"     # one-shot action — not a toggle
    _TIP_ZOOM_OUT  = "Zoom Out"    # one-shot action — not a toggle

    def __init__(self, tool_bar: "ToolBarWidget") -> None:
        self._toolbar = tool_bar

        # (button, handler) pairs tracked for precise disconnection
        self._active_connections: list[tuple[QPushButton, object]] = []

        # Toggle buttons (resolved once from layout)
        self._btn_grillage: QPushButton | None = self._find_button(self._TIP_GRILLAGE)
        self._btn_node: QPushButton | None     = self._find_button(self._TIP_NODE)
        self._btn_zoom_win: QPushButton | None = self._find_button(self._TIP_ZOOM_WIN)
        self._btn_pan: QPushButton | None      = self._find_button(self._TIP_PAN)

        # One-shot action buttons (not toggles — resolved separately)
        self._btn_zoom_fit: QPushButton | None = self._find_button(self._TIP_ZOOM_FIT)
        self._btn_zoom_in:  QPushButton | None = self._find_button(self._TIP_ZOOM_IN)
        self._btn_zoom_out: QPushButton | None = self._find_button(self._TIP_ZOOM_OUT)

        # Toggle buttons in a list — used for bulk checkable/restore operations
        self._managed_buttons: list[QPushButton] = [
            b for b in (
                self._btn_grillage, self._btn_node,
                self._btn_zoom_win, self._btn_pan,
            )
            if b is not None
        ]

    # ── BUTTON RETRIEVAL ──────────────────────────────────────────────────────

    def _find_button(self, tooltip: str) -> QPushButton | None:
        """
        Walk the ToolBarWidget scroll-area container layout and return the
        first QPushButton whose toolTip() matches *tooltip*.
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

    # ── STYLE / CHECKABLE HELPERS ─────────────────────────────────────────────

    def _make_checkable(self, btn: QPushButton | None, initial: bool = False) -> None:
        """Enable checkable mode + active-highlight style on *btn*."""
        if btn is None:
            return
        btn.setCheckable(True)
        btn.setChecked(initial)
        btn.setStyleSheet(_STYLE_CHECKABLE)

    def _restore_plain(self, btn: QPushButton | None) -> None:
        """Restore *btn* to its original non-checkable appearance."""
        if btn is None:
            return
        btn.blockSignals(True)
        btn.setChecked(False)
        btn.blockSignals(False)
        btn.setCheckable(False)
        btn.setStyleSheet(_STYLE_DEFAULT)

    def _sync_btn_to(self, btn: QPushButton | None, state: bool) -> None:
        """Force *btn* checked state to *state* without emitting signals."""
        if btn is None:
            return
        btn.blockSignals(True)
        btn.setChecked(state)
        btn.blockSignals(False)

    # ── CONNECTION MANAGEMENT ─────────────────────────────────────────────────

    def _connect(self, btn: QPushButton | None, handler) -> None:
        """Connect *handler* to *btn*.clicked and record for teardown."""
        if btn is None:
            return
        btn.clicked.connect(handler)
        self._active_connections.append((btn, handler))

    def _disconnect_all(self) -> None:
        """Disconnect every handler this controller has connected."""
        for btn, handler in self._active_connections:
            try:
                btn.clicked.disconnect(handler)
            except (RuntimeError, TypeError):
                pass
        self._active_connections.clear()

    # ── PUBLIC API ────────────────────────────────────────────────────────────

    def reset(self) -> None:
        """
        Tear down all connections and restore buttons to their original
        non-checkable, plain appearance.  Call when no special view is active.
        """
        self._disconnect_all()
        for btn in self._managed_buttons:
            self._restore_plain(btn)

    def bind_to_cad_3d(self, cad_widget: "CAD3DWindow") -> None:
        """
        Disconnect any existing bindings, then wire toolbar buttons to the
        3D CAD view.

        Toggle buttons: Grillage View, Node
        ────────────────────────────────────
        We use blockSignals + setChecked + _apply() instead of cb.click().
        Reason: BridgeComponentCheckbox.component_selector is hidden until
        render_3d_cad() is called.  Qt's QAbstractButton.click() does not
        reliably emit signals when the widget (or any ancestor) is hidden,
        so the _on_click → _apply chain was silently skipped.

        The fix: set the checkbox state manually (blockSignals so no double-
        fire), then call selector._apply() directly — _apply() builds the
        visible-key list and calls cad_widget.update_component_visibility(),
        which talks to the OCC context regardless of widget visibility.

        One-shot buttons: Zoom Fit, Zoom In
        ────────────────────────────────────
        Call the OCC display API directly after checking readiness.
        """
        self._disconnect_all()

        # Sync toggle button initial state with current checkbox state
        def _initial_cb_state(label: str) -> bool:
            try:
                for cb in cad_widget.component_selector._checkboxes:
                    if cb.text() == label:
                        return cb.isChecked()
            except Exception:
                pass
            return False

        self._make_checkable(self._btn_grillage, _initial_cb_state("Grillage view"))
        self._make_checkable(self._btn_node,     _initial_cb_state("Node"))

        # ── Grillage ─────────────────────────────────────────────────────────
        def _cad_toggle_grillage():
            """
            Qt has already auto-toggled the toolbar button.  Read its new state
            and drive the BridgeComponentCheckbox to match, then call _apply()
            directly so the OCC context updates regardless of widget visibility.
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

        # ── Node ─────────────────────────────────────────────────────────────
        def _cad_toggle_node():
            """Same pattern for the Node checkbox."""
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

        self._connect(self._btn_grillage, _cad_toggle_grillage)
        self._connect(self._btn_node,     _cad_toggle_node)

        # ── Zoom Window (toggle — activates drag-to-zoom rect mode) ────────────
        self._make_checkable(self._btn_zoom_win, initial=False)

        def _cad_toggle_zoom_window():
            """
            Qt has already auto-toggled the toolbar button.
            Delegate to BridgeComponentCheckbox._on_zoom_window_toggled():
              - sets NavMode.ZOOM_WINDOW on the OCC viewer when checked
              - resets NavMode to None when unchecked
              - deactivates Rotate / Pan buttons (mutual exclusion)
            Sync the toolbar button back to whatever state the method settled on.
            """
            want = self._btn_zoom_win.isChecked()
            try:
                selector = cad_widget.component_selector
                # Also uncheck Rotate / Pan toolbar buttons if they exist
                # (the selector handles its own internal buttons via _on_zoom_window_toggled)
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

        # ── Pan (toggle — activates pan navigation mode) ──────────────────────
        self._make_checkable(self._btn_pan, initial=False)

        def _cad_toggle_pan():
            """
            Delegate to BridgeComponentCheckbox._on_pan_toggled():
              - sets NavMode.PAN on the OCC viewer when checked
              - resets NavMode to None when unchecked
              - deactivates Rotate / Zoom Window buttons (mutual exclusion)
            """
            want = self._btn_pan.isChecked()
            try:
                selector = cad_widget.component_selector
                selector._on_pan_toggled(want)
                # Keep internal _pan_btn in sync
                selector._pan_btn.blockSignals(True)
                selector._pan_btn.setChecked(want)
                selector._pan_btn.blockSignals(False)
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

        # ── Zoom Fit (one-shot) ───────────────────────────────────────────────
        def _cad_zoom_fit():
            """Fit all visible geometry in the OCC view."""
            try:
                if cad_widget.display is not None and not cad_widget._cad_init_pending:
                    cad_widget.display.FitAll()
            except Exception:
                pass

        self._connect(self._btn_zoom_fit, _cad_zoom_fit)

        # ── Zoom In (one-shot) ────────────────────────────────────────────────
        def _cad_zoom_in():
            """Zoom into the OCC view by a fixed 10% step."""
            try:
                if cad_widget.display is not None and not cad_widget._cad_init_pending:
                    cad_widget.display.ZoomFactor(1.1)
            except Exception:
                pass

        self._connect(self._btn_zoom_in, _cad_zoom_in)

        # ── Zoom Out (one-shot) ────────────────────────────────────────
        def _cad_zoom_out():
            """Zoom out of the OCC view by a fixed 10% step."""
            try:
                if cad_widget.display is not None and not cad_widget._cad_init_pending:
                    cad_widget.display.ZoomFactor(1 / 1.1)
            except Exception:
                pass

        self._connect(self._btn_zoom_out, _cad_zoom_out)

    def bind_to_plots(self, plots_widget: "MplPlotWidget") -> None:
        """
        Disconnect any existing bindings, then wire Grillage and Node toolbar
        buttons to the MplPlotWidget's own internal checkable buttons.

        The plot widget's internal buttons (_btn_grillage, _btn_nodes) are
        always visible when the Plots view is active, so proxying via .click()
        is safe and fires all the existing toggle/render logic unchanged.
        """
        self._disconnect_all()

        # Start in sync with the internal button states
        try:
            grillage_init = plots_widget._btn_grillage.isChecked()
        except Exception:
            grillage_init = False
        try:
            node_init = plots_widget._btn_nodes.isChecked()
        except Exception:
            node_init = False

        self._make_checkable(self._btn_grillage, grillage_init)
        self._make_checkable(self._btn_node,     node_init)

        # ── Grillage ─────────────────────────────────────────────────────────
        def _plots_toggle_grillage():
            """
            Proxy the click to MplPlotWidget._btn_grillage (it is visible),
            then sync our toolbar button highlight to match its final state.
            """
            try:
                plots_widget._btn_grillage.click()
                self._sync_btn_to(
                    self._btn_grillage,
                    plots_widget._btn_grillage.isChecked()
                )
            except Exception:
                pass

        # ── Node ─────────────────────────────────────────────────────────────
        def _plots_toggle_node():
            """Same for the Nodes button."""
            try:
                plots_widget._btn_nodes.click()
                self._sync_btn_to(
                    self._btn_node,
                    plots_widget._btn_nodes.isChecked()
                )
            except Exception:
                pass

        self._connect(self._btn_grillage, _plots_toggle_grillage)
        self._connect(self._btn_node,     _plots_toggle_node)
