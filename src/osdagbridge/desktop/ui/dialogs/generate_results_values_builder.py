import logging
from osdagbridge.core.utils.common import *

logger = logging.getLogger(__name__)

# ── Empty value sentinel ──────────────────────────────────────────────────────

EMPTY = "-"


# ── Formatting helpers ────────────────────────────────────────────────────────

def _num(value, decimals=2):
    """Round a numeric value. Returns EMPTY on any failure."""
    try:
        return round(float(value), decimals)
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
# Maps table schema id → callable(output_dict) → dict | None

RESOLVER_MAP: dict[str, callable] = {}


def resolve_table(table_id: str, output_dict: dict) -> dict | None:
    """
    Look up and call the resolver for table_id.

    ``output_dict`` is the snapshot the results dialog was constructed with —
    the single read source for every table. Returns None if no resolver exists
    or if the resolver itself returns None (meaning required keys were absent).
    """
    fn = RESOLVER_MAP.get(table_id)
    return fn(output_dict) if fn else None


# ── Resolvers — Bridge Configuration ─────────────────────────────────────────

def resolve_bridge_config_summary(output_dict: dict) -> dict | None:
    od = output_dict
    overall_width  = od.get(KEY_TS_OVERALL_WIDTH)
    span           = od.get(KEY_SPAN)
    no_of_girders  = od.get(KEY_TS_NO_OF_GIRDERS)
    girder_spacing = od.get(KEY_TS_GIRDER_SPACING)
    deck_overhang  = od.get(KEY_TS_DECK_OVERHANG)
    skew_angle     = od.get(KEY_SKEW_ANGLE)

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


def resolve_material_properties_steel(output_dict: dict) -> dict | None:
    od = output_dict
    girder_grade    = od.get(KEY_GIRDER)
    bracing_grade   = od.get(KEY_CROSS_BRACING)
    diaphragm_grade = od.get(KEY_END_DIAPHRAGM)

    if not _has(girder_grade):
        return None

    # All properties are computed at design time and stored under the per-component
    # material keys (see compute_report_values); read them straight from output_dict.
    def _row(component, grade, fu_k, fy_k, e_k, g_k, v_k, thermal_k):
        return [
            component,
            _val(grade),
            _num(od.get(fu_k)),
            _num(od.get(fy_k)),
            _num(od.get(e_k)),
            _num(od.get(g_k)),
            _num(od.get(v_k)),
            _num(od.get(thermal_k)),
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
            _row("Girder", girder_grade,KEY_MATERIAL_GIRDER_FU, KEY_MATERIAL_GIRDER_FY, KEY_MATERIAL_GIRDER_E, KEY_MATERIAL_GIRDER_G, KEY_MATERIAL_GIRDER_POISSON, KEY_MATERIAL_GIRDER_THERMAL),
            _row("Cross Bracing", bracing_grade, KEY_MATERIAL_CROSS_BRACING_FU, KEY_MATERIAL_CROSS_BRACING_FY, KEY_MATERIAL_CROSS_BRACING_E, KEY_MATERIAL_CROSS_BRACING_G, KEY_MATERIAL_CROSS_BRACING_POISSON, KEY_MATERIAL_CROSS_BRACING_THERMAL),
            _row("End Diaphragm", diaphragm_grade, KEY_MATERIAL_END_DIAPHRAGM_FU, KEY_MATERIAL_END_DIAPHRAGM_FY, KEY_MATERIAL_END_DIAPHRAGM_E, KEY_MATERIAL_END_DIAPHRAGM_G, KEY_MATERIAL_END_DIAPHRAGM_POISSON, KEY_MATERIAL_END_DIAPHRAGM_THERMAL),
        ],
    }


def resolve_material_properties_concrete(output_dict: dict) -> dict | None:
    od = output_dict
    concrete_grade = od.get(KEY_DECK_CONCRETE_GRADE_BASIC)

    if not _has(concrete_grade):
        return None

    def _row(component):
        return [
            component,
            _val(concrete_grade),
            _num(od.get(KEY_MATERIAL_DECK_FCK)),
            _num(od.get(KEY_MATERIAL_DECK_FCTM)),
            _num(od.get(KEY_MATERIAL_DECK_ECM)),
            _num(od.get(KEY_MATERIAL_DECK_MODULAR)),
            _num(od.get(KEY_MATERIAL_DECK_DENSITY)),
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
        ],
        "rows": [
            _row("Deck Slab"),
        ],
    }


# ── Resolvers — Member Definitions ───────────────────────────────────────────

def resolve_girder_section_properties(output_dict: dict) -> dict | None:
    od = output_dict
    n_girders = od.get(KEY_TS_NO_OF_GIRDERS)
    if not _has(n_girders):
        return None

    try:
        n = int(n_girders)
    except Exception:
        return None

    def _gk(base_key, gi, mi):
        """Return output_dict[base_key.G{gi}.M{mi}] or None."""
        return od.get(f"{base_key}.G{gi}.M{mi}")

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
            sel = od.get(f"{base_key}.selected.G{gi}.M{mi}")
            if isinstance(sel, (list, tuple)) and sel:
                return ", ".join(str(s) for s in sel)
            return "All"
        if isinstance(v, (list, tuple)):
            return ", ".join(str(s) for s in v) if v else EMPTY
        try:
            return round(float(v), 2)
        except (ValueError, TypeError):
            return _val(v)

    span = _num(od.get(KEY_SPAN)) if _has(od.get(KEY_SPAN)) else EMPTY

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


