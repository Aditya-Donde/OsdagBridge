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
    # CUSTOM MATERIAL PROPERTY VALIDATION
    # Steel members: Girder, Cross Bracing, End Diaphragm.
    # Concrete member: Deck.
    # ==========================================================

    def validate_material_inputs(self, key: str, inputs: dict):
        """
        Per-field validation for custom material properties (steel and concrete/deck).
        Returns (corrected_value, message) on error, None if valid.
        """

        # ── Weight Density (kN/m³) ──────────────────────────────────────────────
        if key == KEY_MATERIAL_GIRDER_DENSITY:
            v = self._to_float(inputs.get(key))
            if v is None:  return 50.0,  "Weight Density must be a numeric value."
            if v < 50.0:   return 50.0,  "Weight Density must be between 50.0 and 120.0 kN/m³."
            if v > 120.0:  return 120.0, "Weight Density must be between 50.0 and 120.0 kN/m³."

        # ── Yield Strength, Fy (MPa) ────────────────────────────────────────────
        elif key == KEY_MATERIAL_GIRDER_FY:
            v = self._to_float(inputs.get(key))
            if v is None:   return 100.0,  "Yield Strength, Fy must be a numeric value."
            if v < 100.0:   return 100.0,  "Yield Strength, Fy must be between 100.0 and 1200.0 MPa."
            if v > 1200.0:  return 1200.0, "Yield Strength, Fy must be between 100.0 and 1200.0 MPa."

        # ── Ultimate Tensile Strength, Fu (MPa) ─────────────────────────────────
        elif key == KEY_MATERIAL_GIRDER_FU:
            v = self._to_float(inputs.get(key))
            if v is None:   return 100.0,  "Ultimate Tensile Strength, Fu must be a numeric value."
            if v < 100.0:   return 100.0,  "Ultimate Tensile Strength, Fu must be between 100.0 and 1500.0 MPa."
            if v > 1500.0:  return 1500.0, "Ultimate Tensile Strength, Fu must be between 100.0 and 1500.0 MPa."

        # ── Modulus of Elasticity, E (GPa) ──────────────────────────────────────
        elif key == KEY_MATERIAL_GIRDER_E:
            v = self._to_float(inputs.get(key))
            if v is None:  return 100.0, "Modulus of Elasticity, E must be a numeric value."
            if v < 100.0:  return 100.0, "Modulus of Elasticity, E must be between 100.0 and 300.0 GPa."
            if v > 300.0:  return 300.0, "Modulus of Elasticity, E must be between 100.0 and 300.0 GPa."

        # ── Modulus of Rigidity, G (GPa) ────────────────────────────────────────
        elif key == KEY_MATERIAL_GIRDER_G:
            v = self._to_float(inputs.get(key))
            if v is None:  return 30.0,  "Modulus of Rigidity, G must be a numeric value."
            if v < 30.0:   return 30.0,  "Modulus of Rigidity, G must be between 30.0 and 120.0 GPa."
            if v > 120.0:  return 120.0, "Modulus of Rigidity, G must be between 30.0 and 120.0 GPa."

        # ── Poisson's Ratio, ν ──────────────────────────────────────────────────
        elif key == KEY_MATERIAL_GIRDER_POISSON:
            v = self._to_float(inputs.get(key))
            if v is None: return 0.0, "Poisson's Ratio must be a numeric value."
            if v < 0.0:   return 0.0, "Poisson's Ratio must be between 0.0 and 0.5."
            if v > 0.5:   return 0.5, "Poisson's Ratio must be between 0.0 and 0.5."

        # ── Thermal Expansion Coefficient (×10⁻⁶/°C) ────────────────────────────
        elif key == KEY_MATERIAL_GIRDER_THERMAL:
            v = self._to_float(inputs.get(key))
            if v is None: return 1.0,  "Thermal Expansion Coefficient must be a numeric value."
            if v < 1.0:   return 1.0,  "Thermal Expansion Coefficient must be between 1.0 and 30.0 (×10⁻⁶/°C)."
            if v > 30.0:  return 30.0, "Thermal Expansion Coefficient must be between 1.0 and 30.0 (×10⁻⁶/°C)."

        # ── Deck: Weight Density (kN/m³) ────────────────────────────────────────
        elif key == KEY_MATERIAL_DECK_DENSITY:
            v = self._to_float(inputs.get(key))
            if v is None: return 18.0, "Weight Density must be a numeric value."
            if v < 18.0:  return 18.0, "Weight Density must be between 18.0 and 28.0 kN/m³."
            if v > 28.0:  return 28.0, "Weight Density must be between 18.0 and 28.0 kN/m³."

        # ── Deck: Char. Compressive (Cube) Strength, fck (MPa) ──────────────────
        elif key == KEY_MATERIAL_DECK_FCK:
            v = self._to_float(inputs.get(key))
            if v is None: return 10.0, "Characteristic Compressive Strength, fck must be a numeric value."
            if v < 10.0:  return 10.0, "Characteristic Compressive Strength, fck must be between 10.0 and 80.0 MPa."
            if v > 80.0:  return 80.0, "Characteristic Compressive Strength, fck must be between 10.0 and 80.0 MPa."

        # ── Deck: Mean Tensile Strength, fctm (MPa) ─────────────────────────────
        elif key == KEY_MATERIAL_DECK_FCTM:
            v = self._to_float(inputs.get(key))
            if v is None: return 0.5, "Mean Tensile Strength, fctm must be a numeric value."
            if v < 0.5:   return 0.5, "Mean Tensile Strength, fctm must be between 0.5 and 6.0 MPa."
            if v > 6.0:   return 6.0, "Mean Tensile Strength, fctm must be between 0.5 and 6.0 MPa."

        # ── Deck: Secant Modulus of Elasticity, Ecm (GPa) ───────────────────────
        elif key == KEY_MATERIAL_DECK_ECM:
            v = self._to_float(inputs.get(key))
            if v is None: return 15.0, "Secant Modulus of Elasticity, Ecm must be a numeric value."
            if v < 15.0:  return 15.0, "Secant Modulus of Elasticity, Ecm must be between 15.0 and 50.0 GPa."
            if v > 50.0:  return 50.0, "Secant Modulus of Elasticity, Ecm must be between 15.0 and 50.0 GPa."

        # ── Deck: Thermal Expansion Coefficient (×10⁻⁶/°C) ──────────────────────
        elif key == KEY_MATERIAL_DECK_THERMAL:
            v = self._to_float(inputs.get(key))
            if v is None: return 5.0,  "Thermal Expansion Coefficient must be a numeric value."
            if v < 5.0:   return 5.0,  "Thermal Expansion Coefficient must be between 5.0 and 15.0 (×10⁻⁶/°C)."
            if v > 15.0:  return 15.0, "Thermal Expansion Coefficient must be between 5.0 and 15.0 (×10⁻⁶/°C)."

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
            cw = self._to_float(inputs.get(KEY_CARRIAGEWAY_WIDTH))
            if cw is not None and v is not None and v > cw:
                return cw, "Footpath width is outside the practical range allowed in the software."

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
            if v < 0.0:   return 0.0, "Wearing course thickness must be greater than 0.0 mm."
            if v > 150.0:  return 150.0, "Wearing course thickness must be less than 150.0 mm."

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

        # ═══MEMBER-PROPERTIES-TAB-VALIDATORS-STARTS══════════════════════════════════════════════════════

        # ── Girder Details: Segment Chain ─────────────────────────────────────
        elif key == "member_properties.girder_details.segment_chain":  # placeholder – KEY_GIRDER_SEGMENT_CHAIN not yet defined
            chain = inputs.get(key)
            if not isinstance(chain, list) or len(chain) == 0:
                return None
            span = self._to_float(inputs.get(KEY_SPAN))
            corrected = [dict(seg) if isinstance(seg, dict) else seg for seg in chain]
            changed = False
            for i in range(len(chain)):
                seg = chain[i]
                if not isinstance(seg, dict):
                    continue
                end = self._to_float(seg.get("end"))
                if end is None:
                    corrected[i]["end"] = 0.0
                    changed = True
                    continue
                if i < len(chain) - 1:
                    next_seg = chain[i + 1]
                    next_end = self._to_float(next_seg.get("end")) if isinstance(next_seg, dict) else None
                    if next_end is not None and end > next_end:
                        corrected[i]["end"] = next_end
                        changed = True
            if span is not None and len(corrected) > 0:
                last = corrected[-1]
                if isinstance(last, dict):
                    last_end = self._to_float(last.get("end"))
                    if last_end is None or abs(last_end - span) > 1e-4:
                        corrected[-1]["end"] = span
                        changed = True
            if changed:
                return corrected, "Segment end values must be numeric, in ascending order, and the last segment end must equal the span length."

        # ── Girder Details: Support Width ─────────────────────────────────────
        elif key == KEY_MP_GD_SUPPORT_WIDTH:
            v = self._to_float(inputs.get(key))
            if v is None: return 400, "Support width must be a numeric value."
            if v < 150:   return 150, "Support width must be between 150 mm and 800 mm (practical range for composite bridge girders per MoRTH/IRC)."
            if v > 800:   return 800, "Support width must be between 150 mm and 800 mm (practical range for composite bridge girders per MoRTH/IRC)."

        # ── Girder Details: Total Depth ───────────────────────────────────────
        elif key == KEY_MP_GIRDER_DEPTH:
            design_mode = str(inputs.get(KEY_DESIGN_MODE) or "").strip().lower()
            if design_mode == "optimized":
                bounds = inputs.get(key)
                if not isinstance(bounds, dict):
                    return {"lower": 200, "upper": 2000, "increment": 25}, "Total depth bounds must be specified."
                lower     = self._to_int(bounds.get("lower"))
                upper     = self._to_int(bounds.get("upper"))
                increment = self._to_int(bounds.get("increment"))
                corrected = dict(bounds)
                changed   = False
                if lower is None:     lower = 200;  changed = True
                if upper is None:     upper = 2000; changed = True
                if increment is None: increment = 25; changed = True
                if lower < 200:       lower = 200;  changed = True
                if lower > 3000:      lower = 3000; changed = True
                if upper < 200:       upper = 200;  changed = True
                if upper > 3000:      upper = 3000; changed = True
                if upper < lower:     upper = lower; changed = True
                if increment <= 0:    increment = 25; changed = True
                if upper > lower and increment > (upper - lower):
                    increment = upper - lower; changed = True
                if changed:
                    corrected.update({"lower": lower, "upper": upper, "increment": increment})
                    return corrected, "Total depth bounds: lower and upper must be integers between 200 and 3000 mm, with upper >= lower. Increment must be a positive integer not exceeding the bound range."
            else:  # Custom
                v = self._to_float(inputs.get(key))
                if v is None: return 200,  "Total depth must be a numeric value."
                if v < 200:   return 200,  "Total depth must be between 200 and 3000 mm."
                if v > 3000:  return 3000, "Total depth must be between 200 and 3000 mm."

        # ── Girder Details: Top Flange Width ──────────────────────────────────
        elif key == KEY_MP_GIRDER_TOP_FLANGE_WIDTH:
            design_mode = str(inputs.get(KEY_DESIGN_MODE) or "").strip().lower()
            if design_mode == "optimized":
                bounds = inputs.get(key)
                if not isinstance(bounds, dict):
                    return {"lower": 100, "upper": 1000, "increment": 10}, "Top flange width bounds must be specified."
                lower     = self._to_int(bounds.get("lower"))
                upper     = self._to_int(bounds.get("upper"))
                increment = self._to_int(bounds.get("increment"))
                corrected = dict(bounds)
                changed   = False
                if lower is None:     lower = 100;  changed = True
                if upper is None:     upper = 1000; changed = True
                if increment is None: increment = 10; changed = True
                if lower < 100:       lower = 100;  changed = True
                if lower > 1500:      lower = 1500; changed = True
                if upper < 100:       upper = 100;  changed = True
                if upper > 1500:      upper = 1500; changed = True
                if upper < lower:     upper = lower; changed = True
                if increment <= 0:    increment = 10; changed = True
                if upper > lower and increment > (upper - lower):
                    increment = upper - lower; changed = True
                if changed:
                    corrected.update({"lower": lower, "upper": upper, "increment": increment})
                    return corrected, "Top flange width bounds: lower and upper must be integers between 100 and 1500 mm, with upper >= lower. Increment must be a positive integer not exceeding the bound range."
            else:  # Custom
                v = self._to_float(inputs.get(key))
                if v is None: return 100,  "Top flange width must be a numeric value."
                if v < 100:   return 100,  "Top flange width must be between 100 and 1500 mm."
                if v > 1500:  return 1500, "Top flange width must be between 100 and 1500 mm."

        # ── Girder Details: Bottom Flange Width ───────────────────────────────
        elif key == KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH:
            design_mode = str(inputs.get(KEY_DESIGN_MODE) or "").strip().lower()
            if design_mode == "optimized":
                bounds = inputs.get(key)
                if not isinstance(bounds, dict):
                    return {"lower": 100, "upper": 1000, "increment": 10}, "Bottom flange width bounds must be specified."
                lower     = self._to_int(bounds.get("lower"))
                upper     = self._to_int(bounds.get("upper"))
                increment = self._to_int(bounds.get("increment"))
                corrected = dict(bounds)
                changed   = False
                if lower is None:     lower = 100;  changed = True
                if upper is None:     upper = 1000; changed = True
                if increment is None: increment = 10; changed = True
                if lower < 100:       lower = 100;  changed = True
                if lower > 1500:      lower = 1500; changed = True
                if upper < 100:       upper = 100;  changed = True
                if upper > 1500:      upper = 1500; changed = True
                if upper < lower:     upper = lower; changed = True
                if increment <= 0:    increment = 10; changed = True
                if upper > lower and increment > (upper - lower):
                    increment = upper - lower; changed = True
                if changed:
                    corrected.update({"lower": lower, "upper": upper, "increment": increment})
                    return corrected, "Bottom flange width bounds: lower and upper must be integers between 100 and 1500 mm, with upper >= lower. Increment must be a positive integer not exceeding the bound range."
            else:  # Custom
                v = self._to_float(inputs.get(key))
                if v is None: return 100,  "Bottom flange width must be a numeric value."
                if v < 100:   return 100,  "Bottom flange width must be between 100 and 1500 mm."
                if v > 1500:  return 1500, "Bottom flange width must be between 100 and 1500 mm."

        # ── Girder Details: Thickness Selections (Optimized only) ─────────────
        elif key == KEY_MP_GIRDER_TOP_FLANGE_THICKNESS:
            selected = inputs.get(key)
            if not isinstance(selected, list) or len(selected) == 0:
                return SAIL_APPROVED_THICKNESS_VALUES, "At least one top flange thickness value must be selected."

        elif key == KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS:
            selected = inputs.get(key)
            if not isinstance(selected, list) or len(selected) == 0:
                return SAIL_APPROVED_THICKNESS_VALUES, "At least one bottom flange thickness value must be selected."

        elif key == KEY_MP_GIRDER_WEB_THICKNESS:
            selected = inputs.get(key)
            if not isinstance(selected, list) or len(selected) == 0:
                return SAIL_APPROVED_THICKNESS_VALUES, "At least one web thickness value must be selected."

        # ── Stiffener Details (Custom design only) ────────────────────────────
        elif key == KEY_MP_STIFFENER_SPACING:
            v         = self._to_float(inputs.get(key))
            if v is None: return 20, "Bearing stiffener spacing must be a numeric value."
            if v < 20:    return 20, "Bearing stiffener spacing must be at least 20 mm."
            if v > 75:    return 75, "Bearing stiffener spacing must not exceed 75 mm."

        elif key == KEY_MP_STIFFENER_BEARING_OUTSTAND:
            v       = self._to_float(inputs.get(key))
            tf_top  = self._to_float(inputs.get(KEY_MP_GIRDER_TOP_FLANGE_WIDTH))
            tf_bot  = self._to_float(inputs.get(KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH))
            web_t   = self._to_float(inputs.get(KEY_MP_GIRDER_WEB_THICKNESS))
            flanges = [f for f in [tf_top, tf_bot] if f is not None]
            max_os  = ((min(flanges) - (web_t or 0.0)) / 2.0) if flanges else None
            if max_os is not None: max_os = max(max_os, 0.0)
            if v is None: return 0, "Outstand of bearing stiffener must be a numeric value."
            if v < 0:     return 0, "Outstand of bearing stiffener must be at least 0 mm."
            if max_os is not None and v > max_os:
                return max_os, f"Outstand of bearing stiffener must not exceed {max_os:.1f} mm ((min flange width - web thickness) / 2)."

        elif key == KEY_MP_STIFFENER_INTERMEDIATE_SPACING:
            v = self._to_float(inputs.get(key))
            if v is None: return 75,   "Intermediate stiffener spacing must be a numeric value."
            if v < 75:    return 75,   "Intermediate stiffener spacing must be between 75 and 3000 mm."
            if v > 3000:  return 3000, "Intermediate stiffener spacing must be between 75 and 3000 mm."

        elif key == KEY_MP_STIFFENER_INTERMEDIATE_OUTSTAND:
            v       = self._to_float(inputs.get(key))
            tf_top  = self._to_float(inputs.get(KEY_MP_GIRDER_TOP_FLANGE_WIDTH))
            tf_bot  = self._to_float(inputs.get(KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH))
            web_t   = self._to_float(inputs.get(KEY_MP_GIRDER_WEB_THICKNESS))
            flanges = [f for f in [tf_top, tf_bot] if f is not None]
            max_os  = ((min(flanges) - (web_t or 0.0)) / 2.0) if flanges else None
            if max_os is not None: max_os = max(max_os, 0.0)
            if v is None: return 0, "Outstand of intermediate stiffener must be a numeric value."
            if v < 0:     return 0, "Outstand of intermediate stiffener must be at least 0 mm."
            if max_os is not None and v > max_os:
                return max_os, f"Outstand of intermediate stiffener must not exceed {max_os:.1f} mm ((min flange width - web thickness) / 2)."

        # ── Cross Bracing Details ─────────────────────────────────────────────
        elif key == KEY_MP_CB_NO_OF_CROSS_BRACINGS:  # placeholder - KEY_NO_C...
            v    = self._to_int(inputs.get(key))
            span = self._to_float(inputs.get(KEY_SPAN))
            max_cb = int(floor(span - 1)) if span is not None and span > 1 else 1
            if v is None: return 1, "No. of cross bracings must be an integer value."
            if v < 1:     return 1, "No. of cross bracings must be at least 1."
            if v > max_cb:
                return max_cb, f"No. of cross bracings must not exceed {max_cb} for the given span."

        # ── End Diaphragm Details (Custom, Welded Beam only) ──────────────────
        elif key == "member_properties.end_diaphragm_details.welded_beam.depth":  # placeholder – KEY_END_DIAPHRAGM_WELDED_DEPTH not yet defined
            end_type    = str(inputs.get(KEY_MP_ED_TYPE) or "").strip()
            design_mode = str(inputs.get(KEY_DESIGN_MODE) or "").strip().lower()
            if end_type == "Welded Beam" and design_mode == "custom":
                v = self._to_float(inputs.get(key))
                if v is None: return 200,  "End diaphragm (Welded Beam) depth must be a numeric value."
                if v < 200:   return 200,  "End diaphragm (Welded Beam) depth must be between 200 and 3000 mm."
                if v > 3000:  return 3000, "End diaphragm (Welded Beam) depth must be between 200 and 3000 mm."

        elif key == "member_properties.end_diaphragm_details.welded_beam.top_flange_width":  # placeholder – KEY_END_DIAPHRAGM_WELDED_TOP_FLANGE_WIDTH not yet defined
            end_type    = str(inputs.get(KEY_MP_ED_TYPE) or "").strip()
            design_mode = str(inputs.get(KEY_DESIGN_MODE) or "").strip().lower()
            if end_type == "Welded Beam" and design_mode == "custom":
                v = self._to_float(inputs.get(key))
                if v is None: return 100,  "End diaphragm (Welded Beam) top flange width must be a numeric value."
                if v < 100:   return 100,  "End diaphragm (Welded Beam) top flange width must be between 100 and 1500 mm."
                if v > 1500:  return 1500, "End diaphragm (Welded Beam) top flange width must be between 100 and 1500 mm."

        elif key == "member_properties.end_diaphragm_details.welded_beam.bottom_flange_width":  # placeholder – KEY_END_DIAPHRAGM_WELDED_BOTTOM_FLANGE_WIDTH not yet defined
            end_type    = str(inputs.get(KEY_MP_ED_TYPE) or "").strip()
            design_mode = str(inputs.get(KEY_DESIGN_MODE) or "").strip().lower()
            if end_type == "Welded Beam" and design_mode == "custom":
                v = self._to_float(inputs.get(key))
                if v is None: return 100,  "End diaphragm (Welded Beam) bottom flange width must be a numeric value."
                if v < 100:   return 100,  "End diaphragm (Welded Beam) bottom flange width must be between 100 and 1500 mm."
                if v > 1500:  return 1500, "End diaphragm (Welded Beam) bottom flange width must be between 100 and 1500 mm."

        # ═══MEMBER-PROPERTIES-TAB-VALIDATORS-ENDS════════════════════════════════════════════════════════

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
            if v < 0.0:   return 0.0, "Dead load is outside the practical range allowed in the software."
            if v > 30000.0: return 30000.0, "Dead load is outside the practical range allowed in the software."

        elif key == KEY_SL_LIVE_LOAD_VALUE:
            mode = inputs.get(KEY_SL_LIVE_LOAD_MODE)
            if mode != "Custom":
                return None
            v = self._to_float(inputs.get(key))
            if v is None: return 0.0, "Live load must be a numeric value."
            if v < 0.0:   return 0.0, "Live load is outside the practical range allowed in the software."
            if v > 30000.0: return 30000.0, "Live load is outside the practical range allowed in the software."

        # ── Wind Load ──────────────────────────────────────────────────────────
        elif key == KEY_WL_AVG_EXPOSED_HEIGHT:
            v = self._to_float(inputs.get(key))
            if v is None: return 0.0, "Average exposed height must be a numeric value."
            if v < 0.0:   return 0.0, "Average exposed height is outside the practical range allowed in the software."
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
            if v < 0.0:   return 0.0, "Superstructure area in elevation is outside the practical range allowed in the software."
            if v > 1000.0: return 1000.0, "Superstructure area in elevation is outside the practical range allowed in the software."

        elif key == KEY_WL_SUPER_AREA_PLAIN_VALUE:
            mode = inputs.get(KEY_WL_SUPER_AREA_PLAIN_MODE)
            if mode != "Custom":
                return None
            v = self._to_float(inputs.get(key))
            if v is None: return 0.0, "Superstructure area in plan must be a numeric value."
            if v < 0.0:   return 0.0, "Superstructure area in plan is outside the practical range allowed in the software."
            if v > 2000.0: return 2000.0, "Superstructure area in plan is outside the practical range allowed in the software."

        elif key == KEY_WL_EXPOSED_FRONTAL_VALUE:
            mode = inputs.get(KEY_WL_EXPOSED_FRONTAL_MODE)
            if mode != "Custom":
                return None
            v = self._to_float(inputs.get(key))
            if v is None: return 0.0, "Exposed frontal area of live load must be a numeric value."
            if v < 0.0:   return 0.0, "Exposed frontal area of live load is outside the practical range allowed in the software."
            if v > 500.0:  return 500.0, "Exposed frontal area of live load is outside the practical range allowed in the software."

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
            flange_mm  = self._to_float(inputs.get(KEY_MP_GIRDER_TOP_FLANGE_WIDTH))
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

        # ── Camber ──────────────────────────────────────────────────────────────
        elif key == KEY_DO_CAMBER_VALUE:
            if inputs.get(KEY_DO_CAMBER_MODE) != "Custom":
                return None
            v = self._to_float(inputs.get(key))
            if v is None: return 0, "Camber must be a numeric value."
            if v < 0:     return 0, "Camber must be between 0 and 4 m."
            if v > 4:     return 4, "Camber must be between 0 and 4 m."

        # ═══DESIGN-OPTIONS-CONT-TAB-VALIDATORS-ENDS═══════════════════════════════════════════════════════


        return None

    # ==========================================================
    # PROJECT LOCATION VALIDATION (DDCL 2.1.x)
    # ==========================================================

    def validate_custom_weather_data(self, wind: str, zone: str, max_temp: str, min_temp: str) -> tuple:
        """
        Validate custom weather data inputs (wind speed, seismic zone,
        min/max shade air temperature).

        Returns (is_valid, error_message).
        ``is_valid`` is True when all checks pass; ``error_message`` is the
        user-facing description when validation fails.
        """
        if not wind or not max_temp or not min_temp or zone == "Select Zone":
            return False, "Please fill in all fields (Wind Speed, Seismic Zone, Min/Max Temperature)."

        try:
            wind_val = float(wind)
            max_val  = float(max_temp)
            min_val  = float(min_temp)
        except ValueError:
            return False, "Wind speed and temperature values must be numeric."

        if not 15.0 <= wind_val <= 100.0:
            return False, "Basic Wind Speed must be between 15.0 and 100.0 m/s."

        if not -50.0 <= min_val <= 40.0:
            return False, "Min Shade Air Temperature must be between -50.0 and 40.0 °C."

        if not 20.0 <= max_val <= 60.0:
            return False, "Max Shade Air Temperature must be between 20.0 and 60.0 °C."

        if max_val <= min_val:
            return False, f"Max temperature ({max_temp}°C) must be greater than Min temperature ({min_temp}°C)."

        return True, ""

    def validate_map_coordinates(self, lat: str, lon: str) -> tuple:
        """
        Validate map / coordinate inputs.

        Returns (is_valid, error_message).
        ``is_valid`` is True when both lat and lon are non-empty numerics.
        """
        if not lat or not lon:
            return False, "Please select a location on the map or enter latitude and longitude."

        try:
            float(lat)
            float(lon)
        except ValueError:
            return False, "Please enter valid numeric latitude and longitude values."

        return True, ""

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
