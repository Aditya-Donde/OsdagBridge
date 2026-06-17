# =============================================================================
# OsdagBridge — Report Generator  
# Matches OsdagBridge expected report format:
#   • Full title page with logo
#   • Numbered TOC (Executive Summary + Chapters 1-9)
#   • Executive Summary with Project Overview table, Key Design Outcomes,
#     Figure 1/2/3, and Design Assumptions
#   • Chapter 1  Project Information
#   • Chapter 2  Input Parameters (Tables 1-7: section, bracing, shear
#                connectors, partial safety factors)
#   • Chapter 3  Loads & Load Combinations (Tables 8-14)
#   • Chapter 4  Analysis Results (Tables 15-17 + figure placeholders)
#   • Chapter 5  Design Checks (Tables 18-39, all IRC 22 / IS 800 checks)
#   • Chapter 6  Drawings & Visualizations (6 sub-sections, 8 figures)
#   • Chapter 7  Material Take-off & Quantity Summary (Table 40)
#   • Chapter 8  Design Log & Verification
#   • Chapter 9  References (13 entries)
# =============================================================================

# =============================================================================
# GAPS REPORT — keys used in templates with no canonical KEY_ in common.py
# =============================================================================
# GAP | Template location         | Literal key used             | Notes
# ─────────────────────────────────────────────────────────────────────────────
# 1   | Table 2.1                 | 'latitude'                   | injected from weather_data; no KEY_ yet
# 2   | Table 2.1                 | 'longitude'                  | injected from weather_data; no KEY_ yet
# 3   | Table 2.4 / Exec Summary  | 'num_lanes'                  | design lane count; NOT the UI counter
#     |                           |                              | KEY_WC_LD_LANE_TABLE_COUNT; stays GAP
# 4   | Exec Summary (Proj Ovw)   | 'overall_design_status'      | output_dict value; no KEY_ needed
# 5   | Exec Summary (Proj Ovw)   | 'governing_check'            | output_dict value; no KEY_ needed
# 6   | Exec Summary (Proj Ovw)   | 'overall_utilization_ratio'  | output_dict value; no KEY_ needed
# 7   | Exec Summary (Table 1)    | 'section_designation'        | output_dict value; no KEY_ needed
# 8   | Table 2.7 / 2.8           | ''              | no. of bracing panels; no KEY_ yet
# 9   | Table 2.8                 | ''              | ED spacing; no KEY_ yet
# 10  | Table 4.1, 4.2            | ''             | Load Cases (DL only, Seismic (EL)); ADD_BACKEND_KEY
# 11  | Table 4.1, 5.22           | ''             | Load Combinations (LC-ULS-1, LC-SLS-1); ADD_BACKEND_KEY
# 12  | Table 5.12                | ''                | tau_fn (67 MPa); PLACEHOLDER
# 13  | Table 5.20b, 5.22         | ''                 | Slenderness limits (250, 400); PLACEHOLDER
# 14  | Table 3.4, 3.5, 3.6       | 'wind_speed', 'seismic_zone' | Weather inputs; no KEY_ yet
# 15  | Table 4.1 - 4.3           | ''             | Analysis solver demands (Max BM, SF, Defl)
# 16  | Table 5.7 - 5.9           | 'stiffener_by_member'        | Stiffener capacities; no KEY_ yet
# 17  | Table 5.14 - 5.17         | ''             | Deck slab / shear connector forces
# 18  | Table 5.20 - 5.21         | ''             | Cross-bracing / Diaphragm forces
# 19  | Table 7.1                 | 'steel_girders_mt' (etc)     | All BOM quantities; no KEY_ yet
# 20  | Chapter 8                 | ''             | Design log; no structural KEY_
# =============================================================================

# =============================================================================
# MISSING DATA REPORT — values needed by templates but not yet confirmed
# as provided by the backend in input_dict
# =============================================================================
# #  | KEY_ constant used                        | Template   | Backend action needed
# ─────────────────────────────────────────────────────────────────────────────
# (All missing data cases for Chapters 1-9 resolved or moved to GAPS)
# =============================================================================

#==============================================================================
#   FLOW OF REPORT GENERATION
# ─────────────────────────────────────────────────────────────────────────────
# USER CLICKS "Generate Report" button
#        │
#        ▼
#[output_dock.py] OutputDock._on_report_clicked()
#        │  traverses UI tree to locate `cad_generator` widget
#        └──► [template_page.py] CustomWindow.open_report_dialog(cad_generator)
#                    │
#                    ├── ReportOptionsDialog(parent=self).exec()
#                    │         [report_options.py — user fills form]
#                    │         └── returns request (ReportRequest dataclass)
#                    │
#                    ├── Spawns background thread: _ReportWorker(backend, request, cad_generator)
#                    │
#                    └──► [template_page.py] _ReportWorker.run()
#                                │
#                                └──► [plategirderbridge.py] PlateGirderBridge.generate_design_report(request, cad_generator)
#                                            │
#                                            ├── self.input_dict.copy() → report_inputs
#                                            ├── dict(self.output_dict) → output_dict
#                                            │
#                                            ├──► [report_generator.py] build_report_payload(request, report_inputs, output_dict)
#                                            │           └── returns ReportPayload dataclass
#                                            │
#                                            ├── self._export_cad_figures(cad_generator)
#                                            │    └── exports 4 headless views to ResourceFiles/Images
#                                            │    └── wires paths onto payload.figures (girder_3d, etc.)
#                                            │
#                                            ├── self.build_figure_grillage() → grillage_fig (matplotlib)
#                                            ├── self.figure_to_bytes(grillage_fig) → grillage_bytes
#                                            ├──► [report_generator.py] export_grillage_figure(grillage_bytes, output_dir, file_stem)
#                                            │           └── writes grillage.png → payload.figures.grillage = path
#                                            │
#                                            └──► [report_generator.py] generate_report(payload, request)
#                                                        │
#                                                        ├── OsdagLatexEnv() → discovers pdflatex binary
#                                                        ├── Creates output_dir/assets/
#                                                        ├── Copies logos & payload figures → assets/
#                                                        ├── Calls 10 chapter functions → full_tex string
#                                                        ├── Writes full_tex to tempdir/stem.tex
#                                                        ├── subprocess.run(pdflatex) × 2 passes
#                                                        ├── shutil.copy2(tmp_pdf → output_dir/stem.pdf)
#                                                        └── returns ReportResult(pdf_path, tex_path)
#                                                                  │
#                                                                  ▼
#                                                      [template_page.py] _on_report_finished()
#                                                          if dialog.is_preview → os.startfile(pdf_path)
#                                                          else → CustomMessageBox("Report Saved")
#==============================================================================

import os, shutil, logging, datetime, tempfile, subprocess
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Literal

from osdagbridge.core.utils.common import (
    # Basic inputs
    KEY_SPAN,
    KEY_CARRIAGEWAY_WIDTH,
    KEY_INCLUDE_MEDIAN,
    KEY_FOOTPATH,
    KEY_SKEW_ANGLE,
    KEY_GIRDER,
    KEY_CROSS_BRACING,
    KEY_END_DIAPHRAGM,
    KEY_DECK_CONCRETE_GRADE_BASIC,
    KEY_PROJECT_LOCATION,
    KEY_STRUCTURE_TYPE,
    KEY_DESIGN_MODE,
    # Typical Section
    KEY_TS_GIRDER_SPACING,
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_TS_DECK_OVERHANG,
    KEY_TS_OVERALL_WIDTH,
    KEY_WC_MATERIAL,
    KEY_WC_THICKNESS,
    KEY_CB_LOAD,
    KEY_CB_TYPE,
    KEY_MD_TYPE,
    KEY_RL_TYPE,
    KEY_RL_LOAD_VALUE,
    # Shear Connector output keys (populated by store_design_results)
    KEY_SD_SHEAR_YIELD_STRENGTH,
    KEY_SD_SHEAR_ULTIMATE_STRENGTH,
    KEY_SD_SHEAR_DIAMETER,
    KEY_SD_SHEAR_HEIGHT,
    KEY_SD_SHEAR_STUDS_PER_SECTION,
    # Design Options Cont — Partial Safety Factors
    KEY_DO_GAMMA_M0,
    KEY_DO_GAMMA_M1,
    KEY_DO_GAMMA_C_BASIC,
    KEY_DO_GAMMA_S,
    KEY_DO_GAMMA_V,
    KEY_DO_GAMMA_FLT,
    KEY_DO_GAMMA_MF,
    # Girder geometry
    KEY_MP_GIRDER_TYPE,
    KEY_MP_GIRDER_SYMMETRY,
    KEY_MP_GIRDER_DEPTH,
    KEY_MP_GIRDER_WEB_THICKNESS,
    KEY_MP_GIRDER_TOP_FLANGE_WIDTH,
    KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
    KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH,
    KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
    KEY_MP_GIRDER_TORSIONAL_RESTRAINT,
    KEY_MP_GIRDER_WARPING_RESTRAINT,
    KEY_MP_GIRDER_WEB_TYPE,
    # Stiffener
    KEY_MP_STIFFENER_INTERMEDIATE,
    KEY_MP_STIFFENER_INTERMEDIATE_SPACING,
    KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS,
    KEY_MP_STIFFENER_LONGITUDINAL,
    # Cross Bracing
    KEY_MP_CB_SELECT_GIRDERS,
    KEY_MP_CB_MEMBER_ID,
    KEY_MP_CB_TYPE,   # string "member_properties.cross_bracing_details.type"
                              # (line 329 of common.py); shadows the list at line 283
    KEY_MP_CB_BRACING_SECTION_DESIGNATION,
    KEY_MP_CB_SPACING,
    # End Diaphragm
    KEY_MP_ED_SELECT_GIRDERS,
    KEY_MP_ED_MEMBER_ID,
    KEY_MP_ED_TYPE,
    KEY_MP_ED_BRACING_SECTION_DESIGNATION,
    # Lane Details
    KEY_WC_LD_LANE_TABLE_COUNT,
    # Girder selector / Member ID (suffixed: .G{n} and .G{n}.M1)
    KEY_MP_GD_SELECT_GIRDER,
    KEY_MP_GD_MEMBER_ID,
    # Steel design section designation
    KEY_SD_SECTION_DESIGNATION,
    # Permanent Load
    KEY_PL_SELF_WEIGHT_FACTOR,
    KEY_MATERIAL_GIRDER_DENSITY,
    KEY_MATERIAL_DECK_DENSITY,
    # Live Load
    KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_70R_WHEELED,
    KEY_LL_IRC_70R_TRACKED,
    KEY_LL_IRC_AA_WHEELED,
    KEY_LL_IRC_AA_TRACKED,
    KEY_LL_IRC_CLASS_SV,
    KEY_LL_IRC_70R_BOGIE,
    KEY_LL_IRC_CLASS_FATIGUE,
    KEY_LL_CUSTOM_VEHICLES,
    # Wind Load (computed values)
    KEY_WL_BASIC_WIND_SPEED,
    KEY_WL_TERRAIN_TYPE,
    KEY_WL_AVG_EXPOSED_HEIGHT,
    KEY_WL_HOURLY_MEAN_WIND,
    KEY_WL_HOURLY_WIND_PRESSURE,
    KEY_WL_TRANSVERSE_WIND_FORCE,
    KEY_WL_LONGITUDINAL_WIND_FORCE,
    KEY_WL_VERTICAL_WIND_FORCE,
    # Seismic Load (computed values)
    KEY_SL_SEISMIC_ZONE,
    KEY_SL_ZONE_FACTOR,
    KEY_SL_IMPORTANCE_FACTOR,
    KEY_SL_SOIL_TYPE,
    KEY_SL_SPECTRAL_COEFF,
    KEY_SL_HORIZONTAL_COEFF,
    KEY_SL_VERTICAL_COEFF,
    # Temperature Load (computed values)
    KEY_TL_BRIDGE_TEMP_MIN,
    KEY_TL_BRIDGE_TEMP_MAX,
    KEY_TL_TEMP_RISE,
    KEY_TL_TEMP_FALL,
    # Section properties card
    KEY_SD_TOTAL_DEPTH,
    KEY_SD_TOP_FLANGE_WIDTH,
    KEY_SD_TOP_FLANGE_THICKNESS,
    KEY_SD_BOTTOM_FLANGE_WIDTH,
    KEY_SD_BOTTOM_FLANGE_THICKNESS,
    KEY_SD_WEB_THICKNESS,
    KEY_MP_GIRDER_SECTIONAL_AREA,
    KEY_MP_GIRDER_SECTIONAL_IZ,
    KEY_MP_GIRDER_ELASTIC_MODULUS_ZZ,
    KEY_MP_GIRDER_PLASTIC_MODULUS_ZUZ,
    KEY_SD_SECTION_PROP_AREA,
    KEY_SD_SECTION_PROP_IZ,
    KEY_SD_SECTION_PROP_ZZ,
    KEY_SD_SECTION_PROP_ZUZ,
    KEY_SD_EFFECTIVE_SLAB_WIDTH,
    KEY_SD_COMPOSITE_IZ,
    KEY_SD_PNA_DEPTH,
    KEY_SD_MU_APPLIED,
    KEY_SD_MD_CAPACITY,
    KEY_SD_FLANGE_SLENDERNESS,
    KEY_SD_WEB_SLENDERNESS,
    KEY_SD_WEB_CLASS_LIMIT,
    KEY_SD_FLANGE_CLASS_LIMIT,
    KEY_SD_CLASS_FLANGE,
    KEY_SD_CLASS_WEB,
    KEY_SD_SECTION_CLASS,
    KEY_SD_SHEAR_VU,
    KEY_SD_SHEAR_AV,
    KEY_SD_PANEL_CD,
    KEY_SD_SHEAR_KV,
    KEY_SD_SHEAR_LAMBDA_W,
    KEY_SD_SHEAR_TAU_B,
    KEY_SD_SHEAR_VCR,
    KEY_SD_HIGH_SHEAR,
    KEY_SD_MDV,
    KEY_SD_MN_AXIAL,
    KEY_SD_MN_MOMENT,
    KEY_SD_MN_RATIO,
    KEY_SD_LTB_MCR,
    KEY_SD_LTB_LAMBDA,
    KEY_SD_LTB_CHI,
    KEY_SD_LTB_MB,
    KEY_SD_STIFF_METHOD,
    KEY_SD_STIFF_INT_THICK,
    KEY_SD_STIFF_INT_SPACING,
    KEY_SD_STIFF_END_THICK,
    KEY_SD_STIFF_END_COUNT,
    KEY_SD_STIFF_LONG,
    KEY_SD_IS_IYS_MIN,
    KEY_SD_IS_IYS_PROV,
    KEY_SD_IS_FQ,
    KEY_SD_IS_FQD,
    KEY_SD_BS_R,
    KEY_SD_BS_FCDW_WB,
    KEY_SD_BS_FCDW_LC,
    KEY_SD_BS_FPSD,
    KEY_SD_BS_FCD,
    # Deflection check keys (Table 5.10)
    KEY_SD_DEFL_LIVE,
    KEY_SD_DEFL_TOTAL,
    KEY_SD_DEFL_ALLOW_LIVE,
    KEY_SD_DEFL_ALLOW_TOTAL,
    # SLS stress-limitation keys (Table 5.11) — nested in output_dict["design_results"]
    KEY_SD_STRESS_STEEL,
    KEY_SD_STRESS_STEEL_ALLOWABLE,
    # Per-girder ULS/SLS check summary (Table 5.12 fatigue) — nested in design_results
    KEY_SD_ULS_PER_GIRDER,
    # Shear connector capacity keys (Table 5.14) — nested in design_results
    KEY_SD_SC_Qu_kN,
    KEY_SD_SC_Qr_kN,
    # Shear connector spacing keys (Table 5.15) — nested in design_results
    KEY_SD_SC_SL1,
    KEY_SD_SC_SL2,
    KEY_SD_SC_SR,
    # Transverse shear & detailing keys (Table 5.16) — nested in design_results
    KEY_SD_TS_VL,
    KEY_SD_TS_VRD,
    KEY_SD_SC_D_LIMIT,
    KEY_SD_SC_EDGE_DIST,
    KEY_SD_SC_REQ_EDGE_DIST,
    KEY_DS_STUD_DIAMETER,
    # Utilizations
    KEY_UTIL_FLEXURE,
    KEY_UTIL_SHEAR,
    KEY_UTIL_LTB,
    KEY_UTIL_DEFLECTION_CRACK,
    KEY_UTIL_INTERACTION,
    KEY_UTIL_LONG_TRANS_SHEAR,
    # Deck materials & cover (read from input for Tables 5.17(a)-(g)).
    KEY_DS_TOP_CLEAR_COVER, KEY_DS_BOTTOM_CLEAR_COVER,
    KEY_DS_REINF_MATERIAL, KEY_MATERIAL_DECK_FCK, KEY_MATERIAL_DECK_FCTM,
    # Deck Slab Design — report output keys (Tables 5.17(a)-(g)),
    # stored in output_dict["deck_report_values"] by design_deck_slab().
    KEY_DD_VEHICLE, KEY_DD_IMPACT_FACTOR, KEY_DD_GAMMA_DL,
    KEY_DD_GAMMA_LL, KEY_DD_SPAN, KEY_DD_WDL,
    KEY_DD_WHEEL_LOAD, KEY_DD_TYRE_WIDTH, KEY_DD_FY,
    KEY_DD_M_DL, KEY_DD_M_LL, KEY_DD_M_ULS_SAG,
    KEY_DD_M_ULS_HOG, KEY_DD_D_BOT, KEY_DD_D_TOP,
    KEY_DD_MU_BOT, KEY_DD_MU_TOP, KEY_DD_AS_REQ_BOT,
    KEY_DD_AS_REQ_TOP, KEY_DD_M_BARRIER,
    KEY_DD_M_DL_OH, KEY_DD_M_LL_OH, KEY_DD_M_ULS_OH,
    KEY_DD_D_OH, KEY_DD_MU_OH, KEY_DD_AS_REQ_OH,
    KEY_DD_PUNCH_VED_KN, KEY_DD_TYRE_LENGTH, KEY_DD_PUNCH_C1,
    KEY_DD_PUNCH_C2, KEY_DD_PUNCH_U1, KEY_DD_PUNCH_VED,
    KEY_DD_VRD_C_MPA, KEY_DD_PUNCH_OK,
    KEY_DD_SHEAR_VED, KEY_DD_SHEAR_VRDC, KEY_DD_SHEAR_OK,
    KEY_DD_AS_MIN, KEY_DD_WK_BOT, KEY_DD_WK_TOP,
    KEY_DD_WK_OH, KEY_DD_WK_LIMIT, KEY_DD_DIA_BOT,
    KEY_DD_SPC_BOT, KEY_DD_AS_BOT, KEY_DD_DIA_TOP,
    KEY_DD_SPC_TOP, KEY_DD_AS_TOP, KEY_DD_DIA_OH,
    KEY_DD_SPC_OH, KEY_DD_AS_OH, KEY_DD_AS_LONG,
    KEY_DD_MIN_COVER, KEY_DD_COVER_OK, KEY_DD_SPACING_MAX,
    KEY_DD_HAS_OVERHANG,
)


logger = logging.getLogger(__name__)

# --- TEMPLATES START ---


# =============================================================================
# LaTeX template sections for OsdagBridge Design Report
# Matches the LaTeX template used in the OsdagBridge desktop application.
# Color: osdagGreen = #91B014
# =============================================================================

def _tex(value):
    """Escape a Python value for safe LaTeX embedding."""
    s = str(value) if value is not None else ''
    if not s:
        return r''
    s = s.replace('\\', r'\textbackslash{}')
    for ch, esc in [('&', r'\&'), ('%', r'\%'), ('$', r'\$'), ('#', r'\#'),
                    ('{', r'\{'), ('}', r'\}'),          
                    ('_', r'\_\allowbreak{}'),            
                    ('~', r'\textasciitilde{}'), ('^', r'\^{}')]:
        s = s.replace(ch, esc)
    s = s.replace(':', r':\allowbreak{}')
    return s


def _render_value(source_dict, key, unit=""):
    val = source_dict.get(key)
    if val in ("", None):
        return ""
    return _tex(val) + unit


def get_girder_entries(input_dict):
    """
    Retrieve all girder labels and member IDs from backend keys.

    Usage Example:
    --------------------------
    girder_entries = get_girder_entries(bridge.input_dict)
    
    # 1. Fallback handling (if backend hasn't populated keys yet)
    if not girder_entries:
        n = int(bridge.input_dict.get(KEY_TS_NO_OF_GIRDERS, 1))
        girder_entries = [(f"Girder {i}", f"M1") for i in range(1, n + 1)]
        
    # 2. Get total number of girders safely
    n_girders = len(girder_entries)
    
    # 3. Iterate over the girders to build table rows
    for lbl, mid in girder_entries:
        # lbl will be e.g., "G1", mid will be e.g., "G1M1"
        # Access girder specific keys dynamically:
        # val = input_dict.get(f"{KEY_MP_GIRDER_DEPTH}.{lbl}.{mid}")
        pass

    Returns:
        List[Tuple[str, str]]
    """
    n = int(input_dict.get(KEY_TS_NO_OF_GIRDERS, 0))

    entries = []

    for i in range(1, n + 1):
        entries.append(
            (
                input_dict.get(f"{KEY_MP_GD_SELECT_GIRDER}.G{i}", ""),
                input_dict.get(f"{KEY_MP_GD_MEMBER_ID}.G{i}.M1", ""),
            )
        )

    return entries


def _fig_or_placeholder(path, caption, width=r'0.9\textwidth'):
    """Embed figure if path is provided (file already copied to assets), else show placeholder box.
    path is the relative path as pdflatex will see it (e.g. 'assets/plan.png').
    """
    if path:
        p = path.replace('\\', '/')
        return (r'\begin{figure}[H]' + '\n'
                r'\centering' + '\n'
                r'\includegraphics[width=' + width + ']{' + p + '}\n'
                r'\caption*{' + caption + '}\n'
                r'\end{figure}')
    return (r'\begin{figure}[H]' + '\n'
            r'\centering' + '\n'
            r'\fbox{\parbox{0.97\textwidth}{' + '\n'
            r'\textit{[ PLACEHOLDER: ' + caption + r' ]}' + '\n'
            r'}}' + '\n'
            r'\caption*{' + caption + '}\n'
            r'\end{figure}')


# ═══════════════════════════════════════════════════════════════════════════════
# PREAMBLE
# ═══════════════════════════════════════════════════════════════════════════════

