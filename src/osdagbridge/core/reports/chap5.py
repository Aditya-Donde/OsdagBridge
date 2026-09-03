# =============================================================================
# Chapter 5: Design Checks
# Extracted from report_generator.py — DO NOT add business logic here.
# =============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING

from osdagbridge.core.utils.common import (
    KEY_DD_AS_BOT,
    KEY_DD_AS_LONG,
    KEY_DD_AS_MIN,
    KEY_DD_AS_OH,
    KEY_DD_AS_REQ_BOT,
    KEY_DD_AS_REQ_OH,
    KEY_DD_AS_REQ_TOP,
    KEY_DD_AS_TOP,
    KEY_DD_COVER_OK,
    KEY_DD_DIA_BOT,
    KEY_DD_DIA_OH,
    KEY_DD_D_BOT,
    KEY_DD_D_OH,
    KEY_DD_FY,
    KEY_DD_GAMMA_DL,
    KEY_DD_GAMMA_LL,
    KEY_DD_HAS_OVERHANG,
    KEY_DD_IMPACT_FACTOR,
    KEY_DD_MIN_COVER,
    KEY_DD_MU_BOT,
    KEY_DD_MU_OH,
    KEY_DD_MU_TOP,
    KEY_DD_M_BARRIER,
    KEY_DD_M_DL,
    KEY_DD_M_DL_OH,
    KEY_DD_M_LL,
    KEY_DD_M_LL_OH,
    KEY_DD_M_ULS_HOG,
    KEY_DD_M_ULS_OH,
    KEY_DD_M_ULS_SAG,
    KEY_DD_PUNCH_C1,
    KEY_DD_PUNCH_C2,
    KEY_DD_PUNCH_OK,
    KEY_DD_PUNCH_U1,
    KEY_DD_PUNCH_VED,
    KEY_DD_PUNCH_VED_KN,
    KEY_DD_SHEAR_OK,
    KEY_DD_SHEAR_VED,
    KEY_DD_SHEAR_VRDC,
    KEY_DD_SPACING_MAX,
    KEY_DD_SPAN,
    KEY_DD_SPC_BOT,
    KEY_DD_SPC_OH,
    KEY_DD_TYRE_LENGTH,
    KEY_DD_TYRE_WIDTH,
    KEY_DD_VEHICLE,
    KEY_DD_VRD_C_MPA,
    KEY_DD_WDL,
    KEY_DD_WHEEL_LOAD,
    KEY_DD_WK_BOT,
    KEY_DD_WK_LIMIT,
    KEY_DD_WK_OH,
    KEY_DD_WK_TOP,
    KEY_DECK_CONCRETE_GRADE_BASIC,
    KEY_DESIGN_MODE,
    KEY_DS_BOTTOM_CLEAR_COVER,
    KEY_DS_REINF_MATERIAL,
    KEY_DS_STUD_DIAMETER,
    KEY_DS_TOP_CLEAR_COVER,
    KEY_MATERIAL_DECK_FCK,
    KEY_MATERIAL_DECK_FCTM,
    KEY_MATERIAL_GIRDER_E,
    KEY_MATERIAL_GIRDER_G,
    KEY_MP_ED_TYPE,
    KEY_SD_BOTTOM_FLANGE_THICKNESS,
    KEY_SD_BOTTOM_FLANGE_WIDTH,
    KEY_SD_BS_FCD,
    KEY_SD_BS_FCDW_LC,
    KEY_SD_BS_FCDW_WB,
    KEY_SD_BS_FPSD,
    KEY_SD_BS_R,
    KEY_SD_CLASS_FLANGE,
    KEY_SD_CLASS_WEB,
    KEY_SD_COMPOSITE_IZ,
    KEY_SD_DEFL_LIVE,
    KEY_SD_DEFL_TOTAL,
    KEY_SD_EFFECTIVE_SLAB_WIDTH,
    KEY_SD_FATIGUE_FFD_MPA,
    KEY_SD_FATIGUE_FF_MPA,
    KEY_DO_GAMMA_MF,
    KEY_SD_FATIGUE_MU_R,
    KEY_SD_FATIGUE_STRESS_RANGE_MPA,
    KEY_SD_FLANGE_CLASS_LIMIT,
    KEY_SD_FLANGE_SLENDERNESS,
    KEY_SD_HIGH_SHEAR,
    KEY_SD_IS_FQ,
    KEY_SD_IS_FQD,
    KEY_SD_IS_IYS_MIN,
    KEY_SD_IS_IYS_PROV,
    KEY_SD_LTB_CHI,
    KEY_SD_LTB_LAMBDA,
    KEY_SD_LTB_LLT,
    KEY_SD_LTB_MB,
    KEY_SD_LTB_MCR,
    KEY_SD_LTB_MP,
    KEY_SD_MDV,
    KEY_SD_MD_CAPACITY,
    KEY_SD_MN_AXIAL,
    KEY_SD_MN_MOMENT,
    KEY_SD_MN_RATIO,
    KEY_SD_MU_APPLIED,
    KEY_SD_PANEL_CD,
    KEY_SD_PNA_DEPTH,
    KEY_SD_SC_D_LIMIT,
    KEY_SD_SC_EDGE_DIST,
    KEY_SD_SC_Qr_kN,
    KEY_SD_SC_Qu_kN,
    KEY_SD_SC_REQ_EDGE_DIST,
    KEY_SD_SC_SL1,
    KEY_SD_SC_SL2,
    KEY_SD_SC_SR,
    KEY_SD_SC_AEC_MM2,
    KEY_SD_SC_VR_PER_MM,
    KEY_SD_SC_H1_kN,
    KEY_SD_SC_H2_kN,
    KEY_SD_SC_SHEAR_SPAN,
    KEY_SD_SC_H_kN,
    KEY_SD_SC_Vr_kN,
    KEY_SD_SECTION_CLASS,
    KEY_SD_SECTION_PROP_AREA,
    KEY_SD_SECTION_PROP_IT,
    KEY_SD_SECTION_PROP_IV,
    KEY_SD_SECTION_PROP_IW,
    KEY_SD_SECTION_PROP_IZ,
    KEY_SD_SECTION_PROP_ZUZ,
    KEY_SD_SECTION_PROP_ZZ,
    KEY_SD_SHEAR_AV,
    KEY_SD_SHEAR_KV,
    KEY_SD_SHEAR_LAMBDA_W,
    KEY_SD_SHEAR_TAU_B,
    KEY_SD_SHEAR_VCR,
    KEY_SD_SHEAR_VU,
    KEY_SD_STIFF_END_COUNT,
    KEY_SD_STIFF_END_THICK,
    KEY_SD_STIFF_INT_SPACING,
    KEY_SD_STIFF_INT_THICK,
    KEY_SD_STIFF_LONG,
    KEY_SD_STIFF_METHOD,
    KEY_SD_STRESS_STEEL,
    KEY_SD_STRESS_STEEL_ALLOWABLE,
    KEY_SD_TOP_FLANGE_THICKNESS,
    KEY_SD_TOP_FLANGE_WIDTH,
    KEY_SD_TOTAL_DEPTH,
    KEY_SD_TS_VL,
    KEY_SD_TS_VRD,
    KEY_SD_TS_AEC,
    KEY_SD_TS_Y,
    KEY_SD_ULS_PER_GIRDER,
    KEY_SD_WEB_CLASS_LIMIT,
    KEY_SD_WEB_SLENDERNESS,
    KEY_SD_WEB_THICKNESS,
    KEY_SPAN,
    KEY_TS_DECK_OVERHANG,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_NO_OF_GIRDERS,
    KEY_UTIL_FLEXURE,
    KEY_UTIL_INTERACTION,
    KEY_UTIL_LTB,
    KEY_UTIL_SHEAR,
    KEY_VEHICLE,
)

from osdagbridge.core.reports.report_utils import _tex, _render_value, get_girder_entries

if TYPE_CHECKING:
    pass
