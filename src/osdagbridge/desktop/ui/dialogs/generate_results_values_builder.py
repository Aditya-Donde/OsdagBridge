import logging
import time
from osdagbridge.core.utils.common import *

logger = logging.getLogger(__name__)

# ── Empty value sentinel ──────────────────────────────────────────────────────

EMPTY = "-"


# ── Formatting helpers ────────────────────────────────────────────────────────

def _mpa(value):
    """Convert Pa → MPa, rounded to 2 dp. Returns EMPTY on any failure."""
    try:
        return round(float(value) / 1e6, 2)
    except Exception:
        return EMPTY


def _num(value, decimals=2):
    """Round a numeric value. Returns EMPTY on any failure."""
    try:
        return round(float(value), decimals)
    except Exception:
        return EMPTY


def _mm(value, decimals=1):
    """Convert metres → mm, rounded. Returns EMPTY on any failure."""
    try:
        return round(float(value) * 1e3, decimals)
    except Exception:
        return EMPTY



def _cm(value, decimals=2):
    """Convert metres → cm. Returns EMPTY on any failure."""
    try:
        return round(float(value) * 100, decimals)
    except Exception:
        return EMPTY


def _cm2(value, decimals=2):
    """Convert m² → cm². Returns EMPTY on any failure."""
    try:
        return round(float(value) * 1e4, decimals)
    except Exception:
        return EMPTY


def _cm3(value, decimals=2):
    """Convert m³ → cm³. Returns EMPTY on any failure."""
    try:
        return round(float(value) * 1e6, decimals)
    except Exception:
        return EMPTY


def _cm4(value, decimals=2):
    """Convert m⁴ → cm⁴. Returns EMPTY on any failure."""
    try:
        return round(float(value) * 1e8, decimals)
    except Exception:
        return EMPTY


def _cm6(value, decimals=2):
    """Convert m⁶ → cm⁶. Returns EMPTY on any failure."""
    try:
        return round(float(value) * 1e12, decimals)
    except Exception:
        return EMPTY


def _val(value):
    """Return value as-is, or EMPTY if missing/blank."""
    return value if value not in (None, "", [], {}) else EMPTY


def _has(*values):
    """Return True only if every value is present (not None / blank)."""
    return all(v not in (None, "", [], {}) for v in values)


# ── Resolver registry ─────────────────────────────────────────────────────────
# Populated at the bottom of this file after all resolver functions are defined.
# Maps table schema id → callable(input_dict, bridge) → dict | None

RESOLVER_MAP: dict[str, callable] = {}


def resolve_table(table_id: str, input_dict: dict, bridge) -> dict | None:
    """
    Look up and call the resolver for table_id.
    Returns None if no resolver exists or if the resolver itself returns None
    (meaning required keys were absent).
    """
    fn = RESOLVER_MAP.get(table_id)
    return fn(input_dict, bridge) if fn else None


# ── Resolvers — Bridge Configuration ─────────────────────────────────────────

def resolve_bridge_config_summary(input_dict: dict, bridge=None) -> dict | None:
    overall_width  = input_dict.get(KEY_TS_OVERALL_WIDTH)
    span           = input_dict.get(KEY_SPAN)
    no_of_girders  = input_dict.get(KEY_TS_NO_OF_GIRDERS)
    girder_spacing = input_dict.get(KEY_TS_GIRDER_SPACING)
    deck_overhang  = input_dict.get(KEY_TS_DECK_OVERHANG)
    skew_angle     = input_dict.get(KEY_SKEW_ANGLE, 0)

    if not _has(overall_width, span, no_of_girders, girder_spacing, deck_overhang):
        return None

    return {
        "id":    "bridge_configuration_summary",
        "label": "Bridge Configuration Summary",
        "columns": [
            "Overall Width (m)",
            "Span (m)",
            "No. of Girders",
            "Girder Spacing (m)",
            "Deck Overhang (m)",
            "Skew Angle (deg)",
        ],
        "rows": [[
            _num(overall_width),
            _num(span),
            _val(no_of_girders),
            _num(girder_spacing),
            _num(deck_overhang),
            _num(skew_angle),
        ]],
    }


def resolve_material_properties_steel(input_dict: dict, bridge=None) -> dict | None:
    girder_grade   = input_dict.get(KEY_GIRDER)
    bracing_grade  = input_dict.get(KEY_CROSS_BRACING)
    diaphragm_grade = input_dict.get(KEY_END_DIAPHRAGM)

    if not _has(girder_grade):
        return None

    # Pull steel properties from bridge DB lookup if bridge is available
    try:
        steel = bridge._build_material_props().steel_prop
        fu = _mpa(steel.Fu)
        fy = _mpa(steel.Fy)
        e  = _mpa(steel.E)
        g  = _mpa(steel.E / (2 * (1 + steel.v)))
        v  = _num(steel.v)
    except Exception:
        fu = fy = e = g = v = EMPTY

    def _row(component, grade):
        return [
            component,
            _val(grade),
            fu, fy, e, g, v,
            11.7,
        ]

    return {
        "id":    "material_properties_steel",
        "label": "Material Properties - Steel",
        "columns": [
            "Component",
            "Grade",
            "Ultimate Tensile Strength, Fᵤ (MPa)",
            "Yield Strength, Fᵧ (MPa)",
            "Modulus of Elasticity, E (MPa)",
            "Modulus of Rigidity, G (MPa)",
            "Poisson's Ratio, ν",
            "Thermal Expansion Coefficient (×10⁻⁶/°C)",
        ],
        "rows": [
            _row("Girder",        girder_grade),
            _row("Cross Bracing", bracing_grade),
            _row("End Diaphragm", diaphragm_grade),
        ],
    }


def resolve_material_properties_concrete(input_dict: dict, bridge=None) -> dict | None:
    concrete_grade = input_dict.get(KEY_DECK_CONCRETE_GRADE_BASIC)

    if not _has(concrete_grade):
        return None

    try:
        mat   = bridge._build_material_props()
        cp    = mat.concrete_prop
        fck   = _num(cp.fck)
        fctm  = _num(cp.fctm)
        ecm   = _num(cp.Ecm)
        # Modular ratio: E_steel / E_concrete (both in MPa)
        steel_e_mpa   = _mpa(mat.steel_prop.E)
        modular_ratio = (
            round(float(steel_e_mpa) / float(ecm), 2)
            if isinstance(steel_e_mpa, (int, float))
            and isinstance(ecm, (int, float))
            and float(ecm) > 0
            else EMPTY
        )
    except Exception:
        fck = fctm = ecm = modular_ratio = EMPTY

    # Density and Poisson's ratio are material constants for normal concrete
    density       = 25.0   # kN/m³
    poissons_ratio = 0.20

    def _row(component):
        return [
            component,
            _val(concrete_grade),
            fck,
            fctm,
            ecm,
            modular_ratio,
            density,
            poissons_ratio,
        ]

    return {
        "id":    "material_properties_concrete",
        "label": "Material Properties - Concrete",
        "columns": [
            "Component",
            "Grade",
            "Characteristic Compressive Strength, fₖ (MPa)",
            "Mean Tensile Strength, fₜₘ (MPa)",
            "Secant Modulus of Elasticity, Eₘ (MPa)",
            "Modular Ratio",
            "Density (kN/m³)",
            "Poisson's Ratio, ν",
        ],
        "rows": [
            _row("Deck Slab"),
        ],
    }


# ── Resolvers — Member Definitions ───────────────────────────────────────────

