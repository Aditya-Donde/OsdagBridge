# Unit definitions
kilo = 1e3
milli = 1e-3
N = 1
m = 1
mm = milli * m
m2 = m ** 2
m3 = m ** 3
m4 = m ** 4
kN = kilo * N
Pa = 1
MPa = N / ((mm) ** 2)
GPa = kilo * MPa
kPa = kilo * Pa
g = 9.81

# ========== Type of Fields Start ==========================================================
TYPE_MODULE = "module"
TYPE_TITLE = "title"
TYPE_COMBOBOX = "combobox"
TYPE_COMBOBOX_CUSTOMIZED = "combobox_customized"
TYPE_TEXTBOX = "textbox"
TYPE_IMAGE = "image"
TYPE_BUTTON = "button"
TYPE_NOTE   = "note"
TYPE_CHECKBOX       = "checkbox"
TYPE_CHECKBOX_ROW   = "checkbox_row"
TYPE_CHECKBOX_GRID  = "checkbox_grid"
TYPE_PERCENT_BAR = "percent_bar"
TYPE_ONLY_BUTTON = "only_button"
TYPE_RADIO_GRID = "radio_button_grid"
TYPE_NOTICE = "notice"
TYPE_BOUND_BTN = "bounds_dialog_btn"
TYPE_TABLE_WITH_COUNTER = "table_with_count"
TYPE_DIRECT_WIDGET = "direct_widget_classes"
TYPE_MODE_LINE = "mode_line_edit"
TYPE_DESCRIPTION = "description"

TYPE_CUSTOM_VEHICLE    = "custom_vehicle"
TYPE_LOAD_COMBINATION = "load_combination"
TYPE_MODE_VALUE = "mode_value"
TYPE_SEGMENT_TABLE  = "segment_table"
TYPE_ADAPTIVE = "adaptive"
TYPE_ALL_CUSTOM = "all_custom"   # combo [All, Custom] where Custom opens popup dialog

# ========== Type of Fields End ==========================================================

# Keys for inputs (consistent dot notation for object names)
KEY_MODULE = "Module"
KEY_STRUCTURE_TYPE = "structure.type"
KEY_PROJECT_LOCATION = "project.location"
KEY_SPAN = "geometry.span"
KEY_CARRIAGEWAY_WIDTH = "geometry.carriageway_width"
KEY_INCLUDE_MEDIAN = "geometry.include_median"
KEY_FOOTPATH = "geometry.footpath"
KEY_SKEW_ANGLE = "geometry.skew_angle"
KEY_ADDITIONAL_GEOMETRY = "geometry.additional_btn"
KEY_DESIGN_MODE = "geometry.design_mode"
KEY_GIRDER = "material.girder"
KEY_CROSS_BRACING = "material.cross_bracing"
KEY_END_DIAPHRAGM = "material.end_diaphragm"
KEY_DECK = "Deck"
KEY_DECK_CONCRETE_GRADE_BASIC = "material.deck"

# ===== Material property keys (populated from DB or user custom inputs) =====
# Steel - girder / structural members
KEY_MATERIAL_GIRDER_FY = "material.girder.fy"
KEY_MATERIAL_GIRDER_FU = "material.girder.fu"
KEY_MATERIAL_GIRDER_E = "material.girder.e"
KEY_MATERIAL_GIRDER_G = "material.girder.g"
KEY_MATERIAL_GIRDER_POISSON = "material.girder.poisson"
KEY_MATERIAL_GIRDER_THERMAL = "material.girder.thermal"
KEY_MATERIAL_GIRDER_DENSITY = "material.girder.density"

# Steel - other member-specific canonical keys (cross bracing, end diaphragm)
KEY_MATERIAL_CROSS_BRACING_FY = "material.cross_bracing.fy"
KEY_MATERIAL_CROSS_BRACING_FU = "material.cross_bracing.fu"
KEY_MATERIAL_CROSS_BRACING_E = "material.cross_bracing.e"
KEY_MATERIAL_CROSS_BRACING_G = "material.cross_bracing.g"
KEY_MATERIAL_CROSS_BRACING_POISSON = "material.cross_bracing.poisson"
KEY_MATERIAL_CROSS_BRACING_THERMAL = "material.cross_bracing.thermal"
KEY_MATERIAL_CROSS_BRACING_DENSITY = "material.cross_bracing.density"

KEY_MATERIAL_END_DIAPHRAGM_FY = "material.end_diaphragm.fy"
KEY_MATERIAL_END_DIAPHRAGM_FU = "material.end_diaphragm.fu"
KEY_MATERIAL_END_DIAPHRAGM_E = "material.end_diaphragm.e"
KEY_MATERIAL_END_DIAPHRAGM_G = "material.end_diaphragm.g"
KEY_MATERIAL_END_DIAPHRAGM_POISSON = "material.end_diaphragm.poisson"
KEY_MATERIAL_END_DIAPHRAGM_THERMAL = "material.end_diaphragm.thermal"
KEY_MATERIAL_END_DIAPHRAGM_DENSITY = "material.end_diaphragm.density"

# Concrete - deck
KEY_MATERIAL_DECK_FCK = "material.deck.fck"
KEY_MATERIAL_DECK_FCTM = "material.deck.fctm"
KEY_MATERIAL_DECK_ECM = "material.deck.ecm"
KEY_MATERIAL_DECK_THERMAL = "material.deck.thermal"
KEY_MATERIAL_DECK_DENSITY = "material.deck.density"

# Display labels for material property fields
DISP_MATERIAL_GIRDER_DENSITY = "Weight Density (kN/m³)"
DISP_MATERIAL_GIRDER_FY = "Yield Strength, F<sub>y</sub> (MPa)"
DISP_MATERIAL_GIRDER_FU = "Ultimate Tensile Strength, F<sub>u</sub> (MPa)"
DISP_MATERIAL_GIRDER_E = "Modulus of Elasticity, E (GPa)"
DISP_MATERIAL_GIRDER_G = "Modulus of Rigidity, G (GPa)"
DISP_MATERIAL_GIRDER_POISSON = "Poisson&apos;s Ratio, &nu;"
DISP_MATERIAL_GIRDER_THERMAL = "Thermal Expansion Coefficient, (&times;10<sup>&minus;6</sup>/°C)"

DISP_MATERIAL_DECK_DENSITY = "Weight Density (kN/m³)"
DISP_MATERIAL_DECK_FCK = "Characteristic Compressive (Cube) Strength of Concrete, f<sub>ck</sub> (MPa)"
DISP_MATERIAL_DECK_FCTM = "Mean Tensile Strength of Concrete, f<sub>ctm</sub> (MPa)"
DISP_MATERIAL_DECK_ECM = "Secant Modulus of Elasticity of Concrete, E<sub>cm</sub> (GPa)"
DISP_MATERIAL_DECK_THERMAL = "Thermal Expansion Coefficient, (&times;10<sup>&minus;6</sup>/°C)"

# ── Output section keys ───────────────────────────────────────────────────────
KEY_SECTION_OUTPUT_ANALYSIS       = "section.output.analysis"
KEY_SECTION_OUTPUT_SUPERSTRUCTURE = "section.output.superstructure"
KEY_SECTION_OUTPUT_SUBSTRUCTURE   = "section.output.substructure"
KEY_SECTION_OUTPUT_STEELDESIGN = "section.output.superstructure.steeldesign"

# ── Output field keys ─────────────────────────────────────────────────────────
KEY_ANALYSIS_MEMBER           = "analysis.member"
KEY_ANALYSIS_LOAD_COMBINATION = "analysis.load_combination"
KEY_ANALYSIS_FORCES           = "analysis.forces"
KEY_ANALYSIS_DISPLAY_OPTIONS  = "analysis.display_options"
KEY_ANALYSIS_UTILIZATION      = "analysis.utilization"

KEY_STEELDESIGN_MEMBER_ID = "steeldesign.member_id"
KEY_STEELDESIGN_LOAD_COMBINATION = "steeldesign.load_combination"

KEY_OUTPUT_DOCK_MEMBER_ID        = "dock.member_id"
KEY_OUTPUT_DOCK_LOAD_COMBINATION = "dock.load_combination"

KEY_OUTPUT_DOCK_MEMBER_ID        = "dock.member_id"
KEY_OUTPUT_DOCK_LOAD_COMBINATION = "dock.load_combination"

# Steel design details UI keys
KEY_SD_DETAILS_DIMENSIONAL_CARD = "steeldesign.details.dimensional"
KEY_SD_DETAILS_SHEAR_CARD = "steeldesign.details.shear_connector"
KEY_SD_DETAILS_SECTION_PROPERTIES_CARD = "steeldesign.details.section_properties"
KEY_SD_DETAILS_STIFFENER_TABLE = "steeldesign.details.stiffener.table"
KEY_SD_DETAILS_CAD_TOP = "steeldesign.details.cad.top"
KEY_SD_DETAILS_CAD_BOTTOM = "steeldesign.details.cad.bottom"

KEY_SD_GRADE_OF_MATERIAL = "steeldesign.details.grade_of_material"
KEY_SD_SECTION_TYPE = "steeldesign.details.section_type"
KEY_SD_SECTION_DESIGNATION = "steeldesign.details.section_designation"
KEY_SD_SECTION_CLASS = "steeldesign.details.section_class"
KEY_SD_TOTAL_DEPTH = "steeldesign.details.total_depth"
KEY_SD_WEB_THICKNESS = "steeldesign.details.web_thickness"
KEY_SD_TOP_FLANGE_WIDTH = "steeldesign.details.top_flange_width"
KEY_SD_TOP_FLANGE_THICKNESS = "steeldesign.details.top_flange_thickness"
KEY_SD_BOTTOM_FLANGE_WIDTH = "steeldesign.details.bottom_flange_width"
KEY_SD_BOTTOM_FLANGE_THICKNESS = "steeldesign.details.bottom_flange_thickness"
KEY_SD_TORSIONAL_RESTRAINT = "steeldesign.details.torsional_restraint"
KEY_SD_WARPING_RESTRAINT = "steeldesign.details.warping_restraint"
KEY_SD_WEB_TYPE = "steeldesign.details.web_type"
KEY_SD_EFFECTIVE_SLAB_WIDTH = "steeldesign.details.effective_slab_width"

KEY_SD_SHEAR_YIELD_STRENGTH = "steeldesign.details.shear.yield_strength"
KEY_SD_SHEAR_ULTIMATE_STRENGTH = "steeldesign.details.shear.ultimate_strength"
KEY_SD_SHEAR_DIAMETER = "steeldesign.details.shear.diameter"
KEY_SD_SHEAR_HEIGHT = "steeldesign.details.shear.height"
KEY_SD_SHEAR_TRANSVERSE_SPACING = "steeldesign.details.shear.transverse_spacing"
KEY_SD_SHEAR_STUDS_PER_SECTION = "steeldesign.details.shear.studs_per_section"
KEY_SD_SHEAR_LONGITUDINAL_SPACING = "steeldesign.details.shear.longitudinal_spacing"

KEY_SD_STIFFENER_ROW_INTERMEDIATE = "steeldesign.details.stiffener.row.intermediate"
KEY_SD_STIFFENER_ROW_LONGITUDINAL = "steeldesign.details.stiffener.row.longitudinal"
KEY_SD_STIFFENER_ROW_BEARING = "steeldesign.details.stiffener.row.bearing"
KEY_SD_STIFFENER_COL_GRADE = "steeldesign.details.stiffener.col.grade"
KEY_SD_STIFFENER_COL_THICKNESS = "steeldesign.details.stiffener.col.thickness"
KEY_SD_STIFFENER_COL_WIDTH = "steeldesign.details.stiffener.col.width"
KEY_SD_STIFFENER_COL_SPACING = "steeldesign.details.stiffener.col.spacing"

# Stiffener inputs
KEY_SD_STIFFENER_DETAILS = "member_properties.stiffener_details.stiffener_details_cad"

# Steel Design Properties
KEY_SD_SECTION_PROP_MASS = "steeldesign.details.section_properties.mass"
KEY_SD_SECTION_PROP_AREA = "steeldesign.details.section_properties.area"
KEY_SD_SECTION_PROP_IZ = "steeldesign.details.section_properties.iz"
KEY_SD_SECTION_PROP_IV = "steeldesign.details.section_properties.iv"
KEY_SD_SECTION_PROP_RZ = "steeldesign.details.section_properties.rz"
KEY_SD_SECTION_PROP_RV = "steeldesign.details.section_properties.rv"
KEY_SD_SECTION_PROP_ZZ = "steeldesign.details.section_properties.zz"
KEY_SD_SECTION_PROP_ZV = "steeldesign.details.section_properties.zv"
KEY_SD_SECTION_PROP_ZUZ = "steeldesign.details.section_properties.zuz"
KEY_SD_SECTION_PROP_ZUV = "steeldesign.details.section_properties.zuv"
KEY_SD_SECTION_PROP_IT = "steeldesign.details.section_properties.it"
KEY_SD_SECTION_PROP_IW = "steeldesign.details.section_properties.iw"

KEY_BTN_STEEL_DESIGN          = "btn.steel_design"
KEY_BTN_TRANSVERSE_DESIGN     = "btn.transverse_design"
KEY_BTN_DECK_DESIGN           = "btn.deck_design"

KEY_UTIL_FLEXURE             = "util.flexure"
KEY_UTIL_SHEAR               = "util.shear"
KEY_UTIL_INTERACTION         = "util.interaction"
KEY_UTIL_LTB                 = "util.ltb"
KEY_UTIL_LONG_TRANS_SHEAR    = "util.long_trans_shear"
KEY_UTIL_FATIGUE             = "util.fatigue"
KEY_UTIL_STRESS_LIMITATION   = "util.stress_limitation"
KEY_UTIL_DEFLECTION_CRACK    = "util.deflection_crack"

#               Deck Slab Design 
# Values computed by deckdesign.design_deck_slab() and stored in
# output_dict["deck_report_values"] for the report generator (Tables 5.17(a)-(g)).
# These are existing computed values only — no new structural calculation.

# -- 5.17(a) Loading & Geometry --
KEY_DD_VEHICLE          = "deck.report.vehicle_class"      # governing IRC 6 vehicle
KEY_DD_IMPACT_FACTOR    = "deck.report.impact_factor"      # 1 + IF
KEY_DD_GAMMA_DL         = "deck.report.gamma_dl"           # ULS partial safety factor (DL)
KEY_DD_GAMMA_LL         = "deck.report.gamma_ll"           # ULS partial safety factor (LL)
KEY_DD_SPAN             = "deck.report.span"               # effective span = girder spacing (m)
KEY_DD_WDL              = "deck.report.w_dl"               # slab dead load (kN/m2)
KEY_DD_WHEEL_LOAD       = "deck.report.wheel_load"         # max single wheel load (kN)
KEY_DD_TYRE_WIDTH       = "deck.report.tyre_contact_width" # transverse tyre contact width (m)
KEY_DD_FY               = "deck.report.fy"                # rebar fy (MPa)

# -- 5.17(b) Interior panel flexure --
KEY_DD_M_DL             = "deck.report.m_dl"              # dead load moment (kNm/m)
KEY_DD_M_LL             = "deck.report.m_ll"              # live load moment, unfactored (kNm/m)
KEY_DD_M_ULS_SAG        = "deck.report.m_uls_sag"        # ULS sagging moment (kNm/m)
KEY_DD_M_ULS_HOG        = "deck.report.m_uls_hog"        # ULS hogging moment (kNm/m)
KEY_DD_D_BOT            = "deck.report.d_bot"            # bottom effective depth (mm)
KEY_DD_D_TOP            = "deck.report.d_top"            # top effective depth (mm)
KEY_DD_MU_BOT           = "deck.report.mu_bot"          # bottom moment capacity (kNm/m)
KEY_DD_MU_TOP           = "deck.report.mu_top"          # top moment capacity (kNm/m)
KEY_DD_AS_REQ_BOT       = "deck.report.as_req_bot"      # bottom required steel (mm2/m)
KEY_DD_AS_REQ_TOP       = "deck.report.as_req_top"      # top required steel (mm2/m)