def ch5_design_checks(checks_data, bridge) -> str:
    """Chapter 5 — Design Checks.

    Parameters
    ----------
    checks_data : dict
        Raw checks payload (currently unused; data is sourced from bridge).
    bridge : ReportDataBridge
        Provides input_dict, output_dict, and helper methods.
    """
    girder_entries = get_girder_entries(bridge.input_dict)
    if not girder_entries:
        n = int(bridge.input_dict.get(KEY_TS_NO_OF_GIRDERS, 1))
        girder_entries = [(f"Girder {i}", f"M1") for i in range(1, n + 1)]
    n_girders = len(girder_entries)

    # Deck slab design report values (Tables 5.17(a)-(g)), keyed to
    # common.KEY_DD_*. Populated by deckdesign.design_deck_slab(); empty
    # dict when deck design has not been run. Look up with deck_rpt.get(KEY_...).
    deck_rpt = bridge.output_dict.get("deck_report_values", {}) or {}

    # Generate Table 5.1 rows (per-girder section properties)
    t51_rows = []
    for lbl, _ in girder_entries:
        t51_rows.append(
            r"\multirow{13}{*}{\makecell{" + lbl + r"""}} & \textnormal{Depth, D (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_TOTAL_DEPTH) + r""" \\[6pt]
\cline{2-3}
 & \textnormal{Top Flange Width, $b_f$ (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_TOP_FLANGE_WIDTH) + r""" \\[6pt]
\cline{2-3}
 & \textnormal{Bottom Flange Width, $b_f$ (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_BOTTOM_FLANGE_WIDTH) + r""" \\[6pt]
\cline{2-3}
 & \textnormal{Top Flange Thickness, $t_f$ (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_TOP_FLANGE_THICKNESS) + r""" \\[6pt]
\cline{2-3}
 & \textnormal{Bottom Flange Thickness, $t_f$ (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_BOTTOM_FLANGE_THICKNESS) + r""" \\[6pt]
\cline{2-3}
 & \textnormal{Web Thickness, $t_w$ (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_WEB_THICKNESS) + r""" \\[6pt]
\cline{2-3}
 & \textnormal{Gross Area, A (cm$^2$)} & """ + _render_value(bridge.output_dict, KEY_SD_SECTION_PROP_AREA) + r""" \\[6pt]
\cline{2-3}
 & \textnormal{Moment of Inertia, $I_z$ (cm$^4$)} & """ + _render_value(bridge.output_dict, KEY_SD_SECTION_PROP_IZ) + r""" \\[6pt]
\cline{2-3}
 & \textnormal{Elastic Section Modulus, $Z_{ez}$ (cm$^3$)} & """ + _render_value(bridge.output_dict, KEY_SD_SECTION_PROP_ZZ) + r""" \\[6pt]
\cline{2-3}
 & \textnormal{Plastic Section Modulus, $Z_{pz}$ (cm$^3$)} & """ + _render_value(bridge.output_dict, KEY_SD_SECTION_PROP_ZUZ) + r""" \\[6pt]
\cline{2-3}
 & \textnormal{Effective Slab Width, $b_{eff}$ (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_EFFECTIVE_SLAB_WIDTH) + r""" \\[6pt]
\cline{2-3}
 & \textnormal{Transformed Composite $I_z$ (cm$^4$)} & """ + _render_value(bridge.output_dict, KEY_SD_COMPOSITE_IZ) + r""" \\[6pt]
\cline{2-3}
 & \textnormal{Depth to Plastic Neutral Axis (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_PNA_DEPTH) + r""" \\[6pt]
\hline"""
        )
    t51_content = "\n".join(t51_rows)

    # Generate Table 5.2 rows
    t52_rows = []
    for lbl, _ in girder_entries:
        t52_rows.append(
            r"\multirow{3}{*}{\makecell{" + lbl + r"""}} & Top Flange & """ + _render_value(bridge.output_dict, KEY_SD_FLANGE_SLENDERNESS) + r""" & """ + _render_value(bridge.output_dict, KEY_SD_FLANGE_CLASS_LIMIT) + r""" & """ + _render_value(bridge.output_dict, KEY_SD_CLASS_FLANGE) + r""" \\[6pt]
\cline{2-5}
 & Web & """ + _render_value(bridge.output_dict, KEY_SD_WEB_SLENDERNESS) + r""" & """ + _render_value(bridge.output_dict, KEY_SD_WEB_CLASS_LIMIT) + r""" & """ + _render_value(bridge.output_dict, KEY_SD_CLASS_WEB) + r""" \\[6pt]
\cline{2-5}
 & Overall Section & --- & --- & """ + _render_value(bridge.output_dict, KEY_SD_SECTION_CLASS) + r""" \\[6pt]
\hline"""
        )
    t52_content = "\n".join(t52_rows)

    # Generate Table 5.3 rows
    # Flexure UR is stored as a percent (cat_urs × 100); show as a ratio (÷100,
    # 2 dp) and PASS when ≤ 1.0.
    try:
        _flex_ur = float(bridge.output_dict.get(KEY_UTIL_FLEXURE)) / 100.0
        _flex_ur_str = f"{_flex_ur:.2f}"
        _flex_status = "PASS" if _flex_ur <= 1.0 else r"\textcolor{red}{FAIL}"
    except (TypeError, ValueError):
        _flex_ur_str = ""
        _flex_status = "---"
    t53_rows = []
    for lbl, _ in girder_entries:
        t53_rows.append(
            r"\multirow{3}{*}{\makecell{" + lbl + r"""}} & Applied Moment, $M_u$ & Governing LC (ULS) & """ + _render_value(bridge.output_dict, KEY_SD_MU_APPLIED, " kN-m") + r""" & --- \\[6pt]
\cline{2-5}
 & Design Moment Capacity, $M_d$ & IRC 22 Cl. 603.3.1 & """ + _render_value(bridge.output_dict, KEY_SD_MD_CAPACITY, " kN-m") + r""" & --- \\[6pt]
\cline{2-5}
 & Utilization Ratio, $M_u / M_d$ & $M_u / M_d$ & """ + _flex_ur_str + r""" & """ + _flex_status + r""" \\[6pt]
\hline"""
        )
    t53_content = "\n".join(t53_rows)

    # Generate Table 5.4 rows
    # Shear UR is stored as a percent (cat_urs × 100); show as a ratio (÷100,
    # 2 dp) and PASS when ≤ 1.0.
    try:
        _shear_ur = float(bridge.output_dict.get(KEY_UTIL_SHEAR)) / 100.0
        _shear_ur_str = f"{_shear_ur:.2f}"
        _shear_status = "PASS" if _shear_ur <= 1.0 else r"\textcolor{red}{FAIL}"
    except (TypeError, ValueError):
        _shear_ur_str = ""
        _shear_status = "---"
    t54_rows = []
    for lbl, _ in girder_entries:
        t54_rows.append(
            r"\multirow{8}{*}{\makecell{" + lbl + r"""}} & Applied Shear, $V_u$ & Governing LC (ULS) & """ + _render_value(bridge.output_dict, KEY_SD_SHEAR_VU, " kN") + r""" & --- \\[6pt]
\cline{2-5}
 & Shear Area, $A_v$ & $d_w \times t_w$ & """ + _render_value(bridge.output_dict, KEY_SD_SHEAR_AV, " mm$^2$") + r""" & --- \\[6pt]
\cline{2-5}
 & Panel Aspect Ratio, c/d & --- & """ + _render_value(bridge.output_dict, KEY_SD_PANEL_CD) + r""" & --- \\[6pt]
\cline{2-5}
 & Shear Buckling Coefficient, $k_v$ & IS 800 Cl. 8.4.2.2 & """ + _render_value(bridge.output_dict, KEY_SD_SHEAR_KV) + r""" & --- \\[6pt]
\cline{2-5}
 & Web Slenderness, $\lambda_w$ & $\sqrt{f_{yw}/(\sqrt{3}\,\tau_{cr})}$ & """ + _render_value(bridge.output_dict, KEY_SD_SHEAR_LAMBDA_W) + r""" & --- \\[6pt]
\cline{2-5}
 & Design Shear Stress, $\tau_b$ & IRC 22 Cl. 603.3.3.2 & """ + _render_value(bridge.output_dict, KEY_SD_SHEAR_TAU_B, " MPa") + r""" & --- \\[6pt]
\cline{2-5}
 & Shear Buckling Resistance, $V_{cr}$ & $A_v \times \tau_b$ & """ + _render_value(bridge.output_dict, KEY_SD_SHEAR_VCR, " kN") + r""" & --- \\[6pt]
\cline{2-5}
 & Utilization Ratio, $V_u / V_d$ & $V_u / V_d$ & """ + _shear_ur_str + r""" & """ + _shear_status + r""" \\[6pt]
\hline"""
        )
    t54_content = "\n".join(t54_rows)

    # Generate Table 5.5 rows
    # Interaction DCRs use the engine bands: PASS <0.90, WARN <1.00, FAIL ≥1.00.
    def _interaction_status(ratio):
        if ratio < 0.90:
            return "PASS"
        elif ratio < 1.00:
            return "WARN"
        return r"\textcolor{red}{FAIL}"
    # M-V interaction UR stored as percent → show ratio (2 dp).
    try:
        _mv_ur = float(bridge.output_dict.get(KEY_UTIL_INTERACTION)) / 100.0
        _mv_ur_str = f"{_mv_ur:.2f}"
        _mv_status = _interaction_status(_mv_ur)
    except (TypeError, ValueError):
        _mv_ur_str = ""
        _mv_status = "---"
    # M-N interaction: None → no axial load → N/A.
    _mn_r  = bridge.output_dict.get(KEY_SD_MN_RATIO)
    _mn_ax = bridge.output_dict.get(KEY_SD_MN_AXIAL)
    _mn_mo = bridge.output_dict.get(KEY_SD_MN_MOMENT)
    if _mn_r is None or _mn_ax is None or _mn_mo is None:
        _mn_cond = _mn_val = _mn_status = "N/A"
    else:
        _mn_cond   = f"{_mn_ax:.2f} + {_mn_mo:.2f} = {_mn_r:.3f}"
        _mn_val    = f"{_mn_r:.3f}"
        _mn_status = _interaction_status(_mn_r)
    t55_rows = []
    for lbl, _ in girder_entries:
        t55_rows.append(
            r"\multirow{4}{*}{\makecell{" + lbl + r"""}} & High Shear Condition? & $V_u > 0.6\,V_d$ & """ + _render_value(bridge.output_dict, KEY_SD_HIGH_SHEAR) + r""" & --- \\[6pt]
\cline{2-5}
 & Reduced Moment Capacity, $M_{dv}$ & IRC 22 Cl. 603.3.3.3 & """ + _render_value(bridge.output_dict, KEY_SD_MDV, " kN-m") + r""" & --- \\[6pt]
\cline{2-5}
 & Interaction Check: $M_u \leq M_{dv}$ & --- & """ + _mv_ur_str + r""" & """ + _mv_status + r""" \\[6pt]
\cline{2-5}
 & Interaction Check: $N_u/N_{Rd} + M_u/M_{dv} \leq 1.0$ & """ + _mn_cond + r""" & """ + _mn_val + r""" & """ + _mn_status + r""" \\[6pt]
\hline"""
        )
    t55_content = "\n".join(t55_rows)

    # Generate Table 5.6 rows
    # LTB UR stored as percent → show ratio (2 dp); engine bands via _interaction_status.
    try:
        _ltb_ur = float(bridge.output_dict.get(KEY_UTIL_LTB)) / 100.0
        _ltb_ur_str = f"{_ltb_ur:.2f}"
        _ltb_status = _interaction_status(_ltb_ur)
    except (TypeError, ValueError):
        _ltb_ur_str = ""
        _ltb_status = "---"

    def _render_scaled(source_dict, key, scale, nd, unit=""):
        v = source_dict.get(key)
        if v in ("", None):
            return ""
        return f"{float(v) * scale:.{nd}f}" + unit

    _iy_cm4_str = _render_scaled(bridge.output_dict, KEY_SD_SECTION_PROP_IV, 1e8, 1, " cm$^4$")
    _it_cm4_str = _render_scaled(bridge.output_dict, KEY_SD_SECTION_PROP_IT, 1e8, 1, " cm$^4$")
    _iw_cm6_str = _render_scaled(bridge.output_dict, KEY_SD_SECTION_PROP_IW, 1e12, 3, " cm$^6$")
    _g_mpa_str  = _render_scaled(bridge.input_dict,  KEY_MATERIAL_GIRDER_G, 1000.0, 1, " MPa")
    _e_mpa_str  = _render_scaled(bridge.input_dict,  KEY_MATERIAL_GIRDER_E, 1000.0, 1, " MPa, ")

    t56_rows = []
    for lbl, _ in girder_entries:
        t56_rows.append(
            r"\multirow{11}{*}{\makecell{" + lbl + r"""}} & Effective Unbraced Length, $L_{LT}$ & $\min(s_{cb},\,L_{span})$ & """ + _render_value(bridge.output_dict, KEY_SD_LTB_LLT, " m") + r""" & --- \\[6pt]
\cline{2-5}
 & Minor-axis M.I., $I_y$ & $\sum t\,b^3/12$ & """ + _iy_cm4_str + r""" & --- \\[6pt]
\cline{2-5}
 & Torsional Constant, $J$ & $\sum b\,t^3/3$ & """ + _it_cm4_str + r""" & --- \\[6pt]
\cline{2-5}
 & Warping Constant, $I_w$ & $\dfrac{I_{y,tf}\,I_{y,bf}}{I_{y,tf}+I_{y,bf}}\,h_w^2$ & """ + _iw_cm6_str + r""" & --- \\[6pt]
\cline{2-5}
 & Elastic / Shear Modulus, $E$, $G$ & Material constants & """ + _e_mpa_str + _g_mpa_str + r""" & --- \\[6pt]
\cline{2-5}
 & Design Bending Strength, $M_p$ & IS 800 Cl. 8.2.1.2 & """ + _render_value(bridge.output_dict, KEY_SD_LTB_MP, " kN-m") + r""" & --- \\[6pt]
\cline{2-5}
 & Elastic Critical Moment, $M_{cr}$ & IRC 22 Cl. 603.3.3.1 & """ + _render_value(bridge.output_dict, KEY_SD_LTB_MCR, " kN-m") + r""" & --- \\[6pt]
\cline{2-5}
 & Non-dim. Slenderness, $\bar{\lambda}_{LT}$ & $\sqrt{M_p / M_{cr}}$ & """ + _render_value(bridge.output_dict, KEY_SD_LTB_LAMBDA) + r""" & --- \\[6pt]
\cline{2-5}
 & LTB Reduction Factor, $\chi_{LT}$ & IS 800 Cl. 8.2.2 & """ + _render_value(bridge.output_dict, KEY_SD_LTB_CHI) + r""" & --- \\[6pt]
\cline{2-5}
 & LTB Resistance, $M_b$ & $\chi_{LT}\,M_p$ & """ + _render_value(bridge.output_dict, KEY_SD_LTB_MB, " kN-m") + r""" & --- \\[6pt]
\cline{2-5}
 & $M_u \leq M_b$ & $M_u / M_b$ & """ + _ltb_ur_str + r""" & """ + _ltb_status + r""" \\[6pt]
\hline"""
        )
    t56_content = "\n".join(t56_rows)

    # Generate Table 5.7 rows
    t57_rows = []
    for lbl, _ in girder_entries:
        t57_rows.append(
            r"\multirow{6}{*}{\makecell{" + lbl + r"""}} & \textnormal{Shear Buckling Design Method} & """ + str(_render_value(bridge.output_dict, KEY_SD_STIFF_METHOD)).replace("_", " ").title() + r""" \\[6pt]
\cline{2-3}
 & \textnormal{Intermediate Stiffener Thickness (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_STIFF_INT_THICK) + r""" \\[6pt]
\cline{2-3}
 & \textnormal{Intermediate Stiffener Spacing (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_STIFF_INT_SPACING) + r""" \\[6pt]
\cline{2-3}
 & \textnormal{End Panel Stiffener Thickness (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_STIFF_END_THICK) + r""" \\[6pt]
\cline{2-3}
 & \textnormal{No. of End Panel Stiffeners} & """ + _render_value(bridge.output_dict, KEY_SD_STIFF_END_COUNT) + r""" \\[6pt]
\cline{2-3}
 & \textnormal{Longitudinal Stiffeners} & """ + _render_value(bridge.output_dict, KEY_SD_STIFF_LONG) + r""" \\[6pt]
\hline"""
        )
    t57_content = "\n".join(t57_rows)

    # Generate table - intermediate stiffener checks (IS 800 CL. 8.7.1.2)
    # Status: PASS when Provided ≥ Required.
    def _ge_status(provided, required):
        try:
            return "PASS" if float(provided) >= float(required) else r"\textcolor{red}{FAIL}"
        except (TypeError, ValueError):
            return "---"
    _iys_status = _ge_status(bridge.output_dict.get(KEY_SD_IS_IYS_PROV),
                             bridge.output_dict.get(KEY_SD_IS_IYS_MIN))
    _fqd_status = _ge_status(bridge.output_dict.get(KEY_SD_IS_FQD),
                             bridge.output_dict.get(KEY_SD_IS_FQ))
    t58_rows = []
    for lbl, _ in girder_entries:
        t58_rows.append(
            r"\multirow{2}{*}{\makecell{" + lbl + r"""}} & Min. Moment of Inertia, $I_s$ & """ + _render_value(bridge.output_dict, KEY_SD_IS_IYS_MIN, " mm$^4$") + r""" & """ + _render_value(bridge.output_dict, KEY_SD_IS_IYS_PROV, " mm$^4$") + r""" & """ + _iys_status + r""" \\[6pt]
\cline{2-5}
 & Buckling Resistance, $F_{qd} \geq F_q$ & """ + _render_value(bridge.output_dict, KEY_SD_IS_FQ, " kN") + r""" & """ + _render_value(bridge.output_dict, KEY_SD_IS_FQD, " kN") + r""" & """ + _fqd_status + r""" \\[6pt]
\hline"""
        )
    t58_content = "\n".join(t58_rows)

    # (Intermediate Stiffener Checks) is a verification table — it only
    # has data when the user supplied stiffener sizes (Design Type = Custom). In
    # Optimized mode the stiffeners are auto-sized (nothing to verify), so the
    # whole table is omitted from the report.
    _is_custom = str(bridge.input_dict.get(KEY_DESIGN_MODE, "Optimized")).strip().lower() in {"custom", "customized"}
    if _is_custom:
        t58_block = r"""
\vspace{1em}

\begin{longtable}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.2cm}|C{1.8cm}|}
\caption{Intermediate Stiffener Checks}
\hline
\textbf{} & \textbf{Check} & \textbf{Required} & \textbf{Provided} & \textbf{Status} \\[6pt]
\hline
""" + t58_content + r"""
\end{longtable}
\noindent\textit{Note: IS 800 Cl. 8.7.1.2}
"""
    else:
        t58_block = ""

    # Generate Table 5.9 rows — bearing stiffener checks (IS 800 Cl.8.7.3).
    # End panel == bearing stiffener for this bridge. Each resistance vs reaction R.
    # Resistances are 0 in guidance-only mode (optimized w/o outstand) → N/A until
    # the designer defaults outstand to (bf−tw)/2.
    _bs_r = bridge.output_dict.get(KEY_SD_BS_R)
    def _bs_check(resist_key):
        prov = bridge.output_dict.get(resist_key)
        # Resistance not computed (guidance mode) → N/A.
        if prov is None or float(prov) <= 0.0 or _bs_r is None:
            return ("N/A", "N/A", "N/A")
        req_s  = f"{_bs_r} kN"
        prov_s = f"{prov} kN"
        status = "PASS" if float(prov) >= float(_bs_r) else r"\textcolor{red}{FAIL}"
        return (req_s, prov_s, status)
    _wb_req, _wb_prov, _wb_st = _bs_check(KEY_SD_BS_FCDW_WB)
    _lc_req, _lc_prov, _lc_st = _bs_check(KEY_SD_BS_FCDW_LC)
    _ps_req, _ps_prov, _ps_st = _bs_check(KEY_SD_BS_FPSD)
    _cb_req, _cb_prov, _cb_st = _bs_check(KEY_SD_BS_FCD)
    t59_rows = []
    for lbl, _ in girder_entries:
        t59_rows.append(
            r"\multirow{4}{*}{\makecell{" + lbl + r"""}} & Web Buckling Resistance & """ + _wb_req + r""" & """ + _wb_prov + r""" & """ + _wb_st + r""" \\[6pt]
