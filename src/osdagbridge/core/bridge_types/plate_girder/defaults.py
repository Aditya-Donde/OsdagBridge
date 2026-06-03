"""Centralized defaults for Plate Girder Bridge."""

from __future__ import annotations


from osdagbridge.core.utils.codes.irc5_2015 import IRC5_2015
from osdagbridge.core.utils.codes.keyfile import (
    KEY_CRASH_BARRIER_TYPE,
    KEY_FOOTPATH,
    KEY_MEDIAN_TYPE,
    KEY_METALLIC_CRASH_BARRIER_TYPE,
    KEY_RAILING_TYPE,
    KEY_RIGID_CRASH_BARRIER_TYPE,
)
from osdagbridge.core.utils.common import (
    DEFAULT_RAILING_WIDTH,
    KEY_TS_GIRDER_SPACING, KEY_TS_NO_OF_GIRDERS, KEY_TS_DECK_OVERHANG, KEY_TS_OVERALL_WIDTH,
    KEY_TS_NO_OF_FOOTPATHS, KEY_TS_DECK_THICKNESS, KEY_TS_FOOTPATH_WIDTH, KEY_TS_FOOTPATH_THICKNESS,
    KEY_CB_TYPE, KEY_CB_DENSITY, KEY_CB_WIDTH, KEY_CB_HEIGHT, KEY_CB_AREA, KEY_CB_LOAD, KEY_CB_POST_SPACING,
    KEY_MD_TYPE, KEY_MD_DENSITY, KEY_MD_WIDTH, KEY_MD_HEIGHT, KEY_MD_AREA, KEY_MD_LOAD, KEY_MD_POST_SPACING,
    KEY_RL_TYPE, KEY_RL_WIDTH, KEY_RL_HEIGHT, KEY_RL_LOAD_MODE, KEY_RL_LOAD_VALUE,
    KEY_WC_MATERIAL, KEY_WC_DENSITY, KEY_WC_THICKNESS,

    KEY_MP_GIRDER_SYMMETRY, KEY_MP_GIRDER_DEPTH, KEY_MP_GIRDER_WEB_DEPTH, KEY_MP_GIRDER_WEB_THICKNESS,
    KEY_MP_GIRDER_TOP_FLANGE_WIDTH, KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
    KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH, KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
    KEY_MP_GIRDER_SECTIONAL_AREA, KEY_MP_GIRDER_MASS,
    KEY_MP_GIRDER_SECTIONAL_IZ, KEY_MP_GIRDER_SECTIONAL_IY,
    KEY_MP_GIRDER_RADIUS_GYRATION_Z, KEY_MP_GIRDER_RADIUS_GYRATION_Y,
    KEY_MP_GIRDER_ELASTIC_MODULUS_ZZ, KEY_MP_GIRDER_ELASTIC_MODULUS_ZY,
    KEY_MP_GIRDER_PLASTIC_MODULUS_ZUZ, KEY_MP_GIRDER_PLASTIC_MODULUS_ZUY,
    KEY_MP_GIRDER_TORSION_CONSTANT_IT, KEY_MP_GIRDER_WARPING_CONSTANT_IW,

    KEY_MP_STIFFENER_NO_BEARING_STIFFENERS,
    KEY_MP_STIFFENER_SPACING,
    KEY_MP_STIFFENER_BEARING_PLATE_THICKNESS,
    KEY_MP_STIFFENER_BEARING_OUTSTAND,
    KEY_MP_STIFFENER_INTERMEDIATE,
    KEY_MP_STIFFENER_INTERMEDIATE_SPACING,
    KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS,
    KEY_MP_STIFFENER_INTERMEDIATE_OUTSTAND,
    KEY_MP_STIFFENER_LONGITUDINAL,
    KEY_MP_STIFFENER_LONGITUDINAL_THICKNESS,
    KEY_MP_STIFFENER_DESIGN_METHOD,
    
    STIFFENER_DETAILS_DEFAULTS,

    KEY_MP_CB_SELECT_GIRDERS,
    KEY_MP_CB_MEMBER_ID,
    KEY_MP_CB_TYPE,
    KEY_MP_CB_BRACING_SECTION_TYPE,
    KEY_MP_CB_BRACING_SECTION_DESIGNATION,
    KEY_MP_CB_TOP_CHORD,
    KEY_MP_CB_TOP_CHORD_SECTION_TYPE,
    KEY_MP_CB_TOP_CHORD_SECTION_DESIG,
    KEY_MP_CB_BOTTOM_CHORD,
    KEY_MP_CB_BOTTOM_CHORD_SECTION_TYPE,
    KEY_MP_CB_BOTTOM_CHORD_SECTION_DESIG,
    KEY_MP_CB_SPACING,
    CROSS_BRACING_DEFAULTS,
    DEFAULT_CROSS_BRACING_SPACING,

    KEY_MP_ED_SELECT_GIRDERS,
    KEY_MP_ED_MEMBER_ID,
    KEY_MP_ED_TYPE,
    KEY_MP_ED_BRACING_TYPE,
    KEY_MP_ED_BRACING_SECTION,
    KEY_MP_ED_BRACING_SECTION_DESIGNATION,
    KEY_MP_ED_TOP_CHORD_SECTION_TYPE,
    KEY_MP_ED_TOP_CHORD_SECTION_DESIG,
    KEY_MP_ED_BOTTOM_CHORD_SECTION_TYPE,
    KEY_MP_ED_BOTTOM_CHORD_SECTION_DESIG,
    KEY_MP_ED_SPACING,
    VALUES_END_DIAPHRAGM_TYPE,

    KEY_DO_GAMMA_C_BASIC, KEY_DO_GAMMA_C_ACCIDENTAL, KEY_DO_GAMMA_M0, KEY_DO_GAMMA_M1, KEY_DO_GAMMA_S,
    KEY_DO_GAMMA_V, KEY_DO_GAMMA_FLT, KEY_DO_GAMMA_MF, KEY_DO_LOAD_CYCLES, KEY_DO_DEFLECTION_LIMIT,
    KEY_DO_ULS_BENDING, KEY_DO_ULS_SHEAR, KEY_DO_ULS_LTB, KEY_DO_ULS_TRANSVERSE, KEY_DO_ULS_LONG_SHEAR, KEY_DO_ULS_FATIGUE,
    KEY_DO_SLS_STRESS, KEY_DO_SLS_LONG_SHEAR, KEY_DO_SLS_DEFLECTION, KEY_DO_SLS_CRACK_WIDTH,

    KEY_DS_CONSTRUCTION_STAGE, KEY_DS_REINF_BOUNDS, KEY_DS_REINF_MATERIAL, KEY_DS_TOP_CLEAR_COVER, KEY_DS_BOTTOM_CLEAR_COVER,
    KEY_DS_SIDE_CLEAR_COVER, KEY_DS_STUD_YIELD_STRENGTH, KEY_DS_STUD_ULTIMATE_STRENGTH, KEY_DS_STUD_DIAMETER,
    KEY_DS_STUD_HEIGHT, KEY_DS_STUD_COUNT, KEY_DS_STUD_TRANSVERSE_SPACING,

    KEY_SC_LEFT_SUPPORT, KEY_SC_RIGHT_SUPPORT, KEY_SC_BEARING_LENGTH,

    KEY_PL_SELF_WEIGHT_FACTOR, KEY_LL_IRC_CLASS_A, KEY_LL_IRC_70R_WHEELED, KEY_LL_IRC_70R_TRACKED, KEY_LL_IRC_AA_WHEELED,
    KEY_LL_IRC_AA_TRACKED, KEY_LL_IRC_CLASS_SV, KEY_LL_IRC_70R_BOGIE, KEY_LL_IRC_CLASS_FATIGUE, KEY_LL_CUSTOM_VEHICLES,
    KEY_LL_ECCENTRICITY, KEY_LL_FOOTPATH_PRESSURE_MODE, KEY_LL_FOOTPATH_PRESSURE_VALUE, KEY_SL_IMPORTANCE_FACTOR,
    KEY_SL_SOIL_TYPE, KEY_SL_TIME_PERIOD, KEY_SL_DAMPING, KEY_SL_RESPONSE_REDUCTION, KEY_SL_DEAD_LOAD_MODE,
    KEY_SL_DEAD_LOAD_VALUE, KEY_SL_LIVE_LOAD_MODE, KEY_SL_LIVE_LOAD_VALUE, KEY_WL_AVG_EXPOSED_HEIGHT, KEY_WL_TERRAIN_TYPE,
    KEY_WL_SITE_TOPOGRAPHY, KEY_WL_GUST_FACTOR_MODE, KEY_WL_GUST_FACTOR_VALUE, KEY_WL_DRAG_COEFF_MODE, KEY_WL_DRAG_COEFF_VALUE,
    KEY_WL_DRAG_COEFF_LL_MODE, KEY_WL_DRAG_COEFF_LL_VALUE, KEY_WL_LIFT_COEFF_MODE, KEY_WL_LIFT_COEFF_VALUE, KEY_WL_SUPER_AREA_ELEV_MODE, 
    KEY_WL_SUPER_AREA_ELEV_VALUE, KEY_WL_SUPER_AREA_PLAIN_MODE, KEY_WL_SUPER_AREA_PLAIN_VALUE, KEY_WL_EXPOSED_FRONTAL_MODE, 
    KEY_WL_EXPOSED_FRONTAL_VALUE, KEY_WL_WIND_ECC_DECK_MODE, KEY_WL_WIND_ECC_DECK_VALUE, KEY_WL_WIND_LL_ECC_MODE, KEY_WL_WIND_LL_ECC_VALUE,
    KEY_TL_THERMAL_COEFF_STEEL, KEY_TL_THERMAL_COEFF_RCC, KEY_LC_COMBINATIONS,

)
from .initial_sizing import (
    DEFAULT_DECK_OVERHANG_RATIO as IS_DEFAULT_DECK_OVERHANG_RATIO,
    DEFAULT_DECK_THICKNESS as IS_DEFAULT_DECK_THICKNESS_MM,
    DEFAULT_FOOTPATH_WIDTH as IS_DEFAULT_FOOTPATH_WIDTH_M,
)


