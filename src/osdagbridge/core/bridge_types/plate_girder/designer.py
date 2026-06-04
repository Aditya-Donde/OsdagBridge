# IRC 22:2015 composite plate-girder design pipeline: Config -> Demand -> Capacity -> DCR -> Report.

from __future__ import annotations

import math
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf-16'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

from osdagbridge.core.bridge_types.plate_girder.analysis_results import PlateGirderAnalysisResults
from osdagbridge.core.bridge_types.plate_girder.initial_sizing import composite_section_properties
from osdagbridge.core.utils.codes.irc22_2015 import IRC22_2014
from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
from osdagbridge.core.utils.codes.keyfile import (
    E_STEEL_MPA,
    G_STEEL_MPA,
    POISSON_RATIO_STEEL,
    GAMMA_M0_STEEL,
    GAMMA_M1_STEEL_ULTIMATE,
    GAMMA_M_REINFORCEMENT,
    KEY_VEHICLE,
    GAMMA_MFT_FATIGUE,
    DCR_PASS_THRESHOLD,
    DCR_FAIL_THRESHOLD,
)
from osdagbridge.core.utils.codes.is800_2007 import IS800_2007


# IRC 22:2015 Cl.601.4 Table 1 — partial safety factors (pulled once at import).
_GAMMA_M = IRC22_2014.cl_601_4_material_safety_factors()
GAMMA_M0 = _GAMMA_M["structural_steel_yield"]["ULS"]              # yielding / instability
GAMMA_M1 = _GAMMA_M["structural_steel_ultimate"]["ULS"]           # ultimate stress
GAMMA_V = _GAMMA_M["bolts_rivets_shear_tension"]["ULS"]           # shear connectors
# GAMMA_MFT_FATIGUE imported from keyfile (IRC 22:2015 Cl.605 Table 3).

# IRC 22:2015 Cl.605.3 — fatigue strength at 5×10^6 cycles derived from IRC module defaults.
_fat_r = IRC22_2014.cl_605_3_fatigue_strength(5_000_000, "rolled")
_fat_w = IRC22_2014.cl_605_3_fatigue_strength(5_000_000, "welded")
FATIGUE_STRENGTH_ROLLED_MPA = _fat_r["ffn_MPa_used"]   # 118.0
FATIGUE_STRENGTH_WELDED_MPA = _fat_w["ffn_MPa_used"]   # 92.0
FATIGUE_SHEAR_STRENGTH_MPA  = _fat_r["tfn_MPa_used"]   # 59.0


# ======================================================================
#  SECTION 1 -- BRIDGE CONFIGURATION (Input Dataclasses)
# ======================================================================


@dataclass
class SteelProperties:
    # Material lookup — structural steel (IRC 22:2015 Annex III + IS 2062), concrete (Annex III
    # Table III.1), reinforcement (IS 1786 / Annex III), partial factors (Cl.601.4 Table 1).
    steel_grade: str
    fy: float                                           # MPa — IS 2062 yield strength
    fu: float                                           # MPa — IS 2062 ultimate strength
    concrete_grade: str
    fck: float                                          # MPa — IRC 22 Annex III cube strength
    fctm: float                                         # MPa — Annex III mean tensile strength
    Ecm: float                                          # MPa — Annex III 28-day secant modulus
    rebar_grade: str = "Fe500"                          # default per common Indian practice
    fy_rebar: float = 500.0                             # MPa — looked up from IRC 22 Annex III

    # IRC 22:2015 Cl.602 Annex III — structural-steel elastic constants (grade-independent).
    Es: float = E_STEEL_MPA
    Gs: float = G_STEEL_MPA
    nu: float = POISSON_RATIO_STEEL

    # IRC 22:2015 Cl.601.4 Table 1 — partial safety factors.
    gamma_m0: float = GAMMA_M0
    gamma_m1: float = GAMMA_M1
    gamma_v: float = GAMMA_V
    gamma_mft: float = GAMMA_MFT_FATIGUE

    @classmethod
    def from_grades(
        cls,
        steel_grade: str,
        fy_struct_MPa: float,
        fu_struct_MPa: float,
        concrete_grade: str,
        rebar_grade: str = "Fe500",
    ) -> "SteelProperties":
        # IRC 22:2015 Cl.602 Annex III — concrete properties by grade.
        conc = IRC22_2014.cl_602_annexIII_concrete_properties(grade=concrete_grade)
        # IRC 22:2015 Cl.602 Annex III — reinforcement properties by grade (IS 1786 Table 3).
        rebar_table = IRC22_2014.cl_602_annexIII_reinforcement_steel_properties()
        rebar_row = rebar_table.get(rebar_grade, rebar_table["Fe500"])
        return cls(
            steel_grade=steel_grade,
            fy=fy_struct_MPa,
            fu=fu_struct_MPa,
            concrete_grade=concrete_grade,
            fck=float(conc["fck"]),
            fctm=float(conc["fctm"]),
            Ecm=float(conc["Ec"]) * 1000.0,             # Annex III stores Ec in GPa
            rebar_grade=rebar_grade,
            fy_rebar=float(rebar_row["fy"]),
        )


@dataclass
class SteelSection:
    # Plate-girder I-section dimensions in mm. D = tf_top + dw + tf_bot; shear area = dw × tw.
    D: float
    bf_top: float
    tf_top: float
    bf_bot: float
    tf_bot: float
    tw: float
    fabrication: str = "welded"

    @property
    def dw(self) -> float:
        return self.D - self.tf_top - self.tf_bot

    @property
    def Af_top(self) -> float:
        return self.bf_top * self.tf_top

    @property
    def Af_bot(self) -> float:
        return self.bf_bot * self.tf_bot

    @property
    def Aw(self) -> float:
        return self.dw * self.tw

    @property
    def A_steel(self) -> float:
        return self.Af_top + self.Aw + self.Af_bot

    @property
    def y_cg_from_bot(self) -> float:
        # Steel centroid measured from bottom fibre (mm).
        y_b = self.tf_bot / 2.0
        y_w = self.tf_bot + self.dw / 2.0
        y_t = self.tf_bot + self.dw + self.tf_top / 2.0
        return (
            self.Af_bot * y_b + self.Aw * y_w + self.Af_top * y_t
        ) / self.A_steel

    @property
    def Iz_steel(self) -> float:
        # Second moment of area about centroidal strong axis (mm^4).
        yc = self.y_cg_from_bot
        y_b = self.tf_bot / 2.0
        y_w = self.tf_bot + self.dw / 2.0
        y_t = self.tf_bot + self.dw + self.tf_top / 2.0
        return (
            self.bf_bot * self.tf_bot ** 3 / 12.0
            + self.Af_bot * (yc - y_b) ** 2
            + self.tw * self.dw ** 3 / 12.0
            + self.Aw * (yc - y_w) ** 2
            + self.bf_top * self.tf_top ** 3 / 12.0
            + self.Af_top * (yc - y_t) ** 2
        )

    @property
    def Zp_steel(self) -> float:
        # Plastic section modulus about strong axis (mm^3).
        half_area = self.A_steel / 2.0
        if self.Af_bot >= half_area:
            y_pna = half_area / self.bf_bot
        elif self.Af_bot + self.Aw >= half_area:
            y_pna = self.tf_bot + (half_area - self.Af_bot) / self.tw
        else:
            y_pna = (self.tf_bot + self.dw
                     + (half_area - self.Af_bot - self.Aw) / self.bf_top)

        def rect_moment(b, t, y_bot_of_rect):
            y_top = y_bot_of_rect + t
            if y_pna >= y_top:
                return b * t * (y_pna - (y_bot_of_rect + t / 2.0))
            elif y_pna <= y_bot_of_rect:
                return b * t * ((y_bot_of_rect + t / 2.0) - y_pna)
            else:
                t_below = y_pna - y_bot_of_rect
                t_above = y_top - y_pna
                return b * t_below * t_below / 2.0 + b * t_above * t_above / 2.0

        return (
            rect_moment(self.bf_bot, self.tf_bot, 0.0)
            + rect_moment(self.tw, self.dw, self.tf_bot)
            + rect_moment(self.bf_top, self.tf_top, self.tf_bot + self.dw)
        )

    @property
    def Ze_steel(self) -> float:
        # Elastic section modulus about strong axis (mm^3).
        yc = self.y_cg_from_bot
        y_top = self.D - yc
        return self.Iz_steel / max(yc, y_top)


@dataclass
class SlabProperties:
    # Concrete deck slab dimensions and reinforcement (all in mm). Covers per IRC 112-2020 durability table.
    thickness: float
    haunch_depth: float = 0.0
    rebar_area_top: float = 0.0
    rebar_area_bot: float = 0.0
    cover_top: float = 40.0
    cover_bot: float = 25.0


@dataclass
class GeometryConfig:
    # Bridge-level geometry (lengths in m). beam_type: "inner" or "outer" per IRC 22 Cl.603.2.1.
    span: float
    beam_spacing: float
    carriageway_width: float
    n_girders: int
    edge_distance: float
    beam_type: str = "inner"
    support_type: str = "simply_supported"
    # Lateral unbraced length for LTB — equals the cross-bracing spacing (m).
    # Defaults to 3.0 m (DEFAULT_CROSS_BRACING_SPACING); wired from Additional Inputs.
    cross_bracing_spacing_m: float = 3.0


@dataclass
class ShearStudConfig:
    # Headed stud connector (IRC 22:2015 Cl.606). fu ≤ 500 MPa per Cl.606.3.1 recommendation.
    diameter: float = 22.0
    height: float = 150.0
    fu: float = 500.0
    n_per_section: int = 2


@dataclass
class FatigueConfig:
    # IRC 22:2015 Cl.605 — fatigue design parameters. Nsc defaults to Table 5 reference life 2×10^6.
    Nsc: int = 2_000_000
    detail_category: str = "welded"
    ffn: float = FATIGUE_STRENGTH_WELDED_MPA            # Cl.605.3 — normal fatigue strength at 5e6 cycles
    tfn: float = FATIGUE_SHEAR_STRENGTH_MPA             # Cl.605.3 — shear fatigue strength at 5e6 cycles


@dataclass
class StiffenerConfig:
    # Stiffener inputs for IRC 24-2010 Cl.509.7 / IS 800:2007 Cl.8.7 checks.
    # Set c_mm > 0 to enable intermediate stiffener checks; bs_R_kN > 0 for bearing stiffener checks.

    # ── Intermediate transverse stiffener (Cl.509.7.2 / IS 800 Cl.8.7.2) ─────────────
    c_mm: float = 0.0           # panel spacing between adjacent stiffeners (mm)
    tq_mm: float = 0.0          # stiffener plate thickness (mm)
    H_mm: float = 0.0           # outstanding leg height (mm)
    n_sides: int = 1             # 1 = one-sided, 2 = two-sided
    Iys_mm4: float = 0.0        # provided MI (mm⁴); 0 = auto-compute from flat-plate formula
    V_kN: float = 0.0           # design shear at stiffener location (kN)
    Vcr_kN: float = 0.0         # critical shear resistance at that location (kN)

    # ── Bearing stiffener (Cl.509.7.3 / IS 800 Cl.8.7.3) ──────────────────────────────
    bs_tq_mm: float = 0.0       # stiffener plate thickness (mm)
    bs_H_mm: float = 0.0        # outstanding leg height (mm)
    bs_n_plates: int = 2        # number of stiffener plates bearing on flange
    bs_R_kN: float = 0.0        # design reaction / concentrated load (kN)
    bs_b1_mm: float = 0.0       # stiff bearing length on flange (0 = auto via IS 800 Cl.8.7.1.3)
    bs_Iys_mm4: float = 0.0     # provided MI (mm⁴) for bearing stiffener; 0 = auto-compute


@dataclass
class BridgeConfig:
    # Single aggregate input consumed by DemandExtractor / IRC22CapacityCalculator / DCREngine / Report.
    material: SteelProperties
    section: SteelSection
    slab: SlabProperties
    geometry: GeometryConfig
    studs: ShearStudConfig = field(default_factory=ShearStudConfig)
    fatigue: FatigueConfig = field(default_factory=FatigueConfig)
    stiffener: Optional[StiffenerConfig] = None            # None = stiffener checks skipped

    @classmethod
    def from_plate_girder_bridge(cls, bridge: Any) -> "BridgeConfig":
        # Build a BridgeConfig from a solved PlateGirderBridge: materials from the project DB
        # (which mirrors IS 2062 / IRC 22 Annex III), concrete/rebar resolved via IRC 22 Annex III.
        from osdagbridge.core.utils.common import (
            KEY_GIRDER, KEY_DECK_CONCRETE_GRADE_BASIC, KEY_TS_DECK_THICKNESS,
            KEY_SPAN, KEY_CARRIAGEWAY_WIDTH, KEY_MP_CB_SPACING,
            KEY_MP_GIRDER_DEPTH, KEY_MP_GIRDER_TOP_FLANGE_WIDTH, KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
            KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH, KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
            KEY_MP_GIRDER_WEB_THICKNESS,
        )

        if not getattr(bridge, "material_props", None):
            bridge.material_props = bridge._build_material_props()

        steel_prop = bridge.material_props.steel_prop
        fy_struct = steel_prop.Fy / 1_000_000.0
        fu_struct = (steel_prop.Fu / 1_000_000.0) if steel_prop.Fu else fy_struct * 1.5

        material = SteelProperties.from_grades(
            steel_grade=str(bridge.basic_inputs.get(KEY_GIRDER, "")),
            fy_struct_MPa=fy_struct,
            fu_struct_MPa=fu_struct,
            concrete_grade=str(bridge.basic_inputs.get(KEY_DECK_CONCRETE_GRADE_BASIC, "")),
        )

        inp = bridge.input_dict
        # NOTE: the DCR capacity check evaluates the representative (first) girder.
        # The grillage analysis model supports distinct per-girder geometry (see
        # analyser._assign_girder_members), but this check is not yet run per
        # girder. Girder geometry is read through resolve_girder_value so it works
        # whether the dict carries per-girder dynamic keys or legacy scalar keys.
        from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import (
            resolve_girder_value as _gv,
        )
        section = SteelSection(
            D=_gv(inp, KEY_MP_GIRDER_DEPTH)                   * 1000,
            bf_top=_gv(inp, KEY_MP_GIRDER_TOP_FLANGE_WIDTH)        * 1000,
            tf_top=_gv(inp, KEY_MP_GIRDER_TOP_FLANGE_THICKNESS)    * 1000,
            bf_bot=_gv(inp, KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH)     * 1000,
            tf_bot=_gv(inp, KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS) * 1000,
            tw=_gv(inp, KEY_MP_GIRDER_WEB_THICKNESS)               * 1000,
        )

        geom = getattr(bridge, "grillage_geometry", None)
        deck = getattr(bridge, "deck_layout", None)
        sizing = getattr(bridge, "sizing_result", None)

        def _req(value, key: str, source: str):
            if value is None:
                raise ValueError(
                    f"{key!r} required for design but not found in {source}; "
                    "populate the input dock and run initial sizing before design check."
                )
            return value

        span = geom.L if geom else _req(bridge.basic_inputs.get(KEY_SPAN), KEY_SPAN, "basic_inputs")
        beam_spacing = geom.ext_to_int_dist if geom else _req(
            getattr(sizing, "girder_spacing", None), "girder_spacing", "sizing_result")
        carriageway = deck.carriageway_width if deck else _req(
            bridge.basic_inputs.get(KEY_CARRIAGEWAY_WIDTH), KEY_CARRIAGEWAY_WIDTH, "basic_inputs")
        n_girders = geom.n_l if geom else _req(
            getattr(sizing, "no_of_girders", None), "no_of_girders", "sizing_result")
        edge_dist = geom.edge_dist if geom else _req(
            getattr(sizing, "deck_overhang", None), "deck_overhang", "sizing_result")

        # Cross-bracing spacing drives the lateral unbraced length for LTB.
        from osdagbridge.core.utils.common import DEFAULT_CROSS_BRACING_SPACING as _DEFAULT_CB_SPACING
        cb_spacing = float(bridge.additional_inputs.get(KEY_MP_CB_SPACING, _DEFAULT_CB_SPACING))

        geometry = GeometryConfig(
            span=float(span),
            beam_spacing=float(beam_spacing),
            carriageway_width=float(carriageway),
            n_girders=int(n_girders),
            edge_distance=float(edge_dist),
            cross_bracing_spacing_m=cb_spacing,
        )

        # Deck thickness lives in the Additional Inputs dialog; fall back to the initial-sizing
        # default when the user has not opened that dialog.
        from osdagbridge.core.bridge_types.plate_girder.initial_sizing import DEFAULT_DECK_THICKNESS
        deck_t = bridge.additional_inputs.get(KEY_TS_DECK_THICKNESS, DEFAULT_DECK_THICKNESS)
        slab = SlabProperties(thickness=float(deck_t))

        # Shear stud parameters from Additional Inputs; defaults match the UI field defaults.
        stud_d   = float(bridge.additional_inputs.get("shear_stud_diameter",         20.0))
        stud_h   = float(bridge.additional_inputs.get("shear_stud_height",           100.0))
        stud_fu  = float(bridge.additional_inputs.get("shear_stud_ultimate_strength", 495.0))
        stud_n   = int(float(bridge.additional_inputs.get("shear_stud_count",          2)))
        studs = ShearStudConfig(diameter=stud_d, height=stud_h, fu=stud_fu, n_per_section=stud_n)

        return cls(material=material, section=section, geometry=geometry, slab=slab, studs=studs)

    @classmethod
    def example_33m_bridge(cls) -> "BridgeConfig":
        # Reference 33.5 m simply-supported composite bridge matching the ospgrillage analyser model.
        # All material properties routed through IRC 22:2015 Annex III lookups.
        return cls(
            material=SteelProperties.from_grades(
                steel_grade="E350",
                fy_struct_MPa=350.0,                    # IS 2062 — E350 yield strength
                fu_struct_MPa=490.0,                    # IS 2062 — E350 ultimate strength
                concrete_grade="M65",
                rebar_grade="Fe500",
            ),
            section=SteelSection(D=1500, bf_top=400, tf_top=20, bf_bot=500, tf_bot=25, tw=12),
            slab=SlabProperties(thickness=250, rebar_area_top=1257.0, rebar_area_bot=1257.0),
            geometry=GeometryConfig(
                span=33.5, beam_spacing=2.2775, carriageway_width=10.0,
                n_girders=7, edge_distance=1.05,
            ),
        )

    def summary(self) -> str:
        s, g, m = self.section, self.geometry, self.material
        return (f"L={g.span}m | {m.steel_grade}/{m.concrete_grade} | "
                f"D={s.D}mm | {g.n_girders} girders @ {g.beam_spacing}m")


# ======================================================================
#  SECTION 2 -- DEMAND EXTRACTOR (Analyser Stage)
# ======================================================================


@dataclass
class DemandEnvelope:
    # Factored force demands at the critical section. Unit suffix is part of each name for clarity.
    Mu_kNm: float = 0.0
    Vu_kN: float = 0.0
    Nu_kN: float = 0.0
    M_construction_kNm: float = 0.0
    delta_live_mm: float = 0.0
    delta_total_mm: float = 0.0
    stress_range_MPa: float = 0.0
    shear_range_MPa: float = 0.0
    Nsc: int = 2_000_000
    governing_combination: str = "ULS Combination I"
    location: str = "midspan"
    member: str = ""
    source: str = "manual"
    M_sls_kNm: float = 0.0
    V_sls_kN: float = 0.0
    Vr_kN: float = 0.0                                    # Cl.606.4.2 — LL shear range (Vmax_LL - Vmin_LL)
    M_girder_sw_kNm: float = 0.0                          # Construction stage 1: girder self-weight only (bare steel)