\cline{2-5}
 & Local Crushing Resistance & """ + _lc_req + r""" & """ + _lc_prov + r""" & """ + _lc_st + r""" \\[6pt]
\cline{2-5}
 & Bearing Capacity & """ + _ps_req + r""" & """ + _ps_prov + r""" & """ + _ps_st + r""" \\[6pt]
\cline{2-5}
 & Column Buckling Resistance & """ + _cb_req + r""" & """ + _cb_prov + r""" & """ + _cb_st + r""" \\[6pt]
\hline"""
        )
    t59_content = "\n".join(t59_rows)

    # ── Table 5.10: Serviceability — Deflection Checks (IRC 22 Cl. 604.3.2) ──────
    # Allowable limits: span-dependent, same for all girders, from output_dict.
    # Actual deflections: per-girder from bridge._deflections_cache — the same
    # source used by resolve_deflection_live_load/total in generate_results_values_builder.py.
    # Keys: {"G1": {"live_mm": X, "total_mm": Y}, ...}
    # lbl from girder_entries is "G1", "G2", ... which matches cache keys exactly.

    def _defl_status(actual, allowable):
        """PASS / red FAIL for deflection; '---' when values are missing."""
        try:
            return "PASS" if float(actual) <= float(allowable) else r"\textcolor{red}{FAIL}"
        except (TypeError, ValueError):
            return "---"

    def _dfmt(v, nd=2):
        """Format a numeric value to nd decimal places; empty string when None."""
        try:
            return f"{float(v):.{nd}f}"
            
        except (TypeError, ValueError):
            return ""

    # Mirror generate_results_values_builder.resolve_deflection_live/total_load
    # exactly so the report shows the same numbers as the Generate Results dialog:
    # allowable from span (L/800, L/600), actual from _deflections_cache.
    try:
        _span_m = float(bridge.input_dict.get(KEY_SPAN))
        _allow_live_mm  = _span_m * 1000.0 / 800.0
        _allow_total_mm = _span_m * 1000.0 / 600.0
    except (TypeError, ValueError):
        _allow_live_mm = _allow_total_mm = None
    _allow_live_str  = (f"L/800 = {_allow_live_mm:.1f} mm")  if _allow_live_mm  is not None else ""
    _allow_total_str = (f"L/600 = {_allow_total_mm:.1f} mm") if _allow_total_mm is not None else ""

    # The report has no live _deflections_cache (it builds a ReportDataBridge from
    # output_dict only). design() persists the same per-girder cache values that
    # the Generate Results dialog shows into output_dict under the canonical
    # "G1".."Gn" suffix, so read them from there by loop index.
    t510_rows = []
    for _gi, (lbl, _) in enumerate(girder_entries, start=1):
        _live_mm  = bridge.output_dict.get(f"{KEY_SD_DEFL_LIVE}.G{_gi}")
        _total_mm = bridge.output_dict.get(f"{KEY_SD_DEFL_TOTAL}.G{_gi}")

        t510_rows.append(
            r"\multirow{2}{*}{\makecell{" + lbl + r"""}} & Live Load Deflection, $\delta_{LL}$ (mm) & """
            + _allow_live_str + r""" & """
            + _dfmt(_live_mm,  nd=3) + r""" & """
            + _defl_status(_live_mm,  _allow_live_mm) + r""" \\[6pt]
\cline{2-5}
 & Total Load Deflection, $\delta_{total}$ (mm) & """
            + _allow_total_str + r""" & """
            + _dfmt(_total_mm, nd=3) + r""" & """
            + _defl_status(_total_mm, _allow_total_mm) + r""" \\[6pt]
\hline"""
        )
    t510_content = "\n".join(t510_rows)

    # Generate Table 5.11 rows — SLS steel stress limitation (IRC 22 Cl. 604.3.1).
    # Concrete & rebar deck stresses are deck-global and belong with the deck
    # checks, so this table shows only the per-girder steel check. Steel stress is
    # a single envelope-SLS value (same for every girder); allowable = 0.9·fy.
    # Both live in the nested output_dict["design_results"] dict, not as flat keys.
    def _mpa(v):
        s = _dfmt(v, nd=2)
        return (s + " MPa") if s else ""

    def _stress_status(actual, allow):
        try:
            return "PASS" if float(actual) <= float(allow) else r"\textcolor{red}{FAIL}"
        except (TypeError, ValueError):
            return "---"

    _dr_511        = bridge.output_dict.get("design_results", {})
    _steel_sigma   = _dr_511.get(KEY_SD_STRESS_STEEL)
    _steel_allow   = _dr_511.get(KEY_SD_STRESS_STEEL_ALLOWABLE)
    _steel_sig_str = _mpa(_steel_sigma)
    _steel_alw_str = _mpa(_steel_allow)
    _steel_status  = _stress_status(_steel_sigma, _steel_allow)

    t511_rows = []
    for lbl, _ in girder_entries:
        t511_rows.append(
            r"\makecell{" + lbl + r"""} & Structural Steel ($0.9\,f_y$) & """
            + _steel_alw_str + r""" & """
            + _steel_sig_str + r""" & """
            + _steel_status + r""" \\[6pt]
\hline"""
        )
    t511_content = "\n".join(t511_rows)

    # Supporting calculation for Table 5.11 — the "Actual Stress" above is NOT
    # a plain Md/Z bending stress; it is the Cl.604.3.1 equivalent stress
    # fe = sqrt(fbc^2 + 3*tau_b^2) on the short-term composite section under
    # the SLS envelope moment. Expose that breakdown so the reported value can
    # be independently recomputed. Source: the controlling girder's own
    # sls_fibre_stresses dict (design_results["per_girder"][controlling_girder]
    # ["sls_fibre_stresses"]), already written by compute_sls_stresses() in
    # designer.py — read-only here, no calculation is added or changed.
    _ctrl_girder = _dr_511.get("controlling_girder")
    _per_girder  = _dr_511.get("per_girder", {}) or {}
    _girder_data = _per_girder.get(_ctrl_girder, {}) or {}
    _sls_fibre   = _girder_data.get("sls_fibre_stresses", {}) or {}

    def _num3(v):
        s = _dfmt(v, nd=3)
        return s if s else "---"

    _sls_vsls = _num3(_sls_fibre.get("V_sls_kN"))
    _sls_aw   = _num3(_sls_fibre.get("Aw_mm2"))
    _sls_fbc    = _num3(_sls_fibre.get("fbc_MPa"))
    _sls_fbt    = _num3(_sls_fibre.get("fbt_MPa"))
    _sls_taub   = _num3(_sls_fibre.get("tau_b_MPa"))
    _sls_fecomp = _num3(_sls_fibre.get("fe_comp_MPa"))
    _sls_fetens = _num3(_sls_fibre.get("fe_tens_MPa"))

    # Equation-by-equation derivation of the governing stress: bending stress,
    # shear stress, equivalent stress (both fibres), then the governing
    # (max) equivalent stress that Table 5.11 reports as "Actual Stress".
    t511_calc_content = rf"""
        \[
        f_{{bc}} = {_sls_fbc}\ \mathrm{{MPa}}, \qquad
        f_{{bt}} = {_sls_fbt}\ \mathrm{{MPa}}
        \]

        \[
        \tau_b=\frac{{V_{{sls}}}}{{A_w}}=\frac{{{_sls_vsls}\times1000}}{{{_sls_aw}}}={_sls_taub}\ \mathrm{{MPa}}
        \qquad \text{{(average web shear stress --- Cl. 604.3.1)}}
        \]

        \[
        f_{{e,comp}} = \sqrt{{f_{{bc}}^2 + 3\tau_b^2}}
        = \sqrt{{{_sls_fbc}^2 + 3\times{_sls_taub}^2}}
        = {_sls_fecomp}\ \mathrm{{MPa}}
        \]

        \[
        f_{{e,tens}} = \sqrt{{f_{{bt}}^2 + 3\tau_b^2}}
        = \sqrt{{{_sls_fbt}^2 + 3\times{_sls_taub}^2}}
        = {_sls_fetens}\ \mathrm{{MPa}}
        \]

        \[
        f_e = \max\left(f_{{e,comp}},\,f_{{e,tens}}\right) = {_steel_sig_str}
        \qquad (\text{{Actual Stress, Table 5.10}})
        \]
        \smallskip
        \hrule
        \smallskip
        """


    # Generate Table 5.12 rows — per-girder fatigue assessment (IRC 22 Cl. 605),
    # mirroring the Generate Results dialog: one row per girder showing the
    # GOVERNING fatigue check (worst of normal/shear by DCR). Source is the nested
    # design_results["steeldesign.uls_per_girder"]["fatigue"][G{i}] dict, keyed by
    # the canonical girder index, with {demand, capacity, ur, status}.
    _fat_cat = ((bridge.output_dict.get("design_results", {}) or {})
                .get(KEY_SD_ULS_PER_GIRDER, {}) or {}).get("fatigue", {}) or {}

    def _fat_status(s):
        if s is None or str(s).strip() == "":
            return "---"
        return r"\textcolor{red}{" + str(s) + "}" if "FAIL" in str(s).upper() else str(s)

    t512_rows = []
    for _gi, (lbl, _) in enumerate(girder_entries, start=1):
        _g = _fat_cat.get(f"G{_gi}", {}) or {}
        t512_rows.append(
            r"\makecell{" + lbl + r"""} & """
            + _mpa(_g.get("demand")) + r""" & """
            + _mpa(_g.get("capacity")) + r""" & """
            + _dfmt(_g.get("ur"), nd=2) + r""" & """
            + _fat_status(_g.get("status")) + r""" \\[6pt]
\hline"""
        )
    t512_content = "\n".join(t512_rows)
    # ------------------------------------------------------------------
    # Table 5.12 – Supporting Calculations
    # ------------------------------------------------------------------

    _fat_stress_range = _dr_511.get(KEY_SD_FATIGUE_STRESS_RANGE_MPA)
    _fat_mu_r         = _dr_511.get(KEY_SD_FATIGUE_MU_R)
    _fat_gamma_mft    = bridge.output_dict.get(KEY_DO_GAMMA_MF)
    _fat_ff           = _dr_511.get(KEY_SD_FATIGUE_FF_MPA)
    _fat_ffd          = _dr_511.get(KEY_SD_FATIGUE_FFD_MPA)

    _fat_ur = (
        (_fat_stress_range / _fat_ffd)
        if (_fat_stress_range is not None and _fat_ffd)
        else None
    )

    t512_calc_content = rf"""
    \medskip
    \noindent\textbf{{Supporting Calculations}}
    \small
    Illustrative fatigue calculation corresponding to the reported assessment.

    \normalsize

    \[
    \Delta\sigma = {_dfmt(_fat_stress_range,2)}\ \mathrm{{MPa}}
    \]

    \[
    f_f = {_dfmt(_fat_ff,2)}\ \mathrm{{MPa}}
    \]

    \[
    \mu_r = {_dfmt(_fat_mu_r,2)}, \qquad
    \gamma_{{mft}} = {_dfmt(_fat_gamma_mft,2)}
    \]

    \[
    f_{{fd}}
    =
    \frac{{\mu_r\,f_f}}{{\gamma_{{mft}}}}
    =
    \frac{{{_dfmt(_fat_mu_r,2)}\times{_dfmt(_fat_ff,2)}}}
        {{{_dfmt(_fat_gamma_mft,2)}}}
    =
    {_dfmt(_fat_ffd,2)}
    \ \mathrm{{MPa}}
    \]

    \[
    \mathrm{{UR}}
    =
    \frac{{\Delta\sigma}}{{f_{{fd}}}}
    =
    \frac{{{_dfmt(_fat_stress_range,2)}}}
        {{{_dfmt(_fat_ffd,2)}}}
    =
    {_dfmt(_fat_ur,2)}
    \]
    """

    # Generate Table 5.13 rows — per-girder design summary, mirroring the Generate
    # Results dialog's resolve_design_results_summary: one row per girder showing
    # the CONTROLLING check (highest DCR among all checks) plus the real load
    # case/combination that drives it. Source: design_results["per_girder"][G{i}].
    _pg_summary = (bridge.output_dict.get("design_results", {}) or {}).get("per_girder", {}) or {}

    def _with_unit(value, unit):
        s = _dfmt(value, nd=2)
        if not s:
            return ""
        return (s + " " + unit) if unit and str(unit) not in ("-", "–") else s

    g_summary_rows = []
    for _gi, (lbl, _) in enumerate(girder_entries, start=1):
        g_data = _pg_summary.get(f"G{_gi}", {}) or {}
        checks = g_data.get("checks") or []
        if not checks:
            g_summary_rows.append(lbl + r""" &  &  &  &  &  &  \\[6pt]
