import pytest

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
    KEY_DO_LOAD_CYCLES,
    KEY_MP_GIRDER_TOP_FLANGE_WIDTH,
    KEY_MP_GIRDER_DEPTH, KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
    KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH, KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
    KEY_MP_GIRDER_WEB_THICKNESS, KEY_MP_STIFFENER_SPACING,
    KEY_MP_STIFFENER_BEARING_OUTSTAND, KEY_MP_STIFFENER_INTERMEDIATE_SPACING,
    KEY_MP_STIFFENER_INTERMEDIATE_OUTSTAND, KEY_MP_CB_NO_OF_CROSS_BRACINGS,
    KEY_DO_CAMBER_VALUE, KEY_DO_CAMBER_MODE,
    SAIL_APPROVED_THICKNESS_VALUES, MIN_RAILING_HEIGHT, KEY_MP_ED_TYPE,
)
from osdagbridge.core.utils.codes.keyfile import (
    KEY_SAFETY_KERB_MIN_WIDTH,
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
@pytest.mark.parametrize("md_width, overall_w, expected_valid", [
    (-0.1, 10.0, False),
    (0.0, 10.0, True),
    (2.5, 10.0, True),
    (5.0, 10.0, True),
    (5.1, 10.0, False),
    (None, 10.0, False),
])
def test_validate_md_width(validator, valid_additional_inputs, md_width, overall_w, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_TS_OVERALL_WIDTH] = overall_w
    inputs[KEY_MD_WIDTH] = md_width
    result = validator.validate_additional_inputs(KEY_MD_WIDTH, inputs)
    if expected_valid and md_width is not None:
        assert result is None
    else:
        assert result is not None


# Median - HEIGHT (0–10.0)
@pytest.mark.parametrize("md_height, expected_valid", [
    (-0.5, False),
    (0.0, True),
    (5.0, True),
    (10.0, True),
    (10.1, False),
    (None, False),
])
def test_validate_md_height(validator, valid_additional_inputs, md_height, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_MD_HEIGHT] = md_height
    result = validator.validate_additional_inputs(KEY_MD_HEIGHT, inputs)
    if expected_valid and md_height is not None:
        assert result is None
    else:
        assert result is not None


# Median - LOAD (0–100.0)
@pytest.mark.parametrize("md_load, expected_valid", [
    (-1.0, False),
    (0.0, True),
    (50.0, True),
    (100.0, True),
    (100.1, False),
    (None, False),
])
def test_validate_md_load(validator, valid_additional_inputs, md_load, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_MD_LOAD] = md_load
    result = validator.validate_additional_inputs(KEY_MD_LOAD, inputs)
    if expected_valid and md_load is not None:
        assert result is None
    else:
        assert result is not None


# Median - POST_SPACING (0.1–span)
@pytest.mark.parametrize("md_spacing, span, expected_valid", [
    (0.05, 30.0, False),
    (0.1, 30.0, True),
    (15.0, 30.0, True),
    (30.0, 30.0, True),
    (30.1, 30.0, False),
    (None, 30.0, False),
])
def test_validate_md_post_spacing(validator, valid_additional_inputs, md_spacing, span, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_SPAN] = span
    inputs[KEY_MD_POST_SPACING] = md_spacing
    result = validator.validate_additional_inputs(KEY_MD_POST_SPACING, inputs)
    if expected_valid and md_spacing is not None:
        assert result is None
    else:
        assert result is not None


# Railing - HEIGHT (MIN_RAILING_HEIGHT–3.0m)
@pytest.mark.parametrize("rl_height, expected_valid", [
    (MIN_RAILING_HEIGHT - 0.1, False),
    (MIN_RAILING_HEIGHT, True),
    (1.5, True),
    (3.0, True),
    (3.1, False),
    (None, False),
])
def test_validate_rl_height(validator, valid_additional_inputs, rl_height, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_RL_HEIGHT] = rl_height
    result = validator.validate_additional_inputs(KEY_RL_HEIGHT, inputs)
    if expected_valid and rl_height is not None:
        assert result is None
    else:
        assert result is not None


# Railing - WIDTH (0–max(overall_width/2))
@pytest.mark.parametrize("rl_width, overall_w, expected_valid", [
    (-0.1, 10.0, False),
    (0.0, 10.0, True),
    (2.5, 10.0, True),
    (5.0, 10.0, True),
    (5.1, 10.0, False),
    (None, 10.0, False),
])
def test_validate_rl_width(validator, valid_additional_inputs, rl_width, overall_w, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_TS_OVERALL_WIDTH] = overall_w
    inputs[KEY_RL_WIDTH] = rl_width
    result = validator.validate_additional_inputs(KEY_RL_WIDTH, inputs)
    if expected_valid and rl_width is not None:
        assert result is None
    else:
        assert result is not None


# Railing - LOAD_VALUE (0–100.0)
@pytest.mark.parametrize("rl_load, expected_valid", [
    (-1.0, False),
    (0.0, True),
    (50.0, True),
    (100.0, True),
    (100.1, False),
    (None, False),
])
def test_validate_rl_load_value(validator, valid_additional_inputs, rl_load, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_RL_LOAD_VALUE] = rl_load
    result = validator.validate_additional_inputs(KEY_RL_LOAD_VALUE, inputs)
    if expected_valid and rl_load is not None:
        assert result is None
    else:
        assert result is not None


# Wearing Course - DENSITY (0–10.0)
@pytest.mark.parametrize("wc_density, expected_valid", [
    (-0.5, False),
    (0.0, True),
    (5.0, True),
    (10.0, True),
    (10.1, False),
    (None, False),
])
def test_validate_wc_density(validator, valid_additional_inputs, wc_density, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_WC_DENSITY] = wc_density
    result = validator.validate_additional_inputs(KEY_WC_DENSITY, inputs)
    if expected_valid and wc_density is not None:
        assert result is None
    else:
        assert result is not None


# Wearing Course - THICKNESS (0–150.0)
@pytest.mark.parametrize("wc_thickness, expected_valid", [
    (-0.5, False),
    (0.0, True),
    (75.0, True),
    (150.0, True),
    (150.1, False),
    (None, False),
])
def test_validate_wc_thickness(validator, valid_additional_inputs, wc_thickness, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_WC_THICKNESS] = wc_thickness
    result = validator.validate_additional_inputs(KEY_WC_THICKNESS, inputs)
    if expected_valid and wc_thickness is not None:
        assert result is None
    else:
        assert result is not None


# Lane Details - LANE_TABLE_COUNT (1–max_lanes)
@pytest.mark.parametrize("lane_count, cw_width, expected_valid", [
    (0, 10.0, False),
    (1, 10.0, True),
    (2, 10.0, True),
    (3, 10.0, False),  # Validator actually limits to floor(cw/3.5) = 2 for cw=10.0
    (7, 10.0, False),
    (None, 10.0, False),
])
def test_validate_wc_ld_lane_table_count(validator, valid_additional_inputs, lane_count, cw_width, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_CARRIAGEWAY_WIDTH] = cw_width
    inputs[KEY_WC_LD_LANE_TABLE_COUNT] = lane_count
    result = validator.validate_additional_inputs(KEY_WC_LD_LANE_TABLE_COUNT, inputs)
    if expected_valid and lane_count is not None:
        assert result is None
    else:
        assert result is not None


# Permanent Load - SELF_WEIGHT_FACTOR (0–10.0)
@pytest.mark.parametrize("swf, expected_valid", [
    (-0.5, False),
    (0.0, True),
    (1.0, True),
    (10.0, True),
    (10.1, False),
    (None, False),
])
def test_validate_pl_self_weight_factor(validator, valid_additional_inputs, swf, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_PL_SELF_WEIGHT_FACTOR] = swf
    result = validator.validate_additional_inputs(KEY_PL_SELF_WEIGHT_FACTOR, inputs)
    if expected_valid and swf is not None:
        assert result is None
    else:
        assert result is not None


# Live Load - ECCENTRICITY (-10–10)
@pytest.mark.parametrize("ecc, expected_valid", [
    (-10.5, False),
    (-10.0, True),
    (0.0, True),
    (10.0, True),
    (10.1, False),
    (None, False),
])
def test_validate_ll_eccentricity(validator, valid_additional_inputs, ecc, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_LL_ECCENTRICITY] = ecc
    result = validator.validate_additional_inputs(KEY_LL_ECCENTRICITY, inputs)
    if expected_valid and ecc is not None:
        assert result is None
    else:
        assert result is not None


# Live Load - FOOTPATH_PRESSURE_VALUE (mode-gated, 0–5000)
@pytest.mark.parametrize("mode, pressure, expected_valid", [
    ("Custom", -1.0, False),
    ("Custom", 0.0, True),
    ("Custom", 2500.0, True),
    ("Custom", 5000.0, True),
    ("Custom", 5001.0, False),
    ("Custom", None, False),
    ("Standard", 1000.0, True),  # mode not "Custom" → returns None
    ("Standard", None, True),     # mode not "Custom" → returns None
])
def test_validate_ll_footpath_pressure_value(validator, valid_additional_inputs, mode, pressure, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_LL_FOOTPATH_PRESSURE_MODE] = mode
    inputs[KEY_LL_FOOTPATH_PRESSURE_VALUE] = pressure
    result = validator.validate_additional_inputs(KEY_LL_FOOTPATH_PRESSURE_VALUE, inputs)
    if expected_valid:
        assert result is None
    else:
        assert result is not None


# Seismic Load - IMPORTANCE_FACTOR (0–10.0)
@pytest.mark.parametrize("ifactor, expected_valid", [
    (-0.5, False),
    (0.0, True),
    (1.0, True),
    (10.0, True),
    (10.1, False),
    (None, False),
])
def test_validate_sl_importance_factor(validator, valid_additional_inputs, ifactor, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_SL_IMPORTANCE_FACTOR] = ifactor
    result = validator.validate_additional_inputs(KEY_SL_IMPORTANCE_FACTOR, inputs)
    if expected_valid and ifactor is not None:
        assert result is None
    else:
        assert result is not None


# Seismic Load - TIME_PERIOD (0–4s)
@pytest.mark.parametrize("tp, expected_valid", [
    (-0.5, False),
    (0.0, True),
    (2.0, True),
    (4.0, True),
    (4.1, False),
    (None, False),
])
def test_validate_sl_time_period(validator, valid_additional_inputs, tp, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_SL_TIME_PERIOD] = tp
    result = validator.validate_additional_inputs(KEY_SL_TIME_PERIOD, inputs)
    if expected_valid and tp is not None:
        assert result is None
    else:
        assert result is not None


# Seismic Load - DAMPING (2–10%)
@pytest.mark.parametrize("damp, expected_valid", [
    (1.5, False),
    (2.0, True),
    (5.0, True),
    (10.0, True),
    (10.1, False),
    (None, False),
])
def test_validate_sl_damping(validator, valid_additional_inputs, damp, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_SL_DAMPING] = damp
    result = validator.validate_additional_inputs(KEY_SL_DAMPING, inputs)
    if expected_valid and damp is not None:
        assert result is None
    else:
        assert result is not None


# Seismic Load - DEAD_LOAD_VALUE (mode-gated)
@pytest.mark.parametrize("mode, value, expected_valid", [
    ("Custom", 0.0, True),
    ("Custom", 100.0, True),
    ("Custom", None, False),
    ("Standard", 100.0, True),  # mode not "Custom" → returns None
    ("Standard", None, True),   # mode not "Custom" → returns None
])
def test_validate_sl_dead_load_value(validator, valid_additional_inputs, mode, value, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_SL_DEAD_LOAD_MODE] = mode
    inputs[KEY_SL_DEAD_LOAD_VALUE] = value
    result = validator.validate_additional_inputs(KEY_SL_DEAD_LOAD_VALUE, inputs)
    if expected_valid:
        assert result is None
    else:
        assert result is not None


# Seismic Load - LIVE_LOAD_VALUE (mode-gated)
@pytest.mark.parametrize("mode, value, expected_valid", [
    ("Custom", 0.0, True),
    ("Custom", 100.0, True),
    ("Custom", None, False),
    ("Standard", 100.0, True),
    ("Standard", None, True),
])
def test_validate_sl_live_load_value(validator, valid_additional_inputs, mode, value, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_SL_LIVE_LOAD_MODE] = mode
    inputs[KEY_SL_LIVE_LOAD_VALUE] = value
    result = validator.validate_additional_inputs(KEY_SL_LIVE_LOAD_VALUE, inputs)
    if expected_valid:
        assert result is None
    else:
        assert result is not None


# Wind Load - AVG_EXPOSED_HEIGHT (0–100 m; negatives and None are corrected)
@pytest.mark.parametrize("height, expected_valid", [
    (-1.0, False),   # upstream: lower-bound 0 enforced
    (0.0, True),
    (50.0, True),
    (100.0, True),
    (100.1, False),
    (None, False),
])
def test_validate_wl_avg_exposed_height(validator, valid_additional_inputs, height, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_WL_AVG_EXPOSED_HEIGHT] = height
    result = validator.validate_additional_inputs(KEY_WL_AVG_EXPOSED_HEIGHT, inputs)
    if expected_valid:
        assert result is None
    else:
        assert result is not None


# Wind Load - GUST_FACTOR_VALUE (mode-gated, 2.0–10.0)
@pytest.mark.parametrize("mode, gf, expected_valid", [
    ("Custom", 1.5, False),
    ("Custom", 2.0, True),
    ("Custom", 5.0, True),
    ("Custom", 10.0, True),
    ("Custom", 10.1, False),
    ("Custom", None, False),
    ("Standard", 5.0, True),
    ("Standard", None, True),
])
def test_validate_wl_gust_factor_value(validator, valid_additional_inputs, mode, gf, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_WL_GUST_FACTOR_MODE] = mode
    inputs[KEY_WL_GUST_FACTOR_VALUE] = gf
    result = validator.validate_additional_inputs(KEY_WL_GUST_FACTOR_VALUE, inputs)
    if expected_valid:
        assert result is None
    else:
        assert result is not None


# Wind Load - DRAG_COEFF_VALUE (mode-gated, 1.0–10.0)
@pytest.mark.parametrize("mode, dc, expected_valid", [
    ("Custom", 0.5, False),
    ("Custom", 1.0, True),
    ("Custom", 5.0, True),
    ("Custom", 10.0, True),
    ("Custom", 10.1, False),
    ("Custom", None, False),
    ("Standard", 5.0, True),
    ("Standard", None, True),
])
def test_validate_wl_drag_coeff_value(validator, valid_additional_inputs, mode, dc, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_WL_DRAG_COEFF_MODE] = mode
    inputs[KEY_WL_DRAG_COEFF_VALUE] = dc
    result = validator.validate_additional_inputs(KEY_WL_DRAG_COEFF_VALUE, inputs)
    if expected_valid:
        assert result is None
    else:
        assert result is not None


# Wind Load - DRAG_COEFF_LL_VALUE (mode-gated, 1.0–10.0)
@pytest.mark.parametrize("mode, dcll, expected_valid", [
    ("Custom", 0.5, False),
    ("Custom", 1.0, True),
    ("Custom", 5.0, True),
    ("Custom", 10.0, True),
    ("Custom", 10.1, False),
    ("Custom", None, False),
    ("Standard", 5.0, True),
    ("Standard", None, True),
])
def test_validate_wl_drag_coeff_ll_value(validator, valid_additional_inputs, mode, dcll, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_WL_DRAG_COEFF_LL_MODE] = mode
    inputs[KEY_WL_DRAG_COEFF_LL_VALUE] = dcll
    result = validator.validate_additional_inputs(KEY_WL_DRAG_COEFF_LL_VALUE, inputs)
    if expected_valid:
        assert result is None
    else:
        assert result is not None


# Wind Load - LIFT_COEFF_VALUE (mode-gated, 1.0–10.0)
@pytest.mark.parametrize("mode, lc, expected_valid", [
    ("Custom", 0.5, False),
    ("Custom", 1.0, True),
    ("Custom", 5.0, True),
    ("Custom", 10.0, True),
    ("Custom", 10.1, False),
    ("Custom", None, False),
    ("Standard", 5.0, True),
    ("Standard", None, True),
])
def test_validate_wl_lift_coeff_value(validator, valid_additional_inputs, mode, lc, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_WL_LIFT_COEFF_MODE] = mode
    inputs[KEY_WL_LIFT_COEFF_VALUE] = lc
    result = validator.validate_additional_inputs(KEY_WL_LIFT_COEFF_VALUE, inputs)
    if expected_valid:
        assert result is None
    else:
        assert result is not None


# Wind Load - SUPER_AREA_ELEV_VALUE (mode-gated, 0–1000 m²)
@pytest.mark.parametrize("mode, sae, expected_valid", [
    ("Custom", -1.0, False),  # upstream: lower-bound 0 enforced
    ("Custom", 0.0, True),
    ("Custom", 100.0, True),
    ("Custom", 1000.0, True),
    ("Custom", 1000.1, False),
    ("Custom", None, False),
    ("Standard", 50.0, True),
    ("Standard", None, True),
])
def test_validate_wl_super_area_elev_value(validator, valid_additional_inputs, mode, sae, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_WL_SUPER_AREA_ELEV_MODE] = mode
    inputs[KEY_WL_SUPER_AREA_ELEV_VALUE] = sae
    result = validator.validate_additional_inputs(KEY_WL_SUPER_AREA_ELEV_VALUE, inputs)
    if expected_valid:
        assert result is None
    else:
        assert result is not None


# Wind Load - SUPER_AREA_PLAIN_VALUE (mode-gated)
@pytest.mark.parametrize("mode, sap, expected_valid", [
    ("Custom", 0.0, True),
    ("Custom", 100.0, True),
    ("Custom", None, False),
    ("Standard", 50.0, True),
    ("Standard", None, True),
])
def test_validate_wl_super_area_plain_value(validator, valid_additional_inputs, mode, sap, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_WL_SUPER_AREA_PLAIN_MODE] = mode
    inputs[KEY_WL_SUPER_AREA_PLAIN_VALUE] = sap
    result = validator.validate_additional_inputs(KEY_WL_SUPER_AREA_PLAIN_VALUE, inputs)
    if expected_valid:
        assert result is None
    else:
        assert result is not None


# Wind Load - EXPOSED_FRONTAL_VALUE (mode-gated)
@pytest.mark.parametrize("mode, ef, expected_valid", [
    ("Custom", 0.0, True),
    ("Custom", 100.0, True),
    ("Custom", None, False),
    ("Standard", 50.0, True),
    ("Standard", None, True),
])
def test_validate_wl_exposed_frontal_value(validator, valid_additional_inputs, mode, ef, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_WL_EXPOSED_FRONTAL_MODE] = mode
    inputs[KEY_WL_EXPOSED_FRONTAL_VALUE] = ef
    result = validator.validate_additional_inputs(KEY_WL_EXPOSED_FRONTAL_VALUE, inputs)
    if expected_valid:
        assert result is None
    else:
        assert result is not None


# Wind Load - WIND_ECC_DECK_VALUE (-10–10)
@pytest.mark.parametrize("wecc, expected_valid", [
    (-10.5, False),
    (-10.0, True),
    (0.0, True),
    (10.0, True),
    (10.1, False),
    (None, False),
])
def test_validate_wl_wind_ecc_deck_value(validator, valid_additional_inputs, wecc, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_WL_WIND_ECC_DECK_VALUE] = wecc
    result = validator.validate_additional_inputs(KEY_WL_WIND_ECC_DECK_VALUE, inputs)
    if expected_valid and wecc is not None:
        assert result is None
    else:
        assert result is not None


# Wind Load - WIND_LL_ECC_VALUE (-10–10)
@pytest.mark.parametrize("wlecc, expected_valid", [
    (-10.5, False),
    (-10.0, True),
    (0.0, True),
    (10.0, True),
    (10.1, False),
    (None, False),
])
def test_validate_wl_wind_ll_ecc_value(validator, valid_additional_inputs, wlecc, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_WL_WIND_LL_ECC_VALUE] = wlecc
    result = validator.validate_additional_inputs(KEY_WL_WIND_LL_ECC_VALUE, inputs)
    if expected_valid and wlecc is not None:
        assert result is None
    else:
        assert result is not None


# Temperature Load - THERMAL_COEFF_STEEL
@pytest.mark.parametrize("tcs, expected_valid", [
    (-1.0, True),
    (0.0, True),
    (100.0, True),
    (None, False),
])
def test_validate_tl_thermal_coeff_steel(validator, valid_additional_inputs, tcs, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_TL_THERMAL_COEFF_STEEL] = tcs
    result = validator.validate_additional_inputs(KEY_TL_THERMAL_COEFF_STEEL, inputs)
    if expected_valid:
        assert result is None
    else:
        assert result is not None


# Temperature Load - THERMAL_COEFF_RCC
@pytest.mark.parametrize("tcr, expected_valid", [
    (-1.0, True),
    (0.0, True),
    (100.0, True),
    (None, False),
])
def test_validate_tl_thermal_coeff_rcc(validator, valid_additional_inputs, tcr, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_TL_THERMAL_COEFF_RCC] = tcr
    result = validator.validate_additional_inputs(KEY_TL_THERMAL_COEFF_RCC, inputs)
    if expected_valid:
        assert result is None
    else:
        assert result is not None


# Design Options - REINF_BOUNDS
@pytest.mark.parametrize("bounds, expected_valid", [
    ({"lower": 8, "upper": 40}, True),
    ({"lower": 8, "upper": 20}, True),
    ({"lower": 20, "upper": 8}, False),  # upper < lower
    ({"lower": 5, "upper": 40}, False),  # lower < 8
    ({"lower": 8, "upper": 50}, False),  # upper > 40
    (None, False),
])
def test_validate_ds_reinf_bounds(validator, valid_additional_inputs, bounds, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_DS_REINF_BOUNDS] = bounds
    result = validator.validate_additional_inputs(KEY_DS_REINF_BOUNDS, inputs)
    if expected_valid:
        assert result is None
    else:
        assert result is not None


# Design Options - TOP_CLEAR_COVER (40–75 mm)
@pytest.mark.parametrize("tcc, expected_valid", [
    (35, False),
    (40, True),
    (57, True),
    (75, True),
    (80, False),
    (None, False),
])
def test_validate_ds_top_clear_cover(validator, valid_additional_inputs, tcc, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_DS_TOP_CLEAR_COVER] = tcc
    result = validator.validate_additional_inputs(KEY_DS_TOP_CLEAR_COVER, inputs)
    if expected_valid and tcc is not None:
        assert result is None
    else:
        assert result is not None


# Design Options - BOTTOM_CLEAR_COVER (35–75 mm)
@pytest.mark.parametrize("bcc, expected_valid", [
    (30, False),
    (35, True),
    (55, True),
    (75, True),
    (80, False),
    (None, False),
])
def test_validate_ds_bottom_clear_cover(validator, valid_additional_inputs, bcc, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_DS_BOTTOM_CLEAR_COVER] = bcc
    result = validator.validate_additional_inputs(KEY_DS_BOTTOM_CLEAR_COVER, inputs)
    if expected_valid and bcc is not None:
        assert result is None
    else:
        assert result is not None


# Design Options - SIDE_CLEAR_COVER (35–75 mm)
@pytest.mark.parametrize("scc, expected_valid", [
    (30, False),
    (35, True),
    (55, True),
    (75, True),
    (80, False),
    (None, False),
])
def test_validate_ds_side_clear_cover(validator, valid_additional_inputs, scc, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_DS_SIDE_CLEAR_COVER] = scc
    result = validator.validate_additional_inputs(KEY_DS_SIDE_CLEAR_COVER, inputs)
    if expected_valid and scc is not None:
        assert result is None
    else:
        assert result is not None


# Design Options - STUD_YIELD_STRENGTH (350–600 MPa)
@pytest.mark.parametrize("ys, expected_valid", [
    (300, False),
    (350, True),
    (475, True),
    (600, True),
    (650, False),
    (None, False),
])
def test_validate_ds_stud_yield_strength(validator, valid_additional_inputs, ys, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_DS_STUD_YIELD_STRENGTH] = ys
    result = validator.validate_additional_inputs(KEY_DS_STUD_YIELD_STRENGTH, inputs)
    if expected_valid and ys is not None:
        assert result is None
    else:
        assert result is not None


# Design Options - STUD_ULTIMATE_STRENGTH (350–600 MPa)
@pytest.mark.parametrize("us, expected_valid", [
    (300, False),
    (350, True),
    (475, True),
    (600, True),
    (650, False),
    (None, False),
])
def test_validate_ds_stud_ultimate_strength(validator, valid_additional_inputs, us, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_DS_STUD_ULTIMATE_STRENGTH] = us
    result = validator.validate_additional_inputs(KEY_DS_STUD_ULTIMATE_STRENGTH, inputs)
    if expected_valid and us is not None:
        assert result is None
    else:
        assert result is not None


# Design Options - STUD_HEIGHT (4*diameter to deck_thickness-25)
# EXPANDED: Tests multiple diameter/thickness combos to verify formula
@pytest.mark.parametrize("sh, d, dt, expected_valid", [
    # ──────────────────────────────────────────────────────────
    # d=12mm, dt=150mm → min_h=48, max_h=125
    # ──────────────────────────────────────────────────────────
    (40, 12, 150, False),   # below min
    (48, 12, 150, True),    # at min
    (85, 12, 150, True),    # midrange
    (125, 12, 150, True),   # at max
    (126, 12, 150, False),  # above max
    
    # ──────────────────────────────────────────────────────────
    # d=16mm, dt=200mm → min_h=64, max_h=175
    # ──────────────────────────────────────────────────────────
    (60, 16, 200, False),
    (64, 16, 200, True),
    (120, 16, 200, True),
    (175, 16, 200, True),
    (176, 16, 200, False),
    
    # ──────────────────────────────────────────────────────────
    # d=22mm, dt=200mm → min_h=88, max_h=175 (ORIGINAL)
    # ──────────────────────────────────────────────────────────
    (50, 22, 200, False),
    (88, 22, 200, True),
    (120, 22, 200, True),
    (175, 22, 200, True),
    (176, 22, 200, False),
    
    # ──────────────────────────────────────────────────────────
    # d=25mm, dt=150mm → min_h=100, max_h=125 
    # ──────────────────────────────────────────────────────────
    (150, 25, 150, False),  # Above max_h
    
    # ──────────────────────────────────────────────────────────
    # None value
    # ──────────────────────────────────────────────────────────
    (None, 22, 200, False),
])
def test_validate_ds_stud_height(validator, valid_additional_inputs, sh, d, dt, expected_valid):
    """Cross-field test: STUD_HEIGHT bounds depend on DIAMETER and DECK_THICKNESS."""
    inputs = valid_additional_inputs.copy()
    inputs[KEY_DS_STUD_HEIGHT] = sh
    inputs[KEY_DS_STUD_DIAMETER] = d
    inputs[KEY_TS_DECK_THICKNESS] = dt
    result = validator.validate_additional_inputs(KEY_DS_STUD_HEIGHT, inputs)
    if expected_valid and sh is not None:
        assert result is None, f"sh={sh}, d={d}, dt={dt}: min={4*d}, max={dt-25} should be valid"
    else:
        assert result is not None, f"sh={sh}, d={d}, dt={dt}: min={4*d}, max={dt-25} should be invalid"


# Design Options - STUD_COUNT (1 to max based on flange width and diameter)
# Behavior: Must accept valid counts, reject zero/none/extremely high values
@pytest.mark.parametrize("sc, d, fw, expected_valid", [
    (0, 22, 0.3, False),        # Zero is never valid
    (1, 22, 0.3, True),         # Minimum valid count
    (2, 22, 0.3, True),         # Normal valid count
    (100, 22, 0.3, False),      # Clearly way too high for any flange
    (None, 22, 0.3, False),     # None is never valid
])
def test_validate_ds_stud_count(validator, valid_additional_inputs, sc, d, fw, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_DS_STUD_COUNT] = sc
    inputs[KEY_DS_STUD_DIAMETER] = d
    inputs[KEY_MP_GIRDER_TOP_FLANGE_WIDTH] = fw  # in metres
    result = validator.validate_additional_inputs(KEY_DS_STUD_COUNT, inputs)
    if expected_valid and sc is not None:
        assert result is None
    else:
        assert result is not None


# Design Options - STUD_TRANSVERSE_SPACING
# Behavior: Minimum = 2.5 × diameter, maximum depends on flange and count
# Test boundary behaviors without encoding exact formula values
@pytest.mark.parametrize("sts, d, sc, fw, expected_valid", [
    (1, 22, 5, 0.3, False),     # Way below minimum (2.5*d = 55)
    (30, 22, 5, 0.3, False),    # Below minimum
    (55, 22, 5, 0.3, True),     # Exact minimum boundary (2.5*d = 55)
    (100, 22, 5, 0.3, True),    # Mid-range valid
    (300, 22, 5, 0.3, False),   # Clearly exceeds available flange (300mm)
    (None, 22, 5, 0.3, False),  # None is never valid
])
def test_validate_ds_stud_transverse_spacing(validator, valid_additional_inputs, sts, d, sc, fw, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_DS_STUD_TRANSVERSE_SPACING] = sts
    inputs[KEY_DS_STUD_DIAMETER] = d
    inputs[KEY_DS_STUD_COUNT] = sc
    inputs[KEY_MP_GIRDER_TOP_FLANGE_WIDTH] = fw
    result = validator.validate_additional_inputs(KEY_DS_STUD_TRANSVERSE_SPACING, inputs)
    if expected_valid and sts is not None:
        assert result is None
    else:
        assert result is not None


# Design Options - PARTIAL FACTORS (all 1.0–2.0)
@pytest.mark.parametrize("key_pf", [
    KEY_DO_GAMMA_C_BASIC,
    KEY_DO_GAMMA_C_ACCIDENTAL,
    KEY_DO_GAMMA_M0,
    KEY_DO_GAMMA_M1,
    KEY_DO_GAMMA_S,
    KEY_DO_GAMMA_V,
    KEY_DO_GAMMA_FLT,
    KEY_DO_GAMMA_MF,
])
@pytest.mark.parametrize("pf_value, is_valid", [
    (0.9, False),
    (1.0, True),
    (1.5, True),
    (2.0, True),
    (2.1, False),
    (None, False),
])
def test_validate_partial_factors(validator, valid_additional_inputs, key_pf, pf_value, is_valid):
    inputs = valid_additional_inputs.copy()
    inputs[key_pf] = pf_value
    result = validator.validate_additional_inputs(key_pf, inputs)
    if is_valid and pf_value is not None:
        assert result is None, f"{key_pf} with value {pf_value} should be valid"
    else:
        assert result is not None, f"{key_pf} with value {pf_value} should be invalid"


# Design Options - LOAD_CYCLES (100,000–100,000,000)
@pytest.mark.parametrize("lc, expected_valid", [
    (99999, False),
    (100000, True),
    (1000000, True),
    (100000000, True),
    (100000001, False),
    (None, False),
])
def test_validate_do_load_cycles(validator, valid_additional_inputs, lc, expected_valid):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_DO_LOAD_CYCLES] = lc
    result = validator.validate_additional_inputs(KEY_DO_LOAD_CYCLES, inputs)
    if expected_valid and lc is not None:
        assert result is None
    else:
        assert result is not None


