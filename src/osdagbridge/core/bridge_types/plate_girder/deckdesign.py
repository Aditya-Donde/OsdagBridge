"""
IRC bridge deck slab design module.

Design pipeline:
  1. Read bridge parameters from the backend.
  2. Receive concrete / rebar properties (fck, fctm, fy) resolved from the material DB.
  3. Fetch impact factor from IRC 6:2017 Cl.208.2 / 208.3.
  4. Fetch ULS partial safety factors from IRC 6:2017 Table B.2.
  5. Compute dead-load and live-load moments (effective-width method, IRC 112:2020 Eq. B3.1/B3.2).
  6. Design transverse reinforcement (bottom sagging + top hogging).
  7. Verify moment capacity.
  8. Return a dict compatible with DeckDesign.load_data().
"""

from __future__ import annotations

import math

from osdagbridge.core.bridge_components.super_structure.deck_reinforcement.geometry import (
    bar_area_mm2, reinforcement_area_per_m_mm2,
)
from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
from osdagbridge.core.utils.codes.irc112_2019 import IRC112_2019
from osdagbridge.core.utils.codes.irc22_2015 import IRC22_2014
from osdagbridge.core.utils.codes.keyfile import KEY_VEHICLE
from osdagbridge.core.utils.common import (
    KEY_SPAN, KEY_CARRIAGEWAY_WIDTH, KEY_DECK_CONCRETE_GRADE_BASIC,
    KEY_TS_GIRDER_SPACING, KEY_TS_DECK_OVERHANG, KEY_TS_DECK_THICKNESS,
    KEY_DS_REINF_MATERIAL, KEY_DS_TOP_CLEAR_COVER, KEY_DS_BOTTOM_CLEAR_COVER,
    KEY_DS_REINF_BOUNDS, KEY_WC_THICKNESS, KEY_MP_CB_SPACING,
    # Report output keys — stored in output_dict["deck_report_values"]
    KEY_DD_VEHICLE, KEY_DD_IMPACT_FACTOR, KEY_DD_GAMMA_DL,
    KEY_DD_GAMMA_LL, KEY_DD_SPAN, KEY_DD_WDL,
    KEY_DD_WHEEL_LOAD, KEY_DD_TYRE_WIDTH, KEY_DD_FY,
    KEY_DD_M_DL, KEY_DD_M_LL, KEY_DD_M_ULS_SAG,
    KEY_DD_M_ULS_HOG, KEY_DD_D_BOT, KEY_DD_D_TOP,
    KEY_DD_MU_BOT, KEY_DD_MU_TOP, KEY_DD_AS_REQ_BOT,
    KEY_DD_AS_REQ_TOP, KEY_DD_M_BARRIER,
    KEY_DD_M_DL_OH, KEY_DD_M_LL_OH, KEY_DD_M_ULS_OH,
    KEY_DD_D_OH, KEY_DD_MU_OH, KEY_DD_AS_REQ_OH,
    KEY_DD_PUNCH_VED_KN, KEY_DD_TYRE_LENGTH, KEY_DD_PUNCH_C1,
    KEY_DD_PUNCH_C2, KEY_DD_PUNCH_U1, KEY_DD_PUNCH_VED,
    KEY_DD_VRD_C_MPA, KEY_DD_PUNCH_OK,
    KEY_DD_SHEAR_VED, KEY_DD_SHEAR_VRDC, KEY_DD_SHEAR_OK,
    KEY_DD_AS_MIN, KEY_DD_WK_BOT, KEY_DD_WK_TOP,
    KEY_DD_WK_OH, KEY_DD_WK_LIMIT, KEY_DD_DIA_BOT,
    KEY_DD_SPC_BOT, KEY_DD_AS_BOT, KEY_DD_DIA_TOP,
    KEY_DD_SPC_TOP, KEY_DD_AS_TOP, KEY_DD_DIA_OH,
    KEY_DD_SPC_OH, KEY_DD_AS_OH, KEY_DD_AS_LONG,
    KEY_DD_MIN_COVER, KEY_DD_COVER_OK, KEY_DD_SPACING_MAX,
    KEY_DD_HAS_OVERHANG,
    KEY_DD_STRESS_CONC_BOTTOM, KEY_DD_STRESS_CONC_TOP, KEY_DD_STRESS_CONC_ALLOWABLE,
    KEY_DD_STRESS_REINF_BOTTOM, KEY_DD_STRESS_REINF_TOP, KEY_DD_STRESS_REINF_ALLOWABLE,
    KEY_DD_CRACK_WK_BOTTOM, KEY_DD_CRACK_WK_TOP, KEY_DD_CRACK_WK_LIMIT,
    # Composite interface check output keys — mutated into design_results.
    KEY_SD_TS_VL, KEY_SD_TS_VCAP_CONC, KEY_SD_TS_VCAP_REINF, KEY_SD_TS_VRD,
    KEY_SD_CRACK_AS_MIN, KEY_SD_CRACK_AS_PROV,
    # Deck verdict keys
    STATUS_PASS, STATUS_FAIL, KEY_DD_VERDICT,
    KEY_DD_CHECK_FLEXURE, KEY_DD_CHECK_SHEAR, KEY_DD_CHECK_PUNCHING,
    KEY_DD_CHECK_STRESS_CONC, KEY_DD_CHECK_STRESS_REINF, KEY_DD_CHECK_CRACK,
    KEY_DD_CHECK_COMP_TRANS_SHEAR, KEY_DD_CHECK_COMP_CRACK,
)

# ── constants ─────────────────────────────────────────────────────────────────
_STANDARD_DIAS_MM = [8, 10, 12, 16, 20, 25, 32]
_PREFERRED_MIN_DIA_MM = 12            # prefer ≥12 mm bars when the bounds allow it
_SPACING_MAX_MM = 300.0
_SPACING_MIN_MM = 75.0
_SPACING_ROUND_MM = 5.0               # round spacing down to nearest 5 mm
_TIGHTEN_TARGET_UR = 0.95


# ── structural mechanics helpers ──────────────────────────────────────────────

def _moment_capacity_kNm(fy_MPa: float, As_mm2: float, d_mm: float,
                         fck_MPa: float, b_mm: float = 1000.0) -> float:
    """
    Moment capacity per m width (kNm/m) for a singly reinforced RC section.
    IS 456 / IRC 112 simplified stress-block:
        xu = 0.87 fy As / (0.36 fck b)
        Mu = 0.87 fy As (d - 0.42 xu)
    """
    xu = (0.87 * fy_MPa * As_mm2) / (0.36 * fck_MPa * b_mm)
    Mu_Nmm = 0.87 * fy_MPa * As_mm2 * (d_mm - 0.42 * xu)
    return Mu_Nmm / 1.0e6


def _required_steel_mm2(M_ULS_kNm: float, fy_MPa: float, d_mm: float,
                         fck_MPa: float, b_mm: float = 1000.0) -> float:
    """
    Solve for minimum As (mm²/m) from the quadratic form of the moment equation.
    Returns 0 if M_ULS ≤ 0.
    """
    if M_ULS_kNm <= 0:
        return 0.0
    M_Nmm = M_ULS_kNm * 1.0e6
    # Exact inverse of _moment_capacity_kNm: Mu = 0.87·fy·As·(d − 0.42·xu), xu = 0.87·fy·As/(0.36·fck·b). Substituting xu gives the quadratic 0.42·(0.87fy)²/(0.36 fck b) · As² − (0.87 fy d) · As + M = 0 The 0.42 (rectangular stress-block lever-arm factor) MUST match the capacity formula, otherwise the solver hits disc<0 ("over-stressed") far too early.
    a = 0.42 * (0.87 * fy_MPa) ** 2 / (0.36 * fck_MPa * b_mm)
    b = 0.87 * fy_MPa * d_mm
    disc = b ** 2 - 4.0 * a * M_Nmm
    if disc < 0:
        return float("inf")            # over-stressed — thickness must increase
    return (b - math.sqrt(disc)) / (2.0 * a)


def _min_steel_mm2(fctm_MPa: float, fy_MPa: float, d_mm: float,
                   b_mm: float = 1000.0) -> float:
    """IRC 112 Cl.16.5.1 minimum reinforcement (mm²/m)."""
    As_min = 0.26 * (fctm_MPa / fy_MPa) * b_mm * d_mm
    return max(As_min, 0.0013 * b_mm * d_mm)


def _crack_control_min_top_steel_mm2_per_m(fctm_MPa: float, fy_MPa: float,
                                           t_slab_mm: float, kc: float = 0.5,
                                           k: float = 0.65) -> float:
    """
    IRC 22:2015 Cl.604.4 crack-control minimum, expressed as the top (tension-face)
    reinforcement per metre width.

    The composite check compares As_min = kc·k·fctm·(beff·t_slab)/fy (total over the
    effective flange) against As_top·beff/1000. The effective width beff cancels, so
    the per-metre requirement on the top mat is:
        As_top ≥ kc·k·fctm·t_slab·1000/fy
    k = 0.65 mirrors the composite flange (width > 800 mm) used in the interface check.
    """
    return kc * k * fctm_MPa * t_slab_mm * 1000.0 / fy_MPa