class DemandExtractor:
    # Factory for DemandEnvelope: from_manual / from_analysis_results / apply_load_factors.

    @staticmethod
    def from_manual(
        Mu_kNm: float,
        Vu_kN: float,
        Nu_kN: float = 0.0,
        M_construction_kNm: float = 0.0,
        delta_live_mm: float = 0.0,
        delta_total_mm: float = 0.0,
        stress_range_MPa: float = 0.0,
        shear_range_MPa: float = 0.0,
        Nsc: int = 2_000_000,
        combination: str = "ULS Combination I",
        location: str = "midspan",
        member: str = "interior_girder",
        M_sls_kNm: float = 0.0,
        V_sls_kN: float = 0.0,
        Vr_kN: float = 0.0,
        M_girder_sw_kNm: float = 0.0,
    ) -> DemandEnvelope:
        # Build a DemandEnvelope from directly supplied factored quantities.
        return DemandEnvelope(
            Mu_kNm=Mu_kNm, Vu_kN=Vu_kN, Nu_kN=Nu_kN, M_construction_kNm=M_construction_kNm,
            delta_live_mm=delta_live_mm, delta_total_mm=delta_total_mm,
            stress_range_MPa=stress_range_MPa, shear_range_MPa=shear_range_MPa,
            Nsc=Nsc, governing_combination=combination,
            location=location, member=member, source="manual",
            M_sls_kNm=M_sls_kNm, V_sls_kN=V_sls_kN, Vr_kN=Vr_kN,
            M_girder_sw_kNm=M_girder_sw_kNm,
        )

    @staticmethod
    def from_analysis_results(
        results: PlateGirderAnalysisResults,
        element_ids: list[int],
        node_ids: list[int],
        Ze_steel_mm3: float,
        Aw_mm2: float,
        Nsc: int = 2_000_000,
        member_name: str = "interior_longitudinal_beam",
        stiffness_ratio: float = 1.0,
    ) -> DemandEnvelope:
        # Extract ULS Mu/Vu envelopes, construction moment, deflections, and fatigue ranges
        # directly from the grillage xarray dataset. forces→N/Nm, displacements→m.
        # stiffness_ratio = I_composite / I_bare_steel: deflections for SDL and live loads
        # (applied after composite action) are divided by this ratio before checking limits.
        import warnings
        import numpy as np

        ds = results.ds
        lc_groups = results.classify_loadcases()
        dead_lcs = lc_groups["dead"]
        live_static = lc_groups["vehicle_static"]
        live_moving = lc_groups["vehicle_moving"]
        all_live_lcs = live_static + live_moving

        def _as_float(arr):
            """Cast xarray/object array to float, coercing non-numeric to NaN."""
            a = np.asarray(arr)
            if a.dtype == object:
                flat = np.empty(a.size, dtype=float)
                for i, v in enumerate(a.flat):
                    try:
                        flat[i] = float(v)
                    except (TypeError, ValueError):
                        flat[i] = np.nan
                return flat.reshape(a.shape)
            return a.astype(float)

        # ------------------------------------------------------------------
        # (1) ULS Mu, Vu  — absolute envelope across every LC
        # ------------------------------------------------------------------
        max_mz = 0.0
        max_vy = 0.0
        for lc in results.get_available_loadcases():
            try:
                mz = _as_float(
                    ds.sel(Loadcase=lc, Element=element_ids,
                           Component=["Mz_i", "Mz_j"])["forces"].values
                )
                vy = _as_float(
                    ds.sel(Loadcase=lc, Element=element_ids,
                           Component=["Vy_i", "Vy_j"])["forces"].values
                )
                mz_finite = mz[~np.isnan(mz)]
                vy_finite = vy[~np.isnan(vy)]
                if mz_finite.size:
                    max_mz = max(max_mz, float(np.abs(mz_finite).max()))
                if vy_finite.size:
                    max_vy = max(max_vy, float(np.abs(vy_finite).max()))
            except KeyError:
                continue

        Mu_kNm = max_mz / 1000.0
        Vu_kN = max_vy / 1000.0

        # ------------------------------------------------------------------
        # (2) Construction moment  — steel self-wt + wet concrete only
        # ------------------------------------------------------------------
        c_patterns = ("girder self weight", "deck slab load",
                      "girder_self_weight", "deck_slab_load",
                      "steel", "wet_concrete")
        construction_mz = 0.0
        matched = 0
        for lc in dead_lcs:
            lc_str = str(lc).lower()
            if any(p in lc_str for p in c_patterns):
                try:
                    mz = _as_float(
                        ds.sel(Loadcase=lc, Element=element_ids,
                               Component=["Mz_i", "Mz_j"])["forces"].values
                    )
                    mz_finite = mz[~np.isnan(mz)]
                    if mz_finite.size:
                        construction_mz += float(np.abs(mz_finite).max())
                        matched += 1
                except KeyError:
                    continue

        if matched == 0:
            warnings.warn(
                "No construction-stage load cases (girder SW / wet concrete) "
                "identified in analysis results. M_construction = 0; the LTB "
                "construction-stage check will be skipped.",
                stacklevel=2,
            )
            M_const_kNm = 0.0
        else:
            # IRC 6:2017 Table B.2 — ULS partial factor for dead load (adding, basic combination).
            gamma_dl = IRC6_2017.table_B2(load_type="dead_load", qualifier="adding", combination="basic")
            M_const_kNm = (construction_mz * gamma_dl) / 1000.0

        # ------------------------------------------------------------------
        # (2b) Girder self-weight only moment — Construction Stage 1
        #      Bare steel girder on its own before wet concrete is placed.
        #      Matches only the girder/steel self-weight LC (excludes deck/wet-concrete).
        # ------------------------------------------------------------------
        _gsw_patterns = ("girder self weight", "girder_self_weight", "steel")
        _deck_exclude = ("deck", "concrete", "wet", "slab")
        girder_sw_mz = 0.0
        for lc in dead_lcs:
            lc_str = str(lc).lower()
            if (any(p in lc_str for p in _gsw_patterns)
                    and not any(p in lc_str for p in _deck_exclude)):
                try:
                    mz = _as_float(
                        ds.sel(Loadcase=lc, Element=element_ids,
                               Component=["Mz_i", "Mz_j"])["forces"].values
                    )
                    mz_finite = mz[~np.isnan(mz)]
                    if mz_finite.size:
                        girder_sw_mz = max(girder_sw_mz, float(np.abs(mz_finite).max()))
                except KeyError:
                    continue

        if girder_sw_mz > 0.0:
            gamma_dl = IRC6_2017.table_B2(load_type="dead_load", qualifier="adding", combination="basic")
            M_girder_sw_kNm = (girder_sw_mz * gamma_dl) / 1000.0
        else:
            M_girder_sw_kNm = 0.0

        # ------------------------------------------------------------------
        # (3) Deflections from `displacements.Component="y"`
        #
        # The grillage model uses bare-steel section properties throughout.
        # For loads applied after composite action is established (SDL + live),
        # deflections must be scaled by I_bare / I_composite = 1 / stiffness_ratio.
        # Construction-stage loads (girder SW + wet concrete) correctly use the
        # bare-steel stiffness and require no correction.
        #
        # Split dead LCs into:
        #   construction_lcs — girder self-weight + wet deck concrete (bare steel ✓)
        #   sdl_lcs          — wearing course, barriers, railings, etc. (composite)
        # ------------------------------------------------------------------
        _const_patterns = ("girder self weight", "deck slab load",
                           "girder_self_weight", "deck_slab_load",
                           "steel", "wet_concrete")
        construction_lcs = [lc for lc in dead_lcs
                            if any(p in str(lc).lower() for p in _const_patterns)]
        _sdl_patterns = ("dw", "footpath", "barrier", "crash", "railing", "median",
                         "wearing", "overlay", "kerb", "curb", "parapet")
        sdl_lcs = [lc for lc in dead_lcs
                   if lc not in set(construction_lcs)
                   and any(p in str(lc).lower() for p in _sdl_patterns)]

        delta_construction_m = 0.0
        delta_sdl_m = 0.0
        delta_live_m = 0.0

        try:
            disp_y = ds.displacements.sel(Component="y", Node=node_ids)

            def _sum_defl(lcs: list) -> float:
                """Sum deflections across additive LCs; return |max| across nodes."""
                if not lcs:
                    return 0.0
                vals = _as_float(disp_y.sel(Loadcase=lcs).values)
                vals = np.nan_to_num(vals, nan=0.0)
                per_node = vals.sum(axis=0) if vals.ndim > 1 else vals
                return float(np.abs(per_node).max()) if per_node.size else 0.0

            delta_construction_m = _sum_defl(construction_lcs)
            delta_sdl_m         = _sum_defl(sdl_lcs)

            if all_live_lcs:
                live_vals = _as_float(disp_y.sel(Loadcase=all_live_lcs).values)
                live_finite = live_vals[~np.isnan(live_vals)]
                if live_finite.size:
                    delta_live_m = float(np.abs(live_finite).max())

        except (KeyError, ValueError) as e:
            warnings.warn(
                f"Could not extract vertical deflections from dataset: {e}. "
                "delta_live / delta_total set to 0.",
                stacklevel=2,
            )

        # Apply composite stiffness correction to post-composite loads (SDL + live).
        # IRC 22:2015 Cl.604.3.2: deflection limits checked at SLS after composite action.
        # delta_live  = live-load-only deflection (L/800 limit); from vehicle LCs only.
        # delta_total = SDL + live deflection (L/600 limit); SLS combinations excluded
        # because they include pre-composite DL (resisted by bare steel, not composite section).
        delta_live_mm  = delta_live_m / stiffness_ratio * 1000.0
        delta_total_mm = (delta_sdl_m + delta_live_m) / stiffness_ratio * 1000.0

        # ------------------------------------------------------------------
        # (4) Fatigue ranges from moving-load envelope
        #     stress_range = (Mz_max - Mz_min) / Ze_steel    [MPa]
        #     shear_range  = (Vy_max - Vy_min) / Aw           [MPa]
        # ------------------------------------------------------------------
        stress_range_MPa = 0.0
        shear_range_MPa = 0.0

        # Fatigue uses moving-load traces (Class A / 70R traversal as proxy for fatigue vehicle).
        # SLS_Frequent combinations are NOT used here — they bundle DL + SDL + factored LL,
        # which would overestimate the stress range. A dedicated IRC fatigue vehicle LC
        # (Annex A of IRC 6) should replace live_moving when that LC is available in the model.
        _fatigue_lcs = live_moving

        if _fatigue_lcs and Ze_steel_mm3 > 0:
            try:
                mz_i = _as_float(
                    ds.forces.sel(Loadcase=_fatigue_lcs, Element=element_ids,
                                  Component="Mz_i").values
                ).flatten()
                mz_j = _as_float(
                    ds.forces.sel(Loadcase=_fatigue_lcs, Element=element_ids,
                                  Component="Mz_j").values
                ).flatten()
                mz_all = np.concatenate([mz_i, mz_j])
                mz_all = mz_all[~np.isnan(mz_all)]
                if mz_all.size:
                    # Nm → Nmm : ×1000  ;  σ = M/Ze
                    # Use max absolute value (not max−min): Mz_i and Mz_j carry
                    # opposite signs by beam equilibrium, so max−min doubles the range.
                    mz_range_Nmm = float(np.abs(mz_all).max()) * 1000.0
                    stress_range_MPa = float(mz_range_Nmm / Ze_steel_mm3)
            except (KeyError, ValueError):
                pass

        if _fatigue_lcs and Aw_mm2 > 0:
            try:
                vy_i = _as_float(
                    ds.forces.sel(Loadcase=_fatigue_lcs, Element=element_ids,
                                  Component="Vy_i").values
                ).flatten()
                vy_j = _as_float(
                    ds.forces.sel(Loadcase=_fatigue_lcs, Element=element_ids,
                                  Component="Vy_j").values
                ).flatten()
                vy_all = np.concatenate([vy_i, vy_j])
                vy_all = vy_all[~np.isnan(vy_all)]
                if vy_all.size:
                    # Same sign-convention fix: use max absolute value.
                    vy_range_N = float(np.abs(vy_all).max())
                    shear_range_MPa = float(vy_range_N / Aw_mm2)
            except (KeyError, ValueError):
                pass

        # ------------------------------------------------------------------
        # (5) SLS moment and shear — post-composite loads only (SDL + live).
        # SLS combinations are NOT used directly: they bundle pre-composite DL
        # (γ=1.0) with SDL + LL. Pre-composite DL is resisted by bare steel alone
        # and must not be applied to the composite section for stress checks.
        # SDL (wearing course, barriers, etc.) IS post-composite and contributes
        # to composite concrete stress, so it is summed with the live-load moment.
        # ------------------------------------------------------------------
        def _peak_mz_vy(lcs):
            mz_max, vy_max, gov = 0.0, 0.0, None
            for lc in lcs:
                try:
                    mz = _as_float(
                        ds.sel(Loadcase=lc, Element=element_ids,
                               Component=["Mz_i", "Mz_j"])["forces"].values
                    )
                    vy = _as_float(
                        ds.sel(Loadcase=lc, Element=element_ids,
                               Component=["Vy_i", "Vy_j"])["forces"].values
                    )
                    mz_f = mz[~np.isnan(mz)]
                    vy_f = vy[~np.isnan(vy)]
                    if mz_f.size:
                        v = float(np.abs(mz_f).max())
                        if v > mz_max:
                            mz_max = v
                            gov = lc
                    if vy_f.size:
                        vy_max = max(vy_max, float(np.abs(vy_f).max()))
                except KeyError:
                    continue
            return mz_max, vy_max, gov

        M_sdl_mz, V_sdl_vy, _        = _peak_mz_vy(sdl_lcs)
        M_ll_mz,  V_ll_vy,  _gov_lc  = _peak_mz_vy(all_live_lcs)

        # SDL and live act simultaneously on the composite section — sum their peak values.
        M_sls_mz = M_sdl_mz + M_ll_mz
        V_sls_vy = V_sdl_vy + V_ll_vy

        print(f"  [SLS stress] SDL LCs={len(sdl_lcs)}  "
              f"M_SDL={M_sdl_mz/1e3:.1f} kNm | "
              f"governing LL LC={_gov_lc}  M_LL={M_ll_mz/1e3:.1f} kNm | "
              f"M_sls={M_sls_mz/1e3:.1f} kNm")

        M_sls_kNm = M_sls_mz / 1000.0
        V_sls_kN  = V_sls_vy / 1000.0

        return DemandEnvelope(
            Mu_kNm=round(Mu_kNm, 2),
            Vu_kN=round(Vu_kN, 2),
            Nu_kN=0.0,
            M_construction_kNm=round(M_const_kNm, 2),
            delta_live_mm=round(delta_live_mm, 3),
            delta_total_mm=round(delta_total_mm, 3),
            stress_range_MPa=round(stress_range_MPa, 3),
            shear_range_MPa=round(shear_range_MPa, 3),
            Nsc=Nsc,
            governing_combination="Max Extracted (All LCs)",
            location="critical element",
            member=member_name,
            source="grillage_analysis",
            M_sls_kNm=round(M_sls_kNm, 2),
            V_sls_kN=round(V_sls_kN, 2),
            M_girder_sw_kNm=round(M_girder_sw_kNm, 2),
        )
        
    @staticmethod
    def apply_load_factors(
        M_dead_kNm: float,
        M_live_kNm: float,
        V_dead_kN: float,
        V_live_kN: float,
        span_m: float,
        vehicle_class: str = KEY_VEHICLE[0],            # default Class 70R(W)
    ) -> DemandEnvelope:
        # IRC 6:2017 Table B.2 (ULS basic) — γDL = 1.35, γLL(leading) = 1.50.
        gamma_dl = IRC6_2017.table_B2(load_type="dead_load", qualifier="adding", combination="basic")
        gamma_ll = IRC6_2017.table_B2(load_type="live_load", qualifier="leading", combination="basic")
        # IRC 6:2017 Cl.208.2 / 208.3 — impact factor by vehicle class.
        if vehicle_class in (KEY_VEHICLE[0], KEY_VEHICLE[1]):       # Class 70R(W) / 70R(T)
            impact = 1.0 + IRC6_2017.cl_208_3_impact_factor(span_m)
        else:                                                       # Class A / Class B
            impact = 1.0 + IRC6_2017.cl_208_2_impact_factor(span_m)

        Mu = gamma_dl * M_dead_kNm + gamma_ll * impact * M_live_kNm
        Vu = gamma_dl * V_dead_kN + gamma_ll * impact * V_live_kN
        return DemandEnvelope(
            Mu_kNm=round(Mu, 3), Vu_kN=round(Vu, 3),
            governing_combination=f"γDL={gamma_dl}·DL + γLL={gamma_ll}·IF={impact:.3f}·LL",
            location="midspan", source="factored_components",
        )


# ======================================================================
#  SECTION 3 -- IRC 22:2015 CAPACITY CALCULATOR
# ======================================================================


@dataclass
class CapacityResults:
    # Aggregated IRC 22:2015 capacity values keyed by the clause that produced them.
    beff_mm: float = 0.0                                # Cl.603.2.1
    xu_mm: float = 0.0                                  # Cl.603.3.1
    pna_location: str = ""
    Mp_kNm: float = 0.0
    Md_kNm: float = 0.0
    Mcr_kNm: float = 0.0                                # Cl.603.3.3.1
    lambda_LT: float = 0.0
    chi_LT: float = 0.0
    Mb_kNm: float = 0.0
    # Stage 1 LTB (girder only, LLT = full span) — lower Mb, used for girder-SW check.
    Mb_kNm_stage1: float = 0.0
    lambda_LT_stage1: float = 0.0
    chi_LT_stage1: float = 0.0
    Av_mm2: float = 0.0                                 # Cl.603.3.3.2
    Vn_kN: float = 0.0
    Vd_kN: float = 0.0
    Mdv_kNm: float = 0.0                                # Cl.603.3.3.3
    beta_interaction: float = 0.0
    defl_limit_live_mm: float = 0.0                     # Cl.604.3.2
    defl_limit_total_mm: float = 0.0
    sigma_c_limit_MPa: float = 0.0                      # Cl.604.3.1 — concrete limit (0.48 fck)
    sigma_s_limit_MPa: float = 0.0                      # Cl.604.3.1 — steel equiv. limit (0.9 fy)
    f_fd_MPa: float = 0.0                               # Cl.605
    tau_fd_MPa: float = 0.0
    f_fd_eff_MPa: float = 0.0                           # Cl.605 — min(f_fd, 1.5*fy)                                                                                                                                                      
    tau_fd_eff_MPa: float = 0.0                         # Cl.605 — min(tau_fd, 1.5*0.43*fy)                                                                                                                                        
    VL_N_per_mm: float = 0.0                            # Cl.606.10 — longitudinal shear per unit length                                                                                                                                  
    transverse_shear_ok: bool = False                   # Cl.606.10                                                                                                                                                                     
    Ast_required_cm2_per_m: float = 0.0                 # Cl.606.10 — minimum transverse steel                                                                                                                                          
    Ast_provided_cm2_per_m: float = 0.0                 # Cl.606.10 — provided transverse steel                                                                                                                                    
    Qu_kN: float = 0.0                                  # Cl.606
    stud_spacing_mm: float = 0.0
    # Composite section properties (Cl.604.3) — short-term transformed section.
    I_comp_short_mm4: float = 0.0                      
    y_top_comp_mm: float = 0.0                          # distance top-of-slab → composite NA
    y_bot_comp_mm: float = 0.0                          # distance composite NA → bottom steel
    # SLS actual stresses (Cl.604.3.1) — computed from M_sls / I_comp.
    sigma_c_actual_MPa: float = 0.0                     # concrete stress at top fibre
    sigma_rebar_actual_MPa: float = 0.0                 # rebar tensile stress
    sigma_steel_equiv_MPa: float = 0.0                  # steel equivalent stress (max of comp/tens)
    tau_web_actual_MPa: float = 0.0                     # average web shear stress
    sigma_rebar_limit_MPa: float = 0.0                  # rebar SLS limit (0.80 fyk)
    # Crack control (Cl.604.4).
    As_min_crack_mm2: float = 0.0                       
    As_provided_crack_mm2: float = 0.0                  # total rebar area (top + bot)
    # Shear connector spacing limits (Cl.606.9).
    stud_spacing_max_mm: float = 600.0                  # governing upper limit (606.9)
    stud_spacing_min_mm: float = 75.0                   # absolute lower limit (606.9)
    # Additional shear connector spacing checks.
    Qr_kN: float = 0.0                                  # Cl.606.3.2 — fatigue stud capacity
    stud_spacing_full_shear_mm: float = 0.0             # Cl.606.4.1.1 — SL2 (full shear)
    stud_spacing_fatigue_mm: float = 0.0                # Cl.606.4.2 — SR (SLS fatigue)
    stud_spacing_governing_mm: float = 0.0              # min(SL1, SL2, SR) — required limit
    stud_spacing_provided_mm: float = 0.0               # actual provided (user input or = governing)
    stud_spacing_user_provided: bool = False            # True when user explicitly gave a spacing
    stud_detailing_ok: bool = True                      # Cl.606.6 — all detailing checks pass
    source: str = "built-in"
    details: Dict[str, dict] = field(default_factory=dict)

    # ── Intermediate stiffener (IRC 24-2010 Cl.509.7.2 / IS 800 Cl.8.7.2) ──────────
    is_H_limit_mm: float = 0.0          # Cl.509.7.2.4 — limiting outstanding leg (14tqε / 20tqε)
    is_Iys_min_mm4: float = 0.0         # Cl.509.7.2.4 — minimum required MI
    is_Iys_prov_mm4: float = 0.0        # Cl.509.7.2.4 — provided MI
    is_Fqd_kN: float = 0.0             # Cl.509.7.2.5 — stiffener design buckling resistance
    is_Fq_kN: float = 0.0              # Cl.509.7.2.5 — demand = max((V − Vcr)/γm0, 0)

    # ── Bearing stiffener (IRC 24-2010 Cl.509.7.3 / IS 800 Cl.8.7.3) ───────────────
    bs_Fcdw_wb_kN: float = 0.0          # Cl.509.7.3.1 — web bearing zone buckling resistance
    bs_Fcdw_lc_kN: float = 0.0          # Cl.509.7.3.2 — local crushing resistance
    bs_Fpsd_kN: float = 0.0             # Cl.509.7.3.3 — bearing contact resistance
    bs_Fcd_kN: float = 0.0             # Cl.509.7.2.5 — stiffener column buckling resistance
    bs_R_kN: float = 0.0               # reaction demand