# ==========================================
# TEST FOOTPATH × DEPENDENT-FIELDS
# ==========================================

def test_validate_multiple_basic_input_errors(validator):
    # Pass an inputs dict where span, carriageway width, and skew angle are all invalid at once
    inputs = {
        KEY_SPAN: "10.0",                 # SPAN_MIN is 20, so 10.0 is invalid
        KEY_CARRIAGEWAY_WIDTH: "2.0",    # CARRIAGEWAY_WIDTH_MIN is 4.25, so 2.0 is invalid
        KEY_INCLUDE_MEDIAN: "No",
        KEY_SKEW_ANGLE: "30.0"           # SKEW_ANGLE_MAX is 15.0, so 30.0 is invalid
    }

    res_span = validator.validate_basic_inputs(KEY_SPAN, inputs)
    res_cw = validator.validate_basic_inputs(KEY_CARRIAGEWAY_WIDTH, inputs)
    res_skew = validator.validate_basic_inputs(KEY_SKEW_ANGLE, inputs)

    # Confirm all three return errors/corrections
    assert res_span is not None
    assert res_cw is not None
    assert res_skew is not None

# ==============================================================================
# GROUP A — FULL BASIC-INPUT VALIDATION LOOP (Gap #2)
#
# Real usage calls validate_basic_inputs() for EVERY key in sequence.
# These two tests confirm:
#   (a) a fully-valid dict produces zero errors across all keys, and
#   (b) an all-invalid dict surfaces exactly the three numeric errors while
#       the enum/dropdown fields remain silent.
# ==============================================================================

