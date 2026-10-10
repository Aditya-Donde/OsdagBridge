from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Trsf
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeFace, BRepBuilderAPI_Transform
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve
from OCC.Core.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCC.Core.TopAbs import TopAbs_EDGE
from OCC.Core.TopExp import TopExp_Explorer
from osdagbridge.core.utils.common import girder_catalog, VALUES_GIRDER_TYPE

_cache = {}

def _profile(g_type, designation):
    p = girder_catalog.get_beam_profile(designation) if g_type == VALUES_GIRDER_TYPE[1] else None
    return p if p is not None and min(p.depth_mm, p.web_thickness_mm, p.flange_width_mm, p.flange_thickness_mm) > 0 else None

def get_rolled_dims(g_type, designation):
    p = _profile(g_type, designation)
    return None if p is None else (p.depth_mm - 2*p.flange_thickness_mm, p.web_thickness_mm, p.flange_width_mm, p.flange_thickness_mm)

def _fillet(shape, r, corners):
    if r <= 0:
        return shape
    try:
        edges = []
        ex = TopExp_Explorer(shape, TopAbs_EDGE)
        while ex.More():
            e = ex.Current()
            if not any(e.IsSame(q) for q in edges):
                edges.append(e)
            ex.Next()
        def is_corner(e):
            c = BRepAdaptor_Curve(e)
            a, d = c.Value(c.FirstParameter()), c.Value(c.LastParameter())
            return abs(a.X()-d.X()) < 1e-6 and abs(a.Z()-d.Z()) < 1e-6 and abs(a.Y()-d.Y()) >= 1e-6 and any(abs(a.X()-x) < 1e-6 and abs(a.Z()-z) < 1e-6 for x, z in corners)
        sel = [e for e in edges if is_corner(e)]
        if len(sel) != 4:
            return shape
        fillet = BRepFilletAPI_MakeFillet(shape)
        for e in sel:
            fillet.Add(r, e)
        fillet.Build()
        return fillet.Shape() if fillet.IsDone() else shape
    except Exception:
        return shape

def _build(length, p):
    h, b, w, T = p.depth_mm / 2, p.flange_width_mm / 2, p.web_thickness_mm / 2, p.flange_thickness_mm
    xz = [(-b, h), (b, h), (b, h-T), (w, h-T), (w, -h+T), (b, -h+T), (b, -h), (-b, -h), (-b, -h+T), (-w, -h+T), (-w, h-T), (-b, h-T)]
    pts = [gp_Pnt(x, 0, z) for x, z in xz]
    wire = BRepBuilderAPI_MakeWire()
    for i in range(12):
        wire.Add(BRepBuilderAPI_MakeEdge(pts[i], pts[(i+1) % 12]).Edge())
    solid = BRepPrimAPI_MakePrism(BRepBuilderAPI_MakeFace(wire.Wire()).Face(), gp_Vec(0, length, 0)).Shape()
    roots = [(x, z) for x in (-w, w) for z in (-(h-T), h-T)]
    toes = [(x, z) for x in (-b, b) for z in (-(h-T), h-T)]
    shape = _fillet(solid, p.root_radius_mm, roots)
    shape = _fillet(shape, p.toe_radius_mm, toes)
    return shape

def get_rolled_girder(g_type, designation, length, z_top, y):
    p = _profile(g_type, designation)
    if p is None:
        return None
    key = (length, designation)
    if key not in _cache:
        _cache[key] = _build(length, p)
    t = gp_Trsf()
    t.SetTranslation(gp_Vec(0, y, z_top - p.depth_mm / 2))
    return BRepBuilderAPI_Transform(_cache[key], t, True).Shape()