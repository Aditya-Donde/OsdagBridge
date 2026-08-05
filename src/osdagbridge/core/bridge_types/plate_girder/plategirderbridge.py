from __future__ import annotations
import sqlite3
import types
from pathlib import Path
from .ui_fields import FrontendData
from .dto import (
    ConcreteProperties,
    DeckLayoutProperties,
    GrillageGeometry,
    SectionProperties,
    SteelProperties,
    MaterialProperties,
    BridgeParametersDTO,
    SectionDimsDTO,
    ISectionDimsDTO,
    ShearStudParamsDTO,
    GirderSegmentDTO,
)
from .defaults import (
    BASIC_INPUT_DICT,
)
from .initial_sizing import DEFAULT_FOOTPATH_WIDTH
from .analyser import BridgeGrillageModel
from osdagbridge.core.utils.memory_guard import OpsMemoryGuard, log_memory, tracemalloc_mark_start
from .analysis_results import PlateGirderAnalysisResults
from .designer import run_design_check
from . import deckdesign
from .plot_generator import (
    build_figure_sfd,
    build_figure_bmd,
    # build_figure_bmd_contour,  # commented out
    build_figure_deflection,
    build_figure_grillage,
    build_nodes_members,
    figure_to_bytes,
)
from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
from osdagbridge.core.utils.common import (
    KEY_STRUCTURE_TYPE,
    KEY_PROJECT_LOCATION,
    KEY_SPAN,
    KEY_CARRIAGEWAY_WIDTH,
    KEY_INCLUDE_MEDIAN,
    KEY_FOOTPATH,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_RAILING_WIDTH,
    KEY_SKEW_ANGLE,
    KEY_DESIGN_MODE,
    KEY_GIRDER,
    KEY_CROSS_BRACING,
    KEY_END_DIAPHRAGM,
    KEY_DECK_CONCRETE_GRADE_BASIC,
    KEY_DS_REINF_MATERIAL,
    KEY_MATERIAL_GIRDER_E, KEY_MATERIAL_GIRDER_G, KEY_MATERIAL_GIRDER_POISSON,
    KEY_MATERIAL_GIRDER_FY, KEY_MATERIAL_GIRDER_FU, KEY_MATERIAL_GIRDER_THERMAL,
    KEY_MATERIAL_DECK_FCK, KEY_MATERIAL_DECK_FCTM, KEY_MATERIAL_DECK_ECM,
    DEFAULT_CRASH_BARRIER_WIDTH,
    DEFAULT_RAILING_WIDTH,
    DEFAULT_GIRDER_SPACING,
    DEFAULT_CROSS_BRACING_SPACING,
    MPa,
    GPa,
    N,
    m,
    KEY_UTIL_FLEXURE,
    KEY_UTIL_SHEAR,
    KEY_UTIL_INTERACTION,
    KEY_UTIL_LTB,
    KEY_UTIL_DEFLECTION_CRACK,
    KEY_UTIL_FATIGUE,
    KEY_UTIL_LONG_TRANS_SHEAR,
    KEY_UTIL_STRESS_LIMITATION,
    KEY_SL_IMPORTANCE_FACTOR, KEY_SL_SOIL_TYPE, KEY_SL_TIME_PERIOD,
    KEY_SL_DAMPING, KEY_SL_RESPONSE_REDUCTION,
    KEY_SL_DEAD_LOAD_MODE, KEY_SL_DEAD_LOAD_VALUE,
    KEY_SL_LIVE_LOAD_MODE, KEY_SL_LIVE_LOAD_VALUE,
    KEY_SL_HORIZONTAL_COEFF, KEY_SL_VERTICAL_COEFF,
    KEY_MD_WIDTH,
    KEY_RL_WIDTH,
    KEY_TS_DECK_OVERHANG,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_OVERALL_WIDTH,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_TS_NO_OF_FOOTPATHS,
    KEY_WC_THICKNESS,
    KEY_WC_DENSITY,
    KEY_LL_ECCENTRICITY,
    KEY_MP_GIRDER_SYMMETRY, KEY_MP_GIRDER_DEPTH, KEY_MP_GIRDER_WEB_DEPTH, KEY_MP_GIRDER_WEB_THICKNESS,
    KEY_MP_GIRDER_TOP_FLANGE_WIDTH, KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
    KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH, KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
    KEY_MP_GIRDER_SECTIONAL_AREA, KEY_MP_GIRDER_MASS,
    KEY_MP_GIRDER_SECTIONAL_IZ, KEY_MP_GIRDER_SECTIONAL_IY,
    KEY_MP_GIRDER_RADIUS_GYRATION_Z, KEY_MP_GIRDER_RADIUS_GYRATION_Y,
    KEY_MP_GIRDER_ELASTIC_MODULUS_ZZ, KEY_MP_GIRDER_ELASTIC_MODULUS_ZY,
    KEY_MP_GIRDER_PLASTIC_MODULUS_ZUZ, KEY_MP_GIRDER_PLASTIC_MODULUS_ZUY,
    KEY_MP_GIRDER_TORSION_CONSTANT_IT, KEY_MP_GIRDER_WARPING_CONSTANT_IW,
    KEY_METALLIC_CRASH_BARRIER_TYPE,
    KEY_RIGID_CRASH_BARRIER_TYPE,
    KEY_CRASH_BARRIER_TYPE,
    KEY_CB_TYPE,
    KEY_RL_TYPE,
    KEY_RAILING_TYPE,
    KEY_MD_TYPE,
    KEY_MEDIAN_TYPE,
    KEY_DS_STUD_DIAMETER,
    KEY_DS_STUD_HEIGHT,
    KEY_DS_STUD_COUNT,
    KEY_DS_STUD_TRANSVERSE_SPACING,
    KEY_DS_STUD_HEAD_DIAMETER,
    KEY_DS_STUD_HEAD_HEIGHT,
    KEY_MP_GIRDER_TORSIONAL_RESTRAINT,
    KEY_MP_GIRDER_WARPING_RESTRAINT,
    KEY_MP_GIRDER_WEB_TYPE,

    # Dimensional card
    KEY_SD_GRADE_OF_MATERIAL,
    KEY_SD_SECTION_TYPE,
    KEY_SD_SECTION_DESIGNATION,
    KEY_SD_SECTION_CLASS,
    KEY_SD_TOTAL_DEPTH,
    KEY_SD_WEB_THICKNESS,
    KEY_SD_TOP_FLANGE_WIDTH,
    KEY_SD_TOP_FLANGE_THICKNESS,
    KEY_SD_BOTTOM_FLANGE_WIDTH,
    KEY_SD_BOTTOM_FLANGE_THICKNESS,
    KEY_SD_TORSIONAL_RESTRAINT,
    KEY_SD_WARPING_RESTRAINT,
    KEY_SD_WEB_TYPE,
    KEY_SD_EFFECTIVE_SLAB_WIDTH,
    # Shear connector card
    KEY_SD_SHEAR_YIELD_STRENGTH,
    KEY_SD_SHEAR_ULTIMATE_STRENGTH,
    KEY_SD_SHEAR_DIAMETER,
    KEY_SD_SHEAR_HEIGHT,
    KEY_SD_SHEAR_TRANSVERSE_SPACING,
    KEY_SD_SHEAR_STUDS_PER_SECTION,
    KEY_SD_SHEAR_LONGITUDINAL_SPACING,
    # Section properties card
    KEY_MP_GIRDER_MASS,
    KEY_MP_GIRDER_SECTIONAL_AREA,
    KEY_MP_GIRDER_SECTIONAL_IZ,
    KEY_MP_GIRDER_SECTIONAL_IY,
    KEY_MP_GIRDER_RADIUS_GYRATION_Z,
    KEY_MP_GIRDER_RADIUS_GYRATION_Y,
    KEY_MP_GIRDER_ELASTIC_MODULUS_ZZ,
    KEY_MP_GIRDER_ELASTIC_MODULUS_ZY,
    KEY_MP_GIRDER_PLASTIC_MODULUS_ZUZ,
    KEY_MP_GIRDER_PLASTIC_MODULUS_ZUY,
    KEY_MP_GIRDER_TORSION_CONSTANT_IT,
    KEY_MP_GIRDER_WARPING_CONSTANT_IW,
    KEY_SD_SECTION_PROP_MASS,
    KEY_SD_SECTION_PROP_AREA,
    KEY_SD_SECTION_PROP_IZ,
    KEY_SD_SECTION_PROP_IV,
    KEY_SD_SECTION_PROP_RZ,
    KEY_SD_SECTION_PROP_RV,
    KEY_SD_SECTION_PROP_ZZ,
    KEY_SD_SECTION_PROP_ZV,
    KEY_SD_SECTION_PROP_ZUZ,
    KEY_SD_SECTION_PROP_ZUV,
    KEY_SD_SECTION_PROP_IT,
    KEY_SD_SECTION_PROP_IW,
    KEY_SD_COMPOSITE_IZ,
    KEY_SD_PNA_DEPTH,
    KEY_SD_MU_APPLIED,
    KEY_SD_MD_CAPACITY,
    KEY_SD_FLANGE_SLENDERNESS,
    KEY_SD_WEB_SLENDERNESS,
    KEY_SD_WEB_CLASS_LIMIT,
    KEY_SD_FLANGE_CLASS_LIMIT,
    KEY_SD_CLASS_FLANGE,
    KEY_SD_CLASS_WEB,
    KEY_SD_SHEAR_VU,
    KEY_SD_SHEAR_AV,
    KEY_SD_PANEL_CD,
    KEY_SD_SHEAR_KV,
    KEY_SD_SHEAR_LAMBDA_W,
    KEY_SD_SHEAR_TAU_B,
    KEY_SD_SHEAR_VCR,
    KEY_SD_HIGH_SHEAR,
    KEY_SD_MDV,
    KEY_SD_MN_AXIAL,
    KEY_SD_MN_MOMENT,
    KEY_SD_MN_RATIO,
    KEY_SD_LTB_MCR,
    KEY_SD_LTB_LAMBDA,
    KEY_SD_LTB_CHI,
    KEY_SD_LTB_MB,
    KEY_SD_STIFF_METHOD,
    KEY_SD_STIFF_INT_THICK,
    KEY_SD_STIFF_INT_SPACING,
    KEY_SD_STIFF_END_THICK,
    KEY_SD_STIFF_END_COUNT,
    KEY_SD_STIFF_LONG,
    KEY_SD_IS_IYS_MIN,
    KEY_SD_IS_IYS_PROV,
    KEY_SD_IS_FQ,
    KEY_SD_IS_FQD,
    KEY_SD_BS_R,
    KEY_SD_BS_FCDW_WB,
    KEY_SD_BS_FCDW_LC,
    KEY_SD_BS_FPSD,
    KEY_SD_BS_FCD,
    # Deflection check keys (Table 5.10)
    KEY_SD_DEFL_LIVE,
    KEY_SD_DEFL_TOTAL,
    KEY_SD_DEFL_ALLOW_LIVE,
    KEY_SD_DEFL_ALLOW_TOTAL,
    # Stiffener table
    KEY_SD_STIFFENER_ROW_INTERMEDIATE,
    KEY_SD_STIFFENER_ROW_LONGITUDINAL,
    KEY_SD_STIFFENER_ROW_BEARING,
    KEY_SD_STIFFENER_COL_GRADE,
    KEY_SD_STIFFENER_COL_THICKNESS,
    KEY_SD_STIFFENER_COL_WIDTH,
    KEY_SD_STIFFENER_COL_SPACING,
    # Design options — shear stud transverse spacing input key
    KEY_DS_STUD_TRANSVERSE_SPACING,
    KEY_MP_STIFFENER_LONGITUDINAL_THICKNESS,
    KEY_MP_STIFFENER_BEARING_OUTSTAND,
    KEY_MP_STIFFENER_BEARING_THICKNESS,
    KEY_MP_STIFFENER_SPACING,
    KEY_MP_STIFFENER_NO_BEARING_STIFFENERS,
    KEY_MP_STIFFENER_INTERMEDIATE,
    KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS,
    KEY_MP_STIFFENER_INTERMEDIATE_OUTSTAND,
    KEY_MP_STIFFENER_INTERMEDIATE_SPACING,
    KEY_MP_STIFFENER_LONGITUDINAL,

    # Cross Bracing Details
    KEY_MP_CB_TYPE,
    KEY_MP_CB_BRACING_SECTION_TYPE,
    KEY_MP_CB_BRACING_SECTION_DESIGNATION,
    KEY_MP_CB_TOP_CHORD,
    KEY_MP_CB_TOP_CHORD_SECTION_TYPE,
    KEY_MP_CB_TOP_CHORD_SECTION_DESIG,
    KEY_MP_CB_BOTTOM_CHORD,
    KEY_MP_CB_BOTTOM_CHORD_SECTION_TYPE,
    KEY_MP_CB_BOTTOM_CHORD_SECTION_DESIG,

    # End Diaphragm Details
    KEY_MP_ED_BRACING_TYPE,
    KEY_MP_ED_BRACING_SECTION,
    KEY_MP_ED_BRACING_SECTION_DESIGNATION,
    KEY_MP_ED_TOP_CHORD,
    KEY_MP_ED_TOP_CHORD_SECTION_TYPE,
    KEY_MP_ED_TOP_CHORD_SECTION_DESIG,
    KEY_MP_ED_BOTTOM_CHORD,
    KEY_MP_ED_BOTTOM_CHORD_SECTION_TYPE,
    KEY_MP_ED_BOTTOM_CHORD_SECTION_DESIG,

    # Transverse member properties
    KEY_TD_CB_PROP_L, KEY_TD_CB_PROP_H, KEY_TD_CB_PROP_B, KEY_TD_CB_PROP_TW, KEY_TD_CB_PROP_TF,
    KEY_TD_CB_PROP_RZ, KEY_TD_CB_PROP_M, KEY_TD_CB_PROP_A, KEY_TD_CB_PROP_IZ, KEY_TD_CB_PROP_IV,
    KEY_TD_CB_PROP_RV, KEY_TD_CB_PROP_ZZ, KEY_TD_CB_PROP_ZV, KEY_TD_CB_PROP_ZUZ, KEY_TD_CB_PROP_ZUV,
            
    KEY_TD_CB_TOP_CHORD_PROP_L, KEY_TD_CB_TOP_CHORD_PROP_H, KEY_TD_CB_TOP_CHORD_PROP_B, KEY_TD_CB_TOP_CHORD_PROP_TW, KEY_TD_CB_TOP_CHORD_PROP_TF,
    KEY_TD_CB_TOP_CHORD_PROP_RZ, KEY_TD_CB_TOP_CHORD_PROP_M, KEY_TD_CB_TOP_CHORD_PROP_A, KEY_TD_CB_TOP_CHORD_PROP_IZ, KEY_TD_CB_TOP_CHORD_PROP_IV,
    KEY_TD_CB_TOP_CHORD_PROP_RV, KEY_TD_CB_TOP_CHORD_PROP_ZZ, KEY_TD_CB_TOP_CHORD_PROP_ZV, KEY_TD_CB_TOP_CHORD_PROP_ZUZ, KEY_TD_CB_TOP_CHORD_PROP_ZUV,
    
    KEY_TD_CB_BOTTOM_CHORD_PROP_L, KEY_TD_CB_BOTTOM_CHORD_PROP_H, KEY_TD_CB_BOTTOM_CHORD_PROP_B, KEY_TD_CB_BOTTOM_CHORD_PROP_TW, KEY_TD_CB_BOTTOM_CHORD_PROP_TF,
    KEY_TD_CB_BOTTOM_CHORD_PROP_RZ, KEY_TD_CB_BOTTOM_CHORD_PROP_M, KEY_TD_CB_BOTTOM_CHORD_PROP_A, KEY_TD_CB_BOTTOM_CHORD_PROP_IZ, KEY_TD_CB_BOTTOM_CHORD_PROP_IV,
    KEY_TD_CB_BOTTOM_CHORD_PROP_RV, KEY_TD_CB_BOTTOM_CHORD_PROP_ZZ, KEY_TD_CB_BOTTOM_CHORD_PROP_ZV, KEY_TD_CB_BOTTOM_CHORD_PROP_ZUZ, KEY_TD_CB_BOTTOM_CHORD_PROP_ZUV,

    KEY_TD_ED_PROP_L, KEY_TD_ED_PROP_H, KEY_TD_ED_PROP_B, KEY_TD_ED_PROP_TW, KEY_TD_ED_PROP_TF,
    KEY_TD_ED_PROP_RZ, KEY_TD_ED_PROP_M, KEY_TD_ED_PROP_A, KEY_TD_ED_PROP_IZ, KEY_TD_ED_PROP_IV,
    KEY_TD_ED_PROP_RV, KEY_TD_ED_PROP_ZZ, KEY_TD_ED_PROP_ZV, KEY_TD_ED_PROP_ZUZ, KEY_TD_ED_PROP_ZUV,

    KEY_TD_ED_TOP_CHORD_PROP_L, KEY_TD_ED_TOP_CHORD_PROP_H, KEY_TD_ED_TOP_CHORD_PROP_B, KEY_TD_ED_TOP_CHORD_PROP_TW, KEY_TD_ED_TOP_CHORD_PROP_TF,
    KEY_TD_ED_TOP_CHORD_PROP_RZ, KEY_TD_ED_TOP_CHORD_PROP_M, KEY_TD_ED_TOP_CHORD_PROP_A, KEY_TD_ED_TOP_CHORD_PROP_IZ, KEY_TD_ED_TOP_CHORD_PROP_IV,
    KEY_TD_ED_TOP_CHORD_PROP_RV, KEY_TD_ED_TOP_CHORD_PROP_ZZ, KEY_TD_ED_TOP_CHORD_PROP_ZV, KEY_TD_ED_TOP_CHORD_PROP_ZUZ, KEY_TD_ED_TOP_CHORD_PROP_ZUV,

    KEY_TD_ED_BOTTOM_CHORD_PROP_L, KEY_TD_ED_BOTTOM_CHORD_PROP_H, KEY_TD_ED_BOTTOM_CHORD_PROP_B, KEY_TD_ED_BOTTOM_CHORD_PROP_TW, KEY_TD_ED_BOTTOM_CHORD_PROP_TF,
    KEY_TD_ED_BOTTOM_CHORD_PROP_RZ, KEY_TD_ED_BOTTOM_CHORD_PROP_M, KEY_TD_ED_BOTTOM_CHORD_PROP_A, KEY_TD_ED_BOTTOM_CHORD_PROP_IZ, KEY_TD_ED_BOTTOM_CHORD_PROP_IV,
    KEY_TD_ED_BOTTOM_CHORD_PROP_RV, KEY_TD_ED_BOTTOM_CHORD_PROP_ZZ, KEY_TD_ED_BOTTOM_CHORD_PROP_ZV, KEY_TD_ED_BOTTOM_CHORD_PROP_ZUZ, KEY_TD_ED_BOTTOM_CHORD_PROP_ZUV,
)

from osdagbridge.core.bridge_types.plate_girder.initial_sizing import (
    DEFAULT_DECK_THICKNESS as _DEFAULT_DECK_THICKNESS_MM,
)
from osdagbridge.core.bridge_components.super_structure.deck.geometry import (
    deck_thickness_from_inputs,
)
from osdagbridge.core.bridge_components.super_structure.crash_barrier.geometry import (
    crash_barrier_load_from_inputs,
)
from osdagbridge.core.bridge_components.super_structure.railing.geometry import (
    railing_load_from_inputs,
)
from osdagbridge.core.bridge_components.super_structure.shear_studs.geometry import (
    min_stud_head_diameter,
    min_stud_head_height,
)
from osdagbridge.core.utils.logger import bridge_logger
from osdagbridge.core.bridge_types.plate_girder.designer import (BridgeConfig, IRC22CapacityCalculator, DCREngine, DemandEnvelope, design_envelope_engine,)

_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "ResourceFiles" / "Intg_osdag.sqlite"

# Steel constants (same values used in analyser.py __main__)
_STEEL_E0       = 200 * GPa    # Initial elastic modulus (Pa)
_STEEL_B        = 0.01         # Strain-hardening ratio
_STEEL_FY_DEFAULT = 250 * MPa  # Fallback Fy if material not found in DB (Pa)


def resolve_girder_value(source: dict, base_key: str, i: int | None = None):
    """
    Resolve a girder property from an input/output dict, tolerating both the
    per-girder dynamic key scheme and the legacy scalar key.

    Per-girder values are stored under ``<base_key>.G{i+1}.M1`` (see
    ``defaults.solve_extend_basic_input_dict``). Resolution order:

      1. ``<base_key>.G{i+1}.M1`` — the requested girder (only when ``i`` given),
      2. ``<base_key>``           — the legacy scalar key, if still populated,
      3. ``<base_key>.G1.M1``     — first girder, the representative fallback used
                                    for edge beams / transverse members and any
                                    consumer that does not care about a specific
                                    girder.

    Raises ``KeyError(base_key)`` if none of the candidates are present.
    """
    candidates = []
    if i is not None:
        candidates.append(f"{base_key}.G{i + 1}.M1")
    candidates.append(base_key)
    candidates.append(f"{base_key}.G1.M1")
    for key in candidates:
        if key in source:
            return source[key]
    raise KeyError(base_key)


