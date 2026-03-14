"""
Comprehensive tests for BridgeInputValidator.
Run with: conda run -n Osdag-bridge python -m pytest tests/test_validator.py -v
"""

import math
import pytest

from osdagbridge.core.bridge_types.plate_girder.validator import BridgeInputValidator
from osdagbridge.core.bridge_types.plate_girder.defaults import AI_DEFAULTS, DEFAULT_NO_OF_GIRDERS
from osdagbridge.core.utils.common import (
    KEY_SPAN, KEY_CARRIAGEWAY_WIDTH, KEY_INCLUDE_MEDIAN, KEY_FOOTPATH, KEY_SKEW_ANGLE,
    SPAN_MIN, SPAN_MAX,
    SKEW_ANGLE_MIN, SKEW_ANGLE_MAX,
    CARRIAGEWAY_WIDTH_MIN, CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN, CARRIAGEWAY_WIDTH_MAX_LIMIT,
    DEFAULT_GIRDER_SPACING, DEFAULT_CRASH_BARRIER_WIDTH,
    DEFAULT_RAILING_WIDTH, MIN_FOOTPATH_WIDTH,
)
from osdagbridge.core.bridge_types.plate_girder.defaults import (
    DEFAULT_AI_LAYOUT_DECK_OVERHANG_M,
    DEFAULT_AI_LAYOUT_MIN_GIRDER_SPACING_M,
    DEFAULT_AI_LAYOUT_MIN_DECK_THICKNESS_MM,
    DEFAULT_AI_LAYOUT_MAX_DECK_THICKNESS_MM,
)
from osdagbridge.core.utils.codes.keyfile import (
    MIN_STUD_HEIGHT_MM, MIN_STUD_HEIGHT_FACTOR, MAX_STUD_DIAMETER_FACTOR,
    KEY_RAILING_MIN_HEIGHT,
    GAMMA_M0_STEEL, GAMMA_M1_STEEL_ULTIMATE, GAMMA_M_REINFORCEMENT, GAMMA_M_SHEAR_CONCRETE,
)

@pytest.fixture
def v():
    return BridgeInputValidator()


# ===========================================================
# HELPERS
# ===========================================================

def _ok(result):
    assert result is None, f"Expected None (valid), got: {result}"

def _err(result, expected_correction=None):
    assert result is not None, "Expected an error tuple, got None (valid)"
    assert isinstance(result, tuple) and len(result) == 2
    corr, msg = result
    assert isinstance(msg, str) and msg, "Message must be a non-empty string"
    if expected_correction is not None:
        assert corr == expected_correction, f"Expected correction {expected_correction!r}, got {corr!r}"
    return corr, msg


# ===========================================================
# BASIC INPUTS
# ===========================================================

class TestBasicSpan:

    def test_valid(self, v):
        _ok(v.validate_basic_inputs(KEY_SPAN, {KEY_SPAN: 33.5}))

    def test_at_min(self, v):
        _ok(v.validate_basic_inputs(KEY_SPAN, {KEY_SPAN: SPAN_MIN}))

    def test_at_max(self, v):
        _ok(v.validate_basic_inputs(KEY_SPAN, {KEY_SPAN: SPAN_MAX}))

    def test_below_min(self, v):
        _err(v.validate_basic_inputs(KEY_SPAN, {KEY_SPAN: 10}), SPAN_MIN)

    def test_above_max(self, v):
        _err(v.validate_basic_inputs(KEY_SPAN, {KEY_SPAN: 100}), SPAN_MAX)

    def test_missing(self, v):
        _err(v.validate_basic_inputs(KEY_SPAN, {}), SPAN_MIN)

    def test_none_value(self, v):
        _err(v.validate_basic_inputs(KEY_SPAN, {KEY_SPAN: None}), SPAN_MIN)

    def test_empty_string(self, v):
        _err(v.validate_basic_inputs(KEY_SPAN, {KEY_SPAN: ""}), SPAN_MIN)

    def test_string_number(self, v):
        _ok(v.validate_basic_inputs(KEY_SPAN, {KEY_SPAN: "33.5"}))

    def test_nan_now_caught(self, v):
        # Fixed: _to_float now returns None for NaN → treated as missing → error
        _err(v.validate_basic_inputs(KEY_SPAN, {KEY_SPAN: float("nan")}), SPAN_MIN)

    def test_pos_infinity_caught(self, v):
        # Fixed: _to_float returns None for inf → treated as missing
        _err(v.validate_basic_inputs(KEY_SPAN, {KEY_SPAN: float("inf")}), SPAN_MIN)

    def test_neg_infinity_caught(self, v):
        _err(v.validate_basic_inputs(KEY_SPAN, {KEY_SPAN: float("-inf")}), SPAN_MIN)

    def test_boolean_true_below_min(self, v):
        _err(v.validate_basic_inputs(KEY_SPAN, {KEY_SPAN: True}), SPAN_MIN)

    def test_unknown_key(self, v):
        _ok(v.validate_basic_inputs("geometry.unknown", {}))


