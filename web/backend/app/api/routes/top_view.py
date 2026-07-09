"""
top_view_router.py
──────────────────
Generates the top-view SVG and hover-zones for any span / carriageway
combination, then NORMALISES everything to a fixed 1400 × 700 canvas
before sending it to the frontend.

That means:
  • The SVG always has  viewBox="0 0 1400 700"  width="1400"  height="700"
  • Hover-zone coords are always in  0–1400 / 0–700  space
  • The frontend never needs to guess units or scale factors
"""

from __future__ import annotations

import re
from fastapi import APIRouter
from fastapi.responses import Response, JSONResponse
from PySide6.QtWidgets import QApplication

from app.models.bridge import BridgeInput
from osdagbridge.desktop.ui.docks.cad_top_view import TopViewCADWidget

router = APIRouter(prefix="/top-view", tags=["Top View"])

_qt_app = QApplication.instance() or QApplication([])
_widget: TopViewCADWidget | None = None

# Fixed output canvas — the frontend always expects this
OUT_W = 1400
OUT_H = 700


# ─────────────────────────────────────────────────────────────────────────────
# Qt widget singleton
# ─────────────────────────────────────────────────────────────────────────────

def get_widget() -> TopViewCADWidget:
    global _widget
    if _widget is None:
        _widget = TopViewCADWidget()
        _widget.resize(OUT_W, OUT_H)
    return _widget


# ─────────────────────────────────────────────────────────────────────────────
# Unit helpers
# ─────────────────────────────────────────────────────────────────────────────

def _to_mm(value: float | int | None, fallback_mm: float) -> float:
    """
    Convert user input to millimetres.

    Users may type metres (35) or millimetres (35000).
    Rule: if the raw value is < 500 we assume metres and multiply by 1000.
          if >= 500 we assume it is already in mm.
    This correctly handles:
        35      →  35 000 mm   (35 m span)
        350     →  350 000 mm  (350 m span — very long but valid)
        3500    →  3 500 mm    (3.5 m girder spacing — already mm)
        35000   →  35 000 mm   (35 000 mm = 35 m span — already mm)
        350000  →  350 000 mm  (350 m span already in mm)
    """
    if value is None:
        return fallback_mm
    v = float(value)
    return v * 1000.0 if v < 500 else v


def _build_params(data: BridgeInput) -> dict:
    # ── Span ──────────────────────────────────────────────────────────────
    if data.span_length:
        span_mm = _to_mm(data.span_length, 35_000)
    elif data.span:
        span_mm = _to_mm(data.span, 35_000)
    else:
        span_mm = 35_000.0

    # ── Carriageway width ─────────────────────────────────────────────────
    cw_raw = data.carriageway_width or data.overall_bridge_width or data.width
    cw_mm  = _to_mm(cw_raw, 12_000)

    # ── Cross bracing spacing ─────────────────────────────────────────────
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

    return {
        "span_length":           span_mm,
        "carriageway_width":     cw_mm,
        "num_girders":           int(data.no_of_girders or data.num_girders or 4),
        "girder_spacing":        _to_mm(data.girder_spacing,        2_750),
        "cross_bracing_spacing": cb_spacing_mm,
        "skew_angle":            float(data.skew_angle or 0),
        "deck_overhang":         _to_mm(data.deck_overhang_width,   1_000),
        "footpath_width":        _to_mm(data.footpath_width,        1_500),
        "footpath_thickness":    _to_mm(data.footpath_thickness,      200),
        "crash_barrier_width":   _to_mm(data.crash_barrier_width,     500),
        "median_present":        bool(data.median_present or False),
        "median_width":          _to_mm(data.median_width,          1_200),
    }


# ─────────────────────────────────────────────────────────────────────────────
# SVG normalisation
# ─────────────────────────────────────────────────────────────────────────────

def _parse_viewbox(svg: str) -> tuple[float, float, float, float] | None:
    m = re.search(r'viewBox=["\']([^"\']+)["\']', svg, re.IGNORECASE)
    if not m:
        return None
    parts = re.split(r'[\s,]+', m.group(1).strip())
    if len(parts) != 4:
        return None
    try:
        return tuple(float(p) for p in parts)          # type: ignore[return-value]
    except ValueError:
        return None