# -- 5.17(c) Cantilever overhang flexure --
KEY_DD_M_BARRIER        = "deck.report.m_barrier"       # crash barrier moment (kNm/m)
KEY_DD_M_DL_OH          = "deck.report.m_dl_oh"         # overhang dead load moment (kNm/m)
KEY_DD_M_LL_OH          = "deck.report.m_ll_oh"         # overhang live load moment (kNm/m)
KEY_DD_M_ULS_OH         = "deck.report.m_uls_oh"        # overhang ULS hogging moment (kNm/m)
KEY_DD_D_OH             = "deck.report.d_oh"            # overhang effective depth (mm)
KEY_DD_MU_OH            = "deck.report.mu_oh"           # overhang moment capacity (kNm/m)
KEY_DD_AS_REQ_OH        = "deck.report.as_req_oh"       # overhang required steel (mm2/m)

# -- 5.17(d) Punching shear (IRC 112 Cl.10.4) --
KEY_DD_PUNCH_VED_KN     = "deck.report.punch_ved_kn"    # ULS design wheel load, γ_LL·(1+IF)·P_w (kN)
KEY_DD_TYRE_LENGTH      = "deck.report.tyre_contact_length"  # raw longitudinal tyre contact (mm)
KEY_DD_PUNCH_C1         = "deck.report.punch_c1"        # dispersed transverse contact c1 (mm)
KEY_DD_PUNCH_C2         = "deck.report.punch_c2"        # dispersed longitudinal contact c2 (mm)
KEY_DD_PUNCH_U1         = "deck.report.punch_u1"        # control perimeter u1 at 2d (mm)
KEY_DD_PUNCH_VED        = "deck.report.punch_ved"       # punching shear stress v_Ed (MPa)
KEY_DD_VRD_C_MPA        = "deck.report.vrd_c_mpa"       # shear resistance stress v_Rd,c (MPa)
KEY_DD_PUNCH_OK         = "deck.report.punch_ok"        # bool — v_Ed ≤ v_Rd,c

# -- 5.17(e) Crack width --
KEY_DD_AS_MIN           = "deck.report.as_min"          # min reinforcement (mm2/m, IRC112 Cl.16.5.1)
KEY_DD_WK_BOT           = "deck.report.wk_bot"          # bottom crack width (mm)
KEY_DD_WK_TOP           = "deck.report.wk_top"          # top crack width (mm)
KEY_DD_WK_OH            = "deck.report.wk_oh"           # overhang crack width (mm)
KEY_DD_WK_LIMIT         = "deck.report.wk_limit"        # permissible crack width (mm)

# -- 5.17(f) One-way (beam) shear (IRC 112 Cl.10.3.2) --
KEY_DD_SHEAR_VED        = "deck.report.shear_ved"       # ULS design shear demand V_Ed (kN/m)
KEY_DD_SHEAR_VRDC       = "deck.report.shear_vrdc"      # shear resistance V_Rd,c = v_Rd,c·b_w·d (kN/m)
KEY_DD_SHEAR_OK         = "deck.report.shear_ok"        # bool — V_Ed ≤ V_Rd,c

# -- 5.17(g) Reinforcement detailing (provided bars) --
KEY_DD_DIA_BOT          = "deck.report.dia_bot"         # bottom bar diameter (mm)
KEY_DD_SPC_BOT          = "deck.report.spc_bot"         # bottom bar spacing (mm)
KEY_DD_AS_BOT           = "deck.report.as_bot"          # bottom steel provided (mm2/m)
KEY_DD_DIA_TOP          = "deck.report.dia_top"         # top bar diameter (mm)
KEY_DD_SPC_TOP          = "deck.report.spc_top"         # top bar spacing (mm)
KEY_DD_AS_TOP           = "deck.report.as_top"          # top steel provided (mm2/m)
KEY_DD_DIA_OH           = "deck.report.dia_oh"          # overhang bar diameter (mm)
KEY_DD_SPC_OH           = "deck.report.spc_oh"          # overhang bar spacing (mm)
KEY_DD_AS_OH            = "deck.report.as_oh"           # overhang steel provided (mm2/m)
KEY_DD_AS_LONG          = "deck.report.as_long"         # distribution (longitudinal) steel provided (mm2/m)
KEY_DD_MIN_COVER        = "deck.report.min_cover"       # IRC 112 Table 14.2 recommended min cover (mm)
KEY_DD_COVER_OK         = "deck.report.cover_ok"        # bool — provided covers ≥ min cover
KEY_DD_SPACING_MAX      = "deck.report.spacing_max"     # max permissible bar spacing (mm)
KEY_DD_HAS_OVERHANG     = "deck.report.has_overhang"    # bool — overhang present

# Module + section identifiers (also used as UI keys)
KEY_MODULE_PLATE_GIRDER = "module.plate_girder"
KEY_SECTION_STRUCTURE = "section.structure"
KEY_SECTION_PROJECT      = "section.project"
KEY_SECTION_GEOMETRIC = "section.geometry"
KEY_SECTION_ADDITIONAL_GEOMETRY = "section.additonal_geometry"
KEY_SECTION_DESIGN_TYPE  = "section.design_type"
KEY_SECTION_MATERIAL = "section.material"

# Display names
DISP_TITLE_STRUCTURE = "Type of Structure"
KEY_DISP_STRUCTURE_TYPE = "Structure Type"
DISP_TITLE_PROJECT = "Project Location"
KEY_DISP_PROJECT_LOCATION = "City in India*"
DISP_TITLE_GEOMETRIC = "Geometric Details"
KEY_DISP_SPAN = "Span (m)"
KEY_DISP_CARRIAGEWAY_WIDTH = "Carriageway Width\n(Each way) (m)"
KEY_DISP_FOOTPATH = "Footpath"
KEY_DISP_SKEW_ANGLE = "Skew Angle (deg)"
DISP_TITLE_MATERIAL = "Material Inputs"
KEY_DISP_GIRDER = "Girder"
KEY_DISP_CROSS_BRACING = "Cross Bracing"
KEY_DISP_END_DIAPHRAGM = "End Diaphragm"
KEY_DISP_DECK_CONCRETE_GRADE = "Deck"

# Sample values
VALUES_STRUCTURE_TYPE = ["Highway Bridge", "Other"]

# Canonical footpath options used across UI + CAD/code clauses.
VALUES_FOOTPATH = ["None", "Single Side", "Both Sides"]

# Validation limits
SPAN_MIN = 20.0
SPAN_MAX = 45.0
CARRIAGEWAY_WIDTH_MIN = 4.25
CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN = 7.5
CARRIAGEWAY_WIDTH_MAX_LIMIT = 23.6
SKEW_ANGLE_MIN = -15.0
SKEW_ANGLE_MAX = 15.0
SKEW_ANGLE_DEFAULT = 0.0

# ===== Additional Inputs Constants =====

# Typical Section Details Keys
KEY_DECK_CONCRETE_GRADE = "Deck Concrete Grade"
KEY_DECK_REINF_MATERIAL = "Deck Reinforcement Material"
KEY_DECK_REINF_SIZE = "Deck Reinforcement Size"
KEY_DECK_REINF_SPACING_LONG = "Deck Reinforcement Spacing Longitudinal"
KEY_DECK_REINF_SPACING_TRANS = "Deck Reinforcement Spacing Transverse"

# ── Generate-Results SLS stress table keys ────────────────────────────────────
# Structural steel: single envelope-SLS equivalent stress applied to every
# girder/member row, plus its allowable (0.9·fy). Stored in design_results.
KEY_SD_STRESS_STEEL           = "steeldesign.stress.steel"
KEY_SD_STRESS_STEEL_ALLOWABLE = "steeldesign.stress.steel.allowable"
# Concrete deck (interior panel SLS): bottom & top fibre stress share one limit
# (0.48·fck). Stored in deck_design_results.
# ULS check per-girder table (stored in design_results under this key)
KEY_SD_ULS_PER_GIRDER         = "steeldesign.uls_per_girder"
KEY_DD_STRESS_CONC_BOTTOM     = "deckdesign.stress.concrete.bottom"
KEY_DD_STRESS_CONC_TOP        = "deckdesign.stress.concrete.top"
KEY_DD_STRESS_CONC_ALLOWABLE  = "deckdesign.stress.concrete.allowable"
# Reinforcement (interior panel SLS): bottom & top fibre stress share one limit
# (0.80·fyk). Stored in deck_design_results.
KEY_DD_STRESS_REINF_BOTTOM    = "deckdesign.stress.reinf.bottom"
KEY_DD_STRESS_REINF_TOP       = "deckdesign.stress.reinf.top"
KEY_DD_STRESS_REINF_ALLOWABLE = "deckdesign.stress.reinf.allowable"

# ── Generate-Results Shear Connector table keys ───────────────────────────────
# All stored as flat keys in design_results after run_design_check.
KEY_SD_SC_Qu_kN            = "steeldesign.shear_connector.qu_kN"
KEY_SD_SC_Qr_kN            = "steeldesign.shear_connector.qr_kN"
KEY_SD_SC_VL               = "steeldesign.shear_connector.vl_n_per_mm"
KEY_SD_SC_SL1              = "steeldesign.shear_connector.sl1_mm"
KEY_SD_SC_SL2              = "steeldesign.shear_connector.sl2_mm"
KEY_SD_SC_SR               = "steeldesign.shear_connector.sr_mm"
KEY_SD_SC_H_kN             = "steeldesign.shear_connector.h_governing_kN"
KEY_SD_SC_Vr_kN            = "steeldesign.shear_connector.vr_kN"
KEY_SD_SC_LIMIT_600        = "steeldesign.shear_connector.limit_600_mm"
KEY_SD_SC_LIMIT_3TSLAB     = "steeldesign.shear_connector.limit_3tslab_mm"
KEY_SD_SC_LIMIT_4HSTUD     = "steeldesign.shear_connector.limit_4hstud_mm"
KEY_SD_SC_D_LIMIT          = "steeldesign.shear_connector.d_limit_mm"
KEY_SD_SC_H_MIN            = "steeldesign.shear_connector.h_min_mm"
KEY_SD_SC_EDGE_DIST        = "steeldesign.shear_connector.edge_distance_mm"
KEY_SD_SC_REQ_EDGE_DIST    = "steeldesign.shear_connector.req_edge_distance_mm"
KEY_SD_SC_CLEAR_COVER      = "steeldesign.shear_connector.clear_cover_mm"
KEY_SD_SC_REQ_CLEAR_COVER  = "steeldesign.shear_connector.req_clear_cover_mm"

# ── Generate-Results Transverse Shear table keys (design_results) ─────────────
# IRC 22:2015 Cl.606.10 — interface shear between steel girder and deck slab.
KEY_SD_TS_VL         = "steeldesign.transverse_shear.vl_kN_per_m"
KEY_SD_TS_VCAP_CONC  = "steeldesign.transverse_shear.vcap_concrete_kN_per_m"
KEY_SD_TS_VCAP_REINF = "steeldesign.transverse_shear.vcap_reinf_kN_per_m"
KEY_SD_TS_VRD        = "steeldesign.transverse_shear.vrd_kN_per_m"

# ── Generate-Results Crack Width table keys ───────────────────────────────────
# Minimum crack-control reinforcement (IRC 22 Cl.604.4) — design_results.
KEY_SD_CRACK_AS_MIN  = "steeldesign.crack.as_min_mm2"
KEY_SD_CRACK_AS_PROV = "steeldesign.crack.as_provided_mm2"
# Calculated crack width per face (IRC 112:2020 Cl.12.3.4) — deck_design_results.
KEY_DD_CRACK_WK_BOTTOM = "deckdesign.crack.wk.bottom"
KEY_DD_CRACK_WK_TOP    = "deckdesign.crack.wk.top"
KEY_DD_CRACK_WK_LIMIT  = "deckdesign.crack.wk.limit"

KEY_RAILING_PRESENT = "Railing Present"
KEY_RAILING_WIDTH = "Railing Width"
KEY_RAILING_HEIGHT = "Railing Height"
KEY_RAILING_MIN_HEIGHT = [1100, 1250]
KEY_CYCLE_TRACK = ["None", "Single", "Both Sides"]
KEY_MIN_SKEW_ANGLE = 30
KEY_MIN_LOGITUDINAL_GRADIENT = 0.3
KEY_MAX_BRIDGE_LENGTH_SINGLE_CURVE = 30
KEY_MIN_SINGLE_LANE = 4.25
KEY_MIN_DOUBLE_LANE = 7.5
KEY_ADDITIONAL_LANE = 3.5

KEY_SAFETY_KERB_PRESENT = "Safety Kerb Present"
KEY_SAFETY_KERB_WIDTH = "Safety Kerb Width"
KEY_SAFETY_KERB_THICKNESS = "Safety Kerb Thickness"
KEY_SAFETY_KERB_MIN_WIDTH = 750
KEY_SAFETY_KERB_PLACEMENT = ["Single Side", "Both Sides"]

KEY_CRASH_BARRIER_PRESENT = "Crash Barrier Present"
KEY_CRASH_BARRIER_DENSITY = "Crash Barrier Material Density"
KEY_CRASH_BARRIER_WIDTH = "Crash Barrier Width"
KEY_CRASH_BARRIER_AREA = "Crash Barrier Area"

#══════════════TYPICAL-SECTION-TAB-KEY-START═══════════════════════════════════════════════════════

# Typical Section - Crash Barrier Type Keys
KEY_MP_CB_TAB = "typical_section.crash_barrier.tab"
KEY_CB_TYPE = "typical_section.crash_barrier.type"
KEY_CB_DENSITY = "typical_section.crash_barrier.density"
KEY_CB_WIDTH = "typical_section.crash_barrier.width"
KEY_CB_HEIGHT = "typical_section.crash_barrier.height"
KEY_CB_AREA = "typical_section.crash_barrier.area"
KEY_CB_LOAD = "typical_section.crash_barrier.load"
KEY_CB_POST_SPACING = "typical_section.crash_barrier.post_spacing"

# Typical Section - Median (UI object names / schema ids)
KEY_MD_TAB = "typical_section.median.tab"
KEY_MD_TYPE = "typical_section.median.type"
KEY_MD_DENSITY = "typical_section.median.density"
KEY_MD_WIDTH = "typical_section.median.width"
KEY_MD_HEIGHT = "typical_section.median.height"
KEY_MD_AREA = "typical_section.median.area"
KEY_MD_LOAD = "typical_section.median.load"
KEY_MD_POST_SPACING = "typical_section.median.post_spacing"

# Typical Section - Railing
KEY_RL_TAB = "typical_section.railing.tab"
KEY_RL_TYPE = "typical_section.railing.type"
KEY_RL_WIDTH = "typical_section.railing.width"
KEY_RL_HEIGHT = "typical_section.railing.height"
KEY_RL_LOAD_MODE = "typical_section.railing.load_mode"
KEY_RL_LOAD_VALUE = "typical_section.railing.load_value"

# Typical Section - Wearing course
KEY_WC_TAB = "typical_section.wearing_course.tab"
KEY_WC_MATERIAL = "typical_section.wearing_course.material"
KEY_WC_DENSITY = "typical_section.wearing_course.density"
KEY_WC_THICKNESS = "typical_section.wearing_course.thickness"

# Typical Section - primary fields (above subtab bar)
KEY_TS_TAB                = "typical_section.tab"
KEY_TS_DECK_TAB           = "typical_section.deck_details.tab"
KEY_TS_GIRDER_SPACING     = "typical_section.girder_spacing"
KEY_TS_NO_OF_GIRDERS      = "typical_section.no_of_girders"
KEY_TS_DECK_OVERHANG      = "typical_section.deck_overhang"
KEY_TS_OVERALL_WIDTH      = "typical_section.overall_bridge_width"
KEY_TS_DECK_THICKNESS     = "typical_section.deck_thickness"
KEY_TS_NO_OF_FOOTPATHS    = "typical_section.no_of_footpaths"
KEY_TS_FOOTPATH_WIDTH     = "typical_section.footpath_width"
KEY_TS_FOOTPATH_THICKNESS = "typical_section.footpath_thickness"

