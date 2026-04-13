"""
Plate Girder Bridge - CAD to IFC Data Extraction Pipeline
Translates PlateGirderCADGenerator UI configurations into parametric dicts/objects.
"""
import math
import numpy as np

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
        
    def extract(self):
        return {
            "girders": self._extract_girders(),
            "stiffeners": self._extract_stiffeners(),
            "cross_bracings": self._extract_cross_bracings(),
            "deck_slab": self._extract_deck_slab(),
            "crash_barriers": self._extract_safety_components(),
            "supports": self._extract_supports()
        }

    def _extract_girders(self):
        girders = []
        total_width = (self.cad.num_girders - 1) * self.cad.girder_spacing
        d = self.cad.girder_section_d
        tw = self.cad.girder_section_tw
        L = self.cad.span_length_L
        
        for i in range(self.cad.num_girders):
            y_offset = (i * self.cad.girder_spacing) - (total_width / 2)
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

    def _extract_stiffeners(self):
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
        
        END_STIFFENER_SPACING = 50.0
        end_stiffener_gap = (T_es / 2.0)
        
        total_width = (self.cad.num_girders - 1) * self.cad.girder_spacing
        
        # Stiffeners Extrude UP (global Z) alongside the web depth
        # For Vertical Stiffeners: T (Profile Width) maps to local X (global X -> Thickness)
        #                          L (Profile Height) maps to local Y (global Y -> Outstand Width)
        #                          W (Extrusion) maps to local Z (global Z -> D)
        uDir_vert = [0, 0, 1] 
        wDir_vert = [1, 0, 0]
        
        for i in range(self.cad.num_girders):
            y_offset = (i * self.cad.girder_spacing) - (total_width / 2)
            
            # Intermediate Stiffeners
            if self.cad.include_intermediate_stiffeners:
                spacing = self.cad.intermediate_stiffener_spacing
                num_panels = max(1, int(L // spacing))
                end_zone = end_stiffener_gap + (self.cad.num_end_stiffener_pairs - 1) * END_STIFFENER_SPACING + END_STIFFENER_SPACING
                
                for j in range(1, num_panels):
                    x_dist = j * spacing
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

    def _extract_cross_bracings(self):
        braces = []
        n_internal = int(self.cad.span_length_L / self.cad.cross_bracing_spacing) - 1
        n_total = n_internal + 2
        spacing = self.cad.span_length_L / (n_total - 1) if n_total > 1 else 0
        x_positions = [i * spacing for i in range(n_total)]
        total_width = (self.cad.num_girders - 1) * self.cad.girder_spacing
        
        depth = self.cad.girder_section_d
        z_bot = -depth / 2
        z_top = depth / 2
        
        def add_member(p1, p2, thickness, sec_type, dims, roll, name):
            braces.append(ExtractedObject("StructuralMember", p1=p1, p2=p2, T=thickness, sec_type=sec_type, dims=dims, roll=roll, ifc_name=name))
            
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
                    d_dims = self.cad.end_diaphragm_dims
                    z_center = z_top - (d_dims.get("depth", 100) / 2)
                    add_member([x_l_eff, yL, z_center], [x_r_eff, yR, z_center], 0, self.cad.end_diaphragm_section, d_dims, +1, "End Diaphragm")
            else:
                build_bracing(self.cad.bracing_type, self.cad.diagonal_section_type, self.cad.diagonal_section_dims, self.cad.diagonal_thickness, self.cad.top_chord_section_type, self.cad.top_chord_section_dims, self.cad.top_chord_thickness, self.cad.bottom_chord_section_type, self.cad.bottom_chord_section_dims, self.cad.bottom_chord_thickness, self.cad.x_bracket_option, self.cad.k_top_bracket)

        for idx, x in enumerate(x_positions):
            is_end = (idx == 0 or idx == len(x_positions)-1)
            is_first = (idx == 0)
            for i in range(self.cad.num_girders - 1):
                yL = (i * self.cad.girder_spacing) - total_width / 2
                extract_bay(x, yL, yL + self.cad.girder_spacing, is_end, is_first)
                
        return braces

    def _extract_deck_slab(self):
        L = self.cad.span_length_L
        W_carriageway = self.cad.carriageway_width
        T = self.cad.deck_thickness
        foot_w = self.cad.footpath_width if self.cad.footpath_config != "NONE" else 0
        rail_w = self.cad.railing_width if self.cad.footpath_config != "NONE" else 0
        barrier_w = 450.0 # Approximate width of crash barrier base
        
        left_add = (foot_w + rail_w + barrier_w) if self.cad.footpath_config in ("LEFT", "BOTH") else barrier_w
        right_add = (foot_w + rail_w + barrier_w) if self.cad.footpath_config in ("RIGHT", "BOTH") else barrier_w
        
        total_width = W_carriageway + left_add + right_add
        
        y_min = -total_width / 2
        y_max = total_width / 2
        
        z_top = self.cad.girder_section_d / 2 + self.cad.girder_section_tf
        z_surface = z_top + T
        
        # Calculate skew polygon (CCW Winding Order for solid topology)
        # These points define the BOTTOM footprint of the slab (aligning with girder top flanges)
        pts = [
            [self._calculate_skew_offset(y_min), y_min, z_top],            # Bottom Left
            [L + self._calculate_skew_offset(y_min), y_min, z_top],        # Bottom Right
            [L + self._calculate_skew_offset(y_max), y_max, z_top],        # Top Right
            [self._calculate_skew_offset(y_max), y_max, z_top]             # Top Left
        ]
        
        return [ExtractedObject("SlabPolygon", points=pts, thickness=T, ifc_name="Deck Slab")]

    def _extract_safety_components(self):
        components = []
        W_carriageway = self.cad.carriageway_width
        L = self.cad.span_length_L
        z_base = self.cad.girder_section_d / 2 + self.cad.girder_section_tf + self.cad.deck_thickness
        
        foot_w = self.cad.footpath_width if self.cad.footpath_config != "NONE" else 0
        rail_w = self.cad.railing_width if self.cad.footpath_config != "NONE" else 0
        barrier_w = 450.0 
        
        left_add = (foot_w + rail_w + barrier_w) if self.cad.footpath_config in ("LEFT", "BOTH") else barrier_w
        right_add = (foot_w + rail_w + barrier_w) if self.cad.footpath_config in ("RIGHT", "BOTH") else barrier_w
        
        y_left_edge = -(W_carriageway/2 + left_add)
        y_right_edge = (W_carriageway/2 + right_add)
        
        # Guard rails / Barriers
        b_type = self.cad.barrier_type
        sub_type = self.cad.crash_barrier_subtype
        
        barrier_offsets = []
        if self.cad.footpath_config in ("LEFT", "BOTH"):
            barrier_offsets.append(y_left_edge + rail_w + foot_w + barrier_w/2)
        else:
            barrier_offsets.append(y_left_edge + barrier_w/2)
            
        if self.cad.footpath_config in ("RIGHT", "BOTH"):
            barrier_offsets.append(y_right_edge - rail_w - foot_w - barrier_w/2)
        else:
            barrier_offsets.append(y_right_edge - barrier_w/2)
            
        for y_off in barrier_offsets:
            components.append(ExtractedObject("BarrierSweep", type=b_type, subtype=sub_type, span=L, 
                z_base=z_base, y_offset=y_off, skew=self.cad.skew_angle, ifc_name="Crash Barrier"))
                
        # Median
        if self.cad.enable_median:
            components.append(ExtractedObject("BarrierSweep", type="Median", subtype=self.cad.median_type, span=L, 
                z_base=z_base, y_offset=0, skew=self.cad.skew_angle, ifc_name="Median Barrier"))
                
        # Railings
        if self.cad.footpath_config in ("LEFT", "BOTH"):
            components.append(ExtractedObject("RailingSweep", type=self.cad.railing_type, count=self.cad.rail_count, span=L, 
                z_base=z_base, y_offset=y_left_edge + rail_w/2, skew=self.cad.skew_angle, ifc_name="Footpath Railing"))
        if self.cad.footpath_config in ("RIGHT", "BOTH"):
            components.append(ExtractedObject("RailingSweep", type=self.cad.railing_type, count=self.cad.rail_count, span=L, 
                z_base=z_base, y_offset=y_right_edge - rail_w/2, skew=self.cad.skew_angle, ifc_name="Footpath Railing"))
                
        return components

    def _extract_supports(self):
        supports = []
        total_width = (self.cad.num_girders - 1) * self.cad.girder_spacing
        D = self.cad.girder_section_d
        z_contact = -(D / 2.0 + self.cad.girder_section_tf_b)
        support_width = max(self.cad.girder_section_bf, self.cad.girder_section_bf_b)
        base_dim = min(0.10 * self.cad.span_length_L, 0.75 * D)
        h_supp = base_dim / 1.5
        w_supp = base_dim / 2.0
        r_cyl = h_supp / 2.0
        
        for i in range(self.cad.num_girders):
            y_offset = (i * self.cad.girder_spacing) - (total_width / 2)
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
