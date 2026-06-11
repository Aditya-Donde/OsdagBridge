"""
OSI File Validation Tests

Tests validate OSI (YAML configuration) files for:
1. Data Correctness - Values are within valid ranges and constraints
2. Data Completeness - All required fields are present
3. Structure Integrity - Correct hierarchy and key naming conventions
"""

import pytest
import yaml
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

from osdagbridge.core.bridge_types.plate_girder.validator import BridgeInputValidator
from osdagbridge.core.utils.common import (
    KEY_STRUCTURE_TYPE, KEY_PROJECT_LOCATION, KEY_SPAN, KEY_CARRIAGEWAY_WIDTH,
    KEY_INCLUDE_MEDIAN, KEY_SKEW_ANGLE, KEY_FOOTPATH, KEY_DESIGN_MODE,
    KEY_GIRDER, KEY_CROSS_BRACING, KEY_END_DIAPHRAGM,
    KEY_DECK_CONCRETE_GRADE_BASIC, KEY_TS_GIRDER_SPACING,
    KEY_TS_NO_OF_GIRDERS, KEY_TS_DECK_OVERHANG, KEY_TS_OVERALL_WIDTH,
    KEY_TS_DECK_THICKNESS, KEY_TS_FOOTPATH_WIDTH, KEY_TS_FOOTPATH_THICKNESS,
    KEY_CB_WIDTH, KEY_CB_HEIGHT, KEY_CB_LOAD, KEY_CB_POST_SPACING,
    KEY_MD_WIDTH, KEY_MD_HEIGHT, KEY_MD_LOAD, KEY_MD_POST_SPACING,
    KEY_RL_HEIGHT, KEY_RL_WIDTH, KEY_RL_LOAD_VALUE, KEY_WC_DENSITY,
    KEY_WC_THICKNESS, KEY_WC_LD_LANE_TABLE_COUNT, KEY_WC_LD_LANE_TABLE,
    KEY_PL_SELF_WEIGHT_FACTOR, KEY_LL_ECCENTRICITY,
    KEY_LL_FOOTPATH_PRESSURE_MODE, KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_SL_IMPORTANCE_FACTOR, KEY_SL_TIME_PERIOD, KEY_SL_DAMPING,
    KEY_SL_DEAD_LOAD_MODE, KEY_SL_DEAD_LOAD_VALUE, KEY_SL_LIVE_LOAD_MODE,
    KEY_SL_LIVE_LOAD_VALUE, KEY_WL_AVG_EXPOSED_HEIGHT,
    KEY_WL_GUST_FACTOR_MODE, KEY_WL_GUST_FACTOR_VALUE,
    KEY_WL_DRAG_COEFF_MODE, KEY_WL_DRAG_COEFF_VALUE,
    KEY_WL_DRAG_COEFF_LL_MODE, KEY_WL_DRAG_COEFF_LL_VALUE,
    KEY_WL_LIFT_COEFF_MODE, KEY_WL_LIFT_COEFF_VALUE,
    KEY_WL_SUPER_AREA_ELEV_MODE, KEY_WL_SUPER_AREA_ELEV_VALUE,
    KEY_WL_SUPER_AREA_PLAIN_MODE, KEY_WL_SUPER_AREA_PLAIN_VALUE,
    KEY_WL_EXPOSED_FRONTAL_MODE, KEY_WL_EXPOSED_FRONTAL_VALUE,
    KEY_WL_WIND_ECC_DECK_MODE, KEY_WL_WIND_ECC_DECK_VALUE,
    KEY_WL_WIND_LL_ECC_MODE, KEY_WL_WIND_LL_ECC_VALUE,
    KEY_TL_THERMAL_COEFF_STEEL, KEY_TL_THERMAL_COEFF_RCC,
    KEY_DS_REINF_BOUNDS, KEY_DS_TOP_CLEAR_COVER,
    KEY_DS_BOTTOM_CLEAR_COVER, KEY_DS_SIDE_CLEAR_COVER,
    KEY_DS_STUD_YIELD_STRENGTH, KEY_DS_STUD_ULTIMATE_STRENGTH,
    KEY_DS_STUD_DIAMETER, KEY_DS_STUD_HEIGHT, KEY_DS_STUD_COUNT,
    KEY_DS_STUD_TRANSVERSE_SPACING, KEY_DO_GAMMA_C_BASIC,
    KEY_DO_GAMMA_C_ACCIDENTAL, KEY_DO_GAMMA_M0, KEY_DO_GAMMA_M1,
    KEY_DO_GAMMA_S, KEY_DO_GAMMA_V, KEY_DO_GAMMA_FLT, KEY_DO_GAMMA_MF,
    KEY_DO_LOAD_CYCLES, KEY_DO_DEFLECTION_LIMIT,
    KEY_MP_GIRDER_TOP_FLANGE_WIDTH,
)

