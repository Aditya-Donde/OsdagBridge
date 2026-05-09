# Unit definitions
kilo = 1e3
milli = 1e-3
N = 1
m = 1
mm = milli * m
m2 = m ** 2
m3 = m ** 3
m4 = m ** 4
kN = kilo * N
Pa = 1
MPa = N / ((mm) ** 2)
GPa = kilo * MPa
kPa = kilo * Pa
g = 9.81

# Constants for input types
TYPE_MODULE = "module"
TYPE_TITLE = "title"
TYPE_COMBOBOX = "combobox"
TYPE_COMBOBOX_CUSTOMIZED = "combobox_customized"
TYPE_TEXTBOX = "textbox"
TYPE_IMAGE = "image"
TYPE_BUTTON = "button"
TYPE_NOTE   = "note"
TYPE_CHECKBOX       = "checkbox"
TYPE_CHECKBOX_ROW   = "checkbox_row"
TYPE_CHECKBOX_GRID  = "checkbox_grid"
TYPE_PERCENT_BAR = "percent_bar"
TYPE_ONLY_BUTTON = "only_button"
TYPE_RADIO_GRID = "radio_button_grid"

# Keys for inputs (consistent dot notation for object names)
KEY_MODULE = "Module"
KEY_STRUCTURE_TYPE = "structure.type"
KEY_PROJECT_LOCATION = "project.location"
KEY_SPAN = "geometry.span"
KEY_CARRIAGEWAY_WIDTH = "geometry.carriageway_width"
KEY_INCLUDE_MEDIAN = "geometry.include_median"
KEY_FOOTPATH = "geometry.footpath"
KEY_SKEW_ANGLE = "geometry.skew_angle"
KEY_ADDITIONAL_GEOMETRY = "geometry.additional_btn"
KEY_DESIGN_MODE = "geometry.design_mode"
KEY_GIRDER = "material.girder"
KEY_CROSS_BRACING = "material.cross_bracing"
KEY_END_DIAPHRAGM = "material.end_diaphragm"
KEY_DECK = "Deck"
KEY_DECK_CONCRETE_GRADE_BASIC = "material.deck_concrete_grade"

# ── Output section keys ───────────────────────────────────────────────────────
KEY_SECTION_OUTPUT_ANALYSIS       = "section.output.analysis"
KEY_SECTION_OUTPUT_SUPERSTRUCTURE = "section.output.superstructure"
KEY_SECTION_OUTPUT_SUBSTRUCTURE   = "section.output.substructure"
KEY_SECTION_OUTPUT_STEELDESIGN = "section.output.superstructure.steeldesign"

# ── Output field keys ─────────────────────────────────────────────────────────
KEY_ANALYSIS_MEMBER           = "analysis.member"
KEY_ANALYSIS_LOAD_COMBINATION = "analysis.load_combination"
KEY_ANALYSIS_FORCES           = "analysis.forces"
KEY_ANALYSIS_DISPLAY_OPTIONS  = "analysis.display_options"
KEY_ANALYSIS_UTILIZATION      = "analysis.utilization"

KEY_STEELDESIGN_MEMBER_ID = "steeldesign.member_id"
KEY_STEELDESIGN_LOAD_COMBINATION = "steeldesign.load_combination"

KEY_BTN_STEEL_DESIGN          = "btn.steel_design"
KEY_BTN_DECK_DESIGN           = "btn.deck_design"

KEY_UTIL_FLEXURE             = "util.flexure"
KEY_UTIL_SHEAR               = "util.shear"
KEY_UTIL_INTERACTION         = "util.interaction"
KEY_UTIL_LTB                 = "util.ltb"
KEY_UTIL_LONG_TRANS_SHEAR    = "util.long_trans_shear"
KEY_UTIL_FATIGUE             = "util.fatigue"
KEY_UTIL_STRESS_LIMITATION   = "util.stress_limitation"
KEY_UTIL_DEFLECTION_CRACK    = "util.deflection_crack"

