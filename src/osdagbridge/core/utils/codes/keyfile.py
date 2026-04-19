# Unit definitions
kilo = 1e3
milli = 1e-3
N = 1
m = 1
g = 9.81
mm = milli * m
m2 = m ** 2
m3 = m ** 3
m4 = m ** 4
kN = kilo * N
t = kN * g
Pa = 1
MPa = N / ((mm) ** 2)
GPa = kilo * MPa
kPa = kilo * Pa

# Carriageway Width limits per IRC 5 Clause 104.3.1
CARRIAGEWAY_WIDTH_MIN = 4.25  # No median present
CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN = 7.5  # Each carriageway when median provided
CARRIAGEWAY_WIDTH_MAX_LIMIT = 23.6  # Current software cap (subject to change)

KEY_MIN_SINGLE_LANE = 4.25  # in meters
KEY_MIN_DOUBLE_LANE = 7.5  # in meters  
KEY_ADDITIONAL_LANE = 3.5  # in meters

# Typical Section Details Validation Constants (IRC 5)
KEY_FOOTPATH_CLEAR_MIN_WIDTH = 1500  # in mm (IRC 5 Clause 104.3.6)
KEY_SAFETY_KERB_MIN_WIDTH = 750  # in mm
KEY_RAILING_MIN_HEIGHT = [1100, 1250] # in mm
KEY_CYCLE_TRACK = ['None', 'Single', 'Both Sides'] 
KEY_FOOTPATH = ["None", "Single Side", "Both Sides"]
KEY_MIN_SKEW_ANGLE = 30  # in degrees
KEY_MIN_LOGITUDINAL_GRADIENT = 0.3  # in percent
KEY_MAX_BRIDGE_LENGTH_SINGLE_CURVE = 30  # in meters
KEY_WEARING_COAT = ['bituminous', 'concrete']
KEY_CRASH_BARRIER_TYPE = ['Flexible', 'Semi-Rigid', 'Rigid']
KEY_METALLIC_CRASH_BARRIER_TYPE = ['Single W-beam', 'Double W-beam']
KEY_RIGID_CRASH_BARRIER_TYPE = ['IRC-5R', 'High Containment']
KEY_RAILING_TYPE = ['IRC 5 RCC railing', 'IRC 5 steel railing']
KEY_MEDIAN_TYPE = [
    'Raised Kerb',
    'RCC Crash Barrier',
    'Metallic Crash Barrier'
]


# IRC 6
KEY_VEHICLE = ['Class70R(W)','Class70R(T)','ClassA','ClassB']
KEY_TYPE_BRIDGE = ['Highway','Rural']
KEY_DESIGN_FATIGUE = ['Dont design for fatigue','Regular Vehicles','Heavy Vehicles']
KEY_TYPE_FOOTWAY = ['Default','Regular Footway','Crowded Footway']

# Characteristic loads for footway types (kg/m^2)
FOOTWAY_LOADS = {
	'Default': 500,
	'Regular Footway': 400,
	'Crowded Footway': 500,
}

KEY_TERRAIN_TYPE = ['plain','obstructed']


# Skew Angle: IRC 24 (2010) requires detailed analysis when skew angle exceeds ±15 degrees
# Default: 0 degrees
SKEW_ANGLE_MIN = -15.0
SKEW_ANGLE_MAX = 15.0
SKEW_ANGLE_DEFAULT = 0.0


# IRC 22 

# Section & fabrication types
KEY_SECTION_FABRICATION = ["rolled", "welded"]

KEY_SECTION_CLASS = [
    "plastic",
    "compact",
    "semi-compact",
    "slender"
]

KEY_SECTION_TYPE = [
    "i_major",
    "i_minor",
    "rhs",
    "chs"
]

#  Material safety factors (Table 1)
GAMMA_M0_STEEL = 1.10
GAMMA_M1_STEEL_ULTIMATE = 1.25
GAMMA_M_REINFORCEMENT = 1.15
GAMMA_M_SHEAR_CONCRETE = 1.25
GAMMA_M_WELD_SHOP = 1.25
GAMMA_M_WELD_FIELD = 1.50

#  Annex III Structural Steel
E_STEEL_MPA = 2.0e5
G_STEEL_MPA = 0.77e5
POISSON_RATIO_STEEL = 0.30

# Coefficient of Thermal Expansion (COTE)
COTE_STEEL_PER_C = 11.7e-6

# Shear connector detailing limits
MIN_STUD_HEIGHT_MM = 100
MIN_STUD_HEIGHT_FACTOR = 4        # h ≥ 4d
MAX_STUD_DIAMETER_FACTOR = 2      # d ≤ 2tf
MIN_EDGE_DISTANCE_MM = 25
MIN_STUD_HEAD_FACTOR = 1.5

# IS 875 Pt 1 / IRC 6:2017 Cl.203 — material densities (kN/m³) for dead-load calculation.
DEFAULT_STEEL_DENSITY = 78.5         # structural steel (rolled / welded plate)
DEFAULT_CONCRETE_DENSITY = 25.0      # reinforced / wet concrete
DEFAULT_BITUMINOUS_DENSITY = 24.0    # bituminous wearing course

# IRC 6:2017 Cl.204.4 Table 6A — multi-lane live-load reduction factors (1st, 2nd, 3rd+ lanes).
LANE_REDUCTION_FACTORS = [1.0, 0.8, 0.4]

# IRC 22:2015 Cl.605 Table 3 — partial safety factor for fatigue strength.
GAMMA_MFT_FATIGUE = 1.35

# Design Capacity Ratio thresholds (PASS < DCR_PASS_THRESHOLD ≤ WARN < DCR_FAIL_THRESHOLD ≤ FAIL).
DCR_PASS_THRESHOLD = 0.90
DCR_FAIL_THRESHOLD = 1.00

