"""Centralized defaults for Plate Girder Bridge."""

from __future__ import annotations

from copy import deepcopy

from osdagbridge.core.utils.codes.irc5_2015 import IRC5_2015
from osdagbridge.core.utils.codes.keyfile import (
    GAMMA_M0_STEEL,
    GAMMA_M1_STEEL_ULTIMATE,
    GAMMA_M_REINFORCEMENT,
    GAMMA_M_SHEAR_CONCRETE,
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
)
from .initial_sizing import (
    DEFAULT_DECK_OVERHANG_RATIO as IS_DEFAULT_DECK_OVERHANG_RATIO,
    DEFAULT_DECK_THICKNESS as IS_DEFAULT_DECK_THICKNESS_MM,
    DEFAULT_FOOTPATH_WIDTH as IS_DEFAULT_FOOTPATH_WIDTH_M,
    # Layout bounds
    MIN_GIRDER_SPACING as IS_MIN_GIRDER_SPACING_M,
    # Deck thickness bounds
    MIN_DECK_THICKNESS as IS_MIN_DECK_THICKNESS_MM,
    MAX_DECK_THICKNESS as IS_MAX_DECK_THICKNESS_MM,
    # Girder depth span ratios
    DEFAULT_DEPTH_SPAN_RATIO as IS_DEFAULT_DEPTH_SPAN_RATIO,
    MIN_DEPTH_SPAN_RATIO as IS_MIN_DEPTH_SPAN_RATIO,
    MAX_DEPTH_SPAN_RATIO as IS_MAX_DEPTH_SPAN_RATIO,
)

# Workflow / Runtime Defaults
DEFAULT_STRUCTURE_NAME = "plate_girder_bridge"
DEFAULT_SPAN_M = 33.5
DEFAULT_CARRIAGEWAY_WIDTH_M = 10.0
DEFAULT_MEDIAN_WIDTH_M = 0.0
DEFAULT_NO_OF_GIRDERS = 4
DEFAULT_DECK_THICKNESS_MM = float(IS_DEFAULT_DECK_THICKNESS_MM)
DEFAULT_GIRDER_SYMMETRY = "Girder Symmetric"
DEFAULT_SKEW_ANGLE_DEG = 0.0
DEFAULT_GEOMETRY_TOLERANCE = 1e-3

# Additional Inputs Defaults
# Layout
AI_LAYOUT_DEFAULTS = {
    # defaults
    "girder_spacing_m": float(DEFAULT_GIRDER_SPACING),
    "no_of_girders": int(DEFAULT_NO_OF_GIRDERS),
    "deck_overhang_ratio": float(IS_DEFAULT_DECK_OVERHANG_RATIO),
    # overhang = ratio × spacing (initial_sizing.py line 236: overhang = 0.5 * spacing)
    "deck_overhang_m": round(float(DEFAULT_GIRDER_SPACING) * float(IS_DEFAULT_DECK_OVERHANG_RATIO), 3),
    "deck_thickness_mm": float(IS_DEFAULT_DECK_THICKNESS_MM),
    "footpath_width_m": float(IS_DEFAULT_FOOTPATH_WIDTH_M),
    "footpath_thickness_mm": float(IS_DEFAULT_DECK_THICKNESS_MM),
    # bounds sourced from initial_sizing.py
    "min_girder_spacing_m": float(IS_MIN_GIRDER_SPACING_M),
    "min_deck_thickness_mm": float(IS_MIN_DECK_THICKNESS_MM),
    "max_deck_thickness_mm": float(IS_MAX_DECK_THICKNESS_MM),
    "default_depth_span_ratio": int(IS_DEFAULT_DEPTH_SPAN_RATIO),
    "min_depth_span_ratio": int(IS_MIN_DEPTH_SPAN_RATIO),
    "max_depth_span_ratio": int(IS_MAX_DEPTH_SPAN_RATIO),
}

