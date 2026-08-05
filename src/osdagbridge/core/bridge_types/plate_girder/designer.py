# IRC 22:2015 composite plate-girder design pipeline: Config -> Demand -> Capacity -> DCR -> Report.

from __future__ import annotations
import warnings
import math
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf-16'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

from osdagbridge.core.bridge_types.plate_girder.analysis_results import PlateGirderAnalysisResults
from osdagbridge.core.bridge_types.plate_girder.initial_sizing import (
    composite_section_properties,
    steel_i_section_properties,
)
from osdagbridge.core.utils.codes.irc22_2015 import IRC22_2014
from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
from osdagbridge.core.utils.common import (
    KEY_MATERIAL_GIRDER_E,
    KEY_MATERIAL_GIRDER_G,
    KEY_MATERIAL_GIRDER_POISSON,
    KEY_DO_GAMMA_MF,
    KEY_DO_GAMMA_M0,
    KEY_DO_GAMMA_M1,
    KEY_DO_GAMMA_V, 
    KEY_DS_REINF_MATERIAL,
    KEY_DS_BOTTOM_CLEAR_COVER,
    KEY_SC_LEFT_SUPPORT,
    KEY_SC_RIGHT_SUPPORT,
    KEY_SD_SC_Qu_kN,
    KEY_SD_SC_Qr_kN,
    KEY_SD_SC_VL,
    KEY_SD_SC_SL1,
    KEY_SD_SC_SL2,
    KEY_SD_SC_SR,
    KEY_SD_SC_H_kN,
    KEY_SD_SC_Vr_kN,
    KEY_SD_SC_LIMIT_600,
    KEY_SD_SC_LIMIT_3TSLAB,
    KEY_SD_SC_LIMIT_4HSTUD,
    KEY_SD_SC_D_LIMIT,
    KEY_SD_SC_H_MIN,
    KEY_SD_SC_EDGE_DIST,
    KEY_SD_SC_REQ_EDGE_DIST,
    KEY_SD_SC_CLEAR_COVER,
    KEY_SD_SC_REQ_CLEAR_COVER,
    KEY_SD_TS_VL,
    KEY_SD_TS_VCAP_CONC,
    KEY_SD_TS_VCAP_REINF,
    KEY_SD_TS_VRD,
    KEY_SD_CRACK_AS_MIN,
    KEY_SD_CRACK_AS_PROV,
)
from osdagbridge.core.utils.codes.keyfile import (
    DCR_PASS_THRESHOLD,
    DCR_FAIL_THRESHOLD,
)
from osdagbridge.core.utils.codes.is800_2007 import IS800_2007
from osdagbridge.core.utils.common import *

# IRC 22:2015 Cl.605.3 — fatigue strength at 5×10^6 cycles derived from IRC module defaults.
_fat_r = IRC22_2014.cl_605_3_fatigue_strength(5_000_000, "rolled")
_fat_w = IRC22_2014.cl_605_3_fatigue_strength(5_000_000, "welded")
FATIGUE_STRENGTH_ROLLED_MPA = _fat_r["ffn_MPa_used"]   # 118.0
FATIGUE_STRENGTH_WELDED_MPA = _fat_w["ffn_MPa_used"]   # 92.0
FATIGUE_SHEAR_STRENGTH_MPA  = _fat_r["tfn_MPa_used"]   # 59.0

def _req(value: Any, key: str, source: str) -> Any:
    """Validate that a required value is not None and not an empty string.

    Use this wherever a missing value should be a hard error rather than
    a silent fallback. Raises ValueError with a clear message identifying
    what is missing and where it was expected to come from.

    Args:
        value  : The value to check (typically from a dict .get() call).
        key    : The name of the field that is missing (used in the error message).
        source : Where the value was expected to come from (used in the error message).

    Returns:
        value  : The original value, unchanged, if it is not None or empty.

    Raises:
        ValueError : If value is None or an empty string.

    Examples:
        span = float(_req(inputs.get("span"), "span", "basic_inputs"))
        deck_t = float(_req(additional_inputs.get(KEY_TS_DECK_THICKNESS),
                            KEY_TS_DECK_THICKNESS, "additional_inputs"))
    """
    if value is None or value == "":
        raise ValueError(
            f"{key!r} is required but was not found in {source!r}. "
            f"Populate {key!r} before running the design check."
        )
    return value


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
    fck: float                                          # MPa — material DB (KEY_MATERIAL_DECK_FCK)
    fctm: float                                         # MPa — material DB (KEY_MATERIAL_DECK_FCTM)
    Ecm: float                                          # MPa — material DB (KEY_MATERIAL_DECK_ECM, stored GPa)
    # Reinforcement — grade from Design Options (KEY_DS_REINF_MATERIAL); fy is a property
    # of that grade, looked up from the material DB. Both required, no defaults.
    rebar_grade: str                                    # e.g. "Fe 415" / "Fe500"
    fy_rebar: float                                     # MPa — material DB lookup by grade

    # IRC 22:2015 Cl.602 Annex III — structural-steel elastic constants. Required, no defaults.
    Es: float                                           # MPa — from material props (steel_prop.E)
    Gs: float                                           # MPa — required input (KEY_MATERIAL_GIRDER_G, GPa)
    nu: float                                           # from material props (steel_prop.v)

    # IRC 22:2015 Cl.601.4 Table 1 — partial safety factors. Required (keyword-only);
    # always supplied from the Design Options (Cont.) inputs
    # (KEY_DO_GAMMA_M0 / _M1 / _V / _MF). No hardcoded defaults.
    gamma_m0: float = field(kw_only=True)
    gamma_m1: float = field(kw_only=True)
    gamma_v: float = field(kw_only=True)
    gamma_mft: float = field(kw_only=True)


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

    def __post_init__(self) -> None:
        # Steel-section equations live in the single source
        # initial_sizing.steel_i_section_properties(). The designer must only
        # *read* the computed values, never recompute them here — so a future
        # custom girder shape only changes its equations in one place. Computed
        # once at construction; the section dimensions are never mutated after.
        props = steel_i_section_properties(
            D=self.D, bf_top=self.bf_top, tf_top=self.tf_top,
            bf_bot=self.bf_bot, tf_bot=self.tf_bot, tw=self.tw,
        )
        self.dw = props[KEY_MP_GIRDER_WEB_DEPTH]                  # web depth (mm)
        self.Af_top = props[KEY_MP_GIRDER_FLANGE_AREA_TOP]        # top-flange area (mm^2)
        self.Af_bot = props[KEY_MP_GIRDER_FLANGE_AREA_BOT]        # bottom-flange area (mm^2)
        self.Aw = props[KEY_MP_GIRDER_WEB_AREA]                   # web area (mm^2)
        self.A_steel = props[KEY_MP_GIRDER_SECTIONAL_AREA]        # total steel area (mm^2)
        self.y_cg_from_bot = props[KEY_MP_GIRDER_CENTROID_YCG]    # centroid from bottom fibre (mm)
        self.Iz_steel = props[KEY_MP_GIRDER_SECTIONAL_IZ]         # strong-axis second moment (mm^4)
        self.Zp_steel = props[KEY_MP_GIRDER_PLASTIC_MODULUS_ZUZ]  # plastic section modulus (mm^3)
        self.Ze_steel = props[KEY_MP_GIRDER_ELASTIC_MODULUS_ZZ]   # elastic section modulus (mm^3)
        # Section label built from the mm dimensions (a formatted string, not a
        # unit-agnostic number, so it is not part of the keyed property output).
        self.designation = (                                     # "D x bf_top x tf_top x bf_bot x tf_bot"
            f"{self.D:.0f} x {self.bf_top:.0f} x {self.tf_top:.0f}"
            f" x {self.bf_bot:.0f} x {self.tf_bot:.0f}"
        )


@dataclass
class SlabProperties:
    # Concrete deck slab dimensions and reinforcement (all in mm). Covers per IRC 112-2020 durability table.
    thickness: float
    haunch_depth: float = 0.0
    rebar_area_top: float = 0.0
    rebar_area_bot: float = 0.0
    # Bottom clear cover — required (keyword-only); wired from the Design Options input
    # KEY_DS_BOTTOM_CLEAR_COVER. No hardcoded default.
    cover_bot: float = field(kw_only=True)


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
    cross_bracing_spacing_m: float = DEFAULT_CROSS_BRACING_SPACING



@dataclass
class ShearStudConfig:
    # Headed stud connector (IRC 22:2015 Cl.606). fu ≤ 500 MPa per Cl.606.3.1 recommendation.
    # All fields are required (no defaults): every value is wired from its Additional Inputs
    diameter: float
    height: float
    fu: float
    fy: float
    n_per_section: int
    transverse_spacing: float   # s_ts (mm) — c/c transverse spacing of studs