# Module + section identifiers (also used as UI keys)
KEY_MODULE_PLATE_GIRDER = "module.plate_girder"
KEY_SECTION_STRUCTURE = "section.structure"
KEY_SECTION_PROJECT      = "section.project"
KEY_SECTION_GEOMETRIC = "section.geometry"
KEY_SECTION_ADDITIONAL_GEOMETRY = "section.additonal_geometry"
KEY_SECTION_DESIGN_TYPE  = "section.design_type"
KEY_SECTION_MATERIAL = "section.material"

# Display names
DISP_TITLE_STRUCTURE = "Type of Structure"
KEY_DISP_STRUCTURE_TYPE = "Structure Type"
DISP_TITLE_PROJECT = "Project Location"
KEY_DISP_PROJECT_LOCATION = "City in India*"
DISP_TITLE_GEOMETRIC = "Geometric Details"
KEY_DISP_SPAN = "Span (m)"
KEY_DISP_CARRIAGEWAY_WIDTH = "Carriageway Width\n(Each way) (m)"
KEY_DISP_FOOTPATH = "Footpath"
KEY_DISP_SKEW_ANGLE = "Skew Angle (deg)"
DISP_TITLE_MATERIAL = "Material Inputs"
KEY_DISP_GIRDER = "Girder"
KEY_DISP_CROSS_BRACING = "Cross Bracing"
KEY_DISP_END_DIAPHRAGM = "End Diaphragm"
KEY_DISP_DECK_CONCRETE_GRADE = "Deck"

# Sample values
VALUES_STRUCTURE_TYPE = ["Highway Bridge", "Other"]

# Canonical footpath options used across UI + CAD/code clauses.
VALUES_FOOTPATH = ["None", "Single Side", "Both Sides"]

# Validation limits
SPAN_MIN = 20.0
SPAN_MAX = 45.0
CARRIAGEWAY_WIDTH_MIN = 4.25
CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN = 7.5
CARRIAGEWAY_WIDTH_MAX_LIMIT = 23.6
SKEW_ANGLE_MIN = -15.0
SKEW_ANGLE_MAX = 15.0
SKEW_ANGLE_DEFAULT = 0.0

# ===== Additional Inputs Constants =====

# Typical Section Details Keys
KEY_GIRDER_SPACING = "Girder Spacing"
KEY_DECK_OVERHANG = "Deck Overhang Width"
KEY_NO_OF_GIRDERS = "No. of Girders"
KEY_DECK_THICKNESS = "Deck Thickness"
KEY_DECK_CONCRETE_GRADE = "Deck Concrete Grade"
KEY_DECK_REINF_MATERIAL = "Deck Reinforcement Material"
KEY_DECK_REINF_SIZE = "Deck Reinforcement Size"
KEY_DECK_REINF_SPACING_LONG = "Deck Reinforcement Spacing Longitudinal"
KEY_DECK_REINF_SPACING_TRANS = "Deck Reinforcement Spacing Transverse"
KEY_FOOTPATH_WIDTH = "Footpath Width"
KEY_FOOTPATH_THICKNESS = "Footpath Thickness"
KEY_RAILING_PRESENT = "Railing Present"
KEY_RAILING_WIDTH = "Railing Width"
KEY_RAILING_HEIGHT = "Railing Height"
KEY_RAILING_MIN_HEIGHT = [1100, 1250]
KEY_CYCLE_TRACK = ["None", "Single", "Both Sides"]
KEY_MIN_SKEW_ANGLE = 30
KEY_MIN_LOGITUDINAL_GRADIENT = 0.3
KEY_MAX_BRIDGE_LENGTH_SINGLE_CURVE = 30
KEY_MIN_SINGLE_LANE = 4.25
KEY_MIN_DOUBLE_LANE = 7.5
KEY_ADDITIONAL_LANE = 3.5

KEY_SAFETY_KERB_PRESENT = "Safety Kerb Present"
KEY_SAFETY_KERB_WIDTH = "Safety Kerb Width"
KEY_SAFETY_KERB_THICKNESS = "Safety Kerb Thickness"
KEY_SAFETY_KERB_MIN_WIDTH = 750
KEY_SAFETY_KERB_PLACEMENT = ["Single Side", "Both Sides"]

