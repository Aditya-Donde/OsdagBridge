from __future__ import annotations
import sqlite3
from pathlib import Path
from .ui_fields import FrontendData
from .dto import DeckLayoutProperties, GrillageGeometry, SectionProperties, MaterialProperties
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

from osdagbridge.core.utils.common import (
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
    DEFAULT_CRASH_BARRIER_WIDTH,
    DEFAULT_RAILING_WIDTH,
    DEFAULT_GIRDER_SPACING,
    MPa,
    GPa,
    N,
    m,
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
        parsed = self._parse_basic_inputs()
        self._solve_bridge_layout(parsed)
        self._build_dtos(parsed)
        self.setup_grillage()
        self.add_dead_loads()
        self.add_live_loads()
        self.analyze()

        print(
            f"[PlateGirderBridge.design] "
            f"span={parsed['span']} m | overall_width={self.sizing_result.overall_width} m | "
            f"girders={self.sizing_result.no_of_girders} | "
            f"spacing={self.sizing_result.girder_spacing} m | "
            f"overhang={self.sizing_result.deck_overhang} m | "
            f"girder_depth={self.section_props['D']:.3f} m"
        )

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
        # n_t: transverse grid lines — approx one division every 2 × girder spacings
        n_t = max(3, int(round(span / (DEFAULT_GIRDER_SPACING * 2))))

        self.grillage_geometry = GrillageGeometry(
            L=span,
            n_l=self.sizing_result.no_of_girders,
            n_t=n_t,
            edge_dist=self.sizing_result.deck_overhang,
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
        try:
            con = sqlite3.connect(_DB_PATH)
            cur = con.cursor()
            query_map = {
                "E": "Modulus of Elasticity",
                "V": "Poisson's Ratio",
                "rho": "Density",
                "fy": "Yield Strength",
            }
            cur.execute(
                f'SELECT "{query_map.get(property)}" FROM Material WHERE "Material Name" = ?',
                (material_name,),
            )
            row = cur.fetchone()
            con.close()
            if row:
                if property == "E":                    # Elastic modulus (Pa)
                    return float(row[0]) * GPa
                elif property == "V":                  # Poisson's ratio (unitless)
                    return float(row[0])
                elif property == "rho":                # Unit weight (N/m³)
                    return float(row[0]) * N / m ** 3
                elif property == "fy":                 # Yield strength (Pa)
                    return float(row[0]) * MPa         # DB stores MPa as integer → convert to Pa
        except sqlite3.Error:
            raise LookupError(f"Error querying material database in PlateGirderBridge._lookup_material: {sqlite3.Error}")

    def _build_material_props(self) -> MaterialProperties:
        """Build a MaterialProperties from the selected girder material in basic_inputs."""
        material_name = str(self.basic_inputs.get(KEY_GIRDER, "")).strip()
        e = self._lookup_material(material_name, "E") if material_name else _STEEL_FY_DEFAULT
        v = self._lookup_material(material_name, "V") if material_name else _STEEL_FY_DEFAULT
        rho = self._lookup_material(material_name, "rho") if material_name else _STEEL_FY_DEFAULT
        fy = self._lookup_material(material_name, "fy") if material_name else _STEEL_FY_DEFAULT
        # print(f"e: {e}, v: {v}, rho: {rho}, fy: {fy}")
        return MaterialProperties(
            material="steel",
            E=e,
            v=v,
            rho=rho,
            Fy=fy,
            E0=_STEEL_E0,
            b=_STEEL_B,
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

        Must be called after setup_grillage() has built and registered the model.
        """
        m = self.grillage_model
        m.create_self_weight_load()
        m.create_deck_load()
        m.create_wearing_course_load()
        m.create_footpath_load()
        m.create_crash_barrier_load()
        m.create_railing_load()

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
        m = self.grillage_model
        m.add_vehicle_load_cases_from_combinations()
        m.create_moving_vehicle_load_cases()

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
        start_offset: float = -25.0,
        span: float | None = None,
    ) -> list:
        """
        Create moving load cases for all vehicles previously created by
        add_vehicle_load_cases_from_combinations().

        Delegates to BridgeGrillageModel.create_moving_vehicle_load_cases().

        Parameters
        ----------
        start_offset : float
            Longitudinal offset (m) behind the bridge start where vehicles
            begin traversal (default -25.0).
        span : float, optional
            Override the bridge span (m); defaults to the analysed span.

        Returns
        -------
        list
            All created moving load case objects.
        """
        return self.grillage_model.create_moving_vehicle_load_cases(
            start_offset=start_offset,
            span=span,
        )

    def add_vehicle_load_with_moving_path(
        self,
        vehicle_type: str = "CLASS70R",
        load_case_name: str = "Class 70R",
        x_coord: float = 0.0,
        z_coord: float = 0.0,
        spacing: float = 1.5,
        span: float | None = None,
        y_coord: float = 0.0,
    ) -> dict:
        """
        Add a single vehicle (static + moving) at an explicit position.

        Delegates to BridgeGrillageModel.add_vehicle_load_with_moving_path().

        Parameters
        ----------
        vehicle_type : str
            Load model type (e.g. ``'CLASS70R'``, ``'CLASSA'``).
        load_case_name : str
            Name given to the static load case.
        x_coord : float
            Initial longitudinal position (m) of the vehicle.
        z_coord : float
            Transverse position (m) of the vehicle.
        spacing : float
            Distance (m) behind bridge start for the moving path origin.
        span : float, optional
            Override the bridge span (m).
        y_coord : float
            Vertical coordinate (default 0.0).

        Returns
        -------
        dict
            Keys: ``'vehicle'``, ``'static_load_case'``,
            ``'moving_load_case'``, ``'moving_path'``.
        """
        return self.grillage_model.add_vehicle_load_with_moving_path(
            vehicle_type=vehicle_type,
            load_case_name=load_case_name,
            x_coord=x_coord,
            z_coord=z_coord,
            spacing=spacing,
            span=span,
            y_coord=y_coord,
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