\hline""")
            continue

        ctrl = max(checks, key=lambda c: c.get("dcr") or 0.0)

        # Worst real load case for the controlling check id (skip Envelope pseudo-LCs)
        ctrl_lc, best_dcr = None, None
        for lc_name, lc_data in (g_data.get("per_lc") or {}).items():
            if str(lc_name).lower().startswith("envelope"):
                continue
            for chk in lc_data.get("checks") or []:
                if chk.get("id") == ctrl.get("check_id"):
                    d = chk.get("dcr") or 0.0
                    if best_dcr is None or d > best_dcr:
                        best_dcr, ctrl_lc = d, lc_name
        if ctrl_lc is None:
            ctrl_lc = (g_data.get("demand") or {}).get("governing_combination") or ""

        g_summary_rows.append(
            lbl + r""" & """ + _tex(str(ctrl_lc)) + r""" & """ + _tex(str(ctrl.get("name", "")))
            + r""" & """ + _with_unit(ctrl.get("demand"),   ctrl.get("demand_unit"))
            + r""" & """ + _with_unit(ctrl.get("capacity"), ctrl.get("capacity_unit"))
            + r""" & """ + _dfmt(ctrl.get("dcr"), nd=3)
            + r""" & """ + _fat_status(ctrl.get("status")) + r""" \\[6pt]
\hline"""
        )
    g_summary_table_content = "\n".join(g_summary_rows)

    # ── Table 5.14: Shear Connector Capacity (bridge-level) ──────────────────
    # Qu (Cl.606.3.1, Eq.6.1) and Qr (Cl.606.3.2, Table 8) are single per-stud
    # values for the bridge, stored flat inside output_dict["design_results"].
    _dr_sc = bridge.output_dict.get("design_results", {}) or {}

    def _kn(v):
        s = _dfmt(v, nd=2)
        return (s + " kN") if s else ""

    t514_content = (
        r"Design Resistance, $Q_u$ & \footnotesize\makecell{$Q_u=\min(Q_{u,s},\,Q_{u,c})$\\[3pt]$Q_{u,s}=\dfrac{0.8\,f_u\,(\pi d^2/4)}{\gamma_v}$\\[3pt]$Q_{u,c}=\dfrac{0.29\,\alpha\,d^2\sqrt{f_{ck}\,E_{cm}}}{\gamma_v}$} & "
        + _kn(_dr_sc.get(KEY_SD_SC_Qu_kN)) + r""" & IRC 22 Cl. 606.3.1 (Eq. 6.1) \\[6pt]
\hline
Fatigue Shear Resistance, $Q_r$ & IRC 22 Table 8 ($\phi d$, $N_{sc}$) & """
        + _kn(_dr_sc.get(KEY_SD_SC_Qr_kN)) + r""" & IRC 22 Cl. 606.3.2 (Table 8) \\[6pt]
\hline"""
    )

    # ── Table 5.15: Shear Connector Spacing (bridge-level) ───────────────────
    # Required spacings SL1/SL2/SR and the max-spacing limit are single bridge
    # values in design_results. Each criterion passes when the provided spacing
    # is no larger than that criterion's required spacing (denser = safe).
    def _mm(v):
        s = _dfmt(v, nd=1)
        return (s + " mm") if s else ""

    _sc_prov     = _dr_sc.get("stud_spacing_provided_mm")
    _sc_prov_str = _mm(_sc_prov)

    def _sp_row(crit, req):
        return (crit + r" & " + _mm(req) + r" & " + _sc_prov_str + r" & "
                + _defl_status(_sc_prov, req) + r" \\[6pt]")
        
    def _detail_row(text):
        return (
            r"\multicolumn{4}{|p{0.96\linewidth}|}{"
            r"\hspace{2mm}\small "
            + text +
            r"} \\"
        )
    def _detail_value(name, value, unit=""):
        s = _dfmt(value, nd=2)
        return _detail_row(
            rf"{name} = {s}" + (f" {unit}" if s else "")
        )    
    

    t515_content = (
        _sp_row("ULS Shear (SL1)", _dr_sc.get(KEY_SD_SC_SL1))
        + "\n\\hline\n"
        + _sp_row("Full Composite (SL2)", _dr_sc.get(KEY_SD_SC_SL2))
        + "\n\\hline\n"
        + _sp_row("SLS Fatigue (SR)", _dr_sc.get(KEY_SD_SC_SR))
        + "\n\\hline\n"
        + _sp_row("Max Spacing Limit (IRC 22)", _dr_sc.get("stud_spacing_max_mm"))
        + "\n\\hline"
    )  
    t515_calc_content = rf"""
    \vspace{{0.4em}}

    \noindent
    \textbf{{Supporting Calculations}}

    \begin{{flushleft}}
    
    % ---------------- S_L1 ----------------
    \noindent\textbullet\hspace{{0.5em}}
    $S_{{L1}}=\dfrac{{\sum Q_u}}{{V_L}}$
    \hfill
    {{\small
    $(V_L:\ \text{{See Table 5.15; IRC 22 Cl. 606.4.1}})$
    }}

    \noindent\textbullet\hspace{{0.5em}}
    $S_{{L2}}=\dfrac{{\sum Q_u}}{{H}}\,L$
    \hfill
    {{\small
    ($L={_dfmt(_dr_sc.get(KEY_SD_SC_SHEAR_SPAN),2)}\,\mathrm{{mm}}$
    : Shear Span)}}

    \hfill


    \hspace*{{1.5em}}
    $H_1=\dfrac{{A_{{sl}}f_{{yk}}}}{{\gamma_m}}\times10^{{-3}}
    ={_dfmt(_dr_sc.get(KEY_SD_SC_H1_kN),2)}\,\mathrm{{kN}}
    \qquad
    (A_{{sl}}={_dfmt(_dr_sc.get("Ag_mm2"),2)}\,\mathrm{{mm^2}})$

    \\

    \hspace*{{1.5em}}
    $H_2=0.36\,f_{{ck}}A_{{ec}}\times10^{{-3}}
    ={_dfmt(_dr_sc.get(KEY_SD_SC_H2_kN),2)}\,\mathrm{{kN}}
    \qquad
    (A_{{ec}}=b_{{eff}}\,t_{{eff}}
    ={_dfmt(_dr_sc.get(KEY_SD_SC_AEC_MM2),2)}\,\mathrm{{mm^2}})$

    \\

    \hspace*{{1.5em}}
    $H=\min(H_1,H_2)
    ={_dfmt(_dr_sc.get(KEY_SD_SC_H_kN),2)}\,\mathrm{{kN}}$

    \\
    
    \vspace{{0.4em}}

    \noindent\textbullet\hspace{{0.5em}}$S_R=\dfrac{{\sum Q_r}}{{V_r}}$

    \hspace*{{1.5em}}
    $V_r=\dfrac{{V_R\,A_{{ec}}\,Y}}{{I_c}}$

    \hspace*{{1.5em}}
    $V_R={_dfmt(_dr_sc.get(KEY_SD_SC_Vr_kN),2)}\,\mathrm{{kN}},
    \;
    V_r={_dfmt(_dr_sc.get(KEY_SD_SC_VR_PER_MM),2)}\,\mathrm{{kN/mm}}$

    \hfill
    {{\small ($Y,I_c$: See Table 5.15)}}
    \vspace{{-1.0em}}
    \end{{flushleft}}
    """
    # ── Table 5.16: Transverse Shear & Detailing Checks (bridge-level) ───────
    # Transverse shear (Cl.606.10): VL vs slab capacity VRd. Detailing (Cl.606.6):
    # min transverse reinforcement, stud diameter ≤ 2·tf, edge distance ≥ 25 mm.
    # All single bridge values in design_results; stud diameter from input_dict.
    def _cm2m(v):
        s = _dfmt(v, nd=2)
        return (s + r" cm$^2$/m") if s else ""

    def _knm(v):
        s = _dfmt(v, nd=2)
        return (s + " kN/m") if s else ""
    
    def _mm2(v):
        s = _dfmt(v, nd=2)
        return (s + " mm$^2$") if s else ""
    
    def _mm4(v):
        s = _dfmt(v, nd=2)
        return (s + " mm$^4$") if s else ""

    _ts_vl  = _dr_sc.get(KEY_SD_TS_VL)
    _ts_vrd = _dr_sc.get(KEY_SD_TS_VRD)
    _ts_v   = _dr_sc.get("Vu_kN")
    _ts_aec   = _dr_sc.get(KEY_SD_TS_AEC)
    _ts_y     = _dr_sc.get(KEY_SD_TS_Y)
    _ts_ic    = _dr_sc.get("I_comp_short_mm4")
    _t_slab = _dr_511.get(KEY_TS_DECK_THICKNESS)
    if _ts_vl is not None and _ts_vrd is not None:
        try:
            _ts_vl_f = float(_ts_vl)
            _ts_vrd_f = float(_ts_vrd)
            if _ts_vrd_f > 0.0:
                _ts_ur_str = f"{_ts_vl_f / _ts_vrd_f:.2f}"
            else:
                _ts_ur_str = "---"
        except (TypeError, ValueError):
            _ts_ur_str = "---"
    else:
        _ts_ur_str = "---"
    _ts_ok = _dr_sc.get("transverse_shear_ok")
    _ts_status = (r"\textcolor{red}{FAIL}" if _ts_ok is False else "PASS") if _ts_ok is not None else "---"

    _ast_req  = _dr_sc.get("Ast_required_cm2_per_m")
    # Provided transverse steel = the deck's main (bottom + top) bars, which run
    # transversely between girders and cross the shear plane. The deck design
    # computes these (>= minimum) and they are what is actually provided. The
    # steel designer's own Ast_provided is 0 because its transverse-shear check
    # runs before design_deck_slab(), so read the deck-design value here instead.
    _dd_516 = bridge.output_dict.get("deck_design_results", {}) or {}
    try:
        _ast_prov = (float(_dd_516.get("rebar_bottom_area") or 0)
                     + float(_dd_516.get("rebar_top_area") or 0)) / 100.0
    except (TypeError, ValueError):
        _ast_prov = None
    _stud_d   = bridge.input_dict.get(KEY_DS_STUD_DIAMETER)
    _d_lim    = _dr_sc.get(KEY_SD_SC_D_LIMIT)
    _edge     = _dr_sc.get(KEY_SD_SC_EDGE_DIST)
    _edge_req = _dr_sc.get(KEY_SD_SC_REQ_EDGE_DIST)
    
    def _row515a(parameter, expression, value,):
        return parameter + r" & " + expression + r" & " + value + r" \\[6pt]"

    def _row516(check, value, status):
        return check + r" & " + value + r" & " + status + r" \\[6pt]"
    
    t515a_content = (
        _row515a(
            r"$V$",
            r"\textnormal{Factored Shear Force, $V$}",
            _dfmt(_ts_v, nd=2) + " kN",
        )
        + "\n\\hline\n"

        + _row515a(
            r"$A_{ec}$ {\small(Transformed)}",
            r"Transformed Compressive Concrete Area, $A_{ec}=\dfrac{b_{eff}t_{eff}}{n}$",
            _mm2(_ts_aec),
        )
        + "\n\\hline\n"

        + _row515a(
            r"$Y$",
            r"\textnormal{Distance to Centroid, $Y$}",
            _mm(_ts_y),
        )
        + "\n\\hline\n"

        + _row515a(
            r"$I_c$",
            r"\textnormal{Composite Second Moment of Area, $I_c$}",
            _mm4(_ts_ic),
        )
        + "\n\\hline\n"

        + _row515a(
            r"$V_L$",
            r"$V_L=\dfrac{V\times A_{ec}\times Y}{I_c}$",
            _dfmt(_ts_vl, nd=2) + " N/mm",
        )
        + "\n\\hline"
    )
    t516_content = (
        _row516(r"\textnormal{Longitudinal Shear per unit length, $V_L$}", _knm(_ts_vl), "---") + "\n\\hline\n"
        + _row516(r"\textnormal{Transverse Shear Capacity of Slab, $V_{Rd}$}", _knm(_ts_vrd), "---") + "\n\\hline\n"
        + _row516(r"\textnormal{Transverse Shear Check}", r"$V_L/V_{Rd}$ = " + _ts_ur_str, _ts_status) + "\n\\hline\n"
        + _row516(r"\textnormal{Min. Transverse Reinforcement, $A_{st,min}$}",
                  r"Required " + _cm2m(_ast_req) + r", Provided " + _cm2m(_ast_prov),
                  _defl_status(_ast_req, _ast_prov)) + "\n\\hline\n"
        + _row516(r"\textnormal{Stud Diameter $\leq 2\,t_f$}",
                  r"$d$ = " + _mm(_stud_d) + r" $\leq 2t_f$ = " + _mm(_d_lim),
                  _defl_status(_stud_d, _d_lim)) + "\n\\hline\n"
        + _row516(r"\textnormal{Stud Edge Distance}",
                  r"Provided " + _mm(_edge) + r" (req. $\geq$ " + _mm(_edge_req) + r")",
                  _defl_status(_edge_req, _edge)) + "\n\\hline"
    )

    # Generate Table 5.20(a) rows
    cb_forces_rows = []
    pairs = bridge.get_cb_pairs()

    if not pairs:
        # fallback: one placeholder row
        cb_forces_rows.append(
            r"""Between Girders & Diagonal &  &  &  &  \\[6pt]
