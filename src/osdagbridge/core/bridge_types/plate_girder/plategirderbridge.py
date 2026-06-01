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
    KEY_TS_FOOTPATH_WIDTH,
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
    KEY_MD_WIDTH,
    KEY_RL_WIDTH,
    KEY_TS_DECK_OVERHANG,
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_OVERALL_WIDTH,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_TS_NO_OF_FOOTPATHS,
    KEY_WC_THICKNESS,
    KEY_WC_DENSITY,
    KEY_GIRDER_SYMMETRY, KEY_GIRDER_DEPTH, KEY_GIRDER_WEB_DEPTH, KEY_GIRDER_WEB_THICKNESS,
    KEY_GIRDER_TOP_FLANGE_WIDTH, KEY_GIRDER_TOP_FLANGE_THICKNESS,
    KEY_GIRDER_BOTTOM_FLANGE_WIDTH, KEY_GIRDER_BOTTOM_FLANGE_THICKNESS,
    KEY_GIRDER_SECTIONAL_AREA, KEY_GIRDER_MASS,
    KEY_GIRDER_SECTIONAL_IZ, KEY_GIRDER_SECTIONAL_IY,
    KEY_GIRDER_RADIUS_GYRATION_Z, KEY_GIRDER_RADIUS_GYRATION_Y,
    KEY_GIRDER_ELASTIC_MODULUS_ZZ, KEY_GIRDER_ELASTIC_MODULUS_ZY,
    KEY_GIRDER_PLASTIC_MODULUS_ZUZ, KEY_GIRDER_PLASTIC_MODULUS_ZUY,
    KEY_GIRDER_TORSION_CONSTANT_IT, KEY_GIRDER_WARPING_CONSTANT_IW,
    KEY_METALLIC_CRASH_BARRIER_TYPE,
    KEY_RIGID_CRASH_BARRIER_TYPE,
    KEY_CRASH_BARRIER_TYPE,
    KEY_CB_TYPE,
    KEY_RL_TYPE,
    KEY_RAILING_TYPE,
    KEY_MD_TYPE,
    KEY_MEDIAN_TYPE
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
        self.output_dict = dict(self.input_dict)   # mutable until end of design()
        self._build_dtos()
        self.setup_grillage()
        self.add_dead_loads()
        self.add_live_loads()
        self.add_wind_loads()
        self.add_temperature_load()
        self.add_seismic_load()
        dataset = self.analyze()
        dataset = self.create_governing_ll_load_case(dataset, partial_safety_factor=1.0)

        self.create_uls_combinations()
        self.create_sls_combinations()
        dataset = self._reanalyze_with_dedup()

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
            f"{'-'*60}\n"
            f"  GIRDER CROSS-SECTION (all dimensions in mm)\n"
            f"{'-'*60}\n"
            f"  Total depth      D    : {inp[KEY_GIRDER_DEPTH]                   * 1e3:.1f}\n"
            f"  Web depth        d_w  : {inp[KEY_GIRDER_WEB_DEPTH]               * 1e3:.1f}\n"
            f"  Web thickness    t_w  : {inp[KEY_GIRDER_WEB_THICKNESS]           * 1e3:.1f}\n"
            f"  Top flange width B_ft : {inp[KEY_GIRDER_TOP_FLANGE_WIDTH]        * 1e3:.1f}\n"
            f"  Top flange thk   T_ft : {inp[KEY_GIRDER_TOP_FLANGE_THICKNESS]    * 1e3:.1f}\n"
            f"  Bot flange width B_fb : {inp[KEY_GIRDER_BOTTOM_FLANGE_WIDTH]     * 1e3:.1f}\n"
            f"  Bot flange thk   T_fb : {inp[KEY_GIRDER_BOTTOM_FLANGE_THICKNESS] * 1e3:.1f}\n"
            f"{'-'*60}\n"
            f"  SECTION PROPERTIES (SI units)\n"
            f"{'-'*60}\n"
            f"  Area   A  : {inp[KEY_GIRDER_SECTIONAL_AREA]:.6f} m^2\n"
            f"  I_z       : {inp[KEY_GIRDER_SECTIONAL_IZ]:.6f} m^4\n"
            f"  I_y       : {inp[KEY_GIRDER_SECTIONAL_IY]:.6f} m^4\n"
            f"  I_t (J)   : {inp[KEY_GIRDER_TORSION_CONSTANT_IT]:.6f} m^3\n"
            f"{'-'*60}\n"
        )

        self._run_dcr_checks(dataset)
        self.result_data = self.grillage_model.get_result_data()

        self.crossbracing_design_results = self._design_cross_bracing_members()
        self.output_dict["crossbracing_design_results"] = self.crossbracing_design_results

        # Freeze output_dict — no further writes allowed after this point
        self.output_dict = types.MappingProxyType(self.output_dict)
        import pprint
        sep = "=" * 60
        print(f"\n{sep}\n  OUTPUT DICT (frozen) — {len(self.output_dict)} keys\n{sep}")
        for k, v in self.output_dict.items():
            if k == "crossbracing_design_results":
                print(f"  {k!r} :")
                pprint.pprint(v, indent=4, width=120)
            else:
                print(f"  {k!r:50s} : {v!r}")
        print(sep)

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
        """Build a SectionProperties for the main/edge longitudinal girder."""
        inp = self.input_dict
        Az = inp[KEY_GIRDER_WEB_DEPTH] * inp[KEY_GIRDER_WEB_THICKNESS]
        Ay = 2 * inp[KEY_GIRDER_TOP_FLANGE_WIDTH] * inp[KEY_GIRDER_TOP_FLANGE_THICKNESS]
        return SectionProperties(
            A=inp[KEY_GIRDER_SECTIONAL_AREA],
            J=inp[KEY_GIRDER_TORSION_CONSTANT_IT],
            Iz=inp[KEY_GIRDER_SECTIONAL_IZ],
            Iy=inp[KEY_GIRDER_SECTIONAL_IY],
            Az=Az,
            Ay=Ay,
        )

    def _transverse_section(self) -> SectionProperties:
        """Build a SectionProperties for the transverse deck slab (half-depth, unit width)."""
        inp = self.input_dict
        t  = inp[KEY_GIRDER_DEPTH] / 2
        Az = t * inp[KEY_GIRDER_WEB_THICKNESS]
        return SectionProperties(
            A=inp[KEY_GIRDER_SECTIONAL_AREA] / 2,
            J=inp[KEY_GIRDER_TORSION_CONSTANT_IT] / 2,
            Iz=inp[KEY_GIRDER_SECTIONAL_IZ] / 2,
            Iy=inp[KEY_GIRDER_SECTIONAL_IY] / 2,
            Az=Az,
            Ay=Az,
        )

    def _end_transverse_section(self) -> SectionProperties:
        """Build a SectionProperties for the end transverse slab (quarter-depth)."""
        inp = self.input_dict
        Az = inp[KEY_GIRDER_WEB_DEPTH] / 2 * inp[KEY_GIRDER_WEB_THICKNESS]
        Ay = inp[KEY_GIRDER_TOP_FLANGE_WIDTH] * inp[KEY_GIRDER_TOP_FLANGE_THICKNESS]
        return SectionProperties(
            A=inp[KEY_GIRDER_SECTIONAL_AREA] / 4,
            J=inp[KEY_GIRDER_TORSION_CONSTANT_IT] / 4,
            Iz=inp[KEY_GIRDER_SECTIONAL_IZ] / 4,
            Iy=inp[KEY_GIRDER_SECTIONAL_IY] / 4,
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
        wc_t_m = float(self.input_dict[KEY_WC_THICKNESS]) / 1000.0
        wc_rho  = float(self.input_dict[KEY_WC_DENSITY])
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
        ai  = self.additional_inputs
        inp = self.input_dict

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
        d_depth   = inp[KEY_GIRDER_DEPTH]
        c_spacing = inp[KEY_TS_GIRDER_SPACING]
        n_girders = inp[KEY_TS_NO_OF_GIRDERS]

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
        tl_raw = self.additional_inputs.get("temperature_load_kN_m2")
        if not tl_raw:
            return
        tl_kN_m2 = float(tl_raw)
        if tl_kN_m2 == 0.0:
            return
        self.grillage_model.create_temperature_load(
            temperature_load_kN_m2=tl_kN_m2,
            partial_safety_factor=1.0,
        )

    def add_seismic_load(self) -> None:
        """
        Apply seismic (earthquake) load to the grillage model as a patch load
        over the full deck footprint per IRC:6-2017 Cl.219 / IS 1893 (Part 3).

        The load intensity is read from ``self.additional_inputs`` using the key
        ``"seismic_load_kN_m2"``.  If the key is absent or zero the load is
        silently skipped (seismic load is optional).

        Delegates to BridgeGrillageModel.create_seismic_load().
        """
        el_raw = self.additional_inputs.get("seismic_load_kN_m2")
        if not el_raw:
            return
        el_kN_m2 = float(el_raw)
        if el_kN_m2 == 0.0:
            return
        self.grillage_model.create_seismic_load(
            seismic_load_kN_m2=el_kN_m2,
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

    def _reanalyze_with_dedup(self):
        """
        Re-run the OpenSees analysis, deduplicate the Loadcase axis (ospgrillage
        appends results on every analyze() call), cache the clean dataset on the
        grillage model, and return it.

        Called by design() after load combinations have been registered so that
        combination results are included in the final results dataset.
        """
        m = self.grillage_model.model
        m.analyze()
        ds = m.get_results()

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

    # ─────────────────────────────────────────────────────────────────────────
    # Load combinations
    # ─────────────────────────────────────────────────────────────────────────

    def create_uls_combinations(self) -> list:
        """
        Create all ULS load combinations per IRC:6-2017 Table B.2.

        Produces 16 combinations:
          BASIC_1 … BASIC_6        — 2 permanent directions × 3 variable leaders
          ACCIDENTAL_1 … ACCIDENTAL_6 — 2 directions × 3 events × 1 valid leader
          SEISMIC_1 … SEISMIC_4    — 2 directions × 2 seismic conditions

        Must be called after create_governing_ll_load_case() so that the LL
        load case (``ll_load_case``) is available for combination.

        Delegates to BridgeGrillageModel.create_uls_combinations().

        Returns
        -------
        list — ospgrillage load-case objects registered with the model.
        """
        return self.grillage_model.create_uls_combinations()

    def create_sls_combinations(self) -> list:
        """
        Create all SLS load combinations per IRC:6-2017 Table B.3.

        Produces 14 combinations:
          SLS_RARE_1 … SLS_RARE_6          — 2 surfacing directions × 3 variable leaders
          SLS_FREQUENT_1 … SLS_FREQUENT_6  — same structure, frequent-column factors
          SLS_QP_1, SLS_QP_2               — quasi-permanent; only TL (0.5) contributes

        Must be called after create_governing_ll_load_case() so that the LL
        load case is available for combination.

        Delegates to BridgeGrillageModel.create_sls_combinations().

        Returns
        -------
        list — ospgrillage load-case objects registered with the model.
        """
        return self.grillage_model.create_sls_combinations()

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
        self.design_results = design_results

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

        self.output_dict[KEY_UTIL_FLEXURE]           = dcr_by_id.get(1,  0.0) * 100
        self.output_dict[KEY_UTIL_SHEAR]             = dcr_by_id.get(2,  0.0) * 100
        self.output_dict[KEY_UTIL_INTERACTION]       = dcr_by_id.get(3,  0.0) * 100
        self.output_dict[KEY_UTIL_LTB]               = dcr_by_id.get(5,  0.0) * 100
        self.output_dict[KEY_UTIL_DEFLECTION_CRACK]  = defl_dcr * 100
        self.output_dict[KEY_UTIL_FATIGUE]           = fatigue_dcr * 100
        self.output_dict[KEY_UTIL_LONG_TRANS_SHEAR]  = trans_shear_dcr * 100
        self.output_dict[KEY_UTIL_STRESS_LIMITATION] = stress_dcr * 100

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
        cb.print_critical_forces(forces_dict)

        pair_designs = cb.run_member_designs(forces_dict)

        enrich_crossbracing_dump(pair_designs)
        self._print_crossbracing_design_results(forces_dict, pair_designs)

        return pair_designs

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

        All values are read from ``self.output_dict`` — the immutable snapshot of
        ``input_dict`` captured at the start of ``design()``.  This includes girder
        geometry, span, carriageway width, footpath/median/skew settings, and
        additional-input keys such as deck thickness.

        Must be called after design() has fully run.
        """
        inp = self.output_dict

        steel_grade    = str(self.output_dict.get(KEY_GIRDER)).strip()
        concrete_grade = str(self.output_dict.get(KEY_DECK_CONCRETE_GRADE_BASIC)).strip()

        # output_dict values are in SI metres; BridgeParametersDTO expects mm
        D       = inp[KEY_GIRDER_DEPTH]                   * 1e3
        tw      = inp[KEY_GIRDER_WEB_THICKNESS]           * 1e3
        B_top   = inp[KEY_GIRDER_TOP_FLANGE_WIDTH]        * 1e3
        t_f_top = inp[KEY_GIRDER_TOP_FLANGE_THICKNESS]    * 1e3
        B_bot   = inp[KEY_GIRDER_BOTTOM_FLANGE_WIDTH]     * 1e3
        t_f_bot = inp[KEY_GIRDER_BOTTOM_FLANGE_THICKNESS] * 1e3

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
