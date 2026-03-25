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

# ── Output field keys ─────────────────────────────────────────────────────────
KEY_ANALYSIS_MEMBER           = "analysis.member"
KEY_ANALYSIS_LOAD_COMBINATION = "analysis.load_combination"
KEY_ANALYSIS_FORCES           = "analysis.forces"
KEY_ANALYSIS_DISPLAY_OPTIONS  = "analysis.display_options"
KEY_ANALYSIS_UTILIZATION      = "analysis.utilization"

KEY_BTN_STEEL_DESIGN          = "btn.steel_design"
KEY_BTN_DECK_DESIGN           = "btn.deck_design"

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
KEY_DISP_SPAN = "Span*"
KEY_DISP_CARRIAGEWAY_WIDTH = "Carriageway Width*\n(Each way)"
KEY_DISP_FOOTPATH = "Footpath"
KEY_DISP_SKEW_ANGLE = "Skew Angle"
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
VALUES_GIRDER_DESIGN_MODE = ["Optimized", "Customized"]
VALUES_GIRDER_SPAN_MODE = ["Full Length", "Custom"]
VALUES_PROFILE_SCOPE = ["All", "Custom"]
VALUES_OPTIMIZATION_MODE = ["Optimized", "Customized", "All"]
VALUES_TORSIONAL_RESTRAINT = [
    "Fully Restrained",
    "Partially Restrained - Support Connection",
    "Partially Restrained - Bearing Support",
]
VALUES_WARPING_RESTRAINT = ["Both Flanges Restrained", "No Restraint"]
VALUES_WEB_TYPE = ["Thin Web with ITS", "Thick Web without ITS"]
VALUES_STIFFENER_DESIGN = ["Simple Post Critical", "Tension Field"]
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
DEFAULT_RAILING_WIDTH = 0.15

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