class PlateGirderBridge:
    """Core backend for Plate Girder Bridge."""

    # Keys that originate from the basic input dock.
    # Everything else in input_dict is treated as an additional input.
    _BASIC_INPUT_KEYS = frozenset({
        KEY_STRUCTURE_TYPE,
        KEY_PROJECT_LOCATION,
        KEY_SPAN,
        KEY_CARRIAGEWAY_WIDTH,
        KEY_INCLUDE_MEDIAN,
        KEY_FOOTPATH,
        KEY_SKEW_ANGLE,
        KEY_DESIGN_MODE,
        KEY_GIRDER,
        KEY_CROSS_BRACING,
        KEY_END_DIAPHRAGM,
        KEY_DECK_CONCRETE_GRADE_BASIC,
        KEY_MD_WIDTH,
    })

    def __init__(self) -> None:
        self.input_dict: dict = {}
        self.basic_inputs: dict = {}
        self.additional_inputs: dict = {}
        self._frontend = FrontendData()
        # Immutable snapshot of input_dict captured at the start of design().
        # All 3D CAD / IFC methods read from this instead of the live input_dict.
        self.output_dict: types.MappingProxyType = types.MappingProxyType({})

        # Results populated by design()
        self.grillage_geometry: GrillageGeometry | None = None
        self.deck_layout: DeckLayoutProperties | None = None
        self.result_data: dict = {}         # flat restructured dataset, set after analysis

        # Analyser — populated by setup_grillage()
        self.grillage_model: BridgeGrillageModel = BridgeGrillageModel()

        # Central ospgrillage / OpenSeesPy memory-release policy (see OpsMemoryGuard).
        self.memory = OpsMemoryGuard(self)

        # When True, design() writes tools/bridge_full_data.json. Off by default.
        self.dump_json: bool = False

    def input_values(self) -> list:
        """Return UI field definitions for the InputDock (delegated to FrontendData)."""
        return self._frontend.input_values()
    
    def output_values(self) -> list:
        """Return UI field definitions for the OutputDock (delegated to FrontendData)."""
        return self._frontend.output_values()

    def set_input(self, input_dict: dict) -> None:
        """
        Receive and store the input dictionary from the UI.

        Stores the full dict in ``self.input_dict`` and splits it into:
        - ``self.basic_inputs``  — keys from the main input dock
        - ``self.additional_inputs`` — all remaining keys (additional-input dialog, etc.)

        All values are normalised so that numeric strings are coerced to
        ``int`` / ``float`` before any downstream consumer touches them.

        Parameters
        ----------
        input_dict : dict
            The flat dictionary built and maintained by ``CustomWindow``.
        """
        self.input_dict = self._normalize_input_dict(input_dict)
        self.basic_inputs = {
            k: v for k, v in self.input_dict.items()
            if k in self._BASIC_INPUT_KEYS
        }
        self.additional_inputs = {
            k: v for k, v in self.input_dict.items()
            if k not in self._BASIC_INPUT_KEYS
        }

    # ------------------------------------------------------------------
    # Input normalisation
    # ------------------------------------------------------------------

    @staticmethod
    def _coerce(value):
        """Convert a value to its natural Python type, recursively.

        * Numeric strings → ``int`` (if no decimal point) or ``float``.
        * ``bool``, ``int``, ``float`` pass through as-is.
        * ``list`` → each element is coerced recursively.
        * ``dict`` → each value is coerced recursively.
        * Everything else (non-numeric strings) is returned unchanged.
        """
        # --- scalars already in the right type ---
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value

        # --- lists: recurse into each element ---
        if isinstance(value, list):
            return [PlateGirderBridge._coerce(item) for item in value]

        # --- dicts: coerce each value, keep keys as-is ---
        if isinstance(value, dict):
            return {k: PlateGirderBridge._coerce(v) for k, v in value.items()}

        # --- strings: try numeric conversion ---
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return value
            # int check first — ``"400"`` should stay int, not float
            try:
                int_val = int(text)
                if str(int_val) == text:
                    return int_val
            except (ValueError, TypeError):
                pass
            try:
                return float(text)
            except (ValueError, TypeError):
                pass
        return value

    @classmethod
    def _normalize_input_dict(cls, raw: dict) -> dict:
        """Return a copy of *raw* with all values coerced to native types."""
        return {k: cls._coerce(v) for k, v in raw.items()}

    # ─────────────────────────────────────────────────────────────────────────
    # Design pipeline
    # ─────────────────────────────────────────────────────────────────────────

    def _resolve_optimized_bounds_to_mm(self) -> None:
        """
        For Optimised design, per-girder dimensional keys may hold list values
        (user-supplied optimisation bounds in mm) or the string "All".
        This method collapses each such key to a single float **stored in metres**
        so that designer and analyser remain in SI units.

        Resolution rule (applied only to list / string values):
          * list  → floor(min(min(list), max(list), initial_sizing_default_mm)) / 1000
          * "All" → snap the initial-sizing default UP to the next SAIL-approved
                    thickness (smallest SAIL value >= initial_sizing_mm), / 1000.
                    "All" is only ever stored for the three thickness keys.
          * float (mm) → left for _convert_girder_dims_mm_to_m to divide by 1000.

        ``initial_sizing_default_mm`` is BridgeConfigurationSolver
        .compute_section_properties() value × 1000.

        Keys resolved (per girder, suffix ``.G{n}.M1``):
            KEY_MP_GIRDER_DEPTH, KEY_MP_GIRDER_WEB_DEPTH,
            KEY_MP_GIRDER_TOP_FLANGE_WIDTH, KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH,
            KEY_MP_GIRDER_TOP_FLANGE_THICKNESS, KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
            KEY_MP_GIRDER_WEB_THICKNESS
        """
        import math
        from .initial_sizing import BridgeConfigurationSolver
        from osdagbridge.core.utils.common import SAIL_APPROVED_THICKNESS_VALUES

        inp = self.input_dict
        if str(inp.get(KEY_DESIGN_MODE, '')).strip() != 'Optimized':
            return

        sail_mm = sorted(float(s) for s in SAIL_APPROVED_THICKNESS_VALUES)

        def _snap_up_to_sail(value_mm: float) -> float:
            """Smallest SAIL-approved thickness >= value_mm.

            If value_mm exceeds the largest SAIL value, use value_mm itself
            (no clamping to the SAIL maximum).
            """
            for s in sail_mm:
                if s >= value_mm:
                    return s
            return value_mm

        span  = float(inp[KEY_SPAN])
        count = self._girder_count()

        _DIM_KEYS = [
            (KEY_MP_GIRDER_DEPTH,                   'D'),
            (KEY_MP_GIRDER_WEB_DEPTH,               'd_web'),
            (KEY_MP_GIRDER_TOP_FLANGE_WIDTH,        'B_top'),
            (KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH,     'B_bot'),
            (KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,    't_f_top'),
            (KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS, 't_f_bot'),
            (KEY_MP_GIRDER_WEB_THICKNESS,           't_w'),
        ]

        solver = BridgeConfigurationSolver(
            carriageway_width=float(inp.get(KEY_CARRIAGEWAY_WIDTH))
        )

        def _resolve_one(full_key: str, initial_sizing_mm: float) -> None:
            raw = inp.get(full_key)
            if isinstance(raw, list) and raw:
                list_min = min(float(v) for v in raw)
                list_max = max(float(v) for v in raw)
                resolved_mm = min(list_min, list_max, initial_sizing_mm)
                inp[full_key] = math.floor(resolved_mm) / 1000.0  # floor in mm, store as m
            elif isinstance(raw, str):
                # "All" → snap initial sizing up to the next SAIL-approved thickness.
                inp[full_key] = _snap_up_to_sail(initial_sizing_mm) / 1000.0
            # float mm value — left for _convert_girder_dims_mm_to_m to divide by 1000

        for gi in range(count):
            suffix   = f".G{gi + 1}.M1"
            symmetry = inp.get(f"{KEY_MP_GIRDER_SYMMETRY}{suffix}")
            props    = solver.compute_section_properties(span=span, symmetry=symmetry)

            for base_key, prop_key in _DIM_KEYS:
                initial_sizing_mm = props[prop_key] * 1e3  # m → mm
                _resolve_one(f"{base_key}{suffix}", initial_sizing_mm)
                # Legacy scalar (un-suffixed) key, resolved first by no-index
                # consumers (e.g. SteelSection); use the first girder's sizing.
                if gi == 0:
                    _resolve_one(base_key, initial_sizing_mm)

    def _convert_girder_dims_mm_to_m(self) -> None:
        """
        Convert per-girder dimensional keys from mm back to SI metres in
        input_dict before the design pipeline consumes them.

        defaults.py stores these keys in mm for UI display. The analyser,
        designer, and all section-property helpers expect SI metres.

        Keys converted for ALL design modes (always numeric mm):
            KEY_MP_GIRDER_DEPTH, KEY_MP_GIRDER_WEB_DEPTH,
            KEY_MP_GIRDER_TOP_FLANGE_WIDTH, KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH

        Keys converted only for non-Optimized mode (numeric mm). Optimized mode
        stores "All" for these and _resolve_optimized_bounds_to_mm handles them:
            KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
            KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
            KEY_MP_GIRDER_WEB_THICKNESS
        """
        _DIM_KEYS_ALL_MODES = [
            KEY_MP_GIRDER_DEPTH,
            KEY_MP_GIRDER_WEB_DEPTH,
            KEY_MP_GIRDER_TOP_FLANGE_WIDTH,
            KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH,
        ]
        _DIM_KEYS_NON_OPTIMIZED = [
            KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
            KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
            KEY_MP_GIRDER_WEB_THICKNESS,
        ]

        inp = self.input_dict
        is_optimized = str(inp.get(KEY_DESIGN_MODE, '')).strip() == 'Optimized'
        count = self._girder_count()

        keys_to_convert = list(_DIM_KEYS_ALL_MODES)
        if not is_optimized:
            keys_to_convert.extend(_DIM_KEYS_NON_OPTIMIZED)

        def _to_m(full_key: str) -> None:
            val = inp.get(full_key)
            if val is None:
                return
            try:
                inp[full_key] = float(val) / 1000.0
            except (ValueError, TypeError):
                pass  # leave non-numeric strings ("All") for _resolve_optimized_bounds_to_mm

        for base_key in keys_to_convert:
            # The legacy scalar (un-suffixed) key must be converted too: SteelSection
            # and other no-index consumers resolve it FIRST via resolve_girder_value,
            # so leaving it in mm yields a mm×1000 unit blow-up (negative web depth).
            _to_m(base_key)
            for gi in range(count):
                _to_m(f"{base_key}.G{gi + 1}.M1")

    def _run_stage(self, stage_num: str, func, *args, **kwargs):
        # Check for user cancel before entering each stage, then emit start/complete markers
        bridge_logger.check_cancel()
        bridge_logger.stage_start(stage_num)
        result = func(*args, **kwargs)
        bridge_logger.stage_complete(stage_num)
        return result

    def _validate_inputs(self):
        """Perform strict validation on essential input dictionary keys."""
        inp = self.input_dict
        required_keys = [
            KEY_SPAN,
            KEY_TS_OVERALL_WIDTH,
            KEY_TS_NO_OF_GIRDERS,
            KEY_TS_GIRDER_SPACING,
        ]
        missing = [k for k in required_keys if k not in inp or inp[k] is None or str(inp[k]).strip() == ""]
        if missing:
            raise ValueError(f"Missing required input parameters: {', '.join(missing)}")

        span = float(inp[KEY_SPAN])
        if span <= 0:
            raise ValueError(f"Span must be strictly positive, got {span}.")
        n_girders = int(inp[KEY_TS_NO_OF_GIRDERS])
        if n_girders < 2:
            raise ValueError(f"Minimum 2 girders required, got {n_girders}.")
        spacing = float(inp[KEY_TS_GIRDER_SPACING])
        if spacing <= 0:
            raise ValueError(f"Girder spacing must be positive, got {spacing}.")

    def _solve_bridge_layout(self):
        """Snapshot input_dict into mutable output_dict for the pipeline."""
        self.output_dict = dict(self.input_dict)
        
    def _stage_grillage_setup(self):
        self._build_dtos()
        self.setup_grillage()

    def _stage_load_combinations(self):
        bridge_logger.sub_step("Running initial analysis for live load envelope...")
        dataset_initial = self.analyze()
        
        bridge_logger.sub_step("Creating governing LL load case...")
        self.create_governing_ll_load_case(dataset_initial, partial_safety_factor=1.0)

        bridge_logger.sub_step("Creating braking load case...")
        self.create_braking_load_case()

        bridge_logger.sub_step("Creating DL+LL combination...")
        self.create_dl_ll_combination(dl_factor=1.0, ll_factor=1.0)
        
        bridge_logger.check_cancel()
        bridge_logger.sub_step("Creating ULS and SLS combinations...")
        self.create_uls_combinations()
        
        self.create_sls_combinations()

    def _stage_cad_generation(self):
        # Validate that the CAD parameter DTO can be assembled, but do NOT build
        # the OCC solid model here: the desktop 3D viewer regenerates its own
        # copy from these parameters at render time (cad_3d.render_3d_cad), and
        # the copy previously stored on self.cad_components had no consumers —
        # it just kept a second full solid model resident until release().
        self.get_3d_cad_parameters()
        bridge_logger.sub_step("CAD parameters prepared; geometry is built by the viewer at render time.")

    def _stage_transverse_design(self):
        self.crossbracing_design_results = self._design_cross_bracing_members()
        self.output_dict["crossbracing_design_results"] = self.crossbracing_design_results
        self.end_diaphragm_design_results = self._design_end_diaphragm_members()
        self.output_dict["end_diaphragm_design_results"] = self.end_diaphragm_design_results
        return self.crossbracing_design_results

    def design(self) -> None:
        """
        Run the full analysis/design pipeline.
        Orchestrates the 14 linear stages mapping exactly to the revised architecture.
        """
        bridge_logger.analysis_start()

        # Log memory at the start of every design so per-iteration growth is visible.
        log_memory("design: START")
        # Mark the Python-allocation baseline (opt-in via OSDAGBRIDGE_MEM_TRACE=1) so release()
        # can name the top Python growers per cycle — the decisive Python-vs-native leak test.
        tracemalloc_mark_start()

        # Release the previous run's OpenSeesPy domain + cached datasets before rebuilding,
        # so a redesign (even while the input dock is still locked) starts clean.
        # set_input() has already run, so input_dict is untouched by this.
        self.memory.release()

        try:
            # Pre-stage: Unit conversions (must run before validation)
            self._resolve_optimized_bounds_to_mm()
            self._convert_girder_dims_mm_to_m()
            
            # Stage 1: Input Validation
            self._run_stage("1", self._validate_inputs)
            
            # Stage 2: Bridge Layout Solving
            self._run_stage("2", self._solve_bridge_layout)
            
            # Stage 3: Grillage Setup
            self._run_stage("3", self._stage_grillage_setup)
            
            # Stage 4A: Dead Load Application
            self._run_stage("4A", self.add_dead_loads)
            
            # Stage 4B: Live Load Application
            self._run_stage("4B", self.add_live_loads)
            
            # Stage 4C: Wind Load Application
            self._run_stage("4C", self.add_wind_loads)
            
            # Stage 4D: Temperature Load Application
            self._run_stage("4D", self.add_temperature_load)
            
            # Stage 4E: Seismic Load Application
            self._run_stage("4E", self.add_seismic_loads)
            
            # Stage 4F: Load Combination Envelope
            self._run_stage("4F", self._stage_load_combinations)
            
            # Stage 4G: Structural Analysis
            dataset = self._run_stage("4G", self._reanalyze_with_dedup)
            dataset = self.create_envelope_load_case(dataset)
            dataset = self._drop_moving_increment_cases(dataset)

            # Drop the raw ospgrillage per-load-case records as soon as the
            # deduplicated dataset is cached: everything downstream (design checks,
            # get_result_data, plots, output dock) reads that cached dataset, so
            # holding the records through stages 5-8 only inflates the peak RSS.
            self.memory.clear_intermediate_results()
            
            # Print Summary
            inp = self.input_dict
            print(
                f"\n{'-'*60}\n"
                f"  PLATE GIRDER BRIDGE - DESIGN SUMMARY\n"
                f"{'-'*60}\n"
                f"  Span                  : {float(inp[KEY_SPAN]):.1f} m\n"
                f"  Overall width         : {inp[KEY_TS_OVERALL_WIDTH]:.3f} m\n"
                f"  No. of girders        : {inp[KEY_TS_NO_OF_GIRDERS]}\n"
                f"  Girder spacing        : {inp[KEY_TS_GIRDER_SPACING] * 1e3:.1f} mm\n"
                f"  Deck overhang         : {inp[KEY_TS_DECK_OVERHANG] * 1e3:.1f} mm\n"
            )
            # Per-girder cross-section block (each girder may differ).
            for gi in range(self._girder_count()):
                v = lambda key: self._girder_value(key, gi)
                print(
                    f"{'-'*60}\n"
                    f"  GIRDER G{gi + 1} CROSS-SECTION (mm) / PROPERTIES (SI)\n"
                    f"{'-'*60}\n"
                    f"  Total depth      D    : {v(KEY_MP_GIRDER_DEPTH)                   * 1e3:.1f}\n"
                    f"  Web depth        d_w  : {v(KEY_MP_GIRDER_WEB_DEPTH)               * 1e3:.1f}\n"
                    f"  Web thickness    t_w  : {v(KEY_MP_GIRDER_WEB_THICKNESS)           * 1e3:.1f}\n"
                    f"  Top flange width B_ft : {v(KEY_MP_GIRDER_TOP_FLANGE_WIDTH)        * 1e3:.1f}\n"
                    f"  Top flange thk   T_ft : {v(KEY_MP_GIRDER_TOP_FLANGE_THICKNESS)    * 1e3:.1f}\n"
                    f"  Bot flange width B_fb : {v(KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH)     * 1e3:.1f}\n"
                    f"  Bot flange thk   T_fb : {v(KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS) * 1e3:.1f}\n"
                    f"  Area   A  : {v(KEY_MP_GIRDER_SECTIONAL_AREA):.6f} m^2\n"
                    f"  I_z       : {v(KEY_MP_GIRDER_SECTIONAL_IZ):.6f} m^4\n"
                    f"  I_y       : {v(KEY_MP_GIRDER_SECTIONAL_IY):.6f} m^4\n"
                    f"  I_t (J)   : {v(KEY_MP_GIRDER_TORSION_CONSTANT_IT):.6f} m^3\n"
                    f"{'-'*60}"
                )

            # Built before Stage 5: the designer reads result_data["girders"] for the
            # canonical G1..Gn girder set (edge members already excluded), the same
            # source CrossBracingForces uses. Safe here — the analysis completed in
            # Stage 4G above, and nothing in Stage 5 mutates the OpenSees model.
            self.result_data = self.grillage_model.get_result_data()

            # Stage 5: Girder Design Checks
            self._run_stage("5", self._run_dcr_checks, dataset)

            if self.dump_json:
                from osdagbridge.core.bridge_types.plate_girder.results_data import dump_full_data
                dump_full_data(
                    self.grillage_model.model,
                    edge_dist=self.grillage_model.edge_dist or 0.0,
                    # Use the envelope-augmented dataset so the Envelope ULS / Envelope
                    # SLS pseudo load cases appear in the dump; falls back to
                    # model.get_results() if absent.
                    dataset=getattr(self.grillage_model, "_deduplicated_results", None),
                )

            # Stage 6: Deck Slab Design
            self.deck_design_results = self._run_stage("6", self.design_deck_slab)
            
            # Stage 7: Transverse Member Design
            self.crossbracing_design_results = self._run_stage("7", self._stage_transverse_design)
            
            self.bridge_component_solver()
            self.compute_load_effects_cache()
            for _gi, _vals in (self._deflections_cache or {}).items():
                _live = _vals.get("live_mm")
                _total = _vals.get("total_mm")
                if _live is not None:
                    self.output_dict[f"{KEY_SD_DEFL_LIVE}.{_gi}"] = round(float(_live), 3)
                if _total is not None:
                    self.output_dict[f"{KEY_SD_DEFL_TOTAL}.{_gi}"] = round(float(_total), 3)
            
            # Stage 8: 3D CAD & Drawing Generation
            self._run_stage("8", self._stage_cad_generation)

            # Freeze output_dict — no further writes allowed after this point
            self.output_dict = types.MappingProxyType(self.output_dict)
            # Log memory after the design completes so growth per iteration is visible.
            log_memory("design: COMPLETE")
            bridge_logger.analysis_complete()

        except Exception as e:
            bridge_logger.analysis_failed(str(e))
            raise

    def reset(self) -> None:
        # Release all heavy analysis memory (unlock / app-close entry point).
        self.memory.release()

    def _export_cad_figures(self, cad_generator) -> dict:
        """
        Export 4 CAD views to the fixed internal Images folder.
        Returns { ReportFigures_attr: absolute_path } for each view.
        Returns {} on any failure. Never raises.
        """
        import os
        import logging
        _log = logging.getLogger(__name__)

        # ── Resolve save path: core/data/ResourceFiles/Images/ ───────
        resource_files_dir = os.path.normpath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', '..', '..', 'core', 'data', 'ResourceFiles'
        ))
        figures_dir = os.path.join(resource_files_dir, 'Images')
        if not os.path.exists(figures_dir):
            os.makedirs(figures_dir)

        if not cad_generator:
            return {}

        core = cad_generator

        # ── Verify model has been generated ───────────────────────────
        if not getattr(core, 'model_data', None):
            _log.warning(
                "_export_cad_figures: model_data is empty — "
                "run design first")
            return {}

        # ── Create headless Viewer3d — no window, no auto-export ─────
        try:
            from OCC.Display.OCCViewer import Viewer3d
            off_display = Viewer3d()
            off_display.Create()          # NO arguments — avoids TypeError
            off_display.SetModeShaded()
        except Exception as exc:
            _log.warning(
                "_export_cad_figures: Viewer3d init failed: "
                "%s — export skipped", exc)
            return {}

        if not hasattr(off_display, 'ExportToImage'):
            _log.warning(
                "_export_cad_figures: off_display has no ExportToImage "
                "— export skipped")
            return {}

        # ── Stub cad_widget for off-screen rendering ─────────────────
        # osdag_display_shape() calls canvas.model_ais_objects — provide it.
        class _OffscreenCanvas:
            def __init__(self):
                self.model_ais_objects = {}
        off_canvas = _OffscreenCanvas()

        # ── Save originals BEFORE touching anything ──────────────────
        original_display    = getattr(core, 'display', None)
        original_cad_widget = getattr(core, 'cad_widget', None)
        original_component  = getattr(core, 'component', None)

        figure_paths = {}

        # Freeze GC around this guard-less headless viewer's render/teardown (Shiboken-GC segfault guard).
        import gc
        _gc_was_enabled = gc.isenabled()
        gc.disable()

        try:
            # ── Substitute + render all components onto off-screen display
            core.display    = off_display
            core.cad_widget = off_canvas

            for component in ["Girder", "Stiffener", "Cross Bracing",
                              "Deck", "Crash Barrier", "Railing", "Median"]:
                try:
                    if hasattr(core, 'display_3dModel'):
                        core.display_3dModel(component)
                except Exception as exc:
                    _log.debug("component %s skipped: %s", component, exc)

            off_display.FitAll()

            # View 1 — Isometric / 3D
            try:
                off_display.set_bg_gradient_color(
                    [235, 235, 235], [195, 195, 195])
                p = os.path.join(figures_dir, 'girder_3d.png')
                off_display.ExportToImage(p)
                if os.path.exists(p):
                    figure_paths['girder_3d'] = os.path.abspath(p)
            except Exception as exc:
                _log.warning("3D view export failed: %s", exc)

            # View 2 — Front
            try:
                off_display.View_Front()
                off_display.FitAll()
                off_display.set_bg_gradient_color(
                    [235, 235, 235], [195, 195, 195])
                p = os.path.join(figures_dir, 'girder_front.png')
                off_display.ExportToImage(p)
                if os.path.exists(p):
                    figure_paths['girder_front'] = os.path.abspath(p)
            except Exception as exc:
                _log.warning("Front view export failed: %s", exc)

            # View 3 — Top
            try:
                off_display.View_Top()
                off_display.FitAll()
                off_display.set_bg_gradient_color(
                    [235, 235, 235], [195, 195, 195])
                p = os.path.join(figures_dir, 'girder_top.png')
                off_display.ExportToImage(p)
                if os.path.exists(p):
                    figure_paths['girder_top'] = os.path.abspath(p)
            except Exception as exc:
                _log.warning("Top view export failed: %s", exc)

            # View 4 — Side (Right)
            try:
                off_display.View_Right()
                off_display.FitAll()
                off_display.set_bg_gradient_color(
                    [235, 235, 235], [195, 195, 195])
                p = os.path.join(figures_dir, 'girder_end.png')
                off_display.ExportToImage(p)
                if os.path.exists(p):
                    figure_paths['girder_end'] = os.path.abspath(p)
            except Exception as exc:
                _log.warning("Side view export failed: %s", exc)

        finally:
            # ── CRITICAL: isolation cleanup — ALWAYS runs ────────────
            # Ordered teardown: Remove each AIS's C++ ref before EraseAll, then restore GC.
            try:
                ctx = off_display.Context
                for ais_list in off_canvas.model_ais_objects.values():
                    items = ais_list if isinstance(ais_list, (list, tuple)) else [ais_list]
                    for ais in items:
                        try:
                            if ctx.IsDisplayed(ais):
                                ctx.Remove(ais, False)
                        except Exception:
                            pass
                off_canvas.model_ais_objects.clear()
            except Exception:
                pass
            try:
                off_display.EraseAll()
            except Exception:
                pass
            core.display    = original_display
            core.cad_widget = original_cad_widget
            core.component  = original_component
            if _gc_was_enabled:
                gc.enable()

        _log.info(
            "_export_cad_figures: exported %d view(s) to %s",
            len(figure_paths), figures_dir)
        return figure_paths


    def generate_design_report(self, request, cad_generator, is_preview=False):
        """Compile the final PDF design report."""
        from osdagbridge.core.reports.report_generator import build_report_payload, generate_report

        report_inputs = self.input_dict.copy()
        output_dict   = dict(self.output_dict)  # MappingProxyType → dict

        # ── Chapter 4: analysis summary for Tables ──────────────────
        lc_sum  = getattr(self, '_lc_summary',       None)
        rxn_sum = getattr(self, '_reaction_summary',  None)
        if lc_sum is not None or rxn_sum is not None:
            output_dict['analysis_summary'] = {
                'load_cases': lc_sum  or {},
                'reactions':  rxn_sum or {},
            }

        payload = build_report_payload(request, report_inputs, output_dict)

        # Collect figure bytes into payload.figure_data — no disk writes here
        figure_data = {}
        if isinstance(cad_generator, dict):
            figure_data.update(cad_generator.get('figure_data', {}))

        payload.figure_data = figure_data  # handed off; generate_report clears it after writing

        return generate_report(payload, request)

    def _build_dtos(self) -> None:
        """Construct GrillageGeometry and DeckLayoutProperties DTOs from solved results."""
        inp = self.input_dict
        span = float(inp[KEY_SPAN])
        # n_t: transverse grid lines — span divided by cross-bracing spacing, rounded to nearest odd integer with minimum of 3 (1 at each end + at least 1 internal for bracing)
        n_t = max(3, (int(round(span / (DEFAULT_CROSS_BRACING_SPACING)*2) + 1)))

        deck_overhang = float(inp[KEY_TS_DECK_OVERHANG])
        # When there is an overhang, the two edge beams add 2 extra longitudinal
        # grid lines on top of the structural girder count.
        n_l = int(inp[KEY_TS_NO_OF_GIRDERS]) + (2 if deck_overhang > 0 else 0)

        self.grillage_geometry = GrillageGeometry(
            L=span,
            n_l=n_l,
            n_t=n_t,
            edge_dist=deck_overhang,
            ext_to_int_dist=float(inp[KEY_TS_GIRDER_SPACING]),
            angle=self._to_float(KEY_SKEW_ANGLE, 0.0),
        )

        self.deck_layout = DeckLayoutProperties(
            carriageway_width=float(inp[KEY_CARRIAGEWAY_WIDTH]),
            crash_barrier_width=float(DEFAULT_CRASH_BARRIER_WIDTH),
            footpath_width=float(inp[KEY_TS_FOOTPATH_WIDTH]),
            railing_width=float(inp[KEY_RL_WIDTH]),
            median_width=float(inp[KEY_MD_WIDTH]),
            n_footpaths=int(inp[KEY_TS_NO_OF_FOOTPATHS]),
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Bridge component solver
    # ─────────────────────────────────────────────────────────────────────────

    def bridge_component_solver(self) -> None:
        """
        Single entry-point that computes all derived bridge-component
        geometry values and writes them into ``self.output_dict``.

        **How to add a new component in the future**

        1. Create a private ``_solve_<component>(self)`` method below.
        2. Add **one line** calling it here.

        ``bridge_component_solver()`` is called only **once** from the
        design pipeline; each private sub-method owns its own slice of
        ``output_dict`` and can be developed and tested independently.

        Current components
        ------------------
        * Shear studs  --> ``_solve_shear_studs()``
        """
        self._solve_shear_studs()

        # ── Future components: add one line per component here ────────────────
        # self._solve_deck()
        # self._solve_bearings()
        # self._solve_stiffeners()
        # self._solve_cross_bracing()

    def _solve_shear_studs(self) -> None:
        """
        Compute derived shear-stud geometry values and update ``output_dict``.

        Keys written
        ------------
        KEY_DS_STUD_HEAD_DIAMETER
            Minimum stud head diameter = 1.5 x d_stud
            [IRC 22:2015 - Cl. 606.6 - Detailing of Shear Connectors]

        KEY_DS_STUD_HEAD_HEIGHT
            Minimum stud head height = 0.667 x d_stud
            [IS 3935:1966 - Composite Construction]

        Raises
        ------
        ValueError
            If ``KEY_DS_STUD_DIAMETER`` is missing or cannot be parsed as float.
        """
        # KEY_DS_STUD_DIAMETER is always populated by _update_design_options_defaults()
        d_stud_mm = float(self.output_dict[KEY_DS_STUD_DIAMETER])

        # ── Compute geometry values ───────────────────────────────────────────
        # Minimum head diameter  [IRC 22:2015 - Cl. 606.6]
        head_d_mm = min_stud_head_diameter(d_stud_mm)

        # Minimum head height    [IS 3935:1966]
        head_h_mm = min_stud_head_height(d_stud_mm)

        # ── Write results into output_dict ────────────────────────────────────
        self.output_dict.update({
            KEY_DS_STUD_HEAD_DIAMETER: head_d_mm,
            KEY_DS_STUD_HEAD_HEIGHT:   head_h_mm,
        })

    # ─────────────────────────────────────────────────────────────────────────
    # Grillage model setup
    # ─────────────────────────────────────────────────────────────────────────

    def setup_grillage(self) -> None:
        """
        Initialise and build the BridgeGrillageModel in order:
          1. set_geometry   — grillage dimensions and cross-section layout
          2. create_sections — section properties for all member types
          3. create_material — steel material from the DB-backed girder selection
          4. assign_members  — pair sections with material to create member objects
          5. create_model    — build and run the OpenSees grillage model

        Must be called after design() has populated grillage_geometry,
        deck_layout, and section_props.
        """
        self.grillage_model.set_geometry(self.grillage_geometry, self.deck_layout)
        # Build one SectionProperties per main girder. When the input dict carries
        # per-girder dynamic keys (``<base>.G{i}.M1``) the girders may differ;
        # otherwise every girder falls back to the shared scalar section.
        n_girders = self._girder_count()
        girder_sections = [self._girder_section(i) for i in range(n_girders)]
        self.grillage_model.create_sections(
            girder_sections=girder_sections,
            edge_longitudinal=self._girder_section(),
            transverse=self._transverse_section(),
            end_transverse=self._end_transverse_section(),
        )
        self.material_props = self._build_material_props()
        self.grillage_model.create_material(self.material_props)
        self.grillage_model.assign_members()
        self.grillage_model.create_model()

    def _lookup_material(self, material_name: str, property: str) -> float:
        """
        Query the Osdag SQLite database for the specified property of the given
        material name.  Returns the property value in its respective units.  Falls back to the default value
        if the DB is missing or the material is not found.
        """
        if not _DB_PATH.exists():
            raise LookupError(f"Material database not found at {_DB_PATH} in PlateGirderBridge._lookup_material")

        # Choose the table: rebar (Fe-grades), structural steel (E-grades), or concrete
        if material_name.startswith('Fe'):
            table = 'Rebar_Grade_Properties'
        elif material_name[0] == 'E':
            table = 'Steel_Grade_Properties'
        else:
            table = 'Concrete_Grade_Properties'

        try:
            con = sqlite3.connect(_DB_PATH)
            cur = con.cursor()
            cur.execute(
                f'SELECT "{property}" FROM {table} WHERE "Grade" = ?',
                (material_name,),
            )
            row = cur.fetchone()
            con.close()
            if row:
                if property == "Modulus of Elasticity":     # Elastic modulus (Pa)
                    return float(row[0]) * GPa
                elif property == "Poisson's Ratio":         # Poisson's ratio (unitless)
                    return float(row[0])
                elif property == "Density":                 # Unit weight (N/m³)
                    return float(row[0]) * N / m ** 3
                elif property == "Yield Strength":          # Yield strength (Pa)
                    return float(row[0]) * MPa              # DB stores MPa as integer → convert to Pa
                elif property == "Ultimate Tensile Strength":
                    return float(row[0]) * MPa
                elif property in ("fck", "fctm", "Ecm", "fy", "fu", "Es"):  # Concrete (MPa/GPa) and rebar (MPa) properties — returned as plain numbers
                    return float(row[0])
                else:
                    raise SyntaxError(f"Unknown property '{property}' requested in table '{table}' in PlateGirderBridge._lookup_material")

        except sqlite3.Error:
            raise LookupError(f"Error querying material database in PlateGirderBridge._lookup_material: {sqlite3.Error}")

    def _build_material_props(self) -> MaterialProperties:
        """Build a MaterialProperties from the selected girder material in input_dict.
        
        For DB grades (e.g. 'E 250A') properties are looked up from the SQLite database.
        For custom grades (those not found in the DB) the sub-values already stored in
        input_dict (material.girder.e, .fy, .fu, .poisson, .g) are used directly.
        This prevents a NoneType crash when the user has entered a custom material.
        """
        _DEFAULT_DENSITY = 78500.0  # N/m³ — fallback when not available in DB

        # ── Steel (Girder) ────────────────────────────────────────────────────
        steel_grade = str(self.input_dict.get(KEY_GIRDER, "")).strip()
        e = self._lookup_material(steel_grade, "Modulus of Elasticity")
        if e is None:
            # Custom grade — read from the material sub-keys populated by the UI
            raw_e = self.input_dict.get(KEY_MATERIAL_GIRDER_E)
            e = float(raw_e) * GPa if raw_e not in (None, "") else _STEEL_E0

        v = self._lookup_material(steel_grade, "Poisson's Ratio")
        if v is None:
            raw_v = self.input_dict.get(KEY_MATERIAL_GIRDER_POISSON)
            v = float(raw_v) if raw_v not in (None, "") else 0.3

        rho = self._lookup_material(steel_grade, "Density")
        if rho is None:
            rho = _DEFAULT_DENSITY

        fy = self._lookup_material(steel_grade, "Yield Strength")
        if fy is None:
            raw_fy = self.input_dict.get(KEY_MATERIAL_GIRDER_FY)
            fy = float(raw_fy) * MPa if raw_fy not in (None, "") else _STEEL_FY_DEFAULT

        fu = self._lookup_material(steel_grade, "Ultimate Tensile Strength")
        if fu is None:
            raw_fu = self.input_dict.get(KEY_MATERIAL_GIRDER_FU)
            fu = float(raw_fu) * MPa if raw_fu not in (None, "") else fy * 1.25

        steel_prop = SteelProperties(
            grade=steel_grade,
            E=e,
            v=v,
            rho=rho,
            Fy=fy,
            Fu=fu,
            E0=_STEEL_E0,
            b=_STEEL_B,
        )

        # ── Concrete (Deck) ───────────────────────────────────────────────────
        concrete_grade = str(self.input_dict.get(KEY_DECK_CONCRETE_GRADE_BASIC, "")).strip()
        fck = self._lookup_material(concrete_grade, "fck")
        if fck is None:
            raw_fck = self.input_dict.get(KEY_MATERIAL_DECK_FCK)
            fck = float(raw_fck) if raw_fck not in (None, "") else 25.0

        fctm = self._lookup_material(concrete_grade, "fctm")
        if fctm is None:
            raw_fctm = self.input_dict.get(KEY_MATERIAL_DECK_FCTM)
            fctm = float(raw_fctm) if raw_fctm not in (None, "") else 2.2

        Ecm = self._lookup_material(concrete_grade, "Ecm")
        if Ecm is None:
            raw_ecm = self.input_dict.get(KEY_MATERIAL_DECK_ECM)
            Ecm = float(raw_ecm) if raw_ecm not in (None, "") else 30.0

        concrete_prop = ConcreteProperties(
            grade=concrete_grade,
            fck=fck,
            fctm=fctm,
            Ecm=Ecm,
        )

        return MaterialProperties(
            steel_prop=steel_prop,
            concrete_prop=concrete_prop,
        )

    def _girder_count(self) -> int:
        """Number of structural main girders (excludes overhang edge beams)."""
        try:
            return max(1, int(self.input_dict[KEY_TS_NO_OF_GIRDERS]))
        except (KeyError, TypeError, ValueError):
            return 1

    def _girder_value(self, base_key: str, i: int | None = None):
        """
        Read a girder property from ``input_dict`` (see ``resolve_girder_value``
        for the per-girder/scalar resolution order).
        """
        return resolve_girder_value(self.input_dict, base_key, i)

    def _girder_section(self, i: int | None = None) -> SectionProperties:
        """
        Build a SectionProperties for main girder ``i`` (0-based).

        ``i=None`` builds from the representative (first) girder — used for edge
        beams and as the uniform fallback.
        """
        g = lambda key: self._girder_value(key, i)
        Az = g(KEY_MP_GIRDER_WEB_DEPTH) * g(KEY_MP_GIRDER_WEB_THICKNESS)
        Ay = 2 * g(KEY_MP_GIRDER_TOP_FLANGE_WIDTH) * g(KEY_MP_GIRDER_TOP_FLANGE_THICKNESS)
        return SectionProperties(
            A=g(KEY_MP_GIRDER_SECTIONAL_AREA),
            J=g(KEY_MP_GIRDER_TORSION_CONSTANT_IT),
            Iz=g(KEY_MP_GIRDER_SECTIONAL_IZ),
            Iy=g(KEY_MP_GIRDER_SECTIONAL_IY),
            Az=Az,
            Ay=Ay,
        )

    def _transverse_section(self) -> SectionProperties:
        """Build a SectionProperties for the transverse deck slab (half-depth, unit width)."""
        g = lambda key: self._girder_value(key)  # representative (first) girder
        t  = g(KEY_MP_GIRDER_DEPTH) / 2
        Az = t * g(KEY_MP_GIRDER_WEB_THICKNESS)
        return SectionProperties(
            A=g(KEY_MP_GIRDER_SECTIONAL_AREA) / 2,
            J=g(KEY_MP_GIRDER_TORSION_CONSTANT_IT) / 2,
            Iz=g(KEY_MP_GIRDER_SECTIONAL_IZ) / 2,
            Iy=g(KEY_MP_GIRDER_SECTIONAL_IY) / 2,
            Az=Az,
            Ay=Az,
        )

    def _end_transverse_section(self) -> SectionProperties:
        """Build a SectionProperties for the end transverse slab (quarter-depth)."""
        g = lambda key: self._girder_value(key)  # representative (first) girder
        Az = g(KEY_MP_GIRDER_WEB_DEPTH) / 2 * g(KEY_MP_GIRDER_WEB_THICKNESS)
        Ay = g(KEY_MP_GIRDER_TOP_FLANGE_WIDTH) * g(KEY_MP_GIRDER_TOP_FLANGE_THICKNESS)
        return SectionProperties(
            A=g(KEY_MP_GIRDER_SECTIONAL_AREA) / 4,
            J=g(KEY_MP_GIRDER_TORSION_CONSTANT_IT) / 4,
            Iz=g(KEY_MP_GIRDER_SECTIONAL_IZ) / 4,
            Iy=g(KEY_MP_GIRDER_SECTIONAL_IY) / 4,
            Az=Az,
            Ay=Ay,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Dead loads — permanent loads applied after the grillage model is built
    # ─────────────────────────────────────────────────────────────────────────

    def add_dead_loads(self) -> None:
        """
        Apply all permanent dead loads to the grillage model in order:
          1. Girder self weight     — line load along each longitudinal member
          2. Deck slab              — patch load over the full deck area
          3. Wearing course         — patch load over the carriageway area
          4. Footpath               — patch load on footpath strips (skipped if none)
          5. Crash barrier          — line load at each barrier centreline (skipped if none)
          6. Railing                — line load at each railing centreline (skipped if none)
          7. Median                 — line load at median centreline (skipped if none)
          8. DL combination         — combines all above into a single "DL" load case

        Must be called after setup_grillage() has built and registered the model.
        """
        deck_t_m = deck_thickness_from_inputs(self.input_dict, _DEFAULT_DECK_THICKNESS_MM)
        wc_t_m = float(self.input_dict[KEY_WC_THICKNESS]) / 1000.0
        wc_rho  = float(self.input_dict[KEY_WC_DENSITY])
        barrier_load_kN_m = crash_barrier_load_from_inputs(self.input_dict)
        railing_load_kN_m = railing_load_from_inputs(self.input_dict)

        model = self.grillage_model
        model.create_self_weight_load()
        model.create_deck_load(slab_thickness_m=deck_t_m)
        model.create_wearing_course_load(thickness_m=wc_t_m, density_kN_m3=wc_rho, partial_safety_factor=1.0)
        model.create_footpath_load()
        model.create_crash_barrier_load(barrier_load_kN_per_m=barrier_load_kN_m)
        model.create_railing_load(railing_load_kN_per_m=railing_load_kN_m)
        model.create_median_load()
        model.create_dead_load_combination(partial_safety_factor=1.0)

    # ─────────────────────────────────────────────────────────────────────────
    # Live loads — vehicle and moving loads applied after the grillage model
    # ─────────────────────────────────────────────────────────────────────────

    def add_live_loads(self) -> None:
        """
        Apply all live loads to the grillage model in order:
          1. Vehicle load cases — static placements per IRC:6 Table 6A
          2. Moving vehicle load cases — moving paths for each vehicle
          3. Fatigue vehicle — IRC:6 Cl.204.6 truck on the carriageway centreline
          4. Moving fatigue vehicle — the fatigue truck traversing the span

        The braking load (IRC:6 Cl.211) is not created here: it derives from
        whichever case turns out to govern, so it is built in
        _stage_load_combinations() once create_governing_ll_load_case() has run.

        Must be called after setup_grillage() has built and registered the model.
        """
        model = self.grillage_model
        model.add_vehicle_load_cases_from_combinations()
        bridge_logger.check_cancel()

        model.create_moving_vehicle_load_cases()
        bridge_logger.check_cancel()

        model.add_fatigue_vehicle_load_case()
        bridge_logger.check_cancel()

        model.create_moving_fatigue_load_cases()

    # ─────────────────────────────────────────────────────────────────────────
    # Wind loads — applied after dead and live loads, before analysis
    # ─────────────────────────────────────────────────────────────────────────

    def add_wind_loads(self) -> None:
        """
        Apply wind loads to the grillage model per IRC:6-2017 Cl.209.3.3–209.3.5.

        Wind parameters are read from ``self.input_dict`` (the
        Additional Inputs dialog).  Any parameter not yet supplied falls back
        to a sensible default so the method is always safe to call.

        Load cases created (delegated to BridgeGrillageModel.create_wind_load):
          - ``"WL Transverse"``   — FT line load on the two exterior girders
          - ``"WL Longitudinal"`` — FL = 0.25 FT patch load over the full deck
          - ``"WL Uplift"``       — Pz × G × CL patch load (upward) on the deck
          - ``"1.0 WL"``          — combined load case with partial_safety_factor = 1.0
        """
        ai  = self.additional_inputs
        inp = self.input_dict

        # ── Wind speed / terrain ─────────────────────────────────────────
        basic_wind_speed = float(ai.get("basic_wind_speed") or 33.0)
        if basic_wind_speed == 0.0:
            bridge_logger.info("Wind load absent (speed=0); skipping.")
            return

        height_for_pz = float(ai.get("avg_exposed_height") or 10.0)
        terrain_raw   = str(ai.get("terrain_type") or "Plain Terrain")
        terrain       = "plain" if "plain" in terrain_raw.lower() else "obstructed"

        # ── Exposed height components ────────────────────────────────────
        railing_height       = float(ai.get("railing_height")       or 0.0)
        crash_barrier_height = float(ai.get("crash_barrier_height") or 0.0)
        deck_t_m             = deck_thickness_from_inputs(ai, _DEFAULT_DECK_THICKNESS_MM)

        # ── Girder geometry for CD ───────────────────────────────────────
        # Use the governing (deepest) girder for the windward drag depth so a
        # mix of per-girder depths still yields a conservative transverse force.
        n_girders = inp[KEY_TS_NO_OF_GIRDERS]
        d_depth   = max(
            self._girder_value(KEY_MP_GIRDER_DEPTH, i) for i in range(self._girder_count())
        )
        c_spacing = inp[KEY_TS_GIRDER_SPACING]

        self.grillage_model.create_wind_load(
            railing_height=railing_height,
            crash_barrier_height=crash_barrier_height,
            deck_thickness=deck_t_m,
            height_for_pz=height_for_pz,
            terrain=terrain,
            basic_wind_speed=basic_wind_speed,
            girder_section="plate",
            number_of_girders=n_girders,
            c_spacing=c_spacing,
            d_depth=d_depth,
            partial_safety_factor=1.0,
        )

    # ============================================================
    #   Temperature Load Analysis  IRC:6-2017 Cl.215
    # ============================================================

    def analyse_uniform_temperature(
        self,
        max_shade_temp: float,
        min_shade_temp: float,
        girders: list[dict],
        structural_type: str = 'metallic',
        snowbound: bool = False,
        k_fixed: float = 1_000_000.0,
        k_free: float = 100.0,
        s_girder: float | None = None,
        h_diaphragm: float | None = None,
    ) -> list[dict]:
        """
        Restrained axial force, bearing movement and end-diaphragm shear under
        uniform temperature change per IRC:6-2017 Cl.215.2.

        Analysis is performed per girder; girders may have different E_s and A_s.

        Parameters
        ----------
        max_shade_temp : float
            Maximum shade air temperature (°C) from IRC:6-2017 Annexure F / Table 15.
        min_shade_temp : float
            Minimum shade air temperature (°C).
        girders : list of dict
            One entry per girder, each containing:
              'E_s' (float, MPa) — steel elastic modulus
              'A_s' (float, m²)  — steel girder cross-section area
        structural_type : str
            'metallic' (default) or 'other' — controls effective temperature
            derivation per IRC:6-2017 Cl.215.2.
        snowbound : bool
            True if the location is snowbound (metallic structures only).
        k_fixed : float
            Longitudinal stiffness of the fixed bearing (kN/m).
            Default: 1 000 000 kN/m (virtually rigid pot bearing).
        k_free : float
            Longitudinal stiffness of the expansion bearing (kN/m).
            Default: 100 kN/m.
        s_girder : float, optional
            Centre-to-centre girder spacing (m) — for end-diaphragm shear (Step 5).
        h_diaphragm : float, optional
            Height of the end diaphragm (m) — for end-diaphragm shear (Step 5).

        Returns
        -------
        list of dict
            One result dict per girder.  Key output quantities:

            delta_free_rise_m   (m)    free thermal expansion
            delta_free_fall_m   (m)    free thermal contraction
            k_girder_kN_m       (kN/m) girder axial stiffness
            N_temp_rise_kN      (kN)   restrained axial force (rise)
            N_temp_fall_kN      (kN)   restrained axial force (fall)
            bearing_movement_m  (m)    governing bearing design movement
            V_diaphragm_rise_kN (kN)   end-diaphragm transverse shear (rise)
            V_diaphragm_fall_kN (kN)   end-diaphragm transverse shear (fall)
        """
        L = self.L   # span length (m)

        # ── IRC:6-2017 Cl.215.2 — effective bridge temperature range ──────────
        temp_range = IRC6_2017.cl_215_2_effective_bridge_temperature(
            max_temp=max_shade_temp,
            min_temp=min_shade_temp,
            structural_type=structural_type,
            snowbound=snowbound,
        )
        T_max  = temp_range['T_max']            # effective max bridge temperature (°C)
        T_min  = temp_range['T_min']            # effective min bridge temperature (°C)
        T_mean = (T_max + T_min) / 2.0          # mean construction temperature (°C)

        # ── IRC:6-2017 Cl.215.2 — thermal expansion coefficient ──────────────
        alpha = IRC6_2017.cl_215_4_material_properties()['alpha']   # /°C

        # Temperature differentials from mean construction temperature
        delta_T_rise = T_max - T_mean   # °C  rise above mean
        delta_T_fall = T_mean - T_min   # °C  fall below mean

        print(
            f"Uniform temperature (IRC:6-2017 Cl.215.2): "
            f"T_max={T_max:.1f}°C  T_min={T_min:.1f}°C  T_mean={T_mean:.1f}°C  "
            f"alpha={alpha:.2e}/°C  "
            f"delta_T_rise={delta_T_rise:.1f}°C  delta_T_fall={delta_T_fall:.1f}°C"
        )

        results = []

        for idx, girder in enumerate(girders):
            E_s = girder['E_s']   # steel modulus (MPa)
            A_s = girder['A_s']   # steel girder cross-section area (m²)

            # Step 1 — Free thermal expansion / contraction  [m]  — IRC:6-2017 Cl.215.2
            #   delta = alpha × delta_T × L
            delta_free_rise = alpha * delta_T_rise * L   # m
            delta_free_fall = alpha * delta_T_fall * L   # m

            # Step 2 — Girder axial stiffness  [kN/m]
            #   E_s [MPa] × 1000 → [kN/m²];  × A_s [m²] / L [m]  →  kN/m
            k_girder = (E_s * 1000.0 * A_s) / L   # kN/m

            # Step 3 — Restrained axial force via spring compatibility  [kN]
            #   Girder (k_g) + fixed bearing (k_f) + expansion bearing (k_e) in series
            #   k_eff = k_g × k_f × k_e / (k_g×k_f + k_g×k_e + k_f×k_e)
            denom       = (k_girder * k_fixed
                           + k_girder * k_free
                           + k_fixed  * k_free)
            k_eff       = (k_girder * k_fixed * k_free) / denom   # kN/m
            N_temp_rise = k_eff * delta_free_rise   # kN  axial compression on rise
            N_temp_fall = k_eff * delta_free_fall   # kN  axial tension on fall

            # Step 4 — Bearing design movement  [m]
            #   Expansion-end displacement u = N / k_free
            u_free_end_rise  = N_temp_rise / k_free                     # m
            u_free_end_fall  = N_temp_fall / k_free                     # m
            bearing_movement = max(u_free_end_rise, u_free_end_fall)    # m  governing

            # Step 5 — End-diaphragm transverse racking shear  [kN]  (approximate)
            #   V ≈ N_temp × (s_girder / h_diaphragm)
            #   NOTE: approximate 2D frame analogy; use 3D FEM for exact value.
            V_rise = V_fall = None
            if s_girder is not None and h_diaphragm is not None:
                V_rise = N_temp_rise * (s_girder / h_diaphragm)   # kN
                V_fall = N_temp_fall * (s_girder / h_diaphragm)   # kN

            print(
                f"  Girder {idx}: k_girder={k_girder:.0f} kN/m  "
                f"N_rise={N_temp_rise:.2f} kN  N_fall={N_temp_fall:.2f} kN  "
                f"bearing_mov={bearing_movement * 1000:.2f} mm"
            )

            results.append({
                # Identification
                'girder_index':        idx,
                'E_s_MPa':             E_s,
                'A_s_m2':              A_s,
                'clause':              temp_range['clause'],
                # Effective temperatures (°C)
                'T_max':               T_max,
                'T_min':               T_min,
                'T_mean':              T_mean,
                'delta_T_rise':        delta_T_rise,
                'delta_T_fall':        delta_T_fall,
                # Step 1 — free movement (m)
                'delta_free_rise_m':   delta_free_rise,
                'delta_free_fall_m':   delta_free_fall,
                # Step 2 — stiffnesses (kN/m)
                'k_girder_kN_m':       k_girder,
                'k_fixed_kN_m':        k_fixed,
                'k_free_kN_m':         k_free,
                # Step 3 — axial forces (kN)
                'N_temp_rise_kN':      N_temp_rise,
                'N_temp_fall_kN':      N_temp_fall,
                # Step 4 — bearing movement (m)
                'u_free_end_rise_m':   u_free_end_rise,
                'u_free_end_fall_m':   u_free_end_fall,
                'bearing_movement_m':  bearing_movement,
                # Step 5 — end-diaphragm shear (kN); None if geometry not supplied
                'V_diaphragm_rise_kN': V_rise,
                'V_diaphragm_fall_kN': V_fall,
                'diaphragm_note': (
                    'Approximate (3D FEM for exact). '
                    'V = N_temp × (s_girder / h_diaphragm).'
                ) if V_rise is not None else (
                    'Not computed: s_girder or h_diaphragm not provided.'
                ),
            })

        self.temp_uniform_results = results
        return results

    def analyse_temperature_gradient(
        self,
        parts: list[dict],
        h_slab: float,
        E_s: float,
        T_profile_rise: list[tuple] | None = None,
        T_profile_fall: list[tuple] | None = None,
        dy: float = 0.001,
    ) -> dict:
        """
        Eigen stresses in the composite cross-section under the IRC:6-2017 Cl.215.4
        non-uniform temperature gradient.

        Stresses are self-equilibrating and exist even in a simply supported beam.
        For a simply supported span, secondary (hyperstatic) reactions are zero;
        the gradient causes free curvature only.

        Parameters
        ----------
        parts : list of dict
            Rectangular section components from top to bottom, each containing:
              'label'  (str)   : e.g. 'slab', 'top_flange', 'web', 'bot_flange'
              'b'      (float) : width (m)
              'h'      (float) : height / thickness (m)
              'E'      (float) : elastic modulus (MPa) — E_c for slab, E_s for steel
              'y_top'  (float) : depth of top face from top of composite section (m)
        h_slab : float
            Slab thickness (m) — controls the extent of the Cl.215.4 gradient.
        E_s : float
            Steel modulus (MPa) — reference for transformed-section properties.
        T_profile_rise : list of (y, T), optional
            Signed temperature (°C) at each depth y (m) for positive gradient
            (top heating).  If None, derived from IRC:6-2017 Cl.215.4 'heating'.
        T_profile_fall : list of (y, T), optional
            Signed temperature (°C) for negative gradient (top cooling).
            If None, derived from IRC:6-2017 Cl.215.4 'cooling' with negated values
            so cooling → negative F_N (contraction) and correct bending sign.
        dy : float
            Integration strip height (m).  Default: 0.001 m.

        Returns
        -------
        dict with keys:
            y_NA_m, A_eq_m2, I_eq_m4,
            F_N_rise_kN, M_N_rise_kNm, F_N_fall_kN, M_N_fall_kNm,
            sigma_eigen_rise_MPa, sigma_eigen_fall_MPa,
            kappa_rise_per_m, kappa_fall_per_m,
            delta_mid_rise_m, delta_mid_fall_m,
            clause, note_secondary
        """
        L = self.L

        # ── IRC:6-2017 Cl.215.2 — thermal expansion coefficient ──────────────
        alpha = IRC6_2017.cl_215_4_material_properties()['alpha']   # /°C

        D_total = max(p['y_top'] + p['h'] for p in parts)   # total composite depth (m)

        # ── Build IRC:6-2017 Cl.215.4 profiles when not supplied ─────────────
        if T_profile_rise is None:
            gr    = IRC6_2017.cl_215_4_temperature_gradient(h_slab, gradient_type='heating')
            T_fn  = gr['T_at_y']
            n_pts = max(int(D_total / 0.001) + 2, 3)
            # T_fn returns 0 for y > h_slab; profile covers full composite depth
            T_profile_rise = [(i * 0.001, T_fn(i * 0.001)) for i in range(n_pts)]
            print(f"Gradient profile (heating): T1={gr['T1']:.1f}°C  h1={gr['h1']:.3f} m  [{gr['clause']}]")

        if T_profile_fall is None:
            gr    = IRC6_2017.cl_215_4_temperature_gradient(h_slab, gradient_type='cooling')
            T_fn  = gr['T_at_y']
            n_pts = max(int(D_total / 0.001) + 2, 3)
            # Negate magnitudes: cooling → negative F_N and correct bending sign
            T_profile_fall = [(i * 0.001, -T_fn(i * 0.001)) for i in range(n_pts)]
            print(f"Gradient profile (cooling): T1={gr['T1']:.1f}°C  h1={gr['h1']:.3f} m  [{gr['clause']}]")

        # ── Step 1 — Transformed section properties (reference modulus = E_s) ─
        # Modular ratio n_i = E_i / E_s  (< 1 for concrete, = 1 for steel)
        A_eq   = 0.0   # m²   total transformed area
        Ay_sum = 0.0   # m³   first moment of transformed area from top face

        for part in parts:
            n_i    = part['E'] / E_s
            y_c_i  = part['y_top'] + part['h'] / 2.0   # part centroid depth (m)
            A_eq  += n_i * part['b'] * part['h']
            Ay_sum += n_i * part['b'] * part['h'] * y_c_i

        y_NA = Ay_sum / A_eq   # neutral axis depth from top (m)

        # Transformed second moment of area about NA  (parallel-axis theorem)
        I_eq = 0.0   # m⁴
        for part in parts:
            n_i   = part['E'] / E_s
            b_i   = part['b']
            h_i   = part['h']
            y_c_i = part['y_top'] + h_i / 2.0
            I_eq += n_i * (b_i * h_i**3 / 12.0
                           + b_i * h_i * (y_c_i - y_NA)**2)

        print(
            f"Transformed section (IRC:6-2017 Cl.215.4): "
            f"y_NA={y_NA:.4f} m  A_eq={A_eq:.5f} m²  I_eq={I_eq:.6f} m⁴"
        )

        # ── Helper: piecewise linear interpolation of (y, T) profile ─────────
        def interp_profile(T_profile: list[tuple], y: float) -> float:
            """Linearly interpolate; returns boundary value outside defined range."""
            if not T_profile:
                return 0.0
            if y <= T_profile[0][0]:
                return T_profile[0][1]
            if y >= T_profile[-1][0]:
                return T_profile[-1][1]
            for i in range(len(T_profile) - 1):
                y0, T0 = T_profile[i]
                y1, T1 = T_profile[i + 1]
                if y0 <= y <= y1:
                    return T0 + (y - y0) / (y1 - y0) * (T1 - T0)
            return 0.0

        # ── Helper: fine-strip numerical integration of F_N and M_N ──────────
        def integrate_profile(T_profile: list[tuple]) -> tuple[float, float]:
            """
            Axial (F_N, kN) and moment (M_N, kN·m) thermal resultants.

            Unit path:
              E_i [MPa] × 1000 → [kN/m²]
              × alpha [/°C] × T(y) [°C] × b [m] × dy [m]  →  kN
              × (y − y_NA) [m]                              →  kN·m

            Each part uses its own E_i, so the concrete-to-steel interface at
            the slab soffit is handled correctly.  Parts with T = 0 throughout
            contribute zero without special-casing.
            """
            F_N = 0.0
            M_N = 0.0
            for part in parts:
                y_top    = part['y_top']
                b        = part['b']      # m
                E_i      = part['E']      # MPa
                n_strips = max(1, int(round(part['h'] / dy)))
                dy_i     = part['h'] / n_strips
                for k in range(n_strips):
                    y_mid = y_top + (k + 0.5) * dy_i
                    T_y   = interp_profile(T_profile, y_mid)
                    dF    = E_i * 1000.0 * alpha * T_y * b * dy_i   # kN
                    F_N  += dF
                    M_N  += dF * (y_mid - y_NA)                      # kN·m
            return F_N, M_N

        # ── Step 2 — Piecewise integration of thermal resultants ──────────────
        F_N_rise, M_N_rise = integrate_profile(T_profile_rise)
        F_N_fall, M_N_fall = integrate_profile(T_profile_fall)

        # ── Step 3 — Eigen stresses at key fibre locations ────────────────────
        def E_at_y(y_check: float) -> float:
            """E (MPa) of the part whose depth range contains y_check."""
            for p in parts:
                if p['y_top'] <= y_check <= p['y_top'] + p['h']:
                    return p['E']
            return E_s   # gap between parts — fall back to steel

        def sigma_eigen(
            y_f: float,
            F_N: float,
            M_N: float,
            T_profile: list[tuple],
        ) -> float:
            """
            Eigen stress (MPa) at fibre depth y_f from top of section.

            sigma = E_f × alpha × T_f
                    − F_N / (A_eq × 1000)
                    − M_N × (y_f − y_NA) / (I_eq × 1000)

            Unit check (all terms → MPa):
              E_f [MPa] × alpha [/°C] × T_f [°C]             = MPa ✓
              F_N [kN] / (A_eq [m²] × 1000)                  = MPa ✓
              M_N [kN·m] × Δy [m] / (I_eq [m⁴] × 1000)      = MPa ✓
            """
            E_f = E_at_y(y_f)
            T_f = interp_profile(T_profile, y_f)
            return (
                E_f * alpha * T_f
                - F_N / (A_eq * 1000.0)
                - M_N * (y_f - y_NA) / (I_eq * 1000.0)
            )

        # Standard fibre check depths — identified from parts labels
        web_part = next(
            (p for p in parts if 'web' in p.get('label', '').lower()), None
        )
        bot_fl = next(
            (p for p in parts
             if 'bot' in p.get('label', '').lower()
             and 'flange' in p.get('label', '').lower()),
            None,
        )

        fibre_locs: list[tuple[str, float]] = [
            ('top_of_slab',         0.0),
            ('bottom_of_slab',      h_slab),
            ('top_of_steel_flange', h_slab),   # coincides with slab soffit
        ]
        if web_part:
            fibre_locs.append(('top_of_web',    web_part['y_top']))
            fibre_locs.append(('mid_depth_web', web_part['y_top'] + web_part['h'] / 2.0))
        if bot_fl:
            fibre_locs.append(('bottom_flange_top', bot_fl['y_top']))
        fibre_locs.append(('bottom_fibre', D_total))

        sigma_rise = {
            lbl: sigma_eigen(y_f, F_N_rise, M_N_rise, T_profile_rise)
            for lbl, y_f in fibre_locs
        }
        sigma_fall = {
            lbl: sigma_eigen(y_f, F_N_fall, M_N_fall, T_profile_fall)
            for lbl, y_f in fibre_locs
        }

        # ── Step 4 — Midspan deflection from gradient  (simply supported) ─────
        # No secondary reactions — IRC:6-2017 Cl.215.4
        # kappa = M_N / (E_s [kN/m²] × I_eq [m⁴])
        # delta_mid = kappa × L² / 8
        kappa_rise     = M_N_rise / (E_s * 1000.0 * I_eq)   # 1/m
        kappa_fall     = M_N_fall / (E_s * 1000.0 * I_eq)   # 1/m
        delta_mid_rise = kappa_rise * L**2 / 8.0             # m
        delta_mid_fall = kappa_fall * L**2 / 8.0             # m

        print(
            f"Thermal resultants: "
            f"F_N_rise={F_N_rise:.2f} kN  M_N_rise={M_N_rise:.2f} kN·m  "
            f"delta_mid_rise={delta_mid_rise * 1000:.2f} mm"
        )

        result = {
            # Transformed section properties
            'y_NA_m':               y_NA,
            'A_eq_m2':              A_eq,
            'I_eq_m4':              I_eq,
            # Thermal resultants
            'F_N_rise_kN':          F_N_rise,
            'M_N_rise_kNm':         M_N_rise,
            'F_N_fall_kN':          F_N_fall,
            'M_N_fall_kNm':         M_N_fall,
            # Eigen stresses at standard fibre locations (MPa)
            'sigma_eigen_rise_MPa': sigma_rise,
            'sigma_eigen_fall_MPa': sigma_fall,
            # Curvature and midspan deflection from gradient
            'kappa_rise_per_m':     kappa_rise,
            'kappa_fall_per_m':     kappa_fall,
            'delta_mid_rise_m':     delta_mid_rise,
            'delta_mid_fall_m':     delta_mid_fall,
            # Metadata
            'clause':               'IRC 6:2017 Cl.215.4',
            'note_secondary': (
                'Simply supported span: secondary (hyperstatic) reactions = 0. '
                'Gradient causes free curvature only.'
            ),
        }

        self.temp_gradient_results = result
        return result

    # ─────────────────────────────────────────────────────────────────────────
    # Temperature and seismic loads
    # ─────────────────────────────────────────────────────────────────────────

    def add_temperature_load(self) -> None:
        """
        Apply temperature load to the grillage model as a patch load over the
        full deck footprint per IRC:6-2017 Cl.215.

        The load intensity is read from ``self.additional_inputs`` using the key
        ``"temperature_load_kN_m2"``.  If the key is absent or zero the load is
        silently skipped (temperature load is optional).

        Delegates to BridgeGrillageModel.create_temperature_load().
        """
        tl_raw = self.input_dict.get("temperature_load_kN_m2")
        if not tl_raw or float(tl_raw) == 0.0:
            bridge_logger.info("Temperature load absent; skipping.")
            return
        tl_kN_m2 = float(tl_raw)
        self.grillage_model.create_temperature_load(
            temperature_load_kN_m2=tl_kN_m2,
            partial_safety_factor=1.0,
        )

    def add_seismic_loads(self) -> None:
        """
        Apply seismic load cases to the grillage model per IRC:6-2017 Cl. 218.

        Must be called AFTER ``create_governing_ll_load_case()`` so that:
          - the dead-load cases exist on the grillage model (total DL is
            integrated from them on demand), and
          - ``governing_ll_name`` is set so the governing vehicle weight can
            be computed for the IRC 218.5.2 live-load fraction.

        Input sources
        -------------
        ``KEY_PROJECT_LOCATION`` : zone factor Z from ``weather_data['z_value']``.
        ``KEY_SL_*``             : importance factor, soil type, time period,
                                   damping, response reduction factor and the
                                   UI-computed Ah / Av coefficients.
        DL / LL                  : derived from model state, unless the seismic
                                   tab's Custom mode supplies explicit values.

        Load cases created (delegated to
        BridgeGrillageModel.create_seismic_load_cases):
          - ``"EQ_X"``            → Longitudinal seismic (0% LL)
          - ``"EQ_Z"``            → Transverse seismic (20% LL)
          - ``"EQ_Y"``            → Vertical seismic, Av = (2/3)×Ah (20% LL)
          - ``"1.5 EQ (a/b/c)"``  → IRC 218.3 design combinations with γ = 1.5
        """
        inp = self.input_dict

        # ── Zone factor Z: from project-location weather_data ──
        location = inp.get(KEY_PROJECT_LOCATION) or {}
        if isinstance(location, str) and '{' in location:
            import ast
            try:
                location = ast.literal_eval(location)
            except (ValueError, SyntaxError):
                location = {}
        z_value = 0.10  # Zone II default (lowest hazard)
        if isinstance(location, dict):
            weather = location.get('weather_data') or {}
            z_val = weather.get('z_value')
            if z_val is not None:
                z_value = float(z_val)

        # ── Soil type from the seismic tab ──
        soil_str = str(inp.get(KEY_SL_SOIL_TYPE) or "")
        soil_type = 3 if "III" in soil_str else (2 if "II" in soil_str else 1)

        # ── IRC 218 parameters from the seismic tab ──
        def _to_float(key: str, default: float) -> float:
            try:
                return float(inp.get(key))
            except (TypeError, ValueError):
                return default

        importance_factor = _to_float(KEY_SL_IMPORTANCE_FACTOR, 1.0)
        damping_pct       = _to_float(KEY_SL_DAMPING, 2.0)
        R                 = _to_float(KEY_SL_RESPONSE_REDUCTION, 1.0)
        time_period       = _to_float(KEY_SL_TIME_PERIOD, 0.5)

        # ── Ah and Av: use UI-computed values if present; else computed in
        # the analyser from z_value / soil / T / damping ──
        def _to_coeff(key: str) -> float | None:
            try:
                v = float(inp.get(key))
                return v if v > 0 else None
            except (TypeError, ValueError):
                return None

        Ah = _to_coeff(KEY_SL_HORIZONTAL_COEFF)
        Av = _to_coeff(KEY_SL_VERTICAL_COEFF)

        # ── DL / LL: Custom mode overrides; Automatic (default) derives them
        # from model state inside create_seismic_load_cases() ──
        def _custom_load(mode_key: str, value_key: str) -> float | None:
            if str(inp.get(mode_key) or "Automatic") != "Custom":
                return None
            try:
                return float(inp.get(value_key))
            except (TypeError, ValueError):
                return None

        dead_load_kN = _custom_load(KEY_SL_DEAD_LOAD_MODE, KEY_SL_DEAD_LOAD_VALUE)
        live_load_kN = _custom_load(KEY_SL_LIVE_LOAD_MODE, KEY_SL_LIVE_LOAD_VALUE)

        self.grillage_model.create_seismic_load_cases(
            z_value=z_value,
            soil_type=soil_type,
            importance_factor=importance_factor,
            damping_percent=damping_pct,
            response_reduction_factor=R,
            time_period=time_period,
            Ah=Ah,
            Av=Av,
            dead_load_kN=dead_load_kN,
            live_load_kN=live_load_kN,
            partial_safety_factor=1.5,  # IRC:6-2017 Table B.2 seismic ULS
        )

    def vehicle_lane_coordinates(self) -> list:
        """
        Return vehicle-to-coordinate mappings for all IRC:6-2017 Table 6A
        combinations.

        Delegates to BridgeGrillageModel.vehicle_lane_coordinates().

        Returns
        -------
        list of dict
            Each dict has 'case_num' and 'combinations' keys.
        """
        return self.grillage_model.vehicle_lane_coordinates()

    def create_vehicle_load_cases(self) -> list:
        """
        Create static vehicle load cases based on IRC:6-2017 lane combinations.

        Delegates to BridgeGrillageModel.create_vehicle_load_cases().

        Returns
        -------
        list
            All created load case objects.
        """
        return self.grillage_model.create_vehicle_load_cases()

    def add_vehicle_load_cases_from_combinations(self) -> list:
        """
        Create vehicle load cases with lane factors (alf) and dynamic load
        allowance (dla) applied, using IRC:6-2017 combinations.

        Delegates to BridgeGrillageModel.add_vehicle_load_cases_from_combinations().

        Returns
        -------
        list
            All created load case objects.
        """
        return self.grillage_model.add_vehicle_load_cases_from_combinations()

    def create_moving_vehicle_load_cases(
        self,
        span: float | None = None,
    ) -> list:
        """
        Create moving load cases for all vehicles previously created by
        add_vehicle_load_cases_from_combinations().

        The traversal path extents are derived from each vehicle's IRC:6
        length: start = -vehicle_length, end = span + vehicle_length.

        Delegates to BridgeGrillageModel.create_moving_vehicle_load_cases().

        Parameters
        ----------
        span : float, optional
            Override the bridge span (m); defaults to the analysed span.

        Returns
        -------
        list
            All created moving load case objects.
        """
        return self.grillage_model.create_moving_vehicle_load_cases(
            span=span,
        )

    def add_fatigue_vehicle_load_case(self, apply_dla: bool = True) -> list:
        """
        Create the static IRC:6-2017 Cl.204.6 fatigue-truck load case — a single
        case holding one truck on the centreline of each carriageway (two trucks
        when a median splits the deck).

        Delegates to BridgeGrillageModel.add_fatigue_vehicle_load_case().

        Parameters
        ----------
        apply_dla : bool
            Apply the Cl.208.3 dynamic load allowance to the load case
            (default True).

        Returns
        -------
        list
            A single-element list holding the created static fatigue load case.
        """
        return self.grillage_model.add_fatigue_vehicle_load_case(apply_dla=apply_dla)

    def create_moving_fatigue_load_cases(self, span: float | None = None) -> list:
        """
        Create the moving fatigue load case for the trucks previously created by
        add_fatigue_vehicle_load_case(). All trucks share one path and move
        together from -vehicle_length to span + vehicle_length, each along its
        own carriageway centreline.

        Delegates to BridgeGrillageModel.create_moving_fatigue_load_cases().

        Parameters
        ----------
        span : float, optional
            Override the bridge span (m); defaults to the analysed span.

        Returns
        -------
        list
            A single-element list holding the created moving fatigue load case.
        """
        return self.grillage_model.create_moving_fatigue_load_cases(span=span)

    def create_braking_load_case(self):
        """
        Create the single unfactored ``"Braking Load"`` case for the governing
        live-load case.

        The heaviest vehicle in the governing case sets the force: Fx = 20% of
        its total vertical load (Cl.211.2), applied with the couple Mz = Fx × e
        it produces by acting e above the deck (Cl.211.3). Both are shared
        equally between the main girder nodes. No partial safety factor is
        applied — γ belongs to the combination builders.

        The eccentricity e is read from ``self.additional_inputs``
        (``KEY_LL_ECCENTRICITY``, "Eccentricity from top of Deck"); when absent
        it falls back to the IRC 1.2 m value inside the grillage model.

        Must be called after create_governing_ll_load_case() so the governing
        case is known.

        Delegates to BridgeGrillageModel.create_braking_load_case().

        Returns
        -------
        LoadCase or None
            The created ``"Braking Load"`` case, or None when no governing
            live-load case is available.
        """
        ecc_raw = self.additional_inputs.get(KEY_LL_ECCENTRICITY)
        try:
            eccentricity = float(ecc_raw) if ecc_raw not in (None, "") else None
        except (TypeError, ValueError):
            bridge_logger.info(
                f"Braking eccentricity {ecc_raw!r} is not numeric; using the IRC default."
            )
            eccentricity = None

        return self.grillage_model.create_braking_load_case(eccentricity=eccentricity)

    def analyze(self):
        """
        Run the OpenSees grillage analysis for all registered load cases.

        Delegates to BridgeGrillageModel.analyze(), which executes the model,
        retrieves results for every load case, and stores them in
        ``self.grillage_model.dataset``.

        Must be called after add_dead_loads() and add_live_loads() have
        registered all load cases on the model.

        Returns
        -------
        xarray.Dataset
            Results dataset containing displacements and forces for all load
            cases, indexed by Loadcase, Node/Element, and Component.
        """
        bridge_logger.check_cancel()
        result = self.grillage_model.analyze()
        return result

    def create_governing_ll_load_case(self, dataset, partial_safety_factor: float = 1.0):
        """
        Identify the governing static vehicle load case, create a
        ``"{partial_safety_factor} LL"`` load case from it, and solve just that case.

        Must be called after analyze().

        Parameters
        ----------
        dataset : xarray.Dataset
            Results from the initial analysis.
        partial_safety_factor : float
            ULS partial safety factor for the governing LL case (default 1.0).

        Returns
        -------
        None
            The combined dataset is built once by _reanalyze_with_dedup().
        """
        return self.grillage_model.create_governing_ll_load_case(
            dataset=dataset,
            partial_safety_factor=partial_safety_factor,
        )

    def _reanalyze_with_dedup(self):
        """
        Solve the load cases added since the initial analysis (the DL+LL case and
        the ULS/SLS combinations), build the combined results dataset once, cache
        it on the grillage model, and return it.

        A bare analyze() would re-solve EVERY registered case — including all
        ~50 increments of each moving load — and ospgrillage's record store
        (extract_analysis -> dict.setdefault) would then discard the repeated
        results, so only the new cases are passed to analyze().

        Called by design() after load combinations have been registered so that
        combination results are included in the final results dataset.
        """
        g = self.grillage_model
        m = g.model

        new_cases = [
            lc.name
            for lc in (
                [getattr(g, "dl_ll_combination", None)]
                + list(getattr(g, "uls_combinations", None) or [])
                + list(getattr(g, "sls_combinations", None) or [])
            )
            if lc is not None
        ]
        if new_cases:
            m.analyze(load_case=new_cases)

        ds = m.get_results()

        # Safety net only: with the installed ospgrillage the records are keyed by
        # load-case name, so no duplicate Loadcase labels occur; keep the axis
        # unique anyway in case a future ospgrillage version changes behaviour.
        lc_vals = ds.coords["Loadcase"].values
        seen: set = set()
        unique_idx = []
        for i, val in enumerate(lc_vals):
            if val not in seen:
                seen.add(val)
                unique_idx.append(i)
        if len(unique_idx) < len(lc_vals):
            ds = ds.isel(Loadcase=unique_idx)

        self.grillage_model._deduplicated_results = ds
        return ds

    def _drop_moving_increment_cases(self, ds):
        """
        Drop the per-position "Moving CaseN at global position ..." rows from the
        cached results dataset once the envelopes exist.

        These ~50-increments-per-vehicle rows dominate the Loadcase axis (about
        two thirds of it) but have no post-design consumer: governing-LL
        detection uses the static vehicle cases during stage 4F, envelopes cover
        the combinations, the plots dropdown deliberately hides them
        (mpl_plot_widget.link_output_dock), and the load-effects table excludes
        them. Keeping them just multiplies the resident dataset (and everything
        derived from it, e.g. result_data) roughly 3x.
        """
        lcs = ds.coords["Loadcase"].values
        keep = [lc for lc in lcs if not str(lc).startswith("Moving ")]
        if len(keep) == len(lcs):
            return ds
        ds = ds.sel(Loadcase=keep)
        self.grillage_model._deduplicated_results = ds
        log_memory(
            f"design: dropped {len(lcs) - len(keep)} moving-increment load cases "
            f"from cached dataset ({len(lcs)} -> {len(keep)})"
        )
        return ds

    def create_envelope_load_case(self, dataset=None):
        """
        Build two worst-signed-magnitude force/displacement envelopes — one over
        the ULS combinations and one over the SLS combinations — and inject them
        into the results dataset as the pseudo load cases ``Envelope ULS`` and
        ``Envelope SLS``.

        Delegates to BridgeGrillageModel.create_envelope_load_case(), which
        caches the augmented dataset on the grillage model's
        ``_deduplicated_results`` and the standalone enveloped DataArrays on its
        ``result_envelopes`` (``{label: {"forces", "displacements"}}``). Both are
        mirrored onto this object.

        Parameters
        ----------
        dataset : xarray.Dataset, optional
            Results dataset to envelope. Defaults to the deduplicated results
            cached on the grillage model.

        Returns
        -------
        xarray.Dataset
            The augmented dataset with the ``Envelope ULS`` / ``Envelope SLS`` rows.
        """
        augmented = self.grillage_model.create_envelope_load_case(dataset=dataset)
        self.result_envelopes = self.grillage_model.result_envelopes
        self._results_with_envelope = augmented
        return augmented

    # ─────────────────────────────────────────────────────────────────────────
    # Load combinations
    # ─────────────────────────────────────────────────────────────────────────

    #: Input-dict key holding the per-combination include/exclude selection
    #: persisted by the load-combination checkbox widget (LoadCombinationWidget).
    _LC_SELECTION_KEY = "irc6_default_combinations"

    def _combination_keys(self, namespace_filter):
        """
        Return the set of selected (included) combination keys, or ``None``.

        Reads the per-combination selection saved by the load-combination UI
        (a list of ``{"key", "included", ...}`` dicts). ``namespace_filter`` is
        a predicate on the key string used to keep only ULS or only SLS keys.

        Returns ``None`` when no selection exists (dialog never opened) so the
        analyser falls back to generating every combination. Returns a (possibly
        empty) ``set`` otherwise — an empty set means the user de-selected every
        combination in that limit state, so none should be generated.
        """
        sel = self.input_dict.get(self._LC_SELECTION_KEY)
        if not sel:
            return None
        return {
            e["key"] for e in sel
            if e.get("included") and e.get("key") and namespace_filter(e["key"])
        }

    def create_uls_combinations(self) -> list:
        """
        Create the user-selected ULS load combinations per IRC:6-2017 Table B.2.

        When all are selected, produces 13 combinations:
          BASIC_1 … BASIC_6        — 2 permanent directions × 3 variable leaders
          ACCIDENTAL_1 … ACCIDENTAL_3 — 3 events × 1 valid leader
          SEISMIC_1 … SEISMIC_4    — 2 directions × 2 seismic conditions

        The combinations the user de-selected in the load-combination UI are
        skipped; with no saved selection every combination is generated.

        Must be called after create_governing_ll_load_case() so that the LL
        load case (``ll_load_case``) is available for combination.

        Delegates to BridgeGrillageModel.create_uls_combinations().

        Returns
        -------
        list — ospgrillage load-case objects registered with the model.
        """
        included = self._combination_keys(lambda k: ".sls." not in k)
        return self.grillage_model.create_uls_combinations(included_keys=included)

    def create_sls_combinations(self) -> list:
        """
        Create the user-selected SLS load combinations per IRC:6-2017 Table B.3.

        When all are selected, produces 14 combinations:
          SLS_RARE_1 … SLS_RARE_6          — 2 surfacing directions × 3 variable leaders
          SLS_FREQUENT_1 … SLS_FREQUENT_6  — same structure, frequent-column factors
          SLS_QP_1, SLS_QP_2               — quasi-permanent; only TL (0.5) contributes

        The combinations the user de-selected in the load-combination UI are
        skipped; with no saved selection every combination is generated.

        Must be called after create_governing_ll_load_case() so that the LL
        load case is available for combination.

        Delegates to BridgeGrillageModel.create_sls_combinations().

        Returns
        -------
        list — ospgrillage load-case objects registered with the model.
        """
        included = self._combination_keys(lambda k: ".sls." in k)
        return self.grillage_model.create_sls_combinations(included_keys=included)

    def create_dl_ll_combination(self, dl_factor: float = 1.0, ll_factor: float = 1.0):
        """
        Create the ``"{dl_factor} DL + {ll_factor} LL"`` load case combining the
        dead-load combination with the governing live-load case.

        With the defaults this registers a ``"1.0 DL + 1.0 LL"`` case carrying
        the unfactored sum of dead and live loads.

        Must be called after create_dead_load_combination() (via add_dead_loads())
        and create_governing_ll_load_case() so both sub-cases are available.

        Delegates to BridgeGrillageModel.create_dl_ll_combination().

        Returns
        -------
        The ospgrillage load-case object registered with the model, or ``None``
        if neither sub-case was available.
        """
        return self.grillage_model.create_dl_ll_combination(
            dl_factor=dl_factor, ll_factor=ll_factor
        )

    # ─────────────────────────────────────────────────────────────────────────
    # DCR checks
    # ─────────────────────────────────────────────────────────────────────────

    def _run_dcr_checks(self, dataset) -> None:
        """Run structural capacity checks and push DCR percentages to the output dock."""
        results = PlateGirderAnalysisResults(dataset=dataset, bridge=self.grillage_model)
        _, engine, design_results = run_design_check(
            plate_girder_bridge=self,
            analysis_results=results,
            print_report=True,
        )
        self._dcr_engine = engine
        bridge_logger.check_cancel()
        self.design_results = design_results

        # Write every output into output_dict while it is still mutable.
        # store_design_results also sets the KEY_UTIL_* values so the block
        # below is redundant — but kept for the _frontend.set_output_value calls.
        self.store_design_results(design_results)

    def _design_cross_bracing_members(self) -> dict:
        """
        Run Osdag member designs for cross-bracing diagonals and chords.

        Returns
        -------
        dict — nested by pair → member → force_type → Osdag result.
        """
        from osdagbridge.core.bridge_types.plate_girder.crossbracingforces import CrossBracingForces
        from osdagbridge.core.bridge_types.plate_girder.results_data import enrich_crossbracing_dump

        if not self.result_data:
            print("[CrossBracing] No analysis results available — skipping.")
            return {}

        cb = CrossBracingForces(bridge=self)
        if not cb.get_crossbracing_count():
            print("[CrossBracing] No cross-bracing panels found — skipping.")
            return {}

        forces_dict = cb.get_design_forces_dict()
        if not forces_dict or not forces_dict.get("pairs"):
            return {}
        
        # Store configuration in output_dict
        self.output_dict["member_properties.cross_bracing_details.type"] = forces_dict.get("brace_type", "X")
        self.output_dict["member_properties.cross_bracing_details.top_chord"] = forces_dict.get("top_chord", True)
        self.output_dict["member_properties.cross_bracing_details.bottom_chord"] = forces_dict.get("bottom_chord", True)
        
        cb.print_critical_forces(forces_dict)

        bridge_logger.check_cancel()
        pair_designs = cb.run_member_designs(forces_dict)
        self.output_dict["crossbracing_forces_dict"] = forces_dict

        enrich_crossbracing_dump(pair_designs)
        self._print_crossbracing_design_results(forces_dict, pair_designs)

        # Resolve all possible intermediate girder pairs
        n_girders = int(self.input_dict[KEY_TS_NO_OF_GIRDERS])
        pairs = [f"G{i}-G{i+1}" for i in range(1, n_girders)]

        # Key mapping function
        def make_pair_key(key: str, pair_id: str) -> str:
            for pfx in (
                "transverse_member_design.cb.section_properties.bracing",
                "transverse_member_design.cb.section_properties.top_chord",
                "transverse_member_design.cb.section_properties.bottom_chord",
            ):
                if key.startswith(pfx):
                    suffix = key[len(pfx):].lstrip(".")
                    return f"{pfx}.{pair_id}.{suffix}"
            pfx = "member_properties.cross_bracing_details"
            if key.startswith(pfx):
                suffix = key[len(pfx):].lstrip(".")
                return f"{pfx}.{pair_id}.{suffix}"
            return f"{key}.{pair_id}"

        # Initialize keys to None for all pairs (both brace & chords)
        for pair in pairs:
            pair_id = pair.replace("-", "")
            
            # Diagonal/bracing
            for k in (
                KEY_TD_CB_PROP_L, KEY_TD_CB_PROP_H, KEY_TD_CB_PROP_B, KEY_TD_CB_PROP_TW, KEY_TD_CB_PROP_TF,
                KEY_TD_CB_PROP_RZ, KEY_TD_CB_PROP_M, KEY_TD_CB_PROP_A, KEY_TD_CB_PROP_IZ, KEY_TD_CB_PROP_IV,
                KEY_TD_CB_PROP_RV, KEY_TD_CB_PROP_ZZ, KEY_TD_CB_PROP_ZV, KEY_TD_CB_PROP_ZUZ, KEY_TD_CB_PROP_ZUV,
            ):
                self.output_dict[make_pair_key(k, pair_id)] = None

            # Top chord
            for k in (
                KEY_TD_CB_TOP_CHORD_PROP_L, KEY_TD_CB_TOP_CHORD_PROP_H, KEY_TD_CB_TOP_CHORD_PROP_B, KEY_TD_CB_TOP_CHORD_PROP_TW, KEY_TD_CB_TOP_CHORD_PROP_TF,
                KEY_TD_CB_TOP_CHORD_PROP_RZ, KEY_TD_CB_TOP_CHORD_PROP_M, KEY_TD_CB_TOP_CHORD_PROP_A, KEY_TD_CB_TOP_CHORD_PROP_IZ, KEY_TD_CB_TOP_CHORD_PROP_IV,
                KEY_TD_CB_TOP_CHORD_PROP_RV, KEY_TD_CB_TOP_CHORD_PROP_ZZ, KEY_TD_CB_TOP_CHORD_PROP_ZV, KEY_TD_CB_TOP_CHORD_PROP_ZUZ, KEY_TD_CB_TOP_CHORD_PROP_ZUV,
            ):
                self.output_dict[make_pair_key(k, pair_id)] = None

            # Bottom chord
            for k in (
                KEY_TD_CB_BOTTOM_CHORD_PROP_L, KEY_TD_CB_BOTTOM_CHORD_PROP_H, KEY_TD_CB_BOTTOM_CHORD_PROP_B, KEY_TD_CB_BOTTOM_CHORD_PROP_TW, KEY_TD_CB_BOTTOM_CHORD_PROP_TF,
                KEY_TD_CB_BOTTOM_CHORD_PROP_RZ, KEY_TD_CB_BOTTOM_CHORD_PROP_M, KEY_TD_CB_BOTTOM_CHORD_PROP_A, KEY_TD_CB_BOTTOM_CHORD_PROP_IZ, KEY_TD_CB_BOTTOM_CHORD_PROP_IV,
                KEY_TD_CB_BOTTOM_CHORD_PROP_RV, KEY_TD_CB_BOTTOM_CHORD_PROP_ZZ, KEY_TD_CB_BOTTOM_CHORD_PROP_ZV, KEY_TD_CB_BOTTOM_CHORD_PROP_ZUZ, KEY_TD_CB_BOTTOM_CHORD_PROP_ZUV,
            ):
                self.output_dict[make_pair_key(k, pair_id)] = None

        # Process design results and query database per pair
        from osdagbridge.core.bridge_types.plate_girder.results_data import _extract_osdag_summary

        top_chord_enabled = self.output_dict.get("member_properties.cross_bracing_details.top_chord", True)
        bottom_chord_enabled = self.output_dict.get("member_properties.cross_bracing_details.bottom_chord", True)

        for pair in pairs:
            pair_id = pair.replace("-", "")
            member_designs = pair_designs.get(pair, {}) if pair_designs else {}

            # Diagonal section designation for this pair
            diag_des = ""
            diag_data = member_designs.get("diagonal", {})
            for force_type in ("tension", "compression"):
                res = _extract_osdag_summary(diag_data.get(force_type) or {})
                sec = res.get("section")
                if sec:
                    diag_des = str(sec)
                    break

            # Chord section designation for this pair
            chord_des = ""
            chord_data = member_designs.get("chord", {})
            for force_type in ("tension", "compression"):
                res = _extract_osdag_summary(chord_data.get(force_type) or {})
                sec = res.get("section")
                if sec:
                    chord_des = str(sec)
                    break

            # Query database and populate diagonal section properties
            if diag_des:
                self.output_dict[make_pair_key(KEY_MP_CB_BRACING_SECTION_TYPE, pair_id)] = diag_des
                diag_details = self._query_crossbracing_section(diag_des)
                if diag_details:
                    self.output_dict[make_pair_key("member_properties.cross_bracing_details.diagonal.section_type", pair_id)] = diag_details["type"]
                    
                    # Set diagonal dimensions
                    leg_h_key = make_pair_key("member_properties.cross_bracing_details.diagonal.leg_h", pair_id)
                    leg_w_key = make_pair_key("member_properties.cross_bracing_details.diagonal.leg_w", pair_id)
                    thick_key = make_pair_key("member_properties.cross_bracing_details.diagonal.thickness", pair_id)
                    if diag_details["type"] == "ANGLE":
                        self.output_dict[leg_h_key] = diag_details["H"] * 1000.0
                        self.output_dict[leg_w_key] = diag_details["B"] * 1000.0
                        self.output_dict[thick_key] = diag_details["tw"] * 1000.0
                    elif diag_details["type"] == "CHANNEL":
                        self.output_dict[leg_h_key] = diag_details["L"] * 1000.0
                        self.output_dict[leg_w_key] = diag_details["B"] * 1000.0
                        self.output_dict[thick_key] = diag_details["tw"] * 1000.0

                    self.output_dict[make_pair_key(KEY_TD_CB_PROP_L, pair_id)] = diag_details["L"]
                    self.output_dict[make_pair_key(KEY_TD_CB_PROP_H, pair_id)] = diag_details["H"]
                    self.output_dict[make_pair_key(KEY_TD_CB_PROP_B, pair_id)] = diag_details["B"]
                    self.output_dict[make_pair_key(KEY_TD_CB_PROP_TW, pair_id)] = diag_details["tw"]
                    self.output_dict[make_pair_key(KEY_TD_CB_PROP_TF, pair_id)] = diag_details["tF"]
                    self.output_dict[make_pair_key(KEY_TD_CB_PROP_RZ, pair_id)] = diag_details["rz"]
                    self.output_dict[make_pair_key(KEY_TD_CB_PROP_M, pair_id)] = diag_details["M"]
                    self.output_dict[make_pair_key(KEY_TD_CB_PROP_A, pair_id)] = diag_details["A"]
                    self.output_dict[make_pair_key(KEY_TD_CB_PROP_IZ, pair_id)] = diag_details["Iz"]
                    self.output_dict[make_pair_key(KEY_TD_CB_PROP_IV, pair_id)] = diag_details["Iv"]
                    self.output_dict[make_pair_key(KEY_TD_CB_PROP_RV, pair_id)] = diag_details["rv"]
                    self.output_dict[make_pair_key(KEY_TD_CB_PROP_ZZ, pair_id)] = diag_details["Zz"]
                    self.output_dict[make_pair_key(KEY_TD_CB_PROP_ZV, pair_id)] = diag_details["Zv"]
                    self.output_dict[make_pair_key(KEY_TD_CB_PROP_ZUZ, pair_id)] = diag_details["Zuz"]
                    self.output_dict[make_pair_key(KEY_TD_CB_PROP_ZUV, pair_id)] = diag_details["Zuv"]

            # Query database and populate top/bottom chords section properties
            if chord_des:
                self.output_dict[make_pair_key(KEY_MP_CB_TOP_CHORD_SECTION_DESIG, pair_id)] = chord_des
                self.output_dict[make_pair_key(KEY_MP_CB_BOTTOM_CHORD_SECTION_DESIG, pair_id)] = chord_des
                chord_details = self._query_crossbracing_section(chord_des)
                if chord_details:
                    if top_chord_enabled:
                        self.output_dict[make_pair_key("member_properties.cross_bracing_details.top_chord.section_type", pair_id)] = chord_details["type"]
                        tc_h_key = make_pair_key("member_properties.cross_bracing_details.top_chord.leg_h", pair_id)
                        tc_w_key = make_pair_key("member_properties.cross_bracing_details.top_chord.leg_w", pair_id)
                        tc_t_key = make_pair_key("member_properties.cross_bracing_details.top_chord.thickness", pair_id)
                        if chord_details["type"] == "ANGLE":
                            self.output_dict[tc_h_key] = chord_details["H"] * 1000.0
                            self.output_dict[tc_w_key] = chord_details["B"] * 1000.0
                            self.output_dict[tc_t_key] = chord_details["tw"] * 1000.0
                        elif chord_details["type"] == "CHANNEL":
                            self.output_dict[tc_h_key] = chord_details["L"] * 1000.0
                            self.output_dict[tc_w_key] = chord_details["B"] * 1000.0
                            self.output_dict[tc_t_key] = chord_details["tw"] * 1000.0

                        self.output_dict[make_pair_key(KEY_TD_CB_TOP_CHORD_PROP_L, pair_id)] = chord_details["L"]
                        self.output_dict[make_pair_key(KEY_TD_CB_TOP_CHORD_PROP_H, pair_id)] = chord_details["H"]
                        self.output_dict[make_pair_key(KEY_TD_CB_TOP_CHORD_PROP_B, pair_id)] = chord_details["B"]
                        self.output_dict[make_pair_key(KEY_TD_CB_TOP_CHORD_PROP_TW, pair_id)] = chord_details["tw"]
                        self.output_dict[make_pair_key(KEY_TD_CB_TOP_CHORD_PROP_TF, pair_id)] = chord_details["tF"]
                        self.output_dict[make_pair_key(KEY_TD_CB_TOP_CHORD_PROP_RZ, pair_id)] = chord_details["rz"]
                        self.output_dict[make_pair_key(KEY_TD_CB_TOP_CHORD_PROP_M, pair_id)] = chord_details["M"]
                        self.output_dict[make_pair_key(KEY_TD_CB_TOP_CHORD_PROP_A, pair_id)] = chord_details["A"]
                        self.output_dict[make_pair_key(KEY_TD_CB_TOP_CHORD_PROP_IZ, pair_id)] = chord_details["Iz"]
                        self.output_dict[make_pair_key(KEY_TD_CB_TOP_CHORD_PROP_IV, pair_id)] = chord_details["Iv"]
                        self.output_dict[make_pair_key(KEY_TD_CB_TOP_CHORD_PROP_RV, pair_id)] = chord_details["rv"]
                        self.output_dict[make_pair_key(KEY_TD_CB_TOP_CHORD_PROP_ZZ, pair_id)] = chord_details["Zz"]
                        self.output_dict[make_pair_key(KEY_TD_CB_TOP_CHORD_PROP_ZV, pair_id)] = chord_details["Zv"]
                        self.output_dict[make_pair_key(KEY_TD_CB_TOP_CHORD_PROP_ZUZ, pair_id)] = chord_details["Zuz"]
                        self.output_dict[make_pair_key(KEY_TD_CB_TOP_CHORD_PROP_ZUV, pair_id)] = chord_details["Zuv"]

                    if bottom_chord_enabled:
                        self.output_dict[make_pair_key("member_properties.cross_bracing_details.bottom_chord.section_type", pair_id)] = chord_details["type"]
                        bc_h_key = make_pair_key("member_properties.cross_bracing_details.bottom_chord.leg_h", pair_id)
                        bc_w_key = make_pair_key("member_properties.cross_bracing_details.bottom_chord.leg_w", pair_id)
                        bc_t_key = make_pair_key("member_properties.cross_bracing_details.bottom_chord.thickness", pair_id)
                        if chord_details["type"] == "ANGLE":
                            self.output_dict[bc_h_key] = chord_details["H"] * 1000.0
                            self.output_dict[bc_w_key] = chord_details["B"] * 1000.0
                            self.output_dict[bc_t_key] = chord_details["tw"] * 1000.0
                        elif chord_details["type"] == "CHANNEL":
                            self.output_dict[bc_h_key] = chord_details["L"] * 1000.0
                            self.output_dict[bc_w_key] = chord_details["B"] * 1000.0
                            self.output_dict[bc_t_key] = chord_details["tw"] * 1000.0

                        self.output_dict[make_pair_key(KEY_TD_CB_BOTTOM_CHORD_PROP_L, pair_id)] = chord_details["L"]
                        self.output_dict[make_pair_key(KEY_TD_CB_BOTTOM_CHORD_PROP_H, pair_id)] = chord_details["H"]
                        self.output_dict[make_pair_key(KEY_TD_CB_BOTTOM_CHORD_PROP_B, pair_id)] = chord_details["B"]
                        self.output_dict[make_pair_key(KEY_TD_CB_BOTTOM_CHORD_PROP_TW, pair_id)] = chord_details["tw"]
                        self.output_dict[make_pair_key(KEY_TD_CB_BOTTOM_CHORD_PROP_TF, pair_id)] = chord_details["tF"]
                        self.output_dict[make_pair_key(KEY_TD_CB_BOTTOM_CHORD_PROP_RZ, pair_id)] = chord_details["rz"]
                        self.output_dict[make_pair_key(KEY_TD_CB_BOTTOM_CHORD_PROP_M, pair_id)] = chord_details["M"]
                        self.output_dict[make_pair_key(KEY_TD_CB_BOTTOM_CHORD_PROP_A, pair_id)] = chord_details["A"]
                        self.output_dict[make_pair_key(KEY_TD_CB_BOTTOM_CHORD_PROP_IZ, pair_id)] = chord_details["Iz"]
                        self.output_dict[make_pair_key(KEY_TD_CB_BOTTOM_CHORD_PROP_IV, pair_id)] = chord_details["Iv"]
                        self.output_dict[make_pair_key(KEY_TD_CB_BOTTOM_CHORD_PROP_RV, pair_id)] = chord_details["rv"]
                        self.output_dict[make_pair_key(KEY_TD_CB_BOTTOM_CHORD_PROP_ZZ, pair_id)] = chord_details["Zz"]
                        self.output_dict[make_pair_key(KEY_TD_CB_BOTTOM_CHORD_PROP_ZV, pair_id)] = chord_details["Zv"]
                        self.output_dict[make_pair_key(KEY_TD_CB_BOTTOM_CHORD_PROP_ZUZ, pair_id)] = chord_details["Zuz"]
                        self.output_dict[make_pair_key(KEY_TD_CB_BOTTOM_CHORD_PROP_ZUV, pair_id)] = chord_details["Zuv"]
        
        self.crossbracing_design_results = pair_designs
        return pair_designs
    
    def _design_end_diaphragm_members(self) -> dict:
        """
        Run Osdag member designs for end-diaphragm bracing members (diagonals/chords)
        if type is "Cross Bracing", or calculate and populate section properties if
        type is "Rolled Beam" or "Welded Beam".

        Returns
        -------
        dict — nested by pair → member → force_type → Osdag result.
        """
        import copy
        import math
        import sqlite3
        from osdagbridge.core.bridge_types.plate_girder.results_data import _extract_osdag_summary
        from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import resolve_girder_value as _gv
        from osdagbridge.core.utils.common import (
            KEY_TS_NO_OF_GIRDERS,
            KEY_TS_GIRDER_SPACING,
            KEY_MP_GIRDER_DEPTH,
            KEY_MP_ED_TYPE,
            KEY_MP_ED_BRACING_TYPE,
            KEY_MP_ED_BRACING_SECTION_DESIGNATION,
            KEY_MP_ED_TOP_CHORD,
            KEY_MP_ED_TOP_CHORD_SECTION_DESIG,
            KEY_MP_ED_BOTTOM_CHORD,
            KEY_MP_ED_BOTTOM_CHORD_SECTION_DESIG,
            KEY_MP_ED_IS_SECTION,
            KEY_MP_ED_SYMMETRY,
            KEY_MP_ED_TOTAL_DEPTH,
            KEY_MP_ED_WEB_THICKNESS,
            KEY_MP_ED_TOP_FLANGE_WIDTH,
            KEY_MP_ED_BOTTOM_FLANGE_WIDTH,
            KEY_MP_ED_TOP_FLANGE_THICKNESS,
            KEY_MP_ED_BOTTOM_FLANGE_THICKNESS,
            KEY_TD_ED_PROP_L, KEY_TD_ED_PROP_H, KEY_TD_ED_PROP_B, KEY_TD_ED_PROP_TW, KEY_TD_ED_PROP_TF,
            KEY_TD_ED_PROP_RZ, KEY_TD_ED_PROP_M, KEY_TD_ED_PROP_A, KEY_TD_ED_PROP_IZ, KEY_TD_ED_PROP_IV,
            KEY_TD_ED_PROP_RV, KEY_TD_ED_PROP_ZZ, KEY_TD_ED_PROP_ZV, KEY_TD_ED_PROP_ZUZ, KEY_TD_ED_PROP_ZUV,
            KEY_TD_ED_TOP_CHORD_PROP_L, KEY_TD_ED_TOP_CHORD_PROP_H, KEY_TD_ED_TOP_CHORD_PROP_B, KEY_TD_ED_TOP_CHORD_PROP_TW, KEY_TD_ED_TOP_CHORD_PROP_TF,
            KEY_TD_ED_TOP_CHORD_PROP_RZ, KEY_TD_ED_TOP_CHORD_PROP_M, KEY_TD_ED_TOP_CHORD_PROP_A, KEY_TD_ED_TOP_CHORD_PROP_IZ, KEY_TD_ED_TOP_CHORD_PROP_IV,
            KEY_TD_ED_TOP_CHORD_PROP_RV, KEY_TD_ED_TOP_CHORD_PROP_ZZ, KEY_TD_ED_TOP_CHORD_PROP_ZV, KEY_TD_ED_TOP_CHORD_PROP_ZUZ, KEY_TD_ED_TOP_CHORD_PROP_ZUV,
            KEY_TD_ED_BOTTOM_CHORD_PROP_L, KEY_TD_ED_BOTTOM_CHORD_PROP_H, KEY_TD_ED_BOTTOM_CHORD_PROP_B, KEY_TD_ED_BOTTOM_CHORD_PROP_TW, KEY_TD_ED_BOTTOM_CHORD_PROP_TF,
            KEY_TD_ED_BOTTOM_CHORD_PROP_RZ, KEY_TD_ED_BOTTOM_CHORD_PROP_M, KEY_TD_ED_BOTTOM_CHORD_PROP_A, KEY_TD_ED_BOTTOM_CHORD_PROP_IZ, KEY_TD_ED_BOTTOM_CHORD_PROP_IV,
            KEY_TD_ED_BOTTOM_CHORD_PROP_RV, KEY_TD_ED_BOTTOM_CHORD_PROP_ZZ, KEY_TD_ED_BOTTOM_CHORD_PROP_ZV, KEY_TD_ED_BOTTOM_CHORD_PROP_ZUZ, KEY_TD_ED_BOTTOM_CHORD_PROP_ZUV,
        )
        


        if not self.result_data:
            print("[EndDiaphragm] No analysis results available — skipping.")
            return {}

        model = self.grillage_model.model
        if not model:
            print("[EndDiaphragm] No analysis grillage model available — skipping.")
            return {}

        # 1. Map support element IDs (start and end edges) to adjacent girder pairs
        start_elements = [str(e) for e in model.get_element(member="start_edge", options="elements")]
        end_elements = [str(e) for e in model.get_element(member="end_edge", options="elements")]
        all_edge_elements = start_elements + end_elements

        girders = self.result_data.get("girders", {})
        girder_node_sets = {
            g_name: set(g_data.get("nodes", []))
            for g_name, g_data in girders.items()
        }

        def _find_girder(node) -> str | None:
            for g_name, node_set in girder_node_sets.items():
                if node in node_set:
                    return g_name
            return None

        pair_to_elements = {}
        for m in all_edge_elements:
            if m not in self.result_data.get("members", {}):
                continue
            n1, n2 = self.result_data["members"][m]
            g1 = _find_girder(n1)
            g2 = _find_girder(n2)
            if g1 and g2 and g1 != g2:
                idx1 = girders[g1].get("index", 0)
                idx2 = girders[g2].get("index", 0)
                pair = f"{g1}-{g2}" if idx1 <= idx2 else f"{g2}-{g1}"
                pair_to_elements.setdefault(pair, []).append(m)

        # 2. Key mapping function for end diaphragm details
        def make_pair_key(key: str, pair_id: str) -> str:
            for pfx in (
                "transverse_member_design.ed.section_properties.end_diaphragm",
                "transverse_member_design.ed.section_properties.top_chord",
                "transverse_member_design.ed.section_properties.bottom_chord",
            ):
                if key.startswith(pfx):
                    suffix = key[len(pfx):].lstrip(".")
                    return f"{pfx}.{pair_id}.{suffix}"
            pfx = "member_properties.end_diaphragm_details"
            if key.startswith(pfx):
                suffix = key[len(pfx):].lstrip(".")
                return f"{pfx}.{pair_id}.{suffix}"
            return f"{key}.{pair_id}"

        # 3. Resolve possible intermediate girder pairs
        n_girders = int(self.input_dict[KEY_TS_NO_OF_GIRDERS])
        pairs = [f"G{i}-G{i+1}" for i in range(1, n_girders)]

        # Initialize output keys to None
        for pair in pairs:
            pair_id = pair.replace("-", "")
            
            # Diagonal/bracing
            for k in (
                KEY_TD_ED_PROP_L, KEY_TD_ED_PROP_H, KEY_TD_ED_PROP_B, KEY_TD_ED_PROP_TW, KEY_TD_ED_PROP_TF,
                KEY_TD_ED_PROP_RZ, KEY_TD_ED_PROP_M, KEY_TD_ED_PROP_A, KEY_TD_ED_PROP_IZ, KEY_TD_ED_PROP_IV,
                KEY_TD_ED_PROP_RV, KEY_TD_ED_PROP_ZZ, KEY_TD_ED_PROP_ZV, KEY_TD_ED_PROP_ZUZ, KEY_TD_ED_PROP_ZUV,
            ):
                self.output_dict[make_pair_key(k, pair_id)] = None

            # Top chord
            for k in (
                KEY_TD_ED_TOP_CHORD_PROP_L, KEY_TD_ED_TOP_CHORD_PROP_H, KEY_TD_ED_TOP_CHORD_PROP_B, KEY_TD_ED_TOP_CHORD_PROP_TW, KEY_TD_ED_TOP_CHORD_PROP_TF,
                KEY_TD_ED_TOP_CHORD_PROP_RZ, KEY_TD_ED_TOP_CHORD_PROP_M, KEY_TD_ED_TOP_CHORD_PROP_A, KEY_TD_ED_TOP_CHORD_PROP_IZ, KEY_TD_ED_TOP_CHORD_PROP_IV,
                KEY_TD_ED_TOP_CHORD_PROP_RV, KEY_TD_ED_TOP_CHORD_PROP_ZZ, KEY_TD_ED_TOP_CHORD_PROP_ZV, KEY_TD_ED_TOP_CHORD_PROP_ZUZ, KEY_TD_ED_TOP_CHORD_PROP_ZUV,
            ):
                self.output_dict[make_pair_key(k, pair_id)] = None

            # Bottom chord
            for k in (
                KEY_TD_ED_BOTTOM_CHORD_PROP_L, KEY_TD_ED_BOTTOM_CHORD_PROP_H, KEY_TD_ED_BOTTOM_CHORD_PROP_B, KEY_TD_ED_BOTTOM_CHORD_PROP_TW, KEY_TD_ED_BOTTOM_CHORD_PROP_TF,
                KEY_TD_ED_BOTTOM_CHORD_PROP_RZ, KEY_TD_ED_BOTTOM_CHORD_PROP_M, KEY_TD_ED_BOTTOM_CHORD_PROP_A, KEY_TD_ED_BOTTOM_CHORD_PROP_IZ, KEY_TD_ED_BOTTOM_CHORD_PROP_IV,
                KEY_TD_ED_BOTTOM_CHORD_PROP_RV, KEY_TD_ED_BOTTOM_CHORD_PROP_ZZ, KEY_TD_ED_BOTTOM_CHORD_PROP_ZV, KEY_TD_ED_BOTTOM_CHORD_PROP_ZUZ, KEY_TD_ED_BOTTOM_CHORD_PROP_ZUV,
            ):
                self.output_dict[make_pair_key(k, pair_id)] = None

        # 4. Sizing and Geometry
        D = float(_gv(self.input_dict, KEY_MP_GIRDER_DEPTH))
        h = D * 0.85  # Default depth ratio
        s = float(self.input_dict[KEY_TS_GIRDER_SPACING])

        # 5. Process design results and queries
        forces_dict = {"pairs": {}}
        pair_designs = {}
        for pair in pairs:
            pair_designs[pair] = {}

        for i, pair in enumerate(pairs, start=1):
            pair_id = pair.replace("-", "")
            # M1 = start end, M2 = finish end. Both share the same design config
            # within a pair, so read from whichever slot has data.
            _m1 = f".{pair_id}.E{i}M1"
            _m2 = f".{pair_id}.E{i}M2"
            member_suffix = _m1 if self.input_dict.get(f"{KEY_MP_ED_TYPE}{_m1}") else _m2

            ed_type = self.input_dict.get(f"{KEY_MP_ED_TYPE}{member_suffix}") or ""
            if not ed_type:
                continue   # no data for this pair, skip cleanly
            self.output_dict[make_pair_key(KEY_MP_ED_TYPE, pair_id)] = ed_type
            
            # -- CASE A: CROSS BRACING DIAPHRAGM --
            if ed_type == "Cross Bracing":
                bracing_type = self.input_dict.get(f"{KEY_MP_ED_BRACING_TYPE}{member_suffix}")
                top_chord_enabled = self.input_dict.get(f"{KEY_MP_ED_TOP_CHORD}{member_suffix}")
                top_chord_enabled = str(top_chord_enabled).strip().lower() not in ("no", "false", "0", "none", "")
                bottom_chord_enabled = self.input_dict.get(f"{KEY_MP_ED_BOTTOM_CHORD}{member_suffix}")
                bottom_chord_enabled = str(bottom_chord_enabled).strip().lower() not in ("no", "false", "0", "none", "")

                self.output_dict[make_pair_key(KEY_MP_ED_BRACING_TYPE, pair_id)] = bracing_type
                self.output_dict[make_pair_key(KEY_MP_ED_TOP_CHORD, pair_id)] = top_chord_enabled
                self.output_dict[make_pair_key(KEY_MP_ED_BOTTOM_CHORD, pair_id)] = bottom_chord_enabled

                # Compute Diagonal length
                horiz_proj = s if bracing_type in ("X", "X-Bracing") else s / 2.0
                L_d = math.sqrt(horiz_proj ** 2 + h ** 2)
                cos_alpha = math.cos(math.atan2(h, horiz_proj))

                # Collect envelope forces over both ends and all load cases
                elements = pair_to_elements.get(pair, [])
                diag_tens_max = 0.0
                diag_comp_max = 0.0
                chord_tens_max = 0.0
                chord_comp_max = 0.0
                diag_tens_lc = None
                diag_comp_lc = None
                chord_tens_lc = None
                chord_comp_lc = None
                _tol = 0.005

                for lc in self.result_data["loadcases"]:
                    lc_str = str(lc)
                    # Envelope pseudo cases copy the governing combination's values;
                    # skip them so they can't steal the governing-LC label here.
                    if lc_str.startswith("Envelope"):
                        continue
                    for m in elements:
                        if lc_str not in self.result_data["forces"] or m not in self.result_data["forces"][lc_str]:
                            continue
                        vz_i = self.result_data["forces"][lc_str][m].get("Vz_i")
                        if vz_i is None:
                            continue
                        vz_kn = vz_i / 1000.0
                        f_diag = vz_kn / cos_alpha
                        f_chord = vz_kn

                        if f_diag > diag_tens_max:
                            diag_tens_max = f_diag
                            diag_tens_lc = lc_str
                        if f_chord > chord_tens_max:
                            chord_tens_max = f_chord
                            chord_tens_lc = lc_str
                        if f_diag < diag_comp_max:
                            diag_comp_max = f_diag
                            diag_comp_lc = lc_str
                        if f_chord < chord_comp_max:
                            chord_comp_max = f_chord
                            chord_comp_lc = lc_str

                pair_forces = {
                    "diag_tension_kN": round(diag_tens_max, 3) if diag_tens_max > _tol else None,
                    "diag_tension_gov_lc": diag_tens_lc if diag_tens_max > _tol else None,
                    "diag_compression_kN": round(abs(diag_comp_max), 3) if diag_comp_max < -_tol else None,
                    "diag_compression_gov_lc": diag_comp_lc if diag_comp_max < -_tol else None,
                    "chord_tension_kN": round(chord_tens_max, 3) if chord_tens_max > _tol else None,
                    "chord_tension_gov_lc": chord_tens_lc if chord_tens_max > _tol else None,
                    "chord_compression_kN": round(abs(chord_comp_max), 3) if chord_comp_max < -_tol else None,
                    "chord_compression_gov_lc": chord_comp_lc if chord_comp_max < -_tol else None,
                }
                forces_dict["pairs"][pair] = pair_forces

                # Run Osdag design checks
                from osdagbridge.core.utils.connect import (
                    design_dict_struts_bolted,
                    design_dict_tension_bolted,
                    design_pool,
                    run_calculation,
                )
                jobs = []
                for member, L_mm, t_key, c_key in (
                    ("diagonal", round(L_d * 1000), "diag_tension_kN", "diag_compression_kN"),
                    ("chord", round(s * 1000), "chord_tension_kN", "chord_compression_kN"),
                ):
                    if pair_forces.get(t_key) is not None:
                        d = copy.deepcopy(design_dict_tension_bolted)
                        d["Load.Axial"] = str(float(pair_forces[t_key]))
                        d["Member.Length"] = str(L_mm)
                        jobs.append((pair, member, "tension", d))
                    if pair_forces.get(c_key) is not None:
                        d = copy.deepcopy(design_dict_struts_bolted)
                        d["Load.Axial"] = str(float(pair_forces[c_key]))
                        d["Member.Length"] = str(L_mm)
                        jobs.append((pair, member, "compression", d))

                if jobs:
                    cpu_count = __import__("os").cpu_count() or 4
                    max_workers = min(cpu_count, len(jobs))
                    # spawn-context pool: forking under the design worker thread
                    # deadlocks (see connect.design_pool).
                    with design_pool(max_workers) as executor:
                        futures = {executor.submit(run_calculation, j[3]): j for j in jobs}
                        for future, (p, member, force_type, _) in futures.items():
                            try:
                                res = future.result()
                            except Exception as exc:
                                print(f"  [EndDiaphragm] SKIP {p} {member} {force_type}: {exc}")
                                res = None
                            pair_designs.setdefault(p, {}).setdefault(member, {})[force_type] = res

                # Fetch selected designations
                member_designs = pair_designs.get(pair, {})
                diag_des = ""
                diag_data = member_designs.get("diagonal", {})
                for force_type in ("tension", "compression"):
                    res = _extract_osdag_summary(diag_data.get(force_type) or {})
                    sec = res.get("section")
                    if sec:
                        diag_des = str(sec)
                        break
                if not diag_des:
                    diag_des = self.input_dict.get(f"{KEY_MP_ED_BRACING_SECTION_DESIGNATION}{member_suffix}")

                chord_des = ""
                chord_data = member_designs.get("chord", {})
                for force_type in ("tension", "compression"):
                    res = _extract_osdag_summary(chord_data.get(force_type) or {})
                    sec = res.get("section")
                    if sec:
                        chord_des = str(sec)
                        break

                top_chord_des = chord_des if chord_des else self.input_dict.get(f"{KEY_MP_ED_TOP_CHORD_SECTION_DESIG}{member_suffix}")
                bottom_chord_des = chord_des if chord_des else self.input_dict.get(f"{KEY_MP_ED_BOTTOM_CHORD_SECTION_DESIG}{member_suffix}")

                # Populate diagonal properties
                if diag_des:
                    self.output_dict[make_pair_key(KEY_MP_ED_BRACING_SECTION_DESIGNATION, pair_id)] = diag_des
                    diag_details = self._query_crossbracing_section(diag_des)
                    if diag_details:
                        self.output_dict[make_pair_key("member_properties.end_diaphragm_details.diagonal.section_type", pair_id)] = diag_details["type"]
                        
                        leg_h_key = make_pair_key("member_properties.end_diaphragm_details.diagonal.leg_h", pair_id)
                        leg_w_key = make_pair_key("member_properties.end_diaphragm_details.diagonal.leg_w", pair_id)
                        thick_key = make_pair_key("member_properties.end_diaphragm_details.diagonal.thickness", pair_id)
                        if diag_details["type"] == "ANGLE":
                            self.output_dict[leg_h_key] = diag_details["H"] * 1000.0
                            self.output_dict[leg_w_key] = diag_details["B"] * 1000.0
                            self.output_dict[thick_key] = diag_details["tw"] * 1000.0
                        elif diag_details["type"] == "CHANNEL":
                            self.output_dict[leg_h_key] = diag_details["L"] * 1000.0
                            self.output_dict[leg_w_key] = diag_details["B"] * 1000.0
                            self.output_dict[thick_key] = diag_details["tw"] * 1000.0

                        self.output_dict[make_pair_key(KEY_TD_ED_PROP_L, pair_id)] = diag_details["L"]
                        self.output_dict[make_pair_key(KEY_TD_ED_PROP_H, pair_id)] = diag_details["H"]
                        self.output_dict[make_pair_key(KEY_TD_ED_PROP_B, pair_id)] = diag_details["B"]
                        self.output_dict[make_pair_key(KEY_TD_ED_PROP_TW, pair_id)] = diag_details["tw"]
                        self.output_dict[make_pair_key(KEY_TD_ED_PROP_TF, pair_id)] = diag_details["tF"]
                        self.output_dict[make_pair_key(KEY_TD_ED_PROP_RZ, pair_id)] = diag_details["rz"]
                        self.output_dict[make_pair_key(KEY_TD_ED_PROP_M, pair_id)] = diag_details["M"]
                        self.output_dict[make_pair_key(KEY_TD_ED_PROP_A, pair_id)] = diag_details["A"]
                        self.output_dict[make_pair_key(KEY_TD_ED_PROP_IZ, pair_id)] = diag_details["Iz"]
                        self.output_dict[make_pair_key(KEY_TD_ED_PROP_IV, pair_id)] = diag_details["Iv"]
                        self.output_dict[make_pair_key(KEY_TD_ED_PROP_RV, pair_id)] = diag_details["rv"]
                        self.output_dict[make_pair_key(KEY_TD_ED_PROP_ZZ, pair_id)] = diag_details["Zz"]
                        self.output_dict[make_pair_key(KEY_TD_ED_PROP_ZV, pair_id)] = diag_details["Zv"]
                        self.output_dict[make_pair_key(KEY_TD_ED_PROP_ZUZ, pair_id)] = diag_details["Zuz"]
                        self.output_dict[make_pair_key(KEY_TD_ED_PROP_ZUV, pair_id)] = diag_details["Zuv"]

                # Populate chords
                if top_chord_enabled and top_chord_des:
                    self.output_dict[make_pair_key(KEY_MP_ED_TOP_CHORD_SECTION_DESIG, pair_id)] = top_chord_des
                    chord_details = self._query_crossbracing_section(top_chord_des)
                    if chord_details:
                        self.output_dict[make_pair_key("member_properties.end_diaphragm_details.top_chord.section_type", pair_id)] = chord_details["type"]
                        tc_h_key = make_pair_key("member_properties.end_diaphragm_details.top_chord.leg_h", pair_id)
                        tc_w_key = make_pair_key("member_properties.end_diaphragm_details.top_chord.leg_w", pair_id)
                        tc_t_key = make_pair_key("member_properties.end_diaphragm_details.top_chord.thickness", pair_id)
                        if chord_details["type"] == "ANGLE":
                            self.output_dict[tc_h_key] = chord_details["H"] * 1000.0
                            self.output_dict[tc_w_key] = chord_details["B"] * 1000.0
                            self.output_dict[tc_t_key] = chord_details["tw"] * 1000.0
                        elif chord_details["type"] == "CHANNEL":
                            self.output_dict[tc_h_key] = chord_details["L"] * 1000.0
                            self.output_dict[tc_w_key] = chord_details["B"] * 1000.0
                            self.output_dict[tc_t_key] = chord_details["tw"] * 1000.0

                        self.output_dict[make_pair_key(KEY_TD_ED_TOP_CHORD_PROP_L, pair_id)] = chord_details["L"]
                        self.output_dict[make_pair_key(KEY_TD_ED_TOP_CHORD_PROP_H, pair_id)] = chord_details["H"]
                        self.output_dict[make_pair_key(KEY_TD_ED_TOP_CHORD_PROP_B, pair_id)] = chord_details["B"]
                        self.output_dict[make_pair_key(KEY_TD_ED_TOP_CHORD_PROP_TW, pair_id)] = chord_details["tw"]
                        self.output_dict[make_pair_key(KEY_TD_ED_TOP_CHORD_PROP_TF, pair_id)] = chord_details["tF"]
                        self.output_dict[make_pair_key(KEY_TD_ED_TOP_CHORD_PROP_RZ, pair_id)] = chord_details["rz"]
                        self.output_dict[make_pair_key(KEY_TD_ED_TOP_CHORD_PROP_M, pair_id)] = chord_details["M"]
                        self.output_dict[make_pair_key(KEY_TD_ED_TOP_CHORD_PROP_A, pair_id)] = chord_details["A"]
                        self.output_dict[make_pair_key(KEY_TD_ED_TOP_CHORD_PROP_IZ, pair_id)] = chord_details["Iz"]
                        self.output_dict[make_pair_key(KEY_TD_ED_TOP_CHORD_PROP_IV, pair_id)] = chord_details["Iv"]
                        self.output_dict[make_pair_key(KEY_TD_ED_TOP_CHORD_PROP_RV, pair_id)] = chord_details["rv"]
                        self.output_dict[make_pair_key(KEY_TD_ED_TOP_CHORD_PROP_ZZ, pair_id)] = chord_details["Zz"]
                        self.output_dict[make_pair_key(KEY_TD_ED_TOP_CHORD_PROP_ZV, pair_id)] = chord_details["Zv"]
                        self.output_dict[make_pair_key(KEY_TD_ED_TOP_CHORD_PROP_ZUZ, pair_id)] = chord_details["Zuz"]
                        self.output_dict[make_pair_key(KEY_TD_ED_TOP_CHORD_PROP_ZUV, pair_id)] = chord_details["Zuv"]

                if bottom_chord_enabled and bottom_chord_des:
                    self.output_dict[make_pair_key(KEY_MP_ED_BOTTOM_CHORD_SECTION_DESIG, pair_id)] = bottom_chord_des
                    chord_details = self._query_crossbracing_section(bottom_chord_des)
                    if chord_details:
                        self.output_dict[make_pair_key("member_properties.end_diaphragm_details.bottom_chord.section_type", pair_id)] = chord_details["type"]
                        bc_h_key = make_pair_key("member_properties.end_diaphragm_details.bottom_chord.leg_h", pair_id)
                        bc_w_key = make_pair_key("member_properties.end_diaphragm_details.bottom_chord.leg_w", pair_id)
                        bc_t_key = make_pair_key("member_properties.end_diaphragm_details.bottom_chord.thickness", pair_id)
                        if chord_details["type"] == "ANGLE":
                            self.output_dict[bc_h_key] = chord_details["H"] * 1000.0
                            self.output_dict[bc_w_key] = chord_details["B"] * 1000.0
                            self.output_dict[bc_t_key] = chord_details["tw"] * 1000.0
                        elif chord_details["type"] == "CHANNEL":
                            self.output_dict[bc_h_key] = chord_details["L"] * 1000.0
                            self.output_dict[bc_w_key] = chord_details["B"] * 1000.0
                            self.output_dict[bc_t_key] = chord_details["tw"] * 1000.0

                        self.output_dict[make_pair_key(KEY_TD_ED_BOTTOM_CHORD_PROP_L, pair_id)] = chord_details["L"]
                        self.output_dict[make_pair_key(KEY_TD_ED_BOTTOM_CHORD_PROP_H, pair_id)] = chord_details["H"]
                        self.output_dict[make_pair_key(KEY_TD_ED_BOTTOM_CHORD_PROP_B, pair_id)] = chord_details["B"]
                        self.output_dict[make_pair_key(KEY_TD_ED_BOTTOM_CHORD_PROP_TW, pair_id)] = chord_details["tw"]
                        self.output_dict[make_pair_key(KEY_TD_ED_BOTTOM_CHORD_PROP_TF, pair_id)] = chord_details["tF"]
                        self.output_dict[make_pair_key(KEY_TD_ED_BOTTOM_CHORD_PROP_RZ, pair_id)] = chord_details["rz"]
                        self.output_dict[make_pair_key(KEY_TD_ED_BOTTOM_CHORD_PROP_M, pair_id)] = chord_details["M"]
                        self.output_dict[make_pair_key(KEY_TD_ED_BOTTOM_CHORD_PROP_A, pair_id)] = chord_details["A"]
                        self.output_dict[make_pair_key(KEY_TD_ED_BOTTOM_CHORD_PROP_IZ, pair_id)] = chord_details["Iz"]
                        self.output_dict[make_pair_key(KEY_TD_ED_BOTTOM_CHORD_PROP_IV, pair_id)] = chord_details["Iv"]
                        self.output_dict[make_pair_key(KEY_TD_ED_BOTTOM_CHORD_PROP_RV, pair_id)] = chord_details["rv"]
                        self.output_dict[make_pair_key(KEY_TD_ED_BOTTOM_CHORD_PROP_ZZ, pair_id)] = chord_details["Zz"]
                        self.output_dict[make_pair_key(KEY_TD_ED_BOTTOM_CHORD_PROP_ZV, pair_id)] = chord_details["Zv"]
                        self.output_dict[make_pair_key(KEY_TD_ED_BOTTOM_CHORD_PROP_ZUZ, pair_id)] = chord_details["Zuz"]
                        self.output_dict[make_pair_key(KEY_TD_ED_BOTTOM_CHORD_PROP_ZUV, pair_id)] = chord_details["Zuv"]

            # -- CASE B: ROLLED BEAM DIAPHRAGM --
            elif ed_type == "Rolled Beam":
                is_sec_des = self.input_dict.get(f"{KEY_MP_ED_IS_SECTION}{member_suffix}")
                if is_sec_des:
                    self.output_dict[make_pair_key(KEY_MP_ED_IS_SECTION, pair_id)] = is_sec_des
                    beam_details = self._query_rolled_beam_section(is_sec_des)
                    if beam_details:
                        self.output_dict[make_pair_key(KEY_TD_ED_PROP_L, pair_id)] = s
                        self.output_dict[make_pair_key(KEY_TD_ED_PROP_H, pair_id)] = beam_details["H"]
                        self.output_dict[make_pair_key(KEY_TD_ED_PROP_B, pair_id)] = beam_details["B"]
                        self.output_dict[make_pair_key(KEY_TD_ED_PROP_TW, pair_id)] = beam_details["tw"]
                        self.output_dict[make_pair_key(KEY_TD_ED_PROP_TF, pair_id)] = beam_details["tF"]
                        self.output_dict[make_pair_key(KEY_TD_ED_PROP_M, pair_id)] = beam_details["M"]
                        self.output_dict[make_pair_key(KEY_TD_ED_PROP_A, pair_id)] = beam_details["A"]
                        self.output_dict[make_pair_key(KEY_TD_ED_PROP_IZ, pair_id)] = beam_details["Iz"]
                        self.output_dict[make_pair_key(KEY_TD_ED_PROP_IV, pair_id)] = beam_details["Iv"]
                        self.output_dict[make_pair_key(KEY_TD_ED_PROP_RZ, pair_id)] = beam_details["rz"]
                        self.output_dict[make_pair_key(KEY_TD_ED_PROP_RV, pair_id)] = beam_details["rv"]
                        self.output_dict[make_pair_key(KEY_TD_ED_PROP_ZZ, pair_id)] = beam_details["Zz"]
                        self.output_dict[make_pair_key(KEY_TD_ED_PROP_ZV, pair_id)] = beam_details["Zv"]
                        self.output_dict[make_pair_key(KEY_TD_ED_PROP_ZUZ, pair_id)] = beam_details["Zuz"]
                        self.output_dict[make_pair_key(KEY_TD_ED_PROP_ZUV, pair_id)] = beam_details["Zuv"]

            # -- CASE C: WELDED BEAM DIAPHRAGM --
            elif ed_type == "Welded Beam":
                depth = float(self.input_dict.get(f"{KEY_MP_ED_TOTAL_DEPTH}{member_suffix}") or 0.0)
                web_t = float(self.input_dict.get(f"{KEY_MP_ED_WEB_THICKNESS}{member_suffix}") or 0.0)
                top_w = float(self.input_dict.get(f"{KEY_MP_ED_TOP_FLANGE_WIDTH}{member_suffix}") or 0.0)
                bot_w = float(self.input_dict.get(f"{KEY_MP_ED_BOTTOM_FLANGE_WIDTH}{member_suffix}") or 0.0)
                top_t = float(self.input_dict.get(f"{KEY_MP_ED_TOP_FLANGE_THICKNESS}{member_suffix}") or 0.0)
                bot_t = float(self.input_dict.get(f"{KEY_MP_ED_BOTTOM_FLANGE_THICKNESS}{member_suffix}") or 0.0)
                
                if depth > 0:
                    h_w = depth - top_t - bot_t
                    a_f1 = top_w * top_t
                    a_f2 = bot_w * bot_t
                    a_w = h_w * web_t
                    a_total = a_f1 + a_f2 + a_w

                    y_f2 = bot_t / 2.0
                    y_w = bot_t + h_w / 2.0
                    y_f1 = depth - top_t / 2.0
                    y_c = (a_f2 * y_f2 + a_w * y_w + a_f1 * y_f1) / a_total

                    i_z = (1.0 / 12.0) * bot_w * (bot_t ** 3) + a_f2 * ((y_c - y_f2) ** 2) + \
                        (1.0 / 12.0) * web_t * (h_w ** 3) + a_w * ((y_c - y_w) ** 2) + \
                        (1.0 / 12.0) * top_w * (top_t ** 3) + a_f1 * ((y_c - y_f1) ** 2)

                    i_y = (1.0 / 12.0) * bot_t * (bot_w ** 3) + \
                        (1.0 / 12.0) * h_w * (web_t ** 3) + \
                        (1.0 / 12.0) * top_t * (top_w ** 3)

                    r_z = math.sqrt(i_z / a_total)
                    r_y = math.sqrt(i_y / a_total)

                    z_z = i_z / max(y_c, depth - y_c)
                    z_y = i_y / max(top_w / 2.0, bot_w / 2.0)

                    if abs(a_f2 - a_f1) < 1e-3:
                        z_pz = top_w * top_t * (depth - top_t) + 0.25 * web_t * ((depth - 2.0 * top_t) ** 2)
                    else:
                        y_p = bot_t + (a_total / 2.0 - a_f2) / web_t
                        z_pz = a_f2 * (y_p - bot_t / 2.0) + 0.5 * web_t * ((y_p - bot_t) ** 2) + \
                            a_f1 * (depth - y_p - top_t / 2.0) + 0.5 * web_t * ((depth - y_p - top_t) ** 2)

                    z_py = 0.25 * top_t * (top_w ** 2) + 0.25 * bot_t * (bot_w ** 2) + 0.25 * h_w * (web_t ** 2)
                    mass = a_total * 0.00785

                    self.output_dict[make_pair_key(KEY_TD_ED_PROP_L, pair_id)] = s
                    self.output_dict[make_pair_key(KEY_TD_ED_PROP_H, pair_id)] = depth / 1000.0
                    self.output_dict[make_pair_key(KEY_TD_ED_PROP_B, pair_id)] = top_w / 1000.0
                    self.output_dict[make_pair_key(KEY_TD_ED_PROP_TW, pair_id)] = web_t / 1000.0
                    self.output_dict[make_pair_key(KEY_TD_ED_PROP_TF, pair_id)] = top_t / 1000.0
                    self.output_dict[make_pair_key(KEY_TD_ED_PROP_M, pair_id)] = mass
                    self.output_dict[make_pair_key(KEY_TD_ED_PROP_A, pair_id)] = a_total / 100.0
                    self.output_dict[make_pair_key(KEY_TD_ED_PROP_IZ, pair_id)] = i_z / 10000.0
                    self.output_dict[make_pair_key(KEY_TD_ED_PROP_IV, pair_id)] = i_y / 10000.0
                    self.output_dict[make_pair_key(KEY_TD_ED_PROP_RZ, pair_id)] = r_z / 10.0
                    self.output_dict[make_pair_key(KEY_TD_ED_PROP_RV, pair_id)] = r_y / 10.0
                    self.output_dict[make_pair_key(KEY_TD_ED_PROP_ZZ, pair_id)] = z_z / 1000.0
                    self.output_dict[make_pair_key(KEY_TD_ED_PROP_ZV, pair_id)] = z_y / 1000.0
                    self.output_dict[make_pair_key(KEY_TD_ED_PROP_ZUZ, pair_id)] = z_pz / 1000.0
                    self.output_dict[make_pair_key(KEY_TD_ED_PROP_ZUV, pair_id)] = z_py / 1000.0

        if forces_dict.get("pairs"):
            self._print_enddiaphragm_design_results(forces_dict, pair_designs)
        
        self.output_dict["end_diaphragm_forces_dict"] = forces_dict
        self.end_diaphragm_design_results = pair_designs
        return pair_designs

    def _query_rolled_beam_section(self, designation: str) -> dict | None:
        """Query the Osdag database for details of a rolled beam section using its designation."""
        if not designation:
            return None
        
        designation = designation.strip()
        if not _DB_PATH.exists():
            raise LookupError(f"Database not found at {_DB_PATH}")

        import re
        nums = re.findall(r"\d+(?:\.\d+)?", designation)
        like_pattern = "%" + "%".join(nums) + "%" if nums else designation

        try:
            con = sqlite3.connect(_DB_PATH)
            cur = con.cursor()

            # Try exact match first
            cur.execute(
                'SELECT Designation, Mass, Area, D, B, tw, T, Iz, Iy, rz, ry, Zz, Zy, Zpz, Zpy, It, Iw FROM Beams WHERE Designation = ?',
                (designation,)
            )
            row = cur.fetchone()
            if not row:
                # Try case-insensitive exact match
                cur.execute(
                    'SELECT Designation, Mass, Area, D, B, tw, T, Iz, Iy, rz, ry, Zz, Zy, Zpz, Zpy, It, Iw FROM Beams WHERE LOWER(Designation) = LOWER(?)',
                    (designation,)
                )
                row = cur.fetchone()
            if not row:
                # Fallback to LIKE with numbers
                cur.execute(
                    'SELECT Designation, Mass, Area, D, B, tw, T, Iz, Iy, rz, ry, Zz, Zy, Zpz, Zpy, It, Iw FROM Beams WHERE Designation LIKE ?',
                    (like_pattern,)
                )
                row = cur.fetchone()
            
            if row:
                con.close()
                def val_f(val):
                    return float(val) if val is not None else 0.0
                return {
                    "designation": row[0],
                    "type": "BEAM",
                    "H": val_f(row[3]) / 1000.0,
                    "B": val_f(row[4]) / 1000.0,
                    "tw": val_f(row[5]) / 1000.0,
                    "tF": val_f(row[6]) / 1000.0,
                    "M": val_f(row[2]),
                    "A": val_f(row[3]),
                    "Iz": val_f(row[10]),
                    "Iv": val_f(row[11]),
                    "rz": val_f(row[12]),
                    "rv": val_f(row[13]),
                    "Zz": val_f(row[14]),
                    "Zv": val_f(row[15]),
                    "Zuz": val_f(row[16]),
                    "Zuv": val_f(row[17]),
                }
            con.close()
        except Exception as exc:
            print(f"Error querying rolled beam: {exc}")
        return None

    @staticmethod
    def _print_enddiaphragm_design_results(forces_dict: dict, pair_designs: dict) -> None:
        """Print Osdag design check summary to the terminal."""
        from osdagbridge.core.bridge_types.plate_girder.results_data import _extract_osdag_summary

        sep = "=" * 75
        print(f"\n{sep}")
        print(f"{'END DIAPHRAGM — OSDAG DESIGN RESULTS':^75}")
        print(sep)

        for pair, vals in forces_dict.get("pairs", {}).items():
            designs = pair_designs.get(pair, {})
            print(f"  Pair : {pair}")

            for label, t_key, c_key, member in (
                ("Diagonal", "diag_tension_kN",  "diag_compression_kN",  "diagonal"),
                ("Chord",    "chord_tension_kN", "chord_compression_kN", "chord"),
            ):
                member_designs = designs.get(member, {})
                for force_type, force_key in (("Tension", t_key), ("Compression", c_key)):
                    force_kn = vals.get(force_key)
                    if force_kn is None:
                        continue
                    res  = _extract_osdag_summary(member_designs.get(force_type.lower()) or {})
                    sec  = res.get("section")     or "—"
                    cap  = res.get("capacity_kN") or "—"
                    eff  = res.get("efficiency")
                    slnd = res.get("slenderness")
                    conn = res.get("connection")  or "—"

                    eff_str  = f"  eff={float(eff):.2f}" if eff  not in (None, "") else ""
                    slnd_str = f"  λ={float(slnd):.1f}"  if slnd not in (None, "") else ""

                    print(
                        f"    {label:<8} [{force_type:>11}  {force_kn:>8.3f} kN]"
                        f"  →  {sec}   cap={cap} kN{eff_str}{slnd_str}  {conn}"
                    )

        print(sep)


    @staticmethod
    def _print_crossbracing_design_results(forces_dict: dict, pair_designs: dict) -> None:
        from osdagbridge.core.bridge_types.plate_girder.results_data import _extract_osdag_summary

        sep = "=" * 75
        print(f"\n{sep}")
        print(f"{'CROSS BRACING — OSDAG DESIGN RESULTS':^75}")
        print(sep)

        for pair, vals in forces_dict.get("pairs", {}).items():
            designs = pair_designs.get(pair, {})
            print(f"  Pair : {pair}")

            for label, t_key, c_key, member in (
                ("Diagonal", "diag_tension_kN",  "diag_compression_kN",  "diagonal"),
                ("Chord",    "chord_tension_kN", "chord_compression_kN", "chord"),
            ):
                member_designs = designs.get(member, {})
                for force_type, force_key in (("Tension", t_key), ("Compression", c_key)):
                    force_kn = vals.get(force_key)
                    if force_kn is None:
                        continue
                    res  = _extract_osdag_summary(member_designs.get(force_type.lower()) or {})
                    sec  = res.get("section")     or "—"
                    cap  = res.get("capacity_kN") or "—"
                    eff  = res.get("efficiency")
                    slnd = res.get("slenderness")
                    conn = res.get("connection")  or "—"

                    eff_str  = f"  eff={float(eff):.2f}" if eff  not in (None, "") else ""
                    slnd_str = f"  λ={float(slnd):.1f}"  if slnd not in (None, "") else ""

                    print(
                        f"    {label:<8} [{force_type:>11}  {force_kn:>8.3f} kN]"
                        f"  →  {sec}   cap={cap} kN{eff_str}{slnd_str}  {conn}"
                    )

        print(sep)

    def design_deck_slab(self) -> dict:
        """
        Design the concrete deck slab from the current inputs and store the
        result in ``self.output_dict`` under ``"deck_design_results"``.

        Resolves the deck concrete (fck, fctm) and reinforcement (fy) material
        properties from the Osdag material database via :meth:`_lookup_material`,
        then delegates the structural design to :func:`deckdesign.design_deck_slab`.

        Called from :meth:`design` while ``output_dict`` is still mutable.

        Also stores the report-generator values dict (keyed to
        common.KEY_DD_*) under ``self.output_dict["deck_report_values"]``.

        Returns
        -------
        dict
            Deck-design summary keyed to DECK_DESIGN_SUMMARY_SCHEMA
            (see :func:`deckdesign.design_deck_slab`).  The same dict is stored
            in ``self.output_dict["deck_design_results"]``.
        """
        rebar_grade = str(self.input_dict[KEY_DS_REINF_MATERIAL]).strip()

        # Use already-resolved concrete props (handles custom grades).
        fck  = self.material_props.concrete_prop.fck
        Ecm  = self.material_props.concrete_prop.Ecm
        fctm = self.material_props.concrete_prop.fctm
        fy = self._lookup_material(rebar_grade, "fy")
        Es = self._lookup_material(rebar_grade, "Es")

        # Stage-5 steel design_results (composite beff / VL, SLS stresses) are passed in so deckdesign can run the composite interface checks (Cl.606.10 transverse shear, Cl.604.4 crack control) with the real designed deck reinforcement and write the values back into design_results (report/tables) and the deck dialog utilization bars. bf_top_mm is resolved here so deckdesign stays free of girder-resolution logic.
        result, report_values = deckdesign.design_deck_slab(
            self.input_dict, fck=fck, fctm=fctm, fy=fy, Ecm=Ecm, Es=Es,
            design_results=self.design_results,
            bf_top_mm=resolve_girder_value(self.input_dict, KEY_MP_GIRDER_TOP_FLANGE_WIDTH) * 1000.0,
            stud_height_mm=float(self.input_dict[KEY_DS_STUD_HEIGHT]),
        )
        self.output_dict["deck_design_results"] = result
        # Raw numeric values for the report generator (Tables 5.17(a)-(g)),
        # keyed to common.KEY_DD_*.
        self.output_dict["deck_report_values"] = report_values

        sep = "=" * 60
        print(f"\n{sep}\n  DECK SLAB DESIGN RESULTS\n{sep}")
        if result.get("deck_design_check"):
            print(result["deck_design_check"])
        print(sep)

        return result

    # ─────────────────────────────────────────────────────────────────────────
    # Plotting
    # ─────────────────────────────────────────────────────────────────────────

    def get_results_dataset(self):
        """Return the xarray Dataset of analysis results.

        Returns the dataset cached by _reanalyze_with_dedup() so downstream
        consumers (plot widgets, result handlers) never trigger a fresh
        model.get_results() rebuild — after clear_intermediate_results() the raw
        records are empty, so the cached copy is the only complete dataset.
        """
        if self.grillage_model.model is None:
            return None
        cached = getattr(self.grillage_model, '_deduplicated_results', None)
        if cached is not None:
            return cached
        return self.grillage_model.model.get_results()
    
    def get_results(self) -> dict:
        """Return the dictionary of design check outputs and results."""
        return dict(self.output_dict)

    # ─────────────────────────────────────────────────────────────────────────
    # 2-D analysis result factory
    # ─────────────────────────────────────────────────────────────────────────

    def get_result_handler(self) -> PlateGirderAnalysisResults | None:
        """
        Build and return a PlateGirderAnalysisResults bound to the current
        analysis dataset and grillage model.

        This is the **canonical factory** for PlateGirderAnalysisResults in
        the entire application.  All callers — dialogs, widgets, scripts —
        must obtain their handler from this method, never construct one
        themselves.

        Returns
        -------
        PlateGirderAnalysisResults or None
            A fully initialised result handler ready to be injected into a
            GirderGraphEngine, or None if analysis has not been run.

        Notes
        -----
        This method is safe to call multiple times; each call constructs a
        fresh handler bound to the current dataset snapshot.  If you need to
        share one handler across several components (e.g. to avoid duplicate
        construction), call this once, hold the reference, and pass it
        explicitly to build_graph_engine().
        """
        results = self.get_results_dataset()
        if results is None:
            return None
        return PlateGirderAnalysisResults(
            dataset=results,
            bridge=self.grillage_model,
        )

    def compute_load_effects_cache(self) -> None:
        """
        Pre-compute per-girder, per-load-case max/min Mz and Vy and store on
        ``self._load_effects_cache``.  Called once at the end of design() so
        that Generate Results tables open instantly without re-querying OpenSeesPy.

        The handler is built with the actual deck-overhang edge_dist so that
        build_girders() labels the first/last members as EB1/EB2 when an
        overhang exists — allowing build_load_effects_cache() to skip them.
        """
        from osdagbridge.core.bridge_types.plate_girder.results_data import (
            build_load_effects_cache, build_deflections_cache, build_forces_summary,
        )
        results = self.get_results_dataset()
        if results is None:
            self._load_effects_cache        = {}
            self._deflections_cache         = {}
            self._lc_summary       = {}
            self._reaction_summary= {}
            return
        edge_dist = self.get_edge_dist()
        rh = PlateGirderAnalysisResults(
            dataset=results,
            bridge=self.grillage_model,
            edge_dist=edge_dist,
        )
        self._load_effects_cache = build_load_effects_cache(rh)
        self._deflections_cache  = build_deflections_cache(rh)
        ch4 = build_forces_summary(rh, self._load_effects_cache)
        self._lc_summary       = ch4["load_cases"]
        self._reaction_summary= ch4["reactions"]

    def get_3d_cad_parameters(self) -> BridgeParametersDTO:
        """
        Build a BridgeParametersDTO for 3D CAD rendering.

        All values are read from ``self.output_dict`` — the immutable snapshot of
        ``input_dict`` captured at the start of ``design()``.  This includes girder
        geometry, span, carriageway width, footpath/median/skew settings, and
        additional-input keys such as deck thickness.

        Must be called after design() has fully run.
        """
        inp = self.output_dict

        steel_grade    = str(self.output_dict.get(KEY_GIRDER)).strip()
        concrete_grade = str(self.output_dict.get(KEY_DECK_CONCRETE_GRADE_BASIC)).strip()

        # output_dict values are in SI metres; BridgeParametersDTO expects mm.
        # CAD currently renders a single uniform segment, so use the representative
        # (first) girder via resolve_girder_value (tolerates per-girder keys).
        gv = lambda key: resolve_girder_value(inp, key)
        D       = gv(KEY_MP_GIRDER_DEPTH)                   * 1e3
        tw      = gv(KEY_MP_GIRDER_WEB_THICKNESS)           * 1e3
        B_top   = gv(KEY_MP_GIRDER_TOP_FLANGE_WIDTH)        * 1e3
        t_f_top = gv(KEY_MP_GIRDER_TOP_FLANGE_THICKNESS)    * 1e3
        B_bot   = gv(KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH)     * 1e3
        t_f_bot = gv(KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS) * 1e3

        span_mm = float(self.output_dict[KEY_SPAN]) * 1e3
        cw_each_way_m = float(self.output_dict[KEY_CARRIAGEWAY_WIDTH])
        _skew_raw = self.output_dict.get(KEY_SKEW_ANGLE)
        skew = 0.0 if (_skew_raw is None or str(_skew_raw).strip().lower() in ("", "none")) else float(_skew_raw)

        footpath_str   = str(self.output_dict.get(KEY_FOOTPATH,       "None")).strip()
        include_median = str(self.output_dict.get(KEY_INCLUDE_MEDIAN, "No")).strip().lower() == "yes"

        if footpath_str in ("None", ""):
            footpath_config   = "NONE"
            footpath_width_mm = 0.0
            railing_width_mm  = 0.0
        elif "Both" in footpath_str:
            footpath_config   = "BOTH"
            footpath_width_mm = DEFAULT_FOOTPATH_WIDTH * 1e3
            railing_width_mm  = DEFAULT_RAILING_WIDTH  * 1e3
        else:
            footpath_config   = "LEFT"
            footpath_width_mm = DEFAULT_FOOTPATH_WIDTH * 1e3
            railing_width_mm  = DEFAULT_RAILING_WIDTH  * 1e3

        # geometry.carriageway_width is entered as "Each way" in UI.
        # For divided carriageway with median, CAD expects total traffic width.
        cw_m = (2.0 * cw_each_way_m) if include_median else cw_each_way_m
        cw_mm = cw_m * 1e3

        deck_t_mm = deck_thickness_from_inputs(self.output_dict, _DEFAULT_DECK_THICKNESS_MM) * 1e3
        cross_bracing_mm = DEFAULT_CROSS_BRACING_SPACING * 1e3

        girder_segment = GirderSegmentDTO(
            length=span_mm,
            D=D,
            tw=tw,
            T_ft=t_f_top,
            T_fb=t_f_bot,
            B_ft=B_top,
            B_fb=B_bot,
        )

        _angle_dims = SectionDimsDTO(leg_h=100, leg_w=50, connection_type="LONGER_LEG")
        _small_dims = SectionDimsDTO(leg_h=80,  leg_w=40, connection_type="LONGER_LEG")


        raw_cb_value = self.output_dict.get(KEY_CB_TYPE, ["IRC 5 - RCC Crash Barrier"])
        raw_cb_string = raw_cb_value[0] if isinstance(raw_cb_value, list) else raw_cb_value
        if raw_cb_string == "IRC 5 - RCC Crash Barrier":
            resolved_barrier_type = KEY_CRASH_BARRIER_TYPE[2]               # "Rigid"
            resolved_cb_subtype = KEY_RIGID_CRASH_BARRIER_TYPE[0]           # "IRC-5R"
        elif raw_cb_string == "IRC 5 - High Containment RCC Crash Barrier":
            resolved_barrier_type = KEY_CRASH_BARRIER_TYPE[2]               # "Rigid"
            resolved_cb_subtype = KEY_RIGID_CRASH_BARRIER_TYPE[1]           # "High Containment"
        elif raw_cb_string == "IRC 5 - Metallic Crash Barrier with Single W-Beam":
            resolved_barrier_type = KEY_CRASH_BARRIER_TYPE[1]               # "Semi-Rigid"
            resolved_cb_subtype = KEY_METALLIC_CRASH_BARRIER_TYPE[0]        # "Single W-Beam"
        elif raw_cb_string == "IRC 5 - Metallic Crash Barrier with Double W-Beam":
            resolved_barrier_type = KEY_CRASH_BARRIER_TYPE[1]               # "Semi-Rigid"
            resolved_cb_subtype = KEY_METALLIC_CRASH_BARRIER_TYPE[1]        # "Double W-Beam"
        else:
            # Fallback for "Custom" or empty values
            resolved_barrier_type = "Rigid"
            resolved_cb_subtype = "IRC-5R"

        raw_rl_value = self.output_dict.get(KEY_RL_TYPE, ["IRC 5 RCC railing"])
        raw_rl_string = raw_rl_value[0] if isinstance(raw_rl_value, list) else raw_rl_value
        if raw_rl_string == "IRC 5 - RCC Railing":
            resolved_railing_value = KEY_RAILING_TYPE[0]
        elif raw_rl_string == "IRC 5 - Steel Railing":
            resolved_railing_value = KEY_RAILING_TYPE[1]
        else:
            resolved_railing_value = KEY_RAILING_TYPE[0]

        # Median type mapping:
        # The Additional Inputs UI stores IRC-facing display labels, while the CAD
        # generator currently accepts only the broad internal median categories from
        # KEY_MEDIAN_TYPE:
        #   - "Raised Kerb"
        #   - "RCC Crash Barrier"
        #   - "Metallic Crash Barrier"
        #
        # Because the current BridgeParametersDTO has only `median_type` and no separate
        # `median_subtype`, both metallic UI options are intentionally collapsed to
        # KEY_MEDIAN_TYPE[2] ("Metallic Crash Barrier"):
        #   - "IRC 5 - Metallic Crash Barrier with Single W-Beam"
        #   - "IRC 5 - Metallic Crash Barrier with Double W-Beam"
        #
        # TODO: Add a dedicated median_subtype field to BridgeParametersDTO and CAD
        # generator so Single W-Beam and Double W-Beam median barriers can be preserved
        # separately instead of being reduced to the broad metallic category.

        raw_md_value = self.output_dict.get(KEY_MD_TYPE, ["IRC 5 - RCC Crash Barrier"])
        raw_md_string = raw_md_value[0] if isinstance(raw_md_value, list) else raw_md_value
        raw_md_string = str(raw_md_string or "").strip()

        if raw_md_string == "IRC 5 - Raised Kerb":
            resolved_median_type = KEY_MEDIAN_TYPE[0]  # "Raised Kerb"
        elif raw_md_string == "IRC 5 - RCC Crash Barrier":
            resolved_median_type = KEY_MEDIAN_TYPE[1]  # "RCC Crash Barrier"
        elif raw_md_string.startswith("IRC 5 - Metallic Crash Barrier"):
            resolved_median_type = KEY_MEDIAN_TYPE[2]  # "Metallic Crash Barrier"
        elif raw_md_string in KEY_MEDIAN_TYPE:
            resolved_median_type = raw_md_string
        else:
            resolved_median_type = KEY_MEDIAN_TYPE[1]  # safe default: RCC

        print("DEBUG railing raw:", raw_rl_string)
        print("DEBUG railing resolved:", resolved_railing_value)
        print("DEBUG girder spacing input m:", self.output_dict[KEY_TS_GIRDER_SPACING])
        print("DEBUG girder spacing dto mm:", self.output_dict[KEY_TS_GIRDER_SPACING] * 1e3)

        # --- Stiffeners: read from flat per-girder keys in output_dict ---
        # Keys are stored as  "<KEY_MP_STIFFENER_xxx>.G{gi}.M1".
        _is_optimized = str(inp.get(KEY_DESIGN_MODE, "Optimized")).strip() == "Optimized"

        num_girders = int(self.output_dict[KEY_TS_NO_OF_GIRDERS])
        stiffeners_dict = {}

        for i in range(num_girders):
            gi = i + 1
            # Fetch girder-specific inputs
            def _stiff_inp_gi(base_key, fallback=None):
                v = inp.get(f"{base_key}.G{gi}.M1")
                if v is not None and str(v).strip() not in ("", "None", "NA"):
                    return str(v).strip()
                return fallback

            g_int_spacing_raw = _stiff_inp_gi(KEY_MP_STIFFENER_INTERMEDIATE_SPACING)
            g_int_thick_raw = _stiff_inp_gi(KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS)
            g_int_outstand_raw = _stiff_inp_gi(KEY_MP_STIFFENER_INTERMEDIATE_OUTSTAND)

            if _is_optimized:
                if g_int_spacing_raw is not None and str(g_int_spacing_raw).strip() not in ("", "0", "0.0"):
                    g_int_stiff_on = True
                    g_int_spacing = float(g_int_spacing_raw)
                    g_int_thickness = float(g_int_thick_raw)
                    g_int_outstand = float(g_int_outstand_raw)
                else:
                    g_int_stiff_on = False
                    g_int_spacing = 0.0
                    g_int_thickness = 0.0
                    g_int_outstand = None
            else:
                g_int_stiff_flag = _stiff_inp_gi(KEY_MP_STIFFENER_INTERMEDIATE, "No")
                g_int_stiff_on   = str(g_int_stiff_flag).strip().lower() == "yes"

                if g_int_stiff_on:
                    g_int_spacing = float(g_int_spacing_raw)
                    g_int_thickness = float(g_int_thick_raw)

                    g_int_outstand = float(g_int_outstand_raw)
                else:
                    g_int_spacing = 0.0
                    g_int_thickness = 0.0
                    g_int_outstand = None

            g_long_stiff_raw = _stiff_inp_gi(KEY_MP_STIFFENER_LONGITUDINAL, "No")
            g_long_stiff_on  = str(g_long_stiff_raw).strip().lower() not in ("no", "none", "")
            g_num_long_stiff = 1
            if g_long_stiff_on:
                import re as _re
                _m = _re.search(r"\d+", g_long_stiff_raw)
                g_num_long_stiff = int(_m.group()) if _m else 1

            g_long_thick_raw = _stiff_inp_gi(KEY_MP_STIFFENER_LONGITUDINAL_THICKNESS)

            if not _is_optimized:
                if g_long_stiff_on:
                    g_long_thickness = float(g_long_thick_raw)
                else:
                    g_long_thickness = 0.0
            else:
                g_long_thickness = float(g_long_thick_raw)

            g_bear_pairs_raw = _stiff_inp_gi(KEY_MP_STIFFENER_NO_BEARING_STIFFENERS)
            g_bear_thick_raw = _stiff_inp_gi(KEY_MP_STIFFENER_BEARING_THICKNESS)
            g_bear_outstand_raw = _stiff_inp_gi(KEY_MP_STIFFENER_BEARING_OUTSTAND)

            if not _is_optimized:
                g_num_bear_pairs = max(1, int(float(g_bear_pairs_raw)))

                g_bear_thickness = float(g_bear_thick_raw)

                g_bear_outstand = float(g_bear_outstand_raw)
            else:
                g_num_bear_pairs = max(1, int(float(g_bear_pairs_raw))) 
                g_bear_thickness = float(g_bear_thick_raw)
                g_bear_outstand = float(g_bear_outstand_raw)

            stiffeners_dict[i] = {
                "include_intermediate_stiffeners": g_int_stiff_on,
                "intermediate_stiffener_spacing": g_int_spacing,
                "intermediate_stiffener_thickness": g_int_thickness,
                "intermediate_stiffener_outstand": g_int_outstand,
                "num_end_stiffener_pairs": g_num_bear_pairs,
                "end_stiffener_thickness": g_bear_thickness,
                "end_stiffener_outstand": g_bear_outstand,
                "include_longitudinal_stiffeners": g_long_stiff_on,
                "num_longitudinal_stiffeners": max(1, g_num_long_stiff) if g_long_stiff_on else 1,
                "longitudinal_stiffener_thickness": g_long_thickness,
                "longitudinal_stiffener_outstand": None,
            }

        # Keep representative (first girder) values for DTO scalar fields
        rep = stiffeners_dict[0]
        _int_stiff_on = rep["include_intermediate_stiffeners"]
        _int_spacing = rep["intermediate_stiffener_spacing"]
        _int_thickness = rep["intermediate_stiffener_thickness"]
        _int_outstand = rep["intermediate_stiffener_outstand"]
        _num_bear_pairs = rep["num_end_stiffener_pairs"]
        _bear_thickness = rep["end_stiffener_thickness"]
        _bear_outstand = rep["end_stiffener_outstand"]
        _long_stiff_on = rep["include_longitudinal_stiffeners"]
        _num_long_stiff = rep["num_longitudinal_stiffeners"]
        _long_thickness = rep["longitudinal_stiffener_thickness"]

        print(f"DEBUG stiffeners | mode={'Optimized' if _is_optimized else 'Custom'} | intermediate_on={_int_stiff_on} spacing={_int_spacing} thick={_int_thickness} outstand={_int_outstand} | longitudinal_on={_long_stiff_on} count={_num_long_stiff} thick={_long_thickness} | bearing_pairs={_num_bear_pairs} thick={_bear_thickness} outstand={_bear_outstand}")
        print(f"DEBUG stiffeners raw keys | intermediate={inp.get(KEY_MP_STIFFENER_INTERMEDIATE+'.G1.M1')!r} longitudinal={inp.get(KEY_MP_STIFFENER_LONGITUDINAL+'.G1.M1')!r}")

        return BridgeParametersDTO(
            # --- Material Grades ---
            steel_grade=steel_grade,
            concrete_grade=concrete_grade,
            
            # --- Girder ---
            span_length_L=span_mm,
            girder_section_d=D,
            girder_section_bf=B_top,
            girder_section_bf_b=B_bot,
            girder_section_tf=t_f_top,
            girder_section_tf_b=t_f_bot,
            girder_section_tw=tw,
            num_girders=self.output_dict[KEY_TS_NO_OF_GIRDERS],
            girder_spacing=self.output_dict[KEY_TS_GIRDER_SPACING] * 1e3,
            # --- Geometry ---
            skew_angle=skew,
            # --- Deck ---
            carriageway_width=cw_mm,
            deck_thickness=deck_t_mm,
            footpath_config=footpath_config,
            footpath_width=footpath_width_mm,
            railing_width=railing_width_mm,
            # --- Crash barrier (defaults until additional inputs wired) ---
            barrier_type=resolved_barrier_type,
            crash_barrier_subtype=resolved_cb_subtype,
            # --- Median ---
            enable_median=include_median,
            median_type=resolved_median_type,
            # --- Railing (defaults) ---
            rail_count=3,
            railing_type=resolved_railing_value,
            # --- Intermediate stiffeners ---
            include_intermediate_stiffeners=_int_stiff_on,
            intermediate_stiffener_spacing=_int_spacing,
            intermediate_stiffener_thickness=_int_thickness,
            intermediate_stiffener_outstand=_int_outstand,
            # --- End / Bearing stiffeners ---
            num_end_stiffener_pairs=_num_bear_pairs,
            end_stiffener_thickness=_bear_thickness,
            end_stiffener_outstand=_bear_outstand,
            # --- Longitudinal stiffeners ---
            include_longitudinal_stiffeners=_long_stiff_on,
            num_longitudinal_stiffeners=max(1, _num_long_stiff) if _long_stiff_on else 1,
            longitudinal_stiffener_thickness=_long_thickness,
            longitudinal_stiffener_outstand=None,
            # --- Cross bracing ---
            cross_bracing_spacing=cross_bracing_mm,
            bracing_type="K" if "K" in str(inp.get(KEY_MP_CB_TYPE, "X")).upper() else "X",
            x_bracket_option="BOTH",
            k_top_bracket=True,
            diagonal_section_type="ANGLE",
            diagonal_section_dims=_angle_dims,
            diagonal_thickness=8.0,
            top_chord_section_type="DOUBLE_CHANNEL",
            top_chord_section_dims=_small_dims,
            top_chord_thickness=8.0,
            bottom_chord_section_type="ANGLE",
            bottom_chord_section_dims=_small_dims,
            bottom_chord_thickness=8.0,
            # --- End diaphragm ---
            end_diaphragm_type="Cross Bracing",
            end_diaphragm_spacing=200,
            end_diaphragm_bracing_type="X",
            end_diaphragm_diagonal_section_type="ANGLE",
            end_diaphragm_diagonal_section_dims=_angle_dims,
            end_diaphragm_diagonal_thickness=8.0,
            end_diaphragm_top_chord_section_type="CHANNEL",
            end_diaphragm_top_chord_section_dims=_small_dims,
            end_diaphragm_top_chord_thickness=8.0,
            end_diaphragm_bottom_chord_section_type="ANGLE",
            end_diaphragm_bottom_chord_section_dims=_small_dims,
            end_diaphragm_bottom_chord_thickness=8.0,
            end_diaphragm_section="I_SECTION",
            end_diaphragm_dims=ISectionDimsDTO(
                depth=D * 0.6,
                flange_width=B_top,
                web_thickness=tw,
                flange_thickness=t_f_top,
            ),
            # --- Shear studs ---
            # All values are read directly from output_dict with no fallbacks.
            # base_diameter      [KEY_DS_STUD_DIAMETER]             : shank diameter (mm)
            # top_diameter       [KEY_DS_STUD_HEAD_DIAMETER]        : min head diameter = 1.5 x d  [IRC 22:2015 Cl. 606.6]
            # base_height        [KEY_DS_STUD_HEIGHT]               : stud shank height (mm)
            # top_height         [KEY_DS_STUD_HEAD_HEIGHT]          : min head height = 0.667 x d  [IS 3935:1966]
            # num_per_section    [KEY_DS_STUD_COUNT]                : studs per section
            # transverse_spacing [KEY_DS_STUD_TRANSVERSE_SPACING]   : transverse spacing (mm)
            shear_stud_params=ShearStudParamsDTO(
                base_diameter      = float(inp[KEY_DS_STUD_DIAMETER]),
                top_diameter       = float(inp[KEY_DS_STUD_HEAD_DIAMETER]),
                base_height        = float(inp[KEY_DS_STUD_HEIGHT]),
                top_height         = float(inp[KEY_DS_STUD_HEAD_HEIGHT]),
                num_per_section    = int(float(inp[KEY_DS_STUD_COUNT])),
                transverse_spacing = float(inp[KEY_DS_STUD_TRANSVERSE_SPACING]),
                pitch=500,
            ),
            # --- Girder segments (single uniform segment) ---
            girder_segments=[girder_segment],
            girder_segments_dict={},
            stiffeners_dict=stiffeners_dict,
            output_dict=self.output_dict,
        )



    def get_ifc_export_parameters(self, input_dict: dict | None = None) -> BridgeParametersDTO:
        """
        Build a BridgeParametersDTO for IFC export.

        Identical to get_3d_cad_parameters() but overrides crash-barrier,
        median, railing, footpath-width and railing-width fields from the
        supplied input_dict dict (values from the Additional Inputs
        dialog that are not part of the basic input set).

        Must be called after design() has fully run.
        """
        params = self.get_3d_cad_parameters()
        ai = input_dict or {}

        # --- Crash Barrier ---
        barrier_label = str(ai.get("crash_barrier_type", params.barrier_type))
        params.barrier_type = barrier_label
        if "High Containment" in barrier_label:
            params.crash_barrier_subtype = "High Containment"
        elif "Double W-Beam" in barrier_label or "Double W-beam" in barrier_label:
            params.crash_barrier_subtype = "Double W-beam"
        elif "Single W-Beam" in barrier_label or "Single W-beam" in barrier_label:
            params.crash_barrier_subtype = "Single W-beam"
        else:
            params.crash_barrier_subtype = "IRC-5R"

        # --- Median ---
        params.median_type = str(ai.get("median_type", params.median_type))

        # --- Railing ---
        railing_raw = str(ai.get("railing_type", params.railing_type))
        params.railing_type = (
            "IRC 5 - Steel Railing" if "steel" in railing_raw.lower() else "IRC 5 - RCC Railing"
        )
        params.rail_count = int(ai.get("railing_rail_count", params.rail_count))

        # --- Footpath / railing widths (additional input may override default) ---
        if KEY_TS_FOOTPATH_WIDTH in ai:
            params.footpath_width = float(ai[KEY_TS_FOOTPATH_WIDTH]) * 1000
        if KEY_RAILING_WIDTH in ai:
            params.railing_width = float(ai[KEY_RAILING_WIDTH]) * 1000

        return params

    def build_graph_engine(
        self,
        figure,
        ax_scheme,
        ax_bmd,
        ax_sfd,
        ax_defl,
        result_handler: PlateGirderAnalysisResults | None = None,
    ):
        """
        Construct and return a GirderGraphEngine wired to this bridge's
        result handler.

        This keeps GirderGraphEngine construction out of dialogs and widgets.
        The caller owns the matplotlib Figure and axes; this method assembles
        the engine and injects the data source.

        Parameters
        ----------
        figure : matplotlib.figure.Figure
            Shared matplotlib Figure owned by the calling dialog or widget.
        ax_scheme : matplotlib.axes.Axes
            Top panel — girder support schematic.
        ax_bmd : matplotlib.axes.Axes
            Bending moment diagram panel.
        ax_sfd : matplotlib.axes.Axes
            Shear force diagram panel.
        ax_defl : matplotlib.axes.Axes
            Deflection diagram panel.
        result_handler : PlateGirderAnalysisResults, optional
            If provided, this handler is injected directly.  If None,
            ``get_result_handler()`` is called automatically.  Pass an
            explicit handler when you have already called
            ``get_result_handler()`` and want to reuse the same instance
            across multiple engines.

        Returns
        -------
        GirderGraphEngine
            Fully initialised engine, ready to call ``get_girder_keys()``,
            ``extract_member_results()``, and ``render_plots()``.

        Raises
        ------
        RuntimeError
            Propagated from ``get_result_handler()`` if ``design()`` /
            ``analyze()`` has not yet been called.

        Notes
        -----
        GirderGraphEngine is imported inside this method body (deferred
        import) to keep plategirderbridge.py's top-level import cost low.
        The import only executes when a dialog actually requests a 2-D plot.
        """
        from osdagbridge.core.bridge_types.plate_girder.graph_engine import (
            GirderGraphEngine,
        )
        handler = (
            result_handler
            if result_handler is not None
            else self.get_result_handler()
        )
        return GirderGraphEngine(
            figure=figure,
            ax_scheme=ax_scheme,
            ax_bmd=ax_bmd,
            ax_sfd=ax_sfd,
            ax_defl=ax_defl,
            result_handler=handler,
        )

    def get_available_loadcases(self) -> list[str]:
        """Return sorted list of loadcase name strings from the results dataset."""
        results = self.get_results_dataset()
        handler = PlateGirderAnalysisResults(dataset=results, bridge=self.grillage_model)
        return [str(lc) for lc in handler.get_available_loadcases()]
    
    def get_dcr_engine_for_selection(
        self, girder_name: str | None, load_case: str | None
    ) -> "DCREngine | None":
        """
        Single source of truth for DCR computation.
        Returns a fully-run DCREngine for the given (girder, loadcase).
        Both the Output Dock percent bars and the Steel Design check cards
        call this — never compute DCR anywhere else.
        """


        dr = getattr(self, "design_results", None)
        if not dr:
            return None

        per_girder = dr.get("per_girder", {})
        if not per_girder:
            return None

        if girder_name and girder_name in per_girder:
            girder_names = [girder_name]
        else:
            girder_names = list(per_girder)

        # "Design Envelope": for each check, the worst (highest) utilization across only the load cases that affect that check. Built from the already-computed per-LC check results rather than a single synthetic demand — see designer.design_envelope_engine. Check gating by lc_type means a load case only contributes the checks it actually influences (LTB from SW/DL-stage cases, fatigue from frequent-SLS cases, etc.).
        if load_case == "Design Envelope":
            return design_envelope_engine(girder_names, per_girder)

        # per_girder's key order is already edge-beam-free and in physical girder
        # order (built from build_girders() minus EB1/EB2) — its position is the
        # 0-based girder_index that resolve_girder_value()'s ".G{i+1}.M1" keys expect.
        _girder_order = list(per_girder)

        stored_r = dr.get("bs_R_kN", 0.0)

        best_engine = None

        for g_name in girder_names:
            try:
                config = BridgeConfig.from_plate_girder_bridge(
                    self, girder_index=_girder_order.index(g_name)
                )
            except Exception:
                continue

            # Mirror the bearing reaction resolved during run_design_check so
            # bearing stiffener checks fire here too (from_plate_girder_bridge
            # always leaves bs_R_kN=0.0).
            if config.stiffener is not None and stored_r and stored_r > 0.0:
                config.stiffener.bs_R_kN = float(stored_r)

            g_data = per_girder.get(g_name, {})
            per_lc = g_data.get("per_lc", {})
            lc_demand = per_lc.get(load_case)
            if not lc_demand:
                continue

            g_env = g_data.get("demand", {})

            demand = DemandEnvelope(
                Mu_kNm               = lc_demand.get("Mu_kNm",              0.0),
                Vu_kN                = lc_demand.get("Vu_kN",               0.0),
                Nu_kN                = lc_demand.get("Nu_kN",               0.0),
                M_construction_kNm   = lc_demand.get("M_construction_kNm",  0.0),
                M_girder_sw_kNm      = lc_demand.get("M_girder_sw_kNm",     0.0),
                M_sls_kNm            = lc_demand.get("M_sls_kNm",           0.0),
                V_sls_kN             = lc_demand.get("V_sls_kN",            0.0),
                delta_live_mm        = lc_demand.get("delta_live_mm",       0.0),
                delta_total_mm       = lc_demand.get("delta_total_mm",      0.0),
                stress_range_MPa     = lc_demand.get("stress_range_MPa",    0.0),
                shear_range_MPa      = lc_demand.get("shear_range_MPa",     0.0),
                Mx_kNm               = lc_demand.get("Mx_kNm",              0.0),
                My_kNm               = lc_demand.get("My_kNm",              0.0),
                Vz_kN                = lc_demand.get("Vz_kN",               0.0),
                Dx_mm                = lc_demand.get("Dx_mm",               0.0),
                Dy_mm                = lc_demand.get("Dy_mm",               0.0),
                Dz_mm                = lc_demand.get("Dz_mm",               0.0),
                Vr_kN                = g_env.get("Vr_kN", 0.0),        # cross-LC aggregate → girder level
                Nsc                  = int(dr.get("Nsc", 2_000_000)),  # config constant
                governing_combination = load_case,
                member               = g_name,
                source               = "per_lc",
                lc_type              = lc_demand.get("lc_type", ""),
            )
            try:
                capacity = IRC22CapacityCalculator(config).compute_all(
                    Vu_kN=demand.Vu_kN,
                    stress_range_MPa=demand.stress_range_MPa,
                    M_sls_kNm=demand.M_sls_kNm,
                    V_sls_kN=demand.V_sls_kN,
                    Vr_kN=demand.Vr_kN,
                )
                engine = DCREngine(demand, capacity)
                engine.run_all_checks()

                max_dcr  = engine.max_dcr()
                best_max = best_engine.max_dcr() if best_engine else -1.0
                if max_dcr > best_max:
                    best_engine = engine
            except Exception:
                continue

        return best_engine

    def get_dcr_for_selection(
        self, girder_name: str | None, load_case: str | None
    ) -> dict[str, float]:
        """
        Return DCR percentages for the Output Dock percent bars.
        Thin wrapper around get_dcr_engine_for_selection — no computation here.
        """
        from osdagbridge.core.utils.common import (
            KEY_UTIL_FLEXURE, KEY_UTIL_SHEAR, KEY_UTIL_INTERACTION,
            KEY_UTIL_LTB, KEY_UTIL_LONG_TRANS_SHEAR, KEY_UTIL_FATIGUE,
            KEY_UTIL_STRESS_LIMITATION, KEY_UTIL_DEFLECTION_CRACK,
        )

        engine = self.get_dcr_engine_for_selection(girder_name, load_case)
        if engine is None:
            return {}

        by_id: dict[int, float] = {}
        for c in engine.checks:
            if c.check_id not in by_id or c.dcr > by_id[c.check_id]:
                by_id[c.check_id] = c.dcr

        def _max_ids(*ids):
            vals = [by_id[i] for i in ids if i in by_id]
            return (max(vals) * 100) if vals else None

        return {
            KEY_UTIL_FLEXURE:           _max_ids(1),
            KEY_UTIL_SHEAR:             _max_ids(2),
            KEY_UTIL_INTERACTION:       _max_ids(3, 4),
            KEY_UTIL_LTB:               _max_ids(5),
            KEY_UTIL_LONG_TRANS_SHEAR:  _max_ids(6, 7, 16, 17),
            KEY_UTIL_FATIGUE:           _max_ids(8, 9),
            KEY_UTIL_STRESS_LIMITATION: _max_ids(10, 11, 12),
            KEY_UTIL_DEFLECTION_CRACK:  _max_ids(13, 14, 15),
        }

    def get_nodes_members(self) -> tuple[dict, dict]:
        """Return (nodes, members) dicts built from the active openseespy model."""
        return build_nodes_members()

    def get_edge_dist(self) -> float:
        """Return the deck overhang distance (0.0 when no overhang)."""
        return self.output_dict.get(KEY_TS_DECK_OVERHANG) or 0.0

    def build_figure_sfd(self, ds, force_key: str):
        """Build and return a matplotlib Figure for the SFD of the given dataset slice."""
        nodes, members = self.get_nodes_members()
        return build_figure_sfd(ds, force_key, nodes, members, edge_dist=self.get_edge_dist())

    def build_figure_bmd(self, ds, force_key: str):
        """Build and return a matplotlib Figure for the BMD of the given dataset slice."""
        nodes, members = self.get_nodes_members()
        return build_figure_bmd(ds, force_key, nodes, members, edge_dist=self.get_edge_dist())

    # def build_figure_bmd_contour(self, ds, force_key: str):
    #     """Build and return a matplotlib Figure for the BMD contour plot (commented out)."""
    #     nodes, members = self.get_nodes_members()
    #     return build_figure_bmd_contour(ds, force_key, nodes, members, edge_dist=self.get_edge_dist())

    def build_figure_deflection(self, ds, disp_key: str):
        """Build and return a matplotlib Figure for the deflection diagram of the given dataset slice."""
        nodes, members = self.get_nodes_members()
        return build_figure_deflection(ds, disp_key, nodes, members, edge_dist=self.get_edge_dist())

    def build_figure_grillage(self):
        """Build and return a matplotlib Figure showing only the bridge grillage mesh."""
        nodes, members = self.get_nodes_members()
        return build_figure_grillage(nodes, members)

    def figure_to_bytes(self, fig, fmt: str = "png", dpi: int = 150) -> bytes:
        """Render a matplotlib Figure to raw bytes (PNG by default)."""
        return figure_to_bytes(fig, fmt=fmt, dpi=dpi)

    # ─────────────────────────────────────────────────────────────────────────
    def _query_crossbracing_section(self, designation: str) -> dict | None:
        """
        Query the Osdag database for details of a cross bracing member section
        using its designation.
        """
        if not designation:
            return None
        
        # Clean designation: strip spaces and any double-section prefix '2-'
        designation = designation.strip()
        if designation.startswith("2-"):
            designation = designation[2:].strip()
            
        if not _DB_PATH.exists():
            raise LookupError(f"Database not found at {_DB_PATH}")

        # Build a regex numbers-like pattern to search with LIKE, as in UI
        import re
        nums = re.findall(r"\d+(?:\.\d+)?", designation)
        if not nums:
            return None
        like_pattern = "%" + "%".join(nums) + "%"

        try:
            con = sqlite3.connect(_DB_PATH)
            cur = con.cursor()

            # 1. Try EqualAngle and UnequalAngle
            for table in ("EqualAngle", "UnequalAngle"):
                # First try exact match
                cur.execute(
                    f'SELECT Designation, Mass, Area, a, b, t, Iz, Iy, "Iv(min)", rz, ry, "rv(min)", Zz, Zy, Zpz, Zpy FROM {table} WHERE Designation = ?',
                    (designation,)
                )
                row = cur.fetchone()
                if not row:
                    # Try case-insensitive exact match
                    cur.execute(
                        f'SELECT Designation, Mass, Area, a, b, t, Iz, Iy, "Iv(min)", rz, ry, "rv(min)", Zz, Zy, Zpz, Zpy FROM {table} WHERE LOWER(Designation) = LOWER(?)',
                        (designation,)
                    )
                    row = cur.fetchone()
                if not row:
                    # Fallback to LIKE with numbers
                    cur.execute(
                        f'SELECT Designation, Mass, Area, a, b, t, Iz, Iy, "Iv(min)", rz, ry, "rv(min)", Zz, Zy, Zpz, Zpy FROM {table} WHERE Designation LIKE ?',
                        (like_pattern,)
                    )
                    row = cur.fetchone()
                if row:
                    con.close()
                    
                    def val_f(val):
                        return float(val) if val is not None else 0.0

                    return {
                        "designation": row[0],
                        "type": "ANGLE",
                        "L": val_f(row[3]) / 1000.0,
                        "H": val_f(row[4]) / 1000.0,
                        "B": val_f(row[5]) / 1000.0,
                        "tw": val_f(row[5]) / 1000.0,
                        "tF": val_f(row[5]) / 1000.0,
                        "rz": val_f(row[9]),
                        "M": val_f(row[1]),
                        "A": val_f(row[2]),
                        "Iz": val_f(row[6]),
                        "Iv": val_f(row[8]),
                        "rv": val_f(row[11]),
                        "Zz": val_f(row[12]),
                        "Zv": val_f(row[13]),
                        "Zuz": val_f(row[14]),
                        "Zuv": val_f(row[15]),
                    }

            # 2. Try Channels
            cur.execute(
                'SELECT Designation, Mass, Area, D, B, tw, T, Iz, Iy, rz, ry, Zz, Zy, Zpz, Zpy FROM Channels WHERE Designation = ?',
                (designation,)
            )
            row = cur.fetchone()
            if not row:
                cur.execute(
                    'SELECT Designation, Mass, Area, D, B, tw, T, Iz, Iy, rz, ry, Zz, Zy, Zpz, Zpy FROM Channels WHERE LOWER(Designation) = LOWER(?)',
                    (designation,)
                )
                row = cur.fetchone()
            if not row:
                cur.execute(
                    'SELECT Designation, Mass, Area, D, B, tw, T, Iz, Iy, rz, ry, Zz, Zy, Zpz, Zpy FROM Channels WHERE Designation LIKE ?',
                    (like_pattern,)
                )
                row = cur.fetchone()
            if row:
                con.close()
                
                def val_f(val):
                    return float(val) if val is not None else 0.0

                return {
                    "designation": row[0],
                    "type": "CHANNEL",
                    "L": val_f(row[3]) / 1000.0,
                    "H": val_f(row[4]) / 1000.0,
                    "B": val_f(row[4]) / 1000.0,
                    "tw": val_f(row[5]) / 1000.0,
                    "tF": val_f(row[6]) / 1000.0,
                    "rz": val_f(row[9]),
                    "M": val_f(row[1]),
                    "A": val_f(row[2]),
                    "Iz": val_f(row[7]),
                    "Iv": val_f(row[8]),
                    "rv": val_f(row[10]),
                    "Zz": val_f(row[11]),
                    "Zv": val_f(row[12]),
                    "Zuz": val_f(row[13]),
                    "Zuv": val_f(row[14]),
                }

            con.close()
        except sqlite3.Error:
            pass

        return None

    def _to_float(self, key: str, fallback: float) -> float:
        """Safely convert a input_dict value to float, falling back on error."""
        val = self.input_dict.get(key)
        if val is None or str(val).strip().lower() in ("", "none"):
            return fallback
        try:
            return float(val)
        except (TypeError, ValueError):
            return fallback
        

    def store_design_results(self, design_results: dict) -> None:
        """Write every IRC 22:2015 design-check output into self.output_dict.

        Reads from two sources:
        - design_results  : mm / MPa / kN / kNm values from run_design_check()
        - self.input_dict : SI values (m, Pa, m^4 …) from initial sizing

        All KEY_SD_* output-dock keys are populated here so every tab can read
        directly from self.output_dict without touching design_results themselves.

        Call this immediately after run_design_check() inside _run_dcr_checks().
        output_dict must still be mutable (i.e. before the MappingProxyType freeze).
        """
        dr  = design_results          # alias: mm/MPa/kN from designer pipeline
        inp = self.input_dict         # alias: SI (m, Pa) from initial sizing
        out = self.output_dict        # must be mutable dict at this point

        # ── 1. Category URs — eight utilisation percent values ─────────────────
        cat_urs = dr.get("category_urs", {})
        out[KEY_UTIL_FLEXURE]          = cat_urs.get(1, {}).get("max_dcr", 0.0) * 100
        out[KEY_UTIL_SHEAR]            = cat_urs.get(2, {}).get("max_dcr", 0.0) * 100
        out[KEY_UTIL_INTERACTION]      = cat_urs.get(3, {}).get("max_dcr", 0.0) * 100
        out[KEY_UTIL_LTB]              = cat_urs.get(4, {}).get("max_dcr", 0.0) * 100
        out[KEY_UTIL_LONG_TRANS_SHEAR] = cat_urs.get(5, {}).get("max_dcr", 0.0) * 100
        out[KEY_UTIL_FATIGUE]          = cat_urs.get(6, {}).get("max_dcr", 0.0) * 100
        out[KEY_UTIL_STRESS_LIMITATION]= cat_urs.get(7, {}).get("max_dcr", 0.0) * 100
        out[KEY_UTIL_DEFLECTION_CRACK] = cat_urs.get(8, {}).get("max_dcr", 0.0) * 100

        # ── 2. Dimensional card ─────────────────────────────────────────────────
        # Grade, type, designation, class, and all plate dimensions in mm.
        out[KEY_SD_GRADE_OF_MATERIAL]       = dr["steel_grade"]
        out[KEY_SD_SECTION_TYPE]            = dr["fabrication"].title()   # "Welded" / "Rolled"

        # Designation: "D × bf_top × tf_top × bf_bot × tf_bot" (overall depth D, not clear web)
        # Built directly here from design_results plate dimensions (all in mm).
        dw  = dr["dw_mm"]
        D   = dr["D_mm"]
        bft = dr["bf_top_mm"]
        tft = dr["tf_top_mm"]
        bfb = dr["bf_bot_mm"]
        tfb = dr["tf_bot_mm"]
        tw  = dr["tw_mm"]
        out[KEY_SD_SECTION_DESIGNATION] = (
            f"{D:.0f} × {bft:.0f} × {tft:.0f} × {bfb:.0f} × {tfb:.0f}"
        )
        out[KEY_SD_SECTION_CLASS]           = dr["section_class_governing"]
        out[KEY_SD_TOTAL_DEPTH]             = D          # mm
        out[KEY_SD_WEB_THICKNESS]           = tw         # mm
        out[KEY_SD_TOP_FLANGE_WIDTH]        = bft        # mm
        out[KEY_SD_TOP_FLANGE_THICKNESS]    = tft        # mm
        out[KEY_SD_BOTTOM_FLANGE_WIDTH]     = bfb        # mm
        out[KEY_SD_BOTTOM_FLANGE_THICKNESS] = tfb        # mm

        # Torsional/warping restraint and web type come from the Additional Inputs
        # dialog, not from the designer pipeline. Read them directly from input_dict
        # so the output card echoes back what the user configured.
        out[KEY_SD_TORSIONAL_RESTRAINT] = inp.get(KEY_MP_GIRDER_TORSIONAL_RESTRAINT, "—")
        out[KEY_SD_WARPING_RESTRAINT]   = inp.get(KEY_MP_GIRDER_WARPING_RESTRAINT,   "—")
        out[KEY_SD_WEB_TYPE]            = inp.get(KEY_MP_GIRDER_WEB_TYPE,            "—")

        # Effective slab width from the composite capacity check (mm)
        out[KEY_SD_EFFECTIVE_SLAB_WIDTH] = dr["beff_mm"]

        # ── 2b. Per-girder dimensional values ───────────────────────────────────
        # The flat KEY_SD_* keys above hold the controlling girder (the Details tab's
        # default). Publish each girder's own section under ".G{n}.M1" so the Steel
        # Design Details tab can show the girder picked in its selector — read only
        # from output_dict. Per-girder sections come from design_results["per_girder"]
        # (see designer.run_design_check); grade/type are global, restraint/web-type
        # are per-girder inputs echoed from input_dict.
        def _gv_or_empty(inp, base_key, gi):
            """Per-girder input value, or '—' when no key variant is present."""
            return resolve_girder_value(inp, base_key, gi)

        per_girder = dr.get("per_girder", {})
        for gi, g_name in enumerate(per_girder):
            sec = per_girder[g_name].get("section")
            if not sec:
                continue
            suf = f".G{gi + 1}.M1"
            out[KEY_SD_GRADE_OF_MATERIAL + suf]       = dr["steel_grade"]
            out[KEY_SD_SECTION_TYPE + suf]            = sec["fabrication"].title()
            out[KEY_SD_SECTION_DESIGNATION + suf]     = sec["designation"]
            out[KEY_SD_SECTION_CLASS + suf]           = sec["section_class"]
            out[KEY_SD_TOTAL_DEPTH + suf]             = sec["D_mm"]
            out[KEY_SD_WEB_THICKNESS + suf]           = sec["tw_mm"]
            out[KEY_SD_TOP_FLANGE_WIDTH + suf]        = sec["bf_top_mm"]
            out[KEY_SD_TOP_FLANGE_THICKNESS + suf]    = sec["tf_top_mm"]
            out[KEY_SD_BOTTOM_FLANGE_WIDTH + suf]     = sec["bf_bot_mm"]
            out[KEY_SD_BOTTOM_FLANGE_THICKNESS + suf] = sec["tf_bot_mm"]
            out[KEY_SD_EFFECTIVE_SLAB_WIDTH + suf]    = sec["beff_mm"]
            out[KEY_SD_TORSIONAL_RESTRAINT + suf] = _gv_or_empty(inp, KEY_MP_GIRDER_TORSIONAL_RESTRAINT, gi)
            out[KEY_SD_WARPING_RESTRAINT + suf]   = _gv_or_empty(inp, KEY_MP_GIRDER_WARPING_RESTRAINT, gi)
            out[KEY_SD_WEB_TYPE + suf]            = _gv_or_empty(inp, KEY_MP_GIRDER_WEB_TYPE, gi)

        # ── 3. Shear connector card ─────────────────────────────────────────────
        # All stud dimensions in mm; strengths in MPa; count and spacing as numbers.
        out[KEY_SD_SHEAR_YIELD_STRENGTH]      = dr.get("stud_fy_MPa", 350.0)   # MPa
        out[KEY_SD_SHEAR_ULTIMATE_STRENGTH]   = dr["stud_fu_MPa"]              # MPa
        out[KEY_SD_SHEAR_DIAMETER]            = dr["stud_dia_mm"]              # mm
        out[KEY_SD_SHEAR_HEIGHT]              = dr["stud_height_mm"]           # mm
        # Transverse spacing: not a direct design_results field — read from
        # Additional Inputs (KEY_DS_STUD_TRANSVERSE_SPACING); fall back to "—".
        out[KEY_SD_SHEAR_TRANSVERSE_SPACING]  = inp.get(
            KEY_DS_STUD_TRANSVERSE_SPACING, "—"
        )
        out[KEY_SD_SHEAR_STUDS_PER_SECTION]   = dr["studs_per_section"]         # count
        out[KEY_SD_SHEAR_LONGITUDINAL_SPACING]= dr["stud_spacing_provided_mm"]  # mm

        # ── 4. Section properties card ──────────────────────────────────────────
        # input_dict stores these in SI (m², m⁴, m³, kg/m).
        # The section-property card is expected to show SI values (matching the
        # initial sizing display), so no unit conversion is applied here.
        out[KEY_MP_GIRDER_MASS]  = inp.get(KEY_MP_GIRDER_MASS,               0.0)   # kg/m
        out[KEY_MP_GIRDER_SECTIONAL_AREA]  = inp.get(KEY_MP_GIRDER_SECTIONAL_AREA,     0.0)   # m²
        out[KEY_MP_GIRDER_SECTIONAL_IZ]    = inp.get(KEY_MP_GIRDER_SECTIONAL_IZ,       0.0)   # m⁴
        out[KEY_MP_GIRDER_SECTIONAL_IY]    = inp.get(KEY_MP_GIRDER_SECTIONAL_IY,       0.0)   # m⁴
        out[KEY_MP_GIRDER_RADIUS_GYRATION_Z]    = inp.get(KEY_MP_GIRDER_RADIUS_GYRATION_Z,  0.0)   # m
        out[KEY_MP_GIRDER_RADIUS_GYRATION_Y]    = inp.get(KEY_MP_GIRDER_RADIUS_GYRATION_Y,  0.0)   # m
        out[KEY_MP_GIRDER_ELASTIC_MODULUS_ZZ]    = inp.get(KEY_MP_GIRDER_ELASTIC_MODULUS_ZZ, 0.0)   # m³ (Ze about zz)
        out[KEY_MP_GIRDER_ELASTIC_MODULUS_ZY]    = inp.get(KEY_MP_GIRDER_ELASTIC_MODULUS_ZY, 0.0)   # m³ (Ze about zy)
        out[KEY_MP_GIRDER_PLASTIC_MODULUS_ZUZ]   = inp.get(KEY_MP_GIRDER_PLASTIC_MODULUS_ZUZ,0.0)   # m³ (Zp about zz)
        out[KEY_MP_GIRDER_PLASTIC_MODULUS_ZUY]   = inp.get(KEY_MP_GIRDER_PLASTIC_MODULUS_ZUY,0.0)   # m³ (Zp about zy)
        out[KEY_MP_GIRDER_TORSION_CONSTANT_IT]    = inp.get(KEY_MP_GIRDER_TORSION_CONSTANT_IT,0.0)   # m³ (torsion J)
        out[KEY_MP_GIRDER_WARPING_CONSTANT_IW]    = inp.get(KEY_MP_GIRDER_WARPING_CONSTANT_IW,0.0)   # m⁶ (warping Iw)

        # Steel section properties come from design_results (mm-based units).
        # Report table expects engineering units: cm², cm⁴, cm³.
        out[KEY_SD_SECTION_PROP_MASS]  = inp.get(KEY_MP_GIRDER_MASS,               0.0)          # kg/m (unchanged)
        out[KEY_SD_SECTION_PROP_AREA]  = round(dr["A_steel_mm2"]   / 1e2,  2)                    # mm²  → cm²
        out[KEY_SD_SECTION_PROP_IZ]    = round(dr["Iz_steel_mm4"]  / 1e4,  2)                    # mm⁴  → cm⁴
        out[KEY_SD_SECTION_PROP_IV]    = inp.get(KEY_MP_GIRDER_SECTIONAL_IY,       0.0)          # m⁴  (unused in report)
        out[KEY_SD_SECTION_PROP_RZ]    = inp.get(KEY_MP_GIRDER_RADIUS_GYRATION_Z,  0.0)          # m   (unused in report)
        out[KEY_SD_SECTION_PROP_RV]    = inp.get(KEY_MP_GIRDER_RADIUS_GYRATION_Y,  0.0)          # m   (unused in report)
        out[KEY_SD_SECTION_PROP_ZZ]    = round(dr["Ze_steel_mm3"]  / 1e3,  2)                    # mm³  → cm³
        out[KEY_SD_SECTION_PROP_ZV]    = inp.get(KEY_MP_GIRDER_ELASTIC_MODULUS_ZY, 0.0)          # m³  (unused in report)
        out[KEY_SD_SECTION_PROP_ZUZ]   = round(dr["Zp_steel_mm3"]  / 1e3,  2)                    # mm³  → cm³
        out[KEY_SD_SECTION_PROP_ZUV]   = inp.get(KEY_MP_GIRDER_PLASTIC_MODULUS_ZUY,0.0)          # m³  (unused in report)
        out[KEY_SD_SECTION_PROP_IT]    = inp.get(KEY_MP_GIRDER_TORSION_CONSTANT_IT,0.0)          # m³  (unused in report)
        out[KEY_SD_SECTION_PROP_IW]    = inp.get(KEY_MP_GIRDER_WARPING_CONSTANT_IW,0.0)          # m⁶  (unused in report)
        out[KEY_SD_COMPOSITE_IZ]       = round(dr["I_comp_short_mm4"] / 1e4, 2)                  # mm⁴  → cm⁴
        out[KEY_SD_PNA_DEPTH]          = round(dr["xu_mm"], 1)                                    # mm

        # ── 4b. Flexure check (Table 5.3): applied moment & design capacity ─────
        # Controlling-girder values from design_results; already in kN·m.
        out[KEY_SD_MU_APPLIED]         = round(dr["Mu_kNm"], 2)                                   # kN·m
        out[KEY_SD_MD_CAPACITY]        = round(dr["Md_kNm"], 2)                                   # kN·m

        # ── 4c. Section classification (Table 5.2): slenderness, limit, class ───
        # Ratios & web limit from classify_section(); classes already strings.
        out[KEY_SD_FLANGE_SLENDERNESS] = dr["b_tf_ratio"]                                         # b/tf
        out[KEY_SD_WEB_SLENDERNESS]    = dr["d_tw_ratio"]                                         # d/tw
        out[KEY_SD_WEB_CLASS_LIMIT]    = dr["web_class_limit"]                                    # limit (×ε)
        out[KEY_SD_FLANGE_CLASS_LIMIT] = dr["flange_class_limit"]                                 # limit (×ε)
        out[KEY_SD_CLASS_FLANGE]       = dr["section_class_flange"]
        out[KEY_SD_CLASS_WEB]          = dr["section_class_web"]

        # ── 4d. Shear check (Table 5.4): applied shear, area, buckling breakdown ─
        out[KEY_SD_SHEAR_VU]           = round(dr["Vu_kN"], 2)                                    # kN
        out[KEY_SD_SHEAR_AV]           = round(dr["Av_mm2"], 1)                                   # mm²
        out[KEY_SD_PANEL_CD]           = dr["panel_cd_ratio"]                                     # c/d (None if unstiffened)
        out[KEY_SD_SHEAR_KV]           = dr["Kv"]
        out[KEY_SD_SHEAR_LAMBDA_W]     = dr["lambda_w"]
        out[KEY_SD_SHEAR_TAU_B]        = round(dr["tau_b_buck_MPa"], 2)                           # MPa
        out[KEY_SD_SHEAR_VCR]          = round(dr["Vcr_kN"], 2)                                   # kN

        # ── 4e. Interaction checks (Table 5.5): high shear, Mdv, M-N terms ──────
        out[KEY_SD_HIGH_SHEAR]         = "Yes" if dr["beta_interaction"] > 0 else "No"
        out[KEY_SD_MDV]                = round(dr["Mdv_kNm"], 2)                                  # kN·m
        _mn_ax, _mn_mo, _mn_r = dr["mn_axial_term"], dr["mn_moment_term"], dr["mn_ratio"]
        out[KEY_SD_MN_AXIAL]           = round(_mn_ax, 2) if _mn_ax is not None else None
        out[KEY_SD_MN_MOMENT]          = round(_mn_mo, 2) if _mn_mo is not None else None
        out[KEY_SD_MN_RATIO]           = round(_mn_r, 3) if _mn_r is not None else None

        # ── 4f. LTB check (Table 5.6, construction stage): Mcr, λ_LT, χ_LT, Mb ──
        out[KEY_SD_LTB_MCR]            = round(dr["Mcr_kNm"], 2)                                  # kN·m
        out[KEY_SD_LTB_LAMBDA]         = round(dr["lambda_LT"], 3)
        out[KEY_SD_LTB_CHI]            = round(dr["chi_LT"], 3)
        out[KEY_SD_LTB_MB]             = round(dr["Mb_kNm"], 2)                                   # kN·m

        # ── 4g. Stiffener design summary (Table 5.7) ────────────────────────────
        # Custom design → user-provided values; Optimized → designer-computed.
        _is_custom_stiff = str(inp.get(KEY_DESIGN_MODE, "Optimized")).strip().lower() in {"custom", "customized"}
        def _rnum(v, nd=1):
            return round(v, nd) if isinstance(v, (int, float)) else v
        out[KEY_SD_STIFF_METHOD]       = dr["stiff_method"]
        out[KEY_SD_STIFF_INT_THICK]    = _rnum(dr["is_tq_mm"] if _is_custom_stiff else dr["stiff_int_thick_req"])
        out[KEY_SD_STIFF_INT_SPACING]  = _rnum(dr["is_c_mm"]  if _is_custom_stiff else dr["stiff_int_space_req"])
        out[KEY_SD_STIFF_END_THICK]    = _rnum(dr["bs_tq_mm"] if _is_custom_stiff else dr["stiff_end_thick_req"])
        out[KEY_SD_STIFF_END_COUNT]    = dr["bs_n_plates"]
        # Longitudinal: only the user can specify them; optimizer adds none.
        _stiff_data  = inp.get("stiffener_by_member") or {}
        _first_stiff = next(iter(_stiff_data.values()), {}) if _stiff_data else {}
        _long_val    = str((_first_stiff or {}).get("longitudinal_stiffener", "No")).strip()
        out[KEY_SD_STIFF_LONG]         = ((_long_val if _long_val and _long_val not in ("None", "NA", "") else "No")
                                          if _is_custom_stiff else "None")

        # ── 4h. Intermediate stiffener checks (Table 5.8 — Custom only) ──────────
        # Verification values; only meaningful in Custom mode (table is omitted in
        # the report otherwise). Iys in mm⁴; Fq/Fqd in kN.
        out[KEY_SD_IS_IYS_MIN]         = round(dr["is_Iys_min_mm4"], 0)                           # mm⁴
        out[KEY_SD_IS_IYS_PROV]        = round(dr["is_Iys_prov_mm4"], 0)                          # mm⁴
        out[KEY_SD_IS_FQ]              = round(dr["is_Fq_kN"], 2)                                 # kN
        out[KEY_SD_IS_FQD]             = round(dr["is_Fqd_kN"], 2)                                # kN

        # ── 4i. Bearing stiffener checks (Table 5.9) — IS 800 Cl.8.7.3 ──────────
        # End panel == bearing stiffener for this bridge. Resistances vs reaction R.
        # Populated in full-check mode; 0 in guidance-only (optimized w/o outstand).
        out[KEY_SD_BS_R]               = round(dr["bs_R_kN"], 2)                                  # kN
        out[KEY_SD_BS_FCDW_WB]         = round(dr["bs_Fcdw_wb_kN"], 2)                            # kN
        out[KEY_SD_BS_FCDW_LC]         = round(dr["bs_Fcdw_lc_kN"], 2)                            # kN
        out[KEY_SD_BS_FPSD]            = round(dr["bs_Fpsd_kN"], 2)                               # kN
        out[KEY_SD_BS_FCD]             = round(dr["bs_Fcd_kN"], 2)                                # kN

        # ── 4j. Deflection checks (Table 5.10) — IRC 22 Cl. 604.3.2 ──────────────
        # Values already computed by run_design_check(); just forward them here.
        # Actual deflections from demand; allowable limits from capacity.
        out[KEY_SD_DEFL_LIVE]        = round(dr["delta_live_mm"],       3)   # mm — actual live-load deflection
        out[KEY_SD_DEFL_TOTAL]       = round(dr["delta_total_mm"],      3)   # mm — actual total-load deflection
        out[KEY_SD_DEFL_ALLOW_LIVE]  = round(dr["defl_limit_live_mm"],  2)   # mm — allowable = L/800
        out[KEY_SD_DEFL_ALLOW_TOTAL] = round(dr["defl_limit_total_mm"], 2)   # mm — allowable = L/600

        # In store_design_results(), replace the stiffener section (── 5. Stiffener table ──) with:

        grade = str(inp.get(KEY_GIRDER, ""))

        # Read stiffener state from the nested structure saved by StiffenerDetailsTab.collect_data()
        stiffener_data = inp.get("stiffener_by_member") or {}
        # Use the first member's state as the representative (bearing stiffeners are per bridge end)
        first_member_state = {}
        if stiffener_data:
            first_key = next(iter(stiffener_data), None)
            if first_key:
                first_member_state = stiffener_data[first_key] or {}

        def _stiff_from_member(key, fallback="NA"):
            v = first_member_state.get(key)
            if v is not None and str(v).strip() not in ("", "None", "NA"):
                return str(v)
            return fallback

        # ── Bearing ─────────────────────────────────────────────────────────────────
        out["stiff_bearing_grade"]     = grade
        out["stiff_bearing_thickness"] = _stiff_from_member("bearing_thickness_value")
        out["stiff_bearing_width"]     = _stiff_from_member("bearing_outstand_mm")
        out["stiff_bearing_spacing"]   = _stiff_from_member("bearing_spacing_mm")

        # ── Intermediate ────────────────────────────────────────────────────────────
        int_stiff_on = _stiff_from_member("intermediate_stiffener", "No") == "Yes"
        if int_stiff_on:
            out["stiff_intermediate_grade"]     = grade
            out["stiff_intermediate_thickness"] = _stiff_from_member("intermediate_thickness_value")
            out["stiff_intermediate_width"]     = _stiff_from_member("intermediate_outstand_mm")
            out["stiff_intermediate_spacing"]   = _stiff_from_member("intermediate_spacing_mm")
        else:
            out["stiff_intermediate_grade"]     = "NA"
            out["stiff_intermediate_thickness"] = "NA"
            out["stiff_intermediate_width"]     = "NA"
            out["stiff_intermediate_spacing"]   = "NA"

        # ── Longitudinal ─────────────────────────────────────────────────────────────
        long_val = _stiff_from_member("longitudinal_stiffener", "No")
        long_stiff_on = (long_val != "No")
        if long_stiff_on:
            out["stiff_longitudinal_grade"]     = grade
            out["stiff_longitudinal_thickness"] = _stiff_from_member("longitudinal_thickness_value")
            out["stiff_longitudinal_width"]     = "NA"
            out["stiff_longitudinal_spacing"]   = "NA"
        else:
            out["stiff_longitudinal_grade"]     = "NA"
            out["stiff_longitudinal_thickness"] = "NA"
            out["stiff_longitudinal_width"]     = "NA"
            out["stiff_longitudinal_spacing"]   = "NA"
            
        # ── 6. Full design_results blob — consumed by dialogs / report tab ──────
        # Store the entire dict under a single key so any tab that needs deeper
        # data (capacity details, per-girder breakdown, report text) can get it
        # without re-running the pipeline.
        out["design_results"] = design_results    

        # ── Torsional / Warping Restraint / Web Type ────────────────────────────────
        # These are Additional Inputs fields. If the user never opened the dialog
        # the keys are absent from input_dict — fall back to IRC 22 design defaults.
        out[KEY_SD_TORSIONAL_RESTRAINT] = str(
            inp.get(KEY_MP_GIRDER_TORSIONAL_RESTRAINT) or "Fully Restrained"
        )
        out[KEY_SD_WARPING_RESTRAINT] = str(
            inp.get(KEY_MP_GIRDER_WARPING_RESTRAINT) or "Both Flanges Restrained"
        )
        out[KEY_SD_WEB_TYPE] = str(
            inp.get(KEY_MP_GIRDER_WEB_TYPE) or "Thin Web with ITS"
        )