class IRC22CapacityCalculator:
    # Clause-by-clause IRC 22:2015 capacity calculator driven by a single BridgeConfig.

    def __init__(self, config: BridgeConfig):
        self.cfg = config
        self.mat = config.material
        self.sec = config.section
        self.slab = config.slab
        self.geo = config.geometry
        self.studs = config.studs
        self.fatigue = config.fatigue

    # IRC 22:2015 Cl.603.2.1 — effective width of concrete flange for simply-supported girder.
    def compute_effective_width(self) -> dict:
        # IRC22_2014.cl_603_2_1_effective_width_simply_supported takes Lo and B in metres
        # and returns beff_m in metres.
        Lo_m = self.geo.span
        B_m  = self.geo.beam_spacing

        if self.geo.beam_type == "inner":
            res = IRC22_2014.cl_603_2_1_effective_width_simply_supported(
                Lo=Lo_m, beam_type="inner", B=B_m
            )
        else:
            # B1 = centre-to-centre spacing to adjacent inner beam
            # B0 = edge_distance = distance from outer beam centreline to free slab edge
            res = IRC22_2014.cl_603_2_1_effective_width_simply_supported(
                Lo=Lo_m, beam_type="outer",
                B1=B_m,
                B0=self.geo.edge_distance,
            )

        beff_mm = res["beff_m"] * 1000.0        # clause returns metres; convert to mm for design
        return {
            "beff_mm"  : round(beff_mm, 1),
            "Lo_mm"    : Lo_m * 1000.0,
            "B_mm"     : B_m  * 1000.0,
            "beam_type": self.geo.beam_type,
            "method"   : res["equation_used"],
            "clause"   : res["clause"],
            "source"   : "IRC22_2014",
        }

    # IRC 22:2015 Cl.603 — section classification (web + flange governed by d/tw and b/tf ratios).
    def classify_section(self) -> dict:
        sec = self.sec
        fy  = self.mat.fy

        # Web classification — delegate to IRC22_2014.cl_603_check_steel_web_classification
        # (which references IS 800:2007 Table 2 web limits via epsilon = sqrt(250/fy)).
        web_res = IRC22_2014.cl_603_check_steel_web_classification(
            depth_web_mm=sec.dw,
            tw_mm=sec.tw,
            fy_MPa=fy,
            axial_force_N=0.0,          # pure bending — zero axial compression
            load_type="Compression",
        )
        web_class = web_res["section_class"]

        # Flange classification (outstanding element of compression flange) —
        # delegate to IRC22_2014.cl_602_table2_i_outstanding_compression_flange,
        # which wraps IS 800:2007 Table 2 row (i).
        # Outstanding half-width = (total flange width − web thickness) / 2
        b_outstanding = (sec.bf_top / 2.0) - (sec.tw / 2.0)
        flange_result = IRC22_2014.cl_602_table2_i_outstanding_compression_flange(
            width_mm=b_outstanding,
            thickness_mm=sec.tf_top,
            fy_MPa=fy,
            section_type=sec.fabrication,   # "rolled" or "welded" — as stored in SteelSection
        )
        # IS800_2007.Table2_i returns [section_class, b/t ratio]
        flange_class = flange_result[0]
        b_tf = b_outstanding / sec.tf_top

        class_order = {"Plastic": 1, "Compact": 2, "Semi-Compact": 3, "Slender": 4}
        governing = max(web_class, flange_class, key=lambda c: class_order.get(c, 4))

        return {
            "epsilon"        : round(web_res["epsilon"], 4),
            "d_tw_ratio"     : round(web_res["d_by_t"], 2),
            "b_tf_ratio"     : round(b_tf, 2),
            "web_class"      : web_class,
            "flange_class"   : flange_class,
            "governing_class": governing,
            "clause"         : "IRC 22:2015 - Cl.603 | IS 800:2007 Table 2",
            "source"         : "IRC22_2014",
        }

    # IRC 22:2015 Cl.603.3.1 — plastic positive moment capacity (sagging, full shear interaction).
    #
    # delegates to IRC22_2014.cl_603_3_1_positive_moment_capacity which implements
    # IRC 22 Annex I.1 / I.2 formulation:
    #   • Equivalent rectangular stress block: f_conc = αcc × η × fck / γc;  a = λ × xu
    #   • η and λ factors for high-strength concrete (fck > 60 MPa)
    #   • PNA-in-slab:  xu from force equilibrium; lever arm = steel CG − a/2
    #   • PNA-in-steel: force balance across top flange → web → bottom flange; full plastic moment
    #   • Annex I.2 beff restriction for non-compact sections
    # Partial safety factors γm0 and γc are embedded in T and C; Md_kNm = Mp_kNm directly.
    def compute_moment_capacity(self, beff_mm: float) -> dict:
        res = IRC22_2014.cl_603_3_1_positive_moment_capacity(
            fck=self.mat.fck,
            fy=self.mat.fy,
            beff=beff_mm,
            ds=self.slab.thickness,
            As=self.sec.A_steel,
            bf_top=self.sec.bf_top,
            tf_top=self.sec.tf_top,
            tw=self.sec.tw,
            dw=self.sec.dw,
            bf_bot=self.sec.bf_bot,
            tf_bot=self.sec.tf_bot,
            D_steel=self.sec.D,
            ys_from_bot=self.sec.y_cg_from_bot,
            h_haunch=self.slab.haunch_depth,
            gamma_m0=self.mat.gamma_m0,
            combination_type="basic",
        )
        return {
            "xu_mm"         : res["xu_mm"],
            "pna_location"  : res["pna_location"],
            "T_steel_kN"    : res["T_design_kN"],
            "C_conc_max_kN" : res["C_slab_max_kN"],
            "eta"           : res["eta"],
            "lambda_factor" : res["lambda_factor"],
            "a_mm"          : res["a_mm"],
            "Mp_kNm"        : res["Mp_kNm"],
            "Md_kNm"        : res["Md_kNm"],   # = Mp_kNm; γm0 and γc already embedded
            "gamma_m0"      : self.mat.gamma_m0,
            "clause"        : res["clause"],
            "source"        : "IRC22_2014",
        }

    # IRC 22:2015 Cl.603.3.3.2 — plastic shear resistance of the web.
    def compute_shear_capacity(self) -> dict:
        # Delegate entirely to IRC22_2014.cl_603_3_3_2_plastic_shear_resistance.
        # For a welded I-section (plate girder) the shear area is Av = dw × tw (clear web depth).
        res = IRC22_2014.cl_603_3_3_2_plastic_shear_resistance(
            section_type="i_major",
            fyw=self.mat.fy,
            fabrication=self.sec.fabrication,   # "welded" → Av = dw × tw
            d=self.sec.dw,
            tw=self.sec.tw,
        )
        return {
            "Av_mm2"  : res["Av_mm2"],
            "fyw_MPa" : res["fyw_MPa"],
            "Vn_kN"   : res["Vn_kN"],
            "Vd_kN"   : res["Vd_kN"],
            "gamma_m0": res["gamma_m0"],
            "clause"  : res["clause"],
            "source"  : "IRC22_2014",
        }

    # IRC 22:2015 Cl.603.3.3.1 — lateral-torsional buckling resistance at construction stage.
    def compute_buckling_resistance(self, beff_mm: float, section_class: str = "",
                                    LLT_mm_override: float = None) -> dict:
        # Section properties required by the IRC22 clause method.
        sec = self.sec
        mat = self.mat
        # Stage 1 (girder only): caller passes full span as override.
        # Stage 2 (cross-bracings in place): use cross-bracing spacing (default).
        if LLT_mm_override is not None:
            LLT_mm = LLT_mm_override
        else:
            LLT_mm = min(self.geo.cross_bracing_spacing_m * 1000.0, self.geo.span * 1000.0)

        It = (sec.bf_top * sec.tf_top ** 3
              + sec.dw  * sec.tw    ** 3
              + sec.bf_bot * sec.tf_bot ** 3) / 3.0

        Iy = (sec.tf_top * sec.bf_top ** 3 / 12.0
              + sec.dw  * sec.tw    ** 3 / 12.0
              + sec.tf_bot * sec.bf_bot ** 3 / 12.0)

        hw = sec.dw + sec.tf_top / 2.0 + sec.tf_bot / 2.0
        Iy_top = sec.tf_top * sec.bf_top ** 3 / 12.0
        Iy_bot = sec.tf_bot * sec.bf_bot ** 3 / 12.0
        Iw = (Iy_top * Iy_bot) / (Iy_top + Iy_bot) * hw**2

        # Allow the caller to pass section_class from a prior classify_section() call to
        # avoid a second classification run; fall back to a fresh call when not supplied.
        if not section_class:
            section_class = self.classify_section()["governing_class"]

        # Delegate to IRC22_2014.cl_603_3_3_1_buckling_resistance_moment.
        # Internally this calls IS800_2007.cl_8_2_1_2_design_bending_strength for Mpl,
        # then applies the λLT / χLT buckling reduction per IS 800:2007 Cl.8.2.1.2.
        res = IRC22_2014.cl_603_3_3_1_buckling_resistance_moment(
            section_class=section_class.lower(),
            Zp=sec.Zp_steel,
            Ze=sec.Ze_steel,
            fy=mat.fy,
            gamma_mo=mat.gamma_m0,
            Iy=Iy,
            It=It,
            Iw=Iw,
            LLT=LLT_mm,
            section_type=sec.fabrication,   # "rolled" or "welded" → sets αLT (0.21 / 0.49)
            E=mat.Es,
            G=mat.Gs,
        )

        # phi_LT is computed internally by the IRC22 clause method but not returned;
        # derive it from the returned alpha_LT and lambda_LT for the report.
        alpha_LT  = res["alpha_LT"]
        lambda_LT = res["lambda_LT"]
        phi_LT    = round(0.5 * (1.0 + alpha_LT * (lambda_LT - 0.2) + lambda_LT ** 2), 4)

        return {
            "It_mm4"   : round(It, 1),
            "Iy_mm4"   : round(Iy, 1),
            "LLT_mm"   : LLT_mm,
            "Mcr_kNm"  : res["Mcr_kNm"],
            "lambda_LT": res["lambda_LT"],
            "alpha_LT" : res["alpha_LT"],
            "phi_LT"   : phi_LT,
            "chi_LT"   : res["chi_LT"],
            "Mb_kNm"   : res["Mpl_buckling_kNm"],
            "clause"   : res["clause"],
            "source"   : "IRC22_2014",
        }

    # IRC 22:2015 Cl.603.3.3.3 — reduced bending resistance under high shear (V > 0.6·Vd).
    def compute_combined_bending_shear(self, Md_kNm: float, V_kN: float, Vd_kN: float) -> dict:
        sec = self.sec
        fy, gm0 = self.mat.fy, self.mat.gamma_m0

        # Mfd = plastic bending strength of the section excluding the shear area (web).
        # For an I-section: Mfd ≈ fy × Af_bot × hw / γm0  (flange-only contribution).
        hw = sec.dw + sec.tf_top / 2.0 + sec.tf_bot / 2.0
        Mfd_kNm = fy * sec.Af_bot * hw / 1e6 / gm0

        # Delegate to IRC22_2014.cl_603_3_3_3_reduced_bending_under_high_shear (Eq 3.13).
        res = IRC22_2014.cl_603_3_3_3_reduced_bending_under_high_shear(
            Md_kNm=Md_kNm,
            Mfd_kNm=Mfd_kNm,
            V_kN=V_kN,
            Vd_kN=Vd_kN,
        )
        return {
            "Mdv_kNm"           : res["Mdv_kNm"],
            "Mfd_kNm"           : res["Mfd_kNm"],
            "beta"              : res["beta"],
            "reduction_required": res["is_reduction_required"],
            "clause"            : res["clause"],
            "source"            : "IRC22_2014",
        }

    # IRC 22:2015 Cl.604.3 — short-term and long-term composite section properties.
    # These are needed for SLS stress calculations (Cl.604.3.1) and stud spacing (Cl.606.4.1).
    def compute_composite_section_props(self, beff_mm: float) -> dict:
        """
        Compute transformed composite second moment of area, neutral-axis depths, and
        section moduli for both short-term (n = Es/Ecm) and long-term (2n = Es/(0.5*Ecm))
        modular ratios per IRC 22:2015 Cl.604.3.

        Delegates the geometry to composite_section_properties() from initial_sizing.py.
        Coordinate system: all y-distances measured from BOTTOM of steel section (upward +ve).
        """
        sec, mat, slab = self.sec, self.mat, self.slab
        mod = IRC22_2014.cl_604_3_modular_ratio(Ecm=mat.Ecm, Kc=0.5)
        n_short = mod["m_short_term"]   # Es/Ecm  ≥ 7.5
        n_long  = mod["m_long_term"]    # Es/(0.5*Ecm) ≥ 15.0

        return {
            "short_term" : composite_section_properties(
                beff_mm=beff_mm, ds_mm=slab.thickness, h_haunch_mm=slab.haunch_depth,
                A_steel_mm2=sec.A_steel, Iz_steel_mm4=sec.Iz_steel,
                y_cg_from_bot_mm=sec.y_cg_from_bot, D_steel_mm=sec.D, n=n_short,
            ),
            "long_term"  : composite_section_properties(
                beff_mm=beff_mm, ds_mm=slab.thickness, h_haunch_mm=slab.haunch_depth,
                A_steel_mm2=sec.A_steel, Iz_steel_mm4=sec.Iz_steel,
                y_cg_from_bot_mm=sec.y_cg_from_bot, D_steel_mm=sec.D, n=n_long,
            ),
            "clause" : mod["clause"],
            "source" : "IRC22_2014",
        }

    # IRC 22:2015 Cl.604.3.1 — actual SLS stresses from service moment.
    # Calculates concrete, rebar, and steel stresses; delegates limit checks to IRC22_2014.
    def compute_sls_stresses(                                            
        self,
        beff_mm: float,
        M_sls_kNm: float,
        V_sls_kN: float,
        comp_props: dict = None,
    ) -> dict:
        """
        IRC 22:2015 Cl.604.3.1 — Actual SLS stress calculation and limit checks.

        Uses the SHORT-TERM composite section (modular ratio n = Es/Ecm) as required
        for serviceability checks under live loading.

        Stresses computed:
          σ_c   = M_sls × y_top / I_comp          concrete compressive stress (top of slab)
          σ_r   = M_sls × y_rebar / I_comp        rebar tensile stress (bottom rebar centroid)
          f_bc  = M_sls × |y_steel_top| / I_comp  steel bending stress at top fibre
          f_bt  = M_sls × y_bot / I_comp          steel bending stress at bottom fibre
          τ_b   = V_sls / A_web                   average web shear stress
          f_e   = √(f²_bc + f²_p ± f_bc·f_p + 3τ²_b)  equivalent steel stress

        Limits (from IRC22_2014.cl_604_3_1_limiting_stresses):
          σ_c  ≤ k1 × fck  = 0.48 fck   (IRC 112-2011 Cl.12.2.1)
          σ_r  ≤ k3 × fyk  = 0.80 fyk   (IRC 112-2011 Cl.12.2.2)
          f_e  ≤ 0.9 fy                  (IRC 22:2015 Cl.604.3.1)
        """
        if M_sls_kNm <= 0.0:
            return {"skipped": True, "reason": "M_sls_kNm = 0; supply SLS moment to enable this check."}

        sec, mat, slab = self.sec, self.mat, self.slab

        if comp_props is None:
            comp_props = self.compute_composite_section_props(beff_mm)

        short      = comp_props["short_term"]
        I_comp     = short["I_comp_mm4"]
        y_top      = short["y_top_mm"]          # from top of slab to composite NA (compression arm)
        y_bot      = short["y_bot_mm"]          # from composite NA to bottom of steel (tension arm)
        y_comp_bot = short["y_comp_from_bot_mm"]

        M_Nmm = M_sls_kNm * 1e6
        V_N   = V_sls_kN  * 1e3

        # ── Concrete compressive stress at top of slab ────────────────────────
        sigma_c = M_Nmm * y_top / I_comp

        # ── Rebar tensile stress at bottom rebar centroid ─────────────────────
        # Rebar centroid from bottom of slab = cover_bot + approx half-bar-dia (6 mm)
        y_rebar_from_slab_bot = slab.cover_bot + 6.0
        # Position from bottom of steel: D + h_haunch + ds - y_rebar_from_slab_bot
        y_rebar_from_steel_bot = sec.D + slab.haunch_depth + slab.thickness - y_rebar_from_slab_bot
        y_rebar_from_NA        = y_rebar_from_steel_bot - y_comp_bot   # +ve → below NA (tension)
        sigma_rebar = max(M_Nmm * y_rebar_from_NA / I_comp, 0.0)       # tension = positive

        # ── Structural steel bending stresses ─────────────────────────────────
        # y of top-steel-fibre from bottom of steel
        y_steel_top_from_bot_steel = sec.D
        y_steel_top_from_NA        = y_steel_top_from_bot_steel - y_comp_bot  # −ve → above NA (comp)
        fbc = M_Nmm * abs(y_steel_top_from_NA) / I_comp   # compressive stress at top steel fibre
        fbt = M_Nmm * y_bot / I_comp                        # tensile stress at bottom steel fibre

        # ── Average web shear stress ───────────────────────────────────────────
        tau_b = V_N / sec.Aw if sec.Aw > 0.0 else 0.0

        # fp = bearing stress at the section — 0 unless at support with known reaction/area
        fp = 0.0

        # ── Equivalent steel stress (IRC 22:2015 Cl.604.3.1) ──────────────────
        fe_comp = math.sqrt(fbc**2 + fp**2 + fbc * fp + 3.0 * tau_b**2)
        fe_tens = math.sqrt(fbt**2 + fp**2 + fbt * fp + 3.0 * tau_b**2)
        fe_max  = max(fe_comp, fe_tens)

        # ── Delegate limit checks to IRC22_2014 ───────────────────────────────
        lim = IRC22_2014.cl_604_3_1_limiting_stresses(
            f_ck_cu=mat.fck,
            f_yk_reinf=mat.fy_rebar,
            f_y_struct=mat.fy,
            fbc=fbc,
            fbt=fbt,
            fp=fp,
            tau_b=tau_b,
        )
        sigma_c_limit    = lim["concrete_allowable_stress_MPa"]
        sigma_rebar_limit = lim["reinforcement_allowable_stress_MPa"]
        sigma_steel_limit = lim["steel_equivalent_limit_0.9fy_MPa"]

        return {
            "M_sls_kNm"          : M_sls_kNm,
            "V_sls_kN"           : V_sls_kN,
            "I_comp_mm4"         : round(I_comp, 0),
            "y_top_mm"           : round(y_top, 2),
            "y_bot_mm"           : round(y_bot, 2),
            # Concrete
            "sigma_c_MPa"        : round(sigma_c, 3),
            "sigma_c_limit_MPa"  : round(sigma_c_limit, 3),
            "concrete_ok"        : sigma_c <= sigma_c_limit,
            # Rebar
            "sigma_rebar_MPa"    : round(sigma_rebar, 3),
            "sigma_rebar_limit_MPa": round(sigma_rebar_limit, 3),
            "rebar_ok"           : sigma_rebar <= sigma_rebar_limit,
            # Structural steel
            "fbc_MPa"            : round(fbc, 3),
            "fbt_MPa"            : round(fbt, 3),
            "tau_b_MPa"          : round(tau_b, 3),
            "fe_comp_MPa"        : round(fe_comp, 3),
            "fe_tens_MPa"        : round(fe_tens, 3),
            "fe_max_MPa"         : round(fe_max, 3),
            "sigma_steel_limit_MPa": round(sigma_steel_limit, 3),
            "steel_ok"           : fe_max <= sigma_steel_limit,
            "clause"             : lim["clause"],
            "source"             : "IRC22_2014",
        }

    # IRC 22:2015 Cl.604.4 — minimum reinforcement for crack control.
    def compute_crack_control(self, beff_mm: float) -> dict:            
        """
        IRC 22:2015 Cl.604.4 + IRC 112-2011 Cl.12.3.3 — Minimum reinforcement for crack control.
        Delegates entirely to IRC22_2014.cl_604_4_crack_control_As_min.
        As_provided = total of top and bottom rebar areas from SlabProperties.
        """
        slab, mat = self.slab, self.mat
        As_total = slab.rebar_area_top + slab.rebar_area_bot
        res = IRC22_2014.cl_604_4_crack_control_As_min(
            fctm=mat.fctm,
            beff=beff_mm,
            t_slab=slab.thickness,
            fy=mat.fy_rebar,
            kc=0.5,
            width_mm=beff_mm,
            element_type="flange",
            As_provided=As_total if As_total > 0.0 else None,
        )
        return {
            "As_min_mm2"      : res["As_min_mm2"],
            "As_provided_mm2" : As_total,
            "is_ok"           : res.get("is_ok"),    # None if As_provided = 0
            "kc"              : res["kc"],
            "k"               : res["k"],
            "fctm_MPa"        : res["fctm_MPa"],
            "clause"          : res["clause"],
            "source"          : "IRC22_2014",
        }

    # IRC 22:2015 Cl.606.9 — limiting spacing of shear connectors.
    def compute_stud_spacing_limits(                                     
        self, provided_spacing_mm: float = None
    ) -> dict:
        """
        IRC 22:2015 Cl.606.9 — Limiting criteria for shear connector spacing.
        Max spacing = min(600, 3 × t_slab, 4 × h_stud).  Min spacing = 75 mm.
        Delegates entirely to IRC22_2014.cl_606_9_shear_connector_spacing_limits.
        """
        res = IRC22_2014.cl_606_9_shear_connector_spacing_limits(
            tslab_mm=self.slab.thickness,
            h_stud_mm=self.studs.height,
            provided_spacing_mm=provided_spacing_mm,
        )
        return {
            "max_spacing_mm"      : res["max_spacing_limit_mm"],
            "min_spacing_mm"      : res["minimum_spacing_limit_mm"],
            "limit_600_mm"        : res["limit_600_mm"],
            "limit_3_tslab_mm"    : res["limit_3_tslab_mm"],
            "limit_4_hstud_mm"    : res["limit_4_hstud_mm"],
            "provided_spacing_mm" : provided_spacing_mm,
            "is_ok"               : res.get("is_spacing_acceptable"),
            "clause"              : res["clause"],
            "source"              : "IRC22_2014",
        }

    # IRC 22:2015 Cl.604.3 — short- and long-term modular ratio (min bounds 7.5 / 15.0).
    def compute_modular_ratio(self) -> dict:
        res = IRC22_2014.cl_604_3_modular_ratio(Ecm=self.mat.Ecm, Kc=0.5)
        return {
            "Es_MPa": res["Es_MPa"], "Ecm_MPa": res["Ecm_MPa"], "Kc": res["Kc"],
            "m_short": res["m_short_term"], "m_long": res["m_long_term"],
            "clause": res["clause"], "source": "IRC22_2014",
        }

    # IRC 22:2015 Cl.604.3.1 — SLS allowable stresses (concrete k1·fck, rebar k3·fyk, steel 0.9·fy).
    def compute_sls_stress_limits(self) -> dict:
        res = IRC22_2014.cl_604_3_1_limiting_stresses(
            f_ck_cu=self.mat.fck,
            f_yk_reinf=self.mat.fy_rebar,
            f_y_struct=self.mat.fy,
        )
        return {
            "sigma_c_allow_MPa": res["concrete_allowable_stress_MPa"],
            "sigma_rebar_allow_MPa": res["reinforcement_allowable_stress_MPa"],
            "sigma_steel_allow_MPa": res["steel_equivalent_limit_0.9fy_MPa"],
            "clause": res["clause"], "source": "IRC22_2014",
        }

    # IRC 22:2015 Cl.604.3.2 — deflection limits (live+impact ≤ L/800, total ≤ L/600).
    def compute_deflection_limits(self) -> dict:
        res = IRC22_2014.cl_604_3_2_deflection_limits(span_m=self.geo.span)
        main = res["main_girder_limits"]
        return {
            "span_mm": res["span_mm"],
            "defl_limit_live_mm": main["allow_live_impact_mm"],
            "defl_limit_total_mm": main["allow_total_mm"],
            "clause": res["clause"], "source": "IRC22_2014",
        }

    # IRC 22:2015 Cl.605.2 / 605.3 / 605.4 — thickness correction μr, f_f, τ_f, f_fd, τ_fd.
    def compute_fatigue(self, stress_range_MPa: float = 0.0) -> dict:
        fat = self.fatigue
        mat = self.mat
        tp = max(self.sec.tf_top, self.sec.tf_bot)

        # Cl.605.2 — thickness correction factor μr (welded + tp>25 mm only).
        design = IRC22_2014.cl_605_2_fatigue_design(
            tp_mm=tp,
            f_MPa=max(stress_range_MPa, 1e-6),
            Nsc=fat.Nsc,
            section_type=self.sec.fabrication,
            gamma_mft=mat.gamma_mft,
        )
        mu_r = design["mu_r"]

        # Cl.605.3 — design fatigue stress ranges f_f and τ_f for Nsc cycles.
        strength = IRC22_2014.cl_605_3_fatigue_strength(
            Nsc=fat.Nsc, section_type=self.sec.fabrication, ffn=fat.ffn, tfn=fat.tfn,
        )

        # Cl.605.4 — design fatigue strengths after μr and γmft.
        assessment = IRC22_2014.cl_605_4_fatigue_assessment(
            ff=strength["f_f_normal_MPa"],
            tf=strength["tau_f_shear_MPa"],
            mu_r=mu_r,
            gamma_mft=mat.gamma_mft,
            fy=mat.fy,
        )

        f_fd = assessment["f_fd_MPa"]                                                                                                                                                                                                    
        tau_fd = assessment["tau_fd_MPa"] 

        return {
            "mu_r": mu_r,
            "f_f_MPa": strength["f_f_normal_MPa"],
            "tau_f_MPa": strength["tau_f_shear_MPa"],
            "f_fd_MPa": f_fd,
            "tau_fd_MPa": tau_fd,
            "f_fd_eff_MPa": min(f_fd, 1.5 * mat.fy),
            "tau_fd_eff_MPa": min(tau_fd, 1.5 * 0.43 * mat.fy),
            "Nsc": fat.Nsc,
            "exempt_stress_check": design["stress_condition_ok"],
            "clause": "IRC 22:2015 - Cl.605.2 / 605.3 / 605.4",
            "source": "IRC22_2014",
        }

    # IRC 22:2015 Cl.606.3.1 — headed-stud design strength Qu (Eq 6.1: min of steel and concrete modes).
    def compute_stud_capacity(self) -> dict:
        stud = self.studs
        mat = self.mat
        res = IRC22_2014.cl_606_3_1_stud_connector_strength(
            d_mm=stud.diameter,
            hs_mm=stud.height,
            fu_MPa=stud.fu,
            fck_cu_MPa=mat.fck,
            Ecm_MPa=mat.Ecm,
            gamma_v=mat.gamma_v,
            use_table7_reference=False,
            debug=True,
        )
        return {
            "Qu_kN": res["Qu_kN"],
            "Qu_steel_kN": res["Qu_steel_kN"],
            "Qu_conc_kN": res["Qu_concrete_kN"],
            "governs": res["governing_mode"],
            "alpha": res["alpha"],
            "fck_cyl_MPa": res["fck_cyl_MPa"],
            "clause": res["clause"],
            "source": "IRC22_2014",
        }

    # IRC 22:2015 Cl.606.4.1 — required headed-stud spacing at ULS (longitudinal shear).
    def compute_stud_spacing(self, Vu_kN: float, beff_mm: float,
                              xu_mm: float, Qu_kN: float,
                              Ic_mm4: float = None) -> dict:
        mat, slab = self.mat, self.slab
        n_studs = self.studs.n_per_section

        res = IRC22_2014.cl_606_4_1_longitudinal_shear_and_spacing(
            V_kN=Vu_kN,
            beff_mm=beff_mm,
            xu_mm=xu_mm,
            t_slab_mm=slab.thickness,
            Qu_kN=Qu_kN,
            Es_MPa=mat.Es,
            Ecm_MPa=mat.Ecm,
            Ic_mm4=Ic_mm4,
            studs_per_section=n_studs,
        )
        return {
            "modular_ratio"      : res["n_modular_ratio"],
            "VL_N_per_mm"        : res["VL_N_per_mm"],
            "spacing_mm"         : res["spacing_mm"],
            "n_studs_per_section": n_studs,
            "clause"             : res["clause"],
            "source"             : "IRC22_2014",
        }

    # IRC 22:2015 Cl.606.3.2 — fatigue capacity of headed studs (Qr).
    def compute_stud_fatigue_capacity(self) -> dict:
        stud = self.studs
        fat = self.fatigue
        res = IRC22_2014.cl_606_3_2_stud_connector_fatigue_strength(
            Nsc=fat.Nsc,
            stud_d_mm=stud.diameter,
            use_table8=True,
        )
        return {
            "tau_f_MPa" : res["tau_f_MPa"],
            "Qr_kN"     : res.get("Qr_table8_kN"),
            "Nsc"       : fat.Nsc,
            "clause"    : res["clause"],
            "source"    : "IRC22_2014",
        }

    # IRC 22:2015 Cl.606.4.1.1 — full shear connection spacing (SL2).
    def compute_stud_full_shear_spacing(
        self, beff_mm: float, xu_mm: float, Qu_kN: float
    ) -> dict:
        sec, mat, slab = self.sec, self.mat, self.slab
        n_studs = self.studs.n_per_section
        shear_span_mm = self.geo.span * 1000.0 / 2.0   # L/2 for simply supported

        res = IRC22_2014.cl_606_4_1_1_full_shear_spacing(
            As_mm2=sec.A_steel,
            fyk_MPa=mat.fy,
            fck_cu_MPa=mat.fck,
            beff_mm=beff_mm,
            xu_mm=xu_mm,
            t_slab_mm=slab.thickness,
            Qu_kN=Qu_kN,
            shear_span_mm=shear_span_mm,
            studs_per_section=n_studs,
        )
        return {
            "H1_kN"           : res["H1_kN"],
            "H2_kN"           : res["H2_kN"],
            "H_governing_kN"  : res["H_governing_kN"],
            "shear_span_mm"   : shear_span_mm,
            "spacing_mm"      : res["spacing_mm"],
            "clause"          : res["clause"],
            "source"          : "IRC22_2014",
        }

    # IRC 22:2015 Cl.606.4.2 — SLS fatigue stud spacing (SR).
    def compute_stud_fatigue_spacing(
        self, Vr_kN: float, beff_mm: float, xu_mm: float,
        Qr_kN: float, I_comp_mm4: float
    ) -> dict:
        mat, slab = self.mat, self.slab
        n_studs = self.studs.n_per_section
        n = mat.Es / mat.Ecm

        res = IRC22_2014.cl_606_4_2_fatigue_shear_spacing(
            Vr_kN=Vr_kN,
            beff_mm=beff_mm,
            xu_mm=xu_mm,
            t_slab_mm=slab.thickness,
            I_composite_mm4=I_comp_mm4,
            Qu_kN=Qr_kN,
            n=n,
            studs_per_section=n_studs,
        )
        return {
            "Vr_kN"         : Vr_kN,
            "Aec_mm2"       : res["Aec_mm2"],
            "Y_mm"          : res["Y_mm"],
            "Vr_per_mm_kN"  : res["Vr_per_mm_kN"],
            "spacing_mm"    : res["spacing_SR_mm"],
            "clause"        : res["clause"],
            "source"        : "IRC22_2014",
        }

    # IRC 22:2015 Cl.606.6 — detailing checks for headed studs.
    def compute_stud_detailing(self) -> dict:
        stud, sec, slab = self.studs, self.sec, self.slab
        res = IRC22_2014.cl_606_6_shear_connector_detailing(
            d_stud_mm=stud.diameter,
            h_stud_mm=stud.height,
            t_flange_mm=sec.tf_top,
            t_slab_mm=slab.thickness,
        )
        return {
            "stud_diameter_check" : res["stud_diameter_check"],
            "stud_height_check"   : res["stud_height_check"],
            "stud_head_check"     : res.get("stud_head_check"),
            "edge_distance_check" : res.get("edge_distance_check"),
            "projection_check"    : res.get("projection_check"),
            "clear_cover_check"   : res.get("clear_cover_check"),
            "all_ok"              : res["all_requirements_satisfied"],
            "clause"              : res["clause"],
            "source"              : "IRC22_2014",
        }

    # IRC 22:2015 Cl.606.10 — transverse shear check at the steel–concrete interface.
    def compute_transverse_shear(self, VL_N_per_mm: float) -> dict:
        sec, mat, slab, studs = self.sec, self.mat, self.slab, self.studs
        # Shear plane length for interior girder: shorter of slab thickness or (2*hstud + bf_top).
        L_mm = min(slab.thickness, 2.0 * studs.height + sec.bf_top)
        # Transverse reinforcement: top + bot rebar area (mm²) converted to cm².
        # n_layers = 6 accounts for bars within 1 m at a 200 mm longitudinal spacing.
        Ast_cm2_per_m = (slab.rebar_area_top + slab.rebar_area_bot) / 100.0
        n_layers = 6
        res = IRC22_2014.cl_606_10_transverse_shear_check(
            VL_kN=VL_N_per_mm,          # N/mm ≡ kN/m
            fck=mat.fck,
            fyk=mat.fy_rebar,
            L_mm=L_mm,
            Ast_cm2_per_m=Ast_cm2_per_m,
            n_layers=n_layers,
        )
        return {
            "VL_N_per_mm"                : VL_N_per_mm,
            "L_shear_plane_mm"           : L_mm,
            "Ast_provided_cm2_per_m"     : Ast_cm2_per_m,
            "n_layers"                   : n_layers,
            "Vcap1_kN_per_m"             : res["Vcap1_kN_per_m"],
            "Vcap2_kN_per_m"             : res["Vcap2_kN_per_m"],
            "governing_capacity_kN_per_m": res["governing_capacity_kN_per_m"],
            "check_ok"                   : res["check_ok"],
            "min_Ast_required_cm2_per_m" : res["min_Ast_required_cm2_per_m"],
            "Ast_provided_ok"            : res["Ast_provided_ok"],
            "clause"                     : res["clause"],
            "source"                     : "IRC22_2014",
        }

    # ==============================================================================
    # STIFFENER CHECKS — IRC 24-2010 Cl.509.7 / IS 800:2007 Cl.8.7
    # TODO: Move these functions to IS800_2007 when ready.
    # ==============================================================================

    def compute_intermediate_stiffener(self) -> dict:
        """Intermediate transverse stiffener checks per IRC 24-2010 Cl.509.7.2 / IS 800 Cl.8.7.2.

        Always computes geometry-based required dimensions (H_max, tq_req, c_req).
        Runs verification checks only when c_mm / tq_mm / H_mm are all provided.
        """
        sec, mat = self.sec, self.mat
        d    = sec.dw
        tw   = sec.tw
        fy   = mat.fy
        E    = mat.Es
        gm0  = mat.gamma_m0
        eps  = math.sqrt(250.0 / fy)

        # Physical outstand limit — stiffener must fit between web and flange edge (both sides)
        H_max = (min(sec.bf_top, sec.bf_bot) - tw) / 2.0

        # Minimum tq to satisfy the outstanding-leg limit at H_max
        tq_req_1sided = H_max / (14.0 * eps) if eps > 0 else 0.0
        tq_req_2sided = H_max / (20.0 * eps) if eps > 0 else 0.0

        cfg = self.cfg.stiffener
        full_check = cfg and cfg.c_mm > 0 and cfg.tq_mm > 0 and cfg.H_mm > 0

        if not full_check:
            # Design guidance: compute required spacing for the minimum viable plate
            # Assume one-sided (conservative), tq = tq_req_1sided, H = H_max
            tq_des  = tq_req_1sided
            Iys_des = tq_des * H_max**3 / 3.0   # flat-plate one-sided, about face of web
            # Minimum c such that Iys_min(c) ≤ Iys_des (from 1.5·d³·tw³/c² ≤ Iys_des)
            c_req = (math.sqrt(1.5 * d**3 * tw**3 / Iys_des)
                     if Iys_des > 0 else 0.0)
            # If c_req/d ≥ √2 the simpler formula 0.75·d·tw³ governs and is always satisfiable
            if c_req > 0 and (c_req / d) >= math.sqrt(2.0):
                c_req = 0.0
            return {
                "design_guidance"    : True,
                "H_max_mm"           : round(H_max, 1),
                "tq_req_1sided_mm"   : round(tq_req_1sided, 2),
                "tq_req_2sided_mm"   : round(tq_req_2sided, 2),
                "c_req_min_mm"       : round(c_req, 1),
                "Iys_at_Hmax_mm4"    : round(Iys_des, 1),
            }

        # ── Full verification ────────────────────────────────────────────────────────
        c       = cfg.c_mm
        tq      = cfg.tq_mm
        H       = cfg.H_mm
        n_sides = cfg.n_sides

        # Cl.509.7.2.4 — outstanding leg limit
        H_limit = (14.0 if n_sides == 1 else 20.0) * tq * eps
        # Minimum tq needed for the provided H to satisfy the leg limit
        tq_req_provided = H / ((14.0 if n_sides == 1 else 20.0) * eps)

        # Cl.509.7.2.4 — minimum MI
        if (c / d) < math.sqrt(2.0):
            Iys_min     = 1.5 * d**3 * tw**3 / c**2
            iys_formula = "1.5·d³·tw³/c²"
        else:
            Iys_min     = 0.75 * d * tw**3
            iys_formula = "0.75·d·tw³"

        # Provided MI — auto-compute from flat-plate formula when not explicitly given
        if cfg.Iys_mm4 > 0:
            Iys_prov = cfg.Iys_mm4
        elif n_sides == 1:
            Iys_prov = tq * H**3 / 3.0
        else:
            Iys_prov = 2.0 * (tq * H**3 / 12.0 + tq * H * (tw / 2.0 + H / 2.0)**2)

        # Cl.509.7.2.5 — buckling check
        h_w_strip = min(20.0 * tw, c / 2.0)
        Aeff      = n_sides * H * tq + n_sides * h_w_strip * tw
        Astiff    = n_sides * H * tq

        rys  = math.sqrt(Iys_prov / Aeff) if Aeff > 0 else 0.0
        KL   = 0.7 * d
        KL_r = KL / rys if rys > 0 else 1e9

        fcd    = IS800_2007.cl_7_1_2_1_design_compressisive_stress_plategirder(fy, gm0, KL_r, E)
        Fqd_kN = fcd * Astiff / 1000.0
        Fq_kN  = max((cfg.V_kN - cfg.Vcr_kN) / gm0, 0.0)

        return {
            "design_guidance"    : False,
            "H_max_mm"           : round(H_max, 1),
            "tq_req_1sided_mm"   : round(tq_req_1sided, 2),
            "tq_req_2sided_mm"   : round(tq_req_2sided, 2),
            "H_mm"               : H,
            "H_limit_mm"         : round(H_limit, 3),
            "H_limit_type"       : f"{'14' if n_sides == 1 else '20'}·tq·ε",
            "tq_req_provided_mm" : round(tq_req_provided, 2),
            "Iys_prov_mm4"       : round(Iys_prov, 3),
            "Iys_min_mm4"        : round(Iys_min, 3),
            "iys_formula"        : iys_formula,
            "h_w_strip_mm"       : round(h_w_strip, 3),
            "Aeff_mm2"           : round(Aeff, 3),
            "Astiff_mm2"         : round(Astiff, 3),
            "rys_mm"             : round(rys, 3),
            "KL_mm"              : round(KL, 3),
            "KL_r"               : round(KL_r, 3),
            "alpha"              : 0.49,
            "fcd_MPa"            : round(fcd, 3),
            "Fqd_kN"             : round(Fqd_kN, 3),
            "Fq_kN"              : round(Fq_kN, 3),
        }

    def compute_bearing_stiffener(self) -> dict:
        """Bearing stiffener checks per IRC 24-2010 Cl.509.7.3 / IS 800 Cl.8.7.3.

        Requires bs_R_kN > 0 (reaction known).
        Runs full verification when bs_tq_mm and bs_H_mm are also provided;
        otherwise returns design guidance (required tq) for the given R.
        """
        cfg = self.cfg.stiffener
        if not cfg or cfg.bs_R_kN <= 0:
            return {"skipped": True}

        sec, mat = self.sec, self.mat
        d    = sec.dw
        tw   = sec.tw
        fy   = mat.fy
        E    = mat.Es
        gm0  = mat.gamma_m0
        eps  = math.sqrt(250.0 / fy)

        R        = cfg.bs_R_kN
        n_plates = cfg.bs_n_plates or 2

        # Physical outstand limit (same formula as intermediate stiffener)
        H_max = (min(sec.bf_top, sec.bf_bot) - tw) / 2.0

        full_check = cfg.bs_tq_mm > 0 and cfg.bs_H_mm > 0

        if not full_check:
            # Design guidance: minimum tq from bearing contact check at H_max
            fcd_y = fy / gm0
            tq_req_bearing = (R * 1000.0 / (fcd_y * n_plates * H_max)
                              if H_max > 0 and fcd_y > 0 else 0.0)
            # Minimum tq for outstanding leg at H_max (one-sided limit, conservative)
            tq_req_leg = H_max / (14.0 * eps) if eps > 0 else 0.0
            tq_req = max(tq_req_bearing, tq_req_leg)
            return {
                "design_guidance"   : True,
                "H_max_mm"          : round(H_max, 1),
                "tq_req_bearing_mm" : round(tq_req_bearing, 2),
                "tq_req_leg_mm"     : round(tq_req_leg, 2),
                "tq_req_mm"         : round(tq_req, 2),
                "n_plates"          : n_plates,
                "R_kN"              : R,
            }

        # ── Full verification ────────────────────────────────────────────────────────
        tq = cfg.bs_tq_mm
        H  = cfg.bs_H_mm

        # b1: stiff bearing length — user-provided or auto from IS 800 Cl.8.7.1.3
        if cfg.bs_b1_mm > 0:
            b1 = cfg.bs_b1_mm
        else:
            b1 = IS800_2007.cl_8_7_1_3_stiff_bearing_length(R, tw, sec.tf_top, 0.0, fy)

        # Bearing stiffener MI — auto-compute (two-sided flat plates about CL of web) if not given
        if cfg.bs_Iys_mm4 > 0:
            Iys = cfg.bs_Iys_mm4
        else:
            Iys = 2.0 * (tq * H**3 / 12.0 + tq * H * (tw / 2.0 + H / 2.0)**2)

        KL = 0.7 * d

        # Cl.509.7.3.1 / IS 800 8.7.3.1 — Web buckling check
        # Checks if the unstiffened web bearing zone can carry R (Euler stress, no imperfection reduction).
        n1      = d / 2.0
        A_wb    = (b1 + n1) * tw
        rys_wb  = math.sqrt(Iys / A_wb) if A_wb > 0 else 0.0
        KL_r_wb = KL / rys_wb if rys_wb > 0 else 1e9
        fcc_wb  = (math.pi**2 * E) / KL_r_wb**2
        Fcdw_wb_kN = fcc_wb * A_wb / 1000.0

        # Cl.509.7.3.2 / IS 800 8.7.3.2 — Local crushing check
        n2         = 2.5 * sec.tf_top
        A_lc       = (b1 + n2) * tw
        fcd_y      = fy / gm0
        Fcdw_lc_kN = fcd_y * A_lc / 1000.0

        # Cl.509.7.3.3 / IS 800 8.7.3.3 — Bearing contact check
        Aq      = n_plates * H * tq
        Fpsd_kN = fcd_y * Aq / 1000.0
        # Minimum tq required for the bearing check to pass
        tq_req_bearing = (R * 1000.0 / (fcd_y * n_plates * H) if H > 0 and fcd_y > 0 else 0.0)

        # Cl.509.7.1.5 / 509.7.2.5 — Stiffener column buckling check
        h_w_strip = 20.0 * tw
        Aeff_bs   = 2 * H * tq + 2 * h_w_strip * tw
        rys_bs    = math.sqrt(Iys / Aeff_bs) if Aeff_bs > 0 else 0.0
        KL_r_bs   = KL / rys_bs if rys_bs > 0 else 1e9

        fcd_bs = IS800_2007.cl_7_1_2_1_design_compressisive_stress_plategirder(fy, gm0, KL_r_bs, E)
        Fcd_kN = fcd_bs * Aeff_bs / 1000.0

        # Outstanding leg limit for the provided plate
        H_limit_bs = 14.0 * tq * eps        # one-sided (conservative); bearing stiffeners are two-sided
        tq_req_leg = H / (14.0 * eps) if eps > 0 else 0.0

        return {
            "design_guidance"   : False,
            "H_max_mm"          : round(H_max, 1),
            "tq_req_bearing_mm" : round(tq_req_bearing, 2),
            "tq_req_leg_mm"     : round(tq_req_leg, 2),
            "b1_mm"             : round(b1, 3),
            "n1_mm"             : round(n1, 3),
            "A_wb_mm2"          : round(A_wb, 3),
            "rys_wb_mm"         : round(rys_wb, 3),
            "KL_mm"             : round(KL, 3),
            "fcc_wb_MPa"        : round(fcc_wb, 3),
            "Fcdw_wb_kN"        : round(Fcdw_wb_kN, 3),
            "n2_mm"             : round(n2, 3),
            "A_lc_mm2"          : round(A_lc, 3),
            "fcd_y_MPa"         : round(fcd_y, 3),
            "Fcdw_lc_kN"        : round(Fcdw_lc_kN, 3),
            "n_plates"          : n_plates,
            "Aq_mm2"            : round(Aq, 3),
            "Fpsd_kN"           : round(Fpsd_kN, 3),
            "h_w_strip_mm"      : round(h_w_strip, 3),
            "Aeff_bs_mm2"       : round(Aeff_bs, 3),
            "rys_bs_mm"         : round(rys_bs, 3),
            "KL_r_bs"           : round(KL_r_bs, 3),
            "fcd_bs_MPa"        : round(fcd_bs, 3),
            "H_limit_bs_mm"     : round(H_limit_bs, 3),
            "Fcd_kN"            : round(Fcd_kN, 3),
            "R_kN"              : R,
        }

    # Orchestrator — runs every IRC 22:2015 clause computation into one CapacityResults.
    def compute_all(
        self,
        Vu_kN: float = 0.0,
        stress_range_MPa: float = 0.0,
        M_sls_kNm: float = 0.0,
        V_sls_kN: float = 0.0,
        Vr_kN: float = 0.0,              # Cl.606.4.2 — LL shear range for fatigue stud spacing
        provided_stud_spacing_mm: float = None,
    ) -> CapacityResults:
        results = CapacityResults()
        results.source = "IRC22_2014"

        # 1. Effective width
        eff_w = self.compute_effective_width()
        results.beff_mm = eff_w["beff_mm"]
        results.details["effective_width"] = eff_w

        # 2. Section classification
        sec_class = self.classify_section()
        results.details["section_class"] = sec_class

        # 3. Moment capacity
        moment = self.compute_moment_capacity(results.beff_mm)
        results.xu_mm = moment["xu_mm"]
        results.pna_location = moment["pna_location"]
        results.Mp_kNm = moment["Mp_kNm"]
        results.Md_kNm = moment["Md_kNm"]
        results.details["moment_capacity"] = moment

        # 4. Shear capacity
        shear = self.compute_shear_capacity()
        results.Av_mm2 = shear["Av_mm2"]
        results.Vn_kN = shear["Vn_kN"]
        results.Vd_kN = shear["Vd_kN"]
        results.details["shear_capacity"] = shear

        # 5. LTB buckling resistance — Stage 2: cross-bracings in place, LLT = cross-bracing spacing.
        ltb = self.compute_buckling_resistance(results.beff_mm,
                                               section_class=sec_class["governing_class"])
        results.Mcr_kNm = ltb["Mcr_kNm"]
        results.lambda_LT = ltb["lambda_LT"]
        results.chi_LT = ltb["chi_LT"]
        results.Mb_kNm = ltb["Mb_kNm"]
        results.details["buckling_resistance"] = ltb

        # 5b. LTB buckling resistance — Stage 1: girder only (no cross-bracings), LLT = full span.
        ltb_s1 = self.compute_buckling_resistance(
            results.beff_mm,
            section_class=sec_class["governing_class"],
            LLT_mm_override=self.geo.span * 1000.0,
        )
        results.Mb_kNm_stage1 = ltb_s1["Mb_kNm"]
        results.lambda_LT_stage1 = ltb_s1["lambda_LT"]
        results.chi_LT_stage1 = ltb_s1["chi_LT"]
        results.details["buckling_resistance_stage1"] = ltb_s1

        # 6. Combined bending + shear
        combined = self.compute_combined_bending_shear(
            results.Md_kNm, Vu_kN, results.Vd_kN
        )
        results.Mdv_kNm = combined["Mdv_kNm"]
        results.beta_interaction = combined["beta"]
        results.details["combined_bending_shear"] = combined

        # 7. Modular ratio
        results.details["modular_ratio"] = self.compute_modular_ratio()

        # 8. SLS stress limits
        sls_stress = self.compute_sls_stress_limits()
        results.sigma_c_limit_MPa = sls_stress["sigma_c_allow_MPa"]
        results.sigma_s_limit_MPa = sls_stress["sigma_steel_allow_MPa"]
        results.details["sls_stress_limits"] = sls_stress

        # 9. Deflection limits
        defl = self.compute_deflection_limits()
        results.defl_limit_live_mm = defl["defl_limit_live_mm"]
        results.defl_limit_total_mm = defl["defl_limit_total_mm"]
        results.details["deflection_limits"] = defl

        # 10. Fatigue
        fatigue = self.compute_fatigue(stress_range_MPa=stress_range_MPa)
        results.f_fd_MPa = fatigue["f_fd_MPa"]
        results.tau_fd_MPa = fatigue["tau_fd_MPa"]
        results.f_fd_eff_MPa = fatigue["f_fd_eff_MPa"]
        results.tau_fd_eff_MPa = fatigue["tau_fd_eff_MPa"]
        results.details["fatigue"] = fatigue

        # 11. Shear stud capacity
        stud_cap = self.compute_stud_capacity()
        results.Qu_kN = stud_cap["Qu_kN"]
        results.details["stud_capacity"] = stud_cap

        # 12. Composite section properties (Cl.604.3) — computed before stud spacing so that
        # the elastic I_comp can be passed to cl_606_4_1 instead of recomputing it there.
        comp_props = self.compute_composite_section_props(results.beff_mm)
        short = comp_props["short_term"]
        results.I_comp_short_mm4 = short["I_comp_mm4"]
        results.y_top_comp_mm    = short["y_top_mm"]
        results.y_bot_comp_mm    = short["y_bot_mm"]
        results.details["composite_section_props"] = comp_props

        # 13. Stud spacing (ULS) — passes pre-computed I_comp to avoid duplicate calculation.
        if Vu_kN > 0 and results.xu_mm > 0:
            stud_sp = self.compute_stud_spacing(
                Vu_kN, results.beff_mm, results.xu_mm, results.Qu_kN,
                Ic_mm4=results.I_comp_short_mm4,
            )
            results.stud_spacing_mm = stud_sp["spacing_mm"]
            results.VL_N_per_mm = stud_sp["VL_N_per_mm"]
            results.details["stud_spacing"] = stud_sp

        # 13b. Fatigue stud capacity (Cl.606.3.2).
        stud_fat_cap = self.compute_stud_fatigue_capacity()
        results.Qr_kN = stud_fat_cap.get("Qr_kN") or 0.0
        results.details["stud_fatigue_capacity"] = stud_fat_cap

        # 13c. Full shear connection spacing (Cl.606.4.1.1).
        if results.xu_mm > 0:
            full_sp = self.compute_stud_full_shear_spacing(
                results.beff_mm, results.xu_mm, results.Qu_kN
            )
            results.stud_spacing_full_shear_mm = full_sp["spacing_mm"]
            results.details["stud_spacing_full_shear"] = full_sp

        # 13d. Fatigue stud spacing (Cl.606.4.2).
        if Vr_kN > 0 and results.Qr_kN > 0 and results.I_comp_short_mm4 > 0:
            fat_sp = self.compute_stud_fatigue_spacing(
                Vr_kN, results.beff_mm, results.xu_mm,
                results.Qr_kN, results.I_comp_short_mm4,
            )
            results.stud_spacing_fatigue_mm = fat_sp["spacing_mm"]
            results.details["stud_spacing_fatigue"] = fat_sp

        # 13e. Governing spacing = min(SL1, SL2, SR) — ignores any that were not computed.
        _spacing_candidates = [s for s in [
            results.stud_spacing_mm,
            results.stud_spacing_full_shear_mm,
            results.stud_spacing_fatigue_mm,
        ] if s > 0]
        results.stud_spacing_governing_mm = min(_spacing_candidates) if _spacing_candidates else 0.0

        # 13f. Stud detailing (Cl.606.6).
        detailing = self.compute_stud_detailing()
        results.stud_detailing_ok = detailing["all_ok"]
        results.details["stud_detailing"] = detailing

        # 14. SLS actual stress checks (Cl.604.3.1) — only when M_sls_kNm provided.
        sls_actual = self.compute_sls_stresses(              
            beff_mm=results.beff_mm,
            M_sls_kNm=M_sls_kNm,
            V_sls_kN=V_sls_kN,
            comp_props=comp_props,
        )
        results.details["sls_actual_stresses"] = sls_actual
        if not sls_actual.get("skipped"):                    
            results.sigma_c_actual_MPa    = sls_actual["sigma_c_MPa"]      
            results.sigma_rebar_actual_MPa = sls_actual["sigma_rebar_MPa"] 
            results.sigma_steel_equiv_MPa = sls_actual["fe_max_MPa"]       
            results.tau_web_actual_MPa    = sls_actual["tau_b_MPa"]        
            results.sigma_rebar_limit_MPa = sls_actual["sigma_rebar_limit_MPa"]  

        # 15. Crack control — minimum reinforcement (Cl.604.4).
        crack = self.compute_crack_control(results.beff_mm)  
        results.As_min_crack_mm2      = crack["As_min_mm2"]   
        results.As_provided_crack_mm2 = crack["As_provided_mm2"]  
        results.details["crack_control"] = crack

        # 16. Shear connector spacing limits (Cl.606.9).
        stud_lim = self.compute_stud_spacing_limits(         
            provided_spacing_mm=provided_stud_spacing_mm
        )
        results.stud_spacing_max_mm = stud_lim["max_spacing_mm"]
        results.stud_spacing_min_mm = stud_lim["min_spacing_mm"]
        results.details["stud_spacing_limits"] = stud_lim

        # Resolve provided spacing now that max_spacing is known.
        # User-supplied spacing is used as-is.
        # If not given, default = min(governing_required, max_spacing): geometry always governs
        # when the loading demand allows wider spacing than the code geometric limit.
        results.stud_spacing_user_provided = (provided_stud_spacing_mm is not None)
        results.stud_spacing_provided_mm = (
            provided_stud_spacing_mm if provided_stud_spacing_mm is not None
            else min(results.stud_spacing_governing_mm, results.stud_spacing_max_mm)
                 if results.stud_spacing_governing_mm > 0 else 0.0
        )

        # 17. Transverse shear check (Cl.606.10).
        if results.VL_N_per_mm > 0:
            trans_shear = self.compute_transverse_shear(results.VL_N_per_mm)
            results.transverse_shear_ok = trans_shear["check_ok"]
            results.Ast_required_cm2_per_m = trans_shear["min_Ast_required_cm2_per_m"]
            results.Ast_provided_cm2_per_m = trans_shear["Ast_provided_cm2_per_m"]
            results.details["transverse_shear"] = trans_shear

        # 18. Intermediate stiffener checks (IRC 24-2010 Cl.509.7.2 / IS 800 Cl.8.7.2).
        # Opt-in by setting cfg.stiffener to any StiffenerConfig. Runs guidance when c/tq/H not given.
        if self.cfg.stiffener is not None:
            is_res = self.compute_intermediate_stiffener()
            results.details["intermediate_stiffener"] = is_res
            if not is_res.get("skipped") and not is_res.get("design_guidance"):
                results.is_H_limit_mm   = is_res["H_limit_mm"]
                results.is_Iys_min_mm4  = is_res["Iys_min_mm4"]
                results.is_Iys_prov_mm4 = is_res["Iys_prov_mm4"]
                results.is_Fqd_kN       = is_res["Fqd_kN"]
                results.is_Fq_kN        = is_res["Fq_kN"]

        # 19. Bearing stiffener checks (IRC 24-2010 Cl.509.7.3 / IS 800 Cl.8.7.3).
        # Requires bs_R_kN > 0. Runs guidance when tq/H not given.
        if self.cfg.stiffener is not None and self.cfg.stiffener.bs_R_kN > 0:
            bs_res = self.compute_bearing_stiffener()
            results.details["bearing_stiffener"] = bs_res
            if not bs_res.get("skipped") and not bs_res.get("design_guidance"):
                results.bs_Fcdw_wb_kN = bs_res["Fcdw_wb_kN"]
                results.bs_Fcdw_lc_kN = bs_res["Fcdw_lc_kN"]
                results.bs_Fpsd_kN    = bs_res["Fpsd_kN"]
                results.bs_Fcd_kN     = bs_res["Fcd_kN"]
                results.bs_R_kN       = bs_res["R_kN"]

        return results


