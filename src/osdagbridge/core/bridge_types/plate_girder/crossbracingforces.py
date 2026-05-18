"""
CrossBracingForces
------------------
Resolves grillage analysis forces into design axial forces for the
diagonals and chords of intermediate cross bracing between adjacent
plate girders.

Supported brace types
---------------------
  X-type  Two full diagonals crossing the full width × height panel.
  K-type  Two diagonals from the TOP FLANGE of each girder converging
          at the CENTRE of the bottom chord (chevron / inverted-V).
          The top chord is optional.

Step-wise process
-----------------
  Step 1  Identify brace configuration.
          Brace type (X / K), top/bottom chord presence, and panel
          spacing are read from PlateGirderBridge.additional_inputs.

  Step 2  Compute brace geometry.
          Girder depth D, spacing s, and span L come from
          PlateGirderBridge (section_props, sizing_result,
          grillage_geometry).  Diagonal angle and length follow.

  Step 3  Call forces from analysis results.
          Vz (horizontal transverse shear) and Mx (torsion) at each
          cross-bracing station are read from PlateGirderAnalysisResults.
          Internal station-to-node mapping locates the right element;
          once analysis_results.py exposes a direct station-query API,
          that internal lookup can be replaced transparently.

  Step 4  Resolve member forces.
          Panel shear F_T and torsion Mx are converted to diagonal
          and chord axial forces using the portal-method analogy.

  Step 5  Tabulate and envelope for design.
          Forces are assembled into a full DataFrame and enveloped
          per girder pair; get_design_forces_dict() packages the
          result for the cross-bracing design module.

Geometry reference
------------------
X-type  (elevation of the transverse plane between two girders)

    G_i ──── top chord ──── G_(i+1)     y = h  (top flange level)
     │                           │
      \\                         /
       \\          D2           /
        \\                     /
    D1   ──────── X ────────       (diagonals cross at mid-panel)
        /                     \\
       /          D3            \\
      /                         \\
     │                           │
    G_i ─── bottom chord ──── G_(i+1)   y = 0  (bottom flange level)
         |<──────── s ─────────>|

    alpha_X = atan(h / s)
    L_d_X   = sqrt(s² + h²)

K-type (inverted-V / chevron)

    G_i ──── top chord ──── G_(i+1)     y = h  (optional top chord)
     │                           │
      \\                         /
       \\                       /
        \\                     /
         \\                   /          alpha_K = atan(h / (s/2))
          \\                 /           L_d_K   = sqrt((s/2)² + h²)
           ──── ─── *─── ────            centre node  (z = s/2)
     │         s/2   s/2          │
    G_i ─── bottom chord ──── G_(i+1)   y = 0

Force resolution
----------------
Both types use the PORTAL-METHOD ANALOGY (story-shear approach), which
is standard for braced-frame design:

  Panel shear F_T acts horizontally (from Vz at both brace-node girders)

    F_diag        = |F_T| / (2 · sin α)       per diagonal (from shear)
    F_chord_shear = |F_T| / (2 · tan α)       chord from shear

  where α is the diagonal angle from horizontal (alpha_X or alpha_K).

  Torsion Mx in the girders creates a force couple at the chord level:

    F_couple      = (|Mx_L| + |Mx_R|) / h
    F_chord_torsion = F_couple / 2             (top/bottom chord each carry half)
    F_diag_torsion  = F_couple / (2 · sin α)  (diagonal from torsion)

  Design forces:
    F_chord_total = F_chord_shear + F_chord_torsion
    F_diag_total  = F_diag + F_diag_torsion

  For K-type, alpha_K = atan(h / (s/2)) is steeper than alpha_X,
  resulting in larger diagonal forces for the same F_T.  If the top
  chord is absent, F_chord_shear is zero (no top chord to carry it)
  and only the torsion term contributes to chord design.

Usage
-----
    pgb = PlateGirderBridge()
    pgb.set_input(input_dict)
    pgb.design()

    results = pgb.get_result_handler()
    cb = CrossBracingForces(bridge=pgb, results=results)

    df   = cb.compute_panel_forces()        # full table
    crit = cb.get_critical_forces()         # envelope per pair
    d    = cb.get_design_forces_dict()      # for design module
    cb.print_critical_forces()
"""

from __future__ import annotations

import math
from typing import Optional

import pandas as pd

