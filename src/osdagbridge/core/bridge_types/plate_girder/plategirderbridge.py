from __future__ import annotations
import sqlite3
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
    DEFAULTS_DICT,
    DEFAULT_SPAN_M,
    DEFAULT_CARRIAGEWAY_WIDTH_M,
    DEFAULT_NO_OF_GIRDERS,
    DEFAULT_GIRDER_SYMMETRY,
    DEFAULT_MEDIAN_WIDTH_M,
)
from .initial_sizing import BridgeConfigurationSolver, DEFAULT_FOOTPATH_WIDTH
from .analyser import BridgeGrillageModel
from .analysis_results import PlateGirderAnalysisResults
from .designer import run_design_check
from .plot_generator import (
    build_figure_sfd,
    build_figure_bmd,
    build_figure_bmd_contour,
    build_figure_deflection,
    build_figure_grillage,
    build_nodes_members,
    figure_to_bytes,
)

from osdagbridge.core.utils.common import (
    KEY_STRUCTURE_TYPE,
    KEY_PROJECT_LOCATION,
    KEY_SPAN,
    KEY_CARRIAGEWAY_WIDTH,
    KEY_INCLUDE_MEDIAN,
    KEY_FOOTPATH,
    KEY_FOOTPATH_WIDTH,
    KEY_RAILING_WIDTH,
    KEY_SKEW_ANGLE,
    KEY_DESIGN_MODE,
    KEY_GIRDER,
    KEY_CROSS_BRACING,
    KEY_END_DIAPHRAGM,
    KEY_DECK_CONCRETE_GRADE_BASIC,
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
    STIFFENER_DETAILS_DEFAULTS,
    VALUES_TORSIONAL_RESTRAINT,
    VALUES_WARPING_RESTRAINT,
    VALUES_WEB_TYPE,
)
from osdagbridge.core.bridge_types.plate_girder.initial_sizing import (
    DEFAULT_DECK_THICKNESS as _DEFAULT_DECK_THICKNESS_MM,
)
from osdagbridge.core.bridge_types.plate_girder.defaults import (
    DEFAULT_AI_WEARING_THICKNESS_MM as _DEFAULT_WC_THICKNESS_MM,
    DEFAULT_AI_WEARING_DENSITY_KN_PER_M3 as _DEFAULT_WC_DENSITY_KN_M3,
)
from osdagbridge.core.bridge_components.super_structure.deck.geometry import (
    deck_thickness_from_inputs,
    wearing_course_params_from_inputs,
)
from osdagbridge.core.bridge_components.super_structure.crash_barrier.geometry import (
    crash_barrier_load_from_inputs,
)
from osdagbridge.core.bridge_components.super_structure.railing.geometry import (
    railing_load_from_inputs,
)

# Default median width (m) used when user enables median but no additional-input
# width has been supplied yet.
_DEFAULT_MEDIAN_WIDTH_M = 1.2

_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "ResourceFiles" / "Intg_osdag.sqlite"