def _chord_cells(flag_key, type_key, desig_key, pair, *, yes_no, sec_label, od):
    """(present, section type, designation) for one chord (top/bottom).

    The section columns only carry a value when the chord is actually present —
    the defaults seed a type/designation for every pair regardless, so an absent
    chord would otherwise report a section it does not have. ``yes_no`` / ``sec_label``
    / ``od`` are the calling resolver's per-pair lookup helpers.
    """
    present = yes_no(flag_key, pair)
    if present != "Yes":
        return [present, EMPTY, EMPTY]
    return [present, sec_label(od(type_key, pair)), _val(od(desig_key, pair))]


def resolve_cross_bracing_section_properties(output_dict: dict) -> dict | None:
    # All values come from output_dict. Cross-bracing keys are stored as
    # "<base>.<field>.<pair>.<member>" (e.g. ".bracing_section_type.G1G2.B1M1");
    # "no_of_cross_bracings" is a single global key. Absent keys render as EMPTY.
    od = output_dict
    n_girders = od.get(KEY_TS_NO_OF_GIRDERS)
    if not _has(n_girders):
        return None
    try:
        n = int(n_girders)
    except Exception:
        return None
    if n < 2:
        return None   # cross bracing needs at least one adjacent girder pair

    def _od(key, pair):
        """First non-blank value of "<key>.<pair>.<member>" for the given pair."""
        prefix = f"{key}.{pair}."
        for k, v in od.items():
            if k.startswith(prefix) and v not in (None, "", [], {}):
                return v
        return None

    def _yes_no(key, pair):
        """'Yes'/'No' from the per-pair flag; EMPTY only when the key is absent."""
        prefix = f"{key}.{pair}."
        for k, v in od.items():
            if k.startswith(prefix):
                return "Yes" if str(v).strip().lower() in ("yes", "true", "1") else "No"
        return EMPTY

    SECTION_LABELS = {
        "ANGLE": "Angle", "CHANNEL": "Channel", "BEAM": "Beam",
        "DOUBLE_ANGLE": "Double Angles", "DOUBLE_ANGLES": "Double Angles",
        "DOUBLE_CHANNEL": "Double Channel",
    }

    def _sec_label(v):
        return SECTION_LABELS.get(str(v).strip().upper(), str(v)) if v is not None else EMPTY

    def _brace_label(v):
        return ("K-Bracing" if "K" in str(v).upper() else "X-Bracing") if v is not None else EMPTY

    # No. of cross bracings is a single global value in output_dict.
    n_cb_disp = _val(od.get(KEY_MP_CB_NO_OF_CROSS_BRACINGS))

    rows = []
    for i in range(1, n):
        pair = f"G{i}G{i + 1}"
        sp = _od(KEY_MP_CB_SPACING, pair)
        rows.append([
            pair,
            _brace_label(_od(KEY_MP_CB_TYPE, pair)),
            n_cb_disp,
            _sec_label(_od(KEY_MP_CB_BRACING_SECTION_TYPE, pair)),
            _val(_od(KEY_MP_CB_BRACING_SECTION_DESIGNATION, pair)),
            *_chord_cells(KEY_MP_CB_TOP_CHORD, KEY_MP_CB_TOP_CHORD_SECTION_TYPE,
                          KEY_MP_CB_TOP_CHORD_SECTION_DESIG, pair,
                          yes_no=_yes_no, sec_label=_sec_label, od=_od),
            *_chord_cells(KEY_MP_CB_BOTTOM_CHORD, KEY_MP_CB_BOTTOM_CHORD_SECTION_TYPE,
                          KEY_MP_CB_BOTTOM_CHORD_SECTION_DESIG, pair,
                          yes_no=_yes_no, sec_label=_sec_label, od=_od),
            _num(sp) if sp is not None else EMPTY,
        ])

    if not rows:
        return None

    return {
        "id": "cross_bracing_section_properties",
        "label": "Cross Bracing Section Properties",
        "columns": [
            "Member",
            "Type of Bracing",
            "No. of Cross Bracing",
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


def resolve_end_diaphragm_section_properties(output_dict: dict) -> dict | None:
    od = output_dict
    n_girders = od.get(KEY_TS_NO_OF_GIRDERS)
    if not _has(n_girders):
        return None
    try:
        n = int(n_girders)
    except Exception:
        return None
    if n < 2:
        return None

    def _od(key, pair):
        """First non-blank value of "<key>.<pair>.<member>" for the given pair."""
        prefix = f"{key}.{pair}."
        for k, v in od.items():
            if k.startswith(prefix) and v not in (None, "", [], {}):
                return v
        return None

    def _yes_no(key, pair):
        """'Yes'/'No' from the per-pair flag; EMPTY only when the key is absent."""
        prefix = f"{key}.{pair}."
        for k, v in od.items():
            if k.startswith(prefix):
                return "Yes" if str(v).strip().lower() in ("yes", "true", "1") else "No"
        return EMPTY

    def _member_count(pair):
        """Number of distinct E* member slots for the pair (= no. of end diaphragms)."""
        prefix = f"{KEY_MP_ED_TYPE}.{pair}."
        members = {k[len(prefix):].split(".")[0] for k in od if k.startswith(prefix)}
        return len(members) or None

    SECTION_LABELS = {
        "ANGLE": "Angle", "CHANNEL": "Channel", "BEAM": "Beam",
        "DOUBLE_ANGLE": "Double Angles", "DOUBLE_ANGLES": "Double Angles",
        "DOUBLE_CHANNEL": "Double Channel",
    }

    def _sec_label(v):
        return SECTION_LABELS.get(str(v).strip().upper(), str(v)) if v is not None else EMPTY

    def _brace_label(v):
        return ("K-Bracing" if "K" in str(v).upper() else "X-Bracing") if v is not None else EMPTY

    columns = [
        "Member ID",
        "Type",
        "No. of End Diaphragm",
        "Bracing Type",
        "Type of Connection",
        "Bracing Section Type",
        "Bracing Section Designation",
        "Top Chord",
        "Top Chord Section Type",
        "Top Chord Section Designation",
        "Bottom Chord",
        "Bottom Chord Section Type",
        "Bottom Chord Section Designation",
    ]

    rows = []
    for i in range(1, n):
        pair  = f"G{i}G{i + 1}"
        cells = {c: EMPTY for c in columns}
        cells["Member ID"] = pair

        ed_type = _od(KEY_MP_ED_TYPE, pair)
        cells["Type"] = _val(ed_type)
        cells["No. of End Diaphragm"] = _val(_member_count(pair))

        if ed_type is not None and "brac" in str(ed_type).strip().lower():
            # Cross Bracing diaphragm — bracing/chord sections.
            cells["Type of Connection"]               = _val(_od(KEY_MP_ED_BRACING_CONNECTION, pair))
            cells["Bracing Type"]                     = _brace_label(_od(KEY_MP_ED_BRACING_TYPE, pair))
            cells["Bracing Section Type"]             = _sec_label(_od(KEY_MP_ED_BRACING_SECTION, pair))
            cells["Bracing Section Designation"]      = _val(_od(KEY_MP_ED_BRACING_SECTION_DESIGNATION, pair))
            # The section columns only carry a value when that chord is actually
            # present — the defaults seed a type/designation for every pair
            # regardless, so an absent chord would report a section it does not have.
            for face, flag_key, type_key, desig_key in (
                ("Top",    KEY_MP_ED_TOP_CHORD,
                 KEY_MP_ED_TOP_CHORD_SECTION_TYPE,    KEY_MP_ED_TOP_CHORD_SECTION_DESIG),
                ("Bottom", KEY_MP_ED_BOTTOM_CHORD,
                 KEY_MP_ED_BOTTOM_CHORD_SECTION_TYPE, KEY_MP_ED_BOTTOM_CHORD_SECTION_DESIG),
            ):
                present, sec_type, desig = _chord_cells(
                    flag_key, type_key, desig_key, pair,
                    yes_no=_yes_no, sec_label=_sec_label, od=_od)
                cells[f"{face} Chord"] = present
                cells[f"{face} Chord Section Type"] = sec_type
                cells[f"{face} Chord Section Designation"] = desig

        rows.append([cells[c] for c in columns])

    if not rows:
        return None

    return {
        "id":    "end_diaphragm_section_properties",
        "label": "End Diaphragm Section Properties",
        "columns": columns,
        "rows": rows,
    }


def resolve_shear_stud_properties(output_dict: dict) -> dict | None:
    od = output_dict
    fy                  = od.get(KEY_DS_STUD_YIELD_STRENGTH)
    fu                  = od.get(KEY_DS_STUD_ULTIMATE_STRENGTH)
    diameter            = od.get(KEY_DS_STUD_DIAMETER)
    height              = od.get(KEY_DS_STUD_HEIGHT)
    transverse_spacing  = od.get(KEY_DS_STUD_TRANSVERSE_SPACING)
    count               = od.get(KEY_DS_STUD_COUNT)
    avg_long_spacing    = od.get(KEY_SD_SHEAR_LONGITUDINAL_SPACING)

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

def resolve_permanent_load_summary(output_dict: dict) -> dict | None:
    """
    Permanent (dead) load breakdown per girder (kN/m). All values are computed at
    design time (see _store_permanent_load_breakdown) and read straight from
    output_dict. SW and DL vary per girder; SW-factor / DC / DD / DW / SIDL are
    shared. DL = SW + DC + DD + DW + SIDL.
    """
    od = output_dict
    n_girders = od.get(KEY_TS_NO_OF_GIRDERS)
    if not _has(n_girders):
        return None
    try:
        n = int(n_girders)
    except Exception:
        return None

    sw_factor = od.get(KEY_PL_SELF_WEIGHT_FACTOR)
    dc   = od.get(KEY_SD_DL_DC)
    dd   = od.get(KEY_SD_DL_DD)
    dw   = od.get(KEY_SD_DL_DW)
    sidl = od.get(KEY_SD_DL_SIDL)

    rows = []
    for i in range(1, n + 1):
        rows.append([
            f"Girder {i}",
            _num(sw_factor),
            _num(od.get(f"{KEY_SD_DL_SW}.G{i}"), 3),
            _num(dc, 3),
            _num(dd, 3),
            _num(dw, 3),
            _num(sidl, 3),
            _num(od.get(f"{KEY_SD_PERMANENT_DL}.G{i}"), 3),
        ])

    return {
        "id":    "permanent_load_summary",
        "label": "Permanent Load Summary",
        "columns": [
            "Girder",
            "Self-weight Factor",
            "Self Weight, SW (kN/m)",
            "Other Steel, DC (kN/m)",
            "Deck Slab, DD (kN/m)",
            "Wearing Course, DW (kN/m)",
            "Superimposed DL, SIDL (kN/m)",
            "Total Dead Load, DL (kN/m)",
        ],
        "rows": rows,
    }


def resolve_live_load_definitions(output_dict: dict) -> dict | None:
    od = output_dict

    def _yn(key: str) -> str:
        raw = od.get(key)
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
    ecc = od.get(KEY_LL_ECCENTRICITY)
    rows.append([
        "Breaking Load : Eccentricity from top of Deck (m)",
        _num(ecc) if _has(ecc) else EMPTY,
    ])

    # ── Footpath Pressure: mode-aware ────────────────────────────────────
    fp_mode  = od.get(KEY_LL_FOOTPATH_PRESSURE_MODE)
    fp_value = od.get(KEY_LL_FOOTPATH_PRESSURE_VALUE)

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

def resolve_seismic_load_parameters(output_dict: dict) -> dict | None:
    """
    One row per girder. All seismic parameters are bridge-level (not girder-specific),
    so the same values repeat across rows — girder column anchors each row.
    Dead/Live load for seismic use mode+value pattern same as live load footpath.
    """
    od = output_dict
    n_girders = od.get(KEY_TS_NO_OF_GIRDERS)
    if not _has(n_girders):
        return None

    try:
        n = int(n_girders)
    except Exception:
        return None

    # ── Parameters & coefficients — all resolved and stored at design time ──
    # (see compute_report_values); read straight from output_dict.
    zone              = od.get(KEY_SL_SEISMIC_ZONE)
    importance        = od.get(KEY_SL_IMPORTANCE_FACTOR)
    soil_type         = od.get(KEY_SL_SOIL_TYPE)
    time_period       = od.get(KEY_SL_TIME_PERIOD)
    damping           = od.get(KEY_SL_DAMPING)
    response_red      = od.get(KEY_SL_RESPONSE_REDUCTION)

    zone_factor       = od.get(KEY_SL_ZONE_FACTOR)
    spectral_coeff    = od.get(KEY_SL_SPECTRAL_COEFF)
    horizontal_coeff  = od.get(KEY_SL_HORIZONTAL_COEFF)
    vertical_coeff    = od.get(KEY_SL_VERTICAL_COEFF)

    # ── Dead load for seismic: mode + value ───────────────────────────────
    dl_mode  = od.get(KEY_SL_DEAD_LOAD_MODE)
    dl_value = od.get(KEY_SL_DEAD_LOAD_VALUE)
    if _has(dl_mode) and str(dl_mode).lower() == "automatic":
        dl_display = "Automatic"
    elif _has(dl_value):
        dl_display = _num(dl_value)
    else:
        dl_display = EMPTY

    # ── Live load for seismic: mode + value ───────────────────────────────
    ll_mode  = od.get(KEY_SL_LIVE_LOAD_MODE)
    ll_value = od.get(KEY_SL_LIVE_LOAD_VALUE)
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

def resolve_wind_load_parameters(output_dict: dict) -> dict | None:
    """
    One row per girder. All wind parameters are bridge-level so values repeat
    across rows — girder column anchors each row.
    Mode-aware fields (Automatic / As per IRC 6 / User-defined) show the mode
    string when set to automatic/IRC, or the numeric value when user-defined.
    """
    od = output_dict
    n_girders = od.get(KEY_TS_NO_OF_GIRDERS)
    if not _has(n_girders):
        return None

    try:
        n = int(n_girders)
    except Exception:
        return None

    # ── Direct (basic wind speed resolved & stored at design time) ──
    basic_wind_speed    = od.get(KEY_WL_BASIC_WIND_SPEED)
    avg_exposed_height  = od.get(KEY_WL_AVG_EXPOSED_HEIGHT)
    terrain_type        = od.get(KEY_WL_TERRAIN_TYPE)
    site_topography     = od.get(KEY_WL_SITE_TOPOGRAPHY)

    # ── Mode-aware helper: show mode label or numeric value ───────────────
    def _mode_val(mode_key, value_key, decimals=2):
        mode  = od.get(mode_key)
        value = od.get(value_key)
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

    # ── Computed values (Vz, Pz) — computed and stored at design time ──────
    hourly_mean_wind    = od.get(KEY_WL_HOURLY_MEAN_WIND)
    hourly_wind_pressure = od.get(KEY_WL_HOURLY_WIND_PRESSURE)

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

def resolve_temperature_load_parameters(output_dict: dict) -> dict | None:
    """
    Single summary row — temperature load is bridge-level, not per-girder.
    All values come from the Loading tab (self-contained, no analysis needed):
      • Highest/lowest air temp — synced from the project location.
      • Thermal coefficients (steel/RCC) — Loading-tab  (IRC default 12e-6).
      • Effective bridge temps + design rise/fall — recomputed per IRC 6 Cl. 215.2.
    """
    # ── All temperatures & coefficients resolved and stored at design time ──
    # (see compute_report_values); read straight from output_dict.
    od = output_dict
    highest_max_temp    = od.get(KEY_TL_HIGHEST_MAX_TEMP)
    lowest_min_temp     = od.get(KEY_TL_LOWEST_MIN_TEMP)
    thermal_coeff_steel = od.get(KEY_TL_THERMAL_COEFF_STEEL)
    thermal_coeff_rcc   = od.get(KEY_TL_THERMAL_COEFF_RCC)
    bridge_temp_min     = od.get(KEY_TL_BRIDGE_TEMP_MIN)
    bridge_temp_max     = od.get(KEY_TL_BRIDGE_TEMP_MAX)
    temp_rise           = od.get(KEY_TL_TEMP_RISE)
    temp_fall           = od.get(KEY_TL_TEMP_FALL)

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

def resolve_load_combinations(output_dict: dict) -> dict | None:
    """
    Load combinations table — sourced entirely from output_dict.

    The backend builds the authoritative report at design time (IRC6 defaults +
    custom, each {name, expr, included}) and stores it under KEY_LC_REPORT.
    'Selected' reflects each combination's included flag.
    """
    od = output_dict

    def _yesno(raw) -> str:
        selected = (
            raw is True
            or str(raw).strip().lower() in ("true", "yes", "1", "checked")
        )
        return "Yes" if selected else "No"

    rows = []
    for c in (od.get(KEY_ALL_LOAD_COMBINATIONS) or []):
        if not isinstance(c, dict):
            continue
        name = str(c.get("name", ""))
        if " : " in name:
            label, expr = name.split(" : ", 1)
        else:
            label, expr = name, str(c.get("expr", ""))
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


def resolve_deflection_dead_load(output_dict: dict) -> dict | None:
    """Per-girder DL-only deflection vs allowable, read straight from output_dict
    (design() stores post-camber actuals under "<KEY_SD_DEFL_AFTER_CAMBER>.G{i}").
    The allowable is KEY_SD_DEFL_ALLOW_TOTAL (L/600) — IRC 22 Cl.604.3.2 gives no
    DL-only limit, so designer._add_check(18, "SLS Deflection (DL)") checks it
    against the total-load limit. No fallbacks — absent values render empty."""
    od = output_dict
    n_girders = od.get(KEY_TS_NO_OF_GIRDERS)
    if not _has(n_girders):
        return None
    try:
        n = int(n_girders)
    except Exception:
        return None

    allow = od.get(KEY_SD_DEFL_ALLOW_TOTAL)
    allow_disp = _num(allow) if _has(allow) else EMPTY

    rows = []
    for i in range(1, n + 1):
        girder = f"G{i}"
        defl_mm = od.get(f"{KEY_SD_DEFL_AFTER_CAMBER}.{girder}")
        ur, status = _defl_ur(defl_mm, allow) if (_has(defl_mm) and _has(allow)) else (EMPTY, EMPTY)
        rows.append([
            girder,
            _num(defl_mm) if _has(defl_mm) else EMPTY,
            allow_disp,
            ur,
            status,
        ])

    return {
        "id":    "deflection_dead_load",
        "label": "Deflection - Dead Load",
        "columns": [
            "Girder",
            "Deflection due to Dead Load (post-camber), δ_DL (mm)",
            "Permissible Limit (mm)",
            "Utilization Ratio",
            "Status",
        ],
        "rows": rows,
    }


def resolve_deflection_live_load(output_dict: dict) -> dict | None:
    """Per-girder live-load deflection vs allowable, read straight from output_dict
    (design() stores actuals under "<KEY_SD_DEFL_LIVE>.G{i}"; store_design_results
    stores the allowable, L/800 per IRC 22 Cl.604.3.2, under KEY_SD_DEFL_ALLOW_LIVE).
    No fallbacks — absent values render empty."""
    od = output_dict
    n_girders = od.get(KEY_TS_NO_OF_GIRDERS)
    if not _has(n_girders):
        return None
    try:
        n = int(n_girders)
    except Exception:
        return None

    allow = od.get(KEY_SD_DEFL_ALLOW_LIVE)
    allow_disp = _num(allow) if _has(allow) else EMPTY

    rows = []
    for i in range(1, n + 1):
        girder = f"G{i}"
        defl_mm = od.get(f"{KEY_SD_DEFL_LIVE}.{girder}")
        ur, status = _defl_ur(defl_mm, allow) if (_has(defl_mm) and _has(allow)) else (EMPTY, EMPTY)
        rows.append([
            girder,
            _num(defl_mm) if _has(defl_mm) else EMPTY,
            allow_disp,
            ur,
            status,
        ])

    return {
        "id":    "deflection_live_load",
        "label": "Deflection - Live Load",
        "columns": [
            "Girder",
            "Deflection due to Live Load, δ_ₗᵢᵥₑ (mm)",
            "Permissible Limit (mm)",
            "Utilization Ratio",
            "Status",
        ],
        "rows": rows,
    }


def resolve_deflection_total_load(output_dict: dict) -> dict | None:
    """Per-girder total-load deflection vs allowable, read straight from output_dict
    (design() stores actuals under "<KEY_SD_DEFL_TOTAL>.G{i}"; store_design_results
    stores the governing allowable under KEY_SD_DEFL_ALLOW_TOTAL). No fallbacks —
    absent values render empty."""
    od = output_dict
    n_girders = od.get(KEY_TS_NO_OF_GIRDERS)
    if not _has(n_girders):
        return None
    try:
        n = int(n_girders)
    except Exception:
        return None

    allow = od.get(KEY_SD_DEFL_ALLOW_TOTAL)
    allow_disp = _num(allow) if _has(allow) else EMPTY

    rows = []
    for i in range(1, n + 1):
        girder = f"G{i}"
        defl_mm = od.get(f"{KEY_SD_DEFL_TOTAL}.{girder}")
        ur, status = _defl_ur(defl_mm, allow) if (_has(defl_mm) and _has(allow)) else (EMPTY, EMPTY)
        rows.append([
            girder,
            _num(defl_mm) if _has(defl_mm) else EMPTY,
            allow_disp,
            ur,
            status,
        ])

    return {
        "id":    "deflection_total_load",
        "label": "Deflection - Total Load",
        "columns": [
            "Girder",
            "Total Deflection, δₜₒₜₐₗ (mm)",
            "Permissible Limit (mm)",
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


def _get_uls_per_girder(output_dict) -> dict:
    """Return design_results[KEY_SD_ULS_PER_GIRDER], or {} if unavailable."""
    return ((output_dict or {}).get("design_results") or {}).get(KEY_SD_ULS_PER_GIRDER) or {}


def _uls_check_rows(output_dict, category: str) -> list | None:
    """Return ordered (girder_label, demand, capacity, ur, status) rows for one check category.

    Girder order and all values come from output_dict["design_results"]
    [uls_per_girder] (stored by _build_uls_per_girder in the designer).
    Returns None if the data is not available yet.
    """
    uls_pg = _get_uls_per_girder(output_dict)
    cat_data = uls_pg.get(category)
    if not cat_data:
        return None

    rows = []
    for girder, g_chk in cat_data.items():
        if g_chk is None:
            rows.append([f"{girder}M1", EMPTY, EMPTY, EMPTY, EMPTY])
        else:
            rows.append([
                f"{girder}M1",
                _num(g_chk["demand"]),
                _num(g_chk["capacity"]),
                _num(g_chk["ur"]),
                g_chk.get("status", EMPTY),
            ])
    return rows if rows else None


def resolve_flexural_resistance_check(output_dict: dict) -> dict | None:
    rows = _uls_check_rows(output_dict, "flexure")
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


def resolve_shear_resistance_check(output_dict: dict) -> dict | None:
    rows = _uls_check_rows(output_dict, "shear")
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


def resolve_bending_shear_interaction_check(output_dict: dict) -> dict | None:
    rows = _uls_check_rows(output_dict, "interaction")
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


def resolve_lateral_torsional_buckling_check(output_dict: dict) -> dict | None:
    rows = _uls_check_rows(output_dict, "ltb")
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


# ── Resolvers — Fatigue ───────────────────────────────────────────────────────

def resolve_fatigue_assessment_girder(output_dict: dict) -> dict | None:
    rows = _uls_check_rows(output_dict, "fatigue")
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

def _get_sc_dr(output_dict) -> dict:
    """Return design_results dict, or {} if design not yet run."""
    return (output_dict or {}).get("design_results") or {}


def _sc_girder_rows(output_dict) -> int | None:
    """Return the number of non-EB girder rows for shear connector tables."""
    n_girders = (output_dict or {}).get(KEY_TS_NO_OF_GIRDERS)
    if not _has(n_girders):
        return None
    return _uls_girder_rows(n_girders)


def resolve_shear_connector_capacity(output_dict: dict) -> dict | None:
    n = _sc_girder_rows(output_dict)
    if n is None:
        return None

    od = output_dict
    diameter = od.get(KEY_DS_STUD_DIAMETER)
    height   = od.get(KEY_DS_STUD_HEIGHT)
    fu_stud  = od.get(KEY_DS_STUD_ULTIMATE_STRENGTH)
    count    = od.get(KEY_DS_STUD_COUNT)

    fck = _num(od.get(KEY_MATERIAL_DECK_FCK)) if _has(od.get(KEY_MATERIAL_DECK_FCK)) else EMPTY
    ecm = _num(od.get(KEY_MATERIAL_DECK_ECM)) if _has(od.get(KEY_MATERIAL_DECK_ECM)) else EMPTY

    dr     = _get_sc_dr(output_dict)
    Qu     = _num(dr.get(KEY_SD_SC_Qu_kN)) if dr.get(KEY_SD_SC_Qu_kN) is not None else EMPTY
    n_stud = _val(count) if _has(count) else EMPTY
    try:
        sum_Qd = _num(float(dr[KEY_SD_SC_Qu_kN]) * int(count)) if (dr.get(KEY_SD_SC_Qu_kN) and _has(count)) else EMPTY
    except Exception:
        sum_Qd = EMPTY
    

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
        ],
        "rows": rows,
    }


def resolve_shear_connector_spacing_uls(output_dict: dict) -> dict | None:
    n = _sc_girder_rows(output_dict)
    if n is None:
        return None

    count = output_dict.get(KEY_DS_STUD_COUNT)
    dr    = _get_sc_dr(output_dict)

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

    rows = [
        [f"Girder {i}", VL, sum_Qd, SL1, H, SL2, min_sl]
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
        ],
        "rows": rows,
    }


def resolve_shear_connector_spacing_fatigue(output_dict: dict) -> dict | None:
    n = _sc_girder_rows(output_dict)
    if n is None:
        return None

    count = output_dict.get(KEY_DS_STUD_COUNT)
    dr    = _get_sc_dr(output_dict)

    Vr     = _num(dr[KEY_SD_SC_Vr_kN])  if dr.get(KEY_SD_SC_Vr_kN) is not None else EMPTY
    Qr     = _num(dr[KEY_SD_SC_Qr_kN])  if dr.get(KEY_SD_SC_Qr_kN) is not None else EMPTY
    n_stud = _val(count) if _has(count) else EMPTY
    SR     = _num(dr[KEY_SD_SC_SR])      if dr.get(KEY_SD_SC_SR)    is not None else EMPTY
    cd     = (dr.get("capacity_details") or {})
    

    rows = [
        [f"Girder {i}", Vr, Qr, n_stud, SR,]
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
        ],
        "rows": rows,
    }


