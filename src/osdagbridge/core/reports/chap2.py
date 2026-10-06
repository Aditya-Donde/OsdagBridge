# Chapter 2: Input Parameters — exact LaTeX template match


from osdagbridge.core.utils.common import (
    KEY_CARRIAGEWAY_WIDTH,
    KEY_CB_LOAD,
    KEY_CB_TYPE,
    KEY_CROSS_BRACING,
    KEY_DECK_CONCRETE_GRADE_BASIC,
    KEY_DESIGN_MODE,
    KEY_DO_GAMMA_C_BASIC,
    KEY_DO_GAMMA_FLT,
    KEY_DO_GAMMA_M0,
    KEY_DO_GAMMA_M1,
    KEY_DO_GAMMA_MF,
    KEY_DO_GAMMA_S,
    KEY_DO_GAMMA_V,
    KEY_END_DIAPHRAGM,
    KEY_FOOTPATH,
    KEY_GIRDER,
    KEY_INCLUDE_MEDIAN,
    KEY_MD_TYPE,
    KEY_MP_CB_BRACING_SECTION_DESIGNATION,
    KEY_MP_CB_MEMBER_ID,
    KEY_MP_CB_SELECT_GIRDERS,
    KEY_MP_CB_SPACING,
    KEY_MP_CB_TYPE,
    KEY_MP_ED_BRACING_SECTION_DESIGNATION,
    KEY_MP_ED_MEMBER_ID,
    KEY_MP_ED_SELECT_GIRDERS,
    KEY_MP_ED_TYPE,
    KEY_MP_GD_MEMBER_ID,
    KEY_MP_GD_SELECT_GIRDER,
    KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
    KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH,
    KEY_MP_GIRDER_DEPTH,
    KEY_MP_GIRDER_SYMMETRY,
    KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
    KEY_MP_GIRDER_TOP_FLANGE_WIDTH,
    KEY_MP_GIRDER_TORSIONAL_RESTRAINT,
    KEY_MP_GIRDER_TYPE,
    KEY_MP_GIRDER_WARPING_RESTRAINT,
    KEY_MP_GIRDER_WEB_THICKNESS,
    KEY_MP_GIRDER_WEB_TYPE,
    KEY_MP_STIFFENER_BEARING_THICKNESS,
    KEY_MP_STIFFENER_INTERMEDIATE,
    KEY_MP_STIFFENER_INTERMEDIATE_SPACING,
    KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS,
    KEY_MP_STIFFENER_LONGITUDINAL,
    KEY_MP_STIFFENER_NO_BEARING_STIFFENERS,
    KEY_MP_STIFFENER_SPACING,
    KEY_RL_LOAD_VALUE,
    KEY_RL_TYPE,
    KEY_SD_SHEAR_DIAMETER,
    KEY_SD_SHEAR_HEIGHT,
    KEY_SD_SHEAR_STUDS_PER_SECTION,
    KEY_SD_SHEAR_ULTIMATE_STRENGTH,
    KEY_SD_SHEAR_YIELD_STRENGTH,
    KEY_SKEW_ANGLE,
    KEY_SPAN,
    KEY_STRUCTURE_TYPE,
    KEY_TS_DECK_OVERHANG,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_OVERALL_WIDTH,
    KEY_WC_LD_LANE_TABLE_COUNT,
    KEY_WC_MATERIAL,
    KEY_WC_THICKNESS
)

from osdagbridge.core.reports.report_utils import _render_value, get_girder_entries, _tex, render_report_table


def _kv_table(caption, rows, longtable=False):
    return render_report_table(
        caption, rows, headers=["parameter", "value"],
        widths=[1, 1], longtable=longtable, escape=False)

