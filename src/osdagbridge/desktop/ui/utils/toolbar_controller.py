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

• Each toolbar button is made checkable when a view is bound, with a
  green "active" highlight so the user always knows the current state.

• For 3D CAD: clicking a toolbar button reads its new checked state
  (Qt auto-toggles it on click) and **calls cb.click()** on the matching
  BridgeComponentCheckbox checkbox so that _on_click → _apply → the 3D
  context receive the update properly.  Then the toolbar button is forced
  in sync with the checkbox's final state.

• For Plots: clicking a toolbar button delegates directly to
  the MplPlotWidget's own internal checkable buttons via .click(), then
  syncs the toolbar button state from the internal button.

• reset() unchecks all managed buttons and restores them to non-checkable
  plain buttons (matching their original appearance in ToolBarWidget).
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
    _TIP_GRILLAGE = "Grillage View"
    _TIP_NODE     = "Node"

    def __init__(self, tool_bar: "ToolBarWidget") -> None:
        self._toolbar = tool_bar

        # (button, handler) pairs tracked for precise disconnection
        self._active_connections: list[tuple[QPushButton, object]] = []

        # Buttons managed by this controller (resolved once from layout)
        self._btn_grillage: QPushButton | None = self._find_button(self._TIP_GRILLAGE)
        self._btn_node: QPushButton | None     = self._find_button(self._TIP_NODE)

        # All managed buttons in one list — convenient for bulk operations
        self._managed_buttons: list[QPushButton] = [
            b for b in (self._btn_grillage, self._btn_node) if b is not None
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
        Disconnect any existing bindings, then wire Grillage and Node toolbar
        buttons to the BridgeComponentCheckbox inside *cad_widget*.

        The key fix vs the previous version
        ────────────────────────────────────
        We call **cb.click()** (not cb.setChecked()) so that Qt emits the
        clicked(checked) signal.  That propagates through _on_click() →
        _apply() → update_component_visibility() and the 3D display updates.

        After cb.click() the checkbox's isChecked() reflects the new truth;
        we then force-sync the toolbar button to match so the highlight stays
        accurate even if BridgeComponentCheckbox's logic overrides the state.
        """
        self._disconnect_all()

        # Determine current checkbox states so the toolbar button starts in sync
        def _initial_state(label: str) -> bool:
            try:
                for cb in cad_widget.component_selector._checkboxes:
                    if cb.text() == label:
                        return cb.isChecked()
            except Exception:
                pass
            return False

        self._make_checkable(self._btn_grillage, _initial_state("Grillage view"))
        self._make_checkable(self._btn_node,     _initial_state("Node"))

        # ── Grillage ─────────────────────────────────────────────────────────
        def _cad_toggle_grillage():
            """
            Qt has already toggled btn_grillage when this handler fires.
            Read the button's new state and drive the CAD checkbox to match.
            """
            want = self._btn_grillage.isChecked()
            try:
                selector = cad_widget.component_selector
                for cb in selector._checkboxes:
                    if cb.text() == "Grillage view":
                        if cb.isChecked() != want:
                            cb.click()           # emits clicked → _on_click → _apply → 3D update
                        # Force-sync button to whatever the checkbox settled on
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
                        if cb.isChecked() != want:
                            cb.click()           # emits clicked → _on_click → _apply → 3D update
                        self._sync_btn_to(self._btn_node, cb.isChecked())
                        break
            except Exception:
                pass

        self._connect(self._btn_grillage, _cad_toggle_grillage)
        self._connect(self._btn_node,     _cad_toggle_node)

    def bind_to_plots(self, plots_widget: "MplPlotWidget") -> None:
        """
        Disconnect any existing bindings, then wire Grillage and Node toolbar
        buttons to the MplPlotWidget's own internal checkable buttons.

        Delegation strategy
        ───────────────────
        The plot widget already has checkable buttons (_btn_grillage, _btn_nodes)
        with their own logic.  We proxy the click through to those buttons via
        .click() so all existing toggle / render logic still runs unchanged.

        After the proxy click the toolbar button is forced in sync with the
        internal button's state so the highlight reflects reality.
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
            Proxy the click through to MplPlotWidget._btn_grillage, then sync
            our toolbar button so its highlight matches the internal state.
            """
            try:
                plots_widget._btn_grillage.click()          # runs all plot logic
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
