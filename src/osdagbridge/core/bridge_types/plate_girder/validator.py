"""
Osdag Bridge Input Validators
Validates Basic and Additional Inputs
"""

import math
from math import isclose

from osdagbridge.core.utils.codes.keyfile import *
from osdagbridge.core.utils.codes.irc5_2015 import IRC5_2015
from osdagbridge.core.utils.common import *
from osdagbridge.core.bridge_types.plate_girder.defaults import (
    AI_DEFAULTS,
    DEFAULT_AI_CRASH_BARRIER_POST_SPACING_M,
    DEFAULT_AI_MEDIAN_POST_SPACING_M,
    DEFAULT_NO_OF_GIRDERS,
    DEFAULT_AI_LAYOUT_DECK_OVERHANG_M,
    DEFAULT_AI_LAYOUT_MIN_GIRDER_SPACING_M,
    DEFAULT_AI_LAYOUT_MIN_DECK_THICKNESS_MM,
    DEFAULT_AI_LAYOUT_MAX_DECK_THICKNESS_MM,
)

# Pull numeric defaults directly from AI_DEFAULTS to avoid str-formatted aliases
_DEFAULT_DECK_THICKNESS_MM    = float(AI_DEFAULTS["layout"]["deck_thickness_mm"])
_DEFAULT_WEARING_DENSITY      = float(AI_DEFAULTS["wearing_course"]["density_kn_per_m3"])
_DEFAULT_WEARING_THICKNESS_MM = float(AI_DEFAULTS["wearing_course"]["thickness_mm"])
_DEFAULT_BEARING_LENGTH       = float(AI_DEFAULTS["support_conditions"]["bearing_length"])