class TestBasicCarriageway:

    def test_valid_no_median(self, v):
        _ok(v.validate_basic_inputs(KEY_CARRIAGEWAY_WIDTH,
            {KEY_CARRIAGEWAY_WIDTH: 5.0, KEY_INCLUDE_MEDIAN: False}))

    def test_valid_with_median_bool(self, v):
        _ok(v.validate_basic_inputs(KEY_CARRIAGEWAY_WIDTH,
            {KEY_CARRIAGEWAY_WIDTH: 8.0, KEY_INCLUDE_MEDIAN: True}))

    def test_valid_with_median_string_yes(self, v):
        _ok(v.validate_basic_inputs(KEY_CARRIAGEWAY_WIDTH,
            {KEY_CARRIAGEWAY_WIDTH: 8.0, KEY_INCLUDE_MEDIAN: "Yes"}))

    def test_median_string_no_is_not_truthy_bug_fixed(self, v):
        # Fixed: "No" is now correctly treated as no-median
        _ok(v.validate_basic_inputs(KEY_CARRIAGEWAY_WIDTH,
            {KEY_CARRIAGEWAY_WIDTH: 5.0, KEY_INCLUDE_MEDIAN: "No"}))

    def test_missing_width_no_median(self, v):
        _err(v.validate_basic_inputs(KEY_CARRIAGEWAY_WIDTH,
            {KEY_INCLUDE_MEDIAN: False}), CARRIAGEWAY_WIDTH_MIN)

    def test_missing_width_with_median(self, v):
        _err(v.validate_basic_inputs(KEY_CARRIAGEWAY_WIDTH,
            {KEY_INCLUDE_MEDIAN: True}), CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN)

    def test_below_min_no_median(self, v):
        _err(v.validate_basic_inputs(KEY_CARRIAGEWAY_WIDTH,
            {KEY_CARRIAGEWAY_WIDTH: 3.0, KEY_INCLUDE_MEDIAN: False}))

    def test_above_max(self, v):
        _err(v.validate_basic_inputs(KEY_CARRIAGEWAY_WIDTH,
            {KEY_CARRIAGEWAY_WIDTH: 999.0, KEY_INCLUDE_MEDIAN: False}),
            CARRIAGEWAY_WIDTH_MAX_LIMIT)


class TestBasicSkewAngle:

    def test_valid_zero(self, v):
        _ok(v.validate_basic_inputs(KEY_SKEW_ANGLE, {KEY_SKEW_ANGLE: 0.0}))

    def test_at_min(self, v):
        _ok(v.validate_basic_inputs(KEY_SKEW_ANGLE, {KEY_SKEW_ANGLE: SKEW_ANGLE_MIN}))

    def test_at_max(self, v):
        _ok(v.validate_basic_inputs(KEY_SKEW_ANGLE, {KEY_SKEW_ANGLE: SKEW_ANGLE_MAX}))

    def test_below_min(self, v):
        _err(v.validate_basic_inputs(KEY_SKEW_ANGLE, {KEY_SKEW_ANGLE: -30}), SKEW_ANGLE_MIN)

    def test_above_max(self, v):
        _err(v.validate_basic_inputs(KEY_SKEW_ANGLE, {KEY_SKEW_ANGLE: 30}), SKEW_ANGLE_MAX)

    def test_missing(self, v):
        _err(v.validate_basic_inputs(KEY_SKEW_ANGLE, {}), SKEW_ANGLE_MIN)


# ===========================================================
# DISPATCH
# ===========================================================

class TestDispatch:

    def test_unknown_tab(self, v):
        _ok(v.validate_additional_inputs("nonexistent_tab", "any_key", {}))

    def test_unknown_key_in_valid_tab(self, v):
        _ok(v.validate_additional_inputs("layout", "nonexistent_key", {}))

    def test_all_tabs_reachable_without_crash(self, v):
        for tab in ["layout", "crash_barrier", "median", "railing", "wearing_course",
                    "lane_details", "support_conditions", "design_options",
                    "design_options_cont", "girder_details"]:
            result = v.validate_additional_inputs(tab, "__probe__", {})
            assert result is None, f"Tab '{tab}' raised on unknown key"


# ===========================================================
# LAYOUT TAB
# ===========================================================

class TestLayoutGirderSpacing:

    def test_valid(self, v):
        _ok(v.validate_additional_inputs("layout", "girder_spacing", {"girder_spacing": 2.5}))

    def test_at_min_boundary(self, v):
        _ok(v.validate_additional_inputs("layout", "girder_spacing",
            {"girder_spacing": DEFAULT_AI_LAYOUT_MIN_GIRDER_SPACING_M}))

    def test_below_min(self, v):
        _err(v.validate_additional_inputs("layout", "girder_spacing", {"girder_spacing": 0.5}),
            DEFAULT_AI_LAYOUT_MIN_GIRDER_SPACING_M)

    def test_at_max_boundary(self, v):
        _ok(v.validate_additional_inputs("layout", "girder_spacing", {"girder_spacing": 50.0}))

    def test_above_max(self, v):
        _err(v.validate_additional_inputs("layout", "girder_spacing", {"girder_spacing": 51.0}), 50.0)

    def test_missing(self, v):
        _err(v.validate_additional_inputs("layout", "girder_spacing", {}), DEFAULT_GIRDER_SPACING)

    def test_string_number(self, v):
        _ok(v.validate_additional_inputs("layout", "girder_spacing", {"girder_spacing": "2.5"}))

    def test_zero(self, v):
        _err(v.validate_additional_inputs("layout", "girder_spacing", {"girder_spacing": 0.0}),
            DEFAULT_AI_LAYOUT_MIN_GIRDER_SPACING_M)

    def test_nan_caught(self, v):
        _err(v.validate_additional_inputs("layout", "girder_spacing",
            {"girder_spacing": float("nan")}), DEFAULT_GIRDER_SPACING)

    def test_inf_caught(self, v):
        _err(v.validate_additional_inputs("layout", "girder_spacing",
            {"girder_spacing": float("inf")}), DEFAULT_GIRDER_SPACING)

    def test_list_treated_as_missing(self, v):
        _err(v.validate_additional_inputs("layout", "girder_spacing",
            {"girder_spacing": [2.5]}), DEFAULT_GIRDER_SPACING)