def resolve_girder_section_properties(input_dict: dict, bridge=None) -> dict | None:
    n_girders = input_dict.get(KEY_TS_NO_OF_GIRDERS)
    if not _has(n_girders):
        return None

    try:
        n = int(n_girders)
    except Exception:
        return None

    def _gk(base_key, gi, mi):
        """Return input_dict[base_key.G{gi}.M{mi}] or None."""
        return input_dict.get(f"{base_key}.G{gi}.M{mi}")

    span = _num(input_dict.get(KEY_SPAN)) if _has(input_dict.get(KEY_SPAN)) else EMPTY

    rows = []
    for gi in range(1, n + 1):
        mi = 1
        while True:
            if _gk(KEY_MP_GIRDER_DEPTH, gi, mi) is None:
                break
            rows.append([
                f"G{gi}M{mi}",
                span,
                _val(_gk(KEY_MP_GIRDER_TYPE,                  gi, mi)),
                _val(_gk(KEY_MP_GIRDER_SYMMETRY,               gi, mi)),
                _mm (_gk(KEY_MP_GIRDER_DEPTH,                  gi, mi)),
                _mm (_gk(KEY_MP_GIRDER_TOP_FLANGE_WIDTH,       gi, mi)),
                _mm (_gk(KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,   gi, mi)),
                _mm (_gk(KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH,    gi, mi)),
                _mm (_gk(KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,gi, mi)),
                _val(_gk(KEY_MP_SUPPORT_TYPE,                  gi, mi)),
                _num(_gk(KEY_MP_SUPPORT_WIDTH,                 gi, mi)),  # stored in mm
                _mm (_gk(KEY_MP_GIRDER_WEB_THICKNESS,          gi, mi)),
                _val(_gk(KEY_MP_GIRDER_TORSIONAL_RESTRAINT,    gi, mi)),
                _val(_gk(KEY_MP_GIRDER_WARPING_RESTRAINT,      gi, mi)),
                _val(_gk(KEY_MP_GIRDER_WEB_TYPE,               gi, mi)),
                _num(_gk(KEY_MP_GIRDER_MASS,                   gi, mi)),  # kg/m, no conversion
                _cm2(_gk(KEY_MP_GIRDER_SECTIONAL_AREA,         gi, mi)),
                _cm4(_gk(KEY_MP_GIRDER_SECTIONAL_IZ,           gi, mi)),
                _cm4(_gk(KEY_MP_GIRDER_SECTIONAL_IY,           gi, mi)),
                _cm (_gk(KEY_MP_GIRDER_RADIUS_GYRATION_Z,      gi, mi)),
                _cm (_gk(KEY_MP_GIRDER_RADIUS_GYRATION_Y,      gi, mi)),
                _cm3(_gk(KEY_MP_GIRDER_ELASTIC_MODULUS_ZZ,     gi, mi)),
                _cm3(_gk(KEY_MP_GIRDER_ELASTIC_MODULUS_ZY,     gi, mi)),
                _cm3(_gk(KEY_MP_GIRDER_PLASTIC_MODULUS_ZUZ,    gi, mi)),
                _cm3(_gk(KEY_MP_GIRDER_PLASTIC_MODULUS_ZUY,    gi, mi)),
                _cm4(_gk(KEY_MP_GIRDER_TORSION_CONSTANT_IT,    gi, mi)),
                _cm6(_gk(KEY_MP_GIRDER_WARPING_CONSTANT_IW,    gi, mi)),
            ])
            mi += 1

    if not rows:
        return None

    return {
        "id":    "girder_section_properties",
        "label": "Girder Section Properties",
        "columns": [
            "Member",
            "Total Span (m)",
            "Type",
            "Symmetry",
            "Total Depth, d (mm)",
            "Width of Top Flange (mm)",
            "Top Flange Thickness (mm)",
            "Width of Bottom Flange (mm)",
            "Bottom Flange Thickness (mm)",
            "Support Type",
            "Support Width (mm)",
            "Web Thickness (mm)",
            "Torsional Restraint",
            "Warping Restraint",
            "Web Type",
            "Mass, M (kg/m)",
            "Sectional Area, a (cm²)",
            "2nd Moment of Area, Iᵤ (cm⁴)",
            "2nd Moment of Area, Iᵧ (cm⁴)",
            "Radius of Gyration, rᵤ (cm)",
            "Radius of Gyration, rᵧ (cm)",
            "Elastic Modulus, Zᵤ (cm³)",
            "Elastic Modulus, Zᵧ (cm³)",
            "Plastic Modulus, Zₚᵤ (cm³)",
            "Plastic Modulus, Zₚᵧ (cm³)",
            "Torsion Constant, Iₜ (cm⁴)",
            "Warping Constant, Iᵥᵥ (cm⁶)",
        ],
        "rows": rows,
    }


def resolve_cross_bracing_section_properties(input_dict: dict, bridge=None) -> dict | None:
    n_girders = input_dict.get(KEY_TS_NO_OF_GIRDERS)
    if not _has(n_girders):
        return None
    try:
        n = int(n_girders)
    except Exception:
        return None

    def _cbk(base_key, gi, mi):
        return input_dict.get(f"{base_key}.G{gi}G{gi + 1}.B{gi}M{mi}")

    rows = []
    for gi in range(1, n):
        mi = 1
        while True:
            if _cbk(KEY_MP_CB_TYPE, gi, mi) is None:
                break
            rows.append([
                f"G{gi}G{gi + 1}_B{gi}M{mi}",
                _val(_cbk(KEY_MP_CB_TYPE, gi, mi)),
                _val(_cbk(KEY_MP_CB_BRACING_SECTION_TYPE, gi, mi)),
                _val(_cbk(KEY_MP_CB_BRACING_SECTION_DESIGNATION, gi, mi)),
                _val(_cbk(KEY_MP_CB_TOP_CHORD, gi, mi)),
                _val(_cbk(KEY_MP_CB_TOP_CHORD_SECTION_TYPE, gi, mi)),
                _val(_cbk(KEY_MP_CB_TOP_CHORD_SECTION_DESIG, gi, mi)),
                _val(_cbk(KEY_MP_CB_BOTTOM_CHORD, gi, mi)),
                _val(_cbk(KEY_MP_CB_BOTTOM_CHORD_SECTION_TYPE, gi, mi)),
                _val(_cbk(KEY_MP_CB_BOTTOM_CHORD_SECTION_DESIG, gi, mi)),
                _num(_cbk(KEY_MP_CB_SPACING, gi, mi)),
            ])
            mi += 1

    if not rows:
        return None

    return {
        "id": "cross_bracing_section_properties",
        "label": "Cross Bracing Section Properties",
        "columns": [
            "Member",
            "Type of Bracing",
            "Bracing Section Type",
            "Bracing Section Designation",
            "Top Chord",
            "Top Chord Section Type",
            "Top Chord Section Designation",
            "Bottom Chord",
            "Bottom Chord Section Type",
            "Bottom Chord Section Designation",
            "Spacing (m)",
        ],
        "rows": rows,
    }


def resolve_end_diaphragm_section_properties(input_dict: dict, bridge=None) -> dict | None:
    """
    One row per end diaphragm member ID.
    With n girders there are (n-1) adjacent pairs. Each pair has 2 end
    diaphragms sharing the same config: E{i}M1 and E{i}M2 for pair G{i}G{i+1}.

    Key pattern (mirrors defaults.py _on_no_of_girders_changed):
        <KEY_MP_ED_*>.G{i}G{i+1}.E{i}M{member_id}

    Member ID label in table:  G1G2_E1, G1G2_E2, G2G3_E1, G2G3_E2, ...
    """
    n_girders = input_dict.get(KEY_TS_NO_OF_GIRDERS)
    if not _has(n_girders):
        return None

    try:
        n = int(n_girders)
    except Exception:
        return None

    if n < 2:
        return None

    rows = []

    for i in range(1, n):
        g_pair       = f"G{i}G{i + 1}"          # e.g. "G1G2"
        pair_label   = f"G{i}G{i + 1}"           # e.g. "G1G2" (used in Member ID)

        # ── Read config from M1 (both members share the same config) ──────
        suffix = f".{g_pair}.E{i}M1"

        ed_type      = input_dict.get(f"{KEY_MP_ED_TYPE}{suffix}")
        bracing_type = input_dict.get(f"{KEY_MP_ED_BRACING_TYPE}{suffix}")
        br_sec_type  = input_dict.get(f"{KEY_MP_ED_BRACING_SECTION}{suffix}")
        br_sec_desig = input_dict.get(f"{KEY_MP_ED_BRACING_SECTION_DESIGNATION}{suffix}")
        top_chord    = input_dict.get(f"{KEY_MP_ED_TOP_CHORD}{suffix}")
        tc_sec_type  = input_dict.get(f"{KEY_MP_ED_TOP_CHORD_SECTION_TYPE}{suffix}")
        tc_sec_desig = input_dict.get(f"{KEY_MP_ED_TOP_CHORD_SECTION_DESIG}{suffix}")
        bot_chord    = input_dict.get(f"{KEY_MP_ED_BOTTOM_CHORD}{suffix}")
        bc_sec_type  = input_dict.get(f"{KEY_MP_ED_BOTTOM_CHORD_SECTION_TYPE}{suffix}")
        bc_sec_desig = input_dict.get(f"{KEY_MP_ED_BOTTOM_CHORD_SECTION_DESIG}{suffix}")

        def _col(v):
            return _val(v) if _has(v) else EMPTY

        shared = [
            _col(ed_type),
            _col(bracing_type),
            _col(br_sec_type),
            _col(br_sec_desig),
            _col(top_chord),
            _col(tc_sec_type),
            _col(tc_sec_desig),
            _col(bot_chord),
            _col(bc_sec_type),
            _col(bc_sec_desig),
        ]

        # ── Two rows per pair — E{i}M1 and E{i}M2 share the same config ──
        rows.append([f"{pair_label}_E1"] + shared)
        rows.append([f"{pair_label}_E2"] + shared)

    return {
        "id":    "end_diaphragm_section_properties",
        "label": "End Diaphragm Section Properties",
        "columns": [
            "Member ID",
            "Type",
            "Type of Bracing",
            "Bracing Section Type",
            "Bracing Section Designation",
            "Top Chord",
            "Top Chord Section Type",
            "Top Chord Section Designation",
            "Bottom Chord",
            "Bottom Chord Section Type",
            "Bottom Chord Section Designation",
        ],
        "rows": rows,
    }


