"""
Osdag Bridge Input Validators
Validates Basic and Additional Inputs
"""

from math import isclose

from osdagbridge.core.utils.codes.keyfile import *
from osdagbridge.core.utils.codes.irc5_2015 import IRC5_2015


class BridgeInputValidator:

    # ==========================================================
    # BASIC INPUT VALIDATION (DDCL 2.1.2)
    # ==========================================================

    def validate_basic_inputs(self, inputs: dict) -> dict:

        errors = {}
		
        span = self._to_float(inputs.get("span"))
        carriageway_width = self._to_float(inputs.get("carriageway_width"))
        median = inputs.get("median")
        footpath = inputs.get("footpath")
        skew_angle = self._to_float(inputs.get("skew_angle"))

		# ----------------------------------
		# Span (Software Scope Limit)
		# ----------------------------------
        if span is None or not (20 <= span <= 45):
            errors["span"] = "Span must be between 20 m and 45 m (software limitation)."
			
			
		# ----------------------------------
		# Carriageway Width (IRC 5 Cl.104.3.1)
		# ----------------------------------
        if carriageway_width is None:
            errors["carriageway_width"] = "Carriageway width must be specified."

        else:
			# Determine minimum lane assumption
            if median == "No":
                assumed_lanes = 1
            else:
                assumed_lanes = 2

            required_width = IRC5_2015.cl_104_3_1_carriageway_width(
				carriageway_width,
				assumed_lanes
			)

            if carriageway_width < required_width:
                errors["carriageway_width"] = (
					f"Minimum carriageway width required is "
					f"{required_width:.2f} m as per IRC 5:2015 Clause 104.3.1."
				)

			# Software upper limit
            if carriageway_width > 23.6:
                errors["carriageway_width"] = (
					"Carriageway width exceeds 23.6 m (software limitation)."
				)


        # ----------------------------
        # Skew Angle (IRC 24 via keyfile)
        # ----------------------------
        if skew_angle is not None:
            if not (SKEW_ANGLE_MIN <= skew_angle <= SKEW_ANGLE_MAX):
                errors["skew_angle"] = (
                    f"Skew angle must be between "
                    f"{SKEW_ANGLE_MIN}° and {SKEW_ANGLE_MAX}°."
                )

        return self._format_response(errors)
		

    # ==========================================================
    # ADDITIONAL INPUT VALIDATION (DDCL 2.1.3)
    # ==========================================================

    def validate_additional_inputs(self, inputs: dict) -> dict:

        errors = {}

        overall_width = self._to_float(inputs.get("overall_bridge_width"))
        girder_spacing = self._to_float(inputs.get("girder_spacing"))
        overhang = self._to_float(inputs.get("deck_overhang"))
        no_girders = self._to_int(inputs.get("no_of_girders"))

        # ----------------------------
        # Layout Equation Check
        # ----------------------------
        if all(v is not None for v in
               [overall_width, girder_spacing, overhang, no_girders]):

            lhs = (no_girders - 1) * girder_spacing + 2 * overhang

            if not isclose(lhs, overall_width, rel_tol=1e-2):
                errors["layout_equation"] = (
                    "Layout must satisfy: "
                    "Overall Width = (No. of Girders − 1) × Spacing + 2 × Overhang."
                )

        # ----------------------------
        # Safety Kerb Check (IRC 5 Cl.101.41)
        # ----------------------------
        kerb_width = self._to_float(inputs.get("kerb_width"))
        footpath = inputs.get("footpath")

        if kerb_width is not None:

            kerb_result = IRC5_2015.cl_101_41_safety_kerb_width(
                kerb_width,
                footpath
            )

            if kerb_result["applicable"] and not kerb_result["is_compliant"]:
                errors["kerb_width"] = kerb_result["remarks"]
		
		# ----------------------------
        # Footpath Width (IRC 5 Cl.104.3.6)
        # ----------------------------
        footpath_width = self._to_float(inputs.get("footpath_width"))

        result = IRC5_2015.cl_104_3_6_footpath_width(
            footpath,
            footpath_width
        )

        if result["applicable"] and not result["is_compliant"]:
            errors["footpath_width"] = result["remarks"]
		
        # ----------------------------
        # Railing Height (IRC 5 Cl.109.7.2)
        # ----------------------------
        railing_height = self._to_float(inputs.get("railing_height"))

        if railing_height is not None and footpath in KEY_FOOTPATH:
            if railing_height < KEY_RAILING_MIN_HEIGHT[0]:
                errors["railing_height"] = (
                    f"Minimum railing height is "
                    f"{KEY_RAILING_MIN_HEIGHT[0]} mm."
                )

        # ----------------------------
        # Stud Detailing (Keyfile constants)
        # ----------------------------
        stud_height = self._to_float(inputs.get("stud_height"))
        stud_diameter = self._to_float(inputs.get("stud_diameter"))
        flange_thickness = self._to_float(inputs.get("top_flange_thickness"))

        if stud_height is not None:
            if stud_height < MIN_STUD_HEIGHT_MM:
                errors["stud_height"] = (
                    f"Minimum stud height must be "
                    f"{MIN_STUD_HEIGHT_MM} mm."
                )

        if stud_diameter and flange_thickness:
            if stud_diameter > MAX_STUD_DIAMETER_FACTOR * flange_thickness:
                errors["stud_diameter"] = (
                    "Stud diameter exceeds permitted proportion of flange thickness."
                )

        # ----------------------------
        # Edge Distance
        # ----------------------------
        edge_distance = self._to_float(inputs.get("stud_edge_distance"))

        if edge_distance is not None:
            if edge_distance < MIN_EDGE_DISTANCE_MM:
                errors["stud_edge_distance"] = (
                    f"Minimum edge distance must be "
                    f"{MIN_EDGE_DISTANCE_MM} mm."
                )

        return self._format_response(errors)

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