KEY_CRASH_BARRIER_PRESENT = "Crash Barrier Present"
KEY_CRASH_BARRIER_DENSITY = "Crash Barrier Material Density"
KEY_CRASH_BARRIER_WIDTH = "Crash Barrier Width"
KEY_CRASH_BARRIER_AREA = "Crash Barrier Area"

# Typical Section - Crash Barrier Type Keys
KEY_CB_TAB = "typical_section.crash_barrier.tab"
KEY_CB_TYPE = "typical_section.crash_barrier.type"
KEY_CB_DENSITY = "typical_section.crash_barrier.density"
KEY_CB_WIDTH = "typical_section.crash_barrier.width"
KEY_CB_HEIGHT = "typical_section.crash_barrier.height"
KEY_CB_AREA = "typical_section.crash_barrier.area"
KEY_CB_LOAD = "typical_section.crash_barrier.load"
KEY_CB_POST_SPACING = "typical_section.crash_barrier.post_spacing"

# Typical Section - Median (UI object names / schema ids)
KEY_MD_TAB = "typical_section.median.tab"
KEY_MD_TYPE = "typical_section.median.type"
KEY_MD_DENSITY = "typical_section.median.density"
KEY_MD_WIDTH = "typical_section.median.width"
KEY_MD_HEIGHT = "typical_section.median.height"
KEY_MD_AREA = "typical_section.median.area"
KEY_MD_LOAD = "typical_section.median.load"
KEY_MD_POST_SPACING = "typical_section.median.post_spacing"

# Typical Section - Railing
KEY_RL_TAB = "typical_section.railing.tab"
KEY_RL_TYPE = "typical_section.railing.type"
KEY_RL_WIDTH = "typical_section.railing.width"
KEY_RL_HEIGHT = "typical_section.railing.height"
KEY_RL_LOAD_MODE = "typical_section.railing.load_mode"
KEY_RL_LOAD_VALUE = "typical_section.railing.load_value"

# Typical Section - Wearing course
KEY_WC_TAB = "typical_section.wearing_course.tab"
KEY_WC_MATERIAL = "typical_section.wearing_course.material"
KEY_WC_DENSITY = "typical_section.wearing_course.density"
KEY_WC_THICKNESS = "typical_section.wearing_course.thickness"

# Typical Section - primary fields (above subtab bar)
KEY_TS_TAB                = "typical_section.tab"
KEY_TS_DECK_TAB           = "typical_section.deck_details.tab"
KEY_TS_GIRDER_SPACING     = "typical_section.girder_spacing"
KEY_TS_NO_OF_GIRDERS      = "typical_section.no_of_girders"
KEY_TS_DECK_OVERHANG      = "typical_section.deck_overhang"
KEY_TS_OVERALL_WIDTH      = "typical_section.overall_bridge_width"
KEY_TS_DECK_THICKNESS     = "typical_section.deck_thickness"
KEY_TS_FOOTPATH_WIDTH     = "typical_section.footpath_width"
KEY_TS_FOOTPATH_THICKNESS = "typical_section.footpath_thickness"

# Typical Section - Lane Deatils
KEY_WC_LD_TAB = "typical_section.lane_details.tab"
KEY_WC_LD_LANE_TABLE = "typical_section.lane_details.lane_table"
KEY_WC_LD_LANE_TABLE_COUNT = "typical_section.lane_details.lane_table_count"

KEY_METALLIC_CRASH_BARRIER_TYPE = ["Single W-beam", "Double W-beam"]
KEY_RIGID_CRASH_BARRIER_TYPE = ["IRC-5R", "High Containment"]
KEY_CRASH_BARRIER_TYPE = ["Flexible", "Semi-Rigid", "Rigid"]
KEY_MEDIAN_TYPE = ["Raised Kerb", "RCC Crash Barrier", "Metallic Crash Barrier"]
KEY_FOOTPATH_CLEAR_MIN_WIDTH = 1500

