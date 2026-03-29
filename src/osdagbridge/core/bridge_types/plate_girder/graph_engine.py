"""
GirderGraphEngine — Data extraction and matplotlib rendering engine for the Steel Design dialog.

Architecture
------------
This module is the single source of truth for all structural data computation and
visualisation logic. It enforces a strict UI ↔ engine boundary:

    SteelDesign (PySide6 dialog)
        │  calls engine methods to discover model, extract results, compute peaks
        │  receives plain numpy arrays and dicts in return
        ▼
    GirderGraphEngine (this module)
        │  owns the ospgrillage model reference, result cache, and girder map
        │  extracts forces / displacements from the xarray dataset
        │  draws on four matplotlib axes
        │  knows nothing about Qt widgets
        ▼
    FigureCanvas (Qt widget, owned by SteelDesign)

Key design decisions
--------------------
- Zero PySide6 imports.  Only ``matplotlib``, ``numpy``, and backend analysis classes.
- All mutable state (cached model, results, girder map) lives here, not in the dialog.
- The dialog only stores cursor/interaction state and the numpy arrays returned by
  ``extract_member_results`` — it never touches the raw xarray dataset directly.
"""

from __future__ import annotations

import numpy as np

from osdagbridge.core.bridge_types.plate_girder.analysis_results import (
    PlateGirderAnalysisResults,
)


# =============================================================================
#   MODULE-LEVEL UTILITY
# =============================================================================

def _match_length(arr: np.ndarray, target_len: int) -> np.ndarray:
    """
    Trim or zero-pad *arr* to exactly *target_len* elements.

    Used to reconcile the force array length (n_elements) with the node path
    length (n_elements + 1) after boundary padding.
    """
    n = len(arr)
    if n == target_len:
        return arr
    if n > target_len:
        return arr[:target_len]
    return np.concatenate([arr, np.zeros(target_len - n, dtype=arr.dtype)])


# =============================================================================
#   RENDERING AND DATA ENGINE
# =============================================================================