def resolve_shear_stud_properties(input_dict: dict, bridge=None) -> dict | None:
    fy                  = input_dict.get(KEY_DS_STUD_YIELD_STRENGTH)
    fu                  = input_dict.get(KEY_DS_STUD_ULTIMATE_STRENGTH)
    diameter            = input_dict.get(KEY_DS_STUD_DIAMETER)
    height              = input_dict.get(KEY_DS_STUD_HEIGHT)
    transverse_spacing  = input_dict.get(KEY_DS_STUD_TRANSVERSE_SPACING)
    count               = input_dict.get(KEY_DS_STUD_COUNT)
    avg_long_spacing    = input_dict.get(KEY_SD_SHEAR_LONGITUDINAL_SPACING)

    if not _has(diameter, height, fu, fy, count):
        return None

    return {
        "id":    "shear_stud_properties",
        "label": "Shear Connector Details",
        "columns": [
            "Material Yield Strength (MPa)",
            "Material Ultimate Strength (MPa)",
            "Diameter (mm)",
            "Height (mm)",
            "Transverse Spacing (mm)",
            "No. of Shear Studs per Section",
            "Average Longitudinal Spacing (mm)",
        ],
        "rows": [[
            _num(fy),
            _num(fu),
            _num(diameter),
            _num(height),
            _num(transverse_spacing),
            _val(count),
            _num(avg_long_spacing),
        ]],
    }


def resolve_deck_slab_properties(input_dict: dict, bridge=None) -> dict | None:
    thickness    = input_dict.get(KEY_TS_DECK_THICKNESS)
    reinf_size   = input_dict.get(KEY_DS_REINF_BOUNDS)
    reinf_mat    = input_dict.get(KEY_DS_REINF_MATERIAL)
    top_cover    = input_dict.get(KEY_DS_TOP_CLEAR_COVER)
    bot_cover    = input_dict.get(KEY_DS_BOTTOM_CLEAR_COVER)

    if not _has(thickness):
        return None

    # Format reinforcement label as "Grade @ spacing" when both are available,
    # otherwise show whichever part is present.
    def _reinf_label(size, mat):
        if _has(size) and _has(mat):
            return f"{mat} — {size}mm"
        return _val(size or mat)

    return {
        "id":    "deck_slab_properties",
        "label": "Deck Slab Properties",
        "columns": [
            "Thickness (mm)",
            "Reinforcement Material",
            "Reinforcement Size (mm)",
            "Top Cover (mm)",
            "Bottom Cover (mm)",
        ],
        "rows": [[
            _mm(thickness),
            _val(reinf_mat),
            _val(reinf_size),
            _num(top_cover),
            _num(bot_cover),
        ]],
    }

# ── Resolvers — Load Definitions ─────────────────────────────────────────────

def resolve_live_load_definitions(input_dict: dict, bridge=None) -> dict | None:

    def _yn(key: str) -> str:
        raw = input_dict.get(key)
        if raw is None:
            return "No"
        selected = (
            raw is True
            or str(raw).strip().lower() in ("true", "yes", "1", "checked")
        )
        return "Yes" if selected else "No"

    # ── Vehicle Classes ───────────────────────────────────────────────────
    VEHICLE_KEYS = [
        ("Class A",           KEY_LL_IRC_CLASS_A),
        ("Class AA Wheeled",  KEY_LL_IRC_AA_WHEELED),
        ("Class AA Tracked",  KEY_LL_IRC_AA_TRACKED),
        ("Class 70R Wheeled", KEY_LL_IRC_70R_WHEELED),
        ("Class 70R Tracked", KEY_LL_IRC_70R_TRACKED),
        ("Class 70R Bogie",   KEY_LL_IRC_70R_BOGIE),
        ("Class SV",          KEY_LL_IRC_CLASS_SV),
        ("Class Fatigue",     KEY_LL_IRC_CLASS_FATIGUE),
    ]

    # ── Breaking Load ─────────────────────────────────────────────────────
    BREAKING_LOAD_KEYS = [
        ("Breaking Load : Class A",           KEY_BL_IRC_CLASS_A),
        ("Breaking Load : Class AA Wheeled",  KEY_BL_IRC_AA_WHEELED),
        ("Breaking Load : Class AA Tracked",  KEY_BL_IRC_AA_TRACKED),
        ("Breaking Load : Class 70R Wheeled", KEY_BL_IRC_70R_WHEELED),
        ("Breaking Load : Class 70R Tracked", KEY_BL_IRC_70R_TRACKED),
        ("Breaking Load : Class 70R Bogie",   KEY_BL_IRC_70R_BOGIE),
        ("Breaking Load : Class SV",          KEY_BL_IRC_CLASS_SV),
        ("Breaking Load : Class Fatigue",     KEY_BL_IRC_CLASS_FATIGUE),
        ("Breaking Load : Eccentricity",      KEY_BL_ECCENTRICITY),
    ]

    rows = []

    # Header row — Vehicle Classes
    rows.append(["── Vehicle Classes ──", ""])

    for label, key in VEHICLE_KEYS:
        rows.append([label, _yn(key)])

    # Header row — Breaking Load
    rows.append(["── Breaking Load ──", ""])

    for label, key in BREAKING_LOAD_KEYS:
        rows.append([label, _yn(key)])

    # ── Footpath Pressure: mode-aware ────────────────────────────────────
    fp_mode  = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE)
    fp_value = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE)

    if _has(fp_mode):
        mode_str = str(fp_mode).strip().lower()
        if mode_str in ("as per irc 6", "as per irc6", "automatic"):
            fp_display = str(fp_mode).strip()
        elif _has(fp_value):
            fp_display = _num(fp_value)
        else:
            fp_display = EMPTY
    else:
        fp_display = _num(fp_value) if _has(fp_value) else EMPTY

    rows.append(["Footpath Pressure (kN/mm²)", fp_display])

    return {
        "id":    "live_load_definitions",
        "label": "Live Load Definitions",
        "columns": [
            "Type of Live Load",
            "Value / Status",
        ],
        "rows": rows,
    }