class OSIValidator:
    """
    Comprehensive OSI file validator that checks correctness, completeness,
    and structure of OSI YAML configuration files.
    """

    # =========================================================================
    # REQUIRED FIELD DEFINITIONS
    # =========================================================================
    
    REQUIRED_TOP_LEVEL_KEYS = {
        'geometry',
        'material',
        'member_properties',
        'design_options',
        'design_options_cont',
        'loading',
        'typical_section',
        'support_conditions',
        'structure',
        'project'
    }

    REQUIRED_GEOMETRY_KEYS = {
        'span',
        'carriageway_width',
        'include_median',
        'design_mode',
        'footpath'
    }

    REQUIRED_LOADING_KEYS = {
        'permanent_load',
        'live_load',
        'seismic_load',
        'wind_load',
        'temperature_load'
    }

    REQUIRED_DESIGN_OPTIONS_KEYS = {
        'construction',
        'deck',
        'shear_studs'
    }

    REQUIRED_MATERIAL_KEYS = {
        'girder',
        'deck',
        'cross_bracing',
        'end_diaphragm'
    }

    # NOTE:
    # `examples`/tests use a simplified OSI structure under:
    # member_properties.cross_bracing_details
    # (e.g. {"type": {"G1G2": {"B1M1": "K-bracing"}}}).
    # The validator must not require a full expanded subsection schema,
    # otherwise even valid/simple OSI files fail.
    REQUIRED_MEMBER_PROPERTIES_SUBSECTIONS = {
        'cross_bracing_details': [
            'type',
        ]
    }

    # =========================================================================
    # VALIDATION RANGE DEFINITIONS (From validator.py)
    # =========================================================================
    
    VALIDATION_RANGES = {
        'geometry.span': (10, 100),
        'geometry.carriageway_width': (3, 30),
        'geometry.skew_angle': (0, 45),
        'design_options.deck.top_clear_cover': (20, 100),
        'design_options.deck.bottom_clear_cover': (20, 100),
        'design_options.deck.side_clear_cover': (20, 100),
        'design_options.shear_studs.diameter': (10, 30),
        'design_options.shear_studs.height': (50, 300),
        'design_options.shear_studs.count': (1, 10),
        'design_options.shear_studs.transverse_spacing': (50, 300),
        'loading.live_load.eccentricity': (-10, 10),
        'typical_section.deck_thickness': (100, 500),
        'typical_section.footpath_thickness': (100, 500),
        'typical_section.girder_spacing': (0.5, 10),
        'typical_section.no_of_girders': (2, 8),
        'typical_section.deck_overhang': (0, 5),
    }

    VALIDATION_PATTERNS = {
        'material.girder': r'^(E 250|E 350|E 450|E 550|M40|M50|Fe 415|Fe 500)',
        'material.deck': r'^(M30|M40|M50|M60)',
    }

    OPTIONAL_EMPTY_LIST_PATHS = {
        'loading.live_load.custom_vehicles',
        'loading.load_combination.combinations',
    }

    BASIC_VALIDATOR_KEYS = [
        KEY_SPAN,
        KEY_CARRIAGEWAY_WIDTH,
        KEY_SKEW_ANGLE,
    ]

    REQUIRED_BRIDGE_INPUT_KEYS = [
        KEY_STRUCTURE_TYPE,
        # KEY_PROJECT_LOCATION is intentionally excluded: in the OSI file it is a
        # *nested* dict (with sub-keys data/method/weather_data), so the flat
        # representation never produces a leaf named "project.location" and the
        # presence check would always fail on valid files.
        KEY_SPAN,
        KEY_CARRIAGEWAY_WIDTH,
        KEY_INCLUDE_MEDIAN,
        # KEY_SKEW_ANGLE is intentionally excluded from the *required* list because
        # null is a valid representation of "no skew" (straight bridge). The value
        # is instead normalised to 0.0 before being passed to the bridge validator.
        KEY_FOOTPATH,
        KEY_DESIGN_MODE,
        KEY_GIRDER,
        KEY_CROSS_BRACING,
        KEY_END_DIAPHRAGM,
        KEY_DECK_CONCRETE_GRADE_BASIC,
    ]

    ADDITIONAL_VALIDATOR_KEYS = [
        KEY_TS_GIRDER_SPACING,
        KEY_TS_NO_OF_GIRDERS,
        KEY_TS_DECK_OVERHANG,
        KEY_TS_DECK_THICKNESS,
        KEY_TS_FOOTPATH_WIDTH,
        KEY_TS_FOOTPATH_THICKNESS,
        KEY_CB_WIDTH,
        KEY_CB_HEIGHT,
        KEY_CB_LOAD,
        KEY_CB_POST_SPACING,
        KEY_MD_WIDTH,
        KEY_MD_HEIGHT,
        KEY_MD_LOAD,
        KEY_MD_POST_SPACING,
        KEY_RL_HEIGHT,
        KEY_RL_WIDTH,
        KEY_RL_LOAD_VALUE,
        # KEY_WC_DENSITY and KEY_WC_THICKNESS are intentionally excluded here.
        # The OSI file stores density in kN/m³ (e.g. 24.0) and thickness in mm
        # (e.g. 50.0), but BridgeInputValidator expects density ≤ 10.0 (t/m³ or
        # similar) and thickness in metres (≤ 10.0 m). Passing the raw OSI values
        # would always trigger false out-of-range errors. They are validated
        # separately in _validate_wearing_course_with_units() below.
        KEY_WC_LD_LANE_TABLE_COUNT,
        KEY_WC_LD_LANE_TABLE,
        KEY_PL_SELF_WEIGHT_FACTOR,
        KEY_LL_ECCENTRICITY,
        KEY_LL_FOOTPATH_PRESSURE_VALUE,
        KEY_SL_IMPORTANCE_FACTOR,
        KEY_SL_TIME_PERIOD,
        KEY_SL_DAMPING,
        KEY_SL_DEAD_LOAD_VALUE,
        KEY_SL_LIVE_LOAD_VALUE,
        KEY_WL_AVG_EXPOSED_HEIGHT,
        KEY_WL_GUST_FACTOR_VALUE,
        KEY_WL_DRAG_COEFF_VALUE,
        KEY_WL_DRAG_COEFF_LL_VALUE,
        KEY_WL_LIFT_COEFF_VALUE,
        KEY_WL_SUPER_AREA_ELEV_VALUE,
        KEY_WL_SUPER_AREA_PLAIN_VALUE,
        KEY_WL_EXPOSED_FRONTAL_VALUE,
        KEY_WL_WIND_ECC_DECK_VALUE,
        KEY_WL_WIND_LL_ECC_VALUE,
        KEY_TL_THERMAL_COEFF_STEEL,
        KEY_TL_THERMAL_COEFF_RCC,
        KEY_DS_REINF_BOUNDS,
        KEY_DS_TOP_CLEAR_COVER,
        KEY_DS_BOTTOM_CLEAR_COVER,
        KEY_DS_SIDE_CLEAR_COVER,
        KEY_DS_STUD_YIELD_STRENGTH,
        KEY_DS_STUD_ULTIMATE_STRENGTH,
        KEY_DS_STUD_HEIGHT,
        KEY_DS_STUD_COUNT,
        KEY_DS_STUD_TRANSVERSE_SPACING,
        KEY_DO_GAMMA_C_BASIC,
        KEY_DO_GAMMA_C_ACCIDENTAL,
        KEY_DO_GAMMA_M0,
        KEY_DO_GAMMA_M1,
        KEY_DO_GAMMA_S,
        KEY_DO_GAMMA_V,
        KEY_DO_GAMMA_FLT,
        KEY_DO_GAMMA_MF,
        KEY_DO_LOAD_CYCLES,
        KEY_DO_DEFLECTION_LIMIT,
    ]

    # OSI unit → validator unit conversion factors for wearing course fields.
    # OSI stores density in kN/m³ and thickness in mm; the bridge validator
    # uses density in t/m³ (≤ 10) and thickness in metres (≤ 10).
    _WC_UNIT_CONVERSIONS = {
        KEY_WC_DENSITY:   1.0 / 9.81,   # kN/m³ → t/m³  (approx: 24 kN/m³ ≈ 2.45 t/m³)
        KEY_WC_THICKNESS: 1.0 / 1000.0, # mm    → m     (50 mm → 0.05 m)
    }

    VALIDATOR_DEPENDENCY_KEYS = [
        KEY_TS_OVERALL_WIDTH,
        KEY_CARRIAGEWAY_WIDTH,
        KEY_SPAN,
        KEY_FOOTPATH,
        KEY_LL_FOOTPATH_PRESSURE_MODE,
        KEY_SL_DEAD_LOAD_MODE,
        KEY_SL_LIVE_LOAD_MODE,
        KEY_WL_GUST_FACTOR_MODE,
        KEY_WL_DRAG_COEFF_MODE,
        KEY_WL_DRAG_COEFF_LL_MODE,
        KEY_WL_LIFT_COEFF_MODE,
        KEY_WL_SUPER_AREA_ELEV_MODE,
        KEY_WL_SUPER_AREA_PLAIN_MODE,
        KEY_WL_EXPOSED_FRONTAL_MODE,
        KEY_DS_STUD_DIAMETER,
        KEY_TS_DECK_THICKNESS,
        KEY_MP_GIRDER_TOP_FLANGE_WIDTH,
        KEY_DS_STUD_COUNT,
    ]

    # =========================================================================
    # VALIDATION METHODS
    # =========================================================================

    def validate_osi_file(self, file_path: str) -> Dict[str, Any]:
        """
        Main validation entry point. Performs all checks on the OSI file.
        
        Returns:
            Dict with keys:
                - is_valid: bool
                - errors: List[str]
                - warnings: List[str]
                - completeness_score: float (0-100)
                - structure_issues: List[str]
        """
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'completeness_score': 100,
            'structure_issues': [],
            'corrected_values': {}
        }

        try:
            # Load YAML file
            data = self._load_yaml(file_path)
            if data is None:
                result['is_valid'] = False
                result['errors'].append("Failed to load YAML file. Check syntax.")
                return result
        except Exception as e:
            result['is_valid'] = False
            result['errors'].append(f"YAML parsing error: {str(e)}")
            return result

        # Run all validation checks
        self._check_structure(data, result)
        self._check_completeness(data, result)
        self._check_correctness(data, result)
        self._validate_against_plate_girder_validator(data, result)

        result['is_valid'] = len(result['errors']) == 0
        return result

    def _load_yaml(self, file_path: str) -> Optional[Dict]:
        """Load and parse YAML file, converting flat format to nested if needed."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # Check if file is in flat key-value format (e.g., "design_options.construction.stage")
            if isinstance(data, dict) and data and all(isinstance(k, str) and '.' in k for k in data.keys()):
                # Convert flat format to nested
                nested_data = {}
                for flat_key, value in data.items():
                    keys = flat_key.split('.')
                    current = nested_data
                    for i, key in enumerate(keys[:-1]):
                        if key not in current:
                            current[key] = {}
                        elif not isinstance(current[key], dict):
                            # Path conflict: value already exists, skip
                            break
                        current = current[key]
                    else:
                        # Only set value if we didn't break out of the loop
                        current[keys[-1]] = value
                return nested_data
            
            return data
        except yaml.YAMLError as e:
            raise ValueError(f"YAML syntax error: {e}")
        except FileNotFoundError:
            raise FileNotFoundError(f"OSI file not found: {file_path}")

    # =========================================================================
    # STRUCTURE VALIDATION
    # =========================================================================

    def _check_structure(self, data: Dict, result: Dict) -> None:
        """
        Validate YAML structure:
        - Proper hierarchy
        - Correct key naming conventions
        - Valid nesting levels
        """
        if not isinstance(data, dict):
            result['errors'].append("Root element must be a dictionary (YAML mapping).")
            result['is_valid'] = False
            return

        # Check for duplicate keys at top level
        self._validate_no_duplicates(data, result, "top-level")

        # Check key naming conventions (should be snake_case) - recursive
        self._check_naming_conventions(data, result, "")

        # Validate nested structure integrity
        self._validate_nested_structure(data, result)

    def _validate_no_duplicates(self, obj: Any, result: Dict, context: str) -> None:
        """Check for duplicate keys in dictionaries."""
        if not isinstance(obj, dict):
            return
        # Note: Python dicts inherently prevent duplicates, but we check YAML parsing
        for key, value in obj.items():
            if isinstance(value, dict):
                self._validate_no_duplicates(value, result, f"{context}.{key}")

    def _check_naming_conventions(self, obj: Any, result: Dict, path: str) -> None:
        """Recursively check all keys for snake_case naming convention.
        
        Skips structural identifiers (girder IDs like G1, member IDs like B1M1, etc.)
        which legitimately contain uppercase letters.
        """
        # Paths where uppercase identifiers are allowed (girders, members, etc.)
        IDENTIFIER_PATHS = {
            'member_properties.girder_details.select_girder',
            'member_properties.girder_details.section_input',
            'member_properties.girder_details.section_properties',
            'member_properties.girder_details.material_properties',
            'member_properties.girder_details',
            'member_properties.stiffener_details.select_member_id',
            'member_properties.stiffener_details.design_method',
            'member_properties.stiffener_details',
            'member_properties.member_id',
            'member_properties.cross_bracing_details',
            'member_properties.end_diaphragm_details',
        }
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                
                # Check if this path is in identifier zone
                is_identifier_zone = any(current_path.startswith(id_path) for id_path in IDENTIFIER_PATHS)
                
                # Only check naming if NOT in identifier zone
                if not is_identifier_zone and not self._is_valid_key_name(key):
                    result['structure_issues'].append(
                        f"Key '{current_path}' should follow snake_case naming convention (no uppercase letters)."
                    )
                
                self._check_naming_conventions(value, result, current_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                current_path = f"{path}[{i}]"
                self._check_naming_conventions(item, result, current_path)

    def _is_valid_key_name(self, key: str) -> bool:
        """Validate key follows snake_case convention."""
        if not isinstance(key, str):
            return False
        # Valid snake_case: only lowercase letters, digits, underscores, and dots
        for char in key:
            if char.isupper():
                return False
        return True

    def _validate_nested_structure(self, data: Dict, result: Dict, path: str = "") -> None:
        """
        Recursively validate nested structure for:
        - Consistent indentation (YAML constraint)
        - Valid nesting depth (warn if >10 levels)
        - Null values in required contexts
        """
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key

            if isinstance(value, dict):
                # Check nesting depth
                depth = len(current_path.split('.'))
                if depth > 10:
                    result['warnings'].append(
                        f"Deep nesting at '{current_path}' (depth: {depth}). "
                        "Consider flattening structure."
                    )
                self._validate_nested_structure(value, result, current_path)

            elif isinstance(value, list):
                # Validate list structure
                if len(value) == 0 and current_path not in self.OPTIONAL_EMPTY_LIST_PATHS:
                    result['warnings'].append(f"Empty list at '{current_path}'.")
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        self._validate_nested_structure(item, result, f"{current_path}[{i}]")

    # =========================================================================
    # COMPLETENESS VALIDATION
    # =========================================================================

    def _check_completeness(self, data: Dict, result: Dict) -> None:
        """
        Validate all required fields are present.
        Calculate completeness score based on actual leaf fields vs expected.
        """
        missing_keys = []
        
        # Check top-level keys
        for key in self.REQUIRED_TOP_LEVEL_KEYS:
            if key not in data:
                missing_keys.append(f"Top-level: '{key}'")
                result['errors'].append(f"Missing required top-level key: '{key}'")

        # Check nested required keys
        if 'geometry' in data and isinstance(data['geometry'], dict):
            for key in self.REQUIRED_GEOMETRY_KEYS:
                if key not in data['geometry']:
                    missing_keys.append(f"geometry.{key}")

        if 'loading' in data and isinstance(data['loading'], dict):
            for key in self.REQUIRED_LOADING_KEYS:
                if key not in data['loading']:
                    missing_keys.append(f"loading.{key}")

        if 'design_options' in data and isinstance(data['design_options'], dict):
            for key in self.REQUIRED_DESIGN_OPTIONS_KEYS:
                if key not in data['design_options']:
                    missing_keys.append(f"design_options.{key}")

        if 'material' in data and isinstance(data['material'], dict):
            for key in self.REQUIRED_MATERIAL_KEYS:
                if key not in data['material']:
                    missing_keys.append(f"material.{key}")

        # NEW: Check member_properties subsections completeness
        member_props_missing = self._check_member_properties_completeness(data)
        missing_keys.extend(member_props_missing)
        
        # Count actual leaf fields (values, not containers)
        actual_fields = self._count_leaf_fields(data)
        
        # Calculate completeness score
        expected_top_level = (
            len(self.REQUIRED_TOP_LEVEL_KEYS) +
            len(self.REQUIRED_GEOMETRY_KEYS) +
            len(self.REQUIRED_LOADING_KEYS) +
            len(self.REQUIRED_DESIGN_OPTIONS_KEYS) +
            len(self.REQUIRED_MATERIAL_KEYS)
        )
        
        # For scoring: use both missing required keys and count of actual leaf fields
        # If there are many more actual fields than expected, normalize based on leaf count
        missing_count = len(missing_keys)
        
        # Score based on: (actual_fields - errors) / actual_fields
        if actual_fields > 0:
            score = max(0, ((actual_fields - missing_count) / actual_fields) * 100)
        else:
            score = max(0, ((expected_top_level - missing_count) / expected_top_level) * 100)
        
        result['completeness_score'] = score

        if missing_keys:
            result['errors'].extend([f"Missing field: {k}" for k in missing_keys])

    def _is_missing_value(self, value: Any) -> bool:
        """Return True for values that cannot be used as required inputs."""
        if value is None:
            return True
        if isinstance(value, str) and value.strip() == "":
            return True
        return False

    def _count_leaf_fields(self, obj: Any, path: str = "") -> int:

        """
        Recursively count all leaf fields (actual values, not containers).
        Used to determine expected field count for completeness scoring.
        """
        count = 0
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                if isinstance(value, dict):
                    count += self._count_leaf_fields(value, current_path)
                elif isinstance(value, list):
                    # Count list as 1 field, then count items inside
                    count += 1
                    for item in value:
                        if isinstance(item, dict):
                            count += self._count_leaf_fields(item, current_path)
                        else:
                            count += 1
                else:
                    # Leaf value
                    count += 1
        elif isinstance(obj, list):
            for item in obj:
                count += self._count_leaf_fields(item, path)
        else:
            count += 1
        return count

    def _check_member_properties_completeness(self, data: Dict) -> List[str]:
        """
        Validate that member_properties contains expected subsections.
        Returns list of missing fields.
        """
        missing = []
        
        if 'member_properties' not in data:
            return missing
        
        mp = data.get('member_properties', {})
        if not isinstance(mp, dict):
            return missing
        
        # Check cross_bracing_details subsections
        if 'cross_bracing_details' in mp:
            cbd = mp['cross_bracing_details']
            if isinstance(cbd, dict):
                expected_members_by_pair = self._expected_cross_bracing_members(cbd)
                for required_subsection in self.REQUIRED_MEMBER_PROPERTIES_SUBSECTIONS.get('cross_bracing_details', []):
                    if required_subsection not in cbd:
                        missing.append(f"member_properties.cross_bracing_details.{required_subsection}")
                    else:
                        subsection_data = cbd[required_subsection]
                        if isinstance(subsection_data, dict):
                            subsection_missing = self._validate_subsection_consistency(
                                subsection_data,
                                f"member_properties.cross_bracing_details.{required_subsection}",
                                expected_members_by_pair,
                            )
                            missing.extend(subsection_missing)
        
        return missing

    def _expected_cross_bracing_members(self, cross_bracing_details: Dict) -> Dict[str, set]:
        """
        Build expected member IDs per girder pair.

        Member IDs legitimately differ by girder pair, for example G1G2 uses
        B1M* while G2G3 uses B2M*. Do not use one girder pair as the template
        for another; that creates hundreds of false "missing B1M*" errors.
        """
        member_id_section = cross_bracing_details.get("member_id")
        if isinstance(member_id_section, dict) and member_id_section:
            return {
                pair: set(members.keys())
                for pair, members in member_id_section.items()
                if isinstance(members, dict)
            }

        expected = {}
        for subsection in cross_bracing_details.values():
            if not isinstance(subsection, dict):
                continue
            for pair, members in subsection.items():
                if isinstance(members, dict):
                    expected.setdefault(pair, set()).update(members.keys())
        return expected

    def _validate_subsection_consistency(
        self,
        subsection: Dict,
        base_path: str,
        expected_members_by_pair: Dict[str, set],
    ) -> List[str]:
        """
        Validate that each subsection contains the expected members for each
        girder pair, without comparing member names across different pairs.
        """
        missing = []
        
        if not isinstance(subsection, dict) or not subsection:
            return missing

        for girder_pair, expected_members in expected_members_by_pair.items():
            members = subsection.get(girder_pair)
            if members is None:
                missing.append(f"{base_path}.{girder_pair}")
                continue
            if not isinstance(members, dict):
                continue

            for missing_member in sorted(expected_members - set(members.keys())):
                missing.append(f"{base_path}.{girder_pair}.{missing_member}")
        
        return missing


    # =========================================================================
    # CORRECTNESS VALIDATION
    # =========================================================================

    def _check_correctness(self, data: Dict, result: Dict) -> None:
        """
        Validate data correctness:
        - Value ranges
        - Data types
        - Cross-field constraints
        - Material codes validity
        """
        self._validate_value_ranges(data, result)
        self._validate_data_types(data, result)
        self._validate_material_codes(data, result)
        self._validate_cross_field_constraints(data, result)

    def _validate_value_ranges(self, data: Dict, result: Dict) -> None:
        """Validate numeric values are within specified ranges."""
        self._check_ranges_recursive(data, result, "")

    def _check_ranges_recursive(self, obj: Any, result: Dict, path: str) -> None:
        """Recursively check value ranges."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                self._check_ranges_recursive(value, result, current_path)

        else:
            if path in self.VALIDATION_RANGES:
                if self._is_missing_value(obj):
                    return
                obj = self._to_float(obj)
                if obj is None:
                    result['errors'].append(
                        f"Value at '{path}' must be numeric."
                    )
                    return
                min_val, max_val = self.VALIDATION_RANGES[path]
                if not (min_val <= obj <= max_val):
                    result['errors'].append(
                        f"Value at '{path}' is {obj}, but must be between {min_val} and {max_val}."
                    )
                    result['corrected_values'][path] = max(min_val, min(obj, max_val))

    def _validate_against_plate_girder_validator(self, data: Dict, result: Dict) -> None:
        """Validate OSI values using the same validator used by PlateGirderBridge."""
        flat_inputs = self._flatten_osi_data(data)

        # Normalise skew_angle: null means "straight bridge" (0°), which is valid.
        # We substitute 0.0 so the bridge validator does not see a None value and
        # mistakenly report it as a missing required input.
        if KEY_SKEW_ANGLE in flat_inputs and flat_inputs[KEY_SKEW_ANGLE] is None:
            flat_inputs[KEY_SKEW_ANGLE] = 0.0

        bridge_validator = BridgeInputValidator()

        for key in self.REQUIRED_BRIDGE_INPUT_KEYS:
            if key not in flat_inputs or self._is_missing_value(flat_inputs.get(key)):
                self._record_missing_bridge_input(key, bridge_validator, flat_inputs, result)

        # Always validate skew_angle (use 0.0 when absent/null — straight bridge).
        skew_inputs = dict(flat_inputs)
        if self._is_missing_value(skew_inputs.get(KEY_SKEW_ANGLE)):
            skew_inputs[KEY_SKEW_ANGLE] = 0.0
        validation_error = bridge_validator.validate_basic_inputs(KEY_SKEW_ANGLE, skew_inputs)
        self._record_bridge_validation_error(KEY_SKEW_ANGLE, validation_error, result)

        for key in self.BASIC_VALIDATOR_KEYS:
            if key == KEY_SKEW_ANGLE:
                continue  # Already handled above with null→0 normalisation.
            if key not in flat_inputs or self._is_missing_value(flat_inputs.get(key)):
                continue
            validation_error = bridge_validator.validate_basic_inputs(key, flat_inputs)
            self._record_bridge_validation_error(key, validation_error, result)

        for key in self.ADDITIONAL_VALIDATOR_KEYS:
            if key not in flat_inputs:
                continue
            if self._should_skip_inactive_additional_key(key, flat_inputs):
                continue
            validation_error = bridge_validator.validate_additional_inputs(key, flat_inputs)
            self._record_bridge_validation_error(key, validation_error, result)

        # Validate wearing course fields with unit conversion applied first.
        self._validate_wearing_course_with_units(flat_inputs, bridge_validator, result)

    def _validate_wearing_course_with_units(
        self,
        flat_inputs: Dict[str, Any],
        bridge_validator: BridgeInputValidator,
        result: Dict,
    ) -> None:
        """Validate wearing course density and thickness after converting OSI units.

        The OSI file stores:
          - density  in kN/m³  (e.g. 24.0)  → validator expects t/m³  (≤ 10.0)
          - thickness in mm    (e.g. 50.0)  → validator expects metres (≤ 10.0)

        We build a shallow copy of flat_inputs with the converted values so that
        the bridge validator sees numbers in its expected unit system.
        """
        for key, factor in self._WC_UNIT_CONVERSIONS.items():
            if key not in flat_inputs:
                continue
            raw = flat_inputs.get(key)
            if self._is_missing_value(raw):
                continue
            converted = self._to_float(raw)
            if converted is None:
                result['errors'].append(
                    f"Value at '{key}' must be numeric (got {raw!r})."
                )
                continue
            converted_inputs = dict(flat_inputs)
            converted_inputs[key] = converted * factor
            validation_error = bridge_validator.validate_additional_inputs(key, converted_inputs)
            self._record_bridge_validation_error(key, validation_error, result)

    def _should_skip_inactive_additional_key(self, key: str, flat_inputs: Dict[str, Any]) -> bool:
        """Skip blank values for controls that are inactive in the current OSI."""
        if not self._is_missing_value(flat_inputs.get(key)):
            return False

        median_keys = {
            KEY_MD_WIDTH,
            KEY_MD_HEIGHT,
            KEY_MD_LOAD,
            KEY_MD_POST_SPACING,
        }
        if key in median_keys and flat_inputs.get(KEY_INCLUDE_MEDIAN) != "Yes":
            return True

        custom_value_modes = {
            KEY_LL_FOOTPATH_PRESSURE_VALUE: KEY_LL_FOOTPATH_PRESSURE_MODE,
            KEY_SL_DEAD_LOAD_VALUE: KEY_SL_DEAD_LOAD_MODE,
            KEY_SL_LIVE_LOAD_VALUE: KEY_SL_LIVE_LOAD_MODE,
            KEY_WL_GUST_FACTOR_VALUE: KEY_WL_GUST_FACTOR_MODE,
            KEY_WL_DRAG_COEFF_VALUE: KEY_WL_DRAG_COEFF_MODE,
            KEY_WL_DRAG_COEFF_LL_VALUE: KEY_WL_DRAG_COEFF_LL_MODE,
            KEY_WL_LIFT_COEFF_VALUE: KEY_WL_LIFT_COEFF_MODE,
            KEY_WL_SUPER_AREA_ELEV_VALUE: KEY_WL_SUPER_AREA_ELEV_MODE,
            KEY_WL_SUPER_AREA_PLAIN_VALUE: KEY_WL_SUPER_AREA_PLAIN_MODE,
            KEY_WL_EXPOSED_FRONTAL_VALUE: KEY_WL_EXPOSED_FRONTAL_MODE,
            KEY_WL_WIND_ECC_DECK_VALUE: KEY_WL_WIND_ECC_DECK_MODE,
            KEY_WL_WIND_LL_ECC_VALUE: KEY_WL_WIND_LL_ECC_MODE,
        }
        mode_key = custom_value_modes.get(key)
        if mode_key and flat_inputs.get(mode_key) != "Custom":
            return True

        return False

    def _record_missing_bridge_input(
        self,
        key: str,
        bridge_validator: BridgeInputValidator,
        flat_inputs: Dict[str, Any],
        result: Dict,
    ) -> None:
        """Record one clear message for a missing required bridge input."""
        validation_error = None
        if key in self.BASIC_VALIDATOR_KEYS:
            validation_error = bridge_validator.validate_basic_inputs(key, flat_inputs)

        if validation_error is None:
            result['errors'].append(f"Missing required bridge input: '{key}'")
            return

        corrected_value, message = validation_error
        result['errors'].append(
            f"Missing required bridge input: '{key}'. {message} Suggested value: {corrected_value!r}."
        )
        result['corrected_values'][key] = corrected_value

    def _record_bridge_validation_error(self, key: str, validation_error: Any, result: Dict) -> None:
        """Convert BridgeInputValidator output into OSI validation errors."""
        if validation_error is None:
            return

        corrected_value, message = validation_error
        result['errors'].append(
            f"Invalid value at '{key}': {message} Suggested value: {corrected_value!r}."
        )
        result['corrected_values'][key] = corrected_value

    def _flatten_osi_data(self, data: Any, prefix: str = "") -> Dict[str, Any]:
        """Flatten nested OSI YAML into dot-separated keys.

        IMPORTANT:
        `BridgeInputValidator` expects OSI keys exactly as they appear in the
        UI/validator constants (e.g. "geometry.span", "typical_section.no_of_girders").

        The previous implementation also emitted intermediate container keys
        (e.g. "geometry" -> { ... }), and attempted to split keys that contain
        dots. That can cause the wrong key/value to be passed into the bridge
        validator.

        This implementation:
        - Flattens only dictionaries into nested dotted paths.
        - Never splits key names on '.' (keys are treated literally).
        - Does not emit container keys; only leaf values are included.
        """
        flat: Dict[str, Any] = {}
        if not isinstance(data, dict):
            return flat

        for key, value in data.items():
            joined = ".".join(part for part in [prefix, str(key)] if part)

            if isinstance(value, dict):
                flat.update(self._flatten_osi_data(value, joined))
            else:
                # Leaf value (including lists/scalars)
                flat[joined] = value

        return flat


    def _validate_data_types(self, data: Dict, result: Dict) -> None:
        """Validate expected data types."""
        type_checks = {
            'geometry.span': (int, float, str),
            'geometry.carriageway_width': (int, float, str),
            'geometry.skew_angle': (int, float, str, type(None)),
            'typical_section.deck_thickness': (int, float, str),
            'typical_section.no_of_girders': (int, str),
            'design_options.shear_studs.count': (int, str),
        }

        self._check_types_recursive(data, result, "", type_checks)

    def _check_types_recursive(self, obj: Any, result: Dict, path: str, type_checks: Dict) -> None:
        """Recursively check data types."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                if current_path in type_checks:
                    expected_types = type_checks[current_path]
                    if not isinstance(value, expected_types):
                        result['warnings'].append(
                            f"Type mismatch at '{current_path}': got {type(value).__name__}, "
                            f"expected {expected_types}."
                        )
                self._check_types_recursive(value, result, current_path, type_checks)

    def _validate_material_codes(self, data: Dict, result: Dict) -> None:
        """Validate material designation codes."""
        materials_to_check = [
            ('material.girder', 'steel'),
            ('material.deck', 'concrete'),
            ('material.cross_bracing', 'steel'),
            ('material.end_diaphragm', 'steel'),
        ]

        for mat_path, mat_type in materials_to_check:
            value = self._get_nested_value(data, mat_path)
            if value:
                if not self._is_valid_material_code(value, mat_type):
                    result['errors'].append(
                        f"Invalid material code at '{mat_path}': '{value}' is not recognized."
                    )

    def _is_valid_material_code(self, code: str, material_type: str) -> bool:
        """Check if material code is valid."""
        valid_steel = {'E 250', 'E 350', 'E 450', 'E 550', 'Fe 410', 'Fe 500', 'Fe 415'}
        valid_concrete = {'M20', 'M25', 'M30', 'M40', 'M50', 'M60', 'M80'}

        if material_type == 'steel':
            return any(code.startswith(m) for m in valid_steel)
        elif material_type == 'concrete':
            return any(code.startswith(m) for m in valid_concrete)
        return True

    def _validate_cross_field_constraints(self, data: Dict, result: Dict) -> None:
        """
        Validate constraints between related fields:
        - girder_spacing < overall_bridge_width
        - deck_thickness within deck properties
        - design_mode consistency
        """
        try:
            # Constraint: girder_spacing < overall_bridge_width
            ts = data.get('typical_section', {})
            if isinstance(ts, dict):
                spacing = self._to_float(ts.get('girder_spacing'))
                overall = self._to_float(ts.get('overall_bridge_width'))
                if spacing and overall and spacing >= overall:
                    result['errors'].append(
                        f"Invalid: girder_spacing ({spacing}) must be less than "
                        f"overall_bridge_width ({overall})."
                    )

            # Constraint: no_of_girders * girder_spacing should be reasonable
            no_girders = self._to_int(ts.get('no_of_girders'))
            if spacing and no_girders:
                total = no_girders * spacing
                if total > (overall * 1.5 if overall else 50):
                    result['warnings'].append(
                        f"Total girder span ({total:.2f}m) seems excessive relative to "
                        f"overall width ({overall}m)."
                    )

            # Constraint: design_mode values
            geom = data.get('geometry', {})
            if isinstance(geom, dict):
                design_mode = geom.get('design_mode')
                valid_modes = {'Manual', 'Optimized', 'Standard'}
                if design_mode and design_mode not in valid_modes:
                    result['errors'].append(
                        f"Invalid design_mode: '{design_mode}'. Must be one of {valid_modes}."
                    )

        except Exception as e:
            result['warnings'].append(f"Could not validate cross-field constraints: {str(e)}")

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def _get_nested_value(self, data: Dict, path: str) -> Optional[Any]:
        """Get value from nested dict using dot-separated path."""
        keys = path.split('.')
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return None
        return current

    def _to_float(self, value: Any) -> Optional[float]:
        """Safely convert value to float."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _to_int(self, value: Any) -> Optional[int]:
        """Safely convert value to int."""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None


