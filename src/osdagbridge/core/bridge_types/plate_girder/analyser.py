import ospgrillage as og
import xarray as xr
# from math import sqrt, pi
# import openseespy.opensees as ops
from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
from osdagbridge.core.utils.codes.keyfile import LANE_REDUCTION_FACTORS
from osdagbridge.core.utils.common import *
from osdagbridge.core.bridge_components.super_structure.plate_girder.geometry import (
    girder_self_weight_kN_m,
    STEEL_UNIT_WEIGHT_kN_m3,
)
from osdagbridge.core.bridge_components.super_structure.deck.geometry import (
    slab_dead_load_kN_m2,
    wearing_course_dead_load_kN_m2,
    WET_CONCRETE_DENSITY_kN_m3,
)
from osdagbridge.core.bridge_components.super_structure.footpath.geometry import (
    footpath_dead_load_kN_m2,
)
from osdagbridge.core.bridge_components.super_structure.crash_barrier.geometry import (
    crash_barrier_dead_load_kN_m,
)
from osdagbridge.core.bridge_components.super_structure.railing.geometry import (
    railing_dead_load_kN_m,
)
from osdagbridge.core.bridge_components.super_structure.median.geometry import (
    median_dead_load_kN_m,
)
from osdagbridge.core.bridge_types.plate_girder.bridge_geometry import BridgeGeometry, CrossSectionLayout
from osdagbridge.core.bridge_types.plate_girder.load_placement import LoadPlacementManager
import warnings
from osdagbridge.core.bridge_types.plate_girder.analysis_results import PlateGirderAnalysisResults
from osdagbridge.core.bridge_types.plate_girder.dto import (SectionProperties, SteelProperties, ConcreteProperties, MaterialProperties, GrillageGeometry, DeckLayoutProperties)
from osdagbridge.core.bridge_types.plate_girder.results_data import restructure_data as restructure_data_direct


#: Axle-span length (m) of the IRC:6-2017 Cl.204.6 fatigue truck — axles at
#: 0.0, 4.5 and 5.9 m, per ospgrillage LoadModel.create_fatigue_vehicle().
FATIGUE_VEHICLE_LENGTH = 5.9


