# =============================================================================
# Chapter 3: Loads and Load Combinations
# Extracted from report_generator.py — DO NOT add business logic here.
# =============================================================================

from osdagbridge.core.utils.common import (
    KEY_BL_IRC_CLASS_SV,
    KEY_CB_LOAD,
    KEY_LL_ECCENTRICITY,
    KEY_LL_CUSTOM_VEHICLES,
    KEY_LL_FOOTPATH_PRESSURE_MODE,
    KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_LL_IRC_70R_BOGIE,
    KEY_LL_IRC_70R_TRACKED,
    KEY_LL_IRC_70R_WHEELED,
    KEY_LL_IRC_AA_TRACKED,
    KEY_LL_IRC_AA_WHEELED,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_CLASS_FATIGUE,
    KEY_LL_IRC_CLASS_SV,
    KEY_MATERIAL_DECK_DENSITY,
    KEY_MATERIAL_GIRDER_DENSITY,
    KEY_PL_SELF_WEIGHT_FACTOR,
    KEY_RL_LOAD_VALUE,
    KEY_SL_DAMPING,
    KEY_SL_DEAD_LOAD_MODE,
    KEY_SL_DEAD_LOAD_VALUE,
    KEY_SL_FORCE_LONGITUDINAL,
    KEY_SL_FORCE_TRANSVERSE,
    KEY_SL_HORIZONTAL_COEFF,
    KEY_SL_IMPORTANCE_FACTOR,
    KEY_SL_LIVE_LOAD_MODE,
    KEY_SL_LIVE_LOAD_VALUE,
    KEY_SL_SEISMIC_ZONE,
    KEY_SL_SOIL_TYPE,
    KEY_SL_SPECTRAL_COEFF,
    KEY_SL_TIME_PERIOD,
    KEY_SL_VERTICAL_COEFF,
    KEY_SL_ZONE_FACTOR,
    KEY_SPAN,
    KEY_TL_BRIDGE_TEMP_MAX,
    KEY_TL_BRIDGE_TEMP_MIN,
    KEY_TL_HIGHEST_MAX_TEMP,
    KEY_TL_LOWEST_MIN_TEMP,
    KEY_TL_TEMP_FALL,
    KEY_TL_TEMP_RISE,
    KEY_WC_LD_LANE_TABLE_COUNT,
    KEY_WC_MATERIAL,
    KEY_WC_THICKNESS,
    KEY_WL_AVG_EXPOSED_HEIGHT,
    KEY_WL_BASIC_WIND_SPEED,
    KEY_WL_HOURLY_MEAN_WIND,
    KEY_WL_HOURLY_WIND_PRESSURE,
    KEY_WL_LONGITUDINAL_WIND_FORCE,
    KEY_WL_TERRAIN_TYPE,
    KEY_WL_TRANSVERSE_WIND_FORCE,
    KEY_WL_VERTICAL_WIND_FORCE
)

from osdagbridge.core.reports.report_utils import (
    _tex, _render_value, render_report_table, render_vehicle_live_load_table,
    render_parameter_value_table
)