# ======================================================================
#  SECTION 4 -- DCR ENGINE (Demand-to-Capacity Ratios)
# ======================================================================


@dataclass
class CheckResult:
    # Single row of the design-check table (one IRC clause evaluated).
    check_id: int
    name: str
    clause: str
    demand: float
    demand_unit: str
    capacity: float
    capacity_unit: str
    dcr: float
    status: str                                         # PASS | WARN | FAIL | INFO
    note: str = ""


class DCREngine:
    # Demand/Capacity ratio engine — PASS < DCR_PASS_THRESHOLD, WARN to DCR_FAIL_THRESHOLD, FAIL ≥.
    # Thresholds sourced from keyfile to avoid duplication.
    PASS_THRESHOLD = DCR_PASS_THRESHOLD
    FAIL_THRESHOLD = DCR_FAIL_THRESHOLD

    def __init__(self, demand: DemandEnvelope, capacity: CapacityResults):
        self.demand = demand
        self.capacity = capacity
        self.checks: List[CheckResult] = []

    @staticmethod
    def classify(dcr: float) -> str:
        if dcr < DCREngine.PASS_THRESHOLD:
            return "PASS"
        elif dcr < DCREngine.FAIL_THRESHOLD:
            return "WARN"
        return "FAIL"

    def _add_check(self, check_id, name, clause, demand, capacity, unit, note=""):
        if capacity > 0:
            dcr = demand / capacity
            status = self.classify(dcr)
        else:
            dcr = float("inf")
            status = "FAIL"

        result = CheckResult(
            check_id=check_id, name=name, clause=clause,
            demand=round(demand, 2), demand_unit=unit,
            capacity=round(capacity, 2), capacity_unit=unit,
            dcr=round(dcr, 4), status=status, note=note,
        )
        self.checks.append(result)
        return result

    # Run all IRC 22:2015 design checks — mapped to the 8 output-dock categories.    # ←── CHANGED
    def run_all_checks(self) -> List[CheckResult]:
        self.checks.clear()
        d, c = self.demand, self.capacity

        # ── CATEGORY 1: Strength Limit State (Flexure) ───────────────────────
        self._add_check(1, "ULS Flexure", "Cl.603.3.1",
                         d.Mu_kNm, c.Md_kNm, "kNm",
                         note=f"PNA in {c.pna_location}, xu={c.xu_mm:.1f} mm")

        # ── CATEGORY 2: Strength Limit State (Shear) ─────────────────────────
        self._add_check(2, "ULS Shear", "Cl.603.3.3.2",
                         d.Vu_kN, c.Vd_kN, "kN",
                         note=f"Av={c.Av_mm2:.0f} mm²")

        # ── CATEGORY 3: Interaction ───────────────────────────────────────────
        # 3a. Moment–Shear interaction (Cl.603.3.3.3)
        effective_Md = c.Mdv_kNm if c.beta_interaction > 0 else c.Md_kNm
        self._add_check(3, "M-V Interaction", "Cl.603.3.3.3",
                         d.Mu_kNm, effective_Md, "kNm",
                         note=f"beta={c.beta_interaction:.4f}")

        # 3b. Moment–Axial interaction (Cl.603.3.3.3)
        # NRd = Ag × fy / γm0  (yielding of gross steel section under compression/tension)
        if d.Nu_kN > 0.0:                                               
            _moment_det = c.details.get("moment_capacity", {})          
            _gamma_m0   = _moment_det.get("gamma_m0", 1.1)             
            _shear_det  = c.details.get("shear_capacity", {})          
            _fyw        = _shear_det.get("fyw_MPa", 350.0)             
            _Av         = _shear_det.get("Av_mm2", 0.0)                            
            _Ag         = sec.A_steel
            NRd_kN      = _Ag * _fyw / _gamma_m0 / 1e3 if _Ag > 0.0 else 0.0  
            if NRd_kN > 0.0 and c.Md_kNm > 0.0:                        
                interaction_ratio = d.Nu_kN / NRd_kN + d.Mu_kNm / c.Md_kNm  
                self._add_check(4, "M-N Interaction", "Cl.603.3.3.3",  
                                 interaction_ratio, 1.0, "–",           
                                 note=f"Nu/NRd + Mu/MRd = {interaction_ratio:.3f}")            

        # ── CATEGORY 4: Lateral Torsional Buckling ────────────────────────────
        # 4a. Construction Stage 1 — girder only, no cross-bracings, LLT = full span.
        if d.M_girder_sw_kNm > 0:
            Mb_s1 = c.Mb_kNm_stage1 if c.Mb_kNm_stage1 > 0 else c.Mb_kNm
            ltb_s1 = c.details.get("buckling_resistance_stage1", {})
            lLT_s1 = ltb_s1.get("lambda_LT", c.lambda_LT_stage1)
            chi_s1 = ltb_s1.get("chi_LT", c.chi_LT_stage1)
            LLT_s1 = ltb_s1.get("LLT_mm", 0.0)
            self._add_check(5, "LTB (Girder SW Only)", "Cl.603.3.3.1",
                             d.M_girder_sw_kNm, Mb_s1, "kNm",
                             note=(f"Stage 1: girder self-weight only, LLT=span={LLT_s1/1000:.1f}m; "
                                   f"λ_LT={lLT_s1:.4f}, χ_LT={chi_s1:.4f}"))

        # 4b. Construction Stage 2 — steel + wet concrete, cross-bracings in place, LLT = cb spacing.
        ltb_s2 = c.details.get("buckling_resistance", {})
        LLT_s2 = ltb_s2.get("LLT_mm", 0.0)
        self._add_check(5, "LTB (Construction Stage)", "Cl.603.3.3.1",
                         d.M_construction_kNm if d.M_construction_kNm > 0 else d.Mu_kNm,
                         c.Mb_kNm, "kNm",
                         note=(f"Stage 2: steel self-weight + wet concrete, LLT=cb_spacing={LLT_s2/1000:.1f}m; "
                               f"λ_LT={c.lambda_LT:.4f}, χ_LT={c.chi_LT:.4f}"))

        # ── CATEGORY 5: Resistance to Longitudinal & Transverse Shear ─────────
        s_prov = c.stud_spacing_provided_mm
        s_gov  = c.stud_spacing_governing_mm   # required governing spacing (min of SL1, SL2, SR)

        if c.stud_spacing_user_provided:
            # User gave an actual spacing — verify it against every requirement.
            # 5a. Provided ≤ SL1 (ULS).
            if c.stud_spacing_mm > 0.0:
                self._add_check(6, "Stud Spacing ULS (SL1)", "Cl.606.4.1",
                                 s_prov, c.stud_spacing_mm, "mm",
                                 note=f"Sprov={s_prov:.0f} ≤ SL1={c.stud_spacing_mm:.0f} mm")
            # 5b. Provided ≤ SL2 (full shear).
            if c.stud_spacing_full_shear_mm > 0.0:
                self._add_check(6, "Stud Spacing Full-Shear (SL2)", "Cl.606.4.1.1",
                                 s_prov, c.stud_spacing_full_shear_mm, "mm",
                                 note=f"Sprov={s_prov:.0f} ≤ SL2={c.stud_spacing_full_shear_mm:.0f} mm")
            # 5c. Provided ≤ SR (fatigue).
            if c.stud_spacing_fatigue_mm > 0.0:
                self._add_check(6, "Stud Spacing Fatigue (SR)", "Cl.606.4.2",
                                 s_prov, c.stud_spacing_fatigue_mm, "mm",
                                 note=f"Sprov={s_prov:.0f} ≤ SR={c.stud_spacing_fatigue_mm:.0f} mm")
            # 5d. Provided ≤ geometric max (Cl.606.9).
            self._add_check(7, "Stud Spacing ≤ Max (Cl.606.9)", "Cl.606.9",
                             s_prov, c.stud_spacing_max_mm, "mm",
                             note=f"Sprov={s_prov:.0f} ≤ max={c.stud_spacing_max_mm:.0f} mm")
            # 5e. Provided ≥ geometric min (Cl.606.9).
            self._add_check(7, "Stud Spacing ≥ Min (Cl.606.9)", "Cl.606.9",
                             c.stud_spacing_min_mm, s_prov, "mm",
                             note=f"min={c.stud_spacing_min_mm:.0f} ≤ Sprov={s_prov:.0f} mm")
        elif s_gov > 0.0:
            # No user spacing — check feasibility only.
            # SL1/SL2/SR are upper bounds on spacing; max_spacing is also an upper bound.
            # When s_gov > max_spacing, geometry governs and the design is fine (use max_spacing).
            # The one meaningful check: the governing effective spacing ≥ min_spacing (75 mm).
            s_eff = min(s_gov, c.stud_spacing_max_mm)
            self._add_check(7, "Stud Spacing Feasibility (Cl.606.9)", "Cl.606.9",
                             c.stud_spacing_min_mm, s_eff, "mm",
                             note=(f"min={c.stud_spacing_min_mm:.0f} ≤ "
                                   f"Seff=min(Sreq,max)={s_eff:.0f} mm"))

        # 5f. Stud detailing (Cl.606.6): demand=0 (all pass) or 1 (any fail).
        det = c.details.get("stud_detailing", {})
        if det:
            self._add_check(7, "Stud Detailing", "Cl.606.6",
                             0.0 if c.stud_detailing_ok else 1.0, 1.0, "–",
                             note="d≤2tf, h≥max(4d,100), edge≥25, cover≥25")    

        # ── CATEGORY 6: Resistance to Fatigue ────────────────────────────────
        if d.stress_range_MPa > 0 and c.f_fd_eff_MPa > 0:
            self._add_check(8, "Fatigue Normal Stress", "Cl.605",       
                             d.stress_range_MPa, c.f_fd_eff_MPa, "MPa",
                             note=f"Nsc={d.Nsc:,}")

        if d.shear_range_MPa > 0 and c.tau_fd_eff_MPa > 0:
            self._add_check(9, "Fatigue Shear Stress", "Cl.605",
                             d.shear_range_MPa, c.tau_fd_eff_MPa, "MPa",
                             note=f"Nsc={d.Nsc:,}")

        # ── CATEGORY 7: Stress Limitation (SLS) ──────────────────────────────
        # 7a. Concrete compressive stress (Cl.604.3.1)
        sls_act = c.details.get("sls_actual_stresses", {})             
        if not sls_act.get("skipped") and c.sigma_c_actual_MPa > 0.0:  
            self._add_check(10, "SLS Concrete Stress", "Cl.604.3.1",   
                             c.sigma_c_actual_MPa, c.sigma_c_limit_MPa, "MPa", 
                             note=f"Limit = 0.48 fck = {c.sigma_c_limit_MPa:.1f} MPa")  

        # 7b. Structural steel equivalent stress (Cl.604.3.1)
        if not sls_act.get("skipped") and c.sigma_steel_equiv_MPa > 0.0:  
            self._add_check(11, "SLS Steel Equiv. Stress", "Cl.604.3.1",  
                             c.sigma_steel_equiv_MPa, c.sigma_s_limit_MPa, "MPa",  
                             note=f"fe = √(fbc²+fp²+fbc·fp+3τ²) ≤ 0.9fy = {c.sigma_s_limit_MPa:.1f} MPa")  

        # 7c. Rebar tensile stress (Cl.604.3.1 / IRC 112 Cl.12.2.2)
        if not sls_act.get("skipped") and c.sigma_rebar_actual_MPa > 0.0 and c.sigma_rebar_limit_MPa > 0.0:  
            self._add_check(12, "SLS Rebar Stress", "Cl.604.3.1",      
                             c.sigma_rebar_actual_MPa, c.sigma_rebar_limit_MPa, "MPa",  
                             note=f"Limit = 0.80 fyk = {c.sigma_rebar_limit_MPa:.1f} MPa")  

        # ── CATEGORY 8: Deflection and Crack Control ──────────────────────────
        if d.delta_live_mm > 0:
            self._add_check(13, "SLS Deflection (Live)", "Cl.604.3.2", 
                             d.delta_live_mm, c.defl_limit_live_mm, "mm",
                             note="Limit = L/800")

        if d.delta_total_mm > 0:
            self._add_check(14, "SLS Deflection (Total)", "Cl.604.3.2",
                             d.delta_total_mm, c.defl_limit_total_mm, "mm",
                             note="Limit = L/600")

        # Crack control — minimum reinforcement check (Cl.604.4)
        if c.As_min_crack_mm2 > 0.0 and c.As_provided_crack_mm2 > 0.0:
            self._add_check(15, "Crack Control (As_min)", "Cl.604.4", 
                             c.As_min_crack_mm2, c.As_provided_crack_mm2, "mm²", 
                             note=(f"As_min={c.As_min_crack_mm2:.0f} mm², " 
                                   f"As_prov={c.As_provided_crack_mm2:.0f} mm²"))

        # ── CATEGORY 5 (cont.): Transverse Shear (Cl.606.10)
        ts = c.details.get("transverse_shear", {})
        if ts:
            self._add_check(16, "Transverse Shear (VL vs Vcap)", "Cl.606.10",
                            ts["VL_N_per_mm"], ts["governing_capacity_kN_per_m"], "kN/m",
                            note=f"L={ts['L_shear_plane_mm']:.0f} mm")
            if c.Ast_provided_cm2_per_m > 0.0:
                self._add_check(17, "Transverse Shear (Ast_min)", "Cl.606.10",
                            c.Ast_required_cm2_per_m, c.Ast_provided_cm2_per_m, "cm²/m",
                            note=(f"Ast_req={c.Ast_required_cm2_per_m:.3f}, "
                                  f"Ast_prov={c.Ast_provided_cm2_per_m:.3f} cm²/m"))

        # ── IRC 24-2010 STIFFENER CHECKS (Cl.509.7 / IS 800 Cl.8.7) ─────────────────
        # Intermediate transverse stiffener
        is_det = c.details.get("intermediate_stiffener", {})
        if is_det and not is_det.get("skipped"):
            if is_det.get("design_guidance"):
                # No dimensions provided — report required values as a single guidance row
                _note = (f"H_max={(is_det['H_max_mm']):.0f} mm = (bf_min−tw)/2; "
                         f"tq_req(1-sided)≥{is_det['tq_req_1sided_mm']:.1f} mm, "
                         f"tq_req(2-sided)≥{is_det['tq_req_2sided_mm']:.1f} mm")
                if is_det["c_req_min_mm"] > 0:
                    _note += f"; c_req≥{is_det['c_req_min_mm']:.0f} mm (from Iys check)"
                self._add_check(20, "Int.Stiff: Sizing Required", "Cl.509.7.2.4",
                                 0.0, 1.0, "–", note=_note)
            else:
                # Full verification — three separate checks
                # Cl.509.7.2.4 — outstanding leg: H ≤ H_limit
                self._add_check(20, "Int.Stiff: Leg ≤ H_limit", "Cl.509.7.2.4",
                                 is_det["H_mm"], is_det["H_limit_mm"], "mm",
                                 note=(f"{is_det['H_limit_type']}; "
                                       f"H_max={is_det['H_max_mm']:.0f} mm; "
                                       f"tq_req≥{is_det['tq_req_provided_mm']:.1f} mm"))
                # Cl.509.7.2.4 — MI: Iys_prov ≥ Iys_min
                self._add_check(20, "Int.Stiff: Iys ≥ Iys_min", "Cl.509.7.2.4",
                                 is_det["Iys_min_mm4"], is_det["Iys_prov_mm4"], "mm⁴",
                                 note=f"min={is_det['iys_formula']}")
                # Cl.509.7.2.5 — buckling (only when shear demand is positive)
                if is_det["Fq_kN"] > 0:
                    self._add_check(20, "Int.Stiff: Buckling Fqd≥Fq", "Cl.509.7.2.5",
                                     is_det["Fq_kN"], is_det["Fqd_kN"], "kN",
                                     note=(f"fcd={is_det['fcd_MPa']:.2f} MPa, α=0.49, "
                                           f"KL/r={is_det['KL_r']:.2f}"))

        # Bearing stiffener
        bs_det = c.details.get("bearing_stiffener", {})
        if bs_det and not bs_det.get("skipped"):
            R = bs_det["R_kN"]
            if bs_det.get("design_guidance"):
                # No dimensions provided — report required tq as a single guidance row
                self._add_check(21, "Brg.Stiff: Sizing Required", "Cl.509.7.3.3",
                                 0.0, 1.0, "–",
                                 note=(f"R={R:.1f} kN; H_max={bs_det['H_max_mm']:.0f} mm; "
                                       f"tq_req(bearing)≥{bs_det['tq_req_bearing_mm']:.1f} mm, "
                                       f"tq_req(leg)≥{bs_det['tq_req_leg_mm']:.1f} mm "
                                       f"(n_plates={bs_det['n_plates']})"))
            else:
                # Full verification — four separate checks
                # Cl.509.7.3.1 — web buckling (PASS = stiffener not needed; FAIL = stiffener needed)
                self._add_check(21, "Brg.Stiff: Web Buckling", "Cl.509.7.3.1",
                                 R, bs_det["Fcdw_wb_kN"], "kN",
                                 note=(f"fcc={bs_det['fcc_wb_MPa']:.2f} MPa, "
                                       f"A=(b1+n1)·tw={bs_det['A_wb_mm2']:.0f} mm²"))
                # Cl.509.7.3.2 — local crushing
                self._add_check(21, "Brg.Stiff: Local Crushing", "Cl.509.7.3.2",
                                 R, bs_det["Fcdw_lc_kN"], "kN",
                                 note=(f"fcd={bs_det['fcd_y_MPa']:.2f} MPa, "
                                       f"A=(b1+n2)·tw={bs_det['A_lc_mm2']:.0f} mm²"))
                # Cl.509.7.3.3 — bearing contact
                self._add_check(21, "Brg.Stiff: Bearing Contact", "Cl.509.7.3.3",
                                 R, bs_det["Fpsd_kN"], "kN",
                                 note=(f"fyd={bs_det['fcd_y_MPa']:.2f} MPa, "
                                       f"Aq={bs_det['Aq_mm2']:.0f} mm², "
                                       f"tq_req≥{bs_det['tq_req_bearing_mm']:.1f} mm"))
                # Cl.509.7.2.5 — stiffener column buckling
                self._add_check(21, "Brg.Stiff: Column Buckling", "Cl.509.7.2.5",
                                 R, bs_det["Fcd_kN"], "kN",
                                 note=(f"fcd={bs_det['fcd_bs_MPa']:.2f} MPa, α=0.49, "
                                       f"KL/r={bs_det['KL_r_bs']:.2f}"))

        return self.checks

    def overall_status(self) -> str:
        if not self.checks:
            return "NO CHECKS RUN"
        if any(c.status == "FAIL" for c in self.checks):
            return "FAIL"
        if any(c.status == "WARN" for c in self.checks):
            return "WARN"
        return "PASS"

    def max_dcr(self) -> float:
        return max((c.dcr for c in self.checks), default=0.0)

    def critical_check(self) -> CheckResult:
        return max(self.checks, key=lambda c: c.dcr)

    def n_pass(self) -> int:
        return sum(1 for c in self.checks if c.status == "PASS")

    def n_warn(self) -> int:
        return sum(1 for c in self.checks if c.status == "WARN")

    def n_fail(self) -> int:
        return sum(1 for c in self.checks if c.status == "FAIL")