# =========================================================================
# PYTEST TEST CASES
# =========================================================================

class TestOSIFileValidation:
    """Test suite for OSI file validation."""

    @pytest.fixture
    def validator(self):
        """Provide validator instance."""
        return OSIValidator()

    @pytest.fixture
    def sample_osi_file(self, tmp_path):
        """Create a valid sample OSI file for testing."""
        content = """
geometry:
  span: '25'
  carriageway_width: '6'
  include_median: 'No'
  design_mode: Optimized
  footpath: None
  skew_angle: '0'

material:
  girder: E 350A
  deck: M40
  cross_bracing: E 350A
  end_diaphragm: E 350A

member_properties:
  girder_details:
    select_girder:
      G1: G1
  cross_bracing_details:
    type:
      G1G2:
        B1M1: K-bracing

design_options:
  construction:
    stage: 'Yes'
  deck:
    top_clear_cover: '50'
    bottom_clear_cover: '50'
    side_clear_cover: '50'
    reinforcement_material: Fe 415
    reinforcement_bounds:
      lower: null
      upper: null
  shear_studs:
    diameter: '16'
    height: '100'
    count: '2'
    yield_strength: '400'
    ultimate_strength: '400'
    transverse_spacing: '100'

design_options_cont:
  deflection:
    limit: '600.00'
  partial_factor:
    yielding_and_buckling:
      gamma_m0: '1.10'

loading:
  permanent_load:
    dead_load:
      self_weight_factor: '1.00'
  live_load:
    eccentricity: '1.2'
  seismic_load:
    importance_factor: '1.0'
  wind_load:
    avg_exposed_height: '10'
  temperature_load:
    thermal_coeff_steel: '12.0e-6'

typical_section:
  deck_thickness: 200.0
  footpath_width: 0.0
  girder_spacing: 1.73
  no_of_girders: 4
  deck_overhang: 0.855
  overall_bridge_width: 6.9

support_conditions:
  bearing_length: '400.00'
  left_support: Pinned
  right_support: Roller

structure:
  type: Highway Bridge

project:
  location: Test Location
"""
        file_path = tmp_path / "test.osi"
        file_path.write_text(content)
        return str(file_path)

    def test_valid_osi_file(self, validator, sample_osi_file):
        """Test validation of a complete, correct OSI file."""
        result = validator.validate_osi_file(sample_osi_file)
        assert result['is_valid'], f"Errors: {result['errors']}"
        assert len(result['errors']) == 0
        assert result['completeness_score'] >= 90

    def test_osi_file_not_found(self, validator):
        """Test handling of missing OSI file."""
        result = validator.validate_osi_file("/nonexistent/path/file.osi")
        assert not result['is_valid']
        assert any("not found" in err.lower() for err in result['errors'])

    def test_missing_required_geometry_fields(self, validator, tmp_path):
        """Test detection of missing required geometry fields."""
        content = """
geometry:
  span: '25'
material: {}
design_options: {}
loading: {}
typical_section: {}
support_conditions: {}
structure: {}
project: {}
"""
        file_path = tmp_path / "incomplete.osi"
        file_path.write_text(content)
        result = validator.validate_osi_file(str(file_path))
        assert not result['is_valid']
        assert result['completeness_score'] < 100
        assert any("carriageway_width" in err.lower() for err in result['errors'])

    def test_span_value_out_of_range(self, validator, tmp_path):
        """Test detection of span value outside valid range."""
        content = """
geometry:
  span: '150'
  carriageway_width: '6'
  include_median: 'No'
  design_mode: Optimized
  footpath: null
material: {}
design_options: {}
loading: {}
typical_section: {}
support_conditions: {}
structure: {}
project: {}
"""
        file_path = tmp_path / "invalid_span.osi"
        file_path.write_text(content)
        result = validator.validate_osi_file(str(file_path))
        assert any("span" in err.lower() for err in result['errors'] + result['warnings'])

    def test_invalid_material_code(self, validator, tmp_path):
        """Test detection of invalid material designation."""
        content = """
geometry:
  span: '25'
  carriageway_width: '6'
  include_median: 'No'
  design_mode: Optimized
  footpath: null
material:
  girder: UNKNOWN_GRADE
  deck: M40
  cross_bracing: E 350A
  end_diaphragm: E 350A
design_options: {}
loading: {}
typical_section: {}
support_conditions: {}
structure: {}
project: {}
"""
        file_path = tmp_path / "invalid_material.osi"
        file_path.write_text(content)
        result = validator.validate_osi_file(str(file_path))
        assert any("material" in err.lower() for err in result['errors'])

    def test_invalid_design_mode(self, validator, tmp_path):
        """Test detection of invalid design mode."""
        content = """
geometry:
  span: '25'
  carriageway_width: '6'
  include_median: 'No'
  design_mode: InvalidMode
  footpath: null
material:
  girder: E 350A
  deck: M40
  cross_bracing: E 350A
  end_diaphragm: E 350A
design_options: {}
loading: {}
typical_section: {}
support_conditions: {}
structure: {}
project: {}
"""
        file_path = tmp_path / "invalid_design_mode.osi"
        file_path.write_text(content)
        result = validator.validate_osi_file(str(file_path))
        assert any("design_mode" in err.lower() for err in result['errors'])

    def test_deck_thickness_out_of_range(self, validator, tmp_path):
        """Test detection of deck thickness outside valid range."""
        content = """
geometry:
  span: '25'
  carriageway_width: '6'
  include_median: 'No'
  design_mode: Optimized
  footpath: null
material:
  girder: E 350A
  deck: M40
  cross_bracing: E 350A
  end_diaphragm: E 350A
design_options: {}
loading: {}
typical_section:
  deck_thickness: 50.0
support_conditions: {}
structure: {}
project: {}
"""
        file_path = tmp_path / "invalid_thickness.osi"
        file_path.write_text(content)
        result = validator.validate_osi_file(str(file_path))
        assert any("thickness" in err.lower() for err in result['errors'] + result['warnings'])

    def test_girder_spacing_greater_than_overall_width(self, validator, tmp_path):
        """Test cross-field constraint: girder_spacing < overall_bridge_width."""
        content = """
geometry:
  span: '25'
  carriageway_width: '6'
  include_median: 'No'
  design_mode: Optimized
  footpath: null
material:
  girder: E 350A
  deck: M40
  cross_bracing: E 350A
  end_diaphragm: E 350A
design_options: {}
loading: {}
typical_section:
  deck_thickness: 200.0
  girder_spacing: 50.0
  overall_bridge_width: 6.9
  no_of_girders: 4
support_conditions: {}
structure: {}
project: {}
"""
        file_path = tmp_path / "invalid_spacing.osi"
        file_path.write_text(content)
        result = validator.validate_osi_file(str(file_path))
        assert any("spacing" in err.lower() for err in result['errors'])

    def test_yaml_syntax_error(self, validator, tmp_path):
        """Test handling of malformed YAML."""
        content = """
geometry:
  span: '25'
  carriageway_width: '6
  invalid yaml [
"""
        file_path = tmp_path / "malformed.osi"
        file_path.write_text(content)
        result = validator.validate_osi_file(str(file_path))
        assert not result['is_valid']
        assert any("yaml" in err.lower() or "syntax" in err.lower() for err in result['errors'])

    def test_completeness_score_calculation(self, validator, tmp_path):
        """Test completeness score is calculated correctly."""
        content = """
geometry:
  span: '25'
material: {}
design_options: {}
loading: {}
typical_section: {}
support_conditions: {}
structure: {}
project: {}
"""
        file_path = tmp_path / "partial.osi"
        file_path.write_text(content)
        result = validator.validate_osi_file(str(file_path))
        assert 0 <= result['completeness_score'] <= 100
        assert result['completeness_score'] < 100

    def test_null_values_in_required_bridge_fields_are_reported(self, validator, tmp_path):
        """Test null handling for required bridge fields.

        - geometry.footpath = null is a *required* field with no sensible default
          and must be reported as missing.
        - geometry.skew_angle = null means "straight bridge" (0°), which is a
          valid value, so it must NOT be reported as an error.
        """
        content = """
geometry:
  span: '25'
  carriageway_width: '6'
  include_median: 'No'
  design_mode: Optimized
  footpath: null
  skew_angle: null
material:
  girder: E 350A
  deck: M40
  cross_bracing: E 350A
  end_diaphragm: E 350A
design_options: {}
loading: {}
typical_section:
  deck_thickness: 200.0
support_conditions: {}
structure: {}
project: {}
"""
        file_path = tmp_path / "with_nulls.osi"
        file_path.write_text(content)
        result = validator.validate_osi_file(str(file_path))
        # footpath=null is genuinely missing and must be flagged.
        assert any("geometry.footpath" in err for err in result['errors'])
        # skew_angle=null means 0° (straight bridge) and must NOT be an error.
        assert not any("geometry.skew_angle" in err for err in result['errors']), (
            "null skew_angle should be treated as 0° (straight bridge), not an error"
        )

    def test_value_type_coercion(self, validator, tmp_path):
        """Test that numeric strings are properly handled."""
        content = """
geometry:
  span: '25'
  carriageway_width: '6'
  include_median: 'No'
  design_mode: Optimized
  footpath: null
material:
  girder: E 350A
  deck: M40
  cross_bracing: E 350A
  end_diaphragm: E 350A
design_options:
  shear_studs:
    count: '2'
    diameter: '16'
loading: {}
typical_section:
  deck_thickness: '200'
  no_of_girders: '4'
support_conditions: {}
structure: {}
project: {}
"""
        file_path = tmp_path / "string_numbers.osi"
        file_path.write_text(content)
        result = validator.validate_osi_file(str(file_path))
        # String numbers should be accepted and coerced
        assert not any("type" in err.lower() and "error" in err.lower() for err in result['errors'])

    def test_structure_key_naming_convention(self, validator, tmp_path):
        """Test detection of non-standard key naming."""
        content = """
geometry:
  Span: '25'
  carriageway_width: '6'
  include_median: 'No'
  design_mode: Optimized
  footpath: null
material: {}
design_options: {}
loading: {}
typical_section: {}
support_conditions: {}
structure: {}
project: {}
"""
        file_path = tmp_path / "bad_naming.osi"
        file_path.write_text(content)
        result = validator.validate_osi_file(str(file_path))
        # Should have warnings about naming convention
        assert any("naming" in issue.lower() or "convention" in issue.lower() 
                   for issue in result['structure_issues'])

    def test_shear_studs_all_parameters_present(self, validator, tmp_path):
        """Test all shear stud parameters are validated."""
        content = """
geometry:
  span: '25'
  carriageway_width: '6'
  include_median: 'No'
  design_mode: Optimized
  footpath: null
material:
  girder: E 350A
  deck: M40
  cross_bracing: E 350A
  end_diaphragm: E 350A
design_options:
  shear_studs:
    diameter: '16'
    height: '100'
    count: '2'
    yield_strength: '400'
    ultimate_strength: '400'
    transverse_spacing: '100'
loading: {}
typical_section:
  deck_thickness: 200.0
support_conditions: {}
structure: {}
project: {}
"""
        file_path = tmp_path / "studs_complete.osi"
        file_path.write_text(content)
        result = validator.validate_osi_file(str(file_path))
        assert not any("shear_stud" in err.lower() for err in result['errors'])