def _normalise_svg(svg: str) -> tuple[str, float, float, float, float]:
    """
    Rewrite the SVG so it always has viewBox="0 0 1400 700".

    Returns
    -------
    (normalised_svg, src_vb_x, src_vb_y, src_vb_w, src_vb_h)

    Strategy
    --------
    Wrap the original content in a  <g transform="scale(sx,sy) translate(-vbx,-vby)">
    so that the original coordinate space maps linearly onto 0–1400 / 0–700.
    """
    vb = _parse_viewbox(svg)

    if vb:
        vbx, vby, vbw, vbh = vb
    else:
        # No viewBox — try width/height attributes
        wm = re.search(r'<svg\b[^>]*\bwidth=["\']([0-9.]+)', svg, re.IGNORECASE)
        hm = re.search(r'<svg\b[^>]*\bheight=["\']([0-9.]+)', svg, re.IGNORECASE)
        vbx, vby = 0.0, 0.0
        vbw = float(wm.group(1)) if wm else float(OUT_W)
        vbh = float(hm.group(1)) if hm else float(OUT_H)

    sx = OUT_W / vbw if vbw else 1.0
    sy = OUT_H / vbh if vbh else 1.0

    # Remove existing width / height / viewBox from the <svg> open tag
    def strip_svg_attr(tag: str) -> str:
        tag = re.sub(r'\s+width=["\'][^"\']*["\']',  '', tag)
        tag = re.sub(r'\s+height=["\'][^"\']*["\']', '', tag)
        tag = re.sub(r'\s+viewBox=["\'][^"\']*["\']','', tag, flags=re.IGNORECASE)
        return tag

    # Replace the <svg ...> opening tag
    def replace_svg_open(m: re.Match) -> str:
        tag = strip_svg_attr(m.group(0))
        # Insert our fixed canvas attributes just before the closing >
        tag = re.sub(
            r'\s*/?>$',
            f' width="{OUT_W}" height="{OUT_H}" viewBox="0 0 {OUT_W} {OUT_H}">',
            tag
        )
        return tag

    svg_out = re.sub(r'<svg\b[^>]*>', replace_svg_open, svg, count=1, flags=re.IGNORECASE)

    # Wrap all existing content in a scaling group
    # Find the position right after the <svg ...> tag
    svg_open_end = re.search(r'<svg\b[^>]*>', svg_out, re.IGNORECASE)
    if svg_open_end:
        insert_after = svg_open_end.end()
        scale_open  = f'<g transform="scale({sx},{sy}) translate({-vbx},{-vby})">'
        scale_close = '</g>'
        # Insert opening wrapper after <svg> and closing wrapper before </svg>
        svg_out = (
            svg_out[:insert_after]
            + scale_open
            + svg_out[insert_after:]
        )
        close_pos = svg_out.rfind('</svg>')
        if close_pos != -1:
            svg_out = svg_out[:close_pos] + scale_close + svg_out[close_pos:]

    return svg_out, vbx, vby, vbw, vbh


def _normalise_zones(
    zones_payload: dict,
    src_vbx: float, src_vby: float,
    src_vbw: float, src_vbh: float,
) -> dict:
    """
    Remap zone coords from whatever space the backend returned
    into the normalised  0–OUT_W / 0–OUT_H  canvas.
    """
    raw_zones = zones_payload.get("zones", [])

    # Determine the coordinate space the backend used for zones
    # (it may return widget_width/height, or the raw viewBox dims)
    backend_w = float(zones_payload.get("widget_width",  src_vbw or OUT_W))
    backend_h = float(zones_payload.get("widget_height", src_vbh or OUT_H))

    # Scale factors: backend zone space → normalised canvas
    zsx = OUT_W / backend_w if backend_w else 1.0
    zsy = OUT_H / backend_h if backend_h else 1.0

    normalised = []
    for z in raw_zones:
        normalised.append({
            **z,
            "x":      z["x"]      * zsx,
            "y":      z["y"]      * zsy,
            "width":  z["width"]  * zsx,
            "height": z["height"] * zsy,
        })

    return {
        **zones_payload,
        "zones":        normalised,
        "widget_width":  OUT_W,
        "widget_height": OUT_H,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/generate")
def generate_top_view(data: BridgeInput):
    widget = get_widget()
    params = _build_params(data)
    widget.update_params(params)

    raw_svg   = widget.export_svg()
    raw_zones = widget.export_hover_zones()

    # Normalise SVG → always 1400×700
    norm_svg, vbx, vby, vbw, vbh = _normalise_svg(raw_svg)

    # Normalise zones → always 0–1400 / 0–700
    norm_zones = _normalise_zones(raw_zones, vbx, vby, vbw, vbh)

    widget._cached_svg   = norm_svg
    widget._cached_zones = norm_zones

    return {"status": "generated"}


@router.get("/svg")
def get_svg():
    widget = get_widget()
    svg = getattr(widget, "_cached_svg", None)
    if svg is None:
        raw = widget.export_svg()
        svg, *_ = _normalise_svg(raw)
    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={"Cache-Control": "no-store"},
    )


@router.get("/hover-zones")
def get_hover_zones():
    widget = get_widget()
    zones = getattr(widget, "_cached_zones", None)
    if zones is None:
        raw_svg   = widget.export_svg()
        raw_zones = widget.export_hover_zones()
        _, vbx, vby, vbw, vbh = _normalise_svg(raw_svg)
        zones = _normalise_zones(raw_zones, vbx, vby, vbw, vbh)
    return JSONResponse(
        content=zones,
        headers={"Cache-Control": "no-store"},
    )