class GirderGraphEngine:
    """
    Combined data-extraction and rendering engine for the four-panel girder figure.

    Data Pipeline
    -------------
    The engine owns the complete life-cycle of structural data:

    1. ``discover_model(main_window)``  — locates the ospgrillage model.
    2. ``fetch_results()``              — calls ``model.get_results()`` and caches.
    3. ``build_girder_map()``           — discovers longitudinal girder lines from
                                          the mesh topology.
    4. ``get_girder_keys()``            — returns ordered girder identifiers.
    5. ``get_available_loadcases()``    — returns load case names from the dataset.
    6. ``extract_member_results(...)``  — extracts force and displacement arrays.
    7. ``compute_maximums(...)``        — computes peak values and their positions.

    Rendering API
    -------------
    8. ``render_plots(...)``            — draws BMD / SFD / Deflection diagrams.
    9. ``clear_axes(...)``              — resets axes before a re-render.
    10. ``show_blank_state(...)``       — placeholder when no data is available.
    11. ``draw_cursors(...)``           — overlays cursor markers in both modes.

    Attributes
    ----------
    figure : matplotlib.figure.Figure
    ax_scheme : Axes — girder support schematic.
    ax_bmd    : Axes — bending moment diagram.
    ax_sfd    : Axes — shear force diagram.
    ax_defl   : Axes — deflection diagram (y-axis inverted).
    _cached_model   : ospgrillage model or None.
    _cached_results : xarray Dataset returned by model.get_results(), or None.
    _girder_map     : dict keyed by girder identifier, each value holds element
                      ids and node path.
    """

    def __init__(self, figure, ax_scheme, ax_bmd, ax_sfd, ax_defl):
        """
        Initialise the engine with the four matplotlib axes created by the dialog.

        Parameters
        ----------
        figure    : matplotlib.figure.Figure
        ax_scheme : Axes — girder support schematic
        ax_bmd    : Axes — bending moment diagram
        ax_sfd    : Axes — shear force diagram
        ax_defl   : Axes — deflection diagram
        """
        self.figure    = figure
        self.ax_scheme = ax_scheme
        self.ax_bmd    = ax_bmd
        self.ax_sfd    = ax_sfd
        self.ax_defl   = ax_defl

        # Cursor state owned by this engine
        self._cursor_lines: list = []

        # ── Data pipeline state ───────────────────────────────────────────────
        self._cached_model:   object = None   # ospgrillage BridgeGrillageModel
        self._cached_results: object = None   # xarray Dataset from get_results()
        self._girder_map:     dict   = {}     # {key: {"elements": [...], "path": [...]}}

    # =========================================================================
    #   DATA PIPELINE — MODEL DISCOVERY
    # =========================================================================

    def discover_model(self, main_window) -> bool:
        """
        Locate the ospgrillage model from the already-completed analysis engine.

        Walks ``cad_state`` and the backend for any ``PlateGirderBridge`` or
        ``BridgeGrillageModel`` whose ``_analysis_engine`` has been populated.

        Parameters
        ----------
        main_window : QMainWindow
            The application main window, expected to expose ``cad_state`` and
            optionally ``backend``.

        Returns
        -------
        bool
            ``True`` if a model was found and cached; ``False`` otherwise.
        """
        # ── 1. Walk cad_state values ──────────────────────────────────────────
        if hasattr(main_window, 'cad_state') and main_window.cad_state:
            for val in main_window.cad_state.values():
                engine = getattr(val, '_analysis_engine', None)
                if engine is not None:
                    model = getattr(engine, 'model', None)
                    if model is not None:
                        self._cached_model = model
                        return True

                model = getattr(val, 'model', None)
                if model is not None and hasattr(model, 'get_results'):
                    self._cached_model = model
                    return True

        # ── 2. Try backend's run result or direct attribute ───────────────────
        if hasattr(main_window, 'backend') and main_window.backend:
            try:
                result = getattr(main_window.backend, 'last_run_result', None)
                if result is None and hasattr(main_window.backend, 'get_run_result'):
                    result = main_window.backend.get_run_result()

                for source in (result, main_window.backend):
                    if source is None:
                        continue
                    engine = getattr(source, '_analysis_engine', None)
                    if engine is not None:
                        model = getattr(engine, 'model', None)
                        if model is not None:
                            self._cached_model = model
                            return True
            except Exception:
                pass

        return False

    def fetch_results(self) -> bool:
        """
        Call ``model.get_results()`` and cache the resulting xarray Dataset.

        Returns
        -------
        bool
            ``True`` on success; ``False`` if the model is absent or raises.
        """
        if self._cached_model is None:
            return False
        try:
            self._cached_results = self._cached_model.get_results()
            return self._cached_results is not None
        except Exception:
            return False

    # =========================================================================
    #   DATA PIPELINE — GIRDER MAP
    # =========================================================================

    def build_girder_map(self) -> None:
        """
        Populate ``self._girder_map`` by discovering longitudinal girder lines
        from the ospgrillage mesh topology.

        The mesh stores longitudinal elements in ``Mesh_obj.z_group_to_ele``, grouped
        by z_group (one z_group = one girder line).  Elements in each group are
        sorted longitudinally by x-coordinate to form an ordered element list and
        node path.

        Resulting structure::

            self._girder_map = {
                "g1": {"elements": [ele_tag, ...], "path": [node_tag, ...]},
                "g2": {...},
                ...
            }
        """
        self._girder_map = {}

        if self._cached_model is None:
            return

        mesh      = self._cached_model.Mesh_obj
        node_spec = mesh.node_spec  # {tag: {"coordinate": [x, y, z], ...}}

        try:
            z_group_to_ele = mesh.z_group_to_ele
        except AttributeError:
            return

        def _z_coord_of_group(z_group):
            """Return z-coordinate of first node in group for left→right sorting."""
            elems = z_group_to_ele.get(z_group, [])
            if not elems:
                return 0.0
            ni = elems[0][1]
            try:
                return float(node_spec[ni]["coordinate"][2])
            except (KeyError, IndexError):
                return 0.0

        sorted_z_groups = sorted(z_group_to_ele.keys(), key=_z_coord_of_group)

        for girder_idx, z_group in enumerate(sorted_z_groups):
            raw_elems = z_group_to_ele[z_group]
            if not raw_elems:
                continue

            def _x_of_elem(elem):
                """Return x-coordinate of element's i-node for longitudinal ordering."""
                ni = elem[1]
                try:
                    return float(node_spec[ni]["coordinate"][0])
                except (KeyError, IndexError):
                    return 0.0

            sorted_elems = sorted(raw_elems, key=_x_of_elem)
            element_ids  = [int(e[0]) for e in sorted_elems]
            node_path    = [int(e[1]) for e in sorted_elems]
            node_path.append(int(sorted_elems[-1][2]))  # append j-node of last element

            girder_key = f"g{girder_idx + 1}"
            self._girder_map[girder_key] = {
                "elements": element_ids,
                "path":     node_path,
            }

    # =========================================================================
    #   DATA PIPELINE — QUERY HELPERS
    # =========================================================================

    def get_girder_keys(self) -> list:
        """Return the ordered list of girder identifier keys (e.g. ['g1', 'g2'])."""
        return list(self._girder_map.keys())

    def get_available_loadcases(self) -> list:
        """
        Return the list of load case names present in the cached results dataset.

        Returns
        -------
        list[str]
            Empty list if results are not yet cached or an error occurs.
        """
        if self._cached_results is None:
            return []
        try:
            analyzer = PlateGirderAnalysisResults(
                self._cached_results, self._cached_model
            )
            return analyzer.get_available_loadcases()
        except Exception:
            return []

    # =========================================================================
    #   DATA PIPELINE — RESULT EXTRACTION
    # =========================================================================

    def extract_member_results(
        self,
        member_key: str,
        loadcase: str,
        bmd_key: str = "Mz_i",
        sfd_key: str = "Vy_i",
        defl_key: str = "dy",
    ):
        """
        Extract x-coordinate, BMD, SFD, and deflection arrays for a given
        girder and load case directly from the cached ospgrillage results xarray.

        Parameters
        ----------
        member_key : str
            Girder identifier key, e.g. ``"g1"``.
        loadcase : str
            Load case label as stored in ``results.forces``.
        bmd_key : str
            Force component name for the moment diagram (default: ``"Mz_i"``).
        sfd_key : str
            Force component name for the shear diagram (default: ``"Vy_i"``).
        defl_key : str
            Displacement component for deflection (default: ``"dy"``).

        Returns
        -------
        tuple or None
            ``(xs, bmd_values, sfd_values, defl_values, all_data)`` where each
            array is a ``numpy.ndarray``.  Units: xs [m], forces [kN/kNm],
            deflection [mm].  Returns ``None`` on any failure.
        """
        if member_key not in self._girder_map:
            return None

        girder      = self._girder_map[member_key]
        element_ids = girder["elements"]
        node_path   = girder["path"]

        try:
            node_spec = self._cached_model.Mesh_obj.node_spec

            # ── Build x-coordinate array zeroed at the first node ─────────────
            x_raw = []
            for node_tag in node_path:
                try:
                    x_raw.append(float(node_spec[node_tag]["coordinate"][0]))
                except (KeyError, IndexError, TypeError):
                    x_raw.append(0.0)

            if not x_raw:
                return None

            x_offset = min(x_raw)
            xs = np.array([x - x_offset for x in x_raw], dtype=float)

            # ── Force extraction helper ───────────────────────────────────────
            analyzer = PlateGirderAnalysisResults(
                self._cached_results, self._cached_model
            )

            def _get_force_array(component, is_moment=False, is_force=False):
                """Extract one per-element force component for the given loadcase."""
                values = []
                try:
                    res_dict = analyzer.get_beam_element_results(
                        element_ids, loadcase, component
                    )
                    for eid in element_ids:
                        v = res_dict.get(eid)
                        if v is None:
                            v = 0.0
                        else:
                            try:
                                v = float(v)
                            except (TypeError, ValueError):
                                v = 0.0
                        values.append(v)
                except Exception:
                    values = [0.0] * len(element_ids)

                values.append(0.0)  # pad to n_elements + 1 to match node_path length
                arr = np.nan_to_num(
                    _match_length(np.array(values, dtype=float), len(xs))
                )
                if is_moment or is_force:
                    return arr / 1000.0  # N·m → kNm  or  N → kN
                return arr

            # ── Displacement extraction helper ────────────────────────────────
            disp = self._cached_results.displacements

            def _get_disp_array(component):
                """Extract per-node vertical displacement for the given loadcase (m → mm)."""
                defl_raw = []
                try:
                    disp_sel = disp.sel(Loadcase=loadcase, Component=component)
                    for node_tag in node_path:
                        try:
                            v = float(
                                disp_sel.sel(Node=node_tag).values.item()
                            ) * 1000.0  # m → mm
                            defl_raw.append(v)
                        except Exception:
                            defl_raw.append(np.nan)
                except Exception:
                    defl_raw = [np.nan] * len(node_path)

                return np.nan_to_num(
                    _match_length(np.array(defl_raw, dtype=float), len(xs))
                )

            # ── Assemble all components ───────────────────────────────────────
            all_data = {
                "Mz_i": _get_force_array("Mz_i", is_moment=True),
                "My_i": _get_force_array("My_i", is_moment=True),
                "Mx_i": _get_force_array("Mx_i", is_moment=True),
                "Vy_i": _get_force_array("Vy_i", is_force=True),
                "Vz_i": _get_force_array("Vz_i", is_force=True),
                "Fx_i": _get_force_array("Fx_i", is_force=True),
                "dy":   _get_disp_array("dy"),
                "dz":   _get_disp_array("dz"),
                "dx":   _get_disp_array("dx"),
            }

            bmd_values  = all_data.get(bmd_key,  np.zeros(len(xs)))
            sfd_values  = all_data.get(sfd_key,  np.zeros(len(xs)))
            defl_values = all_data.get(defl_key, np.zeros(len(xs)))

            print(bmd_values, "BMD VALUES")
            print(sfd_values, "SFD VALUES")
            print(defl_values, "DEFL VALUES")

            return xs, bmd_values, sfd_values, defl_values, all_data

        except Exception:
            return None

    # =========================================================================
    #   DATA PIPELINE — PEAK VALUE COMPUTATION
    # =========================================================================

    def compute_maximums(
        self,
        xs: np.ndarray,
        bmd_values: np.ndarray,
        sfd_values: np.ndarray,
        defl_values: np.ndarray,
        all_data: dict,
    ) -> dict:
        """
        Find the peak absolute values for all components and their x-positions.

        Parameters
        ----------
        xs : np.ndarray
            x-coordinate array along the girder span (m).
        bmd_values : np.ndarray
            Active bending moment array (kNm).
        sfd_values : np.ndarray
            Active shear force array (kN).
        defl_values : np.ndarray
            Active deflection array (mm).
        all_data : dict
            Dictionary mapping force component keys to data arrays.

        Returns
        -------
        dict
            Peak values and exact x-positions keyed by UI field identifiers.
            Keys: ``M_max``, ``V_max``, ``D_max``, ``x_M``, ``x_V``, ``x_D``,
            plus per-component peaks ``M_z``, ``M_y``, ``T_x``, ``V_y``, ``V_z``,
            ``F_x``, ``D_y``, ``D_z``, ``D_x`` and their ``x_<key>`` counterparts.
        """
        idx_m = int(np.argmax(np.abs(bmd_values)))
        idx_v = int(np.argmax(np.abs(sfd_values)))
        idx_d = int(np.argmax(np.abs(defl_values)))

        result = {
            "M_max": float(bmd_values[idx_m]),
            "V_max": float(sfd_values[idx_v]),
            "D_max": float(defl_values[idx_d]),
            "x_M":  float(xs[idx_m]),
            "x_V":  float(xs[idx_v]),
            "x_D":  float(xs[idx_d]),
        }

        # Per-component peaks (used by left-panel summary fields)
        comps   = ["Mz_i", "My_i", "Mx_i", "Vy_i", "Vz_i", "Fx_i", "dy", "dz", "dx"]
        ui_keys = ["M_z",  "M_y",  "T_x",  "V_y",  "V_z",  "F_x",  "D_y", "D_z", "D_x"]

        for comp, uik in zip(comps, ui_keys):
            arr     = all_data.get(comp, np.zeros(len(xs)))
            idx_max = int(np.argmax(np.abs(arr)))
            result[uik]         = float(arr[idx_max])
            result[f"x_{uik}"]  = float(xs[idx_max])

        return result

    # =========================================================================
    #   PUBLIC RENDERING API
    # =========================================================================

    def render_plots(
        self,
        xs: np.ndarray,
        bmd_values: np.ndarray,
        sfd_values: np.ndarray,
        defl_values: np.ndarray,
        canvas,
    ) -> None:
        """
        Draw the girder schematic and BMD / SFD / Deflection diagrams.

        Parameters
        ----------
        xs : np.ndarray
            x-coordinate array along the girder span (metres).
        bmd_values : np.ndarray
            Bending moment array (kNm).
        sfd_values : np.ndarray
            Shear force array (kN).
        defl_values : np.ndarray
            Deflection array (mm).
        canvas : FigureCanvasQTAgg
            The Qt canvas widget; ``canvas.draw()`` is called at the end.
        """
        # ── Girder schematic ──────────────────────────────────────────────────
        self.ax_scheme.plot([xs[0], xs[-1]], [0, 0], color='#90A4AE', linewidth=3)
        self.ax_scheme.annotate(
            "", xy=(xs[0], 0), xytext=(xs[0], -0.2),
            arrowprops=dict(arrowstyle="->", color='#90A4AE', lw=2),
        )
        self.ax_scheme.annotate(
            "", xy=(xs[-1], 0), xytext=(xs[-1], -0.2),
            arrowprops=dict(arrowstyle="->", color='#90A4AE', lw=2),
        )
        # Add 'A' and 'B' labels at girder ends
        self.ax_scheme.annotate(
            "A", xy=(xs[0], 0), xytext=(xs[0], 0.05),
            ha='center', va='bottom', fontsize=12, fontweight='bold', color='#2B2B2B',
        )
        self.ax_scheme.annotate(
            "B", xy=(xs[-1], 0), xytext=(xs[-1], 0.05),
            ha='center', va='bottom', fontsize=12, fontweight='bold', color='#2B2B2B',
        )
        self.ax_scheme.set_ylim(-0.25, 0.35)
        self.ax_scheme.axis('off')

        # Vertical node grid lines
        for ax in (self.ax_bmd, self.ax_sfd, self.ax_defl):
            for x in xs[1:-1]:
                ax.axvline(x, linestyle=":", linewidth=0.5, color="#bfbfbf", clip_on=True)
            ax.set_xlim(xs[0], xs[-1])

        for x in xs:
            self.ax_scheme.axvline(x, linestyle=":", linewidth=0.5, color="#bfbfbf")
        self.ax_scheme.set_xlim(xs[0], xs[-1])

        # ── Bending Moment Diagram ────────────────────────────────────────────
        self.ax_bmd.plot(xs, bmd_values, color='#4C72B0', linewidth=1.5)
        self.ax_bmd.fill_between(xs, bmd_values, 0, color='#4C72B0', alpha=0.25)
        self.ax_bmd.axhline(0, color='#B0BEC5', linewidth=1.0, clip_on=True)
        self.ax_bmd.set_title("Bending Moment Diagram", fontsize=11, pad=5, y=-0.25)
        self.ax_bmd.get_xaxis().set_visible(False)

        # ── Shear Force Diagram ───────────────────────────────────────────────
        self.ax_sfd.plot(xs, sfd_values, color='#4C72B0', linewidth=1.5)
        self.ax_sfd.fill_between(xs, sfd_values, 0, color='#4C72B0', alpha=0.25)
        self.ax_sfd.axhline(0, color='#B0BEC5', linewidth=1.0, clip_on=True)
        self.ax_sfd.set_title("Shear Force Diagram", fontsize=11, pad=5, y=-0.25)
        self.ax_sfd.get_xaxis().set_visible(False)

        # ── Deflection Diagram ────────────────────────────────────────────────
        self.ax_defl.plot(xs, defl_values, color='#4C72B0', linewidth=1.5)
        self.ax_defl.fill_between(xs, defl_values, 0, color='#4C72B0', alpha=0.25)
        self.ax_defl.axhline(0, color='#B0BEC5', linewidth=1.0, clip_on=True)
        if not self.ax_defl.yaxis.get_inverted():
            self.ax_defl.invert_yaxis()  # y-axis reset after clear; re-invert
        self.ax_defl.set_title("Deflection", fontsize=11, pad=5, y=-0.4)
        self.ax_defl.get_xaxis().set_visible(False)

        # Ensure minimum scaling for plots with near-zero values
        for ax, vals in zip([self.ax_bmd, self.ax_sfd], [bmd_values, sfd_values]):
            vmax = float(np.max(np.abs(vals)))
            if np.isnan(vmax) or vmax < 1e-4:
                ax.set_ylim(-1.0, 1.0)
            else:
                lim = vmax * 1.15
                ax.set_ylim(-lim, lim)

        vmax_d = float(np.max(np.abs(defl_values)))
        if np.isnan(vmax_d) or vmax_d < 1e-4:
            self.ax_defl.set_ylim(1.0, -1.0)
        else:
            lim_d = vmax_d * 1.15
            self.ax_defl.set_ylim(lim_d, -lim_d)

        canvas.draw()

    def clear_axes(self, canvas) -> None:
        """Clear all axes and restore baseline formatting before a re-render."""
        for ax in (self.ax_scheme, self.ax_bmd, self.ax_sfd, self.ax_defl):
            ax.clear()
            ax.set_facecolor('#ffffff')
            ax.grid(False)
            ax.set_yticks([])
            ax.set_ylabel("")
            ax.axis('on')

        # Schematic: frameless
        for spine in self.ax_scheme.spines.values():
            spine.set_visible(False)

        # Data axes: four visible spines as a subtle frame
        for ax in (self.ax_bmd, self.ax_sfd, self.ax_defl):
            for spine in ax.spines.values():
                spine.set_visible(True)
                spine.set_linewidth(0.8)
                spine.set_color('#cccccc')

        canvas.draw()

    def show_blank_state(self, canvas) -> None:
        """
        Show a placeholder message when no analysis results are available.
        Directs the user to run the analysis before viewing the tab.
        """
        self.clear_axes(canvas)
        for ax in (self.ax_scheme, self.ax_bmd, self.ax_sfd, self.ax_defl):
            ax.axis('off')
        self.ax_sfd.text(
            0.5, 0.5,
            "Run the analysis first to see results.",
            ha='center', va='center', transform=self.ax_sfd.transAxes,
            color='#666666', fontsize=11, style='italic',
        )
        canvas.draw()

    def draw_cursors(
        self,
        mode: str,
        cursor_x,
        current_x,
        max_dict: dict,
        canvas,
    ) -> None:
        """
        Draw vertical dashed cursor lines on the diagram axes.

        Maximum Values mode:
            Draws a separate cursor at the peak absolute-value location for each
            of the three data diagrams (BMD, SFD, Deflection).

        Scroll for Values mode:
            Draws a single shared vertical line across all four axes so the cursor
            runs continuously from the girder schematic down through every diagram.

        Parameters
        ----------
        mode : str
            Either ``"Maximum Values"`` or ``"Scroll for Values"``.
        cursor_x : float | None
            Exact cursor x-position for Scroll for Values mode.
        current_x : np.ndarray | None
            Full x-coordinate array; used to derive default cursor position.
        max_dict : dict
            Peak location dict from :meth:`compute_maximums`.
        canvas : FigureCanvasQTAgg
            Qt canvas widget; ``canvas.draw()`` is called at the end.
        """
        # Remove previous cursor lines
        for line in self._cursor_lines:
            try:
                line.remove()
            except Exception:
                pass
        self._cursor_lines = []

        if current_x is None or len(current_x) == 0:
            canvas.draw()
            return

        if mode == "Scroll for Values":
            cx = cursor_x if cursor_x is not None else float(current_x[0])
            for ax in (self.ax_scheme, self.ax_bmd, self.ax_sfd, self.ax_defl):
                self._cursor_lines.append(
                    ax.axvline(cx, color='#1f4e79', linestyle='--', linewidth=1.5, clip_on=True)
                )

        elif mode == "Maximum Values" and max_dict:
            # Three separate peak markers — one per data diagram
            self._cursor_lines.append(
                self.ax_bmd.axvline(
                    max_dict.get("x_M", 0.0),
                    color='#1f4e79', linestyle='--', linewidth=1.5, clip_on=True,
                )
            )
            self._cursor_lines.append(
                self.ax_sfd.axvline(
                    max_dict.get("x_V", 0.0),
                    color='#1f4e79', linestyle='--', linewidth=1.5, clip_on=True,
                )
            )
            self._cursor_lines.append(
                self.ax_defl.axvline(
                    max_dict.get("x_D", 0.0),
                    color='#1f4e79', linestyle='--', linewidth=1.5, clip_on=True,
                )
            )

        canvas.draw()