#--------------Inp-dict-Start--------------
from osdagbridge.core.utils.common import (
    KEY_STRUCTURE_TYPE, KEY_PROJECT_LOCATION, KEY_SPAN, KEY_CARRIAGEWAY_WIDTH, KEY_INCLUDE_MEDIAN,
    KEY_FOOTPATH, KEY_SKEW_ANGLE, KEY_DESIGN_MODE, KEY_GIRDER, KEY_CROSS_BRACING, KEY_END_DIAPHRAGM, KEY_DECK_CONCRETE_GRADE_BASIC,
    connectdb,
)
steel_properties = connectdb("Steel_Grade_Properties")
concrete_properies = connectdb("Concrete_Grade_Properties")

# This is default initial dictionary
BASIC_INPUT_DICT = {

    # Input Dock Defaults
    KEY_STRUCTURE_TYPE: "Highway Bridge",
    KEY_PROJECT_LOCATION: None,  # Required field will be none by default
    KEY_SPAN: None,
    KEY_CARRIAGEWAY_WIDTH: None,
    KEY_INCLUDE_MEDIAN: "No",
    KEY_FOOTPATH: "None",
    KEY_SKEW_ANGLE: None,
    KEY_DESIGN_MODE: "Optimized",
    KEY_GIRDER: steel_properties[12],
    KEY_CROSS_BRACING: steel_properties[12],
    KEY_END_DIAPHRAGM: steel_properties[12],
    KEY_DECK_CONCRETE_GRADE_BASIC: concrete_properies[5],

    # Additional Inputs Defaults
    

}
#--------------Inp-dict-End----------------