def _pick_rebar(As_req_mm2: float,
                dias: list = _STANDARD_DIAS_MM) -> tuple[float, float, float]:
    """
    Choose the smallest bar diameter from `dias` and round-down spacing
    such that As_provided ≥ As_req.
    Returns (dia_mm, spacing_mm, As_prov_mm2_per_m).
    `dias` is pre-filtered by KEY_DS_REINF_BOUNDS before this call.
    """
    for dia in dias:
        a_bar = bar_area_mm2(dia)
        spacing = a_bar * 1000.0 / As_req_mm2
        spacing = min(spacing, _SPACING_MAX_MM)
        spacing = max(spacing, _SPACING_MIN_MM)
        # round down to nearest _SPACING_ROUND_MM
        spacing = math.floor(spacing / _SPACING_ROUND_MM) * _SPACING_ROUND_MM
        spacing = max(spacing, _SPACING_MIN_MM)
        As_prov = reinforcement_area_per_m_mm2(dia, spacing)
        if As_prov >= As_req_mm2:
            return dia, spacing, As_prov
    # largest allowed bar at minimum spacing
    dia = dias[-1]
    spacing = _SPACING_MIN_MM
    return dia, spacing, reinforcement_area_per_m_mm2(dia, spacing)


# ── shear helpers ─────────────────────────────────────────────────────────────

def _wheel_contact_length_mm(vehicle_class: str) -> float:
    """Longitudinal wheel-contact length (mm) for punching — IRC 6:2017 drawings."""
    if vehicle_class in (KEY_VEHICLE[0], KEY_VEHICLE[1]):
        return 150.0   # Class 70R
    return 200.0       # Class A


def _v_Rd_c_MPa(As_mm2: float, d_mm: float, fck_MPa: float,
                b_mm: float = 1000.0) -> float:
    """
    IRC 112:2020 Eq.10.1 — design shear resistance stress (MPa), σ_cp = 0.
    Shared by one-way shear (Cl.10.3.2, V_Rd,c = result × b_w × d)
    and punching shear (Cl.10.4, compared directly to v_Ed = V/(u1·d)).
    """
    k = min(1.0 + math.sqrt(200.0 / d_mm), 2.0)
    rho1 = min(As_mm2 / (b_mm * d_mm), 0.02)
    return max(
        0.12 * k * (80.0 * rho1 * fck_MPa) ** 0.33,
        0.031 * k ** 1.5 * math.sqrt(fck_MPa),
    )


def _tighten_for_oneway_shear(V_ULS_kN_per_m: float, dia: float, spc: float,
                              As: float, deck_t_mm: float, cover_mm: float,
                              fck: float, allowed_dias: list,
                              target_ur: float = _TIGHTEN_TARGET_UR) -> tuple:
    """
    Increase reinforcement until the one-way shear capacity (IRC 112:2020
    Cl.10.3.2, VRd,c = v_Rd,c·d, no links) leaves the wanted margin. v_Rd,c rises
    with the reinforcement ratio ρ1 (capped at 0.02), so adding steel helps until
    that cap. The target capacity is V_ULS/target_ur so the reported utilisation
    (V_ULS/VRd,c) lands at ≈target_ur. Returns (dia, spc, As, d). Only adds steel;
    stops when the target is met, the ρ1 cap is reached, or the bars are maxed out
    (capacity can't grow further — the check still passes, just nearer 100%).
    """
    V_target = V_ULS_kN_per_m / target_ur
    d_mm = deck_t_mm - cover_mm - dia / 2.0
    for _ in range(60):
        VRd_c = _v_Rd_c_MPa(As, d_mm, fck) * d_mm        # MPa·mm = N/mm = kN/m
        if VRd_c >= V_target:
            break
        if As / (1000.0 * d_mm) >= 0.02:                 # ρ1 cap — steel can't help more
            break
        dia_new, spc_new, As_new = _pick_rebar(As * 1.03, allowed_dias)
        if As_new <= As:                                 # bars maxed out
            break
        dia, spc, As = dia_new, spc_new, As_new
        d_mm = deck_t_mm - cover_mm - dia / 2.0
    return dia, spc, As, d_mm


# ── SLS helpers ───────────────────────────────────────────────────────────────

def _cracked_section(As_mm2: float, d_mm: float, Es_MPa: float, Ecm_MPa: float,
                     b_mm: float = 1000.0) -> tuple:
    """
    Cracked-section neutral axis depth x (mm), I_cr (mm⁴), and αe = Es/Ecm.
    Solves b/2·x² + αe·As·x − αe·As·d = 0.
    """
    alpha_e = Es_MPa / Ecm_MPa
    A = b_mm / 2.0
    B = alpha_e * As_mm2
    C = -alpha_e * As_mm2 * d_mm
    x = (-B + math.sqrt(B**2 - 4.0 * A * C)) / (2.0 * A)
    I_cr = b_mm * x**3 / 3.0 + alpha_e * As_mm2 * (d_mm - x) ** 2
    return x, I_cr, alpha_e


def _sls_stress(M_SLS_kNm: float, As_mm2: float, d_mm: float,
                fck_MPa: float, fy_MPa: float, Es_MPa: float, Ecm_MPa: float, b_mm: float = 1000.0) -> dict:
    """
    IRC 112:2020 Cl.12.2.1 — SLS stress check (characteristic combination).
    Limits: σc ≤ 0.48·fck, σs ≤ 0.80·fyk.
    """
    x, I_cr, alpha_e = _cracked_section(As_mm2, d_mm, Es_MPa, Ecm_MPa, b_mm)
    M_Nmm = M_SLS_kNm * 1.0e6
    sigma_c = M_Nmm * x / I_cr
    sigma_s = M_Nmm * (d_mm - x) * alpha_e / I_cr
    sc_lim = 0.48 * fck_MPa
    ss_lim = 0.80 * fy_MPa
    return {
        "x": x,
        "sigma_c": sigma_c, "sc_lim": sc_lim, "sc_ok": sigma_c <= sc_lim,
        "sigma_s": sigma_s, "ss_lim": ss_lim, "ss_ok": sigma_s <= ss_lim,
        "ok": sigma_c <= sc_lim and sigma_s <= ss_lim,
    }


def _tighten_for_sls_stress(M_SLS_char_kNm: float, dia: float, spc: float,
                            As: float, deck_t_mm: float, cover_mm: float,
                            fck: float, fy: float, Es: float, Ecm: float,
                            allowed_dias: list,
                            target_ur: float = _TIGHTEN_TARGET_UR) -> tuple:
    """
    Increase the reinforcement until the SLS steel stress leaves the wanted margin
    (IRC 112:2020 Cl.12.2.1, σs ≤ 0.8·fy). The target is target_ur·(0.8·fy) so the
    reported utilisation (σs/0.8fy) lands at ≈target_ur. σs is non-linear in As, so
    the bars are bumped (+3 %) and re-picked iteratively. Returns (dia, spc, As, d).
    Only ever adds steel, so any ULS/crack/minimum requirement already met by the
    incoming bars is preserved. Stops if the bars are maxed out (largest allowed
    diameter at minimum spacing) so the section cannot reach the target.
    """
    ss_target = target_ur * 0.80 * fy
    d_mm = deck_t_mm - cover_mm - dia / 2.0
    for _ in range(60):
        sigma_s = _sls_stress(M_SLS_char_kNm, As, d_mm, fck, fy, Es, Ecm)["sigma_s"]
        if sigma_s <= ss_target:
            break
        dia_new, spc_new, As_new = _pick_rebar(As * 1.03, allowed_dias)
        if As_new <= As:          # bars maxed out — cannot add more steel
            break
        dia, spc, As = dia_new, spc_new, As_new
        d_mm = deck_t_mm - cover_mm - dia / 2.0
    return dia, spc, As, d_mm

def _sls_crack_width(M_SLS_kNm: float, As_mm2: float, dia_mm: float,
                     d_mm: float, h_mm: float, cover_mm: float,
                     fctm_MPa: float, Es_MPa: float, Ecm_MPa: float,
                     b_mm: float = 1000.0) -> dict:
    """
    IRC 112:2020 Cl.12.3.2 — crack width check (frequent combination).
    wk limit = 0.3 mm (exposure XS2/XD2 for bridge decks).
    x and d are both measured from the compressive face, so this function
    works identically for sagging (compressive face = top) and hogging
    (compressive face = bottom).
    """
    x, I_cr, alpha_e = _cracked_section(As_mm2, d_mm, Es_MPa, Ecm_MPa, b_mm)
    M_Nmm = M_SLS_kNm * 1.0e6
    sigma_s = M_Nmm * (d_mm - x) * alpha_e / I_cr
    # Effective tension area depth (measured from tensile face)
    Ac_eff = (
        min(2.5 * (cover_mm + dia_mm / 2.0), (h_mm - x) / 3.0, h_mm / 2.0) * b_mm
    )
    rho_p_eff = As_mm2 / Ac_eff
    # Maximum crack spacing — IRC 112:2020 Cl.12.3.4
    k1, k2, k3, k4 = 0.8, 0.5, 3.4, 0.425
    Sr_max = k3 * cover_mm + k1 * k2 * k4 * dia_mm / rho_p_eff
    # Mean strain difference (long-term, kt = 0.5)
    kt = 0.5
    eps_diff = max(
        (sigma_s - kt * (fctm_MPa / rho_p_eff) * (1.0 + alpha_e * rho_p_eff)) / Es_MPa,
        0.6 * sigma_s / Es_MPa,
    )
    wk = Sr_max * eps_diff   # mm
    wk_lim = 0.3
    return {
        "sigma_s": sigma_s, "x": x, "rho_p_eff": rho_p_eff,
        "Sr_max": Sr_max, "eps_diff": eps_diff, "wk": wk, "wk_lim": wk_lim,
        "ok": wk <= wk_lim,
    }