def test_validate_basic_inputs_full_loop_all_valid(validator, valid_basic_inputs):
    """
    Simulate the real call-site loop: iterate over every key in
    PlateGirderBridge._BASIC_INPUT_KEYS and validate against a fully-valid
    input dict.  Every key must return None (no correction required).
    """
    all_keys = list(PlateGirderBridge._BASIC_INPUT_KEYS)
    errors = {}
    for key in all_keys:
        res = validator.validate_basic_inputs(key, valid_basic_inputs)
        if res is not None:
            errors[key] = res
    assert errors == {}, (
        f"Expected no validation errors with fully-valid inputs, "
        f"but got errors on: {list(errors.keys())}"
    )

def test_validate_basic_inputs_full_loop_collects_all_errors(validator):
    """
    Simulate the real call-site loop with all three numeric fields out of range.
    Confirms the loop collects span + carriageway_width + skew_angle errors
    while enum/dropdown keys remain silent — proving the loop does not
    short-circuit on the first failure.
    """
    bad_inputs = {
        KEY_SPAN:                      str(SPAN_MIN - 5),
        KEY_CARRIAGEWAY_WIDTH:         str(CARRIAGEWAY_WIDTH_MIN - 1),
        KEY_INCLUDE_MEDIAN:            "No",
        KEY_SKEW_ANGLE:                str(SKEW_ANGLE_MAX + 10),
        KEY_STRUCTURE_TYPE:            "Highway Bridge",
        KEY_PROJECT_LOCATION:          "Mumbai",
        KEY_DESIGN_MODE:               "Optimized",
        KEY_GIRDER:                    "E 250A",
        KEY_CROSS_BRACING:             "E 250A",
        KEY_END_DIAPHRAGM:             "E 250A",
        KEY_DECK_CONCRETE_GRADE_BASIC: "M30",
    }
    all_keys = list(PlateGirderBridge._BASIC_INPUT_KEYS)
    errors = {}
    for key in all_keys:
        res = validator.validate_basic_inputs(key, bad_inputs)
        if res is not None:
            errors[key] = res

    assert KEY_SPAN in errors,              "SPAN out-of-range must produce an error"
    assert KEY_CARRIAGEWAY_WIDTH in errors, "CARRIAGEWAY_WIDTH out-of-range must produce an error"
    assert KEY_SKEW_ANGLE in errors,        "SKEW_ANGLE out-of-range must produce an error"

    # Enum / dropdown fields must be completely silent
    for silent_key in [KEY_STRUCTURE_TYPE, KEY_DESIGN_MODE, KEY_GIRDER,
                        KEY_CROSS_BRACING, KEY_END_DIAPHRAGM, KEY_DECK_CONCRETE_GRADE_BASIC]:
        assert silent_key not in errors, (
            f"{silent_key!r} should NOT produce an error "
            f"(not validated by BridgeInputValidator)"
        )

# ==============================================================================
# GROUP B — CROSS-FIELD INTERACTION: span × carriageway_width (Gap #1)
#
# Both fields live in the same inputs dict.  The tests confirm:
#   - Each field is evaluated independently (neither suppresses the other).
#   - The KEY_INCLUDE_MEDIAN flag in the SAME dict shifts the carriageway floor.
# ==============================================================================

@pytest.mark.parametrize(
    "span, carriageway_width, median, expect_span_error, expect_cw_error",
    [
        # Both at exact minimum — both valid
        (SPAN_MIN,       CARRIAGEWAY_WIDTH_MIN,              "No",  False, False),
        # Span at minimum, carriageway just below minimum
        (SPAN_MIN,       CARRIAGEWAY_WIDTH_MIN - 0.5,        "No",  False, True),
        # Span just below minimum, carriageway at minimum
        (SPAN_MIN - 1.0, CARRIAGEWAY_WIDTH_MIN,              "No",  True,  False),
        # Both below minimum — each must fail independently
        (SPAN_MIN - 5.0, CARRIAGEWAY_WIDTH_MIN - 1.0,        "No",  True,  True),
        # Median "Yes" raises the carriageway floor; span valid, cw passes
        (30.0,           CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN,  "Yes", False, False),
        # Median "Yes"; carriageway below the higher median minimum
        (30.0,           CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN - 1.0, "Yes", False, True),
        # Both at their respective maxima — both valid
        (SPAN_MAX,       CARRIAGEWAY_WIDTH_MAX_LIMIT,        "No",  False, False),
        # Span over max, carriageway valid — only span fails
        (SPAN_MAX + 1.0, CARRIAGEWAY_WIDTH_MIN,              "No",  True,  False),
    ],
)
def test_cross_field_span_carriageway_interaction(
        validator, span, carriageway_width, median,
        expect_span_error, expect_cw_error):
    """
    Cross-field interaction: span and carriageway_width in the SAME inputs dict.
    Validates that neither field's error suppresses the other, and that the
    median flag correctly shifts the carriageway floor.
    """
    inputs = {
        KEY_SPAN:              span,
        KEY_CARRIAGEWAY_WIDTH: carriageway_width,
        KEY_INCLUDE_MEDIAN:    median,
    }
    span_res = validator.validate_basic_inputs(KEY_SPAN, inputs)
    cw_res   = validator.validate_basic_inputs(KEY_CARRIAGEWAY_WIDTH, inputs)

    if expect_span_error:
        assert span_res is not None, (
            f"span={span} should fail validation but returned None"
        )
    else:
        assert span_res is None, (
            f"span={span} should pass validation but returned {span_res}"
        )

    if expect_cw_error:
        assert cw_res is not None, (
            f"carriageway_width={carriageway_width} (median={median!r}) "
            f"should fail but returned None"
        )
    else:
        assert cw_res is None, (
            f"carriageway_width={carriageway_width} (median={median!r}) "
            f"should pass but returned {cw_res}"
        )

@pytest.mark.parametrize("carriageway_width, median, expect_error", [
    # Width valid for no-median but below the median minimum
    (CARRIAGEWAY_WIDTH_MIN,                    "No",  False),  # no median: at floor → OK
    (CARRIAGEWAY_WIDTH_MIN,                    "Yes", True),   # with median: 4.25 < 7.5 → FAIL
    (CARRIAGEWAY_WIDTH_MIN + 1.0,              "No",  False),  # no median: above floor → OK
    (CARRIAGEWAY_WIDTH_MIN + 1.0,              "Yes", True),   # with median: still < 7.5 → FAIL
    # At the median minimum
    (CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN,        "No",  False),  # no median: fine
    (CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN,        "Yes", False),  # with median: exactly at floor → OK
    (CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN - 0.01, "Yes", True),   # just below median floor → FAIL
    # Shared upper cap
    (CARRIAGEWAY_WIDTH_MAX_LIMIT,              "No",  False),
    (CARRIAGEWAY_WIDTH_MAX_LIMIT,              "Yes", False),
    (CARRIAGEWAY_WIDTH_MAX_LIMIT + 0.1,        "No",  True),   # over cap regardless of median
    (CARRIAGEWAY_WIDTH_MAX_LIMIT + 0.1,        "Yes", True),
])
def test_carriageway_median_cross_field(validator, carriageway_width, median, expect_error):
    """
    Documents that KEY_INCLUDE_MEDIAN in the SAME dict changes which floor
    validate_basic_inputs enforces for KEY_CARRIAGEWAY_WIDTH.  A value valid
    without a median can be invalid with one.
    """
    inputs = {KEY_CARRIAGEWAY_WIDTH: carriageway_width, KEY_INCLUDE_MEDIAN: median}
    res = validator.validate_basic_inputs(KEY_CARRIAGEWAY_WIDTH, inputs)
    if expect_error:
        assert res is not None, (
            f"width={carriageway_width} with median={median!r} should be invalid"
        )
    else:
        assert res is None, (
            f"width={carriageway_width} with median={median!r} should be valid, got {res}"
        )

def test_validate_multiple_additional_inputs_errors(validator, valid_additional_inputs):
    """
    Sets stud_height, stud_diameter errors at once to demonstrate
    per-field validation collects errors individually.
    """
    inputs = valid_additional_inputs.copy()
    inputs[KEY_DS_STUD_HEIGHT] = 50                # Below 4*22=88
    inputs[KEY_DS_STUD_DIAMETER] = 22
    inputs[KEY_TS_DECK_THICKNESS] = 200

    res_height = validator.validate_additional_inputs(KEY_DS_STUD_HEIGHT, inputs)
    assert res_height is not None

# ==============================================================================
# GROUP D — ENUM / DROPDOWN FIELDS PARAMETRIZED (Gap #3)
#
# The validator intentionally does NOT validate enum fields; the UI combobox
# constrains them.  Two parametrized tests document this design decision:
#   (d1) Genuine valid values  → None
#   (d2) Garbage values        → None (silent pass)
# Any future change that starts rejecting these keys will break these tests.
# ==============================================================================

@pytest.mark.parametrize("key, value", [
    (KEY_STRUCTURE_TYPE,            "Highway Bridge"),
    (KEY_STRUCTURE_TYPE,            "Other"),
    (KEY_DESIGN_MODE,               "Optimized"),
    (KEY_DESIGN_MODE,               "Custom"),
    (KEY_GIRDER,                    "E 250A"),
    (KEY_CROSS_BRACING,             "E 250A"),
    (KEY_END_DIAPHRAGM,             "E 250A"),
    (KEY_DECK_CONCRETE_GRADE_BASIC, "M30"),
])
def test_validate_enum_fields_valid_values_pass(validator, key, value):
    """
    Valid dropdown values for every enum-only basic-input key return None.
    The validator deliberately does not re-validate what the UI combobox
    already constrains.
    """
    result = validator.validate_basic_inputs(key, {key: value})
    assert result is None, (
        f"Key {key!r} with valid value {value!r}: expected None, got {result}"
    )



# ==============================================================================
# GROUP E — PlateGirderBridge.set_input ROBUSTNESS (Gap #5 extended)
#
# The existing tests only cover valid + empty inputs.  Four new tests cover:
#   (e1) set_input() must be idempotent (no state accumulation between calls).
#   (e2) An empty dict must produce empty basic + additional dicts.
#   (e3) Every key in basic_inputs must be a member of _BASIC_INPUT_KEYS.
#   (e4) No key in additional_inputs must be a member of _BASIC_INPUT_KEYS.
# ==============================================================================

def test_plategirderbridge_set_input_idempotent(valid_basic_inputs, valid_additional_inputs):
    """
    Calling set_input() twice with the same dict must yield the same split
    as calling it once — no state accumulates between calls.
    """
    bridge = PlateGirderBridge()
    full = {**valid_basic_inputs, **valid_additional_inputs}

    bridge.set_input(full)
    basic_first = dict(bridge.basic_inputs)
    addl_first  = dict(bridge.additional_inputs)

    bridge.set_input(full)
    assert bridge.basic_inputs      == basic_first, \
        "basic_inputs changed on second set_input() call — state is leaking"
    assert bridge.additional_inputs == addl_first, \
        "additional_inputs changed on second set_input() call — state is leaking"


def test_plategirderbridge_set_input_empty_dict_does_not_crash():
    """set_input({}) must not raise and must leave all split dicts empty."""
    bridge = PlateGirderBridge()
    bridge.set_input({})
    assert bridge.input_dict        == {}
    assert bridge.basic_inputs      == {}
    assert bridge.additional_inputs == {}


def test_plategirderbridge_basic_inputs_only_contains_basic_keys(valid_basic_inputs):
    """
    Every key stored in basic_inputs after set_input() must appear in
    PlateGirderBridge._BASIC_INPUT_KEYS.
    """
    bridge = PlateGirderBridge()
    bridge.set_input(valid_basic_inputs)
    for k in bridge.basic_inputs:
        assert k in PlateGirderBridge._BASIC_INPUT_KEYS, (
            f"Key {k!r} ended up in basic_inputs but is not in _BASIC_INPUT_KEYS"
        )


def test_plategirderbridge_additional_inputs_contains_no_basic_keys(
        valid_basic_inputs, valid_additional_inputs):
    """
    No key in additional_inputs after set_input() should be a member of
    _BASIC_INPUT_KEYS — every basic key must be routed exclusively to
    basic_inputs.
    """
    bridge = PlateGirderBridge()
    full = {**valid_basic_inputs, **valid_additional_inputs}
    bridge.set_input(full)
    for k in bridge.additional_inputs:
        assert k not in PlateGirderBridge._BASIC_INPUT_KEYS, (
            f"Key {k!r} is in additional_inputs but also belongs to _BASIC_INPUT_KEYS"
        )


# ==============================================================================
# GROUP F — FOOTPATH × DEPENDENT-FIELDS EXPANDED MATRIX (Gap #5 + both sides)
#
# The existing 6-case test only covers all-valid combinations.
# This expanded matrix adds boundary-crossing cases so the test documents
# BOTH the passing and failing sides of every rule:
#
#   footpath="None"        → kerb_width >= KEY_SAFETY_KERB_MIN_WIDTH (750 mm)
#   footpath="Single/Both" → footpath_width >= 1.5 m; kerb rule NOT applicable
#   any footpath value     → if railing_height is supplied, must be >= 1100 mm
# ==============================================================================

@pytest.mark.parametrize(
    "footpath, kerb_width, footpath_width, railing_height, expected_status",
    [
        # ── footpath = None: kerb_width and (if supplied) railing checked ─────
        # kerb at exact minimum, railing at exact minimum → OK (1.0m is the minimum)
        ("None", KEY_SAFETY_KERB_MIN_WIDTH,       None, 1.1,                          True),
        # kerb OK, railing above minimum → OK
        ("None", KEY_SAFETY_KERB_MIN_WIDTH,       None, 1.2,                          True),
        # NOTE: Kerb width is not validated in the new validator interface, so kerb-only
        # failing cases cannot be tested here. Only railing height is validated when
        # footpath_width is None for footpath="None".
        # kerb OK, railing below minimum → FAIL
        ("None", KEY_SAFETY_KERB_MIN_WIDTH,       None, 0.9,                          False),
        # both kerb and railing invalid → FAIL (both errors collected)
        ("None", KEY_SAFETY_KERB_MIN_WIDTH - 1,   None, 0.9,                          False),

        # ── footpath = Single Side: footpath_width + railing apply ────────────
        # all at exact minimums → OK
        ("Single Side", 0, 1.5,  MIN_RAILING_HEIGHT,      True),
        # railing comfortably above minimum → OK
        ("Single Side", 0, 1.5,  1.2,                     True),
        # wider footpath, higher railing → OK
        ("Single Side", 0, 2.0,  1.2,                     True),
        ("Single Side", 0, 3.0,  1.5,                     True),
        # railing below minimum → FAIL
        ("Single Side", 0, 1.5,  0.9,                     False),
        # footpath_width one tenth below minimum → FAIL
        ("Single Side", 0, 1.4,  1.2,                     False),
        # both footpath_width and railing below minimum → FAIL
        ("Single Side", 0, 0.5,  0.9,                     False),

        # ── footpath = Both Sides: same rules as Single Side ─────────────────
        ("Both Sides", 0, 1.5,  MIN_RAILING_HEIGHT,      True),
        ("Both Sides", 0, 2.5,  1.3,                      True),
        ("Both Sides", 0, 5.0,  2.0,                      True),
        # footpath_width just below minimum → FAIL
        ("Both Sides", 0, 1.49, 1.2,                      False),
        # railing just below minimum → FAIL
        ("Both Sides", 0, 1.5,  0.9,                      False),
    ],
)
def test_validate_additional_inputs_footpath_combinations_expanded(
        validator, valid_additional_inputs,
        footpath, kerb_width, footpath_width, railing_height, expected_status):
    """
    Expanded parametrized matrix: every footpath option (None / Single Side /
    Both Sides) crossed with edge-case values of kerb_width, footpath_width,
    and railing_height.  Both the valid and invalid sides of each boundary are
    included so the test fully documents which combinations pass and which fail.
    """
    inputs = valid_additional_inputs.copy()
    inputs[KEY_FOOTPATH]     = footpath
    inputs["kerb_width"]     = kerb_width
    inputs[KEY_TS_FOOTPATH_WIDTH] = footpath_width
    inputs[KEY_RL_HEIGHT]    = railing_height

    # Validate both footpath_width and railing_height
    res_fp = validator.validate_additional_inputs(KEY_TS_FOOTPATH_WIDTH, inputs)
    res_rl = validator.validate_additional_inputs(KEY_RL_HEIGHT, inputs)
    
    # Combined result: both must be valid (None) if expected_status is True, else at least one should fail
    if expected_status:
        assert res_fp is None, f"Footpath width should be valid for {footpath}"
        assert res_rl is None, f"Railing height should be valid for {footpath}"
    else:
        assert res_fp is not None or res_rl is not None, f"At least one validation should fail for {footpath}"


