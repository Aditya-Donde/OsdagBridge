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
          Girder depth D and spacing s come from PlateGirderBridge
          (section_props, sizing_result).  Diagonal angle and length follow.

  Step 3  Read Vz from the cross-bracing (transverse) members.
          The grillage forces are in global axes.  Cross-bracing members
          run along global Z, so Vz_i is their axial force directly.
          Vz_i at the i-end (left girder) is used; for a member with no
          distributed load Vz_i = -Vz_j, so summing both ends would
          double-count.

  Step 4  Resolve member forces.

          Resolving Vz_i along the diagonal (angle α from horizontal):

            F_diag  =  Vz_i / cos α

          Chord force equals the full vertical shear:

            F_chord  =  Vz_i

          Sign is preserved: positive → tension, negative → compression.

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
Vz of the transverse (cross-bracing) member is in the global axis,
so it is read directly — no coordinate transformation needed.

For a grillage element with no distributed load, Vz_i = -Vz_j.
Both ends carry the same force magnitude; summing them would
double-count the shear.  Vz_i (left girder end) is used.

  Resolving along the diagonal (α from horizontal):

    F_diag  =  Vz_i / cos α     (kN)

  Chord force:

    F_chord =  Vz_i              (kN)

  where
    Vz_i  (kN)  — Vz at the i-end of the cross-bracing member (left girder)
    α     (rad) — atan(h / horiz_proj)
    Sign preserved: positive = tension, negative = compression

TODO
----
  Verify sign convention: Vz_i > 0 is assumed to mean tension and
  Vz_i < 0 compression (forces reported in global axis). Confirm against
  a known result before relying on the T/C classification.

Usage
-----
    pgb = PlateGirderBridge()
    pgb.set_input(input_dict)
    pgb.design()

    cb = CrossBracingForces(bridge=pgb)

    df   = cb.compute_panel_forces()        # full table
    crit = cb.get_critical_forces()         # envelope per pair
    d    = cb.get_design_forces_dict()      # for design module
    cb.print_critical_forces()
