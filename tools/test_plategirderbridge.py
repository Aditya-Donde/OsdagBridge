import pytest

from math import isclose, ceil
from osdagbridge.core.bridge_types.plate_girder.validator import BridgeInputValidator
from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import PlateGirderBridge
from osdagbridge.core.utils.common import (
    KEY_SPAN, KEY_CARRIAGEWAY_WIDTH, KEY_INCLUDE_MEDIAN, KEY_SKEW_ANGLE, KEY_FOOTPATH,
    SPAN_MIN, SPAN_MAX,
    CARRIAGEWAY_WIDTH_MIN, CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN, CARRIAGEWAY_WIDTH_MAX_LIMIT,
    SKEW_ANGLE_MIN, SKEW_ANGLE_MAX,
    KEY_STRUCTURE_TYPE, KEY_PROJECT_LOCATION, KEY_DESIGN_MODE, KEY_GIRDER,
    KEY_CROSS_BRACING, KEY_END_DIAPHRAGM, KEY_DECK_CONCRETE_GRADE_BASIC,
    KEY_TS_GIRDER_SPACING, KEY_TS_NO_OF_GIRDERS, KEY_TS_DECK_OVERHANG,
    KEY_TS_DECK_THICKNESS, KEY_TS_FOOTPATH_WIDTH, KEY_TS_FOOTPATH_THICKNESS, KEY_TS_OVERALL_WIDTH,
    KEY_CB_WIDTH, KEY_CB_HEIGHT, KEY_CB_LOAD, KEY_CB_POST_SPACING,
    KEY_MD_WIDTH, KEY_MD_HEIGHT, KEY_MD_LOAD, KEY_MD_POST_SPACING,
    KEY_RL_HEIGHT, KEY_RL_WIDTH, KEY_RL_LOAD_VALUE,
    KEY_WC_DENSITY, KEY_WC_THICKNESS,
    KEY_WC_LD_LANE_TABLE_COUNT, KEY_WC_LD_LANE_TABLE,
    KEY_PL_SELF_WEIGHT_FACTOR,
    KEY_LL_ECCENTRICITY, KEY_LL_FOOTPATH_PRESSURE_MODE, KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_SL_IMPORTANCE_FACTOR, KEY_SL_TIME_PERIOD, KEY_SL_DAMPING,
    KEY_SL_DEAD_LOAD_MODE, KEY_SL_DEAD_LOAD_VALUE,
    KEY_SL_LIVE_LOAD_MODE, KEY_SL_LIVE_LOAD_VALUE,
    KEY_WL_AVG_EXPOSED_HEIGHT,
    KEY_WL_GUST_FACTOR_MODE, KEY_WL_GUST_FACTOR_VALUE,
    KEY_WL_DRAG_COEFF_MODE, KEY_WL_DRAG_COEFF_VALUE,
    KEY_WL_DRAG_COEFF_LL_MODE, KEY_WL_DRAG_COEFF_LL_VALUE,
    KEY_WL_LIFT_COEFF_MODE, KEY_WL_LIFT_COEFF_VALUE,
    KEY_WL_SUPER_AREA_ELEV_MODE, KEY_WL_SUPER_AREA_ELEV_VALUE,
    KEY_WL_SUPER_AREA_PLAIN_MODE, KEY_WL_SUPER_AREA_PLAIN_VALUE,
    KEY_WL_EXPOSED_FRONTAL_MODE, KEY_WL_EXPOSED_FRONTAL_VALUE,
    KEY_WL_WIND_ECC_DECK_VALUE, KEY_WL_WIND_LL_ECC_VALUE,
    KEY_TL_THERMAL_COEFF_STEEL, KEY_TL_THERMAL_COEFF_RCC,
    KEY_DS_REINF_BOUNDS, KEY_DS_TOP_CLEAR_COVER, KEY_DS_BOTTOM_CLEAR_COVER, KEY_DS_SIDE_CLEAR_COVER,
    KEY_DS_STUD_YIELD_STRENGTH, KEY_DS_STUD_ULTIMATE_STRENGTH,
    KEY_DS_STUD_HEIGHT, KEY_DS_STUD_DIAMETER, KEY_DS_STUD_COUNT, KEY_DS_STUD_TRANSVERSE_SPACING,
    KEY_DO_GAMMA_C_BASIC, KEY_DO_GAMMA_C_ACCIDENTAL, KEY_DO_GAMMA_M0, KEY_DO_GAMMA_M1,
    KEY_DO_GAMMA_S, KEY_DO_GAMMA_V, KEY_DO_GAMMA_FLT, KEY_DO_GAMMA_MF,
    KEY_DO_LOAD_CYCLES, KEY_DO_DEFLECTION_LIMIT,
    KEY_MP_GIRDER_TOP_FLANGE_WIDTH, MIN_FOOTPATH_WIDTH,
    MIN_RAILING_HEIGHT,
)
from osdagbridge.core.utils.codes.keyfile import (
    KEY_SAFETY_KERB_MIN_WIDTH,
    KEY_RAILING_MIN_HEIGHT,
    MIN_STUD_HEIGHT_MM,
    MAX_STUD_DIAMETER_FACTOR,
    MIN_EDGE_DISTANCE_MM,
)
from osdagbridge.core.utils.codes.irc5_2015 import IRC5_2015