# ======================================================================
#  SECTION 5 -- REPORT GENERATOR
# ======================================================================


class ReportGenerator:
    # Text-report formatter for BridgeConfig + DemandEnvelope + CapacityResults + DCREngine.

    LINE_WIDTH = 78
    BAR_WIDTH = 45

    def __init__(self, config: BridgeConfig, demand: DemandEnvelope,
                 capacity: CapacityResults, engine: DCREngine):
        self.cfg = config
        self.demand = demand
        self.capacity = capacity
        self.engine = engine

    def _header_box(self, *lines: str) -> str:
        w = self.LINE_WIDTH
        border = "=" * w
        out = [border]
        for line in lines:
            out.append(line.center(w))
        out.append(border)
        return "\n".join(out)

    def _section_title(self, title: str) -> str:
        return f"\n{title}\n{'-' * len(title)}"

    def _kv(self, key: str, value, unit: str = "", width: int = 24) -> str:
        if isinstance(value, float):
            val_str = f"{value:,.3f}" if value < 1 else f"{value:,.2f}"
        else:
            val_str = str(value)
        return f"  {key:<{width}}: {val_str} {unit}".rstrip()

    def _build_header(self) -> str:
        return self._header_box(
            "IRC 22:2015 COMPOSITE BRIDGE DESIGN CHECK REPORT",
            "Demand (Analyser)  -->  IRC 22 Capacity  -->  DCR Pipeline",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        )

    def _build_config(self) -> str:
        c, s, g, m, slab = self.cfg, self.cfg.section, self.cfg.geometry, self.cfg.material, self.cfg.slab
        lines = [self._section_title("BRIDGE CONFIGURATION")]
        lines.append(self._kv("Span", g.span, "m"))
        lines.append(self._kv("Support", g.support_type))
        lines.append(self._kv("Carriageway Width", g.carriageway_width, "m"))
        lines.append(self._kv("Girder Spacing", g.beam_spacing, "m"))
        lines.append(self._kv("No. of Girders", g.n_girders))
        lines.append(self._kv("Beam Type", g.beam_type))
        lines.append(self._kv("Steel Grade", m.steel_grade, f"(fy = {m.fy} MPa)"))
        lines.append(self._kv("Concrete Grade", m.concrete_grade, f"(fck = {m.fck} MPa)"))
        lines.append(self._kv("Rebar Grade", m.rebar_grade))

        lines.append(self._section_title(f"STEEL SECTION (Plate Girder - {s.fabrication.title()})"))
        lines.append(self._kv("Overall Depth D", s.D, "mm"))
        lines.append(self._kv("Top Flange", f"{s.bf_top} x {s.tf_top}", "mm"))
        lines.append(self._kv("Bottom Flange", f"{s.bf_bot} x {s.tf_bot}", "mm"))
        lines.append(self._kv("Web", f"{s.dw:.0f} x {s.tw}", "mm"))
        lines.append(self._kv("A_steel", f"{s.A_steel:,.0f}", "mm2"))
        lines.append(self._kv("Iz_steel", f"{s.Iz_steel:,.0f}", "mm4"))

        lines.append(self._section_title("CONCRETE SLAB"))
        lines.append(self._kv("Slab Thickness", slab.thickness, "mm"))
        lines.append(self._kv("Haunch Depth", slab.haunch_depth, "mm"))
        return "\n".join(lines)

    def _build_demands(self) -> str:
        d = self.demand
        lines = [self._section_title(f"DESIGN DEMANDS ({d.governing_combination})")]
        lines.append(self._kv("Location", d.location))
        lines.append(self._kv("Member", d.member))
        lines.append(self._kv("Source", d.source))
        lines.append("")
        lines.append(self._kv("Mu (factored)", d.Mu_kNm, "kNm"))
        lines.append(self._kv("Vu (factored)", d.Vu_kN, "kN"))
        if d.Nu_kN != 0:
            lines.append(self._kv("Nu (factored)", d.Nu_kN, "kN"))
        lines.append(self._kv("delta_live", d.delta_live_mm, "mm"))
        lines.append(self._kv("delta_total", d.delta_total_mm, "mm"))
        if d.stress_range_MPa > 0:
            lines.append(self._kv("Stress Range", d.stress_range_MPa, "MPa"))
        if d.shear_range_MPa > 0:
            lines.append(self._kv("Shear Range", d.shear_range_MPa, "MPa"))
        if d.Nsc > 0:
            lines.append(self._kv("Nsc", f"{d.Nsc:,}", "cycles"))
        if d.M_sls_kNm > 0:                                             
            lines.append(self._kv("M_sls (service)", d.M_sls_kNm, "kNm"))  
        if d.V_sls_kN > 0:                                              
            lines.append(self._kv("V_sls (service)", d.V_sls_kN, "kN"))    
        return "\n".join(lines)

    def _build_capacity_summary(self) -> str:
        c = self.capacity
        sc = c.details.get("section_class", {})
        sls = c.details.get("sls_actual_stresses", {})
        cmp = c.details.get("composite_section_props", {})
        crack = c.details.get("crack_control", {})
        stud_lim = c.details.get("stud_spacing_limits", {})
        lines = [self._section_title("IRC 22:2015 CAPACITY COMPUTATIONS")]

        lines.append(f"\n  1. Effective Width (Cl.603.2.1)")
        lines.append(f"     beff = {c.beff_mm:.1f} mm")

        lines.append(f"\n  2. Section Classification (Cl.603)")
        lines.append(f"     epsilon = {sc.get('epsilon', 0):.4f}")
        lines.append(f"     Web: {sc.get('web_class', '?')}  (d/tw = {sc.get('d_tw_ratio', 0):.1f})")
        lines.append(f"     Flange: {sc.get('flange_class', '?')}  (b/tf = {sc.get('b_tf_ratio', 0):.1f})")
        lines.append(f"     Governing: {sc.get('governing_class', '?')}")

        lines.append(f"\n  3. Positive Moment Capacity (Cl.603.3.1)")
        lines.append(f"     PNA Location: {c.pna_location}")
        lines.append(f"     xu = {c.xu_mm:.2f} mm")
        lines.append(f"     Mp = Md = {c.Md_kNm:,.2f} kNm  (γm0 and γc embedded)")

        lines.append(f"\n  4. Plastic Shear Resistance (Cl.603.3.3.2)")
        lines.append(f"     Av = {c.Av_mm2:,.0f} mm²")
        lines.append(f"     Vn = {c.Vn_kN:,.2f} kN")
        lines.append(f"     Vd = {c.Vd_kN:,.2f} kN")

        lines.append(f"\n  5. Buckling Resistance Moment (Cl.603.3.3.1)")
        lines.append(f"     Mcr = {c.Mcr_kNm:,.2f} kNm  |  λ_LT = {c.lambda_LT:.4f}  |  χ_LT = {c.chi_LT:.4f}")
        lines.append(f"     Mb = {c.Mb_kNm:,.2f} kNm")

        lines.append(f"\n  6. Bending–Shear Interaction (Cl.603.3.3.3)")
        lines.append(f"     beta = {c.beta_interaction:.4f}  |  Mdv = {c.Mdv_kNm:,.2f} kNm")

        # Composite section properties
        lines.append(f"\n  7. Composite Section Properties (Cl.604.3)")
        if cmp:
            st = cmp.get("short_term", {})
            lt = cmp.get("long_term",  {})
            lines.append(f"     Short-term (n={cmp.get('short_term',{}).get('n','?')}):  "
                         f"I = {st.get('I_comp_mm4',0):,.0f} mm⁴  |  "
                         f"y_top = {st.get('y_top_mm',0):.1f} mm  |  y_bot = {st.get('y_bot_mm',0):.1f} mm")
            lines.append(f"     Long-term  (n={cmp.get('long_term',{}).get('n','?')}):  "
                         f"I = {lt.get('I_comp_mm4',0):,.0f} mm⁴")

        lines.append(f"\n  8. SLS Stress Limits (Cl.604.3.1)")
        lines.append(f"     Concrete limit   : σc  ≤ 0.48 fck = {c.sigma_c_limit_MPa:.1f} MPa")
        lines.append(f"     Steel equiv. limit: fe  ≤ 0.90 fy  = {c.sigma_s_limit_MPa:.1f} MPa")
        lines.append(f"     Rebar limit      : σr  ≤ 0.80 fyk = {c.sigma_rebar_limit_MPa:.1f} MPa")
        # Actual stresses
        if not sls.get("skipped"):
            lines.append(f"     --- Actual stresses (M_sls = {sls.get('M_sls_kNm',0):.1f} kNm) ---")
            lines.append(f"     σc (concrete)  = {c.sigma_c_actual_MPa:.3f} MPa"
                         f"  {'OK' if c.sigma_c_actual_MPa <= c.sigma_c_limit_MPa else 'FAIL'}")
            lines.append(f"     fe (steel)     = {c.sigma_steel_equiv_MPa:.3f} MPa"
                         f"  {'OK' if c.sigma_steel_equiv_MPa <= c.sigma_s_limit_MPa else 'FAIL'}")
            lines.append(f"     σr (rebar)     = {c.sigma_rebar_actual_MPa:.3f} MPa"
                         f"  {'OK' if c.sigma_rebar_actual_MPa <= c.sigma_rebar_limit_MPa else 'FAIL'}")
            lines.append(f"     τ (web shear)  = {c.tau_web_actual_MPa:.3f} MPa")
        else:
            lines.append(f"     [Actual stresses not computed — supply M_sls_kNm to DemandEnvelope]")

        lines.append(f"\n  9. Deflection Limits (Cl.604.3.2)")
        lines.append(f"     Live + impact ≤ L/800 = {c.defl_limit_live_mm:.2f} mm")
        lines.append(f"     Total         ≤ L/600 = {c.defl_limit_total_mm:.2f} mm")

        lines.append(f"\n  10. Fatigue Assessment (Cl.605)")
        lines.append(f"     f_fd  = {c.f_fd_MPa:.3f} MPa  |  τ_fd = {c.tau_fd_MPa:.3f} MPa")

        lines.append(f"\n  11. Shear Stud Capacity (Cl.606.3.1)")
        lines.append(f"     Qu = {c.Qu_kN:.3f} kN / stud")
        if c.stud_spacing_mm > 0:
            lines.append(f"     Required ULS spacing = {c.stud_spacing_mm:.1f} mm")

        lines.append(f"\n  12. Shear Connector Spacing Limits (Cl.606.9)")
        if stud_lim:
            lines.append(f"     Max spacing = min(600, 3t_slab, 4h_stud) = {c.stud_spacing_max_mm:.0f} mm")
            lines.append(f"     Min spacing = {c.stud_spacing_min_mm:.0f} mm")

        lines.append(f"\n  13. Crack Control — Min Reinforcement (Cl.604.4)")
        if crack:
            lines.append(f"     As_min = {c.As_min_crack_mm2:.0f} mm²  |  "
                         f"As_provided = {c.As_provided_crack_mm2:.0f} mm²  |  "
                         f"{'OK' if c.As_provided_crack_mm2 >= c.As_min_crack_mm2 else 'INSUFFICIENT'}")

        return "\n".join(lines)

    def _build_dcr_table(self) -> str:
        checks = self.engine.checks
        if not checks:
            return "\n  No checks executed."

        lines = [self._section_title("DESIGN CHECK RESULTS (DCR = Demand / Capacity)")]
        hdr = f"  {'#':>3}  {'Check':<28} {'Demand':>10}  {'Capacity':>10}  {'DCR':>7}  {'Status':>6}"
        sep = "  " + "-" * (len(hdr) - 2)
        lines += [sep, hdr, sep]

        for c in checks:
            status_tag = {"PASS": " PASS ", "WARN": " WARN ", "FAIL": "*FAIL*", "INFO": " INFO "}.get(c.status, c.status)
            lines.append(
                f"  {c.check_id:>3}  {c.name:<28} "
                f"{c.demand:>10.2f}  {c.capacity:>10.2f}  {c.dcr:>7.3f}  {status_tag}"
            )
        lines.append(sep)
        return "\n".join(lines)

    def _build_bar_chart(self) -> str:
        checks = self.engine.checks
        if not checks:
            return ""
        lines = [self._section_title("DCR BAR CHART")]
        bw = self.BAR_WIDTH
        for c in checks:
            label = f"  {c.name:<22}"
            filled = int(min(c.dcr, 1.0) * bw)
            bar_char = "X" if c.status == "FAIL" else ("#" if c.status == "WARN" else "|")
            bar = bar_char * filled + "." * (bw - filled)
            lines.append(f"{label} [{bar}] {c.dcr:.3f}")
        return "\n".join(lines)

    def _build_verdict(self) -> str:
        eng = self.engine
        status = eng.overall_status()
        crit = eng.critical_check() if eng.checks else None

        lines = [self._section_title("OVERALL VERDICT"), ""]
        lines.append(f"  Status           : {status}")
        lines.append(f"  Checks Run       : {len(eng.checks)}")
        lines.append(f"  PASS / WARN / FAIL: {eng.n_pass()} / {eng.n_warn()} / {eng.n_fail()}")
        lines.append(f"  Maximum DCR      : {eng.max_dcr():.4f}")
        if crit:
            lines.append(f"  Critical Check   : {crit.name} ({crit.clause})")
        lines.append("")
        if status == "PASS":
            lines.append("  >>> ALL CHECKS SATISFIED - DESIGN IS ADEQUATE <<<")
        elif status == "WARN":
            lines.append("  >>> DESIGN WITHIN 10% OF LIMIT - REVIEW RECOMMENDED <<<")
        else:
            lines.append("  >>> DESIGN FAILS ONE OR MORE CHECKS - REVISION REQUIRED <<<")
        lines.append("")
        return "\n".join(lines)

    # Assemble the full formatted report string.
    def generate(self) -> str:
        return "\n".join([
            self._build_header(), self._build_config(), self._build_demands(),
            self._build_capacity_summary(), self._build_dcr_table(),
            self._build_bar_chart(), self._build_verdict(),
        ])


