"""
CAD generator for Plate Girder Bridge.

"""

from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB, Quantity_NOC_BLACK
from OCC.Core.TopoDS import TopoDS_Shape
from OCC.Core.AIS import AIS_Shape
from OCC.Core.TopAbs import TopAbs_EDGE

# Builder imports

from osdagbridge.core.bridge_components.super_structure.plate_girder.builder import (
    build_plate_girder_geometry
)


from osdagbridge.core.bridge_components.super_structure.deck.builder import (
    build_deck
)

from osdagbridge.core.bridge_components.super_structure.crash_barrier.builder import (
    build_crash_barriers
)

from osdagbridge.core.bridge_components.super_structure.railing.builder import (
    build_railings
)

from osdagbridge.core.bridge_components.super_structure.median.builder import (
    build_median
)

from osdagbridge.core.bridge_components.super_structure.cross_bracing.builder import (
    build_cross_bracings
)


KEY_CAD_GIRDER = "Girder"
KEY_CAD_STIFFENER = "Stiffener"
KEY_CAD_CROSS_BRACING = "Cross Bracing"
KEY_CAD_DECK = "Deck"
KEY_CAD_CRASH_BARRIER = "Crash Barrier"
KEY_CAD_RAILING = "Railing"
KEY_CAD_MEDIAN = "Median"
KEY_MODULE_PG = "Plate Girder"



# CAD GENERATOR CLASS