# Typical Section - Lane Deatils
KEY_WC_LD_TAB = "typical_section.lane_details.tab"
KEY_WC_LD_LANE_TABLE = "typical_section.lane_details.lane_table"
KEY_WC_LD_LANE_TABLE_COUNT = "typical_section.lane_details.lane_table_count"

#══════════════TYPICAL-SECTION-TAB-KEY-ENDS═══════════════════════════════════════════════════════

#══════════════MEMBER-PROPERTIES-TAB-KEY-STARTS═══════════════════════════════════════════════════════
KEY_MEMBER_PROPERTIES_TAB           = "member_properties"

#-------------- Girder Details Sub-Tab --------------------------------------------
KEY_MP_GD_TAB                          = "member_properties.girder_details"
KEY_MP_GD_SP                           = "member_properties.girder_details.section_properties"
KEY_MP_GD_SECTION_DRAWING              = "member_properties.girder_details.section_drawing"
KEY_MP_GD_CAD_BTN_CROSS_SECTION = "member_properties.girder_details.cad_btn.cross_section"
KEY_MP_GD_CAD_BTN_SIDE_VIEW     = "member_properties.girder_details.cad_btn.side_view"

# Top-level composite fields
KEY_MP_GD_CAD_PREVIEW                  = "member_properties.girder_details.cad_preview"
KEY_MP_GD_SEGMENT_TABLE                = "member_properties.girder_details.segment_table"
 
# Overview fields
KEY_MP_GD_SELECT_GIRDER                = "member_properties.girder_details.select_girder"
KEY_MP_GD_SPAN                         = "member_properties.girder_details.span"
KEY_MP_GD_TOTAL_SPAN                   = "member_properties.girder_details.total_span"
 
# Section inputs
KEY_MP_GIRDER_TYPE                    = "member_properties.girder_details.section_input.type"
KEY_MP_GIRDER_SYMMETRY                = "member_properties.girder_details.section_input.symmetry"
KEY_MP_GIRDER_DEPTH                   = "member_properties.girder_details.section_input.depth"
KEY_MP_GIRDER_TOP_FLANGE_WIDTH        = "member_properties.girder_details.section_input.top_flange_width"
KEY_MP_GIRDER_TOP_FLANGE_THICKNESS    = "member_properties.girder_details.section_input.top_flange_thickness"
KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH     = "member_properties.girder_details.section_input.bottom_flange_width"
KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS = "member_properties.girder_details.section_input.bottom_flange_thickness"
KEY_MP_GD_SUPPORT_TYPE                = "member_properties.girder_details.section_inputs.support_type"
KEY_MP_GD_SUPPORT_WIDTH               = "member_properties.girder_details.section_inputs.support_width"
KEY_MP_GIRDER_WEB_THICKNESS           = "member_properties.girder_details.section_input.web_thickness"
KEY_MP_GIRDER_IS_SECTION              = "member_properties.girder_details.section_input.is_section"
KEY_MP_GIRDER_TORSIONAL_RESTRAINT     = "member_properties.girder_details.section_input.torsional_restraint"
KEY_MP_GIRDER_WARPING_RESTRAINT       = "member_properties.girder_details.section_input.warping_restraint"
KEY_MP_GIRDER_WEB_TYPE                = "member_properties.girder_details.section_input.web_type"

KEY_MP_GD_MEMBER_ID                      = "member_properties.girder_details.member_id"
KEY_MP_GD_APPLY_EXTERIOR                 = "member_properties.girder_details.apply_exterior"
KEY_MP_GD_APPLY_INTERIOR                 = "member_properties.girder_details.apply_interior"
KEY_MP_GD_SECTION_PREVIEW                = "member_properties.girder_details.section_preview"

# Steel Design Properties
KEY_MP_GIRDER_MASS = "member_properties.girder_details.section_properties.mass"
KEY_MP_GIRDER_SECTIONAL_AREA = "member_properties.girder_details.section_properties.area"
KEY_MP_GIRDER_SECTIONAL_IY = "member_properties.girder_details.section_properties.iy"
KEY_MP_GIRDER_SECTIONAL_IZ = "member_properties.girder_details.section_properties.iz"
KEY_MP_GIRDER_RADIUS_GYRATION_Y = "member_properties.girder_details.section_properties.radius_gyration_y"
KEY_MP_GIRDER_RADIUS_GYRATION_Z = "member_properties.girder_details.section_properties.radius_gyration_z"
KEY_MP_GIRDER_ELASTIC_MODULUS_ZZ = "member_properties.girder_details.material_properties.modulus_of_elasticity_zz"
KEY_MP_GIRDER_ELASTIC_MODULUS_ZY = "member_properties.girder_details.material_properties.modulus_of_elasticity_zy"
KEY_MP_GIRDER_PLASTIC_MODULUS_ZUZ = "member_properties.girder_details.material_properties.plastic_modulus_zuz"
KEY_MP_GIRDER_PLASTIC_MODULUS_ZUY = "member_properties.girder_details.material_properties.plastic_modulus_zuy"
KEY_MP_GIRDER_TORSION_CONSTANT_IT = "member_properties.girder_details.section_properties.torsion_constant_it"
KEY_MP_GIRDER_WARPING_CONSTANT_IW = "member_properties.girder_details.section_properties.warping_constant_iw"
KEY_SD_SECTION_PROP_MASS = "steeldesign.details.section_properties.mass"
KEY_SD_SECTION_PROP_AREA = "steeldesign.details.section_properties.area"
KEY_SD_SECTION_PROP_IZ = "steeldesign.details.section_properties.iz"
KEY_SD_SECTION_PROP_IV = "steeldesign.details.section_properties.iv"
KEY_SD_SECTION_PROP_RZ = "steeldesign.details.section_properties.rz"
KEY_SD_SECTION_PROP_RV = "steeldesign.details.section_properties.rv"
KEY_SD_SECTION_PROP_ZZ = "steeldesign.details.section_properties.zz"
KEY_SD_SECTION_PROP_ZV = "steeldesign.details.section_properties.zv"
KEY_SD_SECTION_PROP_ZUZ = "steeldesign.details.section_properties.zuz"
KEY_SD_SECTION_PROP_ZUV = "steeldesign.details.section_properties.zuv"
KEY_SD_SECTION_PROP_IT = "steeldesign.details.section_properties.it"
KEY_SD_SECTION_PROP_IW = "steeldesign.details.section_properties.iw"
KEY_SD_COMPOSITE_IZ    = "steeldesign.details.section_properties.composite_iz"   # only for report
KEY_SD_PNA_DEPTH       = "steeldesign.details.section_properties.pna_depth"       # only for report
KEY_SD_MU_APPLIED      = "steeldesign.details.moment.mu_applied"                  # only for report
KEY_SD_MD_CAPACITY     = "steeldesign.details.moment.md_capacity"                 # only for report
KEY_SD_FLANGE_SLENDERNESS = "steeldesign.details.classification.flange_slenderness"  # only for report
KEY_SD_WEB_SLENDERNESS    = "steeldesign.details.classification.web_slenderness"     # only for report
KEY_SD_WEB_CLASS_LIMIT    = "steeldesign.details.classification.web_class_limit"     # only for report
KEY_SD_FLANGE_CLASS_LIMIT = "steeldesign.details.classification.flange_class_limit"  # only for report
KEY_SD_SHEAR_VU         = "steeldesign.details.shear_check.vu_applied"      # only for report
KEY_SD_SHEAR_AV         = "steeldesign.details.shear_check.av_area"         # only for report
KEY_SD_PANEL_CD         = "steeldesign.details.shear_check.panel_cd"        # only for report
KEY_SD_SHEAR_KV         = "steeldesign.details.shear_check.kv"              # only for report
KEY_SD_SHEAR_LAMBDA_W   = "steeldesign.details.shear_check.lambda_w"        # only for report
KEY_SD_SHEAR_TAU_B      = "steeldesign.details.shear_check.tau_b"           # only for report
KEY_SD_SHEAR_VCR        = "steeldesign.details.shear_check.vcr"             # only for report
KEY_SD_HIGH_SHEAR       = "steeldesign.details.interaction.high_shear"      # only for report
KEY_SD_MDV              = "steeldesign.details.interaction.mdv"             # only for report
KEY_SD_MN_AXIAL         = "steeldesign.details.interaction.mn_axial"        # only for report
KEY_SD_MN_MOMENT        = "steeldesign.details.interaction.mn_moment"       # only for report
KEY_SD_MN_RATIO         = "steeldesign.details.interaction.mn_ratio"        # only for report
KEY_SD_LTB_MCR          = "steeldesign.details.ltb.mcr"                     # only for report
KEY_SD_LTB_LAMBDA       = "steeldesign.details.ltb.lambda_lt"              # only for report
KEY_SD_LTB_CHI          = "steeldesign.details.ltb.chi_lt"                 # only for report
KEY_SD_LTB_MB           = "steeldesign.details.ltb.mb"                      # only for report
KEY_SD_STIFF_METHOD     = "steeldesign.details.stiffener_summary.method"        # only for report
KEY_SD_STIFF_INT_THICK  = "steeldesign.details.stiffener_summary.int_thickness"  # only for report
KEY_SD_STIFF_INT_SPACING= "steeldesign.details.stiffener_summary.int_spacing"    # only for report
KEY_SD_STIFF_END_THICK  = "steeldesign.details.stiffener_summary.end_thickness"  # only for report
KEY_SD_STIFF_END_COUNT  = "steeldesign.details.stiffener_summary.end_count"      # only for report
KEY_SD_STIFF_LONG       = "steeldesign.details.stiffener_summary.longitudinal"   # only for report
KEY_SD_IS_IYS_MIN       = "steeldesign.details.int_stiffener.iys_min"      # only for report
KEY_SD_IS_IYS_PROV      = "steeldesign.details.int_stiffener.iys_prov"     # only for report
KEY_SD_IS_FQ            = "steeldesign.details.int_stiffener.fq"           # only for report
KEY_SD_IS_FQD           = "steeldesign.details.int_stiffener.fqd"          # only for report
KEY_SD_BS_R             = "steeldesign.details.bearing_stiffener.reaction"     # only for report
KEY_SD_BS_FCDW_WB       = "steeldesign.details.bearing_stiffener.fcdw_wb"      # only for report
KEY_SD_BS_FCDW_LC       = "steeldesign.details.bearing_stiffener.fcdw_lc"      # only for report
KEY_SD_BS_FPSD          = "steeldesign.details.bearing_stiffener.fpsd"         # only for report
KEY_SD_BS_FCD           = "steeldesign.details.bearing_stiffener.fcd"          # only for report
KEY_SD_CLASS_FLANGE       = "steeldesign.details.classification.flange_class"        # only for report
KEY_SD_CLASS_WEB          = "steeldesign.details.classification.web_class"           # only for report
KEY_SD_DEFL_LIVE        = "steeldesign.deflection.live_mm"       # only for report
KEY_SD_DEFL_TOTAL       = "steeldesign.deflection.total_mm"      # only for report
KEY_SD_DEFL_ALLOW_LIVE  = "steeldesign.deflection.allow_live_mm" # only for report
KEY_SD_DEFL_ALLOW_TOTAL = "steeldesign.deflection.allow_total_mm"# only for report

#-------------- Stiffener Details Sub-Tab --------------------------------------------
KEY_SD_STIFFENER_DETAILS            = "member_properties.stiffener_details.stiffener_details_cad"
KEY_MP_SD_TAB                          = "member_properties.stiffener_details"
KEY_MP_STIFFENER_SELECT_MEMBER_ID             = "member_properties.stiffener_details.select_member_id"
KEY_MP_STIFFENER_APPLY_ALL                    = "member_properties.stiffener_details.apply_all_btn"
KEY_MP_STIFFENER_NO_BEARING_STIFFENERS        = "member_properties.stiffener_details.no_bearing_stiffeners_each_end"
KEY_MP_STIFFENER_SPACING                      = "member_properties.stiffener_details.bearing_stiffener_spacing"
KEY_MP_STIFFENER_BEARING_THICKNESS            = "member_properties.stiffener_details.bearing_stiffener_plate_thickness"
KEY_MP_STIFFENER_BEARING_OUTSTAND             = "member_properties.stiffener_details.bearing_stiffener_outstand"
KEY_MP_STIFFENER_INTERMEDIATE                 = "member_properties.stiffener_details.intermediate_stiffener"
KEY_MP_STIFFENER_INTERMEDIATE_SPACING         = "member_properties.stiffener_details.intermediate_stiffener_spacing"
KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS       = "member_properties.stiffener_details.intermediate_stiffener_thickness"
KEY_MP_STIFFENER_INTERMEDIATE_OUTSTAND        = "member_properties.stiffener_details.intermediate_stiffener_outstand"
KEY_MP_STIFFENER_LONGITUDINAL                 = "member_properties.stiffener_details.longitudinal_stiffener"
KEY_MP_STIFFENER_LONGITUDINAL_THICKNESS       = "member_properties.stiffener_details.longitudinal_stiffener_thickness"
KEY_MP_STIFFENER_DESIGN_METHOD                = "member_properties.stiffener_details.design_method"

#-------------- End Diaphragm Sub-Tab --------------------------------------------
KEY_MP_ED_TAB                          = "member_properties.end_diaphragm_details"

KEY_MP_ED_BRACING_LAYOUT_SECTION   = "member_properties.end_diaphragm_details.bracing_layout_section"
KEY_MP_ED_BRACING_PREVIEW_SECTION  = "member_properties.end_diaphragm_details.bracing_preview_section"
KEY_MP_ED_TOP_CHORD_PREVIEW_SECTION    = "member_properties.end_diaphragm_details.top_chord_preview_section"
KEY_MP_ED_BOTTOM_CHORD_PREVIEW_SECTION = "member_properties.end_diaphragm_details.bottom_chord_preview_section"
KEY_MP_ED_ROLLED_PREVIEW_SECTION   = "member_properties.end_diaphragm_details.rolled_preview_section"
KEY_MP_ED_WELDED_PREVIEW_SECTION   = "member_properties.end_diaphragm_details.welded_preview_section"
KEY_MP_ED_SECTION_PROPERTIES_SECTION = "member_properties.end_diaphragm_details.section_properties_section"

KEY_MP_ED_BRACING_CONNECTION             = "member_properties.end_diaphragm_details.bracing_connection"
KEY_MP_ED_BRACING_CONNECTION_ROW         = "member_properties.end_diaphragm_details.bracing_connection_row"