def ch3_loads(input_dict, output_dict=None):
    output_dict = output_dict if output_dict is not None else {}
    # Live load vehicle names mapping
    vehicles = []
    if input_dict.get(KEY_LL_IRC_CLASS_A):
        vehicles.append("Class A")
    if input_dict.get(KEY_LL_IRC_70R_WHEELED):
        vehicles.append("Class 70R (Wheeled)")
    if input_dict.get(KEY_LL_IRC_70R_TRACKED):
        vehicles.append("Class 70R (Tracked)")
    if input_dict.get(KEY_LL_IRC_AA_WHEELED):
        vehicles.append("Class AA (Wheeled)")
    if input_dict.get(KEY_LL_IRC_AA_TRACKED):
        vehicles.append("Class AA (Tracked)")
    if input_dict.get(KEY_LL_IRC_CLASS_SV):
        vehicles.append("Class SV")
    if input_dict.get(KEY_LL_IRC_70R_BOGIE):
        vehicles.append("Class 70R (Bogie)")
    if input_dict.get(KEY_LL_IRC_CLASS_FATIGUE):
        vehicles.append("Class Fatigue")
    
    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES)
    if custom and isinstance(custom, list):
        for c in custom:
            if isinstance(c, dict) and c.get('name'):
                vehicles.append(c['name'])
            elif isinstance(c, str):
                vehicles.append(c)
                
    vehicles_str = ", ".join(vehicles) if vehicles else "None"

    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
    span = input_dict.get(KEY_SPAN)
    impact_factor_str = ""
    if span not in (None, ""):
        try:
            span_m = float(span)
            factors = []
            if input_dict.get(KEY_LL_IRC_CLASS_A):
                im_a = IRC6_2017.cl_208_2_impact_factor(span_m)
                factors.append(f"Class A: {1.0 + im_a:.3f}")
            is_wheeled_heavy = (
                input_dict.get(KEY_LL_IRC_70R_WHEELED) or 
                input_dict.get(KEY_LL_IRC_AA_WHEELED) or 
                input_dict.get(KEY_LL_IRC_70R_BOGIE)
            )
            is_tracked_heavy = (
                input_dict.get(KEY_LL_IRC_70R_TRACKED) or 
                input_dict.get(KEY_LL_IRC_AA_TRACKED)
            )
            if is_wheeled_heavy or is_tracked_heavy:
                im_aa = IRC6_2017.cl_208_3_impact_factor(span_m)
                factors.append(f"Class AA/70R: {1.0 + im_aa:.3f}")
            
            if factors:
                impact_factor_str = ", ".join(factors)
            else:
                impact_factor_str = "N/A"
        except Exception:
            impact_factor_str = "N/A"
    else:
        impact_factor_str = "N/A"

    def _vehicle_braking_value(kind):
        total = _vehicle_total_load(kind)
        if total == "N/A":
            return "N/A"
        try:
            return f"{0.20 * float(total):.2f}"
        except Exception:
            return "N/A"

    # Vehicles contributing to the braking load: the same vehicles considered for
    # the live load, except Class SV, which is governed by its own braking opt-in
    # (KEY_BL_IRC_CLASS_SV) independent of the live-load Class SV selection.
    brk_vehicles = [
        vehicle
        for key, vehicle in (
            (KEY_LL_IRC_CLASS_A, "Class A"),
            (KEY_LL_IRC_70R_WHEELED, "Class 70R (Wheeled)"),
            (KEY_LL_IRC_70R_TRACKED, "Class 70R (Tracked)"),
            (KEY_LL_IRC_AA_WHEELED, "Class AA (Wheeled)"),
            (KEY_LL_IRC_AA_TRACKED, "Class AA (Tracked)"),
            (KEY_BL_IRC_CLASS_SV, "Class SV"),
            (KEY_LL_IRC_70R_BOGIE, "Class 70R (Bogie)"),
            (KEY_LL_IRC_CLASS_FATIGUE, "Class Fatigue"),
        )
        if output_dict.get(key)
    ]

    brk_custom = output_dict.get(KEY_LL_CUSTOM_VEHICLES)
    if brk_custom and isinstance(brk_custom, list):
        for c in brk_custom:
            if isinstance(c, dict) and c.get('name'):
                brk_vehicles.append(c['name'])
            elif isinstance(c, str):
                brk_vehicles.append(c)

    brk_vehicles_str = ", ".join(brk_vehicles) if brk_vehicles else "None"

    # Braking load eccentricity from top of deck (IRC 6: 1.2 m above deck surface).
    _brk_ecc = output_dict.get(KEY_LL_ECCENTRICITY)
    brk_ecc_str = f"{_brk_ecc} m" if _brk_ecc not in (None, "") else "N/A"

    vehicle_defs = [
        ("Class A", KEY_LL_IRC_CLASS_A, "class_a"),
        ("Class 70R (Wheeled)", KEY_LL_IRC_70R_WHEELED, "70r_wheeled"),
        ("Class 70R (Tracked)", KEY_LL_IRC_70R_TRACKED, "70r_tracked"),
        ("Class AA (Wheeled)", KEY_LL_IRC_AA_WHEELED, "aa_wheeled"),
        ("Class AA (Tracked)", KEY_LL_IRC_AA_TRACKED, "aa_tracked"),
        ("Class SV", KEY_LL_IRC_CLASS_SV, "sv"),
        ("Class 70R (Bogie)", KEY_LL_IRC_70R_BOGIE, "70r_wheeled"),
        ("Class Fatigue", KEY_LL_IRC_CLASS_FATIGUE, "fatigue"),
    ]

    def _checked(source, key):
        val = source.get(key)
        return val is True or str(val).strip().lower() in ("1", "true", "yes", "checked")

    def _vehicle_total_load(kind):
        try:
            if kind == "class_a":
                return f"{sum(IRC6_2017.cl_204_1_ClassA_vehicle().get('wheel_loads', [])) / 1000.0:.2f}"
            if kind == "70r_wheeled":
                return f"{sum(IRC6_2017.cl_204_1_Class70R_vehicle_wheel().get('wheel_loads', [])) / 1000.0:.2f}"
            if kind == "70r_tracked":
                v = IRC6_2017.cl_204_1_Class70R_vehicle_track()
                return f"{v.get('wheel_loads_udl', 0) * (max(v.get('x', [0])) - min(v.get('x', [0]))) * len(v.get('z', [])) / 1000.0:.2f}"
            if kind == "fatigue":
                return f"{sum(IRC6_2017.cl_204_6_fatigue_load().get('wheel_loads', [])) / 1000.0:.2f}"
            if kind == "sv":
                return f"{IRC6_2017.cl_204_5_1_special_vehicle().get('total_load_kN', 'N/A')}"
        except Exception:
            pass
        return "N/A"

    def _vehicle_impact(kind):
        if span in (None, ""):
            return "N/A"
        try:
            span_m = float(span)
            if kind == "class_a":
                return f"{1.0 + IRC6_2017.cl_208_2_impact_factor(span_m):.3f}"
            if kind in ("70r_wheeled", "70r_tracked", "aa_wheeled", "aa_tracked", "fatigue"):
                return f"{1.0 + IRC6_2017.cl_208_3_impact_factor(span_m):.3f}"
        except Exception:
            pass
        return "N/A"

    brk_ecc_table = brk_ecc_str if brk_ecc_str != "N/A" else (_render_value(input_dict, KEY_LL_ECCENTRICITY, " m") or "1.2 m")
    vehicle_rows = []
    for name, key, kind in vehicle_defs:
        if _checked(input_dict, key):
            braking_considered = "Yes"
            if kind == "sv":
                braking_considered = "Yes" if (_checked(input_dict, KEY_BL_IRC_CLASS_SV) or _checked(output_dict, KEY_BL_IRC_CLASS_SV)) else "No"
            if kind == "fatigue":
                braking_considered = "No"
            vehicle_rows.append([
                _tex(name), _vehicle_total_load(kind), _vehicle_impact(kind),
                braking_considered, _vehicle_braking_value(kind) if braking_considered == "Yes" else "---",
                brk_ecc_table if braking_considered == "Yes" else "---"
            ])
    if custom and isinstance(custom, list):
        for c in custom:
            name = c.get("name") if isinstance(c, dict) else c
            if name:
                vehicle_rows.append([_tex(name), "N/A", "N/A", "No", "---", "---"])
    if not vehicle_rows:
        vehicle_rows = [["None", "---", "---", "No", "---", "---"]]

    fp_mode  = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "")
    fp_value = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE, "")
    if str(fp_mode).strip().lower() in ("as per irc 6", "as per irc6", "automatic"):
        try:
            fp_str = f"{IRC6_2017.cl_206_1_footway_load():.3f}" + r" kN/m\textsuperscript{2} (IRC 6 Cl. 206.1)"
        except Exception:
            fp_str = "N/A"
    elif fp_value not in (None, ""):
        fp_str = _tex(str(fp_value)) + r" kN/m\textsuperscript{2}"
    else:
        fp_str = "N/A"
    footpath_rows = [
        ["Footpath live load", fp_str.replace(r" kN/m\textsuperscript{2}", ""), r"kN/m\textsuperscript{2}"],
        ["Pressure mode", _tex(fp_mode) if fp_mode not in ("", None) else "N/A", "---"],
    ]

    # Vz / Pz — prefer stored computed values; fall back to IRC6 Table 12
    vz_val = input_dict.get(KEY_WL_HOURLY_MEAN_WIND)
    pz_val = input_dict.get(KEY_WL_HOURLY_WIND_PRESSURE)
    if not vz_val or not pz_val:
        try:
            _vb  = input_dict.get(KEY_WL_BASIC_WIND_SPEED) or input_dict.get('wind_speed')
            _h   = input_dict.get(KEY_WL_AVG_EXPOSED_HEIGHT)
            _ter = {
                "Plain Terrain": "plain",
                "Terrain with Obstructions": "obstructed",
            }.get(str(input_dict.get(KEY_WL_TERRAIN_TYPE, "")).strip(), "plain")
            _res = IRC6_2017.table_12(float(_h), _ter, float(_vb))
            if not vz_val:
                vz_val = _res.get("Vz")
            if not pz_val:
                pz_val = _res.get("Pz")
        except Exception:
            pass
    vz_str = f"{float(vz_val):.2f} m/s" if vz_val not in (None, "") else "N/A"
    pz_str = (f"{float(pz_val):.2f}" + r" N/m\textsuperscript{2}") if pz_val not in (None, "") else "N/A"

    # Table 3.5 — Seismic: prefer stored computed values; fall back to IRC6 cl_218_5_1
    sl_zone_factor = input_dict.get(KEY_SL_ZONE_FACTOR)
    sl_spectral    = input_dict.get(KEY_SL_SPECTRAL_COEFF)
    sl_ah          = input_dict.get(KEY_SL_HORIZONTAL_COEFF)
    sl_av          = input_dict.get(KEY_SL_VERTICAL_COEFF)
    if not sl_ah or not sl_zone_factor:
        try:
            _zone = input_dict.get(KEY_SL_SEISMIC_ZONE) or input_dict.get('seismic_zone')
            _zmap = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V"}
            _z    = str(_zone).strip().upper()
            if _z.isdigit():
                _z = _zmap.get(_z)
            _smap = {"Type I – Rocky or Hard": 1, "Type II – Medium Soil": 2, "Type III – Soft Soil": 3}
            _st   = _smap.get(str(input_dict.get(KEY_SL_SOIL_TYPE, "")), 1)
            _tp   = input_dict.get(KEY_SL_TIME_PERIOD)
            _damp = input_dict.get(KEY_SL_DAMPING) or "5"
            _dl_v = input_dict.get(KEY_SL_DEAD_LOAD_VALUE)
            _ll_v = input_dict.get(KEY_SL_LIVE_LOAD_VALUE)
            _dead = float(_dl_v) if str(input_dict.get(KEY_SL_DEAD_LOAD_MODE, "")) == "Custom" and _dl_v else 0.0
            _live = float(_ll_v) if str(input_dict.get(KEY_SL_LIVE_LOAD_MODE, "")) == "Custom" and _ll_v else 0.0
            _res  = IRC6_2017.cl_218_5_1(zone=f"Zone {_z}", soil_type=_st, dead_load_kN=_dead,
                        live_load_kN=_live, period_T=float(_tp) if _tp else None,
                        damping_percent=float(_damp))
            if not sl_zone_factor:
                sl_zone_factor = _res.get("Z")
            if not sl_spectral:
                sl_spectral    = _res.get("Sa_g_adjusted")
            if not sl_ah:
                sl_ah          = _res.get("Ah")
            if not sl_av:
                sl_av          = round(_res.get("Ah", 0) * 2 / 3, 4)
        except Exception:
            pass

    def _sl(v, unit=""):
        return f"{float(v):.4f}{unit}" if v not in (None, "") else "N/A"

    # Table 3.6 rows 3 & 4 — effective bridge temperature range and rise/fall.
    # Prefer values already present in output_dict (populated by the additional-
    # inputs UI / design snapshot); otherwise compute the fallback here from the
    # raw shade temperatures and store the results back into output_dict.
    if not output_dict.get(KEY_TL_BRIDGE_TEMP_MIN):
        try:
            # Raw shade temperatures — same source as rows 1 & 2 above. The
            # user-entered value may sit in output_dict (design snapshot) or in
            # input_dict; the weather/location-derived 'shade_temp_*' are added
            # to input_dict during report build. Try all so the fallback fires.
            _tmax = (output_dict.get(KEY_TL_HIGHEST_MAX_TEMP)
                     or input_dict.get(KEY_TL_HIGHEST_MAX_TEMP)
                     or input_dict.get('shade_temp_max'))
            _tmin = (output_dict.get(KEY_TL_LOWEST_MIN_TEMP)
                     or input_dict.get(KEY_TL_LOWEST_MIN_TEMP)
                     or input_dict.get('shade_temp_min'))
            if _tmax and _tmin:
                _res    = IRC6_2017.cl_215_2_effective_bridge_temperature(
                              float(_tmax), float(_tmin), 'metallic', False)
                _bt_min = _res.get('T_min', 0)
                _bt_max = _res.get('T_max', 0)
                _mean   = (_bt_max + _bt_min) / 2.0
                output_dict[KEY_TL_BRIDGE_TEMP_MIN] = f"{_bt_min:.2f}"
                output_dict[KEY_TL_BRIDGE_TEMP_MAX] = f"{_bt_max:.2f}"
                output_dict[KEY_TL_TEMP_RISE]       = f"{_bt_max - _mean:.2f}"
                output_dict[KEY_TL_TEMP_FALL]       = f"{_mean - _bt_min:.2f}"
        except Exception:
            pass

    # --- Table 3.7: Load Combinations (dynamically generated from IRC 6) ---
    _LOAD_LABEL_MAP = {
        'dead_load':         'DL',
        'surfacing':         'SIDL',
        'live_load':         'LL',
        'wind_load':         'WL',
        'thermal_load':      'TL',
        'vehicle_collision': 'VC',
        'barge_impact':      'BI',
        'floating_bodies':   'FB',
        'seismic':           'EQ',
    }

    def _fmt_factors(factors):
        """Format a factors dict into a compact load-case string for the table."""
        parts = []
        for load, val in factors.items():
            label = _LOAD_LABEL_MAP.get(load, load.upper())
            if isinstance(val, dict):  # permanent load with adding/relieving
                add = val.get('adding')
                rel = val.get('relieving')
                add_s = f"{add:.2f}" if add is not None else '--'
                rel_s = f"{rel:.2f}" if rel is not None else '--'
                parts.append(f"{label}({add_s}/{rel_s})")
            else:
                if val is None:
                    continue  # skip N/A factors
                parts.append(f"{label}({val:.2f})")
        return ' + '.join(parts)

    uls_combos = IRC6_2017.uls_load_combinations()
    sls_combos = IRC6_2017.sls_load_combinations()
    lc_rows = []
    for i, combo in enumerate(uls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        lc_rows.append([f"ULS-{i:02d}", cases])
    for i, combo in enumerate(sls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        lc_rows.append([f"SLS-{i:02d}", cases])

    dead_rows = [
        ["Steel Self-Weight Applied", _render_value(input_dict, KEY_MATERIAL_GIRDER_DENSITY, r" kN/m\textsuperscript{3}")],
        ["Concrete Deck Weight", _render_value(input_dict, KEY_MATERIAL_DECK_DENSITY, r" kN/m\textsuperscript{3}")],
        ["Self-Weight Factor", _render_value(input_dict, KEY_PL_SELF_WEIGHT_FACTOR)],
    ]
    surfacing_rows = [
        ["Wearing Course Load", _render_value(input_dict, KEY_WC_MATERIAL) + " x " + _render_value(input_dict, KEY_WC_THICKNESS)],
        ["Additional SIDL (Crash Barrier)", _render_value(input_dict, KEY_CB_LOAD) + " kN/m per barrier"],
        ["Railing Load", _render_value(input_dict, KEY_RL_LOAD_VALUE) + r" kN/m\sdstar{}"],
    ]
    wind_rows = [
        ["Basic Wind Speed, Vb", _render_value(input_dict, 'wind_speed', " m/s") + " [from Project Location]"],
        ["Terrain Type", _render_value(input_dict, KEY_WL_TERRAIN_TYPE)],
        ["Average Exposed Height, H (m)", _render_value(input_dict, KEY_WL_AVG_EXPOSED_HEIGHT, " m")],
        ["Hourly Mean Wind Speed, Vz", vz_str],
        ["Hourly Wind Pressure, Pz", pz_str],
        ["Transverse Wind Force", _render_value(output_dict, KEY_WL_TRANSVERSE_WIND_FORCE, " kN")],
        ["Longitudinal Wind Force", _render_value(output_dict, KEY_WL_LONGITUDINAL_WIND_FORCE, " kN")],
        ["Vertical Wind Force", _render_value(output_dict, KEY_WL_VERTICAL_WIND_FORCE, " kN")],
    ]
    earthquake_rows = [
        ["Seismic Zone", _render_value(input_dict, 'seismic_zone') + " [from Project Location]"],
        ["Zone Factor, Z", _render_value(input_dict, KEY_SL_ZONE_FACTOR)],
        ["Importance Factor, I", _render_value(input_dict, KEY_SL_IMPORTANCE_FACTOR)],
        ["Type of Soil", _render_value(input_dict, KEY_SL_SOIL_TYPE)],
        ["Sa/g", _render_value(input_dict, KEY_SL_SPECTRAL_COEFF)],
        ["Horizontal Seismic Coefficient, Ah", _render_value(input_dict, KEY_SL_HORIZONTAL_COEFF)],
        ["Vertical Seismic Coefficient, Av", _render_value(input_dict, KEY_SL_VERTICAL_COEFF)],
        ["Horizontal Seismic Force (longitudinal)", _render_value(output_dict, KEY_SL_FORCE_LONGITUDINAL, " kN")],
        ["Horizontal Seismic Force (transverse)", _render_value(output_dict, KEY_SL_FORCE_TRANSVERSE, " kN")],
    ]
    temperature_rows = [
        ["Maximum Shade Temperature", _render_value(input_dict, 'shade_temp_max') + r" $^\circ$C"],
        ["Minimum Shade Temperature", _render_value(input_dict, 'shade_temp_min') + r" $^\circ$C"],
        ["Effective Bridge Temp. Range", _render_value(output_dict, KEY_TL_BRIDGE_TEMP_MIN) + " to " + _render_value(output_dict, KEY_TL_BRIDGE_TEMP_MAX) + r" $^\circ$C"],
        ["Temperature Rise / Fall for Design", "+" + _render_value(output_dict, KEY_TL_TEMP_RISE) + r" $^\circ$C / \textminus{}" + _render_value(output_dict, KEY_TL_TEMP_FALL) + r" $^\circ$C"],
    ]

    return r"""
\chapter{Loads and Load Combinations}

This section summarizes all loads applied to the bridge and the load combinations considered for analysis and design.

\vspace{1em}
""" + render_parameter_value_table("Dead Load -- Self Weight", dead_rows) + r"""

\vspace{1em}
""" + render_parameter_value_table("Dead Load for Surfacing (DW)", surfacing_rows) + r"""

\vspace{1em}
""" + render_vehicle_live_load_table(vehicle_rows) + r"""

\vspace{1em}
""" + render_report_table(
    "Footpath Live Load", footpath_rows,
    headers=["parameter", "value", "unit"], align=["L", "C", "C"], escape=False) + r"""

\vspace{1em}
""" + render_parameter_value_table("Wind Load (WL) --- per IRC 6", wind_rows, longtable=True) + r"""

\vspace{1em}
""" + render_parameter_value_table("Earthquake Load (EL) --- per IRC 6", earthquake_rows, longtable=True) + r"""

\vspace{1em}
""" + render_parameter_value_table("Temperature Load (TL) --- per IRC 6", temperature_rows) + r"""

\vspace{1em}
""" + render_report_table("Load Combinations", lc_rows, headers=["combination ID", "load cases"], align=["C", "L"], longtable=True, escape=False) + r"""

\noindent\textit{Note: All IRC 6 load combinations are auto-generated by OsdagBridge. User-defined custom combinations, if any, are appended.}
"""


