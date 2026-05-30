from osdagbridge.core.utils.common import *

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


def _mm2(value, decimals=1):
    """Convert m² → mm², rounded. Returns EMPTY on any failure."""
    try:
        return round(float(value) * 1e6, decimals)
    except Exception:
        return EMPTY


def _mm4(value):
    """Convert m⁴ → mm⁴ in scientific notation string. Returns EMPTY on any failure."""
    try:
        v = float(value) * 1e12
        return round(v, 3)
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
    depth     = input_dict.get(KEY_GIRDER_DEPTH)
    bf_top    = input_dict.get(KEY_GIRDER_TOP_FLANGE_WIDTH)
    tf_top    = input_dict.get(KEY_GIRDER_TOP_FLANGE_THICKNESS)
    bf_bot    = input_dict.get(KEY_GIRDER_BOTTOM_FLANGE_WIDTH)
    tf_bot    = input_dict.get(KEY_GIRDER_BOTTOM_FLANGE_THICKNESS)
    tw        = input_dict.get(KEY_GIRDER_WEB_THICKNESS)
    area      = input_dict.get(KEY_GIRDER_SECTIONAL_AREA)
    iz        = input_dict.get(KEY_GIRDER_SECTIONAL_IZ)
    n_girders = input_dict.get(KEY_TS_NO_OF_GIRDERS)

    if not _has(depth, bf_top, tf_top, bf_bot, tf_bot, tw, area, iz, n_girders):
        return None

    try:
        n = int(n_girders)
    except Exception:
        return None

    row = [
        EMPTY,                  # Girder label — filled per-row below
        _mm(depth),
        _mm(bf_top),
        _mm(bf_bot),
        _mm(tf_top),
        _mm(tf_bot),
        _mm(tw),
        _mm2(area),
        _mm4(iz),
        EMPTY,                  # Cross-section class — not yet resolved from inputs
    ]

    rows = []
    for i in range(1, n + 1):
        r = list(row)
        r[0] = f"Girder {i}"
        rows.append(r)

    return {
        "id":    "girder_section_properties",
        "label": "Girder Section Properties",
        "columns": [
            "Girder",
            "Depth, d (mm)",
            "Top Flange Width, bfₜₒₚ (mm)",
            "Bottom Flange Width, bfᵦₒₜ (mm)",
            "Top Flange Thickness, tfₜₒₚ (mm)",
            "Bottom Flange Thickness, tfᵦₒₜ (mm)",
            "Web Thickness, tᵤ (mm)",
            "Cross-sectional Area, A (mm²)",
            "Second Moment of Area (z-axis), Iᵤ (mm⁴)",
            "Cross-section Class",
        ],
        "rows": rows,
    }


def resolve_cross_bracing_section_properties(input_dict: dict, bridge=None) -> dict | None:
    cb_type    = input_dict.get(KEY_CROSS_BRACING_TYPE)
    cb_section = input_dict.get(KEY_CROSS_BRACING_SECTION)
    cb_spacing = input_dict.get(KEY_CROSS_BRACING_SPACING)

    if not _has(cb_type, cb_spacing):
        return None

    return {
        "id":    "cross_bracing_section_properties",
        "label": "Cross Bracing Section Properties",
        "columns": [
            "Type",
            "Section",
            "Spacing (m)",
        ],
        "rows": [[
            _val(cb_type),
            _val(cb_section),
            _num(cb_spacing),
        ]],
    }


def resolve_end_diaphragm_section_properties(input_dict: dict, bridge=None) -> dict | None:
    ed_type    = input_dict.get(KEY_END_DIAPHRAGM_TYPE)
    ed_section = input_dict.get(KEY_END_DIAPHRAGM_BRACING_SECTION_DESIGNATION)

    if not _has(ed_type):
        return None

    return {
        "id":    "end_diaphragm_section_properties",
        "label": "End Diaphragm Section Properties",
        "columns": [
            "Type",
            "Section",
        ],
        "rows": [[
            _val(ed_type),
            _val(ed_section),
        ]],
    }


def resolve_shear_stud_properties(input_dict: dict, bridge=None) -> dict | None:
    diameter  = input_dict.get(KEY_DS_STUD_DIAMETER)
    height    = input_dict.get(KEY_DS_STUD_HEIGHT)
    fu        = input_dict.get(KEY_DS_STUD_ULTIMATE_STRENGTH)
    fy        = input_dict.get(KEY_DS_STUD_YIELD_STRENGTH)
    count     = input_dict.get(KEY_DS_STUD_COUNT)

    if not _has(diameter, height, fu, fy, count):
        return None

    return {
        "id":    "shear_stud_properties",
        "label": "Shear Stud Properties",
        "columns": [
            "Diameter (mm)",
            "Height (mm)",
            "Ultimate Tensile Strength, Fᵤ (MPa)",
            "Yield Strength, Fᵧ (MPa)",
            "Number per Section",
        ],
        "rows": [[
            _num(diameter),
            _num(height),
            _num(fu),
            _num(fy),
            _val(count),
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
    """
    Populate Vehicle Class and Impact Factor from user-selected vehicle types.
    KEY_VEHICLE holds a list of selected vehicle class strings.
    Impact factor is looked up per IRC:6 clause based on span.
    """
    vehicles = input_dict.get(KEY_VEHICLE)
    span     = input_dict.get(KEY_SPAN)

    if not _has(vehicles):
        return None

    # Normalise: KEY_VEHICLE may be a single string or a list
    if isinstance(vehicles, str):
        vehicles = [vehicles]

    # IRC:6 Cl.208.2 impact factor formula: 4.5/(6+L) for Class A/B;
    # 10% for 70R wheeled; 25% for 70R tracked/Class AA tracked.
    # Show formula string when span is available, else EMPTY.
    def _impact(vehicle_label: str) -> str:
        label = str(vehicle_label).lower()
        if not _has(span):
            return EMPTY
        L = float(span)
        if "70r" in label and "tracked" in label:
            return "25%"
        if "70r" in label or "aa" in label:
            return "10%"
        # Class A / B
        if L <= 3:
            return "50%"
        pct = round(4.5 / (6 + L) * 100, 1)
        return f"{pct}%"

    rows = [[_val(v), _impact(v)] for v in vehicles]

    return {
        "id":    "live_load_definitions",
        "label": "Live Load Definitions",
        "columns": ["Vehicle Class", "Impact Factor"],
        "rows":  rows,
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