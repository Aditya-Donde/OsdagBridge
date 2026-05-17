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
    DEFAULT_CONCRETE_DENSITY,
    DEFAULT_CRASH_BARRIER_WIDTH,
    DEFAULT_GIRDER_SPACING,
    DEFAULT_RAILING_WIDTH,
    KEY_TS_GIRDER_SPACING, KEY_TS_NO_OF_GIRDERS, KEY_TS_DECK_OVERHANG, KEY_TS_OVERALL_WIDTH,
    KEY_TS_NO_OF_FOOTPATHS, KEY_TS_DECK_THICKNESS, KEY_TS_FOOTPATH_WIDTH, KEY_TS_FOOTPATH_THICKNESS,
    KEY_CB_TYPE, KEY_CB_DENSITY, KEY_CB_WIDTH, KEY_CB_HEIGHT, KEY_CB_AREA, KEY_CB_LOAD, KEY_CB_POST_SPACING,
    KEY_MD_TYPE, KEY_MD_DENSITY, KEY_MD_WIDTH, KEY_MD_HEIGHT, KEY_MD_AREA, KEY_MD_LOAD, KEY_MD_POST_SPACING,
    KEY_RL_TYPE, KEY_RL_WIDTH, KEY_RL_HEIGHT, KEY_RL_LOAD_MODE, KEY_RL_LOAD_VALUE,
    KEY_WC_MATERIAL, KEY_WC_DENSITY, KEY_WC_THICKNESS,
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
    KEY_GIRDER: steel_properties[0],
    KEY_CROSS_BRACING: steel_properties[0],
    KEY_END_DIAPHRAGM: steel_properties[0],
    KEY_DECK_CONCRETE_GRADE_BASIC: concrete_properies[0],

    # Additional Inputs Defaults
    

}
#--------------Inp-dict-End----------------