KEY_MP_ED_BRACING_TYPE_ROW                = "member_properties.end_diaphragm_details.bracing_type_row"
KEY_MP_ED_BRACING_SECTION_ROW             = "member_properties.end_diaphragm_details.bracing_section_row"
KEY_MP_ED_BRACING_SECTION_DESIGNATION_ROW = "member_properties.end_diaphragm_details.bracing_section_designation_row"
KEY_MP_ED_TOP_CHORD_ROW                   = "member_properties.end_diaphragm_details.top_chord_row"
KEY_MP_ED_TOP_CHORD_SECTION_TYPE_ROW      = "member_properties.end_diaphragm_details.top_chord_section_type_row"
KEY_MP_ED_TOP_CHORD_SECTION_DESIG_ROW     = "member_properties.end_diaphragm_details.top_chord_section_desig_row"
KEY_MP_ED_BOTTOM_CHORD_ROW                = "member_properties.end_diaphragm_details.bottom_chord_row"
KEY_MP_ED_BOTTOM_CHORD_SECTION_TYPE_ROW   = "member_properties.end_diaphragm_details.bottom_chord_section_type_row"
KEY_MP_ED_BOTTOM_CHORD_SECTION_DESIG_ROW  = "member_properties.end_diaphragm_details.bottom_chord_section_desig_row"
KEY_MP_ED_IS_SECTION_ROW                  = "member_properties.end_diaphragm_details.is_section_row"
KEY_MP_ED_SYMMETRY_ROW                    = "member_properties.end_diaphragm_details.symmetry_row"
KEY_MP_ED_TOTAL_DEPTH_ROW                 = "member_properties.end_diaphragm_details.total_depth_row"
KEY_MP_ED_WEB_THICKNESS_ROW               = "member_properties.end_diaphragm_details.web_thickness_row"
KEY_MP_ED_TOP_FLANGE_WIDTH_ROW            = "member_properties.end_diaphragm_details.top_flange_width_row"
KEY_MP_ED_TOP_FLANGE_THICKNESS_ROW        = "member_properties.end_diaphragm_details.top_flange_thickness_row"
KEY_MP_ED_BOTTOM_FLANGE_WIDTH_ROW         = "member_properties.end_diaphragm_details.bottom_flange_width_row"
KEY_MP_ED_BOTTOM_FLANGE_THICKNESS_ROW     = "member_properties.end_diaphragm_details.bottom_flange_thickness_row"

KEY_MP_ED_SELECT_GIRDERS              = "member_properties.end_diaphragm_details.select_girders"
KEY_MP_ED_MEMBER_ID                   = "member_properties.end_diaphragm_details.member_id"
KEY_MP_ED_TYPE                        = "member_properties.end_diaphragm_details.type"
KEY_MP_ED_BRACING_TYPE                = "member_properties.end_diaphragm_details.bracing_type"
KEY_MP_ED_BRACING_SECTION             = "member_properties.end_diaphragm_details.bracing_section"
KEY_MP_ED_BRACING_SECTION_DESIGNATION = "member_properties.end_diaphragm_details.bracing_section_designation"
KEY_MP_ED_TOP_CHORD                   = "member_properties.end_diaphragm_details.top_chord"
KEY_MP_ED_TOP_CHORD_SECTION_TYPE      = "member_properties.end_diaphragm_details.top_chord_section_type"
KEY_MP_ED_TOP_CHORD_SECTION_DESIG     = "member_properties.end_diaphragm_details.top_chord_section_designation"
KEY_MP_ED_BOTTOM_CHORD                = "member_properties.end_diaphragm_details.bottom_chord"
KEY_MP_ED_BOTTOM_CHORD_SECTION_TYPE   = "member_properties.end_diaphragm_details.bottom_chord_section_type"
KEY_MP_ED_BOTTOM_CHORD_SECTION_DESIG  = "member_properties.end_diaphragm_details.bottom_chord_section_designation"
KEY_MP_ED_SYMMETRY                    = "member_properties.end_diaphragm_details.symmetry"
KEY_MP_ED_TOTAL_DEPTH                   = "member_properties.end_diaphragm_details.total_depth"
KEY_MP_ED_WEB_THICKNESS              = "member_properties.end_diaphragm_details.web_thickness"
KEY_MP_ED_TOP_FLANGE_WIDTH              = "member_properties.end_diaphragm_details.top_flange_width"
KEY_MP_ED_BOTTOM_FLANGE_WIDTH           = "member_properties.end_diaphragm_details.bottom_flange_width"
KEY_MP_ED_TOP_FLANGE_THICKNESS          = "member_properties.end_diaphragm_details.top_flange_thickness"
KEY_MP_ED_BOTTOM_FLANGE_THICKNESS       = "member_properties.end_diaphragm_details.bottom_flange_thickness"
KEY_MP_ED_IS_SECTION                   = "member_properties.end_diaphragm_details.is_section"
KEY_MP_ED_MASS                       = "member_properties.end_diaphragm_details.section_properties.mass"
KEY_MP_ED_SECTIONAL_AREA             = "member_properties.end_diaphragm_details.section_properties.area"
KEY_MP_ED_SECTIONAL_IY             = "member_properties.end_diaphragm_details.section_properties.iy"
KEY_MP_ED_SECTIONAL_IZ             = "member_properties.end_diaphragm_details.section_properties.iz"
KEY_MP_ED_RADIUS_GYRATION_Y       = "member_properties.end_diaphragm_details.section_properties.radius_gyration_y"
KEY_MP_ED_RADIUS_GYRATION_Z       = "member_properties.end_diaphragm_details.section_properties.radius_gyration_z"
KEY_MP_ED_ELASTIC_MODULUS_ZZ     = "member_properties.end_diaphragm_details.material_properties.elastic_modulus_zz"
KEY_MP_ED_ELASTIC_MODULUS_ZY     = "member_properties.end_diaphragm_details.material_properties.elastic_modulus_zy"
KEY_MP_ED_PLASTIC_MODULUS_ZUZ    = "member_properties.end_diaphragm_details.material_properties.plastic_modulus_zuz"
KEY_MP_ED_PLASTIC_MODULUS_ZUY    = "member_properties.end_diaphragm_details.material_properties.plastic_modulus_zuy"
KEY_MP_ED_BRACING_LAYOUT_CAD     = "member_properties.end_diaphragm_details.bracing_layout_cad"
KEY_MP_ED_BRACING_SECTION_PREVIEW = "member_properties.end_diaphragm_details.bracing_section_preview"
KEY_MP_ED_TOP_CHORD_PREVIEW       = "member_properties.end_diaphragm_details.top_chord_preview"
KEY_MP_ED_BOTTOM_CHORD_PREVIEW    = "member_properties.end_diaphragm_details.bottom_chord_preview"
KEY_MP_ED_ROLLED_PREVIEW          = "member_properties.end_diaphragm_details.rolled_preview"
KEY_MP_ED_WELDED_PREVIEW          = "member_properties.end_diaphragm_details.welded_preview"

#-------------- Cross Bracing Sub-Tab --------------------------------------------
KEY_MP_CB_TAB                         = "member_properties.cross_bracing_details"
KEY_MP_CB_SELECT_GIRDERS              = "member_properties.cross_bracing_details.select_girders"
KEY_MP_CB_NO_OF_CROSS_BRACINGS        = "member_properties.cross_bracing_details.no_of_cross_bracings"
KEY_MP_CB_MEMBER_ID                   = "member_properties.cross_bracing_details.member_id"
KEY_MP_CB_TYPE                        = "member_properties.cross_bracing_details.type"
KEY_MP_CB_BRACING_CONNECTION          = "member_properties.cross_bracing_details.bracing_connection"
KEY_MP_CB_BRACING_SECTION_TYPE        = "member_properties.cross_bracing_details.bracing_section_type"
KEY_MP_CB_BRACING_SECTION_DESIGNATION = "member_properties.cross_bracing_details.bracing_section_designation"
KEY_MP_CB_BRACING_PREVIEW              = "member_properties.cross_bracing_details.bracing_preview"
KEY_MP_CB_TOP_CHORD                    = "member_properties.cross_bracing_details.top_chord"
KEY_MP_CB_TOP_CHORD_SECTION_TYPE       = "member_properties.cross_bracing_details.top_chord_section_type"
KEY_MP_CB_TOP_CHORD_SECTION_DESIG      = "member_properties.cross_bracing_details.top_chord_section_designation"
KEY_MP_CB_TOP_CHORD_PREVIEW            = "member_properties.cross_bracing_details.top_chord_preview"
KEY_MP_CB_TOP_CHORD_PREVIEW_SECTION    = "member_properties.cross_bracing_details.top_chord_preview_section"
KEY_MP_CB_BOTTOM_CHORD                 = "member_properties.cross_bracing_details.bottom_chord"
KEY_MP_CB_BOTTOM_CHORD_SECTION_TYPE    = "member_properties.cross_bracing_details.bottom_chord_section_type"
KEY_MP_CB_BOTTOM_CHORD_SECTION_DESIG   = "member_properties.cross_bracing_details.bottom_chord_section_designation"
KEY_MP_CB_BOTTOM_CHORD_PREVIEW         = "member_properties.cross_bracing_details.bottom_chord_preview"
KEY_MP_CB_BOTTOM_CHORD_PREVIEW_SECTION = "member_properties.cross_bracing_details.bottom_chord_preview_section"
KEY_MP_CB_SPACING                      = "member_properties.cross_bracing_details.spacing"

#══════════════MEMBER-PROPERTIES-TAB-KEY-ENDS═══════════════════════════════════════════════════════

#══════════════LOAD-TAB-KEY-START═════════════════════════════════════════════════════════════════

KEY_LOADING_TAB = "loading.tab"

#-------------- Permanent Load Sub-Tab --------------------------------------------
KEY_PL_TAB                  = "loading.permanent_load.tab"
KEY_PL_SELF_WEIGHT_FACTOR   = "loading.permanent_load.dead_load.self_weight_factor"

#--------------- Live Load Sub-Tab -------------------------------------------------
KEY_LL_TAB                      = "loading.live_load.tab"

# IRC Vehicles
KEY_LL_IRC_CLASS_A              = "loading.live_load.irc.class_a"
KEY_LL_IRC_70R_WHEELED          = "loading.live_load.irc.70r_wheeled"
KEY_LL_IRC_70R_TRACKED          = "loading.live_load.irc.70r_tracked"
KEY_LL_IRC_AA_WHEELED           = "loading.live_load.irc.aa_wheeled"
KEY_LL_IRC_AA_TRACKED           = "loading.live_load.irc.aa_tracked"
KEY_LL_IRC_CLASS_SV             = "loading.live_load.irc.class_sv"
KEY_LL_IRC_70R_BOGIE            = "loading.live_load.irc.70r_bogie"
KEY_LL_IRC_CLASS_FATIGUE        = "loading.live_load.irc.class_fatigue"

# Breaking Load keys — mirror the vehicle class keys
KEY_BL_IRC_CLASS_A        = "bl_irc_class_a"
KEY_BL_IRC_AA_WHEELED     = "bl_irc_aa_wheeled"
KEY_BL_IRC_AA_TRACKED     = "bl_irc_aa_tracked"
KEY_BL_IRC_70R_WHEELED    = "bl_irc_70r_wheeled"
KEY_BL_IRC_70R_TRACKED    = "bl_irc_70r_tracked"
KEY_BL_IRC_70R_BOGIE      = "bl_irc_70r_bogie"
KEY_BL_IRC_CLASS_SV       = "bl_irc_class_sv"
KEY_BL_IRC_CLASS_FATIGUE  = "bl_irc_class_fatigue"
KEY_BL_ECCENTRICITY       = "bl_eccentricity"

# Custom Vehicle
KEY_LL_CUSTOM_VEHICLES = "loading.live_load.custom_vehicles"

# Eccentricity
KEY_LL_ECCENTRICITY             = "loading.live_load.eccentricity"

# Footpath pressure
KEY_LL_FOOTPATH_PRESSURE   = "loading.live_load.footpath_pressure"
KEY_LL_FOOTPATH_PRESSURE_MODE   = "loading.live_load.footpath_pressure.mode"
KEY_LL_FOOTPATH_PRESSURE_VALUE  = "loading.live_load.footpath_pressure.value"

#--------------- Seismic Load Sub-Tab -------------------------------------------------
KEY_SL_TAB                      = "loading.seismic_load.tab"
KEY_SL_SEISMIC_ZONE             = "loading.seismic_load.seismic_zone"
KEY_SL_IMPORTANCE_FACTOR        = "loading.seismic_load.importance_factor"
KEY_SL_SOIL_TYPE                = "loading.seismic_load.soil_type"
KEY_SL_TIME_PERIOD              = "loading.seismic_load.time_period"
KEY_SL_DAMPING                  = "loading.seismic_load.damping"
KEY_SL_RESPONSE_REDUCTION       = "loading.seismic_load.response_reduction_factor"

KEY_SL_DEAD_LOAD                = "loading.seismic_load.dead_load"
KEY_SL_DEAD_LOAD_MODE           = "loading.seismic_load.dead_load.mode"
KEY_SL_DEAD_LOAD_VALUE          = "loading.seismic_load.dead_load.value"

KEY_SL_LIVE_LOAD                = "loading.seismic_load.live_load"
KEY_SL_LIVE_LOAD_MODE           = "loading.seismic_load.live_load.mode"
KEY_SL_LIVE_LOAD_VALUE          = "loading.seismic_load.live_load.value"

KEY_SL_ZONE_FACTOR              = "loading.seismic_load.computed.zone_factor"
KEY_SL_SPECTRAL_COEFF           = "loading.seismic_load.computed.spectral_coeff"
KEY_SL_HORIZONTAL_COEFF         = "loading.seismic_load.computed.horizontal_coeff"
KEY_SL_VERTICAL_COEFF           = "loading.seismic_load.computed.vertical_coeff"

#--------------- Wind Load Sub-Tab -------------------------------------------------
KEY_WL_TAB                      = "loading.wind_load.tab"
KEY_WL_BASIC_WIND_SPEED         = "loading.wind_load.basic_wind_speed"
KEY_WL_AVG_EXPOSED_HEIGHT       = "loading.wind_load.avg_exposed_height"
KEY_WL_TERRAIN_TYPE             = "loading.wind_load.terrain_type"
KEY_WL_SITE_TOPOGRAPHY          = "loading.wind_load.site_topography"

KEY_WL_GUST_FACTOR              = "loading.wind_load.gust_factor"
KEY_WL_GUST_FACTOR_MODE         = "loading.wind_load.gust_factor.mode"
KEY_WL_GUST_FACTOR_VALUE        = "loading.wind_load.gust_factor.value"

KEY_WL_DRAG_COEFF               = "loading.wind_load.drag_coeff"
KEY_WL_DRAG_COEFF_MODE          = "loading.wind_load.drag_coeff.mode"
KEY_WL_DRAG_COEFF_VALUE         = "loading.wind_load.drag_coeff.value"

KEY_WL_DRAG_COEFF_LL            = "loading.wind_load.drag_coeff_ll"
KEY_WL_DRAG_COEFF_LL_MODE       = "loading.wind_load.drag_coeff_ll.mode"
KEY_WL_DRAG_COEFF_LL_VALUE      = "loading.wind_load.drag_coeff_ll.value"

KEY_WL_LIFT_COEFF               = "loading.wind_load.lift_coeff"
KEY_WL_LIFT_COEFF_MODE          = "loading.wind_load.lift_coeff.mode"
KEY_WL_LIFT_COEFF_VALUE         = "loading.wind_load.lift_coeff.value"

KEY_WL_SUPER_AREA_ELEV          = "loading.wind_load.super_area_elev"
KEY_WL_SUPER_AREA_ELEV_MODE     = "loading.wind_load.super_area_elev.mode"
KEY_WL_SUPER_AREA_ELEV_VALUE    = "loading.wind_load.super_area_elev.value"

KEY_WL_SUPER_AREA_PLAIN         = "loading.wind_load.super_area_plain"
KEY_WL_SUPER_AREA_PLAIN_MODE    = "loading.wind_load.super_area_plain.mode"
KEY_WL_SUPER_AREA_PLAIN_VALUE   = "loading.wind_load.super_area_plain.value"

KEY_WL_EXPOSED_FRONTAL          = "loading.wind_load.exposed_frontal_area"
KEY_WL_EXPOSED_FRONTAL_MODE     = "loading.wind_load.exposed_frontal_area.mode"
KEY_WL_EXPOSED_FRONTAL_VALUE    = "loading.wind_load.exposed_frontal_area.value"

KEY_WL_WIND_ECC_DECK            = "loading.wind_load.wind_ecc_deck"
KEY_WL_WIND_ECC_DECK_MODE       = "loading.wind_load.wind_ecc_deck.mode"
KEY_WL_WIND_ECC_DECK_VALUE      = "loading.wind_load.wind_ecc_deck.value"