class PlateGirderCADGenerator:
    """
    Plate Girder Bridge CAD Generator.

    Holds parameters and generates assembled CAD geometry.
    """

    def __init__(self, bridge_type=KEY_MODULE_PG):

        self.bridge_type = bridge_type

        # GIRDERS PARAMETERS
        self.span_length_L = 10000

        self.girder_section_d = 900          # clear web depth
        self.girder_section_bf = 500  #top flange width
        self.girder_section_bf_b = 500  #bottom flange width
        self.girder_section_tf = 260  #top flange thickness
        self.girder_section_tf_b = 260  #bottom flange thickness
        self.girder_section_tw = 100

        self.num_girders = 5
        self.girder_spacing = 2750           # center-to-center spacing

        # DECK PARAMETERS
        self.carriageway_width = 12000
        self.deck_thickness = 400

        self.footpath_config = "NONE"         # NONE / LEFT / RIGHT / BOTH
        self.footpath_width = 1500
        self.railing_width = 300

        # CRASH BARRIER PARAMETERS
        self.barrier_type = "Semi-Rigid"  # "Rigid" or "Semi-Rigid"
        self.crash_barrier_subtype = "Single W-beam"  # "IRC-5R", "High Containment", "Single W-beam", "Double W-beam"

        # MEDIAN PARAMETERS
        self.enable_median = True
        self.median_type = "Metallic Crash Barrier"  # "Raised Kerb", "RCC Crash Barrier", "Metallic Crash Barrier"

        # RAILING PARAMETERS
        self.railing_height = 1200
        self.rail_count = 3

        # STIFFENER PARAMETERS
        self.stiffener_width = 200
        self.stiffener_length = 10

        # END STIFFENER PARAMETERS
        self.include_end_stiffeners = True
        self.end_stiffener_thickness = 25


        # CROSS BRACING PARAMETERS
        self.cross_bracing_spacing = 4000
        self.cross_bracing_thickness = 5

        self.bracing_type = "K"               # "X" or "K"
        self.x_bracket_option = "BOTH"
        self.k_top_bracket = True

        self.cross_bracing_section_type = "CHANNEL"
        self.cross_bracing_section_dims = {
            "depth": 100,
            "flange_width": 50,
            "web_thickness": 5,
            "flange_thickness": 7
        }



    # MAIN CAD GENERATION

    def generate(self):
        """
        Generate full bridge CAD.
        """

        # Local helpers
        from OCC.Core.gp import gp_Trsf, gp_Vec
        from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform

        def _translate(shape, dx=0, dy=0, dz=0):
            trsf = gp_Trsf()
            trsf.SetTranslation(gp_Vec(dx, dy, dz))
            return BRepBuilderAPI_Transform(shape, trsf, True).Shape()

        # 1. BUILD SINGLE PLATE GIRDER GEOMETRY
        pg = build_plate_girder_geometry(
            D=self.girder_section_d,
            tw=self.girder_section_tw,
            length=self.span_length_L,
            T_ft=self.girder_section_tf,
            T_fb=self.girder_section_tf_b,
            B_ft=self.girder_section_bf,
            B_fb=self.girder_section_bf_b,
            stiffener_spacing=750,
            T_is=20,
            chamfer_length=40,
            include_end_stiffeners=self.include_end_stiffeners,
            T_es=self.end_stiffener_thickness
        )

        # 2. PLACE MULTIPLE GIRDERS (Y-DIRECTION, CENTERED)
        girders = []
        stiffeners = []

        girder_web = []
        girder_flanges = []

        total_width = (self.num_girders - 1) * self.girder_spacing

        for i in range(self.num_girders):
            y_offset = (i * self.girder_spacing) - (total_width / 2)

            # Web
            web = _translate(pg["web"], dy=y_offset)
            girders.append(web)
            girder_web.append(web)

            # Top flange
            top_flange = _translate(pg["top_flange"], dy=y_offset)
            girders.append(top_flange)
            girder_flanges.append(top_flange)

            # Bottom flange
            bottom_flange = _translate(pg["bottom_flange"], dy=y_offset)
            girders.append(bottom_flange)
            girder_flanges.append(bottom_flange)


            # Stiffeners
            for stiff in pg["stiffeners"]:
                stiffeners.append(
                    _translate(stiff, dy=y_offset)
                )

        supports_tri = []
        supports_cyl = []

        for i in range(self.num_girders):
            y_offset = (i * self.girder_spacing) - (total_width / 2)

            for s in pg["supports_tri"]:
                supports_tri.append(_translate(s, dy=y_offset))

            for s in pg["supports_cyl"]:
                supports_cyl.append(_translate(s, dy=y_offset))


        # 3. REFERENCE Z-LEVELS 

        bracing_girder_depth = (
            (self.girder_section_d / 2)
            + self.girder_section_tf
        )



        # Top of girder for deck placement ONLY
        girder_top_z = (self.girder_section_d / 2) + self.girder_section_tf

        # 4. CROSS BRACING SYSTEM 
        cross_bracings = build_cross_bracings(
            span_length_L=self.span_length_L,
            num_girders=self.num_girders,
            girder_spacing=self.girder_spacing,

            
            girder_depth=bracing_girder_depth,

            flange_thickness=self.girder_section_tf,
            flange_width=self.girder_section_bf,

            bracing_type=self.bracing_type,
            section_type=self.cross_bracing_section_type,
            section_dims=self.cross_bracing_section_dims,
            thickness=self.cross_bracing_thickness,

            panel_spacing=self.cross_bracing_spacing,
            bracket_option=self.x_bracket_option,
            top_bracket=self.k_top_bracket
        )

        # 5. IRC 5 SPECIFICATIONS (CRASH BARRIER)
        from osdagbridge.core.utils.codes.irc5_2015 import IRC5_2015
        from osdagbridge.core.utils.common import (
            KEY_CRASH_BARRIER_TYPE,
            KEY_FOOTPATH,
            KEY_RAILING_TYPE,
            KEY_RIGID_CRASH_BARRIER_TYPE,
            KEY_METALLIC_CRASH_BARRIER_TYPE,
            KEY_MEDIAN_TYPE
        )

        # Map barrier_type string to KEY_CRASH_BARRIER_TYPE index
        barrier_type_map = {"Flexible": 0, "Semi-Rigid": 1, "Rigid": 2}
        barrier_idx = barrier_type_map.get(self.barrier_type, 2)
        
        # Map crash_barrier_subtype
        rigid_subtype_map = {"IRC-5R": 0, "High Containment": 1}
        metallic_subtype_map = {"Single W-beam": 0, "Double W-beam": 1}

        if self.barrier_type == "Rigid":
            rigid_subtype_idx = rigid_subtype_map.get(self.crash_barrier_subtype, 0)
            if self.footpath_config == "NONE":
                design_dict = IRC5_2015.cl_109_6_3_shapes(
                    barrier_type=KEY_CRASH_BARRIER_TYPE[barrier_idx],
                    footpath=KEY_FOOTPATH[0],
                    railing_type=None,
                    design_dict={},
                    crash_barrier_type=KEY_RIGID_CRASH_BARRIER_TYPE[rigid_subtype_idx]
                )
            else:
                design_dict = IRC5_2015.cl_109_6_3_shapes(
                    barrier_type=KEY_CRASH_BARRIER_TYPE[barrier_idx],
                    footpath=KEY_FOOTPATH[1],
                    railing_type=KEY_RAILING_TYPE[0],
                    design_dict={},
                    crash_barrier_type=KEY_RIGID_CRASH_BARRIER_TYPE[rigid_subtype_idx]
                )
            # For rigid, the base width is in "crash_barrier_width"
            actual_base_width = design_dict.get("crash_barrier_width", 450)
        else:
            # Semi-rigid / Metallic
            metallic_subtype_idx = metallic_subtype_map.get(self.crash_barrier_subtype, 0)
            design_dict = IRC5_2015.cl_109_6_3_shapes(
                barrier_type=KEY_CRASH_BARRIER_TYPE[1],
                footpath=KEY_FOOTPATH[0] if self.footpath_config == "NONE" else KEY_FOOTPATH[1],
                railing_type=None,
                design_dict={},
                crash_barrier_type=KEY_METALLIC_CRASH_BARRIER_TYPE[metallic_subtype_idx]
            )
            # For semi-rigid/metallic, the kerb bottom width is the base width
            actual_base_width = design_dict.get("kerb_bottom_width", 550)

        # 6. DECK SYSTEM (USES TOP-OF-GIRDER Z)
        deck_out = build_deck(
            span_length_L=self.span_length_L,
            girder_section_d=girder_top_z,
            deck_thickness=self.deck_thickness,

            footpath_config=self.footpath_config,
            carriageway_width=self.carriageway_width,
            crash_barrier_base_width=actual_base_width,
            footpath_width=self.footpath_width,
            railing_width=self.railing_width
        )

        # 7. CRASH BARRIER PLACEMENT

        crash_barrier_w_beams = []
        crash_barrier_other = []

        crash_barriers_raw = build_crash_barriers(
            span_length_L=self.span_length_L,
            deck_top_z=deck_out["deck_top_z"],
            footpath_config=self.footpath_config,
            carriageway_width=self.carriageway_width,
            footpath_width=self.footpath_width,
            railing_width=self.railing_width,
            design_dict=design_dict,
            barrier_type=self.barrier_type
        )

        crash_barriers = []

        for cb in crash_barriers_raw:
            if isinstance(cb, dict):
                if cb.get("w_beams"):
                    crash_barrier_w_beams.append(cb["w_beams"])
                for k in ("kerb", "posts", "spacers"):
                    if cb.get(k):
                        crash_barrier_other.append(cb[k])
                        crash_barriers.append(cb[k])
            else:
                crash_barriers.append(cb)

        # 8. MEDIAN
        median_barriers = []
        median_w_beams = [] 
        if self.enable_median:
            # Get median design specifications from IRC5_2015
            median_type_map = {"Raised Kerb": 0, "RCC Crash Barrier": 1, "Metallic Crash Barrier": 2}
            median_idx = median_type_map.get(self.median_type, 1)
            
            # Map metallic subtype for median
            metallic_subtype_idx = metallic_subtype_map.get(self.crash_barrier_subtype, 0)
            
            median_design_dict = IRC5_2015.cl_109_6_3_shapes(
                barrier_type=KEY_MEDIAN_TYPE[median_idx],
                footpath=KEY_FOOTPATH[0],
                railing_type=None,
                design_dict={},
                crash_barrier_type=KEY_METALLIC_CRASH_BARRIER_TYPE[metallic_subtype_idx] if self.median_type == "Metallic Crash Barrier" else None
            )
            
            median_barriers_raw = build_median(
                span_length=self.span_length_L,
                deck_top_z=deck_out["deck_top_z"],
                carriageway_center_y=deck_out["carriageway_center_y"],
                design_dict=median_design_dict,
                median_type=self.median_type
            )
            
            median_barriers = []
            median_w_beams = []
            for mb in median_barriers_raw:
                if isinstance(mb, dict):
                    if mb.get("w_beams"):
                        median_w_beams.append(mb["w_beams"])
                    for k in ("kerb", "posts", "spacers"):
                        if mb.get(k):
                            crash_barrier_other.append(mb[k]) # Using same 'other' list for coloring
                            median_barriers.append(mb[k])
                else:
                    median_barriers.append(mb)

        # 8. RAILINGS
        railings = build_railings(
            span_length=self.span_length_L,
            deck_top_z=deck_out["deck_top_z"],
            total_deck_width=deck_out["total_deck_width"],
            footpath_config=self.footpath_config,
            railing_width=self.railing_width,
            railing_height=self.railing_height,
            rail_count=self.rail_count
        )

        supports = supports_tri + supports_cyl


        # FINAL RETURN
        return {
            "girders": girders,
            "girder_web": girder_web,
            "girder_flanges": girder_flanges,

            "stiffeners": stiffeners,

            "supports": supports, 
            "supports_tri": supports_tri,
            "supports_cyl": supports_cyl,


            "cross_bracings": cross_bracings,

            "deck_slab": deck_out["deck_slab"],
            "deck_textures": deck_out["deck_textures"],
            "deck_top_z": deck_out["deck_top_z"],
            "total_deck_width": deck_out["total_deck_width"],

            "crash_barriers": crash_barriers,
            "crash_barrier_w_beams": crash_barrier_w_beams,
            "median_barriers": median_barriers,
            "median_w_beams": median_w_beams,
            "railings": railings
        }


    def display_3dModel(self, component):

        hover_dict = {
                            KEY_CAD_GIRDER: "Girder",
                            KEY_CAD_STIFFENER: "Stiffener",
                            KEY_CAD_DECK: "Deck",
                            KEY_CAD_CRASH_BARRIER: "Crash Barrier",
                            KEY_CAD_RAILING: "Railing",
                            KEY_CAD_MEDIAN: "Median"
        }

        GIRDER_COLOR = Quantity_Color(72/255, 72/255, 54/255, Quantity_TOC_RGB)
        STIFFENER_COLOR = Quantity_Color(30/255, 30/255, 30/255, Quantity_TOC_RGB)
        DECK_COLOR = Quantity_Color(180/255, 180/255, 180/255, Quantity_TOC_RGB)
        BARRIER_COLOR = Quantity_Color(120/255, 120/255, 120/255, Quantity_TOC_RGB)
        BRACING_COLOR = Quantity_Color(60/255, 60/255, 60/255, Quantity_TOC_RGB)
        RAILING_COLOR = Quantity_Color(120/255, 120/255, 120/255, Quantity_TOC_RGB)
        MEDIAN_COLOR = Quantity_Color(120/255, 120/255, 120/255, Quantity_TOC_RGB)

        self.component = component  
        
        if self.component == "Girder":
            label = [KEY_CAD_GIRDER, hover_dict.get(KEY_CAD_GIRDER)]
            shapes = self.model_data["girders"]
            osdag_display_shape(self.display, shapes, color=GIRDER_COLOR, update=True, label=label, canvas=self.cad_widget)

        elif self.component == "Stiffener":
            label = [KEY_CAD_STIFFENER, hover_dict.get(KEY_CAD_STIFFENER)]
            shapes = self.model_data["stiffeners"]
            osdag_display_shape(self.display, shapes, color=STIFFENER_COLOR, update=True, label=label, canvas=self.cad_widget)

        elif self.component == "Cross Bracing":
            label = [KEY_CAD_CROSS_BRACING, hover_dict.get(KEY_CAD_CROSS_BRACING)]
            shapes = self.model_data["cross_bracings"]
            osdag_display_shape(self.display, shapes, color=BRACING_COLOR, update=True, label=label, canvas=self.cad_widget)

        elif self.component == "Deck":
            label = [KEY_CAD_DECK, hover_dict.get(KEY_CAD_DECK)]
            shapes = self.model_data["deck_slab"]
            osdag_display_shape(self.display, shapes, color=DECK_COLOR, update=True, label=label, canvas=self.cad_widget)

        elif self.component == "Crash Barrier":
            label = [KEY_CAD_CRASH_BARRIER, hover_dict.get(KEY_CAD_CRASH_BARRIER)]
            shapes = self.model_data["crash_barriers"]
            osdag_display_shape(self.display, shapes, color=BARRIER_COLOR, update=True, label=label, canvas=self.cad_widget)

        elif self.component == "Railing":
            label = [KEY_CAD_RAILING, hover_dict.get(KEY_CAD_RAILING)]
            shapes = self.model_data["railings"]
            osdag_display_shape(self.display, shapes, color=RAILING_COLOR, update=True, label=label, canvas=self.cad_widget)

        elif self.component == "Median":
            label = [KEY_CAD_MEDIAN, hover_dict.get(KEY_CAD_MEDIAN)]
            shapes = self.model_data["median_barriers"]
            osdag_display_shape(self.display, shapes, color=MEDIAN_COLOR, update=True, label=label, canvas=self.cad_widget)


