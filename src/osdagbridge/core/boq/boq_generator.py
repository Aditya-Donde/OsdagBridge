# =============================================================================
# OsdagBridge — BOQ (Bill of Quantities) Generator
# =============================================================================

import logging
import math
from typing import Any

from osdagbridge.core.bridge_components.super_structure.crash_barrier.properties import RCC_DENSITY
from osdagbridge.core.utils.common import (
    KEY_CB_AREA,
    KEY_CB_DENSITY,
    KEY_CB_LOAD,
    KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
    KEY_MP_GIRDER_DEPTH,
    KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
    KEY_MP_STIFFENER_BEARING_OUTSTAND,
    KEY_MP_STIFFENER_BEARING_THICKNESS,
    KEY_MP_STIFFENER_INTERMEDIATE,
    KEY_MP_STIFFENER_INTERMEDIATE_OUTSTAND,
    KEY_MP_STIFFENER_INTERMEDIATE_SPACING,
    KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS,
    KEY_MP_STIFFENER_NO_BEARING_STIFFENERS,
    KEY_SPAN,
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_GIRDER_SPACING,
)

logger = logging.getLogger("osdagbridge.core.boq_generator")


def resolve_girder_value(source: dict, base_key: str, i: int = 0) -> Any:
    """Resolve a girder property from an input/output dict, tolerating both the
    per-girder dynamic key scheme and the legacy scalar key.
    """
    candidates = [
        f"{base_key}.G{i + 1}.M1",
        base_key,
        f"{base_key}.G1.M1"
    ]
    for key in candidates:
        if key in source:
            return source[key]
    raise KeyError(base_key)


STEEL_DENSITY_T_PER_M3 = 7.85

# Connection material (splices, gussets, bolts, cleats) is taken as a
# percentage of the girder steel it joins, per standard take-off practice.
CONNECTION_ALLOWANCE = 0.10


def _num(value):
    """Best-effort float conversion; returns None for blank/placeholder text."""
    if value in ("", None, "N.A.", "NA", "None", "---"):
        return None
    try:
        return float(str(value).strip())
    except Exception:
        return None


def _truth(value):
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"yes", "true", "1"}:
        return True
    return False


def _girder_value_safe(inputs: dict, base_key: str, i: int):
    """Per-girder property, or None when the key is absent."""
    try:
        return resolve_girder_value(inputs, base_key, i)
    except KeyError:
        return None


def _girder_num(inputs: dict, base_key: str, i: int):
    """Numeric per-girder property, tolerant of the legacy scalar key."""
    return _num(_girder_value_safe(inputs, base_key, i))


def _fmt_small(value: float, decimals: int = 2) -> str:
    """Format a take-off figure to ``decimals`` places.

    A figure too small to survive the rounding is switched to scientific
    notation instead of collapsing to ``0.00``; the LaTeX form keeps it inside
    its column rather than overflowing into the neighbouring one.
    """
    rounded = f"{value:.{decimals}f}"
    if value and float(rounded) == 0.0:
        mantissa, _, exponent = f"{value:.{decimals}e}".partition("e")
        return f"${mantissa} \\times 10^{{{int(exponent)}}}$"
    return rounded


def _plate_quantities(prefix: str, length_mm: float, thickness_mm: float,
                      width_mm: float, qty: int, total_vol: float) -> dict:
    """Take-off entries for a rectangular plate item (stiffeners).

    The volume column carries the plate's own dimensions only. The plate count
    belongs in the quantity column -- multiplying by it here as well made the
    volume column read as the total, contradicting the total volume column.
    """
    length_m = length_mm / 1000.0
    thickness_m = thickness_mm / 1000.0
    width_m = width_mm / 1000.0
    single_vol = length_m * thickness_m * width_m
    return {
        f"{prefix}_vol_formula": (
            f"${length_m:.3f}\\text{{ m}} \\times {thickness_m:.3f}\\text{{ m}}"
            f" \\times {width_m:.3f}\\text{{ m}} = {single_vol:.6f}\\text{{ m}}^3$"
        ),
        f"{prefix}_qty": str(qty),
        f"{prefix}_vol_total": _fmt_small(total_vol),
        f"{prefix}_wt_single": _fmt_small(single_vol * STEEL_DENSITY_T_PER_M3),
        f"{prefix}_wt_total": _fmt_small(total_vol * STEEL_DENSITY_T_PER_M3),
    }