def resolve_governing_shear_connector_spacing(output_dict: dict) -> dict | None:
    n = _sc_girder_rows(output_dict)
    if n is None:
        return None

    dr = _get_sc_dr(output_dict)
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
    lim600 = _num(dr[KEY_SD_SC_LIMIT_600])    if dr.get(KEY_SD_SC_LIMIT_600)    is not None else EMPTY
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


def resolve_shear_connector_detailing_checks(output_dict: dict) -> dict | None:
    n = _sc_girder_rows(output_dict)
    if n is None:
        return None

    od       = output_dict
    diameter = od.get(KEY_DS_STUD_DIAMETER)
    height   = od.get(KEY_DS_STUD_HEIGHT)
    dr       = _get_sc_dr(output_dict)

    d      = _num(diameter) if _has(diameter) else EMPTY
    h      = _num(height)   if _has(height)   else EMPTY
    tf     = _num(float(dr[KEY_SD_SC_D_LIMIT]) / 2.0) if dr.get(KEY_SD_SC_D_LIMIT) else EMPTY
    d_lim  = _num(dr[KEY_SD_SC_D_LIMIT])   if dr.get(KEY_SD_SC_D_LIMIT)   is not None else EMPTY
    h_min  = _num(dr[KEY_SD_SC_H_MIN])     if dr.get(KEY_SD_SC_H_MIN)     is not None else EMPTY
    e_dist = _num(dr[KEY_SD_SC_EDGE_DIST]) if dr.get(KEY_SD_SC_EDGE_DIST) is not None else EMPTY
    e_req  = _num(dr[KEY_SD_SC_REQ_EDGE_DIST]) if dr.get(KEY_SD_SC_REQ_EDGE_DIST) is not None else EMPTY
    cover  = _num(dr[KEY_SD_SC_CLEAR_COVER])   if dr.get(KEY_SD_SC_CLEAR_COVER)   is not None else EMPTY
    c_req  = _num(dr[KEY_SD_SC_REQ_CLEAR_COVER]) if dr.get(KEY_SD_SC_REQ_CLEAR_COVER) is not None else EMPTY
    cd     = (dr.get("capacity_details") or {})
    
    status = ("PASS" if dr.get("stud_detailing_ok") else "FAIL") if "stud_detailing_ok" in dr else EMPTY

    rows = [
        [f"Girder {i}", d, tf, d_lim, h, h_min, e_dist, e_req, cover, c_req, status]
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
            "Status",
        ],
        "rows": rows,
    }