KEY_WL_WIND_LL_ECC              = "loading.wind_load.wind_ll_ecc"
KEY_WL_WIND_LL_ECC_MODE         = "loading.wind_load.wind_ll_ecc.mode"
KEY_WL_WIND_LL_ECC_VALUE        = "loading.wind_load.wind_ll_ecc.value"

KEY_WL_HOURLY_MEAN_WIND         = "loading.wind_load.computed.hourly_mean_wind"
KEY_WL_HOURLY_WIND_PRESSURE     = "loading.wind_load.computed.hourly_wind_pressure"
KEY_WL_TRANSVERSE_WIND_FORCE    = "loading.wind_load.computed.transverse_wind_force"
KEY_WL_LONGITUDINAL_WIND_FORCE  = "loading.wind_load.computed.longitudinal_wind_force"
KEY_WL_VERTICAL_WIND_FORCE      = "loading.wind_load.computed.vertical_wind_force"
KEY_WL_TRANSVERSE_WIND_LL       = "loading.wind_load.computed.transverse_wind_ll"
KEY_WL_LONGITUDINAL_WIND_LL     = "loading.wind_load.computed.longitudinal_wind_ll"

#--------------- Temperature Load Sub-Tab -------------------------------------------------
KEY_TL_TAB                      = "loading.temperature_load.tab"
KEY_TL_HIGHEST_MAX_TEMP         = "loading.temperature_load.highest_max_temp"
KEY_TL_LOWEST_MIN_TEMP          = "loading.temperature_load.lowest_min_temp"
KEY_TL_THERMAL_COEFF_STEEL      = "loading.temperature_load.thermal_coeff_steel"
KEY_TL_THERMAL_COEFF_RCC        = "loading.temperature_load.thermal_coeff_rcc"
KEY_TL_BRIDGE_TEMP_MIN          = "loading.temperature_load.computed.bridge_temp_min"
KEY_TL_BRIDGE_TEMP_MAX          = "loading.temperature_load.computed.bridge_temp_max"
KEY_TL_TEMP_RISE                = "loading.temperature_load.computed.temp_rise"
KEY_TL_TEMP_FALL                = "loading.temperature_load.computed.temp_fall"

#--------------- Load Combination Sub-Tab -------------------------------------------------

KEY_LC_COMBINATIONS   = "loading.load_combination.combinations"
KEY_LC_TAB            = "loading.load_combination.tab"

# ── ULS Load Combination Case Keys ─────────────────────────────────────────

# Basic — adding (DL=1.35, DW=1.75)
KEY_BASIC_LL_ADD_CASE   = "loading.load_combination.basic.ll_leading.adding"
KEY_BASIC_WL_ADD_CASE   = "loading.load_combination.basic.wl_leading.adding"
KEY_BASIC_TL_ADD_CASE   = "loading.load_combination.basic.tl_leading.adding"

# Basic — relieving (DL=1.0, DW=1.0)
KEY_BASIC_LL_REL_CASE   = "loading.load_combination.basic.ll_leading.relieving"
KEY_BASIC_WL_REL_CASE   = "loading.load_combination.basic.wl_leading.relieving"
KEY_BASIC_TL_REL_CASE   = "loading.load_combination.basic.tl_leading.relieving"

# Accidental — adding (DL=1.0 adding)
KEY_ACCIDENTAL_VC_LL_ADD_CASE   = "loading.load_combination.accidental.vc.ll_leading.adding"
KEY_ACCIDENTAL_BI_LL_ADD_CASE   = "loading.load_combination.accidental.bi.ll_leading.adding"
KEY_ACCIDENTAL_FB_LL_ADD_CASE   = "loading.load_combination.accidental.fb.ll_leading.adding"

# Accidental — relieving (DL=1.0 relieving)
KEY_ACCIDENTAL_VC_LL_REL_CASE   = "loading.load_combination.accidental.vc.ll_leading.relieving"
KEY_ACCIDENTAL_BI_LL_REL_CASE   = "loading.load_combination.accidental.bi.ll_leading.relieving"
KEY_ACCIDENTAL_FB_LL_REL_CASE   = "loading.load_combination.accidental.fb.ll_leading.relieving"

# Seismic — adding (DL=1.35)
KEY_SEISMIC_SERVICE_ADD_CASE      = "loading.load_combination.seismic.service.adding"
KEY_SEISMIC_CONSTRUCTION_ADD_CASE = "loading.load_combination.seismic.construction.adding"

# Seismic — relieving (DL=1.0)
KEY_SEISMIC_SERVICE_REL_CASE      = "loading.load_combination.seismic.service.relieving"
KEY_SEISMIC_CONSTRUCTION_REL_CASE = "loading.load_combination.seismic.construction.relieving"


# ── SLS Load Combination Case Keys ─────────────────────────────────────────

# SLS Rare — adding (Surf=1.2)
KEY_SLS_RARE_LL_ADD_CASE    = "loading.load_combination.sls.rare.ll_leading.adding"
KEY_SLS_RARE_WL_ADD_CASE    = "loading.load_combination.sls.rare.wl_leading.adding"
KEY_SLS_RARE_TL_ADD_CASE    = "loading.load_combination.sls.rare.tl_leading.adding"

# SLS Rare — relieving (Surf=1.0)
KEY_SLS_RARE_LL_REL_CASE    = "loading.load_combination.sls.rare.ll_leading.relieving"
KEY_SLS_RARE_WL_REL_CASE    = "loading.load_combination.sls.rare.wl_leading.relieving"
KEY_SLS_RARE_TL_REL_CASE    = "loading.load_combination.sls.rare.tl_leading.relieving"

# SLS Frequent — adding (Surf=1.2)
KEY_SLS_FREQ_LL_ADD_CASE    = "loading.load_combination.sls.frequent.ll_leading.adding"
KEY_SLS_FREQ_WL_ADD_CASE    = "loading.load_combination.sls.frequent.wl_leading.adding"
KEY_SLS_FREQ_TL_ADD_CASE    = "loading.load_combination.sls.frequent.tl_leading.adding"

# SLS Frequent — relieving (Surf=1.0)
KEY_SLS_FREQ_LL_REL_CASE    = "loading.load_combination.sls.frequent.ll_leading.relieving"
KEY_SLS_FREQ_WL_REL_CASE    = "loading.load_combination.sls.frequent.wl_leading.relieving"
KEY_SLS_FREQ_TL_REL_CASE    = "loading.load_combination.sls.frequent.tl_leading.relieving"

# SLS Quasi-permanent — adding (Surf=1.2)
KEY_SLS_QP_ADD_CASE         = "loading.load_combination.sls.quasi_permanent.adding"

# SLS Quasi-permanent — relieving (Surf=1.0)
KEY_SLS_QP_REL_CASE         = "loading.load_combination.sls.quasi_permanent.relieving"

#══════════════LOAD-TAB-KEY-ENDS═════════════════════════════════════════════════════════════════

#══════════════SUPPORT-CONDITIONS-KEY-START══════════════════════════════════════════════════════

KEY_SC_TAB              = "support_conditions.tab"
KEY_SC_LEFT_SUPPORT     = "support_conditions.left_support"
KEY_SC_RIGHT_SUPPORT    = "support_conditions.right_support"
KEY_SC_BEARING_LENGTH   = "support_conditions.bearing_length"
KEY_SC_LEFT_CAD         = "support_conditions.left_cad"
KEY_SC_RIGHT_CAD        = "support_conditions.right_cad"

#══════════════SUPPORT-CONDITIONS-KEY-ENDS══════════════════════════════════════════════════════

#══════════════DESIGN-OPTIONS-TAB-KEY-START═════════════════════════════════════════════════════

KEY_DS_TAB                        = "design_options.tab"

# Construction
KEY_DS_CONSTRUCTION_STAGE         = "design_options.construction.stage"

# Deck Design
KEY_DS_REINF_BOUNDS               = "design_options.deck.reinforcement_bounds"
KEY_DS_REINF_MATERIAL             = "design_options.deck.reinforcement_material"
KEY_DS_TOP_CLEAR_COVER            = "design_options.deck.top_clear_cover"
KEY_DS_BOTTOM_CLEAR_COVER         = "design_options.deck.bottom_clear_cover"
KEY_DS_SIDE_CLEAR_COVER           = "design_options.deck.side_clear_cover"

# Shear Studs
KEY_DS_STUD_YIELD_STRENGTH        = "design_options.shear_studs.yield_strength"
KEY_DS_STUD_ULTIMATE_STRENGTH     = "design_options.shear_studs.ultimate_strength"
KEY_DS_STUD_DIAMETER              = "design_options.shear_studs.diameter"
KEY_DS_STUD_HEIGHT                = "design_options.shear_studs.height"
KEY_DS_STUD_COUNT                 = "design_options.shear_studs.count"
KEY_DS_STUD_TRANSVERSE_SPACING    = "design_options.shear_studs.transverse_spacing"
KEY_DS_STUD_HEAD_DIAMETER         = "design_options.shear_studs.head_diameter"
KEY_DS_STUD_HEAD_HEIGHT           = "design_options.shear_studs.head_height"

#══════════════DESIGN-OPTIONS-TAB-KEY-ENDS═════════════════════════════════════════════════════

#══════════════DESIGN-OPTIONS-CONT-TAB-KEY-START═══════════════════════════════════════════════

KEY_DO_TAB                  = "design_options_cont.tab"

# Partial Factor
KEY_DO_GAMMA_C_BASIC        = "design_options_cont.partial_factor.concrete_basic.gamma_c_basic"
KEY_DO_GAMMA_C_ACCIDENTAL   = "design_options_cont.partial_factor.concrete_accidental.gamma_c_accidental"
KEY_DO_GAMMA_M0             = "design_options_cont.partial_factor.yielding_and_buckling.gamma_m0"
KEY_DO_GAMMA_M1             = "design_options_cont.partial_factor.ultimate_stress.gamma_m1"
KEY_DO_GAMMA_S              = "design_options_cont.partial_factor.reinforcing_steel.gamma_s"
KEY_DO_GAMMA_V              = "design_options_cont.partial_factor.shear_connectors.gamma_v"
KEY_DO_GAMMA_FLT            = "design_options_cont.partial_factor.fatigue_load.gamma_flt"
KEY_DO_GAMMA_MF             = "design_options_cont.partial_factor.fatigue_strength.gamma_mf"

# Fatigue
KEY_DO_LOAD_CYCLES          = "design_options_cont.fatigue.load_cycles"

# Deflection
KEY_DO_DEFLECTION_LIMIT     = "design_options_cont.deflection.limit"

# Ultimate Limit States
KEY_DO_ULS_BENDING          = "design_options_cont.uls.bending_resistance"
KEY_DO_ULS_SHEAR            = "design_options_cont.uls.vertical_shear"
KEY_DO_ULS_LTB              = "design_options_cont.uls.lateral_torsional_buckling"
KEY_DO_ULS_TRANSVERSE       = "design_options_cont.uls.transverse_force"
KEY_DO_ULS_LONG_SHEAR       = "design_options_cont.uls.longitudinal_shear"
KEY_DO_ULS_FATIGUE          = "design_options_cont.uls.fatigue"

# Serviceability Limit States
KEY_DO_SLS_STRESS           = "design_options_cont.sls.stress_limitation"
KEY_DO_SLS_LONG_SHEAR       = "design_options_cont.sls.longitudinal_shear"
KEY_DO_SLS_DEFLECTION       = "design_options_cont.sls.deflection_control"
KEY_DO_SLS_CRACK_WIDTH      = "design_options_cont.sls.crack_width"

#══════════════DESIGN-OPTIONS-CONT-TAB-KEY-ENDS════════════════════════════════════════════════

KEY_METALLIC_CRASH_BARRIER_TYPE = ["Single W-beam", "Double W-beam"]
KEY_RIGID_CRASH_BARRIER_TYPE = ["IRC-5R", "High Containment"]
KEY_CRASH_BARRIER_TYPE = ["Flexible", "Semi-Rigid", "Rigid"]
KEY_MEDIAN_TYPE = ["Raised Kerb", "RCC Crash Barrier", "Metallic Crash Barrier"]
KEY_FOOTPATH_CLEAR_MIN_WIDTH = 1500


# Member Properties - Girder Details - just created for now so it doesnt affects other imports

KEY_MP_GIRDER_WEB_DEPTH = "member_properties.girder_details.section_input.web_depth"




# Loading - Permanent Load
KEY_SELF_WEIGHT = "Self Weight"
KEY_SELF_WEIGHT_FACTOR = "Self Weight Factor"
KEY_WEARING_COAT = ["bituminous", "concrete"]
KEY_RAILING_TYPE = ["IRC 5 RCC railing", "IRC 5 steel railing"]
KEY_RAILING_LOAD_COUNT = "No. of Railings"
KEY_RAILING_LOAD = "Railing Load"
KEY_RAILING_LOAD_LOCATION = "Railing Load Location"
KEY_CRASH_BARRIER_LOAD_COUNT = "No. of Crash Barriers"
KEY_CRASH_BARRIER_LOAD = "Crash Barrier Load"
KEY_CRASH_BARRIER_LOAD_LOCATION = "Crash Barrier Load Location"

# Loading - Live Load
KEY_IRC_CLASS_A = "IRC Class A"
KEY_IRC_CLASS_70R = "IRC Class 70R"
KEY_IRC_CLASS_AA = "IRC Class AA"
KEY_IRC_CLASS_SV = "IRC Class SV"
KEY_CUSTOM_VEHICLE = "Custom Vehicle"
KEY_CUSTOM_AXLE_TYPE = "Custom Axle Type"
KEY_CUSTOM_NO_AXLES = "Custom Number of Axles"
KEY_CUSTOM_AXLE_LOAD = "Custom Axle Load"
KEY_CUSTOM_AXLE_SPACING = "Custom Axle Spacing"
KEY_CUSTOM_VEHICLE_SPACING = "Custom Vehicle Spacing"
KEY_CUSTOM_ECCENTRICITY = "Custom Eccentricity"
KEY_FOOTPATH_PRESSURE = "Footpath Pressure"
KEY_FOOTPATH_PRESSURE_VALUE = "Footpath Pressure Value"

# Support Condition Keys
KEY_LEFT_SUPPORT = "Left Support"
KEY_RIGHT_SUPPORT = "Right Support"
KEY_BEARING_LENGTH = "Bearing Length"

# Transverse Member Design - General Keys
KEY_TD_DIALOG = "transverse_member_design"
KEY_TD_MEMBER_ID = "transverse_member_design.member_id"
KEY_TD_SELECT_GIRDER = "transverse_member_design.select_girder"
KEY_TD_LOAD_COMBINATION = "transverse_member_design.load_combination"
KEY_TD_CB_TAB = "transverse_member_design.cb.tab"
KEY_TD_ED_TAB = "transverse_member_design.ed.tab"

