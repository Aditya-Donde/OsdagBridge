import ospgrillage as og
from math import *
import openseespy.opensees as ops
from osdagbridge.core.utils.codes.irc6_2017 import *
from osdagbridge.core.utils.common import *
from osdagbridge.core.bridge_types.plate_girder.bridge_geometry import *


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
            carriageway_width=7.5,        # TODO: get from UI
            crash_barrier_width=0.45,      # TODO: get from UI
            footpath_width=1.50,           # TODO: get from UI
            railing_width=0.30,            # TODO: get from UI
            median_width=1.20,             # TODO: get from UI
            no_of_footpaths=2,             # TODO: get from UI
        )

        # -------------------------------------------------
        # Bridge geometry (width from layout)
        # -------------------------------------------------
        self.bridge_geometry = BridgeGeometry(
            span=self.L,
            width=self.layout.total_width
        )

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

    def analyze(self, model=None):
        model = model or self.model
        if model is None:
            raise ValueError("Model is not available. Create model before adding loads.")
        # Analysis
        model.analyze()

        results = model.get_results(load_case=['girder self weight', 'Wearing course self weight', 'Footpath load', 'Crash barrier load', 'Railing load', 'Median load'])
        print("results")
        print(results) 

        girder_results = model.get_results(load_case=[ 'girder self weight'])
        print("girder_sw_results") 
        print(girder_results)

        # extract elements and nodes of beam 1
        member_name = "exterior_main_beam_1"

        # get the tag of elements and nodes
        ext_beam_elements = model.get_element(member=member_name, options="elements",)
        print(f"The element tags for Beam 1 is {ext_beam_elements}")

        ext_beam_nodes = model.get_element(member=member_name, options="nodes")
        print(f"The node tags for Beam 1 is {ext_beam_nodes[0]}")


# ============================================================
#   USAGE EXAMPLE
# ============================================================
if __name__ == "__main__":
    bridge = BridgeGrillageModel()
    bridge.create_model()
    # bridge.plot_model()
    # bridge.add_dead_loads()
    bridge.create_self_weight_load()
    bridge.create_wearing_course_load()
    bridge.create_footpath_load()
    bridge.create_crash_barrier_load()
    bridge.create_railing_load()
    bridge.create_median_load()
    bridge.analyze()