DELTA = 0.1

@pytest.fixture
def validator():
    return BridgeInputValidator()

@pytest.fixture
def valid_basic_inputs():
    return {
        KEY_SPAN: str(SPAN_MIN + 5),
        KEY_CARRIAGEWAY_WIDTH: str(CARRIAGEWAY_WIDTH_MIN + 1),
        KEY_INCLUDE_MEDIAN: "No",
        KEY_SKEW_ANGLE: str((SKEW_ANGLE_MIN + SKEW_ANGLE_MAX) / 2),
        KEY_FOOTPATH: "None",
        KEY_STRUCTURE_TYPE: "Highway Bridge",
        KEY_PROJECT_LOCATION: "Mumbai",
        KEY_DESIGN_MODE: "Optimized",
        KEY_GIRDER: "E 250A",
        KEY_CROSS_BRACING: "X",
        KEY_END_DIAPHRAGM: "Cross Bracing",
        KEY_DECK_CONCRETE_GRADE_BASIC: "M30"
    }

@pytest.fixture
def valid_additional_inputs():
    return {
        KEY_TS_OVERALL_WIDTH: 10.0,
        KEY_TS_GIRDER_SPACING: 2.5,
        KEY_TS_DECK_OVERHANG: 1.25,
        KEY_TS_NO_OF_GIRDERS: 4,
        KEY_TS_DECK_THICKNESS: 200,
        KEY_TS_FOOTPATH_WIDTH: 1.6,
        KEY_RL_HEIGHT: 1.15,  # in metres
        KEY_DS_STUD_HEIGHT: 120,
        KEY_DS_STUD_DIAMETER: 22,
        KEY_MP_GIRDER_TOP_FLANGE_WIDTH: 0.3,
        KEY_DS_STUD_COUNT: 3,  # Added for cross-field dependencies
        KEY_DS_STUD_TRANSVERSE_SPACING: 30,
        KEY_FOOTPATH: "None",
    }


# ==========================================
# test_validate_span
# FORMAT: span=<metres, float>
#         expect=VALID → validator must accept it
#         expect=INVALID → validator must reject it
# ==========================================