def _update_typical_section_defaults(input_dict: dict) -> None:
    """Fill Typical Section tab keys that are None with computed/standard defaults."""
    from osdagbridge.core.utils.codes.keyfile import KEY_FOOTPATH as KF_FOOTPATH
    from osdagbridge.core.bridge_components.super_structure.crash_barrier.geometry import (
        rigid_barrier_no_footpath_area,
    )
    from osdagbridge.core.bridge_components.super_structure.crash_barrier.properties import (
        RCC_DENSITY,
        rigid_barrier_no_footpath_load,
    )

    def _update(key, value):
        input_dict.update({key: value})

    # --- Deck Detail sub-tab ---
    _update(KEY_TS_DECK_THICKNESS,     200.0)                        # mm
    _update(KEY_TS_FOOTPATH_WIDTH,     IS_DEFAULT_FOOTPATH_WIDTH_M)  # m
    _update(KEY_TS_FOOTPATH_THICKNESS, 100.0)                        # mm

    # --- Crash Barrier sub-tab ---
    _cb_dims = IRC5_2015.cl_109_6_3_shapes(
        barrier_type=KEY_CRASH_BARRIER_TYPE[2],
        footpath=KF_FOOTPATH[0],
        railing_type=None,
        design_dict={},
        crash_barrier_type=KEY_RIGID_CRASH_BARRIER_TYPE[0],
    )
    _cb_area = rigid_barrier_no_footpath_area()
    _cb_load = rigid_barrier_no_footpath_load()

    _update(KEY_CB_TYPE,         "IRC 5 - RCC Crash Barrier")
    _update(KEY_CB_DENSITY,      RCC_DENSITY)                          # kN/m³
    _update(KEY_CB_WIDTH,        _cb_dims[KEY_CB_WIDTH]  / 1e3)        # mm → m
    _update(KEY_CB_HEIGHT,       _cb_dims[KEY_CB_HEIGHT] / 1e3)        # mm → m
    _update(KEY_CB_AREA,         _cb_area["barrier_area"])             # mm²
    _update(KEY_CB_LOAD,         _cb_load["total_load_kN_per_m"])      # kN/m
    _update(KEY_CB_POST_SPACING, 2)                                    # m

    # --- Median sub-tab ---
    from osdagbridge.core.bridge_components.super_structure.median.geometry import (
        median_rcc_crash_barrier_area,
    )
    include_median = str(input_dict.get(KEY_INCLUDE_MEDIAN, 'No')).strip().lower()
    if include_median == 'yes':
        _md_geom = IRC5_2015.cl_109_6_3_shapes(
            barrier_type=KEY_MEDIAN_TYPE[1],
            footpath=None,
            railing_type=None,
            design_dict={},
            crash_barrier_type=None,
        )
        _md_area_result = median_rcc_crash_barrier_area()
        _md_area    = _md_area_result["total_area"]              # mm²
        _md_load    = (_md_area / 1e6) * RCC_DENSITY             # kN/m
        _md_height  = (_md_geom["barrier_height"] + _md_geom["kerb_height"]) / 1e3  # mm → m
        _update(KEY_MD_TYPE,         "IRC 5 - RCC Crash Barrier")
        _update(KEY_MD_DENSITY,      RCC_DENSITY)                   # kN/m³
        _update(KEY_MD_WIDTH,        _md_geom[KEY_MD_WIDTH] / 1e3)  # mm → m
        _update(KEY_MD_HEIGHT,       _md_height)                    # m
        _update(KEY_MD_AREA,         _md_area)                      # mm²
        _update(KEY_MD_LOAD,         _md_load)                      # kN/m
        _update(KEY_MD_POST_SPACING, 2)                             # m
    else:
        _update(KEY_MD_TYPE,         None)
        _update(KEY_MD_DENSITY,      None)
        _update(KEY_MD_WIDTH,        0.0)
        _update(KEY_MD_HEIGHT,       None)
        _update(KEY_MD_AREA,         None)
        _update(KEY_MD_LOAD,         None)
        _update(KEY_MD_POST_SPACING, None)

    # --- Railing sub-tab ---
    from osdagbridge.core.bridge_components.super_structure.railing.geometry import (
        railing_dead_load_kN_m,
    )
    _rl_load      = railing_dead_load_kN_m()   # kN/m — IRC 6:2017 Cl.206.5 (150 kg/m)
    _rl_height_m  = 1100 / 1e3                 # m    — IRC 5:2015 Cl.109.7.2.3 minimum

    _update(KEY_RL_TYPE,       "As per IRC 6")
    _update(KEY_RL_WIDTH,      DEFAULT_RAILING_WIDTH)  # m
    _update(KEY_RL_HEIGHT,     _rl_height_m)           # m
    _update(KEY_RL_LOAD_MODE,  "As per IRC 6")
    _update(KEY_RL_LOAD_VALUE, _rl_load)               # kN/m

    # --- Wearing Course sub-tab ---
    # Density and thickness match on_wearing_material_changed() in typical_section_details.py
    _update(KEY_WC_MATERIAL,  "Concrete")  # VALUES_WEARING_COAT_MATERIAL[0]
    _update(KEY_WC_DENSITY,   24.0)        # kN/m³
    _update(KEY_WC_THICKNESS, 50.0)        # mm