def ch2_input_parameters(m, input_dict, output_dict=None):
    girder_entries = get_girder_entries(input_dict)
    n_girders = len(girder_entries)
    # Median row only shown when the user included a median
    median_rows = []
    if str(input_dict.get(KEY_INCLUDE_MEDIAN, "")).strip().lower() in ("yes", "true", "1"):
        median_rows = [["Median Type", _render_value(input_dict, KEY_MD_TYPE)]]
    return r"""
\chapter{Input Parameters}

\setlength{\abovecaptionskip}{2pt}
\setlength{\belowcaptionskip}{2pt}

This section documents all inputs provided to OsdagBridge. User-provided inputs are clearly distinguished from software-assumed defaults. Where the user did not supply a value, the software has applied the IRC/IS code default or an empirical guideline; these are annotated with an asterisk (\sdstar{}).

\section{Basic Inputs (User-Defined)}
\label{sec:basic-inputs}

\noindent\textit{Note: These inputs are mandatory and were provided by the user.}

""" + _kv_table(
    "Project Location",
    [["Project Location", _tex(m.project_location)],
     ["Latitude / Longitude", _render_value(input_dict, 'latitude') + ', ' + _render_value(input_dict, 'longitude')],
     ["Seismic Zone (IRC 6)", _render_value(input_dict, 'seismic_zone')],
     ["Basic Wind Speed (IRC 6)", _render_value(input_dict, 'wind_speed', ' m/s')],
     ["Shade Temp. Max / Min (IRC 6)", _render_value(input_dict, 'shade_temp_max') + " °C / "
      + _render_value(input_dict, 'shade_temp_min') + " °C"]]) + r"""

""" + _kv_table("Bridge Geometry", [
    ["Type of Structure", _render_value(input_dict, KEY_STRUCTURE_TYPE)],
    ["Span (m)", _render_value(input_dict, KEY_SPAN, ' m')],
    ["Carriageway Width (m)", _render_value(input_dict, KEY_CARRIAGEWAY_WIDTH, ' m')],
    ["Include Median", _render_value(input_dict, KEY_INCLUDE_MEDIAN)],
    ["Footpath", _render_value(input_dict, KEY_FOOTPATH)],
    ["Skew Angle (degrees)", _render_value(input_dict, KEY_SKEW_ANGLE, '°') + r" (IRC 24 Cl. 504.8 limit: $\pm$15°)"]]) + r"""
\vspace{0.4cm}

""" + _kv_table("Material Selection", [
    ["Girder Steel Grade (IS 2062)", _render_value(input_dict, KEY_GIRDER)],
    ["Cross Bracing Steel Grade", _render_value(input_dict, KEY_CROSS_BRACING)],
    ["End Diaphragm Steel Grade", _render_value(input_dict, KEY_END_DIAPHRAGM)],
    ["Concrete Deck Grade (IRC 22)", _render_value(input_dict, KEY_DECK_CONCRETE_GRADE_BASIC)]]) + r"""
\vspace{0.4cm}

\section{Additional Inputs}
\label{sec:additional-inputs}

Where the user has modified additional inputs, those values are reported here. Where no modification was made, the software default is shown.

\vspace{0.8cm}

""" + _kv_table("Typical Section Details", [
    ["Overall Bridge Width (m)", _render_value(input_dict, KEY_TS_OVERALL_WIDTH)],
    ["No. of Girders", _render_value(input_dict, KEY_TS_NO_OF_GIRDERS)],
    ["Girder Spacing (m)", _render_value(input_dict, KEY_TS_GIRDER_SPACING, ' m')],
    ["Deck Overhang Width (m)", _render_value(input_dict, KEY_TS_DECK_OVERHANG, ' m')],
    ["Deck Thickness (mm)", _render_value(input_dict, KEY_TS_DECK_THICKNESS, ' mm')],
    ["Footpath Width (m)", _render_value(input_dict, KEY_TS_FOOTPATH_WIDTH, ' m') + " (IRC 5 Cl. 104.3.6 min: 1.5 m)"],
    ["No. of Traffic Lanes", _render_value(input_dict, KEY_WC_LD_LANE_TABLE_COUNT) + " (per IRC 5 Cl. 104.3.1)"]],
    longtable=True) + r"""

\vspace{0.8em}

""" + _kv_table("Components Details", [
    ["Crash Barrier Type", _render_value(input_dict, KEY_CB_TYPE)],
    ["Crash Barrier Load (kN/m)", _render_value(input_dict, KEY_CB_LOAD)]]
    + median_rows + [
    ["Railing Type", _render_value(input_dict, KEY_RL_TYPE)],
    ["Railing Load (kN/m)", _render_value(input_dict, KEY_RL_LOAD_VALUE)],
    ["Wearing Course Material", _render_value(input_dict, KEY_WC_MATERIAL)],
    ["Wearing Course Thickness (mm)", _render_value(input_dict, KEY_WC_THICKNESS, ' mm')]],
    longtable=True) + r"""

""" + _girder_tables(input_dict, n_girders) + r"""

""" + _bracing_tables(input_dict, n_girders) + r"""

""" + _shear_connector_table(input_dict, output_dict) + r"""

""" + _safety_factors_table(input_dict)