def extend_basic_input_dict(basic_input_dict: dict) -> None:
    """
    Returns the combined default dict of Input Dock && Additonal Inputs.
    Some additional input defaults are dependant on input dictionary values, 
        so this function is useful
    """
    additonal_inputs_defaults = {}

    # Primary Typical section Fields
    additonal_inputs_defaults[KEY_TS_GIRDER_SPACING] = None
    additonal_inputs_defaults[KEY_TS_NO_OF_GIRDERS] = None
    additonal_inputs_defaults[KEY_TS_DECK_OVERHANG] = None
    additonal_inputs_defaults[KEY_TS_OVERALL_WIDTH] = None

    # Typical Section (tab) -> Deck Detail (sub-tab)
    additonal_inputs_defaults[KEY_TS_DECK_THICKNESS] = None
    additonal_inputs_defaults[KEY_TS_FOOTPATH_WIDTH] = None
    additonal_inputs_defaults[KEY_TS_FOOTPATH_THICKNESS] = None

    # Typical Section (tab) -> Crash Barrier (sub-tab)
    additonal_inputs_defaults[KEY_CB_TYPE] = None
    additonal_inputs_defaults[KEY_CB_DENSITY] = None
    additonal_inputs_defaults[KEY_CB_WIDTH] = None
    additonal_inputs_defaults[KEY_CB_HEIGHT] = None
    additonal_inputs_defaults[KEY_CB_AREA] = None
    additonal_inputs_defaults[KEY_CB_LOAD] = None
    additonal_inputs_defaults[KEY_CB_POST_SPACING] = None

    # Typical Section (tab) -> Median (sub-tab)
    additonal_inputs_defaults[KEY_MD_TYPE] = None
    additonal_inputs_defaults[KEY_MD_DENSITY] = None
    additonal_inputs_defaults[KEY_MD_WIDTH] = None
    additonal_inputs_defaults[KEY_MD_HEIGHT] = None
    additonal_inputs_defaults[KEY_MD_AREA] = None
    additonal_inputs_defaults[KEY_MD_LOAD] = None
    additonal_inputs_defaults[KEY_MD_POST_SPACING] = None

    # Typical Section (tab) -> Railing (sub-tab)
    additonal_inputs_defaults[KEY_RL_TYPE] = None
    additonal_inputs_defaults[KEY_RL_WIDTH] = None
    additonal_inputs_defaults[KEY_RL_HEIGHT] = None
    additonal_inputs_defaults[KEY_RL_LOAD_MODE] = None
    additonal_inputs_defaults[KEY_RL_LOAD_VALUE] = None

    # Typical Section (tab) -> Wearing Course (sub-tab)
    additonal_inputs_defaults[KEY_WC_MATERIAL] = None
    additonal_inputs_defaults[KEY_WC_DENSITY] = None
    additonal_inputs_defaults[KEY_WC_THICKNESS] = None

    # Typical Section (tab) -> Wearing Course (sub-tab)

    # Typical Section (tab) -> Lane Details (sub-tab)
        
    basic_input_dict.update(additonal_inputs_defaults)


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

    def _set(key, value):
        if input_dict.get(key) is None:
            input_dict[key] = value

    # --- Deck Detail sub-tab ---
    _set(KEY_TS_DECK_THICKNESS,     200.0)
    _set(KEY_TS_FOOTPATH_WIDTH,     1500.0)
    _set(KEY_TS_FOOTPATH_THICKNESS, 100.0)

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

    _set(KEY_CB_TYPE,         "IRC 5 - RCC Crash Barrier")
    _set(KEY_CB_DENSITY,      RCC_DENSITY)                          # kN/m³
    _set(KEY_CB_WIDTH,        _cb_dims[KEY_CB_WIDTH]  / 1e3)        # mm → m
    _set(KEY_CB_HEIGHT,       _cb_dims[KEY_CB_HEIGHT] / 1e3)        # mm → m
    _set(KEY_CB_AREA,         _cb_area["barrier_area"])             # mm²
    _set(KEY_CB_LOAD,         _cb_load["total_load_kN_per_m"])      # kN/m
    _set(KEY_CB_POST_SPACING, 2)                                     # m

    # --- Median sub-tab ---
    _set(KEY_MD_TYPE,         None)   # TODO
    _set(KEY_MD_DENSITY,      None)   # TODO
    _set(KEY_MD_HEIGHT,       None)   # TODO
    _set(KEY_MD_AREA,         None)   # TODO
    _set(KEY_MD_LOAD,         None)   # TODO
    _set(KEY_MD_POST_SPACING, None)   # TODO
    # KEY_MD_WIDTH already resolved by solve_bridge_layout — not touched here

    # --- Railing sub-tab ---
    _set(KEY_RL_TYPE,       None)   # TODO
    _set(KEY_RL_HEIGHT,     None)   # TODO
    _set(KEY_RL_LOAD_MODE,  None)   # TODO
    _set(KEY_RL_LOAD_VALUE, None)   # TODO
    _set(KEY_RL_WIDTH, DEFAULT_RAILING_WIDTH)

    # --- Wearing Course sub-tab ---
    _set(KEY_WC_MATERIAL,  None)   # TODO
    _set(KEY_WC_DENSITY,   None)   # TODO
    _set(KEY_WC_THICKNESS, None)   # TODO


def solve_bridge_layout(basic_input_dict: dict) -> None:
    """Parse basic inputs and solve bridge layout. Updates basic_input_dict in-place."""
    from .initial_sizing import BridgeConfigurationSolver

    span = float(basic_input_dict.get(KEY_SPAN))
    footpath_str = str(basic_input_dict.get(KEY_FOOTPATH, 'None')).strip()
    design_mode  = str(basic_input_dict.get(KEY_DESIGN_MODE, 'Optimized')).strip()

    # Fill sub-tab defaults before reading any typical-section keys (e.g. footpath width)
    _update_typical_section_defaults(basic_input_dict)

    if footpath_str in ('None', ''):
        n_footpaths, footpath_width, railing_width = 0, 0.0, 0.0
    elif 'Both' in footpath_str:
        n_footpaths    = 2
        footpath_width = float(basic_input_dict.get(KEY_TS_FOOTPATH_WIDTH))
        railing_width  = float(basic_input_dict.get(KEY_RL_WIDTH))
    else:
        n_footpaths    = 1
        footpath_width = float(basic_input_dict.get(KEY_TS_FOOTPATH_WIDTH))
        railing_width  = float(basic_input_dict.get(KEY_RL_WIDTH))

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
        'section_props':        section_props,
    })

    print(f"[DEBUG] Basic Input Dictionary: {basic_input_dict}")