def _update_loading_tab_defaults(input_dict: dict) -> None:
    """Fill Loading tab keys that are None with schema defaults."""

    def _update(key, value):
        if input_dict.get(key) is None:
            input_dict[key] = value

    # ── Permanent Load ─────────────────────────────────────────────────────
    _update(KEY_PL_SELF_WEIGHT_FACTOR,      "1.00")

    # ── Live Load ──────────────────────────────────────────────────────────
    _update(KEY_LL_IRC_CLASS_A,             True)
    _update(KEY_LL_IRC_AA_WHEELED,          True)
    _update(KEY_LL_IRC_AA_TRACKED,          True)
    _update(KEY_LL_IRC_70R_WHEELED,         True)
    _update(KEY_LL_IRC_70R_TRACKED,         True)
    _update(KEY_LL_IRC_70R_BOGIE,           True)
    _update(KEY_LL_IRC_CLASS_SV,            True)
    _update(KEY_LL_IRC_CLASS_FATIGUE,       True)
    _update(KEY_LL_CUSTOM_VEHICLES,         [])
    _update(KEY_LL_ECCENTRICITY,            "1.2")
    _update(KEY_LL_FOOTPATH_PRESSURE_MODE,  "As per IRC 6")
    _update(KEY_LL_FOOTPATH_PRESSURE_VALUE, "")

    # ── Seismic Load ───────────────────────────────────────────────────────
    _update(KEY_SL_IMPORTANCE_FACTOR,       "1.0")
    _update(KEY_SL_SOIL_TYPE,               "Type I \u2013 Rocky or Hard")
    _update(KEY_SL_TIME_PERIOD,             "0.5")
    _update(KEY_SL_DAMPING,                 "2")
    _update(KEY_SL_RESPONSE_REDUCTION,      "1")
    _update(KEY_SL_DEAD_LOAD_MODE,          "Automatic")
    _update(KEY_SL_DEAD_LOAD_VALUE,         "")
    _update(KEY_SL_LIVE_LOAD_MODE,          "Automatic")
    _update(KEY_SL_LIVE_LOAD_VALUE,         "")

    # ── Wind Load ──────────────────────────────────────────────────────────
    _update(KEY_WL_AVG_EXPOSED_HEIGHT,      "10")
    _update(KEY_WL_TERRAIN_TYPE,            "Plain Terrain")
    _update(KEY_WL_SITE_TOPOGRAPHY,         "Flat")
    _update(KEY_WL_GUST_FACTOR_MODE,        "As per IRC 6")
    _update(KEY_WL_GUST_FACTOR_VALUE,       "")
    _update(KEY_WL_DRAG_COEFF_MODE,         "As per IRC 6")
    _update(KEY_WL_DRAG_COEFF_VALUE,        "")
    _update(KEY_WL_DRAG_COEFF_LL_MODE,      "As per IRC 6")
    _update(KEY_WL_DRAG_COEFF_LL_VALUE,     "")
    _update(KEY_WL_LIFT_COEFF_MODE,         "As per IRC 6")
    _update(KEY_WL_LIFT_COEFF_VALUE,        "")
    _update(KEY_WL_SUPER_AREA_ELEV_MODE,    "Automatic")
    _update(KEY_WL_SUPER_AREA_ELEV_VALUE,   "")
    _update(KEY_WL_SUPER_AREA_PLAIN_MODE,   "Automatic")
    _update(KEY_WL_SUPER_AREA_PLAIN_VALUE,  "")
    _update(KEY_WL_EXPOSED_FRONTAL_MODE,    "Automatic")
    _update(KEY_WL_EXPOSED_FRONTAL_VALUE,   "")
    _update(KEY_WL_WIND_ECC_DECK_MODE,      "As per IRC 6")
    _update(KEY_WL_WIND_ECC_DECK_VALUE,     "")
    _update(KEY_WL_WIND_LL_ECC_MODE,        "As per IRC 6")
    _update(KEY_WL_WIND_LL_ECC_VALUE,       "")

    # ── Temperature Load ───────────────────────────────────────────────────
    _update(KEY_TL_THERMAL_COEFF_STEEL,     "12.0e-6")
    _update(KEY_TL_THERMAL_COEFF_RCC,       "12.0e-6")

    # ── Load Combination ───────────────────────────────────────────────────
    _update(KEY_LC_COMBINATIONS,            [])