def _girder_tables(input_dict, n_girders):
    # Fetch backend-populated labels via exact suffix pattern (defaults.py)
    # KEY_MP_GD_SELECT_GIRDER.G{i}    = 'G{i}'
    # KEY_MP_GD_MEMBER_ID.G{i}.M1     = 'G{i}M1'
    # All other girder/stiffener keys: {BASE_KEY}.G{i}.M1
    n = n_girders if n_girders >= 1 else 1
    girder_entries = get_girder_entries(input_dict)
    if not girder_entries:
        girder_entries = [(f"Girder {i}", f"M1") for i in range(1, n + 1)]
    
    entries_for_table = [
        (lbl, mid, i)
        for i, (lbl, mid) in enumerate(
            girder_entries,
            start=1,
        )
    ]

    gen_rows = [
        [g_lbl, m_id, _render_value(input_dict, KEY_DESIGN_MODE),
         _render_value(input_dict, f"{KEY_MP_GIRDER_TYPE}.G{i}.M1"),
         _render_value(input_dict, f"{KEY_MP_GIRDER_SYMMETRY}.G{i}.M1")]
        for g_lbl, m_id, i in entries_for_table
    ]
    dim_rows = [
        [g_lbl, _render_value(input_dict, f"{KEY_MP_GIRDER_DEPTH}.G{i}.M1", ' mm'),
         _render_value(input_dict, f"{KEY_MP_GIRDER_WEB_THICKNESS}.G{i}.M1", ' mm'),
         _render_value(input_dict, f"{KEY_MP_GIRDER_TOP_FLANGE_WIDTH}.G{i}.M1", ' mm') + ', '
         + _render_value(input_dict, f"{KEY_MP_GIRDER_TOP_FLANGE_THICKNESS}.G{i}.M1", ' mm'),
         _render_value(input_dict, f"{KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH}.G{i}.M1", ' mm') + ', '
         + _render_value(input_dict, f"{KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS}.G{i}.M1", ' mm')]
        for g_lbl, _, i in entries_for_table
    ]
    rst_rows = [
        [g_lbl,
         _render_value(input_dict, f"{KEY_MP_GIRDER_TORSIONAL_RESTRAINT}.G{i}.M1") + ', '
         + _render_value(input_dict, f"{KEY_MP_GIRDER_WARPING_RESTRAINT}.G{i}.M1"),
         _render_value(input_dict, f"{KEY_MP_GIRDER_WEB_TYPE}.G{i}.M1"),
         _render_value(input_dict, f"{KEY_MP_STIFFENER_INTERMEDIATE}.G{i}.M1") + '; Spacing: '
         + _render_value(input_dict, f"{KEY_MP_STIFFENER_INTERMEDIATE_SPACING}.G{i}.M1", ' mm')
         + '; Thickness: ' + _render_value(input_dict, f"{KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS}.G{i}.M1", ' mm'),
         _render_value(input_dict, f"{KEY_MP_STIFFENER_LONGITUDINAL}.G{i}.M1"),
         "No.: " + _render_value(input_dict, f"{KEY_MP_STIFFENER_NO_BEARING_STIFFENERS}.G{i}.M1")
         + '; Spacing: ' + _render_value(input_dict, f"{KEY_MP_STIFFENER_SPACING}.G{i}.M1", ' mm')
         + '; Thickness: ' + _render_value(input_dict, f"{KEY_MP_STIFFENER_BEARING_THICKNESS}.G{i}.M1", ' mm')]
        for g_lbl, _, i in entries_for_table
    ]

    return (r"""
\newpage

\vspace{0.4em}
\noindent
            
\vspace{4pt}
""" + render_report_table("Girder General Information", gen_rows,
    headers=["Girder", "Member ID", "Design Mode", "Girder Type", "Girder Symmetry"],
    longtable=True, escape=False) + r"""

\vspace{0.6em}

\vspace{4pt}
""" + render_report_table("Girder Section Dimensions", dim_rows,
    headers=["Girder", "Total Depth, D (mm)", r"Web, $t_w$ (mm)",
             r"Top Flange (b\textsubscript{tf}, t\textsubscript{tf}) mm",
             r"Bottom Flange (b\textsubscript{bf}, t\textsubscript{bf}) mm"],
    longtable=True, escape=False) + r"""

\vspace{0.6em}

\vspace{4pt}
""" + render_report_table("Girder Restraint and Stiffener Details", rst_rows,
    headers=["Girder", "Torsional / Warping Restraint", "Web Philosophy",
             "Intermediate Stiffeners", "Longitudinal Stiffeners", "Bearing Stiffener"],
    longtable=True, escape=False) + r"""
""")