# ── Resolvers — Crack Width Check (partial) ───────────────────────────────────

def resolve_transverse_shear_check(output_dict: dict) -> dict | None:
    n = _sc_girder_rows(output_dict)
    if n is None:
        return None

    dr = _get_sc_dr(output_dict)
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
    status = ("PASS" if dr.get("transverse_shear_ok") else "FAIL") if "transverse_shear_ok" in dr else EMPTY

    rows = [
        [f"Girder {i}", VL, Vc, Vs, VRd, dcr, status]
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
            "Status",
        ],
        "rows": rows,
    }


def resolve_crack_width_check(output_dict: dict) -> dict | None:
    dd = _get_deck_design(output_dict)
    wk_bot = dd.get(KEY_DD_CRACK_WK_BOTTOM)
    wk_top = dd.get(KEY_DD_CRACK_WK_TOP)
    if wk_bot is None and wk_top is None:
        return None

    wk_lim = dd.get(KEY_DD_CRACK_WK_LIMIT)
    dr      = _get_sc_dr(output_dict)
    as_min  = _num(dr[KEY_SD_CRACK_AS_MIN])  if dr.get(KEY_SD_CRACK_AS_MIN)  is not None else EMPTY
    as_prov = _num(dr[KEY_SD_CRACK_AS_PROV]) if dr.get(KEY_SD_CRACK_AS_PROV) is not None else EMPTY

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
            "Status",
        ],
        "rows": rows,
    }


