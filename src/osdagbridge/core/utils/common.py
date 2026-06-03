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
KEY_DECK_CONCRETE_GRADE_BASIC = "material.deck_concrete_grade"

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

KEY_SD_STIFFENER_ROW_INTERMEDIATE = "steeldesign.details.stiffener.row.intermediate"
KEY_SD_STIFFENER_ROW_LONGITUDINAL = "steeldesign.details.stiffener.row.longitudinal"
KEY_SD_STIFFENER_ROW_BEARING = "steeldesign.details.stiffener.row.bearing"
KEY_SD_STIFFENER_COL_GRADE = "steeldesign.details.stiffener.col.grade"
KEY_SD_STIFFENER_COL_THICKNESS = "steeldesign.details.stiffener.col.thickness"
KEY_SD_STIFFENER_COL_WIDTH = "steeldesign.details.stiffener.col.width"
KEY_SD_STIFFENER_COL_SPACING = "steeldesign.details.stiffener.col.spacing"

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
KEY_CB_TAB = "typical_section.crash_barrier.tab"
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

# Member Properties - Girder Details
KEY_MP_GIRDER_TYPE = "member_properties.girder_details.section_input.type"
KEY_MP_GIRDER_IS_SECTION = "member_properties.girder_details.section_input.is_section"
KEY_MP_GIRDER_SYMMETRY = "member_properties.girder_details.section_input.symmetry"
KEY_MP_GIRDER_TOP_FLANGE_WIDTH = "member_properties.girder_details.section_input.top_flange_width"
KEY_MP_GIRDER_TOP_FLANGE_THICKNESS = "member_properties.girder_details.section_input.top_flange_thickness"
KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH = "member_properties.girder_details.section_input.bottom_flange_width"
KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS = "member_properties.girder_details.section_input.bottom_flange_thickness"
KEY_MP_GIRDER_DEPTH = "member_properties.girder_details.section_input.depth"
KEY_MP_GIRDER_WEB_THICKNESS = "member_properties.girder_details.section_input.web_thickness"
KEY_MP_GIRDER_WEB_DEPTH = "member_properties.girder_details.section_input.web_depth"
KEY_MP_GIRDER_TORSIONAL_RESTRAINT = "member_properties.girder_details.section_input.torsional_restraint"
KEY_MP_GIRDER_WARPING_RESTRAINT = "member_properties.girder_details.section_input.warping_restraint"
KEY_MP_GIRDER_WEB_TYPE = "member_properties.girder_details.section_input.web_type"

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

# Member Properties - Stiffener Details (dynamic keys, mirrors KEY_MP_GIRDER_* pattern)
KEY_MP_STIFFENER_DESIGN_METHOD                = "member_properties.stiffener_details.design_method"
KEY_MP_STIFFENER_NO_BEARING_STIFFENERS        = "member_properties.stiffener_details.no_bearing_stiffeners_each_end"
KEY_MP_STIFFENER_BEARING_PLATE_THICKNESS      = "member_properties.stiffener_details.bearing_stiffener_plate_thickness"
KEY_MP_STIFFENER_BEARING_OUTSTAND             = "member_properties.stiffener_details.bearing_stiffener_outstand"
KEY_MP_STIFFENER_SPACING                      = "member_properties.stiffener_details.bearing_stiffener_spacing"
KEY_MP_STIFFENER_INTERMEDIATE                 = "member_properties.stiffener_details.intermediate_stiffener"
KEY_MP_STIFFENER_INTERMEDIATE_SPACING         = "member_properties.stiffener_details.intermediate_stiffener_spacing"
KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS       = "member_properties.stiffener_details.intermediate_stiffener_thickness"
KEY_MP_STIFFENER_INTERMEDIATE_OUTSTAND        = "member_properties.stiffener_details.intermediate_stiffener_outstand"
KEY_MP_STIFFENER_LONGITUDINAL                 = "member_properties.stiffener_details.longitudinal_stiffener"
KEY_MP_STIFFENER_LONGITUDINAL_THICKNESS       = "member_properties.stiffener_details.longitudinal_stiffener_thickness"


# Member Properties - Cross Bracing Details
KEY_MP_CB_TYPE = "member_properties.cross_bracing_details.type"
KEY_MP_CB_SECTION = "member_properties.cross_bracing_details.section"
KEY_MP_CB_TOP_CHORD_SECTION_TYPE      = "member_properties.cross_bracing_details.top_chord_section_type"
KEY_MP_CB_TOP_CHORD_SECTION_DESIG     = "member_properties.cross_bracing_details.top_chord_section_designation"
KEY_MP_CB_BOTTOM_CHORD_SECTION_TYPE   = "member_properties.cross_bracing_details.bottom_chord_section_type"
KEY_MP_CB_BOTTOM_CHORD_SECTION_DESIG  = "member_properties.cross_bracing_details.bottom_chord_section_designation"
KEY_MP_CB_SPACING = "member_properties.cross_bracing_details.spacing"
KEY_MP_CB_SELECT_GIRDERS              = "member_properties.cross_bracing_details.select_girders"
KEY_MP_CB_MEMBER_ID                   = "member_properties.cross_bracing_details.member_id"
KEY_MP_CB_BRACING_SECTION_TYPE        = "member_properties.cross_bracing_details.bracing_section_type"
KEY_MP_CB_BRACING_SECTION_DESIGNATION = "member_properties.cross_bracing_details.bracing_section_designation"
KEY_MP_CB_TOP_CHORD                   = "member_properties.cross_bracing_details.top_chord"
KEY_MP_CB_BOTTOM_CHORD                = "member_properties.cross_bracing_details.bottom_chord"


