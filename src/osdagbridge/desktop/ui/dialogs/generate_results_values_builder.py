import logging
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


def _weather_value(input_dict: dict, field: str):
    """
    Read a value straight from the project-location weather data, e.g.
        input_dict["project.location"]["weather_data"]["wind_speed" | "zone" |
                                                       "max_temp" | "min_temp"]
    Used as a fallback when the loading-tab sync hasn't persisted the value into
    its own KEY_WL_*/KEY_SL_*/KEY_TL_* key. Returns None if unavailable.
    """
    loc = input_dict.get(KEY_PROJECT_LOCATION)
    if isinstance(loc, dict):
        wd = loc.get("weather_data")
        if isinstance(wd, dict):
            return wd.get(field)
    return None


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

    def _dim(base_key, gi, mi):
        """
        Display a dimension field that may hold a number (Custom design mode),
        the marker "Custom" with the chosen options under a '.selected' sub-key,
        or "All"/a list (Optimized mode, TYPE_ALL_CUSTOM). Always shows something.
        """
        v = _gk(base_key, gi, mi)
        if v in (None, "", [], {}):
            return EMPTY
        if isinstance(v, str) and v.strip().lower() == "custom":
            sel = input_dict.get(f"{base_key}.selected.G{gi}.M{mi}")
            if isinstance(sel, (list, tuple)) and sel:
                return ", ".join(str(s) for s in sel)
            return "All"
        if isinstance(v, (list, tuple)):
            return ", ".join(str(s) for s in v) if v else EMPTY
        try:
            return round(float(v), 2)
        except (ValueError, TypeError):
            return _val(v)

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
                _dim(KEY_MP_GIRDER_DEPTH,                  gi, mi),  # stored in mm
                _dim(KEY_MP_GIRDER_TOP_FLANGE_WIDTH,       gi, mi),  # mm
                _dim(KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,   gi, mi),  # mm / "All"
                _dim(KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH,    gi, mi),  # mm
                _dim(KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,gi, mi),  # mm / "All"
                _val(_gk(KEY_MP_GD_SUPPORT_TYPE,               gi, mi)),
                _num(_gk(KEY_MP_GD_SUPPORT_WIDTH,              gi, mi)),  # mm
                _dim(KEY_MP_GIRDER_WEB_THICKNESS,          gi, mi),  # mm / "All"
                _val(_gk(KEY_MP_GIRDER_TORSIONAL_RESTRAINT,    gi, mi)),
                _val(_gk(KEY_MP_GIRDER_WARPING_RESTRAINT,      gi, mi)),
                _val(_gk(KEY_MP_GIRDER_WEB_TYPE,               gi, mi)),
                _num(_gk(KEY_MP_GIRDER_MASS,                   gi, mi)),  # kg/m, no conversion
                _cm2(_gk(KEY_MP_GIRDER_SECTIONAL_AREA,         gi, mi)),  # m² → cm²
                _cm4(_gk(KEY_MP_GIRDER_SECTIONAL_IZ,           gi, mi)),  # m⁴ → cm⁴
                _cm4(_gk(KEY_MP_GIRDER_SECTIONAL_IY,           gi, mi)),
                _cm (_gk(KEY_MP_GIRDER_RADIUS_GYRATION_Z,      gi, mi)),  # m → cm
                _cm (_gk(KEY_MP_GIRDER_RADIUS_GYRATION_Y,      gi, mi)),
                _cm3(_gk(KEY_MP_GIRDER_ELASTIC_MODULUS_ZZ,     gi, mi)),  # m³ → cm³
                _cm3(_gk(KEY_MP_GIRDER_ELASTIC_MODULUS_ZY,     gi, mi)),
                _cm3(_gk(KEY_MP_GIRDER_PLASTIC_MODULUS_ZUZ,    gi, mi)),
                _cm3(_gk(KEY_MP_GIRDER_PLASTIC_MODULUS_ZUY,    gi, mi)),
                _cm4(_gk(KEY_MP_GIRDER_TORSION_CONSTANT_IT,    gi, mi)),
                _cm6(_gk(KEY_MP_GIRDER_WARPING_CONSTANT_IW,    gi, mi)),  # m⁶ → cm⁶
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
    if n < 2:
        return None   # cross bracing needs at least one adjacent girder pair

    from osdagbridge.core.utils.common import (
        CROSS_BRACING_DEFAULTS, DEFAULT_CROSS_BRACING_SPACING,
    )

    # Number of bracing members per girder pair (defaults to 1).
    try:
        n_brace = max(1, int(float(input_dict.get(KEY_MP_CB_NO_OF_CROSS_BRACINGS) or 1)))
    except Exception:
        n_brace = 1

    # Spacing is a single global value (metres) — NOT stored per member.
    spacing = input_dict.get(KEY_MP_CB_SPACING)
    spacing_disp = _num(spacing) if _has(spacing) else _num(DEFAULT_CROSS_BRACING_SPACING)

    def _cbk(base_key, gi, mi, default_key):
        """Per-member CB value, falling back to CROSS_BRACING_DEFAULTS."""
        v = input_dict.get(f"{base_key}.G{gi}G{gi + 1}.B{gi}M{mi}")
        if v in (None, ""):
            return CROSS_BRACING_DEFAULTS.get(default_key, "")
        return v

    rows = []
    for gi in range(1, n):
        for mi in range(1, n_brace + 1):
            rows.append([
                f"G{gi}G{gi + 1}_B{gi}M{mi}",
                _val(_cbk(KEY_MP_CB_TYPE, gi, mi, "type")),
                _val(_cbk(KEY_MP_CB_BRACING_SECTION_TYPE, gi, mi, "bracing_section_type")),
                _val(_cbk(KEY_MP_CB_BRACING_SECTION_DESIGNATION, gi, mi, "bracing_section_designation")),
                _val(_cbk(KEY_MP_CB_TOP_CHORD, gi, mi, "top_chord")),
                _val(_cbk(KEY_MP_CB_TOP_CHORD_SECTION_TYPE, gi, mi, "top_chord_section_type")),
                _val(_cbk(KEY_MP_CB_TOP_CHORD_SECTION_DESIG, gi, mi, "top_chord_section_desig")),
                _val(_cbk(KEY_MP_CB_BOTTOM_CHORD, gi, mi, "bottom_chord")),
                _val(_cbk(KEY_MP_CB_BOTTOM_CHORD_SECTION_TYPE, gi, mi, "bottom_chord_section_type")),
                _val(_cbk(KEY_MP_CB_BOTTOM_CHORD_SECTION_DESIG, gi, mi, "bottom_chord_section_desig")),
                spacing_disp,
            ])

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
    n_girders = input_dict.get(KEY_TS_NO_OF_GIRDERS)
    if not _has(n_girders):
        return None
    try:
        n = int(n_girders)
    except Exception:
        return None
    if n < 2:
        return None

    # Type defaults to "Cross Bracing"; welded/rolled-beam geometry fields are
    # blank unless that ED type is chosen (mirrors defaults.py _ED_DEFAULTS).
    def _edk(base_key, gi, mi):
        return input_dict.get(f"{base_key}.G{gi}G{gi + 1}.E{gi}M{mi}")

    def _ed_type(gi, mi):
        v = _edk(KEY_MP_ED_TYPE, gi, mi)
        return _val(v) if _has(v) else "Cross Bracing"

    rows = []
    for gi in range(1, n):
        for mi in (1, 2):
            rows.append([
                f"G{gi}G{gi + 1}_E{gi}M{mi}",
                _ed_type(gi, mi),
                _val(_edk(KEY_MP_ED_SYMMETRY,                gi, mi)),
                _num(_edk(KEY_MP_ED_TOTAL_DEPTH,             gi, mi)),
                _num(_edk(KEY_MP_ED_WEB_THICKNESS,           gi, mi)),
                _num(_edk(KEY_MP_ED_TOP_FLANGE_WIDTH,        gi, mi)),
                _num(_edk(KEY_MP_ED_TOP_FLANGE_THICKNESS,    gi, mi)),
                _num(_edk(KEY_MP_ED_BOTTOM_FLANGE_WIDTH,     gi, mi)),
                _num(_edk(KEY_MP_ED_BOTTOM_FLANGE_THICKNESS, gi, mi)),
            ])

    if not rows:
        return None

    return {
        "id":    "end_diaphragm_section_properties",
        "label": "End Diaphragm Section Properties",
        "columns": [
            "Member ID",
            "Type",
            "Symmetry",
            "Total Depth, d(mm)",
            "Web Thickness, wt(mm)",
            "Width of Top Flange(mm)",
            "Top Flange Thickness (mm)",
            "Width of Bottom Flange(mm)",
            "Bottom Flange Thickness (mm)",
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


# ── Resolvers — Load Definitions ─────────────────────────────────────────────

def resolve_permanent_load_summary(input_dict: dict, bridge=None) -> dict | None:
    """
    Total permanent dead load per girder (kN/m) — single cell, matching schema.

    Recomputed self-contained from inputs (no analysis run required), summing the
    same dead-load components the analyser applies, expressed as an average line
    load per girder:
        SW   girder self-weight × self-weight factor   (per-girder kN/m, averaged)
        DD   concrete deck slab        (kN/m² × deck width ÷ n girders)
        DW   wearing course / surfacing (kN/m² × deck width ÷ n girders)
        SIDL footpath (×2 strips), crash barriers (×2), railings (×2), median (×1)
             — line/area loads shared equally across girders.

    Area loads use overall bridge width as the tributary basis. Any missing
    input contributes zero. Sectional area is read as m² (the unit seeded by
    defaults.py and assumed by the section-property resolvers).
    """
    n_girders = input_dict.get(KEY_TS_NO_OF_GIRDERS)
    if not _has(n_girders):
        return None
    try:
        n = int(n_girders)
    except Exception:
        return None
    if n <= 0:
        return None

    from osdagbridge.core.bridge_components.super_structure.plate_girder.geometry import (
        girder_self_weight_kN_m, STEEL_UNIT_WEIGHT_kN_m3,
    )
    from osdagbridge.core.bridge_components.super_structure.deck.geometry import (
        slab_dead_load_kN_m2, wearing_course_dead_load_kN_m2, WET_CONCRETE_DENSITY_kN_m3,
    )
    from osdagbridge.core.bridge_components.super_structure.footpath.geometry import (
        footpath_dead_load_kN_m2,
    )

    def _f(key, default=None):
        try:
            return float(input_dict.get(key))
        except (TypeError, ValueError):
            return default

    # ── SW: average girder self-weight × self-weight factor ────────────────
    sw_factor = _f(KEY_PL_SELF_WEIGHT_FACTOR, 1.0)
    areas = [
        a for gi in range(1, n + 1)
        if (a := _f(f"{KEY_MP_GIRDER_SECTIONAL_AREA}.G{gi}.M1")) is not None
    ]
    sw = (
        (sum(girder_self_weight_kN_m(a, STEEL_UNIT_WEIGHT_kN_m3) for a in areas) / len(areas))
        if areas else 0.0
    ) * sw_factor

    # ── Tributary basis for distributing deck-level loads ──────────────────
    deck_width = _f(KEY_TS_OVERALL_WIDTH, 0.0) or 0.0

    # ── DD: concrete deck slab ─────────────────────────────────────────────
    deck_t = _f(KEY_TS_DECK_THICKNESS)            # mm
    dd = (slab_dead_load_kN_m2(deck_t / 1000.0, WET_CONCRETE_DENSITY_kN_m3) * deck_width / n
          if deck_t else 0.0)

    # ── DW: wearing course / surfacing ─────────────────────────────────────
    wc_t   = _f(KEY_WC_THICKNESS)                 # mm
    wc_rho = _f(KEY_WC_DENSITY)
    if wc_t:
        wc_kw = {} if wc_rho is None else {"density_kN_m3": wc_rho}
        dw = wearing_course_dead_load_kN_m2(wc_t / 1000.0, **wc_kw) * deck_width / n
    else:
        dw = 0.0

    # ── SIDL: footpath (×2) + crash barriers (×2) + railings (×2) + median ──
    fp_w     = _f(KEY_TS_FOOTPATH_WIDTH)
    footpath = (footpath_dead_load_kN_m2() * 2 * fp_w / n) if fp_w else 0.0
    barrier  = (_f(KEY_CB_LOAD, 0.0) * 2) / n
    railing  = (_f(KEY_RL_LOAD_VALUE, 0.0) * 2) / n
    median   = (_f(KEY_MD_LOAD, 0.0)) / n

    total = sw + dd + dw + footpath + barrier + railing + median

    return {
        "id":    "permanent_load_summary",
        "label": "Permanent Load Summary",
        "columns": [
            "Dead Load, DL (kN/m)",
        ],
        "rows": [
            [round(total, 3)],
        ],
    }


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
    # Braking load is derived from the selected vehicle class (IRC 6 Cl. 211.2):
    # a class's braking row is "Yes" when that vehicle is selected — except
    # Class SV, which is an independent opt-in with its own key.
    BREAKING_LOAD_KEYS = [
        ("Breaking Load : Class A",           KEY_LL_IRC_CLASS_A),
        ("Breaking Load : Class AA Wheeled",  KEY_LL_IRC_AA_WHEELED),
        ("Breaking Load : Class AA Tracked",  KEY_LL_IRC_AA_TRACKED),
        ("Breaking Load : Class 70R Wheeled", KEY_LL_IRC_70R_WHEELED),
        ("Breaking Load : Class 70R Tracked", KEY_LL_IRC_70R_TRACKED),
        ("Breaking Load : Class 70R Bogie",   KEY_LL_IRC_70R_BOGIE),
        ("Breaking Load : Class SV",          KEY_BL_IRC_CLASS_SV),
        ("Breaking Load : Class Fatigue",     KEY_LL_IRC_CLASS_FATIGUE),
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

    # Eccentricity is a value (m), not a Yes/No selection.
    ecc = input_dict.get(KEY_LL_ECCENTRICITY)
    rows.append([
        "Breaking Load : Eccentricity from top of Deck (m)",
        _num(ecc) if _has(ecc) else EMPTY,
    ])

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
    if not _has(zone):
        # Fall back to the project-location weather data directly.
        zone = _weather_value(input_dict, "zone")
    # Fall back to the IRC/schema defaults (mirrors defaults._update_loading_tab_defaults)
    # so the table still shows standard values if the loading defaults were never
    # seeded into this session's input_dict.
    importance        = input_dict.get(KEY_SL_IMPORTANCE_FACTOR)  or "1.0"
    soil_type         = input_dict.get(KEY_SL_SOIL_TYPE)          or "Type I – Rocky or Hard"
    time_period       = input_dict.get(KEY_SL_TIME_PERIOD)        or "0.5"
    damping           = input_dict.get(KEY_SL_DAMPING)            or "2"
    response_red      = input_dict.get(KEY_SL_RESPONSE_REDUCTION) or "1"

    # ── Computed coefficients ─────────────────────────────────────────────
    zone_factor       = input_dict.get(KEY_SL_ZONE_FACTOR)
    spectral_coeff    = input_dict.get(KEY_SL_SPECTRAL_COEFF)
    horizontal_coeff  = input_dict.get(KEY_SL_HORIZONTAL_COEFF)
    vertical_coeff    = input_dict.get(KEY_SL_VERTICAL_COEFF)

    # Recompute (Z, Sₐ/g, Aₕ, Aᵥ) when absent — mirrors the UI's
    # _compute_seismic_values so the table populates without the UI compute
    # having run. Needs a valid seismic zone (synced from the project location).
    if (not _has(zone_factor) or not _has(spectral_coeff)
            or not _has(horizontal_coeff) or not _has(vertical_coeff)):
        try:
            from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
            zmap = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V"}
            z = str(zone).strip().upper()
            if z.isdigit():
                z = zmap.get(z)
            smap = {
                "Type I – Rocky or Hard": 1,
                "Type II – Medium Soil":  2,
                "Type III – Soft Soil":   3,
            }
            st = smap.get(str(soil_type), 1)
            dl_v = input_dict.get(KEY_SL_DEAD_LOAD_VALUE)
            ll_v = input_dict.get(KEY_SL_LIVE_LOAD_VALUE)
            dead_kN = float(dl_v) if (str(input_dict.get(KEY_SL_DEAD_LOAD_MODE)) == "Custom" and dl_v) else 0.0
            live_kN = float(ll_v) if (str(input_dict.get(KEY_SL_LIVE_LOAD_MODE)) == "Custom" and ll_v) else 0.0
            res = IRC6_2017.cl_218_5_1(
                zone=f"Zone {z}", soil_type=st,
                dead_load_kN=dead_kN, live_load_kN=live_kN,
                period_T=float(time_period) if time_period else None,
                damping_percent=float(damping) if damping else 5.0,
            )
            if not _has(zone_factor):
                zone_factor = res.get("Z")
            if not _has(spectral_coeff):
                spectral_coeff = res.get("Sa_g_adjusted")
            if not _has(horizontal_coeff):
                horizontal_coeff = res.get("Ah")
            if not _has(vertical_coeff) and res.get("Ah") is not None:
                vertical_coeff = round(res.get("Ah") * 2 / 3, 4)
        except Exception:
            pass

    # ── Dead load for seismic: mode + value ───────────────────────────────
    dl_mode  = input_dict.get(KEY_SL_DEAD_LOAD_MODE) or "Automatic"
    dl_value = input_dict.get(KEY_SL_DEAD_LOAD_VALUE)
    if _has(dl_mode) and str(dl_mode).lower() == "automatic":
        dl_display = "Automatic"
    elif _has(dl_value):
        dl_display = _num(dl_value)
    else:
        dl_display = EMPTY

    # ── Live load for seismic: mode + value ───────────────────────────────
    ll_mode  = input_dict.get(KEY_SL_LIVE_LOAD_MODE) or "Automatic"
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
    if not _has(basic_wind_speed):
        # Fall back to the project-location weather data directly.
        basic_wind_speed = _weather_value(input_dict, "wind_speed")
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

    # ── Computed values (Vz, Pz) ──────────────────────────────────────────
    # Prefer the stored computed values; if absent, recompute self-contained
    # from Vb / H / terrain (same IRC 6 Table 12 the UI compute uses) so the
    # columns populate without depending on the UI compute having run.
    hourly_mean_wind    = input_dict.get(KEY_WL_HOURLY_MEAN_WIND)
    hourly_wind_pressure = input_dict.get(KEY_WL_HOURLY_WIND_PRESSURE)
    if not _has(hourly_mean_wind) or not _has(hourly_wind_pressure):
        try:
            from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
            terrain = {
                "Plain Terrain": "plain",
                "Terrain with Obstructions": "obstructed",
            }.get(str(terrain_type).strip(), "plain")
            res = IRC6_2017.table_12(float(avg_exposed_height), terrain, float(basic_wind_speed))
            if not _has(hourly_mean_wind):
                hourly_mean_wind = res.get("Vz")
            if not _has(hourly_wind_pressure):
                hourly_wind_pressure = res.get("Pz")
        except Exception:
            pass

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
    All values come from the Loading tab (self-contained, no analysis needed):
      • Highest/lowest air temp — synced from the project location.
      • Thermal coefficients (steel/RCC) — Loading-tab inputs (IRC default 12e-6).
      • Effective bridge temps + design rise/fall — recomputed per IRC 6 Cl. 215.2.
    """
    # ── User inputs (fall back to project-location weather + IRC defaults) ──
    highest_max_temp = input_dict.get(KEY_TL_HIGHEST_MAX_TEMP)
    if not _has(highest_max_temp):
        highest_max_temp = _weather_value(input_dict, "max_temp")
    lowest_min_temp = input_dict.get(KEY_TL_LOWEST_MIN_TEMP)
    if not _has(lowest_min_temp):
        lowest_min_temp = _weather_value(input_dict, "min_temp")

    thermal_coeff_steel = input_dict.get(KEY_TL_THERMAL_COEFF_STEEL) or "12.0e-6"
    thermal_coeff_rcc   = input_dict.get(KEY_TL_THERMAL_COEFF_RCC)   or "12.0e-6"

    # ── Computed values — recompute from air temps when absent ─────────────
    bridge_temp_min = input_dict.get(KEY_TL_BRIDGE_TEMP_MIN)
    bridge_temp_max = input_dict.get(KEY_TL_BRIDGE_TEMP_MAX)
    temp_rise       = input_dict.get(KEY_TL_TEMP_RISE)
    temp_fall       = input_dict.get(KEY_TL_TEMP_FALL)

    if (not _has(bridge_temp_min) or not _has(bridge_temp_max)
            or not _has(temp_rise) or not _has(temp_fall)):
        try:
            from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
            res = IRC6_2017.cl_215_2_effective_bridge_temperature(
                float(highest_max_temp), float(lowest_min_temp), 'metallic', False)
            t_min = res.get('T_min', 0)
            t_max = res.get('T_max', 0)
            mean  = (t_max + t_min) / 2.0
            if not _has(bridge_temp_min):
                bridge_temp_min = t_min
            if not _has(bridge_temp_max):
                bridge_temp_max = t_max
            if not _has(temp_rise):
                temp_rise = t_max - mean
            if not _has(temp_fall):
                temp_fall = mean - t_min
        except Exception:
            pass

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
            _num(highest_max_temp)    if _has(highest_max_temp)    else EMPTY,
            _num(lowest_min_temp)     if _has(lowest_min_temp)     else EMPTY,
            _num(thermal_coeff_steel, decimals=8) if _has(thermal_coeff_steel) else EMPTY,
            _num(thermal_coeff_rcc,   decimals=8) if _has(thermal_coeff_rcc)   else EMPTY,
            _num(bridge_temp_min)     if _has(bridge_temp_min)     else EMPTY,
            _num(bridge_temp_max)     if _has(bridge_temp_max)     else EMPTY,
            _num(temp_rise)           if _has(temp_rise)           else EMPTY,
            _num(temp_fall)           if _has(temp_fall)           else EMPTY,
        ]],
    }

def resolve_load_combinations(input_dict: dict, bridge=None) -> dict | None:
    """
    Load combinations table — sourced entirely from the Loading tab.

    IRC 6 default combinations are stored by LoadCombinationWidget as a list under
    'irc6_default_combinations' (each {name: "<label> : <expr>", included, key, expr});
    user-defined ones under KEY_LC_COMBINATIONS (each {name, included, items}).
    'Selected' reflects each combination's included checkbox. Falls back to the
    standard IRC 6 set (all included) when the list hasn't been built yet.
    """

    def _yesno(raw) -> str:
        selected = (
            raw is True
            or str(raw).strip().lower() in ("true", "yes", "1", "checked")
        )
        return "Yes" if selected else "No"

    rows = []

    # ── IRC 6 default combinations (the list the widget persists) ──────────
    combos = input_dict.get("irc6_default_combinations")
    if combos:
        for c in combos:
            if not isinstance(c, dict):
                continue
            name = str(c.get("name", ""))
            if " : " in name:
                label, expr = name.split(" : ", 1)
            else:
                label, expr = name, str(c.get("expr", ""))
            rows.append([label, _val(expr), _yesno(c.get("included"))])
    else:
        # Fallback: standard IRC 6 set, all included (matches the widget's
        # default_checked state) so the table still populates.
        DEFAULTS = [
            ("basic_1", "1.35DL + 1.75DW + 1.5LL + 0.9WL + 0.9TL"),
            ("basic_2", "1.0DL + 1.0DW + 1.5LL + 0.9WL + 0.9TL"),
            ("basic_3", "1.35DL + 1.75DW + 1.15LL + 1.5WL + 0.9TL"),
            ("basic_4", "1.0DL + 1.0DW + 1.15LL + 1.5WL + 0.9TL"),
            ("basic_5", "1.35DL + 1.75DW + 1.15LL + 0.9WL + 1.5TL"),
            ("basic_6", "1.0DL + 1.0DW + 1.15LL + 0.9WL + 1.5TL"),
            ("accidental_1", "1.0DL + 1.0DW + 0.75LL + 0.5TL + 1.0VC"),
            ("accidental_2", "1.0DL + 1.0DW + 0.75LL + 0.5TL + 1.0BI"),
            ("accidental_3", "1.0DL + 1.0DW + 0.75LL + 0.5TL + 1.0FB"),
            ("seismic_1", "1.35DL + 1.75DW + 0.2LL + 0.5TL + 1.5EL"),
            ("seismic_2", "1.0DL + 1.0DW + 0.2LL + 0.5TL + 1.5EL"),
            ("seismic_3", "1.35DL + 1.75DW + 0.2LL + 0.5TL + 0.75EL"),
            ("seismic_4", "1.0DL + 1.0DW + 0.2LL + 0.5TL + 0.75EL"),
            ("rare_1", "1.0DL + 1.2DW + 1.0LL + 0.6WL + 0.6TL"),
            ("rare_2", "1.0DL + 1.0DW + 1.0LL + 0.6WL + 0.6TL"),
            ("rare_3", "1.0DL + 1.2DW + 0.75LL + 1.0WL + 0.6TL"),
            ("rare_4", "1.0DL + 1.0DW + 0.75LL + 1.0WL + 0.6TL"),
            ("rare_5", "1.0DL + 1.2DW + 0.75LL + 0.6WL + 1.0TL"),
            ("rare_6", "1.0DL + 1.0DW + 0.75LL + 0.6WL + 1.0TL"),
            ("frequent_1", "1.0DL + 1.2DW + 0.75LL + 0.5WL + 0.5TL"),
            ("frequent_2", "1.0DL + 1.0DW + 0.75LL + 0.5WL + 0.5TL"),
            ("frequent_3", "1.0DL + 1.2DW + 0.2LL + 0.6WL + 0.5TL"),
            ("frequent_4", "1.0DL + 1.0DW + 0.2LL + 0.6WL + 0.5TL"),
            ("frequent_5", "1.0DL + 1.2DW + 0.2LL + 0.5WL + 0.6TL"),
            ("frequent_6", "1.0DL + 1.0DW + 0.2LL + 0.5WL + 0.6TL"),
            ("quasi_permanent_1", "1.0DL + 1.2DW + 0.5TL"),
            ("quasi_permanent_2", "1.0DL + 1.0DW + 0.5TL"),
        ]
        rows = [[name, expr, "Yes"] for name, expr in DEFAULTS]

    # ── User-defined custom combinations (if any) ──────────────────────────
    for c in (input_dict.get(KEY_LC_COMBINATIONS) or []):
        if not isinstance(c, dict):
            continue
        label = str(c.get("name", "Custom"))
        items = c.get("items") or []
        expr  = " + ".join(
            f"{i.get('factor', '')}{i.get('case', '')}"
            for i in items if isinstance(i, dict)
        )
        rows.append([label, _val(expr), _yesno(c.get("included"))])

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

def _defl_ur(defl_mm, limit_val):
    """Compute utilization ratio for deflection; returns (ur_rounded, status) or (EMPTY, EMPTY)."""
    try:
        ur = round(float(defl_mm) / float(limit_val), 3)
        return ur, ("PASS" if ur <= 1.0 else "FAIL")
    except Exception:
        return EMPTY, EMPTY


def resolve_deflection_live_load(input_dict: dict, bridge=None) -> dict | None:
    span      = input_dict.get(KEY_SPAN)
    n_girders = input_dict.get(KEY_TS_NO_OF_GIRDERS)

    if not _has(n_girders):
        return None
    try:
        n = int(n_girders)
    except Exception:
        return None

    limit_val = None
    limit_str = EMPTY
    if _has(span):
        try:
            limit_val = float(span) * 1000.0 / 800.0
            limit_str = f"L/800 = {round(limit_val, 1)} mm"
        except Exception:
            pass

    defl_cache = getattr(bridge, "_deflections_cache", {}) if bridge else {}

    rows = []
    for i in range(1, n + 1):
        girder = f"G{i}"
        live_mm = defl_cache.get(girder, {}).get("live_mm")
        ur, status = _defl_ur(live_mm, limit_val) if (live_mm is not None and limit_val) else (EMPTY, EMPTY)
        rows.append([
            girder,
            _num(live_mm) if live_mm is not None else EMPTY,
            limit_str,
            ur,
            status,
        ])

    return {
        "id":    "deflection_live_load",
        "label": "Deflection - Live Load",
        "columns": [
            "Girder",
            "Deflection due to Live Load, δ_ₗᵢᵥₑ (mm)",
            "Permissible Limit",
            "Utilization Ratio",
            "Status",
        ],
        "rows": rows,
    }


def resolve_deflection_total_load(input_dict: dict, bridge=None) -> dict | None:
    span      = input_dict.get(KEY_SPAN)
    n_girders = input_dict.get(KEY_TS_NO_OF_GIRDERS)

    if not _has(n_girders):
        return None
    try:
        n = int(n_girders)
    except Exception:
        return None

    limit_val = None
    limit_str = EMPTY
    if _has(span):
        try:
            limit_val = float(span) * 1000.0 / 600.0
            limit_str = f"L/600 = {round(limit_val, 1)} mm"
        except Exception:
            pass

    defl_cache = getattr(bridge, "_deflections_cache", {}) if bridge else {}

    rows = []
    for i in range(1, n + 1):
        girder = f"G{i}"
        total_mm = defl_cache.get(girder, {}).get("total_mm")
        ur, status = _defl_ur(total_mm, limit_val) if (total_mm is not None and limit_val) else (EMPTY, EMPTY)
        rows.append([
            girder,
            _num(total_mm) if total_mm is not None else EMPTY,
            limit_str,
            ur,
            status,
        ])

    return {
        "id":    "deflection_total_load",
        "label": "Deflection - Total Load",
        "columns": [
            "Girder",
            "Total Deflection, δₜₒₜₐₗ (mm)",
            "Permissible Limit",
            "Utilization Ratio",
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


def _get_uls_per_girder(bridge) -> dict:
    """Return design_results[KEY_SD_ULS_PER_GIRDER], or {} if unavailable."""
    if bridge is None:
        return {}
    try:
        return (getattr(bridge, "output_dict", {}).get("design_results") or {}).get(KEY_SD_ULS_PER_GIRDER) or {}
    except Exception:
        return {}


def _uls_check_rows(bridge, category: str) -> list | None:
    """Return ordered (girder_label, demand, capacity, ur, status) rows for one check category.

    Girder order comes from _load_effects_cache (EB-filtered); each row gets
    the per-girder values stored by _build_uls_per_girder in the designer.
    Returns None if the data is not available yet.
    """
    uls_pg = _get_uls_per_girder(bridge)
    cat_data = uls_pg.get(category)
    if not cat_data:
        return None

    cache = getattr(bridge, "_load_effects_cache", None) or {}
    girder_names = sorted(cache.keys()) if cache else sorted(cat_data.keys())

    rows = []
    for g in girder_names:
        g_chk = cat_data.get(g)
        if g_chk is None:
            rows.append([f"{g}M1", EMPTY, EMPTY, EMPTY, EMPTY])
        else:
            rows.append([
                f"{g}M1",
                _num(g_chk["demand"]),
                _num(g_chk["capacity"]),
                _num(g_chk["ur"]),
                g_chk.get("status", EMPTY),
            ])
    return rows if rows else None


def resolve_flexural_resistance_check(input_dict: dict, bridge=None) -> dict | None:
    rows = _uls_check_rows(bridge, "flexure")
    if rows is None:
        return None
    return {
        "id":    "flexural_resistance_check",
        "label": "Flexural Resistance Check",
        "columns": [
            "Girder",
            "Design Moment, Mᵈ (kNm)",
            "Moment Resistance, Mᵣ (kNm)",
            "Utilization Ratio",
            "Status",
        ],
        "rows": rows,
    }


def resolve_shear_resistance_check(input_dict: dict, bridge=None) -> dict | None:
    rows = _uls_check_rows(bridge, "shear")
    if rows is None:
        return None
    return {
        "id":    "shear_resistance_check",
        "label": "Shear Resistance Check",
        "columns": [
            "Girder",
            "Design Shear, Vᵈ (kN)",
            "Shear Resistance, Vᵣ (kN)",
            "Utilization Ratio",
            "Status",
        ],
        "rows": rows,
    }


def resolve_bending_shear_interaction_check(input_dict: dict, bridge=None) -> dict | None:
    rows = _uls_check_rows(bridge, "interaction")
    if rows is None:
        return None
    return {
        "id":    "bending_shear_interaction_check",
        "label": "Bending-Shear Interaction Check",
        "columns": [
            "Girder",
            "Design Moment, Mᵈ (kNm)",
            "Reduced Resistance, Mᵈᵥ (kNm)",
            "Utilization Ratio",
            "Status",
        ],
        "rows": rows,
    }


def resolve_lateral_torsional_buckling_check(input_dict: dict, bridge=None) -> dict | None:
    rows = _uls_check_rows(bridge, "ltb")
    if rows is None:
        return None
    return {
        "id":    "lateral_torsional_buckling_check",
        "label": "Lateral Torsional Buckling Check - Construction Stage",
        "columns": [
            "Girder",
            "Design Moment, Mᵈ (kNm)",
            "LTB Resistance, Mᵦ (kNm)",
            "Utilization Ratio",
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
    rows = _uls_check_rows(bridge, "fatigue")
    if rows is None:
        return None
    return {
        "id":    "fatigue_assessment_girder",
        "label": "Fatigue Assessment - Girder",
        "columns": [
            "Girder",
            "Stress Range, Δσ (MPa)",
            "Fatigue Limit, ffd (MPa)",
            "Utilization Ratio",
            "Status",
        ],
        "rows": rows,
    }


# ── Resolvers — Shear Connector (all 5 tables) ───────────────────────────────

def _get_sc_dr(bridge) -> dict:
    """Return design_results dict, or {} if design not yet run."""
    if bridge is None:
        return {}
    try:
        return getattr(bridge, "output_dict", {}).get("design_results") or {}
    except Exception:
        return {}


def _sc_girder_rows(input_dict, bridge) -> int | None:
    """Return the number of non-EB girder rows for shear connector tables."""
    n_girders = input_dict.get(KEY_TS_NO_OF_GIRDERS)
    if not _has(n_girders):
        return None
    return _uls_girder_rows(n_girders)


def resolve_shear_connector_capacity(input_dict: dict, bridge=None) -> dict | None:
    n = _sc_girder_rows(input_dict, bridge)
    if n is None:
        return None

    diameter = input_dict.get(KEY_DS_STUD_DIAMETER)
    height   = input_dict.get(KEY_DS_STUD_HEIGHT)
    fu_stud  = input_dict.get(KEY_DS_STUD_ULTIMATE_STRENGTH)
    count    = input_dict.get(KEY_DS_STUD_COUNT)

    fck = EMPTY
    ecm = EMPTY
    try:
        cp  = bridge._build_material_props().concrete_prop
        fck = _num(cp.fck)
        ecm = _num(cp.Ecm)
    except Exception:
        pass

    dr     = _get_sc_dr(bridge)
    Qu     = _num(dr.get(KEY_SD_SC_Qu_kN)) if dr.get(KEY_SD_SC_Qu_kN) is not None else EMPTY
    n_stud = _val(count) if _has(count) else EMPTY
    try:
        sum_Qd = _num(float(dr[KEY_SD_SC_Qu_kN]) * int(count)) if (dr.get(KEY_SD_SC_Qu_kN) and _has(count)) else EMPTY
    except Exception:
        sum_Qd = EMPTY
    clause = (dr.get("capacity_details") or {}).get("stud_capacity", {}).get("clause") or "IRC 22 Cl. 606.3.1"

    rows = [
        [
            f"Girder {i}",
            _num(diameter) if _has(diameter) else EMPTY,
            _num(height)   if _has(height)   else EMPTY,
            _num(fu_stud)  if _has(fu_stud)  else EMPTY,
            fck,
            ecm,
            Qu,
            Qu,       # Qd = Qu (formula already includes γv)
            n_stud,
            sum_Qd,
            clause,
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


def resolve_shear_connector_spacing_uls(input_dict: dict, bridge=None) -> dict | None:
    n = _sc_girder_rows(input_dict, bridge)
    if n is None:
        return None

    count = input_dict.get(KEY_DS_STUD_COUNT)
    dr    = _get_sc_dr(bridge)

    VL    = _num(dr[KEY_SD_SC_VL])      if dr.get(KEY_SD_SC_VL)  is not None else EMPTY
    Qu    = dr.get(KEY_SD_SC_Qu_kN)
    try:
        sum_Qd = _num(float(Qu) * int(count)) if (Qu is not None and _has(count)) else EMPTY
    except Exception:
        sum_Qd = EMPTY
    SL1   = _num(dr[KEY_SD_SC_SL1])     if dr.get(KEY_SD_SC_SL1) is not None else EMPTY
    H     = _num(dr[KEY_SD_SC_H_kN])    if dr.get(KEY_SD_SC_H_kN) is not None else EMPTY
    SL2   = _num(dr[KEY_SD_SC_SL2])     if dr.get(KEY_SD_SC_SL2) is not None else EMPTY
    try:
        sl1_v = float(dr[KEY_SD_SC_SL1]) if dr.get(KEY_SD_SC_SL1) else None
        sl2_v = float(dr[KEY_SD_SC_SL2]) if dr.get(KEY_SD_SC_SL2) else None
        min_sl = _num(min(v for v in [sl1_v, sl2_v] if v is not None)) if any(v is not None for v in [sl1_v, sl2_v]) else EMPTY
    except Exception:
        min_sl = EMPTY
    cd     = (dr.get("capacity_details") or {})
    clause = cd.get("stud_spacing", {}).get("clause") or "IRC 22 Cl. 606.4.1"

    rows = [
        [f"Girder {i}", VL, sum_Qd, SL1, H, SL2, min_sl, clause]
        for i in range(1, n + 1)
    ]

    return {
        "id":    "shear_connector_spacing_uls",
        "label": "Shear Connector Spacing - ULS Strength",
        "columns": [
            "Girder",
            "Design Vertical Shear, VL (kN)",
            "Total Stud Capacity, ΣQd (kN)",
            "Spacing from Vertical Shear, SL1 (mm)",
            "Full Shear Connection Force, H (kN)",
            "Spacing from Full Shear Force, SL2 (mm)",
            "Governing ULS Spacing, min(SL1, SL2) (mm)",
            "Clause Reference",
        ],
        "rows": rows,
    }


def resolve_shear_connector_spacing_fatigue(input_dict: dict, bridge=None) -> dict | None:
    n = _sc_girder_rows(input_dict, bridge)
    if n is None:
        return None

    count = input_dict.get(KEY_DS_STUD_COUNT)
    dr    = _get_sc_dr(bridge)

    Vr     = _num(dr[KEY_SD_SC_Vr_kN])  if dr.get(KEY_SD_SC_Vr_kN) is not None else EMPTY
    Qr     = _num(dr[KEY_SD_SC_Qr_kN])  if dr.get(KEY_SD_SC_Qr_kN) is not None else EMPTY
    n_stud = _val(count) if _has(count) else EMPTY
    SR     = _num(dr[KEY_SD_SC_SR])      if dr.get(KEY_SD_SC_SR)    is not None else EMPTY
    cd     = (dr.get("capacity_details") or {})
    clause = cd.get("stud_spacing_fatigue", {}).get("clause") or "IRC 22 Cl. 606.4.2"

    rows = [
        [f"Girder {i}", Vr, Qr, n_stud, SR, clause]
        for i in range(1, n + 1)
    ]

    return {
        "id":    "shear_connector_spacing_fatigue",
        "label": "Shear Connector Spacing - Fatigue",
        "columns": [
            "Girder",
            "Fatigue Shear Range, Vr (kN)",
            "Fatigue Capacity per Stud, Qr (kN)",
            "No. of Studs per Section",
            "Fatigue Governing Spacing, SR (mm)",
            "Clause Reference",
        ],
        "rows": rows,
    }


def resolve_governing_shear_connector_spacing(input_dict: dict, bridge=None) -> dict | None:
    n = _sc_girder_rows(input_dict, bridge)
    if n is None:
        return None

    dr = _get_sc_dr(bridge)
    if not dr:
        return None

    try:
        sl1 = float(dr[KEY_SD_SC_SL1]) if dr.get(KEY_SD_SC_SL1) else None
        sl2 = float(dr[KEY_SD_SC_SL2]) if dr.get(KEY_SD_SC_SL2) else None
        sl  = min(v for v in [sl1, sl2] if v is not None) if any(v is not None for v in [sl1, sl2]) else None
    except Exception:
        sl = None
    SL     = _num(sl) if sl is not None else EMPTY
    SR     = _num(dr[KEY_SD_SC_SR])           if dr.get(KEY_SD_SC_SR)           is not None else EMPTY
    gov    = _num(dr.get("stud_spacing_governing_mm")) if dr.get("stud_spacing_governing_mm") else EMPTY
    lim600 = _num(dr[KEY_SD_SC_LIMIT_600])    if dr.get(KEY_SD_SC_LIMIT_600)    is not None else 600
    lim3t  = _num(dr[KEY_SD_SC_LIMIT_3TSLAB]) if dr.get(KEY_SD_SC_LIMIT_3TSLAB) is not None else EMPTY
    lim4h  = _num(dr[KEY_SD_SC_LIMIT_4HSTUD]) if dr.get(KEY_SD_SC_LIMIT_4HSTUD) is not None else EMPTY
    adopted = _num(dr.get("stud_spacing_max_mm")) if dr.get("stud_spacing_max_mm") else EMPTY
    try:
        prov = float(dr.get("stud_spacing_provided_mm") or 0)
        maxs = float(dr.get("stud_spacing_max_mm") or 0)
        status = "PASS" if (maxs > 0 and prov <= maxs) else ("FAIL" if maxs > 0 else EMPTY)
    except Exception:
        status = EMPTY

    rows = [
        [f"Girder {i}", SL, SR, gov, lim600, lim3t, lim4h, adopted, status]
        for i in range(1, n + 1)
    ]

    return {
        "id":    "governing_shear_connector_spacing",
        "label": "Governing Shear Connector Spacing",
        "columns": [
            "Girder",
            "ULS Spacing, SL (mm)",
            "Fatigue Spacing, SR (mm)",
            "Governing Spacing, min(SL, SR) (mm)",
            "Max Permissible — 600 mm",
            "Max Permissible — 3·t_slab (mm)",
            "Max Permissible — 4·h_stud (mm)",
            "Adopted Permissible Limit (mm)",
            "Status",
        ],
        "rows": rows,
    }


def resolve_shear_connector_detailing_checks(input_dict: dict, bridge=None) -> dict | None:
    n = _sc_girder_rows(input_dict, bridge)
    if n is None:
        return None

    diameter = input_dict.get(KEY_DS_STUD_DIAMETER)
    height   = input_dict.get(KEY_DS_STUD_HEIGHT)
    dr       = _get_sc_dr(bridge)

    d      = _num(diameter) if _has(diameter) else EMPTY
    h      = _num(height)   if _has(height)   else EMPTY
    tf     = _num(float(dr[KEY_SD_SC_D_LIMIT]) / 2.0) if dr.get(KEY_SD_SC_D_LIMIT) else EMPTY
    d_lim  = _num(dr[KEY_SD_SC_D_LIMIT])   if dr.get(KEY_SD_SC_D_LIMIT)   is not None else EMPTY
    h_min  = _num(dr[KEY_SD_SC_H_MIN])     if dr.get(KEY_SD_SC_H_MIN)     is not None else EMPTY
    e_dist = _num(dr[KEY_SD_SC_EDGE_DIST]) if dr.get(KEY_SD_SC_EDGE_DIST) is not None else EMPTY
    e_req  = _num(dr[KEY_SD_SC_REQ_EDGE_DIST]) if dr.get(KEY_SD_SC_REQ_EDGE_DIST) is not None else 25
    cover  = _num(dr[KEY_SD_SC_CLEAR_COVER])   if dr.get(KEY_SD_SC_CLEAR_COVER)   is not None else EMPTY
    c_req  = _num(dr[KEY_SD_SC_REQ_CLEAR_COVER]) if dr.get(KEY_SD_SC_REQ_CLEAR_COVER) is not None else 25
    cd     = (dr.get("capacity_details") or {})
    clause = cd.get("stud_detailing", {}).get("clause") or "IRC 22 Cl. 606.6"
    status = ("PASS" if dr.get("stud_detailing_ok") else "FAIL") if "stud_detailing_ok" in dr else EMPTY

    rows = [
        [f"Girder {i}", d, tf, d_lim, h, h_min, e_dist, e_req, cover, c_req, clause, status]
        for i in range(1, n + 1)
    ]

    return {
        "id":    "shear_connector_detailing_checks",
        "label": "Shear Connector Detailing Checks",
        "columns": [
            "Girder",
            "Stud Diameter, d (mm)",
            "Flange Thickness, tf (mm)",
            "d ≤ 2·tf Check (mm)",
            "Stud Height, h (mm)",
            "h ≥ 4·d Check (mm)",
            "Longitudinal Edge Distance (mm)",
            "Min. Edge Distance Required (mm)",
            "Slab Embedment Above Stud (mm)",
            "Min. Embedment Required (mm)",
            "Clause Reference",
            "Status",
        ],
        "rows": rows,
    }


# ── Resolvers — Crack Width Check (partial) ───────────────────────────────────

def resolve_transverse_shear_check(input_dict: dict, bridge=None) -> dict | None:
    n = _sc_girder_rows(input_dict, bridge)
    if n is None:
        return None

    dr = _get_sc_dr(bridge)
    if not dr:
        return None

    VL    = _num(dr[KEY_SD_TS_VL])         if dr.get(KEY_SD_TS_VL)         is not None else EMPTY
    Vc    = _num(dr[KEY_SD_TS_VCAP_CONC])  if dr.get(KEY_SD_TS_VCAP_CONC)  is not None else EMPTY
    Vs    = _num(dr[KEY_SD_TS_VCAP_REINF]) if dr.get(KEY_SD_TS_VCAP_REINF) is not None else EMPTY
    VRd   = _num(dr[KEY_SD_TS_VRD])        if dr.get(KEY_SD_TS_VRD)        is not None else EMPTY
    try:
        dcr = _num(float(dr[KEY_SD_TS_VL]) / float(dr[KEY_SD_TS_VRD]), 3)
    except Exception:
        dcr = EMPTY
    cd     = (dr.get("capacity_details") or {})
    clause = cd.get("transverse_shear", {}).get("clause") or "IRC 22 Cl. 606.10"
    status = ("PASS" if dr.get("transverse_shear_ok") else "FAIL") if "transverse_shear_ok" in dr else EMPTY

    rows = [
        [f"Girder {i}", VL, Vc, Vs, VRd, dcr, clause, status]
        for i in range(1, n + 1)
    ]

    return {
        "id":    "transverse_shear_check",
        "label": "Transverse Shear Check in Concrete Slab",
        "columns": [
            "Girder",
            "Design Longitudinal Shear per Unit Length, VL (kN/m)",
            "Concrete Shear Resistance (kN/m)",
            "Concrete + Reinforcement Shear Resistance (kN/m)",
            "Total Shear Resistance, VRd (kN/m)",
            "Utilization Ratio",
            "Clause Reference",
            "Status",
        ],
        "rows": rows,
    }


def resolve_crack_width_check(input_dict: dict, bridge=None) -> dict | None:
    dd = _get_deck_design(bridge)
    wk_bot = dd.get(KEY_DD_CRACK_WK_BOTTOM)
    wk_top = dd.get(KEY_DD_CRACK_WK_TOP)
    if wk_bot is None and wk_top is None:
        return None

    wk_lim = dd.get(KEY_DD_CRACK_WK_LIMIT)
    dr      = _get_sc_dr(bridge)
    as_min  = _num(dr[KEY_SD_CRACK_AS_MIN])  if dr.get(KEY_SD_CRACK_AS_MIN)  is not None else EMPTY
    as_prov = _num(dr[KEY_SD_CRACK_AS_PROV]) if dr.get(KEY_SD_CRACK_AS_PROV) is not None else EMPTY
    clause  = "IRC 112:2020 Cl. 12.3.4"

    def _face_row(label, wk, dia_key, spc_key):
        try:
            status = "PASS" if float(wk) <= float(wk_lim) else "FAIL"
        except Exception:
            status = EMPTY
        return [
            label,
            _num(wk, 4),
            _num(wk_lim),
            as_min,
            as_prov,
            _num(dd.get(dia_key)),
            _num(dd.get(spc_key)),
            clause,
            status,
        ]

    rows = [
        _face_row("Deck Slab (Bottom)", wk_bot, "rebar_bottom_dia", "rebar_bottom_spacing"),
        _face_row("Deck Slab (Top)",    wk_top, "rebar_top_dia",    "rebar_top_spacing"),
    ]

    return {
        "id":    "crack_width_check",
        "label": "Crack Width Check",
        "columns": [
            "Member",
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


# ── Resolvers — Design Results Summary ────────────────────────────────────────

def resolve_design_results_summary(input_dict: dict, bridge=None) -> dict | None:
    """One row per girder: the controlling check (highest UR among the 8 design
    checks, from envelope demands) plus the real load case / combination that
    drives that check (worst per-LC UR for the same check id, envelope
    pseudo-cases excluded)."""
    pg = _get_per_girder(bridge)
    if not pg:
        return None

    cache = getattr(bridge, "_load_effects_cache", None) or {}
    girder_names = sorted(cache.keys()) if cache else sorted(
        g for g in pg if not g.startswith("EB")
    )

    def _with_unit(value, unit):
        v = _num(value)
        if v == EMPTY:
            return EMPTY
        return f"{v} {unit}".strip() if unit and unit not in ("–", "-") else v

    rows = []
    for g in girder_names:
        g_data = pg.get(g) or {}
        checks = g_data.get("checks") or []
        if not checks:
            rows.append([f"{g}M1", EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY])
            continue

        ctrl = max(checks, key=lambda c: c.get("dcr") or 0.0)

        # Worst real LC for the controlling check id (skip Envelope pseudo-LCs)
        ctrl_lc, best_dcr = None, None
        for lc_name, lc_data in (g_data.get("per_lc") or {}).items():
            if str(lc_name).lower().startswith("envelope"):
                continue
            for chk in lc_data.get("checks") or []:
                if chk.get("id") == ctrl.get("check_id"):
                    d = chk.get("dcr") or 0.0
                    if best_dcr is None or d > best_dcr:
                        best_dcr, ctrl_lc = d, lc_name
        if ctrl_lc is None:
            ctrl_lc = (g_data.get("demand") or {}).get("governing_combination") or EMPTY

        rows.append([
            f"{g}M1",
            ctrl_lc,
            ctrl.get("name", EMPTY),
            _with_unit(ctrl.get("demand"),   ctrl.get("demand_unit")),
            _with_unit(ctrl.get("capacity"), ctrl.get("capacity_unit")),
            _num(ctrl.get("dcr"), 3),
            ctrl.get("status", EMPTY),
        ])

    if not rows:
        return None

    return {
        "id":    "design_results_summary",
        "label": "Design Results Summary",
        "columns": [
            "Member",
            "Controlling Load Case / Combination",
            "Controlling Design Check",
            "Demand",
            "Capacity",
            "Utilization Ratio",
            "Status",
        ],
        "rows": rows,
    }


def resolve_deck_slab_properties(input_dict: dict, bridge=None) -> dict | None:
    """
    Deck slab properties table.

    Primary source: bridge.output_dict["deck_design_results"] (after design_deck_slab()).
    Fallback:       input_dict for grade/thickness/overhang before design runs.
    """
    dd = {}
    if bridge is not None:
        try:
            dd = getattr(bridge, "output_dict", {}).get("deck_design_results") or {}
        except Exception:
            dd = {}

    def _dd(key):
        v = dd.get(key)
        return v if v not in (None, "", [], {}) else None

    grade     = _dd("deck_grade")     or _val(input_dict.get(KEY_DECK_CONCRETE_GRADE_BASIC))
    thickness = _dd("deck_thickness") or (_mm(input_dict.get(KEY_TS_DECK_THICKNESS)) if _has(input_dict.get(KEY_TS_DECK_THICKNESS)) else None)
    overhang_raw = _dd("deck_overhang")
    if overhang_raw is not None:
        try:
            overhang = round(float(overhang_raw) / 1000.0, 3)
        except Exception:
            overhang = None
    else:
        ov = input_dict.get(KEY_TS_DECK_OVERHANG)
        overhang = _num(ov) if _has(ov) else None

    top_fy   = _dd("rebar_top_yield")
    top_dia  = _dd("rebar_top_dia")
    top_spc  = _dd("rebar_top_spacing")
    top_cov  = _dd("rebar_top_cover")
    top_area = _dd("rebar_top_area")

    bot_fy   = _dd("rebar_bottom_yield")
    bot_dia  = _dd("rebar_bottom_dia")
    bot_spc  = _dd("rebar_bottom_spacing")
    bot_cov  = _dd("rebar_bottom_cover")
    bot_area = _dd("rebar_bottom_area")

    def _v(x):
        return _val(x) if x is not None else EMPTY

    return {
        "id":    "deck_slab_properties",
        "label": "Deck Slab Properties",
        "columns": [
            "Grade of Material",
            "Deck Thickness (mm)",
            "Deck Overhang (m)",
            "Top Layer - Material Strength (MPa)",
            "Top Layer - Diameter (mm)",
            "Top Layer - Spacing (mm)",
            "Top Layer - Clear Cover (mm)",
            "Top Layer - Area (mm²)",
            "Bottom Layer - Material Strength (MPa)",
            "Bottom Layer - Diameter (mm)",
            "Bottom Layer - Spacing (mm)",
            "Bottom Layer - Clear Cover (mm)",
            "Bottom Layer - Area (mm²)",
        ],
        "rows": [[
            _v(grade),
            _v(thickness),
            _v(overhang),
            _v(top_fy),
            _v(top_dia),
            _v(top_spc),
            _v(top_cov),
            _v(top_area),
            _v(bot_fy),
            _v(bot_dia),
            _v(bot_spc),
            _v(bot_cov),
            _v(bot_area),
        ]],
    }


# ── Resolvers — Stress Results ────────────────────────────────────────────────
# These resolvers read from bridge.output_dict["design_results"]["per_girder"]
# which is populated at design time.  per_girder keys: G1, G2, ...
# Each girder dict has "checks" (list with check_id 10/11/12) and
# "sls_fibre_stresses" (raw fbt_MPa / fbc_MPa from compute_sls_stresses).

def _get_per_girder(bridge):
    """Return per_girder dict from design_results, or {} if unavailable."""
    if bridge is None:
        return {}
    try:
        return (getattr(bridge, "output_dict", {}).get("design_results") or {}).get("per_girder") or {}
    except Exception:
        return {}


def _stress_ur(sigma, limit):
    """Return (ur_rounded, status) for a stress / allowable pair."""
    try:
        ur = round(float(sigma) / float(limit), 3)
        return ur, ("PASS" if ur <= 1.0 else "FAIL")
    except Exception:
        return EMPTY, EMPTY


def resolve_stress_results_steel(input_dict: dict, bridge=None) -> dict | None:
    if bridge is None:
        return None

    # Controlling-girder envelope-SLS steel stress + allowable — single source
    # of truth computed in the designer; one value for every girder/member row.
    dr = (getattr(bridge, "output_dict", {}).get("design_results") or {})
    sigma = dr.get(KEY_SD_STRESS_STEEL)
    limit = dr.get(KEY_SD_STRESS_STEEL_ALLOWABLE)
    if sigma is None or limit is None:
        return None

    ur, status = _stress_ur(sigma, limit)

    # Use _load_effects_cache keys — already EB-filtered and labelled G1…Gn
    cache = getattr(bridge, "_load_effects_cache", None) or {}
    if cache:
        girder_names = sorted(cache.keys())
    else:
        girder_names = [g for g in _get_per_girder(bridge).keys()
                        if not g.startswith("EB")]

    if not girder_names:
        return None

    rows = [[f"{g}M1", _num(sigma), _num(limit), ur, status] for g in girder_names]

    return {
        "id": "stress_steel_service",
        "label": "Stress in Structural Steel - Service",
        "columns": ["Member", "Steel Stress (MPa)", "Allowable Stress (MPa)", "Utilization Ratio", "Status"],
        "rows": rows,
    }


def _get_deck_design(bridge):
    """Return deck_design_results dict, or {} if unavailable."""
    if bridge is None:
        return {}
    try:
        return getattr(bridge, "output_dict", {}).get("deck_design_results") or {}
    except Exception:
        return {}


def resolve_stress_results_concrete(input_dict: dict, bridge=None) -> dict | None:
    dd = _get_deck_design(bridge)
    bot_c = dd.get(KEY_DD_STRESS_CONC_BOTTOM)
    top_c = dd.get(KEY_DD_STRESS_CONC_TOP)
    if bot_c is None and top_c is None:
        return None

    allow = dd.get(KEY_DD_STRESS_CONC_ALLOWABLE)
    bot_ur, bot_st = _stress_ur(bot_c, allow)
    top_ur, top_st = _stress_ur(top_c, allow)
    rows = [
        ["Deck Slab (Bottom)", _num(bot_c), _num(allow), bot_ur, bot_st],
        ["Deck Slab (Top)",    _num(top_c), _num(allow), top_ur, top_st],
    ]

    return {
        "id": "stress_concrete_service",
        "label": "Stress in Concrete Deck - Service",
        "columns": ["Member", "Concrete Stress (MPa)", "Allowable Stress (MPa)", "Utilization Ratio", "Status"],
        "rows": rows,
    }


def resolve_stress_results_reinforcement(input_dict: dict, bridge=None) -> dict | None:
    dd = _get_deck_design(bridge)
    bot_s = dd.get(KEY_DD_STRESS_REINF_BOTTOM)
    top_s = dd.get(KEY_DD_STRESS_REINF_TOP)
    if bot_s is None and top_s is None:
        return None

    allow = dd.get(KEY_DD_STRESS_REINF_ALLOWABLE)
    bot_ur, bot_st = _stress_ur(bot_s, allow)
    top_ur, top_st = _stress_ur(top_s, allow)
    rows = [
        ["Deck Slab (Bottom)", _num(bot_s), _num(allow), bot_ur, bot_st],
        ["Deck Slab (Top)",    _num(top_s), _num(allow), top_ur, top_st],
    ]

    return {
        "id": "stress_reinf_service",
        "label": "Stress in Reinforcement - Service",
        "columns": ["Member", "Rebar Stress (MPa)", "Allowable Stress (MPa)", "Utilization Ratio", "Status"],
        "rows": rows,
    }


# ── Resolvers — Analysis Results: Load Effects (Girder) ───────────────────────
# These resolvers read from bridge._load_effects_cache which is pre-computed
# once at the end of design() via PlateGirderBridge.compute_load_effects_cache().
# Cache structure: {girder: {load_case: {Mz_max, Mz_min, Vy_max, Vy_min}}}

def _get_cache(bridge):
    """Return the pre-computed load effects cache, or None if unavailable."""
    cache = getattr(bridge, "_load_effects_cache", None)
    return cache if cache else None


def resolve_bending_moment_envelope(input_dict: dict, bridge=None) -> dict | None:
    if bridge is None:
        return None
    try:
        cache = _get_cache(bridge)
        if cache is None:
            return None

        rows = []
        for girder, lc_data in cache.items():
            env_max = max((v["Mz_max"] for v in lc_data.values() if v.get("Mz_max") is not None), default=None)
            env_min = min((v["Mz_min"] for v in lc_data.values() if v.get("Mz_min") is not None), default=None)
            rows.append([
                girder,
                _num(env_max) if env_max is not None else EMPTY,
                _num(env_min) if env_min is not None else EMPTY,
            ])

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
        cache = _get_cache(bridge)
        if cache is None:
            return None

        rows = []
        for girder, lc_data in cache.items():
            env_max = max((v["Vy_max"] for v in lc_data.values() if v.get("Vy_max") is not None), default=None)
            env_min = min((v["Vy_min"] for v in lc_data.values() if v.get("Vy_min") is not None), default=None)
            rows.append([
                girder,
                _num(env_max) if env_max is not None else EMPTY,
                _num(env_min) if env_min is not None else EMPTY,
            ])

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
        cache = _get_cache(bridge)
        if cache is None:
            return None

        all_lcs = list(next(iter(cache.values())).keys())

        columns = ["Girder"]
        for lc in all_lcs:
            columns.append(f"{lc} - Max (kNm)")
            columns.append(f"{lc} - Min (kNm)")

        rows = []
        for girder, lc_data in cache.items():
            row = [girder]
            for lc in all_lcs:
                entry = lc_data.get(lc, {})
                row.append(_num(entry["Mz_max"]) if entry.get("Mz_max") is not None else EMPTY)
                row.append(_num(entry["Mz_min"]) if entry.get("Mz_min") is not None else EMPTY)
            rows.append(row)

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
        cache = _get_cache(bridge)
        if cache is None:
            return None

        all_lcs = list(next(iter(cache.values())).keys())

        columns = ["Girder"]
        for lc in all_lcs:
            columns.append(f"{lc} - Max (kN)")
            columns.append(f"{lc} - Min (kN)")

        rows = []
        for girder, lc_data in cache.items():
            row = [girder]
            for lc in all_lcs:
                entry = lc_data.get(lc, {})
                row.append(_num(entry["Vy_max"]) if entry.get("Vy_max") is not None else EMPTY)
                row.append(_num(entry["Vy_min"]) if entry.get("Vy_min") is not None else EMPTY)
            rows.append(row)

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
    "permanent_load_summary": resolve_permanent_load_summary,
    "live_load_definitions": resolve_live_load_definitions,
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
    "stress_steel_service":               resolve_stress_results_steel,
    "stress_concrete_service":            resolve_stress_results_concrete,
    "stress_reinf_service":               resolve_stress_results_reinforcement,

    # ── Fatigue ───────────────────────────────────────────────────────────
    "fatigue_assessment_girder":          resolve_fatigue_assessment_girder,

    # ── Shear Connector ───────────────────────────────────────────────────
    "shear_connector_capacity":              resolve_shear_connector_capacity,
    "shear_connector_spacing_uls":           resolve_shear_connector_spacing_uls,
    "shear_connector_spacing_fatigue":       resolve_shear_connector_spacing_fatigue,
    "governing_shear_connector_spacing":     resolve_governing_shear_connector_spacing,
    "shear_connector_detailing_checks":      resolve_shear_connector_detailing_checks,

    # ── Transverse Shear & Crack Width ────────────────────────────────────
    "transverse_shear_check":             resolve_transverse_shear_check,
    "crack_width_check":                  resolve_crack_width_check,

    # ── Design Summary ────────────────────────────────────────────────────
    "design_results_summary":             resolve_design_results_summary,
}