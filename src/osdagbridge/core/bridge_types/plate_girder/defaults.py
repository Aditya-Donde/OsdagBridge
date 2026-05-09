"""Centralized defaults for Plate Girder Bridge."""

from __future__ import annotations

from copy import deepcopy

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
    KEY_TS_DECK_THICKNESS, KEY_TS_FOOTPATH_WIDTH, KEY_TS_FOOTPATH_THICKNESS,
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

# Workflow/runtime defaults used by plategirderbridge.py
DEFAULT_STRUCTURE_NAME = "plate_girder_bridge"
DEFAULT_MEDIAN_WIDTH_M = 0.0
DEFAULT_FALLBACK_MEDIAN_WIDTH_M = 1.2   # used when user enables median but supplies no width
DEFAULT_NO_OF_GIRDERS   = 4
DEFAULT_DECK_THICKNESS_MM = float(IS_DEFAULT_DECK_THICKNESS_MM)
DEFAULT_GIRDER_SYMMETRY = "Girder Symmetric"
DEFAULT_SKEW_ANGLE_DEG = 0.0
DEFAULT_GEOMETRY_TOLERANCE = 1e-3

# CAD defaults used by cad_generator.py
DEFAULT_CAD_CHAMFER_LENGTH_MM = 40
DEFAULT_IRC_RIGID_BARRIER_BASE_WIDTH_MM = 450
DEFAULT_IRC_METALLIC_BARRIER_BASE_WIDTH_MM = 550
DEFAULT_STEEL_RAILING_WIDTH_MM = 200
DEFAULT_RCC_RAILING_WIDTH_MM = 275

DEFAULT_CAD_SPAN_LENGTH_L = 25000
DEFAULT_CAD_GIRDER_SECTION_D = 900
DEFAULT_CAD_GIRDER_SECTION_BF = 500
DEFAULT_CAD_GIRDER_SECTION_BF_B = 500
DEFAULT_CAD_GIRDER_SECTION_TF = 260
DEFAULT_CAD_GIRDER_SECTION_TF_B = 260
DEFAULT_CAD_GIRDER_SECTION_TW = 100
DEFAULT_CAD_NUM_GIRDERS = 5
DEFAULT_CAD_GIRDER_SPACING = 2750
DEFAULT_CAD_SKEW_ANGLE = 0

DEFAULT_CAD_CARRIAGEWAY_WIDTH = 12000
DEFAULT_CAD_DECK_THICKNESS = 400
DEFAULT_CAD_FOOTPATH_CONFIG = "BOTH"
DEFAULT_CAD_FOOTPATH_WIDTH = 1500
DEFAULT_CAD_RAILING_WIDTH = 300

DEFAULT_CAD_BARRIER_TYPE = "Semi-Rigid"
DEFAULT_CAD_CRASH_BARRIER_SUBTYPE = "Double W-beam"
DEFAULT_CAD_ENABLE_MEDIAN = True
DEFAULT_CAD_MEDIAN_TYPE = "Metallic Crash Barrier"
DEFAULT_CAD_RAIL_COUNT = 3
DEFAULT_CAD_RAILING_TYPE = "rcc"

DEFAULT_CAD_INCLUDE_INTERMEDIATE_STIFFENERS = True
DEFAULT_CAD_INTERMEDIATE_STIFFENER_SPACING = 2000
DEFAULT_CAD_INTERMEDIATE_STIFFENER_THICKNESS = 20
DEFAULT_CAD_INTERMEDIATE_STIFFENER_OUTSTAND = None
DEFAULT_CAD_NUM_END_STIFFENER_PAIRS = 4
DEFAULT_CAD_END_STIFFENER_THICKNESS = 30
DEFAULT_CAD_END_STIFFENER_OUTSTAND = None
DEFAULT_CAD_INCLUDE_LONGITUDINAL_STIFFENERS = True
DEFAULT_CAD_NUM_LONGITUDINAL_STIFFENERS = 2
DEFAULT_CAD_LONGITUDINAL_STIFFENER_THICKNESS = 20
DEFAULT_CAD_LONGITUDINAL_STIFFENER_OUTSTAND = None