# Section Properties Keys
KEY_GIRDER_TYPE = "Girder Type"
KEY_GIRDER_IS_SECTION = "Girder IS Section"
KEY_GIRDER_SYMMETRY = "Girder Symmetry"
KEY_GIRDER_TOP_FLANGE_WIDTH = "Girder Top Flange Width"
KEY_GIRDER_TOP_FLANGE_THICKNESS = "Girder Top Flange Thickness"
KEY_GIRDER_BOTTOM_FLANGE_WIDTH = "Girder Bottom Flange Width"
KEY_GIRDER_BOTTOM_FLANGE_THICKNESS = "Girder Bottom Flange Thickness"
KEY_GIRDER_DEPTH = "Girder Depth"
KEY_GIRDER_WEB_THICKNESS = "Girder Web Thickness"
KEY_GIRDER_TORSIONAL_RESTRAINT = "Torsional Restraint"
KEY_GIRDER_WARPING_RESTRAINT = "Warping Restraint"
KEY_GIRDER_WEB_TYPE = "Web Type"

KEY_STIFFENER_DESIGN_METHOD = "Stiffener Design Method"
KEY_STIFFENER_PLATE_THICKNESS = "Stiffener Plate Thickness"
KEY_STIFFENER_SPACING = "Stiffener Spacing"
KEY_LONGITUDINAL_STIFFENER = "Longitudinal Stiffener"
KEY_LONGITUDINAL_STIFFENER_THICKNESS = "Longitudinal Stiffener Thickness"

KEY_CROSS_BRACING_TYPE = "Cross Bracing Type"
KEY_CROSS_BRACING_SECTION = "Cross Bracing Section"
KEY_BRACKET_SECTION = "Bracket Section"
KEY_CROSS_BRACING_SPACING = "Cross Bracing Spacing"

KEY_END_DIAPHRAGM_TYPE = "End Diaphragm Type"
KEY_END_DIAPHRAGM_SECTION = "End Diaphragm Section"
KEY_END_DIAPHRAGM_SPACING = "End Diaphragm Spacing"

# Dead Load Keys
KEY_SELF_WEIGHT = "Self Weight"
KEY_SELF_WEIGHT_FACTOR = "Self Weight Factor"
KEY_WEARING_COAT = ["bituminous", "concrete"]
KEY_WEARING_COAT_MATERIAL = "Wearing Coat Material"
KEY_WEARING_COAT_DENSITY = "Wearing Coat Density"
KEY_WEARING_COAT_THICKNESS = "Wearing Coat Thickness"
KEY_RAILING_TYPE = ["IRC 5 RCC railing", "IRC 5 steel railing"]
KEY_RAILING_LOAD_COUNT = "No. of Railings"
KEY_RAILING_LOAD = "Railing Load"
KEY_RAILING_LOAD_LOCATION = "Railing Load Location"
KEY_CRASH_BARRIER_LOAD_COUNT = "No. of Crash Barriers"
KEY_CRASH_BARRIER_LOAD = "Crash Barrier Load"
KEY_CRASH_BARRIER_LOAD_LOCATION = "Crash Barrier Load Location"

# Live Load Keys
KEY_IRC_CLASS_A = "IRC Class A"
KEY_IRC_CLASS_70R = "IRC Class 70R"
KEY_IRC_CLASS_AA = "IRC Class AA"
KEY_IRC_CLASS_SV = "IRC Class SV"
KEY_CUSTOM_VEHICLE = "Custom Vehicle"
KEY_CUSTOM_AXLE_TYPE = "Custom Axle Type"
KEY_CUSTOM_NO_AXLES = "Custom Number of Axles"
KEY_CUSTOM_AXLE_LOAD = "Custom Axle Load"
KEY_CUSTOM_AXLE_SPACING = "Custom Axle Spacing"
KEY_CUSTOM_VEHICLE_SPACING = "Custom Vehicle Spacing"
KEY_CUSTOM_ECCENTRICITY = "Custom Eccentricity"
KEY_FOOTPATH_PRESSURE = "Footpath Pressure"
KEY_FOOTPATH_PRESSURE_VALUE = "Footpath Pressure Value"