class TestLayoutNoOfGirders:

    def test_valid(self, v):
        _ok(v.validate_additional_inputs("layout", "no_of_girders", {"no_of_girders": 4}))

    def test_at_min(self, v):
        _ok(v.validate_additional_inputs("layout", "no_of_girders", {"no_of_girders": 2}))

    def test_below_min(self, v):
        _err(v.validate_additional_inputs("layout", "no_of_girders", {"no_of_girders": 1}), 2)

    def test_at_max(self, v):
        _ok(v.validate_additional_inputs("layout", "no_of_girders", {"no_of_girders": 100}))

    def test_above_max(self, v):
        _err(v.validate_additional_inputs("layout", "no_of_girders", {"no_of_girders": 101}), 100)

    def test_missing(self, v):
        _err(v.validate_additional_inputs("layout", "no_of_girders", {}), DEFAULT_NO_OF_GIRDERS)

    def test_float_string_now_truncated(self, v):
        # Fixed: "3.9" → int(float("3.9")) = 3 → valid
        _ok(v.validate_additional_inputs("layout", "no_of_girders", {"no_of_girders": "3.9"}))

    def test_float_value_truncated(self, v):
        _ok(v.validate_additional_inputs("layout", "no_of_girders", {"no_of_girders": 3.9}))

    def test_negative(self, v):
        _err(v.validate_additional_inputs("layout", "no_of_girders", {"no_of_girders": -1}), 2)


class TestLayoutDeckOverhang:

    def test_valid(self, v):
        _ok(v.validate_additional_inputs("layout", "deck_overhang", {"deck_overhang": 1.0}))

    def test_zero_allowed(self, v):
        _ok(v.validate_additional_inputs("layout", "deck_overhang", {"deck_overhang": 0.0}))

    def test_negative(self, v):
        _err(v.validate_additional_inputs("layout", "deck_overhang", {"deck_overhang": -0.5}), 0.0)

    def test_above_max(self, v):
        _err(v.validate_additional_inputs("layout", "deck_overhang", {"deck_overhang": 101.0}), 100.0)

    def test_missing(self, v):
        _err(v.validate_additional_inputs("layout", "deck_overhang", {}), DEFAULT_AI_LAYOUT_DECK_OVERHANG_M)


class TestLayoutDeckThickness:

    def test_valid(self, v):
        _ok(v.validate_additional_inputs("layout", "deck_thickness", {"deck_thickness": 200}))

    def test_at_min(self, v):
        _ok(v.validate_additional_inputs("layout", "deck_thickness",
            {"deck_thickness": DEFAULT_AI_LAYOUT_MIN_DECK_THICKNESS_MM}))

    def test_below_min(self, v):
        _err(v.validate_additional_inputs("layout", "deck_thickness", {"deck_thickness": 100}),
            DEFAULT_AI_LAYOUT_MIN_DECK_THICKNESS_MM)

    def test_at_max(self, v):
        _ok(v.validate_additional_inputs("layout", "deck_thickness",
            {"deck_thickness": DEFAULT_AI_LAYOUT_MAX_DECK_THICKNESS_MM}))

    def test_above_max(self, v):
        _err(v.validate_additional_inputs("layout", "deck_thickness",
            {"deck_thickness": DEFAULT_AI_LAYOUT_MAX_DECK_THICKNESS_MM + 1}),
            DEFAULT_AI_LAYOUT_MAX_DECK_THICKNESS_MM)

    def test_missing_returns_default(self, v):
        corr, _ = _err(v.validate_additional_inputs("layout", "deck_thickness", {}))
        assert corr == float(AI_DEFAULTS["layout"]["deck_thickness_mm"])


class TestLayoutFootpathWidth:

    def test_valid_with_footpath(self, v):
        _ok(v.validate_additional_inputs("layout", "footpath_width",
            {KEY_FOOTPATH: "Single Side", "footpath_width": 1.5}))

    def test_below_min_with_footpath(self, v):
        _err(v.validate_additional_inputs("layout", "footpath_width",
            {KEY_FOOTPATH: "Single Side", "footpath_width": 1.0}), MIN_FOOTPATH_WIDTH)

    def test_no_footpath_clause_not_applicable(self, v):
        _ok(v.validate_additional_inputs("layout", "footpath_width",
            {KEY_FOOTPATH: "None", "footpath_width": 0.5}))

    def test_footpath_key_missing_defaults_to_none_string(self, v):
        # Fixed: missing KEY_FOOTPATH defaults to "None" → clause not applicable → valid
        _ok(v.validate_additional_inputs("layout", "footpath_width",
            {"footpath_width": 1.5}))