# ── Resolvers — Design Results Summary ────────────────────────────────────────

def resolve_design_results_summary(output_dict: dict) -> dict | None:
    """One row per girder: the controlling check (highest UR among the 8 design
    checks, from envelope demands) plus the real load case / combination that
    drives that check (worst per-LC UR for the same check id, envelope
    pseudo-cases excluded)."""
    pg = _get_per_girder(output_dict)
    if not pg:
        return None

    def _with_unit(value, unit):
        v = _num(value)
        if v == EMPTY:
            return EMPTY
        return f"{v} {unit}".strip() if unit and unit not in ("–", "-") else v

    rows = []
    for girder in pg:
        g_data = pg.get(girder) or {}
        checks = g_data.get("checks") or []
        if not checks:
            rows.append([f"{girder}M1", EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY])
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
            f"{girder}M1",
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


def resolve_deck_slab_properties(output_dict: dict) -> dict | None:
    """
    Deck slab properties table — read entirely from
    output_dict["deck_design_results"] (populated by design_deck_slab()).
    Absent values render empty.
    """
    dd = _get_deck_design(output_dict)

    def _dd(key):
        v = dd.get(key)
        return v if v not in (None, "", [], {}) else None

    grade     = _dd("deck_grade")
    thickness = _dd("deck_thickness")
    overhang_raw = _dd("deck_overhang")
    if overhang_raw is not None:
        try:
            overhang = round(float(overhang_raw) / 1000.0, 3)
        except Exception:
            overhang = None
    else:
        overhang = None

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
# These resolvers read from output_dict["design_results"]["per_girder"]
# which is populated at design time.  per_girder keys: G1, G2, ...
# Each girder dict has "checks" (list with check_id 10/11/12) and
# "sls_fibre_stresses" (raw fbt_MPa / fbc_MPa from compute_sls_stresses).