def preamble(project_name, job_number, report_date, report_version='Rev 0'):
    pn = _tex(project_name)
    jn = _tex(job_number)
    rd = _tex(report_date)
    rv = _tex(report_version)
    return r"""
\documentclass[12pt,a4paper]{report}

% Packages
\usepackage[a4paper, margin=1in]{geometry}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{booktabs}
\usepackage{array}
\usepackage{tabularx}
\usepackage{float}
\usepackage{fancyhdr}
\usepackage[hidelinks]{hyperref}
\usepackage{xcolor}
\usepackage{setspace}
\usepackage{enumitem}
\usepackage{caption}
\usepackage{subcaption}
\usepackage{multirow}
\usepackage{colortbl}
\usepackage{longtable}
\usepackage{changepage}
\usepackage{titlesec}
\usepackage{titletoc}
\usepackage{lastpage}
\usepackage{makecell}
\usepackage{etoolbox}
\usepackage{needspace}

% Prevent tables from overflowing past the page bottom:
% if fewer than 5 baseline-skips remain, break to the next page first.
\BeforeBeginEnvironment{table}{\needspace{5\baselineskip}}
\BeforeBeginEnvironment{longtable}{\needspace{5\baselineskip}}

\definecolor{osdagGreen}{HTML}{91B014}

\fancypagestyle{main}{
  \fancyhf{}
  \fancyhead[L]{""" + pn + r""" $|$ """ + jn + r"""}
  \fancyhead[R]{""" + rd + r""" $|$ """ + rv + r"""}
  \fancyfoot[L]{Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}
  \fancyfoot[R]{Page \thepage\ of \pageref{LastPage}}
  \renewcommand{\headrule}{\color{osdagGreen}\hrule width\headwidth height 1pt \vspace{2pt}}
  \renewcommand{\footrule}{%
    \ifbool{hasSDonPage}{%
      \vspace{-20pt}%
      \hbox to \headwidth{\textcolor{black}{\footnotesize\textit{* Software default value}}\hfil}%
      \vspace{4pt}%
    }{%
      \vspace{-8pt}%
    }%
    \color{osdagGreen}\hrule width\headwidth height 1pt \vspace{6pt}%
  }
}
\fancypagestyle{plain}{
  \fancyhf{}
  \fancyhead[L]{""" + pn + r""" $|$ """ + jn + r"""}
  \fancyhead[R]{""" + rd + r""" $|$ """ + rv + r"""}
  \fancyfoot[L]{Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}
  \fancyfoot[R]{Page \thepage\ of \pageref{LastPage}}
  \renewcommand{\headrule}{\color{osdagGreen}\hrule width\headwidth height 1pt \vspace{2pt}}
  \renewcommand{\footrule}{%
    \ifbool{hasSDonPage}{%
      \vspace{-20pt}%
      \hbox to \headwidth{\textcolor{black}{\footnotesize\textit{* Software default value}}\hfil}%
      \vspace{4pt}%
    }{%
      \vspace{-8pt}%
    }%
    \color{osdagGreen}\hrule width\headwidth height 1pt \vspace{6pt}%
  }
}
\fancypagestyle{firstpage}{
  \fancyhf{}
  \renewcommand{\headrulewidth}{0pt}
  \fancyfoot[L]{Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}
  \fancyfoot[R]{Page \thepage\ of \pageref{LastPage}}
  \renewcommand{\footrule}{\vspace{-8pt}\color{osdagGreen}\hrule width\headwidth height 1pt \vspace{6pt}}
}
\pagestyle{main}
\setstretch{1.15}

% Custom Commands
\newcommand{\placeholder}[1]{\textit{\textless #1\textgreater}}
\newcommand{\todo}[1]{\colorbox{yellow}{TODO: #1}}
\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}
\newcolumntype{C}[1]{>{\centering\arraybackslash}p{#1}}
\newcolumntype{R}[1]{>{\raggedleft\arraybackslash}p{#1}}

% Software-default asterisk
\newcommand{\sdstar}{\textsuperscript{*}}
\newbool{hasSDonPage}
\boolfalse{hasSDonPage}
\newcommand{\markSD}{\global\booltrue{hasSDonPage}}
\renewcommand{\sdstar}{\textsuperscript{*}\markSD{}}
\AddToHook{shipout/before}{\global\boolfalse{hasSDonPage}}

\title{\Large\textbf{OsdagBridge} \\ \normalsize Open Source Software for Steel Girder Bridge Design \\ \vspace{2cm} \large Design Report}
\author{}
\date{}

\begin{document}
"""


# ═══════════════════════════════════════════════════════════════════════════════
# TITLE PAGE
# ═══════════════════════════════════════════════════════════════════════════════

def title_page(m, osdag_logo, org_logo):
    if osdag_logo:
        lhs = r'\includegraphics[width=\linewidth,keepaspectratio]{' + osdag_logo.replace('\\', '/') + r'}'
    else:
        lhs = r'\textit{(Osdag Logo)}'

    if org_logo:
        rhs = r'\includegraphics[width=\linewidth,height=2.2cm,keepaspectratio]{' + org_logo.replace('\\', '/') + r'}'
    else:
        rhs = r''

    logos_tex = r"""\noindent
\begin{minipage}[c]{0.6\textwidth}
\raggedright
""" + lhs + r"""
\end{minipage}%
\hfill
\begin{minipage}[c]{0.35\textwidth}
\raggedleft
""" + rhs + r"""
\end{minipage}
\\[1cm]
"""

    return r"""
\begin{titlepage}
\thispagestyle{firstpage}
\centering
\vspace*{1.5cm}
""" + logos_tex + r"""
{\Huge \textbf{OsdagBridge}}\\[0.3cm]
{\large Open Source Software for Steel Girder Bridge Design}\\[1.5cm]
{\Large Design Report}\\[1.5cm]
\begin{tabular}{|L{4cm}|L{10cm}|}
\hline
\textbf{Project Name} & """ + _tex(m.project_name) + r""" \\
\hline
\textbf{Project Location} & """ + _tex(m.project_location) + r""" \\
\hline
\textbf{Author / Designer} & """ + _tex(m.designer) + r""" \\
\hline
\textbf{Reviewer} & """ + _tex(m.reviewer) + r""" \\
\hline
\textbf{Organization} & """ + _tex(m.company) + r""" \\
\hline
\textbf{Client Name and Organization} & """ + _tex(m.client) + r""" \\
\hline
\textbf{Job Number} & """ + _tex(m.job_number) + r""" \\
\hline
\textbf{Date} & """ + _tex(m.report_date) + r""" \\
\hline
\textbf{Report Version} & """ + (_tex(m.subtitle) if m.subtitle else '') + r""" \\
\hline
\end{tabular}
\end{titlepage}
"""


# ═══════════════════════════════════════════════════════════════════════════════
# TOC
# ═══════════════════════════════════════════════════════════════════════════════

def toc_section():
    return r"""
% Chapter / TOC Formatting
\titleformat{\chapter}[block]
  {\normalfont\Large\bfseries\centering}{\thechapter}{1em}{}
\titlespacing*{\chapter}{0pt}{0pt}{10pt}
\setcounter{tocdepth}{2}

% TOC styling using titletoc
\titlecontents{chapter}[1.5em]
  {\normalfont\vspace{2pt}}
  {\contentslabel{1.5em}}
  {\hspace*{-1.5em}}
  {\hfill\contentspage}

\titlecontents{section}[3.8em]
  {\normalfont}
  {\contentslabel{2.3em}}
  {\hspace*{-2.3em}}
  {\hfill\contentspage}

\titlecontents{subsection}[7.0em]
  {\normalfont}
  {\contentslabel{3.2em}}
  {\hspace*{-3.2em}}
  {\hfill\contentspage}

\newpage
\renewcommand{\contentsname}{\centering\Large\bfseries Table of Contents}
\tableofcontents
"""


# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTIVE SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

def executive_summary(input_dict, output_dict, fig_paths) -> str:
    plan_fig = _fig_or_placeholder(fig_paths.get('girder_top'), 'Figure 1 -- Overall Bridge Plan')
    cs_fig = _fig_or_placeholder(fig_paths.get('cross_section'),
                                  'Figure 2 -- Typical Cross-Section (with girder, deck, barriers, footpath)')
    geom_fig = _fig_or_placeholder(fig_paths.get('final_geometry'),
                                    'Figure 3 -- 3D View of Bridge Superstructure')

    # All girders share the same section, governing check, and UR
    sec = _render_value(input_dict, KEY_SD_SECTION_DESIGNATION)

    gov_val = output_dict.get('governing_check', '')
    gov = _tex(gov_val) if gov_val not in (None, '', 'None') else ''

    ur_val = output_dict.get('overall_utilization_ratio', '')
    ur = _tex(ur_val) if ur_val not in (None, '', 'None') else ''

    # --- Dynamic Table 1: fetch backend-populated labels via exact suffix pattern ---
    # defaults.py populates: KEY_MP_GD_SELECT_GIRDER + '.G{i}' = 'G{i}'
    #                        KEY_MP_GD_MEMBER_ID     + '.G{i}.M1' = 'G{i}M1'
    labels = get_girder_entries(input_dict)
    if not labels:
        labels = [("", "")]
    n_cols = len(labels)

    # Column widths: row-label column fixed at 2.8cm; girder columns share remainder
    label_col_cm = 2.8
    # Available width ≈ 15.0cm for A4 with 1in margins; each girder col gets equal share
    girder_col_cm = round(max(1.5, (15.0 - label_col_cm) / n_cols), 1)
    col_spec = '|C{' + str(label_col_cm) + 'cm}|' + '|'.join(['C{' + str(girder_col_cm) + 'cm}'] * n_cols) + '|'

    # Header row
    hdr_cells = ' &\n  '.join([r'\textbf{' + _tex(lbl) + '}' for lbl, _ in labels])
    header_row = r'  \textbf{} &' + '\n  ' + hdr_cells + r' \\' + '\n'

    # Member ID row
    mid_cells = ' & '.join([_tex(mid) for _, mid in labels])
    member_id_row = 'Member ID & ' + mid_cells + r' \\' + '\n'

    # Section / Governing Check / UR rows
    sec_cells = ' & '.join([sec] * n_cols)
    sections = f"Section Designation & {sec_cells} \\\\"
    gov_cells = ' & '.join([gov] * n_cols)
    gov_checks = f"Governing Check & {gov_cells} \\\\"
    ur_cells = ' & '.join([ur] * n_cols)
    urs = f"Utilization Ratio & {ur_cells} \\\\"

    table1 = (r'\noindent\textbf{Table 1 -- Final Bridge Geometry (after optimization)}' + '\n\n'
              r'\vspace{0.4em}' + '\n'
              r'\noindent' + '\n'
              r'\begin{tabular}{' + col_spec + '}\n'
              r'\hline' + '\n'
              + header_row +
              r'\hline' + '\n'
              + member_id_row +
              r'\hline' + '\n'
              + sections + '\n'
              r'\hline' + '\n'
              + gov_checks + '\n'
              r'\hline' + '\n'
              + urs + '\n'
              r'\hline' + '\n'
              r'\end{tabular}')

    return r"""
\newpage
{\centering\Large\bfseries Executive Summary\par}
\addcontentsline{toc}{chapter}{Executive Summary}
\vspace{0.8em}

This section provides a concise summary of the bridge design, key inputs, governing loads, and final design outcomes.

\section*{Project Overview}
\addcontentsline{toc}{section}{Project Overview}
\label{sec:project-overview}


\begin{tabular}{|L{5.5cm}|L{8.5cm}|}
\hline
\textbf{Bridge Type} & """ + (_render_value(input_dict, KEY_STRUCTURE_TYPE)) + r""" \\

\hline
\textbf{Design Standard} & IRC 5, IRC 6, IRC 22, IRC 24, IS 800 \\
\hline
\textbf{Span} & """ + (_render_value(input_dict, KEY_SPAN, ' m')) + r""" \\
\hline
\textbf{Carriageway Width} & """ + (_render_value(input_dict, KEY_CARRIAGEWAY_WIDTH, ' m')) + r""" \\
\hline
\textbf{No. of Traffic Lanes} & """ + (_render_value(input_dict, KEY_WC_LD_LANE_TABLE_COUNT)) + r""" \\
\hline
\textbf{No. of Girders} & """ + (_render_value(input_dict, KEY_TS_NO_OF_GIRDERS)) + r""" \\
\hline
\textbf{Girder Spacing} & """ + (_render_value(input_dict, KEY_TS_GIRDER_SPACING)) + r""" \\
\hline
\textbf{Deck Thickness} & """ + (_render_value(input_dict, KEY_TS_DECK_THICKNESS)) + r""" \\
\hline
\textbf{Overall Design Status} & """ + (_tex(output_dict.get('overall_design_status', ''))) + r""" \\
\hline
\textbf{Governing Check} & """ + (_tex(output_dict.get('governing_check', ''))) + r""" \\
\hline
\textbf{Overall Utilization Ratio (max)} & """ + (_tex(output_dict.get('overall_utilization_ratio', ''))) + r""" \\
\hline
\end{tabular}


""" + plan_fig + r"""

\newpage

""" + cs_fig + '\n\n' + geom_fig + '\n\n' + table1 + r"""

\vspace{0.4em}
\noindent\textit{Note: Utilization ratio (UR) = demand / capacity. A value $< 1.0$ indicates a passing check.}

\vspace{1em}

\section*{Key Design Outcomes Summary}
\addcontentsline{toc}{section}{Key Design Outcomes Summary}
\label{sec:key-outcomes}

\noindent Girder design pass \\
Cross bracing design pass \\
End Diaphragm design pass \\
Deck design pass

\section*{Design Assumptions and Limitations}
\addcontentsline{toc}{section}{Design Assumptions and Limitations}
\label{sec:assumptions}

\begin{itemize}
\item Additional inputs not provided by the user were assumed by software per IRC/IS code defaults or practical consideration.
\item Grillage analysis was performed using OSPGrillage assuming simply supported I-girders.
\item Substructure and foundation design are not included in this report.
\item Splice connections and bearings are not designed in this version.
\end{itemize}

% Restore numbered chapter format
\titleformat{\chapter}[block]{\normalfont\Large\bfseries\centering}{\thechapter}{1em}{}
\titlespacing*{\chapter}{0pt}{-30pt}{10pt}
"""


# ═══════════════════════════════════════════════════════════════════════════════
# CHAPTER 1: Project Information
# ═══════════════════════════════════════════════════════════════════════════════

def ch1_project_info(m):
    return r"""
\chapter{Project Information}

This section records all project metadata as entered by the designer.

\section{Project and Design Team Details}
\label{sec:project-details}


\begin{tabular}{|L{5.5cm}|L{8.5cm}|}
\hline
\textbf{Project Name} & """ + _tex(m.project_name) + r""" \\
\hline
\textbf{Project Location} & """ + _tex(m.project_location) + r""" \\
\hline
\textbf{Designer} & """ + _tex(m.designer) + r""" \\
\hline
\textbf{Reviewer} & """ + _tex(m.reviewer) + r""" \\
\hline
\textbf{Organization} & """ + _tex(m.company) + r""" \\
\hline
\textbf{Client} & """ + _tex(m.client) + r""" \\
\hline
\textbf{Software Version} & OsdagBridge \\
\hline
\end{tabular}


\section{Applicable Codes and Standards}
\label{sec:codes}

\begin{itemize}
\item Indian Roads Congress (IRC) 5: General Features of Design
\item Indian Roads Congress (IRC) 6: Loads and Load Combinations
\item Indian Roads Congress (IRC) 22: Composite Construction (Limit State Design)
\item Indian Roads Congress (IRC) 24: Steel Road Bridges (Limit State Method)
\item Indian Roads Congress (IRC) 112: Concrete Road Bridges (deck design)
\item Indian Roads Congress Special Publication (IRC SP) 114: Seismic Design of Road Bridges
\item Indian Standard (IS) 800: General Construction in Steel
\item Indian Standard (IS) 2062: Hot Rolled Structural Steel Specification
\item Indian Standard (IS) 6006: Steel Bearings
\end{itemize}
"""


# Chapter 2: Input Parameters — exact LaTeX template match


def ch2_input_parameters(m, input_dict, output_dict=None):
    girder_entries = get_girder_entries(input_dict)
    n_girders = len(girder_entries)
    return r"""
\chapter{Input Parameters}

\setlength{\abovecaptionskip}{2pt}
\setlength{\belowcaptionskip}{2pt}

This section documents all inputs provided to OsdagBridge. User-provided inputs are clearly distinguished from software-assumed defaults. Where the user did not supply a value, the software has applied the IRC/IS code default or an empirical guideline; these are annotated with an asterisk (\sdstar{}).

\section{Basic Inputs (User-Defined)}
\label{sec:basic-inputs}

\noindent\textit{Note: These inputs are mandatory and were provided by the user.}

\noindent\textbf{Table 2.1 Project Location}
\label{subsec:project-location}


\begin{tabular}{|L{5.5cm}|L{8.5cm}|}
\hline
\textbf{Project Location} & """ + _tex(m.project_location) + r""" \\
\hline
\textbf{Latitude / Longitude} & """ + (_render_value(input_dict,'latitude')) + ', ' + (_render_value(input_dict,'longitude')) + r""" \\
\hline
\textbf{Seismic Zone (IRC 6)} & """ + (_render_value(input_dict,'seismic_zone')) + r""" \\
\hline
\textbf{Basic Wind Speed (IRC 6)} & """ + (_render_value(input_dict,'wind_speed', ' m/s')) + r""" \\
\hline
\textbf{Shade Temp. Max / Min (IRC 6)} & """ + (_render_value(input_dict,'shade_temp_max','')) + r""" °C / """ + (_render_value(input_dict,'shade_temp_min','')) + r""" °C \\
\hline
\end{tabular}
\vspace{0.4cm}

\noindent\textbf{Table 2.2 Bridge Geometry}
\label{subsec:bridge-geometry}


\begin{tabular}{|L{5.5cm}|L{8.5cm}|}
\hline
\textbf{Type of Structure} & """ + (_render_value(input_dict, KEY_STRUCTURE_TYPE)) + r""" \\
\hline
\textbf{Span (m)} & """ + (_render_value(input_dict, KEY_SPAN, ' m')) + r""" \\
\hline
\textbf{Carriageway Width (m)} & """ + (_render_value(input_dict, KEY_CARRIAGEWAY_WIDTH, ' m')) + r""" \\
\hline
\textbf{Include Median} & """ + (_render_value(input_dict, KEY_INCLUDE_MEDIAN)) + r""" \\
\hline
\textbf{Footpath} & """ + (_render_value(input_dict, KEY_FOOTPATH)) + r""" \\
\hline
\textbf{Skew Angle (degrees)} & """ + (_render_value(input_dict, KEY_SKEW_ANGLE, '°')) + r""" (IRC 24 Cl. 504.8 limit: $\pm$15°) \\
\hline
\end{tabular}
\vspace{0.4cm}

\noindent\textbf{Table 2.3 Material Selection}
\label{subsec:material}


\begin{tabular}{|L{5.5cm}|L{8.5cm}|}
\hline
\textbf{Girder Steel Grade (IS 2062)} & """ + (_render_value(input_dict, KEY_GIRDER)) + r""" \\
\hline
\textbf{Cross Bracing Steel Grade} & """ + (_render_value(input_dict, KEY_CROSS_BRACING)) + r""" \\
\hline
\textbf{End Diaphragm Steel Grade} & """ + (_render_value(input_dict, KEY_END_DIAPHRAGM)) + r""" \\
\hline
\textbf{Concrete Deck Grade (IRC 22)} & """ + (_render_value(input_dict, KEY_DECK_CONCRETE_GRADE_BASIC)) + r""" \\
\hline
\end{tabular}
\vspace{0.4cm}

\newpage
\section{Additional Inputs}
\label{sec:additional-inputs}

Where the user has modified additional inputs, those values are reported here. Where no modification was made, the software default is shown.

\noindent\textbf{Table 2.4  Typical Section Details}

\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\hline
\textbf{Overall Bridge Width (m)} & """ + (_render_value(input_dict, KEY_TS_OVERALL_WIDTH)) + r""" \\[6pt]
\hline
\textbf{No. of Girders} & """ + (_render_value(input_dict, KEY_TS_NO_OF_GIRDERS)) + r""" \\[6pt]
\hline
\textbf{Girder Spacing (m)} & """ + (_render_value(input_dict, KEY_TS_GIRDER_SPACING, ' m')) + r""" \\[6pt]
\hline
\textbf{Deck Overhang Width (m)} & """ + (_render_value(input_dict, KEY_TS_DECK_OVERHANG, ' m')) + r""" \\[6pt]
\hline
\textbf{Deck Thickness (mm)} & """ + (_render_value(input_dict, KEY_TS_DECK_THICKNESS, ' mm')) + r""" \\[6pt]
\hline
\textbf{Footpath Width (m)} & """ + (_render_value(input_dict, KEY_TS_FOOTPATH_WIDTH, ' m')) + r""" (IRC 5 Cl. 104.3.6 min: 1.5 m) \\[6pt]
\hline
\textbf{No. of Traffic Lanes} & """ + (_render_value(input_dict, KEY_WC_LD_LANE_TABLE_COUNT)) + r""" (per IRC 5 Cl. 104.3.1) \\[6pt]
\hline
\end{longtable}

\vspace{0.8em}
\noindent\textbf{Table 2.5  Components Details}

\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\hline
\textbf{Crash Barrier Type} & """ + (_render_value(input_dict, KEY_CB_TYPE)) + r""" \\[6pt]
\hline
\textbf{Crash Barrier Load (kN/m)} & """ + (_render_value(input_dict, KEY_CB_LOAD)) + r""" \\[6pt]
\hline
\textbf{Median Type} & """ + (_render_value(input_dict, KEY_MD_TYPE)) + r""" \\[6pt]
\hline
\textbf{Railing Type} & """ + (_render_value(input_dict, KEY_RL_TYPE)) + r""" \\[6pt]
\hline
\textbf{Railing Load (kN/m)} & """ + (_render_value(input_dict, KEY_RL_LOAD_VALUE)) + r""" \\[6pt]
\hline
\textbf{Wearing Course Material} & """ + (_render_value(input_dict, KEY_WC_MATERIAL)) + r""" \\[6pt]
\hline
\textbf{Wearing Course Thickness (mm)} & """ + (_render_value(input_dict, KEY_WC_THICKNESS, ' mm')) + r""" \\[6pt]
\hline
\end{longtable}

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

    # Helper: one girder-dimension row
    def _dim_row(g_lbl, i):
        return (g_lbl + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_GIRDER_DEPTH}.G{i}.M1", ' mm'))
                + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_GIRDER_WEB_THICKNESS}.G{i}.M1", ' mm'))
                + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_GIRDER_TOP_FLANGE_WIDTH}.G{i}.M1", ' mm'))
                + ', '
                + (_render_value(input_dict, f"{KEY_MP_GIRDER_TOP_FLANGE_THICKNESS}.G{i}.M1", ' mm'))
                + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH}.G{i}.M1", ' mm'))
                + ', '
                + (_render_value(input_dict, f"{KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS}.G{i}.M1", ' mm'))
                + r""" \\[8pt]
\hline
""")

    # Helper: one general-info row
    def _gen_row(g_lbl, m_id, i):
        return (g_lbl + r""" & """ + m_id + r""" & """
                + (_render_value(input_dict, KEY_DESIGN_MODE))
                + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_GIRDER_TYPE}.G{i}.M1"))
                + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_GIRDER_SYMMETRY}.G{i}.M1"))
                + r""" \\[8pt]
\hline
""")

    # Helper: one restraint/stiffener row
    def _rst_row(g_lbl, i):
        return (g_lbl + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_GIRDER_TORSIONAL_RESTRAINT}.G{i}.M1"))
                + ', '
                + (_render_value(input_dict, f"{KEY_MP_GIRDER_WARPING_RESTRAINT}.G{i}.M1"))
                + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_GIRDER_WEB_TYPE}.G{i}.M1"))
                + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_STIFFENER_INTERMEDIATE}.G{i}.M1"))
                + '; Spacing: '
                + (_render_value(input_dict, f"{KEY_MP_STIFFENER_INTERMEDIATE_SPACING}.G{i}.M1", ' mm'))
                + '; Thickness: '
                + (_render_value(input_dict, f"{KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS}.G{i}.M1", ' mm'))
                + r""" & Longitudinal: """
                + (_render_value(input_dict, f"{KEY_MP_STIFFENER_LONGITUDINAL}.G{i}.M1"))
                + r"""; End Panel: """
                + ''
                + r""" \\[8pt]
\hline
""")

    gen_rows = "".join([_gen_row(g_lbl, m_id, i) for g_lbl, m_id, i in entries_for_table])
    dim_rows = "".join([_dim_row(g_lbl, i) for g_lbl, _, i in entries_for_table])
    rst_rows = "".join([_rst_row(g_lbl, i) for g_lbl, _, i in entries_for_table])

    return (r"""
\newpage
\noindent\textbf{Table 2.6  Member Properties: Girder Details}

\vspace{0.4em}
\noindent

\captionsetup{justification=raggedright,singlelinecheck=false}
\caption*{\textbf{Table 2.6(a)  Girder General Information}}
\vspace{4pt}
\begin{longtable}{|L{2.2cm}|L{1.8cm}|p{3.8cm}|p{3.8cm}|p{3.8cm}|}
\hline
\textbf{Girder} & \textbf{Member ID} & \textbf{Design Mode} & \textbf{Girder Type} & \textbf{Girder Symmetry} \\[6pt]
\hline
"""
            + gen_rows
            + r"""\end{longtable}

