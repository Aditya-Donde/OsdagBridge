# app/models/bridge.py

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class BridgeInput(BaseModel):
    # ── Basic inputs (from main dashboard) ──────────────────────────────────
    span_length:        Optional[float] = 35000   # mm
    width:              Optional[float] = 12000   # mm  (overall bridge width)
    num_girders:        Optional[int]   = 4
    skew_angle:         Optional[float] = 0

    # Legacy field names (keep for compatibility)
    span:               Optional[float] = None
    carriageway_width:  Optional[float] = None

    # ── Additional inputs (from modal) ──────────────────────────────────────
    girder_spacing:       Optional[float] = 2750   # mm
    no_of_girders:        Optional[int]   = 4
    deck_overhang_width:  Optional[float] = 1000   # mm
    overall_bridge_width: Optional[float] = None   # mm — overrides width if set
    deck_thickness:       Optional[float] = 200    # mm
    footpath_thickness:   Optional[float] = 200    # mm
    footpath_width:       Optional[float] = 1500   # mm
    footpath_config:      Optional[str]   = "none"
    member_properties:    Optional[dict]  = None

    # ── Crash barrier / railing / median ───────────────────────────────────
    crash_barrier_width:  Optional[float] = 500    # mm
    crash_barrier_type:   Optional[str]   = None
    railing_type:         Optional[str]   = None
    railing_width:        Optional[float] = 375    # mm
    railing_height:       Optional[float] = 1000   # mm
    median_present:       Optional[bool]  = False
    median_width:         Optional[float] = 1200   # mm
    median_type:          Optional[str]   = None

    # ── Wearing course ──────────────────────────────────────────────────────
    wearing_course_thickness: Optional[float] = 50  # mm

    # ── Loading ────────────────────────────────────────────────────────────
    self_weight_factor:   Optional[float] = 1.0
    live_load_vehicles:   Optional[Dict[str, Any]] = None
    seismic_zone:         Optional[str]   = None
    importance_factor:    Optional[float] = 1.0
    soil_type:            Optional[str]   = None
    time_period:          Optional[float] = None
    damping_percentage:   Optional[float] = 2.0
    response_factor:      Optional[int]   = 1
    custom_loads:         Optional[List[Any]] = None
    load_combinations:    Optional[Dict[str, Any]] = None

    # ── Support Conditions ──────────────────────────────────────────────────
    left_support:         Optional[str]   = "Pinned"
    right_support:        Optional[str]   = "Roller"
    bearing_length:       Optional[float] = 400.0  # mm

    # ── Design Options ──────────────────────────────────────────────────────
    construction_stage:             Optional[str]   = "Yes"
    reinforcement_material:         Optional[str]   = "Fe 500"
    top_clear_cover:                Optional[float] = 50.0    # mm
    bottom_clear_cover:             Optional[float] = 40.0    # mm
    side_clear_cover:               Optional[float] = 40.0    # mm
    shear_stud_yield_strength:      Optional[float] = 385.0   # MPa
    shear_stud_ultimate_strength:   Optional[float] = 495.0   # MPa
    shear_stud_diameter:            Optional[float] = 20.0    # mm
    shear_stud_height:              Optional[float] = 100.0   # mm
    shear_stud_count:               Optional[int]   = 2
    shear_stud_transverse_spacing:  Optional[float] = 100.0   # mm

    # ── Design Options (Cont.) ──────────────────────────────────────────────
    gamma_c_basic:                  Optional[float] = 1.50
    gamma_c_accidental:             Optional[float] = 1.20
    gamma_m0:                       Optional[float] = 1.10
    gamma_m1:                       Optional[float] = 1.25
    gamma_s:                        Optional[float] = 1.15
    gamma_v:                        Optional[float] = 1.25
    gamma_flt:                      Optional[float] = 1.00
    gamma_mf:                       Optional[float] = 1.35
    load_cycles:                    Optional[float] = 2000000.0
    deflection_limit:               Optional[float] = 600.0
    ultimate_limit_states:          Optional[Dict[str, Any]] = None
    serviceability_limit_states:    Optional[Dict[str, Any]] = None