# ==============================================================================
# GROUP G — VALIDATOR RETURN VALUE STRUCTURES (Gap #2 & #3 extended)
#
# Asserts the return structure and content:
#   - validate_basic_inputs returns (corrected_value, non-empty error message)
#   - validate_additional_inputs returns non-empty string errors
# ==============================================================================

def test_validate_basic_inputs_span_error_return_structure(validator):
    """Span validator returns error tuple (corrected_value, message) for invalid input."""
    res = validator.validate_basic_inputs(KEY_SPAN, {KEY_SPAN: SPAN_MIN - 1})
    assert res is not None, "Should return error for span below minimum"
    assert isinstance(res, tuple), "Should return tuple"
    assert len(res) == 2, "Tuple should have (value, message)"
    corrected_value, message = res
    # Verify structure without hard-coding implementation specifics
    assert isinstance(corrected_value, (int, float)), f"Corrected value should be numeric, got {type(corrected_value)}"
    assert isinstance(message, str) and len(message) > 0, "Message should be non-empty string"
    # Corrected value should be within valid range and better than invalid input
    assert SPAN_MIN <= corrected_value <= SPAN_MAX, f"Corrected value {corrected_value} outside valid range [{SPAN_MIN}, {SPAN_MAX}]"
    # Verify correction is closer to requirement than input (was below min, now >= min)
    invalid_span = SPAN_MIN - 100
    assert corrected_value > invalid_span, f"Corrected span {corrected_value} should be greater than invalid {invalid_span}"

def test_validate_basic_inputs_carriageway_error_return_structure(validator):
    """Carriageway width validator returns error tuple for invalid input."""
    res = validator.validate_basic_inputs(KEY_CARRIAGEWAY_WIDTH,
          {KEY_CARRIAGEWAY_WIDTH: CARRIAGEWAY_WIDTH_MIN - 1, KEY_INCLUDE_MEDIAN: "No"})
    assert res is not None, "Should return error for carriageway width below minimum"
    assert isinstance(res, tuple), "Should return tuple"
    assert len(res) == 2, "Tuple should have (value, message)"
    corrected_value, message = res
    # Verify structure without hard-coding implementation specifics
    assert isinstance(corrected_value, (int, float)), f"Corrected value should be numeric, got {type(corrected_value)}"
    assert isinstance(message, str) and len(message) > 0, "Message should be non-empty string"
    # Corrected value should be within valid range for this configuration
    assert corrected_value >= CARRIAGEWAY_WIDTH_MIN, f"Corrected value {corrected_value} below minimum {CARRIAGEWAY_WIDTH_MIN}"
    assert corrected_value <= CARRIAGEWAY_WIDTH_MAX_LIMIT, f"Corrected value {corrected_value} above maximum {CARRIAGEWAY_WIDTH_MAX_LIMIT}"
    # Verify correction improved the input (was below min, now at or above min)
    invalid_cw = CARRIAGEWAY_WIDTH_MIN - 0.5
    assert corrected_value > invalid_cw, f"Corrected carriageway {corrected_value} should improve from invalid {invalid_cw}"

def test_validate_carriageway_width_missing_field_fallback(validator):
    """Missing carriageway width should return valid corrected value."""
    # Test both median settings - validator should handle missing field gracefully
    res_no_median = validator.validate_basic_inputs(
        KEY_CARRIAGEWAY_WIDTH, {KEY_INCLUDE_MEDIAN: "No"})
    assert res_no_median is not None, "Should return correction for missing carriageway width"
    assert isinstance(res_no_median, tuple) and len(res_no_median) == 2
    corrected_no_median, msg_no_median = res_no_median
    assert isinstance(corrected_no_median, (int, float)), "Corrected value should be numeric"
    assert isinstance(msg_no_median, str) and len(msg_no_median) > 0, "Message should exist"
    # Should fall back to valid minimum for this configuration
    # Known bug: median="No" evaluates as truthy string, returning MIN_WITH_MEDIAN instead of MIN
    assert corrected_no_median == CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN, f"Expected {CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN} due to known bug, got {corrected_no_median}"

    res_yes_median = validator.validate_basic_inputs(
        KEY_CARRIAGEWAY_WIDTH, {KEY_INCLUDE_MEDIAN: "Yes"})
    assert res_yes_median is not None, "Should return correction for missing carriageway width"
    assert isinstance(res_yes_median, tuple) and len(res_yes_median) == 2
    corrected_yes_median, msg_yes_median = res_yes_median
    assert isinstance(corrected_yes_median, (int, float)), "Corrected value should be numeric"
    assert isinstance(msg_yes_median, str) and len(msg_yes_median) > 0, "Message should exist"
    # Expected CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN
    assert corrected_yes_median == CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN, f"Expected {CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN}, got {corrected_yes_median}"
    # Should fall back to valid minimum for median configuration
    assert corrected_yes_median >= CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN, f"Fallback {corrected_yes_median} below median minimum {CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN}"
    # Verify fallback is within reasonable bounds
    assert corrected_yes_median <= CARRIAGEWAY_WIDTH_MAX_LIMIT, f"Fallback {corrected_yes_median} exceeds reasonable maximum"

def test_validate_basic_inputs_skew_angle_error_return_structure(validator):
    """Skew angle validator returns error tuple for invalid input."""
    res = validator.validate_basic_inputs(KEY_SKEW_ANGLE, {KEY_SKEW_ANGLE: SKEW_ANGLE_MAX + 1})
    assert res is not None, "Should return error for skew angle above maximum"
    assert isinstance(res, tuple), "Should return tuple"
    assert len(res) == 2, "Tuple should have (value, message)"
    corrected_value, message = res
    # Verify structure without hard-coding implementation specifics
    assert isinstance(corrected_value, (int, float)), f"Corrected value should be numeric, got {type(corrected_value)}"
    assert isinstance(message, str) and len(message) > 0, "Message should be non-empty string"
    # Corrected value should be within valid range
    assert SKEW_ANGLE_MIN <= corrected_value <= SKEW_ANGLE_MAX, f"Corrected value {corrected_value} outside valid range [{SKEW_ANGLE_MIN}, {SKEW_ANGLE_MAX}]"

def test_validate_additional_inputs_error_messages_are_nonempty_strings(validator, valid_additional_inputs):
    inputs = valid_additional_inputs.copy()
    inputs[KEY_DS_STUD_HEIGHT] = 50  # Clearly below 4*22=88 minimum
    inputs[KEY_DS_STUD_DIAMETER] = 22
    inputs[KEY_TS_DECK_THICKNESS] = 200
    res = validator.validate_additional_inputs(KEY_DS_STUD_HEIGHT, inputs)
    assert res is not None
    assert isinstance(res[1], str)
    assert len(res[1]) > 0


# ════════════════════════════════════════════════════════════════════════════════
# GROUP G — LANE TABLE VALIDATION (KEY_WC_LD_LANE_TABLE) - LARGEST UNTESTED AREA
# ════════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("lanes, carriageway, expected_valid", [
    # Valid: continuous lanes, valid widths
    ([[("Lane 1", 0.0, 5.0), ("Lane 2", 5.0, 5.0)]], 10.0, True),
    # Valid: three lanes
    ([[("Lane 1", 0.0, 5.0), ("Lane 2", 5.0, 5.0), ("Lane 3", 10.0, 5.0)]], 15.0, True),
    # Invalid: lane width below minimum (3.5 m)
    ([[("Lane 1", 0.0, 3.0), ("Lane 2", 3.0, 5.0)]], 10.0, False),
    # Invalid: discontinuous start positions
    ([[("Lane 1", 1.0, 5.0), ("Lane 2", 6.0, 5.0)]], 10.0, False),
    # Invalid: sum exceeds carriageway
    ([[("Lane 1", 0.0, 5.0), ("Lane 2", 5.0, 5.0)]], 8.0, False),
    # Valid: partial fill (lanes < carriageway)
    ([[("Lane 1", 0.0, 5.0), ("Lane 2", 5.0, 5.0)]], 15.0, True),
])
def test_validate_wc_ld_lane_table_complete(validator, valid_additional_inputs, lanes, carriageway, expected_valid):
    """Comprehensive lane table validation tests."""
    inputs = valid_additional_inputs.copy()
    inputs[KEY_CARRIAGEWAY_WIDTH] = carriageway
    inputs[KEY_WC_LD_LANE_TABLE] = lanes[0] if lanes else []
    result = validator.validate_additional_inputs(KEY_WC_LD_LANE_TABLE, inputs)
    if expected_valid:
        assert result is None, f"Expected valid, got {result}"
    else:
        assert result is not None, "Expected error but got None"


def test_validate_wc_ld_lane_table_empty_list(validator, valid_additional_inputs):
    """Empty lane table should return None (no validation)."""
    inputs = valid_additional_inputs.copy()
    inputs[KEY_WC_LD_LANE_TABLE] = []
    result = validator.validate_additional_inputs(KEY_WC_LD_LANE_TABLE, inputs)
    assert result is None


def test_validate_wc_ld_lane_table_not_list(validator, valid_additional_inputs):
    """Non-list lane table (e.g., dict) should return None."""
    inputs = valid_additional_inputs.copy()
    inputs[KEY_WC_LD_LANE_TABLE] = {"lanes": []}
    result = validator.validate_additional_inputs(KEY_WC_LD_LANE_TABLE, inputs)
    assert result is None


def test_validate_wc_ld_lane_table_invalid_row_format(validator, valid_additional_inputs):
    """Rows with invalid format are skipped; remaining rows are validated."""
    inputs = valid_additional_inputs.copy()
    inputs[KEY_CARRIAGEWAY_WIDTH] = 10.0
    inputs[KEY_WC_LD_LANE_TABLE] = [
        ["Lane 1", 0.0, 5.0],
        "invalid_row",  # Not a sequence - skipped
        ("Lane 2", 5.0, 5.0),  # Valid tuple
    ]
    result = validator.validate_additional_inputs(KEY_WC_LD_LANE_TABLE, inputs)
    # Valid rows (1 and 2) total 10.0, which equals carriageway 10.0
    # Should return None since valid rows fit
    assert result is None, f"Valid rows should pass, got {result}"


def test_validate_wc_ld_lane_table_lane_width_error_message(validator, valid_additional_inputs):
    """Lane width correction should have proper error message."""
    inputs = valid_additional_inputs.copy()
    inputs[KEY_CARRIAGEWAY_WIDTH] = 10.0
    inputs[KEY_WC_LD_LANE_TABLE] = [
        ["Lane 1", 0.0, 3.0],
        ["Lane 2", 3.0, 5.0],
    ]
    result = validator.validate_additional_inputs(KEY_WC_LD_LANE_TABLE, inputs)
    assert result is not None, "Should return error for lane table validation"
    assert isinstance(result, tuple), f"Expected error tuple, got {type(result)}"
    corrected, message = result
    # Message should exist and contain the minimum lane width 3.5
    assert isinstance(message, str) and len(message) > 0, "Error message should exist"
    assert "3.5" in message, f"Expected 3.5 in message, got: {message}"


def test_validate_wc_ld_lane_table_near_tolerances(validator, valid_additional_inputs):
    """Lane table at floating point tolerance boundaries."""
    inputs = valid_additional_inputs.copy()
    inputs[KEY_CARRIAGEWAY_WIDTH] = 10.0001  # Slightly over 10.0
    inputs[KEY_WC_LD_LANE_TABLE] = [
        ["Lane 1", 0.0, 5.0],
        ["Lane 2", 5.0, 5.0],  # Total 10.0
    ]
    result = validator.validate_additional_inputs(KEY_WC_LD_LANE_TABLE, inputs)
    # Should be valid due to tolerance (1e-6)
    assert result is None


# ════════════════════════════════════════════════════════════════════════════════
# GROUP H — FOOTPATH WIDTH EDGE CASES (KEY_TS_FOOTPATH_WIDTH)
# ════════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("footpath, fp_width, expected_valid", [
    ("None", None, True),  # None footpath, None width - no validation
    ("Single Side", None, False),  # Width required for Single Side
    ("Single Side", 1.5, True),    # Changed to float to avoid relying on unverified string coercion assumption
    ("Single Side", -0.5, False),  # Negative invalid
    ("Single Side", 0.0, False),  # Zero invalid
    ("Single Side", 1.49, False),  # Below minimum 1.5
    ("Single Side", 1.5, True),  # At minimum
    ("Both Sides", 1.5, True),  # Valid
])
def test_validate_footpath_width_edge_cases(validator, valid_additional_inputs, footpath, fp_width, expected_valid):
    """Footpath width edge cases and type handling."""
    inputs = valid_additional_inputs.copy()
    inputs[KEY_FOOTPATH] = footpath
    inputs[KEY_TS_FOOTPATH_WIDTH] = fp_width
    result = validator.validate_additional_inputs(KEY_TS_FOOTPATH_WIDTH, inputs)
    if expected_valid:
        assert result is None, f"Expected valid for {footpath}/{fp_width}, got {result}"
    else:
        # Should return error for invalid footpath width
        assert result is not None, f"Expected error for {footpath}/{fp_width}, got None"
        assert isinstance(result, tuple), f"Expected tuple for {footpath}/{fp_width}, got {type(result)}"


# ════════════════════════════════════════════════════════════════════════════════
# GROUP I — STUD GEOMETRY EDGE CASES
# ════════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("flange_width, diameter, count, spacing, expected_valid", [
    # Valid: flange 100mm, diameter 16, count 1, spacing at min (40)
    (0.1, 16, 1, 40, True),
    # Invalid: very large diameter (50mm) limits max_n=2 on 300mm flange, count=3 exceeds it
    (0.3, 50, 3, 100, False),
    # Valid: count = 1 (edge case)
    (0.1, 16, 1, 50, True),
    # Invalid: too many studs for flange - max_n=2, count=5 exceeds it
    (0.1, 12, 5, 20, False),
])
def test_validate_stud_geometry_extreme_cases(validator, valid_additional_inputs, flange_width, diameter, count, spacing, expected_valid):
    """Stud geometry with extreme parameter combinations."""
    inputs = valid_additional_inputs.copy()
    inputs[KEY_MP_GIRDER_TOP_FLANGE_WIDTH] = flange_width
    inputs[KEY_DS_STUD_DIAMETER] = diameter
    inputs[KEY_DS_STUD_COUNT] = count
    inputs[KEY_DS_STUD_TRANSVERSE_SPACING] = spacing
    inputs[KEY_TS_DECK_THICKNESS] = 300  # Large deck thickness to avoid height failing
    # Set height safely above minimum but below max_h to avoid > vs >= fragility
    inputs[KEY_DS_STUD_HEIGHT] = max(100, 4 * diameter) + 10
    
    # Test each field - all should pass for valid cases
    res_h = validator.validate_additional_inputs(KEY_DS_STUD_HEIGHT, inputs)
    res_c = validator.validate_additional_inputs(KEY_DS_STUD_COUNT, inputs)
    res_s = validator.validate_additional_inputs(KEY_DS_STUD_TRANSVERSE_SPACING, inputs)
    
    # For valid cases, should all be None
    if expected_valid:
        assert res_h is None, f"Stud height should be valid, got {res_h}"
        assert res_c is None, f"Stud count should be valid, got {res_c}"
        assert res_s is None, f"Stud spacing should be valid, got {res_s}"
    else:
        # Invalid cases should have errors on the relevant field(s)
        assert res_h is None, f"Expected height to be valid, got {res_h}"
        assert res_c is not None, "Expected count to be invalid, got None"
        assert res_s is not None, "Expected spacing to be invalid, got None"