DEFAULT_CAD_CROSS_BRACING_SPACING = 4000
DEFAULT_CAD_BRACING_TYPE = "X"
DEFAULT_CAD_X_BRACKET_OPTION = "BOTH"
DEFAULT_CAD_K_TOP_BRACKET = True
DEFAULT_CAD_DIAGONAL_SECTION_TYPE = "ANGLE"
DEFAULT_CAD_DIAGONAL_SECTION_LEG_H = 100
DEFAULT_CAD_DIAGONAL_SECTION_LEG_W = 50
DEFAULT_CAD_DIAGONAL_SECTION_CONNECTION_TYPE = "LONGER_LEG"
DEFAULT_CAD_DIAGONAL_THICKNESS = 5

DEFAULT_CAD_TOP_CHORD_SECTION_TYPE = "DOUBLE_CHANNEL"
DEFAULT_CAD_TOP_CHORD_SECTION_LEG_H = 80
DEFAULT_CAD_TOP_CHORD_SECTION_LEG_W = 40
DEFAULT_CAD_TOP_CHORD_SECTION_CONNECTION_TYPE = "LONGER_LEG"
DEFAULT_CAD_TOP_CHORD_THICKNESS = 5

DEFAULT_CAD_BOTTOM_CHORD_SECTION_TYPE = "ANGLE"
DEFAULT_CAD_BOTTOM_CHORD_SECTION_LEG_H = 80
DEFAULT_CAD_BOTTOM_CHORD_SECTION_LEG_W = 40
DEFAULT_CAD_BOTTOM_CHORD_SECTION_CONNECTION_TYPE = "LONGER_LEG"
DEFAULT_CAD_BOTTOM_CHORD_THICKNESS = 5

DEFAULT_CAD_END_DIAPHRAGM_TYPE = "Cross Bracing"
DEFAULT_CAD_END_DIAPHRAGM_SPACING = 100
DEFAULT_CAD_END_DIAPHRAGM_BRACING_TYPE = "K"
DEFAULT_CAD_END_DIAPHRAGM_DIAGONAL_SECTION_TYPE = "ANGLE"
DEFAULT_CAD_END_DIAPHRAGM_DIAGONAL_SECTION_LEG_H = 100
DEFAULT_CAD_END_DIAPHRAGM_DIAGONAL_SECTION_LEG_W = 50
DEFAULT_CAD_END_DIAPHRAGM_DIAGONAL_SECTION_CONNECTION_TYPE = "LONGER_LEG"
DEFAULT_CAD_END_DIAPHRAGM_DIAGONAL_THICKNESS = 5

DEFAULT_CAD_END_DIAPHRAGM_TOP_CHORD_SECTION_TYPE = "CHANNEL"
DEFAULT_CAD_END_DIAPHRAGM_TOP_CHORD_SECTION_LEG_H = 80
DEFAULT_CAD_END_DIAPHRAGM_TOP_CHORD_SECTION_LEG_W = 40
DEFAULT_CAD_END_DIAPHRAGM_TOP_CHORD_SECTION_CONNECTION_TYPE = "LONGER_LEG"
DEFAULT_CAD_END_DIAPHRAGM_TOP_CHORD_THICKNESS = 5

DEFAULT_CAD_END_DIAPHRAGM_BOTTOM_CHORD_SECTION_TYPE = "ANGLE"
DEFAULT_CAD_END_DIAPHRAGM_BOTTOM_CHORD_SECTION_LEG_H = 80
DEFAULT_CAD_END_DIAPHRAGM_BOTTOM_CHORD_SECTION_LEG_W = 40
DEFAULT_CAD_END_DIAPHRAGM_BOTTOM_CHORD_SECTION_CONNECTION_TYPE = "LONGER_LEG"
DEFAULT_CAD_END_DIAPHRAGM_BOTTOM_CHORD_THICKNESS = 5

DEFAULT_CAD_END_DIAPHRAGM_SECTION = "I_SECTION"
DEFAULT_CAD_END_DIAPHRAGM_DEPTH = 800
DEFAULT_CAD_END_DIAPHRAGM_FLANGE_WIDTH = 250
DEFAULT_CAD_END_DIAPHRAGM_WEB_THICKNESS = 12
DEFAULT_CAD_END_DIAPHRAGM_FLANGE_THICKNESS = 100