class TestLayoutEquation:

    def test_valid_equation(self, v):
        # (4-1)*2.5 + 2*1.0 = 9.5
        _ok(v.validate_additional_inputs("layout", "_layout_equation", {
            "no_of_girders": 4, "girder_spacing": 2.5,
            "deck_overhang": 1.0, "overall_bridge_width": 9.5
        }))

    def test_invalid_equation(self, v):
        _err(v.validate_additional_inputs("layout", "_layout_equation", {
            "no_of_girders": 4, "girder_spacing": 2.5,
            "deck_overhang": 1.0, "overall_bridge_width": 12.0
        }))

    def test_within_1pct_tolerance(self, v):
        _ok(v.validate_additional_inputs("layout", "_layout_equation", {
            "no_of_girders": 4, "girder_spacing": 2.5,
            "deck_overhang": 1.0, "overall_bridge_width": 9.59
        }))

    def test_missing_field_skips_check(self, v):
        _ok(v.validate_additional_inputs("layout", "_layout_equation", {
            "no_of_girders": 4, "girder_spacing": 2.5,
            "overall_bridge_width": 9.5
            # deck_overhang missing
        }))


# ===========================================================
# CRASH BARRIER TAB
# ===========================================================

class TestCrashBarrier:

    def test_valid_width(self, v):
        _ok(v.validate_additional_inputs("crash_barrier", "crash_barrier_width",
            {"crash_barrier_width": 0.5}))

    def test_width_missing(self, v):
        _err(v.validate_additional_inputs("crash_barrier", "crash_barrier_width", {}),
            DEFAULT_CRASH_BARRIER_WIDTH)

    def test_width_negative(self, v):
        _err(v.validate_additional_inputs("crash_barrier", "crash_barrier_width",
            {"crash_barrier_width": -0.1}), 0.0)

    def test_width_above_max(self, v):
        _err(v.validate_additional_inputs("crash_barrier", "crash_barrier_width",
            {"crash_barrier_width": 3.0}), 2.0)

    def test_height_valid(self, v):
        _ok(v.validate_additional_inputs("crash_barrier", "crash_barrier_height",
            {"crash_barrier_height": 1.1}))

    def test_height_missing_no_default(self, v):
        corr, _ = _err(v.validate_additional_inputs("crash_barrier", "crash_barrier_height", {}))
        assert corr is None

    def test_height_negative(self, v):
        _err(v.validate_additional_inputs("crash_barrier", "crash_barrier_height",
            {"crash_barrier_height": -0.1}), 0.0)

    def test_height_above_max(self, v):
        _err(v.validate_additional_inputs("crash_barrier", "crash_barrier_height",
            {"crash_barrier_height": 4.0}), 3.0)

    def test_density_valid(self, v):
        _ok(v.validate_additional_inputs("crash_barrier", "crash_barrier_density",
            {"crash_barrier_density": 25.0}))

    def test_density_above_max(self, v):
        _err(v.validate_additional_inputs("crash_barrier", "crash_barrier_density",
            {"crash_barrier_density": 101.0}), 100.0)

    def test_density_negative(self, v):
        _err(v.validate_additional_inputs("crash_barrier", "crash_barrier_density",
            {"crash_barrier_density": -1.0}), 0.0)

    def test_area_valid(self, v):
        _ok(v.validate_additional_inputs("crash_barrier", "crash_barrier_area",
            {"crash_barrier_area": 0.5}))

    def test_area_above_max(self, v):
        _err(v.validate_additional_inputs("crash_barrier", "crash_barrier_area",
            {"crash_barrier_area": 11.0}), 10.0)

    def test_load_valid(self, v):
        _ok(v.validate_additional_inputs("crash_barrier", "crash_barrier_load",
            {"crash_barrier_load": 10.0}))

    def test_load_above_max(self, v):
        _err(v.validate_additional_inputs("crash_barrier", "crash_barrier_load",
            {"crash_barrier_load": 600}), 500.0)

    def test_post_spacing_zero(self, v):
        _err(v.validate_additional_inputs("crash_barrier", "crash_barrier_post_spacing",
            {"crash_barrier_post_spacing": 0.0}))

    def test_post_spacing_negative(self, v):
        _err(v.validate_additional_inputs("crash_barrier", "crash_barrier_post_spacing",
            {"crash_barrier_post_spacing": -1.0}))

    def test_post_spacing_above_max(self, v):
        _err(v.validate_additional_inputs("crash_barrier", "crash_barrier_post_spacing",
            {"crash_barrier_post_spacing": 11.0}), 10.0)

    def test_post_spacing_valid(self, v):
        _ok(v.validate_additional_inputs("crash_barrier", "crash_barrier_post_spacing",
            {"crash_barrier_post_spacing": 1.5}))


# ===========================================================
# MEDIAN TAB
# ===========================================================

