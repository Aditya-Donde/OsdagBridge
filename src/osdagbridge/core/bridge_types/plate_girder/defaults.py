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
    KEY_GIRDER_SYMMETRY, KEY_GIRDER_DEPTH, KEY_GIRDER_WEB_DEPTH, KEY_GIRDER_WEB_THICKNESS,
    KEY_GIRDER_TOP_FLANGE_WIDTH, KEY_GIRDER_TOP_FLANGE_THICKNESS,
    KEY_GIRDER_BOTTOM_FLANGE_WIDTH, KEY_GIRDER_BOTTOM_FLANGE_THICKNESS,
    KEY_GIRDER_SECTIONAL_AREA, KEY_GIRDER_MASS,
    KEY_GIRDER_SECTIONAL_IZ, KEY_GIRDER_SECTIONAL_IY,
    KEY_GIRDER_RADIUS_GYRATION_Z, KEY_GIRDER_RADIUS_GYRATION_Y,
    KEY_GIRDER_ELASTIC_MODULUS_ZZ, KEY_GIRDER_ELASTIC_MODULUS_ZY,
    KEY_GIRDER_PLASTIC_MODULUS_ZUZ, KEY_GIRDER_PLASTIC_MODULUS_ZUY,
    KEY_GIRDER_TORSION_CONSTANT_IT, KEY_GIRDER_WARPING_CONSTANT_IW,

    KEY_DO_GAMMA_C_BASIC, KEY_DO_GAMMA_C_ACCIDENTAL, KEY_DO_GAMMA_M0, KEY_DO_GAMMA_M1, KEY_DO_GAMMA_S,
    KEY_DO_GAMMA_V, KEY_DO_GAMMA_FLT, KEY_DO_GAMMA_MF, KEY_DO_LOAD_CYCLES, KEY_DO_DEFLECTION_LIMIT,
    KEY_DO_ULS_BENDING, KEY_DO_ULS_SHEAR, KEY_DO_ULS_LTB, KEY_DO_ULS_TRANSVERSE, KEY_DO_ULS_LONG_SHEAR, KEY_DO_ULS_FATIGUE,
    KEY_DO_SLS_STRESS, KEY_DO_SLS_LONG_SHEAR, KEY_DO_SLS_DEFLECTION, KEY_DO_SLS_CRACK_WIDTH,

    KEY_DS_CONSTRUCTION_STAGE, KEY_DS_REINF_BOUNDS, KEY_DS_REINF_MATERIAL, KEY_DS_TOP_CLEAR_COVER, KEY_DS_BOTTOM_CLEAR_COVER,
    KEY_DS_SIDE_CLEAR_COVER, KEY_DS_STUD_YIELD_STRENGTH, KEY_DS_STUD_ULTIMATE_STRENGTH, KEY_DS_STUD_DIAMETER,
    KEY_DS_STUD_HEIGHT, KEY_DS_STUD_COUNT, KEY_DS_STUD_TRANSVERSE_SPACING,

    KEY_SC_LEFT_SUPPORT, KEY_SC_RIGHT_SUPPORT, KEY_SC_BEARING_LENGTH,

    KEY_LC_COMBINATIONS, KEY_LL_CUSTOM_VEHICLES,


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
    KEY_PROJECT_LOCATION: None, # Required field will be none by default
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

    _update(KEY_RL_TYPE,       "IRC 5 - RCC Railing")
    _update(KEY_RL_WIDTH,      DEFAULT_RAILING_WIDTH)  # m
    _update(KEY_RL_HEIGHT,     _rl_height_m)           # m
    _update(KEY_RL_LOAD_MODE,  "As per IRC 6")
    _update(KEY_RL_LOAD_VALUE, _rl_load)               # kN/m

    # --- Wearing Course sub-tab ---
    # Density and thickness match on_wearing_material_changed() in typical_section_details.py
    _update(KEY_WC_MATERIAL,  "Concrete")  # VALUES_WEARING_COAT_MATERIAL[0]
    _update(KEY_WC_DENSITY,   24.0)        # kN/m³
    _update(KEY_WC_THICKNESS, 50.0)        # mm

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
    _update(KEY_DO_LOAD_CYCLES,        "2000000.00")
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

    # Temporary
    _update(KEY_LC_COMBINATIONS, [])
    _update(KEY_LL_CUSTOM_VEHICLES, [])


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
        KEY_GIRDER_SYMMETRY:                section_props['symmetry'],
        KEY_GIRDER_DEPTH:                   section_props['D'],
        KEY_GIRDER_WEB_DEPTH:               section_props['d_web'],
        KEY_GIRDER_WEB_THICKNESS:           section_props['t_w'],
        KEY_GIRDER_TOP_FLANGE_WIDTH:        section_props['B_top'],
        KEY_GIRDER_TOP_FLANGE_THICKNESS:    section_props['t_f_top'],
        KEY_GIRDER_BOTTOM_FLANGE_WIDTH:     section_props['B_bot'],
        KEY_GIRDER_BOTTOM_FLANGE_THICKNESS: section_props['t_f_bot'],
        KEY_GIRDER_SECTIONAL_AREA:          section_props['Area'],
        KEY_GIRDER_MASS:                    section_props['Mass'],
        KEY_GIRDER_SECTIONAL_IZ:            section_props['I_z'],
        KEY_GIRDER_SECTIONAL_IY:            section_props['I_y'],
        KEY_GIRDER_RADIUS_GYRATION_Z:       section_props['r_z'],
        KEY_GIRDER_RADIUS_GYRATION_Y:       section_props['r_y'],
        KEY_GIRDER_ELASTIC_MODULUS_ZZ:      section_props['Z_ez'],
        KEY_GIRDER_ELASTIC_MODULUS_ZY:      section_props['Z_ey'],
        KEY_GIRDER_PLASTIC_MODULUS_ZUZ:     section_props['Z_pz'],
        KEY_GIRDER_PLASTIC_MODULUS_ZUY:     section_props['Z_py'],
        KEY_GIRDER_TORSION_CONSTANT_IT:     section_props['I_t'],
        KEY_GIRDER_WARPING_CONSTANT_IW:     section_props['I_w'],
    })