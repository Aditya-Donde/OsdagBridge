"""
OSI Input Validation (load-time)

When a user hand-edits a saved ``.osi`` file they can introduce values that the
application cannot use, e.g. ``geometry.span: abcd`` or a span outside the
software limits. Loading such a file silently leads to a failed/garbage design.

This module validates an OSI input dictionary *before* it is populated into the
UI, using the very same :class:`BridgeInputValidator` that the homepage and the
Additional Inputs dialog use for live editing. That keeps the load-time rules in
lock-step with the interactive rules.

Typical usage::

    from osdagbridge.core.utils.osi_validator import validate_osi_inputs

    result = validate_osi_inputs(data)
    if not result.is_valid:
        # show result.error_text() to the user and abort the load
        ...

The validator is intentionally tolerant about *structure*: it only flags values
it can actively prove are wrong, so any OSI file that the app itself saved will
always pass. ``test_Osi.py`` (in this same package) contains the broader
structure/completeness checks used for automated testing; this module is the
lean, user-facing gate wired into the Load Input action.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from osdagbridge.core.bridge_types.plate_girder.validator import BridgeInputValidator
from osdagbridge.core.utils.common import (
    KEY_SKEW_ANGLE, KEY_SPAN, KEY_CARRIAGEWAY_WIDTH,
    KEY_DESIGN_MODE,
    KEY_TS_GIRDER_SPACING, KEY_TS_NO_OF_GIRDERS, KEY_TS_DECK_OVERHANG,
    KEY_TS_DECK_THICKNESS, KEY_TS_FOOTPATH_WIDTH, KEY_TS_FOOTPATH_THICKNESS,
    KEY_CB_WIDTH, KEY_CB_HEIGHT, KEY_CB_LOAD, KEY_CB_POST_SPACING,
    KEY_MD_WIDTH, KEY_MD_HEIGHT, KEY_MD_LOAD, KEY_MD_POST_SPACING,
    KEY_RL_HEIGHT, KEY_RL_WIDTH, KEY_RL_LOAD_VALUE,
    KEY_WC_LD_LANE_TABLE_COUNT, KEY_PL_SELF_WEIGHT_FACTOR, KEY_LL_ECCENTRICITY,
    KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_SL_IMPORTANCE_FACTOR, KEY_SL_TIME_PERIOD, KEY_SL_DAMPING,
    KEY_SL_DEAD_LOAD_VALUE, KEY_SL_LIVE_LOAD_VALUE,
    KEY_WL_AVG_EXPOSED_HEIGHT, KEY_WL_GUST_FACTOR_VALUE, KEY_WL_DRAG_COEFF_VALUE,
    KEY_WL_DRAG_COEFF_LL_VALUE, KEY_WL_LIFT_COEFF_VALUE,
    KEY_WL_SUPER_AREA_ELEV_VALUE, KEY_WL_SUPER_AREA_PLAIN_VALUE,
    KEY_WL_EXPOSED_FRONTAL_VALUE,
    KEY_WL_WIND_ECC_DECK_VALUE, KEY_WL_WIND_LL_ECC_VALUE,
    KEY_TL_THERMAL_COEFF_STEEL, KEY_TL_THERMAL_COEFF_RCC,
    KEY_DS_TOP_CLEAR_COVER, KEY_DS_BOTTOM_CLEAR_COVER, KEY_DS_SIDE_CLEAR_COVER,
    KEY_DS_STUD_YIELD_STRENGTH, KEY_DS_STUD_ULTIMATE_STRENGTH,
    KEY_DS_STUD_HEIGHT, KEY_DS_STUD_COUNT, KEY_DS_STUD_TRANSVERSE_SPACING,
    KEY_DO_GAMMA_C_BASIC, KEY_DO_GAMMA_C_ACCIDENTAL, KEY_DO_GAMMA_M0,
    KEY_DO_GAMMA_M1, KEY_DO_GAMMA_S, KEY_DO_GAMMA_V, KEY_DO_GAMMA_FLT,
    KEY_DO_GAMMA_MF, KEY_DO_LOAD_CYCLES, KEY_DO_CAMBER_MODE, KEY_DO_CAMBER_VALUE,
)


@dataclass
class OsiValidationResult:
    """Outcome of validating an OSI input dictionary."""

    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    # key -> value the validator suggests instead of the rejected one.
    corrected_values: Dict[str, Any] = field(default_factory=dict)

    def error_text(self, limit: Optional[int] = None) -> str:
        """Return a human-readable, newline-separated list of errors."""
        errors = self.errors if limit is None else self.errors[:limit]
        lines = [f"• {msg}" for msg in errors]
        if limit is not None and len(self.errors) > limit:
            lines.append(f"… and {len(self.errors) - limit} more issue(s).")
        return "\n".join(lines)


# Fields validated through BridgeInputValidator.validate_basic_inputs.
_BASIC_KEYS = [
    KEY_SPAN,
    KEY_CARRIAGEWAY_WIDTH,
    KEY_SKEW_ANGLE,
]

# Fields validated through BridgeInputValidator.validate_additional_inputs.
_ADDITIONAL_KEYS = [
    KEY_TS_GIRDER_SPACING, KEY_TS_NO_OF_GIRDERS, KEY_TS_DECK_OVERHANG,
    KEY_TS_DECK_THICKNESS, KEY_TS_FOOTPATH_WIDTH, KEY_TS_FOOTPATH_THICKNESS,
    KEY_CB_WIDTH, KEY_CB_HEIGHT, KEY_CB_LOAD, KEY_CB_POST_SPACING,
    KEY_MD_WIDTH, KEY_MD_HEIGHT, KEY_MD_LOAD, KEY_MD_POST_SPACING,
    KEY_RL_HEIGHT, KEY_RL_WIDTH, KEY_RL_LOAD_VALUE,
    KEY_WC_LD_LANE_TABLE_COUNT, KEY_PL_SELF_WEIGHT_FACTOR, KEY_LL_ECCENTRICITY,
    KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_SL_IMPORTANCE_FACTOR, KEY_SL_TIME_PERIOD, KEY_SL_DAMPING,
    KEY_SL_DEAD_LOAD_VALUE, KEY_SL_LIVE_LOAD_VALUE,
    KEY_WL_AVG_EXPOSED_HEIGHT, KEY_WL_GUST_FACTOR_VALUE, KEY_WL_DRAG_COEFF_VALUE,
    KEY_WL_DRAG_COEFF_LL_VALUE, KEY_WL_LIFT_COEFF_VALUE,
    KEY_WL_SUPER_AREA_ELEV_VALUE, KEY_WL_SUPER_AREA_PLAIN_VALUE,
    KEY_WL_EXPOSED_FRONTAL_VALUE, KEY_WL_WIND_ECC_DECK_VALUE,
    KEY_WL_WIND_LL_ECC_VALUE,
    KEY_TL_THERMAL_COEFF_STEEL, KEY_TL_THERMAL_COEFF_RCC,
    KEY_DS_TOP_CLEAR_COVER, KEY_DS_BOTTOM_CLEAR_COVER, KEY_DS_SIDE_CLEAR_COVER,
    KEY_DS_STUD_YIELD_STRENGTH, KEY_DS_STUD_ULTIMATE_STRENGTH,
    KEY_DS_STUD_HEIGHT, KEY_DS_STUD_COUNT, KEY_DS_STUD_TRANSVERSE_SPACING,
    KEY_DO_GAMMA_C_BASIC, KEY_DO_GAMMA_C_ACCIDENTAL, KEY_DO_GAMMA_M0,
    KEY_DO_GAMMA_M1, KEY_DO_GAMMA_S, KEY_DO_GAMMA_V, KEY_DO_GAMMA_FLT,
    KEY_DO_GAMMA_MF, KEY_DO_LOAD_CYCLES, KEY_DO_CAMBER_MODE, KEY_DO_CAMBER_VALUE,
]

_VALID_DESIGN_MODES = {"Manual", "Optimized", "Standard", "Custom"}


class OsiInputValidator:
    """Validate OSI input values against the live bridge input rules."""

    def __init__(self) -> None:
        self._bridge_validator = BridgeInputValidator()

    # -- public API --------------------------------------------------------

    def validate(self, data: Dict[str, Any]) -> OsiValidationResult:
        """Validate a loaded OSI dictionary (flat or nested)."""
        result = OsiValidationResult()

        if not isinstance(data, dict) or not data:
            result.is_valid = False
            result.errors.append("File does not contain a valid input dictionary.")
            return result

        flat = self._flatten(data)

        # A null skew angle means "straight bridge" (0°); normalise so the
        # validator does not treat it as a non-numeric value.
        if self._is_missing(flat.get(KEY_SKEW_ANGLE)):
            flat[KEY_SKEW_ANGLE] = 0.0

        self._validate_design_mode(flat, result)

        for key in _BASIC_KEYS:
            if self._is_missing(flat.get(key)) and key != KEY_SKEW_ANGLE:
                # Missing basic inputs are not blocked here: the homepage will
                # surface them on Design. We only police *present* values so a
                # hand-edited garbage value cannot slip through.
                continue
            self._run(self._bridge_validator.validate_basic_inputs, key, flat, result)

        for key in _ADDITIONAL_KEYS:
            # Blank/unset additional inputs mean "not configured yet" — they are
            # optional refinements that the homepage validates at Design time.
            # Only police values that are actually present, so a hand-edited
            # garbage value is caught while an untouched field never blocks load.
            if self._is_missing(flat.get(key)):
                continue
            self._run(self._bridge_validator.validate_additional_inputs, key, flat, result)

        result.is_valid = len(result.errors) == 0
        return result

    # -- internals ---------------------------------------------------------

    def _run(self, validate_fn, key: str, flat: Dict[str, Any], result: OsiValidationResult) -> None:
        """Call a BridgeInputValidator method and record any error it returns."""
        try:
            validation_error = validate_fn(key, flat)
        except Exception as exc:  # defensive: a validator bug must not block load
            result.warnings.append(f"Could not validate '{key}': {exc}")
            return

        if validation_error is None:
            return

        corrected_value, message = validation_error
        result.errors.append(f"{self._label(key)}: {message}")
        result.corrected_values[key] = corrected_value

    def _validate_design_mode(self, flat: Dict[str, Any], result: OsiValidationResult) -> None:
        mode = flat.get(KEY_DESIGN_MODE)
        if mode and mode not in _VALID_DESIGN_MODES:
            result.errors.append(
                f"{self._label(KEY_DESIGN_MODE)}: '{mode}' is not a valid design mode "
                f"(expected one of {sorted(_VALID_DESIGN_MODES)})."
            )

    @staticmethod
    def _label(key: str) -> str:
        """Turn a dotted key into a friendlier label for error messages."""
        return key

    @staticmethod
    def _is_missing(value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, str) and value.strip() == "":
            return True
        return False

    def _flatten(self, data: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """Flatten nested OSI data into dot-separated keys.

        OSI files saved by this app already use flat dotted keys, but files may
        also be authored in nested YAML form; both must validate identically.
        Keys are treated literally and never split on '.'.
        """
        flat: Dict[str, Any] = {}
        for key, value in data.items():
            joined = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(value, dict):
                flat.update(self._flatten(value, joined))
            else:
                flat[joined] = value
        return flat


def validate_osi_inputs(data: Dict[str, Any]) -> OsiValidationResult:
    """Convenience wrapper: validate ``data`` and return the result."""
    return OsiInputValidator().validate(data)