@pytest.mark.parametrize("value, expected_valid", [
    # ── Large negatives (INVALID) ──────────────────────────────────────────
    (-200.0, False),
    (-100.0, False),
    (-50.0,  False),
    (-20.0,  False),
    (-10.0,  False),
    (-5.0,   False),
    (-2.0,   False),
    (-1.0,   False),
    # ── Zero (INVALID) ────────────────────────────────────────────────────
    (0.0,    False),
    # ── Positive but far below SPAN_MIN (INVALID) ─────────────────────────
    # (arbitrary midrange stress values to test a wide spread below the limit)
    (1.0,    False),
    (5.0,    False),
    (8.0,    False),
    (10.0,   False),
    (12.0,   False),
    (15.0,   False),
    (17.0,   False),
    # ── Just below SPAN_MIN (INVALID) ─────────────────────────────────────
    (SPAN_MIN - 10.0,  False),
    (SPAN_MIN - 5.0,   False),
    (SPAN_MIN - 2.0,   False),
    (SPAN_MIN - 1.0,   False),
    (SPAN_MIN - 0.5,   False),
    (SPAN_MIN - 0.1,   False),
    (SPAN_MIN - 0.01,  False),
    # ── Exact SPAN_MIN (VALID) ────────────────────────────────────────────
    (SPAN_MIN,         True),
    # ── Just above SPAN_MIN (VALID) ───────────────────────────────────────
    (SPAN_MIN + 0.01,  True),
    (SPAN_MIN + 0.1,   True),
    (SPAN_MIN + 0.5,   True),
    (SPAN_MIN + 1.0,   True),
    # ── Midrange values spread across the valid range (VALID) ─────────────
    (21.0,  True),
    (22.0,  True),
    (23.0,  True),
    (24.0,  True),
    (25.0,  True),
    (26.0,  True),
    (27.0,  True),
    (28.0,  True),
    (29.0,  True),
    (30.0,  True),
    (31.0,  True),
    (32.0,  True),
    (32.5,  True),
    (33.0,  True),
    (34.0,  True),
    (35.0,  True),
    (36.0,  True),
    (37.0,  True),
    (38.0,  True),
    (39.0,  True),
    (40.0,  True),
    (41.0,  True),
    (42.0,  True),
    (43.0,  True),
    (44.0,  True),
    # ── Just below SPAN_MAX (VALID) ───────────────────────────────────────
    (SPAN_MAX - 1.0,   True),
    (SPAN_MAX - 0.5,   True),
    (SPAN_MAX - 0.1,   True),
    (SPAN_MAX - 0.01,  True),
    # ── Exact SPAN_MAX (VALID) ────────────────────────────────────────────
    (SPAN_MAX,         True),
    # ── Just above SPAN_MAX (INVALID) ─────────────────────────────────────
    (SPAN_MAX + 0.01,  False),
    (SPAN_MAX + 0.1,   False),
    (SPAN_MAX + 0.5,   False),
    (SPAN_MAX + 1.0,   False),
    (SPAN_MAX + 5.0,   False),
    (SPAN_MAX + 10.0,  False),
    (SPAN_MAX + 100.0, False),
    # ── Type / edge-case errors (INVALID) ─────────────────────────────────
    (None,      False),
    ("",        False),
    ("abc",     False),
    ("20",      True),   # string of a valid number → valid (accepted by validator)
    ("20.0",    True),
    ([],        False),
    ({},        False),
])
def test_validate_span(validator, value, expected_valid):
    inputs = {KEY_SPAN: value}
    result = validator.validate_basic_inputs(KEY_SPAN, inputs)
    if expected_valid:
        assert result is None, f"Expected span {value} to be valid"
    else:
        assert result is not None, f"Expected span {value} to be invalid"


# ==========================================
# test_validate_carriageway_width
# FORMAT: median=<Yes/No>  lanes=<int>  width=<metres>
#         expect=VALID / INVALID
# ==========================================