class TestMedian:

    def test_valid_width(self, v):
        _ok(v.validate_additional_inputs("median", "median_width", {"median_width": 1.2}))

    def test_above_max_width(self, v):
        _err(v.validate_additional_inputs("median", "median_width", {"median_width": 4.0}), 3.0)

    def test_negative_width(self, v):
        _err(v.validate_additional_inputs("median", "median_width", {"median_width": -1.0}), 0.0)

    def test_missing_width_no_default(self, v):
        corr, _ = _err(v.validate_additional_inputs("median", "median_width", {}))
        assert corr is None

    def test_height_valid(self, v):
        _ok(v.validate_additional_inputs("median", "median_height", {"median_height": 1.0}))

    def test_height_above_max(self, v):
        _err(v.validate_additional_inputs("median", "median_height", {"median_height": 4.0}), 3.0)

    def test_density_valid(self, v):
        _ok(v.validate_additional_inputs("median", "median_density", {"median_density": 25.0}))

    def test_area_above_max(self, v):
        _err(v.validate_additional_inputs("median", "median_area", {"median_area": 11.0}), 10.0)

    def test_load_valid(self, v):
        _ok(v.validate_additional_inputs("median", "median_load", {"median_load": 50.0}))

    def test_load_above_max(self, v):
        _err(v.validate_additional_inputs("median", "median_load", {"median_load": 600}), 500.0)

    def test_post_spacing_zero(self, v):
        _err(v.validate_additional_inputs("median", "median_post_spacing",
            {"median_post_spacing": 0.0}))

    def test_post_spacing_negative(self, v):
        _err(v.validate_additional_inputs("median", "median_post_spacing",
            {"median_post_spacing": -1.0}))

    def test_post_spacing_valid(self, v):
        _ok(v.validate_additional_inputs("median", "median_post_spacing",
            {"median_post_spacing": 1.5}))


# ===========================================================
# RAILING TAB
# ===========================================================

class TestRailing:

    def test_valid_width(self, v):
        _ok(v.validate_additional_inputs("railing", "railing_width", {"railing_width": 150.0}))

    def test_width_missing(self, v):
        _err(v.validate_additional_inputs("railing", "railing_width", {}),
            DEFAULT_RAILING_WIDTH * 1000)

    def test_width_above_max(self, v):
        _err(v.validate_additional_inputs("railing", "railing_width",
            {"railing_width": 2001.0}), 2000.0)

    def test_width_negative(self, v):
        _err(v.validate_additional_inputs("railing", "railing_width",
            {"railing_width": -50.0}), 0.0)

    def test_height_valid(self, v):
        _ok(v.validate_additional_inputs("railing", "railing_height",
            {KEY_FOOTPATH: "None", "railing_height": 1200.0}))

    def test_height_below_min(self, v):
        corr, msg = _err(v.validate_additional_inputs("railing", "railing_height",
            {KEY_FOOTPATH: "None", "railing_height": 500.0}))
        assert corr == KEY_RAILING_MIN_HEIGHT[0]
        assert "1100" in msg

    def test_height_missing_now_returns_mm_value(self, v):
        # Fixed: fallback is KEY_RAILING_MIN_HEIGHT[0]=1100 (mm), not MIN_RAILING_HEIGHT=1.0 (m)
        corr, _ = _err(v.validate_additional_inputs("railing", "railing_height",
            {KEY_FOOTPATH: "None"}))
        assert corr == KEY_RAILING_MIN_HEIGHT[0], \
            f"Expected {KEY_RAILING_MIN_HEIGHT[0]} mm, got {corr}"

    def test_load_valid(self, v):
        _ok(v.validate_additional_inputs("railing", "railing_load_value",
            {"railing_load_value": 5.0}))

    def test_load_above_max(self, v):
        _err(v.validate_additional_inputs("railing", "railing_load_value",
            {"railing_load_value": 60.0}), 50.0)

    def test_load_negative(self, v):
        _err(v.validate_additional_inputs("railing", "railing_load_value",
            {"railing_load_value": -1.0}), 0.0)

    def test_load_missing_no_default(self, v):
        corr, _ = _err(v.validate_additional_inputs("railing", "railing_load_value", {}))
        assert corr is None


# ===========================================================
# WEARING COURSE TAB
# ===========================================================

class TestWearingCourse:

    def test_valid_density(self, v):
        _ok(v.validate_additional_inputs("wearing_course", "wearing_density",
            {"wearing_density": 24.0}))

    def test_density_above_max(self, v):
        _err(v.validate_additional_inputs("wearing_course", "wearing_density",
            {"wearing_density": 41.0}), 40.0)

    def test_density_negative(self, v):
        _err(v.validate_additional_inputs("wearing_course", "wearing_density",
            {"wearing_density": -1.0}), 0.0)

    def test_density_missing_returns_default(self, v):
        corr, _ = _err(v.validate_additional_inputs("wearing_course", "wearing_density", {}))
        assert corr == float(AI_DEFAULTS["wearing_course"]["density_kn_per_m3"])

    def test_thickness_valid(self, v):
        _ok(v.validate_additional_inputs("wearing_course", "wearing_thickness",
            {"wearing_thickness": 50.0}))

    def test_thickness_zero_valid(self, v):
        _ok(v.validate_additional_inputs("wearing_course", "wearing_thickness",
            {"wearing_thickness": 0.0}))

    def test_thickness_above_max(self, v):
        _err(v.validate_additional_inputs("wearing_course", "wearing_thickness",
            {"wearing_thickness": 201.0}), 200.0)

    def test_thickness_negative(self, v):
        _err(v.validate_additional_inputs("wearing_course", "wearing_thickness",
            {"wearing_thickness": -1.0}), 0.0)

    def test_thickness_missing_returns_default(self, v):
        corr, _ = _err(v.validate_additional_inputs("wearing_course", "wearing_thickness", {}))
        assert corr == float(AI_DEFAULTS["wearing_course"]["thickness_mm"])