@dataclass
class FatigueConfig:
    Nsc: int
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
    # Required (keyword-only, no default): wired from KEY_MP_STIFFENER_DESIGN_METHOD via
    # _req() in from_plate_girder_bridge(). "post_critical" | "tension_field". Manual/guidance
    # constructions (no user input) must pass it explicitly — no silent fallback.
    shear_method: str = field(kw_only=True)
    Nf_kN: float = 0.0          # axial force per flange for tension field (0 = ignore)
    c_end_mm: float = 0.0       # end panel width from support (0 = use c_mm)

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
    studs: ShearStudConfig
    fatigue: FatigueConfig
    stiffener: Optional[StiffenerConfig] = None            # None = stiffener checks skipped

    @classmethod
    def from_plate_girder_bridge(cls, bridge: Any, girder_index: int | None = None) -> "BridgeConfig":
        # Build a BridgeConfig from a solved PlateGirderBridge: materials from the project DB
        # (which mirrors IS 2062 / IRC 22 Annex III); concrete fck/fctm/Ecm and rebar fy read
        # from the resolved material-input keys.
        from osdagbridge.core.utils.common import (
            KEY_GIRDER, KEY_DECK_CONCRETE_GRADE_BASIC, KEY_TS_DECK_THICKNESS,
            KEY_SPAN, KEY_CARRIAGEWAY_WIDTH, KEY_MP_CB_SPACING,
            KEY_MP_GIRDER_DEPTH, KEY_MP_GIRDER_TOP_FLANGE_WIDTH, KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
            KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH, KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
            KEY_MP_GIRDER_WEB_THICKNESS,
            KEY_MATERIAL_DECK_FCK, KEY_MATERIAL_DECK_FCTM, KEY_MATERIAL_DECK_ECM,
        )

        if not getattr(bridge, "material_props", None):
            raise AttributeError(
                "bridge.material_props is not set. "
                "Run the material resolution step before calling from_plate_girder_bridge()."
            )

        steel_prop = bridge.material_props.steel_prop
        fy_struct = steel_prop.Fy / 1_000_000.0
        if not steel_prop.Fu:
            raise ValueError(
                f"Fu (ultimate strength) is not set for grade "
                f"{bridge.basic_inputs.get(KEY_GIRDER)!r}. Populate Fu in the material "
                "database before running the design check."
            )
        fu_struct = steel_prop.Fu / 1_000_000.0

        # Structural-steel elastic constants come from the resolved material props
        # (steel_prop) — the same trusted source already used for Fy/Fu above.
        # Es is stored in Pa; convert to MPa. All are hard errors if missing.
        if not steel_prop.E:
            raise ValueError(
                f"Es (modulus of elasticity) is not set for grade "
                f"{bridge.basic_inputs.get(KEY_GIRDER)!r}. Populate it in the material "
                "database before running the design check."
            )
        if steel_prop.v in (None, ""):
            raise ValueError(
                f"Poisson's ratio is not set for grade "
                f"{bridge.basic_inputs.get(KEY_GIRDER)!r}. Populate it in the material "
                "database before running the design check."
            )
        Es_MPa = steel_prop.E / 1_000_000.0
        nu = float(steel_prop.v)
        # Gs (shear modulus) is a required user/DB input (KEY_MATERIAL_GIRDER_G, stored GPa).
        raw_g = bridge.input_dict.get(KEY_MATERIAL_GIRDER_G)
        if raw_g in (None, ""):
            raise ValueError(
                f"Gs (shear modulus) is not set for grade "
                f"{bridge.basic_inputs.get(KEY_GIRDER)!r}. Populate it in the material "
                "database before running the design check."
            )
        Gs_MPa = float(raw_g) * 1000.0                  # GPa → MPa

        # Reinforcement grade comes from the Design Options dialog (required). Its yield
        # strength is a property of that grade, looked up from the material DB — never an
        # input on its own. A grade missing from the DB is a hard error.
        rebar_grade = str(_req(bridge.additional_inputs.get(KEY_DS_REINF_MATERIAL),
                        KEY_DS_REINF_MATERIAL, "additional_inputs")).strip()
        fy_rebar = bridge._lookup_material(rebar_grade, "fy")
        if fy_rebar is None:
            raise ValueError(
                f"Rebar grade {rebar_grade!r} (from {KEY_DS_REINF_MATERIAL!r}) was not "
                "found in the material database. Select a valid reinforcement grade "
                "before running the design check."
            )

        # Concrete fck / fctm / Ecm come straight from the material inputs.
        fck = float(_req(bridge.input_dict.get(KEY_MATERIAL_DECK_FCK),
                    KEY_MATERIAL_DECK_FCK, "input_dict"))
        fctm = float(_req(bridge.input_dict.get(KEY_MATERIAL_DECK_FCTM),
                    KEY_MATERIAL_DECK_FCTM, "input_dict"))
        Ecm = float(_req(bridge.input_dict.get(KEY_MATERIAL_DECK_ECM),
                    KEY_MATERIAL_DECK_ECM, "input_dict")) * 1000.0     # GPa → MPa

        # Partial safety factors come from the Design Options (Cont.) dialog and are
        # required — a missing/blank value is a hard error, never a silent fallback.
        material = SteelProperties(
            steel_grade=str(_req(bridge.basic_inputs.get(KEY_GIRDER),
                     KEY_GIRDER, "basic_inputs")),
            fy=fy_struct,
            fu=fu_struct,
            concrete_grade=str(_req(bridge.basic_inputs.get(KEY_DECK_CONCRETE_GRADE_BASIC),
                        KEY_DECK_CONCRETE_GRADE_BASIC, "basic_inputs")),
            fck=fck,
            fctm=fctm,
            Ecm=Ecm,
            rebar_grade=rebar_grade,
            fy_rebar=float(fy_rebar),
            Es=Es_MPa,
            Gs=Gs_MPa,
            nu=nu,
            gamma_m0=float(_req(bridge.additional_inputs.get(KEY_DO_GAMMA_M0),
                        KEY_DO_GAMMA_M0, "additional_inputs")),
            gamma_m1=float(_req(bridge.additional_inputs.get(KEY_DO_GAMMA_M1),
                        KEY_DO_GAMMA_M1, "additional_inputs")),
            gamma_v=float(_req(bridge.additional_inputs.get(KEY_DO_GAMMA_V),
                        KEY_DO_GAMMA_V, "additional_inputs")),
            gamma_mft=float(_req(bridge.additional_inputs.get(KEY_DO_GAMMA_MF),
                        KEY_DO_GAMMA_MF, "additional_inputs")),
        )

        inp = bridge.input_dict
        # Girder geometry is read through resolve_girder_value so it works whether
        # the dict carries per-girder dynamic keys or legacy scalar keys. Pass
        # girder_index to build a config for that specific girder; None (default)
        # falls back to the representative (first) girder — see resolve_girder_value().
        from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import (
            resolve_girder_value as _gv,
        )
        section = SteelSection(
            D=_gv(inp, KEY_MP_GIRDER_DEPTH, girder_index)                   * 1000,
            bf_top=_gv(inp, KEY_MP_GIRDER_TOP_FLANGE_WIDTH, girder_index)        * 1000,
            tf_top=_gv(inp, KEY_MP_GIRDER_TOP_FLANGE_THICKNESS, girder_index)    * 1000,
            bf_bot=_gv(inp, KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH, girder_index)     * 1000,
            tf_bot=_gv(inp, KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS, girder_index) * 1000,
            tw=_gv(inp, KEY_MP_GIRDER_WEB_THICKNESS, girder_index)               * 1000,
        )

        geom = bridge.grillage_geometry
        deck = bridge.deck_layout

        # AFTER
        if geom is None:
            raise AttributeError(
                "bridge.grillage_geometry is not set. "
                "Run grillage geometry setup before calling from_plate_girder_bridge()."
            )
        span = geom.L
        beam_spacing = geom.ext_to_int_dist
        # AFTER
        if deck is None:
            raise AttributeError(
                "bridge.deck_layout is not set. "
                "Run deck layout setup before calling from_plate_girder_bridge()."
            )
        carriageway = deck.carriageway_width
        n_girders = geom.n_l
        edge_dist = geom.edge_dist

        # Cross-bracing spacing drives the lateral unbraced length for LTB.
        cb_spacing = float(bridge.additional_inputs.get(KEY_MP_CB_SPACING) or
                                DEFAULT_CROSS_BRACING_SPACING)

        # beam_type (Cl.603.2.1 effective width) is a girder *position* property, not a user
        # input: the two outermost main girders are exterior ("outer"), the rest interior
        # ("inner"). Derived from this girder's index among the main girders — _girder_count()
        # excludes the overhang edge beams that geom.n_l counts. girder_index=None builds the
        # representative (interior) config.
        n_main_girders = bridge._girder_count()
        if girder_index is not None and girder_index in (0, n_main_girders - 1):
            beam_type = "outer"
        else:
            beam_type = "inner"

        # support_type is derived from the support-condition inputs (required). A pinned +
        # roller pair is the classic simply-supported case; any other pair is reported verbatim.
        left_support = str(_req(bridge.additional_inputs.get(KEY_SC_LEFT_SUPPORT),
                        KEY_SC_LEFT_SUPPORT, "additional_inputs")).strip()
        right_support = str(_req(bridge.additional_inputs.get(KEY_SC_RIGHT_SUPPORT),
                        KEY_SC_RIGHT_SUPPORT, "additional_inputs")).strip()
        if {left_support.lower(), right_support.lower()} == {"pinned", "roller"}:
            support_type = "simply_supported"
        else:
            support_type = f"{left_support}-{right_support}".lower().replace(" ", "_")

        geometry = GeometryConfig(
            span=float(span),
            beam_spacing=float(beam_spacing),
            carriageway_width=float(carriageway),
            n_girders=int(n_girders),
            edge_distance=float(edge_dist),
            beam_type=beam_type,
            support_type=support_type,
            cross_bracing_spacing_m=cb_spacing,
        )



        # Deck thickness and bottom clear cover both live in the Additional Inputs dialog
        # and are required — a missing value is a hard error, never a silent fallback.
        deck_t = _req(bridge.additional_inputs.get(KEY_TS_DECK_THICKNESS),
                    KEY_TS_DECK_THICKNESS, "additional_inputs")
        cover_bot = _req(bridge.additional_inputs.get(KEY_DS_BOTTOM_CLEAR_COVER),
                    KEY_DS_BOTTOM_CLEAR_COVER, "additional_inputs")
        slab = SlabProperties(thickness=float(deck_t), cover_bot=float(cover_bot))

        # Shear stud parameters — read from Additional Inputs (IRC 22:2015 Cl.606).
        # All fields are seeded by _update_design_options_defaults() and are required:
        # a missing value is a hard error, never a silent fallback.
        ai = bridge.additional_inputs
        stud_d  = float(_req(ai.get(KEY_DS_STUD_DIAMETER),
                             KEY_DS_STUD_DIAMETER, "additional_inputs"))
        stud_h  = float(_req(ai.get(KEY_DS_STUD_HEIGHT),
                             KEY_DS_STUD_HEIGHT, "additional_inputs"))
        stud_fu = float(_req(ai.get(KEY_DS_STUD_ULTIMATE_STRENGTH),
                             KEY_DS_STUD_ULTIMATE_STRENGTH, "additional_inputs"))
        stud_fy = float(_req(ai.get(KEY_DS_STUD_YIELD_STRENGTH),
                             KEY_DS_STUD_YIELD_STRENGTH, "additional_inputs"))
        stud_n  = int(float(_req(ai.get(KEY_DS_STUD_COUNT),
                                 KEY_DS_STUD_COUNT, "additional_inputs")))
        stud_ts = float(_req(ai.get(KEY_DS_STUD_TRANSVERSE_SPACING),
                             KEY_DS_STUD_TRANSVERSE_SPACING, "additional_inputs"))
        studs = ShearStudConfig(diameter=stud_d, height=stud_h, fu=stud_fu, fy=stud_fy,
                                n_per_section=stud_n, transverse_spacing=stud_ts)

        # Fatigue design cycles Nsc — read from Design Options (Cont.) (KEY_DO_LOAD_CYCLES).
        # Required: a missing value is a hard error, never a silent fallback. ffn/tfn keep
        # their code-derived (Cl.605.3) defaults.
        fatigue = FatigueConfig(
            Nsc=int(float(_req(ai.get(KEY_DO_LOAD_CYCLES),
                               KEY_DO_LOAD_CYCLES, "additional_inputs"))),
        )

        # Stiffener parameters — all optional. When plate dimensions are not given (default 0.0),
        # compute_intermediate_stiffener() and compute_bearing_stiffener() run in guidance mode,
        # returning required sizing instead of verification. bs_R_kN=0 means: resolve from
        # max(Vu) in run_design_check().
        def _member_value(key):
            # Stiffener fields (bearing + intermediate) are stored per-member as
            # "<key>.G{n}.M{m}", not under the bare base key. Prefer this girder's
            # own value (when girder_index is given), then the legacy scalar key,
            # then G1's value, then any available girder/member value as a last resort.
            # Returns the raw value (or None).
            v = None
            if girder_index is not None:
                v = ai.get(f"{key}.G{girder_index + 1}.M1")
            if v is None:
                v = ai.get(key)
            if v is None:
                v = ai.get(f"{key}.G1.M1")
            if v is None:
                for k in ai:
                    if k.startswith(key + ".G"):
                        v = ai[k]
                        break
            return v

        def _optfloat(key, default=0.0):
            # Soft per-member float lookup for optional stiffener plate dims
            # (guidance mode when absent). Resolution order: see _member_value.
            v = _member_value(key)
            if v is None or str(v).strip() in ("", "NA", "None"):
                return default
            try:
                return float(v)
            except (TypeError, ValueError):
                return default

        # Shear-buckling design method — required (KEY_MP_STIFFENER_DESIGN_METHOD, stored
        # per-member like the other stiffener fields, always seeded by defaults). A missing
        # value is a hard error. The UI stores VALUES_STIFFENER_DESIGN strings; map them to
        # the internal token consumed by compute_shear_buckling().
        _design_method = str(_req(_member_value(KEY_MP_STIFFENER_DESIGN_METHOD),
                                  KEY_MP_STIFFENER_DESIGN_METHOD, "additional_inputs")).strip()
        _shear_method_map = {
            "Simple Post Critical": "post_critical",
            "Tension Field":        "tension_field",
        }
        shear_method = _shear_method_map.get(_design_method)
        if shear_method is None:
            raise ValueError(
                f"{KEY_MP_STIFFENER_DESIGN_METHOD!r} has unrecognised value {_design_method!r}; "
                f"expected one of {list(_shear_method_map)}."
            )

        stiffener = StiffenerConfig(
            c_mm        = _optfloat(KEY_MP_STIFFENER_INTERMEDIATE_SPACING),
            tq_mm       = _optfloat(KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS),
            H_mm        = _optfloat(KEY_MP_STIFFENER_INTERMEDIATE_OUTSTAND),
            n_sides     = int(_optfloat(KEY_MP_STIFFENER_NO_BEARING_STIFFENERS, 1)),
            shear_method= shear_method,
            bs_tq_mm    = _optfloat(KEY_MP_STIFFENER_BEARING_THICKNESS),
            bs_H_mm     = _optfloat(KEY_MP_STIFFENER_BEARING_OUTSTAND),
            bs_n_plates = int(_optfloat(KEY_MP_STIFFENER_NO_BEARING_STIFFENERS, 2)),
            bs_R_kN     = 0.0,
        )

        return cls(material=material, section=section, geometry=geometry,
                   slab=slab, studs=studs, fatigue=fatigue, stiffener=stiffener)

    def summary(self) -> str:
        s, g, m = self.section, self.geometry, self.material
        return (f"L={g.span}m | {m.steel_grade}/{m.concrete_grade} | "
                f"D={s.D}mm | {g.n_girders} girders @ {g.beam_spacing}m")


# ======================================================================
#  SECTION 2 -- DEMAND EXTRACTOR (Analyser Stage)
# ======================================================================