\vspace{0.6em}

\captionsetup{justification=raggedright,singlelinecheck=false}
\caption*{\textbf{Table 2.6(b)  Girder Section Dimensions}}
\vspace{4pt}
\begin{longtable}{|L{1.8cm}|L{2.3cm}|L{1.8cm}|p{4.8cm}|p{4.8cm}|}
\hline
\textbf{Girder} & \textbf{Total Depth, D (mm)} & \textbf{Web, tw (mm)} & \textbf{Top Flange (b\textsubscript{tf}, t\textsubscript{tf}) mm} & \textbf{Bottom Flange (b\textsubscript{bf}, t\textsubscript{bf}) mm} \\[6pt]
\hline
"""
            + dim_rows
            + r"""\end{longtable}

\vspace{0.6em}

\captionsetup{justification=raggedright,singlelinecheck=false}
\caption*{\textbf{Table 2.6(c)  Girder Restraint and Stiffener Details}}
\vspace{4pt}
\begin{longtable}{|L{1.8cm}|p{3.4cm}|p{3.4cm}|p{3.4cm}|p{3.4cm}|}
\hline
\textbf{Girder} & \textbf{Torsional / Warping Restraint} & \textbf{Web Philosophy} & \textbf{Intermediate Stiffeners} & \textbf{Longitudinal / End Panel Stiffeners} \\[6pt]
\hline
"""
            + rst_rows
            + r"""\end{longtable}
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

    # Helper: one cross-bracing row (all locations share same bracing config)
    def _cb_row(location, member_ids, i):
        return (location + r""" & """ + member_ids + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_CB_TYPE}.G{i}G{i+1}.B{i}M1"))
                + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_CB_BRACING_SECTION_DESIGNATION}.G{i}G{i+1}.B{i}M1"))
                + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_CB_SPACING}.G{i}G{i+1}.B{i}M1", ' m'))
                + r""" & """
                + ''  # GAP — no KEY_ for number of bracing panels
                + r""" \\[6pt]
\hline
""")

    # Helper: one end-diaphragm row (all locations share same config)
    def _ed_row(location, member_ids, i):
        return (location + r""" & """ + member_ids + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_ED_TYPE}.G{i}G{i+1}.E{i}M1"))
                + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_ED_BRACING_SECTION_DESIGNATION}.G{i}G{i+1}.E{i}M1"))
                + r""" & """
                + ''
                + r""" & """
                + ''  # GAP — no KEY_ for number of bracing panels
                + r""" \\[6pt]
\hline
""")

    cb_rows = "".join([_cb_row(cb_loc, cb_ids, i) for cb_loc, cb_ids, _, _, i in panels])
    ed_rows = "".join([_ed_row(ed_loc, ed_ids, i) for _, _, ed_loc, ed_ids, i in panels])

    return (r"""
\newpage
\noindent\textbf{Table 2.7  Member Properties: Cross Bracing Details}

\vspace{0.4em}
\noindent
\setlength{\tabcolsep}{4pt}
\begin{longtable}{|L{2.2cm}|L{2.2cm}|L{3.0cm}|L{2.5cm}|C{1.8cm}|C{1.8cm}|}
\hline
\textbf{Location} & \textbf{Member IDs} & \textbf{Type of Bracing} & \textbf{Bracing Section} & \textbf{Spacing (m)} & \textbf{No. of Panels} \\
\hline
"""
            + cb_rows
            + r"""\end{longtable}

\noindent\textbf{Table 2.8  Member Properties: End Diaphragm Details}

\vspace{0.4em}
\noindent
\setlength{\tabcolsep}{4pt}
\begin{longtable}{|L{2.2cm}|L{2.2cm}|L{3.0cm}|L{2.5cm}|C{1.8cm}|C{1.8cm}|}
\hline
\textbf{Location} & \textbf{Member IDs} & \textbf{Type of Bracing} & \textbf{Bracing Section} & \textbf{Spacing (m)} & \textbf{No. of Panels} \\
\hline
"""
            + ed_rows
            + r"""\end{longtable}
""")



def _shear_connector_table(input_dict, output_dict=None):
    # Stud computed properties live in output_dict (populated by store_design_results)
    od = output_dict or {}
    return r"""
\label{subsec:shear-connectors}

\vspace{2.2em}
\noindent\textbf{Table 2.9  Shear Connector Details}

\vspace{0.4em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\hline
\textbf{Stud Diameter (mm)} & """ + (_render_value(od, KEY_SD_SHEAR_DIAMETER, ' mm')) + r""" \\[6pt]
\hline
\textbf{Stud Height (mm)} & """ + (_render_value(od, KEY_SD_SHEAR_HEIGHT, ' mm')) + r""" \\[6pt]
\hline
\textbf{Stud fy (MPa)} & """ + (_render_value(od, KEY_SD_SHEAR_YIELD_STRENGTH, ' MPa')) + r""" \\[6pt]
\hline
\textbf{Stud fu (MPa)} & """ + (_render_value(od, KEY_SD_SHEAR_ULTIMATE_STRENGTH, ' MPa')) + r""" \\[6pt]
\hline
\textbf{No. of Studs per Section} & """ + (_render_value(od, KEY_SD_SHEAR_STUDS_PER_SECTION)) + r""" \\[6pt]
\hline
\end{longtable}
"""


def _safety_factors_table(input_dict):
    return r"""
\label{subsec:safety-factors}

\vspace{2.2em}
\noindent\textbf{Table 2.10  Partial Safety Factors}

\vspace{0.3em}
\noindent\textit{Note: All values are per IRC 22 Table 1 unless user-modified.}

\vspace{0.4em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\hline
\textbf{$\gamma_{M0}$ (Yielding / Buckling)} & """ + (_render_value(input_dict, KEY_DO_GAMMA_M0)) + r""" \\[6pt]
\hline
\textbf{$\gamma_{M1}$ (Ultimate Stress)} & """ + (_render_value(input_dict, KEY_DO_GAMMA_M1)) + r""" \\[6pt]
\hline
\textbf{$\gamma_C$ (Concrete, Basic)} & """ + (_render_value(input_dict, KEY_DO_GAMMA_C_BASIC)) + r""" \\[6pt]
\hline
\textbf{$\gamma_s$ (Reinforcement)} & """ + (_render_value(input_dict, KEY_DO_GAMMA_S)) + r""" \\[6pt]
\hline
\textbf{$\gamma_v$ (Shear Connectors)} & """ + (_render_value(input_dict, KEY_DO_GAMMA_V)) + r""" \\[6pt]
\hline
\textbf{$\gamma_{fft}$ (Fatigue Load)} & """ + (_render_value(input_dict, KEY_DO_GAMMA_FLT)) + r""" \\[6pt]
\hline
\textbf{$\gamma_{Mft}$ (Fatigue Strength)} & """ + (_render_value(input_dict, KEY_DO_GAMMA_MF)) + r""" \\[6pt]
\hline
\end{longtable}
"""


# Chapters 3-5: Loads, Analysis, Design Checks — exact LaTeX template


