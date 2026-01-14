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

# Carriageway Width limits per IRC 5 Clause 104.3.1
CARRIAGEWAY_WIDTH_MIN = 4.25  # No median present
CARRIAGEWAY_WIDTH_MIN_WITH_MEDIAN = 7.5  # Each carriageway when median provided
CARRIAGEWAY_WIDTH_MAX_LIMIT = 23.6  # Current software cap (subject to change)
# Typical Section Details Validation Constants (IRC 5)
MIN_FOOTPATH_WIDTH = 1.5  # meters (IRC 5 Clause 104.3.6)
MIN_RAILING_HEIGHT = 1.1  # meters (IRC 5 Clauses 109.7.2.3 & 109.7.2.4)
MIN_SAFETY_KERB_WIDTH = 0.75  # meters (IRC 5 Clause 101.41)
KEY_FOOTPATH_CLEAR_MIN_WIDTH = 1500  # in mm
KEY_SAFETY_KERB_MIN_WIDTH = 750  # in mm
# Typical Section Details Keys
KEY_RAILING_MIN_HEIGHT = [1100, 1250] # in mm
KEY_CYCLE_TRACK = ['None', 'Single', 'Both Sides'] 
KEY_MIN_SKEW_ANGLE = 30  # in degrees
KEY_MIN_LOGITUDINAL_GRADIENT = 0.3  # in percent
KEY_MAX_BRIDGE_LENGTH_SINGLE_CURVE = 30  # in meters
# Metallic crash barrier sub-types
KEY_METALLIC_CRASH_BARRIER_TYPE = ['Single W-beam', 'Double W-beam']
KEY_CRASH_BARRIER_TYPE = [
    "Rigid",
    "Semi-rigid",
    "Flexible"
]

KEY_MIN_SINGLE_LANE = 4.25  # in meters
KEY_MIN_DOUBLE_LANE = 7.5  # in meters  
KEY_ADDITIONAL_LANE = 3.5  # in meters


KEY_FOOTPATH = ["None", "Single Side", "Both Sides"]
KEY_SAFETY_KERB_MIN_WIDTH = 750  # in mm
KEY_SAFETY_KERB_PLACEMENT = ['Single Side', 'Both Sides', ]
KEY_FOOTPATH_CLEAR_MIN_WIDTH = 1500  # in mm
KEY_RAILING_MIN_HEIGHT = [1100, 1250] # in mm
KEY_CYCLE_TRACK = ['None', 'Single', 'Both Sides'] 
KEY_MIN_SKEW_ANGLE = 30  # in degrees
KEY_WEARING_COAT = ['bituminous', 'concrete']
KEY_CRASH_BARRIER_TYPE = ['Flexible', 'Semi-Rigid', 'Rigid']
KEY_RAILING_TYPE = ['RCC', 'steel']
KEY_MIN_LOGITUDINAL_GRADIENT = 0.3  # in percent
KEY_MAX_BRIDGE_LENGTH_SINGLE_CURVE = 30  # in meters
KEY_RIGID_CRASH_BARRIER_TYPE = ['IRC-5R', 'High Containment']

KEY_MIN_SINGLE_LANE = 4.25  # in meters
KEY_MIN_DOUBLE_LANE = 7.5  # in meters  
KEY_ADDITIONAL_LANE = 3.5  # in meters
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

KEY_RAILING_TYPE = ['IRC 5 RCC railing','IRC 5 steel railing']
KEY_TERRAIN_TYPE = ['plain','obstructed']
KEY_METALLIC_CRASH_BARRIER_TYPE = ['Single W-beam', 'Double W-beam']
KEY_MEDIAN_TYPE = [
    'Raised Kerb',
    'RCC Crash Barrier',
    'Metallic Crash Barrier'
]








# Skew Angle: IRC 24 (2010) requires detailed analysis when skew angle exceeds ±15 degrees
# Default: 0 degrees
SKEW_ANGLE_MIN = -15.0
SKEW_ANGLE_MAX = 15.0
SKEW_ANGLE_DEFAULT = 0.0