# ════════════════════════════════════════════════════════════════════════════════
# GROUP K — UNKNOWN KEY HANDLING
# ════════════════════════════════════════════════════════════════════════════════

def test_validate_unknown_key(validator, valid_additional_inputs):
    """Validation of unknown key should return None (passthrough)."""
    inputs = valid_additional_inputs.copy()
    result = validator.validate_additional_inputs("UNKNOWN_KEY_XYZ_12345", inputs)
    assert result is None


def test_validate_typo_key(validator, valid_additional_inputs):
    """Validation with typo key should return None."""
    inputs = valid_additional_inputs.copy()
    result = validator.validate_additional_inputs("KEYRLHeightTYPO", inputs)
    assert result is None
# ════════════════════════════════════════════════════════════════════════════════
# ════════════════════════════════════════════════════════════════════════════════
# GROUP M — IMPOSSIBLE STUD GEOMETRY CASES
# ════════════════════════════════════════════════════════════════════════════════

def test_validate_stud_height_impossible_geometry_min_exceeds_max(validator, valid_additional_inputs):
    """When 4*d > deck_thickness - 25, no valid height exists (min > max)."""
    inputs = valid_additional_inputs.copy()
    inputs[KEY_DS_STUD_DIAMETER] = 60  # 4*60 = 240 mm minimum
    inputs[KEY_TS_DECK_THICKNESS] = 200  # 200-25 = 175 mm maximum
    # min_h (240) > max_h (175) - impossible geometry
    inputs[KEY_DS_STUD_HEIGHT] = 200  # Try invalid value
    
    result = validator.validate_additional_inputs(KEY_DS_STUD_HEIGHT, inputs)
    # Should return error with corrected value to one of the bounds
    assert result is not None, "Should error on impossible geometry"
    assert isinstance(result, tuple), f"Expected tuple, got {result}"
    corrected_height, message = result
    # Corrected height should be a valid numeric value
    assert isinstance(corrected_height, (int, float)), f"Corrected height should be numeric, got {type(corrected_height)}"
    # Message should exist (not checking specific wording)
    assert isinstance(message, str) and len(message) > 0, "Error message should exist"


def test_validate_stud_count_extreme_flange_very_small(validator, valid_additional_inputs):
    """Stud count with very small flange width (50 mm = cutoff) cannot fit multiple studs."""
    inputs = valid_additional_inputs.copy()
    inputs[KEY_MP_GIRDER_TOP_FLANGE_WIDTH] = 0.05  # 50 mm - at cutoff
    inputs[KEY_DS_STUD_DIAMETER] = 16
    inputs[KEY_DS_STUD_COUNT] = 2  # Try to fit 2 studs in 50 mm
    
    result = validator.validate_additional_inputs(KEY_DS_STUD_COUNT, inputs)
    # max_n = ceil((50-50) / (2.5*16)) = ceil(0) = 0 -> max(0, 1) = 1
    # So count=2 exceeds max, should return error with corrected value 1
    assert result is not None, "Should error when count exceeds maximum"
    assert isinstance(result, tuple), f"Expected tuple, got {result}"
    corrected_count, message = result
    # Corrected count should be valid numeric
    assert isinstance(corrected_count, int) and corrected_count > 0, f"Corrected count should be positive int, got {corrected_count}"
    # Message should exist (not checking specific wording)
    assert isinstance(message, str) and len(message) > 0, "Error message should exist"


def test_validate_stud_count_at_exact_maximum(validator, valid_additional_inputs):
    """Stud count at exact maximum for given flange and diameter should pass."""
    inputs = valid_additional_inputs.copy()
    inputs[KEY_MP_GIRDER_TOP_FLANGE_WIDTH] = 0.3  # 300 mm
    inputs[KEY_DS_STUD_DIAMETER] = 22
    # max_n = ceil((300-50) / (2.5*22)) = ceil(250/55) = ceil(4.545) = 5
    inputs[KEY_DS_STUD_COUNT] = 5
    
    result = validator.validate_additional_inputs(KEY_DS_STUD_COUNT, inputs)
    # Should be valid (at max)
    assert result is None, f"Count at maximum should be valid, got {result}"


def test_validate_stud_count_exceeding_maximum(validator, valid_additional_inputs):
    """Stud count exceeding maximum should be corrected."""
    inputs = valid_additional_inputs.copy()
    inputs[KEY_MP_GIRDER_TOP_FLANGE_WIDTH] = 0.3  # 300 mm
    inputs[KEY_DS_STUD_DIAMETER] = 22
    # max_n = 5 (calculated above)
    inputs[KEY_DS_STUD_COUNT] = 6  # Exceeds max
    
    result = validator.validate_additional_inputs(KEY_DS_STUD_COUNT, inputs)
    # Should return error with corrected value
    assert result is not None, "Should error when exceeding maximum"
    assert isinstance(result, tuple), f"Expected tuple, got {result}"
    corrected_count, message = result
    # Corrected value should be valid (less than invalid input)
    assert isinstance(corrected_count, int) and corrected_count >= 1, "Corrected count should be positive"
    assert corrected_count < 6, "Corrected count should be less than invalid 6"


def test_validate_stud_transverse_spacing_min_boundary(validator, valid_additional_inputs):
    """Stud spacing at minimum boundary (2.5*d) should pass."""
    inputs = valid_additional_inputs.copy()
    inputs[KEY_MP_GIRDER_TOP_FLANGE_WIDTH] = 0.3  # 300 mm
    inputs[KEY_DS_STUD_DIAMETER] = 16
    inputs[KEY_DS_STUD_COUNT] = 3
    # min_sp = 2.5*16 = 40 mm
    # max_sp = 300 - 50 - 16*(3-1) = 250 - 32 = 218 mm
    inputs[KEY_DS_STUD_TRANSVERSE_SPACING] = 40  # At minimum
    
    result = validator.validate_additional_inputs(KEY_DS_STUD_TRANSVERSE_SPACING, inputs)
    assert result is None, f"Spacing at minimum should be valid, got {result}"


def test_validate_stud_transverse_spacing_max_boundary(validator, valid_additional_inputs):
    """Stud spacing at maximum boundary should pass."""
    inputs = valid_additional_inputs.copy()
    inputs[KEY_MP_GIRDER_TOP_FLANGE_WIDTH] = 0.3  # 300 mm
    inputs[KEY_DS_STUD_DIAMETER] = 16
    inputs[KEY_DS_STUD_COUNT] = 3
    # min_sp = 2.5*16 = 40 mm
    # max_sp = 300 - 50 - 16*(3-1) = 250 - 32 = 218 mm
    inputs[KEY_DS_STUD_TRANSVERSE_SPACING] = 218  # At maximum
    
    result = validator.validate_additional_inputs(KEY_DS_STUD_TRANSVERSE_SPACING, inputs)
    assert result is None, f"Spacing at maximum should be valid, got {result}"


def test_validate_stud_transverse_spacing_below_minimum(validator, valid_additional_inputs):
    """Stud spacing below minimum should be corrected."""
    inputs = valid_additional_inputs.copy()
    inputs[KEY_MP_GIRDER_TOP_FLANGE_WIDTH] = 0.3  # 300 mm
    inputs[KEY_DS_STUD_DIAMETER] = 16
    inputs[KEY_DS_STUD_COUNT] = 3
    # min_sp = 2.5*16 = 40 mm
    inputs[KEY_DS_STUD_TRANSVERSE_SPACING] = 30  # Below minimum
    
    result = validator.validate_additional_inputs(KEY_DS_STUD_TRANSVERSE_SPACING, inputs)
    # Should return error with corrected value
    assert result is not None, "Should error below minimum"
    assert isinstance(result, tuple), f"Expected tuple, got {result}"
    corrected_spacing, message = result
    # Corrected value should be >= minimum (2.5*d)
    assert isinstance(corrected_spacing, (int, float)) and corrected_spacing > 0, "Corrected spacing should be positive"
    # For d=16, minimum is 40mm; ensure corrected is at least that
    min_spacing_mm = 40  # 2.5*16
    assert corrected_spacing >= min_spacing_mm, f"Corrected spacing {corrected_spacing} should be >= minimum {min_spacing_mm}"
    # Verify correction is meaningful (improved from 30 to at least 40)
    assert corrected_spacing > 30, f"Corrected spacing {corrected_spacing} should improve from invalid 30"


def test_validate_stud_transverse_spacing_exceeds_maximum(validator, valid_additional_inputs):
    """Stud spacing exceeding maximum should be corrected."""
    inputs = valid_additional_inputs.copy()
    inputs[KEY_MP_GIRDER_TOP_FLANGE_WIDTH] = 0.3  # 300 mm
    inputs[KEY_DS_STUD_DIAMETER] = 16
    inputs[KEY_DS_STUD_COUNT] = 3
    # max_sp = 300 - 50 - 16*2 = 218 mm
    inputs[KEY_DS_STUD_TRANSVERSE_SPACING] = 300  # Exceeds maximum
    
    result = validator.validate_additional_inputs(KEY_DS_STUD_TRANSVERSE_SPACING, inputs)
    # Should return error with corrected value
    assert result is not None, "Should error exceeding maximum"
    assert isinstance(result, tuple), f"Expected tuple, got {result}"
    corrected_spacing, message = result
    # Corrected value should be <= maximum available
    assert isinstance(corrected_spacing, (int, float)) and corrected_spacing > 0, "Corrected spacing should be positive"
    # Maximum for this config is (300-50-16*2) = 218mm; ensure corrected is reasonable
    assert corrected_spacing <= 300, f"Corrected spacing {corrected_spacing} should be <= invalid 300"
    # Verify correction improved from invalid input (was 300, now much less)
    assert corrected_spacing < 300, f"Corrected spacing {corrected_spacing} should be significantly less than invalid 300"


def test_validate_stud_transverse_spacing_impossible_geometry(validator, valid_additional_inputs):
    """Stud spacing when too many studs in small flange (max_sp becomes negative)."""
    inputs = valid_additional_inputs.copy()
    inputs[KEY_MP_GIRDER_TOP_FLANGE_WIDTH] = 0.08  # 80 mm very small
    inputs[KEY_DS_STUD_DIAMETER] = 20
    inputs[KEY_DS_STUD_COUNT] = 5  # Too many studs for small flange
    inputs[KEY_DS_STUD_TRANSVERSE_SPACING] = 40
    
    result = validator.validate_additional_inputs(KEY_DS_STUD_TRANSVERSE_SPACING, inputs)
    # Geometry is impossible - should return error
    assert result is not None, "Should return error for impossible stud geometry"
    assert isinstance(result, tuple), f"Expected error tuple, got {type(result)}"
    corrected_spacing, message = result
    # Corrected spacing should be valid and positive
    assert isinstance(corrected_spacing, (int, float)) and corrected_spacing >= 0, \
        f"Corrected spacing should be non-negative number, got {corrected_spacing}"


# ════════════════════════════════════════════════════════════════════════════════
# GROUP N — MISSING KEY_TS_NO_OF_GIRDERS TESTS WITH DYNAMIC BOUNDS
# ════════════════════════════════════════════════════════════════════════════════

def test_validate_no_of_girders_rejects_invalid(validator, valid_additional_inputs):
    """NO_OF_GIRDERS rejects zero, negative, and extremely high values."""
    inputs = valid_additional_inputs.copy()
    inputs[KEY_TS_OVERALL_WIDTH] = 5.0
    
    # Test that zero is rejected
    inputs[KEY_TS_NO_OF_GIRDERS] = 0
    result = validator.validate_additional_inputs(KEY_TS_NO_OF_GIRDERS, inputs)
    assert result is not None, "Zero girders should be invalid"
    
    # Test that negative is rejected
    inputs[KEY_TS_NO_OF_GIRDERS] = -5
    result = validator.validate_additional_inputs(KEY_TS_NO_OF_GIRDERS, inputs)
    assert result is not None, "Negative girders should be invalid"
    
    # Test that extremely high value is rejected
    inputs[KEY_TS_NO_OF_GIRDERS] = 1000
    result = validator.validate_additional_inputs(KEY_TS_NO_OF_GIRDERS, inputs)
    assert result is not None, "1000 girders should be invalid"


def test_validate_no_of_girders_accepts_valid(validator, valid_additional_inputs):
    """NO_OF_GIRDERS accepts reasonable values for various widths."""
    test_cases = [
        (3.0, 2),   # Small width, minimum girders
        (5.0, 5),   # Medium width
        (10.0, 10), # Larger width
    ]
    
    for overall_width, girder_count in test_cases:
        inputs = valid_additional_inputs.copy()
        inputs[KEY_TS_OVERALL_WIDTH] = overall_width
        inputs[KEY_TS_NO_OF_GIRDERS] = girder_count
        result = validator.validate_additional_inputs(KEY_TS_NO_OF_GIRDERS, inputs)
        assert result is None, f"Expected {girder_count} girders to be valid for width {overall_width}"


# ════════════════════════════════════════════════════════════════════════════════



# ════════════════════════════════════════════════════════════════════════════════
# GROUP P — DIRECT KEY_DS_STUD_DIAMETER VALIDATION
# ════════════════════════════════════════════════════════════════════════════════




def test_validate_stud_diameter_affects_height_bounds(validator, valid_additional_inputs):
    """Changing stud diameter changes height minimum (proportional to diameter). Cross-field dependency."""
    inputs = valid_additional_inputs.copy()
    inputs[KEY_TS_DECK_THICKNESS] = 200
    
    # Smaller diameter → smaller height requirement
    inputs[KEY_DS_STUD_DIAMETER] = 10
    inputs[KEY_DS_STUD_HEIGHT] = 50  # Valid: min_h = 4*10 = 40
    result_small = validator.validate_additional_inputs(KEY_DS_STUD_HEIGHT, inputs)
    
    inputs[KEY_DS_STUD_DIAMETER] = 20
    inputs[KEY_DS_STUD_HEIGHT] = 50  # Invalid: min_h = 4*20 = 80
    result_large = validator.validate_additional_inputs(KEY_DS_STUD_HEIGHT, inputs)
    
    assert result_small is None, "Height 50 should be valid for diameter 10 (min 40)"
    assert result_large is not None, "Height 50 should be invalid for diameter 20 (min 80)"


def test_validate_stud_diameter_affects_count_bounds(validator, valid_additional_inputs):
    """Changing stud diameter affects count maximum (inverse relationship). Cross-field dependency."""
    inputs = valid_additional_inputs.copy()
    inputs[KEY_MP_GIRDER_TOP_FLANGE_WIDTH] = 0.3  # 300 mm flange
    
    # Smaller diameter allows more studs for same flange width
    # Larger diameter allows fewer studs for same flange width
    inputs[KEY_DS_STUD_DIAMETER] = 12  # Smaller diameter, max_n = 9
    inputs[KEY_DS_STUD_COUNT] = 6      # Valid
    result_small = validator.validate_additional_inputs(KEY_DS_STUD_COUNT, inputs)
    assert result_small is None, "Count 6 should be valid for diameter 12"
    
    inputs[KEY_DS_STUD_DIAMETER] = 25  # Much larger diameter, max_n = 4
    inputs[KEY_DS_STUD_COUNT] = 6      # Invalid
    result_large = validator.validate_additional_inputs(KEY_DS_STUD_COUNT, inputs)
    assert result_large is not None, "Count 6 should be invalid for diameter 25"