# ======================================================================
#  SECTION 6 -- MAIN PIPELINE
# ======================================================================


def _example_demands(config: BridgeConfig) -> DemandEnvelope:
    # Reference factored demands for the 33.5 m example bridge. Dead loads computed from material
    # unit weights (IRC 6:2017 Cl.203), partial factors from IRC 6:2017 Table B.2 (ULS basic),
    # impact factor from IRC 6:2017 Cl.208.3 (Class 70R). Deflection placeholders are illustrative
    # only — real runs should come from the grillage analyser via from_analysis_results().
    L_m = config.geometry.span

    # IRC 6:2017 Cl.203 — steel density = 7.8 t/m³ = 76.518 kN/m³.
    unit_wts = IRC6_2017.cl_203_dead_load()
    gamma_steel_kN_m3 = unit_wts["steel"] * 9.81                # 7.8 t/m³ → kN/m³
    gamma_concrete_kN_m3 = unit_wts["concrete_cement_reinforced"] * 9.81

    A_steel_m2 = config.section.A_steel * 1e-6
    w_self_weight = A_steel_m2 * gamma_steel_kN_m3
    w_wet_slab = gamma_concrete_kN_m3 * (config.slab.thickness / 1000.0) * config.geometry.beam_spacing
    # Illustrative SIDL (surfacing + railing share) — real bridges compute this from deck layout.
    w_sidl = (4.32 * config.geometry.beam_spacing + 1.5 + 4.0 / config.geometry.n_girders)
    w_dead_total = w_self_weight + w_wet_slab + w_sidl

    M_dead_kNm = w_dead_total * L_m ** 2 / 8.0
    V_dead_kN = w_dead_total * L_m / 2.0

    # IRC 6:2017 Table B.2 (ULS basic) — partial safety factors.
    gamma_dl = IRC6_2017.table_B2(load_type="dead_load", qualifier="adding", combination="basic")
    gamma_ll = IRC6_2017.table_B2(load_type="live_load", qualifier="leading", combination="basic")
    # IRC 6:2017 Cl.208.3 — impact factor for Class 70R(W) wheel loading.
    impact_fraction = IRC6_2017.cl_208_3_impact_factor(L_m)
    impact_multiplier = 1.0 + impact_fraction

    # Construction stage 1 — girder self-weight only (bare steel, no wet concrete yet).
    M_girder_sw_kNm = gamma_dl * w_self_weight * L_m ** 2 / 8.0

    # Construction stage 2 — steel self-weight + wet concrete only; no SIDL, no live load.
    w_construction = w_self_weight + w_wet_slab
    M_construction_kNm = gamma_dl * w_construction * L_m ** 2 / 8.0

    # Placeholder unfactored live-load responses (typical Class 70R on 33.5 m span).
    M_live_kNm, V_live_kN = 1800.0, 350.0

    Mu_kNm = gamma_dl * M_dead_kNm + gamma_ll * impact_multiplier * M_live_kNm
    Vu_kN = gamma_dl * V_dead_kN + gamma_ll * impact_multiplier * V_live_kN

    return DemandExtractor.from_manual(
        Mu_kNm=round(Mu_kNm, 2),
        Vu_kN=round(Vu_kN, 2),
        M_construction_kNm=round(M_construction_kNm, 2),
        M_girder_sw_kNm=round(M_girder_sw_kNm, 2),
        Nsc=config.fatigue.Nsc,
        combination=(
            f"ULS Basic: γDL={gamma_dl}·DL + γLL={gamma_ll}·IF={impact_multiplier:.3f}·LL"
        ),
        location="midspan (interior girder)",
        member="interior_longitudinal_beam",
    )