# Dictionary-driven Additional-input defaults used by ui_fields_additional_input.py.
# Layout values are sourced from initial_sizing.py to keep UI/backend in sync.
AI_LAYOUT_DEFAULTS = {
    "girder_spacing_m": float(DEFAULT_GIRDER_SPACING),
    "no_of_girders": int(DEFAULT_NO_OF_GIRDERS),
    "deck_overhang_ratio": float(IS_DEFAULT_DECK_OVERHANG_RATIO),
    "deck_overhang_m": round(float(DEFAULT_GIRDER_SPACING) * float(IS_DEFAULT_DECK_OVERHANG_RATIO), 3),
    "deck_thickness_mm": float(IS_DEFAULT_DECK_THICKNESS_MM),
    "footpath_width_m": float(IS_DEFAULT_FOOTPATH_WIDTH_M),
    "footpath_thickness_mm": float(IS_DEFAULT_DECK_THICKNESS_MM),
}

AI_DEFAULTS: dict[str, dict[str, object]] = {
    "layout": deepcopy(AI_LAYOUT_DEFAULTS),
    "crash_barrier": {
        "width_m": float(DEFAULT_CRASH_BARRIER_WIDTH),
        "post_spacing_m": "1",
    },
    "median": {
        "post_spacing_m": "1",
    },
    "railing": {
        "width_mm": f"{DEFAULT_RAILING_WIDTH * 1000:.0f}",
    },
    "wearing_course": {
        "density_kn_per_m3": "24.0",
        "thickness_mm": "50",
    },
    "permanent_load": {
        "include_self_weight": "Yes",
        "self_weight_factor": "1.00",
        "include_deck_weight": "Yes",
        "include_wearing_course": "Yes",
        "include_crash_barrier": "Yes",
        "include_median": "Yes",
        "include_railing": "Yes",
    },
    "live_load": {
        "irc_vehicles_checked": True,
        "braking_vehicles_checked": True,
        "eccentricity_m": "0.00",
        "footpath_mode": "Automatic",
        "footpath_pressure_kn_per_mm2": "5.00",
    },
    "seismic_load": {
        "zone": "II",
        "importance_factor": "1.0",
        "soil_type": "Type I – Rocky or Hard Soil",
        "damping_percent": "2",
        "response_reduction_factor": "1",
        "dead_load_mode": "Automatic",
        "live_load_mode": "Automatic",
    },
    "wind_load": {
        "avg_exposed_height_m": "10",
        "terrain_type": "Plain Terrain",
        "site_topography": "Flat",
        "gust_factor_mode": "Automatic",
        "gust_factor": "2",
        "drag_coeff_mode": "Automatic",
        "drag_coeff_ll_mode": "Automatic",
        "drag_coeff_ll": "1.2",
        "lift_coeff_mode": "Automatic",
        "lift_coeff": "0.75",
        "super_area_elev_mode": "Automatic",
        "super_area_plain_mode": "Automatic",
        "exposed_frontal_area_mode": "Automatic",
        "ecc_deck_mode": "Automatic",
        "ll_ecc_mode": "Automatic",
    },
    "temperature_load": {
        "thermal_coeff_steel_per_c": "12.0e-6",
        "thermal_coeff_rcc_per_c": "12.0e-6",
    },
    "support_conditions": {
        "left": "Fixed",
        "right": "Pinned",
        "bearing_length": "0",
    },
    "design_options": {
        "construction_stage": "Yes",
        "reinforcement_size": "12 mm",
        "reinforcement_material": "Fe 500",
    },
    "girder_details": {
        "depth_mode": "Optimized",
        "top_flange_width_mode": "Optimized",
        "top_flange_thickness_mode": "All",
        "bottom_flange_width_mode": "Optimized",
        "bottom_flange_thickness_mode": "All",
        "web_thickness_mode": "All",
    },
}


def get_ai_defaults(section: str | None = None) -> dict[str, object] | dict[str, dict[str, object]]:
    """Return dictionary-based Additional Inputs defaults."""
    if section is None:
        return deepcopy(AI_DEFAULTS)
    return deepcopy(AI_DEFAULTS.get(section, {}))


