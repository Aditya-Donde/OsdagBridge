# Constants for input types
TYPE_MODULE = "module"
TYPE_TITLE = "title"
TYPE_COMBOBOX = "combobox"
TYPE_COMBOBOX_CUSTOMIZED = "combobox_customized"
TYPE_TEXTBOX = "textbox"
TYPE_IMAGE = "image"

# Keys for inputs
KEY_MODULE = "Module"
KEY_STRUCTURE_TYPE = "Structure Type"
KEY_PROJECT_LOCATION = "Project Location"
KEY_SPAN = "Span"
KEY_CARRIAGEWAY_WIDTH = "Carriageway Width"
KEY_INCLUDE_MEDIAN = "Include Median"
KEY_FOOTPATH = "Footpath"
KEY_SKEW_ANGLE = "Skew Angle"
KEY_GIRDER = "Girder"
KEY_CROSS_BRACING = "Cross Bracing"
KEY_END_DIAPHRAGM = "End Diaphragm"
KEY_DECK = "Deck"
KEY_DECK_CONCRETE_GRADE_BASIC = "Deck Concrete Grade"

# Display names
KEY_DISP_FINPLATE = "Highway Bridge Design"
DISP_TITLE_STRUCTURE = "Type of Structure"
KEY_DISP_STRUCTURE_TYPE = "Structure Type"
DISP_TITLE_PROJECT = "Project Location"
KEY_DISP_PROJECT_LOCATION = "City in India*"
DISP_TITLE_GEOMETRIC = "Geometric Details"
KEY_DISP_SPAN = "Span (m)* [20-45]"
KEY_DISP_CARRIAGEWAY_WIDTH = "Carriageway Width (m)* [≥4.25]"
KEY_DISP_FOOTPATH = "Footpath"
KEY_DISP_SKEW_ANGLE = "Skew Angle (degrees) [±15]"
DISP_TITLE_MATERIAL = "Material Inputs"
KEY_DISP_GIRDER = "Girder"
KEY_DISP_CROSS_BRACING = "Cross Bracing"
KEY_DISP_END_DIAPHRAGM = "End Diaphragm"
KEY_DISP_DECK = "Deck"
KEY_DISP_DECK_CONCRETE_GRADE = "Deck Concrete Grade [M25+]"

# Sample values
# Type of Structure: Defines the application of the steel girder bridge
# Currently only covers highway bridge
VALUES_STRUCTURE_TYPE = ["Highway Bridge", "Other"]

# Project Location: Cities in India for load calculations
# Organized by regions for easier navigation
VALUES_PROJECT_LOCATION = [
    "Delhi", "Mumbai", "Bangalore", "Kolkata", "Chennai", "Hyderabad",
    "Ahmedabad", "Pune", "Surat", "Jaipur", "Lucknow", "Kanpur",
    "Nagpur", "Indore", "Thane", "Bhopal", "Visakhapatnam", "Pimpri-Chinchwad",
    "Patna", "Vadodara", "Ghaziabad", "Ludhiana", "Agra", "Nashik",
    "Faridabad", "Meerut", "Rajkot", "Kalyan-Dombivali", "Vasai-Virar", "Varanasi",
    "Srinagar", "Aurangabad", "Dhanbad", "Amritsar", "Navi Mumbai", "Allahabad",
    "Ranchi", "Howrah", "Coimbatore", "Jabalpur", "Gwalior", "Vijayawada",
    "Jodhpur", "Madurai", "Raipur", "Kota", "Chandigarh", "Guwahati",
    "Custom"  # Allow custom location entry
]

# Footpath: Single sided or none or both
# Default: None
# Note: IRC 5 Clause 101.41 requires safety kerb when footpath is not present
VALUES_FOOTPATH = ["None", "Single Sided", "Both"]

VALUES_MATERIAL = [
    "E 250A", "E 250BR", "E 250B0", "E 250C",
    "E 275A", "E 275BR", "E 275B0", "E 275C",
    "E 300A", "E 300BR", "E 300B0", "E 300C",
    "E 350A", "E 350BR", "E 350B0", "E 350C",
    "E 410A", "E 410BR", "E 410B0", "E 410C",
    "E 450A", "E 450BR",
    "E 550A", "E 550BR",
    "E 600A", "E 600BR",
    "E 650A", "E 650BR"
]

# Validation limits
# Span: Between 20 to 45 meters
SPAN_MIN = 20.0
SPAN_MAX = 45.0

# Carriageway Width limits per IRC 5 Clause 104.3.1
CARRIAGEWAY_WIDTH_MIN = 4.25  # No median present
CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN = 7.5  # Each carriageway when median provided
CARRIAGEWAY_WIDTH_MAX_LIMIT = 23.6  # Current software cap (subject to change)

