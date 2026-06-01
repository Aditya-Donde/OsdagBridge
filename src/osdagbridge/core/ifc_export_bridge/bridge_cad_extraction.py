import math
import dataclasses
import numpy as np


def _to_dims_dict(dims) -> dict:
    """Normalize a section dims value to a plain dict regardless of its type."""
    if dims is None:
        return {}
    if isinstance(dims, dict):
        return dims
    if dataclasses.is_dataclass(dims):
        return dataclasses.asdict(dims)
    return vars(dims) if hasattr(dims, '__dict__') else {}

# Osdag Core Imports
from osdagbridge.core.utils.codes.irc5_2015 import IRC5_2015
from osdagbridge.core.utils.common import (
    KEY_SPAN, KEY_TS_NO_OF_GIRDERS, KEY_TS_GIRDER_SPACING, KEY_SKEW_ANGLE,
    KEY_CARRIAGEWAY_WIDTH, KEY_TS_DECK_THICKNESS, KEY_FOOTPATH,
    KEY_RAILING_WIDTH, KEY_INCLUDE_MEDIAN, KEY_CRASH_BARRIER_TYPE,
    KEY_RIGID_CRASH_BARRIER_TYPE, KEY_METALLIC_CRASH_BARRIER_TYPE,
    KEY_MEDIAN_TYPE, KEY_RAILING_TYPE, VALUES_FOOTPATH, VALUES_RAILING_TYPE
)
from osdagbridge.core.bridge_components.super_structure.deck.builder import (
    calculate_deck_width,
    calculate_carriageway_center_y
)
from osdagbridge.core.utils.common import (
    DEFAULT_GIRDER_SPACING
)
from osdagbridge.core.bridge_components.super_structure.crash_barrier.builder import (
    calculate_carriageway_offset
)
from osdagbridge.core.bridge_components.super_structure.plate_girder.builder import (
    END_STIFFENER_SPACING
)
from osdagbridge.desktop.cad.irc5_geometry import (
    CrashBarrierGeometry,
    MedianGeometry,
    RailingGeometry
)

class ExtractedObject:
    """A generic mock object to hold geometric parameters for the GeometryMapper."""
    def __init__(self, obj_class, **kwargs):
        self._class_name = obj_class
        for k, v in kwargs.items():
            setattr(self, k, v)