# ===========================================================
# LANE DETAILS TAB
# ===========================================================

class TestLaneDetails:

    def test_valid(self, v):
        _ok(v.validate_additional_inputs("lane_details", "lane_count", {"lane_count": 2}))

    def test_at_min(self, v):
        _ok(v.validate_additional_inputs("lane_details", "lane_count", {"lane_count": 1}))

    def test_at_max(self, v):
        _ok(v.validate_additional_inputs("lane_details", "lane_count", {"lane_count": 6}))

    def test_below_min(self, v):
        _err(v.validate_additional_inputs("lane_details", "lane_count", {"lane_count": 0}), 1)

    def test_above_max(self, v):
        _err(v.validate_additional_inputs("lane_details", "lane_count", {"lane_count": 7}), 6)

    def test_missing(self, v):
        _err(v.validate_additional_inputs("lane_details", "lane_count", {}), 1)

    def test_string_int(self, v):
        _ok(v.validate_additional_inputs("lane_details", "lane_count", {"lane_count": "3"}))

    def test_float_string_truncated(self, v):
        # "2.9" → int(float("2.9")) = 2 → valid
        _ok(v.validate_additional_inputs("lane_details", "lane_count", {"lane_count": "2.9"}))


# ===========================================================
# SUPPORT CONDITIONS TAB
# ===========================================================

class TestSupportConditions:

    def test_valid_bearing(self, v):
        _ok(v.validate_additional_inputs("support_conditions", "bearing_length",
            {"bearing_length": 0.3}))

    def test_bearing_zero_valid(self, v):
        _ok(v.validate_additional_inputs("support_conditions", "bearing_length",
            {"bearing_length": 0.0}))

    def test_bearing_negative(self, v):
        _err(v.validate_additional_inputs("support_conditions", "bearing_length",
            {"bearing_length": -1.0}), 0.0)

    def test_bearing_missing(self, v):
        corr, _ = _err(v.validate_additional_inputs("support_conditions", "bearing_length", {}))
        assert corr == float(AI_DEFAULTS["support_conditions"]["bearing_length"])

    def test_double_roller_invalid(self, v):
        _err(v.validate_additional_inputs("support_conditions", "_support_combination",
            {"left_support": "Roller", "right_support": "Roller"}))

    def test_fixed_pinned_valid(self, v):
        _ok(v.validate_additional_inputs("support_conditions", "_support_combination",
            {"left_support": "Fixed", "right_support": "Pinned"}))

    def test_roller_fixed_valid(self, v):
        _ok(v.validate_additional_inputs("support_conditions", "_support_combination",
            {"left_support": "Roller", "right_support": "Fixed"}))

    def test_missing_supports_valid(self, v):
        # None+None ≠ Roller+Roller → valid
        _ok(v.validate_additional_inputs("support_conditions", "_support_combination", {}))


# ===========================================================
# DESIGN OPTIONS TAB
# ===========================================================

class TestDesignOptions:

    def test_stud_height_valid(self, v):
        _ok(v.validate_additional_inputs("design_options", "shear_stud_height",
            {"shear_stud_height": 150.0, "shear_stud_diameter": 20.0}))

    def test_stud_height_below_absolute_min(self, v):
        _err(v.validate_additional_inputs("design_options", "shear_stud_height",
            {"shear_stud_height": 80.0, "shear_stud_diameter": 20.0}), MIN_STUD_HEIGHT_MM)

    def test_stud_height_passes_absolute_fails_4d(self, v):
        # h=100 (≥ MIN=100), d=30 → 4*30=120 → error
        corr, msg = _err(v.validate_additional_inputs("design_options", "shear_stud_height",
            {"shear_stud_height": 100.0, "shear_stud_diameter": 30.0}))
        assert corr == MIN_STUD_HEIGHT_FACTOR * 30.0
        assert "4" in msg

    def test_stud_height_missing(self, v):
        _err(v.validate_additional_inputs("design_options", "shear_stud_height", {}),
            MIN_STUD_HEIGHT_MM)

    def test_stud_height_no_diameter_skips_4d(self, v):
        _ok(v.validate_additional_inputs("design_options", "shear_stud_height",
            {"shear_stud_height": 100.0}))

    def test_stud_diameter_valid(self, v):
        _ok(v.validate_additional_inputs("design_options", "shear_stud_diameter",
            {"shear_stud_diameter": 20.0, "top_flange_thickness": 20.0}))

    def test_stud_diameter_exceeds_2tf(self, v):
        corr, _ = _err(v.validate_additional_inputs("design_options", "shear_stud_diameter",
            {"shear_stud_diameter": 50.0, "top_flange_thickness": 20.0}))
        assert corr == MAX_STUD_DIAMETER_FACTOR * 20.0

    def test_stud_diameter_zero(self, v):
        _err(v.validate_additional_inputs("design_options", "shear_stud_diameter",
            {"shear_stud_diameter": 0.0}))

    def test_stud_diameter_negative(self, v):
        _err(v.validate_additional_inputs("design_options", "shear_stud_diameter",
            {"shear_stud_diameter": -5.0}))

    def test_stud_diameter_missing(self, v):
        _err(v.validate_additional_inputs("design_options", "shear_stud_diameter", {}))

    def test_stud_diameter_no_flange_skips_2tf(self, v):
        _ok(v.validate_additional_inputs("design_options", "shear_stud_diameter",
            {"shear_stud_diameter": 25.0}))