# Member Properties - End Diaphragm Details
KEY_MP_ED_TYPE = "member_properties.end_diaphragm_details.type"
KEY_MP_ED_BRACING_TYPE = "member_properties.end_diaphragm_details.bracing_type"
KEY_MP_ED_BRACING_SECTION = "member_properties.end_diaphragm_details.bracing_section"
KEY_MP_ED_BRACING_SECTION_DESIGNATION = "member_properties.end_diaphragm_details.bracing_section_designation"
KEY_MP_ED_TOP_CHORD_SECTION_TYPE = "member_properties.end_diaphragm_details.top_chord_section_type" 
KEY_MP_ED_TOP_CHORD_SECTION_DESIG = "member_properties.end_diaphragm_details.top_chord_section_designation"
KEY_MP_ED_BOTTOM_CHORD_SECTION_TYPE = "member_properties.end_diaphragm_details.bottom_chord_section_type"
KEY_MP_ED_BOTTOM_CHORD_SECTION_DESIG = "member_properties.end_diaphragm_details.bottom_chord_section_designation"
KEY_MP_ED_SPACING                     = "member_properties.end_diaphragm_details.spacing"
KEY_MP_ED_SELECT_GIRDERS              = "member_properties.end_diaphragm_details.select_girders"
KEY_MP_ED_MEMBER_ID                   = "member_properties.end_diaphragm_details.member_id"


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
KEY_TD_LOAD_COMBINATION = "transverse_member_design.load_combination"
KEY_TD_SECTION_INPUTS_DESIGN = "transverse_member_design.section_inputs.design"
KEY_TD_SECTION_INPUTS_BRACING_TYPE = "transverse_member_design.section_inputs.bracing_type"
KEY_TD_SECTION_INPUTS_BRACING_SECTION_TYPE = "transverse_member_design.section_inputs.bracing_section_type"
KEY_TD_SECTION_INPUTS_BRACING_SECTION_DESIGNATION = "transverse_member_design.section_inputs.bracing_section_designation"
KEY_TD_SECTION_INPUTS_TOP_CHORD_ENABLED = "transverse_member_design.section_inputs.top_chord_enabled"
KEY_TD_SECTION_INPUTS_TOP_CHORD_SECTION_TYPE = "transverse_member_design.section_inputs.top_chord_section_type"
KEY_TD_SECTION_INPUTS_TOP_CHORD_SECTION_DESIGNATION = "transverse_member_design.section_inputs.top_chord_section_designation"
KEY_TD_SECTION_INPUTS_BOTTOM_CHORD_ENABLED = "transverse_member_design.section_inputs.bottom_chord_enabled"
KEY_TD_SECTION_INPUTS_BOTTOM_CHORD_SECTION_TYPE = "transverse_member_design.section_inputs.bottom_chord_section_type"
KEY_TD_SECTION_INPUTS_BOTTOM_CHORD_SECTION_DESIGNATION = "transverse_member_design.section_inputs.bottom_chord_section_designation"
KEY_TD_SECTION_INPUTS_SPACING = "transverse_member_design.section_inputs.spacing"
KEY_TD_BRACING_DIAGRAM = "transverse_member_design.bracing_diagram"
KEY_TD_SECTION_PROPS_BRACING = "transverse_member_design.section_properties.bracing"
KEY_TD_SECTION_PROPS_TOP_CHORD = "transverse_member_design.section_properties.top_chord"
KEY_TD_SECTION_PROPS_BOTTOM_CHORD = "transverse_member_design.section_properties.bottom_chord"
KEY_TD_DESIGN_CHECK_FORCES_TABLE = "transverse_member_design.design_check.forces_table"
KEY_TD_DESIGN_CHECK_RESULTS = "transverse_member_design.design_check.results"
KEY_TD_DETAILS_TAB = "transverse_member_design.details"
KEY_TD_DESIGN_CHECK_TAB = "transverse_member_design.design_check"