def osdag_display_shape(display, shapes, material=None, texture=None, color=None, transparency=None, update=False, label=[], canvas=None):
    """
    Display a shape with edge styling and register with memory manager.
    
    All shapes and AIS objects are registered with OCCMemoryManager to prevent
    Python's garbage collector from freeing them while OCC/OpenGL are using them.
    """

    set_default_edge_style(shapes, display)
    ais_object = display.DisplayShape(shapes, material, texture, color, transparency, update=update)
    ais = ais_object[0] if isinstance(ais_object, list) else ais_object
    
    
    if canvas.model_ais_objects.get(label[0]) is None:
        canvas.model_ais_objects[label[0]] = [ais]
    else:
        canvas.model_ais_objects[label[0]] += [ais]
    
    # Activate selection mode for whole entity
    display.Context.Activate(ais, 0)


def color_the_edges(shp, display, color, width):
    """
    Colors the edges of a given shape.

    :param shp: The shape to color (TopoDS_Shape).
    :param display: The display context for rendering the shape.
    :param color: The color to apply to the edges (Quantity_Color or predefined constant like Quantity_NOC_BLACK).
    :param width: The width of the edges.
    """
    if not isinstance(shp, TopoDS_Shape):
        raise TypeError("The 'shp' parameter must be a valid TopoDS_Shape.")
    # shapeList = []
    try:
        # Initialize the edge explorer for the given shape
        Ex = TopExp_Explorer(shp, TopAbs_EDGE)
        # Get the display context
        ctx = display.Context
        # Iterate over the edges in the shape
        while Ex.More():
            # Extract the current edge
            aEdge = topods.Edge(Ex.Current())

            # Create an AIS_Shape for the edge
            ais_shape = AIS_Shape(aEdge)
            # Set the color
            ais_shape.SetColor(color)
            # Display the edge
            ctx.Display(ais_shape, False)

            # Store the edge for tracking
            # shapeList.append(aEdge)

            # Move to the next edge
            Ex.Next()

    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()  # This will print the full traceback

        raise RuntimeError(f"Error while coloring edges: {e}")
        
    # return shapeList



def set_default_edge_style(shp, display):
    try:
        color_the_edges(shp, display, Quantity_Color(Quantity_NOC_BLACK), 0.5)
    except Exception as e:
        # Edge styling is optional - don't crash if it fails
        pass