def calculate_stiffener_quantities(inputs: dict, span: float, n_girders: int) -> dict:
    """Bearing and intermediate stiffener take-off, summed over all girders.

    Stiffener plates span the web, not the overall girder depth, so the flange
    thicknesses are deducted where the section input is available.
    """
    quantities = {}

    bearing_qty = 0
    bearing_vol = 0.0
    bearing_dims = None

    int_qty = 0
    int_vol = 0.0
    int_dims = None

    for gi in range(n_girders):
        web_depth = _girder_num(inputs, "member_properties.girder_details.section_input.web_depth", gi)
        if web_depth is None:
            depth = _girder_num(inputs, KEY_MP_GIRDER_DEPTH, gi)
            if depth is None:
                continue
            tft = _girder_num(inputs, KEY_MP_GIRDER_TOP_FLANGE_THICKNESS, gi) or 0.0
            tfb = _girder_num(inputs, KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS, gi) or 0.0
            web_depth = depth - tft - tfb
        if web_depth <= 0:
            continue

        # The same input drives plates-per-end for bearing stiffeners and the
        # one-sided/two-sided count for intermediate ones (see StiffenerConfig).
        n_plates = _girder_num(inputs, KEY_MP_STIFFENER_NO_BEARING_STIFFENERS, gi)
        bearing_t = _girder_num(inputs, KEY_MP_STIFFENER_BEARING_THICKNESS, gi)
        bearing_w = _girder_num(inputs, KEY_MP_STIFFENER_BEARING_OUTSTAND, gi)

        if n_plates and bearing_t and bearing_w:
            qty = int(n_plates) * 2  # two ends per girder
            bearing_qty += qty
            bearing_vol += qty * web_depth * bearing_t * bearing_w / 1e9
            if bearing_dims is None:
                bearing_dims = (web_depth, bearing_t, bearing_w)

        if _truth(_girder_value_safe(inputs, KEY_MP_STIFFENER_INTERMEDIATE, gi)):
            spacing = _girder_num(inputs, KEY_MP_STIFFENER_INTERMEDIATE_SPACING, gi)
            int_t = _girder_num(inputs, KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS, gi)
            int_w = _girder_num(inputs, KEY_MP_STIFFENER_INTERMEDIATE_OUTSTAND, gi)
            if spacing and int_t and int_w and spacing > 0:
                n_locations = max(0, int((span * 1000.0) / spacing) - 1)
                qty = n_locations * int(n_plates or 1)
                int_qty += qty
                int_vol += qty * web_depth * int_t * int_w / 1e9
                if int_dims is None:
                    int_dims = (web_depth, int_t, int_w)

    if bearing_qty and bearing_dims:
        quantities.update(_plate_quantities("stiffener_bearing", *bearing_dims,
                                            bearing_qty, bearing_vol))
    if int_qty and int_dims:
        quantities.update(_plate_quantities("stiffener_int", *int_dims,
                                            int_qty, int_vol))
    return quantities


def calculate_connection_quantities(girder_vol: float, girder_wt: float) -> dict:
    """Connection steel, taken as a fixed percentage of the girder steel."""
    if girder_vol <= 0.0 or girder_wt <= 0.0:
        return {}
    conn_vol = girder_vol * CONNECTION_ALLOWANCE
    conn_wt = girder_wt * CONNECTION_ALLOWANCE
    pct = f"{CONNECTION_ALLOWANCE * 100:g}"
    return {
        "connections_vol_formula": (
            f"${pct}\\% \\times {girder_vol:.5f}\\text{{ m}}^3"
            f" = {conn_vol:.5f}\\text{{ m}}^3$"
        ),
        "connections_qty": "1",
        "connections_vol_total": _fmt_small(conn_vol),
        "connections_wt_single": _fmt_small(conn_wt),
        "connections_wt_total": _fmt_small(conn_wt),
    }