def resolve_seismic_load_parameters(input_dict: dict, bridge=None) -> dict | None:
    """
    One row per girder. All seismic parameters are bridge-level (not girder-specific),
    so the same values repeat across rows — girder column anchors each row.
    Dead/Live load for seismic use mode+value pattern same as live load footpath.
    """
    n_girders = input_dict.get(KEY_TS_NO_OF_GIRDERS)
    if not _has(n_girders):
        return None

    try:
        n = int(n_girders)
    except Exception:
        return None

    # ── User inputs ───────────────────────────────────────────────────────
    zone              = input_dict.get(KEY_SL_SEISMIC_ZONE)
    importance        = input_dict.get(KEY_SL_IMPORTANCE_FACTOR)
    soil_type         = input_dict.get(KEY_SL_SOIL_TYPE)
    time_period       = input_dict.get(KEY_SL_TIME_PERIOD)
    damping           = input_dict.get(KEY_SL_DAMPING)
    response_red      = input_dict.get(KEY_SL_RESPONSE_REDUCTION)

    # ── Computed coefficients ─────────────────────────────────────────────
    zone_factor       = input_dict.get(KEY_SL_ZONE_FACTOR)
    spectral_coeff    = input_dict.get(KEY_SL_SPECTRAL_COEFF)
    horizontal_coeff  = input_dict.get(KEY_SL_HORIZONTAL_COEFF)
    vertical_coeff    = input_dict.get(KEY_SL_VERTICAL_COEFF)

    # ── Dead load for seismic: mode + value ───────────────────────────────
    dl_mode  = input_dict.get(KEY_SL_DEAD_LOAD_MODE)
    dl_value = input_dict.get(KEY_SL_DEAD_LOAD_VALUE)
    if _has(dl_mode) and str(dl_mode).lower() == "automatic":
        dl_display = "Automatic"
    elif _has(dl_value):
        dl_display = _num(dl_value)
    else:
        dl_display = EMPTY

    # ── Live load for seismic: mode + value ───────────────────────────────
    ll_mode  = input_dict.get(KEY_SL_LIVE_LOAD_MODE)
    ll_value = input_dict.get(KEY_SL_LIVE_LOAD_VALUE)
    if _has(ll_mode) and str(ll_mode).lower() == "automatic":
        ll_display = "Automatic"
    elif _has(ll_value):
        ll_display = _num(ll_value)
    else:
        ll_display = EMPTY

    # ── Shared parameter displays ─────────────────────────────────────────
    zone_disp     = _val(zone)          if _has(zone)             else EMPTY
    imp_disp      = _num(importance)    if _has(importance)       else EMPTY
    soil_disp     = _val(soil_type)     if _has(soil_type)        else EMPTY
    tp_disp       = _num(time_period)   if _has(time_period)      else EMPTY
    damp_disp     = _num(damping)       if _has(damping)          else EMPTY
    rr_disp       = _num(response_red)  if _has(response_red)     else EMPTY
    zf_disp       = _num(zone_factor)   if _has(zone_factor)      else EMPTY
    sa_disp       = _num(spectral_coeff)   if _has(spectral_coeff)   else EMPTY
    ah_disp       = _num(horizontal_coeff) if _has(horizontal_coeff) else EMPTY
    av_disp       = _num(vertical_coeff)   if _has(vertical_coeff)   else EMPTY

    rows = [
        [
            f"Girder {i}",
            zone_disp,
            zf_disp,
            imp_disp,
            soil_disp,
            tp_disp,
            damp_disp,
            rr_disp,
            sa_disp,
            ah_disp,
            av_disp,
            dl_display,
            ll_display,
        ]
        for i in range(1, n + 1)
    ]

    return {
        "id":    "seismic_load_parameters",
        "label": "Seismic Load Parameters",
        "columns": [
            "Girder",
            "Zone",
            "Seismic Zone Factor, Z",
            "Importance Factor, I",
            "Soil Type",
            "Time Period (s)",
            "Damping (%)",
            "Response Reduction Factor",
            "Spectral Acceleration / g, Sₐ/g",
            "Horizontal Acceleration Coefficient, Aₕ",
            "Vertical Acceleration Coefficient, Aᵥ",
            "Dead Load Considered for Seismic (kN/m)",
            "Live Load Considered for Seismic (kN/m)",
        ],
        "rows": rows,
    }

def resolve_wind_load_parameters(input_dict: dict, bridge=None) -> dict | None:
    """
    One row per girder. All wind parameters are bridge-level so values repeat
    across rows — girder column anchors each row.
    Mode-aware fields (Automatic / As per IRC 6 / User-defined) show the mode
    string when set to automatic/IRC, or the numeric value when user-defined.
    """
    n_girders = input_dict.get(KEY_TS_NO_OF_GIRDERS)
    if not _has(n_girders):
        return None

    try:
        n = int(n_girders)
    except Exception:
        return None

    # ── Direct user inputs ────────────────────────────────────────────────
    basic_wind_speed    = input_dict.get(KEY_WL_BASIC_WIND_SPEED)
    avg_exposed_height  = input_dict.get(KEY_WL_AVG_EXPOSED_HEIGHT)
    terrain_type        = input_dict.get(KEY_WL_TERRAIN_TYPE)
    site_topography     = input_dict.get(KEY_WL_SITE_TOPOGRAPHY)

    # ── Mode-aware helper: show mode label or numeric value ───────────────
    def _mode_val(mode_key, value_key, decimals=2):
        mode  = input_dict.get(mode_key)
        value = input_dict.get(value_key)
        if _has(mode):
            mode_str = str(mode).strip().lower()
            if mode_str in ("automatic", "as per irc 6", "as per irc6"):
                return str(mode).strip()   # preserve original casing
        if _has(value):
            return _num(value, decimals)
        return EMPTY

    gust_factor         = _mode_val(KEY_WL_GUST_FACTOR_MODE,        KEY_WL_GUST_FACTOR_VALUE)
    drag_coeff          = _mode_val(KEY_WL_DRAG_COEFF_MODE,          KEY_WL_DRAG_COEFF_VALUE)
    drag_coeff_ll       = _mode_val(KEY_WL_DRAG_COEFF_LL_MODE,       KEY_WL_DRAG_COEFF_LL_VALUE)
    lift_coeff          = _mode_val(KEY_WL_LIFT_COEFF_MODE,          KEY_WL_LIFT_COEFF_VALUE)
    super_area_elev     = _mode_val(KEY_WL_SUPER_AREA_ELEV_MODE,     KEY_WL_SUPER_AREA_ELEV_VALUE)
    super_area_plain    = _mode_val(KEY_WL_SUPER_AREA_PLAIN_MODE,    KEY_WL_SUPER_AREA_PLAIN_VALUE)
    exposed_frontal     = _mode_val(KEY_WL_EXPOSED_FRONTAL_MODE,     KEY_WL_EXPOSED_FRONTAL_VALUE)
    wind_ecc_deck       = _mode_val(KEY_WL_WIND_ECC_DECK_MODE,       KEY_WL_WIND_ECC_DECK_VALUE)
    wind_ll_ecc         = _mode_val(KEY_WL_WIND_LL_ECC_MODE,         KEY_WL_WIND_LL_ECC_VALUE)

    # ── Computed values ───────────────────────────────────────────────────
    hourly_mean_wind    = input_dict.get(KEY_WL_HOURLY_MEAN_WIND)
    hourly_wind_pressure = input_dict.get(KEY_WL_HOURLY_WIND_PRESSURE)

    # ── Shared parameter displays ─────────────────────────────────────────
    vb_disp      = _num(basic_wind_speed)   if _has(basic_wind_speed)   else EMPTY
    h_disp       = _num(avg_exposed_height) if _has(avg_exposed_height) else EMPTY
    ter_disp     = _val(terrain_type)       if _has(terrain_type)       else EMPTY
    topo_disp    = _val(site_topography)    if _has(site_topography)    else EMPTY
    vz_disp      = _num(hourly_mean_wind)   if _has(hourly_mean_wind)   else EMPTY
    pz_disp      = _num(hourly_wind_pressure) if _has(hourly_wind_pressure) else EMPTY

    rows = [
        [
            f"Girder {i}",
            vb_disp,
            h_disp,
            ter_disp,
            topo_disp,
            gust_factor,
            drag_coeff,
            drag_coeff_ll,
            lift_coeff,
            super_area_elev,
            super_area_plain,
            exposed_frontal,
            wind_ecc_deck,
            wind_ll_ecc,
            vz_disp,
            pz_disp,
        ]
        for i in range(1, n + 1)
    ]

    return {
        "id":    "wind_load_parameters",
        "label": "Wind Load Parameters",
        "columns": [
            "Girder",
            "Basic Wind Speed, Vᵦ (m/s)",
            "Average Exposed Height, H (m)",
            "Type of Terrain",
            "Site Topography",
            "Gust Factor, G",
            "Drag Coefficient, Cᴅ",
            "Drag Coefficient against Live Load, Cᴅʟʟ",
            "Lift Coefficient, Cᴸ",
            "Superstructure Area in Elevation, A₁ (m²)",
            "Superstructure Area in Plain, A₃ (m²)",
            "Exposed Frontal Area of Live Load, A₁ʟʟ (m²)",
            "Wind Load Eccentricity from Top of Deck (m)",
            "Wind on Live Load Eccentricity from Top of Deck (m)",
            "Hourly Mean Wind Speed, Vᵤ (m/s)",
            "Hourly Wind Pressure, Pᵤ (N/m²)",
        ],
        "rows": rows,
    }