def ch3_loads(input_dict):
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

    lanes = input_dict.get(KEY_WC_LD_LANE_TABLE_COUNT)
    braking_force_str = ""
    if lanes not in (None, ""):
        try:
            lanes_int = int(lanes)
            braking_force_t = IRC6_2017.cl_211_2_braking_force(lanes_int)
            braking_force_kN = braking_force_t * 9.81
            braking_force_str = f"{braking_force_kN:.2f} kN ({braking_force_t:.2f} tonnes)"
        except Exception:
            braking_force_str = "N/A"
    else:
        braking_force_str = "N/A"

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
        return ', '.join(parts)

    uls_combos = IRC6_2017.uls_load_combinations()
    sls_combos = IRC6_2017.sls_load_combinations()
    lc_rows = []
    for i, combo in enumerate(uls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        lc_rows.append(
            f"ULS-{i:02d}" + r" & " + cases + r" \\[6pt]" + "\n"
            + r"\hline"
        )
    for i, combo in enumerate(sls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        lc_rows.append(
            f"SLS-{i:02d}" + r" & " + cases + r" \\[6pt]" + "\n"
            + r"\hline"
        )

    lc_rows_str = "\n".join(lc_rows)

    return r"""
\chapter{Loads and Load Combinations}

This section summarizes all loads applied to the bridge and the load combinations considered for analysis and design.

\vspace{1em}
\noindent\textbf{Table 3.1  Dead Load -- Self Weight}

\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\hline
\textbf{Steel Self-Weight Applied} & """ + (_render_value(input_dict, KEY_MATERIAL_GIRDER_DENSITY, ' kN/m\\textsuperscript{3}')) + r""" \\[6pt]
\hline
\textbf{Concrete Deck Weight} & """ + (_render_value(input_dict, KEY_MATERIAL_DECK_DENSITY, ' kN/m\\textsuperscript{3}')) + r""" \\[6pt]
\hline
\textbf{Self-Weight Factor} & """ + (_render_value(input_dict, KEY_PL_SELF_WEIGHT_FACTOR)) + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\noindent\textbf{Table 3.2  Dead Load for Surfacing (DW)}

\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\hline
\textbf{Wearing Course Load} & """ + (_render_value(input_dict, KEY_WC_MATERIAL)) + r""" x """ + (_render_value(input_dict, KEY_WC_THICKNESS)) + r""" \\[6pt]
\hline
\textbf{Additional SIDL (Crash Barrier)} & """ + (_render_value(input_dict, KEY_CB_LOAD)) + r""" kN/m per barrier \\[6pt]
\hline
\textbf{Railing Load} & """ + (_render_value(input_dict, KEY_RL_LOAD_VALUE)) + r""" kN/m\sdstar{} \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\noindent\textbf{Table 3.3  Live Loads (LL)}

\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\hline
\textbf{Vehicles Considered} & """ + _tex(vehicles_str) + r""" \\[6pt]
\hline
\textbf{Impact Factor (IRC 6)} & """ + _tex(impact_factor_str) + r""" \\[6pt]
\hline
\textbf{Braking Load (IRC 6)} & """ + _tex(braking_force_str) + r""" \\[6pt]
\hline
\textbf{Footpath Live Load (if applicable)} & """ + (_render_value(input_dict, KEY_LL_FOOTPATH_PRESSURE_VALUE, ' kN/m\\textsuperscript{2}')) + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\noindent\textbf{Table 3.4  Wind Load (WL) --- per IRC 6}

\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\hline
\textbf{Basic Wind Speed, Vb} & """ + (_render_value(input_dict,'wind_speed', ' m/s')) + r""" [from Project Location] \\[6pt]
\hline
\textbf{Terrain Type} & """ + (_render_value(input_dict, KEY_WL_TERRAIN_TYPE)) + r""" \\[6pt]
\hline
\textbf{Average Exposed Height, H (m)} & """ + (_render_value(input_dict, KEY_WL_AVG_EXPOSED_HEIGHT, ' m')) + r""" \\[6pt]
\hline
\textbf{Hourly Mean Wind Speed, Vz} & """ + (_render_value(input_dict, KEY_WL_HOURLY_MEAN_WIND, ' m/s')) + r""" \\[6pt]
\hline
\textbf{Hourly Wind Pressure, Pz} & """ + (_render_value(input_dict, KEY_WL_HOURLY_WIND_PRESSURE, ' N/m\\textsuperscript{2}')) + r""" \\[6pt]
\hline
\textbf{Transverse Wind Force} & """ + (_render_value(input_dict, KEY_WL_TRANSVERSE_WIND_FORCE, ' kN')) + r""" \\[6pt]
\hline
\textbf{Longitudinal Wind Force} & """ + (_render_value(input_dict, KEY_WL_LONGITUDINAL_WIND_FORCE, ' kN')) + r""" \\[6pt]
\hline
\textbf{Vertical Wind Force} & """ + (_render_value(input_dict, KEY_WL_VERTICAL_WIND_FORCE, ' kN')) + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\noindent\textbf{Table 3.5  Earthquake Load (EL) --- per IRC 6}

\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\hline
\textbf{Seismic Zone} & """ + (_render_value(input_dict,'seismic_zone')) + r""" [from Project Location] \\[6pt]
\hline
\textbf{Zone Factor, Z} & """ + (_render_value(input_dict, KEY_SL_ZONE_FACTOR)) + r""" \\[6pt]
\hline
\textbf{Importance Factor, I} & """ + (_render_value(input_dict, KEY_SL_IMPORTANCE_FACTOR)) + r""" \\[6pt]
\hline
\textbf{Type of Soil} & """ + (_render_value(input_dict, KEY_SL_SOIL_TYPE)) + r""" \\[6pt]
\hline
\textbf{Sa/g} & """ + (_render_value(input_dict, KEY_SL_SPECTRAL_COEFF)) + r""" \\[6pt]
\hline
\textbf{Horizontal Seismic Coefficient, Ah} & """ + (_render_value(input_dict, KEY_SL_HORIZONTAL_COEFF)) + r""" \\[6pt]
\hline
\textbf{Vertical Seismic Coefficient, Av} & """ + (_render_value(input_dict, KEY_SL_VERTICAL_COEFF)) + r""" \\[6pt]
\hline
\textbf{Horizontal Seismic Force (longitudinal)} & """ + '' + r""" kN \\[6pt]
\hline
\textbf{Horizontal Seismic Force (transverse)} & """ + '' + r""" kN \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\noindent\textbf{Table 3.6  Temperature Load (EL) --- per IRC 6}

\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\hline
\textbf{Maximum Shade Temperature} & """ + (_render_value(input_dict,'shade_temp_max')) + r""" $^\circ$C \\[6pt]
\hline
\textbf{Minimum Shade Temperature} & """ + (_render_value(input_dict,'shade_temp_min')) + r""" $^\circ$C \\[6pt]
\hline
\textbf{Effective Bridge Temp. Range} & """ + (_render_value(input_dict, KEY_TL_BRIDGE_TEMP_MIN)) + r""" to """ + (_render_value(input_dict, KEY_TL_BRIDGE_TEMP_MAX)) + r""" $^\circ$C \\[6pt]
\hline
\textbf{Temperature Rise / Fall for Design} & +""" + (_render_value(input_dict, KEY_TL_TEMP_RISE)) + r""" $^\circ$C / \textminus{}""" + (_render_value(input_dict, KEY_TL_TEMP_FALL)) + r""" $^\circ$C \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\noindent\textbf{Table 3.7  Load Combinations}

\vspace{0.4em}
The following load combinations were evaluated per IRC 6. The governing combination for each member is identified in the design checks section.

\begin{longtable}{|C{4.0cm}|p{11.5cm}|}
\hline
\textbf{Combination ID} & \textbf{Load Cases} \\[6pt]
\hline
""" + lc_rows_str + r"""
\end{longtable}

\noindent\textit{Note: All IRC 6 load combinations are auto-generated by OsdagBridge. User-defined custom combinations, if any, are appended.}
"""


def ch4_analysis(asum, fig_paths, bridge: "ReportDataBridge", span_m: float):
    lc_summary  = (asum or {}).get('load_cases', {})
    rxn_summary = (asum or {}).get('reactions',  {})

    def _is_moving(lc_name: str) -> bool:
        n = str(lc_name).lower()
        return "moving" in n or " pos_" in n

    lc_summary  = {k: v for k, v in lc_summary.items()  if not _is_moving(k)}
    rxn_summary = {k: v for k, v in rxn_summary.items() if not _is_moving(k)}

    def _fmt(val, nd=3):
        try:
            return f"{float(val):.{nd}f}"
        except (TypeError, ValueError):
            return r"---"

    def _merged_row(lc, bm_d, rxn_d):
        bm_d  = bm_d  or {}
        rxn_d = rxn_d or {}
        return (
            _tex(lc)                              + r" & "
            + _fmt(bm_d.get('max_bm'))           + r" & "
            + _tex(bm_d.get('bm_girder', '---')) + r" & "
            + _fmt(bm_d.get('bm_location'))      + r" & "
            + _fmt(bm_d.get('max_sf'))           + r" & "
            + _tex(bm_d.get('sf_girder', '---')) + r" & "
            + _fmt(bm_d.get('sf_location'))      + r" & "
            + _fmt(rxn_d.get('left_kN'))         + r" & "
            + _fmt(rxn_d.get('right_kN'))        + r" \\[6pt]"
        )

    all_lcs = list(lc_summary.keys()) + [k for k in rxn_summary if k not in lc_summary]

    merged_body = ("\n\\hline\n").join(
        _merged_row(lc, lc_summary.get(lc), rxn_summary.get(lc))
        for lc in all_lcs
    ) if all_lcs else r"--- & --- & --- & --- & --- & --- & --- & --- & --- \\[6pt]"

    _span_m         = float(bridge.input_dict.get(KEY_SPAN, 0) or 0)
    _allow_live_mm  = _span_m * 1000.0 / 800.0
    _allow_total_mm = _span_m * 1000.0 / 600.0

    # Find governing girder — worst (max) deflection across all girders
    try:
        n = int(bridge.input_dict.get(KEY_TS_NO_OF_GIRDERS, 1) or 1)
    except (TypeError, ValueError):
        n = 1

    _live_mm  = None
    _total_mm = None
    for _gi in range(1, n + 1):
        _l = bridge.output_dict.get(f"{KEY_SD_DEFL_LIVE}.G{_gi}")
        _t = bridge.output_dict.get(f"{KEY_SD_DEFL_TOTAL}.G{_gi}")
        if _l is not None:
            _live_mm  = max(_live_mm, float(_l))  if _live_mm  is not None else float(_l)
        if _t is not None:
            _total_mm = max(_total_mm, float(_t)) if _total_mm is not None else float(_t)

    _live_str        = f"{_live_mm:.3f} mm"  if _live_mm  is not None else "---"
    _total_str       = f"{_total_mm:.3f} mm" if _total_mm is not None else "---"
    _allow_live_str  = f"L/800 = {_allow_live_mm:.1f} mm"
    _allow_total_str = f"L/600 = {_allow_total_mm:.1f} mm"
    _live_status     = ("PASS" if _live_mm  <= _allow_live_mm  else r"\textcolor{red}{FAIL}") if _live_mm  is not None else "---"
    _total_status    = ("PASS" if _total_mm <= _allow_total_mm else r"\textcolor{red}{FAIL}") if _total_mm is not None else "---"
    return r"""
\chapter{Analysis Results}

A grillage model was used for structural analysis. The deck is idealized as a grid of elastic beam elements --- longitudinal members represent the composite steel girders with effective slab, and transverse members represent the slab or cross frames. This section summarizes the critical output from that analysis.

\vspace{1em}
\noindent\textbf{Table 4.1  Summary of Maximum Demands and Reactions}

\begingroup
\setlength\LTleft{-1.6cm}
\setlength\LTright{-1.4cm}
\setlength{\tabcolsep}{4pt}
\renewcommand{\arraystretch}{1.3}
\begin{longtable}{|C{3.1cm}|C{2cm}|C{1.3cm}|C{1.7cm}|C{2cm}|C{1.3cm}|C{1.7cm}|C{1.7cm}|C{1.7cm}|}
\hline
\multirow{2}{*}{\makecell{\textbf{Load} \\ \textbf{Case/Combin-} \\ \textbf{ation}}} & \multicolumn{3}{c|}{\textbf{Bending Moment}} & \multicolumn{3}{c|}{\textbf{Shear Force}} & \multicolumn{2}{c|}{\textbf{Reaction (kN)}} \\
\cline{2-9}
 & \textbf{Maximum Value (kNm)} & \textbf{Girder} & \textbf{Location (m)} & \textbf{Maximum Value (kN)} & \textbf{Girder} & \textbf{Location (m)} & \textbf{Left Support} & \textbf{Right Support} \\[6pt]
\hline
""" + merged_body + r"""
\hline
\end{longtable}
\endgroup

\vspace{1em}
\noindent\textbf{Table 4.2  Deflection Summary}

\begin{longtable}{|L{7cm}|p{8.5cm}|}
\hline
\textbf{Deflection due to Live Load, delta\_LL} & """ + _live_str + r""" \\[6pt]
\hline
\textbf{Allowable Live Load Deflection} & """ + _allow_live_str + r""" \\[6pt]
\hline
\textbf{Live Load Deflection Check Status} & """ + _live_status + r""" \\[6pt]
\hline
\textbf{Deflection due to Total Load, delta\_total} & """ + _total_str + r""" \\[6pt]
\hline
\textbf{Allowable Total Deflection} & """ + _allow_total_str + r""" \\[6pt]
\hline
\textbf{Total Load Deflection Check Status} & """ + _total_status + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\noindent
""" + _fig_embed(fig_paths.get('bm_envelope'), 'Bending Moment Envelope (Envelope ULS): Max/min BM along span. X-axis: distance from left support (m). Y-axis: Bending Moment (kN-m).', width=r'0.75\textwidth') + r"""
""" + _fig_embed(fig_paths.get('sf_envelope'), 'Shear Force Envelope (Envelope ULS): Max/min SF along span. X-axis: distance from left support (m). Y-axis: Shear Force (kN).', width=r'0.75\textwidth') + r"""
""" + _fig_embed(fig_paths.get('defl_ll'), 'Vertical Deflection D$_y$ (1.0 LL): Maximum deflection along span. Load Case: 1.0 LL, Combination: $D_y$. Nodes shown. Isometric view.', width=r'0.75\textwidth') + r"""
"""


# Chapter 5: Design Checks — exact LaTeX template match

def ch5_design_checks(checks_data, bridge: "ReportDataBridge"):
    girder_entries = get_girder_entries(bridge.input_dict)
    if not girder_entries:
        n = int(bridge.input_dict.get(KEY_TS_NO_OF_GIRDERS, 1))
        girder_entries = [(f"Girder {i}", f"M1") for i in range(1, n + 1)]
    n_girders = len(girder_entries)

    # Deck slab design report values (Tables 5.17(a)-(g)), keyed to
    # common.KEY_DD_*. Populated by deckdesign.design_deck_slab(); empty
    # dict when deck design has not been run. Look up with deck_rpt.get(KEY_...).
    deck_rpt = bridge.output_dict.get("deck_report_values", {}) or {}

    # Generate Table 5.1 rows (per-girder section properties)
    t51_rows = []
    for lbl, _ in girder_entries:
        t51_rows.append(
            r"\multirow{13}{*}{\makecell{" + lbl + r"""}} & \textbf{Depth, D (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_TOTAL_DEPTH) + r""" \\[6pt]
\cline{2-3}
 & \textbf{Top Flange Width, $b_f$ (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_TOP_FLANGE_WIDTH) + r""" \\[6pt]
\cline{2-3}
 & \textbf{Bottom Flange Width, $b_f$ (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_BOTTOM_FLANGE_WIDTH) + r""" \\[6pt]
\cline{2-3}
 & \textbf{Top Flange Thickness, $t_f$ (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_TOP_FLANGE_THICKNESS) + r""" \\[6pt]
\cline{2-3}
 & \textbf{Bottom Flange Thickness, $t_f$ (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_BOTTOM_FLANGE_THICKNESS) + r""" \\[6pt]
\cline{2-3}
 & \textbf{Web Thickness, $t_w$ (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_WEB_THICKNESS) + r""" \\[6pt]
\cline{2-3}
 & \textbf{Gross Area, A (cm$^2$)} & """ + _render_value(bridge.output_dict, KEY_SD_SECTION_PROP_AREA) + r""" \\[6pt]
\cline{2-3}
 & \textbf{Moment of Inertia, $I_z$ (cm$^4$)} & """ + _render_value(bridge.output_dict, KEY_SD_SECTION_PROP_IZ) + r""" \\[6pt]
\cline{2-3}
 & \textbf{Elastic Section Modulus, $Z_{ez}$ (cm$^3$)} & """ + _render_value(bridge.output_dict, KEY_SD_SECTION_PROP_ZZ) + r""" \\[6pt]
\cline{2-3}
 & \textbf{Plastic Section Modulus, $Z_{pz}$ (cm$^3$)} & """ + _render_value(bridge.output_dict, KEY_SD_SECTION_PROP_ZUZ) + r""" \\[6pt]
\cline{2-3}
 & \textbf{Effective Slab Width, $b_{eff}$ (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_EFFECTIVE_SLAB_WIDTH) + r""" \\[6pt]
\cline{2-3}
 & \textbf{Transformed Composite $I_z$ (cm$^4$)} & """ + _render_value(bridge.output_dict, KEY_SD_COMPOSITE_IZ) + r""" \\[6pt]
\cline{2-3}
 & \textbf{Depth to Plastic Neutral Axis (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_PNA_DEPTH) + r""" \\[6pt]
\hline"""
        )
    t51_content = "\n".join(t51_rows)

    # Generate Table 5.2 rows
    t52_rows = []
    for lbl, _ in girder_entries:
        t52_rows.append(
            r"\multirow{3}{*}{\makecell{" + lbl + r"""}} & Top Flange & """ + _render_value(bridge.output_dict, KEY_SD_FLANGE_SLENDERNESS) + r""" & """ + _render_value(bridge.output_dict, KEY_SD_FLANGE_CLASS_LIMIT) + r""" & """ + _render_value(bridge.output_dict, KEY_SD_CLASS_FLANGE) + r""" \\[6pt]
\cline{2-5}
 & Web & """ + _render_value(bridge.output_dict, KEY_SD_WEB_SLENDERNESS) + r""" & """ + _render_value(bridge.output_dict, KEY_SD_WEB_CLASS_LIMIT) + r""" & """ + _render_value(bridge.output_dict, KEY_SD_CLASS_WEB) + r""" \\[6pt]
\cline{2-5}
 & Overall Section & --- & --- & """ + _render_value(bridge.output_dict, KEY_SD_SECTION_CLASS) + r""" \\[6pt]
\hline"""
        )
    t52_content = "\n".join(t52_rows)

    # Generate Table 5.3 rows
    # Flexure UR is stored as a percent (cat_urs × 100); show as a ratio (÷100,
    # 2 dp) and PASS when ≤ 1.0.
    try:
        _flex_ur = float(bridge.output_dict.get(KEY_UTIL_FLEXURE)) / 100.0
        _flex_ur_str = f"{_flex_ur:.2f}"
        _flex_status = "PASS" if _flex_ur <= 1.0 else r"\textcolor{red}{FAIL}"
    except (TypeError, ValueError):
        _flex_ur_str = ""
        _flex_status = "---"
    t53_rows = []
    for lbl, _ in girder_entries:
        t53_rows.append(
            r"\multirow{3}{*}{\makecell{" + lbl + r"""}} & Applied Moment, $M_u$ & Governing LC (ULS) & """ + _render_value(bridge.output_dict, KEY_SD_MU_APPLIED, " kN-m") + r""" & --- \\[6pt]
\cline{2-5}
 & Design Moment Capacity, Md & IRC 22 Cl. 603.3.1 & """ + _render_value(bridge.output_dict, KEY_SD_MD_CAPACITY, " kN-m") + r""" & --- \\[6pt]
\cline{2-5}
 & Utilization Ratio, $M_u / M_d$ & $M_u / M_d$ & """ + _flex_ur_str + r""" & """ + _flex_status + r""" \\[6pt]
\hline"""
        )
    t53_content = "\n".join(t53_rows)

    # Generate Table 5.4 rows
    # Shear UR is stored as a percent (cat_urs × 100); show as a ratio (÷100,
    # 2 dp) and PASS when ≤ 1.0.
    try:
        _shear_ur = float(bridge.output_dict.get(KEY_UTIL_SHEAR)) / 100.0
        _shear_ur_str = f"{_shear_ur:.2f}"
        _shear_status = "PASS" if _shear_ur <= 1.0 else r"\textcolor{red}{FAIL}"
    except (TypeError, ValueError):
        _shear_ur_str = ""
        _shear_status = "---"
    t54_rows = []
    for lbl, _ in girder_entries:
        t54_rows.append(
            r"\multirow{8}{*}{\makecell{" + lbl + r"""}} & Applied Shear, $V_u$ & Governing LC (ULS) & """ + _render_value(bridge.output_dict, KEY_SD_SHEAR_VU, " kN") + r""" & --- \\[6pt]
\cline{2-5}
 & Shear Area, Av & $d_w \times t_w$ & """ + _render_value(bridge.output_dict, KEY_SD_SHEAR_AV, " mm$^2$") + r""" & --- \\[6pt]
\cline{2-5}
 & Panel Aspect Ratio, c/d & --- & """ + _render_value(bridge.output_dict, KEY_SD_PANEL_CD) + r""" & --- \\[6pt]
\cline{2-5}
 & Shear Buckling Coefficient, kv & IS 800 Cl. 8.4.2.2 & """ + _render_value(bridge.output_dict, KEY_SD_SHEAR_KV) + r""" & --- \\[6pt]
\cline{2-5}
 & Web Slenderness, $\lambda_w$ & $\sqrt{f_{yw}/(\sqrt{3}\,\tau_{cr})}$ & """ + _render_value(bridge.output_dict, KEY_SD_SHEAR_LAMBDA_W) + r""" & --- \\[6pt]
\cline{2-5}
 & Design Shear Stress, tau\_b & IRC 22 Cl. 603.3.3.2 & """ + _render_value(bridge.output_dict, KEY_SD_SHEAR_TAU_B, " MPa") + r""" & --- \\[6pt]
\cline{2-5}
 & Shear Buckling Resistance, Vcr & $A_v \times \tau_b$ & """ + _render_value(bridge.output_dict, KEY_SD_SHEAR_VCR, " kN") + r""" & --- \\[6pt]
\cline{2-5}
 & Utilization Ratio, $V_u / V_d$ & $V_u / V_d$ & """ + _shear_ur_str + r""" & """ + _shear_status + r""" \\[6pt]
\hline"""
        )
    t54_content = "\n".join(t54_rows)

    # Generate Table 5.5 rows
    # Interaction DCRs use the engine bands: PASS <0.90, WARN <1.00, FAIL ≥1.00.
    def _interaction_status(ratio):
        if ratio < 0.90:
            return "PASS"
        elif ratio < 1.00:
            return "WARN"
        return r"\textcolor{red}{FAIL}"
    # M-V interaction UR stored as percent → show ratio (2 dp).
    try:
        _mv_ur = float(bridge.output_dict.get(KEY_UTIL_INTERACTION)) / 100.0
        _mv_ur_str = f"{_mv_ur:.2f}"
        _mv_status = _interaction_status(_mv_ur)
    except (TypeError, ValueError):
        _mv_ur_str = ""
        _mv_status = "---"
    # M-N interaction: None → no axial load → N/A.
    _mn_r  = bridge.output_dict.get(KEY_SD_MN_RATIO)
    _mn_ax = bridge.output_dict.get(KEY_SD_MN_AXIAL)
    _mn_mo = bridge.output_dict.get(KEY_SD_MN_MOMENT)
    if _mn_r is None or _mn_ax is None or _mn_mo is None:
        _mn_cond = _mn_val = _mn_status = "N/A"
    else:
        _mn_cond   = f"{_mn_ax:.2f} + {_mn_mo:.2f} = {_mn_r:.3f}"
        _mn_val    = f"{_mn_r:.3f}"
        _mn_status = _interaction_status(_mn_r)
    t55_rows = []
    for lbl, _ in girder_entries:
        t55_rows.append(
            r"\multirow{4}{*}{\makecell{" + lbl + r"""}} & High Shear Condition? & $V_u > 0.6\,V_d$ & """ + _render_value(bridge.output_dict, KEY_SD_HIGH_SHEAR) + r""" & --- \\[6pt]
\cline{2-5}
 & Reduced Moment Capacity, $M_{dv}$ & IRC 22 Cl. 603.3.3.3 & """ + _render_value(bridge.output_dict, KEY_SD_MDV, " kN-m") + r""" & --- \\[6pt]
\cline{2-5}
 & Interaction Check: $M_u \leq M_{dv}$ & --- & """ + _mv_ur_str + r""" & """ + _mv_status + r""" \\[6pt]
\cline{2-5}
 & Interaction Check: $N_u/N_{Rd} + M_u/M_{dv} \leq 1.0$ & """ + _mn_cond + r""" & """ + _mn_val + r""" & """ + _mn_status + r""" \\[6pt]
\hline"""
        )
    t55_content = "\n".join(t55_rows)

    # Generate Table 5.6 rows
    # LTB UR stored as percent → show ratio (2 dp); engine bands via _interaction_status.
    try:
        _ltb_ur = float(bridge.output_dict.get(KEY_UTIL_LTB)) / 100.0
        _ltb_ur_str = f"{_ltb_ur:.2f}"
        _ltb_status = _interaction_status(_ltb_ur)
    except (TypeError, ValueError):
        _ltb_ur_str = ""
        _ltb_status = "---"
    t56_rows = []
    for lbl, _ in girder_entries:
        t56_rows.append(
            r"\multirow{5}{*}{\makecell{" + lbl + r"""}} & Elastic Critical Moment, Mcr & IRC 22 Cl. 603.3.3.1 & """ + _render_value(bridge.output_dict, KEY_SD_LTB_MCR, " kN-m") + r""" & --- \\[6pt]
\cline{2-5}
 & Non-dim. Slenderness, $\bar{\lambda}_{LT}$ & $\sqrt{M_p / M_{cr}}$ & """ + _render_value(bridge.output_dict, KEY_SD_LTB_LAMBDA) + r""" & --- \\[6pt]
\cline{2-5}
 & LTB Reduction Factor, chi\_LT & IS 800 Cl. 8.2.2 & """ + _render_value(bridge.output_dict, KEY_SD_LTB_CHI) + r""" & --- \\[6pt]
\cline{2-5}
 & LTB Resistance, Mb & $\chi_{LT}\,M_p / \gamma_{m0}$ & """ + _render_value(bridge.output_dict, KEY_SD_LTB_MB, " kN-m") + r""" & --- \\[6pt]
\cline{2-5}
 & $M_u \leq M_b$ & $M_u / M_b$ & """ + _ltb_ur_str + r""" & """ + _ltb_status + r""" \\[6pt]
\hline"""
        )
    t56_content = "\n".join(t56_rows)

    # Generate Table 5.7 rows
    t57_rows = []
    for lbl, _ in girder_entries:
        t57_rows.append(
            r"\multirow{6}{*}{\makecell{" + lbl + r"""}} & \textbf{Shear Buckling Design Method} & """ + _render_value(bridge.output_dict, KEY_SD_STIFF_METHOD) + r""" \\[6pt]
\cline{2-3}
 & \textbf{Intermediate Stiffener Thickness (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_STIFF_INT_THICK) + r""" \\[6pt]
\cline{2-3}
 & \textbf{Intermediate Stiffener Spacing (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_STIFF_INT_SPACING) + r""" \\[6pt]
\cline{2-3}
 & \textbf{End Panel Stiffener Thickness (mm)} & """ + _render_value(bridge.output_dict, KEY_SD_STIFF_END_THICK) + r""" \\[6pt]
\cline{2-3}
 & \textbf{No. of End Panel Stiffeners} & """ + _render_value(bridge.output_dict, KEY_SD_STIFF_END_COUNT) + r""" \\[6pt]
\cline{2-3}
 & \textbf{Longitudinal Stiffeners} & """ + _render_value(bridge.output_dict, KEY_SD_STIFF_LONG) + r""" \\[6pt]
\hline"""
        )
    t57_content = "\n".join(t57_rows)

    # Generate Table 5.8 rows
    # Status: PASS when Provided ≥ Required.
    def _ge_status(provided, required):
        try:
            return "PASS" if float(provided) >= float(required) else r"\textcolor{red}{FAIL}"
        except (TypeError, ValueError):
            return "---"
    _iys_status = _ge_status(bridge.output_dict.get(KEY_SD_IS_IYS_PROV),
                             bridge.output_dict.get(KEY_SD_IS_IYS_MIN))
    _fqd_status = _ge_status(bridge.output_dict.get(KEY_SD_IS_FQD),
                             bridge.output_dict.get(KEY_SD_IS_FQ))
    t58_rows = []
    for lbl, _ in girder_entries:
        t58_rows.append(
            r"\multirow{2}{*}{\makecell{" + lbl + r"""}} & Min. Moment of Inertia, $I_s$ & """ + _render_value(bridge.output_dict, KEY_SD_IS_IYS_MIN, " mm$^4$") + r""" & """ + _render_value(bridge.output_dict, KEY_SD_IS_IYS_PROV, " mm$^4$") + r""" & """ + _iys_status + r""" \\[6pt]
\cline{2-5}
 & Buckling Resistance, $F_{qd} \geq F_q$ & """ + _render_value(bridge.output_dict, KEY_SD_IS_FQ, " kN") + r""" & """ + _render_value(bridge.output_dict, KEY_SD_IS_FQD, " kN") + r""" & """ + _fqd_status + r""" \\[6pt]
\hline"""
        )
    t58_content = "\n".join(t58_rows)

    # Table 5.8 (Intermediate Stiffener Checks) is a verification table — it only
    # has data when the user supplied stiffener sizes (Design Type = Custom). In
    # Optimized mode the stiffeners are auto-sized (nothing to verify), so the
    # whole table is omitted from the report.
    _is_custom = str(bridge.input_dict.get(KEY_DESIGN_MODE, "Optimized")).strip().lower() in {"custom", "customized"}
    if _is_custom:
        t58_block = r"""
\vspace{1em}
\noindent\textbf{Table 5.8  Intermediate Stiffener Checks}

\begin{longtable}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.2cm}|C{1.8cm}|}
\hline
\textbf{} & \textbf{Check} & \textbf{Required} & \textbf{Provided} & \textbf{Status} \\[6pt]
\hline
""" + t58_content + r"""
\end{longtable}
\noindent\textit{Note: IS 800 Cl. 8.7.1.2}
"""
    else:
        t58_block = ""

    # Generate Table 5.9 rows — bearing stiffener checks (IS 800 Cl.8.7.3).
    # End panel == bearing stiffener for this bridge. Each resistance vs reaction R.
    # Resistances are 0 in guidance-only mode (optimized w/o outstand) → N/A until
    # the designer defaults outstand to (bf−tw)/2.
    _bs_r = bridge.output_dict.get(KEY_SD_BS_R)
    def _bs_check(resist_key):
        prov = bridge.output_dict.get(resist_key)
        # Resistance not computed (guidance mode) → N/A.
        if prov is None or float(prov) <= 0.0 or _bs_r is None:
            return ("N/A", "N/A", "N/A")
        req_s  = f"{_bs_r} kN"
        prov_s = f"{prov} kN"
        status = "PASS" if float(prov) >= float(_bs_r) else r"\textcolor{red}{FAIL}"
        return (req_s, prov_s, status)
    _wb_req, _wb_prov, _wb_st = _bs_check(KEY_SD_BS_FCDW_WB)
    _lc_req, _lc_prov, _lc_st = _bs_check(KEY_SD_BS_FCDW_LC)
    _ps_req, _ps_prov, _ps_st = _bs_check(KEY_SD_BS_FPSD)
    _cb_req, _cb_prov, _cb_st = _bs_check(KEY_SD_BS_FCD)
    t59_rows = []
    for lbl, _ in girder_entries:
        t59_rows.append(
            r"\multirow{4}{*}{\makecell{" + lbl + r"""}} & Web Buckling Resistance & """ + _wb_req + r""" & """ + _wb_prov + r""" & """ + _wb_st + r""" \\[6pt]
\cline{2-5}
 & Local Crushing Resistance & """ + _lc_req + r""" & """ + _lc_prov + r""" & """ + _lc_st + r""" \\[6pt]
\cline{2-5}
 & Bearing Capacity & """ + _ps_req + r""" & """ + _ps_prov + r""" & """ + _ps_st + r""" \\[6pt]
\cline{2-5}
 & Column Buckling Resistance & """ + _cb_req + r""" & """ + _cb_prov + r""" & """ + _cb_st + r""" \\[6pt]
\hline"""
        )
    t59_content = "\n".join(t59_rows)

    # ── Table 5.10: Serviceability — Deflection Checks (IRC 22 Cl. 604.3.2) ──────
    # Allowable limits: span-dependent, same for all girders, from output_dict.
    # Actual deflections: per-girder from bridge._deflections_cache — the same
    # source used by resolve_deflection_live_load/total in generate_results_values_builder.py.
    # Keys: {"G1": {"live_mm": X, "total_mm": Y}, ...}
    # lbl from girder_entries is "G1", "G2", ... which matches cache keys exactly.

    def _defl_status(actual, allowable):
        """PASS / red FAIL for deflection; '---' when values are missing."""
        try:
            return "PASS" if float(actual) <= float(allowable) else r"\textcolor{red}{FAIL}"
        except (TypeError, ValueError):
            return "---"

    def _dfmt(v, nd=2):
        """Format a numeric value to nd decimal places; empty string when None."""
        try:
            return f"{float(v):.{nd}f}"
            
        except (TypeError, ValueError):
            return ""

    # Mirror generate_results_values_builder.resolve_deflection_live/total_load
    # exactly so the report shows the same numbers as the Generate Results dialog:
    # allowable from span (L/800, L/600), actual from _deflections_cache.
    try:
        _span_m = float(bridge.input_dict.get(KEY_SPAN))
        _allow_live_mm  = _span_m * 1000.0 / 800.0
        _allow_total_mm = _span_m * 1000.0 / 600.0
    except (TypeError, ValueError):
        _allow_live_mm = _allow_total_mm = None
    _allow_live_str  = (f"L/800 = {_allow_live_mm:.1f} mm")  if _allow_live_mm  is not None else ""
    _allow_total_str = (f"L/600 = {_allow_total_mm:.1f} mm") if _allow_total_mm is not None else ""

    # The report has no live _deflections_cache (it builds a ReportDataBridge from
    # output_dict only). design() persists the same per-girder cache values that
    # the Generate Results dialog shows into output_dict under the canonical
    # "G1".."Gn" suffix, so read them from there by loop index.
    t510_rows = []
    for _gi, (lbl, _) in enumerate(girder_entries, start=1):
        _live_mm  = bridge.output_dict.get(f"{KEY_SD_DEFL_LIVE}.G{_gi}")
        _total_mm = bridge.output_dict.get(f"{KEY_SD_DEFL_TOTAL}.G{_gi}")

        t510_rows.append(
            r"\multirow{2}{*}{\makecell{" + lbl + r"""}} & Live Load Deflection, $\delta_{LL}$ (mm) & """
            + _allow_live_str + r""" & """
            + _dfmt(_live_mm,  nd=3) + r""" & """
            + _defl_status(_live_mm,  _allow_live_mm) + r""" \\[6pt]
\cline{2-5}
 & Total Load Deflection, $\delta_{total}$ (mm) & """
            + _allow_total_str + r""" & """
            + _dfmt(_total_mm, nd=3) + r""" & """
            + _defl_status(_total_mm, _allow_total_mm) + r""" \\[6pt]
\hline"""
        )
    t510_content = "\n".join(t510_rows)

    # Generate Table 5.11 rows — SLS steel stress limitation (IRC 22 Cl. 604.3.1).
    # Concrete & rebar deck stresses are deck-global and belong with the deck
    # checks, so this table shows only the per-girder steel check. Steel stress is
    # a single envelope-SLS value (same for every girder); allowable = 0.9·fy.
    # Both live in the nested output_dict["design_results"] dict, not as flat keys.
    def _mpa(v):
        s = _dfmt(v, nd=2)
        return (s + " MPa") if s else ""

    def _stress_status(actual, allow):
        try:
            return "PASS" if float(actual) <= float(allow) else r"\textcolor{red}{FAIL}"
        except (TypeError, ValueError):
            return "---"

    _dr_511        = bridge.output_dict.get("design_results", {}) or {}
    _steel_sigma   = _dr_511.get(KEY_SD_STRESS_STEEL)
    _steel_allow   = _dr_511.get(KEY_SD_STRESS_STEEL_ALLOWABLE)
    _steel_sig_str = _mpa(_steel_sigma)
    _steel_alw_str = _mpa(_steel_allow)
    _steel_status  = _stress_status(_steel_sigma, _steel_allow)

    t511_rows = []
    for lbl, _ in girder_entries:
        t511_rows.append(
            r"\makecell{" + lbl + r"""} & Structural Steel ($0.9\,f_y$) & """
            + _steel_alw_str + r""" & """
            + _steel_sig_str + r""" & """
            + _steel_status + r""" \\[6pt]
\hline"""
        )
    t511_content = "\n".join(t511_rows)

    # Generate Table 5.12 rows — per-girder fatigue assessment (IRC 22 Cl. 605),
    # mirroring the Generate Results dialog: one row per girder showing the
    # GOVERNING fatigue check (worst of normal/shear by DCR). Source is the nested
    # design_results["steeldesign.uls_per_girder"]["fatigue"][G{i}] dict, keyed by
    # the canonical girder index, with {demand, capacity, ur, status}.
    _fat_cat = ((bridge.output_dict.get("design_results", {}) or {})
                .get(KEY_SD_ULS_PER_GIRDER, {}) or {}).get("fatigue", {}) or {}

    def _fat_status(s):
        if s is None or str(s).strip() == "":
            return "---"
        return r"\textcolor{red}{" + str(s) + "}" if "FAIL" in str(s).upper() else str(s)

    t512_rows = []
    for _gi, (lbl, _) in enumerate(girder_entries, start=1):
        _g = _fat_cat.get(f"G{_gi}", {}) or {}
        t512_rows.append(
            r"\makecell{" + lbl + r"""} & """
            + _mpa(_g.get("demand")) + r""" & """
            + _mpa(_g.get("capacity")) + r""" & """
            + _dfmt(_g.get("ur"), nd=2) + r""" & """
            + _fat_status(_g.get("status")) + r""" \\[6pt]
\hline"""
        )
    t512_content = "\n".join(t512_rows)

    # Generate Table 5.13 rows — per-girder design summary, mirroring the Generate
    # Results dialog's resolve_design_results_summary: one row per girder showing
    # the CONTROLLING check (highest DCR among all checks) plus the real load
    # case/combination that drives it. Source: design_results["per_girder"][G{i}].
    _pg_summary = (bridge.output_dict.get("design_results", {}) or {}).get("per_girder", {}) or {}

    def _with_unit(value, unit):
        s = _dfmt(value, nd=2)
        if not s:
            return ""
        return (s + " " + unit) if unit and str(unit) not in ("-", "–") else s

    g_summary_rows = []
    for _gi, (lbl, _) in enumerate(girder_entries, start=1):
        g_data = _pg_summary.get(f"G{_gi}", {}) or {}
        checks = g_data.get("checks") or []
        if not checks:
            g_summary_rows.append(lbl + r""" &  &  &  &  &  &  \\[6pt]
\hline""")
            continue

        ctrl = max(checks, key=lambda c: c.get("dcr") or 0.0)

        # Worst real load case for the controlling check id (skip Envelope pseudo-LCs)
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
            ctrl_lc = (g_data.get("demand") or {}).get("governing_combination") or ""

        g_summary_rows.append(
            lbl + r""" & """ + _tex(str(ctrl_lc)) + r""" & """ + _tex(str(ctrl.get("name", "")))
            + r""" & """ + _with_unit(ctrl.get("demand"),   ctrl.get("demand_unit"))
            + r""" & """ + _with_unit(ctrl.get("capacity"), ctrl.get("capacity_unit"))
            + r""" & """ + _dfmt(ctrl.get("dcr"), nd=3)
            + r""" & """ + _fat_status(ctrl.get("status")) + r""" \\[6pt]
\hline"""
        )
    g_summary_table_content = "\n".join(g_summary_rows)

    # ── Table 5.14: Shear Connector Capacity (bridge-level) ──────────────────
    # Qu (Cl.606.3.1, Eq.6.1) and Qr (Cl.606.3.2, Table 8) are single per-stud
    # values for the bridge, stored flat inside output_dict["design_results"].
    _dr_sc = bridge.output_dict.get("design_results", {}) or {}

    def _kn(v):
        s = _dfmt(v, nd=2)
        return (s + " kN") if s else ""

    t514_content = (
        r"Design Resistance, $Q_u$ & \footnotesize\makecell{$Q_u=\min(Q_{u,s},\,Q_{u,c})$\\[3pt]$Q_{u,s}=\dfrac{0.8\,f_u\,(\pi d^2/4)}{\gamma_v}$\\[3pt]$Q_{u,c}=\dfrac{0.29\,\alpha\,d^2\sqrt{f_{ck}\,E_{cm}}}{\gamma_v}$} & "
        + _kn(_dr_sc.get(KEY_SD_SC_Qu_kN)) + r""" & IRC 22 Cl. 606.3.1 (Eq. 6.1) \\[6pt]
\hline
Fatigue Shear Resistance, $Q_r$ & IRC 22 Table 8 ($\phi d$, $N_{sc}$) & """
        + _kn(_dr_sc.get(KEY_SD_SC_Qr_kN)) + r""" & IRC 22 Cl. 606.3.2 (Table 8) \\[6pt]
\hline"""
    )

    # ── Table 5.15: Shear Connector Spacing (bridge-level) ───────────────────
    # Required spacings SL1/SL2/SR and the max-spacing limit are single bridge
    # values in design_results. Each criterion passes when the provided spacing
    # is no larger than that criterion's required spacing (denser = safe).
    def _mm(v):
        s = _dfmt(v, nd=1)
        return (s + " mm") if s else ""

    _sc_prov     = _dr_sc.get("stud_spacing_provided_mm")
    _sc_prov_str = _mm(_sc_prov)

    def _sp_row(crit, req):
        return (crit + r" & " + _mm(req) + r" & " + _sc_prov_str + r" & "
                + _defl_status(_sc_prov, req) + r" \\[6pt]")

    t515_content = (
        _sp_row("ULS Shear (SL1)",            _dr_sc.get(KEY_SD_SC_SL1)) + "\n\\hline\n"
        + _sp_row("Full Composite (SL2)",       _dr_sc.get(KEY_SD_SC_SL2)) + "\n\\hline\n"
        + _sp_row("SLS Fatigue (SR)",           _dr_sc.get(KEY_SD_SC_SR)) + "\n\\hline\n"
        + _sp_row("Max Spacing Limit (IRC 22)", _dr_sc.get("stud_spacing_max_mm")) + "\n\\hline"
    )

    # ── Table 5.16: Transverse Shear & Detailing Checks (bridge-level) ───────
    # Transverse shear (Cl.606.10): VL vs slab capacity VRd. Detailing (Cl.606.6):
    # min transverse reinforcement, stud diameter ≤ 2·tf, edge distance ≥ 25 mm.
    # All single bridge values in design_results; stud diameter from input_dict.
    def _cm2m(v):
        s = _dfmt(v, nd=2)
        return (s + r" cm$^2$/m") if s else ""

    def _knm(v):
        s = _dfmt(v, nd=2)
        return (s + " kN/m") if s else ""

    _ts_vl  = _dr_sc.get(KEY_SD_TS_VL)
    _ts_vrd = _dr_sc.get(KEY_SD_TS_VRD)
    try:
        _ts_ur_str = f"{float(_ts_vl) / float(_ts_vrd):.2f}"
    except (TypeError, ValueError, ZeroDivisionError):
        _ts_ur_str = "---"
    _ts_ok = _dr_sc.get("transverse_shear_ok")
    _ts_status = (r"\textcolor{red}{FAIL}" if _ts_ok is False else "PASS") if _ts_ok is not None else "---"

    _ast_req  = _dr_sc.get("Ast_required_cm2_per_m")
    # Provided transverse steel = the deck's main (bottom + top) bars, which run
    # transversely between girders and cross the shear plane. The deck design
    # computes these (>= minimum) and they are what is actually provided. The
    # steel designer's own Ast_provided is 0 because its transverse-shear check
    # runs before design_deck_slab(), so read the deck-design value here instead.
    _dd_516 = bridge.output_dict.get("deck_design_results", {}) or {}
    try:
        _ast_prov = (float(_dd_516.get("rebar_bottom_area") or 0)
                     + float(_dd_516.get("rebar_top_area") or 0)) / 100.0
    except (TypeError, ValueError):
        _ast_prov = None
    _stud_d   = bridge.input_dict.get(KEY_DS_STUD_DIAMETER)
    _d_lim    = _dr_sc.get(KEY_SD_SC_D_LIMIT)
    _edge     = _dr_sc.get(KEY_SD_SC_EDGE_DIST)
    _edge_req = _dr_sc.get(KEY_SD_SC_REQ_EDGE_DIST)

    def _row516(check, value, status):
        return check + r" & " + value + r" & " + status + r" \\[6pt]"

    t516_content = (
        _row516(r"\textbf{Longitudinal Shear per unit length, $V_L$}", _knm(_ts_vl), "---") + "\n\\hline\n"
        + _row516(r"\textbf{Transverse Shear Capacity of Slab, $V_{Rd}$}", _knm(_ts_vrd), "---") + "\n\\hline\n"
        + _row516(r"\textbf{Transverse Shear Check}", r"$V_L/V_{Rd}$ = " + _ts_ur_str, _ts_status) + "\n\\hline\n"
        + _row516(r"\textbf{Min. Transverse Reinforcement, $A_{st,min}$}",
                  r"Required " + _cm2m(_ast_req) + r", Provided " + _cm2m(_ast_prov),
                  _defl_status(_ast_req, _ast_prov)) + "\n\\hline\n"
        + _row516(r"\textbf{Stud Diameter $\leq 2\,t_f$}",
                  r"$d$ = " + _mm(_stud_d) + r" $\leq 2t_f$ = " + _mm(_d_lim),
                  _defl_status(_stud_d, _d_lim)) + "\n\\hline\n"
        + _row516(r"\textbf{Stud Edge Distance}",
                  r"Provided " + _mm(_edge) + r" (req. $\geq$ " + _mm(_edge_req) + r")",
                  _defl_status(_edge_req, _edge)) + "\n\\hline"
    )

    # Generate Table 5.20(a) rows
    cb_forces_rows = []
    pairs = bridge.get_cb_pairs()

    if not pairs:
        # fallback: one placeholder row
        cb_forces_rows.append(
            r"""Between Girders & Diagonal &  &  &  &  \\[6pt]
\hline"""
        )
    else:
        for pair in pairs:
            pair_id = pair.replace("-", "")
            for member, label in [("diagonal", "Diagonal"),
                                ("chord", "Top / Bottom chord")]:
                force_str, ftype = bridge.get_cb_governing_force(pair, member)
                conn_type = bridge.get_cb_connection(pair, member, ftype)
                section  = bridge.get_cb_section(pair, member, ftype)

                # Fetch properties from output_dict
                if member == "diagonal":
                    pfx = f"transverse_member_design.cb.section_properties.bracing.{pair_id}"
                else:
                    pfx = f"transverse_member_design.cb.section_properties.bottom_chord.{pair_id}"
                    if bridge.output_dict.get(f"{pfx}.A") is None:
                        pfx = f"transverse_member_design.cb.section_properties.top_chord.{pair_id}"

                area_cm2 = bridge.output_dict.get(f"{pfx}.A")
                rv_cm = bridge.output_dict.get(f"{pfx}.rv")

                # Convert Area: cm² -> mm²
                area_str = f"{float(area_cm2) * 100:.1f}" if area_cm2 is not None else ""
                # Convert rv: cm -> mm
                rmin_str = f"{float(rv_cm) * 10:.1f}" if rv_cm is not None else ""
                cb_forces_rows.append(
                    r"\multirow{2}{*}{\makecell{" + _tex(pair) + r"}} & "
                    + label + r" & " + conn_type + r" & " + section
                    + r" & " + area_str + r" & " + rmin_str
                    + r" \\[6pt]\cline{2-6}"
                )
            cb_forces_rows.append(r"\hline")
    cb_forces_content = "\n".join(cb_forces_rows)

    # Generate Table 5.20(b) rows
    def get_status_str(slnd_str, limit):
        try:
            v = float(slnd_str)
            return r"\textcolor{black}{PASS}" if v <= limit else r"\textcolor{red}{FAIL}"
        except (ValueError, TypeError):
            return ""
    cb_slenderness_rows = []
    if not pairs:
        cb_slenderness_rows.append(
            r"""Between Girders & Diagonal & C &  &  &  ---  \\[6pt]
\hline"""
        )
    else:
        for pair in pairs:
            kl_diag = bridge.get_cb_effective_length("diagonal")
            slnd_diag = bridge.get_cb_slenderness(pair, "diagonal")
            status_diag = get_status_str(slnd_diag, 250)
            
            kl_tc = bridge.get_cb_effective_length("chord")
            slnd_tc = bridge.get_cb_slenderness(pair, "chord")
            status_tc = get_status_str(slnd_tc, 250)
            
            kl_bc = bridge.get_cb_effective_length("chord")
            slnd_bc = bridge.get_cb_slenderness(pair, "chord")
            status_bc = get_status_str(slnd_bc, 400)
            
            top_chord_enabled = bridge.output_dict.get("member_properties.cross_bracing_details.top_chord", True)
            bottom_chord_enabled = bridge.output_dict.get("member_properties.cross_bracing_details.bottom_chord", True)
            
            num_rows = 1 + int(top_chord_enabled) + int(bottom_chord_enabled)
            row_tex = r"\multirow{" + str(num_rows) + r"}{*}{\makecell{" + _tex(pair) + r"}}"
            row_tex += f" & Diagonal & C & {kl_diag} & {slnd_diag} & 250 --- {status_diag} \\\\[6pt]"
            
            if top_chord_enabled:
                row_tex += f"\n\\cline{{2-6}}\n & Top chord & C & {kl_tc} & {slnd_tc} & 250 --- {status_tc} \\\\[6pt]"
            if bottom_chord_enabled:
                row_tex += f"\n\\cline{{2-6}}\n & Bottom chord & T & {kl_bc} & {slnd_bc} & 400 --- {status_bc} \\\\[6pt]"
                
            row_tex += "\n\\hline"
            cb_slenderness_rows.append(row_tex)
    cb_slenderness_content = "\n".join(cb_slenderness_rows)

    # Generate Table 5.20(c) rows
    cb_capacity_rows = []
    for pair in pairs:
        rows_for_pair = []
        for member, label in [("diagonal", "Diagonal"),
                            ("chord", "Chord")]:
            force_str, ftype = bridge.get_cb_governing_force(pair, member)
            section  = bridge.get_cb_section(pair, member, ftype)
            gov_lc   = bridge.get_cb_gov_lc(pair, member, ftype)
            capacity = bridge.get_cb_capacity(pair, member, ftype)
            ur       = bridge.get_cb_efficiency(pair, member, ftype)
            status   = bridge.get_cb_status(pair, member, ftype)
            rows_for_pair.append(
                r" & " + label + r" & " + section
                + r" & " + gov_lc + r" & " + force_str + r" & " + capacity
                + r" & " + ur + r" & " + status + r" \\[6pt]\cline{2-8}"
            )
        first = r"\multirow{2}{*}{\makecell{" + _tex(pair) + r"}}" + rows_for_pair[0]
        rest  = rows_for_pair[1:]
        cb_capacity_rows.append(first)
        cb_capacity_rows.extend(rest)
        cb_capacity_rows.append(r"\hline")
    cb_capacity_content = "\n".join(cb_capacity_rows)



    # ── Deck slab design value helpers (Tables 5.17 a/b/c/e/g) ────────────────
    # Read from deck_rpt = output_dict["deck_report_values"] (common.KEY_DD_*).
    # Tables 5.17(d) punching shear and 5.17(f) one-way shear stay as
    # placeholders — those are not computed by design_deck_slab().
    _dk_has = bool(deck_rpt)
    _dk_oh = bool(deck_rpt.get(KEY_DD_HAS_OVERHANG))
    _DKPH = r"\placeholder{---}"

    def _dkv(key, default=0.0):
        """Raw float for status comparisons (0.0 if missing/non-numeric)."""
        try:
            return float(deck_rpt.get(key))
        except (TypeError, ValueError):
            return default

    def _dkf(key, nd=2, scale=1.0):
        """Formatted display string; placeholder when deck design not run."""
        if not _dk_has:
            return _DKPH
        v = deck_rpt.get(key)
        if v is None or v == "":
            return _DKPH
        try:
            return f"{float(v) * scale:.{nd}f}"
        except (TypeError, ValueError):
            return str(v)

    def _dks(ok):
        """PASS/FAIL status; '---' when deck design not run."""
        return ("PASS" if ok else "FAIL") if _dk_has else "---"

    def _dkoh(key, nd=2, scale=1.0, unit=""):
        """Overhang value; 'N/A' when there is no overhang."""
        if not _dk_has:
            return _DKPH
        if not _dk_oh:
            return "N/A"
        return _dkf(key, nd=nd, scale=scale) + unit

    # Governing crack width = max(bottom, top[, overhang]) vs the limit.
    _dk_wks = [_dkv(KEY_DD_WK_BOT), _dkv(KEY_DD_WK_TOP)]
    if _dk_oh:
        _dk_wks.append(_dkv(KEY_DD_WK_OH))
    _dk_gov_wk = max(_dk_wks)
    _dk_gov_wk_str = (f"{_dk_gov_wk:.4f}" if _dk_has else _DKPH)
    _dk_crack_ok = _dk_has and _dk_gov_wk <= _dkv(KEY_DD_WK_LIMIT)

    # ── Table 5.22: Overall Design Check Summary — fill all rows ─────────────
    # Three row families:
    #  (1) Girder DCR-engine checks: one source (design_results["per_girder"])
    #      gives Demand, Capacity, UR, and the governing LC together. Worst
    #      girder = highest DCR. Most checks fire on the envelope demand (units
    #      available in per_girder["checks"]); SLS-conditional checks (e.g.
    #      deflection) only appear per-LC, so fall back to per_lc for those.
    #  (2) Deck slab: URs from deck_design_results (Demand/Capacity not stored).
    #  (3) Cross bracing: existing get_cb_* helpers (worst pair/member by UR).
    #      End diaphragm has no report helpers yet → "---" for now.
    _pg_522 = (bridge.output_dict.get("design_results", {}) or {}).get("per_girder", {}) or {}
    _dd_522 = bridge.output_dict.get("deck_design_results", {}) or {}

    def _vu_522(v, unit):
        s = _dfmt(v, nd=2)
        if not s:
            return ""
        u = (unit or "").strip()
        return (s + " " + u) if u else s

    def _ur_522(v):
        try:
            f = float(v)
        except (TypeError, ValueError):
            return ""
        s = f"{f:.2f}"
        return (r"\textcolor{red}{" + s + "}") if f > 1.0 else s

    def _lc_short(lc):
        # Show the full combination expression as-is, e.g.
        # "ACCIDENTAL 1: 1.0DL + 1.0DW + 0.75LL" (the per_lc key).
        return _tex(str(lc).strip())

    def _gov_lc_in_522(g, check_ids):
        gd = _pg_522.get(g) or {}
        best = None
        for _lc, _ld in (gd.get("per_lc") or {}).items():
            if str(_lc).lower().startswith("envelope"):
                continue
            for _chk in (_ld.get("checks") or []):
                if _chk.get("id") in check_ids:
                    _d = _chk.get("dcr") or 0.0
                    if best is None or _d > best[0]:
                        best = (_d, _lc)
        return _lc_short(best[1]) if best else "---"

    def _dcr_row(check_ids, fallback_unit=""):
        # Prefer per_girder["checks"] (carries units); worst girder by DCR.
        best = None  # (dcr, demand, capacity, dunit, cunit, g)
        for g, gd in _pg_522.items():
            if str(g).startswith("EB"):
                continue
            for chk in (gd.get("checks") or []):
                if chk.get("check_id") in check_ids:
                    d = chk.get("dcr") or 0.0
                    if best is None or d > best[0]:
                        best = (d, chk.get("demand"), chk.get("capacity"),
                                chk.get("demand_unit") or "", chk.get("capacity_unit") or "", g)
        if best is not None:
            d, dem, cap, du, cu, g = best
            return (_gov_lc_in_522(g, check_ids),
                    _vu_522(dem, du) or "---", _vu_522(cap, cu) or "---", _ur_522(d) or "---")
        # Fallback: per_lc (no units) for SLS-conditional checks (e.g. deflection).
        best = None  # (dcr, demand, capacity, lc)
        for g, gd in _pg_522.items():
            if str(g).startswith("EB"):
                continue
            for _lc, _ld in (gd.get("per_lc") or {}).items():
                if str(_lc).lower().startswith("envelope"):
                    continue
                for chk in (_ld.get("checks") or []):
                    if chk.get("id") in check_ids:
                        d = chk.get("dcr") or 0.0
                        if best is None or d > best[0]:
                            best = (d, chk.get("demand"), chk.get("capacity"), _lc)
        if best is None:
            return ("---", "---", "---", "---")
        d, dem, cap, _lc = best
        return (_lc_short(_lc),
                _vu_522(dem, fallback_unit) or "---", _vu_522(cap, fallback_unit) or "---",
                _ur_522(d) or "---")

    # (3) Cross bracing — worst pair/member by UR for the given force type.
    _cb_pairs_522 = bridge.get_cb_pairs()

    def _cb_row(force_type):
        best = None  # (ur, pair, member, capacity_str)
        for pair in _cb_pairs_522:
            for member in ("diagonal", "chord"):
                cap = bridge.get_cb_capacity(pair, member, force_type)
                eff = bridge.get_cb_efficiency(pair, member, force_type)
                try:
                    ur = float(eff)
                except (TypeError, ValueError):
                    continue
                if best is None or ur > best[0]:
                    best = (ur, pair, member, cap)
        if best is None:
            return ("---", "---", "---", "---")
        ur, pair, member, cap = best
        gov = bridge.get_cb_gov_lc(pair, member, force_type) or "---"
        dem = f"{float(cap) * ur:.2f} kN" if cap else "---"
        cap_s = (cap + " kN") if cap else "---"
        return (gov, dem, cap_s, _ur_522(ur))

    def _cb_slender_row():
        best = None  # (ratio, slend, limit)
        for pair in _cb_pairs_522:
            for member in ("diagonal", "chord"):
                s = bridge.get_cb_slenderness(pair, member)
                try:
                    sf = float(s)
                except (TypeError, ValueError):
                    continue
                lim = 400.0 if member == "chord" else 250.0
                ratio = sf / lim
                if best is None or ratio > best[0]:
                    best = (ratio, sf, lim)
        if best is None:
            return ("---", "---", "---", "---")
        ratio, sf, lim = best
        return ("---", f"{sf:.1f}", f"{lim:.0f}", _ur_522(ratio))

    def _row522(label, cells):
        c = [x if x else "---" for x in cells]
        return label + r" & " + r" & ".join(c) + r" \\[6pt]" + "\n\\hline"

    # Deck rows: Demand/Capacity from deck_report_values (KEY_DD_*, the same dict
    # the 5.17 tables use); UR = Demand/Capacity. The deck is designed for the
    # IRC:6 Basic ULS combination — build that combo string from the stored
    # partial factors (gamma_dl, gamma_ll).
    _deck_combo = (
        r"Basic ULS: " + _tex(f"{_dkv(KEY_DD_GAMMA_DL):g}DL + {_dkv(KEY_DD_GAMMA_LL):g}LL")
    ) if _dk_has else "---"

    def _deck_row(dem_key, cap_key, unit, is_oh=False):
        if not _dk_has:
            return ("---", "---", "---", "---")
        if is_oh and not _dk_oh:
            return (_deck_combo, "N/A", "N/A", "N/A")
        dem = _dkv(dem_key)
        cap = _dkv(cap_key)
        ur = (dem / cap) if cap > 0 else None
        return (_deck_combo, f"{dem:.2f} {unit}", f"{cap:.2f} {unit}", _ur_522(ur))

    def _row522_msg(label, msg):
        # Single message spanning the 4 data columns.
        return label + r" & \multicolumn{4}{c|}{" + msg + r"} \\[6pt]" + "\n\\hline"

    # End diaphragm: when configured as Cross Bracing it is designed as bracing
    # members → mirror the cross-bracing axial rows. For Rolled / Welded beam end
    # diaphragms the moment/shear design is not implemented yet → show a message.
    _ed_type = ""
    for _k, _v in bridge.input_dict.items():
        if str(_k).startswith(KEY_MP_ED_TYPE) and _v:
            _ed_type = str(_v)
            break
    _ed_is_cb = "brac" in _ed_type.strip().lower()
    if _ed_is_cb:
        _ed_moment_row = _row522(r"End Diaphragm --- Moment", _cb_row("compression"))
        _ed_shear_row  = _row522(r"End Diaphragm --- Shear",  _cb_row("tension"))
    else:
        _ed_msg = r"Rolled / Welded section --- design to be added"
        _ed_moment_row = _row522_msg(r"End Diaphragm --- Moment", _ed_msg)
        _ed_shear_row  = _row522_msg(r"End Diaphragm --- Shear",  _ed_msg)

    # Crack width (slab): governing crack width vs limit from the deck designer
    # (frequent SLS combination). _dk_gov_wk is the max of bottom/top/overhang wk.
    # The governing load combo is the SLS-frequent combination with the highest
    # DCR (its full expression comes straight from the per_lc keys).
    def _gov_sls_frequent():
        best = None  # (dcr, lc)
        for _g, _gd in _pg_522.items():
            if str(_g).startswith("EB"):
                continue
            for _lc, _ld in (_gd.get("per_lc") or {}).items():
                if "frequent" not in str(_lc).lower():
                    continue
                _d = _ld.get("max_dcr") or 0.0
                if best is None or _d > best[0]:
                    best = (_d, _lc)
        return _tex(str(best[1]).strip()) if best else "Frequent SLS"

    _wk_lim = _dkv(KEY_DD_WK_LIMIT)
    _crack_cells = (
        (_gov_sls_frequent() if _dk_has else "---"),
        (f"{_dk_gov_wk:.3f} mm" if _dk_has else "---"),
        (f"{_wk_lim:.3f} mm" if _dk_has else "---"),
        (_ur_522(_dk_gov_wk / _wk_lim) if (_dk_has and _wk_lim > 0) else "---"),
    )

    _t522 = [
        _row522(r"Girder --- Moment",             _dcr_row({1})),
        _row522(r"Girder --- Shear",              _dcr_row({2})),
        _row522(r"Girder --- LTB (constr.)",      _dcr_row({5})),
        _row522(r"Girder --- Deflection",         _dcr_row({13, 14}, fallback_unit="mm")),
        _row522(r"Girder --- Stress",             _dcr_row({11}, fallback_unit="MPa")),
        _row522(r"Girder --- Fatigue",            _dcr_row({8, 9}, fallback_unit="MPa")),
        _row522(r"Transverse Shear (slab)",       _dcr_row({16})),
        _row522(r"Crack Width (slab)",            _crack_cells),
        _row522(r"Deck --- Flexure (sagging)",    _deck_row(KEY_DD_M_ULS_SAG, KEY_DD_MU_BOT, "kN-m/m")),
        _row522(r"Deck --- Flexure (hogging)",    _deck_row(KEY_DD_M_ULS_HOG, KEY_DD_MU_TOP, "kN-m/m")),
        _row522(r"Deck --- Cantilever Overhang",  _deck_row(KEY_DD_M_ULS_OH, KEY_DD_MU_OH, "kN-m/m", is_oh=True)),
        _row522(r"Deck --- Punching Shear",       _deck_row(KEY_DD_PUNCH_VED, KEY_DD_VRD_C_MPA, "MPa")),
        _row522(r"Deck --- One-Way Shear",        _deck_row(KEY_DD_SHEAR_VED, KEY_DD_SHEAR_VRDC, "kN/m")),
        _row522(r"Cross Bracing --- Compression", _cb_row("compression")),
        _row522(r"Cross Bracing --- Tension",     _cb_row("tension")),
        _row522(r"Cross Bracing --- Slenderness", _cb_slender_row()),
        _ed_moment_row,
        _ed_shear_row,
    ]
    t522_content = "\n".join(_t522)

    return r"""
\chapter{Design Checks}

This section presents all structural design checks performed by OsdagBridge. For each member, the demand from the governing load combination, the code-based capacity, and the utilization ratio are tabulated. All checks reference IS 800:2007 and IRC 22:2014 unless stated otherwise.

\section{Plate Girder Design}
\label{sec:plate-girder}

\vspace{1em}
\noindent\textbf{Table 5.1  Girder Section Properties (Final Optimized / User-selected)}

\begin{longtable}{|C{2.5cm}|L{8.0cm}|>{\centering\arraybackslash}p{5.0cm}|}
\hline
\textbf{Girder} & \textbf{Property} & \textbf{Value} \\[6pt]
\hline
""" + t51_content + r"""
\end{longtable}

\vspace{1em}
\noindent\textbf{Table 5.2  Girder Section Classification}

\begin{longtable}{|C{2.5cm}|C{3cm}|C{3.5cm}|C{2.5cm}|>{\centering\arraybackslash}p{4.0cm}|}
\hline
\textbf{} & \textbf{Element} & \textbf{Slenderness Ratio} & \textbf{Class Limit} & \textbf{Classification} \\[6pt]
\hline
""" + t52_content + r"""
\end{longtable}
\noindent\textit{Note: IS 800:2007 Table 2}

\vspace{1em}
\noindent\textbf{Table 5.3  Moment Capacity Check}

\begin{longtable}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.2cm}|C{1.8cm}|}
\hline
\textbf{} & \textbf{Parameter} & \textbf{Formula} & \textbf{Value} & \textbf{Status} \\[6pt]
\hline
""" + t53_content + r"""
\end{longtable}
\noindent\textit{Note: IRC 22 Cl. 603.3.1, IS 800 Cl. 8.2.1}

\vspace{1em}
\noindent\textbf{Table 5.4  Shear Capacity Check}

\begin{longtable}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.2cm}|C{1.8cm}|}
\hline
\textbf{} & \textbf{Parameter} & \textbf{Formula} & \textbf{Value} & \textbf{Status} \\[6pt]
\hline
""" + t54_content + r"""
\end{longtable}
\noindent\textit{Note: IS 800 Cl. 8.4, IRC 22 Cl. 603.3.3.2}

\vspace{1em}
\noindent\textbf{Table 5.5  Interaction Checks (M-V and M-N)}

\begin{longtable}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.2cm}|C{1.8cm}|}
\hline
\textbf{} & \textbf{Check} & \textbf{Condition} & \textbf{Value} & \textbf{Status} \\[6pt]
\hline
""" + t55_content + r"""
\end{longtable}
\noindent\textit{Note: IRC 22 Cl. 603.3.3.3}

\vspace{1em}
\noindent\textbf{Table 5.6  Lateral Torsional Buckling Check -- Construction Stage}

\begin{longtable}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.2cm}|C{1.8cm}|}
\hline
\textbf{} & \textbf{Parameter} & \textbf{Formula} & \textbf{Value} & \textbf{Status} \\[6pt]
\hline
""" + t56_content + r"""
\end{longtable}
\noindent\textit{Note: IRC 22 Cl. 603.3.3.1, IS 800 Cl. 8.2.2}


\vspace{1em}
\noindent\textbf{Table 5.7  Stiffener Design Summary}

\begin{longtable}{|C{2.5cm}|L{6.5cm}|>{\arraybackslash}p{6.5cm}|}
\hline
""" + t57_content + r"""
\end{longtable}
""" + t58_block + r"""
\vspace{1em}
\noindent\textbf{Table 5.9  End Panel Stiffener Checks}

\begin{longtable}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.2cm}|C{1.8cm}|}
\hline
\textbf{} & \textbf{Check} & \textbf{Required} & \textbf{Provided} & \textbf{Status} \\[6pt]
\hline
""" + t59_content + r"""
\end{longtable}
\noindent\textit{Note: IS 800 Cl. 8.4.2.2}


\vspace{1em}
\noindent\textbf{Table 5.10  Serviceability -- Deflection Checks}

\begin{longtable}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{3.5cm}|C{2.5cm}|}
\hline
\textbf{} & \textbf{Check} & \textbf{Allowable} & \textbf{Actual} & \textbf{Status} \\[6pt]
\hline
""" + t510_content + r"""
\end{longtable}
\noindent\textit{Note: IRC 22 Cl. 604.3.2}

\vspace{1em}
\noindent\textbf{Table 5.11  Serviceability -- Maximum Stress Limitation}

\begin{longtable}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{3.5cm}|C{2.5cm}|}
\hline
\textbf{} & \textbf{Element} & \textbf{Allowable Stress} & \textbf{Actual Stress} & \textbf{Status} \\[6pt]
\hline
""" + t511_content + r"""
\end{longtable}

\vspace{1em}
\noindent\textbf{Table 5.12  Serviceability -- Fatigue Assessment}

\begin{longtable}{|C{2.5cm}|C{3.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{3.5cm}|C{2.5cm}|}
\hline
\textbf{} & \textbf{Stress Range, $\Delta\sigma$ (MPa)} & \textbf{Fatigue Limit, $f_{fd}$ (MPa)} & \textbf{Utilization Ratio} & \textbf{Status} \\[6pt]
\hline
""" + t512_content + r"""
\end{longtable}
\noindent\textit{Note: IRC 22 Cl. 605 --- governing of normal and shear fatigue (worst by DCR). Capacity reduction factor $\mu_r$ applied where plate thickness > 25 mm.}

\vspace{1em}
\noindent\textbf{Table 5.13  Girder Design Summary (DCR / Utilization Ratio)}

\vspace{0.4em}
\begin{longtable}{|C{1.6cm}|>{\centering\arraybackslash}p{3.4cm}|C{2.4cm}|C{2.1cm}|C{2.1cm}|C{1.7cm}|C{1.6cm}|}
\hline
\textbf{Girder} & \textbf{Controlling LC / Combination} & \textbf{Controlling Check} & \textbf{Demand} & \textbf{Capacity} & \textbf{UR} & \textbf{Status} \\[6pt]
\hline
""" + g_summary_table_content + r"""
\end{longtable}
\noindent\textit{Note: UR = Demand / Capacity. A value $\leq 1.0$ indicates a passing check. The controlling check is the criterion with the highest UR for each girder, with the real load case/combination that drives it.}

\vspace{1em}
\noindent\textbf{Table 5.14  Shear Connector Capacity}

\begin{longtable}{|C{3.6cm}|C{5.6cm}|>{\centering\arraybackslash}p{2.6cm}|C{3.0cm}|}
\hline
\textbf{Parameter} & \textbf{Formula} & \textbf{Value} & \textbf{Reference} \\[6pt]
\hline
""" + t514_content + r"""
\end{longtable}

\vspace{1em}
\noindent\textbf{Table 5.15  Shear Connector Spacing}

\begin{longtable}{|L{3.2cm}|>{\centering\arraybackslash}p{4.3cm}|>{\centering\arraybackslash}p{4.3cm}|C{2.0cm}|}
\hline
\textbf{Criterion} & \textbf{Governing Spacing} & \textbf{Actual Spacing Provided} & \textbf{Status} \\[6pt]
\hline
""" + t515_content + r"""
\end{longtable}
\noindent\textit{Note: IRC 22 Cl. 606.4, 606.9. Governing spacing $= \min(S_{L1}, S_{L2}, S_R)$.}

\vspace{1em}
\noindent\textbf{Table 5.16  Transverse Shear and Detailing Checks}

\begin{longtable}{|L{5.3cm}|>{\arraybackslash}p{7.2cm}|C{2.0cm}|}
\hline
\textbf{Check} & \textbf{Value} & \textbf{Status} \\[6pt]
\hline
""" + t516_content + r"""
\end{longtable}
\noindent\textit{Note: IRC 22 Cl. 606.6, 606.10.}

% ===========================
\section{Deck Slab Design}
\label{sec:deck-design}
% ===========================

The reinforced concrete deck slab is designed per IRC~112:2011 (flexure, shear, crack width) and IRC~22:2014 (composite construction). Wheel loads are distributed using Pigeaud's method. The deck is checked for flexure in the transverse and longitudinal directions, punching shear, one-way (beam) shear, crack width, and reinforcement detailing.

\vspace{1em}
\noindent\textbf{Table 5.17(a)  Deck Slab --- Loading and Geometry}

\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\hline
\textbf{Effective Span of Deck Slab, $l_{eff}$} & """ + _dkf(KEY_DD_SPAN, nd=0, scale=1000.0) + r""" mm (girder spacing, c/c) \\[6pt]
\hline
\textbf{Deck Thickness, $t_s$} & """ + _render_value(bridge.input_dict, KEY_TS_DECK_THICKNESS) + r""" mm \\[6pt]
\hline
\textbf{Clear Cover (IRC 112 Cl. 15.2)} & Top """ + _render_value(bridge.input_dict, KEY_DS_TOP_CLEAR_COVER) + r""" / Bottom """ + _render_value(bridge.input_dict, KEY_DS_BOTTOM_CLEAR_COVER) + r""" mm \\[6pt]
\hline
\textbf{Concrete Grade (IRC 112 Cl. 6.4)} & """ + _render_value(bridge.input_dict, KEY_DECK_CONCRETE_GRADE_BASIC) + r""" ($f_{ck}$ = """ + _render_value(bridge.input_dict, KEY_MATERIAL_DECK_FCK) + r""" MPa, $f_{ctm}$ = """ + _render_value(bridge.input_dict, KEY_MATERIAL_DECK_FCTM) + r""" MPa) \\[6pt]
\hline
\textbf{Reinforcement Grade (IRC 112 Cl. 6.2)} & """ + _render_value(bridge.input_dict, KEY_DS_REINF_MATERIAL) + r""" ($f_y$ = """ + _dkf(KEY_DD_FY, nd=0) + r""" MPa) \\[6pt]
\hline
\textbf{Dead Load per Unit Area, $w_{DL}$} & """ + _dkf(KEY_DD_WDL, nd=2) + r""" kN/m² (slab self-weight) \\[6pt]
\hline
\textbf{IRC 6 Wheel Load (Class A / 70R)} & """ + _dkf(KEY_DD_WHEEL_LOAD, nd=1) + r""" kN \\[6pt]
\hline
\textbf{Tyre Contact Width (IRC 6 Annex~A)} & """ + _dkf(KEY_DD_TYRE_WIDTH, nd=0, scale=1000.0) + r""" mm (transverse) \\[6pt]
\hline
\textbf{Impact Factor (IRC 6 Cl. 208.2)} & """ + _dkf(KEY_DD_IMPACT_FACTOR, nd=3) + r""" \\[6pt]
\hline
\textbf{Governing Live Load Case} & """ + _dkf(KEY_DD_VEHICLE) + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\noindent\textbf{Table 5.17(b)  Deck Slab --- Flexure Check: Interior Panel (Pigeaud's Method)}

\begin{longtable}{|C{3.0cm}|C{3.5cm}|C{3.0cm}|>{\centering\arraybackslash}p{4.2cm}|C{1.8cm}|}
\hline
\textbf{Location} & \textbf{Parameter} & \textbf{Formula / Reference} & \textbf{Value} & \textbf{Status} \\[6pt]
\hline
\multirow{5}{*}{\makecell{At Midspan\\(Sagging)}} & Transverse BM (DL), $M_{T,DL}$ & $w_{DL}\,l_{eff}^2/10$ & """ + _dkf(KEY_DD_M_DL, nd=2) + r""" kN-m/m & --- \\[6pt]
\cline{2-5}
 & Transverse BM (LL), $M_{T,LL}$ & Effective width (IRC 112 B3.1) & """ + _dkf(KEY_DD_M_LL, nd=2) + r""" kN-m/m & --- \\[6pt]
\cline{2-5}
 & Total Design BM, $M_{u,sag}$ & """ + _dkf(KEY_DD_GAMMA_DL, nd=2) + r""" DL + """ + _dkf(KEY_DD_GAMMA_LL, nd=2) + r""" LL & """ + _dkf(KEY_DD_M_ULS_SAG, nd=2) + r""" kN-m/m & --- \\[6pt]
\cline{2-5}
 & Effective depth, $d$ & $t_s - c_{nom} - \phi/2$ & """ + _dkf(KEY_DD_D_BOT, nd=1) + r""" mm & --- \\[6pt]
\cline{2-5}
 & Moment Capacity, $M_{Rd}$ & IRC 112 Cl. 12.2 & """ + _dkf(KEY_DD_MU_BOT, nd=2) + r""" kN-m/m & """ + _dks(_dkv(KEY_DD_MU_BOT) >= _dkv(KEY_DD_M_ULS_SAG)) + r""" \\[6pt]
\hline
\multirow{3}{*}{\makecell{At Support\\(Hogging)}} & Total Design BM, $M_{u,hog}$ & """ + _dkf(KEY_DD_GAMMA_DL, nd=2) + r""" DL + """ + _dkf(KEY_DD_GAMMA_LL, nd=2) + r""" LL (at support) & """ + _dkf(KEY_DD_M_ULS_HOG, nd=2) + r""" kN-m/m & --- \\[6pt]
\cline{2-5}
 & Required Top Steel, $A_{st,top}$ & $M_u / (0.87\,f_y\,d)$ & """ + _dkf(KEY_DD_AS_REQ_TOP, nd=0) + r""" mm²/m & --- \\[6pt]
\cline{2-5}
 & Moment Capacity, $M_{Rd}$ & IRC 112 Cl. 12.2 & """ + _dkf(KEY_DD_MU_TOP, nd=2) + r""" kN-m/m & """ + _dks(_dkv(KEY_DD_MU_TOP) >= _dkv(KEY_DD_M_ULS_HOG)) + r""" \\[6pt]
\hline
\end{longtable}
\noindent\textit{Note: IRC 112 Cl. 12.2. Distribution (longitudinal) reinforcement designed for 20\% of main steel moment (IRC 21 Cl. 305.18).}

\vspace{1em}
\noindent\textbf{Table 5.17(c)  Deck Slab --- Cantilever Overhang Flexure Check}

\begin{longtable}{|L{5.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.5cm}|C{2cm}|}
\hline
\textbf{Parameter} & \textbf{Formula} & \textbf{Value} & \textbf{Status} \\[6pt]
\hline
Overhang Length, $l_{oh}$ & --- & """ + _render_value(bridge.input_dict, KEY_TS_DECK_OVERHANG, " m") + r""" & --- \\[6pt]
\hline
Crash Barrier Load Moment & IRC 6 Cl. 206.4 & """ + _dkoh(KEY_DD_M_BARRIER, nd=2, unit=" kN-m/m") + r""" & --- \\[6pt]
\hline
Dead Load Moment & $w_{DL}\,l_{oh}^2/2$ + railing & """ + _dkoh(KEY_DD_M_DL_OH, nd=2, unit=" kN-m/m") + r""" & --- \\[6pt]
\hline
Live Load Moment (eccentric wheel) & Wheel load $\times$ arm & """ + _dkoh(KEY_DD_M_LL_OH, nd=2, unit=" kN-m/m") + r""" & --- \\[6pt]
\hline
Total Hogging Moment, $M_{u,oh}$ & """ + _dkf(KEY_DD_GAMMA_DL, nd=2) + r""" DL + """ + _dkf(KEY_DD_GAMMA_LL, nd=2) + r""" (LL + CB) & """ + _dkoh(KEY_DD_M_ULS_OH, nd=2, unit=" kN-m/m") + r""" & --- \\[6pt]
\hline
Moment Capacity (top steel), $M_{Rd,oh}$ & IRC 112 Cl. 12.2 & """ + _dkoh(KEY_DD_MU_OH, nd=2, unit=" kN-m/m") + r""" & """ + (_dks(_dkv(KEY_DD_MU_OH) >= _dkv(KEY_DD_M_ULS_OH)) if _dk_oh else ("N/A" if _dk_has else "---")) + r""" \\[6pt]
\hline
\end{longtable}
\noindent\textit{Note: IRC 6 Cl. 206.4 crash barrier loads applied at kerb face; IRC 112 Cl. 12.2 flexure.}

\vspace{1em}
\noindent\textbf{Table 5.17(d)  Deck Slab --- Punching Shear Check (IRC~112 Cl.~10.4.6)}

\begin{longtable}{|L{5.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.5cm}|C{2cm}|}
\hline
\textbf{Parameter} & \textbf{Formula / Reference} & \textbf{Value} & \textbf{Status} \\[6pt]
\hline
Design Wheel Load (ULS), $V_{Ed}$ & $\gamma_Q\,(1+IF)\,P_w$ & """ + _dkf(KEY_DD_PUNCH_VED_KN, nd=1) + r""" kN & --- \\[6pt]
\hline
Tyre Contact Area & $a \times b$ (IRC 6 Annex~A) & """ + _dkf(KEY_DD_TYRE_WIDTH, nd=0, scale=1000.0) + r""" $\times$ """ + _dkf(KEY_DD_TYRE_LENGTH, nd=0) + r""" mm & --- \\[6pt]
\hline
Loaded Area at mid-depth, $b_0$ & $c_1 \times c_2$ (incl.\ WC dispersion) & """ + _dkf(KEY_DD_PUNCH_C1, nd=0) + r""" $\times$ """ + _dkf(KEY_DD_PUNCH_C2, nd=0) + r""" mm & --- \\[6pt]
\hline
Control Perimeter, $u_1$ & $2(c_1+c_2) + 4\pi d$ & """ + _dkf(KEY_DD_PUNCH_U1, nd=0) + r""" mm & --- \\[6pt]
\hline
Punching Shear Stress, $v_{Ed}$ & $V_{Ed} / (u_1\,d)$ & """ + _dkf(KEY_DD_PUNCH_VED, nd=3) + r""" MPa & --- \\[6pt]
\hline
Punching Resistance, $v_{Rd,c}$ & IRC 112 Eq.\ 10.1 & """ + _dkf(KEY_DD_VRD_C_MPA, nd=3) + r""" MPa & --- \\[6pt]
\hline
Punching Shear Check & $v_{Ed} \leq v_{Rd,c}$ & """ + (f"{_dkv(KEY_DD_PUNCH_VED) / _dkv(KEY_DD_VRD_C_MPA):.2f}" if (_dk_has and _dkv(KEY_DD_VRD_C_MPA) > 0) else _DKPH) + r""" & """ + _dks(bool(deck_rpt.get(KEY_DD_PUNCH_OK))) + r""" \\[6pt]
\hline
\end{longtable}
\noindent\textit{Note: Punching shear reinforcement not typically required for deck slabs with $d \geq 200$ mm and adequate longitudinal reinforcement.}

\vspace{1em}
\noindent\textbf{Table 5.17(e)  Crack Width Check (Deck Slab)}

\begin{longtable}{|C{7cm}|>{\arraybackslash}p{8.5cm}|}
\hline
\textbf{Min. Reinforcement for Crack Control, $A_{s,min}$} & """ + _dkf(KEY_DD_AS_MIN, nd=0) + r""" mm²/m [IRC 112 Cl. 16.5.1] \\[6pt]
\hline
\textbf{Provided Reinforcement (bottom)} & $\phi$""" + _dkf(KEY_DD_DIA_BOT, nd=0) + r""" @ """ + _dkf(KEY_DD_SPC_BOT, nd=0) + r""" mm c/c (""" + _dkf(KEY_DD_AS_BOT, nd=0) + r""" mm²/m) \\[6pt]
\hline
\textbf{Max. Permissible Crack Width} & """ + _dkf(KEY_DD_WK_LIMIT, nd=2) + r""" mm \\[6pt]
\hline
\textbf{Calculated Crack Width, $w_k$ (governing)} & """ + _dk_gov_wk_str + r""" mm \\[6pt]
\hline
\textbf{Crack Width Check} & """ + _dks(_dk_crack_ok) + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\noindent\textbf{Table 5.17(f)  One-Way (Beam) Shear Check (Deck Slab)}

\begin{longtable}{|L{5.5cm}|C{3.5cm}|>{\centering\arraybackslash}p{4.5cm}|C{2cm}|}
\hline
\textbf{Parameter} & \textbf{Formula / Reference} & \textbf{Value} & \textbf{Status} \\[6pt]
\hline
Design Shear per unit width, $V_{Ed}$ & $\gamma_{DL} V_{DL} + \gamma_{LL}(1{+}IF)V_{LL}$ & """ + _dkf(KEY_DD_SHEAR_VED, nd=2) + r""" kN/m & --- \\[6pt]
\hline
Effective depth, $d$ & $t_s - c_{nom} - \phi/2$ & """ + _dkf(KEY_DD_D_BOT, nd=1) + r""" mm & --- \\[6pt]
\hline
Size factor, $k$ & $1 + \sqrt{200/d} \leq 2.0$ & """ + (f"{min(1.0 + (200.0 / _dkv(KEY_DD_D_BOT)) ** 0.5, 2.0):.3f}" if (_dk_has and _dkv(KEY_DD_D_BOT) > 0) else _DKPH) + r""" & --- \\[6pt]
\hline
Long.\ reinforcement ratio, $\rho_l$ & $A_{sl}/(b_w\,d) \leq 0.02$ & """ + (f"{min(_dkv(KEY_DD_AS_BOT) / (1000.0 * _dkv(KEY_DD_D_BOT)), 0.02):.4f}" if (_dk_has and _dkv(KEY_DD_D_BOT) > 0) else _DKPH) + r""" & --- \\[6pt]
\hline
Shear resistance (no stirrups), $V_{Rd,c}$ & $v_{Rd,c}\,b_w\,d$ (Cl.\ 10.3.2) & """ + _dkf(KEY_DD_SHEAR_VRDC, nd=2) + r""" kN/m & --- \\[6pt]
\hline
One-Way Shear Check & $V_{Ed} \leq V_{Rd,c}$ & """ + (f"{_dkv(KEY_DD_SHEAR_VED) / _dkv(KEY_DD_SHEAR_VRDC):.2f}" if (_dk_has and _dkv(KEY_DD_SHEAR_VRDC) > 0) else _DKPH) + r""" & """ + _dks(bool(deck_rpt.get(KEY_DD_SHEAR_OK))) + r""" \\[6pt]
\hline
\end{longtable}
\noindent\textit{Note: IRC 112 Cl. 10.3.2. Shear reinforcement not provided in deck slabs; capacity relies on concrete and main reinforcement.}

\vspace{1em}
\noindent\textbf{Table 5.17(g)  Reinforcement Detailing Summary (Deck Slab)}

\begin{longtable}{|L{5.5cm}|>{\centering\arraybackslash}p{4.1cm}|>{\centering\arraybackslash}p{4.1cm}|C{1.8cm}|}
\hline
\textbf{Parameter} & \textbf{Required / Limit} & \textbf{Provided} & \textbf{Status} \\[6pt]
\hline
\multicolumn{4}{|l|}{\textbf{Main Reinforcement --- Bottom (Transverse)}} \\[6pt]
\hline
Required Area, $A_{st,req}$ (mm²/m) & """ + _dkf(KEY_DD_AS_REQ_BOT, nd=0) + r""" mm²/m & """ + _dkf(KEY_DD_AS_BOT, nd=0) + r""" mm²/m & """ + _dks(_dkv(KEY_DD_AS_BOT) >= _dkv(KEY_DD_AS_REQ_BOT)) + r""" \\[6pt]
\hline
Bar Diameter $\times$ Spacing & $\phi \geq 10$ mm (IRC 112) & $\phi$""" + _dkf(KEY_DD_DIA_BOT, nd=0) + r""" @ """ + _dkf(KEY_DD_SPC_BOT, nd=0) + r""" mm c/c & --- \\[6pt]
\hline
Min.\ Reinforcement $A_{s,min}$ (IRC 112 Cl. 16.3.1) & """ + _dkf(KEY_DD_AS_MIN, nd=0) + r""" mm²/m & """ + _dkf(KEY_DD_AS_BOT, nd=0) + r""" mm²/m & """ + _dks(_dkv(KEY_DD_AS_BOT) >= _dkv(KEY_DD_AS_MIN)) + r""" \\[6pt]
\hline
Max.\ Bar Spacing (IRC 112 Cl. 16.3.2) & """ + _dkf(KEY_DD_SPACING_MAX, nd=0) + r""" mm & """ + _dkf(KEY_DD_SPC_BOT, nd=0) + r""" mm & """ + _dks(0.0 < _dkv(KEY_DD_SPC_BOT) <= _dkv(KEY_DD_SPACING_MAX)) + r""" \\[6pt]
\hline
\multicolumn{4}{|l|}{\textbf{Distribution Reinforcement --- Longitudinal}} \\[6pt]
\hline
Required Area, $A_{st,dist}$ (mm²/m) & $\geq 20\%$ of main steel & """ + _dkf(KEY_DD_AS_LONG, nd=0) + r""" mm²/m & """ + _dks(_dkv(KEY_DD_AS_LONG) >= max(0.20 * _dkv(KEY_DD_AS_BOT), _dkv(KEY_DD_AS_MIN))) + r""" \\[6pt]
\hline
\multicolumn{4}{|l|}{\textbf{Top Reinforcement (Support / Cantilever Overhang)}} \\[6pt]
\hline
Required Area, $A_{st,top}$ (mm²/m) & """ + _dkf(KEY_DD_AS_REQ_TOP, nd=0) + r""" mm²/m & """ + _dkf(KEY_DD_AS_TOP, nd=0) + r""" mm²/m & """ + _dks(_dkv(KEY_DD_AS_TOP) >= _dkv(KEY_DD_AS_REQ_TOP)) + r""" \\[6pt]
\hline
\multicolumn{4}{|l|}{\textbf{Cover and Detailing}} \\[6pt]
\hline
Clear Cover (IRC 112 Cl. 15.2) & $\geq$ """ + _dkf(KEY_DD_MIN_COVER, nd=0) + r""" mm (Table 14.2) & Top """ + _render_value(bridge.input_dict, KEY_DS_TOP_CLEAR_COVER) + r""" / Bottom """ + _render_value(bridge.input_dict, KEY_DS_BOTTOM_CLEAR_COVER) + r""" mm & """ + _dks(bool(deck_rpt.get(KEY_DD_COVER_OK))) + r""" \\[6pt]
\hline
\end{longtable}
\noindent\textit{Note: IRC 112 Cl. 16.3, IS 456 Cl. 26.5. All reinforcement provisions satisfy strength and detailing requirements.}

% ===========================
\section{Cross Bracing Design}
\label{sec:cross-bracing}
% ===========================

Cross bracing between adjacent plate girders provides lateral stability during construction, resists transverse loads (wind, seismic, braking) in service, and prevents lateral torsional buckling of the girders. Members are designed per IS~800:2007 Cl.~7 (compression) and Cl.~6 (tension). Forces are derived from the grillage model under the governing load combination  (DL + LL + WL).

\vspace{1em}
\noindent\textbf{Table 5.20(a)  Cross Bracing --- Connection and Section Properties}

\vspace{0.4em}
\noindent
\setlength{\tabcolsep}{4pt}
\begin{longtable}{|C{2.0cm}|C{2.0cm}|C{2.2cm}|C{2.5cm}|C{2.0cm}|C{2.0cm}|}
\hline
\textbf{Panel} & \textbf{Member} & \textbf{Connection} & \textbf{Section} & \textbf{$A_g$ (mm²)} & \textbf{$r_{min}$ (mm)} \\[6pt]
\hline
""" + cb_forces_content + r"""
\end{longtable}
\noindent\textit{Note: $A_g$ = gross cross-sectional area; $r_{min}$ = minimum radius of gyration.}

\vspace{1em}
\noindent\textbf{Table 5.20(b)  Cross Bracing --- Slenderness Ratio Check (IS~800 Cl.~3.8 \& Table~3)}

\begin{longtable}{|C{2.2cm}|C{2.2cm}|C{2.5cm}|C{2.5cm}|C{2.5cm}|>{\centering\arraybackslash}p{3.6cm}|}
\hline
\textbf{Panel} & \textbf{Member} & \textbf{Nature} & \textbf{Eff.\ Length $KL$ (mm)} & \textbf{$KL/r$} & \textbf{Limit / Status} \\[6pt]
\hline
""" + cb_slenderness_content + r"""
\end{longtable}
\noindent\textit{Note:  3. Limit = 250 for compression members, 400 for tension members. $K = 1.0$ for members with both ends pinned.}


\vspace{1em}
\noindent\textbf{Table 5.20(c)  Cross Bracing Design --- Capacity Summary}
\begin{longtable}{|C{2.0cm}|C{1.8cm}|C{2.2cm}|C{3.0cm}|C{1.8cm}|C{1.8cm}|C{1.2cm}|C{1.8cm}|}
\hline
\textbf{Panel} & \textbf{Member} & \textbf{Section} & \textbf{Governing LC} & \textbf{Demand (kN)} & \textbf{Capacity (kN)} & \textbf{UR} & \textbf{Status} \\[6pt]
\hline
""" + cb_capacity_content + r"""
\end{longtable}
\noindent\textit{Note: Designed per IS 800 Cl. 7 (compression) and Cl. 6 (tension). OsdagBridge cross-bracing module used.}

% ===========================
\section{End Diaphragm Design}
\label{sec:end-diaphragm}
% ===========================

End diaphragms at the supports transfer transverse loads to the bearings, restrain the bottom flanges against lateral displacement, and maintain the girder cross-section geometry during construction and in service. They are designed per IS~800:2007 and IRC~24:2010 Cl.~507.

\vspace{1em}
\noindent\textbf{Table 5.21(a)  End Diaphragm --- Connection and Section Properties}

\vspace{0.4em}
\noindent
\setlength{\tabcolsep}{4pt}
\begin{longtable}{|C{2.0cm}|C{2.0cm}|C{2.2cm}|C{2.5cm}|C{2.0cm}|C{2.0cm}|}
\hline
\textbf{Panel} & \textbf{Member} & \textbf{Connection} & \textbf{Section} & \textbf{$A_g$ (mm²)} & \textbf{$r_{min}$ (mm)} \\[6pt]
\hline
""" + cb_forces_content + r"""
\end{longtable}
\noindent\textit{Note: $A_g$ = gross cross-sectional area; $r_{min}$ = minimum radius of gyration.}

\vspace{1em}
\noindent\textbf{Table 5.21(b)  End Diaphragm --- Slenderness Ratio Check (IS~800 Cl.~3.8 \& Table~3)}

\begin{longtable}{|C{2.2cm}|C{2.2cm}|C{2.5cm}|C{2.5cm}|C{2.5cm}|>{\centering\arraybackslash}p{3.6cm}|}
\hline
\textbf{Panel} & \textbf{Member} & \textbf{Nature} & \textbf{Eff.\ Length $KL$ (mm)} & \textbf{$KL/r$} & \textbf{Limit / Status} \\[6pt]
\hline
""" + cb_slenderness_content + r"""
\end{longtable}
\noindent\textit{Note:  3. Limit = 250 for compression members, 400 for tension members. $K = 1.0$ for members with both ends pinned.}


\vspace{1em}
\noindent\textbf{Table 5.21(c)  End Diaphragm Design --- Capacity Summary}
\begin{longtable}{|C{2.0cm}|C{1.8cm}|C{2.2cm}|C{3.0cm}|C{1.8cm}|C{1.8cm}|C{1.2cm}|C{1.8cm}|}
\hline
\textbf{Panel} & \textbf{Member} & \textbf{Section} & \textbf{Governing LC} & \textbf{Demand (kN)} & \textbf{Capacity (kN)} & \textbf{UR} & \textbf{Status} \\[6pt]
\hline
""" + cb_capacity_content + r"""
\end{longtable}
\noindent\textit{Note: Designed per IS 800 Cl. 7 (compression) and Cl. 6 (tension). OsdagBridge cross-bracing module used.}

% ===========================
\section{Overall Design Check Summary}
\label{sec:overall-summary}
% ===========================

\vspace{1em}
\noindent\textbf{Table 5.22  Overall Design Check Summary --- All Members}

\begin{longtable}{|C{3.4cm}|C{4.5cm}|C{2.3cm}|C{2.3cm}|>{\centering\arraybackslash}p{1.6cm}|}
\hline
\textbf{Member / Check} & \textbf{Governing Load Combo} & \textbf{Demand} & \textbf{Capacity} & \textbf{UR} \\[6pt]
\hline
""" + t522_content + r"""
\end{longtable}
\noindent\textit{Note: UR = Demand / Capacity. All values $\leq 1.0$ indicate passing checks. The governing check for each component is highlighted in the individual design check sections above.}

"""


# Chapters 6-9: Drawings, Quantities, Logs, References


def _fig_embed(path, caption, width=r'\textwidth', height=None):
    """Embed a real figure when path is provided (already copied); otherwise use an fbox placeholder."""
    if path:
        p = path.replace('\\', '/')
        opts = 'width=' + width
        if height:
            opts += ',height=' + height + ',keepaspectratio'
        return (r'\begin{figure}[H]' + '\n'
                r'\vspace{-0.5em}' + '\n'
                r'\centering' + '\n'
                r'\includegraphics[' + opts + ']{' + p + '}\n'
                r'\vspace{-0.5em}' + '\n'
                r'\caption*{\small ' + caption + '}\n'
                r'\vspace{-0.5em}' + '\n'
                r'\end{figure}')
    # fbox placeholder — matches template exactly
    return (r'\noindent\fbox{\parbox{0.97\textwidth}{' + '\n'
            r'\textit{[ PLACEHOLDER: ' + caption + r' ]}' + '\n'
            r'}}')


def ch6_drawings(fig_paths):
    """Chapter 6 – Drawings and Visualizations.

    Layout: section heading → figure → small numbered label below.
    No subsection headers. 6.3 and 6.4 are headings only (no figures).
    """

    def _sec_fig(path, label, title):
        """Figure block: image first, numbered label below. Placeholder if no path."""
        label_line = r'\noindent{\small \textbf{' + label + r'}\enspace ' + title + r'}' + '\n\\vspace{8pt}'
        if path:
            p = path.replace('\\', '/')
            return (r'\begin{figure}[H]' + '\n'
                    r'\centering' + '\n'
                    r'\vspace{4pt}' + '\n'
                    r'\includegraphics[width=0.85\textwidth]{' + p + '}\n'
                    r'\vspace{4pt}' + '\n'
                    r'\end{figure}' + '\n'
                    + label_line)
        return (r'\noindent\fbox{\parbox{0.97\textwidth}{' + '\n'
                r'\textit{[ PLACEHOLDER: ' + label + ' ' + title + r' ]}' + '\n'
                r'}}' + '\n'
                + label_line)

    sup3d  = _sec_fig(fig_paths.get('final_geometry'),    '6.1.1', 'Overall 3D Bridge Superstructure')
    cs     = _sec_fig(fig_paths.get('cross_section'),     '6.1.2', 'Typical Cross Section')
    gtop   = _sec_fig(fig_paths.get('girder_top'),        '6.1.3', 'Top View')
    g3d    = _sec_fig(fig_paths.get('girder_3d'),         '6.2.1', '3D View of Plate Girders')
    gxsec  = _sec_fig(fig_paths.get('section_preview'),   '6.2.2', 'Cross Section of Plate Girder')
    gside  = _sec_fig(fig_paths.get('stiffener_preview'), '6.2.3', 'Side View of Girder')
    cbdia  = _sec_fig(fig_paths.get('cb_diagram'),        '6.3.1', 'Cross Bracing Layout')

    def _sec_cell(path, label, title):
        """One minipage cell: image above, numbered label below (for side-by-side row)."""
        if path:
            p = path.replace('\\', '/')
            body = r'\includegraphics[width=\linewidth]{' + p + '}'
        else:
            body = r'\fbox{\parbox{0.95\linewidth}{\centering\textit{[ ' + label + ' ' + title + r' ]}}}'
        return (r'\begin{minipage}[t]{0.31\textwidth}' + '\n'
                r'\centering' + '\n'
                + body + '\n'
                r'\\[4pt]{\small \textbf{' + label + r'}\enspace ' + title + '}\n'
                r'\end{minipage}')

    # The 3 cross bracing section views in a single row.
    cb_sections_row = (r'\begin{figure}[H]' + '\n'
                       r'\centering' + '\n'
                       + _sec_cell(fig_paths.get('cb_bracing'),      '6.3.2', 'Bracing Section') + '\n'
                       r'\hfill' + '\n'
                       + _sec_cell(fig_paths.get('cb_top_chord'),    '6.3.3', 'Top Chord Section') + '\n'
                       r'\hfill' + '\n'
                       + _sec_cell(fig_paths.get('cb_bottom_chord'), '6.3.4', 'Bottom Chord Section') + '\n'
                       r'\end{figure}')

    eddia  = _sec_fig(fig_paths.get('ed_diagram'),        '6.4.1', 'End Diaphragm Layout')

    # The 3 end diaphragm section views in a single row.
    ed_sections_row = (r'\begin{figure}[H]' + '\n'
                       r'\centering' + '\n'
                       + _sec_cell(fig_paths.get('ed_bracing'),      '6.4.2', 'Bracing Section') + '\n'
                       r'\hfill' + '\n'
                       + _sec_cell(fig_paths.get('ed_top_chord'),    '6.4.3', 'Top Chord Section') + '\n'
                       r'\hfill' + '\n'
                       + _sec_cell(fig_paths.get('ed_bottom_chord'), '6.4.4', 'Bottom Chord Section') + '\n'
                       r'\end{figure}')

    return (r"""
\chapter{Drawings and Visualizations}
\label{ch:drawings}

This section presents CAD-generated views of the designed bridge and its components. All views are generated automatically by OsdagBridge using pythonOCC.

\section{Bridge Configuration and Layout}
\label{sec:bridge-layout}

"""
            + sup3d + '\n\n'
            + cs + '\n\n'
            + gtop + r"""

\section{Plate Girder --- Detailed Views}
\label{sec:girder-views}

"""
            + g3d + '\n\n'
            + gxsec + '\n\n'
            + gside + r"""

\section{Cross Bracing Detail}
\label{sec:bracing-detail}

"""
            + cbdia + '\n\n'
            + cb_sections_row + r"""

\section{End Diaphragm Detail}
\label{sec:diaphragm-detail}

"""
            + eddia + '\n\n'
            + ed_sections_row + r"""

""")


def ch7_quantities(input_dict):
    return r"""
\chapter{Material Take-off \& Quantity Summary}
\label{ch:material-takeoff}

\noindent\textbf{Table 7.1  Bill of Materials (Steel, Concrete, and Reinforcement Quantities)}

\begingroup
\setlength{\tabcolsep}{3.5pt}
\begin{longtable}{|C{1.0cm}|L{3.8cm}|C{2.6cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|}
\hline
\textbf{S.N.} & \textbf{Item Description} & \textbf{Volume} & \textbf{Quantity} & \textbf{Total Volume} & \textbf{Weight (MT)} & \textbf{Total Weight (MT)} \\
\hline
1 & Structural Steel (IS 2062) for Girders & """ + str(input_dict.get("steel_girders_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("steel_girders_qty", "N.A.")) + r""" & """ + str(input_dict.get("steel_girders_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("steel_girders_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("steel_girders_wt_total", "N.A.")) + r""" \\
\hline
2(a) & Cross Bracing - Top Chord & """ + str(input_dict.get("bracing_top_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("bracing_top_qty", "N.A.")) + r""" & """ + str(input_dict.get("bracing_top_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("bracing_top_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("bracing_top_wt_total", "N.A.")) + r""" \\
\hline
2(b) & Cross Bracing - Bottom Chord & """ + str(input_dict.get("bracing_bot_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("bracing_bot_qty", "N.A.")) + r""" & """ + str(input_dict.get("bracing_bot_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("bracing_bot_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("bracing_bot_wt_total", "N.A.")) + r""" \\
\hline
2(c) & Cross Bracing - Diagonal Chord & """ + str(input_dict.get("bracing_diag_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("bracing_diag_qty", "N.A.")) + r""" & """ + str(input_dict.get("bracing_diag_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("bracing_diag_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("bracing_diag_wt_total", "N.A.")) + r""" \\
\hline
3 & Concrete (M40) for Deck Slab & """ + str(input_dict.get("concrete_deck_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("concrete_deck_qty", "N.A.")) + r""" & """ + str(input_dict.get("concrete_deck_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("concrete_deck_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("concrete_deck_wt_total", "N.A.")) + r""" \\
\hline
4 & Reinforcement Steel (Fe 500) & """ + str(input_dict.get("rebar_deck_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("rebar_deck_qty", "N.A.")) + r""" & """ + str(input_dict.get("rebar_deck_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("rebar_deck_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("rebar_deck_wt_total", "N.A.")) + r""" \\
\hline
5 & Shear Stud Connectors & """ + str(input_dict.get("shear_studs_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("shear_studs_qty", "N.A.")) + r""" & """ + str(input_dict.get("shear_studs_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("shear_studs_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("shear_studs_wt_total", "N.A.")) + r""" \\
\hline
6 & Crash Barrier & """ + str(input_dict.get("crash_barrier_vol_formula", "N.A.")) + r""" & """ + str(input_dict.get("crash_barrier_qty", "N.A.")) + r""" & """ + str(input_dict.get("crash_barrier_vol_total", "N.A.")) + r""" & """ + str(input_dict.get("crash_barrier_wt_single", "N.A.")) + r""" & """ + str(input_dict.get("crash_barrier_wt_total", "N.A.")) + r""" \\
\hline
\end{longtable}
"""


def ch8_design_log(log_entries: List[str], input_dict: dict) -> str:
    """Render Chapter 8 using real log_entries, matching Osdag color convention."""
    lines_tex = []
    if log_entries:
        for entry in log_entries:
            for raw_line in entry.split('\n'):
                line = raw_line.strip()
                if not line:
                    continue
                escaped = (line
                    .replace('_', r'\_')
                    .replace('%', r'\%')
                    .replace('&', r'\&')
                    .replace('#', r'\#'))
                upper = line.upper()
                if 'WARNING' in upper:
                    lines_tex.append(
                        rf'\textcolor{{blue}}{{{escaped}}}\\')
                elif 'ERROR' in upper:
                    lines_tex.append(
                        rf'\textcolor{{red}}{{{escaped}}}\\')
                elif 'INFO' in upper:
                    lines_tex.append(
                        rf'\textcolor{{osdagGreen}}{{{escaped}}}\\')
                else:
                    continue  # skip lines without a known level — Osdag patter

    mode = str(input_dict.get(KEY_DESIGN_MODE, 'Optimized')).strip().lower()
    is_custom = mode in {'custom', 'customized'}

    log_body = '\n'.join(lines_tex)

    return _ch8_assumptions(is_custom) + '\n\n' + log_body


def _ch8_assumptions(is_custom: bool) -> str:
    assumptions = [
        r"""
\chapter{Standards \& Assumptions}
\label{ch:Design Standards}

This section provides references to standards used to calibrate the OsdagBridge
design modules, and notes the limitations of the current software version.

\section{Design Standards}
\label{sec:design_standards}

The following Indian Road Congress (IRC) codes and Indian Standards (IS) 
form the basis of all design calculations in this software.


\begin{table}[H]
\caption{IRC Codes}
\begin{tabular}{|c|c|p{13cm}|}
\hline
Code & Year & Title / Scope \\ 
\hline
IRC 5 & 2015 & General Features of Design - carriageway widths, kerb, footpath dimensions \\ 
\hline
IRC 6 & 2017 & Loads and Load Combinations - dead load, live load, impact, wind, temperature, etc. \\ 
\hline
IRC 22 & 2015 & Composite Construction (LS) - Composite section properties, ULS/SLS design, shear connectors \\ 
\hline
IRC 24 & 2010 & Steel Road Bridges (LS) - Stiffener design, skew angle limits, diaphragm requirements \\ 
\hline
IRC 112 & 2020 & Concrete Road Bridges - Deck slab flexure, shear, crack width, reinforcement \\ 
\hline
IRC SP 114 & 2018 & Seismic Design of Road Bridges \\ 
\hline
\end{tabular}
\end{table}


\begin{table}[H]
\caption{IS Codes}
\begin{tabular}{|c|c|p{13cm}|}
\hline
Code & Year & Scope \\
\hline
IS 800 & 2007 & Steel construction - tension, compression, bending, shear, LTB, stiffeners, combined checks \\
\hline
IS 456 & 2000 & Concrete - simplified stress-block for deck moment capacity \\
\hline
IS 1786 & 2008 & Reinforcement steel properties \\
\hline
IS 1893 (Part 3) & 2014 & Earthquake resistant design \\
\hline
IS 2062 & 2011 & Structural steel - yield and ultimate strength by grade \\
\hline
\end{tabular}
\end{table}

\clearpage
\section{Analysis and Design Assumptions of This Version}
\label{sec:assumptions}


\textbf{Structural Analysis}

\begin{itemize}
    \item All girders are modelled as simply supported; continuous spans are not currently supported.
    \item A 3D grillage model (OSPGrillage) is used for load distribution. Grillage members carry composite section properties after the construction stage.
    \item The transverse member forces are computed using an approximate 2D frame analogy. For irregular or skewed geometries, a 3D FEM is recommended.
    \item Fixed bearing stiffness is modelled as $k = 1{,}000{,}000 \,\text{kN/m}$ (virtually rigid); free/expansion bearing as $k = 100 \, \text{kN/m}$.
    \item Construction stage sequence analysis is approximate. Detailed staged analysis should be performed for long-term deflection checks.
\end{itemize}

\textbf{Composite Action}

\begin{itemize}
    \item Full shear connection is assumed at ULS with headed stud connectors designed per IRC 22:2015 Cl.606.
    \item Short-term composite section properties (modular ratio $n = E_s/E_{cm}$) are used for ULS checks.
    \item Long-term composite section properties (with creep-adjusted modular ratio) are used for SLS deflection and crack-width checks.
    \item Pre-composite stage: the steel girder alone resists all construction loads prior to concrete gaining strength.
\end{itemize}
"""
    ]

    if not is_custom:
        assumptions.append(r"""
\textbf{Material Properties (IRC 22:2015 Annex III)}

\begin{itemize}
\item Steel: $E_s = 200{,}000 \, \text{MPa}, \ G_s = 80{,}000 \, \text{MPa}, \ \nu = 0.30, \ \alpha = 11.7 \times 10^{-6}/^\circ\mathrm{C}$ (grade-independent).
\item Minimum structural concrete grade: M25.
\item Default reinforcement grade: Fe500.
\end{itemize}

\textbf{Partial Safety Factors (IRC 22:2015 Cl.601.4)}

\begin{itemize}
\item $\gamma_{m0}$ (steel yield, ULS) = 1.10
\item $\gamma_{m1}$ (steel ultimate, ULS) = 1.25
\item Reinforcement (ULS) = 1.15
\item Welds -- shop: 1.25; field: 1.50
\item Fatigue ($\gamma_{mft}$) = 1.35
\end{itemize}

\textbf{Loading}

\begin{itemize}
\item Dead load densities per IRC 6:2017 Cl.203: structural steel $78.5 \ \text{kN/m}^3$, concrete $25.0 \ \text{kN/m}^3$, bituminous wearing course $24.0 \ \text{kN/m}^3$.
\item Multi-lane live load reduction factors per IRC 6:2017 Cl.204.4 Table 6A: 1st lane = 1.0, 2nd lane = 0.8, 3rd lane onwards = 0.4.
\item Impact factor (dynamic load allowance) computed from span per IRC 6:2017 Cl.208.2/208.3.
\item Wind load applied as transverse, longitudinal, and vertical components per IRC 6:2017 Cl.209.3.3--209.3.5.
\end{itemize}

\textbf{Serviceability Limits}

\begin{itemize}
\item Deflection limits (IRC 22:2015 Cl.604.3.2): live load + impact $\leq L/800$; total $\leq L/600$.
\item SLS stress limits: concrete $\sigma_c \leq 0.48 f_{ck}$; rebar $\sigma_s \leq 0.80 f_{yk}$; steel $f_e \leq 0.9 f_y$.
\item Permissible crack width: $w_k \leq 0.3 \ \text{mm}$ (bridge deck, exposure class XS2/XD2 per IRC 112:2020 Cl.12.3.2).
\end{itemize}

\textbf{Fatigue}

\begin{itemize}
\item Reference fatigue life: $N_{sc} = 2 \times 10^6$ cycles (IRC 22:2015 Cl.605).
\item Constant stress range is assumed. A thickness correction factor $\mu_r$ is applied for plate thickness $> 25 \ \text{mm}$.
\end{itemize}

\textbf{Stiffener Design}

\begin{itemize}
\item Intermediate transverse stiffener and bearing stiffener design follows IS 800:2007 Cl.8.7.2/8.7.3 and IRC 24:2010 Cl.509.7.2/509.7.3.
\end{itemize}
""")

    assumptions.append(r"""
\section{Known Limitations of This Version}
\label{sec:limitations}

\begin{itemize}
\item Substructure (piers, pile caps, foundations) and bearing design are not included.
\item Splice connection design is not implemented.
\item Skew angle $>$ 15 degrees requires independent manual analysis (IRC 24 Cl. 504.8).
\item Construction stage sequence analysis is approximate; detailed staged analysis
  should be performed for long-term deflection checks.
\item The grillage analysis assumes simply supported boundary conditions;
  continuous spans are not currently supported.
\end{itemize}
""")

    return "\n".join(assumptions)


def ch9_references():
    return r"""
\chapter{References}
\label{ch:references}

\begin{enumerate}

\item IRC 5 (Latest) --- \textit{Standard Specifications and Code of Practice for Road Bridges, Section I: General Features of Design.}

\item IRC 6 (Latest) --- \textit{Standard Specifications and Code of Practice for Road Bridges, Section II: Loads and Load Combinations.}

\item IRC 22 (2014) --- \textit{Standard Specifications and Code of Practice for Road Bridges, Section VI: Composite Construction (Limit State Design).}

\item IRC 24 (2010) --- \textit{Standard Specifications and Code of Practice for Road Bridges, Section V: Steel Road Bridges (Limit State Method).}

\item IRC 112 (2011) --- \textit{Code of Practice for Concrete Road Bridges.}

\item IRC SP 114 (2018) --- \textit{Guidelines for Seismic Design of Road Bridges.}

\item IS 800 (2007) --- \textit{Indian Standard: General Construction in Steel --- Code of Practice.}

\item IS 2062 (Latest) --- \textit{Hot Rolled Medium and High Tensile Structural Steel --- Specification.}

\item Subramanian, N. (2008). \textit{Design of Steel Structures.} Oxford University Press.

\item Steel-INSDAG Teaching Resource Materials. \url{https://www.steel-insdag.org}

\item OsdagBridge DDCL --- Design of Steel Girder Bridge. Dr. Nidhi Khare, Prof. Siddhartha Ghosh. IIT Bombay, April 2026.

\end{enumerate}
"""

# --- TEMPLATES END ---


# ---------------------------------------------------------------------------
# Public data-classes 
# ---------------------------------------------------------------------------

@dataclass
class ReportMetadata:
    project_name: str
    project_location: str
    designer: str
    client: str
    company: str
    group_name: str = ''
    subtitle: str = ''
    job_number: str = ''
    additional_comments: str = ''
    logo_path: Optional[str] = None
    report_date: str = ''
    reviewer: str = ''

@dataclass
class ReportOptions:
    sections: List[str]
    include_figures: bool
    include_toc: bool
    include_pdf: bool

@dataclass
class ReportRequest:
    metadata: ReportMetadata
    options: ReportOptions
    output_dir: str
    file_stem: str

@dataclass
class ReportFigures:
    plan:            Optional[str] = None
    cross_section:   Optional[str] = None
    final_geometry:  Optional[str] = None
    longitudinal_elevation: Optional[str] = None
    girder_3d:       Optional[str] = None
    girder_front:    Optional[str] = None
    girder_top:      Optional[str] = None
    girder_end:      Optional[str] = None
    bm_envelope:     Optional[str] = None
    sf_envelope:     Optional[str] = None
    defl_ll:         Optional[str] = None
    shear_connector: Optional[str] = None
    cross_bracing:   Optional[str] = None

@dataclass
class ReportPayload:
    metadata:         ReportMetadata
    options:          ReportOptions
    inputs:           dict
    analysis_summary: dict
    design_checks:    list
    figures:          ReportFigures
    log_entries:      List[str] = field(default_factory=list)
    output_dict:      dict = field(default_factory=dict)
    figure_data:      dict = field(default_factory=dict)  # {attr: bytes} — cleared after writing to tmpdir


@dataclass
class ReportResult:
    pdf_path: Optional[str]
    tex_path: Optional[str]


class ReportDataBridge:
    """Centralized data extraction for the OsdagBridge report."""



    def __init__(self, output_dict: dict, input_dict: dict, payload: "ReportPayload"):
        self.output_dict = output_dict
        self.input_dict = input_dict
        self.payload = payload


    # =====================================================================
    # CHAPTER 5: CROSS BRACING
    # =====================================================================

    def _cb_forces_dict(self) -> dict:
        """Internal: return crossbracing_forces_dict from output_dict."""
        return self.output_dict.get("crossbracing_forces_dict", {})

    def _cb_pair_designs(self) -> dict:
        """Internal: return crossbracing_design_results from output_dict."""
        return self.output_dict.get("crossbracing_design_results", {})

    def _cb_osdag(self, pair: str, member: str, force_type: str) -> dict:
        """
        Extract the _extract_osdag_summary dict for one member.
        pair      e.g. "G1-G2"
        member    "diagonal" or "chord"
        force_type "tension" or "compression"
        """
        from osdagbridge.core.bridge_types.plate_girder.results_data import _extract_osdag_summary
        try:
            raw = self._cb_pair_designs()[pair][member][force_type]
            return _extract_osdag_summary(raw or {})
        except (KeyError, TypeError):
            return {}

    def get_cb_pairs(self) -> list:
        """Return sorted list of girder pair keys e.g. ['G1-G2', 'G2-G3']."""
        try:
            return sorted(self._cb_forces_dict().get("pairs", {}).keys())
        except Exception:
            return []

    def get_cb_geometry(self) -> dict:
        """Return the geometry sub-dict from forces_dict."""
        return self._cb_forces_dict().get("geometry", {})

    def get_cb_brace_type(self) -> str:
        try:
            return self._cb_forces_dict().get("brace_type", "X")
        except Exception:
            return "X"

    # --- Table 5.20(a): Member Forces ---

    def get_cb_force(self, pair: str, member: str, force_type: str) -> str:
        """
        Return demand force string for table 5.20(a).
        member: "diagonal" or "chord"
        force_type: "tension" or "compression"
        """
        try:
            pairs = self._cb_forces_dict()["pairs"][pair]
            key = f"diag_{force_type}_kN" if member == "diagonal" else f"chord_{force_type}_kN"
            val = pairs.get(key)
            if val is not None:
                return f"{val:.3f}"
        except (KeyError, TypeError):
            pass
        return ""

    def get_cb_nature(self, pair: str, member: str) -> str:
        """Return 'T', 'C', or 'T/C' depending on what forces exist for this member."""
        try:
            pairs = self._cb_forces_dict()["pairs"][pair]
            t_key = "diag_tension_kN"     if member == "diagonal" else "chord_tension_kN"
            c_key = "diag_compression_kN" if member == "diagonal" else "chord_compression_kN"
            has_t = pairs.get(t_key) is not None
            has_c = pairs.get(c_key) is not None
            if has_t and has_c:
                return "T / C"
            if has_t:
                return "T"
            if has_c:
                return "C"
        except (KeyError, TypeError):
            pass
        return ""

    def get_cb_governing_force(self, pair: str, member: str) -> tuple:
        """
        Return (force_kN_str, force_type) for the governing (max absolute) force.
        Used as the single demand value for capacity tables.
        """
        try:
            pairs = self._cb_forces_dict()["pairs"][pair]
            t_key = "diag_tension_kN"     if member == "diagonal" else "chord_tension_kN"
            c_key = "diag_compression_kN" if member == "diagonal" else "chord_compression_kN"
            t_val = pairs.get(t_key)
            c_val = pairs.get(c_key)
            if t_val is not None and c_val is not None:
                if abs(c_val) >= abs(t_val):
                    return (f"{c_val:.3f}", "compression")
                return (f"{t_val:.3f}", "tension")
            if c_val is not None:
                return (f"{c_val:.3f}", "compression")
            if t_val is not None:
                return (f"{t_val:.3f}", "tension")
        except (KeyError, TypeError):
            pass
        return ("", "compression")

    def get_cb_section(self, pair: str, member: str, force_type: str) -> str:
        """Section designation for a member e.g. '75 x 75 x 8'."""
        val = self._cb_osdag(pair, member, force_type).get("section")
        return _tex(val) if val else ""

    def get_cb_capacity(self, pair: str, member: str, force_type: str) -> str:
        """Capacity in kN."""
        val = self._cb_osdag(pair, member, force_type).get("capacity_kN")
        return f"{float(val):.3f}" if val is not None else ""

    def get_cb_efficiency(self, pair: str, member: str, force_type: str) -> str:
        """Utilization ratio (efficiency)."""
        val = self._cb_osdag(pair, member, force_type).get("efficiency")
        return f"{float(val):.3f}" if val is not None else ""

    def get_cb_slenderness(self, pair: str, member: str) -> str:
        """KL/r — same for tension and compression (geometry-based)."""
        # Prefer compression result (slenderness is more meaningful there)
        for ft in ("compression", "tension"):
            val = self._cb_osdag(pair, member, ft).get("slenderness")
            if val is not None:
                return f"{float(val):.1f}"
        return ""

    def get_cb_status(self, pair: str, member: str, force_type: str) -> str:
        """PASS / FAIL based on UR <= 1.0."""
        try:
            val = self._cb_osdag(pair, member, force_type).get("efficiency")
            if val is not None:
                ur = float(val)
                if ur <= 1.0:
                    return r"\textcolor{black}{PASS}"
                return r"\textcolor{red}{FAIL}"
        except (TypeError, ValueError):
            pass
        return ""

    def get_cb_gov_lc(self, pair: str, member: str, force_type: str) -> str:
        """Governing load case label for member (tension or compression)."""
        try:
            pfx = "diag" if member == "diagonal" else "chord"
            key = f"{pfx}_{force_type}_gov_lc"
            val = self._cb_forces_dict()["pairs"][pair].get(key)
            return _tex(val) if val else ""
        except (KeyError, TypeError):
            return ""

    def get_cb_connection(self, pair: str, member: str, force_type: str) -> str:
        """Return 'Welded' or 'Bolted'."""
        val = self._cb_osdag(pair, member, force_type).get("connection")
        return str(val) if val else ""

    def get_cb_effective_length(self, member: str) -> str:
        """Effective length KL in mm from geometry."""
        try:
            geom = self.get_cb_geometry()
            if member == "diagonal":
                L_m = geom.get("diagonal_length_m", 0)
            else:
                L_m = geom.get("horiz_proj_m", 0)
            return f"{L_m * 1000:.0f}"   # convert m → mm
        except (TypeError, ValueError):
            return ""

    def get_cb_alpha_deg(self) -> str:
        """Diagonal angle in degrees."""
        try:
            return f"{self.get_cb_geometry().get('alpha_deg', 0):.2f}"
        except Exception:
            return ""

def _format_project_location(pl_data):
    if not pl_data:
        return ''
    if isinstance(pl_data, str):
        try:
            import ast
            pl_dict = ast.literal_eval(pl_data)
        except Exception:
            return pl_data
    elif isinstance(pl_data, dict):
        pl_dict = pl_data
    else:
        return str(pl_data)
    
    method = pl_dict.get('method')
    data = pl_dict.get('data', {})
    
    if method == 'location_name':
        dist = data.get('district', '')
        state = data.get('state', '')
        if dist and state:
            return f"{dist}, {state}"
        return dist or state or r''
    elif method == 'map':
        lat = data.get('latitude', '')
        lon = data.get('longitude', '')
        if lat and lon:
            try:
                from osdagbridge.core.bridge_types.plate_girder.ui_fields_project_location import DB_PATH
                from osdagbridge.core.data.project_location.database import Database
                db = Database(DB_PATH)
                db.connect()
                nearest = db.get_nearest_station_temperature(float(lat), float(lon))
                db.close()
                if nearest:
                    return f"{nearest['station']}, {nearest['state']}"
            except Exception as e:
                logger.warning(f"Reverse geocode error: {e}")
            return f"Lat: {lat}°, Lon: {lon}°"
        return 'Map Location'
    elif method == 'custom_data':
        return 'Custom Location Data'
    
    return str(pl_data)

# ---------------------------------------------------------------------------
# Public builder helper (unchanged signature)
# ---------------------------------------------------------------------------

def build_report_payload(request, input_dict, output_dict):
    try:
        rd  = request.metadata.report_date or datetime.date.today().isoformat()
        lp  = request.metadata.logo_path
        raw_pl = request.metadata.project_location or input_dict.get('project.location') or ''
        pl = _format_project_location(raw_pl)

        md = ReportMetadata(
            project_name  = request.metadata.project_name,
            project_location = pl,
            designer      = request.metadata.designer,
            client        = request.metadata.client,
            company       = request.metadata.company,
            group_name    = request.metadata.group_name,
            subtitle      = request.metadata.subtitle,
            job_number    = request.metadata.job_number,
            additional_comments = request.metadata.additional_comments,
            logo_path     = lp,
            report_date   = rd,
            reviewer      = getattr(request.metadata, 'reviewer', ''))

        # Inject detailed project location and weather data into input_dict dict
        try:
            import ast
            if isinstance(raw_pl, str) and '{' in raw_pl:
                pl_dict = ast.literal_eval(raw_pl)
            elif isinstance(raw_pl, dict):
                pl_dict = raw_pl
            else:
                pl_dict = {}
                
            if pl_dict and isinstance(pl_dict, dict):
                data = pl_dict.get('data', {})
                weather = pl_dict.get('weather_data', {})
                
                # We prioritize manual inputs if they exist, else we use the DB/map coordinates
                lat_val = data.get('latitude') or weather.get('latitude')
                lon_val = data.get('longitude') or weather.get('longitude')
                
                if 'latitude' not in input_dict and lat_val:
                    input_dict['latitude'] = lat_val
                if 'longitude' not in input_dict and lon_val:
                    input_dict['longitude'] = lon_val
                    
                if 'seismic_zone' not in input_dict and weather.get('zone'):
                    input_dict['seismic_zone'] = weather.get('zone')
                if 'wind_speed' not in input_dict and weather.get('wind_speed'):
                    input_dict['wind_speed'] = weather.get('wind_speed')
                if 'shade_temp_max' not in input_dict and weather.get('max_temp'):
                    input_dict['shade_temp_max'] = weather.get('max_temp')
                if 'shade_temp_min' not in input_dict and weather.get('min_temp'):
                    input_dict['shade_temp_min'] = weather.get('min_temp')
        except Exception as e:
            logger.warning(f"Failed to parse project location data: {e}")

        asum = {}
        if output_dict:
            asum = output_dict.get('analysis_summary', {})

        # 4) Grab Design Checks and Log
        dc = []
        le = []
        if output_dict:
            if 'design_checks' in output_dict:
                dc = output_dict['design_checks']
            if 'design_log' in output_dict:
                le = output_dict['design_log']

        return ReportPayload(metadata=md, options=request.options, inputs=input_dict,
                             analysis_summary=asum, design_checks=dc,
                             figures=ReportFigures(), log_entries=le,
                             output_dict=output_dict or {})

    except Exception as exc:
        logger.warning("build_report_payload error: %s", exc)
        return ReportPayload(
            metadata=request.metadata, options=request.options,
            inputs={}, analysis_summary={}, design_checks=[],
            figures=ReportFigures(), log_entries=[],
            output_dict={})


# ---------------------------------------------------------------------------



from osdagbridge.core.boq.boq_generator import calculate_material_quantities

# ===========================================================================
# Public entry point
# ===========================================================================

_FIGURE_MAP = [
    ('plan',                  'plan.png'),
    ('cross_section',         'cross_section.png'),
    ('final_geometry',        'final_geometry.png'),
    ('longitudinal_elevation','longitudinal_elevation.png'),
    ('girder_3d',             'girder_3d.png'),
    ('girder_top',            'girder_top.png'),
    ('section_preview',       'section_preview.png'),
    ('stiffener_preview',     'stiffener_preview.png'),
    ('cb_diagram',            'cb_diagram.png'),
    ('cb_bracing',            'cb_bracing.png'),
    ('cb_top_chord',          'cb_top_chord.png'),
    ('cb_bottom_chord',       'cb_bottom_chord.png'),
    ('ed_diagram',            'ed_diagram.png'),
    ('ed_bracing',            'ed_bracing.png'),
    ('ed_top_chord',          'ed_top_chord.png'),
    ('ed_bottom_chord',       'ed_bottom_chord.png'),
    ('bm_envelope',           'bm_envelope.png'),
    ('sf_envelope',           'sf_envelope.png'),
    ('defl_ll',               'defl_ll.png'),
]

def generate_report(payload, request):
    # type: (ReportPayload, ReportRequest) -> ReportResult
    """Compile the full OsdagBridge Design Report to PDF (+ .tex source)."""
    tex_path = None
    try:
        # Use OsdagLatexEnv to discover the bundled pdflatex path
        compiler = 'pdflatex'
        try:
            from osdag_latex_env.__main__ import OsdagLatexEnv
            latex_env = OsdagLatexEnv()
            if latex_env.pdflatex:
                compiler = str(latex_env.pdflatex)
                # Ensure the bin directory is in PATH so subprocess can find DLLs if needed
                if latex_env.bin_dir:
                    import os
                    os.environ['PATH'] = str(latex_env.bin_dir) + os.pathsep + os.environ.get('PATH', '')
        except Exception as e:
            logger.info("osdag_latex_env not found or failed to load. (%s)", e)
            
        logger.info("Compiler: %s", compiler)

        os.makedirs(request.output_dir, exist_ok=True)

        # fig_paths is built inside TemporaryDirectory (see below) after bytes are written

        pdf_path = os.path.join(request.output_dir, request.file_stem + '.pdf')
        tex_path = os.path.join(request.output_dir, request.file_stem + '.tex')

        # Write to temp dir first, compile there, then copy back
        with tempfile.TemporaryDirectory() as tmp_dir:

            # ── Write figure bytes into tmp_dir/images/ then free RAM immediately ──
            tmp_images = os.path.join(tmp_dir, 'images')
            os.makedirs(tmp_images, exist_ok=True)
            fig_paths = {}
            for attr, img_bytes in list(payload.figure_data.items()):
                if img_bytes:
                    p = os.path.join(tmp_images, attr + '.png')
                    with open(p, 'wb') as fh:
                        fh.write(img_bytes)
                    fig_paths[attr] = p.replace('\\', '/')
            payload.figure_data.clear()  # bytes no longer needed — free RAM now

            # ── Write title-page logos into tmp_dir/assets (auto-deleted) ──
            # Nothing is left next to the PDF. Latex paths are relative to tmp_dir.
            tmp_assets = os.path.join(tmp_dir, 'assets')
            os.makedirs(tmp_assets, exist_ok=True)

            osdag_logo_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'ResourceFiles', 'vectors', 'Osdag Logo.png')
            iit_logo_src   = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'IIT Bombay Logo.png')

            osdag_logo_latex = None
            if os.path.exists(osdag_logo_src):
                shutil.copy2(osdag_logo_src, os.path.join(tmp_assets, 'osdag_logo.png'))
                osdag_logo_latex = 'assets/osdag_logo.png'

            org_logo_latex = None
            org_logo_src = payload.metadata.logo_path if (payload.metadata.logo_path and os.path.exists(payload.metadata.logo_path)) else (iit_logo_src if os.path.exists(iit_logo_src) else None)
            if org_logo_src:
                shutil.copy2(org_logo_src, os.path.join(tmp_assets, 'org_logo.png'))
                org_logo_latex = 'assets/org_logo.png'

            # Compute and inject quantities for Chapter 7
            quantities = calculate_material_quantities(payload.inputs, payload.output_dict)
            payload.inputs.update(quantities)

            # ── Assemble LaTeX document (fig_paths now has tmp_dir paths) ──
            bridge = ReportDataBridge(payload.output_dict, payload.inputs, payload)
            span_m = float(payload.inputs.get(KEY_SPAN, 0) or 0)

            doc_parts = []
            doc_parts.append(preamble(payload.metadata.project_name, payload.metadata.job_number, payload.metadata.report_date, payload.metadata.subtitle or r'\placeholder{Rev 0}'))
            doc_parts.append(title_page(payload.metadata, osdag_logo_latex, org_logo_latex))

            if payload.options.include_toc:
                doc_parts.append(toc_section())

            doc_parts.append(executive_summary(payload.inputs, payload.output_dict, fig_paths))
            doc_parts.append(ch1_project_info(payload.metadata))

            secs = payload.options.sections
            if 'Input Parameters' in secs:
                doc_parts.append(ch2_input_parameters(payload.metadata, payload.inputs, payload.output_dict))
    
            doc_parts.append(ch3_loads(payload.inputs))
            doc_parts.append(ch4_analysis(payload.analysis_summary, fig_paths, bridge, span_m))

            if 'Design Checks' in secs:
                doc_parts.append(ch5_design_checks(payload.design_checks, bridge))

            if payload.options.include_figures:
                doc_parts.append(ch6_drawings(fig_paths))

            doc_parts.append(ch7_quantities(payload.inputs))

            if 'Design Log' in secs:
                doc_parts.append(ch8_design_log(payload.log_entries, payload.inputs))

            doc_parts.append(ch9_references())
            doc_parts.append(r"\end{document}")

            full_tex = "\n".join(doc_parts)

            tmp_tex = os.path.join(tmp_dir, request.file_stem + '.tex')
            tmp_pdf = os.path.join(tmp_dir, request.file_stem + '.pdf')

            with open(tmp_tex, 'w', encoding='utf-8') as f:
                f.write(full_tex)

            # Compile twice for TOC and references
            for _ in range(2):
                try:
                    kwargs = {
                        'cwd': tmp_dir,
                        'stdout': subprocess.PIPE,
                        'stderr': subprocess.PIPE,
                        'check': False
                    }
                    if os.name == 'nt':
                        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
                    
                    res = subprocess.run(
                        [compiler, '-interaction=nonstopmode', request.file_stem + '.tex'],
                        **kwargs
                    )
                except Exception as exc:
                    logger.warning(f"pdflatex run failed: {exc}")

            if os.path.exists(tmp_tex):
                shutil.copy2(tmp_tex, tex_path)
            if os.path.exists(tmp_pdf):
                shutil.copy2(tmp_pdf, pdf_path)

        if os.path.exists(pdf_path):
            logger.info("Report generated: %s", pdf_path)
            return ReportResult(pdf_path=pdf_path, tex_path=tex_path)

        logger.error("pdflatex ran but no PDF was produced.")
        if 'res' in locals():
            logger.error("pdflatex STDOUT:\n%s", res.stdout.decode('utf-8', 'ignore'))
            logger.error("pdflatex STDERR:\n%s", res.stderr.decode('utf-8', 'ignore'))
        return ReportResult(pdf_path=None, tex_path=tex_path)

    except Exception as exc:
        logger.error("generate_report failed: %s", exc, exc_info=True)
        if tex_path and os.path.exists(tex_path):
            return ReportResult(pdf_path=None, tex_path=tex_path)
        return ReportResult(pdf_path=None, tex_path=None)