def _bracing_tables(input_dict, n_girders):
    n = n_girders if n_girders >= 2 else 2
    panels = [
        (
            _render_value(input_dict, f"{KEY_MP_CB_SELECT_GIRDERS}.G{i}G{i+1}.B{i}M1"),
            _render_value(input_dict, f"{KEY_MP_CB_MEMBER_ID}.G{i}G{i+1}.B{i}M1"),
            _render_value(input_dict, f"{KEY_MP_ED_SELECT_GIRDERS}.G{i}G{i+1}.E{i}M1"),
            _render_value(input_dict, f"{KEY_MP_ED_MEMBER_ID}.G{i}G{i+1}.E{i}M1"),
            i
        )
        for i in range(1, n)
    ]

    cb_rows = [
        [cb_loc, cb_ids, _render_value(input_dict, f"{KEY_MP_CB_TYPE}.G{i}G{i+1}.B{i}M1"),
         _render_value(input_dict, f"{KEY_MP_CB_BRACING_SECTION_DESIGNATION}.G{i}G{i+1}.B{i}M1"),
         _render_value(input_dict, f"{KEY_MP_CB_SPACING}.G{i}G{i+1}.B{i}M1", ' m')]
        for cb_loc, cb_ids, _, _, i in panels
    ]
    ed_rows = [
        [ed_loc, ed_ids, _render_value(input_dict, f"{KEY_MP_ED_TYPE}.G{i}G{i+1}.E{i}M1"),
         _render_value(input_dict, f"{KEY_MP_ED_BRACING_SECTION_DESIGNATION}.G{i}G{i+1}.E{i}M1")]
        for _, _, ed_loc, ed_ids, i in panels
    ]

    return (r"""
\vspace{0.4em}

""" + render_report_table("Member Properties: Cross Bracing Details", cb_rows,
    headers=["Location", "Member IDs", "Type of Bracing", "Bracing Section", "Spacing (m)"],
    longtable=True, escape=False) + r"""

\vspace{0.4em}
\noindent

""" + render_report_table("Member Properties: End Diaphragm Details", ed_rows,
    headers=["Location", "Member IDs", "Type of Bracing", "Bracing Section"],
    longtable=True, escape=False) + r"""
""")


def _shear_connector_table(input_dict, output_dict=None):
    # Stud computed properties live in output_dict (populated by store_design_results)
    od = output_dict or {}
    return r"""
\label{subsec:shear-connectors}

\vspace{2.2em}

\vspace{0.4em}
""" + _kv_table("Shear Connector Details", [
    ["Stud Diameter (mm)", _render_value(od, KEY_SD_SHEAR_DIAMETER, ' mm')],
    ["Stud Height (mm)", _render_value(od, KEY_SD_SHEAR_HEIGHT, ' mm')],
    [r"Stud $f_y$ (MPa)", _render_value(od, KEY_SD_SHEAR_YIELD_STRENGTH, ' MPa')],
    [r"Stud $f_u$ (MPa)", _render_value(od, KEY_SD_SHEAR_ULTIMATE_STRENGTH, ' MPa')],
    ["No. of Studs per Section", _render_value(od, KEY_SD_SHEAR_STUDS_PER_SECTION)]],
    longtable=True) + r"""
"""

def _safety_factors_table(input_dict):
    return r"""
\label{subsec:safety-factors}

\vspace{2.2em}

""" + _kv_table("Partial Safety Factors", [
    [r"$\gamma_{M0}$ (Yielding / Buckling)", _render_value(input_dict, KEY_DO_GAMMA_M0)],
    [r"$\gamma_{M1}$ (Ultimate Stress)", _render_value(input_dict, KEY_DO_GAMMA_M1)],
    [r"$\gamma_C$ (Concrete, Basic)", _render_value(input_dict, KEY_DO_GAMMA_C_BASIC)],
    [r"$\gamma_s$ (Reinforcement)", _render_value(input_dict, KEY_DO_GAMMA_S)],
    [r"$\gamma_v$ (Shear Connectors)", _render_value(input_dict, KEY_DO_GAMMA_V)],
    [r"$\gamma_{fft}$ (Fatigue Load)", _render_value(input_dict, KEY_DO_GAMMA_FLT)],
    [r"$\gamma_{Mft}$ (Fatigue Strength)", _render_value(input_dict, KEY_DO_GAMMA_MF)]],
    longtable=True) + r"""
\vspace{0.2em}
\noindent\textit{Note: All values are per IRC 22 Table 1 unless user-modified.}
"""