def _composite_stiffness_ratio(config: BridgeConfig) -> float:
    """
    Compute I_composite_transformed / I_bare_steel (short-term modular ratio basis).

    The grillage model uses bare-steel section properties for all load cases.
    Loads applied after composite action is established (SDL and live loads)
    should deflect on the stiffer composite section.  Dividing bare-steel-model
    deflections by this ratio gives the physically correct SLS deflection.

    Uses composite_section_properties() from initial_sizing so the formula lives
    in one place.  Returns a value ≥ 1.0; defaults to 1.0 (conservative) on error.
    """
    try:
        sec, mat, slab, geo = config.section, config.material, config.slab, config.geometry
        beff_mm = min(geo.span * 1000.0 / 4.0, geo.beam_spacing * 1000.0)
        mod = IRC22_2014.cl_604_3_modular_ratio(Ecm=mat.Ecm, Kc=0.5)
        props = composite_section_properties(
            beff_mm=beff_mm, ds_mm=slab.thickness, h_haunch_mm=slab.haunch_depth,
            A_steel_mm2=sec.A_steel, Iz_steel_mm4=sec.Iz_steel,
            y_cg_from_bot_mm=sec.y_cg_from_bot, D_steel_mm=sec.D,
            n=mod["m_short_term"],
        )
        return max(props["I_comp_mm4"] / sec.Iz_steel, 1.0)

    except Exception:
        return 1.0  # conservative fallback: no composite correction applied


def _extract_demands_from_analysis(
    analysis_results: PlateGirderAnalysisResults,
    config: BridgeConfig,
) -> DemandEnvelope:
    """
    Extract every demand quantity from a solved grillage analysis.
    Section properties (Ze_steel, Aw) come from the BridgeConfig so that
    fatigue stress ranges are driven by the same section the capacity
    calculator sees.
    """
    # Section properties needed for stress-range conversions (mm units)
    Ze_steel_mm3 = float(config.section.Ze_steel)
    Aw_mm2 = float(config.section.Aw)
    Nsc = int(config.fatigue.Nsc)

    # Composite-to-bare stiffness ratio for SLS deflection correction.
    ratio = _composite_stiffness_ratio(config)

    # Build girder topology and pick an interior girder
    girders, _ = analysis_results.build_girders(verbose=False)

    def _pick_girder_info(name):
        info = girders.get(name, {})
        return (
            list(info.get("elements", [])),
            list(info.get("path", [])),
            name,
        )

    interior_g_name = next(
        (g for g in girders if "interior" in g.lower()), None
    )

    if interior_g_name is None:
        # Try the analyser's model-side tag lookup as a second option
        try:
            mdl = analysis_results.bridge.model
            els = mdl.get_element(member="interior_main_beam", options="elements")
            nodes = mdl.get_element(member="interior_main_beam", options="nodes")
            if els:
                return DemandExtractor.from_analysis_results(
                    results=analysis_results,
                    element_ids=list(els),
                    node_ids=list(nodes) if nodes else [],
                    Ze_steel_mm3=Ze_steel_mm3,
                    Aw_mm2=Aw_mm2,
                    Nsc=Nsc,
                    member_name="interior_main_beam",
                    stiffness_ratio=ratio,
                )
        except Exception:
            pass

    if interior_g_name is not None:
        elements, nodes, name = _pick_girder_info(interior_g_name)
        if elements:
            return DemandExtractor.from_analysis_results(
                results=analysis_results,
                element_ids=elements,
                node_ids=nodes,
                Ze_steel_mm3=Ze_steel_mm3,
                Aw_mm2=Aw_mm2,
                Nsc=Nsc,
                member_name=name,
                stiffness_ratio=ratio,
            )

    # Last-resort: first available girder
    import warnings
    warnings.warn(
        "No interior girder identified — falling back to first available girder.",
        stacklevel=2,
    )
    first = next(iter(girders), None)
    if first is None:
        raise ValueError(
            "Demand extraction failed: grillage analysis produced no girders."
        )
    elements, nodes, name = _pick_girder_info(first)
    return DemandExtractor.from_analysis_results(
        results=analysis_results,
        element_ids=elements,
        node_ids=nodes,
        Ze_steel_mm3=Ze_steel_mm3,
        Aw_mm2=Aw_mm2,
        Nsc=Nsc,
        member_name=name,
        stiffness_ratio=ratio,
    )