class BridgeGrillageModel:

    def __init__(self):

        # -------------------- MATERIALS --------------------
        # Materials are set via create_material()
        self.steel_custom = None

        # -------------------- SECTIONS --------------------
        # Sections are set via create_sections()
        self.edge_longitudinal_section = None
        self.longitudinal_section = None          # representative (girder 0) — back-compat
        self.transverse_section = None
        self.end_transverse_section = None
        # One ospgrillage section per main girder (set by create_sections()).
        self.girder_sections: list = []

        # Cross-section properties (DTO), stashed by create_sections() so that
        # load magnitudes can be derived from actual geometry instead of
        # hard-coded placeholder values.
        self.longitudinal_props: SectionProperties | None = None  # representative (girder 0)
        self.edge_longitudinal_props: SectionProperties | None = None
        # One SectionProperties DTO per main girder, ordered by girder index.
        self.girder_props: list = []

        # -------------------- GRILLAGE MEMBERS --------------------
        # Members are set via create_material() once sections and material are ready
        self.longitudinal_beam = None            # representative (girder 0) — back-compat
        self.edge_longitudinal_beam = None
        self.transverse_slab = None
        self.end_transverse_slab = None
        # One ospgrillage member per main girder (set by assign_members()).
        self.girder_beams: list = []

        # -------------------- GEOMETRY --------------------
        # Geometry is set via set_geometry()
        self.L = None
        self.n_l = None
        self.n_t = None
        self.edge_dist = None
        self.ext_to_int_dist = None
        self.angle = None
        self.w: float | None = None  # updated from bridge geometry width after set_geometry()

        # placeholder for model
        self.model = None

        # placeholder for overlay load case created later
        self.wearing_course_load = None

        # placeholder for self weight load case created later
        self.self_weight_load_case = None

        # -------------------- LIVE LOAD --------------------
        self.vehicle_moving_loads_by_case: dict = {}  # {case_num: [vehicle, ...]}
        self.vehicle_type_map: dict = {}              # {id(vehicle): vehicle_type_str}

        # -------------------- FATIGUE LOAD (IRC:6 Cl.204.6) --------------------
        self.fatigue_load_cases_list: list = []        # static fatigue load cases
        self.fatigue_vehicles_by_case: dict = {}       # {load_case_name: [vehicle, ...]}
        self.moving_fatigue_load_cases_list: list = []  # moving fatigue load cases

        # -------------------- BRAKING LOAD (IRC:6 Cl.211) --------------------
        self.braking_load_case = None                  # "Braking Load" — from the governing LL case

        # self.geometry = GeometryDefinitions(self.L, self.w, self.model)

        # -------------------- GEOMETRY / LAYOUT --------------------
        self.layout = None
        self.bridge_geometry = None
        self.load_manager = None

    # ============================================================
    #   SET GEOMETRY
    # ============================================================
    def set_geometry(self, geometry: GrillageGeometry, layout: DeckLayoutProperties):
        """
        Sets grillage geometry and builds the cross-section layout and bridge
        geometry from user-supplied GrillageGeometry.

        Parameters
        ----------
        geometry : GrillageGeometry
            Geometry parameters supplied by the user.
        """
        self.L = geometry.L
        self.n_l = geometry.n_l
        self.n_t = geometry.n_t
        self.edge_dist = geometry.edge_dist
        self.ext_to_int_dist = geometry.ext_to_int_dist
        self.angle = geometry.angle

        # -------------------------------------------------
        # Cross-section layout
        # -------------------------------------------------
        self.layout = CrossSectionLayout(
            carriageway_width=layout.carriageway_width,
            crash_barrier_width=layout.crash_barrier_width,
            footpath_width=layout.footpath_width,
            railing_width=layout.railing_width,
            median_width=layout.median_width,
            n_footpaths=layout.n_footpaths,
        )

        # -------------------------------------------------
        # Bridge geometry (width derived from layout)
        # -------------------------------------------------
        self.bridge_geometry = BridgeGeometry(
            span=self.L,
            width=self.layout.total_width,
        )
        print(f"Bridge width from layout: {self.layout.total_width} m")

        # self.layout.validate_against_bridge(self.bridge_geometry.width)

    # ============================================================
    #   CREATE SECTIONS
    # ============================================================
    def create_sections(self,
                        girder_sections: list[SectionProperties],
                        edge_longitudinal: SectionProperties,
                        transverse: SectionProperties,
                        end_transverse: SectionProperties):
        """
        Creates all grillage sections from user-supplied SectionProperties.

        Parameters
        ----------
        girder_sections : list[SectionProperties]
            One entry per main girder, ordered by girder index. A single-element
            list reproduces the legacy uniform-girder behaviour.
        edge_longitudinal : SectionProperties
            Properties for the overhang edge beam.
        transverse : SectionProperties
            Properties for the transverse slab (unit_width=True).
        end_transverse : SectionProperties
            Properties for the end transverse slab.
        """
        if not girder_sections:
            raise ValueError("create_sections requires at least one girder section.")

        # Per-girder DTOs and ospgrillage sections.
        self.girder_props = list(girder_sections)
        self.girder_sections = [
            og.create_section(A=s.A, J=s.J, Iz=s.Iz, Iy=s.Iy, Az=s.Az, Ay=s.Ay)
            for s in girder_sections
        ]

        # Representative girder 0 retained under the legacy attribute names so
        # existing consumers (self-weight fallback, verify_sections, etc.) work.
        self.longitudinal_props = self.girder_props[0]
        self.longitudinal_section = self.girder_sections[0]

        self.edge_longitudinal_props = edge_longitudinal

        self.edge_longitudinal_section = og.create_section(
            A=edge_longitudinal.A,
            J=edge_longitudinal.J,
            Iz=edge_longitudinal.Iz,
            Iy=edge_longitudinal.Iy,
            Az=edge_longitudinal.Az,
            Ay=edge_longitudinal.Ay,
        )

        self.transverse_section = og.create_section(
            A=transverse.A,
            J=transverse.J,
            Iy=transverse.Iy,
            Iz=transverse.Iz,
            Ay=transverse.Ay,
            Az=transverse.Az,
            unit_width=True,
        )

        self.end_transverse_section = og.create_section(
            A=end_transverse.A,
            J=end_transverse.J,
            Iy=end_transverse.Iy,
            Iz=end_transverse.Iz,
            Ay=end_transverse.Ay,
            Az=end_transverse.Az,
        )

    # ============================================================
    #   CREATE MATERIAL
    # ============================================================
    def create_material(self, props: MaterialProperties):
        """
        Creates a custom material from the supplied properties.

        Parameters
        ----------
        props : SteelProperties
            Material properties supplied by the user.
        """
        self.steel_custom = og.create_material(
            material="steel", E=props.steel_prop.E, v=props.steel_prop.v, rho=props.steel_prop.rho,
            Fy=props.steel_prop.Fy, E0=props.steel_prop.E0, b=props.steel_prop.b
        )

    def assign_members(self):
        """
        Creates grillage members by pairing each section with the current
        material (``self.steel_custom``).

        Must be called after both ``create_sections()`` and
        ``create_material()`` have been called.
        """
        self.girder_beams = [
            og.create_member(section=sec, material=self.steel_custom)
            for sec in self.girder_sections
        ]
        # Representative girder 0 under the legacy attribute name.
        self.longitudinal_beam = self.girder_beams[0]
        self.edge_longitudinal_beam = og.create_member(
            section=self.edge_longitudinal_section, material=self.steel_custom
        )
        self.transverse_slab = og.create_member(
            section=self.transverse_section, material=self.steel_custom
        )
        self.end_transverse_slab = og.create_member(
            section=self.end_transverse_section, material=self.steel_custom
        )

    # ============================================================
    #   CREATE THE GRILLAGE MODEL
    # ============================================================
    def create_model(self):

        # -------------------------------------------------
        # Load placement manager
        # -------------------------------------------------
        self.load_manager = LoadPlacementManager(
            bridge=self.bridge_geometry,
            layout=self.layout
        )

        # -------------------------------------------------
        # Update width used by grillage model
        # -------------------------------------------------
        self.w = self.bridge_geometry.width

        self.model = og.create_grillage(
            bridge_name="Osdag Bridge",
            long_dim=self.L,
            width=self.w,
            skew=self.angle,
            num_long_grid=self.n_l,
            num_trans_grid=self.n_t,
            edge_beam_dist=self.edge_dist,                                    
            ext_to_int_dist=self.ext_to_int_dist,
            mesh_type="Oblique"  # ('Ortho' or 'Oblique')
        )

        # Assign members — one section per main girder.
        self._assign_girder_members()

        # Assign edge properties only if overhang exists; otherwise the two outer
        # grid lines are real girders and are already handled by the loop above.
        if self.edge_dist > 0:
            self.model.set_member(self.edge_longitudinal_beam, member="edge_beam")
        self.model.set_member(self.transverse_slab, member="transverse_slab")
        self.model.set_member(self.end_transverse_slab, member="start_edge")
        self.model.set_member(self.end_transverse_slab, member="end_edge")

        # Generate OpenSees model
        self.model.create_osp_model(pyfile=False)

        # update geometry with model
        # self.geometry.model = self.model

    def _assign_girder_members(self):
        """
        Assign one section per main girder by isolating each longitudinal z_group.

        ospgrillage groups longitudinal grid lines into z_groups — one per girder
        line. We build the ordered list of main-girder z_groups (dropping the two
        overhang edge-beam lines when an overhang exists) and assign
        ``self.girder_beams[i]`` to the i-th line using the inclusive
        ``only_group`` targeting added to ospgrillage's ``set_member``.

        z_groups are numbered ascending with transverse (z) position, so index i
        of ``main_groups`` lines up with girder index i of ``self.girder_beams``.
        """
        model = self.model
        zg = model.common_grillage_element_z_group

        # All longitudinal z_groups, ascending by transverse (z) position.
        long_cats = (
            "edge_beam", "exterior_main_beam_1",
            "interior_main_beam", "exterior_main_beam_2",
        )
        all_long_groups = sorted({g for cat in long_cats for g in zg.get(cat, [])})

        # With an overhang the two outermost lines are edge beams (handled by the
        # caller); without one, every longitudinal line is a structural girder.
        main_groups = all_long_groups[1:-1] if self.edge_dist > 0 else all_long_groups

        n_beams = len(self.girder_beams)
        if len(main_groups) != n_beams:
            warnings.warn(
                f"_assign_girder_members: {len(main_groups)} girder grid lines but "
                f"{n_beams} girder section(s); unmatched lines reuse the last section."
            )

        def _member_for_group(g: int) -> str:
            # Any category whose list contains g is a valid set_member target;
            # check the single-line categories before the interior/edge lists.
            for cat in (
                "exterior_main_beam_1", "exterior_main_beam_2",
                "interior_main_beam", "edge_beam",
            ):
                if g in zg.get(cat, []):
                    return cat
            raise ValueError(
                f"z_group {g} not found in any longitudinal member category"
            )

        for i, g in enumerate(main_groups):
            beam = self.girder_beams[i] if i < n_beams else self.girder_beams[-1]
            model.set_member(beam, member=_member_for_group(g), only_group=g)

    # ============================================================
    #   PLOT THE MODEL
    # ============================================================
    def plot_model(self):
        if self.model is None:
            raise ValueError("Model not created yet. Call create_model() first.")

        # basic plot
        og.opsplt.plot_model(show_nodes="yes", show_nodetags="yes")

        # ops_vis 3D plot
        og.opsv.plot_model(az_el=(-90, 0), element_labels=0)
        fig = og.plt.gcf()
        fig.set_size_inches(8, 8)
        og.plt.show()

    # ============================================================
    #   Dead Load
    # ============================================================

    def create_self_weight_load(self, model=None, L=None):
        """Creates beam self weight distributed along length.

        Magnitude is derived per girder from its own section area (m²) × 78.5
        kN/m³, so each loaded grid line tracks the actual section assigned to it
        rather than a single shared value. When all girders share one section
        this reduces to the previous uniform behaviour.
        """
        model = model or self.model
        if model is None:
            raise ValueError("Model is not available. Create model before adding loads.")

        if not self.girder_props:
            raise ValueError(
                "create_sections() must be called before create_self_weight_load(): "
                "girder cross-section area is required to compute self weight."
            )

        L = L or self.L

        start_beam = 0
        end_beam = L

        # Per-girder areas ordered by ascending transverse (z) position.
        girder_areas = [p.A for p in self.girder_props]

        # Ordered transverse positions of the main girders (ascending z); used to
        # map each loaded grid line back to its girder index.
        all_z_sorted = sorted(model.Mesh_obj.noz)
        main_z_sorted = all_z_sorted[1:-1] if self.edge_dist > 0 else all_z_sorted

        def _area_for_z(z: float) -> float:
            if not main_z_sorted:
                return girder_areas[0]
            idx = min(
                range(len(main_z_sorted)),
                key=lambda k: abs(main_z_sorted[k] - z),
            )
            return girder_areas[idx] if idx < len(girder_areas) else girder_areas[-1]

        DL_self_weight = og.create_load_case(name="SW")

        # iterate through all grillage transverse positions (except extreme edges)
        for z_pos in model.Mesh_obj.noz[1:-1]:
            A_girder_m2 = _area_for_z(z_pos)
            beam_mag = girder_self_weight_kN_m(A_girder_m2, STEEL_UNIT_WEIGHT_kN_m3) * kN / m  # N/m
            print(f"Self weight line load @ z={z_pos:.3f} m: {beam_mag:.2f} N/m (A={A_girder_m2:.5f} m²)")
            p1 = og.create_load_vertex(x=start_beam, z=z_pos, p=beam_mag)
            p2 = og.create_load_vertex(x=end_beam, z=z_pos, p=beam_mag)

            line_load = og.create_load(
                loadtype="line",
                point1=p1,
                point2=p2,
            )

            DL_self_weight.add_load(line_load)

        # store reference on the instance
        self.self_weight_load_case = DL_self_weight

        model.add_load_case(DL_self_weight)
        return DL_self_weight

    def create_deck_load(self, model=None, slab_thickness_m: float | None = None,
                         concrete_density_kN_m3: float | None = None):
        """
        Creates the wet-concrete deck slab patch load over the full bridge deck.

        This is the construction-stage slab load applied to the bare steel
        girder (composite action has not developed yet). The magnitude is
        computed as ``slab_thickness × ρ_concrete``; wearing-course and any
        other superimposed dead loads are NOT included here — they belong to
        separate load cases applied after hardening.

        Parameters
        ----------
        slab_thickness_m : float
            Deck slab thickness in metres (required).
        concrete_density_kN_m3 : float, optional
            Wet concrete density (defaults to 25 kN/m³).

        Geometry is obtained from load_manager.
        The created load case is stored on `self.deck_load_case`.
        """
        model = model or self.model
        if model is None:
            raise ValueError("Model is not available. Create model before adding loads.")

        if slab_thickness_m is None:
            raise ValueError(
                "create_deck_load requires slab_thickness_m (in metres) so the "
                "wet-concrete load magnitude can be derived from t × ρ_concrete."
            )

        rho_c = WET_CONCRETE_DENSITY_kN_m3 if concrete_density_kN_m3 is None else concrete_density_kN_m3

        # -------------------------------------------------
        # Load magnitude (UDL over area): t × ρ_concrete  [kN/m²]
        # -------------------------------------------------
        deck_mag = slab_dead_load_kN_m2(slab_thickness_m, rho_c) * kN / m**2  # N/m²
        print(f"Deck slab load magnitude: {deck_mag:.2f} N/m²")

        # -------------------------------------------------
        # Get geometry from load manager
        # -------------------------------------------------
        geom = self.load_manager.deck_load()

        # -------------------------------------------------
        # Convert geometry → ospgrillage vertices
        # -------------------------------------------------
        p1 = og.create_load_vertex(
            x=geom.p1.x, z=geom.p1.z, p=deck_mag
        )
        p2 = og.create_load_vertex(
            x=geom.p2.x, z=geom.p2.z, p=deck_mag
        )
        p3 = og.create_load_vertex(
            x=geom.p3.x, z=geom.p3.z, p=deck_mag
        )
        p4 = og.create_load_vertex(
            x=geom.p4.x, z=geom.p4.z, p=deck_mag
        )

        # -------------------------------------------------
        # Create patch load
        # -------------------------------------------------
        deck_load = og.create_load(
            loadtype="patch",
            name="deck slab",
            point1=p1,
            point2=p2,
            point3=p3,
            point4=p4,
        )

        # -------------------------------------------------
        # Create & register load case
        # -------------------------------------------------
        DL_deck = og.create_load_case(name="DD")
        DL_deck.add_load(deck_load)
        model.add_load_case(DL_deck)

        # store reference
        self.deck_load_case = DL_deck

        return DL_deck

    def create_wearing_course_load(self, model=None, edge_clearance=0.0,
                                   thickness_m: float | None = None,
                                   density_kN_m3: float | None = None,
                                   partial_safety_factor: float = 1.0):
        """Creates wearing course load (patch).

        The magnitude is computed as ``thickness × ρ``. Typical bituminous
        wearing course: 50 mm at 24 kN/m³ → 1.20 kN/m².

        Parameters
        ----------
        thickness_m : float
            Wearing-course thickness in metres (required).
        density_kN_m3 : float, optional
            Unit weight of the wearing-course material. Defaults to
            24 kN/m³ (bituminous). Use 25 kN/m³ for concrete overlays.

        If `model`, `L` or `w` are not provided they default to the
        instance values `self.model`, `self.L`, `self.w`.
        The created load case is stored on `self.wearing_course_load`.
        """
        model = model or self.model
        if model is None:
            raise ValueError("Model is not available. Create model before adding loads.")

        if thickness_m is None:
            raise ValueError(
                "create_wearing_course_load requires thickness_m (in metres) "
                "so the overlay load magnitude can be derived from t × ρ."
            )
        overlay_kw = {} if density_kN_m3 is None else {"density_kN_m3": density_kN_m3}
        overlay_mag = wearing_course_dead_load_kN_m2(thickness_m, **overlay_kw) * kN / m**2  # N/m²
        print(f"Wearing course load magnitude: {overlay_mag:.2f} N/m²")
        # --------------------------------
        # Get geometry from geometry module
        # --------------------------------
        overlay_geom = self.load_manager.overlay_load(
            edge_clearance=edge_clearance
        )

        # --------------------------------
        # Convert geometry → ospgrillage
        # --------------------------------
        p1 = og.create_load_vertex(
            x=overlay_geom.p1.x, z=overlay_geom.p1.z, p=overlay_mag
        )
        p2 = og.create_load_vertex(
            x=overlay_geom.p2.x, z=overlay_geom.p2.z, p=overlay_mag
        )
        p3 = og.create_load_vertex(
            x=overlay_geom.p3.x, z=overlay_geom.p3.z, p=overlay_mag
        )
        p4 = og.create_load_vertex(
            x=overlay_geom.p4.x, z=overlay_geom.p4.z, p=overlay_mag
        )

        overlay = og.create_load(
            loadtype="patch",
            name="overlay",
            point1=p1,
            point2=p2,
            point3=p3,
            point4=p4,
        )

        DL_overlay = og.create_load_case(name=f"{partial_safety_factor} DW")
        DL_overlay.add_load(overlay)
        model.add_load_case(DL_overlay, load_factor=partial_safety_factor)

        # store reference on the instance
        self.wearing_course_load = DL_overlay

        return DL_overlay

    def create_footpath_load(self, model=None):
        """
        Creates footpath patch loads on both sides of the bridge.

        Geometry is obtained from load_manager.
        The created load case is stored on `self.footpath_load_case`.
        """
        model = model or self.model
        if model is None:
            raise ValueError("Model is not available. Create model before adding loads.")

        # If neither footpath side exists, skip load creation entirely
        sides_present = [s for s in ("left", "right") if self.layout.has_component(f"footpath_{s}")]
        if not sides_present:
            warnings.warn("No footpath component in layout; skipping footpath load creation")
            self.footpath_load_case = None
            return None
        # -------------------------------------------------
        # Load magnitude — IRC 6:2017 Cl.206.1 (footway load)
        # -------------------------------------------------
        footpath_mag = footpath_dead_load_kN_m2() * kN / m**2  # N/m²
        print(f"Footpath load magnitude: {footpath_mag:.2f} N/m²")

        # -------------------------------------------------
        # Create load case
        # -------------------------------------------------
        DL_footpath = og.create_load_case(name="Footpath load")

        # -------------------------------------------------
        # Only sides that exist in the layout
        # -------------------------------------------------
        for side in sides_present:
            # geometry from load manager
            geom = self.load_manager.footpath_load(side)

            print(
                f"[Footpath {side}] patch corners: "
                f"p1(x={geom.p1.x:.3f}, z={geom.p1.z:.3f})  "
                f"p2(x={geom.p2.x:.3f}, z={geom.p2.z:.3f})  "
                f"p3(x={geom.p3.x:.3f}, z={geom.p3.z:.3f})  "
                f"p4(x={geom.p4.x:.3f}, z={geom.p4.z:.3f})"
            )

            # convert geometry → ospgrillage vertices
            p1 = og.create_load_vertex(
                x=geom.p1.x, z=geom.p1.z, p=footpath_mag
            )
            p2 = og.create_load_vertex(
                x=geom.p2.x, z=geom.p2.z, p=footpath_mag
            )
            p3 = og.create_load_vertex(
                x=geom.p3.x, z=geom.p3.z, p=footpath_mag
            )
            p4 = og.create_load_vertex(
                x=geom.p4.x, z=geom.p4.z, p=footpath_mag
            )

            # create patch load
            footpath = og.create_load(
                loadtype="patch",
                name=f"{side} footpath",
                point1=p1,
                point2=p2,
                point3=p3,
                point4=p4,
            )

            DL_footpath.add_load(footpath)

        # -------------------------------------------------
        # Register load case
        # -------------------------------------------------
        model.add_load_case(DL_footpath)

        # store reference
        self.footpath_load_case = DL_footpath

        return DL_footpath

    def create_crash_barrier_load(self, model=None, barrier_load_kN_per_m: float | None = None):
        """
        Creates crash (edge) barrier line loads on both sides of the bridge.

        Parameters
        ----------
        barrier_load_kN_per_m : float, optional
            Barrier self-weight per unit length (kN/m). When provided (typically
            from the Additional Inputs dialog), this value is used directly.
            Defaults to ``RCC_CRASH_BARRIER_LOAD_kN_per_m`` (6.54 kN/m) when
            not specified.

        Geometry is obtained from load_manager.
        The created load case is stored on `self.crash_barrier_load_case`.
        """
        model = model or self.model
        if model is None:
            raise ValueError("Model is not available. Create model before adding loads.")

        # If neither crash barrier side exists, skip load creation entirely
        sides_present = [s for s in ("left", "right") if self.layout.has_component(f"crash_barrier_{s}")]
        if not sides_present:
            warnings.warn("No crash barrier component in layout; skipping crash barrier load creation")
            self.crash_barrier_load_case = None
            return None

        # -------------------------------------------------
        # Load magnitude — from input or IRC 5:2015 default (crash_barrier.geometry)
        # -------------------------------------------------
        barrier_load = crash_barrier_dead_load_kN_m(barrier_load_kN_per_m) * kN / m
        print(f"Crash barrier line load magnitude: {barrier_load:.2f} N/m")
        # -------------------------------------------------
        # Create load case
        # -------------------------------------------------
        DL_barrier = og.create_load_case(name="Crash barrier load")

        # -------------------------------------------------
        # Only sides that exist in the layout
        # -------------------------------------------------
        for side in sides_present:
            # geometry from load manager
            geom = self.load_manager.crash_barrier_load(side)

            print(
                f"[Crash barrier {side}] line load: "
                f"start(x={geom.start.x:.3f}, z={geom.start.z:.3f})  "
                f"end(x={geom.end.x:.3f}, z={geom.end.z:.3f})"
            )

            # convert geometry → ospgrillage vertices
            p1 = og.create_load_vertex(
                x=geom.start.x, z=geom.start.z, p=barrier_load
            )
            p2 = og.create_load_vertex(
                x=geom.end.x, z=geom.end.z, p=barrier_load
            )

            # create line load
            barrier = og.create_load(
                loadtype="line",
                name=f"{side} crash barrier",
                point1=p1,
                point2=p2,
            )

            DL_barrier.add_load(barrier)

        # -------------------------------------------------
        # Register load case
        # -------------------------------------------------
        model.add_load_case(DL_barrier)

        # store reference
        self.crash_barrier_load_case = DL_barrier

        return DL_barrier

    def create_railing_load(self, model=None, railing_load_kN_per_m: float | None = None):
        """
        Creates railing line loads on both sides of the bridge.

        Parameters
        ----------
        railing_load_kN_per_m : float, optional
            Railing self-weight per unit length (kN/m). When provided (typically
            from the Additional Inputs dialog), this value is used directly.
            Defaults to ``IRC6_2017.cl_206_5_railing_load()`` (kg/m → kN/m)
            per IRC 6:2017 Cl.206.5 when not specified.

        Geometry is obtained from load_manager.
        The created load case is stored on `self.railing_load_case`.
        """
        model = model or self.model
        if model is None:
            raise ValueError("Model is not available. Create model before adding loads.")

        # If neither railing side exists, skip load creation entirely
        railing_sides_present = [s for s in ("left", "right") if self.layout.has_component(f"railing_{s}")]
        if not railing_sides_present:
            warnings.warn("No railing component in layout; skipping railing load creation")
            self.railing_load_case = None
            return None

        # -------------------------------------------------
        # Load magnitude — from user input or IRC 6:2017 Cl.206.5 default (railing.geometry)
        # -------------------------------------------------
        railing_udl = railing_dead_load_kN_m(railing_load_kN_per_m) * kN / m  # N/m
        print(f"Railing line load magnitude: {railing_udl:.2f} N/m")

        # -------------------------------------------------
        # Create load case
        # -------------------------------------------------
        DL_railing = og.create_load_case(name="Railing load")

        # -------------------------------------------------
        # Only sides that exist in the layout
        # -------------------------------------------------
        for side in railing_sides_present:
            # geometry from load manager
            geom = self.load_manager.railing_load(side)

            print(
                f"[Railing {side}] line load: "
                f"start(x={geom.start.x:.3f}, z={geom.start.z:.3f})  "
                f"end(x={geom.end.x:.3f}, z={geom.end.z:.3f})"
            )

            # convert geometry → ospgrillage vertices
            p1 = og.create_load_vertex(
                x=geom.start.x, z=geom.start.z, p=railing_udl
            )
            p2 = og.create_load_vertex(
                x=geom.end.x, z=geom.end.z, p=railing_udl
            )

            # create line load
            railing = og.create_load(
                loadtype="line",
                name=f"{side} railing",
                point1=p1,
                point2=p2,
            )

            DL_railing.add_load(railing)

        # -------------------------------------------------
        # Register load case
        # -------------------------------------------------
        model.add_load_case(DL_railing)

        # store reference
        self.railing_load_case = DL_railing

        return DL_railing

    def create_median_load(self, model=None, median_load_kN_per_m: float | None = None):
        """
        Creates median line load acting along the centerline of the median.

        Parameters
        ----------
        median_load_kN_per_m : float, optional
            Median self-weight per unit length (kN/m). When provided (typically
            from the Additional Inputs dialog), this value is used directly.
            Defaults to ``MEDIAN_LOAD_kN_per_m`` (4.00 kN/m) when not
            specified.

        Geometry is obtained from load_manager.
        The created load case is stored on `self.median_load_case`.
        """
        model = model or self.model
        if model is None:
            raise ValueError("Model is not available. Create model before adding loads.")

        # -------------------------------------------------
        # Load magnitude — from input or default (median.geometry)
        # -------------------------------------------------
        median_udl = median_dead_load_kN_m(median_load_kN_per_m) * kN / m
        print(f"Median line load magnitude: {median_udl:.2f} N/m")

        # If there is no median component in the layout, skip creating median load
        if not self.layout.has_component("median"):
            warnings.warn("No median component in layout; skipping median load creation")
            self.median_load_case = None
            return None

        # -------------------------------------------------
        # Get geometry from load manager
        # -------------------------------------------------
        geom = self.load_manager.median_line_load()

        print(
            f"[Median] line load: "
            f"start(x={geom.start.x:.3f}, z={geom.start.z:.3f})  "
            f"end(x={geom.end.x:.3f}, z={geom.end.z:.3f})"
        )

        # -------------------------------------------------
        # Convert geometry → ospgrillage vertices
        # -------------------------------------------------
        p1 = og.create_load_vertex(
            x=geom.start.x, z=geom.start.z, p=median_udl
        )
        p2 = og.create_load_vertex(
            x=geom.end.x, z=geom.end.z, p=median_udl
        )

        # -------------------------------------------------
        # Create line load
        # -------------------------------------------------
        median_load = og.create_load(
            loadtype="line",
            name="median",
            point1=p1,
            point2=p2,
        )

        # -------------------------------------------------
        # Create & register load case
        # -------------------------------------------------
        DL_median = og.create_load_case(name="Median load")
        DL_median.add_load(median_load)
        model.add_load_case(DL_median)

        # store reference
        self.median_load_case = DL_median

        return DL_median

    # ============================================================
    #   Temperature Load
    # ============================================================

    def create_temperature_load(
            self,
            model=None,
            temperature_load_kN_m2: float | None = None,
            partial_safety_factor: float = 1.0,
    ):
        """
        Creates a uniform temperature load as a patch load over the full bridge
        deck footprint (same extents as the deck slab load).

        The load represents the equivalent transverse effect of a temperature
        differential on the bridge superstructure per IRC:6-2017 Cl.215.

        Parameters
        ----------
        temperature_load_kN_m2 : float
            Temperature load intensity in kN/m² (required).
        partial_safety_factor : float
            Partial safety factor applied to the ``"{psf} TL"`` load case.
            Default is 1.0.

        The created load case is stored on ``self.temperature_load_case``.
        """
        model = model or self.model
        if model is None:
            raise ValueError("Model is not available. Create model before adding loads.")

        if temperature_load_kN_m2 is None:
            raise ValueError(
                "create_temperature_load requires temperature_load_kN_m2 (in kN/m²) "
                "so the patch load magnitude can be set."
            )

        tl_mag = temperature_load_kN_m2 * kN / m**2  # N/m²
        print(f"Temperature load magnitude: {tl_mag:.2f} N/m²")

        # -------------------------------------------------
        # Get geometry from load manager (full deck footprint)
        # -------------------------------------------------
        geom = self.load_manager.deck_load()

        # -------------------------------------------------
        # Convert geometry → ospgrillage vertices
        # -------------------------------------------------
        p1 = og.create_load_vertex(x=geom.p1.x, z=geom.p1.z, p=tl_mag)
        p2 = og.create_load_vertex(x=geom.p2.x, z=geom.p2.z, p=tl_mag)
        p3 = og.create_load_vertex(x=geom.p3.x, z=geom.p3.z, p=tl_mag)
        p4 = og.create_load_vertex(x=geom.p4.x, z=geom.p4.z, p=tl_mag)

        # -------------------------------------------------
        # Create patch load
        # -------------------------------------------------
        temp_load = og.create_load(
            loadtype="patch",
            name="temperature load",
            point1=p1,
            point2=p2,
            point3=p3,
            point4=p4,
        )

        # -------------------------------------------------
        # Create & register load case
        # -------------------------------------------------
        TL = og.create_load_case(name=f"{partial_safety_factor} TL")
        TL.add_load(temp_load)
        model.add_load_case(TL, load_factor=partial_safety_factor)

        # store reference
        self.temperature_load_case = TL

        return TL

    # ============================================================
    #   Seismic / Earthquake Load
    # ============================================================

    @staticmethod
    def _load_case_resultant_kN(load_case) -> float:
        """
        Integrate the total applied resultant (kN) of a load case directly
        from its load objects: line loads (p in N/m × length), patch loads
        (p in N/m² × quad area), point loads (p in N) and nodal loads (|Fy|).
        Compound loads (e.g. vehicles) are summed over their children.

        Only the per-load ``factor`` stored in ``load_groups`` is applied —
        the registration-time ``load_factor`` passed to
        ``model.add_load_case()`` is NOT included, so the result is the
        unfactored load total of the case.
        """
        if load_case is None:
            return 0.0

        def _resultant_N(load) -> float:
            children = getattr(load, "compound_load_obj_list", None)
            if children:
                return sum(_resultant_N(child) for child in children)
            pts = [pt for pt in getattr(load, "point_list", []) if pt is not None]
            if not pts:
                # nodal load — vertical component only
                return abs(getattr(load, "Fy", 0.0) or 0.0)
            if len(pts) == 1:
                # point load: p is the force (N)
                return abs(pts[0].p)
            if len(pts) >= 4:
                # patch load: shoelace area of the corner quad × average p (N/m²)
                area = 0.5 * abs(sum(
                    pts[i].x * pts[(i + 1) % len(pts)].z
                    - pts[(i + 1) % len(pts)].x * pts[i].z
                    for i in range(len(pts))
                ))
                p_avg = sum(pt.p for pt in pts) / len(pts)
                return abs(p_avg) * area
            # line load (2–3 vertices): trapezoidal p (N/m) over segment lengths
            return abs(sum(
                0.5 * (a.p + b.p) * ((b.x - a.x) ** 2 + (b.z - a.z) ** 2) ** 0.5
                for a, b in zip(pts[:-1], pts[1:])
            ))

        return sum(
            float(entry.get("factor", 1) or 1) * _resultant_N(entry["load"])
            for entry in load_case.load_groups
        ) / 1000.0

    def _total_dead_load_kN(self) -> float:
        """
        Total unfactored dead load (kN) used as the seismic mass per
        IRC:6-2017 Cl.218.5: the ``DL`` combination (self weight, deck,
        footpath and SIDL) plus the wearing-course (surfacing) case, which
        is registered separately as ``DW``.

        Derived on demand from the registered load cases — no per-method
        accumulator is needed because ``create_dead_load_combination()``
        already aggregates every dead-load sub-case applied to the model.
        """
        dl = self._load_case_resultant_kN(getattr(self, "dead_load_combination", None))
        dw = self._load_case_resultant_kN(getattr(self, "wearing_course_load", None))
        if dl == 0.0:
            warnings.warn(
                "Total dead load for seismic is zero — call the dead-load "
                "creation methods and create_dead_load_combination() first."
            )
        return dl + dw

    @staticmethod
    def _vehicle_total_weight_kN(vehicle_type: str) -> float:
        """
        Return total unfactored axle load (kN) for one vehicle.

        The IRC6_2017 vehicle geometries define ``wheel_loads`` with the ``t``
        unit constant (tonne → N), so the sum is in N and converted to kN here.
        """
        try:
            if vehicle_type == 'ClassA':
                return float(sum(IRC6_2017.cl_204_1_ClassA_vehicle()['wheel_loads'])) / kN
            elif vehicle_type == 'Class70R':
                return float(sum(IRC6_2017.cl_204_1_Class70R_vehicle_wheel()['wheel_loads'])) / kN
        except Exception:
            pass
        return 0.0

    def _governing_case_num(self) -> int | None:
        """
        Table 6A case number of the governing live-load case, parsed out of
        ``self.governing_ll_name`` (e.g. ``"Case2 1xClassA + 1xClass70R"`` → 2).

        Returns ``None`` when no governing case has been identified yet or the
        name does not carry a parsable case number.
        """
        governing_name = getattr(self, 'governing_ll_name', None)
        if not governing_name:
            return None
        try:
            return int(str(governing_name).split('Case')[1].split(' ')[0])
        except (IndexError, ValueError):
            return None

    def _get_governing_ll_kN(self) -> float:
        """Total unfactored vehicle weight (kN) for the governing live load case."""
        case_num = self._governing_case_num()
        if case_num is None:
            return 0.0
        vehicles = self.vehicle_moving_loads_by_case.get(case_num, [])
        return sum(
            self._vehicle_total_weight_kN(self.vehicle_type_map.get(id(v), ''))
            for v in vehicles
        )

    @staticmethod
    def _spectral_sa_g(soil_type: int, T: float) -> float:
        """Spectral acceleration coefficient Sa/g per IRC:6-2017 Cl.218.5.1."""
        T = min(max(float(T), 0.0), 4.0)
        if soil_type == 1:    # Type I: Rock / Hard (N > 30)
            corner = 0.40
            factor = 1.00
        elif soil_type == 2:  # Type II: Medium (10 < N ≤ 30)
            corner = 0.55
            factor = 1.36
        else:                 # Type III: Soft (N < 10)
            corner = 0.67
            factor = 1.67
        if T <= 0.10:
            return 1 + 15 * T
        if T <= corner:
            return 2.50
        return factor / T

    def create_seismic_load_cases(
            self,
            model=None,
            z_value: float = 0.10,
            soil_type: int = 1,
            importance_factor: float = 1.0,
            damping_percent: float = 2.0,
            response_reduction_factor: float = 1.0,
            time_period: float = 0.5,
            Ah: float | None = None,
            Av: float | None = None,
            dead_load_kN: float | None = None,
            live_load_kN: float | None = None,
            partial_safety_factor: float = 1.5,
    ) -> dict:
        """
        Creates seismic load cases per IRC:6-2017 Cl. 218.5.1 and combines them
        per Cl. 218.3.

        DL and LL default to model state: total DL is integrated from the
        registered dead-load cases (``_total_dead_load_kN()``) and LL from the
        governing vehicle case (``_get_governing_ll_kN()``). Explicit
        ``dead_load_kN`` / ``live_load_kN`` values (the seismic tab's Custom
        mode) override the automatic derivation.

        Load cases created
        ------------------
        ``"EQ_X"``            : Longitudinal seismic (Fx at all nodes, 0% LL).
        ``"EQ_Z"``            : Transverse seismic (Fz at all nodes, 20% LL).
        ``"EQ_Y"``            : Vertical seismic (Fy upward, Av = 2/3 × Ah, 20% LL).
        ``"{lf} EQ (a/b/c)"`` : IRC 218.3 combination cases registered with
                                ``partial_safety_factor``.

        The vertical-dominant combination (c) is also stored on
        ``self.seismic_load_case`` so the ULS Table B.2 SEISMIC combinations
        include it as their EL term.

        Parameters
        ----------
        z_value : float
            Zone factor Z from IRC Table 16 (project location ``weather_data``).
        soil_type : int
            1 = Rock/Hard (N>30), 2 = Medium (10<N≤30), 3 = Soft (N<10).
        importance_factor : float
            I (IRC Table 19): 1.0 normal, 1.2 important, 1.5 large critical.
        damping_percent : float
            Damping %: 2 (steel/composite), 5 (RC), 10 (retrofitted).
        response_reduction_factor : float
            R from IRC Table 20 (1.0 non-ductile Zone II, 2.0 ductile).
        time_period : float
            Fundamental time period T (s) used for Sa/g when Ah is computed here.
        Ah : float | None
            Horizontal seismic coefficient. If provided by the UI
            (``KEY_SL_HORIZONTAL_COEFF``), it is used directly; otherwise
            computed from z_value, importance_factor, Sa/g and damping factor.
        Av : float | None
            Vertical seismic coefficient. If provided
            (``KEY_SL_VERTICAL_COEFF``), used directly; otherwise taken as
            (2/3) × Ah per IRC 218.4.
        dead_load_kN : float | None
            Custom dead load for seismic force; None → derived from model state.
        live_load_kN : float | None
            Custom live load for seismic force; None → derived from the
            governing vehicle case.
        partial_safety_factor : float
            ULS load factor for combination cases (IRC Table B.2 seismic: 1.5).

        Returns
        -------
        dict
            ``{"EQ_X": ..., "EQ_Z": ..., "EQ_Y": ...,
               "EQ_a": ..., "EQ_b": ..., "EQ_c": ...}``
        """
        model = model or self.model
        if model is None:
            raise ValueError("Model not created. Call create_model() first.")

        # ── DL and LL from model state unless custom values are supplied ──
        if dead_load_kN is None:
            dead_load_kN = self._total_dead_load_kN()
        if live_load_kN is None:
            live_load_kN = self._get_governing_ll_kN()
        print(
            f"Seismic inputs: DL={dead_load_kN:.1f} kN  "
            f"Governing LL={live_load_kN:.1f} kN"
        )

        # ── 1. Seismic coefficients (IRC:6-2017 Cl.218.5.1) ──
        # Use Ah/Av from UI if available; otherwise compute from IRC formula.
        if not Ah:
            sa_g = self._spectral_sa_g(soil_type, time_period)
            damping_factor = IRC6_2017.table_18(damping_percent)
            Ah = (z_value / 2.0) * importance_factor * sa_g * damping_factor
        if not Av:
            Av = (2.0 / 3.0) * Ah  # IRC 218.4: vertical component

        # ── 2. Feq_design for each direction (kN) ──
        # IRC 218.5.2: appropriate LL = 20% for transverse/vertical, 0 for longitudinal
        R = response_reduction_factor
        ll_contribution = 0.20 * live_load_kN
        Feq_X_kN = Ah * dead_load_kN / R                            # longitudinal (0% LL)
        Feq_Z_kN = Ah * (dead_load_kN + ll_contribution) / R        # transverse  (20% LL)
        Feq_Y_kN = Av * (dead_load_kN + ll_contribution) / R        # vertical    (20% LL, Av)

        print(
            f"Seismic loads (IRC:6-2017 Cl.218): Z={z_value}  "
            f"Ah={Ah:.4f}  Av={Av:.4f}\n"
            f"  Feq_X={Feq_X_kN:.2f} kN  "
            f"Feq_Z={Feq_Z_kN:.2f} kN  "
            f"Feq_Y={Feq_Y_kN:.2f} kN"
        )

        # ── 3. Tributary-area distribution (same pattern as wind load) ──
        nox_sorted = sorted(model.Mesh_obj.nox)
        noz_sorted = sorted(model.Mesh_obj.noz)
        node_spec  = model.Mesh_obj.node_spec

        def _trib_1d(positions: list, value: float) -> float:
            """Tributary half-interval for `value` inside sorted `positions`."""
            idx   = min(range(len(positions)), key=lambda i: abs(positions[i] - value))
            left  = (positions[idx] - positions[idx - 1]) / 2 if idx > 0                  else 0.0
            right = (positions[idx + 1] - positions[idx]) / 2 if idx < len(positions) - 1 else 0.0
            return left + right

        total_trib_area = self.L * (self.w or self.bridge_geometry.width)  # m²

        # Convert Feq (kN) → intensity (N/m²) for uniform mass distribution
        Feq_X_N_per_m2 = Feq_X_kN * 1000.0 / total_trib_area
        Feq_Z_N_per_m2 = Feq_Z_kN * 1000.0 / total_trib_area
        Feq_Y_N_per_m2 = Feq_Y_kN * 1000.0 / total_trib_area

        # Pre-compute per-node forces for all 3 directions
        node_forces: dict = {}  # {tag: (Fx, Fz, Fy)}
        for tag, spec in node_spec.items():
            coord = spec["coordinate"]
            trib  = _trib_1d(nox_sorted, coord[0]) * _trib_1d(noz_sorted, coord[2])
            node_forces[tag] = (
                Feq_X_N_per_m2 * trib,   # Fx  (longitudinal +x)
                Feq_Z_N_per_m2 * trib,   # Fz  (transverse +z)
                -Feq_Y_N_per_m2 * trib,  # Fy  (vertical, upward = negative)
            )

        # ── 4. Individual directional load cases ──
        EQ_X = og.create_load_case(name="EQ_X")
        EQ_Z = og.create_load_case(name="EQ_Z")
        EQ_Y = og.create_load_case(name="EQ_Y")

        for tag, (fx, fz, fy) in node_forces.items():
            EQ_X.add_load(og.create_load(
                loadtype="nodal", node_tag=tag,
                Fx=fx, Fy=0,  Fz=0,  Mx=0, My=0, Mz=0,
            ))
            EQ_Z.add_load(og.create_load(
                loadtype="nodal", node_tag=tag,
                Fx=0,  Fy=0,  Fz=fz, Mx=0, My=0, Mz=0,
            ))
            EQ_Y.add_load(og.create_load(
                loadtype="nodal", node_tag=tag,
                Fx=0,  Fy=fy, Fz=0,  Mx=0, My=0, Mz=0,
            ))

        model.add_load_case(EQ_X)
        model.add_load_case(EQ_Z)
        model.add_load_case(EQ_Y)
        self.seismic_x_load_case = EQ_X
        self.seismic_z_load_case = EQ_Z
        self.seismic_y_load_case = EQ_Y

        # ── 5. IRC 218.3 combination cases ──
        # (a) ±r1 ± 0.3r2 ± 0.3r3   r1=EQ_X, r2=EQ_Z, r3=EQ_Y
        # (b) ±0.3r1 ± r2 ± 0.3r3
        # (c) ±0.3r1 ± 0.3r2 ± r3
        COMBOS = [
            ("EQ (a)", 1.0, 0.3, 0.3),   # (cx, cz, cy)
            ("EQ (b)", 0.3, 1.0, 0.3),
            ("EQ (c)", 0.3, 0.3, 1.0),
        ]
        combo_cases = []
        lf = partial_safety_factor
        for name, cx, cz, cy in COMBOS:
            lc = og.create_load_case(name=f"{lf} {name}")
            for tag, (fx, fz, fy) in node_forces.items():
                lc.add_load(og.create_load(
                    loadtype="nodal", node_tag=tag,
                    Fx=cx * fx, Fy=cy * fy, Fz=cz * fz,
                    Mx=0, My=0, Mz=0,
                ))
            model.add_load_case(lc, load_factor=lf)
            combo_cases.append(lc)

        self.seismic_combo_a, self.seismic_combo_b, self.seismic_combo_c = combo_cases

        # The ULS Table B.2 SEISMIC combinations consume ``seismic_load_case``
        # as their EL term. Expose the vertical-dominant IRC 218.3 combination
        # (c) — y direction, perpendicular to the deck — since vertical seismic
        # governs superstructure girder bending. Its load_groups are unfactored
        # (the 1.5 registration factor is not baked in), so the ULS builder's
        # own γ_EL (1.5 service / 0.75 construction) applies without
        # double-counting.
        self.seismic_load_case = combo_cases[2]

        return {
            "EQ_X": EQ_X, "EQ_Z": EQ_Z, "EQ_Y": EQ_Y,
            "EQ_a": combo_cases[0], "EQ_b": combo_cases[1], "EQ_c": combo_cases[2],
        }

    # ============================================================
    #   Wind Load
    # ============================================================

    def create_wind_load(
            self,
            model=None,
            railing_height: float = 0.0,
            crash_barrier_height: float = 0.0,
            deck_thickness: float = 0.2,
            openings_in_railing: float = 0.0,
            height_for_pz: float = 10.0,
            terrain: str = "plain",
            basic_wind_speed: float = 33.0,
            girder_section: str = "plate",
            number_of_girders: int | None = None,
            c_spacing: float | None = None,
            b_width: float | None = None,
            d_depth: float | None = None,
            partial_safety_factor: float = 1.0,
    ) -> dict:
        """
        Creates wind load cases per IRC:6-2017 Cl.209.3.3–209.3.5 and
        combines them into a single WL load case.

        Load cases created
        ------------------
        ``"WL Transverse"``   : FT as a line load on the two exterior main
                                girder grid lines (z-direction, N/m).
        ``"WL Longitudinal"`` : FL = 0.25 × FT as a patch load over the full
                                deck footprint (x-direction, N/m²).
        ``"WL Uplift"``       : upward patch load Pz × G × CL over the full
                                deck footprint (−y direction, N/m²).
        ``"{lf} WL"``         : combined case (all three), registered with
                                ``partial_safety_factor``.

        Parameters
        ----------
        railing_height : float
            Height of railing in metres (KEY_RAILING_HEIGHT). Use 0 when a
            crash barrier is present instead.
        crash_barrier_height : float
            Height of crash barrier in metres. Use 0 when railing is present.
        deck_thickness : float
            Deck slab thickness in metres (KEY_DECK_THICKNESS).
        openings_in_railing : float
            Net openings in railing in metres (0 if solid).
        height_for_pz : float
            Height at which Pz is evaluated via Table 12 (metres).
        terrain : str
            ``"plain"`` or ``"obstructed"``.
        basic_wind_speed : float
            Basic wind speed V_b in m/s (from IRC:6-2017 Fig. 10).
        girder_section : str
            ``"slab"``, ``"plate"``, or ``"rolled"`` — used for CD.
        number_of_girders : int, optional
            Number of main girders. Defaults to the number of main girder
            grid lines derived from the grillage mesh.
        c_spacing : float, optional
            Centre-to-centre girder spacing in metres (KEY_GIRDER_SPACING).
            Required for plate girders (n ≥ 2) and rolled beams (n ≥ 2).
        b_width : float, optional
            Beam/box section width in metres.
        d_depth : float, optional
            Depth of windward girder in metres (KEY_MP_GIRDER_DEPTH).
        partial_safety_factor : float
            Partial safety factor applied to the combined WL load case.

        Returns
        -------
        dict
            ``{"WL_T": ..., "WL_L": ..., "WL_V": ..., "WL": ...}``
            — the four ospgrillage load-case objects.
        """
        model = model or self.model
        if model is None:
            raise ValueError("Model not created. Call create_model() first.")

        span = self.L

        # ── Resolve number of main girders from mesh when not supplied ────
        noz_all = model.Mesh_obj.noz
        # Main girder positions: skip edge-beam slots (index 0 and -1)
        main_noz = noz_all[1:-1] if self.edge_dist > 0 else noz_all
        n_main_girders = number_of_girders or len(main_noz)

        # ── 1. IRC:6-2017 Cl.209.3.3 — transverse wind force ─────────────
        ft_result = IRC6_2017.cl_209_3_3_transverse_wind_load(
            span=span,
            railing_height=railing_height,
            crash_barrier_height=crash_barrier_height,
            deck_thickness=deck_thickness,
            openings_in_railing=openings_in_railing,
            height_for_pz=height_for_pz,
            terrain=terrain,
            basic_wind_speed=basic_wind_speed,
            girder_section=girder_section,
            number_of_girders=n_main_girders,
            c_spacing=c_spacing,
            b_width=b_width,
            d_depth=d_depth,
        )

        Pz       = ft_result["Pz"]          # N/m²
        G        = ft_result["G"]
        FT_total = ft_result["FT"]          # total transverse force (N)

        # Transverse line-load intensity (N/m) on exterior girders
        FT_per_m = FT_total / span

        # Deck footprint — shared by WL_L and WL_V
        deck_geom    = self.load_manager.deck_load()
        bridge_width = self.w or self.bridge_geometry.width
        deck_area    = span * bridge_width                  # m²

        # Longitudinal patch intensity (N/m²) — Cl.209.3.4: FL = 0.25 FT
        FL_per_m2 = (0.25 * FT_total) / deck_area

        # Uplift patch intensity (N/m²) — Cl.209.3.5: FV/A = Pz × G × CL
        CL        = 0.75
        FV_per_m2 = Pz * G * CL                            # upward (applied as −y)

        print(
            f"Wind loads (IRC:6-2017): Pz={Pz:.1f} N/m²  "
            f"FT={FT_total/1000:.2f} kN  FT/m={FT_per_m/1000:.3f} kN/m  "
            f"FL={FL_per_m2:.4f} N/m²  FV={FV_per_m2:.2f} N/m²"
        )

        # ── 2. Exterior main-girder z-positions ───────────────────────────
        # Both exterior girder lines are loaded so analysis covers wind from
        # either side.
        ext_z = [main_noz[0], main_noz[-1]]

        # ── Mesh grid lines (sorted) used for tributary calculations ─────
        nox_sorted = sorted(model.Mesh_obj.nox)   # x grid lines
        noz_sorted = sorted(model.Mesh_obj.noz)   # z grid lines
        node_spec  = model.Mesh_obj.node_spec      # {tag: {"coordinate": [x,y,z]}}

        def _trib_1d(positions: list, value: float) -> float:
            """Tributary half-interval for `value` inside sorted `positions`."""
            idx = min(range(len(positions)), key=lambda i: abs(positions[i] - value))
            left  = (positions[idx] - positions[idx - 1]) / 2 if idx > 0                   else 0.0
            right = (positions[idx + 1] - positions[idx]) / 2 if idx < len(positions) - 1  else 0.0
            return left + right

        TOL = 1e-3  # coordinate matching tolerance (m)

        # ── 3. WL Transverse — nodal Fz on exterior girder nodes ─────────
        # ospgrillage's p parameter is y-direction only; horizontal wind
        # must be applied as nodal forces (Fz for transverse, IRC:6 Cl.209.3.3).
        WL_T = og.create_load_case(name="WL Transverse")
        for z_target in ext_z:
            for tag, spec in node_spec.items():
                coord = spec["coordinate"]
                if abs(coord[2] - z_target) > TOL:
                    continue
                trib_x = _trib_1d(nox_sorted, coord[0])
                Fz = FT_per_m * trib_x   # N (force = intensity × tributary length)
                WL_T.add_load(og.create_load(
                    loadtype="nodal", node_tag=tag,
                    Fx=0, Fy=0, Fz=Fz, Mx=0, My=0, Mz=0,
                ))
        model.add_load_case(WL_T)
        self.wind_transverse_load_case = WL_T

        # ── 4. WL Longitudinal — nodal Fx on all deck nodes ──────────────
        # FL = 0.25 FT distributed over full deck as a horizontal x-direction
        # load (IRC:6 Cl.209.3.4).
        WL_L = og.create_load_case(name="WL Longitudinal")
        for tag, spec in node_spec.items():
            coord = spec["coordinate"]
            trib_area = _trib_1d(nox_sorted, coord[0]) * _trib_1d(noz_sorted, coord[2])
            Fx = FL_per_m2 * trib_area   # N (force = intensity × tributary area)
            WL_L.add_load(og.create_load(
                loadtype="nodal", node_tag=tag,
                Fx=Fx, Fy=0, Fz=0, Mx=0, My=0, Mz=0,
            ))
        model.add_load_case(WL_L)
        self.wind_longitudinal_load_case = WL_L

        # ── 5. WL Uplift — nodal Fy (upward, -y) on every deck node ─────────
        # ospgrillage patch loads only cover nodes strictly inside the boundary;
        # edge nodes may be missed. Nodal loads guarantee full coverage.
        # Fy is negative (upward) per IRC:6 Cl.209.3.5: FV/A = Pz × G × CL.
        WL_V = og.create_load_case(name="WL Uplift")
        for tag, spec in node_spec.items():
            coord = spec["coordinate"]
            trib_area = _trib_1d(nox_sorted, coord[0]) * _trib_1d(noz_sorted, coord[2])
            Fy = -FV_per_m2 * trib_area   # N, negative = upward
            WL_V.add_load(og.create_load(
                loadtype="nodal", node_tag=tag,
                Fx=0, Fy=Fy, Fz=0, Mx=0, My=0, Mz=0,
            ))
        model.add_load_case(WL_V)
        self.wind_uplift_load_case = WL_V

        # ── 6. WL Combined ────────────────────────────────────────────────
        WL = og.create_load_case(name=f"{partial_safety_factor} WL")
        for sub_lc in (WL_T, WL_L, WL_V):
            for entry in sub_lc.load_groups:
                WL.add_load(entry["load"])
        model.add_load_case(WL, load_factor=partial_safety_factor)
        self.wind_load_case = WL

        return {"WL_T": WL_T, "WL_L": WL_L, "WL_V": WL_V, "WL": WL}

    # ============================================================
    #   Dead Load Combination
    # ============================================================

    def create_dead_load_combination(self, model=None, partial_safety_factor=1.0):
        """
        Creates a single ``"DL"`` load case by adding all individual dead-load
        sub-case loads into it.

        Must be called after all individual dead-load methods — and
        ``create_sidl_combination()`` — have been invoked. The superimposed
        dead loads (crash barrier, railing, median) enter via the ``SIDL``
        combination rather than as individual sub-cases, so SIDL must be built
        first. Sub-cases that were skipped (returned ``None``) are automatically
        excluded.
        """
        model = model or self.model
        if model is None:
            raise ValueError("Model is not available. Create model before adding loads.")

        _DL_ATTRS = [
            "self_weight_load_case",
            "deck_load_case",
            "footpath_load_case",
            "sidl_combination",
        ]

        DL_combined = og.create_load_case(name=f"{partial_safety_factor} DL")
        added = False

        for attr in _DL_ATTRS:
            lc = getattr(self, attr, None)
            if lc is not None:
                for entry in lc.load_groups:
                    DL_combined.add_load(entry["load"])
                added = True

        if not added:
            warnings.warn(
                "create_dead_load_combination: no dead-load sub-cases found. "
                "Call the individual dead-load creation methods first."
            )
            return None

        model.add_load_case(DL_combined, load_factor=partial_safety_factor)
        self.dead_load_combination = DL_combined
        return DL_combined

    # ============================================================
    #   SIDL (Superimposed Dead Load) Combination
    # ============================================================

    def create_sidl_combination(self, model=None, partial_safety_factor=1.0):
        """
        Creates a single ``"SIDL"`` load case by adding the superimposed
        dead-load sub-case loads into it.

        SIDL (Superimposed Dead Load) groups the non-structural permanent loads
        carried on the deck — crash barrier, railing and median — as distinct
        from the structural dead load (self weight, deck slab, footpath).

        Must be called after the relevant individual dead-load methods have been
        invoked. Sub-cases that were skipped (returned ``None``) are
        automatically excluded.
        """
        model = model or self.model
        if model is None:
            raise ValueError("Model is not available. Create model before adding loads.")

        _SIDL_ATTRS = [
            "crash_barrier_load_case",
            "railing_load_case",
            "median_load_case",
        ]

        SIDL_combined = og.create_load_case(name=f"{partial_safety_factor} SIDL")
        added = False

        for attr in _SIDL_ATTRS:
            lc = getattr(self, attr, None)
            if lc is not None:
                for entry in lc.load_groups:
                    SIDL_combined.add_load(entry["load"])
                added = True

        if not added:
            warnings.warn(
                "create_sidl_combination: no SIDL sub-cases found. "
                "Call the crash barrier / railing / median load creation methods first."
            )
            return None

        model.add_load_case(SIDL_combined, load_factor=partial_safety_factor)
        self.sidl_combination = SIDL_combined
        return SIDL_combined

    # ============================================================
    #   Live Load
    # ============================================================

    def vehicle_lane_coordinates(self):
        """
        Calculates vehicle-to-coordinate mappings for all combinations
        as per IRC:6-2017 Table 6 and Table 6A.

        Returns vehicle placement for each case where:
        - ClassA occupies 1 lane
        - Class70R occupies 2 lanes

        z -> transverse direction
        x -> longitudinal direction

        Parameters
        ----------
        carriageway_width : float, optional
            Carriageway width in metres. If omitted, reads from self.layout.

        Returns
        -------
        list of dict
            Each dict represents a vehicle combination case with structure:
            {
                'case_num': int,
                'combinations': {
                    'ClassA': [[x_coord, z_coord], ...],
                    'Class70R': [[x_coord, z_coord], ...]
                }
            }
        """
        x_coord = 0.0  # Assuming vehicles start at the beginning of the bridge (x=0)
        layout = self.layout

        # Get lane coordinates
        lane_coords = []  # [(x, z), (x, z), ...]
        carriageway_width = None

        # ---------- Single carriageway ----------
        if layout.has_component("carriageway"):
            cw = layout.get_component("carriageway")
            carriageway_width = cw.width

            n_lanes = IRC6_2017.table_6(cw.width)
            lane_width = cw.width / n_lanes

            for i in range(n_lanes):
                z = cw.z_start + (i + 0.5) * lane_width
                lane_coords.append((x_coord, z))

        # ---------- Split carriageway (with median) ----------
        else:
            cw_left_width = 0.0
            cw_right_width = 0.0
            if layout.has_component("carriageway_left"):
                cw_left = layout.get_component("carriageway_left")
                cw_left_width = cw_left.width

                n_lanes = IRC6_2017.table_6(cw_left.width)
                lane_width = cw_left.width / n_lanes

                for i in range(n_lanes):
                    z = cw_left.z_start + (i + 0.5) * lane_width
                    lane_coords.append((x_coord, z))

            if layout.has_component("carriageway_right"):
                cw_right = layout.get_component("carriageway_right")
                cw_right_width = cw_right.width

                n_lanes = IRC6_2017.table_6(cw_right.width)
                lane_width = cw_right.width / n_lanes

                for i in range(n_lanes):
                    z = cw_right.z_start + (i + 0.5) * lane_width
                    lane_coords.append((x_coord, z))

            carriageway_width = cw_left_width + cw_right_width

        if carriageway_width is None:
            raise ValueError("carriageway_width must be provided or derivable from layout")

        # Get vehicle combinations from Table 6A
        table_6a_result = IRC6_2017.table_6A(carriageway_width)
        vehicle_combinations = table_6a_result.get("vehicle_combinations", [])

        # Map each combination to coordinates
        result_cases = []

        for case_num, combo in enumerate(vehicle_combinations, start=1):
            case_data = {
                'case_num': case_num,
                'combinations': {}
            }

            lane_index = 0

            # Process ClassA vehicles (each occupies 1 lane)
            if 'ClassA' in combo:
                n_a = combo['ClassA']
                class_a_coords = []
                for _ in range(n_a):
                    if lane_index < len(lane_coords):
                        class_a_coords.append(list(lane_coords[lane_index]))
                        lane_index += 1
                if class_a_coords:
                    case_data['combinations']['ClassA'] = class_a_coords

            # Process Class70R vehicles (each occupies 2 lanes)
            if 'Class70R' in combo:
                n_70r = combo['Class70R']
                class_70r_coords = []
                for _ in range(n_70r):
                    if lane_index + 1 < len(lane_coords):
                        # Class70R spans 2 lanes, take center of the two lanes
                        z1 = lane_coords[lane_index][1]
                        z2 = lane_coords[lane_index + 1][1]
                        z_center = (z1 + z2) / 2
                        class_70r_coords.append([lane_coords[lane_index][0], z_center])
                        lane_index += 2
                if class_70r_coords:
                    case_data['combinations']['Class70R'] = class_70r_coords

            result_cases.append(case_data)

        # print(f"Vehicle lane coordinate cases: {result_cases}")
        return result_cases

    def create_vehicle_load_cases(self, model=None):
        """
        Creates vehicle load cases based on vehicle_lane_coordinates().
        Each vehicle in each case gets its own load case.

        Naming format:
            Case{n} ClassA L1
            Case{n} Class70R L1
        """

        model = model or self.model
        if model is None:
            raise ValueError("Model is not available. Create model first.")

        span = self.L
        vehicle_cases = self.vehicle_lane_coordinates()

        all_vehicle_load_cases = []

        for case in vehicle_cases:

            case_num = case["case_num"]
            combinations = case["combinations"]

            # One load case for all vehicles in this case
            vehicle_summary = " + ".join(
                f"{len(coord_list)}x{vehicle_type}"
                for vehicle_type, coord_list in combinations.items()
            )
            lc = og.create_load_case(name=f"Case{case_num} {vehicle_summary}")

            for vehicle_type, coord_list in combinations.items():
                for lane_index, (x_coord, z_coord) in enumerate(coord_list, start=1):
                    vehicle_generator = og.create_load_model(
                        model_type=vehicle_type.upper()
                    )
                    vehicle = vehicle_generator.create()
                    vehicle.set_global_coord(og.Point(x_coord, 0.0, z_coord))
                    lc.add_load(vehicle)

            model.add_load_case(lc)
            all_vehicle_load_cases.append(lc)

        self.vehicle_load_cases_list = all_vehicle_load_cases

        return all_vehicle_load_cases

    def add_vehicle_load_cases_from_combinations(self, model=None):
        """
        Create vehicle load cases using coordinates from vehicle_lane_coordinates().

        - Creates empty moving load list
        - Uses global coordinates from vehicle combinations
        - Applies lane factors (alf)
        - Applies dynamic load allowance (dla)
        """

        model = model or self.model
        if model is None:
            raise ValueError("Model not created yet.")

        vehicle_cases = self.vehicle_lane_coordinates()

        # IRC 6:2017 Cl.204.4 Table 6A — multi-lane live-load reduction factors (keyfile.LANE_REDUCTION_FACTORS).
        alf = list(LANE_REDUCTION_FACTORS)
        # IRC 6:2017 Cl.208.3 — dynamic load allowance computed from actual span.
        dla = 1.0 + IRC6_2017.cl_208_3_impact_factor(self.L)
        # -------------------------------------------------
        # Reset stores
        # -------------------------------------------------
        self.vehicle_load_cases_list = []
        self.vehicle_moving_loads_by_case = {}
        self.vehicle_type_map = {}

        for case in vehicle_cases:

            case_num = case["case_num"]
            combinations = case["combinations"]

            # One load case for all vehicles in this case
            vehicle_summary = " + ".join(
                f"{len(coord_list)}x{vehicle_type}"
                for vehicle_type, coord_list in combinations.items()
            )
            lc = og.create_load_case(name=f"Case{case_num} {vehicle_summary}")
            self.vehicle_moving_loads_by_case[case_num] = []

            for vehicle_type, coord_list in combinations.items():
                for i, (x_coord, z_coord) in enumerate(coord_list):

                    # Lane factor resets per vehicle type (alf indexed within coord_list)
                    lane_factor = alf[i] if alf and i < len(alf) else 1.0

                    vehicle_generator = og.create_load_model(
                        model_type=vehicle_type.upper()
                    )
                    vehicle = vehicle_generator.create()
                    vehicle.set_global_coord(og.Point(x_coord, 0.0, z_coord))

                    lc.add_load(load=vehicle, load_factor=lane_factor)

                    self.vehicle_moving_loads_by_case[case_num].append(vehicle)
                    self.vehicle_type_map[id(vehicle)] = vehicle_type

            model.add_load_case(lc, load_factor=dla)
            self.vehicle_load_cases_list.append(lc)

        # Flat list kept for backward-compat guard checks
        self.vehicle_moving_loads = [
            v for vs in self.vehicle_moving_loads_by_case.values() for v in vs
        ]

        return self.vehicle_load_cases_list

    @staticmethod
    def _vehicle_length(vehicle_type: str) -> float:
        """
        Return the full axle-span length (m) for a vehicle type by reading the
        last axle position from the IRC6_2017 local geometry.

        Class70R last axle ≈ 15.12 m, ClassA last axle ≈ 20.30 m.
        Falls back to 25.0 m for unknown types.
        """
        try:
            if vehicle_type == 'Class70R':
                data = IRC6_2017.cl_204_1_Class70R_vehicle_wheel()
            elif vehicle_type == 'ClassA':
                data = IRC6_2017.cl_204_1_ClassA_vehicle()
            elif vehicle_type == 'Fatigue':
                # IRC:6-2017 Cl.204.6 fatigue truck: axles at 0, 4.5, 5.9 m
                # (matches ospgrillage LoadModel.create_fatigue_vehicle()).
                return FATIGUE_VEHICLE_LENGTH
            else:
                return 25.0
            return float(max(data['x']))
        except Exception:
            return 25.0

    def create_moving_vehicle_load_cases(
            self,
            model=None,
            span=None,
    ):
        """
        Creates moving load cases corresponding to previously created static
        vehicle load cases.

        The traversal path for each case is computed from the IRC:6 vehicle
        geometry:  start = -vehicle_length, end = span + vehicle_length
        so the vehicle fully enters and exits the bridge.  Different cases
        may have different vehicle types and therefore different path extents.
        """

        model = model or self.model
        if model is None:
            raise ValueError("Model not created yet.")

        if not getattr(self, "vehicle_moving_loads_by_case", None):
            raise ValueError("No vehicle loads found. Call add_vehicle_load_cases_from_combinations() first.")

        span = span or self.L

        # -------------------------------------------------
        # One moving load case per IRC:6 case
        # -------------------------------------------------
        self.moving_load_cases_list = []

        for case_num, vehicles in self.vehicle_moving_loads_by_case.items():
            # Compute the longest vehicle length in this case
            max_len = max(
                (self._vehicle_length(self.vehicle_type_map.get(id(v), ''))
                 for v in vehicles),
                default=25.0,
            )

            start = og.create_point(x=-max_len, y=0, z=0)
            end = og.Point(span + max_len, 0, 0)
            moving_path = og.create_moving_path(start_point=start, end_point=end)

            moving_name = f"Moving Case{case_num}"
            moving_load = og.create_moving_load(name=moving_name)
            moving_load.set_path(moving_path)

            for vehicle in vehicles:
                moving_load.add_load(vehicle)

            model.add_load_case(moving_load)
            self.moving_load_cases_list.append(moving_load)

        return self.moving_load_cases_list

    # ------------------------------------------------------------------
    #   Fatigue vehicle (IRC:6-2017 Cl.204.6)
    # ------------------------------------------------------------------

    def carriageway_center_coordinates(self):
        """
        Return the transverse (z) centreline of every carriageway on the deck.

        The cross-section layout already stores each component's extents, so the
        centre comes straight from ``SectionComponent.center`` — no separate
        derivation is needed here.  ``vehicle_lane_coordinates()`` computes lane
        centres (``z_start + (i + 0.5) * lane_width``); this is the carriageway
        centre, which is what the fatigue truck is placed on.

        Returns
        -------
        list of tuple
            ``[(component_name, z_center), ...]`` — one entry for a single
            carriageway, two entries (left, right) for a split carriageway
            with a median.

        Raises
        ------
        ValueError
            If the layout contains no carriageway component.
        """
        layout = self.layout
        centers = []

        # ---------- Single carriageway ----------
        if layout.has_component("carriageway"):
            cw = layout.get_component("carriageway")
            centers.append(("carriageway", cw.center))

        # ---------- Split carriageway (with median) ----------
        else:
            for name in ("carriageway_left", "carriageway_right"):
                if layout.has_component(name):
                    centers.append((name, layout.get_component(name).center))

        if not centers:
            raise ValueError("No carriageway component found in the deck layout")

        return centers

    def add_fatigue_vehicle_load_case(self, model=None, apply_dla: bool = True):
        """
        Create the static fatigue-truck load case, with one truck straddling the
        centreline of each carriageway.

        The fatigue truck is the IRC:6-2017 Cl.204.6 3-axle vehicle built by
        ``ospgrillage``'s ``LoadModel(model_type="FATIGUE")``.  When a median
        splits the deck there is one truck per carriageway, but they belong to a
        single load case named "Fatigue" — the trucks are checked side by side,
        not as independent load cases.  Unlike the Table 6A live-load cases no
        multi-lane reduction factor (alf) applies; only the dynamic load
        allowance is registered on the load case.

        Parameters
        ----------
        model : Grillage, optional
            Target model; defaults to ``self.model``.
        apply_dla : bool
            Apply the Cl.208.3 dynamic load allowance as the load-case factor
            (default True).

        Returns
        -------
        list
            A single-element list holding the created static fatigue load case.
        """
        model = model or self.model
        if model is None:
            raise ValueError("Model not created yet.")

        # IRC 6:2017 Cl.208.3 — dynamic load allowance computed from actual span.
        dla = 1.0 + IRC6_2017.cl_208_3_impact_factor(self.L) if apply_dla else 1.0

        self.fatigue_load_cases_list = []
        self.fatigue_vehicles_by_case = {}

        centers = self.carriageway_center_coordinates()

        # One load case for the whole deck. The name deliberately does not start
        # with "case" so the governing-LL detection in
        # create_governing_ll_load_case() does not pick it up.
        lc_name = "Fatigue"
        lc = og.create_load_case(name=lc_name)
        vehicles = []

        for _cw_name, z_center in centers:
            vehicle_generator = og.create_load_model(model_type="FATIGUE")
            vehicle = vehicle_generator.create()
            vehicle.set_global_coord(og.Point(0.0, 0.0, z_center))

            lc.add_load(load=vehicle)

            vehicles.append(vehicle)
            self.vehicle_type_map[id(vehicle)] = "Fatigue"

        model.add_load_case(lc, load_factor=dla)

        self.fatigue_load_cases_list.append(lc)
        self.fatigue_vehicles_by_case[lc_name] = vehicles

        return self.fatigue_load_cases_list

    def create_moving_fatigue_load_cases(self, model=None, span=None):
        """
        Create the moving fatigue load case corresponding to the static fatigue
        case created by ``add_fatigue_vehicle_load_case()``.

        All fatigue trucks share one moving path and therefore advance together:
        start = ``-vehicle_length``, end = ``span + vehicle_length``, so they
        fully enter and exit the bridge.  Each truck keeps its own transverse
        (z) offset from its global coordinate, so a two-carriageway deck is
        loaded on both carriageways simultaneously at every path increment.

        Parameters
        ----------
        model : Grillage, optional
            Target model; defaults to ``self.model``.
        span : float, optional
            Override the bridge span (m); defaults to ``self.L``.

        Returns
        -------
        list
            A single-element list holding the created moving fatigue load case.
        """
        model = model or self.model
        if model is None:
            raise ValueError("Model not created yet.")

        if not getattr(self, "fatigue_vehicles_by_case", None):
            raise ValueError(
                "No fatigue vehicles found. Call add_fatigue_vehicle_load_case() first."
            )

        span = span or self.L
        veh_len = self._vehicle_length("Fatigue")

        start = og.create_point(x=-veh_len, y=0, z=0)
        end = og.Point(span + veh_len, 0, 0)

        self.moving_fatigue_load_cases_list = []

        for lc_name, vehicles in self.fatigue_vehicles_by_case.items():
            moving_path = og.create_moving_path(start_point=start, end_point=end)

            moving_load = og.create_moving_load(name=f"Moving {lc_name}")
            moving_load.set_path(moving_path)

            for vehicle in vehicles:
                moving_load.add_load(vehicle)

            model.add_load_case(moving_load)
            self.moving_fatigue_load_cases_list.append(moving_load)

        return self.moving_fatigue_load_cases_list

    # ------------------------------------------------------------------
    #   Braking load (IRC:6-2017 Cl.211)
    # ------------------------------------------------------------------

    def create_braking_load_case(self, model=None, eccentricity: float | None = None):
        """
        Creates the single ``"Braking Load"`` load case for the governing
        live-load case.

        The braking force comes from the vehicles standing in the case that
        ``create_governing_ll_load_case()`` picked as governing — the same case
        that became ``"1.0 LL"``. Of the vehicle types in that case the heaviest
        single vehicle governs (Class70R at 981 kN always beats ClassA at
        543 kN when both appear), and

            ``Fx = 0.20 × W``          (Cl.211.2 — 20% of the vertical load)
            ``Mz = Fx × eccentricity`` (Cl.211.3 — Fx acts 1.2 m above the deck)

        ``Fx`` is longitudinal (+x) and ``Mz`` is the couple it produces about
        the transverse (z) axis by acting at height ``eccentricity`` above the
        deck surface, so the pair reproduces the overturning effect that adds to
        girder major-axis bending.

        Both are shared equally between the nodes on the main girder grid lines
        (the overhang edge-beam lines are excluded), so the braking force enters
        the model where it is actually carried down to the bearings. The summed
        nodal ``Fx`` equals the total braking force exactly.

        The case is registered **unfactored** — no partial safety factor is
        applied here, matching the way ``"1.0 LL"`` carries the raw governing
        vehicle loads and leaves γ to the combination builders.

        Must be called after ``create_governing_ll_load_case()`` so that
        ``self.governing_ll_name`` identifies which case to derive from. The
        case is solved selectively on creation, the same way the LL case is,
        because ``_reanalyze_with_dedup()`` only re-solves the combinations.

        Parameters
        ----------
        model : Grillage, optional
            Target model; defaults to ``self.model``.
        eccentricity : float, optional
            Height of the braking force above the top of the deck (m). Defaults
            to ``IRC6_2017.cl_211_3_braking_force_location()`` (1.2 m).

        Returns
        -------
        LoadCase or None
            The created ``"Braking Load"`` load case, or ``None`` when no
            governing live-load case is available to derive it from.
        """
        model = model or self.model
        if model is None:
            raise ValueError("Model not created yet.")

        if eccentricity is None:
            eccentricity = IRC6_2017.cl_211_3_braking_force_location()["height_m"]

        self.braking_load_case = None

        # -------------------------------------------------
        # Governing live-load case → its vehicles → heaviest one
        # -------------------------------------------------
        case_num = self._governing_case_num()
        if case_num is None:
            warnings.warn(
                "create_braking_load_case: no governing live-load case available "
                "— call create_governing_ll_load_case() first; skipping the braking load."
            )
            return None

        vehicle_types = {
            self.vehicle_type_map.get(id(v), '')
            for v in self.vehicle_moving_loads_by_case.get(case_num, [])
        }
        vehicle_types.discard('')

        if not vehicle_types:
            warnings.warn(
                f"create_braking_load_case: governing Case{case_num} carries no "
                "identifiable vehicles; skipping the braking load."
            )
            return None

        governing_type = max(vehicle_types, key=self._vehicle_total_weight_kN)
        W_kN = self._vehicle_total_weight_kN(governing_type)

        if W_kN <= 0:
            warnings.warn(
                f"create_braking_load_case: no weight available for vehicle type "
                f"'{governing_type}'; skipping the braking load."
            )
            return None

        Fx_total = 0.20 * W_kN * kN  # N

        # -------------------------------------------------
        # Main girder nodes
        # -------------------------------------------------
        # Transverse positions of the main girders — the two outermost grid
        # lines are overhang edge beams when an overhang exists, so drop them.
        noz_sorted = sorted(model.Mesh_obj.noz)
        girder_z = noz_sorted[1:-1] if self.edge_dist > 0 else noz_sorted

        TOL = 1e-3  # coordinate matching tolerance (m)
        girder_tags = [
            tag for tag, spec in model.Mesh_obj.node_spec.items()
            if any(abs(spec["coordinate"][2] - z) <= TOL for z in girder_z)
        ]
        if not girder_tags:
            raise ValueError(
                "No main girder nodes found; cannot apply the braking force."
            )

        Fx = Fx_total / len(girder_tags)  # N — equal share per girder node

        BL = og.create_load_case(name="Braking Load")
        for tag in girder_tags:
            BL.add_load(og.create_load(
                loadtype="nodal", node_tag=tag,
                Fx=Fx, Fy=0, Fz=0,
                Mx=0, My=0, Mz=Fx * eccentricity,  # N·m
            ))

        # Unfactored: no load_factor argument.
        model.add_load_case(BL)
        self.braking_load_case = BL

        print(
            f"Braking Load from governing {self.governing_ll_name}: "
            f"vehicle {governing_type} W={W_kN:.2f} kN  "
            f"Fx={Fx_total / 1000:.2f} kN  "
            f"Mz={Fx_total * eccentricity / 1000:.2f} kNm "
            f"(e={eccentricity:.2f} m) over {len(girder_tags)} girder nodes"
        )

        # Solve only the new case — see create_governing_ll_load_case() for why
        # a bare analyze() here would be wasted work.
        model.analyze(load_case=[BL.name])

        return BL

    def create_governing_ll_load_case(self, dataset, model=None, partial_safety_factor: float = 1.0):
        """
        Identify the governing static vehicle load case (max |Mz_i|), create a
        single ``"{partial_safety_factor} LL"`` load case from it, register it with the
        given partial_safety_factor, and solve just that case.

        Must be called after analyze() so the dataset is available.

        Parameters
        ----------
        dataset : xarray.Dataset
            Results from the initial analysis (returned by analyze()).
        partial_safety_factor : float
            ULS partial safety factor applied to the governing LL case (default 1.0).

        Returns
        -------
        None
            The LL case is solved selectively; the combined dataset is built once
            in ``_reanalyze_with_dedup()`` after all combinations are registered.
        """
        model = model or self.model
        if model is None:
            raise ValueError("Model is not available.")

        all_lcs = list(dataset.coords["Loadcase"].values)
        static_lcs = [lc for lc in all_lcs if str(lc).lower().startswith("case")]

        if not static_lcs:
            warnings.warn("No vehicle static load cases found; skipping LL creation.")
            self.ll_load_case = None
            return dataset

        # Collect longitudinal girder elements only (exclude transverse slabs and edge beams)
        girder_elements = []
        for member_type in ("interior_main_beam", "exterior_main_beam_1", "exterior_main_beam_2"):
            try:
                girder_elements.extend(model.get_element(member=member_type, options="elements"))
            except Exception:
                pass
        girder_elements = list(set(girder_elements))

        # Find governing LC via ospgrillage's create_envelope (replaces the
        # manual per-load-case max loop). Restrict the dataset to the static
        # vehicle cases (and girder elements), then envelope |Mz_i| across the
        # Loadcase dimension:
        #   value_mode -> max |Mz_i| per element,
        #   query_mode -> the load-case label producing that max per element.
        # The single governing case is the one at the element carrying the
        # overall largest |Mz_i|.
        sub = dataset.sel(Loadcase=static_lcs)
        if girder_elements:
            sub = sub.sel(Element=girder_elements)

        # Envelope on absolute moment so hogging and sagging are compared on
        # magnitude (create_envelope only does signed max/min).
        abs_ds = sub.copy()
        abs_ds["forces"] = abs(sub["forces"])

        try:
            env_val = og.create_envelope(
                ds=abs_ds, load_effect="Mz_i", array="forces",
                extrema="max", value_mode=True,
            ).get().sel(Component="Mz_i")
            env_lc = og.create_envelope(
                ds=abs_ds, load_effect="Mz_i", array="forces",
                extrema="max", query_mode=True,
            ).get().sel(Component="Mz_i")

            gov_element = env_val.idxmax("Element").item()
            governing_lc = str(env_lc.sel(Element=gov_element).values)
            governing_val = float(env_val.sel(Element=gov_element).values)
        except Exception as exc:
            warnings.warn(
                f"Envelope-based governing LL detection failed ({exc}); "
                "skipping LL creation."
            )
            self.ll_load_case = None
            return dataset

        if not governing_lc or governing_val < 0:
            warnings.warn("Could not determine governing LL case; skipping LL creation.")
            self.ll_load_case = None
            return dataset

        print(f"Governing LL: {governing_lc}  (max |Mz_i| = {governing_val / 1000:.2f} kNm)")

        # Find the matching load case object from vehicle_load_cases_list
        target_lc_obj = next(
            (lc for lc in getattr(self, "vehicle_load_cases_list", [])
             if lc.name == str(governing_lc)),
            None,
        )

        if target_lc_obj is None:
            warnings.warn(f"Load case object '{governing_lc}' not found; skipping LL creation.")
            self.ll_load_case = None
            return dataset

        # Build LL load case from the governing case's loads
        LL = og.create_load_case(name=f"{partial_safety_factor} LL")
        for entry in target_lc_obj.load_groups:
            LL.add_load(entry["load"])

        model.add_load_case(LL, load_factor=partial_safety_factor)
        self.ll_load_case = LL
        self.governing_ll_name = str(governing_lc)

        # Solve ONLY the new LL case. A bare analyze() re-solves every registered
        # case — including all ~50 increments of each moving load — and ospgrillage's
        # record store (extract_analysis -> dict.setdefault) then discards the repeated
        # results, so a full re-analysis here is pure wasted compute and allocation
        # churn. The combined dataset is materialized once, in _reanalyze_with_dedup(),
        # after the load combinations have been registered; nothing consumes it earlier.
        model.analyze(load_case=[LL.name])
        return None

    # ============================================================
    #   Result Envelope  (max / min across ALL load cases)
    # ============================================================

    #: Loadcase labels for the injected envelope pseudo load cases, one per
    #: limit state (enveloped over that limit state's combinations only).
    ENVELOPE_ULS = "Envelope ULS"
    ENVELOPE_SLS = "Envelope SLS"

    # ============================================================
    #   Dead Load + Live Load Combination
    # ============================================================

    def create_dl_ll_combination(self, model=None, dl_factor: float = 1.0, ll_factor: float = 1.0):
        """
        Creates a single ``"{dl_factor} DL + {ll_factor} LL"`` load case by
        combining the dead-load combination and the governing live-load case,
        each scaled by its own partial safety factor.

        With the defaults this produces a load case named ``"1.0 DL + 1.0 LL"``
        carrying the unfactored sum of dead and live loads.

        Must be called after ``create_dead_load_combination()`` and
        ``create_governing_ll_load_case()`` so both sub-cases exist.

        Parameters
        ----------
        dl_factor : float
            Partial safety factor applied to the dead-load loads (default 1.0).
        ll_factor : float
            Partial safety factor applied to the live-load loads (default 1.0).

        The created load case is stored on ``self.dl_ll_combination``.
        """
        model = model or self.model
        if model is None:
            raise ValueError("Model is not available. Create model before adding loads.")

        dl_lc = getattr(self, "dead_load_combination", None)
        ll_lc = getattr(self, "ll_load_case", None)

        combo = og.create_load_case(name=f"{dl_factor} DL + {ll_factor} LL")
        n = 0

        if dl_lc is not None:
            for entry in dl_lc.load_groups:
                combo.add_load(entry["load"], load_factor=float(dl_factor))
            n += len(dl_lc.load_groups)
        else:
            warnings.warn(
                "create_dl_ll_combination: dead-load combination not available — "
                "call create_dead_load_combination() first."
            )

        if ll_lc is not None:
            for entry in ll_lc.load_groups:
                combo.add_load(entry["load"], load_factor=float(ll_factor))
            n += len(ll_lc.load_groups)
        else:
            warnings.warn(
                "create_dl_ll_combination: live-load case not available — "
                "call create_governing_ll_load_case() first."
            )

        if n == 0:
            warnings.warn("create_dl_ll_combination: no loads added — skipping.")
            return None

        model.add_load_case(combo)
        self.dl_ll_combination = combo
        return combo

    def create_envelope_load_case(self, model=None, dataset=None):
        """
        Build **two** force/displacement envelopes — one over the ULS
        combinations and one over the SLS combinations — and inject them back
        into the results dataset as the pseudo load cases ``Envelope ULS`` and
        ``Envelope SLS``.

        An envelope is a post-processing result rather than a re-analyzable
        input load case. For every element/node component this records the
        **worst signed magnitude** across that limit state's combinations: of
        the across-loadcase maximum and minimum, whichever has the larger
        absolute value is kept, with its sign preserved (e.g. a cell seeing
        ``+120`` and ``-300`` records ``-300``). Because the reduction only
        collapses the ``Loadcase`` dimension, each enveloped array keeps its
        spatial axis:

            ``forces`` envelope is **element-wise**  (dims ``Element, Component``)
            ``displacements`` envelope is **node-wise** (dims ``Node, Component``)

        Membership comes from ``self.uls_combinations`` / ``self.sls_combinations``
        (the lists returned by :meth:`create_uls_combinations` /
        :meth:`create_sls_combinations`); only combinations actually present in
        the dataset are enveloped. Each reduced row is concatenated back onto the
        ``Loadcase`` dimension of a *copy* of the results dataset, so the
        envelopes show up as ``Envelope ULS`` / ``Envelope SLS`` alongside the
        real load cases in ``forces``, ``displacements``, etc. The augmented
        dataset is cached on ``self._deduplicated_results`` (this cannot be
        persisted into the OpenSees model — ``model.get_results()`` always
        rebuilds it fresh).

        The standalone enveloped DataArrays are also cached on
        ``self.result_envelopes`` as
        ``{label: {"forces": DataArray, "displacements": DataArray}}`` for
        convenient direct access.

        Must be called after the model has been analysed (and after the ULS/SLS
        combinations have been created and analysed) so a results dataset is
        available.

        Parameters
        ----------
        dataset : xarray.Dataset, optional
            Results dataset to envelope. Defaults to the deduplicated results
            cached by the analysis, falling back to ``model.get_results()``.

        Returns
        -------
        xarray.Dataset
            The augmented dataset with ``Envelope ULS`` / ``Envelope SLS`` added
            on the ``Loadcase`` dimension.
        """
        model = model or self.model
        if model is None:
            raise ValueError("Model is not available. Create and analyze the model first.")

        if dataset is None:
            dataset = getattr(self, "_deduplicated_results", None)
            if dataset is None:
                dataset = model.get_results()

        if "Loadcase" not in dataset.dims:
            warnings.warn("Results dataset has no 'Loadcase' dimension; skipping envelope.")
            return dataset

        # Idempotency: strip any previously injected envelope rows so re-running
        # envelopes the real combinations only.
        env_labels = {self.ENVELOPE_ULS, self.ENVELOPE_SLS}
        all_lcs = [str(lc) for lc in dataset.coords["Loadcase"].values]
        base_lcs = [lc for lc in all_lcs if lc not in env_labels]
        base = dataset.sel(Loadcase=base_lcs) if len(base_lcs) < len(all_lcs) else dataset

        # Split Loadcase-bearing data vars (forces, displacements, velocity,
        # acceleration) from static ones (e.g. ele_nodes) so they can be
        # concatenated and merged back cleanly.
        loadcase_vars = [v for v in base.data_vars if "Loadcase" in base[v].dims]
        static_vars = [v for v in base.data_vars if "Loadcase" not in base[v].dims]

        # Group the real load cases by limit state from the registered
        # combination lists, keeping only those present in the dataset.
        base_set = set(base_lcs)
        uls_names = [lc.name for lc in (getattr(self, "uls_combinations", None) or [])]
        sls_names = [lc.name for lc in (getattr(self, "sls_combinations", None) or [])]
        groups = {
            self.ENVELOPE_ULS: [n for n in uls_names if n in base_set],
            self.ENVELOPE_SLS: [n for n in sls_names if n in base_set],
        }

        def _envelope(sub):
            """Worst-signed-magnitude reduction of ``sub`` over Loadcase.

            Takes ospgrillage's across-loadcase max and min (create_envelope's
            load_effect is required but does NOT filter — get() reduces the whole
            array along Loadcase) and keeps whichever has the larger absolute
            value, preserving sign.
            """
            out = {}
            for var_name in loadcase_vars:
                da_max = og.create_envelope(
                    ds=sub, load_effect=var_name, array=var_name,
                    extrema="max", value_mode=True,
                ).get()
                da_min = og.create_envelope(
                    ds=sub, load_effect=var_name, array=var_name,
                    extrema="min", value_mode=True,
                ).get()
                out[var_name] = xr.where(abs(da_max) >= abs(da_min), da_max, da_min)
            return out

        env_rows = []
        self.result_envelopes = {}
        for label, group_lcs in groups.items():
            if not group_lcs:
                warnings.warn(
                    f"No load cases found for '{label}'; skipping "
                    "(create the combinations and analyse before enveloping)."
                )
                continue
            env_arrays = _envelope(base.sel(Loadcase=group_lcs))
            env_rows.append(xr.Dataset(env_arrays).expand_dims(Loadcase=[label]))
            self.result_envelopes[label] = env_arrays

        # Concat the envelope rows onto the Loadcase axis and merge static vars.
        base_lc = base[loadcase_vars]
        combined_lc = xr.concat([base_lc, *env_rows], dim="Loadcase") if env_rows else base_lc
        combined = xr.merge([combined_lc, base[static_vars]]) if static_vars else combined_lc

        self._deduplicated_results = combined

        # Brief console summary (best-effort — never fail the pipeline on it).
        for label, group_lcs in groups.items():
            if label not in self.result_envelopes:
                continue
            try:
                arrs = self.result_envelopes[label]
                mz = arrs["forces"].sel(Component="Mz_i")
                dy = arrs["displacements"].sel(Component="y")
                print(
                    f"{label} (worst signed magnitude) over {len(group_lcs)} "
                    f"combinations: peak |Mz_i|={float(abs(mz).max()) / 1000:.2f} kNm  "
                    f"peak |dy|={float(abs(dy).max()) * 1000:.2f} mm"
                )
            except Exception:
                pass

        return combined

    # ============================================================
    #   ULS Load Combinations  (IRC:6-2017 Table B.2)
    # ============================================================

    def create_uls_combinations(self, model=None, included_keys=None):
        """
        Creates the selected ULS load combinations per IRC:6-2017 Table B.2.

        Permanent loads (dead_load, surfacing) are applied in **both** directions
        — adding and relieving — for every combination type so that the full
        force envelope can be extracted in post-processing.

        Combinations produced
        ----------------------
        BASIC_1  … BASIC_6  (6 total)
            2 permanent directions  ×  3 variable loads as leading
            Adding   (DL=1.35, Surf=1.75): BASIC_1 LL-lead, BASIC_2 WL-lead, BASIC_3 TL-lead
            Relieving (DL=1.00, Surf=1.00): BASIC_4 LL-lead, BASIC_5 WL-lead, BASIC_6 TL-lead

        ACCIDENTAL_1  … ACCIDENTAL_3  (3 total)
            3 accidental events  ×  1 valid leading
            (only live_load leading is valid; wind/thermal leading = None → skipped).
            DL and Surf are γ=1.0 for both adding and relieving in the accidental
            column, so the two directions are numerically identical — only one is
            generated per event (no direction loop).
            Note: accidental event load cases have no model load case; silently omitted.

        SEISMIC_1  … SEISMIC_4  (4 total)
            2 permanent directions  ×  2 conditions (service γ=1.5, construction γ=0.75)
            Adding    (DL=1.35, Surf=1.75): SEISMIC_1 service, SEISMIC_2 construction
            Relieving  (DL=1.00, Surf=1.00): SEISMIC_3 service, SEISMIC_4 construction
            Wind load accompanying = None for seismic → omitted.
            EL term = ``seismic_load_case``, the vertical-dominant IRC 218.3
            combination (c) set by ``create_seismic_load_cases()``.

        Total: 13 ULS combinations when all are selected.

        Parameters
        ----------
        included_keys : set[str] | None
            Set of canonical combination keys (see
            ``IRC6_2017.ULS_COMBINATION_KEYS``) to generate. ``None`` (default)
            generates every combination; an empty set generates none. Each combo
            is registered only when its key is in this set, letting the user
            choose which combinations are built via the load-combination UI.

        Notes
        -----
        - Loads with factor = None or 0 are silently skipped.
        - Missing sub-case load cases raise a warning (except accidental event types).
        - Call ``analyze()`` again after this method to include the combinations.
        """
        model = model or self.model
        if model is None:
            raise ValueError("Model is not available. Create model before adding loads.")

        γ = IRC6_2017.table_B2

        LC_ATTR_MAP = {
            'dead_load':    'dead_load_combination',
            'surfacing':    'wearing_course_load',
            'live_load':    'll_load_case',
            'wind_load':    'wind_load_case',
            'thermal_load': 'temperature_load_case',
            'seismic':      'seismic_load_case',
        }
        # Short load symbols used to spell out the factored combination in the
        # load-case name, e.g. "BASIC_1: 1.35DL + 1.75DW + 1.5LL".
        LOAD_ABBR = {
            'dead_load':    'DL',
            'surfacing':    'DW',
            'live_load':    'LL',
            'wind_load':    'WL',
            'thermal_load': 'TL',
            'seismic':      'EL',
        }
        ACCIDENTAL_LOADS = ['vehicle_collision', 'barge_impact', 'floating_bodies']
        VARIABLE_LOADS   = ['live_load', 'wind_load', 'thermal_load']
        DIRECTIONS       = ['adding', 'relieving']

        def _lc(key):
            attr = LC_ATTR_MAP.get(key)
            return getattr(self, attr, None) if attr else None

        def _copy_loads(target_lc, src_lc, factor):
            if src_lc is None or factor is None or factor == 0:
                return 0
            for entry in src_lc.load_groups:
                target_lc.add_load(entry["load"], load_factor=float(factor))
            return len(src_lc.load_groups)

        counters: dict = {}
        created: list = []

        def _register(prefix, perm_factors, var_factors, seismic_factor=None, label="", key=""):
            # Skip combinations the user has de-selected. included_keys is None
            # → generate everything (back-compat); an empty/unknown key always
            # passes so a mapping miss can never silently drop a combination.
            if included_keys is not None and key and key not in included_keys:
                return

            # Resolve which sub-cases actually contribute (mirrors _copy_loads:
            # a load is included only when its factor is non-zero and its
            # sub-case exists). Collect both the loads to copy and the factored
            # terms used to spell out the combination in its name.
            seq = counters.get(prefix, 0) + 1
            terms   = []   # display terms, e.g. "1.35DL"
            to_copy = []   # (src_lc, factor) actually added to the combo

            for key, fac in perm_factors.items():
                src = _lc(key)
                if src is None or fac is None or fac == 0:
                    continue
                terms.append(f"{fac}{LOAD_ABBR[key]}")
                to_copy.append((src, fac))

            for key, fac in var_factors.items():
                if fac is None or fac == 0:
                    continue
                src = _lc(key)
                if src is None:
                    warnings.warn(
                        f"{prefix}_{seq}: '{key}' load case not available — "
                        "create it before calling create_uls_combinations()."
                    )
                    continue
                terms.append(f"{fac}{LOAD_ABBR[key]}")
                to_copy.append((src, fac))

            if seismic_factor is not None and seismic_factor != 0:
                src = _lc('seismic')
                if src is None:
                    warnings.warn(f"{prefix}_{seq}: seismic load case not available.")
                else:
                    terms.append(f"{seismic_factor}{LOAD_ABBR['seismic']}")
                    to_copy.append((src, seismic_factor))

            if not to_copy:
                warnings.warn(f"{prefix}_{seq}: no loads added — skipping.")
                return

            counters[prefix] = seq
            lc_name  = f"{prefix}_{seq}: " + " + ".join(terms)
            combo_lc = og.create_load_case(name=lc_name)
            for src, fac in to_copy:
                _copy_loads(combo_lc, src, fac)
            model.add_load_case(combo_lc)
            created.append(combo_lc)
            print(f"  Created: {lc_name:<45s}  {label}")

        # ── BASIC (6 combos: 2 directions × 3 leading) ───────────────────────
        print("ULS Basic combinations:")
        for direction in DIRECTIONS:
            dl_f   = γ('dead_load', direction, 'basic')
            surf_f = γ('surfacing',  direction, 'basic')
            perm   = {'dead_load': dl_f, 'surfacing': surf_f}
            for leading in VARIABLE_LOADS:
                var = {
                    vl: γ(vl, 'leading' if vl == leading else 'accompanying', 'basic')
                    for vl in VARIABLE_LOADS
                }
                if var[leading] is None:
                    continue
                _register('BASIC', perm, var,
                          label=f"DL={dl_f}({direction})  Surf={surf_f}  {leading} leading",
                          key=IRC6_2017.ULS_COMBINATION_KEYS.get(('basic', leading, None, direction), ""))

        # ── ACCIDENTAL (3 combos: 3 events × 1 valid leading) ────────────────
        # In the accidental column of Table B.2 the permanent loads carry
        # γ=1.0 for BOTH adding and relieving, so the two directions are
        # numerically identical — only one is generated per accidental event
        # (3 events × 1 valid leading = 3 combinations).
        print("\nULS Accidental combinations:")
        dl_f   = γ('dead_load', 'adding', 'accidental')
        surf_f = γ('surfacing',  'adding', 'accidental')
        perm   = {'dead_load': dl_f, 'surfacing': surf_f}
        for acc in ACCIDENTAL_LOADS:
            for leading in VARIABLE_LOADS:
                var = {
                    vl: γ(vl, 'leading' if vl == leading else 'accompanying', 'accidental')
                    for vl in VARIABLE_LOADS
                }
                if var[leading] is None:
                    continue
                _register('ACCIDENTAL', perm, var,
                          label=f"DL={dl_f}  {acc}(no lc)  {leading} leading",
                          key=IRC6_2017.ULS_COMBINATION_KEYS.get(('accidental', leading, acc, 'adding'), ""))

        # ── SEISMIC (4 combos: 2 directions × 2 conditions) ──────────────────
        print("\nULS Seismic combinations:")
        var_seis = {vl: γ(vl, 'accompanying', 'seismic') for vl in VARIABLE_LOADS}
        for direction in DIRECTIONS:
            dl_f   = γ('dead_load', direction, 'seismic')
            surf_f = γ('surfacing',  direction, 'seismic')
            perm   = {'dead_load': dl_f, 'surfacing': surf_f}
            for condition in ['service', 'construction']:
                el_f = γ('seismic', condition, 'seismic')
                _register('SEISMIC', perm, var_seis, seismic_factor=el_f,
                          label=f"DL={dl_f}({direction})  EL={el_f}({condition})",
                          key=IRC6_2017.ULS_COMBINATION_KEYS.get(('seismic', condition, None, direction), ""))

        print(f"\nTotal ULS combinations created: {len(created)}")
        self.uls_combinations = created
        return created

    # ============================================================
    #   SLS Load Combinations  (IRC:6-2017 Table B.3)
    # ============================================================

    def create_sls_combinations(self, model=None, included_keys=None):
        """
        Creates the selected SLS load combinations per IRC:6-2017 Table B.3.

        Dead load is always γ=1.0 in SLS regardless of direction.  Surfacing
        carries different adding (1.2) / relieving (1.0) factors, so both
        directions are generated to capture the full envelope.

        Combinations produced
        ----------------------
        SLS_RARE_1  … SLS_RARE_6  (6 total)
            2 surfacing directions  ×  3 variable loads as leading
            Surf adding  (1.2): SLS_RARE_1 LL-lead, SLS_RARE_2 WL-lead, SLS_RARE_3 TL-lead
            Surf relieving (1.0): SLS_RARE_4 LL-lead, SLS_RARE_5 WL-lead, SLS_RARE_6 TL-lead

        SLS_FREQUENT_1  … SLS_FREQUENT_6  (6 total)
            Same structure as Rare; factors from the frequent column of Table B.3.

        SLS_QP_1, SLS_QP_2  (2 total)
            Quasi-permanent: all variable loads accompanying.
            LL=0 and WL=0 → omitted.  Only TL contributes (γ=0.5).
            SLS_QP_1: Surf adding  (1.2)   DL=1.0  TL=0.5
            SLS_QP_2: Surf relieving (1.0)  DL=1.0  TL=0.5

        Total: 14 SLS combinations when all are selected.

        Parameters
        ----------
        included_keys : set[str] | None
            Set of canonical combination keys (see
            ``IRC6_2017.SLS_COMBINATION_KEYS``) to generate. ``None`` (default)
            generates every combination; an empty set generates none. Each combo
            is registered only when its key is in this set, letting the user
            choose which combinations are built via the load-combination UI.

        Notes
        -----
        - Loads with factor = None or 0 are silently skipped.
        - Missing sub-case load cases raise a warning.
        - Call ``analyze()`` again after this method to include the combinations.
        """
        model = model or self.model
        if model is None:
            raise ValueError("Model is not available. Create model before adding loads.")

        γ = IRC6_2017.table_B3

        LC_ATTR_MAP = {
            'dead_load':    'dead_load_combination',
            'surfacing':    'wearing_course_load',
            'live_load':    'll_load_case',
            'wind_load':    'wind_load_case',
            'thermal_load': 'temperature_load_case',
        }
        # Short load symbols used to spell out the factored combination in the
        # load-case name, e.g. "SLS_RARE_1: 1.0DL + 1.2DW + 1.0LL".
        LOAD_ABBR = {
            'dead_load':    'DL',
            'surfacing':    'DW',
            'live_load':    'LL',
            'wind_load':    'WL',
            'thermal_load': 'TL',
        }
        VARIABLE_LOADS = ['live_load', 'wind_load', 'thermal_load']
        DIRECTIONS     = ['adding', 'relieving']

        def _lc(key):
            attr = LC_ATTR_MAP.get(key)
            return getattr(self, attr, None) if attr else None

        def _copy_loads(target_lc, src_lc, factor):
            if src_lc is None or factor is None or factor == 0:
                return 0
            for entry in src_lc.load_groups:
                target_lc.add_load(entry["load"], load_factor=float(factor))
            return len(src_lc.load_groups)

        counters: dict = {}
        created: list = []

        def _register(prefix, dl_f, surf_f, var_factors, label="", key=""):
            # Skip combinations the user has de-selected. included_keys is None
            # → generate everything (back-compat); an empty/unknown key always
            # passes so a mapping miss can never silently drop a combination.
            if included_keys is not None and key and key not in included_keys:
                return

            # Resolve which sub-cases actually contribute (mirrors _copy_loads:
            # a load is included only when its factor is non-zero and its
            # sub-case exists). Collect both the loads to copy and the factored
            # terms used to spell out the combination in its name.
            seq = counters.get(prefix, 0) + 1
            terms   = []   # display terms, e.g. "1.2DW"
            to_copy = []   # (src_lc, factor) actually added to the combo

            for key, fac in [('dead_load', dl_f), ('surfacing', surf_f)]:
                src = _lc(key)
                if src is None or fac is None or fac == 0:
                    continue
                terms.append(f"{fac}{LOAD_ABBR[key]}")
                to_copy.append((src, fac))

            for key, fac in var_factors.items():
                if fac is None or fac == 0:
                    continue
                src = _lc(key)
                if src is None:
                    warnings.warn(
                        f"{prefix}_{seq}: '{key}' load case not available — "
                        "create it before calling create_sls_combinations()."
                    )
                    continue
                terms.append(f"{fac}{LOAD_ABBR[key]}")
                to_copy.append((src, fac))

            if not to_copy:
                warnings.warn(f"{prefix}_{seq}: no loads added — skipping.")
                return

            counters[prefix] = seq
            lc_name  = f"{prefix}_{seq}: " + " + ".join(terms)
            combo_lc = og.create_load_case(name=lc_name)
            for src, fac in to_copy:
                _copy_loads(combo_lc, src, fac)
            model.add_load_case(combo_lc)
            created.append(combo_lc)
            print(f"  Created: {lc_name:<45s}  {label}")

        # ── RARE & FREQUENT (6 + 6 combos) ───────────────────────────────────
        for combo_type, prefix in [('rare', 'SLS_RARE'), ('frequent', 'SLS_FREQUENT')]:
            print(f"SLS {combo_type.capitalize()} combinations:")
            dl_f = γ('dead_load', None, combo_type)       # always 1.0 in SLS
            for direction in DIRECTIONS:
                surf_f = γ('surfacing', direction, combo_type)
                for leading in VARIABLE_LOADS:
                    var = {
                        vl: γ(vl, 'leading' if vl == leading else 'accompanying', combo_type)
                        for vl in VARIABLE_LOADS
                    }
                    if var[leading] is None:
                        continue
                    _register(prefix, dl_f, surf_f, var,
                              label=f"DL={dl_f}  Surf={surf_f}({direction})  {leading} leading",
                              key=IRC6_2017.SLS_COMBINATION_KEYS.get((combo_type, leading, direction), ""))
            print()

        # ── QUASI-PERMANENT (2 combos: adding & relieving surfacing) ─────────
        print("SLS Quasi-permanent combinations:")
        dl_f   = γ('dead_load', None, 'quasi_permanent')
        var_qp = {vl: γ(vl, 'accompanying', 'quasi_permanent') for vl in VARIABLE_LOADS}
        # live_load=0, wind_load=0 → skipped by _copy_loads; thermal_load=0.5 → included
        for direction in DIRECTIONS:
            surf_f = γ('surfacing', direction, 'quasi_permanent')
            _register('SLS_QP', dl_f, surf_f, var_qp,
                      label=f"DL={dl_f}  Surf={surf_f}({direction})  TL=0.5",
                      key=IRC6_2017.SLS_COMBINATION_KEYS.get(('quasi_permanent', None, direction), ""))

        print(f"\nTotal SLS combinations created: {len(created)}")
        self.sls_combinations = created
        return created

    def analyze(self, model=None):

        model = model or self.model
        if model is None:
            raise ValueError("Model not created")

        model.analyze()

        results = model.get_results()
        return results

    def get_result_data(self, dev: bool = False) -> dict:
        """
        Return the flat result dict for all analysed load cases.

        Delegates to results_data.restructure_data(), which reads nodes and
        members directly from the live openseespy model rather than through the
        PlateGirderBridge wrapper.

        Parameters
        ----------
        dataset : xarray.Dataset, optional
            Pre-computed results dataset.  When omitted, ``self.model.get_results()``
            is called internally.
        dev : bool
            If True, also dump the dict to tools/bridge_plot_data.json.
        """
        if self.model is None:
            raise RuntimeError(
                "No model available. Call create_model() before get_result_data()."
            )
        return restructure_data_direct(
            model=self.model,
            # Reuse the dataset already materialized by _reanalyze_with_dedup();
            # omitting it would make restructure_data call model.get_results() and
            # rebuild the entire xarray Dataset from the raw records a second time.
            dataset=getattr(self, "_deduplicated_results", None),
            edge_dist=self.edge_dist or 0.0,
            dev=dev,
            # Serve forces/displacements lazily from the dataset instead of
            # duplicating every load case as nested dicts of Python floats.
            # dev mode needs eager tables for its JSON dumps.
            lazy=not dev,
        )

    def plot(self, model=None):
        model = model or self.model
        if model is None:
            raise ValueError("Model is not available. Create model before plotting.")

        results = model.get_results()
        load_case_of_interest = 'girder self weight'

        ext_beam_nodes = model.get_element(member="exterior_main_beam_1", options="nodes")

        max_def = max(results.displacements.sel(Loadcase=load_case_of_interest, Component="dy", Node=ext_beam_nodes[0]))
        max_report_def = f"The maximum deflection = {max_def.values * 1000:.2f} mm"

        # Plot deflection
        og.plot_defo(model, results, member="exterior_main_beam_1", option="nodes", loadcase=load_case_of_interest)
        og.plt.title(max_report_def)
        og.plt.show()

        # load case specific results
        static_lc_result = model.get_results(load_case=['DW'])
        print("static_lc_result")
        print(static_lc_result)

        static_lc_forces = static_lc_result.forces

        # Select a specific load case from result
        load_case_name = 'DW'

        # extract elements and nodes of beam 1
        member_name = "exterior_main_beam_1"

        # get the tag of elements and nodes
        ext_beam_elements = model.get_element(member=member_name, options="elements", )
        print(f"The element tags for Beam 1 is {ext_beam_elements}")

        # extract maximum bending moment from beam 1(member_name) from static_lc_result
        max_bending = max(static_lc_forces.sel(Component="Mz_i", Element=ext_beam_elements)).values / 1000
        print(f" Maximum bending moment = {max_bending:.2f} kNm")

        # ------------------------------------------------------------------------------
        # Plotting
        # ------------------------------------------------------------------------------

        # Plot BMD and SFD (change component as needed)
        load_case_of_interest = load_case_name
        og.plot_force(model, results, member="exterior_main_beam_1", component="Mz", loadcase=load_case_of_interest)

        max_report_bending = f"Maximum bending moment = {max_bending:.2f} kNm"

        og.plt.title(max_report_bending)
        og.plt.show()