\hline"""
        )
    else:
        for pair in pairs:
            pair_id = pair.replace("-", "")
            for member, label in [("diagonal", "Diagonal"),
                                ("chord", "Top / Bottom chord")]:
                force_str, ftype = bridge.get_cb_governing_force(pair, member)
                conn_type = bridge.get_cb_connection(pair, member, ftype)
                section  = bridge.get_cb_section(pair, member, ftype)

                # Fetch properties from output_dict
                if member == "diagonal":
                    pfx = f"transverse_member_design.cb.section_properties.bracing.{pair_id}"
                else:
                    pfx = f"transverse_member_design.cb.section_properties.bottom_chord.{pair_id}"
                    if bridge.output_dict.get(f"{pfx}.A") is None:
                        pfx = f"transverse_member_design.cb.section_properties.top_chord.{pair_id}"

                area_cm2 = bridge.output_dict.get(f"{pfx}.A")
                rv_cm = bridge.output_dict.get(f"{pfx}.rv")

                # Convert Area: cm² -> mm²
                area_str = f"{float(area_cm2) * 100:.1f}" if area_cm2 is not None else ""
                # Convert rv: cm -> mm
                rmin_str = f"{float(rv_cm) * 10:.1f}" if rv_cm is not None else ""
                cb_forces_rows.append(
                    r"\multirow{2}{*}{\makecell{" + _tex(pair) + r"}} & "
                    + label + r" & " + conn_type + r" & " + section
                    + r" & " + area_str + r" & " + rmin_str
                    + r" \\[6pt]\cline{2-6}"
                )
            cb_forces_rows.append(r"\hline")
    cb_forces_content = "\n".join(cb_forces_rows)

    # Generate Table 5.20(b) rows
    def get_status_str(slnd_str, limit):
        try:
            v = float(slnd_str)
            return r"\textcolor{black}{PASS}" if v <= limit else r"\textcolor{red}{FAIL}"
        except (ValueError, TypeError):
            return ""
    cb_slenderness_rows = []
    if not pairs:
        cb_slenderness_rows.append(
            r"""Between Girders & Diagonal & C &  &  &  ---  \\[6pt]
\hline"""
        )
    else:
        for pair in pairs:
            kl_diag = bridge.get_cb_effective_length("diagonal")
            slnd_diag = bridge.get_cb_slenderness(pair, "diagonal")
            status_diag = get_status_str(slnd_diag, 250)
            
            kl_tc = bridge.get_cb_effective_length("chord")
            slnd_tc = bridge.get_cb_slenderness(pair, "chord")
            status_tc = get_status_str(slnd_tc, 250)
            
            kl_bc = bridge.get_cb_effective_length("chord")
            slnd_bc = bridge.get_cb_slenderness(pair, "chord")
            status_bc = get_status_str(slnd_bc, 400)
            
            top_chord_enabled = bridge.output_dict.get("member_properties.cross_bracing_details.top_chord", True)
            bottom_chord_enabled = bridge.output_dict.get("member_properties.cross_bracing_details.bottom_chord", True)
            
            num_rows = 1 + int(top_chord_enabled) + int(bottom_chord_enabled)
            row_tex = r"\multirow{" + str(num_rows) + r"}{*}{\makecell{" + _tex(pair) + r"}}"
            row_tex += f" & Diagonal & C & {kl_diag} & {slnd_diag} & 250 --- {status_diag} \\\\[6pt]"
            
            if top_chord_enabled:
                row_tex += f"\n\\cline{{2-6}}\n & Top chord & C & {kl_tc} & {slnd_tc} & 250 --- {status_tc} \\\\[6pt]"
            if bottom_chord_enabled:
                row_tex += f"\n\\cline{{2-6}}\n & Bottom chord & T & {kl_bc} & {slnd_bc} & 400 --- {status_bc} \\\\[6pt]"
                
            row_tex += "\n\\hline"
            cb_slenderness_rows.append(row_tex)
    cb_slenderness_content = "\n".join(cb_slenderness_rows)

    # Generate Table 5.20(c) rows
    cb_capacity_rows = []
    for pair in pairs:
        rows_for_pair = []
        for member, label in [("diagonal", "Diagonal"),
                            ("chord", "Chord")]:
            force_str, ftype = bridge.get_cb_governing_force(pair, member)
            section  = bridge.get_cb_section(pair, member, ftype)
            gov_lc   = bridge.get_cb_gov_lc(pair, member, ftype)
            capacity = bridge.get_cb_capacity(pair, member, ftype)
            ur       = bridge.get_cb_efficiency(pair, member, ftype)
            status   = bridge.get_cb_status(pair, member, ftype)
            rows_for_pair.append(
                r" & " + label + r" & " + section
                + r" & " + gov_lc + r" & " + force_str + r" & " + capacity
                + r" & " + ur + r" & " + status + r" \\[6pt]\cline{2-8}"
            )
        first = r"\multirow{2}{*}{\makecell{" + _tex(pair) + r"}}" + rows_for_pair[0]
        rest  = rows_for_pair[1:]
        cb_capacity_rows.append(first)
        cb_capacity_rows.extend(rest)
        cb_capacity_rows.append(r"\hline")
    cb_capacity_content = "\n".join(cb_capacity_rows)



    # ── Deck slab design value helpers (Tables 5.17 a/b/c/e/g) ────────────────
    # Read from deck_rpt = output_dict["deck_report_values"] (common.KEY_DD_*).
    # Tables 5.17(d) punching shear and 5.17(f) one-way shear stay as
    # placeholders — those are not computed by design_deck_slab().
    _dk_has = bool(deck_rpt)
    _dk_oh = bool(deck_rpt.get(KEY_DD_HAS_OVERHANG))
    _DKPH = r"\placeholder{---}"

    # Ground-contact-dimension reference (IRC 6:2017 Cl. 204.1) — Table 2 for
    # Class A, Table 4 for Class B, Fig. 1 for Class 70R (W or T); no numbered
    # table exists for 70R, whose contact dimensions are given on Fig. 1 only.
    _dk_tyre_ref = {
        "ClassA": "IRC 6-2017 Table 2 (Cl. 204.1)",
        "ClassB": "IRC 6-2017 Table 4 (Cl. 204.1)",
        KEY_VEHICLE[0]: "IRC 6-2017 Fig. 1 (Cl. 204.1)",   # Class70R(W)
        KEY_VEHICLE[1]: "IRC 6-2017 Fig. 1 (Cl. 204.1)",   # Class70R(T)
    }.get(deck_rpt.get(KEY_DD_VEHICLE), "IRC 6-2017 Table 2 (Cl. 204.1)")

    def _dkv(key, default=0.0):
        """Raw float for status comparisons (0.0 if missing/non-numeric)."""
        v = deck_rpt.get(key)
        if v is None or v == "":
            return default
        try:
            return float(v)
        except (TypeError, ValueError):
            return default

    def _dkf(key, nd=2, scale=1.0):
        """Formatted display string; placeholder when deck design not run."""
        if not _dk_has:
            return _DKPH
        v = deck_rpt.get(key)
        if v is None or v == "":
            return _DKPH
        try:
            return f"{float(v) * scale:.{nd}f}"
        except (TypeError, ValueError):
            return str(v)

    def _dks(ok):
        """PASS/FAIL status; '---' when deck design not run."""
        return ("PASS" if ok else "FAIL") if _dk_has else "---"

    def _dkoh(key, nd=2, scale=1.0, unit=""):
        """Overhang value; 'N/A' when there is no overhang."""
        if not _dk_has:
            return _DKPH
        if not _dk_oh:
            return "N/A"
        return _dkf(key, nd=nd, scale=scale) + unit

    # Governing crack width = max(bottom, top[, overhang]) vs the limit.
    _dk_wks = [_dkv(KEY_DD_WK_BOT), _dkv(KEY_DD_WK_TOP)]
    if _dk_oh:
        _dk_wks.append(_dkv(KEY_DD_WK_OH))
    _dk_gov_wk = max(_dk_wks)
    _dk_gov_wk_str = (f"{_dk_gov_wk:.4f}" if _dk_has else _DKPH)
    _dk_crack_ok = _dk_has and _dk_gov_wk <= _dkv(KEY_DD_WK_LIMIT)

    # ── Table 5.22: Overall Design Check Summary — fill all rows ─────────────
    # Three row families:
    #  (1) Girder DCR-engine checks: one source (design_results["per_girder"])
    #      gives Demand, Capacity, UR, and the governing LC together. Worst
    #      girder = highest DCR. Most checks fire on the envelope demand (units
    #      available in per_girder["checks"]); SLS-conditional checks (e.g.
    #      deflection) only appear per-LC, so fall back to per_lc for those.
    #  (2) Deck slab: URs from deck_design_results (Demand/Capacity not stored).
    #  (3) Cross bracing: existing get_cb_* helpers (worst pair/member by UR).
    #      End diaphragm has no report helpers yet → "---" for now.
    _pg_522 = (bridge.output_dict.get("design_results", {}) or {}).get("per_girder", {}) or {}
    _dd_522 = bridge.output_dict.get("deck_design_results", {}) or {}

    def _vu_522(v, unit):
        s = _dfmt(v, nd=2)
        if not s:
            return ""
        u = (unit or "").strip()
        return (s + " " + u) if u else s

    def _ur_522(v):
        try:
            f = float(v)
        except (TypeError, ValueError):
            return ""
        s = f"{f:.2f}"
        return (r"\textcolor{red}{" + s + "}") if f > 1.0 else s

    def _lc_short(lc):
        # Show the full combination expression as-is, e.g.
        # "ACCIDENTAL 1: 1.0DL + 1.0DW + 0.75LL" (the per_lc key).
        return _tex(str(lc).strip())

    def _gov_lc_in_522(g, check_ids):
        gd = _pg_522.get(g) or {}
        best = None
        for _lc, _ld in (gd.get("per_lc") or {}).items():
            if str(_lc).lower().startswith("envelope"):
                continue
            for _chk in (_ld.get("checks") or []):
                if _chk.get("id") in check_ids:
                    _d = _chk.get("dcr") or 0.0
                    if best is None or _d > best[0]:
                        best = (_d, _lc)
        return _lc_short(best[1]) if best else "---"

    def _dcr_row(check_ids, fallback_unit=""):
        # Prefer per_girder["checks"] (carries units); worst girder by DCR.
        best = None  # (dcr, demand, capacity, dunit, cunit, g)
        for g, gd in _pg_522.items():
            if str(g).startswith("EB"):
                continue
            for chk in (gd.get("checks") or []):
                if chk.get("check_id") in check_ids:
                    d = chk.get("dcr") or 0.0
                    if best is None or d > best[0]:
                        best = (d, chk.get("demand"), chk.get("capacity"),
                                chk.get("demand_unit") or "", chk.get("capacity_unit") or "", g)
        if best is not None:
            d, dem, cap, du, cu, g = best
            return (_gov_lc_in_522(g, check_ids),
                    _vu_522(dem, du) or "---", _vu_522(cap, cu) or "---", _ur_522(d) or "---")
        # Fallback: per_lc (no units) for SLS-conditional checks (e.g. deflection).
        best = None  # (dcr, demand, capacity, lc)
        for g, gd in _pg_522.items():
            if str(g).startswith("EB"):
                continue
            for _lc, _ld in (gd.get("per_lc") or {}).items():
                if str(_lc).lower().startswith("envelope"):
                    continue
                for chk in (_ld.get("checks") or []):
                    if chk.get("id") in check_ids:
                        d = chk.get("dcr") or 0.0
                        if best is None or d > best[0]:
                            best = (d, chk.get("demand"), chk.get("capacity"), _lc)
        if best is None:
            return ("---", "---", "---", "---")
        d, dem, cap, _lc = best
        return (_lc_short(_lc),
                _vu_522(dem, fallback_unit) or "---", _vu_522(cap, fallback_unit) or "---",
                _ur_522(d) or "---")

    # (3) Cross bracing — worst pair/member by UR for the given force type.
    _cb_pairs_522 = bridge.get_cb_pairs()

    def _cb_row(force_type):
        best = None  # (ur, pair, member, capacity_str)
        for pair in _cb_pairs_522:
            for member in ("diagonal", "chord"):
                cap = bridge.get_cb_capacity(pair, member, force_type)
                eff = bridge.get_cb_efficiency(pair, member, force_type)
                try:
                    ur = float(eff)
                except (TypeError, ValueError):
                    continue
                if best is None or ur > best[0]:
                    best = (ur, pair, member, cap)
        if best is None:
            return ("---", "---", "---", "---")
        ur, pair, member, cap = best
        gov = bridge.get_cb_gov_lc(pair, member, force_type) or "---"
        dem = f"{float(cap) * ur:.2f} kN" if cap else "---"
        cap_s = (cap + " kN") if cap else "---"
        return (gov, dem, cap_s, _ur_522(ur))

    def _cb_slender_row():
        best = None  # (ratio, slend, limit)
        for pair in _cb_pairs_522:
            for member in ("diagonal", "chord"):
                s = bridge.get_cb_slenderness(pair, member)
                try:
                    sf = float(s)
                except (TypeError, ValueError):
                    continue
                lim = 400.0 if member == "chord" else 250.0
                ratio = sf / lim
                if best is None or ratio > best[0]:
                    best = (ratio, sf, lim)
        if best is None:
            return ("---", "---", "---", "---")
        ratio, sf, lim = best
        return ("---", f"{sf:.1f}", f"{lim:.0f}", _ur_522(ratio))

    def _row522(label, cells):
        c = [x if x else "---" for x in cells]
        return label + r" & " + r" & ".join(c) + r" \\[6pt]" + "\n\\hline"

    # Deck rows: Demand/Capacity from deck_report_values (KEY_DD_*, the same dict
    # the 5.17 tables use); UR = Demand/Capacity. The deck is designed for the
    # IRC:6 Basic ULS combination — build that combo string from the stored
    # partial factors (gamma_dl, gamma_ll).
    _deck_combo = (
        r"Basic ULS: " + _tex(f"{_dkv(KEY_DD_GAMMA_DL):g}DL + {_dkv(KEY_DD_GAMMA_LL):g}LL")
    ) if _dk_has else "---"

    def _deck_row(dem_key, cap_key, unit, is_oh=False):
        if not _dk_has:
            return ("---", "---", "---", "---")
        if is_oh and not _dk_oh:
            return (_deck_combo, "N/A", "N/A", "N/A")
        dem = _dkv(dem_key)
        cap = _dkv(cap_key)
        ur = (dem / cap) if cap > 0 else None
        return (_deck_combo, f"{dem:.2f} {unit}", f"{cap:.2f} {unit}", _ur_522(ur))

    def _row522_msg(label, msg):
        # Single message spanning the 4 data columns.
        return label + r" & \multicolumn{4}{c|}{" + msg + r"} \\[6pt]" + "\n\\hline"

    # End diaphragm: when configured as Cross Bracing it is designed as bracing
    # members → mirror the cross-bracing axial rows. For Rolled / Welded beam end
    # diaphragms the moment/shear design is not implemented yet → show a message.
    _ed_type = ""
    for _k, _v in bridge.input_dict.items():
        if str(_k).startswith(KEY_MP_ED_TYPE) and _v:
            _ed_type = str(_v)
            break
    _ed_is_cb = "brac" in _ed_type.strip().lower()
    if _ed_is_cb:
        _ed_moment_row = _row522(r"End Diaphragm --- Moment", _cb_row("compression"))
        _ed_shear_row  = _row522(r"End Diaphragm --- Shear",  _cb_row("tension"))
    else:
        _ed_msg = r"Rolled / Welded section --- design to be added"
        _ed_moment_row = _row522_msg(r"End Diaphragm --- Moment", _ed_msg)
        _ed_shear_row  = _row522_msg(r"End Diaphragm --- Shear",  _ed_msg)

    # Crack width (slab): governing crack width vs limit from the deck designer
    # (frequent SLS combination). _dk_gov_wk is the max of bottom/top/overhang wk.
    # The governing load combo is the SLS-frequent combination with the highest
    # DCR (its full expression comes straight from the per_lc keys).
    def _gov_sls_frequent():
        best = None  # (dcr, lc)
        for _g, _gd in _pg_522.items():
            if str(_g).startswith("EB"):
                continue
            for _lc, _ld in (_gd.get("per_lc") or {}).items():
                if "frequent" not in str(_lc).lower():
                    continue
                _d = _ld.get("max_dcr") or 0.0
                if best is None or _d > best[0]:
                    best = (_d, _lc)
        return _tex(str(best[1]).strip()) if best else "Frequent SLS"

    _wk_lim = _dkv(KEY_DD_WK_LIMIT)
    _crack_cells = (
        (_gov_sls_frequent() if _dk_has else "---"),
        (f"{_dk_gov_wk:.3f} mm" if _dk_has else "---"),
        (f"{_wk_lim:.3f} mm" if _dk_has else "---"),
        (_ur_522(_dk_gov_wk / _wk_lim) if (_dk_has and _wk_lim > 0) else "---"),
    )

    _t522 = [
        _row522(r"Girder --- Moment",             _dcr_row({1})),
        _row522(r"Girder --- Shear",              _dcr_row({2})),
        _row522(r"Girder --- LTB (constr.)",      _dcr_row({5})),
        _row522(r"Girder --- Deflection",         _dcr_row({13, 14}, fallback_unit="mm")),
        _row522(r"Girder --- Stress",             _dcr_row({11}, fallback_unit="MPa")),
        _row522(r"Girder --- Fatigue",            _dcr_row({8, 9}, fallback_unit="MPa")),
        _row522(r"Transverse Shear (slab)",       _dcr_row({16})),
        _row522(r"Crack Width (slab)",            _crack_cells),
        _row522(r"Deck --- Flexure (sagging)",    _deck_row(KEY_DD_M_ULS_SAG, KEY_DD_MU_BOT, "kN-m/m")),
        _row522(r"Deck --- Flexure (hogging)",    _deck_row(KEY_DD_M_ULS_HOG, KEY_DD_MU_TOP, "kN-m/m")),
        _row522(r"Deck --- Cantilever Overhang",  _deck_row(KEY_DD_M_ULS_OH, KEY_DD_MU_OH, "kN-m/m", is_oh=True)),
        _row522(r"Deck --- Punching Shear",       _deck_row(KEY_DD_PUNCH_VED, KEY_DD_VRD_C_MPA, "MPa")),
        _row522(r"Deck --- One-Way Shear",        _deck_row(KEY_DD_SHEAR_VED, KEY_DD_SHEAR_VRDC, "kN/m")),
        _row522(r"Cross Bracing --- Compression", _cb_row("compression")),
        _row522(r"Cross Bracing --- Tension",     _cb_row("tension")),
        _row522(r"Cross Bracing --- Slenderness", _cb_slender_row()),
        _ed_moment_row,
        _ed_shear_row,
    ]
    t522_content = "\n".join(_t522)

    return r"""