# Transverse Member Design - Cross Bracing Design Keys
KEY_TD_CB_SECTION_INPUTS_DESIGN = "transverse_member_design.cb.section_inputs.design"
KEY_TD_CB_SECTION_INPUTS_NO_OF_CB = "transverse_member_design.cb.section_inputs.no_of_cb"
KEY_TD_CB_SECTION_INPUTS_BRACING_TYPE = "transverse_member_design.cb.section_inputs.bracing_type"
KEY_TD_CB_SECTION_INPUTS_CONNECTION_TYPE = "transverse_member_design.cb.section_inputs.connection_type"
KEY_TD_CB_SECTION_INPUTS_BRACING_SECTION_TYPE = "transverse_member_design.cb.section_inputs.bracing_section_type"
KEY_TD_CB_SECTION_INPUTS_BRACING_SECTION_DESIGNATION = "transverse_member_design.cb.section_inputs.bracing_section_designation"
KEY_TD_CB_SECTION_INPUTS_TOP_CHORD_ENABLED = "transverse_member_design.cb.section_inputs.top_chord_enabled"
KEY_TD_CB_SECTION_INPUTS_TOP_CHORD_SECTION_TYPE = "transverse_member_design.cb.section_inputs.top_chord_section_type"
KEY_TD_CB_SECTION_INPUTS_TOP_CHORD_SECTION_DESIGNATION = "transverse_member_design.cb.section_inputs.top_chord_section_designation"
KEY_TD_CB_SECTION_INPUTS_BOTTOM_CHORD_ENABLED = "transverse_member_design.cb.section_inputs.bottom_chord_enabled"
KEY_TD_CB_SECTION_INPUTS_BOTTOM_CHORD_SECTION_TYPE = "transverse_member_design.cb.section_inputs.bottom_chord_section_type"
KEY_TD_CB_SECTION_INPUTS_BOTTOM_CHORD_SECTION_DESIGNATION = "transverse_member_design.cb.section_inputs.bottom_chord_section_designation"
KEY_TD_CB_SECTION_INPUTS_SPACING = "transverse_member_design.cb.section_inputs.spacing"
KEY_TD_CB_BRACING_DIAGRAM = "transverse_member_design.cb.bracing_diagram"
KEY_TD_CB_SECTION_PROPS_BRACING = "transverse_member_design.cb.section_properties.bracing"
KEY_TD_CB_SECTION_PROPS_TOP_CHORD = "transverse_member_design.cb.section_properties.top_chord"
KEY_TD_CB_SECTION_PROPS_BOTTOM_CHORD = "transverse_member_design.cb.section_properties.bottom_chord"
KEY_TD_CB_DESIGN_CHECK_FORCES_TABLE = "transverse_member_design.cb.design_check.forces_table"
KEY_TD_CB_DESIGN_CHECK_RESULTS = "transverse_member_design.cb.design_check.results"
KEY_TD_CB_DETAILS_TAB = "transverse_member_design.cb.details"
KEY_TD_CB_DESIGN_CHECK_TAB = "transverse_member_design.cb.design_check"

# Transverse Member Design - Cross Bracing Section Properties Keys
KEY_TD_CB_PROP_L = "transverse_member_design.cb.section_properties.bracing.L"
KEY_TD_CB_PROP_H = "transverse_member_design.cb.section_properties.bracing.H"
KEY_TD_CB_PROP_B = "transverse_member_design.cb.section_properties.bracing.B"
KEY_TD_CB_PROP_TW = "transverse_member_design.cb.section_properties.bracing.tw"
KEY_TD_CB_PROP_TF = "transverse_member_design.cb.section_properties.bracing.tF"
KEY_TD_CB_PROP_RZ = "transverse_member_design.cb.section_properties.bracing.rz"
KEY_TD_CB_PROP_M = "transverse_member_design.cb.section_properties.bracing.M"
KEY_TD_CB_PROP_A = "transverse_member_design.cb.section_properties.bracing.A"
KEY_TD_CB_PROP_IZ = "transverse_member_design.cb.section_properties.bracing.Iz"
KEY_TD_CB_PROP_IV = "transverse_member_design.cb.section_properties.bracing.Iv"
KEY_TD_CB_PROP_RV = "transverse_member_design.cb.section_properties.bracing.rv"
KEY_TD_CB_PROP_ZZ = "transverse_member_design.cb.section_properties.bracing.Zz"
KEY_TD_CB_PROP_ZV = "transverse_member_design.cb.section_properties.bracing.Zv"
KEY_TD_CB_PROP_ZUZ = "transverse_member_design.cb.section_properties.bracing.Zuz"
KEY_TD_CB_PROP_ZUV = "transverse_member_design.cb.section_properties.bracing.Zuv"

KEY_TD_CB_TOP_CHORD_PROP_L = "transverse_member_design.cb.section_properties.top_chord.L"
KEY_TD_CB_TOP_CHORD_PROP_H = "transverse_member_design.cb.section_properties.top_chord.H"
KEY_TD_CB_TOP_CHORD_PROP_B = "transverse_member_design.cb.section_properties.top_chord.B"
KEY_TD_CB_TOP_CHORD_PROP_TW = "transverse_member_design.cb.section_properties.top_chord.tw"
KEY_TD_CB_TOP_CHORD_PROP_TF = "transverse_member_design.cb.section_properties.top_chord.tF"
KEY_TD_CB_TOP_CHORD_PROP_RZ = "transverse_member_design.cb.section_properties.top_chord.rz"
KEY_TD_CB_TOP_CHORD_PROP_M = "transverse_member_design.cb.section_properties.top_chord.M"
KEY_TD_CB_TOP_CHORD_PROP_A = "transverse_member_design.cb.section_properties.top_chord.A"
KEY_TD_CB_TOP_CHORD_PROP_IZ = "transverse_member_design.cb.section_properties.top_chord.Iz"
KEY_TD_CB_TOP_CHORD_PROP_IV = "transverse_member_design.cb.section_properties.top_chord.Iv"
KEY_TD_CB_TOP_CHORD_PROP_RV = "transverse_member_design.cb.section_properties.top_chord.rv"
KEY_TD_CB_TOP_CHORD_PROP_ZZ = "transverse_member_design.cb.section_properties.top_chord.Zz"
KEY_TD_CB_TOP_CHORD_PROP_ZV = "transverse_member_design.cb.section_properties.top_chord.Zv"
KEY_TD_CB_TOP_CHORD_PROP_ZUZ = "transverse_member_design.cb.section_properties.top_chord.Zuz"
KEY_TD_CB_TOP_CHORD_PROP_ZUV = "transverse_member_design.cb.section_properties.top_chord.Zuv"

KEY_TD_CB_BOTTOM_CHORD_PROP_L = "transverse_member_design.cb.section_properties.bottom_chord.L"
KEY_TD_CB_BOTTOM_CHORD_PROP_H = "transverse_member_design.cb.section_properties.bottom_chord.H"
KEY_TD_CB_BOTTOM_CHORD_PROP_B = "transverse_member_design.cb.section_properties.bottom_chord.B"
KEY_TD_CB_BOTTOM_CHORD_PROP_TW = "transverse_member_design.cb.section_properties.bottom_chord.tw"
KEY_TD_CB_BOTTOM_CHORD_PROP_TF = "transverse_member_design.cb.section_properties.bottom_chord.tF"
KEY_TD_CB_BOTTOM_CHORD_PROP_RZ = "transverse_member_design.cb.section_properties.bottom_chord.rz"
KEY_TD_CB_BOTTOM_CHORD_PROP_M = "transverse_member_design.cb.section_properties.bottom_chord.M"
KEY_TD_CB_BOTTOM_CHORD_PROP_A = "transverse_member_design.cb.section_properties.bottom_chord.A"
KEY_TD_CB_BOTTOM_CHORD_PROP_IZ = "transverse_member_design.cb.section_properties.bottom_chord.Iz"
KEY_TD_CB_BOTTOM_CHORD_PROP_IV = "transverse_member_design.cb.section_properties.bottom_chord.Iv"
KEY_TD_CB_BOTTOM_CHORD_PROP_RV = "transverse_member_design.cb.section_properties.bottom_chord.rv"
KEY_TD_CB_BOTTOM_CHORD_PROP_ZZ = "transverse_member_design.cb.section_properties.bottom_chord.Zz"
KEY_TD_CB_BOTTOM_CHORD_PROP_ZV = "transverse_member_design.cb.section_properties.bottom_chord.Zv"
KEY_TD_CB_BOTTOM_CHORD_PROP_ZUZ = "transverse_member_design.cb.section_properties.bottom_chord.Zuz"
KEY_TD_CB_BOTTOM_CHORD_PROP_ZUV = "transverse_member_design.cb.section_properties.bottom_chord.Zuv"

# Transverse Member Design - End Diaphragm Section Inputs Keys
KEY_TD_ED_SECTION_INPUTS_TYPE = "transverse_member_design.ed.section_inputs.type"
KEY_TD_ED_SECTION_INPUTS_DESIGN = "transverse_member_design.ed.section_inputs.design"
KEY_TD_ED_SECTION_INPUTS_NO_OF_CB = "transverse_member_design.ed.section_inputs.no_of_cb"
KEY_TD_ED_SECTION_INPUTS_BRACING_TYPE = "transverse_member_design.ed.section_inputs.bracing_type"
KEY_TD_ED_SECTION_INPUTS_CONNECTION_TYPE = "transverse_member_design.ed.section_inputs.connection_type"
KEY_TD_ED_SECTION_INPUTS_BRACING_SECTION_TYPE = "transverse_member_design.ed.section_inputs.bracing_section_type"
KEY_TD_ED_SECTION_INPUTS_BRACING_SECTION_DESIGNATION = "transverse_member_design.ed.section_inputs.bracing_section_designation"
KEY_TD_ED_SECTION_INPUTS_TOP_CHORD_ENABLED = "transverse_member_design.ed.section_inputs.top_chord_enabled"
KEY_TD_ED_SECTION_INPUTS_TOP_CHORD_SECTION_TYPE = "transverse_member_design.ed.section_inputs.top_chord_section_type"
KEY_TD_ED_SECTION_INPUTS_TOP_CHORD_SECTION_DESIGNATION = "transverse_member_design.ed.section_inputs.top_chord_section_designation"
KEY_TD_ED_SECTION_INPUTS_BOTTOM_CHORD_ENABLED = "transverse_member_design.ed.section_inputs.bottom_chord_enabled"
KEY_TD_ED_SECTION_INPUTS_BOTTOM_CHORD_SECTION_TYPE = "transverse_member_design.ed.section_inputs.bottom_chord_section_type"
KEY_TD_ED_SECTION_INPUTS_BOTTOM_CHORD_SECTION_DESIGNATION = "transverse_member_design.ed.section_inputs.bottom_chord_section_designation"
KEY_TD_ED_SECTION_INPUTS_SPACING = "transverse_member_design.ed.section_inputs.spacing"
KEY_TD_ED_BRACING_DIAGRAM = "transverse_member_design.ed.bracing_diagram"
KEY_TD_ED_SECTION_PROPS_BRACING = "transverse_member_design.ed.section_properties.bracing"
KEY_TD_ED_SECTION_PROPS_TOP_CHORD = "transverse_member_design.ed.section_properties.top_chord"
KEY_TD_ED_SECTION_PROPS_BOTTOM_CHORD = "transverse_member_design.ed.section_properties.bottom_chord"
KEY_TD_ED_DESIGN_CHECK_FORCES_TABLE = "transverse_member_design.ed.design_check.forces_table"
KEY_TD_ED_DESIGN_CHECK_RESULTS = "transverse_member_design.ed.design_check.results"
KEY_TD_ED_DETAILS_TAB = "transverse_member_design.ed.details"
KEY_TD_ED_DESIGN_CHECK_TAB = "transverse_member_design.ed.design_check"

KEY_TD_ED_SECTION_INPUTS_IS_SECTION = "transverse_member_design.ed.section_inputs.is_section"
KEY_TD_ED_SECTION_INPUTS_SYMMETRY = "transverse_member_design.ed.section_inputs.symmetry"
KEY_TD_ED_SECTION_INPUTS_TOTAL_DEPTH = "transverse_member_design.ed.section_inputs.total_depth"
KEY_TD_ED_SECTION_INPUTS_WEB_THICKNESS = "transverse_member_design.ed.section_inputs.web_thickness"
KEY_TD_ED_SECTION_INPUTS_TOP_FLANGE_WIDTH = "transverse_member_design.ed.section_inputs.top_flange_width"
KEY_TD_ED_SECTION_INPUTS_BOTTOM_FLANGE_WIDTH = "transverse_member_design.ed.section_inputs.bottom_flange_width"
KEY_TD_ED_SECTION_INPUTS_TOP_FLANGE_THICKNESS = "transverse_member_design.ed.section_inputs.top_flange_thickness"
KEY_TD_ED_SECTION_INPUTS_BOTTOM_FLANGE_THICKNESS = "transverse_member_design.ed.section_inputs.bottom_flange_thickness"

# Transverse Member Design - End Diaphragm Section Property Keys
KEY_TD_ED_PROP_L = "transverse_member_design.ed.section_properties.end_diaphragm.L"
KEY_TD_ED_PROP_H = "transverse_member_design.ed.section_properties.end_diaphragm.H"
KEY_TD_ED_PROP_B = "transverse_member_design.ed.section_properties.end_diaphragm.B"
KEY_TD_ED_PROP_TW = "transverse_member_design.ed.section_properties.end_diaphragm.tw"
KEY_TD_ED_PROP_TF = "transverse_member_design.ed.section_properties.end_diaphragm.tF"
KEY_TD_ED_PROP_RZ = "transverse_member_design.ed.section_properties.end_diaphragm.rz"
KEY_TD_ED_PROP_M = "transverse_member_design.ed.section_properties.end_diaphragm.M"
KEY_TD_ED_PROP_A = "transverse_member_design.ed.section_properties.end_diaphragm.A"
KEY_TD_ED_PROP_IZ = "transverse_member_design.ed.section_properties.end_diaphragm.Iz"
KEY_TD_ED_PROP_IV = "transverse_member_design.ed.section_properties.end_diaphragm.Iv"
KEY_TD_ED_PROP_RV = "transverse_member_design.ed.section_properties.end_diaphragm.rv"
KEY_TD_ED_PROP_ZZ = "transverse_member_design.ed.section_properties.end_diaphragm.Zz"
KEY_TD_ED_PROP_ZV = "transverse_member_design.ed.section_properties.end_diaphragm.Zv"
KEY_TD_ED_PROP_ZUZ = "transverse_member_design.ed.section_properties.end_diaphragm.Zuz"
KEY_TD_ED_PROP_ZUV = "transverse_member_design.ed.section_properties.end_diaphragm.Zuv"

KEY_TD_ED_TOP_CHORD_PROP_L = "transverse_member_design.ed.section_properties.top_chord.L"
KEY_TD_ED_TOP_CHORD_PROP_H = "transverse_member_design.ed.section_properties.top_chord.H"
KEY_TD_ED_TOP_CHORD_PROP_B = "transverse_member_design.ed.section_properties.top_chord.B"
KEY_TD_ED_TOP_CHORD_PROP_TW = "transverse_member_design.ed.section_properties.top_chord.tw"
KEY_TD_ED_TOP_CHORD_PROP_TF = "transverse_member_design.ed.section_properties.top_chord.tF"
KEY_TD_ED_TOP_CHORD_PROP_RZ = "transverse_member_design.ed.section_properties.top_chord.rz"
KEY_TD_ED_TOP_CHORD_PROP_M = "transverse_member_design.ed.section_properties.top_chord.M"
KEY_TD_ED_TOP_CHORD_PROP_A = "transverse_member_design.ed.section_properties.top_chord.A"
KEY_TD_ED_TOP_CHORD_PROP_IZ = "transverse_member_design.ed.section_properties.top_chord.Iz"
KEY_TD_ED_TOP_CHORD_PROP_IV = "transverse_member_design.ed.section_properties.top_chord.Iv"
KEY_TD_ED_TOP_CHORD_PROP_RV = "transverse_member_design.ed.section_properties.top_chord.rv"
KEY_TD_ED_TOP_CHORD_PROP_ZZ = "transverse_member_design.ed.section_properties.top_chord.Zz"
KEY_TD_ED_TOP_CHORD_PROP_ZV = "transverse_member_design.ed.section_properties.top_chord.Zv"
KEY_TD_ED_TOP_CHORD_PROP_ZUZ = "transverse_member_design.ed.section_properties.top_chord.Zuz"
KEY_TD_ED_TOP_CHORD_PROP_ZUV = "transverse_member_design.ed.section_properties.top_chord.Zuv"