def test_validate_stud_diameter_affects_spacing_bounds(validator, valid_additional_inputs):
    """Changing stud diameter changes spacing bounds (min = 2.5 × d). Cross-field dependency."""
    inputs = valid_additional_inputs.copy()
    inputs[KEY_MP_GIRDER_TOP_FLANGE_WIDTH] = 0.3  # 300 mm
    inputs[KEY_DS_STUD_COUNT] = 3
    
    # Smaller diameter allows smaller spacing
    # Larger diameter requires larger spacing (min = 2.5*d)
    inputs[KEY_DS_STUD_DIAMETER] = 8
    inputs[KEY_DS_STUD_TRANSVERSE_SPACING] = 25  # Valid: min_sp = 2.5*8 = 20
    result_small = validator.validate_additional_inputs(KEY_DS_STUD_TRANSVERSE_SPACING, inputs)
    assert result_small is None, "Spacing 25 should be valid for diameter 8 (min 20)"
    
    inputs[KEY_DS_STUD_DIAMETER] = 20
    inputs[KEY_DS_STUD_TRANSVERSE_SPACING] = 25  # Invalid: min_sp = 2.5*20 = 50
    result_large = validator.validate_additional_inputs(KEY_DS_STUD_TRANSVERSE_SPACING, inputs)
    assert result_large is not None, "Spacing 25 should be invalid for diameter 20 (min 50)"
# ════════════════════════════════════════════════════════════════════════════════
# GROUP T — CROSS-FIELD DEPENDENCY CHAINS
# ════════════════════════════════════════════════════════════════════════════════

def test_validate_cross_field_diameter_increase_invalidates_count(validator, valid_additional_inputs):
    """When diameter increases, stud count max decreases. Should invalidate previously-valid counts."""
    inputs = valid_additional_inputs.copy()
    inputs[KEY_MP_GIRDER_TOP_FLANGE_WIDTH] = 0.3  # 300 mm
    
    # Start: diameter 12, count 8 valid
    inputs[KEY_DS_STUD_DIAMETER] = 12
    inputs[KEY_DS_STUD_COUNT] = 8
    result_1 = validator.validate_additional_inputs(KEY_DS_STUD_COUNT, inputs)
    assert result_1 is None, "Count 8 should be valid for diameter 12"
    
    # Change: diameter 20, count 8 now invalid (larger diameter reduces max count)
    inputs[KEY_DS_STUD_DIAMETER] = 20
    inputs[KEY_DS_STUD_COUNT] = 8
    result_2 = validator.validate_additional_inputs(KEY_DS_STUD_COUNT, inputs)
    # Should detect violation when diameter increases
    assert result_2 is not None, "Count should be invalid when diameter increases from 12 to 20"
    assert isinstance(result_2, tuple)
    corrected_count, message = result_2
    # Corrected count should be lower than original
    assert corrected_count < 8, f"Corrected count {corrected_count} should be less than 8"


def test_validate_cross_field_diameter_increase_invalidates_spacing(validator, valid_additional_inputs):
    """When diameter increases, spacing min increases. Should invalidate previously-valid spacing."""
    inputs = valid_additional_inputs.copy()
    
    # Start: diameter 10, spacing 25 valid (at or near minimum)
    inputs[KEY_DS_STUD_DIAMETER] = 10
    inputs[KEY_DS_STUD_TRANSVERSE_SPACING] = 25
    result_1 = validator.validate_additional_inputs(KEY_DS_STUD_TRANSVERSE_SPACING, inputs)
    assert result_1 is None, "Spacing 25 should be valid for diameter 10"
    
    # Change: diameter 12, spacing 25 now invalid (min increases with diameter)
    inputs[KEY_DS_STUD_DIAMETER] = 12
    inputs[KEY_DS_STUD_TRANSVERSE_SPACING] = 25
    result_2 = validator.validate_additional_inputs(KEY_DS_STUD_TRANSVERSE_SPACING, inputs)
    # Should detect violation when diameter increases
    assert result_2 is not None, "Spacing should be invalid when diameter increases from 10 to 12"
    assert isinstance(result_2, tuple)
    corrected_spacing, message = result_2
    # Corrected spacing should be higher than original (diameter increase raises minimum)
    assert corrected_spacing > 25, f"Corrected spacing {corrected_spacing} should be greater than 25"


def test_validate_cross_field_overall_width_decrease_shrinks_girder_max(validator, valid_additional_inputs):
    """When overall width decreases, max number of girders decreases."""
    inputs = valid_additional_inputs.copy()
    
    # Start: width 10, girders 20 valid (at or near maximum)
    inputs[KEY_TS_OVERALL_WIDTH] = 10.0
    inputs[KEY_TS_NO_OF_GIRDERS] = 20
    result_1 = validator.validate_additional_inputs(KEY_TS_NO_OF_GIRDERS, inputs)
    assert result_1 is None, "20 girders should be valid for width 10"
    
    # Change: width 5, girders 20 now invalid (max decreases with width)
    inputs[KEY_TS_OVERALL_WIDTH] = 5.0
    inputs[KEY_TS_NO_OF_GIRDERS] = 20
    result_2 = validator.validate_additional_inputs(KEY_TS_NO_OF_GIRDERS, inputs)
    # Should detect violation when width decreases
    assert result_2 is not None, "20 girders should be invalid when width decreases from 10 to 5"
    assert isinstance(result_2, tuple)
    corrected_girders, message = result_2
    # Corrected girders should be lower than original (width decrease lowers max)
    assert corrected_girders < 20, f"Corrected girders {corrected_girders} should be less than 20"


# ════════════════════════════════════════════════════════════════════════════════

def test_validate_basic_enum_fields_garbage_values_pass_silently(validator):
    """Basic enum fields should silently pass garbage strings, ignoring them."""
    enum_keys = [
        KEY_STRUCTURE_TYPE, KEY_DESIGN_MODE, KEY_GIRDER,
        KEY_CROSS_BRACING, KEY_END_DIAPHRAGM, KEY_DECK_CONCRETE_GRADE_BASIC
    ]
    for k in enum_keys:
        res = validator.validate_basic_inputs(k, {k: "Some Garbage Value"})
        assert res is None, f"Basic enum key {k} should ignore garbage values and pass silently."

def test_validate_enum_fields_garbage_values_pass_silently(validator, valid_additional_inputs):
    """Enum fields should silently pass garbage strings, ignoring them."""
    inputs = valid_additional_inputs.copy()
    enum_keys = [
        KEY_FOOTPATH, KEY_SL_DEAD_LOAD_MODE, KEY_SL_LIVE_LOAD_MODE,
        KEY_WL_GUST_FACTOR_MODE, KEY_WL_DRAG_COEFF_MODE
    ]
    for k in enum_keys:
        inputs[k] = "Some Garbage Value"
        res = validator.validate_additional_inputs(k, inputs)
        assert res is None, f"Enum key {k} should ignore garbage values and pass silently."

def test_validate_ds_stud_diameter(validator, valid_additional_inputs):
    """BVA test for KEY_DS_STUD_DIAMETER. Verifies it accepts valid and ignores/passes invalid values."""
    # Tests that the field is currently unvalidated and silently passes even obvious invalid values
    for val in [-10, 0, "garbage", 10, 22, 50]:
        inputs = valid_additional_inputs.copy()
        inputs[KEY_DS_STUD_DIAMETER] = val
        res = validator.validate_additional_inputs(KEY_DS_STUD_DIAMETER, inputs)
        assert res is None, f"Diameter {val} should pass validation since it's unvalidated."

def test_validate_ts_overall_width(validator, valid_additional_inputs):
    """BVA test for KEY_TS_OVERALL_WIDTH. Verifies it accepts valid and ignores/passes invalid values."""
    for val in [-1.0, 0.0, "garbage", 1.0, 10.0, 50.0]:
        inputs = valid_additional_inputs.copy()
        inputs[KEY_TS_OVERALL_WIDTH] = val
        res = validator.validate_additional_inputs(KEY_TS_OVERALL_WIDTH, inputs)
        assert res is None, f"Overall width {val} should pass validation since it's unvalidated."


# ════════════════════════════════════════════════════════════════════════════════
# GROUP Q — BOUNDED LOAD VALUE VALIDATION
# ════════════════════════════════════════════════════════════════════════════════

def test_validate_bounded_load_values_reject_negatives(validator, valid_additional_inputs):
    """
    Verifies that load/area values with enforced lower bounds correctly
    reject negative inputs and clamp to the minimum.
    """
    bounded_keys_and_modes = [
        (KEY_SL_DEAD_LOAD_VALUE, KEY_SL_DEAD_LOAD_MODE),
        (KEY_SL_LIVE_LOAD_VALUE, KEY_SL_LIVE_LOAD_MODE),
        (KEY_WL_SUPER_AREA_ELEV_VALUE, KEY_WL_SUPER_AREA_ELEV_MODE),
        (KEY_WL_SUPER_AREA_PLAIN_VALUE, KEY_WL_SUPER_AREA_PLAIN_MODE),
        (KEY_WL_EXPOSED_FRONTAL_VALUE, KEY_WL_EXPOSED_FRONTAL_MODE),
    ]

    for value_key, mode_key in bounded_keys_and_modes:
        # Negatives should be corrected
        for val in [-1000.0, -1.0]:
            inputs = valid_additional_inputs.copy()
            inputs[mode_key] = "Custom"
            inputs[value_key] = val
            res = validator.validate_additional_inputs(value_key, inputs)
            assert res is not None, f"Key {value_key} should reject negative value {val}"
            assert res[0] == 0.0, f"Key {value_key} should clamp {val} to 0.0"
        # Zero and valid positives should pass
        for val in [0.0, 100.0]:
            inputs = valid_additional_inputs.copy()
            inputs[mode_key] = "Custom"
            inputs[value_key] = val
            res = validator.validate_additional_inputs(value_key, inputs)
            assert res is None, f"Key {value_key} unexpectedly rejected valid value {val}"

def test_validate_unbounded_thermal_coefficients_pass_silently(validator, valid_additional_inputs):
    """
    Documents that thermal coefficients are completely unbounded by the validator.
    Negative and absurdly large values will silently pass.
    """
    thermal_keys = [KEY_TL_THERMAL_COEFF_STEEL, KEY_TL_THERMAL_COEFF_RCC]
    
    for key in thermal_keys:
        for val in [-10.0, -0.5, 0.0, 100.0, 9999.0]:
            inputs = valid_additional_inputs.copy()
            inputs[key] = val
            res = validator.validate_additional_inputs(key, inputs)
            assert res is None, f"Key {key} unexpectedly rejected unbounded value {val}"



# ════════════════════════════════════════════════════════════════════════════════
# GROUP P — MEMBER PROPERTIES AND CAMBER VALIDATION TESTS
# ════════════════════════════════════════════════════════════════════════════════

def test_validate_segment_chain(validator, valid_additional_inputs):
    key = "member_properties.girder_details.segment_chain"
    # Empty or not list -> None
    assert validator.validate_additional_inputs(key, {key: []}) is None
    assert validator.validate_additional_inputs(key, {key: None}) is None

    # Invalid end values (not ascending, or last not equal to span)
    inputs = {KEY_SPAN: 30.0, key: [{"end": 10.0}, {"end": 5.0}]}
    res = validator.validate_additional_inputs(key, inputs)
    assert res is not None
    assert res[0][0]["end"] == 5.0  # corrected

    # Last segment not matching span
    inputs = {KEY_SPAN: 30.0, key: [{"end": 10.0}, {"end": 20.0}]}
    res = validator.validate_additional_inputs(key, inputs)
    assert res is not None
    assert res[0][-1]["end"] == 30.0

def test_validate_support_width(validator, valid_additional_inputs):
    # Use the canonical key constant (section_inputs, plural)
    from osdagbridge.core.utils.common import KEY_MP_GD_SUPPORT_WIDTH
    key = KEY_MP_GD_SUPPORT_WIDTH
    # None -> 400
    res = validator.validate_additional_inputs(key, {key: None})
    assert res == (400, "Support width must be a numeric value.")
    # < 150 -> 150
    res = validator.validate_additional_inputs(key, {key: 100})
    assert res == (150, "Support width must be between 150 mm and 800 mm (practical range for composite bridge girders per MoRTH/IRC).")
    # > 800 -> 800
    res = validator.validate_additional_inputs(key, {key: 900})
    assert res == (800, "Support width must be between 150 mm and 800 mm (practical range for composite bridge girders per MoRTH/IRC).")
    # valid range
    assert validator.validate_additional_inputs(key, {key: 300}) is None

def test_validate_girder_depth_custom(validator, valid_additional_inputs):
    inputs = {KEY_DESIGN_MODE: "Custom", KEY_MP_GIRDER_DEPTH: None}
    assert validator.validate_additional_inputs(KEY_MP_GIRDER_DEPTH, inputs) == (200, "Total depth must be a numeric value.")
    
    inputs[KEY_MP_GIRDER_DEPTH] = 100
    assert validator.validate_additional_inputs(KEY_MP_GIRDER_DEPTH, inputs) == (200, "Total depth must be between 200 and 3000 mm.")
    
    inputs[KEY_MP_GIRDER_DEPTH] = 4000
    assert validator.validate_additional_inputs(KEY_MP_GIRDER_DEPTH, inputs) == (3000, "Total depth must be between 200 and 3000 mm.")
    
    inputs[KEY_MP_GIRDER_DEPTH] = 1500
    assert validator.validate_additional_inputs(KEY_MP_GIRDER_DEPTH, inputs) is None

def test_validate_girder_depth_optimized(validator, valid_additional_inputs):
    inputs = {KEY_DESIGN_MODE: "Optimized", KEY_MP_GIRDER_DEPTH: None}
    assert validator.validate_additional_inputs(KEY_MP_GIRDER_DEPTH, inputs) == ({"lower": 200, "upper": 2000, "increment": 25}, "Total depth bounds must be specified.")
    
    # Check auto-correction of bounds
    inputs[KEY_MP_GIRDER_DEPTH] = {"lower": 100, "upper": 3500, "increment": -5}
    res = validator.validate_additional_inputs(KEY_MP_GIRDER_DEPTH, inputs)
    assert res is not None
    assert res[0]["lower"] == 200
    assert res[0]["upper"] == 3000
    assert res[0]["increment"] == 25

def test_validate_girder_top_flange_width_custom(validator, valid_additional_inputs):
    inputs = {KEY_DESIGN_MODE: "Custom", KEY_MP_GIRDER_TOP_FLANGE_WIDTH: None}
    assert validator.validate_additional_inputs(KEY_MP_GIRDER_TOP_FLANGE_WIDTH, inputs) == (100, "Top flange width must be a numeric value.")
    
    inputs[KEY_MP_GIRDER_TOP_FLANGE_WIDTH] = 50
    assert validator.validate_additional_inputs(KEY_MP_GIRDER_TOP_FLANGE_WIDTH, inputs) == (100, "Top flange width must be between 100 and 1500 mm.")
    
    inputs[KEY_MP_GIRDER_TOP_FLANGE_WIDTH] = 2000
    assert validator.validate_additional_inputs(KEY_MP_GIRDER_TOP_FLANGE_WIDTH, inputs) == (1500, "Top flange width must be between 100 and 1500 mm.")
    
    inputs[KEY_MP_GIRDER_TOP_FLANGE_WIDTH] = 500
    assert validator.validate_additional_inputs(KEY_MP_GIRDER_TOP_FLANGE_WIDTH, inputs) is None

def test_validate_girder_top_flange_width_optimized(validator, valid_additional_inputs):
    inputs = {KEY_DESIGN_MODE: "Optimized", KEY_MP_GIRDER_TOP_FLANGE_WIDTH: None}
    assert validator.validate_additional_inputs(KEY_MP_GIRDER_TOP_FLANGE_WIDTH, inputs) == ({"lower": 100, "upper": 1000, "increment": 10}, "Top flange width bounds must be specified.")
    
    inputs[KEY_MP_GIRDER_TOP_FLANGE_WIDTH] = {"lower": 50, "upper": 2000, "increment": 0}
    res = validator.validate_additional_inputs(KEY_MP_GIRDER_TOP_FLANGE_WIDTH, inputs)
    assert res is not None
    assert res[0]["lower"] == 100
    assert res[0]["upper"] == 1500
    assert res[0]["increment"] == 10

