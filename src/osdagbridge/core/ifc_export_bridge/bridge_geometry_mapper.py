"""
Bridge Geometry Mapper
Transforms generic extracted parameters into IFC4 geometry components.
Operates completely independently from the legacy Osdag general exporter.
"""
import uuid
import math
import ifcopenshell

def create_ifc_guid():
    return ifcopenshell.guid.compress(uuid.uuid4().hex)

class BridgeGeometryMapper:
    def __init__(self, ifc_file):
        self.file = ifc_file
        self._context2d = self._get_or_create_context("Model", "Plan", "GeometricCurveSet")
        self._context3d = self._get_or_create_context("Model", "Body", "SweptSolid")
        
    def _get_or_create_context(self, ctx_type, ctx_id, ctx_type_qualifier):
        contexts = self.file.by_type("IfcGeometricRepresentationContext")
        for ctx in contexts:
            if ctx.ContextType == ctx_type and ctx.ContextIdentifier == ctx_id:
                return ctx
        # Create fallback contexts
        return self.file.createIfcGeometricRepresentationContext(
            ContextIdentifier=ctx_id, ContextType=ctx_type, CoordinateSpaceDimension=2 if ctx_type_qualifier == "GeometricCurveSet" else 3,
            Precision=1e-5, WorldCoordinateSystem=self.file.createIfcAxis2Placement3D(self.file.createIfcCartesianPoint((0.,0.,0.)))
        )

    def define_material(self, name="Steel"):
        mat = self.file.createIfcMaterial(name)
        return mat
        
    def create_cartesian_point_2d(self, x, y):
        return self.file.createIfcCartesianPoint((float(x), float(y)))

    def create_cartesian_point_3d(self, x, y, z):
        return self.file.createIfcCartesianPoint((float(x), float(y), float(z)))

    def create_axis2placement_3d(self, origin, z_dir=(0.,0.,1.), x_dir=(1.,0.,0.)):
        pt = self.create_cartesian_point_3d(*origin)
        hdr = self.file.createIfcDirection([float(v) for v in z_dir])
        xdr = self.file.createIfcDirection([float(v) for v in x_dir])
        return self.file.createIfcAxis2Placement3D(pt, hdr, xdr)
        
    def create_axis2placement_2d(self, origin=(0.,0.), x_dir=(1.,0.)):
        pt = self.create_cartesian_point_2d(*origin)
        xdr = self.file.createIfcDirection([float(v) for v in x_dir])
        return self.file.createIfcAxis2Placement2D(pt, xdr)

    # --- NATIVE PROFILE TRANSLATORS ---
    
    def create_rectangular_profile(self, width, height):
        return self.file.createIfcRectangleProfileDef(
            ProfileType="AREA", ProfileName=None,
            Position=self.create_axis2placement_2d(),
            XDim=float(width), YDim=float(height)
        )
        
    def create_l_shape_profile(self, depth, width, thickness):
        return self.file.createIfcLShapeProfileDef(
            ProfileType="AREA", ProfileName=None,
            Position=self.create_axis2placement_2d(),
            Depth=float(depth), Width=float(width),
            Thickness=float(thickness), FilletRadius=None, EdgeRadius=None,
            LegSlope=None
        )

    def create_c_shape_profile(self, depth, width, web_thickness, flange_thickness):
        return self.file.createIfcCShapeProfileDef(
            ProfileType="AREA", ProfileName=None,
            Position=self.create_axis2placement_2d(),
            Depth=float(depth), Width=float(width),
            WallThickness=float(web_thickness), Girth=float(flange_thickness), InternalFilletRadius=None
        )

    def create_double_angle_profile(self, leg_h, leg_w, thickness, connection_type):
        """Builds a composite polygonal profile for two back-to-back angles."""
        # Using a polygonal profile definition explicitly mapped from coordinates
        pts = []
        if connection_type == "SHORTER_LEG":
            # Mirrors around X-axis
            pts = [
                (-leg_h, -thickness), (0, -thickness), (0, -leg_w),
                (thickness, -leg_w), (thickness, -thickness), (thickness+leg_h, -thickness),
                (thickness+leg_h, 0), (thickness, 0), (thickness, leg_w-thickness),
                (0, leg_w-thickness), (0, 0), (-leg_h, 0)
            ]
        else: # LONGER_LEG
            pts = [
                (-leg_w, -thickness), (0, -thickness), (0, -leg_h),
                (thickness, -leg_h), (thickness, -thickness), (thickness+leg_w, -thickness),
                (thickness+leg_w, 0), (thickness, 0), (thickness, leg_h-thickness),
                (0, leg_h-thickness), (0, 0), (-leg_w, 0)
            ]
        
        ifc_pts = [self.create_cartesian_point_2d(p[0], p[1]) for p in pts]
        polyline = self.file.createIfcPolyline(ifc_pts + [ifc_pts[0]]) # Close loop
        return self.file.createIfcArbitraryClosedProfileDef("AREA", "DoubleAngle", polyline)

    def create_double_channel_profile(self, depth, width, tw, tf):
        """Builds a composite polygonal profile for two back-to-back channels."""
        gap = width # standard gap 
        pts = [
            (-width, depth/2), (0, depth/2), (0, -depth/2), (-width, -depth/2),
            (-width, -depth/2+tf), (-tw, -depth/2+tf), (-tw, depth/2-tf), (-width, depth/2-tf),
            # Transition to second channel via gap
            (gap, depth/2-tf), (gap+tw, depth/2-tf), (gap+tw, -depth/2+tf), (gap, -depth/2+tf),
            (gap, -depth/2), (gap+width, -depth/2), (gap+width, depth/2), (gap, depth/2)
        ]
        ifc_pts = [self.create_cartesian_point_2d(p[0], p[1]) for p in pts]
        polyline = self.file.createIfcPolyline(ifc_pts + [ifc_pts[0]])
        return self.file.createIfcArbitraryClosedProfileDef("AREA", "DoubleChannel", polyline)
        
    def create_polygonal_profile(self, points, name="Polygon"):
        """Used for custom skewed deck slabs and continuous crash barriers."""
        ifc_pts = [self.create_cartesian_point_2d(p[0], p[1]) for p in points]
        polyline = self.file.createIfcPolyline(ifc_pts + [ifc_pts[0]])
        return self.file.createIfcArbitraryClosedProfileDef("AREA", name, polyline)

    # --- GEOMETRIC SOLID EXTRUSION ---
    
    def create_extruded_solid(self, profile, thickness, position_3d):
        """
        Creates standard orthogonal extrusions (IfcExtrudedAreaSolid).
        Used for regular objects.
        """
        extrusion_dir = self.file.createIfcDirection((0., 0., 1.))
        return self.file.createIfcExtrudedAreaSolid(
            SweptArea=profile,
            Position=position_3d,
            ExtrudedDirection=extrusion_dir,
            Depth=float(thickness)
        )
        
    def create_faceted_brep_from_3d_deck(self, top_points_3d, thickness):
        """
        Constructs an IfcFacetedBrep directly from 3D shear-mapped coordinates.
        This provides perfect bounding for the skewed parallelograms without
        relying on directional sweeps which can fail in some IFC viewers.
        top_points_3d = list of (x,y,z) forming the top plane.
        """
        bot_points_3d = [(p[0], p[1], p[2] - thickness) for p in top_points_3d]
        
        # Create IFC Cartesian Points
        top_ifc_pts = [self.create_cartesian_point_3d(*p) for p in top_points_3d]
        bot_ifc_pts = [self.create_cartesian_point_3d(*p) for p in bot_points_3d]
        
        # Build Faces (Top, Bottom, 4 Sides)
        faces = []
        top_polyloop = self.file.createIfcPolyLoop(top_ifc_pts)
        faces.append(self.file.createIfcFaceOuterBound(top_polyloop, True))
        
        bot_polyloop = self.file.createIfcPolyLoop(list(reversed(bot_ifc_pts)))
        faces.append(self.file.createIfcFaceOuterBound(bot_polyloop, True))
        
        for i in range(len(top_points_3d)):
            next_i = (i + 1) % len(top_points_3d)
            # CCW order looking from outside: bot[i] -> bot[next] -> top[next] -> top[i]
            side_pts = [bot_ifc_pts[i], bot_ifc_pts[next_i], top_ifc_pts[next_i], top_ifc_pts[i]]
            side_loop = self.file.createIfcPolyLoop(side_pts)
            faces.append(self.file.createIfcFaceOuterBound(side_loop, True))
            
        ifc_faces = [self.file.createIfcFace([bnd]) for bnd in faces]
        shell = self.file.createIfcClosedShell(ifc_faces)
        return self.file.createIfcFacetedBrep(shell)
