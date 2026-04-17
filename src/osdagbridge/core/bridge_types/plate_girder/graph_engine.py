"""
GirderGraphEngine — Data extraction and matplotlib rendering engine for the Steel Design dialog.

Architecture
------------
This module is the single source of truth for all structural data computation and
visualisation logic.  It enforces a strict UI ↔ engine boundary:

    SteelDesign (PySide6 dialog)
        │  injects a ready PlateGirderAnalysisResults instance at construction
        ▼
    GirderGraphEngine (this module)
        │
        ├── _DataAdapter  (inner layer, private)
        │       calls _get_*_df() methods on the injected handler
        │       returns plain pandas DataFrames or None
        │       all future query() migration happens HERE and nowhere else
        │
        ├── _ArrayBuilder (inner layer, private)
        │       converts DataFrames → numpy arrays
        │       applies nodal smoothing
        │       builds x-coordinate arrays
        │
        └── Rendering layer (public)
                draws on four matplotlib axes
                calls canvas.draw()
                knows nothing about DataFrames, numpy shapes, or xarray
        ▼
    FigureCanvasQTAgg (owned by dialog, never imported here)

Key design decisions
--------------------
- Zero PySide6 imports.  Only ``matplotlib``, ``numpy``, and
  ``PlateGirderAnalysisResults`` (data source).
- No model access, no xarray, no openseespy, no ospgrillage.
- The sole data source is PlateGirderAnalysisResults._get_*_df() methods,
  wrapped inside _DataAdapter._call_*() methods.
- When query() migration is instructed, only _call_*() bodies change.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np

from osdagbridge.core.bridge_types.plate_girder.analysis_results import (
    PlateGirderAnalysisResults,
)

# =============================================================================
#   PENDING API  —  items required from analysis_results.py
# =============================================================================
#
#  The engine is intentionally blocked from extracting these values on its own.
#  Each item below is a specific change request for the analysis_results.py
#  maintainer.  When implemented, replace the corresponding stub in the
#  _DataAdapter section of this file.
#
#  [PENDING-1]  DISPLACEMENTS
#     Needed:  _get_displacements_df(load_case, girder_name, component)
#     Columns: Node (int), <component> (mm)   — one row per node
#     Impact:  Deflection panel renders blank until this exists.
#              show_blank_state() is called with the message defined in
#              _MSG_DEFL_UNAVAILABLE at the top of this file.
#
#  [PENDING-2]  NODE COORDINATES
#     Needed:  _get_girder_paths_df() to include per-node x-coordinates,
#              OR a new _get_node_coords_df(girder_name) returning
#              columns: Node (int), X (m), Y (m), Z (m)
#     Impact:  x-axis array is currently approximated as
#              np.linspace(0, length, n_nodes).  On skewed or non-uniform
#              meshes this is geometrically incorrect.
#
#  [PENDING-3]  GIRDER SELF-WEIGHT EXTRACTION
#     Needed:  _get_girder_sw_df() to accept (load_case_name) instead of
#              (girder_map, nodes) so it can be called without model access.
#     Impact:  Girder self-weight panel is skipped entirely.
#
#  MIGRATION NOTE
#     When the mentor instructs, replace every _DataAdapter._call_*() method
#     body with the equivalent result_handler.query(category, **kwargs) call.
#     No other part of this file changes.
#
# =============================================================================


# =============================================================================
#   MODULE-LEVEL CONSTANTS AND CONFIGURATION
# =============================================================================

logger = logging.getLogger(__name__)

# Set to True during development to log extracted array shapes and values.
_DEBUG_EXTRACTION: bool = False

# Message displayed in the deflection panel while PENDING-1 is unresolved.
_MSG_DEFL_UNAVAILABLE: str = (
    "Deflection unavailable — see PENDING-1 in graph_engine.py"
)

# Visual style palette — all rendering methods read from this dict exclusively.
# No hex strings or magic numbers may appear inside any method.
_STYLE: dict = {
    "line_color":      "#4C72B0",
    "bmd_line_color":  "#FF0000",
    "sfd_line_color":  "#0000FF",
    "line_width":      1.5,
    "fill_alpha":      0.25,
    "deflection_line_color": "#000000",
    "zero_line_color": "#B0BEC5",
    "zero_line_width": 1.0,
    "grid_color":      "#bfbfbf",
    "grid_width":      0.5,
    "cursor_color":    "#1f4e79",
    "cursor_width":    1.5,
    "support_color":   "#90A4AE",
    "support_width":   3.0,
    "label_color":     "#2B2B2B",
    "label_fontsize":  10,
    "title_fontsize":       11,
    "diagram_label_fontsize": 9,     # matches visual weight of 11px UI labels at matplotlib dpi
    "spine_color":         "#cccccc",
    "spine_width":         0.8,
    "reaction_fontsize":   9,
    "scale_fontsize":      8,
    "load_arrow_color":    "#2B2B2B",   # dark — contrasts against green UDL fill
    "load_arrow_lw":       1.5,
    "load_fill_color":     "#90AF13",   # Osdag green — matches app primary accent
    "load_fill_alpha":     0.40,        # slightly more opaque so green reads well
    "point_load_arrow_color": "#000000",  # stays black — intentional
    "fontfamily":          "sans-serif",
}


# =============================================================================
#   RENDERING AND DATA ENGINE
# =============================================================================

class GirderGraphEngine:
    """
    Combined data-extraction and rendering engine for the four-panel girder figure.

    The engine is structured as three clearly delineated internal layers:

    1. **_DataAdapter** — wraps every ``_get_*_df()`` call in a ``_call_*()``
       method.  This is the only layer that will change when ``query()``
       migration is instructed.

    2. **_ArrayBuilder** — converts DataFrames into numpy arrays, applies
       nodal smoothing, and builds x-coordinate arrays.

    3. **Rendering layer** — draws on the four matplotlib axes.  It calls
       ``canvas.draw()`` and knows nothing about DataFrames or numpy shapes.

    Parameters
    ----------
    figure : matplotlib.figure.Figure
        Shared matplotlib Figure owned by the dialog.
    ax_scheme : Axes
        Top panel: girder support schematic.
    ax_bmd : Axes
        Bending moment diagram.
    ax_sfd : Axes
        Shear force diagram.
    ax_defl : Axes
        Deflection diagram (y-axis inverted).
    result_handler : PlateGirderAnalysisResults
        The sole data source.  Must not be None.
    """

    def __init__(
        self,
        figure,
        ax_scheme,
        ax_bmd,
        ax_sfd,
        ax_defl,
        result_handler: Optional[PlateGirderAnalysisResults] = None,
    ) -> None:
        """
        Initialise the engine with four matplotlib axes and a result handler.

        Parameters
        ----------
        figure : matplotlib.figure.Figure
            Matplotlib Figure shared with the dialog.
        ax_scheme : Axes
            Top panel: girder support schematic.
        ax_bmd : Axes
            Bending moment diagram.
        ax_sfd : Axes
            Shear force diagram.
        ax_defl : Axes
            Deflection diagram (y-axis inverted).
        result_handler : PlateGirderAnalysisResults
            Sole data source; never None.
        """
        self.figure    = figure        # matplotlib Figure shared with the dialog
        self.ax_scheme = ax_scheme     # top panel: girder support schematic
        self.ax_bmd    = ax_bmd        # bending moment diagram
        self.ax_sfd    = ax_sfd        # shear force diagram
        self.ax_defl   = ax_defl       # deflection diagram (y-axis inverted)

        self._result_handler = result_handler  # sole data source; None only before injection
        self._cursor_lines: list = []          # active Line2D cursor overlays; cleared before each redraw

    # =========================================================================
    #   _DataAdapter — THE MIGRATION BOUNDARY
    #
    #   All _get_*_df() calls live here.  Each method wraps exactly one
    #   _get_*_df() call.  All future query() migration touches only these
    #   bodies — nothing else in this file changes.
    #
    #   Contract: return pd.DataFrame | None.
    #             None means data is unavailable — never an empty DataFrame,
    #             never a partial result.
    # =========================================================================

    def _require_handler(self, caller: str) -> bool:
        """Return True if result_handler is ready; log and return False otherwise."""
        if self._result_handler is None:
            logger.warning(
                "%s: result_handler is None — inject PlateGirderAnalysisResults "
                "before calling data methods.", caller
            )
            return False
        return True

    def _call_girder_paths(self, girder: Optional[str] = None):
        """
        Fetch the girder path table from the result handler.

        Parameters
        ----------
        girder : str, optional
            If given, return only the row for this girder name.
            If None, return all girders.

        Returns
        -------
        pd.DataFrame or None
            Columns: Girder, Start, End, Length, Nodes.
            ``None`` if the call fails or the result is empty.

        Notes
        -----
        Calls ``_result_handler._get_girder_paths_df(girder_filter=girder)``.
        Replace body with ``result_handler.query('girder_paths', girder=girder)``
        on migration.
        """
        try:
            if not self._require_handler("_call_girder_paths"): return None
            df = self._result_handler._get_girder_paths_df(girder_filter=girder)
            if df is None or df.empty:
                logger.warning(
                    "_call_girder_paths(girder=%r) returned empty/None", girder
                )
                return None
            return df
        except Exception as exc:
            logger.warning(
                "_call_girder_paths(girder=%r) failed: %s", girder, exc,
                exc_info=True,
            )
            return None

    def _call_node_coords(self, girder: str):
        """
        Fetch per-node coordinates for a girder.

        Parameters
        ----------
        girder : str
            Girder identifier, e.g. ``"G1"``.

        Returns
        -------
        pd.DataFrame or None
            Columns: Node (int), X (m), Y (m), Z (m).
            ``None`` if the call fails or the result is empty.
        """
        try:
            if not self._require_handler("_call_node_coords"): return None
            df = self._result_handler._get_node_coords_df(girder)
            if df is None or df.empty:
                logger.warning(
                    "_call_node_coords(girder=%r) returned empty/None", girder
                )
                return None
            return df
        except Exception as exc:
            logger.warning(
                "_call_node_coords(girder=%r) failed: %s", girder, exc,
                exc_info=True,
            )
            return None

    def _call_forces(self, load_case: str, girder: str, component: str):
        """
        Fetch element-wise force/moment values for one load case and one girder.

        Parameters
        ----------
        load_case : str
            Load case name as stored in the dataset.
        girder : str
            Girder identifier, e.g. ``"G1"``.
        component : str
            Force component, e.g. ``"Vy_i"`` or ``"Mz_j"``.

        Returns
        -------
        pd.DataFrame or None
            Columns: Element, ``<component> (kN)`` or ``<component> (kNm)``.
            One row per element.
            ``None`` if the call fails or the result is empty.

        Notes
        -----
        Calls ``_result_handler._get_forces_df(load_case, girder, component)``.
        Replace body with
        ``result_handler.query('forces', name=load_case, girder=girder, component=component)``
        on migration.
        """
        try:
            if not self._require_handler("_call_forces"): return None
            df = self._result_handler._get_forces_df(load_case, girder, component)
            if df is None or df.empty:
                logger.warning(
                    "_call_forces(lc=%r, girder=%r, comp=%r) returned empty/None",
                    load_case, girder, component,
                )
                return None
            return df
        except Exception as exc:
            logger.warning(
                "_call_forces(lc=%r, girder=%r, comp=%r) failed: %s",
                load_case, girder, component, exc,
                exc_info=True,
            )
            return None

    def _call_reactions(self, load_case: str, girder: Optional[str] = None):
        """
        Fetch support reactions (Ra, Rb) for a load case.

        Parameters
        ----------
        load_case : str
            Load case name as stored in the dataset.
        girder : str, optional
            Filter to a specific girder.  If None, returns all girders.

        Returns
        -------
        pd.DataFrame or None
            Columns: Girder, Ra (kN), Rb (kN).
            ``None`` if the call fails or the result is empty.

        Notes
        -----
        Calls ``_result_handler._get_reactions_df(load_case, girder_filter=girder)``.
        Replace body with
        ``result_handler.query('reactions', name=load_case, girder=girder)``
        on migration.
        """
        try:
            if not self._require_handler("_call_reactions"): return None
            df = self._result_handler._get_reactions_df(load_case, girder_filter=girder)
            if df is None or df.empty:
                logger.warning(
                    "_call_reactions(lc=%r, girder=%r) returned empty/None",
                    load_case, girder,
                )
                return None
            return df
        except Exception as exc:
            logger.warning(
                "_call_reactions(lc=%r, girder=%r) failed: %s",
                load_case, girder, exc,
                exc_info=True,
            )
            return None

    def _call_loads(self, load_case: str) -> list[dict]:
        """
        Fetch load descriptors for scheme overlay directly from the bridge object.
        Tries multiple attribute conventions used by ospgrillage load-case objects.
        """
        try:
            if not self._require_handler("_call_loads"):
                return []

            bridge = getattr(self._result_handler, "bridge", None)
            if not bridge:
                return []

            # ── Locate the load-case object ───────────────────────────────────
            lc_obj = None

            # 1) vehicle_load_cases_list
            for lc in getattr(bridge, "vehicle_load_cases_list", []):
                if getattr(lc, "name", "") == load_case:
                    lc_obj = lc
                    break

            # 2) Any *_load_case attribute on the bridge
            if lc_obj is None:
                lc_lower = load_case.lower()
                for attr in dir(bridge):
                    if not attr.endswith("_load_case"):
                        continue
                    val = getattr(bridge, attr, None)
                    if val is None:
                        continue
                    name_match = getattr(val, "name", "") == load_case
                    sw_match   = lc_lower in ("girder self weight", "self weight") \
                                 and attr == "self_weight_load_case"
                    if name_match or sw_match:
                        lc_obj = val
                        break

            # 3) Generic load_case_list
            if lc_obj is None:
                for lc in getattr(bridge, "load_case_list", []):
                    if getattr(lc, "name", "") == load_case:
                        lc_obj = lc
                        break

            if lc_obj is None:
                logger.debug("_call_loads: load case %r not found on bridge", load_case)
                return []

            # ── Resolve load-group iterable (load_groups or loads) ────────────
            raw_groups = getattr(lc_obj, "load_groups", None)
            if not raw_groups:
                raw_groups = getattr(lc_obj, "loads", None)
            if not raw_groups:
                logger.debug("_call_loads: lc_obj %r has no load_groups/loads", lc_obj)
                return []

            # ── Parse each load group ─────────────────────────────────────────
            def _px(p):
                """Return x-coordinate of a load point using common attr names."""
                for a in ("x", "x_coord", "position"):
                    v = getattr(p, a, None)
                    if v is not None:
                        return float(v)
                return None

            def _pp(p):
                """Return load magnitude using common attr names."""
                for a in ("p", "load", "magnitude", "value", "force"):
                    v = getattr(p, a, None)
                    if v is not None:
                        return float(v)
                return 0.0

            loads_out = []
            for lg in raw_groups:
                # Support both dict wrappers and direct load objects
                load = lg.get("load", lg) if isinstance(lg, dict) else lg
                cname = type(load).__name__.lower()

                # Collect defined point handles.
                # ospgrillage stores points as load_point_1 … load_point_8;
                # fall back to point1 … point4 for forward-compatibility.
                pts = []
                for i in range(1, 9):
                    p = getattr(load, f"load_point_{i}", None)
                    if p is None:
                        p = getattr(load, f"point{i}", None)
                    if p is not None and _pp(p) != 0.0:
                        px = _px(p)
                        if px is not None:
                            pts.append((px, _pp(p)))

                if ("line" in cname or "udl" in cname or "uniform" in cname) and len(pts) >= 2:
                    x0, p0 = pts[0]
                    x1, _  = pts[1]
                    loads_out.append({
                        "type": "line",
                        "x_start": min(x0, x1),
                        "x_end":   max(x0, x1),
                        "val": abs(p0) ,
                    })
                elif ("patch" in cname or "area" in cname) and len(pts) >= 4:
                    xs_pts = [p[0] for p in pts]
                    loads_out.append({
                        "type": "line",
                        "x_start": min(xs_pts),
                        "x_end":   max(xs_pts),
                        "val": abs(pts[0][1]),
                    })
                elif ("point" in cname or "nodal" in cname or "concentrated" in cname) and pts:
                    loads_out.append({"type": "point", "x": pts[0][0], "val": abs(pts[0][1])})
                elif hasattr(load, "compound_load_obj_list"):
                    gc = getattr(load, "global_coord", None)
                    gx = float(getattr(gc, "x", 0.0)) if gc else 0.0
                    for sub in getattr(load, "compound_load_obj_list", []):
                        for i in range(1, 9):
                            p = getattr(sub, f"load_point_{i}", None)
                            if p is None:
                                p = getattr(sub, f"point{i}", None)
                            if p is not None and _pp(p) != 0.0:
                                px = _px(p)
                                if px is not None:
                                    loads_out.append({
                                        "type": "point",
                                        "x": gx + px,
                                        "val": abs(_pp(p)),
                                    })
                else:
                    # Last-resort: look for direct x_start/x_end or equivalent
                    x0 = getattr(load, "x_start", getattr(load, "start_x", None))
                    x1 = getattr(load, "x_end",   getattr(load, "end_x",   None))
                    w  = getattr(load, "w", getattr(load, "load", getattr(load, "magnitude", None)))
                    if x0 is not None and x1 is not None:
                        loads_out.append({
                            "type": "line",
                            "x_start": float(x0),
                            "x_end":   float(x1),
                            "val": abs(float(w or 0)),
                        })

            logger.debug("_call_loads: lc=%r → %d loads parsed", load_case, len(loads_out))
            return loads_out

        except Exception as exc:
            logger.warning("_call_loads(lc=%r) failed: %s", load_case, exc, exc_info=True)
            return []


    def _call_envelopes(
        self,
        lc_filter: Optional[str],
        g_filter: Optional[str],
    ):
        """
        Fetch max/min envelope data for moving load cases.

        Parameters
        ----------
        lc_filter : str or None
            Substring filter applied to load-case names.
        g_filter : str or None
            Girder name filter.

        Returns
        -------
        pd.DataFrame or None
            Columns: LoadCase, Girder, Max Vy, Min Vy, Max Mz, Min Mz.
            ``None`` if the call fails or the result is empty.

        Notes
        -----
        Calls ``_result_handler._get_envelopes_df(lc_filter=lc_filter, g_filter=g_filter)``.
        Replace body with
        ``result_handler.query('envelopes', name=lc_filter, girder=g_filter)``
        on migration.
        """
        try:
            if not self._require_handler("_call_envelopes"): return None
            df = self._result_handler._get_envelopes_df(
                lc_filter=lc_filter, g_filter=g_filter
            )
            if df is None or df.empty:
                logger.warning(
                    "_call_envelopes(lc_filter=%r, g_filter=%r) returned empty/None",
                    lc_filter, g_filter,
                )
                return None
            return df
        except Exception as exc:
            logger.warning(
                "_call_envelopes(lc_filter=%r, g_filter=%r) failed: %s",
                lc_filter, g_filter, exc,
                exc_info=True,
            )
            return None

    def _call_moving_trace(self, category: str, girder: str, component: str):
        """
        Fetch the moving load trace (force vs vehicle position) for a girder.

        Parameters
        ----------
        category : str
            Vehicle category name, e.g. ``"ClassA"``.
        girder : str
            Girder identifier, e.g. ``"G1"``.
        component : str
            Force component, e.g. ``"Mz_i"``.

        Returns
        -------
        pd.DataFrame or None
            Columns: X Pos, LoadCase, ``<component> (kN/kNm)``.
            ``None`` if the call fails or the result is empty.

        Notes
        -----
        Calls ``_result_handler._get_moving_trace_df(category, girder, component)``.
        Replace body with
        ``result_handler.query('moving_trace', name=category, girder=girder, component=component)``
        on migration.
        """
        try:
            if not self._require_handler("_call_moving_trace"): return None
            df = self._result_handler._get_moving_trace_df(category, girder, component)
            if df is None or df.empty:
                logger.warning(
                    "_call_moving_trace(cat=%r, girder=%r, comp=%r) returned empty/None",
                    category, girder, component,
                )
                return None
            return df
        except Exception as exc:
            logger.warning(
                "_call_moving_trace(cat=%r, girder=%r, comp=%r) failed: %s",
                category, girder, component, exc,
                exc_info=True,
            )
            return None

    def _call_critical_state(self, category: str, component: str):
        """
        Fetch the governing critical-state row for a vehicle category and component.

        Parameters
        ----------
        category : str
            Vehicle category name, e.g. ``"ClassA"``.
        component : str
            Force component, e.g. ``"Mz_i"``.

        Returns
        -------
        pd.DataFrame or None
            Columns: Category, Component, Max Value, LoadCase, Girder.
            ``None`` if the call fails or the result is empty.

        Notes
        -----
        Calls ``_result_handler._get_critical_state_df(category, component)``.
        Replace body with
        ``result_handler.query('critical_state', name=category, component=component)``
        on migration.
        """
        try:
            if not self._require_handler("_call_critical_state"): return None
            df = self._result_handler._get_critical_state_df(category, component)
            if df is None or df.empty:
                logger.warning(
                    "_call_critical_state(cat=%r, comp=%r) returned empty/None",
                    category, component,
                )
                return None
            return df
        except Exception as exc:
            logger.warning(
                "_call_critical_state(cat=%r, comp=%r) failed: %s",
                category, component, exc,
                exc_info=True,
            )
            return None

    def _call_classify_loadcases(self) -> dict | None:
        """
        Notes
        -----
        Calls _result_handler.classify_loadcases() directly (public method).
        Replace with result_handler.query('classified_loadcases') on migration
        once that category is supported.
        """
        try:
            if not self._require_handler("_call_classify_loadcases"):
                return None
            return self._result_handler.classify_loadcases()
        except Exception as exc:
            logger.warning("_call_classify_loadcases() failed: %s", exc, exc_info=True)
            return None

    def _call_displacements(
        self, load_case: str, girder: str, component: str
    ):
        """
        Fetch per-node displacement values for a load case and girder.

        .. note::
            **PENDING-1**: ``_get_displacements_df()`` does not yet exist in
            ``analysis_results.py``.  This method always returns ``None`` and
            logs ``_MSG_DEFL_UNAVAILABLE`` until PENDING-1 is resolved.

        Parameters
        ----------
        load_case : str
            Load case name.
        girder : str
            Girder identifier.
        component : str
            Displacement component, e.g. ``"dy"``.

        Returns
        -------
        pd.DataFrame or None
            Columns: Node (int), ``<component>`` (mm).
            ``None`` if the call fails or the result is empty.

        Notes
        -----
        Replace body with
        ``result_handler.query('displacements', name=load_case, girder=girder, component=component)``
        on migration.
        """
        try:
            if not self._require_handler("_call_displacements"): return None
            df = self._result_handler._get_displacements_df(load_case, girder, component)
            if df is None or df.empty:
                logger.warning(
                    "_call_displacements(lc=%r, girder=%r, comp=%r) returned empty/None",
                    load_case, girder, component,
                )
                return None
            return df
        except Exception as exc:
            logger.warning(
                "_call_displacements(lc=%r, girder=%r, comp=%r) failed: %s",
                load_case, girder, component, exc,
                exc_info=True,
            )
            return None

    # =========================================================================
    #   _ArrayBuilder — DATAFRAME → NUMPY CONVERSION
    # =========================================================================

    @staticmethod
    def _smooth_nodal(
        v_i: list[float],
        v_j: list[float],
    ) -> np.ndarray:
        """
        Assemble a nodal-smoothed force array from per-element i-node and j-node values.

        Parameters
        ----------
        v_i : list of float
            i-node force values, one per element, in the unit already converted
            (kN or kNm).
        v_j : list of float
            j-node force values, one per element, in the same unit as ``v_i``.

        Returns
        -------
        np.ndarray
            Nodal array of length ``n_elements + 1``.

        Notes
        -----
        **Beam sign convention** — In openseespy / ospgrillage the j-node force
        is returned in the *element's local frame*, where equilibrium requires
        ``Vy_j = -Vy_i`` for a simply supported beam with no intermediate
        loads.  To obtain a *global* diagram value at the j-end we negate the
        stored j value: ``v_global_j = -v_j``.

        **Boundary conditions** — the first node value equals ``v_i[0]``
        exactly (no smoothing at the support); the last node value equals
        ``-v_j[-1]`` exactly.  Interior nodes are the arithmetic mean of the
        incoming right face value (``-v_j[k-1]``) and the outgoing left face
        value (``v_i[k]``).

        **Single-element edge case** — when there is only one element the
        array contains exactly two values: ``[v_i[0], -v_j[0]]``.  No
        averaging is performed because there is no interior node.
        """
        if not v_i:
            return np.zeros(1, dtype=float)

        if len(v_i) == 1:
            return np.array([v_i[0], -v_j[0]], dtype=float)

        nodal: list[float] = []

        # Start boundary: first element i-node, no smoothing
        nodal.append(v_i[0])

        # Interior nodes: average of right face of previous element and left
        # face of next element (both expressed in the global sense)
        for k in range(1, len(v_i)):
            v_left  = -v_j[k - 1]   # flip j-node to global sense
            v_right =  v_i[k]
            nodal.append((v_left + v_right) / 2.0)

        # End boundary: last element j-node, flipped to global sense
        nodal.append(-v_j[-1])

        return np.array(nodal, dtype=float)

    def _build_x_array(self, girder: str, n_nodes: int) -> np.ndarray:
        """
        Build the x-coordinate array for a girder span.

        Parameters
        ----------
        girder : str
            Girder identifier used to look up span length.
        n_nodes : int
            Number of nodes (elements + 1) along the girder.

        Returns
        -------
        np.ndarray
            Equispaced x-coordinates from 0 to span length, shape ``(n_nodes,)``.

        Notes
        -----
        Uses ``_get_node_coords_df()`` to retrieve exact mesh coordinates.
        Falls back to a linear approximation over the span structure length
        if nodal coordinates cannot be resolved.
        """
        df = self._call_node_coords(girder=girder)
        if df is not None and not df.empty:
            xs = df["X (m)"].to_numpy()
            if len(xs) == n_nodes:
                return xs
            else:
                logger.warning(
                    "_build_x_array: node count mismatch (%d vs %d); "
                    "falling back to linspace",
                    len(xs), n_nodes,
                )

        # Fallback to older length approximation
        path_df = self._call_girder_paths(girder=girder)
        if path_df is None or path_df.empty:
            logger.warning(
                "_build_x_array: could not fetch span for girder=%r; "
                "falling back to unit span",
                girder,
            )
            return np.linspace(0.0, 1.0, max(n_nodes, 2))

        length = float(path_df["Length"].iloc[0])
        return np.linspace(0.0, length, max(n_nodes, 2))

    def _build_force_arrays(
        self,
        load_case: str,
        girder: str,
        bmd_key: str,
        sfd_key: str,
    ):
        """
        Extract all six force components for a girder / load case and assemble
        nodal arrays via ``_smooth_nodal()``.

        Parameters
        ----------
        load_case : str
            Load case name.
        girder : str
            Girder identifier.
        bmd_key : str
            Component key for the bending moment trace, e.g. ``"Mz_i"``.
        sfd_key : str
            Component key for the shear force trace, e.g. ``"Vy_i"``.

        Returns
        -------
        tuple[np.ndarray, np.ndarray, np.ndarray, dict] or None
            ``(xs, bmd_values, sfd_values, all_data)`` where:

            - ``xs`` is the x-coordinate array (m).
            - ``bmd_values`` is the nodal BMD array (kNm).
            - ``sfd_values`` is the nodal SFD array (kN).
            - ``all_data`` maps component string keys (``"Mz_i"``, ``"Vy_i"``,
              etc.) to their nodal arrays.

            Returns ``None`` if no force data could be retrieved.

        Notes
        -----
        Each component requires two ``_call_forces()`` calls — one for the
        ``_i`` component and one for the ``_j`` component — so that
        ``_smooth_nodal()`` can average interior nodes correctly.
        """
        _COMPONENTS = [
            ("Mz_i", "Mz_j", "kNm"),
            ("My_i", "My_j", "kNm"),
            ("Mx_i", "Mx_j", "kNm"),
            ("Vy_i", "Vy_j", "kN"),
            ("Vz_i", "Vz_j", "kN"),
            ("Fx_i", "Fx_j", "kN"),
        ]

        # ── Extract i-node and j-node DataFrames for all components ──────────
        raw: dict[str, list[float]] = {}  # key → list of per-element values

        n_elements: Optional[int] = None

        for ci, cj, _unit in _COMPONENTS:
            for comp in (ci, cj):
                df = self._call_forces(load_case, girder, comp)
                if df is None:
                    raw[comp] = []
                    continue

                # The value column is the second column (index 1)
                value_col = df.columns[1]
                values = df[value_col].tolist()
                raw[comp] = [float(v) for v in values]

                if n_elements is None:
                    n_elements = len(values)

        if n_elements is None or n_elements == 0:
            logger.warning(
                "_build_force_arrays(lc=%r, girder=%r): "
                "no element data retrieved; returning None",
                load_case, girder,
            )
            return None

        n_nodes = n_elements + 1
        xs = self._build_x_array(girder, n_nodes)

        # ── Build nodal arrays for each component pair ────────────────────────
        all_data: dict[str, np.ndarray] = {}

        for ci, cj, _unit in _COMPONENTS:
            v_i = raw.get(ci, [0.0] * n_elements)
            v_j = raw.get(cj, [0.0] * n_elements)

            if raw.get(cj) == [] and raw.get(ci):
                logger.warning(
                    "_build_force_arrays: j-component %r returned None for lc=%r, girder=%r. "
                    "Diagram will be incorrect — inform analysis_results.py maintainer.",
                    cj, load_case, girder,
                )

            # Pad if shorter than expected (graceful degradation)
            if len(v_i) < n_elements:
                v_i = v_i + [0.0] * (n_elements - len(v_i))
            if len(v_j) < n_elements:
                v_j = v_j + [0.0] * (n_elements - len(v_j))

            nodal = self._smooth_nodal(v_i[:n_elements], v_j[:n_elements])

            # Trim or pad to match xs length
            if len(nodal) > len(xs):
                nodal = nodal[: len(xs)]
            elif len(nodal) < len(xs):
                nodal = np.concatenate(
                    [nodal, np.zeros(len(xs) - len(nodal), dtype=float)]
                )

            all_data[ci] = np.nan_to_num(nodal)

        # ── Select the traces the caller requested ────────────────────────────
        bmd_values = all_data.get(bmd_key, np.zeros(len(xs)))
        sfd_values = all_data.get(sfd_key, np.zeros(len(xs)))

        if _DEBUG_EXTRACTION:
            np.set_printoptions(precision=3, suppress=True, linewidth=120)
            sep = "-" * 70
            logger.debug(
                "\n%s\n"
                "  EXTRACTED RESULTS  |  girder=%s  |  loadcase=%s\n"
                "%s\n"
                "  x-coords (m)    : %s\n"
                "  n_nodes         : %d   n_elements: %d\n"
                "%s\n"
                "  Mz_i  [kNm] (BMD)  : %s\n"
                "  My_i  [kNm]        : %s\n"
                "  Mx_i  [kNm] (tor.) : %s\n"
                "  Vy_i  [kN]  (SFD)  : %s\n"
                "  Vz_i  [kN]         : %s\n"
                "  Fx_i  [kN]  (axial): %s\n"
                "%s\n"
                "  → PLOTTING: bmd_key=%r  sfd_key=%r\n"
                "    max(|BMD|) = %.3f kNm  max(|SFD|) = %.3f kN\n"
                "%s",
                sep, girder, load_case, sep,
                xs, len(xs), n_elements, sep,
                all_data.get("Mz_i"),
                all_data.get("My_i"),
                all_data.get("Mx_i"),
                all_data.get("Vy_i"),
                all_data.get("Vz_i"),
                all_data.get("Fx_i"),
                sep, bmd_key, sfd_key,
                float(np.max(np.abs(bmd_values))),
                float(np.max(np.abs(sfd_values))),
                sep,
            )

        return xs, bmd_values, sfd_values, all_data

    # =========================================================================
    #   PUBLIC API — DATA QUERIES
    # =========================================================================

    def get_girder_keys(self) -> list[str]:
        """
        Return the ordered list of girder identifier keys.

        Returns
        -------
        list[str]
            Girder names in traversal order, e.g. ``["EB1", "G1", "G2", "EB2"]``.
            Empty list if girder path data is unavailable.

        Notes
        -----
        Delegates to ``_call_girder_paths()``.  Parses the ``Girder``
        column of the returned DataFrame.
        """
        df = self._call_girder_paths()
        if df is None:
            return []
        return df["Girder"].tolist()

    def get_classified_loadcases(self) -> dict:
        """
        Return load cases grouped by category.

        Returns
        -------
        dict
            Keys ``"dead"``, ``"vehicle_static"``, ``"vehicle_moving"``,
            ``"all"``; each value is a ``list[str]``.
            All entries are guaranteed to be plain Python ``str``.
            Returns an empty structure if the result handler fails.

        Notes
        -----
        Delegates directly to
        :meth:`PlateGirderAnalysisResults.classify_loadcases`.
        """
        empty: dict = {
            "dead": [], "vehicle_static": [], "vehicle_moving": [], "all": []
        }
        try:
            raw = self._call_classify_loadcases()
            if not raw:
                return empty
            return {k: [str(lc) for lc in v] for k, v in raw.items()}
        except Exception as exc:
            logger.error(
                "get_classified_loadcases() failed: %s", exc, exc_info=True
            )
            return empty

    # =========================================================================
    #   PUBLIC API — RESULT EXTRACTION
    # =========================================================================

    def extract_reactions(self, load_case: str, girder_key: str) -> dict:
        """
        Return {'Ra': float, 'Rb': float} in kN for the given load case and girder.
        Extracts directly from the real model reactions via _call_reactions(),
        falling back to the SFD boundaries if extraction fails.
        """
        try:
            df = self._call_reactions(load_case, girder_key)
            if df is not None and not df.empty:
                row = df.iloc[0]
                return {
                    "Ra": float(abs(row["Ra (kN)"])),
                    "Rb": float(abs(row["Rb (kN)"])),
                }
        except Exception as e:
            logger.warning("extract_reactions via _call_reactions failed: %s", e)

        # Fallback to SFD boundaries
        res = self.extract_member_results(girder_key, load_case)
        if res is None:
            return {"Ra": None, "Rb": None}
        xs, bmd, sfd, defl, all_data = res
        if len(sfd) == 0:
            return {"Ra": None, "Rb": None}
            
        # Use abs() — the arrow already indicates upward direction.
        # Use sfd[-2] for Rb: the last node is often zero-padded by _smooth_nodal.
        rb_idx = -2 if len(sfd) > 2 else -1
        return {
            "Ra": float(abs(sfd[0])),
            "Rb": float(abs(sfd[rb_idx])),
        }

    def extract_loads(self, load_case: str) -> list[dict]:
        """
        Return load descriptors for the given load case.
        Delegates to _call_loads() — the sole _DataAdapter entry point.
        """
        return self._call_loads(load_case)

    def extract_member_results(
        self,
        member_key: str,
        loadcase: str,
        bmd_key: str = "Mz_i",
        sfd_key: str = "Vy_i",
    ):
        """
        Extract x-coordinate, BMD, and SFD arrays for a girder / load case.

        Parameters
        ----------
        member_key : str
            Girder identifier, e.g. ``"G1"``.
        loadcase : str
            Load case label as stored in the dataset.
        bmd_key : str
            Force component key for the bending moment trace (default ``"Mz_i"``).
        sfd_key : str
            Force component key for the shear force trace (default ``"Vy_i"``).

        Returns
        -------
        tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict] or None
            ``(xs, bmd_values, sfd_values, defl_values, all_data)`` where each
            array is a ``np.ndarray``.  Units: xs in metres, forces in kN/kNm,
            deflection in mm.
            Returns ``None`` on any failure.
        """
        try:
            result = self._build_force_arrays(loadcase, member_key, bmd_key, sfd_key)
            if result is None:
                return None
            xs, bmd_values, sfd_values, all_data = result

            defl_df = self._call_displacements(loadcase, member_key, "dy")
            if defl_df is not None and not defl_df.empty:
                defl_values = defl_df["dy"].to_numpy()
                all_data["dy"] = defl_values
            else:
                defl_values = np.zeros_like(xs)

            return xs, bmd_values, sfd_values, defl_values, all_data
        except Exception as exc:
            logger.error(
                "extract_member_results(member=%r, lc=%r) failed: %s",
                member_key, loadcase, exc,
                exc_info=True,
            )
            return None

    # =========================================================================
    #   PUBLIC API — PEAK VALUE COMPUTATION
    # =========================================================================

    def compute_maximums(
        self,
        xs: np.ndarray,
        bmd_values: np.ndarray,
        sfd_values: np.ndarray,
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
        all_data : dict
            Dictionary mapping force component keys to nodal arrays.

        Returns
        -------
        dict
            Peak values and exact x-positions keyed by UI field identifiers.
            Keys: ``M_max``, ``V_max``, ``D_max``, ``x_M``, ``x_V``, ``x_D``,
            plus per-component peaks ``M_z``, ``M_y``, ``T_x``, ``V_y``,
            ``V_z``, ``F_x``, ``D_y``, ``D_z``, ``D_x`` and their ``x_<key>`` counterparts.
        """
        idx_m = int(np.argmax(np.abs(bmd_values)))
        idx_v = int(np.argmax(np.abs(sfd_values)))

        result: dict = {
            "M_max": float(bmd_values[idx_m]),
            "V_max": float(sfd_values[idx_v]),
            "x_M":  float(xs[idx_m]),
            "x_V":  float(xs[idx_v]),
        }

        if "dy" in all_data:
            idx_d = int(np.argmax(np.abs(all_data["dy"])))
            result["D_max"] = float(all_data["dy"][idx_d])
            result["x_D"] = float(xs[idx_d])

        # Per-component peaks (used by left-panel summary fields)
        comps   = ["Mz_i", "My_i", "Mx_i", "Vy_i", "Vz_i", "Fx_i", "dy"]
        ui_keys = ["M_z",  "M_y",  "T_x",  "V_y",  "V_z",  "F_x",  "D_y"]

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
        canvas,
        reactions=None,
        loads=None,
        defl_values=None,
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
        canvas : FigureCanvasQTAgg
            The Qt canvas widget; ``canvas.draw()`` is called at the end.

        Raises
        ------
        Exception
            Any matplotlib drawing error is caught, logged at ERROR level,
            and a blank state is displayed in its place.
        """
        try:
            self._render_scheme(xs, reactions=reactions, loads=loads)
            self._render_diagram(
                self.ax_bmd, xs, -bmd_values, "Bending Moment Diagram (kNm)",
                show_xaxis=True, color=_STYLE["bmd_line_color"],
                symmetric_ticks=True,
            )
            self._render_diagram(
                self.ax_sfd, xs, sfd_values, "Shear Force Diagram (kN)",
                show_xaxis=True, color=_STYLE["sfd_line_color"],
                symmetric_ticks=True,
            )
            
            if defl_values is not None:
                self._render_deflection_diagram(
                    self.ax_defl, xs, defl_values, "Deflection (mm)", show_xaxis=True
                )
            else:
                _zero = np.zeros_like(xs)
                self._render_deflection_diagram(
                    self.ax_defl, xs, _zero, "Deflection (mm) \u2014 unavailable", show_xaxis=True
                )
            
            # X-axis scale on all data panels — same nice intervals, aligned columns
            for _ax in (self.ax_bmd, self.ax_sfd, self.ax_defl):
                self._render_x_scale(_ax, xs)
                
            canvas.draw()
        except Exception as exc:
            logger.error("render_plots() failed: %s", exc, exc_info=True)
            self.show_blank_state(canvas)

    def _render_scheme(self, xs: np.ndarray, reactions=None, loads=None) -> None:
        """
        Draw the girder support schematic on ``ax_scheme``.

        Parameters
        ----------
        xs : np.ndarray
            x-coordinate array; xs[0] = start support, xs[-1] = end support.
        reactions : dict or None
            {'Ra': float, 'Rb': float} in kN — shown inline with A/B labels.
        loads : list[dict] or None
            Load descriptors from _call_loads(); drawn above the chord as
            filled rectangles (UDL) or downward arrows (point loads).
        """
        ax = self.ax_scheme
        span = float(xs[-1] - xs[0])

        # ── Girder chord ──────────────────────────────────────────────────────
        ax.plot(
            [xs[0], xs[-1]], [0, 0],
            color=_STYLE["support_color"],
            linewidth=_STYLE["support_width"],
            zorder=3,
        )

        # ── Y-layout constants ────────────────────────────────────────────────
        # Visual stack (top → bottom):
        #   y_label  (A / B text)
        #   arrow_top  (top of UDL fill / point-load arrow base)
        #   y_chord  (girder chord line)
        #   y_arrow_base  (tip of upward support arrows)
        #   y_arrow_base - 0.06  (reaction value text)
        y_chord       =  0.0
        arrow_top     =  0.50   # top of UDL fill block (raised for visual space)
        y_label       =  0.64   # A/B label sits above the entire load block
        y_arrow_base  = -0.55   # base of support arrows — longer shaft
        arrow_bot     =  0.15    # raised above chord — v-marker tip extends ~0.05 below center, stays above y=0

        # ── Support upward arrows ─────────────────────────────────────────────
        for x in (xs[0], xs[-1]):
            ax.annotate(
                "", xy=(x, y_chord), xytext=(x, y_arrow_base),
                arrowprops=dict(
                    arrowstyle="-|>",
                    color=_STYLE["support_color"],
                    lw=2.0,
                    mutation_scale=10,          # smaller head so shaft looks longer
                ),
                annotation_clip=False,
            )

        # ── A / B labels with separate reaction value line ────────────────────
        ra = reactions.get("Ra") if reactions else None
        rb = reactions.get("Rb") if reactions else None
        for x, label, val in ((xs[0], "A", ra), (xs[-1], "B", rb)):
            # Line 1: "A" or "B" label (normal weight to match 11px UI text)
            ax.text(
                x, y_label,
                label,
                ha="center", va="bottom",
                fontsize=_STYLE["label_fontsize"],
                fontweight="normal",          # was "bold"
                color=_STYLE["label_color"],
                fontfamily=_STYLE.get("fontfamily", "sans-serif"),
                clip_on=False,
                zorder=5,
            )
            # Line 2: reaction value below the support arrow (only when available)
            if val is not None:
                ax.text(
                    x, y_arrow_base - 0.06,
                    f"{abs(val):.1f} kN",
                    ha="center", va="top",
                    fontsize=_STYLE["reaction_fontsize"],
                    fontweight="normal",
                    color=_STYLE["label_color"],
                    fontfamily=_STYLE.get("fontfamily", "sans-serif"),
                    clip_on=False,
                    zorder=5,
                )

        # ── Load overlays ─────────────────────────────────────────────────────
        if loads:
            fill_h = arrow_top - y_chord   # height of UDL fill block

            # ── Separate point loads from line loads ──────────────────────────
            point_loads = [ld for ld in loads if ld.get("type") == "point"]
            line_loads  = [ld for ld in loads
                          if ld.get("type") == "line"
                          and ld.get("x_start") is not None
                          and ld.get("x_end") is not None]

            # ── Draw ONE merged fill for all line loads ───────────────────────
            # Multiple overlapping load groups (e.g. girder self weight) used to
            # stack transparent fills, producing a darker tint.  Drawing a single
            # fill_between for the overall envelope eliminates this artefact.
            if line_loads:
                merged_x0 = min(ld["x_start"] for ld in line_loads)
                merged_x1 = max(ld["x_end"]   for ld in line_loads)

                # Single fill — consistent colour regardless of how many
                # load groups the bridge object returns.
                ax.fill_between(
                    [merged_x0, merged_x1],
                    [y_chord, y_chord],
                    [arrow_top, arrow_top],
                    color=_STYLE["load_fill_color"],
                    alpha=_STYLE["load_fill_alpha"],
                    linewidth=0,
                    zorder=2,
                )
                # Top border
                ax.plot(
                    [merged_x0, merged_x1],
                    [arrow_top, arrow_top],
                    color=_STYLE["load_arrow_color"],
                    linewidth=1.2,
                    zorder=3,
                )

                # Downward arrows evenly spaced across the merged span
                n_arr = max(2, min(10, int(abs(merged_x1 - merged_x0) / span * 12 + 0.5)))
                for xi in np.linspace(merged_x0, merged_x1, n_arr):
                    ax.plot(
                        [xi, xi], [arrow_top, arrow_bot],
                        color=_STYLE["load_arrow_color"],
                        linewidth=0.8,
                        zorder=5,
                        clip_on=False,
                    )
                    ax.plot(
                        xi, arrow_bot,
                        marker='v',
                        markersize=4,
                        color=_STYLE["load_arrow_color"],
                        zorder=5,
                        clip_on=False,
                    )

            # ── Point loads (unchanged) ───────────────────────────────────────
            for ld in point_loads:
                x = ld.get("x")
                if x is None:
                    continue
                ax.plot(
                    [x, x], [arrow_top, arrow_bot],
                    color=_STYLE["point_load_arrow_color"],
                    linewidth=_STYLE["load_arrow_lw"],
                    zorder=6,
                    clip_on=False,
                )
                ax.plot(
                    x, arrow_bot,
                    marker='v',
                    markersize=6,
                    color=_STYLE["point_load_arrow_color"],
                    zorder=6,
                    clip_on=False,
                )

        # ── Axis limits and frame ─────────────────────────────────────────────
        pad = span * 0.06
        ax.set_xlim(xs[0] - pad, xs[-1] + pad)
        ax.set_ylim(-0.80, 0.82)
        ax.axis("off")

    def _render_diagram(
        self,
        ax,
        xs: np.ndarray,
        values: np.ndarray,
        title: str,
        show_xaxis: bool = False,
        color: str | None = None,
        symmetric_ticks: bool = False,
    ) -> None:
        """
        Draw a single force/moment diagram (line + fill + zero line + title).

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            Target axes.
        xs : np.ndarray
            x-coordinate array (m).
        values : np.ndarray
            Ordinate values (kN or kNm).
        title : str
            Subtitle displayed below the axes.
        """
        _color = color or _STYLE["line_color"]
        ax.plot(
            xs, values,
            color=_color,
            linewidth=_STYLE["line_width"],
        )
        ax.fill_between(
            xs, values, 0,
            color=_color,
            alpha=_STYLE["fill_alpha"],
        )
        ax.axhline(
            0,
            color=_STYLE["zero_line_color"],
            linewidth=_STYLE["zero_line_width"],
            clip_on=True,
            zorder=2,
        )
        # Vertical node grid lines (restored — drawn at x-tick positions)
        ax.xaxis.grid(
            True,
            color=_STYLE["grid_color"],
            linewidth=_STYLE["grid_width"],
            linestyle="--",
            zorder=1,
        )
        ax.set_axisbelow(True)
        ax.set_xlabel(
            title,
            fontsize=_STYLE["diagram_label_fontsize"],
            fontweight="normal",
            color=_STYLE["label_color"],
            labelpad=8,
        )
        if not show_xaxis:
            ax.get_xaxis().set_visible(False)

        # y-axis scaling — ensure a nonzero range
        vmax = float(np.max(np.abs(values))) if values.size else 0.0
        if np.isnan(vmax) or vmax < 1e-4:
            ax.set_ylim(-1.0, 1.0)
        else:
            lim = vmax * 1.15
            ax.set_ylim(-lim, lim)

        self._annotate_y_extremes(ax, values, symmetric=symmetric_ticks)

    def _render_deflection_diagram(
        self,
        ax,
        xs: np.ndarray,
        values: np.ndarray,
        title: str,
        show_xaxis: bool = False,
    ) -> None:
        ax.plot(
            xs, values,
            color=_STYLE["deflection_line_color"],
            linewidth=_STYLE["line_width"],
        )
        ax.axhline(
            0,
            color=_STYLE["zero_line_color"],
            linewidth=_STYLE["zero_line_width"],
            clip_on=True,
            zorder=2,
        )
        # Vertical node grid lines
        ax.xaxis.grid(
            True,
            color=_STYLE["grid_color"],
            linewidth=_STYLE["grid_width"],
            linestyle="--",
            zorder=1,
        )
        ax.set_axisbelow(True)
        ax.set_xlabel(
            title,
            fontsize=_STYLE["diagram_label_fontsize"],
            fontweight="normal",
            color=_STYLE["label_color"],
            labelpad=8,
        )
        if not show_xaxis:
            ax.get_xaxis().set_visible(False)

        # y-axis scaling — ensure a nonzero range
        vmax = float(np.max(np.abs(values))) if values.size else 0.0
        if np.isnan(vmax) or vmax < 1e-4:
            ax.set_ylim(-1.0, 1.0)
        else:
            lim = vmax * 1.15
            ax.set_ylim(-lim, lim)

        self._annotate_y_extremes(ax, values)

    def _annotate_y_extremes(self, ax, values: np.ndarray, symmetric: bool = False) -> None:
        """
        Annotate the y-axis with three reference ticks: the data maximum,
        zero, and the data minimum.  Positioned in data space using
        matplotlib's y-tick system so labels never clip and always align
        with the actual plotted values.

        When *symmetric* is True (used for SFD), the min tick is forced
        to be the negative of the max, and both are always displayed
        regardless of the deduplication threshold.
        """
        if values.size == 0:
            return

        if symmetric:
            abs_max = float(np.max(np.abs(values)))
            vmax = abs_max
            vmin = -abs_max
        else:
            vmax = float(np.max(values))
            vmin = float(np.min(values))

        # Skip when range is effectively zero (all-zero deflection placeholder)
        if abs(vmax - vmin) < 1e-6:
            return

        if symmetric:
            # Symmetric mode (SFD): always show +max, 0, -max — no dedup
            ticks  = [vmax, 0.0, vmin]
            labels = [f"{vmax:.1f}", "0.0", f"{vmin:.1f}"]
        else:
            # Build tick list with deduplication for non-symmetric diagrams
            ticks  = []
            labels = []

            def _add(val):
                for existing in ticks:
                    if abs(existing - val) < abs(vmax - vmin) * 0.05:
                        return  # skip near-duplicate
                ticks.append(val)
                labels.append(f"{val:.1f}")

            _add(vmax)
            _add(0.0)
            _add(vmin)

        ax.set_yticks(ticks)
        ax.set_yticklabels(
            labels,
            fontsize=_STYLE["scale_fontsize"],
            color=_STYLE["label_color"],
            fontfamily=_STYLE.get("fontfamily", "sans-serif"),
        )
        ax.tick_params(
            axis="y",
            direction="out",
            length=3,
            width=0.6,
            color=_STYLE["spine_color"],
            pad=3,
        )
        ax.yaxis.set_visible(True)

    def _render_x_scale(self, ax, xs: np.ndarray) -> None:
        """
        Place x-axis ticks at human-friendly round-number intervals.
        Selects the interval from [1, 2, 5, 10, 20, 25, 50] m such that
        4–6 ticks appear for any span.  First and last span positions are
        always shown.  Tick labels: '0 m', '10 m', etc.
        """
        if len(xs) == 0:
            return

        import math

        span      = float(xs[-1] - xs[0])
        x_start   = float(xs[0])
        x_end     = float(xs[-1])

        # Pick smallest "nice" step that produces at most 6 intervals
        nice_steps = [1, 2, 5, 10, 20, 25, 50]
        step = nice_steps[-1]                       # safe default
        for s in nice_steps:
            if span / s <= 6:
                step = s
                break

        # Build ticks from the first multiple of step >= x_start
        first = math.ceil(x_start / step) * step
        ticks = []
        t = first
        while t <= x_end + 1e-9:
            ticks.append(round(t, 9))
            t += step

        # Always include span endpoints
        if not ticks or abs(ticks[0] - x_start) > 1e-6:
            ticks.insert(0, x_start)
        if not ticks or abs(ticks[-1] - x_end) > 1e-6:
            ticks.append(x_end)

        # Deduplicate and sort
        ticks = sorted(set(round(v, 6) for v in ticks))

        # Format labels
        all_int = all(abs(v - round(v)) < 1e-6 for v in ticks)
        fmt     = "{:.0f} m" if all_int else "{:.1f} m"

        ax.set_xticks(ticks)
        ax.set_xticklabels(
            [fmt.format(t) for t in ticks],
            fontsize=_STYLE["scale_fontsize"],
            color=_STYLE["label_color"],
            fontfamily=_STYLE.get("fontfamily", "sans-serif"),
        )
        ax.tick_params(axis="x", direction="out", length=4,
                       color=_STYLE["spine_color"])
        ax.xaxis.set_visible(True)
        ax.set_xlim(x_start, x_end)

    def _render_blank_axis(self, ax, message: str, title: str = "") -> None:
        """
        Render a single axis as a blank panel with a centred italic message.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            Target axes to blank out.
        message : str
            Text to display, centred in the axes.
        title : str, optional
            Subtitle shown below the axes.
        """
        ax.axis("off")
        ax.text(
            0.5, 0.5,
            message,
            ha="center", va="center",
            transform=ax.transAxes,
            color="#666666",
            fontsize=_STYLE["title_fontsize"],
            style="italic",
        )
        if title:
            ax.set_title(
                title,
                fontsize=_STYLE["title_fontsize"],
                pad=5,
                y=-0.4,
            )

    def clear_axes(self, canvas) -> None:
        """
        Clear all four axes and restore baseline formatting before a re-render.

        Parameters
        ----------
        canvas : FigureCanvasQTAgg
            Qt canvas widget; ``canvas.draw()`` is called at the end.
        """
        for ax in (self.ax_scheme, self.ax_bmd, self.ax_sfd, self.ax_defl):
            ax.clear()
            ax.set_facecolor("#ffffff")
            # NOTE: do NOT call ax.grid(False) here — each _render_diagram
            # call re-enables the x-axis grid; clearing is sufficient.
            ax.set_yticks([])
            ax.set_ylabel("")
            ax.axis("on")

        # Schematic: frameless
        for spine in self.ax_scheme.spines.values():
            spine.set_visible(False)

        # Data axes: subtle frame
        for ax in (self.ax_bmd, self.ax_sfd, self.ax_defl):
            for spine in ax.spines.values():
                spine.set_visible(True)
                spine.set_linewidth(_STYLE["spine_width"])
                spine.set_color(_STYLE["spine_color"])

        canvas.draw()

    def show_blank_state(self, canvas, message: Optional[str] = None) -> None:
        """
        Show a placeholder message on all axes when no data is available.

        Parameters
        ----------
        canvas : FigureCanvasQTAgg
            Qt canvas widget; ``canvas.draw()`` is called at the end.
        message : str, optional
            Custom message to display.  Defaults to a generic instruction
            to run the analysis first.
        """
        self.clear_axes(canvas)

        display_message = (
            message
            if message is not None
            else "Run the analysis first to see results."
        )

        for ax in (self.ax_scheme, self.ax_bmd, self.ax_sfd, self.ax_defl):
            ax.axis("off")

        self.ax_sfd.text(
            0.5, 0.5,
            display_message,
            ha="center", va="center",
            transform=self.ax_sfd.transAxes,
            color="#666666",
            fontsize=_STYLE["title_fontsize"],
            style="italic",
        )
        canvas.draw()

    def draw_cursors(
        self,
        mode: str,
        cursor_x,
        current_x: Optional[np.ndarray],
        max_dict: dict,
        canvas,
    ) -> None:
        """
        Draw vertical dashed cursor lines on the diagram axes.

        **Maximum Values mode** — draws a separate cursor at the peak
        absolute-value location for each of the three data diagrams
        (BMD, SFD).  The deflection axis receives no cursor because
        deflection data is unavailable (PENDING-1).

        **Scroll for Values mode** — draws a single shared vertical line
        across all four axes so the cursor runs continuously from the girder
        schematic down through every diagram.

        Parameters
        ----------
        mode : str
            Either ``"Maximum Values"`` or ``"Scroll for Values"``.
        cursor_x : float or None
            Exact cursor x-position for Scroll for Values mode.
        current_x : np.ndarray or None
            Full x-coordinate array; used to derive the default cursor position
            when ``cursor_x`` is not set.
        max_dict : dict
            Peak location dict from :meth:`compute_maximums`.
            Expected keys: ``"x_M"`` (BMD peak x), ``"x_V"`` (SFD peak x).
        canvas : FigureCanvasQTAgg
            Qt canvas widget; ``canvas.draw()`` is called at the end.

        Raises
        ------
        Exception
            Any error removing a stale cursor line is silently ignored.
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
                    ax.axvline(
                        cx,
                        color=_STYLE["cursor_color"],
                        linestyle="--",
                        linewidth=_STYLE["cursor_width"],
                        clip_on=True,
                    )
                )

        elif mode == "Maximum Values" and max_dict:
            # BMD peak cursor
            self._cursor_lines.append(
                self.ax_bmd.axvline(
                    max_dict.get("x_M", 0.0),
                    color=_STYLE["cursor_color"],
                    linestyle="--",
                    linewidth=_STYLE["cursor_width"],
                    clip_on=True,
                )
            )
            # SFD peak cursor
            self._cursor_lines.append(
                self.ax_sfd.axvline(
                    max_dict.get("x_V", 0.0),
                    color=_STYLE["cursor_color"],
                    linestyle="--",
                    linewidth=_STYLE["cursor_width"],
                    clip_on=True,
                )
            )
            # Deflection axis: no cursor (PENDING-1; data not available)

        canvas.draw()