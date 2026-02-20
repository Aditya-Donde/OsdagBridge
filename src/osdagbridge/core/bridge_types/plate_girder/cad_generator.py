"""
Plate Girder Bridge CAD Generator
==================================

This module generates complete 3D CAD models for plate girder bridges,
including girders, deck, crash barriers, railings, median, and cross bracing systems.

Components Generated:
    - Plate Girders: Web, top flange, bottom flange, stiffeners
    - Deck System: Concrete deck slab with textures
    - Safety Features: Crash barriers, railings, median
    - Bracing System: Cross bracings and end diaphragms
    - Supports: Bearing supports (triangular and cylindrical)

Features:
    - Configurable number of girders and spacing
    - Multiple bracing patterns (X, K)
    - Various end diaphragm options
    - Skew angle support
    - IRC-compliant crash barriers and railings
    - Flexible footpath and median configurations


"""

from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB, Quantity_NOC_BLACK
from OCC.Core.TopoDS import TopoDS_Shape
from OCC.Core.AIS import AIS_Shape
from OCC.Core.TopAbs import TopAbs_EDGE

# Component builder imports
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

from osdagbridge.core.bridge_types.plate_girder.dto import (
    BridgeParametersDTO,
)

# Component keys for CAD organization
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
    
    This class manages all parameters for a plate girder bridge and
    generates the complete 3D CAD geometry.
    
    Attributes:
        bridge_type: Type of bridge module
        
        Girder Parameters:
            span_length_L: Total span length
            girder_section_d: Clear web depth
            girder_section_bf: Top flange width
            girder_section_bf_b: Bottom flange width
            girder_section_tf: Top flange thickness
            girder_section_tf_b: Bottom flange thickness
            girder_section_tw: Web thickness
            num_girders: Number of parallel girders
            girder_spacing: Center-to-center girder spacing
            
        Geometry:
            skew_angle: Bridge skew angle in degrees (0 = no skew)
            
        Deck Parameters:
            carriageway_width: Width of traffic lanes
            deck_thickness: Deck slab thickness
            footpath_config: Footpath configuration ("NONE", "LEFT", "RIGHT", "BOTH")
            footpath_width: Width of footpath
            railing_width: Width of railing
            
        Safety Features:
            barrier_type: Type of crash barrier ("Rigid", "Semi-Rigid", "Flexible")
            crash_barrier_subtype: Specific barrier design
            enable_median: Whether to include median barrier
            median_type: Type of median barrier
            railing_type: Type of railing ("rcc", "steel")
            rail_count: Number of rails
            
        Bracing System:
            cross_bracing_spacing: Spacing between bracing frames
            cross_bracing_thickness: Thickness of bracing members
            bracing_type: Bracing pattern ("X" or "K")
            x_bracket_option: X-bracing bracket option
            k_top_bracket: K-bracing top bracket option
            cross_bracing_section_type: Section type for bracing
            cross_bracing_section_dims: Section dimensions
                For ANGLE/DOUBLE_ANGLE sections:
                    - leg_h: vertical leg height
                    - leg_w: horizontal leg width
                    - connection_type (DOUBLE_ANGLE only): "LONGER_LEG" or "SHORTER_LEG"
                      determines which legs are connected back-to-back
                For CHANNEL/DOUBLE_CHANNEL/I_SECTION:
                    - depth: overall depth
                    - flange_width: flange width
                    - web_thickness: web thickness
                    - flange_thickness: flange thickness
            
        End Diaphragm:
            end_diaphragm_type: Type of end treatment
            end_diaphragm_section: Section type for diaphragm
            end_diaphragm_dims: Diaphragm dimensions
            end_diaphragm_spacing: Reserved for future use
    """

    def __init__(self, bridge_type=KEY_MODULE_PG):

        self.bridge_type = bridge_type
        self.model_data = {}
        self.display = None
        self.cad_widget = None
        self.component = None

    def _set_parameters(self, design_params: BridgeParametersDTO):
        # GIRDER PARAMETERS
        self.span_length_L = design_params.span_length_L
        self.girder_section_d = design_params.girder_section_d
        self.girder_section_bf = design_params.girder_section_bf
        self.girder_section_bf_b = design_params.girder_section_bf_b
        self.girder_section_tf = design_params.girder_section_tf
        self.girder_section_tf_b = design_params.girder_section_tf_b
        self.girder_section_tw = design_params.girder_section_tw
        self.num_girders = design_params.num_girders
        self.girder_spacing = design_params.girder_spacing

        # GEOMETRY PARAMETERS
        self.skew_angle = design_params.skew_angle

        # DECK PARAMETERS
        self.carriageway_width = design_params.carriageway_width
        self.deck_thickness = design_params.deck_thickness
        self.footpath_config = design_params.footpath_config
        self.footpath_width = design_params.footpath_width
        self.railing_width = design_params.railing_width

        # CRASH BARRIER PARAMETERS
        self.barrier_type = design_params.barrier_type
        self.crash_barrier_subtype = design_params.crash_barrier_subtype

        # MEDIAN PARAMETERS
        self.enable_median = design_params.enable_median
        self.median_type = design_params.median_type

        # RAILING PARAMETERS
        self.rail_count = design_params.rail_count
        self.railing_type = design_params.railing_type

        # STIFFENER PARAMETERS
        self.include_intermediate_stiffeners = design_params.include_intermediate_stiffeners
        self.intermediate_stiffener_spacing = design_params.intermediate_stiffener_spacing
        self.intermediate_stiffener_thickness = design_params.intermediate_stiffener_thickness
        self.intermediate_stiffener_outstand = design_params.intermediate_stiffener_outstand

        self.num_end_stiffener_pairs = design_params.num_end_stiffener_pairs
        self.end_stiffener_thickness = design_params.end_stiffener_thickness
        self.end_stiffener_outstand = design_params.end_stiffener_outstand

        self.include_longitudinal_stiffeners = design_params.include_longitudinal_stiffeners
        self.num_longitudinal_stiffeners = design_params.num_longitudinal_stiffeners
        self.longitudinal_stiffener_thickness = design_params.longitudinal_stiffener_thickness
        self.longitudinal_stiffener_outstand = design_params.longitudinal_stiffener_outstand

        # SHEAR STUD PARAMETERS
        self.shear_stud_base_diameter = 50
        self.shear_stud_top_diameter = 70
        self.shear_stud_base_height = 150
        self.shear_stud_top_height = 50
        self.num_shear_studs_per_section = 4
        self.shear_stud_transverse_spacing = 305
        self.shear_stud_pitch = 500

        # CROSS BRACING PARAMETERS
        self.cross_bracing_spacing = design_params.cross_bracing_spacing
        self.bracing_type = design_params.bracing_type
        self.x_bracket_option = design_params.x_bracket_option
        self.k_top_bracket = design_params.k_top_bracket

        self.diagonal_section_type = design_params.diagonal_section_type
        self.diagonal_section_dims = {
            "leg_h": design_params.diagonal_section_dims.leg_h,
            "leg_w": design_params.diagonal_section_dims.leg_w,
            "connection_type": design_params.diagonal_section_dims.connection_type,
        }
        self.diagonal_thickness = design_params.diagonal_thickness

        self.top_chord_section_type = design_params.top_chord_section_type
        self.top_chord_section_dims = {
            "leg_h": design_params.top_chord_section_dims.leg_h,
            "leg_w": design_params.top_chord_section_dims.leg_w,
            "connection_type": design_params.top_chord_section_dims.connection_type,
        }
        self.top_chord_thickness = design_params.top_chord_thickness

        self.bottom_chord_section_type = design_params.bottom_chord_section_type
        self.bottom_chord_section_dims = {
            "leg_h": design_params.bottom_chord_section_dims.leg_h,
            "leg_w": design_params.bottom_chord_section_dims.leg_w,
            "connection_type": design_params.bottom_chord_section_dims.connection_type,
        }
        self.bottom_chord_thickness = design_params.bottom_chord_thickness

        # END DIAPHRAGM PARAMETERS
        self.end_diaphragm_type = design_params.end_diaphragm_type
        self.end_diaphragm_spacing = design_params.end_diaphragm_spacing
        self.end_diaphragm_bracing_type = design_params.end_diaphragm_bracing_type

        self.end_diaphragm_diagonal_section_type = design_params.end_diaphragm_diagonal_section_type
        self.end_diaphragm_diagonal_section_dims = {
            "leg_h": design_params.end_diaphragm_diagonal_section_dims.leg_h,
            "leg_w": design_params.end_diaphragm_diagonal_section_dims.leg_w,
            "connection_type": design_params.end_diaphragm_diagonal_section_dims.connection_type,
        }
        self.end_diaphragm_diagonal_thickness = design_params.end_diaphragm_diagonal_thickness

        self.end_diaphragm_top_chord_section_type = design_params.end_diaphragm_top_chord_section_type
        self.end_diaphragm_top_chord_section_dims = {
            "leg_h": design_params.end_diaphragm_top_chord_section_dims.leg_h,
            "leg_w": design_params.end_diaphragm_top_chord_section_dims.leg_w,
            "connection_type": design_params.end_diaphragm_top_chord_section_dims.connection_type,
        }
        self.end_diaphragm_top_chord_thickness = design_params.end_diaphragm_top_chord_thickness

        self.end_diaphragm_bottom_chord_section_type = design_params.end_diaphragm_bottom_chord_section_type
        self.end_diaphragm_bottom_chord_section_dims = {
            "leg_h": design_params.end_diaphragm_bottom_chord_section_dims.leg_h,
            "leg_w": design_params.end_diaphragm_bottom_chord_section_dims.leg_w,
            "connection_type": design_params.end_diaphragm_bottom_chord_section_dims.connection_type,
        }
        self.end_diaphragm_bottom_chord_thickness = design_params.end_diaphragm_bottom_chord_thickness

        self.end_diaphragm_section = design_params.end_diaphragm_section
        self.end_diaphragm_dims = {
            "depth": design_params.end_diaphragm_dims.depth,
            "flange_width": design_params.end_diaphragm_dims.flange_width,
            "web_thickness": design_params.end_diaphragm_dims.web_thickness,
            "flange_thickness": design_params.end_diaphragm_dims.flange_thickness,
        }   

    def generate(self, design_params: BridgeParametersDTO):
        """
        Generate complete bridge CAD geometry.
        
        This method orchestrates the creation of all bridge components:
        1. Plate girders (web, flanges, stiffeners)
        2. Cross bracing system
        3. Deck slab
        4. Crash barriers
        5. Median barriers (if enabled)
        6. Railings
        7. Support structures
        
        Returns:
            dict: Dictionary containing all generated CAD components:
                - girders: List of girder components (web + flanges)
                - girder_web: List of web components only
                - girder_flanges: List of flange components only
                - stiffeners: List of stiffener components
                - supports: All support structures
                - supports_tri: Triangular supports
                - supports_cyl: Cylindrical supports
                - cross_bracings: Cross bracing members
                - deck_slab: Deck slab geometry
                - deck_textures: Deck surface textures
                - deck_top_z: Z-coordinate of deck top surface
                - total_deck_width: Total width of deck
                - crash_barriers: Crash barrier components
                - crash_barrier_w_beams: W-beam components (if metallic)
                - median_barriers: Median barrier components
                - median_w_beams: Median W-beams (if metallic)
                - railings: Railing components
        """

        self._set_parameters(design_params)
        
        # HELPER FUNCTIONS
        
        import math
        from OCC.Core.gp import gp_Trsf, gp_Vec
        from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform

        def _translate(shape, dx=0, dy=0, dz=0):
            """
            Translate a shape by the specified offsets.
            
            Args:
                shape: TopoDS_Shape to translate
                dx: X-offset
                dy: Y-offset
                dz: Z-offset
                
            Returns:
                Translated TopoDS_Shape
            """
            trsf = gp_Trsf()
            trsf.SetTranslation(gp_Vec(dx, dy, dz))
            return BRepBuilderAPI_Transform(shape, trsf, True).Shape()
        
        def _calculate_skew_offset(lateral_position, reference_position=0):
            """
            Calculate longitudinal offset due to skew angle.
            
            This implements the plan-view geometric offset for skewed bridges:
            longitudinal_shift = lateral_distance x tan(skew_angle)
            
            Args:
                lateral_position: Transverse position (Y-coordinate)
                reference_position: Reference lateral position with zero offset
                
            Returns:
                Longitudinal offset (X-coordinate shift)
            """
            if self.skew_angle == 0:
                return 0.0
            
            skew_rad = math.radians(self.skew_angle)
            lateral_distance = lateral_position - reference_position
            return lateral_distance * math.tan(skew_rad)

        # STEP 1: BUILD SINGLE PLATE GIRDER GEOMETRY
        
        pg = build_plate_girder_geometry(
            D=self.girder_section_d,
            tw=self.girder_section_tw,
            length=self.span_length_L,
            T_ft=self.girder_section_tf,
            T_fb=self.girder_section_tf_b,
            B_ft=self.girder_section_bf,
            B_fb=self.girder_section_bf_b,
            include_intermediate_stiffeners=self.include_intermediate_stiffeners,
            intermediate_stiffener_spacing=self.intermediate_stiffener_spacing,
            intermediate_stiffener_thickness=self.intermediate_stiffener_thickness,
            chamfer_length=40,
            num_end_stiffener_pairs=self.num_end_stiffener_pairs,
            T_es=self.end_stiffener_thickness,
            intermediate_stiffener_outstand=self.intermediate_stiffener_outstand,
            end_stiffener_outstand=self.end_stiffener_outstand,
            include_longitudinal_stiffeners=self.include_longitudinal_stiffeners,
            num_longitudinal_stiffeners=self.num_longitudinal_stiffeners,
            longitudinal_stiffener_thickness=self.longitudinal_stiffener_thickness,
            longitudinal_stiffener_outstand=self.longitudinal_stiffener_outstand,
            shear_stud_base_diameter=self.shear_stud_base_diameter,
            shear_stud_top_diameter=self.shear_stud_top_diameter,
            shear_stud_base_height=self.shear_stud_base_height,
            shear_stud_top_height=self.shear_stud_top_height,
            num_shear_studs_per_section=self.num_shear_studs_per_section,
            shear_stud_transverse_spacing=self.shear_stud_transverse_spacing,
            shear_stud_pitch=self.shear_stud_pitch
        )

        # STEP 2: PLACE MULTIPLE GIRDERS WITH SKEW OFFSET
        
        girders = []
        stiffeners = []
        shear_studs = []
        girder_web = []
        girder_flanges = []

        total_width = (self.num_girders - 1) * self.girder_spacing
        reference_position = 0.0  # Centerline reference for skew

        for i in range(self.num_girders):
            # Calculate transverse offset (Y-direction)
            y_offset = (i * self.girder_spacing) - (total_width / 2)
            
            # Calculate longitudinal offset due to skew (X-direction)
            x_offset = _calculate_skew_offset(y_offset, reference_position)

            # Place web
            web = _translate(pg["web"], dx=x_offset, dy=y_offset)
            girders.append(web)
            girder_web.append(web)

            # Place top flange
            top_flange = _translate(pg["top_flange"], dx=x_offset, dy=y_offset)
            girders.append(top_flange)
            girder_flanges.append(top_flange)

            # Place bottom flange
            bottom_flange = _translate(pg["bottom_flange"], dx=x_offset, dy=y_offset)
            girders.append(bottom_flange)
            girder_flanges.append(bottom_flange)

            # Place stiffeners (follow parent girder's offset)
            for stiff in pg["stiffeners"]:
                stiffeners.append(
                    _translate(stiff, dx=x_offset, dy=y_offset)
                )

            # Place shear studs
            for stud in pg.get("shear_studs", []):
                shear_studs.append(
                    _translate(stud, dx=x_offset, dy=y_offset)
                )

        # STEP 3: PLACE SUPPORT STRUCTURES
        
        supports_tri = []
        supports_cyl = []

        for i in range(self.num_girders):
            # Calculate offsets (same as girders)
            y_offset = (i * self.girder_spacing) - (total_width / 2)
            x_offset = _calculate_skew_offset(y_offset, reference_position)

            # Place triangular supports
            for s in pg["supports_tri"]:
                supports_tri.append(_translate(s, dx=x_offset, dy=y_offset))

            # Place cylindrical supports
            for s in pg["supports_cyl"]:
                supports_cyl.append(_translate(s, dx=x_offset, dy=y_offset))

        # STEP 4: CALCULATE REFERENCE Z-LEVELS
        
        # Bracing girder depth (for cross bracing placement)
        # Use clear web depth D, so top/bottom are at +/- D/2
        bracing_girder_depth = self.girder_section_d

        # Top of girder for deck placement
        girder_top_z = (self.girder_section_d / 2) + self.girder_section_tf

        # STEP 5: BUILD CROSS BRACING SYSTEM
        
        cross_bracings = build_cross_bracings(
            span_length_L=self.span_length_L,
            num_girders=self.num_girders,
            girder_spacing=self.girder_spacing,
            girder_depth=bracing_girder_depth,
            flange_thickness=self.girder_section_tf,
            flange_width=self.girder_section_bf,
            
            # Internal bracing configuration
            bracing_type=self.bracing_type,
            
            # Diagonal members
            diagonal_section_type=self.diagonal_section_type,
            diagonal_section_dims=self.diagonal_section_dims,
            diagonal_thickness=self.diagonal_thickness,
            
            # Top chord/bracket
            top_chord_section_type=self.top_chord_section_type,
            top_chord_section_dims=self.top_chord_section_dims,
            top_chord_thickness=self.top_chord_thickness,
            
            # Bottom chord/bracket
            bottom_chord_section_type=self.bottom_chord_section_type,
            bottom_chord_section_dims=self.bottom_chord_section_dims,
            bottom_chord_thickness=self.bottom_chord_thickness,
            
            panel_spacing=self.cross_bracing_spacing,
            bracket_option=self.x_bracket_option,
            top_bracket=self.k_top_bracket,
            skew_angle=self.skew_angle,
            
            # End diaphragm configuration
            end_diaphragm_type=self.end_diaphragm_type,
            end_diaphragm_bracing_type=self.end_diaphragm_bracing_type,
            
            # End diaphragm diagonal members
            end_diaphragm_diagonal_section_type=self.end_diaphragm_diagonal_section_type,
            end_diaphragm_diagonal_section_dims=self.end_diaphragm_diagonal_section_dims,
            end_diaphragm_diagonal_thickness=self.end_diaphragm_diagonal_thickness,
            
            # End diaphragm top chord
            end_diaphragm_top_chord_section_type=self.end_diaphragm_top_chord_section_type,
            end_diaphragm_top_chord_section_dims=self.end_diaphragm_top_chord_section_dims,
            end_diaphragm_top_chord_thickness=self.end_diaphragm_top_chord_thickness,
            
            # End diaphragm bottom chord
            end_diaphragm_bottom_chord_section_type=self.end_diaphragm_bottom_chord_section_type,
            end_diaphragm_bottom_chord_section_dims=self.end_diaphragm_bottom_chord_section_dims,
            end_diaphragm_bottom_chord_thickness=self.end_diaphragm_bottom_chord_thickness,
            
            # For Rolled/Welded beam diaphragms
            end_diaphragm_section=self.end_diaphragm_section,
            end_diaphragm_dims=self.end_diaphragm_dims,
            end_diaphragm_spacing=self.end_diaphragm_spacing
        )

        # STEP 6: CONFIGURE CRASH BARRIER SPECIFICATIONS (IRC 5:2015)
        
        from osdagbridge.core.utils.codes.irc5_2015 import IRC5_2015
        from osdagbridge.core.utils.common import (
            KEY_CRASH_BARRIER_TYPE,
            VALUES_FOOTPATH,
            KEY_RAILING_TYPE,
            KEY_RIGID_CRASH_BARRIER_TYPE,
            KEY_METALLIC_CRASH_BARRIER_TYPE,
            KEY_MEDIAN_TYPE,
            VALUES_RAILING_TYPE
        )

        # Map barrier types to indices
        barrier_type_map = {"Flexible": 0, "Semi-Rigid": 1, "Rigid": 2}
        barrier_idx = barrier_type_map.get(self.barrier_type, 2)
        
        rigid_subtype_map = {"IRC-5R": 0, "High Containment": 1}
        metallic_subtype_map = {"Single W-beam": 0, "Double W-beam": 1}

        # Map railing types
        railing_map = {
            VALUES_RAILING_TYPE[0]: KEY_RAILING_TYPE[0],  # RCC
            VALUES_RAILING_TYPE[1]: KEY_RAILING_TYPE[1],  # Steel
        }
        
        # Robust railing selection
        selected_railing_key = railing_map.get(self.railing_type)
        if selected_railing_key is None:
            if "steel" in self.railing_type.lower():
                selected_railing_key = KEY_RAILING_TYPE[1]
            else:
                selected_railing_key = KEY_RAILING_TYPE[0]

        # Force RCC railing for Semi-Rigid barriers
        if self.barrier_type != "Rigid":
            selected_railing_key = KEY_RAILING_TYPE[0]

        # Determine railing width
        if selected_railing_key == KEY_RAILING_TYPE[1]:  # Steel
            actual_railing_width = 200
        else:
            actual_railing_width = 275

        # Populate design dictionary based on barrier type
        if self.barrier_type == "Rigid":
            rigid_subtype_idx = rigid_subtype_map.get(self.crash_barrier_subtype, 0)
            design_dict = IRC5_2015.cl_109_6_3_shapes(
                barrier_type=KEY_CRASH_BARRIER_TYPE[barrier_idx],
                footpath=VALUES_FOOTPATH[0] if self.footpath_config == "NONE" else VALUES_FOOTPATH[1],
                railing_type=selected_railing_key,
                design_dict={},
                crash_barrier_type=KEY_RIGID_CRASH_BARRIER_TYPE[rigid_subtype_idx]
            )
            actual_base_width = design_dict.get("crash_barrier_width", 450)
        else:
            # Semi-Rigid / Metallic barrier
            metallic_subtype_idx = metallic_subtype_map.get(self.crash_barrier_subtype, 0)
            design_dict = IRC5_2015.cl_109_6_3_shapes(
                barrier_type=KEY_CRASH_BARRIER_TYPE[1],
                footpath=VALUES_FOOTPATH[0] if self.footpath_config == "NONE" else VALUES_FOOTPATH[1],
                railing_type=selected_railing_key,
                design_dict={},
                crash_barrier_type=KEY_METALLIC_CRASH_BARRIER_TYPE[metallic_subtype_idx]
            )
            actual_base_width = design_dict.get("kerb_bottom_width", 550)
        
        # Ensure railing parameters are in design dictionary
        if selected_railing_key == KEY_RAILING_TYPE[1]:
            design_dict["railing_type"] = "steel"
            design_dict["railing_width"] = 200
        else:
            design_dict["railing_type"] = "RCC"
            design_dict["railing_width"] = 275

        # STEP 7: BUILD DECK SYSTEM
        
        deck_out = build_deck(
            span_length_L=self.span_length_L,
            girder_section_d=girder_top_z,
            deck_thickness=self.deck_thickness,
            footpath_config=self.footpath_config,
            carriageway_width=self.carriageway_width,
            crash_barrier_base_width=actual_base_width,
            footpath_width=self.footpath_width,
            railing_width=actual_railing_width,
            skew_angle=self.skew_angle
        )

        # STEP 8: BUILD CRASH BARRIERS
        
        crash_barrier_w_beams = []
        crash_barrier_other = []

        crash_barriers_raw = build_crash_barriers(
            span_length_L=self.span_length_L,
            deck_top_z=deck_out["deck_top_z"],
            footpath_config=self.footpath_config,
            carriageway_width=self.carriageway_width,
            footpath_width=self.footpath_width,
            railing_width=actual_railing_width,
            design_dict=design_dict,
            barrier_type=self.barrier_type,
            skew_angle=self.skew_angle
        )

        crash_barriers = []

        # Separate W-beams from other barrier components
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

        # STEP 9: BUILD MEDIAN BARRIERS (IF ENABLED)
        
        median_barriers = []
        median_w_beams = []
        
        if self.enable_median:
            # Get median design specifications from IRC 5:2015
            median_type_map = {
                "Raised Kerb": 0, 
                "RCC Crash Barrier": 1, 
                "Metallic Crash Barrier": 2
            }
            median_idx = median_type_map.get(self.median_type, 1)
            
            metallic_subtype_idx = metallic_subtype_map.get(self.crash_barrier_subtype, 0)
            
            median_design_dict = IRC5_2015.cl_109_6_3_shapes(
                barrier_type=KEY_MEDIAN_TYPE[median_idx],
                footpath=VALUES_FOOTPATH[0],
                railing_type=None,
                design_dict={},
                crash_barrier_type=KEY_METALLIC_CRASH_BARRIER_TYPE[metallic_subtype_idx] 
                    if self.median_type == "Metallic Crash Barrier" else None
            )
            
            median_barriers_raw = build_median(
                span_length=self.span_length_L,
                deck_top_z=deck_out["deck_top_z"],
                carriageway_center_y=deck_out["carriageway_center_y"],
                design_dict=median_design_dict,
                median_type=self.median_type,
                skew_angle=self.skew_angle
            )
            
            # Separate W-beams from other median components
            for mb in median_barriers_raw:
                if isinstance(mb, dict):
                    if mb.get("w_beams"):
                        median_w_beams.append(mb["w_beams"])
                    for k in ("kerb", "posts", "spacers"):
                        if mb.get(k):
                            crash_barrier_other.append(mb[k])
                            median_barriers.append(mb[k])
                else:
                    median_barriers.append(mb)

        # STEP 10: BUILD RAILINGS
        
        railings = build_railings(
            span_length=self.span_length_L,
            deck_top_z=deck_out["deck_top_z"],
            total_deck_width=deck_out["total_deck_width"],
            footpath_config=self.footpath_config,
            design_dict=design_dict,
            skew_angle=self.skew_angle
        )

        # STEP 11: CONSOLIDATE SUPPORT STRUCTURES
        
        supports = supports_tri + supports_cyl

        # RETURN ALL GENERATED COMPONENTS
        
        return {
            # Girder components
            "girders": girders,
            "girder_web": girder_web,
            "girder_flanges": girder_flanges,
            
            # Stiffeners
            "stiffeners": stiffeners,
            
            # Shear Studs
            "shear_studs": shear_studs,
            
            # Support structures
            "supports": supports,
            "supports_tri": supports_tri,
            "supports_cyl": supports_cyl,
            
            # Cross bracing system
            "cross_bracings": cross_bracings,
            
            # Deck system
            "deck_slab": deck_out["deck_slab"],
            "deck_textures": deck_out["deck_textures"],
            "deck_top_z": deck_out["deck_top_z"],
            "total_deck_width": deck_out["total_deck_width"],
            
            # Crash barriers
            "crash_barriers": crash_barriers,
            "crash_barrier_w_beams": crash_barrier_w_beams,
            
            # Median barriers
            "median_barriers": median_barriers,
            "median_w_beams": median_w_beams,
            
            # Railings
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