# Support Condition Keys
KEY_LEFT_SUPPORT = "Left Support"
KEY_RIGHT_SUPPORT = "Right Support"
KEY_BEARING_LENGTH = "Bearing Length"

# Value Lists for Additional Inputs
VALUES_NO_YES = ["No", "Yes"]
VALUES_REINF_MATERIAL = ["Fe 415", "Fe 500", "Fe 550"]
VALUES_REINF_SIZE = ["8", "10", "12", "16", "20", "25", "32"]
VALUES_CRASH_BARRIER_TYPE = [
    "IRC 5 - RCC Crash Barrier",
    "IRC 5 - Steel Crash Barrier",
    "IRC 5 - Metal Beam",
    "Custom",
]
VALUES_MEDIAN_TYPE = [
    "IRC 5 - Raised Kerb",
    "IRC 5 - Flush Median",
    "Custom",
]
VALUES_GIRDER_TYPE = ["Welded", "Rolled"]
VALUES_GIRDER_SYMMETRY = ["Girder Symmetric", "Girder Unsymmetric"]
VALUES_GIRDER_SUPPORT_TYPE = [
    "Major Laterally Supported",
    "Minor Laterally Unsupported",
    "Major Laterally Unsupported",
]
VALUES_GIRDER_DESIGN_MODE = ["Optimized", "Custom"]
VALUES_GIRDER_SPAN_MODE = ["Full Length", "Custom"]
VALUES_PROFILE_SCOPE = ["All", "Custom"]
VALUES_OPTIMIZATION_MODE = ["Optimized", "Custom", "All"]
VALUES_TORSIONAL_RESTRAINT = [
    "Fully Restrained",
    "Partially Restrained - Support Connection",
    "Partially Restrained - Bearing Support",
]
VALUES_WARPING_RESTRAINT = ["Both Flanges Restrained", "No Restraint"]
VALUES_WEB_TYPE = ["Thin Web with ITS", "Thick Web without ITS"]
VALUES_STIFFENER_DESIGN = ["Simple Post Critical", "Tension Field"]
VALUES_BEARING_STIFFENER_COUNT = ["1", "2", "3", "4"]
VALUES_LONGITUDINAL_STIFFENER = ["No", "Yes and 1 stiffener", "Yes and 2 stiffeners"]
VALUES_CROSS_BRACING_TYPE = [
    "K-bracing",
    "K-bracing with top bracket",
    "X-bracing",
    "X-bracing with bottom bracket",
    "X-bracing with top and bottom brackets",
]
VALUES_END_DIAPHRAGM_TYPE = ["Cross Bracing", "Rolled Beam", "Welded Beam"]
VALUES_WEARING_COAT_MATERIAL = ["Concrete", "Bituminous", "Other"]
VALUES_RAILING_TYPE = ["IRC 5 - RCC Railing", "IRC 5 - Steel Railing", "Custom"]
VALUES_CUSTOM_AXLE_TYPE = ["Single", "Bogie"]
VALUES_FOOTPATH_PRESSURE_MODE = ["Automatic", "User-defined"]
VALUES_SUPPORT_TYPE = ["Fixed", "Pinned"]

#Sail thic
SAIL_APPROVED_THICKNESS_VALUES=[
        "8", "10", "12", "14", "16", "18", "20", "22", "25", "28", "32", "36",
        "40", "45", "50", "56", "63", "75", "80", "90", "100", "110", "120",
    ]
MIN_BEARING_STIFFENER_SPACING_MM = 50
STIFFENER_DETAILS_DEFAULTS = {
    "form_label_width": 245,
    "combo_width": 190,
    "outstand_default_text": "NA",
    "min_bearing_spacing_mm": MIN_BEARING_STIFFENER_SPACING_MM,
    "bearing_stiffeners_each_end": VALUES_BEARING_STIFFENER_COUNT[1],
    "bearing_spacing_mm": "",
    "bearing_thickness_mode": VALUES_PROFILE_SCOPE[0],
    "bearing_thickness_value": SAIL_APPROVED_THICKNESS_VALUES[0],
    "bearing_outstand_mm": "",
    "intermediate_stiffener": VALUES_NO_YES[0],
    "intermediate_spacing_mm": "NA",
    "intermediate_outstand_mm": "",
    "longitudinal_stiffener": VALUES_LONGITUDINAL_STIFFENER[0],
    "intermediate_thickness_mode": VALUES_PROFILE_SCOPE[0],
    "intermediate_thickness_value": SAIL_APPROVED_THICKNESS_VALUES[0],
    "longitudinal_thickness_mode": VALUES_PROFILE_SCOPE[0],
    "longitudinal_thickness_value": SAIL_APPROVED_THICKNESS_VALUES[0],
    "shear_buckling_method": VALUES_STIFFENER_DESIGN[0] if VALUES_STIFFENER_DESIGN else "",
}