# ============================================================
#   USAGE EXAMPLE
# ============================================================
if __name__ == "__main__":
    bridge = BridgeGrillageModel()

    # --- Test geometry values (replace with UI inputs later) ---
    bridge.set_geometry(GrillageGeometry(
        L=33.5 * m,
        n_l=7,
        n_t=11,
        edge_dist=1.1 * m,
        ext_to_int_dist=2.2775 * m,
        angle=0,
    ), DeckLayoutProperties(
        carriageway_width=7.0 * m,
        crash_barrier_width=0.45 * m,
        footpath_width=1.50 * m,
        railing_width=0.30 * m,
        median_width=1.0 * m,
        n_footpaths=2,
    ))

    # --- Test section values (replace with UI inputs later) ---
    # n_l=7 with edge_dist>0 → 5 structural main girders. Give each a DISTINCT
    # area (linearly scaled) to exercise per-girder section assignment.
    _base = SectionProperties(
        A=1.025 * m ** 2,
        J=0.1878 * m ** 3,
        Iz=0.3694 * m ** 4,
        Iy=0.3634 * m ** 4,
        Az=0.4979 * m ** 2,
        Ay=0.309 * m ** 2,
    )
    n_main = bridge.n_l - 2 if bridge.edge_dist > 0 else bridge.n_l
    girder_sections = [
        SectionProperties(
            A=_base.A * (1.0 + 0.1 * i),
            J=_base.J, Iz=_base.Iz, Iy=_base.Iy, Az=_base.Az, Ay=_base.Ay,
        )
        for i in range(n_main)
    ]
    bridge.create_sections(
        girder_sections=girder_sections,
        edge_longitudinal=SectionProperties(
            A=0.934 * m ** 2,
            J=0.1857 * m ** 3,
            Iz=0.3478 * m ** 4,
            Iy=0.213602 * m ** 4,
            Az=0.444795 * m ** 2,
            Ay=0.258704 * m ** 2,
        ),
        transverse=SectionProperties(
            A=0.504 * m ** 2,
            J=5.22303e-3 * m ** 3,
            Iz=1.3608e-3 * m ** 4,
            Iy=0.32928 * m ** 4,
            Az=0.42 * m ** 2,
            Ay=0.42 * m ** 2,
        ),
        end_transverse=SectionProperties(
            A=0.504 / 2 * m ** 2,
            J=2.5012e-3 * m ** 3,
            Iz=0.6804e-3 * m ** 4,
            Iy=0.04116 * m ** 4,
            Az=0.21 * m ** 2,
            Ay=0.21 * m ** 2,
        ),
    )

    # --- Test material values (replace with UI inputs later) ---
    bridge.create_material(MaterialProperties(
        steel_prop=SteelProperties(
            grade="steel",
            E=200 * GPa,
            v=0.3,
            rho=78.5 * kN / m ** 3,
            Fy=250 * MPa,
            E0=200 * GPa,
            b=0.01,
        ),
        concrete_prop=ConcreteProperties(
            grade="M30",
            fck=30.0,
            fctm=2.9,
            Ecm=31.0,
        ),
    ))

    bridge.assign_members()

    bridge.create_model()
    # bridge.plot_model()
    # bridge.add_dead_loads()
    bridge.create_self_weight_load()
    bridge.create_deck_load(slab_thickness_m=0.200)  # 200 mm RC slab
    bridge.create_wearing_course_load(thickness_m=0.050)  # 50 mm bituminous
    bridge.create_footpath_load()
    bridge.create_crash_barrier_load()
    bridge.create_railing_load()
    bridge.create_median_load()
    bridge.create_dead_load_combination()
    bridge.vehicle_lane_coordinates()
    bridge.create_vehicle_load_cases()
    bridge.add_vehicle_load_cases_from_combinations()
    bridge.create_moving_vehicle_load_cases()
    bridge.add_fatigue_vehicle_load_case()
    bridge.create_moving_fatigue_load_cases()
    # bridge.plot()

    results = bridge.analyze()

    # --- Verify per-girder sections reached the OpenSees elements ---
    import re as _re
    zg = bridge.model.common_grillage_element_z_group
    long_cats = ("edge_beam", "exterior_main_beam_1", "interior_main_beam", "exterior_main_beam_2")
    all_long = sorted({g for c in long_cats for g in zg.get(c, [])})
    main_groups = all_long[1:-1] if bridge.edge_dist > 0 else all_long
    print("\n" + "=" * 60)
    print("  PER-GIRDER SECTION VERIFICATION")
    print("=" * 60)
    for i, g in enumerate(main_groups):
        cat = next(c for c in ("exterior_main_beam_1", "exterior_main_beam_2",
                               "interior_main_beam", "edge_beam") if g in zg.get(c, []))
        eles = bridge.model.get_element(member=cat, options="elements",
                                        z_group_num=zg[cat].index(g))
        cmd = bridge.model.element_command_list.get(eles[0]) if eles else ""
        # element cmd: ...*[ni, nj], *[A, E, G, J, Iy, Iz], ... — area is the
        # first entry of the SECOND bracket group.
        brackets = _re.findall(r"\*\[([^\]]+)\]", cmd)
        elem_A = brackets[1].split(",")[0].strip() if len(brackets) > 1 else "?"
        print(f"  girder {i} z_group {g:<2} [{cat:<20}] "
              f"expected A={girder_sections[i].A:.4f}  element A={elem_A}")
    print("=" * 60)

    result_handler = PlateGirderAnalysisResults(
        dataset=results,
        bridge=bridge,
        edge_dist=bridge.edge_dist
    )

    # result_handler.run_interactive_viewer()
    # result_handler.print_moving_load_trace()