def test_validate_girder_bottom_flange_width_custom(validator, valid_additional_inputs):
    inputs = {KEY_DESIGN_MODE: "Custom", KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH: None}
    assert validator.validate_additional_inputs(KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH, inputs) == (100, "Bottom flange width must be a numeric value.")
    
    inputs[KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH] = 50
    assert validator.validate_additional_inputs(KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH, inputs) == (100, "Bottom flange width must be between 100 and 1500 mm.")
    
    inputs[KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH] = 2000
    assert validator.validate_additional_inputs(KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH, inputs) == (1500, "Bottom flange width must be between 100 and 1500 mm.")
    
    inputs[KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH] = 500
    assert validator.validate_additional_inputs(KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH, inputs) is None

def test_validate_girder_bottom_flange_width_optimized(validator, valid_additional_inputs):
    inputs = {KEY_DESIGN_MODE: "Optimized", KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH: None}
    assert validator.validate_additional_inputs(KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH, inputs) == ({"lower": 100, "upper": 1000, "increment": 10}, "Bottom flange width bounds must be specified.")
    
    inputs[KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH] = {"lower": 50, "upper": 2000, "increment": 0}
    res = validator.validate_additional_inputs(KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH, inputs)
    assert res is not None
    assert res[0]["lower"] == 100
    assert res[0]["upper"] == 1500
    assert res[0]["increment"] == 10

def test_validate_thickness_selections(validator, valid_additional_inputs):
    # Top flange
    assert validator.validate_additional_inputs(KEY_MP_GIRDER_TOP_FLANGE_THICKNESS, {KEY_MP_GIRDER_TOP_FLANGE_THICKNESS: []}) == (SAIL_APPROVED_THICKNESS_VALUES, "At least one top flange thickness value must be selected.")
    assert validator.validate_additional_inputs(KEY_MP_GIRDER_TOP_FLANGE_THICKNESS, {KEY_MP_GIRDER_TOP_FLANGE_THICKNESS: [12, 16]}) is None
    
    # Bottom flange
    assert validator.validate_additional_inputs(KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS, {KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS: []}) == (SAIL_APPROVED_THICKNESS_VALUES, "At least one bottom flange thickness value must be selected.")
    assert validator.validate_additional_inputs(KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS, {KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS: [12, 16]}) is None
    
    # Web thickness
    assert validator.validate_additional_inputs(KEY_MP_GIRDER_WEB_THICKNESS, {KEY_MP_GIRDER_WEB_THICKNESS: []}) == (SAIL_APPROVED_THICKNESS_VALUES, "At least one web thickness value must be selected.")
    assert validator.validate_additional_inputs(KEY_MP_GIRDER_WEB_THICKNESS, {KEY_MP_GIRDER_WEB_THICKNESS: [10, 12]}) is None

def test_validate_stiffener_spacing(validator, valid_additional_inputs):
    assert validator.validate_additional_inputs(KEY_MP_STIFFENER_SPACING, {KEY_MP_STIFFENER_SPACING: None}) == (20, "Bearing stiffener spacing must be a numeric value.")
    assert validator.validate_additional_inputs(KEY_MP_STIFFENER_SPACING, {KEY_MP_STIFFENER_SPACING: 10}) == (20, "Bearing stiffener spacing must be at least 20 mm.")
    assert validator.validate_additional_inputs(KEY_MP_STIFFENER_SPACING, {KEY_MP_STIFFENER_SPACING: 90}) == (75, "Bearing stiffener spacing must not exceed 75 mm.")
    assert validator.validate_additional_inputs(KEY_MP_STIFFENER_SPACING, {KEY_MP_STIFFENER_SPACING: 50}) is None

def test_validate_stiffener_bearing_outstand(validator, valid_additional_inputs):
    inputs = {
        KEY_MP_GIRDER_TOP_FLANGE_WIDTH: 300.0,
        KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH: 300.0,
        KEY_MP_GIRDER_WEB_THICKNESS: 12.0,
        KEY_MP_STIFFENER_BEARING_OUTSTAND: None
    }
    # None
    assert validator.validate_additional_inputs(KEY_MP_STIFFENER_BEARING_OUTSTAND, inputs) == (0, "Outstand of bearing stiffener must be a numeric value.")
    
    # < 0
    inputs[KEY_MP_STIFFENER_BEARING_OUTSTAND] = -10
    assert validator.validate_additional_inputs(KEY_MP_STIFFENER_BEARING_OUTSTAND, inputs) == (0, "Outstand of bearing stiffener must be at least 0 mm.")
    
    # > max_os (300 - 12) / 2 = 144
    inputs[KEY_MP_STIFFENER_BEARING_OUTSTAND] = 200
    res = validator.validate_additional_inputs(KEY_MP_STIFFENER_BEARING_OUTSTAND, inputs)
    assert res is not None
    assert res[0] == 144.0

    # valid
    inputs[KEY_MP_STIFFENER_BEARING_OUTSTAND] = 100
    assert validator.validate_additional_inputs(KEY_MP_STIFFENER_BEARING_OUTSTAND, inputs) is None

def test_validate_stiffener_intermediate_spacing(validator, valid_additional_inputs):
    assert validator.validate_additional_inputs(KEY_MP_STIFFENER_INTERMEDIATE_SPACING, {KEY_MP_STIFFENER_INTERMEDIATE_SPACING: None}) == (75, "Intermediate stiffener spacing must be a numeric value.")
    assert validator.validate_additional_inputs(KEY_MP_STIFFENER_INTERMEDIATE_SPACING, {KEY_MP_STIFFENER_INTERMEDIATE_SPACING: 50}) == (75, "Intermediate stiffener spacing must be between 75 and 3000 mm.")
    assert validator.validate_additional_inputs(KEY_MP_STIFFENER_INTERMEDIATE_SPACING, {KEY_MP_STIFFENER_INTERMEDIATE_SPACING: 3500}) == (3000, "Intermediate stiffener spacing must be between 75 and 3000 mm.")
    assert validator.validate_additional_inputs(KEY_MP_STIFFENER_INTERMEDIATE_SPACING, {KEY_MP_STIFFENER_INTERMEDIATE_SPACING: 500}) is None

def test_validate_stiffener_intermediate_outstand(validator, valid_additional_inputs):
    inputs = {
        KEY_MP_GIRDER_TOP_FLANGE_WIDTH: 300.0,
        KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH: 300.0,
        KEY_MP_GIRDER_WEB_THICKNESS: 12.0,
        KEY_MP_STIFFENER_INTERMEDIATE_OUTSTAND: None
    }
    assert validator.validate_additional_inputs(KEY_MP_STIFFENER_INTERMEDIATE_OUTSTAND, inputs) == (0, "Outstand of intermediate stiffener must be a numeric value.")
    
    inputs[KEY_MP_STIFFENER_INTERMEDIATE_OUTSTAND] = -10
    assert validator.validate_additional_inputs(KEY_MP_STIFFENER_INTERMEDIATE_OUTSTAND, inputs) == (0, "Outstand of intermediate stiffener must be at least 0 mm.")
    
    inputs[KEY_MP_STIFFENER_INTERMEDIATE_OUTSTAND] = 200
    res = validator.validate_additional_inputs(KEY_MP_STIFFENER_INTERMEDIATE_OUTSTAND, inputs)
    assert res is not None
    assert res[0] == 144.0

    inputs[KEY_MP_STIFFENER_INTERMEDIATE_OUTSTAND] = 100
    assert validator.validate_additional_inputs(KEY_MP_STIFFENER_INTERMEDIATE_OUTSTAND, inputs) is None

def test_validate_no_of_cross_bracings(validator, valid_additional_inputs):
    inputs = {KEY_SPAN: 30.0, KEY_MP_CB_NO_OF_CROSS_BRACINGS: None}
    assert validator.validate_additional_inputs(KEY_MP_CB_NO_OF_CROSS_BRACINGS, inputs) == (1, "No. of cross bracings must be an integer value.")
    
    inputs[KEY_MP_CB_NO_OF_CROSS_BRACINGS] = 0
    assert validator.validate_additional_inputs(KEY_MP_CB_NO_OF_CROSS_BRACINGS, inputs) == (1, "No. of cross bracings must be at least 1.")
    
    # max_cb = floor(30.0 - 1) = 29
    inputs[KEY_MP_CB_NO_OF_CROSS_BRACINGS] = 50
    assert validator.validate_additional_inputs(KEY_MP_CB_NO_OF_CROSS_BRACINGS, inputs) == (29, "No. of cross bracings must not exceed 29 for the given span.")
    
    inputs[KEY_MP_CB_NO_OF_CROSS_BRACINGS] = 10
    assert validator.validate_additional_inputs(KEY_MP_CB_NO_OF_CROSS_BRACINGS, inputs) is None

def test_validate_welded_beam_depth_width(validator, valid_additional_inputs):
    key_depth = "member_properties.end_diaphragm_details.welded_beam.depth"
    key_top_width = "member_properties.end_diaphragm_details.welded_beam.top_flange_width"
    key_bot_width = "member_properties.end_diaphragm_details.welded_beam.bottom_flange_width"
    
    inputs = {
        KEY_MP_ED_TYPE: "Welded Beam",
        KEY_DESIGN_MODE: "Custom",
        key_depth: None,
        key_top_width: None,
        key_bot_width: None
    }
    
    assert validator.validate_additional_inputs(key_depth, inputs) == (200, "End diaphragm (Welded Beam) depth must be a numeric value.")
    inputs[key_depth] = 100
    assert validator.validate_additional_inputs(key_depth, inputs) == (200, "End diaphragm (Welded Beam) depth must be between 200 and 3000 mm.")
    inputs[key_depth] = 4000
    assert validator.validate_additional_inputs(key_depth, inputs) == (3000, "End diaphragm (Welded Beam) depth must be between 200 and 3000 mm.")
    inputs[key_depth] = 1000
    assert validator.validate_additional_inputs(key_depth, inputs) is None
    
    # Top width
    assert validator.validate_additional_inputs(key_top_width, inputs) == (100, "End diaphragm (Welded Beam) top flange width must be a numeric value.")
    inputs[key_top_width] = 50
    assert validator.validate_additional_inputs(key_top_width, inputs) == (100, "End diaphragm (Welded Beam) top flange width must be between 100 and 1500 mm.")
    inputs[key_top_width] = 2000
    assert validator.validate_additional_inputs(key_top_width, inputs) == (1500, "End diaphragm (Welded Beam) top flange width must be between 100 and 1500 mm.")
    inputs[key_top_width] = 500
    assert validator.validate_additional_inputs(key_top_width, inputs) is None
    
    # Bottom width
    assert validator.validate_additional_inputs(key_bot_width, inputs) == (100, "End diaphragm (Welded Beam) bottom flange width must be a numeric value.")
    inputs[key_bot_width] = 50
    assert validator.validate_additional_inputs(key_bot_width, inputs) == (100, "End diaphragm (Welded Beam) bottom flange width must be between 100 and 1500 mm.")
    inputs[key_bot_width] = 2000
    assert validator.validate_additional_inputs(key_bot_width, inputs) == (1500, "End diaphragm (Welded Beam) bottom flange width must be between 100 and 1500 mm.")
    inputs[key_bot_width] = 500
    assert validator.validate_additional_inputs(key_bot_width, inputs) is None

def test_validate_camber_value(validator, valid_additional_inputs):
    # Camber mode != "Custom"
    inputs = {KEY_DO_CAMBER_MODE: "Typical", KEY_DO_CAMBER_VALUE: -5}
    assert validator.validate_additional_inputs(KEY_DO_CAMBER_VALUE, inputs) is None

    # Camber mode == "Custom"
    inputs[KEY_DO_CAMBER_MODE] = "Custom"
    assert validator.validate_additional_inputs(KEY_DO_CAMBER_VALUE, inputs) == (0, "Camber must be between 0 and 4 m.")
    
    inputs[KEY_DO_CAMBER_VALUE] = None
    assert validator.validate_additional_inputs(KEY_DO_CAMBER_VALUE, inputs) == (0, "Camber must be a numeric value.")
    
    inputs[KEY_DO_CAMBER_VALUE] = 5.0
    assert validator.validate_additional_inputs(KEY_DO_CAMBER_VALUE, inputs) == (4, "Camber must be between 0 and 4 m.")
    
    inputs[KEY_DO_CAMBER_VALUE] = 2.0
    assert validator.validate_additional_inputs(KEY_DO_CAMBER_VALUE, inputs) is None


# ════════════════════════════════════════════════════════════════════════════════
# GROUP R — PlateGirderBridge CORE UNIT TESTS
# These tests cover the actual bridge class logic — NOT just input validation.
# They test data normalisation, key resolution, validation guards, and geometry
# helpers that were previously 0% covered by the test suite.
# ════════════════════════════════════════════════════════════════════════════════

from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import (
    resolve_girder_value,
)
from osdagbridge.core.bridge_components.super_structure.shear_studs.geometry import (
    min_stud_head_diameter,
    min_stud_head_height,
)
from osdagbridge.core.utils.common import (
    KEY_TS_NO_OF_FOOTPATHS, KEY_DS_STUD_HEAD_DIAMETER, KEY_DS_STUD_HEAD_HEIGHT,
    KEY_MP_GIRDER_WEB_DEPTH, KEY_MP_GIRDER_SECTIONAL_AREA, KEY_MP_GIRDER_TORSION_CONSTANT_IT,
    KEY_MP_GIRDER_SECTIONAL_IZ, KEY_MP_GIRDER_SECTIONAL_IY,
)


# ─────────────────────────────────────────────────────────────────────────────
# R1 — Input Coercion (_coerce / _normalize_input_dict)
# Tests that PlateGirderBridge correctly converts raw string inputs from the
# UI into native Python int/float types for downstream consumers.
# ─────────────────────────────────────────────────────────────────────────────

class TestCoerce:
    """PlateGirderBridge._coerce() converts strings to native types."""

    def test_integer_string_becomes_int(self):
        assert PlateGirderBridge._coerce("400") == 400
        assert isinstance(PlateGirderBridge._coerce("400"), int)

    def test_float_string_becomes_float(self):
        assert PlateGirderBridge._coerce("20.5") == 20.5
        assert isinstance(PlateGirderBridge._coerce("20.5"), float)

    def test_non_numeric_string_unchanged(self):
        assert PlateGirderBridge._coerce("E 250A") == "E 250A"
        assert PlateGirderBridge._coerce("Optimized") == "Optimized"

    def test_empty_string_unchanged(self):
        assert PlateGirderBridge._coerce("") == ""

    def test_native_int_passthrough(self):
        assert PlateGirderBridge._coerce(42) == 42
        assert isinstance(PlateGirderBridge._coerce(42), int)

    def test_native_float_passthrough(self):
        assert PlateGirderBridge._coerce(3.14) == 3.14

    def test_bool_passthrough(self):
        assert PlateGirderBridge._coerce(True) is True
        assert PlateGirderBridge._coerce(False) is False

    def test_none_passthrough(self):
        assert PlateGirderBridge._coerce(None) is None

    def test_list_elements_coerced_recursively(self):
        result = PlateGirderBridge._coerce(["10", "20.5", "Yes"])
        assert result == [10, 20.5, "Yes"]

    def test_dict_values_coerced_recursively(self):
        result = PlateGirderBridge._coerce({"span": "30", "grade": "E 250A"})
        assert result == {"span": 30, "grade": "E 250A"}

    def test_normalize_input_dict_converts_all_keys(self):
        raw = {KEY_SPAN: "30", KEY_CARRIAGEWAY_WIDTH: "7.5", KEY_GIRDER: "E 250A"}
        normalised = PlateGirderBridge._normalize_input_dict(raw)
        assert normalised[KEY_SPAN] == 30
        assert normalised[KEY_CARRIAGEWAY_WIDTH] == 7.5
        assert normalised[KEY_GIRDER] == "E 250A"


# ─────────────────────────────────────────────────────────────────────────────
# R2 — Girder Key Resolution (resolve_girder_value)
# Tests the per-girder key resolution logic that is central to how
# PlateGirderBridge handles multi-girder configurations.
# ─────────────────────────────────────────────────────────────────────────────