@pytest.mark.parametrize("median, num_lanes, value, expected_valid", [
    # ════════════════════════════════════════════════════════════════════════
    # No Median  (min = CARRIAGEWAY_WIDTH_MIN,  max = CARRIAGEWAY_WIDTH_MAX_LIMIT)
    # ════════════════════════════════════════════════════════════════════════

    # Far below min (INVALID)
    ("No", 1, 0.5,  False),
    ("No", 1, 1.0,  False),
    ("No", 1, 2.0,  False),
    ("No", 1, 2.5,  False),
    ("No", 1, 3.0,  False),
    ("No", 1, 3.5,  False),
    ("No", 1, CARRIAGEWAY_WIDTH_MIN - 0.25, False),
    ("No", 1, CARRIAGEWAY_WIDTH_MIN - 0.01, False),

    # Just below CARRIAGEWAY_WIDTH_MIN (INVALID)
    ("No", 1, CARRIAGEWAY_WIDTH_MIN - 1.0,  False),
    ("No", 1, CARRIAGEWAY_WIDTH_MIN - 0.5,  False),
    ("No", 1, CARRIAGEWAY_WIDTH_MIN - 0.1,  False),
    ("No", 1, CARRIAGEWAY_WIDTH_MIN - 0.01, False),

    # Exact CARRIAGEWAY_WIDTH_MIN (VALID)
    ("No", 1, CARRIAGEWAY_WIDTH_MIN,         True),

    # Just above CARRIAGEWAY_WIDTH_MIN (VALID)
    ("No", 1, CARRIAGEWAY_WIDTH_MIN + 0.01,  True),
    ("No", 1, CARRIAGEWAY_WIDTH_MIN + 0.1,   True),
    ("No", 1, CARRIAGEWAY_WIDTH_MIN + 0.25,  True),
    ("No", 1, CARRIAGEWAY_WIDTH_MIN + 0.0000001, True),
    ("No", 1, CARRIAGEWAY_WIDTH_MIN + 0.05,      True),
    ("No", 1, CARRIAGEWAY_WIDTH_MIN + 0.25,      True),

    # Midrange (arbitrary midrange stress values to test a wide spread) (VALID)
    ("No", 1, 5.0,  True),
    ("No", 1, 5.5,  True),
    ("No", 1, 6.0,  True),
    ("No", 1, 6.5,  True),
    ("No", 1, 7.0,  True),
    ("No", 1, 8.0,  True),
    ("No", 1, 9.0,  True),
    ("No", 1, 10.0, True),
    ("No", 1, 11.0, True),
    ("No", 1, 12.0, True),
    ("No", 1, 13.0, True),
    ("No", 1, 15.0, True),
    ("No", 1, 17.0, True),
    ("No", 1, 19.0, True),
    ("No", 1, 20.0, True),
    ("No", 1, 21.0, True),
    ("No", 1, 22.0, True),
    ("No", 1, 23.0, True),

    # Just below CARRIAGEWAY_WIDTH_MAX_LIMIT (VALID)
    ("No", 1, CARRIAGEWAY_WIDTH_MAX_LIMIT - 1.0,  True),
    ("No", 1, CARRIAGEWAY_WIDTH_MAX_LIMIT - 0.5,  True),
    ("No", 1, CARRIAGEWAY_WIDTH_MAX_LIMIT - 0.1,  True),
    ("No", 1, CARRIAGEWAY_WIDTH_MAX_LIMIT - 0.01, True),

    # Exact CARRIAGEWAY_WIDTH_MAX_LIMIT (VALID)
    ("No", 1, CARRIAGEWAY_WIDTH_MAX_LIMIT,         True),

    # Just above CARRIAGEWAY_WIDTH_MAX_LIMIT (INVALID)
    ("No", 1, CARRIAGEWAY_WIDTH_MAX_LIMIT + 0.01,  False),
    ("No", 1, CARRIAGEWAY_WIDTH_MAX_LIMIT + 0.1,   False),
    ("No", 1, CARRIAGEWAY_WIDTH_MAX_LIMIT + 0.5,   False),
    ("No", 1, CARRIAGEWAY_WIDTH_MAX_LIMIT + 1.0,   False),
    ("No", 1, 25.0,  False),
    ("No", 1, 30.0,  False),

    # Type / edge-case errors (INVALID)
    ("No", 1, None,    False),
    ("No", 1, "",      False),
    ("No", 1, "abc",   False),
    ("No", 1, str(CARRIAGEWAY_WIDTH_MIN),  True),

    # ════════════════════════════════════════════════════════════════════════
    # Yes Median  (min = CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN, max = CARRIAGEWAY_WIDTH_MAX_LIMIT)
    # ════════════════════════════════════════════════════════════════════════

    # Far below min (INVALID)
    ("Yes", 2, 0.5,  False),
    ("Yes", 2, 1.0,  False),
    ("Yes", 2, 2.0,  False),
    ("Yes", 2, 3.0,  False),
    ("Yes", 2, 4.0,  False),
    ("Yes", 2, 5.0,  False),
    ("Yes", 2, 6.0,  False),
    ("Yes", 2, 7.0,  False),

    # Just below CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN (INVALID)
    ("Yes", 2, CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN - 1.0,  False),
    ("Yes", 2, CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN - 0.5,  False),
    ("Yes", 2, CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN - 0.1,  False),
    ("Yes", 2, CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN - 0.01, False),

    # Exact CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN (VALID)
    ("Yes", 2, CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN,         True),

    # Just above CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN (VALID)
    ("Yes", 2, CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN + 0.01,  True),
    ("Yes", 2, CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN + 0.1,   True),
    ("Yes", 2, CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN + 0.5,   True),

    # Midrange (arbitrary midrange stress values to test a wide spread) (VALID)
    ("Yes", 2, 8.0,  True),
    ("Yes", 2, 9.0,  True),
    ("Yes", 2, 10.0, True),
    ("Yes", 2, 11.0, True),
    ("Yes", 2, 12.0, True),
    ("Yes", 2, 14.0, True),
    ("Yes", 2, 15.0, True),
    ("Yes", 2, 17.0, True),
    ("Yes", 2, 19.0, True),
    ("Yes", 2, 20.0, True),
    ("Yes", 2, 21.0, True),
    ("Yes", 2, 22.0, True),
    ("Yes", 2, 23.0, True),

    # Just below CARRIAGEWAY_WIDTH_MAX_LIMIT (VALID)
    ("Yes", 2, CARRIAGEWAY_WIDTH_MAX_LIMIT - 1.0,  True),
    ("Yes", 2, CARRIAGEWAY_WIDTH_MAX_LIMIT - 0.5,  True),
    ("Yes", 2, CARRIAGEWAY_WIDTH_MAX_LIMIT - 0.1,  True),
    ("Yes", 2, CARRIAGEWAY_WIDTH_MAX_LIMIT - 0.01, True),

    # Exact CARRIAGEWAY_WIDTH_MAX_LIMIT (VALID)
    ("Yes", 2, CARRIAGEWAY_WIDTH_MAX_LIMIT,         True),

    # Just above CARRIAGEWAY_WIDTH_MAX_LIMIT (INVALID)
    ("Yes", 2, CARRIAGEWAY_WIDTH_MAX_LIMIT + 0.01,  False),
    ("Yes", 2, CARRIAGEWAY_WIDTH_MAX_LIMIT + 0.1,   False),
    ("Yes", 2, CARRIAGEWAY_WIDTH_MAX_LIMIT + 1.0,   False),
    ("Yes", 2, CARRIAGEWAY_WIDTH_MAX_LIMIT + 2.0,   False),
    ("Yes", 2, 25.0,  False),
    ("Yes", 2, 30.0,  False),

    # Type / edge-case errors (INVALID)
    ("Yes", 2, None,   False),
    ("Yes", 2, "",     False),
    ("Yes", 2, "abc",  False),
    ("Yes", 2, str(CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN),  True),
])
def test_validate_carriageway_width(validator, median, num_lanes, value, expected_valid):
    inputs = {KEY_CARRIAGEWAY_WIDTH: value, KEY_INCLUDE_MEDIAN: median}
    result = validator.validate_basic_inputs(KEY_CARRIAGEWAY_WIDTH, inputs)

    val_as_float = None
    if value is not None:
        try:
            val_as_float = float(value)
        except (ValueError, TypeError):
            pass

    required_width = IRC5_2015.cl_104_3_1_carriageway_width(
        val_as_float if val_as_float is not None else 0, num_lanes
    )

    if expected_valid and val_as_float is not None \
            and val_as_float >= required_width and val_as_float <= CARRIAGEWAY_WIDTH_MAX_LIMIT:
        assert result is None, f"Expected carriageway width {value} with median {median} to be valid"
    elif expected_valid:
        assert result is not None
    else:
        assert result is not None, f"Expected carriageway width {value} with median {median} to be invalid"


