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
    KEY_SPAN,
    KEY_MP_CB_SPACING,
    KEY_MP_CB_TYPE,
    KEY_MP_CB_NO_OF_CROSS_BRACINGS,
    KEY_MP_GIRDER_DEPTH,
    KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
    KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
    KEY_TS_GIRDER_SPACING,
    KEY_MP_CB_TOP_CHORD,
    KEY_MP_CB_BOTTOM_CHORD,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BRACE_X = "X"
BRACE_K = "K"

# UI "Section Type" label → (Osdag Member.Profile, Conn_Location override)
_OSDAG_PROFILE_MAP = {
    "Angle":                    ("Angles",                 None),
    "Double Angle (Long Leg)":  ("Back to Back Angles",    "Long Leg"),
    "Double Angle (Short Leg)": ("Back to Back Angles",    "Short Leg"),
    "Channel":                  ("Channels",               None),
    "Double Channel":           ("Back to Back Channels",  None),
}


def _osdag_designation(designation) -> Optional[str]:
    """
    Convert a UI/DB angle designation (e.g. "∠ 100 ⅹ 100ⅹ 10" or
    "IS 100 x 100 x 10") to the plain "100 x 100 x 10" form the Osdag member
    design modules expect. Returns None when the string does not carry the
    three leg/thickness numbers of an angle.
    """
    import re as _re
    nums = _re.findall(r"\d+(?:\.\d+)?", str(designation or ""))
    if len(nums) != 3:
        return None
    return " x ".join(nums)