# ── governing vehicle ─────────────────────────────────────────────────────────

def _governing_vehicle(carriageway_width_m: float) -> str:
    """
    Return the governing vehicle class based on IRC 6:2017 Table 6A.
    Class 70R(W) governs when at least one 70R lane fits; Class A otherwise.
    """
    result = IRC6_2017.table_6A(carriageway_width_m)
    combos = result.get("vehicle_combinations", [])
    for combo in combos:
        if "Class70R" in combo:
            return KEY_VEHICLE[0]      # Class70R(W)
    return KEY_VEHICLE[2]              # ClassA


def _max_wheel_load_kN(vehicle_class: str) -> float:
    """
    Maximum single wheel load (kN) for the governing vehicle per IRC 6:2017.
    wheel_loads are per-axle totals stored in Newtons (IRC6 unit system uses
    t = kN*g = 9810 N); divide by 2 for per-wheel and by 1000 to get kN.
    """
    if vehicle_class in (KEY_VEHICLE[0], KEY_VEHICLE[1]):  # Class 70R
        axle_loads = IRC6_2017.cl_204_1_Class70R_vehicle_wheel()["wheel_loads"]
    else:                                                   # Class A / B
        axle_loads = IRC6_2017.cl_204_1_ClassA_vehicle()["wheel_loads"]
    return max(axle_loads) / 2.0 / 1000.0   # N → kN, axle → per-wheel


def _wheel_contact_width_m(vehicle_class: str) -> float:
    """Transverse wheel-contact width (m) for dispersion — IRC 6:2017 drawings."""
    if vehicle_class in (KEY_VEHICLE[0], KEY_VEHICLE[1]):
        return 0.300                   # Class 70R: 300 mm transverse contact
    return 0.250                       # Class A:   250 mm transverse contact


# ── composite steel–concrete interface checks (IRC 22:2015) ──────────────────
# These are steel/composite-girder checks, but they need the slab reinforcement
# area that is sized in this module — so they live here and are called by the
# steel-design pipeline with its own beff / VL, while the slab steel is supplied
# from here. Return dicts match the original IRC22CapacityCalculator methods.

def crack_control_As_min(beff_mm: float, fctm_MPa: float, fy_rebar_MPa: float,
                         t_slab_mm: float, As_total_mm2: float) -> dict:
    """
    IRC 22:2015 Cl.604.4 + IRC 112-2011 Cl.12.3.3 — minimum reinforcement for crack control.
    As_provided = total top reinforcement over the effective width (tension-face steel);
    0 ⇒ guidance mode.
    """
    res = IRC22_2014.cl_604_4_crack_control_As_min(
        fctm=fctm_MPa,
        beff=beff_mm,
        t_slab=t_slab_mm,
        fy=fy_rebar_MPa,
        kc=0.5,
        width_mm=beff_mm,
        element_type="flange",
        As_provided=As_total_mm2 if As_total_mm2 > 0.0 else None,
    )
    return {
        "As_min_mm2"      : res["As_min_mm2"],
        "As_provided_mm2" : As_total_mm2,
        "is_ok"           : res.get("is_ok"),    # None if As_provided = 0
        "kc"              : res["kc"],
        "k"               : res["k"],
        "fctm_MPa"        : res["fctm_MPa"],
        "clause"          : res["clause"],
        "source"          : "IRC22_2014",
    }