# ==========================================
# test_validate_skew_angle
# FORMAT: angle=<degrees, float>   valid range SKEW_ANGLE_MIN..SKEW_ANGLE_MAX
#         expect=VALID / INVALID
# ==========================================

@pytest.mark.parametrize("value, expected_valid", [
    # ── Large negatives way below SKEW_ANGLE_MIN (INVALID) ────────────────
    (-100.0, False),
    (-50.0,  False),
    (-30.0,  False),
    (-20.0,  False),
    (-16.0,  False),

    # ── Just below SKEW_ANGLE_MIN (INVALID) ───────────────────────────────
    (SKEW_ANGLE_MIN - 10.0,  False),
    (SKEW_ANGLE_MIN - 5.0,   False),
    (SKEW_ANGLE_MIN - 1.0,   False),
    (SKEW_ANGLE_MIN - 0.5,   False),
    (SKEW_ANGLE_MIN - 0.1,   False),
    (SKEW_ANGLE_MIN - 0.01,  False),

    # ── Exact SKEW_ANGLE_MIN (VALID) ──────────────────────────────────────
    (SKEW_ANGLE_MIN,          True),

    # ── Just above SKEW_ANGLE_MIN (VALID) ─────────────────────────────────
    (SKEW_ANGLE_MIN + 0.01,   True),
    (SKEW_ANGLE_MIN + 0.1,    True),
    (SKEW_ANGLE_MIN + 0.5,    True),

    # ── Step through negative portion of valid range (VALID) ──────────────
    (-14.0, True),
    (-13.0, True),
    (-12.0, True),
    (-11.0, True),
    (-10.0, True),
    (-9.0,  True),
    (-8.0,  True),
    (-7.0,  True),
    (-6.0,  True),
    (-5.0,  True),
    (-4.0,  True),
    (-3.0,  True),
    (-2.0,  True),
    (-1.0,  True),

    # ── Zero (VALID) ──────────────────────────────────────────────────────
    (0.0,   True),

    # ── Step through positive portion of valid range (VALID) ──────────────
    (1.0,   True),
    (2.0,   True),
    (3.0,   True),
    (4.0,   True),
    (5.0,   True),
    (6.0,   True),
    (7.0,   True),
    (8.0,   True),
    (9.0,   True),
    (10.0,  True),
    (11.0,  True),
    (12.0,  True),
    (13.0,  True),
    (14.0,  True),

    # ── Just below SKEW_ANGLE_MAX (VALID) ─────────────────────────────────
    (SKEW_ANGLE_MAX - 0.5,   True),
    (SKEW_ANGLE_MAX - 0.1,   True),
    (SKEW_ANGLE_MAX - 0.01,  True),

    # ── Exact SKEW_ANGLE_MAX (VALID) ──────────────────────────────────────
    (SKEW_ANGLE_MAX,          True),

    # ── Just above SKEW_ANGLE_MAX (INVALID) ───────────────────────────────
    (SKEW_ANGLE_MAX + 0.01,   False),
    (SKEW_ANGLE_MAX + 0.1,    False),
    (SKEW_ANGLE_MAX + 0.5,    False),
    (SKEW_ANGLE_MAX + 1.0,    False),
    (SKEW_ANGLE_MAX + 5.0,    False),
    (SKEW_ANGLE_MAX + 10.0,   False),

    # ── Large positives way above SKEW_ANGLE_MAX (INVALID) ────────────────
    (20.0,  False),
    (25.0,  False),
    (30.0,  False),
    (50.0,  False),
    (100.0, False),

    # ── Type / edge-case errors (INVALID) ─────────────────────────────────
    (None,    False),
    ("",      False),
    ("abc",   False),
    ("0",     True),
    ("15",    True),
])
def test_validate_skew_angle(validator, value, expected_valid):
    inputs = {KEY_SKEW_ANGLE: value}
    result = validator.validate_basic_inputs(KEY_SKEW_ANGLE, inputs)
    if expected_valid:
        assert result is None, f"Expected skew angle {value} to be valid"
    else:
        assert result is not None, f"Expected skew angle {value} to be invalid"