# ===========================================================
# DESIGN OPTIONS CONT TAB (NEW)
# ===========================================================

class TestDesignOptionsContGammaFactors:

    def test_gamma_m0_valid(self, v):
        _ok(v.validate_additional_inputs("design_options_cont", "gamma_m0",
            {"gamma_m0": GAMMA_M0_STEEL}))

    def test_gamma_m0_below_1(self, v):
        _err(v.validate_additional_inputs("design_options_cont", "gamma_m0",
            {"gamma_m0": 0.8}), GAMMA_M0_STEEL)

    def test_gamma_m0_above_3(self, v):
        _err(v.validate_additional_inputs("design_options_cont", "gamma_m0",
            {"gamma_m0": 3.5}), 3.0)

    def test_gamma_m0_missing(self, v):
        corr, _ = _err(v.validate_additional_inputs("design_options_cont", "gamma_m0", {}))
        assert corr == GAMMA_M0_STEEL

    def test_gamma_m1_valid(self, v):
        _ok(v.validate_additional_inputs("design_options_cont", "gamma_m1",
            {"gamma_m1": GAMMA_M1_STEEL_ULTIMATE}))

    def test_gamma_m1_below_1(self, v):
        _err(v.validate_additional_inputs("design_options_cont", "gamma_m1",
            {"gamma_m1": 0.5}), GAMMA_M1_STEEL_ULTIMATE)

    def test_gamma_s_valid(self, v):
        _ok(v.validate_additional_inputs("design_options_cont", "gamma_s",
            {"gamma_s": GAMMA_M_REINFORCEMENT}))

    def test_gamma_s_below_1(self, v):
        _err(v.validate_additional_inputs("design_options_cont", "gamma_s",
            {"gamma_s": 0.9}), GAMMA_M_REINFORCEMENT)

    def test_gamma_v_valid(self, v):
        _ok(v.validate_additional_inputs("design_options_cont", "gamma_v",
            {"gamma_v": GAMMA_M_SHEAR_CONCRETE}))

    def test_gamma_c_basic_valid(self, v):
        _ok(v.validate_additional_inputs("design_options_cont", "gamma_c_basic",
            {"gamma_c_basic": 1.5}))

    def test_gamma_c_basic_below_1(self, v):
        _err(v.validate_additional_inputs("design_options_cont", "gamma_c_basic",
            {"gamma_c_basic": 0.5}), 1.0)

    def test_gamma_c_accidental_valid(self, v):
        _ok(v.validate_additional_inputs("design_options_cont", "gamma_c_accidental",
            {"gamma_c_accidental": 1.2}))

    def test_gamma_flt_valid(self, v):
        _ok(v.validate_additional_inputs("design_options_cont", "gamma_flt",
            {"gamma_flt": 1.0}))

    def test_gamma_flt_below_1(self, v):
        _err(v.validate_additional_inputs("design_options_cont", "gamma_flt",
            {"gamma_flt": 0.5}), 1.0)

    def test_gamma_mf_valid(self, v):
        _ok(v.validate_additional_inputs("design_options_cont", "gamma_mf",
            {"gamma_mf": 1.15}))

    def test_gamma_mf_above_3(self, v):
        _err(v.validate_additional_inputs("design_options_cont", "gamma_mf",
            {"gamma_mf": 4.0}), 3.0)


class TestDesignOptionsContLoadCycles:

    def test_valid(self, v):
        _ok(v.validate_additional_inputs("design_options_cont", "load_cycles",
            {"load_cycles": 2000000}))

    def test_zero_invalid(self, v):
        _err(v.validate_additional_inputs("design_options_cont", "load_cycles",
            {"load_cycles": 0}))

    def test_negative_invalid(self, v):
        _err(v.validate_additional_inputs("design_options_cont", "load_cycles",
            {"load_cycles": -1}))

    def test_missing(self, v):
        _err(v.validate_additional_inputs("design_options_cont", "load_cycles", {}))

    def test_string_float_accepted(self, v):
        # "500000.0" → int(float()) = 500000 → valid
        _ok(v.validate_additional_inputs("design_options_cont", "load_cycles",
            {"load_cycles": "500000.0"}))