def resolve_temperature_load_parameters(input_dict: dict, bridge=None) -> dict | None:
    """
    Single summary row — temperature load is bridge-level, not per-girder.
    Inputs: highest/lowest air temp, thermal coefficients for steel and RCC.
    Computed: effective bridge temp min/max, temperature rise/fall for design.
    """
    # ── User inputs ───────────────────────────────────────────────────────
    highest_max_temp     = input_dict.get(KEY_TL_HIGHEST_MAX_TEMP)
    lowest_min_temp      = input_dict.get(KEY_TL_LOWEST_MIN_TEMP)
    thermal_coeff_steel  = input_dict.get(KEY_TL_THERMAL_COEFF_STEEL)
    thermal_coeff_rcc    = input_dict.get(KEY_TL_THERMAL_COEFF_RCC)

    # ── Computed values ───────────────────────────────────────────────────
    bridge_temp_min      = input_dict.get(KEY_TL_BRIDGE_TEMP_MIN)
    bridge_temp_max      = input_dict.get(KEY_TL_BRIDGE_TEMP_MAX)
    temp_rise            = input_dict.get(KEY_TL_TEMP_RISE)
    temp_fall            = input_dict.get(KEY_TL_TEMP_FALL)

    # Require at least the primary user inputs to emit a row
    if not _has(highest_max_temp, lowest_min_temp):
        return None

    return {
        "id":    "temperature_load_parameters",
        "label": "Temperature Load Parameters",
        "columns": [
            "Highest Maximum Air Temperature (°C)",
            "Lowest Minimum Air Temperature (°C)",
            "Coefficient of Thermal Expansion for Steel (1/°C)",
            "Coefficient of Thermal Expansion for RCC (1/°C)",
            "Effective Bridge Temperature - Minimum (°C)",
            "Effective Bridge Temperature - Maximum (°C)",
            "Temperature for Design - Rise (°C)",
            "Temperature for Design - Fall (°C)",
        ],
        "rows": [[
            _num(highest_max_temp),
            _num(lowest_min_temp),
            _num(thermal_coeff_steel, decimals=6) if _has(thermal_coeff_steel) else EMPTY,
            _num(thermal_coeff_rcc,   decimals=6) if _has(thermal_coeff_rcc)   else EMPTY,
            _num(bridge_temp_min)  if _has(bridge_temp_min) else EMPTY,
            _num(bridge_temp_max)  if _has(bridge_temp_max) else EMPTY,
            _num(temp_rise)        if _has(temp_rise)       else EMPTY,
            _num(temp_fall)        if _has(temp_fall)       else EMPTY,
        ]],
    }

def resolve_load_combinations(input_dict: dict, bridge=None) -> dict | None:
    """
    One fixed row per IRC 6 load combination.
    'Selected' = Yes/No based on the checkbox state stored in input_dict.
    Keys map to KEY_BASIC_*, KEY_ACCIDENTAL_*, KEY_SEISMIC_*, KEY_SLS_* from common.py.
    """

    def _selected(key: str) -> str:
        raw = input_dict.get(key)
        if raw is None:
            return "No"
        selected = (
            raw is True
            or str(raw).strip().lower() in ("true", "yes", "1", "checked")
        )
        return "Yes" if selected else "No"

    # (display name, expression string, common.py key)
    COMBINATIONS = [
        # ULS Basic — LL leading adding / relieving
        ("basic_1", "1.35DL + 1.75DW + 1.5LL + 0.9WL + 0.9TL",  KEY_BASIC_LL_ADD_CASE),
        ("basic_2", "1.0DL + 1.0DW + 1.5LL + 0.9WL + 0.9TL",    KEY_BASIC_LL_REL_CASE),
        ("basic_3", "1.35DL + 1.75DW + 1.15LL + 1.5WL + 0.9TL", KEY_BASIC_WL_ADD_CASE),
        ("basic_4", "1.0DL + 1.0DW + 1.15LL + 1.5WL + 0.9TL",   KEY_BASIC_WL_REL_CASE),
        ("basic_5", "1.35DL + 1.75DW + 1.15LL + 0.9WL + 1.5TL", KEY_BASIC_TL_ADD_CASE),
        ("basic_6", "1.0DL + 1.0DW + 1.15LL + 0.9WL + 1.5TL",   KEY_BASIC_TL_REL_CASE),
        # ULS Accidental
        ("accidental_1", "1.0DL + 1.0DW + 0.75LL + 0.5TL + 1.0VC", KEY_ACCIDENTAL_VC_LL_ADD_CASE),
        ("accidental_2", "1.0DL + 1.0DW + 0.75LL + 0.5TL + 1.0BI", KEY_ACCIDENTAL_BI_LL_ADD_CASE),
        ("accidental_3", "1.0DL + 1.0DW + 0.75LL + 0.5TL + 1.0FB", KEY_ACCIDENTAL_FB_LL_ADD_CASE),
        # ULS Seismic
        ("seismic_1", "1.35DL + 1.75DW + 0.2LL + 0.5TL + 1.5EL",  KEY_SEISMIC_SERVICE_ADD_CASE),
        ("seismic_2", "1.0DL + 1.0DW + 0.2LL + 0.5TL + 1.5EL",    KEY_SEISMIC_SERVICE_REL_CASE),
        ("seismic_3", "1.35DL + 1.75DW + 0.2LL + 0.5TL + 0.75EL", KEY_SEISMIC_CONSTRUCTION_ADD_CASE),
        ("seismic_4", "1.0DL + 1.0DW + 0.2LL + 0.5TL + 0.75EL",   KEY_SEISMIC_CONSTRUCTION_REL_CASE),
        # SLS Rare
        ("rare_1", "1.0DL + 1.2DW + 1.0LL + 0.6WL + 0.6TL",   KEY_SLS_RARE_LL_ADD_CASE),
        ("rare_2", "1.0DL + 1.0DW + 1.0LL + 0.6WL + 0.6TL",   KEY_SLS_RARE_LL_REL_CASE),
        ("rare_3", "1.0DL + 1.2DW + 0.75LL + 1.0WL + 0.6TL",  KEY_SLS_RARE_WL_ADD_CASE),
        ("rare_4", "1.0DL + 1.0DW + 0.75LL + 1.0WL + 0.6TL",  KEY_SLS_RARE_WL_REL_CASE),
        ("rare_5", "1.0DL + 1.2DW + 0.75LL + 0.6WL + 1.0TL",  KEY_SLS_RARE_TL_ADD_CASE),
        ("rare_6", "1.0DL + 1.0DW + 0.75LL + 0.6WL + 1.0TL",  KEY_SLS_RARE_TL_REL_CASE),
        # SLS Frequent
        ("frequent_1", "1.0DL + 1.2DW + 0.75LL + 0.5WL + 0.5TL", KEY_SLS_FREQ_LL_ADD_CASE),
        ("frequent_2", "1.0DL + 1.0DW + 0.75LL + 0.5WL + 0.5TL", KEY_SLS_FREQ_LL_REL_CASE),
        ("frequent_3", "1.0DL + 1.2DW + 0.2LL + 0.6WL + 0.5TL",  KEY_SLS_FREQ_WL_ADD_CASE),
        ("frequent_4", "1.0DL + 1.0DW + 0.2LL + 0.6WL + 0.5TL",  KEY_SLS_FREQ_WL_REL_CASE),
        ("frequent_5", "1.0DL + 1.2DW + 0.2LL + 0.5WL + 0.6TL",  KEY_SLS_FREQ_TL_ADD_CASE),
        ("frequent_6", "1.0DL + 1.0DW + 0.2LL + 0.5WL + 0.6TL",  KEY_SLS_FREQ_TL_REL_CASE),
        # SLS Quasi-permanent
        ("quasi_permanent_1", "1.0DL + 1.2DW + 0.5TL", KEY_SLS_QP_ADD_CASE),
        ("quasi_permanent_2", "1.0DL + 1.0DW + 0.5TL", KEY_SLS_QP_REL_CASE),
    ]

    rows = [
        [name, expr, _selected(key)]
        for name, expr, key in COMBINATIONS
    ]

    return {
        "id":    "load_combinations",
        "label": "Load Combinations",
        "columns": [
            "Combination",
            "Expression",
            "Selected",
        ],
        "rows": rows,
    }
    