# Defaults + validation helpers
DEFAULT_SELF_WEIGHT_FACTOR = 1.0
DEFAULT_CONCRETE_DENSITY = 25.0
DEFAULT_STEEL_DENSITY = 78.5
DEFAULT_BEARING_LENGTH = 0.0

MIN_FOOTPATH_WIDTH = 1.5
MIN_RAILING_HEIGHT = 1.0
MIN_SAFETY_KERB_WIDTH = 0.75
DEFAULT_GIRDER_SPACING = 2.5
DEFAULT_DECK_OVERHANG = 1.0
DEFAULT_CRASH_BARRIER_WIDTH = 0.5
DEFAULT_RAILING_WIDTH = 0.375
DEFAULT_CROSS_BRACING_SPACING = 3.0

# IRC helper option constants
KEY_VEHICLE = ["Class70R(W)", "Class70R(T)", "ClassA", "ClassB"]
KEY_TYPE_BRIDGE = ["Highway", "Rural"]
KEY_DESIGN_FATIGUE = ["Dont design for fatigue", "Regular Vehicles", "Heavy Vehicles"]
KEY_TYPE_FOOTWAY = ["Default", "Regular Footway", "Crowded Footway"]
FOOTWAY_LOADS = {
    "Default": 500,
    "Regular Footway": 400,
    "Crowded Footway": 500,
}
KEY_TERRAIN_TYPE = ["plain", "obstructed"]

from pathlib import Path
import sqlite3
_DB_PATH = Path(__file__).resolve().parents[1] / "data" / "ResourceFiles" / "Intg_osdag.sqlite"

def connectdb(table_name: str) -> list[str]:
    """
    Fetches all grade designations from the Grade column of the given table.

    Parameters
    ----------
    table_name : str
        Name of the table to query.

    Returns
    -------
    list[str]
        List of grade strings (e.g. ["M15", "M20", ...]).

    Raises
    ------
    LookupError
        If the database is not found or the query fails.
    """
    if not _DB_PATH.exists():
        raise LookupError(f"Material database not found at {_DB_PATH} in get_grades")

    try:
        con = sqlite3.connect(_DB_PATH)
        cur = con.cursor()
        cur.execute(f'SELECT Grade FROM {table_name}')
        rows = cur.fetchall()
        con.close()
        return [row[0] for row in rows]
    except sqlite3.Error as e:
        raise LookupError(f"Error querying database in connectdb(): {e}")


import platform
import os

def get_documents_folder():
    system = platform.system()

    if system == "Windows":
        # Windows: typically C:\Users\Username\Documents
        docs_path = Path.home() / "Documents"
        if not docs_path.exists():
            docs_path = Path.home() / "OneDrive" / "Documents"
    elif system == "Darwin":  # macOS
        # macOS: typically /Users/Username/Documents
        docs_path = Path.home() / "Documents"
    elif system == "Linux":
        # Linux: typically /home/username/Documents
        # Also check XDG_DOCUMENTS_DIR for custom locations
        xdg_docs = os.environ.get("XDG_DOCUMENTS_DIR")
        if xdg_docs:
            docs_path = Path(xdg_docs)
        else:
            docs_path = Path.home() / "Documents"
    else:
        # Fallback to home directory for unknown systems
        docs_path = Path.home()

    # Ensure the directory exists, otherwise fall back to home
    if not docs_path.exists():
        docs_path = Path.home()
    return str(docs_path)