# Compatibility aliases consumed across UI/CAD modules.
DEFAULT_AI_LAYOUT_GIRDER_SPACING_M = AI_DEFAULTS["layout"]["girder_spacing_m"]
DEFAULT_AI_LAYOUT_NO_OF_GIRDERS = AI_DEFAULTS["layout"]["no_of_girders"]
DEFAULT_AI_LAYOUT_DECK_OVERHANG_RATIO = AI_DEFAULTS["layout"]["deck_overhang_ratio"]
DEFAULT_AI_LAYOUT_DECK_OVERHANG_M = AI_DEFAULTS["layout"]["deck_overhang_m"]
DEFAULT_AI_LAYOUT_DECK_THICKNESS_MM = f"{AI_DEFAULTS['layout']['deck_thickness_mm']:.0f}"
DEFAULT_AI_LAYOUT_FOOTPATH_WIDTH_M = f"{AI_DEFAULTS['layout']['footpath_width_m']:.2f}"
DEFAULT_AI_LAYOUT_FOOTPATH_THICKNESS_MM = f"{AI_DEFAULTS['layout']['footpath_thickness_mm']:.0f}"

DEFAULT_AI_CRASH_BARRIER_WIDTH_M = AI_DEFAULTS["crash_barrier"]["width_m"]
DEFAULT_AI_CRASH_BARRIER_POST_SPACING_M = AI_DEFAULTS["crash_barrier"]["post_spacing_m"]
DEFAULT_AI_MEDIAN_POST_SPACING_M = AI_DEFAULTS["median"]["post_spacing_m"]
DEFAULT_AI_RAILING_WIDTH_MM = AI_DEFAULTS["railing"]["width_mm"]

DEFAULT_AI_WEARING_DENSITY_KN_PER_M3 = AI_DEFAULTS["wearing_course"]["density_kn_per_m3"]
DEFAULT_AI_WEARING_THICKNESS_MM = AI_DEFAULTS["wearing_course"]["thickness_mm"]

DEFAULT_AI_PERM_INCLUDE_SELF_WEIGHT = AI_DEFAULTS["permanent_load"]["include_self_weight"]
DEFAULT_AI_PERM_SELF_WEIGHT_FACTOR = AI_DEFAULTS["permanent_load"]["self_weight_factor"]
DEFAULT_AI_PERM_INCLUDE_DECK_WEIGHT = AI_DEFAULTS["permanent_load"]["include_deck_weight"]
DEFAULT_AI_PERM_INCLUDE_WEARING_COURSE = AI_DEFAULTS["permanent_load"]["include_wearing_course"]
DEFAULT_AI_PERM_INCLUDE_CRASH_BARRIER = AI_DEFAULTS["permanent_load"]["include_crash_barrier"]
DEFAULT_AI_PERM_INCLUDE_MEDIAN = AI_DEFAULTS["permanent_load"]["include_median"]
DEFAULT_AI_PERM_INCLUDE_RAILING = AI_DEFAULTS["permanent_load"]["include_railing"]

DEFAULT_AI_LIVE_IRC_VEHICLES_CHECKED = AI_DEFAULTS["live_load"]["irc_vehicles_checked"]
DEFAULT_AI_LIVE_BRAKING_VEHICLES_CHECKED = AI_DEFAULTS["live_load"]["braking_vehicles_checked"]
DEFAULT_AI_LIVE_ECCENTRICITY_M = AI_DEFAULTS["live_load"]["eccentricity_m"]
DEFAULT_AI_LIVE_FOOTPATH_MODE = AI_DEFAULTS["live_load"]["footpath_mode"]
DEFAULT_AI_LIVE_FOOTPATH_PRESSURE_KN_PER_MM2 = AI_DEFAULTS["live_load"]["footpath_pressure_kn_per_mm2"]

DEFAULT_AI_SEISMIC_ZONE = AI_DEFAULTS["seismic_load"]["zone"]
DEFAULT_AI_SEISMIC_IMPORTANCE_FACTOR = AI_DEFAULTS["seismic_load"]["importance_factor"]
DEFAULT_AI_SEISMIC_SOIL_TYPE = AI_DEFAULTS["seismic_load"]["soil_type"]
DEFAULT_AI_SEISMIC_DAMPING_PERCENT = AI_DEFAULTS["seismic_load"]["damping_percent"]
DEFAULT_AI_SEISMIC_RESPONSE_REDUCTION_FACTOR = AI_DEFAULTS["seismic_load"]["response_reduction_factor"]
DEFAULT_AI_SEISMIC_DEAD_LOAD_MODE = AI_DEFAULTS["seismic_load"]["dead_load_mode"]
DEFAULT_AI_SEISMIC_LIVE_LOAD_MODE = AI_DEFAULTS["seismic_load"]["live_load_mode"]