def _update_support_conditions_defaults(input_dict: dict) -> None:
    """Fill Support Conditions tab keys that are None with schema defaults."""
    
    def _update(key, value):
        if input_dict.get(key) is None:
            input_dict.update({key: value})

    _update(KEY_SC_LEFT_SUPPORT,   "Pinned")
    _update(KEY_SC_RIGHT_SUPPORT,  "Roller")
    _update(KEY_SC_BEARING_LENGTH, "400.00")

def _update_design_options_defaults(input_dict: dict) -> None:
    """Fill Design Options tab keys that are None with schema defaults."""
    
    def _update(key, value):
        input_dict.update({key: value})

    _update(KEY_DS_CONSTRUCTION_STAGE,      "Yes")
    _update(KEY_DS_REINF_BOUNDS,            {
                                                "lower":     None,
                                                "upper":     None,
                                            })
    _update(KEY_DS_REINF_MATERIAL,          "Fe 415")
    _update(KEY_DS_TOP_CLEAR_COVER,         "50")
    _update(KEY_DS_BOTTOM_CLEAR_COVER,      "50")
    _update(KEY_DS_SIDE_CLEAR_COVER,        "50")
    _update(KEY_DS_STUD_YIELD_STRENGTH,     "400")
    _update(KEY_DS_STUD_ULTIMATE_STRENGTH,  "400")
    _update(KEY_DS_STUD_DIAMETER,           "16")
    _update(KEY_DS_STUD_HEIGHT,             "10")
    _update(KEY_DS_STUD_COUNT,              "2")
    _update(KEY_DS_STUD_TRANSVERSE_SPACING, "10")

def _update_design_options_cont_defaults(input_dict: dict) -> None:
    """Fill Design Options (Cont.) tab keys that are None with schema defaults."""
    
    def _update(key, value):
        input_dict.update({key: value})

    _update(KEY_DO_GAMMA_C_BASIC,      "1.50")
    _update(KEY_DO_GAMMA_C_ACCIDENTAL, "1.20")
    _update(KEY_DO_GAMMA_M0,           "1.10")
    _update(KEY_DO_GAMMA_M1,           "1.25")
    _update(KEY_DO_GAMMA_S,            "1.15")
    _update(KEY_DO_GAMMA_V,            "1.25")
    _update(KEY_DO_GAMMA_FLT,          "1.00")
    _update(KEY_DO_GAMMA_MF,           "1.35")
    _update(KEY_DO_LOAD_CYCLES,        "2000000")
    _update(KEY_DO_DEFLECTION_LIMIT,   "600.00")
    _update(KEY_DO_ULS_BENDING,        True)
    _update(KEY_DO_ULS_SHEAR,          True)
    _update(KEY_DO_ULS_LTB,            True)
    _update(KEY_DO_ULS_TRANSVERSE,     True)
    _update(KEY_DO_ULS_LONG_SHEAR,     True)
    _update(KEY_DO_ULS_FATIGUE,        True)
    _update(KEY_DO_SLS_STRESS,         True)
    _update(KEY_DO_SLS_LONG_SHEAR,     True)
    _update(KEY_DO_SLS_DEFLECTION,     True)
    _update(KEY_DO_SLS_CRACK_WIDTH,    True)


