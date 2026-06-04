"""
Osdag Bridge Input Validators
Validates Basic and Additional Inputs
"""

from math import isclose, floor, ceil

from osdagbridge.core.utils.codes.keyfile import *
from osdagbridge.core.utils.codes.irc5_2015 import IRC5_2015
from osdagbridge.core.utils.common import *

class BridgeInputValidator:

    # ==========================================================
    # BASIC INPUT VALIDATION (DDCL 2.1.2)
    # ==========================================================

    def validate_basic_inputs(self, key: str, inputs: dict) -> dict:
        """
        Validate a single field by key against inputs dict.
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
            
            if carriageway_width is None:
                min_w = CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN if median else CARRIAGEWAY_WIDTH_MIN
                return min_w, "Carriageway width must be specified."
            
            assumed_lanes = 2 if median == 'Yes' else 1

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

    def validate_additional_inputs(self, key: str, inputs: dict):
        """
        Per-field validation for additional inputs.
        Returns (corrected_value, message) or None if valid.
        """
        # ═══TYPICAL-SECTION-TAB-VALIDATORS-STARTS═════════════════════════════════════════════════════════

        # ── Layout Fields ──────────────────────────────────────────────────────
        if key == KEY_TS_GIRDER_SPACING:
            v = self._to_float(inputs.get(key))
            overall = self._to_float(inputs.get(KEY_TS_OVERALL_WIDTH))
            max_gs = (overall / 2) if overall else None
            if v is None: return 0.5, "Girder spacing must be a numeric value."
            if v < 0.5:   return 0.5, "Girder spacing is outside the practical range allowed in the software."
            if max_gs is not None and v > max_gs:
                return max_gs, "Girder spacing is outside the practical range allowed in the software."

        elif key == KEY_TS_NO_OF_GIRDERS:
            v = self._to_int(inputs.get(key))
            overall = self._to_float(inputs.get(KEY_TS_OVERALL_WIDTH))
            max_ng = ceil(2 * overall) if overall else None
            if v is None: return 2, "No. of girders must be an integer value."
            if v < 2:     return 2, "No. of girders is outside the practical range allowed in the software."
            if max_ng is not None and v > max_ng:
                return max_ng, "No. of girders is outside the practical range allowed in the software."

        elif key == KEY_TS_DECK_OVERHANG:
            v = self._to_float(inputs.get(key))
            overall = self._to_float(inputs.get(KEY_TS_OVERALL_WIDTH))
            max_ov = (overall / 2) if overall else None
            if v is None: return 0.0, "Deck overhang width must be a numeric value."
            if v < 0.0:   return 0.0, "Deck overhang width is outside the practical range allowed in the software."
            if max_ov is not None and v > max_ov:
                return max_ov, "Deck overhang width is outside the practical range allowed in the software."

        # ── Deck Details ───────────────────────────────────────────────────────
        elif key == KEY_TS_DECK_THICKNESS:
            v = self._to_float(inputs.get(key))
            if v is None: return 200, "Deck thickness must be a numeric value."
            if v < 100:   return 100, "Deck thickness must be at least 100 mm."
            if v > 500:   return 500, "Deck thickness must not exceed 500 mm."

        elif key == KEY_TS_FOOTPATH_WIDTH:
            v = self._to_float(inputs.get(key))
            footpath = inputs.get(KEY_FOOTPATH)
            result = IRC5_2015.cl_104_3_6_footpath_width(footpath, v)
            if result["applicable"] and not result["is_compliant"]:
                return MIN_FOOTPATH_WIDTH, result["remarks"]

        elif key == KEY_TS_FOOTPATH_THICKNESS:
            v = self._to_float(inputs.get(key))
            if v is None: return 200, "Footpath thickness must be a numeric value."
            if v < 100:   return 100, "Footpath thickness must be at least 100 mm."
            if v > 500:   return 500, "Footpath thickness must not exceed 500 mm."

        # ── Crash Barrier ──────────────────────────────────────────────────────
        elif key == KEY_CB_WIDTH:
            v = self._to_float(inputs.get(key))
            overall = self._to_float(inputs.get(KEY_TS_OVERALL_WIDTH))
            max_cbw = (overall / 2) if overall else None
            if v is None: return 0.0, "Crash barrier width must be a numeric value."
            if v < 0.0:   return 0.0, "Crash barrier width is outside the practical range allowed in the software."
            if max_cbw is not None and v > max_cbw:
                return max_cbw, "Crash barrier width is outside the practical range allowed in the software."

        elif key == KEY_CB_HEIGHT:
            v = self._to_float(inputs.get(key))
            if v is None: return 0.0, "Crash barrier height must be a numeric value."
            if v < 0.0:   return 0.0, "Crash barrier height is outside the practical range allowed in the software."
            if v > 10.0:  return 10.0, "Crash barrier height is outside the practical range allowed in the software."

        elif key == KEY_CB_LOAD:
            v = self._to_float(inputs.get(key))
            if v is None: return 0.0, "Crash barrier load must be a numeric value."
            if v < 0.0:   return 0.0, "Crash barrier load is outside the practical range allowed in the software."
            if v > 100.0: return 100.0, "Crash barrier load is outside the practical range allowed in the software."

        elif key == KEY_CB_POST_SPACING:
            v = self._to_float(inputs.get(key))
            span = self._to_float(inputs.get(KEY_SPAN))
            if v is None: return 0.1, "Crash barrier post spacing must be a numeric value."
            if v < 0.1:   return 0.1, "Crash barrier post spacing is outside the practical range allowed in the software."
            if span is not None and v > span:
                return span, "Crash barrier post spacing is outside the practical range allowed in the software."

        # ── Median ─────────────────────────────────────────────────────────────
        elif key == KEY_MD_WIDTH:
            v = self._to_float(inputs.get(key))
            overall = self._to_float(inputs.get(KEY_TS_OVERALL_WIDTH))
            max_mdw = (overall / 2) if overall else None
            if v is None: return 0.0, "Median width must be a numeric value."
            if v < 0.0:   return 0.0, "Median width is outside the practical range allowed in the software."
            if max_mdw is not None and v > max_mdw:
                return max_mdw, "Median width is outside the practical range allowed in the software."

        elif key == KEY_MD_HEIGHT:
            v = self._to_float(inputs.get(key))
            if v is None: return 0.0, "Median height must be a numeric value."
            if v < 0.0:   return 0.0, "Median height is outside the practical range allowed in the software."
            if v > 10.0:  return 10.0, "Median height is outside the practical range allowed in the software."

        elif key == KEY_MD_LOAD:
            v = self._to_float(inputs.get(key))
            if v is None: return 0.0, "Median load must be a numeric value."
            if v < 0.0:   return 0.0, "Median load is outside the practical range allowed in the software."
            if v > 100.0: return 100.0, "Median load is outside the practical range allowed in the software."

        elif key == KEY_MD_POST_SPACING:
            v = self._to_float(inputs.get(key))
            span = self._to_float(inputs.get(KEY_SPAN))
            if v is None: return 0.1, "Median post spacing must be a numeric value."
            if v < 0.1:   return 0.1, "Median post spacing is outside the practical range allowed in the software."
            if span is not None and v > span:
                return span, "Median post spacing is outside the practical range allowed in the software."

        # ── Railing ────────────────────────────────────────────────────────────
        elif key == KEY_RL_HEIGHT:
            v = self._to_float(inputs.get(key))
            if v is None:              return MIN_RAILING_HEIGHT, "Railing height must be a numeric value."
            if v < MIN_RAILING_HEIGHT: return MIN_RAILING_HEIGHT, f"Minimum railing height is {MIN_RAILING_HEIGHT} m as per IRC 5 Cl.109.7.2."
            if v > 3.0:                return 3.0, "Railing height must not exceed 3.0 m."

        elif key == KEY_RL_WIDTH:
            v = self._to_float(inputs.get(key))
            overall = self._to_float(inputs.get(KEY_TS_OVERALL_WIDTH))
            max_rlw = (overall / 2) if overall else None
            if v is None: return 0.0, "Railing width must be a numeric value."
            if v < 0.0:   return 0.0, "Railing width is outside the practical range allowed in the software."
            if max_rlw is not None and v > max_rlw:
                return max_rlw, "Railing width is outside the practical range allowed in the software."

        elif key == KEY_RL_LOAD_VALUE:
            v = self._to_float(inputs.get(key))
            if v is None: return 0.0, "Railing load must be a numeric value."
            if v < 0.0:   return 0.0, "Railing load is outside the practical range allowed in the software."
            if v > 100.0: return 100.0, "Railing load is outside the practical range allowed in the software."

        # ── Wearing Course ─────────────────────────────────────────────────────
        elif key == KEY_WC_DENSITY:
            v = self._to_float(inputs.get(key))
            if v is None: return 0.0, "Wearing course density must be a numeric value."
            if v < 0.0:   return 0.0, "Wearing course density is outside the practical range allowed in the software."
            if v > 10.0:  return 10.0, "Wearing course density is outside the practical range allowed in the software."

        elif key == KEY_WC_THICKNESS:
            v = self._to_float(inputs.get(key))
            if v is None: return 0.0, "Wearing course thickness must be a numeric value."
            if v < 0.0:   return 0.0, "Wearing course thickness is outside the practical range allowed in the software."
            if v > 10.0:  return 10.0, "Wearing course thickness is outside the practical range allowed in the software."

        # ── Lane Details ───────────────────────────────────────────────────────
        elif key == KEY_WC_LD_LANE_TABLE_COUNT:
            carriageway = self._to_float(inputs.get(KEY_CARRIAGEWAY_WIDTH))
            v = self._to_int(inputs.get(key))
            max_lanes = max(1, min(6, int(floor(carriageway / 3.5)))) if carriageway else 6
            if v is None: return 1, "No. of lanes must be an integer value."
            if v < 1:     return 1, "Lane count is outside the practical range allowed in the software (IRC 5 Cl.104.3.1)."
            if v > max_lanes:
                return max_lanes, "Lane count is outside the practical range allowed in the software (IRC 5 Cl.104.3.1)."

        elif key == KEY_WC_LD_LANE_TABLE:
            rows = inputs.get(key)
            if not isinstance(rows, list) or len(rows) == 0:
                return None
            carriageway = self._to_float(inputs.get(KEY_CARRIAGEWAY_WIDTH))
            corrected = []
            start = 0.0
            total = 0.0
            changed = False
            for row in rows:
                if not isinstance(row, (list, tuple)) or len(row) < 3:
                    corrected.append(row)
                    continue
                w = self._to_float(row[2])
                if w is None or w < 3.5:
                    w = 3.5
                    changed = True
                corrected_start = round(start, 6)
                existing_start = self._to_float(row[1])
                if existing_start is None or abs(existing_start - corrected_start) > 1e-3:
                    changed = True
                corrected.append([row[0], corrected_start, w])
                start += w
                total += w
            if changed:
                return corrected, "Lane widths must be at least 3.5 m (IRC 5 Cl.104.3.1) and start positions must be continuous from 0 m."
            if carriageway and total - carriageway > 1e-6:
                return rows, f"Sum of lane widths ({total:.2f} m) exceeds carriageway width ({carriageway:.2f} m). Adjust per IRC 5 Cl.104.3.1."

        # ═══TYPICAL-SECTION-TAB-VALIDATORS-ENDS═══════════════════════════════════════════════════════════

        # ═══LOADING-TAB-VALIDATORS-STARTS════════════════════════════════════════════════════════════════
        # ── Permanent Load ─────────────────────────────────────────────────────
        elif key == KEY_PL_SELF_WEIGHT_FACTOR:
            v = self._to_float(inputs.get(key))
            if v is None: return 1.0, "Self weight modification factor must be a numeric value."
            if v < 0.0:   return 0.0, "Self weight modification factor is outside the practical range allowed in the software."
            if v > 10.0:  return 10.0, "Self weight modification factor is outside the practical range allowed in the software."

        # ── Live Load ──────────────────────────────────────────────────────────
        elif key == KEY_LL_ECCENTRICITY:
            v = self._to_float(inputs.get(key))
            if v is None:  return 0.0, "Eccentricity from top of deck must be a numeric value."
            if v < -10.0:  return -10.0, "Eccentricity from top of deck is outside the practical range allowed in the software."
            if v > 10.0:   return 10.0, "Eccentricity from top of deck is outside the practical range allowed in the software."

        elif key == KEY_LL_FOOTPATH_PRESSURE_VALUE:
            mode = inputs.get(KEY_LL_FOOTPATH_PRESSURE_MODE)
            if mode != "Custom":
                return None
            v = self._to_float(inputs.get(key))
            if v is None:   return 0.0, "Footpath pressure must be a numeric value."
            if v < 0.0:     return 0.0, "Footpath pressure is outside the practical range allowed in the software."
            if v > 5000.0:  return 5000.0, "Footpath pressure is outside the practical range allowed in the software."

        # Custom vehicle popup validators — placeholder

        # ── Seismic Load ───────────────────────────────────────────────────────
        elif key == KEY_SL_IMPORTANCE_FACTOR:
            v = self._to_float(inputs.get(key))
            if v is None: return 1.0, "Importance factor must be a numeric value."
            if v < 0.0:   return 0.0, "Importance factor is outside the practical range allowed in the software."
            if v > 10.0:  return 10.0, "Importance factor is outside the practical range allowed in the software."

        elif key == KEY_SL_TIME_PERIOD:
            v = self._to_float(inputs.get(key))
            if v is None: return 0.0, "Fundamental time period must be a numeric value."
            if v < 0.0:   return 0.0, "Fundamental time period must be between 0 and 4 seconds (outside IRC 6 range)."
            if v > 4.0:   return 4.0, "Fundamental time period must be between 0 and 4 seconds (outside IRC 6 range)."

        elif key == KEY_SL_DAMPING:
            v = self._to_float(inputs.get(key))
            if v is None: return 5.0, "Damping percentage must be a numeric value."
            if v < 2.0:   return 2.0, "Damping percentage must be between 2% and 10% (outside IRC 6 range)."
            if v > 10.0:  return 10.0, "Damping percentage must be between 2% and 10% (outside IRC 6 range)."

        elif key == KEY_SL_DEAD_LOAD_VALUE:
            mode = inputs.get(KEY_SL_DEAD_LOAD_MODE)
            if mode != "Custom":
                return None
            v = self._to_float(inputs.get(key))
            if v is None: return 0.0, "Dead load must be a numeric value."

        elif key == KEY_SL_LIVE_LOAD_VALUE:
            mode = inputs.get(KEY_SL_LIVE_LOAD_MODE)
            if mode != "Custom":
                return None
            v = self._to_float(inputs.get(key))
            if v is None: return 0.0, "Live load must be a numeric value."

        # ── Wind Load ──────────────────────────────────────────────────────────
        elif key == KEY_WL_AVG_EXPOSED_HEIGHT:
            v = self._to_float(inputs.get(key))
            if v is None: return 0.0, "Average exposed height must be a numeric value."
            if v > 100.0: return 100.0, "Average exposed height must not exceed 100 m (outside IRC 6 range)."

        elif key == KEY_WL_GUST_FACTOR_VALUE:
            mode = inputs.get(KEY_WL_GUST_FACTOR_MODE)
            if mode != "Custom":
                return None
            v = self._to_float(inputs.get(key))
            if v is None: return 2.0, "Custom gust factor must be a numeric value."
            if v < 2.0:   return 2.0, "Custom gust factor is outside the practical range allowed in the software."
            if v > 10.0:  return 10.0, "Custom gust factor is outside the practical range allowed in the software."

        elif key == KEY_WL_DRAG_COEFF_VALUE:
            mode = inputs.get(KEY_WL_DRAG_COEFF_MODE)
            if mode != "Custom":
                return None
            v = self._to_float(inputs.get(key))
            if v is None: return 1.0, "Custom drag coefficient must be a numeric value."
            if v < 1.0:   return 1.0, "Custom drag coefficient is outside the practical range allowed in the software."
            if v > 10.0:  return 10.0, "Custom drag coefficient is outside the practical range allowed in the software."

        elif key == KEY_WL_DRAG_COEFF_LL_VALUE:
            mode = inputs.get(KEY_WL_DRAG_COEFF_LL_MODE)
            if mode != "Custom":
                return None
            v = self._to_float(inputs.get(key))
            if v is None: return 1.0, "Custom drag coefficient against live load must be a numeric value."
            if v < 1.0:   return 1.0, "Custom drag coefficient against live load is outside the practical range allowed in the software."
            if v > 10.0:  return 10.0, "Custom drag coefficient against live load is outside the practical range allowed in the software."

        elif key == KEY_WL_LIFT_COEFF_VALUE:
            mode = inputs.get(KEY_WL_LIFT_COEFF_MODE)
            if mode != "Custom":
                return None
            v = self._to_float(inputs.get(key))
            if v is None: return 1.0, "Custom lift coefficient must be a numeric value."
            if v < 1.0:   return 1.0, "Custom lift coefficient is outside the practical range allowed in the software."
            if v > 10.0:  return 10.0, "Custom lift coefficient is outside the practical range allowed in the software."

        elif key == KEY_WL_SUPER_AREA_ELEV_VALUE:
            mode = inputs.get(KEY_WL_SUPER_AREA_ELEV_MODE)
            if mode != "Custom":
                return None
            v = self._to_float(inputs.get(key))
            if v is None: return 0.0, "Superstructure area in elevation must be a numeric value."

        elif key == KEY_WL_SUPER_AREA_PLAIN_VALUE:
            mode = inputs.get(KEY_WL_SUPER_AREA_PLAIN_MODE)
            if mode != "Custom":
                return None
            v = self._to_float(inputs.get(key))
            if v is None: return 0.0, "Superstructure area in plan must be a numeric value."

        elif key == KEY_WL_EXPOSED_FRONTAL_VALUE:
            mode = inputs.get(KEY_WL_EXPOSED_FRONTAL_MODE)
            if mode != "Custom":
                return None
            v = self._to_float(inputs.get(key))
            if v is None: return 0.0, "Exposed frontal area of live load must be a numeric value."

        elif key == KEY_WL_WIND_ECC_DECK_VALUE:
            v = self._to_float(inputs.get(key))
            if v is None:  return 0.0, "Wind load eccentricity from top of deck must be a numeric value."
            if v < -10.0:  return -10.0, "Wind load eccentricity from top of deck is outside the practical range allowed in the software."
            if v > 10.0:   return 10.0, "Wind load eccentricity from top of deck is outside the practical range allowed in the software."

        elif key == KEY_WL_WIND_LL_ECC_VALUE:
            v = self._to_float(inputs.get(key))
            if v is None:  return 0.0, "Wind on live load eccentricity must be a numeric value."
            if v < -10.0:  return -10.0, "Wind on live load eccentricity is outside the practical range allowed in the software."
            if v > 10.0:   return 10.0, "Wind on live load eccentricity is outside the practical range allowed in the software."

        # ── Temperature Load ───────────────────────────────────────────────────
        elif key == KEY_TL_THERMAL_COEFF_STEEL:
            v = self._to_float(inputs.get(key))
            if v is None: return 0.0, "Coefficient of thermal expansion for steel must be a numeric value."

        elif key == KEY_TL_THERMAL_COEFF_RCC:
            v = self._to_float(inputs.get(key))
            if v is None: return 0.0, "Coefficient of thermal expansion for RCC must be a numeric value."

        # ═══LOADING-TAB-VALIDATORS-ENDS══════════════════════════════════════════════════════════════════


        # ═══SUPPORT-CONDITION-TAB-VALIDATORS-STARTS═════════════════════════════════════════════════════
        
        # ═══SUPPORT-CONDITION-TAB-VALIDATORS-ENDS═══════════════════════════════════════════════════════


        # ═══ANALYSIS/DESIGN-OPTIONS-TAB-VALIDATORS-STARTS═════════════════════════════════════════════════════

        # ── Reinforcement Bounds ────────────────────────────────────────────────
        elif key == KEY_DS_REINF_BOUNDS:
            bounds = inputs.get(key)
            if not isinstance(bounds, dict):
                return {"lower": 8, "upper": 40}, "Reinforcement size bounds must be specified with integer lower and upper bar diameters."
            lower = self._to_int(bounds.get("lower"))
            upper = self._to_int(bounds.get("upper"))
            corrected = dict(bounds)
            changed = False
            if lower is None: lower = 8;  changed = True
            if upper is None: upper = 40; changed = True
            if lower < 8:    lower = 8;  changed = True
            if lower > 40:   lower = 40; changed = True
            if upper < 8:    upper = 8;  changed = True
            if upper > 40:   upper = 40; changed = True
            if upper < lower: upper = lower; changed = True
            if changed:
                corrected["lower"] = lower
                corrected["upper"] = upper
                return corrected, "Reinforcement bar diameter bounds must be integers between 8 and 40 mm, with upper bound not less than lower bound."

        # ── Clear Covers ────────────────────────────────────────────────────────
        elif key == KEY_DS_TOP_CLEAR_COVER:
            v = self._to_float(inputs.get(key))
            if v is None: return 40, "Top clear cover must be a numeric value."
            if v < 40:    return 40, "Top clear cover must be between 40 and 75 mm."
            if v > 75:    return 75, "Top clear cover must be between 40 and 75 mm."

        elif key == KEY_DS_BOTTOM_CLEAR_COVER:
            v = self._to_float(inputs.get(key))
            if v is None: return 35, "Bottom clear cover must be a numeric value."
            if v < 35:    return 35, "Bottom clear cover must be between 35 and 75 mm."
            if v > 75:    return 75, "Bottom clear cover must be between 35 and 75 mm."

        elif key == KEY_DS_SIDE_CLEAR_COVER:
            v = self._to_float(inputs.get(key))
            if v is None: return 35, "Side clear cover must be a numeric value."
            if v < 35:    return 35, "Side clear cover must be between 35 and 75 mm."
            if v > 75:    return 75, "Side clear cover must be between 35 and 75 mm."

        # ── Shear Stud Properties ───────────────────────────────────────────────
        elif key == KEY_DS_STUD_YIELD_STRENGTH:
            v = self._to_float(inputs.get(key))
            if v is None: return 350, "Yield strength must be a numeric value."
            if v < 350:   return 350, "Yield strength must be between 350 and 600 MPa."
            if v > 600:   return 600, "Yield strength must be between 350 and 600 MPa."

        elif key == KEY_DS_STUD_ULTIMATE_STRENGTH:
            v = self._to_float(inputs.get(key))
            if v is None: return 350, "Ultimate strength must be a numeric value."
            if v < 350:   return 350, "Ultimate strength must be between 350 and 600 MPa."
            if v > 600:   return 600, "Ultimate strength must be between 350 and 600 MPa."

        elif key == KEY_DS_STUD_HEIGHT:
            v      = self._to_float(inputs.get(key))
            d      = self._to_float(inputs.get(KEY_DS_STUD_DIAMETER))
            deck_t = self._to_float(inputs.get(KEY_TS_DECK_THICKNESS))
            min_h  = (4.0 * d) if d is not None else None
            max_h  = (deck_t - 25.0) if deck_t is not None else None
            if v is None:
                return (min_h if min_h is not None else 0), "Stud height must be a numeric value."
            if min_h is not None and v < min_h:
                return min_h, f"Stud height must be between {min_h:.0f} mm (4× stud diameter) and {max_h:.0f} mm (deck thickness − 25 mm)."
            if max_h is not None and v > max_h:
                return max_h, f"Stud height must be between {min_h:.0f} mm (4× stud diameter) and {max_h:.0f} mm (deck thickness − 25 mm)."

        elif key == KEY_DS_STUD_COUNT:
            v         = self._to_int(inputs.get(key))
            d         = self._to_float(inputs.get(KEY_DS_STUD_DIAMETER))
            flange_m  = self._to_float(inputs.get(KEY_MP_GIRDER_TOP_FLANGE_WIDTH))
            flange_mm = flange_m * 1000.0 if flange_m is not None else None
            max_n     = int(ceil((flange_mm - 50.0) / (2.5 * d))) if (flange_mm is not None and d) else None
            if max_n is not None: max_n = max(max_n, 1)
            if v is None: return 1, "No. of studs per section must be an integer value."
            if v < 1:     return 1, "No. of studs per section is outside the practical range allowed in the software."
            if max_n is not None and v > max_n:
                return max_n, "No. of studs per section is outside the practical range allowed in the software."

        elif key == KEY_DS_STUD_TRANSVERSE_SPACING:
            v         = self._to_float(inputs.get(key))
            d         = self._to_float(inputs.get(KEY_DS_STUD_DIAMETER))
            flange_m  = self._to_float(inputs.get(KEY_MP_GIRDER_TOP_FLANGE_WIDTH))
            flange_mm = flange_m * 1000.0 if flange_m is not None else None
            n         = self._to_int(inputs.get(KEY_DS_STUD_COUNT))
            min_sp    = (2.5 * d) if d is not None else None
            max_sp    = (flange_mm - 50.0 - d * (n - 1)) if (flange_mm is not None and d is not None and n is not None) else None
            if v is None:
                return (min_sp if min_sp is not None else 0), "Transverse spacing must be a numeric value."
            if min_sp is not None and v < min_sp:
                return min_sp, f"Transverse spacing must be between {min_sp:.1f} mm and {max_sp:.1f} mm."
            if max_sp is not None and v > max_sp:
                return max_sp, f"Transverse spacing must be between {min_sp:.1f} mm and {max_sp:.1f} mm."

        # ═══ANALYSIS/DESIGN-OPTIONS-TAB-VALIDATORS-ENDS═══════════════════════════════════════════════════════


        # ═══DESIGN-OPTIONS-CONT-TAB-VALIDATORS-STARTS═════════════════════════════════════════════════════

        # ── Partial Factors ─────────────────────────────────────────────────────
        elif key == KEY_DO_GAMMA_C_BASIC:
            v = self._to_float(inputs.get(key))
            if v is None: return 1.0, "Partial factor γc (basic) must be a numeric value."
            if v < 1.0:   return 1.0, "Partial factor γc (basic) must be between 1.0 and 2.0."
            if v > 2.0:   return 2.0, "Partial factor γc (basic) must be between 1.0 and 2.0."

        elif key == KEY_DO_GAMMA_C_ACCIDENTAL:
            v = self._to_float(inputs.get(key))
            if v is None: return 1.0, "Partial factor γc (accidental) must be a numeric value."
            if v < 1.0:   return 1.0, "Partial factor γc (accidental) must be between 1.0 and 2.0."
            if v > 2.0:   return 2.0, "Partial factor γc (accidental) must be between 1.0 and 2.0."

        elif key == KEY_DO_GAMMA_M0:
            v = self._to_float(inputs.get(key))
            if v is None: return 1.0, "Partial factor γm0 must be a numeric value."
            if v < 1.0:   return 1.0, "Partial factor γm0 must be between 1.0 and 2.0."
            if v > 2.0:   return 2.0, "Partial factor γm0 must be between 1.0 and 2.0."

        elif key == KEY_DO_GAMMA_M1:
            v = self._to_float(inputs.get(key))
            if v is None: return 1.0, "Partial factor γm1 must be a numeric value."
            if v < 1.0:   return 1.0, "Partial factor γm1 must be between 1.0 and 2.0."
            if v > 2.0:   return 2.0, "Partial factor γm1 must be between 1.0 and 2.0."

        elif key == KEY_DO_GAMMA_S:
            v = self._to_float(inputs.get(key))
            if v is None: return 1.0, "Partial factor γs must be a numeric value."
            if v < 1.0:   return 1.0, "Partial factor γs must be between 1.0 and 2.0."
            if v > 2.0:   return 2.0, "Partial factor γs must be between 1.0 and 2.0."

        elif key == KEY_DO_GAMMA_V:
            v = self._to_float(inputs.get(key))
            if v is None: return 1.0, "Partial factor γv must be a numeric value."
            if v < 1.0:   return 1.0, "Partial factor γv must be between 1.0 and 2.0."
            if v > 2.0:   return 2.0, "Partial factor γv must be between 1.0 and 2.0."

        elif key == KEY_DO_GAMMA_FLT:
            v = self._to_float(inputs.get(key))
            if v is None: return 1.0, "Partial factor γFlt must be a numeric value."
            if v < 1.0:   return 1.0, "Partial factor γFlt must be between 1.0 and 2.0."
            if v > 2.0:   return 2.0, "Partial factor γFlt must be between 1.0 and 2.0."

        elif key == KEY_DO_GAMMA_MF:
            v = self._to_float(inputs.get(key))
            if v is None: return 1.0, "Partial factor γMf must be a numeric value."
            if v < 1.0:   return 1.0, "Partial factor γMf must be between 1.0 and 2.0."
            if v > 2.0:   return 2.0, "Partial factor γMf must be between 1.0 and 2.0."

        # ── Fatigue ─────────────────────────────────────────────────────────────
        elif key == KEY_DO_LOAD_CYCLES:
            v = self._to_int(inputs.get(key))
            if v is None:       return 100000, "No. of load cycles must be a numeric value."
            if v < 100000:      return 100000, "No. of load cycles must be between 100,000 and 100,000,000."
            if v > 100000000:   return 100000000, "No. of load cycles must be between 100,000 and 100,000,000."

        # ── Deflection ──────────────────────────────────────────────────────────
        elif key == KEY_DO_DEFLECTION_LIMIT:
            v = self._to_float(inputs.get(key))
            if v is None: return 300, "Deflection limit denominator must be a numeric value."
            if v < 300:   return 300, "Deflection limit denominator must be between 300 and 800."
            if v > 800:   return 800, "Deflection limit denominator must be between 300 and 800."

        # ═══DESIGN-OPTIONS-CONT-TAB-VALIDATORS-ENDS═══════════════════════════════════════════════════════


        return None
    
    # def validate_additional_inputs(self, inputs: dict) -> dict:

    #     errors = {}

    #     overall_width = self._to_float(inputs.get("overall_bridge_width"))
    #     girder_spacing = self._to_float(inputs.get("girder_spacing"))
    #     overhang = self._to_float(inputs.get("deck_overhang"))
    #     no_girders = self._to_int(inputs.get("no_of_girders"))

    #     # ----------------------------
    #     # Layout Equation Check
    #     # ----------------------------
    #     if all(v is not None for v in
    #            [overall_width, girder_spacing, overhang, no_girders]):

    #         lhs = (no_girders - 1) * girder_spacing + 2 * overhang

    #         if not isclose(lhs, overall_width, rel_tol=1e-2):
    #             errors["layout_equation"] = (
    #                 "Layout must satisfy: "
    #                 "Overall Width = (No. of Girders − 1) × Spacing + 2 × Overhang."
    #             )

    #     # ----------------------------
    #     # Safety Kerb Check (IRC 5 Cl.101.41)
    #     # ----------------------------
    #     kerb_width = self._to_float(inputs.get("kerb_width"))
    #     footpath = inputs.get(KEY_FOOTPATH)

    #     if kerb_width is not None:

    #         kerb_result = IRC5_2015.cl_101_41_safety_kerb_width(
    #             kerb_width,
    #             footpath
    #         )

    #         if kerb_result["applicable"] and not kerb_result["is_compliant"]:
    #             errors["kerb_width"] = kerb_result["remarks"]
		
	# 	# ----------------------------
    #     # Footpath Width (IRC 5 Cl.104.3.6)
    #     # ----------------------------
    #     footpath_width = self._to_float(inputs.get("footpath_width"))

    #     result = IRC5_2015.cl_104_3_6_footpath_width(
    #         footpath,
    #         footpath_width
    #     )

    #     if result["applicable"] and not result["is_compliant"]:
    #         errors["footpath_width"] = result["remarks"]
		
    #     # ----------------------------
    #     # Railing Height (IRC 5 Cl.109.7.2)
    #     # ----------------------------
    #     railing_height = self._to_float(inputs.get("railing_height"))

    #     if railing_height is not None and footpath in KEY_FOOTPATH:
    #         if railing_height < KEY_RAILING_MIN_HEIGHT[0]:
    #             errors["railing_height"] = (
    #                 f"Minimum railing height is "
    #                 f"{KEY_RAILING_MIN_HEIGHT[0]} mm."
    #             )

    #     # ----------------------------
    #     # Stud Detailing (Keyfile constants)
    #     # ----------------------------
    #     stud_height = self._to_float(inputs.get("stud_height"))
    #     stud_diameter = self._to_float(inputs.get("stud_diameter"))
    #     flange_thickness = self._to_float(inputs.get("top_flange_thickness"))

    #     if stud_height is not None:
    #         if stud_height < MIN_STUD_HEIGHT_MM:
    #             errors["stud_height"] = (
    #                 f"Minimum stud height must be "
    #                 f"{MIN_STUD_HEIGHT_MM} mm."
    #             )

    #     if stud_diameter and flange_thickness:
    #         if stud_diameter > MAX_STUD_DIAMETER_FACTOR * flange_thickness:
    #             errors["stud_diameter"] = (
    #                 "Stud diameter exceeds permitted proportion of flange thickness."
    #             )

    #     # ----------------------------
    #     # Edge Distance
    #     # ----------------------------
    #     edge_distance = self._to_float(inputs.get("stud_edge_distance"))

    #     if edge_distance is not None:
    #         if edge_distance < MIN_EDGE_DISTANCE_MM:
    #             errors["stud_edge_distance"] = (
    #                 f"Minimum edge distance must be "
    #                 f"{MIN_EDGE_DISTANCE_MM} mm."
    #             )

    #     return self._format_response(errors)

    # ==========================================================
    # INTERNAL HELPERS
    # ==========================================================

    def _format_response(self, errors: dict) -> dict:
        return {
            "status": len(errors) == 0,
            "errors": errors
        }

    def _to_float(self, value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _to_int(self, value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
