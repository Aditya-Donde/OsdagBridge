# app/routers/cross_section.py  (replace your existing file)

from fastapi import APIRouter
from fastapi.responses import Response, JSONResponse
from PySide6.QtWidgets import QApplication

from app.models.bridge import BridgeInput
from osdagbridge.desktop.ui.docks.cad_cross_section import CrossSectionCADWidget

router = APIRouter(prefix="/cross-section", tags=["Cross Section"])

# ── Ensure a Qt application exists (headless) ────────────────────────────────
_qt_app = QApplication.instance() or QApplication([])

# ── Single persistent widget instance ────────────────────────────────────────
_widget: CrossSectionCADWidget | None = None

RENDER_W = 1400
RENDER_H = 700


def _get_or_create_widget() -> CrossSectionCADWidget:
    global _widget
    if _widget is None:
        _widget = CrossSectionCADWidget()
        _widget.resize(RENDER_W, RENDER_H)
    return _widget


def _to_mm(value: float | int | None, fallback_mm: float) -> float:
    if value is None:
        return fallback_mm
    v = float(value)
    return v * 1000.0 if v < 500 else v


def _build_params(data: BridgeInput) -> dict:

    # ---- FRONTEND VALUES COME IN METERS ----
    # Convert ONLY geometric width values to mm

    overall_width_mm = (
        (data.overall_bridge_width * 1000)
        if data.overall_bridge_width
        else (
            (data.width * 1000)
            if data.width
            else 12000
        )
    )

    carriageway_mm = (
        (data.carriageway_width * 1000)
        if data.carriageway_width
        else overall_width_mm
    )

    girder_spacing_mm = (
        (data.girder_spacing * 1000)
        if data.girder_spacing
        else 2750
    )

    deck_overhang_mm = (
        (data.deck_overhang_width * 1000)
        if data.deck_overhang_width
        else 1000
    )

    footpath_width_mm = (
        (data.footpath_width * 1000)
        if data.footpath_width
        else 1500
    )

    # ---- THESE ARE ALREADY IN MM ----

    deck_thickness_mm = data.deck_thickness or 200

    footpath_thickness_mm = (
        data.footpath_thickness or 200
    )

    cb_spacing_m = 3.5
    if data.member_properties and isinstance(data.member_properties, dict):
        cross_bracing = data.member_properties.get("cross_bracing")
        if isinstance(cross_bracing, dict):
            spacing_val = cross_bracing.get("spacing")
            if spacing_val is not None:
                try:
                    cb_spacing_m = float(spacing_val)
                except ValueError:
                    pass
            else:
                by_member = cross_bracing.get("cross_bracing_by_member")
                if isinstance(by_member, dict) and by_member:
                    first_member = list(by_member.values())[0]
                    if isinstance(first_member, dict):
                        spacing_val = first_member.get("spacing")
                        if spacing_val is not None:
                            try:
                                cb_spacing_m = float(spacing_val)
                            except ValueError:
                                pass
    cb_spacing_mm = _to_mm(cb_spacing_m, 3500.0)

    params = {
        "span_length":
            (data.span_length or 35000),

        "carriageway_width":
            carriageway_mm,

        "num_girders":
            data.no_of_girders or 4,

        "girder_spacing":
            girder_spacing_mm,

        "cross_bracing_spacing":
            cb_spacing_mm,

        "deck_overhang":
            deck_overhang_mm,

        "deck_thickness":
            deck_thickness_mm,

        "footpath_width":
            footpath_width_mm,

        "footpath_thickness":
            footpath_thickness_mm,

        "skew_angle":
            data.skew_angle or 0,

        "median_present":
            data.median_present or False,

        "median_width":
            data.median_width or 1200,

        "crash_barrier_width":
            data.crash_barrier_width or 500,

        "railing_width":
            data.railing_width or 375,

        "railing_height":
            data.railing_height or 1000,

        "wearing_course_thickness":
            data.wearing_course_thickness or 50,
    }

    return params


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/generate")
def generate_cross_section(data: BridgeInput):
    """
    Receive bridge parameters, update the widget, re-render SVG + hover zones.
    Frontend calls this on every debounced form change and on Save.
    """
    widget = _get_or_create_widget()
    params = _build_params(data)

    # Push params into the widget — this triggers internal state update
    widget.update_params(params)

    # Force a synchronous re-render at the fixed export size so SVG + zones
    # are in sync before the frontend fetches /svg and /hover-zones
    svg = widget.export_svg()
    zones = widget.export_hover_zones()

    # Cache on the widget so /hover-zones can serve instantly without re-render
    widget._cached_zones = zones
    widget._cached_svg   = svg

    return {"status": "generated", "zone_count": len(zones.get("zones", []))}


@router.get("/svg")
def get_cross_section_svg():
    """Return the most recently generated SVG."""
    widget = _get_or_create_widget()

    # Serve cached SVG if available (set by /generate)
    svg = getattr(widget, "_cached_svg", None)
    if not svg:
        # Fallback: render now with current params
        svg = widget.export_svg()
        zones = widget.export_hover_zones()
        widget._cached_zones = zones
        widget._cached_svg   = svg

    return Response(content=svg, media_type="image/svg+xml",
                    headers={"Cache-Control": "no-store"})


@router.get("/hover-zones")
def get_hover_zones():
    """Return hover zone data for the most recently generated SVG."""
    widget = _get_or_create_widget()

    zones = getattr(widget, "_cached_zones", None)
    if zones is None:
        # Fallback: render to get zones
        svg = widget.export_svg()
        zones = widget.export_hover_zones()
        widget._cached_svg   = svg
        widget._cached_zones = zones

    return JSONResponse(content=zones,
                        headers={"Cache-Control": "no-store"})


@router.get("/steel-sections")
def get_steel_sections():
    """Return all angle and channel designations from the SQLite section catalog."""
    try:
        from osdagbridge.desktop.ui.widgets.section_viewer import SectionCatalog
        catalog = SectionCatalog()
        angles = catalog.list_angles()
        channels = catalog.list_channels()
        return JSONResponse(content={"angles": angles, "channels": channels})
    except Exception as exc:
        return JSONResponse(
            content={"angles": [], "channels": [], "error": str(exc)},
            status_code=200,
        )


@router.get("/rolled-sections")
def get_rolled_sections():
    """Return all available rolled sections from the SQLite catalog and their design properties."""
    from osdagbridge.desktop.ui.dialogs.tabs.sub_tabs.section_properties.girder_details_tab import girder_properties
    sections = girder_properties.list_available_sections()
    result = {}
    for designation, sec in sections.items():
        result[designation] = {
            "mass": sec.mass_per_meter_kg,
            "area": sec.area_cm2,
            "depth": sec.depth_mm,
            "tfw": sec.flange_width_mm,
            "tft": sec.flange_thickness_mm,
            "bfw": sec.flange_width_mm,
            "bft": sec.flange_thickness_mm,
            "wt": sec.web_thickness_mm,
            "iz": sec.moment_of_inertia_zz_cm4,
            "iy": sec.moment_of_inertia_yy_cm4,
            "rz": sec.radius_of_gyration_z_cm,
            "ry": sec.radius_of_gyration_y_cm,
            "zz": sec.elastic_section_modulus_z_cm3,
            "zy": sec.elastic_section_modulus_y_cm3,
            "zpz": sec.plastic_section_modulus_z_cm3,
            "zpy": sec.plastic_section_modulus_y_cm3,
            "it": sec.torsion_constant_cm4,
            "iw": sec.warping_constant_cm6
        }
    return JSONResponse(content=result)