@dataclass
class DemandEnvelope:
    # Demand envelope at the critical section. Unit suffix is part of each name for clarity.
    #
    # Semantic fields (populated at envelope level from specific load combinations/cases):
    #   Mu_kNm            — ULS strong-axis moment (Mz) from ULS combinations
    #   Vu_kN             — ULS vertical shear (Fy) from ULS combinations
    #   Nu_kN             — ULS axial force (Fx) from ULS combinations
    #   M_construction_kNm — Mz from analyser's DL+LL case (SW+DC+DD+SIDL+LL at service)
    #   M_girder_sw_kNm   — Mz from girder self-weight only (construction stage 1, SW case)
    #   M_sls_kNm         — Mz from Envelope_SLS (analyser pre-combined SLS envelope)
    #   V_sls_kN          — Vy from Envelope_SLS
    #   delta_live_mm     — Dy (vertical displacement) from individual live-only LCs
    #   delta_total_mm    — Dy from analyser's DL+LL case (DL = SW+DC+DD+SIDL, not DW)
    #   stress_range_MPa  — Mz range (max−min) across all SLS_FREQUENT_* combinations / Ze
    #   shear_range_MPa   — Vy range (max−min) across all SLS_FREQUENT_* combinations / Aw
    #
    # Raw 9-component fields (populated per-LC; all 9 DOF components from grillage output):
    #   Mx_kNm — torsion about the longitudinal axis
    #   My_kNm — weak-axis bending moment
    #   Vz_kN  — transverse (out-of-plane) shear
    #   Dx_mm  — axial displacement
    #   Dy_mm  — vertical displacement
    #   Dz_mm  — transverse displacement
    Mu_kNm: float = 0.0
    Vu_kN: float = 0.0
    Nu_kN: float = 0.0
    # Raw per-LC components (grillage output; all 9 DOFs stored without semantic reinterpretation)
    Mx_kNm: float = 0.0           # torsion about longitudinal axis
    My_kNm: float = 0.0           # weak-axis bending moment
    Vz_kN: float = 0.0            # transverse (out-of-plane) shear
    Dx_mm: float = 0.0            # axial displacement
    Dy_mm: float = 0.0            # vertical displacement
    Dz_mm: float = 0.0            # transverse displacement
    # Semantic envelope fields
    M_construction_kNm: float = 0.0
    delta_live_mm: float = 0.0
    delta_total_mm: float = 0.0
    stress_range_MPa: float = 0.0
    shear_range_MPa: float = 0.0
    Nsc: int = field(kw_only=True)
    governing_combination: str = "ULS Combination I"
    location: str = "midspan"
    member: str = ""
    source: str = "manual"
    M_sls_kNm: float = 0.0
    V_sls_kN: float = 0.0
    Vr_kN: float = 0.0                                    # Cl.606.4.2 — LL shear range (Vmax_LL - Vmin_LL)
    M_girder_sw_kNm: float = 0.0                          # Construction stage 1: girder self-weight only (bare steel)
    # LC type — governs which checks are applicable (see DCREngine._*_TYPES sets).
    # "" = aggregate envelope (all applicable checks run); typed = per-LC run with scoped checks.
    # Values: "ULS" | "SLS_frequent" | "SLS" | "DL_LL" | "live_only" | "individual" | ""
    lc_type: str = ""


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
    NRd_kN: float = 0.0 
    Mb_kNm_stage1: float = 0.0
    lambda_LT_stage1: float = 0.0
    chi_LT_stage1: float = 0.0
    Ag_mm2: float = 0.0                                 # Gross steel area
    Av_mm2: float = 0.0                                 # Cl.603.3.3.2
    Vn_kN: float = 0.0
    Vd_kN: float = 0.0
    Kv: float = 0.0                                     # Cl.603.3.3.2 post-critical — shear buckling coeff
    lambda_w: float = 0.0                               # web slenderness
    tau_b_buck_MPa: float = 0.0                         # design shear stress from buckling
    Vcr_kN: float = 0.0                                 # governing shear resistance (post-critical or TF)
    shear_method: str = "post_critical"                 # "post_critical" | "tension_field"
    Vtf_kN: float = 0.0                                 # tension field resistance (Cl.603.3.3.2(2)(b))
    phi_tf_deg: float = 0.0                             # tension field angle (deg)
    Mdv_kNm: float = 0.0                                # Cl.603.3.3.3
    beta_interaction: float = 0.0
    mn_axial_term: float = 0.0                          # Cl.603.3.3.3 M-N: Nu/NRd
    mn_moment_term: float = 0.0                         # Cl.603.3.3.3 M-N: Mu/Mdv
    mn_ratio: float = 0.0                               # Cl.603.3.3.3 M-N: Nu/NRd + Mu/Mdv
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
    is_Fq_kN: float = 0.0              # Cl.509.7.2.5 — demand = max(V − Vcr_pc, 0)

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
        # cl_602 wrapper returns [section_class, b/t ratio, class_limit]
        flange_class = flange_result[0]
        flange_limit = flange_result[2]
        b_tf = b_outstanding / sec.tf_top

        # Web class limit — pick the limit for the achieved web class from the
        # values the irc22 web classification already returns (no new constants).
        web_limit = {
            "Plastic":      web_res["plastic_limit"],
            "Compact":      web_res["compact_limit"],
            "Semi-Compact": web_res["semi_compact_limit"],
            "Slender":      web_res["semi_compact_limit"],
        }.get(web_class, web_res["semi_compact_limit"])

        class_order = {"Plastic": 1, "Compact": 2, "Semi-Compact": 3, "Slender": 4}
        governing = max(web_class, flange_class, key=lambda c: class_order.get(c, 4))

        return {
            "epsilon"        : round(web_res["epsilon"], 4),
            "d_tw_ratio"     : round(web_res["d_by_t"], 2),
            "b_tf_ratio"     : round(b_tf, 2),
            "web_limit"      : round(web_limit, 2),
            "flange_limit"   : round(flange_limit, 2),
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

    # IRC 22:2015 Cl.603.3.3.2 — shear buckling resistance (simple post-critical method).
    # c_mm_override: pass the decided panel spacing (from guidance or user input).
    # When None, falls back to config.stiffener.c_mm; if still absent, assumes support-only stiffeners.
    def compute_shear_buckling(self, Av_mm2: float, c_mm_override: float = None) -> dict:
        # c_mm_override is always set by compute_all() for both custom and optimised cases.
        # None → no intermediate stiffeners (support-only bearings), Kv = 5.35.
        c_mm = c_mm_override if (c_mm_override is not None and c_mm_override > 0) else None

        # Simple post-critical is always computed first:
        #   • It is the governing method when shear_method == "post_critical".
        #   • Its tau_b is a required input to the tension field calculation.
        #   • Its Vcr_pc is the correct Vcr for the stiffener force check (IS 800 Cl.8.7.2.5).
        res_pc = IRC22_2014.cl_603_3_3_2_shear_buckling_post_critical(
            Av_mm2=Av_mm2,
            fyw_MPa=self.mat.fy,
            d_mm=self.sec.dw,
            tw_mm=self.sec.tw,
            c_mm=c_mm,
            stiffeners_at_support_only=(c_mm is None),
        )

        result = {
            "Kv"          : res_pc["Kv"],
            "tau_cr_MPa"  : res_pc["tau_cr_MPa"],
            "lambda_w"    : res_pc["lambda_w"],
            "tau_b_MPa"   : res_pc["tau_b_MPa"],
            "Vcr_pc_kN"   : res_pc["Vrd_kN"],   # post-critical only (for stiffener Fq)
            "Vcr_kN"      : res_pc["Vrd_kN"],   # governing — overwritten below if TF
            "shear_method": "post_critical",
            "c_mm"        : c_mm if c_mm is not None else 0.0,
            "clause"      : res_pc["clause"],
            "source"      : "IRC22_2014",
        }

        method = (self.cfg.stiffener.shear_method
                  if self.cfg.stiffener is not None else "post_critical")

        if method == "tension_field" and c_mm is not None:
            # Tension field requires intermediate stiffeners — not valid without c_mm.
            Nf_N = self.cfg.stiffener.Nf_kN * 1e3
            res_tf = IRC22_2014.cl_603_3_3_2_tension_field_method(
                c_mm=c_mm,
                d_mm=self.sec.dw,
                tw_mm=self.sec.tw,
                fyw_MPa=self.mat.fy,
                bf_top_mm=self.sec.bf_top,
                tf_top_mm=self.sec.tf_top,
                bf_bot_mm=self.sec.bf_bot,
                tf_bot_mm=self.sec.tf_bot,
                fyf_MPa=self.mat.fy,
                Nf_N=Nf_N,
                Av_mm2=Av_mm2,
                tau_b_MPa=res_pc["tau_b_MPa"],
            )
            result["shear_method"]  = "tension_field"
            result["Vtf_kN"]        = res_tf["Vtf_kN"]
            result["phi_tf_deg"]    = res_tf["phi_deg"]
            result["Vcr_kN"]        = res_tf["Vtf_kN"]   # governing = TF resistance
            result["tension_field"] = res_tf
            result["clause"]        = res_tf["clause"]

        return result

    def compute_end_panel(self, Av_mm2: float, c_end_mm: float, V_kN: float) -> dict:
        """IS 800:2007 Cl.8.5.1 — End panel check when tension field method is used.

        The panel adjacent to a support must be designed using the simple post-critical
        method only (no tension field allowed in the end panel). Two conditions must hold:
          1. c_end ≤ d  (IS 800 Cl.8.5.2 — end panel must be stocky enough to anchor TF)
          2. Vcr_end ≥ V_Ed  (end panel carries the full applied shear without TF contribution)
        """
        d = self.sec.dw
        c_limit_ok = c_end_mm <= d

        res_ep = IRC22_2014.cl_603_3_3_2_shear_buckling_post_critical(
            Av_mm2=Av_mm2,
            fyw_MPa=self.mat.fy,
            d_mm=d,
            tw_mm=self.sec.tw,
            c_mm=c_end_mm,
            stiffeners_at_support_only=False,
        )
        Vcr_end_kN = res_ep["Vrd_kN"]

        return {
            "c_end_mm"   : round(c_end_mm, 1),
            "d_mm"       : round(d, 1),
            "c_limit_ok" : c_limit_ok,         # c_end ≤ d per IS 800 Cl.8.5.2
            "Kv_end"     : res_ep["Kv"],
            "lambda_w_end": res_ep["lambda_w"],
            "tau_b_end_MPa": res_ep["tau_b_MPa"],
            "Vcr_end_kN" : Vcr_end_kN,
            "V_kN"       : round(V_kN, 2),
            "check_ok"   : c_limit_ok and (Vcr_end_kN >= V_kN),
            "clause"     : "IS 800:2007 Cl.8.5.1",
            "source"     : "IRC22_2014",
        }

    # IRC 22:2015 Cl.603.3.3.1 — lateral-torsional buckling resistance at construction stage.
    def compute_buckling_resistance(self, beff_mm: float, section_class: str = "",
                                    LLT_mm_override: float = None) -> dict:
        # Section properties required by the IRC22 clause method.
        sec = self.sec
        mat = self.mat
        # Stage 1 (girder only): caller passes full span as override.
        # Stage 2 (cross-bracings in place): use cross-bracing spacing (default).
        # AFTER
        if LLT_mm_override is None:
            raise ValueError(
                "LLT_mm_override must be supplied to compute_buckling_resistance(). "
                "Pass the lateral unbraced length in mm explicitly."
            )
        LLT_mm = LLT_mm_override

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

        # AFTER
        if not section_class:
            raise ValueError(
                "section_class must be supplied to compute_buckling_resistance(). "
                "Call classify_section() first and pass the governing_class."
            )

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
        I_comp     = short[KEY_COMP_I]
        y_top      = short[KEY_COMP_Y_TOP]      # from top of slab to composite NA (compression arm)
        y_bot      = short[KEY_COMP_Y_BOT]      # from composite NA to bottom of steel (tension arm)
        y_comp_bot = short[KEY_COMP_Y_FROM_BOT]

        M_Nmm = M_sls_kNm * 1e6
        V_N   = V_sls_kN  * 1e3
        n_ratio = short[KEY_COMP_N]     # short-term modular ratio Es/Ecm

        # ── Concrete compressive stress at top of slab ────────────────────────
        # I_comp is the steel-equivalent (transformed) section; divide by n to
        # convert the fictitious steel stress at the slab top to actual concrete stress.
        sigma_c = M_Nmm * y_top / (n_ratio * I_comp)

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
            KEY_COMP_I           : round(I_comp, 0),
            KEY_COMP_Y_TOP       : round(y_top, 2),
            KEY_COMP_Y_BOT       : round(y_bot, 2),
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
            # Enable edge-distance computation: e = (b_tf - s_ts*(n_s-1) - d_s)/2
            b_tf_mm=sec.bf_top,
            s_ts_mm=stud.transverse_spacing,
            n_s=stud.n_per_section,
        )
        return {
            "stud_diameter_check"      : res["stud_diameter_check"],
            "stud_diameter_limit_mm"   : res["stud_diameter_limit_mm"],
            "stud_height_check"        : res["stud_height_check"],
            "required_min_height_mm"   : res["required_min_height_mm"],
            "stud_head_check"          : res.get("stud_head_check"),
            "edge_distance_check"      : res.get("edge_distance_check"),
            "edge_distance_mm"         : res.get("edge_distance_mm") or res.get("edge_distance_calculated_mm"),
            "required_edge_distance_mm": res["required_edge_distance_mm"],
            "projection_check"         : res.get("projection_check"),
            "clear_cover_check"        : res.get("clear_cover_check"),
            "clear_cover_stud_mm"      : res.get("clear_cover_stud_mm") or res.get("clear_cover_calculated_mm"),
            "required_clear_cover_mm"  : res["required_clear_cover_mm"],
            "all_ok"                   : res["all_requirements_satisfied"],
            "clause"                   : res["clause"],
            "source"                   : "IRC22_2014",
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
            # If c_req/d ≥ √2 the simpler formula 0.75·d·tw³ governs (MI check passes for any c).
            # Use the threshold spacing (√2·d) so shear buckling gets a real c rather than
            # falling back to stiffeners_at_support_only=True.
            if c_req > 0 and (c_req / d) >= math.sqrt(2.0):
                c_req = math.sqrt(2.0) * d
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
        # IS 800 Cl.8.7.2.5: Fq = V − Vcr (no γm0 on demand side; γm0 is already in fcd/Fqd).
        Fq_kN  = max(cfg.V_kN - cfg.Vcr_kN, 0.0)

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
        n_plates = cfg.bs_n_plates

        # Physical outstand limit (same formula as intermediate stiffener)
        H_max = (min(sec.bf_top, sec.bf_bot) - tw) / 2.0

        # Outstand defaults to the physical limit H_max = (bf − tw)/2 when the
        # user has not provided one (optimized design), so the full verification
        # still runs instead of falling back to guidance-only sizing.
        full_check = cfg.bs_tq_mm > 0

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
        H  = cfg.bs_H_mm if cfg.bs_H_mm > 0 else H_max     # default outstand → (bf − tw)/2

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
        results.Ag_mm2 = self.sec.A_steel
        results.details["moment_capacity"] = moment

        # 4. Shear capacity
        shear = self.compute_shear_capacity()
        results.Av_mm2 = shear["Av_mm2"]
        results.Vn_kN = shear["Vn_kN"]
        results.Vd_kN = shear["Vd_kN"]
        results.details["shear_capacity"] = shear

        # 4b. Shear buckling resistance (Cl.603.3.3.2 post-critical, IS 800 Cl.8.4.2.2a)
        # c_mm for buckling is resolved here so the correct panel spacing is always used:
        #   • User supplied c_mm → use it directly.
        #   • No c_mm → run stiffener guidance first to obtain c_req_min_mm, store the
        #     guidance result early, then use c_req for buckling. Step 18 will re-run
        #     (guidance mode again) and overwrite with the same result — no harm done.
        _c_mm_buck: float = 0.0
        if self.cfg.stiffener is not None:
            if self.cfg.stiffener.c_mm > 0:
                _c_mm_buck = self.cfg.stiffener.c_mm
            else:
                _is_guid = self.compute_intermediate_stiffener()
                results.details["intermediate_stiffener"] = _is_guid
                _c_mm_buck = _is_guid.get("c_req_min_mm", 0.0)

        shear_buck = self.compute_shear_buckling(results.Av_mm2,
                                                  c_mm_override=_c_mm_buck or None)
        results.Kv             = shear_buck["Kv"]
        results.lambda_w       = shear_buck["lambda_w"]
        results.tau_b_buck_MPa = shear_buck["tau_b_MPa"]
        results.Vcr_kN         = shear_buck["Vcr_kN"]      # governing (TF or PC)
        results.shear_method   = shear_buck["shear_method"]
        results.Vtf_kN         = shear_buck.get("Vtf_kN", 0.0)
        results.phi_tf_deg     = shear_buck.get("phi_tf_deg", 0.0)
        results.details["shear_buckling"] = shear_buck
        # Auto-populate stiffener Vcr with the POST-CRITICAL value — IS 800 Cl.8.7.2.5
        # uses Vcr from buckling (not the tension field resistance) for the stiffener force.
        if self.cfg.stiffener is not None and self.cfg.stiffener.Vcr_kN == 0.0:
            self.cfg.stiffener.Vcr_kN = shear_buck["Vcr_pc_kN"]

        # 4d. Axial resistance for M-N interaction (Cl.603.3.3.3)
        _fyw  = shear["fyw_MPa"]
        _gm0  = self.mat.gamma_m0
        results.NRd_kN = self.sec.A_steel * _fyw / _gm0 / 1e3

        # 5. LTB buckling resistance — Stage 2: cross-bracings in place, LLT = cross-bracing spacing.
        # FIX
        ltb = self.compute_buckling_resistance(
            results.beff_mm,
            section_class=sec_class["governing_class"],
            LLT_mm_override=min(self.geo.cross_bracing_spacing_m * 1000.0, self.geo.span * 1000.0),
        )
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
        results.I_comp_short_mm4 = short[KEY_COMP_I]
        results.y_top_comp_mm    = short[KEY_COMP_Y_TOP]
        results.y_bot_comp_mm    = short[KEY_COMP_Y_BOT]
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
        results.Qr_kN = stud_fat_cap.get("Qr_kN")
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

        # 15. Crack control (Cl.604.4) — moved to deck design (Stage 6)

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

        # 17. Transverse shear check (Cl.606.10) — moved to deck design (Stage 6), where the
        # slab reinforcement is sized. VL_N_per_mm (computed above) is consumed there;
        # design_results[KEY_SD_TS_*] are populated via PlateGirderBridge.design_deck_slab.

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

        # 20. End panel check (IS 800 Cl.8.5.1) — only when tension field method is used.
        # The end panel must carry the full applied shear by simple post-critical alone
        # and satisfy c_end ≤ d so it can anchor the tension field from the interior panel.
        if (self.cfg.stiffener is not None
                and self.cfg.stiffener.shear_method == "tension_field"
                and _c_mm_buck > 0):
            c_end = (self.cfg.stiffener.c_end_mm
                     if self.cfg.stiffener.c_end_mm > 0 else _c_mm_buck)
            ep_res = self.compute_end_panel(
                Av_mm2=results.Av_mm2,
                c_end_mm=c_end,
                V_kN=Vu_kN,
            )
            results.details["end_panel"] = ep_res

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
    governing_method: str = ""


class DCREngine:
    # Demand/Capacity ratio engine — PASS < DCR_PASS_THRESHOLD, WARN to DCR_FAIL_THRESHOLD, FAIL ≥.
    # Thresholds sourced from keyfile to avoid duplication.
    PASS_THRESHOLD = DCR_PASS_THRESHOLD
    FAIL_THRESHOLD = DCR_FAIL_THRESHOLD

    # lc_type sets used to gate check categories.
    # An empty lc_type ("") means aggregate envelope — all checks are applicable.
    _SLS_FREQUENT_TYPES = frozenset({"SLS_frequent"})
    _LIVE_ONLY_TYPES    = frozenset({"live_only"})
    _DL_LL_TYPES        = frozenset({"DL_LL"})

    CATEGORY_MAP: Dict[int, tuple] = {
    1 : (1, "Strength – Flexure"),
    2 : (2, "Strength – Shear"),
    3 : (3, "Interaction"),
    4 : (3, "Interaction"),
    5 : (4, "Lateral Torsional Buckling"),
    6 : (5, "Resistance to Longitudinal Shear"),
    7 : (5, "Resistance to Longitudinal Shear"),
    8 : (6, "Fatigue"),
    9 : (6, "Fatigue"),
    11: (7, "SLS Stress Limitation"),
    13: (8, "Deflection Check"),
    14: (8, "Deflection Check"),
    # Deck-only checks moved to deck design: concrete σc (10) + rebar stress (12),
    # crack control (15), transverse shear (16, 17). See PlateGirderBridge.design_deck_slab.
    # 20, 21 — stiffener: excluded from the 8-category aggregation
    }

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

    def _add_check(self, check_id, name, clause, demand, capacity, unit, note, governing_method=""):
        if capacity > 0:
            dcr = demand / capacity
            status = self.classify(dcr)
        else:
            dcr = 999.0
            status = "FAIL"

        result = CheckResult(
            check_id=check_id, name=name, clause=clause,
            demand=round(demand, 2), demand_unit=unit,
            capacity=round(capacity, 2), capacity_unit=unit,
            dcr=round(dcr, 4), status=status, note=note,  governing_method=governing_method,
        )
        self.checks.append(result)
        return result
    
    def category_urs(self) -> Dict[int, dict]:
        """Aggregate check-level DCRs into one governing entry per design category (1–8)."""
        from collections import defaultdict

        buckets: Dict[int, list] = defaultdict(list)
        for chk in self.checks:
            cat_entry = self.CATEGORY_MAP.get(chk.check_id)
            if cat_entry is None:
                continue
            cat_no, _ = cat_entry
            buckets[cat_no].append(chk)

        result: Dict[int, dict] = {}
        for cat_no in range(1, 9):
            rows = buckets.get(cat_no)
            if not rows:
                continue
            _, label = self.CATEGORY_MAP[rows[0].check_id]
            max_dcr  = max(c.dcr for c in rows)
            status   = self.classify(max_dcr)
            result[cat_no] = {
                "category_no": cat_no,
                "label"      : label,
                "max_dcr"    : round(max_dcr, 4),
                "status"     : status,
                "sub_checks" : [
                    {
                        "check_id"     : c.check_id,
                        "name"         : c.name,
                        "clause"       : c.clause,
                        "demand"       : c.demand,
                        "demand_unit"  : c.demand_unit,
                        "capacity"     : c.capacity,
                        "capacity_unit": c.capacity_unit,
                        "dcr"          : c.dcr,
                        "status"       : c.status,
                        "note"         : c.note,
                    }
                    for c in rows
                ],
            }
        return result

    # Run all IRC 22:2015 design checks — mapped to the 8 output-dock categories.    # ←── CHANGED
    def run_all_checks(self) -> List[CheckResult]:
        self.checks.clear()
        d, c = self.demand, self.capacity

        # Predicates for check gating based on lc_type.
        # An empty lc_type ("") = aggregate envelope → all checks applicable.
        # _is_sls is "service-level by elimination": every non-ULS, non-Envelope-ULS
        # combination — SLS/SLS_frequent, SW, DL, DD, DL_LL, live_only, individual, etc.
        t = d.lc_type
        _is_sls    = (not t) or (t != "ULS")
        _sls_freq  = (not t) or (t in self._SLS_FREQUENT_TYPES)
        _live_only = (not t) or (t in self._LIVE_ONLY_TYPES)
        _dl_ll     = (not t) or (t in self._DL_LL_TYPES)

        # ── CATEGORIES 1-3: Flexure / Shear / Interaction ─────────────────────
        # Intentionally ungated — run for every load case & combination, so the
        # per-LC table shows each LC's demand against the governing ULS capacity.

        # ── CATEGORY 1: Strength Limit State (Flexure) ───────────────────────
        self._add_check(1, "ULS Flexure", "Cl.603.3.1",
                         d.Mu_kNm, c.Md_kNm, "kNm",
                         note=f"PNA in {c.pna_location}, xu={c.xu_mm:.1f} mm")

        # ── CATEGORY 2: Strength Limit State (Shear) ─────────────────────────
        self._add_check(
            2,
            "ULS Shear",
            "Cl.603.3.3.2",
            d.Vu_kN,
            c.Vd_kN,
            "kN",
            note=f"Av={c.Av_mm2:.0f} mm²",
            governing_method=c.shear_method,
        )

        if c.Vcr_kN > 0:
            if c.shear_method == "tension_field":
                _buck_note = (f"Tension field: Vtf={c.Vtf_kN:.1f} kN, φ={c.phi_tf_deg:.1f}°; "
                              f"PC basis: Kv={c.Kv:.3f}, λw={c.lambda_w:.3f}, "
                              f"τb={c.tau_b_buck_MPa:.1f} MPa")
            else:
                _buck_note = (f"Simple post-critical: Kv={c.Kv:.3f}, "
                              f"λw={c.lambda_w:.3f}, τb={c.tau_b_buck_MPa:.1f} MPa")
            self._add_check(2, "ULS Shear Buckling", "Cl.603.3.3.2",
                             d.Vu_kN, c.Vcr_kN, "kN", note=_buck_note)

        # ── CATEGORY 3: Interaction ───────────────────────────────────────────
        # 3a. Moment–Shear interaction (Cl.603.3.3.3)
        effective_Md = c.Mdv_kNm if c.beta_interaction > 0 else c.Md_kNm
        self._add_check(3, "M-V Interaction", "Cl.603.3.3.3",
                         d.Mu_kNm, effective_Md, "kNm",
                         note=f"beta={c.beta_interaction:.4f}")

        # 3b. Moment–Axial interaction (Cl.603.3.3.3)
        # Uses the shear-reduced moment capacity (effective_Md) so that high shear is
        # accounted for consistently in both the M-V and M-N checks.
        # NRd is pre-computed by compute_all() as Ag × fyw / γm0.
        if d.Nu_kN > 0.0:
            if c.NRd_kN > 0.0 and effective_Md > 0.0:
                c.mn_axial_term  = d.Nu_kN / c.NRd_kN
                c.mn_moment_term = d.Mu_kNm / effective_Md
                interaction_ratio = c.mn_axial_term + c.mn_moment_term
                c.mn_ratio = interaction_ratio
                self._add_check(4, "M-N Interaction", "Cl.603.3.3.3",
                                 interaction_ratio, 1.0, "–",
                                 note=(f"Nu/NRd + Mu/Mdv = {interaction_ratio:.3f}"
                                       + (f" [Mdv={effective_Md:.1f} kNm, shear-reduced]"
                                          if c.beta_interaction > 0 else "")))

        # ── CATEGORY 4: Lateral Torsional Buckling ────────────────────────────
        # 4a. Construction Stage 1 — girder only, no cross-bracings, LLT = full span.
        if d.M_girder_sw_kNm > 0:
            # AFTER
            if c.Mb_kNm_stage1 <= 0:
                raise ValueError(
                    "Mb_kNm_stage1 is zero or not computed. "
                    "Ensure compute_all() has run the Stage 1 LTB check before calling run_all_checks()."
                )
            Mb_s1 = c.Mb_kNm_stage1
            ltb_s1 = c.details.get("buckling_resistance_stage1")
            if not ltb_s1:
                raise KeyError(
                    "'buckling_resistance_stage1' missing from capacity.details. "
                    "Ensure compute_all() has been run."
                )
            # AFTER
            for key in ("lambda_LT", "chi_LT", "LLT_mm"):
                if key not in ltb_s1:
                    raise KeyError(
                        f"'{key}' not found in buckling_resistance_stage1 details. "
                        "Ensure compute_all() has run the Stage 1 LTB check."
                    )
            lLT_s1 = ltb_s1["lambda_LT"]
            chi_s1 = ltb_s1["chi_LT"]
            LLT_s1 = ltb_s1["LLT_mm"]
            self._add_check(5, "LTB (Girder SW Only)", "Cl.603.3.3.1",
                             d.M_girder_sw_kNm, Mb_s1, "kNm",
                             note=(f"Stage 1: girder self-weight only, LLT=span={LLT_s1/1000:.1f}m; "
                                   f"λ_LT={lLT_s1:.4f}, χ_LT={chi_s1:.4f}"))

        # 4b. Construction Stage 2 — steel + wet concrete, cross-bracings in place, LLT = cb spacing.
        # Demand is the DL+LL combination only (mirrors Stage 1's SW-only gate above) — no ULS fallback.
        if d.M_construction_kNm > 0:
            ltb_s2 = c.details.get("buckling_resistance")
            if not ltb_s2:
                raise KeyError(
                    "'buckling_resistance' not found in capacity.details. "
                    "Ensure compute_all() has been run before calling run_all_checks()."
                )
            LLT_s2 = ltb_s2["LLT_mm"]
            self._add_check(5, "LTB (Construction Stage)", "Cl.603.3.3.1",
                             d.M_construction_kNm,
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
        det = c.details.get("stud_detailing")
        if not det:
            raise KeyError(
                "'stud_detailing' missing from capacity.details. "
                "Ensure compute_all() has been run."
            )
        self._add_check(7, "Stud Detailing", "Cl.606.6",
                         0.0 if c.stud_detailing_ok else 1.0, 1.0, "–",
                         note="d≤2tf, h≥max(4d,100), edge≥25, cover≥25")    

        # ── CATEGORY 6: Resistance to Fatigue ────────────────────────────────
        # Fatigue checks apply only under frequent SLS combinations (IRC 22 Cl.604.5).
        if _sls_freq and d.stress_range_MPa > 0 and c.f_fd_eff_MPa > 0:
            self._add_check(8, "Fatigue Normal Stress", "Cl.605",
                             d.stress_range_MPa, c.f_fd_eff_MPa, "MPa",
                             note=f"Nsc={d.Nsc:,}")

        if _sls_freq and d.shear_range_MPa > 0 and c.tau_fd_eff_MPa > 0:
            self._add_check(9, "Fatigue Shear Stress", "Cl.605",
                             d.shear_range_MPa, c.tau_fd_eff_MPa, "MPa",
                             note=f"Nsc={d.Nsc:,}")

        # ── CATEGORY 7: Stress Limitation (SLS) ──────────────────────────────
        # SLS stress checks apply to every service-level case (SLS / SLS_frequent / SW /
        # DL / DD / DL_LL / live_only / individual, etc.) — only ULS combinations are excluded.
        sls_act = c.details.get("sls_actual_stresses")
        if sls_act is None:
            raise KeyError(
                "'sls_actual_stresses' missing from capacity.details. "
                "Ensure compute_all() has been run."
            )
        # 7. Structural steel equivalent stress (Cl.604.3.1). Concrete σc (check 10) and
        # rebar stress (check 12) are deck-material checks — moved to deck design; their
        # values are still computed (in design_results) for the deck dialog to display.
        if _is_sls and not sls_act.get("skipped") and c.sigma_steel_equiv_MPa > 0.0:
            self._add_check(11, "SLS Steel Equiv. Stress", "Cl.604.3.1",
                             c.sigma_steel_equiv_MPa, c.sigma_s_limit_MPa, "MPa",
                             note=f"fe = √(fbc²+fp²+fbc·fp+3τ²) ≤ 0.9fy = {c.sigma_s_limit_MPa:.1f} MPa")

        # ── CATEGORY 8: Deflection and Crack Control ──────────────────────────
        # Live-load deflection: only for live-only individual LCs.
        if _live_only and d.delta_live_mm > 0:
            self._add_check(13, "SLS Deflection (Live)", "Cl.604.3.2",
                             d.delta_live_mm, c.defl_limit_live_mm, "mm",
                             note="Limit = L/800")

        # Total deflection: only for DL+LL combination (DL=SW+DC+SIDL, not DW).
        if _dl_ll and d.delta_total_mm > 0:
            self._add_check(14, "SLS Deflection (Total)", "Cl.604.3.2",
                             d.delta_total_mm, c.defl_limit_total_mm, "mm",
                             note="Limit = L/600")

        # Crack control (Cl.604.4) and transverse shear (Cl.606.10) are deck-only checks —
        # computed in deck design (Stage 6) and shown in the deck dialog, not in the steel
        # DCR cards. Their values live in design_results (KEY_SD_CRACK_* / KEY_SD_TS_*).

        # ── IRC 24-2010 STIFFENER CHECKS (Cl.509.7 / IS 800 Cl.8.7) ─────────────────
        # Intermediate transverse stiffener
        is_det = c.details.get("intermediate_stiffener", {"skipped": True})
        if is_det and not is_det.get("skipped"):
            if "design_guidance" not in is_det:
                raise KeyError("'design_guidance' key missing from intermediate_stiffener details.")
            if is_det["design_guidance"]:
                # No dimensions provided — report required values as a single guidance row
                for key in ("H_max_mm", "tq_req_1sided_mm", "tq_req_2sided_mm", "c_req_min_mm"):
                    if key not in is_det:
                        raise KeyError(f"'{key}' missing from intermediate_stiffener details.")
                _note = (f"H_max={(is_det['H_max_mm']):.0f} mm = (bf_min−tw)/2; "
                         f"tq_req(1-sided)≥{is_det['tq_req_1sided_mm']:.1f} mm, "
                         f"tq_req(2-sided)≥{is_det['tq_req_2sided_mm']:.1f} mm")
                if is_det["c_req_min_mm"] > 0:
                    _note += f"; c_req≥{is_det['c_req_min_mm']:.0f} mm (from Iys check)"
                self._add_check(20, "Int.Stiff: Sizing Required", "Cl.509.7.2.4",
                                 0.0, 1.0, "–", note=_note)
            else:
                # Full verification — three separate checks
                for key in ("H_mm", "H_limit_mm", "H_limit_type", "H_max_mm", "tq_req_provided_mm",
                           "Iys_min_mm4", "Iys_prov_mm4", "iys_formula", "Fq_kN", "Fqd_kN",
                           "fcd_MPa", "KL_r"):
                    if key not in is_det:
                        raise KeyError(f"'{key}' missing from intermediate_stiffener details.")
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
        bs_det = c.details.get("bearing_stiffener", {"skipped": True})
        if bs_det and not bs_det.get("skipped"):
            if "R_kN" not in bs_det:
                raise KeyError("'R_kN' missing from bearing_stiffener details.")
            R = bs_det["R_kN"]
            if "design_guidance" not in bs_det:
                raise KeyError("'design_guidance' key missing from bearing_stiffener details.")
            if bs_det["design_guidance"]:
                # No dimensions provided — report required tq as a single guidance row
                for key in ("H_max_mm", "tq_req_bearing_mm", "tq_req_leg_mm", "n_plates"):
                    if key not in bs_det:
                        raise KeyError(f"'{key}' missing from bearing_stiffener details.")
                self._add_check(21, "Brg.Stiff: Sizing Required", "Cl.509.7.3.3",
                                 0.0, 1.0, "–",
                                 note=(f"R={R:.1f} kN; H_max={bs_det['H_max_mm']:.0f} mm; "
                                       f"tq_req(bearing)≥{bs_det['tq_req_bearing_mm']:.1f} mm, "
                                       f"tq_req(leg)≥{bs_det['tq_req_leg_mm']:.1f} mm "
                                       f"(n_plates={bs_det['n_plates']})"))
            else:
                # Full verification — four separate checks
                for key in ("Fcdw_wb_kN", "fcc_wb_MPa", "A_wb_mm2", "Fcdw_lc_kN", "fcd_y_MPa",
                           "A_lc_mm2", "Fpsd_kN", "Aq_mm2", "tq_req_bearing_mm", "Fcd_kN",
                           "fcd_bs_MPa", "KL_r_bs"):
                    if key not in bs_det:
                        raise KeyError(f"'{key}' missing from bearing_stiffener details.")
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

    def _structural_checks(self) -> List[CheckResult]:
        """Checks belonging to the 8 design categories only (excludes stiffener check_ids 20/21)."""
        return [c for c in self.checks if c.check_id in self.CATEGORY_MAP]

    def overall_status(self) -> str:
        structural = self._structural_checks()
        if not structural:
            return "NO CHECKS RUN"
        if any(c.status == "FAIL" for c in structural):
            return "FAIL"
        if any(c.status == "WARN" for c in structural):
            return "WARN"
        return "PASS"

    def max_dcr(self) -> float:
        return max((c.dcr for c in self._structural_checks()), default=0.0)

    def critical_check(self) -> CheckResult:
        return max(self._structural_checks(), key=lambda c: c.dcr)

    def n_pass(self) -> int:
        return sum(1 for c in self._structural_checks() if c.status == "PASS")

    def n_warn(self) -> int:
        return sum(1 for c in self._structural_checks() if c.status == "WARN")

    def n_fail(self) -> int:
        return sum(1 for c in self._structural_checks() if c.status == "FAIL")


def design_envelope_engine(girder_names, per_girder):
    """Build the "Design Envelope" engine: per check id, keep the load case
    with the highest DCR (across all real load cases for a girder), then
    return the girder whose worst check governs.

    Reuses the per-LC check results already computed in run_design_check —
    no demand is re-synthesised. Because each per-LC engine only emits the
    checks its load case influences (gated by lc_type), taking the per-id
    maximum naturally yields "worst UR over the load cases that affect that
    check" for every one of the 8 categories.
    """
    best_engine = None
    best_max    = -1.0

    for g_name in girder_names:
        per_lc = per_girder.get(g_name, {}).get("per_lc", {})
        worst_by_id: dict[int, CheckResult] = {}
        for lc_res in per_lc.values():
            for chk in lc_res.get("checks", []):
                cid = chk.get("id")
                if cid is None:
                    continue
                dcr  = float(chk.get("dcr", 0.0) or 0.0)
                prev = worst_by_id.get(cid)
                if prev is None or dcr > prev.dcr:
                    worst_by_id[cid] = CheckResult(
                        check_id=cid,
                        name=chk.get("label", ""),
                        clause=chk.get("clause", ""),
                        demand=float(chk.get("demand", 0.0) or 0.0),
                        demand_unit="",
                        capacity=float(chk.get("capacity", 0.0) or 0.0),
                        capacity_unit="",
                        dcr=dcr,
                        status=chk.get("status", ""),
                        note=chk.get("note", ""),
                    )
        if not worst_by_id:
            continue

        # Synthetic engine — only .checks/.demand/.capacity are consumed by the
        # output-dock bars and the steel-design check tab, so skip __init__.
        engine = DCREngine.__new__(DCREngine)
        engine.demand   = None
        engine.capacity = None
        engine.checks   = list(worst_by_id.values())

        g_max = max(c.dcr for c in engine.checks)
        if g_max > best_max:
            best_max    = g_max
            best_engine = engine

    return best_engine


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
        sc = c.details.get("section_class")
        if not sc:
            raise KeyError(
                "'section class' missing from capacity.details. "
                "Ensure compute_all() has been run."
            )
        sls = c.details.get("sls_actual_stresses")
        if sls is None:
            raise KeyError(
                "'sls_actual_stresses=' missing from capacity.details. "
                "Ensure compute_all() has been run."
            )
        cmp = c.details.get("composite_section_props")
        if not cmp:
            raise KeyError(
                "composite_section_props not in capacity.details"
                "Ensure compute_all() has been run"
            )
        # Crack control now runs in deck design (Stage 6); absent here ⇒ skip its report lines.
        crack = c.details.get("crack_control")
        stud_lim = c.details.get("stud_spacing_limits")
        if not stud_lim:
            raise KeyError(
                "'stud_spacing_limits' missing from capacity.details. "
                "Ensure compute_all() has been run."
            )
        lines = [self._section_title("IRC 22:2015 CAPACITY COMPUTATIONS")]

        lines.append(f"\n  1. Effective Width (Cl.603.2.1)")
        lines.append(f"     beff = {c.beff_mm:.1f} mm")

        # Validate section_class keys
        for key in ('epsilon', 'web_class', 'd_tw_ratio', 'flange_class', 'b_tf_ratio', 'governing_class'):
            if key not in sc:
                raise KeyError(
                    f"'{key}' missing from section_class details. "
                    "Ensure compute_all() has been run."
                )
        lines.append(f"\n  2. Section Classification (Cl.603)")
        lines.append(f"     epsilon = {sc['epsilon']:.4f}")
        lines.append(f"     Web: {sc['web_class']}  (d/tw = {sc['d_tw_ratio']:.1f})")
        lines.append(f"     Flange: {sc['flange_class']}  (b/tf = {sc['b_tf_ratio']:.1f})")
        lines.append(f"     Governing: {sc['governing_class']}")

        lines.append(f"\n  3. Positive Moment Capacity (Cl.603.3.1)")
        lines.append(f"     PNA Location: {c.pna_location}")
        lines.append(f"     xu = {c.xu_mm:.2f} mm")
        lines.append(f"     Mp = Md = {c.Md_kNm:,.2f} kNm  (γm0 and γc embedded)")

        lines.append(f"\n  4. Plastic Shear Resistance (Cl.603.3.3.2)")
        lines.append(f"     Av = {c.Av_mm2:,.0f} mm²")
        lines.append(f"     Vn = {c.Vn_kN:,.2f} kN")
        lines.append(f"     Vd = {c.Vd_kN:,.2f} kN")

        lines.append(f"\n  4b. Shear Buckling Resistance (Cl.603.3.3.2 — Post-Critical)")
        lines.append(f"     Kv = {c.Kv:.3f}  |  λw = {c.lambda_w:.3f}")
        lines.append(f"     τb = {c.tau_b_buck_MPa:.2f} MPa  |  Vcr = {c.Vcr_kN:,.2f} kN")

        lines.append(f"\n  5. Buckling Resistance Moment (Cl.603.3.3.1)")
        lines.append(f"     Mcr = {c.Mcr_kNm:,.2f} kNm  |  λ_LT = {c.lambda_LT:.4f}  |  χ_LT = {c.chi_LT:.4f}")
        lines.append(f"     Mb = {c.Mb_kNm:,.2f} kNm")

        lines.append(f"\n  6. Bending–Shear Interaction (Cl.603.3.3.3)")
        lines.append(f"     beta = {c.beta_interaction:.4f}  |  Mdv = {c.Mdv_kNm:,.2f} kNm")

        # Composite section properties
        lines.append(f"\n  7. Composite Section Properties (Cl.604.3)")
        if cmp:
            for key in ('short_term', 'long_term'):
                if key not in cmp:
                    raise KeyError(
                        f"'{key}' missing from composite_section_props. "
                        "Ensure compute_all() has been run."
                    )
            st = cmp["short_term"]
            lt = cmp["long_term"]
            for subkey in (KEY_COMP_N, KEY_COMP_I, KEY_COMP_Y_TOP, KEY_COMP_Y_BOT):
                if subkey not in st:
                    raise KeyError(f"'{subkey}' missing from short_term composite properties.")
            if KEY_COMP_N not in lt or KEY_COMP_I not in lt:
                raise KeyError("'n' or 'I_comp_mm4' missing from long_term composite properties.")
            lines.append(f"     Short-term (n={st[KEY_COMP_N]}):  "
                         f"I = {st[KEY_COMP_I]:,.0f} mm⁴  |  "
                         f"y_top = {st[KEY_COMP_Y_TOP]:.1f} mm  |  y_bot = {st[KEY_COMP_Y_BOT]:.1f} mm")
            lines.append(f"     Long-term  (n={lt[KEY_COMP_N]}):  "
                         f"I = {lt[KEY_COMP_I]:,.0f} mm⁴")

        lines.append(f"\n  8. SLS Stress Limits (Cl.604.3.1)")
        lines.append(f"     Concrete limit   : σc  ≤ 0.48 fck = {c.sigma_c_limit_MPa:.1f} MPa")
        lines.append(f"     Steel equiv. limit: fe  ≤ 0.90 fy  = {c.sigma_s_limit_MPa:.1f} MPa")
        lines.append(f"     Rebar limit      : σr  ≤ 0.80 fyk = {c.sigma_rebar_limit_MPa:.1f} MPa")
        # Actual stresses
        if not sls.get("skipped"):
            lines.append(f"     --- Actual stresses (M_sls = {sls['M_sls_kNm']:.1f} kNm) ---")
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

        if crack:
            lines.append(f"\n  13. Crack Control — Min Reinforcement (Cl.604.4)")
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


def _extract_demands_from_analysis_results(
    analysis_results: PlateGirderAnalysisResults,
    config: BridgeConfig,
    result_data: dict | None = None,
) -> tuple:
    # Build per_girder_demands and per_girder_per_lc using the existing
    # pandas-based methods on PlateGirderAnalysisResults.
    # Returns (Dict[girder_name, DemandEnvelope], Dict[girder_name, Dict[lc, DemandEnvelope]])
    import numpy as np

    # result_data stores member ids as strings; the dataset selects on the int
    # element tags from ops.getEleTags(), so cast them back. "nodes" is only ever
    # used below as a selection set for max/abs, never as an ordered path.
    girders      = {
        name: {
            "elements": [int(m) for m in g.get("members", [])],
            "path":     g.get("nodes", []),
        }
        for name, g in result_data.get("girders").items()
    }
    lc_groups    = analysis_results.classify_loadcases()
    live_static  = lc_groups["vehicle_static"]
    all_live_lcs = live_static
    live_set     = set(str(lc) for lc in all_live_lcs)

    # Typed combination LCs from the analyser's classifier (empty list if key not present).
    # ULS: basic + seismic + accidental.  SLS: frequent + rare + quasi-permanent.
    _sls_frequent_lcs = list(lc_groups.get("sls_frequent",      lc_groups.get("SLS_frequent",      [])))
    _sls_rare_lcs     = list(lc_groups.get("sls_rare",          lc_groups.get("SLS_rare",          [])))
    _sls_quasi_lcs    = list(lc_groups.get("sls_quasi_permanent",lc_groups.get("SLS_quasi_permanent",[])))
    _sls_all_lcs      = _sls_frequent_lcs + _sls_rare_lcs + _sls_quasi_lcs
    _uls_basic_lcs    = list(lc_groups.get("uls_basic",         lc_groups.get("ULS_basic",         [])))
    _uls_seismic_lcs  = list(lc_groups.get("uls_seismic",       lc_groups.get("ULS_seismic",       [])))
    _uls_acc_lcs      = list(lc_groups.get("uls_accidental",    lc_groups.get("ULS_accidental",    [])))
    _uls_all_lcs      = _uls_basic_lcs + _uls_seismic_lcs + _uls_acc_lcs
    # Fatigue-vehicle cases (IRC:6 Cl.204.6) — the static "Fatigue" case plus every
    # increment of "Moving Fatigue ...". These drive the fatigue checks: the stress
    # range comes from the fatigue truck alone, not from the full Table 6A live-load
    # cases. Falls back to the live-load cases when the model carries no fatigue
    # truck (results produced before add_fatigue_vehicle_load_case() was wired in).
    _fatigue_lcs = list(lc_groups.get("fatigue", []))
    _fatigue_range_lcs = _fatigue_lcs or all_live_lcs
    # DL+LL combination case from analyser's create_dl_ll_combination(), e.g. "1.0 DL + 1.0 LL".
    _dl_ll_lcs = list(lc_groups.get("dl_ll", []))
    # Analyser-provided pre-combined envelopes (single load case each).
    _uls_env_lcs = list(lc_groups.get("envelope_uls", lc_groups.get("Envelope_ULS", [])))
    _sls_env_lcs = list(lc_groups.get("envelope_sls", lc_groups.get("Envelope_SLS", [])))
    # SW individual case for construction stage 1.
    _sw_lcs = list(lc_groups.get("sw", lc_groups.get("SW",
              lc_groups.get("girder_sw", lc_groups.get("self_weight", [])))))
    # "X.X DL" case from create_dead_load_combination() — SW+DC for construction stage 2 LTB.
    _dead_lcs    = list(lc_groups.get("dead", []))
    _dl_only_lcs = [lc for lc in _dead_lcs if str(lc).upper().endswith(" DL")]

    _uls_set          = set(str(lc) for lc in _uls_all_lcs)
    _sls_set          = set(str(lc) for lc in _sls_all_lcs)
    _sls_frequent_set = set(str(lc) for lc in _sls_frequent_lcs)
    _dl_ll_set        = set(str(lc) for lc in _dl_ll_lcs)
    _dl_only_set      = set(str(lc) for lc in _dl_only_lcs)

    # Single-LC handles used directly for demand extraction (None = case not available → skip).
    _uls_env_lc  = str(_uls_env_lcs[0])    if _uls_env_lcs    else None
    _sls_env_lc  = str(_sls_env_lcs[0])    if _sls_env_lcs    else None
    _dl_ll_lc    = str(_dl_ll_lcs[0])      if _dl_ll_lcs      else None
    _sw_lc       = str(_sw_lcs[0])         if _sw_lcs         else None
    _dl_only_lc  = str(_dl_only_lcs[0])    if _dl_only_lcs    else None

    def _lc_type(lc_str: str) -> str:
        """Classify a single LC string into a type tag for check scoping.
        Name-based rules take precedence over set membership so that any
        combination LC is correctly tagged regardless of how classify_loadcases
        grouped it.
        """
        n = lc_str.upper()
        # ULS combinations — BASIC_*, ACCIDENTAL_*, SEISMIC_*, or Envelope ULS
        if n.startswith(("BASIC_", "ACCIDENTAL_", "SEISMIC_")) or lc_str == "Envelope ULS":
            return "ULS"
        # SLS frequent — fatigue checks apply here
        if n.startswith("SLS_FREQUENT_"):
            return "SLS_frequent"
        # Any other SLS_ prefix (RARE, QP, OP, …) or Envelope SLS
        if n.startswith("SLS_") or lc_str == "Envelope SLS":
            return "SLS"
        # Fallback to set membership for user-named individual cases
        if lc_str in _dl_ll_set:   return "DL_LL"
        if lc_str in _dl_only_set: return "DL"
        if lc_str in live_set:     return "live_only"
        return "individual"

    # Composite stiffness ratio for SLS deflection correction

    sec, mat, slab, geo = config.section, config.material, config.slab, config.geometry
    beff_mm = min(geo.span * 1000.0 / 4.0, geo.beam_spacing * 1000.0)
    mod   = IRC22_2014.cl_604_3_modular_ratio(Ecm=mat.Ecm, Kc=0.5)
    props = composite_section_properties(
        beff_mm=beff_mm, ds_mm=slab.thickness, h_haunch_mm=slab.haunch_depth,
        A_steel_mm2=sec.A_steel, Iz_steel_mm4=sec.Iz_steel,
        y_cg_from_bot_mm=sec.y_cg_from_bot, D_steel_mm=sec.D, n=mod["m_short_term"],
    )
    stiffness_ratio = max(props[KEY_COMP_I] / sec.Iz_steel, 1.0)


    Ze_steel_mm3 = float(config.section.Ze_steel)
    # Composite section modulus to the bottom steel fibre (I_comp / y_bot, short-term
    # transformed section). The live-load fatigue stress acts on the COMPOSITE section,
    # not the bare steel — referring the moment range to this larger modulus gives the
    # correct steel-fibre stress range (matches the SLS stress check fbt = M·y_bot/I_comp).
    Ze_comp_bot_mm3 = float(props.get(KEY_COMP_S_BOT) or 0.0) or Ze_steel_mm3
    Aw_mm2       = float(config.section.Aw)
    Nsc          = int(config.fatigue.Nsc)

    # All LCs for the per-LC loop: union of every classified group, deduplicated, preserving order.
    _seen_lcs: set = set()
    _all_lcs_for_per_lc: List[str] = []
    for _grp_lcs in lc_groups.values():
        if isinstance(_grp_lcs, list):
            for _lc in _grp_lcs:
                _s = str(_lc)
                if _s not in _seen_lcs:
                    _seen_lcs.add(_s)
                    _all_lcs_for_per_lc.append(_s)

    per_girder_demands: Dict[str, DemandEnvelope] = {}
    per_girder_per_lc:  Dict[str, Dict[str, DemandEnvelope]] = {}

    for g_name, g_info in girders.items():
        elements = list(g_info.get("elements", []))
        nodes    = list(g_info.get("path", []))
        if not elements:
            continue

        # Helper: max(|comp_i|, |comp_j|) across all girder elements for a single named LC.
        # Returns 0.0 if the LC is not available.
        def _fmax_lc(lc_name, comp_i, comp_j):
            if lc_name is None:
                return 0.0
            try:
                f = analysis_results.ds.forces.sel(Loadcase=lc_name, Element=elements)
                vi = float(np.nan_to_num(np.asarray(f.sel(Component=comp_i).values, dtype=float), nan=0.0).max())
                vj = float(np.nan_to_num(np.asarray(f.sel(Component=comp_j).values, dtype=float), nan=0.0).max())
                return max(abs(vi), abs(vj))
            except Exception:
                return 0.0

        # (1) ULS Mu / Vu / Nu — from analyser's Envelope_ULS case.
        Mu_kNm = _fmax_lc(_uls_env_lc, "Mz_i", "Mz_j") / 1e3   # N·m → kN·m
        Vu_kN  = _fmax_lc(_uls_env_lc, "Vy_i", "Vy_j") / 1e3   # N → kN
        Nu_kN  = _fmax_lc(_uls_env_lc, "Vx_i", "Vx_j") / 1e3   # N → kN (axial Fx)

        # (2) Construction moments — from analyser's SW case (stage 1) and DL+LL case (service).
        M_girder_sw_kNm = _fmax_lc(_sw_lc,     "Mz_i", "Mz_j") / 1e3
        M_const_kNm     = _fmax_lc(_dl_only_lc, "Mz_i", "Mz_j") / 1e3

        # (3) Deflections — fetched directly from analyser cases; no summing, no fallback.
        disp_y = analysis_results.ds.displacements.sel(Component="y", Node=nodes)

        # delta_live: max displacement across individual live-only LCs.
        delta_live_mm = 0.0
        if all_live_lcs:
            try:
                lv = np.asarray(disp_y.sel(Loadcase=all_live_lcs).values, dtype=float)
                lv = lv[~np.isnan(lv)]
                if lv.size:
                    delta_live_mm = float(np.abs(lv).max()) / stiffness_ratio * 1000.0
            except Exception:
                pass

        # delta_total: Dy from analyser's DL+LL case (DL = SW+DC+DD+SIDL, not DW).
        delta_total_mm = 0.0
        if _dl_ll_lc:
            try:
                tv = np.asarray(disp_y.sel(Loadcase=_dl_ll_lc).values, dtype=float)
                tv = tv[~np.isnan(tv)]
                if tv.size:
                    delta_total_mm = float(np.abs(tv).max()) / stiffness_ratio * 1000.0
            except Exception:
                pass

        # (4) Fatigue stress/shear ranges — IRC 22 Cl.604.5. Fatigue is driven by the
        # FATIGUE VEHICLE (IRC:6 Cl.204.6) ALONE — permanent loads are steady and don't
        # cycle, and the Table 6A design vehicles are not the fatigue load model. The
        # range is measured AT A GIVEN SECTION as the truck moves on/off: per-element
        # (max − min, against the unloaded 0 state), worst section. These two values
        # feed only the fatigue checks (8/9); other checks keep SLS_frequent.
        stress_range_MPa = shear_range_MPa = 0.0
        if _fatigue_range_lcs:
            try:
                f = analysis_results.ds.forces.sel(Loadcase=_fatigue_range_lcs, Element=elements)

                def _sec_range(comp_i, comp_j):
                    """Worst per-section (max − min) across truck positions, incl. the 0 state."""
                    rng = 0.0
                    for c in (comp_i, comp_j):
                        da   = f.sel(Component=c)
                        emax = da.max("Loadcase").clip(min=0)   # vehicle on  (or 0 if never +)
                        emin = da.min("Loadcase").clip(max=0)   # vehicle off (0) or hogging
                        v    = float((emax - emin).max())
                        if v == v:                              # skip NaN
                            rng = max(rng, v)
                    return rng

                if Ze_comp_bot_mm3 > 0:
                    stress_range_MPa = _sec_range("Mz_i", "Mz_j") * 1000.0 / Ze_comp_bot_mm3
                if Aw_mm2 > 0:
                    shear_range_MPa = _sec_range("Vy_i", "Vy_j") / Aw_mm2
            except Exception:
                pass

        # (5) SLS M and V — from analyser's Envelope_SLS case.
        M_sls_kNm = _fmax_lc(_sls_env_lc, "Mz_i", "Mz_j") / 1e3
        V_sls_kN  = _fmax_lc(_sls_env_lc, "Vy_i", "Vy_j") / 1e3

        Vr_kN = 0.0
        if all_live_lcs:
            try:
                f_ll = analysis_results.ds.forces.sel(Loadcase=all_live_lcs, Element=elements)
                vy_ll = np.concatenate([
                    np.asarray(f_ll.sel(Component=c).values, dtype=float).flatten()
                    for c in ("Vy_i", "Vy_j")
                ])
                vy_ll = vy_ll[~np.isnan(vy_ll)]
                if vy_ll.size:
                    Vr_kN = (max(float(vy_ll.max()), 0.0)
                             - min(float(vy_ll.min()), 0.0)) / 1e3   # N → kN
            except Exception as e:
                warnings.warn(f"Could not compute Vr for girder {g_name}: {e}. Defaulting to 0.0 kN.")
                Vr_kN = 0.0
            
        per_girder_demands[g_name] = DemandEnvelope(
            Mu_kNm=round(Mu_kNm, 2), Vu_kN=round(Vu_kN, 2), Nu_kN=round(Nu_kN, 2),
            M_construction_kNm=round(M_const_kNm, 2), M_girder_sw_kNm=round(M_girder_sw_kNm, 2),
            delta_live_mm=round(delta_live_mm, 3), delta_total_mm=round(delta_total_mm, 3),
            stress_range_MPa=round(stress_range_MPa, 3), shear_range_MPa=round(shear_range_MPa, 3),
            Nsc=Nsc, governing_combination=_uls_env_lc or "Envelope_ULS",
            location="critical element", member=g_name, source="grillage_analysis",
            M_sls_kNm=round(M_sls_kNm, 2), V_sls_kN=round(V_sls_kN, 2),Vr_kN=round(Vr_kN, 2),
            lc_type="",  # aggregate envelope — all applicable checks run
        )

        # Per-LC DemandEnvelopes — one entry per LC from the analyser's classified groups.
        per_lc: Dict[str, DemandEnvelope] = {}

        for lc_str in _all_lcs_for_per_lc:
            # ── Forces: max(|i|, |j|) per component across girder elements ──
            try:
                lc_forces = analysis_results.ds.forces.sel(Loadcase=lc_str, Element=elements)
                def _fmax(comp_i, comp_j):
                    vi = float(np.nan_to_num(np.asarray(lc_forces.sel(Component=comp_i).values, dtype=float), nan=0.0).max())
                    vj = float(np.nan_to_num(np.asarray(lc_forces.sel(Component=comp_j).values, dtype=float), nan=0.0).max())
                    return max(abs(vi), abs(vj))
                Mz = _fmax("Mz_i", "Mz_j") / 1e3   # N·m → kN·m
                Vy = _fmax("Vy_i", "Vy_j") / 1e3   # N → kN
                Vz = _fmax("Vz_i", "Vz_j") / 1e3
                Vx = _fmax("Vx_i", "Vx_j") / 1e3
                Mx = _fmax("Mx_i", "Mx_j") / 1e3
                My = _fmax("My_i", "My_j") / 1e3
            except Exception:
                continue  # skip LC if forces can't be read from dataset

            # ── Displacements: max abs across girder nodes ──────────────────
            try:
                lc_disps = analysis_results.ds.displacements.sel(Loadcase=lc_str, Node=nodes)
                def _dmax(comp):
                    v = np.nan_to_num(np.asarray(lc_disps.sel(Component=comp).values, dtype=float), nan=0.0)
                    return float(np.abs(v).max())
                Dx = _dmax("x") * 1e3   # m → mm
                Dy = _dmax("y") * 1e3
                Dz = _dmax("z") * 1e3
            except Exception:
                Dx = Dy = Dz = 0.0

            lc_t = _lc_type(lc_str)
            # Every semantic field below is derived from THIS LC's own response,
            # gated by its type — the per-LC contract. Cross-LC aggregates
            # (Vr_kN) stay at girder level; Nsc (config constant) is carried through.
            _d_live  = round(Dy / stiffness_ratio, 3) if lc_t == "live_only" else 0.0
            _d_total = round(Dy / stiffness_ratio, 3) if lc_t == "DL_LL" else 0.0
            # Service-level by elimination — every non-ULS LC (SW, DL, DD, DL_LL, live_only,
            # SLS, SLS_frequent, individual, etc.) is eligible for the SLS stress checks.
            _is_sls = lc_t != "ULS"
            _m_sls  = round(Mz, 2) if _is_sls else 0.0
            _v_sls  = round(Vy, 2) if _is_sls else 0.0
            # Construction moment: this LC's Mz when it IS the dead-load-only case ("X.X DL")
            # from create_dead_load_combination() — SW+DC, the correct Stage 2 LTB demand.
            _m_const = round(Mz, 2) if lc_t == "DL" else 0.0
            # Girder self-weight moment: this LC's Mz when it IS the SW case —
            # enables the Stage-1 LTB check (5a, vs Mb_stage1) in the per-LC view.
            _m_sw    = round(Mz, 2) if (_sw_lc is not None and lc_str == _sw_lc) else 0.0
            # Fatigue ranges (checks 8/9) apply only to frequent SLS cases (Cl.604.5).
            # Mz is in kN·m here → ×1e6 = N·mm; Vy in kN → ×1e3 = N.
            _is_fat     = (lc_t == "SLS_frequent")
            # Composite section modulus — live-load fatigue stress acts on the composite section.
            _stress_rng = round(Mz * 1e6 / Ze_comp_bot_mm3, 3) if _is_fat and Ze_comp_bot_mm3 > 0 else 0.0
            _shear_rng  = round(Vy * 1e3 / Aw_mm2, 3)       if _is_fat and Aw_mm2 > 0 else 0.0

            per_lc[lc_str] = DemandEnvelope(
                # Strong-axis moment, vertical shear, axial — directly usable as ULS demands
                Mu_kNm=round(Mz, 2),
                Vu_kN=round(Vy, 2),
                Nu_kN=round(Vx, 2),
                # Raw 9-component grillage output stored without semantic reinterpretation
                Mx_kNm=round(Mx, 2),   # torsion about longitudinal axis
                My_kNm=round(My, 2),   # weak-axis bending moment
                Vz_kN=round(Vz, 2),    # transverse (out-of-plane) shear
                Dx_mm=round(Dx, 3),    # axial displacement
                Dy_mm=round(Dy, 3),    # vertical displacement
                Dz_mm=round(Dz, 3),    # transverse displacement
                delta_live_mm=_d_live,
                delta_total_mm=_d_total,
                M_sls_kNm=_m_sls,
                V_sls_kN=_v_sls,
                M_construction_kNm=_m_const,
                M_girder_sw_kNm=_m_sw,
                stress_range_MPa=_stress_rng,
                shear_range_MPa=_shear_rng,
                Nsc=Nsc,
                governing_combination=lc_str,
                location="critical element", member=g_name, source="grillage_analysis_per_lc",
                lc_type=lc_t,
            )

        per_girder_per_lc[g_name] = per_lc

    return per_girder_demands, per_girder_per_lc


def _compute_per_lc_dcr(
    config: "BridgeConfig",
    g_lc: "Dict[str, DemandEnvelope]",
) -> "Dict[str, dict]":
    # For each LC run capacity + DCR so the output-dock dropdown can show
    # utilization ratios for all 8 checks per LC / girder combination.
    result: Dict[str, dict] = {}
    for lc_name, lc_d in g_lc.items():
        lc_cap = IRC22CapacityCalculator(config).compute_all(
            Vu_kN=lc_d.Vu_kN,
            stress_range_MPa=lc_d.stress_range_MPa,
            M_sls_kNm=lc_d.M_sls_kNm,
            V_sls_kN=lc_d.V_sls_kN,
            Vr_kN=lc_d.Vr_kN,
        )
        lc_engine = DCREngine(lc_d, lc_cap)
        lc_engine.run_all_checks()
        result[lc_name] = {
            # ── raw demand ──────────────────────────────────────────────────
            "Mu_kNm" : lc_d.Mu_kNm,
            "Vu_kN"  : lc_d.Vu_kN,
            "Nu_kN"  : lc_d.Nu_kN,
            "Mx_kNm" : lc_d.Mx_kNm,
            "My_kNm" : lc_d.My_kNm,
            "Vz_kN"           : lc_d.Vz_kN,
            "Dx_mm"           : lc_d.Dx_mm,
            "Dy_mm"           : lc_d.Dy_mm,
            "Dz_mm"           : lc_d.Dz_mm,
            "lc_type"         : lc_d.lc_type,
            "M_sls_kNm"       : lc_d.M_sls_kNm,
            "V_sls_kN"        : lc_d.V_sls_kN,
            "delta_live_mm"   : lc_d.delta_live_mm,
            "delta_total_mm"  : lc_d.delta_total_mm,
            "stress_range_MPa": lc_d.stress_range_MPa,
            "shear_range_MPa" : lc_d.shear_range_MPa,
            "M_construction_kNm": lc_d.M_construction_kNm,
            "M_girder_sw_kNm" : lc_d.M_girder_sw_kNm,

            # ── DCR summary ─────────────────────────────────────────────────
            "overall_status": lc_engine.overall_status(),
            "max_dcr"       : lc_engine.max_dcr(),
            "category_urs"  : lc_engine.category_urs(),
            # ── per-check detail (id, label, demand, capacity, dcr, status) ──
            "checks": [
                {
                    "id"      : chk.check_id,
                    "label"   : chk.name,
                    "clause"  : chk.clause,
                    "demand"  : chk.demand,
                    "capacity": chk.capacity,
                    "dcr"     : chk.dcr,
                    "status"  : chk.status,
                    "note"    : chk.note,
                }
                for chk in lc_engine.checks
            ],
        }
    return result


def _build_uls_per_girder(per_girder_results: dict) -> dict:
    """Build the ULS-check summary consumed by the Generate Results tables.

    Returns a dict keyed by check category (matching KEY_CHECK_* values):
        {
          "flexure":     {g_name: {demand, capacity, ur, status}, ...},
          "shear":       {g_name: {...}, ...},
          "interaction": {g_name: {...}, ...},   # worst of check_ids 3 & 4
          "ltb":         {g_name: {...}, ...},
        }
    Girders are keyed G1..Gn (they come from result_data["girders"], which already
    excludes the edge members); checks missing for a girder are omitted.
    """
    _CATEGORY_IDS = {
        "flexure":     (1,),
        "shear":       (2,),
        "interaction": (3, 4),
        "ltb":         (5,),
        "fatigue":     (8, 9),   # normal + shear fatigue; worst by DCR
    }

    def _worst(checks, *ids):
        candidates = [c for c in checks if c["check_id"] in ids]
        return max(candidates, key=lambda c: c["dcr"]) if candidates else None

    result: Dict[str, Dict[str, dict]] = {cat: {} for cat in _CATEGORY_IDS}

    for g_name, g_data in per_girder_results.items():
        checks = g_data.get("checks") or []
        for cat, ids in _CATEGORY_IDS.items():
            chk = _worst(checks, *ids)
            if chk is None:
                continue
            result[cat][g_name] = {
                "demand"  : chk["demand"],
                "capacity": chk["capacity"],
                "ur"      : chk["dcr"],
                "status"  : chk["status"],
            }

    return result


def run_design_check(
    config: "BridgeConfig | None" = None,
    plate_girder_bridge: Any | None = None,
    analysis_results: Optional[PlateGirderAnalysisResults] = None,
    per_girder_demands: "Dict[str, DemandEnvelope] | None" = None,
    per_girder_per_lc: "Dict[str, Dict[str, DemandEnvelope]] | None" = None,
    print_report: bool = True,
) -> tuple:
    print("=" * 60)
    print("  IRC 22:2015 DESIGN CHECK PIPELINE")
    print("=" * 60)

    # -- Step 1: Configuration --
    print("\n[Step 1] Loading bridge configuration ...")
    if plate_girder_bridge is not None:
        config = BridgeConfig.from_plate_girder_bridge(plate_girder_bridge)
    elif config is None:
        raise ValueError(
            "Either config (BridgeConfig) or plate_girder_bridge must be supplied to run_design_check()."
        )

    # If stiffener was not set at all (e.g. config built manually without from_plate_girder_bridge),
    # create a default StiffenerConfig so the pipeline always runs in guidance mode at minimum.
    if config.stiffener is None:
        config.stiffener = StiffenerConfig()
        print("  [INFO] stiffener not set — using default StiffenerConfig() (guidance mode)")
    print(f"  Config: {config.summary()}")

    if per_girder_demands is None and analysis_results is not None:
        result_data = getattr(plate_girder_bridge, "result_data", None)
        if not result_data.get("girders"):
            raise ValueError(
                "plate_girder_bridge.result_data must contain a 'girders' key "
                "produced by results_data_post_processing.post_process(). "
                "Run the analysis before run_design_check()."
            )
        per_girder_demands, per_girder_per_lc = _extract_demands_from_analysis_results(
            analysis_results, config, result_data
        )

    if not per_girder_demands:
        raise ValueError(
            "Supply either analysis_results or per_girder_demands "
            "(Dict[girder_name, DemandEnvelope] from the analyser)."
        )

    # -- Step 2: Run IRC 22:2015 checks for every girder (1 to N) --
    print(f"\n[Step 2] Running checks for {len(per_girder_demands)} girder(s) ...")
    per_girder_results: Dict[str, dict] = {}

    # Bearing reaction — if not explicitly set by the user, approximate from the maximum
    # shear demand across girders. For a simply supported bridge this is a close estimate.
    # The user can override by setting bearing_stiffener_reaction in Additional Inputs.
    if config.stiffener.bs_R_kN <= 0.0 and per_girder_demands:
        max_Vu = max(d.Vu_kN for d in per_girder_demands.values())
        config.stiffener.bs_R_kN = max_Vu
        print(f"  [INFO] bs_R_kN not set — using max Vu = {max_Vu:.1f} kN as bearing reaction default")

    # Per-girder configs — when a bridge is available, each girder gets its own
    # BridgeConfig (its own section dimensions) instead of sharing one representative
    # config, so capacity (stud spacing, transverse shear, flexure/shear, …) reflects
    # that girder's actual geometry. Without a bridge (config supplied directly by the
    # caller) there is no per-girder data to draw from, so every girder shares `config`.
    per_girder_configs: Dict[str, "BridgeConfig"] = {}

    for idx, (g_name, g_demand) in enumerate(per_girder_demands.items()):
        if plate_girder_bridge is not None:
            try:
                g_config = BridgeConfig.from_plate_girder_bridge(
                    plate_girder_bridge, girder_index=idx
                )
                if g_config.stiffener is None:
                    g_config.stiffener = StiffenerConfig()
                g_config.stiffener.bs_R_kN = config.stiffener.bs_R_kN
            except Exception:
                g_config = config
        else:
            g_config = config
        per_girder_configs[g_name] = g_config

        g_cap = IRC22CapacityCalculator(g_config).compute_all(
            Vu_kN=g_demand.Vu_kN,
            stress_range_MPa=g_demand.stress_range_MPa,
            M_sls_kNm=g_demand.M_sls_kNm,
            V_sls_kN=g_demand.V_sls_kN,
            Vr_kN=g_demand.Vr_kN,
        )
        g_engine = DCREngine(g_demand, g_cap)
        g_engine.run_all_checks()
        g_cat_urs = g_engine.category_urs()
        # FIX
        if per_girder_per_lc is None:
            raise ValueError(
                "per_girder_per_lc must be supplied to run_design_check(). "
                "Pass the per-LC demand breakdown dict from the analyser."
            )
        if g_name not in per_girder_per_lc:
            raise KeyError(
                f"Girder '{g_name}' not found in per_girder_per_lc. "
                "Ensure the analyser has produced per-LC results for every girder."
            )
        g_lc = per_girder_per_lc[g_name]

        per_girder_results[g_name] = {
            "demand": {
                "Mu_kNm"              : g_demand.Mu_kNm,
                "Vu_kN"               : g_demand.Vu_kN,
                "M_construction_kNm"  : g_demand.M_construction_kNm,
                "M_girder_sw_kNm"     : g_demand.M_girder_sw_kNm,
                "M_sls_kNm"           : g_demand.M_sls_kNm,
                "V_sls_kN"            : g_demand.V_sls_kN,
                "delta_live_mm"       : g_demand.delta_live_mm,
                "delta_total_mm"      : g_demand.delta_total_mm,
                "stress_range_MPa"    : g_demand.stress_range_MPa,
                "shear_range_MPa"     : g_demand.shear_range_MPa,
                "governing_combination": g_demand.governing_combination,
                "Vr_kN"               : g_demand.Vr_kN,
                "member"              : g_demand.member,
                "source"              : g_demand.source,
            },
            "overall_status": g_engine.overall_status(),
            "max_dcr"       : g_engine.max_dcr(),
            "n_pass"        : g_engine.n_pass(),
            "n_warn"        : g_engine.n_warn(),
            "n_fail"        : g_engine.n_fail(),
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
                for chk in g_engine.checks
            ],
            "category_urs": g_cat_urs,
            "per_lc": _compute_per_lc_dcr(g_config, g_lc),
            "sls_fibre_stresses": g_cap.details.get("sls_actual_stresses") or {},
            "section": {
                "D_mm"         : g_config.section.D,
                "tw_mm"        : g_config.section.tw,
                "bf_top_mm"    : g_config.section.bf_top,
                "tf_top_mm"    : g_config.section.tf_top,
                "bf_bot_mm"    : g_config.section.bf_bot,
                "tf_bot_mm"    : g_config.section.tf_bot,
                "dw_mm"        : g_config.section.dw,
                "fabrication"  : g_config.section.fabrication,
                "designation"  : g_config.section.designation,
                "beff_mm"      : g_cap.beff_mm,
                "section_class": g_cap.details["section_class"]["governing_class"],
            },
            "_engine"  : g_engine,
            "_capacity": g_cap,
        }
        icon = {"PASS": "+", "WARN": "~", "FAIL": "X"}.get(g_engine.overall_status(), "?")
        print(f"  [{icon}] {g_name:<40} max_DCR={g_engine.max_dcr():.3f}  {g_engine.overall_status()}")

    # -- Step 3: Controlling girder = highest max DCR --
    ctrl_name = max(per_girder_results, key=lambda g: per_girder_results[g]["max_dcr"])
    ctrl      = per_girder_results[ctrl_name]
    demand    = per_girder_demands[ctrl_name]
    capacity  = ctrl.pop("_capacity")
    engine    = ctrl.pop("_engine")
    config    = per_girder_configs[ctrl_name]   # that girder's own section/material config
    for g in per_girder_results.values():
        g.pop("_engine", None)
        g.pop("_capacity", None)
    print(f"\n  Controlling girder: {ctrl_name}  (max_DCR = {ctrl['max_dcr']:.3f})")

    # -- Step 4: Report for controlling girder only --
    print("\n[Step 4] Generating report for controlling girder ...")
    reporter = ReportGenerator(config, demand, capacity, engine)
    report_text = reporter.generate()

    if print_report:
        print("\n" + report_text)

    print("\n" + "=" * 60)
    print(f"  PIPELINE COMPLETE -- {ctrl_name}  Overall: {engine.overall_status()}")
    print("=" * 60)

    # -- Structured results dict --
    _sec = config.section
    _mat = config.material
    _geo = config.geometry
    design_results = {
        # -- bridge configuration --
        "span_m"                    : _geo.span,
        "support_type"              : _geo.support_type,
        "n_girders"                 : _geo.n_girders,
        "beam_spacing_m"            : _geo.beam_spacing,
        "carriageway_width_m"       : _geo.carriageway_width,
        "beam_type"                 : _geo.beam_type,
        "cross_bracing_spacing_m"   : _geo.cross_bracing_spacing_m,
        # -- material properties --
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
        # -- steel section --
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
        # -- slab --
        "slab_thickness_mm"         : config.slab.thickness,
        "haunch_depth_mm"           : config.slab.haunch_depth,
        # -- shear studs --
        "stud_dia_mm"               : config.studs.diameter,
        "stud_height_mm"            : config.studs.height,
        "stud_fu_MPa"               : config.studs.fu,
        "stud_fy_MPa"               : config.studs.fy, 
        "studs_per_section"         : config.studs.n_per_section,
        # -- controlling girder --
        "controlling_girder"        : ctrl_name,
        # -- demands (controlling girder) --
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
        # -- capacities: ULS flexure --
        "Ag_mm2"                    : capacity.Ag_mm2,
        "NRd_kN"                    : capacity.NRd_kN,
        "beff_mm"                   : capacity.beff_mm,
        "xu_mm"                     : capacity.xu_mm,
        "pna_location"              : capacity.pna_location,
        "Mp_kNm"                    : capacity.Mp_kNm,
        "Md_kNm"                    : capacity.Md_kNm,
        # -- section classification --
        "section_class_web"        : capacity.details["section_class"]["web_class"],
        "section_class_flange"     : capacity.details["section_class"]["flange_class"],
        "section_class_governing"  : capacity.details["section_class"]["governing_class"],
        "section_epsilon"          : capacity.details["section_class"]["epsilon"],
        "d_tw_ratio"               : capacity.details["section_class"]["d_tw_ratio"],
        "b_tf_ratio"               : capacity.details["section_class"]["b_tf_ratio"],
        "web_class_limit"          : capacity.details["section_class"]["web_limit"],
        "flange_class_limit"       : capacity.details["section_class"]["flange_limit"],
        "section_designation"      : _sec.designation,
        "stiffener_grade"          : _mat.steel_grade,
        # -- capacities: LTB --
        "Mcr_kNm"                   : capacity.Mcr_kNm,
        "lambda_LT"                 : capacity.lambda_LT,
        "chi_LT"                    : capacity.chi_LT,
        "Mb_kNm"                    : capacity.Mb_kNm,
        # -- capacities: LTB Stage 1 (girder only, no cross-bracings) --
        "Mb_kNm_stage1"            : capacity.Mb_kNm_stage1,
        "lambda_LT_stage1"         : capacity.lambda_LT_stage1,
        "chi_LT_stage1"            : capacity.chi_LT_stage1,
        # -- capacities: shear --
        "Av_mm2"                    : capacity.Av_mm2,
        "Vn_kN"                     : capacity.Vn_kN,
        "Vd_kN"                     : capacity.Vd_kN,
        # -- capacities: shear buckling --
        "Kv"                        : capacity.Kv,
        "lambda_w"                  : capacity.lambda_w,
        "tau_b_buck_MPa"            : capacity.tau_b_buck_MPa,
        "Vcr_kN"                    : capacity.Vcr_kN,
        "panel_c_mm"                : capacity.details["shear_buckling"]["c_mm"],
        "panel_cd_ratio"            : (round(capacity.details["shear_buckling"]["c_mm"] / _sec.dw, 3)
                                       if capacity.details["shear_buckling"]["c_mm"] > 0 else None),
        # -- capacities: M-V interaction --
        "Mdv_kNm"                   : capacity.Mdv_kNm,
        "beta_interaction"          : capacity.beta_interaction,
        # -- capacities: M-N interaction (None when no axial load → N/A) --
        "mn_axial_term"             : capacity.mn_axial_term  if demand.Nu_kN > 0.0 else None,
        "mn_moment_term"            : capacity.mn_moment_term if demand.Nu_kN > 0.0 else None,
        "mn_ratio"                  : capacity.mn_ratio       if demand.Nu_kN > 0.0 else None,
        # -- SLS limits --
        "defl_limit_live_mm"        : capacity.defl_limit_live_mm,
        "defl_limit_total_mm"       : capacity.defl_limit_total_mm,
        "sigma_c_limit_MPa"         : capacity.sigma_c_limit_MPa,
        "sigma_s_limit_MPa"         : capacity.sigma_s_limit_MPa,
        "sigma_rebar_limit_MPa"     : capacity.sigma_rebar_limit_MPa,
        # -- SLS actual stresses --
        "sigma_c_actual_MPa"        : capacity.sigma_c_actual_MPa,
        "sigma_rebar_actual_MPa"    : capacity.sigma_rebar_actual_MPa,
        "sigma_steel_equiv_MPa"     : capacity.sigma_steel_equiv_MPa,
        # -- Generate-Results steel stress table (controlling-girder envelope SLS;
        #    one value applied to every girder/member row) --
        KEY_SD_STRESS_STEEL           : capacity.sigma_steel_equiv_MPa,
        KEY_SD_STRESS_STEEL_ALLOWABLE : capacity.sigma_s_limit_MPa,
        "tau_web_actual_MPa"        : capacity.tau_web_actual_MPa,
        # -- composite section --
        "I_comp_short_mm4"          : capacity.I_comp_short_mm4,
        "y_top_comp_mm"             : capacity.y_top_comp_mm,
        "y_bot_comp_mm"             : capacity.y_bot_comp_mm,
        # -- fatigue --
        "f_fd_MPa"                  : capacity.f_fd_MPa,
        "tau_fd_MPa"                : capacity.tau_fd_MPa,
        "f_fd_eff_MPa"              : capacity.f_fd_eff_MPa,
        "tau_fd_eff_MPa"            : capacity.tau_fd_eff_MPa,
        # -- shear studs --
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
        # -- shear connector key-mapped computed values --
        KEY_SD_SC_Qu_kN            : capacity.Qu_kN,
        KEY_SD_SC_Qr_kN            : capacity.Qr_kN,
        KEY_SD_SC_VL               : capacity.VL_N_per_mm,
        KEY_SD_SC_SL1              : capacity.stud_spacing_mm,
        KEY_SD_SC_SL2              : capacity.stud_spacing_full_shear_mm,
        KEY_SD_SC_SR               : capacity.stud_spacing_fatigue_mm,
        KEY_SD_SC_H_kN             : (capacity.details.get("stud_spacing_full_shear") or {}).get("H_governing_kN"),
        KEY_SD_SC_Vr_kN            : (capacity.details.get("stud_spacing_fatigue")    or {}).get("Vr_kN"),
        KEY_SD_SC_LIMIT_600        : (capacity.details.get("stud_spacing_limits")     or {}).get("limit_600_mm"),
        KEY_SD_SC_LIMIT_3TSLAB     : (capacity.details.get("stud_spacing_limits")     or {}).get("limit_3_tslab_mm"),
        KEY_SD_SC_LIMIT_4HSTUD     : (capacity.details.get("stud_spacing_limits")     or {}).get("limit_4_hstud_mm"),
        KEY_SD_SC_D_LIMIT          : (capacity.details.get("stud_detailing")          or {}).get("stud_diameter_limit_mm"),
        KEY_SD_SC_H_MIN            : (capacity.details.get("stud_detailing")          or {}).get("required_min_height_mm"),
        KEY_SD_SC_EDGE_DIST        : (capacity.details.get("stud_detailing")          or {}).get("edge_distance_mm"),
        KEY_SD_SC_REQ_EDGE_DIST    : (capacity.details.get("stud_detailing")          or {}).get("required_edge_distance_mm"),
        KEY_SD_SC_CLEAR_COVER      : (capacity.details.get("stud_detailing")          or {}).get("clear_cover_stud_mm"),
        KEY_SD_SC_REQ_CLEAR_COVER  : (capacity.details.get("stud_detailing")          or {}).get("required_clear_cover_mm"),
        # -- transverse shear --
        "transverse_shear_ok"       : capacity.transverse_shear_ok,
        "Ast_required_cm2_per_m"    : capacity.Ast_required_cm2_per_m,
        "Ast_provided_cm2_per_m"    : capacity.Ast_provided_cm2_per_m,
        KEY_SD_TS_VL               : (capacity.details.get("transverse_shear") or {}).get("VL_N_per_mm"),
        KEY_SD_TS_VCAP_CONC        : (capacity.details.get("transverse_shear") or {}).get("Vcap1_kN_per_m"),
        KEY_SD_TS_VCAP_REINF       : (capacity.details.get("transverse_shear") or {}).get("Vcap2_kN_per_m"),
        KEY_SD_TS_VRD              : (capacity.details.get("transverse_shear") or {}).get("governing_capacity_kN_per_m"),
        # -- crack control --
        "As_min_crack_mm2"          : capacity.As_min_crack_mm2,
        "As_provided_crack_mm2"     : capacity.As_provided_crack_mm2,
        KEY_SD_CRACK_AS_MIN        : capacity.As_min_crack_mm2,
        KEY_SD_CRACK_AS_PROV       : capacity.As_provided_crack_mm2,
        # -- stiffener inputs (grade = steel_grade above; same material assumed) --
        "is_tq_mm"                  : config.stiffener.tq_mm if config.stiffener else 0.0,
        "is_H_mm"                   : config.stiffener.H_mm if config.stiffener else 0.0,
        "is_c_mm"                   : config.stiffener.c_mm if config.stiffener else 0.0,
        "is_n_sides"                : config.stiffener.n_sides if config.stiffener else 0,
        "bs_tq_mm"                  : config.stiffener.bs_tq_mm if config.stiffener else 0.0,
        "bs_H_mm"                   : config.stiffener.bs_H_mm if config.stiffener else 0.0,
        "bs_n_plates"               : config.stiffener.bs_n_plates if config.stiffener else 0,
        # -- stiffener design summary (Table 5.7): method + computed (optimized) values --
        "stiff_method"              : capacity.shear_method,
        "stiff_int_thick_req"       : capacity.details.get("intermediate_stiffener", {}).get("tq_req_1sided_mm"),
        "stiff_int_space_req"       : capacity.details.get("intermediate_stiffener", {}).get("c_req_min_mm"),
        "stiff_end_thick_req"       : capacity.details.get("bearing_stiffener", {}).get("tq_req_bearing_mm"),
        # -- stiffener capacities --
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
        # -- DCR summary (controlling girder) --
        "overall_status"            : engine.overall_status(),
        "max_dcr"                   : engine.max_dcr(),
        "n_pass"                    : engine.n_pass(),
        "n_warn"                    : engine.n_warn(),
        "n_fail"                    : engine.n_fail(),
        "category_urs": engine.category_urs(),
        # -- DCR check rows --
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
        # -- clause-level detail dicts --
        "capacity_details"          : capacity.details,
        # -- formatted report text --
        "report_text"               : report_text,
        # -- all-girder results --
        "per_girder"                : per_girder_results,
        # -- ULS check table (Generate Results): per-girder demand/capacity/UR/status
        KEY_SD_ULS_PER_GIRDER       : _build_uls_per_girder(per_girder_results),
    }

    return report_text, engine, design_results
