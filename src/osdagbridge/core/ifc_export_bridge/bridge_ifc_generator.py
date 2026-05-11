"""
Bridge IFC Generator
Orchestrates the creation of the IFC4 file and aggregates mapped components.
"""
import uuid
import time
import ifcopenshell
from osdagbridge.core.ifc_export_bridge.bridge_geometry_mapper import BridgeGeometryMapper, create_ifc_guid
from osdagbridge.core.ifc_export_bridge.metadata_mapper import BridgeMetadataMapper

class BridgeIfcGenerator:
    def __init__(self, output_path):
        self.output_path = output_path
        self.file = None
        self.mapper = None
        self._owner_history = None
        
        # Spatial hierarchy elements
        self.project = None
        self.site = None
        self.building = None
        self.storey = None

    def initialize_file(self):
        """Initializes empty IFC4 file with proper schema and default spatial structure."""
        stamp = int(time.time())
        self.file = ifcopenshell.file(schema="IFC4")
        self.mapper = BridgeGeometryMapper(self.file)
        self.metadata = BridgeMetadataMapper(self.file, self.mapper)
        
        # Owner History
        person = self.file.createIfcPerson(Identification="USER", FamilyName="Osdag", GivenName="Bridge")
        org = self.file.createIfcOrganization(Identification="Osdag", Name="Osdag")
        person_org = self.file.createIfcPersonAndOrganization(ThePerson=person, TheOrganization=org)
        app = self.file.createIfcApplication(
            ApplicationDeveloper=org, Version="1.0", ApplicationFullName="Osdag Bridge", ApplicationIdentifier="OSDAG_BRIDGE_IFC"
        )
        self._owner_history = self.file.createIfcOwnerHistory(
            OwningUser=person_org, OwningApplication=app, ChangeAction="ADDED", CreationDate=stamp
        )
        
        # Baseline spatial hierarchy
        
        # Unit Assignment
        length_unit = self.file.createIfcSIUnit(None, "LENGTHUNIT", None, "METRE")
        area_unit = self.file.createIfcSIUnit(None, "AREAUNIT", None, "SQUARE_METRE")
        volume_unit = self.file.createIfcSIUnit(None, "VOLUMEUNIT", None, "CUBIC_METRE")
        angle_unit = self.file.createIfcSIUnit(None, "PLANEANGLEUNIT", None, "RADIAN")
        unit_assignment = self.file.createIfcUnitAssignment([length_unit, area_unit, volume_unit, angle_unit])
        
        self.project = self.file.createIfcProject(create_ifc_guid(), self._owner_history, Name="Osdag Plate Girder Bridge", UnitsInContext=unit_assignment)
        
        # Site, Building, Storey (FacilityPart substitution for IFC4 Bridge)
        place_3d = self.mapper.create_axis2placement_3d((0., 0., 0.))
        self.site = self.file.createIfcSite(create_ifc_guid(), self._owner_history, Name="Default Site", ObjectPlacement=self.file.createIfcLocalPlacement(None, place_3d))
        self.building = self.file.createIfcBuilding(create_ifc_guid(), self._owner_history, Name="Bridge Structure", ObjectPlacement=self.file.createIfcLocalPlacement(self.site.ObjectPlacement, place_3d))
        self.storey = self.file.createIfcBuildingStorey(create_ifc_guid(), self._owner_history, Name="Superstructure", ObjectPlacement=self.file.createIfcLocalPlacement(self.building.ObjectPlacement, place_3d))
        
        # Relate hierarchy
        self.file.createIfcRelAggregates(create_ifc_guid(), self._owner_history, RelatingObject=self.project, RelatedObjects=[self.site])
        self.file.createIfcRelAggregates(create_ifc_guid(), self._owner_history, RelatingObject=self.site, RelatedObjects=[self.building])
        self.file.createIfcRelAggregates(create_ifc_guid(), self._owner_history, RelatingObject=self.building, RelatedObjects=[self.storey])

    def bind_element_to_storey(self, element):
        self.file.createIfcRelContainedInSpatialStructure(create_ifc_guid(), self._owner_history, RelatingStructure=self.storey, RelatedElements=[element])

    def generate_from_extracted_data(self, extracted_dict, cad_context=None):
        """Consume extracted dictionary logic and bind to schema."""
        self.initialize_file()
        s = 0.001 # Global Scale Factor (Meters)
        shared = {"deck_top_m": 0.0}  # Shared state: deck top surface in meters
        
        def _process_plate(item):
            prof = self.mapper.create_rectangular_profile(item.T * s, item.L * s)
            scaled_origin = [v * s for v in item.origin]
            place = self.mapper.create_axis2placement_3d(scaled_origin, z_dir=item.uDir, x_dir=item.wDir)
            # Use identity placement for the solid relative to the object placement
            local_identity = self.mapper.create_axis2placement_3d((0,0,0), z_dir=(0,0,1), x_dir=(1,0,0))
            solid = self.mapper.create_extruded_solid(prof, item.W * s, local_identity)
            
            shape = self.file.createIfcShapeRepresentation(self.mapper._context3d, "Body", "SweptSolid", [solid])
            prod_def = self.file.createIfcProductDefinitionShape(None, None, [shape])
            elem = self.file.createIfcPlate(create_ifc_guid(), self._owner_history, Name=item.ifc_name, ObjectPlacement=self.file.createIfcLocalPlacement(self.storey.ObjectPlacement, place), Representation=prod_def)
            self.bind_element_to_storey(elem)
            if "Stiffener" in item.ifc_name:
                self.metadata.map_stiffener(elem, cad_context, item.ifc_name)
            else:
                self.metadata.map_girder(elem, cad_context, item.ifc_name)

        def _process_brace(item):
            # Dynamic profile type matching
            prof = None
            if item.sec_type == "ANGLE":
                prof = self.mapper.create_l_shape_profile(item.dims.get('leg_h', 100) * s, item.dims.get('leg_w', 50) * s, item.T * s)
            elif item.sec_type == "CHANNEL":
                prof = self.mapper.create_c_shape_profile(item.dims.get('depth', 100) * s, item.dims.get('flange_width', 50) * s, 5 * s, 7 * s)
            elif item.sec_type == "DOUBLE_ANGLE":
                prof = self.mapper.create_double_angle_profile(item.dims.get('leg_h', 100) * s, item.dims.get('leg_w', 50) * s, item.T * s, item.dims.get('connection_type', 'LONGER_LEG'))
            elif item.sec_type == "DOUBLE_CHANNEL":
                prof = self.mapper.create_double_channel_profile(item.dims.get('depth', 100) * s, item.dims.get('flange_width', 50) * s, 5 * s, 7 * s)
            else: # I_SECTION
                prof = self.mapper.create_i_shape_profile(item.dims.get('depth', 100) * s, item.dims.get('flange_width', 100) * s, item.dims.get('web_thickness', 5) * s, item.dims.get('flange_thickness', 5) * s)
            
            # Extrusion vectors
            import math
            dx, dy, dz = item.p2[0]-item.p1[0], item.p2[1]-item.p1[1], item.p2[2]-item.p1[2]
            length = math.sqrt(dx*dx + dy*dy + dz*dz)
            
            if length > 0:
                z_dir = (dx/length, dy/length, dz/length)
            else:
                z_dir = (0, 0, 1)
                
            # Compute a robust orthogonal X axis
            if abs(z_dir[2]) > 0.999: # Vertical member
                x_dir = (1, 0, 0)
            else:
                # Cross product Z_global (0,0,1) x z_dir (dx, dy, dz) => (-dy, dx, 0)
                mag_x = math.sqrt(z_dir[1]**2 + z_dir[0]**2)
                x_dir = (-z_dir[1]/mag_x, z_dir[0]/mag_x, 0)
            
            scaled_p1 = [v * s for v in item.p1]
            place = self.mapper.create_axis2placement_3d(scaled_p1, z_dir=z_dir, x_dir=x_dir)
            local_identity = self.mapper.create_axis2placement_3d((0,0,0), z_dir=(0,0,1), x_dir=(1,0,0))
            solid = self.mapper.create_extruded_solid(prof, length * s, local_identity)
            
            shape = self.file.createIfcShapeRepresentation(self.mapper._context3d, "Body", "SweptSolid", [solid])
            prod_def = self.file.createIfcProductDefinitionShape(None, None, [shape])
            elem = self.file.createIfcMember(create_ifc_guid(), self._owner_history, Name=item.ifc_name, ObjectPlacement=self.file.createIfcLocalPlacement(self.storey.ObjectPlacement, place), Representation=prod_def)
            self.bind_element_to_storey(elem)
            self.metadata.map_brace(elem, cad_context, item)

        def _process_deck(item):
            # Use extracted thickness
            deck_thickness = getattr(item, 'thickness', 200)
            z_base = item.points[0][2] * s
            
            # Store the deck top surface for barrier alignment
            shared["deck_top_m"] = z_base + deck_thickness * s
            
            # Map the globally extracted 3D corners to a pure 2D footprint profile
            pts_2d = [(p[0] * s, p[1] * s) for p in item.points]
            prof = self.mapper.create_polygonal_profile(pts_2d, "DeckProfile")
            
            # Place the solid in world space at Z = z_base
            place = self.mapper.create_axis2placement_3d((0, 0, z_base), z_dir=(0, 0, 1), x_dir=(1, 0, 0))
            local_identity = self.mapper.create_axis2placement_3d((0, 0, 0), z_dir=(0, 0, 1), x_dir=(1, 0, 0))
            
            solid = self.mapper.create_extruded_solid(prof, deck_thickness * s, local_identity)
            
            shape = self.file.createIfcShapeRepresentation(self.mapper._context3d, "Body", "SweptSolid", [solid])
            prod_def = self.file.createIfcProductDefinitionShape(None, None, [shape])
            elem = self.file.createIfcSlab(create_ifc_guid(), self._owner_history, Name=item.ifc_name, 
                ObjectPlacement=self.file.createIfcLocalPlacement(self.storey.ObjectPlacement, place), 
                Representation=prod_def)
            self.bind_element_to_storey(elem)
            self.metadata.map_deck_slab(elem, cad_context)
            
        def _process_metallic_median(item, geo):
              """Generates the multi-component assembly for metallic medians."""
              import math
              s = 0.001
              deck_top = shared["deck_top_m"]
              span_l = item.span
              
              kerb_h = geo.get("kerb_height", 150.0)
              kerb_bot = geo.get("median_width", 1200.0)
              kerb_top = geo.get("kerb_top_width", 1150.0)
              post_h = geo.get("post_height", 950.0)
              post_spacing = geo.get("post_spacing", 1000.0)
              num_rails = geo.get("number_of_w_beams", geo.get("w_beams", 2))
              
              # 1. CREATE CONTINUOUS KERB (Base)
              offset = (kerb_bot - kerb_top) / 2
              kerb_pts = [(0, 0), (kerb_bot, 0), (kerb_bot - offset, kerb_h), (offset, kerb_h)]
              kerb_pts_m = [(p[0] * s, p[1] * s) for p in kerb_pts]
              kerb_prof = self.mapper.create_polygonal_profile(kerb_pts_m, "Median_Kerb_Profile")
              
              x_start = item.y_offset * math.tan(math.radians(item.skew)) if hasattr(item, 'skew') else 0
              y_origin_kerb = item.y_offset * s - (kerb_bot * s / 2.0)
              place_kerb = self.mapper.create_axis2placement_3d([x_start * s, y_origin_kerb, deck_top], z_dir=[1,0,0], x_dir=[0,1,0])
              kerb_solid = self.mapper.create_extruded_solid(kerb_prof, span_l * s, place_kerb)
              all_solids = [kerb_solid]
              
              # 2. CREATE POSTS AND SPACERS
              post_web_h, post_flange_w = 150.0, 75.0
              tw, tf = 5.4, 9.2
              chan_pts_m = [(p[0]*s, p[1]*s) for p in [
                  (0, -post_web_h/2), (post_flange_w, -post_web_h/2), (post_flange_w, -post_web_h/2 + tf),
                  (tw, -post_web_h/2 + tf), (tw, post_web_h/2 - tf), (post_flange_w, post_web_h/2 - tf),
                  (post_flange_w, post_web_h/2), (0, post_web_h/2)
              ]]
              post_prof = self.mapper.create_polygonal_profile(chan_pts_m, "Median_Post_Profile")
              
              sp_h, sp_w, sp_d = 330.0, 200.0, 150.0
              sp_pts_m = [(p[0]*s, p[1]*s) for p in [
                  (0, -sp_w/2), (sp_d, -sp_w/2), (sp_d, -sp_w/2 + 8.0),
                  (5.0, -sp_w/2 + 8.0), (5.0, sp_w/2 - 8.0), (sp_d, sp_w/2 - 8.0),
                  (sp_d, sp_w/2), (0, sp_w/2)
              ]]
              sp_prof = self.mapper.create_polygonal_profile(sp_pts_m, "Median_Spacer_Profile")
              
              num_posts = int(span_l / post_spacing) + 1
              post_y_offsets = [-240.0, 240.0] # Fixed for 1.2m median
              
              for i in range(num_posts):
                  x_p = i * post_spacing
                  for y_off_local in post_y_offsets:
                      side_mult = 1 if y_off_local > 0 else -1
                      y_global = item.y_offset + y_off_local
                      x_off_skew = y_global * math.tan(math.radians(item.skew)) if hasattr(item, 'skew') else 0
                      post_origin = [(x_p + x_off_skew) * s, y_global * s, deck_top + kerb_h * s]
                      
                      place_post = self.mapper.create_axis2placement_3d(post_origin, z_dir=[0,0,1], x_dir=[1,0,0])
                      all_solids.append(self.mapper.create_extruded_solid(post_prof, post_h * s, place_post))
                      
                      h_upper = post_h - 312.0 / 2.0
                      beam_heights = [h_upper - 312.0 - 145.0, h_upper] if num_rails == 2 else [h_upper]
                      for bh in beam_heights:
                          sp_z = deck_top + (kerb_h + bh - sp_h/2.0) * s
                          sp_y_m = post_origin[1] + side_mult * 175.0 * s
                          sp_origin = [post_origin[0], sp_y_m, sp_z]
                          place_sp = self.mapper.create_axis2placement_3d(sp_origin, z_dir=[0,0,1], x_dir=[1,0,0])
                          all_solids.append(self.mapper.create_extruded_solid(sp_prof, sp_h * s, place_sp))

              # 3. CREATE CONTINUOUS RAILS
              rail_y_offsets = [-515.0, 515.0]
              for bh in beam_heights:
                  rail_z = deck_top + (kerb_h + bh - 312.0 / 2.0) * s
                  for y_off_local in rail_y_offsets:
                      y_global = item.y_offset + y_off_local
                      x_start_rail = y_global * math.tan(math.radians(item.skew)) if hasattr(item, 'skew') else 0
                      # Face outward towards traffic: Left rail (-515) faces -Y, Right rail (+515) faces +Y
                      mult = -1.0 if y_global < item.y_offset else 1.0 
                      w_pts_m = _get_w_profile_pts_m(mult, s)
                      w_prof = self.mapper.create_polygonal_profile(w_pts_m, f"W_Rail_{'L' if mult<0 else 'R'}")
                      place_rail = self.mapper.create_axis2placement_3d([x_start_rail * s, y_global * s, rail_z], z_dir=[1,0,0], x_dir=[0,1,0])
                      all_solids.append(self.mapper.create_extruded_solid(w_prof, span_l * s, place_rail))

              _finalize_metallic_assembly(item, all_solids)

        def _process_metallic_barrier(item, geo):
              """Generates the multi-component assembly for edge metallic barriers."""
              import math
              s = 0.001
              deck_top = shared["deck_top_m"]
              span_l = item.span
              
              kerb_h = geo.get("kerb_height", 150.0)
              kerb_bot = 500.0
              kerb_top = 450.0
              post_h = geo.get("post_height", 950.0)
              post_spacing = geo.get("post_spacing", 1000.0)
              num_rails = geo.get("number_of_w_beams", geo.get("w_beams", 1))
              
              # 1. Dimensions based on side (Left/Right)
              is_right_edge = item.y_offset > 0.5
              side_mult = -1 if is_right_edge else 1
              post_y_off = 110.0 if is_right_edge else -110.0 
              rail_y_off = -165.0 if is_right_edge else 165.0
              
              # 2. KERB
              offset = (kerb_bot - kerb_top) / 2
              kerb_pts_m = [(p[0]*s, p[1]*s) for p in [(0, 0), (kerb_bot, 0), (kerb_bot - offset, kerb_h), (offset, kerb_h)]]
              kerb_prof = self.mapper.create_polygonal_profile(kerb_pts_m, "Barrier_Kerb_Profile")
              x_start = item.y_offset * math.tan(math.radians(item.skew)) if hasattr(item, 'skew') else 0
              y_origin_kerb = item.y_offset * s - (kerb_bot * s / 2.0)
              place_kerb = self.mapper.create_axis2placement_3d([x_start * s, y_origin_kerb, deck_top], z_dir=[1,0,0], x_dir=[0,1,0])
              all_solids = [self.mapper.create_extruded_solid(kerb_prof, span_l * s, place_kerb)]
              
              # 3. POSTS AND SPACERS
              post_web_h, post_flange_w = 150.0, 75.0
              tw, tf = 5.4, 9.2
              chan_pts_m = [(p[0]*s, p[1]*s) for p in [
                  (0, -post_web_h/2), (post_flange_w, -post_web_h/2), (post_flange_w, -post_web_h/2 + tf),
                  (tw, -post_web_h/2 + tf), (tw, post_web_h/2 - tf), (post_flange_w, post_web_h/2 - tf),
                  (post_flange_w, post_web_h/2), (0, post_web_h/2)
              ]]
              post_prof = self.mapper.create_polygonal_profile(chan_pts_m, "Barrier_Post_Profile")
              
              sp_h, sp_w, sp_d = 330.0, 200.0, 150.0
              sp_pts_m = [(p[0]*s, p[1]*s) for p in [
                  (0, -sp_w/2), (sp_d, -sp_w/2), (sp_d, -sp_w/2 + 8.0),
                  (5.0, -sp_w/2 + 8.0), (5.0, sp_w/2 - 8.0), (sp_d, sp_w/2 - 8.0),
                  (sp_d, sp_w/2), (0, sp_w/2)
              ]]
              sp_prof = self.mapper.create_polygonal_profile(sp_pts_m, "Barrier_Spacer_Profile")
              
              num_posts = int(span_l / post_spacing) + 1
              for i in range(num_posts):
                  x_p = i * post_spacing
                  y_global = item.y_offset + post_y_off
                  x_off_skew = y_global * math.tan(math.radians(item.skew)) if hasattr(item, 'skew') else 0
                  post_origin = [(x_p + x_off_skew) * s, y_global * s, deck_top + kerb_h * s]
                  place_post = self.mapper.create_axis2placement_3d(post_origin, z_dir=[0,0,1], x_dir=[1,0,0])
                  all_solids.append(self.mapper.create_extruded_solid(post_prof, post_h * s, place_post))
                  
                  h_upper = post_h - 312.0 / 2.0
                  beam_heights = [h_upper - 312.0 - 145.0, h_upper] if num_rails == 2 else [h_upper]
                  for bh in beam_heights:
                      sp_z = deck_top + (kerb_h + bh - sp_h/2.0) * s
                      sp_y_m = post_origin[1] + side_mult * 175.0 * s
                      sp_origin = [post_origin[0], sp_y_m, sp_z]
                      place_sp = self.mapper.create_axis2placement_3d(sp_origin, z_dir=[0,0,1], x_dir=[1,0,0])
                      all_solids.append(self.mapper.create_extruded_solid(sp_prof, sp_h * s, place_sp))

              # 4. CONTINUOUS RAILS
              for bh in beam_heights:
                  rail_z = deck_top + (kerb_h + bh - 312.0 / 2.0) * s
                  y_global = item.y_offset + rail_y_off
                  x_start_rail = y_global * math.tan(math.radians(item.skew)) if hasattr(item, 'skew') else 0
                  # Face inward towards road: Left edge faces +Y, Right edge faces -Y
                  mult = 1.0 if not is_right_edge else -1.0
                  w_pts_m = _get_w_profile_pts_m(mult, s)
                  w_prof = self.mapper.create_polygonal_profile(w_pts_m, f"W_Edge_Rail_{'L' if mult<0 else 'R'}")
                  place_rail = self.mapper.create_axis2placement_3d([x_start_rail * s, y_global * s, rail_z], z_dir=[1,0,0], x_dir=[0,1,0])
                  all_solids.append(self.mapper.create_extruded_solid(w_prof, span_l * s, place_rail))

              _finalize_metallic_assembly(item, all_solids)

        def _get_w_profile_pts_m(mult, s):
              H, D, T = 312.0, 85.0, 3.0
              sigma = H / 10.0
              mu1, mu2 = H * 0.25, H * 0.75
              import math
              amp = D / (1.0 + math.exp(-((mu1-mu2)**2)/(2*sigma**2)))
              num_pts = 40
              pts = []
              for i in range(num_pts + 1):
                  y_l = (H * i) / num_pts
                  x_l = amp * (math.exp(-((y_l-mu1)**2)/(2*sigma**2)) + math.exp(-((y_l-mu2)**2)/(2*sigma**2)))
                  pts.append((mult * x_l * s, y_l * s))
              for i in range(num_pts, -1, -1):
                  y_l = (H * i) / num_pts
                  x_l = amp * (math.exp(-((y_l-mu1)**2)/(2*sigma**2)) + math.exp(-((y_l-mu2)**2)/(2*sigma**2))) - T
                  pts.append((mult * x_l * s, y_l * s))
              return pts

        STEEL_COLOR = (0.6, 0.65, 0.7)
        RCC_COLOR = (0.85, 0.85, 0.82)

        def _finalize_metallic_assembly(item, all_solids):
              shape = self.file.createIfcShapeRepresentation(self.mapper._context3d, "Body", "SweptSolid", all_solids)
              self.mapper.apply_color(shape, STEEL_COLOR)
              prod_def = self.file.createIfcProductDefinitionShape(None, None, [shape])
              elem = self.file.createIfcBuildingElementProxy(create_ifc_guid(), self._owner_history, Name=item.ifc_name, 
                                                              ObjectPlacement=self.file.createIfcLocalPlacement(self.storey.ObjectPlacement, self.mapper.create_axis2placement_3d((0,0,0))), 
                                                              Representation=prod_def)
              self.bind_element_to_storey(elem)
              self.metadata.map_barrier(elem, cad_context, item.ifc_name)

        def _process_barrier(item):
              geo = getattr(item, 'geo', {})
              import math
              
              if geo.get("type") == "metallic":
                  if "Median" in item.ifc_name:
                      _process_metallic_median(item, geo)
                  else:
                      _process_metallic_barrier(item, geo)
                  return

              # 1. Define 2D Profile Points and Reference Width
              if geo.get("type") in ["rcc", "rcc_barrier"]:
                 # Exact IRC profile dimensions as used in Osdag builder.py
                 total_h = geo.get("total_height", geo.get("barrier_height", 900.0))
                 bottom_w = geo.get("bottom_width", geo.get("median_width", 450.0))
                 base_v = geo.get("base_vertical", 100.0)
                 top_w = geo.get("top_width", 175.0) # Standard IRC top notch width

                 # Height levels
                 z1 = base_v
                 z2 = z1 + 250.0  # Transition slope height
                 z3 = total_h

                 # Width levels - shifted so left outer edge is at 0
                 # Right edge is the traffic-facing side (outer) which has the bend
                 right_edge = bottom_w
                 right_at_mid = bottom_w - 100.0  # Transition notch goes 100mm inwards
                 right_at_top = (bottom_w + top_w) / 2.0
                 left_at_top = (bottom_w - top_w) / 2.0
                 left_edge = 0.0

                 pts_2d = [
                     (left_edge, 0), 
                     (right_edge, 0), 
                     (right_edge, z1),
                     (right_at_mid, z2), 
                     (right_at_top, z3),
                     (left_at_top, z3), 
                     (left_edge, z1),
                 ]
              elif geo.get("type") == "kerb":
                  # Raised Kerb: trapezium profile (symmetric)
                  total_h = geo.get("kerb_height", 225)
                  bottom_w = geo.get("kerb_bottom_width", 1200)
                  top_w = geo.get("kerb_top_width", 1150)
                  offset = (bottom_w - top_w) / 2.0
                  pts_2d = [
                      (0, 0), (bottom_w, 0),
                      (bottom_w - offset, total_h), (offset, total_h)
                  ]
              else:
                  # Fallback — simple rectangle
                  total_h = geo.get("total_height", geo.get("kerb_height", 225))
                  bottom_w = geo.get("median_width", geo.get("bottom_width", geo.get("kerb_bottom_width", 1200)))
                  pts_2d = [(0, 0), (bottom_w, 0), (bottom_w, total_h), (0, total_h)]

             # 2. Determine solid placements (Double for medians, single for edge barriers)
              configs = []
              # Check if it's an RCC median (which needs two barriers)
              if item.type == "Median" and geo.get("type") == "rcc_barrier":
                  median_w = geo.get("median_width", 1200.0)
                  # Left barrier: mirrored, placed at -median_w/2
                  configs.append({"y_local": -median_w / 2.0, "mirror": True})
                  # Right barrier: normal, placed at +median_w/2 - bottom_w
                  configs.append({"y_local": median_w / 2.0 - bottom_w, "mirror": False})
              else:
                  # Standard single barrier (edge or non-RCC median)
                  is_right_side = item.y_offset > 0.5 
                  configs.append({"y_local": -bottom_w / 2.0, "mirror": is_right_side})

              deck_top = shared["deck_top_m"]
              # Map Median to IfcWall if it's high, otherwise IfcBuildingElementProxy
              elem_type = self.file.createIfcWall if item._class_name == "BarrierSweep" else self.file.createIfcBuildingElementProxy

              for cfg in configs:
                  # Apply mirroring if needed
                  current_pts = [(bottom_w - x, y) for x, y in pts_2d] if cfg["mirror"] else pts_2d
                  current_pts_m = [(x * s, y * s) for x, y in current_pts]
                  
                  y_global = item.y_offset + cfg["y_local"]
                  x_start = y_global * math.tan(math.radians(item.skew)) if hasattr(item, 'skew') else 0
                  
                  # Create a dedicated placement for this specific barrier
                  # Orientation: extrudes along Global X, profile in Global YZ plane
                  scaled_origin = [x_start * s, y_global * s, deck_top]
                  place = self.mapper.create_axis2placement_3d(scaled_origin, z_dir=[1,0,0], x_dir=[0,1,0])
                  
                  # Use identity for the solid relative to its dedicated element placement
                  local_identity = self.mapper.create_axis2placement_3d((0,0,0), z_dir=(0,0,1), x_dir=(1,0,0))
                  
                  prof = self.mapper.create_polygonal_profile(current_pts_m, f"BarrierProfile_{item.ifc_name}")
                  solid = self.mapper.create_extruded_solid(prof, item.span * s, local_identity)
                  
                  shape = self.file.createIfcShapeRepresentation(self.mapper._context3d, "Body", "SweptSolid", [solid])
                  self.mapper.apply_color(shape, RCC_COLOR)
                  prod_def = self.file.createIfcProductDefinitionShape(None, None, [shape])
                  
                  # Create the individual IFC element
                  elem_name = f"{item.ifc_name} {'Left' if cfg['mirror'] else 'Right'}" if len(configs) > 1 else item.ifc_name
                  elem = elem_type(create_ifc_guid(), self._owner_history, Name=elem_name, 
                                   ObjectPlacement=self.file.createIfcLocalPlacement(self.storey.ObjectPlacement, place), 
                                   Representation=prod_def)
                  self.bind_element_to_storey(elem)
                  self.metadata.map_barrier(elem, cad_context, elem_name)

        def _process_metallic_railing(item, geo):
             """Generates the multi-component assembly for steel railings."""
             import math
             s = 0.001
             deck_top = shared["deck_top_m"]
             span_l = item.span
             
             rail_h = geo.get("height", 1100.0)
             base_h = 100.0
             base_w = 375.0
             post_size = 150.0
             post_spacing = 1000.0
             rail_size = 40.0
             
             all_solids = []
             
             # 1. CREATE CONTINUOUS BASE
             # Base is centered at item.y_offset. Profile is in global YZ (local XY).
             # Local X: [-base_w/2, base_w/2], Local Y: [0, base_h]
             base_pts_m = [(-base_w*s/2, 0), (base_w*s/2, 0), (base_w*s/2, base_h*s), (-base_w*s/2, base_h*s)]
             base_prof = self.mapper.create_polygonal_profile(base_pts_m, f"Railing_Base_Profile_{item.ifc_name}")
             
             x_start = item.y_offset * math.tan(math.radians(item.skew)) if hasattr(item, 'skew') else 0
             # Origin at deck top, extrudes along X
             place_base = self.mapper.create_axis2placement_3d([x_start * s, item.y_offset * s, deck_top], z_dir=[1,0,0], x_dir=[0,1,0])
             all_solids.append(self.mapper.create_extruded_solid(base_prof, span_l * s, place_base))
             
             # 2. CREATE POSTS
             post_h = rail_h - base_h
             # Post profile in XY plane (global XY) extruding UP (Z)
             post_prof = self.mapper.create_rectangular_profile(post_size * s, post_size * s)
             
             # Match builder.py spacing logic
             eff_l = span_l - post_size
             num_spaces = max(1, int(eff_l / post_spacing)) if eff_l > 0 else 1
             actual_spacing = eff_l / num_spaces if eff_l > 0 else 0
             
             for i in range(num_spaces + 1):
                 x_p = i * actual_spacing
                 # Calculate x shift due to skew at this Y
                 x_off_skew = item.y_offset * math.tan(math.radians(item.skew)) if hasattr(item, 'skew') else 0
                 post_origin = [(x_p + x_off_skew) * s, item.y_offset * s, deck_top + base_h * s]
                 place_post = self.mapper.create_axis2placement_3d(post_origin, z_dir=[0,0,1], x_dir=[1,0,0])
                 all_solids.append(self.mapper.create_extruded_solid(post_prof, post_h * s, place_post))
                 
             # 3. CREATE CONTINUOUS RAILS
             rail_prof = self.mapper.create_rectangular_profile(rail_size * s, rail_size * s)
             
             # Top Rail (positioned near top)
             top_rail_z = deck_top + (rail_h - 2 * rail_size) * s
             place_top = self.mapper.create_axis2placement_3d([x_start * s, item.y_offset * s, top_rail_z], z_dir=[1,0,0], x_dir=[0,1,0])
             all_solids.append(self.mapper.create_extruded_solid(rail_prof, span_l * s, place_top))
             
             # Mid Rail
             mid_rail_z = deck_top + (base_h + post_h * 0.5) * s
             place_mid = self.mapper.create_axis2placement_3d([x_start * s, item.y_offset * s, mid_rail_z], z_dir=[1,0,0], x_dir=[0,1,0])
             all_solids.append(self.mapper.create_extruded_solid(rail_prof, span_l * s, place_mid))
             
             _finalize_metallic_assembly(item, all_solids)

        def _process_railing(item):
             geo = getattr(item, 'geo', {})
             import math
             
             rail_w = geo.get("width", 375)
             rail_h = geo.get("height", 1100)
             
             if geo.get("type") == "rcc":
                 # Match Osdag's hollow passage logic from builder.py
                 base_h = 100
                 body_h = rail_h - base_h
                 rail_count = 3
                 
                 # Profile is in local XY plane (global YZ)
                 # X maps to width (Y global), Y maps to height (Z global)
                 # Profile is centered at 0 in both axes
                 
                 # Outer rectangle points
                 w2, h2 = rail_w / 2.0, rail_h / 2.0
                 outer_pts = [(-w2, -h2), (w2, -h2), (w2, h2), (-w2, h2)]
                 
                 # Hollow passages (voids)
                 inner_voids = []
                 hole_w = 0.6 * rail_w
                 hole_h = 0.5 * (body_h / rail_count)
                 spacing = body_h / (rail_count + 1)
                 
                 for i in range(rail_count):
                     z_center_rel = base_h + (i + 1) * spacing
                     y_center = z_center_rel - h2 # Local Y is global Z
                     
                     hw2, hh2 = hole_w / 2.0, hole_h / 2.0
                     void_pts = [
                         (-hw2, y_center - hh2),
                         (hw2, y_center - hh2),
                         (hw2, y_center + hh2),
                         (-hw2, y_center + hh2)
                     ]
                     # Convert to scaled meters
                     inner_voids.append([(p[0] * s, p[1] * s) for p in void_pts])
                 
                 # Scale outer points
                 outer_pts_m = [(p[0] * s, p[1] * s) for p in outer_pts]
                 prof = self.mapper.create_polygonal_profile_with_voids(outer_pts_m, inner_voids, "RailingWithPassages")
                 
                 x_start = item.y_offset * math.tan(math.radians(item.skew)) if hasattr(item, 'skew') else 0
                 deck_top = shared["deck_top_m"]
                 
                 scaled_origin = [x_start * s, item.y_offset * s, deck_top + rail_h * s / 2.0]
                 place = self.mapper.create_axis2placement_3d(scaled_origin, z_dir=[1,0,0], x_dir=[0,1,0])
                 local_identity = self.mapper.create_axis2placement_3d((0,0,0), z_dir=(0,0,1), x_dir=(1,0,0))
                 solid = self.mapper.create_extruded_solid(prof, item.span * s, local_identity)
                 
                 shape = self.file.createIfcShapeRepresentation(self.mapper._context3d, "Body", "SweptSolid", [solid])
                 self.mapper.apply_color(shape, RCC_COLOR)
                 prod_def = self.file.createIfcProductDefinitionShape(None, None, [shape])
                 elem = self.file.createIfcRailing(create_ifc_guid(), self._owner_history, Name=item.ifc_name, ObjectPlacement=self.file.createIfcLocalPlacement(self.storey.ObjectPlacement, place), Representation=prod_def)
                 self.bind_element_to_storey(elem)
                 self.metadata.map_barrier(elem, cad_context, item.ifc_name)
             elif geo.get("type") == "steel":
                 _process_metallic_railing(item, geo)
             else:
                 # Fallback for simple rectangular railing
                 prof = self.mapper.create_rectangular_profile(rail_w * s, rail_h * s)
                 x_start = item.y_offset * math.tan(math.radians(item.skew)) if hasattr(item, 'skew') else 0
                 deck_top = shared["deck_top_m"]
                 scaled_origin = [x_start * s, item.y_offset * s, deck_top + rail_h * s / 2.0]
                 place = self.mapper.create_axis2placement_3d(scaled_origin, z_dir=[1,0,0], x_dir=[0,1,0])
                 local_identity = self.mapper.create_axis2placement_3d((0,0,0), z_dir=(0,0,1), x_dir=(1,0,0))
                 solid = self.mapper.create_extruded_solid(prof, item.span * s, local_identity)
                 shape = self.file.createIfcShapeRepresentation(self.mapper._context3d, "Body", "SweptSolid", [solid])
                 self.mapper.apply_color(shape, RCC_COLOR)
                 prod_def = self.file.createIfcProductDefinitionShape(None, None, [shape])
                 elem = self.file.createIfcRailing(create_ifc_guid(), self._owner_history, Name=item.ifc_name, ObjectPlacement=self.file.createIfcLocalPlacement(self.storey.ObjectPlacement, place), Representation=prod_def)
                 self.bind_element_to_storey(elem)
                 self.metadata.map_barrier(elem, cad_context, item.ifc_name)

        # Iterate over extraction dictionary explicitly
        for key in ["girders", "stiffeners"]:
             for item in extracted_dict.get(key, []):
                 _process_plate(item)
                 
        for key in ["cross_bracings"]:
             for item in extracted_dict.get(key, []):
                 if item._class_name == "StructuralMember":
                     _process_brace(item)
                     
        for key in ["deck_slab"]:
             for item in extracted_dict.get(key, []):
                 if item._class_name == "SlabPolygon":
                     _process_deck(item)
                     
        for key in ["crash_barriers"]: 
             for item in extracted_dict.get(key, []):
                 if item._class_name == "BarrierSweep":
                     _process_barrier(item)
                 elif item._class_name == "RailingSweep":
                     _process_railing(item)
                 
        # Intentionally ignore "deck_textures"
        print("Model assembly complete. Saving...")
        self.file.write(self.output_path)