def run_design_check(
    plate_girder_bridge: Any | None = None,
    analysis_results: PlateGirderAnalysisResults | None = None,
    config: BridgeConfig | None = None,
    demand: DemandEnvelope | None = None,
    print_report: bool = True,
) -> str:
    """
    Execute the complete IRC 22:2015 design-check pipeline.

    Pipeline
    --------
        Step 1 -> BridgeConfig         (configuration)
        Step 2 -> DemandExtractor       (analyser - demand extraction)
        Step 3 -> IRC22CapacityCalc     (IRC 22 - clause-by-clause capacity)
        Step 4 -> DCREngine             (demand / capacity ratios)
        Step 5 -> ReportGenerator       (formatted report)

    Parameters
    ----------
        plate_girder_bridge : Solved PlateGirderBridge instance overriding config
        analysis_results    : Solved PlateGirderAnalysisResults instance
        config       : BridgeConfig (default: 33.5 m example bridge)
        demand       : DemandEnvelope (default: example demands)
        print_report : print report to console
    """
    print("=" * 60)
    print("  IRC 22:2015 DESIGN CHECK PIPELINE")
    print("=" * 60)

    # -- Step 1: Configuration --
    print("\n[Step 1/5] Loading bridge configuration ...")
    if plate_girder_bridge is not None:
        config = BridgeConfig.from_plate_girder_bridge(plate_girder_bridge)
    elif config is None:
        config = BridgeConfig.example_33m_bridge()
    # Always run stiffener guidance even when no stiffener details are provided.
    if config.stiffener is None:
        config.stiffener = StiffenerConfig()
    print(f"  Config: {config.summary()}")

    # -- Step 2: Demand from Analyser --
    print("\n[Step 2/5] Extracting design demands (Analyser) ...")
    if demand is None and analysis_results is not None:
        demand = _extract_demands_from_analysis(analysis_results, config)
    elif demand is None:
        demand = _example_demands(config)
    print(f"  Mu              = {demand.Mu_kNm:.2f} kNm")
    print(f"  Vu              = {demand.Vu_kN:.2f} kN")
    print(f"  M_girder_sw     = {demand.M_girder_sw_kNm:.2f} kNm  (Stage 1: girder SW only)")
    print(f"  M_construction  = {demand.M_construction_kNm:.2f} kNm  (Stage 2: SW + wet concrete)")
    print(f"  delta_live      = {demand.delta_live_mm:.3f} mm")
    print(f"  delta_total     = {demand.delta_total_mm:.3f} mm")
    print(f"  stress_range    = {demand.stress_range_MPa:.3f} MPa")
    print(f"  shear_range     = {demand.shear_range_MPa:.3f} MPa")
    print(f"  Source: {demand.source}")

    # For a simply-supported beam, max shear = end reaction → use as bearing stiffener load.
    # Only set when the caller hasn't already supplied a reaction.
    if config.stiffener.bs_R_kN <= 0.0 and demand.Vu_kN > 0.0:
        config.stiffener.bs_R_kN = demand.Vu_kN

    # -- Step 3: IRC 22 Capacity --
    print("\n[Step 3/5] Computing IRC 22:2015 capacities ...")
    calculator = IRC22CapacityCalculator(config)
    capacity = calculator.compute_all(                                   # ←── CHANGED
        Vu_kN=demand.Vu_kN,
        stress_range_MPa=demand.stress_range_MPa,
        M_sls_kNm=demand.M_sls_kNm,        
        V_sls_kN=demand.V_sls_kN,           
    )
    print(f"  beff  = {capacity.beff_mm:.1f} mm    (Cl.603.2.1)")
    print(f"  Md    = {capacity.Md_kNm:,.2f} kNm  (Cl.603.3.1)")
    print(f"  Vd    = {capacity.Vd_kN:,.2f} kN   (Cl.603.3.3.2)")
    print(f"  Mb    = {capacity.Mb_kNm:,.2f} kNm  (Cl.603.3.3.1)")
    print(f"  Qu    = {capacity.Qu_kN:.3f} kN/stud (Cl.606.3.1)")

    # -- Stiffener detail printout --
    is_det = capacity.details.get("intermediate_stiffener", {})
    if is_det and not is_det.get("skipped"):
        print("\n  [Stiffener] Intermediate transverse (Cl.509.7.2 / IS 800 Cl.8.7.2)")
        print(f"    H_max (physical fit)   = {is_det['H_max_mm']:.1f} mm")
        print(f"    tq_req (1-sided)       >= {is_det['tq_req_1sided_mm']:.2f} mm")
        print(f"    tq_req (2-sided)       >= {is_det['tq_req_2sided_mm']:.2f} mm")
        if is_det.get("design_guidance"):
            c_req = is_det.get("c_req_min_mm", 0.0)
            if c_req > 0:
                print(f"    c_req (min spacing)    >= {c_req:.0f} mm  (from Iys check)")
            else:
                print(f"    c_req: simple formula (0.75·d·tw³) governs — any spacing OK")
            print(f"    --> No dimensions provided; use above as sizing guide.")
        else:
            _pass = lambda d, c: "PASS" if c >= d else "FAIL"
            print(f"    H provided             = {is_det['H_mm']:.1f} mm  "
                  f"[limit {is_det['H_limit_mm']:.2f} mm = {is_det['H_limit_type']}]  "
                  f"{_pass(is_det['H_mm'], is_det['H_limit_mm'])}")
            print(f"    tq_req for H provided  >= {is_det['tq_req_provided_mm']:.2f} mm")
            print(f"    Iys_prov               = {is_det['Iys_prov_mm4']:.0f} mm⁴  "
                  f"[min {is_det['Iys_min_mm4']:.0f} mm⁴ = {is_det['iys_formula']}]  "
                  f"{_pass(is_det['Iys_min_mm4'], is_det['Iys_prov_mm4'])}")
            print(f"    Aeff = {is_det['Aeff_mm2']:.0f} mm²  "
                  f"(Astiff={is_det['Astiff_mm2']:.0f} mm²  "
                  f"rys={is_det['rys_mm']:.2f} mm  KL/r={is_det['KL_r']:.2f})")
            print(f"    fcd = {is_det['fcd_MPa']:.2f} MPa  (α=0.49)  "
                  f"Fqd={is_det['Fqd_kN']:.2f} kN  Fq={is_det['Fq_kN']:.2f} kN  "
                  f"{_pass(is_det['Fq_kN'], is_det['Fqd_kN'])}")

    bs_det = capacity.details.get("bearing_stiffener", {})
    if bs_det and not bs_det.get("skipped"):
        print("\n  [Stiffener] Bearing stiffener (Cl.509.7.3 / IS 800 Cl.8.7.3)")
        print(f"    Reaction R             = {bs_det['R_kN']:.2f} kN")
        print(f"    H_max (physical fit)   = {bs_det['H_max_mm']:.1f} mm")
        print(f"    n_plates               = {bs_det['n_plates']}")
        if bs_det.get("design_guidance"):
            print(f"    tq_req (bearing)       >= {bs_det['tq_req_bearing_mm']:.2f} mm")
            print(f"    tq_req (leg limit)     >= {bs_det['tq_req_leg_mm']:.2f} mm")
            print(f"    tq_req (governing)     >= {bs_det['tq_req_mm']:.2f} mm")
            print(f"    --> No plate dimensions provided; use above as sizing guide.")
        else:
            _pass = lambda d, c: "PASS" if c >= d else "FAIL"
            print(f"    b1 (stiff bearing len) = {bs_det['b1_mm']:.1f} mm")
            print(f"    Cl.509.7.3.1 Web Buckling:  "
                  f"Fcdw_wb={bs_det['Fcdw_wb_kN']:.2f} kN  "
                  f"(fcc={bs_det['fcc_wb_MPa']:.2f} MPa  A_wb={bs_det['A_wb_mm2']:.0f} mm²)  "
                  f"{_pass(bs_det['R_kN'], bs_det['Fcdw_wb_kN'])}")
            print(f"    Cl.509.7.3.2 Local Crushing: "
                  f"Fcdw_lc={bs_det['Fcdw_lc_kN']:.2f} kN  "
                  f"(fcd_y={bs_det['fcd_y_MPa']:.2f} MPa  A_lc={bs_det['A_lc_mm2']:.0f} mm²)  "
                  f"{_pass(bs_det['R_kN'], bs_det['Fcdw_lc_kN'])}")
            print(f"    Cl.509.7.3.3 Bearing Contact: "
                  f"Fpsd={bs_det['Fpsd_kN']:.2f} kN  "
                  f"(Aq={bs_det['Aq_mm2']:.0f} mm²  tq_req>={bs_det['tq_req_bearing_mm']:.2f} mm)  "
                  f"{_pass(bs_det['R_kN'], bs_det['Fpsd_kN'])}")
            print(f"    Cl.509.7.2.5 Column Buckling: "
                  f"Fcd={bs_det['Fcd_kN']:.2f} kN  "
                  f"(fcd={bs_det['fcd_bs_MPa']:.2f} MPa  KL/r={bs_det['KL_r_bs']:.2f}  "
                  f"Aeff={bs_det['Aeff_bs_mm2']:.0f} mm²)  "
                  f"{_pass(bs_det['R_kN'], bs_det['Fcd_kN'])}")
            print(f"    H_limit (leg)          = {bs_det['H_limit_bs_mm']:.2f} mm  "
                  f"tq_req (leg)>={bs_det['tq_req_leg_mm']:.2f} mm")

    # -- Step 4: DCR Engine --
    print("\n[Step 4/5] Running DCR checks ...")
    engine = DCREngine(demand, capacity)
    checks = engine.run_all_checks()
    for chk in checks:
        icon = {"PASS": "+", "WARN": "~", "FAIL": "X"}.get(chk.status, "?")
        print(f"  [{icon}] {chk.name:<28} DCR = {chk.dcr:.3f}  {chk.status}")

    # -- Step 5: Report --
    print("\n[Step 5/5] Generating report ...")
    reporter = ReportGenerator(config, demand, capacity, engine)
    report_text = reporter.generate()

    if print_report:
        print("\n" + report_text)

    print("\n" + "=" * 60)
    print(f"  PIPELINE COMPLETE - Overall: {engine.overall_status()}")
    print("=" * 60)

    # -- Build structured results dict for output dock and report ──────────
    _sec = config.section
    _mat = config.material
    _geo = config.geometry
    design_results = {
        # ── bridge configuration ────────────────────────────────────────────
        "span_m"                    : _geo.span,
        "support_type"              : _geo.support_type,
        "n_girders"                 : _geo.n_girders,
        "beam_spacing_m"            : _geo.beam_spacing,
        "carriageway_width_m"       : _geo.carriageway_width,
        "beam_type"                 : _geo.beam_type,
        "cross_bracing_spacing_m"   : _geo.cross_bracing_spacing_m,
        # ── material properties ─────────────────────────────────────────────
        "steel_grade"               : _mat.steel_grade,
        "fy_MPa"                    : _mat.fy,
        "fu_MPa"                    : _mat.fu,
        "concrete_grade"            : _mat.concrete_grade,
        "fck_MPa"                   : _mat.fck,
        "fctm_MPa"                  : _mat.fctm,
        "Ecm_MPa"                   : _mat.Ecm,
        "rebar_grade"               : _mat.rebar_grade,
        "fy_rebar_MPa"              : _mat.fy_rebar,
        "gamma_m0"                  : _mat.gamma_m0,
        "gamma_m1"                  : _mat.gamma_m1,
        "gamma_v"                   : _mat.gamma_v,
        # ── steel section ───────────────────────────────────────────────────
        "D_mm"                      : _sec.D,
        "bf_top_mm"                 : _sec.bf_top,
        "tf_top_mm"                 : _sec.tf_top,
        "bf_bot_mm"                 : _sec.bf_bot,
        "tf_bot_mm"                 : _sec.tf_bot,
        "tw_mm"                     : _sec.tw,
        "dw_mm"                     : round(_sec.dw, 1),
        "A_steel_mm2"               : round(_sec.A_steel, 1),
        "Iz_steel_mm4"              : round(_sec.Iz_steel, 0),
        "Ze_steel_mm3"              : round(_sec.Ze_steel, 0),
        "Zp_steel_mm3"              : round(_sec.Zp_steel, 0),
        "y_cg_from_bot_mm"          : round(_sec.y_cg_from_bot, 2),
        "fabrication"               : _sec.fabrication,
        # ── slab ────────────────────────────────────────────────────────────
        "slab_thickness_mm"         : config.slab.thickness,
        "haunch_depth_mm"           : config.slab.haunch_depth,
        # ── shear studs ─────────────────────────────────────────────────────
        "stud_dia_mm"               : config.studs.diameter,
        "stud_height_mm"            : config.studs.height,
        "stud_fu_MPa"               : config.studs.fu,
        "studs_per_section"         : config.studs.n_per_section,
        # ── demands ─────────────────────────────────────────────────────────
        "Mu_kNm"                    : demand.Mu_kNm,
        "Vu_kN"                     : demand.Vu_kN,
        "Nu_kN"                     : demand.Nu_kN,
        "M_construction_kNm"        : demand.M_construction_kNm,
        "delta_live_mm"             : demand.delta_live_mm,
        "delta_total_mm"            : demand.delta_total_mm,
        "stress_range_MPa"          : demand.stress_range_MPa,
        "shear_range_MPa"           : demand.shear_range_MPa,
        "Nsc"                       : demand.Nsc,
        "M_sls_kNm"                 : demand.M_sls_kNm,
        "V_sls_kN"                  : demand.V_sls_kN,
        "Vr_kN"                     : demand.Vr_kN,
        "governing_combination"     : demand.governing_combination,
        "demand_location"           : demand.location,
        "demand_member"             : demand.member,
        "demand_source"             : demand.source,
        # ── capacities — ULS flexure ────────────────────────────────────────
        "beff_mm"                   : capacity.beff_mm,
        "xu_mm"                     : capacity.xu_mm,
        "pna_location"              : capacity.pna_location,
        "Mp_kNm"                    : capacity.Mp_kNm,
        "Md_kNm"                    : capacity.Md_kNm,
        # ── capacities — LTB ────────────────────────────────────────────────
        "Mcr_kNm"                   : capacity.Mcr_kNm,
        "lambda_LT"                 : capacity.lambda_LT,
        "chi_LT"                    : capacity.chi_LT,
        "Mb_kNm"                    : capacity.Mb_kNm,
        # ── capacities — shear ──────────────────────────────────────────────
        "Av_mm2"                    : capacity.Av_mm2,
        "Vn_kN"                     : capacity.Vn_kN,
        "Vd_kN"                     : capacity.Vd_kN,
        # ── capacities — M-V interaction ────────────────────────────────────
        "Mdv_kNm"                   : capacity.Mdv_kNm,
        "beta_interaction"          : capacity.beta_interaction,
        # ── SLS limits ──────────────────────────────────────────────────────
        "defl_limit_live_mm"        : capacity.defl_limit_live_mm,
        "defl_limit_total_mm"       : capacity.defl_limit_total_mm,
        "sigma_c_limit_MPa"         : capacity.sigma_c_limit_MPa,
        "sigma_s_limit_MPa"         : capacity.sigma_s_limit_MPa,
        "sigma_rebar_limit_MPa"     : capacity.sigma_rebar_limit_MPa,
        # ── SLS actual stresses ──────────────────────────────────────────────
        "sigma_c_actual_MPa"        : capacity.sigma_c_actual_MPa,
        "sigma_rebar_actual_MPa"    : capacity.sigma_rebar_actual_MPa,
        "sigma_steel_equiv_MPa"     : capacity.sigma_steel_equiv_MPa,
        "tau_web_actual_MPa"        : capacity.tau_web_actual_MPa,
        # ── composite section ───────────────────────────────────────────────
        "I_comp_short_mm4"          : capacity.I_comp_short_mm4,
        "y_top_comp_mm"             : capacity.y_top_comp_mm,
        "y_bot_comp_mm"             : capacity.y_bot_comp_mm,
        # ── fatigue ─────────────────────────────────────────────────────────
        "f_fd_MPa"                  : capacity.f_fd_MPa,
        "tau_fd_MPa"                : capacity.tau_fd_MPa,
        "f_fd_eff_MPa"              : capacity.f_fd_eff_MPa,
        "tau_fd_eff_MPa"            : capacity.tau_fd_eff_MPa,
        # ── shear studs ─────────────────────────────────────────────────────
        "Qu_kN"                     : capacity.Qu_kN,
        "Qr_kN"                     : capacity.Qr_kN,
        "VL_N_per_mm"               : capacity.VL_N_per_mm,
        "stud_spacing_uls_mm"       : capacity.stud_spacing_mm,
        "stud_spacing_full_shear_mm": capacity.stud_spacing_full_shear_mm,
        "stud_spacing_fatigue_mm"   : capacity.stud_spacing_fatigue_mm,
        "stud_spacing_governing_mm" : capacity.stud_spacing_governing_mm,
        "stud_spacing_provided_mm"  : capacity.stud_spacing_provided_mm,
        "stud_spacing_max_mm"       : capacity.stud_spacing_max_mm,
        "stud_spacing_min_mm"       : capacity.stud_spacing_min_mm,
        "stud_detailing_ok"         : capacity.stud_detailing_ok,
        # ── transverse shear ────────────────────────────────────────────────
        "transverse_shear_ok"       : capacity.transverse_shear_ok,
        "Ast_required_cm2_per_m"    : capacity.Ast_required_cm2_per_m,
        "Ast_provided_cm2_per_m"    : capacity.Ast_provided_cm2_per_m,
        # ── crack control ───────────────────────────────────────────────────
        "As_min_crack_mm2"          : capacity.As_min_crack_mm2,
        "As_provided_crack_mm2"     : capacity.As_provided_crack_mm2,
        # ── stiffener ───────────────────────────────────────────────────────
        "is_H_limit_mm"             : capacity.is_H_limit_mm,
        "is_Iys_min_mm4"            : capacity.is_Iys_min_mm4,
        "is_Iys_prov_mm4"           : capacity.is_Iys_prov_mm4,
        "is_Fqd_kN"                 : capacity.is_Fqd_kN,
        "is_Fq_kN"                  : capacity.is_Fq_kN,
        "bs_Fcdw_wb_kN"             : capacity.bs_Fcdw_wb_kN,
        "bs_Fcdw_lc_kN"             : capacity.bs_Fcdw_lc_kN,
        "bs_Fpsd_kN"                : capacity.bs_Fpsd_kN,
        "bs_Fcd_kN"                 : capacity.bs_Fcd_kN,
        "bs_R_kN"                   : capacity.bs_R_kN,
        # ── DCR summary ─────────────────────────────────────────────────────
        "overall_status"            : engine.overall_status(),
        "max_dcr"                   : engine.max_dcr(),
        "n_pass"                    : engine.n_pass(),
        "n_warn"                    : engine.n_warn(),
        "n_fail"                    : engine.n_fail(),
        # ── DCR check rows (for output dock table) ──────────────────────────
        "checks": [
            {
                "check_id"     : chk.check_id,
                "name"         : chk.name,
                "clause"       : chk.clause,
                "demand"       : chk.demand,
                "demand_unit"  : chk.demand_unit,
                "capacity"     : chk.capacity,
                "capacity_unit": chk.capacity_unit,
                "dcr"          : chk.dcr,
                "status"       : chk.status,
                "note"         : chk.note,
            }
            for chk in engine.checks
        ],
        # ── clause-level detail dicts (for report / deep inspection) ────────
        "capacity_details"          : capacity.details,
        # ── formatted report text ────────────────────────────────────────────
        "report_text"               : report_text,
    }

    return report_text, engine, design_results


# ======================================================================
#  ENTRY POINT
# ======================================================================

if __name__ == "__main__":
    run_design_check()
