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

from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
from osdagbridge.core.utils.codes.irc112_2019 import IRC112_2019
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
    KEY_DD_AS_MIN, KEY_DD_WK_BOT, KEY_DD_WK_TOP,
    KEY_DD_WK_OH, KEY_DD_WK_LIMIT, KEY_DD_DIA_BOT,
    KEY_DD_SPC_BOT, KEY_DD_AS_BOT, KEY_DD_DIA_TOP,
    KEY_DD_SPC_TOP, KEY_DD_AS_TOP, KEY_DD_DIA_OH,
    KEY_DD_SPC_OH, KEY_DD_AS_OH, KEY_DD_SPACING_MAX,
    KEY_DD_HAS_OVERHANG,
)

# ── constants ─────────────────────────────────────────────────────────────────
_STANDARD_DIAS_MM = [8, 10, 12, 16, 20, 25, 32]
_SPACING_MAX_MM = 300.0
_SPACING_MIN_MM = 75.0
_SPACING_ROUND_MM = 5.0               # round spacing down to nearest 5 mm


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
    # (0.87fy)²/(0.36 fck b) · As² - (0.87 fy d) · As + M = 0
    a = (0.87 * fy_MPa) ** 2 / (0.36 * fck_MPa * b_mm)
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


def _pick_rebar(As_req_mm2: float,
                dias: list = _STANDARD_DIAS_MM) -> tuple[float, float, float]:
    """
    Choose the smallest bar diameter from `dias` and round-down spacing
    such that As_provided ≥ As_req.
    Returns (dia_mm, spacing_mm, As_prov_mm2_per_m).
    `dias` is pre-filtered by KEY_DS_REINF_BOUNDS before this call.
    """
    for dia in dias:
        a_bar = math.pi * dia ** 2 / 4.0
        spacing = a_bar * 1000.0 / As_req_mm2
        spacing = min(spacing, _SPACING_MAX_MM)
        spacing = max(spacing, _SPACING_MIN_MM)
        # round down to nearest _SPACING_ROUND_MM
        spacing = math.floor(spacing / _SPACING_ROUND_MM) * _SPACING_ROUND_MM
        spacing = max(spacing, _SPACING_MIN_MM)
        As_prov = a_bar * 1000.0 / spacing
        if As_prov >= As_req_mm2:
            return dia, spacing, As_prov
    # largest allowed bar at minimum spacing
    dia = dias[-1]
    a_bar = math.pi * dia ** 2 / 4.0
    spacing = _SPACING_MIN_MM
    return dia, spacing, a_bar * 1000.0 / spacing


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


# ── main design function ──────────────────────────────────────────────────────