"""

from __future__ import annotations

import copy
import json
import math
import time
import warnings
from pathlib import Path
from typing import Optional

import pandas as pd

from osdagbridge.core.utils.common import (
    KEY_MP_CB_SPACING,
    KEY_MP_CB_TYPE,
    KEY_MP_GIRDER_DEPTH,
    KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
    KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
    KEY_TS_GIRDER_SPACING,
    KEY_MP_CB_BRACING_SECTION_TYPE,
    KEY_MP_CB_TOP_CHORD,
    KEY_MP_CB_BOTTOM_CHORD,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BRACE_X = "X"
BRACE_K = "K"

# ===========================================================================
class CrossBracingForces:
    """
    Step-wise force analysis for X-type or K-type cross bracing.

    Parameters
    ----------
    bridge : PlateGirderBridge
        Fully solved bridge (design() already called).
        bridge.result_data must contain a "crossbracings" key produced by
        results_data_post_processing.post_process().
    brace_type : str or None
        'X' or 'K'.  If None, read from bridge.additional_inputs
        [KEY_MP_CB_TYPE]; default 'X'.
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
        brace_type:    Optional[str]   = None,
        top_chord:     Optional[bool]  = None,
        bottom_chord:  Optional[bool]  = None,
        cb_spacing:    Optional[float] = None,
        depth_ratio:   float = 0.85,
        include_edge_beams: bool = False,
    ):
        self.bridge = bridge
        self.depth_ratio = depth_ratio
        self.include_edge_beams = include_edge_beams

        self._identify_configuration(brace_type, top_chord, bottom_chord)
        self._init_geometry(cb_spacing)

    # =======================================================================
    # STEP 1 — IDENTIFY BRACE CONFIGURATION
    # =======================================================================

    def _identify_configuration(
        self,
        brace_type:   Optional[str],
        top_chord:    Optional[bool],
        bottom_chord: Optional[bool],
    ) -> None:
        ai = getattr(self.bridge, "additional_inputs", {})

        if brace_type is not None:
            raw = str(brace_type).strip().upper()
        else:
            # KEY_MP_CB_TYPE stores "K-Bracing" or "X-Bracing" (the pattern type)
            raw = str(ai.get(KEY_MP_CB_TYPE, "")).strip().upper()

        if raw not in (BRACE_X, BRACE_K):
            # Normalise display labels like "K-BRACING" → "K", "X-BRACING" → "X"
            if "K" in raw:
                raw = BRACE_K
            else:
                raw = BRACE_X  # default to X when unrecognised
        self.brace_type: str = raw

        if top_chord is not None:
            self.top_chord = bool(top_chord)
        else:
            val = ai.get(KEY_MP_CB_TOP_CHORD)
            self.top_chord = str(val).strip().lower() not in ("no", "false", "0")

        if bottom_chord is not None:
            self.bottom_chord = bool(bottom_chord)
        else:
            val = ai.get(KEY_MP_CB_BOTTOM_CHORD)
            self.bottom_chord = str(val).strip().lower() not in ("no", "false", "0")

    # =======================================================================
    # STEP 2 — BRACE GEOMETRY
    # =======================================================================

    def _init_geometry(self, cb_spacing: Optional[float]) -> None:
        geom = getattr(self.bridge, "grillage_geometry", None)

        if geom is None:
            raise RuntimeError(
                "CrossBracingForces requires bridge.design() to have been called first."
            )

        if cb_spacing is not None:
            self.cb_spacing = float(cb_spacing)
        else:
            ai = getattr(self.bridge, "additional_inputs", {})
            self.cb_spacing = float(
                ai.get(KEY_MP_CB_SPACING) or 3.0  # TODO: remove fallback once UI always sets spacing
            )

        # --- Girder section dimensions (metres) ---
        # Representative (first) girder; resolve_girder_value tolerates both the
        # per-girder dynamic keys and legacy scalar keys.
        from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import (
            resolve_girder_value as _gv,
        )
        inp = self.bridge.input_dict
        self.D      = float(_gv(inp, KEY_MP_GIRDER_DEPTH))
        self.tf_top = float(_gv(inp, KEY_MP_GIRDER_TOP_FLANGE_THICKNESS))
        self.tf_bot = float(_gv(inp, KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS))
        self.h = self.D * self.depth_ratio
        self.s = float(inp[KEY_TS_GIRDER_SPACING])

        if self.brace_type == BRACE_X:
            self.horiz_proj = self.s
        else:
            self.horiz_proj = self.s / 2.0

        self.L_d      = math.sqrt(self.horiz_proj ** 2 + self.h ** 2)
        self.alpha_rad = math.atan2(self.h, self.horiz_proj)
        self.cos_alpha = math.cos(self.alpha_rad)

    # =======================================================================
    # STEP 3 — BUILD CHAIN MAP FROM crossbracings
    # =======================================================================

    def _build_chain_map(self) -> list:
        """
        Read each cross-bracing chain from result_data["crossbracings"].

        left_girder, right_girder, and connection coordinates are already
        stored on each chain by results_data_post_processing.build_crossbracings
        — no re-derivation needed here.

        Returns
        -------
        chain_stations : list[dict]
            [{ "start_coords", "end_coords",
               "first_member", "last_member",
               "left_girder",  "right_girder" }, ...]
        """
        rd        = self.bridge.result_data
        cb_chains = rd.get("crossbracings", [])

        chain_stations = []
        for chain in cb_chains:
            mems = chain.get("members", [])
            if not mems:
                continue

            left_girder  = chain.get("left_girder")
            right_girder = chain.get("right_girder")
            if left_girder is None or right_girder is None:
                continue

            start = chain.get("start") or {}
            end   = chain.get("end")   or {}

            chain_stations.append({
                "start_coords": start.get("coords"),
                "end_coords":   end.get("coords"),
                "first_member": str(mems[0]),
                "last_member":  str(mems[-1]),
                "left_girder":  left_girder,
                "right_girder": right_girder,
            })

        return chain_stations

    # =======================================================================
    # STEP 3 (cont.) — READ Vz FROM TRANSVERSE MEMBER
    # =======================================================================

    def _read_vz(self, lc: str, member_id: str, is_i: bool) -> Optional[float]:
        """
        Read Vz_i or Vz_j from a transverse (cross-bracing) member.
        Forces are in global axes so Vz is used directly.

        Returns float in N, or None if absent.
        """
        comp = "Vz_i" if is_i else "Vz_j"
        try:
            return float(
                self.bridge.result_data["forces"][str(lc)][member_id][comp]
            )
        except (KeyError, TypeError, ValueError):
            return None

    # =======================================================================
    # STEP 4 — RESOLVE MEMBER FORCES
    # =======================================================================

    def _resolve_forces(self, vz_kn: float) -> dict:
        """
        Resolve Vz_i (left-girder end shear, kN) into diagonal and chord forces.

          F_diag  =  Vz_i / cos α   — axial force in diagonal
          F_chord =  Vz_i            — axial force in chord

        Sign preserved: positive = tension, negative = compression.
        """
        if self.cos_alpha < 1e-9:
            return {"F_diag_kN": 0.0, "F_chord_kN": 0.0}

        return {
            "F_diag_kN":  round(vz_kn / self.cos_alpha, 4),
            "F_chord_kN": round(vz_kn, 4),
        }

    # =======================================================================
    # STEP 5 — TABULATE AND ENVELOPE FOR DESIGN
    # =======================================================================

    def compute_panel_forces(
        self,
        load_case_filter: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Full force table: one row per (load case, cross-bracing chain).

        Returns
        -------
        pd.DataFrame with columns:
            LoadCase, Girder Pair, Vz_i (kN), Vz_j (kN), F_diag (kN), F_chord (kN)
        """
        chain_stations = self._build_chain_map()
        # Skip the "Envelope ULS"/"Envelope SLS" pseudo load cases: their values are
        # per-element copies of the governing combination, so they add no new extreme
        # but would show up as table rows and could steal the governing-LC label.
        all_lcs = [
            lc for lc in self.bridge.result_data["loadcases"]
            if not str(lc).startswith("Envelope")
        ]

        if load_case_filter:
            all_lcs = [lc for lc in all_lcs if load_case_filter in str(lc)]

        _eq_tol = 1e-3  # kN tolerance for Vz_i + Vz_j == 0 check

        rows = []
        for lc in all_lcs:
            lc_str = str(lc)
            for st in chain_stations:

                if not self.include_edge_beams:
                    if st["left_girder"] in ("EB1", "EB2") or \
                       st["right_girder"] in ("EB1", "EB2"):
                        continue

                # Vz_i of first member, Vz_j of last member (global axis)
                vz_l = self._read_vz(lc_str, st["first_member"], is_i=True)
                vz_r = self._read_vz(lc_str, st["last_member"],  is_i=False)

                if vz_l is None or vz_r is None:
                    continue

                vz_l_kn = vz_l / 1e3
                vz_r_kn = vz_r / 1e3

                # Vz_i = -Vz_j must hold for a member with no distributed load
                if abs(vz_l_kn + vz_r_kn) > _eq_tol:
                    warnings.warn(
                        f"[CrossBracingForces] Equilibrium violated — "
                        f"Member {st['first_member']} LC '{lc_str}': "
                        f"Vz_i={vz_l_kn:.4f} kN, Vz_j={vz_r_kn:.4f} kN — "
                        f"expected Vz_i = -Vz_j (diff={vz_l_kn + vz_r_kn:.4f} kN)",
                        stacklevel=2,
                    )

                resolved = self._resolve_forces(vz_l_kn)

                rows.append({
                    "LoadCase":    lc_str,
                    "Girder Pair": f"{st['left_girder']}-{st['right_girder']}",
                    "Vz_i (kN)":   round(vz_l_kn, 4),
                    "Vz_j (kN)":   round(vz_r_kn, 4),
                    "F_diag (kN)": resolved["F_diag_kN"],
                    "F_chord (kN)": resolved["F_chord_kN"],
                })

        return pd.DataFrame(rows)

    def get_critical_forces(self, forces_dict: Optional[dict] = None) -> pd.DataFrame:
        """
        Critical diagonal and chord forces per girder pair — one T row and one C
        row per pair (where those force types exist).

        Parameters
        ----------
        forces_dict : dict, optional
            Pre-computed output of get_design_forces_dict(). If None, it is
            computed here. Pass a pre-computed dict to avoid calling
            compute_panel_forces() more than once.

        Returns
        -------
        pd.DataFrame with columns:
            Girder Pair, Type, F_diag (kN), F_chord (kN), Gov LC
        """
        if forces_dict is None:
            forces_dict = self.get_design_forces_dict()
        if not forces_dict or not forces_dict.get("pairs"):
            return pd.DataFrame()

        rows = []
        for pair, vals in forces_dict["pairs"].items():
            if vals.get("diag_tension_kN") is not None:
                rows.append({
                    "Girder Pair":  pair,
                    "Type":         "T",
                    "F_diag (kN)":  vals["diag_tension_kN"],
                    "F_chord (kN)": vals.get("chord_tension_kN") or 0.0,
                    "Gov LC":       vals.get("diag_tension_gov_lc", ""),
                })
            if vals.get("diag_compression_kN") is not None:
                rows.append({
                    "Girder Pair":  pair,
                    "Type":         "C",
                    "F_diag (kN)":  -vals["diag_compression_kN"],
                    "F_chord (kN)": -(vals.get("chord_compression_kN") or 0.0),
                    "Gov LC":       vals.get("diag_compression_gov_lc", ""),
                })
        return pd.DataFrame(rows)

    def get_design_forces_dict(self) -> dict:
        """
        Design forces per girder pair — both tension and compression reported
        separately because compression governs buckling independently of magnitude.

        Returns
        -------
        dict::

            {
                "brace_type":   "X" or "K",
                "top_chord":    bool,
                "bottom_chord": bool,
                "geometry":     { ... },
                "pairs": {
                    "G1-G2": {
                        "diag_tension_kN":          float or None,
                        "diag_tension_gov_lc":      str   or None,
                        "diag_compression_kN":      float or None,
                        "diag_compression_gov_lc":  str   or None,
                        "chord_tension_kN":         float or None,
                        "chord_tension_gov_lc":     str   or None,
                        "chord_compression_kN":     float or None,
                        "chord_compression_gov_lc": str   or None,
                    },
                    ...
                },
            }
        """
        df = self.compute_panel_forces()
        if df.empty:
            return {}

        diag_col  = "F_diag (kN)"
        chord_col = "F_chord (kN)"
        # 0.005 kN = 5 N minimum — ensures round(..., 3) never produces 0.0
        _tol = 5e-3

        pairs: dict = {}
        for pair, grp in df.groupby("Girder Pair"):
            # F_diag and F_chord are proportional (same Vz_i), so idxmax/idxmin on
            # F_diag gives the governing LC for both diag and chord simultaneously.
            idx_t = grp[diag_col].idxmax()
            idx_c = grp[diag_col].idxmin()

            tens_diag  = float(grp.loc[idx_t, diag_col])
            comp_diag  = float(grp.loc[idx_c, diag_col])
            tens_chord = float(grp.loc[idx_t, chord_col])
            comp_chord = float(grp.loc[idx_c, chord_col])

            pairs[pair] = {
                "diag_tension_kN":          round(tens_diag,       3) if tens_diag  >  _tol else None,
                "diag_tension_gov_lc":      str(grp.loc[idx_t, "LoadCase"]) if tens_diag  >  _tol else None,
                "diag_compression_kN":      round(abs(comp_diag),  3) if comp_diag  < -_tol else None,
                "diag_compression_gov_lc":  str(grp.loc[idx_c, "LoadCase"]) if comp_diag  < -_tol else None,
                "chord_tension_kN":         round(tens_chord,      3) if tens_chord >  _tol else None,
                "chord_tension_gov_lc":     str(grp.loc[idx_t, "LoadCase"]) if tens_chord >  _tol else None,
                "chord_compression_kN":     round(abs(comp_chord), 3) if comp_chord < -_tol else None,
                "chord_compression_gov_lc": str(grp.loc[idx_c, "LoadCase"]) if comp_chord < -_tol else None,
            }

        return {
            "brace_type":   self.brace_type,
            "top_chord":    self.top_chord,
            "bottom_chord": self.bottom_chord,
            "geometry":     self.get_brace_geometry_info(),
            "pairs":        pairs,
        }

    def get_brace_geometry_info(self) -> dict:
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

    def get_crossbracing_count(self) -> int:
        """Return the number of cross-bracing panels in result_data."""
        return len(self.bridge.result_data.get("crossbracings", []))

    def run_member_designs(self, forces_dict: dict, dev: bool = False) -> dict:
        """
        Run Osdag member designs for diagonals and chords.

        Tension and compression are designed separately — a member that sees both
        must satisfy both checks independently. Section selection is left to the user
        since sections cannot be compared programmatically.

        Parameters
        ----------
        forces_dict : dict
            Output of get_design_forces_dict().
        dev : bool
            If True, dump forces_dict as JSON to tools/crossbracing_forces_dict.json.

        Returns
        -------
        dict::

            {
                "G1-G2": {
                    "diagonal": {"tension": result_or_None, "compression": result_or_None},
                    "chord":    {"tension": result_or_None, "compression": result_or_None},
                },
                ...
            }
        """
        if dev:
            out = Path(__file__).parents[5] / "tools" / "crossbracing_forces_dict.json"
            out.write_text(json.dumps(forces_dict, indent=2))
            print(f"[CrossBracing] dev dump → {out}")

        from osdagbridge.core.utils.connect import (
            design_dict_struts_bolted,
            design_dict_tension_bolted,
        )

        if not forces_dict or not forces_dict.get("pairs"):
            return {}

        geom       = forces_dict.get("geometry", {})
        L_diag_mm  = round(geom.get("diagonal_length_m", 0) * 1000)
        L_chord_mm = round(geom.get("horiz_proj_m",      0) * 1000)

        # Build a flat job list so all designs run in one parallel batch.
        # Each job tracks (pair, member_type, force_type) for reassembly.
        jobs: list[tuple[str, str, str, dict]] = []

        for pair, vals in forces_dict["pairs"].items():
            for member, L_mm, t_key, c_key in (
                ("diagonal", L_diag_mm, "diag_tension_kN",  "diag_compression_kN"),
                ("chord",    L_chord_mm, "chord_tension_kN", "chord_compression_kN"),
            ):
                if vals.get(t_key) is not None:
                    d = copy.deepcopy(design_dict_tension_bolted)
                    d["Load.Axial"]    = str(float(vals[t_key]))
                    d["Member.Length"] = str(L_mm)
                    jobs.append((pair, member, "tension", d))

                if vals.get(c_key) is not None:
                    d = copy.deepcopy(design_dict_struts_bolted)
                    d["Load.Axial"]    = str(float(vals[c_key]))
                    d["Member.Length"] = str(L_mm)
                    jobs.append((pair, member, "compression", d))

        if not jobs:
            return {}

        sep = "-" * 60
        print(
            f"\n{sep}\n"
            f"  CROSS BRACING DESIGNS  ({len(forces_dict['pairs'])} pair(s))"
            f"  diag L={L_diag_mm} mm  chord L={L_chord_mm} mm\n"
            f"{sep}"
        )
        from osdagbridge.core.utils.connect import design_pool, run_calculation

        cpu_count = __import__("os").cpu_count() or 4
        max_workers = min(cpu_count, len(jobs))

        t0 = time.perf_counter()
        results: dict = {}

        # spawn-context pool: forking under the design worker thread deadlocks (see design_pool).
        with design_pool(max_workers) as executor:
            futures = {
                executor.submit(run_calculation, j[3]): j
                for j in jobs
            }
            for future, (pair, member, force_type, _) in futures.items():
                try:
                    result = future.result()
                except Exception as exc:
                    print(f"  [CrossBracing] SKIP {pair} {member} {force_type}: {exc}")
                    result = None
                results.setdefault(pair, {}).setdefault(member, {})[force_type] = result

        print(f"  Total time : {time.perf_counter() - t0:.3f}s  |  {len(jobs)} designs\n{sep}")
        return results

    # =======================================================================
    # PRINT / REPORT METHODS
    # =======================================================================

    def print_configuration(self) -> None:
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

    def print_critical_forces(self, forces_dict: Optional[dict] = None) -> None:
        self.print_configuration()
        df = self.get_critical_forces(forces_dict)
        print("\n" + "=" * 95)
        print(" " * 22 + "CROSS BRACING — CRITICAL DESIGN FORCES")
        print("=" * 95)
        if df.empty:
            print("  No critical forces — Vz not in dataset or no load cases found.")
        else:
            print(df.to_string(index=False))
        print("=" * 95)