\chapter{Design Checks}

This section presents all structural design checks performed by OsdagBridge. For each member, the demand from the governing load combination, the code-based capacity, and the utilization ratio are tabulated. All checks reference IS 800:2007 and IRC 22:2014 unless stated otherwise.

\section{Plate Girder Design}
\label{sec:plate-girder}

\vspace{1em}
\begin{longtable}{|C{2.5cm}|L{8.0cm}|>{\centering\arraybackslash}p{5.0cm}|}
\caption{\textbf{Girder Section Properties (Final Optimized / User-selected)}}
\hline
\textbf{Girder} & \textbf{Property} & \textbf{Value} \\[6pt]
\hline
""" + t51_content + r"""
\end{longtable}

\vspace{1em}
\begin{longtable}{|C{2.5cm}|L{3cm}|C{3.5cm}|C{2.5cm}|>{\centering\arraybackslash}p{4.0cm}|}
\caption{\textbf{Girder Section Classification}}
\hline
\textbf{} & \textbf{Element} & \textbf{Slenderness Ratio} & \textbf{Class Limit} & \textbf{Classification} \\[6pt]
\hline
""" + t52_content + r"""
\end{longtable}
\noindent\textit{Note: IS 800:2007 Table 2}

\vspace{1em}
\begin{longtable}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.2cm}|C{1.8cm}|}
\caption{\textbf{Moment Capacity Check}}
\hline
\textbf{} & \textbf{Parameter} & \textbf{Formula} & \textbf{Value} & \textbf{Status} \\[6pt]
\hline
""" + t53_content + r"""
\end{longtable}
\noindent\textit{Note: IRC 22 Cl. 603.3.1, IS 800 Cl. 8.2.1}

\vspace{1em}
\begin{longtable}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.2cm}|C{1.8cm}|}
\caption{\textbf{Shear Capacity Check}}
\hline
\textbf{} & \textbf{Parameter} & \textbf{Formula} & \textbf{Value} & \textbf{Status} \\[6pt]
\hline
""" + t54_content + r"""
\end{longtable}
\noindent\textit{Note: IS 800 Cl. 8.4, IRC 22 Cl. 603.3.3.2}

\vspace{1em}
\begin{longtable}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.2cm}|C{1.8cm}|}
\caption{\textbf{Interaction Checks (M-V and M-N)}}
\hline
\textbf{} & \textbf{Check} & \textbf{Condition} & \textbf{Value} & \textbf{Status} \\[6pt]
\hline
""" + t55_content + r"""
\end{longtable}
\noindent\textit{Note: IRC 22 Cl. 603.3.3.3}

\vspace{1em}
\begin{longtable}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.2cm}|C{1.8cm}|}
\caption{\textbf{Lateral Torsional Buckling Check -- Construction Stage}}
\hline
\textbf{} & \textbf{Parameter} & \textbf{Formula} & \textbf{Value} & \textbf{Status} \\[6pt]
\hline
""" + t56_content + r"""
\end{longtable}
\noindent\textit{Note: IRC 22 Cl. 603.3.3.1, IS 800 Cl. 8.2.2}

\vspace{1em}
\begin{longtable}{|C{2.5cm}|L{6.5cm}|>{\arraybackslash}p{6.5cm}|}
\caption{\textbf{Stiffener Design Summary}}
\hline
""" + t57_content + r"""
\end{longtable}
""" + t58_block + r"""
\vspace{1em}

\begin{longtable}{|C{2.5cm}|L{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.2cm}|C{1.8cm}|}
\caption{\textbf{End Panel Stiffener Checks}}
\hline
\textbf{} & \textbf{Check} & \textbf{Required} & \textbf{Provided} & \textbf{Status} \\[6pt]
\hline
""" + t59_content + r"""
\end{longtable}
\noindent\textit{Note: IS 800 Cl. 8.4.2.2}

\vspace{1em}
\begin{longtable}{|C{2.5cm}|L{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{3.5cm}|C{2.5cm}|}
\caption{\textbf{Serviceability -- Deflection Checks}}
\hline
\textbf{} & \textbf{Check} & \textbf{Allowable} & \textbf{Actual} & \textbf{Status} \\[6pt]
\hline
""" + t510_content + r"""
\end{longtable}
\noindent\textit{Note: IRC 22 Cl. 604.3.2}

\vspace{1em}
\begin{longtable}{|C{2.5cm}|L{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{3.5cm}|C{2.5cm}|}
\caption{\textbf{Serviceability -- Maximum Stress Limitation}}
\hline
\textbf{} & \textbf{Element} & \textbf{Allowable Stress} & \textbf{Actual Stress} & \textbf{Status} \\[6pt]
\hline
""" + t511_content + r"""
\end{longtable}
\noindent\textit{Note: The Actual Stress above is the equivalent stress fe(IRC 22 Cl. 604.3.1) for the short-term composite section under the SLS envelope, not the bare-steel Md/Z bending stress. Since fp=0, the simplified equations below are used.}
""" + t511_calc_content + r"""

\vspace{1em}
\begin{longtable}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{3.5cm}|C{2.5cm}|}
\caption{\textbf{Serviceability -- Fatigue Assessment}}
\hline
\textbf{} & \textbf{Stress Range, $\Delta\sigma$ (MPa)} & \textbf{Fatigue Limit, $f_{fd}$ (MPa)} & \textbf{Utilization Ratio} & \textbf{Status} \\[6pt]
\hline
""" + t512_content + r"""
\end{longtable}
""" + t512_calc_content + r"""
\noindent\textit{Note: IRC 22 Cl. 605 --- governing of normal and shear fatigue (worst by DCR). Capacity reduction factor $\mu_r$ applied where plate thickness $> 25$ mm.}

\vspace{1em}
\vspace{0.4em}
\begin{longtable}{|C{1.6cm}|>{\centering\arraybackslash}p{3.6cm}|C{2.4cm}|C{2.0cm}|C{2.1cm}|C{1.7cm}|C{1.5cm}|}
\caption{\textbf{Girder Design Summary (DCR / Utilization Ratio)}}
\hline
\textbf{Girder} & \textbf{Controlling LC / Combination} & \textbf{Controlling Check} & \textbf{Demand} & \textbf{Capacity} & \textbf{UR} & \textbf{Status} \\[6pt]
\hline
""" + g_summary_table_content + r"""
\end{longtable}
\noindent\textit{Note: UR = Demand / Capacity. A value $\leq 1.0$ indicates a passing check. The controlling check is the criterion with the highest UR for each girder, with the real load case/combination that drives it.}

\vspace{1em}

\begin{longtable}{|L{3.6cm}|C{5.6cm}|>{\centering\arraybackslash}p{2.6cm}|L{3.0cm}|}
\caption{\textbf{Shear Connector Capacity}}
\hline
\textbf{Parameter} & \textbf{Formula} & \textbf{Value} & \textbf{Reference} \\[6pt]
\hline
""" + t514_content + r"""
\end{longtable}

\vspace{1em}

\setlength\LTleft{0pt}
\setlength\LTright{\fill}

\begin{longtable}{|L{3.2cm}|>{\centering\arraybackslash}p{4.3cm}|>{\centering\arraybackslash}p{4.3cm}|C{2.0cm}|}
\caption{\textbf{Shear Connector Spacing}}
\hline
\textbf{Criterion} & \textbf{Governing Spacing} & \textbf{Actual Spacing Provided} & \textbf{Status} \\[6pt]
\hline
""" + t515_content + r"""
\end{longtable}
\noindent\textit{Note: IRC 22 Cl. 606.4, 606.9.
Governing spacing $= \min(S_{L1}, S_{L2}, S_R)$.}
""" + t515_calc_content + r"""
\smallskip
\noindent\hrulefill
\vspace{1.2em}
% -----------------------------
% Table 5.15: Longitudinal Shear
% -----------------------------

\vspace{1em}

\begin{longtable}{|L{3.0cm}|>{\arraybackslash}p{7.5cm}|C{4.0cm}|}
\caption{\textbf{Longitudinal Shear Calculation (IRC 22 Cl.606.4.1)}}
\hline
\textbf{Parameter} &
\textbf{Expression} &
\textbf{Value} \\[6pt]
\hline
""" + t515a_content + r"""
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.3cm}|>{\arraybackslash}p{7.2cm}|C{2.0cm}|}
\caption{\textbf{Transverse Shear and Detailing Checks}}
\hline
\textbf{Check} & \textbf{Value} & \textbf{Status} \\[6pt]
\hline
""" + t516_content + r"""
\end{longtable}
\noindent\textit{Note: IRC 22 Cl. 606.6, 606.10.}