def _get_per_girder(output_dict):
    """Return per_girder dict from design_results, or {} if unavailable."""
    return ((output_dict or {}).get("design_results") or {}).get("per_girder") or {}


def _stress_ur(sigma, limit):
    """Return (ur_rounded, status) for a stress / allowable pair."""
    try:
        ur = round(float(sigma) / float(limit), 3)
        return ur, ("PASS" if ur <= 1.0 else "FAIL")
    except Exception:
        return EMPTY, EMPTY


def resolve_stress_results_steel(output_dict: dict) -> dict | None:
    # Controlling-girder envelope-SLS steel stress + allowable — single source
    # of truth computed in the designer; one value for every girder/member row.
    dr = (output_dict or {}).get("design_results") or {}
    sigma = dr.get(KEY_SD_STRESS_STEEL)
    limit = dr.get(KEY_SD_STRESS_STEEL_ALLOWABLE)
    if sigma is None or limit is None:
        return None

    ur, status = _stress_ur(sigma, limit)

    girders = list(_get_per_girder(output_dict))
    if not girders:
        return None

    rows = [[f"{g}M1", _num(sigma), _num(limit), ur, status] for g in girders]

    return {
        "id": "stress_steel_service",
        "label": "Stress in Structural Steel - Service",
        "columns": ["Member", "Steel Stress (MPa)", "Allowable Stress (MPa)", "Utilization Ratio", "Status"],
        "rows": rows,
    }