DEFAULT_AI_WIND_AVG_EXPOSED_HEIGHT_M = AI_DEFAULTS["wind_load"]["avg_exposed_height_m"]
DEFAULT_AI_WIND_TERRAIN_TYPE = AI_DEFAULTS["wind_load"]["terrain_type"]
DEFAULT_AI_WIND_SITE_TOPOGRAPHY = AI_DEFAULTS["wind_load"]["site_topography"]
DEFAULT_AI_WIND_GUST_FACTOR_MODE = AI_DEFAULTS["wind_load"]["gust_factor_mode"]
DEFAULT_AI_WIND_GUST_FACTOR = AI_DEFAULTS["wind_load"]["gust_factor"]
DEFAULT_AI_WIND_DRAG_COEFF_MODE = AI_DEFAULTS["wind_load"]["drag_coeff_mode"]
DEFAULT_AI_WIND_DRAG_COEFF_LL_MODE = AI_DEFAULTS["wind_load"]["drag_coeff_ll_mode"]
DEFAULT_AI_WIND_DRAG_COEFF_LL = AI_DEFAULTS["wind_load"]["drag_coeff_ll"]
DEFAULT_AI_WIND_LIFT_COEFF_MODE = AI_DEFAULTS["wind_load"]["lift_coeff_mode"]
DEFAULT_AI_WIND_LIFT_COEFF = AI_DEFAULTS["wind_load"]["lift_coeff"]
DEFAULT_AI_WIND_SUPER_AREA_ELEV_MODE = AI_DEFAULTS["wind_load"]["super_area_elev_mode"]
DEFAULT_AI_WIND_SUPER_AREA_PLAIN_MODE = AI_DEFAULTS["wind_load"]["super_area_plain_mode"]
DEFAULT_AI_WIND_EXPOSED_FRONTAL_AREA_MODE = AI_DEFAULTS["wind_load"]["exposed_frontal_area_mode"]
DEFAULT_AI_WIND_ECC_DECK_MODE = AI_DEFAULTS["wind_load"]["ecc_deck_mode"]
DEFAULT_AI_WIND_LL_ECC_MODE = AI_DEFAULTS["wind_load"]["ll_ecc_mode"]

DEFAULT_AI_TEMP_THERMAL_COEFF_STEEL_PER_C = AI_DEFAULTS["temperature_load"]["thermal_coeff_steel_per_c"]
DEFAULT_AI_TEMP_THERMAL_COEFF_RCC_PER_C = AI_DEFAULTS["temperature_load"]["thermal_coeff_rcc_per_c"]

DEFAULT_AI_SUPPORT_LEFT = AI_DEFAULTS["support_conditions"]["left"]
DEFAULT_AI_SUPPORT_RIGHT = AI_DEFAULTS["support_conditions"]["right"]
DEFAULT_AI_SUPPORT_BEARING_LENGTH = AI_DEFAULTS["support_conditions"]["bearing_length"]

DEFAULT_AI_DESIGN_CONSTRUCTION_STAGE = AI_DEFAULTS["design_options"]["construction_stage"]
DEFAULT_AI_DESIGN_REINFORCEMENT_SIZE = AI_DEFAULTS["design_options"]["reinforcement_size"]
DEFAULT_AI_DESIGN_REINFORCEMENT_MATERIAL = AI_DEFAULTS["design_options"]["reinforcement_material"]

DEFAULT_AI_GIRDER_DEPTH_MODE = AI_DEFAULTS["girder_details"]["depth_mode"]
DEFAULT_AI_GIRDER_TOP_FLANGE_WIDTH_MODE = AI_DEFAULTS["girder_details"]["top_flange_width_mode"]
DEFAULT_AI_GIRDER_TOP_FLANGE_THICKNESS_MODE = AI_DEFAULTS["girder_details"]["top_flange_thickness_mode"]
DEFAULT_AI_GIRDER_BOTTOM_FLANGE_WIDTH_MODE = AI_DEFAULTS["girder_details"]["bottom_flange_width_mode"]
DEFAULT_AI_GIRDER_BOTTOM_FLANGE_THICKNESS_MODE = AI_DEFAULTS["girder_details"]["bottom_flange_thickness_mode"]
DEFAULT_AI_GIRDER_WEB_THICKNESS_MODE = AI_DEFAULTS["girder_details"]["web_thickness_mode"]