def _apply_section_override(design_dict: dict, override: Optional[dict]) -> None:
    """Restrict an Osdag design dict to the user-selected section (Custom mode)."""
    if not override:
        return
    raw = str(override.get("designation") or "").strip()
    # Angles are normalized to Osdag's "100 x 100 x 10" form; channel
    # designations ("JC 100", "MC 100") match Osdag's DB verbatim.
    des = _osdag_designation(raw) or raw
    if des:
        design_dict["Member.Designation"] = [des]
    profile, conn_loc = _OSDAG_PROFILE_MAP.get(
        str(override.get("section_type") or "").strip(), (None, None)
    )
    if profile:
        design_dict["Member.Profile"] = profile
    if conn_loc:
        design_dict["Conn_Location"] = conn_loc

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

        # Explicit overrides (constructor args) apply to every pair; None means
        # "read this pair's own input dict value" — brace type and chords are
        # independent per girder pair (G1-G2 can be K-Bracing, G2-G3 X-Bracing).
        self._override_brace_type   = brace_type
        self._override_top_chord    = top_chord
        self._override_bottom_chord = bottom_chord
        self._override_cb_spacing   = cb_spacing

        # Per-pair config, keyed by the no-dash pair id used in input keys
        # (e.g. "G2G3"). Populated lazily per pair the first time it's needed,
        # since the set of pairs is only known once result_data is scanned.
        self._pair_config: dict[str, dict] = {}

    # =======================================================================
    # STEP 1 — IDENTIFY BRACE CONFIGURATION (per pair)
    # =======================================================================

    @staticmethod
    def _pair_id(girder_pair: str) -> str:
        """"G2-G3" -> "G2G3" — the no-dash id used in per-member input keys."""
        return girder_pair.replace("-", "")

    def _get_pair_config(self, girder_pair: str) -> dict:
        """
        Resolve (and cache) brace_type / top_chord / bottom_chord / geometry
        for one girder pair, reading that pair's own input keys.
        """
        cached = self._pair_config.get(girder_pair)
        if cached is not None:
            return cached

        from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import (
            resolve_cb_value as _cb,
        )
        inp = getattr(self.bridge, "input_dict", {}) or {}
        pair_id = self._pair_id(girder_pair)

        if self._override_brace_type is not None:
            raw = str(self._override_brace_type).strip().upper()
        else:
            # Stored per member as "K-Bracing" / "X-Bracing" (legacy: flat "K"/"X")
            raw = str(_cb(inp, KEY_MP_CB_TYPE, "", pair=pair_id) or "").strip().upper()

        if raw.startswith(BRACE_K):
            brace_type = BRACE_K
        elif raw.startswith(BRACE_X):
            brace_type = BRACE_X
        else:
            brace_type = BRACE_X  # fallback when the UI never set a brace type

        if self._override_top_chord is not None:
            top_chord = bool(self._override_top_chord)
        else:
            val = _cb(inp, KEY_MP_CB_TOP_CHORD, True, pair=pair_id)
            top_chord = str(val).strip().lower() not in ("no", "false", "0")

        if self._override_bottom_chord is not None:
            bottom_chord = bool(self._override_bottom_chord)
        else:
            val = _cb(inp, KEY_MP_CB_BOTTOM_CHORD, True, pair=pair_id)
            bottom_chord = str(val).strip().lower() not in ("no", "false", "0")

        cfg = {
            "brace_type":   brace_type,
            "top_chord":    top_chord,
            "bottom_chord": bottom_chord,
        }
        cfg.update(self._compute_geometry(pair_id, brace_type))
        self._pair_config[girder_pair] = cfg
        return cfg

    # =======================================================================
    # STEP 2 — BRACE GEOMETRY (per pair)
    # =======================================================================

    def _compute_geometry(self, pair_id: str, brace_type: str) -> dict:
        geom = getattr(self.bridge, "grillage_geometry", None)
        if geom is None:
            raise RuntimeError(
                "CrossBracingForces requires bridge.design() to have been called first."
            )

        from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import (
            resolve_cb_value as _cb,
            resolve_girder_value as _gv,
        )
        inp = getattr(self.bridge, "input_dict", {}) or {}

        if self._override_cb_spacing is not None:
            cb_spacing = float(self._override_cb_spacing)
        else:
            spacing = _cb(inp, KEY_MP_CB_SPACING, pair=pair_id)
            if not spacing:
                # Recompute from span / (count + 1) — same formula the UI uses.
                try:
                    span  = float(inp.get(KEY_SPAN) or 0)
                    count = int(float(str(_cb(inp, KEY_MP_CB_NO_OF_CROSS_BRACINGS, 0, pair=pair_id) or 0)))
                except (TypeError, ValueError):
                    span, count = 0.0, 0
                spacing = span / (count + 1) if span > 0 and count > 0 else 0.0
            cb_spacing = float(spacing or 3.0)

        # --- Girder section dimensions (metres) ---
        # Representative (first) girder; resolve_girder_value tolerates both the
        # per-girder dynamic keys and legacy scalar keys.
        D      = float(_gv(inp, KEY_MP_GIRDER_DEPTH))
        h      = D * self.depth_ratio
        s      = float(inp[KEY_TS_GIRDER_SPACING])

        horiz_proj = s if brace_type == BRACE_X else s / 2.0
        L_d        = math.sqrt(horiz_proj ** 2 + h ** 2)
        alpha_rad  = math.atan2(h, horiz_proj)
        cos_alpha  = math.cos(alpha_rad)

        return {
            "D": D, "h": h, "s": s, "cb_spacing": cb_spacing,
            "horiz_proj": horiz_proj, "L_d": L_d,
            "alpha_rad": alpha_rad, "cos_alpha": cos_alpha,
        }

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

    def _resolve_forces(self, vz_kn: float, cos_alpha: float) -> dict:
        """
        Resolve Vz_i (left-girder end shear, kN) into diagonal and chord forces.

          F_diag  =  Vz_i / cos α   — axial force in diagonal
          F_chord =  Vz_i            — axial force in chord

        Sign preserved: positive = tension, negative = compression.
        """
        if cos_alpha < 1e-9:
            return {"F_diag_kN": 0.0, "F_chord_kN": 0.0}

        return {
            "F_diag_kN":  round(vz_kn / cos_alpha, 4),
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

                girder_pair = f"{st['left_girder']}-{st['right_girder']}"
                pair_cfg = self._get_pair_config(girder_pair)
                resolved = self._resolve_forces(vz_l_kn, pair_cfg["cos_alpha"])

                rows.append({
                    "LoadCase":    lc_str,
                    "Girder Pair": girder_pair,
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

        Brace type, chords, and geometry are independent per girder pair (e.g.
        G1-G2 can be K-Bracing while G2-G3 is X-Bracing), so those fields are
        dicts keyed by girder pair rather than a single bridge-wide value.

        Returns
        -------
        dict::

            {
                "brace_type":   {"G1-G2": "K"|"X", ...},
                "top_chord":    {"G1-G2": bool, ...},
                "bottom_chord": {"G1-G2": bool, ...},
                "geometry":     {"G1-G2": { ... }, ...},
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
        brace_type: dict = {}
        top_chord: dict = {}
        bottom_chord: dict = {}
        geometry: dict = {}
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

            cfg = self._get_pair_config(pair)
            brace_type[pair]   = cfg["brace_type"]
            top_chord[pair]    = cfg["top_chord"]
            bottom_chord[pair] = cfg["bottom_chord"]
            geometry[pair]     = self.get_brace_geometry_info(pair)

        return {
            "brace_type":   brace_type,
            "top_chord":    top_chord,
            "bottom_chord": bottom_chord,
            "geometry":     geometry,
            "pairs":        pairs,
        }

    def get_brace_geometry_info(self, girder_pair: str) -> dict:
        cfg = self._get_pair_config(girder_pair)
        return {
            "brace_type":        cfg["brace_type"],
            "top_chord":         cfg["top_chord"],
            "bottom_chord":      cfg["bottom_chord"],
            "girder_spacing_m":  round(cfg["s"], 4),
            "brace_height_m":    round(cfg["h"], 4),
            "girder_depth_m":    round(cfg["D"], 4),
            "diagonal_length_m": round(cfg["L_d"], 4),
            "horiz_proj_m":      round(cfg["horiz_proj"], 4),
            "alpha_deg":         round(math.degrees(cfg["alpha_rad"]), 2),
            "cb_spacing_m":      round(cfg["cb_spacing"], 3),
            "depth_ratio":       self.depth_ratio,
        }

    def get_crossbracing_count(self) -> int:
        """Return the number of cross-bracing panels in result_data."""
        return len(self.bridge.result_data.get("crossbracings", []))

    def run_member_designs(
        self,
        forces_dict: dict,
        dev: bool = False,
        custom_sections: Optional[dict] = None,
    ) -> dict:
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
        custom_sections : dict, optional
            Custom-design-mode section overrides per pair::

                {"G1-G2": {"diagonal":     {"designation": ..., "section_type": ...},
                           "top_chord":    {...},
                           "bottom_chord": {...}}, ...}

            When given, each design run is restricted to the user-selected
            section instead of optimizing over the full candidate list.

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

        When the top and bottom chords use different sections, "chord" is
        replaced by separate "top_chord" and "bottom_chord" entries of the
        same shape.
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

        # Diagonal/chord unbraced length depends on brace type (K vs X), which
        # is per girder pair, so geometry is looked up per pair below rather
        # than once for the whole bridge.
        all_geometry = forces_dict.get("geometry", {})

        # Build a flat job list so all designs run in one parallel batch.
        # Each job tracks (pair, member_type, force_type) for reassembly.
        jobs: list[tuple[str, str, str, dict]] = []

        for pair, vals in forces_dict["pairs"].items():
            pair_overrides = (custom_sections or {}).get(pair, {})
            geom       = all_geometry.get(pair, {})
            L_diag_mm  = round(geom.get("diagonal_length_m", 0) * 1000)
            L_chord_mm = round(geom.get("horiz_proj_m",      0) * 1000)

            # Top and bottom chords carry the same force but may be different
            # sections (the user picks each separately), so each is designed
            # against its own section. They collapse back to a single "chord"
            # run when their sections match — the usual case, and always so in
            # Optimized mode — to avoid duplicating identical Osdag jobs.
            members = [("diagonal", L_diag_mm, "diag_tension_kN", "diag_compression_kN", "diagonal")]
            top_ov = pair_overrides.get("top_chord")
            bot_ov = pair_overrides.get("bottom_chord")
            if top_ov != bot_ov:
                members.append(("top_chord",    L_chord_mm, "chord_tension_kN", "chord_compression_kN", "top_chord"))
                members.append(("bottom_chord", L_chord_mm, "chord_tension_kN", "chord_compression_kN", "bottom_chord"))
            else:
                members.append(("chord",        L_chord_mm, "chord_tension_kN", "chord_compression_kN", "top_chord"))

            for member, L_mm, t_key, c_key, ov_key in members:
                override = pair_overrides.get(ov_key)
                if vals.get(t_key) is not None:
                    d = copy.deepcopy(design_dict_tension_bolted)
                    d["Load.Axial"]    = str(float(vals[t_key]))
                    d["Member.Length"] = str(L_mm)
                    _apply_section_override(d, override)
                    jobs.append((pair, member, "tension", d))

                if vals.get(c_key) is not None:
                    d = copy.deepcopy(design_dict_struts_bolted)
                    d["Load.Axial"]    = str(float(vals[c_key]))
                    d["Member.Length"] = str(L_mm)
                    _apply_section_override(d, override)
                    jobs.append((pair, member, "compression", d))

        if not jobs:
            return {}

        sep = "-" * 60
        print(
            f"\n{sep}\n"
            f"  CROSS BRACING DESIGNS  ({len(forces_dict['pairs'])} pair(s), {len(jobs)} job(s))\n"
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

    def print_configuration(self, girder_pairs: Optional[list] = None) -> None:
        pairs = girder_pairs or list(self._pair_config.keys())
        print("\n" + "=" * 70)
        print(" " * 18 + "CROSS BRACING CONFIGURATION & GEOMETRY")
        print("=" * 70)
        for pair in pairs:
            g = self.get_brace_geometry_info(pair)
            print(f"  Girder pair              : {pair}")
            print(f"  Brace type               : {g['brace_type']}-type")
            print(f"  Top chord                : {'Yes' if g['top_chord'] else 'No'}")
            print(f"  Bottom chord             : {'Yes' if g['bottom_chord'] else 'No'}")
            print(f"  Girder spacing (s)       : {g['girder_spacing_m']:.4f} m")
            print(f"  Girder depth (D)         : {g['girder_depth_m']:.4f} m")
            print(f"  Brace clear height (h)   : {g['brace_height_m']:.4f} m  "
                  f"(depth_ratio = {g['depth_ratio']})")
            if g["brace_type"] == BRACE_K:
                print(f"  Diag. horiz. projection  : {g['horiz_proj_m']:.4f} m  (= s/2)")
            print(f"  Diagonal length          : {g['diagonal_length_m']:.4f} m")
            print(f"  Diagonal angle (alpha)   : {g['alpha_deg']:.2f} deg from horizontal")
            print(f"  Panel spacing            : {g['cb_spacing_m']:.3f} m")
            print("-" * 70)
        print("=" * 70)

    def print_critical_forces(self, forces_dict: Optional[dict] = None) -> None:
        if forces_dict is None:
            forces_dict = self.get_design_forces_dict()
        self.print_configuration(list((forces_dict or {}).get("pairs", {}).keys()))
        df = self.get_critical_forces(forces_dict)
        print("\n" + "=" * 95)
        print(" " * 22 + "CROSS BRACING — CRITICAL DESIGN FORCES")
        print("=" * 95)
        if df.empty:
            print("  No critical forces — Vz not in dataset or no load cases found.")
        else:
            print(df.to_string(index=False))
        print("=" * 95)