% ===========================
\section{Deck Slab Design}
\label{sec:deck-design}
% ===========================

The reinforced concrete deck slab is designed per IRC~112:2011 (flexure, shear, crack width) and IRC~22:2014 (composite construction). Wheel loads are distributed using Pigeaud's method. The deck is checked for flexure in the transverse and longitudinal directions, punching shear, one-way (beam) shear, crack width, and reinforcement detailing.

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Deck Slab --- Loading and Geometry}}
\hline
\textnormal{Effective Span of Deck Slab, $l_{eff}$} & """ + _dkf(KEY_DD_SPAN, nd=0, scale=1000.0) + r""" mm (girder spacing, c/c) \\[6pt]
\hline
\textnormal{Deck Thickness, $t_s$} & """ + _render_value(bridge.input_dict, KEY_TS_DECK_THICKNESS) + r""" mm \\[6pt]
\hline
\textnormal{Clear Cover (IRC 112 Cl. 15.2)} & Top """ + _render_value(bridge.input_dict, KEY_DS_TOP_CLEAR_COVER) + r""" / Bottom """ + _render_value(bridge.input_dict, KEY_DS_BOTTOM_CLEAR_COVER) + r""" mm \\[6pt]
\hline
\textnormal{Concrete Grade (IRC 112 Cl. 6.4)} & """ + _render_value(bridge.input_dict, KEY_DECK_CONCRETE_GRADE_BASIC) + r""" ($f_{ck}$ = """ + _render_value(bridge.input_dict, KEY_MATERIAL_DECK_FCK) + r""" MPa, $f_{ctm}$ = """ + _render_value(bridge.input_dict, KEY_MATERIAL_DECK_FCTM) + r""" MPa) \\[6pt]
\hline
\textnormal{Reinforcement Grade (IRC 112 Cl. 6.2)} & """ + _render_value(bridge.input_dict, KEY_DS_REINF_MATERIAL) + r""" ($f_y$ = """ + _dkf(KEY_DD_FY, nd=0) + r""" MPa) \\[6pt]
\hline
\textnormal{Dead Load per Unit Area, $w_{DL}$} & """ + _dkf(KEY_DD_WDL, nd=2) + r""" kN/m² (slab self-weight) \\[6pt]
\hline
\textnormal{IRC 6 Wheel Load (Class A / 70R)} & """ + _dkf(KEY_DD_WHEEL_LOAD, nd=1) + r""" kN \\[6pt]
\hline
\textnormal{Tyre Contact Dimension $B$, along traffic (""" + _dk_tyre_ref + r""")} & """ + _dkf(KEY_DD_TYRE_WIDTH, nd=0, scale=1000.0) + r""" mm \\[6pt]
\hline
\textnormal{Impact Factor Fraction, $i$ (IRC 6 Cl. 208.2)} & """ + (f"{_dkv(KEY_DD_IMPACT_FACTOR) - 1.0:.3f}" if _dk_has else _DKPH) + r""" \\[6pt]
\hline
\textnormal{Impact Multiplier, $(1+i)$} & """ + _dkf(KEY_DD_IMPACT_FACTOR, nd=3) + r""" \\[6pt]
\hline
\textnormal{Governing Live Load Case} & """ + _dkf(KEY_DD_VEHICLE) + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|C{3.0cm}|C{3.5cm}|C{3.0cm}|>{\centering\arraybackslash}p{4.2cm}|C{1.8cm}|}
\caption{\textbf{Deck Slab --- Flexure Check: Interior Panel (Pigeaud's Method)}}
\hline
\textbf{Location} & \textbf{Parameter} & \textbf{Formula / Reference} & \textbf{Value} & \textbf{Status} \\[6pt]
\hline
\multirow{5}{*}{\makecell{At Midspan\\(Sagging)}} & Transverse BM (DL), $M_{T,DL}$ & $w_{DL}\,l_{eff}^2/10$ & """ + _dkf(KEY_DD_M_DL, nd=2) + r""" kN-m/m & --- \\[6pt]
\cline{2-5}
 & Transverse BM (LL), $M_{T,LL}$ & Effective width (IRC 112 B3.1) & """ + _dkf(KEY_DD_M_LL, nd=2) + r""" kN-m/m & --- \\[6pt]
\cline{2-5}
 & Total Design BM, $M_{u,sag}$ & """ + _dkf(KEY_DD_GAMMA_DL, nd=2) + r"""\,$M_{T,DL}$ + """ + _dkf(KEY_DD_GAMMA_LL, nd=2) + r"""\,(1+i)\,$M_{T,LL}$ & """ + _dkf(KEY_DD_M_ULS_SAG, nd=2) + r""" kN-m/m & --- \\[6pt]
\cline{2-5}
 & Effective depth, $d$ & $t_s - c_{nom} - \phi/2$ & """ + _dkf(KEY_DD_D_BOT, nd=1) + r""" mm & --- \\[6pt]
\cline{2-5}
 & Moment Capacity, $M_{Rd}$ & IRC 112 Cl. 9.2, Cl. 8.2.1 & """ + _dkf(KEY_DD_MU_BOT, nd=2) + r""" kN-m/m & """ + _dks(_dkv(KEY_DD_MU_BOT) >= _dkv(KEY_DD_M_ULS_SAG)) + r""" \\[6pt]
\hline
\multirow{3}{*}{\makecell{At Support\\(Hogging)}} & Total Design BM, $M_{u,hog}$ & $0.75\,M_{u,sag}$ & """ + _dkf(KEY_DD_M_ULS_HOG, nd=2) + r""" kN-m/m & --- \\[6pt]
\cline{2-5}
 & Required Top Steel, $A_{st,top}$ & $M_u / (0.87\,f_y\,d)$ & """ + _dkf(KEY_DD_AS_REQ_TOP, nd=0) + r""" mm²/m & --- \\[6pt]
\cline{2-5}
 & Moment Capacity, $M_{Rd}$ & IRC 112 Cl. 9.2, Cl. 8.2.1 & """ + _dkf(KEY_DD_MU_TOP, nd=2) + r""" kN-m/m & """ + _dks(_dkv(KEY_DD_MU_TOP) >= _dkv(KEY_DD_M_ULS_HOG)) + r""" \\[6pt]
\hline
\end{longtable}
\noindent\textit{Note: IRC 112 Cl. 9.2, Cl. 8.2.1. Distribution (longitudinal) reinforcement designed for 20\% of main steel moment (IRC 21 Cl. 305.18).}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.5cm}|C{2cm}|}
\caption{\textbf{Deck Slab --- Cantilever Overhang Flexure Check}}
\hline
\textbf{Parameter} & \textbf{Formula} & \textbf{Value} & \textbf{Status} \\[6pt]
\hline
Overhang Length, $l_{oh}$ & --- & """ + _render_value(bridge.input_dict, KEY_TS_DECK_OVERHANG, " m") + r""" & --- \\[6pt]
\hline
Crash Barrier Load Moment, $M_{barrier}$ & IRC 6 Cl. 206.4 & """ + _dkoh(KEY_DD_M_BARRIER, nd=2, unit=" kN-m/m") + r""" & --- \\[6pt]
\hline
Dead Load Moment, $M_{DL,oh}$ & $w_{DL}\,l_{oh}^2/2$ + railing & """ + _dkoh(KEY_DD_M_DL_OH, nd=2, unit=" kN-m/m") + r""" & --- \\[6pt]
\hline
Live Load Moment (eccentric wheel), $M_{LL,oh}$ & Wheel load $\times$ arm & """ + _dkoh(KEY_DD_M_LL_OH, nd=2, unit=" kN-m/m") + r""" & --- \\[6pt]
\hline
Total Hogging Moment, $M_{u,oh}$ & """ + _dkf(KEY_DD_GAMMA_DL, nd=2) + r"""\,$M_{DL,oh}$ + """ + _dkf(KEY_DD_GAMMA_LL, nd=2) + r"""[(1+i)\,$M_{LL,oh}$ + $M_{barrier}$] & """ + _dkoh(KEY_DD_M_ULS_OH, nd=2, unit=" kN-m/m") + r""" & --- \\[6pt]
\hline
Effective depth, $d$ & $t_s - c_{nom} - \phi/2$ & """ + _dkoh(KEY_DD_D_OH, nd=1, unit=" mm") + r""" & --- \\[6pt]
\hline
Top Reinforcement Provided & --- & $\phi$""" + _dkoh(KEY_DD_DIA_OH, nd=0) + r""" @ """ + _dkoh(KEY_DD_SPC_OH, nd=0) + r""" mm c/c (""" + _dkoh(KEY_DD_AS_OH, nd=0) + r""" mm²/m) & --- \\[6pt]
\hline
Moment Capacity (top steel), $M_{Rd,oh}$ & IRC 112 Cl. 9.2, Cl. 8.2.1 & """ + _dkoh(KEY_DD_MU_OH, nd=2, unit=" kN-m/m") + r""" & """ + (_dks(_dkv(KEY_DD_MU_OH) >= _dkv(KEY_DD_M_ULS_OH)) if _dk_oh else ("N/A" if _dk_has else "---")) + r""" \\[6pt]
\hline
\end{longtable}
\noindent\textit{Note: IRC 6 Cl. 206.4 crash barrier loads applied at kerb face; IRC 112 Cl. 9.2, Cl. 8.2.1 flexure.}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.5cm}|C{2cm}|}
\caption{\textbf{Deck Slab --- Punching Shear Check (IRC~112 Cl.~10.4.6)}}
\hline
\textbf{Parameter} & \textbf{Formula / Reference} & \textbf{Value} & \textbf{Status} \\[6pt]
\hline
Design Wheel Load (ULS), $V_{Ed}$ & $\gamma_Q\,(1+i)\,P_w$ & """ + _dkf(KEY_DD_PUNCH_VED_KN, nd=1) + r""" kN & --- \\[6pt]
\hline
Tyre Contact Dimensions, $B \times W$ & """ + _dk_tyre_ref + r""" & """ + _dkf(KEY_DD_TYRE_WIDTH, nd=0, scale=1000.0) + r""" $\times$ """ + _dkf(KEY_DD_TYRE_LENGTH, nd=0) + r""" mm & --- \\[6pt]
\hline
Loaded Area at mid-depth, $b_0$ & $c_1 \times c_2$ (incl.\ WC dispersion) & """ + _dkf(KEY_DD_PUNCH_C1, nd=0) + r""" $\times$ """ + _dkf(KEY_DD_PUNCH_C2, nd=0) + r""" mm & --- \\[6pt]
\hline
Control Perimeter, $u_1$ & $2(c_1+c_2) + 4\pi d$ & """ + _dkf(KEY_DD_PUNCH_U1, nd=0) + r""" mm & --- \\[6pt]
\hline
Punching Shear Stress, $v_{Ed}$ & $V_{Ed} / (u_1\,d)$ & """ + _dkf(KEY_DD_PUNCH_VED, nd=3) + r""" MPa & --- \\[6pt]
\hline
Punching Resistance, $v_{Rd,c}$ & IRC 112 Eq.\ 10.1 & """ + _dkf(KEY_DD_VRD_C_MPA, nd=3) + r""" MPa & --- \\[6pt]
\hline
Punching Shear Check & $v_{Ed} \leq v_{Rd,c}$ & """ + (f"{_dkv(KEY_DD_PUNCH_VED) / _dkv(KEY_DD_VRD_C_MPA):.2f}" if (_dk_has and _dkv(KEY_DD_VRD_C_MPA) > 0) else _DKPH) + r""" & """ + _dks(bool(deck_rpt.get(KEY_DD_PUNCH_OK))) + r""" \\[6pt]
\hline
\end{longtable}
\noindent\textit{Note: Punching shear reinforcement not typically required for deck slabs with $d \geq 200$ mm and adequate longitudinal reinforcement.}

\vspace{1em}
\clearpage
\begin{longtable}{|L{7cm}|>{\arraybackslash}p{8.5cm}|}
\caption{\textbf{Crack Width Check (Deck Slab)}}
\hline
\textbf{Parameter} & \textbf{Value / Reference} \\[6pt]
\hline
\textnormal{Min. Reinforcement for Crack Control, $A_{s,min}$} & """ + _dkf(KEY_DD_AS_MIN, nd=0) + r""" mm²/m [IRC 112 Cl. 16.5.1] \\[6pt]
\hline
\textnormal{Provided Reinforcement (bottom)} & $\phi$""" + _dkf(KEY_DD_DIA_BOT, nd=0) + r""" @ """ + _dkf(KEY_DD_SPC_BOT, nd=0) + r""" mm c/c (""" + _dkf(KEY_DD_AS_BOT, nd=0) + r""" mm²/m) \\[6pt]
\hline
\textnormal{Max. Permissible Crack Width} & """ + _dkf(KEY_DD_WK_LIMIT, nd=2) + r""" mm \\[6pt]
\hline
\textnormal{Calculated Crack Width, $w_k$ (governing)} & """ + _dk_gov_wk_str + r""" mm \\[6pt]
\hline
\textnormal{Crack Width Check} & """ + _dks(_dk_crack_ok) + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.5cm}|C{2cm}|}
\caption{\textbf{One-Way (Beam) Shear Check (Deck Slab)}}
\hline
\textbf{Parameter} & \textbf{Formula / Reference} & \textbf{Value} & \textbf{Status} \\[6pt]
\hline
Design Shear per unit width, $V_{Ed}$ & $\gamma_{DL} V_{DL} + \gamma_{LL}(1{+}IF)V_{LL}$ & """ + _dkf(KEY_DD_SHEAR_VED, nd=2) + r""" kN/m & --- \\[6pt]
\hline
Effective depth, $d$ & $t_s - c_{nom} - \phi/2$ & """ + _dkf(KEY_DD_D_BOT, nd=1) + r""" mm & --- \\[6pt]
\hline
Size factor, $k$ & $1 + \sqrt{200/d} \leq 2.0$ & """ + (f"{min(1.0 + (200.0 / _dkv(KEY_DD_D_BOT)) ** 0.5, 2.0):.3f}" if (_dk_has and _dkv(KEY_DD_D_BOT) > 0) else _DKPH) + r""" & --- \\[6pt]
\hline
Long.\ reinforcement ratio, $\rho_l$ & $A_{sl}/(b_w\,d) \leq 0.02$ & """ + (f"{min(_dkv(KEY_DD_AS_BOT) / (1000.0 * _dkv(KEY_DD_D_BOT)), 0.02):.4f}" if (_dk_has and _dkv(KEY_DD_D_BOT) > 0) else _DKPH) + r""" & --- \\[6pt]
\hline
Shear resistance (no stirrups), $V_{Rd,c}$ & $v_{Rd,c}\,b_w\,d$ (Cl.\ 10.3.2) & """ + _dkf(KEY_DD_SHEAR_VRDC, nd=2) + r""" kN/m & --- \\[6pt]
\hline
One-Way Shear Check & $V_{Ed} \leq V_{Rd,c}$ & """ + (f"{_dkv(KEY_DD_SHEAR_VED) / _dkv(KEY_DD_SHEAR_VRDC):.2f}" if (_dk_has and _dkv(KEY_DD_SHEAR_VRDC) > 0) else _DKPH) + r""" & """ + _dks(bool(deck_rpt.get(KEY_DD_SHEAR_OK))) + r""" \\[6pt]
\hline
\end{longtable}
\noindent\textit{Note: IRC 112 Cl. 10.3.2. Shear reinforcement not provided in deck slabs; capacity relies on concrete and main reinforcement.}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|>{\centering\arraybackslash}p{4.1cm}|>{\centering\arraybackslash}p{4.1cm}|C{1.8cm}|}
\caption{\textbf{Reinforcement Detailing Summary (Deck Slab)}}
\hline
\textbf{Parameter} & \textbf{Required / Limit} & \textbf{Provided} & \textbf{Status} \\[6pt]
\hline
\multicolumn{4}{|l|}{\textbf{Main Reinforcement --- Bottom (Transverse)}} \\[6pt]
\hline
Required Area, $A_{st,req}$ (mm²/m) & """ + _dkf(KEY_DD_AS_REQ_BOT, nd=0) + r""" mm²/m & """ + _dkf(KEY_DD_AS_BOT, nd=0) + r""" mm²/m & """ + _dks(_dkv(KEY_DD_AS_BOT) >= _dkv(KEY_DD_AS_REQ_BOT)) + r""" \\[6pt]
\hline
Bar Diameter $\times$ Spacing & $\phi \geq 10$ mm (IRC 112) & $\phi$""" + _dkf(KEY_DD_DIA_BOT, nd=0) + r""" @ """ + _dkf(KEY_DD_SPC_BOT, nd=0) + r""" mm c/c & --- \\[6pt]
\hline
Min.\ Reinforcement $A_{s,min}$ (IRC 112 Cl. 16.3.1) & """ + _dkf(KEY_DD_AS_MIN, nd=0) + r""" mm²/m & """ + _dkf(KEY_DD_AS_BOT, nd=0) + r""" mm²/m & """ + _dks(_dkv(KEY_DD_AS_BOT) >= _dkv(KEY_DD_AS_MIN)) + r""" \\[6pt]
\hline
Max.\ Bar Spacing (IRC 112 Cl. 16.3.2) & """ + _dkf(KEY_DD_SPACING_MAX, nd=0) + r""" mm & """ + _dkf(KEY_DD_SPC_BOT, nd=0) + r""" mm & """ + _dks(0.0 < _dkv(KEY_DD_SPC_BOT) <= _dkv(KEY_DD_SPACING_MAX)) + r""" \\[6pt]
\hline
\multicolumn{4}{|l|}{\textbf{Distribution Reinforcement --- Longitudinal}} \\[6pt]
\hline
Required Area, $A_{st,dist}$ (mm²/m) & $\geq 20\%$ of main steel & """ + _dkf(KEY_DD_AS_LONG, nd=0) + r""" mm²/m & """ + _dks(_dkv(KEY_DD_AS_LONG) >= max(0.20 * _dkv(KEY_DD_AS_BOT), _dkv(KEY_DD_AS_MIN))) + r""" \\[6pt]
\hline
\multicolumn{4}{|l|}{\textbf{Top Reinforcement (Support)}} \\[6pt]
\hline
Required Area, $A_{st,top}$ (mm²/m) & """ + _dkf(KEY_DD_AS_REQ_TOP, nd=0) + r""" mm²/m & """ + _dkf(KEY_DD_AS_TOP, nd=0) + r""" mm²/m & """ + _dks(_dkv(KEY_DD_AS_TOP) >= _dkv(KEY_DD_AS_REQ_TOP)) + r""" \\[6pt]
\hline
\multicolumn{4}{|l|}{\textbf{Top Reinforcement (Cantilever Overhang)}} \\[6pt]
\hline
Required Area, $A_{st,oh}$ (mm²/m) & """ + _dkoh(KEY_DD_AS_REQ_OH, nd=0, unit=" mm²/m") + r""" & $\phi$""" + _dkoh(KEY_DD_DIA_OH, nd=0) + r""" @ """ + _dkoh(KEY_DD_SPC_OH, nd=0) + r""" mm c/c (""" + _dkoh(KEY_DD_AS_OH, nd=0) + r""" mm²/m) & """ + (_dks(_dkv(KEY_DD_AS_OH) >= _dkv(KEY_DD_AS_REQ_OH)) if _dk_oh else ("N/A" if _dk_has else "---")) + r""" \\[6pt]
\hline
\multicolumn{4}{|l|}{\textbf{Cover and Detailing}} \\[6pt]
\hline
Clear Cover (IRC 112 Cl. 15.2) & $\geq$ """ + _dkf(KEY_DD_MIN_COVER, nd=0) + r""" mm (Table 14.2) & Top """ + _render_value(bridge.input_dict, KEY_DS_TOP_CLEAR_COVER) + r""" / Bottom """ + _render_value(bridge.input_dict, KEY_DS_BOTTOM_CLEAR_COVER) + r""" mm & """ + _dks(bool(deck_rpt.get(KEY_DD_COVER_OK))) + r""" \\[6pt]
\hline
\end{longtable}
\noindent\textit{Note: IRC 112 Cl. 16.3, IS 456 Cl. 26.5. All reinforcement provisions satisfy strength and detailing requirements.}