# ── Resolvers — Deflections (Analysis Results) ────────────────────────────────

def resolve_deflection_live_load(input_dict: dict, bridge=None) -> dict | None:
    """
    Analysis-result deflection table — live load only.
    KEY_DO_SLS_DEFLECTION stores the user-entered/computed deflection limit toggle.
    Actual deflection values come from analysis; only the limit input is available
    here, so we show the user's limit and leave the computed value as EMPTY.
    """
    defl_limit = input_dict.get(KEY_DO_SLS_DEFLECTION)
    n_girders  = input_dict.get(KEY_TS_NO_OF_GIRDERS)

    if not _has(n_girders):
        return None

    try:
        n = int(n_girders)
    except Exception:
        return None

    rows = [
        [f"Girder {i}", EMPTY, _val(defl_limit) if _has(defl_limit) else EMPTY, EMPTY]
        for i in range(1, n + 1)
    ]

    return {
        "id":    "deflection_live_load",
        "label": "Deflection - Live Load",
        "columns": [
            "Girder",
            "Deflection due to Live Load, δ_ₗᵢᵥₑ (mm)",
            "Permissible Limit",
            "Status",
        ],
        "rows": rows,
    }


def resolve_deflection_total_load(input_dict: dict, bridge=None) -> dict | None:
    """
    Analysis-result deflection table — total load.
    Permissible limit = Span / 600 (IRC:6 Cl.211.2).
    """
    span      = input_dict.get(KEY_SPAN)
    n_girders = input_dict.get(KEY_TS_NO_OF_GIRDERS)

    if not _has(n_girders):
        return None

    try:
        n = int(n_girders)
    except Exception:
        return None

    limit_str = (
        f"L/600 = {round(float(span) * 1000 / 600, 1)} mm"
        if _has(span) else EMPTY
    )

    rows = [
        [f"Girder {i}", EMPTY, limit_str, EMPTY]
        for i in range(1, n + 1)
    ]

    return {
        "id":    "deflection_total_load",
        "label": "Deflection - Total Load",
        "columns": [
            "Girder",
            "Total Deflection, δₜₒₜₐₗ (mm)",
            "Permissible Limit",
            "Status",
        ],
        "rows": rows,
    }


# ── Resolvers — ULS Checks ────────────────────────────────────────────────────

def _uls_girder_rows(n_girders) -> int | None:
    try:
        return int(n_girders)
    except Exception:
        return None


def resolve_flexural_resistance_check(input_dict: dict, bridge=None) -> dict | None:
    dcr       = input_dict.get(KEY_UTIL_FLEXURE)
    n_girders = input_dict.get(KEY_TS_NO_OF_GIRDERS)

    if not _has(n_girders):
        return None
    n = _uls_girder_rows(n_girders)
    if n is None:
        return None

    rows = [
        [f"Girder {i}", EMPTY, EMPTY, _val(dcr) if _has(dcr) else EMPTY, EMPTY]
        for i in range(1, n + 1)
    ]

    return {
        "id":    "flexural_resistance_check",
        "label": "Flexural Resistance Check",
        "columns": [
            "Girder",
            "Ultimate Bending Moment, Mᵤ (kNm)",
            "Design Bending Moment, Mᵈ (kNm)",
            "Demand to Capacity Ratio, DCR",
            "Status",
        ],
        "rows": rows,
    }


def resolve_shear_resistance_check(input_dict: dict, bridge=None) -> dict | None:
    dcr       = input_dict.get(KEY_UTIL_SHEAR)
    n_girders = input_dict.get(KEY_TS_NO_OF_GIRDERS)

    if not _has(n_girders):
        return None
    n = _uls_girder_rows(n_girders)
    if n is None:
        return None

    rows = [
        [f"Girder {i}", EMPTY, EMPTY, _val(dcr) if _has(dcr) else EMPTY, EMPTY]
        for i in range(1, n + 1)
    ]

    return {
        "id":    "shear_resistance_check",
        "label": "Shear Resistance Check",
        "columns": [
            "Girder",
            "Ultimate Shear Force, Vᵤ (kN)",
            "Design Shear Force, Vᵈ (kN)",
            "Demand to Capacity Ratio, DCR",
            "Status",
        ],
        "rows": rows,
    }


def resolve_bending_shear_interaction_check(input_dict: dict, bridge=None) -> dict | None:
    dcr       = input_dict.get(KEY_UTIL_INTERACTION)
    n_girders = input_dict.get(KEY_TS_NO_OF_GIRDERS)

    if not _has(n_girders):
        return None
    n = _uls_girder_rows(n_girders)
    if n is None:
        return None

    rows = [
        [f"Girder {i}", EMPTY, EMPTY, _val(dcr) if _has(dcr) else EMPTY, EMPTY, EMPTY]
        for i in range(1, n + 1)
    ]

    return {
        "id":    "bending_shear_interaction_check",
        "label": "Bending-Shear Interaction Check",
        "columns": [
            "Girder",
            "Ultimate Bending Moment, Mᵤ (kNm)",
            "Reduced Design Bending Resistance, Mᵈᵥ (kNm)",
            "Demand to Capacity Ratio, DCR",
            "Clause Reference",
            "Status",
        ],
        "rows": rows,
    }


def resolve_lateral_torsional_buckling_check(input_dict: dict, bridge=None) -> dict | None:
    dcr       = input_dict.get(KEY_UTIL_LTB)
    n_girders = input_dict.get(KEY_TS_NO_OF_GIRDERS)

    if not _has(n_girders):
        return None
    n = _uls_girder_rows(n_girders)
    if n is None:
        return None

    rows = [
        [f"Girder {i}", EMPTY, EMPTY, EMPTY, EMPTY, _val(dcr) if _has(dcr) else EMPTY, EMPTY, EMPTY]
        for i in range(1, n + 1)
    ]

    return {
        "id":    "lateral_torsional_buckling_check",
        "label": "Lateral Torsional Buckling Check - Construction Stage",
        "columns": [
            "Girder",
            "Ultimate Bending Moment, Mᵤ (kNm)",
            "LTB Design Buckling Resistance, Mᵦ (kNm)",
            "LTB Reduction Factor, χ_LT",
            "Non-Dimensional Slenderness, λ̄_LT",
            "Demand to Capacity Ratio, DCR",
            "Clause Reference",
            "Status",
        ],
        "rows": rows,
    }


# ── Resolvers — SLS / Stress ──────────────────────────────────────────────────

def resolve_stress_reinf_service(input_dict: dict, bridge=None) -> dict | None:
    stress    = input_dict.get(KEY_DO_SLS_STRESS)
    n_girders = input_dict.get(KEY_TS_NO_OF_GIRDERS)

    if not _has(n_girders):
        return None
    n = _uls_girder_rows(n_girders)
    if n is None:
        return None

    rows = [
        [f"Girder {i}", _val(stress) if _has(stress) else EMPTY, EMPTY]
        for i in range(1, n + 1)
    ]

    return {
        "id":    "stress_reinf_service",
        "label": "Stress in Reinforcement - Service",
        "columns": [
            "Girder",
            "Stress in Reinforcement, σᵣₑᵢₙf (MPa)",
            "Allowable Stress (MPa)",
        ],
        "rows": rows,
    }


# ── Resolvers — Fatigue ───────────────────────────────────────────────────────

def resolve_fatigue_assessment_girder(input_dict: dict, bridge=None) -> dict | None:
    fatigue   = input_dict.get(KEY_DO_ULS_FATIGUE)
    n_girders = input_dict.get(KEY_TS_NO_OF_GIRDERS)

    if not _has(n_girders):
        return None
    n = _uls_girder_rows(n_girders)
    if n is None:
        return None

    rows = [
        [f"Girder {i}", _val(fatigue) if _has(fatigue) else EMPTY, EMPTY, EMPTY]
        for i in range(1, n + 1)
    ]

    return {
        "id":    "fatigue_assessment_girder",
        "label": "Fatigue Assessment - Girder",
        "columns": [
            "Girder",
            "Stress Range, Δσ (MPa)",
            "Fatigue Limit, ffd (MPa)",
            "Status",
        ],
        "rows": rows,
    }


