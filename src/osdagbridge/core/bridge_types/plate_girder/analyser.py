import ospgrillage as og
from math import *
import openseespy.opensees as ops
from osdagbridge.core.utils.codes.irc6_2017 import *
from osdagbridge.core.utils.common import *
from osdagbridge.core.bridge_types.plate_girder.bridge_geometry import *
import warnings
from osdagbridge.core.bridge_types.plate_girder.analysis_results import PlateGirderAnalysisResults


class BridgeGrillageModel:

    def __init__(self):

        # -------------------- MATERIALS --------------------
        self.concrete = og.create_material(
            material="concrete", code="AS5100-2017", grade="65MPa"
        )

        self.concrete_custom = og.create_material(
            material="concrete", E=50 * GPa, v=0.3, rho=24 * kN / m**3
        )

        # -------------------- SECTIONS --------------------
        self.edge_longitudinal_section = og.create_section(
            A=0.934 * m**2,
            J=0.1857 * m**3,
            Iz=0.3478 * m**4,
            Iy=0.213602 * m**4,
            Az=0.444795 * m**2,
            Ay=0.258704 * m**2,
        )

        self.longitudinal_section = og.create_section(
            A=1.025 * m**2,
            J=0.1878 * m**3,
            Iz=0.3694 * m**4,
            Iy=0.3634 * m**4,
            Az=0.4979 * m**2,
            Ay=0.309 * m**2,
        )

        self.transverse_section = og.create_section(
            A=0.504 * m**2,
            J=5.22303e-3 * m**3,
            Iy=0.32928 * m**4,
            Iz=1.3608e-3 * m**4,
            Ay=0.42 * m**2,
            Az=0.42 * m**2,
            unit_width=True,
        )

        self.end_transverse_section = og.create_section(
            A=0.504 / 2 * m**2,
            J=2.5012e-3 * m**3,
            Iy=0.04116 * m**4,
            Iz=0.6804e-3 * m**4,
            Ay=0.21 * m**2,
            Az=0.21 * m**2,
        )

        # -------------------- GRILLAGE MEMBERS --------------------
        self.longitudinal_beam = og.create_member(
            section=self.longitudinal_section, material=self.concrete
        )

        self.edge_longitudinal_beam = og.create_member(
            section=self.edge_longitudinal_section, material=self.concrete
        )

        self.transverse_slab = og.create_member(
            section=self.transverse_section, material=self.concrete
        )

        self.end_transverse_slab = og.create_member(
            section=self.end_transverse_section, material=self.concrete
        )

        # -------------------- GEOMETRY --------------------
        self.L = 33.5 * m
        # self.w = 11.565 * m
        self.n_l = 7
        self.n_t = 11
        self.edge_dist = 1.05 * m
        self.ext_to_int_dist = 2.2775 * m
        self.angle = 0

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
    #   CREATE THE GRILLAGE MODEL
    # ============================================================
    def create_model(self):   
        
        # -------------------------------------------------
        # Create cross-section layout (UI inputs)
        # -------------------------------------------------
        self.layout = CrossSectionLayout(
            carriageway_width=10.0,        # TODO: get from UI
            crash_barrier_width=0.45,      # TODO: get from UI
            footpath_width=1.50,           # TODO: get from UI
            railing_width=0.30,            # TODO: get from UI
            median_width=0.0,             # TODO: get from UI
            no_of_footpaths=2,             # TODO: get from UI
        )

        # -------------------------------------------------
        # Bridge geometry (width from layout)
        # -------------------------------------------------
        self.bridge_geometry = BridgeGeometry(
            span=self.L,
            width=self.layout.total_width
        )
        print(f"Bridge width from layout: {self.layout.total_width} m")

        self.layout.validate_against_bridge(self.bridge_geometry.width)

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
        self.model.set_member(self.edge_longitudinal_beam, member="edge_beam")
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

    def create_self_weight_load(self, model=None, L=None):
        """Creates beam self weight distributed along length."""
        model = model or self.model
        if model is None:
            raise ValueError("Model is not available. Create model before adding loads.")

        L = L or self.L
        
        start_beam = 0
        end_beam = L
        beam_mag = 22.4 * kN / 1.0  # kN/m

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
        
        #store reference on the instance
        self.self_weight_load_case = DL_self_weight

        model.add_load_case(DL_self_weight)
        return DL_self_weight

    def create_deck_load(self, model=None):
        """
        Creates deck slab patch load over the full bridge deck.

        Geometry is obtained from load_manager.
        The created load case is stored on `self.deck_load_case`.
        """
        model = model or self.model
        if model is None:
            raise ValueError("Model is not available. Create model before adding loads.")

        # -------------------------------------------------
        # Load magnitude (UDL over area)
        # -------------------------------------------------
        deck_mag = 25.0 * kN / (1.0 ** 2)   # <-- update as per slab + wearing course if needed

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

    def create_wearing_course_load(self, model=None, edge_clearance=0.0):
        """Creates wearing course load (patch).

        If `model`, `L` or `w` are not provided they default to the
        instance values `self.model`, `self.L`, `self.w`.
        The created load case is stored on `self.overlay_load_case`.
        """
        model = model or self.model
        if model is None:
            raise ValueError("Model is not available. Create model before adding loads.")

        # L = L or self.L
        # w = w or self.w

        overlay_mag = 4.32 * kN / (1.0**2)

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
        # Load magnitude (UDL over area)
        # -------------------------------------------------
        footpath_mag = 5.00 * kN / (1.0 ** 2)   # <-- update as per IRC value

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

    def create_crash_barrier_load(self, model=None):
        """
        Creates crash (edge) barrier line loads on both sides of the bridge.

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
        # Load magnitude (UDL along length)
        # -------------------------------------------------
        barrier_load = 6.54 * kN / m

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


    def create_railing_load(self, model=None):
        """
        Creates railing line loads on both sides of the bridge.

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
        # Load magnitude (UDL along length)
        # -------------------------------------------------
        railing_udl = 1.50 * kN / m   # <-- update if code value differs

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

    def create_median_load(self, model=None):
        """
        Creates median line load acting along the centerline of the median.

        Geometry is obtained from load_manager.
        The created load case is stored on `self.median_load_case`.
        """
        model = model or self.model
        if model is None:
            raise ValueError("Model is not available. Create model before adding loads.")

        # -------------------------------------------------
        # Load magnitude (UDL along length)
        # -------------------------------------------------
        median_udl = 4.00 * kN / m   # <-- update as per IRC / project data

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
            if layout.has_component("carriageway_left"):
                cw_left = layout.get_component("carriageway_left")

                n_lanes = IRC6_2017.table_6(cw_left.width)
                lane_width = cw_left.width / n_lanes

                for i in range(n_lanes):
                    z = cw_left.z_start + (i + 0.5) * lane_width
                    lane_coords.append((x_coord, z))

            if layout.has_component("carriageway_right"):
                cw_right = layout.get_component("carriageway_right")

                n_lanes = IRC6_2017.table_6(cw_right.width)
                lane_width = cw_right.width / n_lanes

                for i in range(n_lanes):
                    z = cw_right.z_start + (i + 0.5) * lane_width
                    lane_coords.append((x_coord, z))

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

        print(f"Vehicle lane coordinate cases: {result_cases}")
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

                    print(f"Created load case: {load_case_name}")

        self.vehicle_load_cases_list = all_vehicle_load_cases

        return all_vehicle_load_cases
    

    def add_vehicle_load_cases_from_combinations(self,model=None):
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
        
        alf = [1.0, 0.8, 0.4]
        dla = 1.3
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
                    lc_name = f"Case{case_num} {vehicle_type} L{i+1}"
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
                        load_obj=vehicle,
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

                    print(
                        f"Created {lc_name} at x={x_coord}, z={z_coord}"
                    )

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

            print(f"Created moving load case: {moving_name}")

        return self.moving_load_cases_list


    def vehicle_combination(self, carriageway_width=None):
        """
        Generate all ordered vehicle placement sequences for design lanes determined
        from `carriageway_width` using `IRC6_2017.table_6`.

        - 'ClassA' occupies 1 lane
        - 'Class70R' occupies 2 lanes

        Example (3 lanes) ->
            ['ClassA','ClassA','ClassA'], ['ClassA','Class70R'], ['Class70R','ClassA']

        Parameters
        ----------
        carriageway_width : float, optional
            Carriageway width in metres. If omitted, attempts to read from the
            instance `self.layout` (single or split carriageway).

        Returns
        -------
        list of lists
            Each inner list is an ordered sequence of vehicle types that fills
            the design lanes exactly.
        """
        # Determine carriageway width: prefer provided parameter, else attempt to read from layout
        # if carriageway_width is None:
        #     cw = None
        #     if getattr(self, 'layout', None) and self.layout.has_component('carriageway'):
        #         cw = self.layout.get_component('carriageway').width
        #     else:
        #         left = 0.0
        #         right = 0.0
        #         if getattr(self, 'layout', None) and self.layout.has_component('carriageway_left'):
        #             left = self.layout.get_component('carriageway_left').width
        #         if getattr(self, 'layout', None) and self.layout.has_component('carriageway_right'):
        #             right = self.layout.get_component('carriageway_right').width
        #         if left + right > 0.0:
        #             cw = left + right
        #     if cw is None:
        #         raise ValueError("carriageway_width must be provided or layout with carriageway must exist")
        #     carriageway_width = cw

        lanes = IRC6_2017.table_6(carriageway_width)

        sequences = []

        def _build(remaining_lanes, current_seq):
            if remaining_lanes == 0:
                sequences.append(list(current_seq))
                return
            # place ClassA (1 lane)
            current_seq.append("ClassA")
            _build(remaining_lanes - 1, current_seq)
            current_seq.pop()
            # place Class70R (2 lanes) if space
            if remaining_lanes >= 2:
                current_seq.append("Class70R")
                _build(remaining_lanes - 2, current_seq)
                current_seq.pop()

        _build(lanes, [])
        print("Vehicle placement sequences:", sequences)
        return sequences

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

        # results = model.get_results(load_case=['girder self weight', 'Deck slab load', 'Wearing course self weight',
        # 'Footpath load', 'Crash barrier load', 'Railing load', 'Median load'])
        results = model.get_results()
        print("results")
        print(results) 
        
        forces_table = results.forces
        Fy = forces_table.sel(Component = "Mz_i")
        print(Fy)
        df = Fy.to_pandas()
        df.to_excel("Mz_results_moving1.xlsx")

        results = model.get_results(
            load_case=[
                "girder self weight",
                "Deck slab load",
                "Wearing course self weight",
                "Footpath load",
                "Crash barrier load",
                "Railing load",
                "Median load"
            ]
        )

        return results

    def plot(self, model=None):
        model = model or self.model
        if model is None:
            raise ValueError("Model is not available. Create model before plotting.")

        results = model.get_results()
        load_case_of_interest = 'girder self weight'

        ext_beam_nodes = model.get_element(member="exterior_main_beam_1", options="nodes")

        max_def = max(results.displacements.sel(Loadcase=load_case_of_interest,Component="dy",Node=ext_beam_nodes[0]))
        max_report_def = f"The maximum deflection = {max_def.values*1000:.2f} mm"
        
        # Plot deflection
        og.plot_defo(model, results, member="exterior_main_beam_1", option="nodes",loadcase=load_case_of_interest)
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
        ext_beam_elements = model.get_element(member=member_name, options="elements",)
        print(f"The element tags for Beam 1 is {ext_beam_elements}")

        # extract maximum bending moment from beam 1(member_name) from static_lc_result
        max_bending = max(static_lc_forces.sel(Component="Mz_i",Element=ext_beam_elements)).values/1000
        print(f" Maximum bending moment = {max_bending:.2f} kNm") 

        # ------------------------------------------------------------------------------
        # Plotting
        # ------------------------------------------------------------------------------

        # Plot BMD and SFD (change component as needed)
        load_case_of_interest = load_case_name 
        og.plot_force(model, results, member="exterior_main_beam_1",component="Mz",loadcase=load_case_of_interest)

        max_report_bending = f"Maximum bending moment = {max_bending:.2f} kNm"

        og.plt.title(max_report_bending)
        og.plt.show()



# ============================================================
#   USAGE EXAMPLE
# ============================================================
if __name__ == "__main__":
    bridge = BridgeGrillageModel()
    bridge.create_model()
    # bridge.plot_model()
    # bridge.add_dead_loads()
    bridge.create_self_weight_load()
    bridge.create_deck_load()
    bridge.create_wearing_course_load()
    bridge.create_footpath_load()
    bridge.create_crash_barrier_load()
    bridge.create_railing_load()
    bridge.create_median_load()
    bridge.vehicle_lane_coordinates()
    # bridge.vehicle_combination(carriageway_width=6.0)
    bridge.create_vehicle_load_cases()
    bridge.add_vehicle_load_cases_from_combinations()
    bridge.create_moving_vehicle_load_cases()
    bridge.analyze()
    # bridge.plot()
    bridge.plot()

    results = bridge.analyze()

    result_handler = PlateGirderAnalysisResults(
        dataset=results,
        model=bridge.model
    )

    result_handler.run_interactive_viewer()