AI_DEFAULTS: dict[str, dict[str, object]] = {
    # Layout
    "layout": deepcopy(AI_LAYOUT_DEFAULTS),
    # Crash Barrier
    "crash_barrier": {
        "type": "IRC 5 - RCC Crash Barrier",
        "width_m": float(DEFAULT_CRASH_BARRIER_WIDTH),
        "post_spacing_m": "1",
    },
    # Median
    "median": {
        "type": "IRC 5 - Raised Kerb",
        "post_spacing_m": "1",
    },
    # Railing
    "railing": {
        "type": "IRC 5 - RCC Railing",
        "load_mode": "Automatic (IRC 6)",
        "width_mm": f"{DEFAULT_RAILING_WIDTH * 1000:.0f}",
    },
    # Wearing Course
    "wearing_course": {
        "material": "Concrete",
        "density_kn_per_m3": "24.0",
        "thickness_mm": "50",
    },
    # Lane Details
    "lane_details": {
        "lane_count": "2",
    },
    # Permanent Load
    "permanent_load": {
        "include_self_weight": "Yes",
        "self_weight_factor": "1.00",
        "include_deck_weight": "Yes",
        "include_wearing_course": "Yes",
        "include_crash_barrier": "Yes",
        "include_median": "Yes",
        "include_railing": "Yes",
    },
    # Live Load
    "live_load": {
        "irc_vehicles_checked": True,
        "braking_vehicles_checked": True,
        "eccentricity_m": "0.00",
        "footpath_mode": "Automatic",
        "footpath_pressure_kn_per_mm2": "5.00",
    },
    # Seismic Load
    "seismic_load": {
        "zone": "II",
        "importance_factor": "1.0",
        "soil_type": "Type I \u2013 Rocky or Hard Soil",
        "damping_percent": "2",
        "response_reduction_factor": "1",
        "dead_load_mode": "Automatic",
        "live_load_mode": "Automatic",
    },
    # Wind Load
    "wind_load": {
        "basic_wind_speed": "33",
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
    # Temperature Load
    "temperature_load": {
        "highest_max_temp": "50",
        "lowest_min_temp": "10",
        "thermal_coeff_steel_per_c": "12.0e-6",
        "thermal_coeff_rcc_per_c": "12.0e-6",
    },
    # Support Conditions
    "support_conditions": {
        "left": "Fixed",
        "right": "Pinned",
        "bearing_length": "0",
    },
    # Design Options
    "design_options": {
        "construction_stage": "Yes",
        "reinforcement_size": "12 mm",
        "reinforcement_material": "Fe 500",
        "shear_stud_material": "Fe 410",
        "shear_stud_diameter": "22",
        "shear_stud_height": "100",
    },
    # Design Options (Cont.)
    "design_options_cont": {
        "gamma_c_basic": "1.50",
        "gamma_c_accidental": "1.20",
        "gamma_m0": f"{GAMMA_M0_STEEL}",
        "gamma_m1": f"{GAMMA_M1_STEEL_ULTIMATE}",
        "gamma_s": f"{GAMMA_M_REINFORCEMENT}",
        "gamma_v": f"{GAMMA_M_SHEAR_CONCRETE}",
        "gamma_flt": "1.15",
        "gamma_mf": "1.35",
        "load_cycles": "2000000",
        "k1": "1.0",
        "k3": "1.0",
        "k4": "1.0",
        "k6": "1.0",
        "k3_second": "1.0",
        "k4_second": "1.0",
        "limit_l": f"{DEFAULT_SPAN_M}",
    },
    # Girder Details
    "girder_details": {
        "type": "Welded",
        "span": "Full Length",
        "design": "Optimized",
        "symmetry": "Girder Symmetric",
        "torsional_restraint": "Fully Restrained",
        "warping_restraint": "Both Flanges Restrained",
        "web_type": "Thin Web with ITS",
        "is_section": "ISMB 500",
        "depth_mode": "Optimized",
        "top_flange_width_mode": "Optimized",
        "top_flange_thickness_mode": "All",
        "bottom_flange_width_mode": "Optimized",
        "bottom_flange_thickness_mode": "All",
        "web_thickness_mode": "All",
    },
}


# get_ai_defaults() accessor
def get_ai_defaults(section: str | None = None) -> dict[str, object] | dict[str, dict[str, object]]:
    """Return dictionary-based Additional Inputs defaults."""
    if section is None:
        return deepcopy(AI_DEFAULTS)
    return deepcopy(AI_DEFAULTS.get(section, {}))


# Compatibility Aliases

# Layout
DEFAULT_AI_LAYOUT_GIRDER_SPACING_M = AI_DEFAULTS["layout"]["girder_spacing_m"]
DEFAULT_AI_LAYOUT_NO_OF_GIRDERS = AI_DEFAULTS["layout"]["no_of_girders"]
DEFAULT_AI_LAYOUT_DECK_OVERHANG_RATIO = AI_DEFAULTS["layout"]["deck_overhang_ratio"]
DEFAULT_AI_LAYOUT_DECK_OVERHANG_M = AI_DEFAULTS["layout"]["deck_overhang_m"]
DEFAULT_AI_LAYOUT_DECK_THICKNESS_MM = f"{AI_DEFAULTS['layout']['deck_thickness_mm']:.0f}"
DEFAULT_AI_LAYOUT_FOOTPATH_WIDTH_M = f"{AI_DEFAULTS['layout']['footpath_width_m']:.2f}"
DEFAULT_AI_LAYOUT_FOOTPATH_THICKNESS_MM = f"{AI_DEFAULTS['layout']['footpath_thickness_mm']:.0f}"
# Layout bounds (numeric, for use by validator and backend — sourced from initial_sizing.py)
DEFAULT_AI_LAYOUT_MIN_GIRDER_SPACING_M = AI_DEFAULTS["layout"]["min_girder_spacing_m"]
DEFAULT_AI_LAYOUT_MIN_DECK_THICKNESS_MM = AI_DEFAULTS["layout"]["min_deck_thickness_mm"]
DEFAULT_AI_LAYOUT_MAX_DECK_THICKNESS_MM = AI_DEFAULTS["layout"]["max_deck_thickness_mm"]
DEFAULT_AI_LAYOUT_DEFAULT_DEPTH_SPAN_RATIO = AI_DEFAULTS["layout"]["default_depth_span_ratio"]
DEFAULT_AI_LAYOUT_MIN_DEPTH_SPAN_RATIO = AI_DEFAULTS["layout"]["min_depth_span_ratio"]
DEFAULT_AI_LAYOUT_MAX_DEPTH_SPAN_RATIO = AI_DEFAULTS["layout"]["max_depth_span_ratio"]

# Crash Barrier
DEFAULT_AI_CRASH_BARRIER_TYPE = AI_DEFAULTS["crash_barrier"]["type"]
DEFAULT_AI_CRASH_BARRIER_WIDTH_M = AI_DEFAULTS["crash_barrier"]["width_m"]
DEFAULT_AI_CRASH_BARRIER_POST_SPACING_M = AI_DEFAULTS["crash_barrier"]["post_spacing_m"]

# Median
DEFAULT_AI_MEDIAN_TYPE = AI_DEFAULTS["median"]["type"]
DEFAULT_AI_MEDIAN_POST_SPACING_M = AI_DEFAULTS["median"]["post_spacing_m"]

# Railing
DEFAULT_AI_RAILING_TYPE = AI_DEFAULTS["railing"]["type"]
DEFAULT_AI_RAILING_LOAD_MODE = AI_DEFAULTS["railing"]["load_mode"]
DEFAULT_AI_RAILING_WIDTH_MM = AI_DEFAULTS["railing"]["width_mm"]

# Wearing Course
DEFAULT_AI_WEARING_MATERIAL = AI_DEFAULTS["wearing_course"]["material"]
DEFAULT_AI_WEARING_DENSITY_KN_PER_M3 = AI_DEFAULTS["wearing_course"]["density_kn_per_m3"]
DEFAULT_AI_WEARING_THICKNESS_MM = AI_DEFAULTS["wearing_course"]["thickness_mm"]

# Lane Details
DEFAULT_AI_LANE_COUNT = AI_DEFAULTS["lane_details"]["lane_count"]

# Permanent Load
DEFAULT_AI_PERM_INCLUDE_SELF_WEIGHT = AI_DEFAULTS["permanent_load"]["include_self_weight"]
DEFAULT_AI_PERM_SELF_WEIGHT_FACTOR = AI_DEFAULTS["permanent_load"]["self_weight_factor"]
DEFAULT_AI_PERM_INCLUDE_DECK_WEIGHT = AI_DEFAULTS["permanent_load"]["include_deck_weight"]
DEFAULT_AI_PERM_INCLUDE_WEARING_COURSE = AI_DEFAULTS["permanent_load"]["include_wearing_course"]
DEFAULT_AI_PERM_INCLUDE_CRASH_BARRIER = AI_DEFAULTS["permanent_load"]["include_crash_barrier"]
DEFAULT_AI_PERM_INCLUDE_MEDIAN = AI_DEFAULTS["permanent_load"]["include_median"]
DEFAULT_AI_PERM_INCLUDE_RAILING = AI_DEFAULTS["permanent_load"]["include_railing"]

# Live Load
DEFAULT_AI_LIVE_IRC_VEHICLES_CHECKED = AI_DEFAULTS["live_load"]["irc_vehicles_checked"]
DEFAULT_AI_LIVE_BRAKING_VEHICLES_CHECKED = AI_DEFAULTS["live_load"]["braking_vehicles_checked"]
DEFAULT_AI_LIVE_ECCENTRICITY_M = AI_DEFAULTS["live_load"]["eccentricity_m"]
DEFAULT_AI_LIVE_FOOTPATH_MODE = AI_DEFAULTS["live_load"]["footpath_mode"]
DEFAULT_AI_LIVE_FOOTPATH_PRESSURE_KN_PER_MM2 = AI_DEFAULTS["live_load"]["footpath_pressure_kn_per_mm2"]

# Seismic Load
DEFAULT_AI_SEISMIC_ZONE = AI_DEFAULTS["seismic_load"]["zone"]
DEFAULT_AI_SEISMIC_IMPORTANCE_FACTOR = AI_DEFAULTS["seismic_load"]["importance_factor"]
DEFAULT_AI_SEISMIC_SOIL_TYPE = AI_DEFAULTS["seismic_load"]["soil_type"]
DEFAULT_AI_SEISMIC_DAMPING_PERCENT = AI_DEFAULTS["seismic_load"]["damping_percent"]
DEFAULT_AI_SEISMIC_RESPONSE_REDUCTION_FACTOR = AI_DEFAULTS["seismic_load"]["response_reduction_factor"]
DEFAULT_AI_SEISMIC_DEAD_LOAD_MODE = AI_DEFAULTS["seismic_load"]["dead_load_mode"]
DEFAULT_AI_SEISMIC_LIVE_LOAD_MODE = AI_DEFAULTS["seismic_load"]["live_load_mode"]

# Wind Load
DEFAULT_AI_WIND_BASIC_WIND_SPEED = AI_DEFAULTS["wind_load"]["basic_wind_speed"]
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

# Temperature Load
DEFAULT_AI_TEMP_HIGHEST_MAX_TEMP = AI_DEFAULTS["temperature_load"]["highest_max_temp"]
DEFAULT_AI_TEMP_LOWEST_MIN_TEMP = AI_DEFAULTS["temperature_load"]["lowest_min_temp"]
DEFAULT_AI_TEMP_THERMAL_COEFF_STEEL_PER_C = AI_DEFAULTS["temperature_load"]["thermal_coeff_steel_per_c"]
DEFAULT_AI_TEMP_THERMAL_COEFF_RCC_PER_C = AI_DEFAULTS["temperature_load"]["thermal_coeff_rcc_per_c"]

# Support Conditions
DEFAULT_AI_SUPPORT_LEFT = AI_DEFAULTS["support_conditions"]["left"]
DEFAULT_AI_SUPPORT_RIGHT = AI_DEFAULTS["support_conditions"]["right"]
DEFAULT_AI_SUPPORT_BEARING_LENGTH = AI_DEFAULTS["support_conditions"]["bearing_length"]

# Design Options
DEFAULT_AI_DESIGN_CONSTRUCTION_STAGE = AI_DEFAULTS["design_options"]["construction_stage"]
DEFAULT_AI_DESIGN_REINFORCEMENT_SIZE = AI_DEFAULTS["design_options"]["reinforcement_size"]
DEFAULT_AI_DESIGN_REINFORCEMENT_MATERIAL = AI_DEFAULTS["design_options"]["reinforcement_material"]
DEFAULT_AI_DESIGN_SHEAR_STUD_MATERIAL = AI_DEFAULTS["design_options"]["shear_stud_material"]
DEFAULT_AI_DESIGN_SHEAR_STUD_DIAMETER = AI_DEFAULTS["design_options"]["shear_stud_diameter"]
DEFAULT_AI_DESIGN_SHEAR_STUD_HEIGHT = AI_DEFAULTS["design_options"]["shear_stud_height"]

# Design Options (Cont.)
DEFAULT_AI_DESIGN_CONT_GAMMA_C_BASIC = AI_DEFAULTS["design_options_cont"]["gamma_c_basic"]
DEFAULT_AI_DESIGN_CONT_GAMMA_C_ACCIDENTAL = AI_DEFAULTS["design_options_cont"]["gamma_c_accidental"]
DEFAULT_AI_DESIGN_CONT_GAMMA_M0 = AI_DEFAULTS["design_options_cont"]["gamma_m0"]
DEFAULT_AI_DESIGN_CONT_GAMMA_M1 = AI_DEFAULTS["design_options_cont"]["gamma_m1"]
DEFAULT_AI_DESIGN_CONT_GAMMA_S = AI_DEFAULTS["design_options_cont"]["gamma_s"]
DEFAULT_AI_DESIGN_CONT_GAMMA_V = AI_DEFAULTS["design_options_cont"]["gamma_v"]
DEFAULT_AI_DESIGN_CONT_GAMMA_FLT = AI_DEFAULTS["design_options_cont"]["gamma_flt"]
DEFAULT_AI_DESIGN_CONT_GAMMA_MF = AI_DEFAULTS["design_options_cont"]["gamma_mf"]
DEFAULT_AI_DESIGN_CONT_LOAD_CYCLES = AI_DEFAULTS["design_options_cont"]["load_cycles"]
DEFAULT_AI_DESIGN_CONT_K1 = AI_DEFAULTS["design_options_cont"]["k1"]
DEFAULT_AI_DESIGN_CONT_K3 = AI_DEFAULTS["design_options_cont"]["k3"]
DEFAULT_AI_DESIGN_CONT_K4 = AI_DEFAULTS["design_options_cont"]["k4"]
DEFAULT_AI_DESIGN_CONT_K6 = AI_DEFAULTS["design_options_cont"]["k6"]
DEFAULT_AI_DESIGN_CONT_K3_SECOND = AI_DEFAULTS["design_options_cont"]["k3_second"]
DEFAULT_AI_DESIGN_CONT_K4_SECOND = AI_DEFAULTS["design_options_cont"]["k4_second"]
DEFAULT_AI_DESIGN_CONT_LIMIT_L = AI_DEFAULTS["design_options_cont"]["limit_l"]

# Girder Details
DEFAULT_AI_GIRDER_TYPE = AI_DEFAULTS["girder_details"]["type"]
DEFAULT_AI_GIRDER_SPAN = AI_DEFAULTS["girder_details"]["span"]
DEFAULT_AI_GIRDER_DESIGN = AI_DEFAULTS["girder_details"]["design"]
DEFAULT_AI_GIRDER_SYMMETRY = AI_DEFAULTS["girder_details"]["symmetry"]
DEFAULT_AI_GIRDER_TORSIONAL_RESTRAINT = AI_DEFAULTS["girder_details"]["torsional_restraint"]
DEFAULT_AI_GIRDER_WARPING_RESTRAINT = AI_DEFAULTS["girder_details"]["warping_restraint"]
DEFAULT_AI_GIRDER_WEB_TYPE = AI_DEFAULTS["girder_details"]["web_type"]
DEFAULT_AI_GIRDER_IS_SECTION = AI_DEFAULTS["girder_details"]["is_section"]
DEFAULT_AI_GIRDER_DEPTH_MODE = AI_DEFAULTS["girder_details"]["depth_mode"]
DEFAULT_AI_GIRDER_TOP_FLANGE_WIDTH_MODE = AI_DEFAULTS["girder_details"]["top_flange_width_mode"]
DEFAULT_AI_GIRDER_TOP_FLANGE_THICKNESS_MODE = AI_DEFAULTS["girder_details"]["top_flange_thickness_mode"]
DEFAULT_AI_GIRDER_BOTTOM_FLANGE_WIDTH_MODE = AI_DEFAULTS["girder_details"]["bottom_flange_width_mode"]
DEFAULT_AI_GIRDER_BOTTOM_FLANGE_THICKNESS_MODE = AI_DEFAULTS["girder_details"]["bottom_flange_thickness_mode"]
DEFAULT_AI_GIRDER_WEB_THICKNESS_MODE = AI_DEFAULTS["girder_details"]["web_thickness_mode"]

# Label / Name Constants
AI_CRASH_BARRIER_RCC = "IRC 5 - RCC Crash Barrier"
AI_CRASH_BARRIER_HIGH_CONTAINMENT = "IRC 5 - High Containment RCC Crash Barrier"
AI_CRASH_BARRIER_METALLIC_SINGLE = "IRC 5 - Metallic Crash Barrier with Single W-Beam"
AI_CRASH_BARRIER_METALLIC_DOUBLE = "IRC 5 - Metallic Crash Barrier with Double W-Beam"
AI_MEDIAN_RAISED_KERB = "IRC 5 - Raised Kerb"
AI_MEDIAN_RCC = "IRC 5 - RCC Crash Barrier"
AI_MEDIAN_METALLIC_SINGLE = "IRC 5 - Metallic Crash Barrier with Single W-Beam"
AI_MEDIAN_METALLIC_DOUBLE = "IRC 5 - Metallic Crash Barrier with Double W-Beam"
AI_TYPE_CUSTOM = "Custom"


# Internal Helpers
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


# IRC-Backed Dynamic Default Functions
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
        550 / 1000.0,
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


# Input Dock Defaults (DEFAULTS_DICT)
from osdagbridge.core.utils.common import (
    KEY_STRUCTURE_TYPE, KEY_PROJECT_LOCATION, KEY_SPAN, KEY_CARRIAGEWAY_WIDTH, KEY_INCLUDE_MEDIAN,
    KEY_FOOTPATH, KEY_SKEW_ANGLE, KEY_DESIGN_MODE, KEY_GIRDER, KEY_CROSS_BRACING, KEY_END_DIAPHRAGM,
    KEY_DECK_CONCRETE_GRADE_BASIC, VALUES_DECK_CONCRETE_GRADE,
    connectdb,
)
material_values = connectdb("Material")

DEFAULTS_DICT = {
    # Input Dock Defaults
    KEY_STRUCTURE_TYPE: "Highway Bridge",
    KEY_PROJECT_LOCATION: None,
    KEY_SPAN: DEFAULT_SPAN_M,
    KEY_CARRIAGEWAY_WIDTH: DEFAULT_CARRIAGEWAY_WIDTH_M,
    KEY_INCLUDE_MEDIAN: "No",
    KEY_FOOTPATH: "None",
    KEY_SKEW_ANGLE: DEFAULT_SKEW_ANGLE_DEG,
    KEY_DESIGN_MODE: "Optimized",
    KEY_GIRDER: material_values[0],
    KEY_CROSS_BRACING: material_values[0],
    KEY_END_DIAPHRAGM: material_values[0],
    KEY_DECK_CONCRETE_GRADE_BASIC: VALUES_DECK_CONCRETE_GRADE[0],

    # Additional Inputs Defaults (layout)
    "girder_spacing":   AI_DEFAULTS["layout"]["girder_spacing_m"],
    "no_of_girders":    AI_DEFAULTS["layout"]["no_of_girders"],
    "deck_overhang":    AI_DEFAULTS["layout"]["deck_overhang_m"],
    "deck_thickness":   AI_DEFAULTS["layout"]["deck_thickness_mm"],
    "footpath_width":   AI_DEFAULTS["layout"]["footpath_width_m"],
    "footpath_thickness": AI_DEFAULTS["layout"]["footpath_thickness_mm"],
    # Additional Inputs Defaults (crash barrier — static; IRC-computed fields set below)
    "crash_barrier_type":         DEFAULT_AI_CRASH_BARRIER_TYPE,
    "crash_barrier_width":        AI_DEFAULTS["crash_barrier"]["width_m"],
    "crash_barrier_post_spacing": float(AI_DEFAULTS["crash_barrier"]["post_spacing_m"]),
    # Additional Inputs Defaults (median — static; IRC-computed fields set below)
    "median_type":         DEFAULT_AI_MEDIAN_TYPE,
    "median_post_spacing": float(DEFAULT_AI_MEDIAN_POST_SPACING_M),
    # Additional Inputs Defaults (railing)
    "railing_type":      DEFAULT_AI_RAILING_TYPE,
    "railing_width":     float(AI_DEFAULTS["railing"]["width_mm"]) / 1000.0,
    "railing_load_mode": DEFAULT_AI_RAILING_LOAD_MODE,
    # Additional Inputs Defaults (wearing course)
    "wearing_material":  DEFAULT_AI_WEARING_MATERIAL,
    "wearing_density":   float(AI_DEFAULTS["wearing_course"]["density_kn_per_m3"]),
    "wearing_thickness": float(AI_DEFAULTS["wearing_course"]["thickness_mm"]),
    # Additional Inputs Defaults (lane details)
    "lane_count": str(DEFAULT_AI_LANE_COUNT),
    # Additional Inputs Defaults (permanent load)
    "include_self_weight":    DEFAULT_AI_PERM_INCLUDE_SELF_WEIGHT,
    "self_weight_factor":     DEFAULT_AI_PERM_SELF_WEIGHT_FACTOR,
    "include_deck_weight":    DEFAULT_AI_PERM_INCLUDE_DECK_WEIGHT,
    "include_wearing_course": DEFAULT_AI_PERM_INCLUDE_WEARING_COURSE,
    "include_crash_barrier":  DEFAULT_AI_PERM_INCLUDE_CRASH_BARRIER,
    "include_median":         DEFAULT_AI_PERM_INCLUDE_MEDIAN,
    "include_railing":        DEFAULT_AI_PERM_INCLUDE_RAILING,
    # Additional Inputs Defaults (live load)
    "eccentricity":             DEFAULT_AI_LIVE_ECCENTRICITY_M,
    "footpath_pressure":        DEFAULT_AI_LIVE_FOOTPATH_MODE,
    "footpath_pressure_value":  DEFAULT_AI_LIVE_FOOTPATH_PRESSURE_KN_PER_MM2,
    # Additional Inputs Defaults (seismic load)
    "seismic_zone":              DEFAULT_AI_SEISMIC_ZONE,
    "importance_factor":         DEFAULT_AI_SEISMIC_IMPORTANCE_FACTOR,
    "soil_type":                 DEFAULT_AI_SEISMIC_SOIL_TYPE,
    "damping":                   DEFAULT_AI_SEISMIC_DAMPING_PERCENT,
    "response_reduction_factor": DEFAULT_AI_SEISMIC_RESPONSE_REDUCTION_FACTOR,
    "dead_load_seismic":         DEFAULT_AI_SEISMIC_DEAD_LOAD_MODE,
    "live_load_seismic":         DEFAULT_AI_SEISMIC_LIVE_LOAD_MODE,
    # Additional Inputs Defaults (wind load — modes; value fields default empty)
    "basic_wind_speed":    DEFAULT_AI_WIND_BASIC_WIND_SPEED,
    "avg_exposed_height":  DEFAULT_AI_WIND_AVG_EXPOSED_HEIGHT_M,
    "terrain_type":        DEFAULT_AI_WIND_TERRAIN_TYPE,
    "site_topography":     DEFAULT_AI_WIND_SITE_TOPOGRAPHY,
    "gust_factor":         DEFAULT_AI_WIND_GUST_FACTOR_MODE,
    "gust_factor_value":   DEFAULT_AI_WIND_GUST_FACTOR,
    "drag_coeff":          DEFAULT_AI_WIND_DRAG_COEFF_MODE,
    "drag_coeff_ll":       DEFAULT_AI_WIND_DRAG_COEFF_LL_MODE,
    "drag_coeff_ll_value": DEFAULT_AI_WIND_DRAG_COEFF_LL,
    "lift_coeff":          DEFAULT_AI_WIND_LIFT_COEFF_MODE,
    "lift_coeff_value":    DEFAULT_AI_WIND_LIFT_COEFF,
    "super_area_elev":     DEFAULT_AI_WIND_SUPER_AREA_ELEV_MODE,
    "super_area_plain":    DEFAULT_AI_WIND_SUPER_AREA_PLAIN_MODE,
    "exposed_frontal_area": DEFAULT_AI_WIND_EXPOSED_FRONTAL_AREA_MODE,
    "wind_ecc_deck":       DEFAULT_AI_WIND_ECC_DECK_MODE,
    "wind_ll_ecc":         DEFAULT_AI_WIND_LL_ECC_MODE,
    # Additional Inputs Defaults (temperature load)
    "highest_max_temp":    DEFAULT_AI_TEMP_HIGHEST_MAX_TEMP,
    "lowest_min_temp":     DEFAULT_AI_TEMP_LOWEST_MIN_TEMP,
    "thermal_coeff_steel": DEFAULT_AI_TEMP_THERMAL_COEFF_STEEL_PER_C,
    "thermal_coeff_rcc":   DEFAULT_AI_TEMP_THERMAL_COEFF_RCC_PER_C,
    # Additional Inputs Defaults (design options)
    "construction_stage":     DEFAULT_AI_DESIGN_CONSTRUCTION_STAGE,
    "reinforcement_size":     DEFAULT_AI_DESIGN_REINFORCEMENT_SIZE,
    "reinforcement_material": DEFAULT_AI_DESIGN_REINFORCEMENT_MATERIAL,
    "shear_stud_material":    DEFAULT_AI_DESIGN_SHEAR_STUD_MATERIAL,
    "shear_stud_diameter":    DEFAULT_AI_DESIGN_SHEAR_STUD_DIAMETER,
    "shear_stud_height":      DEFAULT_AI_DESIGN_SHEAR_STUD_HEIGHT,
    # Additional Inputs Defaults (support conditions)
    "left_support":   AI_DEFAULTS["support_conditions"]["left"],
    "right_support":  AI_DEFAULTS["support_conditions"]["right"],
    "bearing_length": float(AI_DEFAULTS["support_conditions"]["bearing_length"]),
}

# Eagerly compute IRC-backed crash barrier defaults (height, density, area, load are IRC-derived).
_cb = get_ai_crash_barrier_defaults(DEFAULT_AI_CRASH_BARRIER_TYPE)
DEFAULTS_DICT.update({
    "crash_barrier_height":  _cb["height_m"]     if _cb.get("height_m")     is not None else 0.75,
    "crash_barrier_density": _cb["density"]       if _cb.get("density")       is not None else float(DEFAULT_CONCRETE_DENSITY),
    "crash_barrier_area":    _cb["area_m2"]       if _cb.get("area_m2")       is not None else 0.375,
    "crash_barrier_load":    _cb["load_kn_per_m"] if _cb.get("load_kn_per_m") is not None else 9.375,
})

# Eagerly compute IRC-backed median defaults (width, height, density, area, load are IRC-derived).
_med = get_ai_median_defaults(DEFAULT_AI_MEDIAN_TYPE)
DEFAULTS_DICT.update({
    "median_width":   _med["width_m"]      if _med.get("width_m")      is not None else 0.5,
    "median_height":  _med["height_m"]     if _med.get("height_m")     is not None else 0.225,
    "median_density": _med["density"]      if _med.get("density")      is not None else float(DEFAULT_CONCRETE_DENSITY),
    "median_area":    _med["area_m2"]      if _med.get("area_m2")      is not None else 0.27,
    "median_load":    _med["load_kn_per_m"] if _med.get("load_kn_per_m") is not None else 6.75,
})