class TestDesignOptionsContKFactors:

    @pytest.mark.parametrize("key", ["k1", "k3", "k4", "k6", "k3_second", "k4_second"])
    def test_valid(self, v, key):
        _ok(v.validate_additional_inputs("design_options_cont", key, {key: 1.0}))

    @pytest.mark.parametrize("key", ["k1", "k3", "k4", "k6"])
    def test_zero_invalid(self, v, key):
        _err(v.validate_additional_inputs("design_options_cont", key, {key: 0.0}))

    @pytest.mark.parametrize("key", ["k1", "k3", "k4", "k6"])
    def test_negative_invalid(self, v, key):
        _err(v.validate_additional_inputs("design_options_cont", key, {key: -0.5}))

    @pytest.mark.parametrize("key", ["k1", "k3", "k4", "k6"])
    def test_missing(self, v, key):
        _err(v.validate_additional_inputs("design_options_cont", key, {}))

    def test_limit_l_valid(self, v):
        _ok(v.validate_additional_inputs("design_options_cont", "limit_l",
            {"limit_l": 25.0}))

    def test_limit_l_zero_invalid(self, v):
        _err(v.validate_additional_inputs("design_options_cont", "limit_l",
            {"limit_l": 0.0}))

    def test_limit_l_missing(self, v):
        _err(v.validate_additional_inputs("design_options_cont", "limit_l", {}))


# ===========================================================
# GIRDER DETAILS TAB
# ===========================================================

class TestGirderDetails:

    def test_valid_depth(self, v):
        _ok(v.validate_additional_inputs("girder_details", "depth", {"depth": 1200.0}))

    def test_depth_zero(self, v):
        _err(v.validate_additional_inputs("girder_details", "depth", {"depth": 0.0}))

    def test_depth_negative(self, v):
        _err(v.validate_additional_inputs("girder_details", "depth", {"depth": -100.0}))

    def test_depth_missing_skips(self, v):
        _ok(v.validate_additional_inputs("girder_details", "depth", {}))

    def test_top_flange_width_valid(self, v):
        _ok(v.validate_additional_inputs("girder_details", "top_flange_width",
            {"top_flange_width": 300.0}))

    def test_top_flange_width_zero(self, v):
        _err(v.validate_additional_inputs("girder_details", "top_flange_width",
            {"top_flange_width": 0.0}))

    def test_bottom_flange_width_negative(self, v):
        _err(v.validate_additional_inputs("girder_details", "bottom_flange_width",
            {"bottom_flange_width": -10.0}))

    def test_top_flange_thickness_valid(self, v):
        _ok(v.validate_additional_inputs("girder_details", "top_flange_thickness",
            {"top_flange_thickness": 20.0}))

    def test_bottom_flange_thickness_zero(self, v):
        _err(v.validate_additional_inputs("girder_details", "bottom_flange_thickness",
            {"bottom_flange_thickness": 0.0}))

    def test_web_thickness_valid(self, v):
        _ok(v.validate_additional_inputs("girder_details", "web_thickness",
            {"web_thickness": 12.0}))

    def test_web_thickness_zero(self, v):
        _err(v.validate_additional_inputs("girder_details", "web_thickness",
            {"web_thickness": 0.0}))

    def test_web_thickness_missing_skips(self, v):
        _ok(v.validate_additional_inputs("girder_details", "web_thickness", {}))


# ===========================================================
# TYPE COERCION EDGE CASES
# ===========================================================

class TestTypeCoercion:

    def test_nan_now_caught_everywhere(self, v):
        nan = float("nan")
        for tab, key, inp in [
            ("layout", "girder_spacing", {"girder_spacing": nan}),
            ("layout", "deck_thickness", {"deck_thickness": nan}),
            ("crash_barrier", "crash_barrier_load", {"crash_barrier_load": nan}),
            ("wearing_course", "wearing_density", {"wearing_density": nan}),
        ]:
            result = v.validate_additional_inputs(tab, key, inp)
            assert result is not None, f"NaN passed silently for {tab}/{key}"

    def test_inf_caught(self, v):
        _err(v.validate_additional_inputs("layout", "girder_spacing",
            {"girder_spacing": float("inf")}), DEFAULT_GIRDER_SPACING)

    def test_neg_inf_caught(self, v):
        _err(v.validate_additional_inputs("layout", "girder_spacing",
            {"girder_spacing": float("-inf")}), DEFAULT_GIRDER_SPACING)

    def test_boolean_false_as_zero(self, v):
        _err(v.validate_additional_inputs("layout", "girder_spacing",
            {"girder_spacing": False}), DEFAULT_AI_LAYOUT_MIN_GIRDER_SPACING_M)

    def test_boolean_true_passes(self, v):
        _ok(v.validate_additional_inputs("layout", "girder_spacing",
            {"girder_spacing": True}))

    def test_list_treated_as_missing(self, v):
        _err(v.validate_additional_inputs("layout", "girder_spacing",
            {"girder_spacing": [2.5]}), DEFAULT_GIRDER_SPACING)

    def test_dict_treated_as_missing(self, v):
        _err(v.validate_additional_inputs("layout", "deck_thickness",
            {"deck_thickness": {"value": 200}}))