KEY_TD_ED_BOTTOM_CHORD_PROP_L = "transverse_member_design.ed.section_properties.bottom_chord.L"
KEY_TD_ED_BOTTOM_CHORD_PROP_H = "transverse_member_design.ed.section_properties.bottom_chord.H"
KEY_TD_ED_BOTTOM_CHORD_PROP_B = "transverse_member_design.ed.section_properties.bottom_chord.B"
KEY_TD_ED_BOTTOM_CHORD_PROP_TW = "transverse_member_design.ed.section_properties.bottom_chord.tw"
KEY_TD_ED_BOTTOM_CHORD_PROP_TF = "transverse_member_design.ed.section_properties.bottom_chord.tF"
KEY_TD_ED_BOTTOM_CHORD_PROP_RZ = "transverse_member_design.ed.section_properties.bottom_chord.rz"
KEY_TD_ED_BOTTOM_CHORD_PROP_M = "transverse_member_design.ed.section_properties.bottom_chord.M"
KEY_TD_ED_BOTTOM_CHORD_PROP_A = "transverse_member_design.ed.section_properties.bottom_chord.A"
KEY_TD_ED_BOTTOM_CHORD_PROP_IZ = "transverse_member_design.ed.section_properties.bottom_chord.Iz"
KEY_TD_ED_BOTTOM_CHORD_PROP_IV = "transverse_member_design.ed.section_properties.bottom_chord.Iv"
KEY_TD_ED_BOTTOM_CHORD_PROP_RV = "transverse_member_design.ed.section_properties.bottom_chord.rv"
KEY_TD_ED_BOTTOM_CHORD_PROP_ZZ = "transverse_member_design.ed.section_properties.bottom_chord.Zz"
KEY_TD_ED_BOTTOM_CHORD_PROP_ZV = "transverse_member_design.ed.section_properties.bottom_chord.Zv"
KEY_TD_ED_BOTTOM_CHORD_PROP_ZUZ = "transverse_member_design.ed.section_properties.bottom_chord.Zuz"
KEY_TD_ED_BOTTOM_CHORD_PROP_ZUV = "transverse_member_design.ed.section_properties.bottom_chord.Zuv"
# =============================================================================
# Design Check Keys — paste these into common.py alongside existing KEY_ consts
# =============================================================================

# ---------------------------------------------------------------------------
# Check identity keys  (used as dict keys / card IDs throughout the codebase)
# ---------------------------------------------------------------------------
KEY_CHECK_FLEXURE          = "flexure"
KEY_CHECK_SHEAR            = "shear"
KEY_CHECK_INTERACTION      = "interaction"
KEY_CHECK_LTB              = "ltb"
KEY_CHECK_SHEAR_LONG_TRANS = "shear_long_trans"
KEY_CHECK_FATIGUE          = "fatigue"
KEY_CHECK_STRESS           = "stress"
KEY_CHECK_DEFLECTION       = "deflection"

# Ordered list used for card layout (left-col, right-col alternating)
DESIGN_CHECK_ORDER = [
    KEY_CHECK_FLEXURE,
    KEY_CHECK_SHEAR_LONG_TRANS,
    KEY_CHECK_SHEAR,
    KEY_CHECK_FATIGUE,
    KEY_CHECK_INTERACTION,
    KEY_CHECK_STRESS,
    KEY_CHECK_LTB,
    KEY_CHECK_DEFLECTION,
]

# Human-readable titles for each check card
DESIGN_CHECK_TITLES = {
    KEY_CHECK_FLEXURE:          "Strength Limit State (Flexure)",
    KEY_CHECK_SHEAR_LONG_TRANS: "Resistance to Longitudinal and Transverse Shear",
    KEY_CHECK_SHEAR:            "Strength Limit State (Shear)",
    KEY_CHECK_FATIGUE:          "Resistance to Fatigue",
    KEY_CHECK_INTERACTION:      "Interaction",
    KEY_CHECK_STRESS:           "Stress Limitation",
    KEY_CHECK_LTB:              "Lateral Torsional Buckling",
    KEY_CHECK_DEFLECTION:       "Deflection and Crack Control",
}

# Units shown next to demand / capacity values in each card
DESIGN_CHECK_UNITS = {
    KEY_CHECK_FLEXURE:          "kNm",
    KEY_CHECK_SHEAR:            "kN",
    KEY_CHECK_INTERACTION:      "",
    KEY_CHECK_LTB:              "kNm",
    KEY_CHECK_SHEAR_LONG_TRANS: "N/mm",
    KEY_CHECK_FATIGUE:          "MPa",
    KEY_CHECK_STRESS:           "MPa",
    KEY_CHECK_DEFLECTION:       "mm",
}

# ---------------------------------------------------------------------------
# LaTeX equation strings — standalone fragment suitable for embedding inside
# a \[ ... \] display-math block in a minimal article document.
#
# Convention:
#   EQ_<KEY>_LINE_<n>   one display-math line  (n = 1, 2, 3 …)
#   EQ_<KEY>_LINES      tuple of all lines in render order
#
# Each string is a *raw* Python string so backslashes reach LaTeX unchanged.
# ---------------------------------------------------------------------------

# -- Flexure (IRC 22 Cl. 603.3.1 / IS 800 Cl. 8.2.1) ----------------------
EQ_FLEXURE_LINE_1 = r"M_d \leq M_r"
EQ_FLEXURE_LINE_2 = r"M_r = \beta_b \cdot Z_p \cdot f_y \;/\; \gamma_{m0}"
EQ_FLEXURE_LINES  = (EQ_FLEXURE_LINE_1, EQ_FLEXURE_LINE_2)

# -- Shear (IS 800 Cl. 8.4 / IRC 22 Cl. 603.3.3) --------------------------
EQ_SHEAR_LINE_1 = r"V_d \leq V_r"
EQ_SHEAR_LINE_2 = r"V_r = \frac{A_v \cdot f_y}{\sqrt{3} \cdot \gamma_{m0}}"
EQ_SHEAR_LINES  = (EQ_SHEAR_LINE_1, EQ_SHEAR_LINE_2)

# -- Interaction (IS 800 Cl. 9.2.2) ----------------------------------------
EQ_INTERACTION_LINE_1 = (
    r"\frac{M_d}{\beta_b\,Z_p\,f_y/\gamma_{m0}}"
    r"+ \frac{V_d}{A_v\,f_y/(\sqrt{3}\,\gamma_{m0})} \leq 1.0"
)
EQ_INTERACTION_LINES  = (EQ_INTERACTION_LINE_1,)

# -- Lateral Torsional Buckling (IRC 22 Cl. 603.3.3.1 / IS 800 Cl. 8.2.2) -
EQ_LTB_LINE_1 = r"M_d \leq M_{cr}"
EQ_LTB_LINE_2 = r"M_{cr} \approx \frac{\pi^2 E\,I_y}{L_{\mathrm{LTB}}^{\,2}}"
EQ_LTB_LINES  = (EQ_LTB_LINE_1, EQ_LTB_LINE_2)

# -- Longitudinal & Transverse Shear (IRC 22 Cl. 606.4.1) ------------------
EQ_SHEAR_LONG_TRANS_LINE_1 = r"V_L \leq n \cdot Q_u \;/\; s"
EQ_SHEAR_LONG_TRANS_LINE_2 = r"V_L = V_d \cdot A_{ec} \cdot \bar{y} \;/\; I_c"
EQ_SHEAR_LONG_TRANS_LINE_3 = (
    r"Q_u = \min\!\left("
    r"0.8\,f_u\,A_s,\;"
    r"\frac{0.29\,\alpha\,d^2\sqrt{f_{ck}\,E_{cm}}}{\gamma_v}"
    r"\right)"
)
EQ_SHEAR_LONG_TRANS_LINES  = (
    EQ_SHEAR_LONG_TRANS_LINE_1,
    EQ_SHEAR_LONG_TRANS_LINE_2,
    EQ_SHEAR_LONG_TRANS_LINE_3,
)

# -- Fatigue (IRC 22 Cl. 605) -----------------------------------------------
EQ_FATIGUE_LINE_1 = r"\Delta\sigma \leq \Delta\sigma_{\mathrm{allowable}}"
EQ_FATIGUE_LINE_2 = r"\Delta\sigma_{\mathrm{allowable}} = \Delta\sigma_C \;/\; \gamma_{mf}"
EQ_FATIGUE_LINES  = (EQ_FATIGUE_LINE_1, EQ_FATIGUE_LINE_2)

# -- Stress Limitation (IRC 22 Cl. 604.3.1) ---------------------------------
EQ_STRESS_LINE_1 = r"\sigma = M_d \;/\; Z"
EQ_STRESS_LINE_2 = r"\sigma \leq f_y \;/\; \gamma_{m0}"
EQ_STRESS_LINES  = (EQ_STRESS_LINE_1, EQ_STRESS_LINE_2)

# -- Deflection (IRC 22 Cl. 604.3.2) ----------------------------------------
EQ_DEFLECTION_LINE_1 = r"\delta \leq L \;/\; x"
EQ_DEFLECTION_LINE_2 = r"(\text{Default } x = 600)"
EQ_DEFLECTION_LINES  = (EQ_DEFLECTION_LINE_1, EQ_DEFLECTION_LINE_2)

# Master map:  key  ->  tuple of LaTeX lines  (imported by the UI tab)
DESIGN_CHECK_EQ_LINES = {
    KEY_CHECK_FLEXURE:          EQ_FLEXURE_LINES,
    KEY_CHECK_SHEAR:            EQ_SHEAR_LINES,
    KEY_CHECK_INTERACTION:      EQ_INTERACTION_LINES,
    KEY_CHECK_LTB:              EQ_LTB_LINES,
    KEY_CHECK_SHEAR_LONG_TRANS: EQ_SHEAR_LONG_TRANS_LINES,
    KEY_CHECK_FATIGUE:          EQ_FATIGUE_LINES,
    KEY_CHECK_STRESS:           EQ_STRESS_LINES,
    KEY_CHECK_DEFLECTION:       EQ_DEFLECTION_LINES,
}

# ---------------------------------------------------------------------------
# HTML fallback equation strings  (used when LaTeX rendering is unavailable)
# ---------------------------------------------------------------------------
EQ_HTML_FLEXURE = (
    "<i>M</i><sub>d</sub> &le; <i>M</i><sub>r</sub><br><br>"
    "<i>M</i><sub>r</sub> = &beta;<sub>b</sub> &middot; <i>Z</i><sub>p</sub>"
    " &middot; <i>f</i><sub>y</sub> / &gamma;<sub>m0</sub>"
)

EQ_HTML_SHEAR = (
    "<i>V</i><sub>d</sub> &le; <i>V</i><sub>r</sub><br><br>"
    "<i>V</i><sub>r</sub> = <i>A</i><sub>v</sub> &middot; <i>f</i><sub>y</sub>"
    " / (&radic;3 &middot; &gamma;<sub>m0</sub>)"
)

EQ_HTML_INTERACTION = (
    "<i>M</i><sub>d</sub> / (&beta;<sub>b</sub> &middot; <i>Z</i><sub>p</sub>"
    " &middot; <i>f</i><sub>y</sub> / &gamma;<sub>m0</sub>)"
    " + <i>V</i><sub>d</sub> / (<i>A</i><sub>v</sub> &middot; <i>f</i><sub>y</sub>"
    " / (&radic;3 &middot; &gamma;<sub>m0</sub>)) &le; 1.0"
)

EQ_HTML_LTB = (
    "<i>M</i><sub>d</sub> &le; <i>M</i><sub>cr</sub><br><br>"
    "<i>M</i><sub>cr</sub> &approx; (&pi;&sup2; &middot; <i>E</i> &middot;"
    " <i>I</i><sub>y</sub>) / <i>L</i><sub>LTB</sub>&sup2;"
)

EQ_HTML_SHEAR_LONG_TRANS = (
    "<i>V</i><sub>L</sub> &le; <i>n</i> &middot; <i>Q</i><sub>u</sub> / <i>s</i><br><br>"
    "<i>V</i><sub>L</sub> = <i>V</i><sub>d</sub> &middot; <i>A</i><sub>ec</sub>"
    " &middot; <i>&#x1D56E;</i> / <i>I</i><sub>c</sub><br><br>"
    "<i>Q</i><sub>u</sub> = min(0.8 <i>f</i><sub>u</sub> <i>A</i><sub>s</sub>,"
    " 0.29 &alpha; <i>d</i>&sup2; &radic;(<i>f</i><sub>ck</sub>"
    " <i>E</i><sub>cm</sub>)) / &gamma;<sub>v</sub>"
)

EQ_HTML_FATIGUE = (
    "&Delta;&sigma; &le; &Delta;&sigma;<sub>allowable</sub><br><br>"
    "&Delta;&sigma;<sub>allowable</sub> = &Delta;&sigma;<sub>C</sub>"
    " / &gamma;<sub>mf</sub>"
)

EQ_HTML_STRESS = (
    "&sigma; = <i>M</i><sub>d</sub> / <i>Z</i><br><br>"
    "&sigma; &le; <i>f</i><sub>y</sub> / &gamma;<sub>m0</sub>"
)

EQ_HTML_DEFLECTION = (
    "&delta; &le; <i>L</i> / <i>x</i><br><br>"
    "(Default <i>x</i> = 600)"
)

# Master HTML fallback map
DESIGN_CHECK_EQ_HTML = {
    KEY_CHECK_FLEXURE:          EQ_HTML_FLEXURE,
    KEY_CHECK_SHEAR:            EQ_HTML_SHEAR,
    KEY_CHECK_INTERACTION:      EQ_HTML_INTERACTION,
    KEY_CHECK_LTB:              EQ_HTML_LTB,
    KEY_CHECK_SHEAR_LONG_TRANS: EQ_HTML_SHEAR_LONG_TRANS,
    KEY_CHECK_FATIGUE:          EQ_HTML_FATIGUE,
    KEY_CHECK_STRESS:           EQ_HTML_STRESS,
    KEY_CHECK_DEFLECTION:       EQ_HTML_DEFLECTION,
}

# ---------------------------------------------------------------------------
# Demand / capacity prefix labels  (HTML, for the value lines in each card)
# ---------------------------------------------------------------------------
DESIGN_CHECK_DEM_PFX = {
    KEY_CHECK_FLEXURE:          "<i>M<sub>d</sub></i>",
    KEY_CHECK_SHEAR:            "<i>V<sub>d</sub></i>",
    KEY_CHECK_LTB:              "<i>M<sub>d</sub></i>",
    KEY_CHECK_SHEAR_LONG_TRANS: "<i>V<sub>L</sub></i>",
    KEY_CHECK_FATIGUE:          "&Delta;<i>&sigma;</i>",
    KEY_CHECK_STRESS:           "<i>&sigma;</i>",
    KEY_CHECK_DEFLECTION:       "<i>&delta;</i>",
}
DESIGN_CHECK_CAP_PFX = {
    KEY_CHECK_FLEXURE:          "<i>M<sub>r</sub></i>",
    KEY_CHECK_SHEAR:            "<i>V<sub>r</sub></i>",
    KEY_CHECK_LTB:              "<i>M<sub>cr</sub></i>",
    KEY_CHECK_SHEAR_LONG_TRANS: "<i>nQ<sub>u</sub>/s</i>",
    KEY_CHECK_FATIGUE:          "&Delta;<i>&sigma;<sub>allowable</sub></i>",
    KEY_CHECK_STRESS:           "<i>f<sub>y</sub> / &gamma;<sub>m</sub></i>",
    KEY_CHECK_DEFLECTION:       "<i>L / x</i>",
}