# Additional-input labels used by the Typical Section UI
AI_CRASH_BARRIER_RCC = "IRC 5 - RCC Crash Barrier"
AI_CRASH_BARRIER_HIGH_CONTAINMENT = "IRC 5 - High Containment RCC Crash Barrier"
AI_CRASH_BARRIER_METALLIC_SINGLE = "IRC 5 - Metallic Crash Barrier with Single W-Beam"
AI_CRASH_BARRIER_METALLIC_DOUBLE = "IRC 5 - Metallic Crash Barrier with Double W-Beam"
AI_MEDIAN_RAISED_KERB = "IRC 5 - Raised Kerb"
AI_MEDIAN_RCC = "IRC 5 - RCC Crash Barrier"
AI_MEDIAN_METALLIC_SINGLE = "IRC 5 - Metallic Crash Barrier with Single W-Beam"
AI_MEDIAN_METALLIC_DOUBLE = "IRC 5 - Metallic Crash Barrier with Double W-Beam"
AI_TYPE_CUSTOM = "Custom"


def _mm_to_m(value: float | int | None, fallback_m: float) -> float:
    if value is None:
        return fallback_m
    try:
        return float(value) / 1000.0
    except (TypeError, ValueError):
        return fallback_m


def _resolve_irc_footpath(footpath_value: str) -> str:
    if footpath_value in KEY_FOOTPATH:
        return footpath_value
    return KEY_FOOTPATH[1] if len(KEY_FOOTPATH) > 1 else "Single Side"


def _resolve_irc_railing(railing_type: str | None) -> str:
    if railing_type and "steel" in railing_type.lower():
        return KEY_RAILING_TYPE[1]
    return KEY_RAILING_TYPE[0]


def get_ai_crash_barrier_defaults(
    barrier_type: str,
    footpath_value: str = "Both Sides",
    railing_type: str | None = None,
) -> dict[str, float | None]:
    """Return IRC-backed defaults for Additional Inputs crash-barrier fields."""
    defaults = {
        "density": None,
        "width_m": None,
        "height_m": None,
        "area_m2": None,
        "load_kn_per_m": None,
        "post_spacing_m": None,
    }

    if barrier_type == AI_TYPE_CUSTOM:
        return defaults

    is_rcc = barrier_type in {AI_CRASH_BARRIER_RCC, AI_CRASH_BARRIER_HIGH_CONTAINMENT}
    is_metallic = barrier_type in {AI_CRASH_BARRIER_METALLIC_SINGLE, AI_CRASH_BARRIER_METALLIC_DOUBLE}
    if not (is_rcc or is_metallic):
        return defaults

    if is_rcc:
        irc_barrier = KEY_CRASH_BARRIER_TYPE[2]  # Rigid (per IRC helper indexing)
        irc_subtype = (
            KEY_RIGID_CRASH_BARRIER_TYPE[1]
            if barrier_type == AI_CRASH_BARRIER_HIGH_CONTAINMENT
            else KEY_RIGID_CRASH_BARRIER_TYPE[0]
        )
    else:
        irc_barrier = KEY_CRASH_BARRIER_TYPE[1]  # Semi-Rigid
        irc_subtype = (
            KEY_METALLIC_CRASH_BARRIER_TYPE[1]
            if barrier_type == AI_CRASH_BARRIER_METALLIC_DOUBLE
            else KEY_METALLIC_CRASH_BARRIER_TYPE[0]
        )

    try:
        design_dict = IRC5_2015.cl_109_6_3_shapes(
            barrier_type=irc_barrier,
            footpath=_resolve_irc_footpath(footpath_value),
            railing_type=_resolve_irc_railing(railing_type),
            design_dict={},
            crash_barrier_type=irc_subtype,
        )
    except Exception:
        design_dict = {}

    if is_rcc:
        width_m = _mm_to_m(
            design_dict.get("crash_barrier_width"),
            float(DEFAULT_AI_CRASH_BARRIER_WIDTH_M),
        )
        height_m = _mm_to_m(design_dict.get("crash_barrier_height"), 0.75)
        density = float(DEFAULT_CONCRETE_DENSITY)
        area_m2 = width_m * height_m
        defaults.update(
            {
                "density": density,
                "width_m": width_m,
                "height_m": height_m,
                "area_m2": area_m2,
                "load_kn_per_m": density * area_m2,
            }
        )
        return defaults

    width_m = _mm_to_m(
        design_dict.get("crash_barrier_width"),
        DEFAULT_IRC_METALLIC_BARRIER_BASE_WIDTH_MM / 1000.0,
    )
    height_m = _mm_to_m(design_dict.get("crash_barrier_height"), 1.05)
    post_spacing_m = _mm_to_m(
        design_dict.get("post_spacing"),
        float(DEFAULT_AI_CRASH_BARRIER_POST_SPACING_M),
    )
    defaults.update(
        {
            "width_m": width_m,
            "height_m": height_m,
            "post_spacing_m": post_spacing_m,
        }
    )
    return defaults


