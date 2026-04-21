import ospgrillage as og
# from math import sqrt, pi
# import openseespy.opensees as ops
from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
from osdagbridge.core.utils.codes.keyfile import (
    DEFAULT_STEEL_DENSITY,
    DEFAULT_CONCRETE_DENSITY,
    DEFAULT_BITUMINOUS_DENSITY,
    LANE_REDUCTION_FACTORS,
)
from osdagbridge.core.utils.common import *
from osdagbridge.core.bridge_types.plate_girder.bridge_geometry import BridgeGeometry, CrossSectionLayout
from osdagbridge.core.bridge_types.plate_girder.load_placement import LoadPlacementManager
import warnings
from osdagbridge.core.bridge_types.plate_girder.analysis_results import PlateGirderAnalysisResults
from osdagbridge.core.bridge_types.plate_girder.dto import (SectionProperties, SteelProperties, MaterialProperties, GrillageGeometry, DeckLayoutProperties)


class BridgeGrillageModel:

    def __init__(self):

        # -------------------- MATERIALS --------------------
        # Materials are set via create_material()
        self.steel_custom = None

        # -------------------- SECTIONS --------------------
        # Sections are set via create_sections()
        self.edge_longitudinal_section = None
        self.longitudinal_section = None
        self.transverse_section = None
        self.end_transverse_section = None

        # Cross-section properties (DTO), stashed by create_sections() so that
        # load magnitudes can be derived from actual geometry instead of
        # hard-coded placeholder values.
        self.longitudinal_props: SectionProperties | None = None
        self.edge_longitudinal_props: SectionProperties | None = None

        # -------------------- GRILLAGE MEMBERS --------------------
        # Members are set via create_material() once sections and material are ready
        self.longitudinal_beam = None
        self.edge_longitudinal_beam = None
        self.transverse_slab = None
        self.end_transverse_slab = None

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
        self.overlay_load_case = None

        # placeholder for self weight load case created later
        self.self_weight_load_case = None

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
                        longitudinal: SectionProperties,
                        edge_longitudinal: SectionProperties,
                        transverse: SectionProperties,
                        end_transverse: SectionProperties):
        """
        Creates all four grillage sections from user-supplied SectionProperties.

        Parameters
        ----------
        longitudinal : SectionProperties
            Properties for the interior longitudinal beam.
        edge_longitudinal : SectionProperties
            Properties for the edge longitudinal beam.
        transverse : SectionProperties
            Properties for the transverse slab (unit_width=True).
        end_transverse : SectionProperties
            Properties for the end transverse slab.
        """
        self.longitudinal_props = longitudinal
        self.edge_longitudinal_props = edge_longitudinal

        self.longitudinal_section = og.create_section(
            A=longitudinal.A,
            J=longitudinal.J,
            Iz=longitudinal.Iz,
            Iy=longitudinal.Iy,
            Az=longitudinal.Az,
            Ay=longitudinal.Ay,
        )

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
        self.longitudinal_beam = og.create_member(
            section=self.longitudinal_section, material=self.steel_custom
        )
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

        # Assign members
        self.model.set_member(self.longitudinal_beam, member="interior_main_beam")
        self.model.set_member(self.longitudinal_beam, member="exterior_main_beam_1")
        self.model.set_member(self.longitudinal_beam, member="exterior_main_beam_2")
        
        # Assign edge properties only if overhang exists; otherwise treat as normal girders
        if self.edge_dist > 0:
            self.model.set_member(self.edge_longitudinal_beam, member="edge_beam")
        else:
            self.model.set_member(self.longitudinal_beam, member="edge_beam")
        self.model.set_member(self.transverse_slab, member="transverse_slab")
        self.model.set_member(self.end_transverse_slab, member="start_edge")
        self.model.set_member(self.end_transverse_slab, member="end_edge")

        # Generate OpenSees model
        self.model.create_osp_model(pyfile=False)

        # update geometry with model
        # self.geometry.model = self.model

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

    # IS 875 (Part 1) / keyfile.DEFAULT_STEEL_DENSITY — structural steel unit weight (kN/m³).
    STEEL_UNIT_WEIGHT_kN_m3 = DEFAULT_STEEL_DENSITY

    def create_self_weight_load(self, model=None, L=None):
        """Creates beam self weight distributed along length.

        Magnitude is derived from the interior longitudinal girder section
        area (m²) × 78.5 kN/m³, so it tracks the actual section chosen by
        initial sizing rather than a hard-coded placeholder.
        """
        model = model or self.model
        if model is None:
            raise ValueError("Model is not available. Create model before adding loads.")

        if self.longitudinal_props is None:
            raise ValueError(
                "create_sections() must be called before create_self_weight_load(): "
                "girder cross-section area is required to compute self weight."
            )

        L = L or self.L

        start_beam = 0
        end_beam = L
        A_girder_m2 = self.longitudinal_props.A
        beam_mag = A_girder_m2 * self.STEEL_UNIT_WEIGHT_kN_m3 * kN / m  # N/m

        DL_self_weight = og.create_load_case(name="girder self weight")

        # iterate through all grillage transverse positions (except extreme edges)
        for z_pos in model.Mesh_obj.noz[1:-1]:
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

    # IRC 6:2017 / IS 875 Pt 1 — reinforced (wet) concrete unit weight (keyfile.DEFAULT_CONCRETE_DENSITY).
    WET_CONCRETE_DENSITY_kN_m3 = DEFAULT_CONCRETE_DENSITY

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

        rho_c = self.WET_CONCRETE_DENSITY_kN_m3 if concrete_density_kN_m3 is None else concrete_density_kN_m3

        # -------------------------------------------------
        # Load magnitude (UDL over area): t × ρ_concrete  [kN/m²]
        # -------------------------------------------------
        deck_mag = slab_thickness_m * rho_c * kN / m**2  # N/m²

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
        DL_deck = og.create_load_case(name="Deck slab load")
        DL_deck.add_load(deck_load)
        model.add_load_case(DL_deck)

        # store reference
        self.deck_load_case = DL_deck

        return DL_deck

    def create_wearing_course_load(self, model=None, edge_clearance=0.0,
                                   thickness_m: float | None = None,
                                   density_kN_m3: float | None = None):
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
        The created load case is stored on `self.overlay_load_case`.
        """
        model = model or self.model
        if model is None:
            raise ValueError("Model is not available. Create model before adding loads.")

        if thickness_m is None:
            raise ValueError(
                "create_wearing_course_load requires thickness_m (in metres) "
                "so the overlay load magnitude can be derived from t × ρ."
            )
        rho_wc = DEFAULT_BITUMINOUS_DENSITY if density_kN_m3 is None else density_kN_m3

        # L = L or self.L
        # w = w or self.w

        overlay_mag = thickness_m * rho_wc * kN / m**2  # N/m²

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

        DL_overlay = og.create_load_case(name="Wearing course self weight")
        DL_overlay.add_load(overlay)
        model.add_load_case(DL_overlay)

        # store reference on the instance
        self.overlay_load_case = DL_overlay

        return DL_overlay

    # IRC 5:2015 / IS 875 Pt 2 — standard SIDL intensities used when the user
    # has not provided explicit load inputs via the Additional Inputs dialog.
    RCC_CRASH_BARRIER_LOAD_kN_per_m = 6.54   # typical RCC crash barrier (IRC 5 Type P3/P4)
    MEDIAN_LOAD_kN_per_m = 4.00               # raised-kerb / RCC median (nominal weight)

    def create_footpath_load(self, model=None):
        """
        Creates footpath patch loads on both sides of the bridge.

        Geometry is obtained from load_manager.
        The created load case is stored on `self.footpath_load_case`.
        """
        model = model or self.model
        if model is None:
            raise ValueError("Model is not available. Create model before adding loads.")

        # If there is no footpath component in the layout, skip creating footpath load
        if not self.layout.has_component("footpath_left") or not self.layout.has_component("footpath_right"):
            warnings.warn("No footpath component in layout; skipping footpath load creation")
            self.footpath_load_case = None
            return None
        # -------------------------------------------------
        # Load magnitude — IRC 6:2017 Cl.206.1 (footway load)
        # -------------------------------------------------
        footpath_mag = IRC6_2017.cl_206_1_footway_load() * kN / m**2  # N/m²

        # -------------------------------------------------
        # Create load case
        # -------------------------------------------------
        DL_footpath = og.create_load_case(name="Footpath load")

        # -------------------------------------------------
        # Left & Right footpaths
        # -------------------------------------------------
        for side in ("left", "right"):
            # geometry from load manager
            geom = self.load_manager.footpath_load(side)

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

        # If there is no crash barrier component in the layout, skip creating crash barrier load
        if not self.layout.has_component("crash_barrier_left") or not self.layout.has_component("crash_barrier_right"):
            warnings.warn("No crash barrier component in layout; skipping crash barrier load creation")
            self.crash_barrier_load_case = None
            return None
        # -------------------------------------------------
        # Load magnitude — from input or code default
        # -------------------------------------------------
        _mag = barrier_load_kN_per_m if barrier_load_kN_per_m is not None else self.RCC_CRASH_BARRIER_LOAD_kN_per_m
        barrier_load = _mag * kN / m

        # -------------------------------------------------
        # Create load case
        # -------------------------------------------------
        DL_barrier = og.create_load_case(name="Crash barrier load")

        # -------------------------------------------------
        # Left & Right barriers
        # -------------------------------------------------
        for side in ("left", "right"):
            # geometry from load manager
            geom = self.load_manager.crash_barrier_load(side)

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

        # If there is no railing component in the layout, skip creating railing load
        if not self.layout.has_component("railing_left") or not self.layout.has_component("railing_right"):
            warnings.warn("No railing component in layout; skipping railing load creation")
            self.railing_load_case = None
            return None

        # -------------------------------------------------
        # Load magnitude — from user input or IRC 6:2017 Cl.206.5 code value.
        # cl_206_5_railing_load() returns kg/m; convert to kN/m via × 9.81/1000.
        # -------------------------------------------------
        if railing_load_kN_per_m is not None:
            _mag = railing_load_kN_per_m
        else:
            _mag = IRC6_2017.cl_206_5_railing_load() * 9.81 / 1000.0
        railing_udl = _mag * kN / m  # N/m

        # -------------------------------------------------
        # Create load case
        # -------------------------------------------------
        DL_railing = og.create_load_case(name="Railing load")

        # -------------------------------------------------
        # Left & Right railings
        # -------------------------------------------------
        for side in ("left", "right"):
            # geometry from load manager
            geom = self.load_manager.railing_load(side)

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
        # Load magnitude — from input or code default
        # -------------------------------------------------
        _mag = median_load_kN_per_m if median_load_kN_per_m is not None else self.MEDIAN_LOAD_kN_per_m
        median_udl = _mag * kN / m

        # If there is no median component in the layout, skip creating median load
        if not self.layout.has_component("median"):
            warnings.warn("No median component in layout; skipping median load creation")
            self.median_load_case = None
            return None

        # -------------------------------------------------
        # Get geometry from load manager
        # -------------------------------------------------
        geom = self.load_manager.median_line_load()

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

            for vehicle_type, coord_list in combinations.items():

                for lane_index, (x_coord, z_coord) in enumerate(coord_list, start=1):
                    # ---------------------------------------
                    # Create vehicle
                    # ---------------------------------------
                    vehicle_generator = og.create_load_model(
                        model_type=vehicle_type.upper()
                    )
                    vehicle = vehicle_generator.create()

                    vehicle.set_global_coord(
                        og.Point(x_coord, 0.0, z_coord)
                    )

                    # ---------------------------------------
                    # Create load case
                    # ---------------------------------------
                    load_case_name = f"Case{case_num} {vehicle_type} L{lane_index}"

                    lc = og.create_load_case(name=load_case_name)
                    lc.add_load(vehicle)

                    model.add_load_case(lc)

                    all_vehicle_load_cases.append(lc)

                    # print(f"Created load case: {load_case_name}")

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
        # Empty lists
        # -------------------------------------------------
        self.vehicle_load_cases_list = []
        self.vehicle_moving_loads = []

        for case in vehicle_cases:

            case_num = case["case_num"]
            combinations = case["combinations"]

            for vehicle_type, coord_list in combinations.items():

                for i, (x_coord, z_coord) in enumerate(coord_list):

                    # -----------------------------
                    # Create load case name
                    # -----------------------------
                    lc_name = f"Case{case_num} {vehicle_type} L{i + 1}"
                    lc = og.create_load_case(name=lc_name)

                    # -----------------------------
                    # Lane factor
                    # -----------------------------
                    if alf is None:
                        lane_factor = 1.0
                    else:
                        lane_factor = alf[i] if i < len(alf) else 1.0

                    # -----------------------------
                    # Create vehicle model
                    # -----------------------------
                    vehicle_generator = og.create_load_model(
                        model_type=vehicle_type.upper()
                    )

                    vehicle = vehicle_generator.create()

                    # -----------------------------
                    # Set global coordinates
                    # (from vehicle_lane_coordinates)
                    # -----------------------------
                    vehicle.set_global_coord(
                        og.Point(x_coord, 0.0, z_coord)
                    )

                    # -----------------------------
                    # Add to load case
                    # -----------------------------
                    lc.add_load(
                        load=vehicle,
                        load_factor=lane_factor
                    )

                    # -----------------------------
                    # Add load case to model
                    # -----------------------------
                    model.add_load_case(
                        lc,
                        load_factor=dla
                    )

                    # -----------------------------
                    # Store references
                    # -----------------------------
                    self.vehicle_load_cases_list.append(lc)
                    self.vehicle_moving_loads.append(vehicle)

                    # print(
                    #     f"Created {lc_name} at x={x_coord}, z={z_coord}"
                    # )

        return self.vehicle_load_cases_list

    def create_moving_vehicle_load_cases(
            self,
            model=None,
            start_offset=-25.0,
            span=None,
    ):
        """
        Creates moving load cases corresponding to
        previously created static vehicle load cases.
        """

        model = model or self.model
        if model is None:
            raise ValueError("Model not created yet.")

        if not hasattr(self, "vehicle_moving_loads") or not self.vehicle_moving_loads:
            raise ValueError("No vehicle loads found. Create vehicle load cases first.")

        span = span or self.L

        # -------------------------------------------------
        # Create moving path
        # -------------------------------------------------
        start = og.create_point(x=start_offset, y=0, z=0)
        end = og.Point(span, 0, 0)

        moving_path = og.create_moving_path(
            start_point=start,
            end_point=end
        )

        # -------------------------------------------------
        # Create moving load cases
        # -------------------------------------------------
        self.moving_load_cases_list = []

        for i, vehicle in enumerate(self.vehicle_moving_loads):
            # Use static load case name
            static_lc_name = self.vehicle_load_cases_list[i].name

            moving_name = f"Moving {static_lc_name}"

            moving_load = og.create_moving_load(name=moving_name)

            moving_load.set_path(moving_path)
            moving_load.add_load(vehicle)

            model.add_load_case(moving_load)

            self.moving_load_cases_list.append(moving_load)

            # print(f"Created moving load case: {moving_name}")

        return self.moving_load_cases_list


    def add_vehicle_load_with_moving_path(
            self,
            model=None,
            vehicle_type="CLASS70R",
            load_case_name="Class 70R",
            x_coord=0.0,
            z_coord=0.0,
            spacing=1.5,
            span=None,
            y_coord=0.0,
    ):
        """
        Adds a vehicle load (static + moving) to the grillage model.

        Parameters
        ----------
        model : ospgrillage.grillage.Grillage
            Grillage model
        vehicle_type : str
            Load model type (e.g. 'M1600', 'CLASS70R')
        load_case_name : str
            Name of the static load case
        x_coord : float
            Initial longitudinal position of vehicle
        z_coord : float
            Transverse position of vehicle
        spacing : float
            Vehicle spacing for moving load start position
        span : float
            Bridge span length
        y_coord : float, optional
            Vertical coordinate (default = 0.0)

        Returns
        -------
        dict
            Dictionary containing:
            - 'vehicle'
            - 'static_load_case'
            - 'moving_load_case'
            - 'moving_path'
        """
        model = model or self.model
        if model is None:
            raise ValueError("Model is not available. Create model before adding loads.")

        span = span or self.L

        # -----------------------------
        # Create vehicle
        # -----------------------------
        vehicle_generator = og.create_load_model(model_type=vehicle_type)
        vehicle = vehicle_generator.create()

        # Set global position
        vehicle.set_global_coord(og.Point(x_coord, y_coord, z_coord))

        # -----------------------------
        # Static load case
        # -----------------------------
        static_lc = og.create_load_case(name=load_case_name)
        static_lc.add_load(vehicle)
        model.add_load_case(static_lc)

        # -----------------------------
        # Moving load path
        # -----------------------------
        start = og.create_point(x=-spacing, y=0, z=0)
        end = og.Point(span, 0, 0)
        path = og.create_moving_path(start_point=start, end_point=end)

        # -----------------------------
        # Moving load case
        # -----------------------------
        moving_lc_name = f"Moving {load_case_name}"
        moving_lc = og.create_moving_load(name=moving_lc_name)
        moving_lc.set_path(path)
        moving_lc.add_load(vehicle)

        model.add_load_case(moving_lc)

        return {
            "vehicle": vehicle,
            "static_load_case": static_lc,
            "moving_load_case": moving_lc,
            "moving_path": path,
        }

    def analyze(self, model=None):

        model = model or self.model
        if model is None:
            raise ValueError("Model not created")

        model.analyze()

        # Get ALL loadcases
        results = model.get_results()

        # ✅ DEBUG: Show all detected loadcases
        # print(results.coords["Loadcase"].values)

        # print("Results dataset:")
        # print(results)

        self.dataset = results

        return results

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
        static_lc_result = model.get_results(load_case=['Deck slab load'])
        print("static_lc_result")
        print(static_lc_result)

        static_lc_forces = static_lc_result.forces

        # Select a specific load case from result
        load_case_name = 'Deck slab load'

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
    bridge.create_sections(
        longitudinal=SectionProperties(
            A=1.025 * m ** 2,
            J=0.1878 * m ** 3,
            Iz=0.3694 * m ** 4,
            Iy=0.3634 * m ** 4,
            Az=0.4979 * m ** 2,
            Ay=0.309 * m ** 2,
        ),
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
    bridge.create_material(SteelProperties(
        grade="steel",
        E=200 * GPa,
        v=0.3,
        rho=78.5 * kN / m ** 3,
        Fy=250 * MPa,
        E0=200 * GPa,
        b=0.01,
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
    bridge.vehicle_lane_coordinates()
    bridge.create_vehicle_load_cases()
    bridge.add_vehicle_load_cases_from_combinations()
    bridge.create_moving_vehicle_load_cases()
    # bridge.plot()

    results = bridge.analyze()

    result_handler = PlateGirderAnalysisResults(
        dataset=results,
        bridge=bridge,
        edge_dist=bridge.edge_dist
    )


    result_handler.run_interactive_viewer()

    # result_handler.print_moving_load_trace()