# Steel constants (same values used in analyser.py __main__)
_STEEL_E0       = 200 * GPa    # Initial elastic modulus (Pa)
_STEEL_B        = 0.01         # Strain-hardening ratio
_STEEL_FY_DEFAULT = 250 * MPa  # Fallback Fy if material not found in DB (Pa)


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
    })

    def __init__(self) -> None:
        self.input_dict: dict = {}
        self.basic_inputs: dict = {}
        self.additional_inputs: dict = {}
        self._frontend = FrontendData()

        # Results populated by design()
        self.sizing_result = None
        self.section_props: dict = {}
        self.grillage_geometry: GrillageGeometry | None = None
        self.deck_layout: DeckLayoutProperties | None = None

        # Analyser — populated by setup_grillage()
        self.grillage_model: BridgeGrillageModel = BridgeGrillageModel()

        # Cached design-check capacity (populated in _run_dcr_checks)
        self._design_capacity = None

    def input_values(self) -> list:
        """Return UI field definitions for the InputDock (delegated to FrontendData)."""
        return self._frontend.input_values()
    
    def output_values(self) -> list:
        """Return UI field definitions for the OutputDock (delegated to FrontendData)."""
        return self._frontend.output_values()

    def get_output_state(self) -> dict:
        return self._frontend.get_output_state()

    def set_input(self, input_dict: dict) -> None:
        """
        Receive and store the input dictionary from the UI.

        Stores the full dict in ``self.input_dict`` and splits it into:
        - ``self.basic_inputs``  — keys from the main input dock
        - ``self.additional_inputs`` — all remaining keys (additional-input dialog, etc.)

        Parameters
        ----------
        input_dict : dict
            The flat dictionary built and maintained by ``CustomWindow``.
        """
        self.input_dict = dict(input_dict)
        self.basic_inputs = {
            k: v for k, v in self.input_dict.items()
            if k in self._BASIC_INPUT_KEYS
        }
        self.additional_inputs = {
            k: v for k, v in self.input_dict.items()
            if k not in self._BASIC_INPUT_KEYS
        }

        # Any fresh input invalidates the previous design outputs until the
        # design pipeline is run again.
        self._frontend.design_status = False
        self._frontend.design_button_status = False

        from pprint import pprint
        pprint(input_dict)

    # ─────────────────────────────────────────────────────────────────────────
    # Design pipeline
    # ─────────────────────────────────────────────────────────────────────────

    def design(self) -> None:
        """
        Run the full initial-sizing pipeline in order:
          1. Parse basic inputs
          2. Solve bridge layout
          3. Build result DTOs
          4. Set up grillage model geometry and sections
          5. Apply dead loads
          6. Apply live loads
        """
        parsed = self._parse_basic_inputs()
        self._solve_bridge_layout(parsed)
        self._build_dtos(parsed)
        self.setup_grillage()
        self.add_dead_loads()
        self.add_live_loads()
        self.add_wind_loads()
        dataset = self.analyze()
        dataset = self.create_governing_ll_load_case(dataset, partial_safety_factor=1.0)

        sp = self.section_props
        sr = self.sizing_result
        print(
            f"\n{'-'*60}\n"
            f"  PLATE GIRDER BRIDGE - DESIGN SUMMARY\n"
            f"{'-'*60}\n"
            f"  Span                  : {parsed['span']:.1f} m\n"
            f"  Overall width         : {sr.overall_width:.3f} m\n"
            f"  No. of girders        : {sr.no_of_girders}\n"
            f"  Girder spacing        : {sr.girder_spacing * 1e3:.1f} mm\n"
            f"  Deck overhang         : {sr.deck_overhang * 1e3:.1f} mm\n"
            f"{'-'*60}\n"
            f"  GIRDER CROSS-SECTION (all dimensions in mm)\n"
            f"{'-'*60}\n"
            f"  Total depth      D    : {sp['D']     * 1e3:.1f}\n"
            f"  Web depth        d_w  : {sp['d_web'] * 1e3:.1f}\n"
            f"  Web thickness    t_w  : {sp['t_w']   * 1e3:.1f}\n"
            f"  Top flange width B_ft : {sp['B_top']   * 1e3:.1f}\n"
            f"  Top flange thk   T_ft : {sp['t_f_top'] * 1e3:.1f}\n"
            f"  Bot flange width B_fb : {sp.get('B_bot',   sp['B_top'])   * 1e3:.1f}\n"
            f"  Bot flange thk   T_fb : {sp.get('t_f_bot', sp['t_f_top']) * 1e3:.1f}\n"
            f"{'-'*60}\n"
            f"  SECTION PROPERTIES (SI units)\n"
            f"{'-'*60}\n"
            f"  Area   A  : {sp['Area']:.6f} m^2\n"
            f"  I_z       : {sp['I_z']:.6f} m^4\n"
            f"  I_y       : {sp['I_y']:.6f} m^4\n"
            f"  I_t (J)   : {sp['I_t']:.6f} m^3\n"
            f"{'-'*60}\n"
        )

        self._run_dcr_checks(dataset)
        self._frontend.design_status = True
        self._frontend.design_button_status = True

    def _parse_basic_inputs(self) -> dict:
        """Extract and normalise scalar values from ``self.basic_inputs``."""
        span       = self._to_float(KEY_SPAN,             DEFAULT_SPAN_M)
        cw_width   = self._to_float(KEY_CARRIAGEWAY_WIDTH, DEFAULT_CARRIAGEWAY_WIDTH_M)
        skew_angle = self._to_float(KEY_SKEW_ANGLE,        0.0)

        include_median = str(self.basic_inputs.get(KEY_INCLUDE_MEDIAN, "No")).strip()
        footpath_str   = str(self.basic_inputs.get(KEY_FOOTPATH,       "None")).strip()
        design_mode    = str(self.basic_inputs.get(KEY_DESIGN_MODE,    "Optimized")).strip()

        if footpath_str in ("None", ""):
            n_footpaths    = 0
            footpath_width = 0.0
            railing_width  = 0.0
        elif "Both" in footpath_str:
            n_footpaths    = 2
            footpath_width = DEFAULT_FOOTPATH_WIDTH
            railing_width  = DEFAULT_RAILING_WIDTH
        else:                                        # Single Side
            n_footpaths    = 1
            footpath_width = DEFAULT_FOOTPATH_WIDTH
            railing_width  = DEFAULT_RAILING_WIDTH

        median_width = (
            _DEFAULT_MEDIAN_WIDTH_M if include_median.lower() == "yes" else 0.0
        )

        return dict(
            span=span,
            cw_width=cw_width,
            skew_angle=skew_angle,
            design_mode=design_mode,
            n_footpaths=n_footpaths,
            footpath_width=footpath_width,
            railing_width=railing_width,
            median_width=median_width,
        )

    def _solve_bridge_layout(self, parsed: dict) -> None:
        """Run BridgeConfigurationSolver and store sizing + section results."""
        solver = BridgeConfigurationSolver(
            carriageway_width=parsed["cw_width"],
            crash_barrier_width=DEFAULT_CRASH_BARRIER_WIDTH,
            footpath_width=parsed["footpath_width"],
            railing_width=parsed["railing_width"],
            median_width=parsed["median_width"],
            n_footpaths=parsed["n_footpaths"],
        )

        sizing_result = solver._solve_layout(
            no_of_girders=DEFAULT_NO_OF_GIRDERS,
            changed_field="girders",
        )

        # Debug print for sizing result
        print("[DEBUG] Bridge Layout Sizing Result:")
        print(f"  overall_width = {sizing_result.overall_width} m")
        print(f"  no_of_girders = {sizing_result.no_of_girders}")
        print(f"  girder_spacing = {sizing_result.girder_spacing} m")
        print(f"  deck_overhang = {sizing_result.deck_overhang} m")

        symmetry = (
            DEFAULT_GIRDER_SYMMETRY
            if parsed["design_mode"] == "Optimized"
            else "Girder Unsymmetric"
        )
        section_props = solver.compute_section_properties(
            span=parsed["span"],
            symmetry=symmetry,
        )

        self.sizing_result = sizing_result
        self.section_props = section_props

    def _build_dtos(self, parsed: dict) -> None:
        """Construct GrillageGeometry and DeckLayoutProperties DTOs from solved results."""
        span = parsed["span"]
        # n_t: transverse grid lines — span divided by cross-bracing spacing, rounded to nearest odd integer with minimum of 3 (1 at each end + at least 1 internal for bracing)
        n_t = max(3, (int(round(span / (DEFAULT_CROSS_BRACING_SPACING)*2) + 1)))

        deck_overhang = self.sizing_result.deck_overhang
        # When there is an overhang, the two edge beams add 2 extra longitudinal
        # grid lines on top of the structural girder count.
        n_l = self.sizing_result.no_of_girders + (2 if deck_overhang > 0 else 0)

        self.grillage_geometry = GrillageGeometry(
            L=span,
            n_l=n_l,
            n_t=n_t,
            edge_dist=deck_overhang,
            ext_to_int_dist=self.sizing_result.girder_spacing,
            angle=parsed["skew_angle"],
        )

        self.deck_layout = DeckLayoutProperties(
            carriageway_width=parsed["cw_width"],
            crash_barrier_width=DEFAULT_CRASH_BARRIER_WIDTH,
            footpath_width=parsed["footpath_width"],
            railing_width=parsed["railing_width"],
            median_width=parsed["median_width"],
            n_footpaths=parsed["n_footpaths"],
        )

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
        self.grillage_model.create_sections(
            longitudinal=self._girder_section(),
            edge_longitudinal=self._girder_section(),
            transverse=self._transverse_section(),
            end_transverse=self._end_transverse_section(),
        )
        self.grillage_model.create_material(self._build_material_props())
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
        
        # Choose the table: steel or concrete
        table = 'Steel_Grade_Properties' if material_name[0] == 'E' else 'Concrete_Grade_Properties'

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
                elif property in ("fck", "fctm", "Ecm"):  # Concrete properties (MPa or GPa depending on property)
                    return float(row[0])
                else:
                    raise SyntaxError(f"Unknown property '{property}' requested in table '{table}' in PlateGirderBridge._lookup_material")

        except sqlite3.Error:
            raise LookupError(f"Error querying material database in PlateGirderBridge._lookup_material: {sqlite3.Error}")

    def _build_material_props(self) -> MaterialProperties:
        """Build a MaterialProperties from the selected girder material in basic_inputs."""
        
        # Collecting Steel Grade Properties
        steel_grade = str(self.basic_inputs.get(KEY_GIRDER)).strip()
        e = self._lookup_material(steel_grade, "Modulus of Elasticity")
        v = self._lookup_material(steel_grade, "Poisson's Ratio")
        rho = self._lookup_material(steel_grade, "Density")
        fy = self._lookup_material(steel_grade, "Yield Strength")
        fu = self._lookup_material(steel_grade, "Ultimate Tensile Strength")
        # print(f"grade: {steel_grade}, e: {e}, v: {v}, rho: {rho}, fy: {fy}, fu: {fu}")
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
        
        # Collecting Deck Concrete Properties
        concrete_grade = str(self.basic_inputs.get(KEY_DECK_CONCRETE_GRADE_BASIC)).strip()
        fck = self._lookup_material(concrete_grade, "fck")
        fctm = self._lookup_material(concrete_grade, "fctm")
        Ecm = self._lookup_material(concrete_grade, "Ecm")
        # print(f"grade: {concrete_grade}, fck: {fck}, fctm: {fctm}, Ecm: {Ecm}")
        concrete_prop = ConcreteProperties(
                        grade=concrete_grade,
                        fck=fck,
                        fctm=fctm,
                        Ecm=Ecm,
                    )
        
        # Return Material Properties DTO
        return MaterialProperties(
                        steel_prop=steel_prop,
                        concrete_prop=concrete_prop
                    )

    def _girder_section(self) -> SectionProperties:
        """Build a SectionProperties for the main/edge longitudinal girder from section_props."""
        sp = self.section_props
        Az = sp["d_web"] * sp["t_w"]                       # web shear area (strong axis)
        Ay = 2 * sp["B_top"] * sp["t_f_top"]               # flange shear area (weak axis)
        return SectionProperties(
            A=sp["Area"],
            J=sp["I_t"],
            Iz=sp["I_z"],
            Iy=sp["I_y"],
            Az=Az,
            Ay=Ay,
        )

    def _transverse_section(self) -> SectionProperties:
        """Build a SectionProperties for the transverse deck slab (half-depth, unit width)."""
        sp = self.section_props
        t = sp["D"] / 2                                     # approximate slab thickness
        Az = t * sp["t_w"]
        Ay = t * sp["t_w"]
        return SectionProperties(
            A=sp["Area"] / 2,
            J=sp["I_t"] / 2,
            Iz=sp["I_z"] / 2,
            Iy=sp["I_y"] / 2,
            Az=Az,
            Ay=Ay,
        )

    def _end_transverse_section(self) -> SectionProperties:
        """Build a SectionProperties for the end transverse slab (quarter-depth)."""
        sp = self.section_props
        Az = sp["d_web"] / 2 * sp["t_w"]
        Ay = sp["B_top"] * sp["t_f_top"]
        return SectionProperties(
            A=sp["Area"] / 4,
            J=sp["I_t"] / 4,
            Iz=sp["I_z"] / 4,
            Iy=sp["I_y"] / 4,
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
        deck_t_m = deck_thickness_from_inputs(self.additional_inputs, _DEFAULT_DECK_THICKNESS_MM)
        wc_t_m, wc_rho = wearing_course_params_from_inputs(
            self.additional_inputs, _DEFAULT_WC_THICKNESS_MM, _DEFAULT_WC_DENSITY_KN_M3
        )
        barrier_load_kN_m = crash_barrier_load_from_inputs(self.additional_inputs)
        railing_load_kN_m = railing_load_from_inputs(self.additional_inputs)

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

        Must be called after setup_grillage() has built and registered the model.
        """
        model = self.grillage_model
        model.add_vehicle_load_cases_from_combinations()
        model.create_moving_vehicle_load_cases()

    # ─────────────────────────────────────────────────────────────────────────
    # Wind loads — applied after dead and live loads, before analysis
    # ─────────────────────────────────────────────────────────────────────────

    def add_wind_loads(self) -> None:
        """
        Apply wind loads to the grillage model per IRC:6-2017 Cl.209.3.3–209.3.5.

        Wind parameters are read from ``self.additional_inputs`` (the
        Additional Inputs dialog).  Any parameter not yet supplied falls back
        to a sensible default so the method is always safe to call.

        Load cases created (delegated to BridgeGrillageModel.create_wind_load):
          - ``"WL Transverse"``   — FT line load on the two exterior girders
          - ``"WL Longitudinal"`` — FL = 0.25 FT patch load over the full deck
          - ``"WL Uplift"``       — Pz × G × CL patch load (upward) on the deck
          - ``"1.0 WL"``          — combined load case with partial_safety_factor = 1.0
        """
        ai = self.additional_inputs
        sp = self.section_props
        sr = self.sizing_result

        # ── Wind speed / terrain ─────────────────────────────────────────
        basic_wind_speed = float(ai.get("basic_wind_speed") or 33.0)
        height_for_pz    = float(ai.get("avg_exposed_height") or 10.0)
        terrain_raw      = str(ai.get("terrain_type") or "Plain Terrain")
        terrain          = "plain" if "plain" in terrain_raw.lower() else "obstructed"

        # ── Exposed height components ────────────────────────────────────
        railing_height       = float(ai.get("railing_height")       or 0.0)
        crash_barrier_height = float(ai.get("crash_barrier_height") or 0.0)
        deck_t_m             = deck_thickness_from_inputs(ai, _DEFAULT_DECK_THICKNESS_MM)

        # ── Girder geometry for CD ───────────────────────────────────────
        d_depth   = sp.get("D",              1.5)             if sp else 1.5
        c_spacing = sr.girder_spacing                         if sr else DEFAULT_GIRDER_SPACING
        n_girders = sr.no_of_girders                          if sr else None

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
        return self.grillage_model.analyze()

    def create_governing_ll_load_case(self, dataset, partial_safety_factor: float = 1.0):
        """
        Identify the governing static vehicle load case, create a
        ``"{partial_safety_factor} LL"`` load case from it, and re-analyze.

        Must be called after analyze().

        Parameters
        ----------
        dataset : xarray.Dataset
            Results from the initial analysis.
        partial_safety_factor : float
            ULS partial safety factor for the governing LL case (default 1.0).

        Returns
        -------
        xarray.Dataset
            Updated dataset including the LL load case.
        """
        return self.grillage_model.create_governing_ll_load_case(
            dataset=dataset,
            partial_safety_factor=partial_safety_factor,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # DCR checks
    # ─────────────────────────────────────────────────────────────────────────

    def _run_dcr_checks(self, dataset) -> None:
        """Run structural capacity checks and push DCR percentages to the output dock."""
        results = PlateGirderAnalysisResults(dataset=dataset, bridge=self.grillage_model)
        _, engine = run_design_check(
            plate_girder_bridge=self,
            analysis_results=results,
            print_report=True,
        )
        self._design_capacity = getattr(engine, "capacity", None)

        dcr_by_id: dict[int, float] = {}
        for c in engine.checks:
            dcr_by_id[c.check_id] = max(dcr_by_id.get(c.check_id, 0.0), c.dcr)
        self._frontend.set_output_value(KEY_UTIL_FLEXURE,          dcr_by_id.get(1,  0.0) * 100)
        self._frontend.set_output_value(KEY_UTIL_SHEAR,            dcr_by_id.get(2,  0.0) * 100)
        self._frontend.set_output_value(KEY_UTIL_INTERACTION,      dcr_by_id.get(3,  0.0) * 100)
        self._frontend.set_output_value(KEY_UTIL_LTB,              dcr_by_id.get(5,  0.0) * 100)
        defl_dcr = max(dcr_by_id.get(13, 0.0), dcr_by_id.get(14, 0.0), dcr_by_id.get(15, 0.0))
        self._frontend.set_output_value(KEY_UTIL_DEFLECTION_CRACK,  defl_dcr * 100)
        fatigue_dcr = max(dcr_by_id.get(8, 0.0), dcr_by_id.get(9, 0.0))
        self._frontend.set_output_value(KEY_UTIL_FATIGUE,           fatigue_dcr * 100)
        trans_shear_dcr = max(dcr_by_id.get(16, 0.0), dcr_by_id.get(17, 0.0))
        self._frontend.set_output_value(KEY_UTIL_LONG_TRANS_SHEAR,  trans_shear_dcr * 100)
        stress_dcr = max(dcr_by_id.get(10, 0.0), dcr_by_id.get(11, 0.0), dcr_by_id.get(12, 0.0))
        self._frontend.set_output_value(KEY_UTIL_STRESS_LIMITATION, stress_dcr * 100)

    # ─────────────────────────────────────────────────────────────────────────
    # Plotting
    # ─────────────────────────────────────────────────────────────────────────

    def get_results_dataset(self):
        """Return the xarray Dataset of analysis results.

        After create_governing_ll_load_case() runs a second analysis pass, the
        raw model.get_results() contains duplicate Loadcase entries.  The
        deduplicated copy is cached on the grillage model and returned here so
        that all downstream consumers (plot widgets, result handlers) always
        see a clean, uniquely-indexed dataset.
        """
        if self.grillage_model.model is None:
            return None
        cached = getattr(self.grillage_model, '_deduplicated_results', None)
        if cached is not None:
            return cached
        return self.grillage_model.model.get_results()

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

    def get_3d_cad_parameters(self) -> BridgeParametersDTO:
        """
        Build a BridgeParametersDTO for 3D CAD rendering.

        Values sourced from:
        - section_props / sizing_result — girder geometry (populated after design())
        - basic_inputs  — span, carriageway width, footpath, median, skew angle
        - additional_inputs — deck thickness
        Fields not yet exposed through additional inputs default to sensible values.

        Must be called after design() has fully run.
        """
        sp = self.section_props
        sr = self.sizing_result

        # section_props are in SI metres; BridgeParametersDTO expects mm
        D       = sp["D"]       * 1e3
        tw      = sp["t_w"]     * 1e3
        B_top   = sp["B_top"]   * 1e3
        t_f_top = sp["t_f_top"] * 1e3
        B_bot   = sp.get("B_bot",   sp["B_top"])   * 1e3   # fallback: symmetric
        t_f_bot = sp.get("t_f_bot", sp["t_f_top"]) * 1e3   # fallback: symmetric

        span_mm = self._to_float(KEY_SPAN,             DEFAULT_SPAN_M) * 1e3
        cw_each_way_m = self._to_float(KEY_CARRIAGEWAY_WIDTH, DEFAULT_CARRIAGEWAY_WIDTH_M)
        skew = self._to_float(KEY_SKEW_ANGLE, 0.0)

        footpath_str   = str(self.basic_inputs.get(KEY_FOOTPATH,       "None")).strip()
        include_median = str(self.basic_inputs.get(KEY_INCLUDE_MEDIAN, "No")).strip().lower() == "yes"

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

        deck_t_mm = deck_thickness_from_inputs(self.additional_inputs, _DEFAULT_DECK_THICKNESS_MM) * 1e3
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

        steel_grade = str(self.basic_inputs.get(KEY_GIRDER, "E 250A")).strip()
        concrete_grade = str(self.basic_inputs.get(KEY_DECK_CONCRETE_GRADE_BASIC, "M30")).strip()

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
            num_girders=sr.no_of_girders,
            girder_spacing=sr.girder_spacing * 1e3,
            # --- Geometry ---
            skew_angle=skew,
            # --- Deck ---
            carriageway_width=cw_mm,
            deck_thickness=deck_t_mm,
            footpath_config=footpath_config,
            footpath_width=footpath_width_mm,
            railing_width=railing_width_mm,
            # --- Crash barrier (defaults until additional inputs wired) ---
            barrier_type="Rigid",
            crash_barrier_subtype="IRC-5R",
            # --- Median ---
            enable_median=include_median,
            median_type="Metallic Crash Barrier",
            # --- Railing (defaults) ---
            rail_count=3,
            railing_type="rcc",
            # --- Intermediate stiffeners (defaults) ---
            include_intermediate_stiffeners=True,
            intermediate_stiffener_spacing=cross_bracing_mm / 2,
            intermediate_stiffener_thickness=20.0,
            intermediate_stiffener_outstand=None,
            # --- End stiffeners (defaults) ---
            num_end_stiffener_pairs=4,
            end_stiffener_thickness=30.0,
            end_stiffener_outstand=None,
            # --- Longitudinal stiffeners (defaults) ---
            include_longitudinal_stiffeners=False,
            num_longitudinal_stiffeners=0,
            longitudinal_stiffener_thickness=20.0,
            longitudinal_stiffener_outstand=None,
            # --- Cross bracing ---
            cross_bracing_spacing=cross_bracing_mm,
            bracing_type="X",
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
            # --- Shear studs (defaults) ---
            shear_stud_params=ShearStudParamsDTO(
                base_diameter=50,
                top_diameter=70,
                base_height=100,
                top_height=20,
                num_per_section=3,
                transverse_spacing=305,
                pitch=500,
            ),
            # --- Girder segments (single uniform segment) ---
            girder_segments=[girder_segment],
            girder_segments_dict={},
        )

    def get_ifc_export_parameters(self, additional_inputs: dict | None = None) -> BridgeParametersDTO:
        """
        Build a BridgeParametersDTO for IFC export.

        Identical to get_3d_cad_parameters() but overrides crash-barrier,
        median, railing, footpath-width and railing-width fields from the
        supplied additional_inputs dict (values from the Additional Inputs
        dialog that are not part of the basic input set).

        Must be called after design() has fully run.
        """
        params = self.get_3d_cad_parameters()
        ai = additional_inputs or {}

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
        if KEY_FOOTPATH_WIDTH in ai:
            params.footpath_width = float(ai[KEY_FOOTPATH_WIDTH]) * 1000
        if KEY_RAILING_WIDTH in ai:
            params.railing_width = float(ai[KEY_RAILING_WIDTH]) * 1000

        return params

    def get_steel_design_state(self) -> dict:
        """Build a flat dict of values for the Steel Design dialog details tab."""
        state: dict[str, object] = {}

        sp = getattr(self, "section_props", {}) or {}
        sr = getattr(self, "sizing_result", None)
        add_inputs = getattr(self, "additional_inputs", {}) or {}
        capacity = getattr(self, "_design_capacity", None)

        # Get girder and stiffener details from additional inputs
        girder_details = add_inputs.get("girder_details", {})
        stiffener_details = add_inputs.get("stiffener_details", {})

        member_id = str(
            girder_details.get("member_id")
            or girder_details.get("selected_girder")
            or "G1M1"
        ).strip()
        state["member_id"] = member_id

        state["grade_of_material"] = str(self.basic_inputs.get(KEY_GIRDER, "")).strip()
        state["span_m"] = self.basic_inputs.get(KEY_SPAN)

        section_type = str(
            girder_details.get("girder_type")
            or girder_details.get("section_type")
            or "Welded"
        ).strip()
        state["section_type"] = section_type

        section_designation = str(
            girder_details.get("rolled_section")
            or girder_details.get("section_designation")
            or ""
        ).strip()
        if not section_designation:
            section_designation = "Built-up Plate Girder" if section_type.lower() == "welded" else section_type
        state["section_designation"] = section_designation

        def _fmt_mm(value: object) -> str:
            try:
                return f"{float(value) * 1e3:.3f}".rstrip("0").rstrip(".")
            except (TypeError, ValueError):
                return ""

        def _fmt_num(value: object, decimals: int = 3) -> str:
            try:
                return f"{float(value):.{decimals}f}".rstrip("0").rstrip(".")
            except (TypeError, ValueError):
                return ""

        # Try to get dimensions from girder_details (user input) first, fallback to section_props (designed values)
        # Note: welded_inputs values are already in mm (keys have _mm suffix), so use them directly
        if girder_details:
            # Extract welded_inputs which contains the actual user-entered dimensions
            welded_inputs = girder_details.get("welded_inputs", {})
            if welded_inputs:
                # welded_inputs values are already in mm, format them consistently
                def _fmt_welded_mm(value: object) -> str:
                    """Format welded input values that are already in mm."""
                    try:
                        return f"{float(value):.3f}".rstrip("0").rstrip(".")
                    except (TypeError, ValueError):
                        return ""
                
                # Only set non-empty values from welded_inputs (already in mm)
                total_depth_val = welded_inputs.get("total_depth_mm")
                if total_depth_val:
                    state["total_depth"] = _fmt_welded_mm(total_depth_val)
                
                web_thickness_val = welded_inputs.get("web_thickness_value_mm")
                if web_thickness_val:
                    state["web_thickness"] = _fmt_welded_mm(web_thickness_val)
                
                top_width_val = welded_inputs.get("top_flange_width_mm")
                if top_width_val:
                    state["top_flange_width"] = _fmt_welded_mm(top_width_val)
                
                top_thickness_val = welded_inputs.get("top_thickness_value_mm")
                if top_thickness_val:
                    state["top_flange_thickness"] = _fmt_welded_mm(top_thickness_val)
                
                bottom_width_val = welded_inputs.get("bottom_flange_width_mm")
                if bottom_width_val:
                    state["bottom_flange_width"] = _fmt_welded_mm(bottom_width_val)
                
                bottom_thickness_val = welded_inputs.get("bottom_thickness_value_mm")
                if bottom_thickness_val:
                    state["bottom_flange_thickness"] = _fmt_welded_mm(bottom_thickness_val)

                # If only top flange values are provided, mirror them for bottom flange.
                if "top_flange_width" in state and "bottom_flange_width" not in state:
                    state["bottom_flange_width"] = state["top_flange_width"]
                if "top_flange_thickness" in state and "bottom_flange_thickness" not in state:
                    state["bottom_flange_thickness"] = state["top_flange_thickness"]
        
        # Always populate from section_props if not already set (ensures values are always available)
        # section_props values are in meters, so convert to mm
        if sp:
            state.setdefault("total_depth", _fmt_mm(sp.get("D")))
            state.setdefault("web_thickness", _fmt_mm(sp.get("t_w")))
            state.setdefault("top_flange_width", _fmt_mm(sp.get("B_top")))
            state.setdefault("top_flange_thickness", _fmt_mm(sp.get("t_f_top")))
            state.setdefault("bottom_flange_width", _fmt_mm(sp.get("B_bot", sp.get("B_top"))))
            state.setdefault("bottom_flange_thickness", _fmt_mm(sp.get("t_f_bot", sp.get("t_f_top"))))

        def _fmt_cm(value: object, factor: float) -> str:
            try:
                return f"{float(value) * factor:.3f}".rstrip("0").rstrip(".")
            except (TypeError, ValueError):
                return ""

        if sp:
            state.setdefault("mass", _fmt_num(sp.get("Mass"), 3))
            state.setdefault("area", _fmt_cm(sp.get("Area"), 1e4))
            state.setdefault("iz", _fmt_cm(sp.get("I_z"), 1e8))
            state.setdefault("iv", _fmt_cm(sp.get("I_y"), 1e8))
            state.setdefault("rz", _fmt_cm(sp.get("r_z"), 100.0))
            state.setdefault("rv", _fmt_cm(sp.get("r_y"), 100.0))
            state.setdefault("zz", _fmt_cm(sp.get("Z_ez"), 1e6))
            state.setdefault("zv", _fmt_cm(sp.get("Z_ey"), 1e6))
            state.setdefault("zuz", _fmt_cm(sp.get("Z_pz"), 1e6))
            state.setdefault("zuv", _fmt_cm(sp.get("Z_py"), 1e6))
            state.setdefault("it", _fmt_cm(sp.get("I_t"), 1e8))
            state.setdefault("iw", _fmt_cm(sp.get("I_w"), 1e12))

        if sr is not None and getattr(sr, "no_of_girders", None) is not None:
            state["no_of_girders"] = int(sr.no_of_girders)

        # Read restraint and web type from girder_details (user input) first, fallback to add_inputs
        torsional_restraint = girder_details.get("torsional_restraint") or add_inputs.get("torsional_restraint")
        warping_restraint = girder_details.get("warping_restraint") or add_inputs.get("warping_restraint")
        web_type = girder_details.get("web_type") or add_inputs.get("web_type")
        state["torsional_restraint"] = (
            torsional_restraint
            or (VALUES_TORSIONAL_RESTRAINT[0] if VALUES_TORSIONAL_RESTRAINT else "")
        )
        state["warping_restraint"] = (
            warping_restraint
            or (VALUES_WARPING_RESTRAINT[0] if VALUES_WARPING_RESTRAINT else "")
        )
        state["web_type"] = web_type or (VALUES_WEB_TYPE[0] if VALUES_WEB_TYPE else "")

        # Shear stud properties come from Design Options tab (add_inputs), not girder_details
        stud_fy = add_inputs.get("shear_stud_yield_strength", "385.00")
        stud_fu = add_inputs.get("shear_stud_ultimate_strength", "495.00")
        if stud_fy:
            state.setdefault("shear_material", f"Fy {stud_fy} MPa")
        elif stud_fu:
            state.setdefault("shear_material", f"Fu {stud_fu} MPa")

        state["shear_diameter"] = add_inputs.get("shear_stud_diameter", "20")
        state["shear_height"] = add_inputs.get("shear_stud_height", "100.00")
        state["shear_transverse_spacing"] = add_inputs.get("shear_stud_transverse_spacing", "100.00")
        state["shear_studs_per_section"] = add_inputs.get("shear_stud_count", "2")

        # Ensure girder_details is included in state for CAD preview
        state["girder_details"] = girder_details

        # Flatten stiffener details from nested structure.
        if not stiffener_details.get("stiffener_by_member"):
            default_member_id = member_id or "G1M1"
            default_stiffener = {
                "bearing_stiffeners_each_end": STIFFENER_DETAILS_DEFAULTS.get("bearing_stiffeners_each_end", "2"),
                "bearing_spacing_mm": STIFFENER_DETAILS_DEFAULTS.get("bearing_spacing_mm", ""),
                "bearing_thickness_mode": STIFFENER_DETAILS_DEFAULTS.get("bearing_thickness_mode", "All"),
                "bearing_thickness_value": STIFFENER_DETAILS_DEFAULTS.get("bearing_thickness_value", ""),
                "bearing_outstand_mm": STIFFENER_DETAILS_DEFAULTS.get("bearing_outstand_mm", ""),
                "intermediate_stiffener": STIFFENER_DETAILS_DEFAULTS.get("intermediate_stiffener", "No"),
                "intermediate_spacing_mm": STIFFENER_DETAILS_DEFAULTS.get("intermediate_spacing_mm", "NA"),
                "intermediate_thickness_mode": STIFFENER_DETAILS_DEFAULTS.get("intermediate_thickness_mode", "All"),
                "intermediate_thickness_value": STIFFENER_DETAILS_DEFAULTS.get("intermediate_thickness_value", ""),
                "intermediate_outstand_mm": STIFFENER_DETAILS_DEFAULTS.get("intermediate_outstand_mm", ""),
                "longitudinal_stiffener": STIFFENER_DETAILS_DEFAULTS.get("longitudinal_stiffener", "No"),
                "longitudinal_thickness_mode": STIFFENER_DETAILS_DEFAULTS.get("longitudinal_thickness_mode", "All"),
                "longitudinal_thickness_value": STIFFENER_DETAILS_DEFAULTS.get("longitudinal_thickness_value", ""),
                "shear_buckling_method": STIFFENER_DETAILS_DEFAULTS.get("shear_buckling_method", ""),
            }
            stiffener_details = {
                "active_member_id": default_member_id,
                "stiffener_by_member": {default_member_id: default_stiffener},
            }
            add_inputs = dict(add_inputs)
            add_inputs["stiffener_details"] = stiffener_details

        # Ensure stiffener_details is included in state for CAD preview
        state["stiffener_details"] = stiffener_details

        stiffener_by_member = stiffener_details.get("stiffener_by_member", {})
        selected_member_id = str(stiffener_details.get("active_member_id") or member_id or "").strip()
        member_data = stiffener_by_member.get(selected_member_id) if selected_member_id else None
        if not isinstance(member_data, dict):
            member_data = next(iter(stiffener_by_member.values()), {}) if stiffener_by_member else {}

        if isinstance(member_data, dict):
            for stiff_type in ("intermediate", "longitudinal", "bearing"):
                grade_value = member_data.get(f"{stiff_type}_grade", "") or state.get("grade_of_material", "")
                state.setdefault(f"stiff_{stiff_type}_grade", str(grade_value))

                thickness_value = member_data.get(f"{stiff_type}_thickness_value", "")
                if thickness_value in (None, ""):
                    thickness_value = member_data.get(f"{stiff_type}_thickness", "")
                state.setdefault(f"stiff_{stiff_type}_thickness", str(thickness_value))

                width_value = member_data.get(f"{stiff_type}_outstand_mm", "")
                state.setdefault(f"stiff_{stiff_type}_width", str(width_value))

                spacing_value = member_data.get("bearing_spacing_mm", "") if stiff_type == "bearing" else member_data.get(f"{stiff_type}_spacing_mm", "")
                state.setdefault(f"stiff_{stiff_type}_spacing", str(spacing_value))

        if capacity is not None:
            details = getattr(capacity, "details", {}) or {}
            sec_class = details.get("section_class", {}) or {}
            eff_width = details.get("effective_width", {}) or {}
            if sec_class:
                state.setdefault("section_class", sec_class.get("governing_class", ""))
            if eff_width:
                state.setdefault("effective_slab_width", eff_width.get("beff_mm", ""))

            spacing = getattr(capacity, "stud_spacing_provided_mm", 0.0) or 0.0
            if spacing <= 0:
                spacing = details.get("stud_spacing", {}).get("spacing_mm", 0.0) or 0.0
            if spacing > 0:
                state.setdefault("shear_longitudinal_spacing", _fmt_num(spacing, 1))

        return state

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

    def get_nodes_members(self) -> tuple[dict, dict]:
        """Return (nodes, members) dicts built from the active openseespy model."""
        return build_nodes_members()

    def get_edge_dist(self) -> float:
        """Return the deck overhang distance (0.0 when no overhang)."""
        if self.sizing_result is None:
            return 0.0
        return self.sizing_result.deck_overhang or 0.0

    def build_figure_sfd(self, ds, force_key: str):
        """Build and return a matplotlib Figure for the SFD of the given dataset slice."""
        nodes, members = self.get_nodes_members()
        return build_figure_sfd(ds, force_key, nodes, members, edge_dist=self.get_edge_dist())

    def build_figure_bmd(self, ds, force_key: str):
        """Build and return a matplotlib Figure for the BMD of the given dataset slice."""
        nodes, members = self.get_nodes_members()
        return build_figure_bmd(ds, force_key, nodes, members, edge_dist=self.get_edge_dist())

    def build_figure_bmd_contour(self, ds, force_key: str):
        """Build and return a matplotlib Figure for the BMD contour plot of the given dataset slice."""
        nodes, members = self.get_nodes_members()
        return build_figure_bmd_contour(ds, force_key, nodes, members, edge_dist=self.get_edge_dist())

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
    # Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _to_float(self, key: str, fallback: float) -> float:
        """Safely convert a basic_inputs value to float, falling back on error."""
        val = self.basic_inputs.get(key)
        if val is None or str(val).strip().lower() in ("", "none"):
            return fallback
        try:
            return float(val)
        except (TypeError, ValueError):
            return fallback