from osdagbridge.core.utils.common import (
    DEFAULT_CROSS_BRACING_SPACING,
    KEY_CROSS_BRACING_SPACING,
    KEY_CROSS_BRACING_TYPE,
    KEY_GIRDER_DEPTH,
    KEY_GIRDER_TOP_FLANGE_THICKNESS,
    KEY_GIRDER_BOTTOM_FLANGE_THICKNESS,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BRACE_X = "X"           # X-type cross bracing
BRACE_K = "K"           # K-type (inverted-V / chevron) cross bracing

# Keys used to look up chord configuration from additional_inputs
_KEY_TOP_CHORD    = "Cross Bracing Top Chord"
_KEY_BOTTOM_CHORD = "Cross Bracing Bottom Chord"


# ===========================================================================
class CrossBracingForces:
    """
    Step-wise force analysis for X-type or K-type cross bracing.

    Parameters
    ----------
    bridge : PlateGirderBridge
        Fully solved bridge (design() already called).
    results : PlateGirderAnalysisResults
        Analysis handler from bridge.get_result_handler().
    brace_type : str or None
        'X' or 'K'.  If None, read from bridge.additional_inputs
        [KEY_CROSS_BRACING_TYPE]; default 'X'.
    top_chord : bool or None
        True if a top chord connects the two girders at the top flange.
        None → read from additional_inputs.  Default True.
    bottom_chord : bool or None
        True if a bottom chord connects the two girders at the bottom
        flange.  None → read from additional_inputs.  Default True.
    cb_spacing : float or None
        Cross-bracing panel spacing (m).  None → read from inputs.
    depth_ratio : float
        Brace clear height = D × depth_ratio.  Default 0.85.
    include_edge_beams : bool
        Include EB1/EB2 edge beams in pair scanning.  Default False.
    """

    def __init__(
        self,
        bridge,
        results,
        brace_type:    Optional[str]   = None,
        top_chord:     Optional[bool]  = None,
        bottom_chord:  Optional[bool]  = None,
        cb_spacing:    Optional[float] = None,
        depth_ratio:   float = 0.85,
        include_edge_beams: bool = False,
    ):
        self.bridge = bridge
        self.results = results
        self.depth_ratio = depth_ratio
        self.include_edge_beams = include_edge_beams

        # Step 1: brace type, chord presence, panel spacing (from bridge)
        self._identify_configuration(brace_type, top_chord, bottom_chord)

        # Step 2: diagonal geometry from bridge section/sizing data
        self._init_geometry(cb_spacing)

        # Propagate deck overhang so build_girders() names edge beams correctly
        sizing = getattr(bridge, "sizing_result", None)
        if sizing is not None:
            overhang = float(getattr(sizing, "deck_overhang", 0.0) or 0.0)
            if overhang > 0 and getattr(results, "edge_dist", 0) == 0:
                results.edge_dist = overhang

    # =======================================================================
    # STEP 1 — IDENTIFY BRACE CONFIGURATION
    # =======================================================================

    def _identify_configuration(
        self,
        brace_type:   Optional[str],
        top_chord:    Optional[bool],
        bottom_chord: Optional[bool],
    ) -> None:
        """
        Determine brace type (X or K) and which chords are present.

        Priority:  argument > additional_inputs > default.
        """
        ai = getattr(self.bridge, "additional_inputs", {})

        # --- Brace type ---
        if brace_type is not None:
            raw = str(brace_type).strip().upper()
        else:
            raw = str(ai.get(KEY_CROSS_BRACING_TYPE, BRACE_X)).strip().upper()

        if raw not in (BRACE_X, BRACE_K):
            raise ValueError(
                f"Unsupported brace_type '{raw}'. Choose 'X' or 'K'."
            )
        self.brace_type: str = raw

        # --- Top chord ---
        if top_chord is not None:
            self.top_chord = bool(top_chord)
        else:
            val = ai.get(_KEY_TOP_CHORD, "Yes")
            self.top_chord = str(val).strip().lower() not in ("no", "false", "0")

        # --- Bottom chord ---
        if bottom_chord is not None:
            self.bottom_chord = bool(bottom_chord)
        else:
            val = ai.get(_KEY_BOTTOM_CHORD, "Yes")
            self.bottom_chord = str(val).strip().lower() not in ("no", "false", "0")

    # =======================================================================
    # STEP 2 — BRACE GEOMETRY
    # =======================================================================

    def _init_geometry(self, cb_spacing: Optional[float]) -> None:
        """
        Compute brace geometry from the solved bridge.

        Common quantities (both types)
        ───────────────────────────────
          h   clear brace height  = D × depth_ratio  (m)
          s   girder spacing                          (m)
          L   bridge span                             (m)

        X-type specific
        ───────────────
          alpha_X = atan(h / s)          angle of full diagonal from horizontal
          L_d_X   = sqrt(s² + h²)        full diagonal length

        K-type specific
        ───────────────
          alpha_K = atan(h / (s/2))      angle of half-diagonal from horizontal
          L_d_K   = sqrt((s/2)² + h²)    half-diagonal length
        """
        sizing = getattr(self.bridge, "sizing_result", None)
        geom   = getattr(self.bridge, "grillage_geometry", None)

        if sizing is None or geom is None:
            raise RuntimeError(
                "CrossBracingForces requires bridge.design() to have been called first."
            )

        # --- Panel spacing ---
        if cb_spacing is not None:
            self.cb_spacing = float(cb_spacing)
        else:
            ai = getattr(self.bridge, "additional_inputs", {})
            self.cb_spacing = float(
                ai.get(KEY_CROSS_BRACING_SPACING, DEFAULT_CROSS_BRACING_SPACING)
            )

        # --- Girder section dimensions (metres) ---
        inp = self.bridge.input_dict
        self.D      = float(inp[KEY_GIRDER_DEPTH])
        self.tf_top = float(inp[KEY_GIRDER_TOP_FLANGE_THICKNESS])
        self.tf_bot = float(inp[KEY_GIRDER_BOTTOM_FLANGE_THICKNESS])

        # --- Common geometry ---
        self.h = self.D * self.depth_ratio          # brace clear height (m)
        self.s = float(sizing.girder_spacing)        # girder spacing (m)
        self.L = float(geom.L)                       # bridge span (m)

        # --- Type-specific diagonal geometry ---
        if self.brace_type == BRACE_X:
            self.horiz_proj = self.s               # horizontal projection of diagonal
        else:  # K-type: diagonals go to centre of bottom chord
            self.horiz_proj = self.s / 2.0

        self.L_d      = math.sqrt(self.horiz_proj ** 2 + self.h ** 2)
        self.alpha_rad = math.atan2(self.h, self.horiz_proj)
        self.sin_alpha = math.sin(self.alpha_rad)
        self.cos_alpha = math.cos(self.alpha_rad)
        self.tan_alpha = math.tan(self.alpha_rad)

    # -----------------------------------------------------------------------
    # Private helper — station-to-node mapping
    # Locates the nearest grillage node (and its element) for each
    # cross-bracing x-position along every girder.  This detail is
    # internal to Step 3; when analysis_results.py gains a direct
    # station-query API it can be replaced without changing the interface.
    # -----------------------------------------------------------------------

    def _build_station_map(self) -> tuple[dict, dict]:
        """
        Map each cross-bracing x-station to the nearest grillage node on
        every girder, plus the element ID and which end of that element.

        Returns
        -------
        station_map : dict
            { station_x (rounded m) ->
                { girder_name ->
                    { node, element, is_i_node, actual_x } } }
        girder_map : dict
            Raw girder map from results.build_girders().
        """
        nodes, _, _  = self.results.build_grillage_connectivity()
        girder_map, _ = self.results.build_girders(verbose=False)

        # Station x-positions: 0, Δ, 2Δ, …, L
        n_int = max(1, round(self.L / self.cb_spacing))
        raw_xs = [i * self.cb_spacing for i in range(n_int + 1)]
        xs = sorted({round(min(x, self.L), 6) for x in raw_xs})
        if not xs or xs[-1] < self.L - 1e-6:
            xs.append(round(self.L, 6))
        xs = sorted(set(xs))

        station_map: dict = {}
        for sx in xs:
            key = round(sx, 3)
            station_map[key] = {}

            for g_name, g_data in girder_map.items():
                path        = g_data["path"]          # ordered node IDs
                element_map = g_data["element_map"]   # list of (eid, n1, n2)

                # Nearest node to this station x
                best = min(path, key=lambda nid: abs(nodes[nid][0] - sx))

                # Find the element and which end this node is
                # Prefer the element where the node is the i-node (start)
                # so we read forces at the beginning of the forward span
                eid, is_i = None, True
                for e, n1, n2 in element_map:
                    if n1 == best:
                        eid, is_i = e, True
                        break
                    if n2 == best:
                        eid, is_i = e, False
                        break

                if eid is not None:
                    station_map[key][g_name] = {
                        "node":     best,
                        "element":  eid,
                        "is_i_node": is_i,
                        "actual_x": round(nodes[best][0], 6),
                    }

        return station_map, girder_map

    # =======================================================================
    # STEP 3 — CALL FORCES FROM ANALYSIS RESULTS
    # =======================================================================

    def _read_component(
        self,
        lc: str,
        eid: int,
        is_i: bool,
        base: str,
    ) -> Optional[float]:
        """
        Read one force/moment component from the xarray dataset.

        Parameters
        ----------
        base : str
            Component root name without end suffix: 'Vz', 'Mx', 'Vy', etc.
            The suffix '_i' or '_j' is appended based on is_i.

        Returns
        -------
        float in raw SI units (N or Nm), or None if the component is absent.
        """
        comp = base + ("_i" if is_i else "_j")
        try:
            return float(
                self.results.ds.sel(
                    Loadcase=lc,
                    Element=eid,
                    Component=comp,
                )["forces"]
            )
        except Exception:
            return None

    def _extract_forces(
        self,
        lc: str,
        info_l: dict,
        info_r: dict,
    ) -> Optional[dict]:
        """
        Extract Vz, Mx, and Vy for the left and right girder nodes at one
        station and load case.

        Returns None if Vz is absent from the dataset for either girder
        (transverse lateral loads not yet modelled).  All returned values
        are in engineering units: kN for forces, kNm for moments.
        """
        def _kN(v):   return v / 1000.0 if v is not None else None
        def _kNm(v):  return v / 1000.0 if v is not None else None

        vz_l = _kN(self._read_component(lc, info_l["element"], info_l["is_i_node"], "Vz"))
        vz_r = _kN(self._read_component(lc, info_r["element"], info_r["is_i_node"], "Vz"))

        # Vz not yet in dataset → skip this station
        if vz_l is None or vz_r is None:
            return None

        return {
            "vz_l":  vz_l,
            "vz_r":  vz_r,
            "mx_l":  _kNm(self._read_component(lc, info_l["element"], info_l["is_i_node"], "Mx")) or 0.0,
            "mx_r":  _kNm(self._read_component(lc, info_r["element"], info_r["is_i_node"], "Mx")) or 0.0,
            "vy_l":  _kN(self._read_component(lc, info_l["element"], info_l["is_i_node"], "Vy")),
            "vy_r":  _kN(self._read_component(lc, info_r["element"], info_r["is_i_node"], "Vy")),
        }

    # =======================================================================
    # STEP 4 — RESOLVE MEMBER FORCES
    # =======================================================================

    def _resolve_forces(
        self,
        F_T_kN:      float,
        Mx_left_kNm: float,
        Mx_right_kNm: float,
    ) -> dict:
        """
        Resolve panel shear F_T and torsions Mx into member axial forces.

        Portal-method analogy (story-shear approach):
          Both diagonals share the panel shear equally — one in tension,
          one in compression.  The diagonal's VERTICAL component
          equilibrates F_T (the same formula applies to both X and K type;
          only the angle alpha differs):

            F_diag_shear  = |F_T| / (2 · sin α)
            F_chord_shear = |F_T| / (2 · tan α)   [if chord present]

          Torsion Mx in the girder creates a horizontal force couple at
          the chord level:

            F_couple       = (|Mx_L| + |Mx_R|) / h
            F_chord_torsion = F_couple / 2
            F_diag_torsion  = F_couple / (2 · sin α)

          For K-type, α = atan(h / (s/2)) → steeper → larger forces.
          If the top chord is absent, F_chord_shear is set to zero
          (no member to carry horizontal shear at the top).

        Returns
        -------
        dict with keys:
            F_diag_kN         axial force per diagonal (shear only)
            F_chord_kN        axial chord force (shear + torsion)
            F_diag_total_kN   diagonal force (shear + torsion)
        """
        if self.sin_alpha < 1e-9 or self.h < 1e-9:
            return {"F_diag_kN": 0.0, "F_chord_kN": 0.0, "F_diag_total_kN": 0.0}

        abs_FT = abs(F_T_kN)

        # --- Panel-shear component ---
        F_diag_shear = abs_FT / (2.0 * self.sin_alpha)

        # Chord carries horizontal shear only when the relevant chord is present
        if self.brace_type == BRACE_X:
            chord_present = self.top_chord or self.bottom_chord
        else:  # K-type: top chord resists horizontal shear at the top
            chord_present = self.top_chord

        F_chord_shear = (abs_FT / (2.0 * self.tan_alpha)) if chord_present else 0.0

        # --- Torsion component ---
        # Each girder's torsion Mx creates a transverse couple = Mx/h at chord level.
        # Top and bottom chords each carry half of the combined couple from both girders.
        mx_couple_kN = (abs(Mx_left_kNm) + abs(Mx_right_kNm)) / self.h
        F_chord_torsion = mx_couple_kN / 2.0
        F_diag_torsion  = mx_couple_kN / (2.0 * self.sin_alpha)

        return {
            "F_diag_kN":       round(F_diag_shear, 4),
            "F_chord_kN":      round(F_chord_shear + F_chord_torsion, 4),
            "F_diag_total_kN": round(F_diag_shear + F_diag_torsion, 4),
        }

    # =======================================================================
    # STEP 5 — TABULATE AND ENVELOPE FOR DESIGN
    # =======================================================================

    def compute_panel_forces(
        self,
        load_case_filter: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Full force table: one row per (load case, station, girder pair).

        Returns an empty DataFrame if Vz is absent from the dataset
        (transverse lateral loads not yet modelled).

        Returns
        -------
        pd.DataFrame with columns:
            LoadCase, Station X (m), Girder Pair,
            Vz Left (kN), Vz Right (kN),
            Mx Left (kNm), Mx Right (kNm),
            Vy Left (kN), Vy Right (kN), dVy (kN),
            F_T (kN), F_diag (kN), F_chord (kN), F_diag+torsion (kN)
        """
        station_map, girder_map = self._build_station_map()
        all_lcs = self.results.get_available_loadcases()

        if load_case_filter:
            all_lcs = [lc for lc in all_lcs if load_case_filter in str(lc)]

        g_order = list(girder_map.keys())
        if not self.include_edge_beams:
            g_order = [g for g in g_order if g not in ("EB1", "EB2")]

        rows = []
        for lc in all_lcs:
            lc_str = str(lc)
            for sx, g_info in sorted(station_map.items()):
                avail = [g for g in g_order if g in g_info]

                for k in range(len(avail) - 1):
                    g_l, g_r  = avail[k], avail[k + 1]
                    info_l    = g_info[g_l]
                    info_r    = g_info[g_r]

                    forces = self._extract_forces(lc, info_l, info_r)
                    if forces is None:
                        continue    # Vz absent → skip

                    vz_l = forces["vz_l"]
                    vz_r = forces["vz_r"]
                    mx_l = forces["mx_l"]
                    mx_r = forces["mx_r"]
                    vy_l = forces["vy_l"]
                    vy_r = forces["vy_r"]

                    # Net lateral panel shear: sum of Vz at both brace nodes.
                    # When both girders shear in the same direction the brace
                    # carries the full combined force; equal-and-opposite Vz
                    # (symmetric gravity) cancels, leaving only Mx to drive design.
                    F_T = vz_l + vz_r

                    resolved = self._resolve_forces(F_T, mx_l, mx_r)
                    dVy = (
                        round(abs(vy_l) - abs(vy_r), 4)
                        if vy_l is not None and vy_r is not None
                        else None
                    )

                    rows.append({
                        "LoadCase":           lc_str,
                        "Station X (m)":      sx,
                        "Girder Pair":        f"{g_l}-{g_r}",
                        "Vz Left (kN)":       round(vz_l, 4),
                        "Vz Right (kN)":      round(vz_r, 4),
                        "Mx Left (kNm)":      round(mx_l, 4),
                        "Mx Right (kNm)":     round(mx_r, 4),
                        "Vy Left (kN)":       round(vy_l, 4) if vy_l is not None else None,
                        "Vy Right (kN)":      round(vy_r, 4) if vy_r is not None else None,
                        "dVy (kN)":           dVy,
                        "F_T (kN)":           round(F_T, 4),
                        "F_diag (kN)":        resolved["F_diag_kN"],
                        "F_chord (kN)":       resolved["F_chord_kN"],
                        "F_diag+torsion (kN)": resolved["F_diag_total_kN"],
                    })

        return pd.DataFrame(rows)

    def get_critical_forces(self) -> pd.DataFrame:
        """
        Envelope (max absolute) diagonal and chord forces across all load
        cases, per girder pair and per cross-bracing station.

        Returns
        -------
        pd.DataFrame with columns:
            Girder Pair, Station X (m),
            Max |F_diag+torsion| (kN), Governing LC (diag),
            Max |F_chord| (kN),        Governing LC (chord)
        """
        df = self.compute_panel_forces()
        if df.empty:
            return pd.DataFrame()

        diag_col  = "F_diag+torsion (kN)"
        chord_col = "F_chord (kN)"
        rows = []
        for (pair, sx), grp in df.groupby(["Girder Pair", "Station X (m)"]):
            idx_d = grp[diag_col].abs().idxmax()
            idx_c = grp[chord_col].abs().idxmax()
            rows.append({
                "Girder Pair":              pair,
                "Station X (m)":            sx,
                "Max |F_diag+torsion| (kN)": round(abs(grp.loc[idx_d, diag_col]), 3),
                "Governing LC (diag)":       grp.loc[idx_d, "LoadCase"],
                "Max |F_chord| (kN)":        round(abs(grp.loc[idx_c, chord_col]), 3),
                "Governing LC (chord)":      grp.loc[idx_c, "LoadCase"],
            })
        return pd.DataFrame(rows)

    def get_design_forces_dict(self) -> dict:
        """
        Structured dict of governing design forces for the design module.

        Per girder pair, takes the WORST station across all stations
        (governing diagonal force and governing chord force may come from
        different stations and load cases).

        Returns
        -------
        dict::

            {
                "brace_type":    "X" or "K",
                "top_chord":     bool,
                "bottom_chord":  bool,
                "geometry": {
                    "girder_spacing_m":  float,
                    "brace_height_m":    float,
                    "girder_depth_m":    float,
                    "diagonal_length_m": float,
                    "alpha_deg":         float,
                    "cb_spacing_m":      float,
                    "depth_ratio":       float,
                },
                "pairs": {
                    "G1-G2": {
                        "max_diagonal_kN":          float,
                        "governing_lc_diag":        str,
                        "critical_station_diag_m":  float,
                        "max_chord_kN":             float,
                        "governing_lc_chord":       str,
                        "critical_station_chord_m": float,
                    },
                    ...
                },
                "overall_max_diagonal_kN": float,
                "overall_max_chord_kN":    float,
            }

        Returns an empty dict when Vz is not yet in the dataset.
        """
        crit = self.get_critical_forces()
        if crit.empty:
            return {}

        # Collapse to one row per girder pair (worst station for each force)
        worst: dict = {}
        for _, row in crit.iterrows():
            pair = row["Girder Pair"]
            f_d  = row["Max |F_diag+torsion| (kN)"]
            f_c  = row["Max |F_chord| (kN)"]
            sx   = row["Station X (m)"]
            lc_d = row["Governing LC (diag)"]
            lc_c = row["Governing LC (chord)"]

            if pair not in worst:
                worst[pair] = {
                    "max_diagonal_kN":          f_d,
                    "governing_lc_diag":        lc_d,
                    "critical_station_diag_m":  sx,
                    "max_chord_kN":             f_c,
                    "governing_lc_chord":       lc_c,
                    "critical_station_chord_m": sx,
                }
            else:
                if f_d > worst[pair]["max_diagonal_kN"]:
                    worst[pair]["max_diagonal_kN"]         = f_d
                    worst[pair]["governing_lc_diag"]       = lc_d
                    worst[pair]["critical_station_diag_m"] = sx
                if f_c > worst[pair]["max_chord_kN"]:
                    worst[pair]["max_chord_kN"]              = f_c
                    worst[pair]["governing_lc_chord"]        = lc_c
                    worst[pair]["critical_station_chord_m"]  = sx

        return {
            "brace_type":             self.brace_type,
            "top_chord":              self.top_chord,
            "bottom_chord":           self.bottom_chord,
            "geometry":               self.get_brace_geometry_info(),
            "pairs":                  worst,
            "overall_max_diagonal_kN": max(v["max_diagonal_kN"] for v in worst.values()),
            "overall_max_chord_kN":    max(v["max_chord_kN"]    for v in worst.values()),
        }

    def get_brace_geometry_info(self) -> dict:
        """Return geometry parameters as a dict (for reporting and design module)."""
        return {
            "brace_type":        self.brace_type,
            "top_chord":         self.top_chord,
            "bottom_chord":      self.bottom_chord,
            "girder_spacing_m":  round(self.s, 4),
            "brace_height_m":    round(self.h, 4),
            "girder_depth_m":    round(self.D, 4),
            "diagonal_length_m": round(self.L_d, 4),
            "horiz_proj_m":      round(self.horiz_proj, 4),
            "alpha_deg":         round(math.degrees(self.alpha_rad), 2),
            "cb_spacing_m":      round(self.cb_spacing, 3),
            "depth_ratio":       self.depth_ratio,
        }

    # =======================================================================
    # PRINT / REPORT METHODS
    # =======================================================================

    def print_configuration(self) -> None:
        """Print brace configuration and geometry."""
        g = self.get_brace_geometry_info()
        print("\n" + "=" * 70)
        print(" " * 18 + "CROSS BRACING CONFIGURATION & GEOMETRY")
        print("=" * 70)
        print(f"  Brace type               : {g['brace_type']}-type")
        print(f"  Top chord                : {'Yes' if g['top_chord'] else 'No'}")
        print(f"  Bottom chord             : {'Yes' if g['bottom_chord'] else 'No'}")
        print("-" * 70)
        print(f"  Girder spacing (s)       : {g['girder_spacing_m']:.4f} m")
        print(f"  Girder depth (D)         : {g['girder_depth_m']:.4f} m")
        print(f"  Brace clear height (h)   : {g['brace_height_m']:.4f} m  "
              f"(depth_ratio = {g['depth_ratio']})")
        if g["brace_type"] == BRACE_K:
            print(f"  Diag. horiz. projection  : {g['horiz_proj_m']:.4f} m  (= s/2)")
        print(f"  Diagonal length          : {g['diagonal_length_m']:.4f} m")
        print(f"  Diagonal angle (alpha)   : {g['alpha_deg']:.2f} deg from horizontal")
        print(f"  Panel spacing            : {g['cb_spacing_m']:.3f} m")
        print("=" * 70)

    def print_panel_forces(
        self,
        load_case_filter: Optional[str] = None,
        max_rows: int = 200,
    ) -> None:
        """Print the full panel-force table (all load cases, stations, pairs)."""
        self.print_configuration()
        df = self.compute_panel_forces(load_case_filter=load_case_filter)
        print("\n" + "=" * 115)
        print(" " * 37 + "CROSS BRACING PANEL FORCES")
        print("=" * 115)
        if df.empty:
            print("  No data — Vz (transverse shear) not yet in dataset, or no load cases found.")
        else:
            print(df.head(max_rows).to_string(index=False))
            if len(df) > max_rows:
                print(f"\n  ... ({len(df) - max_rows} rows omitted; increase max_rows)")
        print("=" * 115)

    def print_critical_forces(self) -> None:
        """Print the design-critical force envelope per girder pair and station."""
        self.print_configuration()
        df = self.get_critical_forces()
        print("\n" + "=" * 115)
        print(" " * 28 + "CROSS BRACING — CRITICAL DESIGN FORCES")
        print("=" * 115)
        if df.empty:
            print("  No critical forces — Vz not in dataset or no load cases found.")
        else:
            print(df.to_string(index=False))
        print("=" * 115)

    def print_station_summary(self, station_x: float, tol: float = 0.5) -> None:
        """
        Print forces for a single cross-bracing station.

        Parameters
        ----------
        station_x : float   Nominal x-position (m).
        tol : float         Search tolerance in metres (default 0.5).
        """
        df = self.compute_panel_forces()
        if df.empty:
            print("No data available.")
            return
        subset = df[(df["Station X (m)"] - station_x).abs() <= tol]
        print(f"\n--- Cross-Bracing Station: x ~ {station_x:.2f} m ---")
        if subset.empty:
            print(f"  No station within ±{tol:.2f} m of x = {station_x:.2f} m.")
        else:
            print(subset.to_string(index=False))