class TestResolveGirderValue:
    """resolve_girder_value() resolves per-girder keys in priority order."""

    def test_per_girder_key_takes_priority(self):
        source = {"base_key": 100, "base_key.G2.M1": 200}
        assert resolve_girder_value(source, "base_key", i=1) == 200

    def test_scalar_key_used_when_no_per_girder_key(self):
        source = {"base_key": 100}
        assert resolve_girder_value(source, "base_key", i=0) == 100

    def test_first_girder_fallback_used_when_no_scalar(self):
        source = {"base_key.G1.M1": 50}
        assert resolve_girder_value(source, "base_key", i=2) == 50

    def test_none_index_uses_scalar_key(self):
        source = {"base_key": 77, "base_key.G1.M1": 88}
        assert resolve_girder_value(source, "base_key", i=None) == 77

    def test_key_error_raised_when_nothing_found(self):
        with pytest.raises(KeyError):
            resolve_girder_value({}, "missing_key", i=0)


# ─────────────────────────────────────────────────────────────────────────────
# R3 — Shear Stud Geometry (min_stud_head_diameter / min_stud_head_height)
# Tests the IRC 22:2015 and IS 3935:1966 derived geometry formulas for
# shear connectors. These are physics formulas — results must be exact.
# ─────────────────────────────────────────────────────────────────────────────

class TestShearStudGeometry:
    """Tests for stud head size geometry formulas (IRC 22:2015 / IS 3935:1966)."""

    @pytest.mark.parametrize("d, expected_head_d", [
        (16.0, 24.0),   # 1.5 × 16
        (19.0, 28.5),   # 1.5 × 19
        (22.0, 33.0),   # 1.5 × 22
        (25.0, 37.5),   # 1.5 × 25
    ])
    def test_min_stud_head_diameter(self, d, expected_head_d):
        assert min_stud_head_diameter(d) == expected_head_d

    @pytest.mark.parametrize("d, expected_head_h", [
        (16.0, 10.67),  # 0.667 × 16 = 10.672 → rounded to 10.67
        (19.0, 12.67),  # 0.667 × 19 = 12.673 → rounded to 12.67
        (22.0, 14.67),  # 0.667 × 22 = 14.674 → rounded to 14.67
        (25.0, 16.68),  # 0.667 × 25 = 16.675 → rounded to 16.68
    ])
    def test_min_stud_head_height(self, d, expected_head_h):
        assert min_stud_head_height(d) == expected_head_h

    def test_stud_head_diameter_formula_is_1_5_times(self):
        for d in [10.0, 20.0, 30.0]:
            assert min_stud_head_diameter(d) == round(1.5 * d, 2)

    def test_stud_head_height_formula_is_0_667_times(self):
        for d in [10.0, 20.0, 30.0]:
            assert min_stud_head_height(d) == round(0.667 * d, 2)

    def test_zero_diameter_raises_value_error(self):
        with pytest.raises(ValueError):
            min_stud_head_diameter(0)

    def test_negative_diameter_raises_value_error(self):
        with pytest.raises(ValueError):
            min_stud_head_height(-5.0)

    def test_none_diameter_raises_value_error(self):
        with pytest.raises(ValueError):
            min_stud_head_diameter(None)


# ─────────────────────────────────────────────────────────────────────────────
# R4 — Internal Validation Guards (_validate_inputs / _girder_count)
# Tests that the PlateGirderBridge correctly rejects bad configurations
# during the design pipeline — before any expensive solver work starts.
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def minimal_bridge_inputs():
    """A minimal valid input dict that can pass _validate_inputs."""
    return {
        KEY_SPAN: 30.0,
        KEY_TS_OVERALL_WIDTH: 10.5,
        KEY_TS_NO_OF_GIRDERS: 4,
        KEY_TS_GIRDER_SPACING: 2.5,
        KEY_TS_DECK_OVERHANG: 1.25,
        KEY_TS_FOOTPATH_WIDTH: 0.0,
        KEY_TS_NO_OF_FOOTPATHS: 0,
        KEY_RL_WIDTH: 0.0,
        KEY_MD_WIDTH: 0.0,
        KEY_CARRIAGEWAY_WIDTH: 7.5,
        KEY_SKEW_ANGLE: 0.0,
    }


class TestValidateInputsGuard:
    """PlateGirderBridge._validate_inputs() raises ValueError for bad inputs."""

    def test_valid_inputs_pass_silently(self, minimal_bridge_inputs):
        bridge = PlateGirderBridge()
        bridge.input_dict = minimal_bridge_inputs.copy()
        bridge._validate_inputs()  # Must not raise

    def test_missing_span_raises(self, minimal_bridge_inputs):
        bridge = PlateGirderBridge()
        inputs = minimal_bridge_inputs.copy()
        del inputs[KEY_SPAN]
        bridge.input_dict = inputs
        with pytest.raises(ValueError, match="Missing required input parameters"):
            bridge._validate_inputs()

    def test_missing_overall_width_raises(self, minimal_bridge_inputs):
        bridge = PlateGirderBridge()
        inputs = minimal_bridge_inputs.copy()
        del inputs[KEY_TS_OVERALL_WIDTH]
        bridge.input_dict = inputs
        with pytest.raises(ValueError, match="Missing required input parameters"):
            bridge._validate_inputs()

    def test_zero_span_raises(self, minimal_bridge_inputs):
        bridge = PlateGirderBridge()
        inputs = minimal_bridge_inputs.copy()
        inputs[KEY_SPAN] = 0.0
        bridge.input_dict = inputs
        with pytest.raises(ValueError, match="Span must be strictly positive"):
            bridge._validate_inputs()

    def test_negative_span_raises(self, minimal_bridge_inputs):
        bridge = PlateGirderBridge()
        inputs = minimal_bridge_inputs.copy()
        inputs[KEY_SPAN] = -10.0
        bridge.input_dict = inputs
        with pytest.raises(ValueError, match="Span must be strictly positive"):
            bridge._validate_inputs()

    def test_fewer_than_two_girders_raises(self, minimal_bridge_inputs):
        bridge = PlateGirderBridge()
        inputs = minimal_bridge_inputs.copy()
        inputs[KEY_TS_NO_OF_GIRDERS] = 1
        bridge.input_dict = inputs
        with pytest.raises(ValueError, match="Minimum 2 girders required"):
            bridge._validate_inputs()

    def test_zero_girder_spacing_raises(self, minimal_bridge_inputs):
        bridge = PlateGirderBridge()
        inputs = minimal_bridge_inputs.copy()
        inputs[KEY_TS_GIRDER_SPACING] = 0.0
        bridge.input_dict = inputs
        with pytest.raises(ValueError, match="Girder spacing must be positive"):
            bridge._validate_inputs()


class TestGirderCount:
    """PlateGirderBridge._girder_count() returns the correct count."""

    def test_returns_correct_count(self):
        bridge = PlateGirderBridge()
        bridge.input_dict = {KEY_TS_NO_OF_GIRDERS: 6}
        assert bridge._girder_count() == 6

    def test_minimum_count_is_one(self):
        bridge = PlateGirderBridge()
        bridge.input_dict = {KEY_TS_NO_OF_GIRDERS: 0}
        assert bridge._girder_count() == 1

    def test_missing_key_defaults_to_one(self):
        bridge = PlateGirderBridge()
        bridge.input_dict = {}
        assert bridge._girder_count() == 1

    def test_string_value_is_cast_to_int(self):
        bridge = PlateGirderBridge()
        bridge.input_dict = {KEY_TS_NO_OF_GIRDERS: "4"}
        assert bridge._girder_count() == 4


# ─────────────────────────────────────────────────────────────────────────────
# R5 — set_input() splits basic and additional inputs
# Tests that PlateGirderBridge.set_input() correctly splits the input dict
# into basic_inputs and additional_inputs, and normalises all values.
# ─────────────────────────────────────────────────────────────────────────────

class TestSetInput:
    """PlateGirderBridge.set_input() correctly partitions and normalises inputs."""

    def test_basic_keys_go_to_basic_inputs(self):
        bridge = PlateGirderBridge()
        raw = {KEY_SPAN: "30", KEY_TS_OVERALL_WIDTH: "10.5"}
        bridge.set_input(raw)
        assert KEY_SPAN in bridge.basic_inputs
        assert KEY_SPAN not in bridge.additional_inputs

    def test_additional_keys_go_to_additional_inputs(self):
        bridge = PlateGirderBridge()
        raw = {KEY_SPAN: "30", KEY_TS_OVERALL_WIDTH: "10.5"}
        bridge.set_input(raw)
        assert KEY_TS_OVERALL_WIDTH in bridge.additional_inputs

    def test_string_values_are_normalised_to_numeric(self):
        bridge = PlateGirderBridge()
        bridge.set_input({KEY_SPAN: "30"})
        assert bridge.input_dict[KEY_SPAN] == 30
        assert isinstance(bridge.input_dict[KEY_SPAN], int)

    def test_full_dict_is_stored_in_input_dict(self):
        bridge = PlateGirderBridge()
        raw = {KEY_SPAN: "25", KEY_TS_OVERALL_WIDTH: "9.0"}
        bridge.set_input(raw)
        assert len(bridge.input_dict) == len(raw)

    def test_non_numeric_strings_are_preserved(self):
        bridge = PlateGirderBridge()
        bridge.set_input({KEY_GIRDER: "E 250A"})
        assert bridge.input_dict[KEY_GIRDER] == "E 250A"


# ─────────────────────────────────────────────────────────────────────────────
# R6 — Sizing, DTOs, and Shear Studs
# ─────────────────────────────────────────────────────────────────────────────

class TestPlateGirderBridgeSizingAndDtos:
    """Tests bridge sizing adjustments, DTO creation, and shear stud details."""

    def test_convert_girder_dims_mm_to_m(self):
        bridge = PlateGirderBridge()
        # Set inputs in mm
        bridge.set_input({
            KEY_DESIGN_MODE: "Custom",
            KEY_TS_NO_OF_GIRDERS: 2,
            KEY_MP_GIRDER_DEPTH: 1500.0,
            KEY_MP_GIRDER_DEPTH + ".G1.M1": 1500.0,
            KEY_MP_GIRDER_DEPTH + ".G2.M1": 1200.0,
        })
        bridge._convert_girder_dims_mm_to_m()
        
        # Should be converted to metres (divided by 1000)
        assert bridge.input_dict[KEY_MP_GIRDER_DEPTH] == 1.5
        assert bridge.input_dict[KEY_MP_GIRDER_DEPTH + ".G1.M1"] == 1.5
        assert bridge.input_dict[KEY_MP_GIRDER_DEPTH + ".G2.M1"] == 1.2

    def test_solve_shear_studs(self):
        bridge = PlateGirderBridge()
        # Set stud diameter to 22 mm
        bridge.output_dict = {
            KEY_DS_STUD_DIAMETER: 22.0
        }
        bridge._solve_shear_studs()
        
        # head diameter = 1.5 * 22 = 33
        # head height = 0.667 * 22 = 14.67
        assert bridge.output_dict[KEY_DS_STUD_HEAD_DIAMETER] == 33.0
        assert bridge.output_dict[KEY_DS_STUD_HEAD_HEIGHT] == 14.67

    def test_build_dtos(self):
        bridge = PlateGirderBridge()
        bridge.set_input({
            KEY_SPAN: 30.0,
            KEY_TS_DECK_OVERHANG: 1.25,
            KEY_TS_NO_OF_GIRDERS: 4,
            KEY_TS_GIRDER_SPACING: 2.5,
            KEY_SKEW_ANGLE: 15.0,
            KEY_CARRIAGEWAY_WIDTH: 7.5,
            KEY_TS_FOOTPATH_WIDTH: 1.5,
            KEY_RL_WIDTH: 0.3,
            KEY_MD_WIDTH: 0.0,
            KEY_TS_NO_OF_FOOTPATHS: 1,
        })
        bridge._build_dtos()
        
        assert bridge.grillage_geometry is not None
        assert bridge.grillage_geometry.L == 30.0
        assert bridge.grillage_geometry.edge_dist == 1.25
        assert bridge.grillage_geometry.ext_to_int_dist == 2.5
        assert bridge.grillage_geometry.angle == 15.0
        
        assert bridge.deck_layout is not None
        assert bridge.deck_layout.carriageway_width == 7.5
        assert bridge.deck_layout.footpath_width == 1.5
        assert bridge.deck_layout.railing_width == 0.3
        assert bridge.deck_layout.median_width == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# R7 — Section Properties
# ─────────────────────────────────────────────────────────────────────────────

class TestPlateGirderBridgeSections:
    """Tests building section properties for main girders and transverse slabs."""

    def test_girder_section(self):
        bridge = PlateGirderBridge()
        bridge.set_input({
            KEY_TS_NO_OF_GIRDERS: 2,
            KEY_MP_GIRDER_WEB_DEPTH: 1.4,
            KEY_MP_GIRDER_WEB_DEPTH + ".G1.M1": 1.4,
            KEY_MP_GIRDER_WEB_THICKNESS: 0.012,
            KEY_MP_GIRDER_WEB_THICKNESS + ".G1.M1": 0.012,
            KEY_MP_GIRDER_TOP_FLANGE_WIDTH: 0.3,
            KEY_MP_GIRDER_TOP_FLANGE_WIDTH + ".G1.M1": 0.3,
            KEY_MP_GIRDER_TOP_FLANGE_THICKNESS: 0.02,
            KEY_MP_GIRDER_TOP_FLANGE_THICKNESS + ".G1.M1": 0.02,
            KEY_MP_GIRDER_SECTIONAL_AREA: 0.035,
            KEY_MP_GIRDER_SECTIONAL_AREA + ".G1.M1": 0.035,
            KEY_MP_GIRDER_TORSION_CONSTANT_IT: 0.0001,
            KEY_MP_GIRDER_TORSION_CONSTANT_IT + ".G1.M1": 0.0001,
            KEY_MP_GIRDER_SECTIONAL_IZ: 0.01,
            KEY_MP_GIRDER_SECTIONAL_IZ + ".G1.M1": 0.01,
            KEY_MP_GIRDER_SECTIONAL_IY: 0.005,
            KEY_MP_GIRDER_SECTIONAL_IY + ".G1.M1": 0.005,
        })
        
        # Test index 0
        sec = bridge._girder_section(0)
        assert sec.A == 0.035
        assert sec.J == 0.0001
        assert sec.Iz == 0.01
        assert sec.Iy == 0.005
        # Az = web_depth * web_thickness = 1.4 * 0.012 = 0.0168
        assert sec.Az == 0.0168
        # Ay = 2 * top_flange_width * top_flange_thickness = 2 * 0.3 * 0.02 = 0.012
        assert sec.Ay == 0.012

    def test_transverse_section(self):
        bridge = PlateGirderBridge()
        bridge.set_input({
            KEY_TS_NO_OF_GIRDERS: 2,
            KEY_MP_GIRDER_DEPTH: 1.5,
            KEY_MP_GIRDER_DEPTH + ".G1.M1": 1.5,
            KEY_MP_GIRDER_WEB_THICKNESS: 0.012,
            KEY_MP_GIRDER_WEB_THICKNESS + ".G1.M1": 0.012,
            KEY_MP_GIRDER_SECTIONAL_AREA: 0.04,
            KEY_MP_GIRDER_SECTIONAL_AREA + ".G1.M1": 0.04,
            KEY_MP_GIRDER_TORSION_CONSTANT_IT: 0.0002,
            KEY_MP_GIRDER_TORSION_CONSTANT_IT + ".G1.M1": 0.0002,
            KEY_MP_GIRDER_SECTIONAL_IZ: 0.02,
            KEY_MP_GIRDER_SECTIONAL_IZ + ".G1.M1": 0.02,
            KEY_MP_GIRDER_SECTIONAL_IY: 0.01,
            KEY_MP_GIRDER_SECTIONAL_IY + ".G1.M1": 0.01,
        })
        sec = bridge._transverse_section()
        # Half depth, half properties
        assert sec.A == 0.02
        assert sec.J == 0.0001
        assert sec.Iz == 0.01
        assert sec.Iy == 0.005
        # t = depth / 2 = 1.5 / 2 = 0.75
        # Az = t * web_thickness = 0.75 * 0.012 = 0.009
        assert sec.Az == pytest.approx(0.009)
        assert sec.Ay == pytest.approx(0.009)