class BridgeInputValidator:

    # ==========================================================
    # BASIC INPUT VALIDATION (DDCL 2.1.2)
    # ==========================================================

    def validate_basic_inputs(self, key: str, inputs: dict) -> tuple | None:
        """
        Validate a single basic-input field by key.
        Returns (corrected_value, message) on error, None if valid.
        """

        # ----------------------------------
		# Span (Software Scope Limit)
		# ----------------------------------

        if key == KEY_SPAN:
            span = self._to_float(inputs.get(KEY_SPAN))
            if span is None:
                return SPAN_MIN, "Span must be a numeric value."
            if span < SPAN_MIN:
                return SPAN_MIN, f"Span must be between {SPAN_MIN} m and {SPAN_MAX} m (software limitation)."
            if span > SPAN_MAX:
                return SPAN_MAX, f"Span must be between {SPAN_MIN} m and {SPAN_MAX} m (software limitation)."

		# ----------------------------------
		# Carriageway Width (IRC 5 Cl.104.3.1)
		# ----------------------------------
        elif key == KEY_CARRIAGEWAY_WIDTH:
            carriageway_width = self._to_float(inputs.get(KEY_CARRIAGEWAY_WIDTH))
            median = inputs.get(KEY_INCLUDE_MEDIAN)

            median_present = median is True or median == "Yes"
            if carriageway_width is None:
                min_w = CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN if median_present else CARRIAGEWAY_WIDTH_MIN
                return min_w, "Carriageway width must be specified."

            assumed_lanes = 2 if median_present else 1
            required_width = IRC5_2015.cl_104_3_1_carriageway_width(carriageway_width, assumed_lanes)

            if carriageway_width < required_width:
                return required_width, f"Minimum carriageway width required is {required_width:.2f} m as per IRC 5:2015 Clause 104.3.1."
            if carriageway_width > CARRIAGEWAY_WIDTH_MAX_LIMIT:
                return CARRIAGEWAY_WIDTH_MAX_LIMIT, f"Carriageway width exceeds {CARRIAGEWAY_WIDTH_MAX_LIMIT} m (software limitation)."

        # ----------------------------
        # Skew Angle (IRC 24 via keyfile)
        # ----------------------------
        elif key == KEY_SKEW_ANGLE:
            skew_angle = self._to_float(inputs.get(KEY_SKEW_ANGLE))
            if skew_angle is None:
                return SKEW_ANGLE_MIN, "Skew angle must be a numeric value."
            if skew_angle < SKEW_ANGLE_MIN:
                return SKEW_ANGLE_MIN, f"Skew angle must be between {SKEW_ANGLE_MIN}° and {SKEW_ANGLE_MAX}°."
            if skew_angle > SKEW_ANGLE_MAX:
                return SKEW_ANGLE_MAX, f"Skew angle must be between {SKEW_ANGLE_MIN}° and {SKEW_ANGLE_MAX}°."

        return None

    # ==========================================================
    # ADDITIONAL INPUT VALIDATION (DDCL 2.1.3)
    # ==========================================================

    # Dispatches by tab → key, mirroring validate_basic_inputs.
    # Returns (corrected_value, message) on error, None if valid.

    def validate_additional_inputs(self, tab: str, key: str, inputs: dict) -> tuple | None:
        """
        Validate a single additional-input field identified by (tab, key).
        Returns (corrected_value, message) on error, None if valid.
        """
        _dispatch = {
            "layout":              self._validate_layout_tab,
            "crash_barrier":       self._validate_crash_barrier_tab,
            "median":              self._validate_median_tab,
            "railing":             self._validate_railing_tab,
            "wearing_course":      self._validate_wearing_course_tab,
            "lane_details":        self._validate_lane_details_tab,
            "support_conditions":  self._validate_support_conditions_tab,
            "design_options":      self._validate_design_options_tab,
            "design_options_cont": self._validate_design_options_cont_tab,
            "girder_details":      self._validate_girder_details_tab,
        }
        validator = _dispatch.get(tab)
        if validator is None:
            return None
        return validator(key, inputs)

    # ----------------------------------------------------------
    # Tab: Layout
    # ----------------------------------------------------------

    def _validate_layout_tab(self, key: str, inputs: dict) -> tuple | None:

        # ----------------------------
        # Girder Spacing
        # ----------------------------
        if key == "girder_spacing":
            v = self._to_float(inputs.get("girder_spacing"))
            if v is None:
                return DEFAULT_GIRDER_SPACING, "Girder spacing must be a numeric value."
            if v < DEFAULT_AI_LAYOUT_MIN_GIRDER_SPACING_M:
                return DEFAULT_AI_LAYOUT_MIN_GIRDER_SPACING_M, (
                    f"Girder spacing must be at least {DEFAULT_AI_LAYOUT_MIN_GIRDER_SPACING_M} m "
                    "(IRC 24 — not less than 1/20 of span for main girders)."
                )
            if v > 50.0:
                return 50.0, "Girder spacing must not exceed 50.0 m."

        # ----------------------------
        # No. of Girders
        # ----------------------------
        elif key == "no_of_girders":
            v = self._to_int(inputs.get("no_of_girders"))
            if v is None:
                return DEFAULT_NO_OF_GIRDERS, "Number of girders must be an integer."
            if v < 2:
                return 2, "Minimum number of girders is 2."
            if v > 100:
                return 100, "Number of girders must not exceed 100."

        # ----------------------------
        # Deck Overhang (IRC 5 – layout geometry)
        # ----------------------------
        elif key == "deck_overhang":
            v = self._to_float(inputs.get("deck_overhang"))
            if v is None:
                return DEFAULT_AI_LAYOUT_DECK_OVERHANG_M, "Deck overhang must be a numeric value."
            if v < 0.0:
                return 0.0, "Deck overhang must not be negative."
            if v > 100.0:
                return 100.0, "Deck overhang must not exceed 100.0 m."

        # ----------------------------
        # Deck Thickness
        # ----------------------------
        elif key == "deck_thickness":
            v = self._to_float(inputs.get("deck_thickness"))
            if v is None:
                return _DEFAULT_DECK_THICKNESS_MM, "Deck thickness must be a numeric value."
            if v < DEFAULT_AI_LAYOUT_MIN_DECK_THICKNESS_MM:
                return DEFAULT_AI_LAYOUT_MIN_DECK_THICKNESS_MM, (
                    f"Deck thickness must be at least {DEFAULT_AI_LAYOUT_MIN_DECK_THICKNESS_MM:.0f} mm "
                    "(RDSO composite-girder standard)."
                )
            if v > DEFAULT_AI_LAYOUT_MAX_DECK_THICKNESS_MM:
                return DEFAULT_AI_LAYOUT_MAX_DECK_THICKNESS_MM, (
                    f"Deck thickness must not exceed {DEFAULT_AI_LAYOUT_MAX_DECK_THICKNESS_MM:.0f} mm "
                    "(RDSO composite-girder standard)."
                )

        # ----------------------------
        # Footpath Width (IRC 5 Cl.104.3.6)
        # ----------------------------
        elif key == "footpath_width":
            footpath = inputs.get(KEY_FOOTPATH, "None")  # default to "None" if key absent
            footpath_width = self._to_float(inputs.get("footpath_width"))

            result = IRC5_2015.cl_104_3_6_footpath_width(footpath, footpath_width)
            if result["applicable"] and not result["is_compliant"]:
                return MIN_FOOTPATH_WIDTH, result["remarks"]

        # ----------------------------
        # Footpath Thickness
        # ----------------------------
        elif key == "footpath_thickness":
            v = self._to_float(inputs.get("footpath_thickness"))
            if v is None:
                return _DEFAULT_DECK_THICKNESS_MM, "Footpath thickness must be a numeric value."
            if v < 100.0:
                return 100.0, "Footpath thickness must be at least 100 mm."
            if v > 500.0:
                return 500.0, "Footpath thickness must not exceed 500 mm."

        # ----------------------------
        # Layout Equation (cross-field check)
        # ----------------------------
        elif key == "_layout_equation":
            n  = self._to_int(inputs.get("no_of_girders"))
            s  = self._to_float(inputs.get("girder_spacing"))
            oh = self._to_float(inputs.get("deck_overhang"))
            w  = self._to_float(inputs.get("overall_bridge_width"))

            if all(v is not None for v in [n, s, oh, w]):
                lhs = (n - 1) * s + 2 * oh
                if not isclose(lhs, w, rel_tol=1e-2):
                    return None, (
                        "Layout must satisfy: "
                        "Overall Width = (No. of Girders − 1) × Spacing + 2 × Overhang."
                    )

        return None

    # ----------------------------------------------------------
    # Tab: Crash Barrier
    # ----------------------------------------------------------

    def _validate_crash_barrier_tab(self, key: str, inputs: dict) -> tuple | None:

        # ----------------------------
        # Crash Barrier Width (IRC 5 Cl.109.6 – standard barrier widths)
        # ----------------------------
        if key == "crash_barrier_width":
            v = self._to_float(inputs.get("crash_barrier_width"))
            if v is None:
                return DEFAULT_CRASH_BARRIER_WIDTH, "Crash barrier width must be a numeric value."
            if v < 0.0:
                return 0.0, "Crash barrier width must not be negative."
            if v > 2.0:
                return 2.0, "Crash barrier width must not exceed 2.0 m."

        # ----------------------------
        # Crash Barrier Height
        # ----------------------------
        elif key == "crash_barrier_height":
            v = self._to_float(inputs.get("crash_barrier_height"))
            if v is None:
                return None, "Crash barrier height must be a numeric value."
            if v < 0.0:
                return 0.0, "Crash barrier height must not be negative."
            if v > 3.0:
                return 3.0, "Crash barrier height must not exceed 3.0 m."

        # ----------------------------
        # Crash Barrier Density
        # ----------------------------
        elif key == "crash_barrier_density":
            v = self._to_float(inputs.get("crash_barrier_density"))
            if v is None:
                return None, "Material density must be a numeric value."
            if v < 0.0:
                return 0.0, "Material density must not be negative."
            if v > 100.0:
                return 100.0, "Material density must not exceed 100.0 kN/m³."

        # ----------------------------
        # Crash Barrier Area
        # ----------------------------
        elif key == "crash_barrier_area":
            v = self._to_float(inputs.get("crash_barrier_area"))
            if v is None:
                return None, "Crash barrier area must be a numeric value."
            if v < 0.0:
                return 0.0, "Crash barrier area must not be negative."
            if v > 10.0:
                return 10.0, "Crash barrier area must not exceed 10.0 m²."

        # ----------------------------
        # Crash Barrier Load
        # ----------------------------
        elif key == "crash_barrier_load":
            v = self._to_float(inputs.get("crash_barrier_load"))
            if v is None:
                return None, "Crash barrier load must be a numeric value."
            if v < 0.0:
                return 0.0, "Crash barrier load must not be negative."
            if v > 500.0:
                return 500.0, "Crash barrier load must not exceed 500.0 kN/m."

        # ----------------------------
        # Post Spacing
        # ----------------------------
        elif key == "crash_barrier_post_spacing":
            v = self._to_float(inputs.get("crash_barrier_post_spacing"))
            if v is None:
                return float(DEFAULT_AI_CRASH_BARRIER_POST_SPACING_M), "Post spacing must be a numeric value."
            if v <= 0.0:
                return float(DEFAULT_AI_CRASH_BARRIER_POST_SPACING_M), "Post spacing must be greater than 0."
            if v > 10.0:
                return 10.0, "Post spacing must not exceed 10.0 m."

        return None

    # ----------------------------------------------------------
    # Tab: Median
    # ----------------------------------------------------------

    def _validate_median_tab(self, key: str, inputs: dict) -> tuple | None:

        # ----------------------------
        # Median Width
        # ----------------------------
        if key == "median_width":
            v = self._to_float(inputs.get("median_width"))
            if v is None:
                return None, "Median width must be a numeric value."
            if v < 0.0:
                return 0.0, "Median width must not be negative."
            if v > 3.0:
                return 3.0, "Median width must not exceed 3.0 m."

        # ----------------------------
        # Median Height
        # ----------------------------
        elif key == "median_height":
            v = self._to_float(inputs.get("median_height"))
            if v is None:
                return None, "Median height must be a numeric value."
            if v < 0.0:
                return 0.0, "Median height must not be negative."
            if v > 3.0:
                return 3.0, "Median height must not exceed 3.0 m."

        # ----------------------------
        # Median Density
        # ----------------------------
        elif key == "median_density":
            v = self._to_float(inputs.get("median_density"))
            if v is None:
                return None, "Material density must be a numeric value."
            if v < 0.0:
                return 0.0, "Material density must not be negative."
            if v > 100.0:
                return 100.0, "Material density must not exceed 100.0 kN/m³."

        # ----------------------------
        # Median Area
        # ----------------------------
        elif key == "median_area":
            v = self._to_float(inputs.get("median_area"))
            if v is None:
                return None, "Median area must be a numeric value."
            if v < 0.0:
                return 0.0, "Median area must not be negative."
            if v > 10.0:
                return 10.0, "Median area must not exceed 10.0 m²."

        # ----------------------------
        # Median Load
        # ----------------------------
        elif key == "median_load":
            v = self._to_float(inputs.get("median_load"))
            if v is None:
                return None, "Median load must be a numeric value."
            if v < 0.0:
                return 0.0, "Median load must not be negative."
            if v > 500.0:
                return 500.0, "Median load must not exceed 500.0 kN/m."

        # ----------------------------
        # Post Spacing
        # ----------------------------
        elif key == "median_post_spacing":
            v = self._to_float(inputs.get("median_post_spacing"))
            if v is None:
                return float(DEFAULT_AI_MEDIAN_POST_SPACING_M), "Post spacing must be a numeric value."
            if v <= 0.0:
                return float(DEFAULT_AI_MEDIAN_POST_SPACING_M), "Post spacing must be greater than 0."
            if v > 10.0:
                return 10.0, "Post spacing must not exceed 10.0 m."

        return None

    # ----------------------------------------------------------
    # Tab: Railing
    # ----------------------------------------------------------

    def _validate_railing_tab(self, key: str, inputs: dict) -> tuple | None:

        # ----------------------------
        # Railing Width
        # ----------------------------
        if key == "railing_width":
            v = self._to_float(inputs.get("railing_width"))
            if v is None:
                return DEFAULT_RAILING_WIDTH * 1000, "Railing width must be a numeric value."
            if v < 0.0:
                return 0.0, "Railing width must not be negative."
            if v > 2000.0:
                return 2000.0, "Railing width must not exceed 2000 mm."

        # ----------------------------
        # Railing Height (IRC 5 Cl.109.7.2)
        # ----------------------------
        elif key == "railing_height":
            footpath = inputs.get(KEY_FOOTPATH)
            v = self._to_float(inputs.get("railing_height"))

            if v is None:
                return KEY_RAILING_MIN_HEIGHT[0], "Railing height must be a numeric value."

            corrected = IRC5_2015.cl_109_7_2_3_railing_height(footpath, v)
            if corrected != v:
                return corrected, (
                    f"Minimum railing height is {KEY_RAILING_MIN_HEIGHT[0]} mm "
                    "as per IRC 5:2015 Clause 109.7.2."
                )

        # ----------------------------
        # Railing Load (user-defined mode)
        # ----------------------------
        elif key == "railing_load_value":
            v = self._to_float(inputs.get("railing_load_value"))
            if v is None:
                return None, "Railing load must be a numeric value."
            if v < 0.0:
                return 0.0, "Railing load must not be negative."
            if v > 50.0:
                return 50.0, "Railing load must not exceed 50.0 kN/m."

        return None

    # ----------------------------------------------------------
    # Tab: Wearing Course
    # ----------------------------------------------------------

    def _validate_wearing_course_tab(self, key: str, inputs: dict) -> tuple | None:

        # ----------------------------
        # Wearing Course Density
        # ----------------------------
        if key == "wearing_density":
            v = self._to_float(inputs.get("wearing_density"))
            if v is None:
                return _DEFAULT_WEARING_DENSITY, "Wearing course density must be a numeric value."
            if v < 0.0:
                return 0.0, "Wearing course density must not be negative."
            if v > 40.0:
                return 40.0, "Wearing course density must not exceed 40.0 kN/m³."

        # ----------------------------
        # Wearing Course Thickness (IRC 5 Cl.109.5)
        # ----------------------------
        elif key == "wearing_thickness":
            v = self._to_float(inputs.get("wearing_thickness"))
            if v is None:
                return _DEFAULT_WEARING_THICKNESS_MM, "Wearing course thickness must be a numeric value."
            if v < 0.0:
                return 0.0, "Wearing course thickness must not be negative."
            if v > 200.0:
                return 200.0, "Wearing course thickness must not exceed 200 mm."

        return None

    # ----------------------------------------------------------
    # Tab: Lane Details
    # ----------------------------------------------------------

    def _validate_lane_details_tab(self, key: str, inputs: dict) -> tuple | None:

        # ----------------------------
        # Lane Count (IRC 6 Cl.204.1)
        # ----------------------------
        if key == "lane_count":
            v = self._to_int(inputs.get("lane_count"))
            if v is None:
                return 1, "Number of traffic lanes must be an integer."
            if v < 1:
                return 1, "Minimum number of traffic lanes is 1."
            if v > 6:
                return 6, "Number of traffic lanes must not exceed 6."

        return None

    # ----------------------------------------------------------
    # Tab: Support Conditions
    # ----------------------------------------------------------

    def _validate_support_conditions_tab(self, key: str, inputs: dict) -> tuple | None:

        # ----------------------------
        # Bearing Length
        # ----------------------------
        if key == "bearing_length":
            v = self._to_float(inputs.get("bearing_length"))
            if v is None:
                return _DEFAULT_BEARING_LENGTH, "Bearing length must be a numeric value."
            if v < 0.0:
                return 0.0, "Bearing length must not be negative."

        # ----------------------------
        # Support combination (cross-field check)
        # ----------------------------
        elif key == "_support_combination":
            left  = inputs.get("left_support")
            right = inputs.get("right_support")
            if left == "Roller" and right == "Roller":
                return None, (
                    "Both supports cannot be rollers – "
                    "the structure would be unstable."
                )

        return None

    # ----------------------------------------------------------
    # Tab: Design Options (shear studs & deck)
    # ----------------------------------------------------------

    def _validate_design_options_tab(self, key: str, inputs: dict) -> tuple | None:

        # ----------------------------
        # Shear Stud Height (IRC 22 / keyfile)
        # ----------------------------
        if key == "shear_stud_height":
            h = self._to_float(inputs.get("shear_stud_height"))
            d = self._to_float(inputs.get("shear_stud_diameter"))

            if h is None:
                return MIN_STUD_HEIGHT_MM, "Stud height must be a numeric value."
            if h < MIN_STUD_HEIGHT_MM:
                return MIN_STUD_HEIGHT_MM, (
                    f"Minimum stud height is {MIN_STUD_HEIGHT_MM} mm."
                )
            if d is not None and h < MIN_STUD_HEIGHT_FACTOR * d:
                corrected = MIN_STUD_HEIGHT_FACTOR * d
                return corrected, (
                    f"Stud height must be at least {MIN_STUD_HEIGHT_FACTOR}× "
                    f"stud diameter ({MIN_STUD_HEIGHT_FACTOR * d:.1f} mm)."
                )

        # ----------------------------
        # Shear Stud Diameter (IRC 22 / keyfile)
        # ----------------------------
        elif key == "shear_stud_diameter":
            d  = self._to_float(inputs.get("shear_stud_diameter"))
            tf = self._to_float(inputs.get("top_flange_thickness"))

            if d is None:
                return None, "Stud diameter must be a numeric value."
            if d <= 0.0:
                return None, "Stud diameter must be greater than 0."
            if tf is not None and d > MAX_STUD_DIAMETER_FACTOR * tf:
                return MAX_STUD_DIAMETER_FACTOR * tf, (
                    f"Stud diameter must not exceed "
                    f"{MAX_STUD_DIAMETER_FACTOR}× top flange thickness "
                    f"({MAX_STUD_DIAMETER_FACTOR * tf:.1f} mm)."
                )

        return None

    # ----------------------------------------------------------
    # Tab: Design Options (cont.) — Partial Safety Factors & K-Factors
    # ----------------------------------------------------------

    def _validate_design_options_cont_tab(self, key: str, inputs: dict) -> tuple | None:

        # --------------------------------------------------
        # Partial Safety Factors (IRC 22 / IS 800 Table 1)
        # All gamma values must be > 1.0 (< 1 would be non-conservative)
        # --------------------------------------------------

        # Concrete — basic & seismic (γC). IRC 112: 1.50 basic, 1.20 accidental
        if key == "gamma_c_basic":
            v = self._to_float(inputs.get("gamma_c_basic"))
            if v is None:
                return None, "Concrete partial safety factor (γC basic) must be a numeric value."
            if v < 1.0:
                return 1.0, "Concrete safety factor (γC basic) must be ≥ 1.0."
            if v > 3.0:
                return 3.0, "Concrete safety factor (γC basic) must not exceed 3.0."

        # Concrete — accidental
        elif key == "gamma_c_accidental":
            v = self._to_float(inputs.get("gamma_c_accidental"))
            if v is None:
                return None, "Concrete partial safety factor (γC accidental) must be a numeric value."
            if v < 1.0:
                return 1.0, "Concrete safety factor (γC accidental) must be ≥ 1.0."
            if v > 3.0:
                return 3.0, "Concrete safety factor (γC accidental) must not exceed 3.0."

        # Structural steel — yielding & buckling (γM0). Reference: GAMMA_M0_STEEL = 1.10
        elif key == "gamma_m0":
            v = self._to_float(inputs.get("gamma_m0"))
            if v is None:
                return GAMMA_M0_STEEL, "Structural steel safety factor (γM0) must be a numeric value."
            if v < 1.0:
                return GAMMA_M0_STEEL, f"γM0 must be ≥ 1.0 (reference value: {GAMMA_M0_STEEL})."
            if v > 3.0:
                return 3.0, "γM0 must not exceed 3.0."

        # Structural steel — ultimate stress (γM1). Reference: GAMMA_M1_STEEL_ULTIMATE = 1.25
        elif key == "gamma_m1":
            v = self._to_float(inputs.get("gamma_m1"))
            if v is None:
                return GAMMA_M1_STEEL_ULTIMATE, "Structural steel safety factor (γM1) must be a numeric value."
            if v < 1.0:
                return GAMMA_M1_STEEL_ULTIMATE, f"γM1 must be ≥ 1.0 (reference value: {GAMMA_M1_STEEL_ULTIMATE})."
            if v > 3.0:
                return 3.0, "γM1 must not exceed 3.0."

        # Reinforcing steel (γS). Reference: GAMMA_M_REINFORCEMENT = 1.15
        elif key == "gamma_s":
            v = self._to_float(inputs.get("gamma_s"))
            if v is None:
                return GAMMA_M_REINFORCEMENT, "Reinforcing steel safety factor (γS) must be a numeric value."
            if v < 1.0:
                return GAMMA_M_REINFORCEMENT, f"γS must be ≥ 1.0 (reference value: {GAMMA_M_REINFORCEMENT})."
            if v > 3.0:
                return 3.0, "γS must not exceed 3.0."

        # Shear connectors — yield (γV). Reference: GAMMA_M_SHEAR_CONCRETE = 1.25
        elif key == "gamma_v":
            v = self._to_float(inputs.get("gamma_v"))
            if v is None:
                return GAMMA_M_SHEAR_CONCRETE, "Shear connector safety factor (γV) must be a numeric value."
            if v < 1.0:
                return GAMMA_M_SHEAR_CONCRETE, f"γV must be ≥ 1.0 (reference value: {GAMMA_M_SHEAR_CONCRETE})."
            if v > 3.0:
                return 3.0, "γV must not exceed 3.0."

        # Fatigue load (γflt)
        elif key == "gamma_flt":
            v = self._to_float(inputs.get("gamma_flt"))
            if v is None:
                return None, "Fatigue load safety factor (γflt) must be a numeric value."
            if v < 1.0:
                return 1.0, "γflt must be ≥ 1.0."
            if v > 3.0:
                return 3.0, "γflt must not exceed 3.0."

        # Fatigue strength (γMf)
        elif key == "gamma_mf":
            v = self._to_float(inputs.get("gamma_mf"))
            if v is None:
                return None, "Fatigue strength safety factor (γMf) must be a numeric value."
            if v < 1.0:
                return 1.0, "γMf must be ≥ 1.0."
            if v > 3.0:
                return 3.0, "γMf must not exceed 3.0."

        # --------------------------------------------------
        # Number of Load Cycles (IRC 22 Cl.605.3, Cl.605.4)
        # --------------------------------------------------
        elif key == "load_cycles":
            v = self._to_int(inputs.get("load_cycles"))
            if v is None:
                return None, "Number of load cycles must be a numeric value."
            if v <= 0:
                return None, "Number of load cycles must be greater than 0."

        # --------------------------------------------------
        # K Factors (IRC 22 fatigue reduction factors, all > 0)
        # --------------------------------------------------
        elif key in ("k1", "k3", "k4", "k6", "k3_second", "k4_second"):
            v = self._to_float(inputs.get(key))
            if v is None:
                return None, f"{key.upper()} must be a numeric value."
            if v <= 0.0:
                return None, f"{key.upper()} must be greater than 0."

        # --------------------------------------------------
        # Limit L (m) — span length for fatigue check
        # --------------------------------------------------
        elif key == "limit_l":
            v = self._to_float(inputs.get("limit_l"))
            if v is None:
                return None, "Limit L must be a numeric value."
            if v <= 0.0:
                return None, "Limit L must be greater than 0."

        return None

    # ----------------------------------------------------------
    # Tab: Girder Details
    # ----------------------------------------------------------

    def _validate_girder_details_tab(self, key: str, inputs: dict) -> tuple | None:

        # ----------------------------
        # Total Depth (welded girder)
        # ----------------------------
        if key == "depth":
            v = self._to_float(inputs.get("depth"))
            if v is not None and v <= 0.0:
                return None, "Girder depth must be greater than 0."

        # ----------------------------
        # Top / Bottom Flange Width
        # ----------------------------
        elif key in ("top_flange_width", "bottom_flange_width"):
            v = self._to_float(inputs.get(key))
            if v is not None and v <= 0.0:
                label = "Top" if "top" in key else "Bottom"
                return None, f"{label} flange width must be greater than 0."

        # ----------------------------
        # Top / Bottom Flange Thickness
        # ----------------------------
        elif key in ("top_flange_thickness", "bottom_flange_thickness"):
            v = self._to_float(inputs.get(key))
            if v is not None and v <= 0.0:
                label = "Top" if "top" in key else "Bottom"
                return None, f"{label} flange thickness must be greater than 0."

        # ----------------------------
        # Web Thickness
        # ----------------------------
        elif key == "web_thickness":
            v = self._to_float(inputs.get("web_thickness"))
            if v is not None and v <= 0.0:
                return None, "Web thickness must be greater than 0."

        return None

    # ==========================================================
    # INTERNAL HELPERS
    # ==========================================================

    def _to_float(self, value):
        try:
            f = float(value)
            return f if math.isfinite(f) else None
        except (TypeError, ValueError):
            return None

    def _to_int(self, value):
        # Accept both int strings ("4") and float strings ("3.9" → 3)
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None