def design_deck_slab(input_dict: dict, fck: float, fctm: float, fy: float, Es: float, Ecm: float) -> tuple[dict, dict]:
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
    cb_spacing_m = float(inp.get(KEY_MP_CB_SPACING) or 3.0)  # longitudinal cross-bracing spacing (m)

    rebar_grade = str(inp[KEY_DS_REINF_MATERIAL]).strip()
    cover_top_mm = float(inp[KEY_DS_TOP_CLEAR_COVER])
    cover_bot_mm = float(inp[KEY_DS_BOTTOM_CLEAR_COVER])

    bounds = inp[KEY_DS_REINF_BOUNDS]
    # lower/upper may be None — an explicit "no bound", i.e. open at that end.
    lower_dia = int(bounds["lower"]) if bounds["lower"] is not None else _STANDARD_DIAS_MM[0]
    upper_dia = int(bounds["upper"]) if bounds["upper"] is not None else _STANDARD_DIAS_MM[-1]
    allowed_dias = [d for d in _STANDARD_DIAS_MM if lower_dia <= d <= upper_dia]

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
    As_req_bot = max(_required_steel_mm2(M_ULS_bot_kNm, fy, d_bot_mm, fck),
                     _min_steel_mm2(fctm, fy, d_bot_mm))
    dia_bot, spc_bot, As_bot = _pick_rebar(As_req_bot, allowed_dias)
    d_bot_mm = deck_t_mm - cover_bot_mm - dia_bot / 2.0   # refined with actual bar
    # Second pass — recheck with refined d to guard against d decreasing for larger bars
    As_req_bot2 = max(_required_steel_mm2(M_ULS_bot_kNm, fy, d_bot_mm, fck),
                      _min_steel_mm2(fctm, fy, d_bot_mm))
    if As_req_bot2 > As_bot:
        dia_bot, spc_bot, As_bot = _pick_rebar(As_req_bot2, allowed_dias)
        d_bot_mm = deck_t_mm - cover_bot_mm - dia_bot / 2.0

    # ── 8. design top (hogging) reinforcement ────────────────────────────────
    d_top_mm = deck_t_mm - cover_top_mm - 6.0
    As_req_top = max(_required_steel_mm2(M_ULS_top_kNm, fy, d_top_mm, fck),
                     _min_steel_mm2(fctm, fy, d_top_mm))
    dia_top, spc_top, As_top = _pick_rebar(As_req_top, allowed_dias)
    d_top_mm = deck_t_mm - cover_top_mm - dia_top / 2.0
    As_req_top2 = max(_required_steel_mm2(M_ULS_top_kNm, fy, d_top_mm, fck),
                      _min_steel_mm2(fctm, fy, d_top_mm))
    if As_req_top2 > As_top:
        dia_top, spc_top, As_top = _pick_rebar(As_req_top2, allowed_dias)
        d_top_mm = deck_t_mm - cover_top_mm - dia_top / 2.0

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

        # Crash barrier horizontal moment — IRC 6:2017 Cl.206.4
        barrier = IRC6_2017.cl_206_4_crash_barrier_load()
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
        As_req_oh = max(_required_steel_mm2(M_ULS_oh, fy, d_oh_mm, fck),
                        _min_steel_mm2(fctm, fy, d_oh_mm))
        dia_oh, spc_oh, As_oh = _pick_rebar(As_req_oh, allowed_dias)
        d_oh_mm = deck_t_mm - cover_top_mm - dia_oh / 2.0
        # Second pass — recheck with refined d (larger bars reduce d below d_init)
        As_req_oh2 = max(_required_steel_mm2(M_ULS_oh, fy, d_oh_mm, fck),
                         _min_steel_mm2(fctm, fy, d_oh_mm))
        if As_req_oh2 > As_oh:
            dia_oh, spc_oh, As_oh = _pick_rebar(As_req_oh2, allowed_dias)
            d_oh_mm = deck_t_mm - cover_top_mm - dia_oh / 2.0

        Mu_oh = _moment_capacity_kNm(fy, As_oh, d_oh_mm, fck)
        oh_ok = Mu_oh >= M_ULS_oh

        overhang_lines = [
            "",
            "Deck Overhang Design",
            "-" * 40,
            f"  Overhang length L_oh  : {overhang_m * 1000:.0f} mm  ({overhang_m:.3f} m)",
            f"  Edge clearance f      : {f_edge:.3f} m  [IRC 6:2017 Table 3]",
            f"  Railing DL load       : {railing_kN_m:.3f} kN/m  [IRC 6:2017 Cl.206.5]",
            f"  Crash barrier moment  : {M_barrier_kNm:.2f} kNm/m  [IRC 6:2017 Cl.206.4]",
            f"  Wheel arm from root   : {arm_wheel:.3f} m",
            f"  M_DL (overhang)       : {M_DL_oh:.3f} kNm/m  (slab {M_DL_slab_oh:.3f} + railing {M_DL_railing_oh:.3f})",
            f"  M_LL (overhang)       : {M_LL_oh:.3f} kNm/m",
            f"  M_ULS (overhang)      : {M_ULS_oh:.3f} kNm/m",
            "",
            "Overhang Top Reinforcement",
            "-" * 40,
            f"  Effective depth d     : {d_oh_mm:.1f} mm",
            f"  As required           : {As_req_oh:.0f} mm²/m",
            f"  Provided              : Ø{dia_oh:.0f} @ {spc_oh:.0f} mm c/c  →  {As_oh:.0f} mm²/m",
            f"  Moment capacity Mu    : {Mu_oh:.3f} kNm/m",
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
    wc_t_mm = wc_t_m * 1000.0
    c1_mm = _wheel_contact_width_m(vehicle_class) * 1000.0 + 2.0 * wc_t_mm   # transverse
    c2_mm = _wheel_contact_length_mm(vehicle_class) + 2.0 * wc_t_mm           # longitudinal
    u1_bot_mm = 2.0 * (c1_mm + c2_mm) + 4.0 * math.pi * d_bot_mm
    v_Ed_bot_punch = P_wheel_kN * 1000.0 / (u1_bot_mm * d_bot_mm)
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
        v_Ed_oh_punch = P_wheel_kN * 1000.0 / (u1_oh_mm * d_oh_mm)
        punch_oh_ok = v_Rd_c_oh >= v_Ed_oh_punch
        ur_oh_punch = v_Ed_oh_punch / v_Rd_c_oh if v_Rd_c_oh > 0 else 9.999
        overhang_shear_lines = [
            "",
            "Shear Check — Overhang  [IRC 112:2020 Cl.10.3.2]",
            "-" * 40,
            f"  V_ULS (one-way) at root : {V_ULS_oh_shear:.3f} kN/m",
            f"  VRd,c (no links)        : {VRd_c_oh:.3f} kN/m  → {'PASS' if shear_oh_ok else 'FAIL'}",
            "",
            "Punching Shear — Overhang  [IRC 112:2020 Cl.10.4]",
            "-" * 40,
            f"  Control perimeter u1    : {u1_oh_mm:.0f} mm  (at 2d = {2*d_oh_mm:.0f} mm)",
            f"  vEd                     : {v_Ed_oh_punch:.4f} MPa",
            f"  vRd,c                   : {v_Rd_c_oh:.4f} MPa  → {'PASS' if punch_oh_ok else 'FAIL'}",
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
        f"  V_DL at support         : {V_DL_kN_m:.3f} kN/m",
        f"  V_LL at support         : {V_LL_kN_m:.3f} kN/m",
        f"  V_ULS                   : {V_ULS_bot_shear:.3f} kN/m",
        f"  VRd,c (no links)        : {VRd_c_bot:.3f} kN/m  → {'PASS' if shear_bot_ok else 'FAIL'}",
        "",
        "Punching Shear — Interior Span  [Cl.10.4]",
        "-" * 40,
        f"  Effective contact c1    : {c1_mm:.0f} mm  (transverse, incl. WC dispersion)",
        f"  Effective contact c2    : {c2_mm:.0f} mm  (longitudinal, incl. WC dispersion)",
        f"  Control perimeter u1    : {u1_bot_mm:.0f} mm  (at 2d = {2*d_bot_mm:.0f} mm)",
        f"  vEd                     : {v_Ed_bot_punch:.4f} MPa",
        f"  vRd,c                   : {v_Rd_c_bot:.4f} MPa  → {'PASS' if punch_bot_ok else 'FAIL'}",
        *overhang_shear_lines,
    ]

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
            f"  M_SLS,char (overhang) : {M_SLS_char_oh:.3f} kNm/m  (γ_DL=1.0, γ_LL=1.0)",
            f"  Concrete σc           : {sc_oh['sigma_c']:.2f} MPa  ≤ {sc_oh['sc_lim']:.1f} MPa  → {'PASS' if sc_oh['sc_ok'] else 'FAIL'}",
            f"  Steel σs              : {sc_oh['sigma_s']:.2f} MPa  ≤ {sc_oh['ss_lim']:.1f} MPa  → {'PASS' if sc_oh['ss_ok'] else 'FAIL'}",
            "",
            "Overhang Crack Width Check  [IRC 112:2020 Cl.12.3.4]",
            "-" * 40,
            f"  M_SLS,freq (overhang) : {M_SLS_freq_oh:.3f} kNm/m  (γ_DL=1.0, γ_LL=0.75)",
            f"  Steel stress σs       : {cw_oh['sigma_s']:.2f} MPa",
            f"  ρp,eff                : {cw_oh['rho_p_eff']:.5f}",
            f"  Crack spacing Sr,max  : {cw_oh['Sr_max']:.1f} mm",
            f"  Strain diff εsm-εcm   : {cw_oh['eps_diff']:.3e}",
            f"  Crack width wk        : {cw_oh['wk']:.4f} mm  ≤ {cw_oh['wk_lim']:.1f} mm  → {'PASS' if cw_oh['ok'] else 'FAIL'}",
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

    sls_lines = [
        "",
        "=" * 52,
        "SLS Checks  (IRC 112:2020)",
        "=" * 52,
        "",
        "Stress Check — Bottom (Sagging)  [Cl.12.2.1]",
        "-" * 40,
        f"  M_SLS,char (sagging)  : {M_SLS_char_bot:.3f} kNm/m  (γ_DL=1.0, γ_LL=1.0)",
        f"  Neutral axis depth x  : {sc_bot['x']:.1f} mm",
        f"  Concrete σc           : {sc_bot['sigma_c']:.2f} MPa  ≤ {sc_bot['sc_lim']:.1f} MPa  → {'PASS' if sc_bot['sc_ok'] else 'FAIL'}",
        f"  Steel σs              : {sc_bot['sigma_s']:.2f} MPa  ≤ {sc_bot['ss_lim']:.1f} MPa  → {'PASS' if sc_bot['ss_ok'] else 'FAIL'}",
        "",
        "Stress Check — Top (Hogging)  [Cl.12.2.1]",
        "-" * 40,
        f"  M_SLS,char (hogging)  : {M_SLS_char_top:.3f} kNm/m  (γ_DL=1.0, γ_LL=1.0)",
        f"  Concrete σc           : {sc_top['sigma_c']:.2f} MPa  ≤ {sc_top['sc_lim']:.1f} MPa  → {'PASS' if sc_top['sc_ok'] else 'FAIL'}",
        f"  Steel σs              : {sc_top['sigma_s']:.2f} MPa  ≤ {sc_top['ss_lim']:.1f} MPa  → {'PASS' if sc_top['ss_ok'] else 'FAIL'}",
        "",
        "Crack Width Check — Bottom (Sagging)  [Cl.12.3.4]",
        "-" * 40,
        f"  M_SLS,freq (sagging)  : {M_SLS_freq_bot:.3f} kNm/m  (γ_DL=1.0, γ_LL=0.75)",
        f"  Steel stress σs       : {cw_bot['sigma_s']:.2f} MPa",
        f"  ρp,eff                : {cw_bot['rho_p_eff']:.5f}",
        f"  Crack spacing Sr,max  : {cw_bot['Sr_max']:.1f} mm",
        f"  Strain diff εsm-εcm   : {cw_bot['eps_diff']:.3e}",
        f"  Crack width wk        : {cw_bot['wk']:.4f} mm  ≤ {cw_bot['wk_lim']:.1f} mm  → {'PASS' if cw_bot['ok'] else 'FAIL'}",
        "",
        "Crack Width Check — Top (Hogging)  [Cl.12.3.4]",
        "-" * 40,
        f"  M_SLS,freq (hogging)  : {M_SLS_freq_top:.3f} kNm/m  (γ_DL=1.0, γ_LL=0.75)",
        f"  Steel stress σs       : {cw_top['sigma_s']:.2f} MPa",
        f"  ρp,eff                : {cw_top['rho_p_eff']:.5f}",
        f"  Crack spacing Sr,max  : {cw_top['Sr_max']:.1f} mm",
        f"  Strain diff εsm-εcm   : {cw_top['eps_diff']:.3e}",
        f"  Crack width wk        : {cw_top['wk']:.4f} mm  ≤ {cw_top['wk_lim']:.1f} mm  → {'PASS' if cw_top['ok'] else 'FAIL'}",
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
        f"γ_DL  [Table B.2]      : {gamma_dl}",
        f"γ_LL  [Table B.2]      : {gamma_ll}",
        "",
        f"Effective span (S)     : {S:.3f} m  (girder c/c)",
        f"Deck thickness         : {deck_t_mm:.0f} mm",
        f"Concrete               : {concrete_grade}  (fck = {fck:.0f} MPa, fctm = {fctm:.1f} MPa)",
        f"Reinforcement          : {rebar_grade}  (fy = {fy:.0f} MPa)",
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
        f"  Dead load (w_DL)     : {w_DL_kN_m2:.2f} kN/m²",
        f"  Max wheel load (P)   : {P_wheel_kN:.1f} kN  [IRC 6:2017 Cl.204]",
        f"  Cross-bracing spacing : {cb_spacing_m:.3f} m  (b/l_o = {cb_spacing_m/S:.2f})",
        f"  Effective width beff : {beff_m:.3f} m  [IRC 112:2020 Eq. B3.1, α_e={alpha_e:.2f}]",
        "",
        "Interior Span Design Moments",
        "-" * 40,
        f"  M_DL                 : {M_DL_kNm:.3f} kNm/m",
        f"  M_LL (unfactored)    : {M_LL_kNm:.3f} kNm/m",
        f"  M_ULS (sagging)      : {M_ULS_bot_kNm:.3f} kNm/m",
        f"  M_ULS (hogging, 75%) : {M_ULS_top_kNm:.3f} kNm/m",
        "",
        "Bottom (Sagging) Reinforcement",
        "-" * 40,
        f"  Effective depth d    : {d_bot_mm:.1f} mm",
        f"  As required          : {As_req_bot:.0f} mm²/m",
        f"  Provided             : Ø{dia_bot:.0f} @ {spc_bot:.0f} mm c/c  →  {As_bot:.0f} mm²/m",
        f"  Moment capacity Mu   : {Mu_bot:.3f} kNm/m",
        f"  Status               : {'PASS' if bot_ok else 'FAIL'}",
        "",
        "Top (Hogging) Reinforcement",
        "-" * 40,
        f"  Effective depth d    : {d_top_mm:.1f} mm",
        f"  As required          : {As_req_top:.0f} mm²/m",
        f"  Provided             : Ø{dia_top:.0f} @ {spc_top:.0f} mm c/c  →  {As_top:.0f} mm²/m",
        f"  Moment capacity Mu   : {Mu_top:.3f} kNm/m",
        f"  Status               : {'PASS' if top_ok else 'FAIL'}",
        "",
        "Longitudinal (Distribution) Reinforcement  [IRC 112:2020 Cl.16.6.1]",
        "-" * 40,
        f"  20% of As_bot        : {0.20 * As_bot:.0f} mm²/m",
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
        KEY_DD_SPACING_MAX    : _SPACING_MAX_MM,
        KEY_DD_HAS_OVERHANG   : has_overhang,
    }
    return result, report_values