def get_ai_median_defaults(median_type: str) -> dict[str, float | None]:
    """Return IRC-backed defaults for Additional Inputs median fields."""
    defaults = {
        "density": None,
        "width_m": None,
        "height_m": None,
        "area_m2": None,
        "load_kn_per_m": None,
        "post_spacing_m": None,
    }

    if median_type == AI_TYPE_CUSTOM:
        return defaults

    is_rcc = median_type in {AI_MEDIAN_RAISED_KERB, AI_MEDIAN_RCC}
    is_metallic = median_type in {AI_MEDIAN_METALLIC_SINGLE, AI_MEDIAN_METALLIC_DOUBLE}
    if not (is_rcc or is_metallic):
        return defaults

    if median_type == AI_MEDIAN_RAISED_KERB:
        irc_median = KEY_MEDIAN_TYPE[0]
        irc_subtype = None
    elif median_type == AI_MEDIAN_RCC:
        irc_median = KEY_MEDIAN_TYPE[1]
        irc_subtype = None
    else:
        irc_median = KEY_MEDIAN_TYPE[2]
        irc_subtype = (
            KEY_METALLIC_CRASH_BARRIER_TYPE[1]
            if median_type == AI_MEDIAN_METALLIC_DOUBLE
            else KEY_METALLIC_CRASH_BARRIER_TYPE[0]
        )

    try:
        design_dict = IRC5_2015.cl_109_6_3_shapes(
            barrier_type=irc_median,
            footpath=KEY_FOOTPATH[0],
            railing_type=None,
            design_dict={},
            crash_barrier_type=irc_subtype,
        )
    except Exception:
        design_dict = {}

    width_m = _mm_to_m(design_dict.get("median_width"), 1.2)

    if median_type == AI_MEDIAN_RAISED_KERB:
        height_m = _mm_to_m(design_dict.get("kerb_height"), 0.225)
    elif median_type == AI_MEDIAN_RCC:
        total_height_mm = (design_dict.get("barrier_height") or 0) + (design_dict.get("kerb_height") or 0)
        height_m = _mm_to_m(total_height_mm or None, 1.0)
    else:
        total_height_mm = (design_dict.get("post_height") or 0) + (design_dict.get("kerb_height") or 0)
        height_m = _mm_to_m(total_height_mm or None, 1.05)

    defaults.update({"width_m": width_m, "height_m": height_m})

    if is_rcc:
        density = float(DEFAULT_CONCRETE_DENSITY)
        area_m2 = width_m * height_m
        defaults.update(
            {
                "density": density,
                "area_m2": area_m2,
                "load_kn_per_m": density * area_m2,
            }
        )
        return defaults

    post_spacing_m = _mm_to_m(
        design_dict.get("post_spacing"),
        float(DEFAULT_AI_MEDIAN_POST_SPACING_M),
    )
    defaults["post_spacing_m"] = post_spacing_m
    return defaults


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
    KEY_SKEW_ANGLE: DEFAULT_SKEW_ANGLE_DEG,
    KEY_DESIGN_MODE: "Optimized",
    KEY_GIRDER: steel_properties[0],
    KEY_CROSS_BRACING: steel_properties[0],
    KEY_END_DIAPHRAGM: steel_properties[0],
    KEY_DECK_CONCRETE_GRADE_BASIC: concrete_properies[0],

    # Additional Inputs Defaults
    

}
#--------------Inp-dict-End----------------