def validate_osi_file_cli(file_path: str) -> None:
    """
    CLI tool to validate an OSI file.
    Usage: python test_Osi.py <path_to_osi_file>
    """
    import json
    from pathlib import Path
    
    file_path_obj = Path(file_path)
    
    if not file_path_obj.exists():
        print(f"❌ Error: File not found: {file_path}")
        return
    
    print(f"\n{'='*70}")
    print(f"OSI FILE VALIDATION REPORT")
    print(f"{'='*70}")
    print(f"File: {file_path}")
    print(f"{'='*70}\n")
    
    validator = OSIValidator()
    result = validator.validate_osi_file(file_path)
    
    # Print validation status
    status = "✅ VALID" if result['is_valid'] else "❌ INVALID"
    print(f"Overall Status: {status}")
    print(f"Completeness Score: {result['completeness_score']:.1f}%\n")
    
    # Print errors
    if result['errors']:
        print(f"ERRORS ({len(result['errors'])}):")
        print("-" * 70)
        for i, error in enumerate(result['errors'], 1):
            print(f"  {i}. {error}")
        print()
    
    # Print warnings
    if result['warnings']:
        print(f"WARNINGS ({len(result['warnings'])}):")
        print("-" * 70)
        for i, warning in enumerate(result['warnings'], 1):
            print(f"  {i}. {warning}")
        print()
    
    # Print structure issues
    if result['structure_issues']:
        print(f"STRUCTURE ISSUES ({len(result['structure_issues'])}):")
        print("-" * 70)
        for i, issue in enumerate(result['structure_issues'], 1):
            print(f"  {i}. {issue}")
        print()
    
    # Print corrected values if any
    if result['corrected_values']:
        print(f"SUGGESTED CORRECTIONS ({len(result['corrected_values'])}):")
        print("-" * 70)
        for path, corrected_value in result['corrected_values'].items():
            print(f"  {path}: {corrected_value}")
        print()
    
    print(f"{'='*70}\n")


if __name__ == "__main__":
    import sys
    
    # If a file path is provided as argument, validate that file
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        validate_osi_file_cli(sys.argv[1])
    else:
        # Otherwise, run pytest
        pytest.main([__file__, "-v"])