# ── Resolvers — Shear Connector Capacity (partial) ───────────────────────────

def resolve_shear_connector_capacity(input_dict: dict, bridge=None) -> dict | None:
    """
    Populate columns that come directly from user inputs.
    Computed columns (Qu, Qd, ΣQd, Clause) remain EMPTY until analysis runs.
    """
    diameter  = input_dict.get(KEY_DS_STUD_DIAMETER)
    height    = input_dict.get(KEY_DS_STUD_HEIGHT)
    fu_stud   = input_dict.get(KEY_DS_STUD_ULTIMATE_STRENGTH)
    count     = input_dict.get(KEY_DS_STUD_COUNT)
    n_girders = input_dict.get(KEY_TS_NO_OF_GIRDERS)

    if not _has(n_girders):
        return None
    n = _uls_girder_rows(n_girders)
    if n is None:
        return None

    # fck comes from the material DB via bridge if available
    fck = EMPTY
    ecm = EMPTY
    try:
        cp  = bridge._build_material_props().concrete_prop
        fck = _num(cp.fck)
        ecm = _num(cp.Ecm)
    except Exception:
        pass

    rows = [
        [
            f"Girder {i}",
            _num(diameter) if _has(diameter) else EMPTY,
            _num(height)   if _has(height)   else EMPTY,
            _num(fu_stud)  if _has(fu_stud)  else EMPTY,
            fck,
            ecm,
            EMPTY,   # Qu — computed
            EMPTY,   # Qd — computed
            _val(count) if _has(count) else EMPTY,
            EMPTY,   # ΣQd — computed
            EMPTY,   # Clause
        ]
        for i in range(1, n + 1)
    ]

    return {
        "id":    "shear_connector_capacity",
        "label": "Shear Connector Capacity",
        "columns": [
            "Girder",
            "Stud Diameter, d (mm)",
            "Stud Height, h (mm)",
            "Ultimate Tensile Strength of Stud, fu (MPa)",
            "Characteristic Compressive Strength, fck (MPa)",
            "Modulus of Elasticity of Concrete, Ec (MPa)",
            "Nominal Capacity per Stud, Qu (kN)",
            "Design Capacity per Stud, Qd (kN)",
            "No. of Studs per Section",
            "Total Design Capacity, ΣQd (kN)",
            "Clause Reference",
        ],
        "rows": rows,
    }


# ── Resolvers — Crack Width Check (partial) ───────────────────────────────────

def resolve_crack_width_check(input_dict: dict, bridge=None) -> dict | None:
    bar_dia     = input_dict.get(KEY_DS_REINF_BOUNDS)
    spacing_t   = input_dict.get(KEY_DECK_REINF_SPACING_TRANS)
    spacing_l   = input_dict.get(KEY_DECK_REINF_SPACING_LONG)
    n_girders   = input_dict.get(KEY_TS_NO_OF_GIRDERS)

    if not _has(n_girders):
        return None
    n = _uls_girder_rows(n_girders)
    if n is None:
        return None

    # Use transverse spacing as the governing bar spacing for crack width
    spacing = spacing_t if _has(spacing_t) else spacing_l

    rows = [
        [
            f"Girder {i}",
            EMPTY,   # wk — computed
            EMPTY,   # permissible limit — computed
            EMPTY,   # As,min — computed
            EMPTY,   # As,prov — computed
            _val(bar_dia) if _has(bar_dia) else EMPTY,
            _val(spacing) if _has(spacing) else EMPTY,
            EMPTY,   # Clause
            EMPTY,   # Status
        ]
        for i in range(1, n + 1)
    ]

    return {
        "id":    "crack_width_check",
        "label": "Crack Width Check",
        "columns": [
            "Girder",
            "Calculated Crack Width, wₖ (mm)",
            "Permissible Crack Width Limit (mm)",
            "Minimum Reinforcement Area, As,min (mm²)",
            "Reinforcement Area Provided, As,prov (mm²)",
            "Bar Diameter, φ (mm)",
            "Bar Spacing, s (mm)",
            "Clause Reference",
            "Status",
        ],
        "rows": rows,
    }


# ── Fix: deck_slab_properties — Bottom Reinforcement column ──────────────────
# The schema has "Bottom Reinforcement" but the original resolver only returns
# "Reinforcement Material" and "Reinforcement Size".  Override the resolver to
# match the schema column list exactly.

def resolve_deck_slab_properties(input_dict: dict, bridge=None) -> dict | None:
    thickness  = input_dict.get(KEY_TS_DECK_THICKNESS)
    reinf_size = input_dict.get(KEY_DS_REINF_BOUNDS)
    reinf_mat  = input_dict.get(KEY_DS_REINF_MATERIAL)
    top_cover  = input_dict.get(KEY_DS_TOP_CLEAR_COVER)
    bot_cover  = input_dict.get(KEY_DS_BOTTOM_CLEAR_COVER)

    if not _has(thickness):
        return None

    # Top reinforcement: combine material + size when both available
    top_reinf = (
        f"{reinf_mat} — {reinf_size} mm"
        if _has(reinf_mat) and _has(reinf_size)
        else _val(reinf_mat or reinf_size)
    )
    # Bottom reinforcement: same bar size/material, different cover — show same label
    bot_reinf = top_reinf   # symmetrical until a separate key is introduced

    return {
        "id":    "deck_slab_properties",
        "label": "Deck Slab Properties",
        "columns": [
            "Thickness (mm)",
            "Top Reinforcement",
            "Bottom Reinforcement",
            "Top Cover (mm)",
            "Bottom Cover (mm)",
        ],
        "rows": [[
            _mm(thickness),
            top_reinf,
            bot_reinf,
            _num(top_cover),
            _num(bot_cover),
        ]],
    }



# ── Resolvers — Analysis Results: Load Effects (Girder) ───────────────────────

def _get_force_context(bridge):
    """
    Build all data needed for force lookups in one shot.

    Returns (ds, g_map, girders, filtered_lcs) or (None, None, None, None).
    build_girders() is expensive (calls OpenSeesPy) so we call it exactly once
    here and share the result across all element loops.
    Vehicle (live load position) cases are excluded — only dead loads and
    combination load cases are included.
    """
    rh = bridge.get_result_handler()
    if rh is None:
        return None, None, None, None
    ds = rh.ds
    if ds is None:
        return None, None, None, None
    g_map, _ = rh.build_girders(verbose=False)
    girders = [k for k in g_map if not k.startswith("EB")]

    classified = rh.classify_loadcases()
    exclude = set(
        classified.get("vehicle_static", []) +
        classified.get("vehicle_moving", [])
    )
    all_lcs = [
        lc for lc in classified.get("all", [])
        if lc not in exclude and "moving" not in str(lc).lower()
    ]

    if not girders or not all_lcs:
        return None, None, None, None
    return ds, g_map, girders, all_lcs


def _force_max_min(ds, g_map, load_case: str, girder: str, comp_i: str, comp_j: str):
    """
    Return (max_val, min_val) across both element ends for one girder / load case.
    Queries the xarray dataset directly — no per-call build_girders() overhead.
    Values are divided by 1000 (N→kN / Nmm→kNm).
    Returns (None, None) if no data is available.
    """
    elements = g_map.get(girder, {}).get("elements", [])
    values = []
    for comp in (comp_i, comp_j):
        for eid in elements:
            try:
                val = float(ds.sel(Loadcase=load_case, Element=eid, Component=comp)["forces"]) / 1000.0
                values.append(val)
            except Exception:
                pass
    if not values:
        return None, None
    return round(max(values), 3), round(min(values), 3)