def _get_deck_design(output_dict):
    """Return deck_design_results dict, or {} if unavailable."""
    return (output_dict or {}).get("deck_design_results") or {}


def resolve_stress_results_concrete(output_dict: dict) -> dict | None:
    dd = _get_deck_design(output_dict)
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


def resolve_stress_results_reinforcement(output_dict: dict) -> dict | None:
    dd = _get_deck_design(output_dict)
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
# These tables need the per-girder / per-load-case bending-moment and shear-force
# envelope {girder: {load_case: {Mz_max, Mz_min, Vy_max, Vy_min}}}. That data is
# NOT stored in output_dict, so under the strict "output_dict only" rule these
# tables render empty until the design pipeline persists it under a key.

def _get_cache(output_dict):
    """Return the load-effects envelope from output_dict, or None if absent."""
    cache = output_dict.get("load_effects_cache")
    return cache if cache else None


def resolve_bending_moment_envelope(output_dict: dict) -> dict | None:
    try:
        cache = _get_cache(output_dict)
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


def resolve_shear_force_envelope(output_dict: dict) -> dict | None:
    try:
        cache = _get_cache(output_dict)
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


def resolve_bending_moment_by_load_case(output_dict: dict) -> dict | None:
    try:
        cache = _get_cache(output_dict)
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


def resolve_shear_force_by_load_case(output_dict: dict) -> dict | None:
    try:
        cache = _get_cache(output_dict)
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
    "deflection_dead_load":               resolve_deflection_dead_load,
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