# Value Lists for Additional Inputs
VALUES_NO_YES = ["No", "Yes"]
VALUES_REINF_MATERIAL = ["Fe 415", "Fe 500", "Fe 550"]
VALUES_REINF_SIZE = ["8", "10", "12", "16", "20", "25", "32"]
VALUES_CRASH_BARRIER_TYPE = [
    "IRC 5 - RCC Crash Barrier",
    "IRC 5 - Steel Crash Barrier",
    "IRC 5 - Metal Beam",
    "Custom",
]
VALUES_MEDIAN_TYPE = [
    "IRC 5 - Raised Kerb",
    "IRC 5 - Flush Median",
    "Custom",
]
VALUES_GIRDER_TYPE = ["Welded", "Rolled"]
VALUES_GIRDER_SYMMETRY = ["Girder Symmetric", "Girder Unsymmetric"]
VALUES_GIRDER_SUPPORT_TYPE = [
    "Major Laterally Supported",
    "Minor Laterally Unsupported",
    "Major Laterally Unsupported",
]
VALUES_GIRDER_DESIGN_MODE = ["Optimized", "Custom"]
VALUES_GIRDER_SPAN_MODE = ["Full Length", "Custom"]
VALUES_PROFILE_SCOPE = ["All", "Custom"]
VALUES_OPTIMIZATION_MODE = ["Optimized", "Custom", "All"]
VALUES_TORSIONAL_RESTRAINT = [
    "Fully Restrained",
    "Partially Restrained - Support Connection",
    "Partially Restrained - Bearing Support",
]
VALUES_WARPING_RESTRAINT = ["Both Flanges Restrained", "No Restraint"]
VALUES_WEB_TYPE = ["Thin Web with ITS", "Thick Web without ITS"]
VALUES_STIFFENER_DESIGN = ["Simple Post Critical", "Tension Field"]
VALUES_BEARING_STIFFENER_COUNT = ["1", "2", "3", "4"]
VALUES_LONGITUDINAL_STIFFENER = ["No", "Yes and 1 stiffener", "Yes and 2 stiffeners"]
VALUES_CROSS_BRACING_TYPE = [
    "K-bracing",
    "K-bracing with top bracket",
    "X-bracing",
    "X-bracing with bottom bracket",
    "X-bracing with top and bottom brackets",
]
VALUES_END_DIAPHRAGM_TYPE = ["Cross Bracing", "Rolled Beam", "Welded Beam"]
VALUES_WEARING_COAT_MATERIAL = ["Concrete", "Bituminous", "Other"]
VALUES_RAILING_TYPE = ["IRC 5 - RCC Railing", "IRC 5 - Steel Railing", "Custom"]
VALUES_CUSTOM_AXLE_TYPE = ["Single", "Bogie"]
VALUES_FOOTPATH_PRESSURE_MODE = ["Automatic", "User-defined"]
VALUES_SUPPORT_TYPE = ["Fixed", "Pinned"]

#Sail thic
SAIL_APPROVED_THICKNESS_VALUES=[
        "8", "10", "12", "14", "16", "18", "20", "22", "25", "28", "32", "36",
        "40", "45", "50", "56", "63", "75", "80", "90", "100", "110", "120",
    ]
MIN_BEARING_STIFFENER_SPACING_MM = 50
STIFFENER_DETAILS_DEFAULTS = {
    "form_label_width": 245,
    "combo_width": 190,
    "outstand_default_text": "NA",
    "min_bearing_spacing_mm": MIN_BEARING_STIFFENER_SPACING_MM,
    "bearing_stiffeners_each_end": VALUES_BEARING_STIFFENER_COUNT[1],
    "bearing_spacing_mm": "50",
    "bearing_thickness_mode": VALUES_PROFILE_SCOPE[0],
    "bearing_thickness_value": SAIL_APPROVED_THICKNESS_VALUES[0],
    "bearing_outstand_mm": "",
    "intermediate_stiffener": VALUES_NO_YES[0],
    "intermediate_spacing_mm": "NA",
    "intermediate_outstand_mm": "",
    "longitudinal_stiffener": VALUES_LONGITUDINAL_STIFFENER[0],
    "intermediate_thickness_mode": VALUES_PROFILE_SCOPE[0],
    "intermediate_thickness_value": SAIL_APPROVED_THICKNESS_VALUES[0],
    "longitudinal_thickness_mode": VALUES_PROFILE_SCOPE[0],
    "longitudinal_thickness_value": SAIL_APPROVED_THICKNESS_VALUES[0],
    "shear_buckling_method": VALUES_STIFFENER_DESIGN[0] if VALUES_STIFFENER_DESIGN else "",
}

# Defaults + validation helpers
DEFAULT_SELF_WEIGHT_FACTOR = 1.0
DEFAULT_CONCRETE_DENSITY = 25.0
DEFAULT_STEEL_DENSITY = 78.5
DEFAULT_BEARING_LENGTH = 0.0

MIN_FOOTPATH_WIDTH = 1.5
MIN_RAILING_HEIGHT = 1.0
MIN_SAFETY_KERB_WIDTH = 0.75
DEFAULT_GIRDER_SPACING = 2.5
DEFAULT_DECK_OVERHANG = 1.0
DEFAULT_CRASH_BARRIER_WIDTH = 0.5
DEFAULT_RAILING_WIDTH = 0.375
DEFAULT_CROSS_BRACING_SPACING = 3.0

CROSS_BRACING_DEFAULTS = {
    "select_girders":               "",
    "member_id":                    "",
    "type":                         VALUES_CROSS_BRACING_TYPE[0],   # "K-bracing"
    "bracing_connection":           "Bolted",
    "bracing_section_type":         "",
    "bracing_section_designation":  "",
    "top_chord":                    VALUES_NO_YES[0],               # "No"
    "top_chord_section_type":       "",
    "top_chord_section_desig":      "",
    "bottom_chord":                 VALUES_NO_YES[0],               # "No"
    "bottom_chord_section_type":    "",
    "bottom_chord_section_desig":   "",
    "spacing":                      DEFAULT_CROSS_BRACING_SPACING,  # 3.0
}

# IRC helper option constants
KEY_VEHICLE = ["Class70R(W)", "Class70R(T)", "ClassA", "ClassB"]
KEY_TYPE_BRIDGE = ["Highway", "Rural"]
KEY_DESIGN_FATIGUE = ["Dont design for fatigue", "Regular Vehicles", "Heavy Vehicles"]
KEY_TYPE_FOOTWAY = ["Default", "Regular Footway", "Crowded Footway"]
FOOTWAY_LOADS = {
    "Default": 500,
    "Regular Footway": 400,
    "Crowded Footway": 500,
}
KEY_TERRAIN_TYPE = ["plain", "obstructed"]

from pathlib import Path
import sqlite3
_DB_PATH = Path(__file__).resolve().parents[1] / "data" / "ResourceFiles" / "Intg_osdag.sqlite"

def connectdb(table_name: str) -> list[str]:
    """
    Fetches all grade designations from the Grade column of the given table.

    Parameters
    ----------
    table_name : str
        Name of the table to query.

    Returns
    -------
    list[str]
        List of grade strings (e.g. ["M15", "M20", ...]).

    Raises
    ------
    LookupError
        If the database is not found or the query fails.
    """
    if not _DB_PATH.exists():
        raise LookupError(f"Material database not found at {_DB_PATH} in get_grades")

    try:
        con = sqlite3.connect(_DB_PATH)
        cur = con.cursor()
        cur.execute(f'SELECT Grade FROM {table_name}')
        rows = cur.fetchall()
        con.close()
        return [row[0] for row in rows]
    except sqlite3.Error as e:
        raise LookupError(f"Error querying database in connectdb(): {e}")


def get_angle_section_properties(designation: str) -> dict:
    """
    Fetch section properties for a single angle from the Angles table.

    Parameters
    ----------
    designation : str
        Angle designation as stored in the DB, e.g. "100 x 100 x 10".
        A leading "IS " prefix (as shown in the UI) is stripped automatically.

    Returns
    -------
    dict
        All columns of the matching Angles row, keyed by column name
        (e.g. {"Mass": 15.04, "Area": 19.1, "Iz": 180.0, ...}).

    Raises
    ------
    LookupError
        If the database is missing, the query fails, or no row matches.
    """
    if not _DB_PATH.exists():
        raise LookupError(f"Material database not found at {_DB_PATH} in get_angle_section_properties")

    designation = designation.strip()
    if designation.upper().startswith("IS "):
        designation = designation[3:].strip()

    try:
        con = sqlite3.connect(_DB_PATH)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM Angles WHERE Designation = ?", (designation,))
        row = cur.fetchone()
        con.close()
    except sqlite3.Error as e:
        raise LookupError(f"Error querying database in get_angle_section_properties(): {e}")

    if row is None:
        raise LookupError(f"Angle designation '{designation}' not found in Angles table")
    return dict(row)


import platform
import os

def get_documents_folder():
    system = platform.system()

    if system == "Windows":
        # Windows: typically C:\Users\Username\Documents
        docs_path = Path.home() / "Documents"
        if not docs_path.exists():
            docs_path = Path.home() / "OneDrive" / "Documents"
    elif system == "Darwin":  # macOS
        # macOS: typically /Users/Username/Documents
        docs_path = Path.home() / "Documents"
    elif system == "Linux":
        # Linux: typically /home/username/Documents
        # Also check XDG_DOCUMENTS_DIR for custom locations
        xdg_docs = os.environ.get("XDG_DOCUMENTS_DIR")
        if xdg_docs:
            docs_path = Path(xdg_docs)
        else:
            docs_path = Path.home() / "Documents"
    else:
        # Fallback to home directory for unknown systems
        docs_path = Path.home()

    # Ensure the directory exists, otherwise fall back to home
    if not docs_path.exists():
        docs_path = Path.home()
    return str(docs_path)

# ------- Database Interaction -------------------------------------------------------------
"""Standalone girder section catalog — no UI dependencies.

Provides:
    GirderSectionCatalog  — loads rolled beam data from SQLite
    BeamSection           — frozen dataclass for beam properties
    girder_catalog        — module-level singleton instance

Public API:
    get_is_section_list()              → list[str]
    get_is_section_properties(desig)   → dict | None
"""

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


# ── Database location ─────────────────────────────────────────────────────────

def _locate_database() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "core" / "data" / "ResourceFiles" / "Intg_osdag.sqlite"
        if candidate.exists():
            return candidate
    return current.parents[4] / "core" / "data" / "ResourceFiles" / "Intg_osdag.sqlite"

DB_PATH = _locate_database()

# ── Data container ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class BeamSection:
    """Immutable container for rolled beam section properties."""
    designation:                  str
    type_name:                    str
    mass_per_meter_kg:            float
    area_cm2:                     float
    depth_mm:                     float
    flange_width_mm:              float
    web_thickness_mm:             float
    flange_thickness_mm:          float
    root_radius_mm:               float
    toe_radius_mm:                float
    moment_of_inertia_zz_cm4:    float
    moment_of_inertia_yy_cm4:    float
    radius_of_gyration_z_cm:     float
    radius_of_gyration_y_cm:     float
    elastic_section_modulus_z_cm3: float
    elastic_section_modulus_y_cm3: float
    plastic_section_modulus_z_cm3: float
    plastic_section_modulus_y_cm3: float
    torsion_constant_cm4:         float
    warping_constant_cm6:         float

# ── Catalog ───────────────────────────────────────────────────────────────────

class GirderSectionCatalog:
    """Loads rolled girder data from the bundled SQLite database."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self._sections: Dict[str, BeamSection] = {}
        self._outlines:  Dict[str, dict]       = {}
        self._load()

    def _load(self) -> None:
        if not self.db_path.exists():
            return
        conn   = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT Designation, Type, Mass, Area, D, B, tw, T,
                       R1, R2, Iz, Iy, rz, ry, Zz, Zy, Zpz, Zpy, It, Iw
                FROM Beams
            """)
            for row in cursor.fetchall():
                (desig, type_name, mass, area, depth, b_flange,
                 tw, tf, r1, r2, iz, iy, rz, ry,
                 zz, zy, zpz, zpy, it, iw) = row

                section = BeamSection(
                    designation               = str(desig).strip(),
                    type_name                 = str(type_name or "").strip(),
                    mass_per_meter_kg         = float(mass  or 0.0),
                    area_cm2                  = float(area  or 0.0),
                    depth_mm                  = float(depth or 0.0),
                    flange_width_mm           = float(b_flange or 0.0),
                    web_thickness_mm          = float(tw    or 0.0),
                    flange_thickness_mm       = float(tf    or 0.0),
                    root_radius_mm            = float(r1    or 0.0),
                    toe_radius_mm             = float(r2    or 0.0),
                    moment_of_inertia_zz_cm4  = float(iz    or 0.0),
                    moment_of_inertia_yy_cm4  = float(iy    or 0.0),
                    radius_of_gyration_z_cm   = float(rz    or 0.0),
                    radius_of_gyration_y_cm   = float(ry    or 0.0),
                    elastic_section_modulus_z_cm3 = float(zz  or 0.0),
                    elastic_section_modulus_y_cm3 = float(zy  or 0.0),
                    plastic_section_modulus_z_cm3 = float(zpz or 0.0),
                    plastic_section_modulus_y_cm3 = float(zpy or 0.0),
                    torsion_constant_cm4      = float(it    or 0.0),
                    warping_constant_cm6      = float(iw    or 0.0),
                )
                self._sections[section.designation] = section
                self._outlines[section.designation] = {
                    "designation":            section.designation,
                    "depth_mm":               section.depth_mm,
                    "top_flange_width_mm":    section.flange_width_mm,
                    "bottom_flange_width_mm": section.flange_width_mm,
                    "web_thickness_mm":       section.web_thickness_mm,
                    "top_flange_thickness_mm":    section.flange_thickness_mm,
                    "bottom_flange_thickness_mm": section.flange_thickness_mm,
                }
        finally:
            conn.close()

    def list_available_sections(self) -> Dict[str, BeamSection]:
        return dict(self._sections)

    def get_beam_profile(self, designation: str) -> Optional[BeamSection]:
        if not designation:
            return None
        return self._sections.get(str(designation).strip())

    def get_rolled_section(self, designation: str) -> Optional[dict]:
        if not designation:
            return None
        return self._outlines.get(str(designation).strip())


# ── Module-level singleton ────────────────────────────────────────────────────

girder_catalog = GirderSectionCatalog()

# ── Public API ────────────────────────────────────────────────────────────────

def get_is_section_list() -> list[str]:
    """Return sorted list of all IS section designations available in the database."""
    return sorted(girder_catalog.list_available_sections().keys())


def get_is_section_properties(designation: str) -> Optional[dict]:
    """Return section properties for the given designation.

    Keys match KEY_MP_GIRDER_* suffix names used in working_input_dict:
        mass, area, iz, iy, rz, ry, zz, zy, zuz, zuy, it, iw

    Returns None if designation is not found.
    """
    beam = girder_catalog.get_beam_profile(designation)
    if beam is None:
        return None
    return {
        "mass":  beam.mass_per_meter_kg,
        "area":  beam.area_cm2,
        "iz":    beam.moment_of_inertia_zz_cm4,
        "iy":    beam.moment_of_inertia_yy_cm4,
        "rz":    beam.radius_of_gyration_z_cm,
        "ry":    beam.radius_of_gyration_y_cm,
        "zz":    beam.elastic_section_modulus_z_cm3,
        "zy":    beam.elastic_section_modulus_y_cm3,
        "zuz":   beam.plastic_section_modulus_z_cm3,
        "zuy":   beam.plastic_section_modulus_y_cm3,
        "it":    beam.torsion_constant_cm4,
        "iw":    beam.warping_constant_cm6,
    }

def get_angle_designation_list() -> list[str]:
    """Return sorted list of all angle designations (equal + unequal) from the database."""
    if not _DB_PATH.exists():
        return []
    try:
        con = sqlite3.connect(_DB_PATH)
        cur = con.cursor()
        designations: set[str] = set()
        for table in ("EqualAngle", "UnequalAngle"):
            try:
                cur.execute(f"SELECT Designation FROM {table}")
                for (des,) in cur.fetchall():
                    designations.add(str(des).strip())
            except sqlite3.Error:
                pass
        con.close()
        return sorted(designations)
    except sqlite3.Error:
        return []


def get_channel_section_list() -> list[str]:
    """Return sorted list of all channel designations from the database."""
    if not _DB_PATH.exists():
        return []
    try:
        con = sqlite3.connect(_DB_PATH)
        cur = con.cursor()
        cur.execute("SELECT Designation FROM Channels")
        designations = sorted(str(des).strip() for (des,) in cur.fetchall())
        con.close()
        return designations
    except sqlite3.Error:
        return []