def transverse_shear_check(VL_N_per_mm: float, fck_MPa: float, fy_rebar_MPa: float,
                           bf_top_mm: float, stud_height_mm: float, t_slab_mm: float,
                           As_total_mm2: float, n_layers: int = 6) -> dict:
    """
    IRC 22:2015 Cl.606.10 — transverse shear check at the steel–concrete interface.
    Shear plane length for an interior girder: shorter of slab thickness or
    (2·h_stud + bf_top). n_layers=6 ≈ bars within 1 m at 200 mm longitudinal spacing.
    """
    L_mm = min(t_slab_mm, 2.0 * stud_height_mm + bf_top_mm)
    Ast_cm2_per_m = As_total_mm2 / 100.0   # mm²/m → cm²/m
    res = IRC22_2014.cl_606_10_transverse_shear_check(
        VL_kN=VL_N_per_mm,          # N/mm ≡ kN/m
        fck=fck_MPa,
        fyk=fy_rebar_MPa,
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


# ── deck verdict ──────────────────────────────────────────────────────────────

# Deck check key -> the result-dict UR fields feeding it (worst location governs).
# Fields absent from result (no overhang / non-composite deck) are skipped.
_DECK_VERDICT_UR_FIELDS = {
    KEY_DD_CHECK_FLEXURE:          ("ur_bot_uls", "ur_top_uls", "ur_oh_uls"),
    KEY_DD_CHECK_SHEAR:            ("ur_bot_shear", "ur_oh_shear"),
    KEY_DD_CHECK_PUNCHING:         ("ur_bot_punch", "ur_oh_punch"),
    KEY_DD_CHECK_STRESS_CONC:      ("ur_bot_sls_c", "ur_top_sls_c", "ur_oh_sls_c",
                                    "ur_composite_conc_stress"),
    KEY_DD_CHECK_STRESS_REINF:     ("ur_bot_sls_s", "ur_top_sls_s", "ur_oh_sls_s",
                                    "ur_composite_rebar_stress"),
    KEY_DD_CHECK_CRACK:            ("ur_bot_crack", "ur_top_crack", "ur_oh_crack"),
    KEY_DD_CHECK_COMP_TRANS_SHEAR: ("ur_composite_trans_shear",),
    KEY_DD_CHECK_COMP_CRACK:       ("ur_composite_crack",),
}


def collect_deck_verdict(result: dict) -> dict:
    """Reduce the deck checks to one PASS/FAIL verdict.

    Reads the UR fields already in ``result``; a check passes when its worst UR
    (over interior sagging / hogging / overhang) is <= 1.0. Checks with no fields
    present (no overhang, non-composite deck) are omitted.

    Returns { KEY_DD_CHECK_*: {"pass": bool, "ur": float}, ...,
              "status": STATUS_PASS | STATUS_FAIL, "max_ur": float }.
    """
    cats = {}
    max_ur = 0.0
    for key, fields in _DECK_VERDICT_UR_FIELDS.items():
        urs = [float(result[f]) for f in fields if f in result]
        if not urs:
            continue
        worst = max(urs)
        max_ur = max(max_ur, worst)
        cats[key] = {"pass": worst <= 1.0, "ur": round(worst, 3)}

    # `cats and` is load-bearing: all() of an empty dict is True, so without it a
    # verdict with no checks at all would report PASS.
    cats["status"] = (STATUS_PASS
                      if cats and all(c["pass"] for c in cats.values()
                                      if isinstance(c, dict))
                      else STATUS_FAIL)
    cats["max_ur"] = round(max_ur, 3)
    return cats


# ── main design function ──────────────────────────────────────────────────────

def design_deck_slab(input_dict: dict, fck: float, fctm: float, fy: float, Es: float, Ecm: float,
                     *, design_results: dict | None = None,
                     bf_top_mm: float = 0.0, stud_height_mm: float = 0.0) -> tuple[dict, dict]:
    """
    Design the concrete deck slab of a plate girder bridge.

    Parameters
    ----------
    input_dict : dict
        Flat bridge input dictionary (``PlateGirderBridge.input_dict``) populated
        before/after design() has been run.
    fck : float
        Characteristic concrete compressive strength (MPa), from the material DB.
    fctm : float
        Mean concrete tensile strength (MPa), from the material DB.
    fy : float
        Reinforcement characteristic yield strength (MPa), from the material DB.
    Es : float
        Modulus of elasticity of reinforcement (MPa), from the material DB.
    Ecm : float
        Modulus of elasticity of concrete (MPa), from the material DB.
    design_results : dict, optional
        The Stage-5 steel-design results dict (``output_dict["design_results"]``).
        When it carries the composite ``beff_mm`` and longitudinal shear
        ``VL_N_per_mm``, the composite steel–concrete interface checks (Cl.606.10
        transverse shear, Cl.604.4 crack control) are run with the deck-designed
        reinforcement and their values written back into it in place (report /
        generate-results tables). If None/incomplete, those checks are skipped.
    bf_top_mm : float, optional
        Girder top-flange width (mm) — resolved by the caller (girder resolution
        stays out of this module). Required for the transverse-shear check.
    stud_height_mm : float, optional
        Shear-stud height (mm) from the caller's ``input_dict``. Used by the
        transverse-shear check.

    Returns
    -------
    tuple[dict, dict]
        ``(result, report_values)``.

        ``result`` — UI-facing dict keyed to DeckDesign.load_data() /
        DECK_DESIGN_SUMMARY_SCHEMA:
        deck_grade, deck_thickness, deck_overhang,
        rebar_{top,bottom,overhang}_{yield,dia,spacing,cover,area},
        ur_{bot,top,oh}_{uls,sls_c,sls_s,crack},
        deck_design_check.

        ``report_values`` — raw numeric values keyed to common.KEY_DD_*,
        consumed by the report generator (Tables 5.17(a)-(g)). Stored in
        output_dict["deck_report_values"].
    """
    # ── 1. read bridge parameters ─────────────────────────────────────────────
    inp = input_dict

    span_m = float(inp[KEY_SPAN])
    cw_m = float(inp[KEY_CARRIAGEWAY_WIDTH])
    concrete_grade = str(inp[KEY_DECK_CONCRETE_GRADE_BASIC]).strip()

    beam_spacing_m = float(inp[KEY_TS_GIRDER_SPACING])
    overhang_m = float(inp[KEY_TS_DECK_OVERHANG])
    deck_t_mm = float(inp[KEY_TS_DECK_THICKNESS])
    wc_t_m = float(inp[KEY_WC_THICKNESS]) / 1000.0   # wearing course thickness (m)
    from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import resolve_cb_value
    cb_spacing_m = float(resolve_cb_value(inp, KEY_MP_CB_SPACING) or 3.0)  # longitudinal cross-bracing spacing (m)

    rebar_grade = str(inp[KEY_DS_REINF_MATERIAL]).strip()
    cover_top_mm = float(inp[KEY_DS_TOP_CLEAR_COVER])
    cover_bot_mm = float(inp[KEY_DS_BOTTOM_CLEAR_COVER])

    bounds = inp[KEY_DS_REINF_BOUNDS]
    # lower/upper may be None — an explicit "no bound", i.e. open at that end.
    lower_dia = int(bounds["lower"]) if bounds["lower"] is not None else _STANDARD_DIAS_MM[0]
    upper_dia = int(bounds["upper"]) if bounds["upper"] is not None else _STANDARD_DIAS_MM[-1]
    allowed_dias = [d for d in _STANDARD_DIAS_MM if lower_dia <= d <= upper_dia]
    # 8/10 mm bars are impractically small for a bridge deck — prefer to start the
    # bar selection at 12 mm, but only when the user's bounds actually allow it.
    practical_dias = [d for d in allowed_dias if d >= _PREFERRED_MIN_DIA_MM]
    if practical_dias:
        allowed_dias = practical_dias

    # ── 2. material properties (fck, fctm, fy resolved from the material DB) ───
    # concrete_grade / rebar_grade are read above only for the report text.

    # ── 2a. recommended minimum cover from IRC 112:2020 Table 14.2 ───────────
    cover_rec = IRC112_2019.table_14_2_min_cover(concrete_grade)
    min_cover_rec_mm = cover_rec["min_cover_mm"]
    cover_top_ok = cover_top_mm >= min_cover_rec_mm
    cover_bot_ok = cover_bot_mm >= min_cover_rec_mm

    # ── 3. governing vehicle & IRC 6 loads ────────────────────────────────────
    vehicle_class = _governing_vehicle(cw_m)

    # Impact factor — IRC 6:2017 Cl.208
    if vehicle_class in (KEY_VEHICLE[0], KEY_VEHICLE[1]):
        IF = IRC6_2017.cl_208_3_impact_factor(span_m)
    else:
        IF = IRC6_2017.cl_208_2_impact_factor(span_m)
    impact_factor = 1.0 + IF

    # ULS partial safety factors — IRC 6:2017 Table B.2
    gamma_dl = IRC6_2017.table_B2("dead_load", "adding", "basic")
    gamma_ll = IRC6_2017.table_B2("live_load", "leading", "basic")

    # Maximum single wheel load (kN) — IRC 6:2017 Cl.204
    P_wheel_kN = _max_wheel_load_kN(vehicle_class)

    # ── 4. dead load moment (continuous slab, per m width) ───────────────────
    # Unit weight from IRC 6:2017 Cl.203 (t/m³ × 9.81 → kN/m³)
    gamma_concrete_kN_m3 = IRC6_2017.cl_203_dead_load()["concrete_cement_reinforced"] * 9.81
    w_DL_kN_m2 = gamma_concrete_kN_m3 * (deck_t_mm / 1000.0)
    S = beam_spacing_m
    M_DL_kNm = w_DL_kN_m2 * S ** 2 / 10.0   # kNm/m — moment in a continuous slab

    # ── 5. live load moment (effective-width method, IRC 112:2020 Eq. B3.1) ────
    # The deck slab forms rectangular panels bounded by:
    #   l_o = S   (transverse girder spacing — the span direction)
    #   b = cb_spacing_m  (longitudinal cross-bracing spacing — dimension parallel to supports)
    # b1 = tyre contact width + 2 × wearing course thickness (IRC 112:2020 Eq. B3.1)
    b1_m = _wheel_contact_width_m(vehicle_class) + 2.0 * wc_t_m
    alpha_e = IRC112_2019.table_B31_alpha_e(cb_spacing_m / S, continuous=True)
    a = S / 2.0   # load at mid-span for maximum sagging moment
    beff_m = IRC112_2019.eq_B31_effective_width(S, a, b1_m, cb_spacing_m / S, continuous=True, b_cap=S)
    # Transverse moment at mid-span: M = P × a × (S-a) / (S × beff)
    M_LL_kNm = P_wheel_kN * a * (S - a) / (S * beff_m)

    # ── 6. ULS design moment ─────────────────────────────────────────────────
    M_ULS_bot_kNm = gamma_dl * M_DL_kNm + gamma_ll * impact_factor * M_LL_kNm
    M_ULS_top_kNm = 0.75 * M_ULS_bot_kNm   # hogging over support ≈ 75% of sagging

    # ── 7. design bottom (sagging) reinforcement ──────────────────────────────
    d_bot_mm = deck_t_mm - cover_bot_mm - 6.0    # initial estimate (6 mm = half 12 mm bar)
    As_req_bot = max(_required_steel_mm2(M_ULS_bot_kNm / _TIGHTEN_TARGET_UR, fy, d_bot_mm, fck),
                     _min_steel_mm2(fctm, fy, d_bot_mm))
    dia_bot, spc_bot, As_bot = _pick_rebar(As_req_bot, allowed_dias)
    d_bot_mm = deck_t_mm - cover_bot_mm - dia_bot / 2.0   # refined with actual bar
    # Second pass — recheck with refined d to guard against d decreasing for larger bars
    As_req_bot2 = max(_required_steel_mm2(M_ULS_bot_kNm / _TIGHTEN_TARGET_UR, fy, d_bot_mm, fck),
                      _min_steel_mm2(fctm, fy, d_bot_mm))
    if As_req_bot2 > As_bot:
        dia_bot, spc_bot, As_bot = _pick_rebar(As_req_bot2, allowed_dias)
        d_bot_mm = deck_t_mm - cover_bot_mm - dia_bot / 2.0
    # Bottom mat must also satisfy the SLS steel-stress limit (Cl.12.2.1).
    dia_bot, spc_bot, As_bot, d_bot_mm = _tighten_for_sls_stress(
        M_DL_kNm + impact_factor * M_LL_kNm, dia_bot, spc_bot, As_bot,
        deck_t_mm, cover_bot_mm, fck, fy, Es, Ecm, allowed_dias)
    # …and the interior one-way (cantilever) shear demand at the support face —
    # v_Rd,c rises with the reinforcement ratio, so add steel if the demand isn't met.
    V_ULS_bot_demand = (gamma_dl * (w_DL_kN_m2 * S / 2.0)
                        + gamma_ll * impact_factor * (P_wheel_kN / beff_m))
    dia_bot, spc_bot, As_bot, d_bot_mm = _tighten_for_oneway_shear(
        V_ULS_bot_demand, dia_bot, spc_bot, As_bot,
        deck_t_mm, cover_bot_mm, fck, allowed_dias)

    # ── 8. design top (hogging) reinforcement ────────────────────────────────
    d_top_mm = deck_t_mm - cover_top_mm - 6.0
    # Top mat must also satisfy the composite crack-control minimum (Cl.604.4) so
    # that a thicker slab cannot fail crack control (which scales with slab depth).
    As_crack_min_top = _crack_control_min_top_steel_mm2_per_m(fctm, fy, deck_t_mm)
    As_req_top = max(_required_steel_mm2(M_ULS_top_kNm / _TIGHTEN_TARGET_UR, fy, d_top_mm, fck),
                     _min_steel_mm2(fctm, fy, d_top_mm), As_crack_min_top)
    dia_top, spc_top, As_top = _pick_rebar(As_req_top, allowed_dias)
    d_top_mm = deck_t_mm - cover_top_mm - dia_top / 2.0
    As_req_top2 = max(_required_steel_mm2(M_ULS_top_kNm / _TIGHTEN_TARGET_UR, fy, d_top_mm, fck),
                      _min_steel_mm2(fctm, fy, d_top_mm), As_crack_min_top)
    if As_req_top2 > As_top:
        dia_top, spc_top, As_top = _pick_rebar(As_req_top2, allowed_dias)
        d_top_mm = deck_t_mm - cover_top_mm - dia_top / 2.0
    # Top mat must also satisfy the SLS steel-stress limit (Cl.12.2.1).
    dia_top, spc_top, As_top, d_top_mm = _tighten_for_sls_stress(
        0.75 * (M_DL_kNm + impact_factor * M_LL_kNm), dia_top, spc_top, As_top,
        deck_t_mm, cover_top_mm, fck, fy, Es, Ecm, allowed_dias)

    # ── 9. moment capacity check ─────────────────────────────────────────────
    Mu_bot = _moment_capacity_kNm(fy, As_bot, d_bot_mm, fck)
    Mu_top = _moment_capacity_kNm(fy, As_top, d_top_mm, fck)
    bot_ok = Mu_bot >= M_ULS_bot_kNm
    top_ok = Mu_top >= M_ULS_top_kNm

    # ── 9a. longitudinal (distribution) reinforcement ────────────────────────
    # IRC 112:2020 Cl.16.6.1: secondary reinforcement ≥ 20 % of main transverse.
    As_req_long = max(0.20 * As_bot, _min_steel_mm2(fctm, fy, d_bot_mm))
    dia_long, spc_long, As_long = _pick_rebar(As_req_long, allowed_dias)

    # ── 10. deck overhang design ─────────────────────────────────────────────
    if overhang_m > 0.01:
        # Edge clearance f: min distance from kerb/barrier face to wheel — IRC 6:2017 Table 3
        # (g is the inter-vehicle gap, f is the wheel-to-edge clearance used for arm calculation)
        table3 = IRC6_2017.table_3(cw_m)
        f_edge = float(table3["f"])

        # Railing dead load — IRC 6:2017 Cl.206.5 (kg/m → kN/m)
        railing_kN_m = IRC6_2017.cl_206_5_railing_load() * 9.81 / 1000.0

        # Crash barrier horizontal moment — IRC 6:2017 Cl.206.6
        barrier = IRC6_2017.cl_206_6_crash_barrier_load()
        M_barrier_kNm = barrier["moment_at_base_kNm_per_m"]

        # DL cantilever moments at root (kNm/m)
        M_DL_slab_oh = w_DL_kN_m2 * overhang_m ** 2 / 2.0
        M_DL_railing_oh = railing_kN_m * overhang_m
        M_DL_oh = M_DL_slab_oh + M_DL_railing_oh

        # LL cantilever moment: wheel placed at f_edge clearance from the free (kerb) edge
        arm_wheel = overhang_m - f_edge
        if arm_wheel > 0.0:
            # IRC 112:2020 Eq. B3.2 — cantilever effective width
            # b1 = tyre contact width + 2 × wearing course thickness
            b1_oh = _wheel_contact_width_m(vehicle_class) + 2.0 * wc_t_m
            beff_oh = IRC112_2019.eq_B32_effective_width_cantilever(arm_wheel, b1_oh, span_m)
            M_LL_oh = P_wheel_kN * arm_wheel / beff_oh
        else:
            arm_wheel = 0.0
            beff_oh = overhang_m
            M_LL_oh = 0.0

        # ULS hogging moment at root
        M_ULS_oh = (gamma_dl * M_DL_oh
                    + gamma_ll * impact_factor * M_LL_oh
                    + gamma_ll * M_barrier_kNm)

        # Design top (hogging) reinforcement for overhang
        d_oh_mm = deck_t_mm - cover_top_mm - 6.0
        As_req_oh = max(_required_steel_mm2(M_ULS_oh / _TIGHTEN_TARGET_UR, fy, d_oh_mm, fck),
                        _min_steel_mm2(fctm, fy, d_oh_mm))
        dia_oh, spc_oh, As_oh = _pick_rebar(As_req_oh, allowed_dias)
        d_oh_mm = deck_t_mm - cover_top_mm - dia_oh / 2.0
        # Second pass — recheck with refined d (larger bars reduce d below d_init)
        As_req_oh2 = max(_required_steel_mm2(M_ULS_oh / _TIGHTEN_TARGET_UR, fy, d_oh_mm, fck),
                         _min_steel_mm2(fctm, fy, d_oh_mm))
        if As_req_oh2 > As_oh:
            dia_oh, spc_oh, As_oh = _pick_rebar(As_req_oh2, allowed_dias)
            d_oh_mm = deck_t_mm - cover_top_mm - dia_oh / 2.0
        # Overhang bars must also pass one-way (cantilever) shear — v_Rd,c rises
        # with the reinforcement ratio, so add steel if the demand isn't met.
        V_DL_oh_v = w_DL_kN_m2 * overhang_m + railing_kN_m
        V_LL_oh_v = P_wheel_kN / beff_oh if arm_wheel > 0.0 else 0.0
        V_ULS_oh_demand = gamma_dl * V_DL_oh_v + gamma_ll * impact_factor * V_LL_oh_v
        dia_oh, spc_oh, As_oh, d_oh_mm = _tighten_for_oneway_shear(
            V_ULS_oh_demand, dia_oh, spc_oh, As_oh,
            deck_t_mm, cover_top_mm, fck, allowed_dias)

        Mu_oh = _moment_capacity_kNm(fy, As_oh, d_oh_mm, fck)
        oh_ok = Mu_oh >= M_ULS_oh

        overhang_lines = [
            "",
            "Deck Overhang Design",
            "-" * 40,
            f"  Overhang length L<sub>oh</sub> : {overhang_m * 1000:.0f} mm  ({overhang_m:.3f} m)",
            f"  Edge clearance f      : {f_edge:.3f} m  [IRC 6:2017 Table 3]",
            f"  Railing DL load       : {railing_kN_m:.3f} kN/m  [IRC 6:2017 Cl.206.5]",
            f"  Crash barrier moment  : {M_barrier_kNm:.2f} kNm/m  [IRC 6:2017 Cl.206.6]",
            f"  Wheel arm from root   : {arm_wheel:.3f} m",
            f"  M<sub>DL</sub> (overhang)       : {M_DL_oh:.3f} kNm/m  (slab {M_DL_slab_oh:.3f} + railing {M_DL_railing_oh:.3f})",
            f"  M<sub>LL</sub> (overhang)       : {M_LL_oh:.3f} kNm/m",
            f"  M<sub>ULS</sub> (overhang)      : {M_ULS_oh:.3f} kNm/m",
            "",
            "Overhang Top Reinforcement",
            "-" * 40,
            f"  Effective depth d     : {d_oh_mm:.1f} mm",
            f"  As required           : {As_req_oh:.0f} mm²/m",
            f"  Provided              : Ø{dia_oh:.0f} @ {spc_oh:.0f} mm c/c  →  {As_oh:.0f} mm²/m",
            f"  Moment capacity M<sub>u</sub>    : {Mu_oh:.3f} kNm/m",
            f"  Status                : {'PASS' if oh_ok else 'FAIL'}",
        ]
    else:
        f_edge = railing_kN_m = M_barrier_kNm = 0.0
        M_DL_oh = M_LL_oh = M_ULS_oh = arm_wheel = 0.0
        dia_oh = spc_oh = As_oh = As_req_oh = d_oh_mm = Mu_oh = 0.0
        oh_ok = True
        overhang_lines = []

    # ── 10b. shear checks (IRC 112:2020 Cl.10.3.2 & Cl.10.4) ────────────────
    # One-way shear — interior span, conservative: shear at support face.
    V_DL_kN_m = w_DL_kN_m2 * S / 2.0
    V_LL_kN_m = P_wheel_kN / beff_m
    V_ULS_bot_shear = gamma_dl * V_DL_kN_m + gamma_ll * impact_factor * V_LL_kN_m
    v_Rd_c_bot = _v_Rd_c_MPa(As_bot, d_bot_mm, fck)        # MPa
    VRd_c_bot = v_Rd_c_bot * d_bot_mm                       # kN/m (b_w = 1000 mm)
    shear_bot_ok = VRd_c_bot >= V_ULS_bot_shear
    ur_bot_shear = V_ULS_bot_shear / VRd_c_bot if VRd_c_bot > 0 else 9.999

    # Punching shear — wheel on interior slab (load dispersed through wearing course)
    # ULS design wheel load: γ_LL × impact factor × characteristic wheel load (IRC 112 Cl.10.4).
    P_wheel_uls_kN = gamma_ll * impact_factor * P_wheel_kN
    wc_t_mm = wc_t_m * 1000.0
    c1_mm = _wheel_contact_width_m(vehicle_class) * 1000.0 + 2.0 * wc_t_mm   # transverse
    c2_mm = _wheel_contact_length_mm(vehicle_class) + 2.0 * wc_t_mm           # longitudinal
    u1_bot_mm = 2.0 * (c1_mm + c2_mm) + 4.0 * math.pi * d_bot_mm
    v_Ed_bot_punch = P_wheel_uls_kN * 1000.0 / (u1_bot_mm * d_bot_mm)
    punch_bot_ok = v_Rd_c_bot >= v_Ed_bot_punch
    ur_bot_punch = v_Ed_bot_punch / v_Rd_c_bot if v_Rd_c_bot > 0 else 9.999

    # Shear checks — overhang cantilever at root
    if overhang_m > 0.01:
        V_DL_oh_v = w_DL_kN_m2 * overhang_m + railing_kN_m
        V_LL_oh_v = P_wheel_kN / beff_oh if arm_wheel > 0.0 else 0.0
        V_ULS_oh_shear = gamma_dl * V_DL_oh_v + gamma_ll * impact_factor * V_LL_oh_v
        v_Rd_c_oh = _v_Rd_c_MPa(As_oh, d_oh_mm, fck)
        VRd_c_oh = v_Rd_c_oh * d_oh_mm
        shear_oh_ok = VRd_c_oh >= V_ULS_oh_shear
        ur_oh_shear = V_ULS_oh_shear / VRd_c_oh if VRd_c_oh > 0 else 9.999
        u1_oh_mm = 2.0 * (c1_mm + c2_mm) + 4.0 * math.pi * d_oh_mm
        v_Ed_oh_punch = P_wheel_uls_kN * 1000.0 / (u1_oh_mm * d_oh_mm)
        punch_oh_ok = v_Rd_c_oh >= v_Ed_oh_punch
        ur_oh_punch = v_Ed_oh_punch / v_Rd_c_oh if v_Rd_c_oh > 0 else 9.999
        overhang_shear_lines = [
            "",
            "Shear Check — Overhang  [IRC 112:2020 Cl.10.3.2]",
            "-" * 40,
            f"  V<sub>ULS</sub> (one-way) at root : {V_ULS_oh_shear:.3f} kN/m",
            f"  V<sub>RD</sub>,c (no links)        : {VRd_c_oh:.3f} kN/m  → {'PASS' if shear_oh_ok else 'FAIL'}",
            "",
            "Punching Shear — Overhang  [IRC 112:2020 Cl.10.4]",
            "-" * 40,
            f"  Control perimeter u1    : {u1_oh_mm:.0f} mm  (at 2d = {2*d_oh_mm:.0f} mm)",
            f"  v<sub>ED</sub>                    : {v_Ed_oh_punch:.4f} MPa",
            f"  v<sub>RD</sub>,c                   : {v_Rd_c_oh:.4f} MPa  → {'PASS' if punch_oh_ok else 'FAIL'}",
        ]
    else:
        V_ULS_oh_shear = VRd_c_oh = ur_oh_shear = ur_oh_punch = 0.0
        shear_oh_ok = punch_oh_ok = True
        overhang_shear_lines = []

    shear_lines = [
        "",
        "=" * 52,
        "Shear Checks  (IRC 112:2020)",
        "=" * 52,
        "",
        "One-Way Shear — Interior Span  [Cl.10.3.2]",
        "-" * 40,
        f"  V<sub>DL</sub> at support         : {V_DL_kN_m:.3f} kN/m",
        f"  V<sub>LL</sub> at support         : {V_LL_kN_m:.3f} kN/m",
        f"  V<sub>ULS</sub>          : {V_ULS_bot_shear:.3f} kN/m",
        f"  V<sub>RD</sub>,c (no links)        : {VRd_c_bot:.3f} kN/m  → {'PASS' if shear_bot_ok else 'FAIL'}",
        "",
        "Punching Shear — Interior Span  [Cl.10.4]",
        "-" * 40,
        f"  Effective contact c1    : {c1_mm:.0f} mm  (transverse, incl. WC dispersion)",
        f"  Effective contact c2    : {c2_mm:.0f} mm  (longitudinal, incl. WC dispersion)",
        f"  Control perimeter u1    : {u1_bot_mm:.0f} mm  (at 2d = {2*d_bot_mm:.0f} mm)",
        f"  v<sub>ED</sub>                    : {v_Ed_bot_punch:.4f} MPa",
        f"  v<sub>RD</sub>,c                   : {v_Rd_c_bot:.4f} MPa  → {'PASS' if punch_bot_ok else 'FAIL'}",
        *overhang_shear_lines,
    ]

    # ── 10c. composite steel–concrete interface checks  [IRC 22:2015 Cl.606.10
    #         transverse shear, Cl.604.4 crack control] ──────────────────────────
    # Run with the deck-designed reinforcement (As_bot/As_top). Needs the steel
    # girder's beff / VL from the Stage-5 DCR run (design_results); when present the
    # check values are written back into design_results in place (report /
    # generate-results tables). Crack control uses the slab **top** (tension-face)
    # steel, not the longitudinal distribution steel. Skipped if beff/VL are absent.
    dr = design_results
    has_composite = bool(dr and dr.get("beff_mm") and dr.get("VL_N_per_mm") is not None)
    if has_composite:
        beff_comp_mm = dr["beff_mm"]
        VL           = dr["VL_N_per_mm"]

        ts = transverse_shear_check(
            VL_N_per_mm=VL, fck_MPa=fck, fy_rebar_MPa=fy,
            bf_top_mm=bf_top_mm, stud_height_mm=stud_height_mm, t_slab_mm=deck_t_mm,
            As_total_mm2=As_bot + As_top,
        )
        crack = crack_control_As_min(
            beff_mm=beff_comp_mm, fctm_MPa=fctm, fy_rebar_MPa=fy, t_slab_mm=deck_t_mm,
            As_total_mm2=As_top * beff_comp_mm / 1000.0,
        )

        dr["transverse_shear_ok"]    = ts["check_ok"]
        dr["Ast_required_cm2_per_m"] = ts["min_Ast_required_cm2_per_m"]
        dr["Ast_provided_cm2_per_m"] = ts["Ast_provided_cm2_per_m"]
        dr[KEY_SD_TS_VL]         = ts["VL_N_per_mm"]
        dr[KEY_SD_TS_VCAP_CONC]  = ts["Vcap1_kN_per_m"]
        dr[KEY_SD_TS_VCAP_REINF] = ts["Vcap2_kN_per_m"]
        dr[KEY_SD_TS_VRD]        = ts["governing_capacity_kN_per_m"]

        dr["As_min_crack_mm2"]      = crack["As_min_mm2"]
        dr["As_provided_crack_mm2"] = crack["As_provided_mm2"]
        dr[KEY_SD_CRACK_AS_MIN]  = crack["As_min_mm2"]
        dr[KEY_SD_CRACK_AS_PROV] = crack["As_provided_mm2"]
    else:
        print("  [INFO] composite interface checks skipped — beff/VL not in design_results.")

    # ── 11. SLS checks (IRC 112:2020) ────────────────────────────────────────
    # Characteristic combination (stress, Cl.12.2.1): γ_DL=1.0, γ_LL=1.0
    # Frequent combination    (crack width, Cl.12.3.4): γ_DL=1.0, γ_LL=0.75
    M_SLS_char_bot = M_DL_kNm + impact_factor * M_LL_kNm
    M_SLS_char_top = 0.75 * M_SLS_char_bot
    M_SLS_freq_bot = M_DL_kNm + 0.75 * impact_factor * M_LL_kNm
    M_SLS_freq_top = 0.75 * M_SLS_freq_bot

    sc_bot = _sls_stress(M_SLS_char_bot, As_bot, d_bot_mm, fck, fy, Es, Ecm)
    sc_top = _sls_stress(M_SLS_char_top, As_top, d_top_mm, fck, fy, Es, Ecm)
    cw_bot = _sls_crack_width(M_SLS_freq_bot, As_bot, dia_bot, d_bot_mm,
                               deck_t_mm, cover_bot_mm, fctm, Es, Ecm)
    cw_top = _sls_crack_width(M_SLS_freq_top, As_top, dia_top, d_top_mm,
                               deck_t_mm, cover_top_mm, fctm, Es, Ecm)

    if overhang_m > 0.01:
        M_SLS_char_oh = M_DL_oh + impact_factor * M_LL_oh + M_barrier_kNm
        M_SLS_freq_oh = M_DL_oh + 0.75 * (impact_factor * M_LL_oh + M_barrier_kNm)
        sc_oh  = _sls_stress(M_SLS_char_oh, As_oh, d_oh_mm, fck, fy, Es, Ecm)
        cw_oh  = _sls_crack_width(M_SLS_freq_oh, As_oh, dia_oh, d_oh_mm,
                                   deck_t_mm, cover_top_mm, fctm, Es, Ecm)
        overhang_sls_lines = [
            "",
            "Overhang SLS Stress Check  [IRC 112:2020 Cl.12.2.1]",
            "-" * 40,
            f"  M<sub>SLS</sub>,char (overhang) : {M_SLS_char_oh:.3f} kNm/m  (γ_DL=1.0, γ_LL=1.0)",
            f"  Concrete σ<sub>c</sub>          : {sc_oh['sigma_c']:.2f} MPa  ≤ {sc_oh['sc_lim']:.1f} MPa  → {'PASS' if sc_oh['sc_ok'] else 'FAIL'}",
            f"  Steel σ<sub>s</sub>              : {sc_oh['sigma_s']:.2f} MPa  ≤ {sc_oh['ss_lim']:.1f} MPa  → {'PASS' if sc_oh['ss_ok'] else 'FAIL'}",
            "",
            "Overhang Crack Width Check  [IRC 112:2020 Cl.12.3.4]",
            "-" * 40,
            f"  M<sub>SLS</sub>,freq (overhang) : {M_SLS_freq_oh:.3f} kNm/m  (γ_DL=1.0, γ_LL=0.75)",
            f"  Steel stress σ<sub>s</sub>      : {cw_oh['sigma_s']:.2f} MPa",
            f"  ρ<sub>p,eff</sub>                : {cw_oh['rho_p_eff']:.5f}",
            f"  Crack spacing S<sub>r,max</sub> : {cw_oh['Sr_max']:.1f} mm",
            f"  Strain diff ε<sub>sm</sub> − ε<sub>cm</sub>  : {cw_oh['eps_diff']:.3e}",
            f"  Crack width w<sub>k</sub>       : {cw_oh['wk']:.4f} mm  ≤ {cw_oh['wk_lim']:.1f} mm  → {'PASS' if cw_oh['ok'] else 'FAIL'}",
        ]
    else:
        overhang_sls_lines = []

    # ── utilization ratios (demand / capacity) ────────────────────────────────
    ur_bot_uls = M_ULS_bot_kNm / Mu_bot if Mu_bot > 0 else 9.999
    ur_top_uls = M_ULS_top_kNm / Mu_top if Mu_top > 0 else 9.999
    ur_bot_sls_c = sc_bot["sigma_c"] / sc_bot["sc_lim"]
    ur_bot_sls_s = sc_bot["sigma_s"] / sc_bot["ss_lim"]
    ur_top_sls_c = sc_top["sigma_c"] / sc_top["sc_lim"]
    ur_top_sls_s = sc_top["sigma_s"] / sc_top["ss_lim"]
    ur_bot_crack = cw_bot["wk"] / cw_bot["wk_lim"]
    ur_top_crack = cw_top["wk"] / cw_top["wk_lim"]

    # Composite interface utilization ratios (demand / capacity) — only when the
    # composite checks ran. Concrete / rebar SLS-stress URs are read back from
    # design_results (computed in Stage 5).
    if has_composite:
        def _ur(demand, capacity):
            return round(demand / capacity, 3) if capacity else 0.0
        ur_composite_trans_shear  = _ur(ts["VL_N_per_mm"], ts["governing_capacity_kN_per_m"])
        ur_composite_crack        = _ur(crack["As_min_mm2"], crack["As_provided_mm2"])
        ur_composite_conc_stress  = _ur(dr.get("sigma_c_actual_MPa") or 0.0,
                                        dr.get("sigma_c_limit_MPa") or 0.0)
        ur_composite_rebar_stress = _ur(dr.get("sigma_rebar_actual_MPa") or 0.0,
                                        dr.get("sigma_rebar_limit_MPa") or 0.0)

    sls_lines = [
        "",
        "=" * 52,
        "SLS Checks  (IRC 112:2020)",
        "=" * 52,
        "",
        "Stress Check — Bottom (Sagging)  [Cl.12.2.1]",
        "-" * 40,
        f"  M<sub>SLS</sub>,char (sagging)  : {M_SLS_char_bot:.3f} kNm/m  (γ<sub>DL</sub>=1.0, γ<sub>LL</sub>=1.0)",
        f"  Neutral axis depth x  : {sc_bot['x']:.1f} mm",
        f"  Concrete σ<sub>c</sub>         : {sc_bot['sigma_c']:.2f} MPa  ≤ {sc_bot['sc_lim']:.1f} MPa  → {'PASS' if sc_bot['sc_ok'] else 'FAIL'}",
        f"  Steel σ<sub>s</sub>            : {sc_bot['sigma_s']:.2f} MPa  ≤ {sc_bot['ss_lim']:.1f} MPa  → {'PASS' if sc_bot['ss_ok'] else 'FAIL'}",
        "",
        "Stress Check — Top (Hogging)  [Cl.12.2.1]",
        "-" * 40,
        f"  M<sub>SLS</sub>,char (hogging)  : {M_SLS_char_top:.3f} kNm/m  (γ<sub>DL</sub>=1.0, γ<sub>LL</sub>=1.0)",
        f"  Concrete σ<sub>c</sub>           : {sc_top['sigma_c']:.2f} MPa  ≤ {sc_top['sc_lim']:.1f} MPa  → {'PASS' if sc_top['sc_ok'] else 'FAIL'}",
        f"  Steel σ<sub>s</sub>              : {sc_top['sigma_s']:.2f} MPa  ≤ {sc_top['ss_lim']:.1f} MPa  → {'PASS' if sc_top['ss_ok'] else 'FAIL'}",
        "",
        "Crack Width Check — Bottom (Sagging)  [Cl.12.3.4]",
        "-" * 40,
        f"  M<sub>SLS</sub>,freq (sagging)  : {M_SLS_freq_bot:.3f} kNm/m  (γ<sub>DL</sub>=1.0, γ<sub>LL</sub>=0.75)",
        f"  Steel stress σ<sub>s</sub>       : {cw_bot['sigma_s']:.2f} MPa",
        f"  ρ<sub>p,eff</sub>               : {cw_bot['rho_p_eff']:.5f}",
        f"  Crack spacing S<sub>r,max</sub>  : {cw_bot['Sr_max']:.1f} mm",
        f"  Strain diff ε<sub>sm</sub>−ε<sub>cm</sub>  : {cw_bot['eps_diff']:.3e}",
        f"  Crack width w<sub>k</sub>      : {cw_bot['wk']:.4f} mm  ≤ {cw_bot['wk_lim']:.1f} mm  → {'PASS' if cw_bot['ok'] else 'FAIL'}",
        "",
        "Crack Width Check — Top (Hogging)  [Cl.12.3.4]",
        "-" * 40,
        f"  M<sub>SLS</sub>,freq (hogging)  : {M_SLS_freq_top:.3f} kNm/m  (γ<sub>DL</sub>=1.0, γ<sub>LL</sub>=0.75)",
        f"  Steel stress σ<sub>s</sub>       : {cw_top['sigma_s']:.2f} MPa",
        f"  ρ<sub>p,eff</sub>              : {cw_top['rho_p_eff']:.5f}",
        f"  Crack spacing S<sub>r,max</sub>   : {cw_top['Sr_max']:.1f} mm",
        f"  Strain diff ε<sub>sm</sub>−ε<sub>cm</sub>  : {cw_top['eps_diff']:.3e}",
        f"  Crack width w<sub>k</sub>      : {cw_top['wk']:.4f} mm  ≤ {cw_top['wk_lim']:.1f} mm  → {'PASS' if cw_top['ok'] else 'FAIL'}",
        *overhang_sls_lines,
    ]

    # ── 12. design check report ───────────────────────────────────────────────
    lines = [
        "IRC 6:2017 Deck Slab Design Summary",
        "=" * 52,
        "",
        f"Governing vehicle      : {vehicle_class}",
        f"Impact factor (IF)     : {impact_factor:.3f}  [IRC 6:2017 Cl.208]",
        f"  (1 + {IF:.3f} for span {span_m:.1f} m)",
        f"γ<sub>DL</sub>  [Table B.2]      : {gamma_dl}",
        f"γ<sub>LL</sub>  [Table B.2]      : {gamma_ll}",
        "",
        f"Effective span (S)     : {S:.3f} m  (girder c/c)",
        f"Deck thickness         : {deck_t_mm:.0f} mm",
        f"Concrete               : {concrete_grade}  (f<sub>ck</sub> = {fck:.0f} MPa, f<sub>ctm</sub> = {fctm:.1f} MPa)",
        f"Reinforcement          : {rebar_grade}  (f<sub>y</sub> = {fy:.0f} MPa)",
        "",
        "Cover Adequacy  [IRC 112:2020 Table 14.2 — 100-yr service life]",
        "-" * 40,
        f"  Concrete grade        : {concrete_grade}  → Exposure: {cover_rec['exposure_condition']}",
        f"  Recommended min cover : {min_cover_rec_mm} mm",
        f"  Top cover provided    : {cover_top_mm:.0f} mm  → {'OK' if cover_top_ok else 'BELOW RECOMMENDED'}",
        f"  Bottom cover provided : {cover_bot_mm:.0f} mm  → {'OK' if cover_bot_ok else 'BELOW RECOMMENDED'}",
        "",
        "Interior Span Loads",
        "-" * 40,
        f"  Dead load (w<sub>DL</sub>)     : {w_DL_kN_m2:.2f} kN/m²",
        f"  Max wheel load (P)   : {P_wheel_kN:.1f} kN  [IRC 6:2017 Cl.204]",
        f"  Cross-bracing spacing : {cb_spacing_m:.3f} m  (b/l<sub>o</sub> = {cb_spacing_m/S:.2f})",
        f"  Effective width b<sub>e</sub> : {beff_m:.3f} m  [IRC 112:2020 Eq. B3.1, α<sub>e</sub> = {alpha_e:.2f}]",
        "",
        "Interior Span Design Moments",
        "-" * 40,
        f"  M<sub>DL</sub>                : {M_DL_kNm:.3f} kNm/m",
        f"  M<sub>LL</sub> (unfactored)    : {M_LL_kNm:.3f} kNm/m",
        f"  M<sub>ULS</sub> (sagging)      : {M_ULS_bot_kNm:.3f} kNm/m",
        f"  M<sub>ULS</sub> (hogging, 75%) : {M_ULS_top_kNm:.3f} kNm/m",
        "",
        "Bottom (Sagging) Reinforcement",
        "-" * 40,
        f"  Effective depth d    : {d_bot_mm:.1f} mm",
        f"  A<sub>s</sub> required          : {As_req_bot:.0f} mm²/m",
        f"  Provided             : Ø{dia_bot:.0f} @ {spc_bot:.0f} mm c/c  →  {As_bot:.0f} mm²/m",
        f"  Moment capacity M<sub>u</sub>  : {Mu_bot:.3f} kNm/m",
        f"  Status               : {'PASS' if bot_ok else 'FAIL'}",
        "",
        "Top (Hogging) Reinforcement",
        "-" * 40,
        f"  Effective depth d    : {d_top_mm:.1f} mm",
        f"  A<sub>s</sub> required          : {As_req_top:.0f} mm²/m",
        f"  Provided             : Ø{dia_top:.0f} @ {spc_top:.0f} mm c/c  →  {As_top:.0f} mm²/m",
        f"  Moment capacity M<sub>u</sub>   : {Mu_top:.3f} kNm/m",
        f"  Status               : {'PASS' if top_ok else 'FAIL'}",
        "",
        "Longitudinal (Distribution) Reinforcement  [IRC 112:2020 Cl.16.6.1]",
        "-" * 40,
        f"  20% of A<sub>s</sub>bot        : {0.20 * As_bot:.0f} mm²/m",
        f"  As required          : {As_req_long:.0f} mm²/m",
        f"  Provided             : Ø{dia_long:.0f} @ {spc_long:.0f} mm c/c  →  {As_long:.0f} mm²/m",
        *overhang_lines,
        *shear_lines,
        *sls_lines,
    ]
    design_check_text = "\n".join(lines)

    # ── 13. return dict keyed to DECK_DESIGN_SUMMARY_SCHEMA ──────────────────
    result = {
        # ── properties card ─────────────────────────────────────────────────
        "deck_grade"             : concrete_grade,
        "deck_thickness"         : f"{deck_t_mm:.0f}",
        "deck_overhang"          : f"{overhang_m * 1000:.0f}",
        "deck_exposure"          : cover_rec["exposure_condition"],
        "min_cover_recommended"  : str(min_cover_rec_mm),
        # ── bottom reinforcement (interior sagging) ─────────────────────────
        "rebar_bottom_yield"     : f"{fy:.0f}",
        "rebar_bottom_dia"       : f"{dia_bot:.0f}",
        "rebar_bottom_spacing"   : f"{spc_bot:.0f}",
        "rebar_bottom_cover"     : f"{cover_bot_mm:.0f}",
        "rebar_bottom_area"      : f"{As_bot:.0f}",
        # ── top reinforcement (interior hogging) ────────────────────────────
        "rebar_top_yield"        : f"{fy:.0f}",
        "rebar_top_dia"          : f"{dia_top:.0f}",
        "rebar_top_spacing"      : f"{spc_top:.0f}",
        "rebar_top_cover"        : f"{cover_top_mm:.0f}",
        "rebar_top_area"         : f"{As_top:.0f}",
        # ── longitudinal (distribution) reinforcement ────────────────────────
        "rebar_long_yield"       : f"{fy:.0f}",
        "rebar_long_dia"         : f"{dia_long:.0f}",
        "rebar_long_spacing"     : f"{spc_long:.0f}",
        "rebar_long_cover"       : f"{cover_bot_mm:.0f}",
        "rebar_long_area"        : f"{As_long:.0f}",
        # ── SLS stress demand / limit (interior) ────────────────────────────
        # Bottom & top fibre share one material limit (0.48 fck / 0.80 fyk).
        KEY_DD_STRESS_CONC_BOTTOM    : round(sc_bot["sigma_c"], 3),
        KEY_DD_STRESS_CONC_TOP       : round(sc_top["sigma_c"], 3),
        KEY_DD_STRESS_CONC_ALLOWABLE : round(sc_bot["sc_lim"],  3),
        KEY_DD_STRESS_REINF_BOTTOM   : round(sc_bot["sigma_s"], 3),
        KEY_DD_STRESS_REINF_TOP      : round(sc_top["sigma_s"], 3),
        KEY_DD_STRESS_REINF_ALLOWABLE: round(sc_bot["ss_lim"],  3),
        # ── crack width (interior, frequent combination) ─────────────────────
        KEY_DD_CRACK_WK_BOTTOM       : round(cw_bot["wk"], 4),
        KEY_DD_CRACK_WK_TOP          : round(cw_top["wk"], 4),
        KEY_DD_CRACK_WK_LIMIT        : cw_bot["wk_lim"],
        # ── utilization ratios (interior) ────────────────────────────────────
        "ur_bot_uls"             : round(ur_bot_uls, 3),
        "ur_top_uls"             : round(ur_top_uls, 3),
        "ur_bot_sls_c"           : round(ur_bot_sls_c, 3),
        "ur_bot_sls_s"           : round(ur_bot_sls_s, 3),
        "ur_top_sls_c"           : round(ur_top_sls_c, 3),
        "ur_top_sls_s"           : round(ur_top_sls_s, 3),
        "ur_bot_crack"           : round(ur_bot_crack, 3),
        "ur_top_crack"           : round(ur_top_crack, 3),
        "ur_bot_shear"           : round(ur_bot_shear, 3),
        "ur_bot_punch"           : round(ur_bot_punch, 3),
        # ── design check report text ────────────────────────────────────────
        "deck_design_check"      : design_check_text,
    }
    if overhang_m > 0.01:
        result.update({
            # ── overhang reinforcement ──────────────────────────────────────
            "rebar_overhang_yield"   : f"{fy:.0f}",
            "rebar_overhang_dia"     : f"{dia_oh:.0f}",
            "rebar_overhang_spacing" : f"{spc_oh:.0f}",
            "rebar_overhang_cover"   : f"{cover_top_mm:.0f}",
            "rebar_overhang_area"    : f"{As_oh:.0f}",
            # ── overhang utilization ratios ─────────────────────────────────
            "ur_oh_uls"              : round(M_ULS_oh / Mu_oh if Mu_oh > 0 else 9.999, 3),
            "ur_oh_sls_c"            : round(sc_oh["sigma_c"] / sc_oh["sc_lim"], 3),
            "ur_oh_sls_s"            : round(sc_oh["sigma_s"] / sc_oh["ss_lim"], 3),
            "ur_oh_crack"            : round(cw_oh["wk"] / cw_oh["wk_lim"], 3),
            "ur_oh_shear"            : round(ur_oh_shear, 3),
            "ur_oh_punch"            : round(ur_oh_punch, 3),
        })
    if has_composite:
        result.update({
            # ── composite steel–concrete interface utilization ratios ────────
            "ur_composite_trans_shear"  : ur_composite_trans_shear,
            "ur_composite_crack"        : ur_composite_crack,
            "ur_composite_conc_stress"  : ur_composite_conc_stress,
            "ur_composite_rebar_stress" : ur_composite_rebar_stress,
        })

    # Deck verdict — per-check PASS/FAIL dict (built from the URs above)
    result[KEY_DD_VERDICT] = collect_deck_verdict(result)

    # ── 14. report values dict (keyed to common.KEY_DD_*) ──────────────
    # Raw numeric values consumed by the report generator (Tables 5.17(a)-(g)),
    # stored separately from the UI-facing `result` dict above. Existing
    # computed values only — no new structural calculation.
    has_overhang = overhang_m > 0.01
    as_min_bot = _min_steel_mm2(fctm, fy, d_bot_mm)
    report_values = {
        # -- 5.17(a) loading & geometry --
        KEY_DD_VEHICLE        : vehicle_class,
        KEY_DD_IMPACT_FACTOR  : impact_factor,
        KEY_DD_GAMMA_DL       : gamma_dl,
        KEY_DD_GAMMA_LL       : gamma_ll,
        KEY_DD_SPAN           : S,
        KEY_DD_WDL            : w_DL_kN_m2,
        KEY_DD_WHEEL_LOAD     : P_wheel_kN,
        KEY_DD_TYRE_WIDTH     : _wheel_contact_width_m(vehicle_class),
        KEY_DD_FY             : fy,
        # -- 5.17(b) interior panel flexure --
        KEY_DD_M_DL           : M_DL_kNm,
        KEY_DD_M_LL           : M_LL_kNm,
        KEY_DD_M_ULS_SAG      : M_ULS_bot_kNm,
        KEY_DD_M_ULS_HOG      : M_ULS_top_kNm,
        KEY_DD_D_BOT          : d_bot_mm,
        KEY_DD_D_TOP          : d_top_mm,
        KEY_DD_MU_BOT         : Mu_bot,
        KEY_DD_MU_TOP         : Mu_top,
        KEY_DD_AS_REQ_BOT     : As_req_bot,
        KEY_DD_AS_REQ_TOP     : As_req_top,
        # -- 5.17(c) cantilever overhang flexure --
        KEY_DD_M_BARRIER      : M_barrier_kNm,
        KEY_DD_M_DL_OH        : M_DL_oh,
        KEY_DD_M_LL_OH        : M_LL_oh,
        KEY_DD_M_ULS_OH       : M_ULS_oh,
        KEY_DD_D_OH           : d_oh_mm,
        KEY_DD_MU_OH          : Mu_oh,
        KEY_DD_AS_REQ_OH      : As_req_oh,
        # -- 5.17(d) punching shear --
        KEY_DD_PUNCH_VED_KN   : P_wheel_uls_kN,
        KEY_DD_TYRE_LENGTH    : _wheel_contact_length_mm(vehicle_class),
        KEY_DD_PUNCH_C1       : c1_mm,
        KEY_DD_PUNCH_C2       : c2_mm,
        KEY_DD_PUNCH_U1       : u1_bot_mm,
        KEY_DD_PUNCH_VED      : v_Ed_bot_punch,
        KEY_DD_VRD_C_MPA      : v_Rd_c_bot,
        KEY_DD_PUNCH_OK       : punch_bot_ok,
        # -- 5.17(f) one-way (beam) shear --
        KEY_DD_SHEAR_VED      : V_ULS_bot_shear,
        KEY_DD_SHEAR_VRDC     : VRd_c_bot,
        KEY_DD_SHEAR_OK       : shear_bot_ok,
        # -- 5.17(e) crack width --
        KEY_DD_AS_MIN         : as_min_bot,
        KEY_DD_WK_BOT         : cw_bot["wk"],
        KEY_DD_WK_TOP         : cw_top["wk"],
        KEY_DD_WK_OH          : (cw_oh["wk"] if has_overhang else 0.0),
        KEY_DD_WK_LIMIT       : cw_bot["wk_lim"],
        # -- 5.17(g) reinforcement detailing (provided bars) --
        KEY_DD_DIA_BOT        : dia_bot,
        KEY_DD_SPC_BOT        : spc_bot,
        KEY_DD_AS_BOT         : As_bot,
        KEY_DD_DIA_TOP        : dia_top,
        KEY_DD_SPC_TOP        : spc_top,
        KEY_DD_AS_TOP         : As_top,
        KEY_DD_DIA_OH         : dia_oh,
        KEY_DD_SPC_OH         : spc_oh,
        KEY_DD_AS_OH          : As_oh,
        KEY_DD_AS_LONG        : As_long,
        KEY_DD_MIN_COVER      : min_cover_rec_mm,
        KEY_DD_COVER_OK       : (cover_top_ok and cover_bot_ok),
        KEY_DD_SPACING_MAX    : _SPACING_MAX_MM,
        KEY_DD_HAS_OVERHANG   : has_overhang,
    }

    return result, report_values