# ── Layout Fields ──────────────────────────────────────────────────────
# KEY_TS_GIRDER_SPACING: 0.5 – max(overall_width/2)
@pytest.mark.parametrize("spacing, overall_w, expected_valid", [
    (0.3, 10.0, False),  # below 0.5
    (0.5, 10.0, True),   # at minimum
    (1.0, 10.0, True),   # midrange
    (4.9, 10.0, True),   # just below max 5.0
    (5.0, 10.0, True),   # at maximum
    (5.1, 10.0, False),  # above maximum
    (None, 10.0, False), # None → error with fallback 0.5
])
def test_validate_ts_girder_spacing(validator, valid_additional_inputs, spacing, overall_w, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_TS_OVERALL_WIDTH] = overall_w
    inputs[KEY_TS_GIRDER_SPACING] = spacing
    result = validator.validate_additional_inputs(KEY_TS_GIRDER_SPACING, inputs)
    if expected_valid and spacing is not None:
        assert result is None, f"Expected spacing {spacing} to be valid, got {result}"
    else:
        assert result is not None, f"Expected spacing {spacing} to be invalid, got None"


# KEY_TS_NO_OF_GIRDERS: 2 – ceil(2*overall_width)
@pytest.mark.parametrize("n_girders, overall_w, expected_valid", [
    (1, 10.0, False),    # below 2
    (2, 10.0, True),     # at minimum
    (5, 10.0, True),     # midrange
    (19, 10.0, True),    # just below max 20
    (20, 10.0, True),    # at maximum
    (21, 10.0, False),   # above maximum
    (None, 10.0, False), # None → error with fallback 2
])
def test_validate_ts_no_of_girders(validator, valid_additional_inputs, n_girders, overall_w, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_TS_OVERALL_WIDTH] = overall_w
    inputs[KEY_TS_NO_OF_GIRDERS] = n_girders
    result = validator.validate_additional_inputs(KEY_TS_NO_OF_GIRDERS, inputs)
    if expected_valid and n_girders is not None:
        assert result is None, f"Expected n_girders {n_girders} to be valid, got {result}"
    else:
        assert result is not None, f"Expected n_girders {n_girders} to be invalid, got None"