ADDITIONAL_INPUT_DICT = {
    # Computed from basic_input_dict by solve_basic_input()
    'n_footpaths':    0,
    'footpath_width': 0.0,
    'railing_width':  0.0,
    'median_width':   0.0,
    # Layout solver results (populated by solve_basic_input)
    'overall_width':  None,
    'no_of_girders':  DEFAULT_NO_OF_GIRDERS,
    'girder_spacing': float(DEFAULT_GIRDER_SPACING),
    'deck_overhang':  None,
}

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


def solve_basic_input(basic_input_dict: dict):
    """Parse basic inputs and solve bridge layout.

    Returns
    -------
    tuple[dict, BridgeLayoutResult, dict]
        (combined_dict, sizing_result, section_props)

        combined_dict merges ADDITIONAL_INPUT_DICT defaults with solved values,
        then basic_input_dict appended on top.
    """
    from .initial_sizing import BridgeConfigurationSolver

    def _to_float(val, fallback):
        if val is None or str(val).strip().lower() in ('', 'none'):
            return fallback
        try:
            return float(val)
        except (TypeError, ValueError):
            return fallback

    span       = float(basic_input_dict[KEY_SPAN])
    cw_width   = float(basic_input_dict[KEY_CARRIAGEWAY_WIDTH])
    skew_angle = _to_float(basic_input_dict.get(KEY_SKEW_ANGLE), DEFAULT_SKEW_ANGLE_DEG)

    include_median = str(basic_input_dict.get(KEY_INCLUDE_MEDIAN, 'No')).strip()
    footpath_str   = str(basic_input_dict.get(KEY_FOOTPATH,       'None')).strip()
    design_mode    = str(basic_input_dict.get(KEY_DESIGN_MODE,    'Optimized')).strip()

    if footpath_str in ('None', ''):
        n_footpaths, footpath_width, railing_width = 0, 0.0, 0.0
    elif 'Both' in footpath_str:
        n_footpaths = 2
        footpath_width = float(IS_DEFAULT_FOOTPATH_WIDTH_M)
        railing_width  = float(DEFAULT_RAILING_WIDTH)
    else:
        n_footpaths = 1
        footpath_width = float(IS_DEFAULT_FOOTPATH_WIDTH_M)
        railing_width  = float(DEFAULT_RAILING_WIDTH)

    median_width = DEFAULT_FALLBACK_MEDIAN_WIDTH_M if include_median.lower() == 'yes' else 0.0

    solver = BridgeConfigurationSolver(
        carriageway_width=cw_width,
        crash_barrier_width=DEFAULT_CRASH_BARRIER_WIDTH,
        footpath_width=footpath_width,
        railing_width=railing_width,
        median_width=median_width,
        n_footpaths=n_footpaths,
    )
    sizing_result = solver._solve_layout(no_of_girders=DEFAULT_NO_OF_GIRDERS, changed_field='girders')

    print("[DEBUG] Bridge Layout Sizing Result:")
    print(f"  overall_width = {sizing_result.overall_width} m")
    print(f"  no_of_girders = {sizing_result.no_of_girders}")
    print(f"  girder_spacing = {sizing_result.girder_spacing} m")
    print(f"  deck_overhang = {sizing_result.deck_overhang} m")

    symmetry = DEFAULT_GIRDER_SYMMETRY if design_mode == 'Optimized' else 'Girder Unsymmetric'
    section_props = solver.compute_section_properties(span=span, symmetry=symmetry)

    combined = deepcopy(ADDITIONAL_INPUT_DICT)
    combined.update({
        'n_footpaths':    n_footpaths,
        'footpath_width': footpath_width,
        'railing_width':  railing_width,
        'median_width':   median_width,
        'overall_width':  sizing_result.overall_width,
        'no_of_girders':  sizing_result.no_of_girders,
        'girder_spacing': sizing_result.girder_spacing,
        'deck_overhang':  sizing_result.deck_overhang,
    })
    combined.update(basic_input_dict)
    print(f"[DEBUG] Combined Input Dictionary: {combined}")
    return combined, sizing_result, section_props