% ===========================
\section{Cross Bracing Design}
\label{sec:cross-bracing}
% ===========================

Cross bracing between adjacent plate girders provides lateral stability during construction, resists transverse loads (wind, seismic, braking) in service, and prevents lateral torsional buckling of the girders. Members are designed per IS~800:2007 Cl.~7 (compression) and Cl.~6 (tension). Forces are derived from the grillage model under the governing load combination  (DL + LL + WL).

\vspace{1em}

\vspace{0.4em}
\noindent
\setlength{\tabcolsep}{4pt}
\setlength\LTleft{0pt}
\setlength\LTright{\fill}

\begin{longtable}{|C{2.0cm}|L{2.0cm}|L{2.2cm}|C{2.5cm}|C{2.0cm}|C{2.0cm}|}
\caption{\textbf{Cross Bracing --- Connection and Section Properties}}
\hline
\textbf{Panel} & \textbf{Member} & \textbf{Connection} & \textbf{Section} & \textbf{$A_g$ (mm²)} & \textbf{$r_{min}$ (mm)} \\[6pt]
\hline
""" + cb_forces_content + r"""
\end{longtable}
\noindent\textit{Note: $A_g$ = gross cross-sectional area; $r_{min}$ = minimum radius of gyration.}

\vspace{1em}
\begin{longtable}{|C{2.2cm}|L{2.2cm}|L{2.5cm}|C{2.5cm}|C{2.5cm}|>{\centering\arraybackslash}p{3.6cm}|}
\caption{\textbf{Cross Bracing --- Slenderness Ratio Check (IS~800 Cl.~3.8 )}}
\hline
\textbf{Panel} & \textbf{Member} & \textbf{Nature} & \textbf{Eff.\ Length $KL$ (mm)} & \textbf{$KL/r$} & \textbf{Limit / Status} \\[6pt]
\hline
""" + cb_slenderness_content + r"""
\end{longtable}
\noindent\textit{Note:  3. Limit = 250 for compression members, 400 for tension members. $K = 1.0$ for members with both ends pinned.}

\vspace{1em}
\begin{longtable}{|C{2.0cm}|L{1.8cm}|C{2.2cm}|C{3.0cm}|C{1.8cm}|C{1.8cm}|C{1.2cm}|C{1.8cm}|}
\caption{\textbf{Cross Bracing Design --- Capacity Summary}}
\hline
\textbf{Panel} & \textbf{Member} & \textbf{Section} & \textbf{Governing LC} & \textbf{Demand (kN)} & \textbf{Capacity (kN)} & \textbf{UR} & \textbf{Status} \\[6pt]
\hline
""" + cb_capacity_content + r"""
\end{longtable}
\noindent\textit{Note: Designed per IS 800 Cl. 7 (compression) and Cl. 6 (tension). OsdagBridge cross-bracing module used.}

% ===========================
\section{End Diaphragm Design}
\label{sec:end-diaphragm}
% ===========================

End diaphragms at the supports transfer transverse loads to the bearings, restrain the bottom flanges against lateral displacement, and maintain the girder cross-section geometry during construction and in service. They are designed per IS~800:2007 and IRC~24:2010 Cl.~507.

\vspace{1em}

\vspace{0.4em}
\noindent
\setlength{\tabcolsep}{4pt}
\setlength{\LTleft}{0pt}
\setlength{\LTright}{\fill}

\begin{longtable}{|C{2.0cm}|L{2.0cm}|L{2.2cm}|C{2.5cm}|C{2.0cm}|C{2.0cm}|}
\caption{\textbf{End Diaphragm --- Connection and Section Properties}}
\hline
\textbf{Panel} & \textbf{Member} & \textbf{Connection} & \textbf{Section} & \textbf{$A_g$ (mm²)} & \textbf{$r_{min}$ (mm)} \\[6pt]
\hline
""" + cb_forces_content + r"""
\end{longtable}
\noindent\textit{Note: $A_g$ = gross cross-sectional area; $r_{min}$ = minimum radius of gyration.}

\vspace{1em}
\begin{longtable}{|C{2.2cm}|L{2.2cm}|L{2.5cm}|C{2.5cm}|C{2.5cm}|>{\centering\arraybackslash}p{3.6cm}|}
\caption{\textbf{End Diaphragm --- Slenderness Ratio Check (IS~800 Cl.~3.8 )}}
\hline
\textbf{Panel} & \textbf{Member} & \textbf{Nature} & \textbf{Eff.\ Length $KL$ (mm)} & \textbf{$KL/r$} & \textbf{Limit / Status} \\[6pt]
\hline
""" + cb_slenderness_content + r"""
\end{longtable}
\noindent\textit{Note:  3. Limit = 250 for compression members, 400 for tension members. $K = 1.0$ for members with both ends pinned.}

\vspace{1em}

\begin{longtable}{|C{2.0cm}|L{1.8cm}|C{2.2cm}|C{3.0cm}|C{1.8cm}|C{1.8cm}|C{1.2cm}|C{1.8cm}|}
\caption{\textbf{End Diaphragm Design --- Capacity Summary}}
\hline
\textbf{Panel} & \textbf{Member} & \textbf{Section} & \textbf{Governing LC} & \textbf{Demand (kN)} & \textbf{Capacity (kN)} & \textbf{UR} & \textbf{Status} \\[6pt]
\hline
""" + cb_capacity_content + r"""
\end{longtable}
\noindent\textit{Note: Designed per IS 800 Cl. 7 (compression) and Cl. 6 (tension). OsdagBridge cross-bracing module used.}

% ===========================
\section{Overall Design Check Summary}
\label{sec:overall-summary}
% ===========================

\vspace{1em}
\begin{longtable}{|C{3.4cm}|L{4.5cm}|C{2.3cm}|C{2.3cm}|>{\centering\arraybackslash}p{1.6cm}|}
\caption{\textbf{Overall Design Check Summary --- All Members}}
\hline
\textbf{Member / Check} & \textbf{Governing Load Combo} & \textbf{Demand} & \textbf{Capacity} & \textbf{UR} \\[6pt]
\hline
""" + t522_content + r"""
\end{longtable}
\noindent\textit{Note: UR = Demand / Capacity. All values $\leq 1.0$ indicate passing checks. The governing check for each component is highlighted in the individual design check sections above.}

"""