def _on_no_of_girders_changed(working_input_dict: dict, count: int) -> None:
    from osdagbridge.core.bridge_types.plate_girder.defaults import solve_extend_basic_input_dict

    working_input_dict[KEY_TS_NO_OF_GIRDERS] = count

    try:
        solve_extend_basic_input_dict(working_input_dict)
    except Exception:
        return


def solve_extend_basic_input_dict(basic_input_dict: dict) -> None:
    """Parse basic inputs and solve bridge layout. Updates basic_input_dict in-place."""
    from .initial_sizing import BridgeConfigurationSolver

    def _railing_width_m(value) -> float:
        if value in (None, ""):
            return 0.0
        width = float(value)
        # Railing width is edited in mm in Additional Inputs, while solver uses m.
        return width / 1000.0 if width > 10 else width

    span = float(basic_input_dict.get(KEY_SPAN))
    footpath_str = str(basic_input_dict.get(KEY_FOOTPATH, 'None')).strip()
    design_mode  = str(basic_input_dict.get(KEY_DESIGN_MODE, 'Optimized')).strip()

    # Fill sub-tab defaults before reading any typical-section keys (e.g. footpath width)
    _update_typical_section_defaults(basic_input_dict)

    _update_loading_tab_defaults(basic_input_dict)

    _update_support_conditions_defaults(basic_input_dict)
    
    _update_design_options_defaults(basic_input_dict)
    
    _update_design_options_cont_defaults(basic_input_dict)

    if footpath_str in ('None', ''):
        n_footpaths, footpath_width, railing_width = 0, 0.0, 0.0
    elif 'Both' in footpath_str:
        n_footpaths    = 2
        footpath_width = float(basic_input_dict.get(KEY_TS_FOOTPATH_WIDTH))
        railing_width  = _railing_width_m(basic_input_dict.get(KEY_RL_WIDTH))
    else:
        n_footpaths    = 1
        footpath_width = float(basic_input_dict.get(KEY_TS_FOOTPATH_WIDTH))
        railing_width  = _railing_width_m(basic_input_dict.get(KEY_RL_WIDTH))

    median_width  = basic_input_dict.get(KEY_MD_WIDTH) or 0.0
    no_of_girders = int(basic_input_dict.get(KEY_TS_NO_OF_GIRDERS) or 4)

    solver = BridgeConfigurationSolver(
        carriageway_width=float(basic_input_dict.get(KEY_CARRIAGEWAY_WIDTH)),
        crash_barrier_width=float(basic_input_dict.get(KEY_CB_WIDTH)),
        footpath_width=footpath_width,
        railing_width=railing_width,
        median_width=float(median_width),
        n_footpaths=n_footpaths,
    )
    sizing_result = solver._solve_layout(no_of_girders=no_of_girders, changed_field='girders')

    print("[DEBUG] Bridge Layout Sizing Result:")
    print(f"  overall_width = {sizing_result.overall_width} m")
    print(f"  no_of_girders = {sizing_result.no_of_girders}")
    print(f"  girder_spacing = {sizing_result.girder_spacing} m")
    print(f"  deck_overhang = {sizing_result.deck_overhang} m")

    symmetry = 'Girder Symmetric' if design_mode == 'Optimized' else 'Girder Unsymmetric'
    section_props = solver.compute_section_properties(span=span, symmetry=symmetry)

    basic_input_dict.update({
        KEY_TS_NO_OF_FOOTPATHS: n_footpaths,
        KEY_TS_FOOTPATH_WIDTH:  footpath_width,
        KEY_RL_WIDTH:           railing_width,
        KEY_TS_OVERALL_WIDTH:   sizing_result.overall_width,
        KEY_TS_NO_OF_GIRDERS:   sizing_result.no_of_girders,
        KEY_TS_GIRDER_SPACING:  sizing_result.girder_spacing,
        KEY_TS_DECK_OVERHANG:   sizing_result.deck_overhang,
    })
    # --- Remove all stale dynamic girder keys first (handles girder count change) ---
    # Match on the common prefix of all KEY_MP_GIRDER_* values from common.py
    # which all start with "member_properties.girder_details." and contain "_G"
    stale_keys = [
        k for k in basic_input_dict
        if k.startswith("member_properties.girder_details.") and "_G" in k
    ]
    for k in stale_keys:
        del basic_input_dict[k]

    # --- Mapping: imported constant value (from common.py) → section_props value ---
    # To add a new property in future, just add one line here.
    # The imported constant's string VALUE is used as the base key,
    # e.g. KEY_MP_GIRDER_DEPTH = "member_properties.girder_details.section_input.depth"
    # produces → "member_properties.girder_details.section_input.depth_G1M1"
    MP_GIRDER_PROPS = [
        (KEY_MP_GIRDER_SYMMETRY,                section_props['symmetry']),
        (KEY_MP_GIRDER_DEPTH,                   section_props['D']),
        (KEY_MP_GIRDER_WEB_DEPTH,               section_props['d_web']),
        (KEY_MP_GIRDER_WEB_THICKNESS,           section_props['t_w']),
        (KEY_MP_GIRDER_TOP_FLANGE_WIDTH,        section_props['B_top']),
        (KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,    section_props['t_f_top']),
        (KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH,     section_props['B_bot']),
        (KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS, section_props['t_f_bot']),
        (KEY_MP_GIRDER_SECTIONAL_AREA,          section_props['Area']),
        (KEY_MP_GIRDER_MASS,                    section_props['Mass']),
        (KEY_MP_GIRDER_SECTIONAL_IZ,            section_props['I_z']),
        (KEY_MP_GIRDER_SECTIONAL_IY,            section_props['I_y']),
        (KEY_MP_GIRDER_RADIUS_GYRATION_Z,       section_props['r_z']),
        (KEY_MP_GIRDER_RADIUS_GYRATION_Y,       section_props['r_y']),
        (KEY_MP_GIRDER_ELASTIC_MODULUS_ZZ,      section_props['Z_ez']),
        (KEY_MP_GIRDER_ELASTIC_MODULUS_ZY,      section_props['Z_ey']),
        (KEY_MP_GIRDER_PLASTIC_MODULUS_ZUZ,     section_props['Z_pz']),
        (KEY_MP_GIRDER_PLASTIC_MODULUS_ZUY,     section_props['Z_py']),
        (KEY_MP_GIRDER_TORSION_CONSTANT_IT,     section_props['I_t']),
        (KEY_MP_GIRDER_WARPING_CONSTANT_IW,     section_props['I_w']),
    ]

    # --- Populate dynamic girder keys for each girder and member ---
    # girder_idx : 1 to no_of_girders (driven by user input)
    # member_id  : always 1 for now; extend the list below when multiple members needed
    for girder_idx in range(1, no_of_girders + 1):
        for member_id in [1]:  # extend to [1, 2, 3] for multiple members per girder
            for base_key, value in MP_GIRDER_PROPS:
                dynamic_key = f"{base_key}_G{girder_idx}M{member_id}"
                basic_input_dict[dynamic_key] = value

    # --- Remove all stale dynamic stiffener keys (handles girder count change) ---
    stale_stiffener_keys = [
        k for k in basic_input_dict
        if k.startswith("member_properties.stiffener_details.") and "_G" in k
    ]
    for k in stale_stiffener_keys:
        del basic_input_dict[k]

    MP_STIFFENER_PROPS = [
        (KEY_MP_STIFFENER_NO_BEARING_STIFFENERS,  "bearing_stiffeners_each_end"),
        (KEY_MP_STIFFENER_SPACING,                "bearing_spacing_mm"),
        (KEY_MP_STIFFENER_BEARING_PLATE_THICKNESS,      "bearing_thickness_value"),
        (KEY_MP_STIFFENER_BEARING_OUTSTAND,       "bearing_outstand_mm"),
        (KEY_MP_STIFFENER_INTERMEDIATE,           "intermediate_stiffener"),
        (KEY_MP_STIFFENER_INTERMEDIATE_SPACING,   "intermediate_spacing_mm"),
        (KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS, "intermediate_thickness_value"),
        (KEY_MP_STIFFENER_INTERMEDIATE_OUTSTAND,  "intermediate_outstand_mm"),
        (KEY_MP_STIFFENER_LONGITUDINAL,           "longitudinal_stiffener"),
        (KEY_MP_STIFFENER_LONGITUDINAL_THICKNESS, "longitudinal_thickness_value"),
        (KEY_MP_STIFFENER_DESIGN_METHOD,          "shear_buckling_method"),
    ]

    for girder_idx in range(1, no_of_girders + 1):
        for member_id in [1]:
            for base_key, defaults_key in MP_STIFFENER_PROPS:
                dynamic_key = f"{base_key}_G{girder_idx}M{member_id}"
                basic_input_dict[dynamic_key] = STIFFENER_DETAILS_DEFAULTS[defaults_key]

    # --- Remove all stale dynamic cross bracing keys ---
    stale_cb_keys = [
        k for k in basic_input_dict
        if k.startswith("member_properties.cross_bracing_details.") and "_G" in k
    ]
    for k in stale_cb_keys:
        del basic_input_dict[k]

    # --- Cross Bracing props map: (KEY_MP_CB_* constant, default value) ---
    no_of_members = 9  # B1M1 to B1M9, extend here when needed

    MP_CB_PROPS = [
        (KEY_MP_CB_SELECT_GIRDERS,              "select_girders"),
        (KEY_MP_CB_MEMBER_ID,                   "member_id"),
        (KEY_MP_CB_TYPE,                        "type"),
        (KEY_MP_CB_BRACING_SECTION_TYPE,        "bracing_section_type"),
        (KEY_MP_CB_BRACING_SECTION_DESIGNATION, "bracing_section_designation"),
        (KEY_MP_CB_TOP_CHORD,                   "top_chord"),
        (KEY_MP_CB_TOP_CHORD_SECTION_TYPE,      "top_chord_section_type"),
        (KEY_MP_CB_TOP_CHORD_SECTION_DESIG,     "top_chord_section_desig"),
        (KEY_MP_CB_BOTTOM_CHORD,                "bottom_chord"),
        (KEY_MP_CB_BOTTOM_CHORD_SECTION_TYPE,   "bottom_chord_section_type"),
        (KEY_MP_CB_BOTTOM_CHORD_SECTION_DESIG,  "bottom_chord_section_desig"),
        (KEY_MP_CB_SPACING,                     "spacing"),
    ]

    # --- Populate dynamic cross bracing keys ---
    for girder_idx in range(1, no_of_girders):
        g_pair = f"G{girder_idx}G{girder_idx + 1}"
        for member_id in range(1, no_of_members + 1):
            b_member = f"B1M{member_id}"
            suffix = f"_{g_pair}_{b_member}"
            select_girders_value = f"G{girder_idx} to G{girder_idx + 1}"
            member_id_value      = f"B1M1 to B1M{no_of_members}"
            for base_key, defaults_key in MP_CB_PROPS:
                dynamic_key = f"{base_key}{suffix}"
                if defaults_key == "select_girders":
                    basic_input_dict[dynamic_key] = select_girders_value
                elif defaults_key == "member_id":
                    basic_input_dict[dynamic_key] = member_id_value
                else:
                    basic_input_dict[dynamic_key] = CROSS_BRACING_DEFAULTS[defaults_key]

    # --- Remove all stale dynamic end diaphragm keys ---
    stale_ed_keys = [
        k for k in basic_input_dict
        if k.startswith("member_properties.end_diaphragm_details.") and "_G" in k
    ]
    for k in stale_ed_keys:
        del basic_input_dict[k]

    # --- End Diaphragm props map ---
    no_of_ed_members = 2  # E1M1 and E1M2 per girder pair

    _ED_DEFAULTS = {
        "select_girders":               "",
        "member_id":                    "",
        "type":                         VALUES_END_DIAPHRAGM_TYPE[0],   # "Cross Bracing"
        "bracing_type":                 "",
        "bracing_section":              "",
        "bracing_section_designation":  "",
        "top_chord_section_type":       "",
        "top_chord_section_desig":      "",
        "bottom_chord_section_type":    "",
        "bottom_chord_section_desig":   "",
        "spacing":                      DEFAULT_CROSS_BRACING_SPACING,  # 3.0
    }

    MP_ED_PROPS = [
        (KEY_MP_ED_SELECT_GIRDERS,              "select_girders"),
        (KEY_MP_ED_MEMBER_ID,                   "member_id"),
        (KEY_MP_ED_TYPE,                        "type"),
        (KEY_MP_ED_BRACING_TYPE,                "bracing_type"),
        (KEY_MP_ED_BRACING_SECTION,             "bracing_section"),
        (KEY_MP_ED_BRACING_SECTION_DESIGNATION, "bracing_section_designation"),
        (KEY_MP_ED_TOP_CHORD_SECTION_TYPE,      "top_chord_section_type"),
        (KEY_MP_ED_TOP_CHORD_SECTION_DESIG,     "top_chord_section_desig"),
        (KEY_MP_ED_BOTTOM_CHORD_SECTION_TYPE,   "bottom_chord_section_type"),
        (KEY_MP_ED_BOTTOM_CHORD_SECTION_DESIG,  "bottom_chord_section_desig"),
        (KEY_MP_ED_SPACING,                     "spacing"),
    ]

    # --- Populate dynamic end diaphragm keys ---
    for girder_idx in range(1, no_of_girders):
        g_pair = f"G{girder_idx}G{girder_idx + 1}"
        for member_id in range(1, no_of_ed_members + 1):
            e_member = f"E1M{member_id}"
            suffix = f"_{g_pair}_{e_member}"
            select_girders_value = f"G{girder_idx} to G{girder_idx + 1}"
            member_id_value      = f"E1M1 to E1M{no_of_ed_members}"
            for base_key, defaults_key in MP_ED_PROPS:
                dynamic_key = f"{base_key}{suffix}"
                if defaults_key == "select_girders":
                    basic_input_dict[dynamic_key] = select_girders_value
                elif defaults_key == "member_id":
                    basic_input_dict[dynamic_key] = member_id_value
                else:
                    basic_input_dict[dynamic_key] = _ED_DEFAULTS[defaults_key]
