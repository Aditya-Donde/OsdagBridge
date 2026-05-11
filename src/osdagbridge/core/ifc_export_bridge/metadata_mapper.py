"""
Metadata Mapper for IFC Export

This module handles mapping custom metadata properties to IFC elements.
"""
import uuid
import ifcopenshell
import sqlite3
from pathlib import Path

_DB_PATH = Path(__file__).resolve().parents[1] / "data" / "ResourceFiles" / "Intg_osdag.sqlite"

def create_ifc_guid():
    return ifcopenshell.guid.compress(uuid.uuid4().hex)

class BridgeMetadataMapper:
    def __init__(self, file, mapper):
        self.file = file
        self.mapper = mapper
        self._steel_cache = {}
        self._concrete_cache = {}

    def _to_meters(self, value):
        """Safely converts mm to meters, handling None values."""
        if value is None:
            return None
        try:
            return float(value) / 1000.0
        except (TypeError, ValueError):
            return None

    def _lookup_material_properties(self, grade: str, is_steel: bool) -> dict:
        """Fetches material properties from Intg_osdag.sqlite database."""
        if not grade or not _DB_PATH.exists():
            return {}
            
        cache = self._steel_cache if is_steel else self._concrete_cache
        if grade in cache:
            return cache[grade]
            
        table = 'Steel_Grade_Properties' if is_steel else 'Concrete_Grade_Properties'
        props = {}
        
        try:
            con = sqlite3.connect(_DB_PATH)
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute(f'SELECT * FROM {table} WHERE "Grade" = ?', (grade,))
            row = cur.fetchone()
            con.close()
            
            if row:
                if is_steel:
                    props["YieldStrength_MPa"] = float(row["Yield Strength"])
                    props["UltimateTensileStrength_MPa"] = float(row["Ultimate Tensile Strength"])
                    props["ModulusOfElasticity_GPa"] = float(row["Modulus of Elasticity"])
                    props["PoissonsRatio"] = float(row["Poisson's Ratio"])
                    props["Density_N_m3"] = float(row["Density"])
                else:
                    props["fck_MPa"] = float(row["fck"])
                    props["fctm_MPa"] = float(row["fctm"])
                    props["Ecm_GPa"] = float(row["Ecm"])
                    
            cache[grade] = props
            return props
        except Exception as e:
            print(f"Error extracting DB properties for {grade}: {e}")
            return {}

    def assign_metadata(self, element, properties, property_set_name="Pset_OsdagBridgeProperties"):
        ifc_props = []
        owner_history = getattr(self.mapper, '_owner_history', None)
        
        for key, value in properties.items():
            if value is None:
                continue
            
            val_type = "IfcLabel"
            if isinstance(value, bool):
                val_type = "IfcBoolean"
            elif isinstance(value, float):
                val_type = "IfcReal"
            elif isinstance(value, int):
                val_type = "IfcInteger"
            else:
                value = str(value)
                
            try:
                ifc_val = self.file.create_entity(val_type, value)
                prop = self.file.createIfcPropertySingleValue(key, None, ifc_val, None)
                ifc_props.append(prop)
            except Exception as e:
                pass
                
        if not ifc_props:
            return
            
        pset = self.file.createIfcPropertySet(
            create_ifc_guid(),
            owner_history,
            property_set_name,
            None,
            ifc_props
        )
        
        self.file.createIfcRelDefinesByProperties(
            create_ifc_guid(),
            owner_history,
            None,
            None,
            [element],
            pset
        )

    def map_girder(self, element, cad, ifc_name):
        if not cad: return
        steel_grade = getattr(cad, "steel_grade", "E 250A")
        props = {
            "Material": steel_grade, 
            "SpanLength": self._to_meters(getattr(cad, "span_length_L", 0)),
            "GirderSpacing": self._to_meters(getattr(cad, "girder_spacing", 0))
        }
        
        # Merge DB properties
        db_props = self._lookup_material_properties(steel_grade, is_steel=True)
        props.update(db_props)

        if "Web" in ifc_name:
            props["ComponentRole"] = "Girder Web"
            props["Depth"] = self._to_meters(cad.girder_section_d)
            props["Thickness"] = self._to_meters(cad.girder_section_tw)
        elif "TopFlange" in ifc_name:
            props["ComponentRole"] = "Girder Top Flange"
            props["Width"] = self._to_meters(cad.girder_section_bf)
            props["Thickness"] = self._to_meters(cad.girder_section_tf)
        elif "BottomFlange" in ifc_name:
            props["ComponentRole"] = "Girder Bottom Flange"
            props["Width"] = self._to_meters(cad.girder_section_bf_b)
            props["Thickness"] = self._to_meters(cad.girder_section_tf_b)
        else:
            props["ComponentRole"] = "Main Girder"
            
        self.assign_metadata(element, props)

    def map_deck_slab(self, element, cad):
        if not cad: return
        concrete_grade = getattr(cad, "concrete_grade", "M30")
        props = {
            "ComponentRole": "Deck Slab",
            "DeckThickness": self._to_meters(getattr(cad, "deck_thickness", 0)),
            "CarriagewayWidth": self._to_meters(getattr(cad, "carriageway_width", 0)),
            "SpanLength": self._to_meters(getattr(cad, "span_length_L", 0)),
            "SkewAngle": getattr(cad, "skew_angle", 0),
            "Material": concrete_grade
        }
        
        # Merge DB properties
        db_props = self._lookup_material_properties(concrete_grade, is_steel=False)
        props.update(db_props)
        
        self.assign_metadata(element, props)

    def map_stiffener(self, element, cad, ifc_name):
        if not cad: return
        props = {}
        if "Intermediate" in ifc_name:
            props = {
                "ComponentRole": "Intermediate Stiffener",
                "Thickness": self._to_meters(cad.intermediate_stiffener_thickness),
                "Spacing": self._to_meters(cad.intermediate_stiffener_spacing),
                "Outstand": self._to_meters(getattr(cad, "intermediate_stiffener_outstand", None))
            }
        elif "End" in ifc_name:
            props = {
                "ComponentRole": "End Stiffener",
                "Thickness": self._to_meters(cad.end_stiffener_thickness),
                "Outstand": self._to_meters(getattr(cad, "end_stiffener_outstand", None))
            }
        elif "Longitudinal" in ifc_name:
            props = {
                "ComponentRole": "Longitudinal Stiffener",
                "Thickness": self._to_meters(cad.longitudinal_stiffener_thickness),
                "Outstand": self._to_meters(getattr(cad, "longitudinal_stiffener_outstand", None))
            }
        
        if props:
            steel_grade = getattr(cad, "steel_grade", "E 250A")
            props["Material"] = steel_grade
            db_props = self._lookup_material_properties(steel_grade, is_steel=True)
            props.update(db_props)
            self.assign_metadata(element, props)

    def map_brace(self, element, cad, item):
        if not cad: return
        
        props = {}
        is_end_diaphragm = "EndDiaphragm" in item.ifc_name

        sys_name = "End Diaphragm" if is_end_diaphragm else "Intermediate Bracing"
        prefix = "end_diaphragm_" if is_end_diaphragm else ""

        if "TopChord" in item.ifc_name:
            c_prefix = prefix + "top_chord" if is_end_diaphragm else "top_chord"
            props = {
                "ComponentRole": f"{sys_name} Top Chord",
                "ProfileType": getattr(cad, f"{c_prefix}_section_type", ""),
                "ProfileThickness": self._to_meters(getattr(cad, f"{c_prefix}_thickness", None)),
                "StructuralSystem": sys_name
            }
        elif "BottomChord" in item.ifc_name:
            c_prefix = prefix + "bottom_chord" if is_end_diaphragm else "bottom_chord"
            props = {
                "ComponentRole": f"{sys_name} Bottom Chord",
                "ProfileType": getattr(cad, f"{c_prefix}_section_type", ""),
                "ProfileThickness": self._to_meters(getattr(cad, f"{c_prefix}_thickness", None)),
                "StructuralSystem": sys_name
            }
        elif "Diagonal" in item.ifc_name:
            c_prefix = prefix + "diagonal" if is_end_diaphragm else "diagonal"
            bracing_pattern = cad.end_diaphragm_bracing_type if is_end_diaphragm else cad.bracing_type
            props = {
                "ComponentRole": f"{sys_name} Diagonal",
                "BracingPattern": bracing_pattern,
                "ProfileType": getattr(cad, f"{c_prefix}_section_type", ""),
                "ProfileThickness": self._to_meters(getattr(cad, f"{c_prefix}_thickness", None)),
                "StructuralSystem": sys_name
            }

        # Dynamically map the unpacked dimensions based on the shape type
        if hasattr(item, 'dims') and isinstance(item.dims, dict):
            if props.get("ProfileType") in ["ANGLE", "DOUBLE_ANGLE"]:
                props["ProfileDepth_or_LegHeight"] = self._to_meters(item.dims.get("leg_h"))
                props["ProfileWidth_or_LegWidth"] = self._to_meters(item.dims.get("leg_w"))
                if "connection_type" in item.dims:
                    props["ConnectionType"] = item.dims.get("connection_type")
            else:
                props["ProfileDepth_or_LegHeight"] = self._to_meters(item.dims.get("depth"))
                props["ProfileWidth_or_LegWidth"] = self._to_meters(item.dims.get("flange_width"))
                if "web_thickness" in item.dims:
                    props["WebThickness"] = self._to_meters(item.dims.get("web_thickness"))
                if "flange_thickness" in item.dims:
                    props["FlangeThickness"] = self._to_meters(item.dims.get("flange_thickness"))
                if "connection_type" in item.dims:
                    props["ConnectionType"] = item.dims.get("connection_type")

        if props:
            steel_grade = getattr(cad, "steel_grade", "E 250A")
            props["Material"] = steel_grade
            db_props = self._lookup_material_properties(steel_grade, is_steel=True)
            props.update(db_props)
            self.assign_metadata(element, props)

    def map_barrier(self, element, cad, ifc_name):
        if not cad: return
        props = {}
        if "CrashBarrier" in ifc_name:
            props = {
                "ComponentRole": "Crash Barrier",
                "Standard": cad.barrier_type,
                "SubType": cad.crash_barrier_subtype
            }
        elif "Median" in ifc_name:
            props = {
                "ComponentRole": "Median",
                "Standard": cad.median_type,
            }
        elif "Railing" in ifc_name:
            props = {
                "ComponentRole": "Railing",
                "Standard": cad.railing_type,
            }
            if cad.railing_type.lower() == "steel":
                props["RailCount"] = getattr(cad, "rail_count", 0)
                props["PostSpacing"] = 2.0
            else:
                props["RailingStyle"] = "Continuous"
            
        if props:
            self.assign_metadata(element, props)