def calculate_material_quantities(inputs: dict, outputs: dict) -> dict:
    """Calculate quantities (steel tonnage, concrete volume, rebar, studs)
    needed for the material take-off summary (Chapter 7).
    """
    quantities = {
        "steel_girders_vol_formula": r"\placeholder{Area $\times$ Length}",
        "steel_girders_qty": "N.A.",
        "steel_girders_vol_total": "N.A.",
        "steel_girders_wt_single": "N.A.",
        "steel_girders_wt_total": "N.A.",
        
        "steel_bracing_vol_formula": r"\placeholder{Area $\times$ Length}",
        "steel_bracing_qty": "N.A.",
        "steel_bracing_vol_total": "N.A.",
        "steel_bracing_wt_single": "N.A.",
        "steel_bracing_wt_total": "N.A.",

        "bracing_top_vol_formula": r"\placeholder{Area $\times$ Length}",
        "bracing_top_qty": "N.A.",
        "bracing_top_vol_total": "N.A.",
        "bracing_top_wt_single": "N.A.",
        "bracing_top_wt_total": "N.A.",

        "bracing_bot_vol_formula": r"\placeholder{Area $\times$ Length}",
        "bracing_bot_qty": "N.A.",
        "bracing_bot_vol_total": "N.A.",
        "bracing_bot_wt_single": "N.A.",
        "bracing_bot_wt_total": "N.A.",

        "bracing_diag_vol_formula": r"\placeholder{Area $\times$ Length}",
        "bracing_diag_qty": "N.A.",
        "bracing_diag_vol_total": "N.A.",
        "bracing_diag_wt_single": "N.A.",
        "bracing_diag_wt_total": "N.A.",
        
        "concrete_deck_vol_formula": r"\placeholder{Width $\times$ Thickness $\times$ Length}",
        "concrete_deck_qty": "N.A.",
        "concrete_deck_vol_total": "N.A.",
        "concrete_deck_wt_single": "N.A.",
        "concrete_deck_wt_total": "N.A.",
        
        "rebar_deck_vol_formula": r"\placeholder{Area $\times$ Length}",
        "rebar_deck_qty": "N.A.",
        "rebar_deck_vol_total": "N.A.",
        "rebar_deck_wt_single": "N.A.",
        "rebar_deck_wt_total": "N.A.",
        
        "stiffener_bearing_vol_formula": "N.A.",
        "stiffener_bearing_qty": "N.A.",
        "stiffener_bearing_vol_total": "N.A.",
        "stiffener_bearing_wt_single": "N.A.",
        "stiffener_bearing_wt_total": "N.A.",

        "stiffener_int_vol_formula": "N.A.",
        "stiffener_int_qty": "N.A.",
        "stiffener_int_vol_total": "N.A.",
        "stiffener_int_wt_single": "N.A.",
        "stiffener_int_wt_total": "N.A.",

        "connections_vol_formula": "N.A.",
        "connections_qty": "N.A.",
        "connections_vol_total": "N.A.",
        "connections_wt_single": "N.A.",
        "connections_wt_total": "N.A.",

        "shear_studs_vol_formula": r"\placeholder{Area $\times$ Height}",
        "shear_studs_qty": "N.A.",
        "shear_studs_vol_total": "N.A.",
        "shear_studs_wt_single": "N.A.",
        "shear_studs_wt_total": "N.A.",

        "crash_barrier_vol_formula": r"\placeholder{Area $\times$ Length}",
        "crash_barrier_qty": "N.A.",
        "crash_barrier_vol_total": "N.A.",
        "crash_barrier_wt_single": "N.A.",
        "crash_barrier_wt_total": "N.A.",
    }
    try:
        span_val = inputs.get(KEY_SPAN)
        n_girders_val = inputs.get(KEY_TS_NO_OF_GIRDERS)
        if span_val is None or n_girders_val is None:
            return quantities
            
        try:
            span = float(span_val)
            n_girders = int(n_girders_val)
        except Exception:
            return quantities

        if span <= 0 or n_girders <= 0:
            return quantities

        # 1. Concrete deck volume (Cu.m) and Weight (t)
        overall_width_val = inputs.get("typical_section.overall_bridge_width")
        deck_thickness_val = inputs.get(KEY_TS_DECK_THICKNESS)
        
        if overall_width_val is not None and deck_thickness_val is not None:
            try:
                overall_width = float(overall_width_val)
                deck_thickness = float(deck_thickness_val) / 1000.0  # mm to m
                if overall_width > 0 and deck_thickness > 0:
                    concrete_vol = span * overall_width * deck_thickness
                    quantities["concrete_deck_vol_formula"] = f"${overall_width:.2f}\\text{{ m}} \\times {deck_thickness:.2f}\\text{{ m}} \\times {span:.2f}\\text{{ m}} = {concrete_vol:.2f}\\text{{ m}}^3$"
                    quantities["concrete_deck_qty"] = "1"
                    quantities["concrete_deck_vol_total"] = _fmt_small(concrete_vol)
                    quantities["concrete_deck_wt_single"] = _fmt_small((concrete_vol * 2.5))
                    quantities["concrete_deck_wt_total"] = _fmt_small((concrete_vol * 2.5))

                    # 2. Reinforcement Steel (Cu.m) and Weight (t)
                    rebar_wt_kg = concrete_vol * 120.0
                    rebar_vol = rebar_wt_kg / 7850.0
                    rebar_area = rebar_vol / span if span > 0 else 0.0
                    quantities["rebar_deck_vol_formula"] = f"${rebar_area:.6f}\\text{{ m}}^2 \\times {span:.2f}\\text{{ m}} = {rebar_vol:.5f}\\text{{ m}}^3$"
                    quantities["rebar_deck_qty"] = "1"
                    quantities["rebar_deck_vol_total"] = _fmt_small(rebar_vol)
                    
                    rebar_wt_mt = rebar_wt_kg / 1000.0
                    quantities["rebar_deck_wt_single"] = _fmt_small(rebar_wt_mt)
                    quantities["rebar_deck_wt_total"] = _fmt_small(rebar_wt_mt)
            except Exception:
                pass

        # 3. Steel Girders (Cu.m) and Weight (t)
        girder_area = 0.0
        try:
            # Resolve representative girder sectional area
            girder_area = float(resolve_girder_value(inputs, "member_properties.girder_details.section_properties.area", 0))
        except Exception:
            pass

        # Calculate from inputs if not in properties
        if girder_area <= 0:
            try:
                dw_val = resolve_girder_value(inputs, "member_properties.girder_details.section_input.web_depth", 0)
                tw_val = resolve_girder_value(inputs, "member_properties.girder_details.section_input.web_thickness", 0)
                bft_val = resolve_girder_value(inputs, "member_properties.girder_details.section_input.top_flange_width", 0)
                tft_val = resolve_girder_value(inputs, "member_properties.girder_details.section_input.top_flange_thickness", 0)
                bfb_val = resolve_girder_value(inputs, "member_properties.girder_details.section_input.bottom_flange_width", 0)
                tfb_val = resolve_girder_value(inputs, "member_properties.girder_details.section_input.bottom_flange_thickness", 0)
                
                if (dw_val is not None and tw_val is not None and 
                    bft_val is not None and tft_val is not None and 
                    bfb_val is not None and tfb_val is not None):
                    
                    dw = float(dw_val)
                    tw = float(tw_val)
                    bft = float(bft_val)
                    tft = float(tft_val)
                    bfb = float(bfb_val)
                    tfb = float(tfb_val)
                    
                    # All dimensions in mm, compute in m²
                    girder_area = ((dw * tw) + (bft * tft) + (bfb * tfb)) / 1e6
            except Exception:
                pass

        total_girder_mass = 0.0
        if girder_area > 0:
            girder_vol = girder_area * span
            quantities["steel_girders_vol_formula"] = f"${girder_area:.5f}\\text{{ m}}^2 \\times {span:.2f}\\text{{ m}} = {girder_vol:.5f}\\text{{ m}}^3$"
            quantities["steel_girders_qty"] = str(n_girders)
            
            # calculate tonnage / volume
            for gi in range(n_girders):
                try:
                    mass_per_m = float(resolve_girder_value(inputs, "member_properties.girder_details.section_properties.mass", gi))
                    total_girder_mass += mass_per_m * span
                except Exception:
                    total_girder_mass += girder_area * span * 7850.0
            
            girder_total_vol = n_girders * girder_vol
            quantities["steel_girders_vol_total"] = _fmt_small(girder_total_vol)
            
            single_girder_wt = (total_girder_mass / n_girders) / 1000.0
            total_girder_wt = total_girder_mass / 1000.0
            quantities["steel_girders_wt_single"] = _fmt_small(single_girder_wt)
            quantities["steel_girders_wt_total"] = _fmt_small(total_girder_wt)

            # Connections are an allowance on the girder steel they join.
            quantities.update(calculate_connection_quantities(girder_total_vol, total_girder_wt))

        # 3a. Bearing and intermediate stiffeners
        quantities.update(calculate_stiffener_quantities(inputs, span, n_girders))

        # 4. Shear Stud Connectors (Cu.m) and Weight (t)
        spacing_mm = 0.0
        studs_per_sec = 0
        stud_d = 0.0
        stud_h_mm = 0.0

        spacing_val = outputs.get("steeldesign.details.shear.longitudinal_spacing")
        studs_val = outputs.get("steeldesign.details.shear.studs_per_section")
        stud_d_val = outputs.get("steeldesign.details.shear.diameter") or inputs.get("design_options.shear_studs.diameter")
        stud_h_val = outputs.get("steeldesign.details.shear.height") or inputs.get("design_options.shear_studs.height")

        if spacing_val is not None and studs_val is not None and stud_d_val is not None and stud_h_val is not None:
            try:
                spacing_mm = float(spacing_val)
                studs_per_sec = int(studs_val)
                stud_d = float(stud_d_val)
                stud_h_mm = float(stud_h_val)
            except Exception:
                pass

        if spacing_mm > 0.0 and studs_per_sec > 0 and stud_d > 0.0 and stud_h_mm > 0.0:
            stud_h = stud_h_mm / 1000.0  # mm to m
            n_sections = int(span * 1000.0 / spacing_mm) + 1
            total_studs = n_girders * studs_per_sec * n_sections
            
            stud_area = (3.14159 * (stud_d / 1000.0) ** 2) / 4.0
            stud_vol = stud_area * stud_h
            quantities["shear_studs_vol_formula"] = f"${stud_area:.6f}\\text{{ m}}^2 \\times {stud_h:.3f}\\text{{ m}} = {stud_vol:.6f}\\text{{ m}}^3$"
            quantities["shear_studs_qty"] = str(total_studs)
            
            studs_total_vol = total_studs * stud_vol
            quantities["shear_studs_vol_total"] = _fmt_small(studs_total_vol)
            
            # density of steel = 7850 kg/m^3 = 7.85 tonnes/m^3
            single_stud_wt = stud_vol * 7.85
            total_studs_wt = studs_total_vol * 7.85
            quantities["shear_studs_wt_single"] = _fmt_small(single_stud_wt)
            quantities["shear_studs_wt_total"] = _fmt_small(total_studs_wt)
        else:
            quantities["shear_studs_vol_formula"] = "N.A."
            quantities["shear_studs_qty"] = "N.A."
            quantities["shear_studs_vol_total"] = "N.A."
            quantities["shear_studs_wt_single"] = "N.A."
            quantities["shear_studs_wt_total"] = "N.A."

        # 5. Steel Bracings (Cu.m) and Weight (t)
        # Find bracing section properties from outputs or skip if not present
        bracing_area = 0.0
        bracing_len = 0.0
        top_chord_enabled = True
        bot_chord_enabled = True

        bracing_area_val = outputs.get("transverse_member_design.cb.section_properties.bracing.G1G2.A")
        cb_forces = outputs.get("crossbracing_forces_dict")
        bracing_len_val = None
        if cb_forces:
            cb_geom = cb_forces.get("geometry")
            if cb_geom:
                bracing_len_val = cb_geom.get("diagonal_length_m")

        if bracing_area_val is not None and bracing_len_val is not None:
            try:
                bracing_area = float(bracing_area_val) / 10000.0  # Convert cm² to m²
                bracing_len = float(bracing_len_val)
            except Exception:
                pass

        spacing_val = inputs.get(KEY_TS_GIRDER_SPACING)
        spacing = 0.0
        if spacing_val is not None:
            try:
                spacing = float(spacing_val)
            except Exception:
                pass

        # Only perform calculations if bracing is designed (area and length are positive)
        if bracing_area > 0.0 and bracing_len > 0.0 and spacing > 0.0:
            cb_forces = outputs.get("crossbracing_forces_dict", {}) or {}
            cb_geom = cb_forces.get("geometry", {}) or {}
            cb_spacing_val = cb_geom.get("cb_spacing_m")
            cb_spacing = 0.0
            if cb_spacing_val is not None:
                try:
                    cb_spacing = float(cb_spacing_val)
                except Exception:
                    pass
                    
            if cb_spacing > 0.0:
                n_panels = max(1, round(span / cb_spacing) - 1)
            else:
                n_panels = max(3, int(span / 5.0))

            # 5a. Top Chord
            top_chord_qty = (n_girders - 1) * n_panels if top_chord_enabled else 0
            top_chord_vol_single = bracing_area * spacing
            top_chord_vol_total = top_chord_qty * top_chord_vol_single
            top_chord_wt_single = top_chord_vol_single * 7.85
            top_chord_wt_total = top_chord_vol_total * 7.85
            
            quantities["bracing_top_vol_formula"] = f"${bracing_area:.5f}\\text{{ m}}^2 \\times {spacing:.2f}\\text{{ m}} = {top_chord_vol_single:.5f}\\text{{ m}}^3$"
            quantities["bracing_top_qty"] = str(top_chord_qty)
            quantities["bracing_top_vol_total"] = _fmt_small(top_chord_vol_total) if top_chord_enabled else "0.00"
            quantities["bracing_top_wt_single"] = _fmt_small(top_chord_wt_single)
            quantities["bracing_top_wt_total"] = _fmt_small(top_chord_wt_total) if top_chord_enabled else "0.00"

            # 5b. Bottom Chord
            bot_chord_qty = (n_girders - 1) * n_panels if bot_chord_enabled else 0
            bot_chord_vol_single = bracing_area * spacing
            bot_chord_vol_total = bot_chord_qty * bot_chord_vol_single
            bot_chord_wt_single = bot_chord_vol_single * 7.85
            bot_chord_wt_total = bot_chord_vol_total * 7.85
            
            quantities["bracing_bot_vol_formula"] = f"${bracing_area:.5f}\\text{{ m}}^2 \\times {spacing:.2f}\\text{{ m}} = {bot_chord_vol_single:.5f}\\text{{ m}}^3$"
            quantities["bracing_bot_qty"] = str(bot_chord_qty)
            quantities["bracing_bot_vol_total"] = _fmt_small(bot_chord_vol_total) if bot_chord_enabled else "0.00"
            quantities["bracing_bot_wt_single"] = _fmt_small(bot_chord_wt_single)
            quantities["bracing_bot_wt_total"] = _fmt_small(bot_chord_wt_total) if bot_chord_enabled else "0.00"

            # 5c. Diagonal
            diags_qty = (n_girders - 1) * n_panels * 2
            diag_vol_single = bracing_area * bracing_len
            diag_vol_total = diags_qty * diag_vol_single
            diag_wt_single = diag_vol_single * 7.85
            diag_wt_total = diag_vol_total * 7.85
            
            quantities["bracing_diag_vol_formula"] = f"${bracing_area:.5f}\\text{{ m}}^2 \\times {bracing_len:.2f}\\text{{ m}} = {diag_vol_single:.5f}\\text{{ m}}^3$"
            quantities["bracing_diag_qty"] = str(diags_qty)
            quantities["bracing_diag_vol_total"] = _fmt_small(diag_vol_total)
            quantities["bracing_diag_wt_single"] = _fmt_small(diag_wt_single)
            quantities["bracing_diag_wt_total"] = _fmt_small(diag_wt_total)
        else:
            # Keep all bracing volumes, quantities, and weights as default placeholder "N.A."
            for prefix in ("bracing_top", "bracing_bot", "bracing_diag"):
                quantities[f"{prefix}_vol_formula"] = "N.A."
                quantities[f"{prefix}_qty"] = "N.A."
                quantities[f"{prefix}_vol_total"] = "N.A."
                quantities[f"{prefix}_wt_single"] = "N.A."
                quantities[f"{prefix}_wt_total"] = "N.A."

        # 6. Crash Barrier (Cu.m) and Weight (t)
        # Density is entered in kN/m³ (RCC default 25); convert to T/m³ for the take-off.
        cb_density_kn = 0.0
        try:
            cb_density_kn = float(inputs.get(KEY_CB_DENSITY))
        except Exception:
            cb_density_kn = 0.0
        if cb_density_kn <= 0.0:
            cb_density_kn = RCC_DENSITY
        cb_density_t = cb_density_kn / 9.81

        # The barrier area reaches us in either unit: defaults.py seeds it in
        # mm², while compute_crash_barrier_values() writes m². Normalise here
        # rather than at the source, since the UI reads the defaults as-is.
        # A barrier cross-section is well under 10 m², so a larger value is mm².
        cb_area = 0.0
        cb_area_val = inputs.get(KEY_CB_AREA)
        if cb_area_val is not None:
            try:
                cb_area = float(cb_area_val)
            except Exception:
                cb_area = 0.0
            if cb_area > 10.0:
                cb_area /= 1e6

        # Metallic barriers carry no area input; recover it from the udl,
        # since that load is itself derived as area x density.
        if cb_area <= 0.0:
            try:
                cb_load = float(inputs.get(KEY_CB_LOAD))
                if cb_load > 0.0:
                    cb_area = cb_load / cb_density_kn
            except Exception:
                pass

        if cb_area > 0.0:
            cb_vol = cb_area * span
            quantities["crash_barrier_vol_formula"] = f"${cb_area:.5f}\\text{{ m}}^2 \\times {span:.2f}\\text{{ m}} = {cb_vol:.5f}\\text{{ m}}^3$"
            quantities["crash_barrier_qty"] = "2"

            cb_total_vol = 2 * cb_vol
            quantities["crash_barrier_vol_total"] = _fmt_small(cb_total_vol)

            single_cb_wt = cb_vol * cb_density_t
            total_cb_wt = cb_total_vol * cb_density_t
            quantities["crash_barrier_wt_single"] = _fmt_small(single_cb_wt)
            quantities["crash_barrier_wt_total"] = _fmt_small(total_cb_wt)
        else:
            quantities["crash_barrier_vol_formula"] = "N.A."
            quantities["crash_barrier_qty"] = "N.A."
            quantities["crash_barrier_vol_total"] = "N.A."
            quantities["crash_barrier_wt_single"] = "N.A."
            quantities["crash_barrier_wt_total"] = "N.A."

    except Exception as exc:
        logger.warning(f"Error calculating material quantities: {exc}")

    return quantities