# KEY_TS_DECK_OVERHANG: 0.0 – max(overall_width/2)
@pytest.mark.parametrize("overhang, overall_w, expected_valid", [
    (-0.1, 10.0, False),  # negative
    (0.0, 10.0, True),    # at minimum
    (2.0, 10.0, True),    # midrange
    (4.9, 10.0, True),    # just below max 5.0
    (5.0, 10.0, True),    # at maximum
    (5.1, 10.0, False),   # above maximum
    (None, 10.0, False),  # None → error with fallback 0.0
])
def test_validate_ts_deck_overhang(validator, valid_additional_inputs, overhang, overall_w, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_TS_OVERALL_WIDTH] = overall_w
    inputs[KEY_TS_DECK_OVERHANG] = overhang
    result = validator.validate_additional_inputs(KEY_TS_DECK_OVERHANG, inputs)
    if expected_valid and overhang is not None:
        assert result is None, f"Expected overhang {overhang} to be valid, got {result}"
    else:
        assert result is not None, f"Expected overhang {overhang} to be invalid, got None"


# Deck Details
# KEY_TS_DECK_THICKNESS: 100–500 mm
@pytest.mark.parametrize("thickness, expected_valid", [
    (50, False),     # below 100
    (100, True),     # at minimum
    (300, True),     # midrange
    (500, True),     # at maximum
    (600, False),    # above 500
    (None, False),   # None → error with fallback 200
])
def test_validate_ts_deck_thickness(validator, valid_additional_inputs, thickness, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_TS_DECK_THICKNESS] = thickness
    result = validator.validate_additional_inputs(KEY_TS_DECK_THICKNESS, inputs)
    if expected_valid and thickness is not None:
        assert result is None, f"Expected thickness {thickness} to be valid, got {result}"
    else:
        assert result is not None, f"Expected thickness {thickness} to be invalid, got None"


