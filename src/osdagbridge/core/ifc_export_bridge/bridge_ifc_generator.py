"""
Bridge IFC Generator
Orchestrates the creation of the IFC4 file and aggregates mapped components.
"""
import uuid
import time
import ifcopenshell
from osdagbridge.core.ifc_export_bridge.bridge_geometry_mapper import BridgeGeometryMapper, create_ifc_guid

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

    def generate_from_extracted_data(self, extracted_dict):
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
                prof = self.mapper.create_rectangular_profile(item.dims.get('flange_width', 100) * s, item.dims.get('depth', 100) * s) # Simple default mapping
            
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
            
        def _process_barrier(item):
             geo = getattr(item, 'geo', {})
             import math
             
             # 1. Define 2D Profile Points and Reference Width
             if geo.get("type") == "rcc":
                 total_h = geo["total_height"]
                 bottom_w = geo["bottom_width"]
                 base_v = geo["base_vertical"]
                 mid_off = geo["mid_offset"]
                 shape_scale = bottom_w / 525.0
                 right_at_mid = 300 * shape_scale
                 left_at_top = 50 * shape_scale
                 right_at_top = 225 * shape_scale

                 pts_2d = [
                     (0, 0), (bottom_w, 0), (bottom_w, base_v),
                     (right_at_mid, mid_off), (right_at_top, total_h),
                     (left_at_top, total_h), (0, base_v),
                 ]
             elif geo.get("type") == "metallic":
                 kerb_h = geo.get("kerb_height", 150.0)
                 bottom_w = geo.get("median_width", geo.get("kerb_bottom_width", 550))
                 kerb_top = geo.get("kerb_top_width", 500)
                 offset = (bottom_w - kerb_top) / 2
                 pts_2d = [
                     (0, 0), (bottom_w, 0),
                     (bottom_w - offset, kerb_h),
                     (offset, kerb_h),
                 ]
             else: 
                 # Median / Others fallback
                 total_h = geo.get("total_height", geo.get("kerb_height", 1100))
                 bottom_w = geo.get("median_width", geo.get("bottom_width", geo.get("kerb_bottom_width", 1200)))
                 pts_2d = [(0, 0), (bottom_w, 0), (bottom_w, total_h), (0, total_h)]

             # 2. Apply Mirroring for Right Side (Orientation Fix)
             is_right_side = item.y_offset > 0.5 
             if is_right_side:
                 pts_2d = [(bottom_w - x, y) for x, y in pts_2d]

             # 3. Scaling and Transformation
             pts_2d_m = [(x * s, y * s) for x, y in pts_2d]
             
             x_start = item.y_offset * math.tan(math.radians(item.skew)) if hasattr(item, 'skew') else 0
             deck_top = shared["deck_top_m"]
             
             y_origin = item.y_offset * s - (bottom_w * s / 2.0)
             scaled_origin = [x_start * s, y_origin, deck_top]
             
             prof = self.mapper.create_polygonal_profile(pts_2d_m, "BarrierProfile")
             place = self.mapper.create_axis2placement_3d(scaled_origin, z_dir=[1,0,0], x_dir=[0,1,0])
             local_identity = self.mapper.create_axis2placement_3d((0,0,0), z_dir=(0,0,1), x_dir=(1,0,0))
             solid = self.mapper.create_extruded_solid(prof, item.span * s, local_identity)
             
             shape = self.file.createIfcShapeRepresentation(self.mapper._context3d, "Body", "SweptSolid", [solid])
             prod_def = self.file.createIfcProductDefinitionShape(None, None, [shape])
             # Map Median to IfcWall if it's high, otherwise IfcBuildingElementProxy
             elem_type = self.file.createIfcWall if item._class_name == "BarrierSweep" else self.file.createIfcBuildingElementProxy
             elem = elem_type(create_ifc_guid(), self._owner_history, Name=item.ifc_name, ObjectPlacement=self.file.createIfcLocalPlacement(self.storey.ObjectPlacement, place), Representation=prod_def)
             self.bind_element_to_storey(elem)

        def _process_railing(item):
             geo = getattr(item, 'geo', {})
             import math
             
             rail_w = geo.get("width", 375)
             rail_h = geo.get("height", 1100)
             prof = self.mapper.create_rectangular_profile(rail_w * s, rail_h * s)
             
             x_start = item.y_offset * math.tan(math.radians(item.skew)) if hasattr(item, 'skew') else 0
             deck_top = shared["deck_top_m"]
             
             scaled_origin = [x_start * s, item.y_offset * s, deck_top + rail_h * s / 2.0]
             place = self.mapper.create_axis2placement_3d(scaled_origin, z_dir=[1,0,0], x_dir=[0,1,0])
             local_identity = self.mapper.create_axis2placement_3d((0,0,0), z_dir=(0,0,1), x_dir=(1,0,0))
             solid = self.mapper.create_extruded_solid(prof, item.span * s, local_identity)
             
             shape = self.file.createIfcShapeRepresentation(self.mapper._context3d, "Body", "SweptSolid", [solid])
             prod_def = self.file.createIfcProductDefinitionShape(None, None, [shape])
             elem = self.file.createIfcRailing(create_ifc_guid(), self._owner_history, Name=item.ifc_name, ObjectPlacement=self.file.createIfcLocalPlacement(self.storey.ObjectPlacement, place), Representation=prod_def)
             self.bind_element_to_storey(elem)

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
