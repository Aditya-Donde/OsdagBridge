from osdagbridge.core.utils.codes.irc5_2015 import IRC5_2015
from osdagbridge.core.utils.codes.keyfile import *
import math
import numpy as np
from osdagbridge.core.utils.codes.keyfile import *
from osdagbridge.core.utils.codes.irc5_2015 import IRC5_2015



class IRC6_2017:
    @staticmethod
    def cl_203_dead_load():
        # Clause 203 Dead Load
        """Returns dead load values for various materials in t/m3 as per IRC:6-2017 Clause 203."""
        dead_load = {}
        dead_load['ashlar_granite'] = 2.7  # t/m3
        dead_load['ashlar_sandstone'] = 2.4  # t/m3
        dead_load['stone_setts_granite'] = 2.6  # t/m3
        dead_load['stone_setts_basalt'] = 2.7  # t/m3
        dead_load['ballast_granite'] = 1.4  # t/m3
        dead_load['ballast_basalt'] = 1.6  # t/m3
        dead_load['brickwork_pressed_cement'] = 2.2  # t/m3
        dead_load['brickwork_common_cement'] = 1.9  # t/m3
        dead_load['brickwork_common_lime'] = 1.8  # t/m3
        dead_load['concrete_asphalt'] = 2.2  # t/m3
        dead_load['concrete_bitumen'] = 1.4  # t/m3
        dead_load['concrete_cement_plain'] = 2.5  # t/m3
        dead_load['concrete_cement_plain_plums'] = 2.5  # t/m3
        dead_load['concrete_cement_reinforced'] = 2.5  # t/m3
        dead_load['concrete_cement_prestressed'] = 2.5  # t/m3
        dead_load['concrete_lime_brick'] = 1.9  # t/m3
        dead_load['concrete_lime_stone'] = 2.1  # t/m3
        dead_load['earth_compacted'] = 2.0  # t/m3
        dead_load['gravel'] = 1.8  # t/m3
        dead_load['macadam_binder'] = 2.2  # t/m3
        dead_load['macadam_rolled'] = 2.6  # t/m3
        dead_load['sand_loose'] = 1.7  # t/m3
        dead_load['sand_wet'] = 1.9  # t/m3
        dead_load['rubble_stone_coursed'] = 2.6  # t/m3
        dead_load['stone_masonry_lime'] = 2.4  # t/m3
        dead_load['water'] = 1.0  # t/m3
        dead_load['wood'] = 0.8  # t/m3
        dead_load['cast_iron'] = 7.2  # t/m3
        dead_load['wrought_iron'] = 7.7  # t/m3
        dead_load['steel'] = 7.8  # t/m3
        return dead_load
    
    @staticmethod
    def cl_204_1_Class70R_vehicle_wheel():
        """
        Makes an Class70R vehicle in local coordinates
        Returns a dictionary with keys:
            'x' - list of longitudinal load positions (m)
            'z' - list of transverse load positions (m)
            'wheel_loads' - list of wheel loads (kN)
        """
        # Define units
        front_gap = 0.81 * m
        axle_dist1= 3.960 * m
        axle_dist2= 1.520 * m
        gap_bogie= 2.130 * m
        bogie_axle_dist1= 1.370 * m
        bogie_axle_dist2= 3.050 * m
        rear_gap = 0.91 * m

        # Define wheel loads (kN) for each longitudinal axle position
        # Mapping to the 7 longitudinal positions in `load_positions_x`.
        # Values provided by user (converted to kN):
        # [8, 12, 12, 17, 17, 17, 17]
        wheel_loads = [8 * t, 12 * t, 12 * t, 17 * t,
                      17 * t, 17 * t, 17 * t]

        # Define longitudinal positions of each axle
        load_positions_x = [
                front_gap,
                front_gap + axle_dist1,
                front_gap + axle_dist1 + axle_dist2,
                front_gap + axle_dist1 + axle_dist2 + gap_bogie,
                front_gap + axle_dist1 + axle_dist2 + gap_bogie + bogie_axle_dist1,
                front_gap + axle_dist1 + axle_dist2 + gap_bogie + bogie_axle_dist1 + bogie_axle_dist2,
                front_gap + axle_dist1 + axle_dist2 + gap_bogie + bogie_axle_dist1 + bogie_axle_dist2 + bogie_axle_dist1,
                front_gap + axle_dist1 + axle_dist2 + gap_bogie + bogie_axle_dist1 + bogie_axle_dist2 + bogie_axle_dist1 + rear_gap,
                ]
            
        # Transverse position of each wheel
        load_positions_z = [-0.965, 0.965]

        # Spacing between two sucessive class 70R vehicles
        spacing_Class70R = 30.0 * m

        # Minimum clearance g_min between the road face of the kerb and the outer edge of the wheel or track 
        min_clearance = 1.2 * m

        # make a dictonary to return vehicle data
        return {
            'x': load_positions_x,
            'z': load_positions_z,
            'wheel_loads': wheel_loads,
            'spacing_Class70R': spacing_Class70R,
            'min_clearance': min_clearance
        }
    
    @staticmethod
    def cl_204_1_Class70R_vehicle_track():
        """
        Makes an Class70R vehicle(Track) in local coordinates
        Returns a dictionary with keys:
            'x' - list of longitudinal load positions vertex(m)
            'z' - list of transverse load positions vertex(m)
            'wheel_loads' - list of wheel loads (t)
        """
        # Define units
        start_vertex_x = 0.0 * m
        end_vertex_x = 4.570 * m

        # Define track loads (t/m) 
        track_loads_udl = 7.66 * t / m 

        # Define longitudinal positions of track vertices
        load_positions_x = [
                start_vertex_x,
                start_vertex_x + end_vertex_x,
                ]
            
        # Transverse position of each track
        load_positions_z = [-1.03, 1.03]

        # Spacing between two sucessive class 70R track vehicles
        spacing_Class70R_T = 90.0 * m

        # make a dictonary to return vehicle data
        return {
            'x': load_positions_x,
            'z': load_positions_z,
            'wheel_loads_udl': track_loads_udl,
            'spacing_Class70R(T)': spacing_Class70R_T
        }
    
    @staticmethod
    def cl_204_1_ClassA_vehicle():
        """
        Makes an ClassA vehicle in local coordinates
        Returns a dictionary with keys:
            'x' - list of longitudinal load positions (m)
            'z' - list of transverse load positions (m)
            'wheel_loads' - list of wheel loads (kN)
        """
        # Define units
        front_gap = 0.6 * m
        axle_dist1 = 1.100 * m
        axle_dist2 = 3.200 * m
        axle_dist3 = 1.200 * m
        gap_bogie = 4.300 * m
        bogie_axle_dist = 3.000 * m
        rear_gap = 0.900 * m

       # Define wheel loads (kN) for each longitudinal axle position
       # Mapping to the 8 longitudinal positions in `load_positions_x`.
       # Values provided by user (converted to kN):
       # [2.7, 2.7, 11.4, 11.4, 6.8, 6.8, 6.8, 6.8]
        wheel_loads = [2.7 * t, 2.7 * t, 11.4 * t, 11.4 * t,
                      6.8 * t, 6.8 * t, 6.8 * t, 6.8 * t]

        # Define longitudinal positions of each axle
        load_positions_x = [
            front_gap,
            front_gap + axle_dist1,
            front_gap + axle_dist1 + axle_dist2,
            front_gap + axle_dist1 + axle_dist2 + axle_dist3,
            front_gap + axle_dist1 + axle_dist2 + axle_dist3 + gap_bogie,
            front_gap + axle_dist1 + axle_dist2 + axle_dist3 + gap_bogie + bogie_axle_dist,
            front_gap + axle_dist1 + axle_dist2 + axle_dist3 + gap_bogie + bogie_axle_dist + bogie_axle_dist,
            front_gap + axle_dist1 + axle_dist2 + axle_dist3 + gap_bogie + bogie_axle_dist + bogie_axle_dist + bogie_axle_dist,
            front_gap + axle_dist1 + axle_dist2 + axle_dist3 + gap_bogie + bogie_axle_dist + bogie_axle_dist + bogie_axle_dist + rear_gap,
            ]
        # Transverse position of each wheel
        load_positions_z = [-0.9,0.9]

        # Spacing between two sucessive class A vehicles
        spacing_ClassA = 18.5 * m

        # make a dictonary to return vehicle data
        return {
            'x': load_positions_x,
            'z': load_positions_z,
            'wheel_loads': wheel_loads,
            'spacing_ClassA': spacing_ClassA
        }
    
    

    @staticmethod
    def table_3(carriageway_width):
        """
        IRC:6-2017 Table 3  Minimum clearance for Class A vehicle

        Returns allowable clearance values.
        """
        if carriageway_width < 0:
            raise ValueError("Carriageway width cannot be negative")

        f = 0.15  # meters (150 mm)

        # Get number of design lanes from Table 6
        design_lanes = IRC6_2017.table_6(carriageway_width)  # replace IRC with your class name if needed

        # Single-lane carriageway
        if design_lanes == 1:
            g = (0.0, 0.0)

        # Multi-lane carriageway
        elif 5.3 <= carriageway_width <= 6.1:
            g = (0.4, 1.2)  # allowable range

        else:  # > 6.1 m
            g = (1.2, 1.2)  # fixed value

        return {
            "g_min": g[0],
            "g_max": g[1],
            "f": f
        }

    @staticmethod
    def table_6(carriageway_width):
        """
        Determines the number of lanes for design purposes based on carriageway width
        as per IRC:6-2017 Table 6.
        
        Args:
            carriageway_width (float): The carriageway width (CW) in meters
            
        Returns:
            int: Number of lanes for design purposes
            
        Raises:
            ValueError: If the carriageway width is negative
        """
        if carriageway_width < 0:
            raise ValueError("Carriageway width cannot be negative")

        # Determine the number of lanes for design purposes based on ranges
        # Assign to variable `lanes` (so other functions can use it)
        if carriageway_width < 5.3:
            design_lanes = 1
        elif carriageway_width < 9.6:
            design_lanes = 2
        elif carriageway_width < 13.1:
            design_lanes = 3
        elif carriageway_width < 16.6:
            design_lanes = 4
        elif carriageway_width < 20.1:
            design_lanes = 5
        elif carriageway_width < 23.6:
            design_lanes = 6
        else:
            # For widths >= 23.6m, extrapolate using the same pattern
            # Each additional ~3.5 m adds one lane (approximate rule)
            additional_width = carriageway_width - 20.1
            additional_lanes = math.ceil(additional_width / 3.5)
            design_lanes = 6 + additional_lanes

        return int(design_lanes)

    @staticmethod
    def table_6A(carriageway_width):
        """
        IRC:6-2017 Table 6A
        Returns all permissible vehicle combinations for a given carriageway width.

        Each Class A vehicle occupies 1 lane.
        Each Class 70R vehicle occupies 2 lanes.
        """

        if carriageway_width <= 0:
            raise ValueError("Invalid carriageway width")

        # Step 1: get design lanes from Table 6
        design_lanes = IRC6_2017.table_6(carriageway_width)

        combinations = []

        # Step 2: generate all valid combinations
        max_70R = design_lanes // 2

        for n70R in range(max_70R + 1):
            nA = design_lanes - 2 * n70R
            if nA >= 0:
                combo = {}
                if nA > 0:
                    combo["ClassA"] = nA
                if n70R > 0:
                    combo["Class70R"] = n70R
                combinations.append(combo)

        return {
            "design_lanes": design_lanes,
            "vehicle_combinations": combinations
        }

    
    @staticmethod
    def table_7(span: float) -> float:
        """
        Returns the congestion factor for a given bridge span (in metres) as per Table 7 (image attached).

        Rules implemented:
        - For span <= 10 m: raises ValueError (table applies to spans above 10 m)
        - For 10 < span <= 30 m: congestion factor = 1.15 (constant)
        - For spans between the listed breakpoints (30,40,50,60,70) the congestion
          factor is linearly interpolated between the corresponding values.
        - For span >= 70 m: congestion factor = 1.70 (constant)

        Breakpoints used (span_m -> factor):
            30 -> 1.15
            40 -> 1.30
            50 -> 1.45
            60 -> 1.60
            70 -> 1.70

        Args:
            span (float): bridge span in metres

        Returns:
            float: congestion factor (rounded to 3 decimal places)
        """
        if span is None:
            raise ValueError("Span must be provided (in metres)")

        try:
            s = float(span)
        except Exception:
            raise ValueError("Span must be a number")

        if s <= 10.0:
            raise ValueError("Table 7 applies to spans above 10 m")

        # constant for upto 30 m
        if s <= 30.0:
            return round(1.15, 3)

        # constant for beyond 70 m
        if s >= 70.0:
            return round(1.70, 3)

        # Breakpoints for interpolation
        breakpoints = [
            (30.0, 1.15),
            (40.0, 1.30),
            (50.0, 1.45),
            (60.0, 1.60),
            (70.0, 1.70),
        ]

        # find interval that contains s
        for i in range(len(breakpoints) - 1):
            x0, y0 = breakpoints[i]
            x1, y1 = breakpoints[i + 1]
            if x0 <= s <= x1:
                # linear interpolation
                t = (s - x0) / (x1 - x0) if x1 != x0 else 0.0
                val = y0 + t * (y1 - y0)
                return round(val, 3)

        # fallback (should not reach here) - return nearest endpoint
        if s < breakpoints[0][0]:
            return round(breakpoints[0][1], 3)
        return round(breakpoints[-1][1], 3)
    
    @staticmethod
    def cl_204_6_fatigue_load():
        """
        Makes an Fatigue truck vehicle in local coordinates
        Returns a dictionary with keys:
            'x' - list of longitudinal load positions (m)
            'z' - list of transverse load positions (m)
            'wheel_loads' - list of wheel loads (t)
        """
        # Define units
        axle_dist1= 4.50 * m
        axle_dist2= 1.40 * m
   

        # Define wheel loads (t) for each longitudinal axle position
        # Mapping to the 3 longitudinal positions in `load_positions_x`.
        # Values provided by user (converted to t):
        # [12, 14, 14]
        wheel_loads = [12 * t, 14 * t, 14 * t]

        # Define longitudinal positions of each axle
        load_positions_x = [
                0,
                axle_dist1,
                axle_dist1 + axle_dist2,
                ]
            
        # Transverse position of each wheel
        load_positions_z = [-0.840, 0.840]

        if KEY_DESIGN_FATIGUE[2]:
            fatigue_cycles = 10 * 10**6
        elif KEY_DESIGN_FATIGUE[1]:
            fatigue_cycles = 2 * 10 **6
        elif KEY_TYPE_BRIDGE[1]:
            fatigue_cycles = 0

        # make a dictonary to return vehicle data
        return {
            'x': load_positions_x,
            'z': load_positions_z,
            'wheel_loads': wheel_loads,
            'fatigue_cycles': fatigue_cycles
        }
    
    @staticmethod
    def cl_206_1_footway_load():
        """
        Returns the footway load in kg/m2 based on the selected footway type
        as per IRC:6-2017 Clause 206.1.
        """
        footway_type = KEY_TYPE_FOOTWAY[0]

        # Get the load in kg/m2 from the FOOTWAY_LOADS dictionary
        load_kg_m2 = FOOTWAY_LOADS.get(footway_type, 500)  # default to 500 kg/m2 if not found

        # Convert load to kN/m2
        load_kN_m2 = (load_kg_m2 * 9.81) / 1000.0  # kN/m2

        return round(load_kN_m2, 3)
    
    @staticmethod
    def cl_206_2_kerb_load():
        """
        IRC:6-2017 Clause 206.2
        Kerb load based on kerb width (obtained from IRC5)

        @author: Sweta Pal
        """

        # Get kerb data from IRC5
        kerb_data = IRC5_2015.cl_109_8_1_road_kerb_outline({})

        kerb_width_mm = kerb_data.get("road_kerb_width", 0)

        # Default footway load
        footway_load_kg_m2 = FOOTWAY_LOADS.get("Default", 500)

        # Apply condition
        kerb_load_kg_m2 = footway_load_kg_m2 if kerb_width_mm >= 600 else 0

        # Convert to kN/m2
        kerb_kN_m2 = (kerb_load_kg_m2 * 9.81) / 1000.0

        return {
            "kerb_width_mm": kerb_width_mm,
            "kerb_load_kN_per_m2": round(kerb_kN_m2, 3),
            "clause": "IRC 6:2017 - 206.2"
        }


    @staticmethod
    def cl_206_6_crash_barrier_load():
        """
        IRC:6-2017 Clause 206.6 — Crash Barrier Load.

        A horizontal load of 7.5 kN/m is applied at 1.0 m above the deck
        surface for design of the deck overhang and crash barrier anchorage.

        Returns
        -------
        dict
            horizontal_load_kN_per_m : float  — 7.5 kN/m
            height_m                 : float  — 1.0 m above deck surface
            moment_at_base_kNm_per_m : float  — 7.5 kNm/m (= 7.5 × 1.0)
            clause                   : str
        """
        horizontal_load = 7.5   # kN/m
        height_m = 1.0           # m above deck surface
        return {
            "horizontal_load_kN_per_m" : horizontal_load,
            "height_m"                 : height_m,
            "moment_at_base_kNm_per_m" : horizontal_load * height_m,
            "clause"                   : "IRC 6:2017 - 206.6",
        }

    @staticmethod
    def cl_206_5_railing_load():
        """
        Returns the parapet load in kg/m based on the parapet type
        as per IRC:6-2017 Clause 206.5.
        """
        if KEY_RAILING_TYPE[0] == 'IRC 5 RCC railing':
            railing_load_kg_m2 = 150.0  # kg/m
        elif KEY_RAILING_TYPE[0] == 'IRC 5 steel railing':
            railing_load_kg_m2 = 150.0  # kg/m

        return round(railing_load_kg_m2, 3)
    
    @staticmethod
    def cl_208_2_impact_factor(span):
        """
        Returns the impact factor (IM) for Class A or Class B loading 
        according to IRC:6-2017 Clause 208.2.

        Parameters:
            span (float): span in metres

        Returns:
            float: impact factor (IM)
        """
        if span < 3.0: #span less than 3 m
            span = 3.0
            IM = 9.0/(13.5 + span)
        elif 3.0 <= span <= 45.0: #span between 3 m and 45 m
            IM = 9.0/(13.5 + span)
        else: #span greater than 45 m
            span = 45.0
            IM = 9.0/(13.5 + span)

        return round(IM, 3)
    
    @staticmethod
    def cl_208_3_impact_factor(span):
        """
        Returns the impact factor (IM) for Class AA and Class 70R loading 
        according to IRC:6-2017 Clause 208.3.

        Parameters:
            span (float): span in metres
        Returns:
            float: impact factor (IM)
        """
        if span < 9.0: #span less than 9 m
            if KEY_VEHICLE[1]: # Class70R(T)
                if span < 5.0:
                    IM = 0.25
                if span >= 5.0:
                    IM = 0.10
            elif KEY_VEHICLE[0]: # Class70R(W)
                IM = 0.25
        
        elif 9.0 <= span <= 45.0: #span between 9 m and 45 m
            if KEY_VEHICLE[1]: # Class70R(T)
                IM = 0.10
            elif KEY_VEHICLE[0]: # Class70R(W)
                if span < 23.0:
                    IM = 0.25
                if span >= 23.0:
                    IM = 9.0/(13.5 + span)
        else: #span greater than 45 m
            span = 45.0
            IM = 9.0/(13.5 + span)
        
        return round(IM, 3)
            
    
    @staticmethod
    def table_12(height, terrain, basic_wind_speed=33):
        """
        Returns wind speed (Vz) and wind pressure (Pz) according to IRC:6-2017 Table 12,
        including interpolation and scaling for arbitrary basic wind speed.

        Parameters:
            height (float): height H in meters
            terrain (str): "plain" or "obstructed"
            basic_wind_speed (float): local basic wind speed Vb (m/s)

        Returns:
            dict: {"Vz": scaled_hourly_mean_speed, "Pz": scaled_horizontal_pressure}
        """

        # Base table for Vb = 33 m/s
        table = {
            "plain": {
                10: (27.80, 463.70),
                15: (29.20, 512.50),
                20: (30.30, 550.60),
                30: (31.40, 590.20),
                50: (33.10, 659.20),
                60: (33.60, 676.30),
                70: (34.00, 693.60),
                80: (34.40, 711.20),
                100: (35.30, 747.00)
            },
            "obstructed": {
                10: (17.80, 190.50),
                15: (19.60, 230.50),
                20: (21.00, 265.30),
                30: (22.80, 312.20),
                50: (24.90, 373.40),
                60: (25.60, 392.90),
                70: (26.20, 412.80),
                80: (26.90, 433.30),
                100: (28.20, 475.60)
            }
        }

        if terrain not in table:
            raise ValueError("terrain must be 'plain' or 'obstructed'")

        # Extract terrain data
        terrain_table = table[terrain]

        # Clamp height to 10 m minimum as per "Up to 10 m"
        if height <= 10:
            Vz_33, Pz_33 = terrain_table[10]
        else:
            # Sort heights for interpolation
            heights = sorted(terrain_table.keys())

            # If exact match exists
            if height in heights:
                Vz_33, Pz_33 = terrain_table[height]
            else:
                # Find bounding heights
                lower = max(h for h in heights if h < height)
                upper = min(h for h in heights if h > height)

                # Linear interpolation
                V_low, P_low = terrain_table[lower]
                V_high, P_high = terrain_table[upper]
                ratio = (height - lower) / (upper - lower)

                Vz_33 = V_low + ratio * (V_high - V_low)
                Pz_33 = P_low + ratio * (P_high - P_low)

        # IRC:6-2017 Cl.209.2: for Vb ≠ 33 m/s, scale Table 12 values by Vb/33 (speed) and (Vb/33)² (pressure)
        Vb = basic_wind_speed
        Vz_scaled = Vz_33 * (Vb / 33)
        Pz_scaled = Pz_33 * (Vb / 33) ** 2

        return {"Vz": Vz_scaled, "Pz": Pz_scaled}

    @staticmethod
    def cl_209_3_3_transverse_wind_load(
            span,
            railing_height,
            crash_barrier_height,
            deck_thickness,
            openings_in_railing,
            height_for_pz,
            terrain,
            basic_wind_speed,
            girder_section,
            number_of_girders,
            c_spacing=None,
            b_width=None,
            d_depth=None
    ):
        """
        Computes total transverse wind force as per IRC:6-2017 Clause 209.3.3.

        Formula: FT = Pz × A1 × G × CD  (in Newtons, total force)

        Parameters:
            span (float): span length in metres. (KEY_SPAN)
            railing_height (float): height of railing in m. (KEY_RAILING_HEIGHT)
                Set to 0 if crash barrier is used instead.
            crash_barrier_height (float): height of crash barrier in m.
                Set to 0 if railing is used instead.
            deck_thickness (float): thickness of deck slab in m. (KEY_DECK_THICKNESS)
            openings_in_railing (float): net openings in railing in m (use 0 if solid/unknown).
            height_for_pz (float): height at which Pz is evaluated via Table 12, in m.
            terrain (str): "plain" or "obstructed".
            basic_wind_speed (float): basic wind speed V_b in m/s.
            girder_section (str): "slab", "plate", or "rolled".
            number_of_girders (int): number of girders. (KEY_NO_OF_GIRDERS)
            c_spacing (float, optional): centre-to-centre spacing of adjacent girders in m.
                (KEY_GIRDER_SPACING) Required for plate girders (n≥2) and rolled beams (n≥2).
            b_width (float, optional): width of beam/box section in m.
                Required for rolled single and rolled multiple cases.
            d_depth (float, optional): depth of windward girder in m. (KEY_MP_GIRDER_DEPTH)
                Required for all beam/girder cases except single plate.

        Returns:
            dict: {"A1": m², "Pz": N/m², "G": dimensionless, "CD": dimensionless, "FT": N}
        """
        # ------------------------------------------------------------------
        # 1. A1 — total projected solid area (m²)  [IRC:6-2017 Cl.209.3.2]
        # ------------------------------------------------------------------
        exposed_height = (max(railing_height, crash_barrier_height)
                          + deck_thickness - openings_in_railing)
        if exposed_height < 0:
            exposed_height = 0.0
        A1 = span * exposed_height

        # ------------------------------------------------------------------
        # 2. Pz — design wind pressure (N/m²) from Table 12
        # ------------------------------------------------------------------
        Pz = IRC6_2017.table_12(height_for_pz, terrain, basic_wind_speed)["Pz"]

        # ------------------------------------------------------------------
        # 3. G — gust factor (= 2.0 for highway bridges with span ≤ 150 m)
        # ------------------------------------------------------------------
        if span <= 150.0:
            G = 2.0
        else:
            raise ValueError(
                "G for span > 150 m is not tabulated in IRC:6-2017 Cl.209.3.3. "
                "A specialist wind study is required."
            )

        # ------------------------------------------------------------------
        # 4. CD — drag coefficient
        # ------------------------------------------------------------------
        girder_section = girder_section.strip().lower()

        # Case 0: Slab bridge (b/d ≥ 10)
        if girder_section == "slab":
            CD = 1.1

        # Case 1: Single plate girder
        elif girder_section == "plate" and number_of_girders == 1:
            CD = 2.2

        # Case 2: Two or more plate girders
        # CD = 2(1 + c/20d), not more than 4.0
        # c = centre-to-centre distance of adjacent girders, d = depth of windward girder
        elif girder_section == "plate" and number_of_girders >= 2:
            if c_spacing is None or d_depth is None:
                raise ValueError(
                    "For plate girders with n >= 2, c_spacing and d_depth must be provided."
                )
            CD = min(2.0 * (1.0 + c_spacing / (20.0 * d_depth)), 4.0)

        # Case 3: Single rolled beam / box girder
        # CD interpolated between 1.5 (b/d=2) and 1.3 (b/d≥6)
        elif girder_section == "rolled" and number_of_girders == 1:
            if b_width is None or d_depth is None:
                raise ValueError(
                    "For a single rolled beam/box girder, b_width and d_depth must be provided."
                )
            bd_ratio = b_width / d_depth
            if bd_ratio <= 2.0:
                CD = 1.5
            elif bd_ratio >= 6.0:
                CD = 1.3
            else:
                CD = 1.5 + (bd_ratio - 2.0) * (1.3 - 1.5) / (6.0 - 2.0)

        # Case 4: Two or more rolled beams / box girders
        # CD = 1.5 × CD_single when clear distance / depth ≤ 7
        elif girder_section == "rolled" and number_of_girders >= 2:
            if c_spacing is None or b_width is None or d_depth is None:
                raise ValueError(
                    "For multiple rolled beams, c_spacing, b_width, and d_depth must be provided."
                )
            # Clause uses clear distance between beams (not c/c spacing)
            clear_over_depth = (c_spacing - b_width) / d_depth
            if clear_over_depth <= 7.0:
                bd_single = b_width / d_depth
                if bd_single <= 2.0:
                    CD_single = 1.5
                elif bd_single >= 6.0:
                    CD_single = 1.3
                else:
                    CD_single = 1.5 + (bd_single - 2.0) * (1.3 - 1.5) / (6.0 - 2.0)
                CD = 1.5 * CD_single
            else:
                raise ValueError(
                    f"Clear distance / depth ratio ({clear_over_depth:.3f}) exceeds 7. "
                    "IRC:6-2017 Cl.209.3.3 does not define CD beyond this limit."
                )

        else:
            raise ValueError(
                f"Invalid girder_section '{girder_section}'. "
                "Expected 'slab', 'plate', or 'rolled'."
            )

        # ------------------------------------------------------------------
        # 5. FT — total transverse wind force (N)
        # ------------------------------------------------------------------
        FT = Pz * A1 * G * CD

        # Todo: add wind force eccentricity below slab top
        return {
            "A1": A1,
            "Pz": Pz,
            "G": G,
            "CD": CD,
            "FT": FT
        }
    
    @staticmethod
    def cl_209_3_4_logitudinal_force():
        """
        Computes longitudinal wind force as per IRC:6-2017 Clause 209.3.4.
        Returns:
            float: Longitudinal wind force FL in kN (rounded to 3 decimal places)
        """
        FL = 0.25 * IRC6_2017.cl_209_3_3_transverse_wind_load()['FT']
        return round(FL, 3)
    
    @staticmethod
    def cl_209_3_5_vertical_force(carriageway_width, footpath_width, span):
        """
        Computes vertical wind force as per IRC:6-2017 Clause 209.3.5.
        Returns:
            float: Vertical wind force FV in kN (rounded to 3 decimal places)
        """
        G = IRC6_2017.cl_209_3_3_transverse_wind_load()['G']
        Pz = IRC6_2017.cl_209_3_3_transverse_wind_load()['Pz']

        A3 = span * (carriageway_width + footpath_width)
        CL = 0.75  # Lift coefficient for flat plate

        FV = Pz * A3 * G * CL
        return round(FV, 3)
    
    @staticmethod
    def cl_209_3_6_transverse_wind_load_per_unit(
            railing_height,
            crash_barrier_height,
            height_for_pz,
            terrain,
            basic_wind_speed
    ):
        """
        Computes transverse wind load per unit length on parapet/railing 
        as per IRC:6-2017 Clause 209.3.6.
        
        Args:
            railing_height (float): height of railing in metres
            crash_barrier_height (float): height of crash barrier in metres
            height_for_pz (float): height at which Pz is evaluated (Table 12)
            terrain (str): "plain" or "obstructed"
            basic_wind_speed (float): basic wind speed V_b in m/s
            
        Returns:
            float: Transverse wind load per unit length FTL in kN/m (rounded to 3 decimal places)
        """
        
        # Wind pressure from Table 12
        Pz = IRC6_2017.table_12(height_for_pz, terrain, basic_wind_speed)["Pz"]
        
        # Gust factor (constant per IRC:6 for spans ≤150m)
        G = 2.0
        
        CD = 1.2  # Drag coefficient for parapet
        
        # Determine if railing or crash barrier is present
        if KEY_RAILING_TYPE[0] or KEY_CRASH_BARRIER_TYPE[0]:
            railing_present = True
        else:
            railing_present = False

        if railing_present: 
            A1 = 3.0 - railing_height   # Area exposed to wind per unit length (m2/m)
        else:
            A1 = 3.0 - crash_barrier_height
        
        # Final transverse wind load per unit length
        FT_LL = Pz * A1 * G * CD

        # Longitudinal wind load on live load = 25% of transverse (IRC:6-2017 Cl.209.3.6)
        # Both loads applied simultaneously at 1.5 m above the roadway
        FL_LL = 0.25 * FT_LL
        application_height_m = 1.5

        return {
            'FT_LL': round(FT_LL, 3),
            'FL_LL': round(FL_LL, 3),
            'application_height_m': application_height_m,
            'clause': 'IRC 6:2017 - 209.3.6'
        }
    
    @staticmethod
    def cl_209_3_7(wind_speed):
        """
        The bridges shall not be considered to be carrying any live load when the wind 
        speed at deck level exceeds 36 m/s as per IRC:6-2017 Clause 209.3.7.
        args:
            wind_speed (float): wind speed at deck level in m/s
        Returns:
            bool: True if live load is to be considered, False otherwise
        """
        if wind_speed <= 36.0:
            live_load_considered = True
        else:
            live_load_considered = False
        
        # Todo, add this clause to load combinations
        
        return live_load_considered
    
    @staticmethod
    def cl_211_2_braking_force(design_lanes):
        """
        Returns braking force as per IRC:6-2017 Clause 211.2.
        Returns:
            float: Braking force in t (rounded to 3 decimal places)
        """
        for lane in range(1, design_lanes + 1):
            if lane == 1 or lane == 2:
                wheel_load = IRC6_2017.cl_204_1_ClassA_vehicle()['wheel_loads']
                braking_force_1 = 0.20 * sum(wheel_load)  # t
            if lane > 2:
                wheel_load = IRC6_2017.cl_204_1_Class70R_vehicle_wheel()['wheel_loads']
                braking_force_2 = 0.05 * sum(wheel_load)  # t
            
            total_braking_force = braking_force_1 + braking_force_2
        return round(total_braking_force, 3)
    
    @staticmethod
    def cl_211_3_braking_force_location():
        """
        Returns braking force application height as per IRC:6-2017 Clause 211.3.

        The force due to braking effect acts along a line parallel to the roadway
        and 1.2 m above it. While transferring the force to the bearings, the change
        in the vertical reaction at the bearings should be taken into account.

        Returns:
            dict: height_m (float) — height above roadway in metres
        """
        return {
            'height_m': 1.2,
        }
    
    
    @staticmethod
    def table_15():
        """
        Returns bridge temperature as per IRC:6-2017 Table 15.
        Returns:
            float: Bridge temperature in °C (rounded to 3 decimal places)
        """
        max_temp = None  # °C
        min_temp = None  # °C
        delta_temp = max_temp - min_temp  # °C
        if delta_temp > 20.0:
            bridge_temp = ((max_temp + min_temp) / 2.0) + 10.0 # °C
        elif delta_temp < 20.0:
            bridge_temp = ((max_temp + min_temp) / 2.0) + 5.0  # °C 
        return round(bridge_temp, 3)
    
    @staticmethod
    def cl_215_2_effective_bridge_temperature(
            max_temp: float,
            min_temp: float,
            structural_type: str = 'metallic',
            snowbound: bool = False
    ) -> dict:
        """
        Returns the range of effective bridge temperature as per IRC:6-2017 Clause 215.2.

        For metallic structures (default when type is unknown):
          - Snowbound areas : -35°C to +50°C
          - Other areas     : (min_air_shade_temp − 10°C) to (max_air_shade_temp + 15°C)

        For other (restrained) structures, Table 15 applies:
          - delta > 20°C : mean ± 10°C (whichever is critical)
          - delta < 20°C : mean ± 5°C  (whichever is critical)

        Parameters:
            max_temp (float): Maximum shade air temperature in °C (from Annexure F)
            min_temp (float): Minimum shade air temperature in °C (from Annexure F)
            structural_type (str): 'metallic' or 'other'; defaults to 'metallic' if unknown
            snowbound (bool): True if location is snowbound (metallic structures only)

        Returns:
            dict: T_min, T_max (°C), structural_type used, clause reference
        """
        stype = structural_type.strip().lower() if structural_type else 'metallic'

        if stype == 'metallic':
            if snowbound:
                T_min = -35.0
                T_max = 50.0
            else:
                # Other areas: max + 15, min - 10
                T_min = min_temp - 10.0
                T_max = max_temp + 15.0
        else:
            # Non-metallic restrained structure — Table 15
            delta = max_temp - min_temp
            mean = (max_temp + min_temp) / 2.0
            if delta > 20.0:
                T_min = mean - 10.0
                T_max = mean + 10.0
            else:
                T_min = mean - 5.0
                T_max = mean + 5.0

        return {
            'T_min': round(T_min, 3),
            'T_max': round(T_max, 3),
            'structural_type': stype,
            'clause': 'IRC 6:2017 - 215.2'
        }

    @staticmethod
    def cl_215_4_temperature_gradient(h: float, gradient_type: str = 'heating') -> dict:
        """
        Temperature gradient across bridge deck section per IRC:6-2017 Clause 215.4.

        NOTE: Clause figure assumes 50 mm surfacing on top of slab.
        h = slab (deck) thickness in metres.

        ── Heating (positive gradient) ─────────────────────────────────────────
        h₁ = 0.6 × h  (depth of upper zone from top surface)
        h₂ = 0.4 m    (depth of lower zone from soffit; fixed)

        Temperature variation (y measured downward from top surface):
          Zone 1  0 ≤ y ≤ h₁  :  T(y) = T₁ × (1 − y/h₁)^(1/4)
                  4th-root parabola — the "4" in the clause figure denotes the
                  1/4-power curve shape. T = T₁ at surface, reduces to 0 at h₁.
          Zone 2  h₁ < y < h − h₂  :  T(y) = 0
          Zone 3  h − h₂ ≤ y ≤ h   :  T(y) = 0  (no soffit temperature for heating)

        T₁ (°C) with 50 mm surfacing — from figure:
            H = 0.2 m  →  T₁ = 18.0 °C
            H = 0.3 m  →  T₁ = 20.5 °C
            (linearly interpolated for intermediate H; capped at H = 0.3 m for H ≥ 0.3 m)

        ── Cooling (negative gradient) ──────────────────────────────────────────
        h₁ = 0.6 × h  (same zone proportions as heating)
        h₂ = 0.4 m    (bottom zone; fixed)

        Temperature variation:
          Zone 1  0 ≤ y ≤ h₁  :  T(y) = T₁ × (1 − y/h₁)
                  Linear decrease — triangular profile; "8" in the clause figure
                  labels the reference temperature level at the base of h₂ zone.
                  T = T₁ at surface, reduces linearly to 0 at depth h₁.
          Zone 2  h₁ < y < h − h₂  :  T(y) = 0
          Zone 3  h − h₂ ≤ y ≤ h   :  T(y) = 0

        T₁ (°C) with 50 mm surfacing — from figure:
            H = 0.2 m  →  T₁ = 4.4 °C
            H = 0.3 m  →  T₁ = 6.8 °C

        Parameters:
            h (float): slab thickness in metres
            gradient_type (str): 'heating' (positive) or 'cooling' (negative)

        Returns dict:
            T1          – peak temperature differential at top surface (°C)
            h1          – depth of top zone (m)
            h2          – depth of bottom zone from soffit (m; fixed 0.4)
            T_at_y      – callable T_at_y(y) → temperature (°C) at depth y from top
            gradient_type – 'heating' or 'cooling'
            clause      – reference string
        """
        _heating_T1 = {0.2: 18.0, 0.3: 20.5}
        _cooling_T1  = {0.2:  4.4, 0.3:  6.8}

        def _interp_T1(table: dict, h_val: float) -> float:
            if h_val <= 0.2:
                return table[0.2]
            if h_val >= 0.3:
                return table[0.3]
            return table[0.2] + (h_val - 0.2) / 0.1 * (table[0.3] - table[0.2])

        g  = gradient_type.strip().lower()
        h1 = round(0.6 * h, 4)
        h2 = 0.4  # fixed 0.4 m from soffit

        if g == 'heating':
            T1 = _interp_T1(_heating_T1, h)

            def T_at_y(y: float) -> float:
                # Zone 1: T(y) = T₁ × (1 − y/h₁)^(1/4)  [4th-root parabola]
                # Zone 2 & 3: T = 0
                if y < 0 or y > h:
                    return 0.0
                if y <= h1:
                    return round(T1 * (1.0 - y / h1) ** 0.25, 4)
                return 0.0

        elif g == 'cooling':
            T1 = _interp_T1(_cooling_T1, h)

            def T_at_y(y: float) -> float:
                # Zone 1: T(y) = T₁ × (1 − y/h₁)  [linear, triangular profile]
                # Zone 2 & 3: T = 0
                if y < 0 or y > h:
                    return 0.0
                if y <= h1:
                    return round(T1 * (1.0 - y / h1), 4)
                return 0.0

        else:
            raise ValueError(
                f"gradient_type must be 'heating' or 'cooling', got '{gradient_type}'"
            )

        return {
            'T1': round(T1, 3),
            'h1': h1,
            'h2': h2,
            'T_at_y': T_at_y,
            'gradient_type': g,
            'clause': 'IRC 6:2017 - 215.4',
        }

    @staticmethod
    def cl_215_4_material_properties() -> dict:
        """
        Thermal material properties per IRC:6-2017 Cl.215.2.

        Returns
        -------
        dict
            alpha  (float) : coefficient of thermal expansion (/°C)
            clause (str)   : code reference
        """
        thermal_expansion_coefficient = 11.7e-6  # /°C — IRC 6:2017 Cl.215.2 (metallic / composite)
        return {
            'alpha':  thermal_expansion_coefficient,
            'clause': 'IRC 6:2017 Cl.215.2',
        }



    @staticmethod
    def table_16():
        """
        Returns dictionary of zone factors as per IRC:6-2017 Table 16.
        Returns:
            dict: zone factors {'Seismic Zone': factor}
        """
        zone_factors = {
            'Zone II': 0.10,
            'Zone III': 0.16,
            'Zone IV': 0.24,
            'Zone V': 0.36
        }
        return zone_factors
    

    # Special Vehicle

    @staticmethod
    def cl_204_5_1_special_vehicle():

        # IRC:6-2017 Clause 204.5 / 204.5.1
        # Special Vehicle (Prime mover + 20 axle hydraulic trailer)

        # Longitudinal Spacing 
        dist12 = 3.200 * m
        dist23 = 1.370 * m
        dist34 = 5.389 * m
        trailer_spacing = 1.500 * m

        #  Axle Loads (tonnes) 
        axle_loads_tonne = (
            [6.0] +           # 1 steering axle
            [9.5, 9.5] +      # 2 bogie axles
            [18.0] * 20       # 20 trailer axles
        )

        # Convert tonne → kN
        wheel_loads = [ax * g for ax in axle_loads_tonne]

        #  Longitudinal Positions 
        load_positions_x = [0.0]
        load_positions_x.append(load_positions_x[-1] + dist12)
        load_positions_x.append(load_positions_x[-1] + dist23)
        load_positions_x.append(load_positions_x[-1] + dist34)

        # 19 spacings → gives 20 trailer axle positions total
        for _ in range(19):
            load_positions_x.append(load_positions_x[-1] + trailer_spacing)

        #  Transverse Positions 
        load_positions_z = [-0.9, 0.9]

        #  Totals 
        total_load_tonne = sum(axle_loads_tonne)
        total_load_kN = sum(wheel_loads)

        #  Axle ↔ Position Explicit Mapping 

        axle_load_map = []
        location_table = []
        header = f"{'Axle':>4} | {'X (m)':>7} | {'Load (t)':>8} | {'Load (kN)':>9}"
        location_table.append(header)
        location_table.append("-" * len(header))

        for i in range(len(axle_loads_tonne)):
            axle = {
                'axle_no': i + 1,
                'x': round(load_positions_x[i], 3),
                'load_tonne': round(axle_loads_tonne[i], 2),
                'load_kN': round(wheel_loads[i], 2)
            }
            axle_load_map.append(axle)

            # printable line
            location_table.append(
                f"{axle['axle_no']:>4} | {axle['x']:>7.3f} | {axle['load_tonne']:>8.2f} | {axle['load_kN']:>9.2f}"
            )

        pretty_table = "\n".join(location_table)


        assert len(load_positions_x) == len(axle_loads_tonne), \
            "Axle count and position count mismatch"

        return {
            'x': load_positions_x,
            'z': load_positions_z,
            'wheel_loads': wheel_loads,
            'total_load_kN': round(total_load_kN, 3),
            'total_load_tonne': round(total_load_tonne, 3),
            'axle_load_map': axle_load_map,
            'pretty_axle_table': pretty_table
        }

    @staticmethod
    def cl_204_5_3_sv_placement(carriageway_width, include_median='no', footpath='none'):
        """
        Determines Special Vehicle (SV) transverse placement requirements as per 
        IRC:6-2017 Clause 204.5.3 / Table 6B.
        
        Parameters:
            carriageway_width (float): Carriageway width in metres
            include_median (str): 'yes' or 'no' - whether median is present
            footpath (str): 'none', 'single_sided', or 'both_sides'
            
        Returns:
            dict: Contains 'sv_applicable', 'eccentricity_mm', 'carriageway_width',
                  'vehicle_combination' (if applicable), 'case_description'
            Returns None if no SV combination is needed
        """
        # Normalize inputs
        median_lower = include_median.strip().lower()
        footpath_lower = footpath.strip().lower().replace(' ', '_').replace('-', '_')
        
        # Get number of design lanes from table_6A
        result_6a = IRC6_2017.table_6A(carriageway_width)
        num_lanes = result_6a.get('design_lanes', 1)
        
        # Check if SV combination applies (requires more than 1 lane)
        if num_lanes <= 1:
            return {
                'sv_applicable': False,
                'reason': f'Only {num_lanes} design lane(s). SV combination requires > 1 lane.',
                'carriageway_width': carriageway_width,
                'num_lanes': num_lanes
            }
        
        # Case 1: Multi-lane undivided, no median, footpath on both sides or none
        # Symmetrical configuration - eccentricity = +300mm
        if median_lower == 'no' and footpath_lower in ['none', 'both_sides', 'both']:
            return {
                'sv_applicable': True,
                'case': 1,
                'case_description': 'Single Multi-Lane Undivided Carriageway with Symmetrical '
                                   'Configuration with Footway on Both Sides or Without Footpath',
                'eccentricity_mm': 300,
                'carriageway_width': carriageway_width,
                'num_lanes': num_lanes,
                'note': 'No other load permitted during passage of SV loading'
            }
        
        # Case 2: Multi-lane undivided, no median, footpath on single side
        # Unsymmetrical configuration - eccentricity = -300mm (towards footpath side)
        if median_lower == 'no' and footpath_lower in ['single_sided', 'single', 'one_side']:
            return {
                'sv_applicable': True,
                'case': 2,
                'case_description': 'Single Multi-Lane Undivided Carriageway having '
                                   'Unsymmetrical Configuration with Footway on one Side',
                'eccentricity_mm': -300,
                'carriageway_width': carriageway_width,
                'num_lanes': num_lanes,
                'note': 'No other load permitted during passage of SV loading'
            }
        
        # Case 5: Dual carriageway with central median (no structural gap),
        # common substructure - eccentricity = +300mm and vehicle combination applies
        if median_lower == 'yes':
            # Get vehicle combination from table_6A
            vehicle_combination = result_6a.get('vehicle_combinations', 'See Table 6A')
            
            return {
                'sv_applicable': True,
                'case': 5,
                'case_description': 'Dual Multi-Lane Carriageway with Central Median but '
                                   'without any Structural Gap with Common Sub-Structure '
                                   '& Foundation for Dual Carriageway',
                'eccentricity_mm': 300,
                'carriageway_width': carriageway_width,
                'num_lanes': num_lanes,
                'vehicle_combination': vehicle_combination,
                'note': 'Load Combinations & Partial safety factors as given in clause 204.5.4 '
                       'shall apply for the entire structure'
            }
        
        # No case matched - SV combination not required
        return {
            'sv_applicable': False,
            'reason': 'Configuration does not require SV combination per Table 6B.',
            'carriageway_width': carriageway_width,
            'num_lanes': num_lanes,
            'include_median': include_median,
            'footpath': footpath
        }
    # =========================================================================
    # CLAUSE 218: SEISMIC DESIGN FUNCTIONS
    # =========================================================================

    @staticmethod
    def figure_17(city_or_region):
        """
        Returns the seismic zone for an Indian city/region as per IRC:6-2017 Figure 17.
        
        Parameters:
            city_or_region (str): Name of the city or region (case-insensitive)
            
        Returns:
            str: Seismic zone ('Zone II', 'Zone III', 'Zone IV', or 'Zone V')
        """
        # Comprehensive mapping of Indian cities/regions to seismic zones
        # Based on IS 1893:2016 and IRC:6-2017 Figure 17
        zone_mapping = {
            # Zone V (Very High Seismic Risk) - Z = 0.36
            'Zone V': [
                'guwahati', 'shillong', 'imphal', 'kohima', 'aizawl', 'agartala',
                'itanagar', 'gangtok', 'srinagar', 'jammu', 'dharamsala', 'mandi',
                'kullu', 'chamba', 'uttarkashi', 'chamoli', 'pithoragarh', 'almora',
                'nainital', 'tehri', 'pauri', 'rudraprayag', 'bageshwar', 'champawat',
                'port blair', 'andaman', 'nicobar', 'digboi', 'dibrugarh', 'jorhat',
                'tezpur', 'north lakhimpur', 'sibsagar', 'golaghat', 'nagaon',
            ],
            # Zone IV (High Seismic Risk) - Z = 0.24
            'Zone IV': [
                'delhi', 'new delhi', 'faridabad', 'gurgaon', 'gurugram', 'noida',
                'ghaziabad', 'meerut', 'saharanpur', 'muzaffarnagar', 'dehradun',
                'haridwar', 'rishikesh', 'roorkee', 'shimla', 'chandigarh', 'ludhiana',
                'jalandhar', 'amritsar', 'pathankot', 'hoshiarpur', 'ambala',
                'panchkula', 'karnal', 'panipat', 'rohtak', 'sonipat', 'lucknow',
                'kanpur', 'agra', 'varanasi', 'allahabad', 'prayagraj', 'gorakhpur',
                'bareilly', 'moradabad', 'aligarh', 'mathura', 'firozabad', 'patna',
                'muzaffarpur', 'bhagalpur', 'gaya', 'darbhanga', 'munger', 'purnia',
                'siliguri', 'darjeeling', 'jalpaiguri', 'cooch behar', 'malda',
                'bhopal', 'jabalpur', 'gwalior', 'arunachal pradesh', 'manipur',
                'meghalaya', 'mizoram', 'nagaland', 'sikkim', 'tripura',
            ],
            # Zone III (Moderate Seismic Risk) - Z = 0.16
            'Zone III': [
                'mumbai', 'pune', 'nashik', 'aurangabad', 'kolhapur', 'solapur',
                'ahmednagar', 'satara', 'sangli', 'ratnagiri', 'kolkata', 'howrah',
                'hooghly', 'bardhaman', 'burdwan', 'asansol', 'durgapur', 'midnapore',
                'kharagpur', 'ahmedabad', 'vadodara', 'surat', 'rajkot', 'bhavnagar',
                'jamnagar', 'junagadh', 'porbandar', 'kutch', 'bhuj', 'gandhidham',
                'jaipur', 'jodhpur', 'udaipur', 'kota', 'ajmer', 'bikaner', 'alwar',
                'bharatpur', 'sikar', 'jhunjhunu', 'chittorgarh', 'pali', 'nagaur',
                'indore', 'ujjain', 'ratlam', 'guna', 'sagar', 'rewa', 'satna',
                'cuttack', 'bhubaneswar', 'puri', 'rourkela', 'sambalpur', 'berhampur',
                'ranchi', 'jamshedpur', 'dhanbad', 'bokaro', 'hazaribagh', 'deoghar',
                'visakhapatnam', 'vijayawada', 'guntur', 'nellore', 'tirupati',
                'mangalore', 'mangaluru', 'udupi', 'karwar', 'hubli', 'dharwad',
                'belgaum', 'belagavi', 'goa', 'panaji', 'margao', 'vasco',
                'thiruvananthapuram', 'trivandrum', 'kochi', 'cochin', 'kozhikode',
                'calicut', 'thrissur', 'kannur', 'kollam', 'alappuzha', 'palakkad',
                'coimbatore', 'madurai', 'tiruchirappalli', 'trichy', 'salem',
                'tirunelveli', 'erode', 'vellore', 'thoothukudi', 'tuticorin',
                'pondicherry', 'puducherry', 'lakshadweep',
            ],
            # Zone II (Low Seismic Risk) - Z = 0.10
            'Zone II': [
                'chennai', 'hyderabad', 'secunderabad', 'warangal', 'nizamabad',
                'karimnagar', 'khammam', 'ramagundam', 'bengaluru', 'bangalore',
                'mysore', 'mysuru', 'tumkur', 'davangere', 'bellary', 'ballari',
                'gulbarga', 'kalaburagi', 'bidar', 'raichur', 'shimoga', 'shivamogga',
                'nagpur', 'amravati', 'akola', 'chandrapur', 'wardha', 'yavatmal',
                'nanded', 'latur', 'osmanabad', 'beed', 'jalna', 'parbhani',
                'raipur', 'bhilai', 'durg', 'bilaspur', 'korba', 'rajnandgaon',
                'kanyakumari', 'thanjavur', 'cuddalore', 'chidambaram', 'nagapattinam',
                'karaikal', 'mahabalipuram', 'kanchipuram', 'chengalpattu',
            ],
        }
        
        # Normalize input
        city_lower = city_or_region.strip().lower()
        
        # Search for the city in zone mapping
        for zone, cities in zone_mapping.items():
            if city_lower in cities:
                return zone
        
        # If not found, raise error
        raise ValueError(
            f"City/region '{city_or_region}' not found in seismic zone database. "
            "Please provide a valid Indian city or manually specify the seismic zone."
        )

    @staticmethod
    def cl_218_3_vertical_seismic_component(Ah):
        """
        Returns the vertical seismic coefficient as per IRC:6-2017 Clause 218.3.

        Two horizontal components are taken as of equal magnitude, and the vertical
        component is taken as two-thirds of the horizontal component.

        Parameters:
            Ah (float): Horizontal seismic coefficient

        Returns:
            float: Vertical seismic coefficient Av = (2/3) * Ah
        """
        Av = (2.0 / 3.0) * Ah
        return round(Av, 4)

    @staticmethod
    def cl_218_4_seismic_combinations(r1, r2, r3):
        """
        Returns the design seismic force combinations as per IRC:6-2017 Clause 218.4.

        The design seismic force resultants shall be combined as:
        a) ± r1 ± 0.3*r2 ± 0.3*r3
        b) ± 0.3*r1 ± r2 ± 0.3*r3
        c) ± 0.3*r1 ± 0.3*r2 ± r3

        Parameters:
            r1 (float): Seismic force resultant in direction 1 (longitudinal)
            r2 (float): Seismic force resultant in direction 2 (transverse)
            r3 (float): Seismic force resultant in direction 3 (vertical)

        Returns:
            list: List of dictionaries containing all combinations
        """
        combinations = [
            # Combination a): ± r1 ± 0.3*r2 ± 0.3*r3
            {'case': 'a', 'r1_factor': 1.0, 'r2_factor': 0.3, 'r3_factor': 0.3,
             'r1': r1, 'r2': 0.3 * r2, 'r3': 0.3 * r3,
             'total_positive': r1 + 0.3 * r2 + 0.3 * r3,
             'description': '± r1 ± 0.3*r2 ± 0.3*r3'},
            
            # Combination b): ± 0.3*r1 ± r2 ± 0.3*r3
            {'case': 'b', 'r1_factor': 0.3, 'r2_factor': 1.0, 'r3_factor': 0.3,
             'r1': 0.3 * r1, 'r2': r2, 'r3': 0.3 * r3,
             'total_positive': 0.3 * r1 + r2 + 0.3 * r3,
             'description': '± 0.3*r1 ± r2 ± 0.3*r3'},
            
            # Combination c): ± 0.3*r1 ± 0.3*r2 ± r3
            {'case': 'c', 'r1_factor': 0.3, 'r2_factor': 0.3, 'r3_factor': 1.0,
             'r1': 0.3 * r1, 'r2': 0.3 * r2, 'r3': r3,
             'total_positive': 0.3 * r1 + 0.3 * r2 + r3,
             'description': '± 0.3*r1 ± 0.3*r2 ± r3'},
        ]
        
        return combinations 

    @staticmethod
    def table_18(damping_percent=5.0):
        """
        Returns the damping multiplying factor as per IRC:6-2017 Table 18.
        
        Parameters:
            damping_percent (float): Damping percentage (2, 5, or 10)
            
        Returns:
            float: Multiplying factor for damping
        """
        # 2% damping: Prestressed concrete, Steel and composite steel
        # 5% damping: Reinforced concrete
        # 10% damping: Retrofitting of old bridges with RC piers
        damping_factors = {
            2: 1.4,
            5: 1.0,
            10: 0.8,
        }
        
        if damping_percent in damping_factors:
            return damping_factors[damping_percent]
        
        # Interpolate for intermediate values
        if damping_percent < 2:
            return 1.4
        elif damping_percent < 5:
            return 1.4 + (damping_percent - 2) * (1.0 - 1.4) / (5 - 2)
        elif damping_percent < 10:
            return 1.0 + (damping_percent - 5) * (0.8 - 1.0) / (10 - 5)
        else:
            return 0.8

    @staticmethod
    def table_19(bridge_class='normal'):
        """
        Returns the importance factor (I) as per IRC:6-2017 Table 19.
        
        Parameters:
            bridge_class (str): One of 'normal', 'important', or 'large_critical'
            
        Returns:
            float: Importance factor (1.0, 1.2, or 1.5)
        """
        # Normal bridges: All bridges except those mentioned below (I = 1.0)
        # Important bridges: River bridges, flyovers, National/State Highways (I = 1.2)
        # Large critical bridges: >1km, perennial rivers, no alternatives (I = 1.5)
        importance_factors = {
            'normal': 1.0,
            'important': 1.2,
            'large_critical': 1.5,
        }
        
        bridge_class_lower = bridge_class.strip().lower()
        
        if bridge_class_lower not in importance_factors:
            raise ValueError(
                f"Invalid bridge class '{bridge_class}'. "
                "Must be 'normal', 'important', or 'large_critical'."
            )
        
        return importance_factors[bridge_class_lower]

    @staticmethod
    def table_20(bridge_component='integral', ductile_detailing=True, seismic_zone='Zone III'):
        """
        Returns the response reduction factor (R) as per IRC:6-2017 Table 20.
        
        Parameters:
            bridge_component (str): Type of bridge component
                - 'integral', 'semi_integral', 'framed' for type (a) - R=2.0 ductile
                - 'precast', 'segmental', 'other' for type (b) - R=1.0 always
            ductile_detailing (bool): Whether ductile detailing is provided
            seismic_zone (str): Seismic zone (only Zone II allows non-ductile for type a)
            
        Returns:
            float: Response reduction factor R
        """
        # R values: (with_ductile, without_ductile_zone_II_only)
        # Type (a): Superstructure of integral/Semi integral bridge/Framed bridges
        type_a = {
            'integral': (2.0, 1.0),
            'semi_integral': (2.0, 1.0),
            'semi-integral': (2.0, 1.0),
            'framed': (2.0, 1.0),
        }
        # Type (b): Other types of Superstructure, including precast segmental construction
        type_b = {
            'precast': (1.0, 1.0),
            'segmental': (1.0, 1.0),
            'precast_segmental': (1.0, 1.0),
            'other': (1.0, 1.0),
        }
        
        component_lower = bridge_component.strip().lower()
        
        # Determine which type the component belongs to
        if component_lower in type_a:
            r_ductile, r_non_ductile = type_a[component_lower]
        elif component_lower in type_b:
            r_ductile, r_non_ductile = type_b[component_lower]
        elif component_lower == 'superstructure':
            # Default to type (a) for backward compatibility
            r_ductile, r_non_ductile = (2.0, 1.0)
        else:
            raise ValueError(
                f"Invalid bridge_component '{bridge_component}'. "
                "Use 'integral', 'semi_integral', 'framed' for type (a), or "
                "'precast', 'segmental', 'other' for type (b)."
            )
        
        if ductile_detailing:
            return r_ductile
        else:
            # Non-ductile only allowed in Zone II
            zone_lower = seismic_zone.strip().lower()
            if zone_lower == 'zone ii':
                return r_non_ductile
            else:
                raise ValueError(
                    f"Non-ductile detailing (R={r_non_ductile}) is only allowed "
                    f"in Zone II. Current zone: {seismic_zone}"
                )

    @staticmethod
    def cl_218_5_1(zone, soil_type, dead_load_kN, live_load_kN=0.0,
                   lateral_force_per_mm=None, period_T=None, 
                   bridge_class='normal', bridge_component='superstructure',
                   ductile_detailing=True, damping_percent=5.0,
                   direction='perpendicular'):
        """
        Calculates seismic forces as per IRC:6-2017 Clause 218.5.1.
        
        Parameters:
            zone (str): Seismic zone ('Zone II', 'Zone III', 'Zone IV', 'Zone V')
            soil_type (int): Soil type (1=Rock/Hard, 2=Medium, 3=Soft)
            dead_load_kN (float): Dead load in kN
            live_load_kN (float): Live load in kN
            lateral_force_per_mm (float): Force for 1mm deflection (kN/mm), for T calculation
            period_T (float): Fundamental period (if known, overrides calculation)
            bridge_class (str): 'normal', 'important', or 'large_critical'
            bridge_component (str): Component type for R factor
            ductile_detailing (bool): Whether ductile detailing is provided
            damping_percent (float): Damping percentage (2, 5, or 10)
            direction (str): 'perpendicular' (20% LL), 'parallel' (0% LL), or 'vertical'
            
        Returns:
            dict: Contains T, Sa_g, Z, I, R, Ah, Feq, and Feq_design (Feq/R)
        """
        # Get zone factor Z from Table 16
        zone_factors = IRC6_2017.table_16()
        # Match zone by lowercase comparison
        zone_lower = zone.strip().lower()
        zone_key = next((k for k in zone_factors if k.lower() == zone_lower), None)
        if zone_key is None:
            raise ValueError(f"Invalid zone '{zone}'. Must be 'Zone II', 'Zone III', 'Zone IV', or 'Zone V'.")
        Z = zone_factors[zone_key]
        
        # Get importance factor I
        I = IRC6_2017.table_19(bridge_class)
        
        # Get response reduction factor R
        R = IRC6_2017.table_20(bridge_component, ductile_detailing, zone)
        
        # Get damping multiplying factor
        damping_factor = IRC6_2017.table_18(damping_percent)
        
        # Calculate fundamental period T
        if period_T is not None:
            T = period_T
        elif lateral_force_per_mm is not None and lateral_force_per_mm > 0:
            T = 2.0 * math.sqrt(dead_load_kN / (1000 * lateral_force_per_mm))
        else:
            # Default: assume 2.5 for Sa/g (small bridges approximation)
            T = 0.5  # Results in Sa/g = 2.5 for all soil types
        
        # Cap T at 4.0 seconds
        T = min(T, 4.0)
        
        # Calculate Sa/g based on soil type and period
        if T < 0:
            raise ValueError("Period T must be non-negative")
        
        if soil_type == 1:  # Type I: Rock/Hard (N > 30)
            if T <= 0.10:
                sa_g = 1 + 15 * T
            elif T <= 0.40:
                sa_g = 2.50
            else:
                sa_g = 1.00 / T
        elif soil_type == 2:  # Type II: Medium (10 < N <= 30)
            if T <= 0.10:
                sa_g = 1 + 15 * T
            elif T <= 0.55:
                sa_g = 2.50
            else:
                sa_g = 1.36 / T
        elif soil_type == 3:  # Type III: Soft (N < 10)
            if T <= 0.10:
                sa_g = 1 + 15 * T
            elif T <= 0.67:
                sa_g = 2.50
            else:
                sa_g = 1.67 / T
        else:
            raise ValueError(f"Invalid soil type {soil_type}. Must be 1, 2, or 3.")
        
        # Apply damping factor (Sa/g values are for 5% damping)
        sa_g_adjusted = sa_g * damping_factor
        
        # Calculate horizontal seismic coefficient Ah
        Ah = (Z / 2) * I * sa_g_adjusted
        
        # Calculate seismic force Feq
        if direction.lower() == 'perpendicular':
            appropriate_LL = 0.20 * live_load_kN
        else:
            appropriate_LL = 0.0
        
        Feq = Ah * (dead_load_kN + appropriate_LL)
        
        # Design force for combining with other forces (Feq/R)
        Feq_design = Feq / R
        
        return {
            'T': round(T, 3),
            'Sa_g': round(sa_g, 3),
            'Sa_g_adjusted': round(sa_g_adjusted, 3),
            'Z': Z,
            'I': I,
            'R': R,
            'damping_factor': damping_factor,
            'Ah': round(Ah, 4),
            'Feq': round(Feq, 3),
            'Feq_design': round(Feq_design, 3),  # For force combinations
            'direction': direction,
        }


    # =========================================================================
    # ANNEX B: PARTIAL SAFETY FACTORS FOR LOADS
    # =========================================================================

    # Canonical stable keys for each ULS / SLS load combination. These are the
    # single source of truth shared by the core combination builder
    # (BridgeGrillageModel.create_uls_combinations / create_sls_combinations) and
    # the desktop per-combination checkbox widget (LoadCombinationWidget), so the
    # two agree on which combination a checkbox refers to regardless of display
    # numbering. Do NOT key off the display number — the widget numbers combos
    # leading-first while the analyser numbers them direction-first.
    #
    # ULS key tuple: (combination_type, leading_or_condition, accidental_load, direction)
    ULS_COMBINATION_KEYS = {
        ('basic',       'live_load',  None,                'adding'):    'loading.load_combination.basic.ll_leading.adding',
        ('basic',       'wind_load',  None,                'adding'):    'loading.load_combination.basic.wl_leading.adding',
        ('basic',       'thermal_load', None,              'adding'):    'loading.load_combination.basic.tl_leading.adding',
        ('basic',       'live_load',  None,                'relieving'): 'loading.load_combination.basic.ll_leading.relieving',
        ('basic',       'wind_load',  None,                'relieving'): 'loading.load_combination.basic.wl_leading.relieving',
        ('basic',       'thermal_load', None,              'relieving'): 'loading.load_combination.basic.tl_leading.relieving',
        ('accidental',  'live_load',  'vehicle_collision', 'adding'):    'loading.load_combination.accidental.vc.ll_leading.adding',
        ('accidental',  'live_load',  'barge_impact',      'adding'):    'loading.load_combination.accidental.bi.ll_leading.adding',
        ('accidental',  'live_load',  'floating_bodies',   'adding'):    'loading.load_combination.accidental.fb.ll_leading.adding',
        ('accidental',  'live_load',  'vehicle_collision', 'relieving'): 'loading.load_combination.accidental.vc.ll_leading.relieving',
        ('accidental',  'live_load',  'barge_impact',      'relieving'): 'loading.load_combination.accidental.bi.ll_leading.relieving',
        ('accidental',  'live_load',  'floating_bodies',   'relieving'): 'loading.load_combination.accidental.fb.ll_leading.relieving',
        ('seismic',     'service',    None,                'adding'):    'loading.load_combination.seismic.service.adding',
        ('seismic',     'construction', None,              'adding'):    'loading.load_combination.seismic.construction.adding',
        ('seismic',     'service',    None,                'relieving'): 'loading.load_combination.seismic.service.relieving',
        ('seismic',     'construction', None,              'relieving'): 'loading.load_combination.seismic.construction.relieving',
    }

    # SLS key tuple: (combination_type, leading, direction)
    SLS_COMBINATION_KEYS = {
        ('rare',            'live_load',    'adding'):    'loading.load_combination.sls.rare.ll_leading.adding',
        ('rare',            'wind_load',    'adding'):    'loading.load_combination.sls.rare.wl_leading.adding',
        ('rare',            'thermal_load', 'adding'):    'loading.load_combination.sls.rare.tl_leading.adding',
        ('rare',            'live_load',    'relieving'): 'loading.load_combination.sls.rare.ll_leading.relieving',
        ('rare',            'wind_load',    'relieving'): 'loading.load_combination.sls.rare.wl_leading.relieving',
        ('rare',            'thermal_load', 'relieving'): 'loading.load_combination.sls.rare.tl_leading.relieving',
        ('frequent',        'live_load',    'adding'):    'loading.load_combination.sls.frequent.ll_leading.adding',
        ('frequent',        'wind_load',    'adding'):    'loading.load_combination.sls.frequent.wl_leading.adding',
        ('frequent',        'thermal_load', 'adding'):    'loading.load_combination.sls.frequent.tl_leading.adding',
        ('frequent',        'live_load',    'relieving'): 'loading.load_combination.sls.frequent.ll_leading.relieving',
        ('frequent',        'wind_load',    'relieving'): 'loading.load_combination.sls.frequent.wl_leading.relieving',
        ('frequent',        'thermal_load', 'relieving'): 'loading.load_combination.sls.frequent.tl_leading.relieving',
        ('quasi_permanent', None,           'adding'):    'loading.load_combination.sls.quasi_permanent.adding',
        ('quasi_permanent', None,           'relieving'): 'loading.load_combination.sls.quasi_permanent.relieving',
    }

    # IRC:6-2017 Table B.2 — Partial Safety Factor for Verification of Structural Strength
    # key: (load_type, qualifier)  →  {combination: γ}
    # qualifier: sub-row label (effect or load_category); None for single-row entries
    # None value means not applicable ('-' in table); 'refer_note_2' follows table footnote
    _TABLE_B2 = {
        # 1. Permanent Loads
        # 1.1 Dead Load, Snow load (if present), SIDL except surfacing
        ('dead_load',             'adding'):       {'basic': 1.35, 'accidental': 1.0,           'seismic': 1.35},
        ('dead_load',             'relieving'):    {'basic': 1.0,  'accidental': 1.0,           'seismic': 1.0 },
        # 1.2 Surfacing
        ('surfacing',             'adding'):       {'basic': 1.75, 'accidental': 1.0,           'seismic': 1.75},
        ('surfacing',             'relieving'):    {'basic': 1.0,  'accidental': 1.0,           'seismic': 1.0 },
        # 1.3 Prestress and Secondary effect of prestress
        ('prestress',             None):           {'basic': 1.5,  'accidental': 'refer_note_2','seismic': None},
        # 1.4 Back-fill Weight
        ('backfill_weight',       'adverse'):      {'basic': 1.35, 'accidental': 1.0,           'seismic': 1.0 },
        ('backfill_weight',       'relieving'):    {'basic': 1.0,  'accidental': 1.0,           'seismic': 1.0 },
        # 1.5 Earth Pressure
        ('earth_pressure',        'adding'):       {'basic': 1.5,  'accidental': 1.0,           'seismic': 1.0 },
        ('earth_pressure',        'relieving'):    {'basic': 1.0,  'accidental': 1.0,           'seismic': 1.0 },
        # 2. Variable Loads
        # 2.1 Carriageway Live load + associated loads (braking, tractive, centrifugal) + Footway live load
        ('live_load',             'leading'):      {'basic': 1.5,  'accidental': 0.75,          'seismic': None},
        ('live_load',             'accompanying'): {'basic': 1.15, 'accidental': 0.2,           'seismic': 0.2 },
        ('live_load',             'construction'): {'basic': 1.35, 'accidental': 1.0,           'seismic': 1.0 },
        # 2.2 Wind Load during service and construction
        ('wind_load',             'leading'):      {'basic': 1.5,  'accidental': None,          'seismic': None},
        ('wind_load',             'accompanying'): {'basic': 0.9,  'accidental': None,          'seismic': None},
        # 2.3 Live Load Surcharge effects (as accompanying load)
        ('live_load_surcharge',   None):           {'basic': 1.2,  'accidental': 0.2,           'seismic': 0.2 },
        # 2.4 Construction Dead Load (launching girder, truss, cantilever construction equipment)
        ('construction_dead_load',None):           {'basic': 1.35, 'accidental': 1.0,           'seismic': 1.35},
        # 2.5 Thermal Loads
        ('thermal_load',          'leading'):      {'basic': 1.5,  'accidental': None,          'seismic': None},
        ('thermal_load',          'accompanying'): {'basic': 0.9,  'accidental': 0.5,           'seismic': 0.5 },
        # 3. Accidental Loads
        # 3.1 Vehicle collision
        ('vehicle_collision',     None):           {'basic': None, 'accidental': 1.0,           'seismic': None},
        # 3.2 Barge Impact
        ('barge_impact',          None):           {'basic': None, 'accidental': 1.0,           'seismic': None},
        # 3.3 Impact due to floating bodies
        ('floating_bodies',       None):           {'basic': None, 'accidental': 1.0,           'seismic': None},
        # 4. Seismic Effect
        ('seismic',               'service'):      {'basic': None, 'accidental': None,          'seismic': 1.5 },
        ('seismic',               'construction'): {'basic': None, 'accidental': None,          'seismic': 0.75},
    }

    @staticmethod
    def table_B2(load_type, qualifier=None, combination='basic'):
        """
        IRC:6-2017 Table B.2 — Partial Safety Factor for Verification of Structural Strength.

        Args:
            load_type (str): Load type key (see _TABLE_B2 for valid values).
            qualifier (str | None): Sub-row label — effect ('adding', 'relieving', 'adverse')
                or load category ('leading', 'accompanying', 'construction', 'service').
                Pass None for single-row load types (e.g. 'prestress', 'live_load_surcharge').
            combination (str): 'basic', 'accidental', or 'seismic'.

        Returns:
            float | None | str: Partial safety factor, None (not applicable), or 'refer_note_2'.
        """
        key = (load_type.strip().lower(), qualifier.strip().lower() if qualifier else None)
        return IRC6_2017._TABLE_B2[key][combination.strip().lower()]

    @staticmethod
    def uls_load_combinations() -> list[dict]:
        """
        Generate all valid ULS load combinations per IRC:6-2017 Table B.2.

        Active load types
        -----------------
        Permanent : dead_load, surfacing
        Variable  : live_load, wind_load, thermal_load
        Accidental: vehicle_collision, barge_impact, floating_bodies (one at a time)
        Seismic   : seismic (service and construction separately)

        Skipped   : prestress, backfill_weight, earth_pressure,
                    live_load_surcharge, construction_dead_load

        Permanent load rule
        -------------------
        dead_load and surfacing each carry BOTH factors in every combination:
            {'adding': γ_add, 'relieving': γ_rel}
        Adding and relieving are mutually exclusive within a single check —
        the caller applies whichever direction the load effect takes at that
        cross-section. dead_load and surfacing always share the same effect
        direction (both adding or both relieving together).

        Variable load rule
        ------------------
        Exactly one variable load is 'leading'; the rest are 'accompanying'.
        A permutation is excluded when the leading factor is None (not applicable
        in that combination type). Consequently:
          - Basic      : 3 permutations
          - Accidental : 3 accidental loads × 1 valid leading (live_load only) = 3
          - Seismic    : 2 service conditions (all variable loads accompanying)

        Returns
        -------
        list[dict]  Each entry contains:
            'name'             : str   — human-readable label
            'combination_type' : str   — 'basic' | 'accidental' | 'seismic'
            'factors'          : dict  — permanent loads as {'adding': γ, 'relieving': γ};
                                         variable/accidental/seismic loads as flat γ (or None)
        """
        γ = IRC6_2017.table_B2

        VARIABLE_LOADS   = ['live_load', 'wind_load', 'thermal_load']
        ACCIDENTAL_LOADS = ['vehicle_collision', 'barge_impact', 'floating_bodies']

        def perm_pair(load_type, combo):
            return {
                'adding':    γ(load_type, 'adding',    combo),
                'relieving': γ(load_type, 'relieving', combo),
            }

        combinations = []

        # ── Basic Combination ─────────────────────────────────────────────────
        perm_basic = {
            'dead_load': perm_pair('dead_load', 'basic'),
            'surfacing':  perm_pair('surfacing',  'basic'),
        }
        for leading in VARIABLE_LOADS:
            var = {
                vl: γ(vl, 'leading' if vl == leading else 'accompanying', 'basic')
                for vl in VARIABLE_LOADS
            }
            if var[leading] is None:
                continue
            combinations.append({
                'name':             f'Basic — {leading} leading',
                'combination_type': 'basic',
                'factors':          {**perm_basic, **var},
            })

        # ── Accidental Combination ────────────────────────────────────────────
        perm_acc = {
            'dead_load': perm_pair('dead_load', 'accidental'),
            'surfacing':  perm_pair('surfacing',  'accidental'),
        }
        for acc in ACCIDENTAL_LOADS:
            for leading in VARIABLE_LOADS:
                var = {
                    vl: γ(vl, 'leading' if vl == leading else 'accompanying', 'accidental')
                    for vl in VARIABLE_LOADS
                }
                if var[leading] is None:
                    continue
                combinations.append({
                    'name':             f'Accidental ({acc}) — {leading} leading',
                    'combination_type': 'accidental',
                    'factors':          {**perm_acc, **var, acc: γ(acc, None, 'accidental')},
                })

        # ── Seismic Combination ───────────────────────────────────────────────
        perm_seis = {
            'dead_load': perm_pair('dead_load', 'seismic'),
            'surfacing':  perm_pair('surfacing',  'seismic'),
        }
        var_seis = {vl: γ(vl, 'accompanying', 'seismic') for vl in VARIABLE_LOADS}
        for condition in ['service', 'construction']:
            combinations.append({
                'name':             f'Seismic ({condition}) — all variable loads accompanying',
                'combination_type': 'seismic',
                'factors':          {**perm_seis, **var_seis, 'seismic': γ('seismic', condition, 'seismic')},
            })

        return combinations

    # IRC:6-2017 Table B.3 — Partial Safety Factor for Verification of Serviceability Limit State
    # Skipped: earth_pressure, prestress, shrinkage_creep, settlement, live_load_surcharge,
    #          hydraulic_loads (water_current, wave_pressure, buoyancy)
    _TABLE_B3 = {
        # 1. Permanent Loads
        # 1.1 Dead Load, Snow load if present, SIDL except surfacing and back fill weight
        ('dead_load',    None):           {'rare': 1.0,  'frequent': 1.0,  'quasi_permanent': 1.0 },
        # 1.2 Surfacing
        ('surfacing',    'adding'):       {'rare': 1.2,  'frequent': 1.2,  'quasi_permanent': 1.2 },
        ('surfacing',    'relieving'):    {'rare': 1.0,  'frequent': 1.0,  'quasi_permanent': 1.0 },
        # 3. Variable Loads
        # 3.1 Carriageway Live load + associated loads (braking, tractive, centrifugal) + Footway live load
        ('live_load',    'leading'):      {'rare': 1.0,  'frequent': 0.75, 'quasi_permanent': None},
        ('live_load',    'accompanying'): {'rare': 0.75, 'frequent': 0.2,  'quasi_permanent': 0   },
        # 3.2 Thermal Load
        ('thermal_load', 'leading'):      {'rare': 1.0,  'frequent': 0.60, 'quasi_permanent': None},
        ('thermal_load', 'accompanying'): {'rare': 0.60, 'frequent': 0.50, 'quasi_permanent': 0.5 },
        # 3.3 Wind Load
        ('wind_load',    'leading'):      {'rare': 1.0,  'frequent': 0.60, 'quasi_permanent': None},
        ('wind_load',    'accompanying'): {'rare': 0.60, 'frequent': 0.50, 'quasi_permanent': 0   },
    }

    @staticmethod
    def table_B3(load_type, qualifier=None, combination='rare'):
        """
        IRC:6-2017 Table B.3 — Partial Safety Factor for Verification of Serviceability Limit State.

        Args:
            load_type (str): Load type key (see _TABLE_B3 for valid values).
            qualifier (str | None): 'adding' or 'relieving' for surfacing;
                'leading' or 'accompanying' for variable loads; None for dead_load.
            combination (str): 'rare', 'frequent', or 'quasi_permanent'.

        Returns:
            float | None: Partial safety factor, or None (not applicable).
        """
        key = (load_type.strip().lower(), qualifier.strip().lower() if qualifier else None)
        return IRC6_2017._TABLE_B3[key][combination.strip().lower()]

    @staticmethod
    def sls_load_combinations() -> list[dict]:
        """
        Generate all valid SLS load combinations per IRC:6-2017 Table B.3.

        Active load types
        -----------------
        Permanent : dead_load, surfacing
        Variable  : live_load, wind_load, thermal_load

        Skipped   : earth_pressure, prestress, shrinkage_creep, settlement,
                    live_load_surcharge, hydraulic_loads

        Permanent load rule
        -------------------
        dead_load is always 1.0 (no adding/relieving distinction in SLS).
        surfacing carries both factors: {'adding': γ_add, 'relieving': γ_rel}
        — mutually exclusive per cross-section check, always applied together.

        Variable load rule
        ------------------
        Exactly one variable load is 'leading'; the rest are 'accompanying'.
        For quasi-permanent, no variable load has a valid leading factor (all
        None), so one combination is generated with all loads accompanying.
        Consequently:
          - Rare            : 3 permutations
          - Frequent        : 3 permutations
          - Quasi-permanent : 1 (all variable loads accompanying)

        Returns
        -------
        list[dict]  Each entry contains:
            'name'             : str   — human-readable label
            'combination_type' : str   — 'rare' | 'frequent' | 'quasi_permanent'
            'factors'          : dict  — dead_load as flat γ; surfacing as
                                         {'adding': γ, 'relieving': γ};
                                         variable loads as flat γ (or None)
        """
        γ = IRC6_2017.table_B3

        VARIABLE_LOADS = ['live_load', 'wind_load', 'thermal_load']

        def surf_pair(combo):
            return {
                'adding':    γ('surfacing', 'adding',    combo),
                'relieving': γ('surfacing', 'relieving', combo),
            }

        combinations = []

        # ── Rare & Frequent ───────────────────────────────────────────────────
        for combo_type in ['rare', 'frequent']:
            perm = {
                'dead_load': γ('dead_load', None, combo_type),
                'surfacing':  surf_pair(combo_type),
            }
            for leading in VARIABLE_LOADS:
                var = {
                    vl: γ(vl, 'leading' if vl == leading else 'accompanying', combo_type)
                    for vl in VARIABLE_LOADS
                }
                if var[leading] is None:
                    continue
                combinations.append({
                    'name':             f'SLS {combo_type.capitalize()} — {leading} leading',
                    'combination_type': combo_type,
                    'factors':          {**perm, **var},
                })

        # ── Quasi-permanent ───────────────────────────────────────────────────
        # No variable load has a valid leading factor — all accompanying
        perm_qp = {
            'dead_load': γ('dead_load', None, 'quasi_permanent'),
            'surfacing':  surf_pair('quasi_permanent'),
        }
        var_qp = {vl: γ(vl, 'accompanying', 'quasi_permanent') for vl in VARIABLE_LOADS}
        combinations.append({
            'name':             'SLS Quasi-permanent — all variable loads accompanying',
            'combination_type': 'quasi_permanent',
            'factors':          {**perm_qp, **var_qp},
        })

        return combinations