class PlateGirderIFCExtractor:
    """
    Extracts structural objects parametrically. Reconstructs locations 
    to bypass native OpenCASCADE B-Rep tessellation for cleaner IFC output.
    """
    def __init__(self, cad_generator):
        self.cad = cad_generator
        
    def _calculate_skew_offset(self, lateral_position, reference_position=0):
        if self.cad.skew_angle == 0:
            return 0.0
        skew_rad = math.radians(self.cad.skew_angle)
        return (lateral_position - reference_position) * math.tan(skew_rad)

    def _build_design_dict(self):
        """Replicates Osdag Step 6 mapping to get exact IRC 5 dimensions."""
        barrier_type_map = {"Flexible": 0, "Semi-Rigid": 1, "Rigid": 2}
        barrier_idx = barrier_type_map.get(self.cad.barrier_type, 2)
        
        rigid_subtype_map = {"IRC-5R": 0, "High Containment": 1}
        metallic_subtype_map = {"Single W-beam": 0, "Double W-beam": 1}

        railing_map = {
            VALUES_RAILING_TYPE[0]: KEY_RAILING_TYPE[0],  # RCC
            VALUES_RAILING_TYPE[1]: KEY_RAILING_TYPE[1],  # Steel
        }
        
        selected_railing_key = railing_map.get(self.cad.railing_type)
        if selected_railing_key is None:
            selected_railing_key = KEY_RAILING_TYPE[1] if "steel" in str(self.cad.railing_type).lower() else KEY_RAILING_TYPE[0]

        if self.cad.barrier_type != "Rigid":
            selected_railing_key = KEY_RAILING_TYPE[0]

        if self.cad.barrier_type == "Rigid":
            rigid_subtype_idx = rigid_subtype_map.get(self.cad.crash_barrier_subtype, 0)
            design_dict = IRC5_2015.cl_109_6_3_shapes(
                barrier_type=KEY_CRASH_BARRIER_TYPE[barrier_idx],
                footpath=VALUES_FOOTPATH[0] if self.cad.footpath_config == "NONE" else VALUES_FOOTPATH[1],
                railing_type=selected_railing_key,
                design_dict={},
                crash_barrier_type=KEY_RIGID_CRASH_BARRIER_TYPE[rigid_subtype_idx]
            )
            actual_base_width = design_dict.get("crash_barrier_width", 500)
        else:
            metallic_subtype_idx = metallic_subtype_map.get(self.cad.crash_barrier_subtype, 0)
            design_dict = IRC5_2015.cl_109_6_3_shapes(
                barrier_type=KEY_CRASH_BARRIER_TYPE[1],
                footpath=VALUES_FOOTPATH[0] if self.cad.footpath_config == "NONE" else VALUES_FOOTPATH[1],
                railing_type=selected_railing_key,
                design_dict={},
                crash_barrier_type=KEY_METALLIC_CRASH_BARRIER_TYPE[metallic_subtype_idx]
            )
            # Standard Osdag reserved width for crash barriers is 500mm (0.5m)
            actual_base_width = design_dict.get("kerb_bottom_width", 500)
        
        # Standard Osdag Railing width is 375mm (0.375m)
        actual_railing_width = 375
        return design_dict, actual_base_width, actual_railing_width
    def extract(self):
        design_dict, actual_base_width, actual_railing_width = self._build_design_dict()
        
        # Step 1: Calculate dynamic deck width
        total_width = self._calculate_total_deck_width(actual_base_width, actual_railing_width)
        
        # Step 2: Solve for structural girder layout
        n_girders, spacing, overhang = self._solve_girder_layout(total_width)
        
        return {
            "girders": self._extract_girders(n_girders, spacing),
            "stiffeners": self._extract_stiffeners(n_girders, spacing),
            "cross_bracings": self._extract_cross_bracings(n_girders, spacing),
            "deck_slab": self._extract_deck_slab(total_width),
            "crash_barriers": self._extract_safety_components(total_width, actual_base_width, actual_railing_width),
            "supports": self._extract_supports(n_girders, spacing)
        }

    def _solve_girder_layout(self, total_width):
        """
        Dynamically solves for n, spacing, and overhang based on Osdag's structural sizing rules.
        OverallBridgeWidth = (n - 1) * spacing + 2 * overhang
        """
        target_s = getattr(self.cad, 'girder_spacing', DEFAULT_GIRDER_SPACING * 1000)
        target_o = getattr(self.cad, 'deck_overhang', target_s / 2.0)
        
        # Rule: n = Width / TargetSpacing (assuming overhang = spacing/2)
        n = max(2, int(round(total_width / target_s)))
        
        # Adjust spacing and overhang to fit width exactly
        # We keep overhang at target_o if possible, and solve for s
        if n > 1:
            actual_s = (total_width - 2 * target_o) / (n - 1)
            actual_o = target_o
        else:
            actual_s = 0
            actual_o = total_width / 2.0
            
        return n, actual_s, actual_o

    def _extract_girders(self, n_girders, spacing):
        girders = []
        total_structural_width = (n_girders - 1) * spacing
        d = self.cad.girder_section_d
        tw = self.cad.girder_section_tw
        L = self.cad.span_length_L
        
        for i in range(n_girders):
            y_offset = (i * spacing) - (total_structural_width / 2.0)
            x_offset = self._calculate_skew_offset(y_offset)
            
            # Girders span along +X global vector
            uDir = [1, 0, 0] # Z extrusion direction
            wDir = [0, 1, 0] # X axis direction for Profile
            # Thus Profile spans Local X (global Y) and Local Y (global Z)
            
            # Web
            girders.append(ExtractedObject(
                "Plate", T=tw, L=d, W=L, 
                origin=[x_offset, y_offset, 0], uDir=uDir, wDir=wDir, ifc_name=f"Girder Web {i+1}"
            ))
            
            # Top Flange
            girders.append(ExtractedObject(
                "Plate", 
                T=self.cad.girder_section_bf, L=self.cad.girder_section_tf, W=L, 
                origin=[x_offset, y_offset, (d + self.cad.girder_section_tf) / 2], 
                uDir=uDir, wDir=wDir, ifc_name=f"Top Flange {i+1}"
            ))
            
            # Bottom Flange
            girders.append(ExtractedObject(
                "Plate", 
                T=self.cad.girder_section_bf_b, L=self.cad.girder_section_tf_b, W=L, 
                origin=[x_offset, y_offset, -(d + self.cad.girder_section_tf_b) / 2], 
                uDir=uDir, wDir=wDir, ifc_name=f"Bottom Flange {i+1}"
            ))
            
        return girders

    def _extract_stiffeners(self, n_girders, spacing):
        stiffeners = []
        D = self.cad.girder_section_d
        tw = self.cad.girder_section_tw
        L = self.cad.span_length_L
        B_ft = self.cad.girder_section_bf
        B_fb = self.cad.girder_section_bf_b
        T_es = self.cad.end_stiffener_thickness
        
        default_stiff_width = (min(B_ft, B_fb) - tw) / 2
        int_stiff_width = self.cad.intermediate_stiffener_outstand if self.cad.intermediate_stiffener_outstand else default_stiff_width
        end_stiff_width = self.cad.end_stiffener_outstand if self.cad.end_stiffener_outstand else default_stiff_width
        
        end_stiffener_gap = (T_es / 2.0)
        
        total_width = (n_girders - 1) * spacing
        
        # Stiffeners Extrude UP (global Z) alongside the web depth
        # For Vertical Stiffeners: T (Profile Width) maps to local X (global X -> Thickness)
        #                          L (Profile Height) maps to local Y (global Y -> Outstand Width)
        #                          W (Extrusion) maps to local Z (global Z -> D)
        uDir_vert = [0, 0, 1] 
        wDir_vert = [1, 0, 0]
        
        for i in range(n_girders):
            y_offset = (i * spacing) - (total_width / 2)
            
            # Intermediate Stiffeners
            if self.cad.include_intermediate_stiffeners:
                spacing_stiff = self.cad.intermediate_stiffener_spacing
                num_panels = max(1, int(L // spacing_stiff))
                end_zone = end_stiffener_gap + (self.cad.num_end_stiffener_pairs - 1) * END_STIFFENER_SPACING + END_STIFFENER_SPACING
                
                for j in range(1, num_panels):
                    x_dist = j * spacing_stiff
                    if x_dist <= end_zone or x_dist >= (L - end_zone): continue
                    
                    x_shift = self._calculate_skew_offset(y_offset)
                    # Right Side Stiffener
                    stiffeners.append(ExtractedObject("StiffenerPlate", T=self.cad.intermediate_stiffener_thickness, L=int_stiff_width, W=D,
                        origin=[x_shift + x_dist, y_offset + tw/2 + int_stiff_width/2, -D/2], uDir=uDir_vert, wDir=wDir_vert, ifc_name=f"Intermediate Stiffener {i+1}"))
                    # Left Side Stiffener
                    stiffeners.append(ExtractedObject("StiffenerPlate", T=self.cad.intermediate_stiffener_thickness, L=int_stiff_width, W=D,
                        origin=[x_shift + x_dist, y_offset - tw/2 - int_stiff_width/2, -D/2], uDir=uDir_vert, wDir=wDir_vert, ifc_name=f"Intermediate Stiffener {i+1}"))

            # End Stiffeners
            end_positions = []
            for j in range(self.cad.num_end_stiffener_pairs):
                end_positions.extend([end_stiffener_gap + j * END_STIFFENER_SPACING, L - end_stiffener_gap - j * END_STIFFENER_SPACING])
                
            for x_pos in end_positions:
                x_shift = self._calculate_skew_offset(y_offset)
                stiffeners.append(ExtractedObject("StiffenerPlate", T=T_es, L=end_stiff_width, W=D,
                        origin=[x_shift + x_pos, y_offset + tw/2 + end_stiff_width/2, -D/2], uDir=uDir_vert, wDir=wDir_vert, ifc_name=f"End Stiffener {i+1}"))
                stiffeners.append(ExtractedObject("StiffenerPlate", T=T_es, L=end_stiff_width, W=D,
                        origin=[x_shift + x_pos, y_offset - tw/2 - end_stiff_width/2, -D/2], uDir=uDir_vert, wDir=wDir_vert, ifc_name=f"End Stiffener {i+1}"))
                        
            # Longitudinal Stiffeners extrude laterally along the beam
            if self.cad.include_longitudinal_stiffeners:
                long_stiff_width = self.cad.longitudinal_stiffener_outstand if self.cad.longitudinal_stiffener_outstand else default_stiff_width
                long_stiff_start = T_es
                long_stiff_len = L - 2 * long_stiff_start
                
                uDir_long = [1, 0, 0] # global X
                wDir_long = [0, 1, 0] # Profile local X maps to global Y
                
                heights = [D/2 - D/3] if self.cad.num_longitudinal_stiffeners == 1 else [D/2 - D/3, D/2 - 2*D/3]
                for h in heights:
                    x_shift = self._calculate_skew_offset(y_offset)
                    # Right Side
                    stiffeners.append(ExtractedObject("Plate", T=long_stiff_width, L=self.cad.longitudinal_stiffener_thickness, W=long_stiff_len,
                        origin=[x_shift + long_stiff_start, y_offset + tw/2 + long_stiff_width/2, h], 
                        uDir=uDir_long, wDir=wDir_long, ifc_name=f"Longitudinal Stiffener {i+1} R"))
                    # Left Side
                    stiffeners.append(ExtractedObject("Plate", T=long_stiff_width, L=self.cad.longitudinal_stiffener_thickness, W=long_stiff_len,
                        origin=[x_shift + long_stiff_start, y_offset - tw/2 - long_stiff_width/2, h], 
                        uDir=uDir_long, wDir=wDir_long, ifc_name=f"Longitudinal Stiffener {i+1} L"))
                        
        return stiffeners

    def _extract_cross_bracings(self, n_girders, spacing):
        braces = []
        n_internal = int(self.cad.span_length_L / self.cad.cross_bracing_spacing) - 1
        n_total = n_internal + 2
        spacing_x = self.cad.span_length_L / (n_total - 1) if n_total > 1 else 0
        x_positions = [i * spacing_x for i in range(n_total)]
        total_width = (n_girders - 1) * spacing
        
        depth = self.cad.girder_section_d
        z_bot = -depth / 2
        z_top = depth / 2
        
        def add_member(p1, p2, thickness, sec_type, dims, roll, name):
            braces.append(ExtractedObject("StructuralMember", p1=p1, p2=p2, T=thickness, sec_type=sec_type, dims=_to_dims_dict(dims), roll=roll, ifc_name=name))
            
        def extract_bay(x, yL, yR, is_end, is_first):
            x_l = x + self._calculate_skew_offset(yL)
            x_r = x + self._calculate_skew_offset(yR)
            x_m = x + self._calculate_skew_offset((yL + yR) / 2)
            ym = (yL + yR) / 2
            
            # Sub-function for type dispatch
            def build_bracing(b_type, d_sec, d_dims, d_t, t_sec, t_dims, t_t, b_sec, b_dims, b_t, bracket_opt, k_top_opt):
                if b_type == "X":
                    add_member([x_l, yL, z_top], [x_r, yR, z_bot], d_t, d_sec, d_dims, +1, "Diagonal Brace")
                    add_member([x_l, yL, z_bot], [x_r, yR, z_top], d_t, d_sec, d_dims, -1, "Diagonal Brace")
                    if bracket_opt in ("LOWER", "BOTH"):
                        add_member([x_l, yL, z_bot], [x_r, yR, z_bot], b_t, b_sec, b_dims, +1, "Bottom Chord")
                    if bracket_opt in ("UPPER", "BOTH"):
                        add_member([x_l, yL, z_top], [x_r, yR, z_top], t_t, t_sec, t_dims, +1, "Top Chord")
                        
                elif b_type == "K":
                    add_member([x_l, yL, z_top], [x_m, ym, z_bot], d_t, d_sec, d_dims, +1, "Diagonal Brace")
                    add_member([x_r, yR, z_top], [x_m, ym, z_bot], d_t, d_sec, d_dims, -1, "Diagonal Brace")
                    add_member([x_l, yL, z_bot], [x_r, yR, z_bot], b_t, b_sec, b_dims, +1, "Bottom Chord")
                    if k_top_opt:
                        add_member([x_l, yL, z_top], [x_r, yR, z_top], t_t, t_sec, t_dims, +1, "Top Chord")

            if is_end:
                base_offset = self.cad.end_diaphragm_spacing if self.cad.end_diaphragm_spacing > 0 else 200.0
                extra_offset = 300.0 * math.tan(math.radians(abs(self.cad.skew_angle)))
                offset = base_offset + extra_offset
                x_eff = (x + offset) if is_first else (x - offset)
                x_l_eff = x_eff + self._calculate_skew_offset(yL)
                x_r_eff = x_eff + self._calculate_skew_offset(yR)
                
                if self.cad.end_diaphragm_type == "Cross Bracing":
                    build_bracing(self.cad.end_diaphragm_bracing_type, self.cad.end_diaphragm_diagonal_section_type, self.cad.end_diaphragm_diagonal_section_dims, self.cad.end_diaphragm_diagonal_thickness, self.cad.end_diaphragm_top_chord_section_type, self.cad.end_diaphragm_top_chord_section_dims, self.cad.end_diaphragm_top_chord_thickness, self.cad.end_diaphragm_bottom_chord_section_type, self.cad.end_diaphragm_bottom_chord_section_dims, self.cad.end_diaphragm_bottom_chord_thickness, self.cad.x_bracket_option, self.cad.k_top_bracket)
                else: # Rolled Beam / Welded Beam
                    d_dims = _to_dims_dict(self.cad.end_diaphragm_dims)
                    z_center = z_top - (d_dims.get("depth", 100) / 2)
                    add_member([x_l_eff, yL, z_center], [x_r_eff, yR, z_center], 0, self.cad.end_diaphragm_section, d_dims, +1, "End Diaphragm")
            else:
                build_bracing(self.cad.bracing_type, self.cad.diagonal_section_type, self.cad.diagonal_section_dims, self.cad.diagonal_thickness, self.cad.top_chord_section_type, self.cad.top_chord_section_dims, self.cad.top_chord_thickness, self.cad.bottom_chord_section_type, self.cad.bottom_chord_section_dims, self.cad.bottom_chord_thickness, self.cad.x_bracket_option, self.cad.k_top_bracket)

        for idx, x in enumerate(x_positions):
            is_end = (idx == 0 or idx == len(x_positions)-1)
            is_first = (idx == 0)
            for i in range(n_girders - 1):
                yL = (i * spacing) - total_width / 2
                extract_bay(x, yL, yL + spacing, is_end, is_first)
                
        return braces

    def _calculate_total_deck_width(self, actual_base_width, actual_railing_width):
        """Replicates Osdag's CrossSectionLayout logic for total width."""
        cw = self.cad.carriageway_width
        cb = actual_base_width
        fp = self.cad.footpath_width
        rl = actual_railing_width
        
        # Base road width
        if self.cad.enable_median:
            # Get median width (standard 1200mm)
            median_label = "IRC 5 - Raised Kerb" # Default to fetch standard width
            median_geo = MedianGeometry.get_geometry(median_label)
            mw = median_geo.get("median_width", 1200)
            road_width = (2 * cw) + mw
        else:
            road_width = cw
            
        # Total width = 2 * crash barriers + road_width + footpaths/railings
        total = road_width + (2 * cb)
        
        if self.cad.footpath_config == "LEFT":
            total += fp + rl
        elif self.cad.footpath_config == "RIGHT":
            total += fp + rl
        elif self.cad.footpath_config == "BOTH":
            total += 2 * (fp + rl)
            
        return total

    def _extract_deck_slab(self, total_width):
        """Extract deck slab geometry with synchronized structural width."""
        L = self.cad.span_length_L
        T = self.cad.deck_thickness
        
        y_min = -total_width / 2
        y_max = total_width / 2
        z_top = self.cad.girder_section_d / 2 + self.cad.girder_section_tf
        
        pts = [
            [self._calculate_skew_offset(y_min), y_min, z_top],
            [L + self._calculate_skew_offset(y_min), y_min, z_top],
            [L + self._calculate_skew_offset(y_max), y_max, z_top],
            [self._calculate_skew_offset(y_max), y_max, z_top]
        ]
        
        return [ExtractedObject("SlabPolygon", points=pts, thickness=T, ifc_name="Deck Slab")]

    def _extract_safety_components(self, design_dict, actual_base_width, actual_railing_width):
        components = []
        L = self.cad.span_length_L
        z_base = self.cad.girder_section_d / 2 + self.cad.girder_section_tf + self.cad.deck_thickness
        
        total_deck_width = self._calculate_total_deck_width(actual_base_width, actual_railing_width)
        
        # Calculate road assembly offset (same as calculate_carriageway_offset in Osdag)
        carriageway_offset = 0.0
        if self.cad.footpath_config == "LEFT":
            carriageway_offset = (self.cad.footpath_width + actual_railing_width) / 2.0
        elif self.cad.footpath_config == "RIGHT":
            carriageway_offset = -(self.cad.footpath_width + actual_railing_width) / 2.0
            
        # Internal widths
        cw = self.cad.carriageway_width
        cb = actual_base_width
        
        # Define Y positions for barriers (positioned at the edge of the road assembly)
        y_l = -total_deck_width / 2.0 + cb / 2.0
        if self.cad.footpath_config in ("LEFT", "BOTH"):
            y_l += (self.cad.footpath_width + actual_railing_width)

        y_r = total_deck_width / 2.0 - cb / 2.0
        if self.cad.footpath_config in ("RIGHT", "BOTH"):
            y_r -= (self.cad.footpath_width + actual_railing_width)
            
        # Map barrier types to labels for Geometry Retrieval
        # UI stores the full IRC label directly (e.g., "IRC 5 - RCC Crash Barrier")
        # Support both full IRC labels (new) and legacy short names (old)
        bt = str(self.cad.barrier_type)
        if bt.startswith("IRC 5"):
            barrier_label = bt  # Already a full IRC label from the UI
        elif bt == "Rigid":
            barrier_label = "IRC 5 - High Containment RCC Crash Barrier" if self.cad.crash_barrier_subtype == "High Containment" else "IRC 5 - RCC Crash Barrier"
        else:  # Legacy "Flexible" / "Semi-Rigid" / "Metallic"
            barrier_label = "IRC 5 - Metallic Crash Barrier with Double W-Beam" if self.cad.crash_barrier_subtype == "Double W-beam" else "IRC 5 - Metallic Crash Barrier with Single W-Beam"

        barrier_geo = CrashBarrierGeometry.get_geometry(barrier_label)
        
        # Left barrier
        components.append(ExtractedObject("BarrierSweep", type=self.cad.barrier_type, subtype=self.cad.crash_barrier_subtype, 
            span=L, z_base=z_base, y_offset=y_l, skew=self.cad.skew_angle, geo=barrier_geo, ifc_name="Crash Barrier L"))
        # Right barrier
        components.append(ExtractedObject("BarrierSweep", type=self.cad.barrier_type, subtype=self.cad.crash_barrier_subtype, 
            span=L, z_base=z_base, y_offset=y_r, skew=self.cad.skew_angle, geo=barrier_geo, ifc_name="Crash Barrier R"))
                
        # Median
        if self.cad.enable_median:
            # Median is centered in the road assembly
            median_y = carriageway_offset
            
            # Map median type to labels
            # UI stores the full IRC label directly (e.g., "IRC 5 - Raised Kerb")
            # Support both full IRC labels (new) and legacy short names (old)
            mt = str(self.cad.median_type)
            if mt.startswith("IRC 5"):
                median_label = mt  # Already a full IRC label from the UI
            elif mt == "Raised Kerb":
                median_label = "IRC 5 - Raised Kerb"
            elif mt == "RCC Crash Barrier":
                median_label = "IRC 5 - RCC Crash Barrier"
            elif "Double" in mt:
                median_label = "IRC 5 - Metallic Crash Barrier with Double W-Beam"
            else:
                median_label = "IRC 5 - Metallic Crash Barrier with Single W-Beam"

            median_geo = MedianGeometry.get_geometry(median_label)
            components.append(ExtractedObject("BarrierSweep", type="Median", subtype=self.cad.median_type, span=L, 
                z_base=z_base, y_offset=median_y, skew=self.cad.skew_angle, geo=median_geo, ifc_name="Median Barrier"))
                
        # Railings
        railing_label = "IRC 5 - RCC Railing" if "rcc" in str(self.cad.railing_type).lower() else "IRC 5 - Steel Railing"
        railing_geo = RailingGeometry.get_geometry(railing_label)
        if self.cad.footpath_config in ("LEFT", "BOTH"):
            y_railing_left = -total_deck_width / 2.0 + actual_railing_width / 2.0
            components.append(ExtractedObject("RailingSweep", type=self.cad.railing_type, count=self.cad.rail_count, span=L, 
                z_base=z_base, y_offset=y_railing_left, skew=self.cad.skew_angle, geo=railing_geo, ifc_name="Footpath Railing L"))
        if self.cad.footpath_config in ("RIGHT", "BOTH"):
            y_railing_right = total_deck_width / 2.0 - actual_railing_width / 2.0
            components.append(ExtractedObject("RailingSweep", type=self.cad.railing_type, count=self.cad.rail_count, span=L, 
                z_base=z_base, y_offset=y_railing_right, skew=self.cad.skew_angle, geo=railing_geo, ifc_name="Footpath Railing R"))
                
        return components

    def _extract_supports(self, n_girders, spacing):
        supports = []
        total_width = (n_girders - 1) * spacing
        D = self.cad.girder_section_d
        z_contact = -(D / 2.0 + self.cad.girder_section_tf_b)
        support_width = max(self.cad.girder_section_bf, self.cad.girder_section_bf_b)
        base_dim = min(0.10 * self.cad.span_length_L, 0.75 * D)
        h_supp = base_dim / 1.5
        w_supp = base_dim / 2.0
        r_cyl = h_supp / 2.0
        
        for i in range(n_girders):
            y_offset = (i * spacing) - (total_width / 2)
            x_offset = self._calculate_skew_offset(y_offset)
            
            # Left Triangular Support
            supports.append(ExtractedObject("StiffenerPlate", L=w_supp*2, W=h_supp, T=support_width, 
                origin=[x_offset + w_supp, y_offset - support_width/2, z_contact],
                uDir=[0,1,0], wDir=[0,0,-1], ifc_name=f"Triangular Support {i+1}"))
            
            # Right Cylindrical Support
            supports.append(ExtractedObject("CircularSolid", r=r_cyl, H=support_width,
                origin=[x_offset + self.cad.span_length_L - r_cyl, y_offset - support_width/2, z_contact - r_cyl],
                uDir=[0,1,0], wDir=[0,0,1], ifc_name=f"Cylindrical Support {i+1}"))
                
        return {"supports_tri": [s for s in supports if s._class_name == "StiffenerPlate"], "supports_cyl": [s for s in supports if s._class_name == "CircularSolid"]}