# Transverse Member Design - section property field keys
KEY_TD_BRACING_PROP_L = "transverse_member_design.section_properties.bracing.L"
KEY_TD_BRACING_PROP_H = "transverse_member_design.section_properties.bracing.H"
KEY_TD_BRACING_PROP_B = "transverse_member_design.section_properties.bracing.B"
KEY_TD_BRACING_PROP_TW = "transverse_member_design.section_properties.bracing.tw"
KEY_TD_BRACING_PROP_TF = "transverse_member_design.section_properties.bracing.tF"
KEY_TD_BRACING_PROP_RZ = "transverse_member_design.section_properties.bracing.rz"
KEY_TD_BRACING_PROP_M = "transverse_member_design.section_properties.bracing.M"
KEY_TD_BRACING_PROP_A = "transverse_member_design.section_properties.bracing.A"
KEY_TD_BRACING_PROP_IZ = "transverse_member_design.section_properties.bracing.Iz"
KEY_TD_BRACING_PROP_IV = "transverse_member_design.section_properties.bracing.Iv"
KEY_TD_BRACING_PROP_RV = "transverse_member_design.section_properties.bracing.rv"
KEY_TD_BRACING_PROP_ZZ = "transverse_member_design.section_properties.bracing.Zz"
KEY_TD_BRACING_PROP_ZV = "transverse_member_design.section_properties.bracing.Zv"
KEY_TD_BRACING_PROP_ZUZ = "transverse_member_design.section_properties.bracing.Zuz"
KEY_TD_BRACING_PROP_ZUV = "transverse_member_design.section_properties.bracing.Zuv"

KEY_TD_TOP_CHORD_PROP_L = "transverse_member_design.section_properties.top_chord.L"
KEY_TD_TOP_CHORD_PROP_H = "transverse_member_design.section_properties.top_chord.H"
KEY_TD_TOP_CHORD_PROP_B = "transverse_member_design.section_properties.top_chord.B"
KEY_TD_TOP_CHORD_PROP_TW = "transverse_member_design.section_properties.top_chord.tw"
KEY_TD_TOP_CHORD_PROP_TF = "transverse_member_design.section_properties.top_chord.tF"
KEY_TD_TOP_CHORD_PROP_RZ = "transverse_member_design.section_properties.top_chord.rz"
KEY_TD_TOP_CHORD_PROP_M = "transverse_member_design.section_properties.top_chord.M"
KEY_TD_TOP_CHORD_PROP_A = "transverse_member_design.section_properties.top_chord.A"
KEY_TD_TOP_CHORD_PROP_IZ = "transverse_member_design.section_properties.top_chord.Iz"
KEY_TD_TOP_CHORD_PROP_IV = "transverse_member_design.section_properties.top_chord.Iv"
KEY_TD_TOP_CHORD_PROP_RV = "transverse_member_design.section_properties.top_chord.rv"
KEY_TD_TOP_CHORD_PROP_ZZ = "transverse_member_design.section_properties.top_chord.Zz"
KEY_TD_TOP_CHORD_PROP_ZV = "transverse_member_design.section_properties.top_chord.Zv"
KEY_TD_TOP_CHORD_PROP_ZUZ = "transverse_member_design.section_properties.top_chord.Zuz"
KEY_TD_TOP_CHORD_PROP_ZUV = "transverse_member_design.section_properties.top_chord.Zuv"

KEY_TD_BOTTOM_CHORD_PROP_L = "transverse_member_design.section_properties.bottom_chord.L"
KEY_TD_BOTTOM_CHORD_PROP_H = "transverse_member_design.section_properties.bottom_chord.H"
KEY_TD_BOTTOM_CHORD_PROP_B = "transverse_member_design.section_properties.bottom_chord.B"
KEY_TD_BOTTOM_CHORD_PROP_TW = "transverse_member_design.section_properties.bottom_chord.tw"
KEY_TD_BOTTOM_CHORD_PROP_TF = "transverse_member_design.section_properties.bottom_chord.tF"
KEY_TD_BOTTOM_CHORD_PROP_RZ = "transverse_member_design.section_properties.bottom_chord.rz"
KEY_TD_BOTTOM_CHORD_PROP_M = "transverse_member_design.section_properties.bottom_chord.M"
KEY_TD_BOTTOM_CHORD_PROP_A = "transverse_member_design.section_properties.bottom_chord.A"
KEY_TD_BOTTOM_CHORD_PROP_IZ = "transverse_member_design.section_properties.bottom_chord.Iz"
KEY_TD_BOTTOM_CHORD_PROP_IV = "transverse_member_design.section_properties.bottom_chord.Iv"
KEY_TD_BOTTOM_CHORD_PROP_RV = "transverse_member_design.section_properties.bottom_chord.rv"
KEY_TD_BOTTOM_CHORD_PROP_ZZ = "transverse_member_design.section_properties.bottom_chord.Zz"
KEY_TD_BOTTOM_CHORD_PROP_ZV = "transverse_member_design.section_properties.bottom_chord.Zv"
KEY_TD_BOTTOM_CHORD_PROP_ZUZ = "transverse_member_design.section_properties.bottom_chord.Zuz"
KEY_TD_BOTTOM_CHORD_PROP_ZUV = "transverse_member_design.section_properties.bottom_chord.Zuv"

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
    "bearing_spacing_mm": "",
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