# KEY_TS_FOOTPATH_THICKNESS: 100–500 mm
@pytest.mark.parametrize("thickness, expected_valid", [
    (50, False),
    (100, True),
    (300, True),
    (500, True),
    (600, False),
    (None, False),
])
def test_validate_ts_footpath_thickness(validator, valid_additional_inputs, thickness, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_TS_FOOTPATH_THICKNESS] = thickness
    result = validator.validate_additional_inputs(KEY_TS_FOOTPATH_THICKNESS, inputs)
    if expected_valid and thickness is not None:
        assert result is None
    else:
        assert result is not None


# Crash Barrier - WIDTH (0–max(overall_width/2))
@pytest.mark.parametrize("cb_width, overall_w, expected_valid", [
    (-0.1, 10.0, False),
    (0.0, 10.0, True),
    (2.5, 10.0, True),
    (5.0, 10.0, True),
    (5.1, 10.0, False),
    (None, 10.0, False),
])
def test_validate_cb_width(validator, valid_additional_inputs, cb_width, overall_w, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_TS_OVERALL_WIDTH] = overall_w
    inputs[KEY_CB_WIDTH] = cb_width
    result = validator.validate_additional_inputs(KEY_CB_WIDTH, inputs)
    if expected_valid and cb_width is not None:
        assert result is None
    else:
        assert result is not None


# Crash Barrier - HEIGHT (0–10.0)
@pytest.mark.parametrize("cb_height, expected_valid", [
    (-0.5, False),
    (0.0, True),
    (5.0, True),
    (10.0, True),
    (10.1, False),
    (None, False),
])
def test_validate_cb_height(validator, valid_additional_inputs, cb_height, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_CB_HEIGHT] = cb_height
    result = validator.validate_additional_inputs(KEY_CB_HEIGHT, inputs)
    if expected_valid and cb_height is not None:
        assert result is None
    else:
        assert result is not None


# Crash Barrier - LOAD (0–100.0)
@pytest.mark.parametrize("cb_load, expected_valid", [
    (-1.0, False),
    (0.0, True),
    (50.0, True),
    (100.0, True),
    (100.1, False),
    (None, False),
])
def test_validate_cb_load(validator, valid_additional_inputs, cb_load, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_CB_LOAD] = cb_load
    result = validator.validate_additional_inputs(KEY_CB_LOAD, inputs)
    if expected_valid and cb_load is not None:
        assert result is None
    else:
        assert result is not None


# Crash Barrier - POST_SPACING (0.1–span)
@pytest.mark.parametrize("cb_spacing, span, expected_valid", [
    (0.05, 30.0, False),
    (0.1, 30.0, True),
    (15.0, 30.0, True),
    (30.0, 30.0, True),
    (30.1, 30.0, False),
    (None, 30.0, False),
])
def test_validate_cb_post_spacing(validator, valid_additional_inputs, cb_spacing, span, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_SPAN] = span
    inputs[KEY_CB_POST_SPACING] = cb_spacing
    result = validator.validate_additional_inputs(KEY_CB_POST_SPACING, inputs)
    if expected_valid and cb_spacing is not None:
        assert result is None
    else:
        assert result is not None


# Median - WIDTH (0–max(overall_width/2))
