# IRC 22:2015 composite plate-girder design pipeline: Config -> Demand -> Capacity -> DCR -> Report.

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

from osdagbridge.core.bridge_types.plate_girder.analysis_results import PlateGirderAnalysisResults
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
)


# IRC 22:2015 Cl.601.4 Table 1 — partial safety factors (pulled once at import).
_GAMMA_M = IRC22_2014.cl_601_4_material_safety_factors()
GAMMA_M0 = _GAMMA_M["structural_steel_yield"]["ULS"]              # yielding / instability
GAMMA_M1 = _GAMMA_M["structural_steel_ultimate"]["ULS"]           # ultimate stress
GAMMA_V = _GAMMA_M["bolts_rivets_shear_tension"]["ULS"]           # shear connectors
GAMMA_MFT_FATIGUE = 1.35                                          # IRC 22:2015 Cl.605 Table 3

# IRC 22:2015 Cl.605.3 — fatigue strength at 5×10^6 cycles (rolled vs welded).
FATIGUE_STRENGTH_ROLLED_MPA = 118.0
FATIGUE_STRENGTH_WELDED_MPA = 92.0
FATIGUE_SHEAR_STRENGTH_MPA = 59.0


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
class BridgeConfig:
    # Single aggregate input consumed by DemandExtractor / IRC22CapacityCalculator / DCREngine / Report.
    material: SteelProperties
    section: SteelSection
    slab: SlabProperties
    geometry: GeometryConfig
    studs: ShearStudConfig = field(default_factory=ShearStudConfig)
    fatigue: FatigueConfig = field(default_factory=FatigueConfig)

    @classmethod
    def from_plate_girder_bridge(cls, bridge: Any) -> "BridgeConfig":
        # Build a BridgeConfig from a solved PlateGirderBridge: materials from the project DB
        # (which mirrors IS 2062 / IRC 22 Annex III), concrete/rebar resolved via IRC 22 Annex III.
        from osdagbridge.core.utils.common import (
            KEY_GIRDER, KEY_DECK_CONCRETE_GRADE_BASIC, KEY_DECK_THICKNESS,
            KEY_SPAN, KEY_CARRIAGEWAY_WIDTH,
        )

        if not getattr(bridge, "material_props", None):
            bridge.material_props = bridge._build_material_props()
        if not getattr(bridge, "section_props", None):
            bridge.section_props = bridge._girder_section()

        steel_prop = bridge.material_props.steel_prop
        fy_struct = steel_prop.Fy / 1_000_000.0
        fu_struct = (steel_prop.Fu / 1_000_000.0) if steel_prop.Fu else fy_struct * 1.5

        material = SteelProperties.from_grades(
            steel_grade=str(bridge.basic_inputs.get(KEY_GIRDER, "")),
            fy_struct_MPa=fy_struct,
            fu_struct_MPa=fu_struct,
            concrete_grade=str(bridge.basic_inputs.get(KEY_DECK_CONCRETE_GRADE_BASIC, "")),
        )

        props = bridge.section_props
        section = SteelSection(
            D=props["D"] * 1000,
            bf_top=props["B_top"] * 1000,
            tf_top=props["t_f_top"] * 1000,
            bf_bot=props["B_bot"] * 1000,
            tf_bot=props["t_f_bot"] * 1000,
            tw=props["t_w"] * 1000,
        )

        geom = getattr(bridge, "grillage_geometry", None)
        deck = getattr(bridge, "deck_layout", None)
        sizing = getattr(bridge, "sizing_result", None)

        geometry = GeometryConfig(
            span=geom.L if geom else float(bridge.basic_inputs[KEY_SPAN]),
            beam_spacing=geom.ext_to_int_dist if geom else sizing.girder_spacing,
            carriageway_width=deck.carriageway_width if deck else float(bridge.basic_inputs[KEY_CARRIAGEWAY_WIDTH]),
            n_girders=geom.n_l if geom else sizing.no_of_girders,
            edge_distance=geom.edge_dist if geom else sizing.deck_overhang,
        )

        slab = SlabProperties(thickness=float(bridge.basic_inputs[KEY_DECK_THICKNESS]))
        return cls(material=material, section=section, geometry=geometry, slab=slab)

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
    ) -> DemandEnvelope:
        # Build a DemandEnvelope from directly supplied factored quantities.
        return DemandEnvelope(
            Mu_kNm=Mu_kNm, Vu_kN=Vu_kN, Nu_kN=Nu_kN, M_construction_kNm=M_construction_kNm,
            delta_live_mm=delta_live_mm, delta_total_mm=delta_total_mm,
            stress_range_MPa=stress_range_MPa, shear_range_MPa=shear_range_MPa,
            Nsc=Nsc, governing_combination=combination,
            location=location, member=member, source="manual",
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
    ) -> DemandEnvelope:
        # Extract ULS Mu/Vu envelopes, construction moment, deflections, and fatigue ranges
        # directly from the grillage xarray dataset. forces→N/Nm, displacements→m.
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
            gamma_dl = IRC6_2017.table_B2(load_type="dead_load", effect="adding", combination="basic")
            M_const_kNm = (construction_mz * gamma_dl) / 1000.0

        # ------------------------------------------------------------------
        # (3) Deflections from `displacements.Component="y"`
        #     live  : max |y-disp| over live LCs × girder nodes
        #     total : max |Σ dead-LC y-disp  +  live-LC y-disp| per node
        # ------------------------------------------------------------------
        delta_live_m = 0.0
        delta_dead_m = 0.0
        try:
            disp_y = ds.displacements.sel(Component="y", Node=node_ids)

            if all_live_lcs:
                live_vals = _as_float(disp_y.sel(Loadcase=all_live_lcs).values)
                live_finite = live_vals[~np.isnan(live_vals)]
                if live_finite.size:
                    delta_live_m = float(np.abs(live_finite).max())

            if dead_lcs:
                dead_vals = _as_float(disp_y.sel(Loadcase=dead_lcs).values)
                dead_vals = np.nan_to_num(dead_vals, nan=0.0)
                # sum across LCs for each node, then take |·|max
                if dead_vals.ndim > 1:
                    per_node = dead_vals.sum(axis=0)
                else:
                    per_node = dead_vals
                if per_node.size:
                    delta_dead_m = float(np.abs(per_node).max())
        except (KeyError, ValueError) as e:
            warnings.warn(
                f"Could not extract vertical deflections from dataset: {e}. "
                "delta_live / delta_total set to 0.",
                stacklevel=2,
            )

        delta_live_mm = delta_live_m * 1000.0
        delta_total_mm = (delta_dead_m + delta_live_m) * 1000.0

        # ------------------------------------------------------------------
        # (4) Fatigue ranges from moving-load envelope
        #     stress_range = (Mz_max - Mz_min) / Ze_steel    [MPa]
        #     shear_range  = (Vy_max - Vy_min) / Aw           [MPa]
        # ------------------------------------------------------------------
        stress_range_MPa = 0.0
        shear_range_MPa = 0.0

        if live_moving and Ze_steel_mm3 > 0:
            try:
                mz_i = _as_float(
                    ds.forces.sel(Loadcase=live_moving, Element=element_ids,
                                  Component="Mz_i").values
                ).flatten()
                mz_j = _as_float(
                    ds.forces.sel(Loadcase=live_moving, Element=element_ids,
                                  Component="Mz_j").values
                ).flatten()
                mz_all = np.concatenate([mz_i, mz_j])
                mz_all = mz_all[~np.isnan(mz_all)]
                if mz_all.size:
                    # Nm → Nmm : ×1000   ;   σ = M/Ze
                    mz_range_Nmm = (mz_all.max() - mz_all.min()) * 1000.0
                    stress_range_MPa = float(mz_range_Nmm / Ze_steel_mm3)
            except (KeyError, ValueError):
                pass

        if live_moving and Aw_mm2 > 0:
            try:
                vy_i = _as_float(
                    ds.forces.sel(Loadcase=live_moving, Element=element_ids,
                                  Component="Vy_i").values
                ).flatten()
                vy_j = _as_float(
                    ds.forces.sel(Loadcase=live_moving, Element=element_ids,
                                  Component="Vy_j").values
                ).flatten()
                vy_all = np.concatenate([vy_i, vy_j])
                vy_all = vy_all[~np.isnan(vy_all)]
                if vy_all.size:
                    vy_range_N = vy_all.max() - vy_all.min()
                    shear_range_MPa = float(vy_range_N / Aw_mm2)
            except (KeyError, ValueError):
                pass

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
        gamma_dl = IRC6_2017.table_B2(load_type="dead_load", effect="adding", combination="basic")
        gamma_ll = IRC6_2017.table_B2(load_type="live_load", load_category="leading", combination="basic")
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
    Av_mm2: float = 0.0                                 # Cl.603.3.3.2
    Vn_kN: float = 0.0
    Vd_kN: float = 0.0
    Mdv_kNm: float = 0.0                                # Cl.603.3.3.3
    beta_interaction: float = 0.0
    defl_limit_live_mm: float = 0.0                     # Cl.604.3.2
    defl_limit_total_mm: float = 0.0
    sigma_c_limit_MPa: float = 0.0                      # Cl.604.3.1
    sigma_s_limit_MPa: float = 0.0
    f_fd_MPa: float = 0.0                               # Cl.605
    tau_fd_MPa: float = 0.0
    Qu_kN: float = 0.0                                  # Cl.606
    stud_spacing_mm: float = 0.0
    source: str = "built-in"
    details: Dict[str, dict] = field(default_factory=dict)


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
        Lo_mm = self.geo.span * 1000.0
        B_mm = self.geo.beam_spacing * 1000.0

        if self.geo.beam_type == "inner":
            beff = min(Lo_mm / 4.0, B_mm)
            method = f"inner beam: min(Lo/4={Lo_mm/4:.1f}, B={B_mm:.1f})"
        else:
            B1 = B_mm / 2.0
            B0 = self.geo.edge_distance * 1000.0
            beff = min(Lo_mm / 8.0, B1 / 2.0) + min(B0, Lo_mm / 8.0)
            method = "outer beam: min(Lo/8, B1/2) + min(B0, Lo/8)"

        return {
            "beff_mm": round(beff, 1), "Lo_mm": Lo_mm, "B_mm": B_mm,
            "beam_type": self.geo.beam_type, "method": method,
            "clause": "IRC 22:2015 - Cl.603.2.1", "source": "built-in",
        }

    # IRC 22:2015 Cl.603 — section classification (web + flange governed by d/tw and b/tf ratios).
    def classify_section(self) -> dict:
        fy = self.mat.fy
        epsilon = math.sqrt(250.0 / fy)
        sec = self.sec
        d_tw = sec.dw / sec.tw
        b_tf = (sec.bf_bot / 2.0 - sec.tw / 2.0) / sec.tf_bot

        web_class = self._classify_web(d_tw, epsilon)
        flange_class = self._classify_flange(b_tf, epsilon, sec.fabrication)
        class_order = {"Plastic": 1, "Compact": 2, "Semi-Compact": 3, "Slender": 4}
        governing = max(web_class, flange_class, key=lambda c: class_order.get(c, 4))

        return {
            "epsilon": round(epsilon, 4),
            "d_tw_ratio": round(d_tw, 2), "b_tf_ratio": round(b_tf, 2),
            "web_class": web_class, "flange_class": flange_class,
            "governing_class": governing,
            "clause": "IRC 22:2015 - Cl.603", "source": "built-in",
        }

    @staticmethod
    def _classify_web(d_tw: float, epsilon: float) -> str:
        if d_tw <= 84.0 * epsilon:
            return "Plastic"
        elif d_tw <= 105.0 * epsilon:
            return "Compact"
        elif d_tw <= 126.0 * epsilon:
            return "Semi-Compact"
        return "Slender"

    @staticmethod
    def _classify_flange(b_tf: float, epsilon: float, fab: str) -> str:
        limits = [9.4, 13.6] if fab == "welded" else [10.5, 15.7]
        if b_tf <= 8.4 * epsilon:
            return "Plastic"
        elif b_tf <= limits[0] * epsilon:
            return "Compact"
        elif b_tf <= limits[1] * epsilon:
            return "Semi-Compact"
        return "Slender"

    # IRC 22:2015 Cl.603.3.1 — plastic positive moment capacity (sagging, full shear interaction).
    def compute_moment_capacity(self, beff_mm: float) -> dict:
        sec = self.sec
        mat = self.mat
        slab = self.slab
        fy, fck, gm0 = mat.fy, mat.fck, mat.gamma_m0
        ds, h_haunch = slab.thickness, slab.haunch_depth

        T_all = sec.A_steel * fy
        C_max = 0.36 * fck * beff_mm * ds

        if T_all <= C_max:
            xu = T_all / (0.36 * fck * beff_mm)
            pna_location = "slab"
            y_steel_cg = ds + h_haunch + sec.D - sec.y_cg_from_bot
            Mp_Nmm = T_all * (y_steel_cg - xu / 2.0)
        else:
            C_conc = C_max
            F_excess = T_all - C_conc
            pna_location, y_pna, Mp_Nmm = self._pna_in_steel(
                C_conc, F_excess, beff_mm, ds, h_haunch
            )
            xu = ds

        Mp_kNm = Mp_Nmm / 1e6
        Md_kNm = Mp_kNm / gm0

        return {
            "xu_mm": round(xu, 2), "pna_location": pna_location,
            "T_steel_kN": round(T_all / 1e3, 2),
            "C_conc_max_kN": round(C_max / 1e3, 2),
            "Mp_kNm": round(Mp_kNm, 2), "Md_kNm": round(Md_kNm, 2),
            "gamma_m0": gm0,
            "clause": "IRC 22:2015 - Cl.603.3.1", "source": "built-in",
        }

    def _pna_in_steel(self, C_conc, F_excess, beff_mm, ds, h_haunch):
        sec = self.sec
        fy = self.mat.fy
        A_switch = F_excess / (2.0 * fy)

        if A_switch <= sec.Af_top:
            pna_location = "top_flange"
        elif A_switch <= sec.Af_top + sec.Aw:
            pna_location = "web"
        else:
            pna_location = "bottom_flange"

        if pna_location == "top_flange":
            y_pna = ds + h_haunch + A_switch / sec.bf_top
        elif pna_location == "web":
            y_pna = ds + h_haunch + sec.tf_top + (A_switch - sec.Af_top) / sec.tw
        else:
            y_pna = ds + h_haunch + sec.tf_top + sec.dw

        steel_elements = self._steel_elements(ds, h_haunch)
        Mp_Nmm = C_conc * (y_pna - ds / 2.0)

        for (y_bot, height, width) in steel_elements:
            y_top_elem = y_bot + height
            if y_top_elem <= y_pna:
                Mp_Nmm += fy * width * height * (y_pna - (y_bot + height / 2.0))
            elif y_bot >= y_pna:
                Mp_Nmm += fy * width * height * ((y_bot + height / 2.0) - y_pna)
            else:
                h_comp = y_pna - y_bot
                h_tens = y_top_elem - y_pna
                Mp_Nmm += fy * width * h_comp * h_comp / 2.0
                Mp_Nmm += fy * width * h_tens * h_tens / 2.0

        return pna_location, y_pna, Mp_Nmm

    def _steel_elements(self, ds, h_haunch):
        sec = self.sec
        base = ds + h_haunch
        return [
            (base, sec.tf_top, sec.bf_top),
            (base + sec.tf_top, sec.dw, sec.tw),
            (base + sec.tf_top + sec.dw, sec.tf_bot, sec.bf_bot),
        ]

    # IRC 22:2015 Cl.603.3.3.2 — plastic shear resistance of the web (Vd = Av·fy / (√3·γm0)).
    def compute_shear_capacity(self) -> dict:
        sec = self.sec
        fyw, gm0 = self.mat.fy, self.mat.gamma_m0
        Av = sec.dw * sec.tw
        Vn = Av * fyw / math.sqrt(3.0)
        Vd = Vn / gm0

        return {
            "Av_mm2": round(Av, 1), "fyw_MPa": fyw,
            "Vn_kN": round(Vn / 1e3, 2), "Vd_kN": round(Vd / 1e3, 2),
            "gamma_m0": gm0,
            "clause": "IRC 22:2015 - Cl.603.3.3.2", "source": "built-in",
        }

    # IRC 22:2015 Cl.603.3.3.1 — lateral-torsional buckling resistance at construction stage.
    def compute_buckling_resistance(self, beff_mm: float) -> dict:
        sec = self.sec
        mat = self.mat
        fy, Es = mat.fy, mat.Es
        G = mat.Gs                                      # IRC 22 Annex III — shear modulus.
        # Cross-bracing at 4–6 m intervals in practice — clamp LLT to 6000 mm for the construction stage.
        LLT_mm = min(self.geo.span * 1000.0, 6000.0)

        It = (sec.bf_top * sec.tf_top ** 3
              + sec.dw * sec.tw ** 3
              + sec.bf_bot * sec.tf_bot ** 3) / 3.0

        Iy = (sec.tf_top * sec.bf_top ** 3 / 12.0
              + sec.dw * sec.tw ** 3 / 12.0
              + sec.tf_bot * sec.bf_bot ** 3 / 12.0)

        hw = sec.dw + sec.tf_top / 2.0 + sec.tf_bot / 2.0
        Iw = sec.Af_bot * (hw ** 2) / 4.0 * (sec.bf_bot ** 2 / 12.0)

        Zp = sec.Zp_steel

        pi2_EIy = math.pi ** 2 * Es * Iy / (LLT_mm ** 2)
        Mcr_Nmm = math.sqrt(
            pi2_EIy * (G * It + math.pi ** 2 * Es * Iw / LLT_mm ** 2)
        )
        Mcr_kNm = Mcr_Nmm / 1e6

        lambda_LT = math.sqrt(Zp * fy / Mcr_Nmm) if Mcr_Nmm > 0 else 999.0
        alpha_LT = 0.49 if sec.fabrication == "welded" else 0.21
        phi_LT = 0.5 * (1.0 + alpha_LT * (lambda_LT - 0.2) + lambda_LT ** 2)

        discriminant = phi_LT ** 2 - lambda_LT ** 2
        chi_LT = min(1.0 / (phi_LT + math.sqrt(discriminant)), 1.0) if discriminant > 0 else 1.0
        chi_LT = max(chi_LT, 0.0)

        Mb_kNm = chi_LT * Zp * fy / mat.gamma_m0 / 1e6

        return {
            "It_mm4": round(It, 1), "Iy_mm4": round(Iy, 1),
            "LLT_mm": LLT_mm, "Mcr_kNm": round(Mcr_kNm, 2),
            "lambda_LT": round(lambda_LT, 4), "alpha_LT": alpha_LT,
            "phi_LT": round(phi_LT, 4), "chi_LT": round(chi_LT, 4),
            "Mb_kNm": round(Mb_kNm, 2),
            "clause": "IRC 22:2015 - Cl.603.3.3.1", "source": "built-in",
        }

    # IRC 22:2015 Cl.603.3.3.3 — reduced bending resistance under high shear (V > 0.6·Vd).
    def compute_combined_bending_shear(self, Md_kNm: float, V_kN: float, Vd_kN: float) -> dict:
        sec = self.sec
        fy, gm0 = self.mat.fy, self.mat.gamma_m0
        hw = sec.dw + sec.tf_top / 2.0 + sec.tf_bot / 2.0
        Mfd_kNm = fy * sec.Af_bot * hw / 1e6 / gm0

        if V_kN <= 0.6 * Vd_kN:
            return {
                "Mdv_kNm": round(Md_kNm, 2), "Mfd_kNm": round(Mfd_kNm, 2),
                "beta": 0.0, "reduction_required": False,
                "clause": "IRC 22:2015 - Cl.603.3.3.3", "source": "built-in",
            }

        beta = min((2.0 * V_kN / Vd_kN - 1.0) ** 2, 1.0)
        Mdv_kNm = Md_kNm - beta * (Md_kNm - Mfd_kNm)

        return {
            "Mdv_kNm": round(Mdv_kNm, 2), "Mfd_kNm": round(Mfd_kNm, 2),
            "beta": round(beta, 4), "reduction_required": True,
            "clause": "IRC 22:2015 - Cl.603.3.3.3", "source": "built-in",
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

        return {
            "mu_r": mu_r,
            "f_f_MPa": strength["f_f_normal_MPa"],
            "tau_f_MPa": strength["tau_f_shear_MPa"],
            "f_fd_MPa": assessment["f_fd_MPa"],
            "tau_fd_MPa": assessment["tau_fd_MPa"],
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
                              xu_mm: float, Qu_kN: float) -> dict:
        sec, mat, slab = self.sec, self.mat, self.slab
        ds, h_haunch = slab.thickness, slab.haunch_depth
        n_studs = self.studs.n_per_section

        n = mat.Es / mat.Ecm
        t_eff = min(xu_mm, ds)
        Aec = beff_mm * t_eff / n
        y_steel = ds + h_haunch + sec.D - sec.y_cg_from_bot
        y_conc = t_eff / 2.0
        total_A = sec.A_steel + Aec
        y_composite = (sec.A_steel * y_steel + Aec * y_conc) / total_A
        I_steel = sec.Iz_steel + sec.A_steel * (y_steel - y_composite) ** 2
        I_conc = beff_mm * t_eff ** 3 / (12.0 * n) + Aec * (y_composite - y_conc) ** 2
        Ic = I_steel + I_conc
        Y = abs(y_composite - y_conc)
        VL = Vu_kN * 1e3 * Aec * Y / Ic
        spacing = n_studs * Qu_kN * 1e3 / VL if VL > 0 else float("inf")

        return {
            "modular_ratio": round(n, 3), "Aec_mm2": round(Aec, 1),
            "Ic_mm4": round(Ic, 0), "Y_mm": round(Y, 2),
            "VL_N_per_mm": round(VL, 3), "spacing_mm": round(spacing, 1),
            "n_studs_per_section": n_studs,
            "clause": "IRC 22:2015 - Cl.606.4.1", "source": "built-in",
        }

    # Orchestrator — runs every IRC 22:2015 clause computation into one CapacityResults.
    def compute_all(self, Vu_kN: float = 0.0, stress_range_MPa: float = 0.0) -> CapacityResults:
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

        # 5. LTB buckling resistance
        ltb = self.compute_buckling_resistance(results.beff_mm)
        results.Mcr_kNm = ltb["Mcr_kNm"]
        results.lambda_LT = ltb["lambda_LT"]
        results.chi_LT = ltb["chi_LT"]
        results.Mb_kNm = ltb["Mb_kNm"]
        results.details["buckling_resistance"] = ltb

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
        results.details["fatigue"] = fatigue

        # 11. Shear stud capacity
        stud_cap = self.compute_stud_capacity()
        results.Qu_kN = stud_cap["Qu_kN"]
        results.details["stud_capacity"] = stud_cap

        # 12. Stud spacing
        if Vu_kN > 0 and results.xu_mm > 0:
            stud_sp = self.compute_stud_spacing(
                Vu_kN, results.beff_mm, results.xu_mm, results.Qu_kN
            )
            results.stud_spacing_mm = stud_sp["spacing_mm"]
            results.details["stud_spacing"] = stud_sp

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
    # Demand/Capacity ratio engine — PASS < 0.90, WARN 0.90–1.00, FAIL ≥ 1.00.

    PASS_THRESHOLD = 0.90
    FAIL_THRESHOLD = 1.00

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

    # Run all eight IRC 22:2015 design checks (flexure, shear, interaction, LTB, deflections, fatigue).
    def run_all_checks(self) -> List[CheckResult]:
        self.checks.clear()
        d, c = self.demand, self.capacity

        self._add_check(1, "ULS Flexure", "Cl.603.3.1",
                         d.Mu_kNm, c.Md_kNm, "kNm",
                         note=f"PNA in {c.pna_location}, xu={c.xu_mm:.1f} mm")

        self._add_check(2, "ULS Shear", "Cl.603.3.3.2",
                         d.Vu_kN, c.Vd_kN, "kN",
                         note=f"Av={c.Av_mm2:.0f} mm2")

        effective_Md = c.Mdv_kNm if c.beta_interaction > 0 else c.Md_kNm
        self._add_check(3, "Bending-Shear Interaction", "Cl.603.3.3.3",
                         d.Mu_kNm, effective_Md, "kNm",
                         note=f"beta={c.beta_interaction:.4f}")

        self._add_check(4, "LTB (Construction Stage)", "Cl.603.3.3.1",
                         d.M_construction_kNm if d.M_construction_kNm > 0 else d.Mu_kNm, c.Mb_kNm, "kNm",
                         note=f"lambda_LT={c.lambda_LT:.4f}, chi_LT={c.chi_LT:.4f}")

        if d.delta_live_mm > 0:
            self._add_check(5, "SLS Deflection (Live)", "Cl.604.3.2",
                             d.delta_live_mm, c.defl_limit_live_mm, "mm",
                             note="Limit = L/800")

        if d.delta_total_mm > 0:
            self._add_check(6, "SLS Deflection (Total)", "Cl.604.3.2",
                             d.delta_total_mm, c.defl_limit_total_mm, "mm",
                             note="Limit = L/600")

        if d.stress_range_MPa > 0 and c.f_fd_MPa > 0:
            self._add_check(7, "Fatigue Normal Stress", "Cl.605",
                             d.stress_range_MPa, c.f_fd_MPa, "MPa",
                             note=f"Nsc={d.Nsc:,}")

        if d.shear_range_MPa > 0 and c.tau_fd_MPa > 0:
            self._add_check(8, "Fatigue Shear Stress", "Cl.605",
                             d.shear_range_MPa, c.tau_fd_MPa, "MPa",
                             note=f"Nsc={d.Nsc:,}")

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
        return "\n".join(lines)

    def _build_capacity_summary(self) -> str:
        c = self.capacity
        sc = c.details.get("section_class", {})
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
        lines.append(f"     Mp = {c.Mp_kNm:,.2f} kNm")
        lines.append(f"     Md = Mp / gamma_m0 = {c.Md_kNm:,.2f} kNm")

        lines.append(f"\n  4. Plastic Shear Resistance (Cl.603.3.3.2)")
        lines.append(f"     Av = {c.Av_mm2:,.0f} mm2")
        lines.append(f"     Vn = {c.Vn_kN:,.2f} kN")
        lines.append(f"     Vd = Vn / gamma_m0 = {c.Vd_kN:,.2f} kN")

        lines.append(f"\n  5. Buckling Resistance Moment (Cl.603.3.3.1)")
        lines.append(f"     Mcr = {c.Mcr_kNm:,.2f} kNm")
        lines.append(f"     lambda_LT = {c.lambda_LT:.4f}")
        lines.append(f"     chi_LT = {c.chi_LT:.4f}")
        lines.append(f"     Mb = {c.Mb_kNm:,.2f} kNm")

        lines.append(f"\n  6. Combined Bending + Shear (Cl.603.3.3.3)")
        lines.append(f"     beta = {c.beta_interaction:.4f}")
        lines.append(f"     Mdv = {c.Mdv_kNm:,.2f} kNm")

        lines.append(f"\n  7. Deflection Limits (Cl.604.3.2)")
        lines.append(f"     Live + impact  <= L/800 = {c.defl_limit_live_mm:.2f} mm")
        lines.append(f"     Total          <= L/600 = {c.defl_limit_total_mm:.2f} mm")

        lines.append(f"\n  8. Fatigue Assessment (Cl.605)")
        lines.append(f"     f_fd  = {c.f_fd_MPa:.3f} MPa")
        lines.append(f"     tau_fd = {c.tau_fd_MPa:.3f} MPa")

        lines.append(f"\n  9. Shear Stud Capacity (Cl.606.3.1)")
        lines.append(f"     Qu = {c.Qu_kN:.3f} kN per stud")
        if c.stud_spacing_mm > 0:
            lines.append(f"     Required spacing = {c.stud_spacing_mm:.1f} mm")

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
    gamma_dl = IRC6_2017.table_B2(load_type="dead_load", effect="adding", combination="basic")
    gamma_ll = IRC6_2017.table_B2(load_type="live_load", load_category="leading", combination="basic")
    # IRC 6:2017 Cl.208.3 — impact factor for Class 70R(W) wheel loading.
    impact_fraction = IRC6_2017.cl_208_3_impact_factor(L_m)
    impact_multiplier = 1.0 + impact_fraction

    # Construction stage — steel self-weight + wet concrete only; no SIDL, no live load.
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
        Nsc=config.fatigue.Nsc,
        combination=(
            f"ULS Basic: γDL={gamma_dl}·DL + γLL={gamma_ll}·IF={impact_multiplier:.3f}·LL"
        ),
        location="midspan (interior girder)",
        member="interior_longitudinal_beam",
    )

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
    print(f"  Config: {config.summary()}")

    # -- Step 2: Demand from Analyser --
    print("\n[Step 2/5] Extracting design demands (Analyser) ...")
    if demand is None and analysis_results is not None:
        demand = _extract_demands_from_analysis(analysis_results, config)
    elif demand is None:
        demand = _example_demands(config)
    print(f"  Mu              = {demand.Mu_kNm:.2f} kNm")
    print(f"  Vu              = {demand.Vu_kN:.2f} kN")
    print(f"  M_construction  = {demand.M_construction_kNm:.2f} kNm")
    print(f"  delta_live      = {demand.delta_live_mm:.3f} mm")
    print(f"  delta_total     = {demand.delta_total_mm:.3f} mm")
    print(f"  stress_range    = {demand.stress_range_MPa:.3f} MPa")
    print(f"  shear_range     = {demand.shear_range_MPa:.3f} MPa")
    print(f"  Source: {demand.source}")

    # -- Step 3: IRC 22 Capacity --
    print("\n[Step 3/5] Computing IRC 22:2015 capacities ...")
    calculator = IRC22CapacityCalculator(config)
    capacity = calculator.compute_all(Vu_kN=demand.Vu_kN, stress_range_MPa=demand.stress_range_MPa)
    print(f"  beff  = {capacity.beff_mm:.1f} mm    (Cl.603.2.1)")
    print(f"  Md    = {capacity.Md_kNm:,.2f} kNm  (Cl.603.3.1)")
    print(f"  Vd    = {capacity.Vd_kN:,.2f} kN   (Cl.603.3.3.2)")
    print(f"  Mb    = {capacity.Mb_kNm:,.2f} kNm  (Cl.603.3.3.1)")
    print(f"  Qu    = {capacity.Qu_kN:.3f} kN/stud (Cl.606.3.1)")

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

    return report_text, engine


# ======================================================================
#  ENTRY POINT
# ======================================================================

if __name__ == "__main__":
    run_design_check()