# Skew Angle: IRC 24 (2010) requires detailed analysis when skew angle exceeds ±15 degrees
# Default: 0 degrees
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
KEY_SAFETY_KERB_PRESENT = "Safety Kerb Present"
KEY_SAFETY_KERB_WIDTH = "Safety Kerb Width"
KEY_SAFETY_KERB_THICKNESS = "Safety Kerb Thickness"
KEY_CRASH_BARRIER_PRESENT = "Crash Barrier Present"
KEY_CRASH_BARRIER_TYPE = "Crash Barrier Type"
KEY_CRASH_BARRIER_DENSITY = "Crash Barrier Material Density"
KEY_CRASH_BARRIER_WIDTH = "Crash Barrier Width"
KEY_CRASH_BARRIER_AREA = "Crash Barrier Area"

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
KEY_WEARING_COAT_MATERIAL = "Wearing Coat Material"
KEY_WEARING_COAT_DENSITY = "Wearing Coat Density"
KEY_WEARING_COAT_THICKNESS = "Wearing Coat Thickness"
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
VALUES_YES_NO = ["No", "Yes"]
VALUES_DECK_CONCRETE_GRADE = [
    "M 25", "M 30", "M 35", "M 40", "M 45", "M 50",
    "M 55", "M 60", "M 65", "M 70", "M 75", "M 80",
    "M 85", "M 90"
]
VALUES_REINF_MATERIAL = ["Fe 415", "Fe 500", "Fe 550"]
VALUES_REINF_SIZE = ["8", "10", "12", "16", "20", "25", "32"]
VALUES_CRASH_BARRIER_TYPE = [
    "IRC 5 - RCC Crash Barrier",
    "IRC 5 - Steel Crash Barrier",
    "IRC 5 - Metal Beam",
    "Custom"
]
VALUES_MEDIAN_TYPE = [
    "IRC 5 - Raised Kerb",
    "IRC 5 - Flush Median",
    "Custom"
]
VALUES_GIRDER_TYPE = ["IS Standard Rolled Beam", "Plate Girder"]
VALUES_GIRDER_SYMMETRY = ["Symmetrical", "Unsymmetrical"]
VALUES_OPTIMIZATION_MODE = ["Optimized", "Customized", "All"]
VALUES_TORSIONAL_RESTRAINT = ["Fully Restrained", "Partially Restrained - Support Connect", "Partially Restrained - Bearing Support"]
VALUES_WARPING_RESTRAINT = ["Both Flange Restraint", "No Restraint"]
VALUES_WEB_TYPE = ["Thin Web", "Thick Web"]
VALUES_STIFFENER_DESIGN = ["Simple Post", "Tension Field"]
VALUES_CROSS_BRACING_TYPE = ["K-bracing", "K-bracing with top bracket", "X-bracing", "X-bracing with bottom bracket", "X-bracing with top and bottom brackets"]
VALUES_END_DIAPHRAGM_TYPE = ["Cross Bracing", "Rolled Beam", "Welded Beam"]
VALUES_WEARING_COAT_MATERIAL = ["Concrete", "Bituminous", "Other"]
VALUES_RAILING_TYPE = [
    "IRC 5 - RCC Railing",
    "IRC 5 - Steel Railing",
    "Custom"
]
VALUES_CUSTOM_AXLE_TYPE = ["Single", "Bogie"]
VALUES_FOOTPATH_PRESSURE_MODE = ["Automatic", "User-defined"]
VALUES_SUPPORT_TYPE = ["Fixed", "Pinned"]

# Default values
DEFAULT_SELF_WEIGHT_FACTOR = 1.0
DEFAULT_CONCRETE_DENSITY = 25.0  # kN/m³
DEFAULT_STEEL_DENSITY = 78.5  # kN/m³
DEFAULT_BEARING_LENGTH = 0.0  # mm

# Typical Section Details Validation Constants (IRC 5)
MIN_FOOTPATH_WIDTH = 1.5  # meters (IRC 5 Clause 104.3.6)
MIN_RAILING_HEIGHT = 1.0  # meters (IRC 5 Clauses 109.7.2.3 & 109.7.2.4)
MIN_SAFETY_KERB_WIDTH = 0.75  # meters (IRC 5 Clause 101.41)
DEFAULT_GIRDER_SPACING = 2.5  # meters (preliminary design assumption)
DEFAULT_DECK_OVERHANG = 1.0  # meters (preliminary design assumption)
DEFAULT_CRASH_BARRIER_WIDTH = 0.5  # meters (typical)
DEFAULT_RAILING_WIDTH = 0.15  # meters (typical)

def connectdb(table_name, popup=None):
    """Mock database connection - returns sample data"""
    if table_name == "Material":
        return VALUES_MATERIAL
    return []

