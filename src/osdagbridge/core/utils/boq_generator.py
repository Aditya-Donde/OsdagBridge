# =============================================================================
# OsdagBridge — BOQ (Bill of Quantities) Generator
# =============================================================================

import logging
import math
from typing import Any

from osdagbridge.core.utils.common import (
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


def calculate_material_quantities(inputs: dict, outputs: dict) -> dict:
    """Calculate quantities (steel tonnage, concrete volume, rebar, studs)
    needed for the material take-off summary (Chapter 7).
    """
    quantities = {
        "steel_girders_vol_formula": r"\placeholder{Area $\times$ Length}",
        "steel_girders_qty": "---",
        "steel_girders_vol_total": "---",
        "steel_girders_wt_single": "---",
        "steel_girders_wt_total": "---",
        
        "steel_bracing_vol_formula": r"\placeholder{Area $\times$ Length}",
        "steel_bracing_qty": "---",
        "steel_bracing_vol_total": "---",
        "steel_bracing_wt_single": "---",
        "steel_bracing_wt_total": "---",

        "bracing_top_vol_formula": r"\placeholder{Area $\times$ Length}",
        "bracing_top_qty": "---",
        "bracing_top_vol_total": "---",
        "bracing_top_wt_single": "---",
        "bracing_top_wt_total": "---",

        "bracing_bot_vol_formula": r"\placeholder{Area $\times$ Length}",
        "bracing_bot_qty": "---",
        "bracing_bot_vol_total": "---",
        "bracing_bot_wt_single": "---",
        "bracing_bot_wt_total": "---",

        "bracing_diag_vol_formula": r"\placeholder{Area $\times$ Length}",
        "bracing_diag_qty": "---",
        "bracing_diag_vol_total": "---",
        "bracing_diag_wt_single": "---",
        "bracing_diag_wt_total": "---",
        
        "concrete_deck_vol_formula": r"\placeholder{Width $\times$ Thickness $\times$ Length}",
        "concrete_deck_qty": "---",
        "concrete_deck_vol_total": "---",
        "concrete_deck_wt_single": "---",
        "concrete_deck_wt_total": "---",
        
        "rebar_deck_vol_formula": r"\placeholder{Area $\times$ Length}",
        "rebar_deck_qty": "---",
        "rebar_deck_vol_total": "---",
        "rebar_deck_wt_single": "---",
        "rebar_deck_wt_total": "---",
        
        "shear_studs_vol_formula": r"\placeholder{Area $\times$ Height}",
        "shear_studs_qty": "---",
        "shear_studs_vol_total": "---",
        "shear_studs_wt_single": "---",
        "shear_studs_wt_total": "---",

        "crash_barrier_vol_formula": r"\placeholder{Area $\times$ Length}",
        "crash_barrier_qty": "---",
        "crash_barrier_vol_total": "---",
        "crash_barrier_wt_single": "---",
        "crash_barrier_wt_total": "---",
    }
    try:
        span = float(inputs.get(KEY_SPAN, 0.0) or 0.0)
        n_girders = int(inputs.get(KEY_TS_NO_OF_GIRDERS, 0) or 0)
        if span <= 0 or n_girders <= 0:
            return quantities

        # 1. Concrete deck volume (Cu.m) and Weight (MT)
        overall_width = float(inputs.get("typical_section.overall_bridge_width", 0.0) or 0.0)
        deck_thickness = float(inputs.get(KEY_TS_DECK_THICKNESS, 0.0) or 0.0) / 1000.0  # mm to m
        
        concrete_vol = 0.0
        if overall_width > 0 and deck_thickness > 0:
            concrete_vol = span * overall_width * deck_thickness
            quantities["concrete_deck_vol_formula"] = f"${overall_width:.2f}\\text{{ m}} \\times {deck_thickness:.2f}\\text{{ m}} \\times {span:.2f}\\text{{ m}} = {concrete_vol:.2f}\\text{{ m}}^3$"
            quantities["concrete_deck_qty"] = "1"
            quantities["concrete_deck_vol_total"] = f"{concrete_vol:.2f}"
            quantities["concrete_deck_wt_single"] = f"{(concrete_vol * 2.5):.2f}"
            quantities["concrete_deck_wt_total"] = f"{(concrete_vol * 2.5):.2f}"

            # 2. Reinforcement Steel (Cu.m) and Weight (MT)
            rebar_wt_kg = concrete_vol * 120.0
            rebar_vol = rebar_wt_kg / 7850.0
            rebar_area = rebar_vol / span if span > 0 else 0.0
            quantities["rebar_deck_vol_formula"] = f"${rebar_area:.6f}\\text{{ m}}^2 \\times {span:.2f}\\text{{ m}} = {rebar_vol:.5f}\\text{{ m}}^3$"
            quantities["rebar_deck_qty"] = "1"
            quantities["rebar_deck_vol_total"] = f"{rebar_vol:.2f}"
            
            rebar_wt_mt = rebar_wt_kg / 1000.0
            quantities["rebar_deck_wt_single"] = f"{rebar_wt_mt:.2f}"
            quantities["rebar_deck_wt_total"] = f"{rebar_wt_mt:.2f}"

        # 3. Steel Girders (Cu.m) and Weight (MT)
        girder_area = 0.0
        try:
            # Resolve representative girder sectional area
            girder_area = float(resolve_girder_value(inputs, "member_properties.girder_details.section_properties.area", 0))
        except Exception:
            pass

        # Calculate from inputs if not in properties
        if girder_area <= 0:
            try:
                dw = float(resolve_girder_value(inputs, "member_properties.girder_details.section_input.web_depth", 0) or 0.0)
                tw = float(resolve_girder_value(inputs, "member_properties.girder_details.section_input.web_thickness", 0) or 0.0)
                bft = float(resolve_girder_value(inputs, "member_properties.girder_details.section_input.top_flange_width", 0) or 0.0)
                tft = float(resolve_girder_value(inputs, "member_properties.girder_details.section_input.top_flange_thickness", 0) or 0.0)
                bfb = float(resolve_girder_value(inputs, "member_properties.girder_details.section_input.bottom_flange_width", 0) or 0.0)
                tfb = float(resolve_girder_value(inputs, "member_properties.girder_details.section_input.bottom_flange_thickness", 0) or 0.0)
                
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
            quantities["steel_girders_vol_total"] = f"{girder_total_vol:.2f}"
            
            single_girder_wt = (total_girder_mass / n_girders) / 1000.0
            total_girder_wt = total_girder_mass / 1000.0
            quantities["steel_girders_wt_single"] = f"{single_girder_wt:.2f}"
            quantities["steel_girders_wt_total"] = f"{total_girder_wt:.2f}"

        # 4. Shear Stud Connectors (Cu.m) and Weight (MT)
        spacing_mm = float(outputs.get("shear_connectors.stud_spacing_provided_mm", 300.0) or 300.0)
        studs_per_sec = int(inputs.get("shear_connectors.studs_per_section", 2) or 2)
        n_sections = int(span * 1000.0 / spacing_mm) + 1
        total_studs = n_girders * studs_per_sec * n_sections
        
        stud_d = float(inputs.get("shear_connectors.stud_diameter", 22.0) or 22.0)
        stud_h = float(inputs.get("shear_connectors.stud_height", 150.0) or 150.0) / 1000.0  # mm to m
        stud_area = (3.14159 * (stud_d / 1000.0) ** 2) / 4.0

        stud_vol = stud_area * stud_h
        quantities["shear_studs_vol_formula"] = f"${stud_area:.6f}\\text{{ m}}^2 \\times {stud_h:.3f}\\text{{ m}} = {stud_vol:.6f}\\text{{ m}}^3$"
        quantities["shear_studs_qty"] = str(total_studs)
        
        studs_total_vol = total_studs * stud_vol
        quantities["shear_studs_vol_total"] = f"{studs_total_vol:.2f}"
        
        # density of steel = 7850 kg/m^3 = 7.85 tonnes/m^3
        single_stud_wt = stud_vol * 7.85
        total_studs_wt = studs_total_vol * 7.85
        quantities["shear_studs_wt_single"] = f"{single_stud_wt:.6f}"
        quantities["shear_studs_wt_total"] = f"{total_studs_wt:.3f}"

        # 5. Steel Bracings (Cu.m) and Weight (MT)
        # Find bracing section properties from G1G2 or input defaults
        bracing_area = 0.0
        bracing_len = 0.0
        top_chord_enabled = True
        bot_chord_enabled = True

        try:
            bracing_area = float(outputs.get("transverse_member_design.section_properties.bracing.G1G2.A") or 0.0)
            bracing_len = float(outputs.get("transverse_member_design.section_properties.bracing.G1G2.length") or 0.0)
            top_chord_enabled = outputs.get("member_properties.cross_bracing_details.top_chord", True)
            bot_chord_enabled = outputs.get("member_properties.cross_bracing_details.bottom_chord", True)
        except Exception:
            pass

        # Fallbacks
        spacing = float(inputs.get(KEY_TS_GIRDER_SPACING, 2.5) or 2.5)
        try:
            dw_m = float(resolve_girder_value(inputs, "member_properties.girder_details.section_input.web_depth", 0) or 1000.0) / 1000.0
        except Exception:
            dw_m = 1.0
        
        if bracing_len <= 0:
            bracing_len = math.sqrt(spacing**2 + dw_m**2)

        if bracing_area <= 0:
            bracing_area = 0.001539  # Default ISA 100x100x8

        n_panels = max(3, int(span / 5.0))
        
        # 5a. Top Chord
        top_chord_qty = (n_girders - 1) * n_panels if top_chord_enabled else 0
        top_chord_vol_single = bracing_area * spacing
        top_chord_vol_total = top_chord_qty * top_chord_vol_single
        top_chord_wt_single = top_chord_vol_single * 7.85
        top_chord_wt_total = top_chord_vol_total * 7.85
        
        quantities["bracing_top_vol_formula"] = f"${bracing_area:.5f}\\text{{ m}}^2 \\times {spacing:.2f}\\text{{ m}} = {top_chord_vol_single:.5f}\\text{{ m}}^3$"
        quantities["bracing_top_qty"] = str(top_chord_qty)
        quantities["bracing_top_vol_total"] = f"{top_chord_vol_total:.2f}" if top_chord_enabled else "0.00"
        quantities["bracing_top_wt_single"] = f"{top_chord_wt_single:.4f}"
        quantities["bracing_top_wt_total"] = f"{top_chord_wt_total:.2f}" if top_chord_enabled else "0.00"

        # 5b. Bottom Chord
        bot_chord_qty = (n_girders - 1) * n_panels if bot_chord_enabled else 0
        bot_chord_vol_single = bracing_area * spacing
        bot_chord_vol_total = bot_chord_qty * bot_chord_vol_single
        bot_chord_wt_single = bot_chord_vol_single * 7.85
        bot_chord_wt_total = bot_chord_vol_total * 7.85
        
        quantities["bracing_bot_vol_formula"] = f"${bracing_area:.5f}\\text{{ m}}^2 \\times {spacing:.2f}\\text{{ m}} = {bot_chord_vol_single:.5f}\\text{{ m}}^3$"
        quantities["bracing_bot_qty"] = str(bot_chord_qty)
        quantities["bracing_bot_vol_total"] = f"{bot_chord_vol_total:.2f}" if bot_chord_enabled else "0.00"
        quantities["bracing_bot_wt_single"] = f"{bot_chord_wt_single:.4f}"
        quantities["bracing_bot_wt_total"] = f"{bot_chord_wt_total:.2f}" if bot_chord_enabled else "0.00"

        # 5c. Diagonal
        diags_qty = (n_girders - 1) * n_panels * 2
        diag_vol_single = bracing_area * bracing_len
        diag_vol_total = diags_qty * diag_vol_single
        diag_wt_single = diag_vol_single * 7.85
        diag_wt_total = diag_vol_total * 7.85
        
        quantities["bracing_diag_vol_formula"] = f"${bracing_area:.5f}\\text{{ m}}^2 \\times {bracing_len:.2f}\\text{{ m}} = {diag_vol_single:.5f}\\text{{ m}}^3$"
        quantities["bracing_diag_qty"] = str(diags_qty)
        quantities["bracing_diag_vol_total"] = f"{diag_vol_total:.2f}"
        quantities["bracing_diag_wt_single"] = f"{diag_wt_single:.4f}"
        quantities["bracing_diag_wt_total"] = f"{diag_wt_total:.2f}"

        # 6. Crash Barrier (Cu.m) and Weight (MT)
        KEY_CB_AREA = "typical_section.crash_barrier.area"
        cb_area = 0.0
        try:
            cb_area = float(inputs.get(KEY_CB_AREA, 0.0) or 0.0) / 1e6
        except Exception:
            pass
        if cb_area <= 0:
            cb_area = 0.301875  # Default area in m²
        
        cb_vol = cb_area * span
        quantities["crash_barrier_vol_formula"] = f"${cb_area:.5f}\\text{{ m}}^2 \\times {span:.2f}\\text{{ m}} = {cb_vol:.5f}\\text{{ m}}^3$"
        quantities["crash_barrier_qty"] = "2"
        
        cb_total_vol = 2 * cb_vol
        quantities["crash_barrier_vol_total"] = f"{cb_total_vol:.2f}"
        
        single_cb_wt = cb_vol * 2.5
        total_cb_wt = cb_total_vol * 2.5
        quantities["crash_barrier_wt_single"] = f"{single_cb_wt:.2f}"
        quantities["crash_barrier_wt_total"] = f"{total_cb_wt:.2f}"

    except Exception as exc:
        logger.warning(f"Error calculating material quantities: {exc}")

    return quantities