def resolve_bending_moment_envelope(input_dict: dict, bridge=None) -> dict | None:
    if bridge is None:
        return None
    try:
        _t0 = time.perf_counter()
        ds, g_map, girders, all_lcs = _get_force_context(bridge)
        _t1 = time.perf_counter()
        print(f"[TIMER] bending_moment_envelope  context: {_t1-_t0:.3f}s  ({len(all_lcs or [])} LCs, {len(girders or [])} girders)")
        if ds is None:
            return None

        rows = []
        for girder in girders:
            env_max, env_min = None, None
            for lc in all_lcs:
                mx, mn = _force_max_min(ds, g_map, lc, girder, "Mz_i", "Mz_j")
                if mx is not None:
                    env_max = mx if env_max is None else max(env_max, mx)
                if mn is not None:
                    env_min = mn if env_min is None else min(env_min, mn)
            rows.append([
                girder,
                _num(env_max) if env_max is not None else EMPTY,
                _num(env_min) if env_min is not None else EMPTY,
            ])

        print(f"[TIMER] bending_moment_envelope  total:   {time.perf_counter()-_t0:.3f}s")
        return {
            "id": "bending_moment_envelope",
            "label": "Bending Moment Diagram - Envelope",
            "columns": [
                "Girder",
                "Maximum Bending Moment, Mₘₐₓ (kNm)",
                "Minimum Bending Moment, Mₘᵢₙ (kNm)",
            ],
            "rows": rows,
        }
    except Exception as exc:
        logger.warning("resolve_bending_moment_envelope failed: %s", exc, exc_info=True)
        return None


def resolve_shear_force_envelope(input_dict: dict, bridge=None) -> dict | None:
    if bridge is None:
        return None
    try:
        _t0 = time.perf_counter()
        ds, g_map, girders, all_lcs = _get_force_context(bridge)
        _t1 = time.perf_counter()
        print(f"[TIMER] shear_force_envelope     context: {_t1-_t0:.3f}s  ({len(all_lcs or [])} LCs, {len(girders or [])} girders)")
        if ds is None:
            return None

        rows = []
        for girder in girders:
            env_max, env_min = None, None
            for lc in all_lcs:
                mx, mn = _force_max_min(ds, g_map, lc, girder, "Vy_i", "Vy_j")
                if mx is not None:
                    env_max = mx if env_max is None else max(env_max, mx)
                if mn is not None:
                    env_min = mn if env_min is None else min(env_min, mn)
            rows.append([
                girder,
                _num(env_max) if env_max is not None else EMPTY,
                _num(env_min) if env_min is not None else EMPTY,
            ])

        print(f"[TIMER] shear_force_envelope     total:   {time.perf_counter()-_t0:.3f}s")
        return {
            "id": "shear_force_envelope",
            "label": "Shear Force Diagram - Envelope",
            "columns": [
                "Girder",
                "Maximum Shear Force, Vₘₐₓ (kN)",
                "Minimum Shear Force, Vₘᵢₙ (kN)",
            ],
            "rows": rows,
        }
    except Exception as exc:
        logger.warning("resolve_shear_force_envelope failed: %s", exc, exc_info=True)
        return None


def resolve_bending_moment_by_load_case(input_dict: dict, bridge=None) -> dict | None:
    if bridge is None:
        return None
    try:
        _t0 = time.perf_counter()
        ds, g_map, girders, all_lcs = _get_force_context(bridge)
        _t1 = time.perf_counter()
        print(f"[TIMER] bending_moment_by_lc     context: {_t1-_t0:.3f}s  ({len(all_lcs or [])} LCs, {len(girders or [])} girders)")
        if ds is None:
            return None

        columns = ["Girder"]
        for lc in all_lcs:
            columns.append(f"{lc} - Max (kNm)")
            columns.append(f"{lc} - Min (kNm)")

        rows = []
        for girder in girders:
            row = [girder]
            for lc in all_lcs:
                mx, mn = _force_max_min(ds, g_map, lc, girder, "Mz_i", "Mz_j")
                row.append(_num(mx) if mx is not None else EMPTY)
                row.append(_num(mn) if mn is not None else EMPTY)
            rows.append(row)

        print(f"[TIMER] bending_moment_by_lc     total:   {time.perf_counter()-_t0:.3f}s")
        return {
            "id": "bending_moment_by_load_case",
            "label": "Bending Moment - By Load Case",
            "columns": columns,
            "rows": rows,
        }
    except Exception as exc:
        logger.warning("resolve_bending_moment_by_load_case failed: %s", exc, exc_info=True)
        return None


def resolve_shear_force_by_load_case(input_dict: dict, bridge=None) -> dict | None:
    if bridge is None:
        return None
    try:
        _t0 = time.perf_counter()
        ds, g_map, girders, all_lcs = _get_force_context(bridge)
        _t1 = time.perf_counter()
        print(f"[TIMER] shear_force_by_lc        context: {_t1-_t0:.3f}s  ({len(all_lcs or [])} LCs, {len(girders or [])} girders)")
        if ds is None:
            return None

        columns = ["Girder"]
        for lc in all_lcs:
            columns.append(f"{lc} - Max (kN)")
            columns.append(f"{lc} - Min (kN)")

        rows = []
        for girder in girders:
            row = [girder]
            for lc in all_lcs:
                mx, mn = _force_max_min(ds, g_map, lc, girder, "Vy_i", "Vy_j")
                row.append(_num(mx) if mx is not None else EMPTY)
                row.append(_num(mn) if mn is not None else EMPTY)
            rows.append(row)

        print(f"[TIMER] shear_force_by_lc        total:   {time.perf_counter()-_t0:.3f}s")
        return {
            "id": "shear_force_by_load_case",
            "label": "Shear Force - By Load Case",
            "columns": columns,
            "rows": rows,
        }
    except Exception as exc:
        logger.warning("resolve_shear_force_by_load_case failed: %s", exc, exc_info=True)
        return None


# ── Registry — must be after all resolver definitions ────────────────────────

RESOLVER_MAP: dict[str, callable] = {
    # ── Model Definition ──────────────────────────────────────────────────
    "bridge_configuration_summary":       resolve_bridge_config_summary,
    "material_properties_steel":          resolve_material_properties_steel,
    "material_properties_concrete":       resolve_material_properties_concrete,
    "girder_section_properties":          resolve_girder_section_properties,
    "cross_bracing_section_properties":   resolve_cross_bracing_section_properties,
    "end_diaphragm_section_properties":   resolve_end_diaphragm_section_properties,
    "shear_stud_properties":              resolve_shear_stud_properties,
    "deck_slab_properties":               resolve_deck_slab_properties,       # ← overrides original

    # ── Load Definitions ──────────────────────────────────────────────────
    "seismic_load_parameters": resolve_seismic_load_parameters,
    "wind_load_parameters": resolve_wind_load_parameters,
    "temperature_load_parameters": resolve_temperature_load_parameters,
    "load_combinations": resolve_load_combinations,

    # ── Analysis Results — Load Effects (Girder) ─────────────────────────────
    "bending_moment_envelope":            resolve_bending_moment_envelope,
    "shear_force_envelope":               resolve_shear_force_envelope,
    "bending_moment_by_load_case":        resolve_bending_moment_by_load_case,
    "shear_force_by_load_case":           resolve_shear_force_by_load_case,

    # ── Analysis Results — Deflections ────────────────────────────────────
    "deflection_live_load":               resolve_deflection_live_load,
    "deflection_total_load":              resolve_deflection_total_load,

    # ── ULS Checks ────────────────────────────────────────────────────────
    "flexural_resistance_check":          resolve_flexural_resistance_check,
    "shear_resistance_check":             resolve_shear_resistance_check,
    "bending_shear_interaction_check":    resolve_bending_shear_interaction_check,
    "lateral_torsional_buckling_check":   resolve_lateral_torsional_buckling_check,

    # ── SLS — Deflection Control ──────────────────────────────────────────
    "deflection_control_live":            resolve_deflection_live_load,        # same data, two table IDs
    "deflection_control_total":           resolve_deflection_total_load,

    # ── SLS — Stress ──────────────────────────────────────────────────────
    "stress_reinf_service":               resolve_stress_reinf_service,

    # ── Fatigue ───────────────────────────────────────────────────────────
    "fatigue_assessment_girder":          resolve_fatigue_assessment_girder,

    # ── Shear Connector ───────────────────────────────────────────────────
    "shear_connector_capacity":           resolve_shear_connector_capacity,

    # ── Crack Width ───────────────────────────────────────────────────────
    "crack_width_check":                  resolve_crack_width_check,
}