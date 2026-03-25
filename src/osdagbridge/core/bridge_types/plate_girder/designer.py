"""
IRC 22:2015 Composite Bridge Design Checker — Single-File Pipeline
===================================================================

Automated limit-state verification of steel-concrete composite bridge
girders per IRC:22-2015 (Limit State Method for Composite Construction).

Pipeline Flow
-------------
    Step 1 - BridgeConfig       : Material, section, geometry parameters
    Step 2 - DemandExtractor    : Factored force demands (Mu, Vu, deflections)
    Step 3 - IRC22Capacity      : Clause-by-clause capacity computation
    Step 4 - DCREngine          : Demand / Capacity ratios & PASS/WARN/FAIL
    Step 5 - ReportGenerator    : Formatted engineering report

Clause Coverage (IRC 22:2015)
-----------------------------
    Cl. 603.2.1   - Effective width of concrete flange
    Cl. 603       - Section classification (web + flange)
    Cl. 603.3.1   - Positive moment capacity (plastic)
    Cl. 603.3.3.1 - Lateral-torsional buckling resistance
    Cl. 603.3.3.2 - Plastic shear resistance
    Cl. 603.3.3.3 - Combined bending + high shear
    Cl. 604.3     - Modular ratio
    Cl. 604.3.1   - SLS limiting stresses
    Cl. 604.3.2   - Deflection limits
    Cl. 605       - Fatigue assessment
    Cl. 606.3.1   - Shear stud connector strength
    Cl. 606.4.1   - Longitudinal shear & stud spacing

Author      : Karn Agarwal
Affiliation : Dayalbagh Educational Institute, Agra
License     : MIT
Version     : 1.0.0

Usage
-----
    python main.py
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


# ======================================================================
#  SECTION 1 -- BRIDGE CONFIGURATION (Input Dataclasses)
# ======================================================================


@dataclass
class SteelProperties:
    """
    Material strengths and partial safety factors.

    References
    ----------
    IRC 22:2015 Annexure III - Steel, Concrete, Reinforcement properties
    IRC 22:2015 Table 1 (Cl.601.4) - Partial safety factors
    """
    # -- Structural steel (IS 2062 / IRC 22 Annex III) --
    steel_grade: str = "E350"
    fy: float = 350.0           # MPa - characteristic yield strength
    fu: float = 490.0           # MPa - ultimate tensile strength
    Es: float = 200_000.0      # MPa - modulus of elasticity (Cl.602)

    # -- Concrete (IRC 22 Annex III Table III.1) --
    concrete_grade: str = "M65"
    fck: float = 65.0           # MPa - cube compressive strength
    fctm: float = 4.1           # MPa - mean tensile strength
    Ecm: float = 38_000.0      # MPa - secant modulus at 28 days

    # -- Reinforcement (IS 1786 / IRC 22 Annex III) --
    rebar_grade: str = "Fe500"
    fy_rebar: float = 500.0     # MPa - characteristic yield strength

    # -- Partial safety factors (IRC 22 Table 1, Cl.601.4) --
    gamma_m0: float = 1.10      # yielding / instability
    gamma_m1: float = 1.25      # ultimate stress
    gamma_v: float = 1.25       # shear connectors
    gamma_mft: float = 1.35     # fatigue strength


@dataclass
class SteelSection:
    """
    Plate girder / rolled I-section dimensions (all in mm).

    Depth relation : D = tf_top + dw + tf_bot
    Shear area Av  = dw x tw
    """
    D: float            # overall depth
    bf_top: float       # top flange width
    tf_top: float       # top flange thickness
    bf_bot: float       # bottom flange width
    tf_bot: float       # bottom flange thickness
    tw: float           # web thickness
    fabrication: str = "welded"   # "welded" or "rolled"

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
        """Steel centroid measured from bottom fibre (mm)."""
        y_b = self.tf_bot / 2.0
        y_w = self.tf_bot + self.dw / 2.0
        y_t = self.tf_bot + self.dw + self.tf_top / 2.0
        return (
            self.Af_bot * y_b + self.Aw * y_w + self.Af_top * y_t
        ) / self.A_steel

    @property
    def Iz_steel(self) -> float:
        """Second moment of area about centroidal strong axis (mm^4)."""
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
        """Plastic section modulus about strong axis (mm^3)."""
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
        """Elastic section modulus about strong axis (mm^3)."""
        yc = self.y_cg_from_bot
        y_top = self.D - yc
        return self.Iz_steel / max(yc, y_top)


@dataclass
class SlabProperties:
    """Concrete slab dimensions and reinforcement (all mm)."""
    thickness: float
    haunch_depth: float = 0.0
    rebar_area_top: float = 0.0
    rebar_area_bot: float = 0.0
    cover_top: float = 40.0
    cover_bot: float = 25.0


@dataclass
class GeometryConfig:
    """Bridge-level geometry parameters (lengths in m)."""
    span: float
    beam_spacing: float
    carriageway_width: float
    beam_type: str = "inner"
    n_girders: int = 7
    edge_distance: float = 1.05
    support_type: str = "simply_supported"


@dataclass
class ShearStudConfig:
    """Headed stud connector properties (Cl.606)."""
    diameter: float = 22.0
    height: float = 150.0
    fu: float = 500.0
    n_per_section: int = 2


@dataclass
class FatigueConfig:
    """Fatigue design parameters (Cl.605)."""
    Nsc: int = 2_000_000
    stress_range: float = 55.0
    shear_range: float = 30.0
    detail_category: str = "welded"
    ffn: float = 92.0
    tfn: float = 59.0


@dataclass
class BridgeConfig:
    """
    Master bridge configuration - single input to the entire pipeline.

        BridgeConfig
            |-- DemandExtractor
            |-- IRC22CapacityCalculator
            |-- DCREngine
            +-- ReportGenerator
    """
    material: SteelProperties = field(default_factory=SteelProperties)
    section: SteelSection = field(default_factory=lambda: SteelSection(
        D=1500, bf_top=400, tf_top=20, bf_bot=500, tf_bot=25, tw=12,
    ))
    slab: SlabProperties = field(default_factory=lambda: SlabProperties(thickness=250))
    geometry: GeometryConfig = field(default_factory=lambda: GeometryConfig(
        span=33.5, beam_spacing=2.2775, carriageway_width=10.0,
    ))
    studs: ShearStudConfig = field(default_factory=ShearStudConfig)
    fatigue: FatigueConfig = field(default_factory=FatigueConfig)

    @classmethod
    def example_33m_bridge(cls) -> "BridgeConfig":
        """
        Factory: realistic 33.5 m simply-supported composite bridge
        matching the ospgrillage analyser model.
        """
        return cls(
            material=SteelProperties(
                steel_grade="E350", fy=350.0, fu=490.0, Es=200_000.0,
                concrete_grade="M65", fck=65.0, fctm=4.1, Ecm=38_000.0,
                rebar_grade="Fe500", fy_rebar=500.0,
            ),
            section=SteelSection(
                D=1500, bf_top=400, tf_top=20,
                bf_bot=500, tf_bot=25, tw=12, fabrication="welded",
            ),
            slab=SlabProperties(
                thickness=250, haunch_depth=0,
                rebar_area_top=1257.0, rebar_area_bot=1257.0,
            ),
            geometry=GeometryConfig(
                span=33.5, beam_spacing=2.2775,
                carriageway_width=10.0, beam_type="inner",
                n_girders=7, edge_distance=1.05,
            ),
            studs=ShearStudConfig(diameter=22, height=150, fu=500, n_per_section=2),
            fatigue=FatigueConfig(
                Nsc=2_000_000, stress_range=55.0, shear_range=30.0,
                detail_category="welded", ffn=92.0, tfn=59.0,
            ),
        )

    def summary(self) -> str:
        s = self.section
        g = self.geometry
        m = self.material
        return (
            f"L={g.span}m | {m.steel_grade}/{m.concrete_grade} | "
            f"D={s.D}mm | {g.n_girders} girders @ {g.beam_spacing}m"
        )


# ======================================================================
#  SECTION 2 -- DEMAND EXTRACTOR (Analyser Stage)
# ======================================================================


@dataclass
class DemandEnvelope:
    """
    Factored force demands at the critical section.
    Every field carries its unit in the name suffix for clarity.
    """
    # -- ULS demands --
    Mu_kNm: float = 0.0
    Vu_kN: float = 0.0
    Nu_kN: float = 0.0

    # -- SLS demands --
    delta_live_mm: float = 0.0
    delta_total_mm: float = 0.0

    # -- Fatigue demands --
    stress_range_MPa: float = 0.0
    shear_range_MPa: float = 0.0
    Nsc: int = 2_000_000

    # -- Metadata --
    governing_combination: str = "ULS Combination I"
    location: str = "midspan"
    member: str = ""
    source: str = "manual"


class DemandExtractor:
    """
    Factory for DemandEnvelope objects.

    Two entry-points:
        1. from_manual(...)           - user supplies demand values directly
        2. apply_load_factors(...)    - builds envelope from unfactored DL/LL
    """

    @staticmethod
    def from_manual(
        Mu_kNm: float,
        Vu_kN: float,
        Nu_kN: float = 0.0,
        delta_live_mm: float = 0.0,
        delta_total_mm: float = 0.0,
        stress_range_MPa: float = 0.0,
        shear_range_MPa: float = 0.0,
        Nsc: int = 2_000_000,
        combination: str = "ULS Combination I",
        location: str = "midspan",
        member: str = "interior_girder",
    ) -> DemandEnvelope:
        """Create demand envelope from user-supplied values."""
        return DemandEnvelope(
            Mu_kNm=Mu_kNm, Vu_kN=Vu_kN, Nu_kN=Nu_kN,
            delta_live_mm=delta_live_mm, delta_total_mm=delta_total_mm,
            stress_range_MPa=stress_range_MPa, shear_range_MPa=shear_range_MPa,
            Nsc=Nsc, governing_combination=combination,
            location=location, member=member, source="manual",
        )

    @staticmethod
    def apply_load_factors(
        M_dead_kNm: float,
        M_live_kNm: float,
        V_dead_kN: float,
        V_live_kN: float,
        gamma_dead: float = 1.35,
        gamma_live: float = 1.50,
        impact_factor: float = 1.10,
    ) -> DemandEnvelope:
        """
        Build demand envelope from unfactored dead/live force components.
        IRC:6-2017 load combination factors applied.
        """
        Mu = gamma_dead * M_dead_kNm + gamma_live * impact_factor * M_live_kNm
        Vu = gamma_dead * V_dead_kN + gamma_live * impact_factor * V_live_kN
        return DemandEnvelope(
            Mu_kNm=round(Mu, 3), Vu_kN=round(Vu, 3),
            governing_combination=(
                f"gDL={gamma_dead} x DL + gLL={gamma_live} x IF={impact_factor} x LL"
            ),
            location="midspan", source="factored_components",
        )


# ======================================================================
#  SECTION 3 -- IRC 22:2015 CAPACITY CALCULATOR
# ======================================================================


@dataclass
class CapacityResults:
    """Aggregated capacity values from all IRC 22 checks."""

    # Cl.603.2.1 - Effective width
    beff_mm: float = 0.0

    # Cl.603.3.1 - Positive moment capacity
    xu_mm: float = 0.0
    pna_location: str = ""
    Mp_kNm: float = 0.0
    Md_kNm: float = 0.0

    # Cl.603.3.3.1 - Buckling resistance moment
    Mcr_kNm: float = 0.0
    lambda_LT: float = 0.0
    chi_LT: float = 0.0
    Mb_kNm: float = 0.0

    # Cl.603.3.3.2 - Shear
    Av_mm2: float = 0.0
    Vn_kN: float = 0.0
    Vd_kN: float = 0.0

    # Cl.603.3.3.3 - Combined bending + shear
    Mdv_kNm: float = 0.0
    beta_interaction: float = 0.0

    # Cl.604.3.2 - Deflection limits
    defl_limit_live_mm: float = 0.0
    defl_limit_total_mm: float = 0.0

    # Cl.604.3.1 - SLS stress limits
    sigma_c_limit_MPa: float = 0.0
    sigma_s_limit_MPa: float = 0.0

    # Cl.605 - Fatigue
    f_fd_MPa: float = 0.0
    tau_fd_MPa: float = 0.0

    # Cl.606 - Shear connectors
    Qu_kN: float = 0.0
    stud_spacing_mm: float = 0.0

    # Meta
    source: str = "built-in"
    details: Dict[str, dict] = field(default_factory=dict)


class IRC22CapacityCalculator:
    """
    Clause-by-clause IRC 22:2015 capacity calculator.
    Uses built-in formulas for all clause computations.

    Usage
    -----
        config  = BridgeConfig.example_33m_bridge()
        calc    = IRC22CapacityCalculator(config)
        results = calc.compute_all(Vu_kN=850.0)
    """

    def __init__(self, config: BridgeConfig):
        self.cfg = config
        self.mat = config.material
        self.sec = config.section
        self.slab = config.slab
        self.geo = config.geometry
        self.studs = config.studs
        self.fatigue = config.fatigue

    # ---------------------------------------------------------
    #  Cl.603.2.1 - Effective Width (Simply Supported)
    # ---------------------------------------------------------

    def compute_effective_width(self) -> dict:
        """IRC 22:2015 Cl.603.2.1 - Effective width of concrete flange."""
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

    # ---------------------------------------------------------
    #  Cl.603 - Section Classification
    # ---------------------------------------------------------

    def classify_section(self) -> dict:
        """IRC 22:2015 Cl.603 - web & flange classification."""
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

    # ---------------------------------------------------------
    #  Cl.603.3.1 - Positive Moment Capacity (Plastic)
    # ---------------------------------------------------------

    def compute_moment_capacity(self, beff_mm: float) -> dict:
        """IRC 22:2015 Cl.603.3.1 - Plastic moment capacity (sagging)."""
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

    # ---------------------------------------------------------
    #  Cl.603.3.3.2 - Plastic Shear Resistance
    # ---------------------------------------------------------

    def compute_shear_capacity(self) -> dict:
        """IRC 22:2015 Cl.603.3.3.2 - Plastic shear resistance."""
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

    # ---------------------------------------------------------
    #  Cl.603.3.3.1 - Lateral-Torsional Buckling Resistance
    # ---------------------------------------------------------

    def compute_buckling_resistance(self, beff_mm: float) -> dict:
        """IRC 22:2015 Cl.603.3.3.1 - Buckling resistance moment."""
        sec = self.sec
        mat = self.mat
        fy, Es = mat.fy, mat.Es
        G = Es / (2.0 * (1.0 + 0.3))
        LLT_mm = self.geo.span * 1000.0

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

    # ---------------------------------------------------------
    #  Cl.603.3.3.3 - Combined Bending + High Shear
    # ---------------------------------------------------------

    def compute_combined_bending_shear(self, Md_kNm: float, V_kN: float, Vd_kN: float) -> dict:
        """IRC 22:2015 Cl.603.3.3.3 - Reduced bending under high shear."""
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

    # ---------------------------------------------------------
    #  Cl.604.3 - Modular Ratio
    # ---------------------------------------------------------

    def compute_modular_ratio(self) -> dict:
        """IRC 22:2015 Cl.604.3 - Short- and long-term modular ratio."""
        Es, Ecm = self.mat.Es, self.mat.Ecm
        Kc = 0.5
        m_short = max(Es / Ecm, 7.5)
        m_long = max(Es / (Kc * Ecm), 15.0)
        return {
            "Es_MPa": Es, "Ecm_MPa": Ecm, "Kc": Kc,
            "m_short": round(m_short, 3), "m_long": round(m_long, 3),
            "clause": "IRC 22:2015 - Cl.604.3", "source": "built-in",
        }

    # ---------------------------------------------------------
    #  Cl.604.3.1 - SLS Limiting Stresses
    # ---------------------------------------------------------

    def compute_sls_stress_limits(self) -> dict:
        """IRC 22:2015 Cl.604.3.1 - Allowable stresses for serviceability."""
        return {
            "sigma_c_allow_MPa": round(0.48 * self.mat.fck, 2),
            "sigma_rebar_allow_MPa": round(0.80 * self.mat.fy_rebar, 2),
            "sigma_steel_allow_MPa": round(0.9 * self.mat.fy, 2),
            "clause": "IRC 22:2015 - Cl.604.3.1", "source": "built-in",
        }

    # ---------------------------------------------------------
    #  Cl.604.3.2 - Deflection Limits
    # ---------------------------------------------------------

    def compute_deflection_limits(self) -> dict:
        """IRC 22:2015 Cl.604.3.2 - Deflection limits."""
        span_mm = self.geo.span * 1000.0
        return {
            "span_mm": span_mm,
            "defl_limit_live_mm": round(span_mm / 800.0, 3),
            "defl_limit_total_mm": round(span_mm / 600.0, 3),
            "clause": "IRC 22:2015 - Cl.604.3.2", "source": "built-in",
        }

    # ---------------------------------------------------------
    #  Cl.605 - Fatigue Assessment
    # ---------------------------------------------------------

    def compute_fatigue(self) -> dict:
        """IRC 22:2015 Cl.605 - Fatigue design strength."""
        fat = self.fatigue
        mat = self.mat
        Nsc, ffn, tfn = fat.Nsc, fat.ffn, fat.tfn
        gamma_mft = mat.gamma_mft
        tp = max(self.sec.tf_top, self.sec.tf_bot)

        if self.sec.fabrication == "welded" and tp > 25.0:
            mu_r = min((25.0 / tp) ** 0.25, 1.0)
        else:
            mu_r = 1.0

        exponent = 1.0 / 3.0 if Nsc <= 5e6 else 1.0 / 5.0
        f_f = ffn * (5e6 / Nsc) ** exponent
        tau_f = tfn * (5e6 / Nsc) ** (1.0 / 5.0)
        f_fd = mu_r * f_f / gamma_mft
        tau_fd = mu_r * tau_f / gamma_mft

        return {
            "mu_r": round(mu_r, 4),
            "f_f_MPa": round(f_f, 3), "tau_f_MPa": round(tau_f, 3),
            "f_fd_MPa": round(f_fd, 3), "tau_fd_MPa": round(tau_fd, 3),
            "Nsc": Nsc,
            "exempt_stress_check": fat.stress_range < 27.0 / gamma_mft,
            "clause": "IRC 22:2015 - Cl.605.2 / 605.3 / 605.4",
            "source": "built-in",
        }

    # ---------------------------------------------------------
    #  Cl.606.3.1 - Shear Stud Connector Strength
    # ---------------------------------------------------------

    def compute_stud_capacity(self) -> dict:
        """IRC 22:2015 Cl.606.3.1 - Design strength of headed stud."""
        stud = self.studs
        mat = self.mat
        gv = mat.gamma_v
        d, hs, fu = stud.diameter, stud.height, stud.fu
        fck_cu, Ecm = mat.fck, mat.Ecm

        fck_cyl = 0.8 * fck_cu
        hd = hs / d
        alpha = 1.0 if hd >= 4.0 else 0.2 * (hd + 1.0)
        A_stud = math.pi * d ** 2 / 4.0

        Qu_steel = 0.8 * fu * A_stud / gv
        Qu_conc = 0.29 * alpha * d ** 2 * math.sqrt(fck_cyl * Ecm) / gv
        Qu = min(Qu_steel, Qu_conc)
        governs = "steel" if Qu_steel <= Qu_conc else "concrete"

        return {
            "Qu_kN": round(Qu / 1e3, 3),
            "Qu_steel_kN": round(Qu_steel / 1e3, 3),
            "Qu_conc_kN": round(Qu_conc / 1e3, 3),
            "governs": governs, "alpha": round(alpha, 4),
            "fck_cyl_MPa": round(fck_cyl, 2),
            "clause": "IRC 22:2015 - Cl.606.3.1 (Eq 6.1)",
            "source": "built-in",
        }

    # ---------------------------------------------------------
    #  Cl.606.4.1 - Longitudinal Shear & Stud Spacing
    # ---------------------------------------------------------

    def compute_stud_spacing(self, Vu_kN: float, beff_mm: float,
                              xu_mm: float, Qu_kN: float) -> dict:
        """IRC 22:2015 Cl.606.4.1 - Required stud spacing at ULS."""
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

    # ---------------------------------------------------------
    #  Master: compute_all()
    # ---------------------------------------------------------

    def compute_all(self, Vu_kN: float = 0.0) -> CapacityResults:
        """Run every IRC 22 capacity computation and return aggregated results."""
        results = CapacityResults()
        results.source = "built-in"

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
        fatigue = self.compute_fatigue()
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
    """Single design-check output row."""
    check_id: int
    name: str
    clause: str
    demand: float
    demand_unit: str
    capacity: float
    capacity_unit: str
    dcr: float
    status: str             # "PASS" | "WARN" | "FAIL" | "INFO"
    note: str = ""


class DCREngine:
    """
    Demand-to-Capacity Ratio engine.

    Classification:
        PASS : DCR < 0.90
        WARN : 0.90 <= DCR < 1.00
        FAIL : DCR >= 1.00
    """

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

    def run_all_checks(self) -> List[CheckResult]:
        """
        Execute all IRC 22 design checks:
            1. ULS Flexure           (Cl.603.3.1)
            2. ULS Shear             (Cl.603.3.3.2)
            3. Bending-Shear         (Cl.603.3.3.3)
            4. LTB Construction      (Cl.603.3.3.1)
            5. SLS Deflection Live   (Cl.604.3.2)
            6. SLS Deflection Total  (Cl.604.3.2)
            7. Fatigue Normal        (Cl.605)
            8. Fatigue Shear         (Cl.605)
        """
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
                         d.Mu_kNm, c.Mb_kNm, "kNm",
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
    """Generates formatted design-check reports."""

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

    def generate(self) -> str:
        """Build the complete formatted report string."""
        return "\n".join([
            self._build_header(), self._build_config(), self._build_demands(),
            self._build_capacity_summary(), self._build_dcr_table(),
            self._build_bar_chart(), self._build_verdict(),
        ])

    def save(self, filepath: str) -> str:
        """Write the report to a text file."""
        report_text = self.generate()
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report_text)
        return os.path.abspath(filepath)


# ======================================================================
#  SECTION 6 -- MAIN PIPELINE
# ======================================================================


def _example_demands(config: BridgeConfig) -> DemandEnvelope:
    """
    Realistic factored demand values for the 33.5 m bridge.

    Dead Load Components (per girder):
        Steel self-weight  : ~3 kN/m
        Deck slab          : 25 kN/m3 x t_slab x beam_spacing
        SDL (wearing, rail): distributed

    Live Load (IRC Class 70R + Class A):
        M_LL ~ 1,800 kNm,  V_LL ~ 350 kN  (per interior girder)

    Factored (ULS Comb I):
        gamma_DL = 1.35,  gamma_LL = 1.50,  Impact Factor = 1.10
    """
    L = config.geometry.span
    A_steel_m2 = config.section.A_steel * 1e-6
    w_sw = A_steel_m2 * 78.5
    w_slab = 25.0 * (config.slab.thickness / 1000.0) * config.geometry.beam_spacing
    w_sdl = (4.32 * config.geometry.beam_spacing + 1.5 + 4.0 / config.geometry.n_girders)
    w_total_dl = w_sw + w_slab + w_sdl

    M_dl = w_total_dl * L ** 2 / 8.0
    V_dl = w_total_dl * L / 2.0
    M_ll, V_ll = 1800.0, 350.0
    gamma_dl, gamma_ll, impact = 1.35, 1.50, 1.10

    Mu = gamma_dl * M_dl + gamma_ll * impact * M_ll
    Vu = gamma_dl * V_dl + gamma_ll * impact * V_ll

    return DemandExtractor.from_manual(
        Mu_kNm=round(Mu, 2), Vu_kN=round(Vu, 2),
        delta_live_mm=28.0, delta_total_mm=38.0,
        stress_range_MPa=config.fatigue.stress_range,
        shear_range_MPa=config.fatigue.shear_range,
        Nsc=config.fatigue.Nsc,
        combination=f"ULS Comb I: {gamma_dl}*DL + {gamma_ll}*{impact}*LL",
        location="midspan (interior girder)",
        member="interior_longitudinal_beam",
    )


def run_design_check(
    config: BridgeConfig | None = None,
    demand: DemandEnvelope | None = None,
    save_report: bool = True,
    report_path: str = "design_check_report.txt",
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
        config       : BridgeConfig (default: 33.5 m example bridge)
        demand       : DemandEnvelope (default: example demands)
        save_report  : save .txt report file
        report_path  : output file path
        print_report : print report to console
    """
    print("=" * 60)
    print("  IRC 22:2015 DESIGN CHECK PIPELINE")
    print("=" * 60)

    # -- Step 1: Configuration --
    print("\n[Step 1/5] Loading bridge configuration ...")
    if config is None:
        config = BridgeConfig.example_33m_bridge()
    print(f"  Config: {config.summary()}")

    # -- Step 2: Demand from Analyser --
    print("\n[Step 2/5] Extracting design demands (Analyser) ...")
    if demand is None:
        demand = _example_demands(config)
    print(f"  Mu = {demand.Mu_kNm:.2f} kNm")
    print(f"  Vu = {demand.Vu_kN:.2f} kN")
    print(f"  Source: {demand.source}")

    # -- Step 3: IRC 22 Capacity --
    print("\n[Step 3/5] Computing IRC 22:2015 capacities ...")
    calculator = IRC22CapacityCalculator(config)
    capacity = calculator.compute_all(Vu_kN=demand.Vu_kN)
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

    if save_report:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_dir, report_path)
        saved = reporter.save(full_path)
        print(f"\n  Report saved to: {saved}")

    print("\n" + "=" * 60)
    print(f"  PIPELINE COMPLETE - Overall: {engine.overall_status()}")
    print("=" * 60)

    return report_text


# ======================================================================
#  ENTRY POINT
# ======================================================================

if __name__ == "__main__":
    